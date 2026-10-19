"""Herni data z repa do projektu (novy kontejner, radce 19:15): balíky data/<balik>-<md5>.pck.NNN podle data_manifest.json
se slozi a rozbali z nich modely/ a .godot/imported/ - projekt pak bezi a meri jako s puvodnimi daty (bez zdrojovych
.glb/.jpg, ty jsou v blender/ skriptech, Poly Haven a na Misove Disku). Existujici soubory se neprepisuji.
Na PC (kontejner) nema export pro Android cestu k desktopovym texturam: do *.import s path.etc2= se doplni path=
(Godot ETC2 na PC rozbali sam).   python3 tools/pck_rozbal.py"""
import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def soubory(pck):
    """[(cesta bez res://, offset, velikost)] z PCK v2/v3 (Godot 4)."""
    with open(pck, "rb") as f:
        assert f.read(4) == b"GDPC", pck
        ver = struct.unpack("<4I", f.read(16))[0]
        _flags, base = struct.unpack("<IQ", f.read(12))
        diroff = struct.unpack("<Q", f.read(8))[0] if ver >= 3 else 0
        f.read(64)
        if ver >= 3:
            f.seek(diroff)
        out = []
        for _ in range(struct.unpack("<I", f.read(4))[0]):
            ln = struct.unpack("<I", f.read(4))[0]
            p = f.read(ln).rstrip(b"\0").decode()
            off, sz = struct.unpack("<QQ", f.read(16))
            f.read(20)
            out.append((p[6:] if p.startswith("res://") else p, base + off, sz))
        return out


def rozbal(pck, dest):
    n = 0
    with open(pck, "rb") as f:
        for rel, off, sz in soubory(pck):
            if not rel.startswith(("modely/", ".godot/imported/")):
                continue                                   # project.binary, seznam UID: plati z projektu
            t = os.path.join(dest, rel)
            if os.path.exists(t):
                continue
            os.makedirs(os.path.dirname(t), exist_ok=True)
            f.seek(off)
            open(t, "wb").write(f.read(sz))
            n += 1
    return n


def main():
    man = json.load(open(os.path.join(ROOT, "data_manifest.json")))
    tmp = os.path.join(ROOT, "build", "rozbal")
    os.makedirs(tmp, exist_ok=True)
    celkem = 0
    # opravy z_* az nakonec s prepisem (jako data.gd)
    jmena = sorted(man["packs"], key=lambda n: (n.startswith("z_"), n != "svet", n))
    for name in jmena:
        pk = man["packs"][name]
        pck = os.path.join(tmp, name + ".pck")
        with open(pck, "wb") as o:
            for part in pk["parts"]:
                o.write(open(os.path.join(ROOT, "data", part["file"]), "rb").read())
        if name.startswith("z_"):
            for rel, _, _ in soubory(pck):
                t = os.path.join(ROOT, rel)
                if rel.startswith(("modely/", ".godot/imported/")) and os.path.exists(t):
                    os.remove(t)
        celkem += rozbal(pck, ROOT)
        os.remove(pck)
    # desktopova cesta k texturam (jen pro beh v kontejneru; tablet bere path.etc2)
    opr = 0
    for r, _, fs in os.walk(os.path.join(ROOT, "modely")):
        for fn in fs:
            if fn.endswith(".import"):
                p = os.path.join(r, fn)
                t = open(p).read()
                if "\npath.etc2=" in t and "\npath=" not in t:
                    v = t.split("\npath.etc2=")[1].split("\n")[0]
                    open(p, "w").write(t.replace("\npath.etc2=" + v, "\npath.etc2=" + v + "\npath=" + v))
                    opr += 1
    print("rozbaleno %d souboru z %d baliku, desktopova cesta u %d textur" % (celkem, len(jmena), opr))


if __name__ == "__main__":
    sys.exit(main())
