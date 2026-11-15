extends SceneTree
## Test svarů oděvu (Míša 15. 11. ř. 3: „postavy mají potrhané oblečení“ – tmavé trojúhelníky na ramenou a zádech).
## Bez světa, headless. Každá sada NPC (pravidla/svet/postavy_vzhled.json – obyvatele, podle_role, zalozni) se postaví
## jako ve hře (scripts/lide.gd nova_postava) a v klidu a v test_snimku fázích klipů test_klipy (chůze, klek, sed) se
## síť skinuje na CPU (váhy a bind pózy ze sítě, pózy kostí po modifikátorech přes BoneAttachment3D). Kontroly
## (postavy_vzhled.json svy_odevu):
##  par    – vrcholy se stejnou klidovou polohou (do test_par_m; export glTF je dělí na švech UV) nesmí být v žádné
##           fázi od sebe víc než test_partner_m (stejné váhy = švy se nerozevřou);
##  sev    – v oblasti ramen a horních zad (svy_odevu.oblast, mimo otvory krku, rukávů a lemu) žádná otevřená hrana,
##           naproti které je do test_sev_dosah_m okraj jiné smyčky hranice (jiný kus nebo roztržení) (nesvařený šov = rukáv zasunutý pod trup, kusy
##           k sobě, v rovině látky do test_sev_normala_m; okraj bez protějšku nebo protějšek v jiné vrstvě = lem
##           kápě/roušky nad kotlemi, ten smí být). Povrchy s alfou (vlasy) ne.
## Spuštění: tools/beh.sh svy cmd godot --headless --path . -s res://tools/test_svy_odevu.gd   (BEH_SDILENE=1)
## Volitelně TVRZ_SVY_SADY="npc_ponocny,npc_matej" jen vybrané sady. Výstup: SVY ... řádky, TEST SVY OK/CHYBA.
## Ladění: TVRZ_SVY_LADIT=1 vypíše u každého nálezu klidové polohy okraje a protějšku (které smyčky se potkávají);
## TVRZ_SVY_OBJ=<složka> uloží skinovanou síť povrchů (klid a každá fáze) jako OBJ pro rozbor vrstev mimo Godot.

const Lide := preload("res://scripts/lide.gd")
const Vzhled := preload("res://scripts/vzhled.gd")
var chyb := 0
var R: Dictionary = {}


func _initialize() -> void:
	_beh.call_deferred()


func _kost(kostra: Skeleton3D, jm: String) -> BoneAttachment3D:
	var bx: BoneAttachment3D = kostra.get_node_or_null("svy_" + jm)
	if bx == null:
		bx = BoneAttachment3D.new()
		bx.name = "svy_" + jm
		bx.bone_name = jm
		kostra.add_child(bx)
	return bx


func _sady() -> Array:
	var d: Dictionary = Vzhled.data()
	var s := {}
	for k: String in (d["obyvatele"] as Dictionary).values() + (d["podle_role"] as Dictionary).values() \
			+ (d["zalozni"]["muz"] as Array) + (d["zalozni"]["zena"] as Array):
		s[k] = true
	var out: Array = s.keys()
	out.sort()
	if OS.has_environment("TVRZ_SVY_SADY"):
		out = Array(OS.get_environment("TVRZ_SVY_SADY").split(","))
	return out


