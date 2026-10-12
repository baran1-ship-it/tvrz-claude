extends RefCounted
## Materialy. Kazdy zaznam: {"mat": Material, "tile": velikost jedne dlazdice textury v metrech}.

var m: Dictionary = {}


func _init() -> void:
	_std("stone", "stone_wall", 4.0, true)
	_std("flag", "flagstone", 3.0, true)
	_std("ashlar", "ashlar", 2.0, true)
	_std("plaster", "plaster", 4.0, true)
	_std("plaster_worn", "plaster_worn", 4.0, true)
	_std("planks", "wood_planks", 2.0, true)
	_std("beam", "wood_beam", 2.0, true)
	_std("shingles", "shingles", 2.0, true)
	_std("cobble", "cobble", 3.0, true)
	_std("dirt", "dirt", 3.0, false)
	_std("straw", "straw", 1.5, false)
	_std("fabric", "fabric", 0.5, false)
	_std("bark", "bark", 1.0, false)
	_std("iron", "iron", 1.0, true)
	m["iron"]["mat"].metallic = 1.0
	m["iron"]["mat"].metallic_texture = load("res://textures/iron_orm.png")
	m["iron"]["mat"].metallic_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_BLUE
	_std("target", "target", 1.0, false)

	# jednobarevne materialy bez textur
	_flat("coal", Color(0.035, 0.032, 0.03), 0.95)
	_flat("soot", Color(0.02, 0.02, 0.02), 1.0)
	_flat("leather", Color(0.30, 0.19, 0.11), 0.7)
	_flat("wax", Color(0.92, 0.86, 0.70), 0.5)
	_flat("water", Color(0.03, 0.05, 0.05), 0.08)
	_flat("paint", Color(1, 1, 1), 0.7)
	_flat("clay", Color(0.55, 0.33, 0.2), 0.55)
	var ember := StandardMaterial3D.new()
	ember.albedo_color = Color(0.9, 0.25, 0.05)
	ember.emission_enabled = true
	ember.emission = Color(1.0, 0.32, 0.06)
	ember.emission_energy_multiplier = 3.0
	ember.vertex_color_use_as_albedo = true
	m["ember"] = {"mat": ember, "tile": 1.0}
	var steel := StandardMaterial3D.new()
	steel.albedo_color = Color(0.62, 0.63, 0.65)
	steel.metallic = 1.0
	steel.roughness = 0.38
	steel.vertex_color_use_as_albedo = true
	m["steel"] = {"mat": steel, "tile": 1.0}
	_foliage("spruce", "spruce", 0.34, 0.07, Color(0.12, 0.2, 0.08))
	_foliage("leaves", "leaves", 0.36, 0.09, Color(0.24, 0.32, 0.08))
	_foliage("spruce_tree", "spruce_tree", 0.4, 0.05, Color(0.1, 0.17, 0.07))
	_foliage("grass_tuft", "grass_blades", 0.3, 0.09, Color(0.2, 0.26, 0.08))
	_foliage("banner", "banner", 0.0, 0.16, Color(0.2, 0.1, 0.08))


func _foliage(key: String, tex: String, cut: float, sway: float, back: Color) -> void:
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/foliage.gdshader")
	mat.set_shader_parameter("tex", load("res://textures/%s.png" % tex))
	mat.set_shader_parameter("alpha_cut", cut)
	mat.set_shader_parameter("sway", sway)
	mat.set_shader_parameter("back", back)
	m[key] = {"mat": mat, "tile": 1.0}


func _std(key: String, tex: String, tile: float, has_orm: bool) -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = load("res://textures/%s_a.png" % tex)
	mat.normal_enabled = true
	mat.normal_texture = load("res://textures/%s_n.png" % tex)
	if has_orm:
		var orm: Texture2D = load("res://textures/%s_orm.png" % tex)
		mat.ao_enabled = true
		mat.ao_texture = orm
		mat.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
		mat.ao_light_affect = 0.35
		mat.roughness_texture = orm
		mat.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GREEN
		mat.roughness = 1.0
	else:
		mat.roughness = 0.9
	mat.vertex_color_use_as_albedo = true
	mat.vertex_color_is_srgb = true
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	m[key] = {"mat": mat, "tile": tile}


func _flat(key: String, col: Color, rough: float) -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mat.roughness = rough
	mat.vertex_color_use_as_albedo = true
	mat.vertex_color_is_srgb = true
	m[key] = {"mat": mat, "tile": 1.0}
