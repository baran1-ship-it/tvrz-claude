"""Mapa viditelnosti po trasách hráče (Míša 2. 11., zadání GPT „Inteligentní tvorba scén“ bod 2): z každého bodu trasy
(po krok_m, oko 1,7 m) paprsky do 360° nad skutečným terénem (vysek1m_cesty = DMR + úpravy) a lesem (stromy.bin, koruny
jako objemy). Terén a stavby = neprůhledná clona; koruny a kmeny = částečná clona (útlum po metrech). Výsledek:
dohled ve směrech (medián, p90, podíl dálkových směrů) → typ scény A uzavřená / B polootevřená / C panoramatická,
úseky trasy → pravidla/svet/sceny.json (navrh, ruční úpravy v `rucne` se zachovají), mapa build/viditelnost.png.
  python3 nastroje/viditelnost.py <vysek_prefix> <koren>"""
import sys, os, json, math
import numpy as np
from scipy.ndimage import map_coordinates, maximum_filter
pre, K = sys.argv[1:3]
P = json.load(open(K + "/pravidla/svet/svet.json"))["pocatek"]
CFG = json.load(open(K + "/pravidla/svet/sceny_pravidla.json"))
H = np.load(pre + ".npy").astype(np.float32); M = json.load(open(pre + ".json"))
x0 = M["x0"] - P["X"]; z0 = -(M["y1"] - P["Y"]); Y = H - P["H"]; ny, nx = Y.shape
# --- les: výška korun a spodek korun na mřížce 2 m (koruna = válec r = a·h + b od základu c·h do h)
KR = CFG["les"]; G = 2.0; gx, gz = int(nx / G) + 1, int(ny / G) + 1
top = np.zeros((gz, gx), np.float32); spod = np.full((gz, gx), 1e9, np.float32)
raw = np.fromfile(K + "/hra/data/stromy.bin", np.float32).reshape(-1, 5)
for x, z, h, _, _ in raw:
    r = KR["polomer_a"] * h + KR["polomer_b"]; ci, ri = int((x - x0) / G), int((z - z0) / G); k = int(r / G) + 1
    r0, r1, c0, c1 = max(0, ri - k), min(gz, ri + k + 1), max(0, ci - k), min(gx, ci + k + 1)
    if r0 >= r1 or c0 >= c1: continue
    rr, cc = np.mgrid[r0:r1, c0:c1]; m = (np.hypot(cc * G + G / 2 - (x - x0), rr * G + G / 2 - (z - z0)) <= r)
    top[r0:r1, c0:c1][m] = np.maximum(top[r0:r1, c0:c1][m], h); spod[r0:r1, c0:c1][m] = np.minimum(spod[r0:r1, c0:c1][m], h * KR["spodek_koruny"])
spod[spod > 1e8] = 0
les = top > 0
def ter(x, z):
    a = np.atleast_1d(np.asarray(x, float)); b = np.atleast_1d(np.asarray(z, float)); v = map_coordinates(Y, [b.ravel() - z0, a.ravel() - x0], order=1, mode="nearest").reshape(a.shape)
    return v if np.ndim(x) else float(v[0])
def bunka(x, z):
    c = np.clip(((np.asarray(x) - x0) / G).astype(int), 0, gx - 1); r = np.clip(((np.asarray(z) - z0) / G).astype(int), 0, gz - 1)
    return r, c
# --- stavby jako neprůhledné clony: kolizní kvádry hradů vyšší než 1 m (hra/data/stavby_clony.json ze stavitele hradu)
YO = Y.copy()
if os.path.exists(K + "/hra/data/stavby_clony.json"):
    from PIL import Image as _I, ImageDraw as _D
    for q in json.load(open(K + "/hra/data/stavby_clony.json"))["kvadry"]:
        r = np.array(q["rohy"]); c0_, r0_ = int(r[:, 0].min() - x0) - 1, int(r[:, 1].min() - z0) - 1
        w_, h_ = int(r[:, 0].max() - r[:, 0].min()) + 3, int(r[:, 1].max() - r[:, 1].min()) + 3
        im = _I.new("L", (w_, h_), 0); _D.Draw(im).polygon([(a - x0 - c0_, b - z0 - r0_) for a, b in r], fill=1)
        m = np.array(im).astype(bool); sub = YO[r0_:r0_ + h_, c0_:c0_ + w_]; m = m[:sub.shape[0], :sub.shape[1]]
        sub[m] = np.maximum(sub[m], q["vrch"])
