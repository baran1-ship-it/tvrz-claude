extends Node
## Test ohňů (Míša 15. 11., chyby.md 274): PUCHART_SKRIPT=res://scripts/test_ohne.gd – počet ohňů z dat, světla v rozpočtu
## (u krčmy: nejvýš svetel_max, žádné se stínem), zapnutí / vypnutí jednoho ohně (plamen, světlo). Výpis OHNE_TEST … OK / CHYBA.
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
		if String(oh.ohne[i]["nazev"]).contains("kuchyni"): i0 = i
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
	for o: Dictionary in oh.ohne:
		print("OHNE_TEST oheň %s %s hoří %s zaklad %s" % [o["nazev"], o["druh"], o["hori"], o["zaklad"]])
	_konec(chyby, n, sv)

func _konec(chyby: Array, n: int, sv: int) -> void:
	print("OHNE_TEST ohňů %d, zapnutých světel u krčmy %d: %s" % [n, sv, "OK" if chyby.is_empty() else "CHYBA " + "; ".join(chyby)])
	get_tree().quit(0 if chyby.is_empty() else 1)
