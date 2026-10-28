extends Node3D
const Pravidla := preload("res://scripts/pravidla.gd")
## Odkaz Havrana: intro, hlavni menu, ukladani a hra (Příběh / Pískoviště).
## Svet je vymodelovany v Blenderu (blender/export_game.py) a nacita ho svet.gd.

const Svet := preload("res://scripts/svet.gd")
const Daylight := preload("res://scripts/daylight.gd")
const Player := preload("res://scripts/player.gd")
const Life := preload("res://scripts/life.gd")
const Hud := preload("res://scripts/hud.gd")
const Pad := preload("res://scripts/pad.gd")
const Menu := preload("res://scripts/menu.gd")
const Pohyb := preload("res://scripts/pohyb.gd")
const Data := preload("res://scripts/data.gd")
const Predmety := preload("res://scripts/predmety.gd")
const MenuHrace := preload("res://scripts/menu_hrace.gd")
const Mapa := preload("res://scripts/mapa.gd")

const QUALITY_NAMES := ["Nízká", "Střední", "Vysoká"]
const SENS := [0.35, 0.5, 0.7, 1.0, 1.25, 1.5, 1.8]
const SENS_NAMES := ["Velmi nízká", "Nízká", "Mírná", "Normální", "Vyšší", "Vysoká", "Velmi vysoká"]
## pohyb packou: exponent krivky (vetsi = vic mista pro pomalou chuzi, beh az na doraz)
const POHYB := [2.2, 1.6, 1.0]
const POHYB_NAMES := ["Jemný", "Střední", "Přímý"]
const HUDBA_DB := -6.0            # hudba pod ruchy a zvuky; hlasitost ridi kanal "Hudba" (nastaveni)
const SPAWN := Vector3(2.5, 0.0, 40.0)
const SPAWN_LOOK := Vector3(0.0, 4.5, 15.0)
const SAVE_DIR := "user://ulozeni"
const MODE_NAMES := {"pribeh": "Příběh", "piskoviste": "Pískoviště"}

var info := {"rooms": [], "fires": [], "use": [], "smoke": [], "targets": []}
var svet: RefCounted
var world: Node3D
var day: Node
var player: CharacterBody3D
var telo: Node3D                 # telo hrace v prvni osobe (scripts/telo.gd)
var kun: CharacterBody3D         # kun hrace (scripts/kun.gd)
var kun_drzet_cestu := true      # nastaveni: kun pri jizde sam drzi cestu (KCD2)
var life: Node3D
var voda: Node
var bow: Node3D = null
var hud: CanvasLayer
var pad: Node
var menu: CanvasLayer
var ready_done := false
var mode := ""
var objevena: Array = []         # pribeh: objevena mista (ruiny) - na mape a k rychlemu cestovani

var quality := 1
var sens_i := 3
var pohyb_i := 1
var hudba_on := true
var mereni_on := false
var mereni_fps := false               # radce 07:15 A: panel stoji 4-17 ms - vychozi jen radek FPS, plny panel na vyzadani
# Test pameti (0.59c, pady = RAM roste i bez pohybu): rezim vypina jednu vec kresleni, panel ukazuje rust MB/min
# 0.59e: postupne - rezim k vypne kroky 1..k (prvni rezim, kde RAM prestane rust = vinik)
# 0.59g: kazdy krok vypne JEN svou vec (ostatni zapnute), nejdriv cele 3D - pad za 30 s az 2 min, kroky po 15 s
const TEST_PAMETI := ["vše zapnuté", "bez 3D kreslení", "bez louky", "bez rostlin, předmětů a tvrze", "bez života a zvuků",
		"bez stínů", "bez MSAA", "vše zapnuté"]
var _test_stav := {}
var _test_auto := false
# test zaseku (Misa 28. 10.: „at to meri samo a potom da zpravu pro kopirovani, nechci furt neco prepinat“): hra sama
# vystrida varianty z pravidla/svet/hrac.json test_zaseku, kazdou projde stejnou trasou, zmeri
# percentily snimku a mista spicek a na konci zprava do schranky
var _zas := {}
# hranice kresleni (pravidla/svet/svet.json): kraj.py pasmo okoli bez 35-60 m (Misa 0.69 (308,1329): za hranou bile desky obzoru)
static var HRANICE := Rect2(Pravidla.cti("svet", "hranice_kresleni")["x0"], Pravidla.cti("svet", "hranice_kresleni")["z0"],
		Pravidla.cti("svet", "hranice_kresleni")["x1"] - Pravidla.cti("svet", "hranice_kresleni")["x0"],
		Pravidla.cti("svet", "hranice_kresleni")["z1"] - Pravidla.cti("svet", "hranice_kresleni")["z0"])
var _hranice_t := 0.0
var _test_chuze: Array = []                  # [start, smer, ujito] - test chodi sam tam a zpet
var _test_fps := Vector3.ZERO                # [snimku, cas, nejdelsi dt] posledni 10 s kroku
var test_vysledky: PackedStringArray = []      # "krok: MB/min" (panel)
var _test_t := 0.0
var _test_ram0 := -1
const TEST_KROK_S := 15.0            # rust za poslednich 10 s kroku                  # uzel -> puvodni process_mode / visible
var test_pameti := 0
var _kam_t := 0.0
var msaa_on := false
# radce 16:30 K1: krok fyziky - 0 = 60 Hz/3 kroky (puvodni), 1 = 60 Hz/2 kroky, 2 = 30 Hz/2 kroky (interpolace zapnuta)
var fyzika_i := 1
var snimky_i := 0                 # A/B mikrosekani (reserse 28. 10.): 0 volne, 1 = pevnych 30 FPS (rovnomerne snimky)
const FYZIKA_NAMES := ["60 Hz, až 3 kroky", "60 Hz, až 2 kroky", "30 Hz, až 2 kroky"]
const SNIMKY_NAMES := ["volně (co tablet zvládne)", "pevně 30 FPS (rovnoměrně)"]
var plne_3d := false
var rozliseni_i := 0                  # 0.64: 3D rozliseni 0 snizene (podle kvality), 1 stredni 80 %, 2 plne
var diag: Node            # panel s FPS, kreslenim, trojuhelniky a pameti (nastaveni)
var hudba_vol := 0.7
var zvuky_on := true
var zvuky_vol := 1.0
var _cfg := ConfigFile.new()
var _use: Dictionary = {}
var pohyb: Node
var predmety: Node
var build_mode := false        # piskoviste: jen umistovat, presouvat a odstranovat predmety
var menu_hrace: CanvasLayer
var mapa: CanvasLayer
var ruchy: Node                    # zvuky prostredi podle mista, potok, rybnik, zvirata
var sber: Node                     # sber bylin a hub, dovednost bylinkarstvi
var _pending_save: Dictionary = {}
var _hudba: AudioStreamPlayer          # dobovy podkres uvnitr hradeb (Kevin MacLeod, CC BY 4.0)
var _hudba_i := -1
var _uvnitr := false
var _hudba_tw: Tween


func _ready() -> void:
	get_tree().quit_on_go_back = false
	get_tree().node_added.connect(_pred_novy_uzel)
	# hlidac vykonu a zprava o padu (user://diag.log) bezi od startu aplikace, i behem nacitani sveta
	diag = preload("res://scripts/diag.gd").new()
	diag.name = "Diag"
	add_child(diag)
	diag.setup(self)
	_cfg.load("user://nastaveni.cfg")
	quality = int(_cfg.get_value("hra", "kvalita", 1 if OS.has_feature("mobile") else 2))
	if OS.has_environment("TVRZ_MERENI"):
		quality = 1                      # mereni rozpoctu se stejnou kvalitou jako tablet
	sens_i = clampi(int(_cfg.get_value("hra", "citlivost2", [1, 3, 5][clampi(int(_cfg.get_value("hra", "citlivost", 1)), 0, 2)])), 0, SENS.size() - 1)
	pohyb_i = clampi(int(_cfg.get_value("hra", "pohyb", 1)), 0, POHYB.size() - 1)
	kun_drzet_cestu = bool(_cfg.get_value("hra", "kun_cesta", true))
	var stara := int(_cfg.get_value("hra", "hudba", 2))          # starsi nastaveni: 0 vypnuto, 1-3 hlasitost
	hudba_on = bool(_cfg.get_value("zvuk", "hudba_on", stara != 0))
	hudba_vol = float(_cfg.get_value("zvuk", "hudba_vol", [0.7, 0.35, 0.6, 0.9][clampi(stara, 0, 3)]))
	zvuky_on = bool(_cfg.get_value("zvuk", "zvuky_on", true))
	mereni_on = bool(_cfg.get_value("hra", "mereni", false))
	mereni_fps = bool(_cfg.get_value("hra", "mereni_fps", false))
	if mereni_on:                        # radce 13:40: po startu nejvys radek FPS, plny panel jen kdyz ho Misa zapne
		mereni_on = false
		mereni_fps = true
	if OS.has_environment("TVRZ_PANEL"):
		mereni_on = true                 # test: panel mereni i ve snimcich
	# 0.59h: unik pameti na tabletu jen pri 3D kresleni (test: bez 3D +0 MB/min), od 0.57c (MSAA 4x + 0,55x):
	# na tabletu vychozi bez MSAA; obe volby se uplatni od startu (za behu ovladac uz pamet zabral)
	msaa_on = bool(_cfg.get_value("hra", "msaa", not OS.has_feature("mobile")))
	fyzika_i = int(_cfg.get_value("hra", "fyzika", 1))
	snimky_i = int(_cfg.get_value("hra", "snimky", 0))
	plne_3d = bool(_cfg.get_value("hra", "plne_3d", false))
	rozliseni_i = clampi(int(_cfg.get_value("hra", "rozliseni", 2 if plne_3d else 0)), 0, 2)
	zvuky_vol = float(_cfg.get_value("zvuk", "zvuky_vol", 1.0))
	_audio_buses()
	menu = Menu.new()
	add_child(menu)
	menu.action.connect(_on_menu_action)
	menu.music.bus = "Hudba"
	menu.music.volume_db = HUDBA_DB
	menu.saves = _list_saves()
	_update_settings_texts()
	if OS.has_environment("TVRZ_SMOKE") or OS.has_environment("TVRZ_WALK") or OS.has_environment("TVRZ_INV_SHOT") or OS.has_environment("TVRZ_SAVETEST") or OS.has_environment("TVRZ_TALIR") or OS.has_environment("TVRZ_LOUC") or OS.has_environment("TVRZ_POHLED") or OS.has_environment("TVRZ_MERENI") or OS.has_environment("TVRZ_DALKA") or OS.has_environment("TVRZ_MAPA") or OS.has_environment("TVRZ_TEST") or OS.has_environment("TVRZ_ROZSEV") or OS.has_environment("TVRZ_JIZDA"):
		_start("piskoviste", {})
		return
	menu.play_intro()
	if OS.has_environment("TVRZ_MENU_SHOT"):
		_menu_shot(OS.get_environment("TVRZ_MENU_SHOT"))


func _menu_shot(path: String) -> void:
	# kontrola rozlozeni menu: snimek hlavni stranky a stranky Hrat
	await get_tree().create_timer(1.0).timeout
	menu._end_intro()
	await get_tree().create_timer(1.2).timeout
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_0.png"))
	menu.show_page("help")
	await get_tree().create_timer(0.3).timeout
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_1.png"))
	get_tree().quit()


# ------------------------------------------------------------------ menu

func _on_menu_action(what: String, arg: Variant) -> void:
	match what:
		"story":
			_start("pribeh", {})
		"sandbox":
			_start("piskoviste", {})
		"continue":
			if not menu.saves.is_empty():
				_load_file(String(menu.saves[0]["file"]))
		"load":
			_load_file(String(arg))
		"resume":
			_pause(false)
		"save":
			if ready_done:
				# ulozit, zavrit nabidku a potvrdit ve hre (za nabidkou by hlaska nebyla videt)
				_save_game()
				menu.saves = _list_saves()
				_pause(false)
				life.sfx("ulozeno", -6.0)
				hud.toast("Hra uložena", 2.2)
		"save_quit":
			if ready_done:
				_save_game()
			_save_cfg()
			get_tree().quit()
		"set:quality":
			quality = (quality + 1) % 3
			if ready_done:
				apply_quality()
			_save_cfg()
		"set:sens":
			sens_i = (sens_i + 1) % SENS.size()
			if hud:
				hud.sens = SENS[sens_i]
			_save_cfg()
		"set:kun":
			kun_drzet_cestu = not kun_drzet_cestu
			if kun:
				kun.drzet_cestu = kun_drzet_cestu
			_save_cfg()
		"set:pohyb":
			pohyb_i = (pohyb_i + 1) % POHYB.size()
			if player:
				player.move_curve = POHYB[pohyb_i]
			_save_cfg()
		"set:music":
			hudba_on = not hudba_on
			apply_audio()
			if not hudba_on:
				menu.music.stop()
			elif not menu.music.playing and not ready_done:
				menu.music.play()
			_save_cfg()
		"set:mereni":
			# vypnuto -> jen FPS -> plny panel -> vypnuto
			if mereni_on:
				mereni_on = false
				mereni_fps = false
			elif mereni_fps:
				mereni_fps = false
				mereni_on = true
			else:
				mereni_fps = true
			_save_cfg()
		"set:log":
			var n: int = diag.zkopiruj_log()
			OS.alert("Záznam měření je ve schránce (%d znaků). Vlož ho do chatu (podržet prst → Vložit)." % n, "Odkaz Havrana")
		"set:fyzika":
			fyzika_i = (fyzika_i + 1) % 3
			_save_cfg()
			apply_fyzika()
		"set:test_zaseku":
			if day and ready_done and _zas.is_empty() and not _test_auto:
				_zaseky_start()
			elif not _zas.is_empty():
				_zaseky_konec(true)
		"set:snimky":
			snimky_i = (snimky_i + 1) % 2
			_save_cfg()
			apply_fyzika()
		"set:msaa":
			msaa_on = not msaa_on
			_save_cfg()
			if ready_done:
				apply_quality()
		"set:plne_3d":
			rozliseni_i = (rozliseni_i + 1) % 3
			plne_3d = rozliseni_i == 2
			_save_cfg()
			if ready_done:
				apply_quality()
		"set:test_pameti":
			# automaticky: kazdych 40 s dalsi krok (od kroku 6 neni HUD - rucne by nesel prepnout)
			if day and ready_done and not _test_auto and day.interior > 0.3:
				hud.toast("Test výkonu jen venku", 1.5)
			elif day and ready_done:
				_test_auto = not _test_auto
				test_pameti = 0
				_test_t = 0.0
				_test_ram0 = -1
				test_vysledky.clear()
				# Misa 0.65: "vystrelilo me do vysky, nemohl jsem dolu" - test vypnuty rucne nechal let zapnuty
				if not _test_auto and not _test_chuze.is_empty():
					_test_chuze = []
					player.set_flying(false)
				if _test_auto:
					mereni_on = true
					# 0.65 (Misa: mikrosekani pri chuzi tvrz -> stan): test chodi sam tam a zpet 60 m ve smeru pohledu,
					# 5 m/s - kazdy krok meri FPS a nejdelsi snimek pri chuzi (nacitani bunek), ne ve stoje
					_test_chuze = [Vector2(player.global_position.x, player.global_position.z),
							Vector2(-sin(player.yaw), -cos(player.yaw)), 0.0]
					player.set_flying(true)
					diag.faze("TEST PAMETI start")
				apply_quality()
		"set:zvuky":
			zvuky_on = not zvuky_on
			apply_audio()
			_save_cfg()
		"vol:hudba", "vol:zvuky":
			# posuvnik: jen hlasitost kanalu, stranka nastaveni se nepřekresluje (tah by se prerusil)
			if what == "vol:hudba":
				hudba_vol = float(arg)
			else:
				zvuky_vol = float(arg)
			apply_audio()
			_save_cfg()
			return
		"set:time":
			if day:
				day.set_time(day.next_key(), 2.0)
	_update_settings_texts()


