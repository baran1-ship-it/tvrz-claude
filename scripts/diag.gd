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
	p_main.get_tree().node_added.connect(_pridan)
	# casova osa snimku (overeni 16:45): Performance.TIME_PHYSICS_PROCESS je v 4.4 maximum JEDNOHO kroku za posledni
	# sekundu (main.cpp: physics_process_max, nastavi se 1x za s) - pro zasek nepouzitelne. Vlastni razitka:
	# physics_frame / process_frame (SceneTree je vysila pred uzly) a konec diag._process (bezi posledni).
	p_main.get_tree().physics_frame.connect(_na_fyziku)
	p_main.get_tree().process_frame.connect(_na_process)
	main = p_main
	Engine.set_meta("diag", self)
	process_priority = 100000              # bezi po vsech ostatnich _process: snimek je zmereny cely
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
		_zapis_zaseky(true)
		_oznac(false)
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		_oznac(true)


var _max_dt := 0.0                    # nejdelsi snimek za posledni 2 s (sekani: plynule nizke FPS = GPU, spicky = zasek)
var _max_dt_panel := 0.0
var _cpu_max := 0.0                   # nejdelsi cas procesu (hlavni vlakno) za 2 s
# 0.64 (Misa: stale sekani, nejdelsi snimek 100-145 ms): rozpad nejdelsiho snimku za 0,5 s na panelu - skripty,
# fyzika, priprava kresleni (CPU), GPU; pocet spicek > 50 ms. Kdo z nich je velky, ten seka.
var _sp := [0.0, 0.0, 0.0, 0.0, 0.0]  # [snimek, skripty, fyzika, priprava CPU, GPU] v ms
var _sp_n := 0
var _gpu_sum := 0.0
var _gpu_n := 0
var _mereni_rt := false
# Misa 0.84 „sem tam se to zasekne na vterinku“: spicka se na panelu drzi jen 0,5 s - posledni 3 zaseky nad 100 ms
# zustavaji (cas, kde, rozpad), aby byly na fotce panelu
var _zaseky: Array = []
var zaseku := 0                       # pocet zaseku od startu (panel, log)
const ZASEK := 0.04                   # radce 16:45: jeden prah 40 ms pro zaznam i pocitadlo spicek


## Soucet casu skriptu za minuly snimek bez podrobnosti (klic s ":" je cast jineho mereni - napr. "main: planovac"
## je uvnitr "main"; radce 16:45 bod 1: planovac se pocital dvakrat).
func _skripty_us() -> float:
	var skr := 0.0
	for k: String in _cas_minule:
		if not k.contains(":"):
			skr += float(_cas_minule[k])
	return skr


## Detektor zaseku (radce 16:45 bod 3): kazdy snimek nad 40 ms = zaznam, i v rezimu „jen FPS“ (lehky - bez seznamu
## uzlu); pricina = nejvetsi z fyzika / kresleni CPU / skripty (+ nejdrazsi system) / planovac / louka. Zapis do logu
## ve vlakne (bod 2).
## Razitka snimku: [zacatek, fyzika us (vsechny kroky), kroku, _process us, konec _process] + udaje k nemu
var _t_fyz0 := 0                         # zacatek prvniho kroku fyziky tohoto snimku
var _kroku := 0
var _t_proc0 := 0
var _sn := {}                            # rozpis predchoziho (uz uzavreneho) snimku
var _sn_ted := {}                        # rozpisovany snimek


func _na_fyziku() -> void:
	if _kroku == 0:
		_t_fyz0 = Time.get_ticks_usec()
	_kroku += 1


func _na_process() -> void:
	var t := Time.get_ticks_usec()
	var zac := _t_fyz0 if _kroku > 0 else t
	# uzavrit predchozi snimek: zbytek od konce _process do zacatku tohoto = kresleni (+ cekani na vsync)
	if not _sn_ted.is_empty():
		_sn_ted["celkem"] = zac - int(_sn_ted["zac"])
		_sn_ted["kresleni"] = zac - int(_sn_ted["konec"])
		_sn = _sn_ted
		_detektor()
	_sn_ted = {"zac": zac, "fyzika": t - zac if _kroku > 0 else 0, "kroku": _kroku, "konec": t}
	_kroku = 0
	_t_proc0 = t


