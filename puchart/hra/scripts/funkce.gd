extends Node
## Funkční věci ve stavbách (Míša 15. 11.: „co může mít funkci, tak ji mít bude – vrátka, branky, vrata, dmychadlo v kovárně
## apod.“; spánek „ano, jako Havran“; žlab „nalít vodu“). Data pravidla/svet/funkce.json (zdroj Havran kovarna_mech.gd,
## main.gd bed / offer_sleep / sleep_until, svet.gd _kovarna_dil, _krcma_dil). Věci nejsou záznamy s čísly polohy:
## polozky() je najde ve vložených stavbách (uzly Mista a Ves) podle jmen uzlů modelů:
## - měch kovárny (Kovarna_Paka, Kovarna_Mech, Kovarna_Paka_uchop): „Foukat měchem“ – páka a měch pumpují, výheň se rozhoří (ohne.gd)
## - místa spánku (Hajovna_Spani_Hrac, KrcmaL_Spani_Hrac, pryčny chýší): „Lehnout si“ – lehne si a vybere, do kdy spát (menu_hrace)
## - žlab (Dum2_Kol_Zlab): „Nalít vodu“ – ve žlabu se objeví hladina (shader vody potoků), zůstane
## - jesle nad žlabem (dům najde přes Dum2_Kol_Zlab, tvar z dat): „Nasypat seno“ – v jeslích kupa sena (objem + karty stébel), zůstane
## - kovadlina kovárny (Kovarna_Kovadlina_misto): pevný díl s kolizí a stupni podle vzdálenosti, osadí osad_kovadliny() při startu
## Tlačítko ve stylu dveří (svitek) nad ostatními tlačítky, jen zaměřená věc (zamer.gd) – jako lavice.gd.
const Pravidla := preload("res://scripts/pravidla.gd")
const Zamer := preload("res://scripts/zamer.gd")
var hlavni: Node
var tlacitko: Button
var polozky_: Array = []        # {druh, nazev, pos (bod zaměření), vlastni [RID], …}
var _vrstva: CanvasLayer
var _blizko: Dictionary = {}    # {p: položka, d}
var _mechy: Array = []          # běžící měchy {p, zbyva, cas, faze}
var _zvuk_mech: AudioStream


static func cfg(k: String) -> Dictionary:
	return Pravidla.cti("funkce", k)


## Kořeny vložených staveb (domy, krčma, hájovna pod Mista; kovárna, stodoly pod Ves).
static func _koreny(h: Node) -> Array:
	var out: Array = []
	for jm in ["Mista", "Ves"]:
		var k := h.get_node_or_null(jm)
		if k: out.append(k)
	return out


## AABB kolize těla (StaticBody3D) v souřadnicích uzlu ref (konvexní tvar i kvádr).
static func aabb_kolize(sb: Node, ref: Node3D) -> AABB:
	var ab := AABB(); var prvni := true
	var inv := ref.global_transform.affine_inverse()
	for cs in sb.find_children("*", "CollisionShape3D", true, false):
		var tv: Shape3D = (cs as CollisionShape3D).shape
		var body := PackedVector3Array()
		if tv is BoxShape3D:
			var hs := (tv as BoxShape3D).size * 0.5
			for k in 8: body.append(Vector3(hs.x * (1 if k & 1 else -1), hs.y * (1 if k & 2 else -1), hs.z * (1 if k & 4 else -1)))
		elif tv is ConvexPolygonShape3D: body = (tv as ConvexPolygonShape3D).points
		var t: Transform3D = inv * (cs as CollisionShape3D).global_transform
		for b in body:
			var p := t * b
			if prvni: ab = AABB(p, Vector3.ZERO); prvni = false
			else: ab = ab.expand(p)
	return ab


