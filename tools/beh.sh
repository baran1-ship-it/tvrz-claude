#!/bin/bash
# Jediny spoustec vseho, co bezi v Godotu (testy, foceni, vydani) - aby beh nepadal na zamku nebo limitu:
#  - zamek /tmp/godot_beh.lock bere JEN tento skript (nikdy ho neobalovat dalsim flock ani timeout)
#  - limit je uvnitr (BEH_LIMIT s, vychozi 1500), na konci vzdy jeden radek BEH <jmeno>: OK | CHYBA | LIMIT
#  - log build/beh/<jmeno>.log; pousti se na pozadi (run_in_background) a ceka se na oznameni, ne sleep
#  tools/beh.sh <jmeno> foto "oci;x,z,tx,tz;soubor.png|..."    snimky (xvfb, gl_compatibility jako tablet)
#  tools/beh.sh <jmeno> testy                                    tools/rychle_testy.sh
#  tools/beh.sh <jmeno> cmd <prikaz...>                          cokoli jineho (napr. python3 tools/vydani.py ...)
cd "$(dirname "$0")/.."
jm="$1"; druh="$2"; shift 2
mkdir -p build/beh
log="build/beh/$jm.log"
lim="${BEH_LIMIT:-1500}"
exec 9>/tmp/godot_beh.lock
if ! flock -w 1800 9; then echo "BEH $jm: CHYBA zamek obsazeny 30 min ($(cat /tmp/godot_beh.kdo 2>/dev/null))"; exit 3; fi
echo "$jm $(date +%T)" > /tmp/godot_beh.kdo; export BEH_ZAMEK=1
t0=$(date +%s)
case "$druh" in
  foto) TVRZ_MERENI="$1" timeout "$lim" xvfb-run -a -s "-screen 0 1200x800x24" godot --path . --rendering-driver opengl3 \
          --rendering-method gl_compatibility --resolution 1200x800 > "$log" 2>&1 ;;
  testy) timeout "$lim" bash tools/rychle_testy.sh > "$log" 2>&1 ;;
  cmd) timeout "$lim" "$@" > "$log" 2>&1 ;;
  *) echo "BEH $jm: CHYBA neznamy druh $druh"; exit 2 ;;
esac
rc=$?
dt=$(( $(date +%s) - t0 ))
grep -E "^MERENI|SCRIPT ERROR|Parse Error|^SELHAL|^FAIL|^OK |cesty:" "$log" | head -25
if [ "$druh" = foto ]; then
  for f in $(echo "$1" | tr '|' '\n' | cut -d';' -f3); do [ -s "$f" ] || { echo "chybi snimek $f"; rc=1; }; done
fi
if grep -qE "SCRIPT ERROR|Parse Error" "$log"; then [ $rc -eq 0 ] && rc=1; fi
if [ $rc -eq 124 ]; then echo "BEH $jm: LIMIT po ${dt} s (log $log)"; elif [ $rc -ne 0 ]; then echo "BEH $jm: CHYBA rc=$rc za ${dt} s (log $log)"; else echo "BEH $jm: OK za ${dt} s"; fi
exit $rc
