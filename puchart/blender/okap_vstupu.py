"""Zvednutý okap nad vchody domů (docs/chyby.md 314; Míša 15. 11.: „udělej to, ať to vypadá dobře řemeslně a esteticky“).
Dum2 (omítnutý s doškovou valbou, Havran blender/ves_domy.py) má okap 0,65 m za stěnou a jen 1,69 m nad terénem – postava
(kapsle 1,75 m) jím nad vchodem projde hlavou. Doškař to řeší „obočím“ (eyebrow): nad otvorem se okap vyklene v plochém
oblouku vzhůru, okapní vrstva jde přes otvor v plné tloušťce, hlavní vrstvy se nad ním ztenčí a za otvorem vrátí; obočí
z roviny střechy skoro nevystupuje, sklon nad ním neklesne pod 45° (zdroje v pravidla/svet/mista.json okapy_vstupu.zdroj).
Tesařsky: konce krokví nad vchodem nesou zvednutou okapní latě jako „kočky“ (přiložené konce s mírnějším sklonem) –
krokve, latě a došek se zvednou spolu, nic nevisí a nic se neprostupuje.

Postup (data pravidla/svet/mista.json okapy_vstupu): pro každý dům ze seznamu a každé vnější dveře (<Dům>_Dvere_* na obvodové
stěně) změří nejnižší bod krytiny a krovu nad pásem dveří (+ okraj na každou stranu); je-li pod min_okap_m, posune vrcholy
krytiny a krovu svisle o dy = A · w(z) · g(x) · h(x, z):
  g – od líce dveří (|x| dveří) k okraji okapu hladký náběh (smoothstep), u stěny ~0 (zhlaví a stěna zůstanou zakryté),
  w – 1 v pásu dveří, mimo něj kosinový náběh nabeh_m (k valbě kratší, končí valba_odstup_m před nárožím),
  h – 0 na nároží valby (zvedá se jen podélná plocha střechy, valba zůstane rovná),
  A – tak, aby spodní hrana nad pásem byla cil_okap_m.
Pole nezávisí na y → svislá tloušťka doškového pláště, obruby (M_DoskyHrana) i krokví zůstane; normály a tečny se přepočítají
z Jacobiho matice posunu (n' = n − n_y ∇dy, t' = t + e_y (∇dy · t)), UV zůstanou (mírné natažení). Upraví se podrobná síť
<Dům>_Vnejsek i hrubý obal <Dům>_Daleko (z dálky stejný obrys); střední stupeň staví z výsledku blender/stredni_lod.py.

Úprava jde přímo v binárním glb (bez bpy): domy.glb vyvezl Godot s kolizemi OMI_physics_body/shape (<Dům>_Kol_*), Blender
je při importu/exportu ztratí. Z originálu build/zdroj_celky/domy.glb (ukládá nastroje/stavby_z_havrana.sh hned po vývozu
z Havrana) do hra/modely/stavby_h/domy.glb – opakované spuštění nic nezdvojí.
  python3 blender/okap_vstupu.py <K>     (nebo /opt/bl/bin/python – stačí numpy a scipy)"""
import sys, os, json, struct, math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

K = os.path.abspath(sys.argv[-1] if len(sys.argv) > 1 else ".")
C = json.load(open(os.path.join(K, "pravidla/svet/mista.json")))["okapy_vstupu"]
CT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def nacti(p):
    f = open(p, "rb").read()
    n = struct.unpack("<I", f[12:16])[0]; j = json.loads(f[20:20 + n])
    o = 20 + n; bl = struct.unpack("<I", f[o:o + 4])[0]
    return j, bytearray(f[o + 8:o + 8 + bl]), f[o + 8 + bl:]


def uloz(p, j, b, zbytek):
    js = json.dumps(j, separators=(",", ":"), ensure_ascii=False).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    b = bytes(b) + b"\0" * ((4 - len(b) % 4) % 4)
    j["buffers"][0]["byteLength"] = len(b)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(b) + len(zbytek))
    out += struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(b)) + b"BIN\0" + b + zbytek
    open(p, "wb").write(out)


def _misto(j, i):
    a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]; nc = NC[a["type"]]; dt = np.dtype(CT[a["componentType"]])
    return a, bv.get("byteOffset", 0) + a.get("byteOffset", 0), bv.get("byteStride", 0) or dt.itemsize * nc, nc, dt


