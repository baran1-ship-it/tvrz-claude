extends CanvasLayer
const Pravidla := preload("res://scripts/pravidla.gd")
## Mapa kraje (kriz nahoru nebo ikona mapy): pergamenova mapa z tools/gen_mapa.py (nazvy mist jsou v obraze),
## poloha a smer hrace,
## erby mist pro rychle cestovani (Tvrz, Lhota). Vyber erbu (dotyk, nebo kriz/packa + A) se zepta,
## zda cestovat; cesta ubehne herni cas podle vzdalenosti. B / kriz nahoru / Start zavre.

const GOLD := Color(0.89, 0.73, 0.41)
const INK := Color(0.2, 0.12, 0.06)
# rozsah mapy = hranice pruchodu (pravidla/svet/svet.json; obraz z tools/gen_mapa.py ma stejny rozsah)
static var X0: float = Pravidla.cti("svet", "hranice_pruchod")["x0"]
static var X1: float = Pravidla.cti("svet", "hranice_pruchod")["x1"]
static var Z0: float = Pravidla.cti("svet", "hranice_pruchod")["z0"]
static var Z1: float = Pravidla.cti("svet", "hranice_pruchod")["z1"]
static var MISTA: Array = [
	{"id": "tvrz", "nazev": "Tvrz Havran", "erb": "venku", "p": Vector2(0.0, 0.0),
		"cil": Vector3(2.5, 0.0, 40.0), "pohled": Vector3(0.0, 4.5, 15.0)},
	{"id": "ves", "nazev": "Lhota", "erb": "jidlo", "p": Vector2(470.0, 830.0),
		"cil": Vector3(413.0, 0.0, 781.0), "pohled": Vector3(470.0, 3.0, 830.0)},
	# krok B: hostinec z lokace.json, prichod ze zacatku odbocky k nemu (cesty.json k_hostinci)
	{"id": "hostinec", "nazev": "Zájezdní hostinec", "erb": "piti", "p": _stavba("hostinec"),
		"cil": _odbocka("k_hostinci"), "pohled": Vector3(_stavba("hostinec").x, 3.0, _stavba("hostinec").y)},
	# Misa 24. 10. "dej lom do mapy a rychle cestovani": prichod z louky na kraji lomu, pohled ke stene s lesenim
	{"id": "lom", "nazev": "Lom", "erb": "naradi", "p": Vector2(138.0, 940.0),
		"cil": Vector3(150.0, 0.0, 938.0), "pohled": Vector3(127.0, 4.0, 935.0)},
	# ruiny: v pribehu az po objeveni (dojit k nim), v piskovisti hned
	{"id": "kostel", "nazev": "Kostelík sv. Jiljí", "erb": "ostatni", "p": Vector2(220.0, 40.0), "ruina": true,
		"cil": Vector3(210.1, 0.0, 46.8), "pohled": Vector3(220.0, 2.5, 40.0)},
	{"id": "zanikla_ves", "nazev": "Doubrava", "erb": "ostatni", "p": Vector2(300.0, 340.0), "ruina": true,
		"cil": Vector3(277.1, 0.0, 332.9), "pohled": Vector3(300.0, 2.0, 340.0)},
	{"id": "hradek", "nazev": "Pustá skála", "erb": "zbrojnice", "p": Vector2(-190.0, 540.0), "ruina": true,
		"cil": Vector3(-197.2, 0.0, 558.6), "pohled": Vector3(-190.0, 4.0, 540.0)},
]
const OBJEV_R := 40.0          # jak blizko je treba prijit, aby se ruina objevila

