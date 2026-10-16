extends Node3D
## Postava jako skládačka (Quaternius): tělo + kusy oblečení na jedné kostře, animace z Universal Animation Library.
## Použití: Node3D s tímto skriptem, nastavit `postava` (muz / zena / kluk).
##   obleci("sukne"), svlekni("kalhoty"), prehraj("Walk_Loop")
## Kusy a výchozí oblečení čte z <postava>_sada.json. Kostra a cesty uzlů jsou stejné jako v UAL
## (Armature/Skeleton3D), takže animace UAL hrají bez retargetu.
## UAL knihovny: v Godotu vybrat UAL1_Standard.glb (a UAL2_Standard.glb) → Import As: Animation Library → Reimport.

@export_dir var slozka := "res://modely/postavy/hrdinove"
@export var postava := "muz"
@export var animace: Array[AnimationLibrary] = []      ## UAL1, UAL2 importované jako Animation Library
@export var nazvy_knihoven: PackedStringArray = ["ual1", "ual2"]
@export var vychozi_animace := "Idle_Loop"

var sada: Dictionary = {}
var telo: Node3D
var kostra: Skeleton3D
var prehravac: AnimationPlayer
var _kusy: Dictionary = {}          # název kusu -> Array[MeshInstance3D]

func _ready() -> void:
	var f := FileAccess.open(slozka.path_join(postava + "_sada.json"), FileAccess.READ)
	if f == null:
		push_error("Chybí sada postavy: " + postava)
		return
	sada = JSON.parse_string(f.get_as_text())
	telo = load(slozka.path_join(sada["telo"])).instantiate()
	add_child(telo)
	kostra = _najdi_kostru(telo)
	for k in sada["vychozi"]:
		obleci(k)
	prehravac = AnimationPlayer.new()
	telo.add_child(prehravac)
	prehravac.root_node = NodePath("..")
	for i in animace.size():
		var jm := nazvy_knihoven[i] if i < nazvy_knihoven.size() else "ual%d" % (i + 1)
		prehravac.add_animation_library(jm, animace[i])
	if not animace.is_empty():
		prehraj(vychozi_animace)

func prehraj(nazev: String, prolnuti := 0.3) -> void:
	if prehravac == null:
		return
	for jm in prehravac.get_animation_library_list():
		var plny := (str(jm) + "/" + nazev) if str(jm) != "" else nazev
		if prehravac.has_animation(plny):
			prehravac.play(plny, prolnuti)
			return
	push_warning("Animace nenalezena: " + nazev)

func obleci(kus: String) -> void:
	if _kusy.has(kus):
		for m in _kusy[kus]:
			m.visible = true
		return
	if not sada["kusy"].has(kus):
		push_warning("Neznámý kus: " + kus)
		return
	var sc: Node = load(slozka.path_join(sada["kusy"][kus]["soubor"])).instantiate()
	var meshe: Array = []
	_sber_meshe(sc, meshe)
	var seznam: Array = []
	for mi in meshe:
		var m := mi as MeshInstance3D
		m.get_parent().remove_child(m)
		kostra.add_child(m)
		m.skeleton = NodePath("..")
		seznam.append(m)
	sc.queue_free()
	_kusy[kus] = seznam

func svlekni(kus: String) -> void:
	if _kusy.has(kus):
		for m in _kusy[kus]:
			m.visible = false

func _najdi_kostru(n: Node) -> Skeleton3D:
	if n is Skeleton3D:
		return n
	for c in n.get_children():
		var s := _najdi_kostru(c)
		if s:
			return s
	return null

func _sber_meshe(n: Node, out: Array) -> void:
	if n is MeshInstance3D:
		out.append(n)
	for c in n.get_children():
		_sber_meshe(c, out)
