"""Portaly hostince (radce 15:30): okna a dvere z blender/hostinec.py (OKNA, DVERE, MISTNOSTI) do souradnic sveta
-> modely/portaly.json {mistnost: {"box": [min, max] v modelu, "portaly": [[x, y, z, nx, ny, nz, sirka, vyska, soused]]}}.
Hra (predmety.gd) kresli predmety mistnosti jen kdyz je hrac v ni, v sousedni pres dvere, nebo venku do 25 m a vidi
nekterym oknem/dvermi dovnitr.   /opt/bl/bin/python tools/portaly.py"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "blender"))
import bpy  # noqa: F401,E402
import hostinec  # noqa: E402
import kraj  # noqa: E402

d = json.load(open(os.path.join(ROOT, "modely", "svet.json")))
st = [s for s in d["staticke"] if s["id"] == "hostinec"][0]
y0 = st["p"][1]
yaw = kraj.stavba_yaw("hostinec")


def svet(bx, by, bz):
    x, z = kraj.stavba_bod("hostinec", bx, by)
    return [round(x, 3), round(y0 + bz, 3), round(z, 3)]


def smer(dbx, dby):
    a = kraj.stavba_bod("hostinec", dbx, dby)
    o = kraj.stavba_bod("hostinec", 0.0, 0.0)
    v = (a[0] - o[0], a[1] - o[1])
    ln = math.hypot(*v) or 1.0
    return [round(v[0] / ln, 4), 0.0, round(v[1] / ln, 4)]


mist = {}
for nm, x0, x1, ya, yb, za, zb, _ in hostinec.MISTNOSTI:
    mist[nm] = {"box": [[x0, ya, za], [x1, yb, zb]], "portaly": []}


def kde(bx, by, bz):
    out = []
    for nm, m in mist.items():
        (a, b) = m["box"]
        if a[0] - 0.01 <= bx <= b[0] + 0.01 and a[1] - 0.01 <= by <= b[1] + 0.01 and a[2] <= bz <= b[2]:
            out.append(nm)
    return out


def otvor(osa, rov, ven, u0, u1, z0, z1, dvere):
    um = (u0 + u1) / 2
    zm = (z0 + z1) / 2
    if osa == "y":
        bx, by = um, rov
        n = (0.0, ven)
    else:
        bx, by = rov, um
        n = (ven, 0.0)
    uvnitr = kde(bx - n[0] * 0.3, by - n[1] * 0.3, zm)
    venku = kde(bx + n[0] * 0.3, by + n[1] * 0.3, zm)
    p = svet(bx, by, zm)
    nn = smer(n[0], n[1])
    for nm in uvnitr:
        mist[nm]["portaly"].append(p + nn + [round(u1 - u0, 2), round(z1 - z0, 2), venku[0] if venku else ""])
    for nm in venku:
        mist[nm]["portaly"].append(p + [-nn[0], 0.0, -nn[2]] + [round(u1 - u0, 2), round(z1 - z0, 2), uvnitr[0] if uvnitr else ""])


for o in hostinec.OKNA:
    otvor(*o, dvere=False)
for dv in hostinec.DVERE:
    otvor(*dv[:7], dvere=True)
out = {"hostinec_" + k: v for k, v in mist.items()}
json.dump(out, open(os.path.join(ROOT, "modely", "portaly.json"), "w"), indent=1)
for k, v in out.items():
    print(k, len(v["portaly"]), [p[8] for p in v["portaly"]])
