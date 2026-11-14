extends Node3D
## Hlavní scéna: svět, světlo, obloha, hráč, panel měření. Vše kódem – žádné ručně psané .tscn s vymyšlenými uid
## (pravidlo Havrana 28. 10.).
## Snímek bez hráče: PUCHART_FOTO="x,z,vyska_nad_terenem,cil_x,cil_z,cil_vyska;soubor.png" (y dopočte z terénu).

const Svet := preload("res://scripts/svet.gd")
const Hrac := preload("res://scripts/hrac.gd")
const Diag := preload("res://scripts/diag.gd")
const Les := preload("res://scripts/les.gd")
const BunkyKolem := preload("res://scripts/bunky_kolem.gd")
const Denik := preload("res://scripts/denik.gd")   # deník běhu: poslední krok před pádem (12. 11.)

var svet: Node3D
var hrac: CharacterBody3D
var _foto := ""
var _snimek := 0
var _mereni: Array = []
var _env: Environment
var _fog_zakl: Array = []
var _les := 0.0       # 0..1 zápoj korun kolem hráče (mlha v lese – Havran daylight.gd _les_mlha)
var _uvnitr := 0.0    # 0 venku, 1 pod střechou/klenbou (méně modrého světla z oblohy – Havran _amb)
var den: Node = null  # denní doba (scripts/den.gd, Havran daylight.gd): slunce, obloha, mlha, noc

func _ready() -> void:
	var dn: Node = Denik.new(); dn.name = "Denik"; add_child(dn); dn.zacni(self)
	Denik.zapis("start")
	# herní data mimo APK (scripts/data.gd, Havran): první spuštění je stáhne, další jen načtou
	if not ResourceLoader.exists("res://modely/hrady/puchart.glb"):
		var vrstva := CanvasLayer.new(); add_child(vrstva)
		var pozadi := ColorRect.new(); pozadi.color = Color(0.1, 0.09, 0.08); pozadi.set_anchors_preset(Control.PRESET_FULL_RECT); vrstva.add_child(pozadi)
		var txt := Label.new(); txt.set_anchors_preset(Control.PRESET_FULL_RECT)
		txt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; txt.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		txt.add_theme_font_size_override("font_size", 36); txt.text = "Připravuji herní data…"; vrstva.add_child(txt)
		var dat: Node = load("res://scripts/data.gd").new(); add_child(dat)
		dat.status.connect(func(t: String) -> void:
			txt.text = t
			if not t.begins_with("Stahuji herní data… "): Denik.zapis("data: " + t))
		if not await dat.ensure():
			return   # hláška zůstane na obrazovce (internet / znovu spustit)
		vrstva.queue_free()
	_start()

