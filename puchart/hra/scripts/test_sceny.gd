extends Node
## Hlídač scén (PUCHART_TEST=sceny; GPT „Inteligentní tvorba scén“ bod 9): kamera projde body tras (data/sceny.json,
## nastroje/viditelnost.py) po krok_m ve výšce oka a dívá se po směru trasy. U každého snímku zapíše typ scény,
## vzdálenost kreslení, kreslení (draw calls), trojúhelníky a změnu obrazu proti předchozímu snímku (malý náhled).
## Náhlá změna obrazu při malém posunu = doskakování / viditelný přechod LOD. Výsledek: PUCHART_VYSTUP (JSON),
## vyhodnocení proti rozpočtům a schválenému stavu dělá nastroje/kontrola_scen.py.
var hlavni: Node
var cam: Camera3D
var body: Array = []
var vysl: Array = []
var _pred := PackedByteArray()
var _pr: Dictionary = {}

func zacni(h: Node, c: Camera3D) -> void:
	hlavni = h; cam = c
	var pr: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/sceny_pravidla.json"))["hlidac"]; _pr = pr
	var b: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/sceny.json"))["body"]
	var krok: float = pr["krok_m"]
	for i in b.size() - 1:   # zhuštění po krok_m; skok mezi trasami (> skok_m) = nový začátek
		var a := Vector2(b[i][0], b[i][1]); var e := Vector2(b[i + 1][0], b[i + 1][1])
		if a.distance_to(e) > float(pr["skok_m"]): body.append([a, a + (a - Vector2(b[maxi(i - 1, 0)][0], b[maxi(i - 1, 0)][1])).normalized(), true]); continue
		var n := maxi(1, int(a.distance_to(e) / krok))
		for k in n:
			body.append([a.lerp(e, float(k) / n), e, k == 0 and i == 0])
	hlavni.hrac.set_physics_process(false); cam.top_level = true
	_bez.call_deferred()

func _bez() -> void:
	for i in body.size():
		var p: Vector2 = body[i][0]; var cil: Vector2 = body[i][1]
		var y: float = hlavni.svet.vyska(p.x, p.y) + 1.7
		hlavni.hrac.position = Vector3(p.x, y - 1.65, p.y)
		var smer := (cil - p).normalized() if cil.distance_to(p) > 0.1 else Vector2(0, -1)
		cam.look_at_from_position(Vector3(p.x, y, p.y), Vector3(p.x + smer.x * 10, y, p.y + smer.y * 10), Vector3.UP)
		for f in int(_pr.get("snimku_na_bod", 3)): await get_tree().process_frame
		var img := get_viewport().get_texture().get_image(); img.resize(64, 40, Image.INTERPOLATE_BILINEAR); img.convert(Image.FORMAT_L8)
		var data := img.get_data(); var zmena := -1.0
		if _pred.size() == data.size() and not body[i][2]:
			var s := 0.0
			for k in data.size(): s += absf(float(data[k]) - float(_pred[k]))
			zmena = s / data.size()
		_pred = data
		if i % 20 == 0: print("SCENY_POSTUP %d/%d" % [i, body.size()])
		# kamera ve zdi (spojnice bodů tras vede přes stavbu – 2. 11. falešný doskok u brány B): paprsek dopředu < 1 m
		var q := PhysicsRayQueryParameters3D.create(cam.global_position, cam.global_position - cam.global_basis.z * 1.0)
		var ve_zdi: bool = hlavni.get_world_3d().direct_space_state.intersect_ray(q).size() > 0
		if ve_zdi: _pred = PackedByteArray()   # další snímek neporovnávat se zdí
		vysl.append({"ve_zdi": ve_zdi, "x": snappedf(p.x, 0.1), "z": snappedf(p.y, 0.1), "y": snappedf(y, 0.1), "typ": hlavni.scena_typ, "kresleni_m": snappedf(hlavni._kresleni, 1.0),
			"kresleni": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
			"troj": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME), "zmena": snappedf(zmena, 0.01)})
	var out := OS.get_environment("PUCHART_VYSTUP") if OS.has_environment("PUCHART_VYSTUP") else "user://sceny.json"
	var fl := FileAccess.open(out, FileAccess.WRITE); fl.store_string(JSON.stringify({"snimky": vysl}))
	print("SCENY %d snímků -> %s" % [vysl.size(), out])
	get_tree().quit()
