class_name Styl
extends RefCounted
## Jednotny vzhled nabidek: roztrepeny pergamen (obrazky/ui, tools/gen_ui.py), inkoustove pismo,
## vybrana polozka podtrzena tahem cerveneho inkoustu. Zadna hranata okenka.

const INK := Color(0.2, 0.11, 0.04)
const INK_SOFT := Color(0.36, 0.24, 0.12)
const INK_FADE := Color(0.3, 0.2, 0.1, 0.42)
const RED := Color(0.55, 0.09, 0.04)
const STIN := Color(0, 0, 0, 0.35)

static var _tex := {}
static var _sb := {}


static func tex(n: String) -> Texture2D:
	if not _tex.has(n):
		_tex[n] = load("res://obrazky/ui/%s.png" % n)
	return _tex[n]


## List pergamenu jako StyleBox (okraje se nenatahuji, jen stred).
static func list(obsah := 56.0) -> StyleBoxTexture:
	var key := "list%d" % int(obsah)
	if not _sb.has(key):
		var sb := StyleBoxTexture.new()
		sb.texture = tex("list")
		sb.set_texture_margin_all(120)
		sb.set_content_margin_all(obsah)
		_sb[key] = sb
	return _sb[key]


## Uzky pruh pergamenu (hlasky, popisky, male nabidky).
static func pruh(obsah := 18.0) -> StyleBoxTexture:
	var key := "pruh%d" % int(obsah)
	if not _sb.has(key):
		var sb := StyleBoxTexture.new()
		sb.texture = tex("pruh")
		sb.texture_margin_left = 60
		sb.texture_margin_right = 60
		sb.texture_margin_top = 50
		sb.texture_margin_bottom = 50
		sb.set_content_margin_all(obsah)
		sb.content_margin_left = obsah * 2.0
		sb.content_margin_right = obsah * 2.0
		_sb[key] = sb
	return _sb[key]


static func vyber(jemny := false) -> StyleBoxTexture:
	var key := "vyber%s" % jemny
	if not _sb.has(key):
		var sb := StyleBoxTexture.new()
		sb.texture = tex("vyber_jemny" if jemny else "vyber")
		sb.texture_margin_left = 90
		sb.texture_margin_right = 90
		sb.set_content_margin_all(4)
		_sb[key] = sb
	return _sb[key]


## Polozka nabidky: vlastni opaleny pruh pergamenu (4 varianty, at se neopakuji),
## vybrana = jasnejsi pergamen, cerveny inkoust a voskova pecet vlevo.
static func pruh_tlacitko(var_i: int, stav: String) -> StyleBoxTexture:
	var key := "tl%d%s" % [var_i % 4, stav]
	if not _sb.has(key):
		var sb := StyleBoxTexture.new()
		sb.texture = tex("tlacitko_%d" % (var_i % 4))
		sb.texture_margin_left = 46
		sb.texture_margin_right = 46
		sb.content_margin_left = 40
		sb.content_margin_right = 40
		sb.content_margin_top = 6
		sb.content_margin_bottom = 6
		sb.modulate_color = {"normal": Color(0.86, 0.82, 0.76), "vyber": Color(1.06, 1.03, 0.97),
				"stisk": Color(0.95, 0.9, 0.82), "vyp": Color(0.62, 0.58, 0.54, 0.75)}[stav]
		_sb[key] = sb
	return _sb[key]


static func tlacitko_pruh(b: Button, font: Font, fs: int, var_i: int) -> void:
	b.add_theme_stylebox_override("normal", pruh_tlacitko(var_i, "normal"))
	b.add_theme_stylebox_override("hover", pruh_tlacitko(var_i, "vyber"))
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.add_theme_stylebox_override("pressed", pruh_tlacitko(var_i, "stisk"))
	b.add_theme_stylebox_override("disabled", pruh_tlacitko(var_i, "vyp"))
	b.add_theme_font_override("font", font)
	b.add_theme_font_size_override("font_size", fs)
	b.add_theme_color_override("font_color", INK)
	b.add_theme_color_override("font_hover_color", RED)
	b.add_theme_color_override("font_focus_color", RED)
	b.add_theme_color_override("font_pressed_color", RED)
	b.add_theme_color_override("font_hover_pressed_color", RED)
	b.add_theme_color_override("font_disabled_color", INK_FADE)
	# vybrana polozka (ovladac i mys): jasny pruh a pecet na levem konci
	b.draw.connect(func() -> void:
		var on := b.has_focus() or (b.is_hovered() and not b.disabled)
		if on:
			var r := Rect2(Vector2.ZERO, b.size)
			if b.has_focus() and not b.is_hovered():
				b.draw_style_box(pruh_tlacitko(var_i, "vyber"), r)
				b.draw_string(font, Vector2(0, (b.size.y + font.get_ascent(fs) - font.get_descent(fs)) * 0.5), b.text,
						HORIZONTAL_ALIGNMENT_CENTER, b.size.x, fs, RED)
			kresli_pecet(b, Vector2(18, b.size.y * 0.5), b.size.y * 0.36, "kriz"))
	b.focus_entered.connect(b.queue_redraw)
	b.focus_exited.connect(b.queue_redraw)
	b.mouse_entered.connect(b.queue_redraw)
	b.mouse_exited.connect(b.queue_redraw)


