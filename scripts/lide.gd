extends Node3D
## Lide (Misa 28. 10.: „kazda postava ma domov, praci nebo ucel, svuj denni a nocni rytmus a podle prace se chova“,
## „animace pro cloveka, ne robota - ohyba se i hlava“). Obyvatele, role s rozvrhem po hodinach, mista cinnosti a
## cinnosti jsou zaznamy v pravidla/svet/postavy.json. Postava v kazdem bloku rozvrhu jde po siti cest a pesin
## (AStar2D z os cest sveta) na misto a tam dela cinnost (klipy Quaternius UAL, scripts/anim_ual.gd: chuze podle
## rychlosti, prace, hovor, sezeni; uvnitr domu se nekresli). Hlava a krk sleduji hrace nablizku, jinak smer chuze
## (LookAtModifier3D s prodlevou a limity uhlu). Mimo dosah se postava nepocita - pri zmene bloku se presune rovnou na
## misto (LOD AI); animace zblizka kazdy snimek, dal po krocich (LOD animaci).

const DIR := "res://modely/postavy/"
const Pravidla := preload("res://scripts/pravidla.gd")
const AnimUal := preload("res://scripts/anim_ual.gd")
const Vzhled := preload("res://scripts/vzhled.gd")
const Uchop := preload("res://scripts/uchop.gd")
const NohyIK := preload("res://scripts/nohy_ik.gd")
static var P: Dictionary = {
	"dosah": float(Pravidla.cti("postavy", "dosah_m")), "plna": float(Pravidla.cti("postavy", "anim_plna_m")),
	"do": float(Pravidla.cti("postavy", "anim_do_m")), "fps": float(Pravidla.cti("postavy", "anim_daleko_fps")),
	"blend": float(Pravidla.cti("postavy", "prolinani_s")), "rych": Pravidla.cti("postavy", "rychlost_m_s"),
	"uhyb": float(Pravidla.cti("postavy", "uhyb_hrac_m")), "noc": bool(Pravidla.cti("postavy", "noc_doma")),
	"klip_m_s": Pravidla.cti("postavy", "chuze_klip_m_s"), "hlava": Pravidla.cti("postavy", "hlava"),
	"dum": Pravidla.cti("postavy", "dum_mista"), "graf": Pravidla.cti("postavy", "graf"),
	"mista": Pravidla.cti("postavy", "mista"), "cinnosti": Pravidla.cti("postavy", "cinnosti"),
	"role": Pravidla.cti("postavy", "role"), "obyvatele": Pravidla.cti("postavy", "obyvatele"),
	"pr": Pravidla.cti("postavy", "prirozenost"), "vn": Pravidla.cti("postavy", "vnimani"),
	"reakce": Pravidla.cti("postavy", "reakce"), "repliky": Pravidla.cti("postavy", "repliky"),
	"dojem": Pravidla.cti("postavy", "hrac_dojem"), "schod_m": float(Pravidla.cti("hrac", "schod_m")[0]),
	"dalka_fps": float(Pravidla.cti("postavy", "anim_dalka_fps")), "hlava_do": float(Pravidla.cti("postavy", "hlava_do_m")),
	"drzeni": Pravidla.cti("postavy", "drzeni"), "sedani": Pravidla.cti("postavy", "sedani"),
	"rozvrh": Pravidla.cti("postavy", "rozvrh_rozptyl"), "hovor": Pravidla.cti("postavy", "hovor_skupina"),
	"dvere": Pravidla.cti("postavy", "dvere"), "lom": Pravidla.cti("postavy", "lom"),
	"u_predmetu": Pravidla.cti("postavy", "u_predmetu"), "rozestup": Pravidla.cti("postavy", "rozestup"),
	"spani": Pravidla.cti("postavy", "spani"), "rezim": Pravidla.cti("postavy", "denni_rezim"),
	"nohy_ik": Pravidla.cti("postavy", "nohy_ik")}
## stin postav jen zblizka: trida postava v pravidla_modelu.json (stin_m) - jeden zdroj s testem modelu
static var STIN_M: float = _stin_m()
const PREDMETY_DIR := "res://modely/predmety/"
static var _kat: Dictionary = {}
static var _predmet_sc: Dictionary = {}
var _ves_replika := -1000.0            # cas posledni repliky ve vsi (odstup ves_odstup_s)
var DOSAH: float = P["dosah"]

var main: Node
var _lide: Array = []                  # obyvatel: {id, uzel, kostra, ap, cil_hlavy, role, blok, cesta, i, misto...}
var _t := 0.0
var _sh_hlava: Shader = preload("res://shaders/postava_hlava.gdshader")
var _g := AStar2D.new()                # sit chuze (osy cest sveta)
var _misto_xz := {}                    # id mista -> [Vector2, yaw]
var _rng := RandomNumberGenerator.new()
var _obsazeno := {}                    # klic mista (sedak, skupina hovoru, misto v luzku) -> id obyvatele
var _postele_rozdeleny := false


static func _stin_m() -> float:
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://pravidla/pravidla_modelu.json"))
	for t: Variant in (d.get("tridy", []) if d is Dictionary else []):
		if t is Dictionary and String(t.get("trida", "")) == "postava":
			return float(t["stin_m"])
	push_error("lide: pravidla_modelu.json trida postava stin_m chybi")
	return 0.0


static func katalog() -> Dictionary:
	if _kat.is_empty() and FileAccess.file_exists("res://modely/predmety.json"):
		_kat = JSON.parse_string(FileAccess.get_file_as_string("res://modely/predmety.json"))
	return _kat


func setup(p_main: Node) -> void:
	main = p_main
	_rng.seed = 1393
	Vzhled.zacni()
	# predmety do rukou nacist predem (kontrola 5. 11.: load az pri prvni zmene klipu = zasek u postavy na ocich)
	for cn: Variant in (P["cinnosti"] as Dictionary).values():
		for spec: Variant in ((cn as Dictionary).get("v_rukou", {}) as Dictionary).values():
			for id: Variant in (spec as Dictionary).values():
				var sid := String(id)
				if sid != "" and not _predmet_sc.has(sid):
					_predmet_sc[sid] = load(PREDMETY_DIR + sid + ".glb") if ResourceLoader.exists(PREDMETY_DIR + sid + ".glb") else null
	# rozptyl rozvrhu (plan krok 3.4: selky neodchazeji naraz): obyvatele jedne role rovnomerne v +-rozptyl_min
	var v_roli := {}
	for o: Dictionary in P["obyvatele"]:
		v_roli[o["role"]] = int(v_roli.get(o["role"], 0)) + 1
	var poradi := {}
	for o: Dictionary in P["obyvatele"]:
		var c: Dictionary = nova_postava(o)
		if c.is_empty():
			continue
		var n: int = v_roli[o["role"]]
		var i: int = poradi.get(o["role"], 0)
		poradi[o["role"]] = i + 1
		var r := float(P["rozvrh"]["rozptyl_min"])
		c["posun_h"] = (lerpf(-r, r, (i + 0.5) / n) if n > 1 else 0.0) / 60.0
		(c["uzel"] as Node3D).visible = false
		_lide.append(c)
	for cn: Dictionary in P["cinnosti"].values():
		for jm: String in cn.get("klipy", []) + cn.get("klipy_bez_sedu", []) + ([cn["chuze"]] if cn.has("chuze") else []):
			if not _lide.is_empty() and not (_lide[0]["ap"] as AnimationPlayer).has_animation(jm):
				push_error("lide: klip %s v knihovne UAL neni" % jm)


## Jedna postava (model, prehravac, hlava) - zaznam obyvatele; verejne i pro snimek tools/foto_postava.gd.
func nova_postava(o: Dictionary) -> Dictionary:
	var mt: Array = _model_o(o)
	if mt.is_empty():
		return {}
	var uzel: Node3D = mt[0]
	var kostra: Skeleton3D = mt[1]
	uzel.name = "clovek_" + String(o["id"])
	var ap := AnimationPlayer.new()
	ap.name = "Animace"
	uzel.add_child(ap)
	ap.root_node = NodePath("..")
	ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	ap.add_animation_library("", AnimUal.knihovna(String(uzel.get_path_to(kostra))))
	var rr: Array = P["rych"]
	var c := {"id": o["id"], "o": o, "uzel": uzel, "kostra": kostra, "ap": ap, "role": P["role"][o["role"]],
			"rych": _rng.randf_range(float(rr[0]), float(rr[1])), "y": INF, "y_t": 0.0, "klip": "", "anim_t": 0.0,
			"blok": -1, "cesta": PackedVector2Array(), "i": 0, "na_miste": false, "obmena": 0.0, "obch": 0,
			"misto": Vector2.ZERO, "yaw_mista": INF, "trasa": [], "v": 0.0, "pohled": 0.0, "na_hrace": false,
			"tempo": _rng.randf_range(float(P["pr"]["tempo_klipu"][0]), float(P["pr"]["tempo_klipu"][1])),
			"geo": mt[2], "stin": true, "ruce": {}, "posun_h": 0.0, "cn": {}, "sedak": {}, "na_miste_t": 0.0, "vstava": 0.0}
	uzel.scale = Vector3.ONE * _rng.randf_range(0.94, 1.04)
	_hlava(c)
	# chodidla na zemi (svah, schod, prah): scripts/nohy_ik.gd, jen zblizka (LOD v _process)
	if bool(P["nohy_ik"].get("zapnuto", false)):
		var nik: SkeletonModifier3D = NohyIK.new()
		nik.name = "nohy_ik"
		nik.set("postava", c["uzel"])
		nik.set("D", P["nohy_ik"])
		(c["kostra"] as Skeleton3D).add_child(nik)
		c["nohy_ik"] = nik
	_klip(c, "Idle_Loop", 1.0)
	ap.seek(_rng.randf(), true)
	return c


## Hlava a krk (Misa: „ohyba se i hlava“): LookAtModifier3D na krku (mensi uhel) a hlave, cil = bod cil_hlavy.
func _hlava(c: Dictionary) -> void:
	var h: Dictionary = P["hlava"]
	var cil := Marker3D.new()
	cil.name = "pohled"
	add_child(cil)
	c["cil_hlavy"] = cil
	var kostra: Skeleton3D = c["kostra"]
	for e: Array in [[String(h["krk"]), float(h["krk_limit_st"])], [String(h["kost"]), float(h["limit_st"])]]:
		if kostra.find_bone(e[0]) < 0:
			continue
		var la := LookAtModifier3D.new()
		la.bone_name = e[0]
		la.forward_axis = SkeletonModifier3D.BONE_AXIS_PLUS_Z
		la.primary_rotation_axis = Vector3.AXIS_Y
		la.use_secondary_rotation = true
		la.use_angle_limitation = true
		la.symmetry_limitation = true
		la.primary_limit_angle = deg_to_rad(float(e[1]))
		la.primary_damp_threshold = 0.6
		la.secondary_limit_angle = deg_to_rad(float(h["kyv_st"]))
		la.secondary_damp_threshold = 0.6
		la.duration = float(h["prodleva_s"])
		la.transition_type = Tween.TRANS_SINE
		la.ease_type = Tween.EASE_IN_OUT
		kostra.add_child(la)
		la.target_node = la.get_path_to(cil)
		(c.get_or_add("hlava_mod", []) as Array).append(la)


## Dobovy vzhled obyvatele (scripts/vzhled.gd, sada podle pravidla/svet/postavy_vzhled.json); bez sady stary model.
func _model_o(o: Dictionary) -> Array:
	var mt: Array = Vzhled.model(self, o, DOSAH)
	return mt if not mt.is_empty() else _model(bool(o["muz"]), _rng)


## Model postavy (Quaternius: hlava z tela superhrdiny, odev, vlasy a vousy na jedne kostre); vrati [uzel, kostra, site].
func _model(muz: bool, rng: RandomNumberGenerator) -> Array:
	var zaklad: PackedScene = load(DIR + ("Superhero_Male_FullBody.gltf" if muz else "Superhero_Female_FullBody.gltf"))
	var odev: PackedScene = load(DIR + ("Male_Peasant.gltf" if muz else "Female_Peasant.gltf"))
	if zaklad == null or odev == null:
		return []
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
	var geo: Array = []
	for mi in z.find_children("*", "MeshInstance3D", true, false):
		var g := mi as GeometryInstance3D
		g.visibility_range_end = DOSAH
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		geo.append(g)
	return [uzel, kostra, geo]


