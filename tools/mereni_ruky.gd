extends SceneTree
## Mereni natoceni dlane (Misa 11. 11. „uchopy kladivo, krumpac, kybl, srp jsou porad spatne“; rešerše reports/Živé
## postavy jako v KCD.md: podezreni - anim_cmu.py prenasi rotace kosti nejkratsim obloukem, natoceni dlane kolem
## predlokti (twist) muze byt libovolne). Pro kazdy klip ve 5 casech: uhel natoceni hand_r (a hand_l) vuci lowerarm
## kolem osy predlokti (osa y kosti „dlani dolu“ promitnuta do roviny kolmo k predlokti). Rozsah prirozene ruky
## (pronace/supinace) je asi -90..+90 st. od klidove pozy; klipy UAL (puvodni) jsou vzor.
## Spusteni: tools/beh.sh ruka cmd godot --headless --path . -s res://tools/mereni_ruky.gd
## Vystup: RUKA <klip> <ruka> min/prum/max st.

const Lide := preload("res://scripts/lide.gd")


func _initialize() -> void:
	_beh.call_deferred()


func _twist(sk: Skeleton3D, ruka: String) -> float:
	var la := sk.find_bone("lowerarm_" + ruka)
	var ha := sk.find_bone("hand_" + ruka)
	var gl := sk.get_bone_global_pose(la)
	var gh := sk.get_bone_global_pose(ha)
	var osa := (gh.origin - gl.origin).normalized()
	var a := gl.basis.x - osa * gl.basis.x.dot(osa)
	var b := gh.basis.x - osa * gh.basis.x.dot(osa)
	if a.length() < 1e-4 or b.length() < 1e-4:
		return 0.0
	return rad_to_deg(a.normalized().signed_angle_to(b.normalized(), osa))


func _beh() -> void:
	var koren := Node3D.new()
	root.add_child(koren)
	var lide: Node3D = Lide.new()
	koren.add_child(lide)
	var P: Dictionary = Lide.P
	var c: Dictionary = lide.nova_postava((P["obyvatele"] as Array)[0])
	var sk: Skeleton3D = c["kostra"]
	var ap: AnimationPlayer = c["ap"]
	var hb := sk.find_bone("hand_r")
	print("RUKA kosti hand_r %d lowerarm_r %d, uzel ve strome %s, kostra %s" % [hb, sk.find_bone("lowerarm_r"), (c["uzel"] as Node).is_inside_tree(), sk.get_path()])
	if not (c["uzel"] as Node).is_inside_tree():
		koren.add_child(c["uzel"])
	var klipy: Array = ["Idle_Loop", "Walk_Loop", "Interact", "Sword_Idle", "Sword_Attack", "TreeChopping_Loop", "PickUp_Table",
		"Prace_Kovar_Buseni_Loop", "Kovar_Silny", "Prace_Uder_Loop", "Prace_Kovar_Loop", "Napiti", "Sed_Piti_Loop", "Nese_Stoji_Loop",
		"Chuze_Mix1_Loop", "Stani_Loop", "Farm_Watering", "Farm_Harvest", "Hleda_Loop", "Opreny_Loop", "Kope_Loop"]
	for jm: String in klipy:
		if not ap.has_animation(jm):
			print("RUKA %-26s chybi" % jm)
			continue
		var dl := ap.get_animation(jm).length
		for ruka: String in ["r", "l"]:
			var v: Array = []
			for f: float in [0.0, 0.25, 0.5, 0.75, 0.95]:
				ap.play(jm, 0.0)
				ap.seek(dl * f, true)
				ap.advance(0.0)
				await process_frame
				await process_frame
				sk.force_update_all_bone_transforms()
				v.append(_twist(sk, ruka))
				if ruka == "r" and f == 0.5:
					print("RUKA dbg %s ruka %s loket %s bazeY %s" % [jm, sk.get_bone_global_pose(sk.find_bone("hand_r")).origin.snapped(Vector3.ONE * 0.01), sk.get_bone_global_pose(sk.find_bone("lowerarm_r")).origin.snapped(Vector3.ONE * 0.01), sk.get_bone_global_pose(sk.find_bone("hand_r")).basis.y.snapped(Vector3.ONE * 0.01)])
			v.sort()
			var s := 0.0
			for x: float in v:
				s += x
			print("RUKA %-26s %s  min %7.1f  prum %7.1f  max %7.1f" % [jm, ruka, v[0], s / v.size(), v[v.size() - 1]])
	quit(0)
