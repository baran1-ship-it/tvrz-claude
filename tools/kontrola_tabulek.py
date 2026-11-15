"""Tabulky chyb (docs/rozpracovane/*chyby*.md): opraveny radek musi mit kontrolu v testu (CLAUDE.md: „kazda nova
chyba, kterou najde clovek = nova kontrola v testu“). Kontrola = jmeno testu (test smyslu / test_svet.gd) nebo
"snimek <jmeno>" u ciste vizualni veci; prazdna nebo "(doplnit)" = chyba. Vypise chybejici, rc 1.

15. 11. (hlidaci z Pucharta #5, docs/rozpracovane/hlidaci_z_pucharta.md):
  - stav radku se hleda i bez sloupce Stav (misa_099, misa_0992) a tam, kde ho radek nese jinde (misa_28 r. 49-89
    ma stav ve sloupci Kontrola) - klicova slova pravidla/svet/kontroly.json tabulky (otevrene / hotove);
  - otevrene radky (ceka, rozbor, navrzeno, neovereno, castecne...) a radky bez stavu se VYPISI se souctem - stare tabulky
    vydani neblokuji; v NEJNOVEJSI tabulce (posledni pridana do gitu) je otevreny radek bez duvodu chyba;
  - (Puchart) hotovy radek, jehoz kontrola jmenuje test (`jmeno` z test_svet.gd / test_smyslu), musi mit ten test
    existujici a v poslednim behu (logy kontroly.json tabulky.logy_testu) OK; neexistujici nebo padly test = chyba
    v nejnovejsi tabulce, ve starsich vypis. Test, ktery v zadnem logu nebezel, se vypise (NEBEZEL).
  python3 tools/kontrola_tabulek.py [--vse]     --vse: vypsat vsechny otevrene radky (jinak prvnich 15 na tabulku)"""
import glob
import os
import re
import subprocess
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KT = json.load(open(os.path.join(ROOT, "pravidla", "svet", "kontroly.json"), encoding="utf-8"))["tabulky"]
HOTOVO = re.compile(r"opraven|hotovo|v kódu|v datech|v kodu", re.I)
OTEV = [s.lower() for s in KT["otevrene"]] + ["částečně", "castecne"]
HOT = [s.lower() for s in KT["hotove"]]
DUVOD = [s.lower() for s in KT["duvod"]]


def stav_bunky(c):
    """'otevreno' | 'hotovo' | None podle klicoveho slova na zacatku bunky (prvnich 40 znaku)."""
    z = re.sub(r"[*_`]", "", c).strip().lower()[:40]
    for k in OTEV:                              # neověřeno obsahuje ověřeno -> otevrene napred
        if k in z:
            return "otevreno", k
    for k in HOT:
        if k in z:
            return "hotovo", k
    return None, None


# --- zname testy: seznam v test_svet.gd, kontroly test_smyslu (chyba("druh"...)), funkce _jmeno v tools/test_*.gd
def zname_testy():
    t = set()
    sv = open(os.path.join(ROOT, "tools", "test_svet.gd"), encoding="utf-8").read()
    m = re.search(r'for t: String in \[(.*?)\]:', sv)
    if m:
        t |= set(re.findall(r'"(\w+)"', m.group(1)))
    for f in glob.glob(os.path.join(ROOT, "tools", "test_*.gd")) + glob.glob(os.path.join(ROOT, "tools", "test_*.py")):
        s = open(f, encoding="utf-8", errors="replace").read()
        t |= set(re.findall(r'^func _(\w+)\(', s, re.M))
        t |= set(re.findall(r'chyba\("(\w+)"', s))
    return t


def vysledky_logu():
    """jmeno -> (OK?, log) z posledniho logu (podle casu), ktery test obsahuje"""
    logy = []
    for g in KT["logy_testu"]:
        logy += glob.glob(g if g.startswith("/") else os.path.join(ROOT, g))
    out = {}
    for lg in sorted(set(logy), key=os.path.getmtime):
        try:
            for ln in open(lg, encoding="utf-8", errors="replace"):
                m = re.match(r"^TEST (\w+)\s+(OK|CHYBA)\b", ln)
                if m and m.group(1) != "SVET":
                    out[m.group(1)] = (m.group(2) == "OK", os.path.basename(lg))
        except OSError:
            pass
    return out


