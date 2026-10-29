extends CanvasLayer
## Menu hrace (D-pad dolu nebo ikona brasny): stranky Brasna, Dovednosti, Denik, Staveni (jen piskoviste) a vymena
## s truhlou. Dovednosti a Denik ctou main.dovednosti (scripts/dovednosti.gd, jmena a popisy z pravidla/svet/dovednosti.json).
## Nahore erbovni stity kategorii (LB/RB), stranky LT/RT, vlevo tmavy panel s detailem predmetu,
## vpravo pergamen se seznamem. Kresli se primo (_draw), ovlada ovladacem i dotykem.

const GOLD := Color(0.89, 0.73, 0.41)
const GOLD_D := Color(0.47, 0.33, 0.14)
const INK := Color(0.2, 0.12, 0.06)
const KAT_B := [["vse", "Vše"], ["zbrane", "Zbraně"], ["zbroj", "Zbroj"], ["naradi", "Nářadí"], ["jidlo", "Jídlo"],
		["byliny", "Byliny"], ["nadoby", "Nádoby"], ["ostatni", "Ostatní"]]
const KAT_S := [["venku", "Venku"], ["uvnitr", "Uvnitř"], ["dekorace", "Dekorace"], ["remeslo", "Řemeslo"], ["zbrojnice", "Zbrojnice"], ["jidlo", "Jídlo"], ["polozene", "Položené"]]
const KAT_D := [["vse", "Vše"], ["tuhost", "Tuhost"], ["mrstnost", "Mrštnost"], ["dech", "Dech"], ["vaznost", "Vážnost"]]
const KAT_J := [["skutky", "Skutky"], ["zvyky", "Zvyky"]]
const ROWS := 8
const Dov := preload("res://scripts/dovednosti.gd")

var main: Node
var P: Node                    # predmety.gd
var page := "brasna"           # brasna | dovednosti | denik | staveni | vymena
var tab := 0
var sel := [0, 0]              # vybrany radek (vlevo hrac, vpravo truhla)
var side := 0
var scroll := [0, 0]
var box: Dictionary = {}       # otevrena truhla (zaznam z predmety.gd)
var open := false
var _sleeping := false

var _c: Control
var _fb: Font
var _fm: Font
var _erby: Dictionary = {}
var _trig := [false, false]
var _rects: Array = []         # [Rect2, akce, arg] pro dotyk
var _drag := -1.0
var _tap_row := -1
var _hint_t := ""
var _hint_ms := 0
var _stick_y := false
var _stick_x := false
var _opened_ms := 0           # stisk, ktery menu otevrel, nesmi hned vybrat polozku
var _prec: Array = []          # zalozka Polozene: zaznamy polozenych predmetu (podle vzdalenosti)


func _ready() -> void:
	layer = 18
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	_fb = load("res://fonts/GrenzeGotisch-Bold.ttf")
	_fm = load("res://fonts/GrenzeGotisch-Medium.ttf")
	for k in KAT_B + KAT_S + KAT_D + KAT_J:
		var ep := "res://obrazky/erby/%s.png" % k[0]
		if ResourceLoader.exists(ep):
			_erby[k[0]] = load(ep)
	_c = Control.new()
	_c.set_anchors_preset(Control.PRESET_FULL_RECT)
	_c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_c.draw.connect(_draw_all)
	add_child(_c)


func show_page(p: String, container: Dictionary = {}, keep := false) -> void:
	# keep: navrat do katalogu po polozeni predmetu (stejna zalozka a radek)
	if not (keep and page == p):
		tab = 0
		sel = [0, 0]
		scroll = [0, 0]
	page = p
	box = container
	_opened_ms = Time.get_ticks_msec()
	side = 0 if p != "vymena" else 1
	open = true
	visible = true
	main.hud.visible = false
	get_tree().paused = true
	if p != "spanek":
		main.life.sfx("menu_otevrit" if p != "vymena" else main.predmety.zvuk_kontejneru(box, true), -6.0)
	_c.queue_redraw()


func _hint(t: String) -> void:
	# kratka zprava primo v menu (hlaska ve hre by za menu nebyla videt)
	_hint_t = t
	_hint_ms = Time.get_ticks_msec()
	main.life.sfx("menu_vyber", -10.0)
	_c.queue_redraw()
	get_tree().create_timer(2.2).timeout.connect(_c.queue_redraw)


func close() -> void:
	if not open:
		return
	if page == "vymena" and not box.is_empty():
		P.show_hung(box)
	if page == "spanek" and main.player.seated and not _sleeping:
		main.player.stand_up()
	if page == "vymena":
		main.life.sfx("menu_zpet" if page != "vymena" else main.predmety.zvuk_kontejneru(box, false), -6.0)
	open = false
	visible = false
	main.hud.visible = true
	get_tree().paused = false


# ------------------------------------------------------------------ obsah

func _tabs() -> Array:
	match page:
		"staveni":
			return KAT_S
		"dovednosti":
			return KAT_D
		"denik":
			return KAT_J
	return KAT_B


func _pages() -> Array:
	if page == "vymena":
		return [["vymena", P.name_of(box["id"])]]
	var pages := [["brasna", "Brašna"], ["dovednosti", "Dovednosti"], ["denik", "Deník"]]
	if main.mode == "piskoviste":
		pages.append(["staveni", "Stavění"])
	return pages


func _dv_stranka() -> bool:
	return page == "dovednosti" or page == "denik"


