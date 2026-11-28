extends SceneTree
## Klouzani kopyt pri jizde (Misa 27. 11. „jizda nic moc oproti puvodnimu, musis to sladit“; rešerše
## reserse_animace_postavy_27_11.md kap. 4: tempo klipu podle zmerene rychlosti - RDR2 GDC 2021). Kun (scripts/kun.gd)
## na rovine bez sveta s neviditelnym jezdcem (jako test kun_klid): krok (packa vpred), cval (_stupen 1). Po ustaleni
## se v soustave kone sleduji kosti kopyt (Toe/Finger): v oporne fazi (kopyto do OPORA_M nad nejnizsim bodem) jde
## kopyto vuci telu dozadu - pomer rychlost kone / rychlost kopyta v opore = 1 kopyta neklouzou, > 1 kluzou dopredu
## (klip pomaly, kun rychly), < 1 „cupitaji“. Vystup KLIP_RYCHLOST <chod> ...
## tools/beh.sh kunrych cmd godot --headless --fixed-fps 60 --path . -s res://tools/kun_klipy_rychlost.gd

const OPORA_M := 0.04
var kun: CharacterBody3D
var jezdec: Node3D
var sk: Skeleton3D
var kopyta: Array = []
var faze := 0
var t := 0
var vz: Array = []
var vrych: Array = []
const FAZE := [["krok", 0], ["cval", 1]]


func _initialize() -> void:
	var zem := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var bx := BoxShape3D.new()
	bx.size = Vector3(4000, 1, 4000)
	cs.shape = bx
	cs.position = Vector3(0, -0.5, 0)
	zem.add_child(cs)
	root.add_child(zem)
	var main := Node.new()
	root.add_child(main)
	kun = CharacterBody3D.new()
	kun.set_script(load("res://scripts/kun.gd"))
	root.add_child(kun)
	if not kun.setup(main, Vector3(0, 0.05, 0), 0.0):
		print("KLIP_RYCHLOST setup selhal")
		quit(1)
		return
	var sc := GDScript.new()
	sc.source_code = "extends Node3D\nvar move_input := Vector2.ZERO\nvar fly_up := false\nvar _jump := false\nvar yaw := 0.0\nvar pitch := 0.0\nvar na_koni = null\nvar velocity := Vector3.ZERO\nfunc look(a: float, b: float) -> void:\n\tyaw += a\n"
	sc.reload()
	jezdec = Node3D.new()
	jezdec.set_script(sc)
	root.add_child(jezdec)
	kun.set("drzet_cestu", false)
	kun.set("jezdec", jezdec)
	jezdec.set("na_koni", kun)
	jezdec.set("yaw", float(kun.get("_yaw")))
	jezdec.set("move_input", Vector2(0, 1))
	sk = kun.get("_kostra")
	for i in sk.get_bone_count():
		var n := sk.get_bone_name(i)
		if (n.contains("Toe") or n.contains("Finger")) and not n.ends_with("Nub"):
			kopyta.append(i)


func _physics_process(dt: float) -> bool:
	if kun == null or faze >= FAZE.size():
		return true
	kun.set("_stupen", int(FAZE[faze][1]))
	jezdec.set("move_input", Vector2(0, 1))
	t += 1
	if t > 240:
		var inv := kun.global_transform.affine_inverse()
		for b: int in kopyta:
			vz.append([b, inv * (sk.global_transform * sk.get_bone_global_pose(b).origin)])
		vrych.append(Vector2(kun.velocity.x, kun.velocity.z).length())
	if t == 480:
		var rych: Array = []
		for b: int in kopyta:
			var body: Array = vz.filter(func(e: Array) -> bool: return e[0] == b)
			var ymin := INF
			for e: Array in body:
				ymin = minf(ymin, (e[1] as Vector3).y)
			for i in range(1, body.size()):
				var a: Vector3 = body[i - 1][1]
				var c: Vector3 = body[i][1]
				if a.y < ymin + OPORA_M and c.y < ymin + OPORA_M:
					rych.append(Vector2(c.x - a.x, c.z - a.z).length() / dt)
		rych.sort()
		vrych.sort()
		var med: float = rych[rych.size() / 2] if not rych.is_empty() else 0.0
		var vk: float = vrych[vrych.size() / 2]
		print("KLIP_RYCHLOST %s: kun %.2f m/s, kopyto v opore vuci telu %.2f m/s, pomer %.2f (vzorku %d)" % [FAZE[faze][0], vk, med, vk / maxf(med, 0.01), rych.size()])
		faze += 1
		t = 0
		vz = []
		vrych = []
	return false
