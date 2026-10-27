"""Mapa dohledu z pohledu hrace (krok C bod 7, radce 19:35): body po cestach po 50 m a mrizka 100 m pres mapu, oci
1,7 m (pesi) a 2,4 m (jezdec); z kazdeho bodu 16 smeru, paprsek nad terenem a korunami stromu do 1500 m. Vystup:
build/vyhledy.json (bod, vyska oci, dohled po smerech) a build/vyhledy.png (mapa: zelena = zavreno do 150 m, zluta do
300 m, cervena = dohled > 300 m mimo zaznamy vyhledu v lokace.json kompozice). Pouziva data, ne snimky (sekundy):
  - teren: tools/krok_b/vysky.json (5 m, fort.land pred vodou) - dost na kopce a hrbety;
  - koruny: modely/svet.json rostliny skupiny strom (druhy.json) jako valec polomeru 0,3 vysky, vyska koruny 0,35-1,0 h;
  - stavby: lokace (domy vsi, hostinec, stan, mlyn) jako kvadry 6 m.
  python3 tools/mapa_vyhledu.py [--krok 100] [--max 300]"""
import json
import math
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = 5.0
arg = sys.argv[1:]
KROK = float(arg[arg.index("--krok") + 1]) if "--krok" in arg else 100.0
MAXD = float(arg[arg.index("--max") + 1]) if "--max" in arg else 300.0

vys = json.load(open(os.path.join(ROOT, "tools", "krok_b", "vysky.json")))
nx, nz, X0, Z0 = vys["nx"], vys["nz"], vys["X0"], vys["Z0"]
H = np.array(vys["h"], dtype=np.float32).reshape(nz, nx)
KOR = np.zeros_like(H)                       # vyska prekazky nad terenem (koruny, stavby)
dr = {d["id"]: d for d in json.load(open(os.path.join(ROOT, "pravidla", "svet", "druhy.json")))["druhy"]}
ids = sorted(dr, key=len, reverse=True)


def druh(k):
    for i in ids:
        if k == i or re.fullmatch(re.escape(i) + r"(_\d+|_daleko2?)*", k):
            return i
    return None


svet = json.load(open(os.path.join(ROOT, "modely", "svet.json")))
VYSKY_MODELU = {}
nstrom = 0
for k, arr in svet["rostliny"].items():
    i = druh(k)
    if i is None or dr[i]["skupina"] != "strom" or "daleko" in k:
        continue
    for m in arr:
        sx = math.sqrt(m[0] ** 2 + m[4] ** 2 + m[8] ** 2)       # meritko (vyska v m pro karty ~ model 1 m) - odhad
        sy = math.sqrt(m[1] ** 2 + m[5] ** 2 + m[9] ** 2)
        h = max(4.0, min(30.0, sy * (12.0 if sy < 3.0 else 1.0)))
        r = max(2.0, 0.3 * h)
        x, z = m[3], m[11]
        i0, i1 = int((x - r - X0) / K), int((x + r - X0) / K) + 1
        j0, j1 = int((z - r - Z0) / K), int((z + r - Z0) / K) + 1
        i0, j0 = max(0, i0), max(0, j0)
        KOR[j0:min(nz, j1), i0:min(nx, i1)] = np.maximum(KOR[j0:min(nz, j1), i0:min(nx, i1)], h)
        nstrom += 1
lok = json.load(open(os.path.join(ROOT, "pravidla", "svet", "lokace.json")))
for c in [u["novy_stred"] for u in lok["ves"]["usedlosti"]] + [s["stred"] for s in lok["stavby"]]:
    i, j = int((c[0] - X0) / K), int((c[1] - Z0) / K)
    KOR[max(0, j - 1):j + 2, max(0, i - 1):i + 2] = np.maximum(KOR[max(0, j - 1):j + 2, max(0, i - 1):i + 2], 6.0)
TOP = H + KOR


def vyska(x, z, pole):
    i, j = (x - X0) / K, (z - Z0) / K
    i0, j0 = np.clip(i.astype(int), 0, nx - 2), np.clip(j.astype(int), 0, nz - 2)
    fi, fj = np.clip(i - i0, 0, 1), np.clip(j - j0, 0, 1)
    return (pole[j0, i0] * (1 - fi) + pole[j0, i0 + 1] * fi) * (1 - fj) + (pole[j0 + 1, i0] * (1 - fi) + pole[j0 + 1, i0 + 1] * fi) * fj


