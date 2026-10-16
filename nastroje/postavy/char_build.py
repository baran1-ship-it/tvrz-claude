"""Základ postavy z MPFB2 (MakeHuman, CC0): tělo podle věku a postavy, kostra game_engine, oči.
Spuštění: python3 char_build.py <jmeno> <pohlavi 0=žena..1=muž> <věk_let> [svaly 0..1] [váha 0..1] [výška 0..1]
"""
import sys
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy, os

NAME = sys.argv[1]
GENDER = float(sys.argv[2]); YEARS = float(sys.argv[3])
MUSCLE = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
WEIGHT = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
HEIGHT = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5

def age_value(y):
    # MakeHuman: 0 = 1 rok, 0.1875 = 11 let, 0.5 = 25 let, 1 = 90 let
    if y <= 11: return (y - 1) / 10 * 0.1875
    if y <= 25: return 0.1875 + (y - 11) / 14 * 0.3125
    return 0.5 + (y - 25) / 65 * 0.5

macro = {"gender": GENDER, "age": age_value(YEARS), "muscle": MUSCLE, "weight": WEIGHT,
         "proportions": 0.6, "height": HEIGHT, "cupsize": float(os.environ.get("CUP", "0.5")), "firmness": float(os.environ.get("FIRM", "0.5")),
         "race": {"asian": 0.0, "caucasian": 1.0, "african": 0.0}}
h = HumanService.create_human(macro_detail_dict=macro)
h.name = NAME
import json as _json
FACE = _json.load(open("/home/claude/chars/faces.json")).get(NAME, {})
_troot = "/home/claude/dl/mpfb2/src/mpfb/data/targets"
for tname, w in FACE.items():
    grp = tname.split("-")[0]
    grp = {"l": "eyes" if "eye" in tname else ("cheek" if "cheek" in tname else "ears"),
           "r": "eyes" if "eye" in tname else ("cheek" if "cheek" in tname else "ears"),
           "measure": "neck"}.get(grp, grp)
    path = os.path.join(_troot, grp, tname + ".target.gz")
    if not os.path.exists(path):
        print("MISSING TARGET", tname); continue
    TargetService.load_target(h, path, weight=w)
print("FACE targets", len(FACE))
HumanService.add_builtin_rig(h, "game_engine")
try:
    eyes = HumanService.add_mhclo_asset("/home/claude/dl/mh/makehuman/data/eyes/high-poly/high-poly.mhclo", h,
                                        asset_type="Eyes", subdiv_levels=0, material_type="GAMEENGINE")
    print("EYES", eyes.name, [m.name for m in eyes.data.materials])
except Exception as e:
    import traceback; traceback.print_exc(); print("EYES FAIL", e)
print("CHAR", NAME, "verts", len(h.data.vertices), "dims", tuple(round(x, 2) for x in h.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=f"/home/claude/chars/{NAME}_base.blend")
