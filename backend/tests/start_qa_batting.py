# Helper: log in as QA player, upload bat1.mp4 (batting, side_on), start analysis, print job id
import sys, uuid, time
sys.path.insert(0, "/app/backend/tests")
from conftest import C

c = C()
r = c.post("/auth/login", json={"email": "qa.player+qa@cricanalyze.in", "password": "QaPlayer#2026"})
print("login", r.status_code, r.text[:200])
with open("/app/backend/tests/media/bat1.mp4", "rb") as f:
    r = c.post("/videos", files={"file": ("bat1.mp4", f, "video/mp4")}, data={"analysis_type": "batting", "angle": "side_on"})
print("upload", r.status_code, r.text[:300])
vid = r.json()["id"]
r = c.post("/analyses", json={"analysis_type": "batting", "video_ids": [vid], "consent": True, "idempotency_key": uuid.uuid4().hex})
print("analysis", r.status_code, r.text[:300])
print("JOB", r.json().get("id"), "VID", vid)
