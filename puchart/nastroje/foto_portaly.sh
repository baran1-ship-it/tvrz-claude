#!/bin/bash
# Snímky zblízka každého portálu (build/portaly.json z blender/puchart_hrad.py): zvenku a zevnitř.
# Použití: bash nastroje/foto_portaly.sh výstupní_složka [index...]
K=$(cd "$(dirname "$0")/.." && pwd); G=${G:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}; OUT=$1; shift; mkdir -p "$OUT"
python3 - "$K" "$@" <<'PY' > /tmp/foto_portaly.txt
import json, sys
K = sys.argv[1]; vyb = [int(a) for a in sys.argv[2:]]
P = json.load(open(K + "/build/portaly.json"))["portaly"]
for i, p in enumerate(P):
    if vyb and i not in vyb: continue
    x, y, z = p["pos"]; vx, vz = p["ven"]; h = p["h"]; D = p["hloubka"]
    for jm, s, dist in (("ven", 1, 3.2 + p["w"]), ("dovnitr", -1, D + 2.6 + p["w"] * 0.5)):
        cx, cz = x + vx * s * dist, z + vz * s * dist
        tx, tz = x - vx * s * 0.3, z - vz * s * 0.3
        print("%d_%s;%.2f,%.2f,%.2f,%.2f,%.2f,%.2f" % (i, jm, cx, cz, y + 1.6, tx, tz, y + h * 0.62))
PY
cd "$K/hra"
while IFS=';' read -r jm f; do
  PUCHART_FOTO_ABS=1 PUCHART_FOTO="$f;$OUT/portal_$jm.png" timeout 240 xvfb-run -a -s "-screen 0 1600x1000x24" $G --rendering-driver opengl3 --resolution 1600x1000 >/dev/null 2>&1
done < /tmp/foto_portaly.txt
ls "$OUT" | wc -l
