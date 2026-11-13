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
var _zvuk := {}       # zvuky Havrana (hra/zvuky/pohyb, Kenney CC0): skupina -> {hrac: přehrávač u dílu, smycka: řetěz/rachot}
var _tik := {}
const ZV := "res://zvuky/pohyb/"

func zacni(h: Node, vrstva: CanvasLayer, jen_mosty := false) -> void:
	hlavni = h
	var hrad: Node = h.get_node_or_null("Hrad")
	var zelezo := StandardMaterial3D.new(); zelezo.albedo_color = Color(0.09, 0.085, 0.08); zelezo.metallic = 0.75; zelezo.roughness = 0.5
	_clanek = TorusMesh.new(); _clanek.inner_radius = 0.024; _clanek.outer_radius = 0.046; _clanek.rings = 8; _clanek.ring_segments = 5; _clanek.material = zelezo
	if hrad != null and FileAccess.file_exists("res://data/pohyb.json"):
		for e: Dictionary in JSON.parse_string(FileAccess.get_file_as_string("res://data/pohyb.json"))["dily"]:
			var u: Node3D = hrad.find_child(String(e["name"]), true, false)
			if u == null: continue
			if jen_mosty and String(e.get("kind", "dvere")) != "most": continue   # test průchodu: trasy jsou pro otevřené dveře, kolizi potřebují jen padací mosty
			_pridej(u, e, e.get("group", e["name"]))
	# ves, krčma, hájovna (Míša 13. 11.: „jako na hradě tak i ves, hospoda, hájovna – funkční dveře, vrata, vrátka“):
	# dveře domů z data/pohyb_mista.json (nastroje/pohyb_mista.py, souřadnice uzlu dveří – stejné pro každou instanci domu,
	# skupina dveře@dům), vrata a vrátka plotů zapisuje ves.gd (pohyb_dily, souřadnice světa)
	if not jen_mosty:
		var mi: Node = h.get_node_or_null("Mista")
		if mi != null and FileAccess.file_exists("res://data/pohyb_mista.json"):
			for e: Dictionary in JSON.parse_string(FileAccess.get_file_as_string("res://data/pohyb_mista.json"))["dily"]:
				for u: Node in mi.find_children(String(e["name"]), "Node3D", true, false):
					_pridej(u as Node3D, e, "%s@%s" % [e.get("group", e["name"]), u.get_parent().name])
		var ves: Node = h.get_node_or_null("Ves")
		if ves != null and ves.get("pohyb_dily") != null:
			for e: Dictionary in ves.pohyb_dily:
				var u: Node3D = ves.find_child(String(e["name"]), true, false)
				if u != null: _pridej(u, e, e.get("group", e["name"]))
	if dily.is_empty(): return
	tlacitko = Button.new(); tlacitko.custom_minimum_size = Vector2(260, 90); Styl.tlacitko_pruh(tlacitko, load("res://fonty/GrenzeGotisch-Medium.ttf"), 30, 2)   # svitek (Havran styl.gd)
	tlacitko.anchor_left = 0.5; tlacitko.anchor_right = 0.5; tlacitko.anchor_top = 1.0; tlacitko.anchor_bottom = 1.0
	tlacitko.offset_left = -170; tlacitko.offset_right = 170; tlacitko.offset_top = -170; tlacitko.offset_bottom = -80
	tlacitko.visible = false; tlacitko.pressed.connect(func() -> void: prepni(_blizko))
	vrstva.add_child(tlacitko)
	call_deferred("_retezy")
	print("DVERE %d skupin, mostů %d, řetězů %d, ve vsi a místech %d" % [dily.size(), druh.values().count("most"), retezy.size(), dily.keys().filter(func(x: String) -> bool: return x.contains("@") or x.begins_with("ves_")).size()])

