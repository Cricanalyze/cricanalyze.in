import sys, asyncio, fitz
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
kind = sys.argv[1] if len(sys.argv) > 1 else "batting"


async def main():
    import report_pdf, analysis_routes
    from core import db
    rep = await db.analysis_reports.find_one({"analysis_type": kind, "biomech": {"$exists": True}}, {"_id": 0}, sort=[("created_at", -1)])
    job = await db.analysis_jobs.find_one({"id": rep["job_id"]}, {"_id": 0})
    owner = await db.users.find_one({"id": job["user_id"]})
    await analysis_routes.attach_view({"role": "super_admin", "id": owner["id"]}, job, rep)
    await db.analysis_reports.update_one({"id": rep["id"]}, {"$unset": {"pdf": ""}})
    pdf = await report_pdf.get_or_build(rep, job, owner)
    open(f'/tmp/r_{kind}.pdf', 'wb').write(pdf)

asyncio.run(main())
d = fitz.open(f'/tmp/r_{kind}.pdf')
print("pages", len(d))
for i, pg in enumerate(d):
    pg.get_pixmap(dpi=60).save(f"/tmp/r_{kind}_p{i + 1}.png")
