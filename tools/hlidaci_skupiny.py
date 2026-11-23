#!/usr/bin/env python3
"""Skupiny testů hry podle otisku vstupů (plán 18. 11. E2, podle Pucharta nastroje/hlidaci_skupiny.py; Míša 23. 11.: „ať testy
nejdou hodiny“). Pravidla pravidla/hlidaci_skupiny.json, otisky + výsledky posledního úspěšného běhu build/hlidaci_otisky.json.
Pouští tools/beh.sh <jm> skupiny ["<snímky>"]; ručně:
  plan <jm> [skupina,skupina|vse]  → build/hlidaci_skupiny/<jm>/_plan.json a _testy.txt (testy ke spuštění, čárkami);
                                      převzaté skupiny (nezměněný otisk + poslední výsledek OK) vypíše a nepouští
  zapis <jm> <log Godotu> [--konec] → skupina, jejíž testy všechny doběhly (řádky HOTOVO_TEST), se zapíše HNED: OK = otisk
                                      uložit (restart kontejneru = další běh ji převezme), CHYBA = otisk smazat. --konec: testy
                                      bez výsledku = CHYBA (proces nedoběhl). rc 1, když některá skupina selhala.
  stav                              → přehled skupin: otisk sedí / změněn, poslední OK
HLIDACI_VSE=1 vynutí spuštění všech skupin. Testy z „nevydavat_neblokuje“ běží a vypisují se, skupinu neblokují (E6)."""
import sys, os, re, json, glob, hashlib, fcntl, time, subprocess, contextlib

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(K, "pravidla/hlidaci_skupiny.json")))
OT = os.path.join(K, "build/hlidaci_otisky.json")
KES = os.path.join(K, "build/hlidaci_md5.json")
SADY = ["tools/test_svet.gd", "tools/test_stavby.gd", "tools/test_voda.gd", "tools/test_vykon.gd"]
NEBLOKUJE = set(P.get("nevydavat_neblokuje", []))
_md5 = {}
try: _kes = json.load(open(KES))   # cesta → [velikost, mtime_ns, md5] - velké soubory se nečtou pokaždé
except Exception: _kes = {}


def md5(cesta):
    if cesta not in _md5:
        st = os.stat(os.path.join(K, cesta)); kl = [st.st_size, st.st_mtime_ns]
        if cesta in _kes and _kes[cesta][:2] == kl:
            _md5[cesta] = _kes[cesta][2]; return _md5[cesta]
        h = hashlib.md5()
        with open(os.path.join(K, cesta), "rb") as f:
            for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
        _md5[cesta] = h.hexdigest(); _kes[cesta] = kl + [_md5[cesta]]
    return _md5[cesta]


def soubory(vzory):
    out = set()
    for v in vzory:
        for c in glob.glob(os.path.join(K, v), recursive=True):
            r = os.path.relpath(c, K)
            if os.path.isfile(c) and any(r.endswith(p) for p in P["pripony"]): out.add(r)
    return sorted(out)


def sady():
    """test → (soubor sady, tělo funkce _test) a pomocný kód sad (vše mimo testovací funkce = společný vstup)"""
    testy, pomocne = {}, ""
    for f in SADY:
        tx = open(os.path.join(K, f), encoding="utf-8").read()
        m = re.search(r'for t: String in \[([^\]]*)\]', tx) or re.search(r'const TESTY := \[([^\]]*)\]', tx)
        jm = re.findall(r'"([a-z0-9_]+)"', m.group(1)) if m else []
        funkce = re.split(r'\n(?=func )', tx)
        zbyva = []
        tela = {}
        for kus in funkce:
            mm = re.match(r'func _([a-z0-9_]+)\(', kus)
            if mm and mm.group(1) in jm: tela[mm.group(1)] = kus
            else: zbyva.append(kus)
        # seznam testů v run() je v pomocném kódu; doplnění nového testu do seznamu nesmí zneplatnit všechny skupiny
        pomocne += re.sub(r'for t: String in \[[^\]]*\]|const TESTY := \[[^\]]*\]', '', "\n".join(zbyva))
        for t in jm: testy[t] = (f, tela.get(t, ""))
    return testy, hashlib.md5(pomocne.encode()).hexdigest()


def rozdel(testy):
    sk = P["skupiny"]; zb = next(s for s, v in sk.items() if v.get("zbytek"))
    roz = {s: [t for t in v["testy"] if t in testy] for s, v in sk.items()}
    zarazene = {t for v in roz.values() for t in v}
    roz[zb] += [t for t in testy if t not in zarazene]
    return roz


def vypocet():
    testy, pom = sady()
    roz = rozdel(testy)
    sp = soubory(P["spolecne"])
    o = {}
    for s, v in P["skupiny"].items():
        h = hashlib.md5((pom + json.dumps(roz[s])).encode())
        for c in sorted(set(sp) | set(soubory(v["vstupy"]))): h.update((c + md5(c)).encode())
        for t in roz[s]: h.update(testy[t][1].encode())
        o[s] = h.hexdigest()
    return roz, o


@contextlib.contextmanager
def otisky():
    """zámek – běhy zapisují souběžně"""
    os.makedirs(os.path.dirname(OT), exist_ok=True)
    with open(OT + ".lock", "w") as z:
        fcntl.flock(z, fcntl.LOCK_EX)
        try: d = json.load(open(OT))
        except Exception: d = {}
        yield d
        json.dump(d, open(OT + ".tmp", "w"), ensure_ascii=False, indent=1); os.replace(OT + ".tmp", OT)


