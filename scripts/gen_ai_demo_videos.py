"""One-off: generates realistic 3D demo clips for the upload page via fal.ai (Kling v3 Pro, Universal Key)."""
import os, sys, time, requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
KEY = os.environ["EMERGENT_LLM_KEY"]
# Fal Universal Key supports queue inference through Emergent proxy, not Platform APIs.
CONTROL = os.environ.get("INTEGRATION_PROXY_URL", "https://integrations.emergentagent.com").rstrip("/") + "/api/v1/fal"
EP = "fal-ai/kling-video/v3/pro/text-to-video"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
OUT = "/app/frontend/public/demo/"
NEG = "text, captions, subtitles, watermark, logo, letters, numbers, scoreboard overlay, blur, distortion, extra limbs, low quality, cartoon"

CLIPS = {
    "batting-front-on.mp4": "Photorealistic cinematic 3D render of a professional cricket batsman in white kit, helmet and pads on a sunlit green cricket pitch. "
    "Static camera on a tripod at hip height placed directly in front of the batsman, behind the bowler's end (front-on view), whole body, bat and feet fully in frame. "
    "The batsman taps the bat, lifts it in a high backlift, strides forward and plays a smooth front-foot cover drive, transferring weight onto the front leg, then holds a balanced high follow-through. "
    "Natural daylight, sharp detail, no camera movement, no zoom.",
    "bowling-side-on.mp4": "Photorealistic cinematic 3D render of a professional fast bowler in white cricket kit on a sunlit green cricket pitch. "
    "Static camera on a tripod at hip height placed side-on to the crease, about 12 metres away, whole body visible from the last run-up strides to the follow-through. "
    "The bowler runs in, leaps into the gather, lands back foot then front foot with a braced front leg, swings the bowling arm straight over the top to release the red ball, and follows through across the body. "
    "Natural daylight, sharp detail, no camera movement, no zoom.",
}


def gen(name, prompt):
    r = requests.post(f"{CONTROL}/proxy", headers={**H, "X-Fal-Target-Url": f"https://queue.fal.run/{EP}"}, timeout=60,
                      json={"prompt": prompt, "negative_prompt": NEG, "duration": "4", "aspect_ratio": "16:9", "generate_audio": False})
    if r.status_code == 402:
        sys.exit("Insufficient Universal Key balance")
    r.raise_for_status()
    sub = r.json()
    deadline = time.time() + 900
    while time.time() < deadline:
        try:
            s = requests.get(sub["status_url"], headers=H, timeout=30)
        except requests.RequestException:
            time.sleep(3); continue
        st = (s.json().get("status") or "").upper()
        if st in {"COMPLETED", "OK"}:
            res = requests.get(sub["response_url"], headers=H, timeout=60).json()
            url = res["video"]["url"]
            with open(OUT + name, "wb") as f:
                f.write(requests.get(url, timeout=120).content)
            return f"{name}: saved"
        if st in {"FAILED", "CANCELLED", "CANCELED", "ERROR"}:
            return f"{name}: failed {s.text[:300]}"
        time.sleep(5)
    return f"{name}: timeout"


if __name__ == "__main__":
    with ThreadPoolExecutor(2) as ex:
        for line in ex.map(lambda kv: gen(*kv), CLIPS.items()):
            print(line, flush=True)
