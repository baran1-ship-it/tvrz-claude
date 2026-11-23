#!/bin/bash
# Rychlý režim po KAŽDÉ změně (plán 18. 11. E4, podle Pucharta hlidaci.sh --rychle): sekundy, bez stavby světa v Godotu.
#   tools/rychle.sh            vše níže souběžně, souhrn RYCHLE OK | CHYBA (rc 1), logy build/rychle/<krok>.log
#   tools/rychle.sh --vse-gd   kontrola skriptů všech .gd (jinak jen změněných od posledního úspěšného běhu)
# Kroky: test smyslu (tools/test_smyslu.py), tabulky chyb (kontrola_tabulek.py), skripty (godot --check-only změněných .gd),
# platnost JSON v pravidla/, barvy vrcholů (barvy_vrcholu.py kontrola). Testy hry ve skupinách až před vydáním
# (tools/beh.sh <jm> skupiny), vše znovu jen před velkým vydáním (HLIDACI_VSE=1) – docs/pipeline.md „Kdy co běží“.
cd "$(dirname "$0")/.."
D=build/rychle; mkdir -p $D; rm -f $D/*.rc; t0=$(date +%s)
# E6: běží-li export světa, test smyslu by četl rozdělaná data (planý poplach) - počkat (nejdýl pasma.test.beh_cekani_s)
_cek=$(python3 -c "import json;print(int(json.load(open('pravidla/pravidla_sveta.json'))['pasma']['test']['beh_cekani_s']))")
while pgrep -f "^[^ ]*(python[0-9.]*|bash|sh) (-u )?[^ ]*(blender/export_game\.py|tools/export\.sh)" >/dev/null; do
  [ $(( $(date +%s) - t0 )) -gt $_cek ] && { echo "RYCHLE CHYBA: export světa běží déle než $((_cek/60)) min"; exit 3; }
  [ $(( $(date +%s) - t0 )) -lt 10 ] && echo "RYCHLE čekám na dokončení exportu světa"; sleep 10; done
krok() {   # $1 jméno, zbytek příkaz; rc do $D/<jméno>.rc, čas do .s
  local j=$1 s=$(date +%s); shift
  "$@" > $D/$j.log 2>&1; echo $? > $D/$j.rc; echo $(( $(date +%s) - s )) > $D/$j.s
}
# skripty: změněné .gd od posledního úspěšného běhu (značka), poprvé všechny - Parse Error za sekundy, 4 souběžně
zn=$D/.skripty_ok
# razítko ze ZAČÁTKU běhu (kontrola 23. 11.: značka nastavená až po běhu přeskočila .gd změněný během běhu)
zac=$D/.skripty_zacatek.$$; touch $zac
if [ "$1" = --vse-gd ] || [ ! -f $zn ]; then gd=$(ls scripts/*.gd tools/*.gd)
else gd=$(find scripts tools -name "*.gd" -newer $zn); fi
skripty() {
  [ $# = 0 ] && { echo "skriptů 0 (beze změny)"; return 0; }
  printf '%s\n' "$@" | xargs -P 4 -I{} sh -c 'timeout 60 godot --headless --path . --check-only -s "{}" 2>&1 | grep -qE "SCRIPT ERROR|Parse Error|ERROR: Failed" && { echo "CHYBA {}"; timeout 60 godot --headless --path . --check-only -s "{}" 2>&1 | grep -E -A2 "SCRIPT ERROR|Parse Error" | head -6; }; true' > $D/skripty_chyby.txt
  cat $D/skripty_chyby.txt; echo "skriptů $#"; ! grep -q "^CHYBA" $D/skripty_chyby.txt
}
json_pravidla() {
  python3 - <<'PY'
import json, glob, sys
sp = []
for f in sorted(glob.glob("pravidla/**/*.json", recursive=True)):
    try: json.load(open(f, encoding="utf-8"))
    except Exception as e: sp.append("%s: %s" % (f, e))
print("JSON pravidel %d, chybných %d" % (len(glob.glob("pravidla/**/*.json", recursive=True)), len(sp)))
for s in sp: print("CHYBA", s)
sys.exit(1 if sp else 0)
PY
}
krok smysl /opt/bl/bin/python tools/test_smyslu.py &
krok tabulky python3 tools/kontrola_tabulek.py &
krok barvy python3 tools/barvy_vrcholu.py kontrola &
krok lod python3 tools/lod_import.py kontrola &        # plan 18. 11. C14 citlive site bez LOD importu
krok json json_pravidla &
krok skripty skripty $gd &
wait
rc=0
for j in json skripty tabulky barvy lod smysl; do
  r=$(cat $D/$j.rc 2>/dev/null || echo 9)
  posl=$(grep -vE "^\s*$" $D/$j.log | tail -1 | cut -c1-150)
  printf "RYCHLE %-8s %s %3s s  %s\n" $j "$([ "$r" = 0 ] && echo "OK   " || echo CHYBA)" "$(cat $D/$j.s 2>/dev/null)" "$posl"
  if [ "$r" != 0 ]; then rc=1; grep -E "CHYBA|Error|ERROR" $D/$j.log | head -5 | sed 's/^/    /'; fi
done
if [ "$(cat $D/skripty.rc)" = 0 ]; then mv -f $zac $zn; else rm -f $zac; fi
echo "RYCHLE $([ $rc = 0 ] && echo OK || echo CHYBA) za $(( $(date +%s) - t0 )) s (logy $D/)"
exit $rc
