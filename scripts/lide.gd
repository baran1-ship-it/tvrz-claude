extends Node3D
## Lide (0.62, Misa: "klidne pridej NPC"): vesnicane chodi po navsi a celed po nadvori tvrze. Postavy Quaternius
## (Universal Base Characters + Peasant outfit, CC0, modely/postavy): zakladni postava (hlava, ruce) a odev na jedne
## kostre. Animace v kitu nejsou -> chuze se pocita v kodu (kyvani stehen, lytek a paze kolem bocni osy, houpani
## panve); stoji-li hrac v ceste, postava se zastavi. Kresli se do 70 m, chuze se pocita jen do 45 m.

const DIR := "res://modely/postavy/"
const DOSAH := 70.0
const ANIM_DO := 45.0
const VES := Vector2(470.0, 830.0)
const VES_AU := Vector2(0.76193, 0.64764)
const VES_AV := Vector2(-0.64764, 0.76193)

var main: Node
var _lide: Array = []                  # [{uzel, kostra, kosti, trasa, i, faze, rych, y, y_t, stoji}]
var _t := 0.0
var _sh_hlava: Shader = preload("res://shaders/postava_hlava.gdshader")


func setup(p_main: Node) -> void:
	main = p_main
	var rng := RandomNumberGenerator.new()
	rng.seed = 1393
	# naves: chuze tam a zpet po ose cesty (stejna krivka jako zem.gdshader), kazdy jinym bokem
	for k in 5:
		var bok := rng.randf_range(-1.6, 1.6)
		var u0 := rng.randf_range(-70.0, -10.0)
		var u1 := rng.randf_range(10.0, 60.0)
		var trasa: Array = []
		var u := u0
		while u <= u1:
			trasa.append(_naves(u, bok))
			u += 6.0
		_pridej(k % 2 == 0, trasa, rng)
	# lom (radce 16:20 bod 6): dva lamaci u steny, kamenik u spalku - kratke trasy u pracoviste (prechazi, stoji)
	for tr: Array in [[Vector2(117.0, 936.0), Vector2(117.2, 939.0)], [Vector2(117.5, 948.0), Vector2(118.0, 945.5)],
			[Vector2(126.0, 930.5), Vector2(127.2, 931.5)]]:
		_pridej(true, tr, rng)
	# nadvori tvrze: kruh studna - brana - palac - kovarna
	var dvur := [Vector2(-2.0, 6.0), Vector2(-3.0, 14.0), Vector2(6.0, 4.0), Vector2(-9.0, 10.5), Vector2(-12.0, 4.0)]
	for k in 2:
		var tr: Array = []
		for j in dvur.size():
			tr.append(dvur[(j + k * 2) % dvur.size()])
		tr.append(tr[0])
		_pridej(k == 1, tr, rng)


func _naves(u: float, bok: float) -> Vector2:
	var c0 := 2.5 * sin(u / 23.0) + 1.2 * sin(u / 9.0 + 1.0)
	return VES + VES_AU * u + VES_AV * (c0 + bok)


