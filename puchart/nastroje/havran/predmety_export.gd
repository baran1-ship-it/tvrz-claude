extends SceneTree
const OUT := "/home/user/tvrz-claude/puchart/hra/modely/predmety_h/"
var _alfa := false
func _zmensi(n: Node) -> void:
	_alfa = false
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m: Mesh = (mi as MeshInstance3D).mesh
		if m == null: continue
		for i in m.get_surface_count():
			var mt := m.surface_get_material(i) as BaseMaterial3D
			if mt == null: continue
			for p in ["albedo_texture", "normal_texture", "roughness_texture", "metallic_texture", "ao_texture"]:
				var t: Texture2D = mt.get(p)
				if t == null: continue
				var im := t.get_image()
				if im == null: continue
				if im.is_compressed(): im.decompress()
				var mx := 512 if p == "albedo_texture" else 256
				if max(im.get_width(), im.get_height()) > mx: im.resize(mx, mx * im.get_height() / im.get_width(), Image.INTERPOLATE_LANCZOS)
				if p == "albedo_texture" and im.detect_alpha() != Image.ALPHA_NONE: _alfa = true
				mt.set(p, ImageTexture.create_from_image(im))
			if mt.roughness_texture: mt.roughness_texture = null
			if mt.metallic_texture: mt.metallic_texture = null
func _init():
	var args := OS.get_cmdline_user_args()
	for pk in args:
		ProjectSettings.load_resource_pack(pk, true)
		var id := pk.get_file().get_basename().trim_prefix("p_"); id = id.substr(0, id.rfind("-"))
		var da := DirAccess.open("res://modely/predmety/")
		if da == null: print("NODIR ", id); continue
		var ok := 0
		for f in da.get_files():
			if not f.begins_with(id): continue
			var base := f.trim_suffix(".import").trim_suffix(".remap")
			if not (base == id + ".glb" or base == id + "_kolize.glb" or base == id + "_stredni.glb" or base == id + ".png"): continue
			if FileAccess.file_exists(OUT + base): continue
			var r = load("res://modely/predmety/" + base)
			if r is PackedScene:
				var n: Node = (r as PackedScene).instantiate(); _zmensi(n)
				var gl := GLTFDocument.new(); var st := GLTFState.new()
				if not _alfa: gl.image_format = "JPEG"; gl.lossy_quality = 0.8
				if gl.append_from_scene(n, st) == OK and gl.write_to_filesystem(st, OUT + base) == OK: ok += 1
				n.free()
			elif r is Texture2D:
				var im := (r as Texture2D).get_image()
				if im.is_compressed(): im.decompress()
				if im.get_width() > 128: im.resize(128, 128 * im.get_height() / im.get_width())
				im.save_png(OUT + base); ok += 1
		print("ID ", id, " ", ok)
	quit()
