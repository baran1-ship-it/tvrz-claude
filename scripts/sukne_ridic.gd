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
var _diag := 0


func priprav(sk: Skeleton3D) -> void:
	_tl = sk.find_bone("thigh_l")
	_tr = sk.find_bone("thigh_r")
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
		_retezy.append([b, clampf(predek * 0.5 + bok_l, 0.0, 1.0), clampf(predek * 0.5 + bok_r, 0.0, 1.0)])
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
	for r: Array in _retezy:
		var b: int = r[0]
		var q := Quaternion.IDENTITY.slerp(ql, float(r[1])) * Quaternion.IDENTITY.slerp(qr, float(r[2]))
		var g := sk.get_bone_global_pose(b)
		var p := sk.get_bone_parent(b)
		var gp := sk.get_bone_global_pose(p) if p >= 0 else Transform3D()
		var cil := Basis(qp) * Basis(q) * Basis(qp.inverse()) * g.basis
		sk.set_bone_pose_rotation(b, (gp.basis.inverse() * cil).get_rotation_quaternion().normalized())
