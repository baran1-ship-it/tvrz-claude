#!/bin/bash
# Fotky materiálů hradu (Poly Haven, CC0) do blender/tex + šindel (nastroje/sindel_tex.py).
K=$(cd "$(dirname "$0")/.." && pwd); T=$K/blender/tex; mkdir -p $T
for id in castle_wall_slates plastered_stone_wall wood_planks_grey rough_wood stacked_stone_wall dirt_floor; do
  [ -f $T/${id}_Diffuse.jpg ] && continue
  curl -s https://api.polyhaven.com/files/$id | python3 -c "
import json,sys; d=json.load(sys.stdin)
for k in ('Diffuse','nor_gl','Rough'):
  if k in d: print(k, d[k]['1k']['jpg']['url'])" | while read k u; do curl -s -o $T/${id}_${k}.jpg "$u"; done
done
python3 $K/nastroje/sindel_tex.py $K
