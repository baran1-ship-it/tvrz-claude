#!/bin/bash
# Sady postav obyvatel (Quaternius CC0 + vlastni dobove obleceni, tools/postavy_q/postavy.json) -> modely/postavy/npc/
#   tools/postavy_q/sestav.sh [sada ...]      bez argumentu vsechny sady z pravidla/svet/postavy_vzhled.json
# Na pozadi (run_in_background), Blender jako modul /opt/bl/bin/python (pip: opencv-python-headless).
# Zdroje: vetev assets (quaternius/) -> $Q_WORK/src. Po behu: godot --headless --import, balik z_postavy (tools/vydani.py).
set -u
cd "$(dirname "$0")"; R=$(cd ../..; pwd)
export Q_WORK=${Q_WORK:-/tmp/postavy_q}; W=$Q_WORK
mkdir -p "$W/src"
[ -d "$W/src/quaternius" ] || git -C "$R" archive origin/assets quaternius | tar -x -C "$W/src"
B="$W/src/quaternius/base_characters/Base Characters/Godot - UE"
# na vetvi assets chybi dve normalove mapy, ktere glTF vlasu a oci odkazuji (jsou v modely/postavy z baliku)
for f in T_Hair_1_Normal_png.png T_Eye_Normal_png.png; do [ -f "$B/$f" ] || cp "$R/modely/postavy/$f" "$B/"; done
/opt/bl/bin/python -c "import cv2" 2>/dev/null || /opt/bl/bin/python -m pip install -q opencv-python-headless
OUT="$R/modely/postavy/npc"; mkdir -p "$OUT"
SADY="$*"
[ -n "$SADY" ] || SADY=$(python3 -c "
import json;d=json.load(open('$R/pravidla/svet/postavy_vzhled.json'))
s=list(d['obyvatele'].values())+list(d['podle_role'].values())+d['zalozni']['muz']+d['zalozni']['zena']
print(' '.join(sorted(set(s))))")
jedna() {
  n=$1
  /opt/bl/bin/python -I q_postava.py -- $n "$W/qd_$n.jpg" > "$W/log_d_$n.txt" 2>&1 || { echo "CHYBA postava $n"; return; }
  /opt/bl/bin/python -I q_export2.py -- $n "$W/qd_$n.blend" "$OUT" > "$W/log_e_$n.txt" 2>&1 || { echo "CHYBA export $n"; return; }
  rm -f "$OUT/_${n}_export.blend"
  echo "$n $(grep -o 'CELA troj [0-9]* povrchu [0-9]*' "$W/log_e_$n.txt")"
}
export -f jedna; export W OUT
echo $SADY | tr ' ' '\n' | xargs -P ${Q_PROC:-3} -I{} bash -c 'jedna {}'
python3 - "$R" <<'PY'
import json, glob, os, sys
R = sys.argv[1]; p = f"{R}/pravidla/svet/postavy_vzhled.json"; d = json.load(open(p))
for f in sorted(glob.glob(f"{R}/modely/postavy/npc/*_sada.json")):
    s = json.load(open(f))
    if "cela_trojuhelniky" in s: d["troj"][s["postava"]] = s["cela_trojuhelniky"]
json.dump(d, open(p, "w"), indent=1, ensure_ascii=False)
print("troj", d["troj"])
PY
echo HOTOVO
