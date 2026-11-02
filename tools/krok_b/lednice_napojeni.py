"""Napojeni lednice (odpad z kola) na potok dilu mlyna jako zaznam (Misa 0.994 mlyn c (598, 904): schodovity teren
modelu Mlyn_Teren vycuhoval nad vodou prodlouzene lednice - kraj.py ji prodluzuje k ose toku, hra o tom useku nevedela).
Stejny vypocet jako kraj.voda (posledni bod lednice -> nejblizsi bod osy toku dilu v jeho hladine); zapis do
pravidla/svet/voda.json mlyn.dil.lednice_napojeni: a, b [x, hladina, z], sirka. Hra (svet._mlyn_dil) pod nim snizi teren
dilu na dno (hladina - hloubka_dno_m).
  /opt/bl/bin/python tools/krok_b/lednice_napojeni.py"""
import collections
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "blender"))
import bpy  # noqa: E402,F401
import kraj  # noqa: E402

u = kraj._MVODA["lednice"]
pts = [kraj.mlyn_svet(*p) for p in u["body"]]
tk = next(t for t in kraj.TOKY if t.id == kraj._MDIL["tok"])
ex, ey, ez = pts[-1]
j = min(range(len(tk.osa)), key=lambda i: math.hypot(tk.osa[i][0] - ex, tk.osa[i][1] - ez))
p = os.path.join(ROOT, "pravidla", "svet", "voda.json")
d = json.load(open(p), object_pairs_hook=collections.OrderedDict)
d["mlyn"]["dil"]["lednice_napojeni"] = {
    "a": [round(ex, 3), round(ey, 3), round(ez, 3)],
    "b": [round(tk.osa[j][0], 3), round(tk.hl[j], 3), round(tk.osa[j][1], 3)],
    "sirka": u["sirka"], "hloubka_dno_m": 0.3,
    "duvod": "tools/krok_b/lednice_napojeni.py: usek lednice od modelu k ose potoka (kraj.voda); hra pod nim snizi teren dilu"}
json.dump(d, open(p, "w"), ensure_ascii=False, indent=1)
print("LEDNICE napojeni", d["mlyn"]["dil"]["lednice_napojeni"]["a"], "->", d["mlyn"]["dil"]["lednice_napojeni"]["b"],
      "delka %.2f m" % math.hypot(tk.osa[j][0] - ex, tk.osa[j][1] - ez))
