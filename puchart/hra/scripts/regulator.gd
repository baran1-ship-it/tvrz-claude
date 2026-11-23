extends Node
## Automatika detailu (plán z rešerše 17. 11. A1; Halcyon – PDF 1 s. 3; CLAUDE.md „automatika jen v extrému, snížení detailu,
## ne rozlišení, po zchladnutí zpět“). Hlídá 75. percentil skutečné délky snímku (razítka, ne vyhlazené delta) za posledních
## okno_s sekund. Když p75 drží nad dolu_p75_ms po dolu_vydrz_s, ubere jeden stupeň detailu; když drží pod nahoru_p75_ms po
## nahoru_vydrz_s (tablet vychladl), jeden stupeň vrátí. Jeden dlouhý snímek p75 nepohne. Stupně jsou v datech
## (rozpocty.json automatika.stupne, kumulativní) a mění jen parametry už postavených věcí – dosah trávy a keřů ve shaderu,
## dosah stínu slunce, práh LOD – nic se nepřestavuje (přestavba buněk = zásek) a rozlišení 3D (nastavení hráče) se nemění.
## Během měření (mereni.gd vypni/zapni) je vypnutý a vrácený na stupeň 0, aby čísla byla poctivá.
## Na PC jen s PUCHART_AUTOMATIKA=1 (llvmpipe v testech kreslí každý snímek nad 40 ms – testy a snímky musí mít plný detail).

var cfg: Dictionary = {}
var stupen := 0
var aktivni := false          # běží na tomto zařízení (data zapnuto + tablet / PUCHART_AUTOMATIKA)
var duvod_vypnuti := ""       # „měření“ – dočasně vypnuto
var p75 := -1.0               # poslední vyhodnocený p75 (ms), -1 = málo dat
var zmen := 0                 # počet změn stupně od startu (panel)
var _casy := PackedFloat32Array()
var _suma := 0.0              # součet _casy (ms) = délka okna
var _do_kontroly := 0.0
var _nad := 0.0               # jak dlouho p75 drží nad prahem (s)
var _pod := 0.0
var _beh := 0.0               # čas od startu (zahřátí)
var _posl := 0
var _puvodni := {}            # klíč páky -> původní hodnoty (vrací se přesně)

func _ready() -> void:
	add_to_group("regulator")
	if FileAccess.file_exists("res://data/rozpocty.json"):
		var d: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json"))
		if d is Dictionary: cfg = (d as Dictionary).get("automatika", {})
	var pc_zap := OS.get_environment("PUCHART_AUTOMATIKA") == "1"
	aktivni = not cfg.is_empty() and bool(cfg.get("zapnuto", false)) and (OS.has_feature("mobile") or pc_zap)
	_posl = Time.get_ticks_usec()

func pocet_stupnu() -> int:
	return (cfg.get("stupne", []) as Array).size()

## Měření (mereni.gd): plný detail a žádné zásahy, dokud se nezapne zpět.
func vypni(duvod: String) -> void:
	duvod_vypnuti = duvod
	nastav_stupen(0)
	_reset()

func zapni() -> void:
	duvod_vypnuti = ""
	_reset()
	_posl = Time.get_ticks_usec()

func _reset() -> void:
	_casy = PackedFloat32Array(); _suma = 0.0; _nad = 0.0; _pod = 0.0; _do_kontroly = 0.0; p75 = -1.0

func _process(_d: float) -> void:
	var now := Time.get_ticks_usec(); var ms := (now - _posl) / 1000.0; _posl = now
	if not aktivni or duvod_vypnuti != "": return
	if ms > float(cfg.get("max_snimek_ms", 1000.0)): return   # pauza, nabídka, načítání – není to plynulost hry
	_beh += ms / 1000.0
	if _beh < float(cfg.get("zahrati_s", 20.0)): return
	krok(ms)

## Jeden snímek délky ms (ms). Odděleno od _process kvůli testu (test_regulator.gd simuluje pomalé snímky).
func krok(ms: float) -> void:
	if duvod_vypnuti != "": return
	_casy.append(ms); _suma += ms
	var okno := float(cfg.get("okno_s", 5.0)) * 1000.0
	while _casy.size() > 1 and _suma - _casy[0] >= okno:
		_suma -= _casy[0]; _casy.remove_at(0)
	_do_kontroly += ms / 1000.0
	var kontrola := float(cfg.get("kontrola_s", 1.0))
	if _do_kontroly < kontrola: return
	var dt := _do_kontroly; _do_kontroly = 0.0
	if _suma < okno * 0.9: p75 = -1.0; return   # okno ještě není plné (start, po změně stupně)
	var s := _casy.duplicate(); s.sort()
	p75 = s[int(s.size() * 0.75)]
	_nad = _nad + dt if p75 > float(cfg["dolu_p75_ms"]) else 0.0
	_pod = _pod + dt if p75 < float(cfg["nahoru_p75_ms"]) else 0.0
	if _nad >= float(cfg["dolu_vydrz_s"]) and stupen < pocet_stupnu():
		nastav_stupen(stupen + 1)
		_reset()   # další stupeň až podle snímků s novým detailem
	elif _pod >= float(cfg["nahoru_vydrz_s"]) and stupen > 0:
		nastav_stupen(stupen - 1)
		_reset()