## Sit chuze (po prvnim snimku - osy cest sveta jsou hotove): body os po krok_m, spojene po ose a mezi osami do spoj_m.
func _graf() -> void:
	var sv: RefCounted = main.svet
	var krok := float(P["graf"]["krok_m"])
	var spoj := float(P["graf"]["spoj_m"])
	var mriz := {}
	var osa_id := {}
	var n := 0
	for oi in sv.cesty_osy.size():
		var pts: Variant = sv.cesty_osy[oi]["p"]
		var prev := -1
		var posl := Vector2.INF
		for q0: Variant in pts:
			var q := Vector2(q0.x, q0.z) if q0 is Vector3 else (q0 as Vector2)
			if posl != Vector2.INF and q.distance_to(posl) < krok:
				continue
			_g.add_point(n, q)
			if prev >= 0:
				_g.connect_points(prev, n)
			var cl := Vector2i(floori(q.x / spoj), floori(q.y / spoj))
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for m: int in mriz.get(cl + Vector2i(dx, dz), []):
						if int(osa_id[m]) != oi and _g.get_point_position(m).distance_to(q) < spoj and _volno(_g.get_point_position(m), q):
							_g.connect_points(m, n)
			if not mriz.has(cl):
				mriz[cl] = []
			(mriz[cl] as Array).append(n)
			osa_id[n] = oi
			prev = n
			posl = q
			n += 1
	print("lide: sit chuze %d bodu" % n)


## Spojka mezi dvema osami cest bez zdi (Misa 0.992 „zase sel pres zed“; test vztahy_hra zed|postava): osa cesty
## sama je schudna (most, schody), ale spojky do spoj_m vedly i pres zed mezi soubeznymi cestami. Paprsek v kolenou
## a hlave nad terenem nesmi narazit na stavbu; teren a branky/vrata (Pohyb_*, otviraji se) nevadi.
func _volno(a: Vector2, b: Vector2) -> bool:
	var prostor := get_viewport().get_world_3d().direct_space_state
	for h: float in [0.5, 1.6]:
		var r := PhysicsRayQueryParameters3D.create(Vector3(a.x, float(main.svet.call("_vyska", a.x, a.y)) + h, a.y),
				Vector3(b.x, float(main.svet.call("_vyska", b.x, b.y)) + h, b.y))
		for _k in 4:
			var hit := prostor.intersect_ray(r)
			if hit.is_empty():
				break
			var jm := str((hit["collider"] as Node).get_path())
			if not (jm.contains("Teren") or jm.contains("Pohyb_")):
				return false
			r.exclude = r.exclude + [hit["rid"]]
	return true


## Poloha mista (zaznam postavy.json mista nebo domov/dvere/zahrada obyvatele) -> [Vector2, yaw nebo INF].
func _misto(c: Dictionary, kde: String) -> Array:
	var o: Dictionary = c["o"]
	if kde == "prace":
		kde = String(o.get("prace", "dvere"))
	if kde == "naves":
		var nv: Array = (P["mista"] as Dictionary).keys().filter(func(k: String) -> bool: return String(P["mista"][k].get("skupina", "")) == "naves")
		kde = nv[_rng.randi() % nv.size()]
	if kde in ["domov", "dvere", "zahrada"]:
		var dm: Dictionary = o["domov"]
		if dm.has("misto"):
			return _misto(c, String(dm["misto"]))
		for d: Dictionary in main.svet._domy:
			if int(d["k"]) != int(dm["dum"]) or (dm.has("typ") and String(d["typ"]) != String(dm["typ"])):
				continue
			var m: Dictionary = d["m"]
			var xf: Transform3D = d["xf"]
			var dmi: Dictionary = P["dum"]
			var lok: Vector3
			if m.has("vstup"):
				lok = Vector3(float(m["hw"]) + float(dmi["dvere_za_zdi_m"]), 0.0, float(m["vstup"]))
				if kde == "zahrada":
					lok = Vector3(float(m["hw"]) + float(dmi["zahrada_za_zdi_m"]), 0.0, float(m["f"]) - float(dmi["zahrada_od_stitu_m"]))
			else:
				lok = Vector3(0.0, 0.0, float(m["f"]) + float(dmi["dvere_za_zdi_m"]))
			var w := xf * lok
			var ven := (xf.basis * (Vector3.RIGHT if m.has("vstup") else Vector3.BACK)).normalized()
			# domov = uvnitr (skryty) u dveri; dvere a zahrada = venku, celem od domu
			return [Vector2(w.x, w.z), atan2(ven.x, ven.z)]
		push_warning("lide %s: domov %s nenalezen" % [c["id"], str(dm)])
		return [Vector2((c["uzel"] as Node3D).position.x, (c["uzel"] as Node3D).position.z), INF]
	if _misto_xz.has(kde):
		return _misto_xz[kde]
	var z: Dictionary = P["mista"].get(kde, {})
	var out := [Vector2.ZERO, INF]
	if z.has("p"):
		out = [Vector2(float(z["p"][0]), float(z["p"][1])), deg_to_rad(float(z["yaw_st"])) if z.has("yaw_st") else INF]
	elif z.has("ulice") and main.svet.get("vo") != null:
		var osa: PackedVector2Array = main.svet.vo.osa_ulice()
		out = [osa[clampi(int(float(z["ulice"]) * (osa.size() - 1)), 0, osa.size() - 1)], INF]
	elif z.has("pohyb"):
		for e: Dictionary in main.svet.data["pohyb"]:
			if String(e["name"]).begins_with(String(z["pohyb"])):
				var u: Array = e.get("use", e["pos"])
				out = [Vector2(float(u[0]), float(u[2])), INF]
				break
	elif z.has("dum") and main.svet != null:
		# bod v ramci domu (svet._domy k, typ): lok [x, z], natoceni k bodu k_lok (pastyr u kosare za rychtou)
		for d: Dictionary in main.svet._domy:
			if int(d["k"]) != int(z["dum"]) or (z.has("typ") and String(d["typ"]) != String(z["typ"])):
				continue
			var xf: Transform3D = d["xf"]
			var w := xf * Vector3(float(z["lok"][0]), 0.0, float(z["lok"][1]))
			var kk := xf * Vector3(float(z["k_lok"][0]), 0.0, float(z["k_lok"][1]))
			out = [Vector2(w.x, w.z), atan2(kk.x - w.x, kk.z - w.z)]
	elif z.has("lom_stena_z") and main.svet != null:
		# u skalni steny lomu (Misa r. 48): pata ze svet.lom_stena_x (od zapadu sraz, pak dno), lic steny paprskem,
		# volna bunka mrizky (leseni, kameny) dal po bunce do max_m; celem ke stene
		var lp: Dictionary = P["lom"]
		var lz := float(z["lom_stena_z"])
		var x0 := float(main.svet.call("lom_stena_x", lz))
		# lic steny paprskem (viditelna stena ≠ pata site terenu - svet._lom_stena_svisla, osyp): z dna lomu
		# hledat_m od paty vodorovne ve vysce rukou k zapadu; misto od_steny_m pred licem, dal po bunce do max_m;
		# v kazde vzdalenosti posuny podel steny (sloupy leseni, kameny)
		var sp := get_viewport().get_world_3d().direct_space_state
		var bb := float(P["graf"]["mrizka"]["bunka_m"])
		var q := Vector2(x0 + float(lp["od_steny_m"]), lz)
		var hotovo := false
		var od := float(lp["od_steny_m"])
		while od <= float(lp["max_m"]) and not hotovo:
			for dz: float in lp["posun_z_m"]:
				var z2 := lz + dz
				var xs := float(main.svet.call("lom_stena_x", z2)) + float(lp["hledat_m"])
				var ys := float(main.svet.call("_vyska", xs, z2)) + float(lp["ruce_m"])
				var hl := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(xs, ys, z2), Vector3(xs - 2.0 * float(lp["hledat_m"]), ys, z2)))
				if hl.is_empty():
					continue
				var q2 := Vector2(float((hl["position"] as Vector3).x) + od, z2)
				# dno lomu (teren), nad hlavou volno na rozmach krumpace (ne pod podlahou leseni - Misa r. 48 „pod lesenim
				# seka do prazdna“)
				var yd := float(main.svet.call("_vyska", q2.x, q2.y))
				var nad := PhysicsRayQueryParameters3D.create(Vector3(q2.x, yd + 0.3, q2.y), Vector3(q2.x, yd + float(lp["volno_nad_m"]), q2.y))
				if not sp.intersect_ray(nad).is_empty():
					continue
				if not is_nan(_nav_bunka(_nav_ij(q2), yd)):
					q = q2
					hotovo = true
					break
			od += bb
		out = [q, deg_to_rad(float(z["yaw_st"]))]
		if not hotovo:
			return out                                  # kolize skaly/leseni jeste nejsou - zkusit priste, nepamatovat
	elif z.has("u_predmetu") and main.svet != null:
		# u predmetu v mistnosti (obsluha u stolu, Misa r. 57): predmety daneho id v mistnosti podle x, poradi
		var vb: Array = main.svet.data.get("vybaveni", [])
		var kusy: Array = []
		for ri in vb.size():
			var r: Dictionary = vb[ri]
			if String(r["id"]) == String(z["u_predmetu"]) and _mistnost_u(Vector3(float(r["p"][0]), float(r["p"][1]), float(r["p"][2]))) == String(z.get("mistnost", "")):
				kusy.append([float(r["p"][0]), float(r["p"][2]), ri])
		kusy.sort()
		if kusy.size() > int(z["poradi"]):
			var u := _u_predmetu(c, int(kusy[int(z["poradi"])][2]), String(z.get("strana", "dlouha")), false)
			if not u.is_empty():
				out = u
		if out[0] == Vector2.ZERO:
			push_warning("lide: misto %s - predmet %s v %s nenalezen" % [kde, z["u_predmetu"], z.get("mistnost", "")])
			return [Vector2((c["uzel"] as Node3D).position.x, (c["uzel"] as Node3D).position.z), INF]   # stat na miste, ne k (0,0); nepamatovat
	elif z.has("lokace"):
		var lk: Dictionary = Pravidla.cti("lokace", String(z["lokace"]))
		var a := deg_to_rad(float(z["uhel_st"]))
		out = [Vector2(float(lk["stred"][0]), float(lk["stred"][1])) + Vector2(cos(a), sin(a)) * float(z["r_m"]), INF]
	else:
		push_warning("lide: misto %s nezname" % kde)
	_misto_xz[kde] = out
	return out


## Blok rozvrhu pro hodinu h (od .. do zacatku dalsiho; pred prvnim plati posledni pres pulnoc).
func _blok(c: Dictionary, h: float) -> int:
	h = fposmod(h - float(c.get("posun_h", 0.0)), 24.0)
	var rz: Array = c["role"]["rozvrh"]
	var bi := rz.size() - 1
	for i in rz.size():
		if h >= float(rz[i]["od"]):
			bi = i
	return bi


func _cesta(a: Vector2, b: Vector2, ya := INF) -> PackedVector2Array:
	if ya == INF:
		ya = podlaha(a)
	# blizke misto: mrizkou chuze (zdi, nabytek, leseni) - sit cest do nadvori ani do budov nevede
	if a.distance_to(b) < float(P["graf"]["k_mistu_max_m"]) or _g.get_point_count() == 0:
		var nv := _nav_cesta(a, ya, b)
		if _nav_prer:
			return PackedVector2Array()           # rozpocet snimku dosel - dopocita se dalsi snimek (_dopocitej)
		if not nv.is_empty() or _g.get_point_count() == 0:
			return nv if not nv.is_empty() else _nav_nouze(a, b)
	# dal: k nejblizsimu bodu site, po siti cest, z bodu site k mistu - prvni a posledni usek mrizkou
	var za: Array = _nav_k_siti(a, ya, true)
	if _nav_prer:
		return PackedVector2Array()
	var yb := podlaha(b)
	var zb: Array = _nav_k_siti(b, yb, false)
	if _nav_prer:
		return PackedVector2Array()
	var out := PackedVector2Array()
	if _nav_bez:
		return out                                # usek k siti nebo od site nenalezen - ne rovne
	out.append_array(za[1])
	var p := _g.get_point_path(int(za[0]), int(zb[0]))
	out.append_array(p)
	out.append_array(zb[1])
	if out.is_empty() or out[out.size() - 1] != b:
		out.append(b)
	return out


## Usek mezi dvema body mrizkou chuze (uvnitr budov, otvor mezi mistnostmi); bez nalezene cesty rovne (varovani).
func _usek(p: Vector2, q: Vector2, y: float) -> PackedVector2Array:
	var nv := _nav_cesta(p, y, q)
	if _nav_prer:
		return PackedVector2Array()
	return nv if not nv.is_empty() else _nav_nouze(p, q)


## Cesta neexistuje (Misa 0.99994 r. 46/63: nouzova rovna cara vedla zdi a pod mostem): zadna cesta - _nav_bez,
## cela cesta postavy je prazdna, postava zustane stat a cinnost dela na miste (dalsi blok / dalsi bod obchuzky zkusi znovu).
var _nav_bez := false


func _nav_nouze(p: Vector2, q: Vector2) -> PackedVector2Array:
	_nav_selhani += 1
	_nav_bez = true
	if _nav_selhani <= 20:
		push_warning("lide: mrizka chuze nenasla cestu (%.1f,%.1f)->(%.1f,%.1f) - postava stoji" % [p.x, p.y, q.x, q.y])
	return PackedVector2Array()


