extends Node
## Vykreslování Compatibility ↔ Vulkan (Mobile) v jedné APK + pojistka proti pádu (Míša 15. 11.: „Vulkan chci vyzkoušet“).
## Autoload „Vykreslovani“ (project.godot) – běží před hlavní scénou, takže čítač pádů se zapíše dřív, než se staví svět.
## Volba se zapisuje do user://override.cfg, který Godot načte při dalším startu PŘED vytvořením rendereru
## (project.godot application/config/project_settings_override; zdroj a postup v pravidla/svet/vykreslovani.json).
## Pojistka (vykreslovani.json pojistka): start ve Vulkanu = +1 nedokončený start; potvrzeno po potvrzeni_s s běžící hrou
## nebo návratem ze hry do nabídky = 0. Při pady_max se override.cfg smaže už při startu (běžící Vulkan je načtený) a obnoví
## se až po potvrzení → další pád naběhne v Compatibility; ta pak volbu vrátí a menu ukáže hlášku. Žádný cyklus pádů.

const DATA := "res://data/vykreslovani.json"

var cfg: Dictionary = {}
var metoda := ""        # skutečně běžící (RenderingServer), ne přání
var ovladac := ""
var adapter := ""
var api := ""
var hlaska := ""        # jednorázová zpráva pro nabídku (vrácení na Compatibility)
var _hra_s := 0.0
var _hlida := false     # tento start se počítá (Vulkan z naší volby)
var _n_pred := 0        # čítač před tímto startem
var _potvrzeno := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	metoda = RenderingServer.get_current_rendering_method()
	ovladac = RenderingServer.get_current_rendering_driver_name()
	adapter = RenderingServer.get_video_adapter_name()
	api = RenderingServer.get_video_adapter_api_version()
	if FileAccess.file_exists(DATA):
		var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		if d is Dictionary: cfg = d
	if cfg.is_empty():
		set_process(false); return
	print("VYKRESLOVANI %s / %s | %s | %s" % [metoda, ovladac, adapter, api])
	_pri_startu()
	set_process(_hlida)


## ---------------------------------------------------------------- dotazy pro menu, panel a měření

func je_vulkan() -> bool:
	return ovladac == "vulkan"

## Volba odpovídající běžícímu rendereru (podle metody, ne podle přání).
func bezici() -> Dictionary:
	for v: Dictionary in cfg.get("volby", []):
		if String(v["metoda"]) == metoda: return v
	return {"id": metoda, "nazev": metoda, "kratce": metoda, "metoda": metoda, "ovladac": ovladac}

## Krátký popis do panelu a výsledku měření: „Vulkan Mobile (vulkan) · Adreno … · 1.3.…“.
func popis() -> String:
	return "%s (%s) · %s · %s" % [String(bezici().get("kratce", metoda)), ovladac, adapter, api]

func text(k: String) -> Variant:
	return cfg.get("texty", {}).get(k, k)

## Poslední důvod vrácení (stav_soubor) – pro stránku vykreslování.
func duvod() -> String:
	return String(_stav().get_value("vulkan", "duvod", ""))


## ---------------------------------------------------------------- přepnutí (z nabídky) – zapíše a restartuje

func prepni(id: String) -> void:
	var volba: Dictionary = {}
	for v: Dictionary in cfg.get("volby", []):
		if String(v["id"]) == id: volba = v
	if volba.is_empty(): return
	_hlida = false   # vlastní restart není pád (čítač nastaví volba)
	var st := _stav()
	var vulkan := not (volba.get("override", {}) as Dictionary).is_empty()
	st.set_value("vulkan", "chce", vulkan)
	st.set_value("vulkan", "nedokoncene", 0)
	st.set_value("vulkan", "zmena", Time.get_datetime_string_from_system())
	st.save(String(cfg["stav_soubor"]))
	if vulkan: _zapis_override(volba)
	else: _smaz_override()
	# Android: Main::cleanup → OS_Android::create_instance → nový proces (GodotActivity.onNewGodotInstanceRequested); parametry
	# příkazové řádky exportovaná aktivita zahodí, proto jen override.cfg. Na PC se předají původní parametry (--path).
	OS.set_restart_on_exit(true, OS.get_cmdline_args() if OS.has_feature("pc") else PackedStringArray())
	get_tree().quit()


