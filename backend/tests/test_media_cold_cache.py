# Media endpoint: cold-cache concurrency for every QA player video (playback + original) - all Range requests must be 206
import concurrent.futures as cf
import requests, pytest
from conftest import C, BASE_URL


@pytest.fixture(scope="module")
def urls():
    c = C()
    r = c.post("/auth/login", json={"email": "qa.player+qa@cricanalyze.in", "password": "QaPlayer#2026"})
    if r.status_code != 200:
        pytest.skip("QA player login failed")
    vs = c.get("/videos").json()
    items = vs if isinstance(vs, list) else vs.get("items", [])
    out = []
    for v in items:
        d = c.get(f"/videos/{v['id']}/url").json()
        out += [BASE_URL + d["url"], BASE_URL + d["original_url"]]
    assert out
    return list(dict.fromkeys(out))


def test_parallel_ranges_all_assets(urls):
    def hit(arg):
        u, i = arg
        r = requests.get(u, headers={"Range": f"bytes={i * 2000}-{i * 2000 + 1999}"}, timeout=120)
        return r.status_code
    jobs = [(u, i) for u in urls for i in range(30)]
    with cf.ThreadPoolExecutor(40) as ex:
        codes = list(ex.map(hit, jobs))
    bad = [c for c in codes if c != 206]
    print(f"{len(codes)} requests across {len(urls)} assets; non-206: {bad}")
    assert not bad
