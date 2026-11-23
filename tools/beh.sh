#!/bin/bash
# Jediny spoustec vseho, co bezi v Godotu (testy, foceni, vydani) - aby beh nepadal na zamku nebo limitu:
#  - zamek /tmp/godot_beh.lock bere JEN tento skript (nikdy ho neobalovat dalsim flock ani timeout)
#  - limit je uvnitr (BEH_LIMIT s, vychozi 2400; foceni ~4 min stavba + ~4 min snimek), na konci vzdy jeden radek BEH <jmeno>: OK | CHYBA | LIMIT
#  - log build/beh/<jmeno>.log; pousti se na pozadi (run_in_background) a ceka se na oznameni, ne sleep
#  tools/beh.sh <jmeno> foto "oci;x,z,tx,tz;soubor.png|..."    snimky (xvfb, gl_compatibility jako tablet)
#  tools/beh.sh <jmeno> testy ["test1,test2"]                   tools/rychle_testy.sh (log Godotu build/beh/<jmeno>_godot.log)
#  tools/beh.sh <jmeno> cmd <prikaz...>                          cokoli jineho (napr. python3 tools/vydani.py ...)
#  tools/beh.sh <jmeno> testyfoto "test1,test2" "oci;x,z,tx,tz;s.png|..."   (plan 18. 11. E1) snimky a testy v JEDNOM behu
#       = jedna stavba sveta (~2 min usetreno proti testy + foto); nejdriv snimky, pak testy bez kresleni (jen testy
#       test_svet.gd S_KRESLENIM kresli); "vse" = cela sada, prazdny seznam = CHYBA
#  tools/beh.sh <jmeno> skupiny ["matice,voda|vse"] ["snimky"]   (plan E2) testy po skupinach podle otisku vstupu
#       (pravidla/hlidaci_skupiny.json, tools/hlidaci_skupiny.py): nezmenena skupina s poslednim OK se prevezme a nepousti,
#       vysledek skupiny se zapise hned, jak dobehne; HLIDACI_VSE=1 vse znovu; se snimky = testyfoto
#  po kazde zmene bez Godotu a stavby sveta: tools/rychle.sh (plan E4, sekundy)
#  tools/beh.sh <jmeno> svetlo "x,z,tx,tz" ["x,y,z,cx,cy,cz"]      kontrola svetla po zmene materialu (plan_18_11 C13):
#       misto rano/poledne/vecer (pasma.test.svetlo_hodiny) + interier v noci s louci v ruce -> build/svetlo/<jmeno>_*.png
cd "$(dirname "$0")/.."
jm="$1"; druh="$2"; shift 2
[ "$druh" = svetlo ] && { MISTO="$1"; INTERIER="${2:-}"; }
mkdir -p build/beh
# E6 (plan 18. 11.): bezi-li prave export sveta (Blender/Godot), testy a snimky pockaji - jinak plane poplachy z rozdelaneho
# exportu (Puchart 20. 11.); nejdyl pasma.test.beh_cekani_s
if [ "$druh" != cmd ]; then
  _c0=$(date +%s); _cek=$(python3 -c "import json;print(int(json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test']['beh_cekani_s']))")
  while pgrep -f "^[^ ]*(python[0-9.]*|bash|sh) (-u )?[^ ]*(blender/export_game\.py|tools/export\.sh)" >/dev/null; do
    [ $(( $(date +%s) - _c0 )) -gt $_cek ] && { echo "BEH $jm: CHYBA export sveta bezi dele nez $((_cek/60)) min"; exit 3; }
    [ "$_c0" = "$(date +%s)" ] && echo "BEH $jm: cekam na dokonceni exportu sveta"; sleep 10; done
