extends SceneTree
## Barvy vrcholů lůžek modeláře (COLOR_0 z glTF = lineární) → sRGB pro renderer Compatibility (chyby.md 356).
## Compatibility násobí albedo (textura × albedo_color × COLOR) v sRGB a teprve výsledek převede do lineárního prostoru
## (scene.glsl „albedo = srgb_to_linear(albedo)“; vertex_color_is_srgb tam nic nedělá) → lineární barva vrcholu se vzala
## jako sRGB a ztmavla (béžová 0,34 → 0,095: houně a přikrývka chudé postele téměř černé).
## Volá nastroje/luzka_modely.py: -- <značka> <zpráva.json> <res://…_mesh.res>… ; převede jen sítě bez metadat <značka>
## (opakovaně nic nezmění); do zprávy zapíše u každé sítě značku, velikost souboru a průměrnou barvu vrcholů (test smysl:luzka_barvy).
## Mění jen proud atributů (barva RGBA8 + UV) – vrcholy, indexy, AABB a LOD zůstanou.
func _initialize() -> void:
	var a := OS.get_cmdline_user_args()
	var znacka := StringName(a[0]); var prevedeno := 0; var zprava := {}
	for c in a.slice(2):
		var m := ResourceLoader.load(c, "", ResourceLoader.CACHE_MODE_IGNORE) as ArrayMesh
		if m == null: print("LUZKA_BARVY_CHYBA nelze načíst ", c); quit(1); return
		if m.has_meta(znacka):
			zprava[c] = _zaznam(m, c, znacka); continue
		var su: Array = m.get("_surfaces")
		for i in m.get_surface_count():
			var fmt := m.surface_get_format(i)
			if not (fmt & Mesh.ARRAY_FORMAT_COLOR): continue
			var ar := m.surface_get_arrays(i)
			var col: PackedColorArray = ar[Mesh.ARRAY_COLOR]
			for k in col.size(): col[k] = col[k].linear_to_srgb()
			ar[Mesh.ARRAY_COLOR] = col
			var t := ArrayMesh.new()
			t.add_surface_from_arrays(m.surface_get_primitive_type(i), ar, [], {}, fmt & Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES)
			var nove: PackedByteArray = (t.get("_surfaces") as Array)[0]["attribute_data"]
			if nove.size() != (su[i]["attribute_data"] as PackedByteArray).size():
				print("LUZKA_BARVY_CHYBA jiná délka atributů ", c, " ", i); quit(1); return
			su[i]["attribute_data"] = nove
		m.set("_surfaces", su)
		m.set_meta(znacka, true)
		var e := ResourceSaver.save(m, c, ResourceSaver.FLAG_COMPRESS)   # jako sítě modeláře (RSCC)
		if e != OK: print("LUZKA_BARVY_CHYBA uložení ", c, " ", e); quit(1); return
		prevedeno += 1; zprava[c] = _zaznam(m, c, znacka)
	var f := FileAccess.open(a[1], FileAccess.WRITE); f.store_string(JSON.stringify(zprava, " ")); f.close()
	print("LUZKA_BARVY převedeno %d sítí z %d" % [prevedeno, a.size() - 2])
	quit()


func _zaznam(m: ArrayMesh, c: String, znacka: StringName) -> Dictionary:
	var s := Vector3(); var n := 0
	for i in m.get_surface_count():
		if not (m.surface_get_format(i) & Mesh.ARRAY_FORMAT_COLOR): continue
		for x: Color in m.surface_get_arrays(i)[Mesh.ARRAY_COLOR]: s += Vector3(x.r, x.g, x.b); n += 1
	s /= maxi(n, 1)
	return {"srgb": m.has_meta(znacka), "velikost": FileAccess.get_file_as_bytes(c).size(), "vrcholu_s_barvou": n, "barva_prumer": [snappedf(s.x, 0.001), snappedf(s.y, 0.001), snappedf(s.z, 0.001)]}