var main: Node
var open := false
var sel := 0
var asking := false            # dotaz "Rychle cestovat?"
var ano := true                # vybrana odpoved v dotazu
var _c: Control
var _tex: Texture2D
var _erby := {}
var _fb: Font
var _fm: Font
var _rects: Array = []         # [Rect2, akce, arg]
var _opened_ms := 0
var _stick := false
var _cur := Vector2(-1, -1)     # kurzor na mape (ovladac: leva packa, mys)
var _hover := -1               # misto pod kurzorem
var _objev_t := 0.0
# rychle cestovani jako KCD (Misa 14. 11., prevzato od Pucharta 771eae78): figurka jede po mape po cestach (sit chuze
# postav lide._g), cas ubiha podle chuze nebo jizdy (kun pozna sam), jde zastavit klepnutim na figurku / Zastavit
var _fig := {}                  # "kun" / "pesky" -> Texture2D (game-icons.net CC BY 3.0, obarveno u Pucharta)
var _jizda := {}                # bezici cesta: body, kum, L, s, rychlost_m_s (mapa), kun, km_h, cil, pohled, nazev, hod0


static func _stavba(id: String) -> Vector2:
	for e: Dictionary in Pravidla.cti("lokace", "stavby"):
		if e["id"] == id:
			return Vector2(float(e["stred"][0]), float(e["stred"][1]))
	return Vector2.ZERO


static func _odbocka(id: String) -> Vector3:
	for c: Dictionary in Pravidla.cti("cesty", "vozove"):
		if c["id"] == id:
			return Vector3(float(c["osa"][0][0]), 0.0, float(c["osa"][0][1]))
	return Vector3.ZERO


func _ready() -> void:
	layer = 19
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	_tex = load("res://obrazky/mapa.png") if ResourceLoader.exists("res://obrazky/mapa.png") else null
	_fb = load("res://fonts/GrenzeGotisch-Bold.ttf")
	_fm = load("res://fonts/GrenzeGotisch-Medium.ttf")
	for m: Dictionary in MISTA:
		_erby[m["erb"]] = load("res://obrazky/erby/%s.png" % m["erb"])
	for k in ["kun", "pesky"]:
		if ResourceLoader.exists("res://obrazky/figurka_%s.png" % k):
			_fig[k] = load("res://obrazky/figurka_%s.png" % k)
	_c = Control.new()
	_c.set_anchors_preset(Control.PRESET_FULL_RECT)
	_c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_c.draw.connect(_draw_all)
	add_child(_c)


## Mista, ktera jsou na mape: v piskovisti vsechna, v pribehu ruiny az po objeveni.
func _visible(i: int) -> bool:
	var m: Dictionary = MISTA[i]
	if not bool(m.get("ruina", false)) or main.mode == "piskoviste":
		return true
	return main.objevena.has(String(m["id"]))


## Diag (radce 20:00): cas _process meri obal, poradi behu hry se nemeni (drive diag _process prebiral).
func _process(delta: float) -> void:
	var t_us := Time.get_ticks_usec()
	_process_vlastni(delta)
	var dg: Object = Engine.get_meta("diag", null)
	if dg:
		dg.cas("mapa", Time.get_ticks_usec() - t_us)


func _process_vlastni(delta: float) -> void:
	if main == null or main.player == null:
		return
	if open and not _jizda.is_empty():
		_jizda["s"] = minf(float(_jizda["s"]) + float(_jizda["rychlost_m_s"]) * delta, float(_jizda["L"]))
		_c.queue_redraw()
		if float(_jizda["s"]) >= float(_jizda["L"]):
			_dorazit(true)
		return
	# objevovani ruin chuzi (kontrola jednou za sekundu, i kdyz je mapa zavrena)
	_objev_t -= delta
	if _objev_t <= 0.0 and not open:
		_objev_t = 1.0
		var pp: Vector3 = main.player.global_position
		for m: Dictionary in MISTA:
			if bool(m.get("ruina", false)) and not main.objevena.has(String(m["id"])) \
					and Vector2(pp.x, pp.z).distance_to(m["p"]) < OBJEV_R:
				main.objevena.append(String(m["id"]))
				if main.mode != "piskoviste":
					main.hud.toast("Objeveno místo: %s" % m["nazev"], 3.0)
	if not open or asking:
		return
	# kurzor: leva packa ovladace
	var v := Vector2(Input.get_joy_axis(0, JOY_AXIS_LEFT_X), Input.get_joy_axis(0, JOY_AXIS_LEFT_Y))
	if v.length() > 0.2:
		var s := _c.get_viewport_rect().size
		_cur = (_cur + v * v.length() * 900.0 * delta).clamp(Vector2.ZERO, s)
		_update_hover()
		_c.queue_redraw()


