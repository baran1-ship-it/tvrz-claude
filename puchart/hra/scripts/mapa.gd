extends CanvasLayer
## Mapa na pergamenu (nastroje/mapa.py, styl KCD2 a Havrana scripts/mapa.gd): celá obrazovka, poloha a směr hráče
## jako šipka. Otevírá tlačítko „Mapa“ v procházce nebo klávesa M / Back na ovladači; zavírá totéž nebo dotyk.
var hrac: Node3D
var info: Dictionary
var _r: TextureRect
var _sipka: Polygon2D
var otevrena := false

func _ready() -> void:
	layer = 20
	info = JSON.parse_string(FileAccess.get_file_as_string("res://data/mapa.json"))
	var bg := ColorRect.new(); bg.color = Color(0.08, 0.06, 0.04, 0.92); bg.set_anchors_preset(Control.PRESET_FULL_RECT); add_child(bg)
	_r = TextureRect.new(); _r.texture = load("res://textury/ui/mapa.png")
	_r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; _r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_r.set_anchors_preset(Control.PRESET_FULL_RECT); add_child(_r)
	_sipka = Polygon2D.new(); _sipka.polygon = PackedVector2Array([Vector2(0, -16), Vector2(10, 12), Vector2(0, 6), Vector2(-10, 12)])
	_sipka.color = Color(0.7, 0.08, 0.05); add_child(_sipka)
	visible = false

func prepni() -> void:
	otevrena = not otevrena; visible = otevrena

func _unhandled_input(e: InputEvent) -> void:
	if (e is InputEventKey and e.pressed and e.keycode == KEY_M) or (e is InputEventJoypadButton and e.pressed and e.button_index == JOY_BUTTON_BACK):
		prepni()
	elif otevrena and e is InputEventScreenTouch and e.pressed:
		prepni()

func _process(_d: float) -> void:
	if not otevrena or hrac == null: return
	var vel: Vector2 = get_viewport().get_visible_rect().size
	var tw: float = info["sirka"]; var th: float = info["vyska"]
	var s := minf(vel.x / tw, vel.y / th); var o := (vel - Vector2(tw, th) * s) * 0.5
	var p := hrac.global_position
	_sipka.position = o + Vector2((p.x - float(info["x0"])) / float(info["px_m"]), (p.z - float(info["z0"])) / float(info["px_m"])) * s
	_sipka.rotation = -hrac.global_rotation.y
