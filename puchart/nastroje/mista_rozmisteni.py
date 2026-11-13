"""Stavby nových míst (pravidla/svet/mista.json, Míša 11. 11. schválila polohy): rozmístění usedlostí a terén pod nimi.
Pořadí stavby světa: terén → cesty → STAVBY → voda → vegetace (krok po cesty.py, před teren_dlazdice.py).
- ves (typ „ves“): usedlosti podél cesty, která místem vede – dům štítem (+z modelu) do ulice jako ve vsi Havrana
  (svet.gd VES_STARE: „štít do návsi, vstup +x“), rozestup usedlostí rozestup_m, odstup od osy cesty odstup_m..odstup_max_m;
  jen kde je pod budovami malý sklon (max_prevyseni_m), parcela mimo cesty a toky a nepřekrývá sousedy.
- samota (krčma, hájovna): nejbližší vhodné místo k bodu stred, štít k nejbližší vozové cestě.
Usedlost (mista.json usedlosti, Havran blender/vesnice.py layout/_dvorce/build + lokace.json ves.dvorec): dům, dvůr na
straně vchodu (+x modelu), zahrádka na druhé straně, stodola napříč za dvorem, kůlna, sad (humno), ploty, vrata,
ovocné stromy, lány za humny; každá usedlost z vlastního semínka (semeno + pořadí) – žádné dvě stejné. Vybavení (vozy, sudy,
kurník…) se nestaví (Míša 12. 11. večer). Před každým vstupem (dveře domu z modelu, vrata stodoly/kůlny) pruh bez stavby,
plotu a stromu (usedlosti.vstupy); vyšlapané plochy a cestičky (usedlosti.vyslapano) pro stavby_vegetace.py.
Terén: plošina pod podezdívkou domů a pod hospodářskými stavbami (výška = medián terénu pod půdorysem) s plynulým
přechodem prechod_m (žádné schody, žádné kopání půl kopce). Výška drobností, plotů a stromů z výsledného terénu.
Výstup: hra/data/mista_stavby.json (stavby pro hru – hlavni.gd _mista domy, ves.gd zbytek; půdorysy, dvory, zahrady,
sady a pole pro stavby_vegetace.py) a mřížka terénu <out>.npy.
  python3 mista_rozmisteni.py <vstup_prefix> <vystup_prefix> <koren>"""
import sys, json, math, os, random
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, LineString, Point, MultiPoint
from shapely.ops import unary_union
from PIL import Image
pre, out, K = sys.argv[1:4]
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json"))
P = json.load(open(K + "/pravidla/svet/svet.json"))["pocatek"]
MI = json.load(open(K + "/pravidla/svet/mista.json")); R = MI["rozmisteni"]; U = MI["usedlosti"]
C = json.load(open(K + "/pravidla/svet/cesty_puchart.json"))
V = json.load(open(K + "/pravidla/svet/voda.json"))["toky"]
ny, nx = H.shape; xh0 = M["x0"] - P["X"]; zh0 = -(M["y1"] - P["Y"])
Y = H - P["H"]
def ij(x, z): return int(round(z - zh0)), int(round(x - xh0))
def vys(x, z):
    r, c = ij(x, z); return Y[min(max(r, 0), ny - 1), min(max(c, 0), nx - 1)]
def vys_b(x, z):   # bilineárně (ploty, drobnosti, stromy)
    fr, fc = z - zh0, x - xh0; r0, c0 = int(math.floor(fr)), int(math.floor(fc)); tr, tc = fr - r0, fc - c0
    r0 = min(max(r0, 0), ny - 2); c0 = min(max(c0, 0), nx - 2)
    return float((Y[r0, c0] * (1 - tc) + Y[r0, c0 + 1] * tc) * (1 - tr) + (Y[r0 + 1, c0] * (1 - tc) + Y[r0 + 1, c0 + 1] * tc) * tr)
# překážky: osy cest (bez spojek přes brody) a toky
osy = []
for c in C["cesty"]:
    if c.get("osa") and not c.get("jen_maska"): osy.append((c["id"], np.array(c["osa"], float)[:, :2], c["typ"]))
toky = [np.array(t["body"])[:, [0, 2]] for t in V]
def hust(o, k=1.0):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]; s = np.arange(0, d[-1] + 1e-6, k)
    return np.c_[np.interp(s, d, o[:, 0]), np.interp(s, d, o[:, 1])]
CEST = np.vstack([hust(o) for _, o, _ in osy]); TOK = np.vstack([hust(t) for t in toky])
HLAV = np.vstack([hust(o) for _, o, t in osy if t in ("vozova", "hrebenova")])   # ulice: štít k vozové / hřebenové cestě, ne k pěšině
kc = cKDTree(CEST); kt = cKDTree(TOK); kh = cKDTree(HLAV)
CESTY_L = unary_union([LineString(o) for _, o, _ in osy]); TOKY_L = unary_union([LineString(t) for t in toky])
PUD = dict(MI["pudorysy"])   # model -> [hw (x), z_b, z_f, pod] podle Havrana DUM_MER
for m_, (dl, hl) in MI["modely"]["hospodarske"]["rozmery"].items():
    PUD[m_] = [dl / 2, -hl / 2, hl / 2, 0.0]   # předměty Havrana: počátek ve středu půdorysu na zemi
# stanoviště (lány jen na nelesní půdě): originál před stavbami (stavby_vegetace.py ho ukládá do build/)
_st_p = K + "/build/stanoviste_pred_stavbami.png"
STJ = json.load(open(K + "/hra/data/stanoviste.json"))
ST = np.array(Image.open(_st_p if os.path.exists(_st_p) else K + "/hra/data/stanoviste.png")); ST = ST[..., 0] if ST.ndim == 3 else ST
def sklon(x, z, b=5.0):   # tan sklonu na základně 2b (jak ho vidí orač – plochy.json sklon_zaklad_m)
    return math.hypot(vys_b(x + b, z) - vys_b(x - b, z), vys_b(x, z + b) - vys_b(x, z - b)) / (2 * b)
def trida(x, z):
    c = int((x - STJ["x0_hra"]) / STJ["krok_m"]); r = int((z - STJ["z0_hra"]) / STJ["krok_m"])
    if 0 <= r < ST.shape[0] and 0 <= c < ST.shape[1]: return STJ["tridy"][ST[r, c]]
    return "nic"

