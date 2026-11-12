extends Node
## Deník běhu (Míša 12. 11.: „pořád to padá“ – pád bez hlášení, ladicí symboly pro naši šablonu nejsou): každý krok startu
## a každých 5 s paměť se zapíše do user://denik.txt (soubor se po každém řádku zavře – zápis přežije pád). Když minulý běh
## neskončil řádkem KONEC_OK (pád, zabití systémem), uloží se jako user://denik_minule.txt a jeho konec se ukáže na obrazovce
## – je vidět poslední krok před pádem a kolik bylo paměti.

const SOUBOR := "user://denik.txt"
const MINULE := "user://denik_minule.txt"
var _t := 0.0
var _t0 := 0

static func pamet() -> String:
	var mi := OS.get_memory_info()
	return "halda %d MB, volná RAM %d / %d MB" % [OS.get_static_memory_usage() / 1048576, int(mi.get("available", -1)) / 1048576, int(mi.get("physical", -1)) / 1048576]

static func zapis(krok: String) -> void:
	var f := FileAccess.open(SOUBOR, FileAccess.READ_WRITE) if FileAccess.file_exists(SOUBOR) else FileAccess.open(SOUBOR, FileAccess.WRITE)
	if f == null: return
	f.seek_end()
	f.store_line("%7.1f s  %s  | %s" % [Time.get_ticks_msec() / 1000.0, krok, pamet()])
	f.close()

## Na začátku hry: minulý deník bez KONEC_OK = pád → ukázat jeho konec; pak nový deník.
func zacni(rodic: Node) -> void:
	_t0 = Time.get_ticks_msec()
	if FileAccess.file_exists(SOUBOR):
		var minule := FileAccess.get_file_as_string(SOUBOR)
		if not minule.contains("KONEC_OK"):
			var f := FileAccess.open(MINULE, FileAccess.WRITE)
			if f: f.store_string(minule); f.close()
			if OS.get_environment("PUCHART_FOTO") == "" and OS.get_environment("PUCHART_TEST") == "": _ukaz(rodic, minule)   # snímky a testy bez překryvu
	var g := FileAccess.open(SOUBOR, FileAccess.WRITE)
	if g:
		g.store_line("Moravian Battlefield – deník běhu %s, %s %s, %s" % [Time.get_datetime_string_from_system(), OS.get_name(), OS.get_model_name(), RenderingServer.get_video_adapter_name()])
		g.close()

func _ukaz(rodic: Node, text: String) -> void:
	var radky := text.strip_edges().split("\n")
	var konec := "\n".join(radky.slice(maxi(0, radky.size() - 30)))
	var v := CanvasLayer.new(); v.layer = 120; rodic.add_child(v)
	var p := ColorRect.new(); p.color = Color(0, 0, 0, 0.82); p.set_anchors_preset(Control.PRESET_FULL_RECT); v.add_child(p)
	var l := Label.new(); l.position = Vector2(24, 20); l.add_theme_font_size_override("font_size", 17)
	l.text = "Minulé spuštění skončilo pádem. Poslední kroky (vyfoť a pošli):\n\n" + konec + "\n\n(klepni pro pokračování)"
	v.add_child(l)
	p.gui_input.connect(func(e: InputEvent) -> void:
		if (e is InputEventScreenTouch and e.pressed) or (e is InputEventMouseButton and e.pressed): v.queue_free())

func _process(d: float) -> void:
	_t += d
	if _t >= 5.0:
		_t = 0.0
		zapis("běží, snímků %d" % Engine.get_process_frames())

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_PREDELETE:
		zapis("KONEC_OK")