func _update_settings_texts() -> void:
	var t := {
		"quality": "Grafika: %s" % QUALITY_NAMES[quality],
		"sens": "Citlivost otáčení: %s" % SENS_NAMES[sens_i],
		"pohyb": "Pohyb páčkou: %s" % POHYB_NAMES[pohyb_i],
		"kun": "Kůň drží cestu: %s" % ("ano" if kun_drzet_cestu else "ne"),
		"music": "Hudba: %s" % ("zapnutá" if hudba_on else "vypnutá"),
		"zvuky": "Zvuky: %s" % ("zapnuté" if zvuky_on else "vypnuté"),
		"mereni": "Měření výkonu: %s" % ("plný panel" if mereni_on else ("jen FPS" if mereni_fps else "vypnuté")),
		"msaa": "Vyhlazování hran (MSAA): %s" % ("zapnuté" if msaa_on else "vypnuté"),
		"fyzika": "Fyzika (měření záseků): %s" % FYZIKA_NAMES[fyzika_i],
		"snimky": "Snímky (měření záseků): %s" % SNIMKY_NAMES[snimky_i],
		"test_zaseku": "Test záseků (sám vystřídá nastavení, jde trasou, pak zpráva ke zkopírování): %s" % ("běží – zrušit" if not _zas.is_empty() else "spustit"),
		"plne_3d": "Rozlišení 3D: %s" % ["snížené (nejrychlejší)", "střední 80 %", "plné (nejpomalejší)"][rozliseni_i],
		"log": "Zkopírovat záznam měření do schránky (pak vložit do chatu)",
		"test_pameti": "Test výkonu při chůzi (2 min, jde sám 60 m směrem pohledu): %s" % ("běží" if _test_auto else "spustit"),
		"vol:hudba": hudba_vol,
		"vol:zvuky": zvuky_vol,
	}
	if day:
		t["time"] = "Denní doba: %s (%s)" % [day.NAMES[day.current], day.clock_text()]
	menu.refresh_settings(t)


func _pause(on: bool) -> void:
	if not ready_done:
		return
	get_tree().paused = on
	if on:
		hud.show_menu(false)
		hud.paused = true
		menu.saves = _list_saves()
		_update_settings_texts()
		menu.show_menu(true, true)
		hud._release_all()
	else:
		menu.hide_menu()
		hud.paused = false


# ------------------------------------------------------------------ start hry

func _start(p_mode: String, save: Dictionary) -> void:
	if ready_done:
		# uz bezi svet: jen presun hrace a rezim
		mode = p_mode
		_apply_mode()
		_apply_save(save)
		_pause(false)
		return
	mode = p_mode
	_pending_save = save
	menu.hide_menu()
	var tw := create_tween()
	tw.tween_property(menu.music, "volume_db", -40.0, 3.0)
	tw.tween_callback(menu.music.stop)
	hud = Hud.new()
	add_child(hud)
	await get_tree().process_frame
	await get_tree().process_frame
	var dl := Data.new()
	add_child(dl)
	dl.status.connect(hud.loading_status)
	var ok: bool = await dl.ensure()
	if not ok:
		return
	hud.loading_status("Načítám tvrz…")
	diag.faze("data stazena, stavim svet")
	_build()


func _build() -> void:
	var t0 := Time.get_ticks_msec()
	world = Node3D.new()
	world.name = "Svet"
	add_child(world)
	svet = Svet.new(info)
	svet.build(world, quality)
	diag.faze("svet postaven (modely, rostliny, kolize)")
	pohyb = Pohyb.new()
	pohyb.name = "Pohyb"
	add_child(pohyb)
	pohyb.setup(world.get_node("Tvrz"), svet.data.get("pohyb", []), info)
	pohyb.na_zem.call_deferred("ves_")
	predmety = Predmety.new()
	predmety.name = "PredmetyHra"
	add_child(predmety)
	predmety.setup(self, world)
	menu_hrace = MenuHrace.new()
	menu_hrace.main = self
	menu_hrace.P = predmety
	add_child(menu_hrace)
	mapa = Mapa.new()
	mapa.main = self
	add_child(mapa)
	day = Daylight.new()
	day.name = "Den"
	day.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(day)
	day.time_changed.connect(predmety.on_time)
	day.setup(String(_cfg.get_value("hra", "cas", "odpoledne")))
	# vyskova mlha (rano v nivach) jen nad nejnizsim mistem terenu: pevna hranice -6 m lezela nad celym udolim
	# (ves, louky -8 az -21 m), krajina pak stala cela v huste mlze a byla vybledla az bila
	var dno := 0.0
	for n in world.find_children("Teren*", "MeshInstance3D", true, false):
		dno = minf(dno, (n as MeshInstance3D).get_aabb().position.y)
	day.env.fog_height = dno + 4.0

	player = Player.new()
	player.name = "Hrac"
	add_child(player)
	player.place(SPAWN + Vector3(0, 30, 0), SPAWN_LOOK)
	# telo hrace v prvni osobe (radce 21:20 bod 6): ruce a nohy jsou telo postavy, kamera v hlave; do hry az po hotovem
	# svete (radce 21:45) - jizda.json zapojeno_do_hry, jinak jen zkouska TVRZ_JIZDA
	var funkce_jizda := bool(Pravidla.cti("jizda", "zapojeno_do_hry")) or OS.has_environment("TVRZ_JIZDA")
	if funkce_jizda:
		telo = preload("res://scripts/telo.gd").new()
		telo.name = "TeloHrace"
		add_child(telo)
		if not telo.setup(player):
			telo.queue_free()
			telo = null

	life = Life.new()
	life.name = "Zivot"
	add_child(life)
	life.setup(info, day, player)
	# kun hrace (Misa 27. 10. noc, jizda podle KCD2): zaznam lokace.json kun
	var kz: Dictionary = Pravidla.cti("lokace", "kun")
	var kz_x := float(kz["stred"][0]) + float(kz["natoceni"])          # zaznam se cte vzdy (test pravidla_cteni)
	if not (bool(Pravidla.cti("jizda", "zapojeno_do_hry")) or OS.has_environment("TVRZ_JIZDA")) or is_nan(kz_x):
		kz = {}
	if not kz.is_empty():
		kun = preload("res://scripts/kun.gd").new()
		kun.name = "Kun"
		add_child(kun)
		var kx := float(kz["stred"][0])
		var kzz := float(kz["stred"][1])
		if kun.setup(self, Vector3(kx, svet._vyska(kx, kzz) + 0.1, kzz), float(kz["natoceni"])):
			kun.kopyto.connect(func(sf: String, h: float) -> void: life.step_sound(sf, h))
		else:
			kun.queue_free()
			kun = null
	var lide: Node = preload("res://scripts/lide.gd").new()
	lide.name = "Lide"
	world.add_child(lide)
	lide.setup(self)
	player.surface_at = life.surface_at
	player.stepped.connect(life.step_sound)
	# louka v cele krajine (trsy ze stebel, byliny, kvety) misto starych karet travy
	var louka: Node3D = preload("res://scripts/louka.gd").new()
	louka.name = "Louka"
	louka.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF     # staticke MultiMeshe (viz svet.gd Rostliny)
	add_child(louka)
	louka.setup(self)
	diag.faze("louka")
	voda = preload("res://scripts/voda.gd").new()
	voda.name = "Voda"
	add_child(voda)
	voda.setup(self)
	ruchy = preload("res://scripts/ruchy.gd").new()
	ruchy.name = "Ruchy"
	add_child(ruchy)
	ruchy.setup(self)
	sber = preload("res://scripts/sber.gd").new()
	sber.name = "Sber"
	add_child(sber)
	sber.setup(self)

	hud.player = player
	hud.bow = null
	hud.sens = SENS[sens_i]
	player.move_curve = POHYB[pohyb_i]
	hud.use_pressed.connect(func() -> void: do_act())
	hud.use2_pressed.connect(_on_use2)
	hud.act_pressed.connect(func(i: int) -> void: do_act(i))
	hud.menu_action.connect(func(w: String) -> void:
		if w == "brasna":
			open_player_menu()
		elif w == "stavba":
			toggle_build()
		elif w == "mapa":
			open_map()
		else:
			_pause(true))
	pad = Pad.new()
	pad.name = "Ovladac"
	pad.main = self
	add_child(pad)
	apply_quality()
	diag.faze("kvalita nastavena, prvni snimky")
	# hrac stoji na terenu: najdi zem paprskem shora
	await get_tree().physics_frame
	await get_tree().physics_frame
	svet.dosednout(world)
	svet.tvrz_kryti(world.get_world_3d().direct_space_state)
	if not OS.has_environment("TVRZ_BEZ_OKOLI"):          # srovnani pameti (test pamet)
		svet.kolize_rozdel()
		svet.rostliny_rozdel(world.find_child("Rostliny", true, false))
	svet.kolize_okoli(SPAWN, true)
	svet.rostliny_okoli(SPAWN, true)
	await get_tree().physics_frame
	player.place(_ground(SPAWN), SPAWN_LOOK)
	_apply_mode()
	_apply_save(_pending_save)
	print("build ms: ", Time.get_ticks_msec() - t0, "  fires ", info["fires"].size(), " rooms ", info["rooms"].size(),
			" use ", info["use"].size())
	await _predehrej_shadery()
	ready_done = true
	diag.faze("hra bezi")
	hud.hide_loading()
	if OS.has_environment("TVRZ_INV_SHOT"):
		_inv_shot(OS.get_environment("TVRZ_INV_SHOT"))
	elif OS.has_environment("TVRZ_DALKA"):
		for p: Vector3 in [Vector3(-12, 0, 600), Vector3(470, 0, 830), Vector3(-170, 0, 450)]:
			player.place(Vector3(p.x, _ground_hi(p.x, p.z) + 0.5, p.z), Vector3(p.x, 0, p.z + 10))
			for i in 60:
				await get_tree().physics_frame
			print("DALKA cil %s -> %s" % [p, player.global_position])
		get_tree().quit()
	elif OS.has_environment("TVRZ_ROZSEV"):
		# offline rozsev louky (radce 07:30 A): po zmene sveta, pred vydanim
		get_node("Louka").rozsev_vse()
		get_tree().quit()
	elif OS.has_environment("TVRZ_MERENI"):
		await _mereni(OS.get_environment("TVRZ_MERENI"))
		get_tree().quit()
	elif OS.has_environment("TVRZ_JIZDA"):
		await _jizda_test(OS.get_environment("TVRZ_JIZDA"))
		get_tree().quit()
	elif OS.has_environment("TVRZ_POHLED"):
		await _pohled_shot(OS.get_environment("TVRZ_POHLED"))
		get_tree().quit()
	elif OS.has_environment("TVRZ_MAPA"):
		# snimek mapy, dotaz na rychle cestovani do Lhoty, cesta, snimek po prichodu
		var out := OS.get_environment("TVRZ_MAPA")
		for i in 30:
			await get_tree().process_frame
		open_map()
		await get_tree().create_timer(0.5).timeout
		get_viewport().get_texture().get_image().save_png(out + "_mapa.png")
		mapa.sel = 1
		mapa._ask()
		mapa._c.queue_redraw()
		await get_tree().create_timer(0.4).timeout
		get_viewport().get_texture().get_image().save_png(out + "_dotaz.png")
		var h0: float = day.hour
		mapa._answer(true)
		await get_tree().create_timer(4.0).timeout
		print("MAPA cesta: hrac %s, cas %.2f -> %.2f" % [player.global_position, h0, day.hour])
		get_viewport().get_texture().get_image().save_png(out + "_lhota.png")
		get_tree().quit()
	elif OS.has_environment("TVRZ_LOUC"):
		await _louc_shot(OS.get_environment("TVRZ_LOUC"))
		get_tree().quit()
	elif OS.has_environment("TVRZ_TALIR"):
		for i in 5:
			await get_tree().physics_frame
		await _talir_test()
		get_tree().quit()
	elif OS.has_environment("TVRZ_SAVETEST"):
		_save_test()
	elif OS.has_environment("TVRZ_WALK"):
		_walk_test()
	elif OS.has_environment("TVRZ_SMOKE"):
		_smoke()
	elif OS.has_environment("TVRZ_TEST"):
		add_child(load("res://scripts/dev_test.gd").new())


func _inv_shot(path: String) -> void:
	# snimky menu hrace: brasna, staveni, vymena s truhlou
	player.place(Vector3(-7.0, 0.1, 11.0), Vector3(-6.6, 0.5, 14.0))
	for i in 40:
		await get_tree().process_frame
	var pages := [["brasna", {}], ["staveni", {}], ["vymena", predmety.placed[0]]]
	for i in pages.size():
		menu_hrace.show_page(pages[i][0], pages[i][1])
		if i == 1:
			menu_hrace.tab = 1
		for k in 6:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(path.replace(".png", "_%d.png" % i))
		menu_hrace.close()
	# pokladani lavice na nadvori a pohled na truhlu ve zbrojnici
	player.place(Vector3(-2.0, 0.1, 2.0), Vector3(-2.0, 0.6, 6.0))
	predmety.begin_place("lavice", false)
	for k in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_3.png"))
	predmety.cancel_place()
	player.place(Vector3(-8.5, 0.1, 11.6), Vector3(-6.6, 0.4, 13.4))
	for k in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_4.png"))
	# noc: louc v drzaku ve zbrojnici a louc v ruce na nadvori
	day.set_time("noc", 0.01)
	predmety.spawn_on_wall("drzak_louce", Vector3(-7.5, 1.95, 12.0), Vector3(0, 0, 1))
	player.place(Vector3(-7.0, 0.1, 10.6), Vector3(-7.5, 1.6, 14.0))
	for k in 30:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_5.png"))
	predmety.hold("lucerna", true)
	player.place(Vector3(-3.0, 0.1, 2.0), Vector3(-3.6, 1.0, -1.6))
	for k in 30:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_6.png"))
	# stit na zed zbrojnice (pokladani na zed) a nabidka spanku
	predmety.hold("", false)
	player.place(Vector3(-7.0, 0.1, 11.2), Vector3(-7.0, 1.4, 14.0))
	predmety.begin_place("stit", false)
	for k in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_7.png"))
	predmety.cancel_place()
	offer_sleep()
	for k in 6:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_8.png"))
	menu_hrace.close()
	player.stand_up()
	# sin: krb, vyklenek s oknem, okno do nadvori, svitek s nabidkou u lucerny
	day.set_time("odpoledne", 0.01)
	var shots := [[Vector3(11.8, 0.1, -10.8), Vector3(17.0, 1.7, -10.8)], [Vector3(6.0, 0.1, -12.0), Vector3(6.0, 1.6, -16.0)],
			[Vector3(11.5, 0.1, -9.6), Vector3(11.5, 1.9, -6.0)]]
	for i in shots.size():
		player.place(shots[i][0], shots[i][1])
		for k in 30:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(path.replace(".png", "_%d.png" % (9 + i)))
	predmety.spawn({"id": "lucerna", "p": Vector3(-2.0, 0.0, 3.4), "yaw": 0.0, "obsah": {}, "hori": true})
	player.place(Vector3(-2.0, 0.1, 2.3), Vector3(-2.0, 0.3, 3.4))
	for k in 30:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_12.png"))
	print("SVITEK use %s, akce %s, sedi %s, menu %s" % [_use.get("kind", "nic"), acts, player.seated, menu_hrace.open])
	day.set_time("noc", 0.01)
	player.place(Vector3(11.8, 0.1, -10.8), Vector3(17.0, 1.2, -10.8))
	for k in 30:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_13.png"))
	get_tree().quit()


