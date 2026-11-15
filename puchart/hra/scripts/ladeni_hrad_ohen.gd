extends Node
## DOČASNÝ ladicí skript (smazat): snímek kuchyně hradu a sezení v nice okna.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var h := get_parent()
	var oh: Node = h.get_node("Ohne")
	if not bool(oh.pripraveno): await oh.hotovo
	for i in 30: await get_tree().process_frame
	var pr: Node = null
	for c in h.get_children():
		if c is CanvasLayer and c.get("zebriky") != null: pr = c
	get_tree().paused = false
	if pr and pr.get("menu") and pr.menu.has_method("hide_menu"): pr.menu.hide_menu()
	if h.den: h.den.running = false; h.den.set_hour(18.5, 0.0)
	oh._noc(false, 18.5)
	var ss := get_viewport().get_world_3d().direct_space_state
	var ok: Dictionary = {}
	for o: Dictionary in oh.ohne:
		if true:
			var z: Vector3 = o["zaklad"]
			var r := ss.intersect_ray(PhysicsRayQueryParameters3D.create(z + Vector3.UP * 0.3, z - Vector3.UP))
			var col = r.get("collider")
			var ncs := 0
			if col: ncs = (col as Node).find_children("*", "CollisionShape3D", true, false).size()
			print("LAD ohen %s zaklad %s svetlo %s collider %s (%s, tvaru %d) vlastni %d" % [o["nazev"], z, o["poloha"], col, (col as Node).get_path() if col else "", ncs, (o["vlastni"] as Array).size()])
			if String(o["nazev"]).contains("kuchyni"): ok = o
	var hr: CharacterBody3D = h.hrac
	hr.set_physics_process(false)
	var cil: Vector3 = ok["zaklad"] + Vector3.UP * 0.4
	var best := Vector3.ZERO; var bd := 0.0
	for k in 16:
		var a := k * TAU / 16.0; var sm := Vector3(cos(a), 0, sin(a))
		var q := PhysicsRayQueryParameters3D.create(cil + Vector3.UP * 1.0, cil + Vector3.UP * 1.0 + sm * 4.0)
		var r := ss.intersect_ray(q); var d := 4.0 if r.is_empty() else cil.distance_to(r["position"] - Vector3.UP)
		if d > bd: bd = d; best = sm
	var kde := cil + best * minf(bd - 0.4, 3.2)
	hr.global_position = Vector3(kde.x, ok["zaklad"].y - 0.5, kde.z)
	hr.cam.global_position = Vector3(kde.x, ok["zaklad"].y - 0.5 + 1.65, kde.z)
	hr.cam.look_at(cil, Vector3.UP)
	oh._rozpocet(hr.cam.global_position)
	for i in 60: await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(OS.get_environment("LAD_OUT") + "/ohen.png")
	print("LAD foto ohen, svetel %d, kamera %s" % [oh.pocet_svetel(), hr.cam.global_position])
	# sedátka hradu
	var sed: Array = []
	for m: Dictionary in h.lavice:
		if String(m["lavice"]).contains("Sedatka"): sed.append(m)
	print("LAD sedatek hradu %d z %d" % [sed.size(), h.lavice.size()])
	for m: Dictionary in sed:
		var p: Vector3 = m["pos"]; var v: Vector3 = m["vstat"]
		var r := ss.intersect_ray(PhysicsRayQueryParameters3D.create(v + Vector3.UP * 0.5, v - Vector3.UP * 2.0))
		var pod: float = r["position"].y if not r.is_empty() else NAN
		print("LAD sed %s pos %s yaw %.0f vstat %s podlaha %.2f sed nad podlahou %.2f" % [m["lavice"], p, rad_to_deg(m["yaw"]), v, pod, p.y - pod])
	if sed.size() > 0:
		h.den.set_hour(11.0, 0.0)
		var m: Dictionary = sed[OS.get_environment("LAD_SED").to_int() if OS.get_environment("LAD_SED") != "" else 0]
		hr.set_physics_process(true)
		hr.sit(m["pos"], float(m["oci"]), m["vstat"], float(m["yaw"]), -0.1)
		for i in 90: await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(OS.get_environment("LAD_OUT") + "/lavice.png")
		print("LAD foto lavice %s kamera %s" % [m["lavice"], hr.cam.global_position])
	get_tree().quit()
