extends SceneTree
## Mereni klipu s nastrojem (Misa 12. 11. „porad spatne“, 3. rozbor priciny): drzi-li obe ruce jednu nasadu (klip nahrany
## s nastrojem), je smer od prave ruky k leve v soustave kosti prave ruky v celem klipu stejny a vzdalenost stala.
## Vystup: NASADA <klip> smer (prumer) rozptyl st, vzdalenost min..max - mala odchylka = pevny uchop (soket) v ruce.
## Spusteni: tools/beh.sh nasada cmd godot --headless --path . -s res://tools/mereni_nasady.gd

const Lide := preload("res://scripts/lide.gd")


func _initialize() -> void:
	_beh.call_deferred()


func _beh() -> void:
	var koren := Node3D.new()
	root.add_child(koren)
	var lide: Node3D = Lide.new()
	koren.add_child(lide)
	var c: Dictionary = lide.nova_postava((Lide.P["obyvatele"] as Array)[0])
	var sk: Skeleton3D = c["kostra"]
	var ap: AnimationPlayer = c["ap"]
	for jm: String in ["TreeChopping_Loop", "Kovar_Swing_Loop", "Prace_Uder_Loop", "Prace_Kovar_Loop", "Kope_Loop"]:
		if not ap.has_animation(jm):
			print("NASADA %s chybi" % jm)
			continue
		var dl := ap.get_animation(jm).length
		var smery: Array = []
		var vz: Array = []
		var hr := sk.find_bone("hand_r")
		var hl := sk.find_bone("hand_l")
		for i in 32:
			ap.play(jm, 0.0)
			ap.seek(dl * i / 32.0, true)
			ap.advance(0.0)
			var gr := sk.get_bone_global_pose(hr)
			var gl := sk.get_bone_global_pose(hl)
			var v := gr.basis.orthonormalized().inverse() * (gl.origin - gr.origin)
			smery.append(v.normalized())
			vz.append(v.length())
		var pr := Vector3.ZERO
		for s: Vector3 in smery:
			pr += s
		pr = pr.normalized()
		var nej := 0.0
		for s: Vector3 in smery:
			nej = maxf(nej, rad_to_deg(s.angle_to(pr)))
		vz.sort()
		print("NASADA %-20s delka %.2f s, smer k leve ruce v soustave prave %s, odchylka az %.0f st, vzdalenost %.3f..%.3f m" % [jm, dl, pr.snapped(Vector3.ONE * 0.01), nej, vz[0], vz[vz.size() - 1]])
	quit(0)
