"""Hladina malych toku pod brehy (Misa 0.99 „kanal vykopany bagrem“: na svahu lezel tok na nasypu - hladina linearne
mezi body planovace, teren napric klesal a kraj.voda_tvar dosypal spodni breh az 1,7 m nad okoli).
Pravidlo (voda.json toky_tvar breh_nad_hladinou_min_m): teren bez vody na obou brezich (sirka/2 + breh_sirka_m od osy)
je aspon o tolik nad hladinou -> hladina se snizi (zarez do svahu jako skutecny potok, ktery si koryto vymlel).
Hladina po proudu jen klesa; pevne body (body toku v dilu mlyna a konec toku v nadrzi) se nemeni a hladina nad nimi
nesmi klesnout pod jejich uroven - tam zustane nasyp jako pojistka (vypis, test smyslu toky_nasyp).
  /opt/bl/bin/python tools/krok_b/toky_hladina.py          vypis
  /opt/bl/bin/python tools/krok_b/toky_hladina.py zapis    prepise osa_xzy y ve voda.json"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "blender"))
import fort  # noqa: E402
import kraj  # noqa: E402

# teren bez koryt malych toku, ale s rybniky a hrazemi (kraj.voda_tvar bez tok_near) - TVRZ_BEZ_VODY_TVAR vypnul i
# misu rybnika a hladina potoka u lesniho rybnika zustala 0,6 m nad terenem (0.99 export, tvrz_potok)
_tok_near = kraj.tok_near
kraj.tok_near = lambda x, z: None

VP = os.path.join(ROOT, "pravidla", "svet", "voda.json")
V = json.load(open(VP))
TT = V["toky_tvar"]
MIN = TT["breh_nad_hladinou_min_m"]
zapis = sys.argv[1:2] == ["zapis"]
for tj, t in zip(V["toky"], kraj.TOKY):
    o = tj["osa_xzy"]
    n = len(o)
    pw = tj["sirka_m"] / 2.0
    cil = []
    pevny = []
    for i, (x, z, y) in enumerate(o):
        a, b = o[max(0, i - 1)], o[min(n - 1, i + 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        nx, nz = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        r = (0.0, x, z, float(min(i, n - 2)))
        # cely pas brehu (od kraje vody po hranu brehu) - jen hrana nestacila: niva u vody nizsi nez hrana, nasyp zustal
        # (0.99 export: teren 0,9-2,4 m od osy presne na hladina + breh_m)
        hb = [fort.land(x, z) + MIN - TT["breh_m"]]      # v ose aspon breh_m nad hladinou (tok zarizly, ne na hrbetu)
        for sg in (-1, 1):
            bw = t.breh_sirka(r, x + nx * sg, z + nz * sg)
            for f in (0.0, 0.33, 0.66, 1.0):
                s = pw + bw * f
                hb.append(fort.land(x + nx * sg * s, z + nz * sg * s))
            # za hranou brehu (do 4 m) teren aspon v urovni hladiny - tok neni na hrbetu svahu (test toky_nasyp)
            for s in (pw + bw + 2.0, pw + bw + 4.0):
                hb.append(fort.land(x + nx * sg * s, z + nz * sg * s) + MIN - 0.05)
        cil.append(min(hb) - MIN)
        # okraj lesniho rybnika podle smeru (kraj.ryb_polomer, zalivy) - tok konci na hrane vody (toky_meandry)
        nadrz = [rr for rr in kraj.RYBNIKY if math.hypot(x - rr["stred"][0], z - rr["stred"][1]) <
                 (kraj.ryb_polomer(rr, x, z) if "polomer_m" in rr else rr.get("voda_polomer_m", 0.0)) + 3.0]
        # vtok do rybnika: hladina toku = hladina rybnika (+2 cm proud) - driv puvodni hodnota 0,46 m nad rybnikem
        pevny.append(kraj.v_dilu_mlyna(x, z) or (bool(nadrz) and i > n // 2))
        if nadrz and i > n // 2:
            o[i][2] = min(o[i][2], nadrz[0]["hladina_y"] + 0.02)
    puv = [p[2] for p in o]
    nove = [min(puv[i], cil[i]) for i in range(n)]
    for i in range(1, n):                        # po proudu jen klesa
        nove[i] = min(nove[i], nove[i - 1])
    for i in range(n):
        if pevny[i]:
            nove[i] = puv[i]
    # nad pevnym bodem hladina nesmi byt nize nez on (voda by tekla do kopce)
    podlaha = -1e9
    for i in range(n - 1, -1, -1):
        if pevny[i]:
            podlaha = max(podlaha, puv[i])
        nove[i] = max(nove[i], podlaha)
    nasyp = [i for i in range(n) if nove[i] > cil[i] + 1e-3]
    zarez = max(puv[i] - nove[i] for i in range(n))
    print("%s: %d bodu, snizeno %d (nejvic %.2f m), nasyp zustava %d bodu %s" % (
        t.id, n, sum(1 for i in range(n) if nove[i] < puv[i] - 1e-3), zarez, len(nasyp),
        "" if not nasyp else "(%d-%d, nejvic %.2f m)" % (nasyp[0], nasyp[-1], max(nove[i] - cil[i] for i in nasyp))))
    if nasyp and "-v" in sys.argv:
        print("   ", [(i, round(nove[i] - cil[i], 2), pevny[i], [round(c) for c in o[i][:2]]) for i in nasyp])
    if zapis:
        for i in range(n):
            o[i][2] = round(nove[i], 3)
if zapis:
    txt = json.dumps(V, ensure_ascii=False, indent=1)
    open(VP, "w").write(txt)
    print("zapsano", VP)
