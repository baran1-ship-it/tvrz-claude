extends Node
## Zvuky prostredi (zvuky/prostredi, zvuky/zvirata; autori v zvuky/seznam.txt):
## - smycky podle mista a denni doby, plynule prolinani (les, louka, ves, nadvori, skaly, senk)
## - prostorove smycky: potok podel toku, rybnik, vyhen v kovarne
## - zvirata jednotlive v nahodnych chvilich podle mista (kohout rano, psi a slepice ve vsi, kukacka v lese...)
## Uvnitr se venkovni ruchy tlumi (life._interior).

const BASE_DB := -16.0
# Misa 0.62: "vypni lesni zver, divne skreky - nech jen zpev ptaku a v noci zaby": les_noc (sova, praskot vetvi),
# tvrz_nadvori (havrani, kun), louka_noc a ves_noc (pes) pryc; v noci vsude zaby a rakosi (rybnik)
const AMB := {
	"les": ["les_den", "rybnik"], "louka": ["louka_den", "rybnik"], "ves": ["ves_den", "rybnik"],
	"tvrz": ["louka_den", "rybnik"], "skaly": ["vitr_skaly", "vitr_skaly"], "senk": ["senk", "senk"],
	"hostinec": ["senk_prazdny", "senk_prazdny"],
}
## body toku Bystrice (z blender/kraj.REKA po ~35 m) a stred rybnika ve vsi
const REKA := [Vector2(945.5, 126.8), Vector2(916.0, 146.8), Vector2(885.8, 166.0), Vector2(866.1, 198.0), Vector2(826.3, 205.5),
	Vector2(800.0, 229.4), Vector2(787.8, 262.6), Vector2(769.3, 296.2), Vector2(729.6, 295.7), Vector2(692.3, 294.7),
	Vector2(664.0, 316.2), Vector2(637.1, 340.1), Vector2(604.6, 355.3), Vector2(589.0, 387.2), Vector2(568.2, 420.3),
	Vector2(529.4, 425.7), Vector2(497.6, 441.2), Vector2(472.0, 469.0), Vector2(439.0, 481.2), Vector2(410.5, 502.8),
	Vector2(382.7, 526.0), Vector2(347.4, 532.2), Vector2(310.1, 535.5), Vector2(293.4, 571.3), Vector2(265.2, 592.4),
	Vector2(226.7, 600.6), Vector2(196.5, 624.0), Vector2(186.6, 657.7), Vector2(189.0, 696.7), Vector2(178.0, 731.2),
	Vector2(183.2, 768.3), Vector2(185.9, 803.5), Vector2(201.5, 837.1), Vector2(206.6, 875.4), Vector2(193.9, 909.5),
	Vector2(201.3, 944.8), Vector2(230.0, 967.7), Vector2(243.8, 1000.9), Vector2(232.9, 1037.0), Vector2(252.1, 1068.5),
	Vector2(278.5, 1092.5), Vector2(284.7, 1127.7), Vector2(276.2, 1167.1), Vector2(273.6, 1204.8), Vector2(284.0, 1238.7),
	Vector2(300.5, 1275.3), Vector2(319.8, 1308.5), Vector2(310.1, 1345.2), Vector2(318.1, 1379.7), Vector2(315.9, 1415.5)]
const RYBNIK := Vector3(525.1, 0.0, 879.4)
const VES := Vector2(470.0, 830.0)
const KOVARNA := Vector3(16.3, 1.2, 6.2)
const STROMY := ["smrk", "dub", "lipa", "buk", "jedle", "olse", "briza", "borovice"]
const LES_BUNKA := 32.0

var main: Node
var _hraj := {}                 # nazev smycky -> AudioStreamPlayer
var _cil := {}                  # nazev -> cilova hlasitost (linearne 0..1)
var _les := {}                  # Vector2i -> pocet stromu v bunce 32 m
var _potok: AudioStreamPlayer3D
var _rybnik: AudioStreamPlayer3D
var _zvirata := {}              # druh -> [AudioStream]
var _za := 6.0                  # za kolik sekund dalsi zvire
var zona := ""


