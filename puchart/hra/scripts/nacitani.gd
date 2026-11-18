extends CanvasLayer
## Načítací obrazovka „Blood for Blood“ (autoload Nacitani; Míša 17. 11., předloha nacitani/index.html schválená 17. 11.).
## Tmavé pozadí se zrnem a vinětací, vlevo iluminace v tmavém rámu se zlatou linkou a popisek zdroje, vpravo
## „Potštátsko · léta Páně 1393“, linka s kosočtvercem, pořekadlo s červenou frakturovou iniciálou, převod do dnešní
## češtiny a řádek o sbírce; dole inkoustová linka průběhu. Karta je vidět nejméně cas_min_s (10 s) od zobrazení,
## pak prolnutí do černé (0,7 s) a do hry. Žádné „Stiskni A“. Animace jen prolnutí. Všechny texty a karty:
## hra/data/nacitani.json. Těžké zdroje (seznam „predem“) se načítají vláknem (ResourceLoader.load_threaded_request),
## ať obrazovka nestojí; hlavni.gd pak bere hotové z mezipaměti.
##
## Použití: hlavni.gd na začátku stavby `await Nacitani.zacni()`, na konci `Nacitani.hotovo()`; nabídka čeká na signál
## skonceno (menu.gd play_intro). Vstup do hry z nabídky: `await Nacitani.prechod()` (prochazka.gd) – vrátí se v černé,
## volající přepne na hru a clona se rozplyne.

signal skonceno
signal v_cerne

const DATA := "res://data/nacitani.json"

var cfg: Dictionary = {}
var aktivni := false          # zobrazuje se při tomto spuštění (testy a snímky bez ní – proměnné PUCHART_*)
var bezi := false             # karta je na obrazovce
var karta: Dictionary = {}    # zobrazená karta (test: texty z dat)
var cas := 0.0                # s od zobrazení karty (delta, i v pauze)
var prubeh := 0.0             # zobrazený průběh 0–1

var _cil := 0.0               # skutečný průběh načítání
var _hotovo := false
var _konci := false
var _cekani: Array = []       # cesty ve vláknovém načítání
var _ns := 0
var _posledni := -1
var _fps_vratit := 0          # limit snímků nabídky vrácený po konci karty

var _koren: Control
var _karta_uzel: Control
var _clona: ColorRect
var _obraz: TextureRect
var _ramec: Control
var _popisek: Label
var _misto: Label
var _iniciala: Label
var _citat: Label
var _preklad: Label
var _kdo: RichTextLabel
var _stav: Label
var _linka: Control
var _uvod_uzel: Control    # start aplikace (před nabídkou): jen název a linka, bez karty (Míša 18. 11.)
var uvod := false          # právě běží úvodní načítání


func _ready() -> void:
	layer = 100
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	if FileAccess.file_exists(DATA):
		var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		if typeof(d) == TYPE_DICTIONARY: cfg = d
	aktivni = not cfg.is_empty() and OS.get_environment("PUCHART_NACITANI") != "ne"
	for k: String in cfg.get("bez_obrazovky_pri", []):   # testy, měření a snímky (PUCHART_TEST, PUCHART_FOTO…) bez obrazovky
		if OS.get_environment(k) != "": aktivni = false
	if OS.get_environment("PUCHART_NACITANI") == "ano": aktivni = not cfg.is_empty()
	_postav()


func t(k: String) -> String:
	return String(cfg.get("texty", {}).get(k, ""))


func min_cas() -> float:
	if uvod: return float(cfg.get("uvod_cas_min_s", 2.0))
	return float(cfg.get("cas_min_s", 10.0))


func prolnuti() -> float:
	return float(cfg.get("prolnuti_s", 0.7))


# ------------------------------------------------------------------ stavba obrazovky (rozměry z předlohy 1600×900, výška 1000)

