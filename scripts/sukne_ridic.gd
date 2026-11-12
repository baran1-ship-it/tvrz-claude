extends SkeletonModifier3D
## Kosti sukne rizene stehny (12. 11., Misa: sukne a zastera trci s nohou, pri sedu tuhy plat pres kolena;
## rešerše docs/rozpracovane/obleceni_reserse.md - „knee-driven skirt bones“): kazdy retez sukne_<i>_* natoci koren
## podilem otoceni stehen proti klidove poze - predni retezy podle obou stehen, bocni podle blizsiho, zadni volne.
## Vsede predni cast sukne lezi na stehnech a od kolen pada dolu; pri chuzi se sukne pohne s nohou jen castecne.
## Pruzna simulace (SpringBoneSimulator3D „sukne“) bezi az po nem a pridava jen houpani. Data postavy.json sukne.ridic_*.

var D: Dictionary = {}
var _retezy: Array = []          # [kost korene, vaha leve, vaha prave]
var _tl := -1
var _tr := -1
var _cl := -1                    # lytka (calf) - 12. 11. Misa: sukne ma kopirovat ohnuti kolen, ne trcet dopredu
var _cr := -1
var _diag := 0


func priprav(sk: Skeleton3D) -> void:
	_tl = sk.find_bone("thigh_l")
	_tr = sk.find_bone("thigh_r")
	_cl = sk.find_bone("calf_l")
	_cr = sk.find_bone("calf_r")
	var pel := sk.get_bone_global_rest(sk.find_bone("pelvis")).origin
	var lx := signf(sk.get_bone_global_rest(_tl).origin.x - pel.x)
	var i := 0
	while sk.find_bone("sukne_%d_0" % i) >= 0:
		var b := sk.find_bone("sukne_%d_0" % i)
		var d := sk.get_bone_global_rest(b).origin - pel
		d.y = 0.0
		d = d.normalized()
		var predek := maxf(0.0, d.z) * float(D.get("ridic_predek", 0.8))       # postava hledi po +z
		var bok_l := maxf(0.0, d.x * lx) * float(D.get("ridic_bok", 0.6))
		var bok_r := maxf(0.0, -d.x * lx) * float(D.get("ridic_bok", 0.6))
		var kosti: Array = []
		var j := 0
		while sk.find_bone("sukne_%d_%d" % [i, j]) >= 0:
			kosti.append(sk.find_bone("sukne_%d_%d" % [i, j]))
			j += 1
		_retezy.append([kosti, clampf(predek * 0.5 + bok_l, 0.0, 1.0), clampf(predek * 0.5 + bok_r, 0.0, 1.0)])
		i += 1
	if OS.has_environment("TVRZ_SUKNE_DIAG"):
		print("SUKNE_RIDIC retezu %d, stehna %d %d, vahy %s" % [_retezy.size(), _tl, _tr, str(_retezy.map(func(r: Array) -> String: return "%.2f/%.2f" % [r[1], r[2]]))])


func _process_modification() -> void:
	var sk := get_skeleton()
	if sk == null or _tl < 0 or _tr < 0 or _retezy.is_empty():
		return
	# otoceni stehna proti klidu v soustave kostry
	var ql := (sk.get_bone_global_pose(_tl).basis * sk.get_bone_global_rest(_tl).basis.inverse()).get_rotation_quaternion()
	var qr := (sk.get_bone_global_pose(_tr).basis * sk.get_bone_global_rest(_tr).basis.inverse()).get_rotation_quaternion()
	# podil otoceni panve se odecte (sukne visi z panve, ridi jen pohyb stehen proti panvi)
	var ip := sk.find_bone("pelvis")
	var qp := (sk.get_bone_global_pose(ip).basis * sk.get_bone_global_rest(ip).basis.inverse()).get_rotation_quaternion()
	ql = qp.inverse() * ql
	qr = qp.inverse() * qr
	if _diag < 3 and OS.has_environment("TVRZ_SUKNE_DIAG"):
		_diag += 1
		print("SUKNE_RIDIC bezi, stehno L %.0f st, P %.0f st" % [rad_to_deg(ql.get_angle()), rad_to_deg(qr.get_angle())])
	# lytka proti panvi (vcetne ohnuti v koleni): kosti retezu pod kolenem jdou podle lytka
	var cl := qp.inverse() * (sk.get_bone_global_pose(_cl).basis * sk.get_bone_global_rest(_cl).basis.inverse()).get_rotation_quaternion() if _cl >= 0 else ql
	var cr := qp.inverse() * (sk.get_bone_global_pose(_cr).basis * sk.get_bone_global_rest(_cr).basis.inverse()).get_rotation_quaternion() if _cr >= 0 else qr
	var pod: Array = D.get("ridic_lytko", [0.0, 0.5, 1.0])       # podil lytka po kostech retezu (shora dolu)
	for r: Array in _retezy:
		var kosti: Array = r[0]
		var wl := float(r[1])
		var wr := float(r[2])
		var g0: Array = []
		for b: int in kosti:
			g0.append(sk.get_bone_global_pose(b))           # poza z animace (pred upravou)
		for jj in kosti.size():
			var b: int = kosti[jj]
			var f := float(pod[mini(jj, pod.size() - 1)])
			var dl := ql.slerp(cl, f)
			var dr := qr.slerp(cr, f)
			var q := Quaternion.IDENTITY.slerp(dl, wl) * Quaternion.IDENTITY.slerp(dr, wr)
			var cil := Basis(qp) * Basis(q) * Basis(qp.inverse()) * (g0[jj] as Transform3D).basis
			var p := sk.get_bone_parent(b)
			var gp := sk.get_bone_global_pose(p) if p >= 0 else Transform3D()
			sk.set_bone_pose_rotation(b, (gp.basis.inverse() * cil).get_rotation_quaternion().normalized())
