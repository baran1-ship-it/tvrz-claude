extends RefCounted
## Pravidla sveta z jednoho zdroje (radce 27. 10. 10:45 / 10:55 krok A): pravidla/svet/*.json. Blender (kraj.py)
## i Godot ctou tytez soubory; kod nema vlastni laditelna cisla sveta. Kazde cteni se zapise (test pravidla_cteni:
## klic v JSON, ktery nikdo necte = chyba). Klic precteny = cela jeho vetev (kdo vezme objekt, bere vsechno v nem).
## Klice „popis“, „id“, „nazev“, „jednotky“ (popisne), „blender_*“ a vypsane v „jen_blender“ hra necte (popis pro lidi, blender_* jen kraj.py); sekce se „zapojeno“: false jsou
## zalozene (dnesni hodnoty z kodu), zapojeni v dalsim kroku migrace - test je vypise jako odlozene (rozbor).

const SLOZKA := "res://pravidla/svet/"

static var _soubory := {}
static var cteno := {}                 # "soubor/klic/klic" -> true


static func soubor(nm: String) -> Dictionary:
	if not _soubory.has(nm):
		var t := FileAccess.get_file_as_string(SLOZKA + nm + ".json")
		var d = JSON.parse_string(t)
		_soubory[nm] = d if d is Dictionary else {}
		if not (d is Dictionary):
			push_error("pravidla: %s.json chybi nebo neni objekt" % nm)
	return _soubory[nm]


## Hodnota na ceste klicu v souboru (napr. cti("cesty", "vozove")); zapise se jako prectena.
static func cti(nm: String, a: String, b := "", c := "") -> Variant:
	var v: Variant = soubor(nm).get(a)
	var cesta := nm + "/" + a
	if b != "":
		v = (v as Dictionary).get(b)
		cesta += "/" + b
		if c != "":
			v = (v as Dictionary).get(c)
			cesta += "/" + c
	if v == null:
		push_error("pravidla: chybi %s" % cesta)
	cteno[cesta] = true
	return v


## Rozbor listu souboru pro test pravidla_cteni (Astra 22:00: nacteni vetve neni pouziti): kazdy list (do hloubky 3)
## je prave v jedne skupine - "pouzite" (hra cetla presne ten klic), "vetev" (hra vzala celeho predka, jestli list
## pouziva, test nevi), "odlozene" (jen_blender, zapojeno false) nebo "neprectene" (nikdo = chyba).
static func rozbor(nm: String) -> Dictionary:
	var out := {"pouzite": [], "vetev": [], "odlozene": [], "neprectene": []}
	var jb: Array = soubor(nm).get("jen_blender", [])
	_rozbor(soubor(nm), nm, out, 0, "odlozene" if soubor(nm).get("zapojeno", true) == false else "", jb)
	return out


static func _rozbor(d: Dictionary, cesta: String, out: Dictionary, hl: int, nad: String, jb: Array) -> void:
	for k: String in d:
		if k in ["popis", "id", "nazev", "jednotky", "jen_blender", "zapojeno"] or k.begins_with("blender_"):
			continue
		var p := cesta + "/" + k
		var sk := nad
		# jen_blender: cesta od korene souboru ("ves/rovina_r_m"), i cele vetve ("ruiny")
		if sk == "" and (p.substr(p.find("/") + 1) in jb or (d[k] is Dictionary and (d[k] as Dictionary).get("zapojeno", true) == false)):
			sk = "odlozene"
		var primo := cteno.has(p)
		if d[k] is Dictionary and hl < 2:
			_rozbor(d[k], p, out, hl + 1, sk if sk == "odlozene" else ("vetev" if primo or sk == "vetev" else ""), jb)
		elif sk == "odlozene":
			(out["odlozene"] as Array).append(p)
		else:
			(out["pouzite" if primo else ("vetev" if sk == "vetev" else "neprectene")] as Array).append(p)
