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
	"dojem": Pravidla.cti("postavy", "hrac_dojem"), "schod_m": float(Pravidla.cti("hrac", "schod_m")[0])}
var _ves_replika := -1000.0            # cas posledni repliky ve vsi (odstup ves_odstup_s)
var DOSAH: float = P["dosah"]

var main: Node
var _lide: Array = []                  # obyvatel: {id, uzel, kostra, ap, cil_hlavy, role, blok, cesta, i, misto...}
var _t := 0.0
var _sh_hlava: Shader = preload("res://shaders/postava_hlava.gdshader")
var _g := AStar2D.new()                # sit chuze (osy cest sveta)
var _misto_xz := {}                    # id mista -> [Vector2, yaw]
var _rng := RandomNumberGenerator.new()


func setup(p_main: Node) -> void:
	main = p_main
	_rng.seed = 1393
	for o: Dictionary in P["obyvatele"]:
		var mt: Array = _model(bool(o["muz"]), _rng)
		if mt.is_empty():
			continue
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
				"tempo": _rng.randf_range(float(P["pr"]["tempo_klipu"][0]), float(P["pr"]["tempo_klipu"][1]))}
		uzel.scale = Vector3.ONE * _rng.randf_range(0.94, 1.04)
		_hlava(c)
		_klip(c, "Idle_Loop", 1.0)
		ap.seek(_rng.randf(), true)
		uzel.visible = false
		_lide.append(c)
	for cn: Dictionary in P["cinnosti"].values():
		for jm: String in cn.get("klipy", []) + ([cn["chuze"]] if cn.has("chuze") else []):
			if not _lide.is_empty() and not (_lide[0]["ap"] as AnimationPlayer).has_animation(jm):
				push_error("lide: klip %s v knihovne UAL neni" % jm)


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


## Model postavy (Quaternius: hlava z tela superhrdiny, odev, vlasy a vousy na jedne kostre); vrati [uzel, kostra].
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
	for mi in z.find_children("*", "MeshInstance3D", true, false):
		var g := mi as GeometryInstance3D
		g.visibility_range_end = DOSAH
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	return [uzel, kostra]


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
						if int(osa_id[m]) != oi and _g.get_point_position(m).distance_to(q) < spoj:
							_g.connect_points(m, n)
			if not mriz.has(cl):
				mriz[cl] = []
			(mriz[cl] as Array).append(n)
			osa_id[n] = oi
			prev = n
			posl = q
			n += 1
	print("lide: sit chuze %d bodu" % n)


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
	var rz: Array = c["role"]["rozvrh"]
	var bi := rz.size() - 1
	for i in rz.size():
		if h >= float(rz[i]["od"]):
			bi = i
	return bi


func _cesta(a: Vector2, b: Vector2) -> PackedVector2Array:
	if _g.get_point_count() == 0 or a.distance_to(b) < 6.0:
		return PackedVector2Array([b])
	var ia := _g.get_closest_point(a)
	var ib := _g.get_closest_point(b)
	var p := _g.get_point_path(ia, ib)
	var out := PackedVector2Array()
	out.append_array(p)
	out.append(b)
	return out


## Verejne pro test vztahy_hra: cesta postavy mezi dvema misty po siti.
func cesta(a: Vector2, b: Vector2) -> PackedVector2Array:
	return _cesta(a, b)


func _novy_blok(c: Dictionary, bi: int, viditelna: bool) -> void:
	c["blok"] = bi
	var b: Dictionary = c["role"]["rozvrh"][bi]
	var cn: Dictionary = P["cinnosti"][b["cinnost"]]
	var m: Array = _misto(c, String(b["kde"]))
	c["misto"] = m[0]
	c["yaw_mista"] = m[1]
	c["cn"] = cn
	c["obch"] = 0
	var u: Node3D = c["uzel"]
	var p := Vector2(u.position.x, u.position.z)
	if not viditelna or u.position == Vector3.ZERO:
		# LOD AI: mimo dosah rovnou na misto
		u.position = Vector3((m[0] as Vector2).x, 0.0, (m[0] as Vector2).y)
		c["cesta"] = PackedVector2Array()
		c["na_miste"] = true
	else:
		c["cesta"] = _cesta(p, m[0])
		c["i"] = 0
		c["na_miste"] = false
	if not (c["trasa"] as Array).has(m[0]):
		(c["trasa"] as Array).append(m[0])


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
			if String(r["klip"]) != "" and bool(c["na_miste"]):
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
	ap.speed_scale = tempo * float(c.get("tempo", 1.0))


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
			_novy_blok(c, bi, blizko and u.visible)
		var cn: Dictionary = c["cn"]
		var skryty := bool(cn.get("skryty", false)) and bool(c["na_miste"])
		if not blizko or skryty:
			u.visible = false
			continue
		u.visible = true
		var p := Vector2(u.position.x, u.position.z)
		var kh := Vector2(pp.x, pp.z) - p
		var cesta: PackedVector2Array = c["cesta"]
		var jde := not bool(c["na_miste"]) and int(c["i"]) < cesta.size()
		if jde:
			var cil := cesta[int(c["i"])]
			var k := cil - p
			# hrac v ceste: postava pocka (do uhyb_hrac_m pred ni)
			var ceka := kh.length() < float(P["uhyb"]) and kh.dot(k) > 0.0
			if k.length() < 0.35:
				c["i"] = int(c["i"]) + 1
				if int(c["i"]) >= cesta.size():
					c["na_miste"] = true
					c["obmena"] = 0.0
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
					var kl: Array = cn.get("klipy", ["Idle_Loop"])
					_klip(c, String(kl[_rng.randi() % kl.size()]), 1.0)
		# vyska terenu po 0,25 s (paprsek), plynule
		c["y_t"] = float(c["y_t"]) - dt
		if float(c["y_t"]) <= 0.0:
			c["y_t"] = 0.25
			# paprsek od kolen nahoru (ne z 400 m - trefil strechu mlyna a mlynar chodil po strese, Misa 0.991):
			# prvni podlaha / teren pod postavou z vysky predchozi polohy + schod
			c["y"] = _zem(p, u.position.y)
		var y: float = c["y"]
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
		# LOD animaci: zblizka kazdy snimek, dal po krocich anim_daleko_fps, za anim_do poza stoji
		if d < float(P["plna"]) and d <= mez_plne:
			(c["ap"] as AnimationPlayer).advance(dt)
		elif d < float(P["do"]):
			c["anim_t"] = float(c["anim_t"]) + dt
			if float(c["anim_t"]) >= 1.0 / float(P["fps"]):
				(c["ap"] as AnimationPlayer).advance(float(c["anim_t"]))
				c["anim_t"] = 0.0
