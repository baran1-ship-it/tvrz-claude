extends SceneTree
## Stavby z datových balíků Havrana (z_ves, z_mlyn) → glb pro Puchart (nastroje/stavby_z_havrana.sh).
## Textury zmenšené (albedo 1024, normála 512, bez roughness/metallic – rozpočet tabletu, Havran ves_domy.py „max 1024“).
const OUT := "OUT/"
const SOUBORY := ["res://modely/ves/domy.glb", "res://modely/ves/domy_stredni.glb", "res://modely/mlyn/mlyn.glb", "res://modely/mlyn/mlyn_lod1.glb",
	"res://modely/rostliny/jablon.glb", "res://modely/rostliny/jablon_daleko.glb",
	# hospodářské stavby usedlostí (Havran katalog předmětů, blender/vlastni.py) – zesvětlené jako domy (KCD ves_2, Havran
	# svet.gd „Míša 0.83: stodola téměř černá – zvětralá prkna šedohnědá, světlejší“ tint × 1,7); kolize z predmety_h
	"res://modely/predmety/stodola.glb", "res://modely/predmety/stodola_stredni.glb", "res://modely/predmety/stodola_mala.glb",
	"res://modely/predmety/stodola_mala_stredni.glb", "res://modely/predmety/kolna.glb", "res://modely/predmety/kolna_stredni.glb",
	"res://modely/predmety/kurnik.glb"]   # jabloň sadů a dvorů Havrana (vesnice.py dvorec_stromy, lokace.json ves.dvorec.sad)
const BEZ_JASU := ["jablon"]   # listí a kůra stromu: barvy jsou z fotek (Havran sad), nezesvětlovat jako dřevo staveb
var _alfa := false
var _bez_jasu := false
var _stredni_soubor := false   # předměty Havrana: střední stupeň = celý soubor *_stredni.glb (barva vrcholů)

## Jas venkovních textur podle reference KCD (Havran docs/screens/kcd1/ves_2.jpg: ohlazené dřevo stříbřitě šedohnědé,
## šindel a došky šedohnědé, průměrný jas ~0,42–0,55): Havranovy textury dřeva mají 0,13–0,3 → domy ve hře černé (11. 11.).
## Zesvětlit na JAS_CIL (nejvýš 2,2×); začouzené, vnitřní a povala ne (záměrně tmavé).
const JAS_CIL := 0.5   # KCD ves_2: ohlazené dřevo ~0,5
const JAS_PREDMETY := 0.42   # hospodářské stavby: prkna stodol tmavší než ohlazené roubení domu (KCD1 ves_1 kůlna vpravo, ves_6; 0,5 = růžová prkna, snímek 12. 11.)
static var jas_cil := JAS_CIL
static func _jas(im: Image, jm: String) -> Image:
	for k in ["Zacouz", "Vnitr", "Povala", "Interier", "Pec", "Okn"]:
		if jm.contains(k): return im
	var s := 0.0; var n := 0
	for y in range(0, im.get_height(), 8):
		for x in range(0, im.get_width(), 8): s += im.get_pixel(x, y).get_luminance(); n += 1
	var j := s / maxf(n, 1)
	if j >= jas_cil or j <= 0.01: return im
	im.adjust_bcs(minf(jas_cil / j, 2.6), 1.0, 0.9)
	return im

## Normálová mapa z importu Godotu má jen R a G (komprese normál) – modrý kanál dopočítat (z = √(1 − x² − y²)),
## jinak normály v glb míří do strany a povrch je černý (11. 11.: domy z Havrana tmavé i na slunci).
static func _normala(im: Image) -> Image:
	im.convert(Image.FORMAT_RGB8)
	var s := 0.0
	for i in 64: s += im.get_pixel(i * 7 % im.get_width(), i * 13 % im.get_height()).b
	if s / 64.0 > 0.3: return im
	for y in im.get_height():
		for x in im.get_width():
			var c := im.get_pixel(x, y); var nx := c.r * 2.0 - 1.0; var ny := c.g * 2.0 - 1.0
			im.set_pixel(x, y, Color(c.r, c.g, sqrt(maxf(0.0, 1.0 - nx * nx - ny * ny)) * 0.5 + 0.5))
	return im
