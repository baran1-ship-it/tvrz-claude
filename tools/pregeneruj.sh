#!/bin/bash
# Generovana data mimo git (radce 19:15 bod 4) - jen kdyz se zmeni to, z ceho vznikaji; z baliku (stahni_zdroje.sh) uz jsou.
#   bash tools/pregeneruj.sh [kryti] [reka] [portaly]     (bez argumentu vse)
#   kryti   modely/louka/kryti.bin - paprsky shora pod stoly, strechy, skaly (zmena staveb, skal)
#   reka    modely/reka/*          - potok z koryta (zmena scripts/koryto.gd nebo osy)
#   portaly modely/portaly.json    - okna a dvere hostince z blender/hostinec.py (Blender)
# Po zmene: vydani.py zabali jen baliky, ke kterym jsou zdroje (jinak opravny balik: vydani.py --jen z_<nazev>).
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
CO=${*:-kryti reka portaly}
for c in $CO; do
	case $c in
		kryti) TVRZ_ROZSEV=1 timeout 1800 godot --headless --path . > build/pregeneruj_kryti.log 2>&1 ;;
		reka) timeout 1800 xvfb-run -a -s "-screen 0 1200x800x24" godot --path . --rendering-method gl_compatibility \
				-s res://tools/reka_bake.gd > build/pregeneruj_reka.log 2>&1
			godot --headless --path . --import > /dev/null 2>&1 || true ;;
		portaly) /opt/bl/bin/python tools/portaly.py ;;
		*) echo "neznam: $c"; exit 1 ;;
	esac
	echo "$c OK"
done