def cti(j, b, i):
    a, off, st, nc, dt = _misto(j, i)
    return np.array([np.frombuffer(b, dtype=dt, count=nc, offset=off + k * st) for k in range(a["count"])]) if st != dt.itemsize * nc \
        else np.frombuffer(b, dtype=dt, count=a["count"] * nc, offset=off).reshape(a["count"], nc).copy()


def pis(j, b, i, data):
    a, off, st, nc, dt = _misto(j, i)
    d = np.ascontiguousarray(data.astype(dt))
    if st == dt.itemsize * nc: b[off:off + d.nbytes] = d.tobytes(); return
    for k in range(a["count"]): b[off + k * st:off + k * st + dt.itemsize * nc] = d[k].tobytes()


def smooth(t):
    t = np.clip(t, 0.0, 1.0); return t * t * (3 - 2 * t)


def kusy(P, I):
    """index souvislého kusu pro každý vrchol (trojúhelníky + vrcholy ve stejné poloze do 2 mm)"""
    n = len(P)
    _, inv = np.unique(np.round(P / 0.002).astype(np.int64), axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    r = np.concatenate([I[:, 0], I[:, 1], np.arange(n)]); c = np.concatenate([I[:, 1], I[:, 2], n + inv])
    g = coo_matrix((np.ones(len(r)), (r, c)), shape=(n + inv.max() + 1,) * 2)
    return connected_components(g, directed=False)[1][:n]


def pridej(j, b, data, minmax, indexy=False):
    """nový accessor s daty na konci bufferu (zarovnáno na 4 B)"""
    d = np.ascontiguousarray(data.astype(np.uint32 if indexy else np.float32))
    b.extend(b"\0" * ((4 - len(b) % 4) % 4)); off = len(b); b.extend(d.tobytes())
    j["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": d.nbytes, "target": 34963 if indexy else 34962})
    a = {"bufferView": len(j["bufferViews"]) - 1, "componentType": 5125 if indexy else 5126, "count": len(d),
         "type": "SCALAR" if indexy else {2: "VEC2", 3: "VEC3", 4: "VEC4"}[d.shape[1]]}
    if minmax: a["min"] = d.min(0).tolist(); a["max"] = d.max(0).tolist()
    j["accessors"].append(a); return len(j["accessors"]) - 1


def rez(A, I, sel, osa, roviny, oblast, delka):
    """rozřízne trojúhelníky vybraných vrcholů (jen v oblasti a jen delší než delka podél osy – lať se neřeže podélně)
    rovinami souřadnice osa = roviny[i] najednou: trojúhelník se rozdělí na pásy mezi sousedními rovinami (průnik konvexního
    trojúhelníku s pásem = body obvodu v pásu v pořadí obvodu), pás vějířem na trojúhelníky – počet roste lineárně s rovinami.
    Body řezu leží na původních hranách a sdílí se mezi sousedy (klíč hrana + rovina) → bez trhlin; atributy lineárně."""
    P = A["POSITION"]; d = P[:, osa]; roviny = np.sort(np.asarray(roviny))
    dm, dM = d[I].min(1), d[I].max(1)
    t_ = sel[I].all(1) & (np.ptp(d[I], 1) > delka) & oblast(P[I].mean(1)) & \
        (np.searchsorted(roviny, dM) - np.searchsorted(roviny, dm, side="right") > 0)
    if not t_.any(): return A, I, sel
    nove = {k: [] for k in A}; cache = {}; n0 = len(P)
    def bod(u, v, ri):
        k = (min(u, v), max(u, v), ri)
        if k not in cache:
            t = (roviny[ri] - d[u]) / (d[v] - d[u])
            for a_ in A: nove[a_].append(A[a_][u] + (A[a_][v] - A[a_][u]) * t)
            cache[k] = n0 + len(cache)
        return cache[k]
    tri = []
    for f in I[t_]:
        obvod = []   # (index vrcholu, souřadnice na ose)
        for r in range(3):
            u, v = int(f[r]), int(f[(r + 1) % 3]); obvod.append((u, d[u]))
            lo, hi = sorted((d[u], d[v]))
            ri_ = list(range(np.searchsorted(roviny, lo, side="right"), np.searchsorted(roviny, hi)))
            if d[v] < d[u]: ri_.reverse()
            obvod += [(bod(u, v, ri), roviny[ri]) for ri in ri_]
        lo, hi = d[f].min(), d[f].max()
        meze = [lo] + [c for c in roviny if lo < c < hi] + [hi]
        for c0, c1 in zip(meze[:-1], meze[1:]):
            pol = [q for q, c in obvod if c0 - 1e-9 <= c <= c1 + 1e-9]
            pol = [q for i_, q in enumerate(pol) if q != pol[i_ - 1]] if len(pol) > 1 else pol
            for i_ in range(1, len(pol) - 1): tri.append((pol[0], pol[i_], pol[i_ + 1]))
    A = {k: np.vstack([A[k], np.array(nove[k])]) for k in A}
    I = np.vstack([I[~t_], np.array(tri, dtype=np.int64)])
    return A, I, np.concatenate([sel, np.ones(len(cache), bool)])


