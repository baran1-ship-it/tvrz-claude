extends Node
## Hlidac vykonu: kazde 2 s zapise do user://diag.log stav hry (FPS, pamet, graficka pamet, trojuhelniky,
## volani kresleni, objekty, poloha hrace, bunky louky). Pri startu pozna, ze hra minule spadla
## (nezmizel znacka "bezi"), a zpravu o padu (posledni zaznamy + chyby z logu Godotu) ukaze a zkopiruje do schranky.

const LOG := "user://diag.log"
const ZNACKA := "user://diag_bezi"
const MAX_RADKU := 400

var main: Node
var _t := 0.0
var _radky: PackedStringArray = []
var _start := 0


func setup(p_main: Node) -> void:
	main = p_main
	process_mode = Node.PROCESS_MODE_ALWAYS
	_start = Time.get_ticks_msec()
	var zprava := ""
	if FileAccess.file_exists(ZNACKA):
		zprava = _zprava_o_padu()
	# minuly zaznam stranou, novy zacina
	if FileAccess.file_exists(LOG):
		DirAccess.rename_absolute(LOG, "user://diag_minule.log")
	_oznac(true)
	if zprava != "":
		DisplayServer.clipboard_set(zprava)
		print(zprava)
		await get_tree().create_timer(4.0).timeout
		if main.hud:
			main.hud.toast("Hra minule spadla. Zpráva o pádu je zkopírovaná – vlož ji do chatu.", 8.0)


func _oznac(bezi: bool) -> void:
	if bezi:
		var f := FileAccess.open(ZNACKA, FileAccess.WRITE)
		if f:
			f.store_string(Time.get_datetime_string_from_system())
	elif FileAccess.file_exists(ZNACKA):
		DirAccess.remove_absolute(ZNACKA)


func _notification(what: int) -> void:
	# radne ukonceni nebo odchod do pozadi (Android pak muze aplikaci zavrit) neni pad
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_PREDELETE:
		_zapis("konec/pauza")
		_oznac(false)
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		_oznac(true)


func _process(dt: float) -> void:
	_t += dt
	if _t < 2.0:
		return
	_t = 0.0
	_zapis("")


func _zapis(pozn: String) -> void:
	var p := Vector3.ZERO
	if main and main.player:
		p = main.player.global_position
	var louka: Node = main.get_node_or_null("Louka") if main else null
	var bunky := ""
	if louka:
		bunky = "louka %d/%d/%d+%d" % [louka._bliz.size(), louka._dal.size(), louka._kupy[0].size(), louka._kupy[1].size()]
	var r := "%ds fps %d | ram %d MB (max %d) | gpu %d MB | troj %.1f M | kresleni %d | obj %d | uzly %d | %s | hrac %d,%d,%d %s" % [
		(Time.get_ticks_msec() - _start) / 1000,
		Engine.get_frames_per_second(),
		OS.get_static_memory_usage() / 1048576, OS.get_static_memory_peak_usage() / 1048576,
		Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0,
		Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000000.0,
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		bunky, p.x, p.y, p.z, pozn]
	_radky.append(r)
	if _radky.size() > MAX_RADKU:
		_radky = _radky.slice(_radky.size() - MAX_RADKU)
	# prepsat cely soubor (maly) a hned zavrit: pri padu zustane posledni zapsany stav
	var f := FileAccess.open(LOG, FileAccess.WRITE)
	if f:
		f.store_string("\n".join(_radky) + "\n")
		f.close()


func _zprava_o_padu() -> String:
	var out := "ZPRAVA O PADU (Odkaz Havrana %s, %s)\n" % [ProjectSettings.get_setting("application/config/version", "?"), OS.get_model_name()]
	var f := FileAccess.open(LOG, FileAccess.READ)
	if f:
		var lines := f.get_as_text().strip_edges().split("\n")
		out += "posledni zaznamy:\n" + "\n".join(lines.slice(maxi(0, lines.size() - 12))) + "\n"
	# chyby a varovani z logu Godotu (predchozi beh)
	var dir := DirAccess.open("user://logs")
	if dir:
		var soubory: Array = []
		for n in dir.get_files():
			if n.ends_with(".log"):
				soubory.append(n)
		soubory.sort()
		# nejnovejsi je log tohoto spusteni, predchozi beh je predposledni (nebo godot.log pred prejmenovanim)
		if soubory.size() >= 2:
			var g := FileAccess.open("user://logs/" + String(soubory[soubory.size() - 2]), FileAccess.READ)
			if g:
				var chyby: PackedStringArray = []
				for l in g.get_as_text().split("\n"):
					if l.contains("ERROR") or l.contains("WARNING") or l.contains("memory") or l.contains("Out of"):
						chyby.append(l.strip_edges())
				if not chyby.is_empty():
					out += "chyby z logu:\n" + "\n".join(chyby.slice(maxi(0, chyby.size() - 10))) + "\n"
	return out
