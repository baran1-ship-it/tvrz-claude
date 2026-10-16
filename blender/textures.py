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
    "strecha": "roof_09",
    "kamen": "rock_surface",
    "malta": "plastered_stone_wall",
    "dosky": "thatch_roof_angled",
    "skala_piskovec": "cliff_side",       # erodovane vrstvy piskovce (skalni mesto)
    "skala_vrstvy": "rock_06",            # zluty vrstevnaty kamen
    "kamen_lisejnik": "lichen_rock",      # balvany a skalky s lisejnikem
    "kura": "bark_brown_02",              # kura kulatiny (ohrady, zerdi, polena)
    "drevo_stare": "weathered_brown_planks",  # zasedla prkna plotu a chlevu
    # teren (krok 1 prestavby krajiny): louka, lesni hrabanka, blativa cesta, letecky snimek travy na dalku
    "hrabanka": "forest_leaves_02",
    "blato": "brown_mud_leaves_01",
    "louka_letecky": "aerial_grass_rock",
    # pole (K1b): obili/strniste, oranice/uhor
    "pole_obili": "withered_grass",
    "pole_oranice": "dry_mud_field_001",
}
# naskenovane modely (rostliny, kameny) - glTF
MODELS = ["fir_tree_01", "pine_tree_01", "fir_sapling", "fir_sapling_medium", "pine_sapling_medium",
          "shrub_01", "shrub_02", "shrub_04", "nettle_plant", "fern_02", "weed_plant_02", "dandelion_01",
          "grass_medium_01", "grass_medium_02", "tree_stump_01", "rock_moss_set_01", "dry_branches_medium_01",
          # lesni podrost a zarust ruin (barvinek a vlastovicnik rostou na hrbitovech a u zdi zricenin)
          "periwinkle_plant", "celandine_01", "moss_01", "rock_moss_set_02", "root_cluster_01", "root_cluster_02",
          "dead_tree_trunk", "dead_tree_trunk_02", "tree_stump_02", "bark_debris_01", "pine_sapling_small"]
# ambientCG (CC0): Poly Haven nema svezi zelenou louku (vsechny travnate povrchy jsou suche/podzimni)
ASSETS_ACG = {"louka": ("Grass004", 2.0), "louka_dal": ("Grass001", 2.0)}
ACG_MAPS = {"diff": "Color", "nor": "NormalGL", "rough": "Roughness", "disp": "Displacement"}
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
    # zachovat i textury pridane rucne mimo ASSETS (napr. sindel)
    mp = os.path.join(ROOT, "meta_%s.json" % res)
    meta = json.load(open(mp)) if os.path.exists(mp) else {}
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


def fetch_acg(res="2k"):
    """ambientCG: zip s mapami -> stejne pojmenovani jako Poly Haven (<nazev>_<mapa>_<res>.jpg) do meta."""
    import io
    import zipfile
    mp = os.path.join(ROOT, "meta_%s.json" % res)
    meta = json.load(open(mp)) if os.path.exists(mp) else {}
    for name, (aid, size) in ASSETS_ACG.items():
        url = "https://ambientcg.com/get?file=%s_%s-JPG.zip" % (aid, res.upper())
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
        meta[name] = {"id": "ambientcg:" + aid, "size_m": [size, size], "maps": {}}
        for key, suf in ACG_MAPS.items():
            src = [n for n in z.namelist() if n.endswith("_%s.jpg" % suf)]
            if not src:
                continue
            fn = "%s_%s_%s.jpg" % (name, key, res)
            with open(os.path.join(ROOT, fn), "wb") as f:
                f.write(z.read(src[0]))
            meta[name]["maps"][key] = fn
        print(name, aid, sorted(meta[name]["maps"]))
    with open(mp, "w") as f:
        json.dump(meta, f, indent=1)


def fetch_models(res="1k"):
    for pid in MODELS:
        files = get_json("https://api.polyhaven.com/files/" + pid)
        g = files["gltf"][res]["gltf"]
        d = os.path.join(ROOT, "models", pid)
        os.makedirs(d, exist_ok=True)
        main = os.path.join(d, pid + ".gltf")
        if not os.path.exists(main):
            download(g["url"], main)
        for rel, inc in g.get("include", {}).items():
            path = os.path.join(d, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                download(inc["url"], path)
        print("model", pid)


if __name__ == "__main__":
    fetch(sys.argv[1] if len(sys.argv) > 1 else "2k")
    fetch_acg(sys.argv[1] if len(sys.argv) > 1 else "2k")
    if len(sys.argv) <= 1 or sys.argv[1] == "2k":
        fetch_models()