func _save_test() -> void:
	# ulozit, zmenit svet, nacist pres menu: poloha, predmety, brasna, mechanismy, krb, svetlo v ruce
	for i in 5:
		await get_tree().physics_frame
	player.place(Vector3(-3.0, 0.1, 4.0), Vector3(-3.0, 1.6, -10.0))
	predmety.spawn({"id": "stul_dubovy", "p": Vector3(-2.0, 0.0, 1.0), "yaw": 0.3, "obsah": {}})
	predmety.add_inv("jablko", 3)
	predmety.hold("lucerna", true)
	pohyb.toggle("most")
	life.set_fire("krb", false)
	for i in 400:
		await get_tree().physics_frame
	var before := {"pos": player.global_position.snapped(Vector3(0.01, 0.01, 0.01)), "n": predmety.placed.size(),
			"inv": predmety.inv.duplicate(), "most": pohyb.groups["most"]["target"], "krb": life.fire_on("krb"), "ruka": predmety.held_id}
	_pause(true)
	_on_menu_action("save", null)
	print("ULOZENI souboru %d" % _list_saves().size())
	_pause(false)
	player.place(Vector3(5.0, 0.1, 5.0), Vector3(0, 1.6, 0))
	predmety.delete(predmety.placed[-1])
	predmety.inv = {}
	predmety.hold("", false)
	pohyb.toggle("most")
	life.set_fire("krb", true)
	for i in 30:
		await get_tree().physics_frame
	_pause(true)
	menu.saves = _list_saves()
	_on_menu_action("load", menu.saves[0]["file"])
	for i in 30:
		await get_tree().physics_frame
	var after := {"pos": player.global_position.snapped(Vector3(0.01, 0.01, 0.01)), "n": predmety.placed.size(),
			"inv": predmety.inv.duplicate(), "most": pohyb.groups["most"]["target"], "krb": life.fire_on("krb"), "ruka": predmety.held_id}
	print("ULOZENI pred  ", before)
	print("ULOZENI po    ", after)
	print("ULOZENI pauza %s, menu %s" % [get_tree().paused, menu.visible])
	# hak na zed a stojan se zbranemi, automaticka svetla
	predmety.spawn_on_wall("hak_zbrane", Vector3(-7.0, 1.8, 12.0), Vector3(0, 0, 1), {"obsah": {"stit_rozmberk": 1}})
	predmety.spawn({"id": "stojan_zbrani", "p": Vector3(-8.2, 0.02, 13.2), "yaw": 0.0, "obsah": {"mec_dlouhy": 1, "halapartna": 1, "kopi": 1}})
	predmety.spawn({"id": "stojan_louce", "p": Vector3(-2.0, 0.0, 6.0), "yaw": 0.0, "obsah": {}})
	for r: Dictionary in predmety.placed:
		if r["id"] in ["hak_zbrane", "stojan_zbrani"]:
			print("ZAVESENO %s: %d" % [r["id"], r.get("_hung", []).size()])
		if r["id"] == "stojan_louce":
			day.set_time("poledne", 0.01)
			print("SVETLA stojan v poledne hori %s" % r.get("hori"))
			day.set_time("noc", 0.01)
			print("SVETLA stojan v noci hori %s" % r.get("hori"))
	print("PRIKOP mist s vodou %d" % life._moat_pts.size())
	# postaveni: vidle nastojato
	player.place(Vector3(-2.0, 0.1, 4.0), Vector3(-2.0, 0.3, 1.0))
	predmety.begin_place("vidle", false)
	predmety.toggle_tilt()
	for i in 4:
		await get_tree().physics_frame
	var npos: int = predmety.placed.size()
	predmety.confirm_place()
	menu_hrace.close()
	var vr: Dictionary = predmety.placed[-1]
	print("POSTAVENI vidle orient %s, vyska modelu %.2f, polozeno %d -> %d" % [vr.get("orient"), predmety.dims("vidle", int(vr.get("orient", 0)))[1], npos, predmety.placed.size()])
	# zbran do stojanu: miri na prvni volne misto
	var stj: Dictionary = {}
	for r: Dictionary in predmety.placed:
		if r["id"] == "stojan_zbrani":
			stj = r
	if not stj.is_empty():
		var used: int = predmety._used_slots(stj)
		var sl: Array = predmety.slots("stojan_zbrani")[used]
		var wp: Vector3 = (stj["node"] as Node3D).to_global(Vector3(sl[0], sl[1] + 0.8, sl[2]))
		player.place(wp + (stj["node"] as Node3D).global_transform.basis.z * -1.6 + Vector3(0, -1.5, 0), wp)
		predmety.begin_place("estok", false)
		for i in 4:
			await get_tree().physics_frame
			await get_tree().process_frame
		print("STOJAN cil nalezen %s" % (not predmety._snap.is_empty()))
		predmety.confirm_place()
		menu_hrace.close()
		print("STOJAN zbrani %d -> %d" % [used, predmety._used_slots(stj)])
	await _talir_test()
	predmety.cancel_place()
	if OS.has_environment("TVRZ_SHOT"):
		day.set_time("poledne", 0.01)
		predmety.hold("", false)
		player.place(Vector3(-6.4, 0.1, 10.7), Vector3(-6.4, 1.0, 14.0))
		for i in 30:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(OS.get_environment("TVRZ_SHOT"))
	# truhla ovladacem: otevrit A, presouvat D-padem, A presunout polozku
	var tr: Dictionary = {}
	for r: Dictionary in predmety.placed:
		if predmety.kat[r["id"]].has("kont"):
			tr = r
	tr["obsah"] = {"miska": 2, "lzice": 1}
	open_container(tr)
	_pad_press(JOY_BUTTON_A)
	print("TRUHLA hned po otevreni: truhla %s" % [tr["obsah"]])
	await get_tree().create_timer(0.4).timeout
	_pad_press(JOY_BUTTON_DPAD_DOWN)
	_pad_press(JOY_BUTTON_DPAD_DOWN)
	print("TRUHLA strana %d vyber %s (2 polozky, wrap)" % [menu_hrace.side, menu_hrace.sel])
	_pad_press(JOY_BUTTON_A)
	print("TRUHLA po A: truhla %s" % [tr["obsah"]])
	_pad_press(JOY_BUTTON_DPAD_LEFT)
	_pad_press(JOY_BUTTON_DPAD_UP)
	_pad_press(JOY_BUTTON_A)
	print("TRUHLA vlevo, nahoru (wrap na konec), A: strana %d vyber %s, truhla %s" % [menu_hrace.side, menu_hrace.sel, tr["obsah"]])
	menu_hrace.close()
	get_tree().quit()


var _pred_videno := {}                  # klic kombinace (mesh, multimesh, stin, prolinani, materialy) -> true
var _pred_fronta: Array = []            # A/B „zahrat shadery“ rezim 2: nove uzly ke dohrati
var _pred_dohrev: Node3D                # kopie pred kamerou, uvolni se po 3 snimcich
var _pred_snimku := 0


## Drobna kopie uzlu pred kamerou pro predehrati (kazda nova kombinace jednou); vraci pocet kopii.
func _pred_kopie(g: GeometryInstance3D, koren: Node3D) -> int:
	var mesh: Mesh = null
	var mm: MultiMesh = null
	if g is MultiMeshInstance3D:
		mm = (g as MultiMeshInstance3D).multimesh
		if mm == null or mm.mesh == null:
			return 0
		mesh = mm.mesh
	elif g is MeshInstance3D:
		mesh = (g as MeshInstance3D).mesh
	if mesh == null:
		return 0
	var klic := [mm != null, mm.use_colors if mm else false, mm.use_custom_data if mm else false,
			g.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, g.transparency > 0.0,
			g.visibility_range_fade_mode != GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED,
			g.material_override.get_rid() if g.material_override else RID()]
	for si in mesh.get_surface_count():
		var m: Material = mesh.surface_get_material(si)
		if g is MeshInstance3D and (g as MeshInstance3D).get_surface_override_material(si):
			m = (g as MeshInstance3D).get_surface_override_material(si)
		klic.append(m.get_rid() if m else RID())
	var k := str(klic)
	if _pred_videno.has(k):
		return 0
	_pred_videno[k] = true
	var n := 0
	# opaque kopie a (u prolinanych) kopie v pasmu prolinani visibility_range
	for prolin in (2 if klic[5] else 1):
		var kopie: GeometryInstance3D
		if mm:
			var m2 := MultiMesh.new()
			m2.transform_format = mm.transform_format
			m2.use_colors = mm.use_colors
			m2.use_custom_data = mm.use_custom_data
			m2.mesh = mesh
			m2.instance_count = 1
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = m2
			kopie = mmi
		else:
			var mi := MeshInstance3D.new()
			mi.mesh = mesh
			for si in mesh.get_surface_count():
				mi.set_surface_override_material(si, (g as MeshInstance3D).get_surface_override_material(si))
			kopie = mi
		kopie.material_override = g.material_override
		kopie.cast_shadow = g.cast_shadow
		kopie.transparency = g.transparency
		kopie.extra_cull_margin = 16384.0
		if prolin == 1:
			kopie.visibility_range_fade_mode = g.visibility_range_fade_mode
			kopie.visibility_range_end = 3.5
			kopie.visibility_range_end_margin = 2.0
		kopie.scale = Vector3.ONE * 0.002
		koren.add_child(kopie)
		n += 1
	return n


## Radce 13:40 (0.96 zaseky 0,6-1,9 s jen pri 1. pruchodu = sestaveni shaderu): natrvalo dohriva i uzly, ktere vzniknou za
## hry (planovac, louka, predmety): novou kombinaci nakresli jednou pred kamerou, nejvys 20 uzlu za snimek.
func _pred_novy_uzel(n: Node) -> void:
	if ready_done and n is GeometryInstance3D and not (n.get_parent() == _pred_dohrev):
		_pred_fronta.append(n)


func _pred_dohrivej() -> void:
	if _pred_dohrev and _pred_dohrev.get_child_count() > 0:
		_pred_snimku += 1
		if _pred_snimku > 3:
			for c in _pred_dohrev.get_children():
				c.queue_free()
			_pred_snimku = 0
	if _pred_fronta.is_empty() or player == null or player.cam == null:
		return
	if _pred_dohrev == null:
		_pred_dohrev = Node3D.new()
		_pred_dohrev.name = "Predehrati_dohrev"
		world.add_child(_pred_dohrev)
	var cam: Camera3D = player.cam
	_pred_dohrev.global_transform = Transform3D(cam.global_basis, cam.global_position - cam.global_basis.z * 3.0)
	for _i in mini(20, _pred_fronta.size()):
		var g: Variant = _pred_fronta.pop_back()
		if is_instance_valid(g):
			_pred_kopie(g as GeometryInstance3D, _pred_dohrev)


## Predehrati shaderu za nacitaci obrazovkou (0.62 bod 8, sekani pri vstupu do lesa/skal): renderer Compatibility
## sestavi program az pri prvnim kresleni materialu (Adreno 20-100 ms a skok RAM ovladace). Za jeden snimek se
## kazdy material sveta (i MultiMesh s custom daty/barvou, stin, prolinani visibility_range = pruhledny pruchod)
## nakresli jednou na drobne kopii pred kamerou, pak kopie zmizi. TVRZ_BEZ_PREDEHRATI=1 vypne (mereni).
func _predehrej_shadery() -> void:
	if OS.has_environment("TVRZ_BEZ_PREDEHRATI") or player == null or player.cam == null:
		return
	var t0 := Time.get_ticks_usec()
	var cam: Camera3D = player.cam
	var koren := Node3D.new()
	koren.name = "Predehrati"
	world.add_child(koren)
	koren.global_transform = Transform3D(cam.global_basis, cam.global_position - cam.global_basis.z * 3.0)
	var videno := _pred_videno
	var n := 0
	for gi: Node in find_children("*", "GeometryInstance3D", true, false):
		n += _pred_kopie(gi as GeometryInstance3D, koren)
	# radce 17:45 (mikrosekani "kde pribude novy material"): od 0.68 jsou rostliny mimo okoli startu jen data
	# (svet._rost_data) - predehrati je nevidelo a shader keru, rakosi a bylin se sestavoval az za chuze
	var rd: Dictionary = svet._rost_data if svet else {}
	for b: Vector2i in rd:
		for e: Dictionary in rd[b]:
			var k2 := str([e["mesh"], e["mat"], e["stin"], e["barvy"], e["data"]])
			if videno.has(k2):
				continue
			videno[k2] = true
			for prolin in 2:
				var m3 := MultiMesh.new()
				m3.transform_format = MultiMesh.TRANSFORM_3D
				m3.use_colors = e["barvy"]
				m3.use_custom_data = e["data"]
				m3.mesh = e["mesh"]
				m3.instance_count = 1
				var mmi3 := MultiMeshInstance3D.new()
				mmi3.multimesh = m3
				if e["mat"]:
					mmi3.material_override = e["mat"]
				mmi3.cast_shadow = e["stin"]
				mmi3.extra_cull_margin = 16384.0
				mmi3.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
				if prolin == 1:
					mmi3.visibility_range_end = 3.5
					mmi3.visibility_range_end_margin = 2.0
				mmi3.scale = Vector3.ONE * 0.002
				koren.add_child(mmi3)
				n += 1
	# varianty s vsesmerovym svetlem (louce vecer, Misa: "vecer louce" = spicka)
	var ls := OmniLight3D.new()
	ls.omni_range = 6.0
	ls.light_energy = 0.01
	koren.add_child(ls)
	var t1 := Time.get_ticks_usec()
	for i in 3:
		await get_tree().process_frame
	ls.shadow_enabled = true
	# radce 13:40: i bodove svetlo se stinem (lucerny, louce ve vsi) - samostatna varianta pruchodu v Compatibility
	var sp := SpotLight3D.new()
	sp.spot_range = 6.0
	sp.light_energy = 0.01
	sp.shadow_enabled = true
	koren.add_child(sp)
	for i in 2:
		await get_tree().process_frame
	koren.queue_free()
	var t2 := Time.get_ticks_usec()
	if OS.has_environment("TVRZ_TEST"):
		for i in 3:
			await get_tree().process_frame           # mereni: stejne 3 snimky bez kopii (rozdil = sestaveni shaderu)
	print("PREDEHRATI %d kopii (%d kombinaci), sber %.0f ms, 3 snimky s kopiemi %.0f ms, bez %.0f ms" % [n, videno.size(),
			(t1 - t0) / 1000.0, (t2 - t1) / 1000.0, (Time.get_ticks_usec() - t2) / 1000.0])


