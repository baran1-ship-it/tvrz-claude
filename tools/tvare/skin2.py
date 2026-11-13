"""Pleť 512 px jen barvou: tón, opálení, ruměnec, kruhy pod očima, vrásky (čelo, vějíře, nosoretní rýha, krk),
strniště, pihy, vlasy pod čepicí. Vše počítané z mapy 3D pozic texelů (vzory sedí na obličej, ne na UV)."""
import numpy as np, math
from PIL import Image, ImageFilter

def posmap(obj, S):
    me = obj.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
    mw = obj.matrix_world
    VP = np.array([mw @ v.co for v in me.vertices])
    P = np.zeros((S, S, 3)); M = np.zeros((S, S), bool)
    for t in me.loop_triangles:
        T = np.array([uv[l].uv for l in t.loops]) * S
        A = VP[list(t.vertices)]
        x0, y0 = np.floor(T.min(0)).astype(int); x1, y1 = np.ceil(T.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax, ay), (bx, by), (cx, cy) = T
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: continue
        l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den; l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den; l3 = 1 - l1 - l2
        m = (l1 >= -0.05) & (l2 >= -0.05) & (l3 >= -0.05)
        p = l1[..., None] * A[0] + l2[..., None] * A[1] + l3[..., None] * A[2]
        yy = (S - 1 - (ys[m] - 0.5)).astype(int); xx = (xs[m] - 0.5).astype(int)
        P[yy, xx] = p[m]; M[yy, xx] = True
    # rozšířit okraje ostrovů (aby filtry nebraly nulu)
    for _ in range(3):
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            Ps = np.roll(np.roll(P, dy, 0), dx, 1); Ms = np.roll(np.roll(M, dy, 0), dx, 1)
            add = Ms & ~M; P[add] = Ps[add]; M |= add
    return P, M

