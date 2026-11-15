"""Úprava domů Havrana pro topení od modeláře (pravidla/svet/topeni.json upravy_domy) přímo v glb – bez Blenderu, kolize
OMI_physics zůstanou (Blender je ztrácí, viz blender/okap_vstupu.py):
  pec_pryc  – stará pec Havrana (blender/ves_domy.py: podstavec a kamínkové ohniště M_Kamen, klenba M_PecHlina, začouzení
              M_PecZacouzena, ústí M_Tma, žár M_Zhar) = trojúhelníky sítě <Dům>_Interier celé uvnitř kvádru; uzel kolize
              <Dům>_Kol_Pec pryč. Novou pec (Pec_Chalupni) vloží hra podle topeni.json vlozit.
  prostupy  – otvor pro komín (záklop, střecha): trojúhelníky sítí s danými materiály rozříznuté rovinami x0, x1, z0, z1
              a smazané ty, jejichž těžiště je uvnitř kvádru (prkna záklopu končí na komínu jako u výměny, šindel na lemování).
Běží po blender/okap_vstupu.py (ten zapisuje domy.glb z originálu) a před blender/stredni_lod.py; opakované spuštění nic
nezdvojí (smazané už smazané není, řezy už jsou na rovinách).
  python3 nastroje/topeni_domy.py <K>"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_sit import nacti, uloz, cti, pridej, rozrizni, smaz_uzly, jako_float, z_floatu, zhutni

K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
U = json.load(open(os.path.join(K, "pravidla/svet/topeni.json")))["upravy_domy"]
P_ = os.path.join(K, U["soubor"])
j, b, zbytek = nacti(P_)
N = {n.get("name"): n for n in j["nodes"]}
MAT = [m.get("name", "") for m in j["materials"]]


def site_uzlu(jm):
    n = N.get(jm)
    return [] if n is None or "mesh" not in n else j["meshes"][n["mesh"]]["primitives"]


def zapis_indexy(p, I):
    p["indices"] = pridej(j, b, I.reshape(-1).astype(np.uint32), "i")


celkem = 0
for dum, q in U["pec_pryc"].items():
    x0, x1, y0, y1, z0, z1 = q; n_ = 0
    for p in site_uzlu(dum + "_Interier"):   # síť bez transformace uzlu (domy.glb: sítě v souřadnicích modelu domu)
        P = cti(j, b, p["attributes"]["POSITION"]); I = cti(j, b, p["indices"]).reshape(-1, 3).astype(np.int64)
        T = P[I]; lo = T.min(1); hi = T.max(1)
        uvnitr = (lo[:, 0] >= x0) & (hi[:, 0] <= x1) & (lo[:, 1] >= y0) & (hi[:, 1] <= y1) & (lo[:, 2] >= z0) & (hi[:, 2] <= z1)
        if uvnitr.any():
            zapis_indexy(p, I[~uvnitr]); n_ += int(uvnitr.sum())
    for jm in (dum + "_Interier",):   # materiál bez trojúhelníků (M_Tma, M_PecHlina…) pryč – Godot nepřijme accessor s 0 prvky
        n = N.get(jm)
        if n is not None and "mesh" in n:
            pr = j["meshes"][n["mesh"]]["primitives"]
            pr[:] = [p for p in pr if j["accessors"][p["indices"]]["count"] > 0]
    k_ = smaz_uzly(j, {dum + "_Kol_Pec"})
    N = {n.get("name"): n for n in j["nodes"]}
    print("TOPENI_DOMY %s stará pec: smazáno %d trojúhelníků, kolize %s" % (dum, n_, "pryč" if k_ else "už není"))
    celkem += n_

for dum, seznam in U.get("prostupy", {}).items():
    for o in seznam:
        x0, x1, y0, y1, z0, z1 = o["kvadr"]; n_ = 0
        for jm in o["site"]:
            for p in site_uzlu(jm):
                if not any(MAT[p["material"]].startswith(m) for m in o["materialy"]): continue
                at = p["attributes"]
                A = {k: jako_float(j, i, cti(j, b, i)) for k, i in at.items()}
                I = cti(j, b, p["indices"]).reshape(-1, 3).astype(np.int64)
                n0 = len(I)
                for osa, c in ((0, x0), (0, x1), (2, z0), (2, z1)):
                    T = A["POSITION"][I]; lo = T.min(1); hi = T.max(1)
                    vyber = (hi[:, 0] > x0) & (lo[:, 0] < x1) & (hi[:, 2] > z0) & (lo[:, 2] < z1) & (hi[:, 1] > y0) & (lo[:, 1] < y1)
                    A, I = rozrizni(A, I, osa, c, vyber)
                c_ = A["POSITION"][I].mean(1)
                pryc = (c_[:, 0] > x0) & (c_[:, 0] < x1) & (c_[:, 2] > z0) & (c_[:, 2] < z1) & (c_[:, 1] > y0) & (c_[:, 1] < y1)
                if not pryc.any() and len(I) == n0: continue
                if "NORMAL" in A: A["NORMAL"] /= np.maximum(np.linalg.norm(A["NORMAL"], axis=1, keepdims=True), 1e-9)
                for k, i in list(at.items()):
                    at[k] = pridej(j, b, A[k].astype(np.float32) if j["accessors"][i]["componentType"] == 5126 else z_floatu(j, i, A[k]),
                                   "f" if k == "POSITION" else "a", None if j["accessors"][i]["componentType"] == 5126 else i)
                zapis_indexy(p, I[~pryc]); n_ += int(pryc.sum())
                if not (~pryc).any(): print("TOPENI_DOMY POZOR: prostup smazal celý materiál", MAT[p["material"]])
        print("TOPENI_DOMY %s prostup %s: smazáno %d trojúhelníků" % (dum, o["popis"][:40], n_))
        celkem += n_
uloz(P_, j, zhutni(j, b), zbytek)   # bez starých dat upravených sítí (jinak +5 MB)
print("TOPENI_DOMY hotovo (%d trojúhelníků pryč) → %s" % (celkem, P_))
