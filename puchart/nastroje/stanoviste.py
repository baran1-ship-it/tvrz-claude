"""Maska stanovišť výseku (pečená, ne počítaná ve hře). Pravidla z pravidla/svet/plochy.json.

R = louka/pastvina, G = lesní opad (les), B = skála (strmé), A = břeh a bahno u toku. Součet ≤ 1, zbytek = hlína.
Výstup: hra/textury/maska_vysek.png (RGBA8, krok viz plochy.json maska_krok_m) + docs/screens/maska.png
python3 stanoviste.py <vysek_prefix> <voda.json (hra)> <koren>
"""
import sys, json, os
import numpy as np
from scipy.ndimage import gaussian_filter, distance_transform_edt, zoom
from PIL import Image

pre, voda, koren = sys.argv[1:4]
PL = json.load(open(os.path.join(koren, "pravidla/svet/plochy.json")))
S = json.load(open(os.path.join(koren, "pravidla/svet/svet.json")))
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json"))
k = PL["maska_krok_m"]
Hs = gaussian_filter(H, PL["sklon_zaklad_m"] / 2.0)[::k, ::k]   # sklon „jak ho vidí orač“ (Havran plochy.json)
Hj = gaussian_filter(H, 2.5)[::k, ::k]  # 1,5 m ukazoval trojúhelníky TIN jako skálu
gz, gx = np.gradient(Hs, k); sklon = np.hypot(gx, gz)
gzj, gxj = np.gradient(Hj, k); sklon_j = np.degrees(np.arctan(np.hypot(gxj, gzj)))
# orientace: řádek roste k jihu -> svah k severu má dH/dřádek > 0
sever = gz > 0
# vzdálenost od toku
V = json.load(open(voda)); P = S["pocatek"]
tok = np.zeros(Hs.shape, bool)
x_hra0 = M["x0"] - P["X"]; z_hra0 = -(M["y1"] - P["Y"])
for t in V["toky"]:
    for x, y, z in t["body"]:
        r = int(round((z - z_hra0) / k)); c = int(round((x - x_hra0) / k))
        if 0 <= r < tok.shape[0] and 0 <= c < tok.shape[1]:
            tok[r, c] = True
dtok = distance_transform_edt(~tok) * k
L = PL["les"]; PA = PL["pastvina"]; SK = PL["skala"]; BR = PL["breh"]
def kraj(x, a, b): return np.clip((x - a) / (b - a), 0, 1)
skala = kraj(sklon_j, SK["od_st"], SK["plne_st"])
les = np.maximum(kraj(sklon, L["od_sklonu"] - 0.05, L["od_sklonu"] + 0.05),
                 sever * kraj(sklon, L["sever_od_sklonu"] - 0.05, L["sever_od_sklonu"] + 0.05))
breh = 1 - kraj(dtok, BR["do_m"] * 0.5, BR["do_m"])
louka = 1 - les
les = les * (1 - skala); louka = louka * (1 - skala)
breh = breh * (1 - skala)
les *= (1 - breh); louka *= (1 - breh)
# šum hranic (lem lesa není pravítko – KCD/Havran „okraj lesa členitý“)
rng = np.random.default_rng(1393)
n = gaussian_filter(rng.standard_normal(Hs.shape), 6) * 6
les = np.clip(les + n * (les * (1 - les)) * 4, 0, 1); louka = np.clip(1 - les - skala - breh, 0, 1)
img = np.stack([louka, les, skala, breh], -1)
img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
os.makedirs(os.path.join(koren, "hra/textury"), exist_ok=True)
Image.fromarray(img, "RGBA").save(os.path.join(koren, "hra/textury/maska_vysek.png"))
os.makedirs(os.path.join(koren, "docs/screens"), exist_ok=True)
nah = np.stack([img[..., 2] * 0.6 + img[..., 3] * 0.5 + img[..., 0] * 0.55, img[..., 0] * 0.8 + img[..., 1] * 0.45 + img[..., 2] * 0.6 + img[..., 3] * 0.35,
                img[..., 2] * 0.6 + img[..., 3] * 0.15 + img[..., 0] * 0.2], -1)
Image.fromarray(np.clip(nah, 0, 255).astype(np.uint8)).save(os.path.join(koren, "docs/screens/maska.png"))
for j, a in zip("louka les skala breh".split(), [louka, les, skala, breh]):
    print(j, "%.1f %%" % (100 * a.mean()))