func _zmensi(n: Node) -> void:
	_alfa = false
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null: continue
		for i in m.get_surface_count():
			var mt := m.surface_get_material(i) as BaseMaterial3D
			if mt == null: continue
			for p in ["albedo_texture", "normal_texture"]:
				var t: Texture2D = mt.get(p)
				if t == null: continue
				var im := t.get_image()
				if im == null: continue
				if im.is_compressed(): im.decompress()
				if p == "normal_texture": im = _normala(im)
				if p == "albedo_texture" and not _bez_jasu: im = _jas(im, String(mt.resource_name))
				var mx := 1024 if p == "albedo_texture" else 512
				if max(im.get_width(), im.get_height()) > mx: im.resize(mx, mx * im.get_height() / im.get_width(), Image.INTERPOLATE_LANCZOS)
				if p == "albedo_texture" and im.detect_alpha() != Image.ALPHA_NONE: _alfa = true
				mt.set(p, ImageTexture.create_from_image(im))
			mt.roughness_texture = null; mt.metallic_texture = null
			mt.metallic = 0.0; mt.roughness = maxf(mt.roughness, 0.85)   # bez textury kovovosti zůstal faktor 1,0 = černý kov (11. 11.)

## Střední stupeň (barva vrcholů) a hrubý obal _Daleko (barva materiálu) mají barvu = průměr původních tmavých textur –
## zesvětlit stejně jako textury (_jas), jinak domy od 30 m černé.
static func _jas_barva(c: Color) -> Color:
	var j := c.linear_to_srgb().get_luminance()
	if j >= jas_cil or j <= 0.01: return c
	var f := minf(jas_cil / j, 2.6)
	return Color(c.linear_to_srgb().r * f, c.linear_to_srgb().g * f, c.linear_to_srgb().b * f, c.a).clamp().srgb_to_linear()
func _jas_lod(n: Node) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var jm := String(mi.name); var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null: continue
		if (jm.ends_with("_Stredni") or _stredni_soubor) and m is ArrayMesh:
			var am := ArrayMesh.new()
			for i in m.get_surface_count():
				var a := m.surface_get_arrays(i); var cs = a[Mesh.ARRAY_COLOR]
				if cs != null:
					var nc := PackedColorArray()
					for c in cs: nc.append(_jas_barva(c))
					a[Mesh.ARRAY_COLOR] = nc
				am.add_surface_from_arrays(m.surface_get_primitive_type(i), a)
				am.surface_set_material(i, m.surface_get_material(i))
			(mi as MeshInstance3D).mesh = am
		elif jm.ends_with("_Daleko"):
			for i in m.get_surface_count():
				var mt := m.surface_get_material(i) as BaseMaterial3D
				if mt and mt.albedo_texture == null: mt.albedo_color = _jas_barva(mt.albedo_color.srgb_to_linear()).linear_to_srgb()
func _init():
	for pk in OS.get_cmdline_user_args(): ProjectSettings.load_resource_pack(pk, true)
	for f in SOUBORY:
		if not ResourceLoader.exists(f): print("CHYBI ", f); continue
		_stredni_soubor = f.get_file().ends_with("_stredni.glb") and f.contains("/predmety/")
		jas_cil = JAS_PREDMETY if f.contains("/predmety/") else JAS_CIL
		_bez_jasu = BEZ_JASU.any(func(k: String) -> bool: return f.get_file().begins_with(k))
		var ps := load(f) as PackedScene
		if ps == null: print("CHYBI ", f, " (závislost)"); continue   # jinak chyba skriptu a SceneTree nikdy neskončí (12. 11.)
		var n: Node = ps.instantiate(); _zmensi(n)
		if not _bez_jasu: _jas_lod(n)
		var gl := GLTFDocument.new(); var st := GLTFState.new()
		if not _alfa: gl.image_format = "JPEG"; gl.lossy_quality = 0.85
		var cil: String = OUT + f.get_file()
		print("STAVBA ", f.get_file(), " ", gl.append_from_scene(n, st) == OK and gl.write_to_filesystem(st, cil) == OK)
		n.free()
	quit()
