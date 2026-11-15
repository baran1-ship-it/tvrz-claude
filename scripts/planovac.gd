extends RefCounted
## PLANOVAC SNIMKU (docs/rozpracovane/zaseky_rozbor_system.md §3 bod 1, tester 13.-15. 11. „FPS 5 ve vsi", zaseky):
## jeden rozpocet snimku pro vsechno streamovani - kolize (svet._kol_krok), rostliny (svet.rostliny_okoli), louka
## (bunky trsu i kupy, louka._krok / _kupy_nahrej) a mazani jejich uzlu. Drive tri fronty kazda se svym rozpoctem
## (planovac 2-3 ms, louka 4 ms, kupy bez rozpoctu) -> v jednom snimku se mohly sejit davka kolizi, bunka rostlin,
## odkryti bunky louky, nahrani kup a hromadne queue_free.
## Tri meze snimku (pravidla/svet/rozpocty.json „snimek"; tezkych_uloh_za_snimek z „planovac"):
##  - cas (us) vsech konzumentu dohromady,
##  - bajty nahrane do GPU (model ovladace GLES3, louka._model_b; rostliny nejvys podil rozpoctu - louka ma vzdy zbytek),
##  - tezke ulohy (davka kolizi, odkryti bunky rostlin, dokonceni bunky louky, dil kup) - nejvys N za snimek a stridave
##    mezi tridami (trida, ktera mela tezkou ulohu minule, ustoupi, kdyz minule cekala jina).
## Mazani: uzly streamovani se hned skryji (visible = false) a uvolni nejvys ruseni_za_snimek uzlu za snimek (queue_free
## se provede v „pred kreslenim" - drive desitky MultiMeshu bunky naraz).
## Snimek se pozna podle Engine.get_process_frames(); druhe volani tehoz konzumenta v tomtez snimku (testy volaji
## louka._process v cyklu) zacne novy snimek planovace.
## Bez uzlu a bez class_name: staticke promenne, kazdy konzument si skript preloadne.

const Pravidla := preload("res://scripts/pravidla.gd")

static var _sn := -1
static var _zacali := {}
static var cas_us := 0                   # cas streamovani v tomto snimku (us)
static var bajty := 0                    # bajty nahrane do GPU v tomto snimku (vsichni konzumenti)
static var bajty_rost := 0               # z toho rostliny
static var tezkych := 0
static var tezke_tridy: PackedStringArray = []
static var ruseno := 0
static var _posledni_tezka := ""
static var _chteli := {}                 # tridy, kterym byla tezka uloha v tomto snimku odeprena
static var _chteli_minule := {}
static var _rusit: Array = []            # uzly k uvolneni (skryte)
static var _r := {}
static var _mob := -1
# uzavreny predchozi snimek planovace (test planovac_snimek, diag)
static var posledni := {"cas_us": 0, "bajty": 0, "tezkych": 0, "ruseno": 0, "tridy": ""}
static var snimku := 0


static func _p() -> Dictionary:
	if _r.is_empty():
		_r = Pravidla.cti("rozpocty", "snimek")
		_r["_tezkych"] = int(Pravidla.cti("rozpocty", "planovac", "tezkych_uloh_za_snimek"))
		_r["_nahrani_b"] = int(Pravidla.cti("rozpocty", "louka_nahravani", "nahrani_b_snimek"))
		var xf := int(Pravidla.cti("rozpocty", "louka_nahravani", "gles3_floatu_transform"))
		var cu := int(Pravidla.cti("rozpocty", "louka_nahravani", "gles3_floatu_barva_custom"))
		_r["_inst_b"] = xf * 4
		_r["_inst_b_cust"] = (xf + cu) * 4
	return _r


static func mobil() -> bool:
	if _mob < 0:
		_mob = 1 if OS.has_feature("mobile") or OS.has_environment("TVRZ_MOBIL") else 0
	return _mob == 1


## Konzument (jmeno) zacina praci v tomto snimku. Novy snimek enginu nebo opakovane volani tehoz konzumenta = novy
## snimek planovace (predchozi se uzavre do `posledni`).
static func zacni(kdo: String) -> void:
	var f := Engine.get_process_frames()
	if f != _sn or _zacali.has(kdo):
		_uzavri()
		_sn = f
		_zacali = {}
	_zacali[kdo] = true


