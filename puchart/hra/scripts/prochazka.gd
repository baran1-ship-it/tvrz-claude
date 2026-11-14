extends CanvasLayer
## Po měření (nebo hned, když měření není) úvod a hlavní nabídka jako v Havranovi (menu.gd, Moravian Battlefield): Nová hra
## (Příběh / Pískoviště), Pokračovat, Nahrát, Nastavení, Měření (Míša 12. 11. večer: „na procházku se vykašli“). Ve hře
## menu hráče (menu_hrace.gd) podle Havrana, mapa s rychlým cestováním (mapa.gd, hra/data/mapa_body.json – nabídka Místa
## zrušena: přesun do sklepa propadl pod mapu), ikony vpravo nahoře, létání nahoru/dolů. Denní doba: hlavni.den (den.gd).
var hlavni: Node
var hrac: CharacterBody3D
var _nahoru: Button
var _dolu: Button
var nabidka: Control        # horní lišta (erb + pauza) – pad.gd
var kruhy: Control          # Běh a Let vpravo dole (Havran hud.gd)
var mapa: CanvasLayer
var dvere: Node
var zebriky: Node            # žebříky (zebriky.gd): Lézt nahoru / Slézt dolů
var menu: CanvasLayer       # menu.gd: úvod + pauza
var menu_hrace: CanvasLayer   # Havranovo menu hráče (hv_most.gd)
var hv: Node                  # propojka na Havranovy skripty: předměty, dovednosti, menu hráče, režim hry
var pad_nabidka := false
var _pismo: Font
var _obraz_volby := [1.0, 0.75, 0.6]
var _hudba := 1.0

func _svitek(b: Button, fs := 24, i := 0) -> void:
	if _pismo == null: _pismo = load("res://fonty/GrenzeGotisch-Medium.ttf")
	Styl.tlacitko_pruh(b, _pismo, fs, i)

var _fps_hra := 0
func _fps_menu(ano: bool) -> void:   # statická obrazovka (nabídka, menu hráče) na 10 snímků – méně tepla (rešerše Havrana 10. 11.)
	if ano:
		if Engine.max_fps != 10: _fps_hra = Engine.max_fps
		Engine.max_fps = 10
	else: Engine.max_fps = _fps_hra

func otevri_nabidku() -> void:   # Start: pauza (Havran)
	if menu_hrace.open: menu_hrace.close()
	_fps_menu(true)
	get_tree().paused = true
	menu.show_menu(true)

func zavri_nabidku() -> void:
	menu.hide_menu()
	_fps_menu(false)
	get_tree().paused = false

func otevri_menu_hrace() -> void:
	if menu.visible or menu_hrace.open: return
	menu_hrace.show_page("brasna")
	_fps_menu(true)

var _mh_otevreno := false
func _process(_d: float) -> void:   # Havranovo menu se zavírá samo (B, dotyk) – vrátit snímky hry
	if _mh_otevreno and not menu_hrace.open: _fps_menu(false)
	_mh_otevreno = menu_hrace != null and menu_hrace.open
	if nabidka: nabidka.visible = not _mh_otevreno   # horní lišta (Brašna, Nabídka) přes Havranovo menu neprosvítá
	if kruhy: kruhy.visible = not _mh_otevreno

func pouzij() -> void:   # A: vrata a dveře na dosah, žebřík (bližší z obou)
	var zb: Dictionary = zebriky._blizko if zebriky else {}
	if dvere and dvere._blizko != "":
		var dd: float = (hrac.global_position + Vector3(0, 1.0, 0)).distance_to(dvere.mista[dvere._blizko])
		if zb.is_empty() or dd <= float(zb["d"]): dvere.prepni(dvere._blizko); return
	if not zb.is_empty(): zebriky.pouzij()

