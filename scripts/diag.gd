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
## 15. 11. (Misa „monitor mereni dost bere“, vykon_postavy_puchart_15_11.md bod 1): lehky monitor behem merici trasy -
## pravidelny zapis logu a PSS jen na hranicich useku (trasa_hranice), node_added jen citac, „pod křížem“ vypnuto.
## Zapina mereni_trasa.gd (mereni_trasa.json lehky_monitor), varianta diag_plny = drivejsi stav.
var lehky := false
var _pss_hranice := false


func setup(p_main: Node) -> void:
	p_main.get_tree().node_added.connect(_pridan)
	# casova osa snimku (overeni 16:45): Performance.TIME_PHYSICS_PROCESS je v 4.4 maximum JEDNOHO kroku za posledni
	# sekundu (main.cpp: physics_process_max, nastavi se 1x za s) - pro zasek nepouzitelne. Vlastni razitka:
	# physics_frame / process_frame (SceneTree je vysila pred uzly) a konec diag._process (bezi posledni).
	p_main.get_tree().physics_frame.connect(_na_fyziku)
	p_main.get_tree().process_frame.connect(_na_process)
	# 14. 11. (rozbor zaseku, chybejici mereni 1): rozpad „kresleni+cekani“. Godot 4.4.1 rendering_server_default.cpp:
	# frame_pre_draw vysila draw() na zacatku (hlavni vlakno, po mazani queue_free, casovacich a sync), frame_post_draw
	# konec _draw (bez vlakna kresleni synchronne): mezi nimi aktualizace sceny vc. nahrani MultiMeshu
	# (_update_dirty_multimeshes), orez, volani kresleni; na PC i swap (gl_end_frame), na Androidu je eglSwapBuffers az
	# po kroku enginu (GodotRenderer.java) - tam pada do „swap/GPU“ i se spankem max_fps.
	RenderingServer.frame_pre_draw.connect(_na_pre_draw)
	RenderingServer.frame_post_draw.connect(_na_post_draw)
	main = p_main
	Engine.set_meta("diag", self)
	process_priority = 100000              # bezi po vsech ostatnich _process: snimek je zmereny cely
	process_mode = Node.PROCESS_MODE_ALWAYS
	_start = Time.get_ticks_msec()
	# hlavicka logu (chybejici mereni 4): obnovovaci frekvence obrazovky a jadra (vsync cil, pocet vlaken)
	_hlavicka = "HLAVICKA obrazovka %.1f Hz, jader %d, model %s, %s" % [DisplayServer.screen_get_refresh_rate(), OS.get_processor_count(),
			OS.get_model_name(), sestaveni_text()]
	_radky.append(_hlavicka)
	# panel mereni vykonu (zapina se v nastaveni): levy horni roh, aktualizace 2x za sekundu
	var cl := CanvasLayer.new()
	cl.layer = 50
	add_child(cl)
	_panel = Label.new()
	_panel.position = Vector2(16, 12)
	_panel.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART     # radce 17:10: na tabletu orizly vpravo
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


## Misa 0.91 „kde stahnu log“: user:// na Androidu neni videt - vyber do schranky (nacitani, A/B panelu, zaseky).
func zkopiruj_log() -> int:
	var nac: PackedStringArray = []
	var ab: PackedStringArray = []
	for r: String in _radky:
		if r.contains("FAZE") or r.contains("STAVBA") or r.contains("cesty do terenu"):
			nac.append(r.get_slice(" | hrac", 1).strip_edges() if r.contains(" | hrac") else r)
		elif r.begins_with("[panel"):
			ab.append(r.get_slice(" | halda", 0))
	var t := _hlavicka + "\nZAZNAM MERENI %s\n== nacitani ==\n%s\n== panel / snimek po 2 s ==\n%s\n== zaseky ==\n%s\n" % [sestaveni_text(),
			"\n".join(nac), "\n".join(ab.slice(maxi(0, ab.size() - 150))), "\n".join(_zaseky_log.slice(maxi(0, _zaseky_log.size() - 120)))]
	# posledni vysledek merici trasy (user://mereni_trasa.txt, Misa 2. 11.: tabulka byla jen minutu na obrazovce)
	if FileAccess.file_exists("user://mereni_trasa.txt"):
		t = FileAccess.get_file_as_string("user://mereni_trasa.txt") + "\n" + t
	t += _chyby_enginu()
	DisplayServer.clipboard_set(t)
	return t.length()


