extends SceneTree
## Potok Bystrice pres Waterways (addons/waterways, MIT): sit reky podel krivky toku a zapecene mapy proudeni
## a peny z kolizi (brehy, kameny v korytu). Hra pak pouziva vlastni shader pro Compatibility (shaders/reka.gdshader):
## hloubka neni z hloubkove textury (Compatibility ji nema), ale ve vrcholech (COLOR.r = hloubka vody v m).
##   xvfb-run -a godot --path . --rendering-method gl_compatibility -s res://tools/reka_bake.gd
## Vstup: modely/tvrz.glb (teren, Reka_voda = hladina, kameny), pravidla/svet/voda.json potok.osa (osa toku, cte i blender/kraj.py).
## Vystup: modely/reka/reka.res (sit), reka_flow.png (proudeni RG, pena B, sum A), reka_dist.png, reka.json.

const RiverManager := preload("res://addons/waterways/river_manager.gd")
const ACT := Rect2(-245.0, -245.0, 1140.0, 1590.0)
const ROZLISENI := 1024

var reka


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	var svet: Node3D = (load("res://modely/tvrz.glb") as PackedScene).instantiate()
	root.add_child(svet)
	var hladina: MeshInstance3D = null
	var kolize := 0
	# koryto stejne jako ve hre (scripts/koryto.gd): vyska terenu z mrizky louky v svet.json
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://modely/svet.json"))
	var sv: RefCounted = preload("res://scripts/svet.gd").new({})
	sv.data = data
	var kor: RefCounted = preload("res://scripts/koryto.gd").new()
	kor.priprav(sv._vyska)
	for n in svet.find_children("Teren*", "MeshInstance3D", true, false):
		if String(n.name) == "Teren_reka" or String(n.name) == "Teren_most":
			kor.pokryj(n as MeshInstance3D)               # jako svet.gd: podlaha brehu jen v Teren_reka
	for n in svet.find_children("Teren*", "MeshInstance3D", true, false):
		if String(n.name) != "Teren_obzor" and String(n.name) != "Teren_cesta_kamen":
			kor.vyhloub(n as MeshInstance3D)
	for n in svet.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		if nm == "Reka_voda":
			hladina = mi
			continue
		if nm.begins_with("Teren") or nm.begins_with("Reka") or nm.begins_with("Most"):
			var b := StaticBody3D.new()
			var cs := CollisionShape3D.new()
			var tri := mi.mesh.create_trimesh_shape()
			tri.backface_collision = true
			cs.shape = tri
			b.add_child(cs)
			mi.add_child(b)
			kolize += 1
	print("reka: kolize ", kolize, ", hladina ", hladina != null)
	# hladina ze stavajici site vody (mrizka 1 m): vyska podle nejblizsiho vrcholu
	var hv := {}
	for v: Vector3 in hladina.mesh.get_faces():
		var w := hladina.global_transform * v
		hv[Vector2i(roundi(w.x), roundi(w.z))] = w.y
	for i in 3:
		await physics_frame
	# hladina a sirka z koryta (ne z paprsku na dno) - voda sedi do vyhloubeneho terenu
	var body: Array[Vector3] = []
	var sirky: Array[float] = []
	for k in kor.body.size():
		var p: Vector2 = kor.body[k]
		if not ACT.has_point(p):
			continue
		body.append(Vector3(p.x, kor.hladiny[k], p.y))
		# voda o kus pres sikmy breh (okraj schova teren); 0,6 m siroka voda v Waterways po vyhlazeni krivky pretekala
		# pres travu (Misa 0.67, (240,1031)) - 0,35 m, breh drzi koryto.podlaha
		sirky.append((kor.sirky[k] + 0.35) * 2.0)
	print("reka: bodu osy ", body.size())
	var space := root.get_world_3d().direct_space_state
	var curve := Curve3D.new()
	curve.bake_interval = 0.5
	for k in body.size():
		var a := body[maxi(0, k - 1)]
		var c := body[mini(body.size() - 1, k + 1)]
		var tan := (c - a) * 0.25
		curve.add_point(body[k], -tan, tan)
	var w: Array[float] = []
	for s in sirky:
		w.append(s)
	reka = RiverManager.new()
	reka.name = "Reka"
	reka.curve = curve
	reka.widths = w
	reka.shape_step_length_divs = 6
	reka.shape_step_width_divs = 6
	reka.shape_smoothness = 0.5
	reka.baking_raycast_distance = 6.0
	root.add_child(reka)
	reka._generate_river()
	await physics_frame
	await physics_frame
	print("reka: sit ", (reka.mesh_instance.mesh as ArrayMesh).get_faces().size() / 3, " troj., zapekam ", ROZLISENI)
	await reka._generate_flowmap(ROZLISENI)
	DirAccess.make_dir_recursive_absolute("res://modely/reka")
	(reka.flow_foam_noise as Texture2D).get_image().save_png("res://modely/reka/reka_flow.png")
	(reka.dist_pressure as Texture2D).get_image().save_png("res://modely/reka/reka_dist.png")
	# hloubka do vrcholu (COLOR.r, m): paprsek z hladiny dolu na dno
	var mesh: ArrayMesh = reka.mesh_instance.mesh
	var arr := mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var cols := PackedColorArray()
	cols.resize(verts.size())
	var xf: Transform3D = reka.mesh_instance.global_transform
	for i in verts.size():
		var wv: Vector3 = xf * verts[i]
		var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(wv + Vector3(0, 0.05, 0), wv - Vector3(0, 6.0, 0)))
		var dep: float = 0.0 if h.is_empty() else wv.y - (h["position"] as Vector3).y
		cols[i] = Color(clampf(dep, 0.0, 4.0) / 4.0, 0.0, 0.0, 1.0)
	arr[Mesh.ARRAY_COLOR] = cols
	var out := ArrayMesh.new()
	out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	ResourceSaver.save(out, "res://modely/reka/reka.res")
	var meta := {"uv2_sides": reka._uv2_sides, "steps": reka._steps, "bodu": body.size()}
	FileAccess.open("res://modely/reka/reka.json", FileAccess.WRITE).store_string(JSON.stringify(meta))
	print("reka: hotovo ", meta)
	quit()


func _hladina(hv: Dictionary, x: float, z: float) -> float:
	var best := NAN
	var bd := 1e9
	for dx in range(-6, 7):
		for dz in range(-6, 7):
			var k := Vector2i(roundi(x) + dx, roundi(z) + dz)
			if hv.has(k) and dx * dx + dz * dz < bd:
				bd = dx * dx + dz * dz
				best = hv[k]
	return best
