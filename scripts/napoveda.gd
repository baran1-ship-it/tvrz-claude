extends Control
## Napoveda v menu: na pergamenu bily ovladac a popisky ovladani dobovym pismem, odkazove cary k tlacitkum.

const INK := Color(0.23, 0.14, 0.07)
const INK_SOFT := Color(0.33, 0.22, 0.12, 0.85)
const RED := Color(0.55, 0.1, 0.06)

# [bod na ovladaci, strana, text]
const LABELS := [
	["LT", "L", "LT – zatím bez funkce"],
	["LB", "L", "LB – zatím bez funkce"],
	["LS", "L", "LS – chůze (levá páčka)"],
	["DPAD", "L", "D-pad – dolů brašna, doprava stavění"],
	["VIEW", "L", "View – nabídka, pauza"],
	["RT", "R", "RT – napnout luk, vystřelit"],
	["RB", "R", "RB – zatím bez funkce"],
	["MENU", "R", "Menu – nabídka, pauza"],
	["Y", "R", "Y – denní doba"],
	["B", "R", "B – zpět, let (pískoviště)"],
	["X", "R", "X – zapálit, zhasnout, odstranit"],
	["A", "R", "A – použít, jinak skok"],
	["RS", "R", "RS – rozhlížení (pravá páčka)"],
]
const FOOT := [
	"Dveře, padací most i mříž se ovládají zeleným tlačítkem A, když je na dosah nápis na svitku.",
	"V pískovišti dvakrát rychle skoč a můžeš létat: zeleným A stoupáš, červeným B klesáš.",
	"Světlo v ruce: A položit na zem, X zapálit nebo zhasnout, v brašně Y schovat.",
	"Na dotykové obrazovce: levý kruh chůze, tažení prstem rozhlížení, šipka skok.",
]

var font_title: Font
var font: Font
var parchment: Texture2D
var pad: Texture2D
var points := {}


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	font_title = load("res://fonts/GrenzeGotisch-Bold.ttf")
	font = load("res://fonts/GrenzeGotisch-Medium.ttf")
	parchment = load("res://obrazky/pergamen_velky.png")
	pad = load("res://obrazky/ovladac.png")
	var f := FileAccess.open("res://obrazky/ovladac.json", FileAccess.READ)
	if f:
		var d: Variant = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			points = d["body"]
	resized.connect(queue_redraw)
	visibility_changed.connect(queue_redraw)


func _draw() -> void:
	var s := get_viewport_rect().size
	var u := minf(s.x / 1600.0, s.y / 1000.0)          # meritko proti navrhu 1600x1000
	var mx := s.x * 0.03
	var my := s.y * 0.04
	var page := Rect2(mx, my, s.x - 2 * mx, s.y - 2 * my)
	draw_texture_rect(parchment, page, false)
	# nadpis
	var ty := page.position.y + 92 * u
	_center(font_title, "Ovládání", Vector2(s.x / 2, ty), int(64 * u), INK)
	draw_line(Vector2(s.x / 2 - 220 * u, ty + 18 * u), Vector2(s.x / 2 + 220 * u, ty + 18 * u), INK_SOFT, 2.0 * u)
	# ovladac uprostred
	var pw := 620.0 * u
	var ph := pw * float(pad.get_height()) / float(pad.get_width())
	var pr := Rect2(s.x / 2 - pw / 2, page.position.y + 170 * u, pw, ph)
	draw_texture_rect(pad, pr, false)
	# popisky ve dvou sloupcich, serazene podle vysky bodu
	var fs := int(27 * u)
	var lx := pr.position.x - 40 * u
	var rx := pr.end.x + 40 * u
	for side: String in ["L", "R"]:
		var items := []
		for e: Array in LABELS:
			if e[1] == side and points.has(e[0]):
				items.append(e)
		items.sort_custom(func(a: Array, b: Array) -> bool: return points[a[0]][1] < points[b[0]][1])
		var n := items.size()
		# vyska popisku = vyska bodu (vodorovne cary), pri prekryvu odsunout
		var ys := []
		var gap := fs * 1.7
		for i in n:
			var pt0: Array = points[items[i][0]]
			var y: float = pr.position.y + pt0[1] * pr.size.y + fs * 0.32
			if i > 0:
				y = maxf(y, ys[i - 1] + gap)
			ys.append(y)
		for i in range(n - 2, -1, -1):
			ys[i] = minf(ys[i], ys[i + 1] - gap)
		for i in n:
			var e: Array = items[i]
			var pt: Array = points[e[0]]
			var anchor := pr.position + Vector2(pt[0] * pr.size.x, pt[1] * pr.size.y)
			var y: float = ys[i]
			var txt: String = e[2]
			var w := _text_w(txt, fs)
			var tx := lx - w if side == "L" else rx
			var end := Vector2(lx + 8 * u if side == "L" else rx - 8 * u, y - fs * 0.32)
			var knee := Vector2(anchor.x + (-24 * u if side == "L" else 24 * u), end.y)
			draw_line(end, knee, INK_SOFT, 1.6 * u, true)
			draw_line(knee, anchor, INK_SOFT, 1.6 * u, true)
			draw_circle(anchor, 4.0 * u, RED)
			_text(txt, Vector2(tx, y), fs)
	# poznamky dole
	var fy := pr.end.y + 70 * u
	for line: String in FOOT:
		_center(font, line, Vector2(s.x / 2, fy), int(25 * u), INK)
		fy += 38 * u