func _beh() -> void:
	R = Vzhled.data()["svy_odevu"]
	var koren := Node3D.new()
	root.add_child(koren)
	var lide: Node3D = Lide.new()
	koren.add_child(lide)
	lide.set_process(false)          # jen stavba postav a klipy; bez sveta a hrace (log bez chyb kazdy snimek)
	var P: Dictionary = Lide.P
	var vzor: Dictionary = (P["obyvatele"] as Array)[0]
	var modelu := 0
	for sada: String in _sady():
		if not ResourceLoader.exists(Vzhled.cesta(sada)):
			print("SVY CHYBA %s: sada chybi (%s)" % [sada, Vzhled.cesta(sada)])
			chyb += 1
			continue
		var o: Dictionary = vzor.duplicate()
		o["id"] = "svy_" + sada
		o["vzhled"] = sada
		var c: Dictionary = lide.nova_postava(o)
		if c.is_empty():
			print("SVY CHYBA %s: postava nevznikla" % sada)
			chyb += 1
			continue
		modelu += 1
		var u: Node3D = c["uzel"]
		u.scale = Vector3.ONE
		var kostra: Skeleton3D = c["kostra"]
		var ap: AnimationPlayer = c["ap"]
		var sit := _priprav(u, kostra)
		for i in 6:
			await process_frame
		var h := _zmer(sit)
		_obj(sit, sada + "_klid")
		var vk := _vrstva(sit)
		var vrstvy: int = vk[0]
		print("SVY %s klid: vrchni kus pres hlavu %d ploch, spodnich vrcholu %d, prorusta %d (nejvic %.4f m, klid %s)" % [sada, sit["vrch"].size() / 3, sit["spod"].size(), vk[0], vk[1], vk[2]])
		if vk[0] > 0:
			print("SVY CHYBA %s klid: spodni kus prorusta vrchnim (kukle), %d vrcholu" % [sada, vk[0]])
		var horsi_par: float = h[0]
		var sevy: int = h[1]
		print("SVY %s klid: nejhorsi par %s" % [sada, h[3]])
		print("SVY %s klid: par %.4f m, nesvarene okraje v ramenou %d (%d paru, %d okraju v oblasti)" % [sada, h[0], h[1], sit["pary"].size() / 2, sit["okraje"].size()])
		if h[1] > 0:
			print("SVY CHYBA %s klid: nesvareny sev v ramenou/zadech, %d okraju, napr. %s" % [sada, h[1], str(h[2])])
		var nf := int(R.get("test_snimku", 6))
		for kl: String in (R["test_klipy"] as Array):
			if not ap.has_animation(kl):
				print("SVY %s: klip %s chybi" % [sada, kl])
				continue
			var dl := ap.get_animation(kl).length
			var kp := 0.0
			var ks := 0
			for f in nf:
				c["klip"] = ""
				lide.call("_klip", c, kl, 1.0)
				ap.stop()
				ap.play(kl, 0.0)
				ap.seek(dl * f / float(nf), true)
				ap.advance(0.0)
				for i in 4:
					await process_frame
				var r := _zmer(sit)
				_obj(sit, "%s_%s_%d" % [sada, kl, f])
				var vf := _vrstva(sit)
				vrstvy = maxi(vrstvy, int(vf[0]))
				if int(vf[0]) > 0:
					print("SVY CHYBA %s %s faze %d/%d: spodni kus prorusta vrchnim (kukle), %d vrcholu, nejvic %.4f m, klid %s" % [sada, kl, f, nf, vf[0], vf[1], vf[2]])
				kp = maxf(kp, float(r[0]))
				ks = maxi(ks, int(r[1]))
				if float(r[0]) > float(R["test_partner_m"]) or int(r[1]) > 0:
					if float(r[0]) > float(R["test_partner_m"]):
						print("SVY %s %s par: %s" % [sada, kl, r[3]])
					print("SVY CHYBA %s %s faze %d/%d: par %.4f m (max %.4f), nesvarene okraje %d, napr. %s" % [sada, kl, f, nf, r[0], R["test_partner_m"], r[1], str(r[2])])
			print("SVY %s %s: par nejvic %.4f m, nesvarene okraje nejvic %d" % [sada, kl, kp, ks])
			horsi_par = maxf(horsi_par, kp)
			sevy = maxi(sevy, ks)
		if horsi_par > float(R["test_partner_m"]) or sevy > 0 or vrstvy > 0:
			chyb += 1
		u.queue_free()
		await process_frame
	print("TEST SVY %s (%d chyb, sad %d)" % ["OK" if chyb == 0 else "CHYBA", chyb, modelu])
	quit(1 if chyb else 0)