## Misa 15. 11. („vsimej si vsech chyb, treba najdes, proc se to seka“): chyby enginu z user://logs/godot.log tohoto
## spusteni - kazda opakovana chyba (vypis + zasobnik) stoji cas snimku. Souhrn: pocet a text, nejcastejsi nahore.
func _chyby_enginu() -> String:
	var cesta := "user://logs/godot.log"
	if not FileAccess.file_exists(cesta):
		return "\n== chyby enginu ==\nlog neni (%s)\n" % cesta
	var f := FileAccess.open(cesta, FileAccess.READ)
	if f == null:
		return ""
	var pocty := {}
	var n := 0
	while not f.eof_reached() and n < 400000:
		var r := f.get_line()
		n += 1
		if r.begins_with("ERROR") or r.begins_with("SCRIPT ERROR") or r.begins_with("WARNING"):
			var k := r.left(160)
			pocty[k] = int(pocty.get(k, 0)) + 1
	var klice: Array = pocty.keys()
	klice.sort_custom(func(a: String, b: String) -> bool: return int(pocty[a]) > int(pocty[b]))
	var out := "\n== chyby enginu (%d druhu, %d radku logu) ==\n" % [klice.size(), n]
	for k: String in klice.slice(0, 25):
		out += "%6d x %s\n" % [int(pocty[k]), k]
	return out


## Faze nacitani: zapise se hned (pri padu behem nacitani je videt, kde hra skoncila).
func faze(t: String) -> void:
	print("FAZE %.1f s %s" % [(Time.get_ticks_msec() - _start) / 1000.0, t])   # Misa 0.89: delka nacitani po fazich
	# 11. 11. (trasa 0.99997: kazdy krok kvality = zasek 2,7-3,5 s v neměřeném _process; PODEZRENI = cekani hlavniho
	# vlakna na predchozi zapis ve fronte vlaken plne stavby louky): ve hre faze necekaji, zapis jde vlaknem (pri padu
	# chybi nejvys posledni 2 s); hned jen pri nacitani (pad pri nacitani musi byt v logu)
	_zapis("FAZE " + t, not (main and bool(main.get("ready_done"))))


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
var zaseku := 0                       # pocet zaseku od startu (panel, log): spicka nad prumerem
var pomalych := 0                     # snimky > 40 ms bez spicky (trvale pomale kresleni)
var _sn_prumer := 0.0                 # klouzavy prumer delky snimku (ms, ~1 s)
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


## Skutecna delka uzavreneho snimku (s): dt v _process je vyhlazeny (application/run/delta_smoothing) - Misa 0.89:
## FPS 10 (100 ms) a „nejdelsi 43 ms“ na jednom panelu.
func _skut(dt: float) -> float:
	return float(_sn.get("celkem", 0)) / 1000000.0 if not _sn.is_empty() else dt


## Na cem hrac stoji/narazi (posledni srazky move_and_slide): jmeno, tvar, troj. (radce 17:10 – podklad hrace)
var _tk := 0.0
var _krz_text := "-"
var _krz_xf := Transform3D()
var _krz_hotovo := false


