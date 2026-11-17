extends CanvasLayer
## Hlavní nabídka „Blood for Blood“ (Míša 17. 11., předloha menu/index.html schválená 17. 11.). Původní nabídka
## (Moravian Battlefield, erb, pečeť) je zálohou v menu_stare.gd do schválení.
## Pozadí obrazky/menu_pozadi.jpg (soumrak z přední věže), zleva tmavý přechod, zrno, vinětace. Název Grenze Gotisch,
## pod ním „Potštátsko · léta Páně 1393“ kapitálkami a linka s kosočtvercem. Položky jen text (Cormorant SC, #a8987a);
## vybraná (ovladač, šipky, myš, prst) leží na opáleném pruhu pergamenu (textury/ui/tlacitko_0–3), tmavý inkoust a
## kosočtverec vlevo. Vpravo dole náhodné pořekadlo z hra/data/nacitani.json. Stránky se střídají prolnutím 0,35 s.
## Stejné menu slouží i jako pauza ve hře (Start / tlačítko vpravo nahoře). Akce posílá signálem action(co, arg) –
## obsluhuje prochazka.gd.

signal action(what: String, arg: Variant)

const PROLNUTI := 0.35            # předloha #menu transition .35s
# autoři a licence: jen na této stránce menu (obrázky načítací obrazovky se doplní z hra/data/nacitani.json)
const CREDITS := [
	"Pozadí nabídky: snímek ze hry (soumrak z přední věže)",
	"Hudba nabídky: „Medieval: Exploration“ – RandomMind (opengameart.org), CC0",
	"Textury, rostliny a předměty: Poly Haven, CC0",
	"Figurka na mapě: „Mounted knight“ (Skoll) a „Pikeman“ (Delapouite) – game-icons.net, CC BY 3.0, obarveno",
	"Padlé kmeny: „Dead Tree Trunk“ (Rob Tuytel) a „Dead Tree Trunk 02“ (Jenelle van Heerden, Rico Cilliers) – Poly Haven, CC0",
	"Ostřice a vrby: fotoskeny listů ambientCG, CC0; devětsil: list z „Dim's Arboretum“ – Dim (opengameart.org), CC-BY 3.0",
	"Terén: DMR 5G, ČÚZK; vodní síť a cesty: ZABAGED, OpenStreetMap (ODbL)",
	"Hrad podle kreseb a půdorysů GC80T08 a rešerší (docs/reference)",
	"Pece, krby, kamna, kuchyňská topeniště a nádobí: vlastní modely Míšina modeláře (Topení 1400 a doplněk, 2026); textury Poly Haven, CC0 – Rock Face 03, Rough Wood, White Rough Plaster, Clay Plaster (Amal Kumar), Plaster Stone Wall 01 (Charlotte Baglioni), Large Sandstone Blocks (Rob Tuytel); prameny: Vlastivědné muzeum v Olomouci, NPÚ (Kachlová kamna 2021), Archaeologia historica (kachle z hradu Kost)",
	"Seno a dřevěné vidle: vlastní modely Míšina modeláře (Seno 1400, 2026); fotka sena „Hay“ – RedBirdTheCardinal (opengameart.org), CC0; dřevo vidlí Rough Wood (Rob Tuytel) – Poly Haven, CC0",
	"Písma: Grenze Gotisch (Omnibus-Type), Cormorant SC a Cormorant Garamond (Christian Thalmann, Cormorant Project), UnifrakturMaguntia (j. 'mach' wust, Peter Wiegel) – SIL Open Font License 1.1 (fonty/OFL_*.txt)",
	"Herní engine: Godot Engine, MIT",
]

var in_game := false            # běží hra: menu je pauza
var settings_text: Dictionary = {}
var saves: Array = []             # uložené hry [{file, t, label}] (Havran menu.gd) – plní prochazka.gd
var can_save := false
var data: Dictionary = {}         # hra/data/nacitani.json (název, místo, verze, pořekadla, autoři obrázků)
var porekadlo: Dictionary = {}    # zobrazené pořekadlo (karta z dat)

var _bg: TextureRect
var _tma: Control                 # přechody a vinětace přes pozadí
var _shade: ColorRect             # ztmavení hry pod pauzou
var _head: VBoxContainer
var _box: VBoxContainer
var _scroll: ScrollContainer
var _panel: Control               # sloupec nabídky (prolíná se)
var _saw: VBoxContainer
var _saw_q: RichTextLabel
var _saw_g: Label
var _ver: Label
var _veil: ColorRect
var _page := "main"
var _busy := false
var _intro := false
var music: AudioStreamPlayer


