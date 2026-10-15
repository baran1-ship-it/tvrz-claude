import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
o = bpy.data.objects[sys.argv[2]]
mode = sys.argv[3]
for m in o.data.materials:
    if m.name.endswith("_listi"):
        nt = m.node_tree
        b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        if "nonormal" in mode:
            for l in list(b.inputs["Normal"].links): nt.links.remove(l)
if "nocustom" in mode:
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
        except Exception as e: print("clear fail", e)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[4])