# ---------------------------------------------------------------- geometrie usedlosti (lokální rámec domu)
class Ramec:
    """u = osa domu k ulici (+z modelu, štít), v = na stranu vchodu (+x modelu); počátek = střed domu (Havran Frame au/av)."""
    def __init__(s, x, z, yaw):
        s.x, s.z, s.yaw = x, z, yaw; s.au = np.array([math.sin(yaw), math.cos(yaw)]); s.av = np.array([math.cos(yaw), -math.sin(yaw)])
    def w(s, u, v): return np.array([s.x, s.z]) + s.au * u + s.av * v
    def poly(s, u0, u1, v0, v1): return Polygon([s.w(u0, v0), s.w(u0, v1), s.w(u1, v1), s.w(u1, v0)])

def rohy(x, z, yaw, m, okraj=0.0):
    hw, zb, zf = PUD[m][0] + okraj, PUD[m][1] - okraj, PUD[m][2] + okraj
    cs, sn = math.cos(yaw), math.sin(yaw)
    # model: +x vstup, +z štít; svět: otočení kolem Y o yaw (Godot: x' = x cos + z sin, z' = -x sin + z cos)
    return [[x + px * cs + pz * sn, z - px * sn + pz * cs] for px, pz in ((-hw, zb), (hw, zb), (hw, zf), (-hw, zf))]

def body_pudorysu(x, z, yaw, m, okraj=0.0, krok=1.0):
    hw, zb, zf = PUD[m][0] + okraj, PUD[m][1] - okraj, PUD[m][2] + okraj
    cs, sn = math.cos(yaw), math.sin(yaw); out_ = []
    for px in np.r_[np.arange(-hw, hw, krok), hw]:
        for pz in np.r_[np.arange(zb, zf, krok), zf]: out_.append((x + px * cs + pz * sn, z - px * sn + pz * cs))
    return np.array(out_)

VS = U["vstupy"]; VY = U["vyslapano"]
def _dvere_domu():
    """vnější dveře domů z modelu (uzly <Dům>_Dvere_* na obvodové stěně): model -> [(x, z, strana ±1)]"""
    import struct
    f = open(K + "/hra/" + MI["modely"]["domy"]["soubor"][len("res://"):], "rb").read()
    j = json.loads(f[20:20 + struct.unpack("<I", f[12:16])[0]]); out_ = {}
    for nd in j["nodes"]:
        jm = nd.get("name", ""); m_ = jm.split("_Dvere")[0]
        if "_Dvere" not in jm or m_ not in MI["pudorysy"] or "translation" not in nd: continue
        tx, _, tz = nd["translation"]
        # uzel dveří = pant na kraji otvoru (13. 11.: trasy a rovina před vchodem mířily na zárubeň) – střed otvoru = střed křídla
        if "mesh" in nd:
            acc_ = j["accessors"][j["meshes"][nd["mesh"]]["primitives"][0]["attributes"]["POSITION"]]
            tz = tz + (acc_["min"][2] + acc_["max"][2]) / 2
        if abs(tx) > MI["pudorysy"][m_][0] - 0.3: out_.setdefault(m_, []).append((tx, tz, 1.0 if tx > 0 else -1.0))
    return out_
DVERE = _dvere_domu()
_ROT = lambda yaw, px, pz: (px * math.cos(yaw) + pz * math.sin(yaw), -px * math.sin(yaw) + pz * math.cos(yaw))   # model -> svět (jako rohy)
def vstupy_stavby(m, x, z, yaw):
    """vstupy stavby ve světě: [{druh, c, n (ven), w, pred_poly}] – pred_poly = pruh VS.pred_m před vstupem, o okraj_m širší"""
    loc = []
    if m in DVERE:
        for tx, tz, sg in DVERE[m]: loc.append(("dvere", (sg * PUD[m][0], tz), (sg, 0.0), VS["dvere_sirka_m"]))
    elif m in VS["hospodarske"]:
        e = VS["hospodarske"][m]; sz = PUD[m][2] if e["strana"] == "+z" else PUD[m][1]
        loc.append(("vrata", (0.0, sz), (0.0, 1.0 if e["strana"] == "+z" else -1.0), 2 * PUD[m][0] if e["sirka_m"] == "cela" else float(e["sirka_m"])))
    out_ = []
    for druh, (px, pz), (nx_, nz_), w in loc:
        dx, dz = _ROT(yaw, px, pz); nwx, nwz = _ROT(yaw, nx_, nz_); sx, sz_ = -nwz, nwx
        c = np.array([x + dx, z + dz]); n_ = np.array([nwx, nwz]); s_ = np.array([sx, sz_]); hw_ = w / 2 + VS["okraj_m"]
        pred = Polygon([c + s_ * hw_ + n_ * 0.05, c - s_ * hw_ + n_ * 0.05, c - s_ * hw_ + n_ * VS["pred_m"], c + s_ * hw_ + n_ * VS["pred_m"]])
        out_.append({"stavba": m, "druh": druh, "c": c, "n": n_, "w": w, "pred_poly": pred})
    return out_

def stavba_ok(x, z, yaw, m, od_toku=None):
    """budova: malé převýšení pod půdorysem, odstup od os cest a toků; vrací (výška plošiny, převýšení) nebo None"""
    b = body_pudorysu(x, z, yaw, m, R["okraj_m"])
    h = np.array([vys(p[0], p[1]) for p in b])
    if h.max() - h.min() > (R["max_prevyseni_m"] if m in MI["pudorysy"] else R["max_prevyseni_hospodarske_m"]): return None
    if kc.query(b)[0].min() < R["od_cesty_m"] or kt.query(b)[0].min() < (R["od_toku_m"] if od_toku is None else od_toku): return None
    return float(np.median(h)), float(h.max() - h.min())

def los(rng, tab):
    """vážený los z {klíč: váha}"""
    if not tab: return None
    k = list(tab); w = [float(tab[a]) for a in k]; t = rng.random() * sum(w)
    for a, ww in zip(k, w):
        t -= ww
        if t <= 0: return a
    return k[-1]
def roz(rng, ab): return rng.uniform(float(ab[0]), float(ab[1]))
def rozi(rng, ab): return rng.randint(int(ab[0]), int(ab[1]))

PL = U["ploty"]
def plot_ok(a, b):
    ln = LineString([a, b])
    return ln.distance(CESTY_L) >= PL["od_cesty_m"] and ln.distance(TOKY_L) >= PL["od_toku_m"]

DBG = os.environ.get("MISTA_DBG")
def usedlost(x, z, yaw, m, typ, rng, zabrano):
    r_ = _usedlost(x, z, yaw, m, typ, rng, zabrano)
    if DBG and typ == DBG and isinstance(r_, str): print("  ", round(x, 1), round(z, 1), r_)
    return r_ if isinstance(r_, dict) else None
