#!/bin/sh
# batch: typ seed size jmeno tris px
cd /home/claude/work
while read TYP SEED SIZE NAME TRIS PX; do
  [ -z "$NAME" ] && continue
  [ -f out/$NAME.glb ] && { echo "SKIP $NAME"; continue; }
  python3 rock_geo.py $SEED hi_$NAME.blend $TYP $SIZE > log_$NAME.txt 2>&1
  python3 rock_bake.py hi_$NAME.blend $NAME $TRIS $PX 8 >> log_$NAME.txt 2>&1
  grep RESULT log_$NAME.txt || echo "FAIL $NAME"
done < "$1"