func _pad_press(b: JoyButton) -> void:
	for pr in [true, false]:
		var ev := InputEventJoypadButton.new()
		ev.button_index = b
		ev.pressed = pr
		Input.parse_input_event(ev)
		Input.flush_buffered_events()


func _walk_test() -> void:
	# automaticka pochuze: kazda trasa = start, smer, ocekavany cil (x/z blizko, vyska)
	var routes := [
		["most", Vector3(0.0, 0.0, 33.0), Vector3(0.0, 1.6, 0.0), 420, Vector3(0.0, 0.0, 12.0), 1.2],
		["schody_dole", Vector3(9.4, 0.0, 5.65), Vector3(-30.0, 1.6, 5.65), 260, Vector3(4.6, 3.25, 5.65), 0.8],
		["schody_hradba", Vector3(4.6, 3.4, 5.5), Vector3(4.6, 4.8, 40.0), 300, Vector3(4.6, 6.5, 12.0), 0.8],
		["vez_1", Vector3(-25.75, 0.6, -10.9), Vector3(-25.75, 1.6, -30.0), 240, Vector3(-25.75, 3.25, -14.6), 0.8],
		["vez_2", Vector3(-24.6, 3.8, -14.75), Vector3(10.0, 5.0, -14.75), 300, Vector3(-21.6, 6.5, -14.75), 0.8],
		["ochoz_brana", Vector3(-8.0, 6.6, 14.65), Vector3(10.0, 8.1, 14.65), 300, Vector3(0.0, 6.5, 14.65), 0.8],
		["kovarna", Vector3(-13.2, 0.0, 4.0), Vector3(-13.2, 1.6, 30.0), 300, Vector3(-13.2, 0.0, 12.5), 0.8],
		["podesta_ochoz", Vector3(4.6, 6.6, 10.2), Vector3(4.6, 8.1, 40.0), 200, Vector3(4.6, 6.5, 14.9), 0.8],
		["ochoz_brana_vychod", Vector3(7.0, 6.6, 14.65), Vector3(-30.0, 8.1, 14.65), 300, Vector3(-8.0, 6.5, 14.65), 0.8],
		["staj", Vector3(-15.0, 0.0, -2.2), Vector3(-40.0, 1.6, -2.2), 300, Vector3(-24.2, 0.0, -2.2), 0.8],
		["palac_pavlac", Vector3(-10.4, 0.0, -6.3), Vector3(10.0, 1.6, -6.3), 360, Vector3(-3.0, 3.9, -6.2), 1.0],
	]
	# dvere mezi kovarnou a zbrojnici otevrit (trasa kovarna_zbrojnice)
	for u: Dictionary in info["use"]:
		if u.get("kind", "") == "pohyb" and (u["pos"] as Vector3).distance_to(Vector3(-11.0, 1.2, 11.55)) < 1.0:
			pohyb.toggle(u["id"])
			print("POHYB dvere kovarna-zbrojnice: ", u["id"])
	routes.append(["kovarna_zbrojnice", Vector3(-14.0, 0.0, 11.55), Vector3(10.0, 1.6, 11.55), 300, Vector3(-8.0, 0.0, 11.55), 0.8])
	for r: Array in routes:
		var start: Vector3 = r[1]
		player.flying = false
		player.place(_ground(start + Vector3(0, 0.5, 0)) if start.y < 0.5 else start, r[2] + Vector3(0, start.y, 0))
		for i in 10:
			await get_tree().physics_frame
		player.move_input = Vector2(0, 1)
		var top := -100.0
		for i in int(r[3]):
			await get_tree().physics_frame
			top = maxf(top, player.global_position.y)
		player.move_input = Vector2.ZERO
		var p := player.global_position
		var goal: Vector3 = r[4]
		print("CHUZE %s: konec %s, max vyska %.2f, cil %s" % [r[0], p.snapped(Vector3(0.01, 0.01, 0.01)), top, goal])
	# predmety: vychozi truhla, vybrat ji, polozit sud z katalogu
	print("PREDMETY polozene: %d, brasna: %s" % [predmety.placed.size(), predmety.inv])
	open_container(predmety.placed[0])
	menu_hrace._take_all()
	print("PREDMETY po vybrani truhly: brasna %s, truhla %s" % [predmety.inv, predmety.placed[0]["obsah"]])
	menu_hrace.close()
	predmety.begin_place("sud", false)
	for i in 3:
		await get_tree().physics_frame
	predmety.confirm_place()
	predmety.cancel_place()
	menu_hrace.close()
	print("PREDMETY po polozeni: %d, menu staveni otevrene zpet: ok" % predmety.placed.size())
	# louce: vzit z drzaku, zhasnout, vratit; sednout na lavici a vstat
	predmety.spawn_on_wall("drzak_louce", Vector3(-7.5, 1.95, 12.0), Vector3(0, 0, 1))
	predmety.spawn({"id": "lavice_hodovni", "p": Vector3(-2.0, 0.0, 3.0), "yaw": 0.0, "obsah": {}})
	var dz: Dictionary = {}
	for r: Dictionary in predmety.placed:
		if r["id"] == "drzak_louce":
			dz = r
			break
	print("LOUCE drzaku: %d" % predmety.placed.filter(func(r: Dictionary) -> bool: return r["id"] == "drzak_louce").size())
	if not dz.is_empty():
		predmety.use({"rec": dz})
		print("LOUCE v ruce %s hori %s, drzak ma louc %s" % [predmety.held_torch, predmety.held_lit, dz["louc"]])
		predmety.use2({})
		print("LOUCE po X hori %s" % predmety.held_lit)
		predmety.use({"rec": dz})
		print("LOUCE vracena %s, v ruce %s" % [dz["louc"], predmety.held_torch])
	for r: Dictionary in predmety.placed:
		if r["id"] == "lavice_hodovni":
			predmety.use({"rec": r})
			print("SEZENI sedi %s" % player.seated)
			player.move_input = Vector2(0, 1)
			await get_tree().physics_frame
			await get_tree().physics_frame
			player.move_input = Vector2.ZERO
			print("SEZENI po pohybu sedi %s" % player.seated)
			break
	# krb v sini: zhasnout a znovu zapalit, sezeni ve vyklenku okna
	print("KRB hori %s, lze zapalit %s" % [life.fire_on("krb"), life.can_light("krb")])
	life.set_fire("krb", false)
	print("KRB po zhasnuti hori %s, svetlo %s" % [life.fire_on("krb"), (life.fire_spots["krb"]["light"] as OmniLight3D).visible])
	life.stoke("krb")
	print("KRB po zapaleni hori %s" % life.fire_on("krb"))
	var nsed := 0
	for uu: Dictionary in info["use"]:
		if uu.get("kind", "") == "sed":
			nsed += 1
			if nsed == 1:
				_use = uu
				_on_use()
				print("VYKLENEK sedi %s na %s" % [player.seated, player.global_position.snapped(Vector3(0.01, 0.01, 0.01))])
				player.stand_up()
	print("VYKLENEK sedatek %d" % nsed)
	# lucerna z brasny: do ruky, odlozit (A), znovu vzit, schovat (Y v brasne)
	_use = {}
	predmety.add_inv("lucerna")
	menu_hrace.show_page("brasna")
	menu_hrace.close()
	predmety.hold("lucerna", true)
	predmety.inv["lucerna"] = int(predmety.inv["lucerna"]) - 1
	var np0: int = predmety.placed.size()
	_on_use()
	print("LUCERNA odlozena: v ruce '%s', polozenych %d -> %d" % [predmety.held_id, np0, predmety.placed.size()])
	predmety.use({"rec": predmety.placed[-1]})
	menu_hrace.show_page("brasna")
	menu_hrace._stash()
	menu_hrace.close()
	print("LUCERNA schovana: v ruce '%s', v brasne %d" % [predmety.held_id, int(predmety.inv.get("lucerna", 0))])
	# menu staveni, zalozka Polozene: presun z menu a odstraneni
	menu_hrace.show_page("staveni")
	menu_hrace.tab = menu_hrace.KAT_S.size() - 1
	var npl: int = menu_hrace._items(0).size()
	menu_hrace._remove_sel()
	print("POLOZENE v menu %d, po odstraneni %d" % [npl, menu_hrace._items(0).size()])
	menu_hrace._act()
	for i in 3:
		await get_tree().physics_frame
	predmety.confirm_place()
	print("POLOZENE presun z menu: menu zpet otevrene %s, stranka %s, zalozka %s" % [menu_hrace.open, menu_hrace.page, menu_hrace.KAT_S[menu_hrace.tab][0]])
	menu_hrace.close()
	# presun truhly a zruseni: truhla se vrati i s obsahem
	predmety.placed[0]["obsah"] = {"miska": 1}
	predmety.begin_move(predmety.placed[0])
	for i in 3:
		await get_tree().physics_frame
	predmety.cancel_place()
	print("PREDMETY po zruseni presunu: %d, obsah %s" % [predmety.placed.size(), predmety.placed[-1]["obsah"]])
	# pokus postavit skrin do zdi zbrojnice
	player.place(Vector3(-6.0, 0.1, 12.6), Vector3(-6.0, 1.6, 20.0))
	predmety.begin_place("skrin", false)
	for i in 4:
		await get_tree().physics_frame
	print("PREDMETY skrin u zdi platna: %s" % predmety._valid)
	predmety.cancel_place()
	# stavebni rezim: presun a odstraneni truhly (obsah do brasny)
	toggle_build()
	var nb: int = predmety.placed.size()
	predmety.delete(predmety.placed[-1])
	print("PREDMETY stavebni rezim %s, odstraneno %d -> %d, brasna misek %d" % [build_mode, nb, predmety.placed.size(), int(predmety.inv.get("miska", 0))])
	toggle_build()
	# mechanismy: zvednout most a spustit mriz, otevrit prvni dvere
	for id: String in ["most", "mriz", "dvere1", "vrata", "studna"]:
		pohyb.toggle(id)
	# dvere veze: hrac u nich musi dostat nabidku
	player.place(Vector3(-18.0, 0.0, -12.8), Vector3(-30.0, 1.6, -12.8))
	await get_tree().physics_frame
	var u: Dictionary = life.usable(player.cam)
	print("POHYB u dveri veze: ", u.get("id", "nic"))
	player.move_input = Vector2(0, 1)
	for i in 200:
		await get_tree().physics_frame
	player.move_input = Vector2.ZERO
	print("POHYB do veze: x=%.2f" % player.global_position.x)
	for i in 500:
		await get_tree().physics_frame
	for id: String in ["most", "mriz", "dvere1", "vrata", "studna"]:
		var g: Dictionary = pohyb.groups[id]
		print("POHYB %s t=%.2f" % [id, g["t"]])
	# zvednuty most: hrac neprojde
	player.place(_ground(Vector3(0.0, 0.5, 23.0)), Vector3(0.0, 1.6, 0.0))
	player.move_input = Vector2(0, 1)
	for i in 240:
		await get_tree().physics_frame
	player.move_input = Vector2.ZERO
	print("POHYB pres zvednuty most: z=%.2f" % player.global_position.z)
	get_tree().quit()


func _smoke() -> void:
	# kontrola bez obrazu: hrac stoji na zemi, chuze a let, ulozeni a nacteni
	var shot := OS.get_environment("TVRZ_SMOKE")
	if shot.ends_with(".png"):
		var views := [[Vector3(-2.5, 0.0, 7.5), Vector3(6, 3.0, -8)], [Vector3(2.2, -1.0, 34.0), Vector3(0, 4.5, 15)],
				[Vector3(9.0, 3.9, -9.5), Vector3(16, 4.6, -13)]]
		for i in views.size():
			player.place(_ground(views[i][0]) if views[i][0].y < 1.0 and i < 2 else views[i][0], views[i][1])
			for k in 8:
				await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png(shot.replace(".png", "_%d.png" % i))
			print("SMOKE snimek ", i)
		get_tree().quit()
		return
	print("SMOKE spawn ", player.global_position, " na zemi ", player.is_on_floor())
	player.move_input = Vector2(0, 1)
	for i in 90:
		await get_tree().physics_frame
	print("SMOKE po chuzi ", player.global_position)
	player.move_input = Vector2.ZERO
	player.jump()
	await get_tree().create_timer(0.1).timeout
	player.jump()
	player.fly_up = true
	for i in 60:
		await get_tree().physics_frame
	print("SMOKE let ", player.flying, " vyska ", player.global_position.y)
	player.fly_up = false
	_save_game()
	print("SMOKE ulozeni ", _list_saves().size())
	get_tree().quit()