fi
SKUPINY=""
if [ "$druh" = skupiny ]; then
  python3 tools/hlidaci_skupiny.py plan "$jm" "${1:-vse}" || exit 2
  SKUPINY=build/hlidaci_skupiny/$jm; _t=$(cat $SKUPINY/_testy.txt); _f="${2:-}"
  if [ -z "$_t" ] && [ -z "$_f" ]; then python3 tools/hlidaci_skupiny.py zapis "$jm" /dev/null --konec; echo "BEH $jm: OK za 0 s (vse prevzato, Godot nespusten)"; exit 0; fi
  if [ -z "$_t" ]; then druh=foto; set -- "$_f"; SKUPINY=""
  elif [ -z "$_f" ]; then druh=testy; set -- "$_t"
  else druh=testyfoto; set -- "$_t" "$_f"; fi
  # limit testu podle poctu (pravidla/hlidaci_skupiny.json limit_test_s x testu, nejmene limit_min_s)
  _n=$(echo "$_t" | tr ',' '\n' | grep -c .)
  export TVRZ_TEST_LIMIT=${TVRZ_TEST_LIMIT:-$(python3 -c "import json;p=json.load(open('pravidla/hlidaci_skupiny.json'));print(max(p['limit_min_s'],p['limit_test_s']*$_n))")}
fi
if [ "$druh" = testyfoto ]; then
  [ -z "$1" ] && { echo "BEH $jm: CHYBA testyfoto bez seznamu testu (cela sada = \"vse\")"; exit 2; }
  [ "$1" = vse ] && set -- "" "$2"
  TESTY_JEN="$1"; shift; FOTO_TF="$1"
fi
# svetlo = foto ze ctyr snimku (rano, poledne, vecer; interier v noci s louci - 5. pole "louc" v main._mereni)
if [ "$druh" = svetlo ]; then
  hod=$(python3 -c "import json;print(' '.join(str(h) for h in json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test']['svetlo_hodiny']))")
  set -- $hod; spec=""
  for nm in rano poledne vecer; do spec="$spec|sv_$nm;$MISTO;build/svetlo/${jm}_$nm.png;$1"; shift; done
  [ -n "$INTERIER" ] && spec="$spec|sv_interier;$INTERIER;build/svetlo/${jm}_interier.png;$1;louc"
  druh=foto; set -- "${spec#|}"
fi
# foto: slozky snimku zalozit predem (3. 11. f142: neexistujici build/f142 = "Can't save PNG", snimky ztraceny)
if [ "$druh" = foto ] || [ "$druh" = testyfoto ]; then echo "$1" | tr '|' '\n' | awk -F';' '{print $3}' | xargs -r -n1 dirname | sort -u | xargs -r mkdir -p; fi
log="build/beh/$jm.log"
lim="${BEH_LIMIT:-2400}"
# cekani na zamek (10. 11.: chuze_v10 i telo_v7 padly po 30 min ve fronte za dlouhymi testy) - pasma.test.beh_cekani_s
cek=$(python3 -c "import json;print(int(json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test']['beh_cekani_s']))")
# foto: limit podle poctu snimku (10. 11.: les_foto_po a stav4 padly na LIMIT 2400 s pri 2 soubeznych behach, snimek
# trval 9-15 min misto ~4) - zaklad + snimek x pocet z pasma.test.beh_limit_foto_*
if { [ "$druh" = foto ] || [ "$druh" = testyfoto ]; } && [ -z "$BEH_LIMIT" ]; then
  n=$(echo "$1" | tr '|' '\n' | grep -c .)
  lim=$(python3 -c "import json;t=json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test'];print(t['beh_limit_foto_zaklad_s']+t['beh_limit_foto_snimek_s']*$n)")
  [ "$druh" = testyfoto ] && lim=$(( lim + ${TVRZ_TEST_LIMIT:-300} ))
fi
[ "$druh" = testy ] && [ -n "$TVRZ_TEST_LIMIT" ] && [ -z "$BEH_LIMIT" ] && lim=$(( TVRZ_TEST_LIMIT + 300 ))
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
  if ! flock -w $cek 9; then rm -f /tmp/godot_beh.vyhradne; echo "BEH $jm: CHYBA zamek obsazeny $((cek/60)) min ($(cat /tmp/godot_beh.kdo* 2>/dev/null | tr '\n' ' '))"; exit 3; fi
  rm -f /tmp/godot_beh.vyhradne; misto=vyhradne