def _usedlost(x, z, yaw, m, typ, rng, zabrano):
    """Jedna usedlost kolem domu m (střed x, z, natočení yaw). Vrací slovník nebo None (nevejde se)."""
    T = U["typy"][typ]; F = Ramec(x, z, yaw)
    hw, zb, zf = PUD[m][0], PUD[m][1], PUD[m][2]
    pz = roz(rng, T["predzahradka_m"]); dv = roz(rng, T["dvur_m"]); za = roz(rng, T["zahrada_m"])
    uf = zf + pz + 0.05                       # uliční plot (Havran: v linii štítu, front = L/2 + 0.05)
    vL, vR = -hw - za, hw + dv                # boky parcely: zahrada (−v), dvůr (+v)
    stavby = [(m, x, z, yaw)]; hosp = []; drobne = []; ploty = []; brany = []; stromy = []
    # stodola napříč za dvorem (Havran _dvorce: od boku zahrady od_boku_m, za domem za_domem_m, vrata k domu)
    zd = roz(rng, T["za_domem_m"]); sd = los(rng, T["stodola"]); kol = los(rng, T["kolna"])
    ub_line = zb - zd                          # přední hrana stodoly (k domu)
    zadni = zb - 1.0                           # zadní hrana dvora bez stodoly
    v_kol = None
    kl, kh = MI["modely"]["hospodarske"]["rozmery"]["kolna"]
    if sd and T.get("stodola_poloha") == "k_ceste":
        # stáj vraty (+z modelu) k cestě jako dům, odstup_staje_m od boku domu, čelo v linii štítu (Míša 13. 11.: „stáj bych
        # otočil k cestě, boční budovy kousek dál“; KCD1 web_kcd1_broken_wheel_hostinec: stáje stranou, otevřené k cestě)
        sl, sh = MI["modely"]["hospodarske"]["rozmery"][sd]
        hosp.append([sd, *F.w(zf - sh / 2, T.get("stodola_strana", 1) * (hw + T["odstup_staje_m"] + sl / 2)), yaw])
    elif sd and T.get("stodola_poloha") == "bok_dvora":
        # stáj bokem do dvora (krčma u silnice: za domem svah – stavení v řadě podél cesty, vrata do dvora)
        sl, sh = MI["modely"]["hospodarske"]["rozmery"][sd]
        hosp.append([sd, *F.w(min(uf - 1.0 - sl / 2, (zb + zf) / 2), vR - 0.4 - sh / 2), yaw - math.pi / 2])
    elif sd:
        sl, sh = MI["modely"]["hospodarske"]["rozmery"][sd]
        su = ub_line - sh / 2; sv = vL + T["od_boku_m"] + sl / 2
        if kol == "zadna": sv = vR - T["od_boku_m"] - sl / 2      # stodola od boku dvora, kůlna k zahradě
        hosp.append([sd, *F.w(su, sv), yaw]); zadni = ub_line - sh
        v_kol = (sv + sl / 2 + T["mezera_m"], vR - 0.5) if kol != "zadna" else (vL + 0.5, sv - sl / 2 - T["mezera_m"])
    if kol in ("za_dvorem", "zadna") and sd and v_kol and v_kol[1] - v_kol[0] >= kl - 0.2:
        kv = (v_kol[0] + v_kol[1]) / 2; ku = ub_line - kh / 2
        hosp.append(["kolna", *F.w(ku, kv), yaw])
    elif kol == "misto_zahrady":
        # kůlna na vozy hostů otevřená k cestě, na straně zahrady (krčma: zájezdní dvůr, reserse_mosty_krcma.md)
        hosp.append(["kolna", *F.w(uf - 0.6 - kh / 2, -hw - T.get("odstup_kolny_m", 0.8) - kl / 2), yaw])
    elif kol == "bok_dvora_u_domu":
        # kůlna bokem do dvora, odstup_kolny_m od boku domu, čelo v linii štítu (krčma 13. 11.: za dvorem tok – od_toku_m)
        ks_ = T.get("kolna_strana", 1)   # strana kůlny u domu (krčma: stáj u dvora, kůlna na druhém boku)
        hosp.append(["kolna", *F.w(zf - kl / 2, ks_ * (hw + T["odstup_kolny_m"] + kh / 2)), yaw - ks_ * math.pi / 2])
    elif kol == "bok_dvora" or (kol and not sd):
        # kůlna bokem do dvora (otevřenou stranou +z do dvora, KCD1 ves_1 vpravo), podél vnějšího boku dvora
        if dv >= kh + 4.0:
            ku = min(uf - 1.0 - kl / 2, (zb + zf) / 2); kv = vR - 0.4 - kh / 2
            hosp.append(["kolna", *F.w(ku, kv), yaw - math.pi / 2])
    usad = zadni - 0.6                       # začátek humna / sadu
    ubk = usad - roz(rng, T["sad_m"])         # zadní plot
    parc = F.poly(ubk, uf, vL, vR)
    if parc.distance(CESTY_L) < 1.0: return "parcela na cestě"
    if parc.distance(TOKY_L) < PL["od_toku_m"]: return "parcela u toku"
    if parc.buffer(R["mezi_usedlostmi_m"]).intersects(zabrano): return "soused"
    # budovy: sklon a odstupy (dům už prověřen) a volné vstupy (žádná stavba před dveřmi domu ani před vraty jiné stavby)
    def _hosp_ok(h_, q, yw):
        if not stavba_ok(q[0], q[1], yw, h_[0], R.get("od_toku_hospodarske_m")): return False   # hospodářské blíž k vodě (Míša 13. 11.: 8 m)
        ja = Polygon(rohy(q[0], q[1], yw, h_[0], 0.3))
        for o_ in [(m, x, z, yaw)] + [g_ for g_ in hosp if g_ is not h_]:
            if any(ja.intersects(v_["pred_poly"]) for v_ in vstupy_stavby(*o_)): return False
            if any(Polygon(rohy(o_[1], o_[2], o_[3], o_[0], 0.3)).intersects(v_["pred_poly"]) for v_ in vstupy_stavby(h_[0], q[0], q[1], yw)): return False
        return True
    for h_ in list(hosp):
        if not _hosp_ok(h_, h_[1:3], h_[3]):
            if T.get("povinne", True): return "svah/odstup " + h_[0]
            # samota: posunout v rámci dvora (po 1 m, nejbližší první), jinak bez ní (poloha domu je doložená, má přednost)
            jine = unary_union([Polygon(rohy(o_[1], o_[2], o_[3], o_[0], 0.5)) for o_ in [(m, x, z, yaw)] + hosp if o_ is not h_])
            kand = sorted(((du, dv_) for du in range(-6, 7) for dv_ in range(-4, 5)), key=lambda a: abs(a[0]) + abs(a[1]))
            kand = [(du, dv_, yw) for yw in (h_[3], yaw, yaw + math.pi / 2, yaw - math.pi / 2) for du, dv_ in kand]
            for du, dv_, yw in kand:
                q = np.array(h_[1:3]) + F.au * du + F.av * dv_
                if _hosp_ok(h_, q, yw) and not Polygon(rohy(q[0], q[1], yw, h_[0], 0.5)).intersects(jine) \
                        and Polygon(rohy(q[0], q[1], yw, h_[0])).within(parc):
                    h_[1], h_[2], h_[3] = float(q[0]), float(q[1]), yw; break
            else:
                hosp.remove(h_)
    # ---- ploty (Havran build: laťový do ulice od rohu chalupy, vrata na dvorní straně, branka na zahradní; ohrada kolem)
    p_ul = los(rng, T["plot_ulice"]); p_bok = los(rng, T["plot_bok"]); p_za = los(rng, T["plot_zahrada"])
    bw = PL["kryta_vrata"]["sirka_m"]; br = los(rng, T["brana"])
    v_br = hw + 0.12 + rng.uniform(1.4, max(1.5, dv - bw - 1.2)) + bw / 2     # střed vrat
    if any(h_[0] == "kolna" and abs(h_[3] - (yaw - math.pi / 2)) < 0.01 for h_ in hosp):
        v_br = min(v_br, vR - 0.4 - kh - bw / 2 - 0.3)
    u_ul = uf
    ul_dv = [(hw + 0.12, v_br - bw / 2), (v_br + bw / 2, vR)]
    ul_za = [(vL, -hw - 0.12)] if pz < 0.3 else [(vL, hw + 0.12)]
    if pz >= 0.3: ul_dv = [(ul_za[0][1], v_br - bw / 2), (v_br + bw / 2, vR)]; ul_za = [(vL, -hw - 0.12)]
    # branka v zahradní části uličního plotu
    branka = rng.random() < T["branka_p"] and (ul_za[0][1] - ul_za[0][0]) > 2.0
    seg_za = ul_za
    if branka:
        a0, a1 = ul_za[0]; bv = a1 - 0.7 - PL["branka"]["sirka_m"]
        seg_za = [(a0, bv), (bv + PL["branka"]["sirka_m"], a1)]
        brany.append({"druh": "branka", "a": list(F.w(u_ul, bv)), "b": list(F.w(u_ul, bv + PL["branka"]["sirka_m"]))})
    for v0, v1 in ul_dv + (seg_za if pz < 0.3 else []):
        if v1 - v0 > 0.3: ploty.append([p_ul, F.w(u_ul, v0), F.w(u_ul, v1)])
    if pz >= 0.3:
        for v0, v1 in seg_za:
            if v1 - v0 > 0.3: ploty.append([p_ul, F.w(u_ul, v0), F.w(u_ul, v1)])
        # předzahrádka: uliční plot končí v linii boku domu o pz před štítem – bez navázání zůstala díra mezi koncem plotu
        # a nárožím (Míša 13. 11., foto z tabletu 40db6a53: „ploty nenavazují na domy, jsou tam díry“); plot se vrací podél
        # boku k nároží domu (Havran vesnice.py build: plot „od rohu chalupy“; KCD2 ref_kcd2_ves_ulice, ref_kcd2_ves_plot_cesta:
        # plot navazuje na roh stavení, žádná mezera)
        for sv_ in (-1.0, 1.0):
            ploty.append([p_ul, F.w(u_ul, sv_ * (hw + 0.12)), F.w(zf + PL["k_narozi_m"], sv_ * (hw + 0.12))])
    if br: brany.append({"druh": "kryta_vrata" if br == "krytá" else "vrata", "a": list(F.w(u_ul, v_br - bw / 2)), "b": list(F.w(u_ul, v_br + bw / 2))})
    else: brany[:] = [b_ for b_ in brany if b_["druh"] != "branka"]   # bez plotů (krčma): ani branka
    # boky a záda: zahrada proutím (KCD2 ref_kcd2_zahrada_plot), dvůr a humno ohradou
    u_zah = zb + 0.3                            # zadní plot zahrádky u zadního štítu
    ploty.append([p_za, F.w(uf, vL), F.w(u_zah, vL)])
    ploty.append([p_za, F.w(u_zah, vL), F.w(u_zah, -hw - 0.12)])
    ploty.append([p_bok, F.w(u_zah, vL), F.w(ubk, vL)])
    ploty.append([p_bok, F.w(uf, vR), F.w(ubk, vR)])
    ploty.append([p_bok, F.w(ubk, vR), F.w(ubk, vL)])
    ploty[:] = [p_ for p_ in ploty if p_[0]]   # typ plotu bez možností (mista.json {}) = plot není (krčma: Míša 12. 11. večer)
    for p_ in ploty + [[None, b_["a"], b_["b"]] for b_ in brany]:
        if not plot_ok(p_[1], p_[2]): return "plot u cesty/toku"
    # vstupy staveb: před dveřmi a vraty nesmí stát plot (Míša 12. 11. večer: „vůz nebo kurník u dveří nemá smysl, zavazí“)
    vst = [v_ for o_ in [(m, x, z, yaw)] + hosp for v_ in vstupy_stavby(*o_)]
    for p_ in ploty:
        if any(LineString([p_[1], p_[2]]).intersects(v_["pred_poly"]) for v_ in vst): return "plot před vstupem"
    # vybavení (vozy, sudy, hranice, záhony…) se nestaví – Míša 12. 11. večer: „vymaž všechny vlastní modely vybavení“
    kolna_bok = any(h_[0] == "kolna" and abs(h_[3] - (yaw - math.pi / 2)) < 0.01 for h_ in hosp)
    # ---- stromy: sad v humně (lokace.json ves.dvorec.sad: jabloň 6 m, rozestup 7 m), strom na dvoře, lípa u vjezdu
    for k_ in range(rozi(rng, T["jablone"])):
        for _ in range(12):
            uu = rng.uniform(ubk + 2.0, usad - 1.5); vv = rng.uniform(vL + 2.0, vR - 2.0)
            q = F.w(uu, vv)
            if all(math.hypot(q[0] - s_[1], q[1] - s_[2]) > 5.5 for s_ in stromy):
                stromy.append(["jablon", *q, rng.uniform(0, 6.28), rng.uniform(0.85, 1.15)]); break
    if rng.random() < T["strom_dvur_p"] and not kolna_bok:
        stromy.append(["jablon", *F.w(zb - 1.5 + rng.uniform(-0.5, 0.5), vR - 2.6), rng.uniform(0, 6.28), rng.uniform(0.8, 1.0)])
    if rng.random() < T["lipa_vjezd_p"]:
        stromy.append(["lipa", *F.w(uf + 2.2, vR - 1.0), rng.uniform(0, 6.28), rng.uniform(0.8, 1.0)])
    for s_ in stromy:
        if Point(s_[1], s_[2]).distance(CESTY_L) < 2.5: s_[0] = None
        if any(Point(s_[1], s_[2]).buffer(0.5).intersects(v_["pred_poly"]) for v_ in vst): s_[0] = None   # strom před vstupem
    stromy = [s_ for s_ in stromy if s_[0]]
    # venkovní sezení krčmy (mista.json typy.krcma.sezeni; Míša 13. 11.: „jako v Havranovi, ne v cestě“): stoly s lavicemi
    # před štítem (dveře jsou na bocích), lípa u sezení; nesmí na cestu ani před vstup
    sezeni = []; SZ = T.get("sezeni")
    if SZ:
        us_ = zf + SZ["od_stitu_m"]
        for vv in SZ["stoly_v_m"]:
            sezeni.append([SZ["stul"], *F.w(us_, vv), yaw + math.pi / 2])
            for sg in (-1, 1): sezeni.append([SZ["lavice"], *F.w(us_ + sg * SZ["lavice_od_m"], vv), yaw + (0.0 if sg > 0 else math.pi)])
        for s_ in sezeni:
            if Point(s_[1], s_[2]).distance(CESTY_L) < SZ["od_cesty_min_m"]: return "sezení na cestě"
            if any(Point(s_[1], s_[2]).buffer(0.6).intersects(v_["pred_poly"]) for v_ in vst): return "sezení před vstupem"
        if SZ.get("lipa"): stromy.append(["lipa", *F.w(zf + SZ["lipa"][0], SZ["lipa"][1]), rng.uniform(0, 6.28), rng.uniform(0.85, 1.0)])
    return {"typ": typ, "sezeni": sezeni, "ramec": [x, z, yaw], "parcela": parc, "hosp": hosp, "drobne": drobne, "ploty": ploty, "brany": brany,
            "stromy": stromy, "vstupy": vst, "F": F, "uf": uf, "hw": hw, "vR": vR, "dvur": F.poly(zadni + 0.2, uf, hw, vR), "zahrada": F.poly(u_zah, uf, vL, -hw),
            "sad": F.poly(ubk, usad, vL, vR), "humno": (F, ubk, vL, vR), "pole_ok": T.get("pole", False)}

