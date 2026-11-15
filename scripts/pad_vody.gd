extends RefCounted
const Pravidla := preload("res://scripts/pravidla.gd")
## Pady kaskady potoka (Misa 15. 11. r. 4: „vodopad vypada divne – ploche leskle plachty, prochazi travou a kameny“,
## snimky docs/screens/misa_15_11/08-10). Drive byl pad jen usek jednoho pasu Waterways (tools/reka_bake.gd): plochy
## obdelnik sire tune s ostrym lomem, UV natazene, shader reky lesk 0,15 = zrcadlo oblohy (plech).
## Ted (rese potok_pereje_resers.md body 1-7; Uncharted GDC 2012, Jedi Fallen Order - simonschreibt.de):
##  - zaclona = samostatna sit z koryto.pady (rozmery voda.json raz_toku kaskada schody.pad_vody): okap ve vysce horni
##    tune (plna sirka pasu, zuzuje se), lom s previsem (parabola x ~ sqrt(pad), vodorovna tecna na hrane), napric mirne
##    vypoukla, dole sirsi; UV v metrech (U napric, V po proudu), barva vrcholu R pena, G padajici cast, A okraj
##  - vsechny zaclony = jedna sit (jedno kresleni); trist u paty (plocha peny + 2 krizene karty mlhy) = jedna sdilena
##    jednotkova sit, instance na pad s viditelnosti z pravidel
##  - pas reky: ve stope padu trojuhelniky se |normala.y| < zahodit_normala_y pryc (oriz_pas, pri nacteni - predpeceny
##    pas v baliku z_reka se neprepeka)
## Shader shaders/pad.gdshader: bez lesku (SPECULAR 0, ROUGHNESS 1), posuvne pruhy z foam_noise, bez screen texture.


static func _pv() -> Dictionary:
	var dr: Array = Pravidla.cti("voda", "potok", "raz_toku")["druhy"]
	return ((dr.back() as Dictionary)["schody"] as Dictionary)["pad_vody"]


## Pas reky bez padajicich casti ve stope padu. Vraci novou sit (nebo puvodni, kdyz neni co orezat) + vypis poctu.
static func oriz_pas(mesh: Mesh, kor: RefCounted) -> Mesh:
	if mesh == null or kor == null or (kor.pady as Array).is_empty() or not (mesh is ArrayMesh):
		return mesh
	var pv := _pv()
	var prah := float(pv["zahodit_normala_y"])
	var okraj := float(pv["zahodit_okraj_m"])
	var am := mesh as ArrayMesh
	var out := ArrayMesh.new()
	var pryc := 0
	var celk := 0
	for si in am.get_surface_count():
		var arr := am.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		var bez_idx := idx.is_empty()
		if bez_idx:
			idx.resize(v.size())
			for i in v.size():
				idx[i] = i
		var nove := PackedInt32Array()
		for t in range(0, idx.size() - 2, 3):
			var a := v[idx[t]]
			var b := v[idx[t + 1]]
			var c := v[idx[t + 2]]
			celk += 1
			var st := (a + b + c) / 3.0
			if absf((b - a).cross(c - a).normalized().y) < prah and _ve_stope(kor, Vector2(st.x, st.z), okraj):
				pryc += 1
				continue
			nove.append(idx[t])
			nove.append(idx[t + 1])
			nove.append(idx[t + 2])
		arr[Mesh.ARRAY_INDEX] = nove
		out.add_surface_from_arrays(am.surface_get_primitive_type(si), arr)
		out.surface_set_material(out.get_surface_count() - 1, am.surface_get_material(si))
	print("pady: pas reky - %d troj. padu pryc z %d (|normala.y| < %.2f ve stope %d padu)" % [pryc, celk, prah, (kor.pady as Array).size()])
	return out


static func _ve_stope(kor: RefCounted, q: Vector2, okraj: float) -> bool:
	for pd: Dictionary in kor.pady:
		var v := q - (pd["a"] as Vector2)
		var s := v.dot(pd["smer"] as Vector2)
		if s < -okraj or s > float(pd["L"]) + okraj:
			continue
		if absf(v.dot(pd["nrm"] as Vector2)) <= float(pd["pul_pas"]) + okraj:
			return true
	return false


