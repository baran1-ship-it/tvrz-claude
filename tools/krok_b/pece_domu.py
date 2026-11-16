"""Rozmisteni chalupni pece (Topeni_1400 Pec_Chalupni) a luzka v jizbe domu vsi (Misa 16. 11.: „pece v chalupach
nahradit Pec_Chalupni“). Nova pec (2,52 x 2,50 m s lavici, zapecim a predpecim) je vetsi nez pec modelu (1,48 x 1,91 m)
a na jeji misto u dveri jizby se nevejde - hleda se misto v jizbe podle pravidel a zapise do nabytek.json domy:
  - pudorys pece (obdelnik rozmeru z katalogu, natoceni po 90 st.) cely v jizbe (vnitrni lic sten z kolizi
    Kol_Stena* modelu domy.glb, odstup od zdi pasma.predmet od_zdi_m nebo 0,02), mimo pruchod dveri jizby (sire dveri
    x hloubka pruchod_m), mimo lavici modelu (Kol_Lavice) a stul s lavici (kusy nabytku);
  - pred ustim (znacka Pec_Usti) volne misto pred_ustim_m (prikladani, pekarska lopata);
  - zapeci (mistni -z) a lavice pece (mistni -x) ke zdi (KCD, chalupy 14. st.: pec v koute, zapeci u zdi);
  - pak luzko: cele v jizbe, mimo pec, dvere, lavice, stul; v koute vstupni steny na druhe strane nez pec (Misa 16. 11.:
    jizba po staru - pec v koute u vstupu, stul ve svatem koute, luzko v protejsim koute; dvere jizby jsou v modelech u rohu,
    pec 2,5 x 2,5 m se do rohu u dveri nevejde -> pec v rohu -x hned za pruchodem dveri);
  - drobne kusy (vedro, spalek, truhla, kolebka), ktere zasahuji do pece nebo luzka, se presunou na nejblizsi volne misto.
Vystup: nabytek.json domy[typ] kusy (pec_chalupni + posunute kusy) a pec_modelu (materialy a uzly puvodni pece pryc).
  python3 tools/krok_b/pece_domu.py [--zapis]"""
import json
import math
import struct
import sys

import numpy as np

KAT = json.load(open("modely/predmety.json"))
NAB = json.load(open("pravidla/svet/nabytek.json"))
PR = json.load(open("pravidla/svet/nabytek.json"))["pece_domu"]
TYPY = ["Dum1", "Dum2", "Rychta"]


