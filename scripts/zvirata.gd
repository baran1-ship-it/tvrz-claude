extends Node3D
## Zvirata vsi (Misa 29. 10.: „do vesnice zvirata, ale premyslej“; pravidla/svet/zvirata.json): ovce v kosari, prasata
## v ohradce za chalupou, slepice volne po dvore. Svet (svet.gd _ohrady) dava data "zvirata" - ohrada = stred, natoceni
## a pulrozmery (zvire zustane uvnitr o okraj_m od plutku), dvur = stred a polomer. Modely s kostrou (modely/zvirata,
## Misa 29. 10., zvirata.json modely): v klidu vlastni klip modelu, pri chuzi houpani kosti nohou (Misa 0.992 „slepice
## nehybou nohama“), pastva = predklon, slepice utika pred hracem. Zvuky
## zvuky/zvirata/<druh>_N.ogg v nahodnych chvilich z mista zvirete. Daleko (dosah_m) se zvirata nehybou ani nekresli.

const Pravidla := preload("res://scripts/pravidla.gd")

var main: Node
var _zv: Array = []                  # {node, telo, druh, ch (chovani), mez, cil, stav_t, rych, utek, pastva, zvuk_t, hrac}
var _rng := RandomNumberGenerator.new()
var _zvuky := {}


func setup(p_main: Node) -> void:
	main = p_main
	_rng.seed = 2910
	var ch_vse: Dictionary = Pravidla.cti("zvirata", "chovani")
	for z: Dictionary in main.svet.data.get("zvirata", []):
		var druh := String(z["zvire"])
		var path := "res://modely/zvirata/%s.glb" % druh
		if not ResourceLoader.exists(path) or not ch_vse.has(druh):
			push_warning("zvirata: chybi model nebo chovani %s" % druh)
			continue
		var ps: PackedScene = load(path)
		var ch: Dictionary = ch_vse[druh]
		var c := Vector3(z["stred"][0], z["stred"][1], z["stred"][2])
		print("zvirata: %s %s x%d u %s" % [z["id"], druh, int(z["kusu"]), c.snapped(Vector3.ONE * 0.1)])
		var mez := {"c": c, "yaw": float(z["yaw"])}
		if z.has("pul"):
			mez["pul"] = Vector2(float(z["pul"][0]) - float(ch_vse["okraj_m"]), float(z["pul"][1]) - float(ch_vse["okraj_m"]))
		else:
			mez["r"] = float(z["polomer"])
		for i in int(z["kusu"]):
			var n := Node3D.new()
			n.name = "Zvire_%s_%d" % [String(z["id"]), i]
			add_child(n)
			# n = poloha a smer chuze (+z vpred), kl = predklon (pastva, zobani), telo = model otoceny hlavou na +z (vpred_st)
			var kl := Node3D.new()
			n.add_child(kl)
			var telo: Node3D = ps.instantiate()
			kl.add_child(telo)
			telo.rotation.y = deg_to_rad(float(ch["vpred_st"]))
			telo.scale = Vector3.ONE * float(ch.get("meritko", 1.0))
			var kostra: Skeleton3D = null
			var nohy: Array = []                 # [kost, faze rad]
			for sk in telo.find_children("*", "Skeleton3D", true, false):
				kostra = sk as Skeleton3D
				for nf: Array in ch.get("nohy", []):
					var b := _kost(kostra, String(nf[0]))
					if b >= 0:
						nohy.append([b, deg_to_rad(float(nf[1]))])
					else:
						push_warning("zvirata: %s bez kosti %s" % [druh, nf[0]])
				break
			var ap: AnimationPlayer = null
			for a in telo.find_children("*", "AnimationPlayer", true, false):
				ap = a as AnimationPlayer
				if ap.get_animation_list().size() > 0:
					var an := ap.get_animation(ap.get_animation_list()[0])
					an.loop_mode = Animation.LOOP_LINEAR
					ap.play(ap.get_animation_list()[0])
					ap.seek(_rng.randf() * an.length, true)
				break
			for g in telo.find_children("*", "GeometryInstance3D", true, false):
				var gi := g as GeometryInstance3D
				gi.visibility_range_end = float(ch["dosah_m"])
				gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if bool(ch["stin"]) else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var p := _nahodny_bod(mez)
			n.global_position = Vector3(p.x, _zem(p), p.y)
			n.rotation.y = _rng.randf() * TAU
			_zv.append({"node": n, "telo": kl, "druh": druh, "ch": ch, "mez": mez, "cil": p, "stav_t": _rng.randf_range(0.0, 3.0),
					"rych": 0.0, "pastva": 0.0, "kostra": kostra, "nohy": nohy, "ap": ap, "krok": 0.0, "jde": false, "zvuk_t": _rng.randf_range(float(ch["zvuk_s"][0]), float(ch["zvuk_s"][1])), "faze": _rng.randf() * TAU})
	print("zvirata: %d kusu" % _zv.size())