# ---------------------------------------------------------------- rozmístění
rng0 = random.Random(U["semeno"])
stavby = []; useds = []; zabrano = Polygon()
def pridej_dum(misto, m, x, z, yaw, v):
    stavby.append({"misto": misto["id"], "model": m, "x": round(float(x), 2), "z": round(float(z), 2), "yaw": round(yaw, 4),
                   "y": round(v[0] + PUD[m][3], 3), "teren_y": round(v[0], 3), "prevyseni": round(v[1], 2)})
n_used = 0; ULICE = []
for misto in MI["mista"]:
    if misto.get("stav") not in ("SCHVALENO",) or misto.get("typ") == "mlyn": continue
    sx, sz = misto["stred"]; typ = misto.get("usedlost")
    if misto.get("typ") == "ves":
        # cesta, která místem vede: nejbližší vozová / hřebenová osa
        nej = min(((np.hypot(*(o - [sx, sz]).T).min(), i_, o) for i_, o, t in osy if t in ("vozova", "hrebenova")), key=lambda a: a[0])
        o = hust(nej[2]); dd = np.hypot(o[:, 0] - sx, o[:, 1] - sz); o = o[dd < misto["dosah_m"]]
        modely = misto["modely"]; k = 0; n0 = len(stavby); ULICE.append(o)
        for i in range(0, len(o) - 2, int(R["krok_hledani_m"])):   # hustá řada: parcely se nepřekrývají (zabrano), soused hned vedle
            t = o[min(i + 2, len(o) - 1)] - o[max(i - 2, 0)]; t = t / (np.linalg.norm(t) or 1.0); n_ = np.array([-t[1], t[0]])
            for strana in (1, -1):
                if k >= len(modely): break   # počet usedlostí = seznam modelů místa (mista.json)
                m = modely[k]
                for od in np.arange(R["odstup_m"], R["odstup_max_m"] + 0.1, 1.5):
                    x, z = o[i] + n_ * strana * od
                    rng = random.Random(U["semeno"] * 100 + n_used)
                    d_ = -n_ * strana; yaw = math.atan2(d_[0], d_[1]) + rng.uniform(-0.07, 0.07)   # štít k ulici, natočení ± 4°
                    v = stavba_ok(x, z, yaw, m)
                    if not v or Point(x, z).distance(zabrano) < 2.0: continue
                    us = usedlost(x, z, yaw, m, typ, rng, zabrano) if typ else None
                    if typ and not us: continue
                    pridej_dum(misto, m, x, z, yaw, v); k += 1; n_used += 1
                    if us: us["misto"] = misto["id"]; us["i"] = n_used; useds.append(us); zabrano = zabrano.union(us["parcela"])
                    break
        print(misto["id"], "usedlostí", len(stavby) - n0)
    else:
        m = misto["modely"][0]; best = None
        for r_ in np.arange(0, misto.get("dosah_m", 40), 2.0):
            for a in np.linspace(0, 2 * math.pi, max(1, int(2 * math.pi * r_ / 2.0)), endpoint=False):
                x, z = sx + r_ * math.cos(a), sz + r_ * math.sin(a)
                d_, i_ = kh.query([x, z]); q = HLAV[i_]; yaw = math.atan2(q[0] - x, q[1] - z)
                v = stavba_ok(x, z, yaw, m)
                if not v: continue
                rng = random.Random(U["semeno"] * 100 + 50 + len(useds))
                us = usedlost(x, z, yaw, m, typ, rng, zabrano) if typ else None
                if typ and not us: continue
                best = (x, z, yaw, v, us); break
            if best: break
        if best:
            x, z, yaw, v, us = best; pridej_dum(misto, m, x, z, yaw, v)
            if us: us["misto"] = misto["id"]; us["i"] = len(useds) + 1; useds.append(us); zabrano = zabrano.union(us["parcela"])
            print(misto["id"], "na", round(x, 1), round(z, 1), "převýšení", round(v[1], 2), "od středu", round(math.hypot(x - sx, z - sz), 1), "m")
        else:
            # bez usedlosti aspoň dům (poloha je doložená – přednost má místo)
            print("USEDLOST NEVEŠLA", misto["id"], "– jen dům")
            for r_ in np.arange(0, misto.get("dosah_m", 40), 2.0):
                for a in np.linspace(0, 2 * math.pi, max(1, int(2 * math.pi * r_ / 2.0)), endpoint=False):
                    x, z = sx + r_ * math.cos(a), sz + r_ * math.sin(a); d_, i_ = kh.query([x, z]); q = HLAV[i_]
                    yaw = math.atan2(q[0] - x, q[1] - z); v = stavba_ok(x, z, yaw, m)
                    if v: best = (x, z, yaw, v); break
                if best: break
            if best: pridej_dum(misto, m, *best)