func _ready() -> void:
	layer = 20
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	if FileAccess.file_exists("res://data/nacitani.json"):
		var d: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/nacitani.json"))
		if typeof(d) == TYPE_DICTIONARY: data = d
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	var noc := ColorRect.new(); noc.color = Styl.BFB_NOC; noc.set_anchors_preset(Control.PRESET_FULL_RECT)
	noc.mouse_filter = Control.MOUSE_FILTER_IGNORE; root.add_child(noc)
	_bg = TextureRect.new()
	if ResourceLoader.exists("res://obrazky/menu_pozadi.jpg"): _bg.texture = load("res://obrazky/menu_pozadi.jpg")
	_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_bg.modulate = Color(0.80, 0.77, 0.70)   # předloha .art: brightness .8, sepia .12, saturate .9
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_bg)
	noc.visible = true
	_tma = Control.new(); _tma.set_anchors_preset(Control.PRESET_FULL_RECT); _tma.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_tma)
	# zleva tmavý přechod (zadání: 0 % ~96 %, 24 % ~88 %, 42 % ~45 %, 62 % skoro nic; předloha .fadeL)
	var t0 := Color(12 / 255.0, 9 / 255.0, 6 / 255.0)
	Styl.vrstva(_tma, Styl.prechod([[0.0, Color(t0, 0.96)], [0.24, Color(t0, 0.88)], [0.42, Color(t0, 0.45)], [0.62, Color(t0, 0.05)], [1.0, Color(t0, 0.15)]]))
	var fb := Styl.vrstva(_tma, Styl.prechod([[0.0, Color(10 / 255.0, 7 / 255.0, 5 / 255.0, 0.0)], [1.0, Color(10 / 255.0, 7 / 255.0, 5 / 255.0, 0.9)]], false, true))
	fb.anchor_top = 1.0; fb.offset_top = -290; fb.offset_bottom = 0   # předloha .fadeB 260 px z 900
	Styl.zrno_a_vineta(_tma, 0.55, 0.7)
	_shade = ColorRect.new(); _shade.set_anchors_preset(Control.PRESET_FULL_RECT); _shade.color = Color(0, 0, 0, 0)
	_shade.mouse_filter = Control.MOUSE_FILTER_IGNORE; root.add_child(_shade)

	# hlavička (předloha .head left 130, top 120 z 900)
	var hl: Dictionary = data.get("hlavicka", {})
	_head = VBoxContainer.new(); _head.position = Vector2(130, 130); _head.add_theme_constant_override("separation", 0)
	_head.mouse_filter = Control.MOUSE_FILTER_IGNORE; root.add_child(_head)
	var title := Styl.bfb_label(String(hl.get("nazev", "Blood for Blood")), "titul", 84, Styl.BFB_GOLD)
	title.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.7))
	title.add_theme_constant_override("shadow_offset_y", 3)
	title.add_theme_constant_override("shadow_outline_size", 3)
	_head.add_child(title)
	var place := Styl.bfb_label(String(hl.get("misto", "")), "sc", 20, Color(Styl.BFB_GOLD, 0.8), 6)
	_head.add_child(_mezera(10)); _head.add_child(place)
	_head.add_child(_mezera(18))
	var ln := Styl.Linka.new(Color(Styl.BFB_GOLD, 0.55)); ln.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_head.add_child(ln)

	# nabídka (předloha #menu left 130, top 380 z 900, šířka 520; pruh pergamenu přesahuje o 14 px vlevo)
	_panel = Control.new()
	_panel.anchor_top = 0; _panel.anchor_bottom = 1
	_panel.offset_left = 130 - 24; _panel.offset_right = 130 + 700; _panel.offset_top = 405; _panel.offset_bottom = -110
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.visible = false
	root.add_child(_panel)
	_scroll = ScrollContainer.new()   # Havran (Míša 0.92): nastavení se nevešlo na tablet – posuvná plocha
	_scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_scroll.scroll_deadzone = 12
	_scroll.follow_focus = true
	_panel.add_child(_scroll)
	var okraj := MarginContainer.new()   # místo pro pruh pergamenu nad/pod/vlevo od textu (scroll ořezává)
	okraj.add_theme_constant_override("margin_left", 24)
	okraj.add_theme_constant_override("margin_top", 12)
	okraj.add_theme_constant_override("margin_bottom", 12)
	okraj.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(okraj)
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 0)
	okraj.add_child(_box)

	# pořekadlo vpravo dole (předloha .saw right 120, bottom 96, šířka 640)
	_saw = VBoxContainer.new()
	_saw.anchor_left = 1; _saw.anchor_right = 1; _saw.anchor_top = 1; _saw.anchor_bottom = 1
	_saw.offset_left = -120 - 700; _saw.offset_right = -120; _saw.offset_top = -260; _saw.offset_bottom = -96
	_saw.alignment = BoxContainer.ALIGNMENT_END
	_saw.add_theme_constant_override("separation", 10)
	_saw.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_saw)
	_saw_q = RichTextLabel.new()
	_saw_q.fit_content = true; _saw_q.scroll_active = false
	_saw_q.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_saw_q.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_saw_q.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	_saw_q.add_theme_constant_override("shadow_outline_size", 10)
	_saw_q.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_saw.add_child(_saw_q)
	_saw_g = Styl.bfb_label("", "text", 20, Styl.BFB_INK_DIM)
	_saw_g.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_saw_g.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_saw.add_child(_saw_g)
	nove_porekadlo()

	_ver = Styl.bfb_label(String(data.get("menu", {}).get("verze", "")), "sc", 15, Styl.BFB_INK_OFF, 3)
	_ver.anchor_top = 1; _ver.anchor_bottom = 1; _ver.offset_left = 130; _ver.offset_top = -72; _ver.offset_bottom = -52
	root.add_child(_ver)

	_veil = ColorRect.new(); _veil.color = Color(0, 0, 0, 0); _veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	_veil.mouse_filter = Control.MOUSE_FILTER_IGNORE; root.add_child(_veil)

	music = AudioStreamPlayer.new()
	if ResourceLoader.exists("res://hudba/menu.ogg"):
		var st: AudioStream = load("res://hudba/menu.ogg")
		if st is AudioStreamOggVorbis: (st as AudioStreamOggVorbis).loop = true
		music.stream = st
	music.volume_db = -6.0
	add_child(music)


