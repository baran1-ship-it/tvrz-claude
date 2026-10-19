#!/bin/bash
# Rychla kontrola: spusti hru bez vykreslovani a vypise chyby skriptu.
cd "$(dirname "$0")/.."
timeout -k 5 ${1:-180} godot --headless --path . --quit-after ${2:-4} 2>&1 | grep -vE "^$|^Godot Engine" | head -${3:-40}
