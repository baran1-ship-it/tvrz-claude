extends Node
## Funkční dveře a vrata (Míša 3. 11.: „chci funkční brány a vrata“; Havran kit.movable): uzly Pohyb_* z hradu jsou ve glb
## otevřené (průchod pro test i hráče), data/pohyb.json říká úhel, pant (místní osa Y) a kolizi křídla. Hráč do dosah_m
## od místa ovládání dostane tlačítko Otevřít/Zavřít; křídla skupiny (dvoukřídlá vrata) se pohnou spolu, plynule (dur s).
## Zavřené křídlo má kolizi (AnimatableBody3D jako dítě uzlu – pohybuje se s ním).
const DOSAH := 2.6
var hlavni: Node
var dily := {}        # skupina -> [{uzel, otevreny: Transform3D, zavreny: Transform3D}]
var stav := {}        # skupina -> true = otevřeno
var mista := {}       # skupina -> Vector3 (místo ovládání)
var tlacitko: Button
var _blizko := ""

func zacni(h: Node, vrstva: CanvasLayer) -> void:
	hlavni = h
	if not FileAccess.file_exists("res://data/pohyb.json"): return
	var hrad: Node = h.get_node_or_null("Hrad")
	if hrad == null: return
	for e: Dictionary in JSON.parse_string(FileAccess.get_file_as_string("res://data/pohyb.json"))["dily"]:
		var u: Node3D = hrad.find_child(String(e["name"]), true, false)
		if u == null: continue
		var g: String = e.get("group", e["name"])
		var ot := u.transform
		var zav := ot * Transform3D(Basis(Vector3.UP, deg_to_rad(-float(e.get("open", 0.0)))), Vector3.ZERO)
		var t := AnimatableBody3D.new(); t.sync_to_physics = false   # s true (Jolt) zůstala kolize v otevřené poloze – zavřená vrata pustila (pruchod:vrata_funkce)
		for c: Array in e.get("cols", []):
			var sh := CollisionShape3D.new(); var bx := BoxShape3D.new(); bx.size = Vector3(c[3], c[4], c[5])
			sh.shape = bx; sh.position = Vector3(c[0], c[1], c[2]); t.add_child(sh)
		u.add_child(t)
		if not dily.has(g): dily[g] = []
		dily[g].append({"uzel": u, "otevreny": ot, "zavreny": zav, "dur": float(e.get("dur", 1.0))})
		stav[g] = true
		if e.has("use"): mista[g] = Vector3(e["use"][0], e["use"][1], e["use"][2])
	tlacitko = Button.new(); tlacitko.custom_minimum_size = Vector2(260, 90); Styl.tlacitko_pruh(tlacitko, load("res://fonty/GrenzeGotisch-Medium.ttf"), 30, 2)   # svitek (Havran styl.gd)
	tlacitko.anchor_left = 0.5; tlacitko.anchor_right = 0.5; tlacitko.anchor_top = 1.0; tlacitko.anchor_bottom = 1.0
	tlacitko.offset_left = -130; tlacitko.offset_right = 130; tlacitko.offset_top = -170; tlacitko.offset_bottom = -80
	tlacitko.visible = false; tlacitko.pressed.connect(func() -> void: prepni(_blizko))
	vrstva.add_child(tlacitko)
	print("DVERE %d skupin" % dily.size())

func prepni(g: String) -> void:
	if not dily.has(g): return
	stav[g] = not stav[g]
	for d: Dictionary in dily[g]:
		var tw := create_tween(); tw.set_trans(Tween.TRANS_SINE); tw.set_ease(Tween.EASE_IN_OUT)
		tw.tween_property(d["uzel"], "transform", d["otevreny"] if stav[g] else d["zavreny"], d["dur"])
	tlacitko.text = "Zavřít" if stav[g] else "Otevřít"

func _process(_d: float) -> void:
	if tlacitko == null or hlavni.hrac == null: return
	if Engine.get_process_frames() % 6 != 0: return
	var p: Vector3 = hlavni.hrac.global_position + Vector3(0, 1.0, 0)
	var nej := ""; var nd := DOSAH
	for g in mista:
		var dd: float = p.distance_to(mista[g])
		if dd < nd: nd = dd; nej = g
	_blizko = nej
	tlacitko.visible = nej != ""
	if nej != "": tlacitko.text = "Zavřít" if stav[nej] else "Otevřít"