## Kost podle jmena bez ohledu na znaky mezi slovy (Godot muze tecku v nazvu kosti z glTF nahradit).
func _kost(sk: Skeleton3D, jm: String) -> int:
	var hledej := jm.to_lower().replace(".", "").replace("_", "")
	for b in sk.get_bone_count():
		if sk.get_bone_name(b).to_lower().replace(".", "").replace("_", "").begins_with(hledej):
			return b
	return -1


## Chuze: klip modelu stoji, nohy se houpou kolem bocni osy modelu (kost v prostoru rodice), faze podle ujite drahy.
## Stani: nohy zpet do klidu, klip modelu bezi.
func _nohy(z: Dictionary, krok_m: float, jde: bool) -> void:
	var sk: Skeleton3D = z["kostra"]
	if sk == null or (z["nohy"] as Array).is_empty():
		return
	var ap: AnimationPlayer = z["ap"]
	if jde != bool(z["jde"]):
		z["jde"] = jde
		if ap:
			if jde:
				ap.pause()
			else:
				ap.play()
		if not jde:
			for nf: Array in z["nohy"]:
				sk.set_bone_pose_rotation(int(nf[0]), sk.get_bone_rest(int(nf[0])).basis.get_rotation_quaternion())
	if not jde:
		return
	var ch: Dictionary = z["ch"]
	var faze := float(z["krok"]) / maxf(0.05, krok_m) * TAU
	for nf: Array in z["nohy"]:
		var b := int(nf[0])
		var rodic := sk.get_bone_parent(b)
		var osa := Vector3.RIGHT
		if rodic >= 0:
			osa = (sk.get_bone_global_rest(rodic).basis.inverse() * Vector3.RIGHT).normalized()
		var ang := deg_to_rad(float(ch["noha_st"])) * sin(faze + float(nf[1]))
		sk.set_bone_pose_rotation(b, Quaternion(osa, ang) * sk.get_bone_rest(b).basis.get_rotation_quaternion())


## Nahodny bod uvnitr meze (ohrada nebo dvur) ve vodorovne rovine.
func _nahodny_bod(mez: Dictionary) -> Vector2:
	var c: Vector3 = mez["c"]
	if mez.has("pul"):
		var pul: Vector2 = mez["pul"]
		var l := Vector2(_rng.randf_range(-pul.x, pul.x), _rng.randf_range(-pul.y, pul.y))
		var w := Basis(Vector3.UP, float(mez["yaw"])) * Vector3(l.x, 0.0, l.y)
		return Vector2(c.x + w.x, c.z + w.z)
	var a := _rng.randf() * TAU
	var r := sqrt(_rng.randf()) * float(mez["r"])
	return Vector2(c.x + cos(a) * r, c.z + sin(a) * r)


## Bod do meze (zvire nikdy neprojde plutkem).
func _do_meze(mez: Dictionary, p: Vector2) -> Vector2:
	var c: Vector3 = mez["c"]
	if mez.has("pul"):
		var b := Basis(Vector3.UP, float(mez["yaw"]))
		var l := b.inverse() * Vector3(p.x - c.x, 0.0, p.y - c.z)
		var pul: Vector2 = mez["pul"]
		var w := b * Vector3(clampf(l.x, -pul.x, pul.x), 0.0, clampf(l.z, -pul.y, pul.y))
		return Vector2(c.x + w.x, c.z + w.z)
	var q := p - Vector2(c.x, c.z)
	return Vector2(c.x, c.z) + q.limit_length(float(mez["r"]))


func _zem(p: Vector2) -> float:
	return float(main.svet.call("_vyska", p.x, p.y))


