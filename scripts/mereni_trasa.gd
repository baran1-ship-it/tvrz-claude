extends Node
const Pravidla := preload("res://scripts/pravidla.gd")
## Meřicí trasa (prevzato z Pucharta hra/scripts/mereni.gd, Misa 2. 11.: „zapnu test, proleti mista, na konci data“):
## kamera (a s ni hrac, at se louka a rostliny nacitaji jako pri hre) projede useky z pravidla/svet/mereni_trasa.json,
## kazdy zahrati + mereni; delka snimku ze skutecnych razitek, p50/p95/max, zaseky > 40 ms, kresleni, troj., VRAM.
## „varianty“: cela trasa znovu s jednou vypnutou skupinou (main._ab_skupiny: stiny, louka, rostliny...) - z jedne tabulky
## je videt, co sekani zpusobuje, na kazdem useku. Na konci tabulka na obrazovce (vyfotit) + user://mereni_trasa.txt.

var main: Node
var cfg: Dictionary
var useky: Array = []
var varianty: Array = []
var i_var := 0
var i_us := 0
var t := 0.0
var casy := PackedFloat32Array()
var kres := 0.0
var troj := 0.0
var vz := 0
var _posl := 0
var lbl: Label
var vysledky: Array = []
var _skup: Dictionary
var _sc0 := 1.0
var proc := 0.0
var fyz := 0.0
var gpu := 0.0
var cpu_r := 0.0
var nej: Dictionary = {}                 # nejhorsi snimek useku: ms, skripty, fyzika, gpu, kresleni
var spicky: Array = []                   # snimky nad spicka_ms (cely beh): kde, kolik, rozpad
var nad100 := 0
var _pozice0: Transform3D
var _let0 := false
var _panel0: Array = [false, false]
var _kv0 := false                         # automaticka kvalita pred trasou (behem trasy vypnuta, varianta „auto“ ji zapne)
var _hod0 := -1.0                        # denni doba stoji (0.9991: trasa 30 min, ves uz za soumraku - jine stiny)


func zacni(m: Node) -> void:
	main = m
	cfg = Pravidla.soubor("mereni_trasa")
	useky = cfg["useky"]
	varianty = cfg.get("varianty", [""])
	_skup = main._ab_skupiny()
	# automaticka kvalita vypnuta: meri se pevne varianty (kvalita.json popis); vrati se na konci
	if main.kvalita:
		_kv0 = main.kvalita.zapnuto
		main.kvalita.nastav(false)
	_sc0 = get_viewport().scaling_3d_scale
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	# hrac musi stat (kun by mu kazdy krok prepsal polohu na sedlo), poloha a let se po konci vrati (kontrola 2. 11.)
	var pl: Node = main.player
	if pl.na_koni and pl.na_koni.has_method("sesedni"):
		pl.na_koni.sesedni()
	if pl.seated:
		pl.stand_up()
	_pozice0 = pl.global_transform
	_let0 = pl.flying
	if main.ab_vyp != "":
		(_skup0()[main.ab_vyp] as Callable).call(true)
		main.ab_vyp = ""
	pl.set_physics_process(false)
	pl.flying = true
	var cl := CanvasLayer.new()
	cl.layer = 20
	lbl = Label.new()
	lbl.position = Vector2(30, 140)
	lbl.add_theme_font_size_override("font_size", 24)
	lbl.add_theme_color_override("font_outline_color", Color.BLACK)
	lbl.add_theme_constant_override("outline_size", 6)
	cl.add_child(lbl)
	add_child(cl)
	_hod0 = main.day.hour if main.day else -1.0
	_panel0 = [main.mereni_on, main.mereni_fps]
	main.mereni_on = false                  # plny panel sam stoji 7-10 ms (3. 11.) - behem trasy vypnut
	main.mereni_fps = false
	_varianta(true)
	_posl = Time.get_ticks_usec()


func _skup0() -> Dictionary:
	return main._ab_skupiny()


func _varianta(zap: bool) -> void:
	var v := String(varianty[i_var])
	if v == "karty_cele":                   # karty travy bez orezu (A/B orezu karet, Misa 4. 11.)
		var lo: Node = main.get_node_or_null("Louka")
		if lo:
			lo.nastav_orez_karet(not zap)
	elif v == "louka_un" or v == "louka_stin":  # trava bez / se stinovym pruchodem slunce (mereni 0.9999)
		var lu: Node = main.get_node_or_null("Louka")
		if lu:
			lu.nastav_unshaded((v == "louka_un") if zap else bool(lu._un0))
	elif v == "trava_gpu":                    # prototyp travy GPU (A/B s loukou)
		var tg: Node = main.get_node_or_null("TravaGPU")
		if tg:
			tg.zapni(zap)
	elif v.begins_with("trava_"):              # kratsi dosah trsu (m) - Misa 3. 11.: louka nejvetsi naklad
		var lk: Node = main.get_node_or_null("Louka")
		if lk:
			lk.nastav_dosah_trsu(float(v.substr(6)) if zap else -1.0)
	elif v == "auto":                          # automaticka kvalita zapnuta (overeni smycky, zmeny stupne v tabulce)
		if main.kvalita:
			main.kvalita.nastav(zap)
	elif v.begins_with("3d_"):                 # rozliseni 3D v % soucasneho: roste-li FPS, brzdi vyplnovani pixelu (GPU)
		get_viewport().scaling_3d_scale = _sc0 * float(v.substr(3)) / 100.0 if zap else _sc0
	elif v != "" and _skup.has(v):
		(_skup[v] as Callable).call(not zap)