## Vrcholy všech neprůhledných povrchů se zdrojem skinningu; páry (stejná klidová poloha) a okraje v oblasti ramen.
## {"v": [[klid, [uchyty], [bind], [vahy]]...], "pary": PackedInt32Array (i, j, ...), "okraje": [[a, b]...] (indexy do v),
##  "hranice": [indexy v na okraji], "sousede": {i: [j..]} (okraj), "ok_okraje": ...}
func _priprav(u: Node3D, kostra: Skeleton3D) -> Dictionary:
	var V: Array = []
	var pary := PackedInt32Array()
	var okraje: Array = []
	var hranice := {}
	var sousede := {}
	var troj := PackedInt32Array()
	var krk_y := -INF
	var q := float(R["test_par_m"])
	var ob: Dictionary = R["oblast"]
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
		# oblast z kosti v prostoru site (bind poza^-1 = poloha kosti v klidu); glTF: y nahoru, predek +z
		var poz := {}
		for b in jmena.size():
			poz[jmena[b]] = sk.get_bind_pose(b).affine_inverse().origin
		if not (poz.has("upperarm_l") and poz.has("upperarm_r") and poz.has("neck_01")):
			continue
		var ul: Vector3 = poz["upperarm_l"]
		var ur: Vector3 = poz["upperarm_r"]
		var zr := (ul.y + ur.y) * 0.5
		var xr := maxf(absf(ul.x), absf(ur.x))
		var nz: float = (poz["neck_01"] as Vector3).y
		krk_y = maxf(krk_y, nz)
		var z0 := zr - float(ob["podpazi_pod_ramenem_m"])
		for si in mi.mesh.get_surface_count():
			var mat := mi.mesh.surface_get_material(si) as BaseMaterial3D
			if mat and mat.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED:
				continue                       # vlasy, oboci (alfa vyrez) - karty maji okraje vsude
			if mat and mat.albedo_texture and String(mat.albedo_texture.resource_path).contains("_hlava_"):
				continue                       # hlava + dekolt (kuze, ne odev) - jen povrch tela a odevu
			var ar: Array = mi.mesh.surface_get_arrays(si)
			var vv: PackedVector3Array = ar[Mesh.ARRAY_VERTEX]
			var nn: PackedVector3Array = ar[Mesh.ARRAY_NORMAL]
			var bb: PackedInt32Array = ar[Mesh.ARRAY_BONES]
			var ww: PackedFloat32Array = ar[Mesh.ARRAY_WEIGHTS]
			var ii: PackedInt32Array = ar[Mesh.ARRAY_INDEX]
			if bb.is_empty() or vv.is_empty():
				continue
			var k := bb.size() / vv.size()
			var base := V.size()
			var klic := {}
			var svar := PackedInt32Array()
			svar.resize(vv.size())
			for vi in vv.size():
				var uch: Array = []
				var bind: Array = []
				var vah: Array = []
				for j in k:
					var w := ww[vi * k + j]
					if w <= 0.0:
						continue
					uch.append(_kost(kostra, jmena[bb[vi * k + j]]))
					bind.append(sk.get_bind_pose(bb[vi * k + j]))
					vah.append(w)
				V.append([vv[vi], uch, bind, vah, nn[vi] if vi < nn.size() else Vector3.UP])
				var kk := Vector3i((vv[vi] / q).round())
				if klic.has(kk):
					pary.append(base + vi)
					pary.append(base + int(klic[kk]))
					svar[vi] = int(klic[kk])
				else:
					klic[kk] = vi
					svar[vi] = vi
			# hrany po svaru stejnych poloh; okraj = hrana jedne plochy
			var hrany := {}
			var nt := ii.size() / 3 if not ii.is_empty() else vv.size() / 3
			for t in nt * 3:
				troj.append(base + (ii[t] if not ii.is_empty() else t))
			for t in nt:
				for e in 3:
					var a := svar[ii[t * 3 + e]] if not ii.is_empty() else svar[t * 3 + e]
					var b := svar[ii[t * 3 + (e + 1) % 3]] if not ii.is_empty() else svar[t * 3 + (e + 1) % 3]
					if a == b:
						continue
					var key := Vector2i(mini(a, b), maxi(a, b))
					hrany[key] = int(hrany.get(key, 0)) + 1
			for key: Vector2i in hrany:
				if int(hrany[key]) != 1:
					continue
				var a := base + key.x
				var b := base + key.y
				hranice[a] = true
				hranice[b] = true
				(sousede.get_or_add(a, []) as Array).append(b)
				(sousede.get_or_add(b, []) as Array).append(a)
				var m := (vv[key.x] + vv[key.y]) * 0.5
				if m.y < z0:
					continue
				var ax := absf(m.x)
				var ram := ax >= float(ob["krk_x_m"]) and ax <= xr + float(ob["rameno_x_navic_m"])
				var zad := ax < float(ob["krk_x_m"]) and m.z <= -float(ob["zada_y_m"]) and m.y < nz - float(ob["zada_pod_krkem_m"])
				if ram or zad:
					okraje.append([a, b])
	# smycky okraju (souvisle casti hranice): protejsek svu lezi na JINE smycce (dva kusy / roztrzeni), lem kape
	# skladany do zahybu je jedna smycka a nepocita se
	var smycka := {}
	var ns := 0
	for s0: int in hranice.keys():
		if smycka.has(s0):
			continue
		var st: Array = [s0]
		smycka[s0] = ns
		while not st.is_empty():
			var x: int = st.pop_back()
			for y: int in sousede.get(x, []):
				if not smycka.has(y):
					smycka[y] = ns
					st.append(y)
		ns += 1
	# vrchni kus pres hlavu (kukle): souvisla cast odevu s nejvyssim vrcholem, sahajici test_vrstva_nad_krkem_m nad krk;
	# spodni = vrcholy ostatnich kusu v jejim dosahu (kontrola vrstev _vrstva)
	var rep := {}
	var par: Array = []                  # Array (odkaz) - lambda najdi ho sdili, Packed* by zkopirovala
	par.resize(V.size())
	for i in V.size():
		var kk := Vector3i(((V[i][0] as Vector3) / q).round())
		par[i] = int(rep.get_or_add(kk, i))
	var najdi := func(x: int) -> int:
		while par[x] != x:
			par[x] = par[par[x]]
			x = par[x]
		return x
	for t in range(0, troj.size(), 3):
		var a: int = najdi.call(troj[t])
		for e in [1, 2]:
			var b: int = najdi.call(troj[t + e])
			if a != b:
				par[b] = a
	var vrch := PackedInt32Array()
	var spod := PackedInt32Array()
	var ty := -INF
	var tk := -1
	for i in V.size():
		if (V[i][0] as Vector3).y > ty:
			ty = (V[i][0] as Vector3).y
			tk = najdi.call(i)
	if tk >= 0 and ty > krk_y + float(R["test_vrstva_nad_krkem_m"]):
		var lo := Vector3.INF
		var hi := -Vector3.INF
		for t in range(0, troj.size(), 3):
			if najdi.call(troj[t]) == tk:
				for e in 3:
					vrch.append(troj[t + e])
					lo = lo.min(V[troj[t + e]][0])
					hi = hi.max(V[troj[t + e]][0])
		var dd := Vector3.ONE * float(R["test_vrstva_dosah_m"])
		for i in V.size():
			var p0: Vector3 = V[i][0]
			if najdi.call(i) != tk and p0 == p0.clamp(lo - dd, hi + dd):
				spod.append(i)
	return {"v": V, "pary": pary, "okraje": okraje, "hranice": hranice.keys(), "smycka": smycka, "troj": troj,
		"vrch": vrch, "spod": spod}


