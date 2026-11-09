extends SceneTree
## Test drzeni (Misa 0.99993 r. 47: „postavy drzi veci v rukou spatne“ - kopi vodorovne pri chuzi, vedro a kosik ve
## vzduchu, krumpac jednou rukou). Bez sveta, headless, sekundy: postava z dat (lide.gd nova_postava, ruce jako ve hre),
## pro kazdou cinnost s predmetem v rukou (postavy.json cinnosti.*.v_rukou) kazdy jeji klip, chuze a reakce (predmet
## v ruce zustava) ve trech casech klipu. Kontroly podle drzeni.<id>.rezim (scripts/uchop.gd):
##  visi   - osa predmetu nahoru od svisle nejvys test_drzeni.visi_st, bod uchopu u zapesti;
##  svisle - osa svet_rot_st (kopi: hrot) od chtene nejvys test_drzeni.svisle_st;
##  druha_ruka - zapesti druhe ruky od bodu na predmetu nejvys test_drzeni.druha_ruka_m.
## Spusteni: tools/beh.sh drzeni cmd godot --headless --path . -s res://tools/test_drzeni.gd
## Vystup: DRZENI ... radky, TEST DRZENI OK/CHYBA.

const Lide := preload("res://scripts/lide.gd")
var chyb := 0
var zkous := 0


func _initialize() -> void:
	_beh.call_deferred()


func _beh() -> void:
	var koren := Node3D.new()
	root.add_child(koren)
	var lide: Node3D = Lide.new()
	koren.add_child(lide)
	var P: Dictionary = Lide.P
	var T: Dictionary = P["drzeni"]["_test"]
	var o: Dictionary = (P["obyvatele"] as Array)[0]
	var c: Dictionary = lide.nova_postava(o)
	var u: Node3D = c["uzel"]
	u.rotation.y = 0.7                      # postava natocena (svet_rot_st je v soustave postavy)
	var kostra: Skeleton3D = c["kostra"]
	var ap: AnimationPlayer = c["ap"]
	var reakce: Array = []
	for r: Dictionary in P["reakce"]:
		if String(r.get("klip", "")) != "" and not reakce.has(String(r["klip"])):
			reakce.append(String(r["klip"]))
	for cid: String in P["cinnosti"]:
		var cn: Dictionary = P["cinnosti"][cid]
		if not cn.has("v_rukou"):
			continue
		var klipy: Array = (cn.get("klipy", []) as Array).duplicate()
		if cn.has("chuze"):
			klipy.append(String(cn["chuze"]))
		klipy.append("Walk_Loop")
		for jm: String in klipy:
			if not ap.has_animation(jm):
				continue
			var vr: Dictionary = cn["v_rukou"]
			var spec: Dictionary = vr.get(jm, vr.get("*", {}))
			if spec.is_empty():
				continue
			c["cn"] = cn
			c["klip"] = ""
			lide.call("ruce", c, {})
			lide.call("_klip", c, jm, 1.0)
			var seznam := [jm]
			for rk: String in reakce:                 # reakce nechava predmet v ruce
				if ap.has_animation(rk):
					seznam.append(rk)
			for kl: String in seznam:
				var dl := ap.get_animation(kl).length
				for f: float in [0.2, 0.55, 0.9]:
					ap.stop()
					ap.play(kl, 0.0)
					ap.seek(dl * f, true)
					ap.advance(0.0)
					await process_frame
					await process_frame
					_kontrola(c, kostra, spec, "%s %s %.2f" % [cid, kl, f], T, P)
	print("TEST DRZENI: %d chyb z %d" % [chyb, zkous])
	print("TEST DRZENI %s" % ("OK" if chyb == 0 else "CHYBA"))
	quit(1 if chyb > 0 else 0)


func _kontrola(c: Dictionary, kostra: Skeleton3D, spec: Dictionary, co: String, T: Dictionary, P: Dictionary) -> void:
	var drzi: Dictionary = c["ruce"]
	var smer := (c["uzel"] as Node3D).global_basis.orthonormalized()
	for ruka: String in spec:
		var id := String(spec[ruka])
		var d: Dictionary = P["drzeni"].get(id, {})
		var uz: Node3D = drzi.get(ruka + "_uzel")
		if uz == null:
			continue
		zkous += 1
		var g := uz.global_transform
		var rez := String(d.get("rezim", ""))
		var zp := kostra.global_transform * kostra.get_bone_global_pose(kostra.find_bone("hand_" + ruka)).origin
		if rez != "":
			var sr: Array = d.get("svet_rot_st", [0.0, 0.0, 0.0])
			var chteno := smer * Basis.from_euler(Vector3(deg_to_rad(float(sr[0])), deg_to_rad(float(sr[1])), deg_to_rad(float(sr[2]))))
			var osa := chteno.y if rez == "visi" else chteno.x
			var je := (g.basis.y if rez == "visi" else g.basis.x).normalized()
			var uhel := rad_to_deg(je.angle_to(osa.normalized()))
			var mez := float(T["visi_st"] if rez == "visi" else T["svisle_st"])
			var od := g.origin.distance_to(zp)
			print("DRZENI %-40s %s %s odchylka %.1f st, uchop od zapesti %.3f m" % [co, id, rez, uhel, od])
			if uhel > mez:
				chyb += 1
				print("DRZENI CHYBA %s %s: osa %.1f st (mez %.0f)" % [co, id, uhel, mez])
		var dr: Array = d.get("druha_ruka", [])
		if dr.size() == 3:
			var uc: Array = d.get("uchop", [0.0, 0.0, 0.0])
			var bod := g * (Vector3(float(dr[0]), float(dr[1]), float(dr[2])) - Vector3(float(uc[0]), float(uc[1]), float(uc[2])))
			var druha := "l" if ruka == "r" else "r"
			var z2 := kostra.global_transform * kostra.get_bone_global_pose(kostra.find_bone("hand_" + druha)).origin
			var dd := z2.distance_to(bod)
			print("DRZENI %-40s %s druha ruka od topurka %.3f m" % [co, id, dd])
			if dd > float(T["druha_ruka_m"]):
				chyb += 1
				print("DRZENI CHYBA %s %s: druha ruka %.3f m od predmetu" % [co, id, dd])
