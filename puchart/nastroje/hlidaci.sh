#!/bin/bash
# Hlídači Puchartu (vrstvy z Havrana docs/havran/pipeline.md; Míša 2. 11.: „ať neopakujeme chyby z Havrana“).
# Rychlé (sekundy–minuty): import → geometrie → test smyslu → test průchodu → hlídač scén → matice vztahů → tabulka chyb.
# Volá export_apk.sh před stavbou APK; rc ≠ 0 = nevydávat. Výsledky build/*.json, souhrn build/hlidaci.txt.
#   bash nastroje/hlidaci.sh            celá sada (před vydáním)
#   bash nastroje/hlidaci.sh --rychle   jen data (geometrie, smysl, matice bez průchodu) – při každé změně
set -o pipefail
K=$(cd "$(dirname "$0")/.." && pwd); G=${GODOT:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}
mkdir -p $K/build; S=$K/build/hlidaci.txt; : > $S; rc=0
krok() { echo "== $1" | tee -a $S; }
krok import; (cd $K/hra && $G --headless --import > $K/build/import.log 2>&1) || true
grep -E "ERR_FILE_CORRUPT|Failed loading resource|No loader found" $K/build/import.log | head -5 | tee -a $S
krok geometrie; /opt/bl/bin/python $K/blender/kontrola_geometrie.py $K 2>&1 | grep GEOMETRIE | tee -a $S
krok "test smyslu"; python3 $K/nastroje/test_smyslu.py $K | grep -E "CHYBA|TEST_SMYSLU" | tee -a $S || rc=1
if [ "$1" != "--rychle" ]; then
  krok "test průchodu"
  (cd $K/hra && PUCHART_TEST=pruchod PUCHART_VYSTUP=$K/build/pruchod.json timeout 1500 xvfb-run -a -s "-screen 0 1280x800x24" $G --rendering-driver opengl3 --resolution 1280x800 2>&1 | grep -E "^PRUCHOD" | cut -c1-160 | tee -a $S)
  python3 -c "import json,sys;d=json.load(open('$K/build/pruchod.json'));sys.exit(0 if all(v=='OK' for v in d.values()) else 1)" || rc=1
  krok "hlídač scén"
  (cd $K/hra && PUCHART_TEST=sceny PUCHART_VYSTUP=$K/build/sceny.json timeout 2400 xvfb-run -a -s "-screen 0 640x400x24" $G --rendering-driver opengl3 --resolution 640x400 2>&1 | grep -E "^SCENY" | tee -a $S)
  python3 $K/nastroje/kontrola_scen.py $K | tee -a $S || rc=1
fi
krok "matice vztahů"; python3 $K/nastroje/kontrola_vztahu.py $K | tee -a $S || rc=1
krok "tabulka chyb"; python3 $K/nastroje/kontrola_tabulek.py $K | tee -a $S || rc=1
echo "HLIDACI $([ $rc = 0 ] && echo OK || echo CHYBA)" | tee -a $S
exit $rc
