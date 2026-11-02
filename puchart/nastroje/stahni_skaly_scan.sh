#!/bin/bash
# Naskenované skály Poly Haven (CC0) do blender/skaly_scan/<id>/ (glTF 1k + .bin + textures/). Výběr: rešerše 2. 11.
K=$(cd "$(dirname "$0")/.." && pwd); T=$K/blender/skaly_scan; mkdir -p $T
for id in rock_face_01 rock_face_02 boulder_01 rock_moss_set_01; do
  [ -f $T/$id/$id.bin ] && continue
  mkdir -p $T/$id
  curl -s https://api.polyhaven.com/files/$id | python3 -c "
import json,sys;d=json.load(sys.stdin);g=d['gltf']['1k']['gltf'];print('${id}_1k.gltf',g['url'])
for k,v in g['include'].items(): print(k,v['url'])" | while read f u; do mkdir -p $T/$id/$(dirname $f); curl -s -o "$T/$id/$f" "$u"; done
done
python3 $K/nastroje/scan_barvy.py $K
