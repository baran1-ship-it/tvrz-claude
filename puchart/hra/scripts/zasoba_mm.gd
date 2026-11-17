extends RefCounted
## Pevná zásoba MultiMeshů (P2, docs/rozpracovane/vykon_z_havrana_15_11.md; Havran rozbor_gpu_15_11.md Z4/K5): vrstvy po
## buňkách (louka, byliny, keře, les zblízka, kameny, ves) dřív při každé přestavbě buňky dělaly MultiMesh.new() +
## instance_count = nová alokace bufferu na grafice (Godot 4.7.2 gles3 mesh_storage.cpp _multimesh_allocate_data:
## glGenBuffers + glBufferData) a starý uvolnily – alokace dokola, podezření na záseky (Havran 1,2 s u louky).
## Teď: MultiMesh s pevnou kapacitou (třídy kapacity z rozpocty.json zasoba_mm), vrácený se odloží do kruhu podle sítě
## a kapacity a znovu se použije nejdřív po stari_snimku snímcích (grafika ho už nečte – kruh bufferů, Qualcomm fórum);
## přestavba = přepis bufferu (multimesh_set_buffer stejné velikosti) a visible_instance_count = n.
## Klíč obsahuje síť: změna sítě u MultiMeshe s nahraným bufferem čte buffer zpět z grafiky (_multimesh_set_mesh →
## buffer_get_data = synchronizace CPU–GPU), proto se síť slotu nikdy nemění.

static var _cfg := {}
static var _volne := {}        # klíč -> Array [[MultiMesh, snímek vrácení], ...] (nejstarší vpředu = kruh)
static var novych := 0         # alokací (panel / měření)
static var znovu := 0          # znovupoužití ze zásoby
static var mimo := 0           # nad největší třídou (bez zásoby)

static func _nastaveni() -> Dictionary:
	if _cfg.is_empty():
		var d: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json")) if FileAccess.file_exists("res://data/rozpocty.json") else null
		_cfg = (d as Dictionary).get("zasoba_mm", {}) if d is Dictionary else {}
		if _cfg.is_empty(): _cfg = {"zapnuto": false}
	return _cfg

static func zapnuto() -> bool:
	return bool(_nastaveni().get("zapnuto", false))

static func _kapacita(n: int) -> int:
	for c in _nastaveni().get("tridy_kapacity", []):
		if n <= int(c): return int(c)
	return -1

## MultiMesh se sítí a n instancemi z bufferu (12 floatů na instanci, s custom 16 – formát MultiMesh.buffer).
## custom_aabb: když je zadán, platí pro celý MultiMesh (louka). Bez zásoby (vypnuto nebo n nad třídami) jako dřív.
static func vezmi(mesh: Mesh, buf: PackedFloat32Array, n: int, custom := false, aabb := AABB()) -> MultiMesh:
	var s := 16 if custom else 12
	var cap := _kapacita(n) if zapnuto() else -1
	var mm: MultiMesh = null
	if cap > 0:
		var k := "%d|%d|%d" % [mesh.get_rid().get_id(), cap, s]
		var fr: Array = _volne.get(k, [])
		if not fr.is_empty() and Engine.get_frames_drawn() - int(fr[0][1]) >= int(_cfg.get("stari_snimku", 3)):
			mm = fr.pop_front()[0]; znovu += 1
	if mm == null:
		mm = MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_custom_data = custom; mm.mesh = mesh
		mm.instance_count = cap if cap > 0 else n
		if cap > 0: mm.set_meta("zasoba", true); novych += 1
		else: mimo += 1
	if aabb.size != Vector3.ZERO: mm.custom_aabb = aabb
	var b := buf
	if mm.instance_count > n and n > 0:   # doplnit opakováním skutečných instancí (AABB bez custom_aabb zůstane těsný, nic se nekreslí – visible_instance_count)
		b = buf.duplicate()
		while b.size() < mm.instance_count * s:
			b.append_array(b.slice(0, mini(b.size(), mm.instance_count * s - b.size())))
	if n > 0: mm.buffer = b
	mm.visible_instance_count = n if mm.instance_count != n else -1
	return mm

## Vrátit MultiMesh do zásoby (uzel, který ho kreslí, se ruší – grafika ho smí číst ještě stari_snimku snímků).
static func vrat(mm: MultiMesh) -> void:
	if mm == null or not mm.has_meta("zasoba"): return
	var k := "%d|%d|%d" % [mm.mesh.get_rid().get_id(), mm.instance_count, 16 if mm.use_custom_data else 12]
	if not _volne.has(k): _volne[k] = []
	var fr: Array = _volne[k]
	if fr.size() >= int(_nastaveni().get("max_volnych_na_klic", 12)): return   # strop paměti: přebytečný se uvolní
	mm.visible_instance_count = 0
	fr.append([mm, Engine.get_frames_drawn()])

## Vrátit MultiMeshe všech MultiMeshInstance3D v uzlu (i uzel sám) – volat před queue_free buňky.
static func vrat_strom(n: Node) -> void:
	if n is MultiMeshInstance3D: vrat((n as MultiMeshInstance3D).multimesh)
	for c in n.get_children(): vrat_strom(c)

static func souhrn() -> String:
	var v := 0
	for k in _volne: v += (_volne[k] as Array).size()
	return "zásoba MM: nových %d, znovu %d, mimo tříd %d, volných %d" % [novych, znovu, mimo, v]
