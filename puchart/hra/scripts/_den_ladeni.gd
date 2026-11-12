extends Node
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	await get_tree().create_timer(0.3, true).timeout
	var h: Node = get_parent(); var e: Environment = h._env
	print("DL sun e %.3f col %s dir %s | amb e %.3f col %s skyc %.2f | sky top %s hor %s | fog %s dens %.4f | exp %.2f okolni %.3f okolni_e %.2f" % [h.den.slunce.light_energy, h.den.slunce.light_color, -h.den.slunce.global_basis.z, e.ambient_light_energy, e.ambient_light_color, e.ambient_light_sky_contribution, h.den.obloha.sky_top_color, h.den.obloha.sky_horizon_color, e.fog_light_color, e.fog_density, e.tonemap_exposure, h.den.okolni, h.den.okolni_e])