func _pridej(muz: bool, trasa: Array, rng: RandomNumberGenerator) -> void:
	var zaklad: PackedScene = load(DIR + ("Superhero_Male_FullBody.gltf" if muz else "Superhero_Female_FullBody.gltf"))
	var odev: PackedScene = load(DIR + ("Male_Peasant.gltf" if muz else "Female_Peasant.gltf"))
	if zaklad == null or odev == null:
		return
	var uzel := Node3D.new()
	uzel.name = "clovek_%d" % _lide.size()
	add_child(uzel)
	var z := zaklad.instantiate()
	uzel.add_child(z)
	var kostra := z.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	# z tela superhrdiny jen hlava a krk (shader rez pod krkem); odev s rukama, vlasy a vousy na tutez kostru
	var krk := kostra.find_bone("neck_01")
	var rez := kostra.get_bone_global_rest(krk).origin.y - 0.03 if krk >= 0 else 1.45
	for mi in z.find_children("*", "MeshInstance3D", true, false):
		var mb := mi as MeshInstance3D
		if String(mb.name).begins_with("Super"):
			var sm := ShaderMaterial.new()
			sm.shader = _sh_hlava
			var om := mb.mesh.surface_get_material(0) as BaseMaterial3D
			sm.set_shader_parameter("barva", om.albedo_texture if om else null)
			sm.set_shader_parameter("rez", rez)
			mb.material_override = sm
	var dily: Array = [odev]
	var vlasy: Array = (["Hair_SimpleParted.gltf", "Hair_Long.gltf"] if muz else ["Hair_Long.gltf", "Hair_Buns.gltf"])
	dily.append(load(DIR + vlasy[rng.randi() % 2]))
	if muz and rng.randf() < 0.6:
		dily.append(load(DIR + "Hair_Beard.gltf"))
	# barva vlasu (textura kitu je seda): hneda, tmave hneda, plava, cerna, prosedla
	var barvy := [Color(0.32, 0.2, 0.11), Color(0.18, 0.11, 0.06), Color(0.62, 0.48, 0.28), Color(0.08, 0.06, 0.05), Color(0.45, 0.42, 0.38)]
	var bv: Color = barvy[rng.randi() % barvy.size()]
	for dil: PackedScene in dily:
		if dil == null:
			continue
		var o := dil.instantiate()
		for mi in o.find_children("*", "MeshInstance3D", true, false):
			var m := mi as MeshInstance3D
			if dil != odev:
				for si in m.mesh.get_surface_count():
					var hm := m.mesh.surface_get_material(si) as BaseMaterial3D
					if hm:
						var h2 := hm.duplicate() as BaseMaterial3D
						h2.albedo_color = bv
						m.set_surface_override_material(si, h2)
			var sk := m.skin
			m.get_parent().remove_child(m)
			kostra.add_child(m)
			m.skin = sk
			m.skeleton = NodePath("..")
		o.free()
	for mi in z.find_children("*", "MeshInstance3D", true, false):
		var g := mi as GeometryInstance3D
		g.visibility_range_end = DOSAH
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	var kosti := {}
	for nm: String in ["thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "upperarm_l", "upperarm_r",
			"lowerarm_l", "lowerarm_r", "pelvis", "spine_01", "hand_l", "hand_r"]:
		kosti[nm] = kostra.find_bone(nm)
	var c := {"uzel": uzel, "kostra": kostra, "kosti": kosti, "trasa": trasa, "i": 1, "smer": 1,
			"faze": rng.randf() * TAU, "rych": rng.randf_range(0.95, 1.25), "y": INF, "y_t": 0.0, "stoji": 0.0,
			"skala": rng.randf_range(0.94, 1.04)}
	uzel.scale = Vector3.ONE * float(c["skala"])
	_osy(c)
	var p: Vector2 = trasa[0]
	uzel.position = Vector3(p.x, 0.0, p.y)
	c["muz"] = muz
	_lide.append(c)


## Az po fyzice (prvni snimek hry): body pod strechou a v budovach pryc - paprsek shora musi trefit zem do 0,6 m
## nad mrizkou terenu; postava bez trasy zmizi.
func _over_trasy() -> void:
	for c: Dictionary in _lide.duplicate():
		var tr: Array = []
		for q: Vector2 in c["trasa"]:
			var y: float = main._ground_hi(q.x, q.y)
			if y < float(main.svet._vyska(q.x, q.y)) + 0.6:
				tr.append(q)
		if tr.size() < 2:
			(c["uzel"] as Node).queue_free()
			_lide.erase(c)
			continue
		c["trasa"] = tr
		c["i"] = 1
		(c["uzel"] as Node3D).position = Vector3(tr[0].x, 0.0, tr[0].y)
		print("clovek %s: %d bodu, start %s" % ["muz" if c["muz"] else "zena", tr.size(), tr[0]])


