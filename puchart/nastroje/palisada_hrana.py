"""Palisáda po hraně kopce (Míša 30. 10.: „smysluplně podle terénu a svahu, využij maximální prostor kopce“).
Pro body po ose hřbetu mezi hrady se kolmo na obě strany hledá hrana – první místo, kde sklon (vyhlazený 3 m)
překročí `hrana_sklon`; palisáda stojí kousek za hranou na plošině (`odstup_m`), čára se vyhladí.
Konce se napojí na rohy hradů. Výstup: obě čáry do hrady_navrhy.json (navrh 6).
python3 palisada_hrana.py"""
import json, numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
v = json.load(open("hra/data/vysek.json"))
r = np.fromfile("hra/data/vysek.r16", "<u2").reshape(v["vyska"], v["sirka"]) / 200 + 300 - v["pocatek_H"]
Hs = gaussian_filter(r, 3.0); gz, gx = np.gradient(Hs); S = np.hypot(gx, gz)
def sl(x, z): return float(map_coordinates(S, [[z - v["z0_hra"]], [x - v["x0_hra"]]], order=1)[0])
def h(x, z): return float(map_coordinates(Hs, [[z - v["z0_hra"]], [x - v["x0_hra"]]], order=1)[0])
P = "pravidla/svet/hrady_navrhy.json"; D = json.load(open(P)); A = D["spolecne"]["A"]; B = D["spolecne"]["B"]
HRANA = 0.62; ODSTUP = 1.5
# osa hřbetu: z jižního okraje jádra A k severní zdi B, po nejvyšších bodech
a = np.array([12.0, 18.0]); b = np.array([72.0, 82.0])
osa = []
for t in np.linspace(0, 1, 26):
    p = a + (b - a) * t; d = (b - a) / np.linalg.norm(b - a); n = np.array([-d[1], d[0]])
    best = max(np.arange(-20, 21, 1.0), key=lambda o: h(*(p + n * o)))
    osa.append(p + n * best)
osa = np.array(osa)
osa = np.c_[np.convolve(osa[:, 0], np.ones(5) / 5, "same"), np.convolve(osa[:, 1], np.ones(5) / 5, "same")]
osa[:2] = [a, a + (osa[2] - a) * 0.5]; osa[-2:] = [b + (osa[-3] - b) * 0.5, b]
L, R = [], []
for i in range(len(osa)):
    d = osa[min(i + 1, len(osa) - 1)] - osa[max(i - 1, 0)]; d /= np.linalg.norm(d); n = np.array([-d[1], d[0]])
    for strana, out in ((1, L), (-1, R)):
        o = 0.0
        while o < 45 and sl(*(osa[i] + n * strana * o)) < HRANA:
            o += 0.5
        out.append(osa[i] + n * strana * max(3.0, o - ODSTUP))
def hlad(c):
    c = np.array(c)
    for _ in range(3):
        c[1:-1] = (c[:-2] + 2 * c[1:-1] + c[2:]) / 4
    return c
L, R = hlad(L), hlad(R)
# která strana je západní (Velička)
zap, vych = (L, R) if L[:, 0].mean() < R[:, 0].mean() else (R, L)
j = A["jadro"]; kur = B["kurtina"]["osa"]
zap = np.vstack([[j[3]], zap[2:-2], [kur[0]]])        # SZ roh jádra -> západní roh B
vych = np.vstack([[j[2]], vych[2:-2], [kur[1]]])      # JV roh jádra -> severní roh B
plocha = 0.5 * abs(np.dot(np.r_[zap[:, 0], vych[::-1, 0]], np.roll(np.r_[zap[:, 1], vych[::-1, 1]], 1)) - np.dot(np.r_[zap[:, 1], vych[::-1, 1]], np.roll(np.r_[zap[:, 0], vych[::-1, 0]], 1)))
print("palisáda západ", len(zap), "bodů, východ", len(vych), "bodů, uzavřená plocha %.0f m²" % plocha)
D["spolecne"]["palisada_hrana"] = {"popis": "po hraně plošiny (sklon > %.2f), %g m za hranou; nastroje/palisada_hrana.py" % (HRANA, ODSTUP),
    "zapad": [[round(float(x), 1), round(float(z), 1)] for x, z in zap], "vychod": [[round(float(x), 1), round(float(z), 1)] for x, z in vych], "plocha_m2": round(plocha)}
json.dump(D, open(P, "w"), ensure_ascii=False, indent=1)