## Misa 15. 11. (letajici trsy, mech a houby - na PC nereprodukovano): co je pod krizem - kolize paprskem a nejblizsi
## instance MultiMeshe do 0,8 m od paprsku (do 40 m; poloha z transformace, u louky z custom data): uzel, druh site,
## vyska paty nad terenem. Jednou za 1 s, jen s panelem.
func _pod_krizem() -> String:
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return "-"
	var o := cam.global_position
	var smer := -cam.global_transform.basis.z
	var out := []
	var q := PhysicsRayQueryParameters3D.create(o, o + smer * 60.0)
	var pl: Object = main.get("player") if main else null
	if pl is CollisionObject3D:
		q.exclude = [(pl as CollisionObject3D).get_rid()]
	var h := cam.get_world_3d().direct_space_state.intersect_ray(q)
	var d_kol := 60.0
	if not h.is_empty():
		d_kol = o.distance_to(h["position"])
		var co: Object = h["collider"]
		out.append("kolize %s %.1f m" % [String((co as Node).name) if co is Node else "?", d_kol])
	var nej := [0.8, null, -1, Vector3.ZERO]
	var prohledano := 0
	for n in get_tree().root.find_children("*", "MultiMeshInstance3D", true, false):
		var mmi := n as MultiMeshInstance3D
		if not mmi.is_visible_in_tree() or mmi.multimesh == null:
			continue
		var ab := mmi.global_transform * mmi.get_aabb()
		if ab.grow(1.0).intersects_segment(o, o + smer * minf(d_kol + 1.0, 40.0)) == null:
			continue
		var mm := mmi.multimesh
		var cnt := mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
		if cnt > 30000 or prohledano > 60000:
			continue
		prohledano += cnt
		for i in cnt:
			var lp := mm.get_instance_transform(i).origin
			if lp == Vector3.ZERO and mm.use_custom_data:
				var cd := mm.get_instance_custom_data(i)
				lp = Vector3(cd.g, cd.b, cd.a)
			var wp := mmi.global_transform * lp
			var t := (wp - o).dot(smer)
			if t < 0.3 or t > minf(d_kol + 0.5, 40.0):
				continue
			var kolmo := (o + smer * t).distance_to(wp)
			if kolmo < float(nej[0]):
				nej = [kolmo, mmi, i, wp]
	if nej[1] != null:
		var m2 := nej[1] as MultiMeshInstance3D
		var wp2: Vector3 = nej[3]
		var ty: float = float(main.svet._teren_y(wp2.x, wp2.z)) if main and main.get("svet") else wp2.y
		out.append("%s/%s #%d %s pata %.2f m nad terénem" % [String(m2.get_parent().name), String(m2.name), int(nej[2]),
				m2.multimesh.mesh.resource_name if m2.multimesh.mesh else "?", wp2.y - ty])
	return " · ".join(out) if not out.is_empty() else "nic"


func _pod_nohama() -> String:
	var pl: CharacterBody3D = main.get("player") if main else null
	if pl == null:
		return "-"
	var co: Array = []
	for i in mini(pl.get_slide_collision_count(), 3):
		var k := pl.get_slide_collision(i)
		var o: Object = k.get_collider()
		var sh: Object = k.get_collider_shape()
		var tv := ""
		if sh is CollisionShape3D and (sh as CollisionShape3D).shape:
			var s2 := (sh as CollisionShape3D).shape
			tv = s2.get_class().trim_suffix("Shape3D")          # bez poctu troj. (get_faces kopiruje cele pole)
		var nm: String = String((o as Node).name) if o is Node else "?"
		var rod := String((o as Node).get_parent().name) if o is Node and (o as Node).get_parent() else ""
		co.append("%s/%s %s" % [rod, nm, tv])
	return ", ".join(co) if not co.is_empty() else "nic (%s)" % ("na zemi" if pl.is_on_floor() else "ve vzduchu")


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
		# rozpad (razitka frame_pre_draw / frame_post_draw tohoto snimku; bez nich -1 = snimek se nekreslil)
		var pd := int(_sn_ted.get("pred", 0))
		var po := int(_sn_ted.get("po", 0))
		if pd > 0 and po >= pd:
			_sn_ted["pred_kr"] = pd - int(_sn_ted["konec"])
			_sn_ted["kr_cpu"] = po - pd
			_sn_ted["swap"] = zac - po
		# odebrane uzly (queue_free se maze po _process, pred kreslenim): pocet pred + pridane - pocet ted
		var nu := int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
		_sn_ted["odebrano"] = maxi(0, _uzlu_pred + _pridano_uzlu - nu)
		_uzlu_pred = nu
		_pridano_uzlu = 0
		_sn = _sn_ted
		_detektor()
		_hist_sn.push_back(int(_sn["celkem"]))
		if _hist_sn.size() > 3:
			_hist_sn.pop_front()
	_sn_ted = {"zac": zac, "fyzika": t - zac if _kroku > 0 else 0, "kroku": _kroku, "konec": t}
	_kroku = 0
	_t_proc0 = t


