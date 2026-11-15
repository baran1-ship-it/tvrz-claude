extends Node3D
## Ohně ve stavbách (Míša 15. 11.: „dodělej ohně – v Havranovi jsou a jdou zapnout a vypnout, ale moc se mi nelíbí jejich
## vzhled“; „nešlo by, aby zdálky byla místnost osvětlená a zblízka to bylo funkční?“). Data hra/data/ohne.json
## (pravidla/svet/ohne.json – zdroj Havran life.gd _build_fires / _light a jeho měření).
## - místa ze značek modelů (KrcmaL_Ohen_Kuchyne, Hajovna_Ohen_Sin, Kovarna_Ohen_bod) a z kolizí pecí (*_Kol_Pec): ohniště =
##   plamen na vršku ohniště (paprsek dolů), pec = plamen v ústí (strana pece ke směru nejdelšího volného paprsku = do místnosti),
##   výheň = plamen nad sítí žáru (Kovarna_Zhar dostane žhnoucí překryv)
## - plamen = 3 křížené karty se shaderem shaders/ohen.gdshader (tvar a barva ve shaderu, CPU nic nesimuluje), kreslí se do
##   plamen_do_m; uhlíky = disk se stejným shaderem
## - světlo OmniLight3D NIKDY se stínem (Havran: stín ohně p95 78 ms), útlum pod 1 → místnost čitelná i ode dveří; zapnutá
##   jen nejbližší svetel_max s hysterezí zap_m / vyp_m, blikání siny + pomalý šum + chvění polohy
## - nabídka Zapálit / Uhasit oheň jako dveře a žebříky (tlačítko svitku, zamer.gd); pece domů a kamna hradu hoří večer a v noci,
##   kuchyně hradu v hodinách vaření (hori casy + hodiny; den.gd); značky hradu se hledají pod kořenem m.koren ("Hrad")
const Zamer := preload("res://scripts/zamer.gd")

var hlavni: Node
var cfg: Dictionary = {}
var ohne: Array = []          # [{nazev, druh, zaklad, svetlo, plamen, uhliky, zhar, zvuk, hori, noc, rucne, vlastni, energie, poloha, faze, sum, sum_cil, sum_t}]
signal hotovo
var pripraveno := false
var tlacitko: Button
var _blizko := -1             # index ohně, na který hráč míří (nabídka)
var _mat_plamen: ShaderMaterial
var _mat_uhliky: ShaderMaterial
var _site := {}               # druh -> ArrayMesh plamene
var _disk := {}               # poloměr -> mesh disku uhlíků
var _t_kontrola := 0.0
var _t_noc := 0.0
var _zvuk_stream: AudioStream


func zacni(h: Node) -> void:
	hlavni = h
	if not FileAccess.file_exists("res://data/ohne.json"): pripraveno = true; hotovo.emit(); return
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/ohne.json"))
	print("DBG ohne ceka ", h.get("kolize_hotove"))
	if h.get("kolize_hotove") == false: await h.kolize_hotovo
	print("DBG ohne kolize ok")   # kolize hradu (hlavni.gd _kolize_hradu deferred až po předehrání – dřív paprsky v hradu nic nenašly)
	for i in 3: await get_tree().physics_frame   # kolize staveb (paprsky na ohniště a do místnosti)
	_materialy()
	var zv: Dictionary = cfg["zvuk"]
	if ResourceLoader.exists(String(zv["soubor"])):
		_zvuk_stream = load(String(zv["soubor"]))
		if _zvuk_stream is AudioStreamOggVorbis: (_zvuk_stream as AudioStreamOggVorbis).loop = true
	for m: Dictionary in cfg["mista"]:
		var koreny: Array = []
		for jm in ([m["koren"]] if m.has("koren") else ["Mista", "Ves"]):   # koren = uzel modelu (hrad A: "Hrad"), jinak stavby vsi
			var k := h.get_node_or_null(String(jm))
			if k: koreny.append(k)
		for k: Node in koreny:
			for n in k.find_children(String(m.get("uzel", m.get("pec_kolize", ""))), "", true, false):
				_pridej(m, n as Node3D)
	pripraveno = true
	_noc(true)
	_rozpocet()
	hotovo.emit()
	print("OHNE %d (svetel zapnuto %d)" % [ohne.size(), pocet_svetel()])


