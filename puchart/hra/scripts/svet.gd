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
var vys_hi: PackedByteArray
var vys_lo: PackedByteArray
var vinfo: Dictionary
var kolize := {}          # "i_j" -> StaticBody3D
var kolize_do_m := 180.0  # vytvořit do, zrušit za + 60 m
var _t := 0.0
var _lod: Array
var _hy := 20.0
var _vysledky := []
var nacitani_ms := 0

func _ready() -> void:
	info = JSON.parse_string(FileAccess.get_file_as_string(DLAZDICE))
	vinfo = JSON.parse_string(FileAccess.get_file_as_string(VYSKY_JSON))
	if FileAccess.file_exists(VYSKY + "z"):   # zstd (APK: 8 MB -> menší), nastroje/godot/r16_zstd.gd
		var fz := FileAccess.open_compressed(VYSKY + "z", FileAccess.READ, FileAccess.COMPRESSION_ZSTD)
		var nn := int(vinfo["sirka"]) * int(vinfo["vyska"])
		vys_hi = fz.get_buffer(nn); vys_lo = fz.get_buffer(nn); fz.close()
	else:
		vysky = FileAccess.get_file_as_bytes(VYSKY)
	mat_zem = _material()
	# Dlaždice se staví z výškového souboru (8 MB) ve vláknech – v APK 0.1-ab dělaly hotové sítě 78 MB.
	# Je to jen síť z výšek (≈ 1,4 M vrcholů celkem), žádný výpočet světa; čas se měří (nacitani_ms).
	var t0 := Time.get_ticks_msec()
	var n: Array = info["pocet"]
	_lod = info["lod"]; _hy = info["hystereze_m"]
	_vysledky.resize(int(n[0]) * int(n[1]))
	var task := WorkerThreadPool.add_group_task(_postav_dlazdici, _vysledky.size(), -1, true, "teren")
	WorkerThreadPool.wait_for_group_task_completion(task)
	for k in _vysledky.size():
		_umisti(_vysledky[k])
	_vysledky.clear()
	nacitani_ms = Time.get_ticks_msec() - t0
	print("TEREN dlaždic %d za %d ms" % [int(n[0]) * int(n[1]), nacitani_ms])
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
	var i: int = r * int(vinfo["sirka"]) + c
	var u: int = (vys_hi[i] << 8 | vys_lo[i]) if vysky.is_empty() else vysky.decode_u16(i * 2)
	return float(u) / 200.0 + 300.0 - float(vinfo["pocatek_H"])

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


func _postav_dlazdici(k: int) -> void:
	var D: int = int(info["dlazdice_m"])
	var n: Array = info["pocet"]
	var i := k / int(n[1]); var j := k % int(n[1])
	var lods := []
	for li in _lod.size():
		var krok: int = int(_lod[li]["krok_m"])
		lods.append(_sit(i * D, j * D, D / krok, krok, 3.0 + 1.5 * krok))
	_vysledky[k] = lods

## Pravidelná síť nad výškami od (r0, c0), m×m buněk po krok, se sukní po obvodu (proti škvírám mezi LOD).
func _sit(r0: int, c0: int, m: int, krok: int, sukne: float) -> Array:
	var w := m + 1
	var x0: float = vinfo["x0_hra"]; var z0: float = vinfo["z0_hra"]
	var sirka: int = vinfo["sirka"]; var vyska_m: int = vinfo["vyska"]
	var pos := PackedVector3Array(); pos.resize(w * w + 4 * m * 2 + 8)
	var nor := PackedVector3Array(); nor.resize(pos.size())
	for a in w:
		for b in w:
			var r := r0 + a * krok; var c := c0 + b * krok
			var y := _v(r, c)
			var hx := _v(r, mini(c + 1, sirka - 1)) - _v(r, maxi(c - 1, 0))
			var hz := _v(mini(r + 1, vyska_m - 1), c) - _v(maxi(r - 1, 0), c)
			pos[a * w + b] = Vector3(x0 + c, y, z0 + r)
			nor[a * w + b] = Vector3(-hx * 0.5, 1.0, -hz * 0.5).normalized()
	var idx := PackedInt32Array()
	for a in m:
		for b in m:
			var q := a * w + b
			idx.append_array([q, q + 1, q + w, q + 1, q + w + 1, q + w])
	# sukně: obvod po směru, svisle dolů
	var ob := PackedInt32Array()
	for b in w: ob.append(b)
	for a in range(1, w): ob.append(a * w + m)
	for b in range(m - 1, -1, -1): ob.append(m * w + b)
	for a in range(m - 1, 0, -1): ob.append(a * w)
	ob.append(0)
	var base := w * w
	pos.resize(base + ob.size()); nor.resize(base + ob.size())
	for t in ob.size():
		pos[base + t] = pos[ob[t]] - Vector3(0, sukne, 0)
		nor[base + t] = nor[ob[t]]
	for t in ob.size() - 1:
		var a1 := ob[t]; var b1 := ob[t + 1]; var a2 := base + t; var b2 := base + t + 1
		idx.append_array([a1, b1, a2, b1, b2, a2, a1, a2, b1, b1, a2, b2])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = pos; arr[Mesh.ARRAY_NORMAL] = nor; arr[Mesh.ARRAY_INDEX] = idx
	return arr

func _umisti(lods: Array) -> void:
	for li in lods.size():
		var am := ArrayMesh.new()
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, lods[li])
		var mi := MeshInstance3D.new(); mi.mesh = am
		mi.material_override = mat_zem
		mi.visibility_range_begin = 0.0 if li == 0 else float(_lod[li - 1]["do_m"])
		mi.visibility_range_end = float(_lod[li]["do_m"])
		mi.visibility_range_begin_margin = _hy
		mi.visibility_range_end_margin = _hy
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if li <= 1 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
