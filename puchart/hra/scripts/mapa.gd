extends CanvasLayer
## Mapa na pergamenu (nastroje/mapa.py) s místy pro rychlé cestování – podle Havrana (scripts/mapa.gd + main.gd fast_travel;
## Míša 12. 11. večer: „zruš menu Místa, budeme používat jen mapu jako Havran“). Místa = hra/data/mapa_body.json (erb, název,
## cíl, pohled; hospoda, ves a hájovna z hra/data/mista_stavby.json). Klepnutí na erb (nebo kurzor levou páčkou + A) se
## zeptá „Rychlé cestování?“; cesta zatmí obraz, posune denní dobu o dobu chůze a postaví hráče na zem: výška vždy
## paprskem dolů na kolize (cil_na_zemi) – nikdy z čísla (přesun do sklepa propadl pod mapu). Otevírá ikona mapy,
## klávesa M, kříž nahoru; zavírá pečeť, B, Esc, M.

const INK := Color(0.2, 0.12, 0.06)

var proch: Node                 # prochazka.gd (hlavni, hrac, hv: hud, day)
var hrac: Node3D
var info: Dictionary
var cfg: Dictionary
var mista: Array = []           # [{id, nazev, erb, p: Vector2, cil: Vector2, pohled: Vector2}]
var otevrena := false
var sel := 0
var asking := false
var ano := true
var _c: Control
var _tex: Texture2D
var _erby := {}
var _fb: Font
var _fm: Font
var _rects: Array = []
var _opened_ms := 0
var _stick := false
var _cur := Vector2(-1, -1)
var _hover := -1
# rychlé cestování jako KCD (Míša 14. 11.): figurka jede po mapě po cestách, čas ubíhá podle chůze nebo jízdy, jde zastavit
var _astar := AStar2D.new()
var _fig := {}                  # "kun" / "pesky" -> Texture2D (nastroje/mapa_figurka.py)
var _jizda := {}                # běžící cesta: body, kum (kumulativní délky), L, s, rychlost_m_s (mapa), km_h, cil, pohled, hod0


## Místa mapy z dat: pevná (cil/pohled) i odvozená ze staveb nových míst (misto + prichod).
static func nacti_mista(c: Dictionary) -> Array:
	var ms: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista_stavby.json")) if FileAccess.file_exists("res://data/mista_stavby.json") else {}
	var out: Array = []
	for m: Dictionary in c["mista"]:
		var e := {"id": m["id"], "nazev": m["nazev"], "erb": m["erb"]}
		if m.has("misto"):
			var domy: Array = (ms.get("stavby", []) as Array).filter(func(s: Dictionary) -> bool: return s["misto"] == m["misto"])
			if domy.is_empty(): continue   # místo není postaveno – na mapě není
			var st := Vector2.ZERO
			for s: Dictionary in domy: st += Vector2(float(s["x"]), float(s["z"]))
			st /= domy.size()
			e["p"] = st
			if m.get("prichod", "") == "naves" and not (ms.get("studny", []) as Array).is_empty():
				var nej: Dictionary = {}; var nd := INF
				for sd: Dictionary in ms["studny"]:
					var d := st.distance_to(Vector2(float(sd["x"]), float(sd["z"])))
					if d < nd: nd = d; nej = sd
				var sv := Vector2(float(nej["x"]), float(nej["z"]))
				e["pohled"] = sv
				var od := (st - sv).normalized() if st.distance_to(sv) > 0.1 else Vector2(1, 0)
				e["cil"] = sv + od * float(c["od_studny_m"])
			else:   # před dveře domu místa (vstupy domů z modelu, mista_rozmisteni.py)
				var usedl := {}
				for u: Dictionary in ms.get("usedlosti", []): usedl[int(u["i"])] = u["misto"]
				var vst: Dictionary = {}
				for v: Dictionary in ms.get("vstupy", []):
					if usedl.get(int(v["usedlost"]), "") == m["misto"] and v["druh"] == "dvere" and String(v["stavba"]).begins_with("Dum"):
						vst = v; break
				if vst.is_empty():
					e["cil"] = st + Vector2(6, 0); e["pohled"] = st
				else:
					var cc := Vector2(vst["c"][0], vst["c"][1]); var n := Vector2(vst["n"][0], vst["n"][1])
					e["cil"] = cc + n * float(c["pred_dvermi_m"]); e["pohled"] = cc
		else:
			e["p"] = Vector2(m["p"][0], m["p"][1]); e["cil"] = Vector2(m["cil"][0], m["cil"][1]); e["pohled"] = Vector2(m["pohled"][0], m["pohled"][1])
		out.append(e)
	return out


