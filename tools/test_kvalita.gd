extends SceneTree
## Lehky test automaticke kvality (headless, bez sveta, ~2 s): scripts/kvalita.gd se simulovanymi delkami snimku podle
## pravidla/svet/kvalita.json - snizeni pri trvalem trendu nad rezervou (ne pri jednom skubnuti), jemne kroky pred
## nouzovymi, vyber podle GPU/CPU, odklad pri otaceni kamery, zvyseni po klidu, hystereze (zdvojnasobeni cekani),
## teplo predem, tisen pameti; a ze Nastaveni ma volbu „Kvalita“ (menu.gd + main.gd text).
## Spusteni: tools/beh.sh kvalita cmd godot --headless --path . -s res://tools/test_kvalita.gd
## Vystup: radky TEST KVALITA ... OK/CHYBA, souhrn TEST KVALITA: n chyb.

var chyb := 0
var k: Node
var cfg: Dictionary


func _init() -> void:
	k = load("res://scripts/kvalita.gd").new()
	cfg = k.cfg
	var r := float(cfg["rozpocet_ms"])
	var dobre := r * float(cfg["nahoru_p95_podil"]) * 0.8      # pod klidem
	var spatne := r * float(cfg["dolu_p95_podil"]) * 1.1       # nad rezervou (ale pod 33 ms - neceka na pad pod 30 FPS)
	k.zapnuto = true
	# 1. klid: nic se nemeni
	_hraj(dobre, 20.0, true)
	_over("klid nemeni", k.stupen == 0, "stupen %d" % k.stupen)
	# 2. jedno skubnuti (1 okno spatne) nesnizi
	_hraj(spatne, float(cfg["okno_s"]) * 1.05, true)
	_hraj(dobre, 3.0, true)
	_over("jedno skubnuti nesnizi", k.stupen == 0, "stupen %d" % k.stupen)
	# 3. trvaly trend nad rezervou (p95 %.0f < 33 ms) snizi; prvni krok = prvni jemny setrici GPU
	var prvni := _prvni_jemny("gpu")
	var t := _hraj_do(spatne, func() -> bool: return k.stupen >= 1, 60.0, true)
	_over("trend nad rezervou snizi", k.stupen == 1 and k.akt[0] == prvni,
			"za %.1f s (cekano dolu_oken x okno = %.1f s), krok %s (cekan %s), p95 %.1f" % [t, float(cfg["dolu_oken"]) * float(cfg["okno_s"]), str(k.akt), prvni, k.p95])
	# 4. otaceni kamery: snizeni se odlozi, nejdele odklad_dolu_s
	var z: int = k.stupen
	var omez: int = k.max_fps()
	var hodne := (1000.0 / omez * float(cfg["omezeno_dolu_x"]) * 1.2) if omez > 0 else spatne * 1.2
	t = _hraj_do(hodne, func() -> bool: return k._chce > 0, 60.0, false)
	var t2 := _hraj_do(hodne, func() -> bool: return k.stupen > z, 30.0, false)
	_over("pri otaceni odlozeno nejvys odklad_dolu_s", k.stupen == z + 1 and t2 >= float(cfg["odklad_dolu_s"]) - 0.1 and t2 <= float(cfg["odklad_dolu_s"]) + 0.2,
			"pozadavek za %.1f s, provedeno po %.1f s (odklad %.1f)" % [t, t2, float(cfg["odklad_dolu_s"])])
	# 5. CPU: hra stoji na procesoru -> dalsi krok setri cpu (nebo prvni volny jemny, kdyz zadny cpu)
	var cpu_cekany := _prvni_jemny("cpu")
	z = k.stupen
	_hraj_do(hodne, func() -> bool: return k.stupen > z, 60.0, true, 0.9)
	_over("CPU uzke hrdlo vybere cpu krok", k.uzke == "cpu" and k.akt[-1] == cpu_cekany, "uzke %s, krok %s (cekan %s)" % [k.uzke, k.akt[-1], cpu_cekany])
	# 6. jemne vsechny, nouzove az po nouzova_s trvaleho nedostatku
	_hraj_do(hodne, func() -> bool: return k._jemne_vycerpane(), 600.0, true)
	var n_jemne: int = k.stupen
	var t_n := _hraj_do(hodne, func() -> bool: return k.stupen > n_jemne, 600.0, true)
	var nouzove := false
	for kk: Dictionary in k.kroky:
		if String(kk.get("uroven", "")) == "nouzova":
			nouzove = true
	_over("nouzova az po vycerpani jemne a nouzova_s", not nouzove or (t_n >= float(cfg["nouzova_s"]) and String(k._vsechny[k.akt[-1]]["uroven"]) == "nouzova"),
			"jemnych %d, nouzovy %s po %.0f s (nouzova_s %.0f)" % [n_jemne, k.akt[-1], t_n, float(cfg["nouzova_s"])])
	# 7. klid -> zvyseni po nahoru_s (pri omezeni snimku drzi 1000/f ms)
	var ns: float = k._nahoru_s
	z = k.stupen
	t = _hraj_do(_klidne(), func() -> bool: return k.stupen < z, 600.0, true)
	_over("klid zvysi po nahoru_s", k.stupen == z - 1 and t >= ns - 0.1, "za %.1f s (nahoru_s %.0f)" % [t, ns])
	# 8. hystereze: spadne hned po zvyseni -> cekani na dalsi zvyseni dvojnasobne
	ns = k._nahoru_s
	z = k.stupen
	_hraj_do(hodne * 1.3, func() -> bool: return k.stupen > z, 60.0, true)
	_over("hystereze zdvojnasobi cekani", absf(k._nahoru_s - minf(ns * 2.0, float(cfg["nahoru_s_max"]))) < 0.01, "nahoru_s %.0f -> %.0f" % [ns, k._nahoru_s])
	# 9. teplo: nad prah_dolu snizi i pri dobrych snimcich; nad prah_blok_nahoru nezvysi
	k.nastav(false)
	k.nastav(true)
	k.teplo_hodnota(float(cfg["teplo"]["prah_dolu"]) + 0.01, 10.0)
	_hraj(dobre, 0.5, true)
	_over("teplo snizi predem", k.stupen == 1, "stupen %d, teplo %.2f" % [k.stupen, k.teplo])
	k.teplo_hodnota(float(cfg["teplo"]["prah_blok_nahoru"]) + 0.01, 10.0)
	_hraj(_klidne(), float(cfg["nahoru_s"]) * 2.0, true)
	_over("teplo blokuje zvyseni", k.stupen == 1, "stupen %d" % k.stupen)
	k.teplo_hodnota(0.3, 10.0)
	_hraj(_klidne(), float(cfg["nahoru_s"]) + 10.0, true)
	_over("po vychladnuti zvysi", k.stupen == 0, "stupen %d, klid %.1f s, chce %d, nahoru_s %.0f, teplo %.2f, p95 %.1f, max_fps %d, akt %s" % [k.stupen, k._klid_t, k._chce, k._nahoru_s, k.teplo, k.p95, k.max_fps(), str(k.akt)])
	# 10. trend ohrevu: headroom roste rychle nad trend_od -> snizi predem
	k.teplo_hodnota(float(cfg["teplo"]["trend_od"]) - 0.1, 10.0)
	k._teplo_dolu_t = 1000.0
	k.teplo_hodnota(float(cfg["teplo"]["trend_od"]) + 0.02, 10.0)
	_hraj(dobre, 0.5, true)
	_over("rychly ohrev snizi predem", k.stupen == 1, "stupen %d (trend %.2f/min)" % [k.stupen, 0.12 / 10.0 * 60.0])
	k.teplo_hodnota(0.3, 10.0)
	k.teplo = -1.0
	# 11. tisen pameti s hysterezi
	var p: Dictionary = cfg["pamet"]
	k.pamet(int(p["ram_volna_min_mb"]) - 50, 500.0)
	var pk: bool = k.tisen_pameti
	k.pamet(int(p["ram_volna_min_mb"]) + 50, 500.0)        # mezi min a ok: drzi
	var drzi: bool = k.tisen_pameti
	k.pamet(int(p["ram_volna_ok_mb"]) + 50, 500.0)
	_over("tisen pameti s hysterezi", pk and drzi and not k.tisen_pameti, "zapnuto %s, mezi prahy %s, po uvolneni %s" % [pk, drzi, k.tisen_pameti])
	# 12. vypnuti vrati rucni kvalitu
	k.nastav(false)
	_over("vypnuti vrati plnou kvalitu", k.stupen == 0 and k.max_fps() == 0, "stupen %d" % k.stupen)
	# 13. Nastaveni: volba v menu a text v main
	var menu_src := FileAccess.get_file_as_string("res://scripts/menu.gd")
	var main_src := FileAccess.get_file_as_string("res://scripts/main.gd")
	_over("volba Kvalita v Nastaveni", menu_src.contains("\"kvalita_auto\"") and main_src.contains("\"set:kvalita_auto\":") and main_src.contains("\"kvalita_auto\": ("),
			"menu.gd klic, main.gd akce a text")
	k.free()
	print("TEST KVALITA: %d chyb" % chyb)
	quit(1 if chyb > 0 else 0)