# ---------------------------------------------------------------- náves: studna a lípa (Havran vesnice.py: studna na návsi)
studny = []; navesni_stromy = []
for misto in MI["mista"]:
    nv = misto.get("naves")
    if not nv or misto.get("stav") != "SCHVALENO": continue
    domy = [s for s in stavby if s["misto"] == misto["id"]]
    if not domy: continue
    cx_ = np.mean([s["x"] for s in domy]); cz_ = np.mean([s["z"] for s in domy]); best = None
    for r_ in np.arange(0, 40, 1.0):
        for a in np.linspace(0, 2 * math.pi, max(1, int(2 * math.pi * r_)), endpoint=False):
            p = Point(cx_ + r_ * math.cos(a), cz_ + r_ * math.sin(a))
            if p.distance(CESTY_L) >= U["studna"]["od_cesty_m"] and p.distance(zabrano) > 2.5 and p.distance(TOKY_L) > 8 \
                    and all(math.hypot(p.x - s["x"], p.y - s["z"]) > 8 for s in stavby):
                best = (p.x, p.y); break
        if best: break
    if best and nv.get("studna"):
        studny.append({"x": round(best[0], 2), "z": round(best[1], 2), "y": round(vys_b(*best) - 0.05, 3), "yaw": round(rng0.uniform(0, 3.14), 3)})
        if nv.get("lipa_u_studny"):
            for a in np.linspace(0, 2 * math.pi, 12, endpoint=False):
                q = (best[0] + 5.5 * math.cos(a), best[1] + 5.5 * math.sin(a))
                if Point(q).distance(CESTY_L) > 3.0 and Point(q).distance(zabrano) > 2.0:
                    navesni_stromy.append(["lipa", q[0], q[1], rng0.uniform(0, 6.28), 1.15]); break
    print(misto["id"], "studna", best)

