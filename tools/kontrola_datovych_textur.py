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
print("DATOVE_TEXTURY %s %s" % ("OK" if not chyby else "CHYBA", chyby))
sys.exit(1 if chyby else 0)