## Bod na zemi pro hráče (Havran fast_travel: volné místo pro kapsli po spirále): paprsek dolů od terénu + paprsek_nad_m
## na kolize (podlaha nádvoří, dlažba, terén); kolize terénu a kmenů se v cíli postaví hned.
static func cil_na_zemi(hl: Node, c: Dictionary, cil: Vector2, bez: Array[RID]) -> Vector3:
	var space: PhysicsDirectSpaceState3D = hl.get_world_3d().direct_space_state
	var cap := CapsuleShape3D.new(); cap.radius = 0.4; cap.height = 1.8
	var cq := PhysicsShapeQueryParameters3D.new(); cq.shape = cap; cq.exclude = bez
	var prvni := Vector3.INF
	for k in int(c["volne_pokusu"]):
		var q := cil + Vector2.from_angle(k * 2.4) * (k * float(c["volne_spirala_m"]))
		var y := _zem(hl, space, q, c, bez)
		if prvni == Vector3.INF: prvni = Vector3(q.x, y, q.y)
		cq.transform = Transform3D(Basis(), Vector3(q.x, y + 1.05, q.y))
		if space.intersect_shape(cq, 1).is_empty(): return Vector3(q.x, y, q.y)
	return prvni


static func _zem(hl: Node, space: PhysicsDirectSpaceState3D, q: Vector2, c: Dictionary, bez: Array[RID]) -> float:
	var t: float = hl.svet.vyska(q.x, q.y)
	var rq := PhysicsRayQueryParameters3D.create(Vector3(q.x, t + float(c["paprsek_nad_m"]), q.y), Vector3(q.x, t - float(c["paprsek_pod_m"]), q.y))
	rq.exclude = bez
	var h := space.intersect_ray(rq)
	return float(h["position"].y) if not h.is_empty() else t


## Před paprskem: kolize terénu a kmenů v cíli (po nich je třeba jeden krok fyziky).
static func priprav_kolize(hl: Node, cil: Vector2) -> void:
	var p := Vector3(cil.x, hl.svet.vyska(cil.x, cil.y), cil.y)
	hl.svet.kolize_ihned(p)
	var les: Node = hl.get_node_or_null("Les")
	if les and les.has_method("aktualizuj_kolize"): les.aktualizuj_kolize(p, true)


func _ready() -> void:
	layer = 19
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	info = JSON.parse_string(FileAccess.get_file_as_string("res://data/mapa.json"))
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/mapa_body.json"))
	mista = nacti_mista(cfg)
	_tex = load("res://textury/ui/mapa.png") if ResourceLoader.exists("res://textury/ui/mapa.png") else null
	_fb = load("res://fonty/GrenzeGotisch-Bold.ttf"); _fm = load("res://fonty/GrenzeGotisch-Medium.ttf")
	for m: Dictionary in mista:
		if not _erby.has(m["erb"]): _erby[m["erb"]] = load("res://obrazky/erby/%s.png" % m["erb"])
	if FileAccess.file_exists("res://data/cesty_graf.json"):   # síť cest (nastroje/cesty_graf.py)
		var g: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/cesty_graf.json"))
		var uz: Array = g["uzly"]
		_astar.reserve_space(uz.size())
		for i in uz.size(): _astar.add_point(i, Vector2(uz[i][0], uz[i][1]))
		for h: Array in g["hrany"]: _astar.connect_points(int(h[0]), int(h[1]))
	for k in ["kun", "pesky"]:
		if ResourceLoader.exists("res://textury/ui/figurka_%s.png" % k): _fig[k] = load("res://textury/ui/figurka_%s.png" % k)
	_c = Control.new(); _c.set_anchors_preset(Control.PRESET_FULL_RECT)
	_c.mouse_filter = Control.MOUSE_FILTER_IGNORE   # dotyky čte _input jen při otevřené mapě (tlačítka dveří pod ní nesmí blokovat)
	_c.draw.connect(_draw_all); add_child(_c)


func prepni() -> void:
	if otevrena: close()
	else: show_map()


