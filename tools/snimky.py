"""Snimky a cisla z referencnich mist po kazdem kroku: docs/screens/<stitek>_<misto>.jpg + tabulka do docs/stav.md.

Pouziti:  python3 tools/snimky.py K1 "popis zmeny jednou vetou"
Mereni: Compatibility (jako tablet), kvalita 1, 1200x800, prumer 30 snimku (main.gd _mereni)."""
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MISTA = [  # nazev souboru, popis, x, z, cil x, cil z
    ("tvrz", "tvrz nadvori", -4, 4, -4, -10),
    ("louka", "louka u tvrze", 60, 200, 60, 320),
    ("vesnice", "vesnice", 470, 830, 520, 860),
    ("skaly", "skalni mesto", -185, 535, -195, 560),
    ("hostinec", "hostinec ke skalam", -62, 881, -150, 881),
    ("potok", "potok u mostu", 222, 604, 240, 600),
    # zblizka (textury): cesta, zed tvrze
    ("cesta", "cesta zblizka", 470, 845, 470, 852),
    ("zed", "zed tvrze zblizka", 0, 30, 0, 20),
]


def main():
    stitek = sys.argv[1]
    popis = sys.argv[2] if len(sys.argv) > 2 else ""
    tmp = tempfile.mkdtemp()
    spec = "|".join("%s;%g,%g,%g,%g;%s" % (p, x, z, tx, tz, os.path.join(tmp, f + ".png")) for f, p, x, z, tx, tz in MISTA)
    env = dict(os.environ, TVRZ_MERENI=spec)
    out = subprocess.run(["timeout", "2400", "xvfb-run", "-a", "-s", "-screen 0 1200x800x24", "godot", "--path", ROOT,
                          "--rendering-driver", "opengl3", "--rendering-method", "gl_compatibility", "--resolution", "1200x800"],
                         env=env, capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        m = re.match(r"MERENI (.+?)\s+kresleni\s+(\d+)\s+troj\s+([\d.]+) M\s+objekty\s+\d+\s+gpu\s+(\d+) MB \(textury (\d+), buffery (\d+)\)", line)
        if m:
            rows.append(m.groups())
    sd = os.path.join(ROOT, "docs", "screens")
    os.makedirs(sd, exist_ok=True)
    for f, *_ in MISTA:
        src = os.path.join(tmp, f + ".png")
        if os.path.exists(src):
            Image.open(src).convert("RGB").save(os.path.join(sd, "%s_%s.jpg" % (stitek, f)), quality=85)
    tab = ["", "## %s – měření na PC (Compatibility, kvalita 1, 1200×800)" % stitek, ""]
    if popis:
        tab += [popis, ""]
    tab += ["| Místo | Kreslení | Troj. | GPU (textury / buffery) |", "|---|---|---|---|"]
    for p, dc, tr, gpu, tx, bf in rows:
        tab.append("| %s | %s | %s M | %s MB (%s / %s) |" % (p.strip(), dc, tr, gpu, tx, bf))
    tab.append("")
    tab.append("Snímky: docs/screens/%s_*.jpg" % stitek)
    with open(os.path.join(ROOT, "docs", "stav.md"), "a") as fh:
        fh.write("\n".join(tab) + "\n")
    print("\n".join(tab))


if __name__ == "__main__":
    main()
