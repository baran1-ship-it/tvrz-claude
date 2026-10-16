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
@export var vychozi_animace := "Idle"

var sada: Dictionary = {}
var telo: Node3D
var kostra: Skeleton3D
var prehravac: AnimationPlayer
var _kusy: Dictionary = {}          # název kusu -> Array[MeshInstance3D]
var _oblecene: Dictionary = {}      # název kusu -> true (právě oblečené)

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

## Godot při importu odřízne příponu "_Loop" (podle ní zapne smyčku): "Walk_Loop" i "Walk" najdou totéž.
func prehraj(nazev: String, prolnuti := 0.3) -> void:
	if prehravac == null:
		return
	var varianty: Array[String] = [nazev, nazev.trim_suffix("_Loop")]
	for jm in prehravac.get_animation_library_list():
		for n in varianty:
			var plny: String = (str(jm) + "/" + str(n)) if str(jm) != "" else str(n)
			if prehravac.has_animation(plny):
				prehravac.play(plny, prolnuti)
				return
	push_warning("Animace nenalezena: " + nazev)

func obleci(kus: String) -> void:
	if _kusy.has(kus):
		for m in _kusy[kus]:
			m.visible = true
		_oblecene[kus] = true
		_aktualizuj_telo()
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
		m.owner = null
		kostra.add_child(m)
		m.skeleton = NodePath("..")
		seznam.append(m)
	sc.queue_free()
	_kusy[kus] = seznam
	_oblecene[kus] = true
	_aktualizuj_telo()

func svlekni(kus: String) -> void:
	if _kusy.has(kus):
		for m in _kusy[kus]:
			m.visible = false
	_oblecene.erase(kus)
	_aktualizuj_telo()

## Díly těla (MeshInstance3D "<postava>_telo_<díl>") pod oblečenými kusy se skryjí – nepropichují látku a nekreslí se.
func _aktualizuj_telo() -> void:
	if kostra == null:
		return
	var skryt := {}
	for k in _oblecene:
		for d in sada["kusy"][k].get("skryva", []):
			skryt[d] = true
	for c in kostra.get_children():
		if c is MeshInstance3D:
			var jm := String(c.name)
			var i := jm.find("_telo_")
			if i >= 0:
				c.visible = not skryt.has(jm.substr(i + 6))

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
