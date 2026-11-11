extends Node
## Ctvrta sada (Misa 11. 11., trasa 0.99997): izolovany test kroku automaticke kvality ve svete.
## Na tabletu po krocich stiny_kratsi / stiny_predmetu / efekty snimek 2,7-3,5 s v neměřeném _process (0.99996: 37-332 ms).
##   kroky_kvality  ve svete (tvrz) zapne a zase vypne kazdy krok kvality.json zvlast a zmeri nejdelsi snimek a nejdelsi
##                  _process (Performance.TIME_PROCESS) v nasledujicich snimcich. Headless = bez kresleni: co se ukaze
##                  tady, jsou skripty; co ne, je ovladac / kresleni. Mez pasma.test.krok_kvality_max_ms.
## Spusteni: tools/beh.sh kroky testy "kroky_kvality"

var main: Node
var vysledky: Array = []
const TESTY := ["kroky_kvality"]


func run(p_main: Node) -> void:
	main = p_main
	var jen := OS.get_environment("TVRZ_TEST_JEN").split(",", false)
	var nic := true
	for t: String in TESTY:
		if jen.has(t):
			nic = false
			await call("_" + t)
	if nic:
		return
	var ok := true
	print("TEST VYKON ------------------------------")
	for v: Array in vysledky:
		print("TEST %-14s %s  %s" % [v[0], "OK   " if v[1] else "CHYBA", v[2]])
		ok = ok and bool(v[1])
	print("TEST VYKON %s" % ("PROSEL" if ok else "NEPROSEL"))


func _snimky(n: int) -> Array:
	var nej := 0.0
	var nej_p := 0.0
	var t0 := Time.get_ticks_usec()
	for i in n:
		await get_tree().process_frame
		var t := Time.get_ticks_usec()
		nej = maxf(nej, (t - t0) / 1000.0)
		nej_p = maxf(nej_p, Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
		t0 = t
	return [nej, nej_p]


func _kroky_kvality() -> void:
	var kv: Node = main.kvalita
	if kv == null:
		vysledky.append(["kroky_kvality", false, "main.kvalita chybi"])
		return
	var mez := float(main.svet.pasma()["test"]["krok_kvality_max_ms"])
	kv.nastav(false)
	await _snimky(60)                              # dobehnout nacitani okoli
	var zakl: Array = await _snimky(30)
	print("KROK zaklad: nejdelsi snimek %.0f ms, _process %.0f ms" % [zakl[0], zakl[1]])
	var ok := true
	var txt: Array = []
	for k: Dictionary in kv.cfg["kroky"]:
		if not bool(k.get("povoleno", true)):
			continue
		var id := String(k["id"])
		for zap in [true, false]:
			if zap:
				kv.akt.append(id)
			else:
				kv.akt.erase(id)
			var t0 := Time.get_ticks_usec()
			kv._uplatni()
			var upl := (Time.get_ticks_usec() - t0) / 1000.0
			var po: Array = await _snimky(8)
			var r := "%s %s: uplatneni %.0f ms, nejdelsi snimek %.0f ms, _process %.0f ms" % ["+" if zap else "-", id, upl, po[0], po[1]]
			print("KROK " + r)
			txt.append("%s%s %.0f/%.0f" % ["+" if zap else "-", id, upl, po[0]])
			if upl + po[0] > mez:
				ok = false
	vysledky.append(["kroky_kvality", ok, "mez %.0f ms; %s" % [mez, ", ".join(txt)]])
