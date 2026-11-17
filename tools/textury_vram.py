"""Audit textur v graficke pameti tabletu (ETC2) – podle Puchartu 17. 11. (nastroje/textury_vram.py), Misa 17. 11.:
0.9999991 VRAM 1067 MB (textury 673 MB) a pad po ~44 min. Cte jen data, nic nemeni.
Pro kazdy import textury (*.import mimo .godot/build/apk/data) precte hlavicku vysledneho .ctex (tablet: path.etc2,
bezeztratove: path bez pripony formatu) a spocte bajty v graficke pameti z rozmeru, formatu a mip urovni.
Duplicity = stejny obsah .ctex (data za hlavickou) pod vic cestami – i textury rozbalene z glb bez zdroje. Vystup: build/textury_vram.json + .md, na stdout souhrn.
  python3 tools/textury_vram.py [--json build/x.json] [--top 30]"""
import glob
import hashlib
import json
import os
import re
import struct
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
# Godot 4 Image::Format -> (jmeno, bity na pixel, blokovy)
FMT = {0: ("L8", 8, 0), 1: ("LA8", 16, 0), 2: ("R8", 8, 0), 3: ("RG8", 16, 0), 4: ("RGB8", 24, 0), 5: ("RGBA8", 32, 0),
       6: ("RGBA4444", 16, 0), 7: ("RGB565", 16, 0), 17: ("DXT1", 4, 1), 18: ("DXT3", 8, 1), 19: ("DXT5", 8, 1),
       20: ("RGTC_R", 4, 1), 21: ("RGTC_RG", 8, 1), 22: ("BPTC_RGBA", 8, 1), 25: ("ETC", 4, 1), 26: ("ETC2_R11", 4, 1),
       27: ("ETC2_R11S", 4, 1), 28: ("ETC2_RG11", 8, 1), 29: ("ETC2_RG11S", 8, 1), 30: ("ETC2_RGB8", 4, 1),
       31: ("ETC2_RGBA8", 8, 1), 32: ("ETC2_RGB8A1", 4, 1), 33: ("ETC2_RA_AS_RG", 8, 1), 35: ("ASTC_4x4", 8, 1)}


def hlavicka(f):
    b = open(f, "rb").read(52)
    if len(b) < 52 or b[:4] != b"GST2":
        return None
    df, iw, ih, mips, fmt = struct.unpack("<IHHII", b[36:52])
    return df, iw, ih, mips, fmt


