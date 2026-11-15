"""Datove textury (tools/datove_textury.txt) pred importem Godotu nastavit bezztratove: compress/mode=0 a
detect_3d/compress_to=0. Bez toho Godot pri prvnim pouziti ve 3D prepne texturu na VRAM kompresi (ETC2) a prepise
.import (export 5. 11.: reka_dist/reka_flow znovu mode=2 -> hlidac kontrola_datovych_textur rc 11).
.import jsou v .gitignore (modely/), proto to musi delat export, ne rucni uprava."""
import os, re
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
for r in open("tools/datove_textury.txt", encoding="utf-8"):
    r = r.strip()
    if not r or r.startswith("#"):
        continue
    imp = r + ".import"
    if not os.path.exists(imp):
        continue
    t = open(imp, encoding="utf-8").read()
    if not re.search(r"^compress/mode=", t, re.M):
        # .import bez [params] (zdroj chybel pri predchozim importu, 15. 11.) -> Godot by zvolil vychozi kompresi
        t0 = t
        t = t.rstrip() + ("\n" if "[params]" in t else "\n\n[params]\n\n") + "compress/mode=0\ndetect_3d/compress_to=0\nmipmaps/generate=false\n"
        open(imp, "w", encoding="utf-8").write(t)
        print("datove textury: %s -> doplneny params bezztratove" % r)
    n = re.sub(r"^compress/mode=\d+", "compress/mode=0", t, flags=re.M)
    n = re.sub(r"^detect_3d/compress_to=\d+", "detect_3d/compress_to=0", n, flags=re.M)
    if n != t:
        open(imp, "w", encoding="utf-8").write(n)
        print("datove textury: %s -> bezztratove" % r)
