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
# kovárna (Míša 14. 11., Disk „budovy“ kovarna.zip – model Odkazu Havrana; docs/reference/kovarna/NAVOD_KOVARNA.md): glb + LOD1
KOV=$(python3 -c "import json;print(json.load(open('$K/pravidla/svet/mista.json'))['modely']['hospodarske']['kovarna_disk_id'])")
[ -f $K/hra/modely/stavby_h/kovarna.glb ] || (curl -sSL -m 300 -o $T/kovarna.zip "https://drive.usercontent.google.com/download?id=$KOV&export=download&confirm=t" && unzip -oq -j $T/kovarna.zip kovarna.glb kovarna_lod1.glb -d $K/hra/modely/stavby_h/)
# celé stavby z Disku (krčma, hájovna – Míša 14. 11.): stáhnout zip, vybrat glb; krčma do řady upravená blender/celky_upravy.py
python3 -c "import json;C=json.load(open('$K/pravidla/svet/mista.json'))['modely']['celky'];[print(k,v['disk_id'],' '.join(v['zip'])) for k,v in C.items() if isinstance(v,dict)]" | while read M_ ID_ Z_; do
  (curl -sSL -m 300 -o $T/$M_.zip "https://drive.usercontent.google.com/download?id=$ID_&export=download&confirm=t" && unzip -oq -j $T/$M_.zip $Z_ -d $T/$M_/) || continue
  if python3 -c "import json,sys;sys.exit(0 if 'uprava' in json.load(open('$K/pravidla/svet/mista.json'))['modely']['celky']['$M_'] else 1)"; then
    set -- $Z_; /opt/bl/bin/python $K/blender/celky_upravy.py $K $M_ $T/$M_/$1 $K/hra/modely/stavby_h/krcma_rada.glb $T/$M_/$2 $K/hra/modely/stavby_h/krcma_rada_lod1.glb
  else cp $T/$M_/*.glb $K/hra/modely/stavby_h/; fi
done
rm -rf $T; ls -la $K/hra/modely/stavby_h/
