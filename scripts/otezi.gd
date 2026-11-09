extends MeshInstance3D
## Otezi (Misa 9. 11. r. 86, snimek misa_9_11/17: „ruce na otezich jsou, ale chybi samotne otezi“): dva remeny od
## udidla kone (krouzky u koutku huby) do dlani jezdce. Model kone (kun_henry, uzdecka v siti Bridle) otezi nema;
## hotovy model otezi s pohyblivymi konci jsme nenasli (Sketchfab/Poly Haven maji otezi jen jako pevnou cast modelu
## kone), proto tenky remen pocitany kazdy snimek: retezovka priblizena parabolou, provis z delky remene a
## vzdalenosti koncu (jizda.json kun.otezi), dva krizene pasky na usek (videt z kazdeho uhlu), ~100 trojuhelniku.
## Krouzky udidla: body site uzdecky v predni casti hlavy (osa kost hlavy -> nos, udidlo_od_nosu_m), nejvic do stran
## a nejniz - spoctene jednou v klidove poze, pak jdou s kosti hlavy (kost_hlavy).

var D: Dictionary = {}
var kostra: Skeleton3D
var _hlava := -1
var _krouzky: Array = []          # [levy, pravy] v soustave kosti hlavy (klid)
var _im: ImmediateMesh
var konce: Array = []             # posledni konce [udidlo_l, udidlo_r, ruka_l, ruka_r] (test)


func setup(kun: Node3D, data: Dictionary) -> bool:
	D = data
	kostra = kun.get("_kostra")
	if kostra == null:
		return false
	_hlava = _kost(String(D["kost_hlavy"]))
	var hl0 := _kost(String(D["kost_hlavy_zacatek"]))
	if _hlava < 0 or hl0 < 0:
		push_error("otezi: kost hlavy kone %s / %s nenalezena" % [D["kost_hlavy"], D["kost_hlavy_zacatek"]])
		return false
	var uzd: MeshInstance3D = null
	for mi in kun.find_children("*", "MeshInstance3D", true, false):
		if String(mi.name).contains(String(D["uzdecka_sit"])):
			uzd = mi
	if uzd == null or uzd.mesh == null:
		push_error("otezi: sit uzdecky %s nenalezena" % D["uzdecka_sit"])
		return false
	# klidova poza: vrcholy site = soustava kostry (skin s bind = klid)
	var a0 := kostra.get_bone_global_rest(hl0).origin
	var a1 := kostra.get_bone_global_rest(_hlava).origin
	var osa := (a1 - a0).normalized()
	var nahoru := (kostra.global_basis.inverse() * Vector3.UP).normalized()
	var bok := osa.cross(nahoru).normalized()
	var v: PackedVector3Array = PackedVector3Array()
	for si in uzd.mesh.get_surface_count():
		v.append_array(uzd.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX])
	var smax := -INF
	for p in v:
		smax = maxf(smax, (p - a0).dot(osa))
	var od := float(D["udidlo_od_nosu_m"]) / maxf(kostra.global_basis.get_scale().y, 1e-4)
	var pas := float(D["udidlo_pas_m"]) / maxf(kostra.global_basis.get_scale().y, 1e-4)
	for strana: float in [-1.0, 1.0]:
		var vyber: Array = []
		var tmax := 0.0
		for p in v:
			var s := (p - a0).dot(osa)
			if absf(s - (smax - od)) < pas and (p - a0).dot(bok) * strana > 0.0:
				vyber.append(p)
				tmax = maxf(tmax, absf((p - a0).dot(bok)))
		if vyber.is_empty():
			push_error("otezi: v siti uzdecky nejsou body udidla")
			return false
		# nejvic do strany (krouzek venku na tvari), z nich nejniz
		var kraj: Array = vyber.filter(func(p: Vector3) -> bool: return absf((p - a0).dot(bok)) > tmax * 0.8)
		kraj.sort_custom(func(p: Vector3, q: Vector3) -> bool: return p.dot(nahoru) < q.dot(nahoru))
		var st := Vector3.ZERO
		var n := mini(kraj.size(), 6)
		for i in n:
			st += kraj[i]
		st /= float(n)
		_krouzky.append(kostra.get_bone_global_rest(_hlava).affine_inverse() * st)
	_im = ImmediateMesh.new()
	mesh = _im
	top_level = true
	global_transform = Transform3D.IDENTITY
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	extra_cull_margin = 4.0
	var m := StandardMaterial3D.new()
	var b: Array = D["barva"]
	m.albedo_color = Color(float(b[0]), float(b[1]), float(b[2]))
	m.roughness = 0.8
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	material_override = m
	return true


## Kost podle zacatku jmena (importer muze pridat priponu).
func _kost(predpona: String) -> int:
	for i in kostra.get_bone_count():
		if kostra.get_bone_name(i).begins_with(predpona):
			return i
	return -1


func udidla() -> Array:
	var g := kostra.global_transform * kostra.get_bone_global_pose(_hlava)
	return [g * (_krouzky[0] as Vector3), g * (_krouzky[1] as Vector3)]


## Konce v rukou (svet): levy, pravy. Remen ruka -> udidlo stejne strany.
func aktualizuj(ruka_l: Vector3, ruka_r: Vector3) -> void:
	if _im == null:
		return
	var ud := udidla()
	konce = [ud[0], ud[1], ruka_l, ruka_r]
	_im.clear_surfaces()
	_im.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for k in 2:
		_remen(ud[k], ruka_l if k == 0 else ruka_r)
	_im.surface_end()


func _remen(a: Vector3, b: Vector3) -> void:
	var n := int(D["useku"])
	var d := a.distance_to(b)
	var delka := maxf(float(D["delka_m"]), d)
	# parabola s delkou oblouku ~ delka: provis h = sqrt(3/16 * d * (delka - d)) (priblizeni retezovky)
	var h := sqrt(maxf(0.0, 3.0 / 16.0 * d * (delka - d)))
	var w := float(D["sirka_m"]) * 0.5
	var body: Array = []
	for i in n + 1:
		var t := float(i) / n
		body.append(a.lerp(b, t) + Vector3.DOWN * h * 4.0 * t * (1.0 - t))
	for i in n:
		var p0: Vector3 = body[i]
		var p1: Vector3 = body[i + 1]
		var sm := (p1 - p0).normalized()
		var s1 := sm.cross(Vector3.UP)
		if s1.length_squared() < 1e-6:
			s1 = Vector3.RIGHT
		s1 = s1.normalized() * w
		var s2 := sm.cross(s1).normalized() * w
		for s: Vector3 in [s1, s2]:
			_im.surface_set_normal(sm.cross(s).normalized())
			_im.surface_add_vertex(p0 - s)
			_im.surface_add_vertex(p0 + s)
			_im.surface_add_vertex(p1 + s)
			_im.surface_add_vertex(p0 - s)
			_im.surface_add_vertex(p1 + s)
			_im.surface_add_vertex(p1 - s)
