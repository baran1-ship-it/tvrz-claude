import sys
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy, importlib, os
sys.path.insert(0, "/home/claude/chars")
import skin_mat, head_features
NAME = sys.argv[1]
SKIN = {"zena": "/home/claude/dl/mhassets/skins/onlytheghosts_young_eurasian_female/young_eurasian_female_diffuse.png"}.get(NAME)
if SKIN and not os.path.exists(SKIN): SKIN = None
P = {
 "muz":  dict(tone=(0.26, 0.15, 0.105), freckles=0.0, stubble=0.85, age=0.45, ruddy=0.45, brow=(0.075, 0.055, 0.04),
              hair="muz", hcol=(0.065, 0.045, 0.032)),
 "zena": dict(tone=(0.3, 0.18, 0.13), freckles=0.15, stubble=0.0, age=0.08, ruddy=0.35, brow=(0.05, 0.035, 0.025),
              hair="zena", hcol=(0.05, 0.032, 0.022)),
 "kluk": dict(tone=(0.36, 0.2, 0.14), freckles=0.8, stubble=0.0, age=0.1, ruddy=0.55, brow=(0.34, 0.15, 0.06),
              hair="kluk", hcol=(0.30, 0.10, 0.04)),
}[NAME]
import os, json, numpy as np
from PIL import Image as _PI
_fj = f"/home/claude/chars/foto/{NAME}_predni.json"
if os.path.exists(_fj) and NAME == "muz":
    _pp = np.array(json.load(open(_fj))); _ar = np.asarray(_PI.open(_fj.replace(".json", ".jpg")).convert("RGB")).astype(float) / 255
    _r = max(4, int(np.linalg.norm(_pp[16] - _pp[0]) / 30))
    _c = np.mean([_ar[int(_pp[k][1]) - _r:int(_pp[k][1]) + _r, int(_pp[k][0]) - _r:int(_pp[k][0]) + _r].reshape(-1, 3).mean(0) for k in (2, 3, 13, 14, 31, 35)], 0)
    _lin = np.where(_c <= 0.04045, _c / 12.92, ((_c + 0.055) / 1.055) ** 2.4)
    P["tone"] = tuple(float(x) * 1.3 * k for x, k in zip(_lin, (1.12, 0.97, 0.85))); print("TONE z fotky", P["tone"])
bpy.ops.wm.open_mainfile(filepath=f"/home/claude/chars/{NAME}_base.blend")
body = bpy.data.objects[NAME]
L = head_features.landmarks(body)
print("LANDMARKS", {k: tuple(round(x, 3) for x in v) for k, v in L.items() if hasattr(v, "x")})
skin_mat.apply(body, tone=P["tone"], freckles=P["freckles"], stubble=P["stubble"], age=P["age"], ruddy=P["ruddy"],
               L=L, brow_col=P["brow"], brow_th=0.0040 if NAME == "zena" else (0.0055 if NAME == "muz" else 0.0045), brow_amt=0.95 if SKIN else (0.6 if NAME == "zena" else 0.85), tex=SKIN, tint=(0.88, 0.78, 0.7))
# vlasy: MakeHuman system assets (mh_hair.py); procedurální slupka se už nepoužívá
import mh_hair
if NAME == "zena":
    # cop a rozpuštěné vlasy z MakeHuman system assets (CC0), tónované do tmavě hnědé
    mh_hair.add(HumanService, body, "braid01", f"{NAME}_cop", None, recolor=(0.30, 0.19, 0.13))
    mh_hair.add(HumanService, body, "long01", f"{NAME}_rozpustene", None, recolor=(0.30, 0.19, 0.13))
elif NAME == "muz":
    mh_hair.add(HumanService, body, "short02", f"{NAME}_vlasy", "bogdan666_short_02_brown", tint=(0.3, 0.24, 0.2), grey=0.05)
else:
    mh_hair.add(HumanService, body, "short02", f"{NAME}_vlasy", "bogdan666_short_02_red", tint=(0.62, 0.34, 0.2))
LASH = "/home/claude/dl/mhassets/eyelashes/mindfront_eyelashes_02/mindfront_eyelashes_02.mhclo"
if os.path.exists(LASH):
    try:
        la = HumanService.add_mhclo_asset(LASH, body, asset_type="Eyelashes", subdiv_levels=0, material_type="GAMEENGINE")
        print("LASHES", la.name, [m.name for m in la.data.materials])
    except Exception as e:
        import traceback; traceback.print_exc(); print("LASH FAIL", e)
eyes = bpy.data.objects.get(f"{NAME}.high-poly")
if eyes:
    img = bpy.data.images.load(f"/home/claude/chars/eye_{NAME}.png")
    for m in eyes.data.materials:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.name == "DiffuseTexture": n.image = img
bpy.ops.wm.save_as_mainfile(filepath=f"/home/claude/chars/{NAME}_head.blend")