## Konec snimku (posledni _process): skripty tohoto snimku, planovac, nove uzly.
func _konec_snimku() -> void:
	if _sn_ted.is_empty():
		return
	var t := Time.get_ticks_usec()
	_sn_ted["konec"] = t
	_sn_ted["process"] = t - _t_proc0
	_sn_ted["skripty"] = _skripty_us()
	var nej := "-"
	var nv := 0.0
	for k: String in _cas_minule:
		if float(_cas_minule[k]) > nv:
			nv = float(_cas_minule[k])
			nej = k
	_sn_ted["nej"] = nej
	_sn_ted["nej_us"] = nv
	_sn_ted["uzly"] = _okno_geom
	var sv2: Object = main.get("svet") if main else null
	if sv2 and sv2.get("plan_uloha") != null:
		_sn_ted["plan"] = ", plán %.1f ms (%s)" % [float(sv2.get("plan_ms")), String(sv2.get("plan_uloha"))]


## Detektor zaseku: uzavreny snimek nad 40 ms -> zaznam (prave ten snimek, ne o snimek pozdeji). Lehky: jen
## formatovani radku; soubor se zapise ve vlakne nejvys 2x za sekundu (_zapis_zaseky).
func _detektor() -> void:
	var cel := float(_sn.get("celkem", 0)) / 1000.0
	if cel <= ZASEK * 1000.0 or not main or not main.get("ready_done"):
		return
	zaseku += 1
	var fy := float(_sn.get("fyzika", 0)) / 1000.0
	var pc := float(_sn.get("process", 0)) / 1000.0
	var kr := float(_sn.get("kresleni", 0)) / 1000.0
	var pr := "fyzika" if fy >= maxf(kr, pc) else ("kreslení" if kr >= pc else "skripty")
	var z := "%.0f ms (%s) u %s, t %ds: fyzika %.0f (%d kroků), _process %.0f (měřené skripty %.0f, %s %.0f), kreslení+čekání %.0f, nové uzly %d%s%s" % [
			cel, pr, poloha_text().get_slice(" (", 0), int(Time.get_ticks_msec() / 1000), fy, int(_sn.get("kroku", 0)), pc,
			float(_sn.get("skripty", 0)) / 1000.0, String(_sn.get("nej", "-")), float(_sn.get("nej_us", 0)) / 1000.0, kr,
			int(_sn.get("uzly", 0)), String(_sn.get("plan", "")), ", měřič PSS" if bool(_sn.get("pss", false)) else ""]
	if main.player and bool(main.player.get("flying")):
		z += ", LET"                      # rychly pohyb = rychlejsi nacitani okoli (Misa 26. 10.)
	_zaseky.push_front(z)
	_zaseky = _zaseky.slice(0, 3)
	_zaseky_log.append(Time.get_time_string_from_system() + " ZASEK " + z)
	if _zaseky_log.size() > MAX_ZASEKU:
		_zaseky_log = _zaseky_log.slice(_zaseky_log.size() - MAX_ZASEKU)


const MAX_ZASEKU := 300
const LOG_ZASEKY := "user://zaseky.log"
var _zaseky_log: PackedStringArray = []
var _zaseky_zapsano := 0
var _zaseky_t := 0
var _zaseky_uloha := -1
var _zaseky_do_logu := 0


