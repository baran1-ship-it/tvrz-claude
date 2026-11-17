extends Node
## Měřicí trasa (PDF kap. 13 „stejná cesta, stejné podmínky“): kamera proletí 4 úseky – hrad, les, voda, vyhlídka –
## každý zahřátí 5 s + měření 30 s. Na konci tabulka na obrazovce + user://mereni.txt. Spouští se, když existuje
## res://data/mereni.json (měřicí APK) nebo PUCHART_MERENI=1.
## Délka snímku = skutečná razítka (ne vyhlazené delta – poučení Havrana), p50/p95/max, záseky > 40 ms.
## Plán 17. 11. A3 (Halcyon, Havran): podíl snímků pod cílem 30 FPS (> 33,3 ms, rozpocty.json snimek.cil_fps), p99 a průměr
## nejhorších 5 % snímků – sloupce na konci řádku (dřívější sloupce beze změny). Automatika detailu (regulator.gd) je během
## měření vypnutá na stupni 0. Na konci výpis textur použitých ve scéně (textury_vram.gd → user://textury_vram.txt).

var trasa: Array
var cam: Camera3D
var svet: Node3D
var useky := []
var i_usek := 0
var t := 0.0
var casy := PackedFloat32Array()
var _proc_max := 0.0   # nejdelší _process za úsek (ms, Performance.TIME_PROCESS) – špičky přestavby buněk i na PC, kde llvmpipe kreslí > 40 ms
var kres := 0.0
var troj := 0.0
var vzorku := 0
var _posl := 0
var lbl: Label
var verze := ""
var skaly := [1.0]
var i_sk := 0
var varianty: Array = []
var i_var := -1
var _skryte: Array = []
var _slunce: DirectionalLight3D
var _louka_un := false
var _hra_3d := 0.75
var vykreslovani := ""   # renderer · ovladač · GPU · API (vykreslovani.gd popis)
var _vyk_id := ""
var _cil_ms := 1000.0 / 30.0   # snímek pod cílem FPS (rozpocty.json snimek.cil_fps)
signal konec

