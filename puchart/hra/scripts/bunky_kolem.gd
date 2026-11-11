extends Node3D
## Vrstva po buňkách kolem hráče – převzato z Havrana (svet.gd rostliny_rozdel / rostliny_okoli / planovac, Míša 0.67
## „pád (RAM): 47 000 MultiMeshInstance3D rozsevu po celé mapě“). Puchart 11. 11.: stejná chyba – les v buňkách 4 m na celou
## mapu = přes 115 tis. uzlů, tablet padal hned při startu (výpis „mem_new is null“ = došla paměť).
## Platí pro každou vrstvu s krátkým dosahem (les zblízka, kameny v korytech, rostliny skal): po postavení jen data
## (buffer instancí po buňkách), uzly vznikají v okolí hráče. Jeden plánovač pro všechny vrstvy s rozpočtem času na snímek
## (hra/pravidla/svet/rozpocty.json planovac: tablet 2 ms, PC 3 ms): nejbližší buňka první, po jednom MultiMeshi,
## buňka je vidět až celá (žádné díry), uvolňování až když nic nechybí. Start a skok (teleport, test) = vše hned.

const Pravidla := preload("res://scripts/pravidla.gd")
const DAVKA := 512                 # instancí na jeden MultiMesh (Havran rostliny_rozdel)

var B := 25.0                      # m, strana buňky
var R := 60.0                      # m, buňky se středem do R (dosah kreslení + půl úhlopříčky + rezerva) se staví
var rezerva := 30.0                # m, uvolnit až za R + rezerva (Havran rostliny_uvolnit_m = dosah + 30)
var vyrob: Callable                # func(skupina, buf: PackedFloat32Array, n: int) -> Array[GeometryInstance3D]

var _data := {}                    # Vector2i -> [[skupina, buf (12 floatů na instanci), n], ...] po dávkách DAVKA
var _sber := {}                    # při plnění: Vector2i -> {skupina -> PackedFloat32Array}
var _uzly := {}                    # Vector2i -> Node3D (i rozestavěná buňka, skrytá)
var _rozest := {}                  # Vector2i -> další index dávky (rozestavěné)
var _posledni := Vector3(1e9, 0.0, 1e9)

static var _vrstvy: Array = []     # všechny vrstvy – jeden plánovač
static var _snimek := -1
static var _cfg := {}

func pridej(t: Transform3D, skupina) -> void:
	var c := Vector2i(floori(t.origin.x / B), floori(t.origin.z / B))
	if not _sber.has(c): _sber[c] = {}
	# Packed pole ve slovníku je hodnota (kopie při zápisu): vyjmout, doplnit, vrátit – jinak se zápis ztratí
	var buf: PackedFloat32Array = _sber[c].get(skupina, PackedFloat32Array()); _sber[c].erase(skupina)
	var b := t.basis
	buf.append_array([b.x.x, b.y.x, b.z.x, t.origin.x, b.x.y, b.y.y, b.z.y, t.origin.y, b.x.z, b.y.z, b.z.z, t.origin.z])
	_sber[c][skupina] = buf

## po naplnění: sběr → dávky (samo při prvním použití – vrstva se může plnit i po vložení do stromu)
func _uzavri() -> void:
	if _sber.is_empty(): return
	for c in _sber:
		_data[c] = []
		for sk in _sber[c]:
			var buf: PackedFloat32Array = _sber[c][sk]; var n := buf.size() / 12; var od := 0
			while od < n:
				var nn := mini(DAVKA, n - od)
				(_data[c] as Array).append([sk, buf.slice(od * 12, (od + nn) * 12), nn])
				od += nn
	_sber.clear()

func _ready() -> void:
	_vrstvy.append(self)

func _exit_tree() -> void:
	_vrstvy.erase(self)

func postavenych() -> int:
	return _uzly.size()

func bunek() -> int:
	_uzavri(); return _data.size()

func _process(_d: float) -> void:
	if _snimek == Engine.get_process_frames(): return
	_snimek = Engine.get_process_frames()
	var cam := get_viewport().get_camera_3d()
	if cam: planovac(cam.global_position)