src = os.path.join(K, C["vstup"]); dst = os.path.join(K, C["vystup"])
if not os.path.exists(src):
    sys.exit("OKAP_CHYBI originál %s (nastroje/stavby_z_havrana.sh ho uloží po vývozu domů z Havrana)" % src)
j, b, zbytek = nacti(src)
N = {n.get("name"): n for n in j["nodes"]}
MAT = [m.get("name", "") for m in j["materials"]]
upraveno = 0
for dum in C["domy"]:
    site = [N[dum + s] for s in C["site"] if dum + s in N]
    prim = [(p, n["name"]) for n in site for p in j["meshes"][n["mesh"]]["primitives"]]
    krytina = lambda m: any(k in m for k in C["krytina"])
    PK = np.concatenate([cti(j, b, p["attributes"]["POSITION"]) for p, _ in prim if krytina(MAT[p["material"]])])
    xe = float(np.abs(PK[:, 0]).max()); ze = float(np.abs(PK[:, 2]).max())   # okraj okapu (podélná strana) a valby / štítu
    dvere = []
    for jm, n in N.items():
        if not jm.startswith(dum + "_Dvere_") or "mesh" not in n: continue
        t = n.get("translation", [0, 0, 0]); a = j["accessors"][j["meshes"][n["mesh"]]["primitives"][0]["attributes"]["POSITION"]]
        if abs(t[0]) < C["vnejsi_od_x_m"]: continue   # vnitřní dveře (síň, komora)
        dvere.append((jm, abs(t[0]), np.sign(t[0]), t[2] + a["min"][2], t[2] + a["max"][2]))
    # díly, které se zvedají: krytina a krov (materiály), k tomu kusy celé za lícem dveří (čela krokví); ne zhlaví trámů a stěny
    data = []
    for p, uzel in prim:
        P = cti(j, b, p["attributes"]["POSITION"]); I = cti(j, b, p["indices"]).reshape(-1, 3).astype(np.int64)
        m = MAT[p["material"]]
        if krytina(m) or any(k in m for k in C["krov_materialy"]): sel = np.ones(len(P), bool)
        else:
            k = kusy(P, I); mn = np.full(k.max() + 1, 9e9); np.minimum.at(mn, k, np.abs(P[:, 0]))
            x_dv = min([d[1] for d in dvere], default=9e9)
            sel = mn[k] > x_dv + C["presah_od_dveri_m"]
        data.append((p, P, sel, I, uzel))
    # nejnižší bod zvedaných dílů nad pásem každých dveří → potřebné zvednutí
    pasy = []
    for jm, xd, s, z0, z1 in dvere:
        a0, a1 = z0 - C["okraj_m"], z1 + C["okraj_m"]
        ys = [P[sel & (s * P[:, 0] > xd + C["presah_od_dveri_m"]) & (P[:, 2] > a0) & (P[:, 2] < a1), 1] for _, P, sel, _, _ in data]
        ys = np.concatenate(ys); y = float(ys.min()) if len(ys) else 9e9
        if y >= C["min_okap_m"]:
            print("OKAP_OK %s %s spodní hrana nad vchodem %.2f m" % (dum, jm, y)); continue
        A = C["cil_okap_m"] - y
        # náběh: ke středu stěny nabeh_m, k valbě kratší (končí valba_odstup_m před nárožím)
        r0 = C["nabeh_m"] if a0 > 0 else max(0.2, min(C["nabeh_m"], ze - C["valba_odstup_m"] - abs(a0)))
        r1 = C["nabeh_m"] if a1 < 0 else max(0.2, min(C["nabeh_m"], ze - C["valba_odstup_m"] - abs(a1)))
        pasy.append((s, xd, a0, a1, r0, r1, A))
        print("OKAP_ZVEDNUT %s %s z %.2f…%.2f: spodní hrana %.2f → %.2f m (zvednutí %.2f, náběh %.2f/%.2f m)" % (dum, jm, a0, a1, y, C["cil_okap_m"], A, r0, r1))
    if not pasy: continue
    # sousední vchody na téže stěně blíž než spojit_do_m → jeden souvislý zvednutý okap (dva oblouky by mezi dveřmi
    # udělaly ostrý zub; doškař vede okapní vrstvu přes oba otvory jedním plochým obloukem)
    pasy.sort(key=lambda q: (q[0], q[2])); sp = [pasy[0]]
    for q in pasy[1:]:
        s0 = sp[-1]
        if q[0] == s0[0] and q[2] - s0[3] < C["spojit_do_m"]:
            sp[-1] = (s0[0], min(s0[1], q[1]), s0[2], max(s0[3], q[3]), s0[4], q[5], max(s0[6], q[6]))
            print("OKAP_SPOJENO %s z %.2f…%.2f (mezera %.2f m)" % (dum, s0[2], q[3], q[2] - s0[3]))
        else: sp.append(q)
    pasy = sp

    def pole(x, z):
        dy = np.zeros_like(x)
        for s, xd, a0, a1, r0, r1, A in pasy:
            g = smooth((s * x - xd) / (xe - xd))
            d0 = np.clip((a0 - z) / r0, 0, 1); d1 = np.clip((z - a1) / r1, 0, 1)
            w = np.where(z < a0, 0.5 * (1 + np.cos(np.pi * d0)), np.where(z > a1, 0.5 * (1 + np.cos(np.pi * d1)), 1.0))
            h = smooth(((ze - np.abs(z)) - (xe - s * x)) / C["valba_prechod_m"])   # 0 na nároží valby a za ním
            dy = np.maximum(dy, A * g * w * h * (s * x > xd))
        return dy

    e = 1e-3
    for p, P, sel, I, uzel in data:
        if not sel.any(): continue
        A_ = {k: cti(j, b, i).astype(np.float64) for k, i in p["attributes"].items() if k in ("POSITION", "NORMAL", "TANGENT", "TEXCOORD_0")}
        if len(A_) != len(p["attributes"]): sys.exit("OKAP neznámý atribut %s" % list(p["attributes"]))
        # dlouhé díly (latě, krokve, hrubý obal) mají vrcholy jen na koncích – rozřezat rovinami po krok_m v pásmu posunu,
        # aby se ohnuly po oblouku (krytina je hustá, ta se neřeže)
        rezat = uzel.endswith("_Daleko") or not krytina(MAT[p["material"]])
        if rezat:
            for s_, xd, a0, a1, r0, r1, A in pasy:
                obl = lambda q, s_=s_, xd=xd: s_ * q[:, 0] > xd
                A_, I, sel = rez(A_, I, sel, 2, np.arange(a0 - r0, a1 + r1, C["krok_z_m"]) + 0.0137, obl, C["krok_z_m"])
                A_, I, sel = rez(A_, I, sel, 0, s_ * (np.arange(xd, xe, C["krok_x_m"]) + 0.0071), obl, C["krok_x_m"])
        P = A_["POSITION"]; x, z = P[:, 0], P[:, 2]
        dy = pole(x, z) * sel
        if not (dy > 1e-5).any(): continue
        gx = (pole(x + e, z) - pole(x - e, z)) / (2 * e) * sel; gz = (pole(x, z + e) - pole(x, z - e)) / (2 * e) * sel
        P[:, 1] += dy
        if "NORMAL" in A_:
            Nn = A_["NORMAL"]; Nn[:, 0] -= Nn[:, 1] * gx; Nn[:, 2] -= Nn[:, 1] * gz
            Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-9)
        if "TANGENT" in A_:
            T = A_["TANGENT"]; T[:, 1] += gx * T[:, 0] + gz * T[:, 2]
            T[:, :3] /= np.maximum(np.linalg.norm(T[:, :3], axis=1, keepdims=True), 1e-9)
        if rezat:   # nový počet vrcholů → nové accessory na konci bufferu (původní data zůstanou nevyužitá)
            for k_, v_ in A_.items(): p["attributes"][k_] = pridej(j, b, v_, k_ == "POSITION")
            p["indices"] = pridej(j, b, I.reshape(-1).astype(np.uint32), False, True)
        else:
            for k_, v_ in A_.items(): pis(j, b, p["attributes"][k_], v_)
            a = j["accessors"][p["attributes"]["POSITION"]]; a["min"] = P.min(0).tolist(); a["max"] = P.max(0).tolist()
        upraveno += int((dy > 1e-5).sum())
uloz(dst, j, b, zbytek)
print("OKAP hotovo: posunuto %d vrcholů → %s" % (upraveno, dst))
