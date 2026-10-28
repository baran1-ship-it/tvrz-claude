"""Mapa stavby a chyb (Misa 28. 10.: „at ti to pomaha stavet a lepe hledat chyby, at ti to ukazuje co a jak“).

Z build/protokol_stavby.json (svet.gd: ktery krok zmenil teren, kde a o kolik) nakresli pohled shora: bunky 8 m
obarvene podle kroku (jas = velikost zmeny), osy toku z voda.json (modre), osy cest, jak je postavila hra (hnede) a chyby
testu z logu (radky "<DRUH> <druh> (x, z) ..." - ZASAZENI, KORYTO, SIT, ZABER): cerveny krizek s cislem, legenda
dole. Vystup build/mapa_stavby[_<oblast>].png.

  python3 tools/protokol_mapa.py [--oblast x0,z0,x1,z1] [--log build/beh/testy_X_godot.log ...]
Bez --oblast: obdelnik pres vsechny zmeny a chyby.
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BARVY = [(230, 159, 0), (86, 180, 233), (0, 158, 115), (240, 228, 66), (0, 114, 178), (213, 94, 0), (204, 121, 167),
         (120, 120, 120), (150, 90, 40), (90, 160, 60), (170, 70, 170), (60, 170, 170), (200, 200, 90), (110, 80, 200)]
CHYBA_RE = re.compile(r"^(ZASAZENI|KORYTO|SIT|ZABER|ZAMEK|MLYN)\s+(\S+)\s+\((-?[\d.]+),\s*(-?[\d.]+)\)\s*(.*)$")


def arg(nm, default=None):
    if nm in sys.argv:
        return sys.argv[sys.argv.index(nm) + 1]
    return default


def main():
    pj = json.load(open(os.path.join(ROOT, "build", "protokol_stavby.json")))
    prot = pj["kroky"]
    chyby = []
    for i, a in enumerate(sys.argv):
        if a == "--log":
            for ln in open(sys.argv[i + 1], errors="replace"):
                m = CHYBA_RE.match(ln.strip())
                if m:
                    chyby.append((m.group(1), m.group(2), float(m.group(3)), float(m.group(4)), m.group(5)[:60]))
    obl = arg("--oblast")
    if obl:
        x0, z0, x1, z1 = [float(v) for v in obl.split(",")]
    else:
        xs, zs = [], []
        for z in prot:
            for c in z["bunky"]:
                cx, cz = [int(v) for v in c.split(",")]
                xs.append(cx * 8)
                zs.append(cz * 8)
        for c in chyby:
            xs.append(c[2])
            zs.append(c[3])
        x0, x1, z0, z1 = min(xs) - 20, max(xs) + 28, min(zs) - 20, max(zs) + 28
    px = max(1.0, min(4.0, 1600.0 / max(x1 - x0, z1 - z0)))
    W, H = int((x1 - x0) * px), int((z1 - z0) * px)
    leg_h = 18 * (len(prot) + 2) + 18 * min(len(chyby), 30)
    img = Image.new("RGB", (max(W, 900), H + leg_h), (245, 242, 232))
    d = ImageDraw.Draw(img)

    def p(x, z):
        return (x - x0) * px, (z - z0) * px

    for k, z in enumerate(prot):
        b = BARVY[k % len(BARVY)]
        for c, dy in z["bunky"].items():
            cx, cz = [int(v) for v in c.split(",")]
            if cx * 8 + 8 < x0 or cx * 8 > x1 or cz * 8 + 8 < z0 or cz * 8 > z1:
                continue
            a = min(1.0, 0.35 + float(dy) / 1.5)
            col = tuple(int(245 + (bb - 245) * a) for bb in b)
            d.rectangle([p(cx * 8, cz * 8), p(cx * 8 + 8, cz * 8 + 8)], fill=col)
    voda = json.load(open(os.path.join(ROOT, "pravidla", "svet", "voda.json")))
    for t in voda["toky"]:
        d.line([p(q[0], q[1]) for q in t["osa_xzy"]], fill=(30, 90, 200), width=max(1, int(px * t["sirka_m"])))
    for body in pj.get("cesty", []):
        if len(body) > 1:
            d.line([p(q[0], q[1]) for q in body], fill=(140, 100, 60), width=max(1, int(px * 1.5)))
    for n, c in enumerate(chyby):
        x, y = p(c[2], c[3])
        r = 5
        d.line([x - r, y - r, x + r, y + r], fill=(220, 0, 0), width=2)
        d.line([x - r, y + r, x + r, y - r], fill=(220, 0, 0), width=2)
        d.text((x + 6, y - 6), str(n + 1), fill=(160, 0, 0))
    y = H + 6
    d.text((6, y), "oblast x %.0f..%.0f, z %.0f..%.0f (%.1f px/m); bunky 8 m = krok, ktery zmenil teren" % (x0, x1, z0, z1, px), fill=(0, 0, 0))
    y += 18
    for k, z in enumerate(prot):
        d.rectangle([6, y + 2, 20, y + 14], fill=BARVY[k % len(BARVY)])
        d.text((26, y), "%s: %d vrcholu, max dy %.2f m, %s" % (z["krok"], z["vrcholu"], z["max_dy"], ", ".join(z["site"])[:90]), fill=(0, 0, 0))
        y += 18
    for n, c in enumerate(chyby[:30]):
        d.text((6, y), "%d  %s %s (%.0f, %.0f) %s" % (n + 1, c[0], c[1], c[2], c[3], c[4]), fill=(160, 0, 0))
        y += 18
    jm = "mapa_stavby" + ("_" + obl.replace(",", "_") if obl else "") + ".png"
    out = os.path.join(ROOT, "build", jm)
    img.save(out)
    # kopie k snimkum s otiskem exportu (radce 28. 10. 16:40: mapa vedle snimku, Misa a radce ji vidi pred tabletem)
    try:
        ot = json.load(open(os.path.join(ROOT, "data_manifest.json"))).get("otisk", "")[:10] or "bez_otisku"
    except (OSError, ValueError):
        ot = "bez_otisku"
    os.makedirs(os.path.join(ROOT, "docs", "screens"), exist_ok=True)
    img.convert("P", palette=Image.ADAPTIVE, colors=64).save(os.path.join(ROOT, "docs", "screens", jm.replace(".png", "_%s.png" % ot)), optimize=True)
    print("MAPA %s: %d kroku, %d chyb" % (out, len(prot), len(chyby)))


if __name__ == "__main__":
    main()
