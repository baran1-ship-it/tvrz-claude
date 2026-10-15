#!/bin/sh
cd /home/claude/work
while read SP SEED NAME AGE; do
  [ -z "$NAME" ] && continue
  python3 tree_geo.py $SP $SEED $NAME $AGE > log_$NAME.txt 2>&1
  python3 bush_far.py $NAME >> log_$NAME.txt 2>&1
  grep -E "^RESULT|^FAR|Traceback" log_$NAME.txt | tr '\n' ' '; echo
done < stromy_fronta.txt
echo STROMY DONE
