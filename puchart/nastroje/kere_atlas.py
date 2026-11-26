"""Spojí impostory keřů (hra/textury/impostory/ker_<druh>_a/_n.png, 1024², blender/impostory.py) do jednoho atlasu
kere_vse_a/_n.png (4 × 3 políčka) + zápis "kere_atlas" do impostory.json – vzdálené keře (byliny.gd režim daleko) pak kreslí
všechny druhy jedním MultiMeshem na buňku (1 volání kreslení místo 11; hlídač scén 23. 11.: typ C nad 1000 volání).
Byliny (Míša 26. 11.: „pořád doskakují keře atd., musí tam něco být místo nich“): stejně byl_<druh> → byliny_vse.
  python3 nastroje/kere_atlas.py <koren> [predpona=ker_] [atlas=kere_vse]"""
import sys, json, os
from PIL import Image
K = sys.argv[1]; D = K + "/hra/textury/impostory"
PRE = sys.argv[2] if len(sys.argv) > 2 else "ker_"; AT = sys.argv[3] if len(sys.argv) > 3 else "kere_vse"
meta = json.load(open(D + "/impostory.json"))
druhy = sorted(k[len(PRE):] for k in meta if k.startswith(PRE) and os.path.exists("%s/%s_a.png" % (D, k)))
SL = 4
P = Image.open("%s/%s%s_a.png" % (D, PRE, druhy[0])).size[0]   # políčko = velikost atlasu druhu (keře 1024, byliny 512)
RA = (len(druhy) + SL - 1) // SL
for s in ("a", "n"):
    im = Image.new("RGBA", (SL * P, RA * P), (0, 0, 0, 0) if s == "a" else (128, 128, 255, 0))
    for i, d in enumerate(druhy):
        t = Image.open("%s/%s%s_%s.png" % (D, PRE, d, s)).convert("RGBA")
        if t.size != (P, P): t = t.resize((P, P), Image.LANCZOS)
        im.paste(t, ((i % SL) * P, (i // SL) * P))
    im.save("%s/%s_%s.png" % (D, AT, s), optimize=True)
meta.pop("kere_atlas", None)
meta[AT] = {"sloupcu": SL, "radku": RA, "druhy": {d: i for i, d in enumerate(druhy)},
                      "pozn": "nastroje/kere_atlas.py – políčko i = sloupec i %% sloupcu, řádek i // sloupcu; uvnitř 8×8 pohledů jako %s<druh>" % PRE}
json.dump(meta, open(D + "/impostory.json", "w"), ensure_ascii=False, indent=1)
print("ATLAS", AT, len(druhy), "druhů", SL, "×", RA)
