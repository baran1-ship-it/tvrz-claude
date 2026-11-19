"""Skupiny tras testu průchodu a jejich otisky (Míša 19. 11.: „když upravujeme jen hrad, tak není třeba procházet celý svět“).
Pravidla pravidla/svet/hlidaci_skupiny.json, otisky + výsledky posledního úspěšného běhu build/hlidaci_otisky.json.
  plan <K>                 → build/pruchod_skupiny/_plan.tsv (skupina, PUCHART_TRASA, PUCHART_JEN) pro skupiny ke spuštění;
                             převzaté skupiny zapíše rovnou do build/pruchod_skupiny/<s>.json („převzato z běhu …“)
  zapis <K> <s> <json>     → výsledek skupiny; úplný a OK = uložit otisk hned (odolnost proti restartu), jinak otisk smazat
  sluc <K>                 → build/pruchod.json ze všech skupin
  otisk_souboru <K> <cesty…> → md5 souborů (geometrie)
HLIDACI_VSE=1 vynutí spuštění všech skupin."""
import sys, os, json, glob, hashlib, fcntl, time, subprocess, contextlib

K = sys.argv[2]
P = json.load(open(os.path.join(K, "pravidla/svet/hlidaci_skupiny.json")))
OT = os.path.join(K, "build/hlidaci_otisky.json")
D = os.path.join(K, "build/pruchod_skupiny")
_md5 = {}


try: _kes = json.load(open(os.path.join(K, "build/hlidaci_md5.json")))   # (velikost, mtime) → md5, ať se 1,7 GB modelů nečte pokaždé
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


def soubory(vzory, vynechat=()):
    out = set()
    for v in vzory:
        for c in glob.glob(os.path.join(K, v), recursive=True):
            r = os.path.relpath(c, K)
            if os.path.isfile(c) and r not in vynechat and any(r.endswith(p) for p in P["pripony"]): out.add(r)
    return sorted(out)


def otisk(cesty, navic=""):
    h = hashlib.md5(navic.encode())
    for c in cesty: h.update((c + md5(c)).encode())
    return h.hexdigest()


@contextlib.contextmanager
def otisky():
    """zámek – skupiny zapisují souběžně"""
    os.makedirs(os.path.dirname(OT), exist_ok=True)
    with open(OT + ".lock", "w") as z:
        fcntl.flock(z, fcntl.LOCK_EX)
        try: d = json.load(open(OT))
        except Exception: d = {}
        yield d
        json.dump(d, open(OT + ".tmp", "w"), ensure_ascii=False, indent=1); os.replace(OT + ".tmp", OT)


def trasy():
    t = {}
    for f in sorted(glob.glob(os.path.join(K, "hra/data/pruchody*.json"))): t.update(json.load(open(f))["trasy"])
    return t


def rozdel():
    """trasa → skupina podle předpon; co nikam nepatří, jde do skupiny se „zbytek“"""
    T = trasy(); sk = P["skupiny"]; zb = next(s for s, v in sk.items() if v.get("zbytek"))
    roz = {s: [] for s in sk}
    for jm in T:
        s = next((s for s, v in sk.items() if any(jm == p or jm.startswith(p) for p in v["trasy"])), zb)
        roz[s].append(jm)
    return T, roz


def vypocet():
    T, roz = rozdel()
    sp = soubory(P["spolecne"], set(P.get("vynechat_spolecne", [])))
    o = {}
    for s, v in P["skupiny"].items():
        defin = json.dumps({"trasy": {j: T[j] for j in roz[s]}, "testy": v["testy"]}, sort_keys=True)
        o[s] = otisk(sp + soubory(v["vstupy"]), defin)
    return roz, o


def commit():
    try: return subprocess.run(["git", "-C", K, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception: return "?"


cmd = sys.argv[1]
if cmd == "plan":
    roz, o = vypocet(); vse = os.environ.get("HLIDACI_VSE") == "1"
    os.makedirs(D, exist_ok=True)
    for f in glob.glob(D + "/*"): os.remove(f)
    with otisky() as d: pr = dict(d.get("pruchod", {}))
    json.dump({"otisky": o, "trasy": roz}, open(D + "/_plan.json", "w"))
    radky = []
    trv = {s: z.get("trvani_s", 0) for s, z in pr.items()}
    for s, v in sorted(P["skupiny"].items(), key=lambda i: -(trv.get(i[0]) or len(roz[i[0]]) + 5 * len(i[1]["testy"]))):
        z = pr.get(s)
        if not vse and z and z.get("otisk") == o[s]:
            json.dump(z["vysledek"], open("%s/%s.json" % (D, s), "w"), ensure_ascii=False)
            print("PRUCHOD_SKUPINA %s převzato z běhu %s (commit %s, %d výsledků)" % (s, z.get("cas", "?"), z.get("commit", "?"), len(z["vysledek"])))
            continue
        jen = ",".join(P["testy_jen"][t] for t in v["testy"]) or "-"   # „-“ = žádný pevný test (PUCHART_JEN neprázdné → jen trasy)
        radky.append("%s\t%s\t%s" % (s, ",".join(roz[s]), jen))
        print("PRUCHOD_SKUPINA %s spustit: %d tras, testy %s (%s)" % (s, len(roz[s]), v["testy"], "HLIDACI_VSE" if vse else "otisk změněn" if z else "bez úspěšného běhu"))
    json.dump(_kes, open(os.path.join(K, "build/hlidaci_md5.json"), "w"))
    open(D + "/_plan.tsv", "w").write("".join(r + "\n" for r in radky))
elif cmd == "zapis":
    s, f = sys.argv[3], sys.argv[4]; t = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    pl = json.load(open(D + "/_plan.json"))
    try: v = json.load(open(f))
    except Exception: v = {}
    ocek = set(pl["trasy"][s]) | set(P["skupiny"][s]["testy"])
    for k in ocek - set(v): v[k] = "CHYBA: bez výsledku (proces skupiny %s nedoběhl)" % s
    json.dump(v, open("%s/%s.json" % (D, s), "w"), ensure_ascii=False)
    ok = all(x == "OK" for x in v.values())
    with otisky() as d:
        pr = d.setdefault("pruchod", {})
        if ok: pr[s] = {"otisk": pl["otisky"][s], "cas": time.strftime("%d. %m. %H:%M"), "commit": commit(), "trvani_s": t, "vysledek": v}
        else: pr.pop(s, None)
    print("PRUCHOD_SKUPINA %s %s (%d výsledků, %d s%s)" % (s, "OK" if ok else "CHYBA", len(v), t, ", otisk uložen" if ok else ""))
elif cmd == "sluc":
    v = {}
    for s in P["skupiny"]:
        try: v.update(json.load(open("%s/%s.json" % (D, s))))
        except Exception: print("PRUCHOD_SKUPINA %s CHYBA: bez výsledku" % s)
    json.dump(v, open(os.path.join(K, "build/pruchod.json"), "w"), ensure_ascii=False, indent=1)
elif cmd == "otisk_souboru":
    print(otisk(sys.argv[3:]))
