extends RefCounted
## Výpis textur použitých ve scéně (plán z rešerše 17. 11. A2; tablet ukazuje VRAM 938 MB a roste). Godot 4.7 nemá
## v GDScriptu výpis grafické paměti po texturách (RenderingServer.texture_debug_usage není vystavený), proto se projdou
## materiály všech sítí ve scéně (MeshInstance3D, MultiMesh, GPUParticles, material_override i materiály povrchů) a
## textury v nich (StandardMaterial3D, parametry ShaderMaterial). Velikost = šířka × výška × bajty formátu (RenderingServer
## texture_get_format) × 4/3 na mipmapy – ODHAD, ne změřená paměť; skutečný součet je RENDERING_INFO_VIDEO_MEM_USED.
## Zapisuje mereni.gd na konci měření do user://textury_vram.txt (všechny od největší + součet), na PC nástroj nastroje/textury_vram.py.

# bajty na pixel podle Image.Format (Godot 4.7 core/io/image.h); komprimované bloky přepočtené na pixel
const BPP := {0: 1.0, 1: 2.0, 2: 1.0, 3: 2.0, 4: 3.0, 5: 4.0, 6: 2.0, 7: 2.0, 8: 4.0, 9: 8.0, 10: 12.0, 11: 16.0,
	12: 2.0, 13: 4.0, 14: 6.0, 15: 8.0, 16: 4.0, 17: 0.5, 18: 1.0, 19: 1.0, 20: 0.5, 21: 1.0, 22: 1.0, 23: 1.0, 24: 1.0,
	25: 0.5, 26: 0.5, 27: 0.5, 28: 1.0, 29: 1.0, 30: 0.5, 31: 1.0, 32: 0.5, 33: 1.0, 34: 1.0, 35: 1.0, 36: 1.0, 37: 0.25, 38: 0.25}
const JMENA := {0: "L8", 4: "RGB8", 5: "RGBA8", 17: "DXT1", 19: "DXT5", 21: "RGTC_RG", 25: "ETC", 28: "ETC2_RG11",
	30: "ETC2_RGB8", 31: "ETC2_RGBA8", 32: "ETC2_RGB8A1", 35: "ASTC_4x4", 37: "ASTC_8x8"}

static func _textury_materialu(m: Material, out: Dictionary) -> void:
	if m == null: return
	var hodnoty: Array = []
	if m is BaseMaterial3D:
		for p in m.get_property_list():
			if String(p["name"]).ends_with("_texture"): hodnoty.append(m.get(p["name"]))
	elif m is ShaderMaterial and (m as ShaderMaterial).shader:
		for u in (m as ShaderMaterial).shader.get_shader_uniform_list():
			hodnoty.append((m as ShaderMaterial).get_shader_parameter(u["name"]))
	for v in hodnoty:
		if v is Texture2D or v is TextureLayered or v is Texture3D:
			var t := v as Texture
			var k := t.get_instance_id()
			if not out.has(k): out[k] = {"tex": t, "uziti": 0}
			out[k]["uziti"] += 1
	if m.next_pass: _textury_materialu(m.next_pass, out)

static func _site(n: Node, out: Dictionary) -> void:
	var mesh: Mesh = null
	if n is MeshInstance3D:
		mesh = (n as MeshInstance3D).mesh
		for i in (n as MeshInstance3D).get_surface_override_material_count():
			_textury_materialu((n as MeshInstance3D).get_surface_override_material(i), out)
	elif n is MultiMeshInstance3D and (n as MultiMeshInstance3D).multimesh:
		mesh = (n as MultiMeshInstance3D).multimesh.mesh
	elif n is GPUParticles3D:
		mesh = (n as GPUParticles3D).draw_pass_1
	if n is GeometryInstance3D: _textury_materialu((n as GeometryInstance3D).material_override, out)
	if mesh:
		for i in mesh.get_surface_count(): _textury_materialu(mesh.surface_get_material(i), out)

static func seznam(koren: Node) -> Array:
	var out := {}
	if koren == null: return []
	_site(koren, out)
	for n in koren.find_children("*", "GeometryInstance3D", true, false): _site(n, out)
	var a: Array = []
	for k in out:
		var t: Texture = out[k]["tex"]
		var w := 0; var h := 0; var vrstev := 1
		if t is Texture2D: w = (t as Texture2D).get_width(); h = (t as Texture2D).get_height()
		elif t is TextureLayered: w = (t as TextureLayered).get_width(); h = (t as TextureLayered).get_height(); vrstev = (t as TextureLayered).get_layers()
		elif t is Texture3D: w = (t as Texture3D).get_width(); h = (t as Texture3D).get_height(); vrstev = (t as Texture3D).get_depth()
		var f := RenderingServer.texture_get_format(t.get_rid()) if t.get_rid().is_valid() else -1
		var mb := w * h * vrstev * float(BPP.get(f, 4.0)) * 4.0 / 3.0 / 1048576.0
		a.append({"cesta": t.resource_path if t.resource_path != "" else "(%s bez cesty)" % t.get_class(), "w": w, "h": h, "vrstev": vrstev,
			"format": JMENA.get(f, str(f)), "mb": mb, "uziti": out[k]["uziti"]})
	a.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return float(x["mb"]) > float(y["mb"]))
	return a

## Zapíše výpis do souboru, vrátí jeden řádek souhrnu do výsledku měření.
static func zapis(koren: Node, soubor: String, kolik := 100000) -> String:   # všechny, od největší (prvních 30 = tabulka)
	var a := seznam(koren)
	var celk := 0.0
	for x in a: celk += float(x["mb"])
	var vram := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0
	var tex := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED) / 1048576.0
	var txt := "textury ve scéně: %d, odhad %.0f MB (VRAM celkem %.0f MB, z toho textury %.0f MB podle Godotu)\n" % [a.size(), celk, vram, tex]
	txt += "   MB  šířka×výška  vrstev  formát       užití  cesta\n"
	for i in mini(kolik, a.size()):
		var x: Dictionary = a[i]
		txt += "%6.1f  %5d×%-5d  %6d  %-11s %6d  %s\n" % [x["mb"], x["w"], x["h"], x["vrstev"], x["format"], x["uziti"], x["cesta"]]
	var f := FileAccess.open(soubor, FileAccess.WRITE)
	if f: f.store_string(txt); f.close()
	return "textury ve scéně %d, odhad %.0f MB, Godot textury %.0f MB (výpis %s)" % [a.size(), celk, tex, soubor]