func _postav() -> void:
	_koren = Control.new()
	_koren.set_anchors_preset(Control.PRESET_FULL_RECT)
	_koren.mouse_filter = Control.MOUSE_FILTER_STOP   # dotyk a myš během načítání nikam neprojdou
	add_child(_koren)
	var bg := ColorRect.new(); bg.color = Color("#0b0806"); bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE; _koren.add_child(bg)
	Styl.vrstva(_koren, Styl.prechod([[0.0, Color("#120d09")], [1.0, Color("#0b0806")]], false, true))
	# světlo svíce zleva a slabší odlesk vpravo (předloha .bg: elipsy 55×75 % v 30/52 % a 40×60 % v 72/48 %)
	_elipsa(Vector2(0.30, 0.52), Vector2(0.55, 0.75), Color(120 / 255.0, 78 / 255.0, 38 / 255.0, 0.38), 0.70)
	_elipsa(Vector2(0.72, 0.48), Vector2(0.40, 0.60), Color(70 / 255.0, 48 / 255.0, 28 / 255.0, 0.22), 0.75)
	Styl.zrno_a_vineta(_koren, 0.5, 0.75)

	_karta_uzel = Control.new()
	_karta_uzel.set_anchors_preset(Control.PRESET_FULL_RECT)
	_karta_uzel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_koren.add_child(_karta_uzel)
	# deska s iluminací (předloha .plateWrap left 110, šířka 640; obraz max 540 × 630 → při výšce 1000 max 700)
	var deska := VBoxContainer.new()
	deska.alignment = BoxContainer.ALIGNMENT_CENTER
	deska.add_theme_constant_override("separation", 18)
	deska.anchor_top = 0.0; deska.anchor_bottom = 1.0
	deska.offset_left = 110; deska.offset_right = 750
	deska.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_karta_uzel.add_child(deska)
	_ramec = Ramec.new()
	_ramec.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	deska.add_child(_ramec)
	_obraz = TextureRect.new()
	_obraz.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_obraz.stretch_mode = TextureRect.STRETCH_SCALE
	_obraz.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_obraz.modulate = Color(0.86, 0.80, 0.70)   # předloha: sepia .22, saturate .88, brightness .84
	_ramec.add_child(_obraz)
	_popisek = Styl.bfb_label("", "kurziva", 17, Color(Styl.BFB_INK_DIM, 0.7))
	_popisek.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	deska.add_child(_popisek)

	# pravý sloupec (předloha .text left 840, right 120)
	var sl := VBoxContainer.new()
	sl.alignment = BoxContainer.ALIGNMENT_CENTER
	sl.anchor_left = 0.0; sl.anchor_right = 1.0; sl.anchor_top = 0.0; sl.anchor_bottom = 1.0
	sl.offset_left = 840; sl.offset_right = -120
	sl.add_theme_constant_override("separation", 0)
	sl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_karta_uzel.add_child(sl)
	_misto = Styl.bfb_label("", "sc", 20, Color(Styl.BFB_GOLD_NAC, 0.85), 6)
	sl.add_child(_misto)
	sl.add_child(_mezera(22))
	var ln := Styl.Linka.new(Color(Styl.BFB_GOLD_NAC, 0.55)); ln.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	sl.add_child(ln)
	sl.add_child(_mezera(38))
	var radek := HBoxContainer.new()
	radek.add_theme_constant_override("separation", 12)
	radek.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sl.add_child(radek)
	_iniciala = Styl.bfb_label("", "fraktura", 118, Styl.BFB_RUBRIC)
	_iniciala.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.35))
	_iniciala.add_theme_constant_override("shadow_offset_y", 2)
	# iniciála přes dva řádky (předloha float, line-height .82): pevná buňka 100 px, písmeno vytažené nahoru
	var bunka := Control.new(); bunka.custom_minimum_size = Vector2(96, 100); bunka.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bunka.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_iniciala.position = Vector2(-4, -34)
	bunka.add_child(_iniciala)
	radek.add_child(bunka)
	_citat = Styl.bfb_label("", "kurziva", 44, Styl.BFB_INK)
	_citat.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_citat.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_citat.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_citat.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.6))
	_citat.add_theme_constant_override("shadow_offset_y", 2)
	_citat.add_theme_constant_override("shadow_outline_size", 8)
	_citat.add_theme_constant_override("line_spacing", 4)
	radek.add_child(_citat)
	sl.add_child(_mezera(26))
	_preklad = Styl.bfb_label("", "text", 25, Color(Styl.BFB_INK_DIM, 0.85))
	_preklad.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sl.add_child(_preklad)
	sl.add_child(_mezera(30))
	_kdo = RichTextLabel.new()
	_kdo.fit_content = true
	_kdo.scroll_active = false
	_kdo.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_kdo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sl.add_child(_kdo)

	# dole: inkoustová linka průběhu a stav (předloha .bottom left 840, right 120, bottom 78)
	var dole := Control.new()
	dole.anchor_left = 0; dole.anchor_right = 1; dole.anchor_top = 1; dole.anchor_bottom = 1
	dole.offset_left = 840; dole.offset_right = -120; dole.offset_top = -118; dole.offset_bottom = -78
	dole.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_koren.add_child(dole)
	_linka = Prubeh.new(); _linka.nac = self
	_linka.set_anchors_preset(Control.PRESET_FULL_RECT); _linka.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dole.add_child(_linka)
	_stav = Styl.bfb_label("", "sc", 17, Styl.BFB_INK_DIM, 4)
	_stav.modulate.a = 0.6
	_stav.position = Vector2(0, -2)
	dole.add_child(_stav)

	# úvod při startu aplikace: jen název hry a místo uprostřed (karty s pořekadly až mezi nabídkou a hrou – Míša 18. 11.)
	_uvod_uzel = VBoxContainer.new()
	_uvod_uzel.set_anchors_preset(Control.PRESET_CENTER)
	_uvod_uzel.grow_horizontal = Control.GROW_DIRECTION_BOTH; _uvod_uzel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_uvod_uzel.alignment = BoxContainer.ALIGNMENT_CENTER
	_uvod_uzel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var h: Dictionary = cfg.get("hlavicka", {})
	var tn := Styl.bfb_label(String(h.get("nazev", "")), "titul", 96, Color("#d9c9a3"), 0)
	tn.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_uvod_uzel.add_child(tn)
	var tm := Styl.bfb_label(String(h.get("misto", "")), "sc", 22, Color(Styl.BFB_GOLD_NAC, 0.85), 6)
	tm.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_uvod_uzel.add_child(tm)
	_uvod_uzel.visible = false
	_koren.add_child(_uvod_uzel)

	_clona = ColorRect.new(); _clona.color = Color.BLACK; _clona.set_anchors_preset(Control.PRESET_FULL_RECT)
	_clona.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_koren.add_child(_clona)


