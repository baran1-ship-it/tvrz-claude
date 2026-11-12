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
static var PRST_OSA := Vector3(1, 0, 0)   # osa ohybu clanku prstu (11. 11. diag: klipy ohybaji prsty kolem x)
var prsty_st := 50.0
const PRSTY := ["index_01", "index_02", "index_03", "middle_01", "middle_02", "middle_03", "ring_01", "ring_02", "ring_03",
		"pinky_01", "pinky_02", "pinky_03"]
static var R := {}                      # postavy.json drzeni._reseni (tloustka prstu, rozsah kloubu, kroky)
static var _pozy := {}
## Sikma osa uchopu v dlani (rešerše: silovy uchop - nasada sikmo pres dlan od hypotenaru k bazi ukazovaku, s predloktim
## ~70/110 st): osa z ruky (k palci) naklonena k prstum o _reseni.sikmo_st.
static func osa_dlane() -> Vector3:
	var a := deg_to_rad(float(R.get("sikmo_st", 20.0)))
	return Vector3(0.0, sin(a), cos(a))
                  # klic (predmet, ruka, kostra, osa) -> {kost: Quaternion}
static var diag := false               # test_drzeni: vypis reseni


static func _eul(a: Array) -> Basis:
	return Basis.from_euler(Vector3(deg_to_rad(float(a[0])), deg_to_rad(float(a[1])), deg_to_rad(float(a[2]))))


func nastav(ruka: String, id: String, d: Dictionary, uzel: Node3D) -> void:
	if id == "" or uzel == null:
		polozky.erase(ruka)
	else:
		polozky[ruka] = {"id": id, "d": d, "uzel": uzel}
		# jednorucni nastroj: nasada sikmo pres dlan (rot_st da osu z ruky, naklon k prstum o sikmo_st)
		if bool(d.get("nasada", false)) and not d.has("druha_ruka") and String(d.get("rezim", "")) == "":
			if R.is_empty():
				R = (preload("res://scripts/pravidla.gd").soubor("postavy")["drzeni"] as Dictionary).get("_reseni", {})
			uzel.basis = Basis(Vector3.RIGHT, -deg_to_rad(float(R.get("sikmo_st", 20.0)))) * uzel.basis
	active = blizko and not polozky.is_empty()


## LOD (lide.gd): uchop jen do postavy.json anim_do_m - dal predmet zustane v poze klipu (neni videt), modifikator nestoji cas.
func zapni(b: bool) -> void:
	blizko = b
	var a := b and not polozky.is_empty()
	if active != a:
		active = a


var klip_ted := ""                    # prave hrany klip postavy (lide._klip) - drzeni.<id>.klipy_bez_rezimu
var _rozsah := {}                     # klip -> Vector2(min, max) vysky rukou nad rameny (faze svihu)


