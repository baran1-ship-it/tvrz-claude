"""Textury pro tablet bez zdrojovych souboru (radce 20:45 krok 4, cil <= 300 MB): v hotovych ETC2 .ctex
(.godot/imported, z baliku) odstrihne nejvetsi mip urovne, dokud textura nesplni limit. Jen ETC2 (tablet);
PC (S3TC) beze zmeny. Vystup: seznam zmenenych souboru build/textury_tablet.txt pro tools/pck_textury.gd.
  python3 tools/textury_tablet.py [--suchy]
Limity: rostliny (mimo stromy a skaly) a predmety 512, ostatni 1024 (stromy, skaly, teren, stavby)."""
import glob
import os
import re
import struct
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
STROMY = ("smrk", "dub", "lipa", "briza", "buk", "olse", "vrba", "borovice", "skala_", "impostor")
SUCHY = "--suchy" in sys.argv


def limit(src):
    p = src.replace("res://", "")
    n = os.path.basename(p)
    if p.startswith("modely/rostliny/") and not n.startswith(STROMY):
        return 512
    if p.startswith("modely/predmety/"):
        return 512
    if p.startswith("obrazky/impostory/"):
        return 0
    return 1024


def ctex_info(b):
    if b[:4] != b"GST2":
        return None
    w, h = struct.unpack("<II", b[8:16])
    df, iw, ih, mips, fmt = struct.unpack("<IHHII", b[36:52])
    return w, h, df, iw, ih, mips, fmt


def level_sizes(iw, ih, mips, total):
    for bs in (8, 16):
        s = []
        w, h = iw, ih
        for _ in range(mips + 1):
            s.append(max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * bs)
            w, h = max(1, w // 2), max(1, h // 2)
        if sum(s) == total:
            return s
    return None


zmeny = []
pred = po = 0
for imp in glob.glob("**/*.import", recursive=True):
    if imp.startswith((".godot", "build", "apk", "data")):
        continue
    t = open(imp, encoding="utf-8", errors="ignore").read()
    m = re.search(r'path\.etc2="res://(\.godot/imported/[^"]+\.etc2\.ctex)"', t)
    if not m:
        continue
    f = m.group(1)
    if not os.path.exists(f):
        continue
    lim = limit(imp[:-len(".import")])
    b = open(f, "rb").read()
    inf = ctex_info(b)
    pred += len(b)
    if not inf or not lim or inf[2] != 0:
        po += len(b)
        continue
    w, h, df, iw, ih, mips, fmt = inf
    data = b[52:]
    ls = level_sizes(iw, ih, mips, len(data))
    if ls is None:
        po += len(b)
        continue
    off = 0
    while max(iw, ih) > lim and mips > 0:
        off += ls[0]
        ls = ls[1:]
        iw, ih, w, h, mips = iw // 2, ih // 2, max(1, w // 2), max(1, h // 2), mips - 1
    if off == 0:
        po += len(b)
        continue
    nb = b[:8] + struct.pack("<II", w, h) + b[16:36] + struct.pack("<IHHII", df, iw, ih, mips, fmt) + data[off:]
    po += len(nb)
    zmeny.append(f)
    if not SUCHY:
        open(f, "wb").write(nb)
os.makedirs("build", exist_ok=True)
if not SUCHY:
    # seznam se jen doplnuje (druhy beh uz nic nezmeni a nesmi seznam vymazat)
    st = set(open("build/textury_tablet.txt").read().split()) if os.path.exists("build/textury_tablet.txt") else set()
    open("build/textury_tablet.txt", "w").write("\n".join(sorted(st | set(zmeny))) + "\n")
print("textury tablet: %d zmeneno, ETC2 %.0f MB -> %.0f MB%s" % (len(zmeny), pred / 1048576, po / 1048576, " (suchy beh)" if SUCHY else ""))