def ter_o(x, z):
    a = np.asarray(x, float); b = np.asarray(z, float)
    return map_coordinates(YO, [b.ravel() - z0, a.ravel() - x0], order=0, mode="nearest").reshape(a.shape)
V = CFG["paprsky"]; smery = np.radians(np.arange(0, 360, V["krok_stupne"])); kroky = np.arange(V["krok_m"], V["dosah_m"] + 1e-6, V["krok_m"])
def dohled(px, pz, oko):
    y0 = ter(px, pz) + oko
    X = px + np.outer(np.sin(smery), kroky); Z = pz - np.outer(np.cos(smery), kroky)
    T = ter(X, Z); TO = ter_o(X, Z)   # TO: terén se stavbami (clona), T: zem (cíl a vegetace)
    # terén: paprsek k bodu ve vzdálenosti d je vidět, když úhel k němu ≥ max úhel všech bližších (cíl = terén + 1,5 m)
    uhel = (T + 1.5 - y0) / kroky; uhel_t = (TO - y0) / kroky
    zakryto_t = uhel < np.maximum.accumulate(np.c_[np.full(len(smery), -9), uhel_t[:, :-1]], axis=1)
    # vegetace: útlum podél paprsku ve výšce přímky oko -> cíl (zjednodušeně ve výšce oka nad terénem + sklon k cíli)
    r, c = bunka(X, Z); h_rel = (y0 - T)   # výška paprsku nad terénem při vodorovném pohledu
    vys = np.maximum(h_rel, V["vyska_paprsku_min_m"])
    v_korune = les[r, c] & (vys >= spod[r, c]) & (vys <= top[r, c])
    pod_korunou = les[r, c] & (vys < spod[r, c])
    utlum = np.where(v_korune, KR["utlum_koruna_m"], np.where(pod_korunou, KR["utlum_kmeny_m"], 0.0)) * V["krok_m"]
    prop = np.exp(-np.cumsum(utlum, axis=1))
    vid = (~zakryto_t) & (prop > V["prah_propustnosti"])
    # dohled ve směru = nejvzdálenější viditelný bod (terén za kopcem může být vidět znovu – rozhoduje nejdál)
    d = np.where(vid.any(1), kroky[np.where(vid, np.arange(len(kroky)), 0).max(1)], 0.0)
    return d, (X[vid], Z[vid])
cesty = json.load(open(K + "/pravidla/svet/cesty_puchart.json"))["cesty"]
mista = json.load(open(K + "/hra/data/mista.json"))["mista"]
TR = CFG["trasy"]; body = []
for t in TR:
    if "cesta" in t:
        o = np.array(next(c for c in cesty if c["id"] == t["cesta"])["osa"], float)
        if t.get("obracene"): o = o[::-1]
        s = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]
        for si in np.arange(0, s[-1] + 1e-6, CFG["krok_trasy_m"]):
            body.append((t["id"], float(np.interp(si, s, o[:, 0])), float(np.interp(si, s, o[:, 1])), None, si))
    for jm in t.get("mista", []):
        m = next(m for m in mista if m["nazev"] == jm); body.append((t["id"], m["kde"][0], m["kde"][1], m.get("y"), jm))
TY = CFG["typy"]; vysl = []; vid_mapa = np.zeros((gz, gx), np.uint16)
for tid, x, z, y, s in body:
    oko = 1.7 if y is None else (y + 1.7 - float(ter(x, z)))
    d, (vx, vz) = dohled(x, z, oko)
    r_, c_ = bunka(vx, vz); np.add.at(vid_mapa, (r_, c_), 1)
    med, p90, dal = float(np.median(d)), float(np.percentile(d, 90)), float((d >= TY["panorama_od_m"]).mean())
    typ = "C" if dal >= TY["panorama_podil_smeru"] else ("A" if p90 < TY["uzavrena_do_m"] else "B")
    vysl.append({"trasa": tid, "x": round(x, 1), "z": round(z, 1), "u": s if isinstance(s, str) else round(s), "typ": typ,
                 "dohled_median_m": round(med), "dohled_p90_m": round(p90), "podil_dalky": round(dal, 2), "v_lese": bool(les[bunka(x, z)])})
