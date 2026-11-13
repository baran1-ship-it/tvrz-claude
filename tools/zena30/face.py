"""Úprava obličeje: měkké deformace (symetrické v X), aplikované na tělo, oči i obočí."""
import numpy as np
from mathutils import Vector
# (střed x,y,z), poloměr, posun (dx,dy,dz) nebo ("scale", f)
OPS = [
    # nos: menší špička, užší křídla, kratší
    ((0.0, -0.112, 1.615), 0.022, (0, 0.0045, 0.0015)),
    ((0.016, -0.097, 1.608), 0.016, (-0.0045, 0.0015, 0.0005)),
    ((0.0, -0.100, 1.640), 0.016, (0, 0.0015, 0)),
    # čelist a brada: užší, jemnější
    ((0.060, -0.030, 1.550), 0.055, (-0.0065, 0, 0.003)),
    ((0.0, -0.082, 1.535), 0.030, (0, 0.003, 0.006)),
    ((0.0, -0.06, 1.545), 0.045, (0, 0, 0.003)),
    ((0.022, -0.075, 1.537), 0.018, (-0.002, 0.001, 0.001)),
    # tváře plnější, lícní kosti mírně výš
    ((0.048, -0.074, 1.600), 0.026, (0.0015, -0.0045, 0.001)),
    # rty: plnější horní ret, koutky mírně nahoru
    ((0.0, -0.093, 1.584), 0.011, (0, -0.0025, 0.0005)),
    ((0.0, -0.090, 1.573), 0.011, (0, -0.0020, 0)),
    ((0.022, -0.080, 1.578), 0.008, (0, 0, 0.0012)),
    # oči o kus větší (oblast kolem středu oka)
    ((0.0345, -0.063, 1.656), 0.018, ("scale", 1.04)),
    # čelo: hladší, menší nadočnicový oblouk
]
def falloff(d, r):
    t = np.clip(d / r, 0, 1)
    return (1 - t * t) ** 2

def deform(V):
    V = V.copy(); orig = V.copy()
    for c, r, op in OPS:
        c = np.array(c, float)
        cs = [c] if abs(c[0]) < 1e-6 else [c, c * np.array([-1, 1, 1])]
        for cc in cs:
            d = np.linalg.norm(orig - cc, axis=1); w = falloff(d, r)
            if op[0] == "scale":
                V += (orig - cc) * (op[1] - 1) * w[:, None]
            else:
                dv = np.array(op, float)
                if cc[0] < 0: dv[0] = -dv[0]
                V += dv * w[:, None]
    return V

def apply(obj):
    mw = obj.matrix_world; mi = mw.inverted()
    V = np.array([mw @ v.co for v in obj.data.vertices])
    N = deform(V)
    for v, p in zip(obj.data.vertices, N): v.co = mi @ Vector(p)
    # i tvarové klíče, pokud jsou
    if obj.data.shape_keys:
        for kb in obj.data.shape_keys.key_blocks:
            K = np.array([mw @ d.co for d in kb.data]); K2 = deform(K)
            for d, p in zip(kb.data, K2): d.co = mi @ Vector(p)