## Všechny funkční věci ve světě (hra i test průchodu).
static func polozky(h: Node) -> Array:
	var out: Array = []
	var me: Dictionary = cfg("mech")
	for k: Node in _koreny(h):
		for pk in k.find_children(String(me["paka"]), "Node3D", true, false):
			var kor: Node = pk.get_parent()
			var mech := kor.find_child(String(me["mech"]), true, false) as MeshInstance3D
			var uch := kor.find_child(String(me["uchop"]), true, false) as Node3D
			if mech == null or uch == null: continue
			out.append({"druh": "mech", "nazev": String(me["nabidka"]), "pos": uch.global_position, "vlastni": [], "koren": kor,
				"paka": pk, "mech": mech, "zaklad": (pk as Node3D).transform.basis, "tvar": mech.find_blend_shape_by_name(String(me["tvar"]))})
	var sp: Dictionary = cfg("spanek")
	for m: Dictionary in sp["mista"]:
		for k: Node in _koreny(h):
			var znacky: Array = k.find_children(String(m["uzel"]), "Node3D", true, false) if String(m.get("uzel", "")) != "" else []
			if znacky.is_empty() and String(m.get("kolize", "")) != "":   # pryčna jen s kolizí: horní plocha uprostřed
				for sb in k.find_children(String(m["kolize"]), "StaticBody3D", true, false):
					var ab := aabb_kolize(sb, sb.get_parent() as Node3D)
					var zn := sb.get_parent().get_node_or_null("Spani_" + String(sb.name)) as Node3D
					if zn: znacky.append(zn); continue
					zn = Node3D.new(); zn.name = "Spani_" + String(sb.name); (sb.get_parent() as Node3D).add_child(zn)
					zn.position = Vector3(ab.get_center().x, ab.end.y - float(sp["nad_znackou_m"]), ab.get_center().z)
					znacky.append(zn)
			for zn: Node3D in znacky:
				var vl: Array = []
				var inst: Node = zn
				while inst.get_parent() != k: inst = inst.get_parent()   # vložená stavba (dítě Mista / Ves) – kolize lůžka nemusí být sourozenec značky
				var kol: Node = inst.find_child(String(m.get("kolize", "")), true, false) if String(m.get("kolize", "")) != "" else null
				if kol is CollisionObject3D: vl.append((kol as CollisionObject3D).get_rid())
				var p := zn.global_position + Vector3.UP * float(sp["nad_znackou_m"])
				out.append({"druh": "spani", "nazev": String(sp["nabidka"]), "pos": p, "vlastni": vl, "misto": String(m["nazev"]),
					"leh": p - Vector3.UP * float(sp["leh_pod_m"]), "znacka": zn})
	var zl: Dictionary = cfg("zlab")
	for jm in zl["kolize"]:
		for k: Node in _koreny(h):
			for sb in k.find_children(String(jm), "StaticBody3D", true, false):
				var dum := sb.get_parent() as Node3D
				var ab := aabb_kolize(sb, dum)
				out.append({"druh": "zlab", "nazev": String(zl["nabidka"]), "pos": dum.global_transform * Vector3(ab.get_center().x, ab.end.y, ab.get_center().z),
					"vlastni": [(sb as CollisionObject3D).get_rid()], "dum": dum, "aabb": ab, "kolize": String(jm), "voda": null})
	var je: Dictionary = cfg("jesle")
	for jm in je["kolize"]:
		var tv: Dictionary = je["tvar"][jm]
		for k: Node in _koreny(h):
			for sb in k.find_children(String(jm), "StaticBody3D", true, false):
				var dum := sb.get_parent() as Node3D
				var b: Array = tv["bod"]
				out.append({"druh": "jesle", "nazev": String(je["nabidka"]), "pos": dum.global_transform * Vector3(b[0], b[1], b[2]),
					"vlastni": [], "dum": dum, "kolize": String(jm), "seno": null})
	return out


