"""Herní data mimo APK (Havran tools/vydani.py, zjednodušeno): balík .pck z presetu Android (vše, co hra potřebuje),
rozdělený na části pod velikost_apk.data_mimo_apk.cast_mb do puchart/data/, popis hra/data_manifest.json (jde do APK).
Hra (scripts/data.gd) stáhne jen balík, jehož md5 ještě nemá.  python3 nastroje/data_balik.py <koren>"""
import sys, os, json, hashlib, subprocess, glob
K = os.path.abspath(sys.argv[1]); G = os.environ.get("GODOT", "/opt/godot47/Godot_v4.7.2-stable_linux.x86_64")
R = json.load(open(K + "/pravidla/svet/rozpocty.json"))["velikost_apk"]["data_mimo_apk"]
PART = int(R["cast_mb"]) * 1024 * 1024
os.makedirs(K + "/build/data", exist_ok=True); os.makedirs(K + "/data", exist_ok=True)
pck = K + "/build/data/puchart_data.pck"
# balík jen při změně zdrojů (Havran vydani.py): export .pck není bajtově stejný, tablet by stahoval znovu i beze změny
H = K + "/hra"; zh = hashlib.md5()
for kor in (".godot/imported", "modely", "dlazdice", "textury", "data"):
    for dp, dn, fn in os.walk(os.path.join(H, kor)):
        dn.sort()
        for f in sorted(fn):
            if f in ("mereni.json", "sestava.json", "data_manifest.json"): continue
            q = os.path.join(dp, f); zh.update(os.path.relpath(q, H).encode())
            with open(q, "rb") as fh:
                for blok in iter(lambda: fh.read(1 << 22), b""): zh.update(blok)
zdroj = zh.hexdigest()
try:
    stary = json.load(open(H + "/data_manifest.json"))
    if stary.get("zdroj") == zdroj and all(os.path.exists(K + "/data/" + c["file"]) for v in stary["packs"].values() for c in v["parts"]):
        print("datové balíky beze změny"); sys.exit(0)
except (OSError, ValueError, KeyError):
    pass
# měření jen v testovací APK (v balíku by ho spustila i procházková); sestava (čas) by měnila md5 balíku při každém
# vydání a tablet by stahoval 74 MB znovu – oba soubory jsou v APK, balík je nepotřebuje
odloz = [K + "/hra/data/mereni.json", K + "/hra/data/sestava.json"]
for f in odloz:
    if os.path.exists(f): os.replace(f, f.replace("/hra/data/", "/build/data/") + ".odlozeno")
