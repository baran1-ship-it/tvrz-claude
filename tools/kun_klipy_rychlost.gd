extends SceneTree
## Rychlost klipu chodu kone (Misa 27. 11. „jizda nic moc oproti puvodnimu, musis to sladit“; rešerše
## reserse_animace_postavy_27_11.md kap. 4: tempo klipu podle zmerene rychlosti, aby kopyta neklouzala - RDR2 GDC 2021).
## Kun (scripts/kun.gd) bez sveta; kazdy klip chodu se prehraje primo AnimationPlayerem (strom vypnuty), po snimcich
## 1/60 s se sleduji kosti kopyt (jizda.json kun.kopyta_kosti, jinak kosti s „Foot“/„Toe“ ve jmene) v soustave kone:
## v oporne fazi (kopyto do opora_m nad svym nejnizsim bodem) se kopyto pohybuje vuci telu dozadu rychlosti, kterou
## kun jde. Vystup: KLIP_RYCHLOST <klip> <m/s> (median pres kopyta a opory), delka klipu.
## tools/beh.sh kunrych cmd godot --headless --path . -s res://tools/kun_klipy_rychlost.gd

const OPORA_M := 0.03


func _initialize() -> void:
	var main := Node.new()
	root.add_child(main)
	var kun: CharacterBody3D = CharacterBody3D.new()
	kun.set_script(load("res://scripts/kun.gd"))
	root.add_child(kun)
	if not kun.setup(main, Vector3.ZERO, 0.0):
		print("KLIP_RYCHLOST setup selhal")
		quit(1)
		return
	var ap: AnimationPlayer = kun.get("_ap")
	var at: AnimationTree = kun.get("_at")
	at.active = false
	var sk: Skeleton3D = kun.get("_kostra")
	var kopyta: Array = []
	for i in sk.get_bone_count():
		var n := sk.get_bone_name(i)
		if (n.contains("Toe") or n.contains("Foot")) and not n.ends_with("Nub"):
			kopyta.append(i)
	print("KLIP_RYCHLOST kopyta %s" % str(kopyta.map(func(i: int) -> String: return sk.get_bone_name(i))))
	var zivy: Node = kun.get("_zivy")
	if zivy:
		zivy.set("active", false)
	var inv := kun.global_transform.affine_inverse()
	var vpred := Vector3(0, 0, -1)                      # kun.gd: kun hlavou k -Z (vlastni soustava)
	for jm: String in ["Walk", "Trot", "Gallop", "Walk_L", "Gallop_L"]:
		var k: String = kun.call("_klip", jm)
		if k == "" or not ap.has_animation(k):
			print("KLIP_RYCHLOST %s nenalezen" % jm)
			continue
		var an := ap.get_animation(k)
		var dl := an.length
		ap.play(k)
		var vz: Array = []                                # [cas, kopyto, poloha v soustave kone]
		var dt := 1.0 / 60.0
		var t := 0.0
		while t < dl:
			ap.seek(t, true)
			sk.force_update_all_bone_transforms() if sk.has_method("force_update_all_bone_transforms") else null
			for b: int in kopyta:
				var g := sk.global_transform * sk.get_bone_global_pose(b).origin
				vz.append([t, b, inv * g])
			t += dt
		var rych: Array = []
		for b: int in kopyta:
			var body: Array = vz.filter(func(e: Array) -> bool: return e[1] == b)
			var ymin := INF
			for e: Array in body:
				ymin = minf(ymin, (e[2] as Vector3).y)
			for i in range(1, body.size()):
				var a: Vector3 = body[i - 1][2]
				var c: Vector3 = body[i][2]
				if a.y < ymin + OPORA_M and c.y < ymin + OPORA_M:
					rych.append(-(c - a).dot(vpred) / dt)
		rych.sort()
		var med: float = rych[rych.size() / 2] if not rych.is_empty() else 0.0
		print("KLIP_RYCHLOST %s %.2f m/s (vzorku opory %d, delka klipu %.2f s)" % [jm, med, rych.size(), dl])
	quit()
