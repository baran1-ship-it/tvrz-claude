extends Node
## Testy staveb a predmetu (Misa 6. 11., radky 49, 55, 56, 60, 62, 67-69 tabulky misa_28_chyby.md) - samostatna sada
## vedle tools/test_svet.gd (ten upravuje jiny pomocnik). Spousti dev_test.gd v rezimu svet po test_svet.gd se stejnym
## TVRZ_TEST_JEN: tools/beh.sh jm testy "co_je,klobouky,..." ; vystup TEST <jmeno> OK/CHYBA, souhrn TEST STAVBY.
##   co_je      diagnostika: TVRZ_BODY="x,z;..." - vybaveni, site, multimeshe a stavby u bodu (co je to za objekt)
##   klobouky   r. 67: site bez textury 0,3-4 m (hnede polokoule v trave) - kolik, kde, jaky material
##   schody     r. 69: chuze po schodech dilu (*Kol_Schody*: mlyn, vetrny mlyn) nahoru i dolu bez skoku; zebrikove
##              schody (strmejsi nez hrac.json schody_zebrik_nad_st) lezenim nahoru i dolu
##   zebriky_jeden r. 55: k jednomu otvoru jeden zebrik (katalogovy zebrik ne vedle zebriku modelu, vystupy > 1,5 m od sebe)
##   dil_na_teren r. 56: kusy siti dilu (voda.json mlyn.dil na_teren_dilu, obruba cesty k mlynu) nejsou zapadle v terenu
##   opreny_o_zed r. 68: metla (a kus nabytek.json s "o_zed") neleze nalezato - stoji opreny o zed
##   nocleh_pred_zdi kontrola 9. 11.: nocleh slepic u chalupy pred licem zdi (koule tela mimo kolizi zdi)
##   stavby_vse_na_zemi r. 60/77: spodek kazde pevne stavby z katalogu (stodoly, kulny...) nejvys pasma.budova.na_zemi_m nad terenem

const Pravidla := preload("res://scripts/pravidla.gd")
var main: Node
var player: CharacterBody3D
var sv
var vysledky: Array = []
const TESTY := ["co_je", "klobouky", "schody", "zebriky_jeden", "opreny_o_zed", "dil_na_teren", "stavby_vse_na_zemi", "nocleh_pred_zdi"]


func run(p_main: Node) -> void:
	main = p_main
	player = main.player
	sv = main.svet
	var jen := OS.get_environment("TVRZ_TEST_JEN").split(",", false)
	var nic := true
	for t: String in TESTY:
		if jen.has(t):
			nic = false
			await call("_" + t)
	if nic:
		return
	var ok := true
	print("TEST STAVBY ------------------------------")
	for v: Array in vysledky:
		print("TEST %-14s %s  %s" % [v[0], "OK   " if v[1] else "CHYBA", v[2]])
		ok = ok and bool(v[1])
	print("TEST STAVBY %s" % ("PROSEL" if ok else "NEPROSEL"))


func _vysledek(nazev: String, ok: bool, text: String) -> void:
	vysledky.append([nazev, ok, text])


func _cesta(n: Node) -> String:
	return String(main.get_path_to(n)) if main.is_ancestor_of(n) else String(n.get_path())


func _mat_popis(g: GeometryInstance3D, mesh: Mesh) -> String:
	var s := []
	for si in mini(mesh.get_surface_count(), 4):
		var mt: Material = g.material_override
		if mt == null and g is MeshInstance3D:
			mt = (g as MeshInstance3D).get_active_material(si)
		if mt == null:
			mt = mesh.surface_get_material(si)
		var d := "nic"
		if mt is BaseMaterial3D:
			var bm := mt as BaseMaterial3D
			d = "%s tex=%s barva=%s vc=%s" % [mt.resource_name, bm.albedo_texture != null, bm.albedo_color.to_html(false), bm.vertex_color_use_as_albedo]
		elif mt is ShaderMaterial:
			d = "%s sh=%s" % [mt.resource_name, (mt as ShaderMaterial).shader.resource_path.get_file() if (mt as ShaderMaterial).shader else "?"]
		s.append(d)
	return str(s)


