#!/bin/bash
cd "$(dirname "$0")/.."
TVRZ_TEST=probe TVRZ_PROBE="$1" timeout -k 5 300 godot --headless --path . --audio-driver Dummy 2>&1 | grep -vE "^$|^Godot Engine|leaked|still in use|PagedAllocator|at: |ObjectDB|^trava|^flora|^build" | head -${2:-80}