func zacni(h: Node, p: CharacterBody3D) -> void:
	hlavni = h; hrac = p
	process_mode = Node.PROCESS_MODE_ALWAYS
	if FileAccess.file_exists("res://data/rozpocty.json"):
		_obraz_volby = JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json"))["obraz_3d"]["volby"]
	var dv: Node = load("res://scripts/dvere.gd").new(); dv.name = "Dvere"; add_child(dv); dv.zacni(h, self); dvere = dv   # vrata a dveře
	var zbr: Node = load("res://scripts/zebriky.gd").new(); zbr.name = "Zebriky"; add_child(zbr); zbr.zacni(h, self); zebriky = zbr   # žebříky (hájovna)
	var ak: Control = load("res://scripts/akce.gd").new(); ak.name = "Akce"; add_child(ak); ak.zacni(self)   # akce předmětů jako Havran (zapálit, otevřít…)
	var pd: Node = load("res://scripts/pad.gd").new(); pd.name = "Pad"; pd.proch = self; pd.hrac = p; add_child(pd)
	var vp := get_viewport().get_visible_rect().size
	# ikony vpravo nahoře jako v Havranovi (hud.gd _btn_menu/_btn_map/_btn_bag/_btn_build; Míša 10. 11.: „mrkni, jak má ikony
	# na ploše pro mapu a stavění“): nabídka = pergamen se třemi řádky, mapa = pergamen s cestou a cílem, brašna = erb
	# se lvem (erby/vse.png), stavění = erb řemesla (erby/remeslo.png) jen v pískovišti
	var lis := Ikony.new(); lis.proch = self; lis.set_anchors_preset(Control.PRESET_FULL_RECT); lis.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(lis); nabidka = lis
	hrac.ui.append(lis)
	# běh a létání na obrazovce jako Havran (hud.gd _run_center/_jump_center, Míša 12. 11. večer: „běh a létání chci mít na
	# obrazovce pro dotyk i na Xbox ovladači jako Havran“): kruhy vpravo dole, dotyk chytají jen samotné kruhy (_has_point)
	var kr := Kruhy.new(); kr.proch = self; kr.set_anchors_preset(Control.PRESET_FULL_RECT); kr.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(kr); kruhy = kr; hrac.ui.append(kr)
	# nahoru/dolů při létání: držená tlačítka vlevo od kruhů
	for i in 2:
		var t := Button.new(); t.text = "▲ nahoru" if i == 0 else "▼ dolů"; t.custom_minimum_size = Vector2(200, 110)
		_svitek(t, 28, i); t.position = Vector2(vp.x - 520, vp.y - 260 + i * 130); t.visible = false
		var smer := 1.0 if i == 0 else -1.0
		t.button_down.connect(func(): hrac.vzhuru = smer)
		t.button_up.connect(func(): hrac.vzhuru = 0.0)
		add_child(t)
		if i == 0: _nahoru = t
		else: _dolu = t
		hrac.ui.append(t)
	mapa = load("res://scripts/mapa.gd").new(); mapa.hrac = hrac; mapa.proch = self; add_child(mapa)
	hv = load("res://scripts/hv_most.gd").new(); hv.name = "Havran"; add_child(hv); hv.setup(h, p)   # menu hráče, předměty, dovednosti z Havrana
	menu_hrace = hv.menu_hrace
	menu = load("res://scripts/menu.gd").new(); add_child(menu)
	menu.action.connect(_akce)
	_nastaveni()
	menu.saves = _seznam_ulozeni()
	_na_start()
	get_tree().paused = true
	_fps_menu(true)
	menu.play_intro()   # úvod: erb Bočka z Kunštátu, název hry, hudba (Havran)
	if OS.get_environment("PUCHART_SAVETEST") != "":   # test ukládání: pískoviště, předmět do brašny, uložit, posunout, nahrát
		await get_tree().create_timer(3.0).timeout
		_akce("sandbox", null); await get_tree().create_timer(0.5).timeout
		hv.predmety.add_inv("sud", 3); var p0 := hrac.global_position
		_akce("save", null); menu.saves = _seznam_ulozeni()
		hrac.position += Vector3(30, 0, 30); hv.predmety.add_inv("sud", -3)
		_akce("load", menu.saves[0]["file"]); await get_tree().create_timer(0.5).timeout
		print("SAVETEST ulozeni %d, poloha zpet %.2f m, sudu %d, rezim %s" % [menu.saves.size(), hrac.global_position.distance_to(p0), int(hv.predmety.inv.get("sud", 0)), hv.mode])
		get_tree().quit()
	if OS.get_environment("PUCHART_MENU_HRACE_FOTO") != "":   # snímek menu hráče (Havran) v pískovišti: stránka z PUCHART_MENU_STRANKA
		await get_tree().create_timer(3.0).timeout
		_akce("sandbox", null); await get_tree().create_timer(1.0).timeout
		if OS.get_environment("PUCHART_MENU_STRANKA") != "hud": menu_hrace.show_page(OS.get_environment("PUCHART_MENU_STRANKA") if OS.get_environment("PUCHART_MENU_STRANKA") != "" else "brasna")
		await get_tree().create_timer(2.0).timeout
		get_viewport().get_texture().get_image().save_png(OS.get_environment("PUCHART_MENU_HRACE_FOTO")); get_tree().quit()
	if OS.get_environment("PUCHART_MENU_FOTO") != "":   # snímek úvodní nabídky (kontrola vzhledu bez tabletu)
		await get_tree().create_timer(9.0).timeout
		get_viewport().get_texture().get_image().save_png(OS.get_environment("PUCHART_MENU_FOTO")); get_tree().quit()

