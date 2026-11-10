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
		var mm: Mesh = (mi as MeshInstance3D).mesh
		if String(mi.name).contains(String(D["uzdecka_sit"])) or (mm != null and String(mm.resource_name).contains(String(D["uzdecka_sit"]))):
			uzd = mi
	if uzd == null or uzd.mesh == null:
		push_error("otezi: sit uzdecky %s nenalezena" % D["uzdecka_sit"])
		return false
	# Vrcholy presne jako je kresli skinovani (soustava kostry, aktualni poza): sum vaha * poza(kost) * vazba * vrchol.
	# 10. 11. (test_otezi): klid kostry * vazba kosti 0 -> krouzky 3,3 m od hlavy (klid kun_henry neni poza vazby);
	# vazba kosti hlavy -> 26 m (vrcholy huby jsou vazane na jine kosti). Pak do soustavy kosti hlavy (aktualni poza).
	var sk_uzd: Skin = uzd.skin
	if sk_uzd == null:
		push_error("otezi: sit uzdecky bez skinu")
		return false
	var kosti_vazby := PackedInt32Array()
	for i in sk_uzd.get_bind_count():
		var b := sk_uzd.get_bind_bone(i)
		if b < 0:
			b = kostra.find_bone(String(sk_uzd.get_bind_name(i)))
		kosti_vazby.append(b)
	var hl_poza := kostra.get_bone_global_pose(_hlava)
	var do_hlavy := hl_poza.affine_inverse()
	var v: PackedVector3Array = PackedVector3Array()
	for si in uzd.mesh.get_surface_count():
		var ar: Array = uzd.mesh.surface_get_arrays(si)
		var vv: PackedVector3Array = ar[Mesh.ARRAY_VERTEX]
		var bb: PackedInt32Array = ar[Mesh.ARRAY_BONES]
		var ww: PackedFloat32Array = ar[Mesh.ARRAY_WEIGHTS]
		var nv := bb.size() / maxi(vv.size(), 1)
		for i in vv.size():
			var p := Vector3.ZERO
			var ws := 0.0
			for k in nv:
				var w := ww[i * nv + k]
				var bi := bb[i * nv + k]
				if w <= 0.0 or bi < 0 or bi >= kosti_vazby.size() or kosti_vazby[bi] < 0:
					continue
				p += (kostra.get_bone_global_pose(kosti_vazby[bi]) * sk_uzd.get_bind_pose(bi) * vv[i]) * w
				ws += w
			if ws > 0.0:
				v.append(do_hlavy * (p / ws))
	var a1 := Vector3.ZERO                                             # pocatek kosti hlavy
	var a0 := do_hlavy * kostra.get_bone_global_pose(hl0).origin
	var osa := (a1 - a0).normalized()
	var nahoru := ((kostra.global_basis * hl_poza.basis).inverse() * Vector3.UP).normalized()
	var bok := osa.cross(nahoru).normalized()
	var smax := -INF
	for p in v:
		smax = maxf(smax, (p - a0).dot(osa))
	var od := float(D["udidlo_od_nosu_m"]) / maxf((kostra.global_basis * hl_poza.basis).get_scale().y, 1e-4)
	var pas := float(D["udidlo_pas_m"]) / maxf((kostra.global_basis * hl_poza.basis).get_scale().y, 1e-4)
	# stred hlavy napric = prumer bodu pasu (kost hlavy nemusi lezet v ose huby - test_otezi 9. 11.: na jedne strane
	# kosti nebyl v pasu zadny vrchol); strany se deli podle nej, ne podle kosti
	var stred := 0.0
	var npas := 0
	for p in v:
		if absf((p - a0).dot(osa) - (smax - od)) < pas:
			stred += (p - a0).dot(bok)
			npas += 1
	if npas > 0:
		stred /= float(npas)
	a0 += bok * stred
	for strana: float in [-1.0, 1.0]:
		var vyber: Array = []
		var tmax := 0.0
		for p in v:
			var s := (p - a0).dot(osa)
			if absf(s - (smax - od)) < pas and (p - a0).dot(bok) * strana > 0.0:
				vyber.append(p)
				tmax = maxf(tmax, absf((p - a0).dot(bok)))
		if vyber.is_empty():
			var smin := INF
			for p in v:
				smin = minf(smin, (p - a0).dot(osa))
			push_error("otezi: v siti uzdecky nejsou body udidla (strana %+.0f; %d vrcholu, po ose hlavy %.3f..%.3f, pas %.3f +- %.3f, delka kosti hlavy %.3f, meritko kostry %.4f, skin %s)" % [strana, v.size(), smin, smax, smax - od, pas, a0.distance_to(a1), kostra.global_basis.get_scale().y, sk_uzd != null])
			return false
		# nejvic do strany (krouzek venku na tvari), z nich nejniz
		var kraj: Array = vyber.filter(func(p: Vector3) -> bool: return absf((p - a0).dot(bok)) > tmax * 0.8)
		kraj.sort_custom(func(p: Vector3, q: Vector3) -> bool: return p.dot(nahoru) < q.dot(nahoru))
		var st := Vector3.ZERO
		var n := mini(kraj.size(), 6)
		for i in n:
			st += kraj[i]
		st /= float(n)
		_krouzky.append(st)
		print_verbose("otezi: krouzek %+.0f v kostre %s (hlava %s / %s, nos %.3f po ose)" % [strana, st, a0, a1, smax])
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


## Vazba (inverzni bind) kosti v skinu, null = kost neni vazana.
func _vazba(sk: Skin, kost: int) -> Variant:
	if sk == null:
		return null
	for i in sk.get_bind_count():
		var b := sk.get_bind_bone(i)
		if b < 0:
			b = kostra.find_bone(String(sk.get_bind_name(i)))
		if b == kost:
			return sk.get_bind_pose(i)
	return null


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