func _process_modification() -> void:
	if R.is_empty():
		R = (preload("res://scripts/pravidla.gd").soubor("postavy")["drzeni"] as Dictionary).get("_reseni", {})
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
		if (d.get("klipy_bez_rezimu", []) as Array).has(klip_ted):
			rez = ""                          # 11. 11.: korbel svisle pri chuzi, pri piti naklon z klipu
		var sc := uz.basis.get_scale()
		if (d.get("klipy_piti", []) as Array).has(klip_ted):
			rez = "svisle"
		if rez == "svisle":
			# ruka = chtene natoceni predmetu * uchop^-1 (v soustave kostry), poloha zapesti z klipu
			var chteno := smer * _eul(d.get("svet_rot_st", [0.0, 0.0, 0.0]))
			if (d.get("klipy_piti", []) as Array).has(klip_ted):
				# 12. 11. (korbel za ucho lezel pri piti naplocho - klip Mixamo drzi hrnek za telo): nadoba svisle, cim bliz
				# ruka k ustum (kost Head), tim vic se okraj natoci k ustum (piti.naklon_st pri ustech)
				var ihd := sk.find_bone("Head")
				if ihd >= 0:
					var pv: Dictionary = d.get("piti", {})
					var hp := skg * sk.get_bone_global_pose(ih).origin
					var hd := skg * sk.get_bone_global_pose(ihd).origin
					var t := clampf(1.0 - (hp.distance_to(hd) - float(pv.get("u_ust_m", 0.15))) / float(pv.get("od_m", 0.35)), 0.0, 1.0)
					var k_ustum := Vector3(hd.x - hp.x, 0.0, hd.z - hp.z).normalized()
					var naklon := deg_to_rad(float(pv.get("naklon_st", 70.0))) * t
					var osa_n := Vector3.UP.cross(k_ustum).normalized()
					if osa_n.length_squared() > 0.5:
						chteno = Basis(osa_n, naklon) * chteno
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
			var uc: Array = d.get("uchop", [0.0, 0.0, 0.0])
			var bod := Vector3(float(dr[0]), float(dr[1]), float(dr[2])) - Vector3(float(uc[0]), float(uc[1]), float(uc[2]))
			bod.y -= float(p.get("posun", 0.0))       # predmet posunuty v horni ruce (klouzani), druha ruka drzi konec
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
				var z_rukou := (R.get("klipy_nasada_z_rukou", []) as Array).has(klip_ted)
				if z_rukou:
					# 12. 11. klip nahrany s obourucni zbrani (mereni_nasady.gd): nasada = primka pres dlane obou rukou z klipu
					var dl_b := Vector3(-uz.position.x, uz.position.y, uz.position.z)
					var g2c := sk.get_bone_global_pose(ih2)
					osa_y = (hg.origin + hg.basis * uz.position) - (g2c.origin + g2c.basis * dl_b)
				if osa_y.length_squared() > 1e-8:
					osa_y = osa_y.normalized()
					var vpravo := -(skb.inverse() * smer.x).normalized()      # postava hledi po +z, vpravo = -x
					# 12. 11. (Misa: nastroj u obliceje mirí dopredu; rešerše docs/rozpracovane/uchop_reserse.md - USDA Ax
					# Manual, hackmotion zapesti v napahu ~90 st): faze svihu z vysky rukou nad rameny v tomto klipu (min =
					# uder, max = napah, beh si pamatuje rozsah klipu) -> zalomeni zapesti 0..svih.zalomeni_max_st dozadu
					# (hlava nastroje za hlavu postavy); horni ruka klouze po nasade od hlavy (napah) k dolni ruce (uder)
					var nahoru := (skb.inverse() * Vector3.UP).normalized()
					var ramena := (sk.get_bone_global_pose(iu1).origin + sk.get_bone_global_pose(iu2).origin) * 0.5
					var hv := ((hg.origin + h2) * 0.5 - ramena).dot(nahoru)
					var sr: Array = (R.get("svih_rozsah", {}) as Dictionary).get(klip_ted, [])
					var rz: Vector2 = _rozsah.get(klip_ted, Vector2(float(sr[0]), float(sr[1])) if sr.size() == 2 else Vector2(hv, hv))
					rz = Vector2(minf(rz.x, hv), maxf(rz.y, hv))
					_rozsah[klip_ted] = rz
					var faze := clampf((hv - rz.x) / maxf(rz.y - rz.x, 1e-4), 0.0, 1.0) if rz.y - rz.x > float(R.get("svih_min_m", 0.2)) / maxf(skg.basis.get_scale().x, 1e-4) else 0.0
					var dopredu := (skb.inverse() * smer.z).normalized()
					var zal := 0.0 if z_rukou else deg_to_rad(float(R.get("zalomeni_max_st", 90.0))) * faze
					var o1 := osa_y.rotated(vpravo, zal)
					var o2 := osa_y.rotated(vpravo, -zal)
					osa_y = o1 if o1.dot(dopredu) < o2.dot(dopredu) else o2
					var uu: float = float((d.get("uchop", [0.0, 0.0, 0.0]) as Array)[1])
					var ud := float(d.get("uchop_uder_y", uu))
					var posun := (lerpf(ud, uu, faze) - uu)                        # m po nasade od bodu uchopu dat
					if z_rukou:
						posun = float(d.get("uchop_z_rukou_y", uu)) - uu                # ruce v klipu drzi nasadu samy
					p["posun"] = posun
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
					# 11. 11. (test_drzeni: nasada 38-69 st k prstum, ma byt 90): dlan natocit, aby nasada vedla napric
					# dlani (osa z kosti ruky = napric dlani k palci, y = k prstum) - jako kladivo v jedne ruce
					var od_h := hg.basis * osa_dlane()
					_otoc(sk, ih, od_h, osa_y if od_h.dot(osa_y) >= 0.0 else -osa_y)
					hg = sk.get_bone_global_pose(ih)
					uz.basis = (hg.basis.orthonormalized().inverse() * chteno_sk).orthonormalized().scaled(sc)
					# klouzani horni ruky: predmet se v ruce posune podel nasady (bod uchopu dat -> uchop_uder_y)
					var t0: Node3D = uz.get_child(0) as Node3D if uz.get_child_count() > 0 else null
					if t0:
						var uc0: Array = d.get("uchop", [0.0, 0.0, 0.0])
						t0.position = -Vector3(float(uc0[0]), float(uc0[1]) + float(p.get("posun", 0.0)), float(uc0[2]))
					var cil0 := hg * (uz.position + Basis(uz.basis.get_rotation_quaternion()) * bod * sc.x)   # od bodu uchopu v dlani (drive od zapesti - druha ruka 9-10 cm vedle)
					# 12. 11. (fotky: v napahu druha ruka mimo dosah pevneho bodu, visela ve vzduchu): druha ruka se chyti
					# nejblizsiho mista nasady k bodu sve dlane z klipu, v rozsahu drzeni.druha_ruka_rozsah [od, do] (m od
					# bodu druha_ruka po nasade) - IK ji jen dotahne
					var rozs: Array = d.get("druha_ruka_rozsah", [0.0, 0.0])
					var dl2a := Vector3(-uz.position.x, uz.position.y, uz.position.z)
					var pd := sk.get_bone_global_pose(ih2)
					var pd_bod := pd.origin + pd.basis * dl2a
					var osa_n := (hg.basis * (Basis(uz.basis.get_rotation_quaternion()) * Vector3.UP)).normalized()
					var k0 := float(rozs[0]) * sc.x
					var k1 := float(rozs[1]) * sc.x
					var k := clampf((pd_bod - cil0).dot(osa_n), k0, k1)
					# mimo dosah paze (rameno -> bod nasady > delka paze): misto nasady nejblize rameni
					var ia := sk.find_bone("upperarm_" + druha)
					var il2 := sk.find_bone("lowerarm_" + druha)
					var A0 := sk.get_bone_global_pose(ia).origin
					var dosah := A0.distance_to(sk.get_bone_global_pose(il2).origin) + sk.get_bone_global_pose(il2).origin.distance_to(pd.origin)
					var vzd := dl2a.length() * 0.5                                  # bod dlane je kus za zapestim
					if A0.distance_to(cil0 + osa_n * k) > dosah + vzd:
						k = clampf((A0 - cil0).dot(osa_n), k0, k1)
					cil0 += osa_n * k
					_ik(sk, druha, cil0)
					var hg2 := sk.get_bone_global_pose(ih2)
					_otoc(sk, ih2, hg2.basis.z, osa_y if hg2.basis.z.dot(osa_y) >= 0.0 else -osa_y)
					# 12. 11. (rešerše: druha ruka IK na uchop, ne zapesti): na nasade ma byt dutina pesti druhe ruky
					# (bod uchopu zrcadlene), ne zapesti - IK znovu s cilem posunutym o bod dlane
					# IK hybe pazi a tim i natocenim ruky, natoceni zas posune bod dlane - 3 kola (sbiha se)
					var dl2 := Vector3(-uz.position.x, uz.position.y, uz.position.z)
					for _k in int(R.get("ik_kol", 6)):
						hg2 = sk.get_bone_global_pose(ih2)
						_ik(sk, druha, cil0 - hg2.basis.orthonormalized() * dl2)   # kost ruky ma v soustave kostry meritko
						hg2 = sk.get_bone_global_pose(ih2)
						var od2 := hg2.basis * osa_dlane()
						_otoc(sk, ih2, od2, osa_y if od2.dot(osa_y) >= 0.0 else -osa_y)
					hg2 = sk.get_bone_global_pose(ih2)
					if diag:
						var gp := hg2.origin + hg2.basis * dl2
						var hg1 := sk.get_bone_global_pose(ih)
						var bod0 := hg1 * (Basis(uz.basis.get_rotation_quaternion()) * bod * sc.x)
						var v2 := gp - hg1.origin
						var osa_w := (hg1.basis * (uz.basis.get_rotation_quaternion() * Vector3.UP)).normalized()
						var osa_g := (skg.basis * osa_w).normalized()
						var p0g := skg * hg1.origin + skg.basis * (hg1.basis * uz.position)
						var zg := skg * hg2.origin - p0g
						print("UCHOP_ZAPESTI %s %s osa %s, zapesti od osy %.3f, uz.global %s %s" % [Engine.get_process_frames(), (skg * hg2.origin).snapped(Vector3.ONE * 0.001), osa_g.snapped(Vector3.ONE * 0.01), (zg - osa_g * zg.dot(osa_g)).length(), uz.global_position.snapped(Vector3.ONE * 0.001), uz.global_basis.y.normalized().snapped(Vector3.ONE * 0.01)])
						print("UCHOP_DRUHA %s klip %s faze %.2f: bod dlane od cile %.3f, od osy %.3f, cil od osy %.3f, zapesti od cile %.3f" % [String(p["id"]), klip_ted, faze, gp.distance_to(cil0), (v2 - osa_w * v2.dot(osa_w)).length(), ((bod0 - hg1.origin) - osa_w * (bod0 - hg1.origin).dot(osa_w)).length(), hg2.origin.distance_to(cil0)])
					_prsty(sk, ruka, p, d)
					var a2 := (hg2.basis.orthonormalized().inverse() * osa_y).normalized()
					# skutecna nasada v soustave druhe ruky (kdyz IK nedosahne presne): bod osy nejblize bodu dlane,
					# zaokrouhleny na 5 mm (cache) - prsty obejmou nasadu tam, kde je
					var p_osa := hg2.affine_inverse() * (hg.origin + hg.basis * uz.position)
					var bod2 := p_osa + a2 * (dl2 - p_osa).dot(a2)
					bod2 = dl2 + ((bod2 - dl2) / 0.005).round() * 0.005                       # po 5 mm (1 cm: prsty 4-9 mm v tenke nasade); predpocitane test_drzeni
					var pz2: Dictionary = _poza(sk, druha, {"id": String(p["id"]) + "_druha" + str(bod2 - dl2), "uzel": uz}, d, bod2, a2)
					for ib: int in pz2:
						sk.set_bone_pose_rotation(ib, pz2[ib])
					if diag:
						var hgl := sk.get_bone_global_pose(ih)
						var o_s := (hgl.basis * (uz.basis.get_rotation_quaternion() * Vector3.UP)).normalized()
						var p_s := hgl.origin + hgl.basis * uz.position
						var tx := ""
						for fn: String in ["index_03", "middle_03", "ring_03"]:
							var q := sk.get_bone_global_pose(sk.find_bone(fn + "_" + druha)).origin - p_s
							tx += " %s %.3f" % [fn, (q - o_s * q.dot(o_s)).length()]
						var q2 := sk.get_bone_global_pose(ih2).origin + sk.get_bone_global_pose(ih2).basis * dl2 - p_s
						print("UCHOP_PRSTY2 %s a2 %s dlan od osy %.3f%s" % [Engine.get_process_frames(), a2.snapped(Vector3.ONE * 0.01), (q2 - o_s * q2.dot(o_s)).length(), tx])
					continue
			var cil := hg * (uz.position + Basis(uz.basis.get_rotation_quaternion()) * bod * sc.x)   # od bodu uchopu v dlani (drive od zapesti - druha ruka 9-10 cm vedle)
			_ik(sk, druha, cil)
		_prsty(sk, ruka, p, d)