## Bod site cest pro prvni (od = true: od bodu q k siti) nebo posledni usek (od siti k q): kandidati podle vzdalenosti,
## usek mrizkou chuze (Misa 0.991/0.99993: postava sla zdi - drive rovny paprsek nad terenem). Vrati [id, usek].
func _nav_k_siti(q: Vector2, yq: float, od: bool) -> Array:
	# kandidati (pruchod vsemi body site) v pameti pozadavku - opakovany pokus dalsi snimek je nepocita znovu
	var kk := "k%.2f,%.2f" % [q.x, q.y]
	var kandidati: Array = _nav_hotove.get(kk, [])
	if kandidati.is_empty():
		for i in _g.get_point_ids():
			var d := _g.get_point_position(i).distance_to(q)
			if d < float(P["graf"]["k_mistu_max_m"]):
				kandidati.append([d, i])
		kandidati.sort()
		if _nav_sond >= 0:
			_nav_hotove[kk] = kandidati
	for k: Array in kandidati.slice(0, int(P["graf"]["mrizka"]["kandidatu_site"])):
		var g := _g.get_point_position(int(k[1]))
		var nv := _nav_cesta(q, yq, g) if od else _nav_cesta(g, podlaha(g), q)
		if _nav_prer:
			return [-1, PackedVector2Array()]
		if not nv.is_empty():
			if od:
				return [int(k[1]), nv.slice(0, nv.size() - 1)]
			return [int(k[1]), nv]
	var nej := _g.get_closest_point(q)
	return [nej, _nav_nouze(q, _g.get_point_position(nej)) if od else _nav_nouze(_g.get_point_position(nej), q)]


## Podlaha pod bodem: paprsek z terenu + hlava_m dolu (prvni plocha - podlaha budovy, nadvori, teren); bez zasahu teren.
func podlaha(q: Vector2, y0 := INF) -> float:
	var yt := float(main.svet.call("_vyska", q.x, q.y))
	var od := (yt if y0 == INF else y0) + float(P["graf"]["mrizka"]["hlava_m"])
	var r := PhysicsRayQueryParameters3D.create(Vector3(q.x, od, q.y), Vector3(q.x, od - 6.0, q.y))
	var h := get_viewport().get_world_3d().direct_space_state.intersect_ray(r)
	return float((h["position"] as Vector3).y) if not h.is_empty() else yt


## --- Mrizka chuze (Misa 0.99993 r. 46: „postava s vedrem chodi pres zed, borec stoji na posteli“). Prvni pokus
## (0.991-0.992) byl paprsek v kolenou a hlave nad mrizkou vysek louky - na nadvori a v budovach mrizka nezna podlahu,
## paprsky sly pod zdi a pres postel. Ted A* po bunkach bunka_m: podlaha paprskem dolu z vysky sousedni bunky
## + schod_m (vyssi plocha = postel, lavice, truhla = prekazka), postava = kvadr pas_m od schod_m do hlava_m nad
## podlahou bez kolize (zdi, stoly, leseni); dvere (Pohyb_) se otviraji. Bunky se pocitaji az pri hledani a pamatuji.
var _nav_kes := {}
var _nav_selhani := 0
var _nav_q: PhysicsShapeQueryParameters3D
## Rozpocet mrizky na snimek (Misa 6. 11., panel tabletu: skript lide 692 / 868 / 957 ms v jednom snimku pri zmene
## rozvrhu - A* az max_bunek bunek, kazda nova = paprsek + intersect_shape, synchronne). _process dava kazdy snimek
## sondy_snimek novych sond a cas_ms_snimek; hledani se v kontrolnich bodech (zacatek, kazda bunka A*) prerusi,
## stav A* se ulozi (_nav_rozpr) a dalsi snimek pokracuje, hotove useky se pamatuji (_nav_hotove). Prerusena cesta
## = postava stoji (c.ceka), nikdy rovna cara pres zed. -1 = bez limitu (testy, verejna cesta()).
var _nav_sond := -1
var _nav_do_us := 0
var _nav_cas_us := 0
var _nav_prer := false
var _nav_hotove := {}                  # klic useku -> hotova cesta (jen pri rozpoctu, maze se, kdyz nikdo neceka)
var _nav_rozpr := {}                   # klic useku -> rozpracovany stav A*
var _nav_nelze := {}                   # dvojice bunek bez cesty -> cas zapisu (ms), plati nelze_platnost_s
var _nav_fronta: Array = []            # postavy cekajici na cestu (na rade se stridaji - jedna dlouha nebrzdi ostatni)
var _nav_sond_n := 0                   # novych sond celkem (mereni)


## Kontrolni bod rozpoctu: true = prerusit (sond na dalsi bunku nezbyva nebo dosel cas snimku).
func _nav_dost(sond: int) -> bool:
	if _nav_sond < 0:
		return false
	if _nav_do_us == 0:
		_nav_do_us = Time.get_ticks_usec() + _nav_cas_us        # cas hledani cest v tomto snimku (od prvni sondy)
	if _nav_sond < sond or Time.get_ticks_usec() > _nav_do_us:
		_nav_prer = true
	return _nav_prer


func _nav_bunka(ij: Vector2i, y_ref: float) -> float:
	var k := Vector3i(ij.x, ij.y, roundi(y_ref * 4.0))
	if _nav_kes.has(k):
		return _nav_kes[k]
	var m: Dictionary = P["graf"]["mrizka"]
	var bb := float(m["bunka_m"])
	var schod := float(m["schod_m"])
	var w := Vector2(ij.x + 0.5, ij.y + 0.5) * bb
	var sp := get_viewport().get_world_3d().direct_space_state
	var r := PhysicsRayQueryParameters3D.create(Vector3(w.x, y_ref + schod + 0.02, w.y), Vector3(w.x, y_ref - float(m["spad_m"]), w.y))
	if main.player:
		r.exclude = [main.player.get_rid()]
	var h := sp.intersect_ray(r)
	_nav_sond_n += 1
	if _nav_sond > 0:
		_nav_sond -= 1                         # mekky rozpocet: kontroluje se jen v kontrolnich bodech (_nav_dost)
	var y := NAN
	if not h.is_empty():
		var fy := float((h["position"] as Vector3).y)
		if _nav_q == null:
			_nav_q = PhysicsShapeQueryParameters3D.new()
			var bx := BoxShape3D.new()
			bx.size = Vector3(float(m["pas_m"]), float(m["hlava_m"]) - schod, float(m["pas_m"]))
			_nav_q.shape = bx
		if main.player:
			_nav_q.exclude = [main.player.get_rid()]
		_nav_q.transform = Transform3D(Basis.IDENTITY, Vector3(w.x, fy + (schod + float(m["hlava_m"])) * 0.5, w.y))
		y = fy
		for hh: Dictionary in sp.intersect_shape(_nav_q, 8):
			if not _nav_pruchozi(hh["collider"]):
				y = NAN
				break
	_nav_kes[k] = y
	return y


static func _nav_pruchozi(col: Object) -> bool:
	return col is Node and str((col as Node).get_path()).contains("Pohyb_")


func _nav_ij(q: Vector2) -> Vector2i:
	var bb := float(P["graf"]["mrizka"]["bunka_m"])
	return Vector2i(floori(q.x / bb), floori(q.y / bb))


func _nav_stred(ij: Vector2i) -> Vector2:
	return (Vector2(ij) + Vector2(0.5, 0.5)) * float(P["graf"]["mrizka"]["bunka_m"])


## Rovny usek bez prekazky (bunky po pul bunce, navazujici podlaha) - zkraceni cesty a prima cesta.
func _nav_volno(p: Vector2, q: Vector2, y: float) -> bool:
	var bb := float(P["graf"]["mrizka"]["bunka_m"])
	var n := maxi(1, ceili(p.distance_to(q) / (bb * 0.5)))
	var yy := y
	var posl := Vector2i(1 << 30, 0)
	for i in n + 1:
		var ij := _nav_ij(p.lerp(q, float(i) / n))
		if ij == posl:
			continue
		posl = ij
		if _nav_sond >= 0 and not _nav_kes.has(Vector3i(ij.x, ij.y, roundi(yy * 4.0))) and _nav_dost(1):
			return false                       # rozpocet dosel (volajici kontroluje _nav_prer)
		var y2 := _nav_bunka(ij, yy)
		if is_nan(y2):
			return false
		yy = y2
	return true


## A* po bunkach mrizky od a (podlaha ya) k b. Vrati body cesty bez a, posledni = b; prazdne = cesta nenalezena.
## Cilova bunka muze byt obsazena (misto u lavice, u steny): staci dojit do cil_m od b.
func _nav_cesta(a: Vector2, ya: float, b: Vector2) -> PackedVector2Array:
	if _nav_prer:
		return PackedVector2Array()
	var klic := "%.2f,%.2f,%.2f>%.2f,%.2f" % [a.x, a.y, ya, b.x, b.y]
	if _nav_sond >= 0 and _nav_hotove.has(klic):
		return _nav_hotove[klic]
	# neprochozi dvojice bunek (A* prohledal max_bunek a nenasel): pamatuje se trvale - jinak by kazda zmena rozvrhu
	# znovu stala tisice sond (9. 11. test lide_zasek: purkrabi k nadvori_brana 14 463 sond, 538 ms PC, pak stejne nouze)
	var kn := Vector3i(_nav_ij(a).x * 65536 + _nav_ij(a).y, _nav_ij(b).x * 65536 + _nav_ij(b).y, roundi(ya * 4.0) if ya != INF else 0)
	# platnost z dat (graf.mrizka.nelze_platnost_s): cesta mohla chybet jen kvuli max_bunek nebo docasne prekazce
	# (kun, vuz, zavrene dvere) - po case se zkusi znovu (nezavisla kontrola 9. 11.)
	if _nav_nelze.has(kn):
		if Time.get_ticks_msec() - int(_nav_nelze[kn]) < int(float(P["graf"]["mrizka"]["nelze_platnost_s"]) * 1000.0):
			return PackedVector2Array()
		_nav_nelze.erase(kn)
	var out := _nav_cesta_v(a, ya, b, klic)
	if not _nav_prer:
		if _nav_sond >= 0:
			_nav_hotove[klic] = out
		if out.is_empty():
			_nav_nelze[kn] = Time.get_ticks_msec()
	return out


func _nav_cesta_v(a: Vector2, ya: float, b: Vector2, klic: String) -> PackedVector2Array:
	var m: Dictionary = P["graf"]["mrizka"]
	var bb := float(m["bunka_m"])
	var smery := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1)]
	var st: Array = _nav_rozpr.get(klic, [])
	if st.is_empty():
		# start a prima cesta: nejvys 25 + delka/pul bunky sond (mekky rozpocet, kontrola pred nimi)
		if _nav_dost(1):
			return PackedVector2Array()
		st = _nav_start(a, ya, b, m)
		if st.size() == 1:
			return st[0]
	var s: Vector2i = st[0]
	var ys: float = st[1]
	var g: Vector2i = st[2]
	var rect: Rect2 = st[3]
	var uzly: Dictionary = st[4]
	var hf: PackedFloat32Array = st[5]
	var hk: Array = st[6]
	var zavrene: Dictionary = st[7]
	var konec: Vector2i = st[11] if st.size() > 11 else Vector2i(1 << 30, 0)
	var nej_k: Vector2i = st[8]
	var nej_d: float = st[9]
	var n: int = st[10]
	var cil_m := float(m["cil_m"])
	while konec.x == 1 << 30 and not hk.is_empty() and n < int(m["max_bunek"]):
		if _nav_dost(smery.size()):
			# rozpocet dosel: stav A* do dalsiho snimku (hf/hk/uzly/zavrene jsou sdilene odkazy, pole se meni na miste)
			_nav_rozpr[klic] = [s, ys, g, rect, uzly, hf, hk, zavrene, nej_k, nej_d, n]
			return PackedVector2Array()
		var cur: Vector2i = _nav_pop(hf, hk)
		if zavrene.has(cur):
			continue
		zavrene[cur] = true
		n += 1
		var cp := _nav_stred(cur)
		var dc := cp.distance_to(b)
		if dc < nej_d:
			nej_d = dc
			nej_k = cur
		if cur == g or dc < bb * 0.75:
			konec = cur
			break
		var uc: Array = uzly[cur]
		var yc := float(uc[1])
		for sm: Vector2i in smery:
			var nb: Vector2i = cur + sm
			if zavrene.has(nb) or not rect.has_point(_nav_stred(nb)):
				continue
			var yn := _nav_bunka(nb, yc)
			if is_nan(yn):
				continue
			if sm.x != 0 and sm.y != 0 and (is_nan(_nav_bunka(cur + Vector2i(sm.x, 0), yc)) or is_nan(_nav_bunka(cur + Vector2i(0, sm.y), yc))):
				continue                                  # bez rezani rohu
			var gn := float(uc[0]) + (1.4142 if sm.x != 0 and sm.y != 0 else 1.0) * bb + absf(yn - yc)
			if uzly.has(nb) and float(uzly[nb][0]) <= gn:
				continue
			uzly[nb] = [gn, yn, cur]
			_nav_push(hf, hk, gn + _nav_stred(nb).distance_to(b) * float(m["vaha_h"]), nb)
	if konec.x == 1 << 30:
		_nav_rozpr.erase(klic)
		if nej_d > cil_m:
			return PackedVector2Array()
		konec = nej_k
	# zpet od konce, pak zkraceni (dalsi bod, kam vede rovny usek bez prekazky)
	var bunky: Array = []
	var k := konec
	while true:
		bunky.push_front(k)
		if k == s:
			break
		k = uzly[k][2]
	var body: Array = [a]
	for ij: Vector2i in bunky:
		body.append(_nav_stred(ij))
	body.append(b)
	var out := PackedVector2Array()
	var i := 0
	var yi := ys
	while i < body.size() - 1:
		var j := body.size() - 1
		while j > i + 1 and not _nav_volno(body[i], body[j], yi):
			j -= 1
		if _nav_prer:
			# zkraceni preruseno rozpoctem: A* hotove (konec), zkraceni znovu dalsi snimek (bunky uz v pameti)
			_nav_rozpr[klic] = [s, ys, g, rect, uzly, hf, hk, zavrene, nej_k, nej_d, n, konec]
			return PackedVector2Array()
		out.append(body[j])
		if j - 1 < bunky.size() and j >= 1 and j - 1 >= 0 and j - 1 < bunky.size():
			yi = float(uzly[bunky[j - 1]][1])
		i = j
	_nav_rozpr.erase(klic)
	return out