# ---------------------------------------------------------------- lány za humny
PO = U["pole"]; pole = []
for us in useds:
    if not us["pole_ok"]: continue
    rng = random.Random(U["semeno"] * 1000 + us["i"])
    F, ubk, vL, vR = us["humno"]; u0 = ubk - PO["od_humna_m"]; L = roz(rng, PO["delka_m"])
    npr = rozi(rng, PO["pruhy"]); sir = (vR - vL - (npr - 1) * PO["mez_m"]) / npr
    for k_ in range(npr):
        a = vL + k_ * (sir + PO["mez_m"]); b = a + sir; dl = 0.0
        while dl < L:   # zkrátit k první překážce (les, cesta, tok, cizí parcela, jiný lán)
            ok = True
            for vv in (a, (a + b) / 2, b):
                q = F.w(u0 - dl, vv); pq = Point(q)
                if trida(*q) in PO["stanoviste_zakazana"] or sklon(*q) > PO["max_sklon"] or pq.distance(CESTY_L) < PO["od_cesty_m"] or pq.distance(TOKY_L) < PO["od_toku_m"] \
                        or (dl > 0 and zabrano.contains(pq)): ok = False; break
            if not ok:
                if DBG == "pole": print("   lán", us["i"], k_, "dl", dl, trida(*q), round(sklon(*q), 2), round(pq.distance(CESTY_L), 1), round(pq.distance(TOKY_L), 1), zabrano.contains(pq))
                break
            dl += 2.0
        if dl < 12.0: continue
        poly = F.poly(u0 - dl, u0, a, b)
        if poly.intersects(zabrano.buffer(-0.01)): continue
        pl = los(rng, PO["plodiny"]); pole.append({"plodina": pl, "poly": poly, "F": F, "u": (u0 - dl, u0), "v": (a, b)})
        zabrano = zabrano.union(poly)
print("lánů", len(pole), {k: sum(1 for p in pole if p["plodina"] == k) for k in PO["plodiny"]})

# ---------------------------------------------------------------- terén: plošiny pod domy a hospodářskými stavbami
plosiny = [(s["x"], s["z"], s["yaw"], s["model"], s["teren_y"]) for s in stavby]
hosp_out = []
for us in useds:
    for h_ in us["hosp"]:
        m_, x_, z_, yw = h_
        if m_ == "kurnik":
            hosp_out.append({"model": m_, "x": x_, "z": z_, "yaw": yw, "misto": us["misto"], "usedlost": us["i"], "plosina": False}); continue
        v = stavba_ok(x_, z_, yw, m_, R.get("od_toku_hospodarske_m"))   # stejná pravidla jako při umístění (hospodářské 8 m od toku)
        plosiny.append((x_, z_, yw, m_, v[0]))
        hosp_out.append({"model": m_, "x": x_, "z": z_, "yaw": yw, "misto": us["misto"], "usedlost": us["i"], "plosina": True, "teren_y": v[0]})
MSK_MISTA = np.zeros_like(Y, bool)
_n_domu = len(stavby)
for x_, z_, yw, m_, ty in plosiny[_n_domu:] + plosiny[:_n_domu]:   # domy nakonec: plocha před jejich dveřmi má přednost před plošinou stodoly/kůlny vedle
    msk = np.zeros_like(Y, bool); b = body_pudorysu(x_, z_, yw, m_, R["okraj_m"], 0.5)
    for p in b:
        r, c = ij(*p)
        if 0 <= r < ny and 0 <= c < nx: msk[r, c] = True
    # před vstupy taky rovina ve výšce domu (Míša 13. 11.: „do hájovny nemůžu vstoupit, všechny budovy musí být vstupné“ –
    # na svahu byl terén před dveřmi 0,3–0,5 m pod domem, se stupněm a prahem přes 0,5 m: postava nevylezla)
    for v_ in vstupy_stavby(m_, x_, z_, yw):
        pp_ = v_["pred_poly"]; bx_ = pp_.bounds
        for zz_ in np.arange(bx_[1], bx_[3] + 0.5, 0.5):
            for xx_ in np.arange(bx_[0], bx_[2] + 0.5, 0.5):
                if pp_.buffer(0.3).contains(Point(xx_, zz_)):
                    r, c = ij(xx_, zz_)
                    if 0 <= r < ny and 0 <= c < nx: msk[r, c] = True
    MSK_MISTA[msk] = True   # teren_dlazdice.py tyto buňky nevyhlazuje (vyhlazení σ 1,5 m stáhlo plochu před dveřmi zpět do svahu)
    r0, c0 = ij(x_, z_); w = 30
    sl = (slice(max(r0 - w, 0), r0 + w), slice(max(c0 - w, 0), c0 + w))
    d = distance_transform_edt(~msk[sl]); a = np.clip(1 - d / R["prechod_m"], 0, 1); a = a * a * (3 - 2 * a)
    Y[sl] = Y[sl] * (1 - a) + ty * a
