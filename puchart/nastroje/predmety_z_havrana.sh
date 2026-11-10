#!/bin/bash
# Předměty z Havrana do Puchartu (Míša 10. 11.: „Havran už to má hotové, předměty upravené“): z datových balíků větve
# Havrana (data/p_<id>-*.pck, katalog data/z_katalog-*.pck) vytáhne modely a ikony předmětů, textury zmenší (albedo 512,
# ostatní 256 px – Havran 0.59: 2k textury předmětů = záseky a pád), uloží do hra/modely/predmety_h/ + katalog predmety_h.json.
# Louč, držák louče a stojací svícen (světla místností) do hra/modely/predmety/. Generované – v gitu je jen tento postup.
set -e
K=$(cd "$(dirname "$0")/.." && pwd); R=$(cd $K/.. && pwd); B=origin/claude/new-session-0dtk58
G=${G:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}; T=$(mktemp -d); mkdir -p $T/pk $K/hra/modely/predmety_h $K/hra/modely/predmety
printf '[application]\nconfig/name="x"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n' > $T/project.godot
cp $K/nastroje/havran/predmety_export.gd $T/ex.gd
sed -i "s#const OUT := .*#const OUT := \"$K/hra/modely/predmety_h/\"#" $T/ex.gd
cd $R; git fetch -q origin claude/new-session-0dtk58 || true
git show $B:$(git ls-tree -r --name-only $B data | grep "^data/z_katalog") > $T/kat.pck
printf 'extends SceneTree\nfunc _init():\n\tProjectSettings.load_resource_pack("%s/kat.pck", false)\n\tvar f := FileAccess.open("%s/hra/modely/predmety_h.json", FileAccess.WRITE); f.store_string(FileAccess.get_file_as_string("res://modely/predmety.json")); f.close()\n\tquit()\n' $T $K > $T/kat.gd
(cd $T && $G --headless --path . -s kat.gd >/dev/null 2>&1)
git ls-tree -r --name-only $B data | grep "^data/p_" | split -l 40 - $T/davka_
for d in $T/davka_*; do
  rm -f $T/pk/*; while read f; do git show $B:$f > $T/pk/$(basename $f .000); done < $d
  (cd $T && timeout 1200 $G --headless --path . -s ex.gd -- pk/*.pck 2>&1 | grep -c "^ID")
done
rm -rf $T; ls $K/hra/modely/predmety_h/*.glb | wc -l
