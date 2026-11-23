extends Node
## Měření troj. ve dvou Míšiných polohách (plán E1): po vrstvách (vše, bez Louka, bez Byliny, bez Kere)
const POLOHY := [["sever", 131.4, 276.4, 0.0], ["273", 146.7, 311.0, 273.0]]
func _ready() -> void:
	var h := get_parent()
	h.set("_foto", "")
	await get_tree().process_frame
	h.hrac.set_physics_process(false)
	var cam: Camera3D = get_viewport().get_camera_3d()
	cam.top_level = true
	for p in POLOHY:
		var y: float = h.svet.vyska(p[1], p[2]) + 1.65
		var a := deg_to_rad(float(p[3]))
		var pos := Vector3(p[1], y, p[2])
		var cil := pos + Vector3(sin(a), 0, -cos(a)) * 50.0
		cam.look_at_from_position(pos, cil, Vector3.UP)
		h.hrac.position = pos - Vector3(0, 1.65, 0)
		for i in 500: await get_tree().process_frame
		var r := {}
		for v in ["vse", "Louka", "Byliny", "Kere"]:
			for jm in ["Louka", "Byliny", "Kere"]:
				var n: Node3D = h.get_node_or_null(jm)
				if n: n.visible = (jm != v)
			for i in 6: await get_tree().process_frame
			r[v] = RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
		for jm in ["Louka", "Byliny", "Kere"]: (h.get_node(jm) as Node3D).visible = true
		var lo: Node = h.get_node("Louka"); var inst := [0, 0]; var bu := [0, 0]
		for k in lo.bunky:
			if lo.bunky[k] != null: var mm_: MultiMesh = (lo.bunky[k] as MultiMeshInstance3D).multimesh; inst[k.z] += mm_.visible_instance_count if mm_.visible_instance_count >= 0 else mm_.instance_count; bu[k.z] += 1
		print("MERTROJ louka instance jemne %d (%d bunek), pas %d (%d bunek)" % [inst[0], bu[0], inst[1], bu[1]])
		print("MERTROJ %s vse %.3f M  louka %.3f  byliny %.3f  kere %.3f  kresleni %d" % [p[0], r["vse"] / 1e6, (r["vse"] - r["Louka"]) / 1e6, (r["vse"] - r["Byliny"]) / 1e6, (r["vse"] - r["Kere"]) / 1e6, RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)])
		if OS.get_environment("MER_FOTO") != "":
			for i in 4: await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png(OS.get_environment("MER_FOTO") + "_" + p[0] + ".png")
	get_tree().quit()
