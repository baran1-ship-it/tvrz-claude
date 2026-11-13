#!/bin/bash
# $1 = tag ; ONLY env
cd /home/claude/z30
python3 -I scripts/outfit.py > /tmp/outfit.log 2>&1 || { grep -A5 Traceback /tmp/outfit.log; exit 1; }
python3 -I scripts/clip_test.py -- outfit.blend out/clip_$1.json 2>&1 | grep "noha\|ČAS"