## Postavi zaclony a trist pod parent. Vraci pocet padu.
static func postav(parent: Node3D, kor: RefCounted) -> int:
	if kor == null or (kor.pady as Array).is_empty():
		return 0
	var pv := _pv()
	var sh: Dictionary = pv["shader"]
	var tr: Dictionary = pv["trist"]
	var tex: Texture2D = null
	# addons/ v APK neni (export_presets exclude) - tablet bere kopii z baliku z_reka; na PC se textury z baliku
	# nenactou (chybi importy), proto napred zdroj Waterways
	for cesta: String in ["res://addons/waterways/textures/foam_noise.png", "res://modely/reka/foam_noise.png"]:
		if ResourceLoader.exists(cesta):
			tex = load(cesta)
			break
	if tex == null:
		push_warning("pady: foam_noise chybi - zaclona bez pruhu")
	var sd := load("res://shaders/pad.gdshader") as Shader
	var mat := func(druh: int, alfa: float) -> ShaderMaterial:
		var m := ShaderMaterial.new()
		m.shader = sd
		m.set_shader_parameter("pena_tex", tex)
		m.set_shader_parameter("druh", druh)
		m.set_shader_parameter("voda", _barva(sh["voda"]))
		m.set_shader_parameter("pena", _barva(sh["pena"]))
		m.set_shader_parameter("rychlost", float(sh["rychlost_m_s"]))
		m.set_shader_parameter("rychlost_okap", float(sh["rychlost_okap_m_s"]))
		var mp: Array = sh["meritko_pruhu"]
		m.set_shader_parameter("meritko_pruhu", Vector2(float(mp[0]), float(mp[1])))
		m.set_shader_parameter("prolinani_hore_m", float(sh["prolinani_hore_m"]))
		m.set_shader_parameter("pruhlednost", float(sh["pruhlednost"]))
		m.set_shader_parameter("okap_kryti", float(sh["okap_kryti"]))
		m.set_shader_parameter("alfa_max", alfa)
		return m
	# zaclony: jedna sit
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var zaklad := 0
	for pd: Dictionary in kor.pady:
		zaklad = _zaclona(st, pd, pv, zaklad)
	var mi := MeshInstance3D.new()
	mi.name = "Pady"
	mi.mesh = st.commit()
	mi.material_override = mat.call(0, 1.0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	# trist u paty: jednotkova sit (plocha peny + 2 karty mlhy), instance na kazdy pad
	var jm := _trist_sit(float(tr["mlha_uhel_st"]))
	jm.surface_set_material(0, mat.call(1, float(tr["pena_alfa"])))
	jm.surface_set_material(1, mat.call(2, minf(float(tr["mlha_alfa"]), 0.25)))     # mlha nikdy nad 0,25
	var dosah := float(tr["viditelnost_m"])
	var i := 0
	for pd: Dictionary in kor.pady:
		var smer: Vector2 = pd["smer"]
		var nrm: Vector2 = pd["nrm"]
		var pata: Vector2 = (pd["a"] as Vector2) + smer * float(pd["L"])
		var pad := float(pd["y_hore"]) - float(pd["y_dole"])
		var sx := float(pd["pul_dole"]) * float(tr["pena_sirka_podil"])
		var sz := float(tr["pena_delka_m"])
		var sy := minf(pad * float(tr["mlha_vyska_podil"]), float(tr["mlha_vyska_max_m"]))
		var b := Basis(Vector3(nrm.x, 0.0, nrm.y) * sx, Vector3.UP * sy, Vector3(smer.x, 0.0, smer.y) * sz)
		var ti := MeshInstance3D.new()
		ti.name = "Pad_trist_%d" % i
		ti.mesh = jm
		ti.transform = Transform3D(b, Vector3(pata.x, float(pd["y_dole"]) + float(pv["nad_hladinou_m"]), pata.y))
		ti.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		ti.visibility_range_end = dosah
		parent.add_child(ti)
		i += 1
	print("pady: %d zaclon (%d vrch.), pena %s, trist do %.0f m; %s" % [(kor.pady as Array).size(), zaklad, tex.resource_path if tex else "-", dosah,
			str((kor.pady as Array).map(func(p: Dictionary) -> String: return "(%.1f, %.1f) pad %.2f L %.2f pul %.2f/%.2f" % [
				(p["a"] as Vector2).x, (p["a"] as Vector2).y, float(p["y_hore"]) - float(p["y_dole"]), float(p["L"]), float(p["pul"]), float(p["pul_pas"])]))])
	return (kor.pady as Array).size()


static func _barva(a: Array) -> Color:
	return Color(float(a[0]), float(a[1]), float(a[2]))


## Jedna zaclona do SurfaceTool: mrizka rad (okap rad_okap + pad rad_pad) x sloupcu. Vraci novy zaklad indexu.
static func _zaclona(st: SurfaceTool, pd: Dictionary, pv: Dictionary, zaklad: int) -> int:
	var a2: Vector2 = pd["a"]
	var smer := Vector3((pd["smer"] as Vector2).x, 0.0, (pd["smer"] as Vector2).y)
	var nrm := Vector3((pd["nrm"] as Vector2).x, 0.0, (pd["nrm"] as Vector2).y)
	var y_h := float(pd["y_hore"]) + float(pv["nad_hladinou_m"])
	var y_d := float(pd["y_dole"]) - float(pv["pod_hladinu_m"])
	var s_h := float(pd["s_hrana"])
	var prev := float(pd["previs"])
	var pul_pas := float(pd["pul_pas"])
	var pul := float(pd["pul"])
	var pul_d := float(pd["pul_dole"])
	var vyp := float(pv["vypoukle_m"])
	var no := int(pv["rad_okap"])
	var npd := int(pv["rad_pad"])
	var ns := int(pv["sloupcu"])
	var okraj := float(pv["okraj_podil"])
	var pena_h := float(pv["pena_hore"])
	var pena_od := float(pv["pena_od"])
	var y_r := y_h - y_d
	# rady: (s po proudu, y, pul sirky, vypouklost, pena, padajici)
	var rady: Array = []
	for j in no:
		var f := float(j) / no
		var sp := smoothstep(0.0, 1.0, f)
		rady.append([s_h * f, y_h, lerpf(pul_pas, pul, sp), vyp * sp * sp, pena_h * sp * 0.5, 0.0])
	for j in npd + 1:
		var v := float(j) / npd
		# volny pad: vodorovne x ~ sqrt(pokles), vodorovna tecna na hrane
		rady.append([s_h + prev * sqrt(v), y_h - y_r * v, lerpf(pul, pul_d, v), vyp, lerpf(pena_h, 1.0, smoothstep(pena_od, 1.0, v)), 1.0])
	var body := []
	var dl_v := 0.0
	var pred := Vector3.ZERO
	for j in rady.size():
		var r: Array = rady[j]
		var stred := Vector3(a2.x, 0.0, a2.y) + smer * float(r[0]) + Vector3(0.0, float(r[1]), 0.0)
		if j > 0:
			dl_v += stred.distance_to(pred)
		pred = stred
		var rada := []
		for i in ns + 1:
			var u := lerpf(-1.0, 1.0, float(i) / ns)
			var p := stred + nrm * (u * float(r[2])) + smer * (float(r[3]) * (1.0 - u * u))
			var al := 1.0 - smoothstep(1.0 - okraj, 1.0, absf(u))
			rada.append([p, Vector2(u * float(r[2]), dl_v), Color(float(r[4]), float(r[5]), 0.0, al)])
		body.append(rada)
	for j in body.size():
		for i in ns + 1:
			var c: Array = body[j][i]
			# normala z mrizky: po proudu x napric, otocena nahoru/po proudu (k divakovi pod padem)
			var tj := (body[mini(j + 1, body.size() - 1)][i][0] as Vector3) - (body[maxi(j - 1, 0)][i][0] as Vector3)
			var ti := (body[j][mini(i + 1, ns)][0] as Vector3) - (body[j][maxi(i - 1, 0)][0] as Vector3)
			var n := ti.cross(tj).normalized()
			if n.y + n.dot(smer) < 0.0:
				n = -n
			st.set_normal(n)
			st.set_uv(c[1])
			st.set_color(c[2])
			st.add_vertex(c[0])
	for j in body.size() - 1:
		for i in ns:
			var i0 := zaklad + j * (ns + 1) + i
			var i1 := i0 + ns + 1
			st.add_index(i0)
			st.add_index(i1)
			st.add_index(i0 + 1)
			st.add_index(i0 + 1)
			st.add_index(i1)
			st.add_index(i1 + 1)
	return zaklad + body.size() * (ns + 1)


## Jednotkova sit trist: surface 0 = plocha peny (x -1..1 napric, z -0,3..1 po proudu, y 0), surface 1 = 2 krizene
## svisle karty mlhy (y 0..1, natocene +-uhel od napricne osy). Barva A = mekky okraj, UV v jednotkach site.
static func _trist_sit(uhel_st: float) -> ArrayMesh:
	var am := ArrayMesh.new()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 8
	for j in n + 1:
		for i in n + 1:
			var x := lerpf(-1.0, 1.0, float(i) / n)
			var z := lerpf(-0.3, 1.0, float(j) / n)
			var r := Vector2(x, (z - 0.25) / 0.75).length()
			st.set_normal(Vector3.UP)
			st.set_uv(Vector2(x, z))
			st.set_color(Color(1.0, 0.0, 0.0, 1.0 - smoothstep(0.45, 1.0, r)))
			st.add_vertex(Vector3(x, 0.0, z))
	for j in n:
		for i in n:
			var i0 := j * (n + 1) + i
			for q: int in [i0, i0 + n + 1, i0 + 1, i0 + 1, i0 + n + 1, i0 + n + 2]:
				st.add_index(q)
	am = st.commit()
	var st2 := SurfaceTool.new()
	st2.begin(Mesh.PRIMITIVE_TRIANGLES)
	var zak := 0
	for zn: float in [1.0, -1.0]:
		var osa := Vector3(cos(deg_to_rad(uhel_st) * zn), 0.0, sin(deg_to_rad(uhel_st) * zn))
		var nr := osa.cross(Vector3.UP).normalized()
		for j in 5:
			for i in 5:
				var u := lerpf(-1.0, 1.0, float(i) / 4)
				var v := float(j) / 4
				st2.set_normal(nr)
				st2.set_uv(Vector2(u, v))
				st2.set_color(Color(1.0, 0.0, 0.0, (1.0 - smoothstep(0.4, 1.0, absf(u))) * smoothstep(0.0, 0.15, v) * (1.0 - smoothstep(0.35, 1.0, v))))
				st2.add_vertex(osa * u + Vector3(0.0, v, 0.0) + Vector3(0.0, 0.0, 0.25))
		for j in 4:
			for i in 4:
				var i0 := zak + j * 5 + i
				for q: int in [i0, i0 + 5, i0 + 1, i0 + 1, i0 + 5, i0 + 6]:
					st2.add_index(q)
		zak += 25
	st2.commit(am)
	return am
