"""Obrázky načítací obrazovky z Wikimedia Commons (Míša 17. 11.): Bible Václava IV. a Velislavova bible, volné dílo.

  python3 nastroje/iluminace.py stahni ADRESAR      # stáhne soubory z hra/data/nacitani.json karty_plan (thumb ≤ 1920 px)
  python3 nastroje/iluminace.py vyrez ADRESAR       # výřez podle karty_plan[].vyrez [x0,y0,x1,y1] (0–1) → 1024 px JPEG

Stahuje se přes API Commons (imageinfo → URL náhledu standardní šířky 1920/1280/960 na upload.wikimedia.org) s obecným
User-Agentem bez osobních údajů a s ohledem na Retry-After (17. 11. vracel upload.wikimedia.org z kontejneru trvale 429).
ADRESAR = vlastní nová složka mimo repo (stažená data se nespouštějí). Výsledek: hra/obrazky/nacitani/<id>.jpg; autory
(soubor, zdroj, licence) doplní do nacitani.json obrazky[]. Karty (obrázek ↔ pořekadlo) se přepínají v nacitani.json ručně
až po kontrole obsahu okem.
"""
import hashlib, json, os, sys, time, urllib.error, urllib.parse, urllib.request

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = K + "/hra/data/nacitani.json"
UA = "PuchartAssetTool/1.0 (generic research script)"
API = "https://commons.wikimedia.org/w/api.php"


def get(url, pokusu=6):
    for _ in range(pokusu):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()
        except urllib.error.HTTPError as e:
            print("  HTTP", e.code, url[-80:], flush=True)
            if e.code != 429:
                return None
            time.sleep(int(e.headers.get("Retry-After") or 600) + 10)
    return None


def info(title):
    q = urllib.parse.urlencode({"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "format": "json"})
    d = json.loads(get(API + "?" + q))
    return next(iter(d["query"]["pages"].values()))["imageinfo"][0]


def stahni(out):
    os.makedirs(out, exist_ok=True)
    for k in json.load(open(DATA))["karty_plan"]:
        fn = os.path.join(out, k["id"] + ".jpg")
        if os.path.exists(fn):
            continue
        ii = info(k["commons"]); time.sleep(2)
        u = ii["url"].split("?")[0]; base, name = u.rsplit("/", 1)
        tb = base.replace("/commons/", "/commons/thumb/") + "/" + name
        w = ii["width"]
        urls = ["%s/%dpx-%s" % (tb, s, name) for s in (1920, 1280, 960) if s < w][:1] + [u]
        for url in urls:
            b = get(url); time.sleep(30)
            if b:
                open(fn, "wb").write(b)
                json.dump({"commons": k["commons"], "puvod": ii["descriptionurl"], "licence": ii["extmetadata"].get("LicenseShortName", {}).get("value", ""),
                           "sha1_url": hashlib.sha1(url.encode()).hexdigest()}, open(fn + ".json", "w"), ensure_ascii=False)
                print("OK", k["id"], len(b), flush=True)
                break
        else:
            print("CHYBA", k["id"], flush=True)


def vyrez(src):
    from PIL import Image
    d = json.load(open(DATA)); znam = {o["soubor"] for o in d.get("obrazky", [])}
    for k in d["karty_plan"]:
        fn = os.path.join(src, k["id"] + ".jpg")
        if not os.path.exists(fn) or not k.get("vyrez"):
            continue
        im = Image.open(fn).convert("RGB"); W, H = im.size; x0, y0, x1, y1 = k["vyrez"]
        im = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        im.thumbnail((1024, 1024), Image.LANCZOS)
        im.save(K + "/hra/" + k["obrazek"][6:], quality=88)
        m = json.load(open(fn + ".json"))
        if k["obrazek"] not in znam:
            d.setdefault("obrazky", []).append({"soubor": k["obrazek"], "popis": "Načítací obrazovka – " + k["obsah"],
                "dilo": d["popisky_zdroje"][k["zdroj"]].split(": ", 1)[1], "commons": m["commons"], "puvod": m["puvod"], "licence": m["licence"]})
        print("VYREZ", k["id"], im.size)
    json.dump(d, open(DATA, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    {"stahni": stahni, "vyrez": vyrez}[sys.argv[1]](sys.argv[2])