# úseky: po sobě jdoucí stejný typ (krátké výkyvy pod min_usek_m se sloučí do sousedního)
sceny = []
for tid in [t["id"] for t in TR]:
    b = [v for v in vysl if v["trasa"] == tid]
    for v in b:
        if sceny and sceny[-1]["trasa"] == tid and sceny[-1]["typ"] == v["typ"]: sceny[-1]["body"].append(v)
        else: sceny.append({"trasa": tid, "typ": v["typ"], "body": [v]})
out = []
for i, sc in enumerate(sceny):
    b = sc["body"]
    out.append({"id": "%s_%02d_%s" % (sc["trasa"], i, sc["typ"]), "trasa": sc["trasa"], "typ": sc["typ"], "od": b[0]["u"], "do": b[-1]["u"],
                "stred": [round(float(np.mean([q["x"] for q in b])), 1), round(float(np.mean([q["z"] for q in b])), 1)],
                "dohled_median_m": round(float(np.median([q["dohled_median_m"] for q in b]))), "dohled_p90_m": round(float(np.max([q["dohled_p90_m"] for q in b]))),
                "v_lese": float(np.mean([q["v_lese"] for q in b])) > 0.5, "bodu": len(b)})
cil = K + "/pravidla/svet/sceny.json"
rucne = json.load(open(cil)).get("rucne", {}) if os.path.exists(cil) else {}
json.dump({"popis": "Scény podél tras (nastroje/viditelnost.py z DMR + stromy.bin; pravidla sceny_pravidla.json). typ A uzavřená / B polootevřená / C panoramatická. `rucne` = schválené úpravy (zachovají se při přepočtu).",
           "sceny": out, "body": vysl, "rucne": rucne}, open(cil, "w"), ensure_ascii=False, indent=1)
np.save(K + "/build/viditelnost.npy", vid_mapa)
json.dump({"popis": "body tras s typem scény a dohledem pro hru (nastroje/viditelnost.py); pravidla hra/data/sceny_pravidla.json",
           "body": [[v["x"], v["z"], v["typ"], v["dohled_p90_m"]] for v in vysl]}, open(K + "/hra/data/sceny.json", "w"))
import shutil; shutil.copy(K + "/pravidla/svet/sceny_pravidla.json", K + "/hra/data/sceny_pravidla.json")
from collections import Counter
print("bodů", len(vysl), "typy", dict(Counter(v["typ"] for v in vysl)), "scén", len(out))
for s in out: print(" ", s["id"], s["od"], "→", s["do"], "dohled med %d p90 %d" % (s["dohled_median_m"], s["dohled_p90_m"]), "les" if s["v_lese"] else "")
# mapa: stínovaný terén, les, viditelné plochy (oranžově), body trasy podle typu
from PIL import Image
sh = np.clip(0.6 + (np.gradient(Y, axis=1) - np.gradient(Y, axis=0)) * 0.6, 0, 1)
img = np.stack([sh * 200, sh * 200, sh * 190], -1)
lz = np.repeat(np.repeat(les, 2, 0), 2, 1)[:ny, :nx]; img[lz] = img[lz] * 0.55 + np.array([20, 90, 30]) * 0.45
vm = np.repeat(np.repeat(vid_mapa > 0, 2, 0), 2, 1)[:ny, :nx]; img[vm] = img[vm] * 0.5 + np.array([255, 150, 40]) * 0.5
im = Image.fromarray(img.astype(np.uint8)); from PIL import ImageDraw; dr = ImageDraw.Draw(im)
bar = {"A": (30, 60, 200), "B": (230, 200, 0), "C": (220, 20, 20)}
for v in vysl:
    px, pz = v["x"] - x0, v["z"] - z0; dr.ellipse([px - 6, pz - 6, px + 6, pz + 6], fill=bar[v["typ"]], outline=(0, 0, 0))
im.save(K + "/build/viditelnost.png"); print("mapa build/viditelnost.png")
