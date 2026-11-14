extends Node
## Žebříky (Míša 14. 11.: „na půdu hájovny se dá vylézt po žebříku v předsíni – vem si z Havrana funkci lezení po žebříku“).
## Havran svet.gd zebrik_use + main.gd (kind "zebrik"): dole u paty nabídka „Lézt nahoru“, nahoře u vrcholu „Slézt dolů“;
## stisk = hrac.chyt_zebrik. Žebříky jsou záznamy v datech (mista.json modely.celky.<model>.zebrik v souřadnicích modelu),
## hlavni.gd _celek je převede do světa do hlavni.zebriky – jiná stavba se žebříkem = jen záznam v datech.
## Tlačítko ve stylu dveří (dvere.gd, svitek Styl), nad tlačítkem dveří, aby se nepřekrývala.
const Pravidla := preload("res://scripts/pravidla.gd")
var hlavni: Node
var tlacitko: Button
var _blizko: Dictionary = {}   # {zb, nahore, d} nejbližší místo použití do dosahu, prázdné = nic

func zacni(h: Node, vrstva: CanvasLayer) -> void:
	hlavni = h
	if (h.get("zebriky") as Array).is_empty(): return
	tlacitko = Button.new(); tlacitko.custom_minimum_size = Vector2(260, 90); Styl.tlacitko_pruh(tlacitko, load("res://fonty/GrenzeGotisch-Medium.ttf"), 30, 1)
	tlacitko.anchor_left = 0.5; tlacitko.anchor_right = 0.5; tlacitko.anchor_top = 1.0; tlacitko.anchor_bottom = 1.0
	tlacitko.offset_left = -170; tlacitko.offset_right = 170; tlacitko.offset_top = -270; tlacitko.offset_bottom = -180
	tlacitko.visible = false; tlacitko.pressed.connect(pouzij)
	vrstva.add_child(tlacitko)
	if vrstva.get("hrac") != null and vrstva.hrac.get("ui") != null: vrstva.hrac.ui.append(tlacitko)   # dotyk na tlačítku nehýbe postavou
	print("ZEBRIKY %d" % (h.zebriky as Array).size())

## Místa použití žebříku (Havran zebrik_use): dole střed nástup–pata, nahoře mezi sestupem a vrcholem.
static func mista_pouziti(zb: Dictionary) -> Array:
	var lz: Dictionary = Pravidla.cti("hrac", "lezeni")
	return [
		{"pos": (zb["nastup"] as Vector3).lerp(zb["pata"], 0.5) + Vector3(0, float(lz["nad_paty_m"]), 0), "nahore": false},
		{"pos": (zb["sestup"] as Vector3).lerp(zb["vrchol"], float(lz["u_vrcholu"])) + Vector3(0, float(lz["nad_vrcholu_m"]), 0), "nahore": true}]

## Nejbližší místo použití do dosah_m od bodu p (hráč + 1 m): {zb, nahore, d} nebo {}.
static func nejblizsi(zebriky: Array, p: Vector3) -> Dictionary:
	var nd := float(Pravidla.cti("hrac", "lezeni", "dosah_m")); var out := {}
	for zb: Dictionary in zebriky:
		for m: Dictionary in mista_pouziti(zb):
			var d := p.distance_to(m["pos"])
			if d < nd: nd = d; out = {"zb": zb, "nahore": m["nahore"], "d": d}
	return out

func pouzij() -> void:
	if _blizko.is_empty() or hlavni.hrac == null: return
	hlavni.hrac.chyt_zebrik(_blizko["zb"], bool(_blizko["nahore"]))
	_blizko = {}
	if tlacitko: tlacitko.visible = false

func _process(_dt: float) -> void:
	if tlacitko == null or hlavni.hrac == null: return
	if Engine.get_process_frames() % 6 != 0: return
	var h: CharacterBody3D = hlavni.hrac
	_blizko = {} if (h.leze or h.leti) else nejblizsi(hlavni.zebriky, h.global_position + Vector3(0, 1.0, 0))
	tlacitko.visible = not _blizko.is_empty()
	if tlacitko.visible: tlacitko.text = "Slézt dolů" if bool(_blizko["nahore"]) else "Lézt nahoru"