## Start A*: volna startovni bunka (start v prekazce - vstava z postele, stoji u stolu: nejblizsi volna do 2 bunek)
## a prima cesta. Vrati [vysledek] (hotovo) nebo pocatecni stav A* [s, ys, g, rect, uzly, hf, hk, zavrene, nej_k, nej_d, n].
func _nav_start(a: Vector2, ya: float, b: Vector2, m: Dictionary) -> Array:
	var s0 := _nav_ij(a)
	var s := s0
	var ys := _nav_bunka(s0, ya)
	if is_nan(ys):
		var nej := INF
		for dx in range(-2, 3):
			for dz in range(-2, 3):
				var y2 := _nav_bunka(s0 + Vector2i(dx, dz), ya)
				if not is_nan(y2) and Vector2(dx, dz).length() < nej:
					nej = Vector2(dx, dz).length()
					s = s0 + Vector2i(dx, dz)
					ys = y2
		if is_nan(ys):
			return [PackedVector2Array()]
	if _nav_volno(_nav_stred(s), b, ys) and _nav_volno(a, _nav_stred(s), ys):
		return [PackedVector2Array([b])]
	if _nav_prer:
		return [PackedVector2Array()]
	var okraj := float(m["okraj_m"])
	var rect := Rect2(Vector2(minf(a.x, b.x), minf(a.y, b.y)) - Vector2.ONE * okraj, (a - b).abs() + Vector2.ONE * okraj * 2.0)
	# uzly: bunka -> [g, podlaha, rodic]; halda hf/hk
	return [s, ys, _nav_ij(b), rect, {s: [0.0, ys, s]}, PackedFloat32Array([b.distance_to(_nav_stred(s))]), [s], {}, s, INF, 0]


static func _nav_push(hf: PackedFloat32Array, hk: Array, f: float, k: Vector2i) -> void:
	hf.append(f)
	hk.append(k)
	var i := hf.size() - 1
	while i > 0:
		var r := (i - 1) >> 1
		if hf[r] <= hf[i]:
			break
		var tf := hf[r]
		hf[r] = hf[i]
		hf[i] = tf
		var tk: Variant = hk[r]
		hk[r] = hk[i]
		hk[i] = tk
		i = r


static func _nav_pop(hf: PackedFloat32Array, hk: Array) -> Vector2i:
	var top: Vector2i = hk[0]
	var n := hf.size() - 1
	hf[0] = hf[n]
	hk[0] = hk[n]
	hf.resize(n)
	hk.resize(n)
	var i := 0
	while true:
		var l := i * 2 + 1
		var r := l + 1
		var mi := i
		if l < n and hf[l] < hf[mi]:
			mi = l
		if r < n and hf[r] < hf[mi]:
			mi = r
		if mi == i:
			break
		var tf := hf[mi]
		hf[mi] = hf[i]
		hf[i] = tf
		var tk: Variant = hk[mi]
		hk[mi] = hk[i]
		hk[i] = tk
		i = mi
	return top


## Verejne pro test vztahy_hra: cesta postavy mezi dvema misty po siti (bez rozpoctu snimku).
func cesta(a: Vector2, b: Vector2, ya := INF) -> PackedVector2Array:
	var sn := _nav_sond
	_nav_sond = -1
	_nav_prer = false
	_nav_bez = false
	var out := _cesta(a, b, ya)
	_nav_sond = sn
	if _nav_bez:
		out = PackedVector2Array()
	return out


## Pozadavek cesty postavy [od, cil, ya, pruchod_cil, pruchod dvermi]: spocita se hned, kolik dovoli rozpocet snimku,
## zbytek dalsi snimky (_dopocitej v _process). Do te doby c.ceka - postava stoji (Idle), nejde rovne pres zed.
## Opakovany vypocet je bez vedlejsich ucinku navic (_cesta_pruchod zapise stejne c.dvere, hotove useky z pameti).
func _pozadej(c: Dictionary, poz: Array) -> void:
	c["ceka"] = poz
	c["cesta"] = PackedVector2Array()
	c["i"] = 0
	_dopocitej(c)


func _dopocitej(c: Dictionary) -> bool:
	var q: Array = c["ceka"]
	_nav_prer = false
	_nav_bez = false
	var cs: PackedVector2Array = _cesta_pruchod(c, q[0], q[1], q[3]) if bool(q[4]) else _cesta(q[0], q[1], q[2])
	if _nav_prer:
		_nav_prer = false
		return false
	if _nav_bez:
		cs = PackedVector2Array()                 # bez cesty stoji (cinnost na miste), nikdy rovne pres zed
		c.erase("dvere")
		_nav_bez = false
	c.erase("ceka")
	c["cesta"] = cs
	c["i"] = 0
	return true


func _novy_blok(c: Dictionary, bi: int, viditelna: bool) -> void:
	c["blok"] = bi
	c.erase("ceka")
	var b: Dictionary = c["role"]["rozvrh"][bi]
	var cn: Dictionary = P["cinnosti"][b["cinnost"]]
	_uvolni(c)
	var m: Array = _misto_cinnosti(c, String(b["kde"]), cn)
	if (c["sedak"] as Dictionary).is_empty() and not bool(cn.get("skupina", false)) and not bool(cn.get("skryty", false)):
		m = [_rozestup(c, m[0]), m[1]]
	c["misto"] = m[0]
	c["yaw_mista"] = m[1]
	c["cn"] = cn
	# obchuzka zacina mistem bloku (Misa r. 63: tri s kbeliky sly stejne kolo za sebou a v sobe)
	c["obch"] = maxi(0, (cn.get("obchuzka", []) as Array).find(String(b["kde"])))
	c["obmena"] = 0.0
	c["na_miste_t"] = 0.0
	var u: Node3D = c["uzel"]
	if int(c.get("vchazi", 0)) > 0 and bool(cn.get("skryty", false)) and not (c.get("dvere", {}) as Dictionary).is_empty() 			and (m[0] as Vector2).distance_to(c["dvere"]["venku"]) < 0.5:
		# dalsi skryta cinnost u tychz dveri (jidlo -> spanek): zustava uvnitr
		c["na_miste"] = true
		c["na_miste_t"] = 1000.0
		c["cesta"] = PackedVector2Array()
		c["vchazi"] = 2
		if not bool(cn.get("spanek", false)):
			# Misa r. 85 (ubytovna: postava stoji na posteli): rano spanek -> dalsi skryta cinnost u tychz dveri
			# (snidane): drive zustala v_posteli s obmenou 0 -> klip cinnosti (Idle) ve vysce luzka = stani na posteli.
			# Uvnitr bez spanku je skryta jako jinde.
			c["v_posteli"] = false
		elif not bool(c.get("v_posteli", false)):
			_do_postele(c, cn)
		return
	# vnitrni misto (mista.dvere): kam se jde dvermi; misto cinnosti uvnitr hostince apod.
	var kde_k := String(b["kde"])
	if kde_k == "prace":
		kde_k = String(c["o"].get("prace", "dvere"))
	var pr_cil := _pruchod(kde_k)
	if int(c.get("vchazi", 0)) > 0:
		# rano / po jidle ven: od vnitrku dveri (ne z postele skrz zed), dvere otevrit a za sebou zavrit
		var dv: Dictionary = c.get("dvere", {})
		if not dv.is_empty():
			var vn: Vector2 = dv["vnitrek"]
			u.position = Vector3(vn.x, u.position.y, vn.y)
			_dvere_otevri(c, true)
			# spal za dvermi budovy, kde je i dalsi misto (hostinsky): uz je uvnitr
			if not pr_cil.is_empty() and (pr_cil["venku"] as Vector2).distance_to(vn) < float(P["dvere"]["stejne_m"]):
				c["uvnitr"] = pr_cil
		c["vchazi"] = 0
		c["v_posteli"] = false
	var p := Vector2(u.position.x, u.position.z)
	# vstavani ze sedu (Sitting_Exit), nez postava vykroci
	if bool(c.get("sedi", false)) and viditelna:
		_klip(c, "Sitting_Exit", 1.0)
		c["vstava"] = _delka(c, "Sitting_Exit")
	c["sedi"] = false
	if not viditelna or u.position == Vector3.ZERO:
		# LOD AI: mimo dosah rovnou na misto
		u.position = Vector3((m[0] as Vector2).x, 0.0, (m[0] as Vector2).y)
		c["cesta"] = PackedVector2Array()
		c["na_miste"] = true
		c["na_miste_t"] = 1000.0
		c["uvnitr"] = pr_cil
	else:
		var pr_ted: Dictionary = c.get("uvnitr", {})
		if bool(cn.get("skryty", false)) and not pr_ted.is_empty() and pr_cil.is_empty() 				and (m[0] as Vector2).distance_to(pr_ted["venku"]) < float(P["dvere"]["stejne_m"]):
			# uvnitr budovy ke dverim tehoz domu (hostinsky jde spat): zevnitr ke dverim (pres body uvnitr pozpatku)
			var bt: PackedVector2Array = pr_ted.get("body", PackedVector2Array())
			var cs := PackedVector2Array()
			for i in range(bt.size() - 1, -1, -1):
				cs.append(bt[i])
			cs.append(m[0])
			c["cesta"] = cs
		else:
			_pozadej(c, [p, m[0], INF, pr_cil, true])
		c["uvnitr_cil"] = pr_cil
		c["i"] = 0
		c["na_miste"] = false
	if not (c["trasa"] as Array).has(m[0]):
		(c["trasa"] as Array).append(m[0])


func _delka(c: Dictionary, jm: String) -> float:
	var ap: AnimationPlayer = c["ap"]
	return ap.get_animation(jm).length / maxf(float(c.get("tempo", 1.0)), 0.1) if ap.has_animation(jm) else 0.0


func _uvolni(c: Dictionary) -> void:
	for k: String in _obsazeno.keys():
		if _obsazeno[k] == c["id"] and not k.begins_with("postel:"):
			_obsazeno.erase(k)
	c["sedak"] = {}


## Misto cinnosti s rezervaci (plan krok 3): sed jen na skutecnem sedaku (vybaveni sveta), hovor ve skupine
## kolem bodu celem k sobe, skryta cinnost (doma, spi) u dveri. Vrati [Vector2, yaw nebo INF].
func _misto_cinnosti(c: Dictionary, kde: String, cn: Dictionary) -> Array:
	var hv: Dictionary = P["hovor"]
	if bool(cn.get("skupina", false)):
		# hovor: misto skupiny, kde uz nekdo ceka a je volno (dvojice), jinak prazdne
		var kandidati: Array = [kde]
		if kde == "naves":
			kandidati = (P["mista"] as Dictionary).keys().filter(func(k: String) -> bool: return String(P["mista"][k].get("skupina", "")) == "naves")
		var uhly: Array = hv["uhly_st"]
		var nej := ""
		var nej_n := -1
		var stred := Vector2.ZERO
		for k: String in kandidati:
			# skupina = poloha stredu (dvere stejneho domu sdili dva obyvatele)
			var st: Vector2 = _misto(c, k)[0]
			var kk := str(st.snapped(Vector2.ONE))
			var n := 0
			for s2 in uhly.size():
				if _obsazeno.has("hovor:%s:%d" % [kk, s2]):
					n += 1
			# nejlepsi: neuplna skupina s nejvic lidmi (partner ceka); prazdna az pak (nahodne poradi)
			var skore := n if n < uhly.size() else -2
			if skore > nej_n or (skore == nej_n and _rng.randf() < 0.5):
				nej_n = skore
				nej = kk
				stred = st
		if nej_n >= 0:
			for s2 in uhly.size():
				var kl := "hovor:%s:%d" % [nej, s2]
				if not _obsazeno.has(kl):
					_obsazeno[kl] = c["id"]
					var a := deg_to_rad(float(uhly[s2]) + float(hv["natoceni_st"]))
					var q := stred + Vector2(sin(a), cos(a)) * float(hv["polomer_m"])
					var k2 := stred - q
					return [q, atan2(k2.x, k2.y)]
	var m: Array = _misto(c, kde)
	if kde == "zahrada":
		var zh := _zahon(c, m[0])
		if not zh.is_empty():
			return zh
	if bool(cn.get("sed", false)):
		var sd := _sedak(c, m[0], String((P["mista"].get(kde, {}) as Dictionary).get("mistnost", "")))
		if not sd.is_empty():
			c["sedak"] = sd
			return [sd["stani"], sd["yaw"]]
	if bool(cn.get("skryty", false)):
		# domov u domu je bod pred dvermi (celem ven) - otocit ke dverim; jine misto: nejblizsi dvere dilu (Pohyb_dvere*)
		var dv := _dvere_u(m[0], c, kde)
		if not dv.is_empty():
			return dv
	return m


