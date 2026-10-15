extends Node
## Predmety ve svete a v brasne: katalog (modely/predmety.json), inventar hrace, polozene predmety
## (truhly s obsahem, lavice, sudy...), rezim pokladani v piskovisti a ulozeni do hry.

const KATALOG := "res://modely/predmety.json"
const DIR := "res://modely/predmety/"

var main: Node
var kat: Dictionary = {}            # id -> {nazev, kat, stav, vaha, cena, rozmer, kont?, sed?, lehat?}
var inv: Dictionary = {}            # id -> pocet (brasna hrace)
var placed: Array = []              # [{id, p: Vector3, yaw: float, obsah: {id: pocet}, node: Node3D}]
var _scenes: Dictionary = {}
var _icons: Dictionary = {}
var root: Node3D

# pokladani
var placing := ""
var _ghost: Node3D
var _gyaw := 0.0
var _gdist := 2.0
var _ui: CanvasLayer
var _from_inv := false
var _moving: Dictionary = {}       # presouvany polozeny predmet (pri zruseni se vrati na misto)
var _valid := true
var _wall := false
var _wall_yaw := 0.0
var _bad_mat: StandardMaterial3D


func setup(p_main: Node, world: Node3D) -> void:
	main = p_main
	var f := FileAccess.open(KATALOG, FileAccess.READ)
	if f:
		kat = JSON.parse_string(f.get_as_text())
	root = Node3D.new()
	root.name = "Predmety"
	world.add_child(root)
	_build_place_ui()


func icon(id: String) -> Texture2D:
	if not _icons.has(id):
		_icons[id] = load(DIR + id + ".png")
	return _icons[id]


func scene(id: String) -> PackedScene:
	if not _scenes.has(id):
		_scenes[id] = load(DIR + id + ".glb")
	return _scenes[id]


func name_of(id: String) -> String:
	return String(kat.get(id, {}).get("nazev", id))


func weight(items: Dictionary) -> float:
	var w := 0.0
	for id: String in items:
		w += float(kat.get(id, {}).get("vaha", 0.0)) * int(items[id])
	return w


func add_inv(id: String, n: int = 1) -> void:
	inv[id] = int(inv.get(id, 0)) + n
	if int(inv[id]) <= 0:
		inv.erase(id)


func start_kit() -> void:
	# pocatecni vybava do piskoviste
	inv = {"sekera": 1, "stit": 1, "lucerna": 1, "miska": 2, "lzice": 2, "talir": 2, "kosik": 1}


# ------------------------------------------------------------------ polozene predmety

func ground_y(x: float, z: float, top := 3.0) -> float:
	var space := root.get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(Vector3(x, top, z), Vector3(x, top - 8.0, z))
	var h := space.intersect_ray(q)
	return float((h["position"] as Vector3).y) if not h.is_empty() else 0.0


func spawn_on_wall(id: String, from: Vector3, dir: Vector3, extra := {}) -> void:
	# vychozi vybaveni: predmet na zed, kam dopadne vodorovny paprsek
	var space := root.get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(from, from + dir * 6.0)
	var h := space.intersect_ray(q)
	if h.is_empty():
		return
	var nrm: Vector3 = h["normal"]
	var r: Array = kat.get(id, {}).get("rozmer", [0.2, 0.2, 0.2])
	var yaw := atan2(nrm.x, nrm.z)
	var p: Vector3 = (h["position"] as Vector3) + nrm * (float(r[2]) * 0.5 + WALL_GAP) - Vector3.UP * float(r[1]) * 0.5
	var rec := {"id": id, "p": p, "yaw": yaw, "spin": 0.0, "obsah": {}}
	rec.merge(extra, true)
	spawn(rec)


func spawn(rec: Dictionary) -> void:
	var id: String = rec["id"]
	if not kat.has(id) or scene(id) == null:
		return                              # predmet ze starsiho ulozeni, ktery uz neexistuje
	var info: Dictionary = kat.get(id, {})
	var n := Node3D.new()
	n.position = rec["p"]
	n.rotation.y = float(rec["yaw"])
	root.add_child(n)
	if rec.has("spin"):
		n.rotate_object_local(Vector3.BACK, float(rec["spin"]))
	var m: Node3D = scene(id).instantiate()
	n.add_child(m)
	# voda v nadobach (kad, vedro): stejna ziva hladina jako kad na kaleni v kovarne
	for gi in m.find_children("*", "MeshInstance3D", true, false):
		var mi := gi as MeshInstance3D
		for si in mi.mesh.get_surface_count():
			var sm := mi.mesh.surface_get_material(si)
			if sm and String(sm.resource_name).begins_with("voda") and main.svet:
				mi.set_surface_override_material(si, main.svet.material("voda"))
	if bool(rec.get("tilt", false)) and not rec.has("orient"):
		rec["orient"] = 1                   # starsi ulozeni
	var r: Array = dims(id, int(rec.get("orient", 0)))
	m.transform = orient_xf(id, int(rec.get("orient", 0)))
	if (info.get("louc", false) or SVETLA.has(id)) and not rec.has("auto") and not NE_DO_RUKY.has(id):
		rec["auto"] = true                 # sviti samo vecer a v noci, dokud ho hrac neovlada rucne
	if info.get("louc", false):
		if not rec.has("louc"):
			rec["louc"] = true
			rec["hori"] = true
		if bool(rec["auto"]):
			rec["hori"] = is_dark()
		_bracket_torch(rec, n)
	elif SVETLA.has(id) and bool(rec.get("auto", false)):
		rec["hori"] = is_dark()
	rec["node"] = n
	if SVETLA.has(id):
		_light_fx(rec)
	# kolize: vetsi veci zastavi hrace; drobnosti a veci na zdi maji kolizi jen pro pokladani
	# (vrstva 2: na talir jde polozit jablko, na polici svicen, hrac o ne nezakopne)
	if true:
		var b := StaticBody3D.new()
		if not ((float(r[1]) > 0.25 or float(r[0]) > 0.6) and not info.get("zed", false)):
			b.collision_layer = 2
			b.collision_mask = 0
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		# vyska presne po horni plochu (na stul se pokladaji drobnosti), pudorys o kousek mensi
		bs.size = Vector3(float(r[0]) * 0.95, float(r[1]), float(r[2]) * 0.95)
		cs.shape = bs
		cs.position.y = float(r[1]) * 0.5
		b.add_child(cs)
		n.add_child(b)
	rec["node"] = n
	if bool(rec.get("pevne", false)):
		for gi in n.find_children("*", "GeometryInstance3D", true, false):
			(gi as GeometryInstance3D).visibility_range_end = 60.0
			(gi as GeometryInstance3D).visibility_range_end_margin = 8.0
			(gi as GeometryInstance3D).visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	if info.has("jen"):
		show_hung(rec)
	placed.append(rec)
	_refresh_use()


