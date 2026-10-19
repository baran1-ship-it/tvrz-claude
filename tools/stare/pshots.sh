#!/bin/bash
# Snimky z pohledu hrace vcetne HUD.  tools/pshots.sh [seznam cisel 01,03] [sirka vyska]
cd "$(dirname "$0")/.."
mkdir -p build/pshots
export TVRZ_TEST=shots TVRZ_OUT="$PWD/build/pshots" TVRZ_VIEWS="${1:-}"
W=${2:-1600}; H=${3:-1000}
timeout -k 5 ${TVRZ_TIMEOUT:-900} xvfb-run -a -s "-screen 0 ${W}x${H}x24" godot --path . --rendering-driver vulkan --resolution ${W}x${H} --audio-driver Dummy 2>&1 \
  | grep -vE "^$|^Godot Engine|^Vulkan |leaked|still in use|PagedAllocator|at: |ObjectDB" | head -60