## Dovednosti: vlohy a umy (vybrana vloha = ona sama a jeji umy); Denik: skutky s poctem / vsechny zvyky (odemcene prvni).
func _dv_items() -> Array:
	var dv: Node = main.dovednosti
	var D: Dictionary = Dov.D
	var out: Array = []
	if page == "dovednosti":
		var k: String = KAT_D[tab][0]
		for v: String in D["vlohy"]:
			if k == "vse" or k == v:
				out.append(v)
		for u: String in D["umy"]:
			if k == "vse" or String(D["umy"][u]["vloha"]) == k:
				out.append(u)
	elif KAT_J[tab][0] == "skutky":
		for sk: String in D.get("skutky", {}):
			if not sk.begins_with("_") and int(dv.skutky.get(sk, 0)) > 0:
				out.append(sk)
	else:
		for z: String in D["zvyky"]["seznam"]:
			if dv.zvyky.has(z):
				out.append(z)
		for z: String in D["zvyky"]["seznam"]:
			if not dv.zvyky.has(z):
				out.append(z)
	return out


func _dv_nazev(id: String) -> String:
	var dv: Node = main.dovednosti
	if page == "dovednosti":
		return dv.nazev_of(id)
	if KAT_J[tab][0] == "skutky":
		return String(Dov.D["skutky"][id][0])
	return String(Dov.D["zvyky"]["seznam"][id]["nazev"])


func _dv_hodnota(id: String) -> String:
	var dv: Node = main.dovednosti
	if page == "dovednosti":
		return str(dv.uroven_of(id))
	if KAT_J[tab][0] == "skutky":
		var e: Array = Dov.D["skutky"][id]
		return String(e[1]) % (int(dv.skutky.get(id, 0)) * int(e[2]))
	return "ano" if dv.zvyky.has(id) else "–"


func _items(s: int) -> Array:
	# seznam id pro stranu s (0 = hrac / katalog, 1 = truhla)
	var out: Array = []
	if _dv_stranka():
		return _dv_items() if s == 0 else out
	if page == "staveni":
		var k: String = KAT_S[tab][0]
		if k == "polozene":
			var pp: Vector3 = main.player.global_position
			_prec = P.placed.filter(func(r: Dictionary) -> bool: return not bool(r.get("pevne", false)))
			_prec.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
				return pp.distance_squared_to(a["p"]) < pp.distance_squared_to(b["p"]))
			for rec: Dictionary in _prec:
				out.append(String(rec["id"]))
			return out
		for id: String in P.kat:
			if str(P.kat[id].get("stav", "")) == k:
				out.append(id)
		return out
	var src: Dictionary = P.inv if s == 0 else box.get("obsah", {})
	var k2: String = KAT_B[tab][0]
	for id: String in src:
		var kk = P.kat.get(id, {}).get("kat", null)
		var cat: String = String(kk) if kk != null else "ostatni"
		if k2 == "vse" or cat == k2 or (k2 == "jidlo" and cat == "piti"):
			out.append(id)
	out.sort_custom(func(a: String, b: String) -> bool: return P.name_of(a) < P.name_of(b))
	return out


func _count(s: int, id: String) -> int:
	if page == "staveni" or _dv_stranka():
		return 0
	var src: Dictionary = P.inv if s == 0 else box.get("obsah", {})
	return int(src.get(id, 0))


func _polozene() -> bool:
	return page == "staveni" and KAT_S[tab][0] == "polozene"


func _selected_rec() -> Dictionary:
	_items(0)
	if _prec.is_empty() or not _polozene():
		return {}
	return _prec[clampi(sel[0], 0, _prec.size() - 1)]


func _remove_sel() -> void:
	# zalozka Polozene, X: odstranit polozeny predmet (menu zustava otevrene)
	var rec := _selected_rec()
	if rec.is_empty():
		return
	P.delete(rec)
	sel[0] = clampi(sel[0], 0, maxi(0, _items(0).size() - 1))
	_c.queue_redraw()


func _stash() -> void:
	# svetlo z ruky zpet do brasny
	if P.held_id == "":
		return
	P.add_inv(P.held_id)
	P.hold("", false)
	main.life.sfx("presun", -8.0)
	_c.queue_redraw()


func _selected() -> String:
	var it := _items(side)
	if it.is_empty():
		return ""
	return it[clampi(sel[side], 0, it.size() - 1)]


# ------------------------------------------------------------------ akce

const SPANEK := [["rano", "Do rána"], ["poledne", "Do poledne"], ["odpoledne", "Do odpoledne"], ["soumrak", "Do soumraku"],
		["noc", "Do noci"]]


func _sleep_opts() -> Array:
	var out := []
	for o: Array in SPANEK:
		if o[0] != main.day.current:
			out.append(o)
	out.append(["", "Jen chvíli poležet"])
	return out


func _act() -> void:
	if page == "spanek":
		var o: Array = _sleep_opts()[clampi(sel[0], 0, _sleep_opts().size() - 1)]
		_sleeping = true          # i "jen polezet": zustane lezet, pohyb ho zvedne
		close()
		_sleeping = false
		if o[0] != "":
			main.sleep_until(o[0])
		return
	var id := _selected()
	if id == "" or _dv_stranka():
		return
	match page:
		"staveni":
			if _polozene():
				var rec := _selected_rec()
				close()
				P.begin_move(rec, true)
			else:
				close()
				P.begin_place(id, false)
		"brasna":
			if P.SVETLA.has(id):
				# lucerna, svicen, louc: do ruky (predchozi svetlo z ruky do brasny)
				if P.held_id != "":
					P.add_inv(P.held_id)
				P.add_inv(id, -1)
				close()
				P.hold(id, false)
			elif main.mode == "piskoviste":
				close()
				P.begin_place(id, true)
		"vymena":
			_move(id, side, 1)
	_c.queue_redraw()