def nejnovejsi(soubory):
    def kdy(f):
        r = subprocess.run(["git", "-C", ROOT, "log", "--diff-filter=A", "--format=%ct", "-1", "--", os.path.relpath(f, ROOT)],
                           capture_output=True, text=True).stdout.strip()
        return int(r) if r else int(os.path.getmtime(f))   # jeste necommitnuta = nejnovejsi
    return max(soubory, key=kdy) if soubory else None


ZNAME = zname_testy()
LOGY = vysledky_logu()
soubory = sorted(glob.glob(os.path.join(ROOT, "docs", "rozpracovane", "*chyby*.md")))
NOVA = nejnovejsi(soubory)
chybi, chyby_nove, otevrene, bez_stavu, testy_vypis, nezarovnane = [], [], {}, {}, [], []
for f in soubory:
    jm = os.path.basename(f)
    nova = f == NOVA
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
        radek = "%s #%s %s" % (jm, b[0], (b[1] if len(b) > 1 else "")[:70])
        # stav: sloupec Stav (radek ma plny pocet bunek), jinak klicove slovo v kterekoli bunce od 3. (odzadu)
        stav, slovo, bst = None, None, ""
        if ist is not None and len(b) == len(hlav):
            stav, slovo = stav_bunky(b[ist])
            bst = b[ist]
        if stav is None:
            for c in reversed(b[2:]):
                stav, slovo = stav_bunky(c)
                if stav:
                    bst = c
                    break
        if stav is None:
            bez_stavu.setdefault(jm, []).append(radek)
            continue
        if stav == "otevreno":
            otevrene.setdefault(jm, []).append("%s [%s]" % (radek, bst[:60]))
            zbytek = bst.lower().split(slovo, 1)[-1]
            if nova and not (any(d in zbytek for d in DUVOD) or re.search(r"[(:–—]", zbytek) or len(zbytek.split()) >= 3):
                chyby_nove.append("OTEVRENO BEZ DUVODU " + radek)
            continue
        # brana jako drive: jen radky se sloupci Kontrola i Stav na svem miste (stare tabulky s posunutymi bunkami
        # vydani automaticky neblokuji - vypisou se jako NEZAROVNANE)
        if ik is not None and ist is not None and len(b) > max(ik, ist):
            kon = b[ik]
            if HOTOVO.search(b[ist]) and (kon == "" or "doplnit" in kon):
                chybi.append(radek)
        else:
            kon = " ".join(b[2:])
            nezarovnane.append(radek)
        # Puchart: test ve sloupci kontroly existuje a v poslednim behu prosel
        for t in set(re.findall(r"`_?(\w+)`", kon)):
            if t in ZNAME:
                r = LOGY.get(t)
                if r is None:
                    testy_vypis.append("NEBEZEL %s: %s" % (radek, t))
                elif not r[0]:
                    (chyby_nove if nova else testy_vypis).append("TEST NEPROSEL %s: %s (%s)" % (radek, t, r[1]))
        for t in re.findall(r"test(?:_svet)?\s+`_?(\w+)`", kon):
            if t not in ZNAME and not t.endswith((".py", ".gd", ".json")):
                (chyby_nove if nova else testy_vypis).append("TEST NEEXISTUJE %s: %s" % (radek, t))
vse = "--vse" in sys.argv
for jm, rr in otevrene.items():
    print("OTEVRENE %s: %d" % (jm, len(rr)))
    for r in rr[: None if vse else 15]:
        print("  " + r)
for jm, rr in bez_stavu.items():
    print("BEZ STAVU %s: %d" % (jm, len(rr)))
    for r in rr[: None if vse else 15]:
        print("  " + r)
for t in testy_vypis:
    print(t)
print("NEZAROVNANE (hotovy radek bez sloupce Kontrola/Stav na miste, kontrola se hleda v celem radku): %d" % len(nezarovnane))
for r in nezarovnane[: None if vse else 10]:
    print("  " + r)
for c in chybi:
    print("BEZ KONTROLY " + c)
for c in chyby_nove:
    print("CHYBA NEJNOVEJSI " + c)
print("tabulky chyb: %d opravenych radku bez kontroly; otevrenych %d, bez stavu %d (nejnovejsi %s: %d chyb)" % (
    len(chybi), sum(len(v) for v in otevrene.values()), sum(len(v) for v in bez_stavu.values()),
    os.path.basename(NOVA) if NOVA else "-", len(chyby_nove)))
sys.exit(1 if chybi or chyby_nove else 0)