## Kovadlina na značce bod v každé kovárně (funkce.json kovadlina): dítě rodiče značky, počátek modelu na značce, bok dráhy
## (model −Z) natočený ke značce kovar (kovář mezi výhní a kovadlinou); stupně model / _stredni / _daleko přes Visibility Range.
## Vrací vložené uzly (už osazené se přeskočí).
static func osad_kovadliny(h: Node) -> Array:
	var kv: Dictionary = cfg("kovadlina"); var out: Array = []
	var cesty := [String(kv.get("model", "")), String(kv.get("model_stredni", "")), String(kv.get("model_daleko", ""))]
	if cesty[0] == "" or not ResourceLoader.exists(cesty[0]):
		if cesty[0] != "": push_warning("FUNKCE kovadlina: model %s chybí (blender/kovadlina.py)" % cesty[0])
		return out
	var meze := [0.0, float(kv["stredni_od_m"]), float(kv["daleko_od_m"]), float(kv["konec_m"])]
	for k: Node in _koreny(h):
		for zn: Node3D in k.find_children(String(kv["bod"]), "Node3D", true, false):
			var rod := zn.get_parent() as Node3D
			if rod.get_node_or_null(String(kv["uzel"])) != null: continue
			var uz := Node3D.new(); uz.name = String(kv["uzel"]); rod.add_child(uz)
			var kovar := rod.find_child(String(kv.get("kovar", "")), true, false) as Node3D if String(kv.get("kovar", "")) != "" else null
			var yaw := zn.global_rotation.y
			if kovar:
				var smer := kovar.global_position - zn.global_position; smer.y = 0.0
				if smer.length() > 0.05: yaw = atan2(-smer.x, -smer.z)   # model −Z ke kováři
			uz.global_transform = Transform3D(Basis(Vector3.UP, yaw), zn.global_position)
			for i in 3:
				if cesty[i] == "" or not ResourceLoader.exists(cesty[i]): continue
				var sc := (load(cesty[i]) as PackedScene).instantiate()
				sc.name = ["Podrobny", "Stredni", "Daleko"][i]; uz.add_child(sc)
				if i > 0:   # kolize jen z podrobného modelu
					for c in sc.find_children("*", "CollisionObject3D", true, false): c.queue_free()
				var konec: float = meze[i + 1]
				if i < 2 and (cesty[i + 1] == "" or not ResourceLoader.exists(cesty[i + 1])): konec = meze[3]
				for g in sc.find_children("*", "GeometryInstance3D", true, false):
					(g as GeometryInstance3D).visibility_range_begin = meze[i]
					(g as GeometryInstance3D).visibility_range_end = konec
			out.append(uz)
	return out


func zacni(h: Node, vrstva: CanvasLayer) -> void:
	hlavni = h; _vrstva = vrstva
	var kov := osad_kovadliny(h)
	if not kov.is_empty(): print("FUNKCE kovadlina osazena %d×" % kov.size())
	polozky_ = polozky(h)
	var me: Dictionary = cfg("mech")
	if ResourceLoader.exists(String(me["zvuk"])): _zvuk_mech = load(String(me["zvuk"]))
	tlacitko = Button.new(); tlacitko.custom_minimum_size = Vector2(260, 90); Styl.tlacitko_pruh(tlacitko, load("res://fonty/GrenzeGotisch-Medium.ttf"), 30, 3)
	tlacitko.anchor_left = 0.5; tlacitko.anchor_right = 0.5; tlacitko.anchor_top = 1.0; tlacitko.anchor_bottom = 1.0
	tlacitko.offset_left = -170; tlacitko.offset_right = 170; tlacitko.offset_top = -270; tlacitko.offset_bottom = -180
	tlacitko.visible = false; tlacitko.pressed.connect(pouzij)
	vrstva.add_child(tlacitko)
	if vrstva.get("hrac") != null and vrstva.hrac.get("ui") != null: vrstva.hrac.ui.append(tlacitko)
	var poc := {}
	for p: Dictionary in polozky_: poc[p["druh"]] = int(poc.get(p["druh"], 0)) + 1
	print("FUNKCE %s" % poc)