func setup(p_main: Node) -> void:
	main = p_main
	process_mode = Node.PROCESS_MODE_ALWAYS
	# hustota lesa z rozmisteni stromu (svet.json "rostliny")
	var ro: Dictionary = main.svet.data.get("rostliny", {})
	for key: String in ro:
		var ok := false
		for s: String in STROMY:
			if key.begins_with(s):
				ok = true
				break
		if not ok or key.contains("_daleko"):
			continue
		for t: Array in ro[key]:
			var c := Vector2i(floori(float(t[3]) / LES_BUNKA), floori(float(t[11]) / LES_BUNKA))
			_les[c] = int(_les.get(c, 0)) + 1
	_potok = _bod3d("potok", -4.0, 45.0)
	_rybnik = _bod3d("rybnik", -6.0, 50.0)
	_rybnik.position = RYBNIK + Vector3(0, _vyska(RYBNIK), 0)
	var kov := _bod3d("pec_kovarna", -10.0, 16.0)
	kov.position = KOVARNA
	kov.play()
	_rybnik.play()
	_potok.play()


func _stream(path: String) -> AudioStream:
	if not ResourceLoader.exists(path):
		return null
	var st: AudioStream = load(path)
	if st is AudioStreamOggVorbis:
		(st as AudioStreamOggVorbis).loop = true
	return st


var zona_drive := ""             # smycka, ktera hraje, nez se nacte nova
var _nacteno := {}               # nazev -> AudioStream nacteny vlaknem (do vytvoreni prehravace)


## Smycka ze souboru bez cekani: prvni volani spusti nacitani ve vlakne, vraci null, dokud neni hotove.
func _stream_vlakno(path: String) -> AudioStream:
	var jm := path.get_file().get_basename()
	if _nacteno.has(jm):
		return _nacteno[jm]
	if not ResourceLoader.exists(path):
		return null
	var stav := ResourceLoader.load_threaded_get_status(path)
	if stav == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
		ResourceLoader.load_threaded_request(path)
		return null
	if stav == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
		return null
	if stav != ResourceLoader.THREAD_LOAD_LOADED:
		return null
	var st: AudioStream = ResourceLoader.load_threaded_get(path)
	if st is AudioStreamOggVorbis:
		(st as AudioStreamOggVorbis).loop = true
	_nacteno[jm] = st
	return st


func _bod3d(n: String, db: float, dosah: float) -> AudioStreamPlayer3D:
	var p := AudioStreamPlayer3D.new()
	p.stream = _stream("res://zvuky/prostredi/%s.ogg" % n)
	p.volume_db = db
	p.unit_size = 6.0
	p.max_distance = dosah
	p.bus = "Zvuky"
	add_child(p)
	return p


func _vyska(p: Vector3) -> float:
	if main.has_method("_ground_hi"):
		return main._ground_hi(p.x, p.z)
	return 0.0


func _les_hustota(p: Vector3) -> float:
	var c := Vector2i(floori(p.x / LES_BUNKA), floori(p.z / LES_BUNKA))
	var n := 0
	for dx in range(-1, 2):
		for dz in range(-1, 2):
			n += int(_les.get(c + Vector2i(dx, dz), 0))
	return n / 9.0


## Kde hrac je (pro vyber smycky)
func _zona(p: Vector3) -> String:
	var rn: String = main.life.room_name
	if rn.begins_with("hostinec_"):
		return "senk" if rn.ends_with("senk") or rn.ends_with("sin") else "hostinec"
	if p.x > -25.0 and p.x < 17.0 and p.z > -14.0 and p.z < 14.0:
		return "tvrz"
	if Vector2(p.x, p.z).distance_to(VES) < 140.0:
		return "ves"
	if String(main.life.place) == "Skalní město":
		return "skaly"
	return "les" if _les_hustota(p) > 9.0 else "louka"


