"""Import textur stromů (sdílené hra/modely/stromy/tex): VRAM komprese, barva listí ≤ 1024 px, normály a kůra ≤ 512 px
(chyba #4: textury stromů nekomprimované → VRAM 1430 MB; 2. 11. nové dřeviny bez nastavení: VRAM 190 → 414 MB).
Spustit po godot --import, pak znovu godot --import. python3 import_stromy.py <koren>"""
import sys, re, glob
import numpy as np
from PIL import Image
K = sys.argv[1]; n = 0
for f in glob.glob(K + "/hra/modely/stromy/tex/*.png.import") + glob.glob(K + "/hra/modely/stromy/tex/*.jpg.import"):
    s = open(f).read()
    if "compress/mode=2" in s: continue
    im = np.asarray(Image.open(f[:-7]).convert("RGBA").resize((64, 64))).astype(float) / 255
    a = im[..., 3] > 0.5
    normala = a.any() and im[a][:, 2].mean() > 0.7 and abs(im[a][:, 0].mean() - 0.5) < 0.12
    listi = (im[..., 3] < 0.5).mean() > 0.1
    px = 512 if normala or not listi else 1024
    s = re.sub(r"compress/mode=\d+", "compress/mode=2", s); s = re.sub(r"process/size_limit=\d+", "process/size_limit=%d" % px, s)
    if normala: s = re.sub(r"compress/normal_map=\d+", "compress/normal_map=1", s)
    open(f, "w").write(s); n += 1; print(f.split("/")[-1], "normála" if normala else ("listí" if listi else "kůra"), px)
print("upraveno", n)
