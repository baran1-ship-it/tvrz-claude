#!/bin/bash
# Generovana data mimo git (radce 19:15 bod 4) - jen kdyz se zmeni to, z ceho vznikaji; z baliku (stahni_zdroje.sh) uz jsou.
#   bash tools/pregeneruj.sh [zaklad] [kryti] [reka] [portaly]     (bez argumentu vse)
#   zaklad  textures/, audio/      - proceduralni textury (plamen, kour, mraky, kov) a zvuky (kroky, kovadlina, luk);
#                                    nejsou v gitu, BEZ NICH APK nema ohen ani zvuky (0.55!)
#   kryti   modely/louka/kryti.bin - paprsky shora pod stoly, strechy, skaly (zmena staveb, skal)
#   reka    modely/reka/*          - potok z koryta (zmena scripts/koryto.gd nebo osy)
#   portaly modely/portaly.json    - okna a dvere hostince z blender/hostinec.py (Blender)
#   pudy    modely/textury/<puda>_{diff,nor}.jpg - fotky pud (svet.gd PUDY) z Poly Haven (blender/textures.py); jen kdyz
#           se meni seznam pud - z baliku jsou importovane i bez zdroje (neni ve vychozim vyberu, stahuje ~200 MB)
# Po zmene: vydani.py zabali jen baliky, ke kterym jsou zdroje (jinak opravny balik: vydani.py --jen z_<nazev>).
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
mkdir -p build
CO=${*:-zaklad kryti reka portaly}
for c in $CO; do
	case $c in
		zaklad) python3 tools/gen_tex.py > build/pregeneruj_zaklad.log 2>&1 && python3 tools/gen_snd.py >> build/pregeneruj_zaklad.log 2>&1
			godot --headless --path . --import > build/pregeneruj_import.log 2>&1 ;;
		kryti) TVRZ_ROZSEV=1 timeout 1800 godot --headless --path . > build/pregeneruj_kryti.log 2>&1 ;;
		reka) timeout 1800 xvfb-run -a -s "-screen 0 1200x800x24" godot --path . --rendering-method gl_compatibility \
				-s res://tools/reka_bake.gd > build/pregeneruj_reka.log 2>&1
			godot --headless --path . --import > build/pregeneruj_import.log 2>&1 ;;
		portaly) /opt/bl/bin/python tools/portaly.py ;;
		pudy) python3 blender/textures.py 2k > build/pregeneruj_pudy.log
			for n in $(grep -o 'const PUDY := \[[^]]*\]' scripts/svet.gd | grep -o '"[a-z_]*"' | tr -d '"'); do
				for k in diff nor; do
					f=$(ls blender/tex_cache/${n}_${k}_2k.* 2>/dev/null | head -1)
					[ -n "$f" ] && cp "$f" modely/textury/${n}_${k}.jpg
				done
			done
			godot --headless --path . --import > build/pregeneruj_import.log 2>&1 ;;
		*) echo "neznam: $c"; exit 1 ;;
	esac
	echo "$c OK"
done