func _na_pre_draw() -> void:
	if not _sn_ted.is_empty():
		_sn_ted["pred"] = Time.get_ticks_usec()


func _na_post_draw() -> void:
	if not _sn_ted.is_empty():
		_sn_ted["po"] = Time.get_ticks_usec()


## Udalosti snimku (chybejici mereni 2): skripty hlasi, co v tomto snimku odkryly / nahraly (louka: bunky, bajty,
## instance; svet: bunky rostlin...). Jen soucet do slovniku; vypis v radku zaseku. Klic konci "_B" = bajty (vypis kB).
func udalost(klic: String, n := 1) -> void:
	_ud[klic] = int(_ud.get(klic, 0)) + n


var _ud := {}
var _hist_sn: Array[int] = []            # delky 3 predchozich snimku (us) pred prave uzavrenym
var _uzlu_pred := 0
var _pridano_uzlu := 0
var _hlavicka := ""


## Konec snimku (posledni _process): skripty tohoto snimku, planovac, nove uzly.
func _konec_snimku() -> void:
	if _sn_ted.is_empty():
		return
	var t := Time.get_ticks_usec()
	_sn_ted["konec"] = t
	_sn_ted["ud"] = _ud
	_ud = {}
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
	# Misa 0.89 (okruh, 1689 „zaseku“ za 8 min): pri 20-30 FPS je > 40 ms skoro kazdy snimek - to je pomale kresleni,
	# ne zasek. Zasek = > 40 ms A zaroven 1,6x delsi nez prumer posledni ~1 s; ostatni > 40 ms = pomaly snimek.
	var prumer := _sn_prumer
	_sn_prumer = cel if _sn_prumer <= 0.0 else lerpf(_sn_prumer, cel, 0.05)
	var _pk_ted := _pipeline_soucet()
	var _pk_pred := _pipe_minule
	_pipe_minule = _pk_ted
	_pipe_pred_snimku = _pk_pred
	if cel <= ZASEK * 1000.0 or not main or not main.get("ready_done"):
		return
	if cel < prumer * 1.6:
		pomalych += 1
		return
	zaseku += 1
	var fy := float(_sn.get("fyzika", 0)) / 1000.0
	var pc := float(_sn.get("process", 0)) / 1000.0
	var kr := float(_sn.get("kresleni", 0)) / 1000.0
	var pr := "fyzika" if fy >= maxf(kr, pc) else ("kreslení" if kr >= pc else "skripty")
	var fz := ""
	if pr == "fyzika":
		# rozpis fyziky: skripty ve fyzice (hrac, voda) a stav fyzikalniho serveru
		var hr := float(_cas_minule.get("fyz: hrac", 0)) / 1000.0
		var ms := float(_cas_minule.get("fyz: hrac m&s", 0)) / 1000.0
		var sc := float(_cas_minule.get("fyz: hrac schod", 0)) / 1000.0
		fz = " [hráč %.1f (move_and_slide %.1f, schod %.1f, zbytek %.1f; pod nohama %s), voda %.1f ms; aktivních %d, párů %d, ostrovů %d]" % [hr, ms, sc, hr - ms - sc, _pod_nohama(),
				float(_cas_minule.get("fyz: voda", 0)) / 1000.0, Performance.get_monitor(Performance.PHYSICS_3D_ACTIVE_OBJECTS),
				Performance.get_monitor(Performance.PHYSICS_3D_COLLISION_PAIRS), Performance.get_monitor(Performance.PHYSICS_3D_ISLAND_COUNT)]
	var z := "%.0f ms (%s)%s u %s, t %ds: fyzika %.0f (%d kroků), _process %.0f (měřené skripty %.0f, %s %.0f), kreslení+čekání %.0f%s, nové uzly %d%s%s" % [
			cel, pr, fz, poloha_text().get_slice(" (", 0), int(Time.get_ticks_msec() / 1000), fy, int(_sn.get("kroku", 0)), pc,
			float(_sn.get("skripty", 0)) / 1000.0, String(_sn.get("nej", "-")), float(_sn.get("nej_us", 0)) / 1000.0, kr,
			_rozpad_kresleni(), int(_sn.get("uzly", 0)), String(_sn.get("plan", "")), ", měřič PSS (vlákno %.0f ms)" % _pss_ms if bool(_sn.get("pss", false)) else ""]
	z += ", odebráno uzlů %d, předchozí snímky %s ms, kreslení %d volání / %.2f M prim., události: %s" % [int(_sn.get("odebrano", 0)),
			_hist_text(),
			RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
			RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME) / 1000000.0, _udalosti_text(_sn.get("ud", {}))]
	# 13. 11. (zasek main 114 ms na nadvori bez rozpisu): u skriptu main nejdrazsi cast (main: ...)
	if String(_sn.get("nej", "")) == "main":
		var nk := ""
		var nv := 0
		for k: String in _cas_minule:
			if k.begins_with("main: ") and int(_cas_minule[k]) > nv:
				nv = int(_cas_minule[k])
				nk = k
		if nk != "":
			z += " [%s %.0f ms]" % [nk, nv / 1000.0]
	# 14. 11. (Misa: zaseky 2-6 s plosne, kreslení+čekání, „neco se najednou objevi“): sestavene programy shaderu od minula
	# (RenderingServer PIPELINE_COMPILATIONS_*; v Compatibility nemusi ovladac hlasit - 0 = nevime, ne „nic“)
	var pk := _pipe_minule
	z += ", shadery +%d" % (pk - _pipe_pred_snimku)
	if main.player and bool(main.player.get("flying")):
		z += ", LET"                      # rychly pohyb = rychlejsi nacitani okoli (Misa 26. 10.)
	z += " | " + _fronty_zasek()
	_zaseky.push_front(z)
	_zaseky = _zaseky.slice(0, 3)
	_zaseky_log.append(Time.get_time_string_from_system() + " ZASEK " + z)
	if _zaseky_log.size() > MAX_ZASEKU:
		_zaseky_log = _zaseky_log.slice(_zaseky_log.size() - MAX_ZASEKU)