## Snimky klidu: bez omezeni pod klidem, s omezenim presne 1000/f ms (hra drzi limit).
func _klidne() -> float:
	var f: int = k.max_fps()
	return 1000.0 / f if f > 0 else float(cfg["rozpocet_ms"]) * float(cfg["nahoru_p95_podil"]) * 0.8


func _prvni_jemny(co: String) -> String:
	for kk: Dictionary in k.kroky:
		if String(kk.get("uroven", "jemna")) != "nouzova" and not k.akt.has(String(kk["id"])) and (kk.get("setri", ["gpu"]) as Array).has(co):
			return String(kk["id"])
	for kk: Dictionary in k.kroky:
		if String(kk.get("uroven", "jemna")) != "nouzova" and not k.akt.has(String(kk["id"])):
			return String(kk["id"])
	return ""


func _hraj(ms: float, s: float, klid: bool, cpu_podil := 0.1) -> void:
	var t := 0.0
	while t < s:
		var m := _ms(ms)
		k.snimek(m, m / 1000.0, klid, m * cpu_podil)
		t += m / 1000.0


## Snimky, dokud neplati podminka (vraci cas v s), nejvys limit s.
func _hraj_do(ms: float, podm: Callable, limit: float, klid: bool, cpu_podil := 0.1) -> float:
	var t := 0.0
	while t < limit and not podm.call():
		var m := _ms(ms)
		k.snimek(m, m / 1000.0, klid, m * cpu_podil)
		t += m / 1000.0
	return t


## Omezeni snimku (krok max_fps): snimek nemuze byt kratsi nez 1000/f ms.
func _ms(ms: float) -> float:
	var f: int = k.max_fps()
	return maxf(ms, 1000.0 / f) if f > 0 else ms


func _over(jm: String, ok: bool, det: String) -> void:
	print("TEST KVALITA %-45s %s  (%s)" % [jm, "OK" if ok else "CHYBA", det])
	if not ok:
		chyb += 1