func _nastaveni() -> void:
	var t := {"beh": "Běh: " + ("ano" if hrac.bezi else "ne"), "let": "Létání: " + ("ano" if hrac.leti else "ne"),
		"obraz": "Obraz 3D: %d %%" % roundi(get_viewport().scaling_3d_scale * 100), "vol:hudba": _hudba}
	if hlavni.den: t["cas"] = "Denní doba: %s (%s)" % [hlavni.den.NAMES[hlavni.den.current], hlavni.den.clock_text()]   # Havran settings „time“
	menu.refresh_settings(t)

func _akce(co: String, arg: Variant) -> void:
	match co:
		"play", "resume":
			zavri_nabidku()
		"story", "sandbox":   # výběr hry jako v Havranovi (Míša 10. 11.): pískoviště = stavění a předměty z katalogu
			hv.mode = "piskoviste" if co == "sandbox" else "pribeh"
			if hv.mode == "piskoviste" and hv.predmety.inv.is_empty(): hv.predmety.start_kit()
			_na_start()   # nová hra: u vnější branky (mapa_body.json start), denní doba od začátku (den.json start)
			if hlavni.den: hlavni.den.set_time(String(hlavni.den.cfg["start"]), 0.01)
			menu.in_game = true; menu.can_save = true
			zavri_nabidku()
		"mapa":
			zavri_nabidku(); mapa.prepni()
		"quit":
			get_tree().quit()
		"save":
			_uloz(); menu.saves = _seznam_ulozeni(); zavri_nabidku(); hv.hud.toast("Hra uložena", 2.2)
		"mereni_spust":   # test výkonu jen na přání (Míša 14. 11.): příznak + nové spuštění, měření začne hned po načtení
			var cf := ConfigFile.new(); cf.load("user://nastaveni.cfg"); cf.set_value("test", "pri_startu", true); cf.save("user://nastaveni.cfg")
			if menu.can_save: _uloz()
			get_tree().paused = false
			Engine.max_fps = 0   # nabídka drží 10 snímků – nesmí přejít do měření (hlavni.gd limit nastaví znovu)
			get_tree().reload_current_scene()
		"save_quit":
			if menu.can_save: _uloz()
			get_tree().quit()
		"continue":
			if not menu.saves.is_empty(): _nahraj(String(menu.saves[0]["file"]))
		"load":
			_nahraj(String(arg))
		"set:beh":
			hrac.bezi = not hrac.bezi; hrac._beh_packa = false   # přepínač: běh trvá, dokud ho hráč nevypne (Havran _beh_tl)
		"set:let":
			hrac.prepni_let(); _nahoru.visible = hrac.leti; _dolu.visible = hrac.leti
		"set:obraz":   # rozlišení 3D dokola podle rozpocty.json
			var i := 0
			for k in _obraz_volby.size():
				if absf(float(_obraz_volby[k]) - get_viewport().scaling_3d_scale) < 0.01: i = k
			get_viewport().scaling_3d_scale = float(_obraz_volby[(i + 1) % _obraz_volby.size()])
			var cf := ConfigFile.new(); cf.load("user://nastaveni.cfg")   # volba hráče platí i po restartu (Míša 12. 11.)
			cf.set_value("obraz", "scale_3d", get_viewport().scaling_3d_scale); cf.save("user://nastaveni.cfg")
		"set:cas":   # Havran: další denní doba (rychlý přechod)
			if hlavni.den: hlavni.den.set_time(hlavni.den.next_key(), 2.0)
		"vol:hudba":
			_hudba = float(arg); menu.music.volume_db = linear_to_db(maxf(_hudba, 0.001)) - 6.0
	_nastaveni()

## Začátek hry (mapa_body.json start): výška paprskem dolů na kolize jako u cestování po mapě (mapa.gd cil_na_zemi).
func _na_start() -> void:
	var st: Dictionary = mapa.cfg["start"]
	var c := Vector2(st["cil"][0], st["cil"][1]); var po := Vector2(st["pohled"][0], st["pohled"][1])
	mapa.priprav_kolize(hlavni, c)
	var bez: Array[RID] = [hrac.get_rid()]
	var p: Vector3 = mapa.cil_na_zemi(hlavni, mapa.cfg, c, bez)
	hrac.velocity = Vector3.ZERO
	hrac.position = p + Vector3(0, 0.1, 0)
	hrac.nastav_pohled(atan2(-(po.x - p.x), -(po.y - p.z)), -0.05)