func show_map() -> void:
	if otevrena or _tex == null or hrac == null: return
	otevrena = true; asking = false; visible = true
	_opened_ms = Time.get_ticks_msec()
	sel = 1 if _here() == 0 and mista.size() > 1 else 0
	_cursor_to(sel)
	get_tree().paused = true
	if proch and proch.has_method("_fps_menu"): proch._fps_menu(true)
	_c.queue_redraw()


func close() -> void:
	if not otevrena: return
	_jizda = {}
	otevrena = false; visible = false
	get_tree().paused = false
	if proch and proch.has_method("_fps_menu"): proch._fps_menu(false)


func _here() -> int:
	var pp := hrac.global_position; var best := 0; var bd := 1e9
	for i in mista.size():
		var d := Vector2(pp.x, pp.z).distance_to(mista[i]["p"])
		if d < bd: bd = d; best = i
	return best


func _process(_d: float) -> void:
	if otevrena and not _jizda.is_empty():
		_jizda["s"] = minf(float(_jizda["s"]) + float(_jizda["rychlost_m_s"]) * _d, float(_jizda["L"]))
		_c.queue_redraw()
		if float(_jizda["s"]) >= float(_jizda["L"]): _dorazit(true)
		return
	if not otevrena or asking: return
	var v := Vector2(Input.get_joy_axis(0, JOY_AXIS_LEFT_X), Input.get_joy_axis(0, JOY_AXIS_LEFT_Y))
	if v.length() > 0.2:
		_cur = (_cur + v * v.length() * 900.0 * _d).clamp(Vector2.ZERO, _c.get_viewport_rect().size)
		_update_hover(); _c.queue_redraw()
	elif Engine.get_process_frames() % 10 == 0:
		_c.queue_redraw()


func _u(r: Rect2) -> float: return clampf(r.size.y / 900.0, 0.6, 1.6)


func _update_hover() -> void:
	var r := _map_rect(); var best := -1; var bd := 70.0 * _u(r)
	for i in mista.size():
		var c := _to_screen(r, mista[i]["p"]) - Vector2(0, 34.0 * _u(r))
		var d := c.distance_to(_cur)
		if d < bd: bd = d; best = i
	_hover = best
	if best >= 0: sel = best


func _cursor_to(i: int) -> void:
	if mista.is_empty(): return
	var r := _map_rect()
	_cur = _to_screen(r, mista[i]["p"]) - Vector2(0, 34.0 * _u(r)); _hover = i


func _next(step: int) -> void:
	if mista.is_empty(): return
	sel = (sel + step + mista.size()) % mista.size(); _cursor_to(sel)


func _map_rect() -> Rect2:
	var s := _c.get_viewport_rect().size
	var ts := _tex.get_size() if _tex else Vector2(1, 1)
	var k := minf((s.x - 40.0) / ts.x, (s.y - 40.0) / ts.y)
	var sz := ts * k
	return Rect2((s - sz) * 0.5, sz)


func _to_screen(r: Rect2, p: Vector2) -> Vector2:
	var px := float(info["px_m"])
	return r.position + Vector2((p.x - float(info["x0"])) / px / float(info["sirka"]) * r.size.x, (p.y - float(info["z0"])) / px / float(info["vyska"]) * r.size.y)


