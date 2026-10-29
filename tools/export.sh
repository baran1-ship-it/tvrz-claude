#!/bin/bash
# Export sveta s branami (radce 27. 10. 20:50; Astra 29. 10. 07:10: set -euo pipefail, kazdy krok vlastni rc, zadny
# grep jako test uspechu - kontroly v tools/export_kontroly.py vraceji rc).
#   BEH_LIMIT=7000 tools/beh.sh export_X cmd bash tools/export.sh [--jen-po]
#   rc 2 test smyslu pred exportem | 3 Blender (rc nebo chybi build/export_hotov.json z tohoto svet.json)
#   rc 4 test smyslu po exportu   | 5 malo mista | 6 poskozeny obrazek | 7 pyflakes | 8 import Godotu
#   rc 9 krok stavby nad mez       | 10 limity textur | 11 textury pro tablet | 12 predpeceni potoka | 13 zapis otisku
# --jen-po: jen brany po exportu a dokonceni nad hotovym exportem (Blender se nespousti).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/beh
stav() { echo "{\"stav\": \"$1\", \"rc\": $2, \"svet_md5\": \"$(md5sum modely/svet.json 2>/dev/null | cut -d' ' -f1)\", \"cas\": \"$(date -u +%FT%TZ)\"}" > build/export_stav.json; }
# krok <rc> <popis> <prikaz...>: prikaz musi skoncit 0, jinak stav CHYBA a konec s rc
krok() {
    local kod=$1 popis=$2
    shift 2
    if "$@"; then
        return 0
    fi
    echo "KROK SELHAL ($popis, rc $kod)"
    stav CHYBA "$kod"
    exit "$kod"
}
stav BEZI 1
REZIM=${1:-}
if [ "$REZIM" != "--jen-po" ]; then
    volno=$(df -m --output=avail / | tail -1 | tr -d ' ')
    min_mb=$(python3 -c "import json;print(int(json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test']['export_volno_mb']))")
    if [ "$volno" -lt "$min_mb" ]; then
        echo "MALO MISTA NA DISKU: $volno MB < $min_mb MB (docs/predani.md: co smazat)"
        stav CHYBA 5
        exit 5
    fi
    /opt/bl/bin/python -m pyflakes --version > /dev/null 2>&1 || /opt/bl/bin/python -m pip install -q pyflakes
    krok 7 "pyflakes skriptu Blenderu" python3 tools/export_kontroly.py pyflakes
    krok 2 "test smyslu pred exportem (build/beh/smysl_pred.log)" bash -c "/opt/bl/bin/python tools/test_smyslu.py > build/beh/smysl_pred.log 2>&1"
    rm -f build/export_hotov.json
    krok 3 "Blender export (build/beh/export_blender.log)" bash -c "set -o pipefail; /opt/bl/bin/python -u blender/export_game.py 2>&1 | tee build/beh/export_blender.log"
    krok 3 "znacka dokonceni Blenderu" python3 tools/export_kontroly.py blender
    krok 6 "obrazky po exportu (build/beh/obrazky_po.log)" bash -c "python3 tools/over_obrazky.py modely > build/beh/obrazky_po.log 2>&1"
    krok 10 "limity textur" python3 tools/limity_textur.py
    krok 8 "import Godotu (build/beh/export_import.log)" bash -c "godot --headless --path . --import > build/beh/export_import.log 2>&1"
    krok 8 "chyby v logu importu" python3 tools/export_kontroly.py import build/beh/export_import.log
    krok 11 "textury pro tablet" python3 tools/textury_tablet.py
fi
krok 4 "test smyslu po exportu (build/beh/smysl_po.log)" bash -c "/opt/bl/bin/python tools/test_smyslu.py --po > build/beh/smysl_po.log 2>&1"
krok 9 "protokol stavby terenu (build/beh/protokol_blender.log)" bash -c "/opt/bl/bin/python tools/protokol_blender.py > build/beh/protokol_blender.log 2>&1"
if ! python3 tools/export_kontroly.py reka; then
    echo "POTOK predpekam (reka_otisk se zmenil)"
    krok 12 "predpeceni potoka (build/pregeneruj_reka.log)" bash tools/pregeneruj.sh reka
    krok 12 "potok po predpeceni z tohoto exportu" python3 tools/export_kontroly.py reka
fi
krok 13 "zapis otisku exportu" python3 tools/otisk_exportu.py zapis
stav OK 0
echo "EXPORT OK"