static func _uzavri() -> void:
	if _sn >= 0:
		posledni = {"cas_us": cas_us, "bajty": bajty, "bajty_rost": bajty_rost, "tezkych": tezkych, "ruseno": ruseno,
				"tridy": ",".join(tezke_tridy)}
		snimku += 1
	cas_us = 0
	bajty = 0
	bajty_rost = 0
	tezkych = 0
	tezke_tridy = PackedStringArray()
	ruseno = 0
	_chteli_minule = _chteli
	_chteli = {}


## Celkovy casovy rozpocet streamovani na snimek (us).
static func rozpocet_us() -> int:
	return int(_p()["rozpocet_us_tablet" if mobil() else "rozpocet_us_pc"])


static func zbyva_us() -> int:
	return rozpocet_us() - cas_us


static func spotrebuj_us(us: int) -> void:
	cas_us += maxi(us, 0)


static func rozpocet_b() -> int:
	return int(_p()["_nahrani_b"])


## Bajty nahrani instanci do GPU (glBufferData celeho bufferu, model ovladace GLES3: transformace 3D + barva/custom
## v jednom uvec4 pri use_colors nebo use_custom_data).
static func b_instanci(n: int, barvy_custom: bool) -> int:
	return n * int(_p()["_inst_b_cust" if barvy_custom else "_inst_b"])


## Vejde se nahrani b bajtu? Prvni nahrani snimku projde vzdy (postup zaruceny); rostliny jen do sveho podilu.
static func vejde_b(b: int, rostliny := false) -> bool:
	if rostliny and bajty_rost + b > int(rozpocet_b() * float(_p()["rostliny_podil_b"])) and bajty_rost > 0:
		return false
	return bajty == 0 or bajty + b <= rozpocet_b()


static func nahraj_b(b: int, rostliny := false) -> void:
	bajty += maxi(b, 0)
	if rostliny:
		bajty_rost += maxi(b, 0)
	var dg: Object = Engine.get_meta("diag", null)
	if dg and b > 0:
		dg.udalost("plan_B", b)


## Smi trida (kolize / rostliny / louka / kupy) v tomto snimku tezkou ulohu? Nejvys tezkych_uloh_za_snimek; trida,
## ktera mela posledni tezkou ulohu, ustoupi, kdyz v minulem snimku cekala jina trida (stridani, zadna nehladovi).
## Pri true je uloha rovnou zapocitana.
static func tezka(trida: String) -> bool:
	var lim := int(_p()["_tezkych"])
	var ustoupit := trida == _posledni_tezka and not _chteli_minule.is_empty() and not (_chteli_minule.size() == 1 and _chteli_minule.has(trida))
	if tezkych >= lim or ustoupit:
		_chteli[trida] = true
		return false
	tezkych += 1
	tezke_tridy.append(trida)
	_posledni_tezka = trida
	var dg: Object = Engine.get_meta("diag", null)
	if dg:
		dg.udalost("plan_" + trida, 1)
	return true


## Uzel streamovani pryc: hned skryt, uvolnit az v krok_ruseni (nejvys ruseni_za_snimek za snimek).
static func zrus(n: Node) -> void:
	if n == null or not is_instance_valid(n):
		return
	if n is Node3D:
		(n as Node3D).visible = false
	n.set_meta("plan_rusit", true)          # rozestavene veci (dily kup) uz do nej nestavet
	_rusit.append(n)


static func krok_ruseni() -> void:
	var lim := int(_p()["ruseni_za_snimek"])
	while ruseno < lim and not _rusit.is_empty():
		var n: Node = _rusit.pop_back()
		if is_instance_valid(n) and not n.is_queued_for_deletion():
			n.queue_free()
			ruseno += 1
			var dg: Object = Engine.get_meta("diag", null)
			if dg:
				dg.udalost("plan_ruseno", 1)


static func ceka_ruseni() -> int:
	return _rusit.size()


## Testy a rychle cestovani: vse ve fronte mazani hned uvolnit.
static func rus_vse() -> void:
	for n: Node in _rusit:
		if is_instance_valid(n) and not n.is_queued_for_deletion():
			n.queue_free()
	_rusit.clear()


static func text() -> String:
	return "snímek %.1f/%.1f ms, GPU %.0f/%.0f kB, těžké %d (%s), mazání %d (fronta %d)" % [posledni["cas_us"] / 1000.0,
			rozpocet_us() / 1000.0, posledni["bajty"] / 1024.0, rozpocet_b() / 1024.0, int(posledni["tezkych"]),
			String(posledni["tridy"]), int(posledni["ruseno"]), _rusit.size()]
