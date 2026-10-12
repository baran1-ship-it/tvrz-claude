#!/bin/bash
# Automaticky test bez vykreslovani: chuze po vsech mistnostech, luk, interakce, dotyk.
cd "$(dirname "$0")/.."
TVRZ_TEST=walk timeout -k 5 ${1:-900} godot --headless --path . --audio-driver Dummy 2>&1 | grep -vE "^$|^Godot Engine|leaked|still in use|PagedAllocator|at: |ObjectDB" | head -${2:-150}
