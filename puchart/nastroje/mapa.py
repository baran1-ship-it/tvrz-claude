"""Mapa výseku na pergamenu (styl KCD2, postup Havrana tools/stare/gen_mapa.py): zestárlý pergamen, kopce stínované
sépií, vrstevnice jemně, les ze stromečků (listnáče kulaté, jehličnany špičaté podle druhů z stromy.bin), louky a pole
v honech, potoky modrou rukou, cesty dvojitou čarou, stezky čárkovaně, hrady jako kreslené hrádky, palisáda, rámeček,
kartuš s názvem a větrná růžice. Názvy míst jsou v obraze; hra kreslí jen polohu hráče.
Data: hra/data/vysek.r16, stanoviste.png, stromy.bin, pravidla/svet/{voda,cesty_puchart,hrady_navrhy,lokace}.json
Výstup: hra/textury/ui/mapa.png (+ mapa.json s rozsahem)
python3 mapa.py <koren>"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import gaussian_filter

K = sys.argv[1]
J = lambda p: json.load(open(os.path.join(K, p)))
V = J("hra/data/vysek.json")
r16 = np.fromfile(os.path.join(K, "hra/data/vysek.r16"), "<u2").reshape(V["vyska"], V["sirka"]) / 200.0
X0, X1, Z0, Z1 = -900.0, 760.0, -1060.0, 840.0          # rozsah mapy (hra), uvnitř výseku
PX = 1.0                                                  # m na pixel
W, Hh = int((X1 - X0) / PX), int((Z1 - Z0) / PX)
c0 = int(X0 - V["x0_hra"]); r0 = int(Z0 - V["z0_hra"])
H = r16[r0:r0 + Hh, c0:c0 + W].astype(np.float32)
rng = np.random.default_rng(1393)
INK = (58, 36, 20)
FB = os.path.join(K, "hra/fonty/GrenzeGotisch-Bold.ttf"); FM = os.path.join(K, "hra/fonty/GrenzeGotisch-Medium.ttf")

def blotch(scale):
    a = rng.random((Hh // scale + 2, W // scale + 2)).astype(np.float32)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((W, Hh), Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale * 0.4))
    return np.array(im, np.float32) / 255.0

# pergamen
img = np.ones((Hh, W, 3), np.float32) * np.array([0.90, 0.82, 0.64], np.float32)
img *= (0.88 + 0.16 * blotch(90))[..., None]; img *= (0.95 + 0.07 * blotch(30))[..., None]; img *= (0.97 + 0.05 * blotch(5))[..., None]
yy, xx = np.mgrid[0:Hh, 0:W]
okraj = np.minimum.reduce([xx, yy, W - 1 - xx, Hh - 1 - yy]).astype(np.float32)
img *= (0.72 + 0.28 * np.clip(okraj / 140.0, 0, 1))[..., None]
# stínování kopců sépií (světlo ze SZ)
Hs = gaussian_filter(H, 3.0); gz, gx = np.gradient(Hs, PX)
shade = np.clip(0.5 + (-gx * 0.6 - gz * 0.6) * 1.4, 0, 1)
img *= (0.68 + 0.38 * shade)[..., None]
# vrstevnice po 10 m, silnější po 50 m
for krok, sila in ((10, 0.06), (50, 0.14)):
    q = np.floor(Hs / krok); e = (q != np.roll(q, 1, 0)) | (q != np.roll(q, 1, 1))
    img[e] = img[e] * (1 - sila) + np.array(INK, np.float32) / 255 * sila
# stanoviště: louky a pole světle zelenožluté, pole v lánech
st = np.array(Image.open(os.path.join(K, "hra/data/stanoviste.png"))); sj = J("hra/data/stanoviste.json")
stu = np.array(Image.fromarray(st).resize((V["sirka"] - 1, V["vyska"] - 1), Image.NEAREST))[r0:r0 + Hh, c0:c0 + W]
T = sj["tridy"]
def maska(jm): return np.isin(stu, [T.index(t) for t in jm if t in T])
louka = maska(["louka_kosena", "pastvina", "les_paseka", "breh"]); pole = maska(["pole", "zemedelstvi"])
img[louka] = img[louka] * 0.82 + np.array([0.80, 0.80, 0.52]) * 0.18
img[pole] = img[pole] * 0.80 + np.array([0.86, 0.76, 0.48]) * 0.20
lany = pole & (((xx * 0.7 + yy * 0.7) // 6) % 4 == 0)
img[lany] *= 0.92
im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
d = ImageDraw.Draw(im)
P = lambda x, z: ((x - X0) / PX, (z - Z0) / PX)
# les ze stromečků (z polohy skutečných stromů, řídce – jeden symbol na ~14 m)
A = np.fromfile(os.path.join(K, "hra/data/stromy.bin"), np.float32).reshape(-1, 5)
dreviny = J("hra/data/stromy.json")["dreviny"]
jehl = {dreviny.index(x) for x in ("JD", "SM", "BO") if x in dreviny}
obs = set()
for x, z, h, dr, _rot in A[rng.permutation(len(A))]:
    if not (X0 + 8 < x < X1 - 8 and Z0 + 8 < z < Z1 - 8): continue
    k = (int(x // 19), int(z // 19))
    if k in obs: continue
    obs.add(k)
    px, pz = P(x, z); s = 3.2 + h * 0.08
    if int(dr) in jehl:
        d.polygon([(px, pz - s * 1.6), (px - s * 0.8, pz + s * 0.5), (px + s * 0.8, pz + s * 0.5)], fill=(70, 80, 44, 210), outline=INK + (200,))
    else:
        d.ellipse([px - s, pz - s * 1.1, px + s, pz + s * 0.6], fill=(88, 98, 52, 200), outline=INK + (190,))
    d.line([(px, pz + s * 0.5), (px, pz + s * 1.1)], fill=INK + (200,), width=1)
# potoky
for t in J("pravidla/svet/voda.json")["toky"]:
    pts = [P(p[0], p[2]) for p in t["body"]]
    sir = 2 + min(5, int(t.get("povodi_km2", 1) / 3))
    d.line(pts, fill=(52, 88, 128, 230), width=sir + 2); d.line(pts, fill=(118, 152, 178, 255), width=sir)
# cesty: vozová dvojitou čarou, stezka čárkovaně
for c in J("pravidla/svet/cesty_puchart.json")["cesty"]:
    pts = [P(*p) for p in c["osa"]]
    if c["typ"] == "vozova":
        d.line(pts, fill=INK + (255,), width=7); d.line(pts, fill=(222, 200, 150, 255), width=4)
    else:
        for a, b in zip(pts[:-1], pts[1:]):
            if (int(a[0] + a[1]) // 7) % 2 == 0: d.line([a, b], fill=INK + (230,), width=2)
# hrady (varianta 6): obrys jader, palisáda, kreslené hrádky
N = J("pravidla/svet/hrady_navrhy.json")["spolecne"]
for k in ("val_vnejsi", "val_vnitrni"):
    pts = [P(*p) for p in N["A"][k]]; d.line(pts, fill=(110, 80, 50, 230), width=5)
ph = N.get("palisada_hrana")
if ph:
    for k in ("zapad", "vychod"):
        pts = [P(*p) for p in ph[k]]
        for a, b in zip(pts[:-1], pts[1:]):
            d.line([a, b], fill=INK + (255,), width=2)
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); d.line([m, (m[0], m[1] - 3)], fill=INK + (255,), width=2)
def hradek(cx, cz, s, vez_vlevo=True):
    x, y = P(cx, cz)
    d.rectangle([x - s, y - s * 0.6, x + s, y + s * 0.5], fill=(214, 196, 160, 255), outline=INK + (255,), width=2)
    for i in range(-2, 3):   # cimbuří
        d.rectangle([x + i * s * 0.4 - s * 0.12, y - s * 0.78, x + i * s * 0.4 + s * 0.12, y - s * 0.6], fill=(214, 196, 160, 255), outline=INK + (255,))
    vx = x - s * 0.55 if vez_vlevo else x + s * 0.55
    d.rectangle([vx - s * 0.32, y - s * 1.6, vx + s * 0.32, y - s * 0.6], fill=(205, 186, 150, 255), outline=INK + (255,), width=2)
    d.polygon([(vx - s * 0.42, y - s * 1.6), (vx + s * 0.42, y - s * 1.6), (vx, y - s * 2.3)], fill=(110, 70, 50, 255), outline=INK + (255,))
    d.rectangle([x - s * 0.18, y + s * 0.05, x + s * 0.18, y + s * 0.5], fill=INK + (255,))
hradek(21, 2, 22, True); hradek(80, 98, 16, False)
# popisky
fB = ImageFont.truetype(FB, 46); fM = ImageFont.truetype(FM, 30); fS = ImageFont.truetype(FM, 24)
def text(x, z, t, f, barva=INK, stin=True):
    px, pz = P(x, z)
    if stin:
        bb = d.textbbox((px, pz), t, font=f, anchor="mm")
        d.rounded_rectangle([bb[0] - 6, bb[1] - 3, bb[2] + 6, bb[3] + 3], radius=6, fill=(232, 218, 182, 190))
    d.text((px, pz), t, font=f, fill=barva + (255,), anchor="mm")
text(60, -95, "Puchart", fB); text(150, 120, "zadní hrad", fS); text(-55, -5, "přední hrad", fS)
text(-260, 150, "Velička", fM, (40, 70, 110)); text(230, -260, "Koutecký potok", fM, (40, 70, 110))
text(-170, -880, "k Kyžlířovu a Potštátu", fS); text(-60, 600, "k Boňkovu", fS); text(258, -40, "vyhlídka", fS)
for t in J("pravidla/svet/voda.json")["toky"]:
    if t.get("jmeno") == "Bradelný potok":
        b = t["body"][len(t["body"]) // 2]; text(b[0] + 40, b[2], "Bradelný p.", fS, (40, 70, 110))
# větrná růžice
cx, cy, R = W - 150, Hh - 170, 85
for i in range(16):
    a = i * math.pi / 8; rr = R if i % 4 == 0 else (R * 0.6 if i % 2 == 0 else R * 0.4)
    p1 = (cx + math.sin(a) * rr, cy - math.cos(a) * rr)
    pl = (cx + math.sin(a - 0.18) * rr * 0.25, cy - math.cos(a - 0.18) * rr * 0.25); pr = (cx + math.sin(a + 0.18) * rr * 0.25, cy - math.cos(a + 0.18) * rr * 0.25)
    d.polygon([p1, pl, (cx, cy)], fill=INK + (255,)); d.polygon([p1, pr, (cx, cy)], fill=(200, 170, 120, 255), outline=INK + (255,))
d.ellipse([cx - R * 0.3, cy - R * 0.3, cx + R * 0.3, cy + R * 0.3], outline=INK + (255,), width=2)
d.text((cx, cy - R - 22), "S", font=fM, fill=INK + (255,), anchor="mm")
# měřítko 200 m
x0s, ys = 80, Hh - 90
for i in range(4):
    d.rectangle([x0s + i * 50, ys, x0s + (i + 1) * 50, ys + 10], fill=INK + (255,) if i % 2 == 0 else (230, 214, 180, 255), outline=INK + (255,))
d.text((x0s + 100, ys - 22), "200 sáhů… (200 m)", font=fS, fill=INK + (255,), anchor="mm")
# kartuš
kx, ky = 60, 50
d.rounded_rectangle([kx, ky, kx + 520, ky + 120], radius=18, fill=(232, 216, 178, 235), outline=INK + (255,), width=3)
d.text((kx + 260, ky + 45), "Panství Puchart", font=fB, fill=INK + (255,), anchor="mm")
d.text((kx + 260, ky + 92), "léta Páně 1393", font=fM, fill=INK + (255,), anchor="mm")
# rámeček
for o, w in ((14, 6), (26, 2)):
    d.rectangle([o, o, W - 1 - o, Hh - 1 - o], outline=INK + (255,), width=w)
im = im.convert("RGB").filter(ImageFilter.SMOOTH)
out = os.path.join(K, "hra/textury/ui/mapa.png"); im.save(out)
json.dump({"x0": X0, "x1": X1, "z0": Z0, "z1": Z1, "px_m": PX, "sirka": W, "vyska": Hh}, open(os.path.join(K, "hra/data/mapa.json"), "w"))
im.resize((W // 2, Hh // 2)).save(os.path.join(K, "docs/screens/mapa_nahled.jpg"), quality=85)
print(out, im.size)