func _mezera(h: float) -> Control:
	var c := Control.new(); c.custom_minimum_size.y = h; c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


## Jedno náhodné pořekadlo z karet načítací obrazovky (staročesky kurzívou, červená iniciála, převod menším písmem).
func nove_porekadlo() -> void:
	var karty: Array = data.get("karty", [])
	if karty.is_empty():
		_saw.visible = false
		return
	porekadlo = karty[randi() % karty.size()]
	Styl.porekadlo(_saw_q, String(porekadlo["ini"]), String(porekadlo["text"]), 30, 44, Color(Styl.BFB_INK, 0.92))
	_saw_g.text = String(porekadlo["preklad"])


func _nacitani() -> Node:
	return get_node_or_null("/root/Nacitani")


# ------------------------------------------------------------------ úvod

## Start hry: nabídka se vynoří z černé (předloha #veil 1,2 s) – až dojede načítací obrazovka (Nacitani.skonceno).
func play_intro() -> void:
	visible = true
	in_game = false
	_intro = true
	_bg.visible = true
	_tma.visible = true
	_shade.color.a = 0.0
	_veil.color.a = 1.0
	show_page("main", false)
	var nc := _nacitani()
	if nc and nc.bezi: await nc.skonceno
	if music.stream: music.play()
	var tw := create_tween()
	tw.tween_property(_veil, "color:a", 0.0, float(data.get("menu", {}).get("uvod_s", 1.2)))
	await tw.finished
	_intro = false


func _input(event: InputEvent) -> void:
	if not visible:
		return
	var nc := _nacitani()
	if _busy or (nc and nc.bezi):
		if event is InputEventKey or event is InputEventJoypadButton or event is InputEventJoypadMotion:
			get_viewport().set_input_as_handled()   # během prolnutí a načítání se nevybírá
		return
	# A na ovladači potvrdí položku s fokusem (na některých zařízeních ui_accept A nemá)
	if event is InputEventJoypadButton and event.pressed and (event as InputEventJoypadButton).button_index == JOY_BUTTON_A:
		var f := get_viewport().gui_get_focus_owner()
		if f is Button and not (f as Button).disabled:
			(f as Button).pressed.emit()
			get_viewport().set_input_as_handled()
			return
	if event is InputEventJoypadButton and event.pressed and (event as InputEventJoypadButton).button_index in [JOY_BUTTON_B, JOY_BUTTON_START]:
		_back()
		get_viewport().set_input_as_handled()
	if event is InputEventKey and event.pressed and (event as InputEventKey).keycode in [KEY_ESCAPE, KEY_BACKSPACE]:
		_back()
		get_viewport().set_input_as_handled()