func zacni(s: Node3D, kamera: Camera3D) -> void:
	svet = s; cam = kamera
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/mereni.json"))
	trasa = cfg["useky"]; verze = cfg.get("verze", "") + " / Godot " + Engine.get_version_info()["string"]
	varianty = cfg.get("varianty", [])
	var jen := OS.get_environment("PUCHART_MERENI_JEN")   # PC vývoj: jen vybrané úseky a jejich varianty (např. "les"), méně času a paměti
	if jen != "":
		var js := jen.split(",")
		trasa = trasa.filter(func(u: Dictionary) -> bool: return String(u["jmeno"]) in js)
		varianty = varianty.filter(func(v: Dictionary) -> bool: return String(v.get("usek", "")) in js)
	var vk := get_node_or_null("/root/Vykreslovani")   # vykreslování do výsledku (Compatibility / Vulkan – stejná trasa v obou, vykreslovani.gd)
	_vyk_id = String(vk.bezici()["id"]) if vk and not vk.cfg.is_empty() else RenderingServer.get_current_rendering_method()
	vykreslovani = vk.popis() if vk and not vk.cfg.is_empty() else "%s (%s) · %s" % [RenderingServer.get_current_rendering_method(), RenderingServer.get_current_rendering_driver_name(), RenderingServer.get_video_adapter_name()]
	_hra_3d = get_viewport().scaling_3d_scale   # rozlišení hry (rozpocty.json obraz_3d) – po měření se vrátí (12. 11.: zůstalo 100 %)
	skaly = cfg.get("scale_3d", [_hra_3d]); get_viewport().scaling_3d_scale = float(skaly[0])
	if FileAccess.file_exists("res://data/rozpocty.json"):
		_cil_ms = 1000.0 / float(JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json")).get("snimek", {}).get("cil_fps", 30))
	var reg := get_tree().get_first_node_in_group("regulator")   # automatika detailu: měří se plný detail, bez zásahů
	if reg: reg.vypni("měření")
	if FileAccess.file_exists("res://data/sestava.json"):
		verze += " / " + str(JSON.parse_string(FileAccess.get_file_as_string("res://data/sestava.json")).get("commit", ""))
	cam.top_level = true
	lbl = Label.new(); lbl.position = Vector2(30, 140)
	lbl.add_theme_font_size_override("font_size", 26)
	lbl.add_theme_color_override("font_outline_color", Color.BLACK); lbl.add_theme_constant_override("outline_size", 6)
	var cl := CanvasLayer.new(); cl.layer = 10; cl.add_child(lbl); add_child(cl)
	_posl = Time.get_ticks_usec()

func _bod(u: Dictionary, f: float) -> Array:
	var a: Array = u["od"]; var b: Array = u["do"]; var c: Array = u["cil"]
	var x := lerpf(a[0], b[0], f); var z := lerpf(a[1], b[1], f)
	var p := Vector3(x, svet.vyska(x, z) + float(u.get("nad", 1.7)), z)
	var cc := Vector3(c[0], svet.vyska(c[0], c[1]) + float(c[2]), c[1])
	return [p, cc]

func _process(d: float) -> void:
	if trasa.is_empty() or i_usek >= trasa.size():
		return
	var now := Time.get_ticks_usec(); var ms := (now - _posl) / 1000.0; _posl = now
	var u: Dictionary = trasa[i_usek]
	t += d
	var celk := 5.0 + 30.0 if OS.get_environment("PUCHART_MERENI_RYCHLE") == "" else 1.0 + 2.0   # hlídač: zkrácené úseky
	var pc := _bod(u, clampf(t / celk, 0.0, 1.0))
	cam.look_at_from_position(pc[0], pc[1], Vector3.UP)
	if t > celk - 30.0 * (1.0 if OS.get_environment("PUCHART_MERENI_RYCHLE") == "" else 2.0 / 30.0):
		casy.append(ms)
		_proc_max = maxf(_proc_max, Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
		kres += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
		troj += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
		vzorku += 1
	lbl.text = "MĚŘENÍ %s\n%s\n3D %d %%  úsek %d/%d: %s  %.0f s" % [verze, vykreslovani, roundi(float(skaly[i_sk]) * 100), i_usek + 1, trasa.size(), u["jmeno"], celk - t]
	if t >= celk:
		var s := casy.duplicate(); s.sort()
		var n := s.size()
		var zas := 0; var zas2 := 0; var pod := 0   # záseky nad 40 ms (rozpocty.json zasek_ms) a nad 2× medián (PC: llvmpipe kreslí každý snímek nad 40 ms); pod cílem FPS
		for x in s:
			if x > 40.0: zas += 1
			if x > 2.0 * s[n / 2]: zas2 += 1
			if x > _cil_ms: pod += 1
		var i5 := mini(int(n * 0.95), n - 1); var nejh := 0.0   # průměr nejhorších 5 % (aspoň jeden snímek)
		for k in range(i5, n): nejh += s[k]
		nejh /= float(n - i5)
		var v := get_viewport().get_visible_rect().size * get_viewport().scaling_3d_scale   # skutečné 3D rozlišení (i varianta „les 70 %“)
		useky.append({"jmeno": ("%s %d%%" % [u["jmeno"], roundi(float(skaly[i_sk]) * 100)]) if i_var < 0 else String(varianty[i_var]["jmeno"]), "px": "%dx%d" % [roundi(v.x), roundi(v.y)], "p50": s[n / 2], "p95": s[int(n * 0.95)], "max": s[n - 1], "zaseky": zas,
			"snimku": n, "kresleni": kres / vzorku, "troj_m": troj / vzorku / 1e6,
			"proc_max": _proc_max, "nad_2p50": zas2,
			"pod_cil_pct": 100.0 * pod / n, "p99": s[mini(int(n * 0.99), n - 1)], "nejh5": nejh,
			"vram_mb": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0,
			"halda_mb": OS.get_static_memory_usage() / 1048576.0})
		casy = PackedFloat32Array(); _proc_max = 0.0; kres = 0; troj = 0; vzorku = 0; t = 0.0
		i_usek += 1
		if i_usek >= trasa.size() and i_sk + 1 < skaly.size():   # další rozlišení 3D, stejná trasa
			i_sk += 1; i_usek = 0; get_viewport().scaling_3d_scale = float(skaly[i_sk])
		elif i_usek >= trasa.size() or i_var >= 0:
			_dalsi_varianta()

## Varianty (mereni.json varianty): jeden úsek znovu se skrytými vrstvami / bez stínu slunce / jiným 3D – cena vrstev na tabletu
func _dalsi_varianta() -> void:
	for n in _skryte: (n as Node3D).visible = true
	_skryte.clear()
	if _slunce: _slunce.shadow_enabled = true
	var lou0 := get_tree().current_scene.get_node_or_null("Louka")   # varianta trava_unshaded: zpět na výchozí (louka.json unshaded)
	if lou0 and lou0.has_method("nastav_unshaded") and _louka_un: lou0.nastav_unshaded(lou0._un_vychozi()); _louka_un = false
	var poc0 := get_tree().current_scene.get_node_or_null("Pocasi")
	if poc0: poc0.vynuceno = -1.0   # po variantě s deštěm a po konci měření zase podle rozvrhu
	get_viewport().scaling_3d_scale = float(skaly[0])
	i_var += 1
	if i_var >= varianty.size(): _konec(); return
	var v: Dictionary = varianty[i_var]
	var koren := get_tree().current_scene
	for jm in v.get("skryj", []):
		var n := koren.get_node_or_null(String(jm))
		if n is Node3D and (n as Node3D).visible: (n as Node3D).visible = false; _skryte.append(n)
	if v.has("stin") and not bool(v["stin"]):
		if _slunce == null:
			var l := koren.find_children("*", "DirectionalLight3D", true, false)
			if not l.is_empty(): _slunce = l[0]
		if _slunce: _slunce.shadow_enabled = false
	if v.has("scale"): get_viewport().scaling_3d_scale = float(v["scale"])
	if v.has("trava_unshaded"):   # tráva bez stínového průchodu / stínovaná (louka.gd nastav_unshaded, Havran varianta louka_un)
		var lou := koren.get_node_or_null("Louka")
		if lou and lou.has_method("nastav_unshaded"): lou.nastav_unshaded(bool(v["trava_unshaded"])); _louka_un = true
	var poc := koren.get_node_or_null("Pocasi")   # varianta s deštěm (pocasi.gd, Míša 12. 11.: „nezasekat tablet“)
	if poc: poc.vynuceno = float(v.get("dest", -1.0))
	for k in trasa.size():
		if trasa[k]["jmeno"] == v["usek"]: i_usek = k
	t = 0.0

func _konec() -> void:
	# měření končí: _process už nic nedělá (12. 11.: běželo dál po trase, na konci úseku „voda“ sáhlo na neexistující
	# variantu – chyba každý snímek, čas do minusu a kamera se přetahovala s hráčem = obraz poskakoval na místě)
	trasa = []; set_process(false)
	get_viewport().scaling_3d_scale = _hra_3d
	var txt := "VÝSLEDEK %s\nvykreslování: %s\n%s\n" % [verze, vykreslovani, Time.get_datetime_string_from_system()]
	txt += "úsek            3D px       p50   p95   max  záseky  snímků  kreslení  troj M  VRAM MB  >2×p50  proc max  >%.1f ms %%    p99  nejh. 5 %%\n" % _cil_ms
	for u in useky:
		txt += "%-14s %-10s %5.1f %5.1f %5.0f %6d %7d %8.0f %7.2f %8.0f %7d %9.1f %11.1f %6.1f %10.1f\n" % [u["jmeno"], u["px"], u["p50"], u["p95"], u["max"], u["zaseky"], u["snimku"], u["kresleni"], u["troj_m"], u["vram_mb"], u["nad_2p50"], u["proc_max"], u["pod_cil_pct"], u["p99"], u["nejh5"]]
	txt += preload("res://scripts/zasoba_mm.gd").souhrn() + "\n"   # P2: kolik MultiMeshů vzniklo / použilo se znovu
	txt += preload("res://scripts/textury_vram.gd").zapis(get_tree().current_scene, "user://textury_vram.txt") + "\n"   # A2: textury ve scéně (odhad VRAM)
	var f0 := FileAccess.open("user://mereni.txt", FileAccess.WRITE)   # uložit hned (Míša 12. 11.: výsledek zmizel pod nabídkou)
	if f0: f0.store_string(txt); f0.close()
	var f1 := FileAccess.open("user://mereni_%s.txt" % _vyk_id, FileAccess.WRITE)   # poslední výsledek každého vykreslování zvlášť – srovnání v nabídce Měření
	if f1: f1.store_string(txt); f1.close()
	lbl.text = txt + "\n(ms na snímek; vyfoť obrazovku a pošli – KLEPNI pro pokračování; znovu: nabídka → Měření)"
	# výsledek zůstává, dokud se neklepne (dřív 20 s a pak ho překryla nabídka – Míša 12. 11.: „nemám data z měření“)
	var kryt := ColorRect.new(); kryt.color = Color(0, 0, 0, 0.55); kryt.set_anchors_preset(Control.PRESET_FULL_RECT); add_child(kryt); move_child(kryt, 0)
	var klep := [false]
	kryt.gui_input.connect(func(e: InputEvent) -> void:
		if (e is InputEventScreenTouch and e.pressed) or (e is InputEventMouseButton and e.pressed): klep[0] = true)
	while not klep[0] and OS.get_environment("PUCHART_MERENI_BEZ_CEKANI") == "":
		await get_tree().process_frame
	kryt.queue_free()
	lbl.text = ""
	if not OS.has_feature("pc") and FileAccess.file_exists("res://data/rozpocty.json"):   # procházka s limitem snímků (Havran 0.99991: teplo)
		Engine.max_fps = int(JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json")).get("snimky_max", {}).get("tablet", 0))
	var reg := get_tree().get_first_node_in_group("regulator")
	if reg: reg.zapni()   # po měření zase automatika (stupeň 0)
	konec.emit()
	var f := FileAccess.open("user://mereni.txt", FileAccess.WRITE)
	if f: f.store_string(txt); f.close()
	print(txt)
	print("MERENI_KONEC úseků %d" % useky.size())
	if OS.get_environment("PUCHART_MERENI_RYCHLE") != "":   # hlídač: chvíli procházky po měření (předání kamery), pak konec
		await get_tree().create_timer(5.0).timeout
		get_tree().quit()
