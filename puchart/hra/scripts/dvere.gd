extends Node
## Funkční dveře, vrata a padací mosty (Míša 3. 11.: „chci funkční brány a vrata“; 12. 11.: „oba mosty půjdou nějakým
## mechanismem zevnitř ovládat“; Havran kit.movable + scripts/pohyb.gd). Uzly Pohyb_* z hradu: dveře a vrata jsou ve glb
## otevřené, padací most spuštěný (průchod pro test i hráče); data/pohyb.json říká úhel, pant (dveře místní Y, most místní X)
## a kolizi. Hráč do DOSAH od místa ovládání (u mostu u navijáku uvnitř) dostane tlačítko; díly skupiny se pohnou spolu
## (stav t 0..1 plynule, dur s), naviják se točí, řetězy mostu se přepočítají (Havran pohyb._update_lines).
## Zavřené křídlo / most má kolizi (AnimatableBody3D jako dítě uzlu – pohybuje se s ním).
const DOSAH := 2.6
var hlavni: Node
var dily := {}        # skupina -> [{uzel, zaklad: Transform3D (glb), e}]
var stav := {}        # skupina -> true = průchozí (dveře otevřené, most spuštěný)
var t := {}           # skupina -> 0 = jak ve glb .. 1 = zavřeno / zvednuto
var cil := {}
var doba := {}
var druh := {}        # skupina -> "dvere" | "vrata" | "most"
var mista := {}       # skupina -> Vector3 (místo ovládání)
var retezy: Array = []   # {mmi, a (svět), uzel, e (místní)}
var tlacitko: Button
var _blizko := ""
var _clanek: TorusMesh

func zacni(h: Node, vrstva: CanvasLayer, jen_mosty := false) -> void:
	hlavni = h
	if not FileAccess.file_exists("res://data/pohyb.json"): return
	var hrad: Node = h.get_node_or_null("Hrad")
	if hrad == null: return
	var zelezo := StandardMaterial3D.new(); zelezo.albedo_color = Color(0.09, 0.085, 0.08); zelezo.metallic = 0.75; zelezo.roughness = 0.5
	_clanek = TorusMesh.new(); _clanek.inner_radius = 0.024; _clanek.outer_radius = 0.046; _clanek.rings = 8; _clanek.ring_segments = 5; _clanek.material = zelezo
	for e: Dictionary in JSON.parse_string(FileAccess.get_file_as_string("res://data/pohyb.json"))["dily"]:
		var u: Node3D = hrad.find_child(String(e["name"]), true, false)
		if u == null: continue
		var g: String = e.get("group", e["name"])
		var k := String(e.get("kind", "dvere"))
		if jen_mosty and k != "most": continue   # test průchodu: trasy jsou pro otevřené dveře, kolizi potřebují jen padací mosty
		var tel := AnimatableBody3D.new(); tel.sync_to_physics = false   # s true (Jolt) zůstala kolize v otevřené poloze – zavřená vrata pustila (pruchod:vrata_funkce)
		for c: Array in e.get("cols", []):
			var sh := CollisionShape3D.new(); var bx := BoxShape3D.new(); bx.size = Vector3(c[3], c[4], c[5])
			sh.shape = bx; sh.position = Vector3(c[0], c[1], c[2]); tel.add_child(sh)
		u.add_child(tel)
		if not dily.has(g): dily[g] = []; t[g] = 0.0; cil[g] = 0.0; stav[g] = true
		dily[g].append({"uzel": u, "zaklad": u.transform, "e": e})
		if k != "navijak": druh[g] = k; doba[g] = float(e.get("dur", 1.0))
		if e.has("use"): mista[g] = Vector3(e["use"][0], e["use"][1], e["use"][2])
		for ch: Array in e.get("chains", []):
			var mmi := MultiMeshInstance3D.new(); mmi.top_level = true
			var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = _clanek; mm.instance_count = 90
			mmi.multimesh = mm; mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(mmi)
			retezy.append({"mmi": mmi, "a": Vector3(ch[0][0], ch[0][1], ch[0][2]), "uzel": u, "e": Vector3(ch[1][0], ch[1][1], ch[1][2])})
	tlacitko = Button.new(); tlacitko.custom_minimum_size = Vector2(260, 90); Styl.tlacitko_pruh(tlacitko, load("res://fonty/GrenzeGotisch-Medium.ttf"), 30, 2)   # svitek (Havran styl.gd)
	tlacitko.anchor_left = 0.5; tlacitko.anchor_right = 0.5; tlacitko.anchor_top = 1.0; tlacitko.anchor_bottom = 1.0
	tlacitko.offset_left = -170; tlacitko.offset_right = 170; tlacitko.offset_top = -170; tlacitko.offset_bottom = -80
	tlacitko.visible = false; tlacitko.pressed.connect(func() -> void: prepni(_blizko))
	vrstva.add_child(tlacitko)
	call_deferred("_retezy")
	print("DVERE %d skupin, mostů %d, řetězů %d" % [dily.size(), druh.values().count("most"), retezy.size()])

