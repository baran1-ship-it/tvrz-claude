extends Node
const Pravidla := preload("res://scripts/pravidla.gd")
## Automaticka kvalita (Misa 5. 11.: „pri nestihani zhorseni grafiky, aby hra jela plynule?“) - jako dynamicke rozliseni
## Unrealu / Unity Adaptive Performance: meri delky snimku, pri trvalem prekroceni rozpoctu snizi stupen, po delsim klidu
## zvysi (hystereze). Vse (prahy, okna, kroky a jejich poradi) v pravidla/svet/kvalita.json - popis tam.
## Stupen n = prvnich n povolenych kroku (bez „jen_pamet“); tisen pameti zapne kroky pamet.kroky navic.
## Bez main (test tools/test_kvalita.gd) se jen pocita stupen, nic se neprepina.

signal zmena(stupen: int, duvod: String)

var main: Node
var zapnuto := false
var stupen := 0
var tisen_pameti := false
var teplo := -1.0                      # Android thermal headroom (0 = bez skrceni, 1 = SEVERE), -1 = nezname
var historie: Array[String] = []        # posledni zmeny (panel, merici trasa)
var zmen := 0

var cfg: Dictionary
var kroky: Array = []                  # povolene kroky stupnu (poradi z dat)
var _vsechny: Dictionary = {}          # id -> krok (i jen_pamet)
var _okno := PackedFloat32Array()
var _okno_t := 0.0
var _zle := 0
var _klid_t := 0.0
var _nahoru_s := 30.0
var _od_zmeny := 1000.0
var _od_zvyseni := -1.0                 # cas od posledniho zvyseni (-1 = zadne cekajici)
var _teplo_dolu_t := 1000.0
var _chce := 0                          # cekajici zmena: +1 nize kvalita, -1 vys
var _chce_duvod := ""
var _chce_t := 0.0
var _rot := 0.0                         # otaceni kamery (st/s, vyhlazene)
var _fwd0 := Vector3.ZERO
var _posl := 0
var _p95 := 0.0
var _pamet_t := 0.0
var _teplo_t := 0.0
var _pm: Variant = null                 # android.os.PowerManager (JavaObject)
var _teplo_ok := true
# zaklad z rucniho nastaveni (main.apply_quality) a co je ted uplatneno
var _zakl_meritko := -1.0
var _zakl_stin := -1.0
var _upl: Dictionary = {}


func _init() -> void:
	cfg = {}
	for k: String in ["vychozi", "cil_ms", "nahoru_ms", "okno_s", "percentil", "min_snimku", "dolu_oken", "nahoru_s",
			"nahoru_s_max", "navrat_s", "po_zmene_s", "ignoruj_ms", "omezeno_dolu_x", "omezeno_klid_x", "kamera_klid_st_s",
			"odklad_dolu_s", "odklad_nahoru_s", "teplo", "pamet", "kroky"]:
		cfg[k] = Pravidla.cti("kvalita", k)
	for k: Dictionary in cfg["kroky"]:
		_vsechny[String(k["id"])] = k
		if bool(k.get("povoleno", true)) and not bool(k.get("jen_pamet", false)):
			kroky.append(k)
	_nahoru_s = float(cfg["nahoru_s"])


## Vychozi volba podle zarizeni (kvalita.json vychozi), kdyz hrac nic neulozil.
func vychozi() -> bool:
	var mob := OS.has_feature("mobile") or OS.has_environment("TVRZ_MOBIL")
	return bool(cfg["vychozi"]["tablet" if mob else "pc"])


## Zapnout / vypnout automatiku; vypnuti vrati stupen 0 (rucni nastaveni).
func nastav(on: bool) -> void:
	zapnuto = on
	_reset_okna()
	_chce = 0
	_klid_t = 0.0
	_nahoru_s = float(cfg["nahoru_s"])
	if not on and (stupen != 0 or tisen_pameti):
		stupen = 0
		tisen_pameti = false
		_zaznam("vypnuto (rucni kvalita)")
		_uplatni()


func max_stupen() -> int:
	return kroky.size()


