#!/bin/bash
# Rychle testy (radce 17:50): headless, bez renderu (llvmpipe = 1-3 s na snimek), jen vypocet nad daty a fyzika.
# Watchdog 5 min = CHYBA. Pouziti: bash tools/rychle_testy.sh "dvere_domu,lezeni" [log]
# Vykon, pamet, chuze s renderem, snimky = sada "tablet" - na PC nespoustet.
cd "$(dirname "$0")/.."
LOG=${2:-/tmp/rychle_testy.log}
[ -n "$BEH_ZAMEK" ] || { exec 9>/tmp/godot_beh.lock; flock 9; }   # pres tools/beh.sh uz zamek drzi
TVRZ_TEST=svet TVRZ_TEST_JEN="$1" timeout 300 godot --headless --path . > "$LOG" 2>&1
r=$?
[ $r -eq 124 ] && echo "TEST WATCHDOG CHYBA: vic nez 5 min ($1)"
grep -E "^TEST|SCRIPT ERROR|Parse Error" "$LOG" | cut -c1-600
# mapa stavby a chyb (tools/protokol_mapa.py): kroky, ktere menily teren, a chyby testu na mape - build/mapa_stavby.png
if [ -f build/protokol_stavby.json ] && [ build/protokol_stavby.json -nt "$0" ]; then
  python3 tools/protokol_mapa.py --log "$LOG" | tail -1
fi