func _move(id: String, from: int, n: int) -> void:
	var src: Dictionary = P.inv if from == 0 else box["obsah"]
	var dst: Dictionary = box["obsah"] if from == 0 else P.inv
	n = mini(n, int(src.get(id, 0)))
	if n <= 0:
		return
	if from == 0 and P.kat[box["id"]].has("jen"):
		# hak a stojan: jen zbrane, nastroje a stity, kazda ma sve misto
		var jen: Array = P.kat[box["id"]]["jen"]
		var kk = P.kat.get(id, {}).get("kat", null)
		if kk == null or not jen.has(String(kk)):
			_hint("Sem patří jen zbraně, štíty a nářadí")
			return
		var used := 0
		for k: String in box["obsah"]:
			used += int(box["obsah"][k])
		if used >= P.slots(box["id"]).size():
			_hint("Všechna místa jsou obsazená")
			return
		n = 1
	elif from == 0:
		var cap := float(P.kat[box["id"]].get("kont", 0))
		var w := float(P.kat.get(id, {}).get("vaha", 0.0))
		n = mini(n, int(floor((cap - P.weight(box["obsah"])) / maxf(w, 0.01))))
		if n <= 0:
			_hint("Do %s se to už nevejde" % P.name_of(box["id"]).to_lower())
			return
	src[id] = int(src[id]) - n
	if int(src[id]) <= 0:
		src.erase(id)
	dst[id] = int(dst.get(id, 0)) + n
	main.life.sfx("presun", -8.0, randf_range(0.9, 1.1))


func _take_all() -> void:
	if _polozene():
		_remove_sel()
		return
	if page != "vymena":
		return
	for id: String in box["obsah"].keys():
		_move(id, 1, int(box["obsah"][id]))
	_c.queue_redraw()


func _tab(d: int) -> void:
	tab = wrapi(tab + d, 0, _tabs().size())
	sel = [0, 0]
	scroll = [0, 0]
	main.life.sfx("listovat", -10.0)
	_c.queue_redraw()


func _page(d: int, cil := "") -> void:
	if page == "vymena":
		return
	var pages := _pages()
	var i := 0
	for j in pages.size():
		if pages[j][0] == page:
			i = j
	page = cil if cil != "" else String(pages[wrapi(i + d, 0, pages.size())][0])
	tab = 0
	scroll = [0, 0]
	sel = [0, 0]
	main.life.sfx("listovat", -8.0)
	_c.queue_redraw()


func _sel(d: int) -> void:
	var n := _items(side).size() if page != "spanek" else _sleep_opts().size()
	if n == 0:
		return
	sel[side] = wrapi(sel[side] + d, 0, n)          # z vrchu dolu a naopak
	if sel[side] < scroll[side]:
		scroll[side] = sel[side]
	elif sel[side] >= scroll[side] + ROWS:
		scroll[side] = sel[side] - ROWS + 1
	_c.queue_redraw()


# ------------------------------------------------------------------ vstup

func _input(event: InputEvent) -> void:
	if not open:
		return
	if event is InputEventJoypadButton and event.pressed:
		if Time.get_ticks_msec() - _opened_ms < 250:
			get_viewport().set_input_as_handled()
			return
		match (event as InputEventJoypadButton).button_index:
			JOY_BUTTON_B, JOY_BUTTON_START:
				close()
			JOY_BUTTON_A:
				_act()
			JOY_BUTTON_X:
				_take_all()
			JOY_BUTTON_Y:
				if page == "brasna":
					_stash()
			JOY_BUTTON_LEFT_SHOULDER:
				_tab(-1)
			JOY_BUTTON_RIGHT_SHOULDER:
				_tab(1)
			JOY_BUTTON_DPAD_UP:
				_sel(-1)
			JOY_BUTTON_DPAD_DOWN:
				_sel(1)
			JOY_BUTTON_DPAD_LEFT:
				if page == "vymena":
					side = 0
					_c.queue_redraw()
			JOY_BUTTON_DPAD_RIGHT:
				if page == "vymena":
					side = 1
					_c.queue_redraw()
		get_viewport().set_input_as_handled()
	elif event is InputEventJoypadMotion:
		var m := event as InputEventJoypadMotion
		if m.axis == JOY_AXIS_LEFT_Y:
			# packa: jeden krok na vychyleni, dalsi az po navratu ke stredu
			if absf(m.axis_value) > 0.6 and not _stick_y:
				_stick_y = true
				_sel(1 if m.axis_value > 0 else -1)
			elif absf(m.axis_value) < 0.3:
				_stick_y = false
		if m.axis == JOY_AXIS_LEFT_X and page == "vymena":
			if absf(m.axis_value) > 0.6 and not _stick_x:
				_stick_x = true
				side = 1 if m.axis_value > 0 else 0
				_c.queue_redraw()
			elif absf(m.axis_value) < 0.3:
				_stick_x = false
		for k in 2:
			var ax: JoyAxis = JOY_AXIS_TRIGGER_LEFT if k == 0 else JOY_AXIS_TRIGGER_RIGHT
			if m.axis == ax:
				var on := m.axis_value > 0.6
				if on and not _trig[k]:
					_page(-1 if k == 0 else 1)
				_trig[k] = on
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenTouch or (event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT):
		var pos: Vector2 = event.position
		if event.pressed:
			_drag = pos.y
			_tap_row = -1
		else:
			if _drag >= 0.0 and absf(pos.y - _drag) < 24.0:
				_tap(pos)
			_drag = -1.0
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag:
		var dd := event as InputEventScreenDrag
		if _drag >= 0.0 and absf(dd.position.y - _drag) > 60.0:
			var st := -1 if dd.position.y > _drag else 1
			scroll[side] = clampi(scroll[side] + st, 0, maxi(0, _items(side).size() - ROWS))
			_drag = dd.position.y
			_c.queue_redraw()
		get_viewport().set_input_as_handled()


