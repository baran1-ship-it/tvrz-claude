#!/bin/bash
# Otisk stavu: obsah sledovaných souborů pracovní kopie (nezávislý na commitu) + upečená data hry. Hlídači ho zapíší po
# úspěchu (build/hlidaci_otisk), export_apk.sh porovná – stejný stav = hlídači se nespouští znovu.
K=$(cd "$(dirname "$0")/.." && pwd); cd $K
{ git ls-files -co --exclude-standard -- . | grep -vE '^(apk|data)/|sestava.json|data_manifest.json|^docs/' | sort | while read f; do [ -f "$f" ] && echo "$f $(git hash-object "$f")"; done
  find hra/data hra/modely hra/dlazdice -type f -printf '%P %s\n' 2>/dev/null | sort; } | md5sum | cut -c1-32
