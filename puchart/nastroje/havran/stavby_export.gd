extends SceneTree
## Stavby z datových balíků Havrana (z_ves, z_mlyn) → glb pro Puchart (nastroje/stavby_z_havrana.sh).
## Textury zmenšené (albedo 1024, normála 512, bez roughness/metallic – rozpočet tabletu, Havran ves_domy.py „max 1024“).
const OUT := "OUT/"
const SOUBORY := ["res://modely/ves/domy.glb", "res://modely/ves/domy_stredni.glb", "res://modely/mlyn/mlyn.glb", "res://modely/mlyn/mlyn_lod1.glb"]
var _alfa := false
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
				var mx := 1024 if p == "albedo_texture" else 512
				if max(im.get_width(), im.get_height()) > mx: im.resize(mx, mx * im.get_height() / im.get_width(), Image.INTERPOLATE_LANCZOS)
				if p == "albedo_texture" and im.detect_alpha() != Image.ALPHA_NONE: _alfa = true
				mt.set(p, ImageTexture.create_from_image(im))
			mt.roughness_texture = null; mt.metallic_texture = null
func _init():
	for pk in OS.get_cmdline_user_args(): ProjectSettings.load_resource_pack(pk, true)
	for f in SOUBORY:
		if not ResourceLoader.exists(f): print("CHYBI ", f); continue
		var n: Node = (load(f) as PackedScene).instantiate(); _zmensi(n)
		var gl := GLTFDocument.new(); var st := GLTFState.new()
		if not _alfa: gl.image_format = "JPEG"; gl.lossy_quality = 0.85
		var cil: String = OUT + f.get_file()
		print("STAVBA ", f.get_file(), " ", gl.append_from_scene(n, st) == OK and gl.write_to_filesystem(st, cil) == OK)
		n.free()
	quit()