func _draw_all() -> void:
	_rects.clear()
	var s := _c.get_viewport_rect().size
	_c.draw_rect(Rect2(Vector2.ZERO, s), Color(0.04, 0.03, 0.02, 0.92))
	if _tex == null: return
	var r := _map_rect()
	_c.draw_texture_rect(_tex, r, false)
	var u := _u(r)
	for i in mista.size():   # erb a název místa
		var m: Dictionary = mista[i]
		var c := _to_screen(r, m["p"])
		var es := 58.0 * u * (1.18 if i == sel else 1.0)
		var er := Rect2(c - Vector2(es * 0.5, es * 1.1), Vector2(es, es))
		if i == sel: _c.draw_circle(er.get_center(), es * 0.7, Color(1.0, 0.85, 0.45, 0.45))
		_c.draw_texture_rect(_erby[m["erb"]], er, false)
		_rects.append([er.grow(12), "misto", i])
	if not _jizda.is_empty():
		_draw_jizda(r, u, s); return
	# hráč: šipka ve směru pohledu (Havran)
	var pp := hrac.global_position
	var pc := _to_screen(r, Vector2(pp.x, pp.z))
	var yaw: float = hrac.get("yaw") if hrac.get("yaw") != null else hrac.global_rotation.y
	var fwd := Vector2(-sin(yaw), -cos(yaw)); var side := Vector2(-fwd.y, fwd.x); var a := 16.0 * u
	var pts := PackedVector2Array([pc + fwd * a, pc - fwd * a * 0.6 + side * a * 0.65, pc - fwd * a * 0.25, pc - fwd * a * 0.6 - side * a * 0.65])
	_c.draw_colored_polygon(pts, Color(0.7, 0.08, 0.05))
	_c.draw_polyline(pts + PackedVector2Array([pts[0]]), Color(0.15, 0.05, 0.02), 2.0, true)
	if _cur.x >= 0.0 and not asking:
		var cc := Color(0.95, 0.85, 0.55, 0.95)
		_c.draw_arc(_cur, 14.0 * u, 0.0, TAU, 28, Color(0, 0, 0, 0.6), 5.0)
		_c.draw_arc(_cur, 14.0 * u, 0.0, TAU, 28, cc, 2.5)
		for dv: Vector2 in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
			_c.draw_line(_cur + dv * 8.0 * u, _cur + dv * 22.0 * u, cc, 2.5)
		if _hover >= 0:   # název místa nad kurzorem (Havran; erby jsou blízko u sebe, popisky by se překrývaly)
			_text(_cur + Vector2(0, -40.0 * u), String(mista[_hover]["nazev"]), int(28 * u), INK, Color(1, 1, 1, 1), _fb)
	_text(Vector2(s.x * 0.5, s.y - 12), "Klepni na místo nebo najeď kurzorem (levá páčka) a potvrď A  ·  B zavřít", int(20 * u), INK, Color(1, 1, 1, 0.92))
	var cr := Rect2(Vector2(s.x - 86, 18), Vector2(68, 60))
	Styl.kresli_pecet(_c, cr.get_center(), 27.0)
	_rects.append([cr, "zavrit", 0])
	if asking: _draw_ask(s, u)


## Jízda po mapě: ujetá část trasy plnou čarou, zbytek čárkovaně, figurka (zrcadlí se podle směru), hodina dne, Zastavit.
func _draw_jizda(r: Rect2, u: float, s: Vector2) -> void:
	var b: PackedVector2Array = _jizda["body"]; var kum: PackedFloat32Array = _jizda["kum"]; var sj: float = _jizda["s"]
	var poz := _bod_trasy(sj)
	var hotovo := PackedVector2Array(); var zbyva := PackedVector2Array()
	for i in b.size():
		if kum[i] <= sj: hotovo.append(_to_screen(r, b[i]))
		else: zbyva.append(_to_screen(r, b[i]))
	var ps := _to_screen(r, poz)
	hotovo.append(ps); zbyva.insert(0, ps)
	if hotovo.size() > 1: _c.draw_polyline(hotovo, Color(0.45, 0.08, 0.05, 0.85), 4.0 * u, true)
	if zbyva.size() > 1:
		for i in zbyva.size() - 1: _c.draw_dashed_line(zbyva[i], zbyva[i + 1], Color(0.2, 0.12, 0.06, 0.9), 3.0 * u, 10.0 * u, false)
	var t: Texture2D = _fig.get("kun" if bool(_jizda["kun"]) else "pesky")
	var fs := float(cfg["cestovani"]["figurka_px"]) * u
	var dalsi := _bod_trasy(minf(sj + 15.0, float(_jizda["L"])))
	var vlevo := dalsi.x < poz.x - 0.01
	var fr := Rect2(ps - Vector2(fs * 0.5, fs * 0.86), Vector2(fs, fs))
	# zrcadlení kolem bodu trasy (Míša 14. 11.: figurka „odskakovala z linie doprava do lesa“ – záporná šířka obdélníku
	# kreslila o celou šířku vedle); podstavec figurky stojí na čáře trasy
	_c.draw_set_transform(ps, 0.0, Vector2(-1.0 if vlevo else 1.0, 1.0))
	if t: _c.draw_texture_rect(t, Rect2(-Vector2(fs * 0.5, fs * 0.86), Vector2(fs, fs)), false)
	_c.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	_rects.append([fr.grow(10), "zastavit", 0])
	var hod := fposmod(float(_jizda["hod0"]) + sj / 1000.0 / float(_jizda["km_h"]), 24.0)
	var min_ := int(round(sj / 1000.0 / float(_jizda["km_h"]) * 60.0))
	_text(Vector2(s.x * 0.5, 64 * u), "%s  ·  %02d:%02d  ·  %d min %s" % [String(_jizda["nazev"]), int(hod), int(fmod(hod, 1.0) * 60.0), min_, "jízdy" if bool(_jizda["kun"]) else "chůze"], int(28 * u), INK, Color(1, 1, 1, 0.92), _fb)
	var br := Rect2(Vector2(s.x * 0.5 - 130 * u, s.y - 96 * u), Vector2(260 * u, 64 * u))
	Styl.kresli_tlacitko(_c, br, 0, true, br.size.y / 76.0)
	_text(br.get_center() + Vector2(0, 12 * u), "Zastavit", int(34 * u), Styl.RED, Color(0, 0, 0, 0), _fb)
	_rects.append([br, "zastavit", 0])


