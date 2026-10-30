extends Node
## Měřicí trasa (PDF kap. 13 „stejná cesta, stejné podmínky“): kamera proletí 4 úseky – hrad, les, voda, vyhlídka –
## každý zahřátí 5 s + měření 30 s. Na konci tabulka na obrazovce + user://mereni.txt. Spouští se, když existuje
## res://data/mereni.json (měřicí APK) nebo PUCHART_MERENI=1.
## Délka snímku = skutečná razítka (ne vyhlazené delta – poučení Havrana), p50/p95/max, záseky > 40 ms.

var trasa: Array
var cam: Camera3D
var svet: Node3D
var useky := []
var i_usek := 0
var t := 0.0
var casy := PackedFloat32Array()
var kres := 0.0
var troj := 0.0
var vzorku := 0
var _posl := 0
var lbl: Label
var verze := ""
signal konec

func zacni(s: Node3D, kamera: Camera3D) -> void:
	svet = s; cam = kamera
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/mereni.json"))
	trasa = cfg["useky"]; verze = cfg.get("verze", "") + " / Godot " + Engine.get_version_info()["string"]
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
	var celk := 5.0 + 30.0
	var pc := _bod(u, clampf(t / celk, 0.0, 1.0))
	cam.look_at_from_position(pc[0], pc[1], Vector3.UP)
	if t > 5.0:
		casy.append(ms)
		kres += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
		troj += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
		vzorku += 1
	lbl.text = "MĚŘENÍ %s\núsek %d/%d: %s  %.0f s" % [verze, i_usek + 1, trasa.size(), u["jmeno"], celk - t]
	if t >= celk:
		var s := casy.duplicate(); s.sort()
		var n := s.size()
		var zas := 0
		for x in s:
			if x > 40.0: zas += 1
		useky.append({"jmeno": u["jmeno"], "p50": s[n / 2], "p95": s[int(n * 0.95)], "max": s[n - 1], "zaseky": zas,
			"snimku": n, "kresleni": kres / vzorku, "troj_m": troj / vzorku / 1e6,
			"vram_mb": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0,
			"halda_mb": OS.get_static_memory_usage() / 1048576.0})
		casy = PackedFloat32Array(); kres = 0; troj = 0; vzorku = 0; t = 0.0
		i_usek += 1
		if i_usek >= trasa.size():
			_konec()

func _konec() -> void:
	var txt := "VÝSLEDEK %s\n%s\n" % [verze, Time.get_datetime_string_from_system()]
	txt += "úsek        p50   p95   max  záseky  snímků  kreslení  troj M  VRAM MB  halda MB\n"
	for u in useky:
		txt += "%-10s %5.1f %5.1f %5.0f %6d %7d %8.0f %7.2f %8.0f %9.0f\n" % [u["jmeno"], u["p50"], u["p95"], u["max"], u["zaseky"], u["snimku"], u["kresleni"], u["troj_m"], u["vram_mb"], u["halda_mb"]]
	lbl.text = txt + "\n(ms na snímek; vyfoť obrazovku a pošli – za 20 s začne procházka)"
	await get_tree().create_timer(20.0).timeout
	lbl.text = ""
	konec.emit()
	var f := FileAccess.open("user://mereni.txt", FileAccess.WRITE)
	if f: f.store_string(txt); f.close()
	print(txt)