## Nejblizsi volny sedak (postavy.json sedani.sedaky, vybaveni sveta) do hledat_m od mista; lavice ma mista po
## sirka_mista_m. Vyska sedaku = rozmer[1] z katalogu, sedak mimo toleranci vysky klipu se nepouzije.
## Vrati {stani: Vector2 (koren postavy), yaw, y: vyska korene, sedak: Vector2, klic} nebo {}.
func _sedak(c: Dictionary, kde: Vector2, mistnost := "") -> Dictionary:
	var sd: Dictionary = P["sedani"]
	var kat := katalog()
	var nej := {}
	var nd := float(sd["hledat_m"])
	if main == null or main.svet == null:
		return {}
	var vb: Array = main.svet.data.get("vybaveni", [])
	for ri in vb.size():
		var r: Dictionary = vb[ri]
		var id := String(r["id"])
		if not (sd["sedaky"] as Array).has(id) or r.has("up"):
			continue
		var rz: Array = (kat.get(id, {}) as Dictionary).get("rozmer", [])
		if rz.size() < 3 or absf(float(rz[1]) - float(sd["vyska_klipu_m"])) > float(sd["tolerance_m"]):
			continue
		var p0 := Vector3(float(r["p"][0]), float(r["p"][1]), float(r["p"][2]))
		# vnitrni misto (mista.mistnost): jen sedak v te mistnosti; venku jen sedak mimo vsechny mistnosti (do domu
		# by postava vesla zdi - dvermi chodi jen k mistum s pruchodem)
		if _mistnost_u(p0) != mistnost:
			continue
		var yaw := float(r["yaw"])
		var osa_x := Vector2(cos(yaw), -sin(yaw))
		var n := maxi(1, floori(float(rz[0]) / float(sd["sirka_mista_m"])))
		for k in n:
			var klic := "sed:%d:%d" % [ri, k]
			if _obsazeno.has(klic):
				continue
			var q := Vector2(p0.x, p0.z) + osa_x * (float(k) - (n - 1) * 0.5) * float(sd["sirka_mista_m"])
			var d := q.distance_to(kde)
			if d < nd:
				nd = d
				nej = {"klic": klic, "yaw": yaw, "y": p0.y + float(rz[1]) - float(sd["vyska_klipu_m"]), "sedak": q, "lavice": n > 1}
	if not nej.is_empty():
		# celem ke stolu u sedaku, jinak k ohni, jinak k mistu cinnosti (_ohen_u); lavice jen kolmo (sedi se na ni
		# obkrocmo jen vyjimecne), stolicka primo k cili - jen pro vybrany sedak (rozpocet snimku)
		var q: Vector2 = nej["sedak"]
		var cil := _ohen_u(q, kde)
		var smer: Vector2
		if bool(nej["lavice"]):
			var osa_z := Vector2(sin(float(nej["yaw"])), cos(float(nej["yaw"])))
			var kam := osa_z.dot(cil - q)
			smer = osa_z * (signf(kam) if kam != 0.0 else 1.0)
		else:
			smer = (cil - q).normalized() if cil.distance_to(q) > 0.05 else Vector2(sin(float(nej["yaw"])), cos(float(nej["yaw"])))
		nej["yaw"] = atan2(smer.x, smer.y)
		nej["stani"] = q + smer * float(sd["pred_m"])
		_obsazeno[nej["klic"]] = c["id"]
	return nej


## Mistnost (svet data mistnosti: stred pos, rozmer size, yaw), ve ktere bod lezi; "" = venku.
## Mistnosti z svet.info rooms (svet._info: otocene mistnosti vsi/hostince = stred podlahy + inv, tvrz = AABB od rohu -
## driv se tu pos bral vzdy jako stred a v tvrzi vychazela spatna mistnost, predani.md „Ubytovna“).
func _mistnost_u(p: Vector3) -> String:
	if main == null or main.svet == null:
		return ""
	for m: Dictionary in (main.svet.info as Dictionary).get("rooms", []):
		var ab: AABB = m["aabb"]
		var q: Vector3 = (m["inv"] as Transform3D) * p if m.has("inv") else p
		if q.x >= ab.position.x and q.x <= ab.end.x and q.z >= ab.position.z and q.z <= ab.end.z \
				and q.y > ab.position.y - 0.5 and q.y < ab.end.y:
			return String(m["name"])
	return ""


## Misto u predmetu (vybaveni sveta ri): stred strany kvadru z katalogu + u_predmetu.od_m, celem k predmetu. strana
## "dlouha" = nejdriv delsi strany (zahon), "cela" = kratsi (celo stolu, lavice jsou podel). Bunka mrizky volna, cil bez
## jine postavy (rozestup); rezervovat = misto obsazeno pro c (_uvolni). Vrati [Vector2, yaw] nebo [].
func _u_predmetu(c: Dictionary, ri: int, strana: String, rezervovat: bool) -> Array:
	var r: Dictionary = main.svet.data["vybaveni"][ri]
	var rz: Array = (katalog().get(String(r["id"]), {}) as Dictionary).get("rozmer", [])
	if rz.size() < 3:
		return []
	var yaw := float(r["yaw"])
	var ox := Vector2(cos(yaw), -sin(yaw))
	var oz := Vector2(sin(yaw), cos(yaw))
	var p0 := Vector2(float(r["p"][0]), float(r["p"][2]))
	var hx := float(rz[0]) * 0.5
	var hz := float(rz[2]) * 0.5
	var od := float(P["u_predmetu"]["od_m"])
	var strany: Array = [[oz, hz, hx], [-oz, hz, hx], [ox, hx, hz], [-ox, hx, hz]]   # [normala, pul hloubky, pul delky strany]
	strany.sort_custom(func(a: Array, b: Array) -> bool: return float(a[2]) > float(b[2]) if strana == "dlouha" else float(a[2]) < float(b[2]))
	for s: Array in strany:
		var q: Vector2 = p0 + (s[0] as Vector2) * (float(s[1]) + od)
		# od sedaku (Misa 9. 11. snimek hospoda_sin2: senkyrka u cela stolu tesne za zady sediciho na konci lavice):
		# misto stoji od_sedaku_m od pudorysu kazdeho sedaku (sedici tam ma zada a lokty), odsune se podel normaly strany
		q = _od_sedaku(q, s[0] as Vector2, p0)
		var klic := "u:%d:%s" % [ri, str((s[0] as Vector2).snapped(Vector2.ONE * 0.01))]
		if rezervovat and _obsazeno.has(klic) and _obsazeno[klic] != c["id"]:
			continue
		if rezervovat and _cil_obsazen(c, q, float(P["rozestup"]["misto_m"])):
			continue                                  # (pevne misto z _misto se pamatuje - bez zavislosti na ostatnich)
		if is_nan(_nav_bunka(_nav_ij(q), float(r["p"][1]))):
			continue
		if rezervovat:
			_obsazeno[klic] = c["id"]
		var k := p0 - q
		return [q, atan2(k.x, k.y)]
	return []


## Bod q odsunuty po normale n od pudorysu sedaku (postavy.json sedani.sedaky, kvadr z katalogu) na u_predmetu.od_sedaku_m.
func _od_sedaku(q: Vector2, n: Vector2, p0: Vector2) -> Vector2:
	var od := float(P["u_predmetu"].get("od_sedaku_m", 0.0))
	if od <= 0.0 or main == null or main.svet == null:
		return q
	var sedaky: Array = P["sedani"]["sedaky"]
	var kat := katalog()
	var kus: Array = []
	for r: Dictionary in main.svet.data.get("vybaveni", []):
		if not sedaky.has(String(r["id"])) or r.has("up"):
			continue
		var c0 := Vector2(float(r["p"][0]), float(r["p"][2]))
		if c0.distance_to(p0) > 4.0:
			continue
		var rz: Array = (kat.get(String(r["id"]), {}) as Dictionary).get("rozmer", [])
		if rz.size() >= 3:
			kus.append([c0, float(r["yaw"]), float(rz[0]) * 0.5, float(rz[2]) * 0.5])
	var krok := float(P["u_predmetu"].get("od_sedaku_krok_m", 0.1))
	for _i in int(P["u_predmetu"].get("od_sedaku_kroku", 10)):
		var blizko := false
		for k: Array in kus:
			var dq: Vector2 = q - (k[0] as Vector2)
			var lx := dq.dot(Vector2(cos(float(k[1])), -sin(float(k[1]))))
			var lz := dq.dot(Vector2(sin(float(k[1])), cos(float(k[1]))))
			if Vector2(maxf(absf(lx) - float(k[2]), 0.0), maxf(absf(lz) - float(k[3]), 0.0)).length() < od:
				blizko = true
				break
		if not blizko:
			break
		q += n * krok
	return q


## Prace na zahonu (Misa r. 71: pracovali vedle zahonu a dva v sobe): nejblizsi zahon (vybaveni id u_predmetu.zahrada*)
## do hledat_m od bodu zahrady domu, misto u jeho dlouhe strany s rezervaci. [] = zadny zahon (stary bod zahrady).
func _zahon(c: Dictionary, kde: Vector2) -> Array:
	var up: Dictionary = P["u_predmetu"]
	var vb: Array = main.svet.data.get("vybaveni", []) if main != null and main.svet != null else []
	var kand: Array = []
	for ri in vb.size():
		var r: Dictionary = vb[ri]
		if not String(r["id"]).begins_with(String(up["zahrada"])):
			continue
		var d := Vector2(float(r["p"][0]), float(r["p"][2])).distance_to(kde)
		if d < float(up["hledat_m"]):
			kand.append([d, ri])
	kand.sort()
	for kk: Array in kand:
		var u := _u_predmetu(c, int(kk[1]), "dlouha", true)
		if not u.is_empty():
			return u
	return []


## Je cil q do r od ciloveho mista jine postavy?
func _cil_obsazen(c: Dictionary, q: Vector2, r: float) -> bool:
	for o: Dictionary in _lide:
		if o != c and o.get("misto") is Vector2 and (o["misto"] as Vector2).distance_to(q) < r:
			return true
	return false


## Rozestup cilu (Misa r. 63/71): cil u ciloveho mista jine postavy -> nejblizsi volny bod na kruhu misto_m (2 kruhy,
## smeru kandidatu), bunka mrizky pruchozi; jinak puvodni cil.
func _rozestup(c: Dictionary, q: Vector2) -> Vector2:
	var rs: Dictionary = P["rozestup"]
	var r := float(rs["misto_m"])
	if not _cil_obsazen(c, q, r):
		return q
	var n := int(rs["smeru"])
	for kruh in [1, 2]:
		for i in n:
			var a := TAU * float(i) / n
			var q2: Vector2 = q + Vector2(sin(a), cos(a)) * r * float(kruh)
			if _cil_obsazen(c, q2, r) or is_nan(_nav_bunka(_nav_ij(q2), podlaha(q2))):
				continue
			return q2
	return q


## Chuze za jinou postavou (rozestup.chuze_m, kuzel 60 st. pred sebou): pocka, nejvys cekani_max_s; na postavu, ktera
## uz ceka na ni, neceka (dve proti sobe se nezablokuji). Vrati true = stat.
func _ceka_za(c: Dictionary, p: Vector2, k: Vector2, dt: float) -> bool:
	var rs: Dictionary = P["rozestup"]
	# prochazi vsechny postavy - jen jednou za kontrola_s (postavy.json rozestup), mezitim plati posledni vysledek
	c["ceka_kt"] = float(c.get("ceka_kt", 0.0)) + dt
	if float(c["ceka_kt"]) < float(rs["kontrola_s"]):
		if c.has("ceka_na"):
			c["ceka_t"] = float(c.get("ceka_t", 0.0)) + dt
		return c.has("ceka_na") and float(c.get("ceka_t", 0.0)) <= float(rs["cekani_max_s"])
	dt = float(c["ceka_kt"])
	c["ceka_kt"] = 0.0
	var r := float(rs["chuze_m"])
	var smer := k.normalized()
	for o: Dictionary in _lide:
		if o == c or not (o["uzel"] as Node3D).visible or String(o.get("ceka_na", "")) == String(c["id"]):
			continue
		var on: Node3D = o["uzel"]
		var d := Vector2(on.position.x, on.position.z) - p
		var dl := d.length()
		if dl < r and dl > 0.01 and d.dot(smer) > dl * 0.5:
			c["ceka_t"] = float(c.get("ceka_t", 0.0)) + dt
			if float(c["ceka_t"]) > float(rs["cekani_max_s"]):
				c.erase("ceka_na")
				return false
			c["ceka_na"] = o["id"]
			return true
	c["ceka_t"] = 0.0
	c.erase("ceka_na")
	return false


