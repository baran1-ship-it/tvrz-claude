#!/bin/bash
# Jediny spoustec vseho, co bezi v Godotu (testy, foceni, vydani) - aby beh nepadal na zamku nebo limitu:
#  - zamek /tmp/godot_beh.lock bere JEN tento skript (nikdy ho neobalovat dalsim flock ani timeout)
#  - limit je uvnitr (BEH_LIMIT s, vychozi 2400; foceni ~4 min stavba + ~4 min snimek), na konci vzdy jeden radek BEH <jmeno>: OK | CHYBA | LIMIT
#  - log build/beh/<jmeno>.log; pousti se na pozadi (run_in_background) a ceka se na oznameni, ne sleep
#  tools/beh.sh <jmeno> foto "oci;x,z,tx,tz;soubor.png|..."    snimky (xvfb, gl_compatibility jako tablet)
#  tools/beh.sh <jmeno> testy ["test1,test2"]                   tools/rychle_testy.sh (log Godotu build/beh/<jmeno>_godot.log)
#  tools/beh.sh <jmeno> cmd <prikaz...>                          cokoli jineho (napr. python3 tools/vydani.py ...)
cd "$(dirname "$0")/.."
jm="$1"; druh="$2"; shift 2
mkdir -p build/beh
# foto: slozky snimku zalozit predem (3. 11. f142: neexistujici build/f142 = "Can't save PNG", snimky ztraceny)
if [ "$druh" = foto ]; then echo "$1" | tr '|' '\n' | awk -F';' '{print $3}' | xargs -r -n1 dirname | sort -u | xargs -r mkdir -p; fi
log="build/beh/$jm.log"
lim="${BEH_LIMIT:-2400}"
# foto: limit podle poctu snimku (10. 11.: les_foto_po a stav4 padly na LIMIT 2400 s pri 2 soubeznych behach, snimek
# trval 9-15 min misto ~4) - zaklad + snimek x pocet z pasma.test.beh_limit_foto_*
if [ "$druh" = foto ] && [ -z "$BEH_LIMIT" ]; then
  n=$(echo "$1" | tr '|' '\n' | grep -c .)
  lim=$(python3 -c "import json;t=json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test'];print(t['beh_limit_foto_zaklad_s']+t['beh_limit_foto_snimek_s']*$n)")
fi
# Souběh (Míša 9. 11.: 5 pomocníků čekalo ve frontě na jeden Godot, stroj 4 jádra / 15 GB, jeden běh ~1,1 jádra a 2,5 GB):
#  - testy a foto = SDÍLENÝ zámek + jedno z N míst (pasma.test.beh_soubezne); nečtou ani nepíšou import (.godot)
#  - cmd (export, import, vydání) = VÝHRADNÍ zámek; čeká, až doběhnou sdílené běhy, a nové sdílené mezitím nepustí
#    (značka /tmp/godot_beh.vyhradne s pid čekajícího, jinak by ho stálý proud testů nikdy nepustil)
#  - cmd, který jen spouští testy/focení, smí jít sdíleně: BEH_SDILENE=1
#  - čekání na zámek se zapisuje do build/beh/cekani.log (kolik s, kdo, kolik míst)
exec 9>/tmp/godot_beh.lock
tc0=$(date +%s)
if [ "$druh" = cmd ] && [ -z "$BEH_SDILENE" ]; then
  echo $$ > /tmp/godot_beh.vyhradne
  if ! flock -w 1800 9; then rm -f /tmp/godot_beh.vyhradne; echo "BEH $jm: CHYBA zamek obsazeny 30 min ($(cat /tmp/godot_beh.kdo* 2>/dev/null | tr '\n' ' '))"; exit 3; fi
  rm -f /tmp/godot_beh.vyhradne; misto=vyhradne
else
  mist=$(python3 -c "import json;print(int(json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test'].get('beh_soubezne',1)))")
  while [ -f /tmp/godot_beh.vyhradne ] && kill -0 "$(cat /tmp/godot_beh.vyhradne 2>/dev/null)" 2>/dev/null; do
    [ $(( $(date +%s) - tc0 )) -gt 1800 ] && { echo "BEH $jm: CHYBA ceka export 30 min"; exit 3; }; sleep 5; done
  if ! flock -s -w 1800 9; then echo "BEH $jm: CHYBA zamek obsazeny 30 min ($(cat /tmp/godot_beh.kdo* 2>/dev/null | tr '\n' ' '))"; exit 3; fi
  misto=""
  while [ -z "$misto" ]; do
    for i in $(seq 1 "$mist"); do
      exec 8>/tmp/godot_beh.misto$i
      if flock -n 8; then misto=$i; break; fi
    done
    if [ -z "$misto" ]; then
      [ $(( $(date +%s) - tc0 )) -gt 1800 ] && { echo "BEH $jm: CHYBA vsechna mista obsazena 30 min"; exit 3; }; sleep 5
    fi
  done
