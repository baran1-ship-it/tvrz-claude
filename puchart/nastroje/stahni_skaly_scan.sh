#!/bin/bash
# Naskenované skály Poly Haven (CC0) do blender/skaly_scan/<id>/ (glTF 1k). Výběr: rešerše 2. 11. (vrstevnaté stěny = droba).
K=$(cd "$(dirname "$0")/.." && pwd); T=$K/blender/skaly_scan; mkdir -p $T
for id in rock_face_01 rock_face_02 boulder_01 rock_moss_set_01; do
  [ -f $T/$id/${id}_1k.gltf ] && continue
  mkdir -p $T/$id
  curl -s https://api.polyhaven.com/files/$id | python3 -c "
import json,sys;d=json.load(sys.stdin);g=d['gltf']['1k']['gltf'];print(g['url']);[print(v['url']) for v in g['include'].values()]" | while read u; do
    f=${u#*1k/}; f=${f#*/}; mkdir -p $T/$id/$(dirname $f); curl -s -o "$T/$id/$f" "$u"; done
done