func _update_hover() -> void:
	var r := _map_rect()
	var best := -1
	var bd := 70.0 * clampf(r.size.y / 900.0, 0.6, 1.6)
	for i in MISTA.size():
		if not _visible(i):
			continue
		var c := _to_screen(r, MISTA[i]["p"].x, MISTA[i]["p"].y) - Vector2(0, 34.0 * clampf(r.size.y / 900.0, 0.6, 1.6))
		var d := c.distance_to(_cur)
		if d < bd:
			bd = d
			best = i
	_hover = best
	if best >= 0:
		sel = best


func _cursor_to(i: int) -> void:
	var r := _map_rect()
	_cur = _to_screen(r, MISTA[i]["p"].x, MISTA[i]["p"].y) - Vector2(0, 34.0 * clampf(r.size.y / 900.0, 0.6, 1.6))
	_hover = i


func _next(step: int) -> void:
	for k in MISTA.size():
		sel = (sel + step + MISTA.size()) % MISTA.size()
		if _visible(sel):
			break
	_cursor_to(sel)


func show_map() -> void:
	if open or _tex == null:
		return
	open = true
	asking = false
	visible = true
	_opened_ms = Time.get_ticks_msec()
	# vybrane je misto, kde hrac neni (kam se nejspis chce dostat)
	sel = 1 if _here() == 0 else 0
	_cursor_to(sel)
	main.hud.visible = false
	get_tree().paused = true
	main.life.sfx("menu_otevrit", -6.0)
	_c.queue_redraw()


func close() -> void:
	if not open:
		return
	_jizda = {}
	open = false
	visible = false
	main.hud.visible = true
	get_tree().paused = false


func _here() -> int:
	var pp: Vector3 = main.player.global_position
	var best := 0
	var bd := 1e9
	for i in MISTA.size():
		var d := Vector2(pp.x, pp.z).distance_to(MISTA[i]["p"])
		if d < bd:
			bd = d
			best = i
	return best


# ------------------------------------------------------------------ kresleni

func _map_rect() -> Rect2:
	var s := _c.get_viewport_rect().size
	var ts := _tex.get_size()
	var k := minf((s.x - 40.0) / ts.x, (s.y - 40.0) / ts.y)
	var sz := ts * k
	return Rect2((s - sz) * 0.5, sz)


func _to_screen(r: Rect2, x: float, z: float) -> Vector2:
	return r.position + Vector2((x - X0) / (X1 - X0) * r.size.x, (z - Z0) / (Z1 - Z0) * r.size.y)