## Pruchod dvermi k vnitrnimu mistu (postavy.json mista: dvere = pohyb dveri, venku / vnitrek = body pred a za
## dvermi). Vrati {skupina, venku, vnitrek} nebo {} (misto venku).
func _pruchod(kde: String) -> Dictionary:
	var z: Dictionary = P["mista"].get(kde, {})
	if not z.has("dvere"):
		return {}
	var sk := String(z["dvere"])
	var ph: Array = main.svet.data.get("pohyb", []) if main != null and main.svet != null else []
	for e: Dictionary in ph:
		if String(e["name"]) == sk:
			sk = String(e.get("group", e["name"]))
			break
	var body := PackedVector2Array()
	for b: Array in z.get("uvnitr", []):
		body.append(Vector2(float(b[0]), float(b[1])))
	return {"skupina": sk, "venku": Vector2(float(z["venku"][0]), float(z["venku"][1])),
			"vnitrek": Vector2(float(z["vnitrek"][0]), float(z["vnitrek"][1])), "body": body}


## Cesta s pruchodem dvermi (Misa 5. 11. „sezeni v senku“): z vnitrku ven dvermi, k vnitrnimu mistu dvermi dovnitr,
## uvnitr tehoz domu rovne. Dvere se otevrou u dveri a zavrou za postavou (c.dvere, po_i = posledni bod pruchodu).
func _cesta_pruchod(c: Dictionary, p: Vector2, cil: Vector2, pr_cil: Dictionary) -> PackedVector2Array:
	var pr_ted: Dictionary = c.get("uvnitr", {})
	var out := PackedVector2Array()
	var od := p
	var stejny := not pr_ted.is_empty() and not pr_cil.is_empty() and String(pr_ted["skupina"]) == String(pr_cil["skupina"])
	if stejny:
		out.append(cil)
		return out
	if not pr_ted.is_empty():
		# ven: body uvnitr pozpatku (otvor mezi mistnostmi), vnitrek, dvere, venku
		var bt: PackedVector2Array = pr_ted.get("body", PackedVector2Array())
		for i in range(bt.size() - 1, -1, -1):
			out.append(bt[i])
		out.append(pr_ted["vnitrek"])
		out.append(pr_ted["venku"])
		c["dvere"] = {"skupina": pr_ted["skupina"], "vnitrek": pr_ted["vnitrek"], "venku": pr_ted["venku"], "otevrel": false, "po_i": out.size() - 1, "pruchod": true}
		od = pr_ted["venku"]
	if pr_cil.is_empty():
		out.append_array(_cesta(od, cil))
		return out
	out.append_array(_cesta(od, pr_cil["venku"]))
	out.append(pr_cil["vnitrek"])
	if pr_ted.is_empty():
		c["dvere"] = {"skupina": pr_cil["skupina"], "vnitrek": pr_cil["vnitrek"], "venku": pr_cil["venku"], "otevrel": false, "po_i": out.size() - 1, "pruchod": true}
	out.append_array(pr_cil.get("body", PackedVector2Array()))
	out.append(cil)
	return out


## Kam se sedici diva: ohniste nebo stul do k_ohni_m od sedaku, jinak misto cinnosti.
func _ohen_u(q: Vector2, kde: Vector2) -> Vector2:
	# Misa 9. 11. r. 82 (hostinec, snimky 09-10: hoste sedi u stolu bokem): drive prvni stul NEBO ohniste do k_ohni_m
	# v poradi vybaveni - v sini hostince vyhralo ohniste a hoste sedeli bokem ke stolu. Ted nejblizsi stul do
	# sedani.ke_stolu_m (od pudorysu stolu) ma prednost, jinak nejblizsi ohniste do k_ohni_m, jinak misto cinnosti.
	var kat := katalog()
	var stul := Vector2.INF
	var ds := float(P["sedani"]["ke_stolu_m"])
	var ohen := Vector2.INF
	var do := float(P["sedani"]["k_ohni_m"])
	for r: Dictionary in main.svet.data.get("vybaveni", []):
		var id := String(r["id"])
		var p := Vector2(float(r["p"][0]), float(r["p"][2]))
		if id.begins_with("stul"):
			var rz: Array = (kat.get(id, {}) as Dictionary).get("rozmer", [1.0, 0.75, 1.0])
			var yw := float(r["yaw"])
			var dq := q - p
			var dk := Vector2(maxf(absf(dq.dot(Vector2(cos(yw), -sin(yw)))) - float(rz[0]) * 0.5, 0.0), maxf(absf(dq.dot(Vector2(sin(yw), cos(yw)))) - float(rz[2]) * 0.5, 0.0)).length()
			if dk < ds:
				ds = dk
				# k nejblizsimu bodu pudorysu stolu (lavice podel stolu: kolmo ke stolu, stolicka u rohu: k rohu)
				var lx := clampf(dq.dot(Vector2(cos(yw), -sin(yw))), -float(rz[0]) * 0.5, float(rz[0]) * 0.5)
				var lz := clampf(dq.dot(Vector2(sin(yw), cos(yw))), -float(rz[2]) * 0.5, float(rz[2]) * 0.5)
				stul = p + Vector2(cos(yw), -sin(yw)) * lx + Vector2(sin(yw), cos(yw)) * lz
		elif id.begins_with("ohniste") and p.distance_to(q) < do:
			do = p.distance_to(q)
			ohen = p
	if stul != Vector2.INF:
		return stul
	if ohen != Vector2.INF:
		return ohen
	return kde if kde.distance_to(q) > 0.3 else q + Vector2(0, 1)


## Dvere pro skrytou cinnost: misto u domu (domov, dvere) uz je bod pred dvermi - postava se otoci ke dverim;
## jine misto -> nejblizsi dvere dilu (svet pohyb Pohyb_<predpona>) do hledat_m, ne v patre. Vrati [Vector2, yaw] nebo [].
func _dvere_u(q: Vector2, c: Dictionary, kde: String) -> Array:
	var dv: Dictionary = P["dvere"]
	if kde in ["domov", "dvere"] and not (c["o"]["domov"] as Dictionary).has("misto"):
		var m: Array = _misto(c, kde)
		return [m[0], float(m[1]) + PI] if float(m[1]) != INF else []
	var z: Dictionary = P["mista"].get(String(c["o"]["domov"].get("misto", kde)) if kde == "domov" else kde, {})
	if z.has("pohyb"):
		return []                                     # misto uz jsou dvere dilu (mlyn)
	if main == null or main.svet == null:
		return []
	var nej: Array = []
	var nd := float(dv["hledat_m"])
	for e: Dictionary in main.svet.data.get("pohyb", []):
		if not String(e["name"]).begins_with(String(dv["predpona"])):
			continue
		var u: Array = e.get("use", e["pos"])
		var p := Vector2(float(u[0]), float(u[2]))
		if float(u[1]) - float(main.svet.call("_vyska", p.x, p.y)) > float(dv["patro_m"]):
			continue
		if p.distance_to(q) < nd:
			nd = p.distance_to(q)
			var k := p - q
			nej = [p, atan2(k.x, k.y)]
	return nej


## Vstup do domu (Misa 5. 11. „dojde ke dverim, otevre, vejde a rano vyjde“): na miste u dveri otevre dvere dilu
## (pohyb.gd skupina do dvere.otevrit_m), vejde dvere.dovnitr_m dovnitr, pak se skryje a dvere, ktere otevrel, zavre.
## Spanek: ma-li obyvatel v budove postel (postavy.json obyvatele.spanek, vybaveni sveta s lehat), lezi v ni
## (klip spani.klip v case 0 - lezici poza), jinak je skryty. Vrati true, kdyz uz je uvnitr.
func _vstup(c: Dictionary, cn: Dictionary) -> bool:
	var st := int(c.get("vchazi", 0))
	var dvp: Dictionary = P["dvere"]
	if st == 0:
		var dvere: Vector2 = c["misto"]
		var fw := Vector2(sin(float(c["yaw_mista"])), cos(float(c["yaw_mista"]))) if float(c["yaw_mista"]) != INF else Vector2.ZERO
		c["dvere"] = {"skupina": _dvere_skupina(dvere), "vnitrek": dvere + fw * float(dvp["dovnitr_m"]), "venku": dvere, "otevrel": false}
		if float(c["na_miste_t"]) >= 1000.0:
			# LOD AI (mimo dohled): rovnou uvnitr
			c["vchazi"] = 2
			_do_postele(c, cn)
			return true
		_dvere_otevri(c, false)
		c["vchazi"] = 1
		c["cesta"] = PackedVector2Array([c["dvere"]["vnitrek"]])
		c["i"] = 0
		c["na_miste"] = false
		return false
	if st == 1:
		c["vchazi"] = 2
		c["na_miste_t"] = float(dvp["cekani_s"])
		_do_postele(c, cn)
	return true


func _do_postele(c: Dictionary, cn: Dictionary) -> void:
	if not bool(cn.get("spanek", false)):
		return
	var pst: Dictionary = _postel(c)
	if pst.is_empty():
		return
	var sp: Dictionary = P["spani"]
	var u: Node3D = c["uzel"]
	var pz: Array = sp["posun"]
	var xf := Transform3D(Basis(Vector3.UP, float(pst["yaw"]) + deg_to_rad(float(sp["otoceni_st"]))), pst["p"])
	# vyska korene nad patou luzka podle druhu (spani.nad_postel_m), v luzku pro dva vedle sebe po rozestup_m
	var bok := (float(pst["misto"]) - (float(pst["mist"]) - 1.0) * 0.5) * float(sp["rozestup_m"])
	u.position = xf * Vector3(float(pz[0]) + bok, nad_postel(String(pst["id"])), float(pz[1]))
	u.rotation.y = float(pst["yaw"]) + deg_to_rad(float(sp["otoceni_st"]))
	c["y"] = u.position.y
	c["yaw_mista"] = u.rotation.y
	c["postel_y"] = u.position.y                       # vyska z postele, ne paprskem
	c["v_posteli"] = true
	ruce(c, {})
	_klip(c, String(sp["klip"]), 0.0)
	(c["ap"] as AnimationPlayer).seek(0.0, true)
	c["obmena"] = 1e9


## Vyska korene lezici postavy nad patou luzka (postavy.json spani.nad_postel_m podle id luzka, "*" ostatni).
static func nad_postel(id: String) -> float:
	var t: Dictionary = P["spani"]["nad_postel_m"]
	return float(t.get(id, t["*"]))


## Postel obyvatele: zaznam spanek {budova, postel} - luzko ze seznamu svet data postele (nabytek.json: kusy s lehat
## ve vybaveni a luzka zapecena v modelu budovy) se stejnou budovou a id; volne misto v luzku (mist) se rezervuje
## natrvalo (manzele vedle sebe). Vrati {p: Vector3, yaw, id, misto, mist} nebo {} (dira - skryty doma).
func _postel(c: Dictionary) -> Dictionary:
	if not _postele_rozdeleny and main != null and main.svet != null:
		# poprve: luzka vsem v poradi obyvatel (hostinsky pred pocestnymi, ne podle toho, kdo jde driv spat)
		_postele_rozdeleny = true
		for c2: Dictionary in _lide:
			_postel_prirad(c2)
	return c.get("postel_z", {}) if c.has("postel_z") else _postel_prirad(c)


func _postel_prirad(c: Dictionary) -> Dictionary:
	if c.has("postel_z"):
		return c["postel_z"]
	var sp: Dictionary = (c["o"] as Dictionary).get("spanek", {})
	if String(sp.get("postel", "")) == "" or main == null or main.svet == null:
		return {}
	if sp.has("sdili"):
		# luzko na smeny (nocni strazny spi ve dne v luzku denniho): stejne misto jako obyvatel sdili
		for c2: Dictionary in _lide:
			if String(c2["id"]) == String(sp["sdili"]):
				var z2: Dictionary = _postel_prirad(c2)
				if not z2.is_empty():
					c["postel_z"] = z2
				return z2
		return {}
	var pst: Array = main.svet.data.get("postele", [])
	for i in pst.size():
		var r: Dictionary = pst[i]
		if String(r["budova"]) != String(sp["budova"]) or String(r["id"]) != String(sp["postel"]):
			continue
		for k in int(r["mist"]):
			var kl := "postel:%d:%d" % [i, k]
			if _obsazeno.has(kl) and _obsazeno[kl] != c["id"]:
				continue
			_obsazeno[kl] = c["id"]
			c["postel_z"] = {"p": r["p"], "yaw": float(r["yaw"]), "id": String(r["id"]), "misto": k, "mist": int(r["mist"])}
			return c["postel_z"]
	return {}


