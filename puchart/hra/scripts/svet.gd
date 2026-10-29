extends Node3D
## Svět Puchartu: načte pečené dlaždice terénu (nastroje/teren_dlazdice.py), nastaví LOD s hysterezí
## (Compatibility: tvrdé přepnutí, žádný průhledný fade – PDF kap. 9) a kolize jen v okolí hráče.
## Nic se tu nepočítá ze surových dat – Havran stavěl svět 83–110 s při startu, Puchart jen načítá.

const DLAZDICE := "res://dlazdice/dlazdice.json"
const VYSKY := "res://data/vysek.r16"
const VYSKY_JSON := "res://data/vysek.json"

@export var hrac: Node3D
var info: Dictionary
var mat_zem: ShaderMaterial
var vysky: PackedByteArray
var vinfo: Dictionary
var kolize := {}          # "i_j" -> StaticBody3D
var kolize_do_m := 180.0  # vytvořit do, zrušit za + 60 m
var _t := 0.0

func _ready() -> void:
	info = JSON.parse_string(FileAccess.get_file_as_string(DLAZDICE))
	vinfo = JSON.parse_string(FileAccess.get_file_as_string(VYSKY_JSON))
	vysky = FileAccess.get_file_as_bytes(VYSKY)
	mat_zem = _material()
	var lod: Array = info["lod"]
	var hy: float = info["hystereze_m"]
	for d in info["dlazdice"]:
		var s: Node3D = load("res://dlazdice/" + d["soubor"]).instantiate()
		add_child(s)
		for li in lod.size():
			var mi := s.get_node("LOD%d" % li) as MeshInstance3D
			mi.material_override = mat_zem
			mi.visibility_range_begin = 0.0 if li == 0 else float(lod[li - 1]["do_m"])
			mi.visibility_range_end = float(lod[li]["do_m"])
			mi.visibility_range_begin_margin = hy
			mi.visibility_range_end_margin = hy
			mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
			# stín jen blízký terén (rozpocty.json stiny.dosah_m); vzdálené LOD stín nevrhají
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if li <= 1 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var o: Node3D = load("res://dlazdice/" + info["obzor"]["soubor"]).instantiate()
	add_child(o)
	var om := o.get_node("OBZOR") as MeshInstance3D
	om.material_override = mat_zem
	om.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func _material() -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/zem.gdshader")
	m.set_shader_parameter("pudy_a", load("res://textury/pudy_a.png"))
	m.set_shader_parameter("pudy_n", load("res://textury/pudy_n.png"))
	m.set_shader_parameter("maska", load("res://textury/maska_vysek.png"))
	m.set_shader_parameter("sum", load("res://textury/sum.png"))
	var pu: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/pudy.json"))
	var vel := PackedFloat32Array()
	for v in pu["vrstvy"]:
		vel.append(float(v["velikost_m"]))
	m.set_shader_parameter("velikost_m", vel)
	return m

## Výška terénu ve hře (bilineárně z r16) – pro pokládání a start hráče.
func vyska(x: float, z: float) -> float:
	var w: int = vinfo["sirka"]; var h: int = vinfo["vyska"]
	var c := clampf(x - float(vinfo["x0_hra"]), 0.0, w - 1.001)
	var r := clampf(z - float(vinfo["z0_hra"]), 0.0, h - 1.001)
	var c0 := int(c); var r0 := int(r); var fc := c - c0; var fr := r - r0
	var a := _v(r0, c0); var b := _v(r0, c0 + 1); var cc := _v(r0 + 1, c0); var d := _v(r0 + 1, c0 + 1)
	return lerpf(lerpf(a, b, fc), lerpf(cc, d, fc), fr)

func _v(r: int, c: int) -> float:
	var i: int = (r * int(vinfo["sirka"]) + c) * 2
	return float(vysky.decode_u16(i)) / 200.0 + 300.0 - float(vinfo["pocatek_H"])

func _process(delta: float) -> void:
	_t += delta
	if _t < 0.25 or hrac == null:
		return
	_t = 0.0
	_kolize_okoli(hrac.global_position)

## Kolize: HeightMapShape3D po dlaždicích, jen kolem hráče (Havran rozpocty kolize bunka 32 m – tady dlaždice 250 m
## s krokem 1 m; jedna dlaždice = 63 k výšek, vytvoření ~ms). Max. jedna nová za tick (žádné nárazové práce, PDF kap. 13).
func _kolize_okoli(p: Vector3) -> void:
	var D: float = info["dlazdice_m"]
	var n: Array = info["pocet"]
	var x0: float = vinfo["x0_hra"]; var z0: float = vinfo["z0_hra"]
	var nove := 0
	for i in int(n[0]):
		for j in int(n[1]):
			var stred := Vector2(x0 + (j + 0.5) * D, z0 + (i + 0.5) * D)
			var d := maxf(absf(p.x - stred.x), absf(p.z - stred.y)) - D * 0.5
			var k := "%d_%d" % [i, j]
			if d < kolize_do_m and not kolize.has(k) and nove == 0:
				kolize[k] = _kolize_dlazdice(i, j); nove += 1
			elif d > kolize_do_m + 60.0 and kolize.has(k):
				kolize[k].queue_free(); kolize.erase(k)

func _kolize_dlazdice(i: int, j: int) -> StaticBody3D:
	var D: int = int(info["dlazdice_m"])
	var hm := HeightMapShape3D.new()
	hm.map_width = D + 1; hm.map_depth = D + 1
	var data := PackedFloat32Array(); data.resize((D + 1) * (D + 1))
	for r in D + 1:
		for c in D + 1:
			data[r * (D + 1) + c] = _v(i * D + r, j * D + c)
	hm.map_data = data
	var b := StaticBody3D.new()
	var cs := CollisionShape3D.new(); cs.shape = hm
	b.add_child(cs)
	add_child(b)
	b.position = Vector3(float(vinfo["x0_hra"]) + j * D + D * 0.5, 0.0, float(vinfo["z0_hra"]) + i * D + D * 0.5)
	return b
