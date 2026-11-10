extends Node
## Propojka Havranových skriptů (menu_hrace, predmety, dovednosti – převzato z větve Havrana beze změny kódu) na Puchart
## (Míša 10. 11.: „Havran už to má hotové“). Havranův main poskytoval life (zvuky, světla, ohně), hud (hlášky), player,
## day, mode, svet, info, udalost/open_container/offer_sleep/sleep_until – tady jejich nejmenší náhrada nad Puchartem.
var mode := "pribeh"           # pribeh | piskoviste (výběr v hlavní nabídce)
var player: CharacterBody3D
var predmety: Node
var menu_hrace: CanvasLayer
var dovednosti: Node
var world: Node3D = null       # Havran: skrývání světa uvnitř budov (portály) – v Puchartu vypnuto
var svet = null                # Havranův svět (voda, žebříky, vybavení vsi) – v Puchartu není
var info := {"use": []}
var day := {"current": "den"}
var hud: CanvasLayer
var life: Node

class Hud extends CanvasLayer:
	var _l: Label
	func _ready() -> void:
		layer = 25; process_mode = Node.PROCESS_MODE_ALWAYS
		_l = Label.new(); _l.position = Vector2(40, 90); _l.add_theme_font_size_override("font_size", 30)
		_l.add_theme_color_override("font_outline_color", Color.BLACK); _l.add_theme_constant_override("outline_size", 8); add_child(_l)
	func toast(t: String, dob := 2.5) -> void:
		_l.text = t; _l.modulate.a = 1.0
		var tw := create_tween(); tw.tween_interval(dob); tw.tween_property(_l, "modulate:a", 0.0, 0.6)

class Life extends Node:
	const FIRE_COL := Color(1.0, 0.64, 0.38)
	var rooms: Array = []
	var room_name := ""
	var lights: Array = []
	var _sounds := {}
	var hl: Node
	func sfx(_jm: String, _db := 0.0) -> void: pass   # zvuky menu z Havrana Puchart zatím nemá
	func _candle_flame(pos: Vector3, h := 0.07) -> Sprite3D:   # Havran: plamínek svíce (sprite); textura měkký přechod
		var s := Sprite3D.new(); var gt := GradientTexture2D.new(); gt.fill = GradientTexture2D.FILL_RADIAL
		gt.fill_from = Vector2(0.5, 0.62); gt.fill_to = Vector2(0.5, 0.05); gt.width = 64; gt.height = 64
		var gr := Gradient.new(); gr.set_color(0, Color(1, 1, 1, 1)); gr.set_color(1, Color(1, 1, 1, 0)); gt.gradient = gr
		s.texture = gt; s.pixel_size = h / 64.0; s.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y; s.shaded = false
		s.alpha_cut = SpriteBase3D.ALPHA_CUT_DISABLED; s.modulate = Color(1.0, 0.75, 0.4, 0.95); s.position = pos + Vector3(0, h * 0.35, 0)
		s.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(s); return s
	func _flames(pos: Vector3, size: float, amount: int, life_s: float) -> CPUParticles3D:
		var p: CPUParticles3D = hl._plamen_castice(size, amount, life_s); p.position = pos; add_child(p); return p

func setup(hlavni: Node3D, hrac: CharacterBody3D) -> void:
	player = hrac
	hud = Hud.new(); add_child(hud)
	life = Life.new(); life.hl = hlavni; add_child(life)
	dovednosti = load("res://scripts/dovednosti.gd").new(); dovednosti.name = "Dovednosti"; add_child(dovednosti)
	dovednosti.setup(self, "mlady")
	predmety = load("res://scripts/predmety.gd").new(); predmety.name = "PredmetyHra"; add_child(predmety)
	predmety.setup(self, hlavni)
	menu_hrace = load("res://scripts/menu_hrace.gd").new(); menu_hrace.main = self; menu_hrace.P = predmety; add_child(menu_hrace)

func udalost(id: String, data := {}) -> void:
	if dovednosti: dovednosti.udalost(id, data)
func open_container(rec: Dictionary) -> void: menu_hrace.show_page("vymena", rec)
func offer_sleep() -> void: hud.toast("Spánek zatím není")
func sleep_until(_kdy: String) -> void: pass