func _ground(p: Vector3) -> Vector3:
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, 60.0, p.z), Vector3(p.x, -30.0, p.z))
	if player:
		q.exclude = [player.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit.is_empty():
		return Vector3(p.x, 1.0, p.z)
	return hit["position"] + Vector3(0, 0.05, 0)


func _apply_mode() -> void:
	player.can_fly = mode == "piskoviste"
	player.buh = mode == "piskoviste"          # Misa 28. 10.: v piskovisti je hrac buh - vse na max
	if mode != "piskoviste":
		build_mode = false
	hud.can_build = mode == "piskoviste"
	if not player.can_fly:
		player.set_flying(false)


## Diag (radce 20:00): cas _process meri obal, poradi behu hry se nemeni (drive diag _process prebiral).
func _process(_delta: float) -> void:
	var t_us := Time.get_ticks_usec()
	_process_vlastni(_delta)
	var dg: Object = Engine.get_meta("diag", null)
	if dg:
		dg.cas("main", Time.get_ticks_usec() - t_us)


func _process_vlastni(_delta: float) -> void:
	_pred_dohrivej()
	if not ready_done:
		return
	if svet and player:
		var tk := Time.get_ticks_usec()
		svet.planovac(player.global_position)        # kolize + rostliny okoli s rozpoctem (radce 16:00 K1)
		var tr := tk
		var tk2 := Time.get_ticks_usec()
		diag.cas("main: planovac", tk2 - tk)          # podrobnost (je uvnitr "main", do souctu se nepocita)
		diag.cas("main: plan kolize", svet.plan_kol_us)   # radce 16:45 bod 4: casti planovace zvlast
		diag.cas("main: plan rostliny", svet.plan_rost_us)
		if tk2 - tk > 8000 and OS.has_environment("TVRZ_TEST"):
			print("OKOLI kolize %.1f ms, rostliny %.1f ms" % [(tr - tk) / 1000.0, (tk2 - tr) / 1000.0])
		# Misa 0.67 (-28,1339), (315,1336): za hranou jemneho terenu (kraj.py ACT) uz jen kulisa - hrac 20 m pred ni
		var gp := player.global_position
		var gx := clampf(gp.x, HRANICE.position.x, HRANICE.end.x)
		var gz := clampf(gp.z, HRANICE.position.y, HRANICE.end.y)
		if gx != gp.x or gz != gp.z:
			player.global_position = Vector3(gx, gp.y, gz)
			player.velocity = Vector3(0.0, player.velocity.y, 0.0)
			if _hranice_t <= 0.0:
				hud.toast("Dál cesta nevede", 2.0)
			_hranice_t = 3.0
		_hranice_t -= _delta
	if _test_auto:
		_test_krok(_delta)
	if not _zas.is_empty():
		_zaseky_krok(_delta)
	_kam_t -= _delta
	if _kam_t <= 0.0 and svet and player:
		_kam_t = 0.5
		svet.kameny_toku_k(Vector2(player.global_position.x, player.global_position.z))
		# mlha v lese: zapoj korun v okoli 12 m (kanaly stanoviste), jen venku
		if day and svet.has_method("_les") and not svet._st_ch.is_empty():
			var pp := player.global_position
			var z := 0.0
			for o: Vector2 in [Vector2.ZERO, Vector2(10, 0), Vector2(-10, 0), Vector2(0, 10), Vector2(0, -10)]:
				z += svet._les(pp.x + o.x, pp.z + o.y)
			day.les_cil = clampf((z / 5.0 - 0.3) / 0.5, 0.0, 1.0) * (0.0 if day.interior > 0.5 else 1.0)
	_music_inside()
	if predmety.placing != "" or player.seated or player.climbing:
		_use = {}
	elif build_mode:
		_use = predmety.nearest(player.cam)
	else:
		_use = life.usable(player.cam)
		if _use.is_empty() and sber != null and predmety.held_id == "":
			_use = sber.usable(player.cam)
	hud.build_mode = build_mode
	_build_acts()


# ------------------------------------------------------------------ nabidka akci (svitek u predmetu)

const NAZVY := {"most": "Padací most", "mriz": "Mříž", "vrata": "Vrata", "studna": "Studna", "bed": "Postel", "fire": "Krb",
		"sed": "Výklenek", "bow": "Luk", "anvil": "Kovadlina"}
var acts: Array = []            # [[text, klic]]
var act_sel := 0
var _acts_key := ""


func _build_acts() -> void:
	# podle predmetu na dosah: nazev a mozne akce; potvrzuje se jen A (dotyk na radek)
	var out: Array = []
	var title := ""
	var anchor = null
	if build_mode:
		if not _use.is_empty() and not bool(_use["rec"].get("pevne", false)):
			title = predmety.name_of(_use["rec"]["id"])
			out = [["Přesunout", "use"], ["Otočit", "rot"]]
			if predmety.can_tilt(String(_use["rec"]["id"])):
				out.append(["Postavení", "tilt"])
			if predmety.kat.get(_use["rec"]["id"], {}).get("kat", null) != null:
				out.append(["Vzít do brašny", "take"])
			out.append(["Odstranit", "use2"])
	elif not _use.is_empty():
		var kind := String(_use["kind"])
		var t1 := ""
		if kind == "pohyb":
			t1 = pohyb.label(String(_use["id"]))
			var gid := String(_use["id"])
			title = NAZVY.get(gid, "Dveře" if gid.begins_with("dvere") else "")
		elif kind == "predmet":
			t1 = predmety.use_label(_use)
			title = predmety.name_of(_use["rec"]["id"])
		elif kind == "sber":
			t1 = sber.label(_use)
			title = sber.nazev(String(_use["id"]))
		elif kind == "zebrik":
			t1 = "Slézt dolů" if bool(_use["nahore"]) else "Lézt nahoru"
			title = "Žebřík"
		else:
			t1 = life.use_label(_use, false)
			title = String(_use.get("nazev", NAZVY.get(kind, "")))
		if t1 != "":
			out.append([t1, "use"])
		var t2: String = predmety.use2_label(_use) if predmety.held_id == "" else ""
		if kind == "fire" and predmety.held_id == "":
			var fn := String(_use.get("name", "krb"))
			t2 = "Zhasnout" if life.can_light(fn) and life.fire_on(fn) else ""
		if t2 != "":
			out.append([t2, "use2"])
		var t3: String = predmety.use3_label(_use) if kind == "predmet" else ""
		if t3 != "":
			out.append([t3, "use3"])
		anchor = _use.get("pos")
	if kun and not build_mode:
		if kun.jezdec != null:
			out = [["Sesednout", "kun_ses"]]
			title = "Kůň"
		elif out.is_empty() and kun.na_dosah(player.global_position):
			out.append(["Nasednout", "kun_nas"])
			title = "Kůň"
			anchor = kun.sedlo_global()
	if predmety.held_id != "" and not build_mode:
		# svetlo v ruce: vzdy jde zapalit/zhasnout, odlozit a schovat
		if out.is_empty():
			title = predmety.name_of(predmety.held_id)
		out.append(["Zhasnout" if predmety.held_lit else "Zapálit", "held"])
		if _use.is_empty():
			out.append(["Odložit", "drop"])
		out.append(["Schovat do brašny", "stash"])
	var key := title + "|" + "|".join(out.map(func(e: Array) -> String: return e[1]))
	if key != _acts_key:
		_acts_key = key
		act_sel = 0
	acts = out
	act_sel = clampi(act_sel, 0, maxi(0, acts.size() - 1))
	hud.acts = acts.map(func(e: Array) -> String: return e[0])
	hud.act_sel = act_sel
	hud.act_title = title
	hud.act_small = not _use.is_empty() and String(_use.get("kind", "")) == "sber"
	hud.use_text = "" if acts.is_empty() else String(acts[0][0])
	hud.use_text2 = ""
	var sp := Vector2(-1, -1)
	if anchor is Vector3 and not player.cam.is_position_behind(anchor):
		sp = player.cam.unproject_position(anchor)
	hud.act_anchor = sp


func act_cycle(d: int) -> bool:
	# D-pad nahoru/dolu: vyber akce, kdyz je jich vic
	if acts.size() < 2:
		return false
	act_sel = wrapi(act_sel + d, 0, acts.size())
	life.sfx("listovat", -14.0, 1.4)
	return true


func do_act(i := -1) -> void:
	if i < 0:
		i = act_sel
	if i >= acts.size():
		return
	if telo:
		telo.akce({"take": "sebrat", "stash": "sebrat", "drop": "sebrat"}.get(String(acts[i][1]), "pouzit"))
		var cp: Variant = _use.get("pos") if not _use.is_empty() else null
		if cp is Vector3:
			# ruka na skutecne misto (klika, predmet, paka) - IK v telo.gd; obema rukama to, co se toci nebo tahne
			# (rumpal studny, vrata, navijak mostu, stavidlo mlyna - jizda.json telo.sahnuti.obe_rukama)
			var obe := false
			for sk: String in Pravidla.cti("jizda", "telo", "sahnuti")["obe_rukama"]:
				obe = obe or String(_use.get("id", _use.get("kind", ""))).begins_with(sk) or String(_use.get("kind", "")) == sk
			telo.sahni(cp, "obe" if obe else "r")
	match String(acts[i][1]):
		"kun_nas":
			kun.nasedni(player)
		"kun_ses":
			kun.sesedni()
		"use":
			_on_use()
		"use2":
			_on_use2()
		"use3":
			predmety.use3(_use)
		"rot":
			predmety.rotate_placed(_use["rec"], PI / 4)
		"tilt":
			predmety.toggle_tilt_placed(_use["rec"])
		"take":
			predmety.take_placed(_use["rec"])
		"held":
			predmety.hold(predmety.held_id, not predmety.held_lit)
			life.sfx("louc_zapalit" if predmety.held_lit else "louc_zhasnout", -8.0)
		"drop":
			predmety.drop_held()
		"stash":
			predmety.add_inv(predmety.held_id)
			predmety.hold("", false)
			life.sfx("presun", -8.0)


# ------------------------------------------------------------------ hudba v tvrzi

## dobova hudba (zvuky/seznam.txt, hudba/LICENCE.txt): v sence ziva hudba, v noci choral
## Misa 0.64: "akcnejsi a emotivnejsi hudbu" - Kevin MacLeod (incompetech, CC BY 4.0, hudba/k_*): epicke
## stredoveke (Crusade, Lord of the Land, Heroic Age, Five Armies, Achilles), emotivni (Teller of the Tales),
## zivejsi kelticka (Celtic Impulse), noc kmenova (Ancient Rite); starsi klidne skladby jen mezi nimi
const HUDBA := {
	"tvrz": ["k_crusade", "tvrz_1", "k_lord_of_the_land", "k_heroic_age", "tvrz_2"],
	"ves": ["k_celtic_impulse", "ves_1", "k_lord_of_the_land", "ves_3"],
	"priroda": ["k_five_armies", "k_teller_of_the_tales", "k_achilles", "krajina_3", "k_prelude_and_action", "k_heroic_age"],
	"senk": ["senk_1", "k_celtic_impulse", "senk_2"],
	"noc": ["k_teller_of_the_tales", "noc_1", "k_ancient_rite"],
}
var _zona := ""
var _ticho := 0.0              # v prirode mezi skladbami chvili jen zvuky prirody


func _music_zone() -> String:
	var p := player.global_position
	if life and String(life.room_name).begins_with("hostinec_") and (life.room_name.ends_with("senk") or life.room_name.ends_with("sin")):
		return "senk"
	var m := 1.5 if _zona == "tvrz" else -0.5            # hystereze u brany
	if p.x > -25.0 - m and p.x < 17.0 + m and p.z > -14.0 - m and p.z < 14.0 + m and p.y < 14.0:
		return "tvrz"
	if day and day.is_night():
		return "noc"
	var dv := Vector2(p.x - 470.0, p.z - 830.0).length()
	if dv < (150.0 if _zona == "ves" else 135.0):
		return "ves"
	return "priroda"


func _music_inside() -> void:
	# hudba podle mista: v tvrzi dobova hudba, ve vsi vesnicka, v prirode dobrodruzna (s pauzami)
	if not hudba_on:
		if _hudba and _hudba.playing:
			_hudba.stop()
		return
	var z := _music_zone()
	_uvnitr = z == "tvrz"
	if _hudba == null:
		_hudba = AudioStreamPlayer.new()
		_hudba.bus = "Hudba"
		_hudba.process_mode = Node.PROCESS_MODE_ALWAYS
		_hudba.finished.connect(func() -> void: _ticho = randf_range(25.0, 70.0) if _zona in ["priroda", "noc"] else 2.0)
		add_child(_hudba)
	# skladba (3-6 MB ogg) se nacita ve vlakne (0.62 bod 8: load v hlavnim vlakne = zasek 20 ms PC / ~100 ms tablet)
	if _hudba_ceka != "":
		var stav := ResourceLoader.load_threaded_get_status(_hudba_ceka)
		if stav == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
			return
		var st: AudioStream = ResourceLoader.load_threaded_get(_hudba_ceka) if stav == ResourceLoader.THREAD_LOAD_LOADED else null
		_hudba_ceka = ""
		if st and _hudba_ceka_zona == _zona:
			_hraj_skladbu(st)
		elif st:
			_next_track()
			return
	if z != _zona:
		_zona = z
		_ticho = 0.0
		if _hudba_tw:
			_hudba_tw.kill()
		_hudba_tw = create_tween()
		if _hudba.playing:
			_hudba_tw.tween_property(_hudba, "volume_db", -50.0, 3.0)
			_hudba_tw.tween_callback(_hudba.stop)
			_hudba_tw.tween_callback(_next_track)
		else:
			_next_track()
		return
	if not _hudba.playing and (_hudba_tw == null or not _hudba_tw.is_running()):
		_ticho -= get_process_delta_time()
		if _ticho <= 0.0:
			_next_track()


func _next_track() -> void:
	var seznam: Array = HUDBA.get(_zona, HUDBA["tvrz"])
	var n := seznam.size()
	_hudba_i = (_hudba_i + 1 + randi() % maxi(1, n - 1)) % n if _hudba_i >= 0 else randi() % n
	if _hudba_ceka != "":
		return                         # nacita se jina skladba: po nacteni se zkontroluje zona
	_hudba_ceka = "res://hudba/%s.ogg" % seznam[_hudba_i % n]
	_hudba_ceka_zona = _zona
	if ResourceLoader.load_threaded_request(_hudba_ceka) != OK:
		_hudba_ceka = ""


var _hudba_ceka := ""                  # skladba nacitana vlaknem
var _hudba_ceka_zona := ""


func _hraj_skladbu(st: AudioStream) -> void:
	_hudba.stream = st
	_hudba.volume_db = -40.0
	_hudba.play()
	if _hudba_tw:
		_hudba_tw.kill()
	_hudba_tw = create_tween()
	var cil: float = HUDBA_DB - (3.0 if _zona in ["priroda", "noc"] else 0.0)
	_hudba_tw.tween_property(_hudba, "volume_db", cil, 5.0)


# ------------------------------------------------------------------ akce

func _on_use2() -> void:
	# stavebni rezim, X: odstranit predmet; jinak zapalit/zhasnout louc
	if build_mode:
		if not _use.is_empty():
			predmety.delete(_use["rec"])
		return
	if predmety.held_id == "" and not _use.is_empty() and String(_use["kind"]) == "fire":
		var fn := String(_use.get("name", "krb"))
		if life.can_light(fn) and life.fire_on(fn):
			life.set_fire(fn, false)
		return
	predmety.use2(_use)


func toggle_build() -> void:
	if mode != "piskoviste" or not ready_done or get_tree().paused:
		return
	build_mode = not build_mode
	predmety.cancel_place()
	life.sfx("listovat", -6.0)
	hud.toast("Stavební režim: přesouvání, otáčení a odstraňování" if build_mode else "Stavební režim ukončen", 1.8)


func _on_use() -> void:
	if _use.is_empty():
		if not build_mode and predmety.held_id != "":
			predmety.drop_held()
		return
	if build_mode:
		predmety.begin_move(_use["rec"])
		return
	if String(_use["kind"]) == "pohyb":
		pohyb.toggle(String(_use["id"]))
		return
	if String(_use["kind"]) == "predmet":
		predmety.use(_use)
		return
	if String(_use["kind"]) == "sber":
		sber.pick(_use)
		return
	if String(_use["kind"]) == "zebrik":
		player.climb(_use["zb"], bool(_use["nahore"]))
		return
	life.sfx("click", -8.0)
	match _use["kind"]:
		"mlyn_stavidlo":
			var kola := get_tree().get_nodes_in_group("mlyn_kolo")
			var pustit := not kola.is_empty() and not bool(kola[0].get("bezi"))
			for k in kola:
				k.set("bezi", pustit)
			hud.toast("Pustil jsi vodu na kolo" if pustit else "Zavřel jsi stavidlo – kolo se zastaví", 2.0)
		"mlyn_mleti":
			_mlyn_mlit()
		"sed":
			var sp: Array = _use["sit"]
			player.sit(Vector3(sp[0], sp[1], sp[2]), float(_use.get("h", 0.46)) + 0.78, player.global_position, float(_use.get("yaw", 0.0)))
		"bed":
			player.sit(Vector3(_use["pos"]) - Vector3(0, 0.5, 0), 0.62, player.global_position, player.yaw, deg_to_rad(55))
			offer_sleep()
		"svetlo":
			var sn := String(_use.get("name", ""))
			life.fire_spots[sn]["auto"] = false            # hrac ho ovlada rucne (jako predmety)
			life.set_fire(sn, not life.fire_on(sn))
		"fire":
			var fn := String(_use.get("name", "krb"))
			var was: bool = life.fire_on(fn)
			life.stoke(fn)
			if was:
				hud.toast("Přiložil jsi polínko", 1.4)


## Mleti (voda.json mlyn.dil.ovladani): jen s kolem v chodu a pytlem obili v brasne; po mleti_s pytel mouky.
var _mele := false


func _mlyn_mlit() -> void:
	var kola := get_tree().get_nodes_in_group("mlyn_kolo")
	if kola.is_empty() or not kola[0].call("v_chodu"):
		hud.toast("Kámen stojí – nejdřív pusť vodu na kolo (stavidlo)", 2.5)
		return
	if _mele:
		return
	if int(predmety.inv.get("pytel_obili", 0)) < 1:
		hud.toast("Nemáš u sebe pytel obilí", 2.0)
		return
	predmety.inv["pytel_obili"] = int(predmety.inv["pytel_obili"]) - 1
	if int(predmety.inv["pytel_obili"]) <= 0:
		predmety.inv.erase("pytel_obili")
	_mele = true
	var cas := float(Pravidla.cti("voda", "mlyn", "dil")["ovladani"]["mleti_s"])
	hud.toast("Sypeš obilí do násypky…", cas)
	await get_tree().create_timer(cas).timeout
	_mele = false
	predmety.add_inv("pytel_mouky", 1)
	hud.toast("Semleto – pytel mouky v brašně", 2.5)


# ------------------------------------------------------------------ ukladani

func _list_saves() -> Array:
	var out: Array = []
	var d := DirAccess.open(SAVE_DIR)
	if d == null:
		return out
	for f in d.get_files():
		if not f.ends_with(".json"):
			continue
		var fa := FileAccess.open(SAVE_DIR + "/" + f, FileAccess.READ)
		if fa == null:
			continue
		var j: Variant = JSON.parse_string(fa.get_as_text())
		if typeof(j) != TYPE_DICTIONARY:
			continue
		out.append({"file": SAVE_DIR + "/" + f, "t": int(j.get("unix", 0)),
				"label": "%s – %s" % [MODE_NAMES.get(j.get("mode", ""), "Hra"), String(j.get("kdy", f))]})
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["t"] > b["t"])
	return out