## jeden pohyblivý díl: kolize (AnimatableBody3D jako dítě uzlu), skupina, zvuk, místo ovládání, řetězy.
## glb_zavreno (domy Havrana, vrata plotů): díl je v modelu zavřený – základ = otevřená poloha (otočení o open), ve hře
## výchozí stav otevřeno jako na hradě; use_mistni = místo ovládání v souřadnicích uzlu (počítá se v zavřené poloze)
func _pridej(u: Node3D, e: Dictionary, g: String) -> void:
	var k := String(e.get("kind", "dvere"))
	var tel := AnimatableBody3D.new(); tel.sync_to_physics = false   # s true (Jolt) zůstala kolize v otevřené poloze – zavřená vrata pustila (pruchod:vrata_funkce)
	for c: Array in e.get("cols", []):
		var sh := CollisionShape3D.new(); var bx := BoxShape3D.new(); bx.size = Vector3(c[3], c[4], c[5])
		sh.shape = bx; sh.position = Vector3(c[0], c[1], c[2]); tel.add_child(sh)
		if c.size() > 6: sh.rotation.x = deg_to_rad(float(c[6]))   # deska padacího mostu ve sklonu
	u.add_child(tel)
	if not u.has_meta("pohyb_use"):   # zacni běží i víckrát (snímek, test průchodu) – díl se otevře a místo spočte jen poprvé
		var uw: Vector3 = Vector3(e["use"][0], e["use"][1], e["use"][2]) if e.has("use") else (u.global_transform * Vector3(e["use_mistni"][0], e["use_mistni"][1], e["use_mistni"][2]) if e.has("use_mistni") else Vector3.INF)
		u.set_meta("pohyb_use", uw)
		if bool(e.get("glb_zavreno", false)): u.transform = u.transform * Transform3D(Basis(Vector3.UP, deg_to_rad(float(e.get("open", 0.0)))), Vector3.ZERO)
		u.set_meta("pohyb_zaklad", u.transform)
	if (u.get_meta("pohyb_use") as Vector3) != Vector3.INF: mista[g] = u.get_meta("pohyb_use")
	if not dily.has(g): dily[g] = []; t[g] = 0.0; cil[g] = 0.0; stav[g] = true
	dily[g].append({"uzel": u, "zaklad": u.get_meta("pohyb_zaklad"), "e": e})
	if k != "navijak": druh[g] = k; doba[g] = float(e.get("dur", 1.0))
	if not _zvuk.has(g): _zvuk[g] = {}
	var hp := AudioStreamPlayer3D.new(); hp.max_distance = 60.0; hp.unit_size = 8.0 if k != "navijak" else 3.0; u.add_child(hp)
	_zvuk[g]["navijak" if k == "navijak" else "dil"] = hp   # Havran pohyb.gd: zvuk u dílu, rohatka u navijáku
	for ch: Array in e.get("chains", []):
		var mmi := MultiMeshInstance3D.new(); mmi.top_level = true
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = _clanek; mm.instance_count = 90
		mmi.multimesh = mm; mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(mmi)
		retezy.append({"mmi": mmi, "a": Vector3(ch[0][0], ch[0][1], ch[0][2]), "uzel": u, "e": Vector3(ch[1][0], ch[1][1], ch[1][2])})

func prepni(g: String) -> void:
	if not dily.has(g): return
	stav[g] = not stav[g]; cil[g] = 0.0 if stav[g] else 1.0
	if tlacitko: tlacitko.text = popis(g)
	var z: Dictionary = _zvuk.get(g, {})
	match String(druh.get(g, "dvere")):   # Havran pohyb.toggle
		"most":
			for kl in ["dil", "navijak"]:
				if z.has(kl):
					var sm := AudioStreamPlayer3D.new(); sm.stream = _ogg("retez", true); sm.max_distance = 60.0; sm.unit_size = 12.0
					sm.pitch_scale = 0.8 if not stav[g] else 0.95; (z[kl] as Node).get_parent().add_child(sm); sm.play()   # rachot řetězu po celou dobu pohybu
					if z.has("smycka_" + kl): (z["smycka_" + kl] as Node).queue_free()
					z["smycka_" + kl] = sm
		"vrata": _hraj(z.get("dil"), "vrata_otevrit" if not stav[g] else "vrzani1", 0.5)
		_: _hraj(z.get("dil"), "dvere_otevrit" if stav[g] else "vrzani1", randf_range(0.9, 1.05))
	var pr := get_parent()
	if druh.get(g, "") == "most" and pr != null and pr.get("hv") != null and pr.hv.get("hud") != null:   # z ochozu most nevidí – nápis
		pr.hv.hud.toast("Naviják – padací most se " + ("spouští" if stav[g] else "zvedá"), 2.5)

func _ogg(jm: String, smycka := false) -> AudioStreamOggVorbis:
	var a: AudioStreamOggVorbis = load(ZV + jm + ".ogg")
	if smycka: a = a.duplicate(); a.loop = true
	return a

func _hraj(p: Variant, jm: String, vyska := 1.0) -> void:
	if p == null: return
	var hp := p as AudioStreamPlayer3D; hp.stream = _ogg(jm); hp.pitch_scale = vyska; hp.play()

## konec pohybu: dopad mostu / zapadka, konec rachotu (Havran pohyb._process_vlastni)
func _dojel(g: String) -> void:
	var z: Dictionary = _zvuk.get(g, {})
	for kl in ["dil", "navijak"]:
		if z.has("smycka_" + kl): (z["smycka_" + kl] as Node).queue_free(); z.erase("smycka_" + kl)
	match String(druh.get(g, "dvere")):
		"most": _hraj(z.get("dil"), "dopad_most" if stav[g] else "zapadka", 1.0 if stav[g] else 0.7)
		"vrata": _hraj(z.get("dil"), "vrata_zavrit" if not stav[g] else "zapadka", 0.55)
		_: if not stav[g]: _hraj(z.get("dil"), "dvere_zavrit")

func popis(g: String) -> String:
	if druh.get(g, "") == "most": return "Zvednout padací most" if stav[g] else "Spustit padací most"
	return "Zavřít" if stav[g] else "Otevřít"

func _process(dt: float) -> void:
	var hnulo := false
	for g: String in dily:
		if absf(float(t[g]) - float(cil[g])) < 1e-4: continue
		t[g] = move_toward(float(t[g]), float(cil[g]), dt / maxf(0.05, float(doba.get(g, 1.0))))
		if absf(float(t[g]) - float(cil[g])) < 1e-4: _dojel(g)
		elif druh.get(g, "") == "most":   # rohatka navijáku během pohybu (Havran: tik po 0,13 s)
			_tik[g] = float(_tik.get(g, 0.0)) + dt
			if float(_tik[g]) > 0.13: _tik[g] = 0.0; _hraj(_zvuk.get(g, {}).get("navijak"), "rohatka", randf_range(0.55, 0.7) if not stav[g] else randf_range(0.75, 0.9))
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