## Diagnostika (Misa: „co je to za objekt“): pro kazdy bod TVRZ_BODY vypise vse v okruhu r (TVRZ_BOD_R, 4 m).
func _co_je() -> void:
	var r := float(OS.get_environment("TVRZ_BOD_R")) if OS.has_environment("TVRZ_BOD_R") else 4.0
	for b: String in OS.get_environment("TVRZ_BODY").split(";", false):
		var xz := b.split(",")
		var q := Vector2(float(xz[0]), float(xz[1]))
		print("CO_JE bod %s (r %.1f) teren %.2f" % [q, r, sv._vyska(q.x, q.y)])
		# vsechny kolize nad sebou (paprsek shora, po zasahu dal)
		var space := player.get_world_3d().direct_space_state
		var od := Vector3(q.x, 200.0, q.y)
		var ex: Array[RID] = []
		var zas: Array = []
		for k in 8:
			var rq := PhysicsRayQueryParameters3D.create(od, Vector3(q.x, -100.0, q.y))
			rq.exclude = ex
			var h := space.intersect_ray(rq)
			if h.is_empty():
				break
			zas.append("%.2f %s" % [(h["position"] as Vector3).y, _cesta(h["collider"] as Node).right(60)])
			ex.append((h["collider"] as CollisionObject3D).get_rid())
		print("CO_JE  kolize shora %s" % str(zas))
		if OS.has_environment("TVRZ_CO_JE_KRATCE"):
			var hl: Array = []
			for n3 in main.find_children("*", "MeshInstance3D", true, false):
				var mi3 := n3 as MeshInstance3D
				if mi3.mesh == null:
					continue
				var ab3 := mi3.global_transform * mi3.mesh.get_aabb()
				if q.x < ab3.position.x or q.x > ab3.end.x or q.y < ab3.position.z or q.y > ab3.end.z:
					continue
				var f3 := mi3.mesh.get_faces()
				for t3 in f3.size() / 3:
					var h3 = Geometry3D.ray_intersects_triangle(Vector3(q.x, 500.0, q.y), Vector3.DOWN, mi3.global_transform * f3[t3 * 3], mi3.global_transform * f3[t3 * 3 + 1], mi3.global_transform * f3[t3 * 3 + 2])
					if h3 != null:
						hl.append("%s %.2f" % [String(mi3.name).left(24), (h3 as Vector3).y])
			print("CO_JE  povrchy %s" % str(hl))
			continue
		# site, jejichz trojuhelnik lezi nad/pod bodem (do 0,3 m vodorovne): vyska trojuhelniku
		for n2 in main.find_children("*", "MeshInstance3D", true, false):
			var mi2 := n2 as MeshInstance3D
			if mi2.mesh == null or not mi2.is_visible_in_tree():
				continue
			var ab2 := mi2.global_transform * mi2.mesh.get_aabb()
			if q.x < ab2.position.x or q.x > ab2.end.x or q.y < ab2.position.z or q.y > ab2.end.z:
				continue
			var f := mi2.mesh.get_faces()
			var ys: Array = []
			for t in f.size() / 3:
				var ta := mi2.global_transform * f[t * 3]
				var tb := mi2.global_transform * f[t * 3 + 1]
				var tc := mi2.global_transform * f[t * 3 + 2]
				var hit = Geometry3D.ray_intersects_triangle(Vector3(q.x, 500.0, q.y), Vector3.DOWN, ta, tb, tc)
				if hit != null:
					ys.append(snappedf((hit as Vector3).y, 0.01))
			if not ys.is_empty():
				print("CO_JE  povrch %s: y %s" % [_cesta(mi2).right(70), str(ys.slice(0, 6))])
		for v: Dictionary in sv.data.get("vybaveni", []):
			var p: Array = v["p"]
			if Vector2(float(p[0]), float(p[2])).distance_to(q) < r:
				print("CO_JE  vybaveni %s" % str(v))
		for d: Dictionary in sv._domy:
			var o: Vector3 = (d["xf"] as Transform3D).origin
			if Vector2(o.x, o.z).distance_to(q) < r + 12.0:
				print("CO_JE  dum %s_%s xf %s m %s" % [d.get("typ", "?"), d.get("k", "?"), d["xf"], str(d["m"]).left(300)])
		for n in main.find_children("*", "GeometryInstance3D", true, false):
			var g := n as GeometryInstance3D
			if not g.is_visible_in_tree():
				continue
			if g is MeshInstance3D and (g as MeshInstance3D).mesh:
				var mi := g as MeshInstance3D
				var ab := mi.global_transform * mi.mesh.get_aabb()
				if ab.size.x > 300.0 or ab.size.z > 300.0:
					continue
				if q.x > ab.position.x - 0.5 and q.x < ab.end.x + 0.5 and q.y > ab.position.z - 0.5 and q.y < ab.end.z + 0.5:
					print("CO_JE  sit %s mesh %s aabb %s xf.basis %s %s" % [_cesta(mi), mi.mesh.resource_name, ab, mi.global_transform.basis, _mat_popis(mi, mi.mesh)])
			elif g is MultiMeshInstance3D and (g as MultiMeshInstance3D).multimesh:
				var mm := (g as MultiMeshInstance3D).multimesh
				if mm.mesh == null or mm.transform_format != MultiMesh.TRANSFORM_3D:
					continue
				var n_bl := 0
				for i in mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count:
					var xf := g.global_transform * mm.get_instance_transform(i)
					if Vector2(xf.origin.x, xf.origin.z).distance_to(q) < r:
						n_bl += 1
						if n_bl <= 6:
							var ab2 := xf * mm.mesh.get_aabb()
							print("CO_JE  multimesh %s mesh %s i %d xf %s aabb %s %s" % [_cesta(g), mm.mesh.resource_name, i, xf, ab2, _mat_popis(g, mm.mesh)])
				if n_bl > 6:
					print("CO_JE  multimesh %s ... celkem %d" % [_cesta(g), n_bl])
	_vysledek("co_je", true, "diagnostika")


