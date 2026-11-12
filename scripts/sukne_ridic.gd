extends SkeletonModifier3D
## Kosti sukne podle tvaru nohou (12. 11., Misa: sukne vsede trci dopredu, ma kopirovat ohnuti kolen; rešerše
## docs/rozpracovane/sukne_sed_reserse.md - CRYENGINE PRow projekce na kapsle nohou, aim kosti na body z kapsli; podil
## rotace stehna sukni trha). Pro kazdy retez sukne_<i>_*: draha od korene retezu na koleno odsunute o polomer stehna
## (latka lezi na stehne; predni stredove retezy na stred mezi koleny - prekleni mezeru mezi nohama), od kolena podel
## holene ke kotniku odsunutemu o polomer holene a dal k zemi. Klouby retezu se rozlozi po draze podle delek kosti,
## kazda kost miri na dalsi kloub. Vaha retezu: predni obe nohy, bocni blizsi noha, zadni nic (visi); celek se prolne
## s pozou z animace podle ohnuti stehen (sed naplno, chuze skoro vubec - sukne nesmi obtahovat nohy jako kalhoty).
## Data postavy.json sukne (polomer_stehna_m, polomer_holene_m, tloustka_m, ohyb_od_st, ohyb_do_st, ridic_predek, ridic_bok).

var D: Dictionary = {}
var _retezy: Array = []          # [kosti, vaha leve, vaha prave, delky]
var _b := {}
var _diag := 0
var _pel_y0 := 0.0


func priprav(sk: Skeleton3D) -> void:
	for n: String in ["pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r"]:
		_b[n] = sk.find_bone(n)
	var pel := sk.get_bone_global_rest(_b["pelvis"]).origin
	_pel_y0 = pel.y
	var lx := signf(sk.get_bone_global_rest(_b["thigh_l"]).origin.x - pel.x)
	var i := 0
	while sk.find_bone("sukne_%d_0" % i) >= 0:
		var kosti: Array = []
		var j := 0
		while sk.find_bone("sukne_%d_%d" % [i, j]) >= 0:
			kosti.append(sk.find_bone("sukne_%d_%d" % [i, j]))
			j += 1
		var delky: Array = []
		for k in kosti.size() - 1:
			delky.append(sk.get_bone_global_rest(kosti[k]).origin.distance_to(sk.get_bone_global_rest(kosti[k + 1]).origin))
		delky.append(delky[delky.size() - 1] if not delky.is_empty() else 0.3)
		var d := sk.get_bone_global_rest(kosti[0]).origin - pel
		d.y = 0.0
		d = d.normalized()
		var predek := maxf(0.0, d.z) * float(D.get("ridic_predek", 1.0))         # postava hledi po +z
		var bok_l := maxf(0.0, d.x * lx) * float(D.get("ridic_bok", 0.6))
		var bok_r := maxf(0.0, -d.x * lx) * float(D.get("ridic_bok", 0.6))
		_retezy.append([kosti, clampf(predek * 0.5 + bok_l, 0.0, 1.0), clampf(predek * 0.5 + bok_r, 0.0, 1.0), delky])
		i += 1
	if OS.has_environment("TVRZ_SUKNE_DIAG"):
		print("SUKNE_RIDIC retezu %d, vahy %s" % [_retezy.size(), str(_retezy.map(func(r: Array) -> String: return "%.2f/%.2f" % [r[1], r[2]]))])


## Bod na lomene care (pole bodu) ve vzdalenosti s od zacatku.
static func _na_draze(dr: Array, s: float) -> Vector3:
	for k in dr.size() - 1:
		var a: Vector3 = dr[k]
		var b: Vector3 = dr[k + 1]
		var l := a.distance_to(b)
		if s <= l or k == dr.size() - 2:
			return a + (b - a).normalized() * s if l > 1e-5 else a
		s -= l
	return dr[dr.size() - 1]


## Odsunuti bodu p od osy useku a-b o polomer r (ve smeru od osy k bodu ref).
static func _od_osy(a: Vector3, b: Vector3, p: Vector3, ref: Vector3, r: float) -> Vector3:
	var ax := (b - a).normalized()
	var v := ref - a
	var n := v - ax * v.dot(ax)
	if n.length_squared() < 1e-8:
		n = Vector3.UP.cross(ax)
	return p + n.normalized() * r


