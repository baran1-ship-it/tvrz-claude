extends Control
## Nabídka akcí u předmětu na dosah (Míša 12. 11.: „světelné zdroje nejdou pustit, chci, aby předměty měly funkce jako
## v Havranovi – louče, svíce, bedny, sudy“). Převzato z Havrana scripts/main.gd _build_acts: předmět, na který se hráč
## dívá (predmety.nearest), a jeho akce use / use2 / use3 (zapálit – zhasnout, otevřít – vzít, sednout…) jako tlačítka
## svitku (styl.gd) dole uprostřed. Dveře a padací mosty mají vlastní tlačítko (dvere.gd) – když jsou na dosah, nabídka mlčí.
var proch: Node
var _use := {}
var _tl: Array = []        # tlačítka řádků
var _klice: Array = []
var _font: Font

func zacni(p: Node) -> void:
	proch = p
	_font = load("res://fonty/GrenzeGotisch-Medium.ttf")
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); mouse_filter = Control.MOUSE_FILTER_IGNORE   # jen kotvy bez okrajů = 0×0, tlačítka byla mimo obrazovku (chyba louče)
	for i in 3:
		var b := Button.new(); b.custom_minimum_size = Vector2(300, 80); Styl.tlacitko_pruh(b, _font, 28, i)
		b.anchor_left = 0.5; b.anchor_right = 0.5; b.anchor_top = 1.0; b.anchor_bottom = 1.0
		b.offset_left = -150; b.offset_right = 150; b.offset_top = -170 - i * 92; b.offset_bottom = -90 - i * 92
		b.visible = false; b.pressed.connect(_stisk.bind(i)); add_child(b); _tl.append(b)

func _process(_d: float) -> void:
	if Engine.get_process_frames() % 6 != 0: return
	var hv: Node = proch.get("hv"); var P: Node = hv.get("predmety") if hv else null
	var cam := get_viewport().get_camera_3d()
	if P == null or cam == null or String(P.get("placing")) != "" or (proch.get("dvere") != null and String(proch.dvere._blizko) != ""):
		_skryj(); return
	_use = P.nearest(cam)
	if _use.is_empty(): _skryj(); return
	var rady: Array = []
	var t1: String = P.use_label(_use); if t1 != "": rady.append([t1, "use"])
	var t2: String = P.use2_label(_use) if String(P.get("held_id")) == "" else ""; if t2 != "": rady.append([t2, "use2"])
	var t3: String = P.use3_label(_use); if t3 != "": rady.append([t3, "use3"])
	_klice = []
	for i in _tl.size():
		var b: Button = _tl[i]
		if i < rady.size(): b.text = rady[i][0]; b.visible = true; _klice.append(rady[i][1])
		else: b.visible = false

func _skryj() -> void:
	for b in _tl: (b as Button).visible = false
	_klice = []

func _stisk(i: int) -> void:
	if i >= _klice.size() or _use.is_empty(): return
	var P: Node = proch.hv.predmety
	match String(_klice[i]):
		"use": P.use(_use)
		"use2": P.use2(_use)
		"use3": P.use3(_use)
	_skryj()
