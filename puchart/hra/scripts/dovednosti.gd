extends Node
## Vlohy, umy a zvyky hrace (docs/rozpracovane/navrh_skilly_menu_hrace.md; data pravidla/svet/dovednosti.json).
## Kod hry jen hlasi, co se stalo: main.udalost(id, data) -> udalost(); o XP rozhoduji data (xp_za umu, vloha_xp_za).
## Uceni praci: XP do umu, podil_vloze z toho do jeho vlohy; vyssi vloha uci rychleji (uceni_za_vlohu); stejny skutek
## dokola (omrzelost) dava jen zlomek. Zvyky se odemknou skutkem (podminka um_od + pocet skutku).

const Pravidla := preload("res://scripts/pravidla.gd")
static var D: Dictionary = _nacti()


static func _nacti() -> Dictionary:
	var d := {}
	for k: String in Pravidla.soubor("dovednosti"):
		if not k.begins_with("_") and k != "popis":
			d[k] = Pravidla.cti("dovednosti", k)
	return d

signal uroven(co: String, nazev: String, lv: int)
signal zvyk_odemcen(id: String, nazev: String)

var main: Node
var lv := {}                    # um/vloha -> uroven
var xp := {}                    # um/vloha -> xp do dalsi urovne
var skutky := {}                # skutek -> pocet (pro zvyky a denik)
var zvyky: Array = []           # odemcene zvyky
var _nedavno: Array = []        # [cas_s, skutek] pro omrzelost


func setup(p_main: Node, profil: String) -> void:
	main = p_main
	nastav_profil(profil)


## Pocatecni urovne (profily: mlady / stary; piskoviste = vse na strop - hrac je buh).
func nastav_profil(profil: String) -> void:
	lv.clear()
	xp.clear()
	var strop := int(D["strop"])
	var pr: Dictionary = (D["profily"] as Dictionary).get(profil, {})
	for v: String in D["vlohy"]:
		lv[v] = strop if profil == "buh" else int((pr.get("vlohy", {}) as Dictionary).get(v, 0))
		xp[v] = 0.0
	for u: String in D["umy"]:
		lv[u] = strop if profil == "buh" else int((pr.get("umy", {}) as Dictionary).get(u, 0))
		xp[u] = 0.0


func uroven_of(co: String) -> int:
	return int(lv.get(co, 0))


func nazev_of(co: String) -> String:
	if (D["umy"] as Dictionary).has(co):
		return String(D["umy"][co]["nazev"])
	if (D["vlohy"] as Dictionary).has(co):
		return String(D["vlohy"][co]["nazev"])
	return co


## XP potrebne z urovne n na n+1.
func potreba(co: String, n: int) -> float:
	var k: Dictionary = D["krivka_vloha"] if (D["vlohy"] as Dictionary).has(co) else D["krivka_um"]
	return roundf(float(k["zaklad"]) + float(k["prirustek"]) * pow(float(n), float(k["mocnina"])))


## Jedina vstupni brana: co se stalo -> XP umum a vloham podle dat.
func udalost(id: String, data := {}) -> void:
	skutky[id] = int(skutky.get(id, 0)) + 1
	var t := Time.get_ticks_msec() / 1000.0
	var om: Dictionary = D["omrzelost"]
	_nedavno = _nedavno.filter(func(e: Array) -> bool: return t - float(e[0]) < float(om["okno_min"]) * 60.0)
	_nedavno.append([t, id])
	var stejnych := _nedavno.filter(func(e: Array) -> bool: return String(e[1]) == id).size()
	var krat := float(om["krat"]) if stejnych > int(om["stejny_skutek_max"]) else 1.0
	krat *= float(data.get("krat", 1.0))
	for u: String in D["umy"]:
		var e: Dictionary = D["umy"][u]
		var xz: Dictionary = e["xp_za"]
		if not xz.has(id):
			continue
		if data.has("um") and String(data["um"]) != u:
			continue                                 # udalost pro konkretni um (zbran, kniha)
		var vl := String(e["vloha"])
		var g := float(xz[id]) * krat * (1.0 + float(D["uceni_za_vlohu"]) * uroven_of(vl))
		_pridej(u, g)
		_pridej(vl, g * float(D["podil_vloze"]))
	var vx: Dictionary = (D["vloha_xp_za"] as Dictionary).get(id, {})
	for v: String in vx:
		_pridej(v, float(vx[v]) * krat)
	_zvyky_over(id)


func _pridej(co: String, g: float) -> void:
	var strop := int(D["strop"])
	if uroven_of(co) >= strop or g <= 0.0:
		return
	xp[co] = float(xp.get(co, 0.0)) + g
	while uroven_of(co) < strop and float(xp[co]) >= potreba(co, uroven_of(co)):
		xp[co] = float(xp[co]) - potreba(co, uroven_of(co))
		lv[co] = uroven_of(co) + 1
		uroven.emit(co, nazev_of(co), uroven_of(co))


func _zvyky_over(skutek: String) -> void:
	var sez: Dictionary = D["zvyky"]["seznam"]
	for z: String in sez:
		if zvyky.has(z):
			continue
		var p: Dictionary = sez[z]["podminka"]
		if String(p["skutek"]) == skutek and uroven_of(String(sez[z]["um"])) >= int(p["um_od"]) and int(skutky.get(skutek, 0)) >= int(p["pocet"]):
			zvyky.append(z)
			zvyk_odemcen.emit(z, String(sez[z]["nazev"]))


## Ucinek vlohy na hodnotu hrace (vloha_ucinky): zaklad + plus_za_uroven * lv, nebo hodnota * (1 + krat_za_uroven * lv).
func ucinek(cil: String, hodnota: float) -> float:
	for v: String in D["vloha_ucinky"]:
		for e: Dictionary in D["vloha_ucinky"][v]:
			if String(e["cil"]) != cil:
				continue
			if e.has("zaklad"):
				hodnota = float(e["zaklad"]) + float(e["plus_za_uroven"]) * uroven_of(v)
			elif e.has("plus_za_uroven"):
				hodnota += float(e["plus_za_uroven"]) * uroven_of(v)
			elif e.has("krat_za_uroven"):
				hodnota *= 1.0 + float(e["krat_za_uroven"]) * uroven_of(v)
	return hodnota


## Tabulka po urovni umu: [[od_urovne, a, b], ...] -> posledni radek s od_urovne <= lv.
func z_tabulky(um: String, klic: String) -> Array:
	var vys: Array = []
	for r: Array in D["umy"][um].get(klic, []):
		if uroven_of(um) >= int(r[0]):
			vys = r
	return vys


func to_save() -> Dictionary:
	return {"lv": lv, "xp": xp, "skutky": skutky, "zvyky": zvyky}


func from_save(d: Dictionary) -> void:
	for k in (d.get("lv", {}) as Dictionary):
		lv[String(k)] = int(d["lv"][k])
	for k in (d.get("xp", {}) as Dictionary):
		xp[String(k)] = float(d["xp"][k])
	skutky = (d.get("skutky", {}) as Dictionary).duplicate()
	zvyky = (d.get("zvyky", []) as Array).duplicate()