## Vrstvy (15. 11., Míša ř. 3 / 02.jpg: tmavý trojúhelník na zádech pod kapucí = kotle prosvítala límcem kukle):
## žádný vrchol spodního kusu, který se kolmo promítá do plochy vrchního kusu přes hlavu (do test_vrstva_dosah_m),
## nesmí ležet vně jeho povrchu víc než test_vrstva_tolerance_m. Vrací [počet, nejvíc m, příklad polohy].
func _vrstva(sit: Dictionary) -> Array:
	var V: Array = sit["v"]
	var vr: PackedInt32Array = sit["vrch"]
	var sp: PackedInt32Array = sit["spod"]
	if vr.is_empty():
		return [0, 0.0, Vector3.ZERO]
	var d := float(R["test_vrstva_dosah_m"])
	var tol := float(R["test_vrstva_tolerance_m"])
	var P := {}
	for i: int in vr:
		if not P.has(i):
			P[i] = _poloha(V[i])
	var mriz := {}
	var F: Array = []
	for t in range(0, vr.size(), 3):
		var a: Vector3 = P[vr[t]]
		var b: Vector3 = P[vr[t + 1]]
		var c: Vector3 = P[vr[t + 2]]
		var n := (b - a).cross(c - a)
		if n.length_squared() < 1e-14:
			continue
		n = n.normalized()
		var nv := _normala(V[vr[t]]) + _normala(V[vr[t + 1]]) + _normala(V[vr[t + 2]])
		if n.dot(nv) < 0.0:
			n = -n
		var fi := F.size()
		F.append([a, b, c, n])
		var lo := Vector3i((a.min(b).min(c) - Vector3.ONE * d) / d)
		var hi := Vector3i((a.max(b).max(c) + Vector3.ONE * d) / d)
		for x in range(lo.x, hi.x + 1):
			for y in range(lo.y, hi.y + 1):
				for z in range(lo.z, hi.z + 1):
					(mriz.get_or_add(Vector3i(x, y, z), []) as Array).append(fi)
	var pocet := 0
	var nej := 0.0
	var kde := Vector3.ZERO
	for i: int in sp:
		var qv := _poloha(V[i])
		for fi: int in mriz.get(Vector3i(qv / d), []):
			var f: Array = F[fi]
			var a: Vector3 = f[0]
			var n: Vector3 = f[3]
			var s := (qv - a).dot(n)
			if absf(s) > d:
				continue
			# kolmý průmět dovnitř trojúhelníku (ne okraj - rukáv v průramku, lem)
			var pr := qv - n * s
			var v0: Vector3 = (f[1] as Vector3) - a
			var v1: Vector3 = (f[2] as Vector3) - a
			var v2 := pr - a
			var d00 := v0.dot(v0)
			var d01 := v0.dot(v1)
			var d11 := v1.dot(v1)
			var d20 := v2.dot(v0)
			var d21 := v2.dot(v1)
			var den := d00 * d11 - d01 * d01
			if den <= 0.0:
				continue
			var bv := (d11 * d20 - d01 * d21) / den
			var bw := (d00 * d21 - d01 * d20) / den
			if bv < 0.0 or bw < 0.0 or bv + bw > 1.0:
				continue
			if s > tol:
				pocet += 1
				if s > nej:
					nej = s
					kde = V[i][0]
			break
	return [pocet, nej, kde]


