#!/bin/sh
cd /home/claude/work
while kill -0 856 2>/dev/null; do sleep 20; done
python3 wagon_bake.py hi_wagon_plachta_1.blend zebrinak_plachta_1 2048 8 > bake_wagon2.log 2>&1
echo QUEUE2 DONE >> batch1.log