## Páky stupňů 1..n (kumulativně); stupeň 0 = vše původní.
func nastav_stupen(n: int) -> void:
	n = clampi(n, 0, pocet_stupnu())
	var pak := {}
	var st: Array = cfg.get("stupne", [])
	for i in n:
		for k: String in (st[i] as Dictionary):
			if k in ["jmeno", "popis", "zdroj"] or k.begins_with("_"): continue
			pak[k] = float(st[i][k])
	_pas(float(pak.get("pas_dosah", 1.0)))
	_trava(float(pak.get("trava_dosah", 1.0)))
	_kere(float(pak.get("kere_dosah", 1.0)))
	_stiny(float(pak.get("stiny_dosah_m", -1.0)))
	_lod(float(pak.get("lod_prah_nasobek", 1.0)))
	if n != stupen:
		zmen += 1
		print("AUTOMATIKA stupeň %d → %d (%s), p75 %.1f ms" % [stupen, n, popis_stupne(n), p75])
	stupen = n

func popis_stupne(n := -1) -> String:
	if n < 0: n = stupen
	if n == 0: return "plný detail"
	return String((cfg["stupne"][n - 1] as Dictionary).get("jmeno", str(n)))

## Řádek do ladicího panelu (diag.gd).
func panel() -> String:
	if cfg.is_empty() or not bool(cfg.get("zapnuto", false)): return "automatika: vypnuta v datech"
	if not aktivni: return "automatika: jen tablet (PC: PUCHART_AUTOMATIKA=1)"
	if duvod_vypnuti != "": return "automatika: vypnuta (%s)" % duvod_vypnuti
	return "automatika: stupeň %d/%d %s · p75 %s ms · změn %d" % [stupen, pocet_stupnu(), popis_stupne(),
		("%.1f" % p75) if p75 >= 0.0 else "N/A", zmen]

## ---- páky (každá si pamatuje původní hodnoty a vrací je přesně)

func _scena() -> Node:
	return get_tree().current_scene if get_tree() else null

## Střední pás trávy (plán E1, louka.json pas): dosah buněk i konec v shaderu × f (louka.gd nastav_pas) – méně troj.
func _pas(f: float) -> void:
	var lou := _scena().get_node_or_null("Louka") if _scena() else null
	if lou and lou.has_method("nastav_pas"): lou.nastav_pas(f)

## Tráva (louka.gd, stebla.gdshader): úbytek trsů hust_do a konec hust_konec blíž – sdílené materiály, bez přestavby buněk.
func _trava(f: float) -> void:
	var lou := _scena().get_node_or_null("Louka") if _scena() else null
	if lou == null or not lou.has_method("vsechny_site"): return
	for m: Mesh in lou.vsechny_site():
		var mat := m.surface_get_material(0) as ShaderMaterial
		if mat == null or mat.get_shader_parameter("rezim") == 2: continue   # střední pás má vlastní páku (_pas)
		var id := "trava%d" % mat.get_instance_id()
		if not _puvodni.has(id): _puvodni[id] = [mat.get_shader_parameter("hust_do"), mat.get_shader_parameter("hust_konec")]
		var p: Array = _puvodni[id]
		if p[0] != null: mat.set_shader_parameter("hust_do", float(p[0]) * f)
		if p[1] != null: mat.set_shader_parameter("hust_konec", float(p[1]) * f)

## Keře a byliny (byliny.gd _fade): rozpouštění do dálky blíž – listí (listi.gdshader zanik), ostatní distance_fade.
func _kere(f: float) -> void:
	if _scena() == null: return
	for jm in ["Kere", "KereDaleko", "Byliny"]:
		var n := _scena().get_node_or_null(jm)
		if n == null or not n.has_method("vsechny_site"): continue
		for m: Mesh in n.vsechny_site():
			for i in m.get_surface_count():
				var mat := m.surface_get_material(i)
				if mat == null: continue
				var id := "ker%d" % mat.get_instance_id()
				if mat is ShaderMaterial:
					var z: Variant = (mat as ShaderMaterial).get_shader_parameter("zanik")
					if not (z is Vector2) or (z as Vector2).x == (z as Vector2).y: continue
					if not _puvodni.has(id): _puvodni[id] = z
					(mat as ShaderMaterial).set_shader_parameter("zanik", (_puvodni[id] as Vector2) * f)
				elif mat is BaseMaterial3D and (mat as BaseMaterial3D).distance_fade_mode != BaseMaterial3D.DISTANCE_FADE_DISABLED:
					var b := mat as BaseMaterial3D
					if not _puvodni.has(id): _puvodni[id] = Vector2(b.distance_fade_min_distance, b.distance_fade_max_distance)
					var v: Vector2 = _puvodni[id] * f
					b.distance_fade_min_distance = v.x; b.distance_fade_max_distance = v.y

## Stín slunce (rozpocty.json stiny.dosah_m 40): kratší dosah = méně stínových těles. -1 = původní.
func _stiny(m: float) -> void:
	if _scena() == null: return
	var l := _scena().find_children("*", "DirectionalLight3D", true, false)
	if l.is_empty(): return
	var s := l[0] as DirectionalLight3D
	if not _puvodni.has("stin"): _puvodni["stin"] = s.directional_shadow_max_distance
	s.directional_shadow_max_distance = float(_puvodni["stin"]) if m <= 0.0 else minf(m, float(_puvodni["stin"]))

## Práh LOD (Viewport.mesh_lod_threshold): větší = jednodušší stupeň sítě dřív (jen sítě s automatickým LOD; stavby
## s lod_bias 50 se nemění).
func _lod(f: float) -> void:
	var vp := get_viewport()
	if vp == null: return
	if not _puvodni.has("lod"): _puvodni["lod"] = vp.mesh_lod_threshold
	vp.mesh_lod_threshold = float(_puvodni["lod"]) * f