## Ladeni (TVRZ_SVY_OBJ=slozka): skinovana sit povrchu odevu a tela v dane fazi jako OBJ (rozbor vrstev mimo Godot)
func _obj(sit: Dictionary, jm: String) -> void:
	if not OS.has_environment("TVRZ_SVY_OBJ"):
		return
	var f := FileAccess.open(OS.get_environment("TVRZ_SVY_OBJ").path_join(jm + ".obj"), FileAccess.WRITE)
	if f == null:
		return
	for z: Array in sit["v"]:
		var p := _poloha(z)
		f.store_line("v %.5f %.5f %.5f" % [p.x, p.y, p.z])
	var t: PackedInt32Array = sit["troj"]
	for i in range(0, t.size(), 3):
		f.store_line("f %d %d %d" % [t[i] + 1, t[i + 1] + 1, t[i + 2] + 1])
	f.close()


func _normala(z: Array) -> Vector3:
	var n := Vector3.ZERO
	var uch: Array = z[1]
	for j in uch.size():
		n += ((uch[j] as BoneAttachment3D).global_basis * (z[2][j] as Transform3D).basis * (z[4] as Vector3)) * float(z[3][j])
	return n.normalized()


func _poloha(z: Array) -> Vector3:
	var p := Vector3.ZERO
	var uch: Array = z[1]
	for j in uch.size():
		p += ((uch[j] as BoneAttachment3D).global_transform * (z[2][j] as Transform3D) * (z[0] as Vector3)) * float(z[3][j])
	return p