else
  mist=$(python3 -c "import json;print(int(json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test'].get('beh_soubezne',1)))")
  while [ -f /tmp/godot_beh.vyhradne ] && kill -0 "$(cat /tmp/godot_beh.vyhradne 2>/dev/null)" 2>/dev/null; do
    [ $(( $(date +%s) - tc0 )) -gt $cek ] && { echo "BEH $jm: CHYBA ceka export $((cek/60)) min"; exit 3; }; sleep 5; done
  if ! flock -s -w $cek 9; then echo "BEH $jm: CHYBA zamek obsazeny $((cek/60)) min ($(cat /tmp/godot_beh.kdo* 2>/dev/null | tr '\n' ' '))"; exit 3; fi
  # E5 (plan 18. 11., 23. 11.): misto se prideli, jen kdyz se vejde do pameti - soucet rezervaci obsazenych mist
  # + tento beh <= MemTotal - pasma.test.beh_pamet_rezerva_mb; rezervace podle druhu pasma.test.beh_pamet_mb (namereno
  # 23. 11.: headless testy spicka 3,1 GB, s obrazem (foto, testyfoto) 7,4 GB) -> 2 testy nebo testy + foto naraz, 2 foto ne
  read pamet_mb rez_mb < <(python3 -c "import json;t=json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test'];p=t['beh_pamet_mb'];print(int(p.get('$druh',p['cmd'])),int(t['beh_pamet_rezerva_mb']))")
  celk_mb=$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo)
  misto=""
  while [ -z "$misto" ]; do
    for i in $(seq 1 "$mist"); do
      exec 8>/tmp/godot_beh.misto$i
      if flock -n 8; then
        obs=0
        for j in $(seq 1 "$mist"); do
          [ "$j" = "$i" ] && continue
          if ! flock -n /tmp/godot_beh.misto$j true 2>/dev/null; then
            r=$(awk '{print $3}' /tmp/godot_beh.kdo$j 2>/dev/null); obs=$(( obs + ${r:-$pamet_mb} ))
          fi
        done
        if [ $(( obs + pamet_mb )) -le $(( celk_mb - rez_mb )) ]; then misto=$i; break; fi
        exec 8>&-
      fi
    done
    if [ -z "$misto" ]; then
      [ $(( $(date +%s) - tc0 )) -gt $cek ] && { echo "BEH $jm: CHYBA vsechna mista obsazena nebo malo pameti $((cek/60)) min"; exit 3; }; sleep 5
    fi
  done