## Zaměřená věc do dosahu (zamer.gd; vlastní kolize věci se přeskočí): {p, d} nebo {}.
static func nejblizsi(pol: Array, cam: Camera3D) -> Dictionary:
	var dosah := float(cfg("nabidka")["dosah_m"]); var out := {}; var best := 1e9
	for p: Dictionary in pol:
		if p["druh"] == "zlab" and p["voda"] != null: continue   # voda už je
		if p["druh"] == "jesle" and p["seno"] != null: continue  # seno už je
		var d := cam.global_position.distance_to(p["pos"])
		var ds := float(cfg("mech")["dosah_m"]) if p["druh"] == "mech" else dosah
		if d >= ds: continue
		var sc := Zamer.skore(cam, p["pos"], ds, p["vlastni"])
		if sc >= 0.0 and sc < best: best = sc; out = {"p": p, "d": d}
	return out


func pouzij() -> void:
	if _blizko.is_empty() or hlavni.hrac == null: return
	pouzij_polozku(_blizko["p"])
	_blizko = {}
	if tlacitko: tlacitko.visible = false


func pouzij_polozku(p: Dictionary) -> void:
	match String(p["druh"]):
		"mech": foukej(p)
		"spani": lehni(p)
		"zlab": nalij(p)
		"jesle": nasyp(p)


## ---------------------------------------------------------------- měch (Havran kovarna_mech.gd pumpuj + main.gd boost výhně)
func foukej(p: Dictionary) -> void:
	for b: Dictionary in _mechy:
		if b["p"] == p: b["zbyva"] = float(cfg("mech")["pumpovat_s"]); return
	_mechy.append({"p": p, "zbyva": float(cfg("mech")["pumpovat_s"]), "cas": 0.0, "faze": 0.0})


func _pumpuj(dt: float) -> void:
	var me: Dictionary = cfg("mech")
	var osa := Vector3(me["osa"][0], me["osa"][1], me["osa"][2]).normalized()
	for b: Dictionary in _mechy.duplicate():
		var p: Dictionary = b["p"]
		b["cas"] = float(b["cas"]) + dt; b["zbyva"] = float(b["zbyva"]) - dt
		var f := float(b["cas"]) * float(me["tempo_rad_s"])
		var t := 0.5 - 0.5 * cos(f)
		var konec := float(b["zbyva"]) <= 0.0 and t < 0.03
		if konec: t = 0.0
		(p["paka"] as Node3D).transform.basis = (p["zaklad"] as Basis) * Basis(osa, float(me["uhel_rad"]) * t)
		if int(p["tvar"]) >= 0: (p["mech"] as MeshInstance3D).set_blend_shape_value(int(p["tvar"]), t)
		# stlačení (t klesá od nadechnutí): výdech do výhně – zvuk a rozhoření
		var zlom := fposmod(f, TAU) >= PI and fposmod(float(b["faze"]), TAU) < PI
		if zlom and not konec:
			var oh: Node = hlavni.get_node_or_null("Ohne")
			if oh and oh.has_method("rozdmychej"): oh.rozdmychej(p["koren"], me["rozhoreni"])
			if _zvuk_mech:
				var a := AudioStreamPlayer3D.new(); a.stream = _zvuk_mech; a.volume_db = float(me["zvuk_db"]); a.max_distance = 25.0
				(p["mech"] as Node3D).add_child(a); a.play(); a.finished.connect(a.queue_free)
		b["faze"] = f
		if konec: _mechy.erase(b)


func mech_bezi(p: Dictionary) -> bool:
	for b: Dictionary in _mechy:
		if b["p"] == p: return true
	return false


## ---------------------------------------------------------------- spánek (Havran main.gd bed → offer_sleep, sleep_until)
func lehni(p: Dictionary) -> void:
	var sp: Dictionary = cfg("spanek"); var h: CharacterBody3D = hlavni.hrac
	h.sit(p["leh"], float(sp["oci_m"]), h.global_position, h.yaw, deg_to_rad(float(sp["pohled_nahoru_st"])))
	var hv: Node = _vrstva.get("hv") if _vrstva else null
	if hv and hv.has_method("offer_sleep"): hv.offer_sleep()