## „kreslení+čekání“ rozdelene razitky frame_pre_draw / frame_post_draw: pred kreslenim (mazani, casovace, sync),
## kresleni CPU (nahrani bufferu, orez, volani kresleni, na PC i swap), swap/GPU (Android: eglSwapBuffers, max_fps).
func _rozpad_kresleni() -> String:
	if not _sn.has("kr_cpu"):
		return " (rozpad -)"
	return " (před kreslením %.1f z toho diag %.1f, kreslení CPU %.1f, swap/GPU %.1f)" % [int(_sn["pred_kr"]) / 1000.0, int(_sn.get("diag_us", 0)) / 1000.0, int(_sn["kr_cpu"]) / 1000.0,
			int(_sn["swap"]) / 1000.0]


func _hist_text() -> String:
	var t := PackedStringArray()
	for u: int in _hist_sn:
		t.append("%.0f" % (u / 1000.0))
	return "/".join(t) if not t.is_empty() else "-"


func _udalosti_text(ud: Dictionary) -> String:
	if ud.is_empty():
		return "-"
	var t := PackedStringArray()
	for k: String in ud:
		t.append("%s %.0f kB" % [k.trim_suffix("_B"), int(ud[k]) / 1024.0] if k.ends_with("_B") else "%s %d" % [k, int(ud[k])])
	return ", ".join(t)


## Stav front a I/O v okamziku zaseku (Astra 29. 10. 07:10 bod 4: „kresleni+cekani“ neni dukaz GPU - muze to byt
## upload bufferu z vlakna louky, nacitani balicku nebo zvuku): louka (vlakna, hotove ke stavbe, rozestavene, kupy),
## predpovezeny zvuky, grafika (video pamet, buffery) a zmena proti minule.
var _vram_minule := 0.0