def dohled(px, pz, oko):
    """16 smeru: vzdalenost, kde paprsek (vodorovne, uhel 0 a +1 st.) narazi na teren / koruny."""
    y0 = vyska(np.array([px]), np.array([pz]), H)[0] + oko
    d = np.arange(10.0, 1500.0, 5.0)
    out = []
    for k in range(16):
        a = k * math.pi / 8
        xs, zs = px + math.sin(a) * d, pz + math.cos(a) * d
        uvnitr = (xs > X0) & (xs < X0 + (nx - 1) * K) & (zs > Z0) & (zs < Z0 + (nz - 1) * K)
        t = vyska(xs, zs, TOP)
        # vyhled pres prekazku jen kdyz je pod zornym paprskem (mirne dolu az 1 st. nahoru = obzor)
        hit = uvnitr & (t > y0 + d * math.tan(math.radians(0.5)))
        out.append(float(d[np.argmax(hit)]) if hit.any() else (float(d[np.argmax(~uvnitr)]) if (~uvnitr).any() else 1500.0))
    return out


body = []
cesty = json.load(open(os.path.join(ROOT, "pravidla", "svet", "cesty.json")))
for e in cesty["vozove"] + cesty["pesiny"]:
    acc, last = 0.0, None
    for p in e["osa"]:
        if last is not None:
            acc += math.hypot(p[0] - last[0], p[1] - last[1])
        if last is None or acc >= 50.0:
            body.append(("cesta:" + e["id"], p[0], p[1]))
            acc = 0.0
        last = p
xs = np.arange(X0 + KROK / 2, X0 + (nx - 1) * K, KROK)
zs = np.arange(Z0 + KROK / 2, Z0 + (nz - 1) * K, KROK)
for x in xs:
    for z in zs:
        body.append(("mrizka", float(x), float(z)))
vyhledy = lok.get("kompozice", {}).get("vyhledy", [])


def zamerny(x, z):
    return any(math.hypot(x - v["stred"][0], z - v["stred"][1]) < v.get("polomer_m", 30.0) for v in vyhledy)


out = []
otevrene = 0
for typ, x, z in body:
    for oko in (1.7, 2.4):
        dl = dohled(x, z, oko)
        mx = max(dl)
        chyba = mx > MAXD and not zamerny(x, z)
        otevrene += chyba
        out.append({"typ": typ, "x": round(x, 1), "z": round(z, 1), "oko": oko, "dohled": [round(v) for v in dl], "max": round(mx), "chyba": chyba})
os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "build", "vyhledy.json"), "w"))
try:
    from PIL import Image, ImageDraw
    sc = 0.5
    W, Hh = int((nx - 1) * K * sc), int((nz - 1) * K * sc)
    im = Image.new("RGB", (W, Hh), (30, 30, 30))
    g = (H - H.min()) / max(1e-3, (H.max() - H.min()))
    tim = Image.fromarray((np.flipud(g) * 180 + 40).astype(np.uint8)).resize((W, Hh))
    im.paste(Image.merge("RGB", (tim, tim, tim)))
    kor = Image.fromarray((np.flipud(KOR > 3.0) * 255).astype(np.uint8)).resize((W, Hh))
    im.paste((40, 90, 40), mask=kor.point(lambda v: 90 if v > 128 else 0))
    dw = ImageDraw.Draw(im)
    for o in out:
        if o["oko"] != 2.4:
            continue
        px, pz = (o["x"] - X0) * sc, Hh - (o["z"] - Z0) * sc
        c = (220, 40, 40) if o["chyba"] else ((230, 200, 40) if o["max"] > 150 else (60, 200, 60))
        dw.ellipse([px - 4, pz - 4, px + 4, pz + 4], fill=c)
    im.save(os.path.join(ROOT, "build", "vyhledy.png"))
except ImportError:
    pass
print("VYHLEDY bodu %d (cesty + mrizka %d m), stromu %d, dohled > %d m mimo zamerne vyhledy: %d z %d" %
      (len(body), KROK, nstrom, MAXD, otevrene, len(out)))
for typ in sorted({o["typ"] for o in out}):
    s = [o for o in out if o["typ"] == typ]
    print("VYHLEDY %-38s bodu %4d  otevreno %4d  (oci 1,7: %d, 2,4: %d)" % (typ, len(s) // 2, sum(o["chyba"] for o in s),
          sum(o["chyba"] for o in s if o["oko"] == 1.7), sum(o["chyba"] for o in s if o["oko"] == 2.4)))