## Přespat do doby kdy (den.gd klíč: rano, poledne, odpoledne, soumrak, noc): zatmění, posun času, vstát, rozednění
## (Havran sleep_until: hud.fade_through, day.set_time, player.stand_up, uložení). ulozit = Callable uložení hry.
func spi_do(kdy: String, ulozit := Callable()) -> void:
	var sp: Dictionary = cfg("spanek")
	var cl := CanvasLayer.new(); cl.layer = 30; cl.process_mode = Node.PROCESS_MODE_ALWAYS
	var fade := ColorRect.new(); fade.color = Color(0, 0, 0, 0); fade.set_anchors_preset(Control.PRESET_FULL_RECT); fade.mouse_filter = Control.MOUSE_FILTER_STOP
	cl.add_child(fade); add_child(cl)
	var tw := create_tween(); tw.tween_property(fade, "color:a", 1.0, float(sp["zatmeni_s"])); await tw.finished
	var den: Node = hlavni.get("den")
	if den and kdy != "": den.set_time(kdy, 0.01)
	var h: CharacterBody3D = hlavni.hrac
	if h and h.seated: h.stand_up()
	if ulozit.is_valid(): ulozit.call()
	await get_tree().create_timer(float(sp["tma_s"])).timeout
	var tw2 := create_tween(); tw2.tween_property(fade, "color:a", 0.0, float(sp["rozednit_s"])); await tw2.finished
	cl.queue_free()


## ---------------------------------------------------------------- žlab (hladina vody ve tvaru kolize žlabu)
func nalij(p: Dictionary) -> void:
	if p["voda"] != null: return
	var zl: Dictionary = cfg("zlab")
	var q: Array = zl["hladina"][p["kolize"]]   # [x0, x1, y, z0, z1] modelu – vnitřek koryta
	var x0 := float(q[0]); var x1 := float(q[1]); var y := float(q[2]); var z0 := float(q[3]); var z1 := float(q[4])
	# rovina: UV.x = metry podél (vlny), UV.y = 1 − hloubka (shader voda.gdshader: h = 1 − UV.y), barva vrcholu bílá (kraj 1);
	# pořadí vrcholů jako Sit.quad (Godot: přední strana po směru hodinových ručiček – normála nahoru)
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var v := [Vector3(x0, y, z0), Vector3(x1, y, z0), Vector3(x1, y, z1), Vector3(x0, y, z1)]
	var uvy := 1.0 - float(zl["hloubka_m"])
	for i in [0, 1, 2, 0, 2, 3]:
		st.set_color(Color(1, 1, 1, 1)); st.set_normal(Vector3.UP); st.set_uv(Vector2((v[i] as Vector3).x - x0, uvy)); st.add_vertex(v[i])
	var mi := MeshInstance3D.new(); mi.name = "VodaZlab"; mi.mesh = st.commit()
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mv = hlavni.get("mat_voda")
	if mv is ShaderMaterial:
		var m2 := (mv as ShaderMaterial).duplicate() as ShaderMaterial; mi.material_override = m2
		for k: String in zl["shader"]: m2.set_shader_parameter(k, float(zl["shader"][k]))   # stojatá zakalená voda v korytě
	(p["dum"] as Node3D).add_child(mi)
	p["voda"] = mi


