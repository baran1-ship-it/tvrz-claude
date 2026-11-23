"""Spojí impostory keřů (hra/textury/impostory/ker_<druh>_a/_n.png, 1024², blender/impostory.py) do jednoho atlasu
kere_vse_a/_n.png (4 × 3 políčka) + zápis "kere_atlas" do impostory.json – vzdálené keře (byliny.gd režim daleko) pak kreslí
všechny druhy jedním MultiMeshem na buňku (1 volání kreslení místo 11; hlídač scén 23. 11.: typ C nad 1000 volání).
  python3 nastroje/kere_atlas.py <koren>"""
import sys, json, os
from PIL import Image
K = sys.argv[1]; D = K + "/hra/textury/impostory"
meta = json.load(open(D + "/impostory.json"))
druhy = sorted(k[4:] for k in meta if k.startswith("ker_") and os.path.exists("%s/%s_a.png" % (D, k)))
SL, P = 4, 1024
RA = (len(druhy) + SL - 1) // SL
for s in ("a", "n"):
    im = Image.new("RGBA", (SL * P, RA * P), (0, 0, 0, 0) if s == "a" else (128, 128, 255, 0))
    for i, d in enumerate(druhy):
        t = Image.open("%s/ker_%s_%s.png" % (D, d, s)).convert("RGBA")
        if t.size != (P, P): t = t.resize((P, P), Image.LANCZOS)
        im.paste(t, ((i % SL) * P, (i // SL) * P))
    im.save("%s/kere_vse_%s.png" % (D, s), optimize=True)
meta["kere_atlas"] = {"sloupcu": SL, "radku": RA, "druhy": {d: i for i, d in enumerate(druhy)},
                      "pozn": "nastroje/kere_atlas.py – políčko i = sloupec i % sloupcu, řádek i // sloupcu; uvnitř 8×8 pohledů jako ker_<druh>"}
json.dump(meta, open(D + "/impostory.json", "w"), ensure_ascii=False, indent=1)
print("KERE_ATLAS", len(druhy), "druhů", SL, "×", RA)