## Pruh tlacitka pro kreslene nabidky (mapa, spanek).
static func kresli_tlacitko(ci: CanvasItem, r: Rect2, var_i: int, on: bool, k := 1.0) -> void:
	_box(ci, pruh_tlacitko(var_i, "vyber" if on else "normal"), r, k)
	if on:
		kresli_pecet(ci, Vector2(r.position.x + 18 * k, r.get_center().y), r.size.y * 0.36, "kriz")


## Tlacitko jako napis inkoustem na pergamenu; vybrane = cerveny inkoust a tah stetcem.
static func tlacitko(b: Button, font: Font, fs: int) -> void:
	var e := StyleBoxEmpty.new()
	b.add_theme_stylebox_override("normal", e)
	b.add_theme_stylebox_override("disabled", e)
	b.add_theme_stylebox_override("hover", vyber(true))
	b.add_theme_stylebox_override("pressed", vyber())
	b.add_theme_stylebox_override("focus", vyber())
	b.add_theme_font_override("font", font)
	b.add_theme_font_size_override("font_size", fs)
	b.add_theme_color_override("font_color", INK)
	b.add_theme_color_override("font_hover_color", RED)
	b.add_theme_color_override("font_focus_color", RED)
	b.add_theme_color_override("font_pressed_color", RED)
	b.add_theme_color_override("font_hover_pressed_color", RED)
	b.add_theme_color_override("font_disabled_color", INK_FADE)
	b.add_theme_constant_override("outline_size", 0)


## Panel s pergamenem pro Control nabidky.
static func panel(obsah := 56.0) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", list(obsah))
	return p


# ------------------------------------------------------------ kresleni (_draw)

static func _box(ci: CanvasItem, sb: StyleBox, r: Rect2, k: float) -> void:
	k = maxf(k, 0.05)
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2(k, k))
	ci.draw_style_box(sb, Rect2(r.position / k, r.size / k))
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


## List pergamenu se stinem; k = meritko okraju (u z navrhu 1600x1000).
static func kresli_list(ci: CanvasItem, r: Rect2, k := 1.0, a := 1.0) -> void:
	k = minf(k, minf(r.size.x, r.size.y) / 250.0)   # okraje (120 px) se musi vejit
	var sb := list()
	if a < 1.0:
		sb = sb.duplicate()
		sb.modulate_color = Color(1, 1, 1, a)
	var st := sb.duplicate() as StyleBoxTexture
	st.modulate_color = Color(0, 0, 0, 0.4 * a)
	_box(ci, st, Rect2(r.position + Vector2(6, 9) * k, r.size), k)
	_box(ci, sb, r, k)


static func kresli_pruh(ci: CanvasItem, r: Rect2, k := 1.0, a := 1.0) -> void:
	k = minf(k, r.size.y / 110.0)                   # okraje (50 px) se musi vejit
	var sb := pruh()
	if a < 1.0:
		sb = sb.duplicate()
		sb.modulate_color = Color(1, 1, 1, a)
	_box(ci, sb, r, k)


static func kresli_vyber(ci: CanvasItem, r: Rect2, k := 1.0, jemny := false) -> void:
	_box(ci, vyber(jemny), r, k)


## Ozdobna inkoustova linka (pod nadpis).
static func kresli_linku(ci: CanvasItem, stred: Vector2, w: float, k := 1.0, a := 1.0) -> void:
	var h := 24.0 * k
	ci.draw_texture_rect(tex("linka"), Rect2(stred.x - w * 0.5, stred.y - h * 0.5, w, h), false, Color(1, 1, 1, a))


## Zaviraci pecet (misto hranateho krizku): cerveny vosk s vyrazenym krizem.
static func kresli_pecet(ci: CanvasItem, c: Vector2, r: float, znak := "x") -> void:
	var pts := PackedVector2Array()
	for i in 28:
		var a := TAU * i / 28.0
		pts.append(c + Vector2(cos(a), sin(a)) * r * (1.0 + 0.07 * sin(a * 5.0 + 1.3)))
	ci.draw_colored_polygon(pts, Color(0.5, 0.07, 0.04))
	ci.draw_circle(c, r * 0.72, Color(0.62, 0.1, 0.06))
	ci.draw_arc(c, r * 0.72, 0, TAU, 28, Color(0.36, 0.04, 0.02), maxf(1.0, r * 0.06), true)
	var d := r * 0.32
	var col := Color(0.32, 0.03, 0.02)
	if znak == "kriz":
		# vyrazeny tlapaty kriz
		for v: Vector2 in [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1)]:
			var n := Vector2(-v.y, v.x)
			ci.draw_colored_polygon(PackedVector2Array([c + n * r * 0.06, c + v * r * 0.46 + n * r * 0.17, c + v * r * 0.46 - n * r * 0.17, c - n * r * 0.06]), col)
	else:
		ci.draw_line(c + Vector2(-d, -d), c + Vector2(d, d), col, r * 0.13, true)
		ci.draw_line(c + Vector2(d, -d), c + Vector2(-d, d), col, r * 0.13, true)
	ci.draw_circle(c + Vector2(-r * 0.3, -r * 0.35), r * 0.12, Color(1, 0.6, 0.5, 0.25))