## Návrat ze hry do nabídky = vstup do hry proběhl (menu.gd show_menu(true)).
func navrat_do_menu() -> void:
	if _hlida: _potvrd()


## ---------------------------------------------------------------- pojistka

func _process(d: float) -> void:
	if _potvrzeno: set_process(false); return
	if not get_tree().paused:   # hra nebo měření běží (nabídka strom pozastaví)
		_hra_s += d
		if _hra_s >= float(cfg["pojistka"]["potvrzeni_s"]): _potvrd()


func _notification(what: int) -> void:
	if not _hlida or _potvrzeno: return
	# čisté ukončení a odchod do pozadí nejsou pád: čítač zpět (při zabití procesu v pozadí by start jinak vypadal jako pád);
	# po návratu z pozadí se znovu hlídá
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_PREDELETE:
		_nastav_citac(_n_pred)
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		_nastav_citac(_n_pred + 1)


func _pri_startu() -> void:
	var st := _stav()
	var chce := bool(st.get_value("vulkan", "chce", false))
	var n := int(st.get_value("vulkan", "nedokoncene", 0))
	var limit := int(cfg["pojistka"]["pady_max"])
	var ovr := String(cfg["override_soubor"])
	if je_vulkan():
		# hlídat jen Vulkan z naší volby (vývojář na PC s --rendering-method mobile čítač nemění)
		_hlida = chce or FileAccess.file_exists(ovr)
		if not _hlida: return
		_n_pred = n
		_nastav_citac(n + 1)
		print("VYKRESLOVANI pojistka: nedokončených startů %d/%d" % [n + 1, limit])
	elif chce:
		# volba Vulkan, ale běží Compatibility: pád (čítač) / Godot přešel na OpenGL (Vulkan nejde) / override chybí
		var proc := ""
		if n >= limit: proc = String(text("hlaska_pad")) % n
		elif FileAccess.file_exists(ovr): proc = String(text("hlaska_fallback"))
		else: proc = String(text("hlaska_bez_override"))
		hlaska = proc
		st.set_value("vulkan", "chce", false)
		st.set_value("vulkan", "nedokoncene", 0)
		st.set_value("vulkan", "duvod", "%s %s (%s / %s, %s)" % [Time.get_datetime_string_from_system(), proc, metoda, ovladac, adapter])
		st.save(String(cfg["stav_soubor"]))
		_smaz_override()
		push_warning("VYKRESLOVANI " + proc)


## Čítač nedokončených startů; při pady_max override pryč (další start = Compatibility), pod ním override zpět.
func _nastav_citac(n: int) -> void:
	var st := _stav()
	st.set_value("vulkan", "nedokoncene", n)
	st.save(String(cfg["stav_soubor"]))
	if n >= int(cfg["pojistka"]["pady_max"]): _smaz_override()
	elif bool(st.get_value("vulkan", "chce", false)): _zapis_override(_volba_vulkan())


func _potvrd() -> void:
	_potvrzeno = true
	_n_pred = 0
	_nastav_citac(0)
	var st := _stav()
	st.set_value("vulkan", "potvrzeno", Time.get_datetime_string_from_system())
	st.save(String(cfg["stav_soubor"]))
	print("VYKRESLOVANI pojistka: start ve Vulkanu potvrzen (%.0f s hry)" % _hra_s)


func _volba_vulkan() -> Dictionary:
	for v: Dictionary in cfg.get("volby", []):
		if not (v.get("override", {}) as Dictionary).is_empty(): return v
	return {}


func _zapis_override(volba: Dictionary) -> void:
	if volba.is_empty(): return
	var c := ConfigFile.new()
	for k: String in (volba["override"] as Dictionary).keys():
		var i := k.find("/")   # „rendering/renderer/rendering_method“ → sekce [rendering], klíč renderer/rendering_method
		c.set_value(k.substr(0, i), k.substr(i + 1), volba["override"][k])
	c.save(String(cfg["override_soubor"]))


func _smaz_override() -> void:
	var ovr := String(cfg["override_soubor"])
	if FileAccess.file_exists(ovr): DirAccess.remove_absolute(ovr)


func _stav() -> ConfigFile:
	var c := ConfigFile.new()
	c.load(String(cfg.get("stav_soubor", "user://vykreslovani.cfg")))
	return c
