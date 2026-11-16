"""Předměty z funkcí zajímavých míst do katalogu brašny (pravidla/svet/zajimava_mista.json predmety; Míša 16. 11.):
uhlí, smola a lomový kámen v katalogu Havrana nejsou – každý záznam = scéna hra/modely/predmety_h/<id>.tscn s modelem
katalogu (pytel, hrnec) nebo kamenem lomu ve zmenšeném měřítku + záznam v hra/modely/predmety_h.json (jméno, váha, rozměr)
+ ikona 128 px (nastroje/godot/ikony_predmetu.gd, jako lůžka a nádobí). Po predmety_z_havrana.sh (katalog musí existovat).
  python3 nastroje/predmety_mist.py <K> [--ikony]"""
import sys, os, json, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from glb_sit import nacti, cti, matice

K = os.path.abspath(sys.argv[1]); PR = json.load(open(K + "/pravidla/svet/zajimava_mista.json"))["predmety"]["zaznamy"]
PRED = K + "/hra/modely/predmety_h"; KATP = K + "/hra/modely/predmety_h.json"
if not os.path.exists(KATP): print("PREDMETY_MIST bez katalogu (nastroje/predmety_z_havrana.sh)"); sys.exit(0)
KAT = json.load(open(KATP)); ids = []


def rozmer(glb):
    j, b, _ = nacti(glb); P = []
    def walk(i, M):
        n = j["nodes"][i]; M = M @ matice(n)
        if "mesh" in n and "colonly" not in n.get("name", ""):
            for p in j["meshes"][n["mesh"]]["primitives"]:
                X = cti(j, b, p["attributes"]["POSITION"]); P.append((np.c_[X, np.ones(len(X))] @ M.T)[:, :3])
        for c in n.get("children", []): walk(c, M)
    for r in j["scenes"][j.get("scene", 0)]["nodes"]: walk(r, np.eye(4))
    P = np.vstack(P); return P.max(0) - P.min(0)


for pid, z in PR.items():
    glb = K + "/hra/" + z["model"].replace("res://", "")
    if not os.path.exists(glb): print("PREDMETY_MIST model chybí", glb); continue
    s = float(z.get("meritko", 1.0))
    open(os.path.join(PRED, pid + ".tscn"), "w").write("\n".join([
        '[gd_scene load_steps=2 format=3]', '', '[ext_resource type="PackedScene" path="%s" id="1"]' % z["model"], '',
        '[node name="%s" type="Node3D"]' % pid, '',
        '[node name="Model" parent="." instance=ExtResource("1")]', 'transform = Transform3D(%g, 0, 0, 0, %g, 0, 0, 0, %g, 0, 0, 0)' % (s, s, s), '']))
    r = rozmer(glb) * s
    KAT[pid] = {"nazev": z["nazev"], "kat": z["kat"], "stav": z["stav"], "vaha": z["vaha"], "cena": z["cena"],
                "rozmer": [round(float(v), 3) for v in r], "zdroj": z["zdroj"]}
    ids.append(pid); print("PREDMETY_MIST %s %s rozměr %s" % (pid, z["nazev"], KAT[pid]["rozmer"]))
json.dump(KAT, open(KATP, "w"), ensure_ascii=False, indent=1)
if "--ikony" in sys.argv and ids:
    G = os.environ.get("G", "/opt/godot47/Godot_v4.7.2-stable_linux.x86_64")
    shutil.copy2(K + "/nastroje/godot/ikony_predmetu.gd", K + "/hra/_ikony_mist.gd")
    subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 640x400x24", G, "--rendering-driver", "opengl3", "--path", K + "/hra", "-s", "res://_ikony_mist.gd", "--"] + ids)
    for f in ("_ikony_mist.gd", "_ikony_mist.gd.uid"):
        if os.path.exists(K + "/hra/" + f): os.remove(K + "/hra/" + f)
print("PREDMETY_MIST hotovo: %d předmětů" % len(ids))
