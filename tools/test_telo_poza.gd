extends SceneTree
## Test telo_poza (Misa 0.99994 r. 73: ruka s louci neni v zaberu, louc u oka obri). Bez sveta, headless, sekundy:
## telo hrace (scripts/telo.gd) s nahradnim hracem (kamera ve vysce oci, pohled vpred), meri kosti v soustave kamery
## [vpravo, nahoru, vpred = -z] ve stani bez predmetu, s louci a v chuzi s louci. Kontroly z jizda.json telo.test_poza:
## hlava tela tesne za okem (oci jsou pred kosti hlavy), rameno ruky s louci ne za hlavou (klicni kost z klipu drzeni
## nesmi rameno stahnout dozadu), zapesti v zaberu ve vzdalenosti od oka jako v KCD (ruka vpravo dole, louc
## prirozene velka).
## Spusteni: tools/beh.sh telopoza cmd godot --headless --path . -s res://tools/test_telo_poza.gd
## Vystup: TELO_POZA ... radky, TEST TELO_POZA OK/CHYBA.

const Pravidla := preload("res://scripts/pravidla.gd")
var T: Dictionary = Pravidla.cti("jizda", "telo", "test_poza")
var hrac: CharacterBody3D
var cam: Camera3D
var telo: Node3D
var t := 0.0
var krok := 0
var chyb := 0
const KOSTI := ["Head", "neck_01", "spine_03", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "upperarm_l"]


func _initialize() -> void:
	var s := GDScript.new()
	s.source_code = "extends CharacterBody3D\nconst WALK := 2.3\nconst RUN := 4.8\nconst EYE := 1.62\nvar yaw := 0.0\nvar pitch := 0.0\nvar cam: Camera3D\nvar climbing := false\nvar na_koni = null\nvar flying := false\nvar seated := false\nvar oci_posun := Vector3.ZERO\nvar _zb := {}\n"
	s.reload()
	hrac = CharacterBody3D.new()
	hrac.set_script(s)
	root.add_child(hrac)
	var head := Node3D.new()
	head.position.y = 1.62
	hrac.add_child(head)
	cam = Camera3D.new()
	cam.fov = 70.0
	head.add_child(cam)
	hrac.set("cam", cam)
	telo = (load("res://scripts/telo.gd") as GDScript).new()
	root.add_child(telo)
	if not telo.call("setup", hrac):
		print("TEST TELO_POZA CHYBA setup")
		quit(1)


func _kam(kost: String) -> Vector3:
	var ks: Skeleton3D = telo.get("kostra")
	var i := ks.find_bone(kost)
	var w := ks.global_transform * ks.get_bone_global_pose(i).origin
	var k := cam.global_transform.affine_inverse() * w
	return Vector3(k.x, k.y, -k.z)                     # vpred kladne


func _vypis(stav: String) -> Dictionary:
	var d := {}
	for k: String in KOSTI:
		d[k] = _kam(k)
		print("TELO_POZA %-14s %-11s vpravo %+.3f nahoru %+.3f vpred %+.3f" % [stav, k, d[k].x, d[k].y, d[k].z])
	return d


func _over(co: String, ok: bool, msg: String) -> void:
	print("TEST TELO_POZA %s %s %s" % [co, "OK" if ok else "CHYBA", msg])
	if not ok:
		chyb += 1


func _process(delta: float) -> bool:
	t += delta
	if krok == 0 and t > 0.6:
		var d := _vypis("stani")
		# oci jsou pred kosti hlavy (lebka): hlava tela nejvys hlava_za_okem_max_m za kamerou
		var hz := -float(d["Head"].z)
		_over("hlava za okem", hz <= float(T["hlava_za_okem_max_m"]) and hz >= 0.0, "%.3f m (mez %.2f)" % [hz, float(T["hlava_za_okem_max_m"])])
		telo.call("drz", "louc")
		krok = 1
		t = 0.0
	elif krok == 1 and t > 0.6:
		var d := _vypis("louc")
		var rz := float(d["upperarm_r"].z) - float(d["Head"].z)
		_over("rameno s louci", rz >= -float(T["rameno_za_hlavou_max_m"]), "rameno %.3f m za hlavou (mez %.2f)" % [-rz, float(T["rameno_za_hlavou_max_m"])])
		var h: Vector3 = d["hand_r"]
		var ok := h.z >= float(T["zapesti_vpred_min_m"]) and h.x > 0.0
		_over("zapesti pred okem", ok, "zapesti vpred %.3f m (min %.2f), vpravo %.3f" % [h.z, float(T["zapesti_vpred_min_m"]), h.x])
		var o := cam.unproject_position(cam.global_transform * Vector3(h.x, h.y, -h.z))
		print("TELO_POZA zapesti v obraze %s (velikost %s)" % [o, cam.get_viewport().get_visible_rect().size])
		hrac.velocity = Vector3(0, 0, -1.4)
		krok = 2
		t = 0.0
	elif krok == 2 and t > 1.0:
		_vypis("louc_chuze")
		print("TEST TELO_POZA: %d chyb" % chyb)
		quit(1 if chyb > 0 else 0)
		return true
	return false