## ---------------------------------------------------------------- jesle (kupa sena: objem po profilu jeslí + karty stébel)
## Profil kupy v rovině (y, z) modelu domu pro parametr s 0..1: čelo za příčkami odspodu nahoru (s 0..0,5), pak vrch kupy
## od horního břevna k roubení (s 0,5..1). Výška vrchu = kupa_m × tvar oblouku × útlum u čel × (1 + šum); čelo i vrch
## posune šum podél normály profilu. Vrací [bod, normála profilu (bez šumu)].
static func _jesle_bod(tv: Dictionary, x: float, s: float, sum: FastNoiseLite) -> Array:
	var d: Array = tv["pricky_dole"]; var n: Array = tv["pricky_nahore"]
	var x0 := float(tv["x"][0]); var x1 := float(tv["x"][1])
	var kraj := clampf(minf(x - x0, x1 - x) / 0.25, 0.0, 1.0); kraj = kraj * kraj * (3.0 - 2.0 * kraj)   # útlum kupy k čelům jeslí (0,25 m)
	var pricka := Vector2(float(n[0]) - float(d[0]), float(n[1]) - float(d[1]))   # (dy, dz) osy příček
	var ven := Vector2(-pricka.y, pricka.x).normalized()                       # normála čela (do chléva: +z, dolů)
	if ven.y < 0.0: ven = -ven
	var pred := float(tv["pred_prickami_m"])
	var p: Vector2; var nrm: Vector2
	if s <= 0.5:
		var t := s / 0.5
		p = Vector2(float(d[0]), float(d[1])) + pricka * t - ven * pred; nrm = ven
	else:
		var t := (s - 0.5) / 0.5   # 0 u horního břevna → 1 u roubení
		var top := Vector2(float(n[0]), float(n[1])) - ven * pred
		var z := lerpf(top.y + float(tv["kupa_ven_m"]) * sin(t * PI) * 0.6, float(tv["stena_z"]), t)
		var oblouk := sin(pow(t, 0.5) * PI) * 0.85 + t * 0.35   # vrchol blíž čelu (kupa hned za břevnem vysoko), u roubení opřená výš
		p = Vector2(top.x + float(tv["kupa_m"]) * oblouk * (0.7 + 0.3 * kraj), z)   # u čel jen mírně nižší – placka M_Slama u krajních příček sahá do y 2,05
		nrm = Vector2(1.0, (0.5 - t) * 1.2).normalized()
	var a := float(tv["sum_m"]) * sum.get_noise_2d(x, s * 3.0) * (0.4 + 0.6 * kraj)
	return [Vector3(x, p.x + nrm.x * a, p.y + nrm.y * a), Vector3(0.0, nrm.x, nrm.y)]


