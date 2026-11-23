extends Node
const Pravidla := preload("res://scripts/pravidla.gd")
## Meřicí trasa (prevzato z Pucharta hra/scripts/mereni.gd, Misa 2. 11.: „zapnu test, proleti mista, na konci data“):
## kamera (a s ni hrac, at se louka a rostliny nacitaji jako pri hre) projede useky z pravidla/svet/mereni_trasa.json,
## kazdy zahrati + mereni; delka snimku ze skutecnych razitek, p50/p95/max, zaseky > 40 ms, kresleni, troj., VRAM.
## „varianty“: cela trasa znovu s jednou vypnutou skupinou (main._ab_skupiny: stiny, louka, rostliny...) - z jedne tabulky
## je videt, co sekani zpusobuje, na kazdem useku. Na konci tabulka na obrazovce (vyfotit) + user://mereni_trasa.txt.

var _vnitrek: Array = []            # bez_vnitrku_vsi: skryte site vnitrku domu vsi
var _houstiny: Array = []           # bez_houstin: skryte MultiMeshe keru houstiny (varianty_parametry.bez_houstin.predpony)
var main: Node
var cfg: Dictionary
var useky: Array = []
var varianty: Array = []
var i_var := 0
var i_us := 0
var t := 0.0
var casy := PackedFloat32Array()
var kres := 0.0
var troj := 0.0
var vz := 0
var _posl := 0
var lbl: Label
var vysledky: Array = []
var _skup: Dictionary
var _sc0 := 1.0
var proc := 0.0
var fyz := 0.0
var gpu := 0.0
var cpu_r := 0.0
var nej: Dictionary = {}                 # nejhorsi snimek useku: ms, skripty, fyzika, gpu, kresleni
var spicky: Array = []                   # snimky nad spicka_ms (cely beh): kde, kolik, rozpad
var spicky_plne: Array = []              # 23. 11. (A1): k nim plny radek detektoru diag (do souboru a schranky, ne na obrazovku)
var _zas0 := 0                           # diag.zaseku v minulem snimku trasy (novy zaznam detektoru = tento snimek)
var nad100 := 0
var _pozice0: Transform3D
var _let0 := false
var _panel0: Array = [false, false]
var _kv0 := false                         # automaticka kvalita pred trasou (behem trasy vypnuta, varianta „auto“ ji zapne)
var _hod0 := -1.0                        # denni doba stoji (0.9991: trasa 30 min, ves uz za soumraku - jine stiny)
# 15. 11. (vykon_postavy_puchart_15_11.md bod 1, mereni_trasa.json lehky_monitor): behem trasy lehky monitor (diag.lehky:
# log a PSS jen na hranicich useku, node_added jen citac, pod krizem vypnuto) a popisek nejvys 1x za popisek_s;
# varianta diag_plny = drivejsi stav (log po 2 s, PSS po 30 s, popisek kazdy snimek)
var _lehky := false
var _lbl_t := 0.0
var _diag0 := false


func zacni(m: Node) -> void:
	main = m
	cfg = Pravidla.soubor("mereni_trasa")
	useky = cfg["useky"]
	varianty = cfg.get("varianty", [""])
	_skup = main._ab_skupiny()
	# automaticka kvalita vypnuta: meri se pevne varianty (kvalita.json popis); vrati se na konci
	if main.kvalita:
		_kv0 = main.kvalita.zapnuto
		main.kvalita.nastav(false)
	_sc0 = get_viewport().scaling_3d_scale
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	# hrac musi stat (kun by mu kazdy krok prepsal polohu na sedlo), poloha a let se po konci vrati (kontrola 2. 11.)
	var pl: Node = main.player
	if pl.na_koni and pl.na_koni.has_method("sesedni"):
		pl.na_koni.sesedni()
	if pl.seated:
		pl.stand_up()
	_pozice0 = pl.global_transform
	_let0 = pl.flying
	if main.ab_vyp != "":
		(_skup0()[main.ab_vyp] as Callable).call(true)
		main.ab_vyp = ""
	pl.set_physics_process(false)
	pl.flying = true
	var cl := CanvasLayer.new()
	cl.layer = 20
	lbl = Label.new()
	lbl.position = Vector2(30, 140)
	lbl.add_theme_font_size_override("font_size", 24)
	lbl.add_theme_color_override("font_outline_color", Color.BLACK)
	lbl.add_theme_constant_override("outline_size", 6)
	cl.add_child(lbl)
	add_child(cl)
	_hod0 = main.day.hour if main.day else -1.0
	_panel0 = [main.mereni_on, main.mereni_fps]
	main.mereni_on = false                  # plny panel sam stoji 7-10 ms (3. 11.) - behem trasy vypnut
	main.mereni_fps = false
	var lm: Dictionary = cfg.get("lehky_monitor", {})
	_lehky = bool(lm.get("zapnuto", false))
	if main.diag:
		_diag0 = bool(main.diag.get("lehky"))
	_varianta(true)
	_monitor()
	_posl = Time.get_ticks_usec()


