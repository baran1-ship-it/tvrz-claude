extends SceneTree
## Test sukne vsede (Misa 12. 11.: „sukne ma kopirovat ohnuti kolen, trci dopredu“; snimek kucharka_s: lem sel po holeni
## dozadu pod lavici skrz prkno). Bez sveta, headless: kazdy model postavy s kostmi sukne_<i>_<j> (scripts/sukne_ridic.gd),
## kazda poza sedu z postavy.json sedani.pozy.klipy a sukne.test_klipy (klek). Kontroly (postavy.json sukne):
##  pod_kolenem - predni retezy (koren pred panvi) pod vyskou kolen nesmi byt za svislici od blizsiho kolena
##                (latka od kolena pada, holen ji jen odtlacuje) vic nez test_tolerance_m;
##  stehno      - zadny kloub sukne nesmi byt uvnitr stehna (polomer_stehna_m * test_stehno_podil od osy stehna).
## Kosti se ctou pres BoneAttachment3D (poza po modifikatorech; get_bone_global_pose v Godot 4.4 vraci pozu animace).
## Spusteni: tools/beh.sh sukne cmd godot --headless --path . -s res://tools/test_sukne.gd
## Vystup: SUKNE ... radky, TEST SUKNE OK/CHYBA.

const Lide := preload("res://scripts/lide.gd")
var chyb := 0


func _initialize() -> void:
	_beh.call_deferred()


func _kost(kostra: Skeleton3D, jm: String) -> Vector3:
	var bx: BoneAttachment3D = kostra.get_node_or_null("test_" + jm)
	if bx == null:
		bx = BoneAttachment3D.new()
		bx.name = "test_" + jm
		bx.bone_name = jm
		kostra.add_child(bx)
	return bx.global_position


