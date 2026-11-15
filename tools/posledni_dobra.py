"""Posledni dobra verze (Puchart nastroje/posledni_dobra.py, docs/rozpracovane/hlidaci_z_pucharta.md #4; CLAUDE.md „Regrese“):
vysledky hlidacu (radky TEST <jmeno> OK/CHYBA z logu test_svet, SMYSL souhrn test_smyslu, GEOMETRIE/ROHATKA) se pri pruchodu
ulozi s commitem a verzi do pravidla/dobra_verze.json (kontroly.json dobra_verze.soubor). Pri nepruchodu vypise, co bylo
v dobre verzi OK a ted neni, a prikaz git diff od dobre verze k izolaci pricinu (CLAUDE.md: posledni dobra -> prvni spatna
-> rozdil commitu -> hypotezy -> izolovany test).

  python3 tools/posledni_dobra.py porovnej <log...>     regrese proti dobre verzi (rc 1 = regrese)
  python3 tools/posledni_dobra.py zapis <log...>        ulozit jako dobrou (jen kdyz v logech nic neselhalo; rc 1 jinak)
  python3 tools/posledni_dobra.py <rc> <log...>         jako Puchart: rc 0 = zapis, jinak porovnej

Log: build/beh/<jmeno>_godot.log nebo vystup rychle_testy.sh / test_smyslu.py / kontrola_geometrie.py (cokoli s radky
TEST <jmeno> OK|CHYBA, SMYSL souhrn ..., GEOMETRIE souhrn ...). Zapis nepise nic jineho nez dobra_verze.json."""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KC = json.load(open(os.path.join(ROOT, "pravidla", "svet", "kontroly.json"), encoding="utf-8"))["dobra_verze"]
SOUBOR = os.path.join(ROOT, KC["soubor"])
RE_TEST = re.compile(r"^TEST (\S+)\s+(OK|CHYBA)\b")


def vysledky(logy):
    out = {}
    for lg in logy:
        try:
            t = open(lg, encoding="utf-8", errors="replace").read()
        except OSError:
            print("DOBRA_VERZE log %s chybi" % lg)
            continue
        for ln in t.splitlines():
            m = RE_TEST.match(ln)
            if m and m.group(1) not in ("SVET",):
                out["test:" + m.group(1)] = m.group(2) == "OK"
            elif ln.startswith("SMYSL souhrn"):
                out["smysl"] = ln.strip().endswith("OK")
            elif ln.startswith("GEOMETRIE souhrn"):
                out["geometrie"] = " novych 0," in ln
            elif ln.startswith("tabulky chyb:"):
                out["tabulky"] = ": 0 " in ln
    return out


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, text=True).stdout.strip()


def verze():
    m = re.search(r'config/version="([0-9.]+)', open(os.path.join(ROOT, "project.godot"), encoding="utf-8").read())
    return m.group(1) if m else ""


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    co = sys.argv[1]
    if co.lstrip("-").isdigit():
        co = "zapis" if int(co) == 0 else "porovnej"
    ted = vysledky(sys.argv[2:])
    if not ted:
        sys.exit("DOBRA_VERZE v logech zadny vysledek")
    if co == "zapis":
        spatne = sorted(k for k, ok in ted.items() if not ok)
        if spatne:
            print("DOBRA_VERZE neulozena - neproslo: %s" % spatne)
            sys.exit(1)
        stare = json.load(open(SOUBOR, encoding="utf-8")) if os.path.exists(SOUBOR) else {}
        vys = dict(stare.get("vysledky", {}))
        vys.update(ted)                  # testy, ktere tento beh nepoustel, zustavaji z posledni dobre
        json.dump({"popis": "vysledky hlidacu posledni dobre verze (tools/posledni_dobra.py)", "commit": git("rev-parse", "--short", "HEAD"),
                   "verze": verze(), "vysledky": vys}, open(SOUBOR, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("DOBRA_VERZE ulozena %s (%s), vysledku %d" % (verze(), git("rev-parse", "--short", "HEAD"), len(vys)))
        return
    if not os.path.exists(SOUBOR):
        print("DOBRA_VERZE zadna ulozena - porovnani neni s cim (%s)" % KC["soubor"])
        sys.exit(1 if any(not ok for ok in ted.values()) else 0)
    d = json.load(open(SOUBOR, encoding="utf-8"))
    reg = sorted(k for k, ok in d["vysledky"].items() if ok and k in ted and not ted[k])
    nove = sorted(k for k, ok in ted.items() if not ok and k not in d["vysledky"])
    print("DOBRA_VERZE dobra %s (%s), ted %s (%s)" % (d.get("verze"), d["commit"], verze(), git("rev-parse", "--short", "HEAD")))
    if reg:
        print("REGRESE proti dobre verzi: %s" % reg)
    if nove:
        print("SELHANI bez predchoziho vysledku (novy test): %s" % nove)
    if reg or nove:
        print("  k izolaci: git log --oneline %s..HEAD ; git diff --stat %s -- scripts pravidla blender tools" % (d["commit"], d["commit"]))
        st = git("diff", "--stat", d["commit"], "--", "scripts", "pravidla", "blender", "tools")
        print("\n".join("  " + r for r in st.splitlines()[-25:]))
        sys.exit(1)
    print("DOBRA_VERZE bez regrese (%d vysledku)" % len(ted))


if __name__ == "__main__":
    main()
