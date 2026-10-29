"""Referenční fotky z webů o výletech (turistika.cz, natreku, vyraznavylet, blogy, ok-tourism, atlas…).

Jen reference pro modely a materiály (postup KCD) – fotky jsou autorská díla, do gitu NEJDOU (build/), v repu je jen
seznam stránek a rozbor (docs/reference_mista.md). Stáhne obrázky > 40 kB z <img>, srcset, og:image a odkazů na .jpg.
python3 fotky_web.py <vystup_dir> <soubor_se_strankami>
"""
import sys, os, re, json, time, hashlib, urllib.request, urllib.parse, html

out, seznam = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) PuchartReference/1.0 (baran1@seznam.cz)"}
def get(u, t=40):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
info = json.load(open(os.path.join(out, "web.json"))) if os.path.exists(os.path.join(out, "web.json")) else []
mam = {i["url_obrazku"] for i in info}
for stranka in [l.strip() for l in open(seznam) if l.strip() and not l.startswith("#")]:
    try:
        h = get(stranka).decode("utf-8", "ignore")
    except Exception as e:
        print("CHYBA", stranka, e); continue
    kand = set()
    for m in re.finditer(r'(?:src|data-src|data-lazy-src|href|content)=["\']([^"\']+\.(?:jpe?g|webp|png)(?:\?[^"\']*)?)["\']', h, re.I):
        kand.add(m.group(1))
    for m in re.finditer(r'srcset=["\']([^"\']+)["\']', h, re.I):
        c = [x.strip().split(" ")[0] for x in m.group(1).split(",") if x.strip()]
        if c: kand.add(c[-1])
    dom = urllib.parse.urlparse(stranka).netloc
    n = 0
    for k in kand:
        u = urllib.parse.urljoin(stranka, html.unescape(k))
        if any(s in u.lower() for s in ("logo", "icon", "avatar", "banner", "sprite", "favicon", "button", "flag")): continue
        if u in mam: continue
        try:
            b = get(u, 30)
        except Exception:
            continue
        if len(b) < 40000: continue
        jm = dom.replace(".", "_") + "_" + hashlib.md5(u.encode()).hexdigest()[:10] + os.path.splitext(urllib.parse.urlparse(u).path)[1][:5]
        open(os.path.join(out, jm), "wb").write(b)
        info.append({"stranka": stranka, "url_obrazku": u, "soubor": jm, "kb": len(b) // 1024}); mam.add(u); n += 1
        time.sleep(0.3)
    print(stranka, "obrázků", n, flush=True)
    json.dump(info, open(os.path.join(out, "web.json"), "w"), ensure_ascii=False, indent=1)
print("celkem", len(info))
