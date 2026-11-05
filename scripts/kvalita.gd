extends Node
const Pravidla := preload("res://scripts/pravidla.gd")
## Automaticka kvalita (Misa 5. 11.: „pri nestihani zhorseni grafiky, aby hra jela plynule?“) - jako dynamicke rozliseni
## Unrealu / Unity Adaptive Performance / ADPF: meri delky snimku a pri trvalem trendu nad rezervou rozpoctu zapne dalsi
## krok kvality (jemne pred nouzovymi, podle toho, zda hra stoji na GPU, nebo CPU), po delsim klidu naposledy zapnuty
## vrati (hystereze). Vse - prahy, okna, kroky, poradi - v pravidla/svet/kvalita.json (popis tam), reserse
## docs/rozpracovane/kvalita_auto.md. Bez main (test tools/test_kvalita.gd) se jen pocita, nic se neprepina.

signal zmena(stupen: int, duvod: String)

var main: Node
var zapnuto := false
var tisen_pameti := false
var teplo := -1.0                      # Android thermal headroom (0 = bez skrceni, 1 = SEVERE), -1 = nezname
var historie: Array[String] = []        # posledni zmeny (panel, merici trasa)
var zmen := 0
var uzke := "gpu"                       # na cem hra stoji v poslednim okne (gpu / cpu)
var p95 := 0.0
var prumer := 0.0

var cfg: Dictionary
var kroky: Array = []                  # povolene kroky v poradi dat
var _vsechny: Dictionary = {}          # id -> krok (i nepovolene - tisen pameti)
var akt: Array[String] = []             # zapnute kroky v poradi zapnuti (zvyseni vraci posledni)
var _okno := PackedFloat32Array()
var _okno_cpu := 0.0
var _okno_t := 0.0
var _zle := 0
var _klid_t := 0.0
var _nouze_t := 0.0
var _nahoru_s := 30.0
var _od_zmeny := 1000.0
var _od_zvyseni := -1.0                 # cas od posledniho zvyseni (-1 = zadne v hlidani)
var _teplo_dolu_t := 1000.0
var _chce := 0                          # cekajici zmena: +1 nizsi kvalita, -1 vyssi
var _chce_duvod := ""
var _chce_t := 0.0
var _rot := 0.0                         # otaceni kamery (st/s, vyhlazene)
var _fwd0 := Vector3.ZERO
var _posl := 0
var _pamet_t := 0.0
var _teplo_t := 0.0
var _teplo0 := -1.0
var _pm: Variant = null                 # android.os.PowerManager (JavaObject)
var _teplo_ok := true
# zaklad z rucniho nastaveni (main.apply_quality) a co je ted uplatneno
var _zakl_meritko := -1.0
var _zakl_stin := -1.0
var _zakl_zare := true
var _upl: Dictionary = {}


func _init() -> void:
	cfg = {}
	for k: String in ["vychozi", "rozpocet_ms", "dolu_p95_podil", "dolu_prumer_podil", "nahoru_p95_podil", "cpu_podil",
			"nouzova_s", "okno_s", "percentil", "min_snimku", "dolu_oken", "nahoru_s", "nahoru_s_max", "navrat_s",
			"po_zmene_s", "ignoruj_ms", "omezeno_dolu_x", "omezeno_klid_x", "kamera_klid_st_s", "odklad_dolu_s",
			"odklad_nahoru_s", "teplo", "pamet", "kroky"]:
		cfg[k] = Pravidla.cti("kvalita", k)
	for k: Dictionary in cfg["kroky"]:
		_vsechny[String(k["id"])] = k
		if bool(k.get("povoleno", true)):
			kroky.append(k)
	_nahoru_s = float(cfg["nahoru_s"])


## Vychozi volba podle zarizeni (kvalita.json vychozi), kdyz hrac nic neulozil.
func vychozi() -> bool:
	var mob := OS.has_feature("mobile") or OS.has_environment("TVRZ_MOBIL")
	return bool(cfg["vychozi"]["tablet" if mob else "pc"])


