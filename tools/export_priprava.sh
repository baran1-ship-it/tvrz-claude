#!/bin/bash
# Priprava zdroju pro plny export sveta v NOVEM kontejneru (predani.md 15. 11.: 9 padu exportu za sebou; 28. 11. skript).
# Po tools/prostredi.sh a tools/stahni_zdroje.sh, pred tools/export.sh. Kazdy krok jen kdyz vystup chybi.
#   tools/beh.sh priprava cmd bash tools/export_priprava.sh
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
B=/opt/bl/bin/python
krok() { echo "== $*"; }
krok "Poly Haven / ambientCG: rostliny, textury"
(cd blender && $B -c 'import textures; textures.fetch_models(); textures.fetch(); textures.fetch_acg()')
krok "sindel (bake_tex)"
[ -f blender/tex_cache/sindel_diff_2k.jpg ] || (cd blender && $B bake_tex.py sindel) || true
krok "karty stromu (trees.py, listnace.py - segfault na konci je normalni)"
[ -f blender/tex_cache/smrk_vetev.png ] || (cd blender && $B trees.py) || true
ls blender/tex_cache/*_karta.png > /dev/null 2>&1 || (cd blender && $B listnace.py) || true
krok "origin/main (nove.py cte modely/nove/*.glb)"
git fetch -q --depth 1 origin main || true
krok "vysky.json (test smyslu)"
[ -f tools/krok_b/vysky.json ] || $B tools/krok_b/vysky.py tools/krok_b/vysky.json
krok "procedurální textury"
python3 tools/gen_tex.py > /dev/null
echo "PRIPRAVA OK (borovice z Disku, jablon strom2.py, domy vsi a dvere tvrz-modely: viz predani.md 15. 11. - kontroluje export)"
