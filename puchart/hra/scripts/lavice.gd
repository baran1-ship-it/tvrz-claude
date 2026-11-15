extends Node
## Lavice z modelů staveb (Míša 15. 11.: „u modelů domů jsou někdy součástí modelu lavičky, tak ať jsou taky funkční“).
## Lavice není záznam s čísly: hlavni.gd _mista/_celek najde ve vložené stavbě kolizní uzly lavic (mista_stavby.json
## modely.lavice.uzel_vzor) a mista() z jejich kvádru za běhu spočte místa k sezení do hlavni.lavice. Nabídka „Sednout si“
## jako žebříky (zebriky.gd): tlačítko ve stylu dveří nad tlačítkem dveří, jen místo, na které hráč míří a které vidí
## (zamer.gd); stisk = hrac.sit (Havran player.gd sit). Vsedě tlačítko „Vstát“ (hrac.stand_up). Čísla hrac.json sezeni.
const Pravidla := preload("res://scripts/pravidla.gd")
const Zamer := preload("res://scripts/zamer.gd")
var hlavni: Node
var tlacitko: Button
var _vrstva: CanvasLayer
var _blizko: Dictionary = {}   # {m: místo, d} zaměřené místo k sezení do dosahu, prázdné = nic

## Místa k sezení na lavicích stavby n (už ve stromu – globální transformace): pro každý StaticBody3D podle vzoru kvádr
## kolize (BoxShape3D / ConvexPolygonShape3D, v souřadnicích tvaru), delší vodorovná osa = podél lavice, 1–mist_max míst
## po rozestup_m, výška = horní plocha, čelem po normále delší strany ke středu stavby (počátek instance) – zády ke stěně.
## Místo: {pos (sed na horní ploše), yaw, vstat (podlaha před lavicí), lavice (jméno), rid (kolize lavice – zaměření ji přeskočí)}.
static func mista(n: Node3D, vzor: String) -> Array:
	var sz: Dictionary = Pravidla.cti("hrac", "sezeni")
	var out: Array = []
	for sb in n.find_children(vzor, "StaticBody3D", true, false):
		for cs in (sb as Node).find_children("*", "CollisionShape3D", true, false):
			var tv: Shape3D = (cs as CollisionShape3D).shape
			var body := PackedVector3Array()
			if tv is BoxShape3D:
				var h := (tv as BoxShape3D).size * 0.5
				for k in 8: body.append(Vector3(h.x * (1 if k & 1 else -1), h.y * (1 if k & 2 else -1), h.z * (1 if k & 4 else -1)))
			elif tv is ConvexPolygonShape3D: body = (tv as ConvexPolygonShape3D).points
			if body.is_empty(): continue
			var ab := AABB(body[0], Vector3.ZERO)
			for b in body: ab = ab.expand(b)
			var gt: Transform3D = (cs as CollisionShape3D).global_transform
			var c := ab.get_center()
			var podel := Vector3(1, 0, 0) if ab.size.x >= ab.size.z else Vector3(0, 0, 1)   # osy tvaru
			var delka := maxf(ab.size.x, ab.size.z)
			var u := (gt.basis * podel).normalized()
			var nrm := (gt.basis * Vector3(podel.z, 0, podel.x)); nrm.y = 0.0; nrm = nrm.normalized()
			var stred := gt * c
			var k_stredu := n.global_position - stred; k_stredu.y = 0.0
			if nrm.dot(k_stredu) < 0.0: nrm = -nrm
			var vrch := (gt * Vector3(c.x, ab.end.y, c.z)).y; var spod := (gt * Vector3(c.x, ab.position.y, c.z)).y
			var pocet := clampi(int(floor((delka - 2.0 * float(sz["okraj_m"])) / float(sz["rozestup_m"]))) + 1, 1, int(sz["mist_max"]))
			for i in pocet:
				var p := stred + u * ((i - (pocet - 1) * 0.5) * float(sz["rozestup_m"]))
				out.append({"pos": Vector3(p.x, vrch, p.z), "yaw": atan2(-nrm.x, -nrm.z), "vstat": Vector3(p.x, spod, p.z) + nrm * float(sz["vstat_m"]),
					"lavice": "%s/%s" % [n.name, sb.name], "rid": (sb as StaticBody3D).get_rid(), "oci": float(sz["oci_nad_sedu_m"])})
	return out