## Hnede „klobouky“ (Misa 0.99994 r. 67, snimek misa_6_11/47): kazda sit / multimesh bez textury a bez barvy vrcholu
## (jednobarevny material) a velka 0,3-4 m - po jmenu site, kolik a kde.
func _klobouky() -> void:
	var skup := {}
	for n in main.find_children("*", "GeometryInstance3D", true, false):
		var g := n as GeometryInstance3D
		if not g.is_visible_in_tree():
			continue
		var mesh: Mesh = null
		var xfs: Array = []
		if g is MeshInstance3D:
			mesh = (g as MeshInstance3D).mesh
			xfs = [g.global_transform]
		elif g is MultiMeshInstance3D and (g as MultiMeshInstance3D).multimesh:
			var mm := (g as MultiMeshInstance3D).multimesh
			mesh = mm.mesh
			if mm.transform_format == MultiMesh.TRANSFORM_3D:
				for i in mm.instance_count:
					xfs.append(g.global_transform * mm.get_instance_transform(i))
		if mesh == null or xfs.is_empty():
			continue
		var bez := false
		for si in mesh.get_surface_count():
			var mt: Material = g.material_override
			if mt == null and g is MeshInstance3D:
				mt = (g as MeshInstance3D).get_active_material(si)
			if mt == null:
				mt = mesh.surface_get_material(si)
			if mt == null or (mt is BaseMaterial3D and (mt as BaseMaterial3D).albedo_texture == null and not (mt as BaseMaterial3D).vertex_color_use_as_albedo):
				bez = true
		if not bez:
			continue
		for xf: Transform3D in xfs:
			var ab := xf * mesh.get_aabb()
			var m := maxf(ab.size.x, ab.size.z)
			if m < 0.3 or m > 4.0 or ab.size.y > 3.0:
				continue
			var k := "%s | %s" % [mesh.resource_name, _cesta(g).left(80)]
			if not skup.has(k):
				skup[k] = [0, [], _mat_popis(g, mesh), ab.size]
			skup[k][0] += 1
			if (skup[k][1] as Array).size() < 4:
				(skup[k][1] as Array).append(Vector3(ab.get_center().x, ab.position.y, ab.get_center().z).snapped(Vector3.ONE * 0.1))
	for k: String in skup:
		print("KLOBOUKY %s: %d x, velikost %s, napr. %s, material %s" % [k, skup[k][0], skup[k][3], str(skup[k][1]), skup[k][2]])
	# jen diagnostika (9. 11.): bez textury jsou i kovani dveri, provazy a vedra - polokouli to nenaslo; MultiMesh (rostliny,
	# houby) headless nevidi (dummy renderer vraci transformace instanci nulove) - rozbor v docs/predani.md
	_vysledek("klobouky", true, "diagnostika: %d druhu siti bez textury 0,3-4 m: %s" % [skup.size(), str(skup.keys()).left(300)])