func prepni(g: String) -> void:
	if not dily.has(g): return
	stav[g] = not stav[g]; cil[g] = 0.0 if stav[g] else 1.0
	if tlacitko: tlacitko.text = popis(g)

func popis(g: String) -> String:
	if druh.get(g, "") == "most": return "Zvednout padací most" if stav[g] else "Spustit padací most"
	return "Zavřít" if stav[g] else "Otevřít"

func _process(dt: float) -> void:
	var hnulo := false
	for g: String in dily:
		if absf(float(t[g]) - float(cil[g])) < 1e-4: continue
		t[g] = move_toward(float(t[g]), float(cil[g]), dt / maxf(0.05, float(doba.get(g, 1.0))))
		var k: float = t[g]; k = k * k * (3.0 - 2.0 * k)   # plynulý rozjezd a dojezd (Havran pohyb._apply)
		for d: Dictionary in dily[g]:
			var e: Dictionary = d["e"]; var z: Transform3D = d["zaklad"]; var u: Node3D = d["uzel"]
			match String(e.get("kind", "dvere")):
				"most": u.transform = z * Transform3D(Basis(Vector3.RIGHT, deg_to_rad(float(e.get("open", -80.0)) * k)), Vector3.ZERO)
				"navijak": u.transform = z * Transform3D(Basis(Vector3.RIGHT, k * float(e.get("turns", 6.0)) * TAU), Vector3.ZERO)
				_: u.transform = z * Transform3D(Basis(Vector3.UP, deg_to_rad(-float(e.get("open", 0.0)) * k)), Vector3.ZERO)
		hnulo = true
	if hnulo: _retezy()
	if tlacitko == null or hlavni.hrac == null: return
	if Engine.get_process_frames() % 6 != 0: return
	var p: Vector3 = hlavni.hrac.global_position + Vector3(0, 1.0, 0)
	var nej := ""; var nd := DOSAH
	for g in mista:
		var dd: float = p.distance_to(mista[g])
		if dd < nd: nd = dd; nej = g
	_blizko = nej
	tlacitko.visible = nej != ""
	if nej != "": tlacitko.text = popis(nej)

## Řetěz z kotvy ve zdi k oku na mostě, prověšený (Havran pohyb._update_lines).
func _retezy() -> void:
	for c: Dictionary in retezy:
		var a: Vector3 = c["a"]; var u: Node3D = c["uzel"]
		if not u.is_inside_tree(): continue
		var b: Vector3 = u.global_transform * (c["e"] as Vector3)
		var mm: MultiMesh = (c["mmi"] as MultiMeshInstance3D).multimesh
		var L := a.distance_to(b); var n := clampi(int(L / 0.075), 2, mm.instance_count); var sag := 0.04 * L; var prev := a
		for i in mm.instance_count:
			if i >= n:
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), a)); continue
			var s := float(i + 1) / n
			var q := a.lerp(b, s) - Vector3(0, sag * sin(PI * s), 0)
			var d := (q - prev).normalized()
			var side := d.cross(Vector3.UP if absf(d.y) < 0.95 else Vector3.RIGHT).normalized()
			if i % 2 == 1: side = d.cross(side).normalized()
			mm.set_instance_transform(i, Transform3D(Basis(d * 1.55, side, d.cross(side).normalized()), (q + prev) * 0.5))
			prev = q