func _prsty(sk: Skeleton3D, ruka: String, p: Dictionary, d: Dictionary) -> void:
	# prsty: reseny uchop (12. 11., rešerše docs/rozpracovane/uchop_reserse.md - asset-tooling #390, deadnight #507):
	# kazdy clanek prstu se ohne od kloubu, az se dotkne nasady (polomer + pul tloustky prstu), palec pres ukazovak;
	# poza prstu je vrstva jen pro prsty (prepise klip), spocita se jednou na predmet a ruku a drzi se v kazdem snimku
	if bool(d.get("nasada", false)) or d.has("uchop_r_m"):
		var pz: Dictionary = _poza(sk, ruka, p, d)
		# bod uchopu pro tuto ruku (predpocitany posun od dat dlan_m): predmet se jednou posune v dlani
		if not p.has("posun_ok") and p.has("posun_dlane"):
			p["posun_ok"] = true
			(p["uzel"] as Node3D).position += p["posun_dlane"]
		for ib: int in pz:
			sk.set_bone_pose_rotation(ib, pz[ib])
	else:
		var ps := deg_to_rad(float(d.get("prsty_st", prsty_st)))
		for pn: String in PRSTY:
			var ip := sk.find_bone(pn + "_" + ruka)
			if ip >= 0 and ps != 0.0:
				sk.set_bone_pose_rotation(ip, sk.get_bone_pose_rotation(ip) * Quaternion(PRST_OSA, ps))


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


