# Media streaming (Range/206, concurrency, signature) regression tests for the AnalysisViewer "no supported sources" fix
import concurrent.futures as cf
import requests, pytest
from conftest import C, BASE_URL

VID = "8525eb55bc7648a794383b9058cd2998"  # QA player's bat1.mp4 upload (iteration 6)


@pytest.fixture(scope="module")
def media_url():
    c = C()
    r = c.post("/auth/login", json={"email": "qa.player+qa@cricanalyze.in", "password": "QaPlayer#2026"})
    if r.status_code != 200:
        pytest.skip("QA player login failed")
    vid = VID
    vs = c.get("/videos")
    if vs.status_code == 200:
        items = vs.json() if isinstance(vs.json(), list) else vs.json().get("items", [])
        if items and not any(i.get("id") == VID for i in items):
            vid = items[0]["id"]
    r = c.get(f"/videos/{vid}/url")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["url"].startswith("/api/media/") and d["expires_in"] == 900
    return BASE_URL + d["url"]


class TestMedia:
    def test_full_get(self, media_url):
        r = requests.get(media_url, timeout=60)
        assert r.status_code == 200
        assert r.headers.get("accept-ranges") == "bytes"
        assert r.headers["content-type"].startswith("video/")
        assert len(r.content) > 1000

    def test_range_first_bytes(self, media_url):
        r = requests.get(media_url, headers={"Range": "bytes=0-1"}, timeout=60)
        assert r.status_code == 206
        assert len(r.content) == 2
        assert r.headers["content-range"].startswith("bytes 0-1/")

    def test_range_suffix_and_open(self, media_url):
        total = int(requests.get(media_url, headers={"Range": "bytes=0-0"}, timeout=60).headers["content-range"].split("/")[1])
        r = requests.get(media_url, headers={"Range": "bytes=-100"}, timeout=60)
        assert r.status_code == 206 and len(r.content) == 100
        r = requests.get(media_url, headers={"Range": f"bytes={total - 50}-"}, timeout=60)
        assert r.status_code == 206 and len(r.content) == 50
        r = requests.get(media_url, headers={"Range": f"bytes={total + 10}-"}, timeout=60)
        assert r.status_code == 416

    def test_concurrent_range_requests_all_206(self, media_url):
        def hit(i):
            start = i * 1000
            return requests.get(media_url, headers={"Range": f"bytes={start}-{start + 999}"}, timeout=90).status_code
        with cf.ThreadPoolExecutor(30) as ex:
            codes = list(ex.map(hit, range(30)))
        assert codes.count(206) == 30, codes

    def test_bad_signature_403(self, media_url):
        bad = media_url.rsplit("sig=", 1)[0] + "sig=deadbeef"
        assert requests.get(bad, timeout=30).status_code == 403

    def test_expired_403(self, media_url):
        import re
        bad = re.sub(r"exp=\d+", "exp=1000", media_url)
        assert requests.get(bad, timeout=30).status_code == 403
