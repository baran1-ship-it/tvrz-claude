extends Node
## Test ohňů (Míša 15. 11., chyby.md 274): PUCHART_SKRIPT=res://scripts/test_ohne.gd – počet ohňů z dat, světla v rozpočtu
## (u krčmy: nejvýš svetel_max, žádné se stínem), zapnutí / vypnutí jednoho ohně (plamen, světlo); všechny ohně hoří v 6, 14, 17
## a 22 h (Míša 15. 11.: v KCD hoří pořád); pece domů mají plamen a uhlíky v ústí (v obalu pece); krby (krby.json, hrad) –
## přeskočeno, dokud model nedodán; chůze vsí: nejvýš svetel_max světel, nejbližší, bez bliknutí; u kuchyně hradu nejvýš
## svetel_max světel ohňů a nejvýš svetel_objekt_max světel celkem (Compatibility: 8 na objekt). Výpis OHNE_TEST … OK / CHYBA.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS   # hlavní nabídka pozastaví strom
	var h := get_parent()
	var oh: Node = h.get_node_or_null("Ohne")
	var chyby: Array = []
	if oh == null: _konec(["uzel Ohne chybí"], 0, 0); return
	if not bool(oh.pripraveno): await oh.hotovo
	var n: int = oh.ohne.size()
	var cfg: Dictionary = oh.cfg
	if n < 4: chyby.append("ohňů jen %d (čekám krčma 2, hájovna, kovárna + pece domů)" % n)
	# rozpočet u krčmy (kuchyně): světla zapnutá nejvýš svetel_max, nikdy stín
	var i0 := -1
	for i in n:
		if String(oh.ohne[i]["nazev"]).contains("kuchyni krčmy"): i0 = i
	if i0 < 0: chyby.append("oheň v kuchyni krčmy nenalezen"); i0 = 0
	var p0: Vector3 = oh.ohne[i0]["zaklad"]
	oh._rozpocet(p0 + Vector3(2, 1.5, 0))
	var sv: int = oh.pocet_svetel()
	if sv < 1 or sv > int(cfg["rozpocet"]["svetel_max"]): chyby.append("zapnutých světel %d" % sv)
	for o: Dictionary in oh.ohne:
		if (o["svetlo"] as OmniLight3D).shadow_enabled: chyby.append("světlo se stínem: " + String(o["nazev"]))
	var o0: Dictionary = oh.ohne[i0]
	if not bool(o0["hori"]) or not (o0["svetlo"] as OmniLight3D).visible: chyby.append("kuchyně krčmy nehoří / nesvítí")
	# uhasit
	oh.prepni(i0); oh._rozpocet(p0 + Vector3(2, 1.5, 0))
	if bool(o0["hori"]) or (o0["plamen"] as Node3D).visible or (o0["svetlo"] as OmniLight3D).visible: chyby.append("po uhašení plamen nebo světlo zůstalo")
	# zapálit
	oh.prepni(i0); oh._rozpocet(p0 + Vector3(2, 1.5, 0))
	if not bool(o0["hori"]) or not (o0["plamen"] as Node3D).visible or not (o0["svetlo"] as OmniLight3D).visible: chyby.append("po zapálení nehoří")
	# daleko (200 m): žádné světlo
	oh._rozpocet(p0 + Vector3(200, 0, 0))
	if oh.pocet_svetel() != 0: chyby.append("světla svítí i 200 m od ohňů (%d)" % oh.pocet_svetel())
	# hrad A: kuchyně v hodinách vaření (hodiny ohne.json), kamna v noci (domy_noc)
	var ik := -1; var ia := -1
	for i in n:
		var nz := String(oh.ohne[i]["nazev"])
		if nz.contains("kuchyni hradu"): ik = i
		if nz.contains("kamna"): ia = i
	if ik < 0 or ia < 0: chyby.append("hrad: kuchyně %d / kamna %d nenalezena (značky HradA_Ohen_* pod uzlem Hrad)" % [ik, ia])
	else:
		var ok_k: Dictionary = oh.ohne[ik]; var ok_a: Dictionary = oh.ohne[ia]
		for hc: Array in [[6.0, true, true], [14.0, true, true], [17.0, true, true], [22.0, true, true]]   # Míša 15. 11.: všechny ohně hoří pořád (KCD, hori vzdy)
			oh._noc(false, float(hc[0]))
			var nehori: Array = []
			for o: Dictionary in oh.ohne:
				if not bool(o["hori"]): nehori.append(String(o["nazev"]))
			print("OHNE_TEST %02d:00 kuchyně hradu hoří %s, kamna hoří %s, nehoří %d ohňů %s" % [int(hc[0]), ok_k["hori"], ok_a["hori"], nehori.size(), nehori])
			if bool(ok_k["hori"]) != bool(hc[1]): chyby.append("kuchyně hradu v %s h hoří %s (čekám %s)" % [hc[0], ok_k["hori"], hc[1]])
			if bool(ok_a["hori"]) != bool(hc[2]): chyby.append("kamna hradu v %s h hoří %s (čekám %s)" % [hc[0], ok_a["hori"], hc[2]])
			if not nehori.is_empty(): chyby.append("v %s h nehoří %s (všechny ohně hoří pořád)" % [hc[0], nehori])
		oh._noc(false, 17.0)   # kuchyně i kamna hoří: rozpočet světel u kuchyně hradu
		var pk: Vector3 = ok_k["zaklad"]; var kde := pk + Vector3(1.5, 1.5, 0)
		oh._rozpocet(kde)
		var svk: int = oh.pocet_svetel()
		var vse := 0   # všechna viditelná světla ve hře, jejichž dosah zasahuje místo u ohně (limit na objekt)
		for l in h.find_children("*", "OmniLight3D", true, false):
			if (l as OmniLight3D).is_visible_in_tree() and (l as OmniLight3D).global_position.distance_to(kde) < (l as OmniLight3D).omni_range: vse += 1
		print("OHNE_TEST hrad u kuchyně: světel ohňů %d (max %d), světel celkem v dosahu %d; kuchyně svítí %s, plamen %s" % [svk, int(cfg["rozpocet"]["svetel_max"]), vse,
			(ok_k["svetlo"] as OmniLight3D).visible, (ok_k["plamen"] as Node3D).visible])
		if svk > int(cfg["rozpocet"]["svetel_max"]) or not (ok_k["svetlo"] as OmniLight3D).visible or not (ok_k["plamen"] as Node3D).visible: chyby.append("kuchyně hradu v 17 h nesvítí / rozpočet %d" % svk)
		if vse > 8: chyby.append("u kuchyně hradu %d světel (Compatibility 8 na objekt)" % vse)
		oh._noc(true)
	_pece(oh, chyby)
	_krby(oh, chyby)
	_ves_rozpocet(oh, chyby)
	# nabídka: hráč 1,8 m od ohně v kuchyni krčmy, míří na něj → „Uhasit oheň“, stisk uhasí, znovu → „Zapálit oheň“
	var hr: CharacterBody3D = h.hrac
	var pr: Node = null
	for c in h.get_children():
		if c is CanvasLayer and c.get("zebriky") != null: pr = c
	if pr == null:
		await get_tree().create_timer(1.0).timeout
		for c in h.get_children():
			if c is CanvasLayer and c.get("zebriky") != null: pr = c
	if pr != null:
		get_tree().paused = false
		if pr.get("menu") and pr.menu.has_method("hide_menu"): pr.menu.hide_menu()
		hr.set_physics_process(false)
		var ss := get_viewport().get_world_3d().direct_space_state
		for io in ([i0, ik] if ik >= 0 else [i0]):   # krčma (kolize ohniště vlastní) a kuchyně hradu (jedna kolize celého hradu)
			var oi: Dictionary = oh.ohne[io]; var pz: Vector3 = oi["zaklad"]
			if io == ik and h.get("den"): h.den.set_hour(17.0, 0.0); oh._noc(false, 17.0)   # kuchyně hradu hoří při vaření večeře
			var cil: Vector3 = pz + Vector3.UP * 0.15
			var smer := Vector3(1.8, 0, 0)
			for k in 8:   # strana ohně, ze které je vidět (ne přes zeď)
				var a := k * TAU / 8.0; var kde := cil + Vector3(cos(a), 0, sin(a)) * 1.8
				var q := PhysicsRayQueryParameters3D.create(cil + Vector3.UP * 1.0, kde + Vector3.UP * 1.0)
				if ss.intersect_ray(q).is_empty(): smer = Vector3(cos(a), 0, sin(a)) * 1.8; break
			var stoj := Vector3(cil.x + smer.x, pz.y, cil.z + smer.z)
			var dol := ss.intersect_ray(PhysicsRayQueryParameters3D.create(stoj + Vector3.UP * 1.0, stoj - Vector3.UP * 3.0))
			if not dol.is_empty(): stoj.y = (dol["position"] as Vector3).y   # podlaha (ohniště hradu je vyvýšené)
			hr.global_position = stoj
			hr.cam.global_position = hr.global_position + Vector3.UP * 1.65
			hr.cam.look_at(cil, Vector3.UP)
			for k in 12: await get_tree().process_frame
			var t: Button = oh.tlacitko
			if t == null or not t.visible: chyby.append("nabídka ohně se neukázala (%s, hráč u ohně, míří na něj)" % oi["nazev"]); continue
			var t0 := t.text
			t.pressed.emit()
			for k in 8: await get_tree().process_frame
			if t0 != String(cfg["nabidka"]["uhasit"]) or bool(oi["hori"]) or t.text != String(cfg["nabidka"]["zapalit"]): chyby.append("nabídka %s: %s → %s, hoří %s" % [oi["nazev"], t0, t.text, oi["hori"]])
			var t1 := t.text
			t.pressed.emit()
			for k in 8: await get_tree().process_frame
			print("OHNE_TEST nabídka %s: %s → %s → %s, hoří %s" % [oi["nazev"], t0, t1, t.text, oi["hori"]])
			if not bool(oi["hori"]): chyby.append("nabídka %s: znovu zapálit nejde" % oi["nazev"])
	else: chyby.append("procházka (tlačítka) nenalezena")
	for o: Dictionary in oh.ohne:
		print("OHNE_TEST oheň %s %s hoří %s zaklad %s" % [o["nazev"], o["druh"], o["hori"], o["zaklad"]])
	_konec(chyby, n, sv)

