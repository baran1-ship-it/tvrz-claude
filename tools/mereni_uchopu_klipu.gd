extends SceneTree
## Surovy klip (bez uchop.gd): pro kazdou fazi spojnice dlani (bod uchopu _dlan_m v kazde ruce, leva zrcadlene),
## kam miri palce (osa z kosti ruky) a dlane (-x prava, +x leva) vuci spojnici. Zjisti, jak herec drzel zbran.
## Spusteni: tools/beh.sh uk cmd godot --headless --path . -s res://tools/mereni_uchopu_klipu.gd

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
	var dl: Array = Lide.P["drzeni"]["_dlan_m"]
	var sc := sk.global_basis.get_scale().x
	var dr := Vector3(float(dl[0]), float(dl[1]), float(dl[2])) / sc
	var dlv := Vector3(-dr.x, dr.y, dr.z)
	for jm: String in ["Uder_Mec_Mx"]:
		var t := ap.get_animation(jm).length
		for i in 9:
			ap.play(jm, 0.0)
			ap.seek(t * i / 8.0, true)
			ap.advance(0.0)
			var gr := sk.get_bone_global_pose(sk.find_bone("hand_r"))
			var gl := sk.get_bone_global_pose(sk.find_bone("hand_l"))
			var pr := gr.origin + gr.basis * dr
			var pl := gl.origin + gl.basis * dlv
			var s := (pl - pr).normalized()
			var up := (sk.global_basis.orthonormalized().inverse() * Vector3.UP).normalized()
			print("UK %.2f s: dlane od sebe %.3f m, spojnice P->L nahoru %.2f | palec P k L %.2f, palec L k L-smeru %.2f | dlan P k L %.2f, dlan L k P %.2f | ruka L vys nez P %.3f" % [
				t * i / 8.0, pr.distance_to(pl) * sc, s.dot(up), gr.basis.orthonormalized().z.dot(s), gl.basis.orthonormalized().z.dot(s),
				(-gr.basis.orthonormalized().x).dot((pl - pr).normalized()), (gl.basis.orthonormalized().x).dot((pr - pl).normalized()), (pl - pr).dot(up) * sc])
	quit(0)
