extends Node
## Pohyblive dilky vymodelovane v Blenderu (blender/kit.py: movable): dvere, padaci most, padaci mriz
## a navijaky. Kazda skupina ma stav t (0 zavreno/dole .. 1 otevreno/nahore) a anima se plynule.

const SND := "res://zvuky/pohyb/"

var groups := {}          # id -> {t, target, dur, kind, items}
var chains: Array = []    # {mmi, a, item, e, n}
var ropes: Array = []     # {mi, a, item, e}
var _snd := {}
var _link_mesh: TorusMesh
var _iron: StandardMaterial3D


func setup(root: Node3D, list: Array, info: Dictionary) -> void:
	_iron = StandardMaterial3D.new()
	_iron.albedo_color = Color(0.09, 0.085, 0.08)
	_iron.metallic = 0.75
	_iron.roughness = 0.5
	_link_mesh = TorusMesh.new()
	_link_mesh.inner_radius = 0.024
	_link_mesh.outer_radius = 0.046
	_link_mesh.rings = 8
	_link_mesh.ring_segments = 5
	_link_mesh.material = _iron
	for n in ["dvere_otevrit", "dvere_zavrit", "vrzani1", "vrzani2", "zapadka"]:
		_snd[n] = load(SND + n + ".ogg")
	for e: Dictionary in list:
		var node := root.find_child(String(e["name"]), true, false) as Node3D
		if node == null:
			push_warning("pohyb: chybi uzel " + String(e["name"]))
			continue
		var it := {"node": node, "base": node.transform, "e": e}
		if (e["cols"] as Array).size() > 0:
			var body := AnimatableBody3D.new()
			body.sync_to_physics = false
			node.add_child(body)
			for c: Array in e["cols"]:
				var cs := CollisionShape3D.new()
				var b := BoxShape3D.new()
				b.size = Vector3(c[3], c[4], c[5])
				cs.shape = b
				cs.position = Vector3(c[0], c[1], c[2])
				body.add_child(cs)
		var g := String(e["group"])
		if not groups.has(g):
			groups[g] = {"t": 0.0, "target": 0.0, "dur": 1.0, "kind": "", "items": [], "player": null}
		var gr: Dictionary = groups[g]
		gr["items"].append(it)
		var kind := String(e["kind"])
		if kind != "navijak":
			gr["kind"] = kind
			gr["dur"] = float(e.get("dur", 1.0))
			var t0 := 0.0
			if kind == "mriz":
				t0 = float(e.get("init", 0.0)) / maxf(0.01, float(e["lift"]))
			elif e.has("open") and absf(float(e["open"])) > 0.01:
				t0 = float(e.get("init", 0.0)) / float(e["open"])
			gr["t"] = t0
			gr["target"] = t0
			var p := AudioStreamPlayer3D.new()
			p.max_distance = 40.0
			p.unit_size = 4.0
			node.add_child(p)
			gr["player"] = p
		if e.has("use"):
			var u: Array = e["use"]
			info["use"].append({"kind": "pohyb", "id": g, "pos": Vector3(u[0], u[1], u[2]), "r": 1.9 if kind == "navijak" else 2.3})
		for ch: Array in e.get("chains", []):
			var mmi := MultiMeshInstance3D.new()
			mmi.top_level = true
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = _link_mesh
			mm.instance_count = 80
			mmi.multimesh = mm
			root.add_child(mmi)
			chains.append({"mmi": mmi, "a": _v(ch[0]), "it": it, "e": _v(ch[1])})
		for rp: Array in e.get("ropes", []):
			var mi := MeshInstance3D.new()
			mi.top_level = true
			var cm := CylinderMesh.new()
			cm.top_radius = 0.016
			cm.bottom_radius = 0.016
			cm.height = 1.0
			cm.radial_segments = 6
			var rm := StandardMaterial3D.new()
			rm.albedo_color = Color(0.42, 0.35, 0.23)
			rm.roughness = 0.95
			cm.material = rm
			mi.mesh = cm
			root.add_child(mi)
			ropes.append({"mi": mi, "a": _v(rp[0]), "it": it, "e": _v(rp[1])})
	for g: String in groups:
		_apply(groups[g])
	_update_lines()


func _v(a: Array) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