func _process(dt: float) -> void:
	if _zv.is_empty() or main.player == null:
		return
	var pp: Vector3 = main.player.global_position
	var roz := float(Pravidla.cti("zvirata", "chovani", "rozestup_m"))
	for z: Dictionary in _zv:
		var n: Node3D = z["node"]
		var ch: Dictionary = z["ch"]
		var gp := n.global_position
		if gp.distance_to(pp) > float(ch["dosah_m"]):
			continue
		var p2 := Vector2(gp.x, gp.z)
		var cil: Vector2 = z["cil"]
		# utek pred hracem (slepice): cil pryc od hrace, rychle
		var utek := float(ch["utek_m"]) > 0.0 and Vector2(pp.x, pp.z).distance_to(p2) < float(ch["utek_m"])
		if utek:
			var od := (p2 - Vector2(pp.x, pp.z)).normalized()
			cil = _do_meze(z["mez"], p2 + od * 2.5 + Vector2(_rng.randf_range(-0.6, 0.6), _rng.randf_range(-0.6, 0.6)))
			z["cil"] = cil
			z["stav_t"] = 0.0
		var k := cil - p2
		var rych := float(ch["utek_rychlost_m_s"]) if utek else float(ch["rychlost_m_s"])
		if k.length() > 0.08:
			# chuze: natocit k cili (plynule), pak krok; jine zvire v ceste = stat a vybrat jiny cil
			var smer := atan2(k.x, k.y)
			n.rotation.y = lerp_angle(n.rotation.y, smer, minf(1.0, dt * (6.0 if utek else 2.5)))
			var krok := minf(k.length(), rych * dt)
			var nova := p2 + Vector2(sin(n.rotation.y), cos(n.rotation.y)) * krok
			var blok := false
			for o: Dictionary in _zv:
				if o != z and o["mez"] == z["mez"] and Vector2((o["node"] as Node3D).global_position.x, (o["node"] as Node3D).global_position.z).distance_to(nova) < roz:
					blok = true
					break
			if blok and not utek:
				z["cil"] = _do_meze(z["mez"], _nahodny_bod(z["mez"]))
			else:
				nova = _do_meze(z["mez"], nova)
				n.global_position = Vector3(nova.x, _zem(nova), nova.y)
			z["pastva"] = move_toward(float(z["pastva"]), 0.0, dt * 2.0)
		else:
			# stani: pastva / zobani (predklon a klip modelu), po case novy cil
			_nohy(z, float(ch.get("krok_m", 0.3)), false)
			z["stav_t"] = float(z["stav_t"]) - dt
			z["pastva"] = move_toward(float(z["pastva"]), 1.0, dt * 0.8)
			if float(z["stav_t"]) <= 0.0:
				z["cil"] = _nahodny_bod(z["mez"])
				z["stav_t"] = _rng.randf_range(float(ch["stani_s"][0]), float(ch["stani_s"][1]))
		var telo: Node3D = z["telo"]
		z["faze"] = float(z["faze"]) + dt
		if ch.has("zobani_hz"):
			var zob := maxf(0.0, sin(float(z["faze"]) * TAU * float(ch["zobani_hz"]))) * float(z["pastva"])
			telo.rotation.x = deg_to_rad(float(ch["zobani_st"])) * zob
		else:
			telo.rotation.x = deg_to_rad(float(ch["pastva_st"])) * float(z["pastva"]) + sin(float(z["faze"]) * 0.7) * 0.01
		# zvuk z mista zvirete
		z["zvuk_t"] = float(z["zvuk_t"]) - dt
		if float(z["zvuk_t"]) <= 0.0:
			z["zvuk_t"] = _rng.randf_range(float(ch["zvuk_s"][0]), float(ch["zvuk_s"][1]))
			_zvuk(n, String(ch["zvuk"]))


func _zvuk(n: Node3D, druh: String) -> void:
	if not _zvuky.has(druh):
		var arr: Array = []
		for i in range(1, 6):
			var pth := "res://zvuky/zvirata/%s_%d.ogg" % [druh, i]
			if ResourceLoader.exists(pth):
				arr.append(load(pth))
		_zvuky[druh] = arr
	var arr2: Array = _zvuky[druh]
	if arr2.is_empty():
		return
	var a := AudioStreamPlayer3D.new()
	a.stream = arr2[_rng.randi() % arr2.size()]
	a.unit_size = 4.0
	a.max_distance = 40.0
	a.pitch_scale = _rng.randf_range(0.92, 1.08)
	n.add_child(a)
	a.play()
	a.finished.connect(a.queue_free)
