"""Textury sena (Míša 15. 11.: „seno ale fotorealistické“, předloha docs/reference/seno/kcd1_seno_staj_misa_15_11.jpg).
2. kolo (Míša 15. 11. přes koordinátora: „hladký objem a dlouhá rovná příliš žlutá stébla v řídkých svazcích“ → povrch kupy
= hustá spleť krátkých, zvlněných, tenkých stébel v náhodných směrech; bledá slámově béžovo-šedá, matná, tmavnutí do hloubky).
Vše vlastní kresba (numpy + PIL), bez cizích podkladů (1. kolo: ambientCG ThatchedRoof001A – „učesaný“ došek, pryč).
Barvy z předlohy KCD1 (rozbor 15. 11.: medián kupy sRGB 143,130,107; světla 186,173,146 – bledá, málo sytá).

Výstup hra/textury/seno/:
  seno_albedo.jpg, seno_normal.jpg – objem kupy (512, dlaždice bez švů): tmavé jádro, spleť stébel v náhodných směrech
  seno_stebla.png – atlas karet RGBA 1024: 4 sloupce × 2 řady buněk 256 × 512 (karta bere celou buňku, pata dole v buňce):
     řada 0 (v 0–0,5) = spleť – hustá vrstva krátkých zvlněných stébel, okraje řídnou (ležící karty těsně po povrchu)
     řada 1 (v 0,5–1) = trsy – pár tenkých stébel z paty, různé délky a sklony (trčící karty)
python3 nastroje/seno_textury.py"""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hra", "textury", "seno")
rnd = random.Random(1393)
# paleta stébel (sRGB): bledá sláma, šedobéžová, tmavší starší, nazelenale šedá (KCD1: bledé, matné, málo syté)
PALETA = [((190, 174, 140), 0.28), ((168, 154, 126), 0.27), ((140, 125, 98), 0.18), ((112, 100, 80), 0.10), ((158, 150, 122), 0.09), ((204, 186, 148), 0.08)]


def barva():
    r = rnd.random(); a = 0.0
    for c, w in PALETA:
        a += w
        if r <= a:
            t = rnd.uniform(0.9, 1.08)
            return tuple(min(255, int(v * t)) for v in c)
    return PALETA[0][0]


def steblo(x0, y0, uhel, delka, krok=8.0, vlna=None, ohyb=None):
    """body zvlněného stébla: směr se plynule stáčí (ohyb) a vlní (krátká vlna – zmačkané suché stéblo)"""
    vlna = vlna if vlna is not None else rnd.uniform(0.05, 0.22)
    ohyb = ohyb if ohyb is not None else rnd.uniform(-0.9, 0.9) / max(delka, 1)
    fz = rnd.uniform(0, 6.28); per = rnd.uniform(18, 60)
    body = [(x0, y0)]; x, y = x0, y0; s = 0.0
    while s < delka:
        a = uhel + ohyb * s + vlna * math.sin(s / per * 6.28 + fz)
        if rnd.random() < 0.025:
            uhel += rnd.uniform(-0.7, 0.7)          # zalomené stéblo
        x += math.cos(a) * krok; y += math.sin(a) * krok; s += krok
        body.append((x, y))
    return body


def orez(body, x0, x1, y0, y1, elipsa=False):
    """stéblo končí na okraji buňky (ne zarovnané podél hrany – rovné čáry na okraji karty); elipsa – okraj spleti oválný"""
    out = []; cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    for x, y in body:
        if not (x0 <= x <= x1 and y0 <= y <= y1) or (elipsa and ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 > elipsa):
            break
        out.append((x, y))
    return out


def kresli(dr_rgb, dr_a, dr_h, body, w, c, posun=(0, 0)):
    ox, oy = posun
    n = len(body) - 1
    for k, (p, q) in enumerate(zip(body, body[1:])):
        t = k / max(n, 1)
        ww = max(1, int(round(w * (1.0 - 0.45 * t))))
        jas = 0.86 + 0.22 * math.sin(t * math.pi) + rnd.uniform(-0.03, 0.03)   # uprostřed světlejší (lesk stébla)
        cc = tuple(min(255, int(v * jas)) for v in c)
        seg = [(p[0] + ox, p[1] + oy), (q[0] + ox, q[1] + oy)]
        dr_rgb.line(seg, fill=cc, width=ww)
        if dr_a is not None:
            dr_a.line(seg, fill=255, width=ww)
        if dr_h is not None:
            dr_h.line(seg, fill=int(150 + 100 * math.sin(t * math.pi)), width=ww)


