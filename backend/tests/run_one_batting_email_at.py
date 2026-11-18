"""Background helper: as qa.player upload bat1.mp4 (batting side_on), start analysis with email_at in the future, poll until done."""
import sys, time, uuid, json, datetime
sys.path.insert(0, "/app/backend/tests")
from conftest import login

c = login("qa.player+qa@cricanalyze.in", "QaPlayer#2026")
with open("/app/backend/tests/media/bat1.mp4", "rb") as fh:
    v = c.post("/videos", files={"file": ("bat1.mp4", fh, "video/mp4")}, data={"analysis_type": "batting", "angle": "side_on"})
print("upload", v.status_code, v.text[:200], flush=True)
vid = v.json()["id"]
ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
email_at = (datetime.datetime.now(ist) + datetime.timedelta(minutes=int(sys.argv[1]) if len(sys.argv) > 1 else 12)).strftime("%Y-%m-%dT%H:%M")
r = c.post("/analyses", json={"analysis_type": "batting", "video_ids": [vid], "consent": True, "idempotency_key": uuid.uuid4().hex, "email_at": email_at})
print("create", r.status_code, r.text[:300], "email_at", email_at, flush=True)
jid = r.json()["id"]
for i in range(180):
    j = c.get(f"/analyses/{jid}").json()
    st = j.get("status") or j.get("job", {}).get("status")
    print(i, st, j.get("stage"), j.get("progress"), flush=True)
    if st in ("completed", "failed"):
        break
    time.sleep(10)
print("JOB", jid, flush=True)
print(json.dumps(c.get(f"/analyses/{jid}/email-schedules").json(), default=str), flush=True)
