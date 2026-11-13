"""Tváře: posuvníky (-1..1) -> měkké posuny sítě (OPS) vůči landmarkům. Síť se nemění, jen tvar.
OPS = [(střed x,y,z), poloměr, (dx,dy,dz) nebo ("scale", f)] – stejný formát jako zena30/face.py (symetrické v X)."""
import numpy as np

SLIDERS = ["nos_delka", "nos_spicka", "nos_sirka", "nos_hrbet", "nos_hacek", "celist", "brada_delka", "brada_vpred",
           "brada_sirka", "licni_kosti", "tvare_plnost", "nadocnice", "oci", "rty", "usta_sirka", "oboci_vyska",
           "obliceji_delka", "usi", "vek_pokles", "vaha", "lebka_sirka", "nos_kratky_pres"]

def _surf_y(V, x, z, r=0.012):
    m = (np.abs(V[:, 0] - x) < r) & (np.abs(V[:, 2] - z) < r)
    if not m.any(): m = np.argsort(np.abs(V[:, 0] - x) + np.abs(V[:, 2] - z))[:5]
    return float(V[m, 1].min())

def build_ops(L, s):
    """L = landmarks, s = dict posuvníků. Vrací OPS v absolutních souřadnicích."""
    V = L["V"]; zE, zN, zC = float(L["eye"][2]), float(L["nose"][2]), float(L["chin"][2]); ex = L["ex"]
    zM = zN + (zC - zN) * 0.42              # ústa
    g = lambda k: float(s.get(k, 0.0))
    ops = []
    def add(x, z, r, d, dy_in=0.0):
        y = _surf_y(V, x, z) + dy_in
        ops.append(((x, y, z), r, d))
    # nos
    add(0, zN, 0.020, (0, -0.005 * g("nos_spicka"), -0.004 * g("nos_delka")))
    add(0.016, zN - 0.006, 0.015, (0.004 * g("nos_sirka"), 0, 0))
    add(0, (zE + zN) / 2, 0.016, (0, -0.004 * g("nos_hrbet"), 0), 0.004)
    add(0, zN + 0.004, 0.012, (0, -0.002 * g("nos_hacek"), -0.004 * g("nos_hacek")))
    add(0, zN - 0.010, 0.012, (0, 0, 0.003 * g("nos_kratky_pres")))
    # čelist, brada
    add(0.060, zC + 0.012, 0.050, (0.008 * g("celist") + 0.004 * g("vaha"), 0, 0.002 * g("celist")), 0.03)
    add(0, zC, 0.028, (0, -0.002 * g("brada_vpred"), -0.006 * g("brada_delka")))
    add(0, zC - 0.004, 0.024, (0, -0.005 * g("brada_vpred"), 0))
    add(0.022, zC + 0.002, 0.018, (0.004 * g("brada_sirka"), 0, 0))
    # lícní kosti, tváře
    add(0.050, zN + 0.012, 0.024, (0.005 * g("licni_kosti"), -0.002 * g("licni_kosti"), 0.002 * g("licni_kosti")))
    add(0.046, zN - 0.012, 0.026, (0.003 * g("tvare_plnost") + 0.004 * g("vaha"), -0.004 * g("tvare_plnost") - 0.002 * g("vaha"), -0.003 * g("vek_pokles")))
    # nadočnicové oblouky, obočí, oči
    add(0.032, zE + 0.022, 0.022, (0, -0.004 * g("nadocnice"), 0))
    add(0.034, zE + 0.026, 0.018, (0, 0, 0.003 * g("oboci_vyska")))
    ops.append(((ex, float(L["eye"][1]), zE), 0.019, ("scale", 1 + 0.06 * g("oci"))))
    # rty, ústa
    add(0, zM + 0.005, 0.011, (0, -0.0025 * g("rty"), 0.0006 * g("rty")))
    add(0, zM - 0.005, 0.011, (0, -0.002 * g("rty"), 0))
    add(0.022, zM, 0.010, (0.003 * g("usta_sirka"), 0, -0.0015 * g("vek_pokles")))
    # délka obličeje (dolní třetina)
    add(0, zC + 0.02, 0.06, (0, 0, -0.006 * g("obliceji_delka")), 0.02)
    # uši, lebka
    add(0.080, zE - 0.01, 0.030, (0.004 * g("usi"), 0.002 * g("usi"), 0), 0.08)
    add(0.075, zE + 0.05, 0.06, (0.005 * g("lebka_sirka"), 0, 0), 0.06)
    # stárnutí: povolené líce u čelisti (lalůčky), propadlé spánky
    add(0.045, zC + 0.010, 0.022, (0.002 * g("vek_pokles"), -0.001 * g("vek_pokles"), -0.004 * g("vek_pokles")))
    add(0.062, zE + 0.012, 0.018, (-0.002 * g("vek_pokles"), 0, 0), 0.03)
    # krk/podbradek při váze
    add(0, zC - 0.025, 0.035, (0, -0.008 * g("vaha"), 0), 0.03)
    return [o for o in ops if not (isinstance(o[2], tuple) and o[2][0] != "scale" and max(abs(c) for c in o[2]) < 1e-6)]

def falloff(d, r):
    t = np.clip(d / r, 0, 1); return (1 - t * t) ** 2

def deform(P, OPS):
    P = np.asarray(P, float); out = P.copy()
    for c, r, op in OPS:
        c = np.array(c, float)
        cs = [c] if abs(c[0]) < 1e-6 else [c, c * np.array([-1, 1, 1])]
        for cc in cs:
            w = falloff(np.linalg.norm(P - cc, axis=1), r)
            if op[0] == "scale": out += (P - cc) * (op[1] - 1) * w[:, None]
            else:
                dv = np.array(op, float)
                if cc[0] < 0: dv[0] = -dv[0]
                out += dv * w[:, None]
    return out

def apply(obj, OPS):
    from mathutils import Vector
    mw = obj.matrix_world; mi = mw.inverted()
    P = np.array([mw @ v.co for v in obj.data.vertices]); N = deform(P, OPS)
    for v, p in zip(obj.data.vertices, N): v.co = mi @ Vector(p)
