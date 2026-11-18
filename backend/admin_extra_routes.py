import asyncio
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field
import key_pool
from core import db, now, uid, audit, ADMIN, sanitize_error, llm_text, AI_MODEL

router = APIRouter(prefix="/api/admin")


# ---------- API key pool ----------
class KeyIn(BaseModel):
    provider: str
    label: str = Field(min_length=1, max_length=60)
    key: str = Field(min_length=8, max_length=400)
    priority: int = 10
    pose_url: Optional[str] = None
    detect_url: Optional[str] = None


class KeyPatch(BaseModel):
    active: Optional[bool] = None
    priority: Optional[int] = None
    label: Optional[str] = None
    pose_url: Optional[str] = None
    detect_url: Optional[str] = None


def _row(r):
    st = key_pool.STATS.get(r["id"], {})
    return {**{k: r.get(k) for k in ("id", "provider", "label", "priority", "active", "pose_url", "detect_url", "masked", "created_at")},
            "ok": st.get("ok", 0), "fail": st.get("fail", 0), "last_error": st.get("last_error"), "cooling": bool(key_pool.cooling_until(r["id"]))}


@router.get("/api-keys")
async def list_keys(a=Depends(ADMIN)):
    from core import get_settings
    rows = [_row(r) for r in await db.api_keys.find({}, {"_id": 0, "key_enc": 0}).sort([("provider", 1), ("priority", 1)]).to_list(200)]
    env = []
    for p, var in key_pool.PROVIDERS.items():
        e = next((x for x in key_pool.entries(p) if x["id"] == "env"), None)
        if e:
            st = key_pool.STATS.get("env", {})
            env.append({"id": "env", "provider": p, "label": f"Main key ({var})", "priority": 0, "active": True, "masked": key_pool.mask(e["key"]),
                        "env": True, "ok": st.get("ok", 0), "fail": st.get("fail", 0), "last_error": st.get("last_error"), "cooling": bool(key_pool.cooling_until("env"))})
    return {"keys": env + rows, "modes": (await get_settings())["keys"]}


@router.post("/api-keys")
async def add_key(body: KeyIn, request: Request, a=Depends(ADMIN)):
    if body.provider not in key_pool.PROVIDERS:
        raise HTTPException(422, "Provider must be anthropic or ultralytics.")
    k = body.key.strip()
    doc = {"id": uid(), "provider": body.provider, "label": body.label.strip(), "key_enc": key_pool.encrypt(k), "masked": key_pool.mask(k),
           "priority": body.priority, "active": True, "pose_url": (body.pose_url or "").strip() or None, "detect_url": (body.detect_url or "").strip() or None,
           "created_at": now(), "created_by": a["id"]}
    await db.api_keys.insert_one(doc)
    await key_pool.refresh(db)
    await audit(a["id"], "admin.api_key_added", doc["id"], {"provider": body.provider, "label": doc["label"]}, request)
    return {"id": doc["id"]}


@router.patch("/api-keys/{kid}")
async def patch_key(kid: str, body: KeyPatch, request: Request, a=Depends(ADMIN)):
    upd = {k: v for k, v in body.model_dump().items() if v is not None}
    r = await db.api_keys.update_one({"id": kid}, {"$set": upd})
    if not r.matched_count:
        raise HTTPException(404, "Key not found.")
    await key_pool.refresh(db)
    await audit(a["id"], "admin.api_key_updated", kid, upd, request)
    return {"ok": True}


@router.delete("/api-keys/{kid}")
async def delete_key(kid: str, request: Request, a=Depends(ADMIN)):
    await db.api_keys.delete_one({"id": kid})
    await key_pool.refresh(db)
    await audit(a["id"], "admin.api_key_deleted", kid, request=request)
    return {"ok": True}


@router.post("/api-keys/{kid}/test")
async def test_key(kid: str, provider: str, a=Depends(ADMIN)):
    e = next((x for x in key_pool.entries(provider) if x["id"] == kid), None) if provider in key_pool.PROVIDERS else None
    if not e:
        raise HTTPException(404, "Key not found or inactive.")
    try:
        if provider == "anthropic":
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            out = await asyncio.wait_for(LlmChat(api_key=e["key"], session_id=f"t-{uid()}", system_message="Reply with OK.").with_model("anthropic", AI_MODEL)
                                         .send_message(UserMessage(text="Say OK")), 40)
            ok = "OK" in out.upper()
        else:
            import numpy as np, cv2, requests
            from ultralytics_client import _url
            jpg = cv2.imencode(".jpg", np.full((320, 320, 3), 127, np.uint8))[1].tobytes()
            r = await asyncio.to_thread(requests.post, _url("detect", e), headers={"Authorization": f"Bearer {e['key']}"},
                                        data={"conf": "0.25", "imgsz": "320"}, files={"file": ("f.jpg", jpg, "image/jpeg")}, timeout=60)
            ok = r.status_code < 400
            if not ok:
                return {"ok": False, "message": f"HTTP {r.status_code}"}
        return {"ok": ok, "message": "Key works." if ok else "Unexpected reply."}
    except Exception as ex:
        return {"ok": False, "message": sanitize_error(ex)}


# ---------- commissions ----------
@router.get("/commissions")
async def commissions(status: Optional[str] = None, a=Depends(ADMIN)):
    q = {"status": status} if status else {}
    rows = await db.commissions.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)
    acs = {x["id"]: x for x in await db.academies.find({"id": {"$in": list({r["academy_id"] for r in rows})}}, {"_id": 0, "id": 1, "name": 1, "code": 1, "commission": 1}).to_list(500)}
    for r in rows:
        r["academy_name"] = (acs.get(r["academy_id"]) or {}).get("name")
    totals = {}
    for r in rows:
        t = totals.setdefault(r["academy_id"], {"academy_id": r["academy_id"], "academy_name": r["academy_name"], "pending": 0, "paid": 0})
        t[r["status"]] = round(t.get(r["status"], 0) + r["amount_inr"], 2)
    return {"rows": rows, "totals": list(totals.values())}


class PaidIn(BaseModel):
    ids: List[str]
    reference: str = Field("", max_length=120)


@router.post("/commissions/mark-paid")
async def mark_paid(body: PaidIn, request: Request, a=Depends(ADMIN)):
    r = await db.commissions.update_many({"id": {"$in": body.ids}, "status": "pending"},
                                         {"$set": {"status": "paid", "paid_at": now(), "paid_by": a["id"], "payout_reference": body.reference}})
    await audit(a["id"], "admin.commission_paid", None, {"count": r.modified_count, "ref": body.reference}, request)
    return {"ok": True, "updated": r.modified_count}


class AcademyCommissionIn(BaseModel):
    mode: Optional[str] = None
    value: Optional[float] = Field(None, ge=0)


@router.put("/academies/{aid}/commission")
async def academy_commission(aid: str, body: AcademyCommissionIn, request: Request, a=Depends(ADMIN)):
    if body.mode and body.mode not in ("fixed_per_student", "percent_first", "percent_every"):
        raise HTTPException(422, "Invalid commission mode.")
    val = {"mode": body.mode, "value": body.value} if body.mode and body.value is not None else None
    r = await db.academies.update_one({"id": aid}, {"$set": {"commission": val}})
    if not r.matched_count:
        raise HTTPException(404, "Academy not found.")
    await audit(a["id"], "admin.academy_commission", aid, val, request)
    return {"ok": True}
