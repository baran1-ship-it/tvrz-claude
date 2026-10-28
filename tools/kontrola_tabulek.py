"""Tabulky chyb (docs/rozpracovane/*chyby*.md): opraveny radek musi mit kontrolu v testu (CLAUDE.md: „kazda nova
chyba, kterou najde clovek = nova kontrola v testu“). Kontrola = jmeno testu (test smyslu / test_svet.gd) nebo
"snimek <jmeno>" u ciste vizualni veci; prazdna nebo "(doplnit)" = chyba. Vypise chybejici, rc 1."""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOTOVO = re.compile(r"opraven|hotovo|v kódu|v datech|v kodu", re.I)
chybi = []
for f in sorted(glob.glob(os.path.join(ROOT, "docs", "rozpracovane", "*chyby*.md"))):
    hlav = None
    for ln in open(f, encoding="utf-8"):
        if not ln.startswith("|"):
            hlav = None if not ln.strip() else hlav
            continue
        b = [c.strip() for c in ln.strip().strip("|").split("|")]
        if hlav is None:
            hlav = [c.lower() for c in b]
            continue
        if set("".join(b)) <= set("-: "):
            continue
        ik = next((i for i, c in enumerate(hlav) if c.startswith("kontrola")), None)
        ist = next((i for i, c in enumerate(hlav) if c.startswith("stav")), None)
        if ik is None or ist is None or len(b) <= max(ik, ist):
            continue
        if HOTOVO.search(b[ist]) and (b[ik] == "" or "doplnit" in b[ik]):
            chybi.append("%s #%s %s" % (os.path.basename(f), b[0], b[1][:70]))
for c in chybi:
    print("BEZ KONTROLY " + c)
print("tabulky chyb: %d opravenych radku bez kontroly" % len(chybi))
sys.exit(1 if chybi else 0)