## Krok omezeni snimku aktivni ve stupni (0 = neomezeno).
func max_fps() -> int:
	var f := 0
	for k: Dictionary in _aktivni():
		if String(k["druh"]) == "max_fps":
			f = int(k["hodnota"]) if f == 0 else mini(f, int(k["hodnota"]))
	return f


func _aktivni() -> Array:
	var a: Array = kroky.slice(0, stupen)
	if tisen_pameti:
		for id: String in cfg["pamet"]["kroky"]:
			if _vsechny.has(id) and not a.has(_vsechny[id]):
				a.append(_vsechny[id])
	return a


func popis_stupne() -> String:
	if stupen == 0:
		return "plná"
	var ids: Array = []
	for k: Dictionary in kroky.slice(0, stupen):
		ids.append(String(k["id"]))
	return ", ".join(ids)


func panel_text() -> String:
	if not zapnuto:
		return ""
	return " · kvalita %d/%d%s%s" % [stupen, max_stupen(), " pamet" if tisen_pameti else "",
			(" teplo %.2f" % teplo) if teplo >= 0.0 else ""]


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
		snimek(ms, dt, _rot < float(cfg["kamera_klid_st_s"]))


## Jeden snimek (ms = skutecna delka, dt = cas hry, klid = kamera se neotaci). Volano z _process i z testu.
func snimek(ms: float, dt: float, klid: bool) -> void:
	_od_zmeny += dt
	_teplo_dolu_t += dt
	if _od_zvyseni >= 0.0:
		_od_zvyseni += dt
		if _od_zvyseni > float(cfg["navrat_s"]):
			_od_zvyseni = -1.0              # zvyseni vydrzelo: cekani na dalsi zvyseni zase kratsi
			_nahoru_s = maxf(float(cfg["nahoru_s"]), _nahoru_s * 0.5)
	if ms < float(cfg["ignoruj_ms"]):
		_okno.append(ms)
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
			_klid_t = float(_nahoru_s) * 0.5


func _vyhodnot_okno() -> void:
	var t := _okno_t
	var s := _okno.duplicate()
	_reset_okna()
	if s.size() < int(cfg["min_snimku"]) or _od_zmeny < float(cfg["po_zmene_s"]):
		return
	s.sort()
	_p95 = s[mini(int(s.size() * float(cfg["percentil"])), s.size() - 1)]
	var f := max_fps()
	var dolu := float(cfg["cil_ms"])
	var klid := _p95 < float(cfg["nahoru_ms"])
	if f > 0:
		dolu = 1000.0 / f * float(cfg["omezeno_dolu_x"])
		klid = _p95 <= 1000.0 / f * float(cfg["omezeno_klid_x"])
	if _p95 > dolu:
		_zle += 1
		_klid_t = 0.0
	else:
		_zle = 0
		_klid_t = _klid_t + t if klid and not _teplo_blokuje() else 0.0
	if _chce != 0:
		return
	if _zle >= int(cfg["dolu_oken"]) and stupen < max_stupen():
		_pozadej(1, "p95 %.0f ms > %.0f" % [_p95, dolu])
	elif stupen > 0 and _klid_t >= _nahoru_s:
		_pozadej(-1, "klid %.0f s, p95 %.0f ms" % [_klid_t, _p95])


func _teplo_blokuje() -> bool:
	return teplo >= float(cfg["teplo"]["prah_blok_nahoru"])


func _pozadej(smer: int, duvod: String) -> void:
	_chce = smer
	_chce_duvod = duvod
	_chce_t = 0.0


func _proved() -> void:
	var z := stupen
	stupen = clampi(stupen + _chce, 0, max_stupen())
	if _chce > 0 and _od_zvyseni >= 0.0:
		_nahoru_s = minf(_nahoru_s * 2.0, float(cfg["nahoru_s_max"]))   # spadlo hned po zvyseni: hystereze
		_od_zvyseni = -1.0
	elif _chce < 0:
		_od_zvyseni = 0.0
	_chce = 0
	_zle = 0
	_klid_t = 0.0
	_od_zmeny = 0.0
	_reset_okna()
	if stupen != z:
		_zaznam("%d -> %d (%s)" % [z, stupen, _chce_duvod])
		_uplatni()


func _reset_okna() -> void:
	_okno = PackedFloat32Array()
	_okno_t = 0.0


