const Pravidla := preload("res://scripts/pravidla.gd")
## Mlha pri zemi nad toky (Misa 18. 11., voda jako v lese Hvozd): pruhledne billboardy (shaders/mlha_vody.gdshader,
## unshaded, bez zapisu hloubky) v MultiMeshich po kusech osy toku - Bystrice (voda.json potok.osa) a male toky
## (toky[].osa_xzy). Vsechna cisla z voda.json mlha_vody; kus = jeden MultiMesh s dosahem viditelnosti (dosah_m),
## aby se vzdalena mlha nekreslila vubec (prekresleni na tabletu). Merici trasa: varianta bez_mlhy_vody skryje uzel.


static func postav(parent: Node3D, sv: RefCounted) -> Node3D:
	var c: Dictionary = Pravidla.cti("voda", "mlha_vody")
	var osy: Array = []
	if bool(c["potok_bystrice"]):
		var o: Array = []
		for b: Array in Pravidla.cti("voda", "potok", "osa"):
			o.append(Vector2(float(b[0]), float(b[1])))
		osy.append(o)
	if bool(c["toky"]):
		for t: Dictionary in Pravidla.cti("voda", "toky"):
			var o: Array = []
			for b: Array in t.get("osa_xzy", []):
				o.append(Vector2(float(b[0]), float(b[1])))
			if o.size() > 1:
				osy.append(o)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(c["seed"])
	var roz := float(c["rozestup_m"])
	var kus := float(c["kus_m"])
	var sir: Array = c["sirka_m"]
	var vys: Array = c["vyska_m"]
	var nad: Array = c["nad_terenem_m"]
	var kr: Array = c["kryti"]
	var max_n := int(c["max_billboardu"])
	# body po ose v rozestupu, rozdelene do kusu (kus_m delky osy)
	var kusy: Array = []           # [[Vector3 poloha, sirka, vyska, kryti, faze], ...]
	var n := 0
	for o: Array in osy:
		var akt: Array = []
		var ujito := 0.0
		var dalsi := 0.0
		var ve_kusu := 0.0
		for i in range(1, o.size()):
			var a: Vector2 = o[i - 1]
			var b: Vector2 = o[i]
			var L := a.distance_to(b)
			if L < 0.001:
				continue
			var smer := (b - a) / L
			while dalsi <= ujito + L and n < max_n:
				var q := a + smer * (dalsi - ujito) + Vector2(-smer.y, smer.x) * rng.randf_range(-1.0, 1.0) * float(c["bok_m"])
				var y := maxf(float(sv._teren_y(q.x, q.y)), float(sv.hladina(q.x, q.y)))
				akt.append([Vector3(q.x, y + rng.randf_range(float(nad[0]), float(nad[1])), q.y),
						rng.randf_range(float(sir[0]), float(sir[1])), rng.randf_range(float(vys[0]), float(vys[1])),
						rng.randf_range(float(kr[0]), float(kr[1])), rng.randf()])
				n += 1
				dalsi += roz * rng.randf_range(0.75, 1.25)
				ve_kusu += roz
				if ve_kusu >= kus:
					kusy.append(akt)
					akt = []
					ve_kusu = 0.0
			ujito += L
		if not akt.is_empty():
			kusy.append(akt)
	var koren := Node3D.new()
	koren.name = "Mlha_vody"
	parent.add_child(koren)
	if n == 0:
		return koren
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/mlha_vody.gdshader")
	for cesta: String in ["res://addons/waterways/textures/foam_noise.png", "res://modely/reka/foam_noise.png"]:
		if ResourceLoader.exists(cesta):
			mat.set_shader_parameter("sum", load(cesta))
			break
	var bc: Array = c["barva"]
	mat.set_shader_parameter("barva", Color(float(bc[0]), float(bc[1]), float(bc[2])))
	var bz: Array = c["blizko_zmizi_m"]
	mat.set_shader_parameter("blizko", Vector2(float(bz[0]), float(bz[1])))
	var dosah := float(c["dosah_m"])
	mat.set_shader_parameter("dosah", dosah)
	var quad := QuadMesh.new()
	quad.size = Vector2(1.0, 1.0)
	quad.center_offset = Vector3(0.0, 0.5, 0.0)
	quad.material = mat
	for k: Array in kusy:
		var st := Vector3.ZERO
		for p: Array in k:
			st += p[0]
		st /= float(k.size())
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true
		mm.mesh = quad
		mm.instance_count = k.size()
		var r := 0.0
		for i in k.size():
			var p: Array = k[i]
			var lp: Vector3 = p[0] - st
			mm.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3(p[1], p[2], 1.0)), lp))
			mm.set_instance_custom_data(i, Color(p[3], p[4], 0.0, 0.0))
			r = maxf(r, Vector2(lp.x, lp.z).length() + float(p[1]) * 0.5)
		var mi := MultiMeshInstance3D.new()
		mi.multimesh = mm
		mi.position = st
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# billboard se toci ve shaderu: obal pres vsechny smery
		mi.custom_aabb = AABB(Vector3(-r, -1.0, -r), Vector3(2.0 * r, float(vys[1]) + 2.0, 2.0 * r))
		mi.visibility_range_end = dosah + r
		koren.add_child(mi)
	print("MLHA_VODY %d billboardu v %d kusech" % [n, kusy.size()])
	return koren