## Ukládání a nahrávání (Havran main.gd _save_game/_list_saves/_apply_save): user://ulozeni/hra_<čas>.json, posledních 20.
## Uloží režim, polohu a pohled, brašnu, výbavu a položené předměty (predmety.to_save) a dovednosti.
const SAVE_DIR := "user://ulozeni"
const REZIMY := {"pribeh": "Příběh", "piskoviste": "Pískoviště"}
func _seznam_ulozeni() -> Array:
	var out: Array = []; var d := DirAccess.open(SAVE_DIR)
	if d == null: return out
	for f in d.get_files():
		if not f.ends_with(".json"): continue
		var j: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_DIR + "/" + f))
		if typeof(j) != TYPE_DICTIONARY: continue
		out.append({"file": SAVE_DIR + "/" + f, "t": int(j.get("unix", 0)), "label": "%s – %s" % [REZIMY.get(j.get("mode", ""), "Hra"), String(j.get("kdy", f))]})
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["t"] > b["t"])
	return out

func _uloz() -> void:
	DirAccess.make_dir_recursive_absolute(SAVE_DIR)
	var now := Time.get_unix_time_from_system(); var dt := Time.get_datetime_dict_from_system(); var p := hrac.global_position
	var j := {"mode": hv.mode, "unix": int(now), "kdy": "%d. %d. %d  %02d:%02d" % [dt["day"], dt["month"], dt["year"], dt["hour"], dt["minute"]],
		"pos": [p.x, p.y, p.z], "yaw": hrac._yaw, "pitch": hrac._pitch, "let": hrac.leti, "predmety": hv.predmety.to_save(), "dovednosti": hv.dovednosti.to_save()}
	if hlavni.den: j["hodina"] = hlavni.den.hour; j["den"] = hlavni.den.day_n   # Havran save: denní doba
	var fa := FileAccess.open(SAVE_DIR + "/hra_%d.json" % int(now), FileAccess.WRITE); fa.store_string(JSON.stringify(j)); fa.close()
	var old := _seznam_ulozeni()
	for k in range(20, old.size()): DirAccess.remove_absolute(String(old[k]["file"]))

func _nahraj(path: String) -> void:
	var j: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(j) != TYPE_DICTIONARY: return
	hv.mode = String(j.get("mode", "pribeh"))
	if j.has("dovednosti"): hv.dovednosti.from_save(j["dovednosti"])
	if j.has("predmety"): hv.predmety.from_save(j["predmety"])
	if hlavni.den and j.has("hodina"): hlavni.den.day_n = int(j.get("den", 1)); hlavni.den.set_hour(float(j["hodina"]), 0.01)
	var a: Array = j["pos"]
	hlavni.svet.kolize_ihned(Vector3(a[0], a[1], a[2]))
	hrac.velocity = Vector3.ZERO; hrac.position = Vector3(a[0], a[1] + 0.05, a[2])
	hrac.nastav_pohled(float(j.get("yaw", 0.0)), float(j.get("pitch", 0.0)))
	if bool(j.get("let", false)) != hrac.leti: hrac.prepni_let()
	menu.in_game = true; menu.can_save = true
	zavri_nabidku()