## Soubor zaseku (user://zaseky.log) ve vlakne, nejvys 2x za s; kdyz predchozi zapis bezi, pocka se na dalsi kolo
## (hlavni vlakno nikdy neceka). Bez mereni RAM (to dela pravidelny zapis po 2 s).
func _zapis_zaseky(hned := false) -> void:
	if zaseku == _zaseky_zapsano:
		return
	var t := Time.get_ticks_msec()
	if not hned and t - _zaseky_t < 500:
		return
	if _zaseky_uloha >= 0:
		if not WorkerThreadPool.is_task_completed(_zaseky_uloha) and not hned:
			return
		WorkerThreadPool.wait_for_task_completion(_zaseky_uloha)
		_zaseky_uloha = -1
	_zaseky_t = t
	_zaseky_zapsano = zaseku
	var text := "\n".join(_zaseky_log) + "\n"
	if hned:
		_zapis_soubor_do(LOG_ZASEKY, text)
	else:
		_zaseky_uloha = WorkerThreadPool.add_task(_zapis_soubor_do.bind(LOG_ZASEKY, text))


func _process(dt: float) -> void:
	var d0 := Time.get_ticks_usec()
	var plny := bool(main.get("mereni_on"))
	var jen_fps := not plny and bool(main.get("mereni_fps"))
	_panel.visible = plny or jen_fps
	_okno_snimek(dt)
	_konec_snimku()                 # diag bezi posledni: skripty snimku hotove (vlastni rezie diag jde do "kresleni")
	_zapis_zaseky()
	if jen_fps:
		# radce 07:15 A: lehky rezim - jeden radek, bez seznamu uzlu, svetel a trojuhelniku (plny panel 4-17 ms)
		_max_dt_panel = maxf(_max_dt_panel, dt)
		_tp += dt
		if _tp >= 0.5:
			_tp = 0.0
			_panel.text = "FPS %d · nejdelší %.0f ms · %s · záseků %d%s" % [Engine.get_frames_per_second(), _max_dt_panel * 1000.0, poloha_text(),
					zaseku, ("\n" + String(_zaseky[0])) if not _zaseky.is_empty() else ""]
			_max_dt_panel = 0.0
		_kontrola_rozpoctu()
		_t += dt
		if _t >= 2.0:
			_t = 0.0
			_zapis("")
		return
	if plny:
		_troj_skupiny()
	_max_dt = maxf(_max_dt, dt)
	_max_dt_panel = maxf(_max_dt_panel, dt)
	_cpu_max = maxf(_cpu_max, Performance.get_monitor(Performance.TIME_PROCESS))
	if _panel.visible:
		var vp_rid := get_viewport().get_viewport_rid()
		if not _mereni_rt:
			RenderingServer.viewport_set_measure_render_time(vp_rid, true)
			_mereni_rt = true
		# docs 4.4: ms; 0 = ovladac GPU cas nevraci (Compatibility na Adrenu) -> N/A
		var gpu := RenderingServer.viewport_get_measured_render_time_gpu(vp_rid)
		if gpu > 0.0:
			_gpu_sum += gpu
			_gpu_n += 1
		if dt > ZASEK:
			_sp_n += 1
		if dt * 1000.0 > float(_sp[0]):
			# fyzika z razitek snimku (_sn = prave uzavreny snimek, delka ~ dt), ne TIME_PHYSICS_PROCESS (max kroku za 1 s)
			var skr := float(_sn.get("skripty", 0))
			_sp = [dt * 1000.0, skr / 1000.0, float(_sn.get("fyzika", 0)) / 1000.0,
					RenderingServer.get_frame_setup_time_cpu() + RenderingServer.viewport_get_measured_render_time_cpu(vp_rid), gpu]
			var serad: Array = _cas_minule.keys()
			serad.sort_custom(func(a: String, b: String) -> bool: return float(_cas_minule[a]) > float(_cas_minule[b]))
			var t := []
			for k: String in serad.slice(0, 3):
				t.append("%s %.1f" % [k, float(_cas_minule[k]) / 1000.0])
			_sp_text = ", ".join(t) if not t.is_empty() else "-"
			_sp_geom = _okno_geom
			_sp_mat = _okno_mat
			if dt > ZASEK:
				print("SPICKA %.0f ms: skripty %.1f (%s), fyzika %.1f, CPU kresleni %.1f, nove uzly %d, materialy %d" % [_sp[0], _sp[1], _sp_text, _sp[2], _sp[3], _sp_geom, _sp_mat])
	_tp += dt
	if _panel.visible and _tp >= 0.5:
		_tp = 0.0
		var gpu_t := "N/A" if _gpu_n == 0 or _gpu_sum <= 0.0 else "%.1f" % (_gpu_sum / _gpu_n)
		var sp_gpu := "N/A" if float(_sp[4]) <= 0.0 else "%.0f" % float(_sp[4])
		_panel.text = "FPS %d  (%.1f ms, nejdelší %.0f ms) · %s\n%s\n%s\ntroj. (odhad LOD0): %s\nkreslení %d · trojúhelníky %.2f M · objekty %d\n%s\n%s\n%s\n%s\nzáseky: %s" % [
			Engine.get_frames_per_second(), 1000.0 / maxf(1.0, Engine.get_frames_per_second()), _max_dt_panel * 1000.0, poloha_text(),
			"špička %.0f ms: skripty (měřené) %.1f, fyzika %.1f, CPU kreslení %.1f, GPU %s (průměr %s) ms · špiček %d" % [_sp[0], _sp[1], _sp[2], _sp[3], sp_gpu,
				gpu_t, _sp_n],
			"nejdražší: %s · nové uzly %d, materiály %d · %s · panel %.1f ms" % [_sp_text, _sp_geom, _sp_mat, _svetla_text(), _rezie_ms],
			_skup_text,
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000000.0,
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			_pamet_text(), _rust_text(), _plan_text(), sestaveni_text(), ("%d · " % zaseku) + " | ".join(_zaseky) if not _zaseky.is_empty() else "žádné"]
		_max_dt_panel = 0.0
		_sp = [0.0, 0.0, 0.0, 0.0, 0.0]
		_sp_n = 0
		_gpu_sum = 0.0
		_gpu_n = 0
	_kontrola_rozpoctu()
	_rezie_ms = (Time.get_ticks_usec() - d0) / 1000.0
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