func _draw_all() -> void:
	_rects.clear()
	var s := _c.get_viewport_rect().size
	_c.draw_rect(Rect2(Vector2.ZERO, s), Color(0.04, 0.03, 0.02, 0.92))
	var r := _map_rect()
	_c.draw_texture_rect(_tex, r, false)
	var u := clampf(r.size.y / 900.0, 0.6, 1.6)
	# mista: erb a nazev
	for i in MISTA.size():
		if not _visible(i):
			continue
		var m: Dictionary = MISTA[i]
		var c := _to_screen(r, m["p"].x, m["p"].y)
		var es := 58.0 * u * (1.18 if i == sel else 1.0)
		var er := Rect2(c - Vector2(es * 0.5, es * 1.1), Vector2(es, es))
		if i == sel:
			_c.draw_circle(er.get_center(), es * 0.7, Color(1.0, 0.85, 0.45, 0.45))
		_c.draw_texture_rect(_erby[m["erb"]], er, false)
		_rects.append([er.grow(12), "misto", i])
	if not _jizda.is_empty():
		_draw_jizda(r, u, s)
		return
	# hrac: sipka ve smeru pohledu
	var pp: Vector3 = main.player.global_position
	var pc := _to_screen(r, pp.x, pp.z)
	var yaw: float = main.player.yaw
	var fwd := Vector2(-sin(yaw), -cos(yaw))
	var side := Vector2(-fwd.y, fwd.x)
	var a := 16.0 * u
	var pts := PackedVector2Array([pc + fwd * a, pc - fwd * a * 0.6 + side * a * 0.65, pc - fwd * a * 0.25, pc - fwd * a * 0.6 - side * a * 0.65])
	_c.draw_colored_polygon(pts, Color(0.7, 0.08, 0.05))
	_c.draw_polyline(pts + PackedVector2Array([pts[0]]), Color(0.15, 0.05, 0.02), 2.0, true)
	# kurzor (kruh se zamerovacem) a nazev mista pod nim
	if _cur.x >= 0.0 and not asking:
		var cc := Color(0.95, 0.85, 0.55, 0.95)
		_c.draw_arc(_cur, 14.0 * u, 0.0, TAU, 28, Color(0, 0, 0, 0.6), 5.0)
		_c.draw_arc(_cur, 14.0 * u, 0.0, TAU, 28, cc, 2.5)
		for dv: Vector2 in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
			_c.draw_line(_cur + dv * 8.0 * u, _cur + dv * 22.0 * u, cc, 2.5)
		if _hover >= 0:
			_text(_cur + Vector2(0, -40.0 * u), String(MISTA[_hover]["nazev"]), int(28 * u), INK, Color(1, 1, 1, 1), _fb)
	# napoveda dole
	var hint := "Klepni na místo nebo najeď kurzorem (levá páčka) a potvrď A  ·  B zavřít"
	_text(Vector2(s.x * 0.5, s.y - 12), hint, int(20 * u), INK, Color(1, 1, 1, 0.92))
	# zavrit (dotyk): vosková pečeť
	var cr := Rect2(Vector2(s.x - 86, 18), Vector2(68, 60))
	Styl.kresli_pecet(_c, cr.get_center(), 27.0)
	_rects.append([cr, "zavrit", 0])
	if asking:
		_draw_ask(s, u)


## Jizda po mape: ujeta cast trasy plnou carou, zbytek carkovane, figurka (zrcadli se podle smeru), hodina dne, Zastavit.
func _draw_jizda(r: Rect2, u: float, s: Vector2) -> void:
	var b: PackedVector2Array = _jizda["body"]
	var kum: PackedFloat32Array = _jizda["kum"]
	var sj: float = _jizda["s"]
	var poz := _bod_trasy(sj)
	var hotovo := PackedVector2Array()
	var zbyva := PackedVector2Array()
	for i in b.size():
		if kum[i] <= sj:
			hotovo.append(_to_screen(r, b[i].x, b[i].y))
		else:
			zbyva.append(_to_screen(r, b[i].x, b[i].y))
	var ps := _to_screen(r, poz.x, poz.y)
	hotovo.append(ps)
	zbyva.insert(0, ps)
	if hotovo.size() > 1:
		_c.draw_polyline(hotovo, Color(0.45, 0.08, 0.05, 0.85), 4.0 * u, true)
	for i in zbyva.size() - 1:
		_c.draw_dashed_line(zbyva[i], zbyva[i + 1], Color(0.2, 0.12, 0.06, 0.9), 3.0 * u, 10.0 * u, false)
	var cf: Dictionary = Pravidla.cti("jizda", "rychle_cestovani")
	var t: Texture2D = _fig.get("kun" if bool(_jizda["kun"]) else "pesky")
	var fs := float(cf["figurka_px"]) * u * 1.6
	var dalsi := _bod_trasy(minf(sj + 15.0, float(_jizda["L"])))
	var vlevo := dalsi.x < poz.x - 0.01
	var fr := Rect2(ps - Vector2(fs * 0.5, fs * 0.86), Vector2(fs, fs))
	if t:
		_c.draw_texture_rect(t, Rect2(fr.position + (Vector2(fs, 0) if vlevo else Vector2.ZERO), Vector2(-fs if vlevo else fs, fs)), false)
	else:
		_c.draw_circle(ps, 10.0 * u, Color(0.7, 0.08, 0.05))
	_rects.append([fr.grow(10), "zastavit", 0])
	var hod := fposmod(float(_jizda["hod0"]) + sj / 1000.0 / float(_jizda["km_h"]), 24.0)
	var min_ := int(round(sj / 1000.0 / float(_jizda["km_h"]) * 60.0))
	_text(Vector2(s.x * 0.5, 64 * u), "%s  ·  %02d:%02d  ·  %d min %s" % [String(_jizda["nazev"]), int(hod), int(fmod(hod, 1.0) * 60.0), min_,
			"jízdy" if bool(_jizda["kun"]) else "chůze"], int(28 * u), INK, Color(1, 1, 1, 0.92), _fb)
	var br := Rect2(Vector2(s.x * 0.5 - 130 * u, s.y - 96 * u), Vector2(260 * u, 64 * u))
	Styl.kresli_tlacitko(_c, br, 0, true, br.size.y / 76.0)
	_text(br.get_center() + Vector2(0, 12 * u), "Zastavit", int(34 * u), Styl.RED, Color(0, 0, 0, 0), _fb)
	_rects.append([br, "zastavit", 0])