func _mezera(h: float) -> Control:
	var c := Control.new(); c.custom_minimum_size.y = h; c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


func _elipsa(stred: Vector2, poloosy: Vector2, col: Color, kraj: float) -> void:
	var r := Styl.vrstva(_koren, Styl.prechod([[0.0, col], [kraj, Color(col, 0.0)], [1.0, Color(col, 0.0)]], true))
	r.set_anchors_preset(Control.PRESET_TOP_LEFT)
	r.anchor_left = stred.x - poloosy.x; r.anchor_right = stred.x + poloosy.x
	r.anchor_top = stred.y - poloosy.y; r.anchor_bottom = stred.y + poloosy.y
	r.offset_left = 0; r.offset_right = 0; r.offset_top = 0; r.offset_bottom = 0


## Vyplní kartu z dat (index < 0 = náhodná, jiná než minule).
func nastav_kartu(i := -1) -> void:
	var karty: Array = cfg.get("karty", [])
	if karty.is_empty(): return
	if i < 0:
		i = randi() % karty.size()
		if karty.size() > 1 and i == _posledni: i = (i + 1) % karty.size()
	_posledni = i
	karta = karty[i]
	var tex: Texture2D = load(String(karta["obrazek"])) if ResourceLoader.exists(String(karta["obrazek"])) else null
	_obraz.texture = tex
	var vel := Vector2(540, 700)
	if tex:
		var k := minf(vel.x / tex.get_width(), vel.y / tex.get_height())
		vel = (Vector2(tex.get_size()) * k).floor()
	_ramec.custom_minimum_size = vel + Vector2(28, 28)
	_obraz.position = Vector2(14, 14); _obraz.size = vel
	_popisek.text = String(cfg.get("popisky_zdroje", {}).get(String(karta["zdroj"]), ""))
	_misto.text = t("misto")
	_iniciala.text = String(karta["ini"])
	_citat.text = String(karta["text"])
	_preklad.text = String(karta["preklad"])
	_kdo.clear()
	_kdo.push_font(Styl.pismo("kurziva"), 19)
	_kdo.push_color(Styl.BFB_RUBRIC); _kdo.add_text("— "); _kdo.pop()
	_kdo.push_color(Styl.BFB_INK_DIM); _kdo.add_text(t("sbirka")); _kdo.pop()
	_kdo.pop()
	_stav.text = t("stav")


