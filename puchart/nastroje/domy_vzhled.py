"""Vzhled domů Havrana ve hře (pravidla/svet/mista.json modely.domy stin_obal, omitka_diry) přímo v glb – bez Blenderu,
kolize OMI_physics zůstanou (viz blender/okap_vstupu.py):
  stin_obal   – stínová kopie hrubého obalu <Dům>_Daleko_Stin: vrcholy stěn obalu (plochy *_daleko_Roubeni), které leží vně
                půdorysu domu zmenšeného o odsazeni_m (půdorys z vnějšího líce podrobné sítě), přesunuté na jeho okraj;
                střecha beze změny. Hra (hlavni.gd _mista) ji kreslí jen do
                stínu. Dřív stín vrhal přímo obal, jehož stěny leží na líci nebo před ním (Dum2: obal ±3,32, omítka ±3,13;
                Dum1, Rychta: obal = líc trámů) → osvětlená zeď ležela ve stínu vlastního obalu a kde ji líc přesáhl, svítily
                pilovité pruhy (Míša 16. 11.: „černé fleky a světlé pruhy na omítce“ Dum2).
  omitka_diry – v textuře opadané omítky (M_OmitkaPecena: bílá omítka s dírami na tmavé roubení) zesvětlit díry na cil_jas:
                převod z Havrana (nastroje/havran/stavby_export.gd _jas) zesvětluje texturu podle průměru – omítka má průměr
                nad 0,5, takže dřevo v dírách zůstalo tmavé (jas 0,21, roubení domů 0,5) a ve stínu bylo černé.
Běží v nastroje/stavby_z_havrana.sh po nastroje/topeni_domy.py a před blender/stredni_lod.py; opakované spuštění nic
nezdvojí (asset.extras.domy_vzhled).
  python3 nastroje/domy_vzhled.py <K>"""
import sys, os, json, io
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_sit import nacti, uloz, cti, pridej, zhutni

K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
MD = json.load(open(os.path.join(K, "pravidla/svet/mista.json")))["modely"]["domy"]
P_ = os.path.join(K, "hra", MD["soubor"][len("res://"):])
j, b, zbytek = nacti(P_)
ex = j.setdefault("asset", {}).setdefault("extras", {})
hotovo = ex.get("domy_vzhled", {})
MAT = [m.get("name", "") for m in j["materials"]]
N_SITI0 = len(j["meshes"])   # sítě se jen přidávají (kolize OMI_physics_shape na ně odkazují indexem)


def pudorys(dum, so):
    """bezpečná oblast pro stěny stínu: půdorys domu z vnějšího líce (vrcholy sítě <Dům>_Vnejsek se svislou normálou v pásu
    pudorys_y, bez materiálů pudorys_bez), po řádcích a sloupcích (dům je ortogonálně konvexní – i Rychta s komorou),
    zmenšený o odsazeni_m. Vrací (mřížka bezpečných buněk, počátek, krok)."""
    from scipy import ndimage
    n = next(n for n in j["nodes"] if n.get("name") == dum + "_Vnejsek"); A = []
    for p in j["meshes"][n["mesh"]]["primitives"]:
        if any(x in MAT[p["material"]] for x in so["pudorys_bez"]): continue
        P = cti(j, b, p["attributes"]["POSITION"]); N = cti(j, b, p["attributes"]["NORMAL"])
        m = (P[:, 1] > so["pudorys_y"][0]) & (P[:, 1] < so["pudorys_y"][1]) & (np.abs(N[:, 1]) < 0.3)
        A.append(P[m][:, [0, 2]])
    A = np.concatenate(A).astype(np.float64); kr = so["mrizka_m"]; pas = so["pas_m"]
    if len(A) < 20: return None   # bez svislých stěn mimo vynechané materiály (chýše s kůrou: stěny = střecha)
    lo = A.min(0) - 1.0; nx, nz = (np.ceil((A.max(0) + 1.0 - lo) / kr)).astype(int)
    X = lo[0] + (np.arange(nx) + 0.5) * kr; Z = lo[1] + (np.arange(nz) + 0.5) * kr
    G = np.ones((nx, nz), bool)
    for osa, S, T_ in ((1, Z, X), (0, X, Z)):   # řádky (pro každé z rozsah x) a sloupce (pro každé x rozsah z)
        jina = 1 - osa
        for k, sv in enumerate(S):
            w = A[np.abs(A[:, osa] - sv) < pas / 2]
            ok = np.zeros(len(T_), bool) if not len(w) else (T_ >= w[:, jina].min()) & (T_ <= w[:, jina].max())
            if osa == 1: G[:, k] &= ok
            else: G[k, :] &= ok
    G = ndimage.binary_opening(G, iterations=2)
    bezp = ndimage.distance_transform_edt(G) * kr >= so["odsazeni_m"]
    return bezp, lo, kr