## Lehky monitor podle varianty (diag_plny = plny jako drive).
func _monitor() -> void:
	var leh := _lehky and String(varianty[i_var]) != "diag_plny"
	if main.diag:
		main.diag.set("lehky", leh)


func _par(v: String) -> Dictionary:
	return (cfg.get("varianty_parametry", {}) as Dictionary).get(v, {})


func _skup0() -> Dictionary:
	return main._ab_skupiny()


func _varianta(zap: bool) -> void:
	var v := String(varianty[i_var])
	if v == "karty_cele":                   # karty travy bez orezu (A/B orezu karet, Misa 4. 11.)
		var lo: Node = main.get_node_or_null("Louka")
		if lo:
			lo.nastav_orez_karet(not zap)
	elif v == "louka_un" or v == "louka_stin":  # trava bez / se stinovym pruchodem slunce (mereni 0.9999)
		var lu: Node = main.get_node_or_null("Louka")
		if lu:
			lu.nastav_unshaded((v == "louka_un") if zap else bool(lu._un0))
	elif v == "trava_gpu":                    # prototyp travy GPU (A/B s loukou)
		var tg: Node = main.get_node_or_null("TravaGPU")
		if tg:
			tg.zapni(zap)
	elif v.begins_with("trava_"):              # kratsi dosah trsu (m) - Misa 3. 11.: louka nejvetsi naklad
		var lk: Node = main.get_node_or_null("Louka")
		if lk:
			lk.nastav_dosah_trsu(float(v.substr(6)) if zap else -1.0)
	elif v == "les_bez_travy":                 # r. 86/88: louka bez travy v lese (zapoj nad les_podrost zapoj_od) - cena travy v lese
		var lt: Node = main.get_node_or_null("Louka")
		if lt:
			lt.nastav_les_bez_travy(zap)
	elif v == "bez_obzoru":                    # Misa 17. 11. r. 13: les za okrajem mapy (Obzor_les, 76 550 impostoru) - cena
		var ob: Node = main.find_child("Obzor_les", true, false)
		if ob:
			(ob as Node3D).visible = not zap
			print("TRASA bez_obzoru: Obzor_les %s" % ("skryt" if zap else "zpet"))
	elif v == "bez_mlhy_vody":                 # 18. 11. (voda Hvozd): billboardy mlhy nad toky skryte - cena prekresleni
		var mv: Node = main.find_child("Mlha_vody", true, false)
		if mv:
			(mv as Node3D).visible = not zap
			print("TRASA bez_mlhy_vody: Mlha_vody %s" % ("skryta" if zap else "zpet"))
	elif v == "les_bez_korun":                 # r. 86/88: stromy jen kmeny (listi pryc, impostory skryte) - cena korun
		_bez_korun(zap)
	elif v == "auto":                          # automaticka kvalita zapnuta (overeni smycky, zmeny stupne v tabulce)
		if main.kvalita:
			main.kvalita.nastav(zap)
	elif v.begins_with("3d_"):                 # rozliseni 3D v % soucasneho: roste-li FPS, brzdi vyplnovani pixelu (GPU)
		get_viewport().scaling_3d_scale = _sc0 * float(v.substr(3)) / 100.0 if zap else _sc0
	elif v == "bez_houstin":                   # 16. 11. (Misa: sceny, houstina jako vrstva krajiny): kere a mlade stromy
		# houstiny skryte (rostliny s predponou z varianty_parametry.bez_houstin.predpony, i bunky vznikle behem varianty
		# se pri dalsim zapnuti skryji) - cena houstiny na tabletu proti vse ve stejnem behu
		var sv_: Object = main.get("svet")
		if sv_ and "trasa_skryt" in sv_:
			sv_.trasa_skryt = (_par(v).get("predpony", []) as Array).duplicate() if zap else []
		if zap:
			_houstiny = []
			var pr: Array = _par(v).get("predpony", [])
			for n in main.world.find_children("*", "GeometryInstance3D", true, false):
				var gi := n as GeometryInstance3D
				for q: String in pr:
					if gi.visible and String(gi.name).begins_with(q):
						gi.visible = false
						_houstiny.append(gi)
						break
			print("TRASA bez_houstin: skryto %d uzlu" % _houstiny.size())
		else:
			for gi: GeometryInstance3D in _houstiny:
				if is_instance_valid(gi):
					gi.visible = true
			_houstiny = []
	elif v == "bez_vnitrku_vsi":               # 14. 11. (0.999996: zasek 2,4 s ve dvorech u usedlosti 6): vnitrek domu vsi
		# (site *Interier* domu a predmety s dosahem ves_vnitrek) skryte - prvni vykresleni vnitrku = podezreni
		if zap:
			_vnitrek = []
			var do_m := float(Pravidla.cti("rozpocty", "ves_vnitrek", "do_m"))
			for n in main.world.find_children("*", "GeometryInstance3D", true, false):
				var gi := n as GeometryInstance3D
				var vnitrni := String(gi.name).contains("Interier") and String(gi.get_parent().name).begins_with("Dum_ves_")
				if gi.visible and (vnitrni or (gi.visibility_range_end > 0.0 and gi.visibility_range_end <= do_m + 0.01)):
					gi.visible = false
					_vnitrek.append(gi)
		else:
			for gi: GeometryInstance3D in _vnitrek:
				if is_instance_valid(gi):
					gi.visible = true
			_vnitrek = []
	elif v == "bez_stropu_koster" or v == "modif_pripojene":   # 15. 11. body 2 a 4: drivejsi stav (bez stropu kroku animace / modifikatory stale na kostre)
		var ls: Node = main.world.get_node_or_null("Lide") if main.world else null
		if ls:
			var ks := "strop" if v == "bez_stropu_koster" else "odpojit"
			if zap:
				ls.trasa_vypni[ks] = true
			else:
				ls.trasa_vypni.erase(ks)
	elif v == "postavy_daleko":                # 15. 11. bod 5: za 45 m bez animace, dohled postav 70 -> 50 m (postavy.json daleko_varianta)
		var ld: Node = main.world.get_node_or_null("Lide") if main.world else null
		if ld:
			ld.nastav_daleko(zap)
	elif v == "louka_bez_stinu":               # 15. 11. bod 6: louka bez stinoveho pruchodu slunce (bunky stin nevrhaji uz ted)
		var lb: Node = main.get_node_or_null("Louka")
		if lb:
			lb.nastav_bez_stinu(zap)
	elif v == "louka_puchart":                 # 15. 11. bod 6: trs krok_m, plna do od_m, ridne do do_m (varianty_parametry)
		var lp: Node = main.get_node_or_null("Louka")
		if lp:
			var pp: Dictionary = _par(v)
			lp.nastav_puchart(zap, float(pp.get("krok_m", 0.5)), float(pp.get("od_m", 14.0)), float(pp.get("do_m", 60.0)))
	elif v == "stin_filtr_1":                  # 15. 11. bod 8: filtr stinu slunce (Compatibility: 2 = PCF 5, 1 = jeden vzorek)
		var q0 := int(ProjectSettings.get_setting_with_override("rendering/lights_and_shadows/directional_shadow/soft_shadow_filter_quality"))
		var q := int(_par(v).get("kvalita", 1)) if zap else q0
		RenderingServer.directional_soft_shadow_filter_set_quality(q as RenderingServer.ShadowQuality)
	elif v == "dohled_kratsi":                 # 15. 11. (Misa: zpusobuje sekani dalka?): far kamery a dosahy viditelnosti x faktor
		_dohled(zap)
	elif v == "teren_dlazdice":                # 16. 11. K4: teren na dlazdice s LOD (pravidla/svet/teren_dlazdice.json) proti celym sitim
		var td: Node3D = main.svet.teren_dlazdice if main.svet else null
		if td:
			td.zapni(zap, true)
	elif v == "diag_plny":                     # 15. 11. bod 1: plny monitor jako drive (prepina _monitor)
		pass
	elif v == "bez_pss":                       # 23. 11. (A1 podezreni): PSS (cteni /proc/self/smaps_rollup ve vlakne) se necte
		if main.diag:
			main.diag.set("pss_vyp", zap)
	elif v == "dest":                          # 13. 11.: cena deste (pocasi.gd z Pucharta) - plny dest po celou variantu
		if main.pocasi:
			main.pocasi.vynuceno = 1.0 if zap else -1.0
	elif v == "postavy_skryte" or v == "postavy_stoji":   # 13. 11.: rozdeli cenu postav na kresleni (skryte, logika bezi) a logiku (stoji, kresli se)
		var lx: Node = main.world.get_node_or_null("Lide") if main.world else null
		if lx:
			if v == "postavy_skryte":
				(lx as Node3D).visible = not zap
			else:
				lx.process_mode = Node.PROCESS_MODE_DISABLED if zap else Node.PROCESS_MODE_INHERIT
	elif v == "bez_postav":                    # rozbor 0.99993: 32 postav (skinning, AI, stin do 15 m) - kresleni i skripty
		var li: Node = main.world.get_node_or_null("Lide") if main.world else null
		if li:
			(li as Node3D).visible = not zap
			li.process_mode = Node.PROCESS_MODE_DISABLED if zap else Node.PROCESS_MODE_INHERIT
	elif v in ["bez_sukne", "bez_uchopu", "bez_modifikatoru", "bez_animace", "chuze_lod"]:  # 13. 11. regrese 0.99999 (postavy +8-10 ms): izolovany test skupin
		var lm: Node = main.world.get_node_or_null("Lide") if main.world else null
		if lm:
			var k := {"bez_sukne": "sukne", "bez_uchopu": "uchop", "bez_modifikatoru": "modifikatory", "bez_animace": "animace", "chuze_lod": "chuze_plna"}[v] as String
			if zap:
				lm.trasa_vypni[k] = true
			else:
				lm.trasa_vypni.erase(k)
	elif v == "bez_svetel":                    # rozbor 0.99993: ohne a svetla (life.lights, i ve dne) skryta
		for d: Dictionary in main.life.lights:
			var l: Light3D = d["light"]
			if is_instance_valid(l):
				if zap:
					d["_trasa_vis"] = l.visible
					l.visible = false
				elif d.has("_trasa_vis"):
					l.visible = bool(d["_trasa_vis"])
					d.erase("_trasa_vis")
	elif v == "svetla_bez_stinu":              # rozbor 0.99993: zadne vsesmerove svetlo se stinem (kvalita life 0)
		main.life.set_quality(0 if zap else main.quality)
	elif v != "" and _skup.has(v):
		(_skup[v] as Callable).call(not zap)


