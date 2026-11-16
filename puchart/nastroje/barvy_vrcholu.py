"""Barvy vrcholů modelů od modeláře lineární (glTF COLOR_0) → sRGB pro renderer Compatibility (pravidla/svet/barvy_vrcholu.json,
chyby.md 356). Spustí nastroje/godot/barvy_vrcholu.gd na sítě *_mesh.res vybraných sad; převedená síť nese metadata značky
(opakovaně nic nezmění), zprávu (značka, velikost, průměrná barva) sloučí do build/barvy_vrcholu.json pro test smysl:barvy_vrcholu.
Pravidla zkopíruje do hra/pravidla/svet.
  python3 nastroje/barvy_vrcholu.py <K> [sada …]   (bez sady = všechny)"""
import sys, os, json, glob, shutil, subprocess, tempfile
import numpy as np

K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
C = json.load(open(os.path.join(K, "pravidla/svet/barvy_vrcholu.json")))
shutil.copy2(os.path.join(K, "pravidla/svet/barvy_vrcholu.json"), os.path.join(K, "hra/pravidla/svet/barvy_vrcholu.json"))
sady = sys.argv[2:] or list(C["sady"])
ZP = os.path.join(K, C["zprava"])
zprava = json.load(open(ZP)) if os.path.exists(ZP) else {}
if not C["prevest_na_srgb"]:
    print("BARVY_VRCHOLU převod vypnut (prevest_na_srgb false)"); sys.exit(0)
G = os.environ.get("G", "/opt/godot47/Godot_v4.7.2-stable_linux.x86_64")
HRA = os.path.join(K, "hra")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _srgb(c):
    c = np.clip(c, 0.0, 1.0); return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def glb_sada(s):
    """sada glb (lesní díly od modeláře – zajimava.gd _barva_vrcholu): COLOR_0 v bufferu glb lineární → sRGB, značka
    v asset.extras (opakovaně nic nezmění); Godot pak glb znovu importuje"""
    from glb_sit import nacti, uloz, cti, jako_float, z_floatu
    out = {}
    for f in sorted(glob.glob(os.path.join(K, C["sady"][s]["site"]))):
        j, b, zb = nacti(f); hot = j.setdefault("asset", {}).setdefault("extras", {}).get(C["znacka"], False)
        acc = sorted({p["attributes"]["COLOR_0"] for m in j.get("meshes", []) for p in m["primitives"] if "COLOR_0" in p["attributes"]})
        n = 0; soucet = np.zeros(3)
        for i in acc:
            d = jako_float(j, i, cti(j, b, i))
            if not hot:
                d[:, :3] = _srgb(d[:, :3]); raw = z_floatu(j, i, d).tobytes()
                a_ = j["accessors"][i]; bv = j["bufferViews"][a_["bufferView"]]
                if bv.get("byteStride", 0) not in (0, len(raw) // a_["count"]): print("BARVY_VRCHOLU_CHYBA %s: prokládaný COLOR_0" % f); sys.exit(1)
                off = bv.get("byteOffset", 0) + a_.get("byteOffset", 0); b[off:off + len(raw)] = raw
            n += len(d); soucet += d[:, :3].sum(0)
        if acc and not hot: j["asset"]["extras"][C["znacka"]] = True; uloz(f, j, b, zb)
        r = "res://" + os.path.relpath(f, HRA).replace(os.sep, "/")
        out[r] = {"srgb": bool(j["asset"]["extras"].get(C["znacka"], False)) or not acc, "velikost": os.path.getsize(f), "vrcholu_s_barvou": n,
                  "barva_prumer": [round(float(v), 3) for v in (soucet / max(n, 1))]}
        print("BARVY_VRCHOLU %s %s: %d vrcholů s barvou%s" % (s, os.path.basename(f), n, "" if hot or not acc else " → sRGB"))
    return out


for s in sady:
    if C["sady"][s]["site"].endswith(".glb"):
        zprava = {k: v for k, v in zprava.items() if not k.startswith("res://" + os.path.dirname(C["sady"][s]["site"])[4:] + "/")}
        zprava.update(glb_sada(s)); continue
    site = ["res://" + os.path.relpath(p, HRA).replace(os.sep, "/") for p in sorted(glob.glob(os.path.join(K, C["sady"][s]["site"])))]
    if not site: print("BARVY_VRCHOLU %s: žádné sítě (%s)" % (s, C["sady"][s]["site"])); continue
    sk = os.path.join(HRA, "_barvy_vrcholu.gd"); shutil.copy2(os.path.join(K, "nastroje/godot/barvy_vrcholu.gd"), sk)
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False); tmp.close()
    r = subprocess.run([G, "--headless", "--path", HRA, "-s", "res://_barvy_vrcholu.gd", "--", C["znacka"], tmp.name] + site, capture_output=True, text=True)
    for f in ("_barvy_vrcholu.gd", "_barvy_vrcholu.gd.uid"):
        if os.path.exists(os.path.join(HRA, f)): os.remove(os.path.join(HRA, f))
    vys = [l for l in r.stdout.splitlines() if l.startswith("BARVY_VRCHOLU")]
    print("\n".join("%s (%s)" % (l, s) for l in vys) or "BARVY_VRCHOLU_CHYBA %s: Godot nic nevypsal (%d)" % (s, r.returncode))
    if r.returncode != 0 or not vys or any("CHYBA" in l for l in vys): os.remove(tmp.name); sys.exit(1)
    zprava = {k: v for k, v in zprava.items() if not k.startswith("res://" + os.path.dirname(C["sady"][s]["site"])[4:] + "/")}
    zprava.update(json.load(open(tmp.name))); os.remove(tmp.name)
os.makedirs(os.path.dirname(ZP), exist_ok=True)
json.dump(zprava, open(ZP, "w"), ensure_ascii=False, indent=1, sort_keys=True)