func _draw_ask(s: Vector2, u: float) -> void:
	_rects.clear()
	var m: Dictionary = mista[sel]
	var w := 660.0 * u; var h := 300.0 * u
	var box := Rect2((s - Vector2(w, h)) * 0.5, Vector2(w, h))
	Styl.kresli_list(_c, box, 0.45 * u)
	_text(box.position + Vector2(w * 0.5, 86 * u), "Rychlé cestování", int(40 * u), INK, Color(0, 0, 0, 0), _fb)
	Styl.kresli_linku(_c, box.position + Vector2(w * 0.5, 104 * u), w * 0.5, u)
	var kun := na_koni()
	_text(box.position + Vector2(w * 0.5, 150 * u), "do: %s  (asi %d minut %s)" % [m["nazev"], int(round(_dist_km() / _km_h(kun) * 60.0)), "jízdy" if kun else "chůze"], int(26 * u), INK, Color(0, 0, 0, 0))
	for k in 2:
		var br := Rect2(box.position + Vector2(w * (0.12 + 0.44 * k), h - 108 * u), Vector2(w * 0.32, 60 * u))
		var on := (k == 0) == ano
		Styl.kresli_tlacitko(_c, br, k, on, br.size.y / 76.0)
		_text(br.get_center() + Vector2(0, 11 * u), "Ano" if k == 0 else "Ne", int(34 * u), Styl.RED if on else INK, Color(0, 0, 0, 0), _fb)
		_rects.append([br, "odpoved", k == 0])