func _tap(p: Vector2) -> void:
	for r: Array in _rects:
		if (r[0] as Rect2).has_point(p):
			match String(r[1]):
				"tab":
					tab = int(r[2])
					sel = [0, 0]
					scroll = [0, 0]
					main.life.sfx("listovat", -10.0)
				"page":
					if page != String(r[2]):
						_page(0, String(r[2]))
				"row":
					var a: Array = r[2]
					if side == int(a[0]) and sel[side] == int(a[1]):
						_act()
					else:
						side = int(a[0])
						sel[side] = int(a[1])
				"act":
					_act()
				"all":
					_take_all()
				"stash":
					_stash()
				"close":
					close()
			_c.queue_redraw()
			return


# ------------------------------------------------------------------ kresleni

func _u() -> float:
	var s := _c.get_viewport_rect().size
	return minf(s.x / 1600.0, s.y / 1000.0)


func _txt(f: Font, t: String, p: Vector2, fs: float, col: Color, align := HORIZONTAL_ALIGNMENT_LEFT, w := -1.0) -> void:
	_c.draw_string(f, p, t, align, w, int(fs), col)


func _draw_all() -> void:
	_rects.clear()
	var s := _c.get_viewport_rect().size
	var u := _u()
	if page == "spanek":
		_draw_sleep(s, u)
		return
	_c.draw_rect(Rect2(Vector2.ZERO, s), Color(0.02, 0.02, 0.03, 0.72))
	var ox := (s.x - 1600 * u) * 0.5
	var O := Vector2(ox, (s.y - 1000 * u) * 0.5)
	# --- stranky (LT/RT)
	var pages := _pages()
	var px := O.x + 40 * u
	for i in pages.size():
		var on: bool = pages[i][0] == page
		var t: String = pages[i][1]
		var fs := 46 * u if on else 34 * u
		_txt(_fb, t, Vector2(px, O.y + 70 * u), fs, GOLD if on else Color(0.75, 0.68, 0.55))
		var w := _fb.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, int(fs)).x
		_rects.append([Rect2(px - 10 * u, O.y + 20 * u, w + 20 * u, 64 * u), "page", pages[i][0]])
		if on:
			_c.draw_line(Vector2(px, O.y + 84 * u), Vector2(px + w, O.y + 84 * u), GOLD, 2.0 * u)
		px += w + 34 * u
	if pages.size() > 1:
		_txt(_fm, "LT · RT", Vector2(O.x + 40 * u, O.y + 116 * u), 20 * u, GOLD_D)
	# --- erby kategorii (LB/RB)
	var tabs := _tabs()
	var ex := O.x + 1600 * u - 120 * u - tabs.size() * 124 * u
	_txt(_fm, "LB", Vector2(ex - 50 * u, O.y + 70 * u), 22 * u, GOLD_D)
	for i in tabs.size():
		var on2 := i == tab
		var sz := (112 if on2 else 92) * u
		var c := Vector2(ex + i * 124 * u + 62 * u, O.y + 60 * u)
		if on2:
			for k in 6:
				_c.draw_circle(c, sz * (0.62 - k * 0.04), Color(1.0, 0.8, 0.45, 0.05))
		if _erby.has(tabs[i][0]):
			_c.draw_texture_rect(_erby[tabs[i][0]], Rect2(c - Vector2(sz, sz) * 0.5, Vector2(sz, sz)), false)
		else:
			# bez erbu (vlohy, denik): pecet s pocatecnim pismenem
			_c.draw_circle(c, sz * 0.36, Color(0.32, 0.08, 0.06) if on2 else Color(0.22, 0.1, 0.07))
			_c.draw_arc(c, sz * 0.36, 0, TAU, 32, GOLD if on2 else GOLD_D, 2.5 * u, true)
			var pis: String = String(tabs[i][1]).substr(0, 1)
			_txt(_fb, pis, Vector2(c.x - sz * 0.36, c.y + sz * 0.15), sz * 0.42, GOLD if on2 else Color(0.8, 0.74, 0.6), HORIZONTAL_ALIGNMENT_CENTER, sz * 0.72)
		var nm: String = tabs[i][1]
		_txt(_fm, nm, Vector2(c.x - 62 * u, O.y + 140 * u), 22 * u, GOLD if on2 else Color(0.8, 0.74, 0.6), HORIZONTAL_ALIGNMENT_CENTER, 124 * u)
		_rects.append([Rect2(c - Vector2(62, 60) * u, Vector2(124, 150) * u), "tab", i])
	_txt(_fm, "RB", Vector2(ex + tabs.size() * 124 * u + 10 * u, O.y + 70 * u), 22 * u, GOLD_D)
	# --- obsah
	if page == "vymena":
		_list(Rect2(O + Vector2(40, 180) * u, Vector2(745, 690) * u), 0, "Brašna", u)
		_list(Rect2(O + Vector2(815, 180) * u, Vector2(745, 690) * u), 1, P.name_of(box["id"]), u)
		_detail_line(Rect2(O + Vector2(40, 890) * u, Vector2(1520, 90) * u), u)
	else:
		if _dv_stranka():
			_dv_detail(Rect2(O + Vector2(40, 180) * u, Vector2(500, 800) * u), u)
		else:
			_detail(Rect2(O + Vector2(40, 180) * u, Vector2(500, 800) * u), u)
		var tit: String = {"brasna": "Kryštofova brašna", "dovednosti": "Kryštofovy dovednosti", "denik": "Kryštofův deník"}.get(page, "Katalog")
		_list(Rect2(O + Vector2(580, 180) * u, Vector2(980, 800) * u), 0, tit, u)
	# zavrit (dotyk)
	var cr := Rect2(Vector2(s.x - 76 * u, 14 * u), Vector2(60, 60) * u)
	Styl.kresli_pecet(_c, cr.get_center(), 27 * u)
	_rects.append([cr.grow(10 * u), "close", 0])
	if _hint_t != "" and Time.get_ticks_msec() - _hint_ms < 2000:
		var hr := Rect2(Vector2(s.x * 0.5 - 360 * u, s.y - 70 * u), Vector2(720 * u, 50 * u))
		Styl.kresli_pruh(_c, hr.grow_individual(0, 10 * u, 0, 10 * u), 0.7 * u)
		_txt(_fm, _hint_t, Vector2(hr.position.x, hr.position.y + 34 * u), 28 * u, INK, HORIZONTAL_ALIGNMENT_CENTER, hr.size.x)