## Jeden plánovač pro všechny vrstvy (Havran svet.planovac): rozpočet času na snímek, nejbližší chybějící buňka první.
static func planovac(p: Vector3, vse := false) -> void:
	if _cfg.is_empty(): _cfg = Pravidla.cti("rozpocty", "planovac")
	var mob := OS.has_feature("mobile")
	var roz := int(_cfg.get("rozpocet_us_tablet" if mob else "rozpocet_us_pc", 2000 if mob else 3000))
	var chybi := []
	for v: Node3D in _vrstvy:
		var skok: bool = Vector2(p.x - v._posledni.x, p.z - v._posledni.z).length() > v.R
		v._posledni = p
		for e in v._chybi(p): chybi.append([e[0], v, e[1], vse or skok])
	chybi.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	var t0 := Time.get_ticks_usec()
	for e in chybi:
		var v: Node3D = e[1]
		if e[3]: v._postav(e[2], true); continue
		if Time.get_ticks_usec() - t0 >= roz: continue
		v._postav(e[2], false, roz - (Time.get_ticks_usec() - t0))
	if chybi.is_empty():
		for v: Node3D in _vrstvy: v._uvolni(p)

## [vzdálenost, buňka] chybějících (i rozestavěných) buněk v dosahu
func _chybi(p: Vector3) -> Array:
	_uzavri()
	var out := []; var n := int(ceil(R / B)) + 1; var c0 := Vector2i(floori(p.x / B), floori(p.z / B))
	for i in range(-n, n + 1):
		for j in range(-n, n + 1):
			var c := c0 + Vector2i(i, j)
			if not _data.has(c) or (_uzly.has(c) and not _rozest.has(c)): continue
			var d := _vzd(c, p)
			if d <= R: out.append([d, c])
	return out

func _uvolni(p: Vector3) -> void:
	for c: Vector2i in _uzly.keys():
		if _vzd(c, p) > R + rezerva:
			_uzly[c].queue_free(); _uzly.erase(c); _rozest.erase(c)

func _vzd(c: Vector2i, p: Vector3) -> float:
	return Vector2((c.x + 0.5) * B - p.x, (c.y + 0.5) * B - p.z).length()

## Staví buňku po dávkách; celá = zobrazit. Bez rozpočtu (vse) celou hned.
func _postav(c: Vector2i, vse: bool, rozpocet_us := 0) -> void:
	if not _uzly.has(c):
		var u := Node3D.new(); u.name = "b_%d_%d" % [c.x, c.y]; u.visible = false; add_child(u)
		_uzly[c] = u; _rozest[c] = 0
	var u: Node3D = _uzly[c]; var t0 := Time.get_ticks_usec(); var d: Array = _data[c]
	while _rozest[c] < d.size():
		if not vse and Time.get_ticks_usec() - t0 >= rozpocet_us: return
		var e: Array = d[_rozest[c]]
		for g: Node3D in vyrob.call(e[0], e[1], e[2]): u.add_child(g)
		_rozest[c] += 1
	_rozest.erase(c); u.visible = true

## Vzorek každé skupiny (jedna instance) pro předehřátí shaderů – buňky u hráče při startu nemusí mít všechny skupiny.
## Uzly nejsou ve stromu scény; predehrati.gd z nich udělá drobné kopie a vzorky uvolní.
func vzory() -> Array:
	_uzavri()
	var vid := {}; var out := []
	for c in _data:
		for e: Array in _data[c]:
			if vid.has(e[0]): continue
			vid[e[0]] = true
			out.append_array(vyrob.call(e[0], (e[1] as PackedFloat32Array).slice(0, 12), 1))
	return out

## MultiMeshInstance3D ze sítě a bufferu instancí (12 floatů na instanci – formát MultiMesh.buffer)
static func mmi(mesh: Mesh, buf: PackedFloat32Array, n: int) -> MultiMeshInstance3D:
	var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = mesh
	mm.instance_count = n; mm.buffer = buf
	var m := MultiMeshInstance3D.new(); m.multimesh = mm
	return m
