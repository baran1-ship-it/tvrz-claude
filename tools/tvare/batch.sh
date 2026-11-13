#!/bin/bash
cd /home/claude/tv
ids=$(python3 -c "import json; print(' '.join(json.load(open('scripts/tvare_spec.json'))))")
echo $ids | tr ' ' '\n' | xargs -P 2 -I{} sh -c 'python3 -I scripts/tvar.py -- {} render > out/log_{}.txt 2>&1; grep -h "VLASY_TROJ\|Error" out/log_{}.txt | head -2'
echo BATCH_HOTOVO