## Poza prstu pro predmet v ruce (z cache, jinak vyresit). Nasada v soustave kosti ruky: primka pres pocatek uzlu drzi_
## (bod uchopu) ve smeru osy nasady predmetu (y), u visicich (vedro, kosik, lucerna) napric dlani (osa z ruky) - drzadlo
## lezi v prstech, predmet visi. Polomer z modelu (vrcholy u bodu uchopu) nebo drzeni.<id>.uchop_r_m.
func _poza(sk: Skeleton3D, ruka: String, p: Dictionary, d: Dictionary, bod := Vector3.INF, osa := Vector3.ZERO) -> Dictionary:
	var uz: Node3D = p["uzel"]
	var visi := String(d.get("rezim", "")) == "visi"
	if osa == Vector3.ZERO:
		var on: Array = d.get("osa_nasady", [0.0, 1.0, 0.0])            # osa drzadla v predmetu (srp: x)
		osa = Vector3(0, 0, 1) if visi else (uz.basis * Vector3(float(on[0]), float(on[1]), float(on[2]))).normalized()
	if bod == Vector3.INF:
		bod = uz.position
	# primka nasady nema smer (prsty ji obejmou stejne) - jedno znamenko osy: jeden klic, jeden posun dlane
	if osa.z < 0.0 or (is_zero_approx(osa.z) and osa.y < 0.0):
		osa = -osa
	var klic := "%s|%s|%s|%s" % [String(p["id"]), ruka, str(sk.get_bone_rest(sk.find_bone("index_01_" + ruka)).origin.snapped(Vector3.ONE * 0.001)), str(osa.snapped(Vector3.ONE * 0.25))]
	if _pozy.has(klic):
		p["r_m"] = _pozy[klic + "|r"]
		p["posun_dlane"] = _pozy.get(klic + "|p", Vector3.ZERO)
		return _pozy[klic]
	# predpocitane pozy (test_drzeni zapise POZY_SOUBOR) - ve hre bez reseni (7-9 ms na PC, na tabletu vic = zasek)
	if _soubor.is_empty():
		_soubor = {"_": true}
		if not diag and FileAccess.file_exists(POZY_SOUBOR):      # test pozy pocita znovu (a zapise)
			_soubor = JSON.parse_string(FileAccess.get_file_as_string(POZY_SOUBOR))
	if _soubor.has(klic):
		var zs: Dictionary = _soubor[klic]
		var pz0 := {}
		for jm: String in zs["kosti"]:
			var ib := sk.find_bone(jm)
			var q: Array = zs["kosti"][jm]
			if ib >= 0:
				pz0[ib] = Quaternion(float(q[0]), float(q[1]), float(q[2]), float(q[3]))
		_pozy[klic] = pz0
		_pozy[klic + "|r"] = float(zs["r"])
		var ps0: Array = zs.get("posun", [0.0, 0.0, 0.0])
		_pozy[klic + "|p"] = Vector3(float(ps0[0]), float(ps0[1]), float(ps0[2]))
		p["r_m"] = float(zs["r"])
		p["posun_dlane"] = _pozy[klic + "|p"]
		return pz0
	if R.is_empty():
		R = (preload("res://scripts/pravidla.gd").soubor("postavy")["drzeni"] as Dictionary).get("_reseni", {})
	var on2: Array = d.get("osa_nasady", [0.0, 1.0, 0.0])
	var r_m := float(d["uchop_r_m"]) if d.has("uchop_r_m") else _polomer(uz, Vector3(float(on2[0]), float(on2[1]), float(on2[2])))
	var t0 := Time.get_ticks_usec()
	var rr := (r_m + float(R.get("prst_pul_m", 0.009))) * uz.scale.x
	var posun := Vector3.ZERO
	if diag and not String(p["id"]).contains("_druha"):
		# test_drzeni: nejlepsi bod uchopu pro tuto ruku (nejmensi nejvetsi mezera/prunik prstu) - ulozi se k poze
		var nej := INF
		var nb := Vector3.ZERO
		for dx in range(-3, 4):
			for dy in range(-4, 3):
				var b2 := bod + Vector3(dx, dy, 0) * 0.005 * uz.scale.x
				var m := _mezera_prstu(sk, ruka, b2, osa, rr)
				if m < nej - 1e-5:
					nej = m
					nb = Vector3(dx, dy, 0) * 0.005
		print("UCHOP_NAVRH %s %s posun bodu dlane %s m, nejvetsi mezera %.1f mm (ted %.1f mm)" % [String(p["id"]), ruka, nb, nej / uz.scale.x * 1000.0, _mezera_prstu(sk, ruka, bod, osa, rr) / uz.scale.x * 1000.0])
		posun = nb * uz.scale.x
		bod += posun
	t0 = Time.get_ticks_usec()                          # cas jen reseni (bez navrhu bodu v testu)
	var pz := _res(sk, ruka, bod, osa, rr)
	if diag:
		print("UCHOP_RESENI %s %s polomer %.4f m, osa %s, %d us" % [String(p["id"]), ruka, r_m, osa, Time.get_ticks_usec() - t0])
	_pozy[klic] = pz
	_pozy[klic + "|r"] = r_m
	_pozy[klic + "|p"] = posun
	p["r_m"] = r_m
	p["posun_dlane"] = posun
	if diag:
		var kosti := {}
		for ib: int in pz:
			var q: Quaternion = pz[ib]
			kosti[sk.get_bone_name(ib)] = [q.x, q.y, q.z, q.w]
		_nove[klic] = {"r": r_m, "kosti": kosti, "posun": [posun.x, posun.y, posun.z]}
	else:
		push_warning("uchop: poza %s neni predpocitana (tools/test_drzeni.gd) - reseno za behu" % klic)
	return pz


