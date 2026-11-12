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
# osy toků (pravidla/svet/voda.json) jsou schválená data – z terénu jen v novém projektu (12. 11.: opakované generování ztratilo
# jména z OSM, mosty se podle jména nenašly a nepostavily); nové vygenerování: smazat voda.json
if [ ! -s $K/pravidla/svet/voda.json ]; then
python3 $K/nastroje/toky.py prehled5m $K/pravidla/svet/osm_toky.json toky_teren.json 0.25
python3 $K/nastroje/voda_hra.py toky_teren.json vysek1m $K
fi
python3 $K/nastroje/stanoviste.py vysek1m $K/pravidla/svet/voda.json $K
python3 $K/nastroje/teren_upravy.py vysek1m vysek1m_upr $K   # plošiny, rampa za branou, průrva (hrad_puchart.json; valy jsou v DMR)
python3 $K/nastroje/koryta.py vysek1m_upr vysek1m_kor $K   # koryta potoků zaříznutá do terénu (voda_hra.json koryto)
python3 $K/nastroje/cesty.py vysek1m_kor vysek1m_cesty $K   # cesty (zářez, maska, stromy pryč)
python3 $K/nastroje/mista_rozmisteni.py vysek1m_cesty vysek1m_mista $K   # stavby nových míst (pravidla/svet/mista.json): domy a plošiny pod nimi
python3 $K/nastroje/teren_dlazdice.py vysek1m_mista obzor10m $K
bash $K/nastroje/stahni_realne.sh   # biotopy, PPV, DMP 1G -> stanoviště 1393, maska, stromy
cp $K/pravidla/svet/pudy.json $K/pravidla/svet/rozpocty.json $K/pravidla/svet/kontroly_hra.json $K/pravidla/svet/hrad_vzhled.json $K/hra/data/
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
cp $K/nastroje/godot/r16_zstd.gd $K/hra/_r16z.gd && godot --headless --path $K/hra -s res://_r16z.gd; rm -f $K/hra/_r16z.gd*
# hrady (návrhy): Blender 4.2 jako modul v /opt/bl (tools/prostredi.sh Havrana)
bash $K/nastroje/stahni_textury_hradu.sh
[ -x /opt/bl/bin/python ] && /opt/bl/bin/python $K/blender/puchart_hrad.py $K && bash $K/nastroje/stahni_skaly_scan.sh && /opt/bl/bin/python $K/blender/skaly.py $K && python3 $K/nastroje/skaly_podklad.py $K && /opt/bl/bin/python $K/blender/voda.py $K && /opt/bl/bin/python $K/blender/kameny_koryta.py $K && python3 $K/nastroje/koryto_kameny.py $K && python3 $K/nastroje/stavby_vegetace.py $K && python3 $K/nastroje/kryt_korun.py $K   # dvojhradí podle zdrojů (staré návrhy: blender/hrady.py $K <id>)
python3 $K/nastroje/stromy_sdilene_textury.py $K/hra/modely/stromy
echo "postav_vse OK"
python3 $K/nastroje/import_velikost.py $K && (cd $K/hra && godot --headless --import > /dev/null 2>&1 || true)
python3 $K/nastroje/import_stromy.py $K && (cd $K/hra && godot --headless --import > /dev/null 2>&1 || true)
[ -d $K/hra/modely/predmety_h ] || bash $K/nastroje/predmety_z_havrana.sh   # předměty, menu hráče a pískoviště z Havrana (Míša 10. 11.)
