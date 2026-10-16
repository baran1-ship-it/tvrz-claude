"""Rozpocet graficke pameti (cil < 700 MB v klidu): limit rozliseni textur podle druhu, vse VRAM komprese + mipmapy.
Spousti se pred kazdym importem (export rostlin slozku maze i s nastavenim).  python3 tools/limity_textur.py"""
import os
import re

STROMY = ("smrk", "dub", "lipa", "briza", "buk", "olse", "vrba", "borovice")
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def limit(rel):
    p = rel.replace("\\", "/")
    if p.startswith("modely/rostliny/"):
        n = os.path.basename(p)
        return 1024 if n.startswith(STROMY) or n.startswith("skala_") else 512
    if p.startswith(("modely/", "textures/", "obrazky/impostory/")):
        return 1024
    return 0


n = 0
for d in ("modely", "textures", "obrazky/impostory"):
    for r, _, fs in os.walk(os.path.join(root, d)):
        for f in fs:
            if not f.endswith(".import"):
                continue
            path = os.path.join(r, f)
            t = open(path).read()
            if 'importer="texture"' not in t:
                continue
            lim = limit(os.path.relpath(path, root))
            if not lim:
                continue
            t2 = re.sub(r"compress/mode=\d", "compress/mode=2", t)
            t2 = re.sub(r"mipmaps/generate=\w+", "mipmaps/generate=true", t2)
            if "process/size_limit=" in t2:
                t2 = re.sub(r"process/size_limit=\d+", "process/size_limit=%d" % lim, t2)
            else:
                t2 = t2.rstrip("\n") + "\nprocess/size_limit=%d\n" % lim
            if t2 != t:
                open(path, "w").write(t2)
                n += 1
print("limity textur: upraveno %d" % n)
