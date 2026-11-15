extends Node
## DOČASNÝ ladicí skript (smazat): snímky ohňů v jednom běhu. PUCHART_FOTO_DIR = složka výstupu.
var h: Node
var out := ""

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	h = get_parent(); out = OS.get_environment("PUCHART_FOTO_DIR")
	h._foto = ""   # nekončit po 40 snímcích
	var oh: Node = h.get_node("Ohne")
	if not bool(oh.pripraveno): await oh.hotovo
	var cam: Camera3D = h.cam if h.get("cam") else get_viewport().get_camera_3d()
	cam = get_viewport().get_camera_3d()
	var ss := get_viewport().get_world_3d().direct_space_state
	# výpis pro modeláře
	for o: Dictionary in oh.ohne:
		var u: Node3D = o["uzel"]; var dum: Node3D = u.get_parent()
		print("FOTO_INFO %s | %s | uzel %s | dum %s | zaklad %s | ven %s | lokalne %s" % [o["nazev"], o["druh"], u.name, dum.name, o["zaklad"], o["ven"], dum.global_transform.affine_inverse() * (o["zaklad"] as Vector3)])
	for x in [52.0, 56.2]:
		var r := ss.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 30, 146.6), Vector3(x, 0, 146.6)))
		print("FOTO_INFO hradB paprsek x %s: %s" % [x, r.get("position")])
		var y := 30.0
		while true:
			var q := ss.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, y, 146.6), Vector3(x, 0, 146.6)))
			if q.is_empty(): break
			print("FOTO_INFO   hit y %.2f" % (q["position"] as Vector3).y); y = (q["position"] as Vector3).y - 0.05
		for zz in [146.6]:
			for dirz in [-1.0, 1.0]:
				var q2 := ss.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 16.0, zz), Vector3(x, 16.0, zz + dirz * 10)))
				print("FOTO_INFO   stěna z směr %s: %s" % [dirz, q2.get("position")])
	for dirx in [-1.0, 1.0]:
		var q3 := ss.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(54, 16.0, 146.6), Vector3(54 + dirx * 12, 16.0, 146.6)))
		print("FOTO_INFO   hradB stěna x směr %s: %s" % [dirx, q3.get("position")])
	var sh: Array = []   # [soubor, cam, cil, hodina]
	var pk: Dictionary = {}; var pa: Dictionary = {}
	for o: Dictionary in oh.ohne:
		var nz := String(o["nazev"]); var z: Vector3 = o["zaklad"]; var v: Vector3 = o["ven"]
		var u: Node3D = o["uzel"]; var dn := String(u.get_parent().name)
		if nz.contains("kuchyni hradu"): pk = o
		if nz.contains("kamna"): pa = o
		var kl := ""
		if String(o["druh"]) == "pec" and String(u.name).begins_with("Dum1") and not sh.any(func(a): return String(a[0]).contains("ohen_pec_usti")): kl = "ohen_pec_usti"
		elif String(o["druh"]) == "pec" and String(u.name).begins_with("Rychta"): kl = "stav_pec_rychta"
		elif String(o["druh"]) == "pec" and String(u.name).begins_with("Dum2") and not sh.any(func(a): return String(a[0]).contains("stav_pec_dum2")): kl = "stav_pec_dum2"
		elif nz.contains("krčmy"): kl = "stav_krcma_kuchyne"
		elif nz.contains("šenkovně"): kl = "stav_krcma_pec"
		elif nz.contains("hájovny"): kl = "stav_hajovna_ohniste"
		elif nz.contains("výheň"): kl = "stav_kovarna_vyhen"
		elif nz.contains("kuchyni hradu"): kl = "stav_hrad_kuchyne"
		elif nz.contains("kamna"): kl = "stav_hrad_kamna"
		if kl == "": continue
		var c := z + v * 2.0 + Vector3.UP * 0.9 + v.cross(Vector3.UP) * 0.6
		if kl == "ohen_pec_usti": c = z + v * 1.6 + Vector3.UP * 0.55 + v.cross(Vector3.UP) * 0.5
		sh.append([kl, c, z + Vector3.UP * 0.2, 22.0])
	# Rychta: místo krbu zevnitř a komín zvenku (souřadnice modelu Rychty)
	for d in h.get_node("Mista").get_children():
		if String(d.name).contains("_Rychta_"):
			var t: Transform3D = (d as Node3D).global_transform
			sh.append(["ohen_krb_rychta", t * Vector3(-2.3, 1.6, 3.4), t * Vector3(1.55, 1.2, -0.45), 22.0])
			sh.append(["rychta_komin", t * Vector3(10.0, 5.0, 8.0), t * Vector3(1.55, 5.0, -0.45), 12.0])
			sh.append(["rychta_misto_krbu_den", t * Vector3(-2.3, 1.6, 3.4), t * Vector3(1.55, 1.2, -0.45), 12.0])
	# hrad A: síň patra (návrh krbu) z bodů kuchyně a kamen: W(1,45; 0; F0)+0,7 a W(5,35; −2,25; F1)+0,3
	if not pk.is_empty() and not pa.is_empty():
		var K: Vector3 = (pk["uzel"] as Node3D).global_position; var A: Vector3 = (pa["uzel"] as Node3D).global_position
		var dv := Vector2(A.x - K.x, A.z - K.z); var ab := Vector2(3.9, -2.25)
		var dd := Vector2((dv.x * ab.x + dv.y * ab.y), (dv.y * ab.x - dv.x * ab.y)).normalized()   # dv / ab (komplexně)
		var D := Vector3(dd.x, 0, dd.y); var S := D.cross(Vector3.UP)
		var p0 := K - D * 1.45 - Vector3.UP * 0.7   # W(0,0,F0)
		var F := A.y - 0.3 - p0.y   # F1 - F0
		print("FOTO_INFO hradA W0 %s d %s s %s F1-F0 %.2f" % [p0, D, S, F])
		var W := func(u: float, v: float, y: float) -> Vector3: return p0 + D * u + S * v + Vector3.UP * y
		print("FOTO_INFO hradA návrh krbu síň patra W(7,2; −3,0; F1) = %s" % [W.call(7.2, -3.0, F)])
		sh.append(["ohen_krb_hrad", W.call(7.2, 2.2, F + 1.6), W.call(7.2, -3.0, F + 1.1), 22.0])
		sh.append(["hradA_sin_svetlo", W.call(5.6, 2.3, F + 1.7), W.call(8.0, -3.0, F + 0.9), 12.0, true])
	sh.append(["hradB_sin_v", Vector3(50.3, 16.3, 146.6), Vector3(57.5, 15.4, 146.6), 12.0, true])
	sh.append(["hradB_sin_z", Vector3(57.5, 16.3, 144.0), Vector3(50.0, 15.4, 149.5), 12.0, true])
	sh.append(["hradB_sin_j", Vector3(53.9, 16.3, 149.6), Vector3(53.9, 15.4, 143.2), 12.0, true])
	var lamp := OmniLight3D.new(); lamp.omni_range = 14.0; lamp.light_energy = 2.0; lamp.visible = false; cam.add_child(lamp)
	var jen := OS.get_environment("PUCHART_FOTO_JEN").split(",", false)
	for s in sh:
		if not jen.is_empty() and not jen.has(String(s[0])): continue
		lamp.visible = s.size() > 4
		if h.get("den"): h.den.set_hour(float(s[3]), 0.0)
		oh._noc(false, float(s[3]))
		cam.look_at_from_position(s[1], s[2], Vector3.UP)
		for k in 45: await get_tree().process_frame
		var f := out + "/" + String(s[0]) + ".png"
		get_viewport().get_texture().get_image().save_png(f)
		print("FOTO_INFO snímek %s cam %s cil %s" % [f, s[1], s[2]])
	get_tree().quit()
