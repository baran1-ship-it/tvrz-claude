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
rm -rf $T; ls -la $K/hra/modely/stavby_h/
