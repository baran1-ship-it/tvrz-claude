extends CanvasLayer
## Po měření (nebo hned, když měření není) předá ovládání hráči: tlačítka běh a rychlé přesuny na zajímavá místa.
## Místa = pravidla (hra/data/mista.json).
var hlavni: Node
var hrac: CharacterBody3D
var mista: Array

func zacni(h: Node, p: CharacterBody3D) -> void:
	hlavni = h; hrac = p
	mista = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista.json"))["mista"]
	var box := VBoxContainer.new(); box.position = Vector2(20, 180)
	add_child(box)
	var b := Button.new(); b.text = "Běh: ne"; b.custom_minimum_size = Vector2(230, 64)
	b.add_theme_font_size_override("font_size", 24)
	b.pressed.connect(func(): hrac.bezi = not hrac.bezi; b.text = "Běh: " + ("ano" if hrac.bezi else "ne"))
	box.add_child(b)
	var mapa: CanvasLayer = load("res://scripts/mapa.gd").new(); mapa.hrac = hrac; add_child(mapa)
	var bm := Button.new(); bm.text = "Mapa"; bm.custom_minimum_size = Vector2(230, 64)
	bm.add_theme_font_size_override("font_size", 24); bm.pressed.connect(mapa.prepni)
	box.add_child(bm)
	for m in mista:
		var t := Button.new(); t.text = m["nazev"]; t.custom_minimum_size = Vector2(230, 56)
		t.add_theme_font_size_override("font_size", 22)
		t.pressed.connect(_presun.bind(m))
		box.add_child(t)
	_presun(mista[0])

func _presun(m: Dictionary) -> void:
	var p: Array = m["kde"]; var c: Array = m["kam"]
	var y: float = float(m["y"]) if m.has("y") else hlavni.svet.vyska(p[0], p[1])
	hlavni.svet.kolize_ihned(Vector3(p[0], y, p[1]))
	hrac.velocity = Vector3.ZERO
	hrac.position = Vector3(p[0], y + 0.3, p[1])
	hrac.nastav_pohled(atan2(-(c[0] - p[0]), -(c[1] - p[1])), -0.05)
