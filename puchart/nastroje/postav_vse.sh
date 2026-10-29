#!/bin/bash
# Celá stavba podkladů výseku od nuly (nový kontejner): DMR 5G -> mřížky -> toky -> maska -> dlaždice -> textury -> import.
# bash nastroje/postav_vse.sh   (~5 min; stahuje ~80 MB z ČÚZK a ~10 MB z Poly Haven)
set -e
K=$(cd "$(dirname "$0")/.." && pwd)
B=$K/build; mkdir -p $B/dmr
pip install -q pyproj "laspy[lazrs]" numpy scipy pillow pysheds affine 2>/dev/null || true
for s in $(python3 -c "import json;print(' '.join(json.load(open('$K/pravidla/svet/zdroje_dat.json'))['dmr5g_listy']))"); do
	[ -f $B/dmr/$s.laz ] || { curl -sS -o $B/dmr/$s.zip https://openzu.cuzk.gov.cz/opendata/DMR5G/epsg-5514/$s.zip && unzip -oq $B/dmr/$s.zip -d $B/dmr && rm $B/dmr/$s.zip; }
done
cd $B
V=$(python3 -c "import json;v=json.load(open('$K/pravidla/svet/svet.json'))['vysek']['sjtsk'];print(v['x0'],v['y0'],v['x1'],v['y1'])")
O=$(python3 -c "import json;v=json.load(open('$K/pravidla/svet/svet.json'))['obzor']['sjtsk'];print(v['x0'],v['y0'],v['x1'],v['y1'])")
python3 $K/nastroje/dmr_mrizka.py dmr vysek1m $V 1
python3 $K/nastroje/dmr_mrizka.py dmr obzor10m $O 10
python3 $K/nastroje/dmr_mrizka.py dmr prehled5m $O 5
python3 $K/nastroje/toky.py prehled5m $K/pravidla/svet/osm_toky.json toky_teren.json 0.25
python3 $K/nastroje/voda_hra.py toky_teren.json vysek1m $K
python3 $K/nastroje/stanoviste.py vysek1m $K/pravidla/svet/voda.json $K
python3 $K/nastroje/teren_upravy.py $K/build/reference/web/www_archeologickyatlas_cz_0b03e4466a.jpg vysek1m vysek1m_upr $K   # valy, příkopy (plán atlasu; obrázek stáhne fotky_web.py)
python3 $K/nastroje/teren_dlazdice.py vysek1m_upr obzor10m $K
bash $K/nastroje/stahni_realne.sh   # biotopy, PPV, DMP 1G -> stanoviště 1393, maska, stromy
cp $K/pravidla/svet/pudy.json $K/hra/data/
mkdir -p $K/hra/textury/zem
for id in $(python3 -c "import json;print(' '.join(v['foto'] for v in json.load(open('$K/pravidla/svet/pudy.json'))['vrstvy']))"); do
	ls $K/hra/textury/zem/${id}_diff_1k.jpg >/dev/null 2>&1 && continue
	curl -s https://api.polyhaven.com/files/$id | python3 -c "
import json,sys; d=json.load(sys.stdin); print(d['Diffuse']['1k']['jpg']['url']); print(d['nor_gl']['1k']['jpg']['url'])" | while read u; do
		f=$(basename "$u"); curl -s -o "$K/hra/textury/zem/${f/_diffuse_/_diff_}" "$u"; done
done
python3 $K/nastroje/pole_textur.py $K
mkdir -p $K/hra/modely/stromy && for m in $(python3 -c "import json;print(' '.join(json.load(open('$K/pravidla/svet/stromy_modely.json'))['varianty']))"); do cp -n $K/../modely/nove/${m}_*.glb $K/hra/modely/stromy/ 2>/dev/null || true; done
python3 $K/nastroje/stromy_lod.py $K/hra/modely/stromy 0.3 1.45
cp $K/pravidla/svet/stromy_modely.json $K/hra/data/
cd $K/hra && godot --headless --import > /dev/null 2>&1 || true
# hrady (návrhy): Blender 4.2 jako modul v /opt/bl (tools/prostredi.sh Havrana)
bash $K/nastroje/stahni_textury_hradu.sh
[ -x /opt/bl/bin/python ] && /opt/bl/bin/python $K/blender/hrady.py $K
python3 $K/nastroje/stromy_sdilene_textury.py $K/hra/modely/stromy
echo "postav_vse OK"
