extends SceneTree
## Rychly snimek jedne postavy bez sveta (postavy_plan krok 2-3: ladeni predmetu v rukou a sedu, sekundy misto
## 15 min stavby sveta). Postava se sklada jako ve hre (scripts/lide.gd nova_postava, ruce), klip cinnosti v case,
## kamera kolem postavy. Spousti se jen pres tools/beh.sh:
##   TVRZ_FOTO_POSTAVA="soubor.png;cinnost;klip;cas_s;uhel_st;vzdalenost_m;vyska_cile_m[;sedak]|..." \
##   tools/beh.sh fp cmd xvfb-run -a -s "-screen 0 900x900x24" godot --path . --rendering-driver opengl3 \
##       --rendering-method gl_compatibility --resolution 900x900 -s res://tools/foto_postava.gd
## sedak = id predmetu z katalogu: postava sedi na nem podle postavy.json sedani (vyska_klipu_m, pred_m); postel (lehat)
## = postava lezi podle postavy.json spani.
## Vypise DIAG radky: meritko kostry, rozmery predmetu, poloha panve a rukou v klipu (pro data drzeni a sedani).

const Lide := preload("res://scripts/lide.gd")


func _initialize() -> void:
	_beh.call_deferred()


func _beh() -> void:
	var koren := Node3D.new()
	root.add_child(koren)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.55, 0.62, 0.7)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.6, 0.6, 0.65)
	env.ambient_light_energy = 0.7
	var we := WorldEnvironment.new()
	we.environment = env
	koren.add_child(we)
	var sl := DirectionalLight3D.new()
	sl.rotation_degrees = Vector3(-50, 35, 0)
	sl.shadow_enabled = true
	koren.add_child(sl)
	var zem := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(6, 6)
	zem.mesh = pm
	var zm := StandardMaterial3D.new()
	zm.albedo_color = Color(0.35, 0.4, 0.25)
	zem.material_override = zm
	koren.add_child(zem)
	var kam := Camera3D.new()
	kam.fov = 40.0
	koren.add_child(kam)
	kam.current = true
	var lide: Node3D = Lide.new()
	koren.add_child(lide)
	var P: Dictionary = Lide.P
	# obyvatel z dat (vzhled podle postavy_vzhled.json): TVRZ_FOTO_KDO, vychozi lamac_1
	var kdo := OS.get_environment("TVRZ_FOTO_KDO") if OS.has_environment("TVRZ_FOTO_KDO") else "lamac_1"
	var o: Dictionary = (P["obyvatele"] as Array).filter(func(x: Dictionary) -> bool: return String(x["id"]) == kdo)[0]
	var c: Dictionary = lide.nova_postava(o)
	var u: Node3D = c["uzel"]
	u.scale = Vector3.ONE
	var kostra: Skeleton3D = c["kostra"]
	var ap: AnimationPlayer = c["ap"]
	print("DIAG kostra meritko %s" % kostra.global_transform.basis.get_scale())
	var kat: Dictionary = Lide.katalog()
	for id: String in P["drzeni"]:
		if id.begins_with("_"):
			continue
		var ps: PackedScene = load(Lide.PREDMETY_DIR + id + ".glb")
		var t: Node3D = ps.instantiate() if ps else null
		if t:
			var ab := AABB()
			var prvni := true
			for g in t.find_children("*", "MeshInstance3D", true, false):
				var mi := g as MeshInstance3D
				var a2: AABB = mi.transform * mi.get_aabb()
				ab = a2 if prvni else ab.merge(a2)
				prvni = false
			print("DIAG predmet %s aabb %s rozmer kat %s" % [id, ab, (kat.get(id, {}) as Dictionary).get("rozmer", [])])
			t.free()
	var sedak_uzel: Node3D = null
	for one: String in OS.get_environment("TVRZ_FOTO_POSTAVA").split("|", false):
		var a := one.split(";")
		var cn: Dictionary = P["cinnosti"].get(a[1], {})
		c["cn"] = cn
		c["klip"] = ""
		u.position = Vector3.ZERO
		u.rotation = Vector3.ZERO
		if sedak_uzel:
			sedak_uzel.free()
			sedak_uzel = null
		if a.size() > 7 and a[7] != "" and bool((kat.get(a[7], {}) as Dictionary).get("lehat", false)):
			# postel: postava lezi podle postavy.json spani
			var spn: Dictionary = P["spani"]
			sedak_uzel = (load(Lide.PREDMETY_DIR + a[7] + ".glb") as PackedScene).instantiate()
			koren.add_child(sedak_uzel)
			var pz: Array = spn["posun"]
			u.rotation.y = deg_to_rad(float(spn["otoceni_st"]))
			u.position = Basis(Vector3.UP, u.rotation.y) * Vector3(float(pz[0]), Lide.nad_postel(a[7]), float(pz[1]))
		elif a.size() > 7 and a[7] != "":
			var sd: Dictionary = P["sedani"]
			var rz: Array = (kat.get(a[7], {}) as Dictionary).get("rozmer", [0.4, 0.45, 0.4])
			sedak_uzel = (load(Lide.PREDMETY_DIR + a[7] + ".glb") as PackedScene).instantiate()
			koren.add_child(sedak_uzel)
			sedak_uzel.position = Vector3(0, 0, -float(sd["pred_m"]))
			u.position.y = float(rz[1]) - float(sd["vyska_klipu_m"])
		lide.call("_klip", c, a[2], 1.0)
		# play() se v rucnim rezimu projevi az pri advance; pak cas klipu (a za prolinanim)
		# snimek bez prolinani z predchoziho klipu (play v rucnim rezimu jinak ukazal predchozi pozu)
		ap.stop()
		ap.play(a[2], 0.0)
		ap.seek(float(a[3]), true)
		ap.advance(0.0)
		for i in 3:
			await process_frame
		var pel := kostra.find_bone("pelvis")
		var hr := kostra.find_bone("hand_r")
		var hl := kostra.find_bone("hand_l")
		var gp := func(b: int) -> Vector3: return kostra.global_transform * kostra.get_bone_global_pose(b).origin
		print("DIAG %s klip %s t %.2f panev %s ruka_r %s ruka_l %s" % [a[0], a[2], float(a[3]), gp.call(pel), gp.call(hr), gp.call(hl)])
		var hb: Transform3D = kostra.global_transform * kostra.get_bone_global_pose(hr)
		print("DIAG %s ruka_r osy x %s y %s z %s" % [a[0], hb.basis.x.normalized(), hb.basis.y.normalized(), hb.basis.z.normalized()])
		var uh := deg_to_rad(float(a[4]))
		var dist := float(a[5])
		var cil := Vector3(0, float(a[6]), 0)
		kam.position = cil + Vector3(sin(uh), 0.15, cos(uh)) * dist
		kam.look_at(cil)
		for i in 4:
			await process_frame
		root.get_viewport().get_texture().get_image().save_png(a[0])
		print("FOTO %s" % a[0])
	quit()