func remove(rec: Dictionary) -> void:
	_torch_off(rec)
	if rec.has("node"):
		(rec["node"] as Node3D).queue_free()
	placed.erase(rec)
	_refresh_use()


func _refresh_use() -> void:
	var use: Array = main.info["use"]
	for i in range(use.size() - 1, -1, -1):
		if String(use[i].get("kind", "")) == "predmet":
			use.remove_at(i)
	for rec: Dictionary in placed:
		var r: Array = kat.get(rec["id"], {}).get("rozmer", [0.5, 0.5, 0.5])
		use.append({"kind": "predmet", "rec": rec, "pos": (rec["p"] as Vector3) + Vector3(0, minf(float(r[1]) * 0.6, 1.2), 0),
				"r": 1.6 + maxf(float(r[0]), float(r[2])) * 0.5})


func _small(id: String) -> bool:
	# drobnost, kterou lze vzit do brasny (ne nabytek)
	var info: Dictionary = kat.get(id, {})
	return info.get("kat", null) != null and float(info.get("vaha", 99)) < 15.0 and not info.get("sed", false)


# svitici predmety: [plamen v lokalnich souradnicich modelu, velikost plamene, sila svetla, dosah, poloha v ruce]
const NE_DO_RUKY := ["lustr", "kotlik_trojnozka"]
const SVETLA := {
	"louc": [Vector3(0, 0.56, 0), 0.42, 1.8, 9.0, Vector3(0.32, -0.42, -0.62)],
	"lucerna": [Vector3(0, 0.2, 0), 0.13, 2.2, 9.5, Vector3(0.36, -0.72, -0.7)],
	"svicen": [Vector3(0, 0.225, 0), 0.09, 0.75, 4.5, Vector3(0.28, -0.45, -0.55)],
	# vicero svicek: prvni bod nese svetlo, ostatni jen plaminek
	"svicny": [[Vector3(-0.005, 0.8, -0.006), Vector3(-0.079, 0.723, 0.145), Vector3(0.095, 0.721, -0.153), Vector3(-0.09, 0.721, -0.141),
			Vector3(0.086, 0.721, 0.157), Vector3(0.178, 0.715, 0.006), Vector3(-0.166, 0.715, 0.006)], 0.07, 1.4, 6.5, Vector3(0.3, -0.92, -0.75)],
	"dvojsvicen": [[Vector3(0.004, 0.366, 0.004), Vector3(-0.11, 0.348, -0.005), Vector3(0.11, 0.347, 0.004)], 0.07, 1.0, 5.0, Vector3(0.3, -0.55, -0.6)],
	"svicen_mosaz": [Vector3(0.004, 0.331, 0.004), 0.07, 0.7, 4.5, Vector3(0.28, -0.5, -0.55)],
	# ohen pod kotlikem na trojnozce (nebere se do ruky, zapaluje se jako krb)
	"kotlik_trojnozka": [Vector3(0, 0.12, 0), 0.75, 2.4, 9.0, Vector3.ZERO],
	"svicen_stojaci": [Vector3(0.0, 1.55, 0.0), 0.09, 1.0, 5.5, Vector3(0.3, -1.5, -0.7)],
	# kruhovy lustr: 4 svice nahore, 8 dole na obruci
	"lustr": [[Vector3(0.0, 0.44, 0.2), Vector3(0.2, 0.44, 0.0), Vector3(0.0, 0.44, -0.2), Vector3(-0.2, 0.44, 0.0),
			Vector3(0.358, 0.31, 0.0), Vector3(0.253, 0.31, 0.254), Vector3(0.0, 0.31, 0.358), Vector3(-0.253, 0.31, 0.254),
			Vector3(-0.358, 0.31, 0.0), Vector3(-0.253, 0.31, -0.254), Vector3(0.0, 0.31, -0.358), Vector3(0.253, 0.31, -0.254)],
			0.06, 1.8, 8.0, Vector3(0.3, -0.9, -0.8)],
}

var held_id := ""                  # co hrac nese v ruce (louc, lucerna, svicen...)
var held_lit := false
var held_torch: bool:
	get:
		return held_id == "louc"
var _hand: Node3D
var _hand_fx: Dictionary = {}


func use_label(u: Dictionary) -> String:
	var rec: Dictionary = u["rec"]
	var info: Dictionary = kat.get(rec["id"], {})
	if info.get("louc", false):
		if bool(rec.get("louc", false)):
			return "" if held_id != "" else "Vzít louč"
		return "Vložit louč" if held_torch else ""
	if SVETLA.has(rec["id"]) and not NE_DO_RUKY.has(rec["id"]):          # lustr visi, ohen pod kotlikem se nebere
		return "" if held_id != "" else "Vzít do ruky"
	if info.has("jen"):
		return "Pověsit zbraň" if info.get("zed", false) else "Uložit zbraň"
	if info.has("kont"):
		return "Otevřít"
	if info.get("lehat", false):
		return "Lehnout si"
	if info.get("sed", false):
		return "Sednout si"
	if info.get("myti", false):
		return "Umýt se"
	if _small(rec["id"]) and not bool(rec.get("pevne", false)):
		return "Sebrat"
	return ""


