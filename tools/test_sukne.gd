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
		for jm: String in ["pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r"]:
			_kost(kostra, jm)
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
				var predni := (k0 - pel).dot(fw) > 0.03
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
			print("SUKNE %s %s: nejvic za kolenem %.3f m, nejbliz ose stehna %.3f m" % [o["id"], kl, horsi_pk, horsi_st])
		u.queue_free()
	print("TEST SUKNE %s (%d chyb, modelu %d)" % ["OK" if chyb == 0 else "CHYBA", chyb, videne.size()])
	quit(1 if chyb else 0)
