"""Kontrola textur v grafické paměti (plán z rešerše 17. 11. A2; tablet ukazuje VRAM 938 MB a roste).

Čte importy Godotu (hra/**/*.import, importer texture a 2d_array_texture) a jejich výsledné soubory v hra/.godot/imported
(pro tablet varianta .etc2.ctex, jinak prostá .ctex). Z hlavičky .ctex (GST2: formát dat, šířka, výška, počet mipmap,
Image.Format) spočte velikost v grafické paměti: VRAM komprimované = data souboru, bezeztrátové (PNG/WebP v .ctex) =
šířka × výška × bajty formátu × mipmapy (rozbalí se při nahrání). Vypíše:
  - 30 největších textur (rozměr, formát, mipmapy, odhad VRAM, režim komprese, kdo na ni odkazuje),
  - duplicity (stejný obsah zdrojového souboru pod více cestami),
  - nepoužité (cesta ani uid se nevyskytuje v kódu, datech, scénách ani v importovaných scénách glb) – jen kandidáti,
  - součty po složkách.
Nic nemaže ani nemění – výsledek je návrh. Celková velikost je horní mez (na tabletu je nahrané jen to, co scéna použije;
skutečný výpis ve hře: hra/scripts/textury_vram.gd → user://textury_vram.txt po měření).

  python3 nastroje/textury_vram.py [K] [--md soubor.md] [--json soubor.json]
"""
import collections, glob, hashlib, json, os, re, struct, sys

K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.join(os.path.dirname(__file__), ".."))
H = os.path.join(K, "hra")
ARG = sys.argv

# Image.Format (Godot 4.7 core/io/image.h) -> (jméno, bajty na pixel)
FMT = {0: ("L8", 1), 1: ("LA8", 2), 2: ("R8", 1), 3: ("RG8", 2), 4: ("RGB8", 3), 5: ("RGBA8", 4), 6: ("RGBA4444", 2),
       7: ("RGB565", 2), 8: ("RF", 4), 9: ("RGF", 8), 10: ("RGBF", 12), 11: ("RGBAF", 16), 12: ("RH", 2), 13: ("RGH", 4),
       14: ("RGBH", 6), 15: ("RGBAH", 8), 16: ("RGBE9995", 4), 17: ("DXT1", .5), 18: ("DXT3", 1), 19: ("DXT5", 1),
       20: ("RGTC_R", .5), 21: ("RGTC_RG", 1), 22: ("BPTC_RGBA", 1), 23: ("BPTC_RGBF", 1), 24: ("BPTC_RGBFU", 1),
       25: ("ETC", .5), 26: ("ETC2_R11", .5), 27: ("ETC2_R11S", .5), 28: ("ETC2_RG11", 1), 29: ("ETC2_RG11S", 1),
       30: ("ETC2_RGB8", .5), 31: ("ETC2_RGBA8", 1), 32: ("ETC2_RGB8A1", .5), 33: ("ETC2_RA_AS_RG", 1),
       34: ("DXT5_RA_AS_RG", 1), 35: ("ASTC_4x4", 1), 36: ("ASTC_4x4_HDR", 1), 37: ("ASTC_8x8", .25), 38: ("ASTC_8x8_HDR", .25)}
REZIM = {0: "bezeztrátová", 1: "ztrátová (WebP)", 2: "VRAM komprese", 3: "VRAM nekompr.", 4: "Basis Universal"}


def ini(p):
    d = {}
    for r in open(p, encoding="utf-8", errors="replace"):
        m = re.match(r'^([\w/]+)=(.*)$', r.strip())
        if m: d[m.group(1)] = m.group(2).strip()
    return d