func _text(p: Vector2, t: String, size: int, col: Color, bg: Color, f: Font = null) -> void:
	if f == null: f = _fm
	var w := f.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	if bg.a > 0.0:
		var pr := Rect2(p.x - w * 0.5 - size * 1.4, p.y - size * 1.25, w + size * 2.8, size * 1.9)
		Styl.kresli_pruh(_c, pr, pr.size.y / 150.0, bg.a)
	_c.draw_string(f, p - Vector2(w * 0.5, 0), t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


func _unhandled_input(e: InputEvent) -> void:   # otevření, když je mapa zavřená (klávesa M)
	if not otevrena and e is InputEventKey and e.pressed and not e.echo and (e as InputEventKey).keycode == KEY_M and not get_tree().paused:
		show_map(); get_viewport().set_input_as_handled()


func _input(event: InputEvent) -> void:
	if not otevrena: return
	if not _jizda.is_empty():   # během jízdy: klepnutí na figurku / Zastavit, B, Esc = zastavit
		var stop := false
		if (event is InputEventScreenTouch and event.pressed) or (event is InputEventMouseButton and event.pressed):
			for rr: Array in _rects:
				if String(rr[1]) == "zastavit" and (rr[0] as Rect2).has_point(event.position): stop = true
		elif event is InputEventJoypadButton and event.pressed and (event as InputEventJoypadButton).button_index in [JOY_BUTTON_A, JOY_BUTTON_B]: stop = true
		elif event is InputEventKey and event.pressed and not event.echo and (event as InputEventKey).keycode in [KEY_ESCAPE, KEY_SPACE]: stop = true
		if event is InputEventScreenTouch or event is InputEventMouseButton or event is InputEventJoypadButton or event is InputEventKey: get_viewport().set_input_as_handled()
		if stop: _dorazit(false)
		return
	if event is InputEventJoypadButton and event.pressed:
		get_viewport().set_input_as_handled()
		if Time.get_ticks_msec() - _opened_ms < 250: return
		var b := (event as InputEventJoypadButton).button_index
		if asking:
			match b:
				JOY_BUTTON_A: _answer(ano)
				JOY_BUTTON_B: _answer(false)
				JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_RIGHT: ano = not ano
			_c.queue_redraw(); return
		match b:
			JOY_BUTTON_B, JOY_BUTTON_START, JOY_BUTTON_DPAD_UP, JOY_BUTTON_BACK: close()
			JOY_BUTTON_A:
				if _hover >= 0: sel = _hover; _ask()
			JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_RIGHT_SHOULDER: _next(1)
			JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_LEFT_SHOULDER: _next(-1)
		_c.queue_redraw()
	elif event is InputEventJoypadMotion:
		var v := Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
		if asking and absf(v) > 0.6 and not _stick:
			_stick = true; ano = not ano; _c.queue_redraw()
		elif absf(v) < 0.3: _stick = false
	elif event is InputEventMouseMotion and not asking:
		_cur = (event as InputEventMouseMotion).position; _update_hover(); _c.queue_redraw()
	elif (event is InputEventScreenTouch and event.pressed) or (event is InputEventMouseButton and event.pressed):
		get_viewport().set_input_as_handled()
		if Time.get_ticks_msec() - _opened_ms < 300: return   # dotyk, který mapu otevřel (Havran: mapa zablikla)
		var pos: Vector2 = event.position
		for rr: Array in _rects:
			if (rr[0] as Rect2).has_point(pos):
				match String(rr[1]):
					"zavrit": close()
					"misto": sel = int(rr[2]); _ask()
					"odpoved": _answer(bool(rr[2]))
				_c.queue_redraw(); return
		if not asking:
			_cur = pos; _update_hover()
			if _hover >= 0: sel = _hover; _ask()
		_c.queue_redraw()
	elif event is InputEventScreenTouch or event is InputEventMouseButton:
		get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and not event.echo and (event as InputEventKey).keycode in [KEY_ESCAPE, KEY_M]:
		get_viewport().set_input_as_handled()
		if asking: asking = false; _c.queue_redraw()
		else: close()


func _dist_km() -> float:
	var pp := hrac.global_position
	return _delka(trasa(Vector2(pp.x, pp.z), mista[sel]["cil"])) / 1000.0


## Sedí hráč na koni? Mapa to pozná sama (Míša 14. 11.: „žádný přepínač“); kůň zatím v Puchartu není → pěšky.
func na_koni() -> bool:
	return hrac != null and hrac.get("na_koni") == true


func _km_h(kun: bool) -> float:
	return float(cfg["kun_km_h"]) if kun else float(cfg["chuze_km_h"])


## Trasa po cestách: od hráče na nejbližší bod sítě, po síti (A*), z nejbližšího bodu k cíli. Když je to vzdušnou čarou
## kratší než jen dojít na cestu a z ní (oba konce mimo cesty blízko u sebe), rovnou.
func trasa(od: Vector2, do_: Vector2) -> PackedVector2Array:
	var p := PackedVector2Array([od])
	if _astar.get_point_count() > 0:
		var a := _astar.get_closest_point(od); var b := _astar.get_closest_point(do_)
		if od.distance_to(do_) > od.distance_to(_astar.get_point_position(a)) + do_.distance_to(_astar.get_point_position(b)):
			p.append_array(_astar.get_point_path(a, b))
	p.append(do_)
	return p


static func _delka(p: PackedVector2Array) -> float:
	var d := 0.0
	for i in p.size() - 1: d += p[i].distance_to(p[i + 1])
	return d


func _bod_trasy(sj: float) -> Vector2:
	var b: PackedVector2Array = _jizda["body"]; var kum: PackedFloat32Array = _jizda["kum"]
	for i in b.size() - 1:
		if kum[i + 1] >= sj:
			var t := (sj - kum[i]) / maxf(kum[i + 1] - kum[i], 0.001)
			return b[i].lerp(b[i + 1], t)
	return b[b.size() - 1]


func _zacni_jizdu(m: Dictionary) -> void:
	var pp := hrac.global_position
	var b := trasa(Vector2(pp.x, pp.z), m["cil"])
	var kum := PackedFloat32Array([0.0])
	for i in b.size() - 1: kum.append(kum[i] + b[i].distance_to(b[i + 1]))
	var L := kum[kum.size() - 1]
	var c: Dictionary = cfg["cestovani"]
	var dur := clampf(L / float(c["mapa_m_za_s"]), float(c["min_s"]), float(c["max_s"]))
	var kun := na_koni()
	var hl: Node = proch.hlavni if proch else null
	_jizda = {"body": b, "kum": kum, "L": L, "s": 0.0, "rychlost_m_s": L / dur, "kun": kun, "km_h": _km_h(kun),
		"cil": m["cil"], "pohled": m["pohled"], "nazev": m["nazev"], "hod0": float(hl.den.hour) if hl and hl.den else 12.0}
	if proch and proch.has_method("_fps_menu"): proch._fps_menu(false)   # figurka jede plynule (otevřená mapa jinak drží 10 snímků)
	_c.queue_redraw()


## Konec jízdy: v cíli (místo z mapy), nebo zastaveno – hráč na cestě v bodě figurky, pohled dál po trase.
## Čas = ujetá vzdálenost / rychlost chůze nebo jízdy.
func _dorazit(v_cili: bool) -> void:
	if _jizda.is_empty(): return
	var sj: float = _jizda["s"]
	var hodin := sj / 1000.0 / float(_jizda["km_h"])
	var cil: Vector2 = _jizda["cil"]; var pohled: Vector2 = _jizda["pohled"]
	if not v_cili:
		cil = _bod_trasy(sj); pohled = _bod_trasy(minf(sj + 20.0, float(_jizda["L"])))
		if pohled.distance_to(cil) < 1.0: pohled = cil + Vector2(0, -10)
	_jizda = {}
	close()
	cestuj(cil, pohled, hodin, true)


func _ask() -> void:
	if Vector2(hrac.global_position.x, hrac.global_position.z).distance_to(mista[sel]["p"]) < float(cfg["uz_tady_m"]):
		if proch and proch.hv: proch.hv.hud.toast("Tady už jsi.", 1.6)
		close(); return
	asking = true; ano = true


func _answer(yes: bool) -> void:
	asking = false
	if not yes:
		_c.queue_redraw(); return
	_zacni_jizdu(mista[sel])


## Rychlé cestování (Havran main.gd fast_travel): zatmít, posunout čas o dobu chůze, kolize v cíli, hráč na zem, rozednít.
func cestuj(cil: Vector2, pohled: Vector2, hodin: float, z_mapy := false) -> void:
	var hl: Node = proch.hlavni
	var cl := CanvasLayer.new(); cl.layer = 30; cl.process_mode = Node.PROCESS_MODE_ALWAYS
	var fade := ColorRect.new(); fade.color = Color(0, 0, 0, 0); fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade.mouse_filter = Control.MOUSE_FILTER_STOP; cl.add_child(fade); add_child(cl)
	# pojistka (Havran Míša 0.995 černá obrazovka): zatmění zmizí nejpozději po 10 s, ať se stane cokoli
	var wcl: WeakRef = weakref(cl)
	get_tree().create_timer(10.0, true).timeout.connect(func() -> void:
		var x: Object = wcl.get_ref()
		if x != null:
			get_tree().paused = false; (x as Node).queue_free())
	get_tree().paused = true
	if z_mapy: fade.color.a = 1.0   # z mapy rovnou do černé (jinak by bliklo staré místo)
	else:
		var tw := create_tween().set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
		tw.tween_property(fade, "color:a", 1.0, 0.7)
		await tw.finished
	if hrac.leti and proch.has_method("_akce"): proch._akce("set:let", null)
	if hodin > 0.0 and hl.den: hl.den.set_hour(hl.den.hour + hodin, 0.01)
	priprav_kolize(hl, cil)
	get_tree().paused = false
	await get_tree().process_frame
	await get_tree().physics_frame
	var bez: Array[RID] = [(hrac as CollisionObject3D).get_rid()]
	var p := cil_na_zemi(hl, cfg, cil, bez)
	(hrac as CharacterBody3D).velocity = Vector3.ZERO
	hrac.position = p + Vector3(0, 0.1, 0)
	hrac.nastav_pohled(atan2(-(pohled.x - p.x), -(pohled.y - p.z)), -0.05)
	for i in 8: await get_tree().physics_frame
	var tw2 := create_tween().set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tw2.tween_property(fade, "color:a", 0.0, 0.9)
	await tw2.finished
	if is_instance_valid(cl): cl.queue_free()