def commit():
    try: return subprocess.run(["git", "-C", K, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception: return "?"


def adresar(jm):
    d = os.path.join(K, "build/hlidaci_skupiny", jm); os.makedirs(d, exist_ok=True); return d


def vysledky_logu(log):
    v = {}
    try:
        for ln in open(log, errors="replace"):
            if ln.startswith("HOTOVO_TEST "):
                c = ln.split()
                if len(c) >= 3: v[c[1]] = c[2]
    except FileNotFoundError: pass
    return v


cmd = sys.argv[1] if len(sys.argv) > 1 else "stav"
if cmd == "plan":
    jm = sys.argv[2]; vyber = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] not in ("", "vse") else ""
    vse = os.environ.get("HLIDACI_VSE") == "1"
    roz, o = vypocet(); D = adresar(jm)
    for f in glob.glob(D + "/*"): os.remove(f)
    with otisky() as d: pr = dict(d.get("skupiny", {}))
    chtene = [s for s in P["skupiny"] if not vyber or s in vyber.split(",")]
    nezname = [s for s in vyber.split(",") if s and s not in P["skupiny"]]
    if nezname: sys.exit("HLIDACI CHYBA: neznámé skupiny %s (pravidla/hlidaci_skupiny.json)" % nezname)
    spustit, prevzate = [], []
    for s in chtene:
        z = pr.get(s)
        if not roz[s]: continue
        if not vse and z and z.get("otisk") == o[s]:
            prevzate.append(s)
            print("SKUPINA %-9s převzato z běhu %s (commit %s, %d testů, %d s)" % (s, z.get("cas", "?"), z.get("commit", "?"), len(roz[s]), z.get("trvani_s", 0)))
            continue
        spustit.append(s)
        print("SKUPINA %-9s spustit: %d testů (%s)" % (s, len(roz[s]), "HLIDACI_VSE" if vse else "otisk změněn" if z else "bez úspěšného běhu"))
    testy = [t for s in spustit for t in roz[s]]
    json.dump({"otisky": o, "testy": roz, "spustit": spustit, "prevzate": prevzate, "zapsano": {}, "t0": time.time()},
              open(D + "/_plan.json", "w"), ensure_ascii=False)
    open(D + "/_testy.txt", "w").write(",".join(testy))
    json.dump(_kes, open(KES + ".tmp", "w")); os.replace(KES + ".tmp", KES)
    print("SKUPINY spustit %d (%d testů), převzato %d" % (len(spustit), len(testy), len(prevzate)))
elif cmd == "zapis":
    jm, log = sys.argv[2], sys.argv[3]; konec = "--konec" in sys.argv
    D = adresar(jm); pl = json.load(open(D + "/_plan.json"))
    v = vysledky_logu(log); rc = 0
    for s in pl["spustit"]:
        if s in pl["zapsano"]:
            rc |= pl["zapsano"][s] != "OK"; continue
        tt = pl["testy"][s]
        if not konec and not all(t in v for t in tt): continue
        vys = {t: v.get(t, "CHYBA_BEZ_VYSLEDKU") for t in tt}
        spatne = [t for t, x in vys.items() if x != "OK" and t not in NEBLOKUJE]
        neblok = [t for t, x in vys.items() if x != "OK" and t in NEBLOKUJE]
        ok = not spatne
        trv = int(time.time() - pl["t0"])
        with otisky() as d:
            sk = d.setdefault("skupiny", {})
            if ok: sk[s] = {"otisk": pl["otisky"][s], "cas": time.strftime("%d. %m. %H:%M"), "commit": commit(), "trvani_s": trv, "vysledek": vys}
            else: sk.pop(s, None)
        pl["zapsano"][s] = "OK" if ok else "CHYBA"; rc |= not ok
        print("SKUPINA %-9s %s (%d testů%s%s%s)" % (s, "OK" if ok else "CHYBA", len(tt), ", otisk uložen" if ok else "",
              ", chybné %s" % spatne if spatne else "", ", CHYBA_NEBLOKUJE %s" % neblok if neblok else ""))
    json.dump(pl, open(D + "/_plan.json.tmp", "w"), ensure_ascii=False); os.replace(D + "/_plan.json.tmp", D + "/_plan.json")
    if konec:
        print("HLIDACI %s: spuštěno %d skupin, převzato %d" % ("CHYBA" if rc else "OK", len(pl["spustit"]), len(pl["prevzate"])))
    sys.exit(1 if rc else 0)
elif cmd == "stav":
    roz, o = vypocet()
    try: pr = json.load(open(OT)).get("skupiny", {})
    except Exception: pr = {}
    for s in P["skupiny"]:
        z = pr.get(s)
        print("SKUPINA %-9s %3d testů  %s" % (s, len(roz[s]), ("převezme se (OK %s, commit %s)" % (z["cas"], z["commit"])) if z and z.get("otisk") == o[s]
              else "poběží (otisk změněn)" if z else "poběží (bez úspěšného běhu)"))
    json.dump(_kes, open(KES + ".tmp", "w")); os.replace(KES + ".tmp", KES)
else:
    sys.exit(__doc__)
