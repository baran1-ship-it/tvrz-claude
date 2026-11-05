extends RefCounted
## Vzhled obyvatel (Misa 5. 11.: dobove postavy, kazdy obyvatel vlastni sada - postava, odev, barvy, vlasy, vek).
## Sada = jedna sit se 3 povrchy (hlava, vlasy+oboci s alfa vyrezem, telo+obleceni na jednom atlasu):
## modely/postavy/npc/<sada>_cela.gltf, stavi tools/postavy_q/sestav.sh (Quaternius CC0 + vlastni dobove obleceni).
## Kostra je stejna jako UAL (Armature/Skeleton3D, 65 kosti) - klipy scripts/anim_ual.gd hraji bez retargetu.
## Vyber sady: obyvatel.vzhled -> obyvatele[id] -> podle_role[role] -> zalozni podle pohlavi (nepouzita) -> opakovani
## (pravidla/svet/postavy_vzhled.json). Kdyz sada chybi (balik z_postavy jeste neni na tabletu), vrati [] a lide.gd
## pouzije stary model (Superhero + Peasant).

const SOUBOR := "res://pravidla/svet/postavy_vzhled.json"
static var _d: Dictionary = {}
static var _pouzite: Dictionary = {}


static func data() -> Dictionary:
	if _d.is_empty():
		var f := FileAccess.open(SOUBOR, FileAccess.READ)
		if f:
			var v: Variant = JSON.parse_string(f.get_as_text())
			if v is Dictionary:
				_d = v
	return _d


static func cesta(sada_jm: String) -> String:
	return String(data().get("slozka", "res://modely/postavy/npc/")) + sada_jm + "_cela.gltf"


## Jmeno sady pro obyvatele. Vyslovne prirazeni (obyvatel.vzhled, obyvatele[id]) plati vzdy, i kdyz se sada opakuje
## (napr. nocni strazny = sada straze); pravidlo „kazda sada jen jednou, dokud staci“ jen pro podle_role a zalozni.
## Kontrola 5. 11.: drive se jednou-pravidlo uplatnilo i na vyslovne prirazeni -> hostinsky = krcmar, Mares = pastyr.
static func sada(o: Dictionary) -> String:
	var d := data()
	for k: String in [String(o.get("vzhled", "")), String((d.get("obyvatele", {}) as Dictionary).get(String(o.get("id", "")), ""))]:
		if k != "" and ResourceLoader.exists(cesta(k)):
			_pouzite[k] = true
			return k
	var kandidati: Array = [String((d.get("podle_role", {}) as Dictionary).get(String(o.get("role", "")), ""))]
	kandidati.append_array((d.get("zalozni", {}) as Dictionary).get("muz" if bool(o.get("muz", true)) else "zena", []))
	for k: String in kandidati:
		if k != "" and not _pouzite.has(k) and ResourceLoader.exists(cesta(k)):
			_pouzite[k] = true
			return k
	for k: String in kandidati:
		if k != "" and ResourceLoader.exists(cesta(k)):
			return k
	return ""


## Novy vyber (lide.setup): zapomenout sady pouzite pri minulem rozdeleni.
static func zacni() -> void:
	_pouzite.clear()


## Model obyvatele pod rodicem: [uzel, kostra, site] jako lide.gd _model, nebo [] (sada chybi).
static func model(rodic: Node3D, o: Dictionary, dosah: float) -> Array:
	var k := sada(o)
	if k == "":
		return []
	var ps: PackedScene = load(cesta(k))
	if ps == null:
		return []
	var uzel := Node3D.new()
	uzel.name = "clovek_" + String(o.get("id", k))
	rodic.add_child(uzel)
	var z := ps.instantiate()
	z.name = "postava"             # stejna cesta ke kostre u vsech sad = jedna sdilena knihovna animaci (anim_ual.gd cache)
	uzel.add_child(z)
	var sk := z.find_children("*", "Skeleton3D", true, false)
	if sk.is_empty():
		uzel.queue_free()
		return []
	var geo: Array = []
	for mi in z.find_children("*", "MeshInstance3D", true, false):
		var g := mi as GeometryInstance3D
		g.visibility_range_end = dosah
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		geo.append(g)
	uzel.set_meta("vzhled", k)
	return [uzel, sk[0], geo]