## U stolu se sedi celem ke stolu (lavice kolmo ke sve delce), jinak zady k mistu, odkud hrac prisel.
func _seat_yaw(rec: Dictionary, fallback: float) -> float:
	var p: Vector3 = rec["p"]
	var best: Dictionary = {}
	var bd := 1.6
	for r: Dictionary in placed:
		if String(r["id"]).begins_with("stul") and (r["p"] as Vector3).distance_to(p) < bd:
			bd = (r["p"] as Vector3).distance_to(p)
			best = r
	if best.is_empty():
		return fallback
	var d: Vector3 = (best["p"] as Vector3) - p
	var dl: Array = kat.get(rec["id"], {}).get("rozmer", [0.5, 0.5, 0.5])
	if float(dl[0]) > 1.0:
		# lavice: smer kolmo k jeji delce (mistni z), na stranu stolu
		var yw := float(rec["yaw"])
		var kz := Vector3(sin(yw), 0.0, cos(yw))
		d = kz * signf(d.dot(kz))
	return atan2(-d.x, -d.z)


## Zvuk polozeni podle materialu predmetu (zvuky/predmety2: polozit_drevo/kov/keramika/latka 1-4).
func zvuk_polozeni(id: String) -> String:
	var k := String(kat.get(id, {}).get("kat", ""))
	for w: String in ["koberec", "kozesina", "polstar", "pytel", "deka", "houne", "plast", "kosile", "slamnik", "kytle"]:
		if id.contains(w):
			return "polozit_latka"
	for w: String in ["hrnec", "dzban", "miska_hlin", "dzban", "pohar_cin", "talir_hlin", "zara", "dzbanek"]:
		if id.contains(w):
			return "polozit_keramika"
	if k in ["zbrane", "zbroj", "naradi"] or id.contains("svicen") or id.contains("lucerna") or id.contains("kotlik") or id.contains("panev"):
		return "polozit_kov"
	if k == "jidlo" or k == "byliny":
		return "polozit_latka"
	return "polozit_drevo"


func zvuk_kontejneru(rec: Dictionary, otevrit: bool) -> String:
	var id := String(rec.get("id", ""))
	var skrin := id.contains("skrin") or id.contains("kredenc") or id.contains("almara")
	return ("skrin_" if skrin else "truhla_") + ("otevrit" if otevrit else "zavrit")


func _zvuk_svetla(id: String, hori: bool) -> String:
	if id == "kotlik_trojnozka":
		return "whoosh" if hori else "kaleni"
	if not hori and (id.contains("svic") or id == "lustr"):
		return "svice_sfouknout"
	return "louc_zapalit" if hori else "louc_zhasnout"


func use(u: Dictionary) -> void:
	var rec: Dictionary = u["rec"]
	var info: Dictionary = kat.get(rec["id"], {})
	if info.get("louc", false):
		if bool(rec.get("louc", false)) and held_id == "":
			rec["louc"] = false
			hold("louc", bool(rec.get("hori", true)))
			_bracket_torch(rec, rec["node"])
			main.life.sfx("presun", -6.0)
		elif not bool(rec.get("louc", false)) and held_torch:
			rec["louc"] = true
			rec["hori"] = held_lit
			hold("", false)
			_bracket_torch(rec, rec["node"])
			main.life.sfx("polozit", -8.0)
		return
	if SVETLA.has(rec["id"]) and not NE_DO_RUKY.has(rec["id"]):          # lustr visi, ohen pod kotlikem se nebere
		if held_id == "":
			hold(rec["id"], bool(rec.get("hori", false)))
			remove(rec)
			main.life.sfx("presun", -6.0)
		return
	if info.has("kont"):
		main.life.sfx(zvuk_kontejneru(rec, true), -4.0)
		main.open_container(rec)
		return
	if info.get("sed", false) or info.get("lehat", false):
		var r: Array = info.get("rozmer", [0.5, 0.5, 0.5])
		var pl: CharacterBody3D = main.player
		var back := pl.global_position
		if info.get("lehat", false):
			# lehnout na postel a nabidnout spanek
			pl.sit((rec["p"] as Vector3) + Vector3(0, 0.15, 0), 0.62, back, pl.yaw, deg_to_rad(55))
			main.offer_sleep()
		else:
			var seat_h := minf(float(r[1]), 0.5) if float(r[1]) > 0.3 else float(r[1])
			pl.sit(rec["p"], seat_h + 0.78, back, _seat_yaw(rec, pl.yaw + PI))
		main.life.sfx("lehnout" if info.get("lehat", false) else "sednout", -6.0)
		return
	if info.get("myti", false):
		# oplachnuti v kadi (spina a jeji vliv prijdou s pribehem)
		# oplachnuti obliceje: dve sploupnuti vody z dlani (ne bublani)
		main.life.sfx("vedro_voda", -4.0, 1.12)
		get_tree().create_timer(0.55).timeout.connect(func() -> void: main.life.sfx("vedro_voda", -6.0, 1.22))
		main.hud.toast("Opláchl ses studenou vodou – jsi čistý.", 2.4)
		return
	if _small(rec["id"]) and not bool(rec.get("pevne", false)):
		add_inv(rec["id"])
		_drop_contents(rec)
		remove(rec)
		main.life.sfx("presun", -6.0)
		main.hud.toast("%s – do brašny" % name_of(rec["id"]), 1.4)


func drop_label() -> String:
	return "Odložit: %s" % name_of(held_id) if held_id != "" else ""


func drop_held() -> void:
	# polozit nesene svetlo pred sebe na zem (hori dal, pokud horelo)
	if held_id == "":
		return
	var pl: CharacterBody3D = main.player
	var f: Vector3 = -(pl.cam as Camera3D).global_transform.basis.z
	f.y = 0.0
	var p: Vector3 = pl.global_position + f.normalized() * 0.8
	p.y = ground_y(p.x, p.z, pl.global_position.y + 1.2)
	var rec := {"id": held_id, "p": p, "yaw": pl.yaw, "obsah": {}, "hori": held_lit, "auto": false}
	hold("", false)
	spawn(rec)
	main.life.sfx(zvuk_polozeni(String(rec["id"])), -6.0)


func use2_label(u: Dictionary) -> String:
	# X: zapalit / zhasnout svetlo v ruce, v drzaku nebo polozene
	if held_id != "":
		return "Zhasnout" if held_lit else "Zapálit"
	if not u.is_empty() and String(u.get("kind", "")) == "predmet":
		var rec: Dictionary = u["rec"]
		if bool(rec.get("louc", false)) or SVETLA.has(rec["id"]):
			return "Zhasnout" if bool(rec.get("hori", false)) else "Zapálit"
	return ""