## [nejvetsi vzdalenost paru, pocet nesvarenych okraju v oblasti, priklad polohy]
func _zmer(sit: Dictionary) -> Array:
	var V: Array = sit["v"]
	var cache := {}
	var pary: PackedInt32Array = sit["pary"]
	var hp := 0.0
	var hp_kde := ""
	for i in range(0, pary.size(), 2):
		var a := pary[i]
		var b := pary[i + 1]
		var pa: Vector3 = cache.get(a) if cache.has(a) else _poloha(V[a])
		var pb: Vector3 = cache.get(b) if cache.has(b) else _poloha(V[b])
		cache[a] = pa
		cache[b] = pb
		if pa.distance_to(pb) > hp:
			hp = pa.distance_to(pb)
			hp_kde = "%s kosti %s / %s" % [(V[a][0] as Vector3).snapped(Vector3.ONE * 0.001), _kosti_txt(V[a]), _kosti_txt(V[b])]
	# mrizka okrajovych vrcholu
	var d := float(R.get("test_sev_dosah_m", 0.03))
	var mr := {}
	for i: int in sit["hranice"]:
		var p: Vector3 = cache.get(i) if cache.has(i) else _poloha(V[i])
		cache[i] = p
		(mr.get_or_add(Vector3i((p / d).floor()), []) as Array).append(i)
	var n := 0
	var pr := Vector3.ZERO
	var okr: Array = sit["okraje"]
	for ei in okr.size():
		var e: Array = okr[ei]
		var m: Vector3 = ((cache[e[0]] as Vector3) + (cache[e[1]] as Vector3)) * 0.5
		var c := Vector3i((m / d).floor())
		var sm: Dictionary = sit["smycka"]
		var moje: int = sm[e[0]]
		var ne := _normala(V[e[0]])
		var hn := float(R.get("test_sev_normala_m", 0.004))
		var nasel := false
		for dx in range(-1, 2):
			for dy in range(-1, 2):
				for dz in range(-1, 2):
					for j: int in mr.get(c + Vector3i(dx, dy, dz), []):
						# protejsek svu = okraj v rovine latky (ne vrstva nad/pod - lem kape nad kotlemi)
						if int(sm[j]) != moje and (cache[j] as Vector3).distance_to(m) < d and absf(((cache[j] as Vector3) - m).dot(ne)) < hn:
							nasel = true
							if OS.has_environment("TVRZ_SVY_LADIT"):
								print("SVY LADIT okraj %s smycka %d / protejsek %s smycka %d, vzdal %.4f, po normale %.4f" % [
									(V[e[0]][0] as Vector3).snapped(Vector3.ONE * 0.001), moje, (V[j][0] as Vector3).snapped(Vector3.ONE * 0.001),
									int(sm[j]), (cache[j] as Vector3).distance_to(m), ((cache[j] as Vector3) - m).dot(ne)])
							break
					if nasel:
						break
				if nasel:
					break
			if nasel:
				break
		if nasel:
			n += 1
			pr = m
	return [hp, n, pr, hp_kde]


func _kosti_txt(z: Array) -> String:
	var s := ""
	for j in (z[1] as Array).size():
		s += "%s:%.2f " % [(z[1][j] as BoneAttachment3D).bone_name, float(z[3][j])]
	return s