## Síť kupy sena v souřadnicích modelu domu: [ArrayMesh objem, ArrayMesh stébla] (bez materiálu).
static func jesle_site(tv: Dictionary, je: Dictionary) -> Array:
	var si: Dictionary = je["sit"]; var stc: Dictionary = je["stebla"]
	var sum := FastNoiseLite.new(); sum.seed = int(stc["seed"]); sum.frequency = 1.0 / float(tv["sum_vlna_m"])
	var x0 := float(tv["x"][0]); var x1 := float(tv["x"][1])
	var nx := maxi(2, int(ceil((x1 - x0) / float(si["delka_krok_m"])))); var ns := int(si["profil_bodu"])
	var mrz: Array = []
	for i in nx + 1:
		var rad: Array = []
		for j in ns + 1: rad.append(_jesle_bod(tv, lerpf(x0, x1, float(i) / nx), float(j) / ns, sum)[0])
		mrz.append(rad)
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var uvm := float(si["uv_m"]); var ao_dole := float(stc["ao_cela_dole"])
	var delky: Array = [0.0]
	for j in ns: delky.append(float(delky[j]) + (mrz[0][j] as Vector3).distance_to(mrz[0][j + 1]))
	for i in nx:
		for j in ns:
			var q := [[i, j], [i + 1, j + 1], [i + 1, j], [i, j], [i, j + 1], [i + 1, j + 1]]   # po směru hodinových ručiček zvenku (přední strana Godotu)
			for ij: Array in q:
				var v: Vector3 = mrz[ij[0]][ij[1]]
				var s := float(ij[1]) / ns
				st.set_color(Color.WHITE * lerpf(ao_dole, 1.0, smoothstep(0.0, 0.55, s)))   # spodek čela ve stínu koše
				# vlákna textury natočená podle šumu (pomalé víření) – jinak „učesaná“ jedním směrem jako došek (snímek 15. 11.)
				var uv := Vector2(v.x / uvm, float(delky[ij[1]]) / uvm)
				st.set_uv(uv.rotated(sum.get_noise_2d(v.x * 0.3 + 40.0, (v.y + v.z) * 0.3) * PI * float(si["viri"]))); st.add_vertex(v)
	st.generate_normals(); st.generate_tangents()
	var objem := st.commit()
	# --- karty stébel (2. kolo): spleť = ležící karty po povrchu ve vrstvách (krok po povrchu v parametrech x, s – karta
	# sleduje zakřivení kupy), trsy = krátké trčící karty; buňky atlasu sloupce × řady (pata karty dole v buňce)
	var rnd := RandomNumberGenerator.new(); rnd.seed = int(stc["seed"])
	var ks := SurfaceTool.new(); ks.begin(Mesh.PRIMITIVE_TRIANGLES)
	var at: Dictionary = stc["atlas"]; var nc := int(at["sloupce"]); var nr := int(at["rady"])
	var lprof := float(delky[ns])
	var vr: Dictionary = stc["vrstva"]; var tr: Dictionary = stc["trsy"]
	var pocty := [int(vr["pocet"]), int(tr["pocet"])]
	for druh in 2:
		var d: Dictionary = vr if druh == 0 else tr
		var rada := int(at["rada_vrstva"] if druh == 0 else at["rada_trsy"])
		for c in pocty[druh]:
			var x := rnd.randf_range(x0 + 0.02, x1 - 0.02)
			var s := pow(rnd.randf(), 0.8) * 0.5 + 0.5 if rnd.randf() < float(d["vrch_podil"]) else rnd.randf_range(0.03, 0.5)   # víc na vrchu (je vidět)
			var L := rnd.randf_range(float(d["delka_m"][0]), float(d["delka_m"][1]))
			var w := L * float(d["pomer"]) * rnd.randf_range(0.85, 1.2)
			var bu := rnd.randi() % nc
			var u0 := float(bu) / nc; var u1 := float(bu + 1) / nc
			var v0 := float(rada) / nr; var v1 := float(rada + 1) / nr
			var ton := rnd.randf_range(0.9, 1.08)
			var radky: Array = []   # [bod, v, jas]
			var bok := Vector3.ZERO; var nn := Vector3.UP
			if druh == 0:
				# vrstvy nad tmavým jádrem (objem): výška nad povrchem zanor_m … vrstva_m, spodní vrstvy tmavší; karta leží v tečné
				# rovině, směr náhodný
				var hl := pow(rnd.randf(), 0.7)
				var pod := -(float(d["vrstva_m"]) * (1.0 - hl) + float(d["zanor_m"]))
				var jas := lerpf(1.0, float(d["ao_spodni"]), hl)
				var az := rnd.randf() * TAU
				for k in 3:
					var t := (float(k) - 1.0) * 0.5   # −0,5 … 0,5 délky (střed karty na bodě)
					var xk := clampf(x + cos(az) * L * t, x0, x1); var sk := clampf(s + sin(az) * L * t / lprof, 0.0, 1.0)
					var bn: Array = _jesle_bod(tv, xk, sk, sum)
					var e := 0.004
					var n2: Vector3 = ((_jesle_bod(tv, xk + e, sk, sum)[0] as Vector3) - (_jesle_bod(tv, xk - e, sk, sum)[0] as Vector3)).cross(
						(_jesle_bod(tv, xk, minf(sk + e, 1.0), sum)[0] as Vector3) - (_jesle_bod(tv, xk, maxf(sk - e, 0.0), sum)[0] as Vector3))
					n2 = n2.normalized() if n2.length() > 1e-6 else (bn[1] as Vector3)
					if n2.dot(bn[1]) < 0.0: n2 = -n2
					if k == 1: nn = n2
					radky.append([(bn[0] as Vector3) - n2 * pod + n2 * rnd.randf_range(-0.004, 0.004), v1 - (v1 - v0) * (float(k) * 0.5), jas])
				var tang := ((radky[2][0] as Vector3) - (radky[0][0] as Vector3))
				bok = tang.cross(nn).normalized() if tang.length() > 1e-5 else nn.cross(Vector3.RIGHT).normalized()
			else:
				var bn: Array = _jesle_bod(tv, x, s, sum)
				nn = bn[1]
				var t1 := nn.cross(Vector3.UP if absf(nn.y) < 0.9 else Vector3.RIGHT).normalized(); var t2 := nn.cross(t1)
				var az := rnd.randf() * TAU
				var sklon := deg_to_rad(rnd.randf_range(float(d["sklon_st"][0]), float(d["sklon_st"][1])))
				var smer := (nn * cos(sklon) + (t1 * cos(az) + t2 * sin(az)) * sin(sklon)).normalized()
				var pata := (bn[0] as Vector3) - nn * float(d["zanor_m"])
				var ao_p := float(d["ao_pata"])
				radky = [[pata, v1, ao_p], [pata + smer * L * 0.5 + Vector3.DOWN * L * float(d["previs_m"]) * 0.3, (v0 + v1) * 0.5, lerpf(ao_p, 1.0, 0.6)],
					[pata + smer * L + Vector3.DOWN * L * float(d["previs_m"]), v0, 1.0]]
				bok = smer.cross(nn).normalized()
				if bok.length() < 0.5: bok = t1
				bok = bok.rotated(smer, rnd.randf_range(-PI * 0.5, PI * 0.5))
			if druh == 0: radky = [radky[0], radky[2]]   # ležící karta = jeden čtyřúhelník (konce na povrchu), rozpočet na víc karet
			for r in radky.size() - 1:
				var a: Array = radky[r]; var bb: Array = radky[r + 1]
				var wa := w * (1.0 if druh == 0 or r == 0 else 0.85); var wb := w * (1.0 if druh == 0 else (0.85 if r == 0 else 0.7))
				var v4 := [[a[0] - bok * wa * 0.5, u0, a[1], a[2]], [a[0] + bok * wa * 0.5, u1, a[1], a[2]],
					[bb[0] + bok * wb * 0.5, u1, bb[1], bb[2]], [bb[0] - bok * wb * 0.5, u0, bb[1], bb[2]]]
				for k in [0, 1, 2, 0, 2, 3]:
					var q4: Array = v4[k]
					ks.set_color(Color.WHITE * float(q4[3]) * ton); ks.set_normal(nn); ks.set_uv(Vector2(float(q4[1]), float(q4[2])))
					ks.add_vertex(q4[0])
	return [objem, ks.commit()]