## Schody dilu (Misa 0.99994 r. 69, snimek misa_6_11/50: „nahoru vybehne, dolu jen skokem“): pro kazde *Kol_Schody*
## (kvadry schodu ze svet._schody_kolize) hrac jde od paty nahoru a shora dolu jen packou (bez skoku), dvere dilu otevrene.
func _schody() -> void:
	var pg: Node = main.get("pohyb")
	if pg:
		for gid: String in (pg.get("groups") as Dictionary):
			if (gid.begins_with("vetrak") or gid.begins_with("mlyn")) and float(pg.get("groups")[gid]["target"]) < 0.5:
				pg.toggle(gid)
	for i in 120:
		await get_tree().physics_frame
	var spatne: Array = []
	var n := 0
	for sb in main.find_children("*Kol_Schody*", "CollisionObject3D", true, false):
		var boxy: Array = []
		for cs in (sb as Node).find_children("*", "CollisionShape3D", true, false):
			var c := cs as CollisionShape3D
			if c.disabled or not (c.shape is BoxShape3D):
				continue
			boxy.append([(c.shape as BoxShape3D).size.y, c.global_transform])
		if boxy.size() < 2:
			continue
		boxy.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) < float(b[0]))
		var dolni: Transform3D = boxy[0][1]
		var horni: Transform3D = boxy[-1][1]
		var smer := Vector3(horni.origin.x - dolni.origin.x, 0.0, horni.origin.z - dolni.origin.z).normalized()
		var vrch := horni.origin.y + float(boxy[-1][0]) * 0.5
		var pata := dolni.origin.y - float(boxy[0][0]) * 0.5
		var start := dolni.origin - smer * 0.45
		var cil := horni.origin + smer * 0.9
		n += 1
		# zebrikove schody (hrac.json schody_zebrik_nad_st): zaznam pouziti zebrik u paty - lezeni nahoru i dolu
		var zb: Dictionary = {}
		for u: Dictionary in main.info["use"]:
			if String(u.get("kind", "")) == "zebrik" and not bool(u["nahore"]) and Vector2((u["zb"]["pata"] as Vector3).x - dolni.origin.x, (u["zb"]["pata"] as Vector3).z - dolni.origin.z).length() < 0.6:
				zb = u["zb"]
		var nahoru: Array
		var dolu: Array
		if not zb.is_empty():
			nahoru = await _lez(zb, true)
			dolu = await _lez(zb, false)
		else:
			nahoru = await _chuze(Vector3(start.x, pata + 0.3, start.z), smer, 8.0, cil, vrch)
			dolu = await _chuze(Vector3(cil.x, vrch + 0.3, cil.z), -smer, 8.0, start, pata)
		var txt := "%s: pata %.2f vrch %.2f, nahoru %s, dolu %s" % [sb.name, pata, vrch, str(nahoru), str(dolu)]
		print("SCHODY " + txt)
		if not (bool(nahoru[0]) and bool(dolu[0])):
			spatne.append(txt)
	_vysledek("schody", spatne.is_empty() and n > 0, "%d schodist, spatne %s" % [n, str(spatne)])


## Lezeni po zebrikovych schodech: nahoru od nastupu az na sestup, dolu od sestupu az na nastup (jen packa).
func _lez(zb: Dictionary, nahoru: bool) -> Array:
	player.flying = false
	player.global_position = (zb["nastup"] if nahoru else zb["sestup"]) as Vector3
	await get_tree().physics_frame
	player.climb(zb, not nahoru)
	player.move_input = Vector2(0, 1 if nahoru else -1)
	var k := 0
	while k < 600 and player.climbing:
		await get_tree().physics_frame
		k += 1
	player.move_input = Vector2.ZERO
	for i in 30:
		await get_tree().physics_frame
	var cil: Vector3 = zb["sestup"] if nahoru else zb["nastup"]
	var p := player.global_position
	# cil = podlaha u nastupu/sestupu (hrac stoji na podlaze, ne v ni): do 0,45 m nad bodem zaznamu
	return [not player.climbing and player.is_on_floor() and p.y - cil.y > -0.1 and p.y - cil.y < 0.45 and Vector2(p.x - cil.x, p.z - cil.z).length() < 1.0, "lezeni", p.snapped(Vector3.ONE * 0.01), "%.1f s" % (k / 60.0)]


