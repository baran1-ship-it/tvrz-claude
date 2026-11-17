"""Znaky mapy (Míša 17. 11.: „chci zájmové body mít taky pod nějakým pěkným malým znakem, ale jen v pískovišti a potom
v příběhu, když to objevím“): malé piktogramy jako ruční kresba inkoustem na pergamenu (inspirace stylem mapy KCD 1 a 2 –
drobné kreslené symboly v barvě inkoustu, akcent červenou; docs/reference/kcd_mapa_znaky.md; nic se nekopíruje).
Seznam znaků, barvy a velikost z pravidla/svet/mapa_body.json zajimava.znak_sada (popis a zdroj každého znaku); kresba
každého znaku je funkce níže (tah pera s mírným chvěním a proměnnou tloušťkou, plochy šrafované nebo plné). Pod znakem
jemný světlý pergamenový lem, aby byl čitelný i na tečkách lesa (tablet 1600×1000).
Výstup hra/textury/ui/mapa_znaky/<znak>.png (RGBA, strana podle znak_sada.textura_px), náhled build/mapa_znaky_nahled.png.
Použití: python3 nastroje/mapa_znaky.py <K>"""
import json, math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

K = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..")
C = json.load(open(os.path.join(K, "pravidla/svet/mapa_body.json")))["zajimava"]["znak_sada"]
OUT = os.path.join(K, "hra/textury/ui/mapa_znaky"); os.makedirs(OUT, exist_ok=True)
S = 512                                   # kreslicí plátno (4× nadvzorkování), souřadnice znaků v −1..1
T = int(C["textura_px"])
INK = tuple(int(round(v * 255)) for v in C["barvy"]["inkoust"])
RED = tuple(int(round(v * 255)) for v in C["barvy"]["cervena"])
LEM = tuple(int(round(v * 255)) for v in C["barvy"]["lem"])


class Pero:
    """Tah pera: polyline v souřadnicích −1..1, rozdělená na krátké úseky, s hladkým chvěním kolmo k tahu a tloušťkou,
    která na začátku a konci tahu mírně slábne (kreslené perem, ne vektorem)."""
    def __init__(self, seed):
        self.r = random.Random(seed)
        self.im = Image.new("L", (S, S), 0); self.d = ImageDraw.Draw(self.im)        # inkoust
        self.im_r = Image.new("L", (S, S), 0); self.d_r = ImageDraw.Draw(self.im_r)  # červená

    def px(self, p): return ((p[0] * 0.43 + 0.5) * S, (p[1] * 0.43 + 0.5) * S)

    def tah(self, body, w=0.07, cervena=False, chveni=0.012):
        d = self.d_r if cervena else self.d
        pts = []
        for a, b in zip(body[:-1], body[1:]):
            n = max(2, int(math.dist(a, b) / 0.04))
            for i in range(n): t = i / n; pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        pts.append(body[-1])
        f1, f2, ph = self.r.uniform(2, 4), self.r.uniform(5, 8), self.r.uniform(0, 6.28)
        L = len(pts)
        for i, p in enumerate(pts):
            t = i / max(1, L - 1)
            j = chveni * (math.sin(f1 * t * 6.28 + ph) + 0.5 * math.sin(f2 * t * 6.28 + 2 * ph))
            q = pts[min(i + 1, L - 1)]; o = pts[max(i - 1, 0)]
            dx, dy = q[0] - o[0], q[1] - o[1]; dl = math.hypot(dx, dy) or 1.0
            pp = (p[0] - dy / dl * j, p[1] + dx / dl * j)
            ww = 1.15 * w * (0.78 + 0.22 * math.sin(math.pi * min(1.0, t * 1.0 + 0.0))) * self.r.uniform(0.96, 1.04)
            c = self.px(pp); r = ww * 0.43 * S / 2
            d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=255)

    def plocha(self, body, cervena=False):
        (self.d_r if cervena else self.d).polygon([self.px(p) for p in body], fill=255)

    def oblouk(self, c, r, a0, a1, w=0.07, cervena=False, n=40, ry=None):
        ry = r if ry is None else ry
        self.tah([(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)], w, cervena)

    def srafy(self, poly, krok=0.11, uhel=0.8, w=0.035):
        """Šrafování plochy (rytina) – rovnoběžky pod úhlem, oříznuté maskou mnohoúhelníku."""
        m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).polygon([self.px(p) for p in poly], fill=255)
        h = Image.new("L", (S, S), 0); hd = ImageDraw.Draw(h)
        ca, sa = math.cos(uhel), math.sin(uhel)
        for k in np.arange(-2.5, 2.5, krok):
            a = (k * ca - 3 * sa, k * sa + 3 * ca); b = (k * ca + 3 * sa, k * sa - 3 * ca)
            hd.line([self.px(a), self.px(b)], fill=255, width=max(1, int(w * 0.43 * S / 2 * 2)))
        self.im.paste(255, (0, 0), Image.fromarray(np.minimum(np.asarray(m), np.asarray(h))))