func use2(u: Dictionary) -> void:
	if held_id != "":
		hold(held_id, not held_lit)
		main.life.sfx(_zvuk_svetla(held_id, held_lit), -8.0)
		return
	if not u.is_empty() and String(u.get("kind", "")) == "predmet":
		var rec: Dictionary = u["rec"]
		if bool(rec.get("louc", false)):
			rec["hori"] = not bool(rec.get("hori", false))
			rec["auto"] = false
			_bracket_torch(rec, rec["node"])
		elif SVETLA.has(rec["id"]):
			rec["hori"] = not bool(rec.get("hori", false))
			rec["auto"] = false
			_light_fx(rec)
		else:
			return
		main.life.sfx(_zvuk_svetla(String(rec["id"]), bool(rec["hori"])), -8.0)


# ------------------------------------------------------------------ louce a svetla

func _fire_fx(parent: Node3D, tips: Variant, energy: float, rng: float, size := 0.42) -> Dictionary:
	# plamen (castice ve svetovych souradnicich, tahnou se za pohybem) a mihotave svetlo se stiny;
	# u svicnu s vice svickami ma kazda svicka plaminek, svetlo je jedno (vykon)
	var tip := Node3D.new()
	var extra: Array = []
	if tips is Array:
		tip.position = tips[0]
		for k in range(1, (tips as Array).size()):
			var cf: Sprite3D = main.life._candle_flame(Vector3.ZERO, 0.075)
			cf.get_parent().remove_child(cf)
			tip.add_child(cf)
			cf.position = (tips[k] as Vector3) - (tips[0] as Vector3) + Vector3(0, 0.026, 0)
			extra.append(cf)
	else:
		tip.position = tips
	parent.add_child(tip)
	var fl: CPUParticles3D = main.life._flames(Vector3.ZERO, size, 14 if size > 0.3 else 8, 0.5 if size > 0.3 else 0.35)
	fl.get_parent().remove_child(fl)
	tip.add_child(fl)
	fl.position = Vector3.ZERO
	var l := OmniLight3D.new()
	l.light_color = main.life.FIRE_COL
	l.light_energy = energy
	l.omni_range = rng
	l.omni_attenuation = 1.4
	l.shadow_enabled = false            # stiny prideluje life._shadow_budget (jen nejblizsi svetlo)
	l.shadow_bias = 0.06
	l.shadow_normal_bias = 1.2
	l.position = Vector3(0, 0.15 if size > 0.3 else 0.05, 0) if extra.is_empty() else Vector3(0, -0.02, 0)
	tip.add_child(l)
	var ld := {"light": l, "base": energy, "phase": randf() * 50.0, "speed": randf_range(8.0, 12.0),
			"night_only": false, "fx": [fl], "shadow": true}
	main.life.lights.append(ld)
	return {"tip": tip, "ld": ld}


func _kill_fx(fx: Dictionary) -> void:
	if fx.is_empty():
		return
	main.life.lights.erase(fx["ld"])
	(fx["tip"] as Node3D).queue_free()


func _torch_off(rec: Dictionary) -> void:
	if rec.has("_fx"):
		_kill_fx(rec["_fx"])
		rec.erase("_fx")
	if rec.has("_louc") and is_instance_valid(rec["_louc"]):
		(rec["_louc"] as Node3D).queue_free()
	rec.erase("_louc")


func _light_fx(rec: Dictionary) -> void:
	# polozena lucerna, svicen...: plamen podle stavu
	if rec.has("_fx"):
		_kill_fx(rec["_fx"])
		rec.erase("_fx")
	if rec.has("_praskani"):
		(rec["_praskani"] as Node).queue_free()
		rec.erase("_praskani")
	if bool(rec.get("hori", false)) and rec.has("node"):
		var sv: Array = SVETLA[rec["id"]]
		rec["_fx"] = _fire_fx(rec["node"], sv[0], sv[2], sv[3], sv[1])
		if rec["id"] == "kotlik_trojnozka" and main.life._sounds.has("fire"):
			# praskani ohne pod kotlikem (stejna nahravka jako krb)
			var p3 := AudioStreamPlayer3D.new()
			p3.stream = main.life._sounds["fire"]
			p3.volume_db = -6.0
			p3.unit_size = 2.5
			p3.max_distance = 18.0
			p3.position = sv[0]
			(rec["node"] as Node3D).add_child(p3)
			p3.play()
			rec["_praskani"] = p3


func _bracket_torch(rec: Dictionary, n: Node3D) -> void:
	# louc v drzaku (objimka 6 cm od zdi), pripadne horici
	_torch_off(rec)
	if not bool(rec.get("louc", false)):
		return
	var t: Node3D = scene("louc").instantiate()
	var lp: Array = kat.get(rec["id"], {}).get("louc_pos", [])
	if lp.size() == 3:
		t.position = Vector3(lp[0], lp[1], lp[2])        # stojan: louc svisle v kalichu
	else:
		t.position = Vector3(0, -0.03, 0.057)
		t.rotation.x = deg_to_rad(12)
	n.add_child(t)
	rec["_louc"] = t
	if bool(rec.get("hori", false)):
		rec["_fx"] = _fire_fx(t, Vector3(0, 0.56, 0), 1.6, 7.5)