## Pece domů s ústím (Míša 15. 11.: oheň vidět v ústí jako v chalupách KCD): uzel plamene a uhlíků existuje, hoří a je viditelný,
## leží v obalu kolize pece (rozšířeném o 0,1 m – karta je těsně před lícem otvoru); každý dům Dum1/Dum2/Rychta aspoň jednou.
func _pece(oh: Node, chyby: Array) -> void:
	var modely := {}
	for o: Dictionary in oh.ohne:
		if String(o["druh"]) != "pec" or not o.has("plamen"): continue
		var tel := o["uzel"] as Node3D
		var ab := AABB(); var prvni := true
		for cs in tel.find_children("*", "CollisionShape3D", true, false):
			var b := (cs as CollisionShape3D).global_transform * (cs as CollisionShape3D).shape.get_debug_mesh().get_aabb()
			ab = b if prvni else ab.merge(b); prvni = false
		ab = ab.grow(0.1)
		var pl := o["plamen"] as MeshInstance3D; var uh := o["uhliky"] as MeshInstance3D
		var pa := pl.global_transform * pl.get_aabb(); var ua := uh.global_transform * uh.get_aabb()
		var ok := bool(o["hori"]) and pl.is_visible_in_tree() and uh.is_visible_in_tree() and ab.encloses(pa) and ab.encloses(ua)
		var m := String(tel.name).get_slice("_Kol_", 0); modely[m] = true
		if not ok: chyby.append("pec %s (%s): plamen v ústí hoří %s viditelný %s/%s, v obalu pece %s/%s" % [m, tel.get_parent().name, o["hori"], pl.is_visible_in_tree(), uh.is_visible_in_tree(), ab.encloses(pa), ab.encloses(ua)])
	print("OHNE_TEST pece s ohněm v ústí: %s" % [modely.keys()])
	for m in ["Dum1", "Dum2", "Rychta"]:
		if not modely.has(m): chyby.append("pec %s bez ohně v ústí" % m)


