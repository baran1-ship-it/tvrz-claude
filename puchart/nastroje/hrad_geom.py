"""Společná geometrie dvojhradu pro terén (teren_upravy.py, numpy) i stavbu (blender/puchart_hrad.py): palác předního hradu
a jeho sklep se šíjí. Jediný zdroj čísel = pravidla/svet/hrad_puchart.json (A.budovy, A.sklep)."""
import numpy as np

def usek(jadro, i):
    j = np.array(jadro, float); a, b = j[i], j[(i + 1) % len(j)]; L = np.linalg.norm(b - a); d = (b - a) / L
    vn = np.array([-d[1], d[0]])
    if np.dot(j.mean(0) - (a + b) / 2, vn) < 0: vn = -vn
    return a, b, L, d, vn

def sklep(A):
    """Vnitřek sklepa (lokálně u podél paláce od V konce, v od jižní/hradební strany k nádvoří) a šíje před S zdí paláce.
    Vrací dict: o (počátek vnitřku), du, dv (jednotkové), Li, Wi, tl (zdi paláce), podl (podlaha paláce), y (podlaha sklepa),
    sije (u0, u1 schodů, v0, v1 výkopu), body() -> svět."""
    S = A["sklep"]; bd = next(b for b in A["budovy"] if b["id"] == S["budova"])
    a, b, L, d, vn = usek(A["jadro"], bd["usek"]); t = A["kurtina_tloustka"]
    o_ = t / 2 + bd.get("odsazeni", -1.0) + bd["hloubka"] / 2
    p0 = a + d * bd["od_m"] + vn * o_; tl = S["zdi_palace"]; h = bd["hloubka"]
    o = p0 + d * (tl / 2) - vn * (h / 2 - tl / 2)
    g = dict(o=o, du=d, dv=vn, Li=(bd["do_m"] - bd["od_m"]) - tl, Wi=h - tl, tl=tl, h=h, p0=p0, p1=a + d * bd["do_m"] + vn * o_,
             podl=S["podlaha_palace_y"], y=S["podlaha_y"], S=S)
    g["svet"] = lambda u, v: o + d * u + vn * v
    return g