func _save_game() -> void:
	DirAccess.make_dir_recursive_absolute(SAVE_DIR)
	var now := Time.get_unix_time_from_system()
	var dt := Time.get_datetime_dict_from_system()
	# vsede ulozit misto, kde se vstava (poloha na sedatku je uvnitr jeho kolize)
	var p: Vector3 = player._stand_p if player.seated else player.global_position
	var j := {
		"mode": mode, "unix": int(now),
		"kdy": "%d. %d. %d  %02d:%02d:%02d" % [dt["day"], dt["month"], dt["year"], dt["hour"], dt["minute"], dt["second"]],
		"pos": [p.x, p.y, p.z], "yaw": player.yaw, "pitch": player.pitch,
		"cas": day.current, "hodina": day.hour, "den": day.day_n, "let": player.flying,
		"predmety": predmety.to_save(),
		"pohyb": pohyb.to_save(), "ohne": life.fires_save(), "objevena": objevena, "sber": sber.to_save(),
	}
	var fa := FileAccess.open(SAVE_DIR + "/hra_%d.json" % int(now), FileAccess.WRITE)
	fa.store_string(JSON.stringify(j))
	fa.close()
	# drzet jen poslednich 20 ulozeni
	var old := _list_saves()
	for k in range(20, old.size()):
		DirAccess.remove_absolute(String(old[k]["file"]))
	_save_cfg()


func _load_file(path: String) -> void:
	var fa := FileAccess.open(path, FileAccess.READ)
	if fa == null:
		return
	var j: Variant = JSON.parse_string(fa.get_as_text())
	if typeof(j) != TYPE_DICTIONARY:
		return
	_start(String(j.get("mode", "piskoviste")), j)


func _apply_save(j: Dictionary) -> void:
	objevena = Array(j.get("objevena", []))
	if sber != null:
		sber.from_save(j.get("sber", {}))
	if j.has("predmety"):
		predmety.from_save(j["predmety"])
	else:
		_default_items()
	if j.is_empty():
		return
	var a: Array = j["pos"]
	player.global_position = Vector3(a[0], a[1], a[2])
	player.yaw = float(j.get("yaw", 0.0))
	player.pitch = float(j.get("pitch", 0.0))
	player.velocity = Vector3.ZERO
	_volne_misto()
	player.reset_physics_interpolation()
	if player.can_fly and bool(j.get("let", false)):
		player.set_flying(true)
	if j.has("hodina"):
		day.day_n = int(j.get("den", 1))
		day.hour = float(j["hodina"])
		day.set_hour(float(j["hodina"]), 0.01)
	elif j.has("cas"):
		day.set_time(String(j["cas"]), 0.01)
	pohyb.from_save(j.get("pohyb", {}))
	life.fires_load(j.get("ohne", {}))


## Starsi ulozeni (vsede, v predmetu): je-li hrac v kolizi, posunout na nejblizsi volne misto s podlahou.
func _volne_misto() -> void:
	player.postav_na_volne(player.global_position)


func _default_items() -> void:
	# vychozi vybaveni sveta: truhla ve zbrojnici se zbranemi, sud a vedro v kovarne
	predmety.from_save({})
	if mode == "piskoviste":
		predmety.start_kit()
	predmety.spawn({"id": "truhla", "p": Vector3(-6.6, 0.04, 13.35), "yaw": PI, "obsah": {"sekera_valecna": 1, "kladivo_valecne": 1, "stit": 1}})
	predmety.spawn({"id": "sud", "p": Vector3(-15.4, 0.02, 13.2), "yaw": 0.0, "obsah": {}})
	predmety.spawn({"id": "vedro", "p": Vector3(-16.2, 0.02, 12.9), "yaw": 0.6, "obsah": {}})
	# _hostinec_svetla()      # Misa 0.70: zbytecne, hostinec ma dva zavesne lustry


## Misa 0.69: "v hostinci stejna logika svetel jako na tvrzi" - louce v drzacich na stenach kazde mistnosti hostince
## (predmety s "auto": vecer a v noci se rozsviti samy, hrac je muze zapalit, zhasnout, vzit do ruky).
func _hostinec_svetla() -> void:
	for r: Dictionary in info["rooms"]:
		if not String(r["name"]).begins_with("hostinec_") or not r.has("inv"):
			continue
		var xf: Transform3D = (r["inv"] as Transform3D).affine_inverse()
		var sz: Vector3 = (r["aabb"] as AABB).size
		var y := minf(1.9, sz.y - 0.4)
		var smery: Array = [Vector3.RIGHT, Vector3.LEFT]
		if sz.z > 6.0 or sz.x > 6.0:
			smery += [Vector3.FORWARD, Vector3.BACK]
		if String(r["name"]) == "hostinec_sklad" or String(r["name"]) == "hostinec_schody":
			smery = [Vector3.RIGHT]
		# jen mistnosti bez vlastniho svetla (sin a senk maji stojany a svicny z vybaveni)
		var ma := false
		for it: Dictionary in svet.data.get("vybaveni", []):
			var pp: Array = it["p"]
			if (r["aabb"] as AABB).grow(0.3).has_point((r["inv"] as Transform3D) * Vector3(pp[0], pp[1] + 0.2, pp[2])) \
					and predmety.SVETLA.has(String(it["id"])) or (String(it["id"]) == "stojan_louce" and (r["aabb"] as AABB).grow(0.3).has_point((r["inv"] as Transform3D) * Vector3(pp[0], pp[1] + 0.2, pp[2]))):
				ma = true
		if ma:
			continue
		for d: Vector3 in smery:
			# ze stredu mistnosti, kus stranou (ne do dveri uprostred steny)
			var od := xf * Vector3(sz.x * 0.2 * absf(d.z), y, sz.z * 0.2 * absf(d.x))
			predmety.spawn_on_wall("drzak_louce", od, xf.basis * d)



func offer_sleep() -> void:
	menu_hrace.show_page("spanek")


func sleep_until(key: String) -> void:
	# prespani: zatmeni, posun denni doby, vstat z postele a ulozit hru
	hud.fade_through(func() -> void:
		day.set_time(key, 0.01)
		player.stand_up()
		life.sfx("spanek", -6.0)
		_save_game()
		menu.saves = _list_saves())
	await get_tree().create_timer(1.6).timeout
	hud.toast("Hra uložena", 2.5)


func open_container(rec: Dictionary) -> void:
	menu_hrace.show_page("vymena", rec)


func open_map() -> void:
	if ready_done and not get_tree().paused and predmety.placing == "" and not player.seated:
		mapa.show_map()


## Rychle cestovani z mapy: zatmit, presunout hrace, posunout herni cas o dobu chuze, rozednit.
func fast_travel(cil: Vector3, pohled: Vector3, hours: float, nazev: String) -> void:
	var cl := CanvasLayer.new()
	cl.layer = 30
	cl.process_mode = Node.PROCESS_MODE_ALWAYS
	var fade := ColorRect.new()
	fade.color = Color(0, 0, 0, 0)
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade.mouse_filter = Control.MOUSE_FILTER_STOP
	cl.add_child(fade)
	add_child(cl)
	get_tree().paused = true
	var tw := create_tween().set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tw.tween_property(fade, "color:a", 1.0, 0.7)
	await tw.finished
	if player.seated:
		player.stand_up()
	if player.flying:
		player.set_flying(false)
	day.set_hour(fmod(day.hour + hours, 24.0), 0.01)
	var louka := get_node_or_null("Louka")
	if louka:
		# Misa 0.65: pad pri rychlem cestovani s RAM 1493 MB (volna 0) - stara louka a nova v cili soucasne. Pod
		# zatmenim starou uvolnit cele (bunky i kupy), v cili se stavi od nuly tak jako tak
		louka.vypni()
	svet.kolize_okoli(cil, true)              # kolize skal a kmenu v cili (paprsky nize je vidi po kroku fyziky)
	svet.rostliny_okoli(cil, true)
	get_tree().paused = false
	await get_tree().process_frame             # queue_free starych bunek probehne pred stavbou novych
	await get_tree().physics_frame
	# volne misto (0.57c: na Pustou skalu hrac uvizl ve zdi zriceniny): kapsle hrace bez kolize, spirala do 6 m
	var cq := PhysicsShapeQueryParameters3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.4
	cap.height = 1.8
	cq.shape = cap
	cq.exclude = [player.get_rid()]
	var space := player.get_world_3d().direct_space_state
	var cil2 := cil
	for k in 40:
		var q := Vector2(cil.x, cil.z) + Vector2.from_angle(k * 2.4) * (k * 0.15)
		cq.transform = Transform3D(Basis(), Vector3(q.x, _ground_hi(q.x, q.y) + 1.05, q.y))
		if space.intersect_shape(cq, 1).is_empty():
			cil2 = Vector3(q.x, 0.0, q.y)
			break
	player.place(Vector3(cil2.x, _ground_hi(cil2.x, cil2.z) + 0.1, cil2.z), Vector3(pohled.x, _ground_hi(pohled.x, pohled.z) + 1.6, pohled.z))
	for i in 8:
		await get_tree().physics_frame
	var tw2 := create_tween()
	tw2.tween_property(fade, "color:a", 0.0, 0.9)
	await tw2.finished
	cl.queue_free()
	hud.toast("%s (%s)" % [nazev, day.clock_text()], 2.5)


func open_player_menu() -> void:
	if ready_done and not get_tree().paused and predmety.placing == "":
		menu_hrace.show_page("staveni" if build_mode else "brasna")


## Zvukove kanaly: Hudba a Zvuky (vse ostatni). Kazdy prehravac pridany do sceny s kanalem Master jde do Zvuky.
func _audio_buses() -> void:
	for n: String in ["Hudba", "Zvuky"]:
		if AudioServer.get_bus_index(n) < 0:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, n)
			AudioServer.set_bus_send(i, "Master")
	get_tree().node_added.connect(func(n: Node) -> void:
		if (n is AudioStreamPlayer or n is AudioStreamPlayer3D or n is AudioStreamPlayer2D) and n.get("bus") == &"Master":
			n.set("bus", &"Zvuky"))
	apply_audio()


func apply_audio() -> void:
	var h := AudioServer.get_bus_index("Hudba")
	var z := AudioServer.get_bus_index("Zvuky")
	AudioServer.set_bus_volume_db(h, linear_to_db(maxf(hudba_vol, 0.001)))
	AudioServer.set_bus_mute(h, not hudba_on or hudba_vol <= 0.01)
	AudioServer.set_bus_volume_db(z, linear_to_db(maxf(zvuky_vol, 0.001)))
	AudioServer.set_bus_mute(z, not zvuky_on or zvuky_vol <= 0.01)


func _save_cfg() -> void:
	_cfg.set_value("hra", "kvalita", quality)
	_cfg.set_value("hra", "citlivost2", sens_i)
	_cfg.set_value("hra", "pohyb", pohyb_i)
	_cfg.set_value("hra", "kun_cesta", kun_drzet_cestu)
	_cfg.set_value("zvuk", "hudba_on", hudba_on)
	_cfg.set_value("zvuk", "hudba_vol", hudba_vol)
	_cfg.set_value("zvuk", "zvuky_on", zvuky_on)
	_cfg.set_value("zvuk", "zvuky_vol", zvuky_vol)
	_cfg.set_value("hra", "mereni", mereni_on)
	_cfg.set_value("hra", "mereni_fps", mereni_fps)
	_cfg.set_value("hra", "msaa", msaa_on)
	_cfg.set_value("hra", "fyzika", fyzika_i)
	_cfg.set_value("hra", "snimky", snimky_i)
	_cfg.set_value("hra", "plne_3d", plne_3d)
	_cfg.set_value("hra", "rozliseni", rozliseni_i)
	if day:
		_cfg.set_value("hra", "cas", day.current)
	_cfg.save("user://nastaveni.cfg")


func _notification(what: int) -> void:
	if not ready_done:
		return
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		_pause(not get_tree().paused)
	elif what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		if not get_tree().paused:
			_pause(true)


# ------------------------------------------------------------------ kvalita obrazu

## Krok fyziky (radce 16:30): pri nizkem FPS bezi az N kroku za snimek - spirala (fyzika 25-34 ms u hostince).
func apply_fyzika() -> void:
	Engine.physics_ticks_per_second = 30 if fyzika_i == 2 else 60
	Engine.max_physics_steps_per_frame = 3 if fyzika_i == 0 else 2
	Engine.max_fps = 30 if snimky_i == 1 else 0