## Chuze packou smerem smer max t s: [dosel (vodorovne do 0,4 m od cile a vyska do 0,3 m od cil_y), konecna poloha, cas].
func _chuze(od: Vector3, smer: Vector3, t: float, cil: Vector3, cil_y: float) -> Array:
	player.flying = false
	player.global_position = od
	player.velocity = Vector3.ZERO
	player.yaw = atan2(-smer.x, -smer.z)
	await get_tree().physics_frame
	var k := 0
	var ok := false
	while k < int(t * 60.0):
		player.move_input = Vector2(0, 1)
		player.yaw = atan2(-smer.x, -smer.z)
		await get_tree().physics_frame
		k += 1
		var p := player.global_position
		if Vector2(p.x - cil.x, p.z - cil.z).length() < 0.4 or (p - od).dot(smer) > (cil - od).dot(smer):
			ok = true
			break
	player.move_input = Vector2.ZERO
	# dosednout (pri chuzi dolu je hrac mezi schody chvili ve vzduchu)
	for i in 40:
		await get_tree().physics_frame
	ok = ok and player.is_on_floor() and absf(player.global_position.y - cil_y) < 0.35
	return [ok, player.global_position.snapped(Vector3.ONE * 0.01), "%.1f s" % (k / 60.0)]


## Jeden zebrik na otvor (Misa 0.99993 r. 55, snimky 24-25 „dva zebriky v mlyne“): u kazdeho zaznamu zebriku
## (pouziti) nesmi byt vedle zebriku modelu (dil zebrik_v_modelu) jeste katalogovy zebrik a dva zaznamy nesmi mit
## vystup (vrchol) blize nez 1,5 m.
func _zebriky_jeden() -> void:
	var zbs: Array = []
	for u: Dictionary in main.info["use"]:
		if String(u.get("kind", "")) == "zebrik" and not bool(u["nahore"]):
			zbs.append(u["zb"])
	var spatne: Array = []
	for i in zbs.size():
		for j in range(i + 1, zbs.size()):
			if (zbs[i]["vrchol"] as Vector3).distance_to(zbs[j]["vrchol"]) < 1.5:
				spatne.append("dva zebriky k vystupu %s" % (zbs[i]["vrchol"] as Vector3).snapped(Vector3.ONE * 0.1))
	var ml: Dictionary = Pravidla.cti("voda", "mlyn", "dil")
	var kat := main.find_children("Mlyn_zebrik", "Node3D", true, false)
	if bool(ml.get("zebrik_v_modelu", false)) and not kat.is_empty():
		spatne.append("mlyn: zebrik modelu i katalogovy Mlyn_zebrik")
	# zaznam mlyna lezi na zebriku modelu: stred useku pata-vrchol do 0,25 m od nejakeho vrcholu site interieru mlyna
	var xf := Transform3D(Basis(Vector3.UP, float(ml["natoceni"])), Vector3(float(ml["stred"][0]), float(ml["y_dvora"]), float(ml["stred"][1])))
	var z: Array = ml["zebrik"]
	var st := xf * ((Vector3(float(z[0][0]), float(z[0][1]), float(z[0][2])) + Vector3(float(z[1][0]), float(z[1][1]), float(z[1][2]))) * 0.5)
	var nejbl := INF
	for mi in main.find_children("Mlyn_Interier*", "MeshInstance3D", true, false):
		var g := mi as MeshInstance3D
		for v: Vector3 in g.mesh.get_faces():
			nejbl = minf(nejbl, (g.global_transform * v).distance_to(st))
	if bool(ml.get("zebrik_v_modelu", false)) and nejbl > 0.25:
		spatne.append("mlyn: zaznam zebriku %.2f m od site zebriku modelu" % nejbl)
	_vysledek("zebriky_jeden", spatne.is_empty() and zbs.size() > 0, "%d zebriku, mlyn: katalogovy %d, zaznam od site modelu %.2f m, spatne %s" % [zbs.size(), kat.size(), nejbl, str(spatne)])