const POZY_SOUBOR := "res://pravidla/svet/uchop_pozy.json"
static var _soubor := {}
static var _nove := {}                  # test: nove vyresene pozy k zapisu


## test_drzeni: zapis predpocitanych poz (klic -> polomer a rotace kosti prstu).
static func zapis_pozy() -> int:
	var f := FileAccess.open(POZY_SOUBOR, FileAccess.WRITE)
	f.store_string(JSON.stringify(_nove, " ", true))
	return _nove.size()


## Polomer nasady z modelu: median vzdalenosti vrcholu od osy y predmetu v okne +-okno_m kolem bodu uchopu, jen do
## max_polomer_m (bez hlavy nastroje). Valec ma vsechny vrcholy na polomeru -> median = polomer.
static func _polomer(uz: Node3D, osa := Vector3.UP) -> float:
	var okno := float(R.get("okno_m", 0.12))
	var mx := float(R.get("max_polomer_m", 0.04))
	var rr: Array = []
	var inv := uz.global_transform.affine_inverse()
	for mi: Node in uz.find_children("*", "MeshInstance3D", true, false):
		var m := (mi as MeshInstance3D).mesh
		if m == null:
			continue
		var tr := inv * (mi as MeshInstance3D).global_transform
		for si in m.get_surface_count():
			for v: Vector3 in m.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
				var w := tr * v
				var podel := w.dot(osa)
				if absf(podel) <= okno:
					var r := (w - osa * podel).length()
					if r <= mx:
						rr.append(r)
	if rr.size() < 4:
		return float(R.get("polomer_vychozi_m", 0.015))
	rr.sort()
	return float(rr[rr.size() / 2])


