"""Overi, ze kazdy obrazek (png, jpg) pod danou slozkou jde cely nacist (useknuty soubor = chyba). tools/export.sh
po exportu (28. 10.: plny disk, export zapsal 150 textur useknutych a skoncil OK).
  python3 tools/over_obrazky.py modely"""
import os
import sys

from PIL import Image

spatne = []
n = 0
for koren, _, soubory in os.walk(sys.argv[1] if len(sys.argv) > 1 else "modely"):
    for f in soubory:
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            p = os.path.join(koren, f)
            n += 1
            try:
                with Image.open(p) as im:
                    im.load()
            except Exception as e:  # noqa: BLE001
                spatne.append((p, str(e)))
for p, e in spatne:
    print("POSKOZENY", p, e)
print("obrazky: %d overeno, poskozenych %d" % (n, len(spatne)))
sys.exit(1 if spatne else 0)