# ------------------------------------------------------------------ průběh

## Zobrazí kartu (prolnutí z černé) a načte vláknem zdroje ze seznamu „predem“; vrátí se, až jsou načtené
## (a karta je celá vidět). Pak hlavni.gd staví svět z mezipaměti a nakonec zavolá hotovo().
func zacni() -> void:
	_ukaz(bool(cfg.get("uvod_bez_karty", true)))
	_cekani.clear()
	for p: String in cfg.get("predem", []):
		if ResourceLoader.exists(p) and ResourceLoader.load_threaded_request(p, "", true) == OK:
			_cekani.append(p)
	_ns = _cekani.size()
	while not _cekani.is_empty() or _clona.color.a > 0.01:
		await get_tree().process_frame
	_cil = maxf(_cil, float(cfg.get("podil_predem", 0.8)))
	await get_tree().process_frame   # aspoň jeden snímek s linkou, než se hlavní vlákno zastaví stavbou


## Svět je postavený: linka doběhne, po uplynutí cas_min_s prolnutí do černé a konec (signál skonceno).
func hotovo() -> void:
	_hotovo = true
	_cil = 1.0


## Vstup do hry z nabídky: karta, nejméně cas_min_s, prolnutí do černé; vrátí se v černé (volající přepne na hru),
## pak se černá rozplyne do hry.
func prechod() -> void:
	_ukaz()
	hotovo()
	await v_cerne


func _ukaz(jen_uvod := false) -> void:
	uvod = jen_uvod
	if not uvod: nastav_kartu()
	_karta_uzel.visible = not uvod
	_uvod_uzel.visible = uvod
	visible = true
	bezi = true
	_hotovo = false
	_konci = false
	cas = 0.0
	prubeh = 0.0
	_cil = 0.0
	_stav.modulate.a = 0.6
	_karta_uzel.modulate.a = 1.0
	_clona.color.a = 1.0
	var tw := create_tween()
	tw.tween_property(_clona, "color:a", 0.0, prolnuti())


