#!/usr/bin/env python3
"""Osa ulice vsi: hra (build/beh/osa_godot.json z testu ves_osa) x Blender (blender/ves_ramec.py). Nejvic 0,05 m."""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
import ves_ramec
g = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "beh", "osa_godot.json")))
p = ves_ramec.osa_ulice()
n = min(len(g), len(p))
d = max(math.hypot(g[i][0] - p[i][0], g[i][1] - p[i][1]) for i in range(n))
ok = len(g) == len(p) and d < 0.05
print("OSA_ULICE %s bodu hra %d, Blender %d, nejvetsi rozdil %.3f m" % ("OK" if ok else "CHYBA", len(g), len(p), d))
sys.exit(0 if ok else 1)