var _dohled0 := {}                       # varianta dohled_kratsi: GeometryInstance3D -> [begin, end] puvodni
var _far0 := 0.0


## Varianta dohled_kratsi (Misa 15. 11.: „dělají sekání dálky?“; varianty_parametry.dohled_kratsi): far kamery a
## visibility_range (begin i end, LOD prechody) vsech uzlu s koncem nad od_m nasobene faktor - vcetne uzlu, ktere
## vzniknou behem varianty (streamovani rostlin, louky, dilu; node_added). Rozdil proti „vse“ = vliv dalky.
func _dohled(zap: bool) -> void:
	var cam: Camera3D = main.player.cam
	if zap:
		_far0 = cam.far
		cam.far = _far0 * float(_par("dohled_kratsi").get("faktor", 0.6))
		for n in main.get_tree().root.find_children("*", "GeometryInstance3D", true, false):
			_dohled_uzel(n)
		if not main.get_tree().node_added.is_connected(_dohled_novy):
			main.get_tree().node_added.connect(_dohled_novy)
		print("TRASA dohled_kratsi: far %.0f -> %.0f m, uzlu %d" % [_far0, cam.far, _dohled0.size()])
	else:
		if main.get_tree().node_added.is_connected(_dohled_novy):
			main.get_tree().node_added.disconnect(_dohled_novy)
		if _far0 > 0.0:
			cam.far = _far0
		for g: Variant in _dohled0:
			if is_instance_valid(g):
				(g as GeometryInstance3D).visibility_range_begin = float(_dohled0[g][0])
				(g as GeometryInstance3D).visibility_range_end = float(_dohled0[g][1])
		_dohled0.clear()