## Běh a Let jako Havran (hud.gd: Běh = přepínač vlevo od skoku, rozsvícený = běží; let v Puchartu vlastním kruhem
## místo dvojklepnutí skoku – Puchart skok nemá). Kreslí se jen kruhy, dotyk berou jen ony (jinak by kryly tlačítka dveří).
class Kruhy extends Control:
	var proch: Node
	var _font: Font = ThemeDB.fallback_font
	func run_c() -> Vector2: return let_c() + Vector2(-118, 22)          # Havran _run_center
	func let_c() -> Vector2: return size - Vector2(120, 120)             # Havran _jump_center
	func _process(_d: float) -> void:
		if Engine.get_process_frames() % 6 == 0: queue_redraw()
	func _draw() -> void:
		var h: Node = proch.hrac
		var rc := run_c()
		draw_circle(rc, 32, Color(1.0, 0.85, 0.4, 0.35) if h.bezi else Color(0, 0, 0, 0.25))
		draw_arc(rc, 32, 0, TAU, 36, Color(1, 1, 1, 0.45), 2.0, true)
		draw_string(_font, rc + Vector2(-32, 6), "Běh", HORIZONTAL_ALIGNMENT_CENTER, 64, 15, Color(1, 1, 1, 0.9))
		var lc := let_c()
		draw_circle(lc, 40, Color(1.0, 0.85, 0.4, 0.35) if h.leti else Color(0, 0, 0, 0.25))
		draw_arc(lc, 40, 0, TAU, 40, Color(1, 1, 1, 0.45), 2.0, true)
		draw_polyline(PackedVector2Array([lc + Vector2(-12, 6), lc + Vector2(0, -8), lc + Vector2(12, 6)]), Color(1, 1, 1, 0.8), 3.0, true)
		draw_string(_font, lc + Vector2(-40, 58), "Přistát" if h.leti else "Let", HORIZONTAL_ALIGNMENT_CENTER, 80, 15, Color(1, 1, 1, 0.85))
	func ma_bod(p: Vector2) -> bool:
		return p.distance_to(run_c()) < 44.0 or p.distance_to(let_c()) < 52.0   # zásahy jako Havran (běh 44, skok 58 px)
	func _has_point(p: Vector2) -> bool:
		return ma_bod(p)
	func _gui_input(e: InputEvent) -> void:
		# jen tlačítko myši: na tabletu ho Godot emuluje z dotyku (emulate_mouse_from_touch), na PC je skutečné – přepínač se
		# přepne právě jednou (dotyk i myš zároveň by ho přepnuly 2×)
		if not (e is InputEventMouseButton and (e as InputEventMouseButton).pressed and (e as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT): return
		var p := (e as InputEventMouseButton).position
		if p.distance_to(run_c()) < 44.0: proch._akce("set:beh", null)
		elif p.distance_to(let_c()) < 52.0: proch._akce("set:let", null)
		else: return
		accept_event(); queue_redraw()


class Ikony extends Control:
	var proch: Node
	var _bag: Texture2D = load("res://obrazky/erby/vse.png")
	var _stav: Texture2D = load("res://obrazky/erby/remeslo.png")
	func _r_menu() -> Rect2: return Rect2(size.x - 86, 18, 68, 60)
	func _r_map() -> Rect2: return Rect2(size.x - 86, 92, 68, 52)
	func _r_bag() -> Rect2: return Rect2(size.x - 170, 14, 68, 68)
	func _r_stav() -> Rect2: return Rect2(size.x - 254, 14, 68, 68)
	func _stavi() -> bool: return proch.hv != null and proch.hv.mode == "piskoviste"
	func _process(_d: float) -> void: queue_redraw()
	func _draw() -> void:
		var mr := _r_menu(); Styl.kresli_pruh(self, mr.grow(4), 0.4, 0.9)
		for k in 3: draw_line(mr.position + Vector2(20, 19 + k * 11), mr.position + Vector2(48, 19 + k * 11), Color(Styl.INK, 0.85), 3.0, true)
		var mp := _r_map(); Styl.kresli_pruh(self, mp.grow(4), 0.4, 0.9)
		draw_polyline(PackedVector2Array([mp.position + Vector2(16, 40), mp.position + Vector2(28, 24), mp.position + Vector2(38, 34), mp.position + Vector2(50, 18)]), Color(Styl.INK, 0.8), 2.0, true)
		draw_circle(mp.position + Vector2(50, 18), 3.5, Color(Styl.RED, 0.95))
		draw_texture_rect(_bag, _r_bag(), false, Color(1, 1, 1, 0.85))
		if _stavi(): draw_texture_rect(_stav, _r_stav(), false, Color(1, 1, 1, 0.8))
	func _has_point(p: Vector2) -> bool:   # Míša 12. 11.: „dveře ani vrata nefungují, nabídka je, ale nejde kliknout“ – ikony přes celou
		return ma_bod(p)                    # obrazovku pohltily dotyk na tlačítku dveří pod sebou; dotyk chytají jen samotné ikony
	func ma_bod(p: Vector2) -> bool:   # dotyk na ikoně nehýbe postavou (hrac.ui)
		return _r_menu().has_point(p) or _r_map().has_point(p) or _r_bag().has_point(p) or (_stavi() and _r_stav().has_point(p))
	func _gui_input(e: InputEvent) -> void:
		var p := Vector2.INF
		if e is InputEventScreenTouch and (e as InputEventScreenTouch).pressed: p = (e as InputEventScreenTouch).position
		elif e is InputEventMouseButton and (e as InputEventMouseButton).pressed: p = (e as InputEventMouseButton).position
		if p == Vector2.INF: return
		if _r_menu().has_point(p): proch.otevri_nabidku()
		elif _r_map().has_point(p): proch.mapa.prepni()
		elif _r_bag().has_point(p): proch.otevri_menu_hrace()
		elif _stavi() and _r_stav().has_point(p):
			proch.otevri_menu_hrace(); proch.menu_hrace.show_page("staveni")
		else: return
		accept_event()