def _sm(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def blur(a, r):
    if a.ndim == 2:
        return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(float) / 255
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(float) / 255

def make(src_path, P, M, L, sp, hair_fn=None, beard_fn=None, S=512, rng=None):
    rng = rng or np.random.default_rng(0)
    src = Image.open(src_path).convert("RGB").resize((S, S), Image.LANCZOS)
    img = np.asarray(src).astype(float) / 255
    X, Y, Z = P[..., 0], P[..., 1], P[..., 2]; AX = np.abs(X)
    zE = float(L["eye"][2]); zN = float(L["nose"][2]); zC = float(L["chin"][2]); yN = float(L["nose"][1]); ex = L["ex"]
    zM = zN + (zC - zN) * 0.42
    face = (Z > zC - 0.06) & (Y < yN + 0.10) & (Z < zE + 0.11)
    skin = blur(img, 10)
    det = img / np.maximum(blur(img, 3), 1e-3)
    # pryč s líčením kolem očí (ženský základ)
    de = np.sqrt(((AX - ex) / 0.03) ** 2 + ((Z - zE) / 0.02) ** 2)
    eyem = np.clip(1 - de, 0, 1) ** 1.2 * (Y < yN + 0.07) * sp.get("odlicit", 1.0)
    img = img * (1 - 0.75 * eyem[..., None]) + np.clip(skin * det ** 0.6, 0, 1) * 0.75 * eyem[..., None]
    # tón pleti
    img = img * np.array(sp.get("ton", [1, 1, 1]))
    # opálení (venkovní práce): víc obličej, krk, ruce
    tan = sp.get("opaleni", 0.0)
    if tan:
        tc = np.array([0.86, 0.72, 0.6])
        img = img * (1 - 0.35 * tan) + img * tc * 0.35 * tan
        img = img * (1 - 0.12 * tan * face[..., None])
    # ruměnec (výheň, krčma) – tváře a nos
    ru = sp.get("rumenec", 0.0)
    if ru:
        m = np.clip(1 - np.sqrt(((AX - 0.045) / 0.03) ** 2 + ((Z - (zN - 0.004)) / 0.022) ** 2), 0, 1) + \
            np.clip(1 - np.sqrt((AX / 0.015) ** 2 + ((Z - zN) / 0.015) ** 2), 0, 1) * 0.7
        m = blur(m * (Y < yN + 0.06), 2) * ru
        img = img + m[..., None] * np.array([0.10, -0.03, -0.03])
    # kruhy pod očima
    kr = sp.get("kruhy", 0.0)
    if kr:
        m = np.clip(1 - np.sqrt(((AX - ex * 1.02) / 0.022) ** 2 + ((Z - (zE - 0.014)) / 0.008) ** 2), 0, 1) * (Y < yN + 0.07)
        m = blur(m, 1.5) * kr
        img = img * (1 - m[..., None] * np.array([0.22, 0.26, 0.18]))
    # vrásky
    vek = sp.get("vek", 0.0)
    if vek > 0.05:
        n1 = rng.random((S, S)); n1 = blur(n1, 1.2)
        lines = np.zeros((S, S))
        # čelo: vodorovné vlnky
        fz = (Z - (zE + 0.035)) / 0.0085 + 0.6 * np.sin(X * 60)
        fl = np.clip(1 - np.abs(fz - np.round(fz)) / 0.13, 0, 1)
        fore = _sm(Z, zE + 0.03, zE + 0.036) * (1 - _sm(Z, zE + 0.068, zE + 0.08)) * (AX < 0.055) * (Y < yN + 0.08)
        lines += fl * fore * (0.6 + 0.6 * n1)
        # mezi obočím svislé
        gz = np.clip(1 - np.abs(AX - 0.007) / 0.0016, 0, 1) * _sm(Z, zE + 0.005, zE + 0.012) * (1 - _sm(Z, zE + 0.03, zE + 0.04)) * (Y < yN + 0.05)
        lines += gz * 0.8
        # vějíře u očí
        dx = AX - (ex + 0.025); dz = Z - zE
        ang = np.arctan2(dz, dx); rad = np.hypot(dx, dz)
        fan = np.clip(1 - np.abs(((ang + 0.6) / 0.33) - np.round((ang + 0.6) / 0.33)) / 0.18, 0, 1) * _sm(rad, 0.004, 0.008) * (1 - _sm(rad, 0.018, 0.026)) * (np.abs(ang) < 0.9) * (Y < yN + 0.08)
        lines += fan * 0.9
        # nosoretní rýha (od křídla nosu ke koutku)
        t = np.clip((zN - 0.004 - Z) / ((zN - 0.004) - (zM - 0.012)), 0, 1)
        cx = 0.019 + t * 0.012 + np.sin(t * math.pi) * 0.004
        nl = np.clip(1 - np.abs(AX - cx) / 0.0022, 0, 1) * (Z < zN - 0.002) * (Z > zM - 0.014) * (Y < yN + 0.06)
        lines += nl * 1.3
        # koutky dolů
        ml = np.clip(1 - np.hypot(AX - 0.03, (Z - (zM - 0.006)) * 0.6) / 0.003, 0, 1) * (Y < yN + 0.06)
        lines += ml * 0.8
        # krk
        nk = (Z - (zC - 0.05)) / 0.012
        lines += np.clip(1 - np.abs(nk - np.round(nk)) / 0.1, 0, 1) * (Z < zC - 0.02) * (Z > zC - 0.11) * (AX < 0.05) * (Y < yN + 0.08) * 0.6
        lines = blur(np.clip(lines, 0, 1.5) / 1.5, 0.6)
        img = img * (1 - lines[..., None] * 0.42 * vek * np.array([1, 1.08, 1.12]))
        # stařecké skvrny + bledší, méně sytá pleť
        if vek > 0.5:
            sp_ = (blur(rng.random((S, S)), 1.5) > 0.62) * face * (vek - 0.5) * 0.25
            img = img * (1 - sp_[..., None] * np.array([0.3, 0.4, 0.55]))
        lum = img.mean(2, keepdims=True); img = lum + (img - lum) * (1 - 0.25 * vek)
    # pihy
    ph = sp.get("pihy", 0.0)
    if ph:
        m = (rng.random((S, S)) > 0.965) * np.clip(1 - np.sqrt((AX / 0.06) ** 2 + ((Z - zN) / 0.03) ** 2), 0, 1) * (Y < yN + 0.06)
        img = img * (1 - blur(m.astype(float), 0.5)[..., None] * ph * np.array([0.25, 0.35, 0.45]))
    # strniště a podklad vousů
    hc = np.array(sp.get("vlasy_barva", [0.1, 0.07, 0.05]))
    st = sp.get("strniste", 0.0)
    if st and beard_fn is not None:
        bf = np.vectorize(lambda x, y, z: beard_fn((x, y, z)), otypes=[float])(X[::2, ::2], Y[::2, ::2], Z[::2, ::2])
        bf = np.asarray(Image.fromarray(((np.clip(bf / 0.01, -1, 1) + 1) * 127.5).astype(np.uint8)).resize((S, S), Image.BILINEAR)).astype(float) / 127.5 - 1
        m = blur(np.clip(bf + 0.3, 0, 1), 2) * M * face
        dots = blur(rng.random((S, S)), 0.5)
        img = img * (1 - m[..., None] * st * (0.55 + 0.45 * dots[..., None])) + hc * m[..., None] * st * 0.5
    # vlasy pod čepicí
    if hair_fn is not None:
        hf = np.vectorize(lambda x, y, z: hair_fn((x, y, z)), otypes=[float])(X[::2, ::2], Y[::2, ::2], Z[::2, ::2])
        hf = np.asarray(Image.fromarray(((np.clip(hf / 0.01, -1, 1) + 1) * 127.5).astype(np.uint8)).resize((S, S), Image.BILINEAR)).astype(float) / 127.5 - 1
        m = blur(np.clip(hf * 1.5 + 0.2, 0, 1), 1.5) * (Z > zE - 0.15)
        img = img * (1 - m[..., None]) + hc * 0.8 * m[..., None]
    return np.clip(img, 0, 1)