fi
echo "$(date '+%F %T') $jm $druh cekal $(( $(date +%s) - tc0 )) s misto $misto" >> build/beh/cekani.log
kdo=/tmp/godot_beh.kdo; [ "$misto" != vyhradne ] && kdo=/tmp/godot_beh.kdo$misto
echo "$jm $(date +%T)" > $kdo; export BEH_ZAMEK=1
trap 'rm -f '"$kdo" EXIT
# disk (28. 10.: plny disk = useknute textury, poskozeny import i nastaveni editoru): pod pasma test beh_volno_mb
# se nic nespusti; prubeh hlida hlidac na pozadi a pri kriticke mezi beh zastavi (lepsi CHYBA nez rozbita data)
volno=$(df -m --output=avail / | tail -1 | tr -d ' ')
min_mb=$(python3 -c "import json;print(int(json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test']['beh_volno_mb']))")
if [ "$volno" -lt "$min_mb" ]; then
  echo "BEH $jm: CHYBA malo mista na disku ($volno MB < $min_mb MB) - nic nespusteno, uklid podle docs/predani.md"; exit 5
fi
t0=$(date +%s)
# pred focenim a testy: rychla kontrola skriptu zmenenych od posledni kontroly (Parse Error za 2 s, ne az po 15 min stavby)
if [ "$druh" = foto ] || [ "$druh" = testy ]; then
  zn=build/beh/.kontrola
  for f in $( [ -f $zn ] && find scripts tools -name "*.gd" -newer $zn || ls scripts/*.gd ); do
    if timeout 60 godot --headless --path . --check-only -s "$f" 2>&1 | grep -E "SCRIPT ERROR|Parse Error"; then
      echo "BEH $jm: CHYBA v $f (kontrola skriptu, nic nespusteno)"; exit 4
    fi
  done
  zm=$( [ -f $zn ] && find shaders -name "*.gdshader" -newer $zn | tr '\n' ' ' || ls shaders/*.gdshader | tr '\n' ' ' )
  if [ "$druh" = foto ] && [ -n "$zm" ]; then
    if SHADERY="$zm" timeout 120 xvfb-run -a -s "-screen 0 320x240x24" godot --path . --rendering-driver opengl3 \
        --rendering-method gl_compatibility --resolution 320x240 -s res://tools/kontrola_shaderu.gd 2>&1 | grep -E "SHADER ERROR|error\(" ; then
      echo "BEH $jm: CHYBA v shaderu ($zm, kontrola, nic nespusteno)"; exit 4
    fi
  fi
  touch $zn
fi
krit_mb=$(python3 -c "import json;print(int(json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test']['beh_kriticke_mb']))")
rm -f "build/beh/$jm.disk"
# hlidac nesmi drzet zamek (fd 9): kdyz hlavni beh skonci jinak nez normalne, osirely hlidac by zamek drzel navzdy
# (3. 11.: f142 hotovo, hlidac visel 40 min, vydani 0.9996 padlo na „zamek obsazeny“)
( exec 9>&- 8>&-; trap "exit 0" TERM; while kill -0 $$ 2>/dev/null && sleep 10; do
    v=$(df -m --output=avail / | tail -1 | tr -d ' ')
    if [ "$v" -lt "$krit_mb" ]; then echo "$v" > "build/beh/$jm.disk"; pkill -TERM -P $$ timeout; exit 0; fi
  done ) &
hlidac=$!
case "$druh" in
  foto) TVRZ_MERENI="$1" timeout "$lim" xvfb-run -a -s "-screen 0 1200x800x24" godot --path . --rendering-driver opengl3 \
          --rendering-method gl_compatibility --resolution 1200x800 > "$log" 2>&1 ;;
  testy) timeout "$lim" bash tools/rychle_testy.sh "${1:-}" "build/beh/${jm}_godot.log" > "$log" 2>&1 ;;
  cmd) timeout "$lim" "$@" > "$log" 2>&1 ;;
  *) echo "BEH $jm: CHYBA neznamy druh $druh"; exit 2 ;;
esac
rc=$?
kill $hlidac 2>/dev/null
if [ -f "build/beh/$jm.disk" ]; then
  echo "BEH $jm: CHYBA disk dosel behem behu ($(cat build/beh/$jm.disk) MB < $krit_mb MB) - beh zastaven, vystupy neplatne"; exit 5
fi
dt=$(( $(date +%s) - t0 ))
grep -E "^MERENI|SCRIPT ERROR|Parse Error|^SELHAL|^FAIL|^OK |cesty:" "$log" | head -25
if [ "$druh" = foto ]; then
  for f in $(echo "$1" | tr '|' '\n' | cut -d';' -f3); do [ -s "$f" ] || { echo "chybi snimek $f"; rc=1; }; done
fi
if grep -qE "SCRIPT ERROR|Parse Error" "$log"; then [ $rc -eq 0 ] && rc=1; fi
# chyby enginu ze seznamu tools/beh_chyby.txt (28. 10.: „Invalid array format“ rozbil teren vsi a snimky bezely
# 40 min dal jako OK): jakakoli = CHYBA, vypsat prvni
if [ "$druh" != cmd ] || grep -q "godot" <<< "$*"; then
  if grep -qFf tools/beh_chyby.txt "$log"; then
    echo "chyby enginu v logu:"; grep -Ff tools/beh_chyby.txt "$log" | sort | uniq -c | sort -rn | head -5
    [ $rc -eq 0 ] && rc=1
  fi
fi
if [ $rc -eq 124 ]; then echo "BEH $jm: LIMIT po ${dt} s (log $log)"; elif [ $rc -ne 0 ]; then echo "BEH $jm: CHYBA rc=$rc za ${dt} s (log $log)"; else echo "BEH $jm: OK za ${dt} s"; fi
exit $rc