## Zapnout / vypnout automatiku; vypnuti vrati vse na rucni nastaveni.
func nastav(on: bool) -> void:
	zapnuto = on
	_reset_okna()
	_chce = 0
	_klid_t = 0.0
	_nouze_t = 0.0
	_zle = 0
	_od_zvyseni = -1.0
	_nahoru_s = float(cfg["nahoru_s"])
	if not on and (not akt.is_empty() or tisen_pameti):
		akt.clear()
		tisen_pameti = false
		_zaznam("vypnuto (rucni kvalita)")
		_uplatni()


var stupen: int:
	get:
		return akt.size()


func max_stupen() -> int:
	return kroky.size()


## Omezeni snimku v zapnutych krocich (0 = neomezeno).
func max_fps() -> int:
	var f := 0
	for k: Dictionary in _aktivni():
		if String(k["druh"]) == "max_fps":
			f = int(k["hodnota"]) if f == 0 else mini(f, int(k["hodnota"]))
	return f


func _aktivni() -> Array:
	var a: Array = []
	for id: String in akt:
		a.append(_vsechny[id])
	if tisen_pameti:
		for id: String in cfg["pamet"]["kroky"]:
			if _vsechny.has(id) and not akt.has(id):
				a.append(_vsechny[id])
	return a


func popis_stupne() -> String:
	return "plna" if akt.is_empty() else ", ".join(akt)


func panel_text() -> String:
	if not zapnuto:
		return ""
	return " · kvalita -%d %s%s%s" % [akt.size(), uzke, " pamet" if tisen_pameti else "",
			(" teplo %.2f" % teplo) if teplo >= 0.0 else ""]


## Dalsi krok ke zapnuti: jemne pred nouzovymi; mezi jemnymi prvni, ktery setri to, na cem hra stoji (jinak prvni
## volny jemny); nouzovy az po nouzova_s trvaleho nedostatku se vsemi jemnymi zapnutymi. "" = neni co ubrat.
func dalsi_krok() -> String:
	var volne_jemne: Array = []
	var volne_nouzove: Array = []
	for k: Dictionary in kroky:
		if akt.has(String(k["id"])):
			continue
		if String(k.get("uroven", "jemna")) == "nouzova":
			volne_nouzove.append(k)
		else:
			volne_jemne.append(k)
	for k: Dictionary in volne_jemne:
		if (k.get("setri", ["gpu"]) as Array).has(uzke):
			return String(k["id"])
	if not volne_jemne.is_empty():
		return String(volne_jemne[0]["id"])
	if not volne_nouzove.is_empty() and _nouze_t >= float(cfg["nouzova_s"]):
		for k: Dictionary in volne_nouzove:
			if (k.get("setri", ["gpu"]) as Array).has(uzke):
				return String(k["id"])
		return String(volne_nouzove[0]["id"])
	return ""


# ------------------------------------------------------------------ smycka

func _process(dt: float) -> void:
	if not zapnuto or main == null or not bool(main.get("ready_done")):
		_posl = 0
		return
	var now := Time.get_ticks_usec()
	var ms := (now - _posl) / 1000.0 if _posl > 0 else 0.0
	_posl = now
	var cam := get_viewport().get_camera_3d()
	if cam:
		var fw := -cam.global_basis.z
		if _fwd0 != Vector3.ZERO and dt > 0.0:
			_rot = lerpf(_rot, rad_to_deg(_fwd0.angle_to(fw)) / dt, minf(1.0, dt * 5.0))
		_fwd0 = fw
	_pamet_krok(dt)
	_teplo_krok(dt)
	if ms > 0.0:
		# procesor: skripty (diag, soucet _process systemu za minuly snimek) + fyzika; zbytek snimku = kresleni a cekani na GPU
		var cpu := Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
		if main.diag and main.diag.has_method("_skripty_us"):
			cpu += main.diag._skripty_us() / 1000.0
		snimek(ms, dt, _rot < float(cfg["kamera_klid_st_s"]), cpu)


