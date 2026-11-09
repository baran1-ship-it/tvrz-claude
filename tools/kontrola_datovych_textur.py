"""Hlidac: datove textury (tools/datove_textury.txt) bezztratove a bez orezu pro tablet. rc 1 = chyba."""
import os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
chyby = []
for r in open("tools/datove_textury.txt", encoding="utf-8"):
    r = r.strip()
    if not r or r.startswith("#"):
        continue
    imp = r + ".import"
    if not os.path.exists(imp):
        chyby.append(r + ": chybi .import")
        continue
    t = open(imp, encoding="utf-8").read()
    m = re.search(r"^compress/mode=(\d+)", t, re.M)
    if not m or m.group(1) != "0":
        chyby.append(r + ": compress/mode=%s (ma byt 0 bezztratove)" % (m.group(1) if m else "?"))
    if "path.etc2=" in t:
        chyby.append(r + ": ma ETC2 variantu (VRAM komprese) - znovu importovat")
if os.path.exists("build/textury_tablet.txt"):
    tt = open("build/textury_tablet.txt").read()
    for r in open("tools/datove_textury.txt", encoding="utf-8"):
        r = r.strip()
        if r and not r.startswith("#") and os.path.basename(r) in tt:
            chyby.append(r + ": orezana pro tablet (textury_tablet)")
# Puchart 9. 11. bod 1: obracene - kazda jina textura (kresli se ve 3D) musi mit mipmapy a VRAM kompresi, jinak
# blika v dalce a zatezuje Adreno (textura nactena jen skriptem se importuje jako 2D bez mipmap a bezztratove)
_dat = set(r.strip() for r in open("tools/datove_textury.txt", encoding="utf-8") if r.strip() and not r.startswith("#"))
for d, _, fs in os.walk("."):
    if d.startswith(("./.godot", "./build", "./.git")):
        continue
    for f in fs:
        if not f.endswith(".import"):
            continue
        imp = os.path.join(d, f)
        r = imp[2:-len(".import")]
        if r in _dat:
            continue
        t = open(imp, encoding="utf-8").read()
        if 'importer="texture"' not in t:
            continue
        if re.search(r"^mipmaps/generate=false", t, re.M) or re.search(r"^compress/mode=0", t, re.M):
            chyby.append(r + ": textura bez mipmap nebo bez VRAM komprese (datova? pak do tools/datove_textury.txt)")
print("DATOVE_TEXTURY %s %s" % ("OK" if not chyby else "CHYBA", chyby))
sys.exit(1 if chyby else 0)