func _dohled_novy(n: Node) -> void:
	if n is GeometryInstance3D:
		_dohled_uzel.call_deferred(n)            # dosah se casto nastavuje az po add_child


func _dohled_uzel(n: Variant) -> void:
	if not is_instance_valid(n) or _dohled0.has(n):
		return
	var g := n as GeometryInstance3D
	if g == null:
		return
	var pp: Dictionary = _par("dohled_kratsi")
	if g.visibility_range_end <= float(pp.get("od_m", 40.0)):
		return
	var f := float(pp.get("faktor", 0.6))
	_dohled0[g] = [g.visibility_range_begin, g.visibility_range_end]
	g.visibility_range_begin *= f
	g.visibility_range_end *= f


var _koruny0 := {}                        # varianta les_bez_korun: MultiMeshInstance3D -> [puvodni sit, viditelnost]


## Varianta les_bez_korun (r. 86/88): kazdemu stromu (sit s povrchem kury i listi) sit jen z povrchu kury, impostory
## (vzdalene koruny) skryte; kere a byliny beze zmeny. Kmeny zustanou - rozdil proti „vse“ = cena korun (listi, stin).
## Sit kmene je bez LOD urovni (jen pro mereni).
func _bez_korun(zap: bool) -> void:
	if not zap:
		for mmi: MultiMeshInstance3D in _koruny0:
			if is_instance_valid(mmi):
				if _koruny0[mmi][0] != null:
					mmi.multimesh.mesh = _koruny0[mmi][0]
				mmi.visible = bool(_koruny0[mmi][1])
		_koruny0.clear()
		return
	var kmeny := {}
	for rs in main.get_tree().root.find_children("Rostliny", "Node3D", true, false):
		for n in rs.find_children("*", "MultiMeshInstance3D", true, false):
			var mmi := n as MultiMeshInstance3D
			if String(mmi.name).begins_with("impostor"):
				_koruny0[mmi] = [null, mmi.visible]
				mmi.visible = false
				continue
			var me: Mesh = mmi.multimesh.mesh if mmi.multimesh else null
			if me == null:
				continue
			if not kmeny.has(me):
				kmeny[me] = _jen_kura(me)
			if kmeny[me] == null:
				continue
			_koruny0[mmi] = [me, mmi.visible]
			mmi.multimesh.mesh = kmeny[me]
	print("TRASA les_bez_korun: %d MultiMeshu stromu jen kmeny, %d druhu siti" % [_koruny0.size(), kmeny.values().filter(func(x: Variant) -> bool: return x != null).size()])