## Jeden snimek: ms = skutecna delka, dt = cas hry, klid = kamera se neotaci, cpu_ms = skripty + fyzika.
## Volano z _process i z testu.
func snimek(ms: float, dt: float, klid: bool, cpu_ms := 0.0) -> void:
	_od_zmeny += dt
	_teplo_dolu_t += dt
	if _od_zvyseni >= 0.0:
		_od_zvyseni += dt
		if _od_zvyseni > float(cfg["navrat_s"]):
			_od_zvyseni = -1.0              # zvyseni vydrzelo: cekani na dalsi zvyseni zase kratsi
			_nahoru_s = maxf(float(cfg["nahoru_s"]), _nahoru_s * 0.5)
	if ms < float(cfg["ignoruj_ms"]):
		_okno.append(ms)
		_okno_cpu += cpu_ms
	_okno_t += dt
	if _okno_t >= float(cfg["okno_s"]):
		_vyhodnot_okno()
	if _chce != 0:
		_chce_t += dt
		var odklad := float(cfg["odklad_dolu_s"] if _chce > 0 else cfg["odklad_nahoru_s"])
		if klid or (_chce > 0 and _chce_t >= odklad):
			_proved()
		elif _chce < 0 and _chce_t >= odklad:
			_chce = 0                        # zvyseni pri pohybu odlozeno - zkusi se po dalsim klidu
			_klid_t = _nahoru_s * 0.5


func _vyhodnot_okno() -> void:
	var t := _okno_t
	var s := _okno.duplicate()
	var cpu := _okno_cpu
	_reset_okna()
	if s.size() < int(cfg["min_snimku"]) or _od_zmeny < float(cfg["po_zmene_s"]):
		return
	var soucet := 0.0
	for x in s:
		soucet += x
	prumer = soucet / s.size()
	uzke = "cpu" if cpu / soucet > float(cfg["cpu_podil"]) else "gpu"
	s.sort()
	p95 = s[mini(int(s.size() * float(cfg["percentil"])), s.size() - 1)]
	var r := float(cfg["rozpocet_ms"])
	var f := max_fps()
	var zle := p95 > r * float(cfg["dolu_p95_podil"]) or prumer > r * float(cfg["dolu_prumer_podil"])
	var klid := p95 < r * float(cfg["nahoru_p95_podil"])
	if f > 0:
		# omezene snimky trvaji aspon 1000/f ms - rezerva se neda zmerit (popis _omezeno v datech)
		var sn := 1000.0 / f
		zle = p95 > sn * float(cfg["omezeno_dolu_x"]) or prumer > sn * float(cfg["omezeno_klid_x"])
		klid = p95 <= sn * float(cfg["omezeno_klid_x"])
	if zle:
		_zle += 1
		_klid_t = 0.0
	else:
		_zle = 0
		_klid_t = _klid_t + t if klid and not _teplo_blokuje() else 0.0
	# nouzova uroven: vsechny jemne zapnute a porad nedostatek
	_nouze_t = _nouze_t + t if zle and _jemne_vycerpane() else 0.0
	if _chce != 0:
		return
	if _zle >= int(cfg["dolu_oken"]) and dalsi_krok() != "":
		_pozadej(1, "p95 %.0f / prumer %.0f ms, %s" % [p95, prumer, uzke])
	elif not akt.is_empty() and _klid_t >= _nahoru_s:
		_pozadej(-1, "klid %.0f s, p95 %.0f ms" % [_klid_t, p95])


func _jemne_vycerpane() -> bool:
	for k: Dictionary in kroky:
		if String(k.get("uroven", "jemna")) != "nouzova" and not akt.has(String(k["id"])):
			return false
	return true


func _teplo_blokuje() -> bool:
	return teplo >= float(cfg["teplo"]["prah_blok_nahoru"])


func _pozadej(smer: int, duvod: String) -> void:
	_chce = smer
	_chce_duvod = duvod
	_chce_t = 0.0


func _proved() -> void:
	var z := akt.size()
	var id := ""
	if _chce > 0:
		id = dalsi_krok()
		if id != "":
			akt.append(id)
		if _od_zvyseni >= 0.0:
			_nahoru_s = minf(_nahoru_s * 2.0, float(cfg["nahoru_s_max"]))   # spadlo hned po zvyseni: hystereze
			_od_zvyseni = -1.0
	elif not akt.is_empty():
		id = akt.pop_back()
		_od_zvyseni = 0.0
	_chce = 0
	_zle = 0
	_klid_t = 0.0
	_nouze_t = 0.0
	_od_zmeny = 0.0
	_reset_okna()
	if akt.size() != z:
		_zaznam("%s %s (%s)" % ["+" if akt.size() > z else "-", id, _chce_duvod])
		_uplatni()


