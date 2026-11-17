extends Node
## Test automatiky detailu (plán 17. 11. A1, regulator.gd): PUCHART_SKRIPT=res://scripts/test_regulator.gd (headless).
## Simuluje délky snímků přímo do regulator.krok (bez čekání): 1) jednotlivé dlouhé snímky (každý 10. 300 ms) stupeň nemění,
## 2) trvale pomalé snímky (60 ms) ubírají stupně po jednom až na poslední a páky se projeví (tráva, keře, stín, LOD),
## 3) klidné snímky u limitu 30 FPS (33,3 ms) vrátí stupně po jednom až na 0 a páky na přesně původní hodnoty,
## 4) vypnutí měřením vrátí stupeň 0 a pomalé snímky pak nic nemění. Výpis REGULATOR_TEST OK / CHYBA.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	get_tree().create_timer(300.0, true, false, true).timeout.connect(func() -> void:
		print("REGULATOR_TEST CHYBA: test nedoběhl v limitu"); get_tree().quit(1))
	await get_tree().process_frame
	var h := get_parent()
	var reg: Node = h.get_node_or_null("Regulator")
	var chyby: Array = []
	if reg == null: _konec(["uzel Regulator chybí"]); return
	reg.set_process(false)   # jen simulované snímky
	reg.duvod_vypnuti = ""
	var cfg: Dictionary = reg.cfg
	var n_st: int = reg.pocet_stupnu()
	if n_st < 1: _konec(["rozpocty.json automatika bez stupňů"]); return
	# původní hodnoty pák
	var lou: Node = h.get_node_or_null("Louka")
	var tm: ShaderMaterial = (lou.vsechny_site()[0] as Mesh).surface_get_material(0) if lou else null
	var tr0: Variant = tm.get_shader_parameter("hust_do") if tm else null
	var km: ShaderMaterial = null
	var ker: Node = h.get_node_or_null("Kere")
	if ker:
		for m: Mesh in ker.vsechny_site():
			for i in m.get_surface_count():
				var mt := m.surface_get_material(i)
				if km == null and mt is ShaderMaterial and (mt as ShaderMaterial).get_shader_parameter("zanik") is Vector2: km = mt
	var kz0: Variant = km.get_shader_parameter("zanik") if km else null
	var sl := h.find_children("*", "DirectionalLight3D", true, false)
	var sun: DirectionalLight3D = sl[0] if not sl.is_empty() else null
	var st0 := sun.directional_shadow_max_distance if sun else -1.0
	var lod0 := get_viewport().mesh_lod_threshold
	if tm == null or tr0 == null: chyby.append("tráva: materiál s hust_do nenalezen")
	if km == null: chyby.append("keře: materiál se zanik nenalezen")
	if sun == null: chyby.append("slunce nenalezeno")
	# 1) jednotlivé dlouhé snímky
	var t := 0.0
	for i in int(120.0 * 30):
		reg.krok(300.0 if i % 10 == 0 else 33.3)
	if reg.stupen != 0: chyby.append("jednotlivé dlouhé snímky změnily stupeň na %d" % reg.stupen)
	# 2) trvale pomalé snímky: stupně po jednom, mezi změnami aspoň dolu_vydrz_s
	var zmeny: Array = []
	var pred: int = reg.stupen
	t = 0.0
	while t < (float(cfg["dolu_vydrz_s"]) + float(cfg["okno_s"]) + 5.0) * (n_st + 1):
		reg.krok(60.0); t += 0.06
		if reg.stupen != pred:
			if reg.stupen != pred + 1: chyby.append("dolů skok %d → %d" % [pred, reg.stupen])
			zmeny.append(t); pred = reg.stupen
	if reg.stupen != n_st: chyby.append("pomalé snímky: stupeň %d, čekám %d" % [reg.stupen, n_st])
	for k in range(1, zmeny.size()):
		if zmeny[k] - zmeny[k - 1] < float(cfg["dolu_vydrz_s"]): chyby.append("dolů příliš rychle (%.1f s)" % (zmeny[k] - zmeny[k - 1]))
	var dolu_s: Array = zmeny.map(func(x: float) -> String: return "%.0f" % x)
	print("REGULATOR_TEST dolů: stupně %s v čase %s s, panel: %s" % [reg.stupen, dolu_s, reg.panel()])
	# páky na posledním stupni (kumulativně z dat)
	var pak := {}
	for s: Dictionary in cfg["stupne"]:
		for k: String in s:
			if not (k in ["jmeno", "popis", "zdroj"] or k.begins_with("_")): pak[k] = float(s[k])
	if tm and tr0 != null and pak.has("trava_dosah") and not is_equal_approx(float(tm.get_shader_parameter("hust_do")), float(tr0) * pak["trava_dosah"]):
		chyby.append("tráva hust_do %s (původně %s)" % [tm.get_shader_parameter("hust_do"), tr0])
	if km and kz0 != null and pak.has("kere_dosah") and not (km.get_shader_parameter("zanik") as Vector2).is_equal_approx((kz0 as Vector2) * pak["kere_dosah"]):
		chyby.append("keře zanik %s (původně %s)" % [km.get_shader_parameter("zanik"), kz0])
	if sun and pak.has("stiny_dosah_m") and not is_equal_approx(sun.directional_shadow_max_distance, minf(pak["stiny_dosah_m"], st0)):
		chyby.append("stín %.1f m (původně %.1f)" % [sun.directional_shadow_max_distance, st0])
	if pak.has("lod_prah_nasobek") and not is_equal_approx(get_viewport().mesh_lod_threshold, lod0 * pak["lod_prah_nasobek"]):
		chyby.append("LOD práh %.2f (původně %.2f)" % [get_viewport().mesh_lod_threshold, lod0])
	if get_viewport().scaling_3d_scale <= 0.0: chyby.append("rozlišení 3D změněno")
	var sc0 := get_viewport().scaling_3d_scale
	# 3) klid u limitu 30 FPS: zpět po jednom, mezi změnami aspoň nahoru_vydrz_s
	zmeny = []; t = 0.0
	while t < (float(cfg["nahoru_vydrz_s"]) + float(cfg["okno_s"]) + 5.0) * (n_st + 1):
		reg.krok(33.3); t += 0.0333
		if reg.stupen != pred:
			if reg.stupen != pred - 1: chyby.append("nahoru skok %d → %d" % [pred, reg.stupen])
			zmeny.append(t); pred = reg.stupen
	if reg.stupen != 0: chyby.append("klidné snímky: stupeň %d, čekám 0" % reg.stupen)
	if zmeny.size() > 0 and zmeny[0] < float(cfg["nahoru_vydrz_s"]): chyby.append("první návrat po %.1f s < nahoru_vydrz_s" % zmeny[0])
	var nahoru_s: Array = zmeny.map(func(x: float) -> String: return "%.0f" % x)
	print("REGULATOR_TEST nahoru: v čase %s s" % [nahoru_s])
	if tm and tr0 != null and float(tm.get_shader_parameter("hust_do")) != float(tr0): chyby.append("tráva nevrácena")
	if km and kz0 != null and km.get_shader_parameter("zanik") != kz0: chyby.append("keře nevráceny")
	if sun and sun.directional_shadow_max_distance != st0: chyby.append("stín nevrácen")
	if get_viewport().mesh_lod_threshold != lod0: chyby.append("LOD nevrácen")
	if get_viewport().scaling_3d_scale != sc0: chyby.append("rozlišení 3D změněno")
	# 4) měření: vypnuto na stupni 0, pomalé snímky nic nemění
	for i in 2000: reg.krok(60.0)
	var pred_mer: int = reg.stupen
	reg.vypni("měření")
	if reg.stupen != 0: chyby.append("vypnutí neobnovilo stupeň 0")
	for i in 3000: reg.krok(80.0)
	if reg.stupen != 0: chyby.append("během měření zásah (stupeň %d)" % reg.stupen)
	reg.zapni()
	print("REGULATOR_TEST měření: před vypnutím stupeň %d, po %d; panel: %s" % [pred_mer, reg.stupen, reg.panel()])
	_konec(chyby)

func _konec(chyby: Array) -> void:
	print("REGULATOR_TEST %s" % ("OK" if chyby.is_empty() else "CHYBA: " + "; ".join(chyby)))
	get_tree().quit(0 if chyby.is_empty() else 1)
