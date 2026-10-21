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
var _panel: Label
var _tp := 0.0


func setup(p_main: Node) -> void:
	main = p_main
	process_mode = Node.PROCESS_MODE_ALWAYS
	_start = Time.get_ticks_msec()
	# panel mereni vykonu (zapina se v nastaveni): levy horni roh, aktualizace 2x za sekundu
	var cl := CanvasLayer.new()
	cl.layer = 50
	add_child(cl)
	_panel = Label.new()
	_panel.position = Vector2(16, 12)
	_panel.add_theme_font_size_override("font_size", 20)
	_panel.add_theme_color_override("font_color", Color(1, 1, 0.85))
	_panel.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	_panel.add_theme_constant_override("outline_size", 5)
	cl.add_child(_panel)
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
		await get_tree().create_timer(1.5).timeout
		# systemove okno (funguje uz v menu, pred nactenim sveta)
		OS.alert("Hra minule spadla. Zpráva o pádu je zkopírovaná do schránky – vlož ji do chatu.\n\n" + _konec(zprava), "Odkaz Havrana – pád")


## Do okna konec zpravy (posledni zaznamy pred padem a chyby z logu), ne zacatek - cela je ve schrance.
func _konec(z: String) -> String:
	if z.length() <= 900:
		return z
	return z.get_slice("\n", 0) + "\n…\n" + z.right(850)


## Faze nacitani: zapise se hned (pri padu behem nacitani je videt, kde hra skoncila).
func faze(t: String) -> void:
	_zapis("FAZE " + t)


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


var _max_dt := 0.0                    # nejdelsi snimek za posledni 2 s (sekani: plynule nizke FPS = GPU, spicky = zasek)
var _max_dt_panel := 0.0
var _cpu_max := 0.0                   # nejdelsi cas procesu (hlavni vlakno) za 2 s


func _process(dt: float) -> void:
	_panel.visible = bool(main.get("mereni_on"))
	_max_dt = maxf(_max_dt, dt)
	_max_dt_panel = maxf(_max_dt_panel, dt)
	_cpu_max = maxf(_cpu_max, Performance.get_monitor(Performance.TIME_PROCESS))
	_tp += dt
	if _panel.visible and _tp >= 0.5:
		_tp = 0.0
		_panel.text = "FPS %d  (%.1f ms, nejdelší %.0f ms)\nkreslení %d\ntrojúhelníky %.2f M\nobjekty %d\nRAM %d MB (volná %d) · GPU %d MB (textury %d, buffery %d)\n%s" % [
			Engine.get_frames_per_second(), 1000.0 / maxf(1.0, Engine.get_frames_per_second()), _max_dt_panel * 1000.0,
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000000.0,
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			_ram, _volna, Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0,
			Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0, Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0,
			_rust_text()]
		_max_dt_panel = 0.0
	_kontrola_rozpoctu()
	_t += dt
	if _t < 2.0:
		return
	_t = 0.0
	_zapis("")
	_max_dt = 0.0
	_cpu_max = 0.0


var _ram := 0
var _ram_max := 0
var _ram_hist: Array = []              # [cas s, ram MB] po 2 s, poslednich 30 s


## Rust RAM za poslednich 30 s v MB/min + rezim testu pameti (main.test_pameti).
func _rust_text() -> String:
	var t := ""
	if _ram_hist.size() >= 2:
		var a: Array = _ram_hist[0]
		var b: Array = _ram_hist[-1]
		t = "RAM %+.0f MB/min" % ((float(b[1]) - float(a[1])) / maxf(float(b[0]) - float(a[0]), 1.0) * 60.0)
	if main and int(main.get("test_pameti")) > 0:
		t += "  · test: " + String(main.TEST_PAMETI[int(main.test_pameti)])
	return t


## RAM procesu (MB). Ve vydani OS.get_static_memory_usage() vraci 0 a /proc/self/statm se na Androidu cte pres
## Java vrstvu s delkou 0 (0.59 panel porad 0) -> Android: nativni halda (android.os.Debug, rychle - tam selhava
## malloc) a volna pamet systemu; jinde rezidentni pamet z /proc/self/statm.
var _dbg: Variant = null
var _volna := -1


func ram_mb() -> int:
	if OS.get_name() == "Android":
		if _dbg == null:
			_dbg = JavaClassWrapper.wrap("android.os.Debug")
		if _dbg != null:
			_ram = int(_dbg.getNativeHeapAllocatedSize()) / 1048576
		var mi := OS.get_memory_info()
		var vol := int(mi.get("available", -1))
		if vol <= 0:
			vol = int(mi.get("free", -1))          # tablet 0.59b: available chybi (panel "volna 0")
		_volna = vol / 1048576
	else:
		var f := FileAccess.open("/proc/self/statm", FileAccess.READ)
		if f:
			var sl := f.get_line().split(" ")
			f.close()
			if sl.size() > 1:
				_ram = int(sl[1]) * 4096 / 1048576
	if _ram <= 0:
		_ram = OS.get_static_memory_usage() / 1048576
	_ram_max = maxi(_ram_max, _ram)
	return _ram