func _jm(v: String) -> String:
	if v == "":
		return "vše" if varianty.find("") == i_var else "vše znovu"
	if v == "auto":
		return "auto -%d" % (main.kvalita.stupen if main.kvalita else 0)
	if v.begins_with("3d_"):
		return "3D x" + v.substr(3) + "%"
	if v == "trava_gpu":
		return "tráva GPU"
	if v == "louka_un":
		return "tráva bez stínu"
	if v == "louka_stin":
		return "tráva se stínem"
	if v == "karty_cele":
		return "karty bez ořezu"
	if v.begins_with("trava_"):
		return "tráva " + v.substr(6) + "m"
	return String(main.AB_NAZVY.get(v, v)).substr(0, 10)


func _bod(u: Dictionary, f: float) -> Array:
	var a: Array = u["od"]
	var b: Array = u["do"]
	var c: Array = u["cil"]
	var x := lerpf(float(a[0]), float(b[0]), f)
	var z := lerpf(float(a[1]), float(b[1]), f)
	var p := Vector3(x, main.svet._vyska(x, z) + float(u.get("nad", 1.7)), z)
	var cc := Vector3(float(c[0]), main.svet._vyska(float(c[0]), float(c[1])) + float(c[2]), float(c[1]))
	return [p, cc]


func _process(d: float) -> void:
	if i_var >= varianty.size():
		return
	var now := Time.get_ticks_usec()
	var ms := (now - _posl) / 1000.0
	_posl = now
	var u: Dictionary = useky[i_us]
	if _hod0 >= 0.0 and absf(main.day.hour - _hod0) > 0.05:
		main.day.set_hour(_hod0, 0.0)
	t += d
	var zah := float(cfg.get("zahrati_s", 5.0))
	var celk := zah + float(cfg.get("mereni_s", 20.0))
	var pc: Array = _bod(u, clampf(t / celk, 0.0, 1.0))
	main.player.global_position = (pc[0] as Vector3) - Vector3(0, 1.6, 0)
	main.player.cam.global_transform = Transform3D(Basis.looking_at((pc[1] as Vector3) - (pc[0] as Vector3), Vector3.UP), pc[0])
	var vrid := get_viewport().get_viewport_rid()
	# merene skripty (diag: soucet _process systemu za minuly snimek); Performance.TIME_PROCESS je cely snimek, ne skripty
	# (0.9995: sloupec skr = 18-29 ms = delka snimku)
	var pr: float = main.diag._skripty_us() / 1000.0 if main.diag and main.diag.has_method("_skripty_us") else 0.0
	var fy := Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
	var gp := RenderingServer.viewport_get_measured_render_time_gpu(vrid)
	var cr := RenderingServer.viewport_get_measured_render_time_cpu(vrid)
	var kr := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
	# spicky v cele trase (i pri zahrati - tam byva kompilace shaderu a nacitani)
	if ms > float(cfg.get("spicka_ms", 200.0)) and spicky.size() < 12:
		spicky.append("%.0f ms %s %s/%s u (%.0f, %.0f): skripty %.0f fyzika %.0f gpu %.0f kresleni %d, uzly %d" % [ms,
				"zahrati" if t <= zah else "mereni", String(varianty[i_var]), u["jmeno"], (pc[0] as Vector3).x, (pc[0] as Vector3).z,
				pr, fy, gp, kr, int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))])
	if t > zah:
		casy.append(ms)
		kres += kr
		troj += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
		proc += pr
		fyz += fy
		gpu += gp
		cpu_r += cr
		vz += 1
		if ms > 100.0:
			nad100 += 1
		if ms > float(nej.get("ms", 0.0)):
			nej = {"ms": ms, "pr": pr, "fy": fy, "gp": gp, "kr": kr}
	var vn := String(varianty[i_var])
	lbl.text = "MĚŘICÍ TRASA – varianta %d/%d: %s   úsek %d/%d: %s   %.0f s" % [i_var + 1, varianty.size(), _jm(vn),
			i_us + 1, useky.size(), u["jmeno"], celk - t]
	if t < celk:
		return
	var s := casy.duplicate()
	s.sort()
	var n := maxi(s.size(), 1)
	var zas := 0
	for x in s:
		if x > 40.0:
			zas += 1
	vysledky.append({"var": _jm(vn) if vn != "louka" else "bez trávy",  # nazev v okamziku mereni (0.9998: prvni „vse“ se vypsalo jako „vse znovu“)
			 "us": String(u["jmeno"]), "p50": s[n / 2] if s.size() > 0 else 0.0,
			"p95": s[mini(int(n * 0.95), n - 1)] if s.size() > 0 else 0.0, "max": s[n - 1] if s.size() > 0 else 0.0,
			"zas": zas, "n": s.size(), "kres": kres / maxf(vz, 1), "troj": troj / maxf(vz, 1) / 1e6,
			"vram": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0,
			"proc": proc / maxf(vz, 1), "fyz": fyz / maxf(vz, 1), "gpu": gpu / maxf(vz, 1), "cpur": cpu_r / maxf(vz, 1),
			"n100": nad100, "nej": nej, "halda": OS.get_static_memory_usage() / 1048576.0,
			"tex": Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0,
			"buf": Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0,
			"uzly": int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))})
	proc = 0.0
	fyz = 0.0
	gpu = 0.0
	cpu_r = 0.0
	nad100 = 0
	nej = {}
	_uloz()                                   # po kazdem useku (0.9991: trasa nedobehla do konce = tabulka ztracena)
	casy = PackedFloat32Array()
	kres = 0.0
	troj = 0.0
	vz = 0
	t = 0.0
	i_us += 1
	if i_us >= useky.size():
		_varianta(false)
		i_us = 0
		i_var += 1
		if i_var < varianty.size():
			_varianta(true)
		else:
			_konec()