func _draw_sleep(s: Vector2, u: float) -> void:
	# maly pergamen uprostred: do kdy spat
	var opts := _sleep_opts()
	var r := Rect2(s.x * 0.5 - 300 * u, s.y * 0.5 - (110 + opts.size() * 34) * u, 600 * u, (190 + opts.size() * 68) * u)
	Styl.kresli_list(_c, r.grow(16 * u), 0.5 * u)
	_txt(_fb, "Jak dlouho spát?", Vector2(r.position.x, r.position.y + 70 * u), 44 * u, INK, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	var y := r.position.y + 105 * u
	for i in opts.size():
		var row := Rect2(r.position.x + 60 * u, y, r.size.x - 120 * u, 56 * u)
		Styl.kresli_tlacitko(_c, row, i, i == sel[0], row.size.y / 76.0)
		_txt(_fm, opts[i][1], Vector2(row.position.x, row.position.y + 40 * u), 32 * u, Styl.RED if i == sel[0] else INK, HORIZONTAL_ALIGNMENT_CENTER, row.size.x)
		_rects.append([row, "row", [0, i]])
		y += 68 * u
	_badge(Vector2(r.position.x + 80 * u, r.end.y - 40 * u), "A", u)
	_txt(_fm, "Spát", Vector2(r.position.x + 102 * u, r.end.y - 31 * u), 26 * u, INK)
	_badge(Vector2(r.end.x - 170 * u, r.end.y - 40 * u), "B", u)
	_txt(_fm, "Vstát", Vector2(r.end.x - 148 * u, r.end.y - 31 * u), 26 * u, INK)
	_rects.append([Rect2(r.end.x - 190 * u, r.end.y - 70 * u, 150 * u, 50 * u), "close", 0])


func _list(r: Rect2, s: int, title: String, u: float) -> void:
	Styl.kresli_list(_c, r.grow(14 * u), 0.55 * u)
	var items := _items(s)
	var x0 := r.position.x + 50 * u
	var colw := r.end.x - 230 * u
	_txt(_fb, title, Vector2(x0, r.position.y + 62 * u), 40 * u, INK)
	if page == "dovednosti":
		_txt(_fm, "úroveň", Vector2(colw, r.position.y + 60 * u), 22 * u, Color(0.42, 0.3, 0.18))
	elif page != "staveni" and page != "denik":
		_txt(_fm, "váha", Vector2(colw, r.position.y + 60 * u), 22 * u, Color(0.42, 0.3, 0.18))
		_txt(_fm, "cena", Vector2(colw + 100 * u, r.position.y + 60 * u), 22 * u, Color(0.42, 0.3, 0.18))
	var rh := (r.size.y - 170 * u) / ROWS
	var y := r.position.y + 88 * u
	if items.is_empty():
		_txt(_fm, "Nic tu není", Vector2(x0, y + 50 * u), 30 * u, Color(0.42, 0.3, 0.18))
	for i in range(scroll[s], mini(items.size(), scroll[s] + ROWS)):
		var id: String = items[i]
		var row := Rect2(r.position.x + 22 * u, y, r.size.x - 44 * u, rh - 6 * u)
		var hot: bool = i == int(sel[s]) and s == side
		if hot:
			Styl.kresli_vyber(_c, row, 0.7 * u)
		elif i == sel[s]:
			Styl.kresli_vyber(_c, row, 0.7 * u, true)
		else:
			_c.draw_line(Vector2(row.position.x + 40 * u, row.end.y + 3 * u), Vector2(row.end.x - 40 * u, row.end.y + 3 * u), Color(0.5, 0.36, 0.2, 0.35), 1.0)
		var ic: Texture2D = null if _dv_stranka() else P.icon(id)
		var isz := rh - 10 * u
		if _dv_stranka():
			_list_dv(row, id, colw, rh, hot, u)
			_rects.append([row, "row", [s, i]])
			y += rh
			continue
		if ic:
			_c.draw_texture_rect(ic, Rect2(row.position + Vector2(10 * u, 2 * u), Vector2(isz, isz)), false)
		var n := _count(s, id)
		var nm: String = P.name_of(id) + ("  ×%d" % n if n > 1 else "")
		if page == "staveni" and _polozene() and i < _prec.size():
			nm += "  · %d m" % int(round((main.player.global_position as Vector3).distance_to(_prec[i]["p"])))
		_txt(_fm, nm, Vector2(row.position.x + isz + 30 * u, row.position.y + rh * 0.62), 32 * u, Styl.RED if hot else INK)
		if page != "staveni":
			var info: Dictionary = P.kat.get(id, {})
			_txt(_fm, "%.1f" % float(info.get("vaha", 0)), Vector2(colw, row.position.y + rh * 0.62), 28 * u, INK)
			_txt(_fm, str(int(info.get("cena", 0))), Vector2(colw + 100 * u, row.position.y + rh * 0.62), 28 * u, INK)
		_rects.append([row, "row", [s, i]])
		y += rh
	if items.size() > ROWS:
		_txt(_fm, "%d–%d z %d" % [scroll[s] + 1, mini(items.size(), scroll[s] + ROWS), items.size()],
				Vector2(r.end.x - 360 * u, r.position.y + 60 * u), 22 * u, Color(0.42, 0.3, 0.18))
	# spodni radek: nosnost / misto
	var by := r.end.y - 38 * u
	var w: float = P.weight(P.inv if s == 0 else box.get("obsah", {}))
	if page != "staveni" and not _dv_stranka():
		var cap := 70.0 if s == 0 else float(P.kat[box["id"]].get("kont", 0))
		_txt(_fm, ("Nosnost %.1f / %d" if s == 0 else "Místo %.1f / %d") % [w, int(cap)], Vector2(x0, by), 26 * u, INK)
		var br := Rect2(x0 + 230 * u, by - 18 * u, r.size.x * 0.32, 14 * u)
		# nosnost: inkoustova linka a vyplnena cast tahem pera
		_c.draw_line(Vector2(br.position.x, br.end.y), br.end, Color(0.42, 0.3, 0.18, 0.7), 1.5, true)
		_c.draw_line(Vector2(br.position.x, br.get_center().y), Vector2(br.position.x + br.size.x * clampf(w / maxf(cap, 1.0), 0, 1), br.get_center().y),
				Styl.RED if w > cap else Styl.INK_SOFT, br.size.y * 0.6, true)
	# tlacitka (u vymeny jsou v dolnim pruhu)
	if s == side and page != "vymena":
		var acts := []
		match page:
			"staveni":
				if _polozene():
					if not items.is_empty():
						acts = [["A", "Přesunout", "act"], ["X", "Odstranit", "all"]]
				else:
					acts = [["A", "Postavit", "act"]]
			"brasna":
				if P.held_id != "":
					acts.append(["Y", "Schovat", "stash"])
				if P.SVETLA.has(_selected()):
					acts.append(["A", "Do ruky", "act"])
				elif main.mode == "piskoviste" and _selected() != "":
					acts.append(["A", "Položit", "act"])
			"vymena":
				acts = [["A", "Přesunout", "act"], ["X", "Vzít vše", "all"]]
			"dovednosti", "denik":
				_txt(_fm, "LT · RT stránky, LB · RB vlohy" if page == "dovednosti" else "LT · RT stránky", Vector2(x0, by), 24 * u, Styl.INK_SOFT)
		acts.append(["B", "Zavřít", "close"])
		var bx := r.end.x - 40 * u - acts.size() * 165 * u
		for a: Array in acts:
			_badge(Vector2(bx + 16 * u, by - 9 * u), a[0], u)
			_txt(_fm, a[1], Vector2(bx + 38 * u, by), 26 * u, INK)
			_rects.append([Rect2(bx - 6 * u, by - 34 * u, 160 * u, 48 * u), a[2], 0])
			bx += 165 * u


func _badge(c: Vector2, b: String, u: float) -> void:
	var col: Color = {"A": Color(0.25, 0.65, 0.2), "B": Color(0.8, 0.18, 0.12), "X": Color(0.2, 0.4, 0.85), "Y": Color(0.85, 0.65, 0.1)}[b]
	_c.draw_circle(c, 15 * u, Color(0.08, 0.07, 0.06))
	_c.draw_arc(c, 15 * u, 0, TAU, 24, col, 2.0 * u, true)
	var f := ThemeDB.fallback_font
	var fs := int(17 * u)
	var w := f.get_string_size(b, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	_c.draw_string(f, c + Vector2(-w / 2, fs * 0.36), b, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)


func _detail(r: Rect2, u: float) -> void:
	Styl.kresli_list(_c, r.grow(14 * u), 0.55 * u)
	var id := _selected()
	if id == "":
		return
	var info: Dictionary = P.kat.get(id, {})
	var x0 := r.position.x + 36 * u
	_txt(_fb, P.name_of(id), Vector2(x0, r.position.y + 70 * u), 42 * u, INK)
	var kk = info.get("kat", null)
	var sub := "Vybavení"
	for k: Array in KAT_B:
		if kk != null and k[0] == kk:
			sub = k[1]
	_txt(_fm, sub, Vector2(x0, r.position.y + 106 * u), 24 * u, Styl.INK_SOFT)
	Styl.kresli_linku(_c, Vector2(r.get_center().x, r.position.y + 124 * u), r.size.x * 0.7, u)
	var c := Vector2(r.get_center().x, r.position.y + 330 * u)
	var ic: Texture2D = P.icon(id)
	if ic:
		_c.draw_texture_rect(ic, Rect2(c - Vector2(190, 190) * u, Vector2(380, 380) * u), false)
	var y := r.position.y + 590 * u
	var lines := []
	var rz: Array = info.get("rozmer", [0, 0, 0])
	lines.append(["Váha", "%.1f kg" % float(info.get("vaha", 0))])
	lines.append(["Cena", "%d grošů" % int(info.get("cena", 0))])
	lines.append(["Rozměr", "%.1f × %.1f × %.1f m" % [float(rz[0]), float(rz[2]), float(rz[1])]])
	if info.has("kont"):
		lines.append(["Úložiště", "%d kg" % int(info["kont"])])
	if info.get("sed", false):
		lines.append(["", "Dá se na to sednout"])
	if info.get("lehat", false):
		lines.append(["", "Dá se na tom spát"])
	for l: Array in lines:
		_txt(_fm, l[0], Vector2(x0, y), 26 * u, Styl.INK_SOFT)
		_txt(_fm, l[1], Vector2(x0 + 150 * u, y), 26 * u, INK)
		y += 38 * u


func _detail_line(r: Rect2, u: float) -> void:
	Styl.kresli_pruh(_c, r.grow(8 * u), 0.8 * u)
	var id := _selected()
	var info: Dictionary = P.kat.get(id, {})
	if id != "":
		_txt(_fb, P.name_of(id), Vector2(r.position.x + 40 * u, r.position.y + 56 * u), 36 * u, INK)
		_txt(_fm, "váha %.1f kg · cena %d grošů" % [float(info.get("vaha", 0)), int(info.get("cena", 0))],
				Vector2(r.position.x + 420 * u, r.position.y + 54 * u), 26 * u, Styl.INK_SOFT)
	var bx := r.end.x - 3 * 175 * u - 20 * u
	var by := r.position.y + 54 * u
	for a: Array in [["A", "Přesunout" if side == 0 else "Vzít", "act"], ["X", "Vzít vše", "all"], ["B", "Zavřít", "close"]]:
		_badge(Vector2(bx + 16 * u, by - 9 * u), a[0], u)
		_txt(_fm, a[1], Vector2(bx + 38 * u, by), 26 * u, INK)
		_rects.append([Rect2(bx - 6 * u, by - 34 * u, 170 * u, 48 * u), a[2], 0])
		bx += 175 * u


# ------------------------------------------------------------------ dovednosti a denik

func _list_dv(row: Rect2, id: String, colw: float, rh: float, hot: bool, u: float) -> void:
	var dv: Node = main.dovednosti
	var vloha: bool = page == "dovednosti" and (Dov.D["vlohy"] as Dictionary).has(id)
	var odsaz := 20.0 * u if vloha else 50.0 * u        # vlohy vlevo, umy pod nimi
	var nm := _dv_nazev(id)
	var f := _fb if vloha else _fm
	var col: Color = Styl.RED if hot else INK
	if page == "denik" and KAT_J[tab][0] == "zvyky" and not dv.zvyky.has(id):
		col = Styl.INK_SOFT
	_txt(f, nm, Vector2(row.position.x + odsaz, row.position.y + rh * 0.62), (34 if vloha else 32) * u, col)
	_txt(_fm, _dv_hodnota(id), Vector2(colw, row.position.y + rh * 0.62), 30 * u, INK)
	if page == "dovednosti":
		_bar(Rect2(colw + 60 * u, row.position.y + rh * 0.42, 100 * u, 10 * u), _postup(id), u)


func _postup(id: String) -> float:
	var dv: Node = main.dovednosti
	var n: int = dv.uroven_of(id)
	if n >= int(Dov.D["strop"]):
		return 1.0
	return clampf(float(dv.xp.get(id, 0.0)) / maxf(1.0, dv.potreba(id, n)), 0.0, 1.0)


func _bar(br: Rect2, f: float, u: float) -> void:
	# inkoustova linka a vyplnena cast tahem pera (jako nosnost)
	_c.draw_line(Vector2(br.position.x, br.end.y), br.end, Color(0.42, 0.3, 0.18, 0.7), 1.5, true)
	if f > 0.0:
		_c.draw_line(Vector2(br.position.x, br.get_center().y), Vector2(br.position.x + br.size.x * f, br.get_center().y), Styl.INK_SOFT, br.size.y * 0.6, true)


func _odstavec(t: String, p: Vector2, w: float, fs: float, col: Color, radku := 4) -> float:
	_c.draw_multiline_string(_fm, p, t, HORIZONTAL_ALIGNMENT_LEFT, w, int(fs), radku, col)
	var h := _fm.get_multiline_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, w, int(fs), radku).y
	return p.y + h


func _dv_detail(r: Rect2, u: float) -> void:
	Styl.kresli_list(_c, r.grow(14 * u), 0.55 * u)
	var dv: Node = main.dovednosti
	var D: Dictionary = Dov.D
	var x0 := r.position.x + 36 * u
	var tw := r.size.x - 72 * u
	var id := _selected()
	if id == "":
		_txt(_fm, "Zatím nic" if page == "denik" else "", Vector2(x0, r.position.y + 70 * u), 30 * u, Styl.INK_SOFT)
		return
	_odstavec(_dv_nazev(id), Vector2(x0, r.position.y + 70 * u), tw, 40 * u, INK, 2)
	var y := r.position.y + 150 * u
	if page == "dovednosti":
		var vloha: bool = (D["vlohy"] as Dictionary).has(id)
		var e: Dictionary = D["vlohy"][id] if vloha else D["umy"][id]
		_txt(_fm, "Vloha" if vloha else "Um · vloha %s" % dv.nazev_of(String(e["vloha"])), Vector2(x0, r.position.y + 112 * u), 24 * u, Styl.INK_SOFT)
		Styl.kresli_linku(_c, Vector2(r.get_center().x, r.position.y + 130 * u), r.size.x * 0.7, u)
		y = _odstavec(String(e.get("popis", "")), Vector2(x0, y + 20 * u), tw, 28 * u, INK) + 30 * u
		var n: int = dv.uroven_of(id)
		var strop := int(D["strop"])
		_txt(_fb, "Úroveň %d / %d" % [n, strop], Vector2(x0, y), 34 * u, INK)
		y += 34 * u
		_bar(Rect2(x0, y, tw, 16 * u), _postup(id), u)
		y += 44 * u
		if n < strop:
			_txt(_fm, "do další úrovně %d / %d" % [int(dv.xp.get(id, 0.0)), int(dv.potreba(id, n))], Vector2(x0, y), 24 * u, Styl.INK_SOFT)
			y += 46 * u
		if vloha:
			# co vloha dela (vloha_ucinky) a ktere umy uci
			for uc: Dictionary in (D["vloha_ucinky"] as Dictionary).get(id, []):
				var cil := String(uc["cil"])
				var hod: float = dv.ucinek(cil, 0.0) if uc.has("zaklad") or uc.has("plus_za_uroven") else 0.0
				var txt: String = {"vydrz_max": "Výdrž +%d", "nosnost_kg": "Nosnost %d kg"}.get(cil, "")
				if txt != "":
					_txt(_fm, txt % int(round(hod)), Vector2(x0, y), 26 * u, INK)
					y += 36 * u
			var um: Array = []
			for u2: String in D["umy"]:
				if String(D["umy"][u2]["vloha"]) == id:
					um.append(dv.nazev_of(u2))
			_odstavec("Učí ji: " + ", ".join(um), Vector2(x0, y + 10 * u), tw, 24 * u, Styl.INK_SOFT, 5)
		else:
			_txt(_fb, "Zvyky", Vector2(x0, y), 30 * u, INK)
			y += 40 * u
			var nic := true
			for z: String in D["zvyky"]["seznam"]:
				var ze: Dictionary = D["zvyky"]["seznam"][z]
				if String(ze["um"]) != id:
					continue
				nic = false
				var ma: bool = dv.zvyky.has(z)
				_txt(_fm, String(ze["nazev"]) + ("" if ma else "  (od úrovně %d)" % int(ze["podminka"]["um_od"])),
						Vector2(x0, y), 26 * u, INK if ma else Styl.INK_SOFT)
				y += 36 * u
			if nic:
				_txt(_fm, "Žádné", Vector2(x0, y), 26 * u, Styl.INK_SOFT)
	elif KAT_J[tab][0] == "skutky":
		_txt(_fm, "Skutek", Vector2(x0, r.position.y + 112 * u), 24 * u, Styl.INK_SOFT)
		Styl.kresli_linku(_c, Vector2(r.get_center().x, r.position.y + 130 * u), r.size.x * 0.7, u)
		_txt(_fb, _dv_hodnota(id), Vector2(x0, y + 40 * u), 44 * u, INK)
		var uci: Array = []
		for u2: String in D["umy"]:
			if (D["umy"][u2]["xp_za"] as Dictionary).has(id):
				uci.append(dv.nazev_of(u2))
		if not uci.is_empty():
			_odstavec("Učí: " + ", ".join(uci), Vector2(x0, y + 110 * u), tw, 26 * u, Styl.INK_SOFT)
	else:
		var ze: Dictionary = D["zvyky"]["seznam"][id]
		var ma: bool = dv.zvyky.has(id)
		_txt(_fm, "Zvyk · %s" % dv.nazev_of(String(ze["um"])), Vector2(x0, r.position.y + 112 * u), 24 * u, Styl.INK_SOFT)
		Styl.kresli_linku(_c, Vector2(r.get_center().x, r.position.y + 130 * u), r.size.x * 0.7, u)
		_txt(_fb, "Odemčen" if ma else "Zatím ne", Vector2(x0, y + 30 * u), 34 * u, INK if ma else Styl.INK_SOFT)
		var p: Dictionary = ze["podminka"]
		var sk: Array = (D.get("skutky", {}) as Dictionary).get(String(p["skutek"]), [String(p["skutek"])])
		_odstavec("Podmínka: %s aspoň %d, skutek „%s“ %d× (zatím %d×)" % [dv.nazev_of(String(ze["um"])), int(p["um_od"]), String(sk[0]),
				int(p["pocet"]), int(dv.skutky.get(String(p["skutek"]), 0))], Vector2(x0, y + 80 * u), tw, 26 * u, INK, 6)