const BADGE := {"A": Color(0.2, 0.55, 0.15), "B": Color(0.72, 0.12, 0.08), "X": Color(0.15, 0.32, 0.75), "Y": Color(0.8, 0.6, 0.05)}


func _pill_w(head: String, fs: int) -> float:
	return ThemeDB.fallback_font.get_string_size(head, HORIZONTAL_ALIGNMENT_LEFT, -1, int(fs * 0.62)).x + fs * 0.7


func _text_w(t: String, fs: int) -> float:
	var dash := t.find(" – ")
	if dash > 0:
		var head := t.substr(0, dash)
		var hw := fs * 1.1 if BADGE.has(head) else _pill_w(head, fs) + fs * 0.15
		return hw + font.get_string_size(t.substr(dash), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	return font.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x


func _text(t: String, p: Vector2, fs: int) -> void:
	# nazev ovladaciho prvku cervene jako v rukopisu; tlacitka A B X Y jako barevny kruh s citelnym pismenem
	var dash := t.find(" – ")
	if dash > 0:
		var head := t.substr(0, dash)
		var hw := 0.0
		if BADGE.has(head):
			var c := p + Vector2(fs * 0.5, -fs * 0.32)
			draw_circle(c, fs * 0.5, Color(0.08, 0.07, 0.06))
			draw_circle(c, fs * 0.5, BADGE[head], false, 2.0)
			var fb := ThemeDB.fallback_font
			var bw := fb.get_string_size(head, HORIZONTAL_ALIGNMENT_LEFT, -1, int(fs * 0.7)).x
			draw_string(fb, c + Vector2(-bw / 2, fs * 0.25), head, HORIZONTAL_ALIGNMENT_LEFT, -1, int(fs * 0.7), BADGE[head])
			hw = fs * 1.1
		else:
			# ostatni prvky pod skutecnym nazvem (LB, RT, LS, View...) v tmavem stitku jako na ovladaci
			var fb2 := ThemeDB.fallback_font
			var fs2 := int(fs * 0.62)
			var pw := _pill_w(head, fs)
			var r := Rect2(p + Vector2(0, -fs * 0.78), Vector2(pw, fs * 0.92))
			var sb := StyleBoxFlat.new()
			sb.bg_color = Color(0.08, 0.07, 0.06)
			sb.set_corner_radius_all(int(fs * 0.46))
			draw_style_box(sb, r)
			var tw := fb2.get_string_size(head, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2).x
			draw_string(fb2, Vector2(r.position.x + (pw - tw) / 2, r.position.y + fs * 0.66), head, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, Color(0.95, 0.93, 0.88))
			hw = pw + fs * 0.15
		draw_string(font, p + Vector2(hw, 0), t.substr(dash), HORIZONTAL_ALIGNMENT_LEFT, -1, fs, INK)
	else:
		draw_string(font, p, t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, INK)


func _center(f: Font, t: String, p: Vector2, fs: int, col: Color) -> void:
	var w := f.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	draw_string(f, Vector2(p.x - w / 2, p.y), t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)
