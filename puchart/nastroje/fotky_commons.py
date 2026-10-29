"""Referenční fotky místa z Wikimedia Commons (KCD postup: skutečné místo → historická úprava).

Prochází kategorie (rekurzivně do hloubky 2) a geosearch kolem hradu; ukládá náhledy 1280 px do build/reference/commons
a seznam s autorem a licencí do build/reference/commons.json. Fotky NEJSOU v gitu (autorská práva) – do repa jde
jen seznam (docs/reference_mista.md) a rozbor.
python3 fotky_commons.py <vystup_dir> <kategorie...>
"""
import sys, json, os, time, urllib.parse, urllib.request

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "PuchartHra/1.0 (baran1@seznam.cz; reference photos for a historical game)"}
API = "https://commons.wikimedia.org/w/api.php?"

def api(**p):
    p["format"] = "json"
    for pokus in range(6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API + urllib.parse.urlencode(p), headers=UA), timeout=40)
            d = json.loads(r.read())
            if "error" in d and "busy" in d["error"].get("code", ""):
                raise RuntimeError("busy")
            time.sleep(2.0); return d
        except Exception as e:
            time.sleep(15 * (pokus + 1))
    return {}

soubory = {}
def kategorie(k, hloubka):
    cont = {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle="Category:" + k, cmtype="file|subcat", cmlimit=500, **cont)
        for m in d.get("query", {}).get("categorymembers", []):
            if m["ns"] == 6: soubory.setdefault(m["title"], k)
            elif m["ns"] == 14 and hloubka > 0: kategorie(m["title"][9:], hloubka - 1)
        if "continue" not in d: break
        cont = {"cmcontinue": d["continue"]["cmcontinue"]}

for k in sys.argv[2:]:
    kategorie(k, 2)
    print(k, len(soubory), flush=True)
d = api(action="query", list="geosearch", gscoord="49.6115|17.6825", gsradius=10000, gslimit=500, gsnamespace=6)
for g in d.get("query", {}).get("geosearch", []):
    soubory.setdefault(g["title"], "geo %d m" % g["dist"])
print("celkem", len(soubory), flush=True)
info = []
tit = list(soubory)
for i in range(0, len(tit), 40):
    d = api(action="query", titles="|".join(tit[i:i + 40]), prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=1280)
    for p in d.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii.get("thumburl") or not p["title"].lower().endswith((".jpg", ".jpeg", ".png")): continue
        em = ii.get("extmetadata", {})
        g = lambda k: em.get(k, {}).get("value", "")
        info.append({"titul": p["title"], "kategorie": soubory[p["title"]], "url": ii.get("descriptionurl"), "nahled": ii["thumburl"],
                     "autor": g("Artist")[:200], "licence": g("LicenseShortName"), "datum": g("DateTimeOriginal")[:30],
                     "popis": g("ImageDescription")[:300]})
for j, f in enumerate(info):
    cil = os.path.join(out, "%03d_" % j + f["titul"][5:].replace("/", "_")[:80])
    f["soubor"] = cil
    if not os.path.exists(cil):
        try:
            urllib.request.urlretrieve if False else None
            r = urllib.request.urlopen(urllib.request.Request(f["nahled"], headers=UA), timeout=60)
            open(cil, "wb").write(r.read()); time.sleep(1.5)
        except Exception as e:
            f["chyba"] = str(e)
json.dump(info, open(os.path.join(out, "commons.json"), "w"), ensure_ascii=False, indent=1)
print("staženo", sum(1 for f in info if "chyba" not in f))
