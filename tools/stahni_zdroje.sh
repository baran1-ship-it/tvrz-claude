#!/bin/bash
# Herni data do modely/ (radce 19:15 bod 2).  bash tools/stahni_zdroje.sh
# Kompletni snimek hotovych dat je v repu: balíky data/*.pck (stejne, jake stahuje tablet). Z nich se rozbali modely/
# a .godot/imported/ - stavba sveta, mereni, snimky i vydani (vydani.py: baliky bez zdroju nechava) funguji bez Blenderu.
# Zdrojove soubory (jen kdyz se meni model/textura): geometrie a rozmisteni = blender/*.py (export_game.py), fotky textur
# a rostlin = Poly Haven / ambientCG (blender/textures.py, predmety.py stahuji samy), Misovy modely = Google Disk,
# slozka "Modely" (https://drive.google.com/drive/folders/1LIf8CIdMUVgmgOiszmP1E567PpmUbi-b), postavy = vetev assets.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
python3 tools/pck_rozbal.py
# import jen toho, co ma zdroj v gitu (obrazky, fonty, zvuky, waterways); data z baliku import neprepise
godot --headless --path . --import > /dev/null 2>&1 || true
echo "data OK: $(ls modely | wc -l) polozek v modely/, $(ls .godot/imported | wc -l) importovanych souboru"