func _reset_okna() -> void:
	_okno = PackedFloat32Array()
	_okno_cpu = 0.0
	_okno_t = 0.0


func _zaznam(t: String) -> void:
	zmen += 1
	var r := "KVALITA %s; zapnuto %d/%d [%s]%s, teplo %s, nahoru za %.0f s" % [t, akt.size(), max_stupen(), popis_stupne(),
			" + tisen pameti" if tisen_pameti else "", ("%.2f" % teplo) if teplo >= 0.0 else "N/A", _nahoru_s]
	historie.append(r)
	if historie.size() > 8:
		historie.pop_front()
	print(r)
	if main and main.diag:
		main.diag.faze(r)
	zmena.emit(akt.size(), t)


# ------------------------------------------------------------------ pamet a teplo

func _pamet_krok(dt: float) -> void:
	_pamet_t += dt
	if _pamet_t < float(cfg["pamet"]["dotaz_s"]) or main.diag == null:
		return
	_pamet_t = 0.0
	var vol := int(main.diag._volna)          # diag._zapis obnovuje kazde 2 s (-1 = nezname)
	pamet(vol, Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0)


## Tisen pameti s hysterezi (volano i z testu).
func pamet(volna_mb: int, vram_mb: float) -> void:
	var p: Dictionary = cfg["pamet"]
	var zle := (volna_mb >= 0 and volna_mb < int(p["ram_volna_min_mb"])) or vram_mb > float(p["vram_max_mb"])
	var dobre := (volna_mb < 0 or volna_mb > int(p["ram_volna_ok_mb"])) and vram_mb < float(p["vram_ok_mb"])
	if zle and not tisen_pameti:
		tisen_pameti = true
		_zaznam("tisen pameti: volna RAM %d MB, VRAM %.0f MB" % [volna_mb, vram_mb])
		_uplatni()
	elif dobre and tisen_pameti:
		tisen_pameti = false
		_zaznam("pamet v poradku: volna RAM %d MB, VRAM %.0f MB" % [volna_mb, vram_mb])
		_uplatni()


func _teplo_krok(dt: float) -> void:
	if not bool(cfg["teplo"]["zapnuto"]) or not _teplo_ok or OS.get_name() != "Android":
		return
	_teplo_t += dt
	if _teplo_t < float(cfg["teplo"]["dotaz_s"]) and _teplo0 >= 0.0:
		return
	var dt_t := _teplo_t
	_teplo_t = 0.0
	var h := _headroom(int(cfg["teplo"]["prognoza_s"]))
	if _teplo0 < 0.0 and (is_nan(h) or h <= 0.0):
		_teplo_ok = false                    # Android: prvni hodnota NaN nebo 0 = API na zarizeni neni
		if main and main.diag:
			main.diag.faze("KVALITA teplo: getThermalHeadroom nedostupne (%s)" % str(h))
		return
	if is_nan(h) or h < 0.0:
		return
	teplo_hodnota(h, dt_t)


## Nova hodnota headroom (volano i z testu): blok zvyseni, snizeni predem, trend ohrevu.
func teplo_hodnota(h: float, dt_t: float) -> void:
	var tc: Dictionary = cfg["teplo"]
	var trend := (h - _teplo0) / dt_t * 60.0 if _teplo0 >= 0.0 and dt_t > 0.0 else 0.0
	_teplo0 = h
	teplo = h
	if _chce != 0 or dalsi_krok() == "":
		return
	if h >= float(tc["prah_hned"]) and _teplo_dolu_t >= float(tc["hned_odstup_s"]):
		_teplo_dolu_t = 0.0
		_pozadej(1, "teplo %.2f (hned)" % h)
	elif h >= float(tc["prah_dolu"]) and _teplo_dolu_t >= float(tc["dolu_odstup_s"]):
		_teplo_dolu_t = 0.0
		_pozadej(1, "teplo %.2f" % h)
	elif h >= float(tc["trend_od"]) and trend >= float(tc["trend_za_min"]) and _teplo_dolu_t >= float(tc["dolu_odstup_s"]):
		_teplo_dolu_t = 0.0
		_pozadej(1, "teplo %.2f roste %+.2f/min" % [h, trend])
	if trend > 0.0:
		_klid_t = 0.0                        # dokud se tablet ohriva, kvalita se nezvysuje (Unity: zvyseni jen v klidu)