func _uloz(hotovo := false) -> void:
	var txt := _tabulka()
	if not hotovo:
		txt = "(trasa nedokončena: %d z %d úseků)\n" % [vysledky.size(), useky.size() * varianty.size()] + txt
	var f := FileAccess.open("user://mereni_trasa.txt", FileAccess.WRITE)
	if f:
		f.store_string(txt)
		f.close()


func _tabulka() -> String:
	var vp := get_viewport().get_visible_rect().size
	var txt := "(skr = měřené skripty; gpu/cpuR = 0, když je zařízení neměří)\nVÝSLEDEK měřicí trasy %s · %s · obrazovka %dx%d, 3D %d %%\n" % [Time.get_datetime_string_from_system(),
			main.diag.sestaveni_text() if main.diag and main.diag.has_method("sestaveni_text") else "", int(vp.x), int(vp.y), roundi(_sc0 * 100)]
	txt += "varianta   úsek      p50 p95 max >40 >100 kresl trojM skr fyz gpu cpuR | nejhorší: ms skr fyz gpu kresl\n"
	for r: Dictionary in vysledky:
		var nj: Dictionary = r["nej"]
		txt += "%-10s %-8s %3.0f %3.0f %3.0f %3d %4d %5.0f %5.2f %3.0f %3.0f %3.0f %3.0f | %3.0f %3.0f %3.0f %3.0f %4d\n" % [
				String(r["var"]), r["us"], r["p50"], r["p95"], r["max"], r["zas"], r["n100"], r["kres"], r["troj"],
				r["proc"], r["fyz"], r["gpu"], r["cpur"], float(nj.get("ms", 0)), float(nj.get("pr", 0)), float(nj.get("fy", 0)),
				float(nj.get("gp", 0)), int(nj.get("kr", 0))]
	var z: Dictionary = vysledky[-1] if not vysledky.is_empty() else {}
	txt += "paměť: VRAM %.0f MB (textury %.0f, buffery %.0f), halda %.0f MB, uzlů %d\n" % [float(z.get("vram", 0)),
			float(z.get("tex", 0)), float(z.get("buf", 0)), float(z.get("halda", 0)), int(z.get("uzly", 0))]
	txt += "špičky nad %.0f ms (%d):\n" % [float(cfg.get("spicka_ms", 200.0)), spicky.size()]
	for sp: String in spicky:
		txt += "  " + sp + "\n"
	if main.kvalita and not main.kvalita.historie.is_empty():
		txt += "automatická kvalita – změny (%d):\n" % main.kvalita.zmen
		for h: String in main.kvalita.historie:
			txt += "  " + h + "\n"
	return txt


func _konec() -> void:
	var txt := _tabulka()
	_uloz(true)
	lbl.text = txt + "\n(ms na snímek; tabulka je ve schránce – vlož ji do chatu. Zpět do hry za 60 s.)"
	print(txt)
	DisplayServer.clipboard_set(txt)
	await get_tree().create_timer(60.0).timeout
	main.player.global_transform = _pozice0
	main.player.set_flying(_let0)
	main.player.velocity = Vector3.ZERO
	main.player.set_physics_process(true)
	main.mereni_on = bool(_panel0[0])
	main.mereni_fps = bool(_panel0[1])
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), false)
	if main.kvalita:
		main.kvalita.nastav(_kv0)
	queue_free()
