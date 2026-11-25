"""Textury kone Hero Horse (tools/kun_hero.py): TIF 4096/2048 z balicku -> PNG pro hru (telo 1024, hriva 512 s alfou,
postroj 1024 s alfou). TIF ma alfu jako 4. kanal (tifffile; PIL ani Blender bez okna ji tady neprectou).
  python3 tools/kun_hero_tex.py <rozbaleny_archiv>"""
import os
import sys

import tifffile
from PIL import Image

SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modely", "kone", "kun_hero_tex")
os.makedirs(OUT, exist_ok=True)
POLOZKY = [("Horse_%s" % s, "srst_%s" % s.lower(), 1024) for s in ("Bay", "Black", "Chestnut", "Palomino", "White")]
POLOZKY += [("Horse_Hair_%s" % s, "hriva_%s" % s.lower(), 512) for s in ("Brown", "Black", "Palomino", "White")]
POLOZKY += [("Horse_Normals", "srst_normaly", 1024), ("Horse_Hair_Normals", "hriva_normaly", 512),
            ("Poor_Armor", "postroj", 1024), ("Poor_Armor_normals", "postroj_normaly", 1024)]
for tif, jm, px in POLOZKY:
    p = os.path.join(SRC, "Textures", tif + ".tif")
    if not os.path.exists(p):
        print("CHYBI", p)
        continue
    a = tifffile.imread(p)
    im = Image.fromarray(a[..., :4] if a.shape[-1] >= 4 else a[..., :3])
    im.resize((px, px), Image.LANCZOS).save(os.path.join(OUT, jm + ".png"), optimize=True)
    print("TEX", jm, im.mode, px)
