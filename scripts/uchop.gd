extends SkeletonModifier3D
## Uchop predmetu podle dat, ne podle jednoho klipu (Misa 0.99993 r. 47: „postavy drzi veci v rukou spatne“ - kopi
## vodorovne, vedro a kosik ve vzduchu, krumpac jednou rukou). Drive byl predmet pevne v soustave kosti ruky
## (postavy.json drzeni.<id>.rot_st, odladene v jednom klipu) - v kazdem jinem klipu (chuze, slozene ruce reakce,
## kleceni) mel jine natoceni. Ted po animaci (SkeletonModifier3D, pred BoneAttachment3D):
##  - "visi" (vedro, lucerna, kosik): predmet visi z bodu uchopu svisle dolu (tize), ruka zustava z klipu;
##  - "svisle" (kopi): ruka se natoci tak, aby predmet mel v soustave postavy natoceni svet_rot_st (kopi hrotem nahoru),
##    jako ruka hrace s louci (telo.gd) - ruka vede predmet, predmet je v ni vzdy stejne;
##  - "druha_ruka" [x, y, z] (krumpac, sekera): druha ruka IK na bod predmetu (topurko) - obourucni nastroj.
## Data: pravidla/svet/postavy.json drzeni.<id> (rezim, svet_rot_st, druha_ruka). lide.gd ruce() nastavi polozky.

var polozky := {}          # "r"/"l" -> {"id", "d": data drzeni, "uzel": Node3D drzi_<id>}
var postava: Node3D        # koren postavy (smer postavy pro svet_rot_st)


static func _eul(a: Array) -> Basis:
	return Basis.from_euler(Vector3(deg_to_rad(float(a[0])), deg_to_rad(float(a[1])), deg_to_rad(float(a[2]))))


func nastav(ruka: String, id: String, d: Dictionary, uzel: Node3D) -> void:
	if id == "" or uzel == null:
		polozky.erase(ruka)
	else:
		polozky[ruka] = {"id": id, "d": d, "uzel": uzel}
	active = not polozky.is_empty()


func _process_modification() -> void:
	var sk := get_skeleton()
	if sk == null or postava == null:
		return
	var skg := sk.global_transform
	var skb := skg.basis.orthonormalized()
	var smer := postava.global_basis.orthonormalized()
	for ruka: String in polozky:
		var p: Dictionary = polozky[ruka]
		var d: Dictionary = p["d"]
		var uz: Node3D = p["uzel"]
		if not is_instance_valid(uz):
			continue
		var ih := sk.find_bone("hand_" + ruka)
		if ih < 0:
			continue
		var rez := String(d.get("rezim", ""))
		var sc := uz.basis.get_scale()
		if rez == "svisle":
			# ruka = chtene natoceni predmetu * uchop^-1 (v soustave kostry), poloha zapesti z klipu
			var chteno := smer * _eul(d.get("svet_rot_st", [0.0, 0.0, 0.0]))
			var ruka_sk := skb.inverse() * chteno * _eul(d.get("rot_st", [0.0, 0.0, 0.0])).inverse()
			var g := sk.get_bone_global_pose(ih)
			sk.set_bone_global_pose(ih, Transform3D(ruka_sk.orthonormalized(), g.origin))
		elif rez == "visi":
			# predmet visi z bodu uchopu (pocatek uzlu drzi_ = uchop): natoceni v soustave kosti ruky = ruka^-1 * svisle
			var hw := (skb * sk.get_bone_global_pose(ih).basis).orthonormalized()
			var chteno := smer * _eul(d.get("svet_rot_st", [0.0, 0.0, 0.0]))
			uz.basis = (hw.inverse() * chteno).orthonormalized().scaled(sc)
		var dr: Array = d.get("druha_ruka", [])
		if dr.size() == 3:
			# bod predmetu (souradnice predmetu) -> soustava kostry: zapesti * drzi_ (natoceni, meritko) * (bod - uchop)
			var uc: Array = d.get("uchop", [0.0, 0.0, 0.0])
			var bod := Vector3(float(dr[0]), float(dr[1]), float(dr[2])) - Vector3(float(uc[0]), float(uc[1]), float(uc[2]))
			var hg := sk.get_bone_global_pose(ih)
			var cil := hg * (Basis(uz.basis.get_rotation_quaternion()) * bod * sc.x * 1.0)
			_ik(sk, "l" if ruka == "r" else "r", cil)


## Dvoukloubova IK v soustave kostry: rameno a loket tak, aby zapesti bylo v cili; rovina lokte z klipu.
static func _ik(sk: Skeleton3D, sx: String, t: Vector3) -> void:
	var iu := sk.find_bone("upperarm_" + sx)
	var il := sk.find_bone("lowerarm_" + sx)
	var ih := sk.find_bone("hand_" + sx)
	if iu < 0 or il < 0 or ih < 0:
		return
	var A := sk.get_bone_global_pose(iu).origin
	var B := sk.get_bone_global_pose(il).origin
	var C := sk.get_bone_global_pose(ih).origin
	var la := A.distance_to(B)
	var lb := B.distance_to(C)
	var at := t - A
	if at.length_squared() < 1e-8:
		return
	var d := clampf(at.length(), absf(la - lb) + 1e-3, la + lb - 1e-3)
	var smer := at.normalized()
	var pol := (B - A) - smer * (B - A).dot(smer)
	if pol.length_squared() < 1e-8:
		pol = Vector3.DOWN - smer * Vector3.DOWN.dot(smer)
	pol = pol.normalized()
	var cos_a := clampf((la * la + d * d - lb * lb) / (2.0 * la * d), -1.0, 1.0)
	var B2 := A + smer * la * cos_a + pol * la * sqrt(1.0 - cos_a * cos_a)
	_otoc(sk, iu, B - A, B2 - A)
	var B3 := sk.get_bone_global_pose(il).origin
	var C3 := sk.get_bone_global_pose(ih).origin
	_otoc(sk, il, C3 - B3, A + smer * d - B3)


static func _otoc(sk: Skeleton3D, i: int, a: Vector3, b: Vector3) -> void:
	if a.length_squared() < 1e-10 or b.length_squared() < 1e-10:
		return
	var q := Quaternion(a.normalized(), b.normalized())
	var g := sk.get_bone_global_pose(i)
	sk.set_bone_global_pose(i, Transform3D(Basis(q) * g.basis, g.origin))