np.save(out + ".npy", (Y + P["H"]).astype(np.float32)); json.dump(M, open(out + ".json", "w"), ensure_ascii=False, indent=1)
_rr, _cc = np.nonzero(MSK_MISTA); np.savez(out + "_plosiny_mista.npz", r=_rr, c=_cc)
# trasy průchodu dovnitř domů (Míša 13. 11.: „všechny budovy musí být vstupné“): hlavní vstup z venku přes práh do síně
_TRM = {}
for s__ in stavby:
    vv_ = vstupy_stavby(s__["model"], s__["x"], s__["z"], s__["yaw"])   # všechny dveře domu (vstup i do dvora)
    for v_ in vv_:
        _TRM["dum_%s_%s_%d" % (s__["misto"], s__["model"], len(_TRM))] = [[round(float(q[0]), 2), round(float(q[1]), 2), None] for q in (v_["c"] + v_["n"] * 2.5, v_["c"] + v_["n"] * 0.8, v_["c"] - v_["n"] * 1.2)]
json.dump({"popis": "trasy průchodu do domů míst (nastroje/mista_rozmisteni.py) – test_pruchod.gd", "trasy": _TRM}, open(K + "/hra/data/pruchody_mista.json", "w"), ensure_ascii=False, indent=1)
print("trasy do domů", len(_TRM))
# doprovodné soubory předchozího kroku (jámy sklepa a šachty, koryta, skály) pod novou předponou – teren_dlazdice.py je
# čte podle předpony (11. 11.: bez nich chyběla díra sklepa, pás koryt a nájezdy k mostům – hlídači)
import glob, shutil
for f in glob.glob(pre + "_*.npz"): shutil.copy(f, out + f[len(pre):])

# ---------------------------------------------------------------- vyšlapáno (mista.json usedlosti.vyslapano): kde se chodí, je hlína
# (Míša 12. 11. večer; KCD misa_kcd_04/14, Havran vesnice.py yard_dirt + ves_paths): ulice, náves, cestičky od vrat a dveří, okap, dvůr
HL = VY["hlina"]; vy_plochy = []; vy_cary = []
def k_ulici(a, smer, w, hl_):
    """cestička z bodu a: rovne_ven_m ve směru smer, pak oblouk k nejbližšímu bodu vozové/hřebenové cesty (Havran ves_paths)"""
    g1 = a + smer * VY["rovne_ven_m"]; j = HLAV[kh.query(g1)[1]]
    body = [a * (1 - t) ** 2 + g1 * 2 * t * (1 - t) + j * t * t for t in np.linspace(0, 1, 13)]
    vy_cary.append({"body": [[r3_(q[0]), r3_(q[1])] for q in body], "polosirka": w, "hlina": hl_, "druh": "chodnik"})
r3_ = lambda a: round(float(a), 2)
for o in ULICE: vy_cary.append({"body": [[r3_(q[0]), r3_(q[1])] for q in o[::2]], "polosirka": VY["ulice_polosirka_m"], "hlina": HL["ulice"], "druh": "ulice"})
for s_ in studny:
    vy_plochy.append({"poly": [[r3_(q[0]), r3_(q[1])] for q in Point(s_["x"], s_["z"]).buffer(VY["naves_polomer_m"], 8).exterior.coords[:-1]], "hlina": HL["naves"], "druh": "naves"})
    k_ulici(np.array([s_["x"], s_["z"]]), np.zeros(2), VY["chodnik_polosirka_m"], HL["naves"])
for us in useds:
    F = us["F"]; vy_plochy.append({"poly": [[r3_(q[0]), r3_(q[1])] for q in us["dvur"].exterior.coords[:-1]], "hlina": HL["dvur"], "druh": "dvur"})
    x_, z_, yw_ = us["ramec"]; m_ = [s for s in stavby if abs(s["x"] - x_) < 0.01 and abs(s["z"] - z_) < 0.01][0]["model"]
    for o_ in [(m_, x_, z_, yw_)] + [tuple(h_) for h_ in us["hosp"]]:
        vy_plochy.append({"poly": [[r3_(q[0]), r3_(q[1])] for q in Polygon(rohy(o_[1], o_[2], o_[3], o_[0], VY["okap_m"])).exterior.coords[:-1]], "hlina": HL["okap"], "druh": "okap"})
    for v_ in us["vstupy"]:
        vy_plochy.append({"poly": [[r3_(q[0]), r3_(q[1])] for q in v_["pred_poly"].exterior.coords[:-1]], "hlina": HL["pred_vstupem"], "druh": "pred_vstupem"})
    if us.get("sezeni"):   # pod stoly a kolem nich udusaná hlína (KCD1 web_kcd1_broken_wheel_hostinec)
        ok_ = U["typy"][us["typ"]]["sezeni"]["vyslapano_okraj_m"]
        vy_plochy.append({"poly": [[r3_(q[0]), r3_(q[1])] for q in MultiPoint([(s_[1], s_[2]) for s_ in us["sezeni"]]).convex_hull.buffer(ok_, 4).exterior.coords[:-1]], "hlina": HL["dvur"], "druh": "sezeni"})
    if not us["ploty"]:   # otevřený dvůr (krčma): celý dvůr a plochy před vstupy volně k cestě (obal s nejbližšími body cesty)
        from shapely.geometry import MultiPoint
        rr = list(us["dvur"].exterior.coords) + [q for v_ in us["vstupy"] for q in v_["pred_poly"].exterior.coords]
        rr += [tuple(HLAV[kh.query(q)[1]]) for q in rr]
        vy_plochy.append({"poly": [[r3_(q[0]), r3_(q[1])] for q in MultiPoint(rr).convex_hull.exterior.coords[:-1]], "hlina": HL["dvur"], "druh": "vjezd_bez_vrat"})
        continue
    for b_ in us["brany"]:
        a_ = (np.array(b_["a"]) + np.array(b_["b"])) / 2
        k_ulici(a_, F.au, VY["vjezd_polosirka_m"] if b_["druh"] != "branka" else VY["chodnik_polosirka_m"], HL["chodnik"])
        for v_ in us["vstupy"]:   # dveře mimo dvůr (do zahrádky) -> k brance
            e_ = v_["c"] + v_["n"] * VS["pred_m"]
            if b_["druh"] == "branka" and not us["dvur"].contains(Point(*e_)):
                vy_cary.append({"body": [[r3_(e_[0]), r3_(e_[1])], [r3_(a_[0] - F.au[0]), r3_(a_[1] - F.au[1])], [r3_(a_[0]), r3_(a_[1])]], "polosirka": VY["chodnik_polosirka_m"] * 0.8, "hlina": HL["chodnik"], "druh": "chodnik"})
