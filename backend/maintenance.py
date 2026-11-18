import time, asyncio, logging
from datetime import timezone
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from core import db, now, audit, ADMIN, STAFF, session_from_request, send_email
from report_view import ist
from analysis_routes import parse_when

router = APIRouter(prefix="/api")
OPEN = ("/api/maintenance", "/api/auth/", "/api/billing/webhook")
_cache = {"at": 0.0, "doc": None}
log = logging.getLogger("cricanalyze")
_tasks = set()


async def notify_users(start, end, message):
    ctx = {"start": ist(start), "end": ist(end), "message": message or "Thank you for your patience."}
    sent = 0
    async for u in db.users.find({"email_verified": True, "status": "active"}, {"_id": 0, "id": 1, "email": 1}):
        sent += bool(await send_email(u["email"], "maintenance", ctx, u["id"]))
        await asyncio.sleep(0.5)
    log.info(f"maintenance notice sent to {sent} users")


async def _doc():
    if time.time() - _cache["at"] > 10:
        _cache["doc"] = await db.settings.find_one({"_id": "maintenance"}, {"_id": 0}) or {}
        _cache["at"] = time.time()
    return _cache["doc"]


def _active(d):
    s, e = d.get("start_at"), d.get("end_at")
    if not d.get("enabled") or not s or not e:
        return False
    return _aware(s) <= now() < _aware(e)


def _aware(d):
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _out(d):
    iso = lambda x: _aware(x).isoformat() if x else None
    return {"active": _active(d), "enabled": bool(d.get("enabled")), "start_at": iso(d.get("start_at")), "end_at": iso(d.get("end_at")),
            "message": d.get("message") or "We're upgrading CricAnalyze to serve you better."}


async def gate(request: Request):
    """Returns a 503 response when maintenance is active and the caller isn't staff, else None."""
    p = request.url.path
    if not p.startswith("/api") or p.startswith(OPEN):
        return None
    d = await _doc()
    if not _active(d):
        return None
    s = await session_from_request(request)
    if s:
        u = await db.users.find_one({"id": s["user_id"]}, {"role": 1})
        if u and u.get("role") in STAFF:
            return None
    return JSONResponse({"detail": "maintenance", **_out(d)}, status_code=503)


@router.get("/maintenance")
async def status():
    return _out(await _doc())


class MaintIn(BaseModel):
    enabled: bool
    start_at: Optional[str] = Field(None, max_length=40)
    end_at: Optional[str] = Field(None, max_length=40)
    message: Optional[str] = Field(None, max_length=300)


@router.put("/admin/maintenance")
async def save(body: MaintIn, request: Request, a=Depends(ADMIN)):
    s = parse_when(body.start_at) if body.start_at else None
    e = parse_when(body.end_at) if body.end_at else None
    if body.enabled and (not s or not e or e <= s):
        raise HTTPException(422, "Set a start time and an end time after it.")
    prev = await db.settings.find_one({"_id": "maintenance"}) or {}
    msg = (body.message or "").strip() or None
    notify = body.enabled and e > now() and (not prev.get("enabled") or prev.get("start_at") != s or prev.get("end_at") != e)
    doc = {"enabled": body.enabled, "start_at": s, "end_at": e, "message": msg, "updated_at": now(), "updated_by": a["id"]}
    await db.settings.update_one({"_id": "maintenance"}, {"$set": doc}, upsert=True)
    _cache["at"] = 0
    if notify:
        task = asyncio.create_task(notify_users(s, e, msg))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    await audit(a["id"], "admin.maintenance", None, {"enabled": body.enabled, "start_at": body.start_at, "end_at": body.end_at}, request)
    return {**_out(await _doc()), "users_notified": bool(notify)}
