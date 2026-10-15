#!/bin/sh
cd /home/claude/work
while kill -0 222 2>/dev/null; do sleep 15; done
./batch.sh fronta1.txt > batch1.log 2>&1
python3 wagon_bake.py hi_wagon_1.blend zebrinak_1 2048 8 > bake_wagon.log 2>&1
echo QUEUE DONE >> batch1.log