## Sit jen z povrchu kury (material „kura*“); null, kdyz sit nema kuru i listi (neni strom).
func _jen_kura(me: Mesh) -> Mesh:
	var am := ArrayMesh.new()
	var listi := false
	for i in me.get_surface_count():
		var mt := me.surface_get_material(i)
		if mt and String(mt.resource_name).contains("kura"):
			am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, me.surface_get_arrays(i))
			am.surface_set_material(am.get_surface_count() - 1, mt)
		else:
			listi = true
	return am if am.get_surface_count() > 0 and listi else null


func _jm(v: String) -> String:
	if v == "":
		return "vše" if varianty.find("") == i_var else "vše znovu"
	if v == "auto":
		return "auto -%d" % (main.kvalita.stupen if main.kvalita else 0)
	if v.begins_with("3d_"):
		return "3D x" + v.substr(3) + "%"
	if v == "trava_gpu":
		return "tráva GPU"
	if v == "louka_un":
		return "tráva bez stínu"
	if v == "louka_stin":
		return "tráva se stínem"
	if v == "karty_cele":
		return "karty bez ořezu"
	if v == "bez_postav":
		return "bez postav"
	if v == "postavy_skryte":
		return "post. skryté"
	if v == "postavy_stoji":
		return "post. stojí"
	if v == "bez_sukne":
		return "bez sukně"
	if v == "bez_uchopu":
		return "bez úchopů"
	if v == "bez_modifikatoru":
		return "bez modif."
	if v == "bez_animace":
		return "bez animace"
	if v == "chuze_lod":
		return "chůze LOD"
	if v == "les_bez_travy":
		return "les-tráva"
	if v == "les_bez_korun":
		return "les-koruny"
	if v == "bez_houstin":
		return "bez houštin"
	if v == "bez_obzoru":
		return "bez obzoru"
	if v == "bez_svetel":
		return "bez světel"
	if v == "svetla_bez_stinu":
		return "svět.bez st"
	if v == "diag_plny":
		return "diag plný"
	if v == "bez_pss":
		return "bez PSS"
	if v == "bez_stropu_koster":
		return "bez stropu"
	if v == "modif_pripojene":
		return "modif.na k."
	if v == "postavy_daleko":
		return "post. 45/50"
	if v == "louka_bez_stinu":
		return "louka b.st"
	if v == "louka_puchart":
		return "louka Puch"
	if v == "stin_filtr_1":
		return "filtr st.1"
	if v == "dohled_kratsi":
		return "dohled x%.1f" % float(_par(v).get("faktor", 0.6))
	if v == "teren_dlazdice":
		return "terén dlažd."
	if v.begins_with("trava_"):
		return "tráva " + v.substr(6) + "m"
	return String(main.AB_NAZVY.get(v, v)).substr(0, 10)