func _materialy() -> void:
	var p: Dictionary = cfg["plamen"]; var u: Dictionary = cfg["uhliky"]
	var sh: Shader = load("res://shaders/ohen.gdshader"); var tx: Texture2D = load("res://textury/ohen_sum.png")
	_mat_plamen = ShaderMaterial.new(); _mat_plamen.shader = sh
	_mat_plamen.set_shader_parameter("sum_tex", tx); _mat_plamen.set_shader_parameter("rezim", 0)
	for k in ["rychlost", "vlneni", "eroze"]: _mat_plamen.set_shader_parameter(k, float(p[k]))
	for k in ["barva_jadro", "barva_zluta", "barva_oranz", "barva_cervena"]:
		var c: Array = p[k]; _mat_plamen.set_shader_parameter(k, Color(c[0], c[1], c[2]))
	_mat_uhliky = _mat_plamen.duplicate() as ShaderMaterial; _mat_uhliky.set_shader_parameter("rezim", 1)
	_mat_uhliky.set_shader_parameter("uhliky_meritko", float(u["meritko"])); _mat_uhliky.set_shader_parameter("uhliky_pulz", float(u["pulz"]))


## Síť plamene: karet svislých karet křížených kolem osy y, základna v 0, UV.y 0 dole → 1 nahoře, barva vrcholu R = fáze karty.
func _sit_plamene(sirka: float, vyska: float) -> ArrayMesh:
	var n := int(cfg["plamen"]["karet"])
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in n:
		var a := PI * float(i) / float(n); var d := Vector3(cos(a), 0, sin(a)) * sirka * 0.5; var nr := Vector3(-sin(a), 0, cos(a))
		var faze := fposmod(float(i) * 0.618, 1.0)
		var v := [[-d, Vector2(0, 0)], [d, Vector2(1, 0)], [d + Vector3(0, vyska, 0), Vector2(1, 1)], [-d + Vector3(0, vyska, 0), Vector2(0, 1)]]
		for k in [0, 1, 2, 0, 2, 3]:
			st.set_color(Color(faze, 0, 0)); st.set_normal(nr); st.set_uv(v[k][1]); st.add_vertex(v[k][0])
	return st.commit()


func _sit_disku(r: float) -> ArrayMesh:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var v := [Vector3(-r, 0, -r), Vector3(r, 0, -r), Vector3(r, 0, r), Vector3(-r, 0, r)]
	var uv := [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]
	for k in [0, 1, 2, 0, 2, 3]:
		st.set_color(Color(0, 0, 0)); st.set_normal(Vector3.UP); st.set_uv(uv[k]); st.add_vertex(v[k])
	return st.commit()


## Směr (vodorovně) s nejdelším volným paprskem z bodu – do místnosti; vyjma = RID vlastní kolize (pec).
func _do_mistnosti(p: Vector3, vyjma: Array) -> Vector3:
	var ss := get_world_3d().direct_space_state; var nej := Vector3.FORWARD; var nd := -1.0
	for k in 16:
		var sm := Vector3(cos(k * TAU / 16.0), 0, sin(k * TAU / 16.0))
		var q := PhysicsRayQueryParameters3D.create(p, p + sm * 8.0); q.exclude = vyjma
		var r := ss.intersect_ray(q)
		var d := 8.0 if r.is_empty() else p.distance_to(r["position"])
		if d > nd: nd = d; nej = sm
	return nej


