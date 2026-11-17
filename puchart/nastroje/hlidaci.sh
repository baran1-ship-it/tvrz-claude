#!/bin/bash
# Hlídači Puchartu (vrstvy z Havrana docs/havran/pipeline.md; Míša 2. 11.: „ať neopakujeme chyby z Havrana“).
# Rychlé (sekundy–minuty): import → geometrie → test smyslu → test průchodu → hlídač scén → matice vztahů → tabulka chyb.
# Volá export_apk.sh před stavbou APK; rc ≠ 0 = nevydávat. Výsledky build/*.json, souhrn build/hlidaci.txt.
#   bash nastroje/hlidaci.sh            celá sada (před vydáním)
#   bash nastroje/hlidaci.sh --rychle   jen data (geometrie, smysl, matice bez průchodu) – při každé změně
set -o pipefail
unset PUCHART_JEN PUCHART_TRASA PUCHART_SKRYJ PUCHART_DEST PUCHART_SKRIPT PUCHART_FOTO   # ladicí proměnné by tiše zúžily testy (audit 15. 11.)
K=$(cd "$(dirname "$0")/.." && pwd); G=${GODOT:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}
mkdir -p $K/build; S=$K/build/hlidaci.txt; : > $S; rc=0
# výšky pro hru (vysek.r16z, kolize a výška terénu ve hře) musí být z aktuální vysek.r16 (14. 11.: po přestavbě vsi zůstala
# r16z z minulého dne – hra stála na starém terénu, domy na nových plošinách nešly vstoupit; test průchodu to chytil)
for _r in vysek vysek_sit; do
  if [ $K/hra/data/$_r.r16 -nt $K/hra/data/$_r.r16z ]; then cp $K/nastroje/godot/r16_zstd.gd $K/hra/_r16z.gd && $G --headless --path $K/hra -s res://_r16z.gd | tee -a $S; rm -f $K/hra/_r16z.gd $K/hra/_r16z.gd.uid; break; fi
done
# staré výsledky pryč (QA 2. 11.: když Godot/Blender spadne, nesmí projít výsledky minulého běhu)
rm -f $K/build/kontrola_geometrie.json $K/build/test_smyslu.json $K/build/hlidaci_beh_godot.log $K/build/hlidaci_otisk
[ "$1" != "--rychle" ] && rm -f $K/build/pruchod.json $K/build/sceny.json $K/build/kontrola_scen.json $K/build/dosah.json $K/build/dosah.png
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
python3 -c "import json,sys;sys.exit(0 if json.load(open('$K/build/kontrola_geometrie.json')).get('hotovo') else 1)" 2>/dev/null || { rc=1; echo "GEOMETRIE CHYBA: výpočet nedoběhl do konce (hotovo chybí)" | tee -a $S; }
krok spoje; python3 $K/nastroje/kontrola_spoju.py $K 2>&1 | grep SPOJE | tee -a $S; [ ${PIPESTATUS[0]} -eq 0 ] || rc=1
krok "test smyslu"; python3 $K/nastroje/test_smyslu.py $K | grep -E "CHYBA|TEST_SMYSLU" | tee -a $S || rc=1
if [ "$1" != "--rychle" ]; then
  # průchod a scény souběžně (Havran 9. 11.: jeden headless Godot ≈ 1,1 jádra a 2,5 GB, stroj 4 jádra / 15 GB; import
  # se tu nedělá – oba jen čtou importovaná data)
  krok "test průchodu + hlídač scén (souběžně)"
  (cd $K/hra && PUCHART_TEST=sceny PUCHART_VYSTUP=$K/build/sceny.json timeout 2400 xvfb-run -a -s "-screen 0 640x400x24" $G --rendering-driver opengl3 --resolution 640x400 > $K/build/hlidaci_sceny_godot.log 2>&1) &
  _PSC=$!
  # + mřížka dosažitelnosti (pruchod:dosah, plán 17. 11. B1): díry a únik ze světa = CHYBA, uvíznutí / ostrovy / dveře bez dosahu
  # výpis; mapa build/dosah.png, nálezy build/dosah.json (pravidla kontroly_hra.json dosah)
  (cd $K/hra && PUCHART_TEST=pruchod PUCHART_VYSTUP=$K/build/pruchod.json PUCHART_DOSAH=$K/build/dosah.json timeout 5400 xvfb-run -a -s "-screen 0 1280x800x24" $G --rendering-driver opengl3 --resolution 1280x800 2>&1 | tee $K/build/hlidaci_beh_godot.log | grep -E "^PRUCHOD|^DOSAH (mřížka|uvíznutí [0-9]|cíle)" | cut -c1-200 | tee -a $S)
  # všechny trasy z dat i pevné testy musí mít výsledek OK (audit 15. 11.: chybějící trasa dřív prošla)
  python3 - "$K" <<'PY' | tee -a $S || rc=1
