extends SceneTree
## Rychlost klipu chodu kone (Misa 27. 11. „jizda nic moc oproti puvodnimu, musis to sladit“; rešerše
## reserse_animace_postavy_27_11.md kap. 4: tempo klipu podle zmerene rychlosti, aby kopyta neklouzala - RDR2 GDC 2021).
## Kun (scripts/kun.gd) bez sveta na miste; animacni strom hraje chod pri rychlosti hry (jizda.json kun.chody, klus_m_s),
## po snimcich (spoustet s --fixed-fps 60) se sleduji kosti kopyt (Toe/Finger) v soustave kone: v oporne fazi (kopyto
## do OPORA_M nad nejnizsim bodem) se kopyto pohybuje vuci telu dozadu rychlosti, kterou klip „jde“. Pomer rychlost
## hry / rychlost klipu = o kolik kopyta kloužou (1 = sedi).
## tools/beh.sh kunrych cmd godot --headless --fixed-fps 60 --path . -s res://tools/kun_klipy_rychlost.gd

const OPORA_M := 0.03
const Pravidla := preload("res://scripts/pravidla.gd")
var kun: CharacterBody3D
var at: AnimationTree
var sk: Skeleton3D
var kopyta: Array = []
var chody: Array = []
var ci := 0
var t := 0
var vz: Array = []


func _initialize() -> void:
	var main := Node.new()
	root.add_child(main)
	kun = CharacterBody3D.new()
	kun.set_script(load("res://scripts/kun.gd"))
	root.add_child(kun)
	if not kun.setup(main, Vector3.ZERO, 0.0):
		print("KLIP_RYCHLOST setup selhal")
		quit(1)
		return
	at = kun.get("_at")
	sk = kun.get("_kostra")
	for i in sk.get_bone_count():
		var n := sk.get_bone_name(i)
		if (n.contains("Toe") or n.contains("Finger")) and not n.ends_with("Nub"):
			kopyta.append(i)
	var CH: Dictionary = Pravidla.cti("jizda", "kun", "chody")
	chody = [["krok", float(CH["krok"])], ["klus", float(Pravidla.cti("jizda", "kun").get("klus_m_s", 0.0))], ["cval", float(CH["cval"])]]
	kun.set_physics_process(false)
	kun.set_process(false)


func _process(dt: float) -> bool:
	if kun == null or ci >= chody.size():
		return true
	at.set("parameters/chod/blend_position", Vector2(0.0, float(chody[ci][1])))
	at.set("parameters/tempo/scale", 1.0)
	t += 1
	if t > 60:
		var inv := kun.global_transform.affine_inverse()
		for b: int in kopyta:
			vz.append([b, inv * (sk.global_transform * sk.get_bone_global_pose(b).origin)])
	if t == 300:
		var rych: Array = []
		var pohyb := 0.0
		for b: int in kopyta:
			var body: Array = vz.filter(func(e: Array) -> bool: return e[0] == b)
			var ymin := INF
			for e: Array in body:
				ymin = minf(ymin, (e[1] as Vector3).y)
				pohyb = maxf(pohyb, (e[1] as Vector3).distance_to(body[0][1]))
			for i in range(1, body.size()):
				var a: Vector3 = body[i - 1][1]
				var c: Vector3 = body[i][1]
				if a.y < ymin + OPORA_M and c.y < ymin + OPORA_M:
					rych.append((c - a).z / dt)          # kun hlavou k -Z: kopyto v opore jde k +Z (dozadu)
		rych.sort()
		var med: float = rych[rych.size() / 2] if not rych.is_empty() else 0.0
		print("KLIP_RYCHLOST %s pri %.2f m/s hry: kopyta v opore %.2f m/s, pomer hra/klip %.2f (vzorku %d, pohyb kopyt %.2f m)" % [chody[ci][0], float(chody[ci][1]), med, float(chody[ci][1]) / maxf(med, 0.01), rych.size(), pohyb])
		ci += 1
		t = 0
		vz = []
	return false
