#!/bin/bash
# Hlídači Puchartu (vrstvy z Havrana docs/havran/pipeline.md; Míša 2. 11.: „ať neopakujeme chyby z Havrana“).
# Rychlé (sekundy–minuty): import → geometrie → test smyslu → test průchodu → hlídač scén → matice vztahů → tabulka chyb.
# Volá export_apk.sh před stavbou APK; rc ≠ 0 = nevydávat. Výsledky build/*.json, souhrn build/hlidaci.txt.
#   bash nastroje/hlidaci.sh            celá sada (před vydáním)
#   bash nastroje/hlidaci.sh --rychle   jen data (geometrie, smysl, matice bez průchodu) – při každé změně
set -o pipefail
K=$(cd "$(dirname "$0")/.." && pwd); G=${GODOT:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}
mkdir -p $K/build; S=$K/build/hlidaci.txt; : > $S; rc=0
# staré výsledky pryč (QA 2. 11.: když Godot/Blender spadne, nesmí projít výsledky minulého běhu)
rm -f $K/build/kontrola_geometrie.json $K/build/test_smyslu.json $K/build/hlidaci_beh_godot.log $K/build/hlidaci_otisk
[ "$1" != "--rychle" ] && rm -f $K/build/pruchod.json $K/build/sceny.json $K/build/kontrola_scen.json
# trvání kroků (rada 9. 11.: měřit čekací doby, ať je vidět, co má smysl pouštět souběžně) → build/hlidaci_casy.txt
_T0=$(date +%s); _KROK=""; : > $K/build/hlidaci_casy.txt
krok() { _T=$(date +%s); [ -n "$_KROK" ] && echo "$_KROK $((_T - _T0)) s" >> $K/build/hlidaci_casy.txt; _KROK="$1"; _T0=$_T; echo "== $1" | tee -a $S; }
krok import; (cd $K/hra && $G --headless --import > $K/build/import.log 2>&1) || true
grep -E "ERR_FILE_CORRUPT|Failed loading resource|No loader found" $K/build/import.log | head -5 | tee -a $S
# vrstva 0 (Havran): skripty se načtou bez chyby – 2. 11. parse chyba v hlavni.gd prošla až do testu průchodu
krok skripty; (cd $K/hra && timeout 300 $G --headless --quit-after 30 > $K/build/skripty.log 2>&1) || true
cp $K/nastroje/godot/nacti_skripty.gd $K/hra/_nacti_skripty.gd; (cd $K/hra && timeout 300 $G --headless -s res://_nacti_skripty.gd >> $K/build/skripty.log 2>&1) || echo "SKRIPT_CHYBA nacitani" >> $K/build/skripty.log; rm -f $K/hra/_nacti_skripty.gd*
if grep -E "SCRIPT ERROR|Parse Error|Failed to load script|SKRIPT_CHYBA" $K/build/skripty.log | head -5 | tee -a $S | grep -q .; then rc=1; echo "SKRIPTY CHYBA" | tee -a $S; else echo "SKRIPTY OK" | tee -a $S; fi
# kód zakomentovaný komentářem uprostřed řádku (9. 11. dvakrát: „bod(a),   # komentář bod(b)…“ – trasa tiše bez bodů)
for _py in $K/blender/*.py $K/nastroje/*.py; do python3 -m py_compile "$_py" 2>&1 | tee -a $S | grep -q . && rc=1; done
if grep -nE "#[^\"']*\bbod\(" $K/blender/*.py | tee -a $S | grep -q .; then rc=1; echo "KOMENTAR_USEKL_KOD CHYBA" | tee -a $S; fi
krok geometrie; /opt/bl/bin/python $K/blender/kontrola_geometrie.py $K 2>&1 | grep GEOMETRIE | tee -a $S
[ -s $K/build/kontrola_geometrie.json ] || { rc=1; echo "GEOMETRIE CHYBA: bez výsledku" | tee -a $S; }
krok spoje; python3 $K/nastroje/kontrola_spoju.py $K 2>&1 | grep SPOJE | tee -a $S; [ ${PIPESTATUS[0]} -eq 0 ] || rc=1
krok "test smyslu"; python3 $K/nastroje/test_smyslu.py $K | grep -E "CHYBA|TEST_SMYSLU" | tee -a $S || rc=1
if [ "$1" != "--rychle" ]; then
  # průchod a scény souběžně (Havran 9. 11.: jeden headless Godot ≈ 1,1 jádra a 2,5 GB, stroj 4 jádra / 15 GB; import
  # se tu nedělá – oba jen čtou importovaná data)
  krok "test průchodu + hlídač scén (souběžně)"
  (cd $K/hra && PUCHART_TEST=sceny PUCHART_VYSTUP=$K/build/sceny.json timeout 2400 xvfb-run -a -s "-screen 0 640x400x24" $G --rendering-driver opengl3 --resolution 640x400 > $K/build/hlidaci_sceny_godot.log 2>&1) &
  _PSC=$!
  (cd $K/hra && PUCHART_TEST=pruchod PUCHART_VYSTUP=$K/build/pruchod.json timeout 2700 xvfb-run -a -s "-screen 0 1280x800x24" $G --rendering-driver opengl3 --resolution 1280x800 2>&1 | tee $K/build/hlidaci_beh_godot.log | grep -E "^PRUCHOD" | cut -c1-160 | tee -a $S)
  python3 -c "import json,sys;d=json.load(open('$K/build/pruchod.json'));sys.exit(0 if all(v=='OK' for v in d.values()) else 1)" || rc=1
  wait $_PSC
  grep -E "^SCENY" $K/build/hlidaci_sceny_godot.log | tee -a $S; cat $K/build/hlidaci_sceny_godot.log >> $K/build/hlidaci_beh_godot.log
  [ -s $K/build/sceny.json ] || { rc=1; echo "SCENY CHYBA: bez výsledku" | tee -a $S; }
  python3 $K/nastroje/kontrola_scen.py $K | tee -a $S || rc=1
fi
# chyby skriptů za běhu v testech (2. 11.: chyba mlha_od prošla kontrolou načtení, objevila se až v testu)
if grep -hE "SCRIPT ERROR" $K/build/hlidaci_beh_godot.log 2>/dev/null | head -3 | tee -a $S | grep -q .; then rc=1; echo "SKRIPTY ZA BEHU CHYBA" | tee -a $S; fi
# rozpočet uzlů scény (pád na tabletu 11. 11. – vrstvy stavěné na celou mapu, došla paměť): výpis UZLY z každého startu hry v testech
UMAX=$(python3 -c "import json;print(json.load(open('$K/pravidla/svet/rozpocty.json'))['pamet']['uzlu_max'])")
UN=$(grep -ohE "^UZLY celkem [0-9]+" $K/build/hlidaci_beh_godot.log 2>/dev/null | awk '{print $3}' | sort -n | tail -1)
if [ -z "$UN" ]; then [ "$1" != "--rychle" ] && { rc=1; echo "UZLY CHYBA: hra nevypsala počet uzlů" | tee -a $S; }
elif [ "$UN" -gt "$UMAX" ]; then rc=1; echo "UZLY CHYBA: $UN uzlů po startu > rozpočet $UMAX (rozpocty.json pamet.uzlu_max)" | tee -a $S
else echo "UZLY OK: $UN (rozpočet $UMAX)" | tee -a $S; fi
# louče a svícny v tmavých místnostech (11. 11.: při běžném startu 0/20 – hledaly zeď dřív, než vznikly kolize hradu)
for sv in $(grep -ohE "^SVICNY [0-9]+/[0-9]+" $K/build/hlidaci_beh_godot.log 2>/dev/null | awk '{print $2}' | sort -u); do
  [ "${sv%/*}" != "${sv#*/}" ] && { rc=1; echo "SVICNY CHYBA: postaveno $sv (každé světlo bez dne potřebuje louč/svícen)" | tee -a $S; }
done
krok "matice vztahů"; python3 $K/nastroje/kontrola_vztahu.py $K $1 | tee -a $S || rc=1
krok "tabulka chyb"; python3 $K/nastroje/kontrola_tabulek.py $K $1 | tee -a $S || rc=1
# poslední dobrá verze (GPT studio bod 7): při úspěchu uložit výsledky s commitem; při chybě vypsat rozdíl proti ní
[ "$1" != "--rychle" ] && python3 $K/nastroje/posledni_dobra.py $K $rc | tee -a $S
[ $rc = 0 ] && [ "$1" != "--rychle" ] && bash $K/nastroje/otisk_stavu.sh > $K/build/hlidaci_otisk   # otisk jen z celého úspěšného běhu
echo "HLIDACI $([ $rc = 0 ] && echo OK || echo CHYBA)" | tee -a $S
krok konec; cat $K/build/hlidaci_casy.txt | tee -a $S
exit $rc
