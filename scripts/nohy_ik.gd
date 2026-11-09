extends SkeletonModifier3D
## Chodidla na zemi (Misa 9. 11. „animace postav v KCD kvalite“): klipy UAL jsou na rovine - na svahu, schodech
## a prahu jedna noha visela ve vzduchu nebo byla v zemi. Po animaci (SkeletonModifier3D) paprsek pod kazdym
## chodidlem: noha se posune o rozdil zeme pod chodidlem proti zemi pod postavou (koren), zvednuti chodidla z klipu
## (krok) zustava; panev klesne o nizsi z obou (aby dosahla noha do dolu), dvoukloubova IK stehno - lytko,
## natoceni chodidla z klipu. Jen zblizka (lide.gd LOD: postavy.json nohy_ik.do_m), paprsky jen kazdy
## nohy_ik.paprsky_snimku snimek (vysledek drzi).
## Data: pravidla/svet/postavy.json nohy_ik.

var postava: Node3D
var D: Dictionary = {}
var _zeme := [0.0, 0.0]          # rozdil zeme pod chodidlem l/r proti korenu (m, svet)
var _panev := 0.0
var _snimek := 0


func _process_modification() -> void:
	var sk := get_skeleton()
	if sk == null or postava == null or D.is_empty():
		return
	var skg := sk.global_transform
	var koren_y := postava.global_position.y
	_snimek += 1
	var strany := ["l", "r"]
	if _snimek % maxi(1, int(D["paprsky_snimku"])) == 1 or int(D["paprsky_snimku"]) <= 1:
		var sp := sk.get_world_3d().direct_space_state
		for k in 2:
			var ifo := sk.find_bone("foot_" + strany[k])
			if ifo < 0:
				return
			var w := skg * sk.get_bone_global_pose(ifo).origin
			var q := PhysicsRayQueryParameters3D.create(Vector3(w.x, koren_y + float(D["nad_m"]), w.z), Vector3(w.x, koren_y - float(D["pod_m"]), w.z), int(D["maska"]))
			var h := sp.intersect_ray(q)
			var cil := clampf((h["position"] as Vector3).y - koren_y, -float(D["pod_m"]), float(D["nad_m"])) if not h.is_empty() else 0.0
			_zeme[k] = lerpf(float(_zeme[k]), cil, float(D["tlumeni"]))
	var pan := minf(minf(float(_zeme[0]), float(_zeme[1])), 0.0)
	pan = maxf(pan, -float(D["panev_max_m"]))
	_panev = lerpf(_panev, pan, float(D["tlumeni"]))
	if absf(_panev) < 0.002 and absf(float(_zeme[0])) < 0.002 and absf(float(_zeme[1])) < 0.002:
		return
	var ip := sk.find_bone("pelvis")
	if ip < 0:
		return
	var gp := sk.get_bone_global_pose(ip)
	# soustava kostry: svet nahoru -> osa kostry (kostra kitu muze byt otocena / meritko)
	var nahoru := (skg.basis.inverse() * Vector3.UP)
	sk.set_bone_global_pose(ip, Transform3D(gp.basis, gp.origin + nahoru * _panev))
	for k in 2:
		var it := sk.find_bone("thigh_" + strany[k])
		var ic := sk.find_bone("calf_" + strany[k])
		var ifo := sk.find_bone("foot_" + strany[k])
		if it < 0 or ic < 0 or ifo < 0:
			continue
		var f0 := sk.get_bone_global_pose(ifo)
		var cil := f0.origin + nahoru * (float(_zeme[k]) - _panev)
		_ik(sk, it, ic, ifo, cil)
		var f1 := sk.get_bone_global_pose(ifo)
		sk.set_bone_global_pose(ifo, Transform3D(f0.basis, f1.origin))     # natoceni chodidla z klipu


static func _ik(sk: Skeleton3D, iu: int, il: int, ih: int, t: Vector3) -> void:
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
		return
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
	var p := sk.get_bone_parent(i)
	var gp := sk.get_bone_global_pose(p) if p >= 0 else Transform3D()
	# mistni rotace z globalni (jako telo.gd _otoc_kost) - deti kosti se prepocitaji
	sk.set_bone_pose_rotation(i, (gp.basis.inverse() * (Basis(q) * g.basis)).get_rotation_quaternion().normalized())