## Misa 0.66: poloha na obrazovce - z fotky panelu se najde misto chyby (x, z vodorovne jako mapa, y vyska;
## smer pohledu podle mapy: sever = -z).
var _sestaveni := ""


## Radce 25. 10. 06:20: radek "sestaveni: verze commit manifest" - Misa fotkou potvrdi, co testuje (sestaveni.json
## pise tools/vydani.py do APK).
func _plan_text() -> String:
	var sv: Object = main.get("svet") if main else null
	if sv == null or not sv.has_method("plan_text"):
		return "plánovač -"
	var t: String = sv.plan_text()
	sv.set("plan_max_ms", 0.0)
	return t


func sestaveni_text() -> String:
	if _sestaveni == "":
		var j = JSON.parse_string(FileAccess.get_file_as_string("res://sestaveni.json")) if FileAccess.file_exists("res://sestaveni.json") else null
		_sestaveni = "sestavení: %s %s, manifest %s, balíky přestavěné: %s" % [j["verze"], j["commit"], j["manifest"], j["prestavene"]] if j is Dictionary else "sestavení: neznámé (z editoru)"
	return _sestaveni


func poloha_text() -> String:
	var pl: Node3D = main.get("player") if main else null
	if pl == null:
		return ""
	var g := pl.global_position
	var sm := fposmod(rad_to_deg(float(pl.get("yaw"))), 360.0)
	var sv: String = ["S", "SZ", "Z", "JZ", "J", "JV", "V", "SV"][int(round(sm / 45.0)) % 8]
	return "x %.0f z %.0f (výška %.1f) pohled %s" % [g.x, g.z, g.y, sv]


## Trend nativni haldy za poslednich 60 s (primka prolozena 30 vzorky po 2 s, ne rozdil dvou vzorku) + test pameti.
func trend_mb_min() -> float:
	var n := _ram_hist.size()
	if n < 5:
		return NAN
	var sx := 0.0
	var sy := 0.0
	var sxx := 0.0
	var sxy := 0.0
	for e: Array in _ram_hist:
		sx += float(e[0])
		sy += float(e[1])
		sxx += float(e[0]) * float(e[0])
		sxy += float(e[0]) * float(e[1])
	var den := n * sxx - sx * sx
	return 0.0 if den <= 0.0 else (n * sxy - sx * sy) / den * 60.0