func _start() -> void:
	_prostredi()
	if FileAccess.file_exists("res://data/rozpocty.json"):   # rozlišení 3D (rozpocty.json obraz_3d)
		var o: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json")).get("obraz_3d", {})
		get_viewport().scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
		get_viewport().scaling_3d_scale = float(o.get("scale", 1.0))
		var cf := ConfigFile.new()   # rozlišení si nastavuje hráč (Nastavení → Obraz 3D, user://nastaveni.cfg); data = výchozí
		if cf.load("user://nastaveni.cfg") == OK: get_viewport().scaling_3d_scale = float(cf.get_value("obraz", "scale_3d", get_viewport().scaling_3d_scale))
		var sm: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json")).get("snimky_max", {})
		if not OS.has_feature("pc") and not chce_mereni():
			Engine.max_fps = int(sm.get("tablet", 0))   # Havran 0.99991: méně tepla = žádné škrcení (sekání po 10 min hry)
	Denik.zapis("svět (terén)")
	svet = Svet.new(); svet.name = "Svet"
	add_child(svet)
	Denik.zapis("hrad")
	var hrad_id := OS.get_environment("PUCHART_HRAD")
	if hrad_id == "":
		hrad_id = "puchart"
	if FileAccess.file_exists("res://modely/hrady/%s.glb" % hrad_id) or ResourceLoader.exists("res://modely/hrady/%s.glb" % hrad_id):
		var h: Node3D = load("res://modely/hrady/%s.glb" % hrad_id).instantiate()
		h.name = "Hrad"
		add_child(h)
		for k in h.find_children("KOLIZE*", "MeshInstance3D", true, false):
			(k as MeshInstance3D).visible = false
		_svetla(h)
		if OS.get_environment("PUCHART_BEZ_LOD") == "": _hrad_lod(h, hrad_id)
		_zdivo_bez_rastru(h)
		if get_node_or_null("HradDaleko"): _zdivo_bez_rastru(get_node("HradDaleko"))
	Denik.zapis("skály")
	if ResourceLoader.exists("res://modely/hrady/skaly.glb"):   # skalní výchozy (blender/skaly.py, skaly.json)
		var sk: Node3D = load("res://modely/hrady/skaly.glb").instantiate(); sk.name = "Skaly"; add_child(sk)
		for k in sk.find_children("KOLIZE*", "MeshInstance3D", true, false):
			(k as MeshInstance3D).visible = false
		# barva vrcholu = odstín/AO po plochách (hrady.barva_kusu) – jako albedo dělala ze skály čtverce („minecraft“, Míša 9. 11.)
		var _sh_skala: Shader = load("res://shaders/skala.gdshader")
		var _droba: StandardMaterial3D = null   # police s mechem dostanou taky drobu – mech dělá shader jen místy (Míša 10. 11.)
		for mi_ in sk.find_children("*", "MeshInstance3D", true, false):
			var m0_ := (mi_ as MeshInstance3D).mesh
			if m0_ == null or _droba != null: continue
			for i_ in m0_.get_surface_count():
				var t_ := m0_.surface_get_material(i_) as StandardMaterial3D
				if t_ and t_.resource_name.begins_with("skala") and not t_.resource_name.begins_with("skala_mech"): _droba = t_; break
		for mi_ in sk.find_children("*", "MeshInstance3D", true, false):
			var ms_ := (mi_ as MeshInstance3D).mesh
			if ms_ == null: continue
			for i_ in ms_.get_surface_count():
				var mt_ := ms_.surface_get_material(i_) as StandardMaterial3D
				if mt_ == null: continue
				# skála jako v KCD: triplanár s plynulým přechodem, tónové skvrny, lišejník, mech nahoře (shaders/skala.gdshader, Míša 10. 11.)
				var sm_ := ShaderMaterial.new(); sm_.shader = _sh_skala
				var zd_ := _droba if (_droba and mt_.resource_name.begins_with("skala_mech")) else mt_
				sm_.set_shader_parameter("tex_a", zd_.albedo_texture); sm_.set_shader_parameter("tex_n", zd_.normal_texture)
				sm_.set_shader_parameter("meritko", 1.0 / 2.6); sm_.set_shader_parameter("mech", 1.0 if mt_.resource_name.begins_with("skala_mech") else 0.0)
				sm_.set_shader_parameter("jas", 0.85)
				ms_.surface_set_material(i_, sm_)
	Denik.zapis("rostliny skal")
	if FileAccess.file_exists("res://data/skaly_rostliny.json"): _rostliny_skal()
	Denik.zapis("stavby míst")
	if FileAccess.file_exists("res://data/mista_stavby.json"): _mista()   # Předhradí, krčma, hájovna (Míša 11. 11.; domy z Havrana)
	if FileAccess.file_exists("res://data/mista_stavby.json"): add_child(preload("res://scripts/ves.gd").new())   # usedlosti: stodoly, kůlny, ploty, zahrady, studna, stromy (ves.gd)
	Denik.zapis("kameny v korytech")
	if FileAccess.file_exists("res://data/koryto_kameny.json"): _kameny_koryta()   # valouny a balvany v korytech (Míša 10. 11.)   # kapradí, tráva, mech, semenáčky na římsách skal
	var _jp_dosah := 220.0
	if FileAccess.file_exists("res://data/voda_hra.json"):
		_jp_dosah = float(JSON.parse_string(FileAccess.get_file_as_string("res://data/voda_hra.json"))["koryto"]["jemny_pas"]["dosah_kresleni_m"])
	Denik.zapis("voda")
	if ResourceLoader.exists("res://modely/voda.glb"):   # potoky a lávky (blender/voda.py, voda_hra.json)
		var vo: Node3D = load("res://modely/voda.glb").instantiate(); vo.name = "Voda"; add_child(vo)
		var mv := ShaderMaterial.new(); mv.shader = load("res://shaders/voda.gdshader")
		mv.set_shader_parameter("normal_tex", load("res://textury/voda_normal.png")); mv.set_shader_parameter("pena_tex", load("res://textury/voda_pena.png"))
		if FileAccess.file_exists("res://data/voda_hra.json"):   # vzhled vody z dat (voda_hra.json vzhled_13_11: pipeta misa_real, Fresnel, čirost)
			var vz: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/voda_hra.json")).get("vzhled_13_11", {})
			for k in ["melka", "hluboka", "odraz", "cirost_m", "hloubka_barvy_m", "fresnel_f0", "drsnost_klid", "drsnost_pena", "specular", "kraj_m", "pena_zaklad", "pena_barva"]:
				if not vz.has(k): continue
				var v = vz[k]
				mv.set_shader_parameter(k if k == "kraj_m" else k.trim_suffix("_m"), Color(v[0], v[1], v[2]) if v is Array else float(v))
		for mi in vo.find_children("*", "MeshInstance3D", true, false):
			var m := mi as MeshInstance3D
			if m.name.begins_with("KOLIZE"): m.visible = false; continue
			if m.name.begins_with("brod_"):   # kameny brodu jen nablízko (hlídač scén 9. 11.: rozpočet trojúhelníků)
				m.visibility_range_end = 120.0; m.visibility_range_end_margin = 10.0
				m.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
			if m.name.begins_with("BREH"):   # jemný pás břehů: materiál terénu, jen nablízko (dál ho nahradí dlaždice)
				m.material_override = svet.mat_zem; m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				m.visibility_range_end = _jp_dosah; continue
			for i in m.mesh.get_surface_count():
				var mt := m.mesh.surface_get_material(i)
				if mt != null and mt.resource_name.begins_with("voda"):
					m.set_surface_override_material(i, mv); m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
					# jemná hladina (na mřížce břehu) jen blízko, dál jednoduchý pás VODA_DALEKO – rozpočet scén (hlídač 4. 11.)
					if m.name.begins_with("VODA_DALEKO"):
						m.visibility_range_begin = _jp_dosah
						var md := mv.duplicate() as ShaderMaterial; md.set_shader_parameter("zdvih_daleko", 0.006); m.set_surface_override_material(i, md)
					else: m.visibility_range_end = _jp_dosah
	Denik.zapis("les")
	var les := Les.new(); les.name = "Les"
	add_child(les)
	les.postav(svet)
	Denik.zapis("hráč")
	hrac = Hrac.new(); hrac.name = "Hrac"
	var tvar := CollisionShape3D.new(); var kap := CapsuleShape3D.new(); kap.radius = 0.3; kap.height = 1.75
	tvar.shape = kap; tvar.position.y = 0.875; hrac.add_child(tvar)
	var cam := Camera3D.new(); cam.name = "Kamera"; cam.position.y = 1.65; cam.fov = 70.0; cam.far = 12000.0; cam.near = 0.1
	hrac.add_child(cam)
	add_child(hrac)
	svet.hrac = hrac
	# start: louka nad předním hradem, pohled k ostrohu (hra: přední hrad = počátek)
	var start := Vector3(-60.0, 0.0, -150.0)
	start.y = svet.vyska(start.x, start.z) + 0.2
	hrac.position = start
	hrac.look_at(Vector3(0.0, svet.vyska(0.0, 0.0) + 1.6, 0.0), Vector3.UP)
	hrac.rotation.x = 0.0
	add_child(Diag.new())
	if chce_mereni(true):
		var Mer := load("res://scripts/mereni.gd")
		var mer: Node = Mer.new(); add_child(mer)
		hrac.set_physics_process(false)
		cam.top_level = true
		mer.konec.connect(_prochazka)
		if den: den.running = false   # měření za stejných podmínek (odpoledne); čas se rozběhne po měření
		_mereni = [mer, cam]
	_foto = OS.get_environment("PUCHART_FOTO")
	var byl: Node3D = load("res://scripts/byliny.gd").new(); byl.name = "Byliny"; add_child(byl)
	if _foto != "":
		var c := _foto.split(";")
		var v := c[0].split_floats(",")
		var ab := OS.get_environment("PUCHART_FOTO_ABS") != ""   # výšky absolutně (snímky portálů v patrech – nastroje/foto_portaly.sh)
		var p := Vector3(v[0], (0.0 if ab else svet.vyska(v[0], v[1])) + v[2], v[1])
		var t := Vector3(v[3], (0.0 if ab else svet.vyska(v[3], v[4])) + v[5], v[4])
		hrac.set_physics_process(false)
		hrac.position = p - Vector3(0, 1.65, 0)
		cam.look_at_from_position(p, t, Vector3.UP)
		cam.top_level = true
		if OS.get_environment("PUCHART_FOTO_SVETLO") != "": var ls_ := OmniLight3D.new(); ls_.omni_range = 25.0; ls_.light_energy = 3.0; cam.add_child(ls_)   # snímek tmavého interiéru
		var dvf: Node = load("res://scripts/dvere.gd").new(); dvf.name = "DvereFoto"; add_child(dvf); dvf.zacni(self, CanvasLayer.new())   # řetězy padacích mostů i na snímku
		if OS.get_environment("PUCHART_FOTO_MOST") != "":   # snímek se zvednutými padacími mosty (ověření výklenku a řetězů)
			for g: String in dvf.druh:
				if dvf.druh[g] == "most": dvf.prepni(g); dvf.doba[g] = 0.05
		if OS.get_environment("PUCHART_ORTO") != "":   # půdorys shora: pravoúhlá projekce, velikost = výška záběru v m
			cam.projection = Camera3D.PROJECTION_ORTHOGONAL
			cam.size = float(OS.get_environment("PUCHART_ORTO"))
	Denik.zapis("byliny")
	byl.postav(svet, cam)
	Denik.zapis("louka")
	var lou: Node3D = load("res://scripts/louka.gd").new(); lou.name = "Louka"; add_child(lou); lou.postav(svet, cam)   # trsy trávy (Havran louka)
	Denik.zapis("keře")
	var ker: Node3D = load("res://scripts/byliny.gd").new(); ker.name = "Kere"; add_child(ker)   # keře a zmlazení (data/kere.json)
	ker.postav(svet, cam, "res://data/kere.json")
	Denik.zapis("předehřátí shaderů")
	if _foto == "" and OS.get_environment("PUCHART_TEST") == "" and _pr.get("predehrati", {}).get("zapojeno", false):   # shadery všech materiálů sestavit hned, ne až za chůze (záseky při 1. průchodu – Havran 0.62)
		await get_tree().process_frame
		await load("res://scripts/predehrati.gd").predehrej(self, cam, byl.vsechny_site() + ker.vsechny_site() + _vzory_bunek(), int(_pr.get("predehrati", {}).get("snimku", 4)))
	# rozpočet uzlů (pád na tabletu 11. 11.: 115 tis. buněk lesu = nedostatek paměti) – výpis po vrstvách
	var uz := []
	for ch in get_children(): uz.append("%s %d" % [ch.name, ch.find_children("*", "", true, false).size()])
	Denik.zapis("UZLY %d" % Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	print("UZLY celkem %d, halda %d MB: %s" % [Performance.get_monitor(Performance.OBJECT_NODE_COUNT), OS.get_static_memory_usage() / 1048576, ", ".join(uz)])
	Denik.zapis("měření / procházka")
	if _mereni.size() > 0: _mereni[0].zacni(svet, _mereni[1])
	var meri := _mereni.size() > 0
	if OS.get_environment("PUCHART_TEST") == "pruchod":
		_test_pruchod.call_deferred()
	elif OS.get_environment("PUCHART_TEST") == "sceny":
		_test_sceny.call_deferred()
	elif _foto == "" and not meri:
		_prochazka.call_deferred()
	_kolize_hradu.call_deferred()
	if OS.get_environment("PUCHART_SKRIPT") != "": var ts_: Node = load(OS.get_environment("PUCHART_SKRIPT")).new(); add_child(ts_)   # ladicí skript (testy funkcí)
	for jm in OS.get_environment("PUCHART_SKRYJ").split(",", false):   # diagnostika výkonu: skrýt vrstvu (Les, Kere, Byliny, Hrad, Skaly, Voda)
		var n := get_node_or_null(jm)
		if n: n.visible = false

## Test výkonu (mereni.gd) jen na přání (Míša 14. 11.: „nespouštěj na začátku hry test, dej ho do nastavení“):
## Nastavení → Spustit test výkonu zapíše user://nastaveni.cfg [test] pri_startu a hru spustí znovu; příznak se při použití smaže.
## Na PC dál PUCHART_MERENI=1 (hlídači).
var _chce_mereni := -1
func chce_mereni(spotrebuj := false) -> bool:
	if not FileAccess.file_exists("res://data/mereni.json"): return false
	if OS.get_environment("PUCHART_MERENI") == "1": return true
	if _chce_mereni < 0:
		var cf := ConfigFile.new(); cf.load("user://nastaveni.cfg")
		_chce_mereni = 1 if bool(cf.get_value("test", "pri_startu", false)) else 0
	if spotrebuj and _chce_mereni == 1:
		var cf2 := ConfigFile.new(); cf2.load("user://nastaveni.cfg")
		cf2.set_value("test", "pri_startu", false); cf2.save("user://nastaveni.cfg")
	return _chce_mereni == 1

## Kolize hradu pro procházku: trojúhelníková kolize ze sítí modelu (zdi, mosty, schody) – jedno statické těleso.
func _kolize_hradu() -> void:
	for jm in (["Hrad"] if _foto != "" else ["Hrad", "Skaly", "Voda"]):   # snímek: jen hrad (louče hledají zeď)
		var h := get_node_or_null(jm)
		if h != null: _kolize_uzlu(h)
	# louče a svícny až po kolizích (hledají podlahu a zeď paprskem; 11. 11.: voláno dřív = 0/20 při běžném startu)
	if not _k_svicnum.is_empty(): _svicny()

func _kolize_uzlu(h: Node) -> void:
	# Havran: kolize z kvádrů uzlu KOLIZE (zdi, podlahy, mostovky, schody jako rampy); starší návrhy bez něj ze sítí
	var kol := h.find_children("KOLIZE*", "MeshInstance3D", true, false)
	for mi in (kol if kol.size() > 0 else h.find_children("*", "MeshInstance3D", true, false)):
		(mi as MeshInstance3D).create_trimesh_collision()
		for cs in (mi as MeshInstance3D).find_children("*", "CollisionShape3D", true, false):   # oboustranně: úlomky suti a stupně skal mají
			if h.name != "Hrad" and (cs as CollisionShape3D).shape is ConcavePolygonShape3D:   # hrad = uzavřené kvádry   # stěny s obráceným pořadím vrcholů – zvenku se jimi procházelo (povrch_kolize)
				((cs as CollisionShape3D).shape as ConcavePolygonShape3D).backface_collision = true

## Pochodně ve věžích, hladomorně a sklepě (data/svetla.json ze stavitele hradu): bez stínů, zhasínají na dálku.
func _svetla(h: Node3D) -> void:
	if not FileAccess.file_exists("res://data/svetla.json"):
		return
	var bez_louci := not bool(JSON.parse_string(FileAccess.get_file_as_string("res://data/svetla.json")).get("louce", true))
	for s in JSON.parse_string(FileAccess.get_file_as_string("res://data/svetla.json"))["svetla"]:
		if bez_louci and not s.get("den", false) and s.get("svit", "louc") != "ohen": continue   # Míša 12. 11.: louče si dá sám z pískoviště (bez držáku ani světla z ničeho)
		var l := OmniLight3D.new(); var p: Array = s["pos"]
		l.position = Vector3(p[0], p[1], p[2]); l.light_color = Color(0.86, 0.9, 1.0) if s.get("den", false) else Color(1.0, 0.68, 0.38)   # den = světlo z oken (Míša 9. 11.)
		l.light_specular = 0.0 if s.get("den", false) else 0.5
		l.light_energy = s["energie"]; l.omni_range = s["dosah"]; l.shadow_enabled = false
		l.distance_fade_enabled = true; l.distance_fade_begin = 35.0; l.distance_fade_length = 10.0
		if s.get("den", false): l.set_meta("den_svetlo", true)   # světlo z oken – den.gd ho v noci zhasne
		h.add_child(l)
		if not s.get("den", false) and s.get("svit", "louc") != "ohen": _k_svicnum.append(l); l.set_meta("svit", s.get("svit", "louc"))

## Světlo místnosti s předmětem Havrana (Míša 10. 11.: „když je místnost tmavá, dej tam louč nebo svícen, vezmi předměty z Havrana“;
## „do sklepa určitě nepatří svícen, ale louč“): svit=louc (sklep, kobky, věže, chodby) = louč v železném držáku na zdi ve 1,9 m,
## svit=svicen (obytné místnosti paláců) = stojací svícen u zdi. Modely z Havranových balíků (modely/predmety, textury zmenšené
## na 256 px – Havran 0.59: 2k textury předmětů = záseky a pád při vstupu do budovy), načtené jednou při startu.
## Paprsek dolů najde podlahu, v 8 směrech nejbližší stěnu (≤ 3 m), světlo se přesune k plameni.
var _k_svicnum: Array = []
var _svicnu_bez := 0
var _svicnu := 0
func _svicny() -> void:
	for i in 4: await get_tree().physics_frame   # kolize hradu (_kolize_hradu deferred)
	var md := {"svicen": "res://modely/predmety/svicen_stojaci.glb", "louc": "res://modely/predmety/louc.glb", "drzak": "res://modely/predmety/drzak_louce.glb"}
	var sc := {}
	for k in md:
		if ResourceLoader.exists(md[k]): sc[k] = load(md[k])
	var ss := get_world_3d().direct_space_state
	for l: OmniLight3D in _k_svicnum:
		var typ: String = l.get_meta("svit", "louc")
		if not sc.has(typ): continue
		var p := l.global_position
		var dol := ss.intersect_ray(PhysicsRayQueryParameters3D.create(p, p - Vector3(0, 4.0, 0)))
		if dol.is_empty(): continue
		var y0: float = dol["position"].y
		var nej := {}; var nd := 3.0; var kraj := {}; var nd_k := 3.0
		for k in 8:
			var sm := Vector3(cos(k * PI / 4), 0, sin(k * PI / 4)); var o := Vector3(p.x, y0 + 1.0, p.z)
			var r := ss.intersect_ray(PhysicsRayQueryParameters3D.create(o, o + sm * 3.0))
			if r.is_empty() or absf((r["normal"] as Vector3).y) >= 0.3: continue
			if o.distance_to(r["position"]) < nd_k: nd_k = o.distance_to(r["position"]); kraj = r
			if o.distance_to(r["position"]) < nd and _plna_zed(ss, r, y0): nd = o.distance_to(r["position"]); nej = r
		typ = "louc"   # Míša 12. 11.: „nechci svícny, chci louče; radši je tam nedávej, dám si je sám z pískoviště“
		if nej.is_empty():   # bez plné rovné zdi louč nedávat a světlo vypnout (svítilo by z ničeho)
			l.visible = false; _svicnu_bez += 1; continue
		var nrm: Vector3 = nej["normal"]; nrm.y = 0; nrm = nrm.normalized()
		var uzel := Node3D.new(); l.get_parent().add_child(uzel)
		if typ == "svicen":
			var q: Vector3 = (nej["position"] as Vector3) + nrm * 0.35; q.y = y0
			var n: Node3D = sc["svicen"].instantiate(); uzel.add_child(n); uzel.global_position = q; uzel.rotation.y = randf() * TAU
			l.global_position = q + Vector3(0, 1.62, 0)
		else:   # louč: přesně jako Havran predmety.spawn_on_wall("drzak_louce") + _bracket_torch (Míša 12. 11.: držák kolmo, louč v držáku)
			var r: Array = [0.09, 0.175, 0.191]   # predmety_h.json drzak_louce rozmer
			var q: Vector3 = nej["position"] + nrm * (float(r[2]) * 0.5 + 0.035) - Vector3.UP * float(r[1]) * 0.5; q.y = y0 + 1.75
			uzel.global_position = q; uzel.rotation.y = atan2(nrm.x, nrm.z)   # +z modelu = od zdi
			if sc.has("drzak"): uzel.add_child(sc["drzak"].instantiate())
			var lc: Node3D = sc["louc"].instantiate(); uzel.add_child(lc)
			lc.position = Vector3(0, -0.03, 0.057); lc.rotation.x = deg_to_rad(12)
			l.global_position = lc.to_global(Vector3(0, 0.56, 0))
			_plamen(l.global_position)
		for mi in uzel.find_children("*", "GeometryInstance3D", true, false): (mi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var sv_: Dictionary = _pr.get("atmosfera", {}).get("svitidla", {})
		l.light_energy = maxf(l.light_energy, 2.2) * float(sv_.get("energie_nasobek", 1.0)); l.omni_range = maxf(l.omni_range, 8.0) * float(sv_.get("dosah_nasobek", 1.0)); l.omni_attenuation = 0.7   # místnost nesmí zůstat tmavá
		_svicnu += 1
	print("SVICNY %d/%d" % [_svicnu + _svicnu_bez, _k_svicnum.size()])
	print("LOUCE %d, bez plné zdi vynecháno %d" % [_svicnu, _svicnu_bez])

## Zeď pro držák musí být plná a rovná (Míša 12. 11.: louč visela v prostoru u dveří – paprsek trefil hranu ostění):
## kolem bodu ±0,4 m do stran a v rozsahu výšky louče (1,4–2,3 m nad podlahou) musí být zeď ve stejné rovině (±8 cm).
func _plna_zed(ss: PhysicsDirectSpaceState3D, r: Dictionary, y0: float) -> bool:
	var n: Vector3 = r["normal"]; n.y = 0; n = n.normalized()
	var t := Vector3(-n.z, 0, n.x); var b: Vector3 = r["position"]
	for d: Vector2 in [Vector2(-0.4, 1.4), Vector2(0.4, 1.4), Vector2(-0.4, 2.3), Vector2(0.4, 2.3), Vector2(0, 1.75)]:
		var c: Vector3 = b + t * d.x; c.y = y0 + d.y
		var h := ss.intersect_ray(PhysicsRayQueryParameters3D.create(c + n * 0.5, c - n * 0.3))
		if h.is_empty() or absf(((h["position"] as Vector3) - c).dot(n)) > 0.08: return false
	return true

func _test_pruchod() -> void:
	await get_tree().create_timer(2.0).timeout   # kolize hradu (deferred) a terén kolem
	var cam: Camera3D = hrac.get_node("Kamera")
	cam.top_level = false; cam.transform = Transform3D(Basis(), Vector3(0, 1.65, 0))
	var t: Node = load("res://scripts/test_pruchod.gd").new(); add_child(t)
	t.zacni(self, hrac)

func _test_sceny() -> void:
	await get_tree().create_timer(1.0).timeout
	var t: Node = load("res://scripts/test_sceny.gd").new(); add_child(t)
	t.zacni(self, hrac.get_node("Kamera"))

## Po měření (nebo hned na PC) hlavní nabídka jako v Havranovi: Nová hra (Příběh / Pískoviště), Pokračovat, Nahrát…
## (Míša 12. 11. večer: „na procházku se vykašli – po měření naběhne menu“). Ovládání hry, mapa a nabídky: prochazka.gd.
func _prochazka() -> void:
	if den: den.running = true
	var cam: Camera3D = hrac.get_node("Kamera")
	cam.top_level = false; cam.transform = Transform3D(Basis(), Vector3(0, 1.65, 0))
	hrac.set_physics_process(true)
	var pr: CanvasLayer = load("res://scripts/prochazka.gd").new(); add_child(pr)
	pr.zacni(self, hrac)

func _atmosfera(d: float) -> void:
	if _env == null or hrac == null: return
	var cam: Camera3D = get_viewport().get_camera_3d()
	if cam == null: return
	var p := cam.global_position
	var lm: Dictionary = _pr.get("atmosfera", {}).get("les_mlha", {}); var it: Dictionary = _pr.get("atmosfera", {}).get("interier", {})
	if Engine.get_process_frames() % 10 == 0:
		var les: Node = get_node_or_null("Les")
		_les_cil = les.zapoj(p.x, p.z, lm) if les and les.has_method("zapoj") and not lm.is_empty() else 0.0
		var q := PhysicsRayQueryParameters3D.create(p, p + Vector3.UP * float(it.get("paprsek_nahoru_m", 25.0)))
		_uvnitr_cil = 1.0 if not it.is_empty() and get_world_3d().direct_space_state.intersect_ray(q).size() > 0 else 0.0
		if _uvnitr_cil > 0.5 and it.has("otvory_paprsky"):   # kolik je vidět ven (okna, dveře) – světlo jen přes otvory (Míša 13. 11.)
			var n_ := int(it["otvory_paprsky"]); var ven_ := 0; var zd: Array = it["otvory_zdvih_st"]; var L_ := float(it["otvory_delka_m"])
			for k_ in n_:
				var az := TAU * float(k_ % 8) / 8.0 + (0.39 if k_ >= 8 else 0.0); var el := deg_to_rad(float(zd[0] if k_ < 8 else zd[1]))
				var sm := Vector3(cos(az) * cos(el), sin(el), sin(az) * cos(el))
				if get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(p, p + sm * L_)).is_empty(): ven_ += 1
			_otvory_cil = float(ven_) / float(n_)
	_les = move_toward(_les, _les_cil, d * float(lm.get("rychlost", 0.5))); _uvnitr = move_toward(_uvnitr, _uvnitr_cil, d * float(it.get("rychlost", 1.5)))
	var hloubkova := _sceny(d, cam) > 0.0
	if not lm.is_empty():
		var lb: Array = lm["barva"]
		_env.fog_light_color = ((den.mlha as Color) if den else (_fog_zakl[0] as Color)).lerp(Color(lb[0], lb[1], lb[2]), _les * float(lm["podil_barvy"]))
		_env.fog_density = 1.0 if hloubkova else lerpf(_fog_zakl[1], float(lm["hustota_max"]), _les)
	else:
		_env.fog_density = 1.0 if hloubkova else _fog_zakl[1]
	_env.fog_sky_affect = clampf(0.35 * (1.0 - _kresleni / 12000.0) * 1.5, 0.0, 0.35)   # obloha do oparu podle zkrácení kreslení (plynule)
	if not it.is_empty():
		var ab: Array = it["ambient_barva"]; var ub := float(it["ubytek_oblohy"])
		var ve: Dictionary = _pr["atmosfera"].get("venku", {})   # venku: část okolního světla odraz od země a zdí (teplý), ne jen modrá obloha
		var vb: Array = ve.get("barva", ab); var vo := float(ve.get("podil_oblohy", 1.0))
		_otvory = move_toward(_otvory, _otvory_cil, d * 0.8)
		var amb_in := float(it["ambient"]) * (1.0 - ub)
		if it.has("ambient_tma"): amb_in = lerpf(float(it["ambient_tma"]), float(it["ambient_okno"]), sqrt(_otvory))
		_env.ambient_light_energy = lerpf(float(ve.get("ambient", it["ambient"])), amb_in, _uvnitr) * (float(den.okolni_e) if den else 1.0)
		_env.ambient_light_sky_contribution = lerpf(vo, 1.0, _uvnitr) * (1.0 - _uvnitr * ub)
		var ok_ := float(den.okolni) if den else 1.0   # v noci teplá složka ubude s oblohou (den.json okolni_pozn)
		var ac_ := Color(vb[0], vb[1], vb[2]).lerp(Color(ab[0], ab[1], ab[2]), _uvnitr)
		_env.ambient_light_color = Color(ac_.r * ok_, ac_.g * ok_, ac_.b * ok_)
		_env.tonemap_exposure = 1.0 + _uvnitr * float(it["expozice_navic"])

var _les_cil := 0.0
var _uvnitr_cil := 0.0
var _otvory := 1.0
var _otvory_cil := 1.0
var _dh: Dictionary = {}        # data/dohled.json (nastroje/viditelnost.py: dohled na mřížce × směry)
var _dh_data := PackedByteArray()
var _sc_pr: Dictionary = {}     # data/sceny_pravidla.json hra
var _kresleni := 12000.0        # aktuální vzdálenost kreslení kamery (plynule)
var _kresleni_cil := 12000.0
var scena_typ := ""
var _sc_prvni := false             # pro diag a hlídač scén

## Scény (GPT „Inteligentní tvorba scén“ bod 4–6): podle nejbližšího bodu trasy typ A/B/C a skutečný dohled z DMR+lesa.
## Kamera kreslí jen do dohledu × násobek, mlha je na konci kreslení skoro neprůhledná – nic neodskočí; panorama C plné.
func _sceny(d: float, cam: Camera3D) -> float:
	if _sc_pr.is_empty():
		if not (FileAccess.file_exists("res://data/dohled.json") and FileAccess.file_exists("res://data/sceny_pravidla.json")): return 0.0
		_sc_pr = JSON.parse_string(FileAccess.get_file_as_string("res://data/sceny_pravidla.json"))
		_dh = JSON.parse_string(FileAccess.get_file_as_string("res://data/dohled.json"))
		_dh_data = FileAccess.get_file_as_bytes("res://data/dohled.bin")
	var hr: Dictionary = _sc_pr["hra"]; var ty_pr: Dictionary = _sc_pr["typy"]
	var p := cam.global_position
	if Engine.get_process_frames() % 6 == 0 or OS.get_environment("PUCHART_TEST") == "sceny":   # test: každý snímek (QA: typ z předchozího bodu)
		# dohled v zorném poli: 3 sektory kolem směru pohledu, maximum ze 4 okolních bodů mřížky (nic nezmizí dřív)
		var f := -cam.global_basis.z; var ns: int = _dh["smeru"]
		var uhel := fposmod(atan2(f.x, -f.z), TAU); var si := int(round(uhel / TAU * ns)) % ns
		var gx := (p.x - float(_dh["x0"])) / float(_dh["krok_m"]); var gz := (p.z - float(_dh["z0"])) / float(_dh["krok_m"])
		var dohled := 0.0   # bilineárně mezi body mřížky, maximum ze 3 sektorů zorného pole
		var ix0 := clampi(int(gx), 0, int(_dh["nx"]) - 2); var iz0 := clampi(int(gz), 0, int(_dh["nz"]) - 2)
		var fx := clampf(gx - ix0, 0.0, 1.0); var fz := clampf(gz - iz0, 0.0, 1.0)
		for k in [-1, 0, 1]:
			var sk: int = (si + int(k) + ns) % ns; var v := [0.0, 0.0, 0.0, 0.0]
			for q in 4:
				var i: int = (((iz0 + q / 2) * int(_dh["nx"]) + ix0 + q % 2) * ns + sk) * 2
				v[q] = float(_dh_data.decode_u16(i))
			dohled = maxf(dohled, lerpf(lerpf(v[0], v[1], fx), lerpf(v[2], v[3], fx), fz))
		var nad: float = p.y - svet.vyska(p.x, p.z)
		var typ := "C" if (dohled >= float(ty_pr["panorama_od_m"]) or nad > float(hr["let_nad_m"])) else ("A" if dohled < float(ty_pr["uzavrena_do_m"]) else "B")
		var ty: Dictionary = hr["typy"][typ]
		_kresleni_cil = clampf(dohled * float(hr["nasobek_dohledu"]), float(ty["kresleni_min_m"]), float(ty["kresleni_max_m"]))
		scena_typ = typ
	# hystereze: dohled se otevírá rychle (nic nesmí chybět), zavírá pomalu (žádné pumpování mlhy při otáčení)
	var rych: float = float(hr["rychlost_m_s"]) * (4.0 if _kresleni_cil > _kresleni else 1.0)
	# první vyhodnocení a test scén: hned na cíl (dřív start na 12 km a zavírání 60 m/s = 3 min kreslení celé krajiny)
	if _foto != "" or not _sc_prvni: _kresleni = _kresleni_cil; _sc_prvni = true
	else: _kresleni = move_toward(_kresleni, _kresleni_cil, d * rych)
	cam.far = _kresleni + 50.0
	# hloubková mlha vždy (dřív přepínání exponenciální ↔ hloubková = skok obrazu na hranici scén, hlídač scén 2. 11.):
	# čistý obraz do mlha_od × kreslení, na konci kreslení plně zakryto; panorama (12 km) = mlha jen u obzoru
	_env.fog_mode = Environment.FOG_MODE_DEPTH
	_env.fog_depth_begin = _kresleni * float(_sc_pr["hra"]["mlha_od"]); _env.fog_depth_end = _kresleni; _env.fog_depth_curve = float(_sc_pr["hra"]["mlha_krivka"])
	return 1.0

func _process(_d: float) -> void:
	_atmosfera(_d)
	_lod_tick()
	if _foto == "":
		return
	_snimek += 1
	if _snimek == 40:
		var c := _foto.split(";")
		get_viewport().get_texture().get_image().save_png(c[1])
		print("FOTO ", c[1], " kresleni ", RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
			" troj ", RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
		get_tree().quit()

var _pr: Dictionary = {}

func _prostredi() -> void:
	if FileAccess.file_exists("res://data/prostredi.json"):
		_pr = JSON.parse_string(FileAccess.get_file_as_string("res://data/prostredi.json"))
	# léto 1393 (PDF: hotová letní krajina); výchozí odpoledne, slunce z JZ – den a noc pak řídí den.gd (Havran daylight.gd).
	# Stín jen blízko (rozpocty.json stiny); jediné slunce, žádné nové stíny ani světla.
	var slunce := DirectionalLight3D.new()
	slunce.rotation_degrees = Vector3(-38.0, -140.0, 0.0)
	slunce.light_energy = 1.0
	slunce.light_color = Color(1.0, 0.95, 0.86)
	slunce.shadow_enabled = true
	slunce.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	slunce.directional_shadow_max_distance = 40.0
	# stíny jen do 40 m: v lese byl kruh stínu korun kolem hráče ostře useknutý – tmavá skvrna, která chodila s hráčem
	# (Míša 4. 11.: „můj stín jako stín budovy, pokrýval obrovskou plochu“) → stín plynule slábne od 35 % dosahu
	slunce.directional_shadow_fade_start = float(_pr.get("stin_slabne_od", 0.35))
	slunce.shadow_normal_bias = 2.0   # zubaté pruhy stínu na prknech schodů a zdech (Míša 4. 11.)
	slunce.shadow_bias = 0.06
	slunce.light_angular_distance = 0.7   # velikost kotouče slunce a v noci měsíce na obloze (Havran daylight.gd)
	add_child(slunce)
	var sky_mat := ShaderMaterial.new()   # obloha Havrana: přechod, záře slunce, mraky, v noci hvězdy a měsíc (shaders/sky.gdshader)
	sky_mat.shader = load("res://shaders/sky.gdshader")
	sky_mat.set_shader_parameter("cloud_tex", load("res://textury/nebe/cloud_noise.png"))
	sky_mat.set_shader_parameter("zenith", Color(0.32, 0.5, 0.78)); sky_mat.set_shader_parameter("horizon", Color(0.72, 0.78, 0.84))
	sky_mat.set_shader_parameter("ground", Color(0.25, 0.27, 0.22))
	var sky := Sky.new(); sky.sky_material = sky_mat
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.35
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_white = 1.6
	# atmosféra z dat (pravidla/svet/prostredi.json atmosfera – Havran daylight.gd, GPT výzkum: hloubková/výšková mlha)
	var at: Dictionary = _pr.get("atmosfera", {})
	var c3 := func(a: Array) -> Color: return Color(a[0], a[1], a[2])
	env.fog_enabled = true
	env.fog_light_color = c3.call(at.get("mlha_barva", [0.68, 0.75, 0.84]))
	env.fog_density = float(at.get("mlha_hustota", 0.0005))
	env.fog_aerial_perspective = float(at.get("vzdusna_perspektiva", 0.75))
	env.fog_sky_affect = 0.0
	env.fog_sun_scatter = float(at.get("rozptyl_slunce", 0.0))
	if at.has("prizemni_mlha"):
		env.fog_height = float(at["prizemni_mlha"]["vyska_y"]); env.fog_height_density = float(at["prizemni_mlha"]["hustota"])
	if at.has("zare"):
		env.glow_enabled = true; env.glow_intensity = float(at["zare"]["intenzita"]); env.glow_bloom = float(at["zare"]["bloom"]); env.glow_hdr_threshold = float(at["zare"]["prah_hdr"])
	if at.has("uprava"):
		env.adjustment_enabled = true; env.adjustment_contrast = float(at["uprava"]["kontrast"]); env.adjustment_saturation = float(at["uprava"]["sytost"])
	_env = env; _fog_zakl = [env.fog_light_color, env.fog_density]
	var we := WorldEnvironment.new(); we.environment = env
	add_child(we)
	if FileAccess.file_exists("res://data/den.json"):   # plynulý den a noc (Havran daylight.gd; pravidla/svet/den.json)
		den = load("res://scripts/den.gd").new(); den.name = "Den"; add_child(den); den.setup(slunce, sky_mat, env, self)
		if FileAccess.file_exists("res://data/pocasi.json"):   # déšť (pocasi.gd, Míša 12. 11.)
			var pc: Node3D = load("res://scripts/pocasi.gd").new(); pc.name = "Pocasi"; add_child(pc); pc.setup(den)

## Hrad blízko plný (reliéf zdiva, ~600 k troj.), dál zjednodušený *_daleko.glb (stavitel ho peče, ale hra ho nenačítala –
## hlídač scén 3. 11.: 7/127 snímků nad rozpočtem i 300 m od hradu). Hranice z pravidla/svet/hrad_vzhled.json lod.
var _lod_pary: Array = []   # [[střed, poloměr, [blízké], [daleké]]] – přepínání podle JEDNOHO středu (dřív visibility_range měřil
var _lod_od := 60.0          # každá verze od středu svého AABB → 50–70 m od hradu nebyla vidět ani jedna; tablet 4. 11.: most bez věže)
var _lod_pr := 10.0
var _lod_init := false
func _hrad_lod(h: Node3D, hid: String) -> void:
	var cesta := "res://modely/hrady/%s_daleko.glb" % hid
	if not ResourceLoader.exists(cesta): return
	var lod: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/hrad_vzhled.json")).get("lod", {})
	_lod_od = float(lod.get("daleko_od_m", 120.0)); _lod_pr = float(lod.get("prolinani_m", 10.0))
	var d: Node3D = load(cesta).instantiate(); d.name = "HradDaleko"; add_child(d)
	var dal := {}
	for m in d.find_children("*", "MeshInstance3D", true, false):
		if String(m.name).begins_with("KOLIZE"): (m as MeshInstance3D).visible = false; continue
		dal[String(m.name)] = m
	for m in h.find_children("*", "MeshInstance3D", true, false):
		var jm := String(m.name)
		if jm.begins_with("KOLIZE") or jm.begins_with("Pohyb"): continue
		var bb: AABB = (m as MeshInstance3D).global_transform * (m as MeshInstance3D).get_aabb()
		var dm = dal.get(jm, null)
		_lod_pary.append([bb.get_center(), bb.size.length() * 0.5, [m], [dm] if dm != null else []])
		dal.erase(jm)
	for jm in dal: (dal[jm] as Node3D).visible = false   # daleká verze bez blízkého protějšku se nekreslí
	_lod_tick(true)

func _lod_tick(hned := false) -> void:
	var c := get_viewport().get_camera_3d()
	if c == null or _lod_pary.is_empty(): return
	if not _lod_init: hned = true; _lod_init = true
	var p := c.global_position
	for par in _lod_pary:
		var dist := maxf(0.0, p.distance_to(par[0]) - float(par[1]) * 0.5)   # od středu hradu minus půl poloměru (velký hrad dřív)
		var blizko: bool = (par[2][0] as Node3D).visible
		if hned: blizko = dist < _lod_od
		elif blizko and dist > _lod_od + _lod_pr: blizko = false
		elif not blizko and dist < _lod_od - _lod_pr: blizko = true
		for m in par[2]: (m as Node3D).visible = blizko
		for m in par[3]: (m as Node3D).visible = not blizko


var _zdivo_mat: Dictionary = {}
const TEXTURA_NAST := {   # Havran scripts/svet.gd material(): šindel radky+skvrny, dřevo kus (+ stékance venku), omítka skvrny+stékance
	"sindel_hra": {"radky": 1.0, "skvrny": 0.8, "budova": 1.0, "mech": 1.0, "stekance": 0.25, "jas": 1.7, "sedost": 0.55},   # KCD: světle šedohnědý zvětralý šindel
	"sindel": {"radky": 1.0, "skvrny": 0.8, "budova": 1.0, "mech": 1.0, "stekance": 0.25, "jas": 1.7, "sedost": 0.55},
	"dub": {"kus": 1.0, "pestrost": 1.0, "tint2": Vector3(0.82, 0.78, 0.72)},
	"hraz": {"kus": 1.0, "stekance": 0.4, "skvrny": 0.5},
	"dub_ven": {"kus": 1.0, "stekance": 0.5, "skvrny": 0.6},
	"prkna_ven": {"kus": 1.0, "stekance": 0.35, "skvrny": 0.5, "pestrost": 1.0, "tint2": Vector3(0.86, 0.8, 0.72), "sedost": 0.08},   # Míša 13. 11.: hnědé opotřebované (dřív sedost 0,35 – šedé)
	"prkno": {"kus": 1.0}, "prkno_ven": {"kus": 1.0, "stekance": 0.3}, "okenice": {"kus": 1.0, "stekance": 0.4},
	"dvere": {"kus": 1.0, "stekance": 0.3},
	"omitka": {"skvrny": 0.7, "stekance": 0.45, "budova": 0.6},
	"kvadr_okno": {"antitile": 1.0, "skvrny": 0.5},
}
var _tex_mat: Dictionary = {}
func _textura_mat(jm: String, mt: StandardMaterial3D) -> Material:
	if not TEXTURA_NAST.has(jm) or mt.albedo_texture == null: return null
	if not _tex_mat.has(jm):
		var z := ShaderMaterial.new(); z.shader = load("res://shaders/textura.gdshader")
		z.set_shader_parameter("tex_a", mt.albedo_texture); z.set_shader_parameter("tex_n", mt.normal_texture)
		z.set_shader_parameter("tex_r", mt.roughness_texture)
		var a := mt.albedo_color; z.set_shader_parameter("tint", Vector3(a.r, a.g, a.b))   # jas materiálu z Blenderu (TEX)
		var nast: Dictionary = TEXTURA_NAST[jm]
		for k in nast:
			if k == "tint2": z.set_shader_parameter("tint2", Vector3(a.r, a.g, a.b) * (nast[k] as Vector3))
			else: z.set_shader_parameter(k, nast[k])
		_tex_mat[jm] = z
	return _tex_mat[jm]

var _okno_mat: Dictionary = {}
func _zdivo_bez_rastru(h: Node) -> void:
	## Zdivo hradů: shader proti opakování textury (Míša 5. 11.: „rastr čtverečků“) – shaders/zdivo.gdshader
	var sh: Shader = load("res://shaders/zdivo.gdshader")
	for mi in h.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null or m.name.begins_with("KOLIZE"): continue
		for i in m.mesh.get_surface_count():
			var mt := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mt == null: continue
			var jm := mt.resource_name
			mt.vertex_color_use_as_albedo = false   # barva vrcholu = odstín a semeno kusu pro shadery, ne barva (železo, sklo by zčervenaly)
			if jm.begins_with("hlina"):   # násyp nájezdu mostu: materiál terénu (navazuje na zem a cestu; dřív světlá „cihla“)
				m.set_surface_override_material(i, svet.mat_zem); continue
			if jm.begins_with("sklo") or jm.begins_with("blana"):   # výplně oken: terčíky / blána, svítí denním světlem (Míša 9. 11.)
				if not _okno_mat.has(jm):
					var om := ShaderMaterial.new(); om.shader = load("res://shaders/okno.gdshader")
					om.set_shader_parameter("sklo", jm.begins_with("sklo")); om.set_shader_parameter("ven", jm.ends_with("_ven")); _okno_mat[jm] = om
				if den and not den.okna.has(_okno_mat[jm]): den.okna.append(_okno_mat[jm])   # v noci okna dovnitř nesvítí
				m.set_surface_override_material(i, _okno_mat[jm]); continue
			if not (jm.begins_with("zdivo") or jm == "kvadr" or jm == "kvadr_sedy"):
				var tm := _textura_mat(jm, mt)   # dřevo, šindel, omítka, ostění: Havranův shader proti rastru (shaders/textura.gdshader)
				if tm != null: m.set_surface_override_material(i, tm)
				continue
			var hr_ := "A" if m.name.contains("_A") else ("B" if m.name.contains("_B") else "")   # přední hrad hlinitá malta, zadní vápenitá (GC80T08)
			var klic_ := jm + hr_
			if not _zdivo_mat.has(klic_):
				var zd: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/materialy_hrad.json"))
				var nast: Dictionary = zd.get(jm, zd["zdivo"])
				if hr_ != "" and zd.has(hr_) and (zd[hr_] as Dictionary).has(jm): nast = zd[hr_][jm]
				var tk: String = zd["textury"]["kamen"]; var to: String = zd["textury"]["omitka"]
				var z := ShaderMaterial.new(); z.shader = sh
				z.set_shader_parameter("kamen_a", load(tk + "_diff.jpg")); z.set_shader_parameter("kamen_n", load(tk + "_nor.jpg"))
				z.set_shader_parameter("kamen_h", load(tk + "_disp.jpg"))
				z.set_shader_parameter("omitka_a", load(to + "_diff.jpg")); z.set_shader_parameter("omitka_n", load(to + "_nor.jpg"))
				z.set_shader_parameter("kryti", float(nast["kryti"])); z.set_shader_parameter("spina", float(nast["spina"]))
				var t1: Array = nast["tint"]; var t2: Array = nast["kamen_tint"]
				z.set_shader_parameter("tint", Vector3(t1[0], t1[1], t1[2])); z.set_shader_parameter("kamen_tint", Vector3(t2[0], t2[1], t2[2]))
				_zdivo_mat[klic_] = z
			m.set_surface_override_material(i, _zdivo_mat[klic_])


## Vzorky všech vrstev po buňkách kolem hráče (bunky_kolem.gd) pro předehřátí shaderů
func _vzory_bunek() -> Array:
	var a := []
	for n in find_children("*", "Node3D", true, false):
		if n.get_script() == BunkyKolem: a.append_array(n.vzory())
	return a


## Stavby nových míst (hra/data/mista_stavby.json z nastroje/mista_rozmisteni.py, pravidla/svet/mista.json): domy vsi z Havrana
## (modely/stavby_h/domy.glb – nastroje/stavby_z_havrana.sh) osazené jako v Havranovi svet.gd _ves_domy: počátek modelu = terén
## plošiny (podezdívka jde pod zem), kolize z modelu (Kol_*), podrobný vnějšek do podrobny_do_m, střední stupeň (1 materiál,
## barva vrcholu) do stredni_do_m (tablet stredni_do_m_mobil), dál hrubý obal _Daleko; vnitřek jen zblízka; stín jen z _Daleko.
func _mista() -> void:
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista_stavby.json"))
	var md: Dictionary = d["modely"]["domy"]
	if (d["stavby"] as Array).is_empty() or not ResourceLoader.exists(String(md["soubor"])): return
	var lod: Dictionary = d.get("lod", {"podrobny_do_m": 30.0, "stredni_do_m": 130.0, "stredni_do_m_mobil": 75.0, "vnitrek_do_m": 35.0, "lod_bias": 50.0})
	var blizko := float(lod["podrobny_do_m"]); var st_do := float(lod["stredni_do_m_mobil" if OS.has_feature("mobile") else "stredni_do_m"])
	var sc: Node = (load(String(md["soubor"])) as PackedScene).instantiate()
	var ssc: Node = (load(String(md["stredni"])) as PackedScene).instantiate() if ResourceLoader.exists(String(md["stredni"])) else null
	var st_mat := StandardMaterial3D.new(); st_mat.vertex_color_use_as_albedo = true; st_mat.roughness = 0.9
	var uzel := Node3D.new(); uzel.name = "Mista"; add_child(uzel)
	for s: Dictionary in d["stavby"]:
		var vzor := sc.get_node_or_null(String(s["model"])) as Node3D
		if vzor == null: continue
		var dum := vzor.duplicate() as Node3D
		dum.name = "%s_%s_%d" % [s["misto"], s["model"], uzel.get_child_count()]   # jedinečné jméno instance: skupina dveří dvere.gd = dveře@dům
		dum.transform = Transform3D(Basis(Vector3.UP, float(s["yaw"])), Vector3(float(s["x"]), float(s["teren_y"]), float(s["z"])))
		uzel.add_child(dum)
		_rampy_dveri(dum)
		var st_vzor: MeshInstance3D = ssc.find_child(String(s["model"]) + "_Stredni", true, false) as MeshInstance3D if ssc else null
		var se_st := st_vzor != null and blizko < st_do
		if se_st:
			var st := MeshInstance3D.new(); st.name = String(s["model"]) + "_Stredni"; st.mesh = st_vzor.mesh; st.transform = st_vzor.transform
			st.material_override = st_mat; st.lod_bias = float(lod["lod_bias"])   # bez automatického LOD (rozpustil šindele – Havran)
			st.visibility_range_begin = blizko; st.visibility_range_end = st_do; st.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			dum.add_child(st)
		var dal := st_do if se_st else (75.0 if OS.has_feature("mobile") else 130.0)
		for ch in dum.get_children():
			if not ch is MeshInstance3D or String(ch.name).ends_with("_Stredni"): continue
			var mi := ch as MeshInstance3D; var cn := String(ch.name)
			if cn.ends_with("_Daleko"):
				mi.visibility_range_begin = dal
				var sd := MeshInstance3D.new(); sd.name = cn + "_Stin"; sd.mesh = mi.mesh; sd.transform = mi.transform
				sd.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY; sd.visibility_range_end = dal
				dum.add_child.call_deferred(sd)
			elif cn.ends_with("Interier") or cn.ends_with("Drobne"):
				mi.visibility_range_end = float(lod["vnitrek_do_m"]) if cn.ends_with("Interier") else blizko
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			else:
				mi.visibility_range_end = blizko if se_st else dal
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	sc.queue_free()
	if ssc: ssc.queue_free()
	print("MISTA staveb %d" % uzel.get_child_count())


## Šikmá kolize u vnějších dveří domu (Míša 13. 11.: „do hájovny nemůžu vstoupit, všechny budovy musí být vstupné“): domy
## Havrana mají před prahem kamenný stupeň 0,15 m a podlahu 0,3 m nad základem, postava nemá krok nahoru (hradní schody mají
## rampu) – rampa z terénu na práh jako u schodů hradu (puchart_hrad.schody2 kol). Vnější dveře = uzel *_Dvere_* na obvodové stěně.
func _rampy_dveri(dum: Node3D) -> void:
	var xmax := 0.0
	for ch in dum.get_children():
		if String(ch.name).contains("_Dvere_") and ch is Node3D: xmax = maxf(xmax, absf((ch as Node3D).position.x))
	var kb := StaticBody3D.new(); kb.name = "RampyDveri"
	for ch in dum.get_children():
		if not (String(ch.name).contains("_Dvere_") and ch is MeshInstance3D): continue
		var mi := ch as MeshInstance3D
		if absf(mi.position.x) < xmax - 0.05: continue   # vnitřní dveře
		var sg := signf(mi.position.x); var ab := mi.get_aabb()
		var zc := mi.position.z + ab.position.z + ab.size.z * 0.5
		var x0 := mi.position.x + sg * 2.8; var x1 := mi.position.x - sg * 0.25   # venku na terénu → za prahem na podlaze (nad hranou stupně 1,05 m před stěnou je rampa 0,17 m – nad stupněm 0,15)
		var y0 := -0.02; var y1 := 0.32
		var L := Vector2(x1 - x0, y1 - y0).length(); var uh := atan2(y1 - y0, absf(x1 - x0))
		var cs := CollisionShape3D.new(); var bx := BoxShape3D.new(); bx.size = Vector3(L, 0.12, 0.9); cs.shape = bx
		cs.position = Vector3((x0 + x1) * 0.5, (y0 + y1) * 0.5 - 0.06, zc)
		cs.rotation.z = uh * (-sg)   # stoupá směrem dovnitř
		kb.add_child(cs)
	if kb.get_child_count() > 0: dum.add_child(kb)
	else: kb.free()


## Rostliny na skalách (blender/skaly.py → hra/data/skaly_rostliny.json; Míša 10. 11.: „vegetaci sem tam, ne jen mech“, fotky
## docs/reference/puchart_skaly): každý druh = modely z modely/rostliny, MultiMesh po buňkách bunka_m, kreslí se do dosah_m.
func _rostliny_skal() -> void:
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/skaly_rostliny.json"))
	var var_ := {}   # druh -> [[mesh, xform], ...] (jedna varianta = jedna síť modelu)
	for druh in d["modely"]:
		var_[druh] = []
		for jm in d["modely"][druh]:
			var f := "res://modely/rostliny/%s.glb" % jm
			if not ResourceLoader.exists(f): continue
			for sm in site_ze_sceny(load(f)):   # sítě bez vytvoření 3D uzlů (pád na tabletu 11. 11. při uvolňování instancí)
				var_[druh].append([sm[1], Transform3D(Basis(), Vector3.ZERO) if jm == "trava_sada" else sm[2]])
	var bm := float(d["bunka_m"]); var skup := {}
	for r in d["rostliny"]:
		var vs: Array = var_.get(r[0], [])
		if vs.is_empty(): continue
		var p := Vector3(float(r[1]), float(r[2]), float(r[3]))
		var v: Array = vs[int(absf(p.x * 7.13 + p.z * 3.71) * 10.0) % vs.size()]
		var t := Transform3D(Basis(Vector3.UP, float(r[4])).scaled(Vector3.ONE * float(r[5])), p) * (v[1] as Transform3D)
		var k := [int(floor(p.x / bm)), int(floor(p.z / bm)), v[0]]
		if not skup.has(k): skup[k] = []
		skup[k].append(t)
	# jen buňky kolem hráče (bunky_kolem.gd – pád na tabletu 11. 11.: vrstvy na celou mapu = došla paměť)
	var bk: Node3D = BunkyKolem.new(); bk.name = "RostlinySkal"; bk.B = bm; bk.R = float(d["dosah_m"]) + bm * 0.75 + 4.0
	var dosah := float(d["dosah_m"])
	bk.vyrob = func(mesh: Mesh, buf: PackedFloat32Array, n: int) -> Array:
		var mmi := BunkyKolem.mmi(mesh, buf, n); mmi.visibility_range_end = dosah
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		return [mmi]
	for k in skup:
		for t in skup[k]: bk.pridej(t, k[2])
	add_child(bk)


## Kameny v korytech (nastroje/koryto_kameny.py → hra/data/koryto_kameny.json, tvary blender/kameny_koryta.py): MultiMesh
## po buňkách a tvarech, materiál skála (skala.gdshader – droba, mech jen nahoře), do dosah_m, bez stínu (drobné).
func _kameny_koryta() -> void:
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/koryto_kameny.json"))
	if not ResourceLoader.exists(String(d["glb"])): return
	var tvary := {}
	for sm in site_ze_sceny(load(String(d["glb"]))):   # bez instancí (pád na tabletu 11. 11.)
		if String(sm[0]).begins_with("valoun_"): tvary[int(String(sm[0]).split("_")[1])] = sm[1]
	# droba jako skály (skala.gdshader, triplanár): drobné šedé bez mechu, velké balvany s mechem nahoře (fotky docs/reference/potok)
	var tex: Texture2D = load("res://modely/hrady/skaly_droba_Diffuse.jpg") if ResourceLoader.exists("res://modely/hrady/skaly_droba_Diffuse.jpg") else null
	var tn: Texture2D = load("res://modely/hrady/skaly_droba_nor_gl.jpg") if ResourceLoader.exists("res://modely/hrady/skaly_droba_nor_gl.jpg") else null
	var mats := []
	for v in 2:
		var m := ShaderMaterial.new(); m.shader = load("res://shaders/skala.gdshader")
		m.set_shader_parameter("tex_a", tex); m.set_shader_parameter("tex_n", tn); m.set_shader_parameter("meritko", 1.0 / 1.5)
		m.set_shader_parameter("mech", 1.0 if v == 1 else -3.0); m.set_shader_parameter("jas", 1.75 if v == 0 else 1.25)   # omletá droba světle šedá (fotky potok_01–02)
		mats.append(m)
	var bm := float(d["bunka_m"]); var skup := {}
	var raw := FileAccess.get_file_as_bytes("res://data/koryto_kameny.bin").to_float32_array()
	for i in range(0, raw.size(), 7):
		var tv := int(raw[i])
		if not tvary.has(tv % 6): continue
		var p := Vector3(raw[i + 1], raw[i + 2], raw[i + 3]); var sc := raw[i + 5]
		var k := Vector3i(int(floor(p.x / bm)), int(floor(p.z / bm)), tv)
		if not skup.has(k): skup[k] = []
		skup[k].append(Transform3D(Basis(Vector3.UP, raw[i + 4]).scaled(Vector3(sc, sc * raw[i + 6], sc * 0.85)), p))
	# jen buňky kolem hráče (bunky_kolem.gd – pád na tabletu 11. 11.): drobné kameny do dosah_m, velké balvany do velky_dosah_m
	for vel in [false, true]:
		var dosah := float(d.get("velky_dosah_m", 160)) if vel else float(d["dosah_m"])
		var bk: Node3D = BunkyKolem.new(); bk.name = "KamenyKorytaVelke" if vel else "KamenyKoryta"; bk.B = bm; bk.R = dosah + bm * 0.75 + 4.0
		var mat: Material = mats[1 if vel else 0]
		bk.vyrob = func(tv: int, buf: PackedFloat32Array, n: int) -> Array:
			var mmi := BunkyKolem.mmi(tvary[tv % 6], buf, n); mmi.visibility_range_end = dosah; mmi.material_override = mat
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if vel else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			return [mmi]
		for k in skup:
			if (int(k.z) >= 6) != vel: continue
			for t in skup[k]: bk.pridej(t, int(k.z))
		add_child(bk)


## Plamen louče (Havran life.gd _flames(pos, 0.38, 10, 0.45) – „torch“): CPUParticles jazyků ohně, aditivní, bez stínu;
## textura plamene měkký kapkovitý přechod (Havran p_flame.png je v jeho datovém balíku – zde GradientTexture2D, bez souboru).
## Světlo louče mihotá (Havran life._light: fáze, rychlost 7–11).
var _plamen_mat: StandardMaterial3D
func _plamen(pos: Vector3) -> void:
	var p := _plamen_castice(0.5, 10, 0.45)   # o něco větší než Havran (louč ve tmě sklepa – plamen nebyl vidět)
	p.visibility_range_end = 40.0
	add_child(p); p.global_position = pos

func _plamen_castice(size: float, amount: int, life_s: float) -> CPUParticles3D:   # Havran life._flames (i pro předměty – svíce, lucerny)
	if _plamen_mat == null:
		var gt := GradientTexture2D.new(); gt.fill = GradientTexture2D.FILL_RADIAL; gt.fill_from = Vector2(0.5, 0.62); gt.fill_to = Vector2(0.5, 0.05)
		var gr := Gradient.new(); gr.set_color(0, Color(1, 1, 1, 1)); gr.set_color(1, Color(1, 1, 1, 0)); gr.add_point(0.45, Color(1, 1, 1, 0.55)); gt.gradient = gr
		gt.width = 64; gt.height = 64
		var m := StandardMaterial3D.new(); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD; m.albedo_texture = gt; m.vertex_color_use_as_albedo = true
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES; m.billboard_keep_scale = true; m.disable_receive_shadows = true
		_plamen_mat = m
	var p := CPUParticles3D.new(); p.amount = amount; p.lifetime = life_s; p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX; p.emission_box_extents = Vector3(0.22, 0.03, 0.12) * size
	p.direction = Vector3.UP; p.spread = 12.0; p.gravity = Vector3(0, 0.9 * size, 0)
	p.initial_velocity_min = 0.25 * size; p.initial_velocity_max = 0.55 * size; p.scale_amount_min = 0.55 * size; p.scale_amount_max = 0.95 * size
	var cv := Curve.new(); cv.add_point(Vector2(0.0, 0.6)); cv.add_point(Vector2(0.25, 1.0)); cv.add_point(Vector2(1.0, 0.15)); p.scale_amount_curve = cv
	var g := Gradient.new(); g.set_color(0, Color(1.0, 0.85, 0.5, 0.0)); g.set_color(1, Color(0.6, 0.12, 0.02, 0.0))
	g.add_point(0.12, Color(1.0, 0.78, 0.38, 0.9)); g.add_point(0.5, Color(1.0, 0.42, 0.1, 0.6)); p.color_ramp = g
	var q := QuadMesh.new(); q.size = Vector2(0.32, 0.42); q.material = _plamen_mat; p.mesh = q
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return p


## Sítě ze scény .glb bez vytvoření uzlů (PackedScene.get_state): [[jméno, Mesh, Transform3D]] – Míša 11. 11.: hra padala na
## tabletu při okamžitém uvolnění instancovaných 3D uzlů (Node.free → ~VisualInstance3D → renderer_scene_cull).
static func site_ze_sceny(ps: PackedScene) -> Array:
	var out := []; var st := ps.get_state()
	for i in st.get_node_count():
		var m: Mesh = null; var t := Transform3D.IDENTITY
		for k in st.get_node_property_count(i):
			var pn := st.get_node_property_name(i, k)
			if pn == "mesh": m = st.get_node_property_value(i, k)
			elif pn == "transform": t = st.get_node_property_value(i, k)
		if m != null: out.append([String(st.get_node_name(i)), m, t])
	return out
