#!/bin/bash
# Mereni zaseku pri prvnim zobrazeni mista (5. 11., lom a most): pocet a cas sestaveni shaderu (glLinkProgram) po presunu.
# Spoustet JEN pres beh: tools/beh.sh <jm> cmd bash tools/mereni_prvni.sh <kes_dir> ["mista"]   (env TVRZ_BEZ_PREDEHRATI=1 = bez predehrati)
# <kes_dir> = user:// pro tento beh (prazdna = studeny start jako 1. spusteni na tabletu; stejna podruhe = teply start z kese).
cd "$(dirname "$0")/.."
kes="$1"; mista="${2:-kostel;220,40,220,80|most;209,591,209,620|lom;143,945,120,945}"
mkdir -p "$kes" build
gcc -shared -fPIC -O2 -o build/glcount.so tools/glcount.c -ldl
TVRZ_PRVNI=1 GLCOUNT_POPIS=1 TVRZ_MERENI="$mista" MESA_SHADER_CACHE_DISABLE=true XDG_DATA_HOME="$kes" LD_PRELOAD="$PWD/build/glcount.so" \
  xvfb-run -a -s "-screen 0 640x400x24" godot --path . --rendering-driver opengl3 --rendering-method gl_compatibility \
  --resolution 640x400 2>&1 | grep -v "^     at:\|resource_format_binary\|invalid UID" | awk '
  /^GLLINK/ { n++; t += $3; if (po) print; next }
  /^ZNACKA konec predehrati/ { po = 1 }
  /^ZNACKA/ { printf "SESTAVENI %-28s %5d programu, %8.0f ms\n", "do: " $2 " " $3, n, t; n = 0; t = 0; print; next }
  { print }
  END { printf "SESTAVENI %-28s %5d programu, %8.0f ms\n", "zbytek", n, t }'