## Skupina pohyblivych dveri (pohyb.gd) u bodu: nejblizsi zaznam pohyb druhu dvere do dvere.otevrit_m.
func _dvere_skupina(q: Vector2) -> String:
	if main == null or main.svet == null:
		return ""
	var nej := ""
	var nd := float(P["dvere"]["otevrit_m"])
	for e: Dictionary in main.svet.data.get("pohyb", []):
		if String(e.get("kind", "")) != "dvere":
			continue
		var u: Array = e.get("use", e["pos"])
		var d := Vector2(float(u[0]), float(u[2])).distance_to(q)
		if d < nd:
			nd = d
			nej = String(e.get("group", e["name"]))
	return nej


func _dvere_otevri(c: Dictionary, ven: bool) -> void:
	var dv: Dictionary = c.get("dvere", {})
	var ph: Node = main.get("pohyb") if main else null
	if dv.is_empty() or ph == null or String(dv["skupina"]) == "":
		return
	var g: Dictionary = (ph.get("groups") as Dictionary).get(String(dv["skupina"]), {})
	if not g.is_empty() and float(g["target"]) < 0.5:
		ph.call("toggle", String(dv["skupina"]))
		dv["otevrel"] = true
		dv["ven"] = ven


## Dvere, ktere postava otevrela, zavre: uvnitr (po skryti) nebo venku, kdyz je od dveri dal nez dvere.zavrit_m.
func _dvere_zavri_za(c: Dictionary) -> void:
	var dv: Dictionary = c.get("dvere", {})
	if dv.is_empty() or not bool(dv.get("otevrel", false)):
		return
	var u: Node3D = c["uzel"]
	var uvnitr := int(c.get("vchazi", 0)) == 2 and float(c["na_miste_t"]) >= float(P["dvere"]["cekani_s"])
	var venku := int(c.get("vchazi", 0)) == 0 and Vector2(u.position.x, u.position.z).distance_to(dv["venku"]) > float(P["dvere"]["zavrit_m"]) 			and int(c["i"]) > int(dv.get("po_i", -1))
	if uvnitr or venku:
		var ph: Node = main.get("pohyb")
		var g: Dictionary = (ph.get("groups") as Dictionary).get(String(dv["skupina"]), {})
		if not g.is_empty() and float(g["target"]) > 0.5:
			ph.call("toggle", String(dv["skupina"]))
		dv["otevrel"] = false


## Tabulka reakci (postavy.json reakce, prvni platna vyhrava; reserse_reakce_kcd2.md 6.5): podminky na povest
## a vzhled hrace (zatim vychozi z hrac_dojem), vzdalenost a povahu role; replika nad hlavou s odstupy, klip jen na miste.
func _reakce(c: Dictionary, cn: Dictionary, d: float) -> void:
	var role: Dictionary = c["role"]
	var dj: Dictionary = P["dojem"]
	var povest := float(dj["povest_vychozi"])
	var trida := float(dj["vzhled_trida"])
	var so := float(cn.get("soustredeni", 0.0)) if bool(c["na_miste"]) else float(P["pr"]["soustredeni_chuze"])
	var ml := float(role.get("mluvnost", 0.3))
	for r: Dictionary in P["reakce"]:
		if r.has("povest_od") and povest < float(r["povest_od"]):
			continue
		if r.has("povest_pod") and povest >= float(r["povest_pod"]):
			continue
		if r.has("trida_od") and trida < float(r["trida_od"]):
			continue
		if r.has("d_m") and d > float(r["d_m"]):
			continue
		if r.has("ucta_od") and float(role.get("ucta", 0.5)) < float(r["ucta_od"]):
			continue
		if r.has("mluvnost_od") and ml < float(r["mluvnost_od"]):
			continue
		if bool(r.get("nahoda_mluvnost", false)) and _rng.randf() >= ml * (1.0 - so):
			continue
		var rep := String(r["replika"])
		if rep == "":
			# jen pohled: zvedavost x (1 - soustredeni), par sekund
			c["na_hrace"] = _rng.randf() < float(role.get("zvedavost", 0.3)) * (1.0 - so)
		else:
			c["na_hrace"] = true
			rep = String((role.get("repliky", {}) as Dictionary).get(rep, rep))
			_rekni(c, rep, float(r.get("mluvnost_k", 1.0)))
			if String(r["klip"]) != "" and bool(c["na_miste"]) and not bool(c.get("sedi", false)) and not bool(c.get("v_posteli", false)):
				_klip(c, String(r["klip"]), 1.0)
				c["obmena"] = 2.5
		var ps: Array = P["pr"]["pohled_hrac_s"]
		c["pohled"] = _rng.randf_range(float(ps[0]), float(ps[1]))
		return


## Replika nad hlavou (Label3D, zobrazit_s) - odstupy: cela ves ves_odstup_s, postava postava_odstup_s, pozdrav
## stejne postavy pozdrav_znovu_s.
func _rekni(c: Dictionary, klic: String, k_sance: float) -> void:
	var rp: Dictionary = P["vn"]["repliky"]
	if _t - _ves_replika < float(rp["ves_odstup_s"]) or _t - float(c.get("rekl_t", -1000.0)) < float(rp["postava_odstup_s"]):
		return
	if klic.begins_with("pozdrav") and _t - float(c.get("pozdrav_t", -1000.0)) < float(rp["pozdrav_znovu_s"]):
		return
	if _rng.randf() > k_sance:
		return
	var moz: Array = P["repliky"].get(klic, [])
	if moz.is_empty():
		return
	var lb: Label3D = c.get("bublina")
	if lb == null:
		lb = Label3D.new()
		lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lb.pixel_size = 0.0035
		lb.font_size = 40
		lb.outline_size = 10
		lb.no_depth_test = false
		lb.position = Vector3(0, 2.05, 0)
		(c["uzel"] as Node3D).add_child(lb)
		c["bublina"] = lb
	lb.text = String(moz[_rng.randi() % moz.size()])
	lb.visible = true
	c["bublina_s"] = float(rp["zobrazit_s"])
	c["rekl_t"] = _t
	_ves_replika = _t
	if klic.begins_with("pozdrav"):
		c["pozdrav_t"] = _t


func _bublina_cas(c: Dictionary, dt: float) -> void:
	if float(c.get("bublina_s", 0.0)) <= 0.0:
		return
	c["bublina_s"] = float(c["bublina_s"]) - dt
	if float(c["bublina_s"]) <= 0.0:
		(c["bublina"] as Label3D).visible = false


## Vyska zeme pod postavou: paprsek z vysky y0 + schod_m dolu (podlaha, schod, teren), bez strech nad hlavou.
## Prvni poloha (y0 = 0, postava jeste neni usazena): teren sveta.
func _zem(p: Vector2, y0: float) -> float:
	if y0 == 0.0:
		return float(main.svet.call("_vyska", p.x, p.y))
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, y0 + float(P["schod_m"]), p.y), Vector3(p.x, y0 - 30.0, p.y))
	var h := get_viewport().get_world_3d().direct_space_state.intersect_ray(q)
	return float((h["position"] as Vector3).y) if not h.is_empty() else float(main.svet.call("_vyska", p.x, p.y))


## Klip postavy: prolinani P.blend, rychlost prehravani (chuze podle rychlosti postavy).
func _klip(c: Dictionary, jm: String, tempo: float) -> void:
	var ap: AnimationPlayer = c["ap"]
	# v posteli jen poza spanku (r. 59, 85): jiny klip by postavu postavil ve vysce luzka - vstava se jen pres
	# _novy_blok (v_posteli = false, pak teprve klip)
	if bool(c.get("v_posteli", false)) and jm != String(P["spani"]["klip"]):
		return
	if String(c["klip"]) != jm:
		# tempo 0 = stojici poza (lezeni v posteli): bez prolinani - prolinani v AnimationPlayer ubyva s casem
		# x speed_scale, pri 0 se nikdy nedokonci a postava zustala v predchozi poze (Misa 0.99993 r. 59: stoji na luzku)
		ap.play(jm, float(P["blend"]) if tempo > 0.0 else 0.0)
		c["klip"] = jm
		# predmety v rukou podle klipu cinnosti (postavy.json cinnosti.v_rukou: klip nebo "*" = ostatni klipy
		# cinnosti i chuze); reakce (kyvnuti) predmet v ruce nechava
		var vr: Dictionary = (c.get("cn", {}) as Dictionary).get("v_rukou", {})
		if not _klip_reakce(jm):
			ruce(c, vr.get(jm, vr.get("*", {})))
	ap.speed_scale = tempo * float(c.get("tempo", 1.0))


static func _klip_reakce(jm: String) -> bool:
	for r: Dictionary in P["reakce"]:
		if String(r.get("klip", "")) == jm and jm != "":
			return true
	return false


