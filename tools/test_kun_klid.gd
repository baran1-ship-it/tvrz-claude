extends SceneTree
## Test kun_klid (Misa 0.99993: „kun pri jizde sebou moc casto hazi hlavou a asi i trochu vzpina; sedlo z jedne strany
## je moc zapustene v koni“). Bez sveta, headless, sekundy: kun (scripts/kun.gd) na rovine, jezdec (nahradni uzel
## s move_input / fly_up / yaw jako player.gd) projede scenar jizda.json test_klid.scenar. Kazdy krok fyziky se meri
## hozeni hlavou, vzpinani (sklon trupu), skok oci jezdce; na zacatku a ve stani pruraz sedla do tela po bocich.
## Spusteni: tools/beh.sh kunklid cmd godot --headless --path . -s res://tools/test_kun_klid.gd
## Vystup: KUN_KLID ... radky, TEST KUN_KLID OK/CHYBA, souhrn TEST KUN_KLID: n chyb.

const Pravidla := preload("res://scripts/pravidla.gd")
var T: Dictionary = Pravidla.cti("jizda", "test_klid")
var kun: CharacterBody3D
var jezdec: Node3D
var faze := -1
var faze_t := 0.0
var t := 0.0
var chyb := 0
var hl := -1                       # index kosti hlavy
var panev := -1
var hrbet := -1
var hist: Array = []               # [t, vyska hlavy] za hlava_okno_s
var sklon0 := INF
var oci_y := INF
var udal := {}                     # druh -> [[t, faze, hodnota]]
var posl := {}                     # druh -> cas posledni udalosti
var max_hl := 0.0
var max_sk := 0.0
var max_skok := 0.0
var oneshot := 0                   # snimky s jednorazovym klipem (Run_Stop, pastva) pod jezdcem
var pruraz_hotovo := {}
var konec := false
var yaw0 := 0.0


func _initialize() -> void:
	var zem := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var bx := BoxShape3D.new()
	bx.size = Vector3(2000, 1, 2000)
	cs.shape = bx
	cs.position = Vector3(0, -0.5, 0)
	zem.add_child(cs)
	root.add_child(zem)
	var main := Node.new()
	main.name = "MainNahrada"
	root.add_child(main)
	kun = CharacterBody3D.new()
	kun.set_script(load("res://scripts/kun.gd"))
	root.add_child(kun)
	if not kun.setup(main, Vector3(0, 0.05, 0), 0.0):
		_over("setup kone", false, "kun.setup selhal")
		konec = true
		return
	var s := GDScript.new()
	s.source_code = "extends Node3D\nvar move_input := Vector2.ZERO\nvar fly_up := false\nvar _jump := false\nvar yaw := 0.0\nvar pitch := 0.0\nvar na_koni = null\nvar velocity := Vector3.ZERO\nfunc look(a: float, b: float) -> void:\n\tyaw += a\n"
	s.reload()
	jezdec = Node3D.new()
	jezdec.set_script(s)
	root.add_child(jezdec)
	var sk: Skeleton3D = kun.get("_kostra")
	for i in sk.get_bone_count():
		var n := sk.get_bone_name(i)
		if n.begins_with("BN_Head_00"):
			hl = i
		elif n.begins_with("BN_Pelvis"):
			panev = i
		elif n.begins_with("BN_Spine_03"):
			hrbet = i


func _kost(i: int) -> Vector3:
	var sk: Skeleton3D = kun.get("_kostra")
	return kun.global_transform.affine_inverse() * (sk.global_transform * sk.get_bone_global_pose(i).origin)


func _physics_process(delta: float) -> bool:
	if konec:
		return true
	t += delta
	if t < 0.5:
		return false                                   # kun dosedne, strom animaci se rozbehne
	if not pruraz_hotovo.has("bez jezdce"):
		_pruraz("bez jezdce")
		kun.set("drzet_cestu", false)
		kun.set("jezdec", jezdec)
		jezdec.set("na_koni", kun)
		_dalsi_faze()
		return false
	var sc: Array = T["scenar"]
	faze_t += delta
	if faze_t >= float(sc[faze][1]):
		if faze == 0:
			_pruraz("stani s jezdcem")
		if faze + 1 >= sc.size():
			_konec()
			return true
		_dalsi_faze()
	var f: Array = sc[faze]
	var ost := String(f[3])
	var y := float(f[2])
	if ost == "klep_vypadky" and faze_t > 1.0 and fmod(faze_t, float(T["vypadek_kazdych_s"])) < float(T["vypadek_s"]):
		y = 0.0
	jezdec.set("move_input", Vector2(0, y))
	jezdec.set("fly_up", (ost.begins_with("klep") and faze_t < 0.15) or ost == "drz")
	if float(f[4]) > 0.0:
		jezdec.set("yaw", yaw0 + deg_to_rad(float(f[4])) * sin(faze_t * TAU / 3.0))
	_mer(delta)
	return false