## ROZPOCET na snimek (zadani 16. 10.): pri prekroceni o 50 % varovani s pozici hrace do user://diag_varovani.log
const MAX_KRESLENI := 1500
const MAX_TROJ := 2000000
var _varovano := 0.0


func _kontrola_rozpoctu() -> void:
	var dc := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	var tr := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	if (dc > MAX_KRESLENI * 1.5 or tr > MAX_TROJ * 1.5) and Time.get_ticks_msec() / 1000.0 - _varovano > 5.0:
		_varovano = Time.get_ticks_msec() / 1000.0
		var p := Vector3.ZERO
		if main and main.player:
			p = main.player.global_position
		var t := "VAROVANI rozpocet: kresleni %d (max %d), troj %.2f M (max %.1f M), hrac %d,%d,%d" % [dc, MAX_KRESLENI, tr / 1e6, MAX_TROJ / 1e6, p.x, p.y, p.z]
		push_warning(t)
		var f := FileAccess.open("user://diag_varovani.log", FileAccess.READ_WRITE if FileAccess.file_exists("user://diag_varovani.log") else FileAccess.WRITE)
		if f:
			if f.get_length() < 200000:
				f.seek_end()
				f.store_line(Time.get_datetime_string_from_system() + " " + t)
			f.close()


func _zapis(pozn: String) -> void:
	var p := Vector3.ZERO
	if main and main.player:
		p = main.player.global_position
	var louka: Node = main.get_node_or_null("Louka") if main else null
	var bunky := ""
	if louka:
		bunky = "louka %d (+%d) / %d+%d, postaveno %d / kupy %d" % [louka._bunky.size(), louka._ceka.size(), louka._kupy[0].size(), louka._kupy[1].size(),
				louka.postaveno, louka.postaveno_kupy]
	ram_mb()
	_ram_hist.append([(Time.get_ticks_msec() - _start) / 1000.0, _ram])
	while _ram_hist.size() > 16:
		_ram_hist.pop_front()
	if _ram > 1200 and Time.get_ticks_msec() / 1000.0 - _varovano > 5.0:
		_varovano = Time.get_ticks_msec() / 1000.0
		push_warning("VAROVANI RAM %d MB (prah 1200)" % _ram)
	var r := "%ds fps %d (nejdelsi snimek %.0f ms, proces max %.1f ms) | ram %d MB (max %d, volna %d) | gpu %d MB (tex %d, buf %d) | troj %.1f M | kresleni %d | obj %d | uzly %d (objekty %d, zdroje %d, sirotci %d) | %s | hrac %d,%d,%d %s" % [
		(Time.get_ticks_msec() - _start) / 1000,
		Engine.get_frames_per_second(), _max_dt * 1000.0, _cpu_max * 1000.0,
		_ram, _ram_max, _volna,
		Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0,
		Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0,
		Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0,
		Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000000.0,
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		Performance.get_monitor(Performance.OBJECT_NODE_COUNT), Performance.get_monitor(Performance.OBJECT_COUNT),
		Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT), Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT),
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
	# chyby z logu Godotu (predchozi beh): aktualni je godot.log, starsi godot<datum>.log - nejnovejsi z nich
	# (0.59: razeni bralo "predposledni", tedy beh pred padlym - ve zprave byla cizi varovani)
	var dir := DirAccess.open("user://logs")
	if dir:
		var soubory: Array = []
		for n in dir.get_files():
			if n.ends_with(".log") and n != "godot.log":
				soubory.append(n)
		soubory.sort()
		if not soubory.is_empty():
			var g := FileAccess.open("user://logs/" + String(soubory[-1]), FileAccess.READ)
			if g:
				var chyby: PackedStringArray = []
				for l in g.get_as_text().split("\n"):
					if l.contains("invalid UID") or l.contains("VAROVANI rozpocet"):
						continue                 # neskodna varovani importu (cesta misto UID) zahlcovala zpravu
					if l.contains("ERROR") or l.contains("WARNING") or l.contains("memory") or l.contains("Out of") or l.contains("   at: "):
						chyby.append(l.strip_edges())
				if not chyby.is_empty():
					out += "chyby z logu (%s):\n" % soubory[-1] + "\n".join(chyby.slice(maxi(0, chyby.size() - 14))) + "\n"
	# posledni zaznamy diagnostiky na konec (okno ukazuje konec zpravy): cas, RAM, misto, bunky louky
	var f := FileAccess.open(LOG, FileAccess.READ)
	if f:
		var lines := f.get_as_text().strip_edges().split("\n")
		out += "posledni zaznamy:\n" + "\n".join(lines.slice(maxi(0, lines.size() - 6))) + "\n"
	return out
