"""One-off: bowling demo clip (no pads) via fal.ai Universal Key: nano-banana-pro start frame -> Kling v3 Pro image-to-video.
Run: python scripts/gen_bowling_demo.py image   |   python scripts/gen_bowling_demo.py video <start_image_url>"""
import os, sys, time, json, requests
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
KEY = os.environ["EMERGENT_LLM_KEY"]
# Fal Universal Key supports queue inference through Emergent proxy, not Platform APIs.
CONTROL = os.environ.get("INTEGRATION_PROXY_URL", "https://integrations.emergentagent.com").rstrip("/") + "/api/v1/fal"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
OUT = "/app/scripts/out/"

KIT = ("He wears ONLY a plain white long-sleeve cricket shirt, plain white cricket trousers and white spiked shoes. "
       "He is NOT wearing leg pads, NOT wearing batting pads, NOT wearing a helmet, NOT wearing gloves; both legs show only white trousers; bare head with short hair. ")
IMG_PROMPT = ("Photorealistic broadcast sports photo, 16:9. A right-arm fast bowler in mid run-up during a cricket match in a large stadium. " + KIT +
              "He holds a red cricket ball in his right hand. Camera exactly side-on at hip height, about 12 metres away, perpendicular to the pitch. "
              "The light-brown 22-yard pitch with white crease lines runs horizontally left to right across the middle of the frame; "
              "the bowler is on the left part of the frame running toward the right; three wooden stumps with bails stand at the bowling crease at the right of the frame. "
              "Background: green outfield, white boundary rope, a white sight screen and packed spectator stands, blue sky, bright afternoon sun. "
              "Whole body in frame, sharp detail, no text, no logos, no watermark.")
VID_PROMPT = ("The fast bowler runs in from left to right along the pitch, leaps into his gather, lands back foot then braced front foot at the crease next to the stumps, "
              "swings his right bowling arm straight over the top and releases the red ball down the pitch toward the right, then follows through. " + KIT +
              "Static side-on camera, no camera movement, no zoom, no cuts, realistic human motion, natural daylight.")
NEG = "leg pads, batting pads, knee pads, shin guards, helmet, gloves, bat, batsman, wicketkeeper, text, captions, watermark, logo, blur, distortion, extra limbs, camera movement, cartoon"


def run(endpoint, payload, timeout=900):
    r = requests.post(f"{CONTROL}/proxy", headers={**H, "X-Fal-Target-Url": f"https://queue.fal.run/{endpoint}"}, json=payload, timeout=60)
    if r.status_code == 402:
        sys.exit("Insufficient Universal Key balance")
    r.raise_for_status()
    sub = r.json()
    end = time.time() + timeout
    while time.time() < end:
        try:
            s = requests.get(sub["status_url"], headers=H, timeout=30).json()
        except requests.RequestException:
            time.sleep(3); continue
        st = (s.get("status") or "").upper()
        if st in {"COMPLETED", "OK"}:
            return requests.get(sub["response_url"], headers=H, timeout=60).json()
        if st in {"FAILED", "CANCELLED", "CANCELED", "ERROR"}:
            sys.exit(f"failed: {json.dumps(s)[:300]}")
        time.sleep(4)
    sys.exit("timeout")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "image":
        res = run("fal-ai/nano-banana-pro", {"prompt": IMG_PROMPT, "num_images": 2, "aspect_ratio": "16:9", "resolution": "2K", "output_format": "png"})
        for i, im in enumerate(res["images"]):
            open(f"{OUT}start_{i}.png", "wb").write(requests.get(im["url"], timeout=120).content)
            print(f"start_{i}.png", im["url"], flush=True)
    else:
        res = run("fal-ai/kling-video/v3/pro/image-to-video", {"start_image_url": sys.argv[2], "prompt": VID_PROMPT, "negative_prompt": NEG, "duration": "5", "generate_audio": False})
        open(f"{OUT}bowling_raw.mp4", "wb").write(requests.get(res["video"]["url"], timeout=180).content)
        print("bowling_raw.mp4 saved", flush=True)