func zacni(h: Node, vrstva: CanvasLayer) -> void:
	hlavni = h; _vrstva = vrstva
	tlacitko = Button.new(); tlacitko.custom_minimum_size = Vector2(260, 90); Styl.tlacitko_pruh(tlacitko, load("res://fonty/GrenzeGotisch-Medium.ttf"), 30, 2)
	tlacitko.anchor_left = 0.5; tlacitko.anchor_right = 0.5; tlacitko.anchor_top = 1.0; tlacitko.anchor_bottom = 1.0
	tlacitko.offset_left = -170; tlacitko.offset_right = 170; tlacitko.offset_top = -270; tlacitko.offset_bottom = -180
	tlacitko.visible = false; tlacitko.pressed.connect(pouzij)
	vrstva.add_child(tlacitko)
	if vrstva.get("hrac") != null and vrstva.hrac.get("ui") != null: vrstva.hrac.ui.append(tlacitko)   # dotyk na tlačítku nehýbe postavou
	print("LAVICE mist %d" % (h.get("lavice") as Array).size())

## Zaměřené místo k sezení do dosah_m od očí (zamer.gd, kolize lavice se přeskočí): {m, d} nebo {}. Bez kamery nejbližší.
static func nejblizsi(mista_: Array, nohy: Vector3, cam: Camera3D = null) -> Dictionary:
	var sz: Dictionary = Pravidla.cti("hrac", "sezeni")
	var dosah := float(sz["dosah_m"]); var out := {}; var best := 1e9
	var oko := cam.global_position if cam else nohy + Vector3(0, 1.0, 0)
	for m: Dictionary in mista_:
		var d := oko.distance_to(m["pos"])
		if d >= dosah: continue
		var sc := d
		if cam != null:
			sc = Zamer.skore(cam, m["pos"], dosah, [m["rid"]])
			if sc < 0.0: continue
		if sc < best: best = sc; out = {"m": m, "d": d}
	return out

## Sednout na místo m (hrac.sit, Havran player.sit): sed na horní ploše, oči oci nad ní, vstane na vstat.
static func sedni(hrac: CharacterBody3D, m: Dictionary) -> void:
	hrac.sit(m["pos"], float(m["oci"]), m["vstat"], float(m["yaw"]))

func pouzij() -> void:
	var h: CharacterBody3D = hlavni.hrac
	if h == null: return
	if h.seated: h.stand_up()
	elif not _blizko.is_empty(): sedni(h, _blizko["m"])
	_blizko = {}
	if tlacitko: tlacitko.visible = false

func _process(_dt: float) -> void:
	if tlacitko == null or hlavni.hrac == null: return
	if Engine.get_process_frames() % 6 != 0: return
	var h: CharacterBody3D = hlavni.hrac
	var sz: Dictionary = Pravidla.cti("hrac", "sezeni")
	_blizko = {} if (h.seated or h.leze or h.leti) else nejblizsi(hlavni.lavice, h.global_position, h.cam)
	tlacitko.visible = h.seated or not _blizko.is_empty()
	if not tlacitko.visible: return
	tlacitko.text = String(sz["vstat"] if h.seated else sz["nabidka"])
	# nad tlačítkem dveří (−170…−80); nepřekrýt jiné viditelné tlačítko dole uprostřed (žebřík, oheň)
	var nad := -180.0; var posun := true
	while posun:
		posun = false
		for b in _vrstva.get_children():
			if b == tlacitko or not (b is Button) or not (b as Button).visible or (b as Button).anchor_top != 1.0 or (b as Button).anchor_left != 0.5: continue
			if (b as Button).offset_top < nad and (b as Button).offset_bottom > nad - 90.0:
				nad = (b as Button).offset_top - 2.0; posun = true
	tlacitko.offset_bottom = nad; tlacitko.offset_top = nad - 90.0
