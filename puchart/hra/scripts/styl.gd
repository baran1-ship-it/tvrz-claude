## Převzato z Havrana (scripts/styl.gd), Míša 3. 11.: „svitky jako v Havranovi“.
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
		_tex[n] = load("res://textury/ui/%s.png" % n)
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


# ------------------------------------------------------------ Blood for Blood (nabídka a načítání, Míša 17. 11.)
# Předloha: návrh „Blood for Blood“ (menu/index.html, nacitani/index.html, schváleno 17. 11.). Barvy z předlohy (:root).

const BFB_INK := Color("#e9dcc0")        # světlý pergamen – text
const BFB_INK_DIM := Color("#a8987a")    # položky nabídky, převod pořekadla
const BFB_INK_OFF := Color("#5f5546")    # nedostupná položka, verze
const BFB_RUBRIC := Color("#b8352a")     # rumělka – frakturová iniciála
const BFB_GOLD := Color("#c9a463")       # zlatá nabídky
const BFB_GOLD_NAC := Color("#b8924f")   # zlatá načítací obrazovky
const BFB_SEL_INK := Color("#2f1c0b")    # tmavý inkoust vybrané položky na pergamenu
const BFB_NOC := Color("#0d0a07")

static var _pisma := {}


## Písma předlohy: titul Grenze Gotisch, kapitálky Cormorant SC, text Cormorant Garamond, iniciála UnifrakturMaguntia
## (bez Č/Ř – záloha Grenze Gotisch). mezera = proložení písmen v px (letter-spacing předlohy).
static func pismo(druh: String, mezera := 0) -> Font:
	var key := "%s%d" % [druh, mezera]
	if _pisma.has(key):
		return _pisma[key]
	var f: Font
	if mezera != 0:
		var fv := FontVariation.new()
		fv.base_font = pismo(druh)
		fv.spacing_glyph = mezera
		f = fv
	else:
		var soubor: String = {"titul": "GrenzeGotisch-Bold", "sc": "CormorantSC-Medium", "text": "CormorantGaramond-Regular",
				"kurziva": "CormorantGaramond-Italic", "fraktura": "UnifrakturMaguntia-Regular"}[druh]
		var ff: FontFile = load("res://fonty/%s.ttf" % soubor)
		if druh == "fraktura":
			ff = ff.duplicate()
			ff.fallbacks = [load("res://fonty/GrenzeGotisch-Bold.ttf")]
		f = ff
	_pisma[key] = f
	return f


static func bfb_label(t: String, druh: String, fs: int, col: Color, mezera := 0) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_override("font", pismo(druh, mezera))
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_color", col)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


## Kosočtverec (čtverec otočený o 45°) – obrys, volitelně výplň.
static func kresli_kosoctverec(ci: CanvasItem, c: Vector2, a: float, col: Color, vypln := Color(0, 0, 0, 0)) -> void:
	var h := a * 0.7071
	var p := PackedVector2Array([c + Vector2(0, -h), c + Vector2(h, 0), c + Vector2(0, h), c + Vector2(-h, 0)])
	if vypln.a > 0.0:
		ci.draw_colored_polygon(p, vypln)
	p.append(p[0])
	ci.draw_polyline(p, col, 1.0, true)


## Tenká linka se zlatým kosočtvercem uprostřed (předloha .rule: 2× 120 px přechod do ztracena, mezera 14, kosočtverec 7).
class Linka extends Control:
	var barva := BFB_GOLD
	func _init(col: Color) -> void:
		barva = col
		custom_minimum_size = Vector2(120 * 2 + 14 * 2 + 9, 12)
		mouse_filter = Control.MOUSE_FILTER_IGNORE
	func _draw() -> void:
		var y := size.y * 0.5
		var c0 := Color(barva, 0.0)
		draw_polygon(PackedVector2Array([Vector2(0, y - 0.5), Vector2(120, y - 0.5), Vector2(120, y + 0.5), Vector2(0, y + 0.5)]),
				PackedColorArray([barva, c0, c0, barva]))
		var x2 := 120.0 + 28.0 + 9.0
		draw_polygon(PackedVector2Array([Vector2(x2, y - 0.5), Vector2(x2 + 120, y - 0.5), Vector2(x2 + 120, y + 0.5), Vector2(x2, y + 0.5)]),
				PackedColorArray([c0, barva, barva, c0]))
		Styl.kresli_kosoctverec(self, Vector2(120 + 14 + 4.5, y), 7.0, barva)


