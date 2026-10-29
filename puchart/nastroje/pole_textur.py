"""Složí fotky půd (Poly Haven, CC0) do svislého pruhu pro import Godotu jako Texture2DArray.
Pořadí vrstev = pravidla/svet/pudy.json. Výstup: hra/textury/pudy_a.png, pudy_n.png (1024 px na vrstvu).
"""
import sys, os, json, glob
from PIL import Image
koren = sys.argv[1]
PU = json.load(open(os.path.join(koren, "pravidla/svet/pudy.json")))
d = os.path.join(koren, "hra/textury/zem")
for druh, vzor in (("a", "_diff"), ("n", "_nor_gl")):
    vrstvy = []
    for v in PU["vrstvy"]:
        f = [g for g in glob.glob(os.path.join(d, v["foto"] + "*_1k.jpg")) if (vzor in g if druh == "n" else ("_diff" in g))]
        assert f, v["foto"]
        vrstvy.append(Image.open(f[0]).convert("RGB").resize((1024, 1024), Image.LANCZOS))
    out = Image.new("RGB", (1024, 1024 * len(vrstvy)))
    for i, im in enumerate(vrstvy): out.paste(im, (0, 1024 * i))
    out.save(os.path.join(koren, f"hra/textury/pudy_{druh}.png"))
print("vrstev", len(PU["vrstvy"]))