def ctex(p):
    """Hlavička .ctex/.ctexarray -> (w, h, mipmaps, formát, VRAM bajtů, vrstev)."""
    b = open(p, "rb").read()
    if b[:4] == b"GST2":
        df, w, h, mip, fmt = struct.unpack("<IHHII", b[36:52])
        vr = 1
    elif b[:4] == b"GSTL":   # vrstvená (Texture2DArray): hlavička se liší, odhad z dat
        return None
    else:
        return None
    nazev, bpp = FMT.get(fmt, (str(fmt), 4))
    if df == 0:   # data přímo ve formátu pro GPU (VRAM komprese / nekomprimované)
        vram = len(b) - 52
    else:          # PNG / WebP uvnitř – při nahrání se rozbalí
        vram = sum(max(w >> i, 1) * max(h >> i, 1) * bpp for i in range(mip + 1))
    return w, h, mip, nazev, int(vram), vr


def zavislosti():
    """Závislosti scén z Godotu (nastroje/godot/zavislosti.gd); bez Godotu prázdné (pak méně „ano“)."""
    import shutil, subprocess, tempfile
    g = os.environ.get("GODOT", "/opt/godot47/Godot_v4.7.2-stable_linux.x86_64")
    if not os.path.exists(g): return {}
    tmp = tempfile.mkdtemp(prefix="tex_zav_")
    sk = os.path.join(H, "_zavislosti.gd")
    shutil.copy(os.path.join(K, "nastroje/godot/zavislosti.gd"), sk)
    env = dict(os.environ, PUCHART_ZAVISLOSTI=tmp + "/z.json", XDG_DATA_HOME=tmp, XDG_CONFIG_HOME=tmp, XDG_CACHE_HOME=tmp)
    try:
        subprocess.run([g, "--headless", "-s", "res://_zavislosti.gd"], cwd=H, env=env, capture_output=True, timeout=600)
        return json.load(open(tmp + "/z.json"))
    except Exception as e:
        print("zavislosti: %s" % e, file=sys.stderr); return {}
    finally:
        for f in (sk, sk + ".uid"):
            if os.path.exists(f): os.remove(f)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    imp = [p for p in glob.glob(H + "/**/*.import", recursive=True) if "/.godot/" not in p]
    tex = []
    for p in imp:
        d = ini(p)
        if d.get("importer", "").strip('"') not in ("texture", "2d_array_texture"): continue
        src = d.get("source_file", "").strip('"')
        dest = re.findall(r'"(res://[^"]+)"', d.get("dest_files", ""))
        cil = next((x for x in dest if ".etc2." in x), dest[0] if dest else None)
        info = None
        if cil:
            f = os.path.join(H, cil.replace("res://", ""))
            if os.path.exists(f): info = ctex(f)
        sp = os.path.join(H, src.replace("res://", ""))
        tex.append({"cesta": src, "uid": d.get("uid", "").strip('"'), "rezim": REZIM.get(int(d.get("compress/mode", "0") or 0), "?"),
                    "mipmapy_import": d.get("mipmaps/generate", "?"), "limit": d.get("process/size_limit", "0"),
                    "info": info, "zdroj_b": os.path.getsize(sp) if os.path.exists(sp) else 0,
                    "md5": hashlib.md5(open(sp, "rb").read()).hexdigest() if os.path.exists(sp) else None,
                    })
    # odkazy: res:// a uid:// řetězce z kódu a dat (kořeny), závislosti scén a modelů z Godotu (importované scény jsou
    # komprimované RSCC – čte je nastroje/godot/zavislosti.gd); textura je použitá, když na ni vede cesta od kořene
    res_set, uid_set, slova = set(), set(), set()
    pat_res = re.compile(rb'res://[^\x00-\x1f"\'\\ ]+'); pat_uid = re.compile(rb'uid://[a-z0-9]+')
    texty = []
    for ext in ("gd", "tscn", "tres", "json", "gdshader", "gdshaderinc", "cfg", "godot"):
        texty += [p for p in glob.glob(H + "/**/*." + ext, recursive=True) if "/.godot/" not in p]
    for p in texty:
        b = open(p, "rb").read()
        res_set |= {m.decode("utf-8", "replace") for m in pat_res.findall(b)}
        uid_set |= {m.decode() for m in pat_uid.findall(b)}
        slova |= {m.decode("utf-8", "replace") for m in re.findall(rb'[A-Za-z0-9_]+', b)}
    zav = zavislosti()
    for t in tex:
        if t["uid"] in uid_set: res_set.add(t["cesta"])
    # vzory složené za běhu: "res://textury/impostory/%s_a.png" -> předpona složky
    predpony = {re.split(r'[%{]', s)[0] for s in res_set if re.search(r'[%{]', s) or s.endswith("/")}
    predpony = {x for x in predpony if x.count("/") >= 3}
    kdo_ma = collections.defaultdict(set)
    for sc, deps in zav.items():
        for d in deps: kdo_ma[d].add(os.path.basename(sc))
    def dosah(koreny):
        vid, fr = set(), list(koreny)
        while fr:
            x = fr.pop()
            if x in vid: continue
            vid.add(x); fr += zav.get(x, [])
        return vid
    jiste = dosah([x for x in res_set if not re.search(r'[%{]', x)])
    # modely skládané za běhu (předmět podle id z dat): jméno modelu je slovo v kódu/datech, nebo leží ve složce z předpony
    moz_mod = [sc for sc in zav if sc not in jiste and (os.path.splitext(os.path.basename(sc))[0] in slova or any(sc.startswith(x) for x in predpony))]
    mozna = dosah(moz_mod) - jiste
    for t in tex:
        c = t["cesta"]
        if c in jiste: t["uziti"] = "ano"
        elif c in mozna or any(c.startswith(x) for x in predpony) or os.path.splitext(os.path.basename(c))[0] in slova:
            t["uziti"] = "možná (cesta skládaná za běhu)"
        else: t["uziti"] = "nenalezeno"
        t["kdo"] = sorted(kdo_ma.get(c, set()))
    ok = [t for t in tex if t["info"]]
    ok.sort(key=lambda t: -t["info"][4])
    celk = sum(t["info"][4] for t in ok)
    # duplicity podle obsahu zdroje
    dup = collections.defaultdict(list)
    for t in tex:
        if t["md5"]: dup[t["md5"]].append(t)
    dupl = sorted((v for v in dup.values() if len(v) > 1), key=lambda v: -(v[0]["info"][4] if v[0]["info"] else 0) * (len(v) - 1))
    dup_mb = sum((v[0]["info"][4] if v[0]["info"] else 0) * (len(v) - 1) for v in dupl) / 2**20
    nepouz = [t for t in ok if t["uziti"] == "nenalezeno"]
    moz = [t for t in ok if t["uziti"].startswith("možná")]
    slozky = collections.Counter(); slozky_n = collections.Counter()
    for t in ok:
        s = "/".join(t["cesta"].replace("res://", "").split("/")[:2]); slozky[s] += t["info"][4]; slozky_n[s] += 1
    fmt_sum = collections.Counter()
    for t in ok: fmt_sum[t["info"][3]] += t["info"][4]
    velke = [t for t in ok if max(t["info"][0], t["info"][1]) >= 2048]
    bezmip = [t for t in ok if t["info"][2] == 0 and t["uziti"] != "nenalezeno" and t["info"][4] > 256 * 1024]
    nekompr = [t for t in ok if t["info"][3] in ("RGBA8", "RGB8", "LA8", "L8", "RGBAH", "RGBAF", "RGBH", "RH", "RF") and t["info"][4] > 512 * 1024]

    mb = lambda b: "%.1f" % (b / 2**20)
    L = []
    L.append("Textur: %d (s výsledkem importu %d). Součet VRAM všech importovaných (tablet ETC2): **%s MB** – horní mez, na tabletu je nahrané jen to, co je ve scéně." % (len(tex), len(ok), mb(celk)))
    L.append("")
    L.append("Po formátech: " + ", ".join("%s %s MB" % (k, mb(v)) for k, v in fmt_sum.most_common()))
    L.append("")
    L.append("### 30 největších")
    L.append("| # | textura | rozměr | formát | mipmapy | VRAM MB | import | odkazy |")
    L.append("|---|---|---|---|---|---|---|---|")
    for i, t in enumerate(ok[:30], 1):
        w, h, mip, f, v, _ = t["info"]
        kdo = ", ".join(t["kdo"][:3]) + (" +%d" % (len(t["kdo"]) - 3) if len(t["kdo"]) > 3 else "")
        L.append("| %d | `%s` | %d×%d | %s | %d | %s | %s%s | %s |" % (i, t["cesta"].replace("res://", ""), w, h, f, mip, mb(v), t["rezim"],
                 (", limit %s px" % t["limit"]) if t["limit"] not in ("0", "") else "", kdo if kdo else t["uziti"]))
    L.append("")
    L.append("### Součty po složkách (nejvíc VRAM)")
    L.append("| složka | textur | VRAM MB |")
    L.append("|---|---|---|")
    for s, v in slozky.most_common(15): L.append("| `%s` | %d | %s |" % (s, slozky_n[s], mb(v)))
    L.append("")
    L.append("### Duplicity (stejný obsah zdroje pod více cestami): %d skupin, zbytečně %s MB VRAM, pokud se nahrají všechny kopie" % (len(dupl), mb(dup_mb * 2**20)))
    L.append("| kopií | VRAM MB/kus | cesty |")
    L.append("|---|---|---|")
    for v in dupl[:25]:
        L.append("| %d | %s | %s |" % (len(v), mb(v[0]["info"][4]) if v[0]["info"] else "?", "<br>".join("`%s` (%s)" % (t["cesta"].replace("res://", ""), t["uziti"].split(" ")[0]) for t in v[:6]) + (" …" if len(v) > 6 else "")))
    L.append("")
    L.append("### Nepoužité – kandidáti (cesta ani uid nenalezeny v kódu, datech, scénách ani importovaných glb): %d, %s MB" % (len(nepouz), mb(sum(t["info"][4] for t in nepouz))))
    L.append("Hra je nenahraje, dokud je nikdo nenačte – VRAM tablet nezatěžují, jen velikost balíku dat. Nic nesmazáno.")
    L.append("")
    L.append("| textura | rozměr | VRAM MB |")
    L.append("|---|---|---|")
    for t in sorted(nepouz, key=lambda t: -t["info"][4])[:25]:
        L.append("| `%s` | %d×%d | %s |" % (t["cesta"].replace("res://", ""), t["info"][0], t["info"][1], mb(t["info"][4])))
    L.append("")
    L.append("Možná použité (jméno souboru nebo složka se v kódu/datech vyskytuje, cesta se skládá za běhu): %d, %s MB." % (len(moz), mb(sum(t["info"][4] for t in moz))))
    L.append("")
    L.append("### Další nálezy")
    L.append("- 2048 px a víc: %d textur, %s MB: %s" % (len(velke), mb(sum(t["info"][4] for t in velke)), ", ".join("`%s`" % t["cesta"].replace("res://", "") for t in velke[:12]) + (" …" if len(velke) > 12 else "")))
    L.append("- bez VRAM komprese nad 0,5 MB (na GPU rozbalené RGBA/RGB): %d textur, %s MB: %s" % (len(nekompr), mb(sum(t["info"][4] for t in nekompr)), ", ".join("`%s` (%s)" % (t["cesta"].replace("res://", ""), t["info"][3]) for t in nekompr[:12])))
    L.append("- použité bez mipmap nad 0,25 MB (ve 3D šum a víc čtení paměti v dálce): %d: %s" % (len(bezmip), ", ".join("`%s`" % t["cesta"].replace("res://", "") for t in bezmip[:12])))
    md = "\n".join(L)
    print(md)
    if "--json" in ARG:
        json.dump([{k: t[k] for k in ("cesta", "uid", "rezim", "uziti", "kdo")} | {"info": t["info"]} for t in ok], open(ARG[ARG.index("--json") + 1], "w"), ensure_ascii=False, indent=0)
    print("TEXTURY_VRAM textur %d, součet %s MB, duplicit %d skupin (%s MB), nepoužitých %d" % (len(tex), mb(celk), len(dupl), mb(dup_mb * 2**20), len(nepouz)), file=sys.stderr)


main()