func _process(d: float) -> void:
	if not bezi: return
	cas += d
	if Engine.max_fps > 0 and Engine.max_fps < 30:   # nabídka drží 10 snímků (prochazka.gd _fps_menu) – prolnutí a linka plynule
		_fps_vratit = Engine.max_fps
		Engine.max_fps = 30
	if not _cekani.is_empty():
		var s := 0.0
		for p: String in _cekani.duplicate():
			var pr := []
			var st := ResourceLoader.load_threaded_get_status(p, pr)
			if st == ResourceLoader.THREAD_LOAD_LOADED or st == ResourceLoader.THREAD_LOAD_FAILED or st == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
				if st == ResourceLoader.THREAD_LOAD_LOADED: ResourceLoader.load_threaded_get(p)   # zůstane v mezipaměti pro load()
				_cekani.erase(p)
			else:
				s += float(pr[0]) if pr.size() > 0 else 0.0
		var hotovych := _ns - _cekani.size()
		_cil = maxf(_cil, float(cfg.get("podil_predem", 0.8)) * (hotovych + s) / maxf(1.0, _ns))
	prubeh = move_toward(prubeh, _cil, d * 0.6)   # inkoust dotéká plynule
	if _hotovo and prubeh >= 0.999 and _stav.modulate.a > 0.0:
		_stav.modulate.a = maxf(0.0, _stav.modulate.a - d / 0.6)
	if _hotovo and not _konci and cas >= min_cas():
		_konci = true
		_konec()


func _konec() -> void:
	var tw := create_tween()
	tw.tween_property(_clona, "color:a", 1.0, prolnuti())
	await tw.finished
	v_cerne.emit()
	await get_tree().process_frame
	bezi = false
	skonceno.emit()
	# do hry: černá se rozplyne (nabídka při startu má vlastní clonu – menu.gd)
	var tw2 := create_tween()
	_karta_uzel.modulate.a = 0.0
	_linka.visible = false
	_stav.modulate.a = 0.0
	_koren.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tw2.tween_property(_clona, "color:a", 0.0, prolnuti())
	await tw2.finished
	if not bezi:
		visible = false
		if _fps_vratit > 0 and get_tree().paused: Engine.max_fps = _fps_vratit   # zpět jen pod nabídkou (hra si limit nastaví sama)
		_fps_vratit = 0
		_linka.visible = true
		_koren.mouse_filter = Control.MOUSE_FILTER_STOP


## Tmavý rám se zlatou linkou (předloha .plate: podklad #17110b, okraj 1 px zlatá .35, vnitřní linka 6 px od kraje .28, stín).
class Ramec extends Control:
	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		for i in 6:   # měkký stín pod deskou
			draw_rect(r.grow(4 + i * 6).grow_individual(0, -i * 2, 0, i * 4), Color(0, 0, 0, 0.09))
		draw_rect(r, Color("#17110b"))
		draw_rect(r, Color(Styl.BFB_GOLD_NAC, 0.35), false, 1.0)
		draw_rect(r.grow(-6), Color(Styl.BFB_GOLD_NAC, 0.28), false, 1.0)
	func _notification(what: int) -> void:
		if what == NOTIFICATION_RESIZED: queue_redraw()


## Inkoustová linka průběhu (předloha .track/.line: stopa 1 px, linka 3 px do světla, svítící kapka na konci).
class Prubeh extends Control:
	var nac: Node
	func _process(_d: float) -> void:
		if nac.bezi: queue_redraw()
	func _draw() -> void:
		var y := size.y - 12.0
		draw_rect(Rect2(0, y, size.x, 1), Color(Styl.BFB_INK, 0.10))
		var w: float = size.x * clampf(nac.prubeh, 0.0, 1.0)
		if w < 1.0: return
		var a := Color("#c9b48a"); var b := Styl.BFB_INK; var z := Color(0.12, 0.08, 0.05, 0.0)
		var x1 := w * 0.3
		draw_polygon(PackedVector2Array([Vector2(0, y - 1), Vector2(x1, y - 1), Vector2(x1, y + 2), Vector2(0, y + 2)]), PackedColorArray([z, a, a, z]))
		draw_polygon(PackedVector2Array([Vector2(x1, y - 1), Vector2(w, y - 1), Vector2(w, y + 2), Vector2(x1, y + 2)]), PackedColorArray([a, b, b, a]))
		for i in 4:
			draw_circle(Vector2(w, y + 0.5), 3.5 + i * 2.5, Color(1.0, 0.84, 0.59, 0.10))
		draw_circle(Vector2(w, y + 0.5), 3.5, Color("#efe3c7"))