## Predmet v ruce postavy (plan krok 2): hotovy model z katalogu (modely/predmety/<id>.glb) na kosti ruky
## (BoneAttachment3D jako telo hrace); uchop = bod predmetu v ruce, rot_st natoceni v soustave kosti (postavy.json drzeni).
## spec {"r": id, "l": id}; prazdny = ruce volne. Predmety stin nevrhaji (male, tablet).
func ruce(c: Dictionary, spec: Dictionary) -> void:
	var dr: Dictionary = P["drzeni"]
	for ruka: String in ["r", "l"]:
		var id := String(spec.get(ruka, ""))
		var drzi: Dictionary = c["ruce"]
		if String(drzi.get(ruka + "_id", "")) == id:
			continue
		var stary: Node = drzi.get(ruka + "_uzel")
		if stary:
			stary.queue_free()
			drzi.erase(ruka + "_uzel")
		drzi[ruka + "_id"] = id
		if drzi.has("mod"):
			(drzi["mod"] as Node).call("nastav", ruka, "", {}, null)
		if id == "":
			continue
		if not _predmet_sc.has(id):
			_predmet_sc[id] = load(PREDMETY_DIR + id + ".glb") if ResourceLoader.exists(PREDMETY_DIR + id + ".glb") else null
		var ps: PackedScene = _predmet_sc[id]
		if ps == null:
			push_warning("lide: predmet %s nema model" % id)
			continue
		var kostra: Skeleton3D = c["kostra"]
		var ba: BoneAttachment3D = drzi.get(ruka + "_kost")
		if ba == null:
			ba = BoneAttachment3D.new()
			ba.bone_name = "hand_" + ruka
			kostra.add_child(ba)
			drzi[ruka + "_kost"] = ba
		var d: Dictionary = dr.get(id, {})
		var drz := Node3D.new()
		drz.name = "drzi_" + id
		var rt: Array = d.get("rot_st", [0.0, 0.0, 0.0])
		drz.rotation_degrees = Vector3(float(rt[0]), float(rt[1]), float(rt[2]))
		# kostra kitu muze mit vlastni meritko (glTF): predmet v metrech jako v katalogu
		var sk := kostra.global_transform.basis.get_scale().x / maxf((c["uzel"] as Node3D).scale.x, 1e-3) if kostra.is_inside_tree() else 1.0
		drz.scale = Vector3.ONE / maxf(sk, 1e-4)
		ba.add_child(drz)
		var t: Node3D = ps.instantiate()
		var uc: Array = d.get("uchop", [0.0, 0.0, 0.0])
		t.position = -Vector3(float(uc[0]), float(uc[1]), float(uc[2]))
		drz.add_child(t)
		for g in t.find_children("*", "GeometryInstance3D", true, false):
			(g as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			(g as GeometryInstance3D).visibility_range_end = DOSAH
		drzi[ruka + "_uzel"] = drz
		# uchop podle dat (r. 47, 83): visi / svisle / druha ruka, sevrene prsty - po animaci kazdeho klipu (scripts/uchop.gd)
		if not drzi.has("mod"):
			var um: SkeletonModifier3D = Uchop.new()
			um.name = "uchop"
			um.set("postava", c["uzel"])
			um.set("prsty_st", float(dr.get("_prsty_st", 50.0)))
			kostra.add_child(um)
			drzi["mod"] = um
		(drzi["mod"] as Node).call("nastav", ruka, id, d, drz)


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
		_graf()
	_t += dt
	var pp: Vector3 = main.player.global_position
	var h: float = main.day.hour if main.day != null else 12.0
	var hl: Dictionary = P["hlava"]
	var pr: Dictionary = P["pr"]
	# rozpocet: plnou animaci ma jen plne_max nejblizsich (AC Unity: tvrdy pocet), ostatni po krocich
	# rozpocet mrizky chuze na snimek (dluh z mekkeho prekroceni se prenasi, strop = jeden snimek)
	var mz: Dictionary = P["graf"]["mrizka"]
	var sn := int(mz["sondy_snimek"])
	_nav_sond = mini(maxi(_nav_sond, 0) + sn, sn) if _nav_sond >= 0 else sn
	_nav_cas_us = int(float(mz["cas_ms_snimek"]) * 1000.0)
	_nav_do_us = 0
	_nav_prer = false
	var ceka_n := 0
	var poradi: Array = _lide.map(func(c0: Dictionary) -> float: return Vector2((c0["uzel"] as Node3D).position.x - pp.x, (c0["uzel"] as Node3D).position.z - pp.z).length())
	var serazene := poradi.duplicate()
	serazene.sort()
	var mez_plne: float = serazene[mini(int(pr["plne_max"]), serazene.size()) - 1] if not serazene.is_empty() else 0.0
	for c: Dictionary in _lide:
		var u: Node3D = c["uzel"]
		var d := Vector2(u.position.x - pp.x, u.position.z - pp.z).length()
		var blizko := d < DOSAH + 20.0
		var bi := _blok(c, h)
		if bi != int(c["blok"]):
			# z domu (skryta u dveri) vychazi dvermi - ne objeveni v poli (postavy_plan 1.6)
			var doma := bool((c["cn"] as Dictionary).get("skryty", false)) and bool(c["na_miste"])
			_novy_blok(c, bi, blizko and (u.visible or doma) and u.position != Vector3.ZERO)
		if c.has("ceka"):
			ceka_n += 1
			if blizko and not bool(c.get("ve_fronte", false)):
				c["ve_fronte"] = true
				_nav_fronta.append(c)
		var cn: Dictionary = c["cn"]
		if bool(c["na_miste"]):
			c["na_miste_t"] = float(c["na_miste_t"]) + dt
		# skryje se az chvili po dojiti ke dverim (dvere.cekani_s), ne v pohybu
		var skryty := bool(cn.get("skryty", false)) and bool(c["na_miste"]) and float(c["na_miste_t"]) >= float(P["dvere"]["cekani_s"])
		if bool(cn.get("skryty", false)) and bool(c["na_miste"]):
			skryty = _vstup(c, cn) and skryty
		if bool(c.get("v_posteli", false)):
			skryty = false
		_dvere_zavri_za(c)
		if not blizko or skryty:
			u.visible = false
			continue
		u.visible = true
		var p := Vector2(u.position.x, u.position.z)
		var kh := Vector2(pp.x, pp.z) - p
		var cesta: PackedVector2Array = c["cesta"]
		var jde := not bool(c["na_miste"]) and int(c["i"]) < cesta.size()
		if float(c["vstava"]) > 0.0:
			c["vstava"] = float(c["vstava"]) - dt     # vstava ze sedu, pak teprve jde
		elif c.has("ceka"):
			# cesta se dopocitava (rozpocet snimku): stoji, z chuze do Idle, cinnost na miste beze zmeny
			if float(c["v"]) > 0.0:
				c["v"] = 0.0
				_klip(c, "Idle_Loop", 1.0)
		elif jde:
			var cil := cesta[int(c["i"])]
			var k := cil - p
			# pruchod dvermi (vnitrni misto): dvere otevrit, az je postava u nich
			var dvc: Dictionary = c.get("dvere", {})
			if bool(dvc.get("pruchod", false)) and not bool(dvc.get("hotovo", false)) 					and p.distance_to(((dvc["venku"] as Vector2) + (dvc["vnitrek"] as Vector2)) * 0.5) < float(P["dvere"]["otevrit_m"]):
				_dvere_otevri(c, false)
				dvc["hotovo"] = true
			# hrac v ceste: postava pocka (do uhyb_hrac_m pred ni)
			var ceka := kh.length() < float(P["uhyb"]) and kh.dot(k) > 0.0
			if not ceka:
				ceka = _ceka_za(c, p, k, dt)
			if k.length() < 0.35:
				c["i"] = int(c["i"]) + 1
				if int(c["i"]) >= cesta.size():
					c["na_miste"] = true
					c["obmena"] = 0.0
					c["uvnitr"] = c.get("uvnitr_cil", {})
					if not (c["sedak"] as Dictionary).is_empty() and not cn.has("obchuzka"):
						# usedani: natocit k mistu, Sitting_Enter, pak klipy sedu
						u.rotation.y = float(c["yaw_mista"])
						c["sedi"] = true
						_klip(c, "Sitting_Enter", 1.0)
						c["obmena"] = _delka(c, "Sitting_Enter")
			# rozjezd a brzdeni (RDR2: plynule zrychleni misto prechodovych klipu), otoceni nejvys otaceni_max_st_s
			var v_cil := 0.0 if ceka else float(c["rych"])
			var dv := v_cil - float(c["v"])
			c["v"] = float(c["v"]) + clampf(dv, -float(pr["brzdeni_m_s2"]) * dt, float(pr["zrychleni_m_s2"]) * dt)
			if k.length() > 0.35:
				p += k.normalized() * minf(float(c["v"]) * dt, k.length())
				var dy := wrapf(atan2(k.x, k.y) - u.rotation.y, -PI, PI)
				var om := deg_to_rad(float(pr["otaceni_max_st_s"])) * dt
				u.rotation.y += clampf(dy * minf(1.0, dt * 6.0), -om, om)
			var ch := String(cn.get("chuze", "Walk_Loop"))
			if float(c["v"]) < 0.15:
				_klip(c, "Idle_Loop", 1.0)
			else:
				_klip(c, ch, float(c["v"]) / float(P["klip_m_s"].get(ch, P["klip_m_s"]["Walk_Loop"])))
		else:
			# na miste: cinnost (stridani klipu), natoceni podle mista; obchuzka = dalsi misto po obmene
			if float(c["yaw_mista"]) != INF:
				u.rotation.y = lerp_angle(u.rotation.y, float(c["yaw_mista"]), minf(1.0, dt * 3.0))
			c["obmena"] = float(c["obmena"]) - dt
			if float(c["obmena"]) <= 0.0:
				var ob: Array = cn.get("obmena_s", [5.0, 10.0])
				c["obmena"] = _rng.randf_range(float(ob[0]), float(ob[1]))
				if cn.has("obchuzka") and String(c["klip"]) != "":
					var ok: Array = cn["obchuzka"]
					c["obch"] = (int(c["obch"]) + 1) % ok.size()
					var m: Array = _misto(c, String(ok[int(c["obch"])]))
					m = [_rozestup(c, m[0]), m[1]]
					c["misto"] = m[0]
					c["yaw_mista"] = m[1]
					_pozadej(c, [p, m[0], u.position.y, {}, false])
					c["na_miste"] = false
				else:
					# sed jen na sedaku; bez nej stoji (klipy_bez_sedu)
					var bez := bool(cn.get("sed", false)) and (c["sedak"] as Dictionary).is_empty()
					var kl: Array = cn.get("klipy_bez_sedu" if bez else "klipy", ["Idle_Loop"])
					_klip(c, String(kl[_rng.randi() % kl.size()]), 1.0)
					if not bez and bool(cn.get("sed", false)):
						c["sedi"] = true
		# vyska terenu po 0,25 s (paprsek), plynule
		c["y_t"] = float(c["y_t"]) - dt
		if float(c["y_t"]) <= 0.0:
			c["y_t"] = 0.25
			# paprsek od kolen nahoru (ne z 400 m - trefil strechu mlyna a mlynar chodil po strese, Misa 0.991):
			# prvni podlaha / teren pod postavou z vysky predchozi polohy + schod
			c["y"] = _zem(p, u.position.y)
		# v sedu vyska z sedaku (paprsek by trefil sedak nebo zem pod nim)
		var y: float = float(c["sedak"]["y"]) if bool(c.get("sedi", false)) and not (c["sedak"] as Dictionary).is_empty() else float(c["y"])
		if bool(c.get("v_posteli", false)):
			y = float(c["postel_y"])
		u.position = Vector3(p.x, lerpf(u.position.y, y, minf(1.0, dt * 8.0)) if u.position.y != 0.0 else y, p.y)
		# hlava: na hrace nablizku, jinak vpred
		var ch2: Marker3D = c["cil_hlavy"]
		# vnimani (reserse_reakce_kcd2.md, KCD2 rpg_param): hrace vidi jen v zornem poli (klidna postava vnitrni kuzel),
		# do hned_m kazdy; dohled = zrak role, v noci kratsi. Vsimne si po rozpoznani_s, zapomene za zapomene_s mimo dohled.
		# Pri vsimnuti tabulka reakci (prvni platna) - pozdrav, nevrly, odvraceni, nebo jen pohled (zvedavost x soustredeni).
		var vn: Dictionary = P["vn"]
		var role: Dictionary = c["role"]
		var noc_: bool = main.day != null and main.day.is_night()
		var dohled := minf(float(role.get("zrak_m", 15.0)), float(vn["dohled_strop_m"])) * (float(vn["noc_dohled"]) if noc_ else 1.0)
		var vidi := d < float(vn["hned_m"])
		if not vidi and d < dohled:
			var fw := u.global_transform.basis.z
			var kp := pp - u.global_position
			fw.y = 0.0
			kp.y = 0.0
			vidi = fw.normalized().dot(kp.normalized()) > cos(deg_to_rad(float(vn["zorne_pole_st"]) * float(vn["vnitrni_kuzel"]) * 0.5))
		if vidi:
			c["rozp"] = float(c.get("rozp", 0.0)) + dt
			c["mimo"] = 0.0
		else:
			c["mimo"] = float(c.get("mimo", 0.0)) + dt
			if float(c["mimo"]) > float(vn["zapomene_s"]):
				c["rozp"] = 0.0
				c["vsiml"] = false
				c["na_hrace"] = false
		if vidi and not bool(c.get("vsiml", false)) and (float(c["rozp"]) >= float(vn["rozpoznani_s"]) or d < float(vn["hned_m"])):
			c["vsiml"] = true
			_reakce(c, cn, d)
		c["pohled"] = float(c["pohled"]) - dt
		if bool(c["na_hrace"]) and float(c["pohled"]) <= 0.0:
			c["na_hrace"] = false                    # dost se podival - zpatky k praci
		if bool(c["na_hrace"]) and d < dohled:
			ch2.global_position = main.player.global_position + Vector3(0, 1.6, 0)
		else:
			ch2.global_position = u.global_position + u.global_transform.basis.z.normalized() * float(hl["pohled_vpred_m"]) + Vector3(0, 1.55, 0)
		_bublina_cas(c, dt)
		# stin jen zblizka (pravidla_modelu.json postava stin_m; tablet), prepina se jen pri zmene
		# automaticka kvalita (kvalita.gd krok stiny_predmetu) vypne stin vsem postavam pres meta stin_vyp
		var se_stinem := d < STIN_M and not bool(get_meta("stin_vyp", false))
		if se_stinem != bool(c["stin"]):
			c["stin"] = se_stinem
			for g: GeometryInstance3D in c["geo"]:
				g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if se_stinem else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# hlava a krk sleduji jen do hlava_do_m (dal pohyb hlavy neni videt, LookAt stoji cas)
		var hl_on := d < float(P["hlava_do"])
		for la: SkeletonModifier3D in c.get("hlava_mod", []):
			if la.active != hl_on:
				la.active = hl_on
		if c.has("nohy_ik"):
			var nik_on := d < float(P["nohy_ik"]["do_m"]) and not bool(c.get("v_posteli", false)) and not bool(c.get("sedi", false))
			if (c["nohy_ik"] as SkeletonModifier3D).active != nik_on:
				(c["nohy_ik"] as SkeletonModifier3D).active = nik_on
		if (c["ruce"] as Dictionary).has("mod"):
			(c["ruce"]["mod"] as Node).call("zapni", d < float(P["do"]))
		# LOD animaci: zblizka kazdy snimek (plne_max nejblizsich), do anim_do_m anim_daleko_fps, dal do dosahu
		# anim_dalka_fps - nikdy ztuhla klouzajici poza (plan krok 3.2)
		if d < float(P["plna"]) and d <= mez_plne:
			(c["ap"] as AnimationPlayer).advance(dt)
		else:
			var fps: float = float(P["fps"]) if d < float(P["do"]) else float(P["dalka_fps"])
			c["anim_t"] = float(c["anim_t"]) + dt
			if float(c["anim_t"]) >= 1.0 / fps:
				(c["ap"] as AnimationPlayer).advance(float(c["anim_t"]))
				c["anim_t"] = 0.0
	# fronta cekajicich: kazdy snimek zacina dalsi v poradi, pocita se, dokud staci rozpocet (_nav_prer)
	var kolo := _nav_fronta.size()
	while kolo > 0 and not _nav_fronta.is_empty():
		kolo -= 1
		var cq: Dictionary = _nav_fronta.pop_front()
		cq["ve_fronte"] = false
		if not cq.has("ceka"):
			continue
		if not _dopocitej(cq):
			cq["ve_fronte"] = true
			_nav_fronta.append(cq)
			if _nav_dost(1):
				break
	# nikdo neceka na cestu: pamet hotovych useku a rozpracovanych A* pryc (bunky _nav_kes zustavaji)
	if ceka_n == 0 and not (_nav_hotove.is_empty() and _nav_rozpr.is_empty()):
		_nav_hotove.clear()
		_nav_rozpr.clear()