# ---------------------------------------------------------------- kresby znaků (osa y dolů, rozsah −1..1)
def kriz_dreveny(p):      # dřevěný kříž na rozcestí se stříškou (NAVOD_LES: dubový sloupek, příčka, stříška)
    p.tah([(0, -0.62), (0, 0.95)], 0.13)
    p.tah([(-0.48, -0.22), (0.48, -0.22)], 0.12)
    p.tah([(-0.36, -0.58), (0, -0.92), (0.36, -0.58)], 0.09)
    p.tah([(-0.32, 0.95), (0.32, 0.95)], 0.08)

def kriz_kamenny(p):      # smírčí kříž – nízký kamenný kříž s rozšířenými rameny, šrafovaný
    o = [(-0.16, -0.78), (0.16, -0.78), (0.13, -0.3), (0.62, -0.36), (0.62, -0.02), (0.13, -0.06), (0.2, 0.72),
         (-0.2, 0.72), (-0.13, -0.06), (-0.62, -0.02), (-0.62, -0.36), (-0.13, -0.3)]
    p.srafy(o, 0.12, 0.8)
    p.tah(o + [o[0]], 0.075)
    p.tah([(-0.7, 0.82), (-0.25, 0.74), (0.3, 0.76), (0.72, 0.84)], 0.06)   # zem

def bozi_muka(p):         # sloupek s výklenkem pod stříškou, křížek na vrcholu
    p.tah([(0, -0.06), (0, 0.92)], 0.14)
    p.tah([(-0.34, 0.92), (0.34, 0.92)], 0.08)
    p.tah([(-0.3, -0.12), (-0.3, -0.5), (0.3, -0.5), (0.3, -0.12), (-0.3, -0.12)], 0.08)
    p.plocha([(-0.14, -0.18), (-0.14, -0.36), (0, -0.44), (0.14, -0.36), (0.14, -0.18)])   # výklenek
    p.tah([(-0.5, -0.46), (0, -0.82), (0.5, -0.46)], 0.09)
    p.tah([(0, -0.82), (0, -1.0)], 0.06, True); p.tah([(-0.09, -0.93), (0.09, -0.93)], 0.05, True)

def milir(p):             # milíř: kupa šrafovaná, kouř z vrcholu
    o = [(-0.8, 0.7)] + [(math.cos(a) * 0.8, 0.7 - math.sin(a) * 0.72) for a in np.linspace(math.pi, 0, 18)]
    p.srafy(o, 0.13, 0.6)
    p.tah(o + [(-0.8, 0.7)], 0.08)
    p.tah([(0.0, -0.06), (-0.12, -0.3), (0.06, -0.52), (-0.08, -0.74), (0.08, -0.96)], 0.06, True)
    p.tah([(0.24, 0.02), (0.36, -0.2), (0.28, -0.4)], 0.05)

