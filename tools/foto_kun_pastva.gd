extends SceneTree
## Snimky pastvy kone z boku (Misa 27. 11. „kun zere s ohnutym krkem“): kun (scripts/kun.gd) na rovine bez sveta;
## klid, pastva (kun_zivy._pastva = 1 -> klip pastvy jizda.json zivy.pastva_klip) a autorsky klip „Eat“ jednorazove.
## Zaroven test kun_pastva: pri pastve je hlava aspon pastva_hlava_pod podilu vysky kohoutku pod koncem krku u hrudi
## a pred nim (vpred od hrudi, ne pod ni - oblouk krku), radek TEST KUN_PASTVA OK/CHYBA.
## Spusteni (render): tools/beh.sh fsedlo cmd xvfb-run -a -s "-screen 0 1200x800x24" godot --path . --rendering-driver opengl3
##   --rendering-method gl_compatibility --resolution 1200x800 -s res://tools/foto_kun_pastva.gd
## Snimky: build/foto_kun_pastva/{klid,pastva_klip,eat_*}.png

const Pravidla := preload("res://scripts/pravidla.gd")
var kun: CharacterBody3D
var cam: Camera3D
var t := 0
var faze := 0
const DIR := "res://build/foto_kun_pastva"


func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(DIR))
	var zem := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var bx := BoxShape3D.new()
	bx.size = Vector3(2000, 1, 2000)
	cs.shape = bx
	cs.position = Vector3(0, -0.5, 0)
	zem.add_child(cs)
	var pl := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(400, 400)
	pl.mesh = pm
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Color(0.35, 0.42, 0.22)
	pl.material_override = mt
	zem.add_child(pl)
	root.add_child(zem)
	var sl := DirectionalLight3D.new()
	sl.rotation_degrees = Vector3(-50, 30, 0)
	sl.shadow_enabled = true
	root.add_child(sl)
	var we := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.62, 0.74, 0.88)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.55, 0.58, 0.62)
	env.ambient_light_energy = 0.8
	we.environment = env
	root.add_child(we)
	var main := Node.new()
	main.name = "MainNahrada"
	root.add_child(main)
	kun = CharacterBody3D.new()
	kun.set_script(load("res://scripts/kun.gd"))
	root.add_child(kun)
	if not kun.setup(main, Vector3(0, 0.05, 0), 0.0):
		print("FOTO_PASTVA kun.setup selhal")
		quit(1)
		return
	cam = Camera3D.new()
	cam.fov = 40.0
	root.add_child(cam)
	cam.current = true


func _foto() -> void:
	var s: Vector3 = kun.call("sedlo_global")
	var b := kun.global_transform.basis
	cam.global_position = s + b * Vector3(-4.2, 0.2, -0.6)
	cam.look_at(s + b * Vector3(0, -0.6, -0.9), Vector3.UP)


func _zivy() -> Node:
	return kun.get("_zivy")


func _process(_d: float) -> bool:
	t += 1
	var zv := _zivy()
	match faze:
		0:
			if zv:
				zv.set("_pastva_cil", 0.0)
				zv.set("_pastva", 0.0)
				zv.set("_pastva_t", 999.0)
			kun.set("_past", 999.0)
			if t == 40:
				_foto()
			elif t == 44:
				_ulozit("klid")
				faze = 1
				t = 0
		1:
			# pastva skriptem (kun_zivy): hlava dole naplno
			if zv:
				zv.set("_pastva_cil", 1.0)
				zv.set("_pastva", 1.0)
				zv.set("_pastva_t", 999.0)
			if t == 120:
				_foto()
			elif t == 124:
				_ulozit("pastva_klip")
				_test()
				if zv:
					zv.set("_pastva_cil", 0.0)
					zv.set("_pastva", 0.0)
				kun.call("_jednou", "Eat")
				faze = 2
				t = 0
		2:
			if zv:
				zv.set("_pastva_cil", 0.0)
				zv.set("_pastva", 0.0)
				zv.set("_pastva_t", 999.0)
			for k in [20, 45, 70]:
				if t == k:
					_foto()
				elif t == k + 3:
					_ulozit("eat_%d" % k)
			if t == 80:
				print("FOTO_PASTVA hotovo")
				return true
	return false


func _ulozit(jm: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(ProjectSettings.globalize_path(DIR + "/" + jm + ".png"))
	print("FOTO_PASTVA %s" % jm)


func _test() -> void:
	var sk: Skeleton3D = kun.get("_kostra")
	var hl := sk.find_bone("horse Head")
	var kr := sk.find_bone("horse Neck")
	if hl < 0 or kr < 0:
		print("TEST KUN_PASTVA CHYBA  kosti horse Head / horse Neck nenalezeny")
		return
	var h := sk.global_transform * sk.get_bone_global_pose(hl).origin
	var n := sk.global_transform * sk.get_bone_global_pose(kr).origin
	var vpred := -kun.global_transform.basis.z
	var pred := (h - n).dot(vpred)
	var pod := n.y - h.y
	var kz: Dictionary = Pravidla.cti("jizda", "kun", "zivy")
	var ok := pod >= float(kz["test_pastva_pod_m"]) and pred >= float(kz["test_pastva_pred_m"])
	print("TEST KUN_PASTVA %s  hlava %.2f m pod koncem krku, %.2f m pred nim (min %.2f / %.2f)" % ["OK" if ok else "CHYBA", pod, pred, float(kz["test_pastva_pod_m"]), float(kz["test_pastva_pred_m"])])
