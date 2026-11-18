"""One-off: generates realistic 3D demo clips for the upload page via fal.ai (Kling v3 Pro, Universal Key)."""
import os, sys, time, requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
KEY = os.environ["EMERGENT_LLM_KEY"]
# Fal Universal Key supports queue inference through Emergent proxy, not Platform APIs.
CONTROL = os.environ.get("INTEGRATION_PROXY_URL", "https://integrations.emergentagent.com").rstrip("/") + "/api/v1/fal"
EP = "fal-ai/kling-video/v3/pro/text-to-video"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
OUT = "/app/frontend/public/demo/"
NEG = "leg pads, batting pads, knee pads, shin guards, helmet, batting gloves, bat, text, captions, subtitles, watermark, logo, letters, numbers, scoreboard overlay, blur, distortion, extra limbs, low quality, cartoon"

CLIPS = {
    "batting-front-on.mp4": "Photorealistic cinematic 3D render of a professional cricket batsman in white kit, helmet and pads on a sunlit green cricket pitch. "
    "Static camera on a tripod at hip height placed directly in front of the batsman, behind the bowler's end (front-on view), whole body, bat and feet fully in frame. "
    "The batsman taps the bat, lifts it in a high backlift, strides forward and plays a smooth front-foot cover drive, transferring weight onto the front leg, then holds a balanced high follow-through. "
    "Natural daylight, sharp detail, no camera movement, no zoom.",
    "bowling-side-on.mp4": "Photorealistic broadcast-quality video of a professional right-arm fast bowler in a real cricket stadium. "
    "Clothing: plain white cricket shirt, plain white cricket trousers, white spiked shoes. NO leg pads, NO batting pads, NO helmet, NO gloves, NO bat - only a red cricket ball in the right hand. "
    "Setting: a 22-yard cricket pitch of light brown rolled turf with white crease lines, running horizontally left to right across the frame; three wooden stumps with bails stand on the popping-crease end at the right side of the frame. "
    "Background: lush green outfield, white boundary rope, white sight screen and spectator stands far behind, clear blue sky, bright afternoon sun. "
    "Camera: static tripod at hip height, exactly side-on and perpendicular to the pitch, about 12 metres from the bowler, whole body always in frame. "
    "Action: the bowler runs in from the left along the pitch toward the stumps on the right, leaps into the gather, lands back foot then front foot next to the stumps with a braced front leg, "
    "swings the bowling arm straight over the top and releases the ball down the pitch toward the right, then follows through. "
    "Natural daylight, sharp detail, realistic human motion, no camera movement, no zoom, no cuts.",
}


def gen(name, prompt):
    r = requests.post(f"{CONTROL}/proxy", headers={**H, "X-Fal-Target-Url": f"https://queue.fal.run/{EP}"}, timeout=60,
                      json={"prompt": prompt, "negative_prompt": NEG, "duration": "4", "aspect_ratio": "16:9", "generate_audio": False})
    if r.status_code == 402:
        sys.exit("Insufficient Universal Key balance")
    r.raise_for_status()
    sub = r.json()
    deadline = time.time() + 900
    while time.time() < deadline:
        try:
            s = requests.get(sub["status_url"], headers=H, timeout=30)
        except requests.RequestException:
            time.sleep(3); continue
        st = (s.json().get("status") or "").upper()
        if st in {"COMPLETED", "OK"}:
            res = requests.get(sub["response_url"], headers=H, timeout=60).json()
            url = res["video"]["url"]
            with open(OUT + name, "wb") as f:
                f.write(requests.get(url, timeout=120).content)
            return f"{name}: saved"
        if st in {"FAILED", "CANCELLED", "CANCELED", "ERROR"}:
            return f"{name}: failed {s.text[:300]}"
        time.sleep(5)
    return f"{name}: timeout"


if __name__ == "__main__":
    with ThreadPoolExecutor(2) as ex:
        only = sys.argv[1:] or list(CLIPS)
        for line in ex.map(lambda kv: gen(*kv), [(k, CLIPS[k]) for k in only]):
            print(line, flush=True)