func _back() -> void:
	if _page == "vykreslovani":
		show_page("settings")
	elif _page != "main":
		show_page("main")
	elif in_game:
		action.emit("resume", null)


# ------------------------------------------------------------------ stránky

func show_menu(game_running: bool) -> void:
	in_game = game_running
	visible = true
	_bg.visible = not game_running
	_tma.visible = true
	_veil.color.a = 0.0
	_shade.color = Color(0, 0, 0, 0.55 if game_running else 0.0)
	var vk := _vyk()
	if game_running and vk: vk.navrat_do_menu()   # pojistka Vulkanu: vstup do hry proběhl (vykreslovani.gd)
	nove_porekadlo()
	show_page("main", false)


func hide_menu() -> void:
	visible = false
	_panel.visible = false
	if music.playing: music.stop()


## Stránka nabídky; prolnout = výměna prolnutím 0,35 s ven a 0,35 s dovnitř (předloha go()).
func show_page(page: String, prolnout := true) -> void:
	if prolnout and visible and _panel.visible:
		if _busy: return
		_busy = true
		get_viewport().gui_release_focus()
		var tw := create_tween()
		tw.tween_property(_panel, "modulate:a", 0.0, PROLNUTI)
		await tw.finished
		_stav_stranku(page)
		var tw2 := create_tween()
		tw2.tween_property(_panel, "modulate:a", 1.0, PROLNUTI)
		await tw2.finished
		_busy = false
		return
	_panel.modulate.a = 1.0
	_stav_stranku(page)


func _stav_stranku(page: String) -> void:
	_page = page
	for c in _box.get_children():
		_box.remove_child(c)
		c.queue_free()
	_panel.visible = true
	_scroll.scroll_vertical = 0
	var first: Button
	match page:
		"main":
			var vk := _vyk()
			if vk and vk.hlaska != "": _note(vk.hlaska)   # „Vulkan spadl, vráceno na Compatibility“ (vykreslovani.gd pojistka)
			# celá herní nabídka jako v Havranovi (Míša 10. 11.: „udělej celé herní menu, ať můžu ukládat“)
			if in_game:
				first = _btn("Pokračovat ve hře", "resume")
			first = _maybe(first, _btn("Nová hra", "page:play"))   # Havran „Hrát“ → Příběh / Pískoviště (Míša 12. 11.: bez procházky)
			if not in_game and not saves.is_empty():
				_btn("Pokračovat", "continue")
			var bl := _btn("Nahrát", "page:load"); bl.disabled = saves.is_empty()
			var bs := _btn("Uložit", "save"); bs.disabled = not can_save
			if in_game:
				_btn("Mapa", "mapa")   # rychlé cestování jen z mapy jako v Havranovi (nabídka Místa zrušena, Míša 12. 11. večer)
			_btn("Nastavení", "page:settings")
			if FileAccess.file_exists("user://mereni.txt"): _btn("Měření", "page:mereni")   # poslední výsledek měření (Míša 12. 11.)
			_btn("Uložit a ukončit" if can_save else "Ukončit", "save_quit")
			_btn("Autoři a licence", "page:credits", true)
		"load":
			for sv: Dictionary in saves.slice(0, 7):
				first = _maybe(first, _btn(String(sv["label"]), "load", true, sv["file"]))
			first = _maybe(first, _btn("Zpět", "page:main", true))
		"play":   # výběr hry jako v Havranovi (Míša 10. 11.)
			first = _btn("Příběh", "story")
			_btn("Pískoviště", "sandbox")
			_btn("Zpět", "page:main", true)
		"mereni":   # poslední výsledek testovacího měření (user://mereni.txt z mereni.gd)
			for line: String in FileAccess.get_file_as_string("user://mereni.txt").split("\n"):
				_note(line)
			var vk := _vyk()   # pro srovnání i poslední měření v druhém vykreslování (mereni.gd user://mereni_<id>.txt)
			if vk:
				for v: Dictionary in vk.cfg.get("volby", []):
					var f := "user://mereni_%s.txt" % v["id"]
					if String(v["metoda"]) == vk.metoda or not FileAccess.file_exists(f): continue
					_note(String(vk.text("mereni_jine")) % v["nazev"])
					for line: String in FileAccess.get_file_as_string(f).split("\n"):
						_note(line)
			first = _btn("Zpět", "page:main", true)
		"vykreslovani":   # přepínač s vysvětlením; volba = zápis user://override.cfg a restart hry
			var vk := _vyk()
			for line: String in vk.text("vysvetleni"):
				_note(line)
			_note(String(vk.text("bezi")) % [vk.bezici()["nazev"], vk.adapter, vk.api])
			if vk.duvod() != "": _note(vk.duvod())
			for v: Dictionary in vk.cfg.get("volby", []):
				var bezi: bool = String(v["metoda"]) == vk.metoda
				var b := _btn(("✓ " if bezi else "") + String(v["nazev"]), "vyk:" + String(v["id"]), true)
				b.disabled = bezi
				if not bezi: first = _maybe(first, b)
			first = _maybe(first, _btn("Zpět", "page:settings", true))
		"credits":
			for line: String in CREDITS + _credits_obrazku():
				_note(line)
			first = _btn("Zpět", "page:main", true)
		"settings":
			for key: String in ["beh", "let", "obraz", "cas"]:
				if key == "cas" and (not in_game or not settings_text.has("cas")): continue   # Havran: denní doba jen ve hře
				var bb := _btn(String(settings_text.get(key, key)), "set:" + key)
				first = _maybe(first, bb)
			_slider("Hlasitost hudby", "vol:hudba", float(settings_text.get("vol:hudba", 1.0)))
			var vk := _vyk()   # Obraz: vykreslování Compatibility / Vulkan (vykreslovani.gd, Míša 15. 11.)
			if vk: _btn(String(vk.text("radek_nastaveni")) % vk.bezici()["nazev"], "page:vykreslovani")
			if FileAccess.file_exists("res://data/mereni.json"): _btn("Spustit test výkonu", "mereni_spust")   # jen na přání (Míša 14. 11.)
			_btn("Zpět", "page:main", true)
	for c in _box.get_children():   # nedostupná položka se přeskakuje (předloha move(): do{…}while(off))
		if c is Button and (c as Button).disabled: (c as Button).focus_mode = Control.FOCUS_NONE
	if first:
		first.call_deferred("grab_focus")


