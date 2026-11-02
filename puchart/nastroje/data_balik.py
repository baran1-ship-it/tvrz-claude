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
    if stary.get("zdroj") == zdroj and all(os.path.exists(K + "/data/" + c["file"]) for c in stary["packs"]["puchart_data"]["parts"]):
        print("datový balík beze změny (%s)" % stary["packs"]["puchart_data"]["md5"][:10]); sys.exit(0)
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
b = open(pck, "rb").read(); md5 = hashlib.md5(b).hexdigest()
vetev = subprocess.run(["git", "-C", K, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
for f in glob.glob(K + "/data/puchart_data-*.pck.*"):
    if md5[:10] not in f: os.remove(f)
parts = []
for i in range(0, len(b), PART):
    kus = b[i:i + PART]; jm = "puchart_data-%s.pck.%03d" % (md5[:10], i // PART)
    open(K + "/data/" + jm, "wb").write(kus)
    parts.append({"file": jm, "size": len(kus), "md5": hashlib.md5(kus).hexdigest()})
json.dump({"popis": "herní data mimo APK (nastroje/data_balik.py, scripts/data.gd)", "vetev": vetev, "zdroj": zdroj,
           "packs": {"puchart_data": {"md5": md5, "size": len(b), "parts": parts}}}, open(K + "/hra/data_manifest.json", "w"), indent=1)
print("datový balík %.1f MB, %d částí, md5 %s" % (len(b) / 1048576, len(parts), md5[:10]))
