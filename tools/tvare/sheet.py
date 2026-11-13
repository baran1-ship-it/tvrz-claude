import json, sys, os
from PIL import Image, ImageDraw
spec = json.load(open("/home/claude/tv/scripts/tvare_spec.json"))
ids = [i for i in spec if os.path.exists(f"/home/claude/tv/out/{i}_pred.png")]
if len(sys.argv) > 2: ids = ids[int(sys.argv[2]):int(sys.argv[3])]
W, H = 380, 440; cols = 4
rows = (len(ids) + cols - 1) // cols
sh = Image.new("RGB", (W * 2 * cols, (H + 24) * rows), "white"); d = ImageDraw.Draw(sh)
for n, i in enumerate(ids):
    x = (n % cols) * W * 2; y = (n // cols) * (H + 24)
    for j, v in enumerate(("pred", "profil")):
        sh.paste(Image.open(f"/home/claude/tv/out/{i}_{v}.png").convert("RGB"), (x + j * W, y + 24))
    s = spec[i]; d.text((x + 8, y + 6), f"{i[4:]} – {s['role']}, {s['vek_let']} let", fill=(0, 0, 0))
sh.save(sys.argv[1], quality=85)
