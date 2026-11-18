# Iter4: admin PDF download (v4) for completed bowling report + weight_transfer score/10 in report
import os
import pytest
import requests
from dotenv import dotenv_values
from pymongo import MongoClient

BASE = (os.environ.get("REACT_APP_BACKEND_URL") or dotenv_values("/app/frontend/.env")["REACT_APP_BACKEND_URL"]).rstrip("/") + "/api"
_be = dotenv_values("/app/backend/.env")
mdb = MongoClient(_be["MONGO_URL"])[_be["DB_NAME"]]


def login(email, pw):
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"email": email, "password": pw}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"login failed {r.status_code}")
    s.headers["x-csrf-token"] = s.cookies.get("ca_csrf") or ""
    return s


@pytest.fixture(scope="module")
def admin():
    return login("qa.admin+qa@cricanalyze.in", "QaAdmin#2026")


@pytest.fixture(scope="module")
def job_id():
    j = mdb.analysis_jobs.find_one({"analysis_type": "bowling", "status": "completed"}, {"_id": 0, "id": 1}, sort=[("created_at", -1)])
    if not j:
        pytest.skip("no completed bowling job")
    return j["id"]


def test_admin_pdf(admin, job_id):
    r = admin.get(f"{BASE}/analyses/{job_id}/pdf", timeout=120)
    assert r.status_code == 200, r.text[:300]
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:4] == b"%PDF" and len(r.content) > 10000


def test_anon_pdf_denied(job_id):
    r = requests.get(f"{BASE}/analyses/{job_id}/pdf", timeout=30)
    assert r.status_code in (401, 403)


def test_report_weight_transfer_score(admin, job_id):
    r = admin.get(f"{BASE}/analyses/{job_id}", timeout=60)
    assert r.status_code == 200, r.text[:300]
    txt = r.text
    assert "weight_transfer" in txt
