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
	"dvere": Pravidla.cti("postavy", "dvere"),
	"spani": Pravidla.cti("postavy", "spani"), "rezim": Pravidla.cti("postavy", "denni_rezim")}
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
var _obsazeno := {}                    # klic mista (sedak, skupina hovoru) -> id obyvatele


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


func _cesta(a: Vector2, b: Vector2) -> PackedVector2Array:
	if _g.get_point_count() == 0 or a.distance_to(b) < 6.0:
		return PackedVector2Array([b])
	# volna primka (nadvori tvrze, dvur): rovnou - sit cest do nadvori nevede a nejblizsi bod site za branou vedl
	# celedina pres zed (Misa 0.992 „zase sel pres zed“)
	if a.distance_to(b) < float(P["graf"]["k_mistu_max_m"]) and _volno(a, b):
		return PackedVector2Array([b])
	var ia := _volny_bod(a)
	var ib := _volny_bod(b)
	var p := _g.get_point_path(ia, ib)
	var out := PackedVector2Array()
	out.append_array(p)
	out.append(b)
	return out


## Bod site chuze, ze ktereho k mistu q vede rovna cesta bez zdi (Misa 0.991: postava chodila skrz zed domu kovarny
## a na strechu zbrojnice - posledni usek od nejblizsiho bodu site k mistu vedl pres stavbu). Kandidati podle vzdalenosti,
## paprsek ve vysce kolen i hlavy; kdyz zadny volny, nejblizsi.
func _volny_bod(q: Vector2) -> int:
	var nej := _g.get_closest_point(q)
	var prostor := get_viewport().get_world_3d().direct_space_state
	var y := float(main.svet.call("_vyska", q.x, q.y))
	var kandidati: Array = []
	for i in _g.get_point_ids():
		var d := _g.get_point_position(i).distance_to(q)
		if d < float(P["graf"]["k_mistu_max_m"]):
			kandidati.append([d, i])
	kandidati.sort()
	for k: Array in kandidati.slice(0, 12):
		var g := _g.get_point_position(int(k[1]))
		var gy := float(main.svet.call("_vyska", g.x, g.y))
		var volno := true
		for h: float in [0.5, 1.6]:
			var r := PhysicsRayQueryParameters3D.create(Vector3(g.x, gy + h, g.y), Vector3(q.x, y + h, q.y))
			if not prostor.intersect_ray(r).is_empty():
				volno = false
				break
		if volno:
			return int(k[1])
	return nej


## Verejne pro test vztahy_hra: cesta postavy mezi dvema misty po siti.
func cesta(a: Vector2, b: Vector2) -> PackedVector2Array:
	return _cesta(a, b)


func _novy_blok(c: Dictionary, bi: int, viditelna: bool) -> void:
	c["blok"] = bi
	var b: Dictionary = c["role"]["rozvrh"][bi]
	var cn: Dictionary = P["cinnosti"][b["cinnost"]]
	_uvolni(c)
	var m: Array = _misto_cinnosti(c, String(b["kde"]), cn)
	c["misto"] = m[0]
	c["yaw_mista"] = m[1]
	c["cn"] = cn
	c["obch"] = 0
	c["obmena"] = 0.0
	c["na_miste_t"] = 0.0
	var u: Node3D = c["uzel"]
	if int(c.get("vchazi", 0)) > 0 and bool(cn.get("skryty", false)) and not (c.get("dvere", {}) as Dictionary).is_empty() 			and (m[0] as Vector2).distance_to(c["dvere"]["venku"]) < 0.5:
		# dalsi skryta cinnost u tychz dveri (jidlo -> spanek): zustava uvnitr
		c["na_miste"] = true
		c["na_miste_t"] = 1000.0
		c["cesta"] = PackedVector2Array()
		c["vchazi"] = 2
		if not bool(c.get("v_posteli", false)):
			_do_postele(c, cn)
		return
	if int(c.get("vchazi", 0)) > 0:
		# rano / po jidle ven: od vnitrku dveri (ne z postele skrz zed), dvere otevrit a za sebou zavrit
		var dv: Dictionary = c.get("dvere", {})
		if not dv.is_empty():
			var vn: Vector2 = dv["vnitrek"]
			u.position = Vector3(vn.x, u.position.y, vn.y)
			_dvere_otevri(c, true)
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
	else:
		c["cesta"] = _cesta(p, m[0])
		c["i"] = 0
		c["na_miste"] = false
	if not (c["trasa"] as Array).has(m[0]):
		(c["trasa"] as Array).append(m[0])


func _delka(c: Dictionary, jm: String) -> float:
	var ap: AnimationPlayer = c["ap"]
	return ap.get_animation(jm).length / maxf(float(c.get("tempo", 1.0)), 0.1) if ap.has_animation(jm) else 0.0


