#!/bin/sh
cd /home/claude/work
while kill -0 1059 2>/dev/null; do sleep 20; done
for n in parez_1 parez_2 parez_3 kmen_1 kmen_2 kmen_3; do
  python3 wagon_bake.py hi_$n.blend $n 1024 8 > bake_$n.log 2>&1
  grep RESULT bake_$n.log >> batch1.log || echo "FAIL $n" >> batch1.log
done
echo QUEUE3 DONE >> batch1.log
