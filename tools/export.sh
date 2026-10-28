#!/bin/bash
# Export sveta s branou smyslu (radce 27. 10. 20:50): test smyslu na datech -> export Blenderu -> test smyslu po exportu.
#   BEH_LIMIT=7000 tools/beh.sh export_X cmd bash tools/export.sh
# Zadna chyba se nepolyka (Astra 22:00: drive "|| true", export i test smely selhat a skript skoncil OK):
#   rc 2 = test smyslu pred exportem neprosel (export se nespusti)
#   rc 3 = Blender export skoncil chybou nebo bez radku "export hotov"
#   rc 4 = test smyslu po exportu neprosel (svet.json je, ale nesmi se balit ani vydat)
#   rc 5 = malo mista na disku pred exportem (pasma test export_volno_mb)
#   rc 6 = po exportu poskozeny (useknuty) obrazek v modely/ (tools/over_obrazky.py)
# Logy zustavaji v build/beh/ (smysl_pred.log, export_blender.log, smysl_po.log).
set -o pipefail
cd "$(dirname "$0")/.."
mkdir -p build/beh
# stav exportu pro tools/vydani.py: bali jen svet, ktery prosel obema testy (md5 svet.json = presne ten export)
stav() { echo "{\"stav\": \"$1\", \"rc\": $2, \"svet_md5\": \"$(md5sum modely/svet.json 2>/dev/null | cut -d' ' -f1)\", \"cas\": \"$(date -u +%FT%TZ)\"}" > build/export_stav.json; }
stav BEZI 1
# misto na disku (28. 10.: pri plnem disku export zapsal 150 textur useknutych a skoncil OK) - pred exportem aspon
# pasma test export_volno_mb, po exportu kazdy obrazek v modely/ cely nacitatelny
volno=$(df -m --output=avail / | tail -1 | tr -d ' ')
min_mb=$(python3 -c "import json;print(int(json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test']['export_volno_mb']))")
if [ "$volno" -lt "$min_mb" ]; then
    echo "MALO MISTA NA DISKU: $volno MB < $min_mb MB - export se nespousti (docs/predani.md: co smazat)"
    stav CHYBA 5
    exit 5
fi
# kontrola skriptu Blenderu za sekundy (28. 10.: chybejici import json/Part shodil test a export po 16 min)
/opt/bl/bin/python -m pyflakes --version > /dev/null 2>&1 || /opt/bl/bin/python -m pip install -q pyflakes > /dev/null 2>&1
if /opt/bl/bin/python -m pyflakes blender/*.py tools/test_smyslu.py 2>&1 | grep -E "undefined name|unable to detect undefined|invalid syntax"; then
    echo "SKRIPTY BLENDERU MAJI CHYBU (pyflakes) - export se nespousti"
    stav CHYBA 7
    exit 7
fi
if ! /opt/bl/bin/python tools/test_smyslu.py > build/beh/smysl_pred.log 2>&1; then
    grep "^SMYSL" build/beh/smysl_pred.log
    echo "TEST SMYSLU NEPROSEL - export se nespousti"
    stav CHYBA 2
    exit 2
fi
echo "TEST SMYSLU pred exportem OK"
/opt/bl/bin/python -u blender/export_game.py 2>&1 | tee build/beh/export_blender.log
rc=$?
if [ $rc -ne 0 ] || ! grep -q "^export hotov" build/beh/export_blender.log; then
    echo "EXPORT SELHAL (rc $rc, radek 'export hotov' $(grep -c '^export hotov' build/beh/export_blender.log)) - log build/beh/export_blender.log"
    stav CHYBA 3
    exit 3
fi
if ! python3 tools/over_obrazky.py modely > build/beh/obrazky_po.log 2>&1; then
    tail -20 build/beh/obrazky_po.log
    echo "POSKOZENE OBRAZKY PO EXPORTU - nebalit, nevydavat"
    stav CHYBA 6
    exit 6
fi
if ! /opt/bl/bin/python tools/test_smyslu.py --po > build/beh/smysl_po.log 2>&1; then
    grep "^SMYSL" build/beh/smysl_po.log | head -60
    echo "TEST SMYSLU PO EXPORTU NEPROSEL - nebalit, nevydavat"
    stav CHYBA 4
    exit 4
fi
grep "SMYSL souhrn" build/beh/smysl_po.log
# protokol stavby terenu v Blenderu (kroky fort.land po 8 m) - mapa stavby ho kresli spolu s kroky hry
if ! /opt/bl/bin/python tools/protokol_blender.py > build/beh/protokol_blender.log 2>&1; then
    grep -E "^MEZ|^PROTOKOL" build/beh/protokol_blender.log
    echo "KROK STAVBY TERENU NAD MEZ (pasma.test.meze_kroku) - nevydavat, opravit pravidlo kroku"
    stav CHYBA 9
    exit 9
fi
grep -E "^PROTOKOL|^meze" build/beh/protokol_blender.log
python3 tools/otisk_exportu.py zapis          # manifest vydani: hash vystupu a vstupu tohoto exportu (vydani.py overi)
# import Godotu hned po exportu (28. 10.: export prepsal modely/rostliny i s .import, testy a snimky bezely bez
# 162 modelu a textur - bile plochy, hodina snimku zbytecne): limity, import s kontrolou, textury pro tablet
python3 tools/limity_textur.py
godot --headless --path . --import > build/beh/export_import.log 2>&1
if grep -qE "ERR_FILE_CORRUPT|Error loading image|Failed loading resource" build/beh/export_import.log; then
    grep -E "ERR_FILE_CORRUPT|Error loading image|Failed loading resource" build/beh/export_import.log | head -10
    echo "IMPORT PO EXPORTU S CHYBAMI - log build/beh/export_import.log"
    stav CHYBA 8
    exit 8
fi
python3 tools/textury_tablet.py
stav OK 0
echo "EXPORT OK"
