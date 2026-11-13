import bpy
from common import imp, UAL1, UAL2
def load_actions():
    """Načte akce UAL1+UAL2 (kostry se smažou), vrátí dict název->akce.
    Pokud už v souboru jsou (zapečené), vrátí ty."""
    ex = {a.name: a for a in bpy.data.actions if a.use_fake_user}
    if len(ex) > 20: return ex
    before = set(bpy.data.actions)
    for p in (UAL1, UAL2, "/home/claude/tvrz-claude/modely/postavy/animace_ual/postavy_idle.glb"):
        objs = imp(p)
        for o in objs:
            if o.type == 'ARMATURE' and o.animation_data: o.animation_data.action = None
        for o in objs: bpy.data.objects.remove(o)
    acts = {a.name: a for a in bpy.data.actions if a not in before}
    for a in acts.values(): a.use_fake_user = True
    return acts
def assign(arm, act, frame=None):
    if not arm.animation_data: arm.animation_data_create()
    arm.animation_data.action = act
    if act.slots and hasattr(arm.animation_data, "action_slot"):
        arm.animation_data.action_slot = act.slots[0]
    if frame is not None: bpy.context.scene.frame_set(int(frame))
