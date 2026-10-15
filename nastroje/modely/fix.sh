#!/bin/sh
cd /home/claude/work
while read SP SEED NAME AGE; do
  [ -z "$NAME" ] && continue
  python3 tree2_geo.py $SP $SEED $NAME $AGE > log2_$NAME.txt 2>&1
  python3 bush_far.py $NAME >> log2_$NAME.txt 2>&1
  grep -E "^RESULT|^FAR|Traceback" log2_$NAME.txt | tr '\n' ' '; echo
done < fix_fronta.txt
echo FIX DONE
