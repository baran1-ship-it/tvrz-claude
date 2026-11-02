extends Node
## Test průchodu hradem (PUCHART_TEST=pruchod): postava sama projde trasy z data/pruchody.json (generuje je stavitel
## hradu ze stejné geometrie) – mosty, brány, nádvoří, schody, ochozy, věže. U každého bodu musí být do 0,6 m
## vodorovně (nebo podle 4. čísla bodu) a ve výšce podlahy (±0,5 m); když 3 s nepostoupí o 5 cm, uvízla. Výsledek: stdout + user://pruchod.json.
var hlavni: Node
var hrac: CharacterBody3D
var trasy: Dictionary
var jmena: Array
var ti := 0
var bi := 0
var vysledek := {}
var _posl := Vector3.ZERO
var _cas_posl := 0.0
var _cekej := 0.0

func zacni(h: Node, p: CharacterBody3D) -> void:
	hlavni = h; hrac = p
	trasy = JSON.parse_string(FileAccess.get_file_as_string("res://data/pruchody.json"))["trasy"]
	for f in DirAccess.get_files_at("res://data"):   # trasy dalších stavitelů (pruchody_voda.json …)
		if f.begins_with("pruchody_") and f.ends_with(".json"):
			trasy.merge(JSON.parse_string(FileAccess.get_file_as_string("res://data/" + f))["trasy"])
	jmena = trasy.keys()
	hrac.set_physics_process(true)
	_start_trasy()

func _y(b: Array) -> float:
	return float(b[2]) if b[2] != null else hlavni.svet.vyska(b[0], b[1])

func _start_trasy() -> void:
	if ti >= jmena.size():
		_konec(); return
	var b: Array = trasy[jmena[ti]][0]
	hlavni.svet.kolize_ihned(Vector3(b[0], _y(b), b[1]))
	hrac.velocity = Vector3.ZERO
	hrac.position = Vector3(b[0], _y(b) + 0.15, b[1])
	bi = 1; _cekej = 1.0; _cas_posl = 0.0; _posl = hrac.position
	hrac.autopilot = Vector3.INF

func _physics_process(dt: float) -> void:
	if ti >= jmena.size() or hrac == null:
		return
	if _cekej > 0.0:   # dosednutí po přesunu
		_cekej -= dt; return
	var body: Array = trasy[jmena[ti]]
	var b: Array = body[bi]
	var cil := Vector3(b[0], 0, b[1])
	hrac.autopilot = cil
	var vod := Vector2(hrac.position.x - b[0], hrac.position.z - b[1]).length()
	if vod < (float(b[3]) if b.size() > 3 else 0.6):   # [x, z, y, tolerance] – přesné body (konec schodů)
		if b[2] != null and absf(hrac.position.y - float(b[2])) > 0.5:
			_chyba("bod %d ve výšce %.2f místo %.2f" % [bi, hrac.position.y, float(b[2])]); return
		bi += 1; _cas_posl = 0.0; _posl = hrac.position
		if bi >= body.size():
			vysledek[jmena[ti]] = "OK"; print("PRUCHOD ", jmena[ti], " OK")
			ti += 1; _start_trasy()
		return
	_cas_posl += dt
	if _cas_posl > 3.0:
		if (hrac.position - _posl).length() < 0.05:
			_chyba("uvízla u [%.2f, %.2f, %.2f] na cestě k bodu %d [%.2f, %.2f]" % [hrac.position.x, hrac.position.z, hrac.position.y, bi, b[0], b[1]]); return
		_cas_posl = 0.0; _posl = hrac.position
	if hrac.position.y < -60.0:
		_chyba("propad pod terén"); return

## strom_kolize: postava jde přímo na kmen nejbližšího stromu u startu – kmen ji musí zastavit (matice strom|hrac)
func _test_kmene() -> void:
	var les: Node = hlavni.get_node_or_null("Les")
	if les == null or not les.has_method("nejblizsi_kmen"):
		vysledek["strom_kolize"] = "CHYBA: les bez kolizí kmenů"; return
	var p0 := Vector3(-60, 0, -150)
	var k: Vector4 = les.nejblizsi_kmen(p0)
	if k.x == INF:
		vysledek["strom_kolize"] = "CHYBA: žádný strom u startu"; return
	var smer := Vector3(1, 0, 0)
	var st := Vector3(k.x, 0, k.z) - smer * 3.0; st.y = hlavni.svet.vyska(st.x, st.z) + 0.2
	les.aktualizuj_kolize(Vector3(k.x, k.y, k.z)); hlavni.svet.kolize_ihned(st)
	hrac.velocity = Vector3.ZERO; hrac.position = st
	await get_tree().create_timer(0.5).timeout
	hrac.autopilot = Vector3(k.x + smer.x * 3.0, 0, k.z)
	var nejbliz := INF   # kmen smí postavu odklonit (obejde ho), ale nesmí jím projít: osa kmene ≥ poloměr + kapsle
	for i in 80:
		await get_tree().physics_frame
		nejbliz = minf(nejbliz, Vector2(hrac.position.x - k.x, hrac.position.z - k.z).length())
	hrac.autopilot = Vector3.INF
	vysledek["strom_kolize"] = "OK" if nejbliz > k.w + 0.2 else "CHYBA: prošla kmenem (nejblíž %.2f m od osy, poloměr %.2f)" % [nejbliz, k.w]
	print("PRUCHOD strom_kolize ", vysledek["strom_kolize"])

func _chyba(t: String) -> void:
	for i in hrac.get_slide_collision_count():
		var c := hrac.get_slide_collision(i)
		t += " | narazila na %s v [%.2f, %.2f, %.2f] normála [%.2f, %.2f, %.2f]" % [c.get_collider().get_parent().name if c.get_collider() else "?", c.get_position().x, c.get_position().z, c.get_position().y, c.get_normal().x, c.get_normal().y, c.get_normal().z]
	vysledek[jmena[ti]] = "CHYBA: " + t; print("PRUCHOD ", jmena[ti], " CHYBA ", t)
	ti += 1; _start_trasy()

func _konec() -> void:
	await _test_kmene()
	hrac.autopilot = Vector3.INF
	var f := FileAccess.open(OS.get_environment("PUCHART_VYSTUP") if OS.has_environment("PUCHART_VYSTUP") else "user://pruchod.json", FileAccess.WRITE); f.store_string(JSON.stringify(vysledek, " "))
	var ok := vysledek.values().all(func(v): return v == "OK")
	print("PRUCHOD VYSLEDEK ", "OK" if ok else "CHYBA", " ", vysledek)
	get_tree().quit(0 if ok else 1)
