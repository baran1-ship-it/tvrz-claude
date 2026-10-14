extends Node
## Pohyblive dilky vymodelovane v Blenderu (blender/kit.py: movable): dvere, padaci most, padaci mriz
## a navijaky. Kazda skupina ma stav t (0 zavreno/dole .. 1 otevreno/nahore) a anima se plynule.

const SND := "res://zvuky/pohyb/"

var groups := {}          # id -> {t, target, dur, kind, items}
var chains: Array = []    # {mmi, a, item, e, n}
var ropes: Array = []     # {mi, a, item, e}
var _snd := {}
var _root: Node3D
var _warm := 0
var _link_mesh: TorusMesh
var _iron: StandardMaterial3D


func setup(root: Node3D, list: Array, info: Dictionary) -> void:
	_root = root
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
	for n in ["dvere_otevrit", "dvere_zavrit", "vrzani1", "vrzani2", "vrzani3", "zapadka", "dopad_drevo", "dopad_zelezo",
			"rohatka", "vrata_otevrit", "vrata_zavrit", "retez", "dopad_most", "dopad_mriz", "vrata_smycka"]:
		_snd[n] = load(SND + n + ".ogg")
	(_snd["retez"] as AudioStreamOggVorbis).loop = true
	(_snd["vrata_smycka"] as AudioStreamOggVorbis).loop = true
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
			groups[g] = {"t": 0.0, "target": 0.0, "dur": 1.0, "kind": "", "items": [], "player": null, "rachot": null, "tik": 0.0}
		var gr: Dictionary = groups[g]
		gr["items"].append(it)
		var kind := String(e["kind"])
		if kind != "navijak":
			gr["kind"] = kind
			gr["dur"] = float(e.get("dur", 1.0))
			var t0 := 0.0
			if kind == "mriz" or kind == "vedro":
				t0 = float(e.get("init", 0.0)) / (float(e["lift"]) if absf(float(e["lift"])) > 0.01 else 1.0)
			elif e.has("open") and absf(float(e["open"])) > 0.01:
				t0 = float(e.get("init", 0.0)) / float(e["open"])
			gr["t"] = t0
			gr["target"] = t0
			var p := AudioStreamPlayer3D.new()
			p.max_distance = 60.0
			p.unit_size = 8.0
			node.add_child(p)
			gr["player"] = p
			if kind == "most" or kind == "mriz" or kind == "vrata":
				# po celou dobu pohybu: rachot retezu a kladek (most, mriz), skripot tezkych vrat
				var lp := AudioStreamPlayer3D.new()
				lp.stream = _snd["vrata_smycka" if kind == "vrata" else "retez"]
				lp.max_distance = 60.0
				lp.unit_size = 12.0
				lp.volume_db = 0.0
				node.add_child(lp)
				gr["smycka"] = lp
		if kind == "navijak":
			# rachot rohatky u navijaku a navijeni retezu/lana na buben
			var rp := AudioStreamPlayer3D.new()
			rp.max_distance = 30.0
			rp.unit_size = 3.0
			node.add_child(rp)
			gr["rachot"] = rp
			if e.has("navin"):
				it["navin"] = _coil(node, e["navin"])
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