func _bod(u: Dictionary, f: float) -> Array:
	var a: Array = u["od"]
	var b: Array = u["do"]
	var c: Array = u["cil"]
	var x := lerpf(float(a[0]), float(b[0]), f)
	var z := lerpf(float(a[1]), float(b[1]), f)
	var p := Vector3(x, main.svet._vyska(x, z) + float(u.get("nad", 1.7)), z)
	var cc := Vector3(float(c[0]), main.svet._vyska(float(c[0]), float(c[1])) + float(c[2]), float(c[1]))
	return [p, cc]


func _process(d: float) -> void:
	if i_var >= varianty.size():
		return
	var now := Time.get_ticks_usec()
	var ms := (now - _posl) / 1000.0
	_posl = now
	var u: Dictionary = useky[i_us]
	if _hod0 >= 0.0 and absf(main.day.hour - _hod0) > 0.05:
		main.day.set_hour(_hod0, 0.0)
	t += d
	var zah := float(cfg.get("zahrati_s", 5.0))
	var celk := zah + float(cfg.get("mereni_s", 20.0))
	var pc: Array = _bod(u, clampf(t / celk, 0.0, 1.0))
	main.player.global_position = (pc[0] as Vector3) - Vector3(0, 1.6, 0)
	main.player.cam.global_transform = Transform3D(Basis.looking_at((pc[1] as Vector3) - (pc[0] as Vector3), Vector3.UP), pc[0])
	var vrid := get_viewport().get_viewport_rid()
	# merene skripty (diag: soucet _process systemu za minuly snimek); Performance.TIME_PROCESS je cely snimek, ne skripty
	# (0.9995: sloupec skr = 18-29 ms = delka snimku)
	var pr: float = main.diag._skripty_us() / 1000.0 if main.diag and main.diag.has_method("_skripty_us") else 0.0
	var fy := Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
	var gp := RenderingServer.viewport_get_measured_render_time_gpu(vrid)
	var cr := RenderingServer.viewport_get_measured_render_time_cpu(vrid)
	var kr := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
	# spicky v cele trase (i pri zahrati - tam byva kompilace shaderu a nacitani)
	var dg: Node = main.diag
	if ms > float(cfg.get("spicka_ms", 200.0)) and spicky.size() < int(cfg.get("spicky_max", 12)):
		# rešerše 10. 11. krok 2b (Android: málo volné paměti = snímky přes 1 s): paměť u každé špičky
		# 11. 11. (trasa 0.99998: „volna -0, halda 0“): OS.get_memory_info a get_static_memory_usage na tabletu vraci 0 -
		# hodnoty z diag (volna z /proc/meminfo, halda Debug.getNativeHeapAllocatedSize)
		# 23. 11. (A1, 0.9999994 hostinec 3029 ms „skripty 0 fyzika 0“): skripty a fyzika ted z razitek uzavreneho snimku
		# diag (drive skripty minuleho snimku a Performance.TIME_PHYSICS_PROCESS = max kroku za 1 s - pro spicku
		# nepouzitelne), rozpad kresleni (pred / CPU / swap), cas v useku, co pribylo a nacetlo se (diag.nacteno_text);
		# plny radek detektoru diag (udalosti planovace a louky, fronty, PSS) do souboru a schranky
		var vol_mb := -1.0
		var hal_mb := -1.0
		var rozpad := "fyz - skr -"
		var nac := "-"
		if dg:
			dg.ram_mb()
			vol_mb = float(dg.get("_volna"))
			hal_mb = float(dg.get("_ram"))
			if dg.has_method("rozpad_kratky"):
				rozpad = dg.rozpad_kratky()
				nac = dg.nacteno_text(dg.get("_sn"))
		var kr_sp := "%.0f ms %s %.1f s %s/%s u (%.0f, %.0f): %s, kresleni %d, uzly %d, volna %.0f MB, halda %.0f MB, vram %.0f MB" % [ms,
				"zahrati" if t <= zah else "mereni", t, String(varianty[i_var]), u["jmeno"], (pc[0] as Vector3).x, (pc[0] as Vector3).z,
				rozpad, kr, int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)), vol_mb, hal_mb,
				Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0]
		spicky.append(kr_sp)
		var det := "(detektor diag snímek nezapsal)"
		if dg and int(dg.get("zaseku")) > _zas0 and not (dg.get("_zaseky") as Array).is_empty():
			det = String((dg.get("_zaseky") as Array)[0])
		spicky_plne.append(kr_sp + "\n    " + nac + "\n    diag: " + det)
		print("TRASA SPICKA " + kr_sp + " | " + nac + " | " + det)
	if dg:
		_zas0 = int(dg.get("zaseku"))
	if t > zah:
		casy.append(ms)
		kres += kr
		troj += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
		proc += pr
		fyz += fy
		gpu += gp
		cpu_r += cr
		vz += 1
		if ms > 100.0:
			nad100 += 1
		if ms > float(nej.get("ms", 0.0)):
			# fyzika nejhorsiho snimku z razitek diag (TIME_PHYSICS_PROCESS je max kroku za 1 s, ne tento snimek)
			var fy_sn: float = float((dg.get("_sn") as Dictionary).get("fyzika", 0)) / 1000.0 if dg else fy
			nej = {"ms": ms, "pr": pr, "fy": fy_sn, "gp": gp, "kr": kr}
	var vn := String(varianty[i_var])
	_lbl_t -= d
	if _lbl_t <= 0.0 or not bool(main.diag.get("lehky") if main.diag else false):
		_lbl_t = float((cfg.get("lehky_monitor", {}) as Dictionary).get("popisek_s", 1.0))
		lbl.text = "MĚŘICÍ TRASA – varianta %d/%d: %s   úsek %d/%d: %s   %.0f s" % [i_var + 1, varianty.size(), _jm(vn),
				i_us + 1, useky.size(), u["jmeno"], celk - t]
	if t < celk:
		return
	var s := casy.duplicate()
	s.sort()
	var n := maxi(s.size(), 1)
	var zas := 0
	var nad := 0
	var nad_ms := float(cfg.get("nad_ms", 33.4))
	for x in s:
		if x > 40.0:
			zas += 1
		if x > nad_ms:
			nad += 1
	vysledky.append({"var": _jm(vn) if vn != "louka" else "bez trávy",  # nazev v okamziku mereni (0.9998: prvni „vse“ se vypsalo jako „vse znovu“)
			 "us": String(u["jmeno"]), "p50": s[n / 2] if s.size() > 0 else 0.0,
			"p95": s[mini(int(n * 0.95), n - 1)] if s.size() > 0 else 0.0, "max": s[n - 1] if s.size() > 0 else 0.0,
			"p99": s[mini(int(n * 0.99), n - 1)] if s.size() > 0 else 0.0, "nad": 100.0 * nad / maxf(s.size(), 1),
			"zas": zas, "n": s.size(), "kres": kres / maxf(vz, 1), "troj": troj / maxf(vz, 1) / 1e6,
			"vram": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0,
			"proc": proc / maxf(vz, 1), "fyz": fyz / maxf(vz, 1), "gpu": gpu / maxf(vz, 1), "cpur": cpu_r / maxf(vz, 1),
			"n100": nad100, "nej": nej, "halda": float(main.diag.get("_ram")) if main.diag else -1.0,
			"tex": Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0,
			"buf": Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0,
			"uzly": int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))})
	proc = 0.0
	fyz = 0.0
	gpu = 0.0
	cpu_r = 0.0
	nad100 = 0
	nej = {}
	_uloz()                                   # po kazdem useku (0.9991: trasa nedobehla do konce = tabulka ztracena)
	if main.diag and main.diag.has_method("trasa_hranice") and bool(main.diag.get("lehky")):
		main.diag.trasa_hranice("TRASA %s / %s" % [_jm(vn), String(u["jmeno"])])
	casy = PackedFloat32Array()
	kres = 0.0
	troj = 0.0
	vz = 0
	t = 0.0
	i_us += 1
	if i_us >= useky.size():
		_varianta(false)
		i_us = 0
		i_var += 1
		if i_var < varianty.size():
			_varianta(true)
			_monitor()
		else:
			_konec()