func _uvolni(c: Dictionary) -> void:
	for k: String in _obsazeno.keys():
		if _obsazeno[k] == c["id"]:
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
	if bool(cn.get("sed", false)):
		var sd := _sedak(c, m[0])
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
func _sedak(c: Dictionary, kde: Vector2) -> Dictionary:
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
				# celem od sedaku na stranu mista cinnosti (lom: k praci, u ohniste k ohni)
				var osa_z := Vector2(sin(yaw), cos(yaw))
				var kam := osa_z.dot(_ohen_u(q, kde) - q)
				var smer := osa_z * (signf(kam) if kam != 0.0 else 1.0)
				nej = {"klic": klic, "yaw": atan2(smer.x, smer.y), "y": p0.y + float(rz[1]) - float(sd["vyska_klipu_m"]),
						"stani": q + smer * float(sd["pred_m"]), "sedak": q}
	if not nej.is_empty():
		_obsazeno[nej["klic"]] = c["id"]
	return nej


## Kam se sedici diva: ohniste nebo stul do k_ohni_m od sedaku, jinak misto cinnosti.
func _ohen_u(q: Vector2, kde: Vector2) -> Vector2:
	for r: Dictionary in main.svet.data.get("vybaveni", []):
		var id := String(r["id"])
		if id.begins_with("ohniste") or id.begins_with("stul"):
			var p := Vector2(float(r["p"][0]), float(r["p"][2]))
			if p.distance_to(q) < float(P["sedani"]["k_ohni_m"]):
				return p
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
	u.position = xf * Vector3(float(pz[0]), float(sp["nad_postel_m"]), float(pz[1]))
	u.rotation.y = float(pst["yaw"]) + deg_to_rad(float(sp["otoceni_st"]))
	c["y"] = u.position.y
	c["yaw_mista"] = u.rotation.y
	c["postel_y"] = u.position.y                       # vyska z postele, ne paprskem
	c["v_posteli"] = true
	ruce(c, {})
	_klip(c, String(sp["klip"]), 0.0)
	(c["ap"] as AnimationPlayer).seek(0.0, true)
	c["obmena"] = 1e9


## Postel obyvatele: zaznam spanek {budova, postel} - predmet s lehat z katalogu ve vybaveni sveta uvnitr mistnosti
## budovy (svet data mistnosti <budova>_*, stred, rozmer, yaw). Vrati {p: Vector3, yaw} nebo {} (dira - skryty doma).
func _postel(c: Dictionary) -> Dictionary:
	var sp: Dictionary = (c["o"] as Dictionary).get("spanek", {})
	if String(sp.get("postel", "")) == "" or main == null or main.svet == null:
		return {}
	var kat := katalog()
	for m: Dictionary in main.svet.data.get("mistnosti", []):
		if not String(m["name"]).begins_with(String(sp["budova"]) + "_"):
			continue
		var st := Vector3(float(m["pos"][0]), float(m["pos"][1]), float(m["pos"][2]))
		var inv := Transform3D(Basis(Vector3.UP, float(m.get("yaw", 0.0))), st).affine_inverse()
		for r: Dictionary in main.svet.data.get("vybaveni", []):
			if String(r["id"]) != String(sp["postel"]) or not bool((kat.get(String(r["id"]), {}) as Dictionary).get("lehat", false)):
				continue
			var q := inv * Vector3(float(r["p"][0]), float(r["p"][1]), float(r["p"][2]))
			if absf(q.x) <= float(m["size"][0]) * 0.5 and absf(q.z) <= float(m["size"][2]) * 0.5 and absf(q.y) < 1.5:
				return {"p": Vector3(float(r["p"][0]), float(r["p"][1]), float(r["p"][2])), "yaw": float(r["yaw"])}
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
	var venku := int(c.get("vchazi", 0)) == 0 and Vector2(u.position.x, u.position.z).distance_to(dv["venku"]) > float(P["dvere"]["zavrit_m"])
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
	if String(c["klip"]) != jm:
		ap.play(jm, float(P["blend"]))
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
		elif jde:
			var cil := cesta[int(c["i"])]
			var k := cil - p
			# hrac v ceste: postava pocka (do uhyb_hrac_m pred ni)
			var ceka := kh.length() < float(P["uhyb"]) and kh.dot(k) > 0.0
			if k.length() < 0.35:
				c["i"] = int(c["i"]) + 1
				if int(c["i"]) >= cesta.size():
					c["na_miste"] = true
					c["obmena"] = 0.0
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
				_klip(c, ch, float(c["v"]) / float(P["klip_m_s"].get(ch, 1.2)))
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
					c["cesta"] = _cesta(p, m[0])
					c["i"] = 0
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
		var se_stinem := d < STIN_M
		if se_stinem != bool(c["stin"]):
			c["stin"] = se_stinem
			for g: GeometryInstance3D in c["geo"]:
				g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if se_stinem else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# hlava a krk sleduji jen do hlava_do_m (dal pohyb hlavy neni videt, LookAt stoji cas)
		var hl_on := d < float(P["hlava_do"])
		for la: SkeletonModifier3D in c.get("hlava_mod", []):
			if la.active != hl_on:
				la.active = hl_on
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