func _coil(node: Node3D, nv: Dictionary) -> MultiMeshInstance3D:
	# navinuty retez nebo lano: clanky/useky po sroubovici na bubnu (lokalni osa X), vic vrstev
	var r := float(nv["r"])
	var L := float(nv["L"]) - 0.5
	var chain := String(nv["typ"]) == "retez"
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	if chain:
		mm.mesh = _link_mesh
	else:
		var cm := CylinderMesh.new()
		cm.top_radius = 0.018
		cm.bottom_radius = 0.018
		cm.height = 0.085
		cm.radial_segments = 5
		var rm := StandardMaterial3D.new()
		rm.albedo_color = Color(0.42, 0.35, 0.23)
		rm.roughness = 0.95
		cm.material = rm
		mm.mesh = cm
	var pitch := 0.1 if chain else 0.04          # posun po ose na otacku
	var step := 0.075 if chain else 0.07
	var pts := []
	var x := -L / 2
	var rr := r + 0.03
	var ang := 0.0
	var dirx := 1.0
	while pts.size() < 600:
		pts.append([x, rr, ang])
		var da := step / rr
		ang += da
		x += dirx * pitch * da / TAU
		if x > L / 2 or x < -L / 2:
			dirx = -dirx
			rr += 0.045 if chain else 0.035
			x = clampf(x, -L / 2, L / 2)
		if rr > r + 0.2:
			break
	mm.instance_count = pts.size()
	for i in pts.size():
		var q: Array = pts[i]
		var a := float(q[2])
		var p := Vector3(float(q[0]), cos(a) * float(q[1]), sin(a) * float(q[1]))
		var tang := Vector3(0, -sin(a), cos(a))
		var radial := Vector3(0, cos(a), sin(a))
		var bas: Basis
		if chain:
			var side := radial if i % 2 == 0 else Vector3.RIGHT
			bas = Basis(tang * 1.55, side, tang.cross(side).normalized())
		else:
			bas = Basis(Vector3.RIGHT, tang, radial)
		mm.set_instance_transform(i, Transform3D(bas, p))
	mm.visible_instance_count = 0
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	node.add_child(mmi)
	return mmi


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
			"vrata":
				p.stream = _snd["vrata_otevrit"] if float(g["target"]) > 0.5 else _snd["vrzani3"]
				p.pitch_scale = 0.5
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
		"vrata":
			return "Zavřít vrata" if up else "Otevřít vrata"
		"most":
			return "Spustit padací most" if up else "Zvednout padací most"
		"mriz":
			return "Spustit mříž" if up else "Vytáhnout mříž"
		"vedro":
			return "Vytáhnout vědro" if up else "Spustit vědro"
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
		var lp: AudioStreamPlayer3D = g.get("smycka")
		if lp:
			if absf(t - tg) < 1e-4:
				lp.stop()
			elif not lp.playing:
				lp.pitch_scale = 0.8 if tg > t else 0.95       # zvedani pomaleji a tezceji
				lp.play()
		# rachot rohatky navijaku behem pohybu
		var rp: AudioStreamPlayer3D = g.get("rachot")
		if rp:
			g["tik"] = float(g["tik"]) + delta
			if float(g["tik"]) > 0.13:
				g["tik"] = 0.0
				rp.stream = _snd["rohatka"]
				rp.pitch_scale = randf_range(0.55, 0.7) if tg > t else randf_range(0.75, 0.9)
				rp.volume_db = 2.0
				rp.play()
		if absf(t - tg) < 1e-4:
			var p: AudioStreamPlayer3D = g["player"]
			var kind := String(g["kind"])
			if p == null:
				continue
			p.pitch_scale = 1.0
			p.volume_db = 0.0
			if kind == "dvere" and tg < 0.5:
				p.stream = _snd["dvere_zavrit"]
			elif kind == "vrata":
				p.stream = _snd["vrata_zavrit"] if tg < 0.5 else _snd["dopad_drevo"]
				p.pitch_scale = 0.55
				p.volume_db = 0.0 if tg < 0.5 else -6.0
			elif kind == "most" and tg < 0.5:
				# tezky dreveny most dopadl na kraj prikopu
				p.stream = _snd["dopad_most"]
				p.max_distance = 70.0
				p.unit_size = 10.0
				p.volume_db = 6.0
			elif kind == "vedro":
				# vedro dosedlo na hladinu / nahore narazilo na buben
				p.stream = _snd["dopad_drevo"] if tg > 0.5 else _snd["zapadka"]
				p.pitch_scale = 1.6 if tg > 0.5 else 0.9
				p.volume_db = -4.0
			elif kind == "mriz" and tg < 0.5:
				# zelezna mriz dopadla na dlazbu
				p.stream = _snd["dopad_mriz"]
				p.max_distance = 70.0
				p.unit_size = 10.0
				p.volume_db = 2.0
			elif kind != "dvere":
				p.stream = _snd["zapadka"]
				p.pitch_scale = 0.7
			else:
				continue
			p.play()
	# prvni snimky po nacteni prepocitat vzdy (globalni transformace jeste nemusi byt platne)
	if _warm < 30:
		_warm += 1
		moved = true
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
			"dvere", "vrata":
				node.transform = base * Transform3D(Basis(Vector3.UP, deg_to_rad(float(e["open"]) * k)), Vector3.ZERO)
			"most":
				node.transform = base * Transform3D(Basis(Vector3.RIGHT, deg_to_rad(float(e["open"]) * k)), Vector3.ZERO)
			"mriz", "vedro":
				node.transform = base * Transform3D(Basis.IDENTITY, Vector3(0, float(e["lift"]) * k, 0))
			"navijak":
				node.transform = base * Transform3D(Basis(Vector3.RIGHT, k * float(e.get("turns", 4.0)) * TAU), Vector3.ZERO)
				if it.has("navin"):
					# navinuto podle stavu: zvednuty most / vytazena mriz = plny buben
					var mm: MultiMesh = (it["navin"] as MultiMeshInstance3D).multimesh
					var full := (1.0 - k) if bool(e["navin"].get("obracene", false)) else k
					mm.visible_instance_count = int(round(full * mm.instance_count))


func _update_lines() -> void:
	for c: Dictionary in chains:
		var it: Dictionary = c["it"]
		var a: Vector3 = c["a"]
		var b: Vector3 = _world(it) * (c["e"] as Vector3)
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
		var b2: Vector3 = _world(it2) * (r["e"] as Vector3)
		var dv := b2 - a2
		var y := dv.normalized()
		var x := y.cross(Vector3.FORWARD if absf(y.z) < 0.9 else Vector3.RIGHT).normalized()
		var z := x.cross(y)
		(r["mi"] as MeshInstance3D).global_transform = Transform3D(Basis(x, y * dv.length(), z), (a2 + b2) * 0.5)


## Svetova transformace dilku slozena z rodicu (nezavisi na tom, zda uz je spocitana globalni).
func _world(it: Dictionary) -> Transform3D:
	var n: Node3D = it["node"]
	var t := n.transform
	var p := n.get_parent()
	while p != null and p is Node3D:
		t = (p as Node3D).transform * t
		p = p.get_parent()
	return t


# ------------------------------------------------------------------ ulozeni

func to_save() -> Dictionary:
	var out := {}
	for id: String in groups:
		out[id] = float(groups[id]["target"])
	return out


func from_save(d: Dictionary) -> void:
	# stav mechanismu (otevreno / zavreno) hned bez animace a zvuku
	for id: String in d:
		if not groups.has(id):
			continue
		var g: Dictionary = groups[id]
		g["target"] = float(d[id])
		g["t"] = float(d[id])
		_apply(g)
	_warm = 0
	_update_lines()