def smolarna(p):          # smolárna: hliněná kopule nad jámou, žlábek a hrnec (dehet)
    o = [(-0.72, 0.42)] + [(math.cos(a) * 0.55 - 0.17, 0.42 - math.sin(a) * 0.68) for a in np.linspace(math.pi, 0, 16)]
    p.tah(o + [(-0.72, 0.42)], 0.08)
    p.srafy(o, 0.14, -0.7)
    p.tah([(0.38, 0.3), (0.72, 0.5)], 0.07)                                   # žlábek
    p.tah([(0.56, 0.56), (0.62, 0.92), (0.92, 0.92), (0.96, 0.56), (0.56, 0.56)], 0.07)   # hrnec
    p.plocha([(0.62, 0.66), (0.9, 0.66), (0.88, 0.86), (0.64, 0.86)], True)
    p.tah([(-0.9, 0.48), (0.4, 0.48)], 0.06)
    p.tah([(-0.17, -0.32), (-0.28, -0.56), (-0.12, -0.78)], 0.05)

def brt(p):               # brť: kmen se dvěma větvemi, dlužka s česnem, včely
    p.tah([(-0.08, 0.95), (-0.04, 0.2), (0.0, -0.95)], 0.16)
    p.tah([(0.0, -0.4), (0.42, -0.78)], 0.08); p.tah([(-0.03, -0.1), (-0.46, -0.48)], 0.08)
    p.tah([(-0.55, 0.95), (0.45, 0.95)], 0.06)
    p.plocha([(0.07, 0.0), (0.33, 0.0), (0.33, 0.42), (0.07, 0.42)])
    p.plocha([(0.15, 0.18), (0.25, 0.18), (0.25, 0.26), (0.15, 0.26)], True)
    for c in [(0.56, -0.1), (0.74, 0.12), (0.62, 0.34)]:
        p.oblouk(c, 0.055, 0, 6.3, 0.05, True, 10)

def studanka(p):          # studánka: stříška na dvou sloupcích nad kamennou obrubou pramene, voda a kapka červeně
    p.tah([(-0.66, -0.4), (0.0, -0.92), (0.66, -0.4)], 0.1)
    p.tah([(-0.44, -0.52), (-0.44, 0.08)], 0.07); p.tah([(0.44, -0.52), (0.44, 0.08)], 0.07)
    p.oblouk((0, 0.18), 0.78, 0.0, math.pi, 0.09, ry=0.6)                    # obruba (miska) pramene
    p.tah([(-0.8, 0.2), (0.8, 0.2)], 0.07)
    p.tah([(-0.5 + 0.17 * i, 0.4 + 0.05 * math.sin(i * 1.9)) for i in range(7)], 0.06, True)
    p.plocha([(0, -0.38), (0.11, -0.14), (0.0, -0.04), (-0.11, -0.14)], True)   # kapka
    p.oblouk((0, -0.12), 0.1, 0, 6.3, 0.04, True, 12)

def lom(p):               # lom: stupňovitá skalní stěna (šrafy) a krumpáč
    o = [(-0.9, 0.85), (-0.9, -0.55), (-0.45, -0.55), (-0.45, -0.1), (0.05, -0.1), (0.05, 0.35), (0.5, 0.35), (0.5, 0.85)]
    p.srafy(o, 0.12, 0.0)
    p.tah(o, 0.08)
    p.tah([(-0.95, 0.85), (0.95, 0.85)], 0.07)
    p.tah([(0.3, -0.85), (0.78, 0.1)], 0.08)                                  # násada krumpáče
    p.tah([(0.0, -0.58), (0.36, -0.86), (0.82, -0.72)], 0.09)                 # želízko

def dul(p):               # štola (důl): kladívko a želízko zkřížené (Schlägel und Eisen) nad ústím štoly
    p.oblouk((0, 0.92), 0.62, math.pi, 2 * math.pi, 0.08, ry=0.5)
    p.plocha([(-0.4, 0.92)] + [(math.cos(a) * 0.4, 0.92 - math.sin(a) * 0.3) for a in np.linspace(math.pi, 0, 12)])
    for sg in (-1, 1):
        a, b = (sg * 0.62, -0.95), (-sg * 0.45, 0.3)
        p.tah([a, b], 0.08)
        hl = (a[0] - sg * 0.04, a[1] + 0.04); kd = (0.22, 0.22 * sg)
        p.tah([(hl[0] - kd[0], hl[1] + kd[1]), (hl[0] + kd[0], hl[1] - kd[1])], 0.17 if sg < 0 else 0.1)