func _draw_ask(s: Vector2, u: float) -> void:
	_rects.clear()
	var m: Dictionary = MISTA[sel]
	var w := 660.0 * u
	var h := 300.0 * u
	var box := Rect2((s - Vector2(w, h)) * 0.5, Vector2(w, h))
	Styl.kresli_list(_c, box, 0.45 * u)
	_text(box.position + Vector2(w * 0.5, 86 * u), "Rychlé cestování", int(40 * u), INK, Color(0, 0, 0, 0), _fb)
	Styl.kresli_linku(_c, box.position + Vector2(w * 0.5, 104 * u), w * 0.5, u)
	var km := _dist_km()
	var kun := na_koni()
	_text(box.position + Vector2(w * 0.5, 150 * u), "do: %s  (asi %d minut %s)" % [m["nazev"], int(round(km / _km_h(kun) * 60.0)), "jízdy" if kun else "chůze"],
			int(26 * u), INK, Color(0, 0, 0, 0))
	for k in 2:
		var br := Rect2(box.position + Vector2(w * (0.12 + 0.44 * k), h - 108 * u), Vector2(w * 0.32, 60 * u))
		var on := (k == 0) == ano
		Styl.kresli_tlacitko(_c, br, k, on, br.size.y / 76.0)
		_text(br.get_center() + Vector2(0, 11 * u), "Ano" if k == 0 else "Ne", int(34 * u), Styl.RED if on else INK, Color(0, 0, 0, 0), _fb)
		_rects.append([br, "odpoved", k == 0])


