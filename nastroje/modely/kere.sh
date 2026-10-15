#!/bin/sh
cd /home/claude/work
while read SP SEED NAME H; do
  [ -z "$NAME" ] && continue
  python3 bush_geo.py $SP $SEED $NAME $H > log_$NAME.txt 2>&1
  python3 bush_far.py $NAME >> log_$NAME.txt 2>&1
  grep -E "^RESULT|^FAR" log_$NAME.txt | tr '\n' ' '; echo
done < kere_fronta.txt
echo KERE DONE