# ------------------------------------------------------------------ atlas karet
S = 2048; CW, CH = S // 4, S // 2                    # kresba 2× (zmenší se – vyhlazená alfa)
rgb = Image.new("RGB", (S, S), (0, 0, 0)); alfa = Image.new("L", (S, S), 0)
dr, da = ImageDraw.Draw(rgb), ImageDraw.Draw(alfa)
for b in range(4):                                     # řada 0: spleť (vrstvy po povrchu kupy)
    x0b, y0b = b * CW, 0
    okraj = 0.07
    for i in range(230):
        # pata stébla uvnitř elipsy buňky, hustota k okraji řídne (karta nemá rovné hrany)
        for _ in range(30):
            u, v = rnd.random(), rnd.random()
            d = math.hypot((u - 0.5) / 0.5, (v - 0.5) / 0.5)
            if d < 0.97 and rnd.random() < min(1.0, (1.0 - d) / 0.4):   # rovnoměrně, jen u okraje řídne (ne hustý „lístek“)
                break
        uhel = rnd.uniform(0, 2 * math.pi)
        if rnd.random() < 0.25:                        # část podél karty (karta leží napříč i podél povrchu)
            uhel = -math.pi / 2 + rnd.uniform(-0.6, 0.6) + (math.pi if rnd.random() < 0.5 else 0)
        delka = rnd.uniform(0.15, 0.5) * CH
        body = orez(steblo(x0b + u * CW, y0b + v * CH, uhel, delka), x0b + okraj * CW, x0b + (1 - okraj) * CW, y0b + okraj * 0.5 * CH, y0b + (1 - okraj * 0.5) * CH, rnd.uniform(0.75, 1.0) ** 2)
        if len(body) < 3:
            continue
        kresli(dr, da, None, body, rnd.uniform(11.0, 17.0), barva())   # stéblo ~2 mm na kartě ~6 cm široké (1/30 buňky) – tenčí se v mipmapách slily do „lístku“
for b in range(4):                                     # řada 1: trsy (trčící stébla z paty)
    x0b, y0b = b * CW, CH
    for i in range(rnd.randint(7, 11)):
        xp = x0b + CW * rnd.uniform(0.38, 0.62); yp = y0b + CH - 4
        uhel = -math.pi / 2 + rnd.uniform(-0.32, 0.32)
        delka = rnd.uniform(0.3, 0.92) * (CH - 10)
        body = steblo(xp, yp, uhel, delka, vlna=rnd.uniform(0.03, 0.12), ohyb=rnd.uniform(-0.5, 0.5) / delka)
        body = orez(body, x0b + 0.04 * CW, x0b + 0.96 * CW, y0b + 6, y0b + CH)
        kresli(dr, da, None, body, rnd.uniform(9.0, 14.0), barva())
a = np.asarray(alfa).astype(float) / 255.0
r = np.asarray(rgb).astype(float)
prum = (r * a[..., None]).sum((0, 1)) / max(a.sum(), 1)
r = r * a[..., None] + prum * (1 - a[..., None])       # pozadí = průměr stébel (mipmapy bez tmavého lemu)
img = Image.fromarray(np.dstack([np.clip(r, 0, 255), a * 255]).astype(np.uint8), "RGBA").resize((S // 2, S // 2), Image.LANCZOS)
img.save(os.path.join(OUT, "seno_stebla.png"), optimize=True)
pokr = [a[:CH, b * CW:(b + 1) * CW].mean() for b in range(4)], [a[CH:, b * CW:(b + 1) * CW].mean() for b in range(4)]

# ------------------------------------------------------------------ objem: tmavé jádro + spleť stébel (dlaždice bez švů)
T = 1024
jadro = np.array([84.0, 75.0, 60.0])                  # stín uvnitř kupy (předloha: tmavá hloubka mezi stébly)
obr = Image.new("RGB", (T, T), tuple(int(v) for v in jadro)); vys = Image.new("L", (T, T), 40)
do, dh = ImageDraw.Draw(obr), ImageDraw.Draw(vys)
for vrstva, (n, ztm) in enumerate(((1300, 0.6), (1300, 0.78), (1000, 0.95))):   # spodní vrstvy tmavší (hloubka)
    for i in range(n):
        u, v = rnd.random() * T, rnd.random() * T
        body = steblo(u, v, rnd.uniform(0, 2 * math.pi), rnd.uniform(0.05, 0.22) * T, krok=4.0)
        c = tuple(int(x * ztm) for x in barva())
        w = rnd.uniform(1.6, 3.2)
        for ox in (-T, 0, T):                         # bez švů: kreslit i posunuté kopie
            for oy in (-T, 0, T):
                if any(-20 < x + ox < T + 20 and -20 < y + oy < T + 20 for x, y in body[::4]):
                    kresli(do, None, dh, body, w, c, (ox, oy))
alb = Image.fromarray(np.asarray(obr)).resize((512, 512), Image.LANCZOS)
alb.save(os.path.join(OUT, "seno_albedo.jpg"), quality=90)
h = np.asarray(vys.filter(ImageFilter.GaussianBlur(1.2))).astype(float) / 255.0
gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 4.0; gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 4.0
nrm = np.dstack([-gx, gy, np.ones_like(h)]); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)   # OpenGL (Y nahoru)
Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "seno_normal.jpg"), quality=92)
print("seno: objem medián", np.median(np.asarray(alb).reshape(-1, 3), 0), "pokrytí spleť", np.round(pokr[0], 2), "trsy", np.round(pokr[1], 2))