## Autoři obrázků načítací obrazovky (soubor na Commons, zdroj, licence – hra/data/nacitani.json obrazky).
func _credits_obrazku() -> Array:
	var out: Array = []
	for o: Dictionary in data.get("obrazky", []):
		out.append("%s: %s – Wikimedia Commons „%s“ (%s), %s" % [String(o.get("popis", "")), String(o.get("dilo", "")),
				String(o.get("commons", "")), String(o.get("puvod", "")), String(o.get("licence", ""))])
	for k: String in data.get("credits", []):
		out.append(k)
	return out


## Autoload Vykreslovani (project.godot) – přes cestu, aby skript šel načíst i bez autoloadů (nástroje --script).
func _vyk() -> Node:
	return get_node_or_null("/root/Vykreslovani")


func refresh_settings(texts: Dictionary) -> void:
	settings_text = texts
	if visible and _page == "settings":
		var f := get_viewport().gui_get_focus_owner()
		var i := f.get_index() if f and f.get_parent() == _box else -1
		_stav_stranku("settings")   # hodnota se mění na místě, bez prolnutí; fokus zůstane na řádku
		if i >= 0 and i < _box.get_child_count() and _box.get_child(i) is Control:
			(_box.get_child(i) as Control).call_deferred("grab_focus")


func _maybe(cur: Button, b: Button) -> Button:
	return cur if cur else b


func _note(t: String) -> void:
	var l := Styl.bfb_label(t, "text", 21 if t.length() < 90 else 18, Styl.BFB_INK_DIM)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size.x = 640.0
	l.add_theme_constant_override("line_spacing", -2)
	var m := MarginContainer.new()
	m.add_theme_constant_override("margin_left", 34)
	m.add_theme_constant_override("margin_bottom", 6)
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.add_child(l)
	_box.add_child(m)


func _btn(t: String, what: String, small := false, arg: Variant = null) -> Button:
	var b := Polozka.new()
	b.text = t
	b.small = small
	b.var_i = _box.get_child_count()
	b.custom_minimum_size = Vector2(520, 58 if not small else 50)
	if small and _box.get_child_count() > 0:
		var m := _mezera(10); _box.add_child(m)   # předloha .it.small margin-top 10
	b.pressed.connect(func() -> void: _press(what, arg))
	_box.add_child(b)
	return b


