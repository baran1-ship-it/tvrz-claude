extends SceneTree
## Snimky sedla z obou boku (Misa 0.99994 r. 62 „sedlo stale zapustene / sikme z jedne strany“): kun (scripts/kun.gd)
## na rovine bez sveta, slunce a obloha; levy a pravy bok ve stani a v kroku (kun jde sam po primce).
## Spusteni (render): tools/beh.sh fsedlo cmd xvfb-run -a -s "-screen 0 1200x800x24" godot --path . --rendering-driver opengl3
##   --rendering-method gl_compatibility --resolution 1200x800 -s res://tools/foto_sedlo.gd
## Snimky: build/foto_sedlo/{stani,krok}_{levy,pravy}.png

var kun: CharacterBody3D
var cam: Camera3D
var t := 0
var faze := 0
const DIR := "res://build/foto_sedlo"


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
		print("FOTO_SEDLO kun.setup selhal")
		quit(1)
		return
	cam = Camera3D.new()
	cam.fov = 40.0
	root.add_child(cam)
	cam.current = true


func _foto(jm: String, bok: float) -> void:
	# kamera z boku kone (bok -1 levy, +1 pravy; kun hlavou k -Z), mirne shora, mirena na sedlo
	var s: Vector3 = kun.call("sedlo_global")
	var b := kun.global_transform.basis
	cam.global_position = s + b * Vector3(bok * 3.2, 0.9, 0.3)
	cam.look_at(s + Vector3(0, -0.15, 0), Vector3.UP)


func _process(_d: float) -> bool:
	t += 1
	match faze:
		0:
			if t == 40:
				_foto("stani_levy", -1.0)
			elif t == 46:
				_ulozit("stani_levy")
				_foto("stani_pravy", 1.0)
			elif t == 52:
				_ulozit("stani_pravy")
				# neviditelny jezdec (jako test kun_klid) - packa vpred = krok; sedlo zustane videt
				var sc := GDScript.new()
				sc.source_code = "extends Node3D\nvar move_input := Vector2.ZERO\nvar fly_up := false\nvar _jump := false\nvar yaw := 0.0\nvar pitch := 0.0\nvar na_koni = null\nvar velocity := Vector3.ZERO\nfunc look(a: float, b: float) -> void:\n\tyaw += a\n"
				sc.reload()
				var jz := Node3D.new()
				jz.set_script(sc)
				root.add_child(jz)
				kun.set("drzet_cestu", false)
				kun.set("jezdec", jz)
				jz.set("na_koni", kun)
				jz.set("yaw", float(kun.get("_yaw")))
				jz.set("move_input", Vector2(0, 1))
				faze = 1
				t = 0
		1:
			# krok: kun jde sam (cil pred nim), kamera s nim
			if t == 90:
				_foto("krok_levy", -1.0)
			elif t == 92:
				_ulozit("krok_levy")
				_foto("krok_pravy", 1.0)
			elif t == 94:
				_ulozit("krok_pravy")
				print("FOTO_SEDLO hotovo")
				return true
	return false


func _ulozit(jm: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(ProjectSettings.globalize_path(DIR + "/" + jm + ".png"))
	print("FOTO_SEDLO %s" % jm)