import json, sys
K = sys.argv[1]; d = json.load(open(K + "/build/pruchod.json"))
oc = set()
for f in ("pruchody.json", "pruchody_mista.json"):
    try: oc |= set(json.load(open(K + "/hra/data/" + f))["trasy"].keys())
    except Exception: pass
oc |= {"strom_kolize", "povrch_kolize", "vrata_funkce", "mapa_cestovani", "zebrik_lezeni", "dosah"}
chybi = sorted(oc - set(d)); spatne = sorted(k for k, v in d.items() if v != "OK")
print("PRUCHOD_UPLNOST tras %d, chybí %d %s, chybných %d %s" % (len(d), len(chybi), chybi[:6], len(spatne), spatne[:6]))
sys.exit(1 if chybi or spatne else 0)
PY
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
# měřicí APK (12. 11.: měření po konci běželo dál, chyba každý snímek a kamera se přetahovala s hráčem): zkrácené měření
# musí doběhnout všech úseků a variant, zastavit se a předat hru procházce – bez chyby skriptu
krok "klepnutí na dveře"; (cd $K/hra && PUCHART_SKRIPT=res://scripts/test_klik.gd timeout 600 xvfb-run -a -s "-screen 0 1280x800x24" $G --rendering-driver opengl3 --resolution 1280x800 2>&1 | grep -E "^KLIK_TEST" | tee -a $S)
grep -q "^KLIK_TEST dvere.*-> OK" $S || { rc=1; echo "KLIK CHYBA: tlačítko dveří nereaguje na dotyk" | tee -a $S; }
# dveře domů, vrata a vrátka ve vsi, krčmě a hájovně (Míša 13. 11.: „co jde, bude funkční“): klepnutí u dveří domu je přepne
krok "klepnutí na dveře ve vsi"; (cd $K/hra && PUCHART_SKRIPT=res://scripts/test_klik_ves.gd timeout 600 xvfb-run -a -s "-screen 0 1280x800x24" $G --rendering-driver opengl3 --resolution 1280x800 2>&1 | grep -E "^KLIK_VES_TEST" | tee -a $S)
grep -q "^KLIK_VES_TEST dvere.*-> OK" $S || { rc=1; echo "KLIK_VES CHYBA: dveře domu ve vsi nereagují na dotyk (nebo chybí vrata plotů)" | tee -a $S; }
krok "zapálení louče dotykem"; (cd $K/hra && PUCHART_SKRIPT=res://scripts/test_louc.gd timeout 600 xvfb-run -a -s "-screen 0 1280x800x24" $G --rendering-driver opengl3 --resolution 1280x800 2>&1 | grep -E "^LOUC_TEST" | tee -a $S)
grep -q "^LOUC_TEST zapaleni.*-> OK" $S || { rc=1; echo "LOUC CHYBA: akce předmětu nereaguje na dotyk" | tee -a $S; }
# ohně (Míša 15. 11.: „dodělej ohně“, místnost osvětlená ode dveří): místa z modelů, zapálit/uhasit, rozpočet světel
krok "ohně"; (cd $K/hra && PUCHART_SKRIPT=res://scripts/test_ohne.gd timeout 600 $G --headless 2>&1 | grep -E "^OHNE_TEST" | tee -a $S)
grep -q "^OHNE_TEST.*OK" $S || { rc=1; echo "OHNE CHYBA: ohně se nepostavily nebo nejdou zapálit/uhasit" | tee -a $S; }
# automatika detailu (plán 17. 11. A1, regulator.gd): simulované pomalé snímky ubírají stupně, klidné je vracejí, měření ji vypíná
krok "automatika detailu"; (cd $K/hra && PUCHART_SKRIPT=res://scripts/test_regulator.gd timeout 600 $G --headless 2>&1 | grep -E "^REGULATOR_TEST" | tee -a $S)
grep -q "^REGULATOR_TEST OK" $S || { rc=1; echo "REGULATOR CHYBA: automatika detailu nemění nebo nevrací stupně" | tee -a $S; }
# běh a létání na obrazovce (Míša 12. 11. večer, Havran hud.gd): dotyk na kruh Běh/Let přepne hrac.bezi/leti a zase zpět
krok "běh a let dotykem"; (cd $K/hra && PUCHART_SKRIPT=res://scripts/test_beh_let.gd timeout 600 xvfb-run -a -s "-screen 0 1280x800x24" $G --rendering-driver opengl3 --resolution 1280x800 2>&1 | grep -E "^BEHLET_TEST" | tee -a $S)
grep -q "^BEHLET_TEST OK" $S || { rc=1; echo "BEHLET CHYBA: kruh Běh nebo Let nereaguje na dotyk" | tee -a $S; }
# znaky mapy (Míša 17. 11.: „jen v pískovišti a potom v příběhu, když to objevím“): příběh skrytý → příchod → viditelný →
# uložit / nová hra / nahrát → zůstane; pískoviště vše hned
krok "znaky mapy a objevování"; (cd $K/hra && PUCHART_SKRIPT=res://scripts/test_mapa_znaky.gd timeout 600 xvfb-run -a -s "-screen 0 1280x800x24" $G --rendering-driver opengl3 --resolution 1280x800 2>&1 | grep -E "^MAPA_ZNAKY_TEST" | tee -a $S)
grep -q "^MAPA_ZNAKY_TEST OK" $S || { rc=1; echo "MAPA_ZNAKY CHYBA: znak zajímavého místa se neobjeví, nezůstane po nahrání nebo chybí v pískovišti" | tee -a $S; }
# hlavní nabídka a načítací obrazovka Blood for Blood (Míša 17. 11.): fokus šipkami/ovladačem, A/B, myš, dotyk, žádná pečeť;
# karty z dat (12–20, každá vlastní obrázek s autorem), karta vidět nejméně 10 s, prolnutí do černé (scripts/test_nabidka.gd)
krok "nabídka a načítací obrazovka"; (cd $K/hra && timeout 300 xvfb-run -a -s "-screen 0 1600x1000x24" $G --rendering-driver opengl3 --resolution 1600x1000 -s res://scripts/test_nabidka.gd 2>&1 | grep -E "^NABIDKA_TEST|CHYBA|SCRIPT ERROR" | tee -a $S)
grep -q "^NABIDKA_TEST OK" $S || { rc=1; echo "NABIDKA CHYBA: nabídka nebo načítací obrazovka (ovládání, data karet, 10 s)" | tee -a $S; }
krok "měření (zkrácené)"
(cd $K/hra && PUCHART_MERENI=1 PUCHART_MERENI_RYCHLE=1 PUCHART_MERENI_BEZ_CEKANI=1 timeout 420 xvfb-run -a -s "-screen 0 640x400x24" $G --rendering-driver opengl3 --resolution 640x400 > $K/build/hlidaci_mereni.log 2>&1)
MU=$(python3 -c "import json;d=json.load(open('$K/hra/data/mereni.json'));print(len(d['useky'])*len(d.get('scale_3d',[1]))+len(d.get('varianty',[])))")
if ! grep -q "^MERENI_KONEC úseků $MU" $K/build/hlidaci_mereni.log; then rc=1; echo "MERENI CHYBA: měření nedoběhlo všech $MU částí ($(grep -o 'MERENI_KONEC.*' $K/build/hlidaci_mereni.log))" | tee -a $S
elif grep -q "SCRIPT ERROR" $K/build/hlidaci_mereni.log; then rc=1; echo "MERENI CHYBA: chyba skriptu" | tee -a $S; grep -m3 -A2 "SCRIPT ERROR" $K/build/hlidaci_mereni.log | tee -a $S
else echo "MERENI OK: $MU částí, bez chyb" | tee -a $S; fi
# B4 (plán 17. 11.): kamera měření došla do cíle každého úseku (mereni.gd MERENI_CIL, mez hra/data/mereni.json dojit_mez_m)
if grep -q "^MERENI_CIL OK" $K/build/hlidaci_mereni.log; then grep -m1 "^MERENI_CIL" $K/build/hlidaci_mereni.log | tee -a $S
else rc=1; echo "MERENI_CIL CHYBA: $(grep -m1 -o 'MERENI_CIL.*' $K/build/hlidaci_mereni.log || echo 'kontrola cíle úseků nevypsána')" | tee -a $S; fi
krok "matice vztahů"; python3 $K/nastroje/kontrola_vztahu.py $K $1 | tee -a $S || rc=1
krok "tabulka chyb"; python3 $K/nastroje/kontrola_tabulek.py $K $1 | tee -a $S || rc=1
# poslední dobrá verze (GPT studio bod 7): při úspěchu uložit výsledky s commitem; při chybě vypsat rozdíl proti ní
[ "$1" != "--rychle" ] && python3 $K/nastroje/posledni_dobra.py $K $rc | tee -a $S
[ $rc = 0 ] && [ "$1" != "--rychle" ] && bash $K/nastroje/otisk_stavu.sh > $K/build/hlidaci_otisk   # otisk jen z celého úspěšného běhu
echo "HLIDACI $([ $rc = 0 ] && echo OK || echo CHYBA)" | tee -a $S
krok konec; cat $K/build/hlidaci_casy.txt | tee -a $S
exit $rc