func _rust_text() -> String:
	var tr := trend_mb_min()
	var t := "trend haldy 60 s: %s" % ("N/A" if is_nan(tr) else "%+.0f MB/min" % tr)
	t += " · " + _fronty_text()
	if main and bool(main.get("_test_auto")):
		t += "  · test: " + String(main.TEST_PAMETI[int(main.test_pameti)])
	if main and not (main.get("test_vysledky") as PackedStringArray).is_empty():
		t += "\ntest (krok: RAM/min, FPS, nejdelší)\n" + "\n".join(main.test_vysledky)
	return t


## Fronty a cache (radce 20:00): bunky louky a jejich fronty, rostliny a kolize okoli, uzly, objekty, zdroje.
func _fronty_text() -> String:
	var lk: Node = main.get_node_or_null("Louka") if main else null
	var sv: Object = main.get("svet") if main else null
	var t := ""
	if lk:
		t += "louka %d (vlákna %d, stavba %d)" % [lk._bunky.size(), lk._ceka.size(), lk._stavba.size()]
	if sv:
		t += " · rostliny %d/%d · kolize %d/%d (fronta %d)" % [sv._rost_uzly.size(), sv._rost_data.size(), sv._kol_uzly.size(),
				sv._kol_data.size(), sv._kol_fronta.size()]
	t += " · uzly %d, objekty %d, zdroje %d" % [Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
			Performance.get_monitor(Performance.OBJECT_COUNT), Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT)]
	return t


func _pamet_text() -> String:
	return "nativní halda %d MB (max %d) · proces PSS %s · volná %s · GPU %d MB (textury %d, buffery %d)" % [_ram, _ram_max,
			"N/A" if _pss < 0 else "%d MB" % _pss, "N/A" if _volna < 0 else "%d MB" % _volna,
			Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0,
			Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0, Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0]


## RAM procesu (MB). Ve vydani OS.get_static_memory_usage() vraci 0 a /proc/self/statm se na Androidu cte pres
## Java vrstvu s delkou 0 (0.59 panel porad 0) -> Android: nativni halda (android.os.Debug, rychle - tam selhava
## malloc) a volna pamet systemu; jinde rezidentni pamet z /proc/self/statm.
var _dbg: Variant = null
var _volna := -1
var _pss := -1
var _pss_t := -100000
var _pss_ms := 0.0


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
		_volna = vol / 1048576 if vol > 0 else -1  # -1 = nezname (N/A), ne 0
		# pamet procesu (PSS, vsechny haldy + ovladac GPU): drahe volani, jednou za 30 s
		if _dbg != null and Time.get_ticks_msec() - _pss_t > 30000:
			_pss_t = Time.get_ticks_msec()
			var u0 := Time.get_ticks_usec()
			_pss = int(_dbg.getPss()) / 1024
			_sn_ted["pss"] = true        # zasek v tomto snimku muze byt od mereni
			_pss_ms = (Time.get_ticks_usec() - u0) / 1000.0
	else:
		var f := FileAccess.open("/proc/self/statm", FileAccess.READ)
		if f:
			var sl := f.get_line().split(" ")
			f.close()
			if sl.size() > 1:
				_ram = int(sl[1]) * 4096 / 1048576
				_pss = _ram
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


