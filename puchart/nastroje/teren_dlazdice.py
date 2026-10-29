"""Pečení terénu do dlaždic (PDF kap. 7 krok 6–7: dlaždice, detailní a vzdálené verze, zabalit do hry).

Vstup:  mřížka 1 m výseku (dmr_mrizka.py), mřížka obzoru, pravidla/svet/svet.json + teren.json
Výstup: data/teren/vysek.r16 + vysek.json   – výšky pro kolize a pokládání (uint16, krok 5 mm)
        hra/dlazdice/t_<i>_<j>.glb          – uzly LOD0..LOD3 (sukně proti škvírám mezi LOD)
        hra/dlazdice/obzor.glb              – vzdálená hmota s dírou pro výsek
Nic z toho se nepočítá na tabletu (poučení z Havrana: svět 83–110 s při startu).

python3 teren_dlazdice.py <vysek_prefix> <obzor_prefix> <koren_puchartu>
"""
import sys, json, os, struct
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

vys_pre, obz_pre, koren = sys.argv[1:4]
S = json.load(open(os.path.join(koren, "pravidla/svet/svet.json")))
T = json.load(open(os.path.join(koren, "pravidla/svet/teren.json")))
P = S["pocatek"]
H = np.load(vys_pre + ".npy").astype(np.float64)
M = json.load(open(vys_pre + ".json"))
assert M["krok_m"] == T["mrizka_m"]
H = gaussian_filter(H, T["vyhlazeni_sigma_m"] / M["krok_m"])
ny, nx = H.shape
# hra: sloupec c -> x = X0 + c - P.X ; řádek r -> z = -(Y1 - r - P.Y)
x_hra0 = M["x0"] - P["X"]
z_hra0 = -(M["y1"] - P["Y"])
Y = (H - P["H"]).astype(np.float32)

out_dat = os.path.join(koren, "hra/data"); os.makedirs(out_dat, exist_ok=True)
r16 = np.clip(np.round((H - 300.0) * 200.0), 0, 65535).astype("<u2")
r16.tofile(os.path.join(out_dat, "vysek.r16"))
json.dump({"sirka": nx, "vyska": ny, "krok_m": 1.0, "x0_hra": x_hra0, "z0_hra": z_hra0,
           "y_z_r16": "y_hra = r16 / 200 + 300 - pocatek.H", "pocatek_H": P["H"],
           "vyhlazeni_sigma_m": T["vyhlazeni_sigma_m"], "zdroj": M["zdroj"]},
          open(os.path.join(out_dat, "vysek.json"), "w"), ensure_ascii=False, indent=1)

# normály z plné mřížky (stejné pro všechny LOD -> LOD se liší jen tvarem, ne světlem)
gz, gx = np.gradient(Y, 1.0)  # gz = dY/dřádek = dY/dz (řádek roste s z)
N = np.stack([-gx, np.ones_like(Y), -gz], -1)
N /= np.linalg.norm(N, axis=-1, keepdims=True)


def glb(meshes, cesta):
    """meshes: [(jmeno, pos(n,3) f32, nor(n,3) f32, idx(m,) u32)] -> jeden .glb, každý mesh vlastní uzel."""
    bin_ = bytearray(); views = []; acc = []; gm = []; nodes = []
    def pridej(data, target, typ, comp, minmax=False):
        nonlocal bin_
        while len(bin_) % 4: bin_ += b"\0"
        off = len(bin_); b = data.tobytes(); bin_ += b
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(b), "target": target})
        a = {"bufferView": len(views) - 1, "componentType": comp, "count": len(data), "type": typ}
        if minmax:
            a["min"] = data.min(0).tolist(); a["max"] = data.max(0).tolist()
        acc.append(a); return len(acc) - 1
    for jm, pos, nor, idx in meshes:
        ip = pridej(pos.astype("<f4"), 34962, "VEC3", 5126, True)
        inn = pridej(nor.astype("<f4"), 34962, "VEC3", 5126)
        ii = pridej(idx.astype("<u4"), 34963, "SCALAR", 5125)
        gm.append({"name": jm, "primitives": [{"attributes": {"POSITION": ip, "NORMAL": inn}, "indices": ii, "mode": 4}]})
        nodes.append({"name": jm, "mesh": len(gm) - 1})
    while len(bin_) % 4: bin_ += b"\0"
    js = {"asset": {"version": "2.0", "generator": "puchart teren_dlazdice.py"}, "scene": 0,
          "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": gm,
          "accessors": acc, "bufferViews": views, "buffers": [{"byteLength": len(bin_)}]}
    j = json.dumps(js, separators=(",", ":")).encode()
    while len(j) % 4: j += b" "
    with open(cesta, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(bin_)))
        f.write(struct.pack("<II", len(j), 0x4E4F534A)); f.write(j)
        f.write(struct.pack("<II", len(bin_), 0x004E4942)); f.write(bin_)


