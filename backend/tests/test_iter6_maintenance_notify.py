# Maintenance email notify (in-process ASGI; notify_users patched to only mail +qa@cricanalyze.in so the real owner is never emailed)
import asyncio, sys, time
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "/app/backend")
import httpx
import pytest


def test_maintenance_notify_flow():
    asyncio.run(_flow())


async def _flow():
    import server, maintenance
    from core import db, send_email
    from report_view import ist

    sent_to = []

    async def qa_only_notify(start, end, message):
        ctx = {"start": ist(start), "end": ist(end), "message": message or "Thank you for your patience."}
        async for u in db.users.find({"email_verified": True, "status": "active", "email": {"$regex": r"\+qa@cricanalyze\.in$"}},
                                     {"_id": 0, "id": 1, "email": 1}):
            if await send_email(u["email"], "maintenance", ctx, u["id"]):
                sent_to.append(u["email"])
    maintenance.notify_users = qa_only_notify

    tr = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=tr, base_url="https://test", headers={"X-Forwarded-For": "10.9.8.7"}) as c:
        r = await c.post("/api/auth/login", json={"email": "qa.admin+qa@cricanalyze.in", "password": "QaAdmin#2026"})
        assert r.status_code == 200, r.text
        c.headers["X-CSRF-Token"] = c.cookies.get("ca_csrf")
        n = datetime.now(timezone.utc)
        f = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
        body = {"enabled": True, "start_at": f(n + timedelta(days=30)), "end_at": f(n + timedelta(days=30, hours=2)), "message": "TEST_ maint notice"}
        t0 = datetime.now(timezone.utc)
        try:
            r = await c.put("/api/admin/maintenance", json=body)
            assert r.status_code == 200, r.text
            d = r.json()
            print("first save:", d)
            assert d["users_notified"] is True and d["enabled"] is True and d["active"] is False
            for _ in range(40):
                await asyncio.sleep(0.5)
                if len(sent_to) >= 1 and await db.email_logs.count_documents({"template": "maintenance", "created_at": {"$gte": t0}}) >= len(sent_to):
                    break
            await asyncio.sleep(3)
            logs = await db.email_logs.find({"template": "maintenance", "created_at": {"$gte": t0}}, {"_id": 0}).to_list(50)
            print("maintenance email_logs:", [(l["to"], l["status"]) for l in logs])
            assert logs and all(l["to"].endswith("+qa@cricanalyze.in") for l in logs)
            assert any(l["status"] == "accepted" for l in logs)

            # re-save same schedule (same strings) -> no re-notify
            r = await c.put("/api/admin/maintenance", json=body)
            print("re-save:", r.json())
            assert r.status_code == 200 and r.json()["users_notified"] is False
            # same instants given in +05:30 offset form -> still no re-notify
            ist_off = timezone(timedelta(hours=5, minutes=30))
            s2 = datetime.fromisoformat(body["start_at"].replace("Z", "+00:00")).astimezone(ist_off).strftime("%Y-%m-%dT%H:%M:%S")
            e2 = datetime.fromisoformat(body["end_at"].replace("Z", "+00:00")).astimezone(ist_off).strftime("%Y-%m-%dT%H:%M:%S")
            r = await c.put("/api/admin/maintenance", json={**body, "start_at": s2, "end_at": e2})
            print("re-save IST naive:", r.json())
            assert r.json()["users_notified"] is False
            # message-only change -> no re-notify
            r = await c.put("/api/admin/maintenance", json={**body, "message": "TEST_ changed"})
            assert r.json()["users_notified"] is False
            # changed end -> notify again
            r = await c.put("/api/admin/maintenance", json={**body, "end_at": f(n + timedelta(days=30, hours=3))})
            print("changed end:", r.json())
            assert r.json()["users_notified"] is True
            await asyncio.sleep(4)
        finally:
            r = await c.put("/api/admin/maintenance", json={"enabled": False, "start_at": None, "end_at": None, "message": None})
            print("disable:", r.status_code, r.json())
            assert r.json()["users_notified"] is False and r.json()["enabled"] is False
        # past window enabled -> no notify (end in past would fail validation only if e<=s)
        r = await c.put("/api/admin/maintenance", json={"enabled": True, "start_at": f(n - timedelta(hours=3)), "end_at": f(n - timedelta(hours=2))})
        print("past window:", r.json())
        assert r.json()["users_notified"] is False
        r = await c.put("/api/admin/maintenance", json={"enabled": False, "start_at": None, "end_at": None, "message": None})
        assert r.json()["enabled"] is False
        # non-admin forbidden
    async with httpx.AsyncClient(transport=tr, base_url="https://test", headers={"X-Forwarded-For": "10.9.8.6"}) as p:
        r = await p.post("/api/auth/login", json={"email": "qa.player+qa@cricanalyze.in", "password": "QaPlayer#2026"})
        p.headers["X-CSRF-Token"] = p.cookies.get("ca_csrf")
        r = await p.put("/api/admin/maintenance", json={"enabled": False})
        assert r.status_code == 403, r.text