## Řádek s posuvníkem hlasitosti (text jako položka, posuvník zlatou linkou).
func _slider(t: String, what: String, v: float) -> void:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 20)
	h.custom_minimum_size = Vector2(520, 58)
	h.mouse_filter = Control.MOUSE_FILTER_PASS
	var l := Styl.bfb_label(t, "sc", 30, Styl.BFB_INK_DIM, 2)
	l.custom_minimum_size.x = 300
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var m := MarginContainer.new(); m.add_theme_constant_override("margin_left", 34); m.add_child(l)
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(m)
	var sl := HSlider.new()
	sl.min_value = 0.0
	sl.max_value = 1.0
	sl.step = 0.05
	sl.value = v
	sl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sl.custom_minimum_size.y = 32
	var tr := StyleBoxFlat.new()
	tr.bg_color = Color(Styl.BFB_INK_DIM, 0.3)
	tr.content_margin_top = 1
	tr.content_margin_bottom = 1
	var fill := tr.duplicate() as StyleBoxFlat
	fill.bg_color = Color(Styl.BFB_GOLD, 0.9)
	sl.add_theme_stylebox_override("slider", tr)
	sl.add_theme_stylebox_override("grabber_area", fill)
	sl.add_theme_stylebox_override("grabber_area_highlight", fill)
	sl.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	sl.value_changed.connect(func(x: float) -> void: action.emit(what, x))
	h.add_child(sl)
	_box.add_child(h)


func _press(what: String, arg: Variant) -> void:
	if _busy: return
	if what.begins_with("page:"):
		show_page(what.substr(5))
		return
	if what.begins_with("vyk:"):   # přepnutí vykreslování: zápis volby a restart (vykreslovani.gd prepni)
		var vk := _vyk()
		if vk:
			for c in _box.get_children(): c.queue_free()
			_note(String(vk.text("restart")))
			vk.prepni.call_deferred(what.substr(4))
		return
	action.emit(what, arg)


## Index položky s fokusem (test a snímky).
func vybrana() -> Button:
	var f := get_viewport().gui_get_focus_owner()
	return f as Button if f is Button and f.get_parent() == _box else null


## Položka nabídky: jen text na tmě (Cormorant SC, #a8987a); vybraná = opálený pruh pergamenu (tlacitko_0–3 dokola),
## tmavý inkoust #2f1c0b a kosočtverec vlevo (předloha .it.sel). Nedostupná #5f5546. Myš i prst nad položkou ji vyberou.
class Polozka extends Button:
	var small := false
	var var_i := 0

	func _ready() -> void:
		flat = true
		focus_mode = Control.FOCUS_ALL
		mouse_filter = Control.MOUSE_FILTER_PASS        # tah prstem po položce posouvá nabídku
		alignment = HORIZONTAL_ALIGNMENT_LEFT
		var e := StyleBoxEmpty.new()
		for s in ["normal", "hover", "pressed", "focus", "disabled", "hover_pressed"]:
			add_theme_stylebox_override(s, e)
		add_theme_font_override("font", Styl.pismo("sc", 2))
		add_theme_font_size_override("font_size", 26 if small else 34)
		for s in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color", "font_hover_pressed_color", "font_disabled_color"]:
			add_theme_color_override(s, Color(0, 0, 0, 0))   # text kreslí _draw (pod ním pergamen)
		mouse_entered.connect(func() -> void:
			if not disabled: grab_focus())
		focus_entered.connect(queue_redraw)
		focus_exited.connect(queue_redraw)

	func _draw() -> void:
		var on := has_focus() and not disabled
		var fs := 26 if small else 34
		var f := Styl.pismo("sc", 2)
		if on:
			var w := 400.0 if small else 470.0
			var tex := Styl.tex("tlacitko_%d" % (var_i % 4))
			var r := Rect2(-14, -9, w, size.y + 18)
			for k in 3:   # drop-shadow 0 4px 10px .55
				draw_texture_rect(tex, Rect2(r.position + Vector2(0, 4 + k), r.size).grow(2 + k * 2), false, Color(0, 0, 0, 0.12))
			draw_texture_rect(tex, r, false, Color(0.98, 0.98, 0.98))
			Styl.kresli_kosoctverec(self, Vector2(8.5, size.y * 0.5), 9.0, Color(Styl.BFB_SEL_INK, 0.85), Color(Styl.BFB_SEL_INK, 0.25))
		var col := Styl.BFB_SEL_INK if on else (Styl.BFB_INK_OFF if disabled else Styl.BFB_INK_DIM)
		var y := (size.y + f.get_ascent(fs) - f.get_descent(fs)) * 0.5
		draw_string(f, Vector2(34, y), text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)