func _dalsi_faze() -> void:
	faze += 1
	faze_t = 0.0
	var f: Array = T["scenar"][faze]
	yaw0 = float(kun.get("_yaw"))
	jezdec.set("yaw", yaw0)
	if String(f[3]) == "prekazka":
		var pm: Array = T["prekazka_m"]
		var b := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var bx := BoxShape3D.new()
		bx.size = Vector3(float(pm[0]), float(pm[1]), float(pm[2]))
		cs.shape = bx
		b.add_child(cs)
		root.add_child(b)
		var vpred := -kun.global_transform.basis.z
		vpred.y = 0.0
		b.global_position = kun.global_position + vpred.normalized() * float(T["prekazka_pred_m"]) + Vector3(0, float(pm[1]) * 0.5, 0)
		b.rotation.y = float(kun.get("_yaw"))
	print("KUN_KLID faze %s (%.1f s)" % [f[0], float(f[1])])


func _udalost(druh: String, hodnota: float) -> void:
	if t - float(posl.get(druh, -INF)) < float(T["udalost_odstup_s"]):
		posl[druh] = t
		return
	posl[druh] = t
	if not udal.has(druh):
		udal[druh] = []
	(udal[druh] as Array).append([t, String(T["scenar"][faze][0]), hodnota])
	print("KUN_KLID udalost %s t %.2f faze %s hodnota %.3f rychlost %.1f klip_jednou %s" % [druh, t, T["scenar"][faze][0], hodnota,
			float(kun.get("_rych")), (kun.get("_at") as AnimationTree).get("parameters/jednou/active")])


func _mer(delta: float) -> void:
	# hlava: odskok od klouzaveho prumeru (kost hlavy v soustave kone)
	var h := _kost(hl).y
	hist.append([t, h])
	while not hist.is_empty() and t - float(hist[0][0]) > float(T["hlava_okno_s"]):
		hist.pop_front()
	var pr := 0.0
	for e: Array in hist:
		pr += float(e[1])
	pr /= hist.size()
	var odsk := absf(h - pr)
	max_hl = maxf(max_hl, odsk)
	if hist.size() > 10 and odsk > float(T["hlava_odskok_m"]):
		_udalost("hozeni hlavou", odsk)
	# vzpinani: sklon panev -> hrbet nad vychozim (prvni mereni ve stani)
	var v := _kost(hrbet) - _kost(panev)
	var sklon := rad_to_deg(atan2(v.y, Vector2(v.x, v.z).length()))
	if sklon0 == INF:
		sklon0 = sklon
	max_sk = maxf(max_sk, sklon - sklon0)
	if sklon - sklon0 > float(T["vzpinani_st"]):
		_udalost("vzpinani", sklon - sklon0)
	# skok oci jezdce za jeden krok fyziky
	var oy := jezdec.global_position.y
	if oci_y != INF:
		max_skok = maxf(max_skok, absf(oy - oci_y))
		if absf(oy - oci_y) > float(T["skok_m"]):
			_udalost("skok jezdce", absf(oy - oci_y))
	oci_y = oy
	if bool((kun.get("_at") as AnimationTree).get("parameters/jednou/active")):
		oneshot += 1


