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
var _ruce := false
var _svih := {}
var _klid_osa := {}


func priprav(sk: Skeleton3D) -> void:
	for n: String in ["pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r", "middle_01_l", "middle_01_r"]:
		_b[n] = sk.find_bone(n)
	# 13. 11. (kontrola pred vydanim): chybi-li povinna kost, ridic se vypne (jinak get_bone_global_pose(-1) kazdy snimek)
	for n: String in ["pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r"]:
		if int(_b[n]) < 0:
			active = false
			return
	_ruce = true
	for n: String in ["lowerarm_l", "lowerarm_r", "hand_l", "hand_r", "middle_01_l", "middle_01_r"]:
		if int(_b[n]) < 0:
			_ruce = false
	for s: String in ["l", "r"]:
		_klid_osa[s] = (sk.get_bone_global_rest(_b["calf_" + s]).origin - sk.get_bone_global_rest(_b["thigh_" + s]).origin).normalized()
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
		if int(_b[n]) >= 0:
			P[n] = sk.get_bone_global_pose(int(_b[n])).origin
	# svih stehen proti klidove poze (jen natoceni osy stehna, bez zkrutu)
	for s: String in ["l", "r"]:
		var t1: Vector3 = (P["calf_" + s] as Vector3) - (P["thigh_" + s] as Vector3)
		_svih[s] = Quaternion(_klid_osa[s], t1.normalized()) if t1.length_squared() > 1e-8 else Quaternion.IDENTITY
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
	# 12. 11. (snimek kotle: pri stani noha od sebe prosla sukni) - vytlaceni z kapsli bezi vzdy, i pri vaze 0
	var vse: Array = []
	for r: Array in _retezy:
		var kosti: Array = r[0]
		var wl := float(r[1])
		var wr := float(r[2])
		var w := clampf(wl + wr, 0.0, 1.0) * w_ohyb
		var koren := sk.get_bone_global_pose(kosti[0]).origin
		var delky: Array = r[3]
		# klouby z animace (vc. konce posledni kosti) - zadni retezy (vaha 0) se jen vytlaci z nohou
		var anim: Array = []
		for k in kosti.size():
			anim.append(sk.get_bone_global_pose(kosti[k]).origin)
		var gl := sk.get_bone_global_pose(kosti[kosti.size() - 1])
		anim.append(gl.origin + gl.basis.y.normalized() * float(delky[delky.size() - 1]))
		# 13. 11. (Misa: noha vylezla z kabatce pri chuzi; rešerše docs/rozpracovane/obleceni_noha_reserse.md - QualiArts,
		# Kawaii Sync Bone, CRYENGINE): predni a bocni retezy jdou podilem svihu stehna (bez zkrutu) kolem kycle
		var pod := float(D.get("noha_podil", 0.45))
		if pod > 0.0 and (wl > 0.0 or wr > 0.0):
			for k in range(1, anim.size()):
				var p0: Vector3 = anim[k]
				var posun := Vector3.ZERO
				for s: String in ["l", "r"]:
					var ws := wl if s == "l" else wr
					if ws <= 0.0:
						continue
					var q: Quaternion = _svih[s]
					var hip: Vector3 = P["thigh_" + s]
					posun += ((hip + Quaternion.IDENTITY.slerp(q, clampf(pod * ws, 0.0, 1.0)) * (p0 - hip)) - p0)
				anim[k] = p0 + posun
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
			# od kolena svisle dolu do vysky kotniku; kdyz je holen vpredu, vytlaci latku krok kapsli nize
			var a_ := Vector3(k_.x, an.y, k_.z)
			# po stehne (12. 11. test_sukne: primka pas-koleno rizla stehno 2-5 cm od osy): body na tretinach stehna
			var s1 := _od_osy(th, kn, th.lerp(kn, 0.33), ref, r_s + tl)
			var s2 := _od_osy(th, kn, th.lerp(kn, 0.66), ref, r_s + tl)
			drahy.append([koren, s1, s2, k_, a_, a_ - nahoru * 0.3])
		var ws := maxf(wl + wr, 1e-5)
		var dr: Array = []
		for q in (drahy[0] as Array).size():
			dr.append(((drahy[0][q] as Vector3) * wl + (drahy[1][q] as Vector3) * wr) / ws)
		var cile: Array = [koren]
		var s_ := 0.0
		for k in kosti.size():
			s_ += float(delky[k])
			cile.append((anim[k + 1] as Vector3).lerp(_na_draze(dr, s_), w))
		vse.append([kosti, cile, ref, anim])
	# vyhlazeni po obvodu (12. 11., snimek kucharka Sed_Poza3: u zkrizenych nohou sousedni retezy kazdy k jine noze,
	# latka mezi nimi zkroucena - tmavy rub); retezy sukne_<i> jdou po obvodu dokola. Vyhlazuje se jen odchylka od animace:
	# prumer poloh sousedu kruh sukne smrstil (snimek kotle - noha pri stani skrz sukni)
	var n_r := vse.size()
	for _it in int(D.get("obvod_kol", 2)):
		var nove: Array = []
		for i in n_r:
			var ci: Array = (vse[i][1] as Array).duplicate()
			var cp: Array = vse[(i - 1 + n_r) % n_r][1]
			var cn: Array = vse[(i + 1) % n_r][1]
			var ai: Array = vse[i][3]
			var ap: Array = vse[(i - 1 + n_r) % n_r][3]
			var an_: Array = vse[(i + 1) % n_r][3]
			for k in range(1, ci.size()):
				if k < cp.size() and k < cn.size() and k < ai.size():
					var odch := (ci[k] as Vector3) - (ai[k] as Vector3)
					var sous := ((cp[k] as Vector3) - (ap[k] as Vector3) + (cn[k] as Vector3) - (an_[k] as Vector3)) * 0.5
					ci[k] = (ai[k] as Vector3) + odch.lerp(sous, float(D.get("obvod_podil", 0.35)))
			nove.append(ci)
		for i in n_r:
			vse[i][1] = nove[i]
	# vytlaceni z kapsli obou nohou (CRYENGINE PRow; 12. 11. test_sukne: zkrizene nohy a klek - prumer drah
	# dvou nohou padl do druhe nohy)
	var kapsle: Array = []
	# ruce (13. 11. Misa: vsede ruce zapadly do zastery) - latka pod dlani; nohy az po nich (vyhrava noha)
	for s: String in ["l", "r"]:
		if _ruce:
			kapsle.append([P["lowerarm_" + s], P["hand_" + s], float(D.get("polomer_predlokti_m", 0.035))])
			kapsle.append([P["hand_" + s], P["middle_01_" + s], float(D.get("polomer_dlane_m", 0.03))])
	for s: String in ["l", "r"]:
		kapsle.append([P["thigh_" + s], P["calf_" + s], r_s + tl])
		kapsle.append([P["calf_" + s], P["foot_" + s], r_h + tl])
	for v: Array in vse:
		var cile: Array = v[1]
		var ref: Vector3 = v[2]
		for k in range(1, cile.size()):
			var c: Vector3 = _ven_z_kapsli(cile[k], kapsle, ref)
			# latka mezi klouby je rovna tetiva: kdyz stred useku vezi v noze (chuze - stehno vpredu), kloub se odsune
			# o dvojnasobek hloubky (stred tetivy pak lezi na povrchu)
			var m: Vector3 = ((cile[k - 1] as Vector3) + c) * 0.5
			var m2 := _ven_z_kapsli(m, kapsle, ref)
			c += (m2 - m) * 2.0
			cile[k] = _ven_z_kapsli(c, kapsle, ref)
	# 13. 11. (snimek ch_s4 zepredu: stehno v kroku proslo latkou MEZI retezy, retezy samy venku): latka mezi sousednimi
	# retezy po obvodu je take tetiva - kdyz jeji stred lezi v noze, oba sousedni klouby se odsunou o hloubku stredu
	for _it in int(D.get("obvod_tetiva_kol", 2)):
		for i in n_r:
			var ca: Array = vse[i][1]
			var cb: Array = vse[(i + 1) % n_r][1]
			for k in range(1, mini(ca.size(), cb.size())):
				var m: Vector3 = ((ca[k] as Vector3) + (cb[k] as Vector3)) * 0.5
				var ven := _ven_z_kapsli(m, kapsle, ((vse[i][2] as Vector3) + (vse[(i + 1) % n_r][2] as Vector3)) * 0.5) - m
				if ven.length_squared() > 1e-8:
					ca[k] = (ca[k] as Vector3) + ven
					cb[k] = (cb[k] as Vector3) + ven
	for v: Array in vse:
		var kosti: Array = v[0]
		var cile: Array = v[1]
		for k in kosti.size():
			var b: int = kosti[k]
			var g := sk.get_bone_global_pose(b)
			var smer := (cile[k + 1] as Vector3) - g.origin
			if smer.length_squared() < 1e-8:
				continue
			var y0 := g.basis.y.normalized()
			var q := Quaternion(y0, smer.normalized())
			var cil := Basis(q) * g.basis
			var p := sk.get_bone_parent(b)
			var gp := sk.get_bone_global_pose(p) if p >= 0 else Transform3D()
			sk.set_bone_pose_rotation(b, (gp.basis.inverse() * cil).get_rotation_quaternion().normalized())


## Bod vytlaceny ze vsech kapsli [a, b, polomer] po kolmici k ose (CRYENGINE PRow projekce).
static func _ven_z_kapsli(c: Vector3, kapsle: Array, ref: Vector3) -> Vector3:
	for kap: Array in kapsle:
		var a: Vector3 = kap[0]
		var ab: Vector3 = (kap[1] as Vector3) - a
		var t := clampf((c - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
		var q := a + ab * t
		var d := c.distance_to(q)
		var rr := float(kap[2])
		if d < rr:
			var n := (c - q) / d if d > 1e-5 else ref - q
			c = q + n.normalized() * rr
	return c
