#!/bin/bash
# Skutečná podoba místa (postup KCD): ortofoto, povrch DMP 1G (výška porostu), biotopy AOPK, potenciální vegetace.
# Volá postav_vse.sh po mřížkách; pracuje v build/. Zdroje a licence: pravidla/svet/zdroje_dat.json.
set -e
K=$(cd "$(dirname "$0")/.." && pwd); B=$K/build; mkdir -p $B/foto; cd $B
read X0 Y0 X1 Y1 < <(python3 -c "import json;v=json.load(open('$K/pravidla/svet/svet.json'))['vysek']['sjtsk'];print(int(v['x0']),int(v['y0']),int(v['x1']),int(v['y1']))")
BB="$X0,$Y0,$X1,$Y1"; N=$(( (X1-X0) ))
[ -f foto/dmp1g.tif ] || curl -sS -o foto/dmp1g.tif "https://ags.cuzk.gov.cz/arcgis2/rest/services/dmp1g/ImageServer/exportImage?bbox=$BB&bboxSR=5514&imageSR=5514&size=$N,$N&format=tiff&pixelType=F32&interpolation=RSP_BilinearInterpolation&f=image"
for t in 0 1; do for s in 0 1; do x0=$((X0+s*1000)); y0=$((Y0+t*1000))
	[ -f foto/orto_${t}_${s}.jpg ] || curl -sS -o foto/orto_${t}_${s}.jpg "https://ags.cuzk.gov.cz/arcgis1/rest/services/ORTOFOTO/MapServer/export?bbox=$x0,$y0,$((x0+1000)),$((y0+1000))&bboxSR=5514&imageSR=5514&size=2000,2000&format=jpg&f=image"
done; done
[ -f biotopy.json ] || curl -sS -o biotopy.json "https://gis.nature.cz/arcgis/rest/services/Biotopy/BiotopyProhlizecka/MapServer/1/query?geometry=$BB&geometryType=esriGeometryEnvelope&inSR=5514&outSR=5514&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=json"
[ -f ppv.json ] || curl -sS -o ppv.json "https://gis.nature.cz/arcgis/rest/services/PrirodniPomery/PotencialVegetace/MapServer/1/query?geometry=$((X0-2000)),$((Y0-2000)),$((X1+2000)),$((Y1+2000))&geometryType=esriGeometryEnvelope&inSR=5514&outSR=5514&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=json"
python3 - <<P
import numpy as np; from PIL import Image
D=np.array(Image.open('foto/dmp1g.tif')).astype(np.float32); H=np.load('vysek1m.npy')[:D.shape[0],:D.shape[1]]
np.save('chm.npy', D-H)
P
python3 $K/nastroje/stanoviste_realne.py $B $K
echo "stahni_realne OK"
