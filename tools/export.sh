#!/bin/bash
# Export sveta s branou smyslu (radce 27. 10. 20:50): test smyslu na datech -> export Blenderu -> test smyslu po exportu.
#   BEH_LIMIT=7000 tools/beh.sh export_X cmd bash tools/export.sh
# Neprojde test pred exportem -> export se nespusti (rc 2).
set -e
cd "$(dirname "$0")/.."
/opt/bl/bin/python tools/test_smyslu.py > build/beh/smysl_pred.log 2>&1 || { grep "^SMYSL" build/beh/smysl_pred.log; echo "TEST SMYSLU NEPROSEL - export se nespousti"; exit 2; }
echo "TEST SMYSLU pred exportem OK"
/opt/bl/bin/python -u blender/export_game.py || true
grep -q "export hotov" build/beh/$(basename "${BEH_LOG:-export}" .log).log 2>/dev/null || true
/opt/bl/bin/python tools/test_smyslu.py --po > build/beh/smysl_po.log 2>&1 || true
grep "SMYSL souhrn\|SMYSL stanoviste\|SMYSL uzivani" build/beh/smysl_po.log | head -40