func nasyp(p: Dictionary) -> void:
	if p["seno"] != null: return
	var je: Dictionary = cfg("jesle")
	var site := jesle_site(je["tvar"][p["kolize"]], je)
	var uz := Node3D.new(); uz.name = "SenoJesle"
	var vid: Dictionary = je["viditelnost_m"]
	for i in 2:
		var mi := MeshInstance3D.new(); mi.name = ["Objem", "Stebla"][i]; mi.mesh = site[i]
		mi.material_override = load(String(je["material"] if i == 0 else je["material_stebla"]))
		mi.visibility_range_end = float(vid["objem"] if i == 0 else vid["stebla"])
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if i == 0 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		uz.add_child(mi)
	(p["dum"] as Node3D).add_child(uz)
	p["seno"] = uz


func _process(dt: float) -> void:
	if not _mechy.is_empty(): _pumpuj(dt)
	if tlacitko == null or hlavni.hrac == null: return
	if Engine.get_process_frames() % 6 != 0: return
	var h: CharacterBody3D = hlavni.hrac
	_blizko = {} if (h.seated or h.leze or h.leti) else nejblizsi(polozky_, h.cam)
	tlacitko.visible = not _blizko.is_empty()
	if not tlacitko.visible: return
	tlacitko.text = String(_blizko["p"]["nazev"])
	var nad := -180.0; var posun := true   # nepřekrýt jiné viditelné tlačítko dole uprostřed (dveře, žebřík, lavice, oheň)
	while posun:
		posun = false
		for b in _vrstva.get_children():
			if b == tlacitko or not (b is Button) or not (b as Button).visible or (b as Button).anchor_top != 1.0 or (b as Button).anchor_left != 0.5: continue
			if (b as Button).offset_top < nad and (b as Button).offset_bottom > nad - 90.0:
				nad = (b as Button).offset_top - 2.0; posun = true
	tlacitko.offset_bottom = nad; tlacitko.offset_top = nad - 90.0