def glb_kolize(cesta):
    d = open(cesta, "rb").read()
    jl = struct.unpack_from("<I", d, 12)[0]
    j = json.loads(d[20:20 + jl])
    B = d[28 + jl:]

    def acc(i):
        a = j["accessors"][i]
        bv = j["bufferViews"][a["bufferView"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.frombuffer(B, dtype=np.float32, count=a["count"] * 3, offset=off).reshape(-1, 3)
    out = {}
    for n in j["nodes"]:
        nm = n.get("name", "")
        if "mesh" in n and ("Kol_" in nm or "_Dvere_" in nm):
            P = acc(j["meshes"][n["mesh"]]["primitives"][0]["attributes"]["POSITION"]) + np.array(n.get("translation", [0, 0, 0]))
            out[nm.replace("-convcolonly", "")] = (P.min(0), P.max(0))
    return out


CHODBA = {}
MER = {}                     # meritko kusu (pec zmensena na velikost pece modelu, pece_domu.meritko)


def obd(id_, x, z, yaw_st):
    """Pudorys kusu (osove zarovnany obdelnik pro natoceni po 90 st.): (x0, x1, z0, z1)."""
    r = [v * MER.get(id_, 1.0) for v in KAT[id_]["rozmer"]]
    a = round(yaw_st / 90.0) % 2
    hx, hz = (r[0] / 2, r[2] / 2) if a == 0 else (r[2] / 2, r[0] / 2)
    return (x - hx, x + hx, z - hz, z + hz)


def lok(id_, x, z, yaw_st, lp):
    """Bod v souradnicich kusu (lx, lz) -> dum (Godot Basis(UP, yaw): x' = x c + z s, z' = -x s + z c)."""
    t = math.radians(yaw_st)
    return x + lp[0] * math.cos(t) + lp[1] * math.sin(t), z - lp[0] * math.sin(t) + lp[1] * math.cos(t)


def prekryv(a, b, okraj=0.0):
    return a[0] < b[1] + okraj and a[1] > b[0] - okraj and a[2] < b[3] + okraj and a[3] > b[2] - okraj


def uvnitr(a, r):
    return a[0] >= r[0] and a[1] <= r[1] and a[2] >= r[2] and a[3] <= r[3]


def pro_typ(typ, kol):
    m = {k[len(typ) + 1:]: v for k, v in kol.items() if k.startswith(typ + "_")}
    # jizba: mezi stenami - levy/pravy lic (StenaL0/R0), pricka sine (P1*) a stit (F0)
    x0 = m["Kol_StenaL0"][1][0] + PR["od_zdi_m"]
    x1 = m["Kol_StenaR0"][0][0] - PR["od_zdi_m"]
    zp = max(v[1][2] for k, v in m.items() if k.startswith("Kol_StenaP1")) + PR["od_zdi_m"]
    zf = m["Kol_StenaF0"][0][2] - PR["od_zdi_m"]
    jizba = (x0, x1, zp, zf)
    dv = m["Dvere_Jizba"]
    dvere = (dv[0][0] - 0.1, dv[1][0] + 0.1, zp - 0.2, zp + float(PR.get("typy", {}).get(typ, {}).get("pruchod_m", PR["pruchod_m"])))
    lav = m["Kol_Lavice"]
    # 17. 11. (test dvere_domu: Dum2 82 %, Rychta 71 % - pec / kolebka v ceste ode dveri do stredu jizby): chodba ode
    # dveri ke stredu jizby volna (sire pruchod_k_stredu_m na kazdou stranu osy)
    dx = (dv[0][0] + dv[1][0]) / 2
    cx, cz = (x0 + x1) / 2, (zp + zf) / 2
    ps = float(PR["pruchod_k_stredu_m"])
    chodba = []                                     # usecka dvere -> stred jizby jako rada ctvercu +- ps (cesta testu)
    sz = zp - float(PR["sin_stred_od_pricky_m"])    # cesta jako test dvere_domu: od stredu sine ke stredu jizby
    for i in range(25):
        t_ = i / 24.0
        qx, qz = dx + (cx - dx) * t_, sz + (cz - sz) * t_
        if qz < zp - 0.2:
            continue
        chodba.append((qx - ps, qx + ps, qz - ps, qz + ps))
    prekazky = [dvere, (lav[0][0], lav[1][0], lav[0][2], lav[1][2])] + chodba
    CHODBA[typ] = chodba
    pr_t = dict(PR, **PR.get("typy", {}).get(typ, {}))
    kusy = [list(k) for k in NAB["domy"][typ]["kusy"] if k[0] not in pr_t.get("vynechat_kusy", []) and k[0] != PR["pec"]]
    pevne = [k for k in kusy if k[0] in PR["pevne_kusy"]]
    for k in pevne:
        prekazky.append(obd(k[0], k[1], k[2], k[3]))
    stara = m["Kol_Pec"]
    sc = ((stara[0][0] + stara[1][0]) / 2, (stara[0][2] + stara[1][2]) / 2)
    pec = PR["pec"]
    # Misa 16. 11. („kdyz je pec moc velka, zmensi ji na puvodni velikost“): meritko pece = nejvetsi rozmer pudorysu
    # pece modelu (Kol_Pec) / nejvetsi rozmer pudorysu nove pece (katalog), jen zmenseni (pece_domu.meritko)
    sp = stara[1] - stara[0]
    MER.clear()
    if PR.get("meritko") == "podle_pece_modelu":
        MER[pec] = round(float(min(1.0, max(sp[0], sp[2]) / max(KAT[pec]["rozmer"][0], KAT[pec]["rozmer"][2]))), 3)
    msc = MER.get(pec, 1.0)
    us = [v * msc for v in KAT[pec]["znacky"]["Pec_Usti"]]
    kand = []
    for yaw in (0.0, 90.0, 180.0, 270.0):
        for x in np.arange(jizba[0], jizba[1], 0.05):
            for z in np.arange(jizba[2], jizba[3], 0.05):
                o = obd(pec, x, z, yaw)
                if not uvnitr(o, jizba) or any(prekryv(o, p) for p in prekazky):
                    continue
                ux, uz = lok(pec, x, z, yaw, (us[0], us[2] + PR["pred_ustim_m"]))
                if not (jizba[0] < ux < jizba[1] and jizba[2] < uz < jizba[3]) or any(p[0] < ux < p[1] and p[2] < uz < p[3] for p in prekazky):
                    continue
                # zapeci (mistni -z) a lavice (mistni -x) ke zdi: vzdalenost jejich strany obdelniku od lice jizby
                zx, zz = lok(pec, x, z, yaw, (0.0, -KAT[pec]["rozmer"][2] * msc / 2))
                lx_, lz_ = lok(pec, x, z, yaw, (-KAT[pec]["rozmer"][0] * msc / 2, 0.0))
                dzed = lambda px, pz: min(px - jizba[0], jizba[1] - px, pz - jizba[2], jizba[3] - pz)
                sk = 4.0 * dzed(zx, zz) + 2.0 * dzed(lx_, lz_) + 0.3 * math.hypot(x - sc[0], z - sc[1])
                # Misa 16. 11.: pec v koute u vstupni steny (pricka sine) - co nejbliz, kam to pruchod dveri dovoli
                sk += float(PR.get("k_vstupni_stene", 0.0)) * (o[2] - jizba[2])
                kand.append((sk, round(float(x), 3), round(float(z), 3), yaw))
    kand.sort()
    for best in kand[:400]:
        r = _luzko(typ, kusy, jizba, prekazky, pec, us, best, pr_t)
        if r:
            print("PECE %s meritko %.3f" % (typ, MER.get(pec, 1.0)))
        if r:
            return r
    return None


def _luzko(typ, kusy, jizba, prekazky, pec, us, best, pr_t):
    _, px, pz, pyaw = best
    po = obd(pec, px, pz, pyaw)
    out = [k for k in kusy]
    # luzko: puvodni kus s lehat, nejblize puvodnimu mistu
    li = next(i for i, k in enumerate(out) if KAT[k[0]].get("lehat"))
    lk = out[li]
    # pred ustim volno (prikladani): obdelnik od usti do pred_ustim_m, sire usti + 2 x 0,25 m
    u0 = lok(pec, px, pz, pyaw, (us[0] - 0.55, us[2]))
    u1 = lok(pec, px, pz, pyaw, (us[0] + 0.55, us[2] + PR["pred_ustim_m"]))
    prek2 = prekazky + [po, (min(u0[0], u1[0]), max(u0[0], u1[0]), min(u0[1], u1[1]), max(u0[1], u1[1]))]
    lb = None
    for yaw in (0.0, 90.0, 180.0, 270.0):
        for x in np.arange(jizba[0], jizba[1], 0.05):
            for z in np.arange(jizba[2], jizba[3], 0.05):
                o = obd(lk[0], x, z, yaw)
                if uvnitr(o, jizba) and not any(prekryv(o, p) for p in prek2):
                    # jizba po staru (Misa 16. 11., pece_domu.luzko_kout): luzko v koute vstupni steny (pricka sine) na druhe
                    # strane nez pec - blizko rohu: roh obdelniku luzka nejblize k rohu jizby
                    # 16. 11. vecer (snimek rychty: luzko uprostred jizby, kout vstupni steny zabral stul) - luzko v nejblizsim
                    # volnem koute: vstupni stena naproti peci ma prednost (+0), ostatni kouty mimo kout pece (+luzko_kout_jinde_m)
                    sk = None
                    for (rx, rz, pl) in ((jizba[1] if px < (jizba[0] + jizba[1]) / 2 else jizba[0], jizba[2], 0.0),
                                         (jizba[0], jizba[2], 1.0), (jizba[1], jizba[2], 1.0), (jizba[0], jizba[3], 1.0), (jizba[1], jizba[3], 1.0)):
                        if prekryv(po, (rx - 0.3, rx + 0.3, rz - 0.3, rz + 0.3)):
                            continue                          # kout pece
                        d_ = math.hypot(min(abs(o[0] - rx), abs(o[1] - rx)), min(abs(o[2] - rz), abs(o[3] - rz))) + pl * float(PR.get("luzko_kout_jinde_m", 0.5))
                        sk = d_ if sk is None else min(sk, d_)
                    sk += (0.0 if yaw == lk[3] else 0.05)
                    if lb is None or sk < lb[0]:
                        lb = (sk, round(float(x), 3), round(float(z), 3), yaw)
    if lb is None:
        return None
    out[li] = [lk[0], lb[1], lb[2], lb[3], lk[4]]
    lo_ = obd(lk[0], lb[1], lb[2], lb[3])
    obsaz = prek2 + [lo_]
    # drobne kusy na podlaze jizby, ktere zasahuji do pece nebo luzka: nejblizsi volne misto
    for i, k in enumerate(out):
        if i == li or k[0] in PR["pevne_kusy"] or len(k) > 5 or float(k[4]) != 0.0:
            continue
        if not (jizba[2] - 0.2 <= k[2] <= jizba[3] + 0.2):
            continue                                  # jen jizba
        o = obd(k[0], k[1], k[2], k[3])
        if not any(prekryv(o, p) for p in [po, lo_] + CHODBA[typ]):
            obsaz.append(o)
            continue
        kb = None
        for x in np.arange(jizba[0], jizba[1], 0.05):
            for z in np.arange(jizba[2], jizba[3], 0.05):
                o2 = obd(k[0], x, z, k[3])
                if uvnitr(o2, jizba) and not any(prekryv(o2, p, 0.05) for p in obsaz):
                    d_ = math.hypot(x - k[1], z - k[2])
                    if kb is None or d_ < kb[0]:
                        kb = (d_, round(float(x), 3), round(float(z), 3))
        if kb:
            out[i] = [k[0], kb[1], kb[2]] + k[3:]
            obsaz.append(obd(k[0], kb[1], kb[2], k[3]))
    out.append([pec, px, pz, pyaw, 0.0] + ([{"sc": MER[pec]}] if MER.get(pec, 1.0) != 1.0 else []))
    return out, best, lb, jizba


if __name__ == "__main__":
    kol = glb_kolize("modely/ves/domy.glb")
    vys = {}
    for t in TYPY:
        r = pro_typ(t, kol)
        if r is None:
            print("PECE %s: pec se do jizby nevejde" % t)
            sys.exit(1)
        out, b, lb, jz = r
        po = obd(PR["pec"], b[1], b[2], b[3])
        u_zdi = sum(1 for v in (po[0] - jz[0], jz[1] - po[1], po[2] - jz[2], jz[3] - po[3]) if v < 0.15)
        if u_zdi < 2:
            # Misa 16. 11.: „nechci, aby pec nekde zavazela uprostred mistnosti“ - pec musi byt v rohu (u dvou zdi)
            print("PECE %s: pec neni v rohu (u zdi %d)" % (t, u_zdi))
            sys.exit(1)
        lo_ = obd([k for k in out if KAT[k[0]].get("lehat")][0][0], lb[1], lb[2], lb[3])
        if sum(1 for v in (lo_[0] - jz[0], jz[1] - lo_[1], lo_[2] - jz[2], jz[3] - lo_[3]) if v < 0.4) < (1 if PR.get("typy", {}).get(t, {}).get("luzko_u_zdi_staci") else 2):      # 0,4: lavice modelu podel zdi
            print("PECE %s: luzko neni v koute %s jizba %s" % (t, [round(v, 2) for v in lo_], [round(float(v), 2) for v in jz]))
            sys.exit(1)
        print("PECE %s: jizba %s, pec %s, luzko %s" % (t, [round(v, 2) for v in jz], b[1:], lb[1:]))
        for k in out:
            print("   ", k)
        vys[t] = out
    if "--zapis" in sys.argv:
        s = open("pravidla/svet/nabytek.json").read()
        d = json.loads(s)
        for t, out in vys.items():
            d["domy"][t]["kusy"] = out
        open("pravidla/svet/nabytek.json", "w").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
        print("zapsano nabytek.json domy")
