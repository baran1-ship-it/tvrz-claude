extends SceneTree
## Potok Bystrice pres Waterways (addons/waterways, MIT): sit reky podel krivky toku a zapecene mapy proudeni
## a peny z kolizi (brehy, kameny v korytu). Hra pak pouziva vlastni shader pro Compatibility (shaders/reka.gdshader):
## hloubka neni z hloubkove textury (Compatibility ji nema), ale ve vrcholech (COLOR.r = hloubka vody v m).
##   xvfb-run -a godot --path . --rendering-method gl_compatibility -s res://tools/reka_bake.gd
## Vstup: modely/tvrz.glb (teren, Reka_voda = hladina, kameny), modely/reka/osa.json (osa toku z blender/kraj.py REKA).
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
	var osa: Array = JSON.parse_string(FileAccess.get_file_as_string("res://modely/reka/osa.json"))
	for i in 3:
		await physics_frame
	var space := root.get_world_3d().direct_space_state
	var body: Array[Vector3] = []
	var sirky: Array[float] = []
	for k in osa.size():
		var p: Array = osa[k]
		if not ACT.has_point(Vector2(p[0], p[1])):
			continue
		# smer toku a kolmice
		var a: Array = osa[maxi(0, k - 1)]
		var c: Array = osa[mini(osa.size() - 1, k + 1)]
		var t := Vector2(float(c[0]) - float(a[0]), float(c[1]) - float(a[1])).normalized()
		var nrm := Vector2(-t.y, t.x)
		# hladina ze dna: nejnizsi misto napric korytem (+-4 m) + 0,4 m (stara sit mela diry -> suche useky)
		var dno := INF
		for o: float in [-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]:
			var q := Vector2(p[0], p[1]) + nrm * o
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(q.x, 200.0, q.y), Vector3(q.x, -200.0, q.y)))
			if not h.is_empty():
				dno = minf(dno, (h["position"] as Vector3).y)
		if dno == INF:
			continue
		var y := dno + 0.4
		# sirka: kam az je teren pod hladinou (+1,5 m pod breh, okraj schova teren)
		var sir := 0.0
		for s: float in [-1.0, 1.0]:
			var d := 0.5
			while d < 14.0:
				var q := Vector2(p[0], p[1]) + nrm * d * s
				var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(q.x, y + 30.0, q.y), Vector3(q.x, y - 30.0, q.y)))
				if not h.is_empty() and (h["position"] as Vector3).y > y + 0.05:
					break
				d += 0.5
			sir = maxf(sir, d)
		body.append(Vector3(p[0], y, p[1]))
		sirky.append(clampf(sir * 2.0 + 1.0, 3.0, 11.0))
	print("reka: bodu osy ", body.size())
	# vyhladit hladinu podel toku (nikdy nestoupa po proudu)
	# vyhladit hladinu podel toku (klouzavy prumer 5 bodu, ne pod mistni hladinu)
	var ys: Array[float] = []
	for b in body:
		ys.append(b.y)
	for k in body.size():
		var s := 0.0
		var n := 0
		for j in range(maxi(0, k - 2), mini(body.size(), k + 3)):
			s += ys[j]
			n += 1
		body[k].y = clampf(s / n, ys[k] - 0.15, ys[k] + 0.1)   # vyhlazeni, ale vzdy 0,25-0,5 m nad dnem
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