## Prepne skupinu (dvere otevrit/zavrit, most zvednout/spustit, mriz vytahnout/spustit).
func toggle(id: String) -> void:
	if not groups.has(id):
		return
	var g: Dictionary = groups[id]
	g["target"] = 0.0 if float(g["target"]) > 0.5 else 1.0
	var p: AudioStreamPlayer3D = g["player"]
	if p:
		match String(g["kind"]):
			"dvere":
				p.stream = _snd["dvere_otevrit"] if float(g["target"]) > 0.5 else _snd["vrzani1"]
				p.pitch_scale = randf_range(0.9, 1.05)
			_:
				p.stream = _snd["vrzani2"]
				p.pitch_scale = 0.55
		p.play()


func label(id: String) -> String:
	if not groups.has(id):
		return "Použít"
	var g: Dictionary = groups[id]
	var up := float(g["target"]) > 0.5
	match String(g["kind"]):
		"dvere":
			return "Zavřít" if up else "Otevřít"
		"most":
			return "Spustit padací most" if up else "Zvednout padací most"
		"mriz":
			return "Spustit mříž" if up else "Vytáhnout mříž"
	return "Použít"


func _process(delta: float) -> void:
	var moved := false
	for id: String in groups:
		var g: Dictionary = groups[id]
		var t := float(g["t"])
		var tg := float(g["target"])
		if absf(t - tg) < 1e-4:
			continue
		var step := delta / maxf(0.05, float(g["dur"]))
		t = move_toward(t, tg, step)
		g["t"] = t
		_apply(g)
		moved = true
		if absf(t - tg) < 1e-4:
			var p: AudioStreamPlayer3D = g["player"]
			if p and String(g["kind"]) == "dvere" and tg < 0.5:
				p.stream = _snd["dvere_zavrit"]
				p.pitch_scale = 1.0
				p.play()
			elif p and String(g["kind"]) != "dvere":
				p.stream = _snd["zapadka"]
				p.pitch_scale = 0.7
				p.play()
	if moved:
		_update_lines()


func _apply(g: Dictionary) -> void:
	var t := float(g["t"])
	var k := t * t * (3.0 - 2.0 * t)      # plynuly rozjezd a dojezd
	for it: Dictionary in g["items"]:
		var e: Dictionary = it["e"]
		var node: Node3D = it["node"]
		var base: Transform3D = it["base"]
		match String(e["kind"]):
			"dvere":
				node.transform = base * Transform3D(Basis(Vector3.UP, deg_to_rad(float(e["open"]) * k)), Vector3.ZERO)
			"most":
				node.transform = base * Transform3D(Basis(Vector3.RIGHT, deg_to_rad(float(e["open"]) * k)), Vector3.ZERO)
			"mriz":
				node.transform = base * Transform3D(Basis.IDENTITY, Vector3(0, float(e["lift"]) * k, 0))
			"navijak":
				node.transform = base * Transform3D(Basis(Vector3.RIGHT, k * float(e.get("turns", 4.0)) * TAU), Vector3.ZERO)


func _update_lines() -> void:
	for c: Dictionary in chains:
		var it: Dictionary = c["it"]
		var a: Vector3 = c["a"]
		var b: Vector3 = (it["node"] as Node3D).global_transform * (c["e"] as Vector3)
		var mm: MultiMesh = (c["mmi"] as MultiMeshInstance3D).multimesh
		var L := a.distance_to(b)
		var n := clampi(int(L / 0.075), 2, mm.instance_count)
		var sag := 0.04 * L
		var prev := a
		for i in mm.instance_count:
			if i >= n:
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), a))
				continue
			var s := float(i + 1) / n
			var p := a.lerp(b, s) - Vector3(0, sag * sin(PI * s), 0)
			var d := (p - prev).normalized()
			var side := d.cross(Vector3.UP if absf(d.y) < 0.95 else Vector3.RIGHT).normalized()
			if i % 2 == 1:
				side = d.cross(side).normalized()
			var nrm := d.cross(side).normalized()
			var bas := Basis(d * 1.55, side, nrm)
			mm.set_instance_transform(i, Transform3D(bas, (p + prev) * 0.5))
			prev = p
	for r: Dictionary in ropes:
		var it2: Dictionary = r["it"]
		var a2: Vector3 = r["a"]
		var b2: Vector3 = (it2["node"] as Node3D).global_transform * (r["e"] as Vector3)
		var dv := b2 - a2
		var y := dv.normalized()
		var x := y.cross(Vector3.FORWARD if absf(y.z) < 0.9 else Vector3.RIGHT).normalized()
		var z := x.cross(y)
		(r["mi"] as MeshInstance3D).global_transform = Transform3D(Basis(x, y * dv.length(), z), (a2 + b2) * 0.5)