## PowerManager.getThermalHeadroom (Android 11+) pres AndroidRuntime (Godot 4.4, bez pluginu). Selze-li volani,
## skript funkci prerusi a _teplo_ok zustane false = teplo se uz nezkousi.
func _headroom(prognoza: int) -> float:
	_teplo_ok = false
	if _pm == null:
		if not Engine.has_singleton("AndroidRuntime"):
			return NAN
		var ver: Variant = JavaClassWrapper.wrap("android.os.Build$VERSION")
		if ver == null or int(ver.SDK_INT) < 30:
			return NAN
		var rt: Variant = Engine.get_singleton("AndroidRuntime")
		var act: Variant = rt.getActivity()
		if act == null:
			return NAN
		_pm = act.getSystemService("power")
		if _pm == null:
			return NAN
	var h := float(_pm.getThermalHeadroom(prognoza))
	_teplo_ok = true
	return h


# ------------------------------------------------------------------ uplatneni

## Zaklad z rucniho nastaveni - volat na konci main.apply_quality (prepise meritko, stiny, zari), pak znovu uplatnit kroky.
func zaklad() -> void:
	_zakl_meritko = get_viewport().scaling_3d_scale
	if main and main.day:
		if main.day.sun:
			_zakl_stin = (main.day.sun as DirectionalLight3D).directional_shadow_max_distance
		if main.day.env:
			_zakl_zare = (main.day.env as Environment).glow_enabled
	for k: String in ["meritko", "stin", "zare"]:
		_upl.erase(k)
	_uplatni()


func _uplatni() -> void:
	var mer := 1.0
	var stin := -1.0
	var un := false
	var zare := true
	var skup: Array = []
	var dos := -1.0
	for k: Dictionary in _aktivni():
		match String(k["druh"]):
			"meritko_3d":
				mer = minf(mer, float(k["hodnota"]))
			"stin_dosah":
				stin = float(k["hodnota"]) if stin < 0.0 else minf(stin, float(k["hodnota"]))
			"trava_unshaded":
				un = true
			"zare":
				zare = false
			"stin_skupiny":
				for g: String in k["hodnota"]:
					if not skup.has(g):
						skup.append(g)
			"dosah_travy":
				dos = float(k["hodnota"]) if dos < 0.0 else minf(dos, float(k["hodnota"]))
	if main == null or not bool(main.get("ready_done")):
		return
	main.apply_fyzika()                          # Engine.max_fps podle max_fps()
	if _zakl_meritko > 0.0 and _upl.get("meritko", -1.0) != mer:
		get_viewport().scaling_3d_scale = _zakl_meritko * mer      # skokem: zmena = nove buffery obrazu
		_upl["meritko"] = mer
	if main.day:
		var sun: DirectionalLight3D = main.day.sun
		if sun and _zakl_stin > 0.0 and _upl.get("stin", -2.0) != stin:
			sun.directional_shadow_max_distance = _zakl_stin if stin < 0.0 else minf(_zakl_stin, stin)
			_upl["stin"] = stin
		var env: Environment = main.day.env
		if env and _upl.get("zare", -1) != int(zare):
			env.glow_enabled = _zakl_zare and zare
			_upl["zare"] = int(zare)
	var lu: Node = main.get_node_or_null("Louka")
	if lu:
		if _upl.get("un", false) != un:
			lu.nastav_unshaded(un or bool(lu._un0))
			_upl["un"] = un
		if _upl.get("dos", -1.0) != dos:
			lu.nastav_dosah_trsu(dos)
			_upl["dos"] = dos
	var bylo: Array = _upl.get("skup", [])
	for g: String in bylo:
		if not skup.has(g):
			main._ab_stin(get_tree().root.find_children(g, "Node3D", true, false), true)
	for g: String in skup:
		if not bylo.has(g):
			main._ab_stin(get_tree().root.find_children(g, "Node3D", true, false), false)
	_upl["skup"] = skup
