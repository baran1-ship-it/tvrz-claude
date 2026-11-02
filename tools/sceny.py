#!/usr/bin/env python3
"""Sceny podle skutecne viditelnosti (Misa 2. 11. „Havran: inteligentni tvorba scen“, docs/rozpracovane/zadani_sceny_2_11.md).

Vstup: build/vyhledy.json z tools/mapa_vyhledu.py --max 1500 (body cest a mrizky; obzor v 16 smerech = nejvzdalenejsi
viditelny bod nad blizsimi prekazkami: teren, stavby, koruny). Vystup: pravidla/svet/sceny.json - mrizka (krok_m) s dohledem kazde bunky a typem sceny:
  uzavrena   (A: les, ulicka, udoli - dohled ve vetsine smeru kratky),
  polootevrena (B: okraj lesa, naves, louka mezi remizky),
  panorama   (C: hreben, vyhlidka - dlouhy dohled; chranene vyhledy z lokace.json kompozice.vyhledy vzdy C).
Dohled bunky = kvantil `kvantil` dohledu po smerech z bodu v okoli (nejvetsi z bodu do `okoli_m`, at prechod mezi
scenami zacne drive nez hrac vyjde z lesa). Hra (scripts/sceny.gd) z neho bere hranici kresleni (kamera far) plynule
a s hysterezi. Pravidla a cisla v pravidla/svet/sceny.json "pravidla" (tento skript je jen pocita).
  python3 tools/mapa_vyhledu.py --krok 50 --max 1500 && python3 tools/sceny.py"""
import json
import math
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIL = os.path.join(ROOT, "pravidla", "svet", "sceny.json")
VYCHOZI = {
    "krok_m": 25.0,
    "okoli_m": 90.0,
    "kvantil": 0.9,
    "uzavrena_do_m": 180.0,
    "panorama_od_m": 600.0,
    "_popis": "krok_m mrizka scen; okoli_m: dohled bunky = nejvetsi z bodu mapy vyhledu do teto vzdalenosti (predstih "
              "a hystereze v prostoru); kvantil: dohled bodu = kvantil pres 16 smeru (0,9 = skoro nejdelsi smer, "
              "jedina mezera v korunach nerozhoduje); uzavrena_do_m / panorama_od_m: hranice typu sceny. Cisla: "
              "odhad 2. 11., NEOVERENO na tablete - overit snimky z hranic scen a merenim.",
}


def main():
    vy = json.load(open(os.path.join(ROOT, "build", "vyhledy.json")))
    stary = json.load(open(CIL)) if os.path.exists(CIL) else {}
    pr = dict(VYCHOZI)
    pr.update(stary.get("pravidla", {}))
    lok = json.load(open(os.path.join(ROOT, "pravidla", "svet", "lokace.json")))
    chran = lok.get("kompozice", {}).get("vyhledy", [])
    # obzor (nejvzdalenejsi viditelny bod nad blizsimi prekazkami, oci jezdce 2,4 m), ne vodorovny dohled - jinak by hra
    # usekla vzdaleny kopec nad remizkem
    pts = np.array([[o["x"], o["z"], float(np.quantile(o["obzor"], pr["kvantil"]))] for o in vy if o.get("obzor")], dtype=np.float64)
    k = float(pr["krok_m"])
    x0, x1 = math.floor(pts[:, 0].min() / k) * k, math.ceil(pts[:, 0].max() / k) * k
    z0, z1 = math.floor(pts[:, 1].min() / k) * k, math.ceil(pts[:, 1].max() / k) * k
    nx, nz = int((x1 - x0) / k) + 1, int((z1 - z0) / k) + 1
    dohled = np.zeros((nz, nx), dtype=np.float64)
    r = float(pr["okoli_m"])
    for j in range(nz):
        for i in range(nx):
            x, z = x0 + i * k, z0 + j * k
            d2 = (pts[:, 0] - x) ** 2 + (pts[:, 1] - z) ** 2
            m = d2 < r * r
            if not m.any():
                m = d2 <= d2.min() + 1e-6          # zadny bod v okoli: nejblizsi
            dohled[j, i] = pts[m, 2].max()
    # chranene vyhledy (lokace.json kompozice.vyhledy): vzdy panorama (zadani bod 4C: panorama se nezakryva)
    for v in chran:
        cx, cz, rr = float(v["stred"][0]), float(v["stred"][1]), float(v["polomer_m"]) + r
        for j in range(nz):
            for i in range(nx):
                if math.hypot(x0 + i * k - cx, z0 + j * k - cz) < rr:
                    dohled[j, i] = max(dohled[j, i], 1500.0)
    typ = np.where(dohled < pr["uzavrena_do_m"], 0, np.where(dohled >= pr["panorama_od_m"], 2, 1))
    out = {
        "popis": "Sceny podle skutecne viditelnosti (tools/sceny.py z build/vyhledy.json). dohled_m: dohled bunky v m "
                 "(radky po z od z0, sloupce po x od x0), typ: 0 uzavrena, 1 polootevrena, 2 panorama. Hra: scripts/sceny.gd "
                 "(hranice kresleni a mlha podle dohledu; profily v 'hra').",
        "pravidla": pr,
        "hra": stary.get("hra", {
            "far_rezerva_k": 1.4,
            "far_rezerva_m": 120.0,
            "far_min_m": 380.0,
            "far_max_m": 2200.0,
            "zmena_m_s": 250.0,
            "_popis": "hranice kresleni (Camera3D.far) = dohled * far_rezerva_k + far_rezerva_m, v mezich far_min_m.."
                      "far_max_m (2200 = puvodni pevna hodnota player.gd); ke zvetseni hned (nic nesmi chybet), ke "
                      "zmenseni nejvys zmena_m_s (hystereze v case). Navrat: far_min_m = 2200 vypne sceny bez nove verze kodu.",
        }),
        "x0": x0, "z0": z0, "krok_m": k, "nx": nx, "nz": nz,
        "dohled_m": [int(round(v)) for v in dohled.ravel()],
        "typ": [int(v) for v in typ.ravel()],
    }
    json.dump(out, open(CIL, "w"), ensure_ascii=False)
    n = typ.size
    print("SCENY mrizka %d x %d po %.0f m: uzavrena %.0f %%, polootevrena %.0f %%, panorama %.0f %%" % (
        nx, nz, k, 100.0 * (typ == 0).sum() / n, 100.0 * (typ == 1).sum() / n, 100.0 * (typ == 2).sum() / n))
    try:
        from PIL import Image
        barvy = np.array([[40, 110, 40], [220, 200, 60], [210, 70, 50]], dtype=np.uint8)
        img = Image.fromarray(np.flipud(barvy[typ])).resize((nx * 4, nz * 4), Image.NEAREST)
        img.save(os.path.join(ROOT, "build", "sceny.png"))
        print("SCENY mapa build/sceny.png (zelena uzavrena, zluta polootevrena, cervena panorama)")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
