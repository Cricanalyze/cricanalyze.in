"""Multiple API keys per provider (Anthropic, Ultralytics) with rotate or failover modes. Env key is always the primary entry."""
import os, time, base64, hashlib, threading
from cryptography.fernet import Fernet

PROVIDERS = {"anthropic": "ANTHROPIC_API_KEY", "ultralytics": "ULTRALYTICS_API_KEY"}
_fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(("keypool:" + os.environ["APP_SECRET"]).encode()).digest()))
_lock = threading.Lock()
_keys = {p: [] for p in PROVIDERS}
_modes = {p: "rotate" for p in PROVIDERS}
_cool = {}
_rr = {p: 0 for p in PROVIDERS}
STATS = {}


def encrypt(v: str) -> str:
    return _fernet.encrypt(v.encode()).decode()


def mask(v: str) -> str:
    return (v[:6] + "…" + v[-4:]) if v and len(v) > 12 else "••••"


async def refresh(db):
    from core import get_settings
    s = (await get_settings()).get("keys", {})
    rows = await db.api_keys.find({"active": True}, {"_id": 0}).sort([("priority", 1), ("created_at", 1)]).to_list(100)
    new = {p: [] for p in PROVIDERS}
    for r in rows:
        try:
            new[r["provider"]].append({"id": r["id"], "label": r["label"], "key": _fernet.decrypt(r["key_enc"].encode()).decode(),
                                       "pose_url": r.get("pose_url"), "detect_url": r.get("detect_url")})
        except Exception:
            continue
    with _lock:
        for p in PROVIDERS:
            _keys[p] = new[p]
            _modes[p] = s.get(f"{p}_mode", "rotate")


def entries(provider):
    env = os.environ.get(PROVIDERS[provider])
    base = [{"id": "env", "label": "Main key (environment)", "key": env, "pose_url": None, "detect_url": None}] if env else []
    return base + list(_keys[provider])


def has(provider):
    return bool(entries(provider))


def ordered(provider):
    """Healthy keys first (rotated in rotate mode, priority order in failover mode); cooling-down keys last."""
    es = entries(provider)
    if not es:
        return []
    with _lock:
        if _modes[provider] == "rotate" and len(es) > 1:
            i = _rr[provider] % len(es)
            _rr[provider] += 1
            es = es[i:] + es[:i]
    t = time.time()
    return [e for e in es if _cool.get(e["id"], 0) <= t] + [e for e in es if _cool.get(e["id"], 0) > t]


def first(provider):
    o = ordered(provider)
    return o[0] if o else None


def _stat(e, ok, err=None):
    s = STATS.setdefault(e["id"], {"ok": 0, "fail": 0, "last_error": None, "last_used": None})
    s["ok" if ok else "fail"] += 1
    s["last_used"] = time.time()
    if err:
        s["last_error"] = err[:160]


def mark_ok(e):
    _stat(e, True)


def mark_bad(e, seconds, err=""):
    _cool[e["id"]] = time.time() + seconds
    _stat(e, False, err)


def cooling_until(kid):
    v = _cool.get(kid, 0)
    return v if v > time.time() else None