## Osa kyvu kazde kosti v jejim lokalnim prostoru: bocni osa postavy (X modelu) a predni osa (paze dolu z T-pozy).
func _osy(c: Dictionary) -> void:
	var kostra: Skeleton3D = c["kostra"]
	var osy := {}
	for nm: String in c["kosti"]:
		var b: int = c["kosti"][nm]
		if b < 0:
			continue
		var gb := kostra.get_bone_global_rest(b).basis.orthonormalized()
		osy[nm] = [gb.inverse() * Vector3(1, 0, 0), gb.inverse() * Vector3(0, 0, 1), kostra.get_bone_rest(b).basis.get_rotation_quaternion()]
	c["osy"] = osy
	# paze z T-pozy dolu: znamenko tak, aby ruka klesla
	for st: String in ["l", "r"]:
		var nm := "upperarm_" + st
		if not osy.has(nm) or int(c["kosti"]["hand_" + st]) < 0:
			continue
		var best := 1.0
		var low := INF
		for sg: float in [1.0, -1.0]:
			_toc(c, nm, 1, sg * 1.25)
			kostra.force_update_all_bone_transforms()
			var y := kostra.get_bone_global_pose(int(c["kosti"]["hand_" + st])).origin.y
			if y < low:
				low = y
				best = sg
		c["paze_" + st] = best
		kostra.reset_bone_pose(int(c["kosti"][nm]))
	# znamenka kyvu (Misa 0.62: "chodi jak zombie, ohybaji nohy v lytkach"): odhad os nesedel -> zkusit uhel a podle
	# polohy chodidla / ruky vuci smeru chuze (+Z postavy v prostoru kostry) zvolit znamenko
	var vpred: Vector3 = (kostra.global_transform.basis.inverse() * (c["uzel"] as Node3D).global_transform.basis.z).normalized()
	for e: Array in [["thigh_l", "foot_l", 1.0], ["thigh_r", "foot_r", 1.0], ["calf_l", "foot_l", -1.0], ["calf_r", "foot_r", -1.0]]:
		var b: int = c["kosti"][e[1]]
		if not osy.has(e[0]) or b < 0:
			continue
		kostra.force_update_all_bone_transforms()
		var p0 := kostra.get_bone_global_pose(b).origin
		_toc(c, e[0], 0, 0.5)
		kostra.force_update_all_bone_transforms()
		var p1 := kostra.get_bone_global_pose(b).origin
		kostra.reset_bone_pose(int(c["kosti"][e[0]]))
		# stehno: + = chodidlo dopredu; lytko: + = pata dozadu (koleno se ohyba jen dozadu)
		c["zn_" + String(e[0])] = 1.0 if (p1 - p0).dot(vpred) * float(e[2]) > 0.0 else -1.0
	for st: String in ["l", "r"]:
		var nm := "upperarm_" + st
		var b: int = c["kosti"]["hand_" + st]
		if not osy.has(nm) or b < 0:
			continue
		var o: Array = osy[nm]
		var dolu := Quaternion(o[1], float(c.get("paze_" + st, 1.0)) * 1.25)
		kostra.set_bone_pose_rotation(int(c["kosti"][nm]), o[2] * dolu)
		kostra.force_update_all_bone_transforms()
		var p0 := kostra.get_bone_global_pose(b).origin
		kostra.set_bone_pose_rotation(int(c["kosti"][nm]), o[2] * dolu * Quaternion(o[0], 0.4))
		kostra.force_update_all_bone_transforms()
		var p1 := kostra.get_bone_global_pose(b).origin
		c["zn_paze_" + st] = 1.0 if (p1 - p0).dot(vpred) > 0.0 else -1.0
		kostra.reset_bone_pose(int(c["kosti"][nm]))


func _toc(c: Dictionary, nm: String, osa: int, uhel: float, pridat := Quaternion.IDENTITY) -> void:
	if not c["osy"].has(nm):
		return
	var o: Array = c["osy"][nm]
	var q: Quaternion = o[2] * Quaternion(o[osa], uhel) * pridat
	(c["kostra"] as Skeleton3D).set_bone_pose_rotation(int(c["kosti"][nm]), q)


## Diag (radce 20:00): cas _process meri obal, poradi behu hry se nemeni (drive diag _process prebiral).
func _process(dt: float) -> void:
	var t_us := Time.get_ticks_usec()
	_process_vlastni(dt)
	var dg: Object = Engine.get_meta("diag", null)
	if dg:
		dg.cas("lide", Time.get_ticks_usec() - t_us)