fi
echo "$(date '+%F %T') $jm $druh cekal $(( $(date +%s) - tc0 )) s misto $misto" >> build/beh/cekani.log
kdo=/tmp/godot_beh.kdo; [ "$misto" != vyhradne ] && kdo=/tmp/godot_beh.kdo$misto
echo "$jm $(date +%T) ${pamet_mb:-0}" > $kdo; export BEH_ZAMEK=1
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
if [ "$druh" = foto ] || [ "$druh" = testy ] || [ "$druh" = testyfoto ]; then
  zn=build/beh/.kontrola
  for f in $( [ -f $zn ] && find scripts tools -name "*.gd" -newer $zn || ls scripts/*.gd ); do
    if timeout 60 godot --headless --path . --check-only -s "$f" 2>&1 | grep -E "SCRIPT ERROR|Parse Error"; then
      echo "BEH $jm: CHYBA v $f (kontrola skriptu, nic nespusteno)"; exit 4
    fi
  done
  zm=$( [ -f $zn ] && find shaders -name "*.gdshader" -newer $zn | tr '\n' ' ' || ls shaders/*.gdshader | tr '\n' ' ' )
  if [ "$druh" != testy ] && [ -n "$zm" ]; then
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
# E2: skupina se zapise hned, jak dobehnou jeji testy (restart kontejneru = dalsi beh prevezme hotove skupiny)
if [ -n "$SKUPINY" ]; then
  ( exec 9>&- 8>&-; trap "exit 0" TERM; while kill -0 $$ 2>/dev/null && sleep 20; do
      python3 tools/hlidaci_skupiny.py zapis "$jm" "build/beh/${jm}_godot.log" >> "$SKUPINY/zapis.log" 2>&1; done ) &
  zapisovac=$!
fi
case "$druh" in
  foto) TVRZ_MERENI="$1" timeout "$lim" xvfb-run -a -s "-screen 0 1200x800x24" godot --path . --rendering-driver opengl3 \
          --rendering-method gl_compatibility --resolution 1200x800 > "$log" 2>&1 ;;
  testy) timeout "$lim" bash tools/rychle_testy.sh "${1:-}" "build/beh/${jm}_godot.log" > "$log" 2>&1 ;;
  testyfoto)
    # jedna stavba sveta: snimky (TVRZ_MERENI), pak testy (main._mereni -> dev_test.gd); log Godotu build/beh/<jm>_godot.log
    # (kontrola_vztahu.py ho najde jako log testu), do <jm>.log cela cast snimku (chyby enginu jako foto) + radky testu
    glog="build/beh/${jm}_godot.log"
    TVRZ_TESTYFOTO=1 TVRZ_TEST=svet TVRZ_TEST_JEN="$TESTY_JEN" TVRZ_MERENI="$FOTO_TF" timeout "$lim" xvfb-run -a -s "-screen 0 1200x800x24" \
      godot --path . --rendering-driver opengl3 --rendering-method gl_compatibility --resolution 1200x800 > "$glog" 2>&1
    rc=$?
    { sed '/^OTISK /,$d' "$glog"; grep -E "^TEST|^HOTOVO_TEST|SCRIPT ERROR|Parse Error" "$glog" | cut -c1-600; } > "$log"
    if [ -f build/protokol_stavby.json ] && [ build/protokol_stavby.json -nt tools/rychle_testy.sh ]; then
      python3 tools/protokol_mapa.py --log "$glog" | tail -1 >> "$log"; fi
    [ $rc -eq 0 ] && ! grep -q "^TEST SVET " "$glog" && { echo "TEST CHYBA: beh bez souhrnu TEST SVET" >> "$log"; rc=1; }
    (exit $rc) ;;
  cmd) timeout "$lim" "$@" > "$log" 2>&1 ;;
  *) echo "BEH $jm: CHYBA neznamy druh $druh"; exit 2 ;;
esac
rc=$?
if [ -n "$SKUPINY" ]; then
  kill $zapisovac 2>/dev/null
  python3 tools/hlidaci_skupiny.py zapis "$jm" "build/beh/${jm}_godot.log" --konec | tee -a "$log" | grep -E "^SKUPINA|^HLIDACI"
  sk_rc=${PIPESTATUS[0]}; [ $rc -eq 0 ] && rc=$sk_rc
fi
kill $hlidac 2>/dev/null
if [ -f "build/beh/$jm.disk" ]; then
  echo "BEH $jm: CHYBA disk dosel behem behu ($(cat build/beh/$jm.disk) MB < $krit_mb MB) - beh zastaven, vystupy neplatne"; exit 5
fi
dt=$(( $(date +%s) - t0 ))
grep -E "^MERENI|SCRIPT ERROR|Parse Error|^SELHAL|^FAIL|^OK |cesty:" "$log" | head -25
[ "$druh" = testyfoto ] && { grep -E "^TEST .* CHYBA|^TEST (SVET|STAVBY|VODA|VYKON) " "$log" | head -20; }
if [ "$druh" = foto ] || [ "$druh" = testyfoto ]; then
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
