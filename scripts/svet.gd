extends RefCounted
const Pravidla := preload("res://scripts/pravidla.gd")
## Svet tvrze vymodelovany v Blenderu (blender/export_game.py): nacte modely/tvrz.glb,
## priradi materialy podle jmen, postavi kolize, rostliny (MultiMesh po bunkach) a predá
## informace o ohnich, mistnostech a pouzitelnych vecech hernimu zivotu (life.gd).

const MOD := "res://modely/"
const BARVA_LOUKY := Vector3(0.145, 0.235, 0.02)   # linearne; kalibrace testem dalka (tools/test_svet.gd)
const BARVA_LESA := Vector3(0.062, 0.095, 0.015)
const BUNKA := 24.0
## textury s vyskovou mapou -> parallax (hloubka v metrech)
const HLOUBKA := {"dlazba": 0.04, "dlazba_hrad": 0.035, "kocicky": 0.05, "piskovec": 0.02, "podlaha": 0.008, "prkna_ven": 0.012, "sindel": 0.035, "skala_piskovec": 0.07, "kamen": 0.04, "kamen_lisejnik": 0.05}

var info: Dictionary
var data: Dictionary
var sum: NoiseTexture2D
var _tex := {}
var _mats := {}
var water_y := -2.75
var water_mat: ShaderMaterial          # hladina prikopu (kruhove vlnky)
## rostliny ke sberu: druh rostliny ve svete -> predmet v brasne; kazda instance je sberne misto (sber.gd)
const SBER := {"nettle_plant": "kopriva", "celandine_01": "vlastovicnik", "periwinkle_plant": "barvinek"}
var sber_spots: Array = []             # {"id", "mmi", "i", "xf"}
var vodni: Array = []                  # materialy vody (vlnky a ceřeni od hrace nastavuje voda.gd)
const VRSTVA_VODA := 1 << 19           # plochy hladin jako Area3D (zjisteni, ze hrac stoji ve vode)


func _init(p_info: Dictionary) -> void:
	info = p_info


var _krok_t := 0


# ---------------------------------------------------------------- ves v oblouku (scripts/ves_oblouk.gd)
var VES_OBLOUK := not OS.has_environment("TVRZ_VES_RADA")
var vo: RefCounted = null


## Bod stare navsi (puvodni rovna osa a jeji okoli, kudy uz cesta nevede) - mimo novou ulici.
func _vo_stara_naves(p: Vector2) -> bool:
	var q := p - Vector2(470.0, 830.0)
	var uu := q.dot(Vector2(0.76193, 0.64764))
	var vv := q.dot(Vector2(-0.64764, 0.76193))
	if uu < -88.0 or uu > 80.0 or absf(vv) > 45.0:
		return false
	return vo.od_ulice(p) > 14.0


func _vo_qrot(q: Array, b: Basis) -> Array:
	# kolize/pohyb: rotace jako [w, x, y, z]
	var qq := Quaternion(b) * Quaternion(float(q[1]), float(q[2]), float(q[3]), float(q[0]))
	return [qq.w, qq.x, qq.y, qq.z]


## Data svet.json: vse ve starem pudorysu usedlosti na nove misto; co lezi v novem pudorysu odjinud (louka, stromy
## navsi), pryc. Mrizka trava_ves (vysky, maska travy) s terenem usedlosti. Pred _ves_stare_pryc (ta uz pracuje
## s novymi ramci domu).
func _vo_data() -> void:
	vo = preload("res://scripts/ves_oblouk.gd").new()
	# vyskovy posun usedlosti: prumer terenu na novem obvodu - na starem obvodu
	for i in vo.u.size():
		var e: Dictionary = vo.u[i]
		var so := 0.0
		var sn := 0.0
		var n := 0
		for k in 24:
			var t := float(k) / 24.0 * 4.0
			var ab := Vector2()
			var a0 := float(e["hu0"])
			var a1 := float(e["hu1"])
			var b0 := float(e["hv0"])
			var b1 := float(e["hv1"])
			if t < 1.0:
				ab = Vector2(lerpf(a0, a1, t), b0)
			elif t < 2.0:
				ab = Vector2(a1, lerpf(b0, b1, t - 1.0))
			elif t < 3.0:
				ab = Vector2(lerpf(a1, a0, t - 2.0), b1)
			else:
				ab = Vector2(a0, lerpf(b1, b0, t - 3.0))
			var po := (e["oc"] as Vector2) + (e["oau"] as Vector2) * ab.x + (e["oav"] as Vector2) * ab.y
			var pn := (e["nc"] as Vector2) + (e["nau"] as Vector2) * ab.x + (e["nav"] as Vector2) * ab.y
			so += _vyska(po.x, po.y)
			sn += _vyska(pn.x, pn.y)
			n += 1
		e["dy"] = (sn - so) / n
	var cnt := {"rost": 0, "rost_pryc": 0, "vyb": 0, "kol": 0, "ost": 0}
	var bod := func(p: Array) -> int:
		return vo.stara(Vector2(float(p[0]), float(p[2])))
	var posun := func(p: Array, i: int) -> Array:
		var q: Vector3 = vo.presun3(i, Vector3(float(p[0]), float(p[1]), float(p[2])))
		return [q.x, q.y, q.z]
	# rostliny (3x4 radkove: baze 0-2, 4-6, 8-10, poloha 3, 7, 11)
	for key: String in data["rostliny"]:
		var arr: Array = data["rostliny"][key]
		var out: Array = []
		for t: Array in arr:
			var p := Vector2(float(t[3]), float(t[11]))
			var i: int = vo.stara(p)
			if i >= 0:
				var b := Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10]))
				b = vo.otoceni(i) * b
				var q: Vector3 = vo.presun3(i, Vector3(t[3], t[7], t[11]))
				out.append([b.x.x, b.y.x, b.z.x, q.x, b.x.y, b.y.y, b.z.y, q.y, b.x.z, b.y.z, b.z.z, q.z])
				cnt["rost"] += 1
			elif int((vo.nova(p, 0.5) as Array)[0]) >= 0:
				cnt["rost_pryc"] += 1
			else:
				out.append(t)
		data["rostliny"][key] = out
	for it: Dictionary in data["vybaveni"]:
		var i: int = bod.call(it["p"])
		if i >= 0:
			it["p"] = posun.call(it["p"], i)
			it["yaw"] = float(it.get("yaw", 0.0)) - float(vo.u[i]["dyaw"])
			cnt["vyb"] += 1
	var kol: Array = []
	for c: Array in data["kolize"]:
		var i: int = bod.call(c)
		if i >= 0:
			var q: Vector3 = vo.presun3(i, Vector3(c[0], c[1], c[2]))
			var r: Array = _vo_qrot([c[3], c[4], c[5], c[6]], vo.otoceni(i))
			kol.append([q.x, q.y, q.z, r[0], r[1], r[2], r[3], c[7], c[8], c[9]])
			cnt["kol"] += 1
		elif int((vo.nova(Vector2(float(c[0]), float(c[2])), 0.0) as Array)[0]) >= 0 and absf(float(c[0]) - 470.0) < 200.0:
			pass                                      # kolize stare navsi/louky v novem dvore pryc
		else:
			kol.append(c)
	data["kolize"] = kol
	for key2: String in ["ohne", "pouziti", "mistnosti"]:
		for o: Dictionary in data[key2]:
			var i: int = bod.call(o["pos"])
			if i >= 0:
				o["pos"] = posun.call(o["pos"], i)
				if o.has("yaw"):
					o["yaw"] = float(o["yaw"]) - float(vo.u[i]["dyaw"])
				elif key2 == "mistnosti":
					o["yaw"] = -float(vo.u[i]["dyaw"])
				cnt["ost"] += 1
	for e2: Dictionary in data["pohyb"]:
		var i: int = bod.call(e2.get("use", e2["pos"]))
		if i >= 0:
			e2["pos"] = posun.call(e2["pos"], i)
			if e2.has("use"):
				e2["use"] = posun.call(e2["use"], i)
			if e2.has("rot"):
				e2["rot"] = _vo_qrot(e2["rot"], vo.otoceni(i))
			# kotvy lan a retezu (svetove souradnice, druhy konec je v dilku): posun s usedlosti - jinak lano studny
			# vedlo z puvodniho mista pres cestu a plot (Misa 28. 10. „hneda klada pres cestu“)
			for k2: String in ["ropes", "chains"]:
				for rp: Array in e2.get(k2, []):
					rp[0] = posun.call(rp[0], i)
			cnt["ost"] += 1
	# nove domy (VES_STARE: stred stare chalupy, yaw osy)
	for s2: Array in VES_STARE:
		var i: int = vo.stara(Vector2(s2[1], s2[2]))
		if i >= 0:
			var q2: Vector2 = vo.presun2(i, Vector2(s2[1], s2[2]))
			s2[1] = q2.x
			s2[2] = q2.y
			s2[3] = float(s2[3]) + float(vo.u[i]["dyaw"])
	# mrizka trava_ves: vyska a maska z puvodniho mista usedlosti (+ posun), kolem prolinani; stara mista louka
	var g: Dictionary = data["trava_ves"]
	var nn := int(g["n"])
	var k := float(g["k"])
	var x0 := float(g["x0"])
	var z0 := float(g["z0"])
	var ys := Marshalls.base64_to_raw(String(g["y"]))
	var ms := Marshalls.base64_to_raw(String(g["m"]))
	var ys2 := ys.duplicate()
	var ms2 := ms.duplicate()
	var louka_m := 200
	var vz := func(arr: PackedByteArray, x: float, z: float) -> float:
		var fx := clampf((x - x0) / k, 0.0, nn - 1.001)
		var fz := clampf((z - z0) / k, 0.0, nn - 1.001)
		var i0 := floori(fx)
		var j0 := floori(fz)
		var a := arr.decode_s16((j0 * nn + i0) * 2)
		var b := arr.decode_s16((j0 * nn + i0 + 1) * 2)
		var c := arr.decode_s16(((j0 + 1) * nn + i0) * 2)
		var d := arr.decode_s16(((j0 + 1) * nn + i0 + 1) * 2)
		return lerpf(lerpf(a, b, fx - i0), lerpf(c, d, fx - i0), fz - j0) / 100.0
	var zm := 0
	for j in nn:
		for i3 in nn:
			var p := Vector2(x0 + i3 * k, z0 + j * k)
			var vh: Array = vo.vahy(p)
			var o := j * nn + i3
			if not vh.is_empty():
				var y0 := ys.decode_s16(o * 2) / 100.0
				var sw := 0.0
				var sy := 0.0
				var wmax := 0.0
				for q: Array in vh:
					var src: Vector2 = vo.zdroj2(int(q[0]), p)
					var wq := float(q[1])
					sy += wq * (maxf(float(vz.call(ys, src.x, src.y)), _breh_toku_y(src.x, src.y)) + float(vo.u[int(q[0])]["dy"]))
					sw += wq
					if wq > wmax:
						wmax = wq
						if wq > 0.5:
							var si := clampi(roundi((src.x - x0) / k), 0, nn - 1)
							var sj := clampi(roundi((src.y - z0) / k), 0, nn - 1)
							ms2[o] = ms[sj * nn + si]
				var y1 := sy / sw if sw >= 1.0 else y0 * (1.0 - sw) + sy
				ys2.encode_s16(o * 2, clampi(roundi(y1 * 100.0), -32000, 32000))
				if wmax <= 0.5 and vo.stara(p) >= 0:
					ms2[o] = louka_m
				zm += 1
			elif vo.stara(p) >= 0:
				ms2[o] = louka_m
	# ulice napric rovna (vo.uprav_y): vyska osy z mrizky po presunu, pak mrizka kolem ulice
	vo.ulice_vysky(func(q: Vector2) -> float: return float(vz.call(ys2, q.x, q.y)))
	var nr := 0
	for j in nn:
		for i3 in nn:
			var p := Vector2(x0 + i3 * k, z0 + j * k)
			var o := j * nn + i3
			var y0 := ys2.decode_s16(o * 2) / 100.0
			var y1: float = vo.uprav_y(p, y0)
			if absf(y1 - y0) > 0.005:
				ys2.encode_s16(o * 2, clampi(roundi(y1 * 100.0), -32000, 32000))
				nr += 1
	print("ves oblouk: ulice napric srovnana, %d bodu mrizky" % nr)
	g["y"] = Marshalls.raw_to_base64(ys2)
	g["m"] = Marshalls.raw_to_base64(ms2)
	# pesina od konce ulice k rybniku (ten zustal stranou za vsi)
	var ko: Vector2 = vo.na_ulici(0.92)
	# konec pesiny tesne za okrajem dilu rybnika (drive pevne 27 m od stredu = 3 m pod terenem dilu, test zasazeni
	# nad_cestou_pesina u (490, 884)): od stredu ke vsi, az je bod 1 m vne ctverce dilu
	var smer_k := (ko - RYB_C).normalized()
	var bi := Basis(Vector3.UP, RYB_YAW).inverse()
	var t := 10.0
	while t < 80.0:
		var lq := bi * Vector3(smer_k.x * t, 0.0, smer_k.y * t)
		if maxf(absf(lq.x), absf(lq.z)) - RYB_POL >= 1.0:
			break
		t += 0.5
	var cil := RYB_C + smer_k * t
	PESINY.append([ko, ko.lerp(cil, 0.35) + Vector2(4.0, -3.0), ko.lerp(cil, 0.7) + Vector2(-2.0, 4.0), cil])
	PES_SIRKA.append(float(Pravidla.cti("cesty", "pesiny_odvozene", "k_rybniku_pulsirka_m")))
	_vys = {}
	_ves_m = PackedByteArray()
	print("ves oblouk data: %s, mrizka %d bodu, posuny %s" % [cnt, zm, vo.u.map(func(e: Dictionary) -> String: return "%.1f" % float(e["dy"]))])


## Scena: trojuhelniky siti vsi a samostatne uzly v pudorysu usedlosti na nove misto; teren Teren_ves (vyska a barva
## vrcholu) s usedlosti, stara mista zatravnit (barva louky).
func _vo_scena(root: Node3D) -> void:
	var t0 := Time.get_ticks_msec()
	var nt := 0
	var nu := 0
	var velke := {}
	for n in root.find_children("Vesnice*", "MeshInstance3D", true, false):
		velke[n] = true
	for mi: MeshInstance3D in velke:
		nt += _vo_sit(mi)
	# samostatne uzly (dvere, vrata, drobne stavby) se stredem ve starem pudorysu
	for n2 in root.find_children("*", "MeshInstance3D", true, false):
		var mi2 := n2 as MeshInstance3D
		if velke.has(mi2) or String(mi2.name).begins_with("Teren") or mi2.mesh == null:
			continue
		var bb: AABB = mi2.global_transform * mi2.get_aabb()
		if bb.size.x > 40.0 or bb.size.z > 40.0:
			continue
		var c := bb.get_center()
		var i: int = vo.stara(Vector2(c.x, c.z))
		if i >= 0:
			mi2.global_transform = vo.xf(i) * mi2.global_transform
			nu += 1
	var ntr := 0
	# i jemny teren u toku a rybniku (Teren_toky, kraj._teren_u_vody): nahrazuje bunky Teren_ves, posun usedlosti a
	# srovnani ulic na nem musi byt stejne (test zasazeni 28. 10.: ulice napric 16-19 % jen nad tokem ve vsi)
	for n3 in root.find_children("Teren_ves*", "MeshInstance3D", true, false) + root.find_children("Teren_toky", "MeshInstance3D", true, false):
		ntr += _vo_teren(n3 as MeshInstance3D)
	print("ves oblouk scena: %d troj. siti, %d uzlu, %d vrcholu terenu, %d ms" % [nt, nu, ntr, Time.get_ticks_msec() - t0])


func _vo_sit(mi: MeshInstance3D) -> int:
	var am := mi.mesh as ArrayMesh
	if am == null:
		return 0
	var gx := mi.global_transform
	var inv := gx.affine_inverse()
	var nove := ArrayMesh.new()
	var n := 0
	for si in am.get_surface_count():
		var arr := am.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var nr: PackedVector3Array = arr[Mesh.ARRAY_NORMAL] if arr[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
		var tg: PackedFloat32Array = arr[Mesh.ARRAY_TANGENT] if arr[Mesh.ARRAY_TANGENT] != null else PackedFloat32Array()
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		# kazdy vrchol podle usedlosti sveho trojuhelniku (vrcholy sdilene mezi usedlostmi nejsou - jsou daleko od sebe)
		var kam := PackedInt32Array()
		kam.resize(v.size())
		kam.fill(-1)
		var nt := idx.size() / 3 if not idx.is_empty() else v.size() / 3
		if idx.is_empty():
			idx.resize(v.size())
			for q in v.size():
				idx[q] = q
		# po souvislych dilech (Misa 0.98: hnede tyce ve vzduchu pres cestu - dil na hranici stareho pudorysu se
		# po trojuhelnicich natahl ze stareho mista na nove): cely dil jede s usedlosti podle sveho stredu, nebo
		# zustane; dil odjinud, ktery by zustal v novem pudorysu usedlosti (plochy navsi), pryc
		var kus := _kusy_trojuhelniku(v, idx)
		var stred := {}
		for t in nt:
			var c3 := v[idx[t * 3]] + v[idx[t * 3 + 1]] + v[idx[t * 3 + 2]]
			var s0: Array = stred.get(kus[t], [Vector3.ZERO, 0])
			stred[kus[t]] = [s0[0] + c3 / 3.0, int(s0[1]) + 1]
		var rozhod := {}
		for r0 in stred:
			var c := gx * ((stred[r0][0] as Vector3) / float(stred[r0][1]))
			var i: int = vo.stara(Vector2(c.x, c.z), 0.5)
			if i < 0 and int(vo.nova(Vector2(c.x, c.z))[0]) >= 0:
				i = -2
			rozhod[r0] = i
		var pryc := 0
		for t in nt:
			var i: int = rozhod[kus[t]]
			if i == -1:
				continue
			for j in 3:
				kam[idx[t * 3 + j]] = i
			n += 1
		for vi in v.size():
			var i2 := kam[vi]
			if i2 == -2:
				v[vi] = v[idx[0]]                         # dil pryc: nulova plocha
				pryc += 1
				continue
			if i2 < 0:
				continue
			var x: Transform3D = inv * vo.xf(i2) * gx
			v[vi] = x * v[vi]
			if not nr.is_empty():
				nr[vi] = (x.basis * nr[vi]).normalized()
			if not tg.is_empty():
				var tv := (x.basis * Vector3(tg[vi * 4], tg[vi * 4 + 1], tg[vi * 4 + 2])).normalized()
				tg[vi * 4] = tv.x
				tg[vi * 4 + 1] = tv.y
				tg[vi * 4 + 2] = tv.z
		arr[Mesh.ARRAY_VERTEX] = v
		arr[Mesh.ARRAY_INDEX] = idx
		if not nr.is_empty():
			arr[Mesh.ARRAY_NORMAL] = nr
		if not tg.is_empty():
			arr[Mesh.ARRAY_TANGENT] = tg
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(si, am.surface_get_material(si))
		nove.surface_set_name(si, am.surface_get_name(si))
	var ovr: Array = []
	for si2 in am.get_surface_count():
		ovr.append(mi.get_surface_override_material(si2))
	mi.mesh = nove
	for si3 in ovr.size():
		mi.set_surface_override_material(si3, ovr[si3])
	return n


## Vyska brehu maleho toku v bode koryta (hladina z voda.json osa_xzy + toky_tvar breh_m), jinak -INF. Mrizka 16 m.
var _breh_mriz := {}


func _breh_toku_y(x: float, z: float) -> float:
	if _breh_mriz.is_empty():
		var tt: Dictionary = Pravidla.cti("voda", "toky_tvar")
		_breh_mriz[Vector2i(1 << 20, 0)] = []
		for t: Dictionary in Pravidla.cti("voda", "toky"):
			var o: Array = t["osa_xzy"]
			var pas := float(t["sirka_m"]) * 0.5 + float(tt["breh_sirka_m"]) + 1.0
			for i in o.size() - 1:
				var e := [Vector2(float(o[i][0]), float(o[i][1])), Vector2(float(o[i + 1][0]), float(o[i + 1][1])),
						float(o[i][2]) + float(tt["breh_m"]), float(o[i + 1][2]) + float(tt["breh_m"]), pas]
				for cx in range(floori((minf(e[0].x, e[1].x) - pas) / 16.0), floori((maxf(e[0].x, e[1].x) + pas) / 16.0) + 1):
					for cz in range(floori((minf(e[0].y, e[1].y) - pas) / 16.0), floori((maxf(e[0].y, e[1].y) + pas) / 16.0) + 1):
						var c := Vector2i(cx, cz)
						if not _breh_mriz.has(c):
							_breh_mriz[c] = []
						(_breh_mriz[c] as Array).append(e)
	var q := Vector2(x, z)
	var best := -INF
	var bd := INF
	for e: Array in _breh_mriz.get(Vector2i(floori(x / 16.0), floori(z / 16.0)), []):
		var c := Geometry2D.get_closest_point_to_segment(q, e[0], e[1])
		var d := c.distance_to(q)
		if d < float(e[4]) and d < bd:
			bd = d
			var f := clampf((e[0] as Vector2).distance_to(c) / maxf((e[0] as Vector2).distance_to(e[1]), 1e-4), 0.0, 1.0)
			best = lerpf(float(e[2]), float(e[3]), f)
	return best


func _vo_teren(mi: MeshInstance3D) -> int:
	var am := mi.mesh as ArrayMesh
	if am == null:
		return 0
	var gx := mi.global_transform
	var inv := gx.affine_inverse()
	var nove := ArrayMesh.new()
	var n := 0
	for si in am.get_surface_count():
		var arr := am.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var cl: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
		# puvodni vysky a barvy po 1 m (vzorkovani zdroje)
		var mapa := {}
		var w := PackedVector3Array()
		w.resize(v.size())
		for vi in v.size():
			w[vi] = gx * v[vi]
			var key := Vector2i(roundi(w[vi].x), roundi(w[vi].z))
			if not mapa.has(key):
				mapa[key] = vi
		var louka := Color(0, 0, 0, 0)
		var nl := 0
		if not cl.is_empty():
			for vi in v.size():
				if cl[vi].g > 0.8 and vo.stara(Vector2(w[vi].x, w[vi].z), 3.0) < 0 and nl < 200:
					louka += cl[vi]
					nl += 1
			louka = louka / maxf(nl, 1)
		var najdi := func(p: Vector2) -> int:
			var c := Vector2i(roundi(p.x), roundi(p.y))
			for r in 3:
				for dx in range(-r, r + 1):
					for dz in range(-r, r + 1):
						if mapa.has(c + Vector2i(dx, dz)):
							return mapa[c + Vector2i(dx, dz)]
			return -1
		var v2 := v.duplicate()
		var cl2 := cl.duplicate()
		for vi in v.size():
			var p := Vector2(w[vi].x, w[vi].z)
			var vh: Array = vo.vahy(p)
			if not vh.is_empty():
				var sw := 0.0
				var sy := 0.0
				var sc := Color(0, 0, 0, 0)
				for q: Array in vh:
					var sv: int = najdi.call(vo.zdroj2(int(q[0]), p))
					if sv < 0:
						continue
					var wq := float(q[1])
					# zdroj v korytu maleho toku (stare misto usedlosti, kudy ted tece potok): vyska brehu, ne dna -
					# jinak si dum na novem miste odnese koryto (test zasazeni 28. 10.: dum 7 podlaha 0,8 m nad terenem)
					sy += wq * (maxf(w[sv].y, _breh_toku_y(w[sv].x, w[sv].z)) + float(vo.u[int(q[0])]["dy"]))
					if not cl.is_empty():
						sc += cl[sv] * wq
					sw += wq
				if sw <= 0.0:
					continue
				var y0 := w[vi].y
				var y1 := sy / sw if sw >= 1.0 else y0 * (1.0 - sw) + sy
				v2[vi] = inv * Vector3(w[vi].x, y1, w[vi].z)
				if not cl.is_empty():
					var c0: Color = louka if (vo.stara(p) >= 0 and nl > 0) else cl[vi]
					cl2[vi] = sc / sw if sw >= 1.0 else c0 * (1.0 - sw) + sc
				n += 1
			elif not cl.is_empty() and vo.stara(p) >= 0 and nl > 0:
				cl2[vi] = louka
		# ulice napric rovna (vo.uprav_y, stejne jako mrizka trava_ves v _vo_data)
		for vi in v2.size():
			var wq := gx * v2[vi]
			var yq: float = vo.uprav_y(Vector2(wq.x, wq.z), wq.y)
			if absf(yq - wq.y) > 0.005:
				v2[vi] = inv * Vector3(wq.x, yq, wq.z)
		arr[Mesh.ARRAY_VERTEX] = v2
		if not cl.is_empty():
			arr[Mesh.ARRAY_COLOR] = cl2
		arr[Mesh.ARRAY_NORMAL] = null
		arr[Mesh.ARRAY_TANGENT] = null
		var st := SurfaceTool.new()
		st.create_from_arrays(arr)
		st.generate_normals()
		st.commit(nove)
		nove.surface_set_material(si, am.surface_get_material(si))
		nove.surface_set_name(si, am.surface_get_name(si))
	var ovr: Array = []
	for si2 in am.get_surface_count():
		ovr.append(mi.get_surface_override_material(si2))
	mi.mesh = nove
	for si3 in ovr.size():
		mi.set_surface_override_material(si3, ovr[si3])
	return n


## Misa 0.89 „nacita 2x dele“: delka kazdeho kroku stavby sveta (nad 300 ms do logu)
## Kroky stavby, ktere zmenily sit terenu (Teren*): kazda uprava terenu meni mi.mesh - stopa = instance siti po kroku.
## Test zamek_terenu porovna se zaznamem poradi v pasma.test.poradi_terenu (pipeline: pozdejsi krok nehybe drivejsim).
var teren_kroky: Array = []
var _teren_stopa := {}


func _protokol_rozdil(z: Dictionary, stara: Mesh, mi: MeshInstance3D) -> void:
	if stara == null or mi.mesh == null:
		return
	var xf := mi.global_transform
	var bunky: Dictionary = z["bunky"]
	# podle polohy vrcholu (x, z po 5 cm), ne podle poradi - SurfaceTool a deleni siti vrcholy preskladaji
	var stare := {}
	for si in stara.get_surface_count():
		for q: Vector3 in stara.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
			stare[Vector2i(roundi(q.x * 20.0), roundi(q.z * 20.0))] = q.y
	for si in mi.mesh.get_surface_count():
		var b: PackedVector3Array = mi.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]
		for i in b.size():
			var kk := Vector2i(roundi(b[i].x * 20.0), roundi(b[i].z * 20.0))
			var dy := (b[i].y - float(stare[kk])) if stare.has(kk) else 0.0
			if absf(dy) > 0.02 or not stare.has(kk):
				z["vrcholu"] = int(z["vrcholu"]) + 1
				z["max_dy"] = maxf(float(z["max_dy"]), absf(dy))
				var w := xf * b[i]
				var c := "%d,%d" % [floori(w.x / 8.0), floori(w.z / 8.0)]
				bunky[c] = maxf(float(bunky.get(c, 0.0)), absf(dy) if absf(dy) > 0.02 else 0.03)


func protokol_zapis() -> void:
	if not PROTOKOL:
		return
	# osy cest tak, jak je hra postavila (po posunu vsi) - mapa je kresli pod kroky a chyby
	var cesty: Array = []
	for o: Dictionary in cesty_osy:
		var pp: PackedVector2Array = o["p"]
		var l: Array = []
		for i in range(0, pp.size(), 2):
			l.append([snappedf(pp[i].x, 0.1), snappedf(pp[i].y, 0.1)])
		cesty.append(l)
	var f := FileAccess.open("res://build/protokol_stavby.json", FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify({"kroky": protokol, "cesty": cesty}))


## Protokol stavby (Misa 28. 10.: „at ti to pomaha stavet a ukazuje co a jak“): pri PROTOKOL u kazdeho kroku, ktery
## zmenil teren, rozdil vrcholu proti predchozi siti - pocet, nejvetsi zmena vysky, bunky 8 m se zmenou (mapa
## tools/protokol_mapa.py). Zapis build/protokol_stavby.json na konci stavby.
var PROTOKOL := OS.has_environment("TVRZ_TEST") or OS.has_environment("TVRZ_MERENI") or OS.has_environment("TVRZ_PROTOKOL")
var protokol: Array = []


func _krok_cas(co: String) -> void:
	if _tvrz_root:
		var zmena := 0
		var zaznam := {"krok": co, "site": [], "vrcholu": 0, "max_dy": 0.0, "bunky": {}}
		for t0 in _tvrz_root.find_children("Teren*", "MeshInstance3D", true, false):
			var mi := t0 as MeshInstance3D
			var id := mi.mesh.get_instance_id() if mi.mesh else 0
			var k := t0.get_instance_id()
			if _teren_stopa.has(k) and int((_teren_stopa[k] as Array)[0]) != id:
				zmena += 1
				(zaznam["site"] as Array).append(String(mi.name))
				if PROTOKOL:
					_protokol_rozdil(zaznam, (_teren_stopa[k] as Array)[1], mi)
			_teren_stopa[k] = [id, mi.mesh if PROTOKOL else null]
		if zmena > 0:
			teren_kroky.append([co, zmena])
			if PROTOKOL:
				protokol.append(zaznam)
				print("PROTOKOL %-34s %2d siti, %6d vrcholu, max dy %.2f m, %d bunek 8 m" % [co, zmena, zaznam["vrcholu"], zaznam["max_dy"], (zaznam["bunky"] as Dictionary).size()])
	var t := Time.get_ticks_msec()
	if t - _krok_t > 300:
		print("STAVBA %s %d ms" % [co, t - _krok_t])
		var dg: Object = Engine.get_meta("diag", null)
		if dg:
			dg.faze("STAVBA %s %d ms" % [co, t - _krok_t])      # Misa 0.90: casy nacitani i v diag.log z tabletu
	_krok_t = t


func build(parent: Node3D, quality: int) -> void:
	_krok_t = Time.get_ticks_msec()
	var f := FileAccess.open(MOD + "svet.json", FileAccess.READ)
	data = JSON.parse_string(f.get_as_text())
	water_y = float(data.get("voda_y", -2.75))
	_pesiny_nacti()                            # pravidla/svet/cesty.json (pred _vo_data, ta pridava pesinu k rybniku)
	pasma()                                    # pasma zasazeni nacist v hlavnim vlakne (vlakna louky jen ctou)
	if VES_OBLOUK:
		_vo_data()
		_krok_cas("_vo_data")
	_ves_stare_pryc()
	_krok_cas("_ves_stare_pryc")
	_make_noise()
	_krok_cas("_make_noise")
	var scene: PackedScene = load(MOD + "tvrz.glb")
	var root := scene.instantiate()
	root.name = "Tvrz"
	parent.add_child(root)
	_tvrz_root = root
	_krok_cas("nacteni sveta")                  # stopa siti terenu z exportu
	if VES_OBLOUK:
		_vo_scena(root)
		_krok_cas("_vo_scena")
	_koryto_terenu(root)
	_krok_cas("_koryto_terenu")
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		_apply_materials(mi)
		# oboustranne stiny: tenke vrstvy (omitka uvnitr, prkna) jinak propousteji svetlo ve skvirach
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		var nm := String(mi.name)
		if nm == "Reka_voda":
			_reka_voda_mesh = mi.mesh
		if nm == "Reka_voda" and reka_predpecena():
			mi.visible = false               # potok: Waterways (_reka), mrizkova hladina se zubatym brehem pryc
		if nm == "Teren_cesta_kamen":
			mi.visible = false               # tmave kocici hlavy pres cestu s ostrou hranou (Misa 17. 10.): pod nimi je cesta
			continue
		if nm.ends_with("_zahrady") and mi.mesh:
			_bez_zeli(mi)
		if nm == "Skaly":
			mi.visible = false               # zaoblene balvany u tvrze: textura ze sveta v "letokruzich" (Misa: smazat)
		if nm == "Most_potok":
			_most_kuly(mi)
			_most_podlozka(mi)
		# sukne jemne site jen pro oko: jako kolize byla svislou stenou na okraji Teren_most (test prochod, breh potoka)
		if (nm.begins_with("Teren") or nm.begins_with("Nadvori")) and not nm.ends_with("_sukne"):
			_trimesh(mi)
		if nm.begins_with("Teren") or nm.begins_with("Reka") or nm.begins_with("Ruiny") or nm.begins_with("Skaly") \
				or nm.ends_with("_zahrady") or nm.begins_with("Hnojiste"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF      # rozpocet: teren, voda, ruiny, zahrady nekreslit do stinu
		if nm.begins_with("Rakos") or nm.begins_with("Slama"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.visibility_range_end = 70.0
	_reka(parent)
	_krok_cas("_reka")
	_zaplaty(root)
	_krok_cas("_zaplaty")
	_kontrola_hladiny(parent)
	_krok_cas("_kontrola_hladiny")
	_collisions(parent)
	_krok_cas("_collisions")
	_static_items(parent)
	_krok_cas("_static_items")
	_lom_sit_priprav(root)
	_krok_cas("_lom_sit_priprav")
	_lom_vybaveni()
	_krok_cas("_lom_vybaveni")
	_lom_sut(parent)
	_krok_cas("_lom_sut")
	_lom_stena_svisla(root, parent)
	_krok_cas("_lom_stena_svisla")
	_rybnik_dil(root, parent)
	_krok_cas("_rybnik_dil")
	_mlyn_dil(root, parent)
	_krok_cas("_mlyn_dil")
	_staj_kone(parent)
	_ves_domy(root)
	_krok_cas("_ves_domy")
	_zamek_terenu(parent)                      # pipeline krok 4/zamek: mrizka vysek = hotova sit terenu (pred rostlinami)
	_krok_cas("_zamek_terenu")
	_erb_tvrze(root)
	_krok_cas("_erb_tvrze")
	_info()
	_krok_cas("_info")
	_plants(parent, quality)
	_krok_cas("_plants")
	_rozdel_site(root)
	_krok_cas("_rozdel_site")
	_kolize_cisteni(parent)
	_krok_cas("_kolize_cisteni")
	_okluzory(parent)
	_krok_cas("_okluzory")
	protokol_zapis()


# ------------------------------------------------------------------ deleni velkych siti (0.60)

## Velke sloucene site tvrz.glb (teren, ves, rakos, ochozy, ruiny - az 1400 m) se kreslily cele, kdykoli byl videt
## kousek: zadne orezani pohledem ani LOD (prikop 2,8 M troj.). Po stavbe sveta (koryto, kolize, rostliny pouzily
## puvodni site) se rozdeli na ctverce a kazdy dostane LOD; puvodni sit se uvolni, jeji kolize zustava.
const DELIT_OD := 60.0                 # site vetsi nez 60 m a s vic nez 8000 troj.
const DELIT_TROJ := 8000


func _rozdel_site(root: Node3D) -> void:
	if OS.has_environment("TVRZ_NEDELIT"):
		return
	var t0 := Time.get_ticks_msec()
	var vody := {}
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var me := (mi as MeshInstance3D).mesh
		if me == null:
			continue
		for i in me.get_surface_count():
			var mt := me.surface_get_material(i)
			if mt and String(mt.resource_name).begins_with("voda"):
				vody[mi] = true                  # hladiny drzi nadrz.gd (shader, hloubka) - nedelit
	var n_siti := 0
	var n_kusu := 0
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		if mi.mesh == null or not mi.visible or vody.has(mi) or nm.begins_with("Pohyb") or mi.mesh.get_blend_shape_count() > 0:
			continue
		# teren se nedeli (0.62): ImporterMesh.generate_lods v behu hry LOD nevytvori (0 urovni, overeno), takze bezove
		# plachty a pyramidy 0.60 a bledé skvrny na kopcich 0.61 delalo samo deleni terenu - teren zustava cely
		if nm.begins_with("Teren"):
			continue
		var bb := mi.mesh.get_aabb()
		var vel := maxf(bb.size.x, bb.size.z)
		var troj := 0
		for i in mi.mesh.get_surface_count():
			troj += mi.mesh.surface_get_array_index_len(i) / 3
		if vel < DELIT_OD or troj < DELIT_TROJ:
			# 0.60: stavby tvrze bez LOD z importu (Ochozy 55 k, vrata 2x 22 k, VezDrevo 36 k...) - dogenerovat
			continue
		var krok := clampf(vel / 5.0, 128.0, 640.0)        # 0.60: vel/10 (64 m) = prikop 1770 kresleni; vetsi ctverce
		var nk := _rozdel(mi, krok)
		print("  deleni %s: %d troj, %.0f m -> %d kusu po %.0f m" % [nm, troj, vel, nk, krok])
		n_kusu += nk
		n_siti += 1
	print("deleni siti: %d siti -> %d kusu, %d ms" % [n_siti, n_kusu, Time.get_ticks_msec() - t0])


func _rozdel(mi: MeshInstance3D, krok: float) -> int:
	var me := mi.mesh
	var kusy := {}                                   # Vector2i -> [[pole povrchu, material], ...]
	for s in me.get_surface_count():
		var a := me.surface_get_arrays(s)
		var mat := mi.get_active_material(s)
		var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		if idx.is_empty():
			idx.resize(v.size())
			for i in v.size():
				idx[i] = i
		# trojuhelniky podle ctverce teziste
		var podle := {}
		for t in idx.size() / 3:
			var c := (v[idx[t * 3]] + v[idx[t * 3 + 1]] + v[idx[t * 3 + 2]]) / 3.0
			var k := Vector2i(floori(c.x / krok), floori(c.z / krok))
			if not podle.has(k):
				podle[k] = []
			(podle[k] as Array).append(t)
		var mapa := PackedInt32Array()
		mapa.resize(v.size())
		mapa.fill(-1)
		for k: Vector2i in podle:
			var tr: Array = podle[k]
			var pouzite := PackedInt32Array()
			var ni := PackedInt32Array()
			ni.resize(tr.size() * 3)
			for j in tr.size():
				for e in 3:
					var vi := idx[tr[j] * 3 + e]
					if mapa[vi] < 0:
						mapa[vi] = pouzite.size()
						pouzite.append(vi)
					ni[j * 3 + e] = mapa[vi]
			for vi in pouzite:
				mapa[vi] = -1
			var na := []
			na.resize(Mesh.ARRAY_MAX)
			na[Mesh.ARRAY_INDEX] = ni
			for ai in [Mesh.ARRAY_VERTEX, Mesh.ARRAY_NORMAL, Mesh.ARRAY_TANGENT, Mesh.ARRAY_COLOR, Mesh.ARRAY_TEX_UV, Mesh.ARRAY_TEX_UV2]:
				if a[ai] == null:
					continue
				var src = a[ai]
				var sl := 4 if ai == Mesh.ARRAY_TANGENT else 1
				var dst = src.slice(0, 0)              # prazdne pole stejneho typu (duplicate by kopiroval cele)
				dst.resize(pouzite.size() * sl)
				for j in pouzite.size():
					for q in sl:
						dst[j * sl + q] = src[pouzite[j] * sl + q]
				na[ai] = dst
			if not kusy.has(k):
				kusy[k] = []
			(kusy[k] as Array).append([na, mat])
	for k: Vector2i in kusy:
		var im := ImporterMesh.new()
		for pv: Array in kusy[k]:
			im.add_surface(Mesh.PRIMITIVE_TRIANGLES, pv[0], [], {}, pv[1])
		var kus := MeshInstance3D.new()
		kus.name = "%s_k%d_%d" % [mi.name, k.x, k.y]
		kus.mesh = im.get_mesh()
		kus.transform = mi.transform
		kus.cast_shadow = mi.cast_shadow
		kus.visibility_range_end = mi.visibility_range_end
		kus.visibility_range_end_margin = mi.visibility_range_end_margin
		kus.visibility_range_fade_mode = mi.visibility_range_fade_mode
		mi.get_parent().add_child(kus)
	mi.mesh = null
	return kusy.size()


# ------------------------------------------------------------------ materialy

func _make_noise() -> void:
	var fn := FastNoiseLite.new()
	fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	fn.frequency = 0.012
	fn.fractal_octaves = 5
	sum = NoiseTexture2D.new()
	sum.width = 512
	sum.height = 512
	sum.seamless = true
	sum.noise = fn
	sum.generate_mipmaps = true


func _t(name: String, kind: String) -> Texture2D:
	var key := "%s_%s" % [name, kind]
	if not _tex.has(key):
		_tex[key] = load(MOD + "textury/%s.jpg" % key)
	return _tex[key]


var _alb := {}


func _albedo() -> Dictionary:
	if _alb.is_empty() and FileAccess.file_exists(MOD + "textury/albedo.json"):
		_alb = JSON.parse_string(FileAccess.get_file_as_string(MOD + "textury/albedo.json"))
	return _alb


func _size(name: String) -> float:
	var s: Array = data["textury"].get(name, [2.0, 2.0])
	return float(s[0])


func material(name: String) -> Material:
	var base := name.split(".")[0]
	if _mats.has(base):
		return _mats[base]
	var d: Dictionary = data["materialy"].get(base, {})
	var m: Material
	if base == "popel":
		# vrstva popela pod poleny = plocha deska (Misa 0.52 dvakrat): neviditelna, polena lezi na kamennem lozi krbu
		var sp := StandardMaterial3D.new()
		sp.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		sp.albedo_color = Color(0, 0, 0, 0)
		_mats[base] = sp
		return sp
	if base == "uhli":
		var su := StandardMaterial3D.new()
		su.albedo_color = Color(0.05, 0.04, 0.035)
		su.emission_enabled = true
		su.emission = Color(1.0, 0.35, 0.08)
		su.emission_energy_multiplier = 0.6             # doutnajici uhliky
		su.roughness = 0.9
		_mats[base] = su
		return su
	match String(d.get("type", "")):
		"zdivo":
			var s := ShaderMaterial.new()
			s.shader = load("res://shaders/zdivo.gdshader")
			var om: String = d["omitka"]
			s.set_shader_parameter("kamen_a", _t("zdivo", "diff"))
			s.set_shader_parameter("kamen_n", _t("zdivo", "nor"))
			s.set_shader_parameter("kamen_r", _t("zdivo", "rough"))
			s.set_shader_parameter("kamen_h", _t("zdivo", "disp"))
			s.set_shader_parameter("omitka_a", _t(om, "diff"))
			s.set_shader_parameter("omitka_n", _t(om, "nor"))
			s.set_shader_parameter("omitka_r", _t(om, "rough"))
			s.set_shader_parameter("kamen_m", _size("zdivo"))
			s.set_shader_parameter("omitka_m", _size(om))
			s.set_shader_parameter("kryti", float(d["kryti"]))
			s.set_shader_parameter("tint", _v3(d["tint"]))
			s.set_shader_parameter("kamen_tint", _v3(d["kamen"]))
			s.set_shader_parameter("spina", float(d["spina"]))
			s.set_shader_parameter("sum", sum)
			m = s
		"tex":
			var s2 := ShaderMaterial.new()
			s2.shader = load("res://shaders/textura.gdshader")
			var tx: String = d["tex"]
			s2.set_shader_parameter("tex_a", _t(tx, "diff"))
			s2.set_shader_parameter("tex_n", _t(tx, "nor"))
			s2.set_shader_parameter("tex_r", _t(tx, "rough"))
			s2.set_shader_parameter("velikost", _size(tx))
			s2.set_shader_parameter("prohodit", bool(d["swap"]))
			s2.set_shader_parameter("svet", String(d["coord"]) == "world")
			s2.set_shader_parameter("tint", _v3(d["tint"]))
			s2.set_shader_parameter("sedost", float(d.get("grey", 0.0)))
			if base == "deska_stodola":
				# Misa 0.83: stodola temer cerna - zvetrala prkna sedohneda (KCD2), svetlejsi
				s2.set_shader_parameter("tint", _v3(d["tint"]) * 1.7)
			if d.has("tint2"):
				s2.set_shader_parameter("tint2", _v3(d["tint2"]))
				s2.set_shader_parameter("pestrost", 1.0)
			if tx in ["skala_piskovec", "kamen_lisejnik", "kamen"]:
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("antitile", 1.0)
				s2.set_shader_parameter("skvrny", 1.0)
			if tx == "sindel":
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("skvrny", 1.0)
				s2.set_shader_parameter("radky", 1.0)
			if tx in ["tram", "prkna_ven", "okenice", "omitka_bila", "malta", "dosky", "drevo_stare", "kura"] and String(base) not in ["dub", "deska", "prkna"]:
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("stekance", 0.55 if String(base).begins_with("roubeni") or String(base) in ["lata", "dub_ven", "sindel_hra"] else 0.4)
				s2.set_shader_parameter("skvrny", 0.6)
			if bool(d["swap"]) and String(d["coord"]) == "uv":
				s2.set_shader_parameter("kus", 1.0)
			if HLOUBKA.has(tx) and (String(d["coord"]) == "world" or tx in ["sindel", "skala_piskovec"]):
				s2.set_shader_parameter("tex_h", _t(tx, "disp"))
				s2.set_shader_parameter("hloubka", HLOUBKA[tx])
			m = s2
		"zem":
			var s3 := ShaderMaterial.new()
			s3.shader = load("res://shaders/zem.gdshader")
			# cesty, dvory, pesiny: udusana hlina bez sterku (fotka "hlina" ma bile oblazky a listi - na tabletu sterk,
			# hlaseni 0.54 bod 3); tmavsi nez louka
			# vsechna useslapana zem z atlasu hliny cest (pravidla povrchu A, radce 15:20): cesty, pesiny, dvory
			s3.set_shader_parameter("hlina_a", load("res://obrazky/cesta/cesta_atlas_a.jpg"))
			s3.set_shader_parameter("hlina_n", load("res://obrazky/cesta/cesta_atlas_n.jpg"))
			s3.set_shader_parameter("louka_a", _t("louka", "diff"))
			s3.set_shader_parameter("louka_n", _t("louka", "nor"))
			s3.set_shader_parameter("zrno", load("res://obrazky/zrno_travy.png"))
			s3.set_shader_parameter("letecky_a", _t("louka_letecky", "diff"))
			s3.set_shader_parameter("louka_dal_a", _t("louka_dal", "diff"))
			s3.set_shader_parameter("louka_dal_m", _size("louka_dal"))
			s3.set_shader_parameter("obili_a", _t("pole_obili", "diff"))
			s3.set_shader_parameter("oranice_a", _t("pole_oranice", "diff"))
			s3.set_shader_parameter("obili_m", _size("pole_obili"))
			# kalibrace odrazivosti: fotka * (skutecna odrazivost povrchu / prumer fotky), viz tools/albedo_textur.py
			s3.set_shader_parameter("hlina_k", 0.64)          # atlas cest: stred jasu ~140 (rozbor fotek KCD2, 0.82)
			for u: Array in [     # Misa 0.65: "cesta moc hneda, spis svetlejsi" (0,05 = mokra hlina)

					["obili_k", "pole_obili", 0.20], ["oranice_k", "pole_oranice", 0.10]]:
				s3.set_shader_parameter(u[0], u[2] / maxf(float(_albedo().get(u[1], u[2])), 0.01))
			# louka: barva podkladu = prumer atlasu travy po kanalech -> hrana trsu zmizi
			var at: Array = _albedo().get("atlas_travy_rgb", [0.1, 0.125, 0.025])
			# barva louky z dalky = louka, jak ji hrac vidi vykreslenou (trsy nasvicene shora a s prosvitem, sRGB ~85,118,36),
			# ne prumer atlasu (89,99,44 = olivove hneda - "dalka hneda/seda", hlaseni 0.55 bod 6); overuje test dalka
			s3.set_shader_parameter("barva_louky", BARVA_LOUKY)
			s3.set_shader_parameter("lom_rect", Vector4(100.0, LOM_Z.x - 16.0, 180.0, LOM_Z.y + 40.0))
			s3.set_shader_parameter("lom_albedo", float(Pravidla.cti("plochy", "lom", "albedo")))
			s3.set_shader_parameter("lom_cerstve", LESENI_Z)
			var pata := PackedFloat32Array()
			for k in 16:
				pata.append(lom_stena_x(LOM_Z.x + k * 5.0))
			s3.set_shader_parameter("lom_pata", pata)
			if TRZISTE:
				s3.set_shader_parameter("trziste", Vector4(TRZ_O.x, TRZ_O.y, TRZ_U.x, TRZ_U.y))
				s3.set_shader_parameter("ves_rovna", not VES_OBLOUK)
				s3.set_shader_parameter("trziste_r", Vector4(TRZ_R.position.x, TRZ_R.end.x, TRZ_R.position.y, TRZ_R.end.y))
			s3.set_shader_parameter("lom_y", maxf(_vyska(lom_stena_x(930.0) + 12.0, 930.0), _vyska(lom_stena_x(970.0) + 12.0, 970.0)))
			s3.set_shader_parameter("barva_lesa", BARVA_LESA)
			for u2: Array in [["louka_k", "louka"], ["louka_dal_k", "louka_dal"]]:
				var fr: Array = _albedo().get(String(u2[1]) + "_rgb", at)
				# x 1,1 (driv 0,8; 1,3 = svetle zlute plochy u pesin na tabletu, 0.57): teren louky jako osvetleny list, jinak je mezera mezi trsy tmava dira
				# (radce 09:05 bod 2, test dira)
				s3.set_shader_parameter(u2[0], Vector3(float(at[0]) / float(fr[0]), float(at[1]) / float(fr[1]), float(at[2]) / float(fr[2])) * 0.95)   # Misa 0.68 (7,48), (460,790): svetle ploske mezi trsy
			s3.set_shader_parameter("oranice_m", _size("pole_oranice"))
			s3.set_shader_parameter("hlina_m", _size("pesina"))
			s3.set_shader_parameter("louka_m", _size("louka"))
			s3.set_shader_parameter("letecky_m", _size("louka_letecky"))
			s3.set_shader_parameter("sum", sum)
			m = s3
		"rybnik":
			# rybnik (okrehek, mirne kalny) a potok (tekouci, cisty - dno videt)
			var s4 := ShaderMaterial.new()
			s4.shader = load("res://shaders/voda.gdshader")
			s4.set_shader_parameter("nmap", load("res://obrazky/voda_normaly.png"))
			s4.set_shader_parameter("sum", sum)
			var tek := float(d.get("tekouci", 0.0))
			s4.set_shader_parameter("tekouci", tek)
			s4.set_shader_parameter("okrehek", 0.0 if tek > 0.5 else 1.0)
			s4.set_shader_parameter("kalnost", 0.35 if tek > 0.5 else 0.82)
			s4.set_shader_parameter("zakal", Color(0.1, 0.11, 0.07) if tek > 0.5 else Color(0.13, 0.16, 0.10))
			if tek < 0.5:
				s4.set_shader_parameter("deep", Color(0.08, 0.115, 0.08))         # zelenohneda, ne cerna (radce 16:40 bod 2)
			if base == "voda_prikop":
				# prikop: vzhled z voda.json prikop (okrehek, kalnost, hloubka)
				var pk: Dictionary = Pravidla.cti("voda", "prikop")
				s4.set_shader_parameter("okrehek", float(pk["okrehek"]))
				s4.set_shader_parameter("kalnost", float(pk["kalnost"]))
				s4.set_shader_parameter("deep", Color(float(pk["deep"][0]), float(pk["deep"][1]), float(pk["deep"][2])))
			s4.set_shader_parameter("hloubka_vrcholu", tek < 0.5)
			vodni.append(s4)
			m = s4
		"malba":
			var s5 := ShaderMaterial.new()
			s5.shader = load("res://shaders/malba.gdshader")
			s5.set_shader_parameter("zaklad", _v3(d["zaklad"]))
			s5.set_shader_parameter("barva", _v3(d["barva"]))
			s5.set_shader_parameter("sum", sum)
			m = s5
		"sklo":
			var s6 := ShaderMaterial.new()
			s6.shader = load("res://shaders/sklo.gdshader")
			s6.set_shader_parameter("terce", bool(d.get("terce", false)))
			m = s6
		"trava":
			var g := StandardMaterial3D.new()
			g.albedo_color = Color(_v3(d["col"]).x, _v3(d["col"]).y, _v3(d["col"]).z)
			g.vertex_color_use_as_albedo = false
			g.cull_mode = BaseMaterial3D.CULL_DISABLED
			g.roughness = 0.75
			g.backlight_enabled = true
			g.backlight = Color(0.25, 0.3, 0.1)
			m = g
		"voda":
			# prikop: stejna hladina jako rybnik (posouvane vlnky) a kruhove vlnky z life.gd
			var w := ShaderMaterial.new()
			w.shader = load("res://shaders/voda.gdshader")
			w.set_shader_parameter("nmap", load("res://obrazky/voda_normaly.png"))
			w.set_shader_parameter("sum", sum)
			# zelenohneda (radce 16:40 bod 2: 0,10/0,14/0,10), zakal svetlejsi u brehu
			w.set_shader_parameter("deep", Color(0.08, 0.115, 0.08))
			w.set_shader_parameter("zakal", Color(0.13, 0.16, 0.11))
			w.set_shader_parameter("kalnost", 0.82)
			w.set_shader_parameter("hloubka_vrcholu", true)
			vodni.append(w)
			water_mat = w
			m = w
		_:
			var sm := StandardMaterial3D.new()
			var c: Array = d.get("col", [0.5, 0.48, 0.45])
			sm.albedo_color = Color(c[0], c[1], c[2])
			sm.roughness = float(d.get("rough", 0.8))
			sm.metallic = float(d.get("metal", 0.0))
			if d.has("emit"):
				sm.emission_enabled = true
				sm.emission = Color(c[0], c[1], c[2])
				sm.emission_energy_multiplier = minf(float(d["emit"]), 4.0)
			m = sm
	_mats[base] = m
	return m


func _v3(a: Array) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func _apply_materials(mi: MeshInstance3D) -> void:
	var mesh := mi.mesh
	if mesh == null:
		return
	if mi.has_meta("hotovo"):
		return
	_dlazba_normaly(mi)
	mesh = mi.mesh
	for i in mesh.get_surface_count():
		if mi.has_meta("skryt_%d" % i):
			continue                                   # puvodni hladina male nadrze (nadrz.nova_hladina)
		var old := mesh.surface_get_material(i)
		var nm := old.resource_name if old else ""
		if nm != "":
			var mt := material(nm)
			mi.set_surface_override_material(i, mt)
			if vodni.has(mt):
				_hladina(mi, i)


## Radce 13:50 (Misa 0.74, nadvori (0,9)): kusy dlazby (material dlazba_kus) cerne - normaly vrcholu dolu/nahodne
## (export kusu) -> teren svetla nevidi. Kus dlazby je plochy kamen: normaly nahoru, tecny znovu.
func _dlazba_normaly(mi: MeshInstance3D) -> void:
	var am := mi.mesh as ArrayMesh
	if am == null:
		return
	var nalez := false
	for i in am.get_surface_count():
		var mt := am.surface_get_material(i)
		if mt and String(mt.resource_name).begins_with("dlazba_kus"):
			nalez = true
	if not nalez:
		return
	var nove := ArrayMesh.new()
	var n := 0
	for i in am.get_surface_count():
		var arr := am.surface_get_arrays(i)
		var mt := am.surface_get_material(i)
		if mt and String(mt.resource_name).begins_with("dlazba_kus"):
			var nr: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
			for j in nr.size():
				if nr[j].y < 0.5:
					nr[j] = Vector3.UP
					n += 1
			arr[Mesh.ARRAY_NORMAL] = nr
			arr[Mesh.ARRAY_TANGENT] = null
			var st := SurfaceTool.new()
			st.create_from_arrays(arr)
			if arr[Mesh.ARRAY_TEX_UV] != null:
				st.generate_tangents()
			arr = st.commit_to_arrays()
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(i, mt)
		nove.surface_set_name(i, am.surface_get_name(i))
	mi.mesh = nove
	print("dlazba: %d normal nahoru (%s)" % [n, mi.name])


## Hladina jako oblast (jen pro dotaz "je tu voda a v jake vysce"), ne kolize; male nadoby vynechat.
func _hladina(mi: MeshInstance3D, i: int) -> void:
	var arr := mi.mesh.surface_get_arrays(i)
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var bb := am.get_aabb()
	if maxf(bb.size.x, bb.size.z) < 3.0:
		return
	var ar := Area3D.new()
	ar.collision_layer = VRSTVA_VODA
	ar.collision_mask = 0
	ar.monitoring = false
	var cs := CollisionShape3D.new()
	cs.shape = am.create_trimesh_shape()
	ar.add_child(cs)
	mi.add_child(ar)


# ------------------------------------------------------------------ kolize

## Potok z Waterways (tools/reka_bake.gd): sit s hloubkou ve vrcholech, mapy proudeni a peny, shader pro Compatibility.
## Predpeceny potok (modely/reka) jen kdyz je upeceny z hladiny tohoto exportu (stejny reka_otisk v reka.json a
## svet.json); jinak hladina Reka_voda z exportu. Misa 28. 10.: stary balik z_reka (pred presunem Bystrice) schoval
## hladinu exportu a kreslil hladinu stare trasy - v novem korytu skoro zadna voda.
var _reka_voda_mesh: Mesh = null       # hladina Bystrice z exportu (Reka_voda)


func reka_predpecena() -> bool:
	if not FileAccess.file_exists("res://modely/reka/reka.res") or not FileAccess.file_exists("res://modely/reka/reka.json"):
		return false
	var meta: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://modely/reka/reka.json"))
	var ot := String(data.get("reka_otisk", ""))
	return meta is Dictionary and ot != "" and String((meta as Dictionary).get("reka_otisk", "")) == ot


func _reka(parent: Node3D) -> void:
	if not reka_predpecena():
		if FileAccess.file_exists("res://modely/reka/reka.res"):
			print("reka: predpeceny potok nesedi na export (reka_otisk) - hladina Reka_voda z exportu")
		return
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://modely/reka/reka.json"))
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/reka.gdshader")
	m.set_shader_parameter("normal_bump_texture", load("res://modely/reka/water1_normal_bump.png"))
	m.set_shader_parameter("i_texture_foam_noise", load("res://modely/reka/foam_noise.png"))
	m.set_shader_parameter("i_flowmap", load("res://modely/reka/reka_flow.png"))
	m.set_shader_parameter("i_distmap", load("res://modely/reka/reka_dist.png"))
	m.set_shader_parameter("i_valid_flowmap", true)
	m.set_shader_parameter("i_uv2_sides", int(meta["uv2_sides"]))
	m.set_shader_parameter("flow_speed", 0.3)
	m.set_shader_parameter("normal_scale", 0.6)
	m.set_shader_parameter("roughness", 0.15)
	m.set_shader_parameter("foam_amount", 1.2)
	m.set_shader_parameter("foam_color", Color(0.7, 0.72, 0.66, 0.6))
	# barvy v linearnim prostoru (source_color): melka hnedozelena, hluboka tmava; tablet bez HDR = tmavsi nez navrh
	m.set_shader_parameter("melka", Color(0.24, 0.27, 0.15))
	m.set_shader_parameter("hluboka", Color(0.06, 0.08, 0.05))
	m.set_shader_parameter("hloubka_barvy", 1.4)
	m.set_shader_parameter("cirost", 0.55)                # mela voda pruhledna: dno s oblazky a kameny videt
	var mi := MeshInstance3D.new()
	mi.name = "Potok"
	mi.mesh = load("res://modely/reka/reka.res")
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	reka_mat = m


## Koryto potoka (radce 04:55 bod 4): hladina z osy, teren pod ni vyhloubeny (scripts/koryto.gd) - site terenu
## i mrizka vysek louky (rostliny, trava), pred kolizemi. Stejne koryto pouziva tools/reka_bake.gd pro vodu.
var koryto: RefCounted
var reka_mat: ShaderMaterial         # potok: kameny v toku (kam[]) nastavuje kameny_toku_k()
var kameny_toku: Array = []          # [Vector4(x, z, polomer, uhel proudu)] - kameny ve vode (_krajina)


## 12 nejblizsich kamenu v toku k bodu q do shaderu potoka (cereni a pena kolem kamenu, 0.60 FRONTA voda).
func kameny_toku_k(q: Vector2) -> void:
	if reka_mat == null or kameny_toku.is_empty():
		return
	var kand: Array = []
	for v: Vector4 in kameny_toku:
		var d := Vector2(v.x, v.y).distance_squared_to(q)
		if d < 3600.0:
			kand.append([d, v])
	kand.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	var arr: Array = []
	for i in 12:
		arr.append(kand[i][1] if i < kand.size() else Vector4(0, 0, 0, 0))
	reka_mat.set_shader_parameter("kam", arr)
var nadrz: RefCounted
var _tvrz_root: Node3D
var _vys_sit := {}                    # okoli tvrze: vyska z vrcholu siti terenu (mrizka louky val a prikop nezna)


## Hladina prikopu pod padacim mostem (Misa 0.62: "pod mostem tvrze neni voda"): sit Prikop_voda z Blenderu ma
## pod mostem diru ~5 x 7 m (x -2,5..2,5, z 19..26) -> bez hladiny se tam ani nekopalo dno (nadrz kope jen pod
## hladinou) a pod mostem zustal suchy breh. Diru najit podel osy (od x 0 do stran) a zaplatit mrizkou 0,5 m.
func _prikop_zaplata(root: Node3D) -> void:
	var mi := root.find_child("Prikop_voda", true, false) as MeshInstance3D
	if mi == null or not (mi.mesh is ArrayMesh):
		return
	var am := mi.mesh as ArrayMesh
	var si := -1
	for i in am.get_surface_count():
		var mt := am.surface_get_material(i)
		if mt and String(mt.resource_name).begins_with("voda_prikop"):
			si = i
	if si < 0:
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var arr := am.surface_get_arrays(si)
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
	var tris: Array = []
	var y := 0.0
	for t in idx.size() / 3:
		var p0 := xf * v[idx[t * 3]]
		var p1 := xf * v[idx[t * 3 + 1]]
		var p2 := xf * v[idx[t * 3 + 2]]
		y = p0.y
		if maxf(maxf(p0.z, p1.z), p2.z) > 12.0 and minf(minf(p0.x, p1.x), p2.x) < 12.0 and maxf(maxf(p0.x, p1.x), p2.x) > -12.0:
			tris.append(PackedVector2Array([Vector2(p0.x, p0.z), Vector2(p1.x, p1.z), Vector2(p2.x, p2.z)]))
	var voda := func(x: float, z: float) -> bool:
		for tri: PackedVector2Array in tris:
			if Geometry2D.is_point_in_polygon(Vector2(x, z), tri):
				return true
		return false
	if voda.call(0.0, 22.5):
		return                                          # dira uz neni (novy export)
	var x0 := 0.0
	var x1 := 0.0
	while x0 > -8.0 and not voda.call(x0, 22.5):
		x0 -= 0.1
	while x1 < 8.0 and not voda.call(x1, 22.5):
		x1 += 0.1
	var z0 := 22.5
	var z1 := 22.5
	while z0 > 14.0 and (voda.call(x0 - 0.3, z0 - 0.1) or voda.call(x1 + 0.3, z0 - 0.1)):
		z0 -= 0.1
	while z1 < 32.0 and (voda.call(x0 - 0.3, z1 + 0.1) or voda.call(x1 + 0.3, z1 + 0.1)):
		z1 += 0.1
	# zaplata o kousek pres okraje (na sev bez mezery), UV jako zbytek site (u = x, v = 1 - z)
	x0 -= 0.05
	x1 += 0.05
	var inv := xf.affine_inverse()
	var nx := maxi(2, ceili((x1 - x0) / 0.5) + 1)
	var nz := maxi(2, ceili((z1 - z0) / 0.5) + 1)
	var col: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
	var uv: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV] if arr[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array()
	var nor: PackedVector3Array = arr[Mesh.ARRAY_NORMAL] if arr[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
	var tan: PackedFloat32Array = arr[Mesh.ARRAY_TANGENT] if arr[Mesh.ARRAY_TANGENT] != null else PackedFloat32Array()
	var b := v.size()
	for j in nz:
		for i in nx:
			var w := Vector3(lerpf(x0, x1, float(i) / (nx - 1)), y, lerpf(z0, z1, float(j) / (nz - 1)))
			v.append(inv * w)
			if not nor.is_empty():
				nor.append(Vector3.UP)
			if not tan.is_empty():
				tan.append_array(PackedFloat32Array([1.0, 0.0, 0.0, 1.0]))
			if not uv.is_empty():
				uv.append(Vector2(w.x, 1.0 - w.z))
			if not col.is_empty():
				col.append(col[0])
	# stejne natoceni jako zbytek site (shader voda cull_back): znamenko podle prvniho trojuhelniku
	var e1 := v[idx[1]] - v[idx[0]]
	var e2 := v[idx[2]] - v[idx[0]]
	var po := e1.z * e2.x - e1.x * e2.z > 0.0
	for j in nz - 1:
		for i in nx - 1:
			var a0 := b + j * nx + i
			if po:
				idx.append_array(PackedInt32Array([a0, a0 + nx + 1, a0 + 1, a0, a0 + nx, a0 + nx + 1]))
			else:
				idx.append_array(PackedInt32Array([a0, a0 + 1, a0 + nx + 1, a0, a0 + nx + 1, a0 + nx]))
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_INDEX] = idx
	if not nor.is_empty():
		arr[Mesh.ARRAY_NORMAL] = nor
	if not tan.is_empty():
		arr[Mesh.ARRAY_TANGENT] = tan
	if not uv.is_empty():
		arr[Mesh.ARRAY_TEX_UV] = uv
	if not col.is_empty():
		arr[Mesh.ARRAY_COLOR] = col
	var nove := ArrayMesh.new()
	for s in am.get_surface_count():
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr if s == si else am.surface_get_arrays(s))
		nove.surface_set_material(s, am.surface_get_material(s))
		nove.surface_set_name(s, am.surface_get_name(s))
	mi.mesh = nove
	print("prikop pod mostem: zaplata hladiny x %.1f..%.1f z %.1f..%.1f (%d vrcholu)" % [x0, x1, z0, z1, nx * nz])


## Terasa (radce 11:00): kolmy schod vyskove mapy (7-36 m na jedne rade mrizky, x 60-275, z 750-1365) -> svah 48-58 st.
## s nepravidelnym profilem, zaoblenou hranou a nabehem do suti. Polovina vysky se ubere nahore, polovina nasype dole:
## H' = (min_q(H_q + s d) + max_q(H_q - s d)) / 2 (kuzel ze dna a z temene, s = 2 tan uhlu). Upravi mrizku trava_kraj
## (rostliny, louka, _vyska) i vrcholy siti Teren* (kolize se stavi az potom). Puvodni hrany schodu -> _terasa_hrany.
const TERASA := Rect2(60.0, 750.0, 215.0, 615.0)
var _terasa_hrany: Array = []         # [Vector2 stred hrany, Vector2 smer ven (od steny), vyska temene, vyska paty]
var terasa_maska := PackedByteArray()  # uzly mrizky trava_kraj ve svahu terasy (stanoviste skalni_stena) - louka bez travy
var _terasa_g := Vector4()             # x0, z0, k, nx mrizky masky


## Stanoviste skalni_stena (svah upravene terasy, sklon nad ~40 st.): bez travy a trsu. Cte se i z vlaken louky.
func terasa_svah(x: float, z: float) -> bool:
	if terasa_maska.is_empty():
		return false
	var i := roundi((x - _terasa_g.x) / _terasa_g.z)
	var j := roundi((z - _terasa_g.y) / _terasa_g.z)
	var k := j * int(_terasa_g.w) + i
	return i >= 0 and j >= 0 and k < terasa_maska.size() and terasa_maska[k] != 0


func _terasa_terenu(root: Node3D) -> void:
	var t0 := Time.get_ticks_msec()
	var g: Dictionary = data["trava_kraj"]
	var ys := Marshalls.base64_to_raw(String(g["y"]))
	var nx := int(g["nx"])
	var nz := int(g["nz"])
	var kr := float(g["k"])
	var gx0 := float(g["x0"])
	var gz0 := float(g["z0"])
	var i0 := maxi(0, floori((TERASA.position.x - gx0) / kr))
	var i1 := mini(nx - 1, ceili((TERASA.end.x - gx0) / kr))
	var j0 := maxi(0, floori((TERASA.position.y - gz0) / kr))
	var j1 := mini(nz - 1, ceili((TERASA.end.y - gz0) / kr))
	var H := PackedFloat32Array()
	H.resize(nx * nz)
	for j in range(j0, j1 + 1):
		for i in range(i0, i1 + 1):
			H[j * nx + i] = ys.decode_s16((j * nx + i) * 2) / 100.0
	# hrany schodu a uzly do 8 bunek od nich
	const W := 8
	var blizko := {}
	for j in range(j0, j1):
		for i in range(i0, i1):
			for sm in 2:
				var a := H[j * nx + i]
				var b := H[(j + sm) * nx + i + 1 - sm]
				var dh := b - a
				if absf(dh) < 3.0 or absf(dh) / kr < 1.2:
					continue
				var dirv := Vector2(1 - sm, sm) * (-1.0 if dh > 0.0 else 1.0)
				var mid := Vector2(gx0 + i * kr, gz0 + j * kr) + Vector2(1 - sm, sm) * kr * 0.5
				_terasa_hrany.append([mid, dirv, maxf(a, b), minf(a, b)])
				for dj in range(-W, W + 1):
					for di in range(-W, W + 1):
						blizko[Vector2i(i + di, j + dj)] = true
	if _terasa_hrany.is_empty():
		return
	var fn := FastNoiseLite.new()
	fn.seed = 1108
	fn.frequency = 0.08                   # uhel svahu po 10-15 m
	var fn2 := FastNoiseLite.new()
	fn2.seed = 1109
	fn2.frequency = 0.3                   # nepravidelny profil 2-4 m
	var H2 := H.duplicate()
	for c: Vector2i in blizko:
		if c.x < i0 or c.y < j0 or c.x > i1 or c.y > j1:
			continue
		var x := gx0 + c.x * kr
		var z := gz0 + c.y * kr
		var sl := 2.0 * tan(deg_to_rad(53.0 + 5.0 * fn.get_noise_2d(x, z)))
		var hu := H[c.y * nx + c.x]
		var hd := hu
		for dj in range(-W, W + 1):
			var jj := c.y + dj
			if jj < j0 or jj > j1:
				continue
			for di in range(-W, W + 1):
				var ii := c.x + di
				if ii < i0 or ii > i1:
					continue
				var dq := sqrt(float(di * di + dj * dj)) * kr * sl
				var hq := H[jj * nx + ii]
				hu = minf(hu, hq + dq)
				hd = maxf(hd, hq - dq)
		H2[c.y * nx + c.x] = 0.5 * (hu + hd)
	# zaobleni hrany a paty (jeden pruchod 3x3 po zmenenych uzlech) a sum profilu jen ve svahu
	var H3 := H2.duplicate()
	var zmen := 0
	for c: Vector2i in blizko:
		if c.x <= i0 or c.y <= j0 or c.x >= i1 or c.y >= j1:
			continue
		var k0 := c.y * nx + c.x
		if absf(H2[k0] - H[k0]) < 0.05:
			continue
		var sm3 := 0.0
		for dj in range(-1, 2):
			for di in range(-1, 2):
				sm3 += H2[(c.y + dj) * nx + c.x + di]
		var zm := absf(H2[k0] - H[k0])
		H3[k0] = lerpf(H2[k0], sm3 / 9.0, 0.6) + fn2.get_noise_2d(gx0 + c.x * kr, gz0 + c.y * kr) * clampf(zm * 0.25, 0.0, 0.9)
		ys.encode_s16(k0 * 2, clampi(roundi(H3[k0] * 100.0), -32000, 32000))
		zmen += 1
	g["y"] = Marshalls.raw_to_base64(ys)
	_vys = {}
	# maska svahu: uzel, kde je po uprave sklon k sousedum nad tan 40 st.
	terasa_maska.resize(nx * nz)
	terasa_maska.fill(0)
	_terasa_g = Vector4(gx0, gz0, kr, nx)
	var ntm := 0
	for c: Vector2i in blizko:
		if c.x <= i0 or c.y <= j0 or c.x >= i1 or c.y >= j1:
			continue
		var k0 := c.y * nx + c.x
		var gr := maxf(maxf(absf(H3[k0 + 1] - H3[k0 - 1]), absf(H3[k0 + nx] - H3[k0 - nx])) / (2.0 * kr),
				maxf(absf(H3[k0] - H3[k0 - 1]), absf(H3[k0] - H3[k0 - nx])) / kr)
		if gr > 0.84:
			terasa_maska[k0] = 1
			ntm += 1
	# vrcholy siti terenu: posun o zmenu mrizky (bilinearne)
	var dlt := func(x: float, z: float) -> float:
		var fx := (x - gx0) / kr
		var fz := (z - gz0) / kr
		var i := floori(fx)
		var j := floori(fz)
		if i < i0 or j < j0 or i >= i1 or j >= j1:
			return 0.0
		fx -= i
		fz -= j
		var a := H3[j * nx + i] - H[j * nx + i]
		var b := H3[j * nx + i + 1] - H[j * nx + i + 1]
		var c2 := H3[(j + 1) * nx + i] - H[(j + 1) * nx + i]
		var d := H3[(j + 1) * nx + i + 1] - H[(j + 1) * nx + i + 1]
		return lerpf(lerpf(a, b, fx), lerpf(c2, d, fx), fz)
	var nv := 0
	for mi in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(mi.name)
		if nm == "Teren_obzor" or nm == "Teren_cesta_kamen":
			continue
		var am := (mi as MeshInstance3D).mesh as ArrayMesh
		if am == null:
			continue
		var xf := (mi as MeshInstance3D).global_transform
		var inv := xf.affine_inverse()
		var nove := ArrayMesh.new()
		var zm2 := 0
		var povrchy: Array = []
		for sf in am.get_surface_count():
			var arr := am.surface_get_arrays(sf)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var zs := 0
			for vi in v.size():
				var w := xf * v[vi]
				if not TERASA.has_point(Vector2(w.x, w.z)):
					continue
				var dd := dlt.call(w.x, w.z) as float
				if absf(dd) > 0.01:
					w.y += dd
					v[vi] = inv * w
					zs += 1
			if zs > 0:
				arr[Mesh.ARRAY_VERTEX] = v
				arr[Mesh.ARRAY_NORMAL] = null
				arr[Mesh.ARRAY_TANGENT] = null
				var st2 := SurfaceTool.new()
				st2.create_from_arrays(arr)
				st2.generate_normals()
				if arr[Mesh.ARRAY_TEX_UV] != null:
					st2.generate_tangents()
				arr = st2.commit_to_arrays()
			povrchy.append(arr)
			zm2 += zs
		if zm2 == 0:
			continue
		for sf in am.get_surface_count():
			nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, povrchy[sf])
			nove.surface_set_material(sf, am.surface_get_material(sf))
			nove.surface_set_name(sf, am.surface_get_name(sf))
		(mi as MeshInstance3D).mesh = nove
		nv += zm2
	print("terasa: %d hran schodu -> svah, %d uzlu mrizky (svah %d), %d vrcholu terenu, %d ms" % [_terasa_hrany.size(), zmen, ntm, nv, Time.get_ticks_msec() - t0])


## Misa 0.76 "u tvrze milion cesticek": stare cesticky zapecene v barve vrcholu terenu z Blenderu (pred branou)
## -> louka (COLOR.g). Driv to delal obdelnik v zem.gdshader, ten ale zazelenal i hlavni cestu (sit Teren_cesta).
const CESTICKY_PRYC := Rect2(-90.0, 24.0, 170.0, 126.0)


func _stare_cesticky(root: Node3D) -> void:
	var nv := 0
	for mi in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(mi.name)
		if nm.begins_with("Teren_cesta") or nm == "Teren_obzor":
			continue
		var am := (mi as MeshInstance3D).mesh as ArrayMesh
		if am == null:
			continue
		var xf := (mi as MeshInstance3D).global_transform
		var ab := xf * am.get_aabb()
		if not Rect2(ab.position.x, ab.position.z, ab.size.x, ab.size.z).intersects(CESTICKY_PRYC):
			continue
		var povrchy: Array = []
		var zm := 0
		for sf in am.get_surface_count():
			var arr := am.surface_get_arrays(sf)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			if arr[Mesh.ARRAY_COLOR] != null:
				var c: PackedColorArray = arr[Mesh.ARRAY_COLOR]
				for vi in v.size():
					var w := xf * v[vi]
					# okraj 4 m plynule
					var o := minf(minf(w.x - CESTICKY_PRYC.position.x, CESTICKY_PRYC.end.x - w.x),
							minf(w.z - CESTICKY_PRYC.position.y, CESTICKY_PRYC.end.y - w.z))
					if o <= 0.0 or c[vi].g >= 0.85:
						continue
					c[vi].g = lerpf(c[vi].g, 0.85, smoothstep(0.0, 4.0, o))
					zm += 1
				arr[Mesh.ARRAY_COLOR] = c
			povrchy.append(arr)
		if zm == 0:
			continue
		var nove := ArrayMesh.new()
		for sf in am.get_surface_count():
			nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, povrchy[sf])
			nove.surface_set_material(sf, am.surface_get_material(sf))
			nove.surface_set_name(sf, am.surface_get_name(sf))
		(mi as MeshInstance3D).mesh = nove
		nv += zm
	print("stare cesticky: %d vrcholu -> louka" % nv)


## Dno malych toku (Misa 28. 10. „takove dno a kameny okolo by mely mit i potoky a strouhy k mlynu“): jemny teren
## u toku (Teren_toky z exportu, kraj._teren_u_vody) dostane COLOR.a < 0,5 = oblazky jako dno Bystrice (koryto.gd)
## do pasma voda dno_toku_m od kraje vody (pod hladinou a holy breh s oblazky).
func _dno_toku(root: Node3D) -> void:
	var mi := root.find_child("Teren_toky", true, false) as MeshInstance3D
	if mi == null or mi.mesh == null:
		return
	var sir := float(pasma()["voda"]["dno_toku_m"])
	var xf := mi.global_transform
	var am := mi.mesh as ArrayMesh
	var nove := ArrayMesh.new()
	var n := 0
	for si in am.get_surface_count():
		var arr := am.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var col: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
		if col.is_empty():
			col.resize(v.size())
			col.fill(Color(0, 0.85, 0, 1))
		for i in v.size():
			var w := xf * v[i]
			var d := _od_toku(w.x, w.z)
			if d < sir:
				col[i].a = minf(col[i].a, 0.5 - 0.5 * clampf(1.0 - maxf(d, 0.0) / sir, 0.0, 1.0))
				n += 1
		arr[Mesh.ARRAY_COLOR] = col
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(si, am.surface_get_material(si))
	mi.mesh = nove
	print("dno malych toku: %d vrcholu s oblazky" % n)


## Vzdalenost od kraje vody maleho toku (bez rybniku; < 0 ve vode).
func _od_toku(x: float, z: float) -> float:
	od_vody(x, z)                                   # postavi mrizku toku
	var q := Vector2(x, z)
	var d := INF
	for e: Array in _voda_mriz.get(Vector2i(floori(x / 16.0), floori(z / 16.0)), []):
		d = minf(d, q.distance_to(Geometry2D.get_closest_point_to_segment(q, e[0], e[1])) - float(e[2]))
	return d


func _koryto_terenu(root: Node3D) -> void:
	_tvrz_root = root
	_terasa_terenu(root)
	_krok_cas("koryto: _terasa_terenu")
	_stare_cesticky(root)
	_krok_cas("koryto: _stare_cesticky")
	_prikop_zaplata(root)
	_krok_cas("koryto: _prikop_zaplata")
	_dno_toku(root)
	_krok_cas("koryto: _dno_toku")
	# rybnik a prikop (radce 04:55 bod 5): hladiny se stojatou vodou vetsi nez 5 m
	var hl: Array = []
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var me := (mi as MeshInstance3D).mesh
		if me == null:
			continue
		for i in me.get_surface_count():
			var mt := me.surface_get_material(i)
			var mn := String(mt.resource_name).split(".")[0] if mt else ""
			if mn == "voda_prikop" or mn == "voda":
				var bb := AABB()
				var vv: PackedVector3Array = me.surface_get_arrays(i)[Mesh.ARRAY_VERTEX]
				for q in vv:
					bb = bb.expand(q)
				if bb.size.x > 5.0 and bb.size.z > 5.0:
					hl.append([mi, i])
	var nd: RefCounted = preload("res://scripts/nadrz.gd").new()
	nd.priprav(hl)
	nadrz = nd
	if RYBNIK_DIL:
		# Misa 24. 10. (rybnik_lhota v3, NAVOD.md bod 1; blender/rybnik_dil.py): navesni rybnicek z vesnice.py pryc - hladina skryta, nadrz
		# (oval, vyhloubeni, bahno) vyrazena; misto nej dil z modely/rybnik (_rybnik_dil)
		for k3 in range(hl.size() - 1, -1, -1):
			if (nd.nadrze[k3]["kruh"] as Array).is_empty():
				continue
			var skr := StandardMaterial3D.new()
			skr.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			skr.albedo_color = Color(0, 0, 0, 0)
			skr.resource_name = "skryta_hladina"
			(hl[k3][0] as MeshInstance3D).set_surface_override_material(hl[k3][1], skr)
			(hl[k3][0] as MeshInstance3D).set_meta("skryt_%d" % int(hl[k3][1]), true)
			hl.remove_at(k3)
			nd.nadrze.remove_at(k3)
	for k2 in hl.size():
		var h: Array = hl[k2]
		var nd2: Dictionary = nd.nadrze[k2]
		if not (nd2["kruh"] as Array).is_empty():
			# vlastni hladina prirozeneho tvaru; puvodni ctvercova plocha z Blenderu pryc (pruhledny material)
			var mi0 := h[0] as MeshInstance3D
			var vm: Material = mi0.mesh.surface_get_material(h[1])
			var vmat: Material = material(String(vm.resource_name).split(".")[0]) if vm else null
			var nova: MeshInstance3D = nd.nova_hladina(nd2, vmat if vmat else vm)
			nova.set_meta("hotovo", true)
			root.add_child(nova)
			_hladina(nova, 0)
			var skryj := StandardMaterial3D.new()
			skryj.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			skryj.albedo_color = Color(0, 0, 0, 0)
			skryj.resource_name = "skryta_hladina"
			mi0.set_surface_override_material(h[1], skryj)
			mi0.set_meta("skryt_%d" % int(h[1]), true)
			print("nadrz: prirozena hladina (oval z vesnice.py) u %s" % str(nd2["kruh"][0]))
			continue
		nd.hloubka_hladiny(h[0], h[1])
	var k: RefCounted = preload("res://scripts/koryto.gd").new()
	var ma_koryto: bool = k.priprav(_vyska)
	if ma_koryto:
		koryto = k
	var n := 0
	var nn := 0
	if ma_koryto:
		for mi in root.find_children("Teren*", "MeshInstance3D", true, false):
			if String(mi.name) == "Teren_reka" or String(mi.name) == "Teren_most":
				k.pokryj(mi as MeshInstance3D)
	for mi in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(mi.name)
		if nm == "Teren_obzor" or nm == "Teren_cesta_kamen":
			continue
		if ma_koryto:
			n += k.vyhloub(mi as MeshInstance3D)
		nn += nd.vyhloub(mi as MeshInstance3D)
	_krok_cas("koryto: potok a nadrze")
	_najezdy_mostu(root)
	_krok_cas("koryto: _najezdy_mostu")
	_teren_pod_vraty(root)
	_krok_cas("koryto: _teren_pod_vraty")
	_upravy_terenu(root)
	_krok_cas("koryto: _upravy_terenu")
	_cesty_tvar(root)
	_krok_cas("koryto: _cesty_tvar")
	# koryta malych toku az po vsech upravach terenu ve hre (posun vsi, ulice, cesty, domy) - jinak hladina lezela
	# nad travou a suche koryto vedle (Misa 0.98); pravidla zasazeni: voda po stavbach, pozdejsi krok nehybe drivejsim
	_koryta_naposled(root)
	_krok_cas("koryto: _koryta_naposled")
	# mrizka vysek (2 m) pro rostliny a louku
	var g: Dictionary = data["trava_kraj"]
	var ys := Marshalls.base64_to_raw(String(g["y"]))
	var nx := int(g["nx"])
	var nz := int(g["nz"])
	var m := 0
	for j in nz:
		for i in nx:
			var x := float(g["x0"]) + i * float(g["k"])
			var z := float(g["z0"]) + j * float(g["k"])
			var st: float = minf(k.strop(x, z) if ma_koryto else INF, nd.strop(x, z))
			var y0 := ys.decode_s16((j * nx + i) * 2) / 100.0
			var y1 := minf(st, y0)
			if ma_koryto:
				y1 = maxf(y1, k.podlaha(x, z))
			y1 = maxf(y1, nd.podlaha(x, z))
			y1 = najezd_y(x, z, y1)
			y1 = dum_teren(x, z, uprava_y(x, z, y1))
			y1 = koryto_toku_y(x, z, ryb_mrizka(x, z, y1))
			if absf(y1 - y0) > 0.005:
				ys.encode_s16((j * nx + i) * 2, clampi(roundi(y1 * 100.0), -32000, 32000))
				m += 1
	g["y"] = Marshalls.raw_to_base64(ys)
	# mrizka vsi (trava_ves, jemnejsi) pod dilem rybnika Lhota: povrch dilu - jinak trsy pod dilem (holy ctverec)
	var gv: Dictionary = data.get("trava_ves", {})
	if not gv.is_empty():
		var yv := Marshalls.base64_to_raw(String(gv["y"]))
		var mv := 0
		for j in int(gv.get("nz", gv.get("n", 0))):
			for i in int(gv.get("nx", gv.get("n", 0))):
				var x := float(gv["x0"]) + i * float(gv["k"])
				var z := float(gv["z0"]) + j * float(gv["k"])
				var y0 := yv.decode_s16((j * int(gv.get("nx", gv.get("n", 0))) + i) * 2) / 100.0
				var y1 := koryto_toku_y(x, z, ryb_mrizka(x, z, dum_teren(x, z, y0)))
				if absf(y1 - y0) > 0.005:
					yv.encode_s16((j * int(gv.get("nx", gv.get("n", 0))) + i) * 2, clampi(roundi(y1 * 100.0), -32000, 32000))
					mv += 1
		gv["y"] = Marshalls.raw_to_base64(yv)
		print("rybnik: mrizka vsi %d bodu" % mv)
	_vys = {}
	print("koryto potoka: %d vrcholu terenu, rybnik a prikop %d (%d hladin), %d bodu mrizky" % [n, nn, hl.size(), m])


## Tvar koryta a doliny maleho toku (stejne jako blender/kraj.py voda_tvar, cisla z voda.json toky a toky_tvar):
## dno = hladina - hloubka, breh do sirka/2 + breh_sirka_m vysky hloubka + breh_m, dal svah doliny. Tvrde minimum -
## opakovane pouziti nic neprohlubuje. Mrizka useku 8 m.
var _kor_mriz := {}


func koryto_toku_y(x: float, z: float, y: float) -> float:
	if _kor_mriz.is_empty():
		var tt: Dictionary = Pravidla.cti("voda", "toky_tvar")
		_kor_mriz[Vector2i(1 << 20, 0)] = []
		for tk: Dictionary in Pravidla.cti("voda", "toky"):
			var o: Array = tk["osa_xzy"]
			var pw := float(tk["sirka_m"]) * 0.5
			var pas := pw + float(tt["breh_sirka_m"]) + float(tt["dolina_m"]) + float(tt["dolina_nabeh_m"])
			for i in o.size() - 1:
				var e := [Vector2(float(o[i][0]), float(o[i][1])), Vector2(float(o[i + 1][0]), float(o[i + 1][1])),
						float(o[i][2]), float(o[i + 1][2]), pw, float(tk["hloubka_m"]), pas]
				for cx in range(floori((minf(e[0].x, e[1].x) - pas) / 8.0), floori((maxf(e[0].x, e[1].x) + pas) / 8.0) + 1):
					for cz in range(floori((minf(e[0].y, e[1].y) - pas) / 8.0), floori((maxf(e[0].y, e[1].y) + pas) / 8.0) + 1):
						var c := Vector2i(cx, cz)
						if not _kor_mriz.has(c):
							_kor_mriz[c] = []
						(_kor_mriz[c] as Array).append(e)
	var seg: Array = _kor_mriz.get(Vector2i(floori(x / 8.0), floori(z / 8.0)), [])
	if seg.is_empty():
		return y
	var tt2: Dictionary = Pravidla.cti("voda", "toky_tvar")
	var q := Vector2(x, z)
	var nasyp := -INF
	var v_korytu := false
	for k: String in ["rybnik_lhota", "rybnik_tvrz"]:
		var r: Dictionary = Pravidla.cti("voda", k)
		if q.distance_to(Vector2(float(r["stred"][0]), float(r["stred"][1]))) < float(r.get("polomer_m", r.get("voda_polomer_m", 0.0))) + float(tt2["breh_sirka_m"]) + 2.0:
			v_korytu = true                           # u nadrze nasyp ne (tok do ni vtece), jako kraj.voda_tvar
	for e: Array in seg:
		var c := Geometry2D.get_closest_point_to_segment(q, e[0], e[1])
		var d := c.distance_to(q)
		if d > float(e[6]):
			continue
		var f := clampf((e[0] as Vector2).distance_to(c) / maxf((e[0] as Vector2).distance_to(e[1]), 1e-4), 0.0, 1.0)
		var hl := lerpf(float(e[2]), float(e[3]), f)
		var pw := float(e[4])
		var bs := float(tt2["breh_sirka_m"])
		var hk := float(e[5])
		if _na_brodu_toku(q):
			hk = float(tt2["brod_hloubka_m"])          # zaznam prechodu (cesty.json druh brod): melke koryto, bez nasypu
			v_korytu = true
		var allow := (hk + float(tt2["breh_m"])) * smoothstep(pw, pw + bs, d) + float(tt2["svah"]) * maxf(0.0, d - pw - bs)
		# jako kraj.voda_tvar: dolina jen do dolina_m, pak plynule puvodni teren
		var kd := pw + bs + float(tt2["dolina_m"])
		var w_d := 1.0 - smoothstep(kd, kd + float(tt2["dolina_nabeh_m"]), d)
		y = minf(y, lerpf(y, hl - hk + allow, w_d))
		if d >= pw:
			# jako kraj.voda_tvar: breh ne nize nez hladina + breh_m, dal svah nasypu
			nasyp = maxf(nasyp, hl + float(tt2["breh_m"]) - float(tt2["nasyp_svah"]) * maxf(0.0, d - pw - bs))
		elif d < pw:
			v_korytu = true
	return y if v_korytu else maxf(y, nasyp)


var _brody_toku: Array = []


## Bod v zaznamu prechodu malého toku druhu brod (cesty.json prechody s tok mimo bystrice)?
func _na_brodu_toku(q: Vector2) -> bool:
	if _brody_toku.is_empty():
		_brody_toku.append(null)
		for pr: Dictionary in Pravidla.cti("cesty", "prechody"):
			if String(pr["druh"]) == "brod" and String(pr["tok"]) != "bystrice":
				_brody_toku.append([Vector2(float(pr["stred"][0]), float(pr["stred"][1])), float(pr["polomer_m"])])
	for b: Variant in _brody_toku:
		if b != null and q.distance_to((b as Array)[0]) < float((b as Array)[1]):
			return true
	return false


func _koryta_naposled(root: Node3D) -> void:
	var zmen := 0
	for t0 in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(t0.name)
		if nm == "Teren_obzor" or nm == "Teren_cesta_kamen" or nm.ends_with("_sukne"):
			continue
		var mi := t0 as MeshInstance3D
		var am := mi.mesh as ArrayMesh
		if am == null:
			continue
		var xf := mi.global_transform
		var inv := xf.affine_inverse()
		# nejdriv zjistit, jestli se sit meni - jinak ji nechat (prestavba povrchu bez zmeny rozbila vlastni kanaly)
		var pole: Array = []
		var zde := 0
		for si in am.get_surface_count():
			var arr := am.surface_get_arrays(si)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			for i in v.size():
				var w := xf * v[i]
				var y2 := koryto_toku_y(w.x, w.z, w.y)
				if absf(y2 - w.y) > 0.005:
					w.y = y2
					v[i] = inv * w
					zde += 1
			arr[Mesh.ARRAY_VERTEX] = v
			pole.append(arr)
		if zde == 0:
			continue
		# vlastni kanaly (teren pod cestami CUSTOM0/1, _cesta_format) zustanou; normaly prepocitat z ploch
		# (SurfaceTool vlastni kanaly zahodi -> „Invalid array format“, teren vsi zmizel, 28. 10.)
		var nove := ArrayMesh.new()
		for si in am.get_surface_count():
			var arr: Array = pole[si]
			_normaly_z_ploch(arr)
			arr[Mesh.ARRAY_TANGENT] = null
			nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr, [], {}, _cesta_format(arr))
			nove.surface_set_material(si, am.surface_get_material(si))
			nove.surface_set_name(si, am.surface_get_name(si))
		mi.mesh = nove
		zmen += zde
	_vys = {}
	print("koryta toku naposled: %d vrcholu terenu" % zmen)


## Radce 17:05 bod 6 (Misa 0.70 "vratka ve vzduchu"): branky a vrata ve vsi visely 0,1-0,74 m nad terenem
## (Teren_ves po vyhloubeni a mrizce 2 m nize nez _land v Blenderu). Teren pod kridlem a kuly zvednout ke spodku
## kridla - 3 cm (do 1,2 m od stredu plne, do 3 m plynule).
func _teren_pod_vraty(root: Node3D) -> void:
	var body: Array = []
	var tv := PackedVector3Array()                  # vrcholy Teren_ves ve svete (vyska pod kridly)
	# okno = vsechna vrata a branky po posunu vsi (driv pevne x 400-560, z 760-900 = stara ves; Misa 0.98)
	var okno := AABB()
	var prvni := true
	for nd0 in root.find_children("Pohyb_ves_*", "MeshInstance3D", true, false):
		if String(nd0.name).contains("branka") or String(nd0.name).contains("vrata"):
			var b0 := (nd0 as MeshInstance3D).global_transform * (nd0 as MeshInstance3D).get_aabb()
			okno = b0 if prvni else okno.merge(b0)
			prvni = false
	okno = okno.grow(4.0)
	for t0 in root.find_children("Teren_ves*", "MeshInstance3D", true, false):
		var m0 := t0 as MeshInstance3D
		if m0.mesh == null:
			continue
		var x0 := m0.global_transform
		for si in m0.mesh.get_surface_count():
			for vv: Vector3 in m0.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
				var w := x0 * vv
				if not prvni and w.x > okno.position.x and w.x < okno.end.x and w.z > okno.position.z and w.z < okno.end.z:
					tv.append(w)
	for nd in root.find_children("Pohyb_ves_*", "MeshInstance3D", true, false):
		var nm := String(nd.name)
		if not (nm.contains("branka") or nm.contains("vrata")):
			continue
		var mi := nd as MeshInstance3D
		_prkna_tram(mi)
		var bb := mi.global_transform * mi.get_aabb()
		# Misa 0.72 "branka strasne, zrus i kopecek": teren se pod kridlem uz nezveda - kridlo se spusti na teren
		# (nejvyssi bod terenu pod kridlem, at nikde nevisi vys nez 2 cm); kul a plot zustavaji
		# vyska ze site Teren_ves (mrizka 2 m _vyska se lisi az o 0,5 m): nejnizsi vrchol pod kridlem; vyssi teren
		# pod kridlem se nize srovna (zarez pro otevreni), nikdy nezvedne
		var c2 := Vector2(bb.get_center().x, bb.get_center().z)
		var r2 := maxf(bb.size.x, bb.size.z) * 0.5 + 0.6
		# vyska vrat = median terenu pod kridlem (Misa 0.98 „vrata v jame“: nejnizsi vrchol okoli po posunu vsi na
		# svahu srazil cele okoli do jamy)
		var pod: Array = []
		for vv: Vector3 in tv:
			if Vector2(vv.x, vv.z).distance_to(c2) < r2:
				pod.append(vv.y)
		var ymin := _vyska(c2.x, c2.y)
		if not pod.is_empty():
			pod.sort()
			ymin = float(pod[pod.size() / 2])
		if bb.position.y > ymin + 0.02:
			var dy := bb.position.y - ymin - 0.02
			mi.global_position.y -= dy
			bb.position.y -= dy
		body.append([Vector2(bb.get_center().x, bb.get_center().z), bb.position.y - 0.03, maxf(bb.size.x, bb.size.z) * 0.5])
	if body.is_empty():
		return
	var zmen := 0
	for t in root.find_children("Teren_ves*", "MeshInstance3D", true, false):
		var mi2 := t as MeshInstance3D
		var am := mi2.mesh as ArrayMesh
		if am == null:
			continue
		var xf := mi2.global_transform
		var inv := xf.affine_inverse()
		var nove := ArrayMesh.new()
		for si in am.get_surface_count():
			var arr := am.surface_get_arrays(si)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			for i in v.size():
				var w := xf * v[i]
				for b: Array in body:
					var d := Vector2(w.x, w.z).distance_to(b[0]) - float(b[2])
					if d < 1.3 and w.y > float(b[1]) + 0.05:
						# kridlo by se otevrelo do zeme: teren pod nim na spodek kridla, do 1,3 m plynule (ne schod)
						w.y = lerpf(float(b[1]), w.y, smoothstep(0.0, 1.3, d))
						v[i] = inv * w
						zmen += 1
			arr[Mesh.ARRAY_VERTEX] = v
			arr[Mesh.ARRAY_NORMAL] = null
			arr[Mesh.ARRAY_TANGENT] = null
			var st := SurfaceTool.new()
			st.create_from_arrays(arr)
			st.generate_normals()
			if arr[Mesh.ARRAY_TEX_UV] != null:
				st.generate_tangents()
			nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, st.commit_to_arrays())
			nove.surface_set_material(si, am.surface_get_material(si))
			nove.surface_set_name(si, am.surface_get_name(si))
		mi2.mesh = nove
	print("teren pod vraty: %d vrcholu (%d kridel)" % [zmen, body.size()])
	# mrizka vysek (louka, rostliny) se zvedne taky
	_vratka_body = body
	_zahrady_tab(root)


var _vratka_body: Array = []


## Zahradky ve vsi (Vesnice_zahrady z Blenderu: zahony, zeli): bunky 1 m pod siti - louka tam netrsuje (Misa 0.72).
var _zahrady := {}


func _zahrady_tab(root: Node3D) -> void:
	for nd in root.find_children("*_zahrady*", "MeshInstance3D", true, false):
		var mi := nd as MeshInstance3D
		if mi.mesh == null:
			continue
		var xf := mi.global_transform
		var f := mi.mesh.get_faces()
		for i in range(0, f.size(), 3):
			var a := xf * f[i]
			var b := xf * f[i + 1]
			var c := xf * f[i + 2]
			var lo := Vector2(minf(a.x, minf(b.x, c.x)), minf(a.z, minf(b.z, c.z)))
			var hi := Vector2(maxf(a.x, maxf(b.x, c.x)), maxf(a.z, maxf(b.z, c.z)))
			if (hi - lo).length() > 12.0:
				continue
			for x in range(floori(lo.x), floori(hi.x) + 1):
				for z in range(floori(lo.y), floori(hi.y) + 1):
					_zahrady[Vector2i(x, z)] = true
	print("zahradky: %d m2" % _zahrady.size())


func v_zahrade(x: float, z: float) -> bool:
	if not _zahrady.has(Vector2i(floori(x), floori(z))):
		return false
	# stara zahradka vyriznuta (nove domy maji vlastni zahony) - bunka zustala bez travy = zeleny rastr (Misa 0.84)
	return _domy.is_empty() or not _v_stare_zahrade(x, z)


## Nove zahrady (_zahrada): 2 = pod zahonem (bez travy), 1 = mezi zahony (nizka seslapana trava jako nadvori),
## 0 = jinde. Jen cteni (louka ve vlaknech).
var _nove_zahrady: Array = []        # [inv Transform3D domu, stred Vector2, x0, x1, z0, z1, zahony [Vector2 mistne]]


func v_nove_zahrade(x: float, z: float) -> int:
	for g: Array in _nove_zahrady:
		if (g[1] as Vector2).distance_squared_to(Vector2(x, z)) > 400.0:
			continue
		var q: Vector3 = (g[0] as Transform3D) * Vector3(x, 0.0, z)
		if q.x < float(g[2]) or q.x > float(g[3]) or q.z < float(g[4]) or q.z > float(g[5]):
			continue
		for b: Vector2 in g[6]:
			if absf(q.x - b.x) < 0.68 and absf(q.z - b.y) < 1.62:
				return 2
		return 1
	return 0


## Diry v terenu podel potoka (test prochod 0.56: u mostu pas 7 x 12 m bez site i kolize - jemna sit mostu konci,
## sousedni maji vyrez): mrizka 1 m v pasu koryta, kde paprsek shora nic netrefi, se zalepi ctverci z vysek mrizky
## (po vyhloubeni). Sit Teren_zaplata dostane material zeme a kolizi jako ostatni teren.
func _zaplaty(root: Node3D) -> void:
	if koryto == null:
		return
	var space := root.get_world_3d().direct_space_state
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hotovo := {}
	var n := 0
	var kr = koryto
	for k in kr.body.size() - 1:
		var a: Vector2 = kr.body[k]
		var b: Vector2 = kr.body[k + 1]
		var dl := a.distance_to(b)
		var nrm := (b - a).normalized().orthogonal()
		for m in int(dl) + 1:
			for o in range(-22, 23):
				var q := a.lerp(b, m / maxf(dl, 0.01)) + nrm * o
				var c := Vector2i(floori(q.x), floori(q.y))
				if hotovo.has(c):
					continue
				hotovo[c] = true
				var x := c.x + 0.5
				var z := c.y + 0.5
				# dira = nic pod paprskem, nebo jen hruba sit zapustena 2,5 m pod jemnou tam, kde jemna konci
				# (test prochod: breh za koncem Teren_most, hrac 2 m pod terenem u steny mostu)
				var dira := false
				for sx: float in [-0.25, 0.25]:
					for sz: float in [-0.25, 0.25]:
						var hh := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x + sx, 300, z + sz), Vector3(x + sx, -200, z + sz)))
						# v korytu proti dnu (strop koryta), ne proti mrizce: hruba sit 2,5 m pod dnem tam, kde jemna konci, byla
						# "dnem" a hladina nad ni visela jako trojuhelnik u brehu (Misa 0.62, test hladina); zaplata ma material
						# zeme s UV a tecnami (sede desky 0.56b byly bez nich)
						dira = dira or hh.is_empty() or ((hh["position"] as Vector3).y < minf(_vyska(x + sx, z + sz), kr.strop(x + sx, z + sz)) - 0.8 \
								and not String((hh["collider"] as Node).name).begins_with("Teren_reka") \
								and not String((hh["collider"] as Node).name).begins_with("Teren_most"))
				if not dira:
					continue
				# bunka 1 m s rezervou 0,25 m (prekryv s okolnim terenem, zadna nova skvira)
				var p0 := Vector2(c.x - 0.25, c.y - 0.25)
				var p1 := Vector2(c.x + 1.25, c.y + 1.25)
				var v00 := Vector3(p0.x, minf(_vyska(p0.x, p0.y), kr.strop(p0.x, p0.y)) - 0.03, p0.y)
				var v10 := Vector3(p1.x, minf(_vyska(p1.x, p0.y), kr.strop(p1.x, p0.y)) - 0.03, p0.y)
				var v01 := Vector3(p0.x, minf(_vyska(p0.x, p1.y), kr.strop(p0.x, p1.y)) - 0.03, p1.y)
				var v11 := Vector3(p1.x, minf(_vyska(p1.x, p1.y), kr.strop(p1.x, p1.y)) - 0.03, p1.y)
				for v: Vector3 in [v00, v11, v10, v00, v01, v11]:
					st.set_color(Color(0, 0.85, 0, 1))
					st.set_uv(Vector2(v.x, v.z))
					st.add_vertex(v)
				n += 1
	if n == 0:
		return
	st.generate_normals()
	st.generate_tangents()                 # bez UV a tecen kreslil zem.gdshader zaplatu sede (normala z mapy = 0)
	var mi := MeshInstance3D.new()
	mi.name = "Teren_zaplata"
	mi.mesh = st.commit()
	mi.material_override = material("zem")
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mi)
	_trimesh(mi)
	print("zaplaty terenu u potoka: %d bunek 1 m" % n)


## Kuly mostu (Misa 0.62: "podpery konci ve vzduchu"): kuly z modelu stoji na puvodnim terenu, zarez potoka
## (koryto.gd) dno snizil o 1-2 m. Kazdy svisly kul (kus site kury vyssi nez 1 m a 2x vyssi nez siroky) se prodlouzi:
## spodni vrcholy na teren v miste kulu - 0,5 m (zapusteni), UV po delce se protahne umerne (kura se nenatahne).
func _most_kuly(mi: MeshInstance3D) -> void:
	var me := mi.mesh as ArrayMesh
	if me == null:
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var inv := xf.affine_inverse()
	var nove := ArrayMesh.new()
	var popis: Array = []
	for si in me.get_surface_count():
		var arr := me.surface_get_arrays(si)
		var mt := me.surface_get_material(si)
		if mt != null and String(mt.resource_name).begins_with("kura") and arr[Mesh.ARRAY_INDEX] != null:
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var uv = arr[Mesh.ARRAY_TEX_UV]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
			# kusy site: trojuhelniky + vrcholy ve stejne poloze (union-find)
			var par: Array = range(v.size())
			var poz := {}
			for k in v.size():
				var key := Vector3i(roundi(v[k].x * 1000.0), roundi(v[k].y * 1000.0), roundi(v[k].z * 1000.0))
				if poz.has(key):
					par[_koren(par, k)] = _koren(par, poz[key])
				else:
					poz[key] = k
			for t in idx.size() / 3:
				var a := _koren(par, idx[t * 3])
				par[_koren(par, idx[t * 3 + 1])] = a
				par[_koren(par, idx[t * 3 + 2])] = a
			var skup := {}
			for k in v.size():
				var r := _koren(par, k)
				if not skup.has(r):
					skup[r] = []
				(skup[r] as Array).append(k)
			for r: int in skup:
				var ks: Array = skup[r]
				var bb := AABB(xf * v[ks[0]], Vector3.ZERO)
				for k: int in ks:
					bb = bb.expand(xf * v[k])
				if bb.size.y < 0.5 or bb.size.y < 2.0 * maxf(bb.size.x, bb.size.z):
					continue
				var s := bb.get_center()
				var zem := INF
				for o: Vector2 in [Vector2.ZERO, Vector2(0.3, 0), Vector2(-0.3, 0), Vector2(0, 0.3), Vector2(0, -0.3)]:
					zem = minf(zem, _teren_y(s.x + o.x, s.z + o.y))
				var y0 := bb.position.y
				var y1 := bb.end.y
				var pata := zem - 0.5
				if pata > y0 - 0.05:
					continue
				for k: int in ks:
					var w := xf * v[k]
					if w.y > y0 + 0.02:
						continue
					if uv != null:
						# protejsi vrchol nahore (stejne misto v pudorysu): UV po delce v pomeru nove delky
						var hor := -1
						var hd := INF
						for k2: int in ks:
							var w2 := xf * v[k2]
							var dd := Vector2(w2.x - w.x, w2.z - w.z).length_squared()
							if w2.y > y1 - 0.02 and dd < hd:
								hd = dd
								hor = k2
						if hor >= 0:
							uv[k] = uv[hor] + (uv[k] - uv[hor]) * (y1 - pata) / maxf(y1 - y0, 0.01)
					v[k] = inv * Vector3(w.x, pata, w.z)
				popis.append("%.1f,%.1f pata %.2f -> %.2f (teren %.2f)" % [s.x, s.z, y0, pata, zem])
			arr[Mesh.ARRAY_VERTEX] = v
			if uv != null:
				arr[Mesh.ARRAY_TEX_UV] = uv
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(si, mt)
		nove.surface_set_name(si, me.surface_get_name(si))
	if popis.is_empty():
		return
	var ovr: Array = []
	for si in me.get_surface_count():
		ovr.append(mi.get_surface_override_material(si))
	mi.mesh = nove
	for si in ovr.size():
		mi.set_surface_override_material(si, ovr[si])
	print("most: %d kulu do zeme: %s" % [popis.size(), "; ".join(popis)])


func _koren(par: Array, a: int) -> int:
	while int(par[a]) != a:
		par[a] = par[par[a]]
		a = par[a]
	return a


## Teren po zarezu potoka a najezdech mostu (mrizka vysek, dno koryta, najezd).
func _teren_y(x: float, z: float) -> float:
	var y := _vyska(x, z)
	if koryto != null:
		y = maxf(minf(y, koryto.strop(x, z)), koryto.podlaha(x, z))
	return najezd_y(x, z, y)


## Kontrola hladiny potoka (Misa 0.62 bod 5: "trojuhelnik hladiny u brehu"): pod kazdym vrcholem hladiny musi byt dno
## do 1,5 m (paprsek na kolize terenu po zarezu, najezdech a zaplatach). Hloubka z peceni (COLOR.r * 4 m) odlisi tune
## (hluboko i pri peceni) od visici hladiny (pri peceni melko, ted pod ni dira nebo hruba sit). Vypis do logu.
## Hloubka ve vrcholech se zaroven prepocita na skutecne dno (Misa 0.62 bod 1: pod mostem pecene 0,2-0,4 m misto
## 0,6 m = pruhledna voda ve stinu mostu jako suche koryto); visici hladina dostane hloubku 0 (pruhledna, neni videt).
func _kontrola_hladiny(parent: Node3D) -> void:
	var pm := parent.get_node_or_null("Potok") as MeshInstance3D
	if pm == null or pm.mesh == null:
		return
	var t0 := Time.get_ticks_msec()
	var space := parent.get_world_3d().direct_space_state
	var arr := pm.mesh.surface_get_arrays(0)
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var col = arr[Mesh.ARRAY_COLOR]
	if col == null or (col as PackedColorArray).size() != v.size():
		return
	var cols: PackedColorArray = col
	var hot := {}                        # poloha -> nova hloubka (m), nebo -1 = ponechat pecenou
	var visi: Array = []
	var tune := 0
	var zmen := 0
	var bez_site := 0
	for i in v.size():
		var q := pm.global_transform * v[i]
		var key := Vector3i(roundi(q.x * 20.0), roundi(q.y * 20.0), roundi(q.z * 20.0))
		if not hot.has(key):
			var dep := -1.0
			var pec := cols[i].r * 4.0
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(q + Vector3(0, 3.0, 0), q - Vector3(0, 40.0, 0)))
			if h.is_empty():
				if koryto != null and not koryto.blizko(q.x, q.z).is_empty():
					bez_site += 1                       # konec toku za siti terenu (jen Teren_obzor bez kolize)
					dep = 0.0
			else:
				var hl := q.y - (h["position"] as Vector3).y
				if hl <= 1.5:
					dep = maxf(hl, 0.0)
				elif pec > 1.2:
					tune += 1
					dep = minf(hl, 4.0)
				else:
					visi.append("%.1f,%.1f %.1f m (%s)" % [q.x, q.z, hl, String((h["collider"] as Node).name).trim_suffix("_kolize")])
					dep = 0.0
			hot[key] = dep
		var d: float = hot[key]
		if d >= 0.0 and absf(d - cols[i].r * 4.0) > 0.03:
			cols[i].r = clampf(d, 0.0, 4.0) / 4.0
			zmen += 1
	if zmen > 0:
		arr[Mesh.ARRAY_COLOR] = cols
		var am := ArrayMesh.new()
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		pm.mesh = am
	print("hladina potoka: %d vrcholu, dno do 1,5 m chybi pod %d (visici hladina, skryta), mimo sit terenu %d, tune hloubeji %d, hloubka prepoctena u %d (%d ms) %s" % [
			hot.size(), visi.size(), bez_site, tune, zmen, Time.get_ticks_msec() - t0, str(visi.slice(0, 12)) if not visi.is_empty() else ""])


## Most pres potok (Misa 0.53: z dalky blika): mezi prkny mostovky jsou 1,5cm mezery, kterymi z dalky problikava
## svetla voda a teren (aliasing). Pod prkna tmava deska po celem pudorysu prken - mezery jsou pak tmave a stale.
func _most_podlozka(mi: MeshInstance3D) -> void:
	_prkna_tram(mi)
	_most_podlozka_deska(mi)


## Prkna z drevo_plot (fotka 13 vodorovnych desek na 1,8 m, s prohozenym UV napric = „ctverecky“): jedno prkno =
## fotka tramu podel. Most (0.62) a vrata a branky do dvoru (Misa 0.83 „vrata ze ctverecku jako kdysi most“).
func _prkna_tram(mi: MeshInstance3D) -> void:
	var me := mi.mesh
	for i in me.get_surface_count():
		var mt := me.surface_get_material(i)
		if mt == null or not String(mt.resource_name).begins_with("drevo_plot"):
			continue
		var pm := mi.get_surface_override_material(i)
		if pm == null:
			pm = material(String(mt.resource_name))
		if pm is ShaderMaterial:
			pm = pm.duplicate()
			pm.set_shader_parameter("tex_a", _t("tram", "diff"))
			pm.set_shader_parameter("tex_n", _t("tram", "nor"))
			pm.set_shader_parameter("tex_r", _t("tram", "rough"))
			pm.set_shader_parameter("velikost", 1.2)
			pm.set_shader_parameter("prohodit", true)
			mi.set_surface_override_material(i, pm)


func _most_podlozka_deska(mi: MeshInstance3D) -> void:
	var me := mi.mesh
	for i in me.get_surface_count():
		var mt := me.surface_get_material(i)
		if mt == null or not String(mt.resource_name).begins_with("drevo_plot"):
			continue
		# Misa 0.62: mostovka "ctverecky misto prken" - textura prken v _prkna_tram
		var v: PackedVector3Array = me.surface_get_arrays(i)[Mesh.ARRAY_VERTEX]
		var body := PackedVector2Array()
		var y0 := INF
		for q in v:
			body.append(Vector2(q.x, q.z))
			y0 = minf(y0, q.y)
		var hull := Geometry2D.convex_hull(body)
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		st.set_normal(Vector3.UP)
		for k in range(1, hull.size() - 2):
			for p: Vector2 in [hull[0], hull[k], hull[k + 1]]:
				st.add_vertex(Vector3(p.x, y0 + 0.005, p.y))
		var pod := MeshInstance3D.new()
		pod.name = "Most_podlozka"
		pod.mesh = st.commit()
		var sm := StandardMaterial3D.new()
		sm.albedo_color = Color(0.05, 0.04, 0.03)
		sm.cull_mode = BaseMaterial3D.CULL_DISABLED
		sm.roughness = 1.0
		pod.material_override = sm
		pod.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.add_child(pod)
		return


func _trimesh(mi: MeshInstance3D) -> void:
	if mi.has_meta("bez_kolize"):
		return
	var body := StaticBody3D.new()
	body.name = String(mi.name) + "_kolize"
	var cs := CollisionShape3D.new()
	var tri := (mi.get_meta("kolize_sit") as Mesh if mi.has_meta("kolize_sit") else mi.mesh).create_trimesh_shape()     # Teren_cesta: kolize na vysce cesty
	# oboustranne: modely ze SketchUpu maji cast ploch otocenych (podlaha hostince normalou dolu) - jednostranna
	# kolize hrace shora propustila na teren pod podlahou a zespodu ho drzela (zaseknuti ve dverich a na schodech)
	tri.backface_collision = true
	cs.shape = tri
	body.add_child(cs)
	mi.add_child(body)


## Sit skaly/balvanu pro kolizi a usazeni: skala z LOD1 (_daleko, ~800 troj.), balvan z modelu; jen povrch skaly.
func _skala_sit(key: String) -> Mesh:
	var kind := key.trim_suffix("_0")
	var path := "res://modely/rostliny/%s.glb" % (kind + "_daleko" if kind.begins_with("skala_") else kind)
	if not ResourceLoader.exists(path):
		path = "res://modely/rostliny/%s.glb" % kind
	var ps: PackedScene = load(path)
	if ps == null:
		return null
	var inst := ps.instantiate()
	var me: Mesh = null
	for m in inst.find_children("*", "MeshInstance3D", true, false):
		var mm := (m as MeshInstance3D).mesh
		if mm.get_surface_count() > 0:
			me = mm
			break
	inst.free()
	return me


## Plochy site skaly pro dosednuti rostlin (vsechny: nejvyssi prusecik svisle primky je skutecny povrch shora;
## filtr podle normaly bral i spodky previsu a strom skoncil pod rimsou).
func _horni_plochy(me: Mesh) -> PackedVector3Array:
	return me.get_faces()


## Rostliny nad skalou (export je posadil do vysky vrcholu podle obrysu, u uzke jehly ale vedle ni - visely ve
## vzduchu): svisly paprsek proti hornim plocham skaly; bez zasahu dolu na teren.
func _na_povrch_skal(site: Dictionary, mriz: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	var plochy := {}
	var dosedlo := 0
	var dolu := 0
	for key: String in r:
		if site.has(key) or key.begins_with("skala_"):
			continue
		for t: Array in r[key]:
			var q := Vector2(t[3], t[11])
			var y := float(t[7])
			var ter := _vyska(q.x, q.y)
			if y < ter + 1.5:
				continue
			var cc := Vector2i(floori(q.x / 16.0), floori(q.y / 16.0))
			var best := -INF
			var kandidat := false
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for pl: Array in mriz.get(cc + Vector2i(dx, dz), []):
						if q.distance_to(pl[0]) > float(pl[1]):
							continue
						kandidat = true
						var sk: String = pl[4]
						if not plochy.has(sk):
							plochy[sk] = _horni_plochy(site[sk])
						var tr: Array = r[sk][pl[5]]
						var xf := Transform3D(Basis(Vector3(tr[0], tr[4], tr[8]), Vector3(tr[1], tr[5], tr[9]), Vector3(tr[2], tr[6], tr[10])), Vector3(tr[3], tr[7], tr[11]))
						var inv := xf.affine_inverse()
						var o := inv * Vector3(q.x, y + 60.0, q.y)          # shora nad celou skalou (jinak start uvnitr)
						var d := (inv.basis * Vector3.DOWN).normalized()
						var pf: PackedVector3Array = plochy[sk]
						for i in range(0, pf.size(), 3):
							var h: Variant = Geometry3D.ray_intersects_triangle(o, d, pf[i], pf[i + 1], pf[i + 2])
							if h != null:
								best = maxf(best, (xf * (h as Vector3)).y)
			if not kandidat:
				continue
			if best > ter:
				t[7] = best - 0.1
				dosedlo += 1
			else:
				t[7] = ter - 0.05
				dolu += 1
	print("usazeni skal: na povrch skaly %d, bez skaly pod sebou na zem %d" % [dosedlo, dolu])
	_na_zem(site, mriz)
	_na_zem_arg = [site, mriz]


## Vsechny rostliny mimo skaly na teren (radce 11:20, D: teren -> upravy -> usazeni -> rozsev): export je
## rozmistil na teren pred upravami (koryto, srovnani u staveb), stromy pak visely 5-17 m nad zemi nebo byly
## zakopane. Tvrz a ves maji vlastni teren (nadvori, dvory) - tam se nesahá.
var _na_zem_arg: Array = []


func _na_zem(site: Dictionary, mriz: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	var n := 0
	for key: String in r:
		if site.has(key) or key.begins_with("skala_"):
			continue
		for t: Array in r[key]:
			var q := Vector2(t[3], t[11])
			# uvnitr hradeb tvrze (nadvori ma vlastni teren); ves a okoli tvrze dosednou na teren jako vse ostatni
			# (radce 13:20: bříza u vsi visela - vyjimka byla polomer, ne stavba)
			# okoli tvrze ma vlastni teren (val, prikop - mrizka louky ho nezna); kameny export dal na cesty a dlazbu,
			# ktere mrizka taky nezna (zakopal by je)
			# nadvori tvrze ma vlastni teren (Nadvori*), za hradbou val a prikop - vyska ze site terenu, ne z mrizky louky
			if absf(q.x + 4.5) < 24.0 and absf(q.y - 0.4) < 19.0:
				continue
			var ter := _vyska(q.x, q.y)
			if Vector2(q.x + 4.0, q.y).length() < 75.0:
				ter = _vyska_sit(q.x, q.y)
				if ter == INF:
					continue
			var y := float(t[7])
			# kameny z exportu lezi i na cestach a dlazbe, ktere mrizka nezna (zakopal by je) - dolu jen tam, kde teren
			# snizilo koryto (zarez potoka 0.55: visely 1-20 m nad svahem, hlaseni z hrani 0.55)
			if key.begins_with("kamen_") and Vector2(q.x - 470.0, q.y - 830.0).length() < 130.0:
				continue                                      # ves: kameny na dlazbe a cestach, ktere mrizka nezna
			if y < ter + 0.25 and y > ter - 1.0:
				continue
			# nad skalou (dosedlo na jeji povrch) nechat
			var na_skale := false
			var cc := Vector2i(floori(q.x / 16.0), floori(q.y / 16.0))
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for pl: Array in mriz.get(cc + Vector2i(dx, dz), []):
						if q.distance_to(pl[0]) <= float(pl[1]):
							na_skale = true
			if na_skale:
				continue
			if OS.has_environment("TVRZ_NA_ZEM"):
				var oblast := "tvrz" if Vector2(q.x + 4.0, q.y).length() < 80.0 else ("ves" if q.distance_to(Vector2(470.0, 830.0)) < 130.0 else "jinde")
				var kl := "%s %s %s" % [oblast, key.substr(0, 8), "nad" if y > ter else "pod"]
				_stat[kl] = int(_stat.get(kl, 0)) + 1
			t[7] = ter - 0.05
			n += 1
	print("rostliny na teren (visely nebo zakopane): ", n, " ", _stat)


## Usazeni skal a balvanu (radce 04:55): pata na nejnizsim bodu terenu pod obvodem paty (12 smeru), zapustit 0,4 m.
## Plati pro vsechny LOD (stejny index instance) a pro kvadrove kolize balvanu na stejnem miste.
func _usad_skaly(site: Dictionary) -> Dictionary:
	var r: Dictionary = data["rostliny"]
	var posun := {}                      # Vector2i(x*2, z*2) -> dy
	var n := 0
	var hloubky: Array[float] = []
	var plosiny: Array = []              # [stred xz, polomer, vyska nad patou, dy] - co stoji na skale, jde s ni dolu
	for key: String in site:
		var me: Mesh = site[key]
		var fa := me.get_faces()
		var dno := INF
		for v in fa:
			dno = minf(dno, v.y)
		# obvod paty: nejvzdalenejsi vrchol spodniho metru v kazdem z 12 smeru
		var obvod: Array[float] = []
		obvod.resize(12)
		obvod.fill(0.0)
		for v in fa:
			if v.y > dno + 1.0:
				continue
			var i := posmod(roundi(atan2(v.z, v.x) / TAU * 12.0), 12)
			obvod[i] = maxf(obvod[i], Vector2(v.x, v.z).length())
		var kind := key.trim_suffix("_0")
		var klice := [key]
		for k2: String in [kind + "_daleko_0", kind + "_daleko2_0"]:
			if r.has(k2) and (r[k2] as Array).size() == (r[key] as Array).size():
				klice.append(k2)
		for i in (r[key] as Array).size():
			var t: Array = r[key][i]
			var bs := Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10]))
			var o := Vector3(t[3], t[7], t[11])
			var low := _vyska(o.x, o.z)
			for j in 12:
				if obvod[j] <= 0.0:
					continue
				var a := float(j) / 12.0 * TAU
				var w := o + bs * (Vector3(cos(a), 0.0, sin(a)) * obvod[j] * 0.9)
				low = minf(low, _vyska(w.x, w.z))
			var y := low - 0.4 - (bs * Vector3(0, dno, 0)).y
			var dy := minf(y - o.y, 0.0)          # jen dolu; i neposunuta skala je plosina pro dosednuti rostlin
			# balvan nezakopat cely: nejvys 40 % vysky (vez stoji ve svahu, tam rozhoduje obvod)
			if key.begins_with("balvan_"):
				var vy := (bs * Vector3(0, me.get_aabb().size.y, 0)).y
				dy = maxf(dy, -0.4 * vy)
			if dy < 0.0:
				hloubky.append(-dy)
				n += 1
			for k2: String in klice:
				(r[k2][i] as Array)[7] = float(r[k2][i][7]) + dy
			posun[Vector2i(roundi(o.x * 2.0), roundi(o.z * 2.0))] = dy
			# cela skala (vrchol byva sirsi nez pata): co stoji nad ni, jde dolu s ni
			var ab := me.get_aabb()
			var rmax := maxf(maxf(absf(ab.position.x), absf(ab.end.x)), maxf(absf(ab.position.z), absf(ab.end.z)))
			plosiny.append([Vector2(o.x, o.z), rmax * bs.x.length() + 0.5, o.y + 1.0, dy, key, i])
	# rostliny na vrcholu a rimsach skal (borovice na vezi) posunout se skalou, jinak visi ve vzduchu
	var mriz := {}
	for pl: Array in plosiny:
		var cc := Vector2i(floori((pl[0] as Vector2).x / 16.0), floori((pl[0] as Vector2).y / 16.0))
		if not mriz.has(cc):
			mriz[cc] = []
		mriz[cc].append(pl)
	var nahore := 0
	for key: String in r:
		if site.has(key) or key.begins_with("skala_"):
			continue
		for t: Array in r[key]:
			var q := Vector2(t[3], t[11])
			var cc := Vector2i(floori(q.x / 16.0), floori(q.y / 16.0))
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for pl: Array in mriz.get(cc + Vector2i(dx, dz), []):
						# na skale = nad patou skaly i nad terenem (ve svahu u paty roste na zemi)
						if float(t[7]) > float(pl[2]) and q.distance_to(pl[0]) < float(pl[1]) and float(t[7]) > _vyska(q.x, q.y) + 0.5:
							t[7] = float(t[7]) + float(pl[3])
							nahore += 1
	print("usazeni skal: s nimi posunuto %d rostlin a kamenu" % nahore)
	_na_povrch_skal(site, mriz)
	hloubky.sort()
	if n > 0:
		print("usazeni skal: %d zapusteno, median %.2f m, 90 %% %.2f m, max %.2f m" % [n, hloubky[n / 2], hloubky[n * 9 / 10], hloubky[n - 1]])
	return posun


func _collisions(parent: Node3D) -> void:
	var body := StaticBody3D.new()
	body.name = "Kolize"
	parent.add_child(body)
	_kolize_body = body
	# skaly a balvany: trimesh z LOD1 (radce 04:55) - konvexni obal premostil prurvy mezi vezemi (neviditelne steny)
	var site := {}
	for key: String in data["rostliny"]:
		if (key.begins_with("skala_") or key.begins_with("balvan_")) and not key.contains("_daleko") and key.ends_with("_0"):
			var me := _skala_sit(key)
			if me:
				site[key] = me
	_usad_skaly(site)
	var veze := {}
	var troj := 0
	for key: String in site:
		# radce 09:20 bod 1 (tablet u potoka (-35,27): fyzika 150 ms): balvan mel kolizi z cele site (4 000 troj.
		# trimesh, 4 pres sebe v korytu) -> konvexni obal (balvan je obly); skaly (veze, previsy) zustavaji trimesh z LOD1
		var tvar: Shape3D = (site[key] as Mesh).create_convex_shape(true, true) if key.begins_with("balvan_") \
				else (site[key] as Mesh).create_trimesh_shape()
		troj += 0 if key.begins_with("balvan_") else (site[key] as Mesh).get_faces().size() / 3
		var bb := (site[key] as Mesh).get_aabb()
		for t: Array in data["rostliny"][key]:
			veze[Vector2i(roundi(float(t[3]) * 2.0), roundi(float(t[11]) * 2.0))] = true
			kolize(tvar, bb, Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])), Vector3(t[3], t[7], t[11])))
	print("kolize skal: ", site.size(), " druhu, ", troj, " troj. na sadu")
	# mekke rostliny (mech, kapradi, byliny) kolizi nemaji (radce 13:20: mech u tvrze se obchazel jako predmet) -
	# export jim nechal kvadr (u mechu zvetseneho 25-50x i 4 m vysoky)
	var mekke := {}
	for key: String in data["rostliny"]:
		for mk: String in MEKKE:
			if key.begins_with(mk):
				for t: Array in data["rostliny"][key]:
					mekke[Vector2i(floori(float(t[3])), floori(float(t[11])))] = true
	# skryte balvany u tvrze (uzel Skaly, Misa: smazat): jejich kvadry z exportu by zustaly jako neviditelne prekazky
	# (test prochod: tvrz-ves zasekl u (11, 60))
	var skryte := {}
	var sk_mi := parent.find_child("Skaly", true, false) as MeshInstance3D
	if sk_mi and not sk_mi.visible and sk_mi.mesh:
		var sxf := sk_mi.global_transform
		for v: Vector3 in sk_mi.mesh.get_faces():
			var g := sxf * v
			skryte[Vector2i(floori(g.x), floori(g.z))] = true
	var bez := 0
	var bez_sk := 0
	for c: Array in data["kolize"]:
		var kc := Vector2i(roundi(float(c[0]) * 2.0), roundi(float(c[2]) * 2.0))
		if veze.has(kc):
			continue
		# uvnitr hradeb tvrze (vcetne zdi a vezi) nic nevynechavat: filtry nize (kvadry rostlin u mechu, skryte balvany)
		# brali i podlahu ochozu, podesty a stupne vezi, zdi vezi a pilire palace (Misa 0.70: propady z ochozu a ve vezi,
		# louc ani tapiserie na zed nesly; test steny, prochod "schody ve vezi")
		var v_tvrzi := float(c[0]) > -29.0 and float(c[0]) < 19.6 and float(c[2]) > -17.8 and float(c[2]) < 17.9
		# jen nizke kvadry (balvany do 3 m): pilire severni zdi palace mezi vyklenky (1,3-1,6 m siroke, 8-12 m vysoke)
		# lezi pod skrytou siti Skaly a byly pryc - tapiserie a louc na prostredni zed nesly (Misa 0.70, test steny)
		if not v_tvrzi and skryte.has(Vector2i(floori(float(c[0])), floori(float(c[2])))) and maxf(absf(c[7]), absf(c[9])) < 3.0 and absf(c[8]) < 3.0:
			bez_sk += 1
			continue
		# kvadr rostliny z exportu (do 2 m) u mekke rostliny do 1 m od stredu (stred kvadru neni pata modelu)
		var u_mekke := false
		for dx in range(-1, 2):
			for dz in range(-1, 2):
				u_mekke = u_mekke or mekke.has(Vector2i(floori(float(c[0])) + dx, floori(float(c[2])) + dz))
		if not v_tvrzi and u_mekke and maxf(absf(c[7]), absf(c[9])) < 2.0 and absf(c[8]) < 2.5:     # ne pilire zdi (test steny)
			bez += 1
			continue
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(absf(c[7]), absf(c[8]), absf(c[9])).max(Vector3(0.02, 0.02, 0.02))
		var rot := Quaternion(c[4], c[5], c[6], c[3]).normalized()
		# zabradli schodu (blender/fort.py rail: kvadr 0,12 x 1,1 x L sklopeny podel ramene): celo sklopeneho kvadru
		# je kolme na rameno, na podeste tedy trci sikmo nad ni ve vysce hrudi a kapsle se o nej zastavila (Misa 0.63,
		# test prochod "schody na ochoz": naraz normala -z na konci zabradli). Misto kvadru hranol se svislymi cely:
		# spodni hrana podel ramene, vyska 1,1 m svisle - konec zabradli je svisla plocha na okraji ramene
		if box.size.x < 0.15 and absf(box.size.y - 1.1) < 0.05 and box.size.z > 1.5 and absf((Basis(rot) * Vector3.BACK).y) > 0.2:
			var bs := Basis(rot)
			var ax := bs * Vector3.BACK * (box.size.z * 0.5)
			var dn := bs * Vector3.UP * (box.size.y * 0.5)
			var sx := bs * Vector3.RIGHT * (box.size.x * 0.5)
			var cp := Vector3(c[0], c[1], c[2])
			# konce spodni hrany vodorovne tam, kde stred cela kvadru (ne jeho spodni roh): roh horniho konce trcel
			# 0,4 m do podesty a v zatacce na horni rameno zbylo 0,7 m pro kapsli 0,8 m (Misa 0.65: schody na hradbu,
			# "prostredni podesta a schody nahoru"); jeste 5 cm kratsi
			var axn := ax.normalized()
			var axh := Vector2(axn.x, axn.z)
			var sp := Vector2(dn.x, dn.z).dot(axh) / maxf(axh.length_squared(), 0.0001)
			var hl := box.size.z * 0.5 - 0.05
			var body_pts := PackedVector3Array()
			for e: Vector3 in [cp - dn + axn * (sp - hl), cp - dn + axn * (sp + hl)]:
				for sd: float in [-1.0, 1.0]:
					body_pts.append(e + sx * sd)
					body_pts.append(e + sx * sd + Vector3.UP * box.size.y)
			var cvx := ConvexPolygonShape3D.new()
			cvx.points = body_pts
			cs.shape = cvx
			body.add_child(cs)
			continue
		cs.shape = box
		cs.transform = Transform3D(Basis(rot), Vector3(c[0], c[1], c[2]))
		# rampa schodu (fort.py stairs: deska 0,1 m, osa po hranach stupnu, ~45 st.): horni plocha 5 cm nad hranou
		# = na podeste hrana 7 cm a k tomu 45 st. -> kapsle se o ni zastavila; a deska 0,1 m je tenka - kapsle opreta o
		# jeji spodni hranu se vytlacila DOLU pod ni a propadla na zem (Misa 0.63 "propadl podestou", test "schody na
		# ochoz": z podesty y 3,2 na zem y 0 u z 6,7). Deska 0,6 m dolu, horni plocha po hranach stupnu.
		if absf(box.size.y - 0.1) < 0.02 and box.size.z > 2.0 and box.size.x > 0.8 and absf((Basis(rot) * Vector3.BACK).y) > 0.3:
			box.size.y = 0.6
			cs.position -= Basis(rot) * Vector3.UP * 0.3
		# podesty schodu (deska 0,2 m vodorovne): z rampy na podestu hrana -> kapsle se vytlacila pod tenkou podestu a
		# propadla (test: na podeste y 3,08 < 3,25) - podesta 0,8 m dolu, horni plocha stejna
		# podlaha pavlace palace (0,08 m, Misa 0.65 "na nadvori nejde vyjit ani sejit, propadl") a podesty veze (0,1 m)
		# stejne: tenka vodorovna deska nad zemi -> 0,8 m dolu, horni plocha stejna
		var tl := box.size.y
		if tl > 0.06 and tl < 0.22 and box.size.x > 0.8 and box.size.z > 0.8 and absf((Basis(rot) * Vector3.UP).y) > 0.99 \
				and float(c[1]) > 1.0:
			box.size.y = 0.8
			cs.position.y -= 0.4 - tl * 0.5
		body.add_child(cs)
	print("kolize: %d kvadru mekkych rostlin vynechano, %d kvadru skrytych balvanu" % [bez, bez_sk])


## Posledni posazeni na to, co hrac vidi a po cem chodi (radce 20:05 bod 1): paprsek do fyziky sveta (teren, skaly,
## balvany, stavby - kmeny jeste nejsou). Mrizka 2 m se od vzdalene site terenu (Teren_okoli, ridsi) v zarezu potoka
## lisi az o 10 m - to byly stromy a kere visici nad svahem. Visi-li pata vic nez 0,25 m, dosedne (zapusteni zustava);
## co lezi za okrajem terenu (paprsek nic nenajde ani shora), se zahodi.
const NA_POVRCH_NAD := 0.5               # paprsek usazeni od paty nahoru (i test zasazeni visi_*: tataz definice)


func _na_povrch(parent: Node3D) -> void:
	var space := parent.get_world_3d().direct_space_state
	var r: Dictionary = data["rostliny"]
	var dolu := 0
	var pryc := 0
	for key: String in r:
		if key.begins_with("skala_"):
			continue
		var zust: Array = []
		for t: Array in r[key]:
			var x := float(t[3])
			var z := float(t[11])
			var y := float(t[7])
			if absf(x + 4.5) < 24.0 and absf(z - 0.4) < 19.0:
				zust.append(t)                                # nadvori tvrze
				continue
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, y + NA_POVRCH_NAD, z), Vector3(x, y - 80.0, z)))
			if h.is_empty():
				var hu := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, y + 120.0, z), Vector3(x, y, z)))
				if hu.is_empty():
					pryc += 1                                 # za okrajem terenu s kolizi (ani pod, ani nad nic)
					continue
				zust.append(t)                                # pod povrchem (zapusteny balvan, kamen v korytu)
				continue
			var hy := float((h["position"] as Vector3).y)
			if y > hy + 0.25:
				var ponor := clampf(_vyska(x, z) - y, 0.05, 1.0)
				t[7] = hy - ponor
				dolu += 1
			zust.append(t)
		r[key] = zust
	print("na povrch (fyzika): dolu %d, za okrajem pryc %d" % [dolu, pryc])


## Impostor ma polohu v pul presnosti (do 6 cm vedle stromu): borovice na hrane skalni veze pak "visela" 4,5 m nad
## zemi pod vezi. Nejvyssi zasah z paprsku v bode a 7 cm kolem.
static func paprsek_imp(space: PhysicsDirectSpaceState3D, pos: Vector3, h: Dictionary) -> Dictionary:
	for o: Vector2 in [Vector2(0.07, 0), Vector2(-0.07, 0), Vector2(0, 0.07), Vector2(0, -0.07)]:
		var p := pos + Vector3(o.x, 0, o.y)
		var h2 := space.intersect_ray(PhysicsRayQueryParameters3D.create(p + Vector3(0, 0.5, 0), p - Vector3(0, 60, 0)))
		if not h2.is_empty() and (h.is_empty() or (h2["position"] as Vector3).y > (h["position"] as Vector3).y):
			h = h2
	return h


## Dosednuti po prvnim kroku fyziky (main po build): tvary pridane do tela uz ve scene se do prostoru propisi az
## krokem fyziky, _na_povrch je proto nevidel vsechny (skaly skalniho mesta, kvadry) - kamen na skale, mech
## a borovice nad vezi visely 1-1,5 m. Tady stejny paprsek jako hrac/test nad kazdou instanci: visi-li pata
## vic nez 0,25 m, dosedne 5 cm pod povrch.
## Najezdy mostu (Misa 0.60: "most nema napojeni"; "prekresli krajinu"): zarez potoka snizil teren i tam, kam
## mela z mostu navazovat cesta (mostovka 2-5 m nad zemi). Konce mostovky z modelu (hlavni osa vrcholu, most je
## sikmo), teren pred kazdym koncem zvednout k mostovce a do 14 m plynule zpet do puvodniho; v sirce mostovky + 3 m.
## Pred kolizemi a pred mrizkou vysek (trava, rostliny sedi na novem terenu).
const NAJEZD_DELKA := 14.0
var _najezdy: Array = []                  # [konec Vector2, smer ven Vector2, bok Vector2, pul sirky, y mostovky]


func _najezdy_mostu(root: Node3D) -> void:
	var mi := root.find_child("Most_potok", true, false) as MeshInstance3D
	if mi == null or mi.mesh == null:
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var body: Array = []
	var ymax := -INF
	var ymin := INF
	for si in mi.mesh.get_surface_count():
		for q: Vector3 in (mi.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX] as PackedVector3Array):
			var w := xf * q
			body.append(w)
			ymax = maxf(ymax, w.y)
			ymin = minf(ymin, w.y)
	if body.is_empty():
		return
	# mostovka: nejcastejsi vyska vrcholu v horni polovine (prkna), po 5 cm
	var hist := {}
	for w: Vector3 in body:
		if w.y > ymin + (ymax - ymin) * 0.35 and w.y < ymax - 0.6:
			var b := roundi(w.y * 20.0)
			hist[b] = int(hist.get(b, 0)) + 1
	var yb := 0
	var nb := -1
	for b: int in hist:
		if int(hist[b]) > nb:
			nb = hist[b]
			yb = b
	var y_most := yb / 20.0 + 0.05
	# hlavni osa v pudorysu (kovariance vrcholu mostovky)
	var c := Vector2.ZERO
	var deck: Array = []
	for w: Vector3 in body:
		if absf(w.y - y_most) < 0.5:
			deck.append(Vector2(w.x, w.z))
			c += Vector2(w.x, w.z)
	c /= maxf(deck.size(), 1)
	var sxx := 0.0
	var szz := 0.0
	var sxz := 0.0
	for p2: Vector2 in deck:
		var d := p2 - c
		sxx += d.x * d.x
		szz += d.y * d.y
		sxz += d.x * d.y
	var uhel := 0.5 * atan2(2.0 * sxz, sxx - szz)
	var osa := Vector2(cos(uhel), sin(uhel))
	var bok := Vector2(-osa.y, osa.x)
	var a0 := INF
	var a1 := -INF
	var b1 := 0.0
	for p2: Vector2 in deck:
		var t := (p2 - c).dot(osa)
		a0 = minf(a0, t)
		a1 = maxf(a1, t)
		b1 = maxf(b1, absf((p2 - c).dot(bok)))
	for e: Array in [[a1, osa], [a0, -osa]]:
		_najezdy.append([c + osa * float(e[0]), e[1], bok, b1, y_most])
	print("most: mostovka y %.2f, osa %s, delka %.1f, pul sirky %.1f" % [y_most, osa, a1 - a0, b1])
	for n in root.find_children("Teren*", "MeshInstance3D", true, false):
		if String(n.name) == "Teren_obzor":
			continue
		_najezd_sit(n as MeshInstance3D)


## Vyska terenu v miste s najezdem mostu (y = puvodni; vraci zvednutou nebo y).
func najezd_y(x: float, z: float, y: float) -> float:
	for nj: Array in _najezdy:
		var d := Vector2(x, z) - (nj[0] as Vector2)
		var al := d.dot(nj[1])
		var lat := absf(d.dot(nj[2]))
		var sir: float = float(nj[3]) + 0.3
		# Misa 0.61: boky najezdu se zvedaly na 3 m = strmina (skala, "klin" pod mostem) -> pozvolny bok 9 m
		if al < -NAJEZD_DELKA or al > NAJEZD_DELKA or lat > sir + 9.0:
			continue
		var cil: float = float(nj[4]) - 0.08                     # tesne pod prkny
		var t := smoothstep(0.0, NAJEZD_DELKA, maxf(al, 0.0))
		var wl := 1.0 - smoothstep(sir, sir + 9.0, lat)
		wl *= wl * (3.0 - 2.0 * wl)
		var ny := lerpf(cil, y, t)
		if al < -1.5:
			# pod koncem mostovky svah naspu 1:1,25 (Misa 0.62: najezd koncil 1,5 m za koncem svislou stenou, pata mostu
			# a kuly visely nad zarezem); do vody (sirka hladiny + 1 m) nikdy - hladina pod mostem souvisla
			ny = cil - (-al - 1.5) * 0.8
			if koryto != null:
				var bl: Array = koryto.blizko(x, z)
				if not bl.is_empty() and float(bl[0]) < float(bl[2]) + 1.0:
					continue
		if ny > y:
			y = lerpf(y, ny, wl)
	return y


func _najezd_sit(mi: MeshInstance3D) -> void:
	var am := mi.mesh as ArrayMesh
	if am == null or _najezdy.is_empty():
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var inv := xf.affine_inverse()
	var nove := ArrayMesh.new()
	var zmen := 0
	for si in am.get_surface_count():
		var arr := am.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		for i in v.size():
			var w := xf * v[i]
			var ny := najezd_y(w.x, w.z, w.y)
			if ny > w.y + 0.01:
				v[i] = inv * Vector3(w.x, ny, w.z)
				zmen += 1
		arr[Mesh.ARRAY_VERTEX] = v
		arr[Mesh.ARRAY_NORMAL] = null
		arr[Mesh.ARRAY_TANGENT] = null
		var st2 := SurfaceTool.new()
		st2.create_from_arrays(arr)
		st2.generate_normals()
		if arr[Mesh.ARRAY_TEX_UV] != null:
			st2.generate_tangents()
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, st2.commit_to_arrays())
		nove.surface_set_material(si, am.surface_get_material(si))
		nove.surface_set_name(si, am.surface_get_name(si))
	if zmen > 0:
		mi.mesh = nove
		print("  najezd mostu: %s %d vrcholu" % [mi.name, zmen])


func dosednout(parent: Node3D) -> void:
	var rost := parent.find_child("Rostliny", true, false)
	if rost == null:
		return
	var space := parent.get_world_3d().direct_space_state
	var n := 0
	for mmi in rost.find_children("*", "MultiMeshInstance3D", true, false):
		if String(mmi.name).begins_with("skala_"):
			continue
		var mm: MultiMesh = (mmi as MultiMeshInstance3D).multimesh
		if mm == null:
			continue
		var imp := String(mmi.name).begins_with("impostor_")
		var xf := (mmi as Node3D).global_transform
		if String(mmi.name).begins_with("mech_") or String(mmi.name).begins_with("moss_"):
			n += _mech_na_zem(space, mm, xf)
			continue
		for i in mm.instance_count:
			var pos: Vector3
			var ti := Transform3D.IDENTITY
			if imp:
				var cd := mm.get_instance_custom_data(i)
				pos = xf.origin + Vector3(cd.r, cd.g, cd.b)
			else:
				ti = mm.get_instance_transform(i)
				pos = xf * ti.origin
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(pos + Vector3(0, 0.5, 0), pos - Vector3(0, 60, 0)))
			if imp:
				h = paprsek_imp(space, pos, h)
			if h.is_empty():
				continue
			var dy := (h["position"] as Vector3).y - 0.05 - pos.y
			if dy > -0.25:
				continue
			n += 1
			if imp:
				var cd := mm.get_instance_custom_data(i)
				cd.g += dy
				mm.set_instance_custom_data(i, cd)
			else:
				ti.origin += xf.basis.inverse() * Vector3(0, dy, 0)
				mm.set_instance_transform(i, ti)
	print("dosednuti po fyzice: ", n)


## Misa 0.68/0.69 "mech se vznasi, i na dvore tvrze": placka mechu (~1 m) lezi na kolizi (kamen, dlazba, teren)
## jen stredem - na nerovne zemi okraje visi. Sklopit podle normaly povrchu pod stredem a posadit na nejnizsi z 5 bodu
## (stred + 4 okraje v polovine sirky), 3 cm do povrchu: radeji kus zapadly nez ve vzduchu.
func _mech_na_zem(space: PhysicsDirectSpaceState3D, mm: MultiMesh, xf: Transform3D) -> int:
	var n := 0
	var r0 := mm.mesh.get_aabb().size
	for i in mm.instance_count:
		var ti := mm.get_instance_transform(i)
		var g := xf * ti
		var sc := g.basis.get_scale().x
		var rr := maxf(r0.x, r0.z) * sc * 0.4
		var pos := g.origin
		var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(pos + Vector3(0, 0.6, 0), pos - Vector3(0, 3.0, 0)))
		if h.is_empty():
			continue
		var nrm: Vector3 = h["normal"]
		var y: float = (h["position"] as Vector3).y
		for o: Vector2 in [Vector2(rr, 0), Vector2(-rr, 0), Vector2(0, rr), Vector2(0, -rr)]:
			var q := Vector3(pos.x + o.x, y, pos.z + o.y)
			var h2 := space.intersect_ray(PhysicsRayQueryParameters3D.create(q + Vector3(0, 0.6, 0), q - Vector3(0, 1.5, 0)))
			if not h2.is_empty():
				# na sklopene placce je okraj o sklon vys - porovnat s rovinou povrchu pod stredem
				var rov: float = y - (nrm.x * o.x + nrm.z * o.y) / maxf(nrm.y, 0.3)
				y = minf(y, (h2["position"] as Vector3).y + (y - rov))
		var yaw := atan2(-g.basis.x.z, g.basis.x.x)
		var bs := Basis(Quaternion(Vector3.UP, nrm.normalized())) * Basis(Vector3.UP, yaw).scaled(g.basis.get_scale())
		var nova := Transform3D(bs, Vector3(pos.x, y - 0.03, pos.z))
		mm.set_instance_transform(i, xf.affine_inverse() * nova)
		n += 1
	return n


## Mekka rostlina z rozsevu (kere v korytu, u prikopu) na miste maleho kvadru z exportu (kamen, polena): hrac by
## narazil do "kere" (Misa 20:10: krovim projde) - rostlina pryc, kamen zustava.
func _mekke_mimo_kvadry() -> void:
	var kvadry := {}
	for c in _kolize_body.get_children():
		var cs := c as CollisionShape3D
		if cs == null or not (cs.shape is BoxShape3D):
			continue
		var sz: Vector3 = (cs.shape as BoxShape3D).size
		if maxf(sz.x, sz.z) >= 2.0:
			continue
		var key := Vector2i(floori(cs.position.x), floori(cs.position.z))
		if not kvadry.has(key):
			kvadry[key] = []
		(kvadry[key] as Array).append(Vector2(cs.position.x, cs.position.z))
	var pryc := 0
	var r: Dictionary = data["rostliny"]
	for k: String in r:
		var mek := false
		for m: String in MEKKE:
			mek = mek or k.begins_with(m)
		if not mek:
			continue
		var zust: Array = []
		for t: Array in r[k]:
			var pt := Vector2(float(t[3]), float(t[11]))
			var key := Vector2i(floori(pt.x), floori(pt.y))
			var u := false
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for c2: Vector2 in kvadry.get(key + Vector2i(dx, dz), []):
						u = u or c2.distance_to(pt) < 0.6
			if u:
				pryc += 1
			else:
				zust.append(t)
		r[k] = zust
	print("mekke na kvadru pryc: ", pryc)


## Pesina je volna (test prochod: balvan sute pod skalami pres pesinu na Pustou skalu): stromy, balvany, padle kmeny,
## parezy a vetsi kameni do 1,2 m od osy pesiny pryc - kameni na kraji (0,8-1,5 m) a mekke rostliny zustavaji.
func _pesiny_volne() -> void:
	var r: Dictionary = data["rostliny"]
	var pryc := 0
	var smazane := {}
	# skala, kterou osa pesiny neobesla (dve veze tesne u sebe - odsunuti mezi nimi osciluje): pesina ma prednost,
	# skala pryc i se vzdalenymi verzemi (test prochod: tvrz-skaly-hostinec u (-105, 267))
	var skal := 0
	for key: String in r.keys():
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var me := _skala_sit(key)
		if me == null:
			continue
		var rp := maxf(me.get_aabb().size.x, me.get_aabb().size.z) * 0.5
		var vv := me.get_faces()
		for t: Array in r[key]:
			var sc := Vector3(t[0], t[4], t[8]).length()
			if pes_d(float(t[3]), float(t[11])) > rp * sc + 1.0:
				continue
			# prekazi jen skala, jejiz sit zasahuje do prujezdu hrace: 0,7 m od osy, 0,3-2 m nad zemi
			var xf := Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])), Vector3(t[3], t[7], t[11]))
			for i in range(0, vv.size(), 3):
				var g := xf * vv[i]
				if pes_d(g.x, g.z) < 0.7:
					var nad := g.y - _vyska(g.x, g.z)
					if nad > 0.3 and nad < 2.0:
						smazane[Vector2i(roundi(float(t[3]) * 4.0), roundi(float(t[11]) * 4.0))] = true
						break
	for key: String in r.keys():
		if not key.begins_with("skala_"):
			continue
		var zs: Array = []
		for t: Array in r[key]:
			if smazane.has(Vector2i(roundi(float(t[3]) * 4.0), roundi(float(t[11]) * 4.0))):
				skal += 1
			else:
				zs.append(t)
		r[key] = zs
	if skal > 0:
		print("pesiny volne: skal pryc ", skal)
	for key: String in r:
		var tvrde := key.begins_with("balvan_") or key.begins_with("dead_tree") or key.begins_with("tree_stump") \
				or key.begins_with("root_cluster") or _imp_druh(key.substr(0, key.rfind("_"))) != ""
		if not tvrde:
			continue
		# balvan: polomer podle site a meritka (velky balvan 1,5 m od osy pesinu prekryl)
		var rp := 0.0
		if key.begins_with("balvan_") and not key.contains("_daleko"):
			var me := _skala_sit(key.substr(0, key.rfind("_")) + "_0")
			if me:
				rp = maxf(me.get_aabb().size.x, me.get_aabb().size.z) * 0.5
		var zust: Array = []
		for t: Array in r[key]:
			var q := Vector2(float(t[3]), float(t[11]))
			if pes_d(q.x, q.y) < 1.2 + rp * Vector3(t[0], t[4], t[8]).length():
				pryc += 1
				smazane[Vector2i(roundi(q.x * 4.0), roundi(q.y * 4.0))] = true
				continue
			zust.append(t)
		r[key] = zust
	# kolize odebranych (balvany maji trimesh z _collisions uz pred rozsevem): jinak neviditelna prekazka na pesine
	var kol := 0
	for c in _kolize_body.get_children():
		var cs := c as CollisionShape3D
		if cs and smazane.has(Vector2i(roundi(cs.position.x * 4.0), roundi(cs.position.z * 4.0))):
			cs.queue_free()
			_kolize_body.remove_child(cs)
			kol += 1
	print("pesiny volne: pryc %d, kolizi %d" % [pryc, kol])


## Kmeny stromu (Misa 20:10: "hrac projde krovim, ale stromem, kamenem, skalou ne"): valec do 3 m, prumer podle
## vysky stromu (impostor) a meritka; kere, mlade stromky a vzdalene verze bez kolize.
func _kmeny() -> void:
	var r: Dictionary = data["rostliny"]
	var tvary := {}
	var n := 0
	for key: String in r:
		if key.contains("_daleko") or key.contains("sapling"):
			continue
		var kind := key.substr(0, key.rfind("_"))
		var d := _imp_druh(kind)
		if d == "":
			continue
		var vys := float(_imp_meta[d]["vyska"])
		for t: Array in r[key]:
			var sc := Vector3(t[0], t[4], t[8]).length()
			var pr := clampf(vys * sc * 0.012, 0.12, 0.6)          # strom 20 m -> kmen 0,48 m prumer
			var q := snappedf(pr, 0.04)
			if not tvary.has(q):
				var cy := CylinderShape3D.new()
				cy.radius = q
				cy.height = 3.0
				tvary[q] = cy
			var xf := Transform3D(Basis(), Vector3(float(t[3]), float(t[7]) + 1.4, float(t[11])))
			if kolize(tvary[q], AABB(Vector3(-q, -1.5, -q), Vector3(2 * q, 3.0, 2 * q)), xf, float(t[7])):
				n += 1
	print("kolize kmenu: ", n)


## Jedine misto, kde vznika kolizni teleso krajiny (radce 20:05 bod 3; Misa 20:10: "hrac projde krovim, ale stromem,
## kamenem, skalou ne - co jde preskocit, to preskoci, ostatni musi obejit, fyzika"). Tvrde veci (skala, balvan, kamen,
## kmen, padly strom) kolizi maji vzdy; mekke (ker, mech, kapradi, trava) nikdy - ty sem nechodi. Jen co vycniva mene
## nez 0,15 m, se vynecha (krok hrace to prekroci stejne, usetri se teleso). bb = AABB tvaru v jeho souradnicich.
const KOLIZE_MIN := 0.15
const MEKKE := ["mech_", "moss_", "kapradi_", "ker_husty", "ker_kulaty", "fern_", "celandine", "periwinkle", "dandelion", "weed_plant", "nettle",
		"shrub_", "sipek", "bez_cerny", "divoka_trava", "grass_", "rakos", "orobinec", "bark_debris", "dry_branches"]


## Misa 0.66/0.67 pad (RAM): 26 500 CollisionShape3D (skaly, balvany, kmeny) po cele mape. Po postaveni sveta
## (vcetne dosednuti) se tvary z kolize() presunou do dat po bunkach KOL_BUNKA a uzly vznikaji jen v okoli hrace
## (kolize_okoli, 3 x 3 bunky = aspon 32 m kolem). Kvadry staveb z exportu zustavaji vzdy.
const KOL_BUNKA := 32.0
var _kol_data := {}                       # bunka -> [[tvar, transform], ...]
var _kol_uzly := {}                       # bunka -> StaticBody3D
var _kol_stred := Vector2i(1 << 20, 0)
var kol_vse := false                      # testy: vsechny bunky nactene (paprsky pres celou mapu)


## Misa 0.70 (trava ve vstupu do veze (-23,-13) a v kovarne (-12,8)): offline kryti (louka/kryti.bin) tyto stavby
## neznalo. Po postaveni kolizi paprsky shora po 0,5 m v pudorysu tvrze: prvni zasah > 1,6 m nad terenem = strecha,
## strop nebo ochoz -> pod tim trava neroste (louka._v_budove).
const TK_R := Rect2(-29.0, -18.0, 49.0, 36.0)
var kryti_tvrz := PackedByteArray()


func tvrz_kryti(space: PhysicsDirectSpaceState3D) -> void:
	var nx := int(TK_R.size.x * 2.0)
	var nz := int(TK_R.size.y * 2.0)
	var out := PackedByteArray()
	out.resize(nx * nz)
	var n := 0
	for j in nz:
		for i in nx:
			var x := TK_R.position.x + (i + 0.5) * 0.5
			var z := TK_R.position.y + (j + 0.5) * 0.5
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 40.0, z), Vector3(x, -10.0, z)))
			var pod := not h.is_empty() and (h["position"] as Vector3).y > _vyska(x, z) + 1.6
			# krov kovarny a zbrojnice (blender/hospodar.py forge_armory) nema kolizi
			pod = pod or (x > -20.5 and x < -3.7 and z > 8.6 and z < 15.9)
			if pod:
				out[j * nx + i] = 1
				n += 1
	kryti_tvrz = out
	print("tvrz kryti: %d bunek pod strechou" % n)


func pod_strechou_tvrze(x: float, z: float) -> bool:
	if kryti_tvrz.is_empty() or not TK_R.has_point(Vector2(x, z)):
		return false
	var i := int((x - TK_R.position.x) * 2.0)
	var j := int((z - TK_R.position.y) * 2.0)
	return kryti_tvrz[j * int(TK_R.size.x * 2.0) + i] == 1


func kolize_rozdel() -> void:
	var n := 0
	for c in _kolize_body.get_children():
		var cs := c as CollisionShape3D
		if cs == null or not cs.has_meta("tok"):
			continue
		var b := Vector2i(floori(cs.position.x / KOL_BUNKA), floori(cs.position.z / KOL_BUNKA))
		if not _kol_data.has(b):
			_kol_data[b] = []
		(_kol_data[b] as Array).append([cs.shape, cs.transform])
		_kolize_body.remove_child(cs)
		cs.free()
		n += 1
	print("kolize po bunkach: %d tvaru v %d bunkach, zustava %d" % [n, _kol_data.size(), _kolize_body.get_child_count()])


## Radce 13:10 (tablet 0.68, les (10,549): fyzika 50 ms): cela bunka (az stovky trimeshu skal) v jednom snimku =
## spicka fyziky. Bunka se stavi po davkach KOL_DAVKA tvaru (kazda davka vlastni StaticBody3D), nejvys jedna davka
## za snimek; ruseni odlozene (bunky za 2 od hrace, jedno teleso za snimek). Hrac je od kraje 3 x 3 aspon 32 m.
const KOL_DAVKA := 20
var _kol_fronta: Array = []               # [bunka, index prvniho tvaru]
var _kol_rusit: Array = []                # StaticBody3D k uvolneni


func _kol_davka(b: Vector2i, od: int) -> int:
	var tv: Array = _kol_data[b]
	var sb := StaticBody3D.new()
	sb.name = "Kolize_%d_%d_%d" % [b.x, b.y, od]
	sb.collision_layer = _kolize_body.collision_layer
	sb.collision_mask = _kolize_body.collision_mask
	var do_ := mini(od + KOL_DAVKA, tv.size())
	for i in range(od, do_):
		var cs := CollisionShape3D.new()
		cs.shape = tv[i][0]
		cs.transform = tv[i][1]
		sb.add_child(cs)
	_kolize_body.get_parent().add_child(sb)
	(_kol_uzly[b] as Array).append(sb)
	return do_


func _kol_bunka(b: Vector2i, hned := false) -> void:
	if _kol_uzly.has(b) or not _kol_data.has(b):
		return
	_kol_uzly[b] = []
	if hned:
		var od := 0
		while od < (_kol_data[b] as Array).size():
			od = _kol_davka(b, od)
	else:
		_kol_fronta.append([b, 0])


## Kolize v okoli bodu (hrac; pred rychlym cestovanim cil s hned = true). Paprsek je vidi az po dalsim kroku fyziky.
func kolize_okoli(p: Vector3, hned := false) -> void:
	if _kol_data.is_empty() or kol_vse:
		return
	var c := Vector2i(floori(p.x / KOL_BUNKA), floori(p.z / KOL_BUNKA))
	if c != _kol_stred or hned:
		_kol_stred = c
		for b: Vector2i in _kol_uzly.keys():
			if absi(b.x - c.x) > 2 or absi(b.y - c.y) > 2 or (hned and (absi(b.x - c.x) > 1 or absi(b.y - c.y) > 1)):
				_kol_rusit.append_array(_kol_uzly[b])
				_kol_uzly.erase(b)
		var fr: Array = []
		for e: Array in _kol_fronta:
			if _kol_uzly.has(e[0]):
				fr.append(e)
		_kol_fronta = fr
		# nejdriv vlastni bunka, pak sousedni
		_kol_bunka(c, true if hned else false)
		for dx in range(-1, 2):
			for dz in range(-1, 2):
				_kol_bunka(c + Vector2i(dx, dz), hned)
		_kol_fronta.sort_custom(func(a2: Array, b2: Array) -> bool:
			return (a2[0] as Vector2i).distance_squared_to(c) < (b2[0] as Vector2i).distance_squared_to(c))
	if not planovac_on:
		_kol_krok()


## Jedna uloha kolizi: davka tvaru nejblizsi bunky (tezka), jinak uvolneni jednoho tela. Vraci jmeno ulohy nebo "".
func _kol_krok() -> String:
	if not _kol_fronta.is_empty():
		var e: Array = _kol_fronta[0]
		e[1] = _kol_davka(e[0], int(e[1]))
		if int(e[1]) >= (_kol_data[e[0]] as Array).size():
			_kol_fronta.pop_front()
		return "kolize davka %s" % str(e[0])
	elif not _kol_rusit.is_empty():
		var n: Node = _kol_rusit.pop_back()
		if is_instance_valid(n):
			n.queue_free()
		return "kolize uvolneni"
	return ""


## Testy: vsechny bunky (true), nebo zpet jen okoli (false).
func kolize_vse(vse: bool) -> void:
	kol_vse = vse
	_kol_stred = Vector2i(1 << 20, 0)
	if vse:
		for b: Vector2i in _kol_data:
			_kol_bunka(b, true)


## Misa 0.67 pad (RAM): 47 000 MultiMeshInstance3D rozsevu (druh x bunka 24 m) po cele mape. Druhy s dosahem
## do 100 m (byliny, puda, kere, kameni) jsou po postaveni jen data (buffer instanci) po bunkach a uzly vznikaji
## v okoli hrace jako trava (louka.gd): do ROST_R postavit (nejvyse ROST_ZA_SNIMEK za snimek, nejblizsi prvni),
## za ROST_R + 30 m zrusit.
var _rost_data := {}                      # bunka 24 m -> [{...}, ...]
var _rost_uzly := {}                      # bunka -> Array[MultiMeshInstance3D]
var _rost_root: Node3D
var rost_vse := false


func rostliny_rozdel(root: Node3D) -> void:
	_rost_root = root
	var n := 0
	var inst := 0
	for c in root.get_children():
		var mmi := c as MultiMeshInstance3D
		if mmi == null or not mmi.has_meta("tok"):
			continue
		var mm := mmi.multimesh
		var sc := mm.get_aabb().get_center()            # stred instanci (bunka 24 nebo 48 m)
		var b := Vector2i(floori(sc.x / BUNKA), floori(sc.z / BUNKA))
		if not _rost_data.has(b):
			_rost_data[b] = []
		var buf := mm.buffer
		var st := buf.size() / maxi(mm.instance_count, 1)          # floatu na instanci
		var od := 0
		while od < mm.instance_count:
			var nn := mini(512, mm.instance_count - od)
			(_rost_data[b] as Array).append({"mesh": mm.mesh, "buf": buf.slice(od * st, (od + nn) * st), "n": nn, "barvy": mm.use_colors,
					"data": mm.use_custom_data, "end": mmi.visibility_range_end, "okraj": mmi.visibility_range_end_margin,
					"stin": mmi.cast_shadow, "jm": "%s_%d" % [mmi.name, od], "mat": mmi.material_override})
			od += nn
		inst += mm.instance_count
		root.remove_child(mmi)
		mmi.free()
		n += 1
	print("rostliny po bunkach: %d multimesh (%d instanci) v %d bunkach" % [n, inst, _rost_data.size()])


## Radce 20:15 (overeno v kodu): cela bunka (vsechny MultiMeshe a buffery) najednou = spicka; limit se kontroloval
## az po ni. Ted po jednom MultiMeshi (davka do 512 instanci, rostliny_rozdel), rozpocet se kontroluje pred kazdym.
## Bunka je videt az cela (uzly skryte, pak naraz zobrazit - zadne prazdne mezery).
func _rost_dil(b: Vector2i, i: int) -> void:
	var e: Dictionary = (_rost_data[b] as Array)[i]
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = e["barvy"]
	mm.use_custom_data = e["data"]
	mm.mesh = e["mesh"]
	mm.instance_count = e["n"]
	mm.buffer = e["buf"]
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.name = e["jm"]
	mmi.visibility_range_end = e["end"]
	mmi.visibility_range_end_margin = e["okraj"]
	mmi.cast_shadow = e["stin"]
	if e["mat"]:
		mmi.material_override = e["mat"]
	mmi.visible = false
	_rost_root.add_child(mmi)
	(_rost_uzly[b] as Array).append(mmi)


func _rost_postav(b: Vector2i) -> void:
	_rost_uzly[b] = []
	for i in (_rost_data[b] as Array).size():
		_rost_dil(b, i)
	for m: Node3D in _rost_uzly[b]:
		m.visible = true


var _rost_rozest: Array = []              # [bunka, dalsi index] rozestavena bunka


## Rostliny v okoli bodu (hrac). vse = postavit hned vsechny v dosahu (start, rychle cestovani).
func rostliny_okoli(p: Vector3, vse := false, rozpocet_us := 1500) -> void:
	if _rost_data.is_empty() or rost_vse:
		return
	var ROST_R: float = float(_nac().get("rostliny_dosah_m", 115.0))
	var uvol: float = float(_nac().get("rostliny_uvolnit_m", ROST_R + 30.0))
	var q := Vector2(p.x, p.z)
	for b: Vector2i in _rost_uzly.keys():
		if (Vector2(b) * BUNKA + Vector2.ONE * BUNKA * 0.5).distance_to(q) > uvol + BUNKA:
			for m: Node in _rost_uzly[b]:
				m.queue_free()
			_rost_uzly.erase(b)
	var chybi: Array = []
	var r := int(ceil(ROST_R / BUNKA)) + 1
	var c0 := Vector2i(floori(p.x / BUNKA), floori(p.z / BUNKA))
	for dx in range(-r, r + 1):
		for dz in range(-r, r + 1):
			var b := c0 + Vector2i(dx, dz)
			if _rost_uzly.has(b) or not _rost_data.has(b):
				continue
			var d := (Vector2(b) * BUNKA + Vector2.ONE * BUNKA * 0.5).distance_to(q) - BUNKA * 1.5   # i bunky 48 m
			if d < ROST_R:
				chybi.append([d, b])
	chybi.sort_custom(func(a2: Array, b2: Array) -> bool: return a2[0] < b2[0])
	if vse:
		for e: Array in chybi:
			_rost_postav(e[1])
		_rost_rozest = []
		return
	# po jednom MultiMeshi do 1,5 ms za snimek; nejvys jedna bunka rozestavena
	_rost_chybi = chybi.size()
	var t0 := Time.get_ticks_usec()
	while Time.get_ticks_usec() - t0 < rozpocet_us:
		if _rost_rozest.is_empty():
			if chybi.is_empty():
				break
			var b0: Vector2i = (chybi.pop_front() as Array)[1]
			_rost_uzly[b0] = []
			_rost_rozest = [b0, 0]
		var bb: Vector2i = _rost_rozest[0]
		if not _rost_uzly.has(bb):
			_rost_rozest = []
			continue
		var ii: int = _rost_rozest[1]
		if ii >= (_rost_data[bb] as Array).size():
			for m: Node3D in _rost_uzly[bb]:
				m.visible = true
			_rost_rozest = []
			continue
		_rost_dil(bb, ii)
		_rost_rozest[1] = ii + 1


## PLANOVAC (radce 16:00 pravidlo 2, K1): jedna fronta okoli s rozpoctem na snimek (tablet 2 ms, PC 3 ms,
## pravidla_modelu.json nacitani). Poradi: kolize (blizko hrace, nejvys 1 tezka uloha = davka tvaru), pak rostliny
## (MultiMeshe po kusech do zbytku rozpoctu), uvolnovani jen kdyz nic nechybi. Panel: ms, fronta, posledni tezka uloha.
var planovac_on := true
var plan_ms := 0.0                    # cas planovace za posledni snimek
var plan_max_ms := 0.0                # nejvic za 2 s (panel)
var plan_uloha := ""                  # posledni tezka uloha a jeji cas
var _rost_chybi := 0
var _nac_d := {}


func _nac() -> Dictionary:
	if _nac_d.is_empty():
		_nac_d = Pravidla.cti("rozpocty", "planovac")          # pravidla/svet/rozpocty.json (drive pravidla_modelu.json nacitani)
	return _nac_d


func planovac(p: Vector3) -> void:
	var t0 := Time.get_ticks_usec()
	plan_kol_us = 0
	plan_rost_us = 0
	var mob := OS.has_feature("mobile") or OS.has_environment("TVRZ_MOBIL")
	var roz := int(_nac().get("rozpocet_us_tablet" if mob else "rozpocet_us_pc", 2000 if mob else 3000))
	kolize_okoli(p)                     # jen sprava bunek (stred, fronta, ruseni) - uloha nize
	okluzory_u_hrace(p)                 # okluzory remizku u hrace vypnout (16 vzdalenosti, levne)
	var tezke := int(_nac().get("tezkych_uloh_za_snimek", 1))
	if not _kol_fronta.is_empty() and tezke > 0:
		var tk := Time.get_ticks_usec()
		var u := _kol_krok()
		plan_kol_us = Time.get_ticks_usec() - tk
		plan_uloha = "%s %.1f ms" % [u, plan_kol_us / 1000.0]
	var zbyva := roz - int(Time.get_ticks_usec() - t0)
	if zbyva > 200:
		var tr := Time.get_ticks_usec()
		rostliny_okoli(p, false, zbyva)
		plan_rost_us = Time.get_ticks_usec() - tr
	if _kol_fronta.is_empty() and _rost_chybi == 0 and Time.get_ticks_usec() - t0 < roz:
		_kol_krok()                     # uvolneni (fronta kolizi prazdna = jen ruseni)
	plan_ms = (Time.get_ticks_usec() - t0) / 1000.0
	plan_max_ms = maxf(plan_max_ms, plan_ms)


var plan_kol_us := 0                     # kolizni davka tohoto snimku (diag: main: plan kolize)
var plan_rost_us := 0                    # rostliny okoli tohoto snimku


func plan_text() -> String:
	var fz := "fyzika %d Hz/%d kroky%s · " % [Engine.physics_ticks_per_second, Engine.max_physics_steps_per_frame, ", max %d FPS" % Engine.max_fps if Engine.max_fps > 0 else ""]
	var t := fz + "plánovač %.1f ms (max %.1f) · fronta: kolize %d, rostliny %d, uvolnit %d · poslední %s" % [plan_ms, plan_max_ms,
			_kol_fronta.size(), _rost_chybi, _kol_rusit.size(), plan_uloha if plan_uloha != "" else "-"]
	return t


## Testy: vsechny bunky (true), nebo zpet jen okoli (false).
func rostliny_vse(vse: bool) -> void:
	rost_vse = vse
	if vse:
		for b: Vector2i in _rost_data:
			if not _rost_uzly.has(b):
				_rost_postav(b)


func kolize(tvar: Shape3D, bb: AABB, xf: Transform3D, pata := INF) -> bool:
	var w: AABB = xf * bb
	var o := xf.origin
	var ter := _vyska(o.x, o.z) if pata == INF else pata
	if Vector2(o.x + 4.0, o.z).length() < 80.0:
		ter = minf(ter, _vyska_sit(o.x, o.z))             # val a prikop tvrze: mrizka louky je nezna
	if w.end.y - ter < KOLIZE_MIN:
		return false
	var cs := CollisionShape3D.new()
	cs.shape = tvar
	cs.transform = xf
	cs.set_meta("tok", true)
	_kolize_body.add_child(cs)
	return true


# ------------------------------------------------------------------ informace pro hru

## Vybaveni lomu (radce 16:20 bod 4): jen to, co lamaci potrebuji - pevne predmety (svet.json "vybaveni").
func _lom_vybaveni() -> void:
	var vb: Array = data.get("vybaveni", [])
	_lom_zabrano.clear()
	var kat_p: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://modely/predmety.json")) if FileAccess.file_exists("res://modely/predmety.json") else {}
	# Misa 24. 10. "vypada to tam neusporadane, nastuduj si ty stare obrazky (KCD lom u Talmberka 16:11)": jako na nich
	# - u steny osyp a leseni (jen u lamane casti, svetla stena), pred nim RADA pristresku a stanu s pracovisti
	# kameniku, za ni sklad hotovych kvadru v radach podel lomu, vozy u skladu, dal volna ujezdena plocha
	# s kolejemi a kalouzemi, tabor (ohniste, lavice) u stanu, drevo na lesení na severnim konci.
	# [id, vzdalenost od paty steny (m), z, natoceni (u rovne steny podel z; pridava se odklon steny)]
	var polozky := [
			# rada pristresku a stanu (u 8-9)
			["stan_jehlan", 9.0, 916.0, 0.2], ["pristresek_plachta", 8.0, 928.0, 1.57], ["pristresek_maly", 8.5, 940.0, 1.57],
			["pristresek_plachta", 8.0, 970.0, 1.65],
			# pracoviste kamenika pod 1. pristreskem
			["kovadlina_spalek", 7.6, 927.2, 0.4], ["stolicka", 8.6, 926.6, 0.0], ["palice", 7.0, 928.6, 0.9],
			["kladivo_kamenicke", 8.2, 928.4, 0.2], ["bedna", 9.4, 929.6, 0.1], ["vedro", 6.8, 926.4, 0.0],
			# pracoviste pod 2. pristreskem
			["spalek", 8.2, 939.3, 0.0], ["kladivo_kamenicke", 8.0, 940.6, 1.2], ["krumpac", 9.6, 941.2, 0.6], ["kad", 7.4, 941.4, 0.0],
			# sklad pod 3. pristreskem: sudy, pytle, kad
			["sud", 7.2, 969.0, 0.0], ["sud_stary", 7.9, 969.4, 0.6], ["pytel_obili", 8.8, 970.6, 0.4], ["pytel_kupecky", 8.4, 971.4, 1.0],
			["bedna", 7.0, 971.2, 0.0],
			# tabor u stanu: ohniste s kotlem, lavice, spalky, kosik, voda
			["ohniste_kamenne", 15.5, 917.0, 0.0], ["lavice_selska", 15.5, 915.0, 0.0],
			["lavice_selska", 17.6, 917.2, 1.57], ["kosik", 14.4, 915.2, 0.4], ["sud", 13.2, 914.6, 0.0],
			["koryto_kone", 19.5, 921.0, 0.0],
			# drevo na leseni a palivo: severni konec, v rade
			["drevo_kulatina", 4.5, 908.6, 0.0], ["drevo_dlouha_2", 8.8, 908.4, 0.04], ["drevo_hromada", 12.5, 908.9, -0.6],
			["spalek_stipani", 15.0, 909.5, 0.0], ["kolo_vozu", 16.5, 908.4, 0.3],
			# vozy u skladu kvadru, trakare u prace
			["zebrinak", 20.5, 930.0, 1.57], ["zebrinak", 20.8, 943.5, 1.5], ["zebrinak", 14.5, 952.5, 1.6],
			["trakar", 5.2, 924.0, 0.3], ["trakar", 12.0, 938.5, 1.4], ["trakar", 4.6, 961.5, 2.0],
			# jerab u paty steny, vyloznik nad hromadou kvadru (radce 17:55), u paty hromada dreva
			["jerab_slapaci", 6.5, 956.0, 0.0], ["drevo_vysoka_1", 2.6, 961.0, 1.57],
			["zebrik", 4.6, 949.6, 0.0], ["lopata", 5.4, 950.6, 2.1], ["krumpac", 3.5, 952.0, 2.5]]
	var nrm := func(z: float) -> Vector2:
		var t := Vector2(lom_stena_x(z + 3.0) - lom_stena_x(z - 3.0), 6.0).normalized()
		return Vector2(t.y, -t.x)
	for it: Array in polozky:
		var z: float = it[2]
		var n: Vector2 = nrm.call(z)
		var x: float = lom_stena_x(z) + float(it[1]) * n.x
		z += float(it[1]) * n.y
		var yaw := float(it[3]) + atan2(-n.y, n.x)
		# Misa 0.76 "vozy, napajedlo, kamen levituji": pata na terenu pod celym pudorysem (rozmer z katalogu, otoceni
		# yaw) - vozy prumer pod koly (stoji na kolech, ne zapadle ani ve vzduchu), ostatni nejnizsi bod pudorysu
		var rz0: Array = (kat_p.get(String(it[0]), {}) as Dictionary).get("rozmer", [0.6, 0.6, 0.6])
		var y := pata_lom(x, z, yaw, float(rz0[0]), float(rz0[2]))
		var rec := {"id": it[0], "p": [x, y, z], "yaw": yaw}
		if NA_BODECH.has(String(it[0])):
			# Misa 0.77 "porad kolo od vozu levituje": vozy, napajedlo, trakar na oporne body (kola, nohy, spalky) -
			# poloha = prumer zasahu, naklon podle roviny bodu, yaw zustava (place_on_points)
			var pb := polozit_na_body(x, z, yaw, opory(String(it[0]), float(rz0[0]), float(rz0[2])))
			rec["p"] = [pb[0].x, pb[0].y, pb[0].z]
			rec["up"] = [pb[1].x, pb[1].y, pb[1].z]
		if String(it[0]) in NASTOJATO:
			rec["orient"] = 3                     # Misa 0.75 "krumpac postaveny na vysku by tak nestal" - polozit naplocho
		vb.append(rec)
		var rz: Array = (kat_p.get(String(it[0]), {}) as Dictionary).get("rozmer", [0.6, 0.6, 0.6])
		_lom_zabrano.append(Vector3(x, z, maxf(float(rz[0]), float(rz[2])) * 0.5 + 0.15))
	# leseni podel lamane casti steny (radce 17:55, Misa "5x vetsi, u steny"): ctyri useky ruzne vysoke, kazdy
	# zadni radou 0,35 m od steny, natoceny podle steny; na podlahach naradi a kvadry (mista z modelu)
	var rng := RandomNumberGenerator.new()
	rng.seed = 949
	var naradi := ["kladivo_kamenicke", "palice", "krumpac", "vedro", "kvadr_hruby_3", "kosik", "lopata"]
	var za := LESENI_Z.x
	for usek: Array in [["leseni_lom_3", 7.5], ["leseni_lom_2", 12.5], ["leseni_lom", 10.0], ["leseni_lom_3", 7.5]]:
		var zb := za + float(usek[1])
		var a := Vector2(lom_stena_x(za), za)
		var b := Vector2(lom_stena_x(zb), zb)
		var t := (b - a).normalized()
		var n := Vector2(t.y, -t.x)
		var c := (a + b) * 0.5
		var m := -INF
		for k in 11:
			var zz := lerpf(za, zb, k / 10.0)
			m = maxf(m, (Vector2(lom_stena_x(zz), zz) - c).dot(n))
		var inf_l: Dictionary = kat_p.get(usek[0], {})
		var piv: Array = inf_l.get("dily", {}).get("kolize", {}).get("pivot", [0.0, 0.4, 0.06])
		var zad := 1.6 - float(piv[2])                    # zadni rada za pocatkem modelu
		var pos := c + n * (m + 0.35 + zad)
		var yaw := atan2(t.y, -t.x)
		var y := INF
		for k in 7:
			var q := pos + t * lerpf(-float(usek[1]) / 2, float(usek[1]) / 2, k / 6.0)
			y = minf(y, minf(vyska_lom(q.x, q.y), vyska_lom(q.x - n.x * zad, q.y - n.y * zad)))
		vb.append({"id": usek[0], "p": [pos.x, y, pos.y], "yaw": yaw})
		_leseni_rect.append([a, b, n, m + 0.35 + zad + 2.0])
		var bs := Basis(Vector3.UP, yaw)
		var kvadru := 0
		for mp: Array in inf_l.get("dily", {}).get("kolize", {}).get("mista", []):
			if rng.randf() < 0.35:
				continue
			var id: String = naradi[rng.randi() % naradi.size()]
			if id == "kvadr_hruby_3":
				kvadru += 1
				if kvadru > 2:
					id = "vedro"
			var w := Vector3(pos.x, y, pos.y) + bs * Vector3(float(mp[0]), float(mp[1]), float(mp[2]))
			var r2 := {"id": id, "p": [w.x, w.y, w.z], "yaw": rng.randf() * TAU, "leseni": true}
			if id in NASTOJATO:
				r2["orient"] = 3
			vb.append(r2)
		za = zb + 0.4
	# zahony ve vsi: zeli a salat z Disku (Misa 24. 10.) misto zelenych koulí
	# nove domy (0.78) maji vlastni zahony (_zahrada) - hlavky na mistech starych zahradek lezely v trave
	# (Misa 0.82 "oprav zahony")
	if VES_DOMY and ResourceLoader.exists(VES_DOMY_GLB):
		_zeli_mista.clear()
	for m: Vector3 in _zeli_mista:
		var id := "salat" if rng.randf() < 0.3 else "zeli_hlavka"
		vb.append({"id": id, "p": [m.x, _vyska(m.x, m.z) - 0.05, m.z], "yaw": rng.randf() * TAU, "sc": rng.randf_range(0.8, 1.15)})
	print("zahony: %d hlavek zeli a salatu" % _zeli_mista.size())
	_trziste(vb, rng)
	data["vybaveni"] = vb


func _info() -> void:
	info["mista"] = data.get("nazvy_mist", [])          # ruiny a jina pojmenovana mista v krajine
	for r: Dictionary in data["mistnosti"]:
		var a: Array = r["ambient"]
		if r.has("yaw"):
			# otocena mistnost (chalupy ve vsi): stred podlahy, rozmery v ramci domu
			var sz: Vector3 = _v3(r["size"])
			var xf := Transform3D(Basis(Vector3.UP, float(r["yaw"])), _v3(r["pos"]))
			info["rooms"].append({"name": r["name"], "title": String(r.get("title", "")), "inv": xf.affine_inverse(), "c": xf.origin,
					"aabb": AABB(Vector3(-sz.x / 2, 0, -sz.z / 2), sz), "ambient": Color(a[0], a[1], a[2])})
			continue
		info["rooms"].append({"name": r["name"], "aabb": AABB(_v3(r["pos"]), _v3(r["size"])),
				"ambient": Color(a[0], a[1], a[2])})
	for fdat: Dictionary in data["ohne"]:
		var d := fdat.duplicate()
		d["pos"] = _v3(fdat["pos"])
		d["night_only"] = false
		info["fires"].append(d)
	for u: Dictionary in data["pouziti"]:
		var d2 := u.duplicate()
		d2["pos"] = _v3(u["pos"])
		info["use"].append(d2)
	for s: Array in data["kour"]:
		info["smoke"].append(_v3(s))


# ------------------------------------------------------------------ rostliny

const NIZKE := ["divoka_trava", "grass_medium_01", "grass_medium_02", "dandelion_01", "nettle_plant", "fern_02",
		"kamen_maly_1", "kamen_maly_2", "kamen_maly_3", "kamen_maly_4", "kamen_maly_5"]
const STREDNI := ["shrub_02", "sipek", "fir_sapling", "rock_moss_set_01", "dry_branches_medium_01", "tree_stump_01",
		"kamen_zula_1", "kamen_zula_2", "kamen_piskovec_1", "kamen_piskovec_2", "kamen_droba_1",
		"orobinec_1", "orobinec_2", "rakos_1", "rakos_2", "bez_cerny_1", "bez_cerny_2", "bez_cerny_3",
		"dead_tree_trunk", "dead_tree_trunk_02", "root_cluster_01", "pine_sapling_small", "tree_stump_02", "balvan_droba_1", "ker_husty", "ker_kulaty"]
## Podrost z druheho chatu (jen zblizka) a dvojice strom / vzdalena verze (prepnuti kolem 60 m).
const PODROST := ["kapradi_1", "kapradi_2", "kapradi_3", "kapradi_les", "kopretiny", "kvety_bile", "byliny", "mech_1", "mech_2", "mech_3", "celandine_01", "periwinkle_plant", "moss_01",
		"bark_debris_01"]
const LOD_M := 220.0
## Stromy zdalky: misto modelu z karet (zdalky ploche "placky") plny nizkopolygonovy tvar stejne velikosti
## (smrk vrstvene kuzely, listnac hrouda koruny); zblizka plny strom. Karty <model>_daleko se uz nepouzivaji.
# 0.61 (les 13-16 FPS na tabletu, overdraw karet listi): plny strom na tabletu jen do 40 m, dal impostor
var STROM_PREP := 40.0 if (OS.has_feature("mobile") or OS.has_environment("TVRZ_MOBIL")) else 60.0
const SKALA_LOD0 := 40.0
const SKALA_LOD1 := 120.0
const STROM_DOHLED := 120.0                # rozpocet: za 120 m zadne stromy (radeji prazdny obzor nez pad)
const ZJEDNODUSIT := {"nettle_plant": 300, "dandelion_01": 300, "celandine_01": 300, "fern_02": 300, "periwinkle_plant": 300,
		"weed_plant": 300, "bez_cerny": 600, "shrub_02": 600}
var _zjedn := {}


## Sit na nejvys `cil` trojuhelniku (podily povrchu podle velikosti); jen indexy, vrcholy a UV zustanou.
func _zjednodus(mesh: Mesh, cil: int) -> Mesh:
	if _zjedn.has(mesh):
		return _zjedn[mesh]
	var celk := 0
	for i in mesh.get_surface_count():
		var ia = mesh.surface_get_arrays(i)[Mesh.ARRAY_INDEX]
		celk += (ia.size() if ia != null else 0) / 3
	if celk <= cil or not (mesh is ArrayMesh):
		_zjedn[mesh] = mesh
		return mesh
	var am := mesh as ArrayMesh
	var nove := ArrayMesh.new()
	var po := 0
	for i in am.get_surface_count():
		var arr := am.surface_get_arrays(i)
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
		var t := idx.size() / 3
		var ct := maxi(12, int(float(cil) * t / celk))
		if t > ct:
			var st := SurfaceTool.new()
			st.create_from_arrays(arr)
			var lod := st.generate_lod(1e6, ct * 3)
			if lod.size() >= 3:
				arr[Mesh.ARRAY_INDEX] = lod
		po += (arr[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(i, am.surface_get_material(i))
		nove.surface_set_name(i, am.surface_get_name(i))
	print("zjednoduseno %s: %d -> %d troj." % [am.resource_path.get_file(), celk, po])
	_zjedn[mesh] = nove
	return nove


## Vyska bylin a kvetin ve hre [od, do] m (kopriva 0,25-0,5 - Misa: "vetsina kopriv ma cca 30 cm", pampeliska 0,15-0,35, vlastovicnik 0,3-0,6, kapradi 0,4-0,9).
const VYSKA_BYLIN := {"nettle_plant": Vector2(0.25, 0.5), "dandelion_01": Vector2(0.15, 0.35), "celandine_01": Vector2(0.3, 0.6),
		"fern_02": Vector2(0.4, 0.9), "periwinkle_plant": Vector2(0.1, 0.25),
		# Misa 0.64: "sedmikrasky jako slunecnice" - model ma hlavicky ~1/4 vysky: 12-20 cm = kvet 3-5 cm
		"kopretiny": Vector2(0.12, 0.2), "kvety_bile": Vector2(0.1, 0.17),
		"kapradi_": Vector2(0.35, 0.8),
		# radce 20:30: rakosi zblizka obri listy (2x) - rakos 1,2-2 m, orobinec 1-1,6 m
		"rakos_": Vector2(1.2, 2.0), "orobinec_": Vector2(1.0, 1.6)}
const LISTNACE := ["lipa", "dub", "briza", "vrba", "buk", "olse", "borovice"]
const TINT_LISTI := {"dub_": Color(0.6, 0.84, 0.58), "briza": Color(0.82, 0.96, 0.72), "smrk": Color(1.3, 1.4, 1.15),
		"borovice": Color(0.9, 1.05, 0.85)}
var _tvary := {}


func _strom_tvar(kind: String) -> String:
	if kind == "smrk" or kind.begins_with("smrk_"):
		return "smrk"
	for l: String in LISTNACE:
		if kind == l or kind.begins_with(l + "_"):
			return l
	return ""


## Plny tvar stromu do obrysu (aabb) puvodniho modelu: barva z vrcholu, dole tmavsi (zdalky objem, ne list papiru).
func _tvar_mesh(druh: String, bb: AABB, listi: Material = null) -> Mesh:
	var key := "%s_%d_%d_%d" % [druh, int(bb.size.y * 10), int(bb.size.x * 10), listi.get_instance_id() if listi else 0]
	if _tvary.has(key):
		return _tvary[key]
	var r := RandomNumberGenerator.new()
	r.seed = hash(key)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# obal koruny s texturou listi stromu (pruhledne mezery), pod nim tmave jadro - ne hladke jednobarevne koule
	var st2: SurfaceTool = null
	if listi and druh != "smrk":
		st2 = SurfaceTool.new()
		st2.begin(Mesh.PRIMITIVE_TRIANGLES)
	var c := bb.get_center()
	var y0 := bb.position.y
	var h := bb.size.y
	var rad := minf(bb.size.x, bb.size.z) * 0.5
	var kura := Color(0.2, 0.15, 0.1) if druh != "briza" else Color(0.6, 0.58, 0.52)
	var zel: Color = {"smrk": Color(0.07, 0.13, 0.06), "briza": Color(0.2, 0.28, 0.1), "vrba": Color(0.2, 0.26, 0.14),
			"borovice": Color(0.1, 0.16, 0.07),
			"olse": Color(0.11, 0.19, 0.07)}.get(druh, Color(0.14, 0.22, 0.08))
	# kmen
	var kr := maxf(h * 0.012, 0.12)
	_valec(st, Vector3(c.x, y0, c.z), kr, kr * 0.6, h * (0.5 if druh == "smrk" else 0.45), 5, kura, kura)
	if druh == "smrk":
		# patra kuzelu, kazde nize sirsi, zubaty okraj (vetve)
		var pater := 5
		var dole := y0 + h * 0.12
		for i in pater:
			var t0 := float(i) / pater
			var ya := dole + (h - (dole - y0)) * t0 * 0.92
			var yb := ya + (h - (dole - y0)) * 0.34
			if i == pater - 1:
				yb = y0 + h
			var rr := rad * (1.0 - t0 * 0.82) * r.randf_range(0.9, 1.05)
			_kuzel(st, Vector3(c.x, ya, c.z), rr, yb - ya, 9, r, zel * 0.6, zel * 1.15)
	else:
		# koruna: shluk hrud (zploštělé koule s nerovnym povrchem)
		var kz := y0 + h * (0.55 if druh == "borovice" else (0.32 if druh != "vrba" else 0.4))
		var kv := y0 + h - kz
		var n := 5 if rad > 3.0 else 4
		_hruda(st, Vector3(c.x, kz + kv * 0.5, c.z), Vector3(rad * 0.8, kv * 0.5, rad * 0.8), r, zel, st2)
		for i in n:
			var a := TAU * i / n + r.randf() * 0.6
			var d := rad * r.randf_range(0.35, 0.55)
			var p := Vector3(c.x + cos(a) * d, kz + kv * r.randf_range(0.35, 0.65), c.z + sin(a) * d)
			var s := rad * r.randf_range(0.45, 0.6)
			_hruda(st, p, Vector3(s, minf(s, kv * 0.4), s), r, zel * r.randf_range(0.9, 1.1), st2)
	st.generate_normals()
	var mesh := st.commit()
	if st2:
		st2.generate_normals()
		st2.commit(mesh)
		var lm := listi.duplicate() as Material
		if lm is BaseMaterial3D:
			(lm as BaseMaterial3D).cull_mode = BaseMaterial3D.CULL_DISABLED
		mesh.surface_set_material(1, lm)
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 1.0
	mat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	mat.diffuse_mode = BaseMaterial3D.DIFFUSE_LAMBERT_WRAP
	mesh.surface_set_material(0, mat)
	_tvary[key] = mesh
	return mesh


func _valec(st: SurfaceTool, b: Vector3, r0: float, r1: float, h: float, n: int, c0: Color, c1: Color) -> void:
	for i in n:
		var a0 := TAU * i / n
		var a1 := TAU * (i + 1) / n
		var p0 := b + Vector3(cos(a0) * r0, 0, sin(a0) * r0)
		var p1 := b + Vector3(cos(a1) * r0, 0, sin(a1) * r0)
		var q0 := b + Vector3(cos(a0) * r1, h, sin(a0) * r1)
		var q1 := b + Vector3(cos(a1) * r1, h, sin(a1) * r1)
		for v: Array in [[p0, c0], [q0, c1], [q1, c1], [p0, c0], [q1, c1], [p1, c0]]:
			st.set_color(v[1])
			st.add_vertex(v[0])


func _kuzel(st: SurfaceTool, b: Vector3, rr: float, h: float, n: int, r: RandomNumberGenerator, c0: Color, c1: Color) -> void:
	var spic := b + Vector3(0, h, 0)
	var okraj: Array = []
	for i in n * 2:
		# zuby: stridave dal a bliz, konce vetvi lehce dolu
		var a := TAU * i / (n * 2) + r.randf_range(-0.1, 0.1)
		var d := rr * (1.0 if i % 2 == 0 else 0.62) * r.randf_range(0.85, 1.1)
		okraj.append(b + Vector3(cos(a) * d, -h * (0.08 if i % 2 == 0 else 0.0), sin(a) * d))
	var m := okraj.size()
	for i in m:
		var a: Vector3 = okraj[i]
		var bb: Vector3 = okraj[(i + 1) % m]
		for v: Array in [[a, c0], [spic, c1], [bb, c0]]:
			st.set_color(v[1])
			st.add_vertex(v[0])
		# spodek patra (tmavy, zdola nevidet skrz)
		for v: Array in [[a, c0 * 0.5], [bb, c0 * 0.5], [b + Vector3(0, h * 0.2, 0), c0 * 0.4]]:
			st.set_color(v[1])
			st.add_vertex(v[0])


func _hruda(st: SurfaceTool, cen: Vector3, sz: Vector3, r: RandomNumberGenerator, zel: Color, st2: SurfaceTool = null) -> void:
	if st2:
		_obal(st2, cen, sz * 1.12, r)
		sz *= 0.82
	var ny := 4
	var nx := 9
	var body: Array = []
	for j in ny + 1:
		var row: Array = []
		var th := PI * j / ny
		for i in nx:
			var ph := TAU * i / nx
			var k := 1.0 if j == 0 or j == ny else r.randf_range(0.8, 1.15)
			var d := Vector3(sin(th) * cos(ph), cos(th), sin(th) * sin(ph))
			row.append(cen + Vector3(d.x * sz.x, d.y * sz.y, d.z * sz.z) * k)
		body.append(row)
	for j in ny:
		for i in nx:
			var a: Vector3 = body[j][i]
			var b: Vector3 = body[j][(i + 1) % nx]
			var c2: Vector3 = body[j + 1][i]
			var d2: Vector3 = body[j + 1][(i + 1) % nx]
			for v: Vector3 in [a, b, d2, a, d2, c2]:
				# nahore svetlejsi (slunce), dole tmavy stin koruny
				var t := clampf((v.y - cen.y) / sz.y * 0.5 + 0.5, 0.0, 1.0)
				st.set_color(zel * lerpf(0.45, 1.2, t))
				st.add_vertex(v)


var _listi_sh: Shader


func _listi_shader(om: BaseMaterial3D, bb: AABB, strom: bool) -> ShaderMaterial:
	if _listi_sh == null:
		_listi_sh = load("res://shaders/listi.gdshader")
	var m := ShaderMaterial.new()
	m.shader = _listi_sh
	m.resource_name = om.resource_name
	m.set_shader_parameter("barva", om.albedo_texture)
	m.set_shader_parameter("tint", om.albedo_color)
	m.set_shader_parameter("prah", om.alpha_scissor_threshold)
	var c := bb.get_center()
	m.set_shader_parameter("stred", Vector3(c.x, bb.position.y + bb.size.y * (0.62 if strom else 0.5), c.z))
	m.set_shader_parameter("vyska", maxf(bb.end.y, 0.5))
	m.set_shader_parameter("sila_vetru", 1.0 if strom else 0.6)       # kere mene
	m.set_shader_parameter("objem", 0.65 if strom else 0.5)
	return m


func _listi(mesh: Mesh) -> Material:
	# material listi stromu: povrch s pruhlednosti (alfa) - ten se pouzije na obal vzdalene koruny
	for i in mesh.get_surface_count():
		var m := mesh.surface_get_material(i)
		if m is BaseMaterial3D and (m as BaseMaterial3D).transparency != BaseMaterial3D.TRANSPARENCY_DISABLED \
				and (m as BaseMaterial3D).albedo_texture:
			return m
	return null


func _obal(st: SurfaceTool, cen: Vector3, sz: Vector3, r: RandomNumberGenerator) -> void:
	# koule s UV pro texturu listi (opakuje se zhruba po 2,5 m), nerovny povrch
	var ny := 4
	var nx := 9
	var rep := maxf(1.0, maxf(sz.x, sz.y) / 1.25)
	var body: Array = []
	for j in ny + 1:
		var row: Array = []
		var th := PI * j / ny
		for i in nx + 1:
			var ph := TAU * i / nx
			var k := 1.0 if j == 0 or j == ny or i == nx else r.randf_range(0.85, 1.12)
			var d := Vector3(sin(th) * cos(ph), cos(th), sin(th) * sin(ph))
			row.append(cen + Vector3(d.x * sz.x, d.y * sz.y, d.z * sz.z) * k)
		if j > 0 and j < ny:
			row[nx] = row[0]
		body.append(row)
	for j in ny:
		for i in nx:
			var q := [[j, i], [j, i + 1], [j + 1, i + 1], [j, i], [j + 1, i + 1], [j + 1, i]]
			for ij: Array in q:
				st.set_uv(Vector2(float(ij[1]) / nx * rep * 2.0, float(ij[0]) / ny * rep))
				st.add_vertex(body[ij[0]][ij[1]])


const IMP_BUNKA := 1024.0               # Misa 0.92 (tablet 1300 kresleni): 256 m = 312 uzlu, 180-220 kresleni u rybnika/hostince
const IMP_DOHLED := 900.0
var _imp_meta := {}


func _imp_druh(kind: String) -> String:
	if _imp_meta.is_empty() and FileAccess.file_exists("res://obrazky/impostory/impostory.json"):
		_imp_meta = JSON.parse_string(FileAccess.get_file_as_string("res://obrazky/impostory/impostory.json"))
	if _imp_meta.has(kind):
		return kind
	for d: String in _imp_meta:
		if kind.begins_with(d) or (d == "vrba" and kind.begins_with("vrba")):
			return d
	return ""


## Impostory: jeden ctverec na strom, MultiMesh po druzich a bunkach 256 m, jednotkove transformace
## (poloha v INSTANCE_CUSTOM), obal bunky rucne (jinak by Godot videl vsechny instance v pocatku).
func _impostory(root: Node3D, imp: Dictionary, bunka := IMP_BUNKA, dohled := IMP_DOHLED, jmeno := "impostor") -> void:
	var quad := ArrayMesh.new()
	var a := []
	a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-1, 0, 0), Vector3(1, 0, 0), Vector3(1, 2, 0), Vector3(-1, 2, 0)])
	a[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
	a[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	quad.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a)
	var n := 0
	for d: String in imp:
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/impostor.gdshader")
		m.set_shader_parameter("barva", load("res://obrazky/impostory/%s_a.png" % d))
		m.set_shader_parameter("normaly", load("res://obrazky/impostory/%s_n.png" % d))
		var st: Array = _imp_meta[d]["stred"]
		m.set_shader_parameter("stred", Vector3(st[0], st[1], st[2]))
		m.set_shader_parameter("polomer", float(_imp_meta[d]["polomer"]))
		m.set_shader_parameter("fade_od", STROM_PREP - 10.0)
		m.set_shader_parameter("fade_do", dohled)
		for pf: String in TINT_LISTI:
			if d.begins_with(pf):
				m.set_shader_parameter("tint", TINT_LISTI[pf])
		for bc: Vector2i in imp[d]:
			var list: Array = imp[d][bc]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_custom_data = true
			mm.mesh = quad
			mm.instance_count = list.size()
			var lo := Vector3(INF, INF, INF)
			var hi := -lo
			var o := Vector3((bc.x + 0.5) * bunka, 0.0, (bc.y + 0.5) * bunka)     # stred bunky: custom data v pul presnosti
			for i in list.size():
				var c: Color = list[i]
				c = Color(c.r - o.x, c.g, c.b - o.z, c.a)
				mm.set_instance_transform(i, Transform3D.IDENTITY)
				mm.set_instance_custom_data(i, c)
				lo = lo.min(Vector3(c.r, c.g, c.b))
				hi = hi.max(Vector3(c.r, c.g, c.b))
			var r := float(_imp_meta[d]["polomer"]) * 2.5
			mm.custom_aabb = AABB(lo - Vector3(r, r, r), hi - lo + Vector3(r, r, r) * 2.0)
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.material_override = m
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mmi.name = "%s_%s_%d_%d" % [jmeno, d, bc.x, bc.y]
			mmi.position = o
			root.add_child(mmi)
			n += list.size()
	print("%s: %d stromu" % [jmeno, n])


## Konec mapy (Misa 0.67 "konec mapy jen obrazkem - vyhled do dalky", radce 08:55): za pasmem 5 m (blender ACT) je jen
## Teren_obzor (mrizka 25 m) a zem.gdshader tam maluje les ze sumu (venku > 0) - z mapy holé olivove kopce. Na tato
## mista lesa impostory (jeden ctverec na strom, bunky 1024 m = malo volani kresleni), hustota klesa se vzdalenosti,
## dohled 2500 m (v mlze). Mimo Rostliny: testy a dosednuti po fyzice obzor nemaji (bez kolize).
const OBZ_ACT := Rect2(-250.0, -250.0, 1150.0, 1600.0)
const OBZ_PAS := 1100.0
const OBZ_BUNKA := 1024.0


func _obzor_les(root: Node3D) -> void:
	var to := _tvrz_root.find_child("Teren_obzor", true, false) as MeshInstance3D if _tvrz_root else null
	if to == null or to.mesh == null or _imp_meta.is_empty():
		return
	if sum.get_image() == null:
		await sum.changed
	var img := sum.get_image()
	if img == null:
		return
	if img.is_compressed():
		img.decompress()
	var iw := img.get_width()
	var ih := img.get_height()
	var sm := func(uv: Vector2) -> float:
		return img.get_pixel(posmod(int(uv.x * iw), iw), posmod(int(uv.y * ih), ih)).r
	# vysky obzoru: vrcholy site do mrizky 25 m
	var vy := {}
	var xf := to.global_transform if to.is_inside_tree() else to.transform
	for si in to.mesh.get_surface_count():
		for v: Vector3 in to.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
			var w := xf * v
			vy[Vector2i(roundi(w.x / 25.0), roundi(w.z / 25.0))] = w.y
	var vyska := func(x: float, z: float) -> float:
		var fx := x / 25.0
		var fz := z / 25.0
		var i := floori(fx)
		var j := floori(fz)
		var c := [vy.get(Vector2i(i, j)), vy.get(Vector2i(i + 1, j)), vy.get(Vector2i(i, j + 1)), vy.get(Vector2i(i + 1, j + 1))]
		if c.has(null):
			return INF
		fx -= i
		fz -= j
		return lerpf(lerpf(c[0], c[1], fx), lerpf(c[2], c[3], fx), fz)
	var druhy := [["smrk", 0.55], ["buk_stredni", 0.3], ["dub_stredni", 0.15]]          # 3 druhy = malo volani kresleni
	var rng := RandomNumberGenerator.new()
	rng.seed = 2500
	var imp := {}
	var n := 0
	var krok := 7.5
	var oblast := OBZ_ACT.grow(OBZ_PAS)
	var z := oblast.position.y
	while z < oblast.end.y:
		var x := oblast.position.x
		while x < oblast.end.x:
			var p := Vector2(x + rng.randf_range(-3.2, 3.2), z + rng.randf_range(-3.2, 3.2))
			x += krok
			var dv := maxf(maxf(OBZ_ACT.position.x - p.x, p.x - OBZ_ACT.end.x), maxf(OBZ_ACT.position.y - p.y, p.y - OBZ_ACT.end.y))
			if dv < 0.0:
				continue
			# tytez dva sumy jako zem.gdshader (venku): stejna mista lesa
			var nl: float = sm.call(p * 0.0021 + Vector2(0.37, 0.37)) * 0.7 + sm.call(p * 0.011 + Vector2(0.11, 0.11)) * 0.3
			var les := smoothstep(0.44, 0.56, nl)
			# hustota: u kraje plny les, dal ridsi (v mlze a pod 1 px stejne splyne s barvou zeme)
			if rng.randf() > smoothstep(0.0, 0.6, les) * lerpf(1.0, 0.45, clampf(dv / OBZ_PAS, 0.0, 1.0)):
				continue
			var y: float = vyska.call(p.x, p.y)
			if y == INF:
				continue
			var r := rng.randf()
			var d := "smrk"
			for dr: Array in druhy:
				r -= float(dr[1])
				if r <= 0.0:
					d = dr[0]
					break
			if not _imp_meta.has(d):
				continue
			var sc := rng.randf_range(1.05, 1.55)                       # dospely les, z dalky jinak "sad"
			var bc := Vector2i(floori(p.x / OBZ_BUNKA), floori(p.y / OBZ_BUNKA))
			if not imp.has(d):
				imp[d] = {}
			if not imp[d].has(bc):
				imp[d][bc] = []
			imp[d][bc].append(Color(p.x, y - 0.8, p.y, roundf(sc * 256.0) + rng.randf() * 0.999))
			n += 1
		z += krok
	var uzel := Node3D.new()
	uzel.name = "Obzor_les"
	root.add_child(uzel)
	_impostory(uzel, imp, OBZ_BUNKA, 2500.0, "obzor")


## Realie 1393 (Misa, radce 09:20): smrk v niznim udoli nerostl. Pod 25 m nad tvrzi (udoli, okoli vsi, louky)
## nahradit smrk dubohabrinou (dub, buk, lipa); na hrebenech, ve skalnim meste a jako primes (15 %) zustava.
func _skala_detail(om: BaseMaterial3D) -> Material:
	var m := ShaderMaterial.new()
	m.resource_name = om.resource_name
	m.shader = load("res://shaders/skala_detail.gdshader")
	m.set_shader_parameter("barva", om.albedo_texture)
	m.set_shader_parameter("normala", om.normal_texture)
	m.set_shader_parameter("detail", _t("skala_piskovec", "diff"))
	m.set_shader_parameter("detail_n", _t("skala_piskovec", "nor"))
	m.set_shader_parameter("detail_m", _size("skala_piskovec"))
	m.set_shader_parameter("detail_prumer", float(_albedo().get("skala_piskovec", 0.2)))   # linearni, jako textura v shaderu
	return m


func _smrky_na_listnace() -> void:
	var r: Dictionary = data["rostliny"]
	var cile := ["dub_stredni_0", "buk_stredni_0", "lipa_stredni_0", "dub_stredni_0"]
	if not cile.all(func(k: String) -> bool: return r.has(k)):
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 1393
	var n := 0
	for key: String in r.keys():
		if not key.begins_with("smrk_") or key.contains("_daleko"):
			continue
		var zustava: Array = []
		for t: Array in r[key]:
			if float(t[7]) < 25.0 and rng.randf() > 0.15:
				var cil: String = cile[rng.randi() % cile.size()]
				var k := rng.randf_range(0.8, 1.15) / maxf(Vector3(t[0], t[4], t[8]).length(), 0.01)
				var u := t.duplicate()
				for i in [0, 1, 2, 4, 5, 6, 8, 9, 10]:
					u[i] = float(t[i]) * k
				(r[cil] as Array).append(u)
				n += 1
			else:
				zustava.append(t)
		r[key] = zustava
	print("smrky v udoli nahrazeny listnaci: ", n)


var _vys := {}


## Vyska terenu z mrizky louky (trava_kraj: 2 m, cm v int16) - uz pri stavbe, pred fyzikou.
func _vyska(x: float, z: float) -> float:
	if _vys.is_empty():
		for key: String in ["trava_ves", "trava_kraj"]:
			var g: Dictionary = data.get(key, {})
			if g.is_empty():
				continue
			_vys[key] = {"x0": float(g["x0"]), "z0": float(g["z0"]), "k": float(g["k"]), "nx": int(g.get("nx", g.get("n", 0))),
					"nz": int(g.get("nz", g.get("n", 0))), "y": Marshalls.base64_to_raw(String(g["y"]))}
	# ves ma vlastni jemnejsi teren (Teren_ves, mrizka trava_ves); jinde krajina
	for key: String in ["trava_ves", "trava_kraj"]:
		if not _vys.has(key):
			continue
		var g: Dictionary = _vys[key]
		var fx := (x - float(g["x0"])) / float(g["k"])
		var fz := (z - float(g["z0"])) / float(g["k"])
		if key == "trava_ves" and (fx < 1.0 or fz < 1.0 or fx > int(g["nx"]) - 2 or fz > int(g["nz"]) - 2):
			continue
		var i := clampi(floori(fx), 0, int(g["nx"]) - 2)
		var j := clampi(floori(fz), 0, int(g["nz"]) - 2)
		fx = clampf(fx - i, 0.0, 1.0)
		fz = clampf(fz - j, 0.0, 1.0)
		var ys: PackedByteArray = g["y"]
		var nx: int = g["nx"]
		var a := ys.decode_s16((j * nx + i) * 2)
		var b := ys.decode_s16((j * nx + i + 1) * 2)
		var c := ys.decode_s16(((j + 1) * nx + i) * 2)
		var d := ys.decode_s16(((j + 1) * nx + i + 1) * 2)
		return lerpf(lerpf(a, b, fx), lerpf(c, d, fx), fz) / 100.0
	return 0.0


## Nejnizsi teren v okoli (mrizka 2 m na srazu mine skutecny teren o 1-3 m): kmen radeji zapustit nez nechat viset.
func _vyska_min(x: float, z: float, r := 2.0) -> float:
	return minf(minf(_vyska(x, z), minf(_vyska(x + r, z), _vyska(x - r, z))), minf(_vyska(x, z + r), _vyska(x, z - r)))


## Radce 17:05 bod 3 (Misa 0.69/0.70 "brizy maji bily spodek a sedy vrch"): v modelu (LOLIPOP birch pack) je spodek
## kmene do ~2 m soucasti plochy listi (atlas) - kreslil se shaderem listi (prosvit, vitr, tint) = bily, nad nim kura
## jinou texturou sedsi. Spodek se oddeli do neprusvitne kury (atlas, alfa orez) a jas obou textur se srovna.
var _briza_kmeny := {}


func _briza_kmen(mesh: Mesh) -> Mesh:
	if _briza_kmeny.has(mesh):
		return _briza_kmeny[mesh]
	var am := mesh as ArrayMesh
	if am == null or am.get_surface_count() != 2:
		return mesh
	# model s vlastnim materialem kury (briza.glb od 0.9x: briza_listi + briza_kura) uz kmen ma - prevod spodku z atlasu
	# by vzal spodek kury a dal mu material listi (Misa 0.98: zeleny plochy spodek kmene)
	for si in am.get_surface_count():
		var mt := am.surface_get_material(si)
		if mt and String(mt.resource_name).contains("kura"):
			_briza_kmeny[mesh] = mesh
			return mesh
	var kura0 := am.surface_get_material(0) as BaseMaterial3D
	var a0 := am.surface_get_arrays(0)
	var kura_y := INF
	for q: Vector3 in a0[Mesh.ARRAY_VERTEX]:
		kura_y = minf(kura_y, q.y)
	var a1 := am.surface_get_arrays(1)
	var v1: PackedVector3Array = a1[Mesh.ARRAY_VERTEX]
	var uv1: PackedVector2Array = a1[Mesh.ARRAY_TEX_UV]
	var idx: PackedInt32Array = a1[Mesh.ARRAY_INDEX] if a1[Mesh.ARRAY_INDEX] != null else PackedInt32Array(range(v1.size()))
	var spod := PackedInt32Array()
	var listi := PackedInt32Array()
	for t in range(0, idx.size(), 3):
		var hi := maxf(v1[idx[t]].y, maxf(v1[idx[t + 1]].y, v1[idx[t + 2]].y))
		if hi < kura_y + 0.4:
			spod.append_array([idx[t], idx[t + 1], idx[t + 2]])
		else:
			listi.append_array([idx[t], idx[t + 1], idx[t + 2]])
	if spod.is_empty() or kura0 == null:
		_briza_kmeny[mesh] = mesh
		return mesh
	var lm := am.surface_get_material(1)
	var atlas: Texture2D = null
	if lm is ShaderMaterial:
		atlas = (lm as ShaderMaterial).get_shader_parameter("barva")
	elif lm is BaseMaterial3D:
		atlas = (lm as BaseMaterial3D).albedo_texture
	# spodek dostane kuru kmene (stejny material) s UV dopoctenymi jako na kmeni: v podle vysky (linearni prolozeni
	# dolniho metru kmene), u podle uhlu kolem osy; atlas ma jinou, bilou kuru (Misa 0.70 "bily spodek, sedy vrch")
	var v0: PackedVector3Array = a0[Mesh.ARRAY_VERTEX]
	var uv0: PackedVector2Array = a0[Mesh.ARRAY_TEX_UV]
	var sy := 0.0
	var sv_ := 0.0
	var syy := 0.0
	var syv := 0.0
	var nn := 0
	var cx := 0.0
	var cz := 0.0
	var umin := INF
	var umax := -INF
	for q in v0.size():
		if v0[q].y < kura_y + 1.2:
			sy += v0[q].y
			sv_ += uv0[q].y
			syy += v0[q].y * v0[q].y
			syv += v0[q].y * uv0[q].y
			cx += v0[q].x
			cz += v0[q].z
			umin = minf(umin, uv0[q].x)
			umax = maxf(umax, uv0[q].x)
			nn += 1
	var ka := 0.0
	var kb := 0.0
	if nn > 3:
		ka = (nn * syv - sy * sv_) / maxf(nn * syy - sy * sy, 1e-6)
		kb = (sv_ - ka * sy) / nn
		cx /= nn
		cz /= nn
	# radce 21:35 (Misa 0.75 (-44,9) "sede desky" mezi brizami): u paty atlasu jsou i ploche karty daleko od osy
	# kmene (koreny/prizemni chomac na nepruhledne casti atlasu) - s kurou byly sede desky; jen co je u osy je kmen
	var spod2 := PackedInt32Array()
	var pryc := 0
	# Misa 0.76 "brizy maji useknuty spodek": kmen je i siroka pata - rozhoduje smer plochy: kura kmene hledi od osy
	# (normala ~ radialni), plocha karta (deska) stoji pres osu bokem (normala kolma k radialnimu smeru)
	for t in range(0, spod.size(), 3):
		var a3 := v1[spod[t]]
		var b3 := v1[spod[t + 1]]
		var c3 := (a3 + b3 + v1[spod[t + 2]]) / 3.0
		var nn3 := (b3 - a3).cross(v1[spod[t + 2]] - a3)
		var rad := Vector2(c3.x - cx, c3.z - cz)
		var n2 := Vector2(nn3.x, nn3.z)
		var radial := absf(n2.normalized().dot(rad.normalized())) if n2.length() > 1e-6 and rad.length() > 0.02 else 1.0
		if radial > 0.45:
			spod2.append_array([spod[t], spod[t + 1], spod[t + 2]])
		else:
			pryc += 1
	spod = spod2
	var uv3 := uv1.duplicate()
	for t in spod.size():
		var q2 := v1[spod[t]]
		uv3[spod[t]] = Vector2(umin + (umax - umin) * (atan2(q2.z - cz, q2.x - cx) / TAU + 0.5), ka * q2.y + kb)
	var km := kura0
	var nove := ArrayMesh.new()
	nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a0)
	nove.surface_set_material(0, kura0)
	var a2 := a1.duplicate()
	a2[Mesh.ARRAY_INDEX] = listi
	nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a2)
	nove.surface_set_material(1, lm)
	var a3 := a1.duplicate()
	a3[Mesh.ARRAY_INDEX] = spod
	a3[Mesh.ARRAY_TEX_UV] = uv3
	nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a3)
	nove.surface_set_material(2, km)
	print("briza: spodek kmene %d troj. do kury (v = %.3f y + %.3f), plochych karet u paty pryc %d" % [spod.size() / 3, ka, kb, pryc])
	_briza_kmeny[mesh] = nove
	return nove


## Radce 17:05 bod 7 (Misa 0.70: ker a kameny na ceste k domum, (474,806), (448,811)): ve vsi na cestach, navsi
## a ve dvorech (mrizka trava_ves m < 60 = bez travy, jak ji kreslil Blender) zadny ker, kamen, kmen ani bylina;
## stromy zustavaji.
var _ves_m := PackedByteArray()


## Maska trava_ves (m < 60 = bez travy, z Blenderu: stara rovna naves) podle nove ulice vsi (Misa 27. 10. foto
## z vysky: „neni videt, ze cesta jde celou vsi“ - travni koberec zdalky kryl ulici svetlym pasem, maska ji neznala).
func _ves_maska_ulice() -> void:
	var g: Dictionary = data.get("trava_ves", {})
	if g.is_empty() or not VES_OBLOUK:
		return
	var m := Marshalls.base64_to_raw(String(g["m"]))
	var n := int(g["n"])
	var k := float(g["k"])
	var x0 := float(g["x0"])
	var z0 := float(g["z0"])
	var bunek := 0
	for o: Dictionary in cesty_osy:
		if not bool(o.get("ves", false)):
			continue
		var pp: PackedVector2Array = o["p"]
		var ws: PackedFloat32Array = o["w"]
		for i in pp.size():
			var sp := float(o["s0"]) + i * 0.8
			var r := maxf(cesta_ok(ws[i], sp, 1.0), cesta_ok(ws[i], sp, -1.0))          # jizdni pas = hlina
			for j in range(floori((pp[i].y - r - z0) / k), ceili((pp[i].y + r - z0) / k) + 1):
				for ii in range(floori((pp[i].x - r - x0) / k), ceili((pp[i].x + r - x0) / k) + 1):
					if ii < 0 or j < 0 or ii >= n or j >= n:
						continue
					if Vector2(x0 + ii * k, z0 + j * k).distance_to(pp[i]) < r and m[j * n + ii] >= 60:
						m[j * n + ii] = 20
						bunek += 1
	g["m"] = Marshalls.raw_to_base64(m)
	_ves_m = PackedByteArray()
	print("ves: maska travy podle ulice, %d bunek bez travy" % bunek)


func ves_cesta(x: float, z: float) -> bool:
	var g: Dictionary = data.get("trava_ves", {})
	if g.is_empty():
		return false
	if _ves_m.is_empty():
		_ves_m = Marshalls.base64_to_raw(String(g["m"]))
	var n := int(g["n"])
	var i := roundi((x - float(g["x0"])) / float(g["k"]))
	var j := roundi((z - float(g["z0"])) / float(g["k"]))
	if i < 1 or j < 1 or i >= n - 1 or j >= n - 1:
		return false
	# i soused (kousek kere pres okraj cesty)
	for dj in range(-1, 2):
		for di in range(-1, 2):
			if _ves_m[(j + dj) * n + i + di] < 60:
				return true
	return false


func _ves_cesty_volne() -> void:
	var r: Dictionary = data["rostliny"]
	var pryc := 0
	for key: String in r.keys():
		if _strom_tvar(key.split("_daleko")[0].substr(0, key.split("_daleko")[0].rfind("_"))) != "" or key.begins_with("skala_"):
			continue
		var zust: Array = []
		for t: Array in r[key]:
			if ves_cesta(float(t[3]), float(t[11])):
				pryc += 1
			else:
				zust.append(t)
		r[key] = zust
	print("ves: z cest a dvoru pryc %d (kere, kameny, byliny)" % pryc)


## Radce 08:05, Misa 0.66 ("kere ploche, ridke"): fotoskeny shrub_02 a bushcover (ker_husty) -> kulaty ker z karet
## (blender/stromy.py ker_kulaty, bush.glb z Misova Disku), 3 velikosti; poloha a otoceni zustava, vyska 0,7-1,3x.
func _kere_kulate() -> void:
	var r: Dictionary = data["rostliny"]
	if not ResourceLoader.exists(MOD + "rostliny/ker_kulaty.glb"):
		return
	for v in 3:
		if not r.has("ker_kulaty_%d" % v):
			r["ker_kulaty_%d" % v] = []
	var n := 0
	for k: String in ["shrub_02_0", "shrub_02_1", "ker_husty_0"]:
		if not r.has(k):
			continue
		for t: Array in r[k]:
			var x: float = t[3]
			var z: float = t[11]
			var h := fposmod(sin(x * 12.9898 + z * 78.233) * 43758.5453, 1.0)
			var v := 0 if h < 0.5 else (1 if h < 0.75 else 2)
			(r["ker_kulaty_%d" % v] as Array).append(_xf(x, float(t[7]) - 0.05, z, atan2(-float(t[8]), float(t[0])), lerpf(0.7, 1.3, fmod(h * 7.0, 1.0))))
			n += 1
		r[k] = []
	print("kere kulate: %d (shrub_02, bushcover)" % n)


func _xf(x: float, y: float, z: float, yaw: float, sc: float, nakl := Vector3.ZERO) -> Array:
	var bs := Basis(Vector3.UP, yaw).rotated(Vector3.RIGHT, nakl.x).rotated(Vector3.FORWARD, nakl.z).scaled(Vector3.ONE * sc)
	return [bs.x.x, bs.y.x, bs.z.x, x, bs.x.y, bs.y.y, bs.z.y, y, bs.x.z, bs.y.z, bs.z.z, z]


## Skalni mesto (radce 09:05): vez nestoji na travniku - u paty sut odpadlych bloku zapadana do zeme, mezi nimi
## kapradi, mech a borůvčí (kerik), v okoli borovice, smrk a briza (les mezi vezemi). Pridava do stavajicich druhu.
func _skalni_mesto() -> void:
	var r: Dictionary = data["rostliny"]
	var need := ["balvan_piskovec_2_0", "kamen_piskovec_1_0", "kamen_piskovec_2_0", "kapradi_1_0", "kapradi_2_0", "kapradi_3_0",
			"mech_1_0", "shrub_02_0", "borovice_0", "smrk_0", "briza_0"]
	for k: String in need:
		if not r.has(k):
			return
	var rng := RandomNumberGenerator.new()
	rng.seed = 7313
	var n := 0
	for key: String in r.keys():
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var ps: PackedScene = load("res://modely/rostliny/%s.glb" % key.trim_suffix("_0"))
		if ps == null:
			continue
		var inst := ps.instantiate()
		var bb := AABB()
		for m in inst.find_children("*", "MeshInstance3D", true, false):
			bb = bb.merge((m as MeshInstance3D).get_aabb())
		inst.free()
		var r0 := maxf(bb.size.x, bb.size.z) * 0.5
		for t: Array in r[key]:
			var sc := Vector3(t[0], t[4], t[8]).length()
			var c := Vector2(t[3], t[11])
			var rad := r0 * sc
			# sut: 5 bloku a kamenu u paty, zapadane 25-40 %
			for q in 5:
				var a := rng.randf() * TAU
				var d := rad * rng.randf_range(0.85, 1.25)
				var p := c + Vector2(cos(a), sin(a)) * d
				var velky := q == 0
				var s2 := rng.randf_range(0.6, 1.1) if velky else rng.randf_range(0.5, 1.4)
				var kind := "balvan_piskovec_2_0" if velky else ("kamen_piskovec_1_0" if rng.randf() < 0.6 else "kamen_piskovec_2_0")
				(r[kind] as Array).append(_xf(p.x, _vyska(p.x, p.y) - s2 * rng.randf_range(0.2, 0.4), p.y, rng.randf() * TAU, s2,
						Vector3(rng.randf_range(-0.3, 0.3), 0, rng.randf_range(-0.3, 0.3))))
				n += 1
			# kapradi, mech a kerik mezi sutí
			for q in 7:
				var a := rng.randf() * TAU
				var p := c + Vector2(cos(a), sin(a)) * rad * rng.randf_range(0.9, 1.6)
				var kind: String = ["kapradi_1_0", "kapradi_2_0", "kapradi_3_0", "kapradi_1_0", "mech_1_0", "mech_1_0", "shrub_02_0"][q]
				var s2 := rng.randf_range(0.04, 0.09) if kind.begins_with("mech") else rng.randf_range(0.7, 1.3)
				(r[kind] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.05, p.y, rng.randf() * TAU, s2))
				n += 1
			# les mezi vezemi: jeden strom u kazde veze (borovice, smrk v chladne souteske, briza na svetline)
			var a := rng.randf() * TAU
			var p := c + Vector2(cos(a), sin(a)) * rad * rng.randf_range(1.6, 2.6)
			var u := rng.randf()
			var kind := "borovice_0" if u < 0.5 else ("smrk_0" if u < 0.8 else "briza_0")
			var ref: Array = (r[kind] as Array)[0]
			var s0 := Vector3(ref[0], ref[4], ref[8]).length()
			(r[kind] as Array).append(_xf(p.x, _vyska_min(p.x, p.y) - 0.15, p.y, rng.randf() * TAU, s0 * rng.randf_range(0.8, 1.2)))
			n += 1
	print("skalni mesto: pridano ", n, " kamenu, rostlin a stromu")


## Les neni park (radce 09:05 C): u stromu parezy, spadle vetve, keriky (lesni patro). Kazdy 5. strom pare nebo
## vetve, kazdy 3. kerik (sipek, ker) v okoli; meritka podle prvni instance druhu (tak jak je model navrzeny).
func _lesni_patro() -> void:
	var r: Dictionary = data["rostliny"]
	var drevo := ["tree_stump_01_0", "tree_stump_02_0", "dry_branches_medium_01_0", "dry_branches_medium_01_1", "dry_branches_medium_01_2"]
	var kere: Array = ["shrub_02_0", "sipek_0"].filter(func(k: String) -> bool: return r.has(k) and not (r[k] as Array).is_empty())
	for k: String in drevo:
		if not r.has(k) or (r[k] as Array).is_empty():
			return
	if kere.is_empty():
		return
	var mer := {}
	for k: String in drevo + kere:
		var t: Array = r[k][0]
		mer[k] = Vector3(t[0], t[4], t[8]).length()
	var rng := RandomNumberGenerator.new()
	rng.seed = 404
	var n := 0
	for key: String in r.keys():
		var lesni := false
		for d: String in ["dub_", "buk_", "lipa_", "smrk_", "borovice_", "olse_", "briza_"]:
			if key.begins_with(d) and not key.contains("_daleko"):
				lesni = true
		if not lesni:
			continue
		var i := 0
		# jen stromy z dat a skalniho mesta (nove lesy a doplneni lesa pridavaji na konec seznamu - patro by houstlo s nimi)
		for t: Array in (r[key] as Array).slice(0, int(_stromy_6a.get(key, (r[key] as Array).size()))):
			i += 1
			if i % 5 == 0:
				var k: String = drevo[rng.randi() % drevo.size()]
				var a := rng.randf() * TAU
				var p := Vector2(t[3], t[11]) + Vector2(cos(a), sin(a)) * rng.randf_range(2.0, 6.0)
				if not druh_smi_hra(k, p.x, p.y):
					continue                                # parez ani vetev ne na ceste, ve vstupu, ve vode
				(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.05, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.8, 1.3)))
				n += 1
			if i % 2 == 0:
				var k: String = kere[rng.randi() % kere.size()]
				var a := rng.randf() * TAU
				var p := Vector2(t[3], t[11]) + Vector2(cos(a), sin(a)) * rng.randf_range(3.0, 7.0)
				if not druh_smi_hra(k, p.x, p.y):
					continue                                # druhy.json vyjma (ker ne uprostred louky)
				(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.05, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.7, 1.3)))
				n += 1
	print("lesni patro: pridano ", n, " parezu, vetvi a keru")


## Huste lesy misto neudrzovanych luk (Misa 0.64: "mame strasne luk, spis huste... fakt huste lesy lemovane keri,
## cesta skrz les, kde stromy maji vetve nad cestou jako v KCD2"). Na neudrzovane louce (divokost > 0,55, mimo kosene
## okoli tvrze a vsi) velke celky lesa ze sumu (~55 % plochy), stromy po 6 m s posunem, okraj 6-10 m keri (sipek, bez,
## husty ker); pesiny lesem zustanou volne 3,5 m od osy (vlnena osa jako _pes_postav) - stromy podel nich pridava
## _les_hustsi, koruny se nad pesinou sejdou. Jehlicnany jen nad 25 m (pravidlo 1393), jinak listnace.
func _nove_lesy() -> void:
	var r: Dictionary = data["rostliny"]
	var g: Dictionary = data["trava_kraj"]
	var obl := Rect2(float(g["x0"]), float(g["z0"]), int(g["nx"]) * float(g["k"]), int(g["nz"]) * float(g["k"]))
	var listn: Array = []
	var jehl: Array = []
	for k: String in ["buk_stredni_0", "dub_stredni_0", "lipa_stredni_0", "briza_0", "briza_1", "briza_2", "dub_stary_0"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			listn.append(k)
	for k: String in ["smrk_0", "smrk_1", "smrk_2", "borovice_0"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			jehl.append(k)
	if listn.is_empty():
		return
	var sc_ref := {}
	for k: String in listn + jehl:
		var t: Array = r[k][0]
		sc_ref[k] = Vector3(t[0], t[4], t[8]).length()
	# osy pesin (vlnene jako _pes_postav) do mrizky 8 m
	var pes := {}
	var sg := pes_useky()
	for si in sg.size():
		var a := Vector2(sg[si].x, sg[si].y)
		var b := Vector2(sg[si].z, sg[si].w)
		var dl := a.distance_to(b)
		var dr := (b - a) / maxf(dl, 0.01)
		for m in int(dl / 2.0) + 1:
			var x := minf(m * 2.0, dl)
			var q := a + dr * x + dr.orthogonal() * _pes_o(x, dl, si) * _brod_tlum(a + dr * x)
			var cc := Vector2i(floori(q.x / 8.0), floori(q.y / 8.0))
			if not pes.has(cc):
				pes[cc] = []
			(pes[cc] as Array).append(q)
	var pes_blizko := func(q: Vector2, d: float) -> bool:
		var c0 := Vector2i(floori(q.x / 8.0), floori(q.y / 8.0))
		for dx in range(-1, 2):
			for dz in range(-1, 2):
				for w: Vector2 in pes.get(c0 + Vector2i(dx, dz), []):
					if w.distance_to(q) < d:
						return true
		return false
	# stavajici stromy (mrizka 6 m) - novy les se neprekryva se starym
	var stare := {}
	for key: String in r:
		for pf: String in LISTNACE + JEHLICNATE:
			if key.begins_with(pf) and not key.contains("_daleko"):
				for t: Array in r[key]:
					stare[Vector2i(floori(float(t[3]) / 6.0), floori(float(t[11]) / 6.0))] = true
	var ns := FastNoiseLite.new()
	ns.seed = 6411
	ns.frequency = 0.006
	ns.fractal_octaves = 3
	var nd := FastNoiseLite.new()
	nd.seed = 77
	nd.frequency = 0.02
	var rng := RandomNumberGenerator.new()
	rng.seed = 6412
	var nt := 0
	var nk := 0
	var y := obl.position.y
	while y < obl.end.y:
		var x := obl.position.x
		while x < obl.end.x:
			var p := Vector2(x, y) + Vector2(rng.randf_range(-2.0, 2.0), rng.randf_range(-2.0, 2.0))
			x += 5.0
			var div := divokost(p.x, p.y)
			if div < 0.4 or _louka_m(p.x, p.y) < 0.5:
				continue
			var v := ns.get_noise_2d(p.x, p.y) * 0.5 + 0.5 + (div - 0.7) * 0.3
			if v < 0.4:
				continue
			if stare.has(Vector2i(floori(p.x / 6.0), floori(p.y / 6.0))) or _u_mostu(p.x, p.y):
				continue
			if pes_blizko.call(p, 3.5) or not smi_tu_byt(p.x, p.y, "strom") or sklon_bunky(p.x, p.y) > 0.9:
				continue
			var hy := _vyska(p.x, p.y)
			if hy < float(data.get("voda_y", -2.75)) + 0.5:
				continue
			if koryto and not koryto.blizko(p.x, p.y).is_empty() and koryto.strop(p.x, p.y, false) < hy + 1.5:
				continue                                  # zarez potoka
			if v < 0.48:
				# okraj lesa: husty lem keru (Misa: "vstupy do lesu a lemy cest jsou predevsim kere, huste")
				for _j in rng.randi_range(3, 6):
					var q := p + Vector2(rng.randf_range(-2.5, 2.5), rng.randf_range(-2.5, 2.5))
					if pes_blizko.call(q, 2.5):
						continue
					var kk: String = ["ker_husty_0", "sipek_0", "sipek_2", "ker_husty_0", "ker_husty_0"][rng.randi() % 5]
					if not r.has(kk) or (r[kk] as Array).is_empty():
						continue
					var s0 := 1.0 if kk.begins_with("ker_husty") else Vector3(r[kk][0][0], r[kk][0][4], r[kk][0][8]).length()
					(r[kk] as Array).append(_xf(q.x, _vyska(q.x, q.y) - 0.06, q.y, rng.randf() * TAU, s0 * rng.randf_range(0.7, 1.3)))
					nk += 1
				continue
			var jeh := hy > 25.0 and not jehl.is_empty() and nd.get_noise_2d(p.x, p.y) > -0.2
			var k: String = jehl[rng.randi() % jehl.size()] if jeh else listn[rng.randi() % listn.size()]
			(r[k] as Array).append(_xf(p.x, hy - 0.1, p.y, rng.randf() * TAU, float(sc_ref[k]) * rng.randf_range(0.75, 1.15)))
			nt += 1
		y += 5.0
	print("nove lesy: stromu %d, keru na okraji %d" % [nt, nk])


## Lesni plast (Misa 0.64: "kraje lesu vsude jsou plne keru, dle reality"): prechod les - louka je v prirode pas
## 5-15 m - zevne bylinny lem (kopriva, vysoka bylina), pak husty kerovy plast (sipek, bez, liska/husty ker), uvnitr
## mlade stromy. Pro VSECHNY okraje lesa (i z Blenderu): kraj = misto bez zapoje (< 0,35), ale do 8 m zapoj > 0,6.
## Mrizka 2,5 m; plast ~ 75 % bodu, lem 30 %. Mimo pesiny, vodu, most, tvrz a ves.
func _lesni_plast() -> void:
	var r: Dictionary = data["rostliny"]
	var kere: Array = []
	# jen lehke kere (ker_husty 382, sipek 650 troj.; bez a shrub_02 maji i po zjednoduseni 2-3 tisice)
	for k: String in ["ker_husty_0", "ker_husty_0", "ker_husty_0", "sipek_0", "sipek_1", "sipek_2"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			kere.append(k)
	if kere.is_empty() or _st_ch.is_empty():
		return
	var mlade: Array = []
	for k: String in ["buk_stredni_0", "lipa_stredni_0", "briza_0", "briza_1", "olse_mlada_0"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			mlade.append(k)
	var rng := RandomNumberGenerator.new()
	rng.seed = 6414
	var nk := 0
	var nl := 0
	var nm := 0
	var K := 2.5
	# hruba mrizka 10 m: jen bunky, kde se les a bezlesi potkavaji (jinak 9 cteni masky na kazdy bod 2,5 m)
	var t0 := Time.get_ticks_msec()
	var kraj := {}
	var gy := stan_rect.position.y
	while gy < stan_rect.end.y:
		var gx := stan_rect.position.x
		while gx < stan_rect.end.x:
			var lo := 1.0
			var hi := 0.0
			for o: Vector2 in [Vector2(0, 0), Vector2(10, 0), Vector2(0, 10), Vector2(10, 10), Vector2(5, 5)]:
				var lv := _les(gx + o.x, gy + o.y)
				lo = minf(lo, lv)
				hi = maxf(hi, lv)
			if hi > 0.5 and lo < 0.45:
				for dx in range(-1, 2):
					for dz in range(-1, 2):
						kraj[Vector2i(floori(gx / 10.0) + dx, floori(gy / 10.0) + dz)] = true
			gx += 10.0
		gy += 10.0
	var y := stan_rect.position.y
	while y < stan_rect.end.y:
		var x := stan_rect.position.x
		while x < stan_rect.end.x:
			if not kraj.has(Vector2i(floori(x / 10.0), floori(y / 10.0))):
				x += K
				continue
			var p := Vector2(x, y) + Vector2(rng.randf_range(-1.0, 1.0), rng.randf_range(-1.0, 1.0)) * K * 0.45
			x += K
			var l := _les(p.x, p.y)
			if l > 0.6:
				continue
			var mx := 0.0
			for o: Vector2 in [Vector2(6, 0), Vector2(-6, 0), Vector2(0, 6), Vector2(0, -6), Vector2(4.2, 4.2), Vector2(-4.2, 4.2), Vector2(4.2, -4.2), Vector2(-4.2, -4.2)]:
				mx = maxf(mx, _les(p.x + o.x, p.y + o.y))
			if mx < 0.6:
				continue
			if absf(p.x + 4.0) < 80.0 and absf(p.y) < 75.0 or Vector2(p.x - 470.0, p.y - 830.0).length() < 140.0:
				continue
			if pes_d(p.x, p.y) < 1.8 or _u_mostu(p.x, p.y) or not smi_tu_byt(p.x, p.y, "ker") or sklon_bunky(p.x, p.y) > 0.9:
				continue
			var hy := _vyska(p.x, p.y)
			if hy < float(data.get("voda_y", -2.75)) + 0.4:
				continue
			var u := rng.randf()
			if l > 0.35:
				# vnitrni okraj: mlady strom (podrost) nebo ker
				if u < 0.3 and not mlade.is_empty():
					var km: String = mlade[rng.randi() % mlade.size()]
					var sm := Vector3(r[km][0][0], r[km][0][4], r[km][0][8]).length()
					(r[km] as Array).append(_xf(p.x, hy - 0.08, p.y, rng.randf() * TAU, sm * rng.randf_range(0.25, 0.5)))
					nm += 1
					continue
				if u > 0.6:
					continue
			elif l < 0.12:
				# zevni lem: kopriva / vysoka bylina, obcas ker
				# (kopriva ma i po zjednoduseni 1-1,5 tisice troj. - 25 000 kusu bylo moc; lem = kapradi a ker)
				if u < 0.3 and r.has("kapradi_les_0"):
					for _j in rng.randi_range(1, 3):
						var q := p + Vector2(rng.randf_range(-0.8, 0.8), rng.randf_range(-0.8, 0.8))
						(r["kapradi_les_0"] as Array).append(_xf(q.x, _vyska(q.x, q.y) - 0.03, q.y, rng.randf() * TAU, 1.0))
						nl += 1
				if u > 0.45:
					continue
			elif u > 0.8:
				continue
			var k: String = kere[rng.randi() % kere.size()]
			var s0 := 1.0 if k.begins_with("ker_husty") else Vector3(r[k][0][0], r[k][0][4], r[k][0][8]).length()
			(r[k] as Array).append(_xf(p.x, hy - 0.06, p.y, rng.randf() * TAU, s0 * rng.randf_range(0.7, 1.35)))
			nk += 1
		y += K
	print("lesni plast: keru %d, mladych stromu %d, kapradi v lemu %d (%d ms)" % [nk, nm, nl, Time.get_ticks_msec() - t0])


## Kere podel pesin v lese a na jeho okraji (Misa 0.64: "lemy cest jsou predevsim kere a huste"): po ose pesiny
## kazde 3 m na obe strany 1,8-3,2 m od osy ker (70 %), kde je les nebo jeho okraj (zapoj v okoli 8 m).
func _kere_podel_pesin() -> void:
	var r: Dictionary = data["rostliny"]
	var kere: Array = []
	for k: String in ["ker_husty_0", "sipek_0", "sipek_1", "ker_husty_0"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			kere.append(k)
	if kere.is_empty():
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 6413
	var n := 0
	var osa := pes_osa
	for i in range(1, osa.size() - 1):
		var a := osa[i - 1]
		var b := osa[i + 1]
		if a == Vector2.INF or b == Vector2.INF or osa[i] == Vector2.INF or i % 2 == 1:
			continue
		var p := osa[i]
		var lz := maxf(maxf(_les(p.x, p.y), _les(p.x + 8.0, p.y)), maxf(_les(p.x - 8.0, p.y), maxf(_les(p.x, p.y + 8.0), _les(p.x, p.y - 8.0))))
		if lz < 0.25 or absf(p.x + 4.0) < 75.0 and absf(p.y) < 70.0:
			continue
		var bok := (b - a).normalized().orthogonal()
		for sd: float in [-1.0, 1.0]:
			# Misa 0.87 „pravidelne“: jen v usecich (pomaly sum podel pesiny), ne kazdy druhy bod obe strany
			if rng.randf() > 0.45 or _vln(float(i) * 0.09 + sd * 3.1) < 0.1:
				continue
			var q := p + bok * sd * rng.randf_range(1.8, 5.0) * pes_f[i] + (b - a).normalized() * rng.randf_range(-1.0, 1.0)
			if pes_d(q.x, q.y) < 1.5 or _u_mostu(q.x, q.y) or not smi_tu_byt(q.x, q.y, "ker"):
				continue
			var k: String = kere[rng.randi() % kere.size()]
			var s0 := 1.0 if k.begins_with("ker_husty") else Vector3(r[k][0][0], r[k][0][4], r[k][0][8]).length()
			(r[k] as Array).append(_xf(q.x, _vyska(q.x, q.y) - 0.06, q.y, rng.randf() * TAU, s0 * rng.randf_range(0.75, 1.3)))
			n += 1
	print("kere podel pesin: %d" % n)


## Lesni puda (0.63 LES, Misa: "chybi kere, huste lesy"; KCD reference 3-5: kapradi a kere mezi kmeny):
## kolem lesnich stromu v lese (stanoviste) shluky kapradi (3-7 kusu na 1-2 m) a husty nizky ker; ne na pesine.
## Modely z Misova Disku (blender/stromy.py ker_husty, kapradi_les; CC-BY).
func _lesni_puda() -> void:
	var r: Dictionary = data["rostliny"]
	var kap := ["kapradi_les_0", "kapradi_les_1"]
	# Misa 0.63 (Disk Modely/Rostliny): kapradi fern_02 a vlastovicnik (Poly Haven) i do lesa, ne jen ke skalam a hradbam
	for k: String in ["kapradi_1_0", "kapradi_2_0", "kapradi_3_0", "fern_02_0", "fern_02_1", "celandine_01_0", "celandine_01_1"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			kap.append(k)
	for k: String in ["kapradi_les_0", "kapradi_les_1", "ker_husty_0"]:
		if not ResourceLoader.exists(MOD + "rostliny/%s.glb" % k.substr(0, k.rfind("_"))):
			return
		if not r.has(k):
			r[k] = []
	var mer := {}
	for k: String in kap:
		mer[k] = 1.0 if k.begins_with("kapradi_les") else Vector3(r[k][0][0], r[k][0][4], r[k][0][8]).length()
	var rng := RandomNumberGenerator.new()
	rng.seed = 7171
	var nk := 0
	var nb := 0
	var stromy: Array = []
	for key: String in r.keys():
		for d: String in ["dub_", "buk_", "lipa_", "smrk_", "borovice_", "briza_"]:
			if key.begins_with(d) and not key.contains("_daleko"):
				stromy.append(key)
	for key: String in stromy:
		var i := 0
		for t: Array in r[key]:
			i += 1
			var q := Vector2(t[3], t[11])
			if _les(q.x, q.y) < 0.35:
				continue
			# shluk kapradi (u kazdeho druheho stromu), v listnatem lese vic
			if i % 2 == 0:
				var a := rng.randf() * TAU
				var c := q + Vector2(cos(a), sin(a)) * rng.randf_range(1.5, 5.0)
				var k: String = kap[rng.randi() % kap.size()]
				for _j in rng.randi_range(3, 7):
					var p := c + Vector2(rng.randf_range(-1.6, 1.6), rng.randf_range(-1.6, 1.6))
					if pes_d(p.x, p.y) < 1.6 or _u_mostu(p.x, p.y) or not smi_tu_byt(p.x, p.y, k):
						continue
					(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.03, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.7, 1.3)))
					nk += 1
			# husty ker (u kazdeho tretiho), 2-6 m od kmene
			if i % 3 == 1:
				var a := rng.randf() * TAU
				var p := q + Vector2(cos(a), sin(a)) * rng.randf_range(2.0, 6.0)
				if pes_d(p.x, p.y) < 2.2 or _u_mostu(p.x, p.y) or not smi_tu_byt(p.x, p.y, "ker_husty"):
					continue
				(r["ker_husty_0"] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.08, p.y, rng.randf() * TAU, rng.randf_range(0.7, 1.4)))
				nb += 1
	print("lesni puda: kapradi %d, kere %d" % [nk, nb])


## Kvetiny na louce (0.63, Misa: "mely by tam byt i byliny"; bush_daisies z Disku bez slunecnice, blender/kvety.py):
## shluky kopretin a bilych kvetu (5-14 kusu na 1,5 m) po louce mimo les, cesty a vodu; jen zblizka (PODROST).
func _kvetiny_louky() -> void:
	var r: Dictionary = data["rostliny"]
	for k: String in ["kopretiny_0", "kvety_bile_0"]:
		if not ResourceLoader.exists(MOD + "rostliny/%s.glb" % k.trim_suffix("_0")):
			return
		if not r.has(k):
			r[k] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 5150
	var n := 0
	var shluku := int(stan_rect.size.x * stan_rect.size.y / 900.0)
	for _i in shluku:
		var c := stan_rect.position + Vector2(rng.randf(), rng.randf()) * stan_rect.size
		if _louka_m(c.x, c.y) < 0.6 or _les(c.x, c.y) > 0.1 or pes_d(c.x, c.y) < 2.5 or _u_mostu(c.x, c.y):
			continue
		# byliny louky (Misa: "mely by tam byt i byliny"): kopretiny, bile kvety, pampelisky (Disk Rostliny, Poly Haven)
		var w := rng.randf()
		var k := "kopretiny_0" if w < 0.45 else ("kvety_bile_0" if w < 0.7 else "dandelion_01_%d" % (rng.randi() % 5))
		if not r.has(k) or (r[k] as Array).is_empty():
			k = "kopretiny_0"
		# meritko modelu z exportu (pampeliska ma v svet.json sve), nove kvetiny 1
		var sc0 := 1.0 if (r[k] as Array).is_empty() or k.begins_with("kopret") or k.begins_with("kvety") \
				else Vector3(r[k][0][0], r[k][0][4], r[k][0][8]).length()
		for _j in rng.randi_range(5, 14):
			var a := rng.randf() * TAU
			var p := c + Vector2(cos(a), sin(a)) * sqrt(rng.randf()) * 1.5
			if not smi_tu_byt(p.x, p.y, k):
				continue
			(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.02, p.y, rng.randf() * TAU, sc0 * rng.randf_range(0.8, 1.25)))
			n += 1
	print("kvetiny louky: %d kusu, %d shluku zkuseno" % [n, shluku])


## Byliny (0.64, vetev assets: radce 10:00 BYLINY, pravidla_sveta.json): jitrocel a podbel na kraji pesin (seslapana
## hlina), pelynek na neudrzovane louce (uhor, mez), divizna na vyslunenych strmych strachach; shluky 2-6, jen zblizka.
func _byliny_rozsev() -> void:
	var r: Dictionary = data["rostliny"]
	if not ResourceLoader.exists(MOD + "rostliny/byliny.glb"):
		return
	for i in 4:
		if not r.has("byliny_%d" % i):
			r["byliny_%d" % i] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 6464
	var n := [0, 0, 0, 0]
	for _i in int(stan_rect.size.x * stan_rect.size.y / 120.0):
		var c := stan_rect.position + Vector2(rng.randf(), rng.randf()) * stan_rect.size
		if _les(c.x, c.y) > 0.3 or _u_mostu(c.x, c.y):
			continue
		var pd := pes_d(c.x, c.y)
		var k := -1
		if pd > 0.7 and pd < 1.8:
			k = 1 if rng.randf() < 0.6 else 3                  # jitrocel / podbel u pesiny
		elif divokost(c.x, c.y) > 0.5 and _louka_m(c.x, c.y) > 0.5 and rng.randf() < 0.25:
			k = 2                                              # pelynek na uhoru
		elif sklon_bunky(c.x, c.y) > 0.35 and sklon_bunky(c.x, c.y) < 1.0 and rng.randf() < 0.5:
			k = 0                                              # divizna na strani
		if k < 0:
			continue
		var key := "byliny_%d" % k
		for _j in rng.randi_range(2, 6):
			var p := c + Vector2(rng.randf_range(-0.8, 0.8), rng.randf_range(-0.8, 0.8))
			if pes_d(p.x, p.y) < 0.6 or not smi_tu_byt(p.x, p.y, key):
				continue
			(r[key] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.02, p.y, rng.randf() * TAU, rng.randf_range(0.75, 1.25)))
			n[k] += 1
	print("byliny: divizna %d, jitrocel %d, pelynek %d, podbel %d" % n)


## Strom ani ker neroste z balvanu (Misa 0.63: strom skrz balvan): pudorysny kruh kazdeho balvanu a kamene
## (meritko x pul sirky modelu) - stromy, mlade stromy a kere uvnitr 85 % polomeru pryc. Mrizka 8 m.
func _stromy_mimo_balvany() -> void:
	var r: Dictionary = data["rostliny"]
	var mriz := {}
	var nb := 0
	for k: String in r.keys():
		if not (k.begins_with("balvan_") or k.begins_with("kamen_zula") or k.begins_with("kamen_piskovec") or k.begins_with("kamen_droba")) \
				or k.contains("_daleko") or (r[k] as Array).is_empty():
			continue
		var sit := _skala_sit(k)
		if sit == null:
			continue
		var bb := sit.get_aabb()
		var pul := maxf(bb.size.x, bb.size.z) * 0.5
		for t: Array in r[k]:
			var rad := Vector3(t[0], t[4], t[8]).length() * pul
			if rad < 0.4:
				continue
			var c := Vector2i(floori(float(t[3]) / 8.0), floori(float(t[11]) / 8.0))
			if not mriz.has(c):
				mriz[c] = []
			(mriz[c] as Array).append(Vector3(t[3], t[11], rad))
			nb += 1
	var pryc := 0
	for k: String in r.keys():
		var strom := k.begins_with("shrub") or k.begins_with("sipek") or k.begins_with("bez_") or k.begins_with("ker_husty")
		for pf: String in LISTNACE + JEHLICNATE:
			if k.begins_with(pf):
				strom = true
		if not strom:
			continue
		var zust: Array = []
		for t: Array in r[k]:
			var x := float(t[3])
			var z := float(t[11])
			var c := Vector2i(floori(x / 8.0), floori(z / 8.0))
			var ven := false
			for dj in range(-1, 2):
				for di in range(-1, 2):
					for b: Vector3 in mriz.get(c + Vector2i(di, dj), []):
						if Vector2(x - b.x, z - b.y).length() < b.z * 0.85:
							ven = true
							break
					if ven:
						break
				if ven:
					break
			if not ven:
				zust.append(t)
		pryc += (r[k] as Array).size() - zust.size()
		r[k] = zust
	print("stromy z balvanu pryc: %d (balvanu %d)" % [pryc, nb])


## Hustsi les (0.63, Misa: "chybi kere, huste lesy, cesticky pres les kryte z vrchu stromy"; reference KCD):
## 1) podrost - u kazdeho druheho lesniho stromu mlady strom tehoz druhu (meritko 0,25-0,5, 3-7 m od nej);
## 2) pesiny lesem: kazdych 5-9 m po obou stranach strom 2,2-4,5 m od osy (koruny se nad pesinou sejdou),
##    jehlicnan kde prevazuje jehlicnaty porost. Pote _pesiny_volne (nic do 1,2 m od osy) a _kmeny.
func _les_hustsi() -> void:
	var r: Dictionary = data["rostliny"]
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	var listn: Array = []
	var jehl: Array = []
	for k: String in ["buk_stredni_0", "dub_stredni_0", "lipa_stredni_0", "briza_0", "briza_1", "briza_2", "briza_3"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			listn.append(k)
	for k: String in ["smrk_0", "smrk_1", "smrk_2", "borovice_0"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			jehl.append(k)
	if listn.is_empty() or jehl.is_empty():
		return
	var sc_ref := {}
	for k: String in listn + jehl:
		var t: Array = r[k][0]
		sc_ref[k] = Vector3(t[0], t[4], t[8]).length()
	# 1) podrost
	var n_mlade := 0
	for key: String in r.keys():
		if key.contains("_daleko") or not (listn.has(key) or jehl.has(key)):
			continue
		var i := 0
		for t: Array in (r[key] as Array).duplicate():
			i += 1
			if i % 2 != 0 or _les(float(t[3]), float(t[11])) < 0.3:
				continue
			var a := rng.randf() * TAU
			var p := Vector2(t[3], t[11]) + Vector2(cos(a), sin(a)) * rng.randf_range(3.0, 7.0)
			if pes_d(p.x, p.y) < 2.0 or not smi_tu_byt(p.x, p.y, key) or _u_mostu(p.x, p.y):
				continue
			(r[key] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.1, p.y, rng.randf() * TAU, float(sc_ref[key]) * rng.randf_range(0.25, 0.5)))
			n_mlade += 1
	# 2) stromoradi podel pesin v lese
	var n_pes := 0
	var osa := pes_osa
	for si in osa.size() - 1:
		var a2 := osa[si]
		var b2 := osa[si + 1]
		if a2 == Vector2.INF or b2 == Vector2.INF:
			continue
		var dl := a2.distance_to(b2)
		var nrm := (b2 - a2).normalized().orthogonal()
		var t2 := rng.randf_range(0.0, 5.0)
		while t2 < dl:
			var o := a2.lerp(b2, t2 / dl)
			t2 += rng.randf_range(5.0, 9.0)
			if _les(o.x, o.y) < 0.25 or absf(o.x + 4.0) < 60.0 and absf(o.y) < 60.0:
				continue
			for sg: float in [1.0, -1.0]:
				var q := o + nrm * sg * rng.randf_range(2.2, 4.5) * pes_f[si]
				if pes_d(q.x, q.y) < 2.0 or not smi_tu_byt(q.x, q.y, "strom") or _u_mostu(q.x, q.y):
					continue
				var kk: String = (jehl if _st(0, q.x, q.y) > _st(1, q.x, q.y) else listn)[rng.randi() % (jehl.size() if _st(0, q.x, q.y) > _st(1, q.x, q.y) else listn.size())]
				(r[kk] as Array).append(_xf(q.x, _vyska(q.x, q.y) - 0.1, q.y, rng.randf() * TAU, float(sc_ref[kk]) * rng.randf_range(0.8, 1.2)))
				n_pes += 1
	print("les hustsi: mladych stromu %d, stromu podel pesin %d" % [n_mlade, n_pes])


## Most a najezdy bez stromu a keru (Misa 0.62: "strom roste skrz zabradli" - ker nebo mlady strom z pozdejsiho
## rozsevu, lesni patro, les hustsi): posledni pruchod po vsech rozsevech; most a najezdy (14 m) v sirce mostu + 4 m
## (stromy + 7 m, koruna nad zabradli), vcetne vzdalenych verzi (stejne misto).
func _most_bez_stromu() -> void:
	if _najezdy.size() < 2:
		return
	var a: Vector2 = _najezdy[0][0]
	var b: Vector2 = _najezdy[1][0]
	var c := (a + b) * 0.5
	var osa: Vector2 = _najezdy[0][1]
	var bok: Vector2 = _najezdy[0][2]
	var pul := a.distance_to(b) * 0.5 + NAJEZD_DELKA
	var sir := float(_najezdy[0][3])
	var r: Dictionary = data["rostliny"]
	var pryc := 0
	for key: String in r.keys():
		var kind := key.split("_daleko")[0]
		var strom := _strom_tvar(kind) != "" or kind.begins_with("vrba") or kind.begins_with("olse") or kind.begins_with("borovice") \
				or kind.begins_with("briza") or kind.begins_with("dead_tree")
		var ker := kind.begins_with("shrub") or kind.begins_with("bez_") or kind.begins_with("sipek") or kind.begins_with("liska") \
				or kind.begins_with("ker")
		if not strom and not ker:
			continue
		var okraj := sir + (7.0 if strom else 4.0)
		var zust: Array = []
		for t: Array in r[key]:
			var d := Vector2(float(t[3]), float(t[11])) - c
			if absf(d.dot(osa)) < pul and absf(d.dot(bok)) < okraj:
				pryc += 1
				continue
			zust.append(t)
		r[key] = zust
	print("most: stromu a keru u mostu a najezdu pryc ", pryc)


## Jen pudorys mostu + 5 m (bez vody - _u_mostu bere i cele koryto).
func _u_mostu_jen(x: float, z: float) -> bool:
	var mm := _tvrz_root.find_child("Most_potok", true, false) as MeshInstance3D if _tvrz_root else null
	if mm == null:
		return false
	var b := ((mm.global_transform if mm.is_inside_tree() else mm.transform) * mm.get_aabb()).grow(5.0)
	return x > b.position.x and x < b.end.x and z > b.position.z and z < b.end.z


func _u_mostu(x: float, z: float) -> bool:
	if _tvrz_root == null:
		return false
	var mm := _tvrz_root.find_child("Most_potok", true, false) as MeshInstance3D
	if mm == null:
		return false
	var b := ((mm.global_transform if mm.is_inside_tree() else mm.transform) * mm.get_aabb()).grow(5.0)
	var ve_vode: bool = koryto != null and not koryto.blizko(x, z).is_empty() and float(koryto.blizko(x, z)[0]) < float(koryto.blizko(x, z)[2]) + 0.5
	return ve_vode or (x > b.position.x and x < b.end.x and z > b.position.z and z < b.end.z)


var _zeli_mista: Array = []


## Stredy hlavek zeli z Blenderu (shluky vrcholu do 0,25 m) -> sem prijdou modely zeli a salatu z Disku.
func _zeli_stredy(xf: Transform3D, v: PackedVector3Array) -> void:
	var shl := {}
	for q in v:
		var w := xf * q
		var c := Vector2i(floori(w.x / 0.5), floori(w.z / 0.5))
		if not shl.has(c):
			shl[c] = [Vector3.ZERO, 0]
		shl[c][0] += w
		shl[c][1] += 1
	for c: Vector2i in shl:
		var p: Vector3 = shl[c][0] / float(shl[c][1])
		var blizko := false
		for m: Vector3 in _zeli_mista:
			if Vector2(m.x, m.z).distance_to(Vector2(p.x, p.z)) < 0.35:
				blizko = true
				break
		if not blizko:
			_zeli_mista.append(p)


## Pravidlo 1 (radce 09:20, Misa: "zelenina v zahone - stahni pekne modely"): zeli z Blenderu jsou zelene koule
## s trojuhelniky - radeji nic nez primitiv; plochy s materialem zeli_* pryc, zahon (hlina v radcich) zustava.
func _bez_zeli(mi: MeshInstance3D) -> void:
	var am := mi.mesh as ArrayMesh
	if am == null:
		return
	var nove := ArrayMesh.new()
	var pryc := 0
	for si in am.get_surface_count():
		var mt := am.surface_get_material(si)
		var mn := String(mt.resource_name) if mt else String(am.surface_get_name(si))
		if mn.begins_with("zeli"):
			pryc += 1
			if mn.begins_with("zeli_hlava"):
				_zeli_stredy(mi.global_transform if mi.is_inside_tree() else mi.transform, am.surface_get_arrays(si)[Mesh.ARRAY_VERTEX])
			continue
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, am.surface_get_arrays(si))
		nove.surface_set_material(nove.get_surface_count() - 1, mt)
		nove.surface_set_name(nove.get_surface_count() - 1, am.surface_get_name(si))
	if pryc > 0:
		mi.mesh = nove
	print("zahradky: zeli pryc %d ploch (%s)" % [pryc, mi.name])


## Brody (Misa 0.74, radce 13:50: "brod jak ma byt"): kde stezka nebo cesta (PESINY) prechazi potok mimo most.
## Osa stezky se u brodu nevlni (_brod_tlum), teren: v korytu melcina 0,28 m pod hladinou, brehy srazene na 1:4
## v pasu 5 m (uprava_y); dno a najezdy zpevnene kameny a sterkem (_brody).
var brody: Array = []                  # [stred Vector2, smer Vector2, pul sirky koryta, hladina]


func _najdi_brody() -> void:
	brody = []
	_brody_malych_toku()
	if koryto == null:
		return
	for sg: Vector4 in pes_useky():
		var a := Vector2(sg.x, sg.y)
		var b := Vector2(sg.z, sg.w)
		var n := maxi(1, int(a.distance_to(b) / 0.5))
		var v_vode := false
		var zac := Vector2.ZERO
		for q in n + 1:
			var p := a.lerp(b, float(q) / n)
			var bl: Array = koryto.blizko(p.x, p.y)
			var voda := not bl.is_empty() and float(bl[0]) < float(bl[2])
			if voda and not v_vode:
				zac = p
			elif not voda and v_vode:
				var c := (zac + p) * 0.5
				var b2: Array = koryto.blizko(c.x, c.y)
				if not b2.is_empty() and not _u_mostu_jen(c.x, c.y):
					var dup := false
					for br: Array in brody:
						dup = dup or (br[0] as Vector2).distance_to(c) < 10.0
					if not dup:
						brody.append([c, (b - a).normalized(), float(b2[2]), float(b2[1])])
			v_vode = voda
	# Misa 0.76 "brod od lomu je hraz": hladina z koryta (-9,2) lezi o ~1 m niz nez viditelna voda potoku (reka.res,
	# -8,3) - dno pod ni bylo 1,2 m hluboko, hladina se tam skryla (hloubka > 1,5) a zbyl suchy pas napric. Dno brodu
	# podle viditelne vody: median vysky vrcholu hladiny do 6 m od stredu brodu.
	var rm: Mesh = load("res://modely/reka/reka.res") if reka_predpecena() else _reka_voda_mesh
	var rv := rm.get_faces() if rm else PackedVector3Array()
	for br: Array in brody:
		var ys: Array = []
		for q in rv:
			if Vector2(q.x, q.z).distance_to(br[0]) < 6.0:
				ys.append(q.y)
		if ys.size() > 4:
			ys.sort()
			var vv := float(ys[ys.size() / 2])
			print("brod (%.0f,%.0f): hladina koryta %.2f, viditelna voda %.2f" % [br[0].x, br[0].y, br[3], vv])
			# viditelna voda z jine trasy nez koryto (stary predpeceny potok) by brod vykopala hluboko (lom 28. 10.)
			if absf(vv - float(br[3])) <= float(pasma()["test"].get("brod_odchylka_max_m", 1.5)):
				br[3] = vv
			else:
				push_warning("brod (%.0f,%.0f): viditelna voda %.2f nesedi na koryto %.2f - dno podle koryta" % [br[0].x, br[0].y, vv, br[3]])
	print("brody: %s" % ", ".join(brody.map(func(b3: Array) -> String: return "(%.0f,%.0f)" % [b3[0].x, b3[0].y])))


## Brody na malych tocich ze zaznamu cesty.json prechody (druh brod, tok z voda.json toky; test smyslu hlida, ze kazde
## krizeni cesty s tokem ma zaznam): stred, smer cesty v miste, pul sirky koryta (tok + 0,5 m), hladina toku.
func _brody_malych_toku() -> void:
	var toky := {}
	for t: Dictionary in Pravidla.cti("voda", "toky"):
		toky[String(t["id"])] = t
	var osy := {}
	for c: Dictionary in (Pravidla.cti("cesty", "vozove") as Array) + (Pravidla.cti("cesty", "pesiny") as Array):
		osy[String(c["id"])] = c["osa"]
	for p: Dictionary in Pravidla.cti("cesty", "prechody"):
		if String(p["druh"]) != "brod" or not toky.has(String(p["tok"])) or not osy.has(String(p["cesta"])):
			continue
		var c := Vector2(float(p["stred"][0]), float(p["stred"][1]))
		var osa: Array = osy[String(p["cesta"])]
		var best := INF
		var dr := Vector2.RIGHT
		for i in osa.size() - 1:
			var a := Vector2(float(osa[i][0]), float(osa[i][1]))
			var b := Vector2(float(osa[i + 1][0]), float(osa[i + 1][1]))
			var q := Geometry2D.get_closest_point_to_segment(c, a, b)
			if q.distance_to(c) < best:
				best = q.distance_to(c)
				dr = (b - a).normalized()
		var t: Dictionary = toky[String(p["tok"])]
		var hl := 0.0
		var bd := INF
		for o: Array in t["osa_xzy"]:
			var dd := c.distance_to(Vector2(float(o[0]), float(o[1])))
			if dd < bd:
				bd = dd
				hl = float(o[2])
		brody.append([c, dr, float(t["sirka_m"]) * 0.5 + 0.5, hl])


func _brod_tlum(p: Vector2) -> float:
	var d := INF
	for br: Array in brody:
		d = minf(d, p.distance_to(br[0]))
	return smoothstep(4.0, 14.0, d)


## Havrani erb na tvrzi (radce 06:45, obrazky/erb): cizi stit (cervene sukno s bilym pruhem z fort.py PR.shield) nad
## branou a v sini skryt a misto nej stit_havran; na vrchol veze nad branou prapor korouhev_havran (zlate pole s havranem,
## vlaje po vetru) misto male zelezne korouhvicky.
func _erb_tvrze(root: Node3D) -> void:
	var kat := {}
	if FileAccess.file_exists(MOD + "predmety.json"):
		kat = JSON.parse_string(FileAccess.open(MOD + "predmety.json", FileAccess.READ).get_as_text())
	if not kat.has("stit_havran"):
		return
	var skryj := StandardMaterial3D.new()
	skryj.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	skryj.albedo_color = Color(0, 0, 0, 0)
	skryj.resource_name = "skryty_stit"
	var mist: Array = []
	for nm: String in ["Brana", "Sin"]:
		var mi := root.find_child(nm, true, false) as MeshInstance3D
		if mi == null:
			continue
		for si in mi.mesh.get_surface_count():
			var mt := mi.mesh.surface_get_material(si)
			var mn := String(mt.resource_name) if mt else ""
			if mn.begins_with("sukno_cervene") or mn.begins_with("bila"):
				var vv: PackedVector3Array = mi.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]
				if vv.size() > 120:
					continue                   # jen maly stit (palac ma cervene sukno na zdech)
				var ab := AABB(vv[0], Vector3.ZERO)
				for q in vv:
					ab = ab.expand(q)
				ab = mi.global_transform * ab if mi.is_inside_tree() else mi.transform * ab
				mi.set_surface_override_material(si, skryj)
				if mn.begins_with("sukno_cervene"):
					mist.append(ab)
	for ab: AABB in mist:
		var c := ab.get_center()
		# stit na zdi: lice od zdi ven (tenka osa AABB = normala zdi; ven = od stredu tvrze)
		var yaw := 0.0 if ab.size.z < ab.size.x else (-PI / 2.0 if c.x > 0.0 else PI / 2.0)
		if ab.size.z < ab.size.x and c.z < 0.0:
			yaw = PI
		data["vybaveni"].append({"id": "stit_havran", "p": [c.x, ab.position.y - 0.04, c.z], "yaw": yaw})
	# prapor: vrchol veze nad branou = nejvyssi mosazna makovice site BranaDrevo (kulicka 1,32 m nad vrcholem strechy)
	var bd := root.find_child("BranaDrevo", true, false) as MeshInstance3D
	if bd == null or not kat.has("korouhev_havran"):
		return
	var xf := bd.global_transform if bd.is_inside_tree() else bd.transform
	var top := Vector3(0, -INF, 0)
	for si in bd.mesh.get_surface_count():
		var mt := bd.mesh.surface_get_material(si)
		if mt and String(mt.resource_name).begins_with("mosaz"):
			for q: Vector3 in bd.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
				var w := xf * q
				if w.y > top.y:
					top = w
	if top.y == -INF:
		return
	var apex := Vector3(top.x, top.y - 1.37, top.z)
	# zelezna korouhvicka (fort.py: plech 0,55 x 0,36 m 0,85 m nad vrcholem) pryc - zerd praporu kryje tyc
	var am := bd.mesh as ArrayMesh
	var nove := ArrayMesh.new()
	var pryc := 0
	for si in am.get_surface_count():
		var arr := am.surface_get_arrays(si)
		var mt := am.surface_get_material(si)
		if mt and String(mt.resource_name).begins_with("zelezo"):
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
			var ni := PackedInt32Array()
			for t in idx.size() / 3:
				var c := xf * ((v[idx[t * 3]] + v[idx[t * 3 + 1]] + v[idx[t * 3 + 2]]) / 3.0)
				if c.y > apex.y + 0.8 and c.y < apex.y + 1.26 and c.x > apex.x - 0.02 and c.x < apex.x + 0.62 and absf(c.z - apex.z) < 0.15:
					pryc += 1
					continue
				ni.append_array([idx[t * 3], idx[t * 3 + 1], idx[t * 3 + 2]])
			arr[Mesh.ARRAY_INDEX] = ni
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(nove.get_surface_count() - 1, mt)
		nove.surface_set_name(nove.get_surface_count() - 1, am.surface_get_name(si))
	bd.mesh = nove
	data["vybaveni"].append({"id": "korouhev_havran", "p": [apex.x, apex.y - 0.15, apex.z], "yaw": -atan2(0.6, 0.8)})
	print("erb: %d stity, prapor na %s (korouhvicka %d troj. pryc)" % [mist.size(), apex, pryc])


## Nove domy vsi Lhota (Misa 25. 10.: "ves prestavet z novych domu, chalupy nahradit, ne pridat, dispozice zustava";
## modely/ves/domy.glb z blender/ves_domy.py, NAVOD.md modelare): chalupy 1-7 z blender/vesnice.py layout() pryc
## (trojuhelniky site Vesnice, kolize, mistnosti, vybaveni, ohne, dvere), na jejich miste dum 1, dum 2 a rychta.
## Krcma (usedlost 0), chlevy, ploty, vrata a zahradky zustavaji. Osa domu: stit (+z modelu) do navsi jako stara
## chalupa, vstup (+x modelu) na stranu zahradky, dvorni dvere (-x) do dvora.
var VES_DOMY := not OS.has_environment("TVRZ_BEZ_DOMU")
const VES_DOMY_GLB := "res://modely/ves/domy.glb"
# usedlost: [k, stred stare chalupy x, z, yaw osy (vesnice.py Frame), L, W, model]
var VES_STARE := [
	[1, 484.24, 798.14, 2.2753, 11.26, 5.68, "Dum2"],
	[2, 505.59, 816.28, 2.2753, 11.08, 6.37, "Dum1"],
	[3, 525.66, 833.34, 2.2753, 11.92, 5.65, "Dum2"],
	[4, 419.39, 830.95, -0.8663, 11.41, 6.17, "Dum1"],
	[5, 441.20, 849.49, -0.8663, 13.00, 7.00, "Rychta"],
	[6, 461.50, 866.74, -0.8663, 10.66, 6.08, "Dum2"],
	[7, 483.64, 885.56, -0.8663, 11.33, 5.74, "Dum1"],
]
# mistni rozmery modelu (Godot, +z stit do navsi): podezdivka f/b (z), hw (x), strecha rx/rz0/rz1, podlaha, sin z0..z1,
# jizba z0..z1, komora z0..z1 (dvere mistnosti z kolizi Kol_StenaP*), mistnosti x do +-ix
const DUM_MER := {
	"Dum1": {"vstup": -0.5, "dvur": 0.45, "f": 5.17, "b": -5.17, "hw": 3.67, "rx": 4.42, "rz0": -5.95, "rz1": 5.95, "pod": 0.305, "ix": 3.4,
			"jizba": [0.81, 4.9], "sin": [-1.69, 0.59], "komora": [-4.9, -1.91], "nazev": "Selský dům", "komora_t": "Komora"},
	"Dum2": {"vstup": -0.2, "dvur": 0.2, "f": 4.67, "b": -4.67, "hw": 3.17, "rx": 3.8, "rz0": -5.14, "rz1": 5.14, "pod": 0.255, "ix": 2.9,
			"jizba": [1.0, 4.4], "sin": [-1.2, 0.8], "komora": [-4.4, -1.4], "nazev": "Chalupa", "komora_t": "Chlév"},
	"Rychta": {"vstup": -2.25, "dvur": 2.2, "f": 4.07, "b": -8.88, "hw": 3.97, "rx": 4.72, "rz0": -9.39, "rz1": 4.86, "pod": 0.305, "ix": 3.7,
			"jizba": [-0.45, 3.8], "sin": [-3.8, -0.66], "komora": [-8.23, -4.64], "nazev": "Rychta", "komora_t": "Kamenná komora"},
	# chyse A (NAVOD_CHYSE.md): bez podezdivky - teren pod chysi a pred ni (ohniste, spalek, hranice: "ft") na urovni podlahy
	"ChyseKura": {"f": 2.85, "b": -2.85, "hw": 1.9, "rx": 2.25, "rz0": -3.12, "rz1": 2.94, "pod": 0.0, "ft": 4.8, "t_in": -0.03, "t_pas": -0.03},
	"ChysePrkna": {"f": 2.41, "b": -2.41, "hw": 2.22, "rx": 2.25, "rz0": -2.9, "rz1": 2.9, "pod": 0.5, "ft": 4.8, "t_in": 0.05, "t_pas": -0.02},
}
# chyse (Misa/radce 07:45): [x, z, smer predku (uhel osy +z ve svete, rad), model, paseka r (stromy pryc), kam vede
# vyslapany chodnicek od dveri (Misa 25. 10. "k chysim chodnicky vyslapane a pred vstupy, at vypada zabydlene")]
# 2x u lomu naproti stene v trave (prkna, dvere k lomu), 2x uhlirske v lese nad vsi (kura, vyklizeny plac)
const VES_CHYSE := [
	# mista vybrana podle svahu (place_building: svah pod pudorysem < zidka 0,5 m / kuly 0,29 m) - rovinky 0,2-0,3 m
	[642.0, 818.0, PI / 4.0, "ChyseKura", 12.0, [Vector2(640.0, 825.0)]],
	[651.0, 821.0, PI - 0.2, "ChyseKura", 12.0, [Vector2(640.0, 825.0)]],
]
# vybaveni (katalog predmetu): [id, x, z, yaw v ramci domu, vyska nad podlahou] - jizba u lavice ve svatem koute
# (lavice podel +x, pec v koute -x u sine), sin nechava volne dvere, komora zasoby
const DUM_VYB := {
	"Dum1": [["stul_selsky", 2.25, 3.4, PI / 2, 0.0], ["lavice_selska", 1.4, 3.4, PI / 2, 0.0], ["miska", 2.2, 3.0, 0.3, 0.776],
			["hrnec", 2.3, 3.9, 0.0, 0.776], ["lzice", 2.1, 3.6, 1.2, 0.776], ["ovci_kuze", -2.4, 4.1, 0.2, 0.0],
			["truhla_vyrezavana", -0.3, 4.45, 0.0, 0.0], ["vedro", -1.45, 3.1, 0.0, 0.0], ["spalek", -1.2, 3.6, 0.0, 0.0],
			["metla", -2.9, -1.35, PI / 2, 0.0], ["pytel_obili", -2.9, -4.4, 0.4, 0.0], ["pytel_obili", -2.3, -4.5, -0.2, 0.0],
			["sud", 2.8, -4.3, 0.0, 0.0], ["kosik", 2.75, -2.5, 0.5, 0.0], ["bedna", -2.8, -2.6, PI / 2, 0.0]],
	"Dum2": [["stul_selsky", 1.65, 3.2, PI / 2, 0.0], ["lavice_selska", 0.85, 3.2, PI / 2, 0.0], ["miska", 1.6, 2.8, 0.3, 0.776],
			["hrnec", 1.7, 3.6, 0.0, 0.776], ["ovci_kuze", -1.9, 3.9, 0.2, 0.0], ["bedna", -0.2, 4.0, 0.0, 0.0],
			["vedro", -1.2, 3.3, 0.0, 0.0], ["metla", -2.45, -0.9, PI / 2, 0.0]],
	"Rychta": [["stul_selsky", 2.35, 1.7, PI / 2, 0.0], ["lavice_selska", 1.5, 1.7, PI / 2, 0.0], ["miska", 2.3, 1.3, 0.3, 0.776],
			["korbel", 2.4, 2.0, 0.0, 0.776], ["vino_dzban", 2.3, 2.3, 0.0, 0.776], ["svicen", 2.45, 1.0, 0.0, 0.776],
			["truhla_vyrezavana", -0.6, 3.35, 0.0, 0.0], ["kolebka", -1.9, 3.2, 0.0, 0.0], ["vedro", -1.9, 0.1, 0.0, 0.0],
			["metla", 3.4, -3.3, 0.0, 0.0], ["sud", 2.9, -3.2, 0.0, 0.0], ["pytel_obili", -1.6, -7.7, 0.3, -0.75],
			["pytel_obili", -1.0, -7.8, -0.4, -0.75], ["pytel_mouky", 1.5, -7.7, 0.1, -0.75], ["sud", 1.6, -5.2, 0.0, -0.75]],
}
var _domy: Array = []                # {k, typ, m (DUM_MER), o: Vector2, b: Basis, xf, inv, y}
var _kat_p: Dictionary = {}
const DUM_DREVO := {
	1: [["drevo_hromada", -1, 0.25, 1.6, 0.4], ["spalek_stipani", -1, 0.1, 3.2, 0.0]],
	2: [["drevo_vysoka_1", -1, 0.2, 0.05, 0.0]],
	3: [["drevo_mala", 0, 0.65, 0.05, 0.0]],
	4: [["drevo_dlouha_1", -1, 0.5, 0.05, 0.0]],
	5: [["drevo_kulatina", -1, 0.35, 3.5, 0.1], ["drevo_vysoka_2", 0, 0.3, 0.05, 0.0]],
	6: [["drevo_dlouha_2", 1, 0.15, 0.05, 0.0]],
	7: [["drevo_hromada", 0, 0.5, 1.2, 1.1], ["drevo_mala", -1, 0.3, 0.05, PI]],
}
# zebrik na pudu (model: v sini, sklon podel x, vrchol u otvoru v povale): pata, vrchol, nastup (podlaha sine),
# sestup (povala vedle otvoru) v souradnicich modelu
const DUM_ZEBRIK := {
	"Dum1": [Vector3(1.72, 0.30, 0.27), Vector3(0.62, 2.84, 0.27), Vector3(2.35, 0.30, 0.27), Vector3(-1.0, 2.64, 0.25)],
	"Dum2": [Vector3(1.72, 0.25, 0.47), Vector3(0.62, 2.79, 0.47), Vector3(2.35, 0.25, 0.47), Vector3(-1.0, 2.59, 0.35)],
	"Rychta": [Vector3(2.24, 0.30, -0.98), Vector3(0.95, 2.84, -0.98), Vector3(2.8, 0.30, -0.98), Vector3(-0.8, 2.64, -1.03)],
}


## Zebrik do nabidky pouziti: dole "Lézt nahoru" u paty, nahore "Slézt dolů" u sestupu.
func zebrik_use(zb: Dictionary) -> void:
	info["use"].append({"kind": "zebrik", "pos": (zb["nastup"] as Vector3).lerp(zb["pata"], 0.5) + Vector3(0, 1.0, 0), "r": 2.2,
			"zb": zb, "nahore": false, "nazev": "Žebřík"})
	info["use"].append({"kind": "zebrik", "pos": (zb["sestup"] as Vector3).lerp(zb["vrchol"], 0.4) + Vector3(0, 0.6, 0), "r": 2.2,
			"zb": zb, "nahore": true, "nazev": "Žebřík"})


## Ramce novych domu (jen xz): pocatek modelu tak, aby predni podezdivka lezela v linii stitu stare chalupy.
func _domy_ramce() -> void:
	_domy.clear()
	if not VES_DOMY or not ResourceLoader.exists(VES_DOMY_GLB):
		return
	for s: Array in VES_STARE:
		var a := float(s[3])
		var au := Vector2(cos(a), sin(a))
		var m: Dictionary = DUM_MER[s[6]]
		var o := Vector2(s[1], s[2]) + au * (float(s[4]) * 0.5 - float(m["f"]))
		var b := Basis(Vector3.UP, PI / 2.0 - a)
		var xf := Transform3D(b, Vector3(o.x, 0.0, o.y))
		_domy.append({"k": int(s[0]), "typ": String(s[6]), "m": m, "c": Vector2(s[1], s[2]), "au": au,
				"av": Vector2(-sin(a), cos(a)), "L": float(s[4]), "W": float(s[5]), "xf": xf, "inv": xf.affine_inverse(), "y": INF})
	for i in VES_CHYSE.size():
		var ch: Array = VES_CHYSE[i]
		var a2 := float(ch[2])
		var xf2 := Transform3D(Basis(Vector3.UP, PI / 2.0 - a2), Vector3(ch[0], 0.0, ch[1]))
		_domy.append({"k": 20 + i, "typ": String(ch[3]), "m": DUM_MER[ch[3]], "c": Vector2(ch[0], ch[1]), "au": Vector2(cos(a2), sin(a2)),
				"av": Vector2(-sin(a2), cos(a2)), "L": 0.0, "W": 0.0, "xf": xf2, "inv": xf2.affine_inverse(), "y": INF,
				"paseka": float(ch[4]), "k_cili": ch[5]})
	_pesiny_k_domum()


## Vyslapane chodnicky (pesiny 0,5 m): od vstupu domu ven pres mezeru v plotu k navsi, od dvornich dveri do dvora,
## od dveri chysi k cili (lom, pesina k uhlirum). Pridava se na konec PESINY (index >= 12, mimo vyluku u tvrze).
func _pesiny_k_domum() -> void:
	var w := func(d: Dictionary, x: float, z: float) -> Vector2:
		var p: Vector3 = (d["xf"] as Transform3D) * Vector3(x, 0.0, z)
		return Vector2(p.x, p.z)
	var n := 0
	for d: Dictionary in _domy:
		var m: Dictionary = d["m"]
		var hw := float(m["hw"])
		var f := float(m["f"])
		var cesty: Array = []
		if m.has("vstup"):
			var zv := float(m["vstup"])
			# cesticka od paty schodu a az za okapem (ne pod schody ani pod strechou; test zasazeni 28. 10. Dum2 schod)
			var sch := maxf(float(pasma()["budova"]["schody_m"]), float(pasma()["budova"]["okap_m"]))
			cesty.append([w.call(d, hw + sch, zv), w.call(d, hw + sch + 0.6, zv + 0.8), w.call(d, hw + 1.4, f + 0.5), w.call(d, hw + 0.9, f + 3.0)])
			var zd := float(m["dvur"])
			cesty.append([w.call(d, -hw - 0.25, zd), w.call(d, -hw - 2.0, zd - 0.3), w.call(d, -hw - 4.0, zd - 1.2)])
		else:
			var c: Array = [w.call(d, 0.0, f + maxf(float(pasma()["budova"]["schody_m"]), float(pasma()["budova"]["okap_m"]))), w.call(d, 0.3, f + 2.6)]
			c.append_array(d.get("k_cili", []))
			cesty.append(c)
		_pesina_k_ulici(cesty[0])                  # jen od dveri (dvorek zustava za plotem)
		for c: Array in cesty:
			PESINY.append(c)
			PES_SIRKA.append(float(Pravidla.cti("cesty", "pesiny_odvozene", "ke_dverim_pulsirka_m")))
			n += 1
	print("ves: %d chodnicku ke dverim" % n)


## Chodnicek od dveri dovede az na ulici (Misa 27. 10.: „pekne to napoj k domum“) - konci-li do 16 m od ni: mirne
## zahnuty, posledni bod na okraji ulice smerem k vjezdu (chodi se tam, kam se jde).
func _pesina_k_ulici(c: Array) -> void:
	if not VES_OBLOUK or c.size() < 2:
		return
	var a: Vector2 = c[c.size() - 1]
	if vo.od_ulice(a) > 16.0:
		return
	var osa: PackedVector2Array = vo.osa_ulice() if _vo_osa.is_empty() else _vo_osa
	_vo_osa = osa
	var bi := 0
	for i in osa.size():
		if a.distance_squared_to(osa[i]) < a.distance_squared_to(osa[bi]):
			bi = i
	var cil := osa[maxi(bi - 2, 0)]
	var smer := (a - (c[c.size() - 2] as Vector2)).normalized()
	var d := a.distance_to(cil)
	if d < 1.5:
		return
	c.append(a + smer * minf(d * 0.4, 2.5) + (cil - a) * 0.25)
	c.append(cil.lerp(a, 1.0 / d))


var _vo_osa := PackedVector2Array()


## Chyse u lomu (Misa 0.78: "nerespektujes cesty, boudy do cesty, vchody kousek od sebe na jednu stranu"): misto se
## hleda - mimo lom (> 6 m), od pesin i vozove cesty (Teren_cesta) > 7 m, nejrovnejsi pudorys; druha chyse 8-11 m
## od prvni, obe vchodem ke spolecnemu dvorku mezi nimi, z dvorku chodnicek na pesinu k lomu.
const LOM_CHYSE_OBLAST := Rect2(150.0, 885.0, 60.0, 85.0)


const LOM_VCHOD := Vector2(150.0, 935.0)       # plocha lomu (PESINY 6 zacina 140,940)


func _chyse_k_lomu() -> void:
	if not VES_DOMY or not ResourceLoader.exists(VES_DOMY_GLB):
		return
	var cesta := {}
	var cmi := _tvrz_root.find_child("Teren_cesta", true, false) as MeshInstance3D if _tvrz_root else null
	if cmi and cmi.mesh:
		var cxf := cmi.global_transform if cmi.is_inside_tree() else cmi.transform
		for q: Vector3 in cmi.mesh.get_faces():
			var w := cxf * q
			if LOM_CHYSE_OBLAST.grow(20.0).has_point(Vector2(w.x, w.z)):
				cesta[Vector2i(floori(w.x / 2.0), floori(w.z / 2.0))] = true
	var vzd_pes := func(p: Vector2) -> float:
		var best := INF
		for c: Array in PESINY:
			for i in c.size() - 1:
				best = minf(best, Geometry2D.get_closest_point_to_segment(p, c[i], c[i + 1]).distance_to(p))
		return best
	var u_cesty := func(p: Vector2) -> bool:
		var c0 := Vector2i(floori(p.x / 2.0), floori(p.y / 2.0))
		for dx in range(-4, 5):
			for dz in range(-4, 5):
				if cesta.has(c0 + Vector2i(dx, dz)):
					return true
		return false
	var svah := func(p: Vector2) -> float:
		var mn := INF
		var mx := -INF
		for o: Vector2 in [Vector2.ZERO, Vector2(2.5, 2.5), Vector2(-2.5, 2.5), Vector2(2.5, -2.5), Vector2(-2.5, -2.5), Vector2(0, 4.5)]:
			var y := _vyska(p.x + o.x, p.y + o.y)
			mn = minf(mn, y)
			mx = maxf(mx, y)
		return mx - mn
	var mista: Array = []
	var x := LOM_CHYSE_OBLAST.position.x
	while x < LOM_CHYSE_OBLAST.end.x:
		var z := LOM_CHYSE_OBLAST.position.y
		while z < LOM_CHYSE_OBLAST.end.y:
			var p := Vector2(x, z)
			if v_lomu(x, z) > 6.0 and vzd_pes.call(p) > 7.0 and not u_cesty.call(p):
				mista.append([svah.call(p), p])
			z += 1.5
		x += 1.5
	if mista.is_empty():
		push_warning("chyse u lomu: zadne volne misto mimo cesty")
		return
	mista.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	var a: Vector2 = mista[0][1]
	var b := Vector2.INF
	# druha chyse VEDLE prvni (prucelí obou ke vchodu lomu), ne za ni: jinak cesticka od druhe na spolecny placek
	# vede skrz prvni (test zasazeni 28. 10.: pesina pod strechou a stitem chyse (163, 957))
	var k0 := (LOM_VCHOD - a).normalized()
	for m: Array in mista:
		var d := (m[1] as Vector2).distance_to(a)
		if d >= 8.0 and d <= 11.0 and absf(((m[1] as Vector2) - a).normalized().dot(k0)) < 0.5:
			b = m[1]
			break
	if b == Vector2.INF:
		push_warning("chyse u lomu: druhe misto nenalezeno")
		return
	var dvur := (a + b) * 0.5
	var dc := 0.0
	var k := 20
	var lom6: Array = PESINY[6]
	# Misa 0.88: vchody k lomu; pred chysemi spolecny vyslapany placek (udusana hlina), z nej JEDNA cesticka na cestu
	# k lomu (ne kazda chyse vlastni)
	var ks := ((LOM_VCHOD - a).normalized() + (LOM_VCHOD - b).normalized()).normalized()
	var plac := (a + b) * 0.5 + ks * (float(DUM_MER["ChysePrkna"]["f"]) + float(pasma()["budova"]["okap_m"]) + float(Pravidla.cti("cesty", "pesiny_odvozene", "placek_chysi_pulsirka_m")))
	var pc := plac
	var dpc := INF
	for i6 in lom6.size() - 1:
		var q6 := Geometry2D.get_closest_point_to_segment(plac, lom6[i6], lom6[i6 + 1])
		if q6.distance_to(plac) < dpc:
			dpc = q6.distance_to(plac)
			pc = q6
	for p: Vector2 in [a, b]:
		var smer := ks
		var a2 := atan2(smer.y, smer.x)
		var xf2 := Transform3D(Basis(Vector3.UP, PI / 2.0 - a2), Vector3(p.x, 0.0, p.y))
		var d := {"k": k, "typ": "ChysePrkna", "m": DUM_MER["ChysePrkna"], "c": p, "au": smer, "av": Vector2(-smer.y, smer.x),
				"L": 0.0, "W": 0.0, "xf": xf2, "inv": xf2.affine_inverse(), "y": INF, "paseka": 6.0, "k_cili": []}
		d["k_cili"] = [plac]
		_domy.append(d)
		k += 1
	# placek: kratka siroka osa pred obema vchody (pul sirky 3 m), cesticka z jeho stredu na cestu k lomu
	# osa placku pred prucelim: prucelí chyse (DUM_MER f) + pul sirky placku + 0,3 m (drive pevne 3,5 m od stredu -
	# placek 3 m siroky zasahoval 1,9 m do chyse, test zasazeni dum_v_ceste u (201, 938))
	var pul_pl := float(Pravidla.cti("cesty", "pesiny_odvozene", "placek_chysi_pulsirka_m"))
	var odst := float(DUM_MER["ChysePrkna"]["f"]) + float(pasma()["budova"]["okap_m"]) + pul_pl
	PESINY.append([a + ks * odst, b + ks * odst])
	PES_SIRKA.append(pul_pl)
	PESINY.append([plac, plac + (pc - plac) * 0.5, pc])
	PES_SIRKA.append(float(Pravidla.cti("cesty", "pesiny_odvozene", "k_chysim_pulsirka_m")))
	# stromy a kere na mistech chysi pryc (rostliny se stavi az pozdeji - data jeste nejsou rozsetá jen ze svet.json)
	for key: String in data["rostliny"]:
		var arr: Array = data["rostliny"][key]
		var zust: Array = []
		for t: Array in arr:
			if Vector2(float(t[3]), float(t[11])).distance_to(a) > 6.0 and Vector2(float(t[3]), float(t[11])).distance_to(b) > 6.0:
				zust.append(t)
		if zust.size() != arr.size():
			data["rostliny"][key] = zust
	print("chyse u lomu: %s a %s (svah %.2f m), dvorek %s, chodnik k pesine %.0f m" % [a, b, mista[0][0], dvur, dc])


## Mistni souradnice domu (x, z) bodu xz.
func _dum_mist(d: Dictionary, x: float, z: float) -> Vector2:
	var q: Vector3 = (d["inv"] as Transform3D) * Vector3(x, 0.0, z)
	return Vector2(q.x, q.z)


## Bod uvnitr stare chalupy (vcetne strechy a sudu u zdi) nebo noveho domu (+ okraj).
func _dum_zabira(x: float, z: float, okraj_novy := 0.2, stara := true) -> bool:
	for d: Dictionary in _domy:
		var p := Vector2(x, z) - (d["c"] as Vector2)
		# stara chalupa: vpredu podsin 1,9 m + presah stitu (Misa 0.78 "zustaly stity starych"), vzadu hranice dreva
		var u := p.dot(d["au"])
		if stara and float(d["L"]) > 0.0 and u < float(d["L"]) * 0.5 + 3.0 and u > -float(d["L"]) * 0.5 - 1.6 \
				and absf(p.dot(d["av"])) < float(d["W"]) * 0.5 + 1.35:
			return true
		var q := _dum_mist(d, x, z)
		var m: Dictionary = d["m"]
		if absf(q.x) < float(m["hw"]) + okraj_novy and q.y < float(m["f"]) + okraj_novy and q.y > float(m["b"]) - okraj_novy:
			return true
	return false


## Data sveta bez starych chalup (pred kolizemi, mistnostmi, vybavenim a pohybem).
func _ves_stare_pryc() -> void:
	_domy_ramce()
	if _domy.is_empty():
		return
	var ks := {}
	for d: Dictionary in _domy:
		ks[int(d["k"])] = true
	var n := [0, 0, 0, 0, 0, 0]
	var kol: Array = []
	for c: Array in data["kolize"]:
		if _dum_zabira(float(c[0]), float(c[2])):
			n[0] += 1
		else:
			kol.append(c)
	data["kolize"] = kol
	var mi: Array = []
	for r: Dictionary in data["mistnosti"]:
		var nm := String(r["name"])
		if nm.begins_with("ves_") and ks.has(int(nm.split("_")[1])):
			n[1] += 1
		else:
			mi.append(r)
	data["mistnosti"] = mi
	var vb: Array = []
	for it: Dictionary in data["vybaveni"]:
		var p: Array = it["p"]
		if _dum_zabira(float(p[0]), float(p[2])):
			n[2] += 1
		else:
			vb.append(it)
	data["vybaveni"] = vb
	var oh: Array = []
	for o: Dictionary in data["ohne"]:
		var p2: Array = o["pos"]
		if _dum_zabira(float(p2[0]), float(p2[2])):
			n[3] += 1
		else:
			oh.append(o)
	data["ohne"] = oh
	var po: Array = []
	_domy_pryc_uzly.clear()
	for e: Dictionary in data["pohyb"]:
		var p3: Array = e.get("use", e["pos"])          # vrata: stred mezi kridly (ne pant jednoho kridla)
		if String(e["name"]).begins_with("Pohyb_ves_") and _dum_zabira(float(p3[0]), float(p3[2]), 0.6, String(e["name"]).contains("dvere")):
			n[4] += 1
			_domy_pryc_uzly.append(String(e["name"]))
		else:
			po.append(e)
	data["pohyb"] = po
	for key: String in data["rostliny"]:
		var arr: Array = data["rostliny"][key]
		var zust: Array = []
		for t: Array in arr:
			if _dum_zabira(float(t[3]), float(t[11]), 0.6, false) or _na_pasece(float(t[3]), float(t[11])):
				n[5] += 1
			else:
				zust.append(t)
		if zust.size() != arr.size():
			data["rostliny"][key] = zust
	print("ves: stare chalupy pryc - kolize %d, mistnosti %d, vybaveni %d, ohne %d, dvere/branky %d, rostliny %d" % n)


var _domy_pryc_uzly: Array = []


## Stara zahradka usedlosti (vesnice.py garden: u = -L/2+0,8..L/2-0,6, v = -W/2-5,8..-W/2-1) - nahrazena zahony.
func _v_stare_zahrade(x: float, z: float) -> bool:
	for d: Dictionary in _domy:
		if float(d["L"]) <= 0.0:
			continue
		var p := Vector2(x, z) - (d["c"] as Vector2)
		var u := p.dot(d["au"])
		var v := p.dot(d["av"])
		# cela stara zahradka usedlosti (zeli koule i mezi novymi zahony, Misa 0.78)
		if absf(u) < float(d["L"]) * 0.5 + 1.5 and v < 0.5 and v > -(float(d["W"]) * 0.5 + 7.0):
			return true
	return false


func _na_pasece(x: float, z: float) -> bool:
	for d: Dictionary in _domy:
		if float(d.get("paseka", 0.0)) > 0.0 and Vector2(x, z).distance_to(d["c"]) < float(d["paseka"]):
			return true
	return false


## Vyska domu z puvodniho terenu (podezdivka 0,45 m pod podlahou + 0,3): prumer rohu a stredu, terén se pod domem
## a v pasu 1,5 m srovna (dum_teren) - nic ve vzduchu, nic v zemi.
func _domy_vysky() -> void:
	_chyse_k_lomu()
	_domy_vysky_hlavni()
	_ryb_pod_domy()


## Teren dilu rybnika (ctverec 60 m, rohem az pod dum 7) pod domy a v pasu kolem nich - stejne jako teren hry
## (dum_teren); Misa 0.78 "chalupa u rybnika ma kopec i uvnitr". Kolize dilu znovu ze site, vysky trav (_ryb_tri) taky.
func _ryb_pod_domy() -> void:
	if _ryb_scena == null:
		return
	var mi := _ryb_scena.find_child("Rybnik_Teren*", true, false) as MeshInstance3D
	if mi == null or not (mi.mesh is ArrayMesh):
		return
	var xf := _ryb_xf * _rel_xf(mi, _ryb_scena)
	var inv := xf.affine_inverse()
	var am := mi.mesh as ArrayMesh
	var nove := ArrayMesh.new()
	var n := 0
	for si in am.get_surface_count():
		var arr := am.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		for i in v.size():
			var w := xf * v[i]
			var y2 := dum_teren(w.x, w.z, w.y)
			if absf(y2 - w.y) > 0.005:
				w.y = y2
				v[i] = inv * w
				n += 1
		arr[Mesh.ARRAY_VERTEX] = v
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(si, am.surface_get_material(si))
	if n == 0:
		return
	mi.mesh = nove
	for sb in mi.find_children("*", "CollisionShape3D", true, false):
		(sb as CollisionShape3D).shape = nove.create_trimesh_shape()
	_ryb_tri.clear()
	var f := nove.get_faces()
	for i in range(0, f.size(), 3):
		var a := xf * f[i]
		var c := xf * f[i + 1]
		var d := xf * f[i + 2]
		for cx in range(floori(minf(a.x, minf(c.x, d.x)) / 2.0), floori(maxf(a.x, maxf(c.x, d.x)) / 2.0) + 1):
			for cz in range(floori(minf(a.z, minf(c.z, d.z)) / 2.0), floori(maxf(a.z, maxf(c.z, d.z)) / 2.0) + 1):
				var key := Vector2i(cx, cz)
				if not _ryb_tri.has(key):
					_ryb_tri[key] = []
				(_ryb_tri[key] as Array).append([a, c, d])
	print("rybnik: teren dilu pod domy srovnan, %d vrcholu" % n)


func _domy_vysky_hlavni() -> void:
	for d: Dictionary in _domy:
		var m: Dictionary = d["m"]
		var ys: Array = []
		for qx in [-1.0, 0.0, 1.0]:
			for qz in [float(m["b"]), 0.0, float(m.get("ft", m["f"]))]:
				var w: Vector3 = (d["xf"] as Transform3D) * Vector3(qx * float(m["hw"]), 0.0, qz)
				ys.append(_vyska(w.x, w.z))
		# place_building (Misa 25. 10.): budova svisle, jen yaw; podlaha 0,1 m nad nejvyssim bodem pudorysu; svah vetsi
		# nez podezdivka (0,45 pod nulou modelu + podlaha) = varovani - teren se srovna (dum_teren), splyne s okolim
		var podl: float = float(ys.max()) + 0.1
		var y0 := podl - float(m["pod"])
		if not m.has("ix"):
			# chyse: zidka / kuly primo na zemi - teren se pod ni srovna na prumer (dum_teren, prechod 6,5 m)
			var s2 := 0.0
			for y2: float in ys:
				s2 += y2
			y0 = s2 / ys.size()
		if m.has("ix") and podl - float(ys.min()) > float(m["pod"]) + 0.45:
			push_warning("dum %s_%d: svah %.2f m vetsi nez podezdivka %.2f m - teren se srovna" % [d["typ"], d["k"], podl - float(ys.min()), float(m["pod"]) + 0.45])
		d["y"] = y0
		var xf: Transform3D = d["xf"]
		xf.origin.y = y0
		d["xf"] = xf
		d["inv"] = xf.affine_inverse()
		print("dum %s (usedlost %d): y %.2f, teren %.2f..%.2f" % [d["typ"], d["k"], y0, ys.min(), ys.max()])


## Teren pod novym domem a kolem nej (vrcholy siti i mrizky).
func dum_teren(x: float, z: float, y: float) -> float:
	for d: Dictionary in _domy:
		if float(d["y"]) == INF:
			continue
		var c: Vector2 = d["c"]
		if absf(x - c.x) > 16.0 or absf(z - c.y) > 16.0:
			continue
		var q := _dum_mist(d, x, z)
		var m: Dictionary = d["m"]
		var y0 := float(d["y"])
		var dx := maxf(absf(q.x) - float(m["hw"]), 0.0)
		var dz := maxf(maxf(q.y - float(m.get("ft", m["f"])), float(m["b"]) - q.y), 0.0)
		if m.has("t_pas"):
			# chyse: hruba sit terenu (vrcholy po ~5 m) - plocha dosypana/srovnana a siroky prechod 6 m do okoli
			# (Misa: "dodelat zem pod nej, ale ne jen pod nim - musi splynout s okolim")
			var dd2 := sqrt(dx * dx + dz * dz)
			if dd2 < 6.5:
				y = lerpf(y0 + float(m["t_pas"]), y, smoothstep(0.0, 6.5, dd2))
			continue
		if dx == 0.0 and dz == 0.0:
			# uvnitr: pod podlahou (zahloubena komora rychty jeste niz); chyse: teren = podlaha z hliny
			# uvnitr presne pod podlahu (i zvednout: nizsi vrchol uvnitr tahl teren u zdi pod dno podezdivky - test
			# stavby_na_zemi, skvira 6 cm u domu 3); zahloubena komora rychty niz
			# komora rychty: jen vrcholy aspon 1 m od zdi (svah trojuhelniku pres zed byl venku jako dolik, Misa 0.83)
			y = y0 - 0.85 if String(d["typ"]) == "Rychta" and q.y < -4.0 and q.y > float(m["b"]) + 1.0 and absf(q.x) < 2.9 else y0 - 0.15
			continue
		var dd := sqrt(dx * dx + dz * dz)
		if dd < 1.8:
			# u zdi: teren 0,2 m pod podlahou (podezdivka videt 0,5 m), plynule do 1,8 m
			# jen dolu, ne nahoru: ve svahu (rychta) srovnani pod podlahu delalo kolem zdi prikop („dolíky“, Misa 0.83)
			var cil := clampf(y, y0 + float(m.get("t_pas", -0.2)), y0 - 0.02)
			y = lerpf(cil, y, smoothstep(0.4, 1.8, dd))
	return y


## Vrata stodol (Misa 0.83 „ať stodoly mají vrata, ať se dají užívat“): kridla jsou v siti Vesnice (material
## "dvere", blender/vesnice.py barn: 2 kridla 1,3 m, panty +-1,42 m, prave pootevrene o 72 st.) - vyriznout jako
## Pohyb_stodola_*, obe zavrena, oteviraji se ven; kolize kridla (otvor ve stene kolize ma).
func _stodoly_vrata(root: Node3D) -> void:
	var mi := root.find_child("Vesnice", true, false) as MeshInstance3D
	if mi == null or not (mi.mesh is ArrayMesh):
		return
	var am := mi.mesh as ArrayMesh
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var dsi := -1
	var desky := PackedVector3Array()
	for si in am.get_surface_count():
		var mt := am.surface_get_material(si)
		var mn := String(mt.resource_name).split(".")[0] if mt else ""
		if mn == "dvere":
			dsi = si
		elif mn == "deska_stodola":
			for q: Vector3 in am.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
				desky.append(xf * q)
	if dsi < 0 or desky.is_empty():
		return
	var arr := am.surface_get_arrays(dsi)
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
	# shluky: 1) trojuhelniky sdilejici vrchol (jeden dil - prkno, prickа), 2) dily, jejichz obalky se dotykaji
	# (+3 cm) - prkna vedle sebe a pricky pres ne = kridlo (Misa 0.84: bunky vrcholu po 0,25 m kridlo nespojily)
	var nt := idx.size() / 3
	var rod: Array = []                 # Array (reference) - lambda si Packed pole kopiruje
	rod.resize(nt)
	for t in nt:
		rod[t] = t
	var najdi := func(a: int) -> int:
		while int(rod[a]) != a:
			rod[a] = rod[int(rod[a])]
			a = int(rod[a])
		return a
	var spoj := func(a: int, b: int) -> void:
		var ra: int = najdi.call(a)
		var rb: int = najdi.call(b)
		if ra != rb:
			rod[ra] = rb
	var prvni := {}
	for t in nt:
		for k in 3:
			var vi := idx[t * 3 + k]
			if prvni.has(vi):
				spoj.call(t, int(prvni[vi]))
			else:
				prvni[vi] = t
	var obal := {}                      # koren -> AABB (svet)
	var zast := {}                      # koren -> trojuhelnik
	for t in nt:
		var r: int = najdi.call(t)
		for k in 3:
			var w := xf * v[idx[t * 3 + k]]
			obal[r] = (obal[r] as AABB).expand(w) if obal.has(r) else AABB(w, Vector3.ZERO)
		zast[r] = t
	var bun := {}
	for r: int in obal:
		var ab: AABB = (obal[r] as AABB).grow(0.03)
		var c0 := Vector3i(ab.get_center() / 2.0)
		for dx in range(-1, 2):
			for dy in range(-1, 2):
				for dz in range(-1, 2):
					for r2: int in bun.get(c0 + Vector3i(dx, dy, dz), []):
						if ab.intersects((obal[r2] as AABB).grow(0.03)):
							spoj.call(int(zast[r]), int(zast[r2]))
		if not bun.has(c0):
			bun[c0] = []
		(bun[c0] as Array).append(r)
	var shluky := {}
	for t in nt:
		var r: int = najdi.call(t)
		if not shluky.has(r):
			shluky[r] = []
		(shluky[r] as Array).append(t)
	# kridlo stodoly: 1,2-1,45 m vodorovne, 2,2-2,5 m vysoke; pant = konec blize prknu steny
	var kridla: Array = []
	for r: int in shluky:
		var ts: Array = shluky[r]
		var pts := PackedVector3Array()
		for t: int in ts:
			for k in 3:
				pts.append(xf * v[idx[t * 3 + k]])
		var c := Vector3.ZERO
		var y0 := INF
		var y1 := -INF
		for p in pts:
			c += p
			y0 = minf(y0, p.y)
			y1 = maxf(y1, p.y)
		c /= pts.size()
		# hlavni vodorovna osa (kovariance xz)
		var sxx := 0.0
		var sxz := 0.0
		var szz := 0.0
		for p in pts:
			sxx += (p.x - c.x) * (p.x - c.x)
			sxz += (p.x - c.x) * (p.z - c.z)
			szz += (p.z - c.z) * (p.z - c.z)
		var ang := 0.5 * atan2(2.0 * sxz, sxx - szz)
		var d := Vector2(cos(ang), sin(ang))
		var s0 := INF
		var s1 := -INF
		for p in pts:
			var s := Vector2(p.x - c.x, p.z - c.z).dot(d)
			s0 = minf(s0, s)
			s1 = maxf(s1, s)
		var delka := s1 - s0
		if y1 - y0 > 1.8:
			print("stodoly: shluk %d troj, %.2f x %.2f m u %s" % [ts.size(), delka, y1 - y0, c.round()])
		if delka < 1.15 or delka > 1.5 or y1 - y0 < 2.1 or y1 - y0 > 2.6:
			continue
		var e0 := Vector2(c.x, c.z) + d * s0
		var e1 := Vector2(c.x, c.z) + d * s1
		var d0 := INF
		var d1 := INF
		for q in desky:
			if absf(q.y - c.y) > 1.5:
				continue
			d0 = minf(d0, Vector2(q.x, q.z).distance_to(e0))
			d1 = minf(d1, Vector2(q.x, q.z).distance_to(e1))
		var pant := e0 if d0 < d1 else e1
		var volny := e1 if d0 < d1 else e0
		kridla.append({"ts": ts, "pant": pant, "smer": (volny - pant).normalized(), "y0": y0, "delka": delka})
	# dvojice kridel jedne stodoly: panty 2,6-3,1 m od sebe
	var pouzite := {}
	var nove_idx := PackedInt32Array()
	var vyrez := {}
	var n := 0
	for i in kridla.size():
		if pouzite.has(i):
			continue
		for j in range(i + 1, kridla.size()):
			if pouzite.has(j):
				continue
			var a: Dictionary = kridla[i]
			var b: Dictionary = kridla[j]
			var dp := (a["pant"] as Vector2).distance_to(b["pant"])
			if dp < 2.6 or dp > 3.1:
				continue
			pouzite[i] = true
			pouzite[j] = true
			n += 1
			# zavreno = kridlo podel steny k druhemu pantu; ven = strana, kam je pootevrene kridlo vytocene
			var osa := ((b["pant"] as Vector2) - (a["pant"] as Vector2)).normalized()
			var nor := Vector2(-osa.y, osa.x)
			var ven := 1.0
			for kr: Dictionary in [a, b]:
				var sd := (kr["smer"] as Vector2).dot(nor)
				if absf(sd) > 0.3:
					ven = signf(sd)
			for q in 2:
				var kr: Dictionary = [a, b][q]
				var zavr: Vector2 = osa if q == 0 else -osa
				var pant: Vector2 = kr["pant"]
				var py := float(kr["y0"])
				# soucasna poloha kridla -> mistni souradnice zavreneho kridla (x podel kridla od pantu, y nahoru)
				var sm: Vector2 = kr["smer"]
				var cur := Basis(Vector3(sm.x, 0, sm.y), Vector3.UP, Vector3(sm.x, 0, sm.y).cross(Vector3.UP))
				var zb := Basis(Vector3(zavr.x, 0, zavr.y), Vector3.UP, Vector3(zavr.x, 0, zavr.y).cross(Vector3.UP))
				var o3 := Vector3(pant.x, py, pant.y)
				var cur_inv := Transform3D(cur, o3).affine_inverse()
				var st := SurfaceTool.new()
				st.begin(Mesh.PRIMITIVE_TRIANGLES)
				var nrm: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
				var uv: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV] if arr[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array()
				for t: int in kr["ts"]:
					vyrez[t] = true
					for k in 3:
						var vi := idx[t * 3 + k]
						if not uv.is_empty():
							st.set_uv(uv[vi])
						if not nrm.is_empty():
							st.set_normal(cur_inv.basis * (xf.basis * nrm[vi]))
						st.add_vertex(cur_inv * (xf * v[vi]))
				st.generate_tangents()
				var node := MeshInstance3D.new()
				var jm := "Pohyb_stodola_%d_%s" % [n, "l" if q == 0 else "p"]
				node.name = jm
				node.mesh = st.commit()
				node.set_surface_override_material(0, mi.get_surface_override_material(dsi) if mi.get_surface_override_material(dsi) else material("dvere"))
				root.add_child(node)
				var rx := root.global_transform if root.is_inside_tree() else root.transform
				var tz := Transform3D(zb, o3)
				node.transform = rx.affine_inverse() * tz
				# otevreni: volny konec (mistni +x) k strane ven; Basis(UP, a) * x = cos a * X - sin a * Z
				var zw := Vector2(zb.z.x, zb.z.z)
				var otev := 90.0 if (-zw).dot(nor * ven) > 0.0 else -90.0
				var dl := float(kr["delka"])
				var use := tz * Vector3(dl * 0.5, 1.1, 0.0)
				data["pohyb"].append({"name": jm, "kind": "dvere", "group": "stodola_%d" % n,
						"cols": [[dl * 0.5, 1.2, 0.0, dl, 2.35, 0.08]], "pos": [use.x, use.y, use.z], "use": [use.x, use.y, use.z],
						"open": otev, "init": 0.0, "dur": 1.6})
			break
	if vyrez.is_empty():
		print("stodoly: zadna vrata")
		return
	for t in nt:
		if not vyrez.has(t):
			nove_idx.append_array([idx[t * 3], idx[t * 3 + 1], idx[t * 3 + 2]])
	# povrch dvere bez kridel stodol (dvere chalup zustavaji)
	var ovr: Array = []
	var nove := ArrayMesh.new()
	for si in am.get_surface_count():
		var a2 := am.surface_get_arrays(si)
		if si == dsi:
			if nove_idx.is_empty():
				continue
			a2[Mesh.ARRAY_INDEX] = nove_idx
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a2)
		nove.surface_set_material(nove.get_surface_count() - 1, am.surface_get_material(si))
		nove.surface_set_name(nove.get_surface_count() - 1, am.surface_get_name(si))
		ovr.append(mi.get_surface_override_material(si))
	mi.mesh = nove
	for i in ovr.size():
		mi.set_surface_override_material(i, ovr[i])
	print("stodoly: %d vrat (%d kridel), %d troj." % [n, n * 2, vyrez.size()])


## Rychta (Misa 0.83 „z chodby do kamenne casti tram ve dverich“): tram stropu komory (M_RoubeniVnitrni, Blender
## y 4,90..5,07, z 1,73..1,92, pres celou sirku) visel nad schody dolu ve vysce hlavy a bez kolize - pryc (strop patra
## komory nese zed a dalsi tramy od y 5,55).
func _rychta_tram_pryc(mi: MeshInstance3D) -> void:
	var am := mi.mesh as ArrayMesh
	if am == null or mi.has_meta("tram_pryc"):
		return
	var nove := ArrayMesh.new()
	var pryc := 0
	for si in am.get_surface_count():
		var arr := am.surface_get_arrays(si)
		var mt := am.surface_get_material(si)
		var mn := String(mt.resource_name) if mt else ""
		if mn.begins_with("M_RoubeniVnitrni"):
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
			var ni := PackedInt32Array()
			for t in idx.size() / 3:
				var c := mi.transform * ((v[idx[t * 3]] + v[idx[t * 3 + 1]] + v[idx[t * 3 + 2]]) / 3.0)
				# glTF y-up: Blender (x, y, z) = hra (x, -z, y)
				if absf(c.x) < 2.5 and c.y > 1.68 and c.y < 1.97 and -c.z > 4.85 and -c.z < 5.12:
					pryc += 1
					continue
				ni.append_array([idx[t * 3], idx[t * 3 + 1], idx[t * 3 + 2]])
			arr[Mesh.ARRAY_INDEX] = ni
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(si, mt)
		nove.surface_set_name(si, am.surface_get_name(si))
	if pryc > 0:
		mi.mesh = nove
	mi.set_meta("tram_pryc", true)
	print("rychta: tram nad schody do komory pryc %d troj." % pryc)


## Modely domu do sveta: kazdy dum = kopie korene z domy.glb (site sdilene), dvere jako Pohyb_*, mistnosti, ohne, vybaveni.
func _ves_domy(root: Node3D) -> void:
	if _domy.is_empty():
		return
	var t0 := Time.get_ticks_msec()
	for nm: String in _domy_pryc_uzly:
		var nd := root.find_child(nm, true, false)
		if nd:
			nd.queue_free()
	_ves_site_vyrez(root)
	_stodoly_vrata(root)
	_chyse_na_sit(root)
	var sc := (load(VES_DOMY_GLB) as PackedScene).instantiate()
	for d: Dictionary in _domy:
		var vzor := sc.get_node_or_null(String(d["typ"]))
		if vzor == null:
			continue
		var dum := vzor.duplicate() as Node3D
		dum.name = "Dum_ves_%d" % int(d["k"])
		dum.transform = d["xf"]
		root.add_child(dum)
		var xf: Transform3D = d["xf"]
		var m: Dictionary = d["m"]
		var typ := String(d["typ"])
		var nazev := String(m.get("nazev", ""))
		var sin_z := (float(m["sin"][0]) + float(m["sin"][1])) * 0.5 if m.has("sin") else 0.0
		var kom_z := (float(m["komora"][0]) + float(m["komora"][1])) * 0.5 if m.has("komora") else 0.0
		for ch in dum.get_children():
			var cn := String(ch.name)
			if ch is MeshInstance3D:
				# rozpocet (ves 2 000 kresleni, 3,4 M troj.): podrobny dum do 60 m, dal _Daleko (blender/ves_domy.py,
				# 3 000 troj., 2 materialy); vnitrek, okna a doplnky jen zblizka
				var mi := ch as MeshInstance3D
				if typ == "Rychta" and cn.ends_with("_Vnejsek"):
					_rychta_tram_pryc(mi)
				# Misa 0.83 „domy se na dohled nedokresluji“: hruby obal od 60 m byl videt jako hneda krabice -
				# podrobny vnejsek do 130 m (tablet ve vsi 47 FPS), drobne/vnitrek dal jen zblizka
				# Misa 0.92 (rybnik 1330 kresleni, z toho domy vsi 420): na tabletu podrobny vnejsek (~22 materialu) do 75 m
				var dal := 75.0 if (OS.has_feature("mobile") or OS.has_environment("TVRZ_MOBIL")) else 130.0
				if cn.ends_with("_Daleko"):
					mi.visibility_range_begin = dal
				elif cn.ends_with("Interier") or cn.ends_with("Drobne"):
					mi.visibility_range_end = 35.0 if cn.ends_with("Interier") else minf(70.0, dal - 15.0)
				else:
					mi.visibility_range_end = dal
				if cn.ends_with("Interier"):
					mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				# Misa 0.92 (stin domu vsi 186 kresleni u rybnika): stin vrha jen hruby dum (2 materialy) - kopie _Daleko
				# „jen stin“ do dosahu stinu; podrobny vnejsek a drobne stin nevrhaji
				if cn.ends_with("_Daleko"):
					var sd := MeshInstance3D.new()
					sd.name = cn + "_Stin"
					sd.mesh = mi.mesh
					sd.transform = mi.transform
					for si in mi.get_surface_override_material_count():
						sd.set_surface_override_material(si, mi.get_surface_override_material(si))
					sd.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
					sd.visibility_range_end = dal
					dum.add_child.call_deferred(sd)
				elif not cn.ends_with("Interier"):
					mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if cn.contains("_Dvere") and ch is MeshInstance3D:
				var dv := ch as MeshInstance3D
				var dk := cn.split("_Dvere")[1].trim_prefix("_")
				var jm := "Pohyb_dum_%d_%s" % [int(d["k"]), dk]
				dv.name = jm
				var ab := dv.mesh.get_aabb()
				var cl := ab.get_center()
				# dovnitr: kridlo se otoci k sini (ven z chleva do chleva)
				var cil := Vector3(0.0, 0.0, kom_z if cn.ends_with("ChlevVen") else sin_z)
				var otev := 100.0
				var p_plus := dv.position + Basis(Vector3.UP, deg_to_rad(otev)) * cl
				var p_minus := dv.position + Basis(Vector3.UP, deg_to_rad(-otev)) * cl
				if Vector2(p_minus.x, p_minus.z).distance_to(Vector2(cil.x, cil.z)) < Vector2(p_plus.x, p_plus.z).distance_to(Vector2(cil.x, cil.z)):
					otev = -otev
				var use := xf * (dv.position + cl + Vector3(0, 0.95 - cl.y, 0))
				var vstup := cn.ends_with("Vstup")
				data["pohyb"].append({"name": jm, "kind": "dvere", "group": "dum_%d_%s" % [int(d["k"]), dk],
						"cols": [[cl.x, cl.y, cl.z, ab.size.x, ab.size.y, maxf(ab.size.z, 0.06)]],
						"pos": [use.x, use.y, use.z], "use": [use.x, use.y, use.z], "open": otev, "init": otev if vstup else 0.0, "dur": 1.0})
		# mistnosti (otocene jako stare chalupy: stred podlahy, rozmery v ramci domu)
		var yaw := PI / 2.0 - atan2(float((d["au"] as Vector2).y), float((d["au"] as Vector2).x))
		for r: Array in ([["jizba", "Jizba", 0.2], ["sin", "Síň", 0.16], ["komora", String(m["komora_t"]), 0.14]] if m.has("jizba") else []):
			var zz: Array = m[r[0]]
			var ix := float(m["ix"]) if not (typ == "Rychta" and r[0] == "komora") else 2.2
			var podl := float(m["pod"]) + (-0.75 if typ == "Rychta" and r[0] == "komora" else 0.0)
			var stred := xf * Vector3(0.0, podl, (float(zz[0]) + float(zz[1])) * 0.5)
			data["mistnosti"].append({"name": "dum_%d_%s" % [int(d["k"]), r[0]], "title": "%s – %s" % [r[1], nazev],
					"pos": [stred.x, stred.y, stred.z], "size": [ix * 2.0, 2.3, absf(float(zz[1]) - float(zz[0]))], "yaw": yaw,
					"ambient": [r[2], r[2] * 0.92, r[2] * 0.8]})
		# ohen v peci (emisni M_Zhar modelu): svetlo a zar
		var zhar := _dum_zhar(dum)
		if zhar != Vector3.INF:
			var zp := xf * zhar
			data["ohne"].append({"kind": "hearth", "pos": [zp.x, zp.y, zp.z], "name": "ohen_dum_%d" % int(d["k"]), "size": 0.4,
					"zap": int(d["k"]) % 2 == 1 or typ == "Rychta", "svetlo": [0.0, 0.5, 0.0]})
		if m.has("ix"):
			_zahrada(d)
		if DUM_ZEBRIK.has(typ):
			var zz: Array = DUM_ZEBRIK[typ]
			zebrik_use({"pata": xf * (zz[0] as Vector3), "vrchol": xf * (zz[1] as Vector3), "nastup": xf * (zz[2] as Vector3),
					"sestup": xf * (zz[3] as Vector3)})
		for v: Array in DUM_VYB.get(typ, []):
			var wp := xf * Vector3(float(v[1]), float(m["pod"]) + float(v[4]), float(v[2]))
			data["vybaveni"].append({"id": v[0], "p": [wp.x, wp.y, wp.z], "yaw": yaw + float(v[3])})
		# drevo u domu (Misa 27. 10.: nove hranice podle KCD1, kazdy dum jinak): [id, strana (-1 dvur / +1 vstup / 0 zadni
		# stit), poloha podel steny (0..1 od stitu do navsi k zadu), odstup od zdi m, pootoceni]
		if _kat_p.is_empty() and FileAccess.file_exists("res://modely/predmety.json"):
			_kat_p = JSON.parse_string(FileAccess.get_file_as_string("res://modely/predmety.json"))
		var kat_p: Dictionary = _kat_p
		for v2: Array in DUM_DREVO.get(int(d["k"]), []):
			var rz2: Array = (kat_p.get(String(v2[0]), {}) as Dictionary).get("rozmer", [1.5, 0.8, 0.5])
			var hl := float(rz2[2]) * 0.5 + float(v2[3])
			var lp := Vector3.ZERO
			var yl := 0.0
			if int(v2[1]) == 0:
				lp = Vector3(lerpf(-float(m["hw"]), float(m["hw"]), float(v2[2])), 0.0, float(m["b"]) - hl)
				yl = 0.0
			else:
				lp = Vector3(float(v2[1]) * (float(m["hw"]) + hl), 0.0, lerpf(float(m["b"]) + 0.8, float(m["f"]) - 0.8, float(v2[2])))
				yl = PI / 2.0
			var wq := xf * lp
			# smer podel zdi (posun mimo pesiny v kroku 9, _vybaveni_mimo_cest) a pulrozmery pudorysu
			var podel := (xf.basis * (Vector3.RIGHT if int(v2[1]) == 0 else Vector3.BACK)).normalized()
			data["vybaveni"].append({"id": v2[0], "p": [wq.x, _vyska_min(wq.x, wq.z, 0.8) - 0.03, wq.z], "yaw": yaw + yl + float(v2[4]),
					"podel_zdi": [podel.x, podel.z], "pul": [float(rz2[0]) * 0.5, float(rz2[2]) * 0.5]})
	sc.free()
	print("ves: %d novych domu, %d ms" % [_domy.size(), Time.get_ticks_msec() - t0])


## Chyse na skutecnou sit terenu (vyska z trojuhelniku siti Teren*, ne z mrizky 2 m): prkenna zidkou na nejnizsim
## bode (do svahu zapustena); kurova (kuly 0,29 m v zemi) mezi dolnim a hornim rohem.
func _chyse_na_sit(root: Node3D) -> void:
	var body: Array = []
	for d: Dictionary in _domy:
		if not d["m"].has("t_pas"):
			continue
		var m: Dictionary = d["m"]
		for qx in [-1.0, 0.0, 1.0]:
			for qz in [float(m["b"]), 0.0, float(m["f"]), float(m["ft"])]:
				var w: Vector3 = (d["xf"] as Transform3D) * Vector3(qx * float(m["hw"]), 0.0, qz)
				body.append([d, Vector2(w.x, w.z), -INF])
	if body.is_empty():
		return
	for t in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(t.name)
		if nm == "Teren_obzor" or nm.begins_with("Teren_cesta_kamen") or nm.ends_with("_sukne"):
			continue
		var mi := t as MeshInstance3D
		if mi.mesh == null:
			continue
		var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
		var ab := xf * mi.mesh.get_aabb()
		var fc := PackedVector3Array()
		for b: Array in body:
			var p: Vector2 = b[1]
			if p.x >= ab.position.x and p.x <= ab.end.x and p.y >= ab.position.z and p.y <= ab.end.z:
				fc = mi.mesh.get_faces()
				break
		for i in range(0, fc.size(), 3):
			var a := xf * fc[i]
			var bb := xf * fc[i + 1]
			var c := xf * fc[i + 2]
			var x0 := minf(a.x, minf(bb.x, c.x))
			var x1 := maxf(a.x, maxf(bb.x, c.x))
			var z0 := minf(a.z, minf(bb.z, c.z))
			var z1 := maxf(a.z, maxf(bb.z, c.z))
			for b: Array in body:
				var p: Vector2 = b[1]
				if p.x < x0 or p.x > x1 or p.y < z0 or p.y > z1:
					continue
				var v0 := Vector2(bb.x - a.x, bb.z - a.z)
				var v1 := Vector2(c.x - a.x, c.z - a.z)
				var v2 := p - Vector2(a.x, a.z)
				var den := v0.x * v1.y - v1.x * v0.y
				if absf(den) < 1e-9:
					continue
				var u := (v2.x * v1.y - v1.x * v2.y) / den
				var w2 := (v0.x * v2.y - v2.x * v0.y) / den
				if u < -0.001 or w2 < -0.001 or u + w2 > 1.001:
					continue
				b[2] = maxf(float(b[2]), a.y + u * (bb.y - a.y) + w2 * (c.y - a.y))
	for d: Dictionary in _domy:
		if not d["m"].has("t_pas"):
			continue
		var mn := INF
		var mx := -INF
		for b: Array in body:
			if b[0] == d and float(b[2]) > -INF:
				mn = minf(mn, float(b[2]))
				mx = maxf(mx, float(b[2]))
		if mn == INF:
			continue
		# place_building: podlaha nad nejvyssim bodem (+0,05), svah vetsi nez zidka (0,5) / kuly v zemi (0,29) = varovani
		var pod := float(d["m"]["pod"])
		var hloubka := pod if pod > 0.2 else 0.29
		# chyse nema podezdivku pod podlahou: prkenna zidkou na nejnizsim bode (nic nevisi), kurova podlahou nad nejvyssim
		var y0 := mn - 0.01 if pod > 0.2 else mx + 0.03
		if mx - mn > hloubka:
			push_warning("chyse %s_%d: svah %.2f m vetsi nez podezdivka %.2f m - presunout" % [d["typ"], d["k"], mx + 0.05 - mn, hloubka])
		var xf2: Transform3D = d["xf"]
		xf2.origin.y = y0
		d["xf"] = xf2
		d["inv"] = xf2.affine_inverse()
		d["y"] = y0
		print("chyse %s_%d: sit %.2f..%.2f -> y %.2f" % [d["typ"], d["k"], mn, mx, y0])


## Zahradka u domu (Misa 25. 10., fotky KCD): na strane vstupu mezi domem a plotem stare usedlosti vyvysene zahony
## s proutenym lemem (zeli, salat, cibule, mrkev, zryty - blender/vlastni.py zahon), od chodnicku oddelene proutenym
## plutkem s mezerou; zahony na terenu na 4 body (naklon), plutek svisle. Kvetiny u zdi: _kvetiny_zahrad.
const PLODINY := ["zahon_zeli", "zahon_cibule", "zahon_salat", "zahon_mrkev", "zahon_zeli", "zahon_prazdny", "zahon_cibule"]


func _zahrada(d: Dictionary) -> void:
	var m: Dictionary = d["m"]
	var xf: Transform3D = d["xf"]
	var yaw := PI / 2.0 - atan2(float((d["au"] as Vector2).y), float((d["au"] as Vector2).x))
	var hw := float(m["hw"])
	var f := float(m["f"])
	var x0 := hw + 2.0                                       # za chodnickem od vstupu (x ~ hw + 1,4)
	var x1 := float(d["W"]) * 0.5 + 5.8                      # plot zahrady stare usedlosti (W/2 + 6,2)
	var z0 := maxf(float(m["b"]), f - float(d["L"]) + 0.8) + 0.2
	var z1 := f - 0.6
	var rng := RandomNumberGenerator.new()
	rng.seed = int(d["k"]) * 131
	var n := 0
	var zahony: Array = []
	var x := x0 + 0.62
	while x + 0.6 <= x1:
		var z := z0 + 1.55
		while z + 1.55 <= z1:
			var id: String = PLODINY[rng.randi() % PLODINY.size()]
			var w := xf * Vector3(x, 0.0, z)
			var yz := yaw + PI / 2.0 + (PI if rng.randf() < 0.5 else 0.0) + rng.randf_range(-0.03, 0.03)
			var pb := polozit_na_body(w.x, w.z, yz, opory("", 3.07, 1.17))
			# hlina zahonu o 3 cm v zemi (lem z proutí zapichnuty)
			data["vybaveni"].append({"id": id, "p": [pb[0].x, pb[0].y - 0.03, pb[0].z], "yaw": yz, "up": [pb[1].x, pb[1].y, pb[1].z]})
			zahony.append(Vector2(x, z))
			n += 1
			z += 3.07 + rng.randf_range(0.45, 0.6)
		x += 1.17 + rng.randf_range(0.42, 0.55)
	if n == 0:
		return
	var sx := xf * Vector3((x0 + x1) * 0.5, 0.0, (z0 + z1) * 0.5)
	_nove_zahrady.append([xf.affine_inverse(), Vector2(sx.x, sx.z), x0 - 0.4, x1 + 0.3, z0 - 0.2, z1 + 0.4, zahony])
	# plutek mezi chodnickem a zahony, uprostred mezera (vstup do zahrady)
	var zp := z0
	var mezera := (z0 + z1) * 0.5
	while zp + 2.07 <= z1 + 0.2:
		if absf(zp + 1.03 - mezera) > 1.2:
			var w2 := xf * Vector3(x0 - 0.3, 0.0, zp + 1.03)
			var yp := yaw + PI / 2.0
			data["vybaveni"].append({"id": "plutek", "p": [w2.x, pata_lom(w2.x, w2.z, yp, 2.07, 0.07) - 0.02, w2.z], "yaw": yp})
		zp += 2.1
	_zahrady_kvety.append([d, x0, z0, z1])


var _zahrady_kvety: Array = []


## Kvetiny zahrad: u zdi domu na strane zahrady a podel plutku (kopretiny, bile kvety), mimo dvere a chodnicek.
func _kvetiny_zahrad() -> void:
	var r: Dictionary = data["rostliny"]
	if not r.has("kopretiny_0") or not r.has("kvety_bile_0"):
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 2511
	var n := 0
	for zk: Array in _zahrady_kvety:
		var d: Dictionary = zk[0]
		var m: Dictionary = d["m"]
		var xf: Transform3D = d["xf"]
		var hw := float(m["hw"])
		var zv := float(m["vstup"])
		for _i in 40:
			var z := rng.randf_range(float(m["b"]) + 0.4, float(m["f"]) - 0.4)
			if absf(z - zv) < 1.3:
				continue
			var lx := hw + rng.randf_range(0.25, 0.7) if rng.randf() < 0.6 else float(zk[1]) - rng.randf_range(0.45, 0.7)
			var w := xf * Vector3(lx, 0.0, z)
			var k := "kopretiny_0" if rng.randf() < 0.55 else "kvety_bile_0"
			if not druh_smi_hra(k, w.x, w.z):
				continue                                    # ne na cesticce, ve vstupu (Misa 0.98: bila bylina na ceste)
			(r[k] as Array).append(_xf(w.x, _vyska(w.x, w.z) - 0.02, w.z, rng.randf() * TAU, rng.randf_range(0.8, 1.2)))
			n += 1
	print("zahrady: %d kvetin" % n)


func _dum_zhar(dum: Node3D) -> Vector3:
	for ch in dum.get_children():
		if ch is MeshInstance3D and (String(ch.name).ends_with("Interier") or String(ch.name).ends_with("Drobne")):
			var me := (ch as MeshInstance3D).mesh
			for s in me.get_surface_count():
				var mt := me.surface_get_material(s)
				if mt and String(mt.resource_name).begins_with("M_Zhar"):
					var vv: PackedVector3Array = me.surface_get_arrays(s)[Mesh.ARRAY_VERTEX]
					var ab := AABB(vv[0], Vector3.ZERO)
					for p in vv:
						ab = ab.expand(p)
					return ab.get_center()
	return Vector3.INF


## Znameni krcmy (vesnice.py cottage sign: vechet z chvoji na tyci nad dvermi, Misa 0.78 "hnusna kvetina nad
## vchodem, smazat"): tyc (a -> b), vzpera, provaz a chvoji.
const VECHET_A := Vector2(459.47, 775.90)
const VECHET_B := Vector2(458.55, 775.12)


func _vechet(c: Vector3, mat: String) -> bool:
	var p := Vector2(c.x, c.z)
	if p.distance_to(VECHET_B) > 2.2:
		return false
	if mat.begins_with("chvoji") or mat.begins_with("provaz"):
		return true
	return mat.begins_with("dub_ven") and Geometry2D.get_closest_point_to_segment(p, VECHET_A, VECHET_B).distance_to(p) < 0.12 \
			and c.y > _vyska(c.x, c.z) + 1.8


## Souvisle kusy site: index kusu pro kazdy trojuhelnik (spolecne vrcholy podle indexu i polohy, union-find).
static func _kusy_trojuhelniku(v: PackedVector3Array, idx: PackedInt32Array) -> PackedInt32Array:
	var par: Array = range(v.size())            # Array je odkaz (Packed* by se v pomocne funkci kopiroval)
	var poloha := {}
	for i in v.size():
		var k := Vector3i(roundi(v[i].x * 200.0), roundi(v[i].y * 200.0), roundi(v[i].z * 200.0))
		if poloha.has(k):
			par[_uf_koren_a(par, i)] = _uf_koren_a(par, int(poloha[k]))
		else:
			poloha[k] = i
	for t in idx.size() / 3:
		var r0 := _uf_koren_a(par, idx[t * 3])
		for j in [1, 2]:
			var rj := _uf_koren_a(par, idx[t * 3 + j])
			if rj != r0:
				par[rj] = r0
	var out := PackedInt32Array()
	out.resize(idx.size() / 3)
	for t in idx.size() / 3:
		out[t] = _uf_koren_a(par, idx[t * 3])
	return out


static func _uf_koren_a(par: Array, a: int) -> int:
	while int(par[a]) != a:
		par[a] = par[int(par[a])]
		a = int(par[a])
	return a


## Site Vesnice (chalupy, sudy, hranice), Vesnice_ploty a Vesnice_zahrady: trojuhelniky starych chalup a vse v pudorysu
## novych domu pryc.
func _ves_site_vyrez(root: Node3D) -> void:
	var n := 0
	for nm: String in ["Vesnice", "Vesnice_ploty", "Vesnice_zahrady"]:
		var mi := root.find_child(nm, true, false) as MeshInstance3D
		if mi == null or not (mi.mesh is ArrayMesh):
			continue
		var am := mi.mesh as ArrayMesh
		var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
		var nove := ArrayMesh.new()
		var prenes: Array = []
		for si in am.get_surface_count():
			var arr := am.surface_get_arrays(si)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
			var ni := PackedInt32Array()
			# ploty stare vsi: cely kus (zerd, sloupek - souvisle trojuhelniky), ktery zasahuje na hlinu nove cesty nebo do
			# pruchodu, pryc (Misa 28. 10. „hneda klada pres cestu“ - zerd stareho plotu pres ulici nove vsi)
			var kus_pryc := {}
			var kus := PackedInt32Array()
			if nm == "Vesnice_ploty":
				kus = _kusy_trojuhelniku(v, idx)
				var od_domu := float(Pravidla.cti("lokace", "ves", "plot_od_domu_m"))
				var kus_blizko := {}
				for t in idx.size() / 3:
					var c0 := xf * ((v[idx[t * 3]] + v[idx[t * 3 + 1]] + v[idx[t * 3 + 2]]) / 3.0)
					if cesta_kraj_osa(c0.x, c0.z).x < 0.0 or v_pruchodu(c0.x, c0.z):
						kus_pryc[kus[t]] = true
					if not kus_blizko.has(kus[t]):
						for u0: Dictionary in Pravidla.cti("lokace", "ves", "usedlosti"):     # vsechny usedlosti vcetne krcmy
							if Vector2(float(u0["novy_stred"][0]), float(u0["novy_stred"][1])).distance_to(Vector2(c0.x, c0.z)) < od_domu:
								kus_blizko[kus[t]] = true
								break
				# plot, ktery nepatri k zadnemu domu nove vsi (zbytek stare vsi, Misa 28. 10. „hneda klada“): pryc
				for t in idx.size() / 3:
					if not kus_blizko.has(kus[t]):
						kus_pryc[kus[t]] = true
			for t in idx.size() / 3:
				var c := xf * ((v[idx[t * 3]] + v[idx[t * 3 + 1]] + v[idx[t * 3 + 2]]) / 3.0)
				if not kus.is_empty() and kus_pryc.has(kus[t]):
					n += 1
					continue
				if _dum_zabira(c.x, c.z, 0.15, nm == "Vesnice") or (nm == "Vesnice_zahrady" and _v_stare_zahrade(c.x, c.z)) \
						or (nm == "Vesnice" and _vechet(c, String(am.surface_get_material(si).resource_name) if am.surface_get_material(si) else "")):
					n += 1
					continue
				ni.append(idx[t * 3])
				ni.append(idx[t * 3 + 1])
				ni.append(idx[t * 3 + 2])
			if ni.is_empty():
				continue
			arr[Mesh.ARRAY_INDEX] = ni
			nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
			nove.surface_set_material(nove.get_surface_count() - 1, am.surface_get_material(si))
			nove.surface_set_name(nove.get_surface_count() - 1, am.surface_get_name(si))
			prenes.append(mi.get_surface_override_material(si))
		mi.mesh = nove
		# materialy hry (override) jdou podle poradi povrchu - po vynechani prazdnych povrchu se posunuly a stodoly
		# zustaly s holym materialem z exportu (Misa 0.83 „nektere domky divna textura“, hnede krabice)
		for i in prenes.size():
			mi.set_surface_override_material(i, prenes[i])
	print("ves: %d trojuhelniku starych chalup pryc" % n)


## CESTY = TVAR, NE TEXTURA (radce 18:00, Misa 25. 10.: reference KCD2 + obraz lesni cesty). Reserse (docs/predani.md):
## CryEngine road = spline nad terenem, okraj do trav prolnuty podle vysky textury (height blend), ne linearne;
## BeamNG road spline = podklad + vrstvy opotrebeni (vyjete koleje) + prechodove pasy, teren pod cestou zapusteny;
## masky v barve vrcholu (trava, louze) potrebuji hustou sit. Dnes je cesta primo teren (_cesty_do_terenu: CUSTOM0/1
## ve vrcholech, koleje, val, louze, rozbity okraj); osy a sirky z pravidla/svet/cesty.json (krok A), pas Teren_cesta
## z Blenderu se nekresli (zustava jen kolize).
var cesty_osy: Array = []            # [{p: PackedVector2Array, y: PackedFloat32Array, w: PackedFloat32Array, k: float}]
var _cesty_mriz := {}                # Vector2i(4 m) -> [[osa, i]]
var _ter_tri := {}                   # trojuhelniky terenu u cest (vyska pro zapusteni)


static func _vln(x: float) -> float:
	return sin(x) * 0.55 + sin(x * 2.31 + 1.7) * 0.3 + sin(x * 5.13 + 0.4) * 0.15


## Profil napric: lat (m od osy, znamenko = strana), hw pulsirka hliny, s podel osy, o = opotrebeni bodu osy
## (x koleje 0..1, y travnaty hrbet 0..1, z bahno 0..1, w vymleti 0..1 - _cesty_opotrebeni, z provozu).
## Radce 18:20: koleje jen detail (5-15 cm, mistami prerusene); hlavni je nerovny povrch hliny s kameny.
## Vraci (dy od vysky osy, trava 0..1, louze/bahno pro barvu a, vzdalenost od stredu koleje).
static func cesta_profil(lat: float, hw: float, s: float, o: Vector4) -> Vector4:
	var a := absf(lat)
	var sd := 1.0 if lat >= 0.0 else -1.0
	var n1 := _vln(s * 0.11 + sd * 3.1)
	var dy := 0.0
	var g := 0.02
	var mok := 0.0
	var roz := clampf(hw * 0.42, 0.55, 0.78) + 0.05 * n1
	var dk := a - roz
	# nerovny povrch: hrboly a prohlubne 0,3-2 m (hlavni charakter), vymleti ve svahu hlubsi rygoly
	dy += (0.035 + 0.03 * o.w) * _vln(s * 0.61 + lat * 1.9) * _vln(s * 0.23 - lat * 0.8 + 2.0)
	dy += 0.02 * sin(s * 1.7 + lat * 5.3) * sin(s * 0.63 - lat * 2.1)
	if o.x > 0.01:
		# Misa 0.81 „jen rastr, na fotkach maji hloubku“: koleje 8-12 cm, okraje kolej vyhrnute, hrbet mezi nimi
		# Misa 0.83 „kolejiste to kazi“ (fotky KCD2: koleje melke, siroke, prerusovane - ne tmave ryhy): 3-5 cm,
		# mekky profil 0,8 m, bez ostre hrany
		var r := 1.0 - smoothstep(0.08, 0.42, absf(dk))
		dy -= o.x * (0.04 + 0.03 * o.z + 0.012 * n1 + 0.008 * _vln(s * 0.37 + sd * 7.7)) * r * r * (3.0 - 2.0 * r)   # v bahne hlubsi
		dy += o.x * 0.01 * smoothstep(0.3, 0.45, absf(dk)) * (1.0 - smoothstep(0.45, 0.7, absf(dk)))
		mok = smoothstep(0.66, 0.88, _vln(s * 0.09 + sd * 1.7 + 4.0) * 0.5 + 0.5) * r * (0.4 + 0.6 * o.z)
		dy -= 0.03 * mok
	var hrb := 1.0 - smoothstep(roz - 0.34, roz - 0.17, a)
	dy += o.x * 0.015 * hrb
	# vymoly (Misa 0.81: kaluze, diry, kaminky, kameny - kazdy usek jiny): bunky po 5 m podel, v kazde jeden vymol
	# s pravdepodobnosti podle useku; 0,4-1 m polomer, 5-12 cm hluboko, na dne kaluz (rovina nebo bahno u vody)
	var uv := cesta_useky(s)
	var c0 := floori(s / 5.0)
	for c in range(c0 - 1, c0 + 2):
		var h1 := fposmod(sin(c * 12.9898) * 43758.5453, 1.0)
		if h1 > uv.y * 0.85:
			continue
		var h2 := fposmod(sin(c * 78.233) * 12345.678, 1.0)
		var h3 := fposmod(sin(c * 39.425) * 24634.633, 1.0)
		var rr := 0.4 + 0.6 * h3
		var dd := Vector2(s - (c + 0.5 * (1.0 + h2 - 0.5)) * 5.0, lat - (h2 * 2.0 - 1.0) * hw * 0.65)
		var dl := dd.length() / rr
		if dl < 1.0:
			var hl := (0.05 + 0.07 * h1 / maxf(uv.y, 0.01)) * (1.0 - smoothstep(0.35, 1.0, dl))
			dy -= hl
			mok = maxf(mok, (1.0 - smoothstep(0.45, 0.7, dl)) * (0.55 + 0.45 * o.z) * (1.0 if h3 + o.z >= 0.3 else 0.0))
	g = maxf(g, hrb * o.y * clampf(0.7 * _vln(s * 0.23 + 11.0), 0.0, 0.9) * 0.22)       # hrbet jen misty a ridce (Misa 0.85 rady trsu)
	mok = maxf(mok, o.z * 0.5 * (1.0 - smoothstep(hw - 0.3, hw + 0.2, a)))                # bahnite useky u vody
	var ok := cesta_ok(hw, s, sd)
	g = maxf(g, smoothstep(ok - 0.35, ok + 0.05, a))          # za okrajem sit nekresli (zem.gdshader discard), je videt teren
	return Vector4(dy, g, mok, dk if o.x > 0.01 else 9.0)


## Vyrovnany podelny profil cest (Misa 0.84 „kousek pred hospodou moc prudky kopec“: teren pod cestou 66 %, brehy
## u brodu 34 %): vyska osy z terenu, klouzavy prumer 16 m, sklon nejvys 14 % (vpred a vzad, prumer obou), rozdil proti
## terenu = zarez / nasyp (o["dl"], nejvys 5 m, ke koncum os 0 - navaznost na krizovatky a stavby). Teren pod cestou
## a do 8 m za okraj (_cesty_teren), vyska cesty (cesta_y) i mrizka _vyska (stromy, kere, stavby) se posunou.
const CESTA_SKLON := 0.14


func _cesty_profil() -> void:
	var nej := 0.0
	for o: Dictionary in cesty_osy:
		var pp: PackedVector2Array = o["p"]
		var n := pp.size()
		var h := PackedFloat32Array()
		h.resize(n)
		for i in n:
			var ty := _tri_vyska(_ter_tri, pp[i].x, pp[i].y)
			h[i] = ty if ty != INF else _vyska(pp[i].x, pp[i].y)
		var sm := PackedFloat32Array()
		sm.resize(n)
		for i in n:
			var a := maxi(i - 10, 0)
			var b := mini(i + 10, n - 1)
			var su := 0.0
			for j in range(a, b + 1):
				su += h[j]
			sm[i] = su / float(b - a + 1)
		var g := CESTA_SKLON * 0.8
		var tf := sm.duplicate()
		for i in range(1, n):
			tf[i] = clampf(tf[i], tf[i - 1] - g, tf[i - 1] + g)
		var tb := sm.duplicate()
		for i in range(n - 2, -1, -1):
			tb[i] = clampf(tb[i], tb[i + 1] - g, tb[i + 1] + g)
		var dl := PackedFloat32Array()
		dl.resize(n)
		# Misa 0.85: krizovatky a udusana mista (hostinec, brana, lom) zustavaji na terenu - jinak schod 5 m mezi osami
		# (kazdy vrchol terenu bere zmenu nejblizsi osy) a cesta zariznuta pod dvur hostince. Kotva rozmazana +-12 m.
		var kt: PackedFloat32Array = o.get("kotva", PackedFloat32Array())
		for i in n:
			var konec := minf(float(i), float(n - 1 - i)) * 0.8
			var kv := 0.0
			for j in range(maxi(i - 15, 0), mini(i + 16, kt.size())):
				kv = maxf(kv, kt[j] * (1.0 - absf(float(j - i)) / 16.0))
			dl[i] = clampf((tf[i] + tb[i]) * 0.5 - h[i], -3.0, 3.0) * smoothstep(0.0, 12.0, konec) * (1.0 - smoothstep(0.2, 0.7, kv))
			nej = maxf(nej, absf(dl[i]))
		if bool(o.get("ves", false)):
			# ulice vsi lezi na terenu (Misa 27. 10. „cesta jakoby v brehu“: vyrovnani mezi dvory delalo nasyp az 3 m) -
			# vysapana cesta kopiruje teren, jen ostre hrbolky se zahladi (do 0,25 m)
			for i in n:
				dl[i] = clampf(dl[i], -0.25, 0.25)
		o["dl"] = dl
	print("cesty: profil vyrovnan, nejvetsi zarez/nasyp %.2f m" % nej)


## Mrizka vysek _vyska (trava_ves, trava_kraj; cm v int16) podle vyrovnaneho profilu - stromy, kere, kameny a stavby
## kolem cest sedi na novem terenu.
func _cesty_vys_mrizka() -> void:
	_vyska(0.0, 0.0)
	var n := 0
	for key: String in _vys:
		var g: Dictionary = _vys[key]
		var k := float(g["k"])
		var nx: int = g["nx"]
		var nz: int = g["nz"]
		var ys: PackedByteArray = g["y"]
		var hotovo := {}
		for c: Vector2i in _cesty_mriz:
			var i0 := floori((c.x * 4.0 - float(g["x0"])) / k)
			var j0 := floori((c.y * 4.0 - float(g["z0"])) / k)
			for i in range(i0, i0 + int(ceil(4.0 / k)) + 1):
				for j in range(j0, j0 + int(ceil(4.0 / k)) + 1):
					if i < 0 or j < 0 or i >= nx or j >= nz or hotovo.has(Vector2i(i, j)):
						continue
					hotovo[Vector2i(i, j)] = true
					var x := float(g["x0"]) + i * k
					var z := float(g["z0"]) + j * k
					var l := cesta_lat(x, z)
					if l.is_empty() or absf(float(l[5])) < 0.01:
						continue
					var dlt := float(l[5]) * (1.0 - smoothstep(float(l[1]) + 1.0, float(l[1]) + 12.0, absf(float(l[0]))))
					var o2 := (j * nx + i) * 2
					ys.encode_s16(o2, clampi(ys.decode_s16(o2) + roundi(dlt * 100.0), -32768, 32767))
					n += 1
		g["y"] = ys
	print("cesty: mrizka vysek upravena v %d bodech" % n)


## Napojeni koncu os (Misa 0.84 „logicka navaznost cest, krizovatek“; slepe konce s hranatou plochou u lomu, u vsi):
## konec osy do 14 m od jine osy se prodlouzi az do jeji stredove cary + 1,5 m dal (pod jejim povrchem, cesta_y konec
## zapusti), smer plynule zahnuty k napojeni. Konce na samotne ceste (napr. u vsi) se nemeni.
func _cesty_napoj() -> void:
	var n := 0
	for oi in cesty_osy.size():
		var o: Dictionary = cesty_osy[oi]
		for konec in 2:
			var pp: PackedVector2Array = o["p"]
			var ys: PackedFloat32Array = o["y"]
			var ws: PackedFloat32Array = o["w"]
			var k := 0 if konec == 0 else pp.size() - 1
			var e := pp[k]
			var dovnitr := (pp[mini(k + 6, pp.size() - 1)] - e if konec == 0 else pp[maxi(k - 6, 0)] - e).normalized()
			var best := Vector2.INF
			# pesiny k domum jen kratce (konec u dveri nikam), cesty az 30 m (lom - cesta od vsi, Misa 0.88)
			var bd := 6.0 if bool(o.get("pesina", false)) else 30.0
			for oj in cesty_osy.size():
				if oj == oi or bool((cesty_osy[oj] as Dictionary).get("pesina", false)):
					continue
				var p2: PackedVector2Array = (cesty_osy[oj] as Dictionary)["p"]
				for j in p2.size():
					var d := p2[j].distance_to(e)
					# ne zpet podel vlastni osy (osa, ktera pokracuje stejnym smerem, se napoji na svuj konec)
					if d < bd and d > 0.4 and (p2[j] - e).normalized().dot(dovnitr) < 0.3:
						bd = d
						best = p2[j]
			if best == Vector2.INF:
				continue
			var smer := (best - e).normalized()
			var cil := best + smer * 1.5
			var m := int(e.distance_to(cil) / 0.8)
			var np := PackedVector3Array()
			var nw := PackedFloat32Array()
			for q in pp.size():
				np.append(Vector3(pp[q].x, ys[q], pp[q].y))
				nw.append(ws[q])
			var pridat := PackedVector3Array()
			for t in range(1, m + 1):
				var q := e.lerp(cil, float(t) / m)
				pridat.append(Vector3(q.x, _vyska(q.x, q.y), q.y))
			if konec == 0:
				pridat.reverse()
				var vse := pridat
				vse.append_array(np)
				np = vse
				var w2 := PackedFloat32Array()
				w2.resize(pridat.size())
				w2.fill(ws[0])
				w2.append_array(nw)
				nw = w2
			else:
				np.append_array(pridat)
				for _t in pridat.size():
					nw.append(ws[ws.size() - 1])
			var ves := bool(o.get("ves", false))
			o.merge(_osa_prevzorkuj(np, nw, 1.0), true)
			o["ves"] = ves
			n += 1
	print("cesty: %d koncu napojeno" % n)


## Useky podel cesty (Misa 0.81): (koleje navic, vymoly 0..1, kamenitost 0..1) - kazdy usek jiny, plynule 20-90 m.
static func cesta_useky(s: float) -> Vector3:
	return Vector3(0.0, smoothstep(0.15, 0.55, _vln(s * 0.017 + 4.1)), smoothstep(0.2, 0.6, _vln(s * 0.021 + 7.7)))


## Okraj hliny (Misa 0.80 fotky KCD2: rozbity, jazyky hliny do travy a trava do hliny, zadna rovna hrana).
static func cesta_ok(hw: float, s: float, sd: float) -> float:
	return hw * (1.0 + 0.16 * _vln(s * 0.13 + sd * 5.0) + 0.08 * _vln(s * 0.55 + sd)) + 0.25 * _vln(s * 1.9 + sd * 2.0)


## Vyska povrchu cesty (Misa 0.80 „rozvaleny beton“): cesta lezi NA terenu (KCD2/CryEngine: road = textura a lehke
## zplosteni na terenu, zadny pas s vlastni vyskou). Puvodni teren + 2 cm, uvnitr +5 cm s hrboly, koleje jen do dna
## +2 cm; ke kraji zvednuti mizi -> okraj splyne s terenem, zadny schod ani val.
func cesta_y(x: float, z: float, a: float, ok: float, dy: float, s := -1.0, dl := 0.0) -> float:
	var ty := _tri_vyska(_ter_tri, x, z)
	if ty == INF:
		ty = _vyska(x, z)
	return ty + dl * (1.0 - smoothstep(ok + 1.0, ok + 12.0, a)) + cesta_d(x, z, a, ok, dy, s)


## Profil cesty nad puvodnim terenem (bez vyrovnani sklonu): mirne vyklenuti hliny, koleje a hrboly (cesta_profil dy),
## relief podle vyskove mapy fotografie hliny, val na kraji (hlina odhrnuta koly do travy, fotky KCD2); ke kraji 0.
func cesta_d(x: float, z: float, a: float, ok: float, dy: float, s := -1.0) -> float:
	var zv := 1.0 - smoothstep(ok - 1.4, ok - 0.1, a)
	var val := smoothstep(ok - 0.6, ok - 0.1, a) * (1.0 - smoothstep(ok + 0.1, ok + 0.8, a))
	return zv * clampf(0.06 + dy + (cesta_disp(x, z, cesta_useky(s).z if s >= 0.0 else 0.0) - 0.5) * 0.12, -0.14, 0.2) + 0.05 * val


## Vyskova mapa povrchu cest (0..1, Poly Haven dry_ground_rocks_disp 512 px na 4 m, jako hlina_a v zem.gdshader:
## p.xz / 4). Jen cteni - vola se i z vlaken louky.
var _disp_data := PackedByteArray()
var _disp_n := 0


func cesta_disp(x: float, z: float, kmn := 0.0) -> float:
	if _disp_n == 0:
		return 0.5
	# atlas vysek 2x2 po 256 px jako cesta_atlas_a: prach (dlazdice 0, 2 m), na kamenitych usecich kameni (2, 2 m)
	var v := _disp_dl(x / 2.0, z / 2.0, 0)
	if kmn > 0.01:
		v = lerpf(v, _disp_dl(x / 2.0 + 0.37, z / 2.0 + 0.37, 2), kmn)
	return v


func _disp_dl(u: float, w: float, k: int) -> float:
	var n := _disp_n / 2
	var ox := (k % 2) * n
	var oz := (k / 2) * n
	var fx := fposmod(u, 1.0) * n - 0.5
	var fz := fposmod(w, 1.0) * n - 0.5
	var ix := floori(fx)
	var iz := floori(fz)
	var tx := fx - ix
	var tz := fz - iz
	var a := _disp_data[(oz + posmod(iz, n)) * _disp_n + ox + posmod(ix, n)]
	var b := _disp_data[(oz + posmod(iz, n)) * _disp_n + ox + posmod(ix + 1, n)]
	var c := _disp_data[(oz + posmod(iz + 1, n)) * _disp_n + ox + posmod(ix, n)]
	var d := _disp_data[(oz + posmod(iz + 1, n)) * _disp_n + ox + posmod(ix + 1, n)]
	return lerpf(lerpf(a, b, tx), lerpf(c, d, tx), tz) / 255.0


func _disp_nacti() -> void:
	var t := load("res://obrazky/cesta/cesta_atlas_disp.png") as Texture2D
	if t == null:
		return
	var im := t.get_image()
	if im.is_compressed():
		im.decompress()
	im.convert(Image.FORMAT_L8)
	# jen hrube hrboly (8 px na 2m dlazdici = ~0,5 m): jemne kaminky z vysek v siti po 0,4 m podel osy byly podelne
	# ryhy - cesta „jak uhrabana“ (Misa 0.82); jemny detail dela normalova mapa textury
	im.resize(16, 16, Image.INTERPOLATE_CUBIC)
	_disp_data = im.get_data()
	_disp_n = im.get_width()


## Vzdalenost za okrajem hliny (louka: nizka ridka trava u cesty, ne zed vysoke travy), INF daleko.
func cesta_kraj(x: float, z: float) -> float:
	var l := cesta_lat(x, z)
	if l.is_empty():
		return INF
	var lat := float(l[0])
	return absf(lat) - cesta_ok(float(l[1]), float(l[3]), 1.0 if lat >= 0.0 else -1.0)


## Pasma zasazeni (radce 27. 10. 09:55, pravidla/pravidla_sveta.json pasma): jedina tabulka odstupu pro cesty,
## budovy, vodu a skaly - cte svet (vegetace, predmety), louka.gd (drn, trsy) a test zasazeni. Nacte se v build()
## (hlavni vlakno), vlakna louky jen ctou.
var _pasma: Dictionary = {}


func pasma() -> Dictionary:
	if _pasma.is_empty():
		var j: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://pravidla/pravidla_sveta.json"))
		_pasma = j["pasma"]
	return _pasma


## Typ osy cesty pro pasma: ulice_vsi (o.ves), pesina (o.pesina), jinak vozova.
func typ_osy(oi: int) -> String:
	var o: Dictionary = cesty_osy[oi]
	return "ulice_vsi" if bool(o.get("ves", false)) else ("pesina" if bool(o.get("pesina", false)) else "vozova")


func pasmo_cesty(oi: int) -> Dictionary:
	return pasma()["cesta"][typ_osy(oi)]


## Skupina druhu rostliny pro pasma (pasma.skupiny): strom, ker, balvan, vysoka_bylina, jinak bylina.
func skupina(key: String) -> String:
	var sk: Dictionary = pasma()["skupiny"]
	for g: String in ["strom", "ker", "balvan", "vysoka_bylina"]:
		for t: String in sk[g]:
			if key.contains(t):
				return g
	return "bylina"


## Odstup druhu od kraje hliny cesty podle pasma osy (m).
func odstup_cesty(key: String, oi: int) -> float:
	var pc := pasmo_cesty(oi)
	match skupina(key):
		"strom":
			return float(pc["kmen_m"])
		"ker", "balvan":
			return float(pc["ker_od_m"])
		"vysoka_bylina":
			return float(pc["trsy_od_m"])
	return 0.0


## Bod vuci nejblizsi ceste: (vzdalenost za krajem hliny, < 0 na hline; index osy) nebo (INF, -1).
func cesta_kraj_osa(x: float, z: float) -> Vector2:
	var l := cesta_lat(x, z)
	if l.is_empty():
		return Vector2(INF, -1.0)
	var lat := float(l[0])
	return Vector2(absf(lat) - cesta_ok(float(l[1]), float(l[3]), 1.0 if lat >= 0.0 else -1.0), float(l[6]))


## Nejblizsi osa cesty: [lat se znamenkem, hw, y osy, s podel, opotrebeni Vector4, dl, index osy] nebo [] daleko.
func cesta_lat(x: float, z: float) -> Array:
	var c := Vector2i(floori(x / 4.0), floori(z / 4.0))
	var best: Array = []
	var bd := INF
	var q := Vector2(x, z)
	# bunka 4 m uz obsahuje vsechny useky do 16 m (okraj mrizky) - sousedni bunky netreba (0.89: 9x mene prace,
	# stavba cest v terenu 94 s)
	for dx in range(0, 1):
		for dz in range(0, 1):
			for e: Array in _cesty_mriz.get(c, []):
				var o: Dictionary = cesty_osy[e[0]]
				var i: int = e[1]
				var pp: PackedVector2Array = o["p"]
				if i + 1 >= pp.size():
					continue
				var a := pp[i]
				var b := pp[i + 1]
				var ab := b - a
				var t := clampf((q - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
				var d := q.distance_to(a + ab * t)
				if d < bd:
					bd = d
					var ys: PackedFloat32Array = o["y"]
					var ws: PackedFloat32Array = o["w"]
					var op: Array = o["op"]
					var dls: PackedFloat32Array = o.get("dl", PackedFloat32Array())
					best = [d * (1.0 if ab.cross(q - a) >= 0.0 else -1.0), lerpf(ws[i], ws[i + 1], t), lerpf(ys[i], ys[i + 1], t),
							float(o["s0"]) + (float(i) + t) * 0.8, (op[i] as Vector4).lerp(op[i + 1], t),
							lerpf(dls[i], dls[i + 1], t) if dls.size() > i + 1 else 0.0, int(e[0])]
	return best


## Trava na ceste (louka, vlakno): (pravdepodobnost trsu, vyska povrchu) nebo x < 0.
func cesta_trava(x: float, z: float) -> Vector2:
	var l := cesta_lat(x, z)
	if l.is_empty() or absf(float(l[0])) > float(l[1]) * 1.4 + 0.9:
		return Vector2(-1, 0)
	var pr := cesta_profil(l[0], l[1], l[3], l[4])
	var lat := float(l[0])
	var ok := cesta_ok(float(l[1]), float(l[3]), 1.0 if lat >= 0.0 else -1.0)
	# za rozbitym okrajem hliny (pas kryti az do 1,3 hw + 0,5) trava jako louka: x > 0,9 = plna trava (louka.gd)
	var za := smoothstep(ok + 0.1, ok + 0.7, absf(lat))
	return Vector2(maxf(pr.y * 0.9, za), cesta_y(x, z, absf(lat), ok, pr.x, -1.0, float(l[5])))


## Mapa opotrebeni z provozu (radce 18:15): pro kazdy bod osy (x koleje, y hrbet s travou, z bahno, w vymleti).
## Provoz: nejdelsi cesta (tvrz - hostinec - konec mapy) 1, druha 0,7, ves 0,6, kratke odbocky 0,3 (bez kolej).
## Krizovatky (jina osa do jeji sire + 3 m) a udusana mista (brana tvrze, hostinec, lom) bez kolej, sirsi;
## bahno na rovine (sklon < 2 st.) do 15 m od vody; vymleti ve svahu nad 8 st.; koleje mistami prerusene.
static var CESTA_UDUSANO: Array[Vector3] = [Vector3(0.0, 24.0, 22.0), _hostinec_udusano(), Vector3(150.0, 938.0, 30.0), Vector3(461.0, 779.0, 14.0)]


static func _hostinec_udusano() -> Vector3:
	for e: Dictionary in Pravidla.cti("lokace", "stavby"):
		if e["id"] == "hostinec":
			return Vector3(float(e["stred"][0]), float(e["stred"][1]), 26.0)     # krok B: poloha z lokace.json
	return Vector3.ZERO


func _cesty_opotrebeni() -> void:
	# provoz podle sire z Blenderu (kraj.py CESTY: hlavni 3,4 m, odbocka do vsi 2,8, ke stavbam 2,2 / 1,7) - osa se
	# na krizovatkach trha na kusy, delka o provozu nic nerika
	var provoz := {}
	for oi in cesty_osy.size():
		var wv: PackedFloat32Array = (cesty_osy[oi]["w"] as PackedFloat32Array).duplicate()
		wv.sort()
		var med := wv[wv.size() / 2]
		var pv := 1.0 if med > 2.05 else (0.7 if med > 1.65 else 0.3)
		if bool(cesty_osy[oi].get("pesina", false)):
			pv = 0.3
		if bool(cesty_osy[oi].get("ves", false)):
			pv = 0.6
		provoz[oi] = pv
	for oi in cesty_osy.size():
		var o: Dictionary = cesty_osy[oi]
		var pp: PackedVector2Array = o["p"]
		var ys: PackedFloat32Array = o["y"]
		var ws: PackedFloat32Array = o["w"]
		var pv: float = provoz[oi]
		var op: Array = []
		var kotva := PackedFloat32Array()            # krizovatka / udusane misto: teren se tu nemeni (_cesty_profil)
		kotva.resize(pp.size())
		for i in pp.size():
			var q := pp[i]
			var s := float(o["s0"]) + i * 0.8
			# krizovatka: jina osa blizko
			var kriz := 0.0
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for e: Array in _cesty_mriz.get(Vector2i(floori(q.x / 4.0) + dx, floori(q.y / 4.0) + dz), []):
						if e[0] == oi:
							continue
						var o2: Dictionary = cesty_osy[e[0]]
						var p2: PackedVector2Array = o2["p"]
						var d2 := q.distance_to(p2[e[1]])
						kriz = maxf(kriz, 1.0 - smoothstep((o2["w"] as PackedFloat32Array)[e[1]] + 1.0, (o2["w"] as PackedFloat32Array)[e[1]] + 6.0, d2))
			var udus := 0.0
			for u: Vector3 in CESTA_UDUSANO:
				udus = maxf(udus, 1.0 - smoothstep(u.z * 0.6, u.z, q.distance_to(Vector2(u.x, u.y))))
			var j0 := maxi(i - 3, 0)
			var j1 := mini(i + 3, pp.size() - 1)
			var sklon := absf(ys[j1] - ys[j0]) / maxf(pp[j0].distance_to(pp[j1]), 0.5)
			var voda := 99.0
			if koryto:
				var kb: Array = koryto.blizko(q.x, q.y)
				if not kb.is_empty():
					voda = float(kb[0]) - float(kb[2])
			var bah := (1.0 - smoothstep(10.0, 15.0, voda)) * (1.0 - smoothstep(0.03, 0.06, sklon))
			var vym := smoothstep(0.12, 0.2, sklon)
			# Misa 0.81 „koleje jsou jen nekde, neni to dogma“: koleje asi na 40 % delky v usecich 30-80 m
			var prer := smoothstep(0.0, 0.35, _vln(s * 0.013 + oi * 3.3) + 0.25 * _vln(s * 0.051 + oi))
			var kol := (pv if pv > 0.35 else 0.0) * prer * (1.0 - kriz) * (1.0 - udus)
			var hrb := clampf(1.15 - pv, 0.0, 1.0) * (1.0 - kriz) * (1.0 - udus)
			# Misa 0.84 „kazdy kousek podle pouziti“: brod a breh - bahno a koleje vzdy, hlubsi (vozy se bori, voda
			# vymiela); tvarem site (cesta_profil o.x), ne jen barvou
			var brod := 1.0 - smoothstep(3.0, 9.0, voda)
			bah = maxf(bah, brod)
			kol = maxf(kol, brod * 1.5 * maxf(pv, 0.5))
			# zatacka: vozy ji zkracuji - sirsi (uhel smeru na +-4 body = 6,4 m)
			var a0 := (pp[i] - pp[maxi(i - 4, 0)]).normalized()
			var a1 := (pp[mini(i + 4, pp.size() - 1)] - pp[i]).normalized()
			var zat := smoothstep(0.12, 0.45, acos(clampf(a0.dot(a1), -1.0, 1.0))) if a0 != Vector2.ZERO and a1 != Vector2.ZERO else 0.0
			op.append(Vector4(kol, hrb, bah, vym))
			kotva[i] = maxf(maxf(kriz, udus * 0.5), smoothstep(0.0, 0.6, 1.0 - smoothstep(6.0, 20.0, voda)))   # brod: koryto a brehy tvaruje _brody, profil ne (Misa 0.85 brod)
			# rozjete sirsi: krizovatky, zatacky, udusana mista (hostinec, brana, lom - plocha pred nimi, Misa 0.84)
			ws[i] = ws[i] * (1.0 + 0.35 * kriz + 0.25 * zat + 0.9 * udus)
		o["op"] = op
		o["w"] = ws
		o["kotva"] = kotva


func _cesty_tvar(root: Node3D) -> void:
	var cmi := root.find_child("Teren_cesta", true, false) as MeshInstance3D
	if cmi == null or cmi.mesh == null:
		return
	var t0 := Time.get_ticks_msec()
	# osy vozovych cest z pravidla/svet/cesty.json (krok A: Blender kresli pas a srovnava teren z teze osy) - drive se
	# skladaly zpetne z barvy pasu Teren_cesta (stred g 0,08, bok 0,3, okraj 0,8) a pulsirka byla median toho mereni
	var body := []
	cesty_osy.clear()
	for c: Dictionary in Pravidla.cti("cesty", "vozove"):
		var osa: Array = c["osa"]
		var pts := PackedVector3Array()
		var ws := PackedFloat32Array()
		for i in range(int(c["hra_od_bodu"]), osa.size()):
			var q := Vector2(float(osa[i][0]), float(osa[i][1]))
			pts.append(Vector3(q.x, _vyska(q.x, q.y) + 0.02, q.y))
			ws.append(float(c["pulsirka_m"]))
		body.append_array(pts)
		cesty_osy.append(_osa_prevzorkuj(pts, ws, 1.0))
	# ves: hlavni cesta navsi (vesnice.py ves_paths: v = 2,5 sin(u/23) + 1,2 sin(u/9 + 1)), do rybnika ne
	var vp := PackedVector3Array()
	var vw := PackedFloat32Array()
	if VES_OBLOUK:
		# ulice v oblouku (ves_oblouk.gd): stare osy cest uvnitr stare navsi pryc (konce pak napoji _cesty_napoj),
		# ulice uzka (Misa 27. 10.: „neni dalnice, nema bricho“ - drive pulsirka az 5,6 m): pulsirka 1,3-1,6 m, u vjezdu
		# 1,9 (napojeni na cestu od tvrze)
		for oi in cesty_osy.size():
			var o: Dictionary = cesty_osy[oi]
			var pp: PackedVector2Array = o["p"]
			var zac := 0
			var kon := pp.size()
			while zac < kon and _vo_stara_naves(pp[zac]):
				zac += 1
			while kon > zac and _vo_stara_naves(pp[kon - 1]):
				kon -= 1
			if zac > 0 or kon < pp.size():
				for key: String in ["p", "y", "w", "k", "op", "dl"]:
					if o.has(key):
						o[key] = o[key].slice(zac, kon)
				o["s0"] = float(o["s0"]) + zac * 0.8
		var osa: PackedVector2Array = vo.osa_ulice()
		for i in osa.size():
			var q := osa[i]
			var f := float(i) / maxf(osa.size() - 1, 1)
			vp.append(Vector3(q.x, _vyska(q.x, q.y) + 0.02, q.y))
			vw.append(vo.pulsirka(f))                     # zaznam pravidla/svet/lokace.json ves.ulice.pulsirka
	for ui in (range(-95, 39) if not VES_OBLOUK else []):
		var u := float(ui)
		var c0 := 2.5 * sin(u / 23.0) + 1.2 * sin(u / 9.0 + 1.0)
		var q := Vector2(470.0, 830.0) + Vector2(0.76193, 0.64764) * u + Vector2(-0.64764, 0.76193) * c0
		vp.append(Vector3(q.x, _vyska(q.x, q.y) + 0.02, q.y))
		vw.append(clampf(2.0 + 3.0 * exp(-pow((u + 6.0) / 30.0, 2.0)) + 0.5 * sin(u / 7.0), 3.2, 4.6))
	var ov := _osa_prevzorkuj(vp, vw, 1.0)
	ov["ves"] = true
	cesty_osy.append(ov)
	# Misa 0.81 „od vsi odbocka do lomu“: cesta do lomu (vozy s kamenem) a od padaciho mostu na hlavni cestu byly jen
	# pesiny v texture (PESINY 6 a 4) - ted osy jako ostatni cesty (Catmull-Rom po 2 m)
	for pi: Array in [[6, 1.8], [4, 2.2]]:
		var pts: Array = PESINY[pi[0]]
		if pi[0] == 4:
			# od padaciho mostu az za prikopem (Misa 0.82: pas cesty vedl vedle mostu dolu do prikopu)
			# od konce pevneho mostu pres prikop (z 28,5; Misa 0.84 „cesta neni dobre navazana na tvrz“ - mezera s travou)
			pts = [Vector2(0.0, 28.5), Vector2(0.3, 38.0), Vector2(1.0, 52.0), Vector2(2.0, 72.0)]
		var cp := PackedVector3Array()
		var cw := PackedFloat32Array()
		for k in pts.size() - 1:
			var p0: Vector2 = pts[maxi(k - 1, 0)]
			var p1: Vector2 = pts[k]
			var p2: Vector2 = pts[k + 1]
			var p3: Vector2 = pts[mini(k + 2, pts.size() - 1)]
			var m := maxi(2, int(p1.distance_to(p2) / 2.0))
			for j in m:
				var t := float(j) / m
				var q := 0.5 * ((2.0 * p1) + (-p0 + p2) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t * t + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t * t * t)
				cp.append(Vector3(q.x, _vyska(q.x, q.y), q.y))
				cw.append(float(pi[1]))
		var pe: Vector2 = pts[pts.size() - 1]
		cp.append(Vector3(pe.x, _vyska(pe.x, pe.y), pe.y))
		cw.append(float(pi[1]))
		# konec u zacatku jine osy (od mostu -> hlavni cesta z 67): spojit v jednu osu - dve site pres sebe
		# z-fightovaly a mely jine skvrny (Misa 0.83 „prvni cast od tvrze zvlastni rastr“)
		var spoj := false
		for o2: Dictionary in cesty_osy:
			var p2: PackedVector2Array = o2["p"]
			var y2: PackedFloat32Array = o2["y"]
			var w2: PackedFloat32Array = o2["w"]
			var obrat := p2[p2.size() - 1].distance_to(pe) < p2[0].distance_to(pe)
			if minf(p2[0].distance_to(pe), p2[p2.size() - 1].distance_to(pe)) > 8.0:
				continue
			var cp2 := PackedVector3Array()
			var cw2 := PackedFloat32Array()
			var z2: Vector2 = p2[p2.size() - 1] if obrat else p2[0]
			for k in cp.size():
				if Vector2(cp[k].x, cp[k].z).distance_to(z2) < 6.0:
					break                         # konec usek nad zacatkem druhe osy - navazat, necouvat
				cp2.append(cp[k])
				cw2.append(cw[k])
			for k in p2.size():
				var j := p2.size() - 1 - k if obrat else k
				cp2.append(Vector3(p2[j].x, y2[j], p2[j].y))
				cw2.append(w2[j])
			var nova := _osa_prevzorkuj(cp2, cw2, 1.0)
			o2.merge(nova, true)
			spoj = true
			break
		if not spoj:
			cesty_osy.append(_osa_prevzorkuj(cp, cw, 1.0))
	# cesticky k domum a chysim (PESINY >= 12, Misa 0.88 „textura cest i jako cesticky k domum“): uzke osy cest
	# (pul sirky 0,75 m, provoz 0,3 = bez kolej), stejny model a povrch jako cesty
	for pi2 in range(12, PESINY.size()):
		var pts2: Array = PESINY[pi2]
		if pts2.size() < 2:
			continue
		var cp3 := PackedVector3Array()
		var cw3 := PackedFloat32Array()
		# sirka: placek pred chysemi (PES_SIRKA >= 1 = pul sirky m), jinak cesticka 0,75
		var sir2: float = float(PES_SIRKA[pi2]) if pi2 < PES_SIRKA.size() and float(PES_SIRKA[pi2]) >= 1.0 else 0.75
		for k in pts2.size() - 1:
			var a2: Vector2 = pts2[k]
			var b2: Vector2 = pts2[k + 1]
			var m2 := maxi(1, int(a2.distance_to(b2) / 1.0))
			for j in m2:
				var q2 := a2.lerp(b2, float(j) / m2)
				cp3.append(Vector3(q2.x, _vyska(q2.x, q2.y), q2.y))
				cw3.append(sir2)
		var pe2: Vector2 = pts2[pts2.size() - 1]
		cp3.append(Vector3(pe2.x, _vyska(pe2.x, pe2.y), pe2.y))
		cw3.append(sir2)
		if cp3.size() < 3:
			continue
		var op2 := _osa_prevzorkuj(cp3, cw3, 1.0)
		op2["pesina"] = true
		cesty_osy.append(op2)
	_cesty_napoj()
	_cesty_mriz.clear()
	var s0 := 0.0
	for oi in cesty_osy.size():
		var o: Dictionary = cesty_osy[oi]
		o["s0"] = s0
		var pp: PackedVector2Array = o["p"]
		s0 += pp.size() * 0.8 + 50.0
		for i in pp.size() - 1:
			var lo := Vector2(minf(pp[i].x, pp[i + 1].x), minf(pp[i].y, pp[i + 1].y)) - Vector2(16.0, 16.0)
			var hi := Vector2(maxf(pp[i].x, pp[i + 1].x), maxf(pp[i].y, pp[i + 1].y)) + Vector2(16.0, 16.0)      # prechod zarezu 12 m za okraj
			for cx in range(floori(lo.x / 4.0), floori(hi.x / 4.0) + 1):
				for cz in range(floori(lo.y / 4.0), floori(hi.y / 4.0) + 1):
					var kk := Vector2i(cx, cz)
					if not _cesty_mriz.has(kk):
						_cesty_mriz[kk] = []
					(_cesty_mriz[kk] as Array).append([oi, i])
	_disp_nacti()
	_cesty_opotrebeni()
	for oi in cesty_osy.size():
		var o: Dictionary = cesty_osy[oi]
		var pp: PackedVector2Array = o["p"]
		var wv: PackedFloat32Array = (o["w"] as PackedFloat32Array).duplicate()
		wv.sort()
		# nejprudsi usek 10 m po skutecnem terenu (Misa 0.84 „pred hospodou moc prudky kopec“)
		var smax := 0.0
		var kde := Vector2.ZERO
		for i in range(0, pp.size() - 13, 2):
			var g := absf(_vyska(pp[i + 12].x, pp[i + 12].y) - _vyska(pp[i].x, pp[i].y)) / maxf(pp[i].distance_to(pp[i + 12]), 1.0)
			if g > smax:
				smax = g
				kde = pp[i + 6]
		print("cesty: osa %d nejprudsi %.0f %% u %s" % [oi, smax * 100.0, kde.round()])
		print("cesty: osa %d %s %d m, %s -> %s pres %s, pulsirka %.1f, koleje %.2f" % [oi, "ves" if o.get("ves", false) else "", int(pp.size() * 0.8),
				pp[0].round(), pp[pp.size() - 1].round(), pp[pp.size() / 2].round(), wv[wv.size() / 2], ((o["op"] as Array)[pp.size() / 2] as Vector4).x])
	var t1 := Time.get_ticks_msec()
	_cesty_teren(root)
	_cesty_vys_mrizka()
	_ves_maska_ulice()
	var t2 := Time.get_ticks_msec()
	var nt := _cesty_do_terenu(root)
	print("cesty: osy %d ms, mrizka %d ms, do terenu %d ms" % [t1 - t0, t2 - t1, Time.get_ticks_msec() - t2])
	# hruby pas Teren_cesta z Blenderu: uz se nekresli ani nekoliduje - cesta je teren (pravidla povrchu A, radce 15:20)
	cmi.visible = false
	cmi.set_meta("bez_kolize", true)
	print("cesty: %d os (%d bodu stredu), v terenu %d troj., %d ms" % [cesty_osy.size(), body.size(), nt, Time.get_ticks_msec() - t0])


## Prevzorkovani osy po 0,8 m, klouzavy prumer polohy, vysky a sirky; konce zapustene (k = 0 bez kolej. u sirky < 1,35).
func _osa_prevzorkuj(pts: PackedVector3Array, ws: PackedFloat32Array, kolej: float) -> Dictionary:
	var vzd := PackedFloat32Array([0.0])
	for i in range(1, pts.size()):
		vzd.append(vzd[i - 1] + Vector2(pts[i].x - pts[i - 1].x, pts[i].z - pts[i - 1].z).length())
	var L := vzd[vzd.size() - 1]
	var n := maxi(2, int(L / 0.8) + 1)
	var p := PackedVector2Array()
	var y := PackedFloat32Array()
	var w := PackedFloat32Array()
	var j := 0
	for i in n:
		var s := minf(i * 0.8, L)
		while j < pts.size() - 2 and vzd[j + 1] < s:
			j += 1
		var t := clampf((s - vzd[j]) / maxf(vzd[j + 1] - vzd[j], 1e-4), 0.0, 1.0)
		var q := pts[j].lerp(pts[j + 1], t)
		p.append(Vector2(q.x, q.z))
		y.append(q.y)
		w.append(lerpf(ws[j], ws[j + 1], t))
	for _it in 3:
		var p2 := p.duplicate()
		var y2 := y.duplicate()
		var w2 := w.duplicate()
		for i in range(2, n - 2):
			p2[i] = (p[i - 2] + p[i - 1] + p[i] + p[i + 1] + p[i + 2]) / 5.0
			y2[i] = (y[i - 2] + y[i - 1] + y[i] + y[i + 1] + y[i + 2]) / 5.0
			w2[i] = (w[i - 2] + w[i - 1] + w[i] + w[i + 1] + w[i + 2]) / 5.0
		p = p2
		y = y2
		w = w2
	return {"p": p, "y": y, "w": w, "k": kolej, "s0": 0.0}


## Teren pod cestou: vrcholy siti Teren* (mimo cestu a obzor) v pasu cesty zapustit (koleje 0,2 m pod osou nesmi
## propichnout teren), plynule do okoli; trojuhelniky terenu u cest pro dorovnani dna koleji.
func _cesty_teren(root: Node3D) -> void:
	# Misa 0.80 „rozvaleny beton“: cesta lezi na puvodnim terenu (cesta_y) - trojuhelniky terenu u cest pred zapustenim
	_ter_tri.clear()
	var nt := 0
	for t in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(t.name)
		if nm.begins_with("Teren_cesta") or nm == "Teren_obzor" or nm.ends_with("_sukne"):
			continue
		var mi := t as MeshInstance3D
		var am := mi.mesh as ArrayMesh
		if am == null:
			continue
		var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
		for si in am.get_surface_count():
			var arr := am.surface_get_arrays(si)
			var vv2: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			for tt in idx.size() / 3:
				var p0 := xf * vv2[idx[tt * 3]]
				var p1 := xf * vv2[idx[tt * 3 + 1]]
				var p2 := xf * vv2[idx[tt * 3 + 2]]
				var cc := (p0 + p1 + p2) / 3.0
				if not _cesty_mriz.has(Vector2i(floori(cc.x / 4.0), floori(cc.z / 4.0))):
					continue
				nt += 1
				for cx in range(floori(minf(p0.x, minf(p1.x, p2.x)) / 2.0), floori(maxf(p0.x, maxf(p1.x, p2.x)) / 2.0) + 1):
					for cz in range(floori(minf(p0.z, minf(p1.z, p2.z)) / 2.0), floori(maxf(p0.z, maxf(p1.z, p2.z)) / 2.0) + 1):
						var kk := Vector2i(cx, cz)
						if not _ter_tri.has(kk):
							_ter_tri[kk] = []
						(_ter_tri[kk] as Array).append([p0, p1, p2])
	_cesty_profil()
	print("cesty: %d trojuhelniku terenu pod cestami" % nt)


## Cesta = teren (pravidla povrchu A, radce 15:10/15:20; Misa 0.88: levitujici trava, diry, hrb, pozdni trava -
## vse z cesty jako samostatne site): trojuhelniky terenu u cest se rozdeli (krok ~0,7 m) a vyska = puvodni teren +
## vyrovnany profil (o["dl"]) + profil cesty (cesta_d). Hrany k nerozdelenym trojuhelnikum linearne (bez trhlin).
## Udaje cesty do vrcholu (CUSTOM0/1) pro zem.gdshader. Kolize a louka pak stoji na tomtez povrchu.
const CESTA_KROK := 1.0                # deleni terenu u cest (0.7 = 687 k troj. navic, 1,0 ~ polovina)


func _cesty_do_terenu(root: Node3D) -> int:
	var nt := 0
	# Misa 0.89 „nacita 2x dele“: deleni povrchu ve vlaknech (WorkerThreadPool, kazdy povrch zvlast; cesta_lat jen cte,
	# louka ji vola z vlaken taky); cteni poli a stavba ArrayMesh v hlavnim vlakne
	var t_zac := Time.get_ticks_msec()
	var ulohy: Array = []               # [mi, si, arr, xf]
	for t in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(t.name)
		if nm.begins_with("Teren_cesta") or nm == "Teren_obzor" or nm.ends_with("_sukne"):
			continue
		var mi := t as MeshInstance3D
		var am := mi.mesh as ArrayMesh
		if am == null:
			continue
		var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
		for si in am.get_surface_count():
			ulohy.append([mi, si, am.surface_get_arrays(si), xf])
	if _disp_n == 0:
		_disp_nacti()                   # cesta_disp nacita liné - ve vlaknech by se nacitalo naraz
	var vys: Array = []
	vys.resize(ulohy.size())
	var prace := func(i: int) -> void:
		var u: Array = ulohy[i]
		var r: Array = _cesta_povrch(u[2], u[3])
		vys[i] = [] if r.is_empty() else [(r[0] as SurfaceTool).commit_to_arrays(), r[1]]
	var tp := Time.get_ticks_msec()
	# Misa 0.89 „nacita 2x dele“: vysledek se uklada do user:// podle sestaveni (commit + manifest) - pri dalsim
	# spusteni teze verze se nepocita (vypocet ~16 s na PC, jeden velky povrch = vlakna skoro nepomohou)
	var cache := _cesty_cache_cesta()
	var z_cache := false
	if cache != "" and FileAccess.file_exists(cache):
		var f := FileAccess.open_compressed(cache, FileAccess.READ, FileAccess.COMPRESSION_ZSTD)
		if f:
			var d = f.get_var()
			f.close()
			if d is Array and (d as Array).size() == ulohy.size():
				vys = d
				z_cache = true
	if not z_cache:
		var g := WorkerThreadPool.add_group_task(prace, ulohy.size(), -1, true, "cesty do terenu")
		WorkerThreadPool.wait_for_group_task_completion(g)
		if cache != "":
			DirAccess.make_dir_recursive_absolute(cache.get_base_dir())
			for stary in DirAccess.get_files_at(cache.get_base_dir()):
				if stary.begins_with("cesty_"):
					DirAccess.remove_absolute(cache.get_base_dir().path_join(stary))
			var f := FileAccess.open_compressed(cache, FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
			if f:
				f.store_var(vys)
				f.close()
	var tv := Time.get_ticks_msec()
	var hotove := {}                    # mi -> {si: vysledek}
	for i in ulohy.size():
		var u: Array = ulohy[i]
		if not hotove.has(u[0]):
			hotove[u[0]] = {}
		hotove[u[0]][u[1]] = [u[2], vys[i]]
	var ct := "cesty do terenu: %d povrchu, priprava %d ms, %s %d ms (%d jader), cache %s %d MB" % [ulohy.size(), tp - t_zac,
			"z cache" if z_cache else "vypocet", tv - tp, OS.get_processor_count(), cache if cache != "" else "-",
			(FileAccess.open(cache, FileAccess.READ).get_length() / 1048576) if cache != "" and FileAccess.file_exists(cache) else 0]
	print(ct)
	var dg: Object = Engine.get_meta("diag", null)
	if dg:
		dg.faze(ct)
	for mi: MeshInstance3D in hotove:
		var am := mi.mesh as ArrayMesh
		var nove := ArrayMesh.new()
		var zmena := false
		var ovr: Array = []
		for si in am.get_surface_count():
			ovr.append(mi.get_surface_override_material(si))
			var arr: Array = hotove[mi][si][0]
			var r: Array = hotove[mi][si][1]
			if r.is_empty():
				nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
			else:
				nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, r[0], [], {}, _cesta_format(r[0]))
				nt += int(r[1])
				zmena = true
			nove.surface_set_material(si, am.surface_get_material(si))
			nove.surface_set_name(si, am.surface_get_name(si))
		if zmena:
			mi.mesh = nove
			for si in ovr.size():
				mi.set_surface_override_material(si, ovr[si])
	return nt


## Soubor ulozenych cest v terenu pro toto sestaveni (res://sestaveni.json: commit + manifest); bez sestaveni (editor,
## testy na PC) se neuklada. TVRZ_BEZ_CACHE vypne.
func _cesty_cache_cesta() -> String:
	if OS.has_environment("TVRZ_BEZ_CACHE") or (not OS.has_environment("TVRZ_CACHE") and (OS.has_feature("editor") or not OS.has_feature("template"))) or not FileAccess.file_exists("res://sestaveni.json"):
		return ""
	var j = JSON.parse_string(FileAccess.get_file_as_string("res://sestaveni.json"))
	if not (j is Dictionary):
		return ""
	return "user://cache/cesty_%s_%s_%d.bin" % [String(j.get("commit", "")), String(j.get("manifest", "")), CESTA_VERZE]


const CESTA_VERZE := 2                   # zvysit pri zmene vypoctu cest v terenu (zneplatni ulozene)
const ZAMEK_VERZE := 1                   # zvysit pri zmene _zamek_terenu


## Zamek terenu (docs/pipeline.md krok 4 -> zamek, Misa 27. 10. „levitovala trava a kere“): teren se upravuje
## nekolika kroky (koryto, profil cest, plosiny, dil rybnika) a mrizka vysek (_vyska: louka, _na_zem, rozsevy) se
## s nimi rozchazela. Po posledni uprave se mrizky trava_kraj a trava_ves prepisou z hotove site terenu: kazdy uzel
## dostane vysku trojuhelniku nad nim, jemnejsi sit prepise hrubsi. Od ted nic nemeni vysky.
func _zamek_terenu(parent: Node3D) -> void:
	if OS.has_environment("TVRZ_BEZ_ZAMKU"):
		return                           # jen mereni pred/po (test vyska_mriz)
	_vyska(0.0, 0.0)                     # nacist _vys
	var t0 := Time.get_ticks_msec()
	# kolize terenu z hotove site (stavely se pred posledni upravou: koryto, zaplaty, lom - test vyska_mriz 394 bodu)
	var nkol := 0
	for n in parent.find_children("Teren*", "MeshInstance3D", true, false):
		var mk := n as MeshInstance3D
		if mk.mesh == null or mk.has_meta("kolize_sit") or mk.has_meta("bez_kolize"):
			continue
		var tb := mk.get_node_or_null(String(mk.name) + "_kolize")
		if tb == null:
			continue
		for cs in tb.get_children():
			if cs is CollisionShape3D and (cs as CollisionShape3D).shape is ConcavePolygonShape3D:
				var tri := mk.mesh.create_trimesh_shape()
				tri.backface_collision = true
				(cs as CollisionShape3D).shape = tri
				nkol += 1
	print("zamek terenu: kolize %d siti z hotoveho terenu" % nkol)
	var cs := _cesty_cache_cesta().replace("cesty_", "vysky_").replace("_%d.bin" % CESTA_VERZE, "_%d.bin" % ZAMEK_VERZE)
	if cs != "" and FileAccess.file_exists(cs):
		var f := FileAccess.open(cs, FileAccess.READ)
		var ulozeno: Dictionary = f.get_var()
		for key: String in ulozeno:
			if _vys.has(key):
				_vys[key]["y"] = ulozeno[key]
		print("zamek terenu: mrizka z cache ", cs)
		return
	var site: Array = []
	for n in parent.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		if mi.mesh == null or not mi.visible or nm.ends_with("_sukne") or nm == "Teren_obzor":
			continue
		if not (nm.begins_with("Teren") or nm.begins_with("Rybnik_Teren")):
			continue
		var xf := mi.global_transform
		var tr := PackedVector3Array()
		for si in mi.mesh.get_surface_count():
			var a := mi.mesh.surface_get_arrays(si)
			var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
			var ix: PackedInt32Array = a[Mesh.ARRAY_INDEX] if a[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			if ix.is_empty():
				for i in v.size():
					tr.append(xf * v[i])
			else:
				for i in ix:
					tr.append(xf * v[i])
		if tr.size() < 3:
			continue
		# velikost trojuhelniku (prumer plochy v XZ): hrube site nejdriv, jemne je prepisou
		var pl := 0.0
		for t in range(0, tr.size(), 3):
			pl += absf((tr[t + 1].x - tr[t].x) * (tr[t + 2].z - tr[t].z) - (tr[t + 2].x - tr[t].x) * (tr[t + 1].z - tr[t].z))
		site.append([pl / float(tr.size() / 3), nm, tr])
	site.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) > float(b[0]))
	var zmen := 0
	var ulozit := {}
	for key: String in ["trava_kraj", "trava_ves"]:
		if not _vys.has(key):
			continue
		var g: Dictionary = _vys[key]
		var x0 := float(g["x0"])
		var z0 := float(g["z0"])
		var k := float(g["k"])
		var nx: int = g["nx"]
		var nz: int = g["nz"]
		var ys: PackedByteArray = g["y"]
		for s_: Array in site:
			var tr: PackedVector3Array = s_[2]
			for t in range(0, tr.size(), 3):
				var a := tr[t]
				var b := tr[t + 1]
				var c := tr[t + 2]
				var den := (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z)
				if absf(den) < 1e-9:
					continue
				var i0 := maxi(0, ceili((minf(a.x, minf(b.x, c.x)) - x0) / k))
				var i1 := mini(nx - 1, floori((maxf(a.x, maxf(b.x, c.x)) - x0) / k))
				var j0 := maxi(0, ceili((minf(a.z, minf(b.z, c.z)) - z0) / k))
				var j1 := mini(nz - 1, floori((maxf(a.z, maxf(b.z, c.z)) - z0) / k))
				for j in range(j0, j1 + 1):
					var pz := z0 + j * k
					for i in range(i0, i1 + 1):
						var px := x0 + i * k
						var l1 := ((b.z - c.z) * (px - c.x) + (c.x - b.x) * (pz - c.z)) / den
						var l2 := ((c.z - a.z) * (px - c.x) + (a.x - c.x) * (pz - c.z)) / den
						var l3 := 1.0 - l1 - l2
						if l1 < -1e-4 or l2 < -1e-4 or l3 < -1e-4:
							continue
						var cm := clampi(roundi((l1 * a.y + l2 * b.y + l3 * c.y) * 100.0), -32768, 32767)
						var o := (j * nx + i) * 2
						if ys.decode_s16(o) != cm:
							zmen += 1
						ys.encode_s16(o, cm)
		g["y"] = ys
		ulozit[key] = ys
	if cs != "":
		DirAccess.make_dir_recursive_absolute("user://cache")
		var f2 := FileAccess.open(cs, FileAccess.WRITE)
		if f2:
			f2.store_var(ulozit)
	_sklony = PackedFloat32Array()
	print("zamek terenu: %d siti, %d uzlu mrizky prepsano podle site, %d ms" % [site.size(), zmen, Time.get_ticks_msec() - t0])


## Udaje cesty v bode: [zmena vysky (plna = s profilem cesty), CUSTOM0, CUSTOM1, zmena jen vyrovnani]
## Format povrchu s CUSTOM0/1 jako RGBA float (jako SurfaceTool.set_custom_format) - add_surface_from_arrays je jinak nezna.
## Normaly vrcholu jako prumer normal ploch (vahou plochy); pole s indexy i bez.
static func _normaly_z_ploch(arr: Array) -> void:
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
	var n := PackedVector3Array()
	n.resize(v.size())
	var nt := idx.size() / 3 if not idx.is_empty() else v.size() / 3
	for t in nt:
		var ia := idx[t * 3] if not idx.is_empty() else t * 3
		var ib := idx[t * 3 + 1] if not idx.is_empty() else t * 3 + 1
		var ic := idx[t * 3 + 2] if not idx.is_empty() else t * 3 + 2
		var f := (v[ic] - v[ia]).cross(v[ib] - v[ia])
		n[ia] += f
		n[ib] += f
		n[ic] += f
	for i in n.size():
		n[i] = n[i].normalized() if n[i].length_squared() > 1e-12 else Vector3.UP
	arr[Mesh.ARRAY_NORMAL] = n


func _cesta_format(arr: Array) -> int:
	var f := 0
	if arr[Mesh.ARRAY_CUSTOM0] != null:
		f |= Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT
	if arr[Mesh.ARRAY_CUSTOM1] != null:
		f |= Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM1_SHIFT
	return f


func _cesta_v(x: float, z: float) -> Array:
	var l := cesta_lat(x, z)
	if l.is_empty():
		return [0.0, Color(9.0, 0.0, 0.0, 0.0), Color(0.0, 0.0, 1.0, 0.0), 0.0]
	var lat := float(l[0])
	var hw := float(l[1])
	var s := float(l[3])
	var op: Vector4 = l[4]
	var a := absf(lat)
	var ok := cesta_ok(hw, s, 1.0 if lat >= 0.0 else -1.0)
	var pr := cesta_profil(lat, hw, s, op)
	var dvyr := float(l[5]) * (1.0 - smoothstep(ok + 1.0, ok + 12.0, a))
	return [dvyr + cesta_d(x, z, a, ok, pr.x, s), Color(lat / maxf(ok, 0.1), s, op.x, ok),
			Color(pr.y, maxf(pr.z, op.z * 0.6), clampf(absf(pr.w) * 0.5, 0.0, 1.0) if op.x > 0.05 else 1.0, 7.0), dvyr]


func _cesta_povrch(arr: Array, xf: Transform3D) -> Array:
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
	if idx.is_empty():
		idx.resize(v.size())
		for i in v.size():
			idx[i] = i
	var uv: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV] if arr[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array()
	var uv2: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV2] if arr[Mesh.ARRAY_TEX_UV2] != null else PackedVector2Array()
	var cl: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
	var inv := xf.affine_inverse()
	var w := PackedVector3Array()
	w.resize(v.size())
	for i in v.size():
		w[i] = xf * v[i]
	var nt := idx.size() / 3
	var klic := func(q: Vector3) -> Vector2i:
		return Vector2i(roundi(q.x * 100.0), roundi(q.z * 100.0))
	# trojuhelniky k rozdeleni (u hliny cesty) a vrcholy, ktere jim patri
	var deli := {}
	var blizko := false
	var delky := PackedFloat32Array()
	for t in nt:
		var a := w[idx[t * 3]]
		var b := w[idx[t * 3 + 1]]
		var c := w[idx[t * 3 + 2]]
		var cc := (a + b + c) / 3.0
		if not _cesty_mriz.has(Vector2i(floori(cc.x / 4.0), floori(cc.z / 4.0))):
			continue
		blizko = true
		var l := cesta_lat(cc.x, cc.z)
		if l.is_empty():
			continue
		var rr := maxf(cc.distance_to(a), maxf(cc.distance_to(b), cc.distance_to(c)))
		var ok := cesta_ok(float(l[1]), float(l[3]), 1.0 if float(l[0]) >= 0.0 else -1.0)
		if absf(float(l[0])) < ok + 0.8 + rr:
			deli[t] = true
			delky.append(maxf(a.distance_to(b), maxf(b.distance_to(c), c.distance_to(a))))
	if not blizko:
		return []
	delky.sort()
	var n := clampi(ceili((delky[delky.size() / 2] if not delky.is_empty() else 1.0) / CESTA_KROK), 1, 12)
	var plne := {}                      # klice vrcholu rozdelenych trojuhelniku (plny profil)
	var hrany := {}                     # hrana (klice) -> pocet rozdelenych trojuhelniku
	var hrany_vse := {}                 # hrana -> pocet trojuhelniku
	for t in nt:
		for k in 3:
			var ka: Vector2i = klic.call(w[idx[t * 3 + k]])
			var kb: Vector2i = klic.call(w[idx[t * 3 + (k + 1) % 3]])
			var he := [ka, kb] if (ka.x < kb.x or (ka.x == kb.x and ka.y < kb.y)) else [kb, ka]
			hrany_vse[he] = int(hrany_vse.get(he, 0)) + 1
			if deli.has(t):
				hrany[he] = int(hrany.get(he, 0)) + 1
				plne[ka] = true
	# udaje vrcholu (cache podle polohy)
	var bod := {}
	var udaj := func(q: Vector3, plny: bool) -> Array:
		var kq := Vector3i(roundi(q.x * 100.0), roundi(q.z * 100.0), 1 if plny else 0)
		if bod.has(kq):
			return bod[kq]
		var r: Array = _cesta_v(q.x, q.z)
		if not plny:
			r = [r[3], r[1], r[2], r[3]]
		bod[kq] = r
		return r
	var vy := PackedFloat32Array()      # nova vyska vrcholu
	vy.resize(v.size())
	for i in v.size():
		var r: Array = udaj.call(w[i], plne.has(klic.call(w[i])))
		vy[i] = w[i].y + float(r[0])
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_custom_format(0, SurfaceTool.CUSTOM_RGBA_FLOAT)
	st.set_custom_format(1, SurfaceTool.CUSTOM_RGBA_FLOAT)
	var pridej := func(q: Vector3, plny: bool, u: Vector2, u2: Vector2, c: Color, y: float) -> void:
		var r: Array = udaj.call(q, plny)
		if not cl.is_empty():
			st.set_color(c)
		if not uv.is_empty():
			st.set_uv(u)
		if not uv2.is_empty():
			st.set_uv2(u2)
		st.set_custom(0, r[1])
		st.set_custom(1, r[2])
		st.add_vertex(inv * Vector3(q.x, y, q.z))
	var nove := 0
	for t in nt:
		var ia := idx[t * 3]
		var ib := idx[t * 3 + 1]
		var ic := idx[t * 3 + 2]
		if not deli.has(t):
			for i in [ia, ib, ic]:
				pridej.call(w[i], plne.has(klic.call(w[i])), uv[i] if not uv.is_empty() else Vector2.ZERO,
						uv2[i] if not uv2.is_empty() else Vector2.ZERO, cl[i] if not cl.is_empty() else Color.WHITE, vy[i])
			nove += 1
			continue
		# hrany: plna, kdyz ji sdili dva rozdelene trojuhelniky; jinak linearne (soused se nedeli)
		var ka: Vector2i = klic.call(w[ia])
		var kb: Vector2i = klic.call(w[ib])
		var kc: Vector2i = klic.call(w[ic])
		var plna := func(k1: Vector2i, k2: Vector2i) -> bool:
			var he := [k1, k2] if (k1.x < k2.x or (k1.x == k2.x and k1.y < k2.y)) else [k2, k1]
			return int(hrany.get(he, 0)) >= 2 and int(hrany_vse.get(he, 0)) == 2
		var p_ab: bool = plna.call(ka, kb)
		var p_ac: bool = plna.call(ka, kc)
		var p_bc: bool = plna.call(kb, kc)
		var mriz := {}
		for i in n + 1:
			for j in n + 1 - i:
				var fu := float(i) / n
				var fv := float(j) / n
				var q := w[ia] + (w[ib] - w[ia]) * fu + (w[ic] - w[ia]) * fv
				var ty := q.y
				var y := 0.0
				var roh := (i == 0 and j == 0) or (i == n and j == 0) or (i == 0 and j == n)
				if roh:
					y = vy[ia] if (i == 0 and j == 0) else (vy[ib] if i == n else vy[ic])
				elif j == 0 and not p_ab:
					y = lerpf(vy[ia], vy[ib], fu)
				elif i == 0 and not p_ac:
					y = lerpf(vy[ia], vy[ic], fv)
				elif i + j == n and not p_bc:
					y = lerpf(vy[ib], vy[ic], fv)
				else:
					y = ty + float((udaj.call(q, true) as Array)[0])
				var u := Vector2.ZERO
				var u2 := Vector2.ZERO
				var c := Color.WHITE
				if not uv.is_empty():
					u = uv[ia] + (uv[ib] - uv[ia]) * fu + (uv[ic] - uv[ia]) * fv
				if not uv2.is_empty():
					u2 = uv2[ia] + (uv2[ib] - uv2[ia]) * fu + (uv2[ic] - uv2[ia]) * fv
				if not cl.is_empty():
					c = cl[ia] + (cl[ib] - cl[ia]) * fu + (cl[ic] - cl[ia]) * fv
				mriz[Vector2i(i, j)] = [q, u, u2, c, y]
		for i in n:
			for j in n - i:
				var tri: Array = [[Vector2i(i, j), Vector2i(i + 1, j), Vector2i(i, j + 1)]]
				if i + j < n - 1:
					tri.append([Vector2i(i + 1, j), Vector2i(i + 1, j + 1), Vector2i(i, j + 1)])
				for tr: Array in tri:
					for g: Vector2i in tr:
						var e: Array = mriz[g]
						pridej.call(e[0], true, e[1], e[2], e[3], e[4])
					nove += 1
	st.index()
	st.generate_normals()
	if not uv.is_empty():
		st.generate_tangents()
	return [st, nove]


## Misa 26. 10. noc („kompozice do blizka, za kopcem a domem nic“): occlusion culling Godotu (RendererSceneCull,
## CPU rastr Embree, nezavisi na rendereru - plati i v Compatibility; predchozi komentare „Compatibility nema occlusion
## culling“ byly omyl). Okluzory: teren (mrizka 12 m, nejnizsi bod bunky - 0,8 m, aby nic na zemi nezakryl) a domy vsi,
## hostinec (krabice uvnitr zdi). Co je cele za kopcem nebo domem, se nekresli - bez zmeny vzhledu.
const OKL_BUNKA := 12.0
const OKL_DOMY := false


func _okluzory(parent: Node3D) -> void:
	var t0 := Time.get_ticks_msec()
	var v := PackedVector3Array()
	var idx := PackedInt32Array()
	var x0 := -250.0
	var z0 := -250.0
	var nx := int((900.0 - x0) / OKL_BUNKA)
	var nz := int((1350.0 - z0) / OKL_BUNKA)
	# vyska uzlu = minimum v okoli bunky (4 x 4 vzorky po 4 m) - okluzor vsude pod terenem
	for j in nz + 1:
		for i in nx + 1:
			var cx := x0 + i * OKL_BUNKA
			var cz := z0 + j * OKL_BUNKA
			var mn := INF
			for a in range(-1, 2):
				for b in range(-1, 2):
					mn = minf(mn, _vyska(cx + a * OKL_BUNKA * 0.5, cz + b * OKL_BUNKA * 0.5))
			v.append(Vector3(cx, mn - 0.8, cz))
	for j in nz:
		for i in nx:
			var k := j * (nx + 1) + i
			idx.append_array([k, k + 1, k + nx + 1, k + 1, k + nx + 2, k + nx + 1])
	var occ := ArrayOccluder3D.new()
	occ.set_arrays(v, idx)
	var oi := OccluderInstance3D.new()
	oi.name = "Okluzor_teren"
	oi.occluder = occ
	parent.add_child(oi)
	# domy vsi a hostinec: krabice z obalu vnejsku zmensene o 15 % (zdi, ne strecha)
	var nd := 0
	# krabice domu jen s prepinanim u hrace (kamera uvnitr krabice by zakryla vse) - zatim vypnuto
	for d in (parent.find_children("Dum_ves_*", "Node3D", true, false) if OKL_DOMY else []):
		for ch in d.get_children():
			if ch is MeshInstance3D and String(ch.name).ends_with("_Vnejsek"):
				nd += _okl_krabice(parent, ch as MeshInstance3D, 0.8)
	for h in (parent.find_children("Staticky_hostinec*", "Node3D", true, false) if OKL_DOMY else []):
		for mi in (h as Node).find_children("*", "MeshInstance3D", true, false):
			if (mi as MeshInstance3D).get_aabb().size.length() > 15.0:
				nd += _okl_krabice(parent, mi as MeshInstance3D, 0.8)
	# remizky (lokace.json kompozice, Misa 28. 10. „pro krasu i pro zobrazovani, at se to neseka“): krabice v hustem
	# jadru (stromy do 0,6 r, kere na kraji) od zeme do zapoje - co je cele za remizkem, se nekresli. U hrace
	# (pasma test okluzor_vypnout_m za okrajem) se vypne, at kamera v krabici nezakryje vse (okluzory_u_hrace).
	var nr := 0
	var pk: Dictionary = Pravidla.cti("lokace", "kompozice")
	for r: Dictionary in (pk.get("remizky", []) as Array):
		var c := Vector2(float(r["stred"][0]), float(r["stred"][1]))
		var rad := float(r["polomer_m"])
		var bo := BoxOccluder3D.new()
		bo.size = Vector3(rad, 6.0, rad)
		var ro := OccluderInstance3D.new()
		ro.name = "Okluzor_remizek_%d" % nr
		ro.occluder = bo
		ro.position = Vector3(c.x, _vyska(c.x, c.y) + 4.0, c.y)
		parent.add_child(ro)
		_okl_prep.append([ro, c, rad * 0.5 + float(pasma()["test"]["okluzor_vypnout_m"])])
		nr += 1
	# nitro lesa (pasma test okluzor_les_*): bunka, kde je les vsude do okraj_m kolem (okraj lesa a plast zustanou
	# videt), dostane krabici od zeme+1 m do zapoje - co je cele za lesem, se nekresli
	var pt: Dictionary = pasma()["test"]
	var kb := float(pt["okluzor_les_bunka_m"])
	var okr := float(pt["okluzor_les_okraj_m"])
	var nl := 0
	var lz := x0
	while lz < 900.0:
		var lzz := z0
		while lzz < 1350.0:
			var cx := lz + kb * 0.5
			var cz := lzz + kb * 0.5
			var hust := true
			for a in [-okr, 0.0, okr]:
				for b in [-okr, 0.0, okr]:
					if hust and _les(cx + a, cz + b) < float(pt["okluzor_les_min"]):
						hust = false
			if hust:
				var bo2 := BoxOccluder3D.new()
				bo2.size = Vector3(kb * 0.8, float(pt["okluzor_les_vyska_m"]), kb * 0.8)
				var lo := OccluderInstance3D.new()
				lo.occluder = bo2
				lo.position = Vector3(cx, _vyska_min(cx, cz, kb * 0.5) + 1.0 + float(pt["okluzor_les_vyska_m"]) * 0.5, cz)
				parent.add_child(lo)
				_okl_prep.append([lo, Vector2(cx, cz), kb * 0.6 + float(pt["okluzor_vypnout_m"])])
				nl += 1
			lzz += kb
		lz += kb
	print("okluzory: teren %d troj., krabic %d, remizku %d, nitro lesa %d, %d ms" % [idx.size() / 3, nd, nr, nl, Time.get_ticks_msec() - t0])


var _okl_prep: Array = []                 # [OccluderInstance3D, stred xz, vzdalenost vypnuti]


## Okluzory s prepinanim u hrace (main.gd po 0,25 s): blize nez vzdalenost vypnuti se okluzor skryje.
func okluzory_u_hrace(p: Vector3) -> void:
	var q := Vector2(p.x, p.z)
	if _okl_mriz.is_empty():
		for e: Array in _okl_prep:
			var c := Vector2i(floori((e[1] as Vector2).x / 32.0), floori((e[1] as Vector2).y / 32.0))
			if not _okl_mriz.has(c):
				_okl_mriz[c] = []
			(_okl_mriz[c] as Array).append(e)
	for e: Array in _okl_skryte:
		(e[0] as OccluderInstance3D).visible = true
	_okl_skryte.clear()
	var c0 := Vector2i(floori(q.x / 32.0), floori(q.y / 32.0))
	for dx in range(-1, 2):
		for dz in range(-1, 2):
			for e: Array in _okl_mriz.get(Vector2i(c0.x + dx, c0.y + dz), []):
				if q.distance_to(e[1]) <= float(e[2]):
					(e[0] as OccluderInstance3D).visible = false
					_okl_skryte.append(e)


var _okl_mriz := {}                       # bunka 32 m -> okluzory s prepinanim
var _okl_skryte: Array = []


func _okl_krabice(parent: Node3D, mi: MeshInstance3D, k: float) -> int:
	var bb := mi.get_aabb()
	if bb.size.x < 2.0 or bb.size.z < 2.0 or bb.size.y < 2.0:
		return 0
	var bo := BoxOccluder3D.new()
	bo.size = Vector3(bb.size.x * k, bb.size.y * 0.6, bb.size.z * k)
	var oi := OccluderInstance3D.new()
	oi.occluder = bo
	oi.transform = mi.global_transform * Transform3D(Basis(), bb.get_center() - Vector3(0, bb.size.y * 0.2, 0))
	parent.add_child(oi)
	return 1


## Radce 20:35 / Misa 0.93 (hostinec: schod 34 ms, move_and_slide 28 ms na hostinec_kolize): test kolize_troj nasel
## v kolizi hostince 537 degenerovanych troj. (nulova plocha - normala nedefinovana, kapsle se na nich zasekava
## v resolveru) a 96 hran > 8 m. Vsechny ConcavePolygon sveta do 60 k troj.: degenerovane pryc.
static func cisti_faces(f: PackedVector3Array) -> PackedVector3Array:
	var o := PackedVector3Array()
	o.resize(f.size())
	var n := 0
	for i in range(0, f.size() - 2, 3):
		var a := f[i]
		var b := f[i + 1]
		var c := f[i + 2]
		if (b - a).cross(c - a).length_squared() < 4e-8:
			continue
		o[n] = a
		o[n + 1] = b
		o[n + 2] = c
		n += 3
	o.resize(n)
	return o


func _kolize_cisteni(parent: Node) -> void:
	var t0 := Time.get_ticks_msec()
	var tvaru := 0
	var pryc := 0
	var hotove := {}
	for cs in parent.find_children("*", "CollisionShape3D", true, false):
		var sh := (cs as CollisionShape3D).shape as ConcavePolygonShape3D
		if sh == null or hotove.has(sh):
			continue
		hotove[sh] = true
		var f := sh.get_faces()
		if f.size() > 180000:
			continue
		var g := cisti_faces(f)
		if g.size() < f.size():
			sh.set_faces(g)
			tvaru += 1
			pryc += (f.size() - g.size()) / 3
	print("kolize cisteni: %d tvaru, %d degenerovanych troj. pryc, %d ms" % [tvaru, pryc, Time.get_ticks_msec() - t0])


## Kamenky u cest jako modely: jen na krajnici za okrajem hliny (radce 27. 10. 19:30 - KCD), 5-20 cm, z poloviny v zemi.
func _cesty_kameny() -> void:
	var r: Dictionary = data["rostliny"]
	var druhy: Array = []
	for i in range(1, 6):
		if r.has("kamen_maly_%d_0" % i):
			druhy.append("kamen_maly_%d_0" % i)
	if druhy.is_empty():
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 18001
	var n := 0
	var kraj_k := float(pasma()["cesta"]["vozova"]["kaminky_kraj_m"])
	for o: Dictionary in cesty_osy:
		var pp: PackedVector2Array = o["p"]
		var ws: PackedFloat32Array = o["w"]
		for i in pp.size() - 1:
			var hw := ws[i]
			var opi: Vector4 = (o["op"] as Array)[i]
			var d := (pp[i + 1] - pp[i]).normalized()
			var nrm := Vector2(-d.y, d.x)
			var s := float(i) * 0.8 + float(o["s0"])
			var kmn := cesta_useky(s).z                       # kamenity usek (Misa 0.81: misty kameny, jinde jen kaminky)
			for _j in 3 + int(9.0 * kmn):
				# radce 27. 10. 19:30 (KCD a pasma, ruseno 26. 10. 18:00): na hrbetu a v kolejich zadne kaminky, jen na
				# krajnici za okrajem hliny (pasma.cesta.<typ>.kaminky_kraj_m)
				var sd2 := 1.0 if rng.randf() < 0.5 else -1.0
				var ok2 := cesta_ok(hw, s, sd2)
				var lat := sd2 * rng.randf_range(ok2, ok2 + kraj_k)
				var pr := cesta_profil(lat, hw, s, opi)
				if rng.randf() > (0.6 + 0.4 * opi.w) or pr.z > 0.3:
					continue
				var q := pp[i] + d * rng.randf() * 0.8 + nrm * lat
				# kraj hliny vuci nejblizsi ose (stejna funkce jako test zasazeni): posun podel useku, oblouk a sousedni
				# osa na krizovatce daly kaminky 0,1-0,2 m na hlinu (1 080 chyb v_pasmu, testy J 27. 10.)
				if cesta_kraj_osa(q.x, q.y).x < 0.0:
					continue
				var sc := rng.randf_range(0.06, 0.2) * (1.4 if absf(lat) > hw - 0.6 else 1.0)
				if rng.randf() < 0.25 * kmn:
					sc = rng.randf_range(0.18, 0.35)              # vetsi kamen vystupujici z cesty
				var dls2: PackedFloat32Array = o.get("dl", PackedFloat32Array())
				var yy := cesta_y(q.x, q.y, absf(lat), cesta_ok(hw, s, 1.0 if lat >= 0.0 else -1.0), pr.x, s, dls2[i] if dls2.size() > i else 0.0) - sc * 0.35
				(r[druhy[rng.randi() % druhy.size()]] as Array).append(_xf(q.x, yy, q.y, rng.randf() * TAU, sc))
				n += 1
	print("cesty: %d kamenku" % n)


## Rostliny z exportu u cest (Misa 0.85: strom uprostred cesty k lomu - cesta byla pesina, ted je to cesta): na ceste
## a 1,5 m kolem pryc, do 12 m za okrajem vyska podle vyrovnaneho profilu (zarez / nasyp). Pred _cesty_kameny a _kere.
func _cesty_rostliny() -> void:
	# krok vegetace (poradi zasazeni): cesty uz stoji, rostliny jim ustupuji podle pasem (pasma.cesta, odstup od kraje
	# hliny podle skupiny druhu); co zustane, sedi na vyrovnanem profilu cesty
	var r: Dictionary = data["rostliny"]
	var pryc := 0
	var posun := 0
	for key: String in r:
		var arr: Array = r[key]
		var nove: Array = []
		var odstupy := {}
		for t: Array in arr:
			if _cesty_mriz.has(Vector2i(floori(float(t[3]) / 4.0), floori(float(t[11]) / 4.0))):
				var lc := cesta_lat(t[3], t[11])
				if not lc.is_empty():
					var ac := absf(float(lc[0]))
					var oi := int(lc[6])
					if not odstupy.has(oi):
						odstupy[oi] = odstup_cesty(key, oi)
					var kraj := ac - cesta_ok(float(lc[1]), float(lc[3]), 1.0 if float(lc[0]) >= 0.0 else -1.0)
					if kraj < float(odstupy[oi]):
						pryc += 1
						continue
					var dy := float(lc[5]) * (1.0 - smoothstep(float(lc[1]) + 1.0, float(lc[1]) + 12.0, ac))
					if absf(dy) > 0.01:
						t = t.duplicate()
						t[7] = float(t[7]) + dy
						posun += 1
			nove.append(t)
		r[key] = nove
	print("cesty: rostlin v pasmu cest pryc %d (pasma.cesta), posunuto podle profilu %d" % [pryc, posun])


## Krovi podel cest (Misa 0.84 „kolem cest, ne vsude - klasika podle realneho sveta“): skupiny keru (sipek, bez,
## liskovy keř) 1,5-4 m za okrajem hliny, useky 10-40 m s mezerami (sum podel osy, kazda strana jinak); ne ve vsi,
## ne u krizovatek a udusanych mist, ne v jine ceste, v lese mene (stin).
## Blok 1.0 (Misa 27. 10. „kazdy koutek hezky, kazda zatacka vyrazi dech“; reference docs/screens/kcd1, ref_kcd2):
## nase naves = rovna 56 m siroka plocha, domy v rade, pruhled pres celou ves („dalnice“). Skutecna ves zavira pohled
## po par domech: dve stare stromy na navsi, stromy a keře v mezerach mezi usedlostmi, strom na konci navsi, u zdi
## kopřivy (predzahradky v KCD1 skoro nejsou). Souradnice navsi: osa u (podel rad), v (napric); rady domu v = 294,6 a 361,6.
const VES_D := Vector2(0.7620, 0.6476)
const VES_N := Vector2(-0.6476, 0.7620)


func _ves_bod(u: float, v: float) -> Vector2:
	return VES_D * u + VES_N * v


func _ves_kompozice() -> void:
	if _domy.is_empty():
		return
	var r: Dictionary = data["rostliny"]
	var rng := RandomNumberGenerator.new()
	rng.seed = 1393
	var n := 0
	# krok vegetace (poradi zasazeni): cesty a budovy uz stoji - odstup od kraje cesty a od zdi z pasem (pasma.cesta
	# podle typu osy a skupiny druhu, pasma.budova.kmen_od_zdi_m pro stromy; plevel a kere u zdi ano)
	var od_zdi := float(pasma()["budova"]["kmen_od_zdi_m"])
	var pridej := func(k: String, q: Vector2, sc: float) -> bool:
		if not r.has(k):
			return false
		var ck := cesta_kraj_osa(q.x, q.y)
		if ck.y >= 0.0 and ck.x < odstup_cesty(k, int(ck.y)):
			return false
		if not smi_tu_byt(q.x, q.y, k) or _v_stare_zahrade(q.x, q.y) and not k.begins_with("bez") and not k.begins_with("shrub"):
			return false
		var zed := od_zdi if skupina(k) == "strom" else 0.2
		for st: Array in _uvnitr:
			var w: Vector3 = (st[0] as Transform3D) * Vector3(q.x, 0.0, q.y)
			if (st[1] as AABB).grow(zed).has_point(Vector3(w.x, (st[1] as AABB).get_center().y, w.z)):
				return false
		var t := _xf(q.x, _vyska(q.x, q.y) - 0.05, q.y, rng.randf() * TAU, sc)
		(r[k] as Array).append(t)
		var kd := k.trim_suffix("_0") + "_daleko_0"
		if r.has(kd):
			(r[kd] as Array).append(t)
		return true
	# 1) velke stare lipy a dub na navsi - nesymetricky, mimo osu cesty (kazdy kousek jinak, ne alej)
	var oblouk := func(f: float, bok: float) -> Vector2:
		return vo.na_ulici(f, bok)
	var stare := [["lipa_stara_0", 878.0, 340.0, 1.2], ["dub_stary_0", 931.0, 312.0, 1.05]]
	if vo:
		# ves se zatackou: lipa na rozsireni u vjezdu, dub ve vnejsim rohu zatacky (zavre pohled podel ulice)
		stare = [["lipa_stara_0", 0.08, 9.0, 1.2], ["dub_stary_0", 0.52, -9.5, 1.1]]
	for it: Array in stare:
		for _pokus in 6:
			var q: Vector2 = oblouk.call(float(it[1]) + rng.randf_range(-0.02, 0.02), float(it[2]) + rng.randf_range(-1.5, 1.5)) if vo \
					else _ves_bod(float(it[1]) + rng.randf_range(-4.0, 4.0), float(it[2]) + rng.randf_range(-3.0, 3.0))
			if pridej.call(it[0], q, float(it[3]) * rng.randf_range(0.9, 1.1)):
				n += 1
				break
	# 2) kazdy dum vlastni scena (Misa 27. 10.: „kazdy dum jinou scenu, ne vsude stejne“; v KCD1 predzahradky
	# skoro nejsou). Scena = kdo tu bydli -> co roste u domu. Mista v ramci domu: [druh, x pres osu (+ strana
	# vstupu), z podel osy (+ k navsi od stitu), meritko]; x/z v metrech od stredu domu, poloviny W/L se pricitaji.
	var kere := ["bez_cerny_1_0", "bez_cerny_2_0", "bez_cerny_3_0", "shrub_02_0", "shrub_02_1", "shrub_02_2"]
	var sceny := {
		# 1 chalupa na kraji: stary bez u rohu, kopřivy kolem zdi, nic udrzovaneho
		1: [["bez_cerny_3_0", 1.2, 0.6, 1.3], ["bez_cerny_1_0", 1.6, 0.2, 1.0], ["k", 0, 0, 0]],
		# 2 selsky dum (bohaty sedlak): velka lipa bokem pred stitem, posekano, jen trsy u plotu
		2: [["lipa_stara_0", -1.0, 0.9, 0.95]],
		# 3 chalupa u rybnika: vrba hlavata u zadniho rohu, rakos a kopřivy
		3: [["vrba_hlavata_1_0", -1.3, -0.8, 0.9], ["k", 0, 0, 0]],
		# 4 selsky dum na kraji navsi: dub za domem (stary strom, dum postaven vedle nej), keř u vstupu
		4: [["dub_stary_0", 0.4, -1.6, 1.0], ["shrub_02_1", 1.25, 0.7, 0.9]],
		# 5 rychta: lipa pred rychtou (soudni lipa), cisto - nic jineho
		5: [["lipa_stara_0", 0.0, 1.9, 1.15]],
		# 6 chalupa mlade rodiny: dve mlade brizy u zahradky
		6: [["briza_1", 1.5, 0.3, 0.75], ["briza_2", 1.7, -0.2, 0.7], ["k", 0, 0, 0]],
		# 7 stary dum na konci: zarostly - bez, keře, kopřivy az ke zdi, mlady dub
		7: [["bez_cerny_2_0", -1.3, 0.5, 1.2], ["shrub_02_2", -1.5, 0.1, 1.1], ["dub_stredni_0", -1.8, -0.9, 0.8],
				["k", 0, 0, 0], ["k", 0, 0, 0]],
	}
	var plevel := ["nettle_plant_0", "nettle_plant_1", "nettle_plant_2", "nettle_plant_3"]
	for d: Dictionary in _domy:
		if int(d["k"]) >= 20:
			continue                                         # chyse u lomu maji svoje
		var c: Vector2 = d["c"]
		var au: Vector2 = d["au"]
		var av: Vector2 = d["av"]
		var f := float(d["L"]) * 0.5
		var hw := float(d["W"]) * 0.5
		for it: Array in sceny.get(int(d["k"]), []):
			if String(it[0]) == "k":
				# kopřivy u paty zdi (shluk na jedne strane)
				var sd := 1.0 if rng.randf() < 0.5 else -1.0
				var z0 := rng.randf_range(-f, f)
				for _j in rng.randi_range(4, 7):
					if pridej.call(plevel[rng.randi() % plevel.size()], c + au * (z0 + rng.randf_range(-1.5, 1.5)) + av * sd * (hw + rng.randf_range(0.3, 0.9)), rng.randf_range(0.5, 0.9)):
						n += 1
				continue
			var x := float(it[1])
			var z := float(it[2])
			var q := c + av * (signf(x) * hw + x * 2.5) + au * (signf(z) * f + z * 2.5)
			for _pokus in 4:
				if pridej.call(it[0], q, float(it[3]) * rng.randf_range(0.93, 1.07)):
					n += 1
					break
				q += Vector2(rng.randf_range(-1.5, 1.5), rng.randf_range(-1.5, 1.5))
		# u paty zdi vzdy neco roste (Misa 27. 10.; fotky KCD1 ves_1-6: plevel a vyssi trava u zdi a plotu, kam se
		# nechodi, sem tam kericek): zadni zed nebo bok bez vstupu, u kazdeho domu jinak dlouhy pas; kerik u rohu
		var zed: Array = [[0.0, -1.0], [-1.0, 0.0]] if d["m"].has("vstup") else [[0.0, -1.0], [1.0, 0.0], [-1.0, 0.0]]
		var z1: Array = zed[rng.randi() % zed.size()]
		for _j in rng.randi_range(3, 6):
			var t1 := rng.randf_range(-0.9, 0.9)
			var q1 := c + av * (float(z1[0]) * (hw + rng.randf_range(0.25, 0.8)) + (1.0 - absf(float(z1[0]))) * t1 * hw) \
					+ au * (float(z1[1]) * (f + rng.randf_range(0.25, 0.8)) + (1.0 - absf(float(z1[1]))) * t1 * f)
			var dr: String = (plevel + ["grass_medium_02_0", "grass_medium_02_0", "dandelion_01_0"])[rng.randi() % 7]
			if pridej.call(dr, q1, rng.randf_range(0.45, 0.85) if dr.begins_with("nettle") else rng.randf_range(0.8, 1.2)):
				n += 1
		if rng.randf() < 0.6:
			var ro := Vector2(1.0 if rng.randf() < 0.5 else -1.0, -1.0 if rng.randf() < 0.7 else 1.0)
			if pridej.call(kere[rng.randi() % kere.size()], c + av * ro.x * (hw + 1.0) + au * ro.y * (f + 1.0), rng.randf_range(0.6, 0.95)):
				n += 1
	# 3) mezery mezi usedlostmi v rade: strom za plotem + keře (zavrou pohled podel rady)
	var mezery: Array = []
	if vo:
		# ves v oblouku: mezi sousednimi usedlostmi na stejne strane ulice (podle uhlu na oblouku)
		# mezi sousednimi usedlostmi (podle poradi podel ulice), strom za plotem v mezere
		var por: Array = []
		for e: Dictionary in vo.u:
			var best := 0.0
			var bd := INF
			for k in 101:
				var dq: float = (vo.na_ulici(k / 100.0) as Vector2).distance_to(e["nc"])
				if dq < bd:
					bd = dq
					best = k / 100.0
			por.append([best, e["nc"]])
		por.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) < float(b[0]))
		for i in por.size() - 1:
			if absf(float(por[i + 1][0]) - float(por[i][0])) > 0.05:
				mezery.append(((por[i][1] as Vector2) + (por[i + 1][1] as Vector2)) * 0.5)
	else:
		for rada: Array in [[885.8, 913.9, 940.2, 294.6, -1.0], [857.7, 886.3, 912.9, 942.0, 361.6, 1.0]]:
			for i in rada.size() - 3:
				mezery.append(_ves_bod((float(rada[i]) + float(rada[i + 1])) * 0.5, float(rada[rada.size() - 2]) + float(rada[rada.size() - 1]) * rng.randf_range(-6.0, 2.0)))
	for q0: Vector2 in mezery:
		if true:
			var q := q0 + Vector2(rng.randf_range(-2.0, 2.0), rng.randf_range(-2.0, 2.0))
			if pridej.call(["lipa_stredni_0", "dub_stredni_0", "briza_2"][rng.randi() % 3], q, rng.randf_range(0.75, 1.05)):
				n += 1
			for _j in rng.randi_range(1, 3):
				pridej.call(kere[rng.randi() % kere.size()], q + Vector2(rng.randf_range(-3.0, 3.0), rng.randf_range(-3.0, 3.0)), rng.randf_range(0.7, 1.3))
	# 4) konce navsi: strom a keře u cesty, kde naves konci (pohled podel navsi se zavre)
	var konce := [[838.0, 322.0], [842.0, 340.0], [962.0, 318.0], [968.0, 336.0]]
	if vo:
		konce = [[-0.03, 9.0], [0.02, -10.0], [1.03, 8.0], [0.98, -9.0]]
	for it2: Array in konce:
		for _pokus in 8:
			var q: Vector2 = (oblouk.call(float(it2[0]), float(it2[1])) + Vector2(rng.randf_range(-4.0, 4.0), rng.randf_range(-4.0, 4.0))) if vo \
					else _ves_bod(float(it2[0]) + rng.randf_range(-6.0, 6.0), float(it2[1]) + rng.randf_range(-5.0, 5.0))
			if pridej.call(["lipa_stara_0", "dub_stredni_0", "lipa_stredni_0"][rng.randi() % 3], q, rng.randf_range(0.85, 1.15)):
				n += 1
				for _j in rng.randi_range(2, 4):
					pridej.call(kere[rng.randi() % kere.size()], q + Vector2(rng.randf_range(-3.5, 3.5), rng.randf_range(-3.5, 3.5)), rng.randf_range(0.7, 1.3))
				break
	print("ves kompozice: %d stromu a keru (lipy na navsi, predzahradky, mezery, konce navsi)" % n)


func _cesty_kere() -> void:
	var r: Dictionary = data["rostliny"]
	var druhy: Array = []
	for k: String in ["sipek_0", "sipek_1", "sipek_2", "bez_cerny_1_0", "bez_cerny_2_0", "bez_cerny_3_0", "shrub_02_0", "shrub_02_1", "shrub_02_2", "shrub_02_3"]:
		if r.has(k):
			druhy.append(k)
	if druhy.is_empty():
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 8402
	var n := 0
	# Misa 0.87 „kere moc pravidelne u cest“: shluky 1-6 keru (polomer do 2,5 m), mezi shluky nepravidelne 6-45 m,
	# kazda strana zvlast, vzdalenost od okraje 1-6 m; uvnitr shluku ruzne druhy a velikosti
	for oi in cesty_osy.size():
		var o: Dictionary = cesty_osy[oi]
		if bool(o.get("ves", false)) or bool(o.get("pesina", false)):
			continue
		var pp: PackedVector2Array = o["p"]
		var ws: PackedFloat32Array = o["w"]
		for sd: float in [-1.0, 1.0]:
			var i := 4 + rng.randi_range(0, 30)
			while i < pp.size() - 4:
				var s := float(i) * 0.8 + float(o["s0"])
				var d := (pp[i + 1] - pp[i - 1]).normalized()
				var nrm := Vector2(-d.y, d.x)
				var ok := cesta_ok(ws[i], s, sd)
				var stred := pp[i] + nrm * sd * (ok + rng.randf_range(1.5, 6.0)) + d * rng.randf_range(-2.0, 2.0)
				var pocet: int = [1, 1, 2, 2, 3, 3, 4, 6][rng.randi() % 8]
				for _j in pocet:
					var q := stred + Vector2(rng.randf_range(-2.5, 2.5), rng.randf_range(-2.5, 2.5))
					var l := cesta_lat(q.x, q.y)
					if not l.is_empty() and absf(float(l[0])) < float(l[1]) * 1.3 + 1.2:
						continue
					var k: String = druhy[rng.randi() % druhy.size()]
					if not smi_tu_byt(q.x, q.y, k):
						continue
					(r[k] as Array).append(_xf(q.x, _vyska(q.x, q.y) - 0.05, q.y, rng.randf() * TAU, rng.randf_range(0.55, 1.35)))
					n += 1
				# dalsi shluk: delsi mezery na kosene louce (divokost), kratsi u lesa
				var mez := rng.randf_range(6.0, 45.0) * (1.6 if divokost(stred.x, stred.y) < 0.15 else 1.0)
				i += int(mez / 0.8)
	print("cesty: %d keru podel cest" % n)


## Navesni rybnik Lhota (Misa 24. 10., modely/rybnik/rybnik.glb z rybnik_lhota_v3.zip, NAVOD.md): dil 60 x 60 m,
## hladina y 0, okraj dilu +0,30 m. Stred v miste stareho rybnicku (vesnice.py POND), delsi osa (x dilu) podel navsi.
var RYBNIK_DIL := not OS.has_environment("TVRZ_BEZ_DILU")
# rybnik Lhota: pravidla/svet/voda.json (krok A); RYB_YAW mistni +x -> VES_AU (0,762; 0,648), RYB_PAS pas za okrajem
# dilu: teren hry se svazi k okraji (+0,30)
static var RYB_C := Vector2(Pravidla.cti("voda", "rybnik_lhota", "stred")[0], Pravidla.cti("voda", "rybnik_lhota", "stred")[1])
static var RYB_YAW := float(Pravidla.cti("voda", "rybnik_lhota", "natoceni"))
static var RYB_POL := float(Pravidla.cti("voda", "rybnik_lhota", "pulsirka_dilu_m"))
static var RYB_PAS := float(Pravidla.cti("voda", "rybnik_lhota", "pas_napojeni_m"))
var _ryb_scena: Node3D
var _ryb_xf := Transform3D()
var _ryb_inv := Transform3D()
var _ryb_y := INF                             # hladina (svet)
var _ryb_tri := {}


## Krok B (radce 16:50): hraz na zapadnim brehu dilu a koryta toku (pritok, odtok s vypusti) do terenu dilu - stejne
## vzorce jako blender/kraj.py voda_tvar (data voda.json), aby voda z rybnika odtekla a pritok do nej dotekl.
func _ryb_hraz_toky(mi: MeshInstance3D, xf: Transform3D) -> void:
	var hz: Dictionary = Pravidla.cti("voda", "rybnik_lhota", "hraz")
	var tt: Dictionary = Pravidla.cti("voda", "toky_tvar")
	var toky: Array = []
	for t: Dictionary in Pravidla.cti("voda", "toky"):
		var o: Array = t["osa_xzy"]
		var seg: Array = []
		for k in o.size() - 1:
			var a := Vector2(o[k][0], o[k][1])
			if a.distance_to(RYB_C) < RYB_POL * 1.6 + 10.0:
				seg.append([a, Vector2(o[k + 1][0], o[k + 1][1]), float(o[k][2]), float(o[k + 1][2])])
		if not seg.is_empty():
			toky.append([seg, float(t["sirka_m"]) / 2.0, float(t["hloubka_m"]), String(t["id"]).ends_with("odtok")])
	var hc := Vector2(hz["stred"][0], hz["stred"][1])
	var hu := Vector2(hz["smer_osy"][0], hz["smer_osy"][1])
	var inv := xf.affine_inverse()
	var am := ArrayMesh.new()
	var zmen := 0
	for si in mi.mesh.get_surface_count():
		var arr := mi.mesh.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		for i in v.size():
			var w := xf * v[i]
			var p := Vector2(w.x, w.z)
			var y := w.y
			# hraz: koruna nad hladinou, svahy; ve vypusti (koryto odtoku) prerusena
			var dd := p - hc
			var a := maxf(0.0, absf(dd.dot(hu)) - float(hz["delka_m"]) / 2.0)
			var bb := maxf(0.0, absf(dd.dot(hu.orthogonal())) - float(hz["koruna_sirka_m"]) / 2.0)
			var yh := _ryb_y + float(hz["koruna_nad_hladinou_m"]) - Vector2(a, bb).length() * float(hz["sklon_svahu"])
			var vypust := false
			for t: Array in toky:
				var best := INF
				var hl := 0.0
				for sg: Array in t[0]:
					var s0: Vector2 = sg[0]
					var s1: Vector2 = sg[1]
					var tq := clampf((p - s0).dot(s1 - s0) / maxf((s1 - s0).length_squared(), 1e-6), 0.0, 1.0)
					var dq := p.distance_to(s0.lerp(s1, tq))
					if dq < best:
						best = dq
						hl = lerpf(float(sg[2]), float(sg[3]), tq)
				var pw: float = t[1]
				if t[3] and best < pw + 0.6:
					vypust = true
				var allow := (float(t[2]) + float(tt["breh_m"])) * smoothstep(pw, pw + float(tt["breh_sirka_m"]), best) \
						+ float(tt["svah"]) * maxf(0.0, best - pw - float(tt["breh_sirka_m"]))
				y = minf(y, hl - float(t[2]) + allow)
			if yh > y and not vypust:
				y = yh
			if absf(y - w.y) > 0.01:
				zmen += 1
				v[i] = inv * Vector3(w.x, y, w.z)
		arr[Mesh.ARRAY_VERTEX] = v
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		am.surface_set_material(am.get_surface_count() - 1, mi.mesh.surface_get_material(si))
	mi.mesh = am
	print("rybnik: hraz a koryta toku v terenu dilu, %d vrcholu" % zmen)


func _ryb_priprav() -> void:
	if not RYBNIK_DIL or not ResourceLoader.exists("res://modely/rybnik/rybnik.glb"):
		return
	_ryb_scena = (load("res://modely/rybnik/rybnik.glb") as PackedScene).instantiate()
	_ryb_scena.name = "Rybnik_dil"
	# vyska: okraj dilu (+0,30) = nizsi kvartil terenu na obvodu ctverce - pas kolem dilu se pak jen snizuje (zvednuty
	# teren zasypal branku_16 o 0,88 m, test vratka)
	var b := Basis(Vector3.UP, RYB_YAW)
	var obvod: Array = []
	var n := 0
	for k in 120:
		var t := k / 30.0
		var q := Vector2(-1.0 + 2.0 * fmod(t, 1.0), 1.0 if int(t) % 2 == 0 else -1.0) * RYB_POL
		if int(t) >= 2:
			q = Vector2(q.y, q.x)
		var w := b * Vector3(q.x, 0, q.y)
		obvod.append(_vyska(RYB_C.x + w.x, RYB_C.y + w.z))
		n += 1
	obvod.sort()
	# krok B: hladina z voda.json (jeden zdroj s Blenderem: odtok, hraz a mlyn jsou spocitane k ni)
	_ryb_y = float(Pravidla.cti("voda", "rybnik_lhota", "hladina_y"))
	_ryb_xf = Transform3D(b, Vector3(RYB_C.x, _ryb_y, RYB_C.y))
	_ryb_inv = _ryb_xf.affine_inverse()
	var mi := _ryb_scena.find_child("Rybnik_Teren*", true, false) as MeshInstance3D
	if mi == null:
		print("rybnik: Rybnik_Teren nenalezen")
		return
	var xf := _ryb_xf * (mi.global_transform if mi.is_inside_tree() else _rel_xf(mi, _ryb_scena))
	_ryb_hraz_toky(mi, xf)
	var f := mi.mesh.get_faces()
	for i in range(0, f.size(), 3):
		var a := xf * f[i]
		var c := xf * f[i + 1]
		var d := xf * f[i + 2]
		for cx in range(floori(minf(a.x, minf(c.x, d.x)) / 2.0), floori(maxf(a.x, maxf(c.x, d.x)) / 2.0) + 1):
			for cz in range(floori(minf(a.z, minf(c.z, d.z)) / 2.0), floori(maxf(a.z, maxf(c.z, d.z)) / 2.0) + 1):
				var key := Vector2i(cx, cz)
				if not _ryb_tri.has(key):
					_ryb_tri[key] = []
				(_ryb_tri[key] as Array).append([a, c, d])
	print("rybnik: dil u (%.0f, %.0f), hladina y %.2f, %d troj. terenu" % [RYB_C.x, RYB_C.y, _ryb_y, f.size() / 3])


func _rel_xf(n: Node3D, koren: Node) -> Transform3D:
	var t := n.transform
	var p := n.get_parent()
	while p and p != koren:
		if p is Node3D:
			t = (p as Node3D).transform * t
		p = p.get_parent()
	return t


## Vyska povrchu dilu rybnika (svet), mimo dil INF.
func ryb_vyska(x: float, z: float) -> float:
	if _ryb_tri.is_empty():
		return INF
	return _tri_vyska(_ryb_tri, x, z)


func _tri_vyska(tri: Dictionary, x: float, z: float) -> float:
	var l: Array = tri.get(Vector2i(floori(x / 2.0), floori(z / 2.0)), [])
	var best := -INF
	var p := Vector2(x, z)
	for t: Array in l:
		var a: Vector3 = t[0]
		var b: Vector3 = t[1]
		var c: Vector3 = t[2]
		var v0 := Vector2(b.x - a.x, b.z - a.z)
		var v1 := Vector2(c.x - a.x, c.z - a.z)
		var v2 := p - Vector2(a.x, a.z)
		var den := v0.x * v1.y - v1.x * v0.y
		if absf(den) < 1e-9:
			continue
		var u := (v2.x * v1.y - v1.x * v2.y) / den
		var w := (v0.x * v2.y - v2.x * v0.y) / den
		if u < -0.001 or w < -0.001 or u + w > 1.001:
			continue
		best = maxf(best, a.y + u * (b.y - a.y) + w * (c.y - a.y))
	return best if best > -INF else INF


## Krok 9: predmet, jehoz pudorys zasahuje na hlinu cesty nebo pesiny (cesta_kraj_osa < 0, tataz funkce jako test
## zasazeni), se posune na nejblizsi volne misto do 3 m (u zdi jen podel zdi, ostatni na vsechny strany); kdyz neni,
## vynecha se.
func _vybaveni_mimo_cest() -> void:
	var zust: Array = []
	var posunuto := 0
	var pryc := 0
	if _kat_p.is_empty() and FileAccess.file_exists("res://modely/predmety.json"):
		_kat_p = JSON.parse_string(FileAccess.get_file_as_string("res://modely/predmety.json"))
	for it: Dictionary in data["vybaveni"]:
		var p0 := Vector2(float(it["p"][0]), float(it["p"][2]))
		# jen predmety u zdi domu (hranice dreva): stoly na placku hostince, vybaveni lomu a zahony s ploty jsou
		# skladby - posun po jednom je rozbil (zkouska 28. 10.: 11 vynechano, zahony bez plutku); jejich stret s osou
		# cesty je chyba dat (osa k_hostinci pres placek, cesta od lomu pres pracoviste), ne predmetu
		if not it.has("podel_zdi") or absf(float(it["p"][1]) - _vyska(p0.x, p0.y)) > 0.6:
			zust.append(it)
			continue
		# u zdi se posouva podel zdi, volne stojici predmet (stul na placku, pristresek v lomu) na vsechny strany
		var u := Vector2(float(it["podel_zdi"][0]), float(it["podel_zdi"][1])) if it.has("podel_zdi") else Vector2.from_angle(float(it.get("yaw", 0.0)))
		var v := u.orthogonal()
		var rz: Array = it["pul"] if it.has("pul") else ((_kat_p.get(String(it["id"]), {}) as Dictionary).get("rozmer", [0.6, 0.6, 0.6]) as Array)
		var pu := float(rz[0]) * (1.0 if it.has("pul") else 0.5)
		var pv := float(rz[1] if it.has("pul") else rz[2]) * (1.0 if it.has("pul") else 0.5)
		var smery: Array = [u, -u] if it.has("podel_zdi") else [u, -u, v, -v, (u + v).normalized(), (u - v).normalized(), (-u + v).normalized(), (-u - v).normalized()]
		var volno := func(c: Vector2) -> bool:
			for su: float in [-1.0, 0.0, 1.0]:
				for sv2: float in [-1.0, 1.0]:
					var q := c + u * su * pu + v * sv2 * pv
					if cesta_kraj_osa(q.x, q.y).x < 0.0:
						return false
			return true
		if volno.call(p0):
			zust.append(it)
			continue
		var hotovo := false
		for k in range(1, 13):
			for sm: Vector2 in smery:
				var c2 := p0 + sm * 0.25 * k
				if not hotovo and volno.call(c2):
					it["p"] = [c2.x, _vyska_min(c2.x, c2.y, 0.8) - 0.03, c2.y]
					hotovo = true
		if hotovo:
			posunuto += 1
			zust.append(it)
			print("predmety mimo cesty: posunut %s z (%.1f, %.1f)" % [it["id"], p0.x, p0.y])
		else:
			pryc += 1
			print("predmety mimo cesty: VYNECHAN %s u (%.1f, %.1f)" % [it["id"], p0.x, p0.y])
	data["vybaveni"] = zust
	print("predmety mimo cesty (krok 9): posunuto %d, vynechano %d" % [posunuto, pryc])


## Mistni souradnice dilu (x, z) a vzdalenost za okrajem ctverce (< 0 uvnitr).
func _ryb_mist(x: float, z: float) -> Vector3:
	var q := _ryb_inv * Vector3(x, 0, z)
	return Vector3(q.x, q.z, maxf(absf(q.x), absf(q.z)) - RYB_POL)


## Teren hry pod dilem: nize nez povrch dilu (NAVOD bod 2), u okraje tesne pod nim; za okrajem pas k okraji (+0,30).
func ryb_teren(x: float, z: float, y: float) -> float:
	if _ryb_y == INF:
		return y
	var m := _ryb_mist(x, z)
	if m.z > RYB_PAS:
		return y
	var okraj := _ryb_y + 0.30
	if m.z >= 0.0:
		return minf(y, lerpf(okraj - 0.02, y, smoothstep(0.0, RYB_PAS, m.z)))
	var h := ryb_vyska(x, z)
	if h == INF:
		h = okraj
	return minf(y, h - (0.06 if m.z > -2.5 else 0.6))


## Mrizka vysek (louka, rostliny) na dilu = povrch dilu.
func ryb_mrizka(x: float, z: float, y: float) -> float:
	if _ryb_y == INF:
		return y
	var m := _ryb_mist(x, z)
	if m.z > RYB_PAS:
		return y
	if m.z >= 0.0:
		return minf(y, lerpf(_ryb_y + 0.28, y, smoothstep(0.0, RYB_PAS, m.z)))
	var h := ryb_vyska(x, z)
	return h if h != INF else y


## Voda nebo bahno dilu (bez travy a rostlin).
func ryb_voda(x: float, z: float) -> bool:
	if _ryb_y == INF:
		return false
	var h := ryb_vyska(x, z)
	return h != INF and h < _ryb_y + 0.12


func _rybnik_dil(root: Node3D, parent: Node3D) -> void:
	if _ryb_scena == null:
		return
	_ryb_scena.transform = _ryb_xf
	parent.add_child(_ryb_scena)
	var tm: Material = null
	for t in root.find_children("Teren_ves*", "MeshInstance3D", true, false):
		var mi0 := t as MeshInstance3D
		for si in mi0.mesh.get_surface_count():
			var sm0 := mi0.get_active_material(si)
			if sm0 is ShaderMaterial and String((sm0 as ShaderMaterial).shader.resource_path).ends_with("zem.gdshader"):
				tm = sm0
	var vm := material("voda")
	for n in _ryb_scena.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		if nm.begins_with("Rybnik_Teren") or nm.begins_with("Rybnik_Voda"):
			# importovana sit nedavala shaderu barvy vrcholu (voda neviditelna: COLOR.r = hloubka) - znovu z poli
			var am := ArrayMesh.new()
			for si in mi.mesh.get_surface_count():
				am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, mi.mesh.surface_get_arrays(si))
			mi.mesh = am
		if nm.begins_with("Rybnik_Teren") and tm:
			mi.material_override = tm
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		elif nm.begins_with("Rybnik_Voda"):
			mi.material_override = vm
			_hladina(mi, 0)
		else:
			mi.visibility_range_end = 90.0
	# Misa 0.91/0.92 (tablet, stani na lavce): move_and_slide 21-59 ms, pod nohama Rybnik_Lavka ConcavePolygon (4 994
	# troj., prkna a kuly) - na PC 0,3 ms. Lavka = jedna konvexni obalka (prkna jsou skoro rovina, kuly pod vodou);
	# konvexni tvar je pro CharacterBody nejlevnejsi a nema hrany mezi prkny, o ktere se kapsle zachytava.
	for lv in _ryb_scena.find_children("Rybnik_Lavka*", "MeshInstance3D", true, false):
		var lm := lv as MeshInstance3D
		for sb in lm.find_children("*", "CollisionShape3D", true, false):
			var cs := sb as CollisionShape3D
			if cs.shape is ConcavePolygonShape3D:
				cs.shape = lm.mesh.create_convex_shape(true, true)
				print("rybnik: kolize lavky konvexni (%d bodu)" % (cs.shape as ConvexPolygonShape3D).points.size())
	# Misa 0.96 (tablet, u rybnika): move_and_slide 30-40 ms, pod nohama Rybnik_Kameny ConcavePolygon (11 840 troj.).
	# Sit je 97 oddelenych kamenu - kazdy kamen vlastni konvexni obal (jako lavka), jedno telo.
	for kv in _ryb_scena.find_children("Rybnik_Kameny*", "MeshInstance3D", true, false):
		var km := kv as MeshInstance3D
		for sb in km.find_children("*", "CollisionShape3D", true, false):
			var cs := sb as CollisionShape3D
			if cs.shape is ConcavePolygonShape3D:
				var dily := _konvexni_dily(km.mesh)
				for i in dily.size():
					var c2 := CollisionShape3D.new()
					c2.shape = dily[i]
					c2.transform = cs.transform
					cs.get_parent().add_child(c2)
				cs.queue_free()
				print("rybnik: kolize kamenu %d konvexnich dilu" % dily.size())
	print("rybnik: dil vlozen, material terenu %s, voda %s" % [tm != null, vm != null])


## Vodni mlyn (Misa 21:44: model z Disku Modely/budovy/mlyn-1.zip, NAVOD_MLYN.md): dil 40 x 40 m na miste z voda.json
## mlyn.dil (tools/krok_b/mlyn_misto.py). Teren sveta pod dilem a hladiny nahonu, vantroku a lednice stavi Blender
## (kraj.mlyn_pad, Toky_voda) - hra jen vlozi model: teren dilu dostane material terenu hry (barvy vrcholu G/A podle
## navodu), kolo a cevnik se toci, interier jen zblizka, z dalky LOD1. Kolize podle navodu (-col, -convcolonly).
## Kone ve staji tvrze (lokace.json staj_kone): model postaveny kopyty na zem (obal siti), hlavou k jeslim; kolize kvadr
## pres kone (hrac jim neprojde). Zatim sochy - kun s animacemi pro jizdu ceka na model.
func _staj_kone(parent: Node3D) -> void:
	var lok: Dictionary = Pravidla.cti("lokace", "staj_kone")
	var ms: Dictionary = lok.get("mistnost", {})
	if not ms.is_empty():
		var c: Array = ms["stred"]
		var vz: Array = ms["velikost"]
		var a: Array = ms["ambient"]
		var y0 := _vyska(float(c[0]), float(c[1]))
		data["mistnosti"].append({"name": "staj_kone", "title": "Stáj", "pos": [float(c[0]), y0 + float(vz[1]) * 0.5, float(c[1])],
				"size": vz, "ambient": a})
	for k: Dictionary in lok["kone"]:
		if not ResourceLoader.exists(String(k["model"])):
			print("staj: model %s chybi" % k["model"])
			continue
		var m := (load(String(k["model"])) as PackedScene).instantiate() as Node3D
		m.name = "Staj_kun"
		parent.add_child(m)
		var mer := float(k.get("meritko", 1.0))
		var bb := AABB()
		var prvni := true
		for mi in m.find_children("*", "MeshInstance3D", true, false):
			var b := _rel_xf(mi as MeshInstance3D, m) * (mi as MeshInstance3D).get_aabb()
			bb = b if prvni else bb.merge(b)
			prvni = false
		var x := float(k["stred"][0])
		var z := float(k["stred"][1])
		var yaw := float(k["natoceni"])
		bb = AABB(bb.position * mer, bb.size * mer)
		m.transform = Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3.ONE * mer), Vector3(x, _vyska(x, z) - bb.position.y, z) - Basis(Vector3.UP, yaw) * Vector3(bb.get_center().x, 0.0, bb.get_center().z))
		# kun s kostrou: usek dlouhe animace modelu jako smycka (stani), obal siti se skinem pres celeho kone
		var aps := m.find_children("*", "AnimationPlayer", true, false)
		if k.has("klip") and not aps.is_empty():
			var ap := aps[0] as AnimationPlayer
			var zdroj := ap.get_animation(ap.get_animation_list()[0])
			var lib := AnimationLibrary.new()
			lib.add_animation("staj", klip_z_useku(zdroj, float(k["klip"][0]), float(k["klip"][1])))
			ap.add_animation_library("staj_kun", lib)
			ap.play("staj_kun/staj")
			for g in m.find_children("*", "GeometryInstance3D", true, false):
				(g as GeometryInstance3D).custom_aabb = AABB(Vector3(-400.0, -50.0, -400.0), Vector3(800.0, 400.0, 800.0))
		for mi in m.find_children("*", "GeometryInstance3D", true, false):
			(mi as GeometryInstance3D).visibility_range_end = 70.0
		var sb := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var bx := BoxShape3D.new()
		bx.size = Vector3(bb.size.x * 0.8, bb.size.y * 0.8, bb.size.z * 0.9)
		cs.shape = bx
		sb.add_child(cs)
		parent.add_child(sb)
		sb.global_position = m.global_position + Basis(Vector3.UP, yaw) * Vector3(bb.get_center().x, bb.get_center().y, bb.get_center().z)
		sb.rotation.y = yaw
		print("staj: kun %s u (%.1f, %.1f), rozmer %s" % [String(k["model"]).get_file(), x, z, bb.size])


var _mlyn_inv := Transform3D()
var _mlyn_tri := {}                      # bunka 2 m -> [[a, b, c, g_a, g_b, g_c]] terenu dilu (svet, G = trava)
var _mlyn_budova := AABB()               # pudorys mlyna v dilu (podezdivka) - bez travy


func _mlyn_tri_postav(mi: MeshInstance3D, xf: Transform3D) -> void:
	for si in mi.mesh.get_surface_count():
		var arr := mi.mesh.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var col: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		var n := idx.size() if idx.size() > 0 else v.size()
		for t in range(0, n, 3):
			var i0 := idx[t] if idx.size() > 0 else t
			var i1 := idx[t + 1] if idx.size() > 0 else t + 1
			var i2 := idx[t + 2] if idx.size() > 0 else t + 2
			var a := xf * v[i0]
			var b := xf * v[i1]
			var c := xf * v[i2]
			var ga := col[i0].g if col.size() > 0 else 1.0
			var gb := col[i1].g if col.size() > 0 else 1.0
			var gc := col[i2].g if col.size() > 0 else 1.0
			for cx in range(floori(minf(a.x, minf(b.x, c.x)) / 2.0), floori(maxf(a.x, maxf(b.x, c.x)) / 2.0) + 1):
				for cz in range(floori(minf(a.z, minf(b.z, c.z)) / 2.0), floori(maxf(a.z, maxf(b.z, c.z)) / 2.0) + 1):
					var key := Vector2i(cx, cz)
					if not _mlyn_tri.has(key):
						_mlyn_tri[key] = []
					(_mlyn_tri[key] as Array).append([a, b, c, ga, gb, gc])


## Teren dilu mlyna v bode: (vyska, trava 0..1 z barvy vrcholu G podle NAVOD_MLYN bod 3) nebo (INF, 0) mimo dil.
## Pudorys mlyna (podezdivka) bez travy.
func mlyn_teren(x: float, z: float) -> Vector2:
	if _mlyn_tri.is_empty():
		return Vector2(INF, 0.0)
	var best := Vector2(-INF, 0.0)
	var p := Vector2(x, z)
	for t: Array in _mlyn_tri.get(Vector2i(floori(x / 2.0), floori(z / 2.0)), []):
		var a: Vector3 = t[0]
		var b: Vector3 = t[1]
		var c: Vector3 = t[2]
		var v0 := Vector2(b.x - a.x, b.z - a.z)
		var v1 := Vector2(c.x - a.x, c.z - a.z)
		var v2 := p - Vector2(a.x, a.z)
		var den := v0.x * v1.y - v1.x * v0.y
		if absf(den) < 1e-9:
			continue
		var u := (v2.x * v1.y - v1.x * v2.y) / den
		var w := (v0.x * v2.y - v2.x * v0.y) / den
		if u < -0.001 or w < -0.001 or u + w > 1.001:
			continue
		var y := a.y + u * (b.y - a.y) + w * (c.y - a.y)
		if y > best.x:
			best = Vector2(y, float(t[3]) + u * (float(t[4]) - float(t[3])) + w * (float(t[5]) - float(t[3])))
	if best.x == -INF:
		return Vector2(INF, 0.0)
	var q := _mlyn_inv * Vector3(x, 0.0, z)
	if _mlyn_budova.size != Vector3.ZERO and _mlyn_budova.grow(0.4).has_point(Vector3(q.x, _mlyn_budova.get_center().y, q.z)):
		best.y = 0.0
	return best


func _mlyn_dil(root: Node3D, parent: Node3D) -> void:
	var d: Dictionary = Pravidla.cti("voda", "mlyn", "dil")
	if not ResourceLoader.exists(String(d["model"])):
		print("mlyn: model %s chybi (balik z_mlyn)" % d["model"])
		return
	var xf := Transform3D(Basis(Vector3.UP, float(d["natoceni"])), Vector3(float(d["stred"][0]), float(d["y_dvora"]), float(d["stred"][1])))
	var sc := (load(String(d["model"])) as PackedScene).instantiate() as Node3D
	sc.name = "Mlyn_dil"
	sc.transform = xf
	_mlyn_inv = xf.affine_inverse()
	parent.add_child(sc)
	var tm: Material = null
	for t in root.find_children("Teren*", "MeshInstance3D", true, false):
		var mi0 := t as MeshInstance3D
		for si in mi0.mesh.get_surface_count():
			var sm0 := mi0.get_active_material(si)
			if sm0 is ShaderMaterial and String((sm0 as ShaderMaterial).shader.resource_path).ends_with("zem.gdshader"):
				tm = sm0
		if tm:
			break
	var dil_do := float(d["dil_do_m"])
	for jm0: String in d.get("vynechat_uzly", []):
		var vn := sc.find_child(jm0, true, false)
		if vn:
			vn.get_parent().remove_child(vn)
			vn.free()
	_mlyn_dvere(sc, root, xf, d)
	var interier := sc.find_child("Mlyn_Interier_skupina", true, false)
	var n := 0
	for nd in sc.find_children("*", "MeshInstance3D", true, false):
		var mi := nd as MeshInstance3D
		var nm := String(mi.name)
		mi.visibility_range_end = float(d["interier_do_m"]) if interier and interier.is_ancestor_of(mi) else dil_do
		if nm.begins_with("Mlyn_Teren"):
			if tm:
				mi.material_override = tm
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_mlyn_tri_postav(mi, xf * _rel_xf(mi, sc))
		elif nm.begins_with("Mlyn_Podezdivka"):
			_mlyn_budova = _rel_xf(mi, sc) * mi.get_aabb()
		n += 1
	for jm: String in ["Mlyn_Kolo", "Mlyn_Cevnik"]:
		var k := sc.find_child(jm, true, false) as Node3D
		if k == null:
			continue
		k.set_script(preload("res://scripts/mlyn_kolo.gd"))
		k.set("osa", Vector3.RIGHT if jm == "Mlyn_Kolo" else Vector3.UP)
		k.set("plna", float(d["kolo_rad_s"]) * (1.0 if jm == "Mlyn_Kolo" else float(d["cevnik_nasobek"])))
		k.set("rozjezd_s", float(d["ovladani"]["rozjezd_s"]))
		k.set("bezi", bool(d["ovladani"]["bezi_na_zacatku"]))
		if jm == "Mlyn_Kolo":
			k.set("pad", root.find_child("Mlyn_pad_vody", true, false))      # dopad vody z vantroku (kraj._mlyn_pad_vody)
		# skript pridany uzlu, ktery uz je ve strome: Godot nezavola _ready ani nezapne _process (0.98: kolo stalo,
		# kamen hlasil „Kamen stoji“ i po stavidle) - zapnout rucne
		k.call("_ready")
		k.set_process(true)
		k.add_to_group("mlyn_kolo")
	# ovladani mlyna (voda.json mlyn.dil.ovladani): paka stavidla a mleti u kamene (main._on_use, druh mlyn_*)
	var ov: Dictionary = d["ovladani"]
	for dr: Array in [["mlyn_stavidlo", "stavidlo", "Stavidlo"], ["mlyn_mleti", "mleti", "Mlýnský kámen"]]:
		var lp: Array = ov[dr[1]]
		var wp := xf * Vector3(float(lp[0]), float(lp[1]), float(lp[2]))
		data["pouziti"].append({"kind": dr[0], "pos": [wp.x, wp.y, wp.z], "r": float(ov["dosah_m"]) / 0.62, "nazev": dr[2]})
	if ResourceLoader.exists(String(d["lod1"])):
		var l1 := (load(String(d["lod1"])) as PackedScene).instantiate() as Node3D
		l1.name = "Mlyn_lod1"
		l1.transform = xf
		parent.add_child(l1)
		for nd in l1.find_children("*", "MeshInstance3D", true, false):
			(nd as MeshInstance3D).visibility_range_begin = float(d["lod1_od_m"])
		for nd in l1.find_children("*", "CollisionShape3D", true, false):
			nd.queue_free()
	print("mlyn: dil u (%.0f, %.0f) y %.2f, %d siti, material terenu %s" % [xf.origin.x, xf.origin.z, xf.origin.y, n, tm != null])


## Dvere mlyna (Misa 28. 10. „do mlyna se neda dostat, zadne dvere nefunguji“): kridla Mlyn_Dvere_* maji pant v pocatku
## uzlu - presun pod uzel v koreni Tvrz (pohyb.gd hleda kridla jen tam) se stejnou polohou, zaznam pohybu jako dvere
## domu vsi; kridlo se otvira dovnitr budovy (k jejimu stredu), dvere_otevrene z voda.json mlyn.dil na zacatku otevrene.
func _mlyn_dvere(sc: Node3D, root: Node3D, xf: Transform3D, d: Dictionary) -> void:
	var drz := Node3D.new()
	drz.name = "Mlyn_dvere"
	drz.transform = xf
	root.add_child(drz)
	for nd in sc.find_children("Mlyn_Dvere_*", "MeshInstance3D", true, false):
		var dv := nd as MeshInstance3D
		var dk := String(dv.name).trim_prefix("Mlyn_Dvere_")
		var lok := _rel_xf(dv, sc)
		dv.get_parent().remove_child(dv)
		drz.add_child(dv)
		dv.transform = lok
		var jm := "Pohyb_mlyn_" + dk
		dv.name = jm
		var ab := dv.mesh.get_aabb()
		var cl := ab.get_center()
		var otev := 100.0
		var cil := Vector3.ZERO                                  # stred budovy (model: budova kolem pocatku)
		var p_plus := dv.position + Basis(Vector3.UP, deg_to_rad(otev)) * cl
		var p_minus := dv.position + Basis(Vector3.UP, deg_to_rad(-otev)) * cl
		if Vector2(p_minus.x, p_minus.z).distance_to(Vector2(cil.x, cil.z)) < Vector2(p_plus.x, p_plus.z).distance_to(Vector2(cil.x, cil.z)):
			otev = -otev
		var use := xf * (dv.position + cl + Vector3(0, 0.95 - cl.y, 0))
		var otevrene := (d.get("dvere_otevrene", []) as Array).has(String(nd.name)) or (d.get("dvere_otevrene", []) as Array).has("Mlyn_Dvere_" + dk)
		data["pohyb"].append({"name": jm, "kind": "dvere", "group": "mlyn_" + dk,
				"cols": [[cl.x, cl.y, cl.z, maxf(ab.size.x, 0.06), ab.size.y, maxf(ab.size.z, 0.06)]],
				"pos": [use.x, use.y, use.z], "use": [use.x, use.y, use.z], "open": otev, "init": otev if otevrene else 0.0, "dur": 1.0})


## Rozdeli sit na souvisle kusy (spolecne vrcholy podle polohy) a vrati konvexni obal kazdeho kusu.
static func _konvexni_dily(m: Mesh) -> Array[ConvexPolygonShape3D]:
	var body := PackedVector3Array()
	var idx := PackedInt32Array()
	for si in m.get_surface_count():
		var a := m.surface_get_arrays(si)
		var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
		var ix: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		var o := body.size()
		body.append_array(v)
		if ix.is_empty():
			for i in v.size():
				idx.append(o + i)
		else:
			for i in ix:
				idx.append(o + i)
	# souvisle kusy: vrcholy se stejnou polohou spoji, pak kazdy trojuhelnik (union-find, bez lambd - pomale)
	var par := PackedInt32Array()
	par.resize(body.size())
	var klic := {}
	for i in body.size():
		var k := Vector3i((body[i] * 1000.0).round())
		par[i] = klic.get(k, i)
		if not klic.has(k):
			klic[k] = i
	for t in range(0, idx.size(), 3):
		var r := _uf_koren(par, idx[t])
		for j in [1, 2]:
			var q := _uf_koren(par, idx[t + j])
			if q != r:
				par[q] = r
	var kusy := {}
	for i in body.size():
		var r := _uf_koren(par, i)
		if not kusy.has(r):
			kusy[r] = []                     # Array (odkaz): Packed pole ve slovniku by se pri append kopirovalo
		(kusy[r] as Array).append(body[i])
	var out: Array[ConvexPolygonShape3D] = []
	for r in kusy:
		var pts := PackedVector3Array(kusy[r] as Array)
		if pts.size() < 4:
			continue
		var s := ConvexPolygonShape3D.new()
		s.points = pts
		out.append(s)
	return out


static func _uf_koren(par: PackedInt32Array, a: int) -> int:
	while par[a] != a:
		a = par[a]
	return a


## Uprava vysky terenu (vrcholy siti i mrizka 2 m): brody a rovina trhu.
func uprava_y(x: float, z: float, y: float) -> float:
	var p := Vector2(x, z)
	for br: Array in brody:
		var q: Vector2 = p - (br[0] as Vector2)
		var dr: Vector2 = br[1]
		var al := absf(q.dot(dr))
		var la := absf(q.dot(dr.orthogonal()))
		var w: float = br[2]
		if la > 5.0 or al > w + 40.0:
			continue
		# Misa 0.76 "brod je hraz": dno v korytu 0,45 m pod vodou (0,28 = skoro pruhledna voda = suchy pas pres potok),
		# brod jen 4 m siroky; mimo koryto najezdy 1:4 zarezane do brehu
		var cil: float = float(br[3]) - 0.45 + maxf(al - w, 0.0) * 0.25
		# v korytu a jeho svazich (zarez az 2 m pod okolim) presne profil brodu, dal jen srazit breh
		var yn := minf(y, cil) if al <= w else (cil if al <= w + 4.0 else minf(y, cil))
		y = lerpf(y, yn, 1.0 - smoothstep(2.5, 4.5, la))
	# Misa 24. 10. "leseni tesne u steny - stenu srovnat": v pasu leseni vybrat skalu do 5 m za patou (dno), dal
	# lavice ve vysce steny; svislou stenu v miste paty dela vlastni sit (_lom_stena_svisla - teren ma body po 5 m)
	if z > LESENI_Z.x - 4.0 and z < LESENI_Z.y + 4.0 and _lom_srov.has(roundi(z)):
		var q: Vector4 = _lom_srov[roundi(z)]
		var u := x - q.x
		var wz := smoothstep(LESENI_Z.x - 4.0, LESENI_Z.x - 0.5, z) * (1.0 - smoothstep(LESENI_Z.y + 0.5, LESENI_Z.y + 4.0, z))
		if u <= 0.3 and u > -5.2:
			y = lerpf(y, minf(y, q.w), wz)
		elif u <= -5.2 and u > -q.y - 6.0:
			y = lerpf(y, maxf(y, q.z), wz)
	var d := v_trzisti(x, z)
	if d < 5.0 and _trz_y != INF:
		y = lerpf(y, _trz_y, 1.0 - smoothstep(0.0, 5.0, d))
	return y


var _trz_y := INF


var _lom_srov := {}                # z -> (pata x, hloubka lavice k, vyska lavice, vyska paty)


func _upravy_terenu(root: Node3D) -> void:
	_najdi_brody()
	_ryb_priprav()
	_domy_vysky()
	# pata lomu z puvodniho terenu (lom_stena_x se cachuje), pak profil srovnane steny za lesenim
	for zi in range(int(LOM_Z.x) - 4, int(LOM_Z.y) + 5):
		lom_stena_x(float(zi))
	for zi in range(int(LESENI_Z.x) - 5, int(LESENI_Z.y) + 6):
		var f := lom_stena_x(float(zi))
		var yf := _vyska(f, float(zi))
		var k := 1.0
		while k < 12.0 and _vyska(f - k, float(zi)) - yf < 9.5:
			k += 0.5
		_lom_srov[zi] = Vector4(f, k, minf(_vyska(f - k, float(zi)), yf + 10.0), yf)
	# rovina trhu: prumer vysky plochy
	var s := 0.0
	var n := 0
	for u in range(int(TRZ_R.position.x), int(TRZ_R.end.x) + 1, 2):
		for v in range(int(TRZ_R.position.y), int(TRZ_R.end.y) + 1, 2):
			var p := trz_bod(u, v)
			s += _vyska(p.x, p.y)
			n += 1
	_trz_y = s / maxf(n, 1) if TRZISTE else INF
	var zmen := 0
	for t in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(t.name)
		if nm == "Teren_obzor" or nm == "Teren_cesta_kamen":
			continue
		var mi := t as MeshInstance3D
		var am := mi.mesh as ArrayMesh
		if am == null:
			continue
		var xf := mi.global_transform
		var inv := xf.affine_inverse()
		var nove := ArrayMesh.new()
		var zde := 0
		for si in am.get_surface_count():
			var arr := am.surface_get_arrays(si)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			for i in v.size():
				var w := xf * v[i]
				var y2 := dum_teren(w.x, w.z, ryb_teren(w.x, w.z, uprava_y(w.x, w.z, w.y)))      # dum az po pasu rybnika
				if absf(y2 - w.y) > 0.005:
					w.y = y2
					v[i] = inv * w
					zde += 1
			arr[Mesh.ARRAY_VERTEX] = v
			arr[Mesh.ARRAY_NORMAL] = null
			arr[Mesh.ARRAY_TANGENT] = null
			var st := SurfaceTool.new()
			st.create_from_arrays(arr)
			st.generate_normals()
			if arr[Mesh.ARRAY_TEX_UV] != null:
				st.generate_tangents()
			nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, st.commit_to_arrays())
			nove.surface_set_material(si, am.surface_get_material(si))
			nove.surface_set_name(si, am.surface_get_name(si))
		if zde > 0:
			mi.mesh = nove
			zmen += zde
	print("upravy terenu: %d vrcholu (brody %d, rovina trhu y %.2f)" % [zmen, brody.size(), _trz_y])


## Kameny brodu: pres celou sirku (5 m) a delku melciny + najezdy, ploche (sterk) a uprostred slapaci kameny.
func _brody() -> void:
	var r: Dictionary = data["rostliny"]
	var male := ["kamen_maly_1_0", "kamen_maly_2_0", "kamen_maly_3_0", "kamen_maly_4_0", "kamen_maly_5_0"]
	var velke := ["kamen_zula_1_0", "kamen_zula_2_0", "kamen_droba_1_0"]
	var vys := {}
	for k: String in male + velke:
		if not r.has(k) or (r[k] as Array).is_empty():
			return
		var me := _skala_sit(k)
		vys[k] = me.get_aabb().size.y if me else 0.3
	var rng := RandomNumberGenerator.new()
	rng.seed = 2207
	var n_k := 0
	for br: Array in brody:
		var c: Vector2 = br[0]
		var dr: Vector2 = br[1]
		var bok := dr.orthogonal()
		var w: float = float(br[2]) + 2.0
		var hl: float = br[3]
		var t := -w
		while t <= w:
			for s_: float in [-2.0, -1.0, 0.0, 1.0, 2.0]:
				var p := c + dr * (t + rng.randf_range(-0.15, 0.15)) + bok * (s_ + rng.randf_range(-0.3, 0.3))
				var dno := _vyska(p.x, p.y)
				var stred := absf(s_) < 0.1 and absf(t) < float(br[2])
				var k: String = velke[rng.randi() % velke.size()] if stred else male[rng.randi() % male.size()]
				var cil := (hl + 0.04 - dno) if stred else 0.07
				var sy := clampf(cil / float(vys[k]), 0.05, 3.0)
				var sx := (rng.randf_range(0.55, 0.75) if stred else rng.randf_range(0.3, 0.5)) / maxf(float(vys[k]), 0.05) * 0.5
				var bs := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sx, sy, sx))
				(r[k] as Array).append([bs.x.x, bs.y.x, bs.z.x, p.x, bs.x.y, bs.y.y, bs.z.y, dno - 0.03, bs.x.z, bs.y.z, bs.z.z, p.y])
				if stred:
					kameny_toku.append(Vector4(p.x, p.y, 0.3, atan2(dr.y, dr.x) + PI * 0.5))
				n_k += 1
			t += 0.5
	print("brody: kamenu %d" % n_k)


## Radce 09:20 / 07:15 C (Misa 0.73 "rybnik bez rakosu a travy"): navesni rybnicek - rakos a orobinec v pasu
## od 0,3 m ve vode do 1,2 m na brehu (husteji na severni a vychodni strane, mezery pro pristup k vode), mezi nimi
## par kamenu; travu az k vode dela louka (louka._vzorek, nadrz._v_kruhu).
func _rybnik_breh() -> void:
	if _ryb_y != INF:
		_rybnik_breh_dil()
		return
	if nadrz == null:
		return
	var r: Dictionary = data["rostliny"]
	var druhy := ["rakos_1_0", "rakos_2_0", "orobinec_1_0", "orobinec_2_0"]
	var mer := {}
	for k: String in druhy:
		if not r.has(k) or (r[k] as Array).is_empty():
			return
		var t: Array = r[k][0]
		mer[k] = Vector3(t[0], t[4], t[8]).length()
	var rng := RandomNumberGenerator.new()
	rng.seed = 5250
	var n := 0
	var na := 220
	for i in na:
		var a := TAU * (i + rng.randf()) / na
		# pristup k vode (u navsi, zapad) bez rakosu
		var pristup := absf(wrapf(a - PI, -PI, PI)) < 0.45
		var hust := 0.35 if pristup else (0.95 if sin(a + 0.6) > 0.0 else 0.7)
		for _j in 2:
			if rng.randf() > hust:
				continue
			var k := 0.93 + rng.randf() * 0.14
			var p: Vector2 = nadrz._pond_bod(a, k)
			var kk: String = druhy[rng.randi() % 4] if rng.randf() < 0.8 else druhy[rng.randi() % 2]
			var y := minf(_vyska(p.x, p.y), float(nadrz.nadrze[0]["y"]) if not nadrz.nadrze.is_empty() else INF)
			for nd: Dictionary in nadrz.nadrze:
				if not (nd["kruh"] as Array).is_empty():
					y = maxf(minf(_vyska(p.x, p.y), float(nd["y"]) + 0.1), float(nd["y"]) - 0.4)
			(r[kk] as Array).append(_xf(p.x, y - 0.05, p.y, rng.randf() * TAU, float(mer[kk]) * rng.randf_range(0.8, 1.25)))
			n += 1
	print("rybnik ve vsi: rakos a orobinec %d" % n)


## Rakos a orobinec u rybnika Lhota (NAVOD bod 4-5): pas od 0,3 m ve vode po ~1,2 m na brehu (podle vysky povrchu
## dilu), ve shlucich; volne okoli lavky, susaku a dlabanky a napajedlo (nejmelci kus brehu). Vrby hlavate a olse
## na sussim brehu.
func _rybnik_breh_dil() -> void:
	var r: Dictionary = data["rostliny"]
	var druhy := ["rakos_1_0", "rakos_2_0", "orobinec_1_0", "orobinec_2_0"]
	var mer := {}
	for k: String in druhy + ["vrba_hlavata_1_0", "vrba_hlavata_2_0", "olse_mlada_0"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			var t: Array = r[k][0]
			mer[k] = Vector3(t[0], t[4], t[8]).length()
		elif r.has(k):
			mer[k] = 1.0                             # rakos jen u rybnicku - po jeho vyrazeni prazdny, meritko modelu
	for k: String in druhy:
		if not mer.has(k):
			print("rybnik Lhota: chybi druh %s" % k)
			return
	var ns := FastNoiseLite.new()
	ns.seed = 879
	ns.frequency = 0.18
	var rng := RandomNumberGenerator.new()
	rng.seed = 5251
	var volno := [Rect2(1.8, 2.4, 6.0, 6.2), Rect2(4.6, 2.6, 5.4, 4.2), Rect2(1.6, 8.0, 5.2, 4.6)]   # lavka, dlabanka, susak (x, z dilu)
	var n := 0
	var st := 0
	var y0 := _ryb_y
	var x := -RYB_POL + 1.0
	while x < RYB_POL - 1.0:
		var z := -RYB_POL + 1.0
		while z < RYB_POL - 1.0:
			var w := _ryb_xf * Vector3(x + rng.randf_range(-0.3, 0.3), 0, z + rng.randf_range(-0.3, 0.3))
			var h := ryb_vyska(w.x, w.z)
			z += 0.55
			if h == INF or h < y0 - 0.3 or h > y0 + 0.28:
				continue
			var m := _ryb_mist(w.x, w.z)
			var ven := false
			for rc: Rect2 in volno:
				ven = ven or rc.has_point(Vector2(m.x, m.y))
			# napajedlo: severni breh (z dilu < -6) v pasu x -4..4 bez rakosu
			if ven or (m.y < -6.0 and absf(m.x) < 4.0):
				continue
			var hus := 0.25 + 0.75 * smoothstep(-0.1, 0.45, ns.get_noise_2d(w.x, w.z))
			if rng.randf() > hus:
				continue
			var kk: String = druhy[rng.randi() % 2] if h < y0 else druhy[rng.randi() % 4]
			(r[kk] as Array).append(_xf(w.x, h - 0.04, w.z, rng.randf() * TAU, float(mer[kk]) * rng.randf_range(0.8, 1.2)))
			n += 1
		x += 0.55
	# stromy na brehu: suchy breh 0,4-1,2 m nad hladinou, od sebe aspon 7 m, mimo lavku
	var stromy := []
	for k in 400:
		if stromy.size() >= 7:
			break
		var lx := rng.randf_range(-24.0, 24.0)
		var lz := rng.randf_range(-24.0, 24.0)
		var w := _ryb_xf * Vector3(lx, 0, lz)
		var h := ryb_vyska(w.x, w.z)
		if h == INF or h < y0 + 0.4 or h > y0 + 1.3 or Rect2(0.0, 0.0, 12.0, 14.0).has_point(Vector2(lx, lz)):
			continue
		var blizko := false
		for q: Vector2 in stromy:
			blizko = blizko or q.distance_to(Vector2(w.x, w.z)) < 7.0
		if blizko:
			continue
		var kk2: String = ["vrba_hlavata_1_0", "vrba_hlavata_2_0", "olse_mlada_0"][stromy.size() % 3]
		if not mer.has(kk2):
			continue
		(r[kk2] as Array).append(_xf(w.x, h - 0.1, w.z, rng.randf() * TAU, float(mer[kk2]) * rng.randf_range(0.85, 1.1)))
		stromy.append(Vector2(w.x, w.z))
		st += 1
	print("rybnik Lhota: rakos a orobinec %d, stromu %d" % [n, st])


## Tvrz zvenci (radce: prvni dojem): u paty hradeb zarostle - koprivy, vysoka trava, pampelisky (kosa tam
## nedosahne); na brehu prikopu vrby hlavate (orezavane, lidska stopa). Obvod hradeb z exportu: x -27..18, z -16..17.
func _tvrz_zvencí() -> void:
	var r: Dictionary = data["rostliny"]
	for k: String in ["nettle_plant_0", "grass_medium_02_0", "dandelion_01_0"]:
		if not r.has(k) or (r[k] as Array).is_empty():
			return
	var mer := {}
	# vrba hlavata jen kdyz je v katalogu (druhy.json pouzit)
	for k: String in ["nettle_plant_0", "grass_medium_02_0", "dandelion_01_0", "vrba_hlavata_1_0", "vrba_hlavata_2_0"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			var t: Array = r[k][0]
			mer[k] = Vector3(t[0], t[4], t[8]).length()
	var voda := float(data.get("voda_y", -2.75))
	var rng := RandomNumberGenerator.new()
	rng.seed = 1390
	var x0 := -27.4
	var x1 := 18.3
	var z0 := -16.4
	var z1 := 17.2
	var obvod := 2.0 * ((x1 - x0) + (z1 - z0))
	var n := 0
	for i in int(obvod * 3.0):
		var u := rng.randf() * obvod
		var off := 0.3 + pow(rng.randf(), 1.5) * 2.2
		var p: Vector2
		if u < x1 - x0:
			p = Vector2(x0 + u, z0 - off)
		elif u < 2.0 * (x1 - x0):
			p = Vector2(x0 + u - (x1 - x0), z1 + off)
		elif u < 2.0 * (x1 - x0) + (z1 - z0):
			p = Vector2(x0 - off, z0 + u - 2.0 * (x1 - x0))
		else:
			p = Vector2(x1 + off, z0 + u - 2.0 * (x1 - x0) - (z1 - z0))
		if absf(p.x + 3.0) < 2.5 and p.y > z1:
			continue                                    # pred branou a mostem volno
		var y := _vyska(p.x, p.y)
		if y < voda + 0.25:
			continue
		var w := rng.randf()
		var k := "nettle_plant_0" if w < 0.4 else ("grass_medium_02_0" if w < 0.85 else "dandelion_01_0")
		(r[k] as Array).append(_xf(p.x, y - 0.03, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.8, 1.3)))
		n += 1
	# kere a kapradi na valu (Misa 0.63: "val prazdny"): sipek, bez, kapradi ve shlucich, ne pred branou
	for kk: String in ["sipek_0", "bez_cerny_1_0", "bez_cerny_2_0", "kapradi_1_0", "fern_02_0", "kopretiny_0"]:
		if not r.has(kk) or (r[kk] as Array).is_empty():
			continue
		var sc0 := 1.0 if kk.begins_with("kopret") else Vector3(r[kk][0][0], r[kk][0][4], r[kk][0][8]).length()
		var pocet := 9 if kk.begins_with("sipek") or kk.begins_with("bez") else 22
		for _i in pocet:
			var u := rng.randf() * obvod
			var off := 0.6 + rng.randf() * 1.6
			var p: Vector2
			if u < x1 - x0:
				p = Vector2(x0 + u, z0 - off)
			elif u < 2.0 * (x1 - x0):
				p = Vector2(x0 + u - (x1 - x0), z1 + off)
			elif u < 2.0 * (x1 - x0) + (z1 - z0):
				p = Vector2(x0 - off, z0 + u - 2.0 * (x1 - x0))
			else:
				p = Vector2(x1 + off, z0 + u - 2.0 * (x1 - x0) - (z1 - z0))
			if absf(p.x + 1.0) < 5.0 and p.y > z1:
				continue                                # pred branou a mostem volno
			var y := _vyska(p.x, p.y)
			if y < voda + 0.3:
				continue
			var shluk := 1 if kk.begins_with("sipek") or kk.begins_with("bez") else rng.randi_range(2, 5)
			for _j in shluk:
				var q := p + Vector2(rng.randf_range(-0.7, 0.7), rng.randf_range(-0.7, 0.7))
				(r[kk] as Array).append(_xf(q.x, _vyska(q.x, q.y) - 0.04, q.y, rng.randf() * TAU, sc0 * rng.randf_range(0.7, 1.15)))
				n += 1
	# vrby hlavate na brehu prikopu: misto tesne nad hladinou na obvodu 4-12 m za hradbou
	var v := 0
	for i in 400:
		if v >= 14:
			break
		var a := rng.randf() * TAU
		var p := Vector2(-4.5, 0.4) + Vector2(cos(a) * 34.0, sin(a) * 28.0) * rng.randf_range(0.95, 1.25)
		var y := _vyska(p.x, p.y)
		if y < voda + 0.15 or y > voda + 1.2 or (absf(p.x + 3.0) < 6.0 and p.y > 0.0):
			continue
		var k := "vrba_hlavata_1_0" if rng.randf() < 0.5 else "vrba_hlavata_2_0"
		if not mer.has(k):
			continue
		(r[k] as Array).append(_xf(p.x, y - 0.1, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.85, 1.15)))
		v += 1
	print("tvrz zvenci: %d rostlin u hradeb, %d vrb u prikopu" % [n, v])


## Maska stanoviste (radce 07:50 bod 1), mrizka louky 2 m: R = krytí korunami jehlicnanu, G = listnacu, B = skaly (pata a
## okoli 12 m), A = pesina. Z ni zem.gdshader vybira povrch (listi / jehlici / pisek s jehlicim / mech / udusana
## pesina) a louka.gd nedava trsy na pesiny. Pocita se z rozmisteni stromu a skal po vsech upravach (_plants).
const JEHLICNATE := ["smrk", "borovice", "fir_", "pine_"]
## Pesiny (radce 07:50): tvrz - kostelik, Doubrava, skalni mesto - Pusta skala - hostinec, ves - Doubrava, od mostu
## tvrze, uhliri, lom, nadvori. Zdroj pravidla/svet/cesty.json „pesiny“ (krok A; poradi = index, kod se odkazuje na 4
## a 6); za behu se pridavaji cesticky k domum a k rybniku. PES_SIRKA = pulsirka (m): hlavni na sirku brany pro vuz
## (Misa 0.67), cesticky na nadvori uzsi. Vzdalenost v poli (stanoviste A, pes_dist) je delena PES_SIRKA[i] /
## PES_ZAKLAD, takze shader, louka i rozsevy (prahy v metrech pro pesinu) roztahnou cestu i jeji okraj se sirkou.
var PESINY: Array = []
var PES_SIRKA: Array = []
var PES_ZAKLAD := 0.55


func _pesiny_nacti() -> void:
	PESINY.clear()
	PES_SIRKA.clear()
	for c: Dictionary in Pravidla.cti("cesty", "pesiny"):
		var pts: Array = []
		for q: Array in c["osa"]:
			pts.append(Vector2(float(q[0]), float(q[1])))
		PESINY.append(pts)
		PES_SIRKA.append(float(c["pulsirka_m"]))
	PES_ZAKLAD = float(Pravidla.cti("cesty", "pesina_zaklad_m"))


var pes_f := PackedFloat32Array()      # nasobek sirky pro kazdy bod pes_osa (usek od bodu i k i + 1)
var stanoviste: Image                  # RGBA8 na mrizce trava_kraj (2 m)
var _st_ch: Array[PackedFloat32Array] = []
var _st_n := Vector2i.ZERO
var _kolize_body: StaticBody3D
var _uvnitr: Array = []
var _stat := {}
var stan_rect := Rect2()


## Osa pesin jako lomena cara (bod po 2 m): zvlnena vlnkou _pes_o a odsunuta od skal (test prochod: pesina na Pustou
## skalu vedla skrz skalni veze) - vsechny pesiny za sebou, mezi pesinami Vector2.INF.
var pes_osa := PackedVector2Array()
var pes_dist: Image                    # vzdalenost od osy pesiny / PES_DMAX (R8, mrizka 0,5 m) - louka, rozsev (shader ma pesinu v stanoviste.a)
const PES_K := 0.5
const PES_DMAX := 4.0


## Kruh pudorysu nesedi na nepravidelnou skalu (masiv se 3 vezemi: test prochod u (-161, 638)): body osy jeste
## odsunout od skutecnych vrcholu a tezist trojuhelniku skal (LOD1) v pasu 0,3-2,2 m nad zemi - na 1,3 m.
func _pes_od_sten() -> void:
	var r: Dictionary = data["rostliny"]
	var body := {}                                   # bunka 16 m -> indexy bodu osy
	for i in pes_osa.size():
		if pes_osa[i] != Vector2.INF:
			var cc := Vector2i(floori(pes_osa[i].x / 16.0), floori(pes_osa[i].y / 16.0))
			if not body.has(cc):
				body[cc] = []
			body[cc].append(i)
	var steny := {}                                  # bunka 2 m -> body sten (xz)
	for key: String in r:
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var me := _skala_sit(key)
		if me == null:
			continue
		var f := me.get_faces()
		var rp := maxf(me.get_aabb().size.x, me.get_aabb().size.z) * 0.5
		for t: Array in r[key]:
			var c := Vector2(float(t[3]), float(t[11]))
			var rr := rp * Vector3(t[0], t[4], t[8]).length() + 3.0
			var blizko := false
			for dx in range(-ceili(rr / 16.0), ceili(rr / 16.0) + 1):
				for dz in range(-ceili(rr / 16.0), ceili(rr / 16.0) + 1):
					blizko = blizko or body.has(Vector2i(floori(c.x / 16.0) + dx, floori(c.y / 16.0) + dz))
			if not blizko:
				continue
			var xf := Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])), Vector3(t[3], t[7], t[11]))
			for i in range(0, f.size(), 3):
				for g: Vector3 in [xf * f[i], xf * f[i + 1], xf * f[i + 2], xf * ((f[i] + f[i + 1] + f[i + 2]) / 3.0)]:
					var nad := g.y - _vyska(g.x, g.z)
					if nad < 0.3 or nad > 2.2:
						continue
					var k2 := Vector2i(floori(g.x / 2.0), floori(g.z / 2.0))
					if not steny.has(k2):
						steny[k2] = []
					steny[k2].append(Vector2(g.x, g.z))
	var posun := 0
	for i in pes_osa.size():
		var p := pes_osa[i]
		if p == Vector2.INF:
			continue
		for it in 4:
			var kk := Vector2i(floori(p.x / 2.0), floori(p.y / 2.0))
			var tlak := Vector2.ZERO
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for v: Vector2 in steny.get(kk + Vector2i(dx, dz), []):
						var d := p.distance_to(v)
						if d < 1.3:
							tlak += (p - v) / maxf(d, 0.01) * (1.3 - d)
			if tlak == Vector2.ZERO:
				break
			p += tlak.limit_length(1.3)
			posun += 1
		pes_osa[i] = p
	print("pesiny od sten skal: %d posunu" % posun)


func _pes_postav() -> void:
	# skaly: kruhy pudorysu (stred, polomer + 1,5 m)
	var skaly: Array = []
	var r: Dictionary = data["rostliny"]
	for key: String in r:
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var me := _skala_sit(key)
		if me == null:
			continue
		var bb := me.get_aabb()
		var rp := maxf(bb.size.x, bb.size.z) * 0.5
		for t: Array in r[key]:
			var sc := Vector3(t[0], t[4], t[8]).length()
			skaly.append([Vector2(t[3], t[11]), rp * sc * 0.9 + 2.0])   # test prochod: 0,8 + 1,5 m zachytilo previs hlavy
	# stavby v ceste (test prochod: vez zriceniny na Puste skale, kvadr chalupy ve vsi): staticke stavby a kvadry
	# z exportu od 0,6 m mimo tvrz (tam vede pesina branou)
	skaly.append_array(_stavby)
	for c: Array in data["kolize"]:
		var vel := maxf(absf(c[7]), absf(c[9]))
		if vel < 0.6 or (absf(float(c[0])) < 45.0 and absf(float(c[2])) < 50.0):
			continue
		# dlouhy tenky kvadr (plot 27 m): retez kruhu po delce, ne jeden kruh pres pul vsi
		var bs := Basis(Quaternion(c[4], c[5], c[6], c[3]).normalized())
		var sx := absf(float(c[7]))
		var sz := absf(float(c[9]))
		var osa_k := Vector2(bs.x.x, bs.x.z).normalized() if sx >= sz else Vector2(bs.z.x, bs.z.z).normalized()
		var delka := maxf(sx, sz)
		var tl := minf(sx, sz)
		var kusu := maxi(1, ceili(delka / maxf(tl, 1.0)))
		for i in kusu:
			var u := (i + 0.5) / kusu - 0.5
			skaly.append([Vector2(c[0], c[2]) + osa_k * u * delka, maxf(tl, delka / kusu) * 0.71 + 1.0])
	var mriz := {}
	for i in skaly.size():
		var c: Vector2 = skaly[i][0]
		var rr := float(skaly[i][1]) - 16.0                  # sousedni bunky pokryji 16 m, vetsi kruh i do dalsich
		var e := maxi(0, ceili(rr / 16.0))
		for ex in range(-e, e + 1):
			for ez in range(-e, e + 1):
				var cc := Vector2i(floori(c.x / 16.0) + ex, floori(c.y / 16.0) + ez)
				if not mriz.has(cc):
					mriz[cc] = []
				mriz[cc].append(i)
	# cesta z Blenderu (Teren_cesta, koleje): pesina vedle ni byla druha souběžna cesta (Misa 0.64: "dve vedle sebe,
	# ani jedna dobre") - kde je cesta do 5 m, pesina se prerusi (cesta je ta pesina)
	# radce 21:35 (Misa 0.75 "cesty mas zdvojene"): vyluka = cela plocha cesty + 6 m. Drive jen vrcholy site cesty
	# (vrcholy po desitkach metru - mezi nimi pesina prosla) a 6 m od vrcholu; ted plocha trojuhelniku po 1 m.
	var cesta := {}
	var cmi := _tvrz_root.find_child("Teren_cesta", true, false) as MeshInstance3D if _tvrz_root else null
	if cmi and cmi.mesh:
		var cxf := cmi.global_transform if cmi.is_inside_tree() else cmi.transform
		var fc := cmi.mesh.get_faces()
		for i in range(0, fc.size(), 3):
			var a := cxf * fc[i]
			var b := cxf * fc[i + 1]
			var c := cxf * fc[i + 2]
			var na := maxi(1, int(maxf(a.distance_to(b), a.distance_to(c)) / 1.0))
			for u in na + 1:
				for v in na + 1 - u:
					var w := a + (b - a) * (float(u) / na) + (c - a) * (float(v) / na)
					cesta[Vector2i(floori(w.x / 2.0), floori(w.z / 2.0))] = true
	var u_cesty := func(q: Vector2) -> bool:
		if cesta.is_empty():
			return false
		var c0 := Vector2i(floori(q.x / 2.0), floori(q.y / 2.0))
		for dx in range(-4, 5):
			for dz in range(-4, 5):
				if cesta.has(c0 + Vector2i(dx, dz)):
					return true
		return false
	var sg := pes_useky()
	var sg_f := PackedFloat32Array()
	var sg_ci := PackedInt32Array()
	for ci in PESINY.size():
		for q in (PESINY[ci] as Array).size() - 1:
			sg_f.append(float(PES_SIRKA[ci]) / PES_ZAKLAD if ci < PES_SIRKA.size() else 1.0)
			sg_ci.append(ci)
	pes_osa = PackedVector2Array()
	pes_f = PackedFloat32Array()
	var predchozi := -1
	for si in sg.size():
		# pesiny, ze kterych jsou cesty (od mostu 4, k lomu 6 - _cesty_tvar): v texture by byly druhou zvlnenou
		# cestou vedle (vlnka az 8 m, Misa 0.84 „cesta z lomu k vesnici - lemy“)
		if sg_ci[si] == 4 or sg_ci[si] == 6 or sg_ci[si] >= 12:
			continue
		var a := Vector2(sg[si].x, sg[si].y)
		var b := Vector2(sg[si].z, sg[si].w)
		if predchozi >= 0 and pes_osa.size() > 0 and pes_osa[pes_osa.size() - 1] != Vector2.INF \
				and pes_osa[pes_osa.size() - 1].distance_to(a) > 0.5:
			pes_osa.append(Vector2.INF)                       # nova pesina
			pes_f.append(1.0)
		var dl := a.distance_to(b)
		var dr := (b - a) / dl
		var n := int(dl / 2.0)
		for m in n + 1:
			var x := dl * m / n
			var p := a + dr * x + dr.orthogonal() * _pes_o(x, dl, si) * _brod_tlum(a + dr * x) * (0.15 if sg_ci[si] == 4 else 1.0)
			# odsunout od skal (3 pruchody - mezi dvema vezemi zustane uprostred)
			for it in 3:
				var cc := Vector2i(floori(p.x / 16.0), floori(p.y / 16.0))
				for dx in range(-1, 2):
					for dz in range(-1, 2):
						for i: int in mriz.get(cc + Vector2i(dx, dz), []):
							var c: Vector2 = skaly[i][0]
							var rr: float = skaly[i][1]
							var d := p.distance_to(c)
							if d < rr:
								p = c + (p - c) / maxf(d, 0.01) * rr
			if m == 0 and predchozi >= 0 and pes_osa.size() > 0 and pes_osa[pes_osa.size() - 1] != Vector2.INF:
				continue                                      # navazny bod useku je uz v ose
			# ke tvrzi vede jen hlavni cesta pres most (radce 21:35): tvrz, prikop a 5 m kolem - zadna stezka
			var ci_s: int = sg_ci[si]
			var u_tvrze := p.x > -46.0 and p.x < 37.0 and p.y > -35.0 and p.y < 36.0 and ci_s != 4 and ci_s < 8
			if u_tvrze or (ci_s != 4 and u_cesty.call(p)):
				if pes_osa.size() > 0 and pes_osa[pes_osa.size() - 1] != Vector2.INF:
					pes_osa.append(Vector2.INF)
					pes_f.append(1.0)
				continue
			pes_osa.append(p)
			pes_f.append(sg_f[si])
		predchozi = si
	# vyhladit (odsunute body by delaly zuby) - klouzavy prumer 5 bodu, konce pesin drzi
	var hl := pes_osa.duplicate()
	for i in range(2, pes_osa.size() - 2):
		var ok := true
		var sm := Vector2.ZERO
		for j in range(i - 2, i + 3):
			if pes_osa[j] == Vector2.INF:
				ok = false
			else:
				sm += pes_osa[j]
		if ok:
			hl[i] = sm / 5.0
	# po vyhlazeni jeste jednou od skal (prumer vrati bod mezi dvema odsunutymi zpet ke skale)
	for i in hl.size():
		var p := hl[i]
		if p == Vector2.INF:
			continue
		var cc := Vector2i(floori(p.x / 16.0), floori(p.y / 16.0))
		for dx in range(-1, 2):
			for dz in range(-1, 2):
				for k: int in mriz.get(cc + Vector2i(dx, dz), []):
					var c: Vector2 = skaly[k][0]
					var d := p.distance_to(c)
					if d < float(skaly[k][1]):
						p = c + (p - c) / maxf(d, 0.01) * float(skaly[k][1])
		hl[i] = p
	pes_osa = hl
	_pes_od_sten()
	# pole vzdalenosti (0,5 m) v pasu PES_DMAX kolem osy
	var w := int(stan_rect.size.x / PES_K)
	var h := int(stan_rect.size.y / PES_K)
	var px := PackedByteArray()
	px.resize(w * h)
	px.fill(255)
	var o := stan_rect.position
	for i in pes_osa.size() - 1:
		var a := pes_osa[i]
		var b := pes_osa[i + 1]
		if a == Vector2.INF or b == Vector2.INF:
			continue
		var f := pes_f[i] if i < pes_f.size() else 1.0
		var lo := (a.min(b) - Vector2(PES_DMAX, PES_DMAX) * f - o) / PES_K
		var hi := (a.max(b) + Vector2(PES_DMAX, PES_DMAX) * f - o) / PES_K
		var ab := b - a
		for jj in range(maxi(0, int(lo.y)), mini(h, int(hi.y) + 1)):
			for ii in range(maxi(0, int(lo.x)), mini(w, int(hi.x) + 1)):
				var q := o + Vector2(ii, jj) * PES_K
				var t := clampf((q - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
				var d := q.distance_to(a + ab * t) / f
				var v := clampi(int(d / PES_DMAX * 255.0), 0, 255)
				if v < px[jj * w + ii]:
					px[jj * w + ii] = v
	pes_dist = Image.create_from_data(w, h, false, Image.FORMAT_R8, px)
	print("pesiny: %d bodu osy, %d skal obejito" % [pes_osa.size(), skaly.size()])


## Vzdalenost od osy pesiny (m), bilinearne z pes_dist; za PES_DMAX vraci PES_DMAX. Cte se i z vlaken louky.
func pes_d(x: float, z: float) -> float:
	if pes_dist == null:
		return PES_DMAX
	var fx := (x - stan_rect.position.x) / PES_K
	var fz := (z - stan_rect.position.y) / PES_K
	var i := floori(fx)
	var j := floori(fz)
	if i < 0 or j < 0 or i >= pes_dist.get_width() - 1 or j >= pes_dist.get_height() - 1:
		return PES_DMAX
	fx -= i
	fz -= j
	var a := lerpf(pes_dist.get_pixel(i, j).r, pes_dist.get_pixel(i + 1, j).r, fx)
	var b := lerpf(pes_dist.get_pixel(i, j + 1).r, pes_dist.get_pixel(i + 1, j + 1).r, fx)
	return lerpf(a, b, fz) * PES_DMAX


## Useky pesin (a.x, a.z, b.x, b.z) za sebou pres vsechny pesiny (vstup pro _pes_postav).
func pes_useky() -> PackedVector4Array:
	var out := PackedVector4Array()
	for cesta: Array in PESINY:
		for q in range(cesta.size() - 1):
			out.append(Vector4(cesta[q].x, cesta[q].y, cesta[q + 1].x, cesta[q + 1].y))
	return out


## Vlnka osy pesiny (m kolmo k useku) ve vzdalenosti x od zacatku useku delky dl; konce useku drzi (navaznost).
static func _pes_o(x: float, dl: float, s: int) -> float:
	return 8.0 * sin(PI * x / dl) * (0.65 * sin(0.045 * x + 1.7 * s) + 0.35 * sin(0.11 * x + 4.1 * s))


## Prumer ctverce (2r+1)^2 bunek mrizky, po radcich a sloupcich.
static func _rozmaz_mriz(d: PackedFloat32Array, nx: int, nz: int, r: int) -> PackedFloat32Array:
	var a := PackedFloat32Array()
	a.resize(nx * nz)
	for j in nz:
		var s := 0.0
		for q in range(0, mini(r, nx - 1) + 1):
			s += d[j * nx + q]
		for i in nx:
			if i + r < nx and i > 0:
				s += d[j * nx + i + r]
			if i - r - 1 >= 0:
				s -= d[j * nx + i - r - 1]
			a[j * nx + i] = s / float(mini(i + r, nx - 1) - maxi(i - r, 0) + 1)
	var b := PackedFloat32Array()
	b.resize(nx * nz)
	for i in nx:
		var s := 0.0
		for q in range(0, mini(r, nz - 1) + 1):
			s += a[q * nx + i]
		for j in nz:
			if j + r < nz and j > 0:
				s += a[(j + r) * nx + i]
			if j - r - 1 >= 0:
				s -= a[(j - r - 1) * nx + i]
			b[j * nx + i] = s / float(mini(j + r, nz - 1) - maxi(j - r, 0) + 1)
	return b


func _stanoviste() -> void:
	var t0 := Time.get_ticks_msec()
	var g: Dictionary = data["trava_kraj"]
	var x0 := float(g["x0"])
	var z0 := float(g["z0"])
	var k := float(g["k"])
	var nx := int(g["nx"])
	var nz := int(g["nz"])
	stan_rect = Rect2(x0, z0, nx * k, nz * k)
	var ch: Array[PackedFloat32Array] = []
	for i in 4:
		var a := PackedFloat32Array()
		a.resize(nx * nz)
		ch.append(a)
	# stromy: koruna ~ 6 m kolem kmene
	for key: String in data["rostliny"]:
		if key.contains("_daleko"):
			continue
		var kind := key.substr(0, key.rfind("_"))
		var c := -1
		for j: String in JEHLICNATE:
			if kind.begins_with(j):
				c = 0
		if c < 0:
			for l: String in LISTNACE:
				if kind.begins_with(l):
					c = 1
		var skala := kind.begins_with("skala_")
		if c < 0 and not skala:
			continue
		# stromy: kryti korunou (radce 11:00 - stin dela koruna 8-12 m, ne kmen); polomer koruny z koule impostoru
		# (vodorovna pulka: sqrt(polomer^2 - (vyska/2)^2), nejmene 18 % vysky) x meritko instance
		var koruna := 3.0
		var imd := _imp_druh(kind) if c >= 0 else ""
		if imd != "":
			var im: Dictionary = _imp_meta[imd]
			koruna = maxf(sqrt(maxf(0.0, pow(float(im["polomer"]), 2.0) - pow(float(im["vyska"]) * 0.5, 2.0))), float(im["vyska"]) * 0.18)
		for t: Array in data["rostliny"][key]:
			var i0 := roundi((float(t[3]) - x0) / k)
			var j0 := roundi((float(t[11]) - z0) / k)
			var sc := Vector3(t[0], t[4], t[8]).length()
			var rm := (sc * 6.0 + 12.0) if skala else koruna * sc
			var rr := ceili(rm / k)
			for dj in range(-rr, rr + 1):
				for di in range(-rr, rr + 1):
					var i := i0 + di
					var j := j0 + dj
					if i < 0 or j < 0 or i >= nx or j >= nz:
						continue
					var dd := sqrt(float(di * di + dj * dj)) * k / maxf(rm, 0.5)
					var w := (1.0 - dd) if skala else (1.0 - smoothstep(0.7, 1.05, dd))
					if w <= 0.0:
						continue
					var a: PackedFloat32Array = ch[2 if skala else c]
					a[j * nx + i] = minf(1.0, a[j * nx + i] + w)
	# les je zapoj, ne jeden strom (radce 20:05 bod 5): kryti korunou plati jen tam, kde je v okoli 10 m prumerne
	# kryti >= 0,35 - samotny strom v louce nema pod sebou opad ani holou zem, louka pod nim zustava
	for c2 in 2:
		var hl := _rozmaz_mriz(_rozmaz_mriz(ch[c2], nx, nz, 2), nx, nz, 2)
		var hl2 := _rozmaz_mriz(_rozmaz_mriz(ch[1 - c2], nx, nz, 2), nx, nz, 2)
		for i in nx * nz:
			ch[c2][i] *= smoothstep(0.25, 0.45, hl[i] + hl2[i])
	# pesiny: osa obchazi skaly (_pes_postav). Kanal A = znamenkova vzdalenost od osy 0,5 + sd / 6 m (+-3 m): linearni
	# pole se bilinearne interpoluje presne i na mrizce 2 m. Samostatna textura pes_dist byla 14. vzorkovac zem.gdshader -
	# na Adrenu (16 jednotek, Godot si cast bere) se shader nesestavil a teren byl pruhledny (Misa 0.56).
	_pes_postav()
	var sd := PackedFloat32Array()
	sd.resize(nx * nz)
	sd.fill(3.0)
	var osa := pes_osa
	for si in osa.size() - 1:
		var a := osa[si]
		var b := osa[si + 1]
		if a == Vector2.INF or b == Vector2.INF:
			continue
		var zac := si == 0 or osa[si - 1] == Vector2.INF
		var kon := si + 2 >= osa.size() or osa[si + 2] == Vector2.INF
		var ab := b - a
		var l2 := maxf(ab.length_squared(), 1e-6)
		var f := pes_f[si] if si < pes_f.size() else 1.0
		var i0 := maxi(0, int((minf(a.x, b.x) - 3.0 * f - x0) / k))
		var i1 := mini(nx - 1, int((maxf(a.x, b.x) + 3.0 * f - x0) / k) + 1)
		var j0 := maxi(0, int((minf(a.y, b.y) - 3.0 * f - z0) / k))
		var j1 := mini(nz - 1, int((maxf(a.y, b.y) + 3.0 * f - z0) / k) + 1)
		for j in range(j0, j1 + 1):
			for i in range(i0, i1 + 1):
				var q := Vector2(x0 + i * k, z0 + j * k)
				var t := (q - a).dot(ab) / l2
				var d := q.distance_to(a + ab * clampf(t, 0.0, 1.0)) / f
				if d >= absf(sd[j * nx + i]):
					continue
				# za koncem pesiny kladne (jinak by zmena znamenka tahla pesinu dal po prodlouzene ose)
				# u vrcholu (t mimo 0..1) znamenko podle prumerneho smeru obou useku - podle primky jednoho useku se na
				# vnejsim ohybu otocilo a bilinearni prechod +2,4 -> -3 delal 5 m vedle cesty druhou "osu" (Misa 0.76)
				var sm := ab
				if t < 0.0 and not zac:
					sm = ab.normalized() + (a - osa[si - 1]).normalized()
				elif t > 1.0 and not kon:
					sm = ab.normalized() + (osa[si + 2] - b).normalized()
				var vr := a if t < 0.5 else b
				var zn := 1.0 if (zac and t < 0.0) or (kon and t > 1.0) else signf(sm.cross(q - (vr if t < 0.0 or t > 1.0 else a)))
				sd[j * nx + i] = d * (zn if zn != 0.0 else 1.0)
	# lom: udusana hlina jako pesina (shader zeme i louka berou A ~ 0,5 = osa pesiny), okraj 3 m do louky
	for j in nz:
		for i in nx:
			var vl := v_lomu(x0 + i * k, z0 + j * k)
			if vl < 3.0:
				sd[j * nx + i] = maxf(vl, 0.0) if absf(sd[j * nx + i]) > maxf(vl, 0.0) else sd[j * nx + i]
	# ch[3] (CPU, _st(3)) zustava maska "pesina do 3 m"; znamenkova hodnota jen do obrazku pro shader
	for i in nx * nz:
		ch[3][i] = clampf(1.0 - absf(sd[i]) / 3.0, 0.0, 1.0)
	var by := PackedByteArray()
	by.resize(nx * nz * 4)
	for i in nx * nz:
		for c in 3:
			by[i * 4 + c] = int(clampf(ch[c][i], 0.0, 1.0) * 255.0)
		by[i * 4 + 3] = roundi((0.5 + 0.5 * clampf(sd[i] / 3.0, -1.0, 1.0)) * 255.0)
	stanoviste = Image.create_from_data(nx, nz, false, Image.FORMAT_RGBA8, by)
	_st_ch = ch
	_st_n = Vector2i(nx, nz)
	print("stanoviste (kryt korun, pesiny, lom) %d ms" % (Time.get_ticks_msec() - t0))


## Kryti shora z offline casti (TVRZ_ROZSEV=1 -> modely/louka/kryti.bin, paprsky pod stoly, lavice, strechy,
## pavlac, skaly): bunka 32 m, mrizka 64 x 64 po 0,5 m.
const KRYTI_SOUBOR := "res://modely/louka/kryti.bin"
var kryti_tab := {}


func _nacti_kryti() -> void:
	if not kryti_tab.is_empty() or not FileAccess.file_exists(KRYTI_SOUBOR):
		return
	var by := FileAccess.get_file_as_bytes(KRYTI_SOUBOR)
	var o := 0
	while o + 516 <= by.size():
		var c := Vector2i(by.decode_s16(o), by.decode_s16(o + 2))
		var kr := PackedByteArray()
		kr.resize(4096)
		for i in 4096:
			kr[i] = (by[o + 4 + (i >> 3)] >> (i & 7)) & 1
		kryti_tab[c] = kr
		o += 516


## Cesta z tvrze (sit Teren_cesta, Misa 0.60: "cesta z hradu plna travy"): louka i rozsevy ji braly jako teren
## (jmeno Teren*). Trojuhelniky site do masky kryti (0,5 m) - na ceste nic neroste, okraj o 0,3 m dovnitr.
func _cesta_do_kryti() -> void:
	if _tvrz_root == null:
		return
	var mi := _tvrz_root.find_child("Teren_cesta", true, false) as MeshInstance3D
	if mi == null or mi.mesh == null:
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var n := 0
	for si in mi.mesh.get_surface_count():
		var a := mi.mesh.surface_get_arrays(si)
		var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		for t in idx.size() / 3:
			var p0 := xf * v[idx[t * 3]]
			var p1 := xf * v[idx[t * 3 + 1]]
			var p2 := xf * v[idx[t * 3 + 2]]
			var tri := PackedVector2Array([Vector2(p0.x, p0.z), Vector2(p1.x, p1.z), Vector2(p2.x, p2.z)])
			var x0 := floorf(minf(minf(p0.x, p1.x), p2.x) * 2.0) / 2.0
			var z0 := floorf(minf(minf(p0.z, p1.z), p2.z) * 2.0) / 2.0
			var x1 := maxf(maxf(p0.x, p1.x), p2.x)
			var z1 := maxf(maxf(p0.z, p1.z), p2.z)
			var x := x0 + 0.25
			while x < x1:
				var z := z0 + 0.25
				while z < z1:
					if Geometry2D.is_point_in_polygon(Vector2(x, z), tri):
						var c := Vector2i(floori(x / 32.0), floori(z / 32.0))
						if not kryti_tab.has(c):
							var kr := PackedByteArray()
							kr.resize(4096)
							kryti_tab[c] = kr
						var i := clampi(floori((x - c.x * 32.0) / 0.5), 0, 63)
						var j := clampi(floori((z - c.y * 32.0) / 0.5), 0, 63)
						kryti_tab[c][j * 64 + i] = 2      # 2 = cesta (louka: ani nizky drn)
						n += 1
					z += 0.5
				x += 0.5
	# cesty = tvar (_cesty_tvar): cely pas cesty 2 - louka tam sazi jen travu cesty (hrbet, kraje: svet.cesta_trava)
	for o: Dictionary in cesty_osy:
		var pp: PackedVector2Array = o["p"]
		var ws: PackedFloat32Array = o["w"]
		for i in pp.size() - 1:
			var dd := (pp[i + 1] - pp[i]).normalized()
			var nn := Vector2(-dd.y, dd.x)
			var lat := -ws[i] * 1.3 - 0.5
			while lat <= ws[i] * 1.3 + 0.5:
				for f: float in [0.0, 0.5]:
					var q: Vector2 = pp[i] + dd * (0.8 * f) + nn * lat
					var c := Vector2i(floori(q.x / 32.0), floori(q.y / 32.0))
					if not kryti_tab.has(c):
						var kr := PackedByteArray()
						kr.resize(4096)
						kryti_tab[c] = kr
					kryti_tab[c][clampi(floori((q.y - c.y * 32.0) / 0.5), 0, 63) * 64 + clampi(floori((q.x - c.x * 32.0) / 0.5), 0, 63)] = 2
				lat += 0.4
	# mosty pres potok (Misa 0.76 "u mostu vysoka trava v ceste"): sit cesty ma u mostu mezeru - pas mostovky
	# prodlouzeny o 6 m na kazdou stranu bez travy
	for mn in ["Most_potok"]:
		var mm := _tvrz_root.find_child(mn, true, false) as MeshInstance3D
		if mm == null:
			continue
		var mxf := mm.global_transform if mm.is_inside_tree() else mm.transform
		var ab := mm.get_aabb()
		var dl := 0 if ab.size.x * mxf.basis.x.length() >= ab.size.z * mxf.basis.z.length() else 2
		var inv := mxf.affine_inverse()
		var gb := (mxf * ab).grow(8.0)
		var x := floorf(gb.position.x)
		while x < gb.end.x:
			var z := floorf(gb.position.z)
			while z < gb.end.z:
				var l := inv * Vector3(x, (mxf * ab).get_center().y, z)
				var podel := l.x if dl == 0 else l.z
				var nap := l.z if dl == 0 else l.x
				var k0 := (ab.position.x if dl == 0 else ab.position.z)
				var k1 := (ab.end.x if dl == 0 else ab.end.z)
				var s0 := (ab.position.z if dl == 0 else ab.position.x)
				var s1 := (ab.end.z if dl == 0 else ab.end.x)
				var sc := (mxf.basis.x.length() if dl == 0 else mxf.basis.z.length())
				if podel > k0 - 6.0 / sc and podel < k1 + 6.0 / sc and nap > s0 + 0.15 * (s1 - s0) and nap < s1 - 0.15 * (s1 - s0):
					var c := Vector2i(floori(x / 32.0), floori(z / 32.0))
					if not kryti_tab.has(c):
						var kr := PackedByteArray()
						kr.resize(4096)
						kryti_tab[c] = kr
					var i := clampi(floori((x - c.x * 32.0) / 0.5), 0, 63)
					var j := clampi(floori((z - c.y * 32.0) / 0.5), 0, 63)
					kryti_tab[c][j * 64 + i] = 2
					n += 1
				z += 0.5
			x += 0.5
	# zapis do slovniku pres retezeny index (kryti_tab[c][i] = 2); (kryti_tab[c] as PackedByteArray)[i] = 2 psalo do kopie
	# (Packed* jsou hodnoty) - cesty nebyly v kryti nikdy, v lese na nich rostla trava (0.81)
	var kon := 0
	for o: Dictionary in cesty_osy:
		var pp0: PackedVector2Array = o["p"]
		var q0 := pp0[pp0.size() / 2]
		var c0 := Vector2i(floori(q0.x / 32.0), floori(q0.y / 32.0))
		if kryti_tab.has(c0) and (kryti_tab[c0] as PackedByteArray)[clampi(floori((q0.y - c0.y * 32.0) / 0.5), 0, 63) * 64 + clampi(floori((q0.x - c0.x * 32.0) / 0.5), 0, 63)] == 2:
			kon += 1
	print("cesta z tvrze v kryti: %d bodu, osy cest v kryti %d/%d" % [n, kon, cesty_osy.size()])


const VODNI := ["rakos", "orobinec", "vrba", "olse"]


var _sklony := PackedFloat32Array()     # sklon bunek mrizky trava_kraj (tan, nejvetsi z hran bunky) - skalni steny


## Sklon (tan) bunky vyskove mrizky v bode: terasy/skalni steny maji 1,2-18 (radce 06:40 bod 7). Mrizka 2 m, ctou ji
## smi_tu_byt (ve stene nic neroste) a _pata_sten.
func sklon_bunky(x: float, z: float) -> float:
	if _sklony.is_empty():
		_vyska(0.0, 0.0)
		if not _vys.has("trava_kraj"):
			return 0.0
		var g: Dictionary = _vys["trava_kraj"]
		var nx: int = g["nx"]
		var nz: int = g["nz"]
		var ys: PackedByteArray = g["y"]
		var kk := 100.0 * float(g["k"])
		_sklony.resize(nx * nz)
		for j in nz - 1:
			for i in nx - 1:
				var a := ys.decode_s16((j * nx + i) * 2)
				var b := ys.decode_s16((j * nx + i + 1) * 2)
				var c := ys.decode_s16(((j + 1) * nx + i) * 2)
				var d := ys.decode_s16(((j + 1) * nx + i + 1) * 2)
				_sklony[j * nx + i] = maxf(maxf(absi(b - a), absi(d - c)), maxf(absi(c - a), absi(d - b))) / kk
	var g2: Dictionary = _vys["trava_kraj"]
	var i2 := floori((x - float(g2["x0"])) / float(g2["k"]))
	var j2 := floori((z - float(g2["z0"])) / float(g2["k"]))
	if i2 < 0 or j2 < 0 or i2 >= int(g2["nx"]) - 1 or j2 >= int(g2["nz"]) - 1:
		return 0.0
	return _sklony[j2 * int(g2["nx"]) + i2]


## Skalni stena (radce 06:40 bod 7, FRONTA terasy): ve stene (sklon > 50 st.) nic neroste - trava, kere, stromy
## z exportu pryc; u paty sut (kameni, piskovcove bloky, cim vyssi stena, tim dal), na hrane obcas borovice.
## Po vsech rozsevech (lesy, plast, puda): na plose lomu jen kameni a balvany, a nic do 3 m pred stenou nahore.
func _lom_cisti() -> void:
	var r: Dictionary = data["rostliny"]
	var pryc := 0
	for key: String in r.keys():
		if key.begins_with("skala_") or key.begins_with("balvan_") or key.begins_with("kamen_"):
			continue
		var zust: Array = []
		for t: Array in r[key]:
			if v_lomu(float(t[3]), float(t[11])) < 3.0:
				pryc += 1
			else:
				zust.append(t)
		r[key] = zust
	print("lom: rostlin pryc %d, pata steny z 930/945/960: %.1f %.1f %.1f, dno %.1f" % [pryc, lom_stena_x(930.0), lom_stena_x(945.0),
			lom_stena_x(960.0), _vyska(165.0, 945.0)])


## Lom: stromy a kere z plochy pryc; u paty steny sut (pas 3-9 m, kameni a balvany) a velke odlomene bloky
## polozapustene; vyska paty z mrizky.
func _lom(pridej: Callable, pocty: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	var pryc := 0
	for key: String in r.keys():
		if key.begins_with("skala_") or key.begins_with("balvan_") or key.begins_with("kamen_"):
			continue
		var zust: Array = []
		for t: Array in r[key]:
			if v_lomu(float(t[3]), float(t[11])) < 2.0:
				pryc += 1
			else:
				zust.append(t)
		r[key] = zust
	var rng := RandomNumberGenerator.new()
	rng.seed = 1393
	# Misa 0.72 "lom je hnus": mechovy piskovec v sedem lomu nepatri - sut ze sede zuly a droby
	var kam := ["kamen_maly_1_0", "kamen_maly_2_0", "kamen_maly_3_0", "kamen_zula_1_0", "kamen_zula_2_0", "kamen_droba_1_0"]
	var bal := ["balvan_zula_1_0", "balvan_droba_1_0"]
	var n := 0
	# Misa 0.74: "na takovy prostor tam musi byt toho kameni tak 50x vice": po celem dne drobna sut a stepy
	# (kameni, odrezky), u paty hustsi osypy; velke kvadry jsou MultiMesh (_lom_sut)
	# Misa 24. 10. "neusporadane" (KCD: plocha pred pristresky volna, ujezdena): stepy jen u steny a u pracovist
	for q in 2200:
		var zq := rng.randf_range(LOM_Z.x + 0.5, LOM_Z.y - 0.5)
		var xq := lom_stena_x(zq) + 0.6 + pow(rng.randf(), 2.2) * 11.0
		if q % 4 == 0:                                   # u pracovist pod pristresky a u skladu kvadru
			var ps: Vector2 = [Vector2(8.0, 928.0), Vector2(8.5, 940.0), Vector2(14.5, 922.0), Vector2(14.5, 933.5), Vector2(14.5, 946.0)][q % 5]
			zq = ps.y + rng.randf_range(-3.5, 3.5)
			xq = lom_stena_x(zq) + ps.x + rng.randf_range(-2.2, 2.2)
		if lom_volno(xq, zq, 0.2):
			pridej.call(kam[rng.randi() % kam.size()], xq, zq, rng.randf_range(0.6, 2.2), -0.25, 0.6, vyska_lom(xq, zq))
		n += 1
	var z := LOM_Z.x + 1.0
	while z < LOM_Z.y - 1.0:
		var wx := lom_stena_x(z)
		for q in 14:
			var x := wx + 1.0 + pow(rng.randf(), 1.6) * 9.0          # husteji u paty
			var zz := z + rng.randf_range(-0.8, 0.8)
			if (lom_vyhrazeno(x, zz) and rng.randf() < 0.7) or not lom_volno(x, zz, 0.4):
				continue
			if rng.randf() < 0.25 and not lom_vyhrazeno(x, zz):
				pridej.call(bal[rng.randi() % bal.size()], x, zz, rng.randf_range(0.35, 0.9), -0.35, 0.4, vyska_lom(x, zz))
			else:
				pridej.call(kam[rng.randi() % kam.size()], x, zz, rng.randf_range(1.2, 3.5), -0.3, 0.5, vyska_lom(x, zz))
			n += 1
		z += 0.9
	# velke bloky odlomene ze steny (1-2 m), sem tam az 15 m od paty
	for q in 30:
		var zb := rng.randf_range(LOM_Z.x + 4.0, LOM_Z.y - 4.0)
		var xb := lom_stena_x(zb) + rng.randf_range(1.5, 6.0)
		if not lom_vyhrazeno(xb, zb) and lom_volno(xb, zb, 1.0):
			pridej.call(bal[rng.randi() % bal.size()], xb, zb, rng.randf_range(1.0, 1.8), -0.4, 0.3, vyska_lom(xb, zb))
	# okraj udusane plochy (lom_okraj): keře nepravidelne, ve shlucich, misty mezera
	var kere := []
	for k0: String in ["shrub_02_0", "sipek_0", "bez_cerny_1_0", "bez_cerny_2_0", "fir_sapling_0"]:
		if r.has(k0):
			kere.append(k0)
	var nk := 0
	if not kere.is_empty():
		var zk := LOM_Z.x
		while zk < LOM_Z.y + 8.0:
			zk += rng.randf_range(1.5, 6.0)
			if rng.randf() < 0.25:
				continue
			for q in rng.randi_range(1, 4):
				var zz := zk + rng.randf_range(-1.5, 1.5)
				var xx := lom_stena_x(minf(zz, LOM_Z.y)) + lom_okraj(zz) + rng.randf_range(0.5, 5.0)
				pridej.call(kere[rng.randi() % kere.size()], xx, zz, rng.randf_range(0.6, 1.3), -0.05, 0.1)
				nk += 1
	pocty["lom: rostlin pryc"] = pryc
	pocty["lom: sut"] = n
	pocty["lom: kere na okraji"] = nk


func _pata_sten(pridej: Callable, pocty: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	if sklon_bunky(0.0, 0.0) == 0.0 and _sklony.is_empty():
		return
	var pryc := 0
	for k: String in r.keys():
		if k.begins_with("skala_") or k.begins_with("balvan_"):
			continue
		# stromy uz od 42 st. (na svahu terasy by visely), ostatni nad 50 st.
		var strom := false
		for pf: String in LISTNACE + JEHLICNATE:
			if k.begins_with(pf):
				strom = true
		var mez := 0.9 if strom else 1.2
		var zust: Array = []
		for t: Array in r[k]:
			if sklon_bunky(float(t[3]), float(t[11])) < mez:
				zust.append(t)
		pryc += (r[k] as Array).size() - zust.size()
		r[k] = zust
	var g: Dictionary = _vys["trava_kraj"]
	var nx: int = g["nx"]
	var nz: int = g["nz"]
	var kr := float(g["k"])
	var gx0 := float(g["x0"])
	var gz0 := float(g["z0"])
	var ys: PackedByteArray = g["y"]
	# hrany: upravena terasa (_terasa_terenu, svah s pulbehem R2 na kazdou stranu) + zbyle kolme schody jinde
	var hrany: Array = []
	for e: Array in _terasa_hrany:
		hrany.append([e[0], e[1], e[2], e[3], true])
	for j in nz - 1:
		for i in nx - 1:
			for sm in 2:
				var a := ys.decode_s16((j * nx + i) * 2) / 100.0
				var b := ys.decode_s16(((j + sm) * nx + i + 1 - sm) * 2) / 100.0
				var dh := b - a
				if absf(dh) < 3.0 or absf(dh) / kr < 1.2:
					continue
				var dirv := Vector2(1 - sm, sm) * (-1.0 if dh > 0.0 else 1.0)
				hrany.append([Vector2(gx0 + i * kr, gz0 + j * kr) + Vector2(1 - sm, sm) * kr * 0.5, dirv, maxf(a, b), minf(a, b), false])
	var rng := RandomNumberGenerator.new()
	rng.seed = 6407
	var kameni := ["kamen_maly_1_0", "kamen_maly_2_0", "kamen_maly_3_0", "kamen_piskovec_1_0", "kamen_piskovec_2_0"]
	var ns := 0
	var nb := 0
	for e: Array in hrany:
		var mid: Vector2 = e[0]
		var dirv: Vector2 = e[1]
		var vys_st := float(e[2]) - float(e[3])
		var r2 := vys_st / (2.0 * tan(deg_to_rad(53.0))) if e[4] else kr * 0.5
		var pata := mid + dirv * r2
		var hrana := mid - dirv * r2
		if absf(pata.x + 4.0) < 90.0 and absf(pata.y) < 90.0 or Vector2(pata.x - 470.0, pata.y - 830.0).length() < 130.0:
			continue
		if e[4]:
			continue                                    # radce 18:00 bod 1: sut terasy vypnuta (levitovala nad travou)
		var dosah := 1.5 + vys_st * 0.22               # sut dobehne dal pod vyssi stenou
		for q in 2 + int(vys_st / 8.0):
			# sut od dolni tretiny svahu po dosah pod patou
			var p := pata + dirv * (dosah * pow(rng.randf(), 1.6) - r2 * 0.5 * rng.randf()) + dirv.orthogonal() * rng.randf_range(-1.0, 1.0) * kr
			if sklon_bunky(p.x, p.y) > 1.1 or pes_d(p.x, p.y) < 1.5 or _louka_m(p.x, p.y) < 0.03 and _les(p.x, p.y) < 0.1 and _st(2, p.x, p.y) < 0.1:
				continue
			var u := rng.randf()
			if u < 0.12:
				pridej.call("balvan_piskovec_2_0" if rng.randf() < 0.6 else "balvan_piskovec_1_0", p.x, p.y,
						rng.randf_range(0.5, 1.1), 0.3 * rng.randf_range(0.5, 1.1), 0.35)
				nb += 1
			elif u < 0.2 and e[4]:
				pridej.call("kapradi_%d_0" % (rng.randi() % 3 + 1), p.x, p.y, rng.randf_range(0.7, 1.2), 0.05)   # kapradi v suti
			else:
				pridej.call(kameni[rng.randi() % kameni.size()], p.x, p.y, clampf(exp(rng.randfn(0.4, 0.5)), 0.6, 3.5), -0.3, 0.4)
				ns += 1
		# borovice na hrane (Cesky raj): obcas, 2-4 m za hranou, kde je nahore rovina
		if vys_st > 6.0 and rng.randf() < 0.07 and r.has("borovice_0"):
			var p2 := hrana - dirv * rng.randf_range(2.0, 4.0) + dirv.orthogonal() * rng.randf_range(-1.0, 1.0)
			if sklon_bunky(p2.x, p2.y) < 0.6 and pes_d(p2.x, p2.y) > 2.0:
				var ref: Array = (r["borovice_0"] as Array)[0]
				var s0 := Vector3(ref[0], ref[4], ref[8]).length()
				(r["borovice_0"] as Array).append(_xf(p2.x, _vyska_min(p2.x, p2.y) - 0.15, p2.y, rng.randf() * TAU, s0 * rng.randf_range(0.7, 1.1),
						Vector3(rng.randf_range(-0.08, 0.08), 0, rng.randf_range(-0.08, 0.08))))
				pocty["borovice na hrane"] = int(pocty.get("borovice na hrane", 0)) + 1
	# _bloky_steny(pridej, pocty)      # radce 18:00 bod 1: bloky terasy skryt, az po vykonu znovu (osa podel hrany)
	pocty["ze steny pryc"] = pryc
	pocty["sut u paty"] = ns
	pocty["balvany u paty"] = nb


## Skalni stena terasy (radce 11:00 bod 2): do svahu zapustene velke balvany piskovce (fotosken), nepravidelne -
## ne rady vezi na boku (Misa 0.63: "hruza" - klady/jitrnice trcici ze svahu). Na kazde ~treti hrane terasy jeden
## balvan 3-6 m, 50 % pod terenem, nahodne natoceny a nakloneny; kolize trimesh (pridej).
func _bloky_steny(pridej: Callable, pocty: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	if _terasa_hrany.is_empty() or not r.has("balvan_piskovec_1_0"):
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 1100
	var tg := tan(deg_to_rad(53.0))
	var mista: Array = []
	var n := 0
	for e: Array in _terasa_hrany:
		var D := float(e[2]) - float(e[3])
		if D < 5.0 or rng.randf() > 0.33:
			continue
		var mid: Vector2 = e[0]
		var dirv: Vector2 = e[1]
		var r2 := D / (2.0 * tg)
		# misto na svahu: od horni ctvrtiny po patu, bokem podel hrany
		var c := mid + dirv * rng.randf_range(-r2 * 0.6, r2 * 0.9) + dirv.orthogonal() * rng.randf_range(-1.0, 1.0)
		var volno := true
		for m: Vector2 in mista:
			if c.distance_to(m) < 9.0:
				volno = false
				break
		if not volno:
			continue
		mista.append(c)
		var k := "balvan_piskovec_%d_0" % (rng.randi() % 3 + 1)
		if not r.has(k):
			k = "balvan_piskovec_1_0"
		pridej.call(k, c.x, c.y, rng.randf_range(2.2, 3.8), -0.5, 0.45)
		n += 1
	pocty["skalni_stena_blok"] = n


## Jedno misto pro vsechny rozsevy (radce 11:20): smi tu rust bylina, kvet, ker, kamen, mrtve drevo?
## Ne pod strechou / stolem / lavici / pavlaci (kryti shora), ne v budove, ne na ceste, ve vode ani na dvore
## (maska louky 0 mimo les a skaly - dvur pred hostincem je 0), ne na pesine. Louka.gd cte tentyz zaklad.
## LOM (radce 16:20, Misa: "u steny (146,949) bude lom"): stena terasy x ~114 (z 906-955), dal po proudu ustupuje
## (+0,5 m na m); plocha lomu 42 m od paty steny, z 906-975. Znamenkova vzdalenost od okraje plochy (< 0 uvnitr).
const LOM_Z := Vector2(906.0, 975.0)
const NASTOJATO := ["krumpac", "kladivo_kamenicke"]     # modely nastojato (hlavou nahoru) - ve vybaveni lezi
const LESENI_Z := Vector2(911.0, 950.5)           # lamana cast steny s lesenim (svetla stena, osyp tam neni)
var _leseni_rect: Array = []
const LOM_SIRKA := 42.0


var _lom_pata := {}


## Pata steny lomu (snimek 0.71: odhad 114 + ... byl na svahu - pristresek visel na stene): od x 100 na vychod
## prvni bod nejvys 1,2 m nad dnem lomu (dno = vyska 40 m od steny), po metrech z
## Kde v lomu nemaji byt velke kusy: leseni (lavky, stojky) a podlaha jerabu.
func lom_vyhrazeno(x: float, z: float) -> bool:
	var u := x - lom_stena_x(z)
	if z > LESENI_Z.x - 1.0 and z < LESENI_Z.y + 1.0 and u < 4.6:
		return true
	return z > 951.5 and z < 960.5 and u < 13.0


func lom_stena_x(z: float) -> float:
	var zi := clampi(roundi(z), int(LOM_Z.x) - 4, int(LOM_Z.y) + 4)
	if not _lom_pata.has(zi):
		# od zapadu: nejdriv sraz (pokles > 0,8 m na 1 m), pata = kde sraz skonci (pokles < 0,25 m na 1 m)
		var zf := float(zi)
		var x := 100.0
		var sraz := false
		while x < 160.0:
			var dh := _vyska(x, zf) - _vyska(x + 1.0, zf)
			if dh > 0.8:
				sraz = true
			elif sraz and dh < 0.25:
				break
			x += 0.5
		_lom_pata[zi] = x + 0.5
	return float(_lom_pata[zi])


## Trziste pred vsi (Misa 24. 10., 0.74: "v hlavni ceste od mostu, rozhazene nesmyslne - udelej to vedle cesty"):
## obdelnik udusane hliny vedle cesty most - ves (blender ODBOCKA, usek (340,712)-(398,766)), v soustave trhu
## u = podel cesty, v = kolmo od osy cesty. Pas v 3,5-7 m volny pro kupujici, v 8,5 m rada tri stanku celem k ceste
## (zbozi srovnane na pultech), za nimi bedny a sudy; na konci u vsi kupecky stan, pred nim stul se stolickou.
## Misa 0.75: "trziste smaz a nekam si ho uloz, budeme na nem delat do budoucna" - vypnute, kod a plan zustavaji
## (docs/patche/trziste.md); TRZISTE = true ho vrati (stanky, rovina, hlina v shaderu, bez travy).
const TRZISTE := false
const TRZ_O := Vector2(381.7, 750.9)                  # bod na ose cesty (plan docs/screens/trziste_plan.png)
const TRZ_U := Vector2(0.7317, 0.6816)                # smer cesty k vsi
const TRZ_V := Vector2(0.6816, -0.7317)               # kolmo od cesty (strana s mirnym svahem)
const TRZ_R := Rect2(-2.0, 6.5, 24.0, 12.0)           # udusana hlina: stanky a ulicka (u od, v od, delka, hloubka)
const TRZ := Vector2(381.7 + 0.7317 * 10.0 + 0.6816 * 12.5, 750.9 + 0.6816 * 10.0 - 0.7317 * 12.5)    # stred ulicky


func trz_bod(u: float, v: float) -> Vector2:
	return TRZ_O + TRZ_U * u + TRZ_V * v


## Znamenkova vzdalenost od okraje trhu (< 0 uvnitr).
func v_trzisti(x: float, z: float) -> float:
	if not TRZISTE:
		return INF
	var q := Vector2(x, z) - TRZ_O
	var u := q.dot(TRZ_U)
	var v := q.dot(TRZ_V)
	return maxf(maxf(TRZ_R.position.x - u, u - TRZ_R.end.x), maxf(TRZ_R.position.y - v, v - TRZ_R.end.y))


func _trziste(vb: Array, rng: RandomNumberGenerator) -> void:
	if not TRZISTE:
		return
	# podle planu docs/screens/trziste_plan.png: ulicka 3 m podel cesty (v 11-14), dve rady po 4 stancich (pult na kozach
	# s platenou striskou) celem do ulicky, za stanky zasoby, na konci kupecky stan; kul s cedulí u vstupu, koryto stranou
	var smer := atan2(-TRZ_U.y, TRZ_U.x)              # yaw: mistni osa X modelu podel cesty
	var y_trh := _trz_y if _trz_y != INF else _vyska(TRZ.x, TRZ.y)
	var polozit := func(id: String, u: float, v: float, yaw: float, rovne := true) -> void:
		var p := trz_bod(u, v)
		vb.append({"id": id, "p": [p.x, (y_trh if rovne else _vyska(p.x, p.y)) - 0.02, p.y], "yaw": yaw + rng.randf_range(-0.03, 0.03)})
	var zbozi := [["zeli_hlavka", "salat", "zeli_hlavka", "salat", "zeli_hlavka"], ["bochnik", "veka", "bochnik", "veka", "bochnik"],
			["hrnec_hlineny", "hrnec_velky", "hrnec_hlineny", "hrnec_hlineny", "hrnec_velky"], ["okurka", "okurka", "zeli_hlavka", "okurka", "salat"],
			["vedro_drevene", "hrnec_hlineny", "vedro_drevene", "hrnec_hlineny", "vedro_drevene"], ["bochnik", "bochnik", "veka", "veka", "bochnik"],
			["zeli_hlavka", "zeli_hlavka", "zeli_hlavka", "salat", "salat"], ["hrnec_velky", "okurka", "hrnec_velky", "okurka", "hrnec_velky"]]
	var zasoby := [["bedna_trzni", "sud"], ["bedna_trzni_2", "pytel_obili"], ["sud", "bedna_trzni_3"], ["bedna_velka_zelenina", "lisa_zelenina"],
			["necky", "bedna_trzni"], ["pytel_obili", "sud"], ["bedna_zelenina", "bedna_trzni_2"], ["sud", "bedna_trzni_3"]]
	var i := 0
	for rada: Array in [[9.0, 6.8], [16.0, 18.6]]:
		for u: float in [2.0, 6.0, 10.0, 14.0]:
			var v: float = rada[0]
			polozit.call("pristresek_maly", u, v, smer)
			# zbozi v rade na stole (deska 0,83 m)
			for q in 5:
				var p := trz_bod(u - 0.8 + q * 0.4, v + rng.randf_range(-0.08, 0.08))
				vb.append({"id": zbozi[i][q], "p": [p.x, y_trh - 0.02 + 0.84, p.y], "yaw": rng.randf() * TAU})
			polozit.call(zasoby[i][0], u - 0.65, rada[1], smer)
			polozit.call(zasoby[i][1], u + 0.55, rada[1], smer)
			i += 1
	polozit.call("stan_jehlan", 19.5, 12.5, smer + PI * 0.5)
	polozit.call("kul_cedule", -1.0, 5.0, smer + PI * 0.5, false)
	polozit.call("koryto_kone", -4.5, 8.8, smer, false)
	print("trziste: 8 stanku, stred ulicky (%.0f, %.0f), rovina y %.2f" % [TRZ.x, TRZ.y, y_trh])


## Lom (Misa 0.74): stovky hrube otesanych kvadru - osypy u paty steny (chaoticky, naklonene), stohy pripravenych
## bloku k odvozu (2-3 vrstvy, srovnane), rozhazene kusy po dne. MultiMesh po variantach (3 volani kresleni),
## dosah 140 m; kolize jen stohy (kvadr). Modely z blender/vlastni.py kvadr_hruby.
func _lom_sut(parent: Node3D) -> void:
	var meshe: Array = []
	var vys: Array = []
	for k in 3:
		var ps: PackedScene = load("res://modely/predmety/kvadr_hruby_%d.glb" % (k + 1))
		if ps == null:
			return
		var inst := ps.instantiate()
		var mi := inst.find_children("*", "MeshInstance3D", true, false)
		if mi.is_empty():
			inst.free()
			return
		meshe.append((mi[0] as MeshInstance3D).mesh)
		vys.append((mi[0] as MeshInstance3D).mesh.get_aabb().size.y)
		inst.free()
	var xfs: Array = [[], [], []]
	var rng := RandomNumberGenerator.new()
	rng.seed = 9490
	var tvar := BoxShape3D.new()
	var kol := StaticBody3D.new()
	kol.name = "Lom_stohy_kolize"
	# 1) osypy u paty steny: kusy naklonene, na sobe (ne pod lesenim a pod jerabem)
	var z := LOM_Z.x + 1.0
	while z < LOM_Z.y - 1.0:
		var wx := lom_stena_x(z)
		for q in 5:
			var k := rng.randi() % 3
			var sc := rng.randf_range(0.45, 1.0)
			var x := wx + 0.8 + pow(rng.randf(), 1.8) * 6.0
			var zz := z + rng.randf_range(-0.7, 0.7)
			if lom_vyhrazeno(x, zz) or not lom_volno(x, zz, 0.5 * sc):
				continue
			# nejnizsi bod pod celym kusem (stred nestacil - naklonene kusy visely nad prohlubni, Misa 0.77)
			var y := pata_lom(x, zz, 0.0, 1.2 * sc, 1.2 * sc) - 0.12 * sc
			var bs := Basis.from_euler(Vector3(rng.randf_range(-0.45, 0.45), rng.randf() * TAU, rng.randf_range(-0.45, 0.45))).scaled(
					Vector3(rng.randf_range(0.8, 1.2), rng.randf_range(0.8, 1.15), rng.randf_range(0.8, 1.2)) * sc)
			(xfs[k] as Array).append(Transform3D(bs, Vector3(x, y, zz)))
		z += 1.3
	# 2) sklad hotovych kvadru (Misa: "ne pravidelne pyramidy, ne nakopirovane"): rady podel lomu, kazdy kvadr jiny
	# (3 modely, ruzne protazene, otocene o 180 st.), mezery nestejne, misty chybi; druha vrstva jen nekde, polozena
	# pres spaaru dvou spodnich; treti vrstva vyjimecne. Pod vyloznikem jerabu hromada k nakladani.
	var delky := [0.95, 1.35, 0.65]
	var sirky := [0.62, 0.7, 0.5]
	for sk: Vector3 in [Vector3(14.0, 922.0, 7.0), Vector3(14.6, 933.5, 8.0), Vector3(14.0, 946.0, 6.0), Vector3(10.6, 957.6, 3.2)]:
		for rada in 2:
			var spod: Array = []                         # [z0, z1, vrch y, u]
			var zc := sk.y - sk.z / 2 + rng.randf_range(0.0, 0.4)
			var u0 := sk.x + rada * 0.82 + rng.randf_range(-0.06, 0.06)
			while zc < sk.y + sk.z / 2:
				var k: int = [0, 0, 0, 1, 1, 2][rng.randi() % 6]
				var sx := rng.randf_range(0.85, 1.18)
				var dl: float = float(delky[k]) * sx
				if rng.randf() < 0.08:
					zc += rng.randf_range(0.5, 1.0)          # chybi kus (odvezen)
					continue
				var zm := zc + dl / 2
				var n2 := nrm_lom(zm)
				var w := Vector2(lom_stena_x(zm), zm) + n2 * (u0 + rng.randf_range(-0.07, 0.07))
				if not lom_volno(w.x, w.y, dl * 0.5):
					zc += dl + 0.2
					continue
				var sy := rng.randf_range(0.85, 1.12)
				var bs := Basis(Vector3.UP, atan2(-n2.y, n2.x) + PI * 0.5 + rng.randf_range(-0.08, 0.08) + (PI if rng.randf() < 0.5 else 0.0)).scaled(
						Vector3(sx, sy, rng.randf_range(0.9, 1.1)))
				var y0 := pata_lom(w.x, w.y, atan2(-n2.y, n2.x), float(sirky[k]), dl) - 0.02
				(xfs[k] as Array).append(Transform3D(bs, Vector3(w.x, y0, w.y)))
				var hy: float = float(vys[k]) * sy
				spod.append([zc, zc + dl, y0 + hy, w, float(sirky[k])])
				_lom_kolize(kol, Vector3(w.x, y0 + hy / 2, w.y), Vector3(float(sirky[k]), hy, dl), atan2(-n2.y, n2.x))
				zc += dl + rng.randf_range(0.04, 0.25)
			# druha vrstva pres spary
			for i in spod.size() - 1:
				if rng.randf() > 0.55:
					continue
				var a: Array = spod[i]
				var b: Array = spod[i + 1]
				# Misa 0.78 "horni kameny levituji": sousede v seznamu nemuseli lezet vedle sebe (chybejici / obsazeny kus
				# mezi nimi) - kvadr nahore visel nad mezerou; jen pres sparu do 0,3 m
				if float(b[0]) - float(a[1]) > 0.3:
					continue
				var k: int = [0, 0, 2][rng.randi() % 3]
				var zm := (float(a[1]) + float(b[0])) / 2 + rng.randf_range(-0.12, 0.12)
				var n2 := nrm_lom(zm)
				var w := Vector2(lom_stena_x(zm), zm) + n2 * (u0 + rng.randf_range(-0.08, 0.08))
				var sy := rng.randf_range(0.85, 1.1)
				var yt := maxf(float(a[2]), float(b[2])) - 0.03
				var bs := Basis(Vector3.UP, atan2(-n2.y, n2.x) + PI * 0.5 + rng.randf_range(-0.12, 0.12) + (PI if rng.randf() < 0.5 else 0.0)).scaled(
						Vector3(rng.randf_range(0.85, 1.1), sy, rng.randf_range(0.9, 1.05)))
				(xfs[k] as Array).append(Transform3D(bs, Vector3(w.x, yt, w.y)))
				_lom_kolize(kol, Vector3(w.x, yt + float(vys[k]) * sy / 2, w.y), Vector3(float(sirky[k]), float(vys[k]) * sy, float(delky[k])), atan2(-n2.y, n2.x))
	# 3) odrezky a zmetky jen u skladu a pod pristresky kameniku
	for q in 60:
		var ps: Vector2 = [Vector2(8.0, 928.0), Vector2(8.5, 940.0), Vector2(13.0, 922.0), Vector2(13.0, 933.5), Vector2(13.0, 946.0)][q % 5]
		var zq := ps.y + rng.randf_range(-3.0, 3.0)
		var xq := lom_stena_x(zq) + ps.x + rng.randf_range(-1.6, 1.6)
		if not lom_volno(xq, zq, 0.3):
			continue
		var k := rng.randi() % 3
		var sc := rng.randf_range(0.25, 0.55)
		var bs := Basis.from_euler(Vector3(rng.randf_range(-0.15, 0.15), rng.randf() * TAU, rng.randf_range(-0.15, 0.15))).scaled(
				Vector3(rng.randf_range(0.7, 1.3), rng.randf_range(0.6, 1.1), rng.randf_range(0.7, 1.3)) * sc)
		(xfs[k] as Array).append(Transform3D(bs, Vector3(xq, pata_lom(xq, zq, 0.0, 1.3 * sc, 1.3 * sc) - 0.08 * sc, zq)))
	var root := Node3D.new()
	root.name = "Lom_sut"
	parent.add_child(root)
	root.add_child(kol)
	var n := 0
	for k in 3:
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = meshe[k]
		mm.instance_count = (xfs[k] as Array).size()
		for i in mm.instance_count:
			mm.set_instance_transform(i, xfs[k][i])
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.visibility_range_end = 140.0
		# cerne kvadry (PC i tablet): normalova mapa z glb v MultiMeshi -> material bez ni, textura zuly
		var om := (meshe[k] as Mesh).surface_get_material(0) as BaseMaterial3D
		if om:
			var m2 := om.duplicate() as BaseMaterial3D
			m2.normal_enabled = false
			m2.albedo_color = Color(1.55, 1.52, 1.45)      # zula jako na fotkach KCD svetle seda, ne cerna
			mmi.material_override = m2
		root.add_child(mmi)
		n += mm.instance_count
	print("lom: kvadru %d" % n)


## Svisla lomova stena za lesenim (Misa: "leseni tesne u steny"): sit 0,5 m od paty do vysky lavice, skala jen
## dozadu zvlnena (nikdy pred patu), nahore vodorovny lem 5,5 m dozadu pres vybrany pas; material terenu
## (zem.gdshader dela z kolme plochy v lomu sedy lamany kamen), kolize z teze site.
func _lom_stena_svisla(root: Node3D, parent: Node3D) -> void:
	var tm: Material = null                     # aktivni material terenu lomu (surface_get_material byl jiny - stena cerna)
	for t in root.find_children("Teren_okoli", "MeshInstance3D", true, false):
		var mi := t as MeshInstance3D
		for si in mi.mesh.get_surface_count():
			var sm0 := mi.get_active_material(si)
			if sm0 is ShaderMaterial and String((sm0 as ShaderMaterial).shader.resource_path).ends_with("zem.gdshader"):
				tm = sm0
	if tm == null or _lom_srov.is_empty():
		return
	var nz := FastNoiseLite.new()
	nz.seed = 911
	nz.frequency = 0.35
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Misa: "cela stena ma korespondovat s kopcem a ostatnimi stenami": na koncich pasu stena nizsi a zapada
	# do puvodni steny lomu, horni hrana odlomena (sum), lic mirne ukloneny dozadu (jako zbytek lomu, ~80 st.),
	# nahore lem na teren lavice / svahu za ni
	# radce 19:05: stena SCHODOVITA - lavice 1-3 m vysoke ustupujici 0,3-1 m, svisle spary po 1-3 m (bloky
	# posunute), dole u paty previs 0,2 m dovnitr, nahore pres 0,5 m pod teren lavice, dole 0,8 m pod dno
	var z0 := LESENI_Z.x - 3.5
	var z1 := LESENI_Z.y + 3.5
	var nzk := int((z1 - z0) / 0.25)
	var NY := 40
	var radky: Array = []
	var hs := func(k: float) -> float:
		return fposmod(sin(k * 12.9898 + 4.1) * 43758.5453, 1.0)
	for j in nzk + 1:
		var z := z0 + j * 0.25
		var f := lom_stena_x(z)
		var q: Vector4 = _lom_srov.get(roundi(z), Vector4(f, 6.0, _vyska(f, z) + 9.0, _vyska(f, z)))
		var e := smoothstep(z0, z0 + 4.5, z) * (1.0 - smoothstep(z1 - 4.5, z1, z))
		var yt := lerpf(q.w + 0.6, q.z + 0.2 + nz.get_noise_2d(z * 0.6, 7.0) * 1.4, e)
		# blok mezi svislymi sparami (1-3 m) a vzdalenost ke spare
		var jz := z / 2.0 + nz.get_noise_2d(z * 0.05, 3.0) * 0.6
		var blok := floorf(jz)
		var ds := minf(jz - blok, blok + 1.0 - jz) * 2.0
		var spara := (1.0 - smoothstep(0.0, 0.12, ds)) * 0.18
		var r: Array = []
		for i in NY:
			var t := i / float(NY - 1)
			var y := lerpf(q.w - 0.8, yt, t)
			var h := y - q.w
			# lavice: hranice po 1-3 m (kazdy blok jinak), kazda ustoupi 0,3-1 m
			var ust := 0.0
			var hh := 0.0
			for k in 6:
				hh += 1.0 + 2.0 * float(hs.call(blok * 7.0 + k))
				if h > hh:
					ust += 0.3 + 0.7 * float(hs.call(blok * 13.0 + k + 0.5))
			var dx: float = 0.12 + ust * 0.55 + (hs.call(blok) - 0.5) * 0.4 + spara + absf(nz.get_noise_2d(z * 2.0, y * 2.0)) * 0.1
			if h < 0.5:
				dx += 0.2 * (1.0 - smoothstep(0.2, 0.5, h))     # previs u paty
			r.append(Vector3(f - dx * e - (1.0 - e) * (0.3 + maxf(h, 0.0) * 0.6), y, z))
		var xt: float = (r[NY - 1] as Vector3).x
		r.append(Vector3(xt - 1.2, yt + 0.25, z))
		r.append(Vector3(xt - 6.0, maxf(_vyska(xt - 6.0, z), yt - 1.0) - 0.5, z))
		radky.append(r)
	for j in nzk:
		var a: Array = radky[j]
		var b: Array = radky[j + 1]
		for i in a.size() - 1:
			for v: Vector3 in [a[i], b[i], a[i + 1], a[i + 1], b[i], b[i + 1]]:
				st.set_color(Color(0.0, 0.0, 0.0, 1.0))
				st.set_uv(Vector2(v.z, v.y) * 0.3)
				st.add_vertex(v)
	st.generate_normals()
	st.generate_tangents()
	var me := st.commit()
	var mi2 := MeshInstance3D.new()
	mi2.name = "Teren_lom_stena"
	mi2.mesh = me
	mi2.material_override = tm
	mi2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi2)
	var sb := StaticBody3D.new()
	sb.name = "Teren_lom_stena_kolize"
	var cs := CollisionShape3D.new()
	cs.shape = me.create_trimesh_shape()
	sb.add_child(cs)
	parent.add_child(sb)


## Misa 0.75 "v lomu predmety levituji" (kvadr (144,937) 10-30 cm): mrizka vysek 2 m je jina nez kreslena sit terenu
## (body po 5 m) - v lomu se predmety pokladaji na skutecne trojuhelniky site (bunky 2 m, jen vodorovnejsi plochy).
var _lom_tri := {}
var _lom_zabrano: Array = []          # [x, z, polomer] polozenych veci lomu - rozsev a kvadry se jim vyhnou


func _lom_sit_priprav(root: Node3D) -> void:
	_lom_tri.clear()
	var x0 := 95.0
	var x1 := 190.0
	var z0 := LOM_Z.x - 20.0
	var z1 := LOM_Z.y + 20.0
	var n := 0
	for t in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(t.name)
		if nm == "Teren_obzor" or nm == "Teren_cesta_kamen" or nm.ends_with("_sukne"):
			continue
		var mi := t as MeshInstance3D
		var am := mi.mesh as ArrayMesh
		if am == null or not mi.get_aabb().intersects(AABB(mi.global_transform.affine_inverse() * Vector3(x0, -500, z0), Vector3(x1 - x0, 1000, z1 - z0)).abs()):
			continue
		var xf := mi.global_transform
		for si in am.get_surface_count():
			var arr := am.surface_get_arrays(si)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			var nt := idx.size() / 3 if idx.size() > 0 else v.size() / 3
			for ti in nt:
				var a := xf * v[idx[ti * 3] if idx.size() > 0 else ti * 3]
				var b := xf * v[idx[ti * 3 + 1] if idx.size() > 0 else ti * 3 + 1]
				var c := xf * v[idx[ti * 3 + 2] if idx.size() > 0 else ti * 3 + 2]
				var mnx := minf(a.x, minf(b.x, c.x))
				var mxx := maxf(a.x, maxf(b.x, c.x))
				var mnz := minf(a.z, minf(b.z, c.z))
				var mxz := maxf(a.z, maxf(b.z, c.z))
				if mxx < x0 or mnx > x1 or mxz < z0 or mnz > z1:
					continue
				if absf((b - a).cross(c - a).normalized().y) < 0.35:
					continue                             # stena, ne podlaha
				for cx in range(floori(mnx / 2.0), floori(mxx / 2.0) + 1):
					for cz in range(floori(mnz / 2.0), floori(mxz / 2.0) + 1):
						var key := Vector2i(cx, cz)
						if not _lom_tri.has(key):
							_lom_tri[key] = []
						(_lom_tri[key] as Array).append([a, b, c])
				n += 1
	print("lom: sit terenu %d trojuhelniku" % n)


## Vyska kreslene site terenu v lomu (nejvyssi plocha pod bodem); mimo lom mrizka.
func vyska_lom(x: float, z: float) -> float:
	var l: Array = _lom_tri.get(Vector2i(floori(x / 2.0), floori(z / 2.0)), [])
	var best := -INF
	var p := Vector2(x, z)
	for t: Array in l:
		var a: Vector3 = t[0]
		var b: Vector3 = t[1]
		var c: Vector3 = t[2]
		var v0 := Vector2(b.x - a.x, b.z - a.z)
		var v1 := Vector2(c.x - a.x, c.z - a.z)
		var v2 := p - Vector2(a.x, a.z)
		var den := v0.x * v1.y - v1.x * v0.y
		if absf(den) < 1e-9:
			continue
		var u := (v2.x * v1.y - v1.x * v2.y) / den
		var w := (v0.x * v2.y - v2.x * v0.y) / den
		if u < -0.001 or w < -0.001 or u + w > 1.001:
			continue
		best = maxf(best, a.y + u * (b.y - a.y) + w * (c.y - a.y))
	return best if best > -INF else _vyska(x, z)


## Vyska paty predmetu v lomu: pudorys w (x modelu) x d (z modelu) otoceny o yaw - nejnizsi bod husteho vzorku
## (5 x 5 pres cely pudorys; Misa 0.77 "porad kolo od vozu levituje a nektere kameny": 4 rohy a prumer pod koly
## nechaly mezi sebou prohlubne - kvadr i kolo nad nimi viselo). Kola: jen body pod koly (boky vozu), nejnizsi - 2 cm;
## ostatni kola se o rozdil zaboři do sterku (lepsi nez viset).
func pata_lom(x: float, z: float, yaw: float, w: float, d: float, kola := false) -> float:
	var b := Basis(Vector3.UP, yaw)
	var mn := INF
	for i in 5:
		for j in 5:
			var u := (i / 4.0 - 0.5) * w * 0.96
			if kola and i != 0 and i != 4:
				continue
			var v := (j / 4.0 - 0.5) * d * (0.8 if kola else 0.96)
			var q := b * Vector3(u, 0, v)
			mn = minf(mn, vyska_lom(x + q.x, z + q.z))
	return mn - (0.02 if kola else 0.01)


## Predmety s vice opernymi body (Misa 25. 10.): vozy na 4 kolech, trakar (kolo vpredu, 2 nohy), napajedlo na spalcich.
const NA_BODECH := ["zebrinak", "trakar", "koryto_kone", "lavice_selska", "lavice", "lavice_nizka", "stul_selsky", "stul_prkenny", "stul_kozy_dub"]


## Oporne body v ramci predmetu (x sirka, z delka modelu; poradi predni levy, predni pravy, zadni levy, zadni pravy).
func opory(id: String, w: float, d: float) -> Array:
	if id == "koryto_kone":
		# jen dva spalky pod korytem (x +-0,8, hloubka 0,55); kuly bradla jsou zarazene (zem0)
		return [Vector3(-0.8, 0, -0.25), Vector3(0.8, 0, -0.25), Vector3(-0.8, 0, 0.25), Vector3(0.8, 0, 0.25)]
	if id == "trakar":
		return [Vector3(0.0, 0, -0.45 * d), Vector3(0.0, 0, -0.45 * d), Vector3(-0.35 * w, 0, 0.4 * d), Vector3(0.35 * w, 0, 0.4 * d)]
	return [Vector3(-0.42 * w, 0, -0.42 * d), Vector3(0.42 * w, 0, -0.42 * d), Vector3(-0.42 * w, 0, 0.42 * d), Vector3(0.42 * w, 0, 0.42 * d)]


## place_on_points (Misa 25. 10.) na kreslene siti terenu lomu: vyska pod kazdym opernym bodem (svet se stavi pred
## fyzikou - paprsek nahrazuje trojuhelnik site, vyska_lom), stred = prumer zasahu, osa nahoru = normala roviny bodu.
## Vraci [stred, nahoru].
func polozit_na_body(x: float, z: float, yaw: float, offsets: Array) -> Array:
	var yb := Basis(Vector3.UP, yaw)
	var h: Array[Vector3] = []
	for off: Vector3 in offsets:
		var q := yb * Vector3(off.x, 0, off.z)
		h.append(Vector3(x + q.x, vyska_lom(x + q.x, z + q.z), z + q.z))
	var fl := h[0]
	var fr := h[1]
	var bl := h[2]
	var br := h[3]
	var stred := (fl + fr + bl + br) / 4.0
	var back := ((bl + br) / 2.0 - (fl + fr) / 2.0).normalized()
	var right := ((fr + br) / 2.0 - (fl + bl) / 2.0)
	if right.length() < 0.01:
		right = yb.x                     # trakar: predni body splyvaji (jedno kolo)
	right = right.normalized()
	var up := back.cross(right).normalized()
	if up.y < 0.0:
		up = -up
	return [stred, up]


func lom_volno(x: float, z: float, r := 0.0) -> bool:
	for q: Vector3 in _lom_zabrano:
		if Vector2(x - q.x, z - q.y).length() < q.z + r:
			return false
	# kvadry ani stohy ne na ceste (test zasazeni 27. 10.: stohy na ceste k lomu u (171, 939)) - odstup jako balvan
	# (pasma.cesta.<typ>.ker_od_m od kraje hliny)
	var ck := cesta_kraj_osa(x, z)
	if ck.y >= 0.0 and ck.x < r + float(odstup_cesty("balvan_kvadr", int(ck.y))):
		return false
	return true


func nrm_lom(z: float) -> Vector2:
	var t := Vector2(lom_stena_x(z + 3.0) - lom_stena_x(z - 3.0), 6.0).normalized()
	return Vector2(t.y, -t.x)


func _lom_kolize(kol: StaticBody3D, p: Vector3, sz: Vector3, yaw: float) -> void:
	var cs := CollisionShape3D.new()
	var bx := BoxShape3D.new()
	bx.size = sz * Vector3(0.95, 1.0, 0.95)
	cs.shape = bx
	cs.transform = Transform3D(Basis(Vector3.UP, yaw), p)
	kol.add_child(cs)


func _trziste_cisti() -> void:
	var r: Dictionary = data["rostliny"]
	var pryc := 0
	for key: String in r.keys():
		var zust: Array = []
		for t: Array in r[key]:
			if v_trzisti(float(t[3]), float(t[11])) < 1.5:
				pryc += 1
			else:
				zust.append(t)
		r[key] = zust
	print("trziste: rostlin pryc %d" % pryc)


## Misa 24. 10. "plac moc velky, travu louky a kere 2 m od vozu nepravidelne, at tam nemame letiste": udusana plocha
## konci zvlnene 23-31 m od paty steny (vozy nejdal 21,6 m); stejna funkce v zem.gdshader (lom_okraj).
func lom_okraj(z: float) -> float:
	return 27.5 + 1.8 * sin(z * 0.19 + 1.3) + 1.2 * sin(z * 0.47 + 0.4) + 0.8 * sin(z * 1.07)


func v_lomu(x: float, z: float) -> float:
	var wx := lom_stena_x(z)
	var dx := maxf(wx + 0.3 - x, x - (wx + lom_okraj(z)))
	var dz := maxf(LOM_Z.x - z, z - LOM_Z.y)
	return maxf(dx, dz)


func smi_tu_byt(x: float, z: float, druh := "") -> bool:
	if v_trzisti(x, z) < 1.5:
		return false
	if ryb_voda(x, z):
		return false
	if not druh_smi_hra(druh, x, z):
		return false                                  # pravidla druhu (druhy.json) a voda + brehovy pas
	if v_lomu(x, z) < 1.0 and not druh.begins_with("kamen") and not druh.begins_with("balvan"):
		return false
	var c := Vector2i(floori(x / 32.0), floori(z / 32.0))
	if kryti_tab.has(c):
		var i := clampi(floori((x - c.x * 32.0) / 0.5), 0, 63)
		var j := clampi(floori((z - c.y * 32.0) / 0.5), 0, 63)
		if (kryti_tab[c] as PackedByteArray)[j * 64 + i] != 0:
			return false
	for st: Array in _uvnitr:
		var q: Vector3 = (st[0] as Transform3D) * Vector3(x, 0.0, z)
		var b: AABB = st[1]
		if q.x > b.position.x and q.x < b.end.x and q.z > b.position.z and q.z < b.end.z:
			return false
	if sklon_bunky(x, z) > 1.2:
		return false                                  # skalni stena (radce 06:40 bod 7)
	if _st_ch.is_empty():
		return true
	# tvrz a ves maji vlastni teren mimo masku krajiny
	if absf(x + 4.0) < 75.0 and absf(z) < 70.0 or Vector2(x - 470.0, z - 830.0).length() < 130.0:
		return true
	for v: String in VODNI:
		if druh.begins_with(v):
			return true
	if koryto and (druh.begins_with("kamen") or druh.begins_with("balvan")) and not koryto.blizko(x, z).is_empty() \
			and float(koryto.blizko(x, z)[0]) < float(koryto.blizko(x, z)[2]) + 2.0:
		return true                                   # kameny v korytu a na brehu potoka
	if _st(3, x, z) > 0.5:
		return false                                  # pesina
	if _louka_m(x, z) < 0.03 and _les(x, z) < 0.1 and _st(2, x, z) < 0.1:
		return false                                  # cesta, voda, dvur, staveniste
	return true


## Kosena louka nebo pole (radce 17:00 a 20:05): maska louky z Blenderu, mimo les, skaly, pesiny, vodu, tvrz a ves, pod
## hrebeny (do 25 m). Tady nesmi byt vychozy, smrky ani kameni - jedna funkce pro rozsev i test (tools/test_svet.gd).
## Kosi se jen do 150 m od tvrze a vsi (radce 07:45: sec, pastva); dal louka_neudrzovana - zarostla.
const SEC_TVRZ := 225.0                # 75 m tvrz s nadvorim + 150 m
const SEC_VES := 280.0                 # 130 m ves + 150 m


## 0 = v dosahu kosy, 1 = 60 m a dal za nim (neudrzovana louka). Jen pocty: cte se i z vlaken louky.
static func divokost(x: float, z: float) -> float:
	var d := minf(Vector2(x + 4.0, z).length() - SEC_TVRZ, Vector2(x - 470.0, z - 830.0).length() - SEC_VES)
	# hranice seci zvlnena (+-4 m, radce 09:05: ne hrana), dve frekvence
	d += 3.0 * sin(x * 0.11 + z * 0.07) * cos(z * 0.13 - x * 0.05) + 1.5 * sin(x * 0.37 - z * 0.31)
	# val mezi hradbou a prikopem (Misa 0.63: "val u tvrze prazdny" - rovny posekany pruh): kosa tam nechodi,
	# neudrzovana trava (trsy, vysoka, byliny)
	if x > -31.5 and x < 22.5 and z > -20.5 and z < 21.5 and not (x > -27.6 and x < 18.5 and z > -16.6 and z < 17.4):
		return maxf(clampf(d / 60.0, 0.0, 1.0), 0.75)
	return clampf(d / 60.0, 0.0, 1.0)


func kosena_louka(x: float, z: float) -> bool:
	if absf(x + 4.0) < 75.0 and absf(z) < 70.0 or Vector2(x - 470.0, z - 830.0).length() < 130.0:
		return false
	if divokost(x, z) > 0.0:
		return false
	if _louka_m(x, z) <= 0.5 or _les(x, z) >= 0.1 or _st(2, x, z) >= 0.15 or _st(3, x, z) >= 0.3 or _vyska(x, z) >= 25.0:
		return false
	if koryto and not koryto.blizko(x, z).is_empty() and koryto.strop(x, z, false) < _vyska(x, z) + 1.0:
		return false                                   # zarez potoka
	if nadrz and not nadrz.misto(x, z).is_empty() and float(nadrz.misto(x, z)[0]) > -6.0:
		return false
	return true


## Pravidla druhu ve hre z pravidla/svet/druhy.json (Astra 22:00: mazani se nahrazuje stanovistem): „pouzit“: false
## = druh se nesazi vubec (duvod v zaznamu), „vyjma“ = masky hry, kde druh neroste (kosena_louka). Jeden zdroj
## s Blenderem (kraj.druh_smi cte totez). Klic instance -> druh: nejdelsi id, ktere je predponou klice.
var _druhy_hra := {}
var _druhy_ids: Array = []
var _stromy_6a := {}                     # klic -> pocet instanci pred novymi lesy (lesni patro jen k nim)


func _druhy_nacti() -> void:
	_druhy_hra = {}
	for d: Dictionary in Pravidla.cti("druhy", "druhy"):
		_druhy_hra[String(d["id"])] = d
	_druhy_ids = _druhy_hra.keys()
	_druhy_ids.sort_custom(func(a: String, b: String) -> bool: return a.length() > b.length())


func druh_klice(key: String) -> String:
	for i: String in _druhy_ids:
		if key == i or key.begins_with(i + "_"):
			return i
	return ""


## Vzdalenost od vody (m, < 0 ve vode): male toky (voda.json toky, od kraje hladiny), rybnik tvrze (polomer) a dil
## rybnika Lhota (pod hladinou = voda). Jedna definice pro rozsev (druh_smi_hra) i test zasazeni (ve_vode_*).
var _voda_mriz := {}                    # bunka 16 m -> [[a, b, pul sirky]]
var _voda_ryb: Array = []


func od_vody(x: float, z: float, y := INF) -> float:
	if _voda_ryb.is_empty():
		for t: Dictionary in Pravidla.cti("voda", "toky"):
			var o: Array = t["osa_xzy"]
			var w := float(t["sirka_m"]) * 0.5
			for i in o.size() - 1:
				var a := Vector2(float(o[i][0]), float(o[i][1]))
				var b := Vector2(float(o[i + 1][0]), float(o[i + 1][1]))
				for cx in range(floori((minf(a.x, b.x) - 16.0) / 16.0), floori((maxf(a.x, b.x) + 16.0) / 16.0) + 1):
					for cz in range(floori((minf(a.y, b.y) - 16.0) / 16.0), floori((maxf(a.y, b.y) + 16.0) / 16.0) + 1):
						var c := Vector2i(cx, cz)
						if not _voda_mriz.has(c):
							_voda_mriz[c] = []
						(_voda_mriz[c] as Array).append([a, b, w])
		var rt: Dictionary = Pravidla.cti("voda", "rybnik_tvrz")
		var rl: Dictionary = Pravidla.cti("voda", "rybnik_lhota")
		# dil Lhota: voda = teren pod hladinou jen do voda_polomer_m + breh_sirka_m (driv 60 m: udoli odtoku pod hrazi
		# je niz nez hladina a bylo „ve vode“ - test zasazeni 28. 10. (504, 889))
		_voda_ryb = [Vector2(float(rt["stred"][0]), float(rt["stred"][1])), float(rt["polomer_m"]),
				Vector2(float(rl["stred"][0]), float(rl["stred"][1])), float(rl["hladina_y"]),
				float(rl["voda_polomer_m"]) + float(Pravidla.cti("voda", "toky_tvar")["breh_sirka_m"])]
	var q := Vector2(x, z)
	var d := q.distance_to(_voda_ryb[0]) - float(_voda_ryb[1])
	if y != INF and q.distance_to(_voda_ryb[2]) < float(_voda_ryb[4]) and y < float(_voda_ryb[3]):
		d = minf(d, -0.1)
	for e: Array in _voda_mriz.get(Vector2i(floori(x / 16.0), floori(z / 16.0)), []):
		d = minf(d, q.distance_to(Geometry2D.get_closest_point_to_segment(q, e[0], e[1])) - float(e[2]))
	return d


const VODNI_DRUHY := ["rakos", "orobinec", "leknin", "okreh"]


## Smi druh klice key rust na (x, z)? Nezname klice (predmety, karty) ano - test smyslu hlida katalog zvlast. Nic
## suchozemskeho ve vode malych toku a rybniku ani na brehovem pasu (pasma voda breh_m; kameny ano).
func druh_smi_hra(key: String, x: float, z: float, y := INF) -> bool:
	if not (key.begins_with("kamen") or key.begins_with("balvan") or key.begins_with("skala_")):
		var vodni := false
		for v: String in VODNI_DRUHY:
			vodni = vodni or key.contains(v)
		if not vodni and od_vody(x, z, y) < float(pasma()["voda"]["breh_m"]):
			return false
	if not uzivani_smi(key, x, z):
		return false                                  # uzivani: zahon, pruchod, vnitrek stavby, cesta
	var d: Dictionary = _druhy_hra.get(druh_klice(key), {})
	if d.is_empty():
		return true
	if d.get("pouzit", true) == false:
		return false
	for m: String in d.get("vyjma", []):
		if m == "kosena_louka" and kosena_louka(x, z):
			return false
		if m == "volna_louka" and volna_louka(x, z):
			return false
	return true


## Uzivani mista (Misa 28. 10. „trava a stromy ve vstupech do vrat, v zahonech, v hostinci, strom uprostred
## cesty“): nic nesazet do zahonu (obdelavany), do pruchodu (vrata, branky, dvere: pasma budova pruchod_m od stredu
## pruchodu), dovnitr pudorysu staveb (_uvnitr) a strom/ker/trs na hlinu cesty (odstup_cesty). Jedno misto pro rozsev,
## vstup exportu (_vstup_druhu) i louku (v_pruchodu).
func uzivani_smi(key: String, x: float, z: float) -> bool:
	if v_nove_zahrade(x, z) == 2 or v_zahrade(x, z):
		return false
	if v_pruchodu(x, z, key):
		return false
	for st: Array in _uvnitr:
		if st.size() > 2:
			continue                                  # dil mlyna: vlastni pravidla (teren dilu)
		var q: Vector3 = (st[0] as Transform3D) * Vector3(x, 0.0, z)
		var b: AABB = st[1]
		if q.x > b.position.x and q.x < b.end.x and q.z > b.position.z and q.z < b.end.z:
			return false
	if key != "" and not (key.begins_with("kamen") or key.begins_with("balvan")):
		# odstup 0 (byliny) = ne na hline cesty; vetsi odstup = dal od kraje (0.98: bylina na ceste)
		var ck := cesta_kraj_osa(x, z)
		if ck.y >= 0.0 and ck.x < odstup_cesty(key, int(ck.y)):
			return false
	return true


var _pruchody := {}                   # bunka 8 m -> [Vector2 stred pruchodu]


## Je bod v pruchodu (vrata, branka, dvere ze zaznamu pohybu)? Mrizka se postavi pri prvnim volani v hlavnim vlakne
## (_plants), louka ve vlaknech jen cte.
func v_pruchodu(x: float, z: float, key := "") -> bool:
	if _pruchody.is_empty():
		_pruchody[Vector2i(1 << 20, 0)] = []
		for e: Dictionary in data.get("pohyb", []):
			var nm := String(e.get("name", ""))
			if not (String(e.get("kind", "")) in ["dvere", "vrata"] or nm.contains("vrata") or nm.contains("branka") or nm.contains("dvere")):
				continue
			var p3: Array = e.get("use", e["pos"])
			var c := Vector2i(floori(float(p3[0]) / 8.0), floori(float(p3[2]) / 8.0))
			if not _pruchody.has(c):
				_pruchody[c] = []
			(_pruchody[c] as Array).append(Vector2(float(p3[0]), float(p3[2])))
	# vstup = pruchod + vyslapany dvur pred nim (pasma budova dvur_m); strom a ker jeste o kmen_od_zdi_m dal
	# (Misa 0.98: stromy a kere ve vstupech - kruh 1,6 m od stredu vrat sirokych 3 m vstup nechranil)
	var pb: Dictionary = pasma()["budova"]
	var r := float(pb["pruchod_m"]) + float(pb["dvur_m"])
	if key != "":
		var sk := String((_druhy_hra.get(druh_klice(key), {}) as Dictionary).get("skupina", ""))
		if sk == "strom" or sk == "ker":
			r += float(pb["kmen_od_zdi_m"])
	var q := Vector2(x, z)
	var c0 := Vector2i(floori(x / 8.0), floori(z / 8.0))
	for dx in range(-1, 2):
		for dz in range(-1, 2):
			for p: Vector2 in _pruchody.get(Vector2i(c0.x + dx, c0.y + dz), []):
				if p.distance_to(q) < r:
					return true
	return false


## Volna louka (maska kroku 7): ne plast lesa (do 12 m), les, skaly, pesiny ani okraj louky (m < 0,6) - kere tu
## nerostou (hlaseni 0.55 "kere uprostred louky").
func volna_louka(x: float, z: float) -> bool:
	var okraj := maxf(maxf(_les(x + 12, z), _les(x - 12, z)), maxf(_les(x, z + 12), _les(x, z - 12)))
	return not (okraj > 0.15 or _les(x, z) > 0.1 or _st(2, x, z) > 0.1 or _louka_m(x, z) < 0.6 or _st(3, x, z) > 0.2)


## Krok 0: druhy s „pouzit“: false se z katalogu vyradi pred rozsevy (vcetne vzdalenych verzi) - rozsev jejich klic
## nenajde a nesazi je. Exporty od 28. 10. je uz neobsahuji (kraj.druh_smi).
func _druhy_mimo_katalog() -> void:
	var pryc: Array = []
	for k: String in data["rostliny"].keys():
		var d: Dictionary = _druhy_hra.get(druh_klice(k), {})
		if d.get("pouzit", true) == false:
			pryc.append("%s %d" % [k, (data["rostliny"][k] as Array).size()])
			data["rostliny"].erase(k)
	print("druhy mimo katalog (druhy.json pouzit false): %s" % ", ".join(pryc))


## Vstup kroku 8: kazdy kus z Blenderu a z kroku 6 na stanovisti podle masek kroku 7 (druhy.json vyjma).
func _vstup_druhu() -> void:
	var pocty := {}
	for k: String in data["rostliny"].keys():
		var zust: Array = []
		for t: Array in data["rostliny"][k]:
			if druh_smi_hra(k, float(t[3]), float(t[11]), float(t[7])):
				zust.append(t)
		var n := (data["rostliny"][k] as Array).size() - zust.size()
		if n > 0:
			pocty[druh_klice(k)] = int(pocty.get(druh_klice(k), 0)) + n
		data["rostliny"][k] = zust
	print("vstup druhu (stanoviste z masek kroku 7, druhy.json vyjma, voda): mimo stanoviste %s" % str(pocty))


## Hodnota kanalu stanoviste (0 jehlicnate, 1 listnate, 2 skaly, 3 pesina) v bode - bilinearne (nejblizsi bunka 2 m
## delala z prahu rozsevu ctverce: okraj kapradi, keru a travy po 2 m, "rastr").
func _st(c: int, x: float, z: float) -> float:
	var fx := clampf((x - stan_rect.position.x) / 2.0, 0.0, _st_n.x - 1.001)
	var fz := clampf((z - stan_rect.position.y) / 2.0, 0.0, _st_n.y - 1.001)
	var i := floori(fx)
	var j := floori(fz)
	fx -= i
	fz -= j
	var a: PackedFloat32Array = _st_ch[c]
	var k := j * _st_n.x + i
	return lerpf(lerpf(a[k], a[k + 1], fx), lerpf(a[k + _st_n.x], a[k + _st_n.x + 1], fx), fz)


func _les(x: float, z: float) -> float:
	return minf(1.0, _st(0, x, z) + _st(1, x, z))


var _maska_m := PackedByteArray()


## Mira louky z mrizky Blenderu (0 = cesta, voda, stavba, pole s nizsi vahou).
func _louka_m(x: float, z: float) -> float:
	var g: Dictionary = data["trava_kraj"]
	if _maska_m.is_empty():
		_maska_m = Marshalls.base64_to_raw(String(g["m"]))
	var i := clampi(roundi((x - float(g["x0"])) / float(g["k"])), 0, int(g["nx"]) - 1)
	var j := clampi(roundi((z - float(g["z0"])) / float(g["k"])), 0, int(g["nx"]) * 0 + int(g["nz"]) - 1)
	return _maska_m[j * int(g["nx"]) + i] / 255.0


## Krajina 07:50 (body 2-4): kameny vsude (pod skalami, v boru, na pesinach, na svazich, vychozy na hrbetech),
## kere v pasech (plast okraje lesa, pod skalami - ne uprostred kosene louky), les ve trech patrech (padle kmeny,
## parezy, kury, koreny, mech, nalet). Vse deterministicky z masky stanoviste; meritka podle prvni instance druhu.
func _krajina() -> void:
	var r: Dictionary = data["rostliny"]
	var mer := {}
	for k: String in r.keys():
		if not (r[k] as Array).is_empty():
			var t: Array = r[k][0]
			mer[k] = Vector3(t[0], t[4], t[8]).length()
	var tvary := {}
	var vysky := {}
	var pridej := func(k: String, x: float, z: float, s: float, ponor: float, naklon := 0.0, y := INF) -> void:
		if not druh_smi_hra(k, x, z):
			return                                          # druhy.json: pouzit / vyjma (stanoviste z masek)
		if not r.has(k):
			r[k] = []
		var rr := RandomNumberGenerator.new()
		rr.seed = hash(Vector2(x, z))
		if ponor < 0.0:
			# zaporny ponor = podil vysky modelu (kameni zapustene o 30 %, radce 20:05 bod 7)
			if not vysky.has(k):
				var me0 := _skala_sit(k)
				vysky[k] = me0.get_aabb().size.y if me0 else 0.2
			ponor = -ponor * float(vysky[k]) * float(mer.get(k, 1.0)) * s
		if k.begins_with("balvan_") and _u_mostu_jen(x, z):
			return                                          # test prochod 0.75: balvan v najezdu mostu (226,597)
		var xf := _xf(x, (_vyska(x, z) if y == INF else y) - ponor, z, rr.randf() * TAU, float(mer.get(k, 1.0)) * s,
				Vector3(rr.randf_range(-naklon, naklon), 0, rr.randf_range(-naklon, naklon)))
		(r[k] as Array).append(xf)
		# balvany a padle kmeny: kolize (kolize sveta uz jsou postavene)
		if (k.begins_with("balvan_") or k.begins_with("dead_tree")) and _kolize_body:
			if not tvary.has(k):
				var me := _skala_sit(k)
				tvary[k] = [me.create_convex_shape(true, true) if k.begins_with("balvan_") else me.create_trimesh_shape(), me.get_aabb()] if me else null
			if tvary[k]:
				kolize(tvary[k][0], tvary[k][1], Transform3D(Basis(Vector3(xf[0], xf[4], xf[8]), Vector3(xf[1], xf[5], xf[9]), Vector3(xf[2], xf[6], xf[10])), Vector3(xf[3], xf[7], xf[11])))
	var rng := RandomNumberGenerator.new()
	rng.seed = 750
	var pocty := {}
	# vrba hlavata: kmen se rozsiruje jako vaza a pata visi nad zemi (hlaseni 0.54, 16:50) - zapustit 0,3 m
	for k: String in r.keys():
		if k.begins_with("vrba_hlavata"):
			for t: Array in r[k]:
				t[7] = float(t[7]) - 0.3
	# 1) kere uprostred louky: pravidlo druhu (druhy.json vyjma volna_louka) uplatnil vstup kroku 8 (_vstup_druhu)
	# 1b) kameni z exportu v kosene louce (hlaseni 0.55 "brouci"): pravidlo druhu (druhy.json vyjma kosena_louka) uz
	# uplatnil vstup kroku 8 (_vstup_druhu)
	var kere := ["shrub_02_0", "shrub_02_1", "sipek_0", "sipek_1", "bez_cerny_1_0", "bez_cerny_2_0", "bez_cerny_3_0"]
	var kameni := ["kamen_maly_1_0", "kamen_maly_2_0", "kamen_maly_3_0", "kamen_maly_4_0", "kamen_maly_5_0"]
	var x0 := stan_rect.position.x
	var z0 := stan_rect.position.y
	var krok := 4.0
	var z := z0 + 2.0
	while z < stan_rect.end.y - 2.0:
		var x := x0 + 2.0
		while x < stan_rect.end.x - 2.0:
			var px := x + rng.randf_range(-1.8, 1.8)
			var pz := z + rng.randf_range(-1.8, 1.8)
			x += krok
			if absf(px + 4.0) < 60.0 and absf(pz) < 55.0:
				continue                                    # tvrz a jeji bezprostredni okoli maji vlastni (_tvrz_zvenci)
			if Vector2(px - 470.0, pz - 830.0).length() < 110.0:
				continue                                    # ves ma vlastni dvory a zahrady
			var les := _les(px, pz)
			var jehl := _st(0, px, pz) / maxf(les, 0.01)
			var skal := _st(2, px, pz)
			var pes := _st(3, px, pz)
			var m := _louka_m(px, pz)
			var u := rng.randf()
			if u > 0.30:
				continue                                    # nic z nize nema vetsi pravdepodobnost nez 30 %
			var okraj := 0.0
			if les < 0.12 and m > 0.2:
				# plast lesa 15-20 m (hlaseni 0.54, 16:50: keř je na fotkach vzacnost): les do 9 a do 18 m od bodu
				for o: float in [9.0, 18.0]:
					okraj = maxf(okraj, maxf(maxf(_les(px + o, pz), _les(px - o, pz)), maxf(_les(px, pz + o), _les(px, pz - o))) * (1.0 if o < 10.0 else 0.8))
			var sklon := 0.0
			if les <= 0.25 and skal <= 0.45 and pes <= 0.55 and u < 0.09:
				sklon = Vector2(_vyska(px + 2, pz) - _vyska(px - 2, pz), _vyska(px, pz + 2) - _vyska(px, pz - 2)).length() / 4.0
			var k := ""
			var sc := 1.0
			var ponor := 0.05
			if les < 0.12 and okraj > 0.35 and m > 0.2 and u < 0.30:
				k = kere[rng.randi() % kere.size()]                    # plast okraje lesa
				sc = rng.randf_range(0.8, 1.4)
			elif skal > 0.45 and les < 0.9:
				if u < 0.45:
					k = kameni[rng.randi() % kameni.size()]          # sut pod skalami
					sc = clampf(exp(rng.randfn(0.5, 0.5)), 0.7, 4.0)
					ponor = 0.3
				elif u < 0.53:
					k = "balvan_piskovec_2_0" if rng.randf() < 0.6 else "balvan_piskovec_1_0"
					sc = rng.randf_range(0.5, 1.2)
					ponor = 0.3
				elif u < 0.60:
					k = kere[rng.randi() % 2]
			elif les > 0.25:
				if jehl > 0.5 and u < 0.10:
					k = kameni[rng.randi() % kameni.size()]          # kameni v boru
					sc = clampf(exp(rng.randfn(0.2, 0.5)), 0.5, 3.5)     # log-normalne: hodne malych, malo velkych
					ponor = 0.3
				elif jehl > 0.5 and u < 0.13:
					k = "kamen_piskovec_1_0"
					sc = rng.randf_range(0.6, 1.4)
					ponor = 0.15
				elif u < 0.155:
					k = "mech_%d_0" % (rng.randi() % 3 + 1)
					sc = rng.randf_range(0.04, 0.08)
				elif u < 0.165:
					k = "pine_sapling_small_0" if jehl > 0.5 else kere[rng.randi() % kere.size()]   # nalet
				elif u < 0.175 and jehl <= 0.5:
					k = "bark_debris_01_%d" % (rng.randi() % 4)
				elif u < 0.178:
					k = "dead_tree_trunk_0" if rng.randf() < 0.5 else "dead_tree_trunk_02_0"     # padle kmeny
					ponor = 0.15
				elif u < 0.182:
					k = ""                                           # vyvraceny koren jen u padleho kmene (nize)
				elif u < 0.192:
					k = "balvan_zula_1_0" if jehl <= 0.5 else "balvan_piskovec_3_0"           # zarostle balvany
					sc = rng.randf_range(0.4, 0.9)
					ponor = 0.35
			elif pes > 0.5 and pes < 0.75 and u < 0.06:
				k = kameni[rng.randi() % kameni.size()]              # kameni na kraji pesiny (0,8-1,5 m od osy)
				sc = clampf(exp(rng.randfn(0.0, 0.45)), 0.5, 2.5)
				ponor = 0.3
			elif sklon > 0.3 and m > 0.1 and u < 0.09:
				# svahy a strane (radce 17:00): nahore Cesky raj - piskovec, dole Posazavi - zula a droba (ohlazene, sede)
				var nahore := _vyska(px, pz) > 20.0
				var w2 := rng.randf()
				# jen balvany, drobne kameni na louce ne (radce 20:05 bod 7)
				if w2 < 0.5:
					k = ("balvan_piskovec_2_0" if rng.randf() < 0.6 else "balvan_piskovec_1_0") if nahore else ("balvan_zula_1_0" if rng.randf() < 0.5 else "balvan_droba_1_0")
					sc = clampf(exp(rng.randfn(0.0, 0.35)), 0.5, 1.6)
					ponor = 0.35
			if k != "":
				pridej.call(k, px, pz, sc, ponor * sc if not k.begins_with("kamen") else -0.3, 0.25)
				pocty[k.substr(0, k.rfind("_"))] = int(pocty.get(k.substr(0, k.rfind("_")), 0)) + 1
				# vyvraceny koren (hlaseni 0.54 bod 3): jen v lese vedle padleho kmene, ne sam na louce
				if k.begins_with("dead_tree") and les > 0.6:
					var rk := RandomNumberGenerator.new()
					rk.seed = hash(Vector2(pz, px))
					var ko := Vector2.from_angle(rk.randf() * TAU) * rk.randf_range(1.5, 3.0)
					if _les(px + ko.x, pz + ko.y) > 0.6 and _st(3, px + ko.x, pz + ko.y) < 0.4:
						pridej.call("root_cluster_01_0", px + ko.x, pz + ko.y, 1.0, 0.1, 0.25)
						pocty["root_cluster_01"] = int(pocty.get("root_cluster_01", 0)) + 1
		z += krok
	_vychozy(rng, pridej, pocty)
	_pata_sten(pridej, pocty)
	_lom(pridej, pocty)
	# kameny v korytu a na brehu potoka (radce 04:55 bod 4) a zarez udoli jako v Posazavi (hlaseni 0.54 bod 1, 16:50,
	# Misa: skalnaty kanon): balvany (zula, droba) v korytu a u paty brehu, na narazovem brehu zatacky skalni vychozy
	# a sut zapustene do svahu, na svahu a hrane keře (liska, bez, sipek) a olse/vrby; jesep na vnitrnim brehu oblazky
	if koryto:
		var kr = koryto
		var kam := ["kamen_maly_1_0", "kamen_maly_2_0", "kamen_maly_3_0", "kamen_maly_4_0", "kamen_maly_5_0", "kamen_zula_1_0", "kamen_zula_2_0"]
		var balv := ["balvan_zula_1_0", "balvan_droba_1_0"]
		var kere_v := ["shrub_02_0", "shrub_02_1", "bez_cerny_1_0", "bez_cerny_2_0", "sipek_0"]
		var nk := 0
		var nv := 0
		var nkr := 0
		var vys := func(x: float, z: float) -> float: return _vyska(x, z)
		for k in kr.body.size() - 1:
			var a: Vector2 = kr.body[k]
			var b: Vector2 = kr.body[k + 1]
			var nrm := (b - a).normalized().orthogonal()
			var w: float = kr.sirky[k]
			var dl := a.distance_to(b)
			var t := 0.0
			while t < dl:
				t += rng.randf_range(0.8, 2.2)
				var u := rng.randf()
				var o := a.lerp(b, minf(t, dl) / dl)
				var sg := 1.0 if rng.randf() < 0.5 else -1.0
				if u < 0.6:
					# na brehu a u kraje vody (pas w-0,4 .. w+1,4 na obou stranach)
					var of := rng.randf_range(w - 0.4, w + 1.4)
					var q := o + nrm * (of * sg)
					var sk := rng.randf_range(1.5, 4.0)
					pridej.call(kam[rng.randi() % kam.size()], q.x, q.y, sk, 0.05, 0.4)
				elif u < 0.8:
					# balvany v korytu, vycnivaji nad hladinu (obtekani, pena z peceni vody)
					var q := o + nrm * rng.randf_range(-w * 0.8, w * 0.8)
					var sb := rng.randf_range(0.5, 1.0)
					pridej.call(balv[rng.randi() % 2], q.x, q.y, sb, 0.25, 0.3)
					kameny_toku.append(Vector4(q.x, q.y, 0.55 * sb, atan2((b - a).y, (b - a).x)))
				nk += 1
			# zarez: kazdych ~3 m na kazde strane podle sirky zarezu (kde svah potka teren)
			t = 0.0
			while t < dl:
				t += rng.randf_range(2.0, 4.0)
				var o := a.lerp(b, minf(t, dl) / dl)
				for sg: float in [1.0, -1.0]:
					var smer: Vector2 = nrm * sg
					var hr: float = kr.hrana(o, smer, w, vys)
					var bl: Array = kr.blizko(o.x + smer.x * (w + 1.0), o.y + smer.y * (w + 1.0))
					var vn: float = float(bl[3]) if not bl.is_empty() else 0.0
					var svah := hr - w - 0.6                 # delka svahu (m)
					var u := rng.randf()
					if svah > 1.5 and vn < -0.3 and u < 0.55 * -vn:
						# narazovy breh: skalni vychoz (velky balvan zapusteny do svahu) a sut pod nim
						var dq := rng.randf_range(w + 1.0, maxf(w + 1.5, hr - 1.0))
						var q := o + smer * dq
						var sc := rng.randf_range(1.0, 2.2) * clampf(svah / 5.0, 0.6, 1.6)
						pridej.call(balv[rng.randi() % 2], q.x, q.y, sc, 0.5 * sc, 0.5)
						for m in 3:
							var q2 := o + smer * rng.randf_range(w + 0.6, dq) + (b - a).normalized() * rng.randf_range(-2.0, 2.0)
							pridej.call(kam[rng.randi() % kam.size()], q2.x, q2.y, rng.randf_range(2.0, 5.0), 0.08, 0.5)
						nv += 1
					elif svah > 1.0 and u < 0.25:
						# balvan zapusteny do svahu (ne prilepeny): pulka v zemi
						var q := o + smer * rng.randf_range(w + 1.2, hr)
						var sc := rng.randf_range(0.5, 1.3)
						pridej.call(balv[rng.randi() % 2], q.x, q.y, sc, 0.45 * sc, 0.4)
						nk += 1
					u = rng.randf()
					if u < 0.45:
						# kere na svahu a na hrane (az 3 m za ni); na jesepu ne
						var q := o + smer * rng.randf_range(w + 1.5 + 4.0 * maxf(vn, 0.0), hr + 3.0)
						if smi_tu_byt(q.x, q.y, "kere"):
							pridej.call(kere_v[rng.randi() % kere_v.size()], q.x, q.y, rng.randf_range(0.8, 1.4), 0.05)
							nkr += 1
		pocty["kameny v potoce"] = nk
		pocty["vychozy v zarezu"] = nv
		pocty["kere v zarezu"] = nkr
		pocty["kameny ve vode (cereni)"] = kameny_toku.size()
		_stromy_u_potoka(r, rng)
	# Misa 0.68 (513,870): rakosi z exportu na suchu kolem rybnika. Rakos a orobinec jen 0-1,5 m od hladiny
	# (nadrz: vzdalenost od brehu; potok: od kraje vody); u tvrze prikop (bez nadrze v datech) nechat
	var pryc_r := 0
	for kk0: String in r.keys():
		if not (kk0.begins_with("rakos_") or kk0.begins_with("orobinec_")) or kk0.contains("_daleko"):
			continue
		var zust: Array = []
		for t: Array in r[kk0]:
			var rxx: float = t[3]
			var rzz: float = t[11]
			var ok := absf(rxx + 4.0) < 80.0 and absf(rzz) < 75.0
			if not ok and nadrz:
				var m: Array = nadrz.misto(rxx, rzz)
				ok = not m.is_empty() and float(m[0]) > -1.5 and float(m[0]) < 0.6
			if not ok and koryto:
				var bl: Array = koryto.blizko(rxx, rzz)
				ok = not bl.is_empty() and float(bl[0]) > float(bl[2]) - 0.6 and float(bl[0]) < float(bl[2]) + 1.5
			if ok:
				zust.append(t)
			else:
				pryc_r += 1
		r[kk0] = zust
	pocty["rakos na suchu pryc"] = pryc_r
	# rakos a orobinec v pasu bahna u rybniku a prikopu (radce 04:55 bod 5)
	if nadrz:
		var vod := []
		for kk: String in ["rakos_1_0", "rakos_2_0", "orobinec_1_0", "orobinec_2_0"]:
			if r.has(kk) and not (r[kk] as Array).is_empty():
				vod.append(kk)
		var nr := 0
		for nd2: Dictionary in nadrz.nadrze:
			var dd: PackedFloat32Array = nd2["d"]
			for j in range(0, int(nd2["nz"]), 2):
				for i in range(0, int(nd2["nx"]), 2):
					var d: float = dd[j * int(nd2["nx"]) + i]
					if d > 0.25 or d < -1.2 or rng.randf() > 0.45 or vod.is_empty():       # jen pas bahna, ne ve vode
						continue
					var rx := float(nd2["x0"]) + i * 0.5 + rng.randf_range(-0.4, 0.4)
					var rz := float(nd2["z0"]) + j * 0.5 + rng.randf_range(-0.4, 0.4)
					var kk: String = vod[rng.randi() % vod.size()]
					var t := _xf(rx, minf(_vyska(rx, rz), float(nd2["y"])) - 0.05, rz, rng.randf() * TAU, float(mer.get(kk, 1.0)) * rng.randf_range(0.8, 1.25))
					(r[kk] as Array).append(t)
					nr += 1
		pocty["rakos u vody"] = nr
		pocty["prikop kameny"] = _prikop_kameny(r, rng, pridej)
	print("krajina 07:50: ", pocty)


## Vyska terenu u tvrze z vrcholu siti Teren* (po vyhloubeni prikopu): mrizka 1 m, nejvyssi vrchol v bunce,
## prazdne bunky z nejblizsiho souseda do 2 m. INF = nic.
func _vyska_sit(x: float, z: float) -> float:
	if _vys_sit.is_empty() and _tvrz_root:
		for mi in _tvrz_root.find_children("Teren*", "MeshInstance3D", true, false):
			var nm := String(mi.name)
			if nm == "Teren_obzor":
				continue
			var xf := (mi as MeshInstance3D).global_transform
			var me := (mi as MeshInstance3D).mesh
			for si in me.get_surface_count():
				for v: Vector3 in me.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
					var w := xf * v
					if absf(w.x + 4.0) > 80.0 or absf(w.z) > 75.0:
						continue
					var c := Vector2i(floori(w.x), floori(w.z))
					_vys_sit[c] = maxf(float(_vys_sit.get(c, -INF)), w.y)
		_vys_sit[Vector2i(99999, 99999)] = 0.0             # postaveno (i kdyby bez vrcholu)
	var c0 := Vector2i(floori(x), floori(z))
	for rr in 3:
		var best := -INF
		for dx in range(-rr, rr + 1):
			for dz in range(-rr, rr + 1):
				best = maxf(best, float(_vys_sit.get(c0 + Vector2i(dx, dz), -INF)))
		if best > -INF:
			return best
	return INF


## Prikop tvrze (hlaseni 0.54, 16:50): hranu rozbit - u paty hradby (vnitrni breh) kamenna plenta z hustych kamenu
## v pasu 0-1,5 m od vody, na vnejsim svahu sut a balvany zapustene do svahu. Z pole vzdalenosti od brehu (nadrz.gd).
func _prikop_kameny(r: Dictionary, rng: RandomNumberGenerator, pridej: Callable) -> int:
	var stred := Vector2(-4.5, 0.4)
	var kam := ["kamen_zula_1_0", "kamen_zula_2_0", "kamen_piskovec_1_0", "kamen_maly_2_0", "kamen_maly_4_0"]
	var n := 0
	for nd: Dictionary in nadrz.nadrze:
		var nx := int(nd["nx"])
		var nz := int(nd["nz"])
		var x0 := float(nd["x0"])
		var z0 := float(nd["z0"])
		if Vector2(x0 + nx * 0.25, z0 + nz * 0.25).distance_to(stred) > 20.0:
			continue                                          # jen prikop kolem tvrze (rybnik je jinde)
		var dd: PackedFloat32Array = nd["d"]
		var y0 := float(nd["y"])
		# stredni vzdalenost vody od stredu tvrze: blize = vnitrni breh u hradby
		var vzd: Array = []
		for j in range(0, nz, 4):
			for i in range(0, nx, 4):
				if dd[j * nx + i] > 1.0:
					vzd.append(Vector2(x0 + i * 0.5, z0 + j * 0.5).distance_to(stred))
		if vzd.is_empty():
			continue
		vzd.sort()
		var stred_vody: float = vzd[vzd.size() / 2]
		for j in nz:
			for i in nx:
				var d := dd[j * nx + i]
				if d > 0.3 or d < -6.0 or rng.randf() > 0.5:
					continue
				var px := x0 + i * 0.5 + rng.randf_range(-0.25, 0.25)
				var pz := z0 + j * 0.5 + rng.randf_range(-0.25, 0.25)
				if absf(px + 3.0) < 4.0 and pz > 10.0:
					continue                                  # most a brana
				var vnitrni := Vector2(px, pz).distance_to(stred) < stred_vody
				var y := _vyska_sit(px, pz)
				if y == INF or y < y0 - 0.4:
					continue
				var k := ""
				var sc := 1.0
				var ponor := 0.05
				var u := rng.randf()
				if vnitrni and d > -1.5 and u < 0.3:
					k = kam[2 + rng.randi() % 3]              # plenta: husty pas kamenu u vody (levne site; zula jen na sut)
					sc = rng.randf_range(2.0, 3.2)
					ponor = 0.1
				elif not vnitrni and d > -6.0 and u < 0.06:
					k = kam[rng.randi() % kam.size()]         # sut na vnejsim svahu
					sc = rng.randf_range(1.0, 3.0)
				elif not vnitrni and d > -5.0 and u < 0.075:
					k = "balvan_zula_1_0" if rng.randf() < 0.5 else "balvan_droba_1_0"
					sc = rng.randf_range(0.5, 1.1)
					ponor = 0.45 * sc
				if k == "":
					continue
				pridej.call(k, px, pz, sc, ponor, 0.3, y)          # vyska ze site (val a prikop mrizka louky nezna)
				n += 1
	return n


## Stromy u potoka (hlaseni 0.54 bod 1): do 2 m od hrany zarezu a na jeho svahu jen olse a vrby (koreny pres breh),
## dub, lipa, buk, briza a smrk odtud pryc (i jejich vzdalene verze - stejny index instance); olse podel hrany.
func _stromy_u_potoka(r: Dictionary, rng: RandomNumberGenerator) -> void:
	var kr = koryto
	var vys := func(x: float, z: float) -> float: return _vyska(x, z)
	var blizko_hrany := func(x: float, z: float) -> bool:
		var bl: Array = kr.blizko(x, z)
		if bl.is_empty():
			return false
		return float(bl[0]) < float(bl[2]) + 0.6 or kr.strop(x, z) < _vyska(x, z) + 0.5 or float(kr.blizko(x, z)[0]) < _hrana_v(kr, x, z, vys) + 2.0
	var pryc := 0
	# Misa 0.60: "strom v rece a v moste zaroven" - zadny strom (ani olse a vrba) ve vode ani do 4 m od mostu
	var most := AABB()
	if _tvrz_root:
		var mm := _tvrz_root.find_child("Most_potok", true, false) as MeshInstance3D
		if mm:
			most = (mm.global_transform if mm.is_inside_tree() else mm.transform) * mm.get_aabb()
			most = most.grow(4.0)
	for key: String in r.keys():
		# u mostu nic vysokeho (Misa 0.62: "most ma zase v zabradli strom" - ker / mlady strom): stromy i kere
		var ker := key.begins_with("shrub") or key.begins_with("bez_") or key.begins_with("sipek") or key.begins_with("liska")
		if _strom_tvar(key.split("_daleko")[0]) == "" and not key.begins_with("vrba") and not key.begins_with("olse") and not ker:
			continue
		var par0 := key.replace("_0", "_daleko_0") if key.ends_with("_0") and not key.contains("_daleko") else ""
		var ma_par0 := par0 != "" and r.has(par0) and (r[par0] as Array).size() == (r[key] as Array).size()
		if key.contains("_daleko") and r.has(key.replace("_daleko", "")):
			continue                                  # vzdalena verze se filtruje s plnou (stejny index)
		var z1: Array = []
		var z2: Array = []
		for i in (r[key] as Array).size():
			var t: Array = r[key][i]
			var x := float(t[3])
			var z := float(t[11])
			var bl: Array = kr.blizko(x, z)
			var ve_vode := not bl.is_empty() and float(bl[0]) < float(bl[2]) + 0.3
			var u_mostu := most.size != Vector3.ZERO and x > most.position.x and x < most.end.x and z > most.position.z and z < most.end.z
			# Misa 0.60: male brizy v krajine rusi (svitici kura) - mladé (meritko < 0,3, pulka bříz) pryc
			var mala_briza := key.begins_with("briza") and Vector3(float(t[1]), float(t[5]), float(t[9])).length() < 0.3
			# tvrz, val a prikop: obrana - zadny strom u hradby ani v prikopu (Misa 0.61: bríza u zdi v prikopu)
			var u_tvrze := absf(x + 4.0) < 38.0 and absf(z) < 34.0
			if ker and not u_mostu:
				z1.append(t)
				if ma_par0:
					z2.append(r[par0][i])
				continue
			if ve_vode or u_mostu or mala_briza or u_tvrze:
				pryc += 1
				continue
			z1.append(t)
			if ma_par0:
				z2.append(r[par0][i])
		r[key] = z1
		if ma_par0:
			r[par0] = z2
	for key: String in r.keys():
		if key.contains("_daleko") or not (key.begins_with("dub") or key.begins_with("lipa") or key.begins_with("buk") \
				or key.begins_with("briza") or key.begins_with("smrk")):
			continue
		var par := key.replace("_0", "_daleko_0") if key.ends_with("_0") else ""
		var ma_par := par != "" and r.has(par) and (r[par] as Array).size() == (r[key] as Array).size()
		var zust: Array = []
		var zust2: Array = []
		for i in (r[key] as Array).size():
			var t: Array = r[key][i]
			if blizko_hrany.call(float(t[3]), float(t[11])):
				pryc += 1
				continue
			zust.append(t)
			if ma_par:
				zust2.append(r[par][i])
		r[key] = zust
		if ma_par:
			r[par] = zust2
	# olse podel hrany, kazdych 12-25 m strida strany (mlada a stredni, se vzdalenou verzi)
	var olse := 0
	var t0 := 0.0
	for k in kr.body.size() - 1:
		var a: Vector2 = kr.body[k]
		var b: Vector2 = kr.body[k + 1]
		t0 += a.distance_to(b)
		if t0 < rng.randf_range(12.0, 25.0):
			continue
		t0 = 0.0
		var nrm := (b - a).normalized().orthogonal() * (1.0 if rng.randf() < 0.5 else -1.0)
		var hr: float = kr.hrana(a, nrm, float(kr.sirky[k]), vys)
		var q := a + nrm * rng.randf_range(float(kr.sirky[k]) + 1.0, hr + 1.5)
		if not smi_tu_byt(q.x, q.y, "olse"):
			continue
		var druh := "olse_mlada" if rng.randf() < 0.4 else "olse_stredni"
		if not r.has(druh + "_0") or not r.has(druh + "_daleko_0") or (r[druh + "_0"] as Array).is_empty():
			continue
		var t1: Array = r[druh + "_0"][0]
		var mer := Vector3(t1[0], t1[4], t1[8]).length()
		var xf := _xf(q.x, _vyska(q.x, q.y) - 0.2, q.y, rng.randf() * TAU, mer * rng.randf_range(0.8, 1.2))
		(r[druh + "_0"] as Array).append(xf)
		(r[druh + "_daleko_0"] as Array).append(xf.duplicate())
		olse += 1
	print("stromy u potoka: pryc %d, olse %d" % [pryc, olse])


func _hrana_v(kr, x: float, z: float, vys: Callable) -> float:
	var bl: Array = kr.blizko(x, z)
	if bl.is_empty():
		return 0.0
	# smer od osy: kolmo podle gradientu vzdalenosti
	var e := 0.5
	var g := Vector2(float(kr.blizko(x + e, z)[0]) - float(kr.blizko(x - e, z)[0]) if not kr.blizko(x + e, z).is_empty() and not kr.blizko(x - e, z).is_empty() else 0.0,
			float(kr.blizko(x, z + e)[0]) - float(kr.blizko(x, z - e)[0]) if not kr.blizko(x, z + e).is_empty() and not kr.blizko(x, z - e).is_empty() else 0.0)
	if g.length() < 1e-4:
		return float(bl[2])
	g = g.normalized()
	var o := Vector2(x, z) - g * float(bl[0])
	return kr.hrana(o, g, float(bl[2]), vys)


## Skalni vychozy mimo skalni mesto (20-40 kusu): na hrbetech v lese, s borovici na vrcholu a kapradim u paty.
func _vychozy(rng: RandomNumberGenerator, pridej: Callable, pocty: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	var key := "skala_hlava_0"
	if not r.has(key):
		return
	var sit := _skala_sit(key)
	var tvar := sit.create_trimesh_shape() if sit else null
	var bb := sit.get_aabb() if sit else AABB()
	var horni := _horni_plochy(sit) if sit else PackedVector3Array()
	var n := 0
	var pokus := 0
	while n < 30 and pokus < 4000:
		pokus += 1
		var x := rng.randf_range(stan_rect.position.x + 40, stan_rect.end.x - 40)
		var z := rng.randf_range(stan_rect.position.y + 40, stan_rect.end.y - 40)
		if _les(x, z) < 0.3 or _st(2, x, z) > 0.05 or absf(x + 4.0) < 90.0 and absf(z) < 90.0 or kosena_louka(x, z) or pes_d(x, z) < 8.0:
			continue
		var h := _vyska(x, z)
		var okoli := 0.0
		for q in 8:
			okoli += _vyska(x + cos(q * TAU / 8) * 25.0, z + sin(q * TAU / 8) * 25.0)
		if h - okoli / 8.0 < 3.0:
			continue                                         # jen hrbet nebo vrsek
		var s := rng.randf_range(4.0, 6.5) / maxf(bb.size.y, 1.0)
		var low := h
		for q in 8:
			low = minf(low, _vyska(x + cos(q * TAU / 8) * bb.size.x * s * 0.45, z + sin(q * TAU / 8) * bb.size.x * s * 0.45))
		var xf := _xf(x, low - 0.5 - bb.position.y * s, z, rng.randf() * TAU, s)
		(r[key] as Array).append(xf)
		for k2: String in ["skala_hlava_daleko_0", "skala_hlava_daleko2_0"]:
			if r.has(k2):
				(r[k2] as Array).append(xf)
		if tvar and _kolize_body:
			kolize(tvar, bb, Transform3D(Basis(Vector3(xf[0], xf[4], xf[8]), Vector3(xf[1], xf[5], xf[9]), Vector3(xf[2], xf[6], xf[10])), Vector3(xf[3], xf[7], xf[11])))
		# borovice na vrcholu (svisly paprsek na horni plochy vychozu), kapradi a sut u paty
		if r.has("borovice_0"):
			var xft := Transform3D(Basis(Vector3(xf[0], xf[4], xf[8]), Vector3(xf[1], xf[5], xf[9]), Vector3(xf[2], xf[6], xf[10])), Vector3(xf[3], xf[7], xf[11]))
			var inv := xft.affine_inverse()
			var o := inv * Vector3(x, low + 80.0, z)
			var dd := (inv.basis * Vector3.DOWN).normalized()
			var top := -INF
			for i in range(0, horni.size(), 3):
				var hh: Variant = Geometry3D.ray_intersects_triangle(o, dd, horni[i], horni[i + 1], horni[i + 2])
				if hh != null:
					top = maxf(top, (xft * (hh as Vector3)).y)
			if top == -INF:
				top = low - 0.5 + bb.size.y * s * 0.92
			var ref: Array = r["borovice_0"][0]
			(r["borovice_0"] as Array).append(_xf(x, top - 0.1, z, rng.randf() * TAU,
					Vector3(ref[0], ref[4], ref[8]).length() * rng.randf_range(0.5, 0.75)))
		for q in 6:
			var a := rng.randf() * TAU
			var d := bb.size.x * s * rng.randf_range(0.5, 0.8)
			pridej.call("kapradi_%d_0" % (q % 3 + 1) if q < 3 else "kamen_maly_%d_0" % (q % 5 + 1), x + cos(a) * d, z + sin(a) * d,
					rng.randf_range(0.8, 1.3) if q < 3 else rng.randf_range(1.0, 3.0), 0.05)
		n += 1
	pocty["vychozy"] = n


## Povrchy lesa a pesin (radce 07:50 bod 1) jako dve pole textur (jeden sampler: mobilni GPU maji 16 jednotek).
## 8 piskovec skalni steny (radce 06:40 bod 7): jen albedo, reliéf dela zem.gdshader z jasu (pudy_n ma 8 vrstev)
## Vrstva 0 se na PC (GL compat) kresli cerna -> mech (hrabanka) byl cerny a odrazel oblohu = modrobile "snehove"
## svahy (radce 0.63 skala, test pole vrstev); na 0 proto pesina, kterou zem.gdshader nepouziva, hrabanka je 4.
const PUDY := ["pesina", "les_listi", "les_jehlici", "les_pisek", "hrabanka", "oblazky", "blato", "kamen_lisejnik", "skala_piskovec"]


## Vrstva pole textur. t.get_image() cte texturu zpet z GPU a u ETC2 (na PC rozbalene pri nahrani) vracel nesmysl:
## data RGBA vydavana za ETC2 -> "rozbalena" do nahodnych barev (bily zrnity sum lisejniku, modrobile "snehove" svahy,
## bile skvrny v lese - Misa 0.61, radce 0.63 skala; zjisteno vypisem pixelu ve hre). Proto obrazek primo z importu
## (.ctex: hlavicka GST2 + surova data s mipmapami). Na PC bez ETC2 rozbalit na 512 px a mipmapy dopocitat
## (RGBA8 je 4x vetsi nez ETC2), tablet bere ETC2 primo.
func _pudy_img(t: Texture2D) -> Image:
	var im: Image = null
	var proc := ""
	if t is CompressedTexture2D:
		var cesta := (t as CompressedTexture2D).load_path
		var f := FileAccess.open(cesta, FileAccess.READ) if cesta != "" else null
		if f == null:
			proc = "nelze otevrit"
		elif f.get_length() < 52 or f.get_buffer(4).get_string_from_ascii() != "GST2":
			proc = "neni GST2"
		else:
			var ver := f.get_32()
			for q in 7:
				f.get_32()                      # sirka, vyska, priznaky, limit mipmap, 3 rezervy
			var df := f.get_32()
			var w := f.get_16()
			var h := f.get_16()
			var mm := f.get_32()
			var fmt := f.get_32()
			if ver != 1 or df != 0:
				proc = "verze %d / data %d" % [ver, df]
			elif w == 0 or h == 0 or fmt >= Image.FORMAT_MAX:
				proc = "hlavicka %dx%d format %d" % [w, h, fmt]
			else:
				var buf := f.get_buffer(f.get_length() - f.get_position())
				# velikost dat proti ocekavane (prazdny obrazek tehoz tvaru) - create_from_data by jinak hlasil chybu
				var vzor := Image.create_empty(w, h, mm > 0, fmt as Image.Format)
				if vzor == null or vzor.get_data_size() != buf.size():
					proc = "data %d B, cekano %d B" % [buf.size(), vzor.get_data_size() if vzor else -1]
				else:
					im = Image.create_from_data(w, h, mm > 0, fmt as Image.Format, buf)
		if im == null or im.is_empty():
			push_warning("pudy: %s - %s, beru get_image()" % [cesta, proc])
			im = null
	if im == null:
		im = t.get_image()
	if im == null or im.is_empty():
		push_warning("pudy: textura %s bez obrazku, sedy zastupce" % t.resource_path)
		im = Image.create_empty(512, 512, true, Image.FORMAT_RGBA8)
		im.fill(Color(0.3, 0.27, 0.22))
		im.generate_mipmaps()
	# PC bez ETC2: rozbalit (512 px, mipmapy dopocitat); tablet ETC2 beze zmeny (RAM)
	if im.is_compressed() and not RenderingServer.has_os_feature("etc2"):
		im = im.duplicate()
		im.decompress()
		im.clear_mipmaps()
		if im.get_width() > 512:
			im.resize(512, 512, Image.INTERPOLATE_BILINEAR)
		im.generate_mipmaps()
	return im


## Texture2DArray.create_from_images chce u vsech vrstev stejnou velikost, format i mipmapy (balik z_textury muze
## orezat jen nekterou .ctex). Kdyz nesedi: vsechny rozbalit a zmensit na nejmensi spolecnou velikost (vyjimka -
## pamet na chvili vic, varovani do logu); jinak beze zmeny.
func _pudy_sjednot(ims: Array[Image]) -> Array[Image]:
	var ok := true
	var w := 1 << 20
	for im: Image in ims:
		w = mini(w, mini(im.get_width(), im.get_height()))
		if im.get_size() != ims[0].get_size() or im.get_format() != ims[0].get_format() or im.has_mipmaps() != ims[0].has_mipmaps():
			ok = false
	if ok:
		return ims
	push_warning("pudy: vrstvy pole maji ruzny tvar - sjednocuji na %d px RGBA8" % w)
	var out: Array[Image] = []
	for im: Image in ims:
		var d := im.duplicate()
		if d.is_compressed():
			d.decompress()
		d.convert(Image.FORMAT_RGBA8)
		d.clear_mipmaps()
		d.resize(w, w, Image.INTERPOLATE_BILINEAR)
		d.generate_mipmaps()
		out.append(d)
	return out


func _pudy(s3: ShaderMaterial) -> void:
	var ia: Array[Image] = []
	var inn: Array[Image] = []
	var ks := PackedFloat32Array()
	for nm: String in PUDY:
		ia.append(_pudy_img(_t(nm, "diff")))
		if nm != "skala_piskovec":
			inn.append(_pudy_img(_t(nm, "nor")))
		# Misa 0.61: na svazich v lese bile/smetanove skvrny (pisek s jehlicim, svetle listi) - lesni puda tmavsi
		# 0.63: puvodni 0,65 tlumilo rozbity obrazek z get_image() (svetle skvrny); se spravnym .ctex v hlubokem stinu
		# lesa puda skoro cerna (snimek skala_t5_les1) -> 0,85
		var tm := 0.7 if nm.begins_with("les_") else (0.75 if nm == "oblazky" or nm == "blato" else 1.0)   # bile tecky na brehu prikopu
		if nm == "skala_piskovec":
			tm = 2.5                       # piskovec svetlejsi nez lesni puda (~0,2, sedobezovy jako bloky skal)
		ks.append(0.08 / maxf(float(_albedo().get(nm, 0.08)), 0.01) * tm)   # kalibrace odrazivosti (lesni puda ~0,08)
	var ta := Texture2DArray.new()
	ta.create_from_images(_pudy_sjednot(ia))
	var tn := Texture2DArray.new()
	tn.create_from_images(_pudy_sjednot(inn))
	s3.set_shader_parameter("pudy_a", ta)
	s3.set_shader_parameter("pudy_n", tn)
	s3.set_shader_parameter("pudy_k", ks)
	s3.set_shader_parameter("pudy_m", 2.2)
	s3.set_shader_parameter("stanoviste", ImageTexture.create_from_image(stanoviste))
	s3.set_shader_parameter("stan_k", float(data["trava_kraj"]["k"]))
	s3.set_shader_parameter("stan_rect", Vector4(stan_rect.position.x, stan_rect.position.y, stan_rect.size.x, stan_rect.size.y))


func _plants(parent: Node3D, quality: int) -> void:
	var root := Node3D.new()
	root.name = "Rostliny"
	# staticke MultiMeshe bez interpolace fyziky (project: physics_interpolation): s ni se zmena instance mimo krok
	# fyziky (dosednout) vratila zpet a kazda bunka nesla dvojity buffer
	root.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	parent.add_child(root)
	var keep_low: float = [0.3, 0.6, 1.0][quality]
	var keep_tree: float = [0.5, 0.8, 1.0][quality]
	var grass_mat := material("trava_divoka")
	var scenes := {}
	# pudorysy statickych staveb (hostinec, stan): uvnitr zadna trava, kapradi ani kere (rostla v krbu)
	var uvnitr: Array = []
	_nacti_kryti()
	_cesta_do_kryti()
	for n in parent.find_children("Staticky_*", "Node3D", true, false):
		var bb := AABB()
		var prvni := true
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var b := ((n as Node3D).global_transform.affine_inverse() * (mi as MeshInstance3D).global_transform) * (mi as MeshInstance3D).get_aabb()
			bb = b if prvni else bb.merge(b)
			prvni = false
		if not prvni and bb.size.x > 4.0 and bb.size.z > 4.0:
			uvnitr.append([(n as Node3D).global_transform.affine_inverse(), bb.grow(-0.1)])
	# dil mlyna (vlastni teren, dvur, budova): zadna trava ani rozsev uvnitr ctverce dilu (jako budova)
	if _mlyn_inv != Transform3D():
		uvnitr.append([_mlyn_inv, AABB(Vector3(-22.0, -30.0, -25.0), Vector3(40.0, 60.0, 40.0)), "dil"])     # louka: trava z terenu dilu
	_uvnitr = uvnitr
	_pruchody = {}                           # znovu: vrata stodol a dvere novych domu pribyly az po prvnim dotazu (0.98)
	v_pruchodu(0.0, 0.0)                     # mrizka pruchodu v hlavnim vlakne (louka ve vlaknech jen cte)
	# Poradi podle kontraktu (docs/pipeline.md, Astra 22:00 bod 3): krok cte jen vystupy drivejsich kroku, druh se nesazi
	# tam, kde nema byt (druhy.json), misto aby se pozdeji mazal.
	# krok 0: katalog - druhy s „pouzit“: false se z dat vyradi pred vsemi rozsevy (sipek, vrba hlavata); rozsevy jejich
	# klice nenajdou a nesazi je
	_druhy_nacti()
	_druhy_mimo_katalog()
	# krok 6a: stromy z dat a lesu (Blender, skalni mesto, nove lesy)
	_smrky_na_listnace()
	_skalni_mesto()
	# lesni patro (krok 8) jen k dosavadnim stromum - nove lesy maji vlastni lem a podrost (stejne pocty jako drive)
	_stromy_6a = {}
	for k: String in data["rostliny"]:
		_stromy_6a[k] = (data["rostliny"][k] as Array).size()
	_nove_lesy()
	# krok 5 + 7: masky pesin a lomu, kryt korun ze stromu 6a
	_stanoviste()
	# krok 6b: doplneni lesa uvnitr zapoje - mlade stromy pod korunami, stromoradi podel lesnich pesin, plast lesa; cte
	# kryt 7 (jehlicnan / listnac podle porostu) a kryt nemeni (mlade stromy a lem uvnitr a na kraji zapoje)
	_les_hustsi()
	_lesni_plast()
	# krok 8 vstup: kazdy kus z Blenderu a kroku 6 na stanovisti sveho druhu podle masek kroku 7 (druhy.json vyjma:
	# kosena_louka - smrk a kameni ne v kosene louce, radce 17:00); dal kazdy rozsev vola druh_smi_hra sam
	_vstup_druhu()
	# krok 8: podrost, kere, byliny, kameni
	_krajina()
	if _mats.has("zem"):
		_pudy(_mats["zem"] as ShaderMaterial)
	_lesni_patro()
	_tvrz_zvencí()
	_kere_podel_pesin()
	_lesni_puda()
	_kvetiny_louky()
	_kvetiny_zahrad()
	_kere_kulate()
	_ves_cesty_volne()
	_rybnik_breh()
	_brody()
	_lom_cisti()
	_trziste_cisti()
	_cesty_kere()
	_ves_kompozice()
	# _byliny_rozsev()                 # byliny z vetve assets: zastaveno (radce 18:00), zapnout po vykonu
	# krok 9: predmety u zdi mimo cesty a pesiny (vybaveni domu se klade pri stavbe vsi, pred odvozenymi pesinami ke
	# dverim - test zasazeni: hranice dreva na pesine domu 4)
	_vybaveni_mimo_cest()
	# krok 10: usazeni vseho z 6-9 (jeden pruchod, radce 20:05 bod 1), volne pesiny a most, kmeny a kolize naposled
	if not _na_zem_arg.is_empty():
		_na_zem(_na_zem_arg[0], _na_zem_arg[1])
	# odstup od cest a vyska podle profilu cesty pred usazenim paprskem (po nem se profil, ktery uz je v povrchu,
	# pricital podruhe - trsy a kere 0,7-1,1 m nad zemi u hlavni cesty (5, 600), test zasazeni visi_*)
	_cesty_rostliny()
	_na_povrch(parent)
	_mekke_mimo_kvadry()
	_pesiny_volne()
	_most_bez_stromu()
	_stromy_mimo_balvany()
	_cesty_kameny()
	_kmeny()
	# zakladni modely pred vzdalenymi verzemi: vzdalene LOD pak sdili materialy (a textury) zakladniho modelu
	var klice: Array = data["rostliny"].keys()
	klice.sort_custom(func(x: String, y: String) -> bool: return int(x.contains("_daleko")) < int(y.contains("_daleko")))
	var mat_zaklad := {}                 # druh -> {jmeno materialu: Material}
	var imp := {}                        # druh impostoru -> {bunka 256 m: [Color(pata xyz, meritko+otoceni)]}
	for key: String in klice:
		var kind := key.substr(0, key.rfind("_"))
		if not scenes.has(kind):
			var path := MOD + "rostliny/%s.glb" % kind
			if not ResourceLoader.exists(path):
				scenes[kind] = null
			else:
				scenes[kind] = (load(path) as PackedScene).instantiate()
		var inst: Node = scenes[kind]
		if inst == null:
			continue
		var mesh: Mesh = null
		for n in inst.find_children("*", "MeshInstance3D", true, false):
			if String(n.name) == key:
				mesh = (n as MeshInstance3D).mesh
		if mesh == null:
			continue
		if kind.contains("_daleko"):
			# LOD1/LOD2: stejne materialy jako plny model (jinak 3 kopie stejnych textur v graficke pameti)
			var zk: String = kind.left(kind.find("_daleko"))
			if mat_zaklad.has(zk):
				mesh = mesh.duplicate()
				for i in mesh.get_surface_count():
					var om := mesh.surface_get_material(i)
					var nm2 := om.resource_name if om else ""
					if (mat_zaklad[zk] as Dictionary).has(nm2):
						mesh.surface_set_material(i, mat_zaklad[zk][nm2])
		elif not mat_zaklad.has(kind):
			var md := {}
			for i in mesh.get_surface_count():
				var om := mesh.surface_get_material(i)
				if om:
					md[om.resource_name] = om
					# listi s pruhlednosti/predpruchodem (briza, smrk): ve stinu se kreslilo jako plny cerny tvar
					# (stinovy pruchod netestuje alfu) - alfa nuzky jako u dubu a lipy
					if om is BaseMaterial3D and (om as BaseMaterial3D).transparency in [BaseMaterial3D.TRANSPARENCY_ALPHA, BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS]:
						(om as BaseMaterial3D).transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
						(om as BaseMaterial3D).alpha_scissor_threshold = 0.5
			# briza: kura svitila (Misa 0.60) - albedo kury o tretinu tmavsi, do sedobila
			if kind.begins_with("briza"):
				for nm_: String in md.keys():
					var km: Material = md[nm_]
					if km is BaseMaterial3D and (km as BaseMaterial3D).transparency == BaseMaterial3D.TRANSPARENCY_DISABLED:
						(km as BaseMaterial3D).albedo_color = (km as BaseMaterial3D).albedo_color * Color(0.62, 0.62, 0.6)
			# listi stromu: vlastni shader s vetrem a normalami od stredu koruny (0.61, Misa: placacky, zadny pohyb)
			if _strom_tvar(kind) != "" or kind.begins_with("bez_") or kind.begins_with("shrub") or kind.begins_with("vrba") \
					or kind.begins_with("ker_husty"):
				var bb := mesh.get_aabb()
				for nm_: String in md.keys():
					var lm: Material = md[nm_]
					if lm is BaseMaterial3D and (lm as BaseMaterial3D).transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR \
							and (lm as BaseMaterial3D).albedo_texture:
						md[nm_] = _listi_shader(lm as BaseMaterial3D, bb, _strom_tvar(kind) != "")
						# Misa 0.63 (tablet): duby a brizy moc zlute, smrky skoro cerne - odstin listi podle druhu
						# (prumerna barva listu z textur: dub 124/120/50 = zlutoolivova, smrk 59/67/57 = sedocerna)
						for pf: String in TINT_LISTI:
							if kind.begins_with(pf):
								var ti: Color = (md[nm_] as ShaderMaterial).get_shader_parameter("tint")
								(md[nm_] as ShaderMaterial).set_shader_parameter("tint", ti * (TINT_LISTI[pf] as Color).linear_to_srgb())   # tint je source_color (sRGB)
				for i in mesh.get_surface_count():
					var om3 := mesh.surface_get_material(i)
					if om3 and md.has(om3.resource_name) and md[om3.resource_name] is ShaderMaterial:
						mesh.surface_set_material(i, md[om3.resource_name])
			if kind.begins_with("skala_") and not kind.contains("_daleko2"):
				for nm_: String in md.keys():
					var om_: Material = md[nm_]
					if om_ is BaseMaterial3D and nm_.begins_with("skala") and (om_ as BaseMaterial3D).albedo_texture:
						md[nm_] = _skala_detail(om_ as BaseMaterial3D)
				for i in mesh.get_surface_count():
					var om2 := mesh.surface_get_material(i)
					if om2 and md.has(om2.resource_name):
						mesh.surface_set_material(i, md[om2.resource_name])
			mat_zaklad[kind] = md
		if kind == "briza":
			mesh = _briza_kmen(mesh)
		# radce 20:30 (ves: kvety 1,9 M troj.): byliny a kere z fotoskenu maji 1-9 tisic troj. na kus (kopriva 8 080,
		# shrub_02 9 234) - pri nacteni zjednodusit na LOD0 <= 300 (kere 600): meshoptimizer (SurfaceTool.generate_lod)
		if not kind.contains("_daleko"):
			for pf: String in ZJEDNODUSIT:
				if kind.begins_with(pf):
					mesh = _zjednodus(mesh, int(ZJEDNODUSIT[pf]))
		if kind == "divoka_trava":
			mesh = mesh.duplicate()
			for i in mesh.get_surface_count():
				var nm := mesh.surface_get_material(i).resource_name if mesh.surface_get_material(i) else ""
				mesh.surface_set_material(i, material(nm) if nm != "" else grass_mat)
		if kind == "divoka_trava" or kind == "grass_medium_01" or kind == "grass_medium_02" or kind.begins_with("dandelion"):
			continue                      # pampeliska: listova ruzice naplocho = "hvezdice" na cestach (radce 07:15 B)                      # travu dela louka (louka.gd); tyto trsy ji jen zdvojovaly (3,6 M troj. u tvrze)
		var low := NIZKE.has(kind) or PODROST.has(kind)
		var daleko := kind.ends_with("_daleko")
		if daleko and not kind.begins_with("skala_"):
			continue
		var tvar := _strom_tvar(kind)
		# K3: za plnym stromem impostor (pohled z atlasu); jednoduchy tvar jen kdyz impostor pro druh chybi
		var imp_druh := _imp_druh(kind) if tvar != "" else ""
		var tvar_mesh: Mesh = _tvar_mesh(tvar, mesh.get_aabb(), _listi(mesh)) if tvar != "" and imp_druh == "" else null
		var imp_s := mesh.get_aabb().size.y / float(_imp_meta[imp_druh]["vyska"]) if imp_druh != "" else 1.0
		var ma_lod: bool = data["rostliny"].has(kind + "_daleko_0")
		var mid := STREDNI.has(kind)
		var keep := keep_low if low else (keep_tree if not mid else 1.0)
		var cells := {}
		# Misa 0.66/0.67 pad: 48 200 MultiMeshInstance3D (druh x bunka 24 m) = cast z 1,5 GB RAM. Druhy viditelne
		# dal nez ~60 m (kameny, balvany, skaly, vzdalene LOD) po 48 m - 4x mene uzlu; kratky dosah (byliny, puda,
		# stromy s impostorem) zustava 24 m, jinak by bunka se stredem za koncem dosahu schovala blizke kusy
		var bk := BUNKA if (low or mid or imp_druh != "" or tvar_mesh != null) else BUNKA * 2.0
		var k := 0
		var vys_druhu := Vector2.ZERO
		for pf: String in VYSKA_BYLIN:
			if kind.begins_with(pf):
				vys_druhu = VYSKA_BYLIN[pf]
		for t: Array in data["rostliny"][key]:
			k += 1
			if keep < 1.0 and fmod(k * 0.6180339, 1.0) > keep:
				continue
			var xf := Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])),
					Vector3(t[3], t[7], t[11]))
			# skutecna vyska byliny (Misa 0.64: "koprivy velke jak clovek" - export z Blenderu mel meritka 1-70x podle
			# podsite, kopriva 1,5-3 m): vyska v metrech z tabulky, uvnitr rozsahu podle polohy
			if vys_druhu.y > 0.0:
				var hm := mesh.get_aabb().size.y * xf.basis.get_scale().y
				if hm > 0.01:
					var hc := lerpf(vys_druhu.x, vys_druhu.y, fposmod(sin(t[3] * 12.9898 + t[11] * 78.233) * 43758.5453, 1.0))
					xf.basis = xf.basis.scaled(Vector3.ONE * (hc / hm))
			# mech u skal byl v exportu zvetseny 25-50x (vyska 0.6-1.6 m misto cm): plachty 30 m ve vzduchu
			if kind.begins_with("mech_") or kind.begins_with("moss_") or kind.begins_with("rock_moss"):
				var sc := xf.basis.get_scale().x
				if sc > 2.0:
					xf.basis = xf.basis.scaled(Vector3.ONE * (randf_range(0.8, 1.6) / sc))
				# Misa 0.65 "mech ve vzduchu nebo pod nim dira": placka mechu (0,8-1,6 m) lezela vodorovne - na svahu
				# jedna strana visela, druha v zemi. Sklopit podle normaly terenu (rozdil vysek +-0,5 m) a 3 cm do zeme
				var ox := xf.origin.x
				var oz := xf.origin.z
				var vy := _vyska(ox, oz)
				var nt := Vector3(_vyska(ox - 0.5, oz) - _vyska(ox + 0.5, oz), 1.0, _vyska(ox, oz - 0.5) - _vyska(ox, oz + 0.5)).normalized()
				if absf(xf.origin.y - vy) < 0.3:             # na zemi (ne na skale nebo zdi)
					if nt.y < 0.999:
						xf.basis = Basis(Quaternion(Vector3.UP, nt)) * xf.basis
					xf.origin.y = minf(xf.origin.y, vy) - 0.03
			if (low or mid) and not smi_tu_byt(xf.origin.x, xf.origin.z, kind):
				continue
			var c := Vector2i(floori(xf.origin.x / bk), floori(xf.origin.z / bk))
			if not cells.has(c):
				cells[c] = []
			cells[c].append(xf)
		for c: Vector2i in cells:
			var list: Array = cells[c]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = mesh
			mm.instance_count = list.size()
			for i in list.size():
				mm.set_instance_transform(i, list[i])
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.name = "%s_%d_%d" % [key, c.x, c.y]
			if SBER.has(kind):
				for i in list.size():
					sber_spots.append({"id": SBER[kind], "mmi": mmi, "i": i, "xf": list[i]})
			# ROZPOCET (1500 kresleni, 2 M troj.): skaly LOD0 do 40 m (jen ta vrha stin), LOD1 40-120 m, LOD2 dal;
			# stromy plne do 60 m (stin), dal jednoduchy tvar bez stinu; ostatni vegetace stiny nevrha vubec
			var stin_ok := quality > 0
			var off := GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var on := GeometryInstance3D.SHADOW_CASTING_SETTING_ON if stin_ok else off
			mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
			mmi.cast_shadow = off
			if key.begins_with("kamen_"):
				mmi.lod_bias = float(pasma()["skala"]["kamen_lod_bias"])
			if imp_druh != "":
				mmi.visibility_range_end = STROM_PREP
				mmi.visibility_range_end_margin = 10.0
				mmi.cast_shadow = on
				for xf: Transform3D in list:
					var bc := Vector2i(floori(xf.origin.x / IMP_BUNKA), floori(xf.origin.z / IMP_BUNKA))
					if not imp.has(imp_druh):
						imp[imp_druh] = {}
					if not imp[imp_druh].has(bc):
						imp[imp_druh][bc] = []
					var yaw := fposmod(atan2(-xf.basis.x.z, xf.basis.x.x), TAU)
					var sc := xf.basis.get_scale().y * imp_s
					imp[imp_druh][bc].append(Color(xf.origin.x, xf.origin.y, xf.origin.z, roundf(sc * 256.0) + yaw / TAU * 0.999))
			elif tvar_mesh:
				mmi.visibility_range_end = STROM_PREP
				mmi.visibility_range_end_margin = 10.0
				mmi.cast_shadow = on
				var mm2 := MultiMesh.new()
				mm2.transform_format = MultiMesh.TRANSFORM_3D
				mm2.mesh = tvar_mesh
				mm2.instance_count = list.size()
				for i in list.size():
					mm2.set_instance_transform(i, list[i])
				var far := MultiMeshInstance3D.new()
				far.multimesh = mm2
				far.name = mmi.name + "_tvar"
				far.visibility_range_begin = STROM_PREP - 5.0
				far.visibility_range_begin_margin = 10.0
				far.visibility_range_end = STROM_DOHLED
				far.visibility_range_end_margin = 15.0
				far.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
				far.cast_shadow = off
				root.add_child(far)
			elif kind.begins_with("skala_"):
				if kind.ends_with("_daleko2"):
					mmi.visibility_range_begin = SKALA_LOD1
					mmi.visibility_range_end = 500.0
					mmi.visibility_range_end_margin = 40.0
				elif daleko:
					mmi.visibility_range_begin = SKALA_LOD0
					mmi.visibility_range_end = SKALA_LOD1
					mmi.visibility_range_end_margin = 10.0
				else:
					mmi.visibility_range_end = SKALA_LOD0
					mmi.visibility_range_end_margin = 5.0
					mmi.cast_shadow = on
			elif daleko:
				mmi.visibility_range_begin = LOD_M
				mmi.visibility_range_end = [300.0, 450.0, 650.0][quality]
			elif ma_lod:
				mmi.visibility_range_end = LOD_M
			elif low:
				mmi.visibility_range_end = [18.0, 25.0, 40.0][quality]       # louka (drn + trsy) pokryva dal
				mmi.visibility_range_end_margin = 6.0
			elif mid:
				mmi.visibility_range_end = [50.0, 70.0, 95.0][quality]
				mmi.visibility_range_end_margin = 10.0
				# radce 18:45 (0.64 FPS venku): lesni puda (kere, mlade jehlicnany, vetve, parezy) na tabletu jen do 40 m
				# - kostelik: puda 0,91 M; kameny, rakos a kmeny zustavaji (vyrazne v krajine)
				var puda := false
				for pf: String in ["shrub", "sipek", "bez_cerny", "ker_husty", "ker_kulaty", "fir_sapling", "pine_sapling", "dry_branches", "tree_stump", "root_cluster", "rock_moss"]:
					if kind.begins_with(pf):
						puda = true
				if puda and (OS.has_feature("mobile") or OS.has_environment("TVRZ_MOBIL")):
					mmi.visibility_range_end = 40.0
					mmi.visibility_range_end_margin = 6.0
			elif kind.begins_with("balvan_") or kind.begins_with("kamen_"):
				# 0.60: balvany 1-2 m a kameny se kreslily do 450 m (prikop: 84 kresleni, 3 plochy na kus) - dal jsou pixel
				var bal := kind.begins_with("balvan_")
				mmi.visibility_range_end = ([100.0, 140.0, 200.0] if bal else [60.0, 90.0, 120.0])[quality]
				mmi.visibility_range_end_margin = 15.0
			else:
				mmi.visibility_range_end = [300.0, 450.0, 650.0][quality]
				mmi.visibility_range_end_margin = 40.0
			# kratky dosah: po postaveni (dosednuti) jen data, uzly v okoli hrace (rostliny_rozdel / rostliny_okoli)
			if mmi.visibility_range_end <= 100.0 and mmi.visibility_range_begin <= 0.0 and not SBER.has(kind) \
					and imp_druh == "" and tvar_mesh == null and not kind.begins_with("skala_"):
				mmi.set_meta("tok", true)
			root.add_child(mmi)
	_impostory(root, imp)
	_obzor_les.call_deferred(root.get_parent() if root.get_parent() else root)
	for kind: String in scenes:
		if scenes[kind]:
			(scenes[kind] as Node).free()


## Pevne predmety z katalogu (bozi muka na krizovatce): model z modely/predmety, kolize kvadrem.
var _stavby: Array = []                # [stred xz, polomer] staticke stavby (zricenina, stan, hostinec) - pesiny je obchazeji


func _static_items(parent: Node3D) -> void:
	var katalog: Dictionary = {}
	var fk := FileAccess.open(MOD + "predmety.json", FileAccess.READ)
	if fk:
		katalog = JSON.parse_string(fk.get_as_text())
	for it: Dictionary in data.get("staticke", []):
		var id := String(it["id"])
		var ps: PackedScene = load(MOD + "predmety/" + id + ".glb")
		if ps == null:
			continue
		var n := Node3D.new()
		n.name = "Staticky_" + id
		var a: Array = it["p"]
		n.position = Vector3(a[0], a[1], a[2])
		n.rotation.y = float(it.get("yaw", 0.0))
		parent.add_child(n)
		n.add_child(ps.instantiate())
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var ab := (mi as MeshInstance3D).global_transform * (mi as MeshInstance3D).get_aabb()
			if ab.size.y > 0.5 and maxf(ab.size.x, ab.size.z) > 0.6:
				_stavby.append([Vector2(ab.get_center().x, ab.get_center().z), maxf(ab.size.x, ab.size.z) * 0.5 + 1.2])
		# modely od Misi (nove._import_sketchup): materialy pojmenovane podle hernich -> stejne fotky jako stavby
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var msh := (mi as MeshInstance3D).mesh
			for i in msh.get_surface_count():
				var om := msh.surface_get_material(i)
				if om and data["materialy"].has(om.resource_name.split(".")[0]):
					(mi as MeshInstance3D).set_surface_override_material(i, material(om.resource_name))
		if it.has("boxy"):
			# stavba s jednoduchymi kolizemi (stan: stoly, sudy, platno; provazy a koliky bez kolize)
			var sb := StaticBody3D.new()
			for q: Array in it["boxy"]:
				var c := CollisionShape3D.new()
				var bx := BoxShape3D.new()
				bx.size = Vector3(q[3], q[4], q[5])
				c.shape = bx
				c.position = Vector3(q[0], q[1], q[2])
				sb.add_child(c)
			n.add_child(sb)
			continue
		if String(it.get("kolize", "")) == "trimesh":
			# stavba (hostinec, stan): presna kolize ze site, dovnitr se da vejit
			# model z importu (hostinec): kolize jen z puvodni site <id>_kolize, ta se nekresli
			var vse := n.find_children("*", "MeshInstance3D", true, false)
			var kol := vse.filter(func(m: Node) -> bool: return String(m.name).ends_with("_kolize"))
			for mi in vse:
				if kol.is_empty() or mi in kol:
					_trimesh(mi as MeshInstance3D)
				if mi in kol:
					(mi as MeshInstance3D).visible = false
				else:
					(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
			continue
		var r: Array = katalog.get(id, {}).get("rozmer", [1.0, 1.0, 1.0])
		var b := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = Vector3(float(r[0]) * 0.7, float(r[1]), float(r[2]) * 0.7)
		cs.shape = bs
		cs.position.y = float(r[1]) * 0.5
		b.add_child(cs)
		n.add_child(b)


## Usek [od, do] s animace jako samostatny klip se smyckou (model s jednou dlouhou animaci, kone od Misy 28. 10.).
static func klip_z_useku(src: Animation, od: float, do_: float) -> Animation:
	var a := Animation.new()
	a.length = do_ - od
	a.loop_mode = Animation.LOOP_LINEAR
	for ti in src.get_track_count():
		var typ := src.track_get_type(ti)
		var ni := a.add_track(typ)
		a.track_set_path(ni, src.track_get_path(ti))
		a.track_set_interpolation_type(ni, src.track_get_interpolation_type(ti))
		for kt: float in [od, do_]:
			pass
		# klic na zacatku a konci useku (interpolovana hodnota) + vsechny klice mezi
		var casy: Array = [od]
		for i in src.track_get_key_count(ti):
			var t := src.track_get_key_time(ti, i)
			if t > od and t < do_:
				casy.append(t)
		casy.append(do_)
		for t: float in casy:
			var v: Variant
			match typ:
				Animation.TYPE_POSITION_3D:
					v = src.position_track_interpolate(ti, t)
				Animation.TYPE_ROTATION_3D:
					v = src.rotation_track_interpolate(ti, t)
				Animation.TYPE_SCALE_3D:
					v = src.scale_track_interpolate(ti, t)
				_:
					v = src.value_track_interpolate(ti, t) if typ == Animation.TYPE_VALUE else null
			if v != null:
				a.track_insert_key(ni, t - od, v)
	return a