func _pridej(m: Dictionary, n: Node3D) -> void:
	var dr: Dictionary = cfg["druhy"][String(m["druh"])]
	var ss := get_world_3d().direct_space_state
	var vlastni: Array = []
	var zaklad: Vector3; var ven: Vector3
	var zhar: MeshInstance3D = null
	if m.has("pec_kolize"):   # pec: ústí na straně do místnosti, výška usti_v nad spodkem pece
		var tel := n if m.has("uzel") == false else n.get_parent().get_parent().find_child(String(m["pec_kolize"]), true, false) as Node3D
		if not tel is CollisionObject3D: return
		vlastni = [(tel as CollisionObject3D).get_rid()]
		var ab := AABB(); var prvni := true
		for cs in tel.find_children("*", "CollisionShape3D", true, false):
			var b := (cs as CollisionShape3D).global_transform * (cs as CollisionShape3D).shape.get_debug_mesh().get_aabb()
			ab = b if prvni else ab.merge(b); prvni = false
		if prvni: return
		var c := ab.get_center()
		ven = _do_mistnosti(c, vlastni)
		# ústí: na líci klenby pece (kolize je jeden kvádr pece i s podstavcem – klenba končí na usti_od_stredu půlrozměru)
		var lic := c + ven * minf(ab.size.x, ab.size.z) * 0.5 * float(dr["usti_od_stredu"])
		zaklad = Vector3(lic.x, ab.position.y + ab.size.y * float(dr["usti_v"]), lic.z)
	else:
		var p := n.global_position
		if m.has("zhar"):
			zhar = n.get_parent().find_child(String(m["zhar"]), false, false) as MeshInstance3D
		if zhar:
			var ab := zhar.global_transform * zhar.get_aabb()
			zaklad = Vector3(ab.get_center().x, ab.end.y - 0.02, ab.get_center().z)
		else:
			var r := ss.intersect_ray(PhysicsRayQueryParameters3D.create(p + Vector3.UP * 0.1, p - Vector3.UP * 1.5))
			zaklad = (r["position"] as Vector3) if not r.is_empty() else p
			# vlastní kolize ohniště (zaměření a paprsky do místnosti ji přeskočí) – ne u modelu s jednou kolizí celku (hrad: KOLIZE_col
			# = celý hrad; jejím vynecháním by paprsky prošly zdmi a nabídka by šla i přes zeď)
			if not r.is_empty() and not m.has("koren"): vlastni = [(r["collider"] as CollisionObject3D).get_rid()]
		ven = _do_mistnosti(zaklad + Vector3.UP * 0.5, vlastni)
	var o := {"nazev": String(m["nazev"]), "druh": String(m["druh"]), "zaklad": zaklad, "vlastni": vlastni, "uzel": n, "boost": 0.0, "boost_cfg": {},
		"hori": String(m["hori"]) == "vzdy", "noc": String(m["hori"]) == "noc", "casy": m.get("hodiny", []) if String(m["hori"]) == "casy" else [],
		"rucne": false, "zap": false,
		"faze": randf() * 50.0, "sum": 0.0, "sum_cil": 0.0, "sum_t": 0.0, "energie": float(dr["energie"])}
	var uz := Node3D.new(); uz.name = "Ohen_%d" % ohne.size(); add_child(uz); uz.global_position = zaklad
	var ps: Array = dr["plamen"]; var kl := "%s" % m["druh"]
	if float(ps[1]) > 0.0:   # pec: ústí je v kuchyni / síni (pec se topí zvenku jizby) – jen světlo a zvuk
		if not _site.has(kl): _site[kl] = _sit_plamene(float(ps[0]), float(ps[1]))
		var pl := MeshInstance3D.new(); pl.name = "Plamen"; pl.mesh = _site[kl]; pl.material_override = _mat_plamen
		_geom(pl); pl.rotation.y = randf() * PI; uz.add_child(pl); o["plamen"] = pl
	if float(dr["uhliky_r"]) > 0.0:
		var r_ := float(dr["uhliky_r"])
		if not _disk.has(r_): _disk[r_] = _sit_disku(r_)
		var uh := MeshInstance3D.new(); uh.name = "Uhliky"; uh.mesh = _disk[r_]; uh.material_override = _mat_uhliky
		_geom(uh); uh.position.y = 0.015; uz.add_child(uh); o["uhliky"] = uh
	if zhar:   # žár výhně: překryv sítě modelu (druhý průchod se stejným shaderem)
		zhar.material_overlay = _mat_uhliky; o["zhar"] = zhar
	var l := OmniLight3D.new(); l.name = "Svetlo"
	var sv: Dictionary = cfg["svetlo"]; var bc: Array = sv["barva"]
	l.light_color = Color(bc[0], bc[1], bc[2]); l.light_energy = o["energie"]; l.omni_range = float(dr["dosah_m"])
	l.omni_attenuation = float(sv["utlum"]); l.light_specular = float(sv["specular"]); l.shadow_enabled = false
	l.visible = false; add_child(l)
	o["poloha"] = zaklad + Vector3.UP * float(dr["svetlo_v"]) + ven * float(dr["svetlo_ven"]); l.global_position = o["poloha"]
	o["svetlo"] = l
	if _zvuk_stream:
		var zv: Dictionary = cfg["zvuk"]; var a := AudioStreamPlayer3D.new(); a.name = "Zvuk"; a.stream = _zvuk_stream
		a.volume_db = float(zv["db"]); a.unit_size = float(zv["unit_size"]); a.max_distance = float(zv["max_m"])
		uz.add_child(a); o["zvuk"] = a
	ohne.append(o)
	_ukaz(o)


func _geom(g: GeometryInstance3D) -> void:
	g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	g.visibility_range_end = float(cfg["rozpocet"]["plamen_do_m"])
	g.add_to_group("predehrat")   # predehrati.gd: shader ohně sestavit při načtení, ne při prvním pohledu na oheň