static var _zrno: Texture2D
## Jemné zrno (předloha: feTurbulence, opacity .16 overlay) – šum v teplé šedi, kreslí se dlaždicí s malou průhledností.
static func zrno() -> Texture2D:
	if _zrno == null:
		var n := FastNoiseLite.new()
		n.noise_type = FastNoiseLite.TYPE_VALUE
		n.frequency = 0.9
		n.fractal_octaves = 3
		var img := Image.create(256, 256, false, Image.FORMAT_RGBA8)
		for y in 256:
			for x in 256:
				var v := clampf(n.get_noise_2d(x, y) * 0.5 + 0.5, 0.0, 1.0)
				img.set_pixel(x, y, Color(v, v * 0.9, v * 0.8, absf(v - 0.5) * 2.0))
		_zrno = ImageTexture.create_from_image(img)
	return _zrno


## Přechod jako textura: body [[poloha 0–1, Color], …]; radial = kruh ze středu (roztáhne se na elipsu podle obdélníku).
static func prechod(body: Array, radial := false, svisle := false) -> GradientTexture2D:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array(body.map(func(b: Array) -> float: return float(b[0])))
	g.colors = PackedColorArray(body.map(func(b: Array) -> Color: return b[1]))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.width = 256
	t.height = 256
	if radial:
		t.fill = GradientTexture2D.FILL_RADIAL
		t.fill_from = Vector2(0.5, 0.5)
		t.fill_to = Vector2(1.0, 0.5)
	elif svisle:
		t.fill_from = Vector2(0, 0)
		t.fill_to = Vector2(0, 1)
	else:
		t.fill_from = Vector2(0, 0)
		t.fill_to = Vector2(1, 0)
	return t


## Vrstva přes celou plochu z textury (přechod, vinětace).
static func vrstva(parent: Node, tex: Texture2D, a := 1.0) -> TextureRect:
	var r := TextureRect.new()
	r.texture = tex
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.set_anchors_preset(Control.PRESET_FULL_RECT)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.modulate.a = a
	parent.add_child(r)
	return r


## Zrno a vinětace (předloha .grain + .vignette: elipsa 85 % × 80 %, tma .7 na kraji). stred_x = střed elipsy (0,55 nabídka, 0,5 načítání).
static func zrno_a_vineta(parent: Node, stred_x: float, tma: float) -> void:
	var z := TextureRect.new()
	z.texture = zrno()
	z.stretch_mode = TextureRect.STRETCH_TILE
	z.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	z.set_anchors_preset(Control.PRESET_FULL_RECT)
	z.mouse_filter = Control.MOUSE_FILTER_IGNORE
	z.modulate = Color(1, 1, 1, 0.07)
	parent.add_child(z)
	# elipsa s poloosami 85 % šířky a 80 % výšky: obdélník 2× tak velký se středem v (stred_x, 0,5)
	var v := TextureRect.new()
	v.texture = prechod([[0.0, Color(0, 0, 0, 0)], [0.55, Color(0, 0, 0, 0)], [1.0, Color(0, 0, 0, tma)]], true)
	v.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	v.stretch_mode = TextureRect.STRETCH_SCALE
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.anchor_left = stred_x - 0.85; v.anchor_right = stred_x + 0.85
	v.anchor_top = 0.5 - 0.8; v.anchor_bottom = 0.5 + 0.8
	parent.add_child(v)
	# mimo elipsu (rohy za obdélníkem nejsou) – rohy pokryje sama elipsa, protože obdélník přesahuje obrazovku


## Pořekadlo s červenou frakturovou iniciálou (předloha .saw / .quote) do RichTextLabel.
static func porekadlo(rt: RichTextLabel, ini: String, text: String, fs: int, fs_ini: int, col: Color) -> void:
	rt.clear()
	rt.push_font(pismo("fraktura"), fs_ini)
	rt.push_color(BFB_RUBRIC)
	rt.add_text(ini)
	rt.pop(); rt.pop()
	rt.push_font(pismo("kurziva"), fs)
	rt.push_color(col)
	rt.add_text(text)
	rt.pop(); rt.pop()
