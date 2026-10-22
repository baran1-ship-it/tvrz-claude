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
# 0.64 (Misa: stale sekani, nejdelsi snimek 100-145 ms): rozpad nejdelsiho snimku za 0,5 s na panelu - skripty,
# fyzika, priprava kresleni (CPU), GPU; pocet spicek > 50 ms. Kdo z nich je velky, ten seka.
var _sp := [0.0, 0.0, 0.0, 0.0, 0.0]  # [snimek, skripty, fyzika, priprava CPU, GPU] v ms
var _sp_n := 0
var _gpu_sum := 0.0
var _gpu_n := 0
var _mereni_rt := false


func _process(dt: float) -> void:
	_panel.visible = bool(main.get("mereni_on"))
	_profil(dt)
	_troj_skupiny()
	_max_dt = maxf(_max_dt, dt)
	_max_dt_panel = maxf(_max_dt_panel, dt)
	_cpu_max = maxf(_cpu_max, Performance.get_monitor(Performance.TIME_PROCESS))
	if _panel.visible:
		var vp_rid := get_viewport().get_viewport_rid()
		if not _mereni_rt:
			RenderingServer.viewport_set_measure_render_time(vp_rid, true)
			_mereni_rt = true
		var gpu := RenderingServer.viewport_get_measured_render_time_gpu(vp_rid)
		_gpu_sum += gpu
		_gpu_n += 1
		if dt > 0.05:
			_sp_n += 1
		if dt * 1000.0 > float(_sp[0]):
			_sp = [dt * 1000.0, Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
					Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
					RenderingServer.get_frame_setup_time_cpu() + RenderingServer.viewport_get_measured_render_time_cpu(vp_rid), gpu]
	_tp += dt
	if _panel.visible and _tp >= 0.5:
		_tp = 0.0
		_panel.text = "FPS %d  (%.1f ms, nejdelší %.0f ms)\n%s\nnejdelší: %s\ntroj.: %s\nkreslení %d\ntrojúhelníky %.2f M\nobjekty %d\nRAM %d MB (volná %d) · GPU %d MB (textury %d, buffery %d)\n%s" % [
			Engine.get_frames_per_second(), 1000.0 / maxf(1.0, Engine.get_frames_per_second()), _max_dt_panel * 1000.0,
			"špička %.0f: skripty %.0f, fyzika %.0f, CPU kreslení %.0f, GPU %.0f (průměr %.0f) · špiček %d" % [_sp[0], _sp[1], _sp[2], _sp[3], _sp[4],
				_gpu_sum / maxf(1.0, _gpu_n), _sp_n],
			_sp_text, _skup_text,
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000000.0,
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			_ram, _volna, Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0,
			Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0, Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0,
			_rust_text()]
		_max_dt_panel = 0.0
		_sp = [0.0, 0.0, 0.0, 0.0, 0.0]
		_pr_max = 0.0
		_sp_n = 0
		_gpu_sum = 0.0
		_gpu_n = 0
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
	if main and bool(main.get("_test_auto")):
		t += "  · test: " + String(main.TEST_PAMETI[int(main.test_pameti)])
	if main and not (main.get("test_vysledky") as PackedStringArray).is_empty():
		t += "\ntest (krok: RAM/min, FPS, nejdelší)\n" + "\n".join(main.test_vysledky)
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
	# prepsat cely soubor (140 kB) a hned zavrit: pri padu zustane posledni zapsany stav. Zapis ve vlakne
	# (0.62 bod 8: na tabletu zapis+zavreni v hlavnim vlakne kazde 2 s = spicka snimku); predchozi musi dobehnout.
	var text := "\n".join(_radky) + "\n"
	if _zapis_uloha >= 0:
		WorkerThreadPool.wait_for_task_completion(_zapis_uloha)
		_zapis_uloha = -1
	if pozn != "":
		_zapis_soubor(text)           # faze nacitani, konec/pauza: hned (pad pri nacitani, Android zavre aplikaci)
	else:
		_zapis_uloha = WorkerThreadPool.add_task(_zapis_soubor.bind(text))


var _zapis_uloha := -1


static func _zapis_soubor(text: String) -> void:
	var f := FileAccess.open(LOG, FileAccess.WRITE)
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


# ------------------------------------------------------------------ profil na tabletu (radce 18:00 bod 3)
# Pri zapnutem mereni diag vola _process skriptu sam (uzly pod Main a Main) a meri kazdy zvlast; pro nejdelsi snimek
# za 0,5 s panel ukaze 3 nejdrazsi skripty + zbytek (kresleni, ovladac). Snimek dt patri k praci od minuleho
# behu diag - proto se pamatuje rozpad predchoziho okna.
var _pr_uzly: Array = []
var _pr_hledat := 0.0
var _pr_okno: Array = []               # [[nazev, ms]] od posledniho behu diag
var _pr_max := 0.0
var _sp_text := "-"


func _profil(dt: float) -> void:
	if not _panel.visible:
		if not _pr_uzly.is_empty():
			for n: Node in _pr_uzly:
				if is_instance_valid(n):
					n.set_process(true)
			_pr_uzly.clear()
		return
	# rozpad okna, ktere skoncilo timto snimkem (dt = cas od minuleho behu)
	if dt * 1000.0 > _pr_max:
		_pr_max = dt * 1000.0
		var serad := _pr_okno.duplicate()
		serad.sort_custom(func(a: Array, b: Array) -> bool: return float(a[1]) > float(b[1]))
		var skr := 0.0
		for e: Array in _pr_okno:
			skr += float(e[1])
		var t := []
		for e: Array in serad.slice(0, 3):
			t.append("%s %.0f" % [e[0], e[1]])
		_sp_text = "%s · skripty %.0f, fyzika %.0f, zbytek %.0f" % [", ".join(t), skr,
				Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0, dt * 1000.0 - skr]
	_pr_okno = []
	_pr_hledat -= dt
	if _pr_hledat <= 0.0:
		_pr_hledat = 2.0
		for n: Node in [main] + main.get_children():
			if n != self and n.get_script() != null and n.has_method("_process") and n.is_processing() and not _pr_uzly.has(n):
				n.set_process(false)
				_pr_uzly.append(n)
	for n: Node in _pr_uzly:
		if not is_instance_valid(n) or not n.is_inside_tree() or not n.can_process():
			continue
		var u0 := Time.get_ticks_usec()
		n.call("_process", dt)
		_pr_okno.append([String(n.name), (Time.get_ticks_usec() - u0) / 1000.0])


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
		"vrba", "imp_", "impostor", "fir_", "pine_"]], ["puda", ["kapradi", "ker_husty", "shrub", "sipek", "bez_", "mech",
		"moss", "fern", "celandine", "periwinkle", "bark", "dry_", "tree_stump", "root_", "dead_"]],
		["kvety", ["kopretiny", "kvety", "dandelion", "nettle", "byliny"]], ["skaly", ["skala", "balvan", "kamen", "rock"]],
		["voda", ["voda", "Reka", "Prikop", "rakos", "orobinec"]]]


func _skupina(n: Node) -> String:
	var nm := String(n.name)
	var pn := String(n.get_parent().name) if n.get_parent() else ""
	for g: Array in SKUPINY:
		for pf: String in g[1]:
			if nm.begins_with(pf) or pn.begins_with(pf):
				return g[0]
	return "stavby"


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
			for g: Array in SKUPINY + [["stavby", []]]:
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