## Opreny o zed (Misa 0.99994 r. 68, snimek 49 „metla v kazde chalupe lezi na zemi“): kazda metla ve svete a kazdy
## kus s o_zed ma naklon od svisle v mezich pasma.predmet (opreny_uhel_st), ne nalezato.
func _opreny_o_zed() -> void:
	var pp: Dictionary = sv.pasma()["predmet"]
	var aa: Array = pp["opreny_uhel_st"]
	var spatne: Array = []
	var n := 0
	for v: Dictionary in sv.data.get("vybaveni", []):
		if String(v["id"]) != "metla" and not v.has("o_zed"):
			continue
		n += 1
		var up: Array = v.get("up", [])
		var uhel := 90.0 if up.is_empty() else rad_to_deg(acos(clampf(float(up[1]) / Vector3(float(up[0]), float(up[1]), float(up[2])).length(), -1.0, 1.0)))
		if up.is_empty() or int(v.get("orient", 0)) == 0 and String(v["id"]) == "metla" or uhel < float(aa[0]) or uhel > float(aa[1]):
			spatne.append("%s %s naklon %.0f st." % [v["id"], str(v["p"]).left(40), uhel])
	_vysledek("opreny_o_zed", spatne.is_empty() and n > 0, "%d kusu (metla, o_zed), spatne %d %s" % [n, spatne.size(), str(spatne.slice(0, 5))])


## Kusy siti dilu na terenu (Misa 0.99993 r. 56, snimek 26 (602,931) „kuly lezi na zemi, rozsypane“ = obruba cesty
## Mlyn_Cesta zapadla v terenu dilu): lezici kus nesmi mit stred pod terenem dilu, kolik musi vycnivat.
func _dil_na_teren() -> void:
	var ml: Dictionary = Pravidla.cti("voda", "mlyn", "dil")
	var pp: Dictionary = sv.pasma()["dil_na_teren"]
	var spatne: Array = []
	var n := 0
	for jm: String in ml.get("na_teren_dilu", []):
		for mi0 in main.find_children(jm, "MeshInstance3D", true, false):
			var mi := mi0 as MeshInstance3D
			var xf := mi.global_transform
			var arrs: Array = []
			for si in mi.mesh.get_surface_count():
				arrs.append(mi.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX])
			for kus: Array in sv._souvisle_kusy(mi.mesh):
				var lo := INF
				var hi := -INF
				var c := Vector3.ZERO
				for sv2: Vector2i in kus:
					var w := xf * (arrs[sv2.x] as PackedVector3Array)[sv2.y]
					lo = minf(lo, w.y)
					hi = maxf(hi, w.y)
					c += w
				c /= maxf(kus.size(), 1)
				var t: float = sv.mlyn_teren(c.x, c.z).x
				if t == INF:
					continue
				n += 1
				var lezi := hi - lo < float(pp["kul_vyska_m"])
				if (lezi and (lo + hi) * 0.5 < t) or (not lezi and hi < t + float(pp["kul_vycniva_m"]) * 0.5):
					spatne.append("%s %s %s y %.2f..%.2f teren %.2f" % [jm, "kus" if lezi else "kolik", c.snapped(Vector3.ONE * 0.1), lo, hi, t])
	_vysledek("dil_na_teren", spatne.is_empty() and n > 0, "%d kusu, zapadlych %d %s" % [n, spatne.size(), str(spatne.slice(0, 5))])