## Reseni (soustava kosti ruky): prsty od kloubu 01 -> 02 -> 03 ohnout po kroku, dokud bod clanku (klouby, stredy
## clanku, konecek _04_leaf) nedojde na rr od osy nasady nebo kloub na rozsah (drzeni._reseni.klouby_st). Smer ohybu
## kazdeho prstu = ten, ktery konecek priblizi k nasade. Palec: kloub 01 hledani natoceni (mrizka), 02-03 ohyb do dotyku,
## cil = konecek palce na ukazovaku z vnejsi strany (palec pres ukazovak, #390).
func _res(sk: Skeleton3D, ruka: String, P0: Vector3, A: Vector3, rr: float, palec := true) -> Dictionary:
	var out := {}
	var lim: Array = R.get("klouby_st", [90.0, 105.0, 80.0])
	var krok := deg_to_rad(float(R.get("krok_st", 2.0)))
	var ukaz := Vector3.ZERO
	for f: String in ["index", "middle", "ring", "pinky"]:
		var ids: Array = []
		for j in ["01", "02", "03", "04_leaf"]:
			ids.append(sk.find_bone("%s_%s_%s" % [f, j, ruka]))
		if ids.has(-1):
			continue
		var q: Array = []
		for j in 3:
			q.append(sk.get_bone_rest(ids[j]).basis.get_rotation_quaternion())
		var zn := _znamenko(sk, ids, q, PRST_OSA, P0, A)
		for j in 3:
			var q0: Quaternion = q[j]
			var a := 0.0
			var dobre := 0.0
			while a <= deg_to_rad(float(lim[j])):
				q[j] = q0 * Quaternion(PRST_OSA, a * zn)
				if _min_od_osy(_fk(sk, ids, q), j + 1, P0, A) <= rr:
					break
				dobre = a
				a += krok
			q[j] = q0 * Quaternion(PRST_OSA, dobre * zn)
		for j in 3:
			out[ids[j]] = q[j]
		if f == "index":
			var b: Array = _fk(sk, ids, q)
			ukaz = b[2]                                  # kloub 03 ukazovaku (stredni clanek)
	if not palec:
		return out
	# palec
	var tid: Array = []
	for j in ["01", "02", "03", "04_leaf"]:
		tid.append(sk.find_bone("thumb_%s_%s" % [j, ruka]))
	if tid.has(-1):
		return out
	var tq0: Array = []
	for j in 3:
		tq0.append(sk.get_bone_rest(tid[j]).basis.get_rotation_quaternion())
	# cil: kloub 03 ukazovaku odsunuty od osy o tloustku prstu (palec lezi na ukazovaku)
	var na_ose := P0 + A * (ukaz - P0).dot(A)
	var cil := ukaz + (ukaz - na_ose).normalized() * rr * 0.5 if ukaz != Vector3.ZERO else P0
	var nej := INF
	var nej_q: Array = tq0.duplicate()
	var ms := float(R.get("palec_mrizka_st", 60.0))
	var mk := float(R.get("palec_krok_st", 15.0))
	var ax := -ms
	while ax <= ms:
		var az := -ms
		while az <= ms:
			var q: Array = tq0.duplicate()
			q[0] = (tq0[0] as Quaternion) * Quaternion.from_euler(Vector3(deg_to_rad(ax), 0.0, deg_to_rad(az)))
			var zn := _znamenko(sk, tid, q, PALEC_OSA, P0, A, 1)
			for j in [1, 2]:
				var q0: Quaternion = q[j]
				var a := 0.0
				var dobre := 0.0
				while a <= deg_to_rad(float(lim[j])):
					q[j] = q0 * Quaternion(PALEC_OSA, a * zn)
					if _min_od_osy(_fk(sk, tid, q), j + 1, P0, A) <= rr:
						break
					dobre = a
					a += krok * 2.0
				q[j] = q0 * Quaternion(PALEC_OSA, dobre * zn)
			var b: Array = _fk(sk, tid, q)
			var pen := maxf(0.0, rr - 0.002 - _min_od_osy(b, 1, P0, A))     # palec nejvys 2 mm v nasade (test_dovnitr_m)
			var cena: float = (b[3] as Vector3).distance_to(cil) + pen * 10.0
			if cena < nej:
				nej = cena
				nej_q = q
			az += mk
		ax += mk
	for j in 3:
		out[tid[j]] = nej_q[j]
	return out