func _fronty_zasek() -> String:
	var lk: Node = main.get_node_or_null("Louka") if main else null
	var lt := ""
	if lk:
		lt = " · louka hotove %d, kupy ve vlaknech %d" % [(lk.get("_hotove") as Array).size(), (lk.get("_ceka_kupy") as Dictionary).size()]
	var vr := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0
	var dv := vr - _vram_minule
	_vram_minule = vr
	return "fronty: %s%s · grafika %.0f MB (%+.1f MB od minuleho zaseku), buffery %.0f MB" % [_fronty_text(), lt, vr, dv,
			Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0]


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
	var text := _hlavicka + "\n" + "\n".join(_zaseky_log) + "\n"
	if hned:
		_zapis_soubor_do(LOG_ZASEKY, text)
	else:
		_zaseky_uloha = WorkerThreadPool.add_task(_zapis_soubor_do.bind(LOG_ZASEKY, text))


## 15. 11.: vlastni rezie diag po razitku konce snimku (panel, zapis logu, mereni pameti) jde do „před kreslením" -
## zmerit zvlast (radek zaseku: „z toho diag"), aby se nemichala se skutecnou praci enginu (mazani, casovace, sync).
func _process(dt: float) -> void:
	_process_diag(dt)
	if not _sn_ted.is_empty() and _sn_ted.has("konec"):
		_sn_ted["diag_us"] = Time.get_ticks_usec() - int(_sn_ted["konec"])
	if _pss_uloha >= 0 and not _sn_ted.is_empty():
		_sn_ted["pss"] = true              # cteni PSS ve vlakne prave bezi (pripadne cekani na zamek pameti jadra)


func _exit_tree() -> void:
	if _pss_uloha >= 0:
		WorkerThreadPool.wait_for_task_completion(_pss_uloha)
		_pss_uloha = -1


