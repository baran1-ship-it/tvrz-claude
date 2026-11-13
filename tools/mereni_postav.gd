extends SceneTree
## Izolovany test ceny postav (13. 11., trasa 0.999993: bez postav -7..-9 ms, bez animace nepomaha): N postav z dat pred
## kamerou, prumer snimku ve trech rezimech - animovane (advance kazdy snimek), zastavene, skryte. Bezi s renderem
## (xvfb, gl_compatibility jako tablet): llvmpipe = jen pomerove srovnani rezimu, ne cisla tabletu.
## Spusteni: tools/beh.sh mp cmd xvfb-run -a -s "-screen 0 900x900x24" godot --path . --rendering-driver opengl3 \
##   --rendering-method gl_compatibility --resolution 900x900 -s res://tools/mereni_postav.gd   (TVRZ_MP_N=20)

const Lide := preload("res://scripts/lide.gd")


func _initialize() -> void:
	_beh.call_deferred()


func _prumer(n: int, postavy: Array, anim: bool) -> float:
	var t0 := Time.get_ticks_usec()
	_proc = 0.0
	for _i in n:
		if anim:
			for c: Dictionary in postavy:
				(c["ap"] as AnimationPlayer).advance(1.0 / 30.0)
		await process_frame
		_proc += Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
	_proc /= n
	return float(Time.get_ticks_usec() - t0) / n / 1000.0


var _proc := 0.0


## 13. 11. (trasa 0.999994: postavy stoji -9..-12 ms, skryte nic; jednotlive vypinace nic): vsechny modifikatory kostry
## postavy (LookAt hlavy, nohy IK, uchop, ridic sukne, pruzina sukne) zapnout / vypnout
func _modif(postavy: Array, zap: bool, jen := "") -> void:
	for c: Dictionary in postavy:
		for m: Node in (c["kostra"] as Skeleton3D).get_children():
			if m is SkeletonModifier3D:
				(m as SkeletonModifier3D).active = zap or (jen != "" and String(m.name) == jen)


func _beh() -> void:
	# A/B (13. 11.): TVRZ_MP_PCK = starsi balik postav (napr. z_postavy z 0.99998) prekryje modely pred nactenim
	if OS.has_environment("TVRZ_MP_PCK"):
		print("MERENI_POSTAV balik %s: %s" % [OS.get_environment("TVRZ_MP_PCK"), ProjectSettings.load_resource_pack(OS.get_environment("TVRZ_MP_PCK"), true)])
	var n := int(OS.get_environment("TVRZ_MP_N")) if OS.has_environment("TVRZ_MP_N") else 20
	var koren := Node3D.new()
	root.add_child(koren)
	var sv := DirectionalLight3D.new()
	sv.rotation_degrees = Vector3(-50, 30, 0)
	koren.add_child(sv)
	var cam := Camera3D.new()
	koren.add_child(cam)
	cam.position = Vector3(0, 1.7, 9)
	cam.look_at(Vector3(0, 1.0, 0))
	var lide: Node3D = Lide.new()
	koren.add_child(lide)
	lide.set_process(false)
	lide.set_physics_process(false)
	var ob: Array = (Lide.P["obyvatele"] as Array)
	var postavy: Array = []
	for i in n:
		var c: Dictionary = lide.nova_postava(ob[i % ob.size()])
		var u: Node3D = c["uzel"]
		u.position = Vector3((i % 5 - 2) * 1.4, 0, -(i / 5) * 1.6)
		c["cn"] = Lide.P["cinnosti"]["volno"]
		c["klip"] = ""
		lide.call("_klip", c, "Walk_Loop", 1.0)
		postavy.append(c)
	# staticke kopie: stejne site bez kostry (skin pryc) na mistech postav - rozdil zastavene x staticke = skinovani
	var stat := Node3D.new()
	koren.add_child(stat)
	for c: Dictionary in postavy:
		for mi: Node in (c["uzel"] as Node3D).find_children("*", "MeshInstance3D", true, false):
			var m2 := MeshInstance3D.new()
			m2.mesh = (mi as MeshInstance3D).mesh
			m2.global_transform = (mi as MeshInstance3D).global_transform
			for si in (mi as MeshInstance3D).get_surface_override_material_count():
				m2.set_surface_override_material(si, (mi as MeshInstance3D).get_surface_override_material(si))
			stat.add_child(m2)
	for _i in 30:
		await process_frame
	var vysl := {}
	for kolo in 2:
		var rezimy: Array = ["animovane", "zastavene", "anim_bez_modif", "kostry_stoji", "staticke", "skryte"]
		for c0: Dictionary in postavy:
			for m: Node in (c0["kostra"] as Skeleton3D).get_children():
				if m is SkeletonModifier3D and not rezimy.has("anim+" + String(m.name)):
					rezimy.append("anim+" + String(m.name))
		for rez: String in rezimy:
			for c: Dictionary in postavy:
				(c["uzel"] as Node3D).visible = rez in ["animovane", "zastavene", "anim_bez_modif", "kostry_stoji"] or rez.begins_with("anim+")
			stat.visible = rez == "staticke"
			_modif(postavy, rez in ["animovane", "zastavene"], rez.trim_prefix("anim+") if rez.begins_with("anim+") else "")
			await process_frame
			var ms: float = await _prumer(90, postavy, rez in ["animovane", "anim_bez_modif"] or rez.begins_with("anim+"))
			var a: Array = vysl.get(rez, [INF, INF])
			vysl[rez] = [minf(a[0], snappedf(ms, 0.01)), minf(a[1], snappedf(_proc, 0.01))]
	var nm := 0
	for m: Node in (postavy[0]["kostra"] as Skeleton3D).get_children():
		nm += 1 if m is SkeletonModifier3D else 0
	print("MERENI_POSTAV modifikatory %s" % str((postavy[0]["kostra"] as Skeleton3D).get_children().filter(func(x: Node) -> bool: return x is SkeletonModifier3D).map(func(x: Node) -> String: return "%s(%s)" % [x.name, x.get_class()])))
	print("MERENI_POSTAV modifikatoru na postave %d, kosti %d" % [nm, (postavy[0]["kostra"] as Skeleton3D).get_bone_count()])
	print("MERENI_POSTAV n=%d: %s ([ms/snimek, proces ms], mensi ze 2 kol; llvmpipe - jen pomer)" % [n, str(vysl)])
	quit()
