extends SceneTree
## Test otezi (Misa 9. 11. r. 86: pri jizde chybi otezi - remeny od udidla k rukam). Bez sveta, headless, sekundy:
## kun (scripts/kun.gd) na rovine, scripts/otezi.gd setup na nem (krouzky udidla ze site uzdecky), konce do dvou bodu
## nad kohoutkem. Kontrola jako telo_zaber: krouzky 0,08-0,35 m od sebe (huba), do 0,45 m od kosti hlavy, oba pod
## temenem; remen ma trojuhelniky. Vypise diagnostiku vyberu (rozsah site po ose hlavy, body v pasu po stranach).
## Spusteni: tools/beh.sh otezi cmd godot --headless --path . -s res://tools/test_otezi.gd
## Vystup: OTEZI ... radky, TEST OTEZI OK/CHYBA.

const Pravidla := preload("res://scripts/pravidla.gd")
var kun: CharacterBody3D
var snimek := 0
var chyb := 0


func _initialize() -> void:
	var zem := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var bx := BoxShape3D.new()
	bx.size = Vector3(200, 1, 200)
	cs.shape = bx
	cs.position = Vector3(0, -0.5, 0)
	zem.add_child(cs)
	root.add_child(zem)
	var main := Node.new()
	main.name = "MainNahrada"
	root.add_child(main)
	kun = CharacterBody3D.new()
	kun.set_script(load("res://scripts/kun.gd"))
	root.add_child(kun)
	if not kun.setup(main, Vector3(0, 0.05, 0), 0.0):
		print("TEST OTEZI CHYBA kun.setup selhal")
		quit(1)


func _over(co: String, ok: bool, msg: String) -> void:
	print("TEST OTEZI %s %s %s" % [co, "OK" if ok else "CHYBA", msg])
	if not ok:
		chyb += 1


func _process(_d: float) -> bool:
	snimek += 1
	if snimek < 20:
		return false
	var D: Dictionary = Pravidla.cti("jizda", "kun", "otezi")
	var ot: MeshInstance3D = (load("res://scripts/otezi.gd") as GDScript).new()
	root.add_child(ot)
	var ok: bool = ot.call("setup", kun, D)
	_over("setup", ok, "krouzky udidla ze site %s" % D["uzdecka_sit"])
	if ok:
		var ks: Skeleton3D = kun.get("_kostra")
		var hl := -1
		for i in ks.get_bone_count():
			if ks.get_bone_name(i).begins_with(String(D["kost_hlavy"])):
				hl = i
		var hp := ks.global_transform * ks.get_bone_global_pose(hl).origin
		var ud: Array = ot.call("udidla")
		var rozpeti := (ud[0] as Vector3).distance_to(ud[1])
		var od := maxf((ud[0] as Vector3).distance_to(hp), (ud[1] as Vector3).distance_to(hp))
		print("OTEZI udidla %s / %s, kost hlavy %s" % [(ud[0] as Vector3).snapped(Vector3.ONE * 0.01), (ud[1] as Vector3).snapped(Vector3.ONE * 0.01), hp.snapped(Vector3.ONE * 0.01)])
		_over("rozpeti", rozpeti >= 0.08 and rozpeti <= 0.35, "%.2f m (huba 0,08-0,35)" % rozpeti)
		_over("u hlavy", od <= 0.45, "%.2f m od kosti hlavy" % od)
		var sedlo: Vector3 = kun.call("sedlo_global") if kun.has_method("sedlo_global") else kun.global_position + Vector3(0, 1.3, 0)
		var vp := -kun.global_basis.z
		ot.call("aktualizuj", sedlo + vp * 0.4 + kun.global_basis.x * 0.12 + Vector3.UP * 0.3, sedlo + vp * 0.4 - kun.global_basis.x * 0.12 + Vector3.UP * 0.3)
		var im: ImmediateMesh = ot.mesh
		var n: int = im.surface_get_array_len(0) if im.get_surface_count() > 0 else 0
		_over("remen", n > 0, "%d vrcholu" % n)
	print("TEST OTEZI %s" % ("OK" if chyb == 0 else "CHYBA"))
	quit(1 if chyb > 0 else 0)
	return true