func _process_diag(dt: float) -> void:
	var d0 := Time.get_ticks_usec()
	var plny := bool(main.get("mereni_on"))
	var jen_fps := not plny and bool(main.get("mereni_fps"))
	_panel.visible = plny or jen_fps
	_okno_snimek(dt)
	_konec_snimku()                 # diag bezi posledni: skripty snimku hotove (vlastni rezie diag jde do "kresleni")
	_zapis_zaseky()
	if jen_fps:
		# radce 07:15 A: lehky rezim - jeden radek, bez seznamu uzlu, svetel a trojuhelniku (plny panel 4-17 ms)
		_max_dt_panel = maxf(_max_dt_panel, _skut(dt))
		_tp += dt
		if _tp >= 0.5:
			_tp = 0.0
			_panel.size.x = maxf(400.0, get_viewport().get_visible_rect().size.x - 230.0)
			# Misa 15. 11. „monitor mereni dost bere“: pod krizem jen jednou, kdyz kamera 1 s stoji (hrac miri) - ne kazdou
			# sekundu za chuze (prochazi instance MultiMeshu = zasek)
			var cam_k := get_viewport().get_camera_3d()
			if cam_k:
				var xk := cam_k.global_transform
				if xk.origin.distance_to(_krz_xf.origin) > 0.05 or xk.basis.z.angle_to(_krz_xf.basis.z) > 0.02:
					_krz_xf = xk
					_tk = 0.0
					_krz_hotovo = false
				else:
					_tk += 0.5
					if _tk >= 1.0 and not _krz_hotovo and not lehky:
						_krz_hotovo = true
						var t_k := Time.get_ticks_usec()
						_krz_text = _pod_krizem() + " (%.0f ms)" % ((Time.get_ticks_usec() - t_k) / 1000.0)
			_panel.text = "FPS %d · nejdelší %.0f ms · %s · záseků %d, pomalých %d%s" % [Engine.get_frames_per_second(), _max_dt_panel * 1000.0, poloha_text(),
					zaseku, pomalych, (main.kvalita.panel_text() if main and main.get("kvalita") else "") + "\npod křížem: " + _krz_text + (("\n" + String(_zaseky[0])) if not _zaseky.is_empty() else "")]
			_max_dt_panel = 0.0
		_kontrola_rozpoctu()
		_t += dt
		if _t >= 2.0 and not lehky:
			_t = 0.0
			_zapis("")
		return
	if plny:
		_troj_skupiny()
	_max_dt = maxf(_max_dt, _skut(dt))
	_max_dt_panel = maxf(_max_dt_panel, _skut(dt))
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
		_panel.size.x = maxf(400.0, get_viewport().get_visible_rect().size.x - 230.0)   # vpravo ikony menu
		_panel.text = "FPS %d  (%.1f ms, nejdelší %.0f ms) · %s\n%s\n%s\ntroj. (odhad LOD0): %s\nkreslení %d · trojúhelníky %.2f M · objekty %d\n%s\n%s\n%s\n%s\nzáseky: %s" % [
			Engine.get_frames_per_second(), 1000.0 / maxf(1.0, Engine.get_frames_per_second()), _max_dt_panel * 1000.0, poloha_text(),
			"špička %.0f ms: skripty (měřené) %.1f, fyzika %.1f, CPU kreslení %.1f, GPU %s (průměr %s) ms · špiček %d" % [_sp[0], _sp[1], _sp[2], _sp[3], sp_gpu,
				gpu_t, _sp_n],
			"nejdražší: %s · nové uzly %d, materiály %d · %s · panel %.1f ms" % [_sp_text, _sp_geom, _sp_mat, _svetla_text(), _rezie_ms],
			_skup_text,
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000000.0,
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			_pamet_text(), _rust_text(), _plan_text(), sestaveni_text(), ("%d (pomalých snímků %d) · " % [zaseku, pomalych]) + " | ".join(_zaseky) if not _zaseky.is_empty() else "žádné"]
		_max_dt_panel = 0.0
		_sp = [0.0, 0.0, 0.0, 0.0, 0.0]
		_sp_n = 0
		_gpu_sum = 0.0
		_gpu_n = 0
	_kontrola_rozpoctu()
	_rezie_ms = (Time.get_ticks_usec() - d0) / 1000.0
	_t += dt
	if _t < 2.0 or lehky:
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
var _pss_ms := 0.0                       # trvani posledniho cteni PSS ve vlakne (ms)
var _pss_uloha := -1
var _pss_kb := -1


## Vlakno: PSS procesu z /proc/self/smaps_rollup (radek „Pss:" v kB); -1 = soubor neni.
func _pss_vlakno() -> void:
	var u0 := Time.get_ticks_usec()
	var kb := -1
	var f := FileAccess.open("/proc/self/smaps_rollup", FileAccess.READ)
	if f:
		while not f.eof_reached():
			var l := f.get_line()
			if l.begins_with("Pss:"):
				kb = int(l.trim_prefix("Pss:").strip_edges().split(" ")[0])
				break
		f.close()
	_pss_kb = kb
	_pss_ms = (Time.get_ticks_usec() - u0) / 1000.0


## Volna pamet systemu z /proc/meminfo (MemAvailable, kB -> B); -1 = nelze precist. Android OS.get_memory_info vraci 0.
static func _meminfo_dostupna() -> int:
	var f := FileAccess.open("/proc/meminfo", FileAccess.READ)
	if f == null:
		return -1
	while not f.eof_reached():
		var l := f.get_line()
		if l.begins_with("MemAvailable:"):
			return int(l.split(":")[1].strip_edges().split(" ")[0]) * 1024
	return -1