## Pruraz sedla do tela: vrcholy site sedla (soustava kone) proti prurezu tela kone (skin v aktualni poze).
func _pruraz(kdy: String) -> void:
	pruraz_hotovo[kdy] = true
	var sk: Skeleton3D = kun.get("_kostra")
	var model: Node3D = kun.get("_model")
	var inv := kun.global_transform.affine_inverse()
	var telo: Array = []
	var tm: MeshInstance3D = null
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var g := mi as MeshInstance3D
		if g.visible and g.skin and (tm == null or g.mesh.get_faces().size() > tm.mesh.get_faces().size()):
			tm = g
	var vaz := {}
	for b in tm.skin.get_bind_count():
		var kost := tm.skin.get_bind_bone(b)
		if kost < 0:
			kost = sk.find_bone(tm.skin.get_bind_name(b))
		vaz[b] = inv * sk.global_transform * sk.get_bone_global_pose(kost) * tm.skin.get_bind_pose(b)
	for si in tm.mesh.get_surface_count():
		var arr := tm.mesh.surface_get_arrays(si)
		var vv: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var bo: PackedInt32Array = arr[Mesh.ARRAY_BONES]
		var we: PackedFloat32Array = arr[Mesh.ARRAY_WEIGHTS]
		var nb := bo.size() / vv.size()
		for i in vv.size():
			var p := Vector3.ZERO
			var sw := 0.0
			for j in nb:
				var w := we[i * nb + j]
				if w > 0.0:
					p += ((vaz[bo[i * nb + j]] as Transform3D) * vv[i]) * w
					sw += w
			telo.append(p / maxf(sw, 1e-6))
	var sedlo: Array = []
	for mi in kun.find_children("*", "MeshInstance3D", true, false):
		if model.is_ancestor_of(mi) or not (mi as MeshInstance3D).is_visible_in_tree():
			continue
		var g := mi as MeshInstance3D
		var x := inv * g.global_transform
		for si in g.mesh.get_surface_count():
			for p: Vector3 in (g.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX] as PackedVector3Array):
				sedlo.append(x * p)
	if sedlo.is_empty():
		_over("sedlo %s" % kdy, false, "sedlo (vystroj) chybi")
		return
	var pz := float(T["prurez_m"])
	var kos := deg_to_rad(float(T["prurez_kos_st"]))
	var tol := float(T["pruraz_tolerance_m"])
	# pres: z (osa kone) -> body tela v pasu; pasy po pz
	var pasy := {}
	for p: Vector3 in telo:
		var k := floori(p.z / pz)
		if not pasy.has(k):
			pasy[k] = []
		(pasy[k] as Array).append(p)
	var vys := {"L": [0, 0.0], "P": [0, 0.0]}
	var smin := Vector3.INF
	var smax := -Vector3.INF
	for p: Vector3 in sedlo:
		smin = smin.min(p)
		smax = smax.max(p)
	var stred_x := 0.0
	var n_st := 0
	for p: Vector3 in sedlo:
		var k := floori(p.z / pz)
		var pas: Array = []
		for dk in [-1, 0, 1]:
			pas.append_array(pasy.get(k + dk, []))
		if pas.size() < 20:
			continue
		# prurez trupu: jen body nad spodkem sedla - 0,5 m (ne nohy), stred = stred obalu
		var x0 := INF
		var x1 := -INF
		var y0 := INF
		var y1 := -INF
		var tr: Array = []
		for q: Vector3 in pas:
			if q.y > smin.y - 0.5:
				tr.append(q)
				x0 = minf(x0, q.x)
				x1 = maxf(x1, q.x)
				y0 = minf(y0, q.y)
				y1 = maxf(y1, q.y)
		if tr.size() < 20:
			continue
		var c := Vector2((x0 + x1) * 0.5, (y0 + y1) * 0.5)
		stred_x += c.x
		n_st += 1
		var d := Vector2(p.x, p.y) - c
		var r_t := 0.0
		for q: Vector3 in tr:
			var dq := Vector2(q.x, q.y) - c
			if absf(angle_difference(dq.angle(), d.angle())) < kos * 0.5:
				r_t = maxf(r_t, dq.length())
		var hl2 := r_t - d.length()
		if hl2 > tol:
			var bok := "L" if p.x < c.x else "P"
			vys[bok][0] += 1
			vys[bok][1] = maxf(float(vys[bok][1]), hl2)
	stred_x /= maxf(n_st, 1)
	var rozdil := absf(float(vys["L"][1]) - float(vys["P"][1]))
	var txt := "%s: levy bok %d vrcholu pod telem (nejhloub %.3f m), pravy %d (%.3f m), sedlo x %.3f..%.3f (stred %.3f) proti stredu tela %.3f, vrcholu %d" % [
			kdy, vys["L"][0], vys["L"][1], vys["P"][0], vys["P"][1], smin.x, smax.x, (smin.x + smax.x) * 0.5, stred_x, sedlo.size()]
	print("KUN_KLID pruraz " + txt)
	_over("sedlo %s" % kdy, rozdil <= float(T["pruraz_rozdil_m"]) and maxf(float(vys["L"][1]), float(vys["P"][1])) <= float(T["pruraz_max_m"]), txt)


func _konec() -> void:
	var sv := ""
	for d: String in ["hozeni hlavou", "vzpinani", "skok jezdce"]:
		var a: Array = udal.get(d, [])
		var fz := {}
		for e: Array in a:
			fz[e[1]] = int(fz.get(e[1], 0)) + 1
		sv = "%d za %.0f s %s" % [a.size(), t, str(fz)]
		_over(d, a.is_empty(), sv)
	print("KUN_KLID max odskok hlavy %.3f m, max sklon trupu +%.1f st., max skok oci %.3f m/krok, jednorazovy klip pod jezdcem %d kroku" % [max_hl, max_sk, max_skok, oneshot])
	print("TEST KUN_KLID: %d chyb" % chyb)
	konec = true


func _over(jm: String, ok: bool, txt: String) -> void:
	if not ok:
		chyb += 1
	print("TEST KUN_KLID %-28s %s  %s" % [jm, "OK" if ok else "CHYBA", txt])