func _process(dt: float) -> void:
	if main == null or main.player == null or not main.ready_done:
		return
	var p: Vector3 = main.player.global_position
	var noc: bool = main.day.is_night()
	zona = _zona(p)
	var jmeno: String = AMB[zona][1 if noc else 0]
	for n: String in _cil:
		_cil[n] = 0.0
	_cil[jmeno] = 1.0
	if not _hraj.has(jmeno):
		var a := AudioStreamPlayer.new()
		a.stream = _stream("res://zvuky/prostredi/%s.ogg" % jmeno)
		a.volume_db = -60.0
		a.bus = "Zvuky"
		a.set_meta("lin", 0.0)
		add_child(a)
		a.play()
		_hraj[jmeno] = a
	# uvnitr (krome hostince, kde je ruch vlastni) se venku tlumi
	var tlum := 1.0
	if not zona in ["senk", "hostinec"]:
		tlum = 1.0 - float(main.life._interior) * 0.8
	for n: String in _hraj.keys():
		var a: AudioStreamPlayer = _hraj[n]
		var lin: float = a.get_meta("lin")
		lin = move_toward(lin, float(_cil.get(n, 0.0)), dt / 3.0)          # prolinani 3 s
		a.set_meta("lin", lin)
		if lin <= 0.001:
			a.queue_free()
			_hraj.erase(n)
			_cil.erase(n)
			continue
		a.volume_db = BASE_DB + linear_to_db(maxf(lin * tlum, 0.0001))
	# potok: zvuk z nejblizsiho mista toku
	var q := Vector2(p.x, p.z)
	var best := Vector2.ZERO
	var bd := 1e9
	for i in REKA.size() - 1:
		var a2: Vector2 = REKA[i]
		var b2: Vector2 = REKA[i + 1]
		var ab := b2 - a2
		var t := clampf((q - a2).dot(ab) / ab.length_squared(), 0.0, 1.0)
		var c2 := a2 + ab * t
		var d := c2.distance_squared_to(q)
		if d < bd:
			bd = d
			best = c2
	_potok.position = Vector3(best.x, p.y, best.y)
	# zvirata vypnuta (hracovi vadila); _zvire(dt, p, noc)


func _zvuk_zvirete(druh: String) -> AudioStream:
	if not _zvirata.has(druh):
		var arr: Array = []
		for i in range(1, 7):
			var path := "res://zvuky/zvirata/%s_%d.ogg" % [druh, i]
			if ResourceLoader.exists(path):
				arr.append(load(path))
		_zvirata[druh] = arr
	var a: Array = _zvirata[druh]
	return a.pick_random() if not a.is_empty() else null


## Jednotlive hlasy zvirat v okoli (podle mista a casu), vzdy z nahodneho smeru 8-40 m od hrace.
func _zvire(dt: float, p: Vector3, noc: bool) -> void:
	_za -= dt
	if _za > 0.0:
		return
	_za = randf_range(9.0, 26.0)
	if zona in ["senk", "hostinec"] or String(main.life.room_name) != "" or float(main.life._interior) > 0.3 or bool(main.player.seated):          # jen venku, ne v posteli
		return
	var h: float = main.day.hour
	var moznosti: Array = []
	# Misa 19. 10.: skreky z lesa (vrany, sovy) pryc - jen ptaci (kukacka, datel) a zaby u vody
	match zona:
		"ves":
			moznosti = ["slepice", "slepice", "pes_stekot", "ovce"] if not noc else ["pes_stekot"]
			if h > 4.5 and h < 8.0:
				moznosti += ["kohout", "kohout"]
		"tvrz":
			moznosti = ["kun_odfrknuti", "slepice"] if not noc else ["kun_odfrknuti"]
			if h > 4.5 and h < 8.0:
				moznosti.append("kohout")
		"les":
			moznosti = ["datel", "kukacka"] if not noc else []
		"louka":
			moznosti = ["kukacka"] if not noc else []
	if Vector2(p.x, p.z).distance_to(Vector2(RYBNIK.x, RYBNIK.z)) < 45.0:
		moznosti += ["zaba", "zaba"]
	# prikop kolem tvrze (obvod ~35 m od stredu)
	var dt_ := Vector2(p.x + 4.5, p.z).length()
	if dt_ > 22.0 and dt_ < 55.0:
		moznosti += ["zaba", "zaba", "zaba"]
	if moznosti.is_empty():
		return
	var st := _zvuk_zvirete(moznosti.pick_random())
	if st == null:
		return
	var a := randf() * TAU
	var r := randf_range(8.0, 40.0)
	main.life.sfx_stream(st, randf_range(-6.0, 0.0), randf_range(0.95, 1.05), p + Vector3(cos(a) * r, randf_range(1.0, 6.0), sin(a) * r))