func hold(id: String, lit: bool) -> void:
	# svetlo v ruce: vpravo dole pred kamerou, plamen se pohupuje s chuzi a tahne se za pohybem
	if _hand:
		_kill_fx(_hand_fx)
		_hand_fx = {}
		_hand.queue_free()
		_hand = null
	held_id = id
	held_lit = lit and id != ""
	if id == "":
		return
	var sv: Array = SVETLA[id]
	_hand = Node3D.new()
	_hand.position = sv[4]
	_hand.rotation = Vector3(deg_to_rad(-14 if id == "louc" else -4), 0, deg_to_rad(-8 if id == "louc" else 0))
	main.player.cam.add_child(_hand)
	var t: Node3D = scene(id).instantiate()
	_hand.add_child(t)
	for mi in t.find_children("*", "GeometryInstance3D", true, false):
		(mi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if held_lit:
		_hand_fx = _fire_fx(_hand, sv[0], sv[2] * 1.1, sv[3] * 1.15, sv[1])


func _hold_torch(on: bool, lit: bool) -> void:
	hold("louc" if on else "", lit)


func delete(rec: Dictionary) -> void:
	# stavebni rezim: odstranit predmet (obsah truhly se presune do brasny)
	var n := _drop_contents(rec)
	remove(rec)
	main.life.sfx("polozit", -8.0, 0.8)
	main.hud.toast("Odstraněno" + (" – obsah je v brašně" if n > 0 else ""), 1.6)


func _drop_contents(rec: Dictionary) -> int:
	var n := 0
	var ob: Dictionary = rec.get("obsah", {})
	for id: String in ob:
		add_inv(id, int(ob[id]))
		n += int(ob[id])
	rec["obsah"] = {}
	return n


func nearest(cam: Camera3D) -> Dictionary:
	# nejblizsi polozeny predmet, na ktery se hrac diva (pro stavebni rezim)
	var best := {}
	var best_d := 1e9
	var eye := cam.global_position
	var fwd := -cam.global_transform.basis.z
	for u: Dictionary in main.info["use"]:
		if String(u.get("kind", "")) != "predmet":
			continue
		var to: Vector3 = (u["pos"] as Vector3) - eye
		var d := to.length()
		if d > float(u["r"]) + 1.0 or (d > 0.9 and fwd.dot(to / d) < 0.6):
			continue
		if d < best_d:
			best_d = d
			best = u
	return best


# ------------------------------------------------------------------ pokladani (piskoviste)

func begin_place(id: String, from_inv: bool) -> void:
	cancel_place()
	placing = id
	_from_inv = from_inv
	_ghost = Node3D.new()
	_ghost_m = scene(id).instantiate()
	_ghost.add_child(_ghost_m)
	root.add_child(_ghost)
	_gorient = 0
	_snap = {}
	for mi in _ghost.find_children("*", "GeometryInstance3D", true, false):
		(mi as GeometryInstance3D).transparency = 0.35
		(mi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var r: Array = kat.get(id, {}).get("rozmer", [0.5, 0.5, 0.5])
	_gdist = 1.3 + maxf(float(r[0]), float(r[2])) * 0.7
	_gyaw = 0.0
	_valid = true
	_ui.visible = true


var _move_menu := false            # presun zahajeny z menu staveni (po polozeni zpet do menu)


func begin_move(rec: Dictionary, from_menu := false) -> void:
	# zvednout polozeny predmet a hned ho pokladat jinam (obsah truhly zustava)
	if rec.is_empty():
		return
	var keep := rec.duplicate()
	remove(rec)
	keep.erase("node")
	begin_place(String(keep["id"]), false)
	_moving = keep
	_move_menu = from_menu
	_gorient = int(keep.get("orient", 0))
	_ghost_m.transform = orient_xf(placing, _gorient)
	_gyaw = float(keep["yaw"]) - (main.player.yaw + PI)


func cancel_and_back() -> void:
	# B pri pokladani z katalogu: zpet do menu staveni
	var back := placing != "" and (_moving.is_empty() or _move_menu)
	var pg := "brasna" if _from_inv and _moving.is_empty() else "staveni"
	cancel_place()
	if back:
		main.menu_hrace.show_page(pg, {}, true)


func cancel_place() -> void:
	if not _moving.is_empty():
		var back := _moving
		_moving = {}
		spawn(back)
	if _ghost:
		_ghost.queue_free()
	_ghost = null
	placing = ""
	_move_menu = false
	if _ui:
		_ui.visible = false


func rotate_place(step: float) -> void:
	_gyaw += step


const POLOHY := ["Naležato", "Nastojato", "Nastojato obráceně", "Na bok", "Zapíchnuté do země"]


func toggle_tilt() -> void:
	# postaveni dokola: nalezato, nastojato, nastojato obracene, na bok (otaceni kolem dokola zvlast)
	if placing == "" or not can_tilt(placing):
		return
	_gorient = (_gorient + 1) % (5 if can_stick(placing) else 4)
	_ghost_m.transform = orient_xf(placing, _gorient)
	main.life.sfx("presun", -12.0, 1.2)
	main.hud.toast(POLOHY[_gorient], 0.9)


func confirm_place() -> void:
	if placing == "" or _ghost == null:
		return
	if not _valid:
		main.hud.toast("Tady to nejde postavit", 1.2)
		return
	if not _snap.is_empty():
		# zbran do haku nebo stojanu
		var tgt: Dictionary = _snap
		var ob: Dictionary = tgt["obsah"]
		ob[placing] = int(ob.get(placing, 0)) + 1
		show_hung(tgt)
		if _from_inv:
			add_inv(placing, -1)
		elif not _moving.is_empty():
			_moving = {}
		main.life.sfx("polozit_kov", -6.0)
		var back0 := "brasna" if _from_inv else "staveni"
		var mm0 := _move_menu
		var was_move := _from_inv == false and mm0
		cancel_place()
		if _from_inv or not was_move:
			main.menu_hrace.show_page(back0, {}, true)
		return
	var rec := {"id": placing, "p": _ghost.global_position, "yaw": _ghost.rotation.y, "obsah": {}}
	if _gorient != 0:
		rec["orient"] = _gorient
	if _wall:
		rec["yaw"] = _wall_yaw
		rec["spin"] = _gyaw
	if not _moving.is_empty():
		rec["obsah"] = _moving.get("obsah", {})
		_moving = {}
		spawn(rec)
		main.life.sfx(zvuk_polozeni(String(rec["id"])), -4.0)
		var mm := _move_menu
		cancel_place()
		if mm:
			main.menu_hrace.show_page("staveni", {}, true)
		return
	if _from_inv:
		add_inv(placing, -1)
	spawn(rec)
	main.life.sfx(zvuk_polozeni(String(rec["id"])), -4.0)
	var back := "brasna" if _from_inv else "staveni"
	cancel_place()
	# zpet do menu, odkud predmet prisel (stejna zalozka a radek); dalsi kus se nebere sam
	main.menu_hrace.show_page(back, {}, true)


func _process(_delta: float) -> void:
	if _ghost == null or main.player == null:
		return
	var cam: Camera3D = main.player.cam
	var fwd := -cam.global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	var p: Vector3 = main.player.global_position + fwd * _gdist
	# zem paprskem shora (prochazi pres podlahy, vybere prvni povrch pod urovni oci)
	var space := root.get_world_3d().direct_space_state
	var r0: Array = kat.get(placing, {}).get("rozmer", [0.5, 0.5, 0.5])
	if kat.get(placing, {}).get("zed", false):
		# predmet na zed: paprsek z oci, zavesi se na svislou plochu (stred na miste, kam hrac miri)
		var eye := cam.global_position
		var wq := PhysicsRayQueryParameters3D.create(eye, eye - cam.global_transform.basis.z * 3.5)
		wq.exclude = [main.player.get_rid()]
		var wh := space.intersect_ray(wq)
		_wall = not wh.is_empty() and absf((wh["normal"] as Vector3).y) < 0.35
		if _wall:
			var nrm: Vector3 = wh["normal"]
			_wall_yaw = atan2(nrm.x, nrm.z)
			var b := Basis(Vector3.UP, _wall_yaw).rotated(nrm, _gyaw)
			_ghost.global_transform = Transform3D(b, (wh["position"] as Vector3) + nrm * (float(r0[2]) * 0.5 + WALL_GAP) - b.y * float(r0[1]) * 0.5)
			_set_valid(true)
			return
	_wall = false
	# zbran / stit / naradi miri na hak nebo stojan s volnym mistem: zaklapne se do nej
	_snap = _find_snap(cam)
	if not _snap.is_empty():
		var sn: Node3D = _snap["node"]
		_ghost.global_transform = sn.global_transform * _hung_xf(_snap, placing, _used_slots(_snap))
		_ghost_m.transform = Transform3D.IDENTITY
		_set_valid(true)
		return
	_ghost_m.transform = orient_xf(placing, _gorient)
	var q := PhysicsRayQueryParameters3D.create(p + Vector3(0, 1.6, 0), p + Vector3(0, -3.0, 0))
	q.exclude = [main.player.get_rid()]
	var hit := space.intersect_ray(q)
	if not hit.is_empty():
		p = hit["position"]
	_ghost.global_position = p
	_ghost.rotation.y = main.player.yaw + PI + _gyaw
	# kontrola mista: kvadr predmetu (bez spodnich 6 cm) nesmi zasahovat do zdi ani jinych veci
	var r: Array = dims(placing, _gorient)
	var bs := BoxShape3D.new()
	bs.size = Vector3(float(r[0]) * 0.85, maxf(0.02, float(r[1]) - 0.08), float(r[2]) * 0.85)
	var sq := PhysicsShapeQueryParameters3D.new()
	sq.shape = bs
	var lift := 0.06 + 0.08 * maxf(float(r[0]), float(r[2]))      # mirny svah pod predmetem nevadi
	sq.transform = Transform3D(Basis(Vector3.UP, _ghost.rotation.y), p + Vector3(0, lift + bs.size.y * 0.5, 0))
	sq.exclude = [main.player.get_rid()]
	var ok := space.intersect_shape(sq, 1).is_empty()
	if ok:
		# misto musi byt videt (nepokladat za zed nebo skrz podlahu)
		var eye2 := cam.global_position
		var tgt := p + Vector3(0, minf(0.5, float(r[1]) * 0.5), 0)
		var lq := PhysicsRayQueryParameters3D.create(eye2, tgt)
		lq.exclude = [main.player.get_rid()]
		var lh := space.intersect_ray(lq)
		if not lh.is_empty() and (lh["position"] as Vector3).distance_to(tgt) > 0.35:
			ok = false
	_set_valid(ok)


func _set_valid(ok: bool) -> void:
	if ok != _valid:
		_valid = ok
		if _bad_mat == null:
			_bad_mat = StandardMaterial3D.new()
			_bad_mat.albedo_color = Color(1.0, 0.15, 0.1, 0.45)
			_bad_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			_bad_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		for mi in _ghost.find_children("*", "GeometryInstance3D", true, false):
			(mi as GeometryInstance3D).material_overlay = null if ok else _bad_mat


func _build_place_ui() -> void:
	# dotykove ovladani pokladani; na ovladaci: LT/RT otocit, A polozit, B zrusit
	_ui = CanvasLayer.new()
	_ui.layer = 6
	_ui.visible = false
	add_child(_ui)
	var box := HBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	box.position = Vector2(-410, -150)
	box.add_theme_constant_override("separation", 14)
	_ui.add_child(box)
	var font: Font = load("res://fonts/GrenzeGotisch-Medium.ttf")
	for it: Array in [["⟲  LT", func() -> void: rotate_place(PI / 8)], ["Položit  A", confirm_place],
			["Postavení  Y", toggle_tilt], ["Zrušit  B", cancel_and_back], ["RT  ⟳", func() -> void: rotate_place(-PI / 8)]]:
		var b := Button.new()
		b.text = it[0]
		b.custom_minimum_size = Vector2(150, 64)
		b.add_theme_font_override("font", font)
		b.add_theme_font_size_override("font_size", 28)
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.1, 0.08, 0.06, 0.8)
		sb.border_color = Color(0.85, 0.68, 0.38)
		sb.set_border_width_all(2)
		sb.set_corner_radius_all(6)
		b.add_theme_stylebox_override("normal", sb)
		b.add_theme_stylebox_override("hover", sb)
		b.add_theme_stylebox_override("pressed", sb)
		b.add_theme_color_override("font_color", Color(0.95, 0.88, 0.7))
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(it[1])
		box.add_child(b)


# ------------------------------------------------------------------ ulozeni

## Vybaveni vesnice (svet.json "vybaveni"): pevne predmety, neukladaji se, nedaji se odnest ani presunout.
func _spawn_fixed() -> void:
	for rec: Dictionary in placed:
		if bool(rec.get("pevne", false)):
			return
	if main.svet == null:
		return
	for it: Dictionary in main.svet.data.get("vybaveni", []):
		var a: Array = it["p"]
		spawn({"id": String(it["id"]), "p": Vector3(a[0], a[1], a[2]), "yaw": float(it["yaw"]), "obsah": {}, "pevne": true})


func to_save() -> Dictionary:
	var arr := []
	for rec: Dictionary in placed:
		if bool(rec.get("pevne", false)):
			continue
		var p: Vector3 = rec["p"]
		var d := {"id": rec["id"], "p": [p.x, p.y, p.z], "yaw": rec["yaw"], "obsah": rec.get("obsah", {})}
		for k: String in ["spin", "louc", "hori", "auto", "orient"]:
			if rec.has(k):
				d[k] = rec[k]
		arr.append(d)
	return {"inv": inv, "polozene": arr, "v_ruce": held_id, "v_ruce_hori": held_lit}


func from_save(j: Dictionary) -> void:
	for rec: Dictionary in placed.duplicate():
		if not bool(rec.get("pevne", false)):
			remove(rec)
	_spawn_fixed()
	inv = {}
	for id: String in j.get("inv", {}):
		if kat.has(id):
			inv[id] = int(j["inv"][id])
	for r: Dictionary in j.get("polozene", []):
		if not kat.has(String(r["id"])):
			continue
		var a: Array = r["p"]
		var obsah := {}
		for id: String in r.get("obsah", {}):
			obsah[id] = int(r["obsah"][id])
		var rec := {"id": String(r["id"]), "p": Vector3(a[0], a[1], a[2]), "yaw": float(r["yaw"]), "obsah": obsah}
		for k: String in ["spin", "louc", "hori", "auto", "orient"]:
			if r.has(k):
				rec[k] = int(r[k]) if k == "orient" else r[k]
		spawn(rec)
	hold(String(j.get("v_ruce", "")), bool(j.get("v_ruce_hori", false)))


# ------------------------------------------------------------------ automaticka svetla

func is_dark() -> bool:
	return main.day != null and String(main.day.current) in ["soumrak", "noc"]


func on_time(_key: String, _night: bool) -> void:
	# louce ve stojanech a drzacich, lucerny a svicny: vecer a v noci se rozsviti, rano zhasnou
	# (jen ty, ktere hrac rucne nezapnul nebo nezhasl)
	var dark := is_dark()
	for rec: Dictionary in placed:
		if not bool(rec.get("auto", false)) or bool(rec.get("hori", false)) == dark:
			continue
		if kat.get(rec["id"], {}).get("louc", false):
			if bool(rec.get("louc", false)):
				rec["hori"] = dark
				_bracket_torch(rec, rec["node"])
		elif SVETLA.has(rec["id"]):
			rec["hori"] = dark
			_light_fx(rec)


func use3_label(u: Dictionary) -> String:
	if u.is_empty() or String(u.get("kind", "")) != "predmet" or held_id != "":
		return ""
	var rec: Dictionary = u["rec"]
	var info: Dictionary = kat.get(rec["id"], {})
	if (info.get("louc", false) or SVETLA.has(rec["id"])) and not bool(rec.get("auto", true)) and not NE_DO_RUKY.has(rec["id"]):
		return "Svítit samo večer a v noci"
	return ""


func use3(u: Dictionary) -> void:
	var rec: Dictionary = u["rec"]
	rec["auto"] = true
	on_time("", false)
	main.hud.toast("Bude svítit samo večer a v noci", 1.6)


# ------------------------------------------------------------------ hak a stojan na zbrane

func slots(id: String) -> Array:
	return kat.get(id, {}).get("sloty", [])


func show_hung(rec: Dictionary) -> void:
	# zbrane, nastroje a stity na haku (licem ven, delsi osa svisle) nebo ve stojanu (svisle, cepeli nahoru)
	for c: Node in rec.get("_hung", []):
		if is_instance_valid(c):
			c.queue_free()
	rec["_hung"] = []
	if not rec.has("node"):
		return
	var sl := slots(rec["id"])
	var wall: bool = kat.get(rec["id"], {}).get("zed", false)
	var ids: Array = []
	for id: String in rec.get("obsah", {}):
		for k in int(rec["obsah"][id]):
			ids.append(id)
	for i in mini(ids.size(), sl.size()):
		var id: String = ids[i]
		if scene(id) == null:
			continue
		var m: Node3D = scene(id).instantiate()
		m.transform = _hung_xf(rec, id, i)
		(rec["node"] as Node3D).add_child(m)
		rec["_hung"].append(m)


# ------------------------------------------------------------------ uprava polozenych (stavebni rezim)

func rotate_placed(rec: Dictionary, step: float) -> void:
	# otocit na miste o 45 stupnu (predmet na zdi kolem osy zdi)
	var n: Node3D = rec.get("node")
	if n == null:
		return
	if kat.get(rec["id"], {}).get("zed", false):
		rec["spin"] = float(rec.get("spin", 0.0)) + step
		n.rotation = Vector3(0, float(rec["yaw"]), 0)
		n.rotate_object_local(Vector3.BACK, float(rec["spin"]))
	else:
		rec["yaw"] = float(rec["yaw"]) + step
		n.rotation.y = float(rec["yaw"])
	main.life.sfx("presun", -10.0, 0.9)


func take_placed(rec: Dictionary) -> void:
	# vzit polozeny predmet do brasny (i s obsahem)
	_drop_contents(rec)
	add_inv(String(rec["id"]))
	remove(rec)
	main.life.sfx("presun", -6.0)
	main.hud.toast("%s – do brašny" % name_of(rec["id"]), 1.4)


# ------------------------------------------------------------------ postaveni na stojato, zaveseni

const WALL_GAP := 0.035          # viditelna omitka je kousek pred kolizi zdi
var _ghost_m: Node3D
var _gorient := 0
var _snap: Dictionary = {}


func can_tilt(id: String) -> bool:
	var info: Dictionary = kat.get(id, {})
	return not info.get("zed", false) and not info.get("lehat", false) and not info.has("jen")


func can_stick(id: String) -> bool:
	# vidle, lopata, mec, kopi...: dlouhe naradi a zbrane jde zapichnout do zeme (hnoje)
	var kk = kat.get(id, {}).get("kat", null)
	var r: Array = kat.get(id, {}).get("rozmer", [0.5, 0.5, 0.5])
	return kk != null and String(kk) in ["naradi", "zbrane"] and maxf(float(r[0]), float(r[2])) > 0.6


func dims(id: String, o: int) -> Array:
	# rozmer [sirka x, vyska, hloubka z] po postaveni
	var r: Array = kat.get(id, {}).get("rozmer", [0.5, 0.5, 0.5])
	var w := float(r[0])
	var h := float(r[1])
	var d := float(r[2])
	var along_x := w >= d
	match o:
		1, 2, 4:
			return [h, w, d] if along_x else [w, d, h]
		3:
			return [w, d, h] if along_x else [h, w, d]
	return r


func orient_xf(id: String, o: int) -> Transform3D:
	# 1 nastojato (hlava, hroty, cepel nahoru), 2 obracene, 3 na bok (preklopeni kolem delsi osy); spodek na zemi
	var r: Array = kat.get(id, {}).get("rozmer", [0.5, 0.5, 0.5])
	var w := float(r[0])
	var h := float(r[1])
	var d := float(r[2])
	var along_x := w >= d
	match o:
		1:
			if along_x:
				return Transform3D(Basis(Vector3.BACK, PI / 2), Vector3(h * 0.5, w * 0.5, 0))
			return Transform3D(Basis(Vector3.RIGHT, -PI / 2), Vector3(0, d * 0.5, h * 0.5))
		2:
			if along_x:
				return Transform3D(Basis(Vector3.BACK, -PI / 2), Vector3(-h * 0.5, w * 0.5, 0))
			return Transform3D(Basis(Vector3.RIGHT, PI / 2), Vector3(0, d * 0.5, -h * 0.5))
		3:
			if along_x:
				return Transform3D(Basis(Vector3.RIGHT, PI / 2), Vector3(0, d * 0.5, -h * 0.5))
			return Transform3D(Basis(Vector3.BACK, -PI / 2), Vector3(-h * 0.5, w * 0.5, 0))
		4:
			# zapichnute: hlavou (hroty, cepeli) dolu, petina delky v zemi, mirne naklonene
			var L := w if along_x else d
			var t := orient_xf(id, 2)
			return Transform3D(Basis(Vector3.BACK, 0.12) * Basis(Vector3.RIGHT, 0.06), Vector3(0, -L * 0.2, 0)) * t
	return Transform3D.IDENTITY


func _used_slots(rec: Dictionary) -> int:
	var n := 0
	for k: String in rec.get("obsah", {}):
		n += int(rec["obsah"][k])
	return n


func _find_snap(cam: Camera3D) -> Dictionary:
	var kk = kat.get(placing, {}).get("kat", null)
	if kk == null:
		return {}
	var eye := cam.global_position
	var fwd := -cam.global_transform.basis.z
	var best := {}
	var best_d := 0.75
	for rec: Dictionary in placed:
		var info: Dictionary = kat.get(rec["id"], {})
		if not info.has("jen") or not (info["jen"] as Array).has(String(kk)) or not rec.has("node"):
			continue
		var sl := slots(rec["id"])
		var used := _used_slots(rec)
		if used >= sl.size():
			continue
		var s0: Array = sl[used]
		# u stojanu se miri na stojan ve vysce oci, ne na kruzek u zeme
		var lift := 0.0 if info.get("zed", false) else 0.75
		var wp: Vector3 = (rec["node"] as Node3D).to_global(Vector3(s0[0], s0[1] + lift, s0[2]))
		var to := wp - eye
		if to.length() > 3.2:
			continue
		# vzdalenost slotu od primky pohledu
		var t := to.dot(fwd)
		if t < 0.2:
			continue
		var d := (eye + fwd * t).distance_to(wp)
		if d < best_d:
			best_d = d
			best = rec
	return best


func _hung_xf(rec: Dictionary, id: String, i: int) -> Transform3D:
	# poloha zavesene / vlozene veci v lokalnich souradnicich haku nebo stojanu
	var sl := slots(rec["id"])
	var wall: bool = kat.get(rec["id"], {}).get("zed", false)
	var r: Array = kat[id].get("rozmer", [0.2, 0.2, 0.2])
	var dm := [float(r[0]), float(r[1]), float(r[2])]
	var order := [0, 1, 2]
	order.sort_custom(func(a: int, b: int) -> bool: return dm[a] > dm[b])
	var cols := [Vector3.ZERO, Vector3.ZERO, Vector3.ZERO]
	# stity maji horni okraj na -Z (lezi licem nahoru, spicka k +Z): na haku spickou dolu
	cols[order[0]] = Vector3.DOWN if String(kat[id].get("kat", "")) == "zbroj" else Vector3.UP
	cols[order[1]] = Vector3.RIGHT
	cols[order[2]] = Vector3.BACK
	var b := Basis(cols[0], cols[1], cols[2])
	if b.determinant() < 0.0:
		cols[order[1]] = Vector3.LEFT
		b = Basis(cols[0], cols[1], cols[2])
	var L: float = dm[order[0]]
	var thin: float = dm[order[2]]
	var s: Array = sl[clampi(i, 0, sl.size() - 1)]
	var c := Vector3(s[0], s[1], s[2])
	if wall:
		c += Vector3(0, -L * 0.5 + 0.06, thin * 0.5)
	else:
		c += Vector3(0, L * 0.5, 0)
	return Transform3D(b, c - b * Vector3(0, float(r[1]) * 0.5, 0))


func toggle_tilt_placed(rec: Dictionary) -> void:
	rec["orient"] = (int(rec.get("orient", 0)) + 1) % (5 if can_stick(String(rec["id"])) else 4)
	rec.erase("tilt")
	main.hud.toast(POLOHY[int(rec["orient"])], 0.9)
	var keep := rec.duplicate()
	remove(rec)
	keep.erase("node")
	keep.erase("_hung")
	spawn(keep)
	main.life.sfx("presun", -10.0, 1.1)