func apply_quality() -> void:
	var vp := get_viewport()
	var mobile := OS.has_feature("mobile")
	var scales := [0.45, 0.55, 0.7] if mobile else [0.7, 0.85, 1.0]     # tablet: fill rate (radce 20:45: KCD Switch 540-720p)
	var sc: float = scales[quality]
	# bilinearni skalovani: FSR na Adrenu delal vodorovne pruhy
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = [sc, maxf(sc, 0.8), 1.0][rozliseni_i]
	# 0.65 zpet na 60 Hz (Misa 0.64: 3x propadl ze schodu na ochoz - pri 30 Hz se kapsle pohne o 2x vic za krok a
	# na hrane podesty/rampy proklouzla; sekani resilo plneni louky po castech, ne fyzika)
	apply_fyzika()
	# tablet (radce 20:45 krok 3): LOD siti driv - prah 4 px -> 10 px (skaly, stavby, stromy s LOD)
	vp.use_occlusion_culling = true          # okluzory teren + domy (svet._okluzory)
	vp.mesh_lod_threshold = 10.0 if mobile or OS.has_environment("TVRZ_MOBIL") else 4.0
	# Vulkan (renderer Mobile) na Adreno 8xx: bez MSAA vodorovne pruhy pres obraz (diagnostika 16. 10.);
	# MSAA 2x je na dlazdicovych GPU skoro zadarmo. Compatibility (OpenGL) beze zmeny.
	# MSAA 4x i na Compatibility: alfa travy jako pokryti (alpha_to_coverage) misto discard (radce 20:30)
	vp.msaa_3d = Viewport.MSAA_4X if msaa_on and not OS.has_feature("mobile") else Viewport.MSAA_DISABLED     # tablet nikdy MSAA (CLAUDE.md)
	var env: Environment = day.env
	env.ssao_enabled = quality >= 2 and not mobile
	env.glow_enabled = quality >= 1
	var sun: DirectionalLight3D = day.sun
	# rozpocet (zadani faze 1): 2 kaskady, stiny do 80 m
	sun.directional_shadow_max_distance = [40.0, 60.0, 80.0][quality]
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	if mobile:
		# tablet (radce 20:45 krok 5): jedna kaskada do 40 m
		# radce 20:00: dosah stinu = plosne omezeni vzhledu -> jen se schvalenim Misy (zkusebne 30 m usetri cast z 335-470)
		sun.directional_shadow_max_distance = 40.0
		sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	RenderingServer.directional_shadow_atlas_set_size(2048, true)        # rozpocet GPU pameti (4096 = 64 MB)
	life.set_quality(quality)
	_test_pameti()


## Automaticky test pameti: krok po 40 s, rust RAM za posledni 30 s kroku do diag logu (preziji pad).
func _test_krok(dt: float) -> void:
	_test_t += dt
	if not _test_chuze.is_empty():
		_test_chuze[2] = float(_test_chuze[2]) + dt * 5.0
		var u := fposmod(float(_test_chuze[2]), 120.0)
		var dp := u if u < 60.0 else 120.0 - u
		var q: Vector2 = (_test_chuze[0] as Vector2) + (_test_chuze[1] as Vector2) * dp
		# vyska terenu, ne nejvyssi kolize (_ground_hi = strechy a koruny stromu -> hrac nad strechou)
		player.global_position = Vector3(q.x, svet._vyska(q.x, q.y) + 0.05, q.y)
		player.velocity = Vector3.ZERO
	if _test_ram0 < 0 and _test_t > TEST_KROK_S - 10.0:
		_test_ram0 = diag.ram_mb()
		_test_fps = Vector3.ZERO
	if _test_ram0 >= 0:
		# 0.64 (radce 18:00): i vykon kroku - prumerne FPS a nejdelsi snimek za poslednich 10 s (ktera vec seka)
		_test_fps += Vector3(1.0, dt, 0.0)
		_test_fps.z = maxf(_test_fps.z, dt)
	if _test_t < TEST_KROK_S:
		return
	var rust: float = (diag.ram_mb() - _test_ram0) * 6.0          # MB za 10 s -> MB/min
	diag.faze("TEST PAMETI krok %d (%s): RAM %+d MB/min" % [test_pameti, TEST_PAMETI[test_pameti], int(rust)])
	var fps := _test_fps.x / maxf(_test_fps.y, 0.001)
	test_vysledky.append("%d: %+d MB, %d fps, max %d ms" % [test_pameti, int(rust), roundi(fps), roundi(_test_fps.z * 1000.0)])
	diag.faze("TEST VYKON krok %d (%s): %.1f fps, nejdelsi %.0f ms" % [test_pameti, TEST_PAMETI[test_pameti], fps, _test_fps.z * 1000.0])
	_test_t = 0.0
	_test_ram0 = -1
	test_pameti += 1
	if test_pameti >= TEST_PAMETI.size():
		test_pameti = 0
		_test_auto = false
		if not _test_chuze.is_empty():
			_test_chuze = []
			player.set_flying(false)
		diag.faze("TEST PAMETI konec")
	apply_quality()


## Test zaseku: varianty z hrac.json test_zaseku.varianty [{nazev, fyzika_i, snimky_i}], kazda varianta_s sekund chuze
## tam a zpet trasa_m ve smeru pohledu (rychlost_m_s); snimky v kazde variante: p50/p95/p99, pocet nad spicka_ms, mista
## spicek. Na konci puvodni nastaveni zpet a zprava do schranky.
func _zaseky_start() -> void:
	var c: Dictionary = Pravidla.cti("hrac", "test_zaseku")
	_zas = {"c": c, "i": 0, "t": 0.0, "dt": [], "spicky": [], "vysl": [], "puvodni": [fyzika_i, snimky_i],
			"a": Vector2(player.global_position.x, player.global_position.z), "smer": Vector2(-sin(player.yaw), -cos(player.yaw)), "s": 0.0}
	player.set_flying(true)
	_zaseky_varianta()
	hud.toast("Test záseků běží – nech tablet být (%d × %d s)" % [(c["varianty"] as Array).size(), int(c["varianta_s"])], 3.0)


func _zaseky_varianta() -> void:
	var v: Dictionary = (_zas["c"]["varianty"] as Array)[int(_zas["i"])]
	fyzika_i = int(v["fyzika_i"])
	snimky_i = int(v["snimky_i"])
	apply_fyzika()
	_zas["t"] = 0.0
	_zas["dt"] = []
	_zas["spicky"] = []
	diag.faze("TEST ZASEKU varianta %s" % v["nazev"])


func _zaseky_krok(dt: float) -> void:
	var c: Dictionary = _zas["c"]
	_zas["t"] = float(_zas["t"]) + dt
	_zas["s"] = float(_zas["s"]) + dt * float(c["rychlost_m_s"])
	var L := float(c["trasa_m"])
	var u := fposmod(float(_zas["s"]), 2.0 * L)
	var q: Vector2 = (_zas["a"] as Vector2) + (_zas["smer"] as Vector2) * (u if u < L else 2.0 * L - u)
	player.global_position = Vector3(q.x, svet._vyska(q.x, q.y) + 0.05, q.y)
	player.velocity = Vector3.ZERO
	if float(_zas["t"]) < float(c["rozjezd_s"]):
		return                                     # po prepnuti varianty chvili nemerit (nacitani bunek)
	(_zas["dt"] as Array).append(dt * 1000.0)
	if dt * 1000.0 > float(c["spicka_ms"]):
		(_zas["spicky"] as Array).append([dt * 1000.0, q])
	if float(_zas["t"]) < float(c["varianta_s"]):
		return
	var a: Array = (_zas["dt"] as Array).duplicate()
	a.sort()
	var pc := func(p: float) -> float: return float(a[clampi(int(p * a.size()), 0, a.size() - 1)]) if not a.is_empty() else 0.0
	var sp: Array = (_zas["spicky"] as Array).duplicate()
	sp.sort_custom(func(x: Array, y: Array) -> bool: return x[0] > y[0])
	var mista := ""
	for e: Array in sp.slice(0, 3):
		mista += " %.0f ms u (%.0f, %.0f)" % [e[0], (e[1] as Vector2).x, (e[1] as Vector2).y]
	var v: Dictionary = (c["varianty"] as Array)[int(_zas["i"])]
	(_zas["vysl"] as Array).append("%s: p50 %.0f ms, p95 %.0f, p99 %.0f, max %.0f, nad %d ms %d×;%s" % [v["nazev"], pc.call(0.5), pc.call(0.95), pc.call(0.99),
			float(a[-1]) if not a.is_empty() else 0.0, int(c["spicka_ms"]), sp.size(), mista])
	diag.faze("TEST ZASEKU " + String((_zas["vysl"] as Array)[-1]))
	_zas["i"] = int(_zas["i"]) + 1
	if int(_zas["i"]) >= (c["varianty"] as Array).size():
		_zaseky_konec(false)
	else:
		_zaseky_varianta()


func _zaseky_konec(zruseno: bool) -> void:
	fyzika_i = int(_zas["puvodni"][0])
	snimky_i = int(_zas["puvodni"][1])
	apply_fyzika()
	player.set_flying(false)
	var g := player.global_position
	var zprava := "Odkaz Havrana %s – test záseků u (%.0f, %.0f)%s\n%s" % [ProjectSettings.get_setting("application/config/version"), g.x, g.z,
			" (zrušen)" if zruseno else "", "\n".join(_zas["vysl"] as Array)]
	_zas = {}
	DisplayServer.clipboard_set(zprava)
	diag.faze("TEST ZASEKU konec")
	OS.alert(zprava + "\n\nZpráva je ve schránce – vlož ji do chatu.", "Test záseků")


## Test pameti: krok k vypne jen svou vec, ostatni vrati.
func _test_pameti() -> void:
	var k := test_pameti
	var vp := get_viewport()
	vp.disable_3d = k == 1
	var lk: Node3D = get_node_or_null("Louka")
	if lk:
		var bez := k == 2
		# radce 20:30: vypni() uvolnilo vsechny bunky najednou a po zapnuti se stavely znovu (295 ms, pak pad) -
		# louka se jen skryje a zastavi, bunky zustanou
		lk.visible = not bez
		lk.set_process(not bez)
	for nm: String in ["Rostliny", "Tvrz", "Predmety"]:
		var n3: Node3D = world.find_child(nm, true, false) if world else null
		if n3:
			n3.visible = k != 3
	if life:
		if k == 4:
			if not _test_stav.has(life):
				_test_stav[life] = life.process_mode
			life.process_mode = Node.PROCESS_MODE_DISABLED
		elif _test_stav.has(life):
			life.process_mode = _test_stav[life]
			_test_stav.erase(life)
		life.visible = k != 4
	AudioServer.set_bus_mute(0, k == 4)
	if day:
		day.sun.shadow_enabled = k != 5
	if k == 6:
		vp.msaa_3d = Viewport.MSAA_DISABLED


func _je_voda(gi: GeometryInstance3D) -> bool:
	var mats: Array = [gi.material_override]
	if gi is MeshInstance3D and (gi as MeshInstance3D).mesh:
		var mi := gi as MeshInstance3D
		for i in mi.mesh.get_surface_count():
			mats.append(mi.get_active_material(i))
	for m: Variant in mats:
		if m is ShaderMaterial and (m as ShaderMaterial).shader and ((m as ShaderMaterial).shader.resource_path.ends_with("voda.gdshader") \
				or (m as ShaderMaterial).shader.resource_path.ends_with("reka.gdshader")):
			return true
	return false


func _talir_test() -> void:
	# jablko na talir: duch se musi zvednout na horni plochu talire
	predmety.spawn({"id": "talir", "p": Vector3(-4.0, predmety.ground_y(-4.0, 3.0), 3.0), "yaw": 0.0, "obsah": {}})
	player.place(Vector3(-4.0, 0.1, 4.2), Vector3(-4.0, 0.0, 3.0))
	predmety.begin_place("jablko", false)
	predmety._gdist = 1.2
	for i in 6:
		await get_tree().physics_frame
		await get_tree().process_frame
	var tn: Node3D = predmety.placed[-1]["node"]
	print("TALIR jablko y %.3f, dno talire %.3f, vyska talire %.3f" % [predmety._ghost.global_position.y, tn.global_position.y, float(predmety.kat["talir"]["rozmer"][1])])


func _louc_shot(path: String) -> void:
	# noc, louc v ruce: okoli musi byt osvetlene (nadvori plne loucí na stojanech)
	day.set_time("noc", 0.01)
	for i in 10:
		predmety.spawn({"id": "stojan_louce", "p": Vector3(-14.0 + i * 3.0, predmety.ground_y(-14.0 + i * 3.0, 14.0), 14.0), "yaw": 0.0, "obsah": {}})
	predmety.on_time("noc", true)
	player.place(Vector3(-6.4, 0.1, 10.7), Vector3(-6.4, -0.6, 7.0))
	predmety.hold("louc", true)
	for i in 40:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path)
	predmety.hold("", false)
	player.place(Vector3(-6.4, 0.1, 10.7), Vector3(-6.4, 1.2, 14.0))
	for i in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_stojany.png"))


func _pohled_shot(spec: String) -> void:
	# snimky z danych mist: "soubor.png;x,y,z,tx,ty,tz;cas|soubor2.png;..." (y oka nad zemi se dopocita fyzikou)
	player.set_flying(true)
	if OS.has_environment("TVRZ_BEZ_HUD"):
		hud.visible = false
	for one: String in spec.split("|"):
		if one.count(";") < 1:
			continue                                # prazdne zadani (napr. TVRZ_JIZDA bez mereni)
		var parts := one.split(";")
		var absolute := parts[1].begins_with("a")
		var v := parts[1].trim_prefix("a").split_floats(",")
		day.set_hour(float(parts[2]) if parts.size() > 2 else 12.0, 0.01)
		# TVRZ_POHLED_PREDMETY='[{"id":"stojan_louce","p":[x,y,z],"yaw":0}]' - predmety jen pro snimek (y nad zemi)
		if OS.has_environment("TVRZ_POHLED_PREDMETY") and one == spec.split("|")[0]:
			for r: Dictionary in JSON.parse_string(OS.get_environment("TVRZ_POHLED_PREDMETY")):
				var pp: Array = r["p"]
				var yy: float = float(pp[1]) if bool(r.get("abs", false)) else _ground_hi(pp[0], pp[2]) + float(pp[1])
				predmety.spawn({"id": r["id"], "p": Vector3(pp[0], yy, pp[2]), "yaw": float(r.get("yaw", 0.0))})
		# vysky jsou nad zemi (oko i cil)
		var gy: float = 0.0 if absolute else _ground_hi(v[0], v[2])
		var ty: float = 0.0 if absolute else _ground_hi(v[3], v[5])
		player.place(Vector3(v[0], gy + v[1], v[2]), Vector3(v[3], ty + v[4], v[5]))
		for i in 40:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(parts[0])


