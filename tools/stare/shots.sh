#!/bin/bash
# Pouziti: tools/shots.sh seznam.json [sirka vyska]  -> snimky do build/shots
cd "$(dirname "$0")/.."
mkdir -p build/shots
export TVRZ_SHOTS="$PWD/build/shots" TVRZ_SHOTLIST="$PWD/$1"
W=${2:-1280}; H=${3:-720}
timeout -k 5 ${TVRZ_TIMEOUT:-420} xvfb-run -a -s "-screen 0 ${W}x${H}x24" godot --path . --rendering-driver vulkan --resolution ${W}x${H} --audio-driver Dummy 2>&1 \
  | grep -vE "^$|^Godot Engine|^Vulkan |shot /" | head -${4:-40}