## Viditelnost plamene a uhlíků podle stavu (světlo řídí _rozpocet).
func _ukaz(o: Dictionary) -> void:
	if o.has("plamen"): (o["plamen"] as Node3D).visible = o["hori"]
	if o.has("uhliky"): (o["uhliky"] as Node3D).visible = o["hori"]
	if o.has("zhar"): (o["zhar"] as GeometryInstance3D).material_overlay = _mat_uhliky if o["hori"] else null


## Zapálit / uhasit oheň i (ručně – pece domů pak nepřepíná denní doba).
func prepni(i: int, rucne := true) -> void:
	if i < 0 or i >= ohne.size(): return
	var o: Dictionary = ohne[i]
	o["hori"] = not o["hori"]
	if rucne: o["rucne"] = true
	_ukaz(o)
	_rozpocet()


## Rozdmýchat oheň ve stavbě koren (měch kovárny – funkce.gd; Havran main.gd kovarna_mech → life.gd fire_spots boost = 1):
## síla 1 klesá na 0 za roz.pokles_s; světlo × (1 + roz.svetlo × síla), plamen × (1 + roz.plamen × síla). Čísla funkce.json mech.rozhoreni.
func rozdmychej(koren: Node, roz: Dictionary) -> bool:
	var ok := false
	for o: Dictionary in ohne:
		var u: Node = o.get("uzel")
		if is_instance_valid(u) and (koren == u or koren.is_ancestor_of(u)):
			o["boost"] = 1.0; o["boost_cfg"] = roz; ok = true
	return ok


func pocet_svetel() -> int:
	var k := 0
	for o: Dictionary in ohne:
		if (o["svetlo"] as OmniLight3D).visible: k += 1
	return k


## Pořadí světel: nejbližších svetel_max hořících ohňů; zapnout pod zap_m, vypnout nad vyp_m; zvuk jen do zvuk_do_m.
func _rozpocet(kde = null) -> void:
	var cam := get_viewport().get_camera_3d()
	var p: Vector3 = kde if kde != null else (cam.global_position if cam else Vector3.ZERO)
	var rz: Dictionary = cfg["rozpocet"]; var zap := float(rz["zap_m"]); var vyp := float(rz["vyp_m"])
	var kand: Array = []
	for i in ohne.size():
		var o: Dictionary = ohne[i]; var d: float = p.distance_to(o["zaklad"]); o["d"] = d
		if o["hori"] and d < (vyp if o["zap"] else zap): kand.append(i)
	kand.sort_custom(func(a: int, b: int) -> bool: return float(ohne[a]["d"]) < float(ohne[b]["d"]))
	var maxn := int(rz["svetel_max"])
	for i in ohne.size():
		var o: Dictionary = ohne[i]
		var na := kand.find(i); o["zap"] = na >= 0 and na < maxn
		(o["svetlo"] as OmniLight3D).visible = o["zap"]
		if o.has("zvuk"):
			var a: AudioStreamPlayer3D = o["zvuk"]; var ma: bool = o["hori"] and float(o["d"]) < float(rz["zvuk_do_m"])
			if ma and not a.playing: a.play(randf() * 60.0)
			elif not ma and a.playing: a.stop()


## Ohně podle denní doby (pokud je hráč nepřepnul ručně): hori "noc" (pece domů, kamna) večer a v noci, ve dne ne;
## hori "casy" (kuchyně hradu) v intervalech hodiny [[od, do], …] hodin den.gd. hod = hodina pro test (jinak den.gd).
func _noc(hned := false, hod := -1.0) -> void:
	var den: Node = hlavni.get("den")
	if hod < 0.0: hod = float(den.hour) if den else 20.0
	var dn: Dictionary = cfg["domy_noc"]
	var noc := hod >= float(dn["hori_od_h"]) or hod < float(dn["hori_do_h"])
	var zmena := false
	for o: Dictionary in ohne:
		if o["rucne"]: continue
		var ma: bool = o["hori"]
		if o["noc"]: ma = noc
		elif not (o["casy"] as Array).is_empty():
			ma = false
			for c: Array in o["casy"]: ma = ma or (hod >= float(c[0]) and hod < float(c[1]))
		if ma != o["hori"]:
			o["hori"] = ma; _ukaz(o); zmena = true
	if zmena and not hned: _rozpocet()