## Krby (modely od modeláře – data/krby.json vlozit; hrad: značky *_Krb_Ohen*): dokud glb / značka chybí, přeskočeno (ne chyba).
func _krby(oh: Node, chyby: Array) -> void:
	var kj: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/krby.json")) if FileAccess.file_exists("res://data/krby.json") else {}
	for k: Dictionary in kj.get("vlozit", []):
		if not ResourceLoader.exists(String(k["soubor"])):
			print("OHNE_TEST krb %s: přeskočeno – model nedodán (%s)" % [k["model"], k["soubor"]]); continue
		var nal := 0
		for o: Dictionary in oh.ohne:
			if String(o["druh"]) == "krb" and String((o["uzel"] as Node).name).begins_with(String(k["model"])):
				nal += 1
				if not bool(o["hori"]) or not (o["plamen"] as Node3D).is_visible_in_tree(): chyby.append("krb %s nehoří" % k["model"])
		print("OHNE_TEST krb %s: ohňů %d" % [k["model"], nal])
		if nal == 0: chyby.append("krb %s: model vložen, ale oheň (značka %s_Krb_Ohen) nenalezen" % [k["model"], k["model"]])
	var kh := 0
	for o: Dictionary in oh.ohne:
		if String(o["druh"]) == "krb" and (o["uzel"] as Node).get_parent() and String((o["uzel"] as Node).name).begins_with("Hrad"):
			kh += 1
			if not bool(o["hori"]): chyby.append("krb hradu %s nehoří" % (o["uzel"] as Node).name)
	print("OHNE_TEST krby hradu: %s" % (("%d hoří" % kh) if kh > 0 else "přeskočeno – v modelu hradu zatím krb není (krby.json navrhy_hrad, model od modeláře)"))