def mlyn(p):              # mlýn: vodní kolo s lopatkami nad vlnkou
    c = (0, -0.1); r = 0.66
    p.oblouk(c, r, 0, 6.3, 0.08); p.oblouk(c, 0.14, 0, 6.3, 0.07, n=14)
    for k in range(8):
        a = k * math.pi / 4
        p.tah([(c[0] + 0.14 * math.cos(a), c[1] + 0.14 * math.sin(a)), (c[0] + r * math.cos(a), c[1] + r * math.sin(a))], 0.05)
        q = (c[0] + r * math.cos(a), c[1] + r * math.sin(a)); t = (-math.sin(a), math.cos(a))
        p.tah([q, (q[0] + 0.16 * math.cos(a) + 0.06 * t[0], q[1] + 0.16 * math.sin(a) + 0.06 * t[1])], 0.08)
    p.tah([(-0.95 + 0.27 * i, 0.86 + 0.06 * math.sin(i * 2.2)) for i in range(8)], 0.06, True)

def ves(p):               # ves: dvě chalupy se sedlovou střechou
    for dx, s in ((-0.4, 0.8), (0.42, 0.62)):
        y0 = 0.82; h = 0.62 * s; w = 0.42 * s
        p.tah([(dx - w, y0), (dx - w, y0 - h), (dx + w, y0 - h), (dx + w, y0)], 0.07)
        roof = [(dx - w - 0.1, y0 - h), (dx, y0 - h - 0.55 * s), (dx + w + 0.1, y0 - h)]
        p.srafy(roof + [roof[0]], 0.1, 1.2); p.tah(roof + [roof[0]], 0.08)
        p.plocha([(dx - 0.08 * s, y0), (dx - 0.08 * s, y0 - 0.28 * s), (dx + 0.08 * s, y0 - 0.28 * s), (dx + 0.08 * s, y0)])
    p.tah([(-0.95, 0.84), (0.95, 0.84)], 0.06)

def hrad(p):              # hrad: věž s cimbuřím a brankou, praporec červeně
    p.tah([(-0.42, 0.9), (-0.42, -0.42), (0.42, -0.42), (0.42, 0.9)], 0.09)
    p.tah([(-0.52, -0.42), (-0.52, -0.66), (-0.3, -0.66), (-0.3, -0.52), (-0.1, -0.52), (-0.1, -0.66), (0.1, -0.66),
           (0.1, -0.52), (0.3, -0.52), (0.3, -0.66), (0.52, -0.66), (0.52, -0.42)], 0.07)
    p.plocha([(-0.15, 0.9), (-0.15, 0.55)] + [(math.cos(a) * 0.15, 0.55 - math.sin(a) * 0.15) for a in np.linspace(math.pi, 0, 8)] + [(0.15, 0.9)])
    p.tah([(0, -0.1), (0, 0.15)], 0.08)
    p.tah([(0, -0.66), (0, -1.0)], 0.05); p.plocha([(0, -1.0), (0.4, -0.92), (0, -0.82)], True)
    p.tah([(-0.8, 0.92), (0.8, 0.92)], 0.06)

def krcma(p):             # krčma: džbán s uchem a víčkem
    o = [(-0.36, -0.5), (-0.46, 0.0), (-0.42, 0.62), (-0.3, 0.86), (0.3, 0.86), (0.42, 0.62), (0.46, 0.0), (0.36, -0.5)]
    p.tah(o, 0.09); p.tah([(-0.44, -0.56), (0.44, -0.56)], 0.1)
    p.oblouk((0.5, 0.12), 0.3, -1.4, 1.4, 0.08)
    p.srafy(o + [o[0]], 0.13, 0.9)
    p.tah([(-0.36, 0.1), (0.36, 0.1)], 0.05, True)