func _zaznam(t: String) -> void:
	zmen += 1
	var r := "KVALITA %s; stupen %d/%d [%s]%s, teplo %s, nahoru za %.0f s" % [t, stupen, max_stupen(), popis_stupne(),
			" + tisen pameti" if tisen_pameti else "", ("%.2f" % teplo) if teplo >= 0.0 else "N/A", _nahoru_s]
	historie.append(r)
	if historie.size() > 8:
		historie.pop_front()
	print(r)
	if main and main.diag:
		main.diag.faze(r)
	zmena.emit(stupen, t)


# ------------------------------------------------------------------ pamet a teplo

func _pamet_krok(dt: float) -> void:
	_pamet_t += dt
	var p: Dictionary = cfg["pamet"]
	if _pamet_t < float(p["dotaz_s"]) or main.diag == null:
		return
	_pamet_t = 0.0
	var vol := int(main.diag._volna)          # diag._zapis obnovuje kazde 2 s (-1 = nezname)
	var vram := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0
	pamet(vol, vram)


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
	var tc: Dictionary = cfg["teplo"]
	if not bool(tc["zapnuto"]) or not _teplo_ok or OS.get_name() != "Android":
		return
	_teplo_t += dt
	if _teplo_t < float(tc["dotaz_s"]):
		return
	_teplo_t = 0.0
	var h := _headroom(int(tc["prognoza_s"]))
	if is_nan(h) or h < 0.0:
		return
	teplo = h
	if h >= float(tc["prah_dolu"]) and _teplo_dolu_t >= float(tc["dolu_odstup_s"]) and stupen < max_stupen() and _chce == 0:
		_teplo_dolu_t = 0.0
		_pozadej(1, "teplo %.2f" % h)


## PowerManager.getThermalHeadroom (Android 11+) pres AndroidRuntime (Godot 4.4, bez pluginu). Selze-li volani
## (stare Android, jine API), skript funkci prerusi a _teplo_ok zustane false = teplo se uz nezkousi.
func _headroom(prognoza: int) -> float:
	_teplo_ok = false
	if _pm == null:
		if not Engine.has_singleton("AndroidRuntime"):
			return -1.0
		var ver: Variant = JavaClassWrapper.wrap("android.os.Build$VERSION")
		if ver == null or int(ver.SDK_INT) < 30:
			return -1.0
		var act: Variant = Engine.get_singleton("AndroidRuntime").getActivity()
		if act == null:
			return -1.0
		_pm = act.getSystemService("power")
		if _pm == null:
			return -1.0
	var h := float(_pm.getThermalHeadroom(prognoza))
	_teplo_ok = true
	return h


# ------------------------------------------------------------------ uplatneni

## Zaklad z rucniho nastaveni - volat na konci main.apply_quality (prepise meritko a stiny), pak znovu uplatnit stupen.
func zaklad() -> void:
	_zakl_meritko = get_viewport().scaling_3d_scale
	if main and main.day and main.day.sun:
		_zakl_stin = (main.day.sun as DirectionalLight3D).directional_shadow_max_distance
	_upl.erase("meritko")
	_upl.erase("stin")
	_uplatni()


func _uplatni() -> void:
	var fps := 0
	var mer := 1.0
	var stin := -1.0
	var un := false
	var skup: Array = []
	var dos := -1.0
	for k: Dictionary in _aktivni():
		match String(k["druh"]):
			"max_fps":
				fps = int(k["hodnota"]) if fps == 0 else mini(fps, int(k["hodnota"]))
			"meritko_3d":
				mer = minf(mer, float(k["hodnota"]))
			"stin_dosah":
				stin = float(k["hodnota"]) if stin < 0.0 else minf(stin, float(k["hodnota"]))
			"trava_unshaded":
				un = true
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
		get_viewport().scaling_3d_scale = _zakl_meritko * mer
		_upl["meritko"] = mer
	var sun: DirectionalLight3D = main.day.sun if main.day else null
	if sun and _zakl_stin > 0.0 and _upl.get("stin", -2.0) != stin:
		sun.directional_shadow_max_distance = _zakl_stin if stin < 0.0 else minf(_zakl_stin, stin)
		_upl["stin"] = stin
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