func _process_modification() -> void:
	var sk := get_skeleton()
	if sk == null or _retezy.is_empty() or int(_b["calf_l"]) < 0:
		return
	var r_s := float(D.get("polomer_stehna_m", 0.075))
	var r_h := float(D.get("polomer_holene_m", 0.05))
	var tl := float(D.get("tloustka_m", 0.01))
	var nahoru := Vector3.UP
	var P := {}
	for n: String in _b:
		P[n] = sk.get_bone_global_pose(int(_b[n])).origin
	# ohnuti stehen (uhel stehna od svisle dolu): prolnuti s pozou animace
	var ohyb := 0.0
	for s: String in ["l", "r"]:
		var t: Vector3 = (P["calf_" + s] as Vector3) - (P["thigh_" + s] as Vector3)
		ohyb = maxf(ohyb, rad_to_deg(t.angle_to(-nahoru)))
	var w_ohyb := smoothstep(float(D.get("ohyb_od_st", 25.0)), float(D.get("ohyb_do_st", 65.0)), ohyb)
	# 12. 11. test_sukne Kleci_Loop: pri kleku stehno svisle (ohyb ~0), latka ve stehne - vaha i podle poklesu panve
	var pokles := _pel_y0 - (P["pelvis"] as Vector3).y
	w_ohyb = maxf(w_ohyb, smoothstep(float(D.get("pokles_od_m", 0.12)), float(D.get("pokles_do_m", 0.3)), pokles))
	if _diag < 2 and OS.has_environment("TVRZ_SUKNE_DIAG"):
		_diag += 1
		print("SUKNE_RIDIC ohyb stehen %.0f st, pokles panve %.2f m, vaha %.2f" % [ohyb, pokles, w_ohyb])
	if w_ohyb <= 0.001:
		return
	for r: Array in _retezy:
		var kosti: Array = r[0]
		var wl := float(r[1])
		var wr := float(r[2])
		var w := clampf(wl + wr, 0.0, 1.0) * w_ohyb
		if w <= 0.001:
			continue
		var koren := sk.get_bone_global_pose(kosti[0]).origin
		var drahy: Array = []
		# smer odsunu od nohy: ven od panve na strane retezu a nahoru (vsede latka na stehne, pri kleku pred stehnem)
		var ven0 := koren - (P["pelvis"] as Vector3)
		ven0.y = 0.0
		var ref := koren + (ven0.normalized() + nahoru) * 0.3
		for s: String in ["l", "r"]:
			var th: Vector3 = P["thigh_" + s]
			var kn: Vector3 = P["calf_" + s]
			var an: Vector3 = P["foot_" + s]
			var k_ := _od_osy(th, kn, kn, ref, r_s + tl)
			# od kolena latka pada svisle (tize); holen ji jen odtlacuje (kapsle PRow), kdyz je kotnik pred svislici -
			# 12. 11. kucharka vsede: nohy zastrcene pod lavici, lem po holeni sel dozadu skrz prkno lavice
			var a_ := _od_osy(kn, an, an, k_, r_h + tl)
			var svisle := Vector3(k_.x, a_.y, k_.z)
			var ven := k_ - koren
			ven.y = 0.0
			if ven.length_squared() > 1e-8 and (a_ - svisle).dot(ven.normalized()) < 0.0:
				a_ = svisle
			# po stehne (12. 11. test_sukne: primka pas-koleno rizla stehno 2-5 cm od osy): body na tretinach stehna
			var s1 := _od_osy(th, kn, th.lerp(kn, 0.33), ref, r_s + tl)
			var s2 := _od_osy(th, kn, th.lerp(kn, 0.66), ref, r_s + tl)
			drahy.append([koren, s1, s2, k_, a_, a_ - nahoru * 0.3])
		var ws := wl + wr
		var dr: Array = []
		for q in (drahy[0] as Array).size():
			dr.append(((drahy[0][q] as Vector3) * wl + (drahy[1][q] as Vector3) * wr) / maxf(ws, 1e-5))
		var cile: Array = [koren]
		var s_ := 0.0
		var delky: Array = r[3]
		for k in kosti.size():
			s_ += float(delky[k])
			cile.append(_na_draze(dr, s_))
		# vytlaceni z kapsli obou nohou (CRYENGINE PRow; 12. 11. test_sukne: zkrizene nohy a klek - prumer drah
		# dvou nohou padl do druhe nohy)
		for k in range(1, cile.size()):
			var c: Vector3 = cile[k]
			for s: String in ["l", "r"]:
				for kap: Array in [[P["thigh_" + s], P["calf_" + s], r_s + tl], [P["calf_" + s], P["foot_" + s], r_h + tl]]:
					var a: Vector3 = kap[0]
					var ab: Vector3 = (kap[1] as Vector3) - a
					var t := clampf((c - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
					var q := a + ab * t
					var d := c.distance_to(q)
					var rr := float(kap[2])
					if d < rr:
						var n := (c - q) / d if d > 1e-5 else ref - q
						c = q + n.normalized() * rr
			cile[k] = c
		for k in kosti.size():
			var b: int = kosti[k]
			var g := sk.get_bone_global_pose(b)
			var smer := (cile[k + 1] as Vector3) - g.origin
			if smer.length_squared() < 1e-8:
				continue
			var y0 := g.basis.y.normalized()
			var q := Quaternion(y0, y0.slerp(smer.normalized(), w).normalized())
			var cil := Basis(q) * g.basis
			var p := sk.get_bone_parent(b)
			var gp := sk.get_bone_global_pose(p) if p >= 0 else Transform3D()
			sk.set_bone_pose_rotation(b, (gp.basis.inverse() * cil).get_rotation_quaternion().normalized())