func _zapis(pozn: String, hned := true) -> void:
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
	while _ram_hist.size() > 30:
		_ram_hist.pop_front()
	if _ram > 1200 and Time.get_ticks_msec() / 1000.0 - _varovano > 5.0:
		_varovano = Time.get_ticks_msec() / 1000.0
		push_warning("VAROVANI RAM %d MB (prah 1200)" % _ram)
	var r := "%ds fps %d (nejdelsi snimek %.0f ms, proces max %.1f ms) | halda %d MB (max %d, volna %d, pss %d, trend %s) | gpu %d MB (tex %d, buf %d) | troj %.1f M | kresleni %d | obj %d | uzly %d (objekty %d, zdroje %d, sirotci %d) | %s | hrac %d,%d,%d %s" % [
		(Time.get_ticks_msec() - _start) / 1000,
		Engine.get_frames_per_second(), _max_dt * 1000.0, _cpu_max * 1000.0,
		_ram, _ram_max, _volna, _pss, "N/A" if is_nan(trend_mb_min()) else "%+.0f" % trend_mb_min(),
		Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0,
		Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0,
		Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0,
		Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000000.0,
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		Performance.get_monitor(Performance.OBJECT_NODE_COUNT), Performance.get_monitor(Performance.OBJECT_COUNT),
		Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT), Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT),
		bunky, p.x, p.y, p.z, pozn]
	# zaseky od minuleho zapisu i do diag.log (nejvys 10 za 2 s, zbytek je v zaseky.log) - bez vlastniho zapisu
	var nz := mini(zaseku - _zaseky_do_logu, _zaseky_log.size())
	for zi in range(_zaseky_log.size() - mini(nz, 10), _zaseky_log.size()):
		_radky.append(_zaseky_log[zi])
	if nz > 10:
		_radky.append("... a dalsich %d zaseku (user://zaseky.log)" % (nz - 10))
	_zaseky_do_logu = zaseku
	_radky.append(r)
	if _radky.size() > MAX_RADKU:
		_radky = _radky.slice(_radky.size() - MAX_RADKU)
	# prepsat cely soubor (140 kB) a hned zavrit: pri padu zustane posledni zapsany stav. Zapis ve vlakne
	# (0.62 bod 8: na tabletu zapis+zavreni v hlavnim vlakne kazde 2 s = spicka snimku); predchozi musi dobehnout.
	var text := "\n".join(_radky) + "\n"
	# radce 20:00: wait_for_task_completion pri kazdem zapisu mohl cekat na pomaly disk v hlavnim vlakne - predchozi
	# zapis jeste bezi -> tento se vynecha (pristi za 2 s zapise vse); jen faze/konec ceka (musi byt na disku)
	if _zapis_uloha >= 0 and WorkerThreadPool.is_task_completed(_zapis_uloha):
		WorkerThreadPool.wait_for_task_completion(_zapis_uloha)
		_zapis_uloha = -1
	if pozn != "" and hned:
		if _zapis_uloha >= 0:
			WorkerThreadPool.wait_for_task_completion(_zapis_uloha)
			_zapis_uloha = -1
		_zapis_soubor(text)           # faze nacitani, konec/pauza: hned (pad pri nacitani, Android zavre aplikaci)
	elif _zapis_uloha < 0:
		_zapis_uloha = WorkerThreadPool.add_task(_zapis_soubor.bind(text))


var _zapis_uloha := -1


static func _zapis_soubor(text: String) -> void:
	_zapis_soubor_do(LOG, text)


static func _zapis_soubor_do(cesta: String, text: String) -> void:
	var f := FileAccess.open(cesta, FileAccess.WRITE)
	if f:
		f.store_string(text)
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
		# vysledky automatickeho testu pameti (main._test_krok) - jen konec radku s vysledkem
		var test: PackedStringArray = []
		for l in lines:
			if l.contains("TEST PAMETI"):
				test.append(l.substr(l.find("FAZE TEST")))
		if not test.is_empty():
			out += "test pameti:\n" + "\n".join(test) + "\n"
		out += "posledni zaznamy:\n" + "\n".join(lines.slice(maxi(0, lines.size() - 6))) + "\n"
	return out


# ------------------------------------------------------------------ profil na tabletu (radce 20:00)
var _sp_text := "-"
# radce 17:45: kolik kreslenych uzlu (MultiMesh, Mesh) a novych materialu pribylo ve snimku (nove = mozna kompilace)
var _nove_geom := 0
var _nove_mat := 0
var _znam_mat := {}
var _okno_geom := 0
var _okno_mat := 0


