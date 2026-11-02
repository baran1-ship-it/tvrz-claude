extends RefCounted
## Předehřátí shaderů při načtení (převzato z Havrana main.gd _predehrej_shadery, 0.62 bod 8 a 0.96): renderer Compatibility
## sestaví program až při prvním kreslení materiálu (Adreno 20–100 ms, někdy přes 1 s) → záseky při prvním vstupu do lesa,
## k vodě, do sklepa s pochodní. Každá kombinace (síť, MultiMesh s barvou/daty, stín, materiál) se jednou nakreslí na drobné
## kopii před kamerou, i podrost, který vzniká až za chůze (byliny.gd), a varianty s bodovým světlem (pochodně).
## Tablet 2. 11.: les max 964 ms a 130 záseků jen v prvním průchodu. PUCHART_BEZ_PREDEHRATI=1 vypne (měření).

static func kopie(g: GeometryInstance3D, koren: Node3D, videno: Dictionary) -> int:
	var mesh: Mesh = null; var mm: MultiMesh = null
	if g is MultiMeshInstance3D:
		mm = (g as MultiMeshInstance3D).multimesh
		if mm == null or mm.mesh == null: return 0
		mesh = mm.mesh
	elif g is MeshInstance3D:
		mesh = (g as MeshInstance3D).mesh
	if mesh == null or not g.is_visible_in_tree(): return 0
	var klic := [mm != null, mm.use_colors if mm else false, mm.use_custom_data if mm else false,
		g.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, g.transparency > 0.0,
		g.material_override.get_rid() if g.material_override else RID()]
	for si in mesh.get_surface_count():
		var m: Material = mesh.surface_get_material(si)
		if g is MeshInstance3D and (g as MeshInstance3D).get_surface_override_material(si):
			m = (g as MeshInstance3D).get_surface_override_material(si)
		klic.append(m.get_rid() if m else RID())
	var k := str(klic)
	if videno.has(k): return 0
	videno[k] = true
	var c: GeometryInstance3D
	if mm:
		var m2 := MultiMesh.new(); m2.transform_format = mm.transform_format
		m2.use_colors = mm.use_colors; m2.use_custom_data = mm.use_custom_data; m2.mesh = mesh; m2.instance_count = 1
		var mmi := MultiMeshInstance3D.new(); mmi.multimesh = m2; c = mmi
	else:
		var mi := MeshInstance3D.new(); mi.mesh = mesh
		for si in mesh.get_surface_count():
			mi.set_surface_override_material(si, (g as MeshInstance3D).get_surface_override_material(si))
		c = mi
	c.material_override = g.material_override; c.cast_shadow = g.cast_shadow; c.transparency = g.transparency
	c.extra_cull_margin = 16384.0; c.scale = Vector3.ONE * 0.002
	koren.add_child(c)
	return 1

## síte navíc (podrost za chůze): [Mesh]
static func predehrej(koren_sveta: Node3D, cam: Camera3D, navic: Array, snimku := 4) -> void:
	if OS.has_environment("PUCHART_BEZ_PREDEHRATI") or cam == null: return
	var t0 := Time.get_ticks_usec()
	var koren := Node3D.new(); koren.name = "Predehrati"; koren_sveta.add_child(koren)
	koren.global_transform = Transform3D(cam.global_basis, cam.global_position - cam.global_basis.z * 3.0)
	var videno := {}; var n := 0
	for gi in koren_sveta.find_children("*", "GeometryInstance3D", true, false):
		if gi.get_parent() != koren: n += kopie(gi as GeometryInstance3D, koren, videno)
	for mesh: Mesh in navic:
		var m3 := MultiMesh.new(); m3.transform_format = MultiMesh.TRANSFORM_3D; m3.mesh = mesh; m3.instance_count = 1
		var mmi := MultiMeshInstance3D.new(); mmi.multimesh = m3
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; mmi.extra_cull_margin = 16384.0
		mmi.scale = Vector3.ONE * 0.002; koren.add_child(mmi); n += 1
	var ls := OmniLight3D.new(); ls.omni_range = 6.0; ls.light_energy = 0.01; koren.add_child(ls)   # varianta s pochodní
	for i in snimku:
		await koren_sveta.get_tree().process_frame
	koren.queue_free()
	print("PREDEHRATI %d kopii, %.0f ms" % [n, (Time.get_ticks_usec() - t0) / 1000.0])