def vram(iw, ih, mips, fmt):
    jm, bpp, blok = FMT.get(fmt, ("?%d" % fmt, 32, 0))
    s, w, h = 0, iw, ih
    for _ in range(mips + 1):
        if blok:
            s += max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * 2 * bpp
        else:
            s += w * h * bpp // 8
        w, h = max(1, w // 2), max(1, h // 2)
    return jm, s


def md5(f, od=0):
    try:
        return hashlib.md5(open(f, "rb").read()[od:]).hexdigest()
    except OSError:
        return None


def audit():
    out = []
    for imp in glob.glob("**/*.import", recursive=True):
        if imp.startswith((".godot", "build", "apk", "data/", "addons")):
            continue
        t = open(imp, encoding="utf-8", errors="ignore").read()
        if 'importer="texture"' not in t:
            continue
        src = imp[:-len(".import")]
        m = re.search(r'path\.etc2="res://([^"]+)"', t) or re.search(r'^path="res://([^"]+\.ctex)"', t, re.M)
        if not m or not os.path.exists(m.group(1)):
            continue
        h = hlavicka(m.group(1))
        if not h:
            continue
        df, iw, ih, mips, fmt = h
        jm, b = vram(iw, ih, mips, fmt)
        cm = re.search(r"compress/mode=(\d)", t)
        sl = re.search(r"process/size_limit=(\d+)", t)
        out.append({"src": src, "ctex": m.group(1), "w": iw, "h": ih, "mips": mips, "fmt": jm, "vram": b,
                    "mode": int(cm.group(1)) if cm else None, "limit": int(sl.group(1)) if sl else 0,
                    "md5": md5(src), "zdroj": os.path.exists(src), "md5_gpu": md5(m.group(1), 36)})
    return out


def slozka(p):
    d = p.split("/")
    return "/".join(d[:2]) if len(d) > 2 else p


def main():
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 30
    js = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else "build/textury_vram.json"
    a = audit()
    MB = 1048576
    tot = sum(x["vram"] for x in a)
    pof = {}
    for x in a:
        pof[x["fmt"]] = pof.get(x["fmt"], 0) + x["vram"]
    pos = {}
    for x in a:
        k = slozka(x["src"])
        n, s = pos.get(k, (0, 0))
        pos[k] = (n + 1, s + x["vram"])
    sk = {}
    for x in a:
        sk.setdefault(x["md5_gpu"], []).append(x)   # stejna data v graficke pameti (i bez zdroje: rozbalene z glb)
    dup = sorted([v for v in sk.values() if len(v) > 1], key=lambda v: -sum(x["vram"] for x in v[1:]))
    dup_mb = sum(sum(x["vram"] for x in v[1:]) for v in dup)
    nekomp = sorted([x for x in a if not x["fmt"].startswith(("ETC", "DXT", "RGTC", "BPTC", "ASTC"))], key=lambda x: -x["vram"])
    L = ["# Textury v graficke pameti tabletu (tools/textury_vram.py)", "",
         "Textur: %d, soucet ETC2/tablet: **%.1f MB** (horni mez – vse importovane; ve hre jen to, co je nahrane)." % (len(a), tot / MB), "",
         "Po formatech: " + ", ".join("%s %.1f MB" % (k, v / MB) for k, v in sorted(pof.items(), key=lambda kv: -kv[1])), "",
         "## %d nejvetsich" % top, "| # | textura | rozmer | format | mip | MB | compress/mode | limit |", "|---|---|---|---|---|---|---|---|"]
    for i, x in enumerate(sorted(a, key=lambda x: -x["vram"])[:top]):
        L.append("| %d | `%s` | %dx%d | %s | %d | %.2f | %s | %s |" % (i + 1, x["src"], x["w"], x["h"], x["fmt"], x["mips"], x["vram"] / MB, x["mode"], x["limit"]))
    L += ["", "## Slozky", "| slozka | textur | MB |", "|---|---|---|"]
    for k, (n, s) in sorted(pos.items(), key=lambda kv: -kv[1][1])[:25]:
        L.append("| `%s` | %d | %.1f |" % (k, n, s / MB))
    L += ["", "## Duplicity podle obsahu .ctex (stejna data v graficke pameti): %d skupin, navic %.1f MB (kdyby se nahraly vsechny kopie)" % (len(dup), dup_mb / MB),
          "| kopii | MB navic | priklad |", "|---|---|---|"]
    for v in dup[:40]:
        L.append("| %d | %.2f | %s |" % (len(v), sum(x["vram"] for x in v[1:]) / MB, "<br>".join("`%s`" % x["src"] for x in v[:4])))
    L += ["", "## Bez VRAM komprese (na GPU rozbalene): %d, %.1f MB" % (len(nekomp), sum(x["vram"] for x in nekomp) / MB),
          "| textura | rozmer | format | mip | MB | mode |", "|---|---|---|---|---|---|"]
    for x in nekomp[:40]:
        L.append("| `%s` | %dx%d | %s | %d | %.2f | %s |" % (x["src"], x["w"], x["h"], x["fmt"], x["mips"], x["vram"] / MB, x["mode"]))
    os.makedirs(os.path.dirname(js) or ".", exist_ok=True)
    json.dump({"soucet_b": tot, "po_formatech": pof, "dup_b": dup_mb, "textury": a}, open(js, "w"), ensure_ascii=False)
    open(js[:-5] + ".md", "w").write("\n".join(L) + "\n")
    print("textury %d, ETC2/tablet %.1f MB, duplicity %d skupin %.1f MB, bez komprese %d %.1f MB -> %s" % (
        len(a), tot / MB, len(dup), dup_mb / MB, len(nekomp), sum(x["vram"] for x in nekomp) / MB, js[:-5] + ".md"))


if __name__ == "__main__":
    main()