print("vyšlapáno: ploch %d, cestiček a ulic %d" % (len(vy_plochy), len(vy_cary)))

# ---------------------------------------------------------------- výstup (výšky z výsledného terénu)
RZ = MI["modely"]["hospodarske"]["rozmery"]
def y_pud(x_, z_, yw, m_):
    """drobnost s půdorysem: nejnižší roh (nic nevisí), jinak bod"""
    if m_ in RZ or m_.startswith("zahon"):
        l_, h_ = RZ.get(m_, RZ["zahon"]); cs, sn = math.cos(yw), math.sin(yw)
        return min(vys_b(x_ + px * cs + pz * sn, z_ - px * sn + pz * cs) for px in (-l_ / 2, l_ / 2) for pz in (-h_ / 2, h_ / 2))
    return vys_b(x_, z_)
r3 = lambda a: round(float(a), 3)
for h in hosp_out:
    h["y"] = r3(h.pop("teren_y")) if h["plosina"] else r3(y_pud(h["x"], h["z"], h["yaw"], h["model"]) - 0.03)
    h["x"], h["z"], h["yaw"] = r3(h["x"]), r3(h["z"]), r3(h["yaw"])
drobne_out = []; ploty_out = []; brany_out = []; stromy_out = []; sezeni_out = []
for us in useds:
    for m_, x_, z_, yw in us["drobne"]:
        drobne_out.append({"model": m_, "x": r3(x_), "y": r3(y_pud(x_, z_, yw, m_) - 0.02), "z": r3(z_), "yaw": r3(yw), "usedlost": us["i"]})
    for dr, a, b in us["ploty"]:
        L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(math.ceil(L / 1.0)))
        body = [[r3(a[0] + (b[0] - a[0]) * t), r3(vys_b(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)), r3(a[1] + (b[1] - a[1]) * t)] for t in np.linspace(0, 1, n + 1)]
        ploty_out.append({"druh": dr, "body": body, "usedlost": us["i"], "semeno": us["i"] * 31 + len(ploty_out)})
    for b_ in us["brany"]:
        a, b = b_["a"], b_["b"]; ya, yb = vys_b(*a), vys_b(*b)
        brany_out.append({"druh": b_["druh"], "a": [r3(a[0]), r3(ya), r3(a[1])], "b": [r3(b[0]), r3(yb), r3(b[1])], "usedlost": us["i"]})
    for m_, x_, z_, yw in us.get("sezeni", []):
        sezeni_out.append({"model": m_, "x": r3(x_), "y": r3(vys_b(x_, z_) - 0.02), "z": r3(z_), "yaw": r3(yw), "usedlost": us["i"]})
    for s_ in us["stromy"]:
        stromy_out.append({"druh": s_[0], "x": r3(s_[1]), "y": r3(vys_b(s_[1], s_[2]) - 0.1), "z": r3(s_[2]), "yaw": r3(s_[3]), "meritko": r3(s_[4])})
for s_ in navesni_stromy:
    stromy_out.append({"druh": s_[0], "x": r3(s_[1]), "y": r3(vys_b(s_[1], s_[2]) - 0.1), "z": r3(s_[2]), "yaw": r3(s_[3]), "meritko": r3(s_[4])})
pp = lambda poly: [[r3(x_), r3(z_)] for x_, z_ in list(poly.exterior.coords)[:-1]]
used_out = [{"i": us["i"], "misto": us["misto"], "typ": us["typ"], "stred": [r3(us["parcela"].centroid.x), r3(us["parcela"].centroid.y)],
             "parcela": pp(us["parcela"])} for us in useds]
json.dump({"popis": "stavby nových míst (nastroje/mista_rozmisteni.py z pravidla/svet/mista.json) – čte hra (hlavni.gd _mista domy, ves.gd hospodářské stavby, ploty, drobnosti, stromy, studna) a stavby_vegetace.py (půdorysy, dvory, zahrady, sady, pole)",
           "vstupy_domu": [{"stavba": s__["model"], "misto": s__["misto"], "y": s__["teren_y"], "body": [[r3_(q[0]), r3_(q[1])] for v__ in vstupy_stavby(s__["model"], s__["x"], s__["z"], s__["yaw"]) for q in (v__["c"] + v__["n"] * 0.6, v__["c"] + v__["n"] * 1.2)]} for s__ in stavby],
           "modely": MI["modely"], "stavby": stavby, "lod_ves": U["lod"], "ploty_pravidla": U["ploty"], "studna_pravidla": U["studna"],
           "usedlosti": used_out, "hospodarske": hosp_out, "drobne": drobne_out, "ploty": ploty_out, "brany": brany_out,
           "stromy": stromy_out, "sezeni": sezeni_out, "studny": studny, "vyslapano": {"trida": VY["trida"], "plochy": vy_plochy, "cary": vy_cary},
           "vstupy": [{"usedlost": us["i"], "stavba": v_["stavba"], "druh": v_["druh"], "c": [r3(v_["c"][0]), r3(v_["c"][1])], "n": [r3(v_["n"][0]), r3(v_["n"][1])], "sirka": r3(v_["w"]),
                       "pred": pp(v_["pred_poly"])} for us in useds for v_ in us["vstupy"]],
           "pudorysy": [rohy(s["x"], s["z"], s["yaw"], s["model"], 0.3) for s in stavby] + [rohy(h["x"], h["z"], h["yaw"], h["model"], 0.3) for h in hosp_out],
           "dvory": [pp(us["dvur"]) for us in useds], "zahrady": [pp(us["zahrada"]) for us in useds], "sady": [pp(us["sad"]) for us in useds],
           "pole": [{"plodina": p["plodina"], "poly": pp(p["poly"])} for p in pole]},
          open(K + "/hra/data/mista_stavby.json", "w"), ensure_ascii=False, indent=1)
print("staveb", len(stavby), "hospodářských", len(hosp_out), "drobností", len(drobne_out), "plotů", len(ploty_out), "bran", len(brany_out), "stromů", len(stromy_out))