func _uloz(hotovo := false) -> void:
	var txt := _tabulka()
	if not hotovo:
		txt = "(trasa nedokončena: %d z %d úseků)\n" % [vysledky.size(), useky.size() * varianty.size()] + txt
	var f := FileAccess.open("user://mereni_trasa.txt", FileAccess.WRITE)
	if f:
		f.store_string(txt)
		f.close()


func _tabulka(plne := true) -> String:
	var vp := get_viewport().get_visible_rect().size
	# 23. 11. (A3, 30 FPS: p50 je vzdy 33 = strop): hlavni je p95, p99 a nad30 = % snimku nad nad_ms (33,4 ms = snimek
	# vypadl z 30 FPS); >40 = pocet snimku nad 40 ms (zaseky jako drive). Sloupce gpu vypusteny (tablet GPU cas nevraci -
	# zaseky_rozbor_system.md F2; na PC je v souboru diag). Porovnani verzi: docs/mereni_verze.md „Jak číst tabulku trasy“.
	var txt := "(ms na snímek; při 30 FPS je p50 vždy 33 – porovnávat p95, p99 a nad30 = %% snímků nad %.1f ms; skr = měřené skripty, cpuR = 0, když zařízení neměří)\nVÝSLEDEK měřicí trasy %s · %s · obrazovka %dx%d, 3D %d %%\n" % [float(cfg.get("nad_ms", 33.4)), Time.get_datetime_string_from_system(),
			main.diag.sestaveni_text() if main.diag and main.diag.has_method("sestaveni_text") else "", int(vp.x), int(vp.y), roundi(_sc0 * 100)]
	txt += "varianta   úsek            p50 p95 p99  max nad30% >40 >100 kresl trojM skr fyz cpuR | nejhorší: ms skr fyz kresl\n"
	for r: Dictionary in vysledky:
		var nj: Dictionary = r["nej"]
		txt += "%-10s %-15s %3.0f %3.0f %3.0f %4.0f %5.1f %4d %4d %5.0f %5.2f %3.0f %3.0f %4.0f | %4.0f %3.0f %3.0f %4d\n" % [
				String(r["var"]), r["us"], r["p50"], r["p95"], float(r.get("p99", 0.0)), r["max"], float(r.get("nad", 0.0)), r["zas"],
				r["n100"], r["kres"], r["troj"], r["proc"], r["fyz"], r["cpur"], float(nj.get("ms", 0)), float(nj.get("pr", 0)),
				float(nj.get("fy", 0)), int(nj.get("kr", 0))]
	var z: Dictionary = vysledky[-1] if not vysledky.is_empty() else {}
	txt += "paměť: VRAM %.0f MB (textury %.0f, buffery %.0f), halda %.0f MB, uzlů %d\n" % [float(z.get("vram", 0)),
			float(z.get("tex", 0)), float(z.get("buf", 0)), float(z.get("halda", 0)), int(z.get("uzly", 0))]
	txt += "špičky nad %.0f ms (%d):\n" % [float(cfg.get("spicka_ms", 200.0)), spicky.size()]
	for sp: String in (spicky_plne if plne else spicky):
		txt += "  " + sp + "\n"
	if main.kvalita and not main.kvalita.historie.is_empty():
		txt += "automatická kvalita – změny (%d):\n" % main.kvalita.zmen
		for h: String in main.kvalita.historie:
			txt += "  " + h + "\n"
	return txt


func _konec() -> void:
	var txt := _tabulka()
	_uloz(true)
	lbl.text = _tabulka(false) + "\n(ms na snímek; tabulka je ve schránce – vlož ji do chatu. Zpět do hry za 60 s.)"
	print(txt)
	DisplayServer.clipboard_set(txt)
	await get_tree().create_timer(60.0).timeout
	main.player.global_transform = _pozice0
	main.player.set_flying(_let0)
	main.player.velocity = Vector3.ZERO
	main.player.set_physics_process(true)
	main.mereni_on = bool(_panel0[0])
	main.mereni_fps = bool(_panel0[1])
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), false)
	if main.kvalita:
		main.kvalita.nastav(_kv0)
	if main.diag:
		main.diag.set("lehky", _diag0)
	queue_free()