const PALEC_OSA := Vector3(0, 0, 1)


## Smer ohybu (+1/-1): ktery konecek (po ohybu vsech tri kloubu o 40 st) je bliz ose nasady.
static func _znamenko(sk: Skeleton3D, ids: Array, q: Array, os: Vector3, P0: Vector3, A: Vector3, od := 0) -> float:
	var nej := 1.0
	var dn := INF
	for zn: float in [1.0, -1.0]:
		var qq: Array = q.duplicate()
		for j in range(od, 3):
			qq[j] = (q[j] as Quaternion) * Quaternion(os, deg_to_rad(40.0) * zn)
		var b: Array = _fk(sk, ids, qq)
		var dd := _od_osy(b[3], P0, A)
		if dd < dn:
			dn = dd
			nej = zn
	return nej


## Polohy kloubu prstu (01, 02, 03, konecek) v soustave kosti ruky; rotace q pro 01-03, posuny z klidove pozy.
static func _fk(sk: Skeleton3D, ids: Array, q: Array) -> Array:
	var t := sk.get_bone_rest(ids[0])
	t = Transform3D(Basis(q[0] as Quaternion), t.origin)
	var b: Array = [t.origin]
	for j in range(1, 4):
		var r := sk.get_bone_rest(ids[j])
		t = t * Transform3D(Basis(q[j] as Quaternion) if j < 3 else r.basis, r.origin)
		b.append(t.origin)
	return b


