"""Textury sena (Míša 15. 11.: „seno ale fotorealistické“, předloha docs/reference/seno/kcd1_seno_staj_misa_15_11.jpg).
Zdroj: ambientCG ThatchedRoof001A 1K-JPG (CC0, https://ambientcg.com/a/ThatchedRoof001A) – Color a NormalGL.
Barva přeladěná na seno z předlohy KCD1 (medián kupy sRGB 143,130,107; světla 186,173,146 – rozbor fotky 15. 11.).
Výstup hra/textury/seno/: seno_albedo.jpg (objem), seno_normal.jpg (objem), seno_stebla.png (karty stébel RGBA,
pata dole v = 1, konec nahoře v = 0).   python3 nastroje/seno_textury.py <slozka ThatchedRoof001A_1K-JPG>"""
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
SRC = sys.argv[1]; OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hra", "textury", "seno")
N = 512
cil_median = np.array([143.0, 130.0, 107.0])       # KCD1 předloha, medián kupy
col = np.asarray(Image.open(os.path.join(SRC, "ThatchedRoof001A_1K-JPG_Color.jpg")).convert("RGB")).astype(float)
med = np.median(col.reshape(-1, 3), axis=0)
seno = np.clip((col - med) * 1.35 + cil_median, 0, 255)   # kontrast stébel o 35 % vyšší (předloha: světlé konce, tmavá hloubka)
Image.fromarray(seno.astype(np.uint8)).resize((N, N), Image.LANCZOS).save(os.path.join(OUT, "seno_albedo.jpg"), quality=90)
Image.open(os.path.join(SRC, "ThatchedRoof001A_1K-JPG_NormalGL.jpg")).convert("RGB").resize((N, N), Image.LANCZOS) \
    .save(os.path.join(OUT, "seno_normal.jpg"), quality=92)
# --- stébla: kreslí se 2× větší a zmenší (vyhlazená alfa); barva stébla = proužek fotky sena podél vláken (svislá)
S = 2 * N; rnd = random.Random(1393)
# stébla světlejší než objem: 75. percentil kupy z předlohy (167,154,129) – volná stébla chytají světlo, objem je stín mezi nimi
seno_st = np.clip((col - med) * 1.35 + np.array([167.0, 154.0, 129.0]), 0, 255)
foto = Image.fromarray(seno_st.astype(np.uint8)).resize((S, S), Image.LANCZOS)
fa = np.asarray(foto).astype(float)
rgb = np.zeros((S, S, 3)); alfa = Image.new("L", (S, S), 0); da = ImageDraw.Draw(alfa)
for i in range(150):
    x0 = rnd.uniform(0.04, 0.96) * S; delka = rnd.uniform(0.45, 1.0) * S * 0.97
    sklon = rnd.uniform(-0.22, 0.22); ohyb = rnd.uniform(-0.12, 0.12)
    w0 = rnd.uniform(5.0, 11.0); ton = rnd.uniform(0.82, 1.18); sx = rnd.randrange(S)
    body = []; kroky = 24
    for k in range(kroky + 1):
        t = k / kroky; y = S - 1 - t * delka
        x = x0 + sklon * t * delka + ohyb * (t * t) * delka
        body.append((x, y, w0 * (1.0 - 0.65 * t)))
    vrstva = Image.new("L", (S, S), 0); dv = ImageDraw.Draw(vrstva)
    for (xa, ya, wa), (xb, yb, wb) in zip(body, body[1:]):
        dv.line([(xa, ya), (xb, yb)], fill=255, width=max(1, int(round((wa + wb) * 0.5))))
    m = np.asarray(vrstva).astype(float) / 255.0
    ys = np.arange(S)[:, None] * np.ones((1, S))
    t = np.clip((S - 1 - ys) / max(delka, 1), 0, 1)
    jas = ton * (0.78 + 0.38 * t)                     # pata tmavší (stín v kupě), konec světlý (předloha)
    proužek = fa[:, (np.arange(S) + sx) % S, :] * jas[..., None]
    rgb = rgb * (1 - m[..., None]) + proužek * m[..., None]
    da.bitmap((0, 0), vrstva, fill=255)
a = np.asarray(alfa).astype(float) / 255.0
# pozadí = průměrná barva stébel (mipmapy nemají tmavý lem), alfa zvlášť
prum = (rgb * a[..., None]).sum((0, 1)) / max(a.sum(), 1)
rgb = rgb * a[..., None] + prum * (1 - a[..., None])
img = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8), "RGBA").resize((N, N), Image.LANCZOS)
img.save(os.path.join(OUT, "seno_stebla.png"), optimize=True)
print("seno: albedo median", np.median(seno.reshape(-1, 3), 0).round(), "stébla pokrytí %.2f" % a.mean())
