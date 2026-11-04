"""Hlídač tesařských spojů (docs/reference/tesarske_spoje.md; Míša 3. 11.: „ne že budou dva kusy trámů do sebe zapuštěné
jakoby vrostlé, má to být stolařsky správně všude“).

Vstup build/tramy.json (blender/puchart_hrad.py zapisuje každý Part.beam). Pro každou dvojici trámů, které se prolínají
víc než o toleranci, rozhodne:
  čep      – konec jednoho trámu je celou čelní plochou uvnitř druhého (čep v dlabu / sloup pod trámem): v pořádku
  plát     – souběžné trámy přeložené přes sebe (nastavení plátem, zábradlí na sloupku): v pořádku
  vrostlý  – konec vstupuje do druhého trámu jen částí čela (šikmo „vrostlý“, čelo trčí ven nebo prorazí na druhé straně)
  křížení  – dva trámy se protínají uprostřed délky bez přeplátování (žádný konec v druhém)
Výstup build/spoje.json + souhrn; návratový kód 1, když vadných spojů přibylo nad strop v pravidla/svet/kontroly.json
(spoje.max_vadnych) – staré vady se odstraňují postupně, nové nesmí přibýt.
"""
import json, os, sys
import numpy as np

K = sys.argv[1] if len(sys.argv) > 1 else "."
D = json.load(open(os.path.join(K, "build/tramy.json")))["tramy"]
DREVO = ("dub", "hraz")
T = [t for t in D if t[3].startswith(DREVO)]
C = np.array([t[0] for t in T]); R = np.array([t[1] for t in T]).transpose(0, 2, 1); Hs = np.array([t[2] for t in T])   # R[i][:, k] = k-tá osa
TOL = 0.02   # přiložený díl (pásek z líce, zábradlí na sloupku) se dotýká – nepravidelnost tesaných trámů j ±5 %

def rohy_cela(i, z):
    c, r, h = C[i], R[i], Hs[i]
    return np.array([c + r[:, 0] * sx * h[0] + r[:, 1] * sy * h[1] + r[:, 2] * z * h[2] for sx in (-1, 1) for sy in (-1, 1)])

def uvnitr(p, j, tol=0.01):
    q = (p - C[j]) @ R[j]
    return np.all(np.abs(q) <= Hs[j] + tol, axis=-1)

def prekryv(i, j):
    """SAT: nejmenší průnik dvou kvádrů (záporné = oddělené)."""
    ax = [R[i][:, k] for k in range(3)] + [R[j][:, k] for k in range(3)]
    for a in range(3):
        for b in range(3):
            v = np.cross(R[i][:, a], R[j][:, b]); n = np.linalg.norm(v)
            if n > 1e-6: ax.append(v / n)
    d = C[j] - C[i]; m = 1e9
    for v in ax:
        ri = np.sum(np.abs(R[i].T @ v) * Hs[i]); rj = np.sum(np.abs(R[j].T @ v) * Hs[j])
        m = min(m, ri + rj - abs(d @ v))
        if m < 0: return m
    return m

# kandidáti přes mřížku AABB
ext = np.abs(R) @ Hs[..., None]; ext = ext[..., 0]
lo, hi = C - ext, C + ext
cell = 2.0; grid = {}
for i in range(len(T)):
    for gx in range(int(lo[i, 0] // cell), int(hi[i, 0] // cell) + 1):
        for gy in range(int(lo[i, 1] // cell), int(hi[i, 1] // cell) + 1):
            for gz in range(int(lo[i, 2] // cell), int(hi[i, 2] // cell) + 1):
                grid.setdefault((gx, gy, gz), []).append(i)
pary = set()
for v in grid.values():
    for a in range(len(v)):
        for b in range(a + 1, len(v)):
            i, j = v[a], v[b]
            if np.all(lo[i] <= hi[j]) and np.all(lo[j] <= hi[i]): pary.add((i, j))

vysl = {"čep": 0, "plát": 0, "přeplátování": 0, "rohový plát": 0, "osedlání": 0, "vrostlý": 0, "křížení": 0}; vady = []
for i, j in sorted(pary):
    if prekryv(i, j) <= TOL: continue
    if abs(R[i][:, 2] @ R[j][:, 2]) > 0.98: vysl["plát"] += 1; continue
    druh = None
    for x, y in ((i, j), (j, i)):
        for z in (-1, 1):
            k = uvnitr(rohy_cela(x, z), y)
            if k.all(): druh = "čep"; break
            stred_in = uvnitr(C[x] + R[x][:, 2] * z * Hs[x][2], y, 0.0)
            if stred_in and 0.25 < abs(R[x][1, 2]) < 0.95 and k.sum() >= 2: druh = "osedlání"; break   # šikmý díl (schodnice, vzpěra) osedlaný na trámu: střed čela v trámu, nanejvýš půl čela venku
            if k.any() or stred_in: druh = druh or "vrostlý"
        if druh == "osedlání": break
        if druh == "čep": break
    if druh == "osedlání": vysl[druh] += 1; continue
    if druh in (None, "vrostlý") and any(uvnitr(rohy_cela(i, z), j, 0.15).any() for z in (-1, 1)) and any(uvnitr(rohy_cela(j, z), i, 0.15).any() for z in (-1, 1)):
        druh = "rohový plát"   # oba trámy končí v sobě navzájem (roh prahu/vaznice, rám) – rohové přeplátování
    if druh is None or druh == "křížení":   # přeplátování: v kolmém směru se prolínají nejvýš o polovinu tloušťky (výřez do půl)
        n_ = np.cross(R[i][:, 2], R[j][:, 2]); n_ /= np.linalg.norm(n_)
        ri = np.sum(np.abs(R[i].T @ n_) * Hs[i]); rj = np.sum(np.abs(R[j].T @ n_) * Hs[j])
        if ri + rj - abs((C[j] - C[i]) @ n_) <= 0.55 * 2 * min(ri, rj) + 0.01: druh = "přeplátování"
    druh = druh or "křížení"
    vysl[druh] += 1
    if druh in ("vrostlý", "křížení"):
        p = (C[i] + C[j]) / 2
        vady.append({"druh": druh, "ij": [int(i), int(j)], "dily": [T[i][4], T[j][4]], "bod": [round(float(p[0]), 2), round(float(p[2]), 2), round(float(p[1]), 2)],
                     "rozmery": [[round(2 * x, 2) for x in Hs[i]], [round(2 * x, 2) for x in Hs[j]]]})
souhrn = {}
for v in vady: souhrn.setdefault(v["dily"][0], {}).setdefault(v["druh"], 0); souhrn[v["dily"][0]][v["druh"]] += 1
json.dump({"popis": "tesařské spoje trámů hradu (nastroje/kontrola_spoju.py)", "pocty": vysl, "souhrn_dilu": souhrn, "vady": vady},
          open(os.path.join(K, "build/spoje.json"), "w"), ensure_ascii=False, indent=1)
print("SPOJE trámů %d, dvojic %d:" % (len(T), len(pary)), vysl)
for d_, v in sorted(souhrn.items(), key=lambda x: -sum(x[1].values()))[:15]: print("  ", d_, v)
strop = json.load(open(os.path.join(K, "pravidla/svet/kontroly.json"))).get("spoje", {}).get("max_vadnych")
n = vysl["vrostlý"] + vysl["křížení"]
if strop is not None and n > strop:
    print("SPOJE CHYBA: vadných %d > strop %d" % (n, strop)); sys.exit(1)
