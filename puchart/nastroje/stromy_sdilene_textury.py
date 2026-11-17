"""Sdílené textury modelů (stromy, stavby): každá varianta (stromy mlady/stredni/stary, _lod1, _daleko; stavby a jejich
LOD1, domy_stredni, jabloně) nesla vlastní kopii stejné fotky (APK 0.1-ab: stromy 203 textur = 185 MB; 17. 11. stavby_h
123 skupin stejných textur ~198 MB ve VRAM scény, docs/rozpracovane/textury_vram_17_11.md T1). Obrázky se vyjmou z glb,
podle obsahu (hash) uloží jednou do <dir>/tex/<hash>.png|jpg a glb na ně odkazuje přes uri; <dir>/tex/puvod.json = hash →
modely (pro pravidla importu podle modelu, nastroje/import_velikost.py). Předměty pískoviště modely/predmety_h (Míša 17. 11.:
„uprav i pískoviště“ – stejné textury Havrana 43× a 126×). Godot je pak importuje jednou
a všechny modely sdílí jednu texturu (ResourceCache). Kopie, které Godot dřív z glb vytáhl vedle modelu (<model>_<obrázek>.*
se stejným obsahem), se smažou i s importy – jinak by zůstaly v balíku dat jako sirotci; soubor, jehož jméno se vyskytuje
ve scénách, datech nebo kódu hry (ikony, ručně odkazované textury), zůstane. Opakované spuštění nic nezmění.
python3 stromy_sdilene_textury.py <adresar_glb> [<koren hra>]"""
import sys, os, glob, hashlib, json
from pygltflib import GLTF2
d = os.path.abspath(sys.argv[1]); td = os.path.join(d, "tex"); os.makedirs(td, exist_ok=True)
H = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hra")
sha = lambda b: hashlib.sha1(b).hexdigest()[:16]
n_img = 0; uniq = set(); prevedene = {}   # jméno modelu -> hashe jeho obrázků
PJ = os.path.join(td, "puvod.json"); puvod = json.load(open(PJ)) if os.path.exists(PJ) else {}
for f in sorted(glob.glob(os.path.join(d, "*.glb"))):
    g = GLTF2().load(f); mj = os.path.splitext(os.path.basename(f))[0]
    for im in g.images or []:   # už převedené (uri tex/<hash>) – jen do původu
        if im.uri and im.uri.startswith("tex/"):
            h = os.path.splitext(im.uri[4:])[0]
            if mj not in puvod.setdefault(h, []): puvod[h].append(mj)
    if not g.images or all(im.uri for im in g.images):
        continue
    blob = g.binary_blob(); hs = set()
    for im in g.images:
        if im.bufferView is None: continue
        bv = g.bufferViews[im.bufferView]
        data = blob[(bv.byteOffset or 0):(bv.byteOffset or 0) + bv.byteLength]
        h = sha(data)
        ext = ".png" if im.mimeType == "image/png" else ".jpg"
        p = os.path.join(td, h + ext)
        if not os.path.exists(p):
            open(p, "wb").write(data)
        uniq.add(h); hs.add(h); n_img += 1
        if mj not in puvod.setdefault(h, []): puvod[h].append(mj)
        im.uri = "tex/" + h + ext; im.bufferView = None; im.mimeType = None
    g.save_binary(f)   # bufferView obrázků zůstane v blobu nevyužitý – velikost glb nevadí (do balíku jde importovaná .scn)
    prevedene[os.path.splitext(os.path.basename(f))[0]] = hs
json.dump(puvod, open(PJ, "w"), ensure_ascii=False, indent=0, sort_keys=True)
TXT = ""   # jména souborů, na která odkazuje hra (scény, data, kód) – ty se nemažou
for q in glob.glob(os.path.join(H, "**", "*"), recursive=True):
    if q.endswith((".tscn", ".tres", ".json", ".gd", ".cfg")) and "/.godot/" not in q and "/tex/" not in q:
        try: TXT += open(q, encoding="utf-8", errors="ignore").read()
        except OSError: pass
# sirotci: obrázky vytažené Godotem z vložených textur (<model>_<jméno>.png/jpg vedle glb) se stejným obsahem
smaz = 0
for p in sorted(glob.glob(os.path.join(d, "*.png")) + glob.glob(os.path.join(d, "*.jpg"))):
    b = os.path.basename(p); m = [s for s in prevedene if b.startswith(s + "_")]
    if not m or sha(open(p, "rb").read()) not in set().union(*(prevedene[s] for s in m)) or b in TXT: continue
    for q in (p, p + ".import"):
        if os.path.exists(q): os.remove(q); smaz += 1
    for q in glob.glob(os.path.join(H, ".godot", "imported", b + "-*")): os.remove(q)
print("modelů převedeno", len(prevedene), "obrázků", n_img, "jedinečných", len(uniq), "smazaných vytažených kopií", smaz)
