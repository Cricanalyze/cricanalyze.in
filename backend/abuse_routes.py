import os
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field
from core import db, now, uid, audit, current_user, ADMIN, send_email, APP_URL, rate_limit

router = APIRouter(prefix="/api")
REASONS = {"harassment": "Harassment or bullying", "inappropriate": "Inappropriate messages or content", "fake": "Fake or impersonated coach",
           "payment": "Asked for money outside CricAnalyze", "privacy": "Misused my videos or data", "other": "Something else"}


async def player_membership(aid, u):
    m = await db.academy_memberships.find_one({"academy_id": aid, "user_id": u["id"], "status": "active"})
    if not m:
        raise HTTPException(404, "Academy not found.")
    return m


@router.get("/academies/{aid}/staff")
async def academy_staff(aid: str, u=Depends(current_user)):
    await player_membership(aid, u)
    ms = await db.academy_memberships.find({"academy_id": aid, "status": "active", "role": {"$ne": "player"}}, {"_id": 0}).to_list(100)
    users = {x["id"]: x for x in await db.users.find({"id": {"$in": [m["user_id"] for m in ms]}}, {"_id": 0, "id": 1, "full_name": 1}).to_list(100)}
    return [{"user_id": m["user_id"], "role": m["role"], "name": users.get(m["user_id"], {}).get("full_name") or "Coach"} for m in ms if m["user_id"] != u["id"]]


class AbuseIn(BaseModel):
    academy_id: str
    target_user_id: Optional[str] = None
    reason: str
    details: str = Field(min_length=10, max_length=2000)


@router.post("/abuse-reports")
async def create_report(body: AbuseIn, request: Request, u=Depends(current_user)):
    if body.reason not in REASONS:
        raise HTTPException(422, "Choose a reason.")
    await rate_limit(f"abuse:{u['id']}", 5, 3600)
    await player_membership(body.academy_id, u)
    a = await db.academies.find_one({"id": body.academy_id}) or {}
    target = None
    if body.target_user_id:
        if not await db.academy_memberships.find_one({"academy_id": body.academy_id, "user_id": body.target_user_id, "status": "active", "role": {"$ne": "player"}}):
            raise HTTPException(422, "That person isn't a coach in this academy.")
        target = await db.users.find_one({"id": body.target_user_id}, {"_id": 0, "id": 1, "full_name": 1, "email": 1})
    doc = {"id": uid(), "reporter_id": u["id"], "reporter_name": u.get("full_name"), "reporter_email": u["email"], "academy_id": body.academy_id,
           "academy_name": a.get("name"), "target_user_id": body.target_user_id, "target_name": (target or {}).get("full_name"),
           "target_email": (target or {}).get("email"), "reason": body.reason, "details": body.details.strip(), "status": "open", "created_at": now()}
    await db.abuse_reports.insert_one(doc)
    await audit(u["id"], "abuse.reported", doc["id"], {"academy_id": body.academy_id, "target": body.target_user_id}, request)
    if os.environ.get("ADMIN_EMAIL"):
        await send_email(os.environ["ADMIN_EMAIL"], "abuse_report", {"reporter": doc["reporter_name"] or "A player", "target": doc["target_name"] or "the academy",
                                                                     "academy": doc["academy_name"] or "academy", "reason": REASONS[body.reason],
                                                                     "details": doc["details"], "link": f"{APP_URL}/admin"})
    return {"ok": True, "id": doc["id"]}


@router.get("/admin/abuse-reports")
async def list_reports(status: Optional[str] = None, a=Depends(ADMIN)):
    q = {"status": status} if status in ("open", "resolved", "dismissed") else {}
    rows = await db.abuse_reports.find(q, {"_id": 0}).sort("created_at", -1).to_list(300)
    return [{**r, "reason_label": REASONS.get(r["reason"], r["reason"])} for r in rows]


class ResolveIn(BaseModel):
    status: str
    note: str = Field("", max_length=1000)


@router.post("/admin/abuse-reports/{rid}")
async def resolve(rid: str, body: ResolveIn, request: Request, a=Depends(ADMIN)):
    if body.status not in ("open", "resolved", "dismissed"):
        raise HTTPException(422, "Invalid status.")
    r = await db.abuse_reports.find_one_and_update({"id": rid}, {"$set": {"status": body.status, "admin_note": body.note.strip() or None,
                                                                          "handled_by": a["id"], "handled_at": now()}})
    if not r:
        raise HTTPException(404, "Report not found.")
    await audit(a["id"], "abuse.updated", rid, {"status": body.status}, request)
    return {"ok": True}
