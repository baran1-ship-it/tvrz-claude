extends Node
## Testy staveb a predmetu (Misa 6. 11., radky 49, 55, 56, 60, 62, 67-69 tabulky misa_28_chyby.md) - samostatna sada
## vedle tools/test_svet.gd (ten upravuje jiny pomocnik). Spousti dev_test.gd v rezimu svet po test_svet.gd se stejnym
## TVRZ_TEST_JEN: tools/beh.sh jm testy "co_je,klobouky,..." ; vystup TEST <jmeno> OK/CHYBA, souhrn TEST STAVBY.
##   co_je      diagnostika: TVRZ_BODY="x,z;..." - vybaveni, site, multimeshe a stavby u bodu (co je to za objekt)

const Pravidla := preload("res://scripts/pravidla.gd")
var main: Node
var player: CharacterBody3D
var sv
var vysledky: Array = []
const TESTY := ["co_je", "klobouky"]


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
	_vysledek("klobouky", skup.is_empty(), "%d druhu siti bez textury 0,3-4 m: %s" % [skup.size(), str(skup.keys()).left(400)])