func _process_vlastni(dt: float) -> void:
	if main == null or main.player == null or not main.ready_done:
		return
	if _t == 0.0:
		_over_trasy()
	# mereni: TVRZ_LIDE_FOTO=N - hrac (kamera) 3 m pred postavou N, cely beh
	if OS.has_environment("TVRZ_LIDE_FOTO") and not _lide.is_empty():
		var c0: Dictionary = _lide[clampi(int(OS.get_environment("TVRZ_LIDE_FOTO")), 0, _lide.size() - 1)]
		var u0: Node3D = c0["uzel"]
		var f0 := u0.global_transform.basis.x.normalized() if OS.get_environment("TVRZ_LIDE_BOK") == "1" else u0.global_transform.basis.z.normalized()
		main.player.place(u0.global_position + f0 * 3.0 + Vector3(0.0, 0.2, 0.0), u0.global_position + Vector3(0, 1.0, 0))
	var pp: Vector3 = main.player.global_position
	_t += dt
	# v noci doma (tma, nikdo nechodi); rano zase venku
	var noc: bool = main.day != null and main.day.is_night()
	for c: Dictionary in _lide:
		var u: Node3D = c["uzel"]
		var d := Vector2(u.position.x - pp.x, u.position.z - pp.z).length()
		if d > DOSAH + 20.0 or noc:
			u.visible = false
			continue
		u.visible = true
		var trasa: Array = c["trasa"]
		var cil: Vector2 = trasa[int(c["i"])]
		var p := Vector2(u.position.x, u.position.z)
		var k := cil - p
		# hrac v ceste: zastavit (do 1,6 m pred postavou)
		var kh := Vector2(pp.x, pp.z) - p
		var stoji := kh.length() < 1.6 and kh.dot(k) > 0.0
		# zastaveni na bode (rozhlizi se, odpociva) 3-8 s
		if float(c["stoji"]) > 0.0:
			c["stoji"] = float(c["stoji"]) - dt
			stoji = true
		var v := 1.15 * float(c["rych"])
		if not stoji:
			if k.length() < 0.3:
				if randf() < 0.15:
					c["stoji"] = randf_range(3.0, 8.0)
				var i := int(c["i"]) + int(c["smer"])
				if i >= trasa.size() or i < 0:
					c["smer"] = -int(c["smer"])
					i = int(c["i"]) + int(c["smer"])
				c["i"] = clampi(i, 0, trasa.size() - 1)
			else:
				p += k.normalized() * minf(v * dt, k.length())
				var yaw := atan2(k.x, k.y)
				u.rotation.y = lerp_angle(u.rotation.y, yaw, minf(1.0, dt * 5.0))
		# vyska terenu po 0,25 s (paprsek), plynule
		c["y_t"] = float(c["y_t"]) - dt
		if float(c["y_t"]) <= 0.0:
			c["y_t"] = 0.25
			c["y"] = main._ground_hi(p.x, p.y)
		var y: float = c["y"]
		u.position = Vector3(p.x, lerpf(u.position.y, y, minf(1.0, dt * 8.0)) if u.position.y != 0.0 else y, p.y)
		if d < ANIM_DO:
			_chuze(c, dt, 0.0 if stoji else v)


## Krok: faze podle ujite drahy; stehna +-28 st, koleno ohnute v zadni fazi, paze proti noham, panev se houpe.
func _chuze(c: Dictionary, dt: float, v: float) -> void:
	var sila := clampf(v / 1.2, 0.0, 1.0)
	c["faze"] = fmod(float(c["faze"]) + dt * v * 2.6, TAU)
	var f: float = c["faze"]
	var s := sin(f)
	# stehna +-25 st dopredu/dozadu; koleno ohnute pri presunu nohy dopredu (svih), v oporne fazi skoro rovne
	_toc(c, "thigh_l", 0, float(c.get("zn_thigh_l", 1.0)) * s * 0.44 * sila)
	_toc(c, "thigh_r", 0, -float(c.get("zn_thigh_r", 1.0)) * s * 0.44 * sila)
	_toc(c, "calf_l", 0, float(c.get("zn_calf_l", 1.0)) * (maxf(0.0, cos(f)) * 0.75 * sila + 0.06))
	_toc(c, "calf_r", 0, float(c.get("zn_calf_r", 1.0)) * (maxf(0.0, -cos(f)) * 0.75 * sila + 0.06))
	for st: String in ["l", "r"]:
		var zn := 1.0 if st == "l" else -1.0
		# paze: nejdriv dolu z T-pozy (predni osa), pak kyv dopredu a dozadu (bocni osa)
		if c["osy"].has("upperarm_" + st):
			var o: Array = c["osy"]["upperarm_" + st]
			# paze proti noze na stejne strane: leva paze dopredu, kdyz jde prava noha dopredu
			var q: Quaternion = o[2] * Quaternion(o[1], float(c.get("paze_" + st, 1.0)) * 1.25) \
					* Quaternion(o[0], -zn * float(c.get("zn_paze_" + st, 1.0)) * s * 0.3 * sila)
			(c["kostra"] as Skeleton3D).set_bone_pose_rotation(int(c["kosti"]["upperarm_" + st]), q)
		_toc(c, "lowerarm_" + st, 0, 0.0)
	_toc(c, "spine_01", 1, sin(f) * 0.04 * sila)
