"""Ultralytics Platform hosted inference (YOLO26n detect + YOLO26n-pose). Key stays server-side."""
import os, time, threading
import cv2
import requests

BASE = "https://platform.ultralytics.com/api/models/ultralytics/yolo26"
_lock = threading.Lock()
_last = {}


class UltralyticsError(Exception):
    pass


def configured():
    import key_pool
    return key_pool.has("ultralytics")


def _url(task, e=None):
    if task == "pose":
        return (e or {}).get("pose_url") or os.environ.get("ULTRALYTICS_POSE_URL") or f"{BASE}/yolo26n-pose/predict"
    return (e or {}).get("detect_url") or os.environ.get("ULTRALYTICS_DETECT_URL") or f"{BASE}/yolo26n/predict"


def _interval():
    return 60.0 / max(1.0, float(os.environ.get("ULTRALYTICS_RPM", "20")))


def _wait(kid):
    with _lock:
        wait = _last.get(kid, 0.0) + _interval() - time.monotonic()
        _last[kid] = max(time.monotonic(), _last.get(kid, 0.0) + _interval())
    if wait > 0:
        time.sleep(wait)


def predict(img, task="detect", conf=0.25, imgsz=640):
    """img: BGR ndarray. Tries each configured key (rotate/failover); rate-limited or rejected keys are skipped."""
    import key_pool
    jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()
    data = {"conf": str(conf), "iou": "0.7", "imgsz": str(imgsz), "normalize": "false"}
    last = "Ultralytics API key is not configured."
    for attempt in range(6):
        keys = key_pool.ordered("ultralytics")
        if not keys:
            raise UltralyticsError(last)
        waits = [key_pool.cooling_until(e["id"]) for e in keys]
        if all(waits):
            time.sleep(min(30, max(1, min(waits) - time.time())))
        for e in keys:
            if attempt < 5 and key_pool.cooling_until(e["id"]) and len(keys) > 1 and not all(waits):
                continue
            _wait(e["id"])
            try:
                r = requests.post(_url(task, e), headers={"Authorization": f"Bearer {e['key']}"}, data=data,
                                  files={"file": ("frame.jpg", jpg, "image/jpeg")}, timeout=60)
            except requests.RequestException as ex:
                key_pool.mark_bad(e, 30, type(ex).__name__)
                last = "Ultralytics could not be reached."
                continue
            if r.status_code == 429:
                key_pool.mark_bad(e, min(float(r.headers.get("Retry-After") or 15), 60), "rate limited (429)")
                last = "Ultralytics rate limit reached; try again later."
                continue
            if r.status_code in (401, 403):
                key_pool.mark_bad(e, 900, f"rejected ({r.status_code})")
                last = "Ultralytics rejected the API key."
                continue
            if r.status_code >= 400:
                key_pool.mark_bad(e, 30, f"HTTP {r.status_code}")
                last = f"Ultralytics inference failed (HTTP {r.status_code})."
                continue
            key_pool.mark_ok(e)
            imgs = r.json().get("images") or [{}]
            return imgs[0].get("results") or []
    raise UltralyticsError(last)


def pose_persons(img):
    """Persons as 17x[x, y, score] (COCO order), matching the local pose contract."""
    out = []
    for p in predict(img, "pose", conf=0.25, imgsz=640):
        k = p.get("keypoints") or {}
        xs, ys, vs = k.get("x") or [], k.get("y") or [], k.get("visible") or []
        if p.get("name", "person") == "person" and len(xs) == 17:
            out.append([[float(xs[j]), float(ys[j]), float(vs[j] if j < len(vs) else 0)] for j in range(17)])
    return out


def balls(img, conf=0.15, imgsz=1280):
    """Sports-ball detections as (cx, cy, w, h, conf) in img pixels."""
    res = []
    for d in predict(img, "detect", conf=conf, imgsz=imgsz):
        if d.get("name") != "sports ball":
            continue
        b = d["box"]
        res.append(((b["x1"] + b["x2"]) / 2, (b["y1"] + b["y2"]) / 2, b["x2"] - b["x1"], b["y2"] - b["y1"], float(d["confidence"])))
    return res