def stin_obal(so):
    """<Dům>_Daleko → <Dům>_Daleko_Stin se stěnami uvnitř půdorysu zmenšeného o odsazeni_m"""
    from scipy import ndimage
    n_ = 0; jmena = {n.get("name"): i for i, n in enumerate(j["nodes"])}
    for dum in MD["koreny"]:
        io_ = jmena.get(dum + so["obal"]); ist = jmena.get(dum + so["obal"] + so["pripona"])
        if io_ is None or "mesh" not in j["nodes"][io_] or dum + "_Vnejsek" not in jmena: continue
        pu = pudorys(dum, so)
        if pu is None: continue
        bezp, lo, kr = pu
        _, (iX, iZ) = ndimage.distance_transform_edt(~bezp, return_indices=True)   # nejbližší bezpečná buňka
        prims = []
        for p in j["meshes"][j["nodes"][io_]["mesh"]]["primitives"]:
            q = {"attributes": {"POSITION": p["attributes"]["POSITION"]}, "indices": p["indices"], "material": p["material"]}
            if MAT[p["material"]].endswith(so["steny"]):
                P = cti(j, b, p["attributes"]["POSITION"]).astype(np.float64)
                gi = np.clip(((P[:, [0, 2]] - lo) / kr).astype(int), 0, np.array(bezp.shape) - 1)
                ven = ~bezp[gi[:, 0], gi[:, 1]]
                cx = iX[gi[:, 0], gi[:, 1]]; cz = iZ[gi[:, 0], gi[:, 1]]
                P2 = P.copy()
                P2[ven, 0] = lo[0] + (cx[ven] + 0.5) * kr; P2[ven, 2] = lo[1] + (cz[ven] + 0.5) * kr
                q["attributes"]["POSITION"] = pridej(j, b, P2.astype(np.float32), "f")
            prims.append(q)
        sit_ = {"name": dum + so["obal"] + so["pripona"], "primitives": prims}
        if ist is not None and "mesh" in j["nodes"][ist]: j["meshes"][j["nodes"][ist]["mesh"]] = sit_   # znovu: přepsat tutéž síť
        else:
            j["meshes"].append(sit_)
            uz = {"name": dum + so["obal"] + so["pripona"], "mesh": len(j["meshes"]) - 1}
            j["nodes"].append(uz); ni = len(j["nodes"]) - 1
            rod = next((i for i, n in enumerate(j["nodes"]) if io_ in n.get("children", [])), None)
            if rod is not None: j["nodes"][rod]["children"].append(ni)
            else: j["scenes"][j.get("scene", 0)]["nodes"].append(ni)
        n_ += 1
    # sítě se nikdy nemažou ani nepřečíslují: kolize OMI_physics_shape (convex.mesh) odkazují na sítě bez uzlu (16. 11.: úklid
    # „neodkazovaných“ sítí rozbil kolize domů – trasy vsi uvízly)
    print("DOMY_VZHLED stin_obal %d domů, stěny %.2f m za vnějším lícem" % (n_, so["odsazeni_m"]))


def omitka_diry(od):
    """díry v opadané omítce (jas pod prah_jas) zesvětlit na průměr cil_jas, přechod měkký (prah_jas … prah_jas_do)"""
    for mi, m in enumerate(j["materials"]):
        if m.get("name") not in od["materialy"]: continue
        ti = m.get("pbrMetallicRoughness", {}).get("baseColorTexture", {}).get("index")
        if ti is None: continue
        im_ = j["images"][j["textures"][ti]["source"]]; bv = j["bufferViews"][im_["bufferView"]]; o = bv.get("byteOffset", 0)
        a = np.asarray(Image.open(io.BytesIO(bytes(b[o:o + bv["byteLength"]]))).convert("RGB")).astype(np.float64) / 255.0
        L = a @ np.array([0.2126, 0.7152, 0.0722])
        vypln = np.all(np.abs(a - a[0, -1]) < 0.02, axis=2)   # šedá výplň atlasu mimo ostrovy UV (roh vpravo nahoře)
        w = np.clip((od["prah_jas_do"] - L) / (od["prah_jas_do"] - od["prah_jas"]), 0.0, 1.0); w[vypln] = 0.0
        w = np.asarray(Image.fromarray((w * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(od["rozostreni_px"]))).astype(np.float64) / 255.0
        dira = w > 0.99
        f = od["cil_jas"] / max(float(L[dira].mean()), 1e-3)
        a2 = np.clip(a * (1.0 + (f - 1.0) * w)[..., None], 0.0, 1.0)
        bio = io.BytesIO(); Image.fromarray((a2 * 255 + 0.5).astype(np.uint8)).save(bio, "JPEG", quality=int(od["jpeg_kvalita"]))
        data = bio.getvalue(); b.extend(b"\0" * ((4 - len(b) % 4) % 4))
        j["bufferViews"].append({"buffer": 0, "byteOffset": len(b), "byteLength": len(data)}); b.extend(data)
        im_["bufferView"] = len(j["bufferViews"]) - 1; im_["mimeType"] = "image/jpeg"
        print("DOMY_VZHLED omitka_diry %s: díry %.1f %% textury, jas %.2f → %.2f (×%.2f)" % (m["name"], 100 * dira.mean(), L[dira].mean(), od["cil_jas"], f))


if "stin_obal" in MD and hotovo.get("stin_obal") != MD["stin_obal"]["odsazeni_m"]:
    stin_obal(MD["stin_obal"]); hotovo["stin_obal"] = MD["stin_obal"]["odsazeni_m"]
if "omitka_diry" in MD and not hotovo.get("omitka_diry"):   # zesvětlení jen jednou (znovu by násobilo)
    omitka_diry(MD["omitka_diry"]); hotovo["omitka_diry"] = MD["omitka_diry"]["cil_jas"]
ex["domy_vzhled"] = hotovo
_sh = j.get("extensions", {}).get("OMI_physics_shape", {}).get("shapes", [])
assert len(j["meshes"]) >= N_SITI0 and all(s_.get(s_["type"], {}).get("mesh", 0) < len(j["meshes"]) for s_ in _sh), "kolize OMI odkazují mimo sítě"
uloz(P_, j, zhutni(j, b), zbytek)
