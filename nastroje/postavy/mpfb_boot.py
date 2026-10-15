import sys, os, importlib
import bpy, addon_utils
bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.extensions.repo_refresh_all()
except Exception as e:
    print("refresh", e)
r = addon_utils.enable("bl_ext.user_default.mpfb", default_set=True, handle_error=lambda e: print("ENABLE ERR", repr(e)))
print("ENABLED", r)
def dyn(path, key):
    for amod in list(sys.modules):
        if amod.endswith(path):
            return getattr(importlib.import_module(amod), key)
    raise ValueError(path)
HumanService = dyn("mpfb.services.humanservice", "HumanService")
TargetService = dyn("mpfb.services.targetservice", "TargetService")
HumanObjectProperties = dyn("mpfb.entities.objectproperties", "HumanObjectProperties")
