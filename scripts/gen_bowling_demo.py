"""One-off: bowling demo clip (no pads, release at the bowling crease) via fal.ai Universal Key.
nano-banana-pro start frame -> nano-banana-pro/edit end frame -> Kling v3 Pro image-to-video (start+end frames).
Run: python scripts/gen_bowling_demo.py start | end <start_url> | video <start_url> <end_url>"""
import os, sys, time, json, requests
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
KEY = os.environ["EMERGENT_LLM_KEY"]
# Fal Universal Key supports queue inference through Emergent proxy, not Platform APIs.
CONTROL = os.environ.get("INTEGRATION_PROXY_URL", "https://integrations.emergentagent.com").rstrip("/") + "/api/v1/fal"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
OUT = "/app/scripts/out/"

KIT = ("He wears ONLY a plain white long-sleeve cricket shirt, plain white cricket trousers and white spiked shoes; "
       "NO leg pads, NO batting pads, NO helmet, NO gloves; bare head with short hair. ")
SCENE = ("Camera exactly side-on at hip height, about 12 metres away, perpendicular to the pitch, static. "
         "The bowler's own end of the pitch fills the frame: in the CENTRE-RIGHT of the frame stand three wooden stumps with bails on the bowling crease, "
         "with the white popping crease line painted on the turf just in front of them (to the right). The rest of the 22-yard light-brown pitch continues off the right edge of the frame toward the far batsman. "
         "Background: green outfield, white boundary rope, white sight screen, packed spectator stands, blue sky, bright afternoon sun. "
         "Whole body in frame, sharp detail, no text, no logos, no watermark. ")
START = ("Photorealistic broadcast sports photo, 16:9. A right-arm fast bowler in a cricket stadium, two strides before the bowling crease, "
         "on the left-centre of the frame, running toward the right, red ball in his right hand held near his chest. " + KIT + SCENE)
END = ("Edit this photo: keep the same bowler, same clothes (no pads, no helmet, no gloves), same camera position, same stadium, same stumps and crease lines. "
       "Change only his pose to the exact moment of ball release in a classic side-on fast-bowling action: his braced, straight front (left) leg is planted on the popping crease right beside the stumps, "
       "his right bowling arm is fully straight and vertical directly above his head, the red ball just leaving his fingertips at the top of the arc, "
       "his left arm is pulled down and tucked into his side, chest and head facing down the pitch to the right, back foot dragging behind him.")
VID = ("Static side-on camera, no camera movement, no pan, no zoom, no cuts. The fast bowler takes his last strides toward the stumps, leaps into the gather, "
       "lands his back foot, then plants a straight braced front leg on the popping crease right beside the stumps while his right bowling arm swings in a full circle "
       "straight over the top of his head, ending at the release point with the arm vertical and the red ball leaving his fingertips. " + KIT +
       "Realistic, athletic fast-bowling motion, natural daylight.")
NEG = "leg pads, batting pads, knee pads, shin guards, helmet, gloves, bat, batsman, wicketkeeper, camera pan, camera tracking, camera movement, zoom, text, watermark, logo, blur, distortion, extra limbs, cartoon"


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


def save_images(res, prefix):
    for i, im in enumerate(res["images"]):
        open(f"{OUT}{prefix}_{i}.png", "wb").write(requests.get(im["url"], timeout=120).content)
        print(f"{prefix}_{i}.png", im["url"], flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    mode = sys.argv[1]
    if mode == "start":
        save_images(run("fal-ai/nano-banana-pro", {"prompt": START, "num_images": 2, "aspect_ratio": "16:9", "resolution": "2K", "output_format": "png"}), "start")
    elif mode == "end":
        save_images(run("fal-ai/nano-banana-pro/edit", {"prompt": END, "image_urls": [sys.argv[2]], "num_images": 1, "aspect_ratio": "16:9", "resolution": "2K", "output_format": "png"}), "end")
    else:
        res = run("fal-ai/kling-video/v3/pro/image-to-video", {"start_image_url": sys.argv[2], "end_image_url": sys.argv[3], "prompt": VID,
                                                              "negative_prompt": NEG, "duration": "4", "cfg_scale": 0.7, "generate_audio": False})
        open(f"{OUT}bowling_raw.mp4", "wb").write(requests.get(res["video"]["url"], timeout=180).content)
        print("bowling_raw.mp4 saved", flush=True)
