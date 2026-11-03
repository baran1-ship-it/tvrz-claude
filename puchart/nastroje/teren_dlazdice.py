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
if os.path.exists(vys_pre + "_jamy.npz"):   # sklep: vyhladit terén, jako by jáma nebyla, a jámu vrátit s ostrou hranou
    from scipy.ndimage import distance_transform_edt
    J = np.load(vys_pre + "_jamy.npz"); mj = np.zeros(H.shape, bool); mj[J["r"], J["c"]] = True
    _, (ir, ic) = distance_transform_edt(mj, return_indices=True)
    H = gaussian_filter(H[ir, ic], T["vyhlazeni_sigma_m"] / M["krok_m"]); H[J["r"], J["c"]] = J["y"]
else:
    H = gaussian_filter(H, T["vyhlazeni_sigma_m"] / M["krok_m"])
ny, nx = H.shape
# hra: sloupec c -> x = X0 + c - P.X ; řádek r -> z = -(Y1 - r - P.Y)
x_hra0 = M["x0"] - P["X"]
z_hra0 = -(M["y1"] - P["Y"])
Y = (H - P["H"]).astype(np.float32)

def jako_sit(A, k):
    """Výšky 1 m přesně podle viditelné sítě LOD0 (krok k, trojúhelníky jako sit(): úhlopříčka (r, c+k)–(r+k, c)).
    Kolize, pokládání stromů/trávy/hradu = co je vidět (Míša 3. 11.: nic nelevituje, nepropadá se; Havran: nesoulad Blender/Godot)."""
    n_r, n_c = A.shape; r = np.arange(n_r); c = np.arange(n_c)
    R0 = np.minimum(r // k * k, n_r - 1 - k); C0 = np.minimum(c // k * k, n_c - 1 - k)
    fr = ((r - R0) / k)[:, None]; fc = ((c - C0) / k)[None, :]
    a = A[R0][:, C0]; b = A[R0][:, C0 + k]; cc = A[R0 + k][:, C0]; d = A[R0 + k][:, C0 + k]
    t1 = a + fc * (b - a) + fr * (cc - a); t2 = d + (1 - fc) * (cc - d) + (1 - fr) * (b - d)
    return np.where(fr + fc <= 1.0, t1, t2)
Hs = jako_sit(H, int(T["lod"][0]["krok_m"]))
jemne = np.zeros(H.shape, bool)   # jemný tvar má vlastní viditelnou síť 1 m: pás koryta (blender/voda.py BREH), jámy sklepa (hrad)
if os.path.exists(vys_pre + "_koryta.npz"):
    _K = np.load(vys_pre + "_koryta.npz"); jemne[_K["r"], _K["c"]] = True
if os.path.exists(vys_pre + "_jamy.npz"):   # jen sklep a šíje (n_upr); zářez koryt mimo pás je vidět sítí -> kolize podle sítě
    _n = int(J["n_upr"]) if "n_upr" in J else len(J["r"]); jemne[J["r"][:_n], J["c"][:_n]] = True
print("výšky podle sítě: max rozdíl %.2f m, jemných buněk %d" % (float(np.abs(Hs - H)[~jemne].max()), int(jemne.sum())))
H0 = H.copy(); H = np.where(jemne, H, Hs)
os.makedirs(os.path.join(koren, "build"), exist_ok=True)   # pro test smyslu teren_shoda: kde má jemný tvar vlastní síť
_kryto = np.zeros(H.shape, bool)
if os.path.exists(vys_pre + "_jamy.npz"): _kryto[J["r"][:_n], J["c"][:_n]] = True
np.savez_compressed(os.path.join(koren, "build/teren_jemne.npz"), m=np.packbits(jemne), kryto=np.packbits(_kryto), tvar=np.array(jemne.shape))
Y = (H - P["H"]).astype(np.float32)
out_dat = os.path.join(koren, "hra/data"); os.makedirs(out_dat, exist_ok=True)
r16 = np.clip(np.round((H - 300.0) * 200.0), 0, 65535).astype("<u2")
r16.tofile(os.path.join(out_dat, "vysek.r16"))
json.dump({"sirka": nx, "vyska": ny, "krok_m": 1.0, "x0_hra": x_hra0, "z0_hra": z_hra0,
           "y_z_r16": "y_hra = r16 / 200 + 300 - pocatek.H", "pocatek_H": P["H"],
           "vyhlazeni_sigma_m": T["vyhlazeni_sigma_m"], "zdroj": M["zdroj"]},
          open(os.path.join(out_dat, "vysek.json"), "w"), ensure_ascii=False, indent=1)

# pod jemným pásem břehů (blender/voda.py BREH, voda_hra.json koryto.jemny_pas) snížit síť dlaždic – pás leží na skutečném
# terénu 1 m, dlaždice 2 m by ho prorážely (Míša 3. 11.: hrany potoka jak pila). Kolize a pokládání dál z vysek.r16 (beze změny).
if os.path.exists(vys_pre + "_koryta.npz"):
    from scipy.ndimage import distance_transform_edt as _edt
    JP = json.load(open(os.path.join(koren, "pravidla/svet/voda_hra.json")))["koryto"]["jemny_pas"]
    KR_ = np.load(vys_pre + "_koryta.npz"); mk = np.zeros(Y.shape, bool); mk[KR_["r"], KR_["c"]] = True
    dv = _edt(mk)   # m od kraje pásu dovnitř
    Y = Y - (JP["pod_terenem_m"] * np.clip(dv / JP["nabeh_m"], 0, 1)).astype(np.float32)   # od kraje pásu (teren_shoda: dřív od 1 m síť vyčuhovala nad pás)
    from scipy.ndimage import maximum_filter as _mf   # ostrý zářez: kde by síť 2 m i tak vyčuhovala nad pás, snížit víc (test teren_shoda)
    k0 = int(T["lod"][0]["krok_m"]); Yp = (H - P["H"]).astype(np.float32)
    from scipy.ndimage import binary_dilation as _bdl
    mL = mk   # jen pás koryta (kryje ho BREH); jámu sklepa a šíje kryje zdivo hradu – za její okraj se nesnižuje (díry u šíje, tablet 2. 11.)
    mkd = _bdl(mL, iterations=k0); Y0 = Y.copy()   # vrcholy trojúhelníků přes okraj pásu smí taky dolů
    for _ in range(12):
        vy = np.where(mL, jako_sit(Y.astype(np.float64), k0) - Yp, -9.0)   # o kolik je síť nad skutečným terénem pásu
        if vy.max() <= -JP["rezerva_m"]: break
        Y = Y - (_mf(np.maximum(vy + JP["rezerva_m"], 0), size=2 * k0 + 1) * mkd).astype(np.float32)
    okraj = int((mkd & ~mL & (np.abs(Y - Y0) > 1e-4)).sum())
    H = np.where(jemne, H0, jako_sit(Y.astype(np.float64), k0) + P["H"])   # mimo pás a jámy: kolize = výsledná viditelná síť
    np.clip(np.round((H - 300.0) * 200.0), 0, 65535).astype("<u2").tofile(os.path.join(out_dat, "vysek.r16"))
    print("okraj pásu za maskou snížen: %d buněk" % okraj)
    print("terén pod jemným pásem snížen: %d buněk, pod jemnými tvary zbývá nad %.2f m" % (int(mk.sum()), float(vy.max())))
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
    rr = r0 + np.minimum(np.arange(n_r + 1) * krok, D); cc = c0 + np.minimum(np.arange(n_c + 1) * krok, D)   # poslední vzorek na D
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


# díry v terénu (Míša 3. 11.: „šachtu chci“): šachta studny – buňky LOD0 kolem ní nahradí jemná síť s otvorem; okraj čtverce
# leží na hranách mřížky 2 m, výšky z rovin trojúhelníků → navazuje přesně, bez škvír. Bez discard v shaderu (Adreno: výkon).
_HP = json.load(open(os.path.join(koren, "pravidla/svet/hrad_puchart.json")))
DIRY = [(float(_HP["A"]["studna"][0]), float(_HP["A"]["studna"][1]), float(_HP["teren"].get("sachta_r_m", 0.69)))]
def dira(pos, nor, idx, r0, c0, n, k):
    for (dx, dz, dr) in DIRY:
        cc = (dx - x_hra0); rr = (dz - z_hra0)   # mřížka 1 m
        q0c = int((cc - dr) // k * k) - k; q1c = int(-(-(cc + dr) // k) * k) + k; q0r = int((rr - dr) // k * k) - k; q1r = int(-(-(rr + dr) // k) * k) + k
        if not (c0 <= q0c and q1c <= c0 + n * k and r0 <= q0r and q1r <= r0 + n * k): continue   # celá ve dlaždici (studna je uprostřed)
        w = n + 1; tri = idx.reshape(-1, 3); nq = n * n
        quad = np.arange(nq * 2) // 2; qr = quad // n; qc = quad % n
        cr = r0 + qr * k; ccq = c0 + qc * k
        ven = ~((cr >= q0r) & (cr < q1r) & (ccq >= q0c) & (ccq < q1c))
        tri = np.concatenate([tri[:nq * 2][ven], tri[nq * 2:]])
        jm = 0.25; xs = np.arange(q0c, q1c + 1e-6, jm); zs = np.arange(q0r, q1r + 1e-6, jm)
        Yg = Y.astype(np.float64)
        def vys(rp, cp):   # rovina trojúhelníku sítě k (jako sit(): úhlopříčka (r, c+k)–(r+k, c))
            R0 = int(rp // k * k); C0 = int(cp // k * k); fr = (rp - R0) / k; fc = (cp - C0) / k
            R1 = min(R0 + k, Yg.shape[0] - 1); C1 = min(C0 + k, Yg.shape[1] - 1)
            a, b, c_, d = Yg[R0, C0], Yg[R0, C1], Yg[R1, C0], Yg[R1, C1]
            return a + fc * (b - a) + fr * (c_ - a) if fr + fc <= 1 else d + (1 - fc) * (c_ - d) + (1 - fr) * (b - d)
        base = len(pos); P_ = []; Nn = []
        for zr in zs:
            for xc in xs:
                P_.append((x_hra0 + xc, vys(zr, xc), z_hra0 + zr)); Nn.append(N[min(int(round(zr)), N.shape[0] - 1), min(int(round(xc)), N.shape[1] - 1)])
        nx_ = len(xs); T_ = []
        for a_ in range(len(zs) - 1):
            for b_ in range(nx_ - 1):
                v0 = base + a_ * nx_ + b_; v1 = v0 + 1; v2 = v0 + nx_; v3 = v2 + 1
                cx_ = xs[b_] + jm / 2; cz_ = zs[a_] + jm / 2
                if np.hypot(cx_ - cc, cz_ - rr) < dr: continue   # otvor šachty
                T_ += [(v0, v2, v1), (v1, v2, v3)]
        pos = np.concatenate([pos, np.array(P_, np.float32)]); nor = np.concatenate([nor, np.array(Nn, np.float32)])
        idx = np.concatenate([tri.ravel(), np.array(T_, np.uint32).ravel()]).astype(np.uint32)
        print("díra v terénu: %.1f, %.1f r %.2f (dlaždice %d,%d)" % (dx, dz, dr, r0 // D, c0 // D))
    return pos, nor, idx

out_hra = os.path.join(koren, "hra/dlazdice"); os.makedirs(out_hra, exist_ok=True)
D = int(T["dlazdice_m"])
nt_r, nt_c = (ny - 1) // D, (nx - 1) // D
seznam = []
for i in range(nt_r):
    for j in range(nt_c):
        meshes = []
        for li, L in enumerate(T["lod"]):
            k = int(L["krok_m"]); n = -(-D // k)   # ceil: dlaždice musí dojít až na D v každém LOD (250/16 dávalo 240 m)
            pos, nor, idx = sit(i * D, j * D, n, n, k, T["sukne_m"] + 1.5 * k)  # škvíra mezi LOD roste s krokem (snímek 01: světlé čáry)
            if li == 0: pos, nor, idx = dira(pos, nor, idx, i * D, j * D, n, k)
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
