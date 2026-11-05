#!/bin/bash
# BVH klipy CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu; „free to use for any purpose“, podekovani:
# database created with funding from NSF EIA-0196217) - prevod cgspeed z github.com/una-dinosauria/cmu-mocap.
#   tools/postavy_q/stahni_cmu.sh <slozka>   pak: /opt/bl/bin/python -I tools/postavy_q/anim_cmu.py -- <slozka>
D=${1:-/tmp/cmu_bvh}; mkdir -p "$D"
for c in 13_23 62_07 62_03 62_11 02_06 13_09 62_12 18_08 19_08 40_10 13_26 69_18; do
  s=$(printf %03d $((10#${c%%_*})))
  [ -s "$D/$c.bvh" ] || curl -sfL -o "$D/$c.bvh" "https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/$s/$c.bvh" || echo "CHYBA $c"
done
ls "$D" | wc -l
