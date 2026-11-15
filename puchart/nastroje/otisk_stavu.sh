#!/bin/bash
# Otisk stavu: obsah sledovaných souborů pracovní kopie (nezávislý na commitu) + upečená data hry. Hlídači ho zapíší po
# úspěchu (build/hlidaci_otisk), export_apk.sh porovná – stejný stav = hlídači se nespouští znovu. Sledované soubory jedním
# voláním git hash-object --stdin-paths (dřív proces na soubor, ~10 s).
K=$(cd "$(dirname "$0")/.." && pwd); cd $K
{ git ls-files -co --exclude-standard -- . | grep -vE '^(apk|data)/|sestava.json|data_manifest.json|dobra_verze.json|^docs/(screens|reference)/' | sort | while read f; do [ -f "$f" ] && echo "$f"; done | tee /tmp/otisk_cesty_$$ | sed "s|^|$K/|" | git hash-object --stdin-paths | paste -d' ' /tmp/otisk_cesty_$$ -; rm -f /tmp/otisk_cesty_$$
  find hra/data hra/modely hra/dlazdice hra/textury -type f -printf '%P %s %T@\n' 2>/dev/null | sort; } | md5sum | cut -c1-32   # i čas změny (audit 15. 11.: vysek.r16 má po přestavbě terénu stejnou velikost – otisk se neměnil a export hlídače přeskočil); docs/chyby.md patří do otisku
