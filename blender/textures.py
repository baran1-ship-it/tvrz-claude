"""Stazeni fotografickych PBR textur z Poly Haven (CC0) do blender/tex_cache.

Pouziti:  python blender/textures.py [2k|1k]
Kazda textura: barva (diff), normala (nor_gl), drsnost (rough), vyska (disp) a skutecny rozmer v metrech.
"""
import json
import os
import sys
import urllib.request

ASSETS = {
    # nazev v tvrzi: id na Poly Haven
    "zdivo": "castle_wall_slates",
    "omitka_kremova": "beige_wall_002",
    "omitka_bila": "medieval_wall_01",
    "tram": "rough_wood",
    "prkna_ven": "weathered_planks",
    "podlaha": "old_wood_floor",
    "okenice": "wood_shutter",
    "dlazba": "stone_floor",
    "dlazba_hrad": "monastery_stone_floor",
    "kocicky": "rock_embedded_floor",
    "piskovec": "old_sandstone_02",
    "hlina": "stony_dirt_path",
    "trava": "grass_path_2",
}
MAPS = {"diff": "Diffuse", "nor": "nor_gl", "rough": "Rough", "disp": "Displacement"}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex_cache")


UA = {"User-Agent": "tvrz-blender/1.0"}


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def download(url, path):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(path, "wb") as f:
        f.write(r.read())


def fetch(res="2k"):
    os.makedirs(ROOT, exist_ok=True)
    meta = {}
    for name, pid in ASSETS.items():
        files = get_json("https://api.polyhaven.com/files/" + pid)
        info = get_json("https://api.polyhaven.com/info/" + pid)
        dims = info.get("dimensions") or [2000, 2000]
        meta[name] = {"id": pid, "size_m": [dims[0] / 1000.0, dims[1] / 1000.0], "maps": {}}
        for key, api_key in MAPS.items():
            if api_key not in files:
                continue
            url = files[api_key][res]["jpg"]["url"] if "jpg" in files[api_key][res] else files[api_key][res]["png"]["url"]
            ext = os.path.splitext(url)[1]
            path = os.path.join(ROOT, "%s_%s_%s%s" % (name, key, res, ext))
            if not os.path.exists(path):
                download(url, path)
            meta[name]["maps"][key] = os.path.basename(path)
        print(name, pid, meta[name]["size_m"], sorted(meta[name]["maps"]))
    with open(os.path.join(ROOT, "meta_%s.json" % res), "w") as f:
        json.dump(meta, f, indent=1)


if __name__ == "__main__":
    fetch(sys.argv[1] if len(sys.argv) > 1 else "2k")
