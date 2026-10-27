extends RefCounted
## Pravidla sveta z jednoho zdroje (radce 27. 10. 10:45 / 10:55 krok A): pravidla/svet/*.json. Blender (kraj.py)
## i Godot ctou tytez soubory; kod nema vlastni laditelna cisla sveta. Kazde cteni se zapise (test pravidla_cteni:
## klic v JSON, ktery nikdo necte = chyba). Klic precteny = cela jeho vetev (kdo vezme objekt, bere vsechno v nem).
## Klice „popis“, „blender_*“ a vypsane v „jen_blender“ hra necte (popis pro lidi, blender_* jen kraj.py); sekce se „zapojeno“: false jsou
## zalozene (dnesni hodnoty z kodu), zapojeni v dalsim kroku migrace - test je vypise zvlast, ne jako chybu.

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


## Klice souboru, ktere hra neprecetla (pro test pravidla_cteni): vsechny listy objektu do hloubky 3 bez
## precteneho predka; popis a blender_* se nepocitaji.
static func neprectene(nm: String) -> Array:
	var out: Array = []
	if soubor(nm).get("zapojeno", true) == false:
		return out                             # cely soubor zalozeny (napr. katalog modelu), zapojeni dal
	var jb: Array = soubor(nm).get("jen_blender", [])
	for k: String in jb:
		cteno[nm + "/" + k] = true            # cte Blender (kraj.py), hra v dalsim kroku
	cteno[nm + "/jen_blender"] = true
	_projdi(soubor(nm), nm, out, 0)
	return out


static func _projdi(d: Dictionary, cesta: String, out: Array, hl: int) -> void:
	for k: String in d:
		if k == "popis" or k.begins_with("blender_"):
			continue
		var p := cesta + "/" + k
		if cteno.has(p):
			continue
		if d[k] is Dictionary and (d[k] as Dictionary).get("zapojeno", true) == false:
			continue                           # zalozeno, zapojeni v dalsim kroku (test to hlasi zvlast)
		if d[k] is Dictionary and hl < 2:
			_projdi(d[k], p, out, hl + 1)
		else:
			out.append(p)


## Sekce se „zapojeno“: false (zalozene, zatim je kod necte).
static func zalozene(nm: String) -> Array:
	var out: Array = []
	var d := soubor(nm)
	if d.get("zapojeno", true) == false:
		return [nm]
	for k: String in d:
		if d[k] is Dictionary and (d[k] as Dictionary).get("zapojeno", true) == false:
			out.append(nm + "/" + k)
	return out
