#!/bin/bash
# Export sveta s branou smyslu (radce 27. 10. 20:50): test smyslu na datech -> export Blenderu -> test smyslu po exportu.
#   BEH_LIMIT=7000 tools/beh.sh export_X cmd bash tools/export.sh
# Zadna chyba se nepolyka (Astra 22:00: drive "|| true", export i test smely selhat a skript skoncil OK):
#   rc 2 = test smyslu pred exportem neprosel (export se nespusti)
#   rc 3 = Blender export skoncil chybou nebo bez radku "export hotov"
#   rc 4 = test smyslu po exportu neprosel (svet.json je, ale nesmi se balit ani vydat)
# Logy zustavaji v build/beh/ (smysl_pred.log, export_blender.log, smysl_po.log).
set -o pipefail
cd "$(dirname "$0")/.."
mkdir -p build/beh
# stav exportu pro tools/vydani.py: bali jen svet, ktery prosel obema testy (md5 svet.json = presne ten export)
stav() { echo "{\"stav\": \"$1\", \"rc\": $2, \"svet_md5\": \"$(md5sum modely/svet.json 2>/dev/null | cut -d' ' -f1)\", \"cas\": \"$(date -u +%FT%TZ)\"}" > build/export_stav.json; }
stav BEZI 1
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
if ! /opt/bl/bin/python tools/test_smyslu.py --po > build/beh/smysl_po.log 2>&1; then
    grep "^SMYSL" build/beh/smysl_po.log | head -60
    echo "TEST SMYSLU PO EXPORTU NEPROSEL - nebalit, nevydavat"
    stav CHYBA 4
    exit 4
fi
grep "SMYSL souhrn" build/beh/smysl_po.log
stav OK 0
echo "EXPORT OK"