## Rozpočet světel při chůzi vsí (všechny pece hoří pořád): trasa přes všechny ohně vsi po 0,5 m; v každém bodě nejvýš svetel_max
## světel, zapnuté jsou nejbližší (žádný nesvítící hořící oheň do zap_m není blíž o víc než hystereze než nějaký svítící),
## bliknutí = světlo ohně se během 3 m chůze zapne a zase vypne (nebo naopak).
func _ves_rozpocet(oh: Node, chyby: Array) -> void:
	var rz: Dictionary = oh.cfg["rozpocet"]; var mx := int(rz["svetel_max"]); var hy := float(rz.get("poradi_hystereze_m", 0.0))
	var body: Array = []
	for o: Dictionary in oh.ohne:
		if not String((o["uzel"] as Node).get_path()).contains("/Hrad/"): body.append((o["zaklad"] as Vector3) + Vector3.UP * 1.0)
	if body.size() < 2: return
	body.sort_custom(func(a: Vector3, b: Vector3) -> bool: return a.x < b.x)
	var hist := {}; var maxsv := 0; var spatne := 0; var kroku := 0; var blik := 0
	for o: Dictionary in oh.ohne: o["zap"] = false
	for i in body.size() - 1:
		var a: Vector3 = body[i]; var b: Vector3 = body[i + 1]; var n := int(ceil(a.distance_to(b) / 0.5))
		for k in n:
			var p := a.lerp(b, float(k) / float(n)); kroku += 1
			oh._rozpocet(p)
			var sv: int = oh.pocet_svetel(); maxsv = maxi(maxsv, sv)
			var dmax := -1.0; var dmin_nesviti := 1e9
			for j in oh.ohne.size():
				var o: Dictionary = oh.ohne[j]
				if not bool(o["hori"]): continue
				if bool(o["zap"]): dmax = maxf(dmax, float(o["d"]))
				elif float(o["d"]) < float(rz["zap_m"]): dmin_nesviti = minf(dmin_nesviti, float(o["d"]))
				var h: Array = hist.get(j, [])
				if h.is_empty() or bool(h[-1][0]) != bool(o["zap"]): h.append([bool(o["zap"]), kroku]); hist[j] = h
			if sv >= mx and dmin_nesviti < dmax - hy - 0.01: spatne += 1
	for j in hist:
		var h: Array = hist[j]
		for q in range(2, h.size()):
			if (int(h[q][1]) - int(h[q - 2][1])) * 0.5 < 3.0: blik += 1
	print("OHNE_TEST ves chůze: bodů %d, ohňů na trase %d, světel nejvýš %d (max %d), nejbližší nevybráno %d×, bliknutí %d" % [kroku, body.size(), maxsv, mx, spatne, blik])
	if maxsv > mx: chyby.append("ve vsi svítí %d světel ohňů (max %d)" % [maxsv, mx])
	if spatne > 0: chyby.append("ve vsi %d× nesvítí bližší oheň" % spatne)
	if blik > 0: chyby.append("ve vsi %d bliknutí světel při chůzi" % blik)


func _konec(chyby: Array, n: int, sv: int) -> void:
	print("OHNE_TEST ohňů %d, zapnutých světel u krčmy %d: %s" % [n, sv, "OK" if chyby.is_empty() else "CHYBA " + "; ".join(chyby)])
	get_tree().quit(0 if chyby.is_empty() else 1)