try:
    subprocess.run([G, "--headless", "--path", K + "/hra", "--export-pack", "Android", pck], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
finally:
    for f in odloz:
        o = f.replace("/hra/data/", "/build/data/") + ".odlozeno"
        if os.path.exists(o): os.replace(o, f)
# --- rozdělení na balíky podle obsahu (Míša 12. 11.: „proč to stahuje znova 545 MB, když jsem to už jednou stáhnul“):
# jeden balík = každá malá změna (pár řádků JSON) změnila md5 celku → tablet stahoval vše. Teď skupiny (les, hrady, předměty,
# stavby, rostliny, terén, základ) – každá vlastní .pck s vlastním md5; nezměněná skupina má stejné bajty → stejné md5 →
# hra (scripts/data.gd) ji nestahuje. Formát .pck Godot 4.7 (verze 4): hlavička 112 B, data po 16 B, adresář na konci.
import struct
B = open(pck, "rb").read()
fb, do = struct.unpack("<QQ", B[24:40]); p = do
n, = struct.unpack("<I", B[p:p + 4]); p += 4
SOUB = []   # (cesta, bajty)
for _ in range(n):
    l, = struct.unpack("<I", B[p:p + 4]); p += 4; cesta = B[p:p + l].rstrip(b"\0").decode(); p += l
    off, sz = struct.unpack("<QQ", B[p:p + 16]); p += 36
    if cesta == "data_manifest.json": continue   # popis balíků je v APK; v balíku by měnil md5 základu při každém vydání
    SOUB.append((cesta, B[fb + off:fb + off + sz]))
SKUPINY = R.get("skupiny", [["les", ["modely/stromy/", "textury/impostory/"]], ["hrady", ["modely/hrady/"]],
                            ["predmety", ["modely/predmety_h/", "modely/predmety/"]], ["stavby", ["modely/stavby_h/"]],
                            ["rostliny", ["modely/"]], ["teren", ["dlazdice/", "textury/", "data/vysek", "data/dohled"]]])
def skupina(zdroj_):
    for jm, pref in SKUPINY:
        if any(zdroj_.startswith(x) for x in pref): return jm
    return "zaklad"
imp_sk = {}   # .godot/imported/x → skupina zdroje (podle path= v .import / .remap)
for cesta, data_ in SOUB:
    if cesta.endswith((".import", ".remap")):
        for radek in data_.decode("utf-8", "replace").splitlines():
            if radek.startswith("path") and "res://.godot/imported/" in radek:
                imp_sk[radek.split('"')[1][6:]] = skupina(cesta)
obsah = {}
for cesta, data_ in SOUB:
    sk = imp_sk.get(cesta) if cesta.startswith(".godot/imported/") else skupina(cesta)
    obsah.setdefault(sk or "zaklad", []).append((cesta, data_))
def pck_bajty(soubory):
    soubory = sorted(soubory)   # stálé pořadí = stálé md5
    hl = bytearray(b"GDPC") + struct.pack("<IIIII", 4, 4, 7, 2, 2)
    telo = bytearray(); adr = bytearray(struct.pack("<I", len(soubory)))
    for cesta, data_ in soubory:
        off = len(telo); telo += data_; telo += b"\0" * ((-len(telo)) % 16)
        pc = cesta.encode() + b"\0"; pc += b"\0" * ((-len(pc)) % 4)
        adr += struct.pack("<I", len(pc)) + pc + struct.pack("<QQ", off, len(data_)) + hashlib.md5(data_).digest() + struct.pack("<I", 0)
    hl += struct.pack("<QQ", 112, 112 + len(telo)) + b"\0" * 72
    return bytes(hl + telo + adr)
vetev = subprocess.run(["git", "-C", K, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
_arch = [v["data"] for v in json.load(open(K + "/pravidla/archiv_vydani.json"))["vydani"]] if os.path.exists(K + "/pravidla/archiv_vydani.json") else []
packs = {}; nove = []
for sk in ["zaklad"] + [s_[0] for s_ in SKUPINY]:
    if sk not in obsah: continue
    b = pck_bajty(obsah[sk]); md5 = hashlib.md5(b).hexdigest(); jm0 = "puchart_%s" % sk
    parts = []
    for i in range(0, len(b), PART):
        kus = b[i:i + PART]; jm = "%s-%s.pck.%03d" % (jm0, md5[:10], i // PART)
        if not os.path.exists(K + "/data/" + jm):   # 14. 11.: při plném disku zůstala napůl zapsaná část a další běh ji bral za hotovou
        open(K + "/data/" + jm + ".tmp", "wb").write(kus); os.replace(K + "/data/" + jm + ".tmp", K + "/data/" + jm); nove.append(jm)
        parts.append({"file": jm, "size": len(kus), "md5": hashlib.md5(kus).hexdigest()})
    packs[jm0] = {"md5": md5, "size": len(b), "parts": parts}
    print("  %-16s %7.1f MB  %s" % (jm0, len(b) / 1048576, md5[:10]))
platne = {c["file"] for v in packs.values() for c in v["parts"]}
for f in glob.glob(K + "/data/puchart_*.pck.*"):   # archivované vydání (pravidla/archiv_vydani.json) se nemaže
    if os.path.basename(f) not in platne and not any(a_ in f for a_ in _arch): os.remove(f)
json.dump({"popis": "herní data mimo APK po skupinách (nastroje/data_balik.py, scripts/data.gd) – stahují se jen změněné", "vetev": vetev, "zdroj": zdroj,
           "packs": packs}, open(K + "/hra/data_manifest.json", "w"), indent=1)
print("datové balíky: %d, celkem %.1f MB, nových částí %d" % (len(packs), sum(v["size"] for v in packs.values()) / 1048576, len(nove)))
