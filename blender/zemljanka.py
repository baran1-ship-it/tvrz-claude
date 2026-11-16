"""Zemljanky (Misa 16. 11.): chyse v lomu a u uhlire z domy.glb (ChyseKura, ChysePrkna) s jamou, dvema stupni dolu
a hlinenymi stenami oblozenymi kuly. Zaznam pravidla/svet/lokace.json zemljanky; postup prevzat z Puchartu
(vetev ccr-f2d32673-9fi7m5: nastroje/zajimava_modely.py jama_steny, nastroje/zajimava_mista.py diry v terenu).

Poradi stavby: teren (kraj.tiles vyrizne otvor po obrys jamy v Teren_zemljanky, rovina pod chysi kraj.MISTA) ->
stavby: tady jama, stupne, steny a kolize v souradnicich sveta (chysi samotnou stavi hra z domy.glb na vysce MISTA).
Vysku prahu (srovnany teren + lom_chyse.teren_pod_prahem_m) zapise export do svet.json zemljanky, hra chysi
postavi na ni (svet._domy_ramce, _chyse_na_sit). Hlidac: kontrola() - stupen nad hrac.json schod_m = chyba exportu."""
import json
import math
import os

from mathutils import Matrix, Vector

from lib import M, Part

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def _json(*cesta):
    with open(os.path.join(_ROOT, *cesta), encoding="utf-8") as f:
        return json.load(f)


_LOK = _json("pravidla", "svet", "lokace.json")
Z = _LOK.get("zemljanky", {})
VYSTUP = []          # polohy chysi pro svet.json zemljanky (export_game.py)


def mista():
    """[(k, typ, x, z, smer)] - stred z mista nebo z lom_chyse.mista[i]."""
    out = []
    for m in Z.get("mista", []):
        if "stred" in m:
            x, z = m["stred"]
        else:
            x, z = _LOK["lom_chyse"]["mista"][m["lom_chyse"]]
        out.append((int(m["k"]), m["typ"], float(x), float(z), float(m["smer"])))
    return out


def theta(smer):
    """Natoceni modelu kolem svisle osy jako ve hre (svet._domy: Basis(UP, PI/2 - smer))."""
    return math.pi / 2.0 - smer


def lok_svet(x, z, smer, lx, lz):
    """Mistni (x, z) chyse -> svet (Godot Basis(UP, th): x' = x cos + z sin, z' = -x sin + z cos)."""
    th = theta(smer)
    c, s = math.cos(th), math.sin(th)
    return x + lx * c + lz * s, z - lx * s + lz * c


def jama_poly(m):
    """Obrys jamy ve svete (4 rohy) pro misto (k, typ, x, z, smer)."""
    k, typ, x, z, smer = m
    x0, x1, z0, z1 = Z["typy"][typ]["jama"]
    return [lok_svet(x, z, smer, a, b) for a, b in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]


def v_jame(px, pz, poly):
    """Bod uvnitr konvexniho ctyruhelniku (rohy v poradi)."""
    zn = 0
    for i in range(4):
        ax, az = poly[i]
        bx, bz = poly[(i + 1) % 4]
        c = (bx - ax) * (pz - az) - (bz - az) * (px - ax)
        if c != 0.0:
            s = 1 if c > 0 else -1
            if zn and s != zn:
                return False
            zn = s
    return True


def kontrola():
    """Stupen (prah -> 1. stupen -> 2. stupen -> dno) nejvys hrac.json schod_m[0]; chyba = vyjimka exportu."""
    sm = float(_json("pravidla", "svet", "hrac.json")["schod_m"][0])
    h = float(Z["hloubka_m"]) / (int(Z["schody"]["pocet"]) + 1)
    if h > sm:
        raise ValueError("zemljanky: stupen %.2f m nad hrac.json schod_m %.2f" % (h, sm))
    return h


def _blok(P, H, xs, zs, vys, yb, mat):
    """Souvisly blok hliny: bunka (ix, iz) ma horni plochu ve vysce vys[iz][ix], mezi bunkami svisle steny, po obvodu
    steny dolu na yb, dno. Vrcholy sdilene podle polohy (jeden kus site)."""
    idx, V, F = {}, [], []

    def v(x, y, z):
        k = (round(x, 4), round(y, 4), round(z, 4))
        if k not in idx:
            idx[k] = len(V)
            V.append(k)
        return idx[k]
    nx, nz = len(xs) - 1, len(zs) - 1

    def hh(ix, iz):
        return vys[iz][ix] if 0 <= ix < nx and 0 <= iz < nz else yb
    for iz in range(nz):
        for ix in range(nx):
            a, b, c, d = xs[ix], xs[ix + 1], zs[iz], zs[iz + 1]
            y = vys[iz][ix]
            F.append((v(a, y, c), v(a, y, d), v(b, y, d), v(b, y, c)))                 # horni plocha
            F.append((v(a, yb, c), v(b, yb, c), v(b, yb, d), v(a, yb, d)))             # dno
            # stena k sousedovi, je-li soused nizsi (u kraje soused = yb): +x, -x, +z, -z
            for (ox, oz, p0, p1) in ((1, 0, (b, d), (b, c)), (-1, 0, (a, c), (a, d)), (0, 1, (a, d), (b, d)), (0, -1, (b, c), (a, c))):
                y2 = hh(ix + ox, iz + oz)
                if y2 < y - 1e-6:
                    F.append((v(p0[0], y2, p0[1]), v(p1[0], y2, p1[1]), v(p1[0], y, p1[1]), v(p0[0], y, p0[1])))
    P.mesh([H @ Vector(p) for p in V], F, mat)


