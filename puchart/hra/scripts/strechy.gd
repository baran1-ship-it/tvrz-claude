extends RefCounted
## Střechy staveb pro „jsem pod střechou?“ (déšť pocasi.gd, světlo interiéru hlavni.gd _atmosfera). Krokve a krytina staveb
## nemají kolizi (chyby.md 312 – hlava by u okapu prošla střechou), takže paprsek nahoru z půdy krčmy, z pavlače nebo pod
## přesahem střechy nic netrefil: v podkroví pršelo a podlaha pavlače se svítila jako venku modrou oblohou (Míša 17. 11.,
## docs/screens/misa_17_11/08.jpg a 12.jpg). Proto vlastní fyzikální prostor jen se střechami (hráč ani jiné paprsky ho
## nevidí – žádný vliv na pohyb a klikání): plochy s krytinou (materiál podle pocasi.json strechy.materialy) z hrubých obalů
## staveb (uzly *_Daleko domů a zemljanek, LOD1_* celků a mlýna – málo trojúhelníků) a ze střech hradů (potomci uzlů
## strechy.predci). Prostor se postaví jednou při prvním dotazu (všechny stavby se načítají při startu).

static var _space := RID()
static var _pocet := 0


static func _je_strecha(jm: String, vzory: Array) -> bool:
	var j := jm.to_lower()
	for v in vzory:
		if j.contains(String(v).to_lower()): return true
	return false


static func _ma_predka(n: Node, predci: Array) -> bool:
	var p := n.get_parent()
	while p:
		if String(p.name) in predci: return true
		p = p.get_parent()
	return false


## Postaví prostor střech ze stromu scény (cfg = pocasi.json strechy). Další volání nic nedělají.
static func zajisti(koren: Node, cfg: Dictionary) -> void:
	if _space.is_valid() or koren == null: return
	_space = PhysicsServer3D.space_create(); PhysicsServer3D.space_set_active(_space, true)
	var mat: Array = cfg.get("materialy", ["sindel"]); var kon: Array = cfg.get("uzly_konec", ["_Daleko"])
	var zac: Array = cfg.get("uzly_zacatek", ["LOD1_"]); var pre: Array = cfg.get("predci", ["Hrad"])
	for g in koren.find_children("*", "MeshInstance3D", true, false):
		var mi := g as MeshInstance3D; var nm := String(mi.name)
		if mi.mesh == null or nm.ends_with("_Stin"): continue
		var ok := false
		for k in kon: ok = ok or nm.ends_with(String(k))
		for k in zac: ok = ok or nm.begins_with(String(k))
		if not ok and not _ma_predka(mi, pre): continue
		for i in mi.mesh.get_surface_count():
			var mt := mi.mesh.surface_get_material(i)
			if mt == null or not _je_strecha(mt.resource_name, mat): continue
			var a: Array = mi.mesh.surface_get_arrays(i)
			var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]; var ix: PackedInt32Array = a[Mesh.ARRAY_INDEX] if a[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			var f := PackedVector3Array()
			if ix.is_empty(): f = v
			else:
				f.resize(ix.size())
				for q in ix.size(): f[q] = v[ix[q]]
			if f.size() < 3: continue
			var sh := PhysicsServer3D.concave_polygon_shape_create()
			PhysicsServer3D.shape_set_data(sh, {"faces": f, "backface_collision": true})
			var b := PhysicsServer3D.body_create(); PhysicsServer3D.body_set_mode(b, PhysicsServer3D.BODY_MODE_STATIC)
			PhysicsServer3D.body_set_space(b, _space); PhysicsServer3D.body_add_shape(b, sh)
			PhysicsServer3D.body_set_state(b, PhysicsServer3D.BODY_STATE_TRANSFORM, mi.global_transform)
			_pocet += 1
	print("STRECHY ploch %d" % _pocet)


## Výška první střechy pod bodem shora (od) do (do), nebo -INF.
static func vyska(od: Vector3, do_: Vector3) -> float:
	if not _space.is_valid(): return -INF
	var h := PhysicsServer3D.space_get_direct_state(_space).intersect_ray(PhysicsRayQueryParameters3D.create(od, do_))
	return (h["position"] as Vector3).y if not h.is_empty() else -INF


## Je nad bodem do vzdálenosti dosah střecha?
static func nad(p: Vector3, dosah: float) -> bool:
	return vyska(p + Vector3.UP * dosah, p) > -INF