## Radce 18:40: svetel v dosahu (zapnutych) a kolik z nich vrha stin.
func _svetla_text() -> String:
	var l: Node = main.get("life") if main else null
	if l == null:
		return ""
	var on := 0
	var st := 0
	for d: Dictionary in l.lights:
		var o: OmniLight3D = d["light"]
		if is_instance_valid(o) and o.is_visible_in_tree() and bool(d.get("on", true)):
			on += 1
			st += int(o.shadow_enabled)
	return "svetel %d (stin %d)" % [on, st]


func _pridan(n: Node) -> void:
	if n is GeometryInstance3D:
		_nove_geom += 1
		var g := n as GeometryInstance3D
		var mats: Array = [g.material_override]
		if n is MultiMeshInstance3D and (n as MultiMeshInstance3D).multimesh and (n as MultiMeshInstance3D).multimesh.mesh:
			var me := (n as MultiMeshInstance3D).multimesh.mesh
			for i in me.get_surface_count():
				mats.append(me.surface_get_material(i))
		elif n is MeshInstance3D and (n as MeshInstance3D).mesh:
			var me2 := (n as MeshInstance3D).mesh
			for i in me2.get_surface_count():
				mats.append((n as MeshInstance3D).get_active_material(i))
		for m: Material in mats:
			if m and not _znam_mat.has(m.get_rid()):
				_znam_mat[m.get_rid()] = true
				_nove_mat += 1


## Cas skriptu meri obal _process kazdeho skriptu (cas()); diag bezi posledni (process_priority) a uzavre snimek.
var _cas_snimek := {}
var _cas_minule := {}
var _sp_geom := 0
var _sp_mat := 0
var _rezie_ms := 0.0


func cas(nazev: String, us: int) -> void:
	_cas_snimek[nazev] = int(_cas_snimek.get(nazev, 0)) + us


func _okno_snimek(_dt: float) -> void:
	_cas_minule = _cas_snimek
	_cas_snimek = {}
	_okno_geom = _nove_geom
	_okno_mat = _nove_mat
	_nove_geom = 0
	_nove_mat = 0


# ------------------------------------------------------------------ troj. po skupinach (radce 18:00 bod 2)
# Viditelne trojuhelniky po skupinach (stromy / trava / lesni puda / kvety / skaly / stavby): uzly s geometrii
# projde po 1500 na snimek (bez spicky), viditelnost = v dosahu visibility_range a v zornem jehlanu kamery;
# troj. = troj. site x instance. LOD siti nepocita (horni odhad).
var _sk_uzly: Array = []
var _sk_i := 0
var _sk_sum := {}
var _sk_troj := {}                     # Mesh RID -> troj.
var _skup_text := "-"
var _sk_zas: Array = []
var _sk_nove: Array = []
const SKUPINY := [["trava", ["louka_", "kupy", "Louka"]], ["stromy", ["dub", "buk", "lipa", "smrk", "borovice", "briza", "olse",
		"vrba", "imp_", "impostor", "fir_", "pine_"]], ["puda", ["kapradi", "ker_husty", "ker_kulaty", "shrub", "sipek", "bez_", "mech",
		"moss", "fern", "celandine", "periwinkle", "bark", "dry_", "tree_stump", "root_", "dead_"]],
		["byliny+kvety", ["kopretiny", "kvety", "dandelion", "nettle", "byliny", "celandine", "periwinkle", "weed"]], ["skaly", ["skala", "balvan", "kamen", "rock"]],
		["voda", ["voda", "Reka", "Prikop", "Potok", "rakos", "orobinec"]], ["teren", ["Teren", "Nadvori", "zaplata"]]]