def build(coll, land_fn, teren_pod_prahem_m):
    """Jama kazde zemljanky (Part Zemljanka_<k>) a seznam poloh chysi pro svet.json: [{k, typ, p, smer}]."""
    if not Z:
        return []
    h = kontrola()
    n = int(Z["schody"]["pocet"])
    dz = float(Z["schody"]["hloubka_m"])
    sw = float(Z["schody"]["sirka_m"]) / 2.0
    T = float(Z["stena_m"])
    kp = Z["kuly"]
    vystup = []
    for m in mista():
        k, typ, x, z, smer = m
        t = Z["typy"][typ]
        prah = float(t["prah_y"])
        yf = prah - float(Z["hloubka_m"])
        yt = prah + 0.02
        x0, x1, z0, z1 = t["jama"]
        zs = z1 - n * dz                                   # zacatek stupnu (strana do jamy)
        y0 = land_fn(x, z) + teren_pod_prahem_m - prah     # pocatek modelu chyse: prah na srovnanem terenu
        H = M((x, y0, z), basis=Matrix.Rotation(theta(smer), 3, "Y"))
        P = Part("Zemljanka_%d" % k)

        def kv(a, b, mat, collide=True):
            lo = Vector((min(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2])))
            hi = Vector((max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2])))
            P.box(H @ Matrix.Translation((lo + hi) * 0.5), tuple(hi - lo), mat, collide=collide)
        # dno, stupne a hlina po stranach stupnu az k prahu = jeden souvisly kus hliny (vyskove pole po bunkach, svisle
        # steny mezi nimi; test smyslu krtinec 16. 11.: samostatne kvadry stupnu a lavic byly „kupky hliny“), kolize po bunkach
        xs = [x0, -sw, sw, x1]
        zr = [z0, zs] + [z1 - (n - 1 - i) * dz for i in range(n)]
        vys = [[yf, yf, yf]] + [[yt, prah - (n - i) * h, yt] for i in range(n)]
        _blok(P, H, xs, zr, vys, yf - 0.25, "hlina_hra")
        for iz in range(len(zr) - 1):
            for ix in range(3):
                lo = Vector((xs[ix], yf - 0.3, zr[iz]))
                hi = Vector((xs[ix + 1], vys[iz][ix], zr[iz + 1]))
                P.cols.append((H @ Matrix.Translation((lo + hi) * 0.5), tuple(hi - lo)))
        for i in range(n):
            ytop = prah - (i + 1) * h
            za = z1 - (i + 1) * dz
            kv((-sw, ytop - 0.08, za), (sw, ytop + 0.01, za + 0.09), "dub", collide=False)   # hrana stupne z kulatiny
        # steny jamy: lic na obrysu, tloustka T za licem (kryje zubaty okraj otvoru v terenu)
        kv((x0 - T, yf, z0 - T), (x0, yt, z1), "hlina_hra")
        kv((x1, yf, z0 - T), (x1 + T, yt, z1), "hlina_hra")
        kv((x0 - T, yf, z0 - T), (x1 + T, yt, z0), "hlina_hra")
        # oblozeni z kulu (pul kulu ve stene)
        r = float(kp["prumer_m"]) / 2.0
        ykt = yt + float(kp["nad_prah_m"])
        zk = z0 + 0.15
        while zk <= zs + 0.01:
            for xk in (x0, x1):
                kv((xk - r, yf, zk - r), (xk + r, ykt, zk + r), "kura", collide=False)
            zk += float(kp["rozestup_m"])
        xk = x0 + 0.16
        while xk < x1:
            kv((xk - r, yf, z0 - r), (xk + r, ykt, z0 + r), "kura", collide=False)
            xk += float(kp["rozestup_m"])
        P.commit(coll)
        vystup.append({"k": k, "typ": typ, "p": [round(x, 3), round(y0, 3), round(z, 3)], "smer": smer,
                       "podlaha_y": round(yf, 3), "prah_y": prah})
        print("zemljanka %d %s: prah %.2f, dno %.2f, stupen %.2f m" % (k, typ, y0 + prah, y0 + yf, h))
    VYSTUP[:] = vystup
    return vystup
