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
			var obouruc := false                      # obourucni nastroj: lide._reakce klip reakce nehraje
			for rr: String in spec:
				if (P["drzeni"].get(String(spec[rr]), {}) as Dictionary).has("druha_ruka"):
					obouruc = true
			# 11. 11.: s predmetem v ruce se reakce nehraje (lide._reakce) - netestuje se
			for kl: String in seznam:
				var dl := ap.get_animation(kl).length
				for f: float in [0.2, 0.55, 0.9]:
					ap.stop()
					ap.play(kl, 0.0)
					ap.seek(dl * f, true)
					ap.advance(0.0)
					for sx: String in ["l", "r"]:                  # ruce s upravenou pozou (viz _kontrola)
						if kostra.get_node_or_null("test_ruka_" + sx) == null:
							var bt := BoneAttachment3D.new()
							bt.name = "test_ruka_" + sx
							bt.bone_name = "hand_" + sx
							kostra.add_child(bt)
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
		if (d.get("klipy_bez_rezimu", []) as Array).has(co.split(" ")[1]):
			rez = ""                                  # pri piti naklon z klipu (uchop.gd klip_ted)
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
		# 11. 11. (Misa: kladivo svira jen v prstech): vzdalenost osy nasady (y predmetu pres jeho pocatek) od dutiny
		# pesti = stred prostrednich clanku prstu (index/middle/ring/pinky _02) - z BoneAttachment (poza po modifikatorech)
		if bool(d.get("nasada", false)) or id == "korbel":
			var st := Vector3.ZERO
			for pn: String in ["index_02", "middle_02", "ring_02", "pinky_02"]:
				var bx: BoneAttachment3D = kostra.get_node_or_null("test_" + pn + "_" + ruka)
				if bx == null:
					bx = BoneAttachment3D.new()
					bx.name = "test_" + pn + "_" + ruka
					bx.bone_name = pn + "_" + ruka
					kostra.add_child(bx)
				st += bx.global_position
			st /= 4.0
			var ax := g.basis.y.normalized()
			var od_osy := ((st - g.origin) - ax * (st - g.origin).dot(ax)).length()
			print("DRZENI %-40s %s pest od osy nasady %.3f m" % [co, id, od_osy])
		# 11. 11. (Misa: uchopy porad spatne; kost ruky v Godotu: osa y podel kosti = k prstum, ne x): osa nasady
		# (y predmetu) proti osam ruky - nasada ma vest napric dlani (kolmo na prsty, |uhel k y ruky - 90| <= nasada_st)
		var ba0: BoneAttachment3D = kostra.get_node_or_null("test_ruka_" + ruka)
		if ba0 != null and rez == "":
			var hb := ba0.global_basis.orthonormalized()
			var ny := g.basis.y.normalized()
			var u_y := rad_to_deg(ny.angle_to(hb.y))
			print("DRZENI %-40s %s nasada k prstum %.0f st, k x %.0f st, k z %.0f st" % [co, id, u_y, rad_to_deg(ny.angle_to(hb.x)), rad_to_deg(ny.angle_to(hb.z))])
			if bool(d.get("nasada", false)) and absf(u_y - 90.0) > float(T.get("nasada_st", 25.0)):
				chyb += 1
				print("DRZENI CHYBA %s %s: nasada %.0f st k prstum (ma byt 90 +-%s)" % [co, id, u_y, str(T.get("nasada_st", 25.0))])
		var dr: Array = d.get("druha_ruka", [])
		if dr.size() == 3:
			var uc: Array = d.get("uchop", [0.0, 0.0, 0.0])
			var bod := g * (Vector3(float(dr[0]), float(dr[1]), float(dr[2])) - Vector3(float(uc[0]), float(uc[1]), float(uc[2])))
			var druha := "l" if ruka == "r" else "r"
			# 10. 11.: poza kosti po modifikatorech (uchop.gd IK) plati jen pri vykresleni - Godot 4.4 ji po
			# skeleton_updated vrati na pozu animace; get_bone_global_pose v testu cetl ruku bez IK (0,25-0,34 m
			# „od topurka“, IK_DIAG ve stejnem behu 0,000 m). Ruka se cte pres BoneAttachment3D (nese upravenou pozu).
			var ba2: BoneAttachment3D = kostra.get_node_or_null("test_ruka_" + druha)
			if ba2 == null:
				ba2 = BoneAttachment3D.new()
				ba2.name = "test_ruka_" + druha
				ba2.bone_name = "hand_" + druha
				kostra.add_child(ba2)
			var z2 := ba2.global_position
			var dd := z2.distance_to(bod)
			print("DRZENI %-40s %s druha ruka od topurka %.3f m" % [co, id, dd])
			if dd > float(T["druha_ruka_m"]):
				chyb += 1
				print("DRZENI CHYBA %s %s: druha ruka %.3f m od predmetu" % [co, id, dd])
