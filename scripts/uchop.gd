extends SkeletonModifier3D
## Uchop predmetu podle dat, ne podle jednoho klipu (Misa 0.99993 r. 47: „postavy drzi veci v rukou spatne“ - kopi
## vodorovne, vedro a kosik ve vzduchu, krumpac jednou rukou). Drive byl predmet pevne v soustave kosti ruky
## (postavy.json drzeni.<id>.rot_st, odladene v jednom klipu) - v kazdem jinem klipu (chuze, slozene ruce reakce,
## kleceni) mel jine natoceni. Ted po animaci (SkeletonModifier3D, pred BoneAttachment3D):
##  - "visi" (vedro, lucerna, kosik): predmet visi z bodu uchopu svisle dolu (tize), ruka zustava z klipu;
##  - "svisle" (kopi): ruka se natoci tak, aby predmet mel v soustave postavy natoceni svet_rot_st (kopi hrotem nahoru),
##    jako ruka hrace s louci (telo.gd) - ruka vede predmet, predmet je v ni vzdy stejne;
##  - "druha_ruka" [x, y, z] (krumpac, sekera): druha ruka IK na bod predmetu (topurko) - obourucni nastroj;
##  - kazdy predmet: prsty sevrene (prsty_st, vychozi drzeni._prsty_st) - ne otevrena dlan pod nasadou (r. 83).
## Data: pravidla/svet/postavy.json drzeni.<id> (rezim, svet_rot_st, druha_ruka). lide.gd ruce() nastavi polozky.

var polozky := {}          # "r"/"l" -> {"id", "d": data drzeni, "uzel": Node3D drzi_<id>}
var postava: Node3D        # koren postavy (smer postavy pro svet_rot_st)
var blizko := true
var prsty_st := 50.0       # vychozi sevreni prstu (postavy.json drzeni._prsty_st)
const PRSTY := ["index_01", "index_02", "index_03", "middle_01", "middle_02", "middle_03", "ring_01", "ring_02", "ring_03",
		"pinky_01", "pinky_02", "pinky_03"]


static func _eul(a: Array) -> Basis:
	return Basis.from_euler(Vector3(deg_to_rad(float(a[0])), deg_to_rad(float(a[1])), deg_to_rad(float(a[2]))))


func nastav(ruka: String, id: String, d: Dictionary, uzel: Node3D) -> void:
	if id == "" or uzel == null:
		polozky.erase(ruka)
	else:
		polozky[ruka] = {"id": id, "d": d, "uzel": uzel}
	active = blizko and not polozky.is_empty()


## LOD (lide.gd): uchop jen do postavy.json anim_do_m - dal predmet zustane v poze klipu (neni videt), modifikator nestoji cas.
func zapni(b: bool) -> void:
	blizko = b
	var a := b and not polozky.is_empty()
	if active != a:
		active = a


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
		# prsty sevrene kolem predmetu (Misa r. 83: kovar drzel kladivo otevrenou dlani) - kazdy predmet v ruce
		var ps := deg_to_rad(float(d.get("prsty_st", prsty_st)))
		if ps != 0.0:
			for pn: String in PRSTY:
				var ip := sk.find_bone(pn + "_" + ruka)
				if ip >= 0:
					sk.set_bone_pose_rotation(ip, sk.get_bone_pose_rotation(ip) * Quaternion(Vector3.RIGHT, ps))
		var dr: Array = d.get("druha_ruka", [])
		if dr.size() == 3:
			var uc: Array = d.get("uchop", [0.0, 0.0, 0.0])
			var bod := Vector3(float(dr[0]), float(dr[1]), float(dr[2])) - Vector3(float(uc[0]), float(uc[1]), float(uc[2]))
			var hg := sk.get_bone_global_pose(ih)
			var druha := "l" if ruka == "r" else "r"
			var ih2 := sk.find_bone("hand_" + druha)
			# Obourucni nastroj (test_drzeni 9. 11.: druha ruka 0,28-0,43 m od topurka i v klipu, kde ruce drzi 0,2 m od
			# sebe): natoceni nastroje z natoceni zapesti mocapu (CMU nema otaceni dlani) melo nasadu nazad a hlavu nahoru
			# pri uderu. Nasada se natoci podle pazi (osa y predmetu od stredu ramen ke stredu rukou - paze a nasada jsou
			# pri uderu jedna paka), ostri (drzeni.ostri_osa, vychozi x) v rovine svihu kolmo k nasade na stranu uderu
			# (nasada x vpravo postavy). Druha ruka pak IK na bod nasady (drzeni.druha_ruka).
			if ih2 >= 0:
				# smer nasady = prodlouzeni pazi: od stredu ramen ke stredu rukou (ruce v mocapu drzi vedle sebe, ne
				# nad sebou - cara mezi rukama by nasadu polozila napric pred telo; snimek fdrz3/kovar2)
				var h2 := sk.get_bone_global_pose(ih2).origin
				var iu1 := sk.find_bone("upperarm_" + ruka)
				var iu2 := sk.find_bone("upperarm_" + druha)
				var osa_y := Vector3.ZERO
				if iu1 >= 0 and iu2 >= 0:
					osa_y = (hg.origin + h2) * 0.5 - (sk.get_bone_global_pose(iu1).origin + sk.get_bone_global_pose(iu2).origin) * 0.5
				if osa_y.length_squared() > 1e-8:
					osa_y = osa_y.normalized()
					var vpravo := -(skb.inverse() * smer.x).normalized()      # postava hledi po +z, vpravo = -x
					var ostri := osa_y.cross(vpravo)
					if ostri.length_squared() < 1e-6:
						ostri = osa_y.cross(skb.inverse() * smer.z)
					ostri = ostri.normalized()
					var bok := ostri.cross(osa_y).normalized()
					var chteno_sk: Basis
					if String(d.get("ostri_osa", "x")) == "z":
						chteno_sk = Basis(-bok, osa_y, ostri)
					else:
						chteno_sk = Basis(ostri, osa_y, bok)
					uz.basis = (hg.basis.orthonormalized().inverse() * chteno_sk).orthonormalized().scaled(sc)
			var cil := hg * (Basis(uz.basis.get_rotation_quaternion()) * bod * sc.x * 1.0)
			_ik(sk, druha, cil)


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
	if OS.has_environment("TVRZ_IK_DIAG"):
		print("IK_DIAG %s cil %s ruka pred %s po %s (od cile %.3f -> %.3f), paze %.3f+%.3f, rameno-cil %.3f" % [sx, t, C, sk.get_bone_global_pose(ih).origin, C.distance_to(t), sk.get_bone_global_pose(ih).origin.distance_to(t), la, lb, at.length()])


static func _otoc(sk: Skeleton3D, i: int, a: Vector3, b: Vector3) -> void:
	if a.length_squared() < 1e-10 or b.length_squared() < 1e-10:
		return
	var q := Quaternion(a.normalized(), b.normalized())
	var g := sk.get_bone_global_pose(i)
	var p := sk.get_bone_parent(i)
	var gp := sk.get_bone_global_pose(p) if p >= 0 else Transform3D()
	# mistni rotace z globalni (jako telo.gd _otoc_kost) - deti kosti se prepocitaji
	sk.set_bone_pose_rotation(i, (gp.basis.inverse() * (Basis(q) * g.basis)).get_rotation_quaternion().normalized())