static func _od_osy(x: Vector3, P0: Vector3, A: Vector3) -> float:
	var v := x - P0
	return (v - A * v.dot(A)).length()


## Nejmensi vzdalenost od osy pro body od kloubu k (vcetne stredu clanku mezi k-1..3).
static func _min_od_osy(b: Array, k: int, P0: Vector3, A: Vector3) -> float:
	var m := INF
	for i in range(maxi(k, 1), 4):
		m = minf(m, _od_osy(b[i], P0, A))
		m = minf(m, _od_osy(((b[i] as Vector3) + (b[i - 1] as Vector3)) * 0.5, P0, A))
	return m


## Nejvetsi mezera mezi prsty (ukazovak-prstenik) a povrchem nasady po reseni pozy prstu (bez palce) - pro navrh bodu.
func _mezera_prstu(sk: Skeleton3D, ruka: String, P0: Vector3, A: Vector3, rr: float) -> float:
	var pz := _res(sk, ruka, P0, A, rr, false)
	var nej := 0.0
	for f: String in ["index", "middle", "ring", "pinky"]:
		var ids: Array = []
		for j in ["01", "02", "03", "04_leaf"]:
			ids.append(sk.find_bone("%s_%s_%s" % [f, j, ruka]))
		if ids.has(-1):
			continue
		var q: Array = [pz[ids[0]], pz[ids[1]], pz[ids[2]]]
		var b: Array = _fk(sk, ids, q)
		if f != "pinky":
			nej = maxf(nej, _min_od_osy(b, 1, P0, A) - rr)             # mezera (prst nedosahne; malicek muze byt mimo)
		nej = maxf(nej, rr - _min_od_osy(b, 1, P0, A) - 0.002)        # prunik (clanek v nasade) nad 2 mm
	return nej