## Stavby na zemi (Misa r. 60 (447,924) a r. 77 (459,907) „stodola a kulna na patkach nad terenem, mezera pod nimi“):
## test_svet stavby_na_zemi hlida jen domy (_domy) - tady kazda pevna stavba z katalogu (vybaveni: stodoly, kulny,
## pristresky, kurnik, stan...; pudorys >= 3 m a vyska >= 2 m). Spodek modelu (vrcholy do 5 cm nad nejnizsim, shluky po
## 0,5 m = patky, prah, sloupy) nad terenem (kolize Teren*, paprsek shora) nejvys pasma.budova.na_zemi_m.
func _stavby_vse_na_zemi() -> void:
	var mez := float(sv.pasma()["budova"]["na_zemi_m"])
	var space := player.get_world_3d().direct_space_state
	var spatne: Array = []
	var n_st := 0
	var n_b := 0
	for rec: Dictionary in main.predmety.placed:
		if not bool(rec.get("pevne", false)) or not rec.has("node"):
			continue
		var rz: Array = (main.predmety.kat.get(String(rec["id"]), {}) as Dictionary).get("rozmer", [0.0, 0.0, 0.0])
		if maxf(float(rz[0]), float(rz[2])) < 3.0 or float(rz[1]) < 2.0:
			continue
		var nd := rec["node"] as Node3D
		var inv := nd.global_transform.affine_inverse()
		var body: Array = []
		var lo := INF
		for mi0 in nd.find_children("*", "MeshInstance3D", true, false):
			var mi := mi0 as MeshInstance3D
			if mi.mesh == null or not mi.is_visible_in_tree():
				continue
			var xf := inv * mi.global_transform
			for v: Vector3 in mi.mesh.get_faces():
				var l := xf * v
				body.append(l)
				lo = minf(lo, l.y)
		if body.is_empty():
			continue
		n_st += 1
		var shl := {}
		for l: Vector3 in body:
			if l.y < lo + 0.05:
				shl[Vector2i(roundi(l.x * 2.0), roundi(l.z * 2.0))] = true
		var nejhur := -INF
		var kde := Vector3.ZERO
		for c: Vector2i in shl:
			var w := nd.global_transform * Vector3(c.x * 0.5, lo, c.y * 0.5)
			var q := PhysicsRayQueryParameters3D.create(Vector3(w.x, w.y + 30.0, w.z), Vector3(w.x, w.y - 30.0, w.z))
			var ex: Array[RID] = [player.get_rid()]
			q.exclude = ex
			var g := INF
			for k in 10:
				var h := space.intersect_ray(q)
				if h.is_empty():
					break
				if String((h["collider"] as Node).name).contains("Teren"):
					g = float((h["position"] as Vector3).y)
					break
				ex.append((h["collider"] as CollisionObject3D).get_rid())
				q.exclude = ex
			if g == INF:
				continue
			n_b += 1
			if w.y - g > nejhur:
				nejhur = w.y - g
				kde = w
		if nejhur > mez:
			spatne.append("%s (%.0f,%.0f) spodek %.2f m nad terenem" % [rec["id"], kde.x, kde.z, nejhur])
	_vysledek("stavby_vse_na_zemi", spatne.is_empty() and n_b > 0, "%d staveb, %d bodu spodku, nad terenem > %.2f m: %d %s" % [n_st, n_b, mez, spatne.size(), str(spatne.slice(0, 8))])


## Nocleh slepic pred zdi (nezavisla kontrola 9. 11.: slepice mizela v lici zdi chalupy): misto noclehu dvora bez kurniku
## (svet._ohrady) - koule tela slepice (polomer 0,2 m, 0,25 m nad zemi) nesmi zasahovat do kolize zdi ani podezdivky.
func _nocleh_pred_zdi() -> void:
	await main.fast_travel(Vector3(440.0, 0.0, 820.0), Vector3(440.0, 1.6, 810.0), 0.0, "test")      # kolize vsi kolem hrace
	for _i in 120:
		await get_tree().physics_frame
	var space := player.get_world_3d().direct_space_state
	var koule := SphereShape3D.new()
	koule.radius = 0.2
	var spatne: Array = []
	var n := 0
	for z: Dictionary in sv.data.get("zvirata", []):
		if not z.has("nocleh"):
			continue
		var q := Vector2(float(z["nocleh"][0]), float(z["nocleh"][1]))
		var ku := false
		for v: Dictionary in sv.data.get("vybaveni", []):
			if String(v["id"]) == "kurnik" and Vector2(float(v["p"][0]), float(v["p"][2])).distance_to(q) < 0.1:
				ku = true                         # do kurniku slepice vejde dvirky - nocleh je jeho stred
		if ku:
			continue
		n += 1
		var pq := PhysicsShapeQueryParameters3D.new()
		pq.shape = koule
		pq.transform = Transform3D(Basis(), Vector3(q.x, sv._vyska(q.x, q.y) + 0.25, q.y))
		pq.exclude = [player.get_rid()]
		var zasahy: Array = []
		for h: Dictionary in space.intersect_shape(pq, 8):
			var nm := String((h["collider"] as Node).name)
			if not nm.contains("Teren"):
				zasahy.append(nm.left(30))
		if not zasahy.is_empty():
			spatne.append("%s nocleh %s v %s" % [z["id"], q.snapped(Vector2.ONE * 0.1), str(zasahy)])
	_vysledek("nocleh_pred_zdi", spatne.is_empty() and n > 0, "%d noclehu u zdi, ve zdi %d %s" % [n, spatne.size(), str(spatne.slice(0, 5))])
