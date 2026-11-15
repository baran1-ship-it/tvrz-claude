#!/bin/bash
# Stavby z Havrana do Puchartu (Míša 11. 11.: „připrav import staveb – vesnice dle pozůstatků v krajině, mlýn vodní, hospoda,
# hájovna“; pravidlo: nejdřív Havran). Z datových balíků větve Havrana (data/z_ves-*, data/z_mlyn-*) vytáhne domy vsi
# (Dum1 roubený, Dum2 omítnutý s doškovou valbou, Rychta, ChyseKura, ChysePrkna + střední LOD) a vodní mlýn (+ LOD1)
# do hra/modely/stavby_h/. Z rostlin Havrana (z_rostliny) jabloň jablon + jablon_daleko pro sady a dvory vsi (Míša 11. 11.: stromy ve vsi). Generované – v gitu je jen tento postup. Umístění: pravidla/svet/mista.json (po schválení Míšou).
set -e
K=$(cd "$(dirname "$0")/.." && pwd); R=$(cd $K/.. && pwd); B=origin/claude/new-session-0dtk58
G=${G:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}; T=$(mktemp -d); mkdir -p $K/hra/modely/stavby_h
printf '[application]\nconfig/name="x"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n' > $T/project.godot
sed "s#const OUT := .*#const OUT := \"$K/hra/modely/stavby_h/\"#" $K/nastroje/havran/stavby_export.gd > $T/ex.gd
cd $R; git fetch -q origin claude/new-session-0dtk58 || true
for f in $(git ls-tree -r --name-only $B data | grep -E "^data/(z_(ves|mlyn|rostliny)|p_(stodola|stodola_mala|kolna|kurnik)|tex_predmety)-"); do git show $B:$f >> $T/$(basename $(basename $f .000) .001); done   # balík po částech .000/.001 = spojit (z_rostliny: jabloň); p_stodola, p_stodola_mala, p_kolna, p_kurnik = hospodářské stavby usedlostí (+ tex_predmety: sdílené textury předmětů, bez nich se model nenačte)
(cd $T && timeout 1200 $G --headless --path . -s ex.gd -- $T/*.pck 2>&1 | grep -E "^STAVBA|^CHYBI")
# originál domů pro úpravy modelu (okap nad vchody, blender/okap_vstupu.py níže) – úprava jde vždy z něj, opakovaně nic nezdvojí
mkdir -p $K/build/zdroj_celky && cp $K/hra/modely/stavby_h/domy.glb $K/build/zdroj_celky/domy.glb
# kovárna (Míša 14. 11., Disk „budovy“ kovarna.zip – model Odkazu Havrana; docs/reference/kovarna/NAVOD_KOVARNA.md): glb + LOD1
KOV=$(python3 -c "import json;print(json.load(open('$K/pravidla/svet/mista.json'))['modely']['hospodarske']['kovarna_disk_id'])")
mkdir -p $K/build/zdroj_celky
[ -f $K/build/zdroj_celky/kovarna.glb ] || (curl -sSL -m 300 -o $T/kovarna.zip "https://drive.usercontent.google.com/download?id=$KOV&export=download&confirm=t" && unzip -oq -j $T/kovarna.zip kovarna.glb kovarna_lod1.glb -d $K/hra/modely/stavby_h/ && cp $K/hra/modely/stavby_h/kovarna.glb $K/build/zdroj_celky/)
# celé stavby z Disku (krčma, hájovna – Míša 14. 11.): stáhnout zip, vybrat glb; krčma do řady upravená blender/celky_upravy.py
python3 -c "import json;C=json.load(open('$K/pravidla/svet/mista.json'))['modely']['celky'];[print(k,v['disk_id'],' '.join(v['zip'])) for k,v in C.items() if isinstance(v,dict)]" | while read M_ ID_ Z_; do
  (curl -sSL -m 300 -o $T/$M_.zip "https://drive.usercontent.google.com/download?id=$ID_&export=download&confirm=t" && unzip -oq -j $T/$M_.zip $Z_ -d $T/$M_/ && mkdir -p $K/build/zdroj_celky/$M_ && cp $T/$M_/*.glb $K/build/zdroj_celky/$M_/) || continue
  if python3 -c "import json,sys;sys.exit(0 if 'uprava' in json.load(open('$K/pravidla/svet/mista.json'))['modely']['celky']['$M_'] else 1)"; then
    set -- $Z_; /opt/bl/bin/python $K/blender/celky_upravy.py $K $M_ $T/$M_/$1 $K/build/zdroj_celky/krcma_rada.glb $T/$M_/$2 $K/hra/modely/stavby_h/krcma_rada_lod1.glb
  else cp $T/$M_/*.glb $K/hra/modely/stavby_h/; cp $T/$M_/*.glb $K/build/zdroj_celky/; fi
done
# jabloně z Disku (Míša 14. 11.: „ty naše stávající se mi nelíbí“): varianty starých a mladých jabloní (mista.json modely.stromy.jablon.disk)
python3 -c "import json;D=json.load(open('$K/pravidla/svet/mista.json'))['modely']['stromy']['jablon']['disk'];[print(v['id'],' '.join(v['soubory'])) for v in D.values()]" | while read ID_ Z_; do
  curl -sSL -m 600 -o $T/j.zip "https://drive.usercontent.google.com/download?id=$ID_&export=download&confirm=t" && unzip -oq -j $T/j.zip $Z_ -d $K/hra/modely/stavby_h/; rm -f $T/j.zip
done
# úpravy částí modelů (mista.json upravy_modelu: přístřešek kovárny, předměty před hájovnou) z originálu v build/zdroj_celky
/opt/bl/bin/python $K/blender/upravy_casti.py -- $K
# zvednutý okap („obočí“) nad vchody domů s nízkým okapem (mista.json okapy_vstupu, docs/chyby.md 314 – Dum2 1,69 m) přímo
# v glb (zachová kolize OMI_physics), pak střední stupeň domů z upraveného modelu (mista.json lod_stredni) – jinak by
# vývoz z Havrana nahoře vrátil starý domy_stredni.glb
python3 $K/blender/okap_vstupu.py $K
/opt/bl/bin/python $K/blender/stredni_lod.py -- $K
rm -rf $T; ls -la $K/hra/modely/stavby_h/