## Text na stredu p; bg.a > 0 -> pod nim pruh pergamenu (pruhlednost podle bg.a).
func _text(p: Vector2, t: String, size: int, col: Color, bg: Color, f: Font = null) -> void:
	if f == null:
		f = _fm
	var w := f.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	if bg.a > 0.0:
		var pr := Rect2(p.x - w * 0.5 - size * 1.4, p.y - size * 1.25, w + size * 2.8, size * 1.9)
		Styl.kresli_pruh(_c, pr, pr.size.y / 150.0, bg.a)
	_c.draw_string(f, p - Vector2(w * 0.5, 0), t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


# ------------------------------------------------------------------ ovladani

func _input(event: InputEvent) -> void:
	if not open:
		return
	if not _jizda.is_empty():
		# behem jizdy: klepnuti na figurku nebo Zastavit, A/B, Esc/mezernik = zastavit
		var stop := false
		if (event is InputEventScreenTouch and event.pressed) or (event is InputEventMouseButton and event.pressed):
			for rr: Array in _rects:
				if String(rr[1]) == "zastavit" and (rr[0] as Rect2).has_point(event.position):
					stop = true
		elif event is InputEventJoypadButton and event.pressed and (event as InputEventJoypadButton).button_index in [JOY_BUTTON_A, JOY_BUTTON_B]:
			stop = true
		elif event is InputEventKey and event.pressed and not event.echo and (event as InputEventKey).keycode in [KEY_ESCAPE, KEY_SPACE]:
			stop = true
		if event is InputEventScreenTouch or event is InputEventMouseButton or event is InputEventJoypadButton or event is InputEventKey:
			get_viewport().set_input_as_handled()
		if stop:
			_dorazit(false)
		return
	if event is InputEventJoypadButton and event.pressed:
		get_viewport().set_input_as_handled()
		if Time.get_ticks_msec() - _opened_ms < 250:
			return
		var b := (event as InputEventJoypadButton).button_index
		if asking:
			match b:
				JOY_BUTTON_A:
					_answer(ano)
				JOY_BUTTON_B:
					_answer(false)
				JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_RIGHT:
					ano = not ano
					main.life.sfx("menu_vyber", -10.0)
			_c.queue_redraw()
			return
		match b:
			JOY_BUTTON_B, JOY_BUTTON_START, JOY_BUTTON_DPAD_UP:
				close()
			JOY_BUTTON_A:
				if _hover >= 0:
					sel = _hover
					_ask()
			JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_RIGHT_SHOULDER:
				_next(1)
				main.life.sfx("menu_vyber", -10.0)
			JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_LEFT_SHOULDER:
				_next(-1)
				main.life.sfx("menu_vyber", -10.0)
		_c.queue_redraw()
	elif event is InputEventJoypadMotion:
		# packa: v dotazu Ano/Ne, jinak kurzor (_process)
		var v := Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
		if asking and absf(v) > 0.6 and not _stick:
			_stick = true
			ano = not ano
			_c.queue_redraw()
		elif absf(v) < 0.3:
			_stick = false
	elif event is InputEventMouseMotion and not asking:
		_cur = (event as InputEventMouseMotion).position
		_update_hover()
		_c.queue_redraw()
	elif (event is InputEventScreenTouch and event.pressed) or (event is InputEventMouseButton and event.pressed):
		get_viewport().set_input_as_handled()
		# dotyk, ktery mapu otevrel (Android k nemu posila i napodobene kliknuti mysi), by ji hned zavrel:
		# ikona mapy lezi tam, kde je na mape Zavrit - mapa zablikla a byl slyset jen zvuk
		if Time.get_ticks_msec() - _opened_ms < 300:
			return
		var pos: Vector2 = event.position
		if not asking:
			# klepnuti kamkoli do blizkosti erbu vybere misto
			_cur = pos
			_update_hover()
			if _hover >= 0:
				sel = _hover
				_ask()
				_c.queue_redraw()
				return
		for rr: Array in _rects:
			if (rr[0] as Rect2).has_point(pos):
				match String(rr[1]):
					"zavrit":
						close()
					"misto":
						sel = int(rr[2])
						_ask()
					"odpoved":
						_answer(bool(rr[2]))
				break
		_c.queue_redraw()
	elif event is InputEventKey and event.pressed and (event as InputEventKey).keycode in [KEY_ESCAPE, KEY_M]:
		close()


func _dist_km() -> float:
	var pp: Vector3 = main.player.global_position
	var c: Vector3 = MISTA[sel]["cil"]
	return _delka(trasa(Vector2(pp.x, pp.z), Vector2(c.x, c.z))) / 1000.0


## Sedi hrac na koni? Mapa to pozna sama (Misa 14. 11.: zadny prepinac).
func na_koni() -> bool:
	return main.player.get("na_koni") != null


func _km_h(kun: bool) -> float:
	var cf: Dictionary = Pravidla.cti("jizda", "rychle_cestovani")
	return float(cf["kun_km_h"]) if kun else float(cf["chuze_km_h"])


## Trasa po cestach (sit chuze postav lide._g z os cest sveta): od hrace na nejblizsi bod site, po siti (A*), z nejblizsiho
## bodu k cili; kdyz je to vzdusnou carou kratsi nez jen dojit na cestu a z ni, rovnou.
func trasa(od: Vector2, do_: Vector2) -> PackedVector2Array:
	var p := PackedVector2Array([od])
	var lide: Node = main.world.get_node_or_null("Lide") if main.world else null
	var g: AStar2D = lide.get("_g") if lide else null
	if g != null and g.get_point_count() > 0:
		var a := g.get_closest_point(od)
		var b := g.get_closest_point(do_)
		if od.distance_to(do_) > od.distance_to(g.get_point_position(a)) + do_.distance_to(g.get_point_position(b)):
			p.append_array(g.get_point_path(a, b))
	p.append(do_)
	return p


static func _delka(p: PackedVector2Array) -> float:
	var d := 0.0
	for i in p.size() - 1:
		d += p[i].distance_to(p[i + 1])
	return d


func _bod_trasy(sj: float) -> Vector2:
	var b: PackedVector2Array = _jizda["body"]
	var kum: PackedFloat32Array = _jizda["kum"]
	for i in b.size() - 1:
		if kum[i + 1] >= sj:
			return b[i].lerp(b[i + 1], (sj - kum[i]) / maxf(kum[i + 1] - kum[i], 0.001))
	return b[b.size() - 1]


func _zacni_jizdu(m: Dictionary) -> void:
	var pp: Vector3 = main.player.global_position
	var c3: Vector3 = m["cil"]
	var b := trasa(Vector2(pp.x, pp.z), Vector2(c3.x, c3.z))
	var kum := PackedFloat32Array([0.0])
	for i in b.size() - 1:
		kum.append(kum[i] + b[i].distance_to(b[i + 1]))
	var L := kum[kum.size() - 1]
	var cf: Dictionary = Pravidla.cti("jizda", "rychle_cestovani")
	var dur := clampf(L / float(cf["mapa_m_za_s"]), float(cf["min_s"]), float(cf["max_s"]))
	var kun := na_koni()
	_jizda = {"body": b, "kum": kum, "L": L, "s": 0.0, "rychlost_m_s": L / dur, "kun": kun, "km_h": _km_h(kun),
		"cil": c3, "pohled": m["pohled"], "nazev": String(m["nazev"]), "hod0": float(main.day.hour) if main.day else 12.0}
	_c.queue_redraw()


## Konec jizdy: v cili (misto z mapy), nebo zastaveno - hrac na ceste v bode figurky, pohled dal po trase.
## Cas = ujeta vzdalenost / rychlost chuze nebo jizdy.
func _dorazit(v_cili: bool) -> void:
	if _jizda.is_empty():
		return
	var sj: float = _jizda["s"]
	var hodin := sj / 1000.0 / float(_jizda["km_h"])
	var cil: Vector3 = _jizda["cil"]
	var pohled: Vector3 = _jizda["pohled"]
	var nazev := String(_jizda["nazev"])
	if not v_cili:
		var c2 := _bod_trasy(sj)
		var p2 := _bod_trasy(minf(sj + 20.0, float(_jizda["L"])))
		if p2.distance_to(c2) < 1.0:
			p2 = c2 + Vector2(0, -10)
		cil = Vector3(c2.x, 0.0, c2.y)
		pohled = Vector3(p2.x, 2.0, p2.y)
		nazev = "cesta"
	_jizda = {}
	close()
	main.fast_travel(cil, pohled, hodin, nazev)


func _ask() -> void:
	if Vector2(main.player.global_position.x, main.player.global_position.z).distance_to(MISTA[sel]["p"]) < 60.0:
		main.hud.toast("Tady už jsi.", 1.6)
		close()
		return
	asking = true
	ano = true
	main.life.sfx("menu_vyber", -8.0)


func _answer(yes: bool) -> void:
	asking = false
	if not yes:
		_c.queue_redraw()
		return
	_zacni_jizdu(MISTA[sel])