func ram_mb() -> int:
	if OS.get_name() == "Android":
		if _dbg == null:
			_dbg = JavaClassWrapper.wrap("android.os.Debug")
		if _dbg != null:
			_ram = int(_dbg.getNativeHeapAllocatedSize()) / 1048576
		var mi := OS.get_memory_info()
		var vol := int(mi.get("available", -1))
		if vol <= 0:
			vol = _meminfo_dostupna()              # tablet 0.99996/7: available i free = 0 ("volna -0 MB")
		if vol <= 0:
			vol = int(mi.get("free", -1))          # tablet 0.59b: available chybi (panel "volna 0")
		_volna = vol / 1048576 if vol > 0 else -1  # -1 = nezname (N/A), ne 0
		# pamet procesu (PSS, vsechny haldy + ovladac GPU): drahe volani, jednou za 30 s.
		# 15. 11. (panel tabletu 0.999998, docs/screens/misa_15_11 20, 23, 25: „před kreslením" 71, 145, 53 ms - vsechny
		# tri radky s „měřič PSS", 8 radku bez nej 1,5-7,3 ms): Debug.getPss() cetl smaps synchronne v hlavnim vlakne az
		# po razitku konce snimku (_konec_snimku) -> padalo do „před kreslením". Ted /proc/self/smaps_rollup ve vlakne
		# (WorkerThreadPool), hlavni vlakno jen prevezme hotove cislo (NEOVERENO NA ZARIZENI: dostupnost smaps_rollup,
		# pripadne cekani hlavniho vlakna na zamek pameti jadra behem cteni - snimky behem cteni nesou „měřič PSS").
		if _pss_uloha >= 0 and WorkerThreadPool.is_task_completed(_pss_uloha):
			WorkerThreadPool.wait_for_task_completion(_pss_uloha)
			_pss_uloha = -1
			_pss = _pss_kb / 1024 if _pss_kb > 0 else -1
		if _pss_uloha < 0 and ((not lehky and Time.get_ticks_msec() - _pss_t > 30000) or (lehky and _pss_hranice)):
			_pss_t = Time.get_ticks_msec()
			_pss_uloha = WorkerThreadPool.add_task(_pss_vlakno)
			_sn_ted["pss"] = true        # zasek v tomto snimku muze byt od mereni
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


## Lehky monitor (merici trasa): radek logu a mereni PSS jen tady - na hranici useku, kde se nemeri.
func trasa_hranice(pozn: String) -> void:
	_pss_hranice = true
	_zapis(pozn, false)
	_pss_hranice = false
	_t = 0.0
	_max_dt = 0.0
	_cpu_max = 0.0


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
	var rez := "plny" if bool(main.get("mereni_on")) else ("jenfps" if bool(main.get("mereni_fps")) else "vyp")
	var r := "[panel %s, snimek prumer %.1f ms] " % [rez, _sn_prumer] + "%ds fps %d (nejdelsi snimek %.0f ms, proces max %.1f ms) | halda %d MB (max %d, volna %d, pss %d, trend %s) | gpu %d MB (tex %d, buf %d) | troj %.1f M | kresleni %d | obj %d | uzly %d (objekty %d, zdroje %d, sirotci %d) | %s | hrac %d,%d,%d %s" % [
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
			var u0 := Time.get_ticks_usec()
			WorkerThreadPool.wait_for_task_completion(_zapis_uloha)
			_zapis_uloha = -1
			var cek := (Time.get_ticks_usec() - u0) / 1000.0
			if cek > 20.0:                # overeni podezreni: kolik hlavni vlakno cekalo na zapis ve vlakne
				_radky.append("cekani na predchozi zapis %.0f ms (%s)" % [cek, pozn])
				text += _radky[-1] + "\n"
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
	_pridano_uzlu += 1
	if lehky:
		return                             # lehky monitor: jen citac (bez materialu a geometrii)
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
		var nd0: Variant = _sk_zas.pop_back()       # uzel mohl byt mezitim uvolnen (typovane prirazeni = SCRIPT ERROR)
		kroku += 1
		if not is_instance_valid(nd0):
			continue
		var nd: Node = nd0
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


var _pipe_minule := 0
var _pipe_pred_snimku := 0


## Soucet sestavenych pipeline (shaderu) od startu: canvas, mesh, surface, draw, specialization.
func _pipeline_soucet() -> int:
	var n := 0
	for k in [RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_CANVAS, RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_MESH,
			RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_SURFACE, RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_DRAW,
			RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_SPECIALIZATION]:
		n += int(RenderingServer.get_rendering_info(k))
	return n
