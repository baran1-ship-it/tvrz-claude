@tool
extends EditorScenePostImport
## Import postav (modely/postavy/…): doplní nastavení materiálů, která glTF neumí přenést.
## V Godotu: vybrat .glb postavy → Import → Import Script = tento soubor → Reimport.
##  - kůže (*_telo*, Quaternius: *_telo_kuze, *_telo_ruce): subsurface 0,2 (červená), detailní normála pórů, okrajové světlo 0,1
##  - vlasy, řasy (*_vlasy*, *_rasy*): alpha scissor, oboustranné, anizotropie 0,6
##  - rohovka (*_rohovka*): průhledná, drsnost 0,05, clearcoat
##  - vlhká linka víček (*_vlhka_linka*): průhledná, lesklá
##  - LOD: uzly *_lod1 viditelné od 20 m, ostatní do 20 m; stín jen LOD0 (do 30 m řeší DirectionalLight)

const DETAIL_NORMAL := "res://modely/postavy/kuze_detail_normal.png"
const LOD_DIST := 20.0

var _ma_lod1 := false

func _post_import(scene: Node) -> Object:
	_ma_lod1 = _najdi_lod1(scene)
	_walk(scene)
	return scene

func _najdi_lod1(n: Node) -> bool:
	if n.name.ends_with("_lod1"):
		return true
	for c in n.get_children():
		if _najdi_lod1(c):
			return true
	return false

func _walk(n: Node) -> void:
	if n is MeshInstance3D:
		_setup_mesh(n)
	for c in n.get_children():
		_walk(c)

func _setup_mesh(mi: MeshInstance3D) -> void:
	# ruční LOD jen u starších postav (uzly *_lod1); Quaternius postavy používají automatický mesh LOD Godotu
	if _ma_lod1:
		var is_lod1 := mi.name.ends_with("_lod1")
		if is_lod1:
			mi.visibility_range_begin = LOD_DIST
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		else:
			mi.visibility_range_end = LOD_DIST
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	if mi.mesh == null:
		return
	# vlasy, oči, obočí/řasy mimo automatický LOD (rozpadly by se) – vysoký lod_bias = vždy plná síť
	var jm := String(mi.name).to_lower()
	if "_hair_" in jm or "_vlasy" in jm or "_oci" in jm or "_oboci" in jm or "_rasy" in jm:
		mi.lod_bias = 100.0
	for i in mi.mesh.get_surface_count():
		var m := mi.mesh.surface_get_material(i)
		if not (m is StandardMaterial3D):
			continue
		var sm: StandardMaterial3D = m.duplicate()
		var nm := String(m.resource_name).to_lower()
		sm.rim_enabled = true
		sm.rim = 0.1
		sm.rim_tint = 0.5
		if "rohovka" in nm:
			sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			sm.roughness = 0.05
			sm.metallic = 0.0
			sm.clearcoat_enabled = true
			sm.clearcoat = 1.0
			sm.clearcoat_roughness = 0.05
			sm.rim_enabled = false
		elif "vlhka_linka" in nm:
			sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			sm.roughness = 0.04
			sm.rim_enabled = false
		elif "_vlasy" in nm or "_rasy" in nm:
			sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			sm.alpha_scissor_threshold = 0.5
			sm.cull_mode = BaseMaterial3D.CULL_DISABLED
			sm.anisotropy_enabled = true
			sm.anisotropy = 0.6
		elif "_telo" in nm:
			sm.subsurf_scatter_enabled = true
			sm.subsurf_scatter_strength = 0.2
			sm.subsurf_scatter_skin_mode = true
			if ResourceLoader.exists(DETAIL_NORMAL):
				sm.detail_enabled = true
				sm.detail_normal = load(DETAIL_NORMAL)
				sm.detail_uv_layer = BaseMaterial3D.DETAIL_UV_1
				sm.uv1_scale = Vector3(1, 1, 1)
		else:
			# oblečení: alfa jen u cípů, jinak plné
			if sm.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED:
				sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
				sm.alpha_scissor_threshold = 0.5
		mi.mesh.surface_set_material(i, sm)