func _skupina(n: Node) -> String:
	var nm := String(n.name)
	var pn := String(n.get_parent().name) if n.get_parent() else ""
	for g: Array in SKUPINY:
		for pf: String in g[1]:
			if nm.begins_with(pf) or pn.begins_with(pf):
				return g[0]
	# radce 20:00: nezname nepadaji do staveb - stavby jen pod modelem sveta (Tvrz) a statickymi stavbami
	var a := n.get_parent()
	for _k in 8:
		if a == null:
			break
		var an := String(a.name)
		if an == "Tvrz" or an.begins_with("Staticky_"):
			return "stavby"
		if an == "Predmety" or an == "PredmetyHra":
			return "predmety"
		a = a.get_parent()
	return "ostatni"


func _troj_site(m: Mesh) -> int:
	if m == null:
		return 0
	var rid := m.get_rid()
	if _sk_troj.has(rid):
		return _sk_troj[rid]
	var t := 0
	if m is ArrayMesh:
		for i in m.get_surface_count():
			var ni := (m as ArrayMesh).surface_get_array_index_len(i)
			t += (ni if ni > 0 else (m as ArrayMesh).surface_get_array_len(i)) / 3
	_sk_troj[rid] = t
	return t


func _troj_skupiny() -> void:
	if not _panel.visible:
		return
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	# radce 18:35: find_children pres 50 000 uzlu = spicka 91 ms ("Diag seznam") a seznam zastaraval (bunky louky
	# se prestavuji -> trava 0,00 M). Strom se prochazi po castech (2 000 uzlu za snimek) a seznam se obnovuje stale.
	if _sk_zas.is_empty() and _sk_i >= _sk_uzly.size():
		if not _sk_nove.is_empty() or not _sk_sum.is_empty():
			var t := []
			for g: Array in SKUPINY + [["stavby", []], ["predmety", []], ["ostatni", []]]:
				t.append("%s %.2f" % [g[0], float(_sk_sum.get(g[0], 0)) / 1e6])
			_skup_text = " · ".join(t) + " M"
		_sk_sum = {}
		_sk_i = 0
		_sk_uzly = _sk_nove
		_sk_nove = []
		_sk_zas = [get_tree().root]
	var kroku := 0
	while not _sk_zas.is_empty() and kroku < 2000:
		var nd: Node = _sk_zas.pop_back()
		kroku += 1
		if not is_instance_valid(nd):
			continue
		if nd is GeometryInstance3D:
			_sk_nove.append(nd)
		if nd is Node3D and not (nd as Node3D).visible:
			continue
		for ch: Node in nd.get_children():
			_sk_zas.append(ch)
	if _sk_i >= _sk_uzly.size():
		return
	var cp := cam.global_position
	var fr := cam.get_frustum()
	var konec := mini(_sk_i + 1500, _sk_uzly.size())
	for i in range(_sk_i, konec):
		var g = _sk_uzly[i]
		if not is_instance_valid(g) or not (g as GeometryInstance3D).is_visible_in_tree():
			continue
		var gi := g as GeometryInstance3D
		var bb := gi.global_transform * (gi.custom_aabb if gi.custom_aabb.size != Vector3.ZERO else gi.get_aabb())
		var c := bb.get_center()
		var rad := bb.size.length() * 0.5
		var d := cp.distance_to(c)
		# visibility_range meri vzdalenost ke stredu AABB (jako Godot)
		if gi.visibility_range_end > 0.0 and d > gi.visibility_range_end + gi.visibility_range_end_margin:
			continue
		if gi.visibility_range_begin > 0.0 and d < gi.visibility_range_begin:
			continue
		var ven := false
		for pl: Plane in fr:
			if pl.distance_to(c) > rad:
				ven = true
				break
		if ven:
			continue
		var troj := 0
		if gi is MultiMeshInstance3D:
			var mm := (gi as MultiMeshInstance3D).multimesh
			if mm:
				var n := mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
				troj = _troj_site(mm.mesh) * n
		elif gi is MeshInstance3D:
			troj = _troj_site((gi as MeshInstance3D).mesh)
		if troj > 0:
			var sk := _skupina(gi)
			_sk_sum[sk] = int(_sk_sum.get(sk, 0)) + troj
	_sk_i = konec



