extends Node
## Funkční věci ve stavbách (Míša 15. 11.: „co může mít funkci, tak ji mít bude – vrátka, branky, vrata, dmychadlo v kovárně
## apod.“; spánek „ano, jako Havran“; žlab „nalít vodu“). Data pravidla/svet/funkce.json (zdroj Havran kovarna_mech.gd,
## main.gd bed / offer_sleep / sleep_until, svet.gd _kovarna_dil, _krcma_dil). Věci nejsou záznamy s čísly polohy:
## polozky() je najde ve vložených stavbách (uzly Mista a Ves) podle jmen uzlů modelů:
## - měch kovárny (Kovarna_Paka, Kovarna_Mech, Kovarna_Paka_uchop): „Foukat měchem“ – páka a měch pumpují, výheň se rozhoří (ohne.gd)
## - místa spánku (Hajovna_Spani_Hrac, KrcmaL_Spani_Hrac, pryčny chýší): „Lehnout si“ – lehne si a vybere, do kdy spát (menu_hrace)
## - žlab (Dum2_Kol_Zlab): „Nalít vodu“ – ve žlabu se objeví hladina (shader vody potoků), zůstane
## - jesle nad žlabem (dům najde přes Dum2_Kol_Zlab, osazení z dat): „Nasypat seno“ – v jeslích model sena (Seno_Jesle_420), zůstane
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


## ---------------------------------------------------------------- jesle (model sena Míšina modeláře, funkce.json jesle)
## Transformace modelu sena v souřadnicích modelu domu (osazeni[kolize]: poloha, sklon kolem x, měřítko).
static func jesle_xf(je: Dictionary, kolize: String) -> Transform3D:
	var o: Dictionary = je["osazeni"][kolize]
	var m: Array = o["meritko"]; var po: Array = o["poloha"]
	var b := Basis(Vector3.RIGHT, deg_to_rad(float(o["natoceni_x_st"]))) * Basis.from_scale(Vector3(float(m[0]), float(m[1]), float(m[2])))
	return Transform3D(b, Vector3(float(po[0]), float(po[1]), float(po[2])))


func nasyp(p: Dictionary) -> void:
	if p["seno"] != null: return
	var je: Dictionary = cfg("jesle")
	if not ResourceLoader.exists(String(je["model"])): push_warning("FUNKCE jesle: model %s chybí (nastroje/seno_modely.py)" % je["model"]); return
	var uz := (load(String(je["model"])) as PackedScene).instantiate() as Node3D
	uz.name = "SenoJesle"; uz.transform = jesle_xf(je, String(p["kolize"]))
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