## Mereni rozpoctu: "nazev;x,z,tx,tz|..." - hrac na zemi, louka dostavena naplno, prumer pres 30 snimku.
## Zkouska tela a jizdy (TVRZ_JIZDA=<slozka snimku>): kun, telo pri pohledu dolu a pri chuzi, nasednuti, krok a cval
## (pohled jezdce + kamera zboku), drzeni cesty; vypis JIZDA ...
func _jizda_test(dir: String) -> void:
	if kun == null:
		print("JIZDA kun chybi")
		return
	var foto := func(nm: String, zboku := false) -> void:
		var kam: Camera3D = null
		if zboku:
			kam = Camera3D.new()
			add_child(kam)
			var k := kun.global_transform
			kam.global_position = k.origin + k.basis * Vector3(4.5, 1.8, -1.0)
			kam.look_at(k.origin + Vector3(0, 1.3, 0))
			kam.make_current()
		for i in 6:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(dir + "/" + nm + ".png")
		if kam:
			kam.queue_free()
			player.cam.make_current()
	var kp := kun.global_position
	player.place(kp + kun.global_transform.basis * Vector3(-2.2, 0.3, 0.0), kp + Vector3(0, 1.2, 0))
	for i in 40:
		await get_tree().physics_frame
	await foto.call("kun")
	# telo a ruce na volnem miste, pohledem od kone (driv kun zakryval cely zaber - ruce nebyly videt)
	player.place(kp + kun.global_transform.basis * Vector3(-6.0, 0.3, 0.0), kp + kun.global_transform.basis * Vector3(-14.0, 1.0, 0.0))
	for i in 20:
		await get_tree().physics_frame
	if telo:
		var ks: Skeleton3D = telo.get("kostra")
		var nl := ks.find_bone("foot_l") if ks else -1
		print("JIZDA telo: _process %s (%s), processing %s, can_process %s, snimek %d" % [telo.get("snimku"), telo.get("naposled"), telo.is_processing(), telo.can_process(), Engine.get_process_frames()])
		print("JIZDA telo: viditelne %s poloha %s meritko %s chodidlo %s kamera %s" % [telo.is_visible_in_tree(), telo.global_position, telo.scale,
				(ks.global_transform * ks.get_bone_global_pose(nl)).origin if nl >= 0 else Vector3.INF, player.cam.global_position])
	print("JIZDA kun: poloha %s viditelny %s model %s" % [kun.global_position, kun.is_visible_in_tree(), (kun.get("_model") as Node3D).global_transform.basis.get_scale() if kun.get("_model") else Vector3.ZERO])
	player.pitch = deg_to_rad(-65.0)
	await foto.call("telo_dolu")
	player.pitch = deg_to_rad(-25.0)
	player.move_input = Vector2(0, 1)
	for i in 60:
		await get_tree().physics_frame
	await foto.call("telo_chuze")
	player.move_input = Vector2.ZERO
	await foto.call("telo_zboku", true)
	# louc v ruce tela (Misa 28. 10. ruce v prvni osobe): pohled vpred a mirne dolu, ruka v poze drzeni
	predmety.hold("louc", true)
	player.pitch = deg_to_rad(-20.0)
	for i in 20:
		await get_tree().process_frame
	await foto.call("telo_louc")
	await foto.call("telo_louc_zboku", true)
	predmety.hold("", false)
	# sahnuti na cil (IK ruky): predmet na zemi pred hracem - snimek ve vrcholu pohybu
	var cil_s := player.global_position + Basis(Vector3.UP, player.yaw) * Vector3(0.15, 0.25, -0.55)
	telo.sahni(cil_s)
	telo.akce("sebrat")
	player.pitch = deg_to_rad(-45.0)
	for i in 8:
		await get_tree().process_frame
	await foto.call("telo_sahnuti_zacatek")
	for i in 10:
		await get_tree().process_frame
	await foto.call("telo_sahnuti")
	await foto.call("telo_sahnuti_zboku", true)
	player.place(kp + kun.global_transform.basis * Vector3(-1.3, 0.3, 0.0), kp + Vector3(0, 1.2, 0))
	for i in 10:
		await get_tree().physics_frame
	print("JIZDA na dosah %s" % kun.na_dosah(player.global_position))
	kun.nasedni(player)
	player.yaw = kun.rotation.y
	player.pitch = deg_to_rad(-12.0)
	player.move_input = Vector2(0, 0.6)
	for i in 240:
		await get_tree().physics_frame
	print("JIZDA krok: poloha %s rychlost %.2f chod %s" % [kun.global_position, kun.velocity.length(), kun.chod])
	await foto.call("jizda_krok")
	print("JIZDA foto krok hotovo")
	await foto.call("jizda_zboku", true)
	print("JIZDA foto zboku hotovo")
	player.beh = true
	player.move_input = Vector2(0, 1)
	var cesta_d := 0.0
	for i in 150:                                   # xvfb bez GPU: snimek ~ s, 150 kroku fyziky staci na rozjeti cvalem
		await get_tree().physics_frame
		var ck: Vector2 = svet.cesta_kraj_osa(kun.global_position.x, kun.global_position.z)
		cesta_d = maxf(cesta_d, ck.x if ck.y >= 0.0 else 99.0)
	print("JIZDA cval: poloha %s rychlost %.2f chod %s vydrz %.1f, nejdal od cesty %.1f m" % [kun.global_position, kun.velocity.length(), kun.chod, kun.vydrz, cesta_d])
	await foto.call("jizda_cval")
	player.move_input = Vector2.ZERO
	player.beh = false
	for i in 120:
		await get_tree().physics_frame
	kun.sesedni()
	print("JIZDA sesednuti: hrac %s kun %s" % [player.global_position, kun.global_position])
	# po sesednuti musi jit odejit (Misa 28. 10.: „mohl jsem jen zase nasednout“)
	var p_ses := player.global_position
	player.yaw = kun.rotation.y + PI * 0.5
	player.move_input = Vector2(0, 1)
	for i in 90:
		await get_tree().physics_frame
	player.move_input = Vector2.ZERO
	print("JIZDA odchod po sesednuti: %.2f m (na_koni %s)" % [player.global_position.distance_to(p_ses), player.get("na_koni")])
	await foto.call("kun_po_sesednuti_zboku", true)


func _mereni(spec: String) -> void:
	player.set_flying(true)
	var louka: Node = get_node_or_null("Louka")
	for one: String in spec.split("|"):
		if one.count(";") < 1:
			continue                                # prazdne zadani (napr. TVRZ_JIZDA bez mereni)
		var parts := one.split(";")
		var v := parts[1].split_floats(",")
		if v.size() >= 6:              # x,y,z,cx,cy,cz: presna vyska (uvnitr stavby, kde paprsek shora trefi strechu)
			player.place(Vector3(v[0], v[1], v[2]), Vector3(v[3], v[4], v[5]))
		else:
			player.place(Vector3(v[0], _ground_hi(v[0], v[1]) + 1.7, v[1]), Vector3(v[2], _ground_hi(v[2], v[3]) + 1.2, v[3]))
		for i in 10:
			await get_tree().process_frame
		if louka:
			louka.nacti_okoli()
			for i in 400:
				louka._process(0.0)
		for i in 20:
			await get_tree().process_frame
		var dc := 0.0
		var tr := 0.0
		var ob := 0.0
		for i in 30:
			await get_tree().process_frame
			dc += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
			tr += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
			ob += Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)
		print("MERENI %-18s kresleni %5d  troj %6.2f M  objekty %5d  gpu %4d MB (textury %d, buffery %d)" % [parts[0], dc / 30.0, tr / 30.0 / 1e6, ob / 30.0,
				Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0, Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0,
				Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0])
		if parts.size() > 2:
			get_viewport().get_texture().get_image().save_png(parts[2])
		if OS.get_environment("TVRZ_ROZPAD") == "2":
			await _odhad_troj()
			continue
		# rozpad: o kolik ubyde, kdyz se skryje kazda cast sceny (deti hlavni sceny a sveta, Rostliny po druzich)
		var casti: Array = []
		if not OS.has_environment("TVRZ_ROZPAD"):
			continue
		for c in get_children() + world.get_children():
			if c is Node3D and c != world and (c as Node3D).visible:
				casti.append(c)
		var rs: Node = world.get_node_or_null("Rostliny")
		var po_druhu := {}
		if rs:
			for c in rs.get_children():
				var nm := String(c.name)
				var k := nm.left(nm.rfind("_", nm.rfind("_") - 1))
				k = k.left(k.rfind("_")) if k.rfind("_") > 0 and k.right(1).is_valid_int() else k
				if not po_druhu.has(k):
					po_druhu[k] = []
				po_druhu[k].append(c)
		for skup in ["Predmety", "Zivot", "Louka", "Tvrz"]:
			var pn: Node = find_child(skup, true, false)
			if pn == null:
				continue
			for c in pn.get_children():
				if not (c is Node3D and (c as Node3D).visible):
					continue
				var k2: String = str(skup) + " " + String(c.name).rstrip("0123456789@_ ").replace("@", "")
				if not po_druhu.has(k2):
					po_druhu[k2] = []
				po_druhu[k2].append(c)
		var vys: Array = []
		for c: Node3D in casti:
			c.visible = false
			for i in 4:
				await get_tree().process_frame
			vys.append([String(c.name), dc / 30.0 - Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
					tr / 30.0 - Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)])
			c.visible = true
		for k: String in po_druhu:
			for c: Node3D in po_druhu[k]:
				c.visible = false
			for i in 3:
				await get_tree().process_frame
			vys.append([k if k.begins_with("Predmety") or k.begins_with("Zivot") or k.begins_with("Louka") else "rostlina " + k, dc / 30.0 - Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
					tr / 30.0 - Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)])
			for c: Node3D in po_druhu[k]:
				c.visible = true
		vys.sort_custom(func(x: Array, y: Array) -> bool: return x[2] + x[1] * 1000.0 > y[2] + y[1] * 1000.0)
		for v2: Array in vys.slice(0, 30):
			if v2[1] > 5 or v2[2] > 50000:
				print("   %-32s kresleni %5d  troj %6.2f M" % [v2[0], v2[1], v2[2] / 1e6])
	# textury pouzite materialy ve scene: 25 nejvetsich (odhad VRAM: 1 B/px + mipmapy)
	var tex := {}
	for n in get_tree().root.find_children("*", "GeometryInstance3D", true, false):
		var gi := n as GeometryInstance3D
		var mats: Array = [gi.material_override]
		var mesh: Mesh = null
		if gi is MeshInstance3D:
			mesh = (gi as MeshInstance3D).mesh
			for i in (gi as MeshInstance3D).get_surface_override_material_count():
				mats.append((gi as MeshInstance3D).get_surface_override_material(i))
		elif gi is MultiMeshInstance3D and (gi as MultiMeshInstance3D).multimesh:
			mesh = (gi as MultiMeshInstance3D).multimesh.mesh
		if mesh:
			for i in mesh.get_surface_count():
				mats.append(mesh.surface_get_material(i))
		for m: Material in mats:
			if m == null:
				continue
			var tt: Array = []
			if m is BaseMaterial3D:
				for prop in ["albedo_texture", "normal_texture", "orm_texture", "roughness_texture", "metallic_texture", "emission_texture", "heightmap_texture"]:
					tt.append(m.get(prop))
			elif m is ShaderMaterial:
				for u: Dictionary in (m as ShaderMaterial).shader.get_shader_uniform_list() if (m as ShaderMaterial).shader else []:
					tt.append((m as ShaderMaterial).get_shader_parameter(u["name"]))
			for t in tt:
				if t is Texture2D:
					tex[(t as Texture2D).get_rid()] = t
	var rad: Array = []
	var celk := 0.0
	for k in tex:
		var t: Texture2D = tex[k]
		var b := t.get_width() * t.get_height() * 1.33
		celk += b
		rad.append([b, t])
	rad.sort_custom(func(x: Array, y: Array) -> bool: return x[0] > y[0])
	print("TEXTURY pouzite: %d, odhad %d MB" % [rad.size(), celk / 1048576])
	for r: Array in rad.slice(0, 25):
		var t: Texture2D = r[1]
		print("   %5.1f MB  %dx%d  %s" % [r[0] / 1048576.0, t.get_width(), t.get_height(), t.resource_path.right(80) if t.resource_path != "" else "(vytvorena za behu)"])


## Rychly rozpad trojuhelniku bez kresleni (TVRZ_ROZPAD=2): viditelne objekty v zornem poli a v dosahu, plna sit
## (bez LOD), MultiMesh x pocet kreslenych instanci; skupiny podle jmena (bez cisel).
func _odhad_troj() -> void:
	var cam := get_viewport().get_camera_3d()
	var fr := cam.get_frustum()
	var cp := cam.global_position
	var sk := {}
	for n in get_tree().root.find_children("*", "GeometryInstance3D", true, false):
		var gi := n as GeometryInstance3D
		if not gi.is_visible_in_tree():
			continue
		var bb := gi.global_transform * gi.get_aabb()
		var ven := false
		for pl: Plane in fr:
			if pl.distance_to(bb.get_support(-pl.normal)) > 0.0:
				ven = true
				break
		if ven:
			continue
		var d := bb.get_center().distance_to(cp)
		if gi.visibility_range_end > 0.0 and d > gi.visibility_range_end + gi.visibility_range_end_margin + bb.size.length() * 0.5:
			continue
		var tr := 0
		if gi is MeshInstance3D and (gi as MeshInstance3D).mesh:
			tr = _troj_site((gi as MeshInstance3D).mesh)
		elif gi is MultiMeshInstance3D and (gi as MultiMeshInstance3D).multimesh and (gi as MultiMeshInstance3D).multimesh.mesh:
			var mm := (gi as MultiMeshInstance3D).multimesh
			tr = _troj_site(mm.mesh) * (mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count)
		var nm := String(gi.name).rstrip("0123456789_-k@ ")
		var par := String(gi.get_parent().name).rstrip("0123456789_-@ ")
		var key := par + "/" + nm
		if not sk.has(key):
			sk[key] = [0, 0, []]
		sk[key][0] += tr
		sk[key][1] += 1
		sk[key][2].append(gi)
	var ks := sk.keys()
	ks.sort_custom(func(x: String, y: String) -> bool: return sk[x][0] > sk[y][0])
	for k: String in ks.slice(0, 35):
		print("   ODHAD %-44s troj %6.3f M  objektu %d" % [k, sk[k][0] / 1e6, sk[k][1]])
	# skutecny ubytek (s LOD) u 8 nejvetsich: skryt, 4 snimky, zmerit
	var t0 := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	var d0 := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	for k: String in ks.slice(0, 8):
		for gi: GeometryInstance3D in sk[k][2]:
			gi.visible = false
		for i in 4:
			await get_tree().process_frame
		print("   SKUTECNE %-41s troj %6.3f M  kresleni %d" % [k, (t0 - Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)) / 1e6,
				d0 - Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)])
		for gi: GeometryInstance3D in sk[k][2]:
			gi.visible = true


func _troj_site(me: Mesh) -> int:
	if not me is ArrayMesh:
		return me.get_faces().size() / 3
	var tr := 0
	for i in me.get_surface_count():
		var n: int = me.surface_get_array_index_len(i)
		tr += (n if n > 0 else me.surface_get_array_len(i)) / 3
	return tr


func _ground_hi(x: float, z: float) -> float:
	var q := PhysicsRayQueryParameters3D.create(Vector3(x, 400.0, z), Vector3(x, -200.0, z))
	var h := get_viewport().get_world_3d().direct_space_state.intersect_ray(q)
	return float((h["position"] as Vector3).y) if not h.is_empty() else 0.0