func _beh() -> void:
	var koren := Node3D.new()
	root.add_child(koren)
	var lide: Node3D = Lide.new()
	koren.add_child(lide)
	var P: Dictionary = Lide.P
	var S: Dictionary = P["sukne"]
	var tol := float(S.get("test_tolerance_m", 0.03))
	var r_s := float(S.get("polomer_stehna_m", 0.09)) * float(S.get("test_stehno_podil", 0.7))
	var klipy: Array = (P["sedani"]["pozy"]["klipy"] as Dictionary).keys() + (S.get("test_klipy", []) as Array)
	var videne := {}
	for o: Dictionary in P["obyvatele"]:
		var c: Dictionary = lide.nova_postava(o)
		var u: Node3D = c["uzel"]
		var kostra: Skeleton3D = c["kostra"]
		var model := ""
		for m in u.find_children("*", "MeshInstance3D", true, false):
			if (m as MeshInstance3D).mesh:
				model += (m as MeshInstance3D).mesh.resource_path
		if kostra.find_bone("sukne_0_0") < 0 or videne.has(model):
			u.queue_free()
			continue
		videne[model] = true
		u.scale = Vector3.ONE
		var ap: AnimationPlayer = c["ap"]
		# uchyty kosti predem (novy BoneAttachment3D ma polohu az po snimku)
		var ret: Array = []          # [[kosti...], delka posledni]
		var i0 := 0
		while kostra.find_bone("sukne_%d_0" % i0) >= 0:
			var jm: Array = []
			while kostra.find_bone("sukne_%d_%d" % [i0, jm.size()]) >= 0:
				jm.append("sukne_%d_%d" % [i0, jm.size()])
			var n := jm.size()
			var dl := kostra.get_bone_global_rest(kostra.find_bone(jm[n - 1])).origin.distance_to(kostra.get_bone_global_rest(kostra.find_bone(jm[n - 2])).origin) if n > 1 else 0.3
			ret.append([jm, dl])
			for j: String in jm:
				_kost(kostra, j)
			i0 += 1
		for jm: String in ["pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "hand_l", "hand_r", "middle_01_l", "middle_01_r"]:
			_kost(kostra, jm)
		var lat := _latka_priprav(u, kostra)
		# Misa 13. 11. (snimek chuze: noha vylezla z kabatce - „obleceni se ma hybat s nohou“): skutecne vrcholy latky
		# sukne (CPU skinning z vah a poz kosti po modifikatorech) proti kapslim stehen, chuze v 8 fazich a stani
		for kl2: String in (S.get("test_latka_klipy", ["Walk_Loop", "Idle_Loop"]) as Array):
			if not ap.has_animation(kl2):
				continue
			var dl2 := ap.get_animation(kl2).length
			var horsi_l := 0
			var hloubka := 0.0
			for f in 8:
				c["klip"] = ""
				lide.call("_klip", c, kl2, 1.0)
				ap.stop()
				ap.play(kl2, 0.0)
				ap.seek(dl2 * f / 8.0, true)
				ap.advance(0.0)
				for i in 6:
					await process_frame
				var r_lat := _latka_v_noze(lat, kostra, float(S.get("polomer_stehna_m", 0.09)) * float(S.get("test_latka_podil", 0.8)))
				horsi_l = maxi(horsi_l, int(r_lat[0]))
				hloubka = maxf(hloubka, float(r_lat[1]))
			print("SUKNE %s %s: latka ve stehne nejvic %d vrcholu, hloubka %.3f m" % [o["id"], kl2, horsi_l, hloubka])
			if horsi_l > int(S.get("test_latka_vrcholu", 3)):
				chyb += 1
				print("SUKNE CHYBA %s %s: noha z obleceni (%d vrcholu latky ve stehne, hloubka %.3f m)" % [o["id"], kl2, horsi_l, hloubka])
		for kl: String in klipy:
			if not ap.has_animation(kl):
				continue
			c["klip"] = ""
			lide.call("_klip", c, kl, 1.0)
			ap.stop()
			ap.play(kl, 0.0)
			ap.seek(0.5, true)
			ap.advance(0.0)
			for i in 30:
				await process_frame
			var pel := _kost(kostra, "pelvis")
			var fw := u.global_basis.z.normalized()
			var kol := {}
			var steh := {}
			for s: String in ["l", "r"]:
				kol[s] = _kost(kostra, "calf_" + s)
				steh[s] = _kost(kostra, "thigh_" + s)
			var horsi_pk := 0.0
			var horsi_st := 1.0
			for i in ret.size():
				var jm: Array = ret[i][0]
				var k0 := _kost(kostra, jm[0])
				# „za kolenem“ jen predni stred (chyba s lavici); bocni retezy u rozkrocenych nohou visi prirozene za stredem kolena
				var hk := k0 - pel
				hk.y = 0.0
				var predni := hk.length() > 0.01 and rad_to_deg(hk.angle_to(fw)) < float(S.get("test_predek_st", 35.0))
				var body: Array = []
				for j in range(1, jm.size()):
					body.append(_kost(kostra, jm[j]))
				var bx: BoneAttachment3D = kostra.get_node("test_" + String(jm[jm.size() - 1]))
				body.append(bx.global_position + bx.global_basis.y.normalized() * float(ret[i][1]))     # lem (konec posledni kosti)
				for j in body.size():
					var p: Vector3 = body[j]
					var bl: String = "l" if p.distance_to(kol["l"]) < p.distance_to(kol["r"]) else "r"
					var kn: Vector3 = kol[bl]
					if predni and p.y < kn.y - 0.05:
						var za := (kn - p).dot(fw)          # kladne = bod za kolenem (dozadu)
						horsi_pk = maxf(horsi_pk, za)
						if za > tol:
							chyb += 1
							print("SUKNE CHYBA %s %s retez %d bod %d: %.3f m za kolenem (pod kolenem ma latka padat svisle)" % [o["id"], kl, i, j + 1, za])
					for s: String in ["l", "r"]:
						var a: Vector3 = steh[s]
						var b: Vector3 = kol[s]
						var t := clampf((p - a).dot(b - a) / maxf((b - a).length_squared(), 1e-6), 0.0, 1.0)
						var d := p.distance_to(a + (b - a) * t)
						horsi_st = minf(horsi_st, d)
						if d < r_s and t > 0.15:
							chyb += 1
							print("SUKNE CHYBA %s %s retez %d bod %d: %.3f m od osy stehna %s (latka ve stehne)" % [o["id"], kl, i, j + 1, d, s])
			# Misa 13. 11. (snimek zastery vsede: ruce zapadly do zastery/sukne): dlan nad latkou v klinu
			var hor_ruka := -1.0
			for s: String in ["l", "r"]:
				var dl_ := (_kost(kostra, "hand_" + s) + _kost(kostra, "middle_01_" + s)) * 0.5
				for i in ret.size():
					var jm: Array = ret[i][0]
					for j in range(1, jm.size()):
						var p := _kost(kostra, jm[j])
						var dh := Vector2(p.x - dl_.x, p.z - dl_.z).length()
						if dh < 0.06 and p.y > dl_.y + tol:
							chyb += 1
							print("SUKNE CHYBA %s %s retez %d bod %d: latka %.3f m nad dlani %s (ruka v latce)" % [o["id"], kl, i, j, p.y - dl_.y, s])
						if dh < 0.06:
							hor_ruka = maxf(hor_ruka, p.y - dl_.y)
			print("SUKNE %s %s: latka nad dlani %.3f m" % [o["id"], kl, hor_ruka])
			print("SUKNE %s %s: nejvic za kolenem %.3f m, nejbliz ose stehna %.3f m" % [o["id"], kl, horsi_pk, horsi_st])
		u.queue_free()
	print("TEST SUKNE %s (%d chyb, modelu %d)" % ["OK" if chyb == 0 else "CHYBA", chyb, videne.size()])
	quit(1 if chyb else 0)


## Vrcholy latky sukne (vaha kosti sukne_* >= 0,3) se zdrojem skinningu: [[mi, vrchol, [kosti], [vahy]], ...]
## a uchyty (BoneAttachment3D) vsech kosti, ktere je hybou.
func _latka_priprav(u: Node3D, kostra: Skeleton3D) -> Array:
	var out: Array = []
	for mi0: Node in u.find_children("*", "MeshInstance3D", true, false):
		var mi := mi0 as MeshInstance3D
		if mi.skin == null or mi.mesh == null:
			continue
		var sk := mi.skin
		var jmena: Array = []
		for b in sk.get_bind_count():
			var jm := String(sk.get_bind_name(b))
			if jm == "":
				jm = kostra.get_bone_name(sk.get_bind_bone(b))
			jmena.append(jm)
		for si in mi.mesh.get_surface_count():
			var ar: Array = mi.mesh.surface_get_arrays(si)
			var vv: PackedVector3Array = ar[Mesh.ARRAY_VERTEX]
			var bb: PackedInt32Array = ar[Mesh.ARRAY_BONES]
			var ww: PackedFloat32Array = ar[Mesh.ARRAY_WEIGHTS]
			if bb.is_empty():
				continue
			var k := bb.size() / vv.size()
			for vi in range(0, vv.size(), 2):         # kazdy druhy vrchol staci
				var su := 0.0
				var kosti: Array = []
				var vahy: Array = []
				for j in k:
					var w := ww[vi * k + j]
					if w <= 0.0:
						continue
					var jm: String = jmena[bb[vi * k + j]]
					kosti.append([jm, sk.get_bind_pose(bb[vi * k + j])])
					vahy.append(w)
					if jm.begins_with("sukne_"):
						su += w
				if su >= 0.3:
					out.append([vv[vi], kosti, vahy])
					for kb: Array in kosti:
						_kost(kostra, kb[0])
	return out


## [pocet vrcholu latky blize ose stehna nez r, nejvetsi hloubka]
func _latka_v_noze(lat: Array, kostra: Skeleton3D, r: float) -> Array:
	var n := 0
	var hl := 0.0
	var osy: Array = []
	for s: String in ["l", "r"]:
		osy.append([_kost(kostra, "thigh_" + s), _kost(kostra, "calf_" + s)])
	for z: Array in lat:
		var p := Vector3.ZERO
		var kosti: Array = z[1]
		var vahy: Array = z[2]
		for j in kosti.size():
			var bx: BoneAttachment3D = kostra.get_node("test_" + String(kosti[j][0]))
			p += (bx.global_transform * (kosti[j][1] as Transform3D) * (z[0] as Vector3)) * float(vahy[j])
		for o: Array in osy:
			var a: Vector3 = o[0]
			var ab: Vector3 = (o[1] as Vector3) - a
			var t := clampf((p - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
			var d := p.distance_to(a + ab * t)
			if d < r and t > 0.1:
				n += 1
				hl = maxf(hl, r - d)
	return [n, hl]
