"""Sdílené textury stromů: každá varianta (mlady/stredni/stary, _lod1, _daleko) nesla vlastní kopii stejné fotky
(APK 0.1-ab: 203 textur = 185 MB). Obrázky se vyjmou z glb, podle obsahu (hash) uloží jednou do <dir>/tex/<hash>.png
a glb na ně odkazuje přes uri. Godot je pak importuje jednou.
python3 stromy_sdilene_textury.py <adresar_glb>"""
import sys, os, glob, hashlib
from pygltflib import GLTF2
d = sys.argv[1]; td = os.path.join(d, "tex"); os.makedirs(td, exist_ok=True)
n_img = 0; uniq = set()
for f in sorted(glob.glob(os.path.join(d, "*.glb"))):
    g = GLTF2().load(f)
    if not g.images or all(im.uri for im in g.images):
        continue
    blob = g.binary_blob()
    for im in g.images:
        if im.bufferView is None: continue
        bv = g.bufferViews[im.bufferView]
        data = blob[(bv.byteOffset or 0):(bv.byteOffset or 0) + bv.byteLength]
        h = hashlib.sha1(data).hexdigest()[:16]
        ext = ".png" if im.mimeType == "image/png" else ".jpg"
        p = os.path.join(td, h + ext)
        if not os.path.exists(p):
            open(p, "wb").write(data)
        uniq.add(h); n_img += 1
        im.uri = "tex/" + h + ext; im.bufferView = None; im.mimeType = None
    g.save_binary(f)   # bufferView obrázků zůstane v blobu nevyužitý – velikost glb nevadí (do APK jde .scn)
print("obrázků", n_img, "jedinečných", len(uniq))
