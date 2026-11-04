## Prototyp travy GPU (Misa 4. 11.: „vezmi hotova reseni“, docs/rozpracovane/trava_hotova_reseni.md): pevna mrizka trsu
## kolem kamery (princip forum Godot vlakno 141821, „normalized“) ve trech prstencich, kazdy jeden MultiMesh, uzel se
## kazdy snimek prichyti na svuj krok; poloha, hustota a vyska trsu dela shader (shaders/trava_gpu.gdshader) z textur
## upecenych jednou z louka._vzorek. Pri pohybu se nic nepocita. A/B: louka.gd v oblastech nesazi trsy vrstvy 0.
extends Node3D

const Pravidla := preload("res://scripts/pravidla.gd")

var main: Node
var louka: Node
var zapnuto := false
var _obl: Array = []              # [{rect, hust: ImageTexture, vys: ImageTexture, uzly: [MultiMeshInstance3D]}]
var _peceni := -1
var _hotovo := false


func setup(m: Node) -> void:
	main = m
	louka = m.get_node_or_null("Louka")
	if louka == null:
		return
	_peceni = WorkerThreadPool.add_task(_pec, false)


## Peceni hustoty a vysky (vlakno): totez pravidlo jako louka (vzorek, prah), zadna druha definice.
func _pec() -> void:
	var cfg: Dictionary = Pravidla.soubor("trava_gpu")
	var k := float(cfg["pecka_krok_m"])
	var t0 := Time.get_ticks_msec()
	for o: Array in cfg["oblasti"]:
		var r := Rect2(float(o[0]), float(o[1]), float(o[2]), float(o[3]))
		var nx := int(r.size.x / k)
		var nz := int(r.size.y / k)
		var hi := Image.create(nx, nz, false, Image.FORMAT_R8)
		var vi := Image.create(nx, nz, false, Image.FORMAT_RF)
		for j in nz:
			for i in nx:
				var px := r.position.x + (i + 0.5) * k
				var pz := r.position.y + (j + 0.5) * k
				var v: Vector3 = louka._vzorek(px, pz)
				var d := 0.0
				if v.x >= louka._prah(px, pz) and not louka._nizka(px, pz):
					d = clampf(v.x * 1.6 * (1.0 + 0.5 * louka.Svet.divokost(px, pz)), 0.0, 1.0)
				hi.set_pixel(i, j, Color(d, 0, 0))
				vi.set_pixel(i, j, Color(v.y, 0, 0))
		_obl.append({"rect": r, "hi": hi, "vi": vi})
	print("TRAVA_GPU upeceno %d oblasti za %d ms" % [_obl.size(), Time.get_ticks_msec() - t0])


func _postav() -> void:
	var cfg: Dictionary = Pravidla.soubor("trava_gpu")
	var trs: Mesh = louka._trs
	var zakl := trs.surface_get_material(0) as ShaderMaterial
	var sh: Shader = load("res://shaders/trava_gpu.gdshader")
	for ob: Dictionary in _obl:
		var ht := ImageTexture.create_from_image(ob["hi"])
		var vt := ImageTexture.create_from_image(ob["vi"])
		var r: Rect2 = ob["rect"]
		ob["uzly"] = []
		var kid := 0
		for pr: Array in cfg["prstence"]:
			var kr := float(pr[0])
			var rout := float(pr[2])
			var n := int(ceil(rout * 2.0 / kr)) + 1
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_custom_data = true
			var m := trs.duplicate() as Mesh
			var mat := ShaderMaterial.new()
			mat.shader = sh
			for p in zakl.shader.get_shader_uniform_list():
				var nm := String(p["name"])
				mat.set_shader_parameter(nm, zakl.get_shader_parameter(nm))
			mat.set_shader_parameter("z_custom", false)
			mat.set_shader_parameter("hust_mapa", ht)
			mat.set_shader_parameter("vyska_mapa", vt)
			mat.set_shader_parameter("mapa_rect", Vector4(r.position.x, r.position.y, r.size.x, r.size.y))
			mat.set_shader_parameter("krok", kr)
			mat.set_shader_parameter("krok_id", kid)
			mat.set_shader_parameter("r_in", float(pr[1]))
			mat.set_shader_parameter("r_out", rout)
			# vetsi krok = ridsi mrizka: trs vetsi, aby pokryl totez (jako louka: zdalky mene a vetsich trsu)
			mat.set_shader_parameter("velikost", sqrt(kr / 0.36))
			m.surface_set_material(0, mat)
			mm.mesh = m
			mm.instance_count = n * n
			var i := 0
			for a in n:
				for b in n:
					mm.set_instance_transform(i, Transform3D())
					mm.set_instance_custom_data(i, Color((a - n / 2) * kr, (b - n / 2) * kr, 0.0, 0.0))
					i += 1
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mmi.custom_aabb = AABB(Vector3(-rout - 2.0, -200.0, -rout - 2.0), Vector3(rout * 2.0 + 4.0, 600.0, rout * 2.0 + 4.0))
			mmi.set_meta("krok", kr)
			mmi.set_meta("r_out", rout)
			mmi.visible = false
			add_child(mmi)
			(ob["uzly"] as Array).append(mmi)
			kid += 1
	_hotovo = true


## Zapnout / vypnout (Nastaveni, varianta merici trasy). Louka v oblastech nesazi trsy vrstvy 0 a buňky se prestavi.
func zapni(on: bool) -> void:
	zapnuto = on
	if louka == null:
		return
	var rects: Array[Rect2] = []
	if on:
		for ob: Dictionary in _obl:
			rects.append(ob["rect"])
	louka.gpu_oblasti(rects)
	for ob: Dictionary in _obl:
		for u: Node3D in ob.get("uzly", []):
			u.visible = false


func _process(_d: float) -> void:
	if not _hotovo:
		if _peceni >= 0 and WorkerThreadPool.is_task_completed(_peceni):
			WorkerThreadPool.wait_for_task_completion(_peceni)
			_peceni = -1
			_postav()
			zapni(zapnuto)
		return
	if not zapnuto:
		return
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var c := cam.global_position
	for ob: Dictionary in _obl:
		var r: Rect2 = ob["rect"]
		for u: Node3D in ob["uzly"]:
			var kr := float(u.get_meta("krok"))
			var ro := float(u.get_meta("r_out"))
			u.visible = r.grow(ro).has_point(Vector2(c.x, c.z))
			if u.visible:
				u.global_position = Vector3(snappedf(c.x, kr), 0.0, snappedf(c.z, kr))