def kovarna(p):           # kovárna: kovadlina a kladivo
    o = [(-0.86, -0.12), (0.62, -0.12), (0.86, -0.28), (0.62, 0.12), (0.26, 0.2), (0.3, 0.5), (0.5, 0.82), (-0.5, 0.82),
         (-0.3, 0.5), (-0.26, 0.2), (-0.62, 0.12)]
    p.plocha(o); p.tah(o + [o[0]], 0.05)
    p.tah([(-0.1, -0.24), (0.42, -0.9)], 0.08)
    p.tah([(0.24, -0.98), (0.62, -0.7)], 0.17)
    for c in [(-0.5, -0.42), (-0.32, -0.6)]:
        p.tah([c, (c[0] - 0.08, c[1] - 0.1)], 0.05, True)

def hajovna(p):           # hájovna: smrk a srub
    p.tah([(-0.42, 0.95), (-0.42, -1.0)], 0.06)
    for i, y in enumerate((-0.7, -0.35, 0.0, 0.35)):
        w = 0.22 + 0.13 * i
        p.tah([(-0.42 - w, y + 0.28), (-0.42, y - 0.12), (-0.42 + w, y + 0.28)], 0.08)
    p.tah([(0.12, 0.92), (0.12, 0.42), (0.86, 0.42), (0.86, 0.92)], 0.07)
    p.tah([(0.02, 0.44), (0.49, 0.05), (0.96, 0.44)], 0.08)
    p.tah([(-0.95, 0.94), (0.98, 0.94)], 0.06)


def znak(jmeno, seed):
    p = Pero(seed); globals()[jmeno](p)   # kresba = funkce se jménem znaku
    a_i = np.asarray(p.im, float) / 255; a_r = np.asarray(p.im_r, float) / 255
    a = np.maximum(a_i, a_r)
    # světlý lem pod kresbou (pergamen, ne bílá) – rozšířená a rozmazaná maska
    lem = Image.fromarray((a * 255).astype("uint8")).filter(ImageFilter.MaxFilter(int(S * float(C["lem_sirka"])) | 1)).filter(ImageFilter.GaussianBlur(S * 0.02))
    al = np.asarray(lem, float) / 255 * float(C["barvy"]["lem"][3])
    rgb = np.zeros((S, S, 3)); ink = np.array(INK, float) / 255; red = np.array(RED, float) / 255; lm = np.array(LEM[:3], float) / 255
    # inkoust není úplně plný (papír prosvítá) – jemný šum krytí jako u pera
    rs = np.random.RandomState(seed); sum_ = 0.9 + 0.1 * rs.rand(S // 16, S // 16).repeat(16, 0).repeat(16, 1)
    ai = a_i * sum_; ar = a_r * (1 - ai)
    out_a = ai + ar + al * (1 - ai - ar)
    rgb = (ink * ai[..., None] + red * ar[..., None] + lm * (al * (1 - ai - ar))[..., None]) / np.maximum(out_a, 1e-6)[..., None]
    im = Image.fromarray(np.dstack([rgb * 255, out_a * 255]).clip(0, 255).astype("uint8"), "RGBA")
    return im.resize((T, T), Image.LANCZOS)


if __name__ == "__main__":
    jm = list(C["znaky"].keys()); nah = Image.new("RGBA", (len(jm) * (T + 24) + 24, T * 2 + 60), (222, 200, 160, 255))
    pg = os.path.join(K, "hra/textury/ui/mapa.png")
    if os.path.exists(pg):   # náhled na skutečném pergamenu mapy (výřez s lesem)
        bg = Image.open(pg).convert("RGBA")
        for x0 in range(0, nah.width, 1000): nah.paste(bg.crop((300, 300, 1300, 300 + nah.height)), (x0, 0))
    for i, j in enumerate(jm):
        im = znak(j, 1393 + i)
        im.save(os.path.join(OUT, j + ".png"))
        nah.alpha_composite(im, (24 + i * (T + 24), 12))
        m = im.resize((int(C["velikost_px"]), int(C["velikost_px"])), Image.LANCZOS)   # skutečná velikost na tabletu
        nah.alpha_composite(m, (24 + i * (T + 24) + (T - m.width) // 2, T + 30))
    os.makedirs(os.path.join(K, "build"), exist_ok=True)
    nah.save(os.path.join(K, "build/mapa_znaky_nahled.png"))
    print("MAPA_ZNAKY %d znaků → %s (%d px), náhled build/mapa_znaky_nahled.png" % (len(jm), OUT, T))