func _process(dt: float) -> void:
	if not pripraveno: return
	_t_kontrola += dt; _t_noc += dt
	if _t_kontrola >= float(cfg["rozpocet"]["kontrola_s"]): _t_kontrola = 0.0; _rozpocet()
	if _t_noc >= 2.0: _t_noc = 0.0; _noc()
	# blikání zapnutých světel (≤ svetel_max): siny + pomalý šum, chvění polohy; mezi zap_m a vyp_m energie ubývá
	var bl: Dictionary = cfg["svetlo"]["blikani"]; var t := Time.get_ticks_msec() / 1000.0
	var zap := float(cfg["rozpocet"]["zap_m"]); var vyp := float(cfg["rozpocet"]["vyp_m"]); var pm := float(bl["poloha_m"])
	for o: Dictionary in ohne:   # rozhoření měchem (rozdmychej): plamen vyšší, síla klesá
		if float(o["boost"]) <= 0.0: continue
		var rz: Dictionary = o["boost_cfg"]
		o["boost"] = maxf(0.0, float(o["boost"]) - dt / float(rz["pokles_s"]))
		if o.has("plamen"): (o["plamen"] as Node3D).scale = Vector3.ONE * (1.0 + float(rz["plamen"]) * float(o["boost"]))
	for o: Dictionary in ohne:
		if not o["zap"]: continue
		var l: OmniLight3D = o["svetlo"]; var f: float = o["faze"] + t
		o["sum_t"] = float(o["sum_t"]) - dt
		if float(o["sum_t"]) <= 0.0: o["sum_t"] = float(bl["sum_krok_s"]) * randf_range(0.6, 1.4); o["sum_cil"] = randf_range(-1.0, 1.0) * float(bl["sum_amp"])
		o["sum"] = lerpf(float(o["sum"]), float(o["sum_cil"]), clampf(dt * 4.0, 0.0, 1.0))
		var k := 1.0 + float(o["sum"])
		for s: Array in bl["siny"]: k += float(s[1]) * sin(f * float(s[0]))
		if float(o["boost"]) > 0.0: k *= 1.0 + float(o["boost_cfg"]["svetlo"]) * float(o["boost"])
		l.light_energy = float(o["energie"]) * k * clampf((vyp - float(o["d"])) / (vyp - zap), 0.0, 1.0)
		l.global_position = (o["poloha"] as Vector3) + Vector3(sin(f * 5.3), sin(f * 6.7) * 0.5, cos(f * 4.1)) * pm
	_nabidka()


## Nabídka Zapálit / Uhasit oheň (styl a místo jako žebříky: tlačítko svitku nad nimi; jen na zaměřený oheň – zamer.gd).
func _nabidka() -> void:
	if Engine.get_process_frames() % 6 != 0: return
	var pr: Node = null
	for c in hlavni.get_children():
		if c is CanvasLayer and c.get("zebriky") != null: pr = c; break
	if pr == null or hlavni.get("hrac") == null: return
	if tlacitko == null:
		tlacitko = Button.new(); tlacitko.custom_minimum_size = Vector2(260, 90); Styl.tlacitko_pruh(tlacitko, load("res://fonty/GrenzeGotisch-Medium.ttf"), 30, 0)
		tlacitko.anchor_left = 0.5; tlacitko.anchor_right = 0.5; tlacitko.anchor_top = 1.0; tlacitko.anchor_bottom = 1.0
		tlacitko.offset_left = -170; tlacitko.offset_right = 170
		tlacitko.visible = false; tlacitko.pressed.connect(pouzij)
		pr.add_child(tlacitko)
		if hlavni.hrac.get("ui") != null: hlavni.hrac.ui.append(tlacitko)
	var h: CharacterBody3D = hlavni.hrac
	_blizko = -1
	if not (h.leze or h.leti):
		var dosah := float(cfg["nabidka"]["dosah_m"]); var best := 1e9
		for i in ohne.size():
			var o: Dictionary = ohne[i]; var c: Vector3 = (o["zaklad"] as Vector3) + Vector3.UP * 0.15
			if h.cam.global_position.distance_to(c) > dosah: continue
			var sc := Zamer.skore(h.cam, c, dosah, o["vlastni"])
			if sc >= 0.0 and sc < best: best = sc; _blizko = i
	tlacitko.visible = _blizko >= 0
	if tlacitko.visible:
		tlacitko.text = String(cfg["nabidka"]["uhasit" if ohne[_blizko]["hori"] else "zapalit"])
		# nad žebříkem (−270) a dveřmi; když Akce ukazuje 3 řádky, ještě výš
		var ak := pr.get_node_or_null("Akce"); var nad := -270.0
		if ak:
			for b in ak.get_children():
				if b is Button and (b as Button).visible: nad = minf(nad, (b as Button).offset_top - 2.0)
		tlacitko.offset_bottom = nad; tlacitko.offset_top = nad - 90.0


func pouzij() -> void:
	if _blizko < 0: return
	prepni(_blizko)
	if tlacitko: tlacitko.text = String(cfg["nabidka"]["uhasit" if ohne[_blizko]["hori"] else "zapalit"])