def sit(r0, c0, n_r, n_c, krok, sukne):
    """Pravidelná síť nad mřížkou Y od (r0, c0), n_r x n_c buněk po krok, se sukní po obvodu."""
    rr = r0 + np.arange(n_r + 1) * krok; cc = c0 + np.arange(n_c + 1) * krok
    R, C = np.meshgrid(rr, cc, indexing="ij")
    pos = np.stack([x_hra0 + C, Y[R, C], z_hra0 + R], -1).reshape(-1, 3)
    nor = N[R, C].reshape(-1, 3)
    w = n_c + 1
    q = (np.arange(n_r)[:, None] * w + np.arange(n_c)[None, :]).ravel()
    idx = np.stack([q, q + w, q + 1, q + 1, q + w, q + w + 1], -1).ravel()
    if sukne > 0:
        # obvod po směru: horní, pravý, dolní, levý; sukně svisle dolů, normála jako hrana
        ob = ([(0, c) for c in range(n_c + 1)] + [(r, n_c) for r in range(1, n_r + 1)]
              + [(n_r, c) for c in range(n_c - 1, -1, -1)] + [(r, 0) for r in range(n_r - 1, 0, -1)])
        ob.append(ob[0])
        bi = np.array([r * w + c for r, c in ob])
        base = len(pos)
        p2 = pos[bi].copy(); p2[:, 1] -= sukne
        pos = np.concatenate([pos, p2]); nor = np.concatenate([nor, nor[bi]])
        k = np.arange(len(bi) - 1)
        a, b, a2, b2 = bi[k], bi[k + 1], base + k, base + k + 1
        idx = np.concatenate([idx, np.stack([a, a2, b, b, a2, b2], -1).ravel(),
                              np.stack([a, b, a2, b, b2, a2], -1).ravel()])  # oboustranně (směr obvodu se mění)
    return pos, nor, idx.astype(np.uint32)


out_hra = os.path.join(koren, "hra/dlazdice"); os.makedirs(out_hra, exist_ok=True)
D = int(T["dlazdice_m"])
nt_r, nt_c = (ny - 1) // D, (nx - 1) // D
seznam = []
for i in range(nt_r):
    for j in range(nt_c):
        meshes = []
        for li, L in enumerate(T["lod"]):
            k = int(L["krok_m"]); n = D // k
            pos, nor, idx = sit(i * D, j * D, n, n, k, T["sukne_m"] + 1.5 * k)  # škvíra mezi LOD roste s krokem (snímek 01: světlé čáry)
            meshes.append((f"LOD{li}", pos, nor, idx))
        jm = f"t_{i}_{j}.glb"; glb(meshes, os.path.join(out_hra, jm))
        seznam.append({"soubor": jm, "stred": [x_hra0 + (j + 0.5) * D, float(Y[i*D:(i+1)*D, j*D:(j+1)*D].mean()), z_hra0 + (i + 0.5) * D],
                       "troj_lod": [len(m[3]) // 3 for m in meshes]})

# obzor: mřížka obzoru po 25 m, díra pro výsek (o 2 buňky menší, aby se překrýval pod sukní)
Ho = np.load(obz_pre + ".npy").astype(np.float64); Mo = json.load(open(obz_pre + ".json"))
ko = int(T["obzor"]["krok_m"] // Mo["krok_m"])
Ho = Ho[::ko, ::ko]; kr = Mo["krok_m"] * ko
xo = Mo["x0"] - P["X"] + np.arange(Ho.shape[1]) * kr
zo = -(Mo["y1"] - P["Y"]) + np.arange(Ho.shape[0]) * kr
ZZ, XX = np.meshgrid(zo, xo, indexing="ij")
Yo = (Ho - P["H"]).astype(np.float32)
# kde je výsek, vzít výšku z vyhlazené mřížky výseku a stáhnout o 1,5 m pod něj (žádný z-fight na okraji)
c = (XX - x_hra0); r = (ZZ - z_hra0)
uvnitr = (c >= 0) & (c <= nx - 1) & (r >= 0) & (r <= ny - 1)
Yo[uvnitr] = map_coordinates(Y, [r[uvnitr], c[uvnitr]], order=1) - 1.5
gzo, gxo = np.gradient(Yo, kr)
No = np.stack([-gxo, np.ones_like(Yo), -gzo], -1); No /= np.linalg.norm(No, axis=-1, keepdims=True)
w = Ho.shape[1]
pos = np.stack([XX, Yo, ZZ], -1).reshape(-1, 3); nor = No.reshape(-1, 3)
okraj = 2 * kr
cel = []
for a in range(Ho.shape[0] - 1):
    for b in range(w - 1):
        x_, z_ = xo[b] + kr / 2, zo[a] + kr / 2
        if (x_hra0 + okraj < x_ < x_hra0 + nx - 1 - okraj) and (z_hra0 + okraj < z_ < z_hra0 + ny - 1 - okraj):
            continue
        q = a * w + b; cel += [q, q + w, q + 1, q + 1, q + w, q + w + 1]
glb([("OBZOR", pos, nor, np.array(cel, np.uint32))], os.path.join(out_hra, "obzor.glb"))
json.dump({"dlazdice_m": D, "pocet": [nt_r, nt_c], "lod": T["lod"], "hystereze_m": T["hystereze_m"], "dlazdice": seznam,
           "obzor": {"soubor": "obzor.glb", "troj": len(cel) // 3}},
          open(os.path.join(out_hra, "dlazdice.json"), "w"), ensure_ascii=False, indent=1)
print("dlaždic", len(seznam), "troj LOD0..3 na dlaždici", seznam[0]["troj_lod"], "obzor troj", len(cel) // 3)
