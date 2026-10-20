extends Node3D
## Louka v cele krajine (radce 07:30, postup CryEngine/KCD): drahe veci jsou spocitane predem (TVRZ_ROZSEV=1 ->
## modely/louka/kryti.bin: paprsky shora pod stoly, strechy a skaly), rozsev bunky 32 m z masek (biotop, okraje lesa)
## je deterministicky a bezi ve vlakne (WorkerThreadPool); hlavni vlakno jen udela MultiMesh z hotoveho bufferu.
## Viditelnost neni po bunkach, ale po trsech: kazdy ma hash, shader ho zmensi do ztracena, kdyz hash > hustota
## podle vzdalenosti (do 20 m vse, k 130 m nic, v dalce vetsi) - louka nema hranu. Trsy v bunce jsou serazene podle
## hashe, takze se kresli jen prvnich N (visible_instance_count). Trs = 3 zkrizene karty s obrazkem z atlasu
## obrazky/trava_atlas.png (blender/atlas_travy.py). Kupy travy (80-650 m) zatim po starem.
## LADENI VYKONU: HUST_DO mensi = mene trsu v dalce, KROK vetsi = ridsi rozsev (nutno znovu TVRZ_ROZSEV=1).

const Svet := preload("res://scripts/svet.gd")    # Svet.divokost (neudrzovana louka)
const BUNKA := 32.0                   # velke bunky: 4x mene objektu a volani kresleni (pady ovladace pri ~7500 volanich)
const KROK := 0.36                    # rozestup trsu (m), plna hustota
const DOSAH := 140.0                  # bunky se nacitaji do teto vzdalenosti (jen stream; za HUST_DO zadny trs)
const HUST_OD := 20.0                 # do 20 m vsechny trsy, k HUST_DO plynule ubyva po jednotlivych trsech
const HUST_DO := 130.0
const KVETY_OD := 12.0
const KVETY_DO := 45.0
## Vrstvy rozsevu (radce 13:20, KCD2: na 1 m2 neni videt puda): 0 trsy (atlas trav), 1 kvety, 2 nizky drn 10-25 cm
## (grass_pack LOLIPOP, 2 karty = 4 troj., hustota DRN_HUST/m2 do 50 m), 3 vysoka trava 60-110 cm na okrajich
## (mez, les, cesta, zed; grass_pack). [od, do] zaniku po trsech podle vzdalenosti.
const VRSTVY := 4
const ZANIK := [[20.0, 130.0], [12.0, 45.0], [12.0, 45.0], [20.0, 110.0]]
const DRN_KROK := 0.35                # ~8 drnu na m2 (0.57 pokryv: zelena zem mezi trsy byla videt; 0,41 = 6/m2)
const ROZSEV := "res://modely/louka/" # offline cast (TVRZ_ROZSEV=1): kryti.bin - zakryti shora po bunkach 32 m
const ZAZNAM := 12                    # bajtu na trs: x u16, z u16, y s16 (cm), (otoceni, sirka, vyska - rezerva), druh u8, hash u8, 0
const VLAKEN := 2                     # soubezne nacitani bunek (WorkerThreadPool)
const KUPY := [                       # kupy travy: [bunka, od, do, meritko min, max, pokryti]
	[64.0, 45.0, 280.0, 1.2, 2.0, 0.85],         # impostor travy od 45 m (radce 07:45, pokryv; drn konci na 45 m)
	[128.0, 240.0, 650.0, 2.6, 4.2, 0.4],
]

var main: Node
var hustota := 1.0
var _mriz: Array = []                 # [{x0, z0, k, nx, nz, ys, ms}]
var _voda_y := -2.75
var _stavby: Array = []               # [Transform3D do mistni soustavy stavby, AABB] - uvnitr bez travy (hostinec, stan)
var _trs: Mesh                        # trs travy = 3 zkrizene karty s obrazkem z atlasu (bunku vybira custom.b)
var _kvety: Array = []
var _sum := FastNoiseLite.new()
var _sum2 := FastNoiseLite.new()
var _bunky := {}                      # Vector2i -> {"uzel", "mm": [MultiMesh trsy, kvety], "hash": [PackedByteArray x2]} / {}
var _ceka := {}                       # Vector2i -> id ulohy ve WorkerThreadPool
var _hotove: Array = []               # vysledky vlaken (pod _zamek)
var _zamek := Mutex.new()
var _ceka_kupy := {}                  # Vector3i(x, z, pasmo) -> id ulohy
var _kr_tab := {}                     # Vector2i -> PackedByteArray 64 x 64 (1 = nad mistem je strecha/stul/skala)
var _kr_nic := PackedByteArray()
var _stan: Image                      # maska stanoviste ze sveta (pesiny)
var _stan_r := Rect2()
var _kupy: Array = [{}, {}]
var _kupa: Mesh
var _drn: Mesh                        # nizky drn (grass_pack, LOLIPOP CC-BY 4.0)
var _kor: RefCounted                  # koryto potoka (svet.koryto), jen cteni ve vlaknech
var _vysoka: Mesh                     # vysoka trava na okrajich (grass_pack)
var _snimek := 0
var _player: Node3D
var _cas := OS.has_environment("TVRZ_LOUKA_CAS")      # mereni: cas stavby kazde bunky


func setup(p_main: Node) -> void:
	main = p_main
	process_mode = Node.PROCESS_MODE_ALWAYS
	_player = main.player
	_kor = main.svet.koryto
	hustota = [0.45, 0.7, 1.0][int(main.quality)]
	for key: String in ["trava_kraj", "trava_ves"]:
		var g: Dictionary = main.svet.data.get(key, {})
		if g.is_empty():
			continue
		_mriz.append({"x0": float(g["x0"]), "z0": float(g["z0"]), "k": float(g["k"]),
				"nx": int(g.get("nx", g.get("n", 0))), "nz": int(g.get("nz", g.get("n", 0))),
				"ys": Marshalls.base64_to_raw(String(g["y"])), "ms": Marshalls.base64_to_raw(String(g["m"]))})
	# staticke stavby s presnou kolizi (hostinec, stan): pudorys mrizka louky nezna -> trava rostla v krbu a u zdi
	for n in main.find_children("Staticky_*", "Node3D", true, false):
		var bb := AABB()
		var prvni := true
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			# do soustavy stavby pres globalni transformace (mezi uzly glb muze byt dalsi transformace)
			var b := ((n as Node3D).global_transform.affine_inverse() * (mi as MeshInstance3D).global_transform) * (mi as MeshInstance3D).get_aabb()
			bb = b if prvni else bb.merge(b)
			prvni = false
		if not prvni and bb.size.x > 4.0 and bb.size.z > 4.0:
			_stavby.append([(n as Node3D).global_transform.affine_inverse(), bb.grow(-0.2)])
	_voda_y = float(main.svet.data.get("voda_y", -2.75))
	_stan = main.svet.stanoviste
	_stan_r = main.svet.stan_rect
	_sum.seed = 1393
	_sum.frequency = 0.045
	_sum2.seed = 77
	_sum2.frequency = 0.16
	_trs = _karta_mesh(3, ATLAS_POMER, 1.0, 0.0, 0.0, 1.0, true)    # blizko: trs vysoky 1 (meritko instance = vyska v m) + karta shora
	_kvety.append(_kvety_atlas([[Color(1.0, 0.85, 0.15), Color(0.9, 0.55, 0.05)], [Color(0.98, 0.98, 0.93), Color(1.0, 0.85, 0.2)],
			[Color(0.95, 0.55, 0.75), Color(0.75, 0.3, 0.45)], [Color(0.6, 0.45, 0.9), Color(0.95, 0.9, 0.5)]]))
	# drn 3,2 x vyska (0,12-0,26 m -> karta 0,4-0,8 m siroka) + karta shora: pri 1,7 kryl jeden drn ~0,1 m2 a mezi
	# nimi byla videt zem (Misa 0.57, 2x zakroužkovano)
	_drn = _karta_mesh(2, 3.2, 1.0, 0.0, 0.0, 0.5, true)
	_atlas_vrstvy(_drn, "res://obrazky/drn_atlas.png", 3, 4, 0.12, 0.26)
	_vysoka = _karta_mesh(3, 1.0, 1.0, 0.0, 0.0, 1.3)
	_atlas_vrstvy(_vysoka, "res://obrazky/trava_vysoka_atlas.png", 3, 2, 0.65, 1.1)
	_nacti_kryti()
	for m: Mesh in [_trs, _kvety[0], _drn, _vysoka]:
		var sm := m.surface_get_material(0) as ShaderMaterial
		sm.set_shader_parameter("z_custom", true)
		sm.set_shader_parameter("hustota", hustota)
	_kupa = _karta_mesh(3, 1.9, 0.6, 0.3, 0.08, 0.25)               # kupa (jako drive hruda o prumeru 2): husty spodek bunky
	# barva terenu pod trsem od use_terrain_color_m (pravidla/pravidla_sveta.json, KCD 80 m): trsy 40-80, drn 20-40,
	# kupy (80-650 m) cele v barve krajiny - stejny zdroj jako dalka terenu
	var zm: ShaderMaterial = main.svet._mats.get("zem")
	for q: Array in [[_trs, 40.0, 80.0], [_vysoka, 40.0, 80.0], [_drn, 20.0, 40.0], [_kupa, 0.0, 1.0]]:
		var sm2 := (q[0] as Mesh).surface_get_material(0) as ShaderMaterial
		if zm == null or sm2 == null:
			continue
		sm2.set_shader_parameter("barva_terenu", true)
		sm2.set_shader_parameter("teren_od", q[1])
		sm2.set_shader_parameter("teren_do", q[2])
		for u: String in ["stanoviste", "stan_rect", "sum", "barva_louky", "barva_lesa"]:
			sm2.set_shader_parameter(u, zm.get_shader_parameter(u))
	print("louka: %d mrizek, hustota %.2f" % [_mriz.size(), hustota])


## (hustota 0..1, vyska) - vetsi z mrizek (ves ma vlastni)
## Okraj lesa: o kolik je hustota louky 6 m od bodu vyssi nez v bode (pas trsu podel krajnich stromu).
## Pocita se na mrizce 4 m pro celou bunku (81 bodu x 5 vzorku), ne pro kazdy trs.
func _okraje(c: Vector2i) -> PackedFloat32Array:
	var o := PackedFloat32Array()
	o.resize(81)
	for j in 9:
		for i in 9:
			var px := c.x * BUNKA + i * 4.0
			var pz := c.y * BUNKA + j * 4.0
			var m := _vzorek(px, pz).x
			var mx := maxf(maxf(_vzorek(px + 6.0, pz).x, _vzorek(px - 6.0, pz).x), maxf(_vzorek(px, pz + 6.0).x, _vzorek(px, pz - 6.0).x))
			o[j * 9 + i] = clampf(mx - m, 0.0, 1.0)
	return o


func _okraj(o: PackedFloat32Array, c: Vector2i, px: float, pz: float) -> float:
	var i := clampi(roundi((px - c.x * BUNKA) / 4.0), 0, 8)
	var j := clampi(roundi((pz - c.y * BUNKA) / 4.0), 0, 8)
	return o[j * 9 + i]


func _vzorek(px: float, pz: float) -> Vector2:
	var best := Vector2(0.0, 0.0)
	var u_zdi := 0.0
	for st: Array in _stavby:
		var q: Vector3 = (st[0] as Transform3D) * Vector3(px, 0.0, pz)
		var b: AABB = st[1]
		# vnitrek stavby resi paprsek shora (_kryti), tady jen pas u zdi
		# u zdi zarostle (kosa tam nedosahne): pas 3 m kolem stavby hustsi
		var dx := maxf(b.position.x - q.x, q.x - b.end.x)
		var dz := maxf(b.position.z - q.z, q.z - b.end.z)
		var d := maxf(dx, dz)
		if d < 2.5:
			u_zdi = maxf(u_zdi, 0.85 * (1.0 - d / 2.5))
	var mam_vysku := false
	for g: Dictionary in _mriz:
		var fx := (px - float(g["x0"])) / float(g["k"])
		var fz := (pz - float(g["z0"])) / float(g["k"])
		var nx: int = g["nx"]
		var i := floori(fx)
		var j := floori(fz)
		if i < 0 or j < 0 or i >= nx - 1 or j >= int(g["nz"]) - 1:
			continue
		fx -= i
		fz -= j
		var a0 := j * nx + i
		var ms: PackedByteArray = g["ms"]
		var ys: PackedByteArray = g["ys"]
		var m := lerpf(lerpf(ms[a0], ms[a0 + 1], fx), lerpf(ms[a0 + nx], ms[a0 + nx + 1], fx), fz) / 255.0
		# vyska z mrizky i tam, kde trava neni (m = 0): jinak 0 m a trs pridany okrajem lesa visel nad udolim
		if m <= best.x and not (best.x == 0.0 and not mam_vysku):
			continue
		mam_vysku = true
		var h0 := ys.decode_s16(a0 * 2)
		var h1 := ys.decode_s16((a0 + 1) * 2)
		var h2 := ys.decode_s16((a0 + nx) * 2)
		var h3 := ys.decode_s16((a0 + nx + 1) * 2)
		best = Vector2(m, lerpf(lerpf(h0, h1, fx), lerpf(h2, h3, fx), fz) / 100.0)
	# pesina (maska stanoviste svet.gd, kanal A): vyslapano, trsy jen na okraji; les a skaly ridi
	if _stan != null and best.x > 0.0:
		var si := clampi(roundi((px - _stan_r.position.x) / 2.0), 0, _stan.get_width() - 1)
		var sj := clampi(roundi((pz - _stan_r.position.y) / 2.0), 0, _stan.get_height() - 1)
		var st := _stan.get_pixel(si, sj)
		# pesina ~1 m (A = 0,5 + znamenkova vzdalenost od osy / 6 m): bilinearne jako zem.gdshader
		var sfx := clampf((px - _stan_r.position.x) / 2.0, 0.0, _stan.get_width() - 1.001)
		var sfz := clampf((pz - _stan_r.position.y) / 2.0, 0.0, _stan.get_height() - 1.001)
		var bi := mini(floori(sfx), _stan.get_width() - 2)
		var bj := mini(floori(sfz), _stan.get_height() - 2)
		var pa := lerpf(lerpf(_stan.get_pixel(bi, bj).a, _stan.get_pixel(bi + 1, bj).a, sfx - bi),
				lerpf(_stan.get_pixel(bi, bj + 1).a, _stan.get_pixel(bi + 1, bj + 1).a, sfx - bi), sfz - bj)
		# tataz vzdalenost od osy jako hlina v zem.gdshader: trava konci tam, kde hlina zacina (radce 20:05 bod 5 -
		# podle hrube masky se ubiralo do 1,5 m, hlina jen do 0,6 m -> holy pruh = "smouhy")
		var lat := absf(pa - 0.5) * 6.0
		if lat < 1.0:
			best.x *= smoothstep(0.5, 0.75, lat)
		# v hustem lese (stin) a v soutesce u skal skoro zadna trava - jehlici, listi, pisek, mech (radce 09:05 A, 07:50)
		# pod korunami (krytí >= 1) trava -90 %, mezi korunami (svetliny) zustava (radce 11:00)
		best.x *= (1.0 - 0.9 * smoothstep(0.6, 1.0, st.r + st.g)) * (1.0 - 0.8 * smoothstep(0.3, 0.7, st.b))
	# u zdi zarostle jen tam, kde uz louka je (dvur a mista u stolu, kde se chodi, zustavaji volna)
	if best.x > 0.02:
		best.x = maxf(best.x, u_zdi)
	# val a breh prikopu kolem tvrze (maska louky ma okoli tvrze vyrizle): za hradbou trava, ve vode ne
	if absf(px + 4.0) < 36.0 and absf(pz) < 32.0 and not (px > -27.6 and px < 18.5 and pz > -16.6 and pz < 17.4):
		if best.y > _voda_y + 0.3 and not (absf(px + 3.0) < 2.0 and pz > 17.0):
			best.x = maxf(best.x, 0.75)
	return best


func _process(_dt: float) -> void:
	if _player == null or _mriz.is_empty() or not main.ready_done:
		return
	var tp := Time.get_ticks_usec()
	_krok()
	if _cas:
		var ms := (Time.get_ticks_usec() - tp) / 1000.0
		if ms > 1.0:
			print("LOUKA snimek %.2f ms" % ms)


func _krok() -> void:
	var p := _player.global_position
	var q := Vector2(p.x, p.z)
	var c0 := Vector2i(floori(p.x / BUNKA), floori(p.z / BUNKA))
	# 1) hotove bunky z vlaken: v hlavnim vlakne jen MultiMesh z hotoveho bufferu (jedna za snimek)
	_zamek.lock()
	var hot: Dictionary = _hotove.pop_front() if not _hotove.is_empty() else {}
	_zamek.unlock()
	if not hot.is_empty() and hot.has("kupy"):
		var kk := Vector3i(hot["c"].x, hot["c"].y, hot["kupy"])
		if _ceka_kupy.has(kk):
			WorkerThreadPool.wait_for_task_completion(_ceka_kupy[kk])
			_ceka_kupy.erase(kk)
			(_kupy[hot["kupy"]] as Dictionary)[hot["c"]] = _kupy_uzel(hot)
	elif not hot.is_empty():
		var c: Vector2i = hot["c"]
		if _ceka.has(c):
			WorkerThreadPool.wait_for_task_completion(_ceka[c])
			_ceka.erase(c)
		var t0 := Time.get_ticks_usec()
		_bunky[c] = _postav(hot)
		_viditelne(c, _bunky[c], q)
		if _cas:
			print("LOUKA nacteni %.2f ms %d trsu" % [(Time.get_ticks_usec() - t0) / 1000.0, int(hot.get("n0", 0))])
	# 2) chybejici bunky do DOSAH (nejblizsi prvni) do vlaken
	if _ceka.size() < VLAKEN:
		var best := Vector2i.ZERO
		var bd := 1e9
		var rd := int(ceil(DOSAH / BUNKA)) + 1
		for dx in range(-rd, rd + 1):
			for dz in range(-rd, rd + 1):
				var c := c0 + Vector2i(dx, dz)
				if _bunky.has(c) or _ceka.has(c):
					continue
				var d := _vzdal_bunky(c, q)
				if d < DOSAH and d < bd:
					bd = d
					best = c
		if bd < 1e9:
			_ceka[best] = WorkerThreadPool.add_task(_nacti.bind(best))
	# 3) kolik trsu kazde bunky kreslit: trsy jsou serazene podle hashe, shader zahodi hash > hustota(vzdalenost),
	# tak se kresli jen prvnich N (bez vrcholu za nic)
	_snimek += 1
	for c: Vector2i in _bunky.keys():
		var b: Dictionary = _bunky[c]
		var d := _vzdal_bunky(c, q)
		if d > DOSAH + BUNKA * 2.0:
			if b.has("uzel"):
				(b["uzel"] as Node).queue_free()
			_bunky.erase(c)
			continue
		if (_snimek + c.x + c.y) % 4 == 0:
			_viditelne(c, b, q)
	# kupy: stridave jedno pasmo za snimek
	for li in ([(_snimek / 3) % KUPY.size()] if _snimek % 3 == 0 else []):
		var KL: Array = KUPY[li]
		var bk: float = KL[0]
		var dosah: float = KL[2]
		var hk: Dictionary = _kupy[li]
		var co := Vector2i(floori(p.x / bk), floori(p.z / bk))
		var ro := int(ceil(dosah / bk)) + 1
		var best := Vector2i(0, 0)
		var bd := 1e9
		for dx in range(-ro, ro + 1):
			for dz in range(-ro, ro + 1):
				var c := co + Vector2i(dx, dz)
				if hk.has(c):
					continue
				var d := Vector2((c.x + 0.5) * bk, (c.y + 0.5) * bk).distance_to(q)
				if d < dosah + bk * 0.75 and d < bd:
					bd = d
					best = c
		if bd < 1e9 and not _ceka_kupy.has(Vector3i(best.x, best.y, li)):
			hk[best] = null                         # rezervace; uzel doplni vysledek vlakna
			_ceka_kupy[Vector3i(best.x, best.y, li)] = WorkerThreadPool.add_task(_kupy_vlakno.bind(best, li))
		for c: Vector2i in hk.keys():
			if Vector2((c.x + 0.5) * bk, (c.y + 0.5) * bk).distance_to(q) > dosah + bk * 2.0:
				var n: Node = hk[c]
				if n:
					n.queue_free()
				hk.erase(c)


## Mereni a snimky: vsechny bunky do DOSAH hned (v hlavnim vlakne), bez cekani na vlakna.
func nacti_okoli() -> void:
	for c: Vector2i in _ceka.keys():
		WorkerThreadPool.wait_for_task_completion(_ceka[c])
	_ceka.clear()
	var p := _player.global_position
	var q := Vector2(p.x, p.z)
	var c0 := Vector2i(floori(p.x / BUNKA), floori(p.z / BUNKA))
	var rd := int(ceil(DOSAH / BUNKA)) + 1
	for dx in range(-rd, rd + 1):
		for dz in range(-rd, rd + 1):
			var c := c0 + Vector2i(dx, dz)
			if not _bunky.has(c) and _vzdal_bunky(c, q) < DOSAH:
				_nacti(c)
	_zamek.lock()
	var zbyle: Array = []
	for hot: Dictionary in _hotove:
		if hot.has("kupy"):
			zbyle.append(hot)            # kupy zpracuje _process
		elif not _bunky.has(hot["c"]):
			_bunky[hot["c"]] = _postav(hot)
			_viditelne(hot["c"], _bunky[hot["c"]], q)
	_hotove = zbyle
	_zamek.unlock()


func _viditelne(c: Vector2i, b: Dictionary, q: Vector2) -> void:
	if not b.has("mm"):
		return
	var d := _vzdal_bunky(c, q)
	for k in VRSTVY:
		var mm: MultiMesh = b["mm"][k]
		if mm:
			var hu := 1.0 - smoothstep(float(ZANIK[k][0]), float(ZANIK[k][1]), d)
			mm.visible_instance_count = _pocet(b["hash"][k], hu * hustota * 1.1)


func _exit_tree() -> void:
	for id: int in _ceka.values() + _ceka_kupy.values():
		WorkerThreadPool.wait_for_task_completion(id)
	_ceka.clear()
	_ceka_kupy.clear()


func _vzdal_bunky(c: Vector2i, q: Vector2) -> float:
	var dx := maxf(maxf(c.x * BUNKA - q.x, q.x - (c.x + 1) * BUNKA), 0.0)
	var dz := maxf(maxf(c.y * BUNKA - q.y, q.y - (c.y + 1) * BUNKA), 0.0)
	return sqrt(dx * dx + dz * dz)


## Pocet trsu s hashem <= h (hashe vzestupne): puleni intervalu.
func _pocet(hs: PackedByteArray, h: float) -> int:
	var lim := int(clampf(h, 0.0, 1.0) * 255.0)
	if hs.is_empty() or lim >= 255:
		return hs.size()
	var lo := 0
	var hi := hs.size()
	while lo < hi:
		var m := (lo + hi) >> 1
		if hs[m] <= lim:
			lo = m + 1
		else:
			hi = m
	return lo


## Vlakno: soubor bunky -> hotove buffery MultiMeshe (transformace + custom), nic ze sceny.
## custom = (druh + hash, poloha paty x, y, z v soustave bunky): shader podle ni zmensuje trs ke pate.
func _nacti(c: Vector2i) -> void:
	var out := {"c": c}
	var t0 := Time.get_ticks_usec()
	var by := _rozsej(c)
	if not by.is_empty():
		var ns: Array[int] = []
		var celk := 0
		for k in VRSTVY:
			ns.append(by.decode_u32(k * 4))
			celk += ns[k]
		var cen := Vector2((c.x + 0.5) * BUNKA, (c.y + 0.5) * BUNKA)
		var o := VRSTVY * 4
		# vyska bunky (uzel): poloha v custom relativne k nemu (custom muze byt v GPU jen 16bitove)
		var y0 := INF
		var y1 := -INF
		for i in celk:
			var y := by.decode_s16(VRSTVY * 4 + i * ZAZNAM + 4) / 100.0
			y0 = minf(y0, y)
			y1 = maxf(y1, y)
		for k in VRSTVY:
			var n := ns[k]
			var buf := PackedFloat32Array()
			buf.resize(n * 16)
			var hs := PackedByteArray()
			hs.resize(n)
			for i in n:
				var j := i * 16
				# transformace instance jednotkova (renderery ji predavaji ruzne): polohu, otoceni a velikost dela shader
				buf[j] = 1.0
				buf[j + 5] = 1.0
				buf[j + 10] = 1.0
				var hh := by[o + 10]
				# vyska navic z bajtu 8 (v * 200, 1.0 = zadna): q = (v - 1) / 0,1 do 3 -> custom.x = druh + 16 q + hash
				var q := clampi(roundi((by[o + 8] / 200.0 - 1.0) / 0.1), 0, 3) if k == 0 else 0
				buf[j + 12] = by[o + 9] + 16 * q + hh / 256.0
				buf[j + 13] = by.decode_u16(o) / 65535.0 * BUNKA - BUNKA * 0.5
				buf[j + 14] = by.decode_s16(o + 4) / 100.0 - y0
				buf[j + 15] = by.decode_u16(o + 2) / 65535.0 * BUNKA - BUNKA * 0.5
				hs[i] = hh
				o += ZAZNAM
			out["buf%d" % k] = buf
			out["hash%d" % k] = hs
			out["n%d" % k] = n
		out["y"] = Vector2(y0, y1)
		out["cen"] = cen
	if _cas:
		print("LOUKA vlakno %.1f ms" % [(Time.get_ticks_usec() - t0) / 1000.0])
	_zamek.lock()
	_hotove.append(out)
	_zamek.unlock()


func _postav(hot: Dictionary) -> Dictionary:
	if not hot.has("cen"):
		return {}
	var cen: Vector2 = hot["cen"]
	var root := Node3D.new()
	root.name = "louka_%d_%d" % [(hot["c"] as Vector2i).x, (hot["c"] as Vector2i).y]
	var yy: Vector2 = hot["y"]
	root.position = Vector3(cen.x, yy.x, cen.y)
	add_child(root)
	yy -= Vector2(yy.x, yy.x)
	# AABB i se zvetsenim trsu v dalce (shader) - jinak orezani pohledu podle transformaci
	var aabb := AABB(Vector3(-BUNKA * 0.5 - 1.5, yy.x - 0.5, -BUNKA * 0.5 - 1.5), Vector3(BUNKA + 3.0, yy.y - yy.x + 2.5, BUNKA + 3.0))
	var mms := []
	mms.resize(VRSTVY)
	var meshe := [_trs, _kvety[0], _drn, _vysoka]
	for k in VRSTVY:
		var n: int = hot.get("n%d" % k, 0)
		if n == 0:
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true
		mm.mesh = meshe[k]
		mm.instance_count = n
		mm.buffer = hot["buf%d" % k]
		mm.visible_instance_count = 0
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.custom_aabb = aabb
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mmi.visibility_range_end = float(ZANIK[k][1]) + 30.0
		root.add_child(mmi)
		mms[k] = mm
	var hs := []
	for k in VRSTVY:
		hs.append(hot.get("hash%d" % k, PackedByteArray()))
	return {"uzel": root, "mm": mms, "hash": hs}


## Offline cast (radce 07:30 A): paprsky shora (fyzika, jen v hlavnim vlakne) pro celou krajinu -> modely/louka/kryti.bin.
## Ulozeny rozsev vsech trsu by mel 132 MB (11,6 M trsu po 12 B); rozsev bunky z masek je cisty vypocet a bezi ve vlakne.
## Spoustet po zmene sveta (stavby, predmety, skaly): TVRZ_ROZSEV=1.
func rozsev_vse() -> void:
	var x0 := INF
	var z0 := INF
	var x1 := -INF
	var z1 := -INF
	for g: Dictionary in _mriz:
		x0 = minf(x0, g["x0"])
		z0 = minf(z0, g["z0"])
		x1 = maxf(x1, float(g["x0"]) + float(g["k"]) * int(g["nx"]))
		z1 = maxf(z1, float(g["z0"]) + float(g["k"]) * int(g["nz"]))
	var t0 := Time.get_ticks_msec()
	var out := PackedByteArray()
	var bunek := 0
	var n := int(BUNKA / KRYTI_K)
	for cz in range(floori(z0 / BUNKA), ceili(z1 / BUNKA)):
		for cx in range(floori(x0 / BUNKA), ceili(x1 / BUNKA)):
			var c := Vector2i(cx, cz)
			var kr := _kryti(c)
			_kryt.erase(c)
			if kr.count(1) == 0:
				continue
			# bitova mapa 64 x 64
			var e := PackedByteArray()
			e.resize(4 + n * n / 8)
			e.encode_s16(0, cx)
			e.encode_s16(2, cz)
			for i in n * n:
				if kr[i] != 0:
					e[4 + (i >> 3)] |= 1 << (i & 7)
			out.append_array(e)
			bunek += 1
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(ROZSEV))
	var f := FileAccess.open(ROZSEV + "kryti.bin", FileAccess.WRITE)
	f.store_buffer(out)
	f.close()
	print("ROZSEV kryti: %d bunek se zakrytim, %.1f kB, %.0f s" % [bunek, out.size() / 1024.0, (Time.get_ticks_msec() - t0) / 1000.0])


func _nacti_kryti() -> void:
	var n := int(BUNKA / KRYTI_K)
	_kr_nic.resize(n * n)
	if not FileAccess.file_exists(ROZSEV + "kryti.bin"):
		push_warning("louka: chybi %skryti.bin (TVRZ_ROZSEV=1) - trava i pod stoly a strechami" % ROZSEV)
		return
	var by := FileAccess.get_file_as_bytes(ROZSEV + "kryti.bin")
	var o := 0
	var sz := 4 + n * n / 8
	while o + sz <= by.size():
		var c := Vector2i(by.decode_s16(o), by.decode_s16(o + 2))
		var kr := PackedByteArray()
		kr.resize(n * n)
		for i in n * n:
			kr[i] = (by[o + 4 + (i >> 3)] >> (i & 7)) & 1
		_kr_tab[c] = kr
		o += sz
	print("louka: kryti %d bunek" % _kr_tab.size())


func _mm(root: Node3D, mesh: Mesh, xfs: Array, cen: Vector3, dos0: float, dos1: float, stin: bool, cust: Array = [], fade := 14.0) -> void:
	if xfs.is_empty():
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = not cust.is_empty()
	mm.mesh = mesh
	mm.instance_count = xfs.size()
	for i in xfs.size():
		var t: Transform3D = xfs[i]
		t.origin -= cen
		mm.set_instance_transform(i, t)
		if not cust.is_empty():
			mm.set_instance_custom_data(i, cust[i])
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.position = cen
	# prolinani dela shader (po trsech, i v rendereru compatibility); viditelnost jen hrube orezava
	var mat := mesh.surface_get_material(0)
	if mat is ShaderMaterial:
		mmi.material_override = _mat_pas(mat, dos0, dos1, fade)
	if dos0 > 0.0:
		mmi.visibility_range_begin = maxf(0.0, dos0 - 20.0)
	mmi.visibility_range_end = dos1 + 30.0 if mat is ShaderMaterial else dos1
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if stin else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mmi)


var _mat_cache := {}


func _mat_pas(mat: Material, od: float, do_: float, fade := 14.0) -> Material:
	var key := "%d_%d_%d_%d" % [mat.get_instance_id(), int(od), int(do_), int(fade)]
	if not _mat_cache.has(key):
		var m := mat.duplicate() as ShaderMaterial
		m.set_shader_parameter("fade_od", od if od > 0.0 else -1.0)
		m.set_shader_parameter("fade_do", do_)
		m.set_shader_parameter("fade_sirka", fade)
		_mat_cache[key] = m
	return _mat_cache[key]


const KRYTI_K := 0.5                  # mrizka paprsku shora (m)


## Paprsky shora (radce 04:55): kde prvni zasah neni teren (strecha, stul, lavice, pavlac, skala, most), tam trava
## neroste - obecne pro vsechny stavby a predmety s kolizi, bez rucnich seznamu. Nejdriv hrube po 2 m, kolem zasahu
## jemne po 0,5 m (cela mrizka 0,5 m stala 48 ms na bunku). Vysledek sdili blizke i stredni pasmo bunky.
var _kryt := {}                       # Vector2i -> PackedByteArray


func _kryti(c: Vector2i) -> PackedByteArray:
	if _kryt.has(c):
		return _kryt[c]
	var n := int(BUNKA / KRYTI_K)
	var out := PackedByteArray()
	out.resize(n * n)
	var space := get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.new()
	q.exclude = [(_player as CollisionObject3D).get_rid()] if _player is CollisionObject3D else []
	var t0 := Time.get_ticks_usec()
	var paprsku := 0
	var hrube := int(BUNKA / 2.0)
	for hj in hrube:
		for hi in hrube:
			paprsku += 1
			if not _zasah(space, q, c.x * BUNKA + hi * 2.0 + 1.0, c.y * BUNKA + hj * 2.0 + 1.0):
				continue
			# jemne: okoli 6 x 6 m kolem hrubeho bodu (stul i lavice vedle nej)
			for j in range(maxi(0, (hj - 1) * 4), mini(n, (hj + 2) * 4)):
				for i in range(maxi(0, (hi - 1) * 4), mini(n, (hi + 2) * 4)):
					if out[j * n + i] != 0:
						continue
					paprsku += 1
					if _zasah(space, q, c.x * BUNKA + (i + 0.5) * KRYTI_K, c.y * BUNKA + (j + 0.5) * KRYTI_K):
						out[j * n + i] = 1
					else:
						out[j * n + i] = 2      # overeno volne
	for k in out.size():
		if out[k] == 2:
			out[k] = 0
	if _cas:
		print("LOUKA kryti %.1f ms %d" % [(Time.get_ticks_usec() - t0) / 1000.0, paprsku])
	_kryt[c] = out
	return out


func _zasah(space: PhysicsDirectSpaceState3D, q: PhysicsRayQueryParameters3D, px: float, pz: float) -> bool:
	var y := _vzorek(px, pz).y
	q.from = Vector3(px, y + 9.0, pz)
	q.to = Vector3(px, y - 2.0, pz)
	var h := space.intersect_ray(q)
	if h.is_empty():
		return true                          # pod mrizkou nic (okraj, diry): trs by visel
	var nm := String((h["collider"] as Node).name)
	if nm.begins_with("Teren") or nm.begins_with("Nadvori"):
		# teren o 0,5 m niz nez mrizka 2 m (hrana skaly, prevys, zarez): trs by levitoval (Misa 0.56b ve skalach);
		# mensi rozdil na svahu je bezny (mrizka vs. trojuhelniky) a trs ho skryje
		return (h["position"] as Vector3).y < y - 0.5
	return true


func _kryto(k: PackedByteArray, c: Vector2i, px: float, pz: float) -> bool:
	var n := int(BUNKA / KRYTI_K)
	var i := clampi(floori((px - c.x * BUNKA) / KRYTI_K), 0, n - 1)
	var j := clampi(floori((pz - c.y * BUNKA) / KRYTI_K), 0, n - 1)
	return k[j * n + i] != 0


## Zarez potoka (hlaseni 0.54, 16:50: vysoka trava po celem zarezu): 1 na svahu zarezu a tesne za hranou, 0 jinde
## a na jesepu/u vody. Ve vlakne jen cte koryto (po stavbe sveta se nemeni).
func _zarez(px: float, pz: float, y: float) -> float:
	var kor = _kor
	if kor == null or not kor._mriz.has(Vector2i(floori(px / 16.0), floori(pz / 16.0))):
		return 0.0
	var b: Array = kor.blizko(px, pz)
	if b.is_empty() or float(b[0]) < float(b[2]) + 1.0 + 4.0 * maxf(float(b[3]), 0.0):
		return 0.0
	return 1.0 - smoothstep(0.5, 1.4, kor.strop(px, pz, false) - y)


## Rozsev jedne bunky (plna hustota, deterministicky podle bunky): trsy, byliny a kvety -> zaznamy serazene podle hashe.
func _rozsej(c: Vector2i) -> PackedByteArray:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(c) ^ 0x5eed
	var zaz: Array = [[], [], [], []]   # [[hash, PackedByteArray zaznam]] trsy, kvety, drn, vysoka
	var okr := _okraje(c)
	var kr: PackedByteArray = main.svet.kryti_tab.get(c, _kr_nic)     # tentyz zaklad jako svet.smi_tu_byt
	var x := 0.0
	while x < BUNKA:
		var z := 0.0
		while z < BUNKA:
			var px := c.x * BUNKA + x + rng.randf_range(-0.45, 0.45) * KROK
			var pz := c.y * BUNKA + z + rng.randf_range(-0.45, 0.45) * KROK
			z += KROK
			var v := _vzorek(px, pz)
			if v.x > 0.02:                                             # hustsi pas na okraji lesa (ne v korytu, prikopu, stavbe)
				v.x = minf(v.x + 0.5 * _okraj(okr, c, px, pz), 1.0)
			# neudrzovana louka (radce 07:45, Misa: "kde nechodi clovek, zarostle az beda"): x1,5 trsu, x1,3 vyska
			var div := Svet.divokost(px, pz)
			if v.x < 0.1 or rng.randf() > v.x * 1.6 * (1.0 + 0.5 * div) or _kryto(kr, c, px, pz):
				continue
			var n1 := _sum.get_noise_2d(px, pz) * 0.5 + 0.5
			var n2 := _sum2.get_noise_2d(px, pz) * 0.5 + 0.5
			var typ := 0 if n1 < 0.45 else (1 if n1 < 0.72 else 2)
			if n2 > 0.72:
				typ = 3
			if v.x < 0.45:
				typ = 2 if rng.randf() < 0.5 else 1          # lem cest a okraje: vyssi trava
			elif rng.randf() < 0.25:
				typ = rng.randi() % 3
			var s := rng.randf_range(0.75, 1.25) * lerpf(0.85, 1.15, v.x)
			# karta z atlasu podle druhu (bunka, vyska karty v m); nizka/stredni/vysoka/sucha = jedna sit, rozdil dela
			# bunka atlasu a meritko; barvu (suchost, odstin) odvodi shader z hashe
			# druh = bunka atlasu + vyska (tabulka v stebla.gdshader): 0 nizka 0,36 m, 1 nizka 0,5, 2 stredni 0,6,
			# 3 vysoka 0,82, 4 sucha 0,6 (karta je ridsi nez stebla: o 20 % vyssi, aby zakryla zem)
			var druh := 0
			if typ == 1:
				druh = 1 if rng.randf() < 0.5 else 2
			elif typ == 2:
				druh = 3
			elif typ == 3:
				druh = 4
			# velikost dela shader z hashe; v zaznamu jen vyska navic neudrzovane louky (x1,3)
			_zaznam(zaz[0], c, px, v.y - 0.04, pz, rng.randf(), s, 1.0 + 0.3 * div, druh, rng.randi() % 256)
			if rng.randf() < 0.22:
				# byliny mezi travou: jitrocel, drobne kvety, na okrajich (u lesa a cest) kapradi
				# 5 jitrocel 0,28 m, 6 kapradi 0,55, 7 drobne kvety 0,32
				var bb := 5
				var r2 := rng.randf()
				if v.x < 0.45 and r2 < 0.3:
					bb = 6
				elif r2 < 0.18:
					bb = 7
				_zaznam(zaz[0], c, px + rng.randf_range(-0.2, 0.2), v.y - 0.03, pz + rng.randf_range(-0.2, 0.2), rng.randf(),
						1.0, 1.0, bb, rng.randi() % 256)
		x += KROK
	# kvety ve skupinkach (na louce, ne v lese ani na cestach)
	# kvety vypnute (Misa 19:45, pravidla_sveta.json kvety hustota 0), dokud nebudou fotograficke
	var nsk := 0 * rng.randi_range(0, 3) * int(BUNKA * BUNKA / 256.0)   # skupinky kvetu na 16x16 m
	for _i in nsk:
		var cx := c.x * BUNKA + rng.randf() * BUNKA
		var cz := c.y * BUNKA + rng.randf() * BUNKA
		if _vzorek(cx, cz).x < 0.55:
			continue
		var mi := rng.randi() % 4
		var rr := rng.randf_range(0.8, 2.2)
		for _j in rng.randi_range(14, 40):
			var aa := rng.randf() * TAU
			var dd := sqrt(rng.randf()) * rr
			var px := cx + cos(aa) * dd
			var pz := cz + sin(aa) * dd
			var vv := _vzorek(px, pz)
			if _kryto(kr, c, px, pz) or px < c.x * BUNKA or pz < c.y * BUNKA or px >= (c.x + 1) * BUNKA or pz >= (c.y + 1) * BUNKA:
				continue
			var sk := rng.randf_range(1.1, 1.9)
			_zaznam(zaz[1], c, px, vv.y - 0.03, pz, rng.randf(), sk, sk, mi, rng.randi() % 256)
	# nizky drn: husta mrizka, zakryje teren mezi trsy (radce 13:20 a)
	var x2 := 0.0
	while x2 < BUNKA:
		var z2 := 0.0
		while z2 < BUNKA:
			var px := c.x * BUNKA + x2 + rng.randf_range(-0.5, 0.5) * DRN_KROK
			var pz := c.y * BUNKA + z2 + rng.randf_range(-0.5, 0.5) * DRN_KROK
			z2 += DRN_KROK
			var v := _vzorek(px, pz)
			# drn je vyplnovy druh (pravidla_sveta.json vyplnovy_druh, pokryv 0,25 m2 x 6/m2 = 1,5): vsude, kde smi
			# trava byt, bez nahodneho vynechani - jinak mezery ("upravena zahrada", Misa 0.56b)
			if v.x < 0.1 or _kryto(kr, c, px, pz):
				continue
			_zaznam(zaz[2], c, px, v.y - 0.02, pz, 0.0, 1.0, 1.0, rng.randi() % 12, rng.randi() % 256)
			# vysoka trava (b): okraje - les, cesta, zed (okraj > 0 nebo louka < 0,5), ridce; v neudrzovane louce vsude
			var okr2 := maxf(maxf(_okraj(okr, c, px, pz), _zarez(px, pz, v.y)), 0.6 * Svet.divokost(px, pz))
			if okr2 > 0.1 and rng.randf() < 0.2 * okr2:                # 0,3 pri 4 drnech/m2 -> stejne vysoke travy na m2
				_zaznam(zaz[3], c, px, v.y - 0.04, pz, 0.0, 1.0, 1.0, [0, 2, 3, 5][rng.randi() % 4], rng.randi() % 256)
		x2 += DRN_KROK
	var prazdne := true
	for k in VRSTVY:
		if not (zaz[k] as Array).is_empty():
			prazdne = false
	if prazdne:
		return PackedByteArray()
	var out := PackedByteArray()
	out.resize(VRSTVY * 4)
	for k in VRSTVY:
		out.encode_u32(k * 4, (zaz[k] as Array).size())
	for k in VRSTVY:
		(zaz[k] as Array).sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
		for e: Array in zaz[k]:
			out.append_array(e[1])
	return out


func _zaznam(lst: Array, c: Vector2i, px: float, py: float, pz: float, rot: float, w: float, v: float, druh: int, hs: int) -> void:
	var e := PackedByteArray()
	e.resize(ZAZNAM)
	e.encode_u16(0, clampi(roundi((px - c.x * BUNKA) / BUNKA * 65535.0), 0, 65535))
	e.encode_u16(2, clampi(roundi((pz - c.y * BUNKA) / BUNKA * 65535.0), 0, 65535))
	e.encode_s16(4, clampi(roundi(py * 100.0), -32768, 32767))
	e[6] = int(rot * 256.0) % 256
	e[7] = clampi(roundi(w * 200.0), 1, 255)
	e[8] = clampi(roundi(v * 200.0), 1, 255)
	e[9] = druh
	e[10] = hs
	lst.append([hs, e])


## Vlakno: kupy bunky (jen vypocet), uzel postavi hlavni vlakno (_kupy_uzel).
func _kupy_vlakno(c: Vector2i, li: int) -> void:
	var L: Array = KUPY[li]
	# kupy travy (siroke nizke karty z husteho spodku bunky atlasu): souvisla zelena hmota nad zemi i daleko
	var bk: float = L[0]
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(c) ^ (0x0b20 + int(bk))
	var cen := Vector3((c.x + 0.5) * bk, 0.0, (c.y + 0.5) * bk)
	var xfs: Array = []
	var cust: Array = []
	var s0: float = L[3]
	var s1: float = L[4]
	var pl := PI * pow((s0 + s1) * 0.5, 2.0)        # plocha jedne kupy
	var n := int(bk * bk / pl * float(L[5]) * 1.3 * lerpf(0.6, 1.0, hustota))
	for _i in n:
		var px := c.x * bk + rng.randf() * bk
		var pz := c.y * bk + rng.randf() * bk
		var v := _vzorek(px, pz)
		if v.x < 0.12 or rng.randf() > v.x * 1.3:
			continue
		var n1 := _sum.get_noise_2d(px, pz) * 0.5 + 0.5
		var s := rng.randf_range(s0, s1) * lerpf(0.8, 1.2, n1)
		xfs.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.7, 1.1) * lerpf(0.9, 1.25, v.x), s)),
				Vector3(px, v.y - 0.08 * s, pz)))
		# nizka trava, misty sucha (stejne skvrny jako blizko)
		var bun := 2 if _sum2.get_noise_2d(px, pz) * 0.5 + 0.5 > 0.72 else (0 if rng.randf() < 0.7 else 1)
		cust.append(Color(rng.randf() * 0.15, rng.randf(), (bun + 0.5) / 6.0, 1.0))
	_zamek.lock()
	_hotove.append({"c": c, "kupy": li, "xfs": xfs, "cust": cust, "cen": cen})
	_zamek.unlock()


func _kupy_uzel(hot: Dictionary) -> Node3D:
	if (hot["xfs"] as Array).is_empty():
		return null
	var L: Array = KUPY[hot["kupy"]]
	var root := Node3D.new()
	root.name = "kupy_mala" if float(L[0]) < 100.0 else "kupy_velka"
	add_child(root)
	_mm(root, _kupa, hot["xfs"], hot["cen"], float(L[1]), float(L[2]), false, hot["cust"])
	return root


## Vsechny kvety v jednom MultiMeshi (rozpocet kresleni): atlas 4 barev vedle sebe, barvu vybira INSTANCE_CUSTOM.r.
func _kvety_atlas(barvy: Array) -> Mesh:
	var atlas := Image.create(512, 128, false, Image.FORMAT_RGBA8)
	for i in barvy.size():
		var im := _kvet_img(barvy[i][0], barvy[i][1], i * 31 + 5)
		atlas.blit_rect(im, Rect2i(0, 0, 128, 128), Vector2i(i * 128, 0))
	atlas.generate_mipmaps()
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://shaders/kvety.gdshader")
	mat.set_shader_parameter("atlas", ImageTexture.create_from_image(atlas))
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for q in 2:
		var ang := PI * q / 2.0 + 0.3
		var tg := Vector3(cos(ang), 0, sin(ang)) * 0.22
		var up := Vector3(0, 0.42, 0)
		var pts := [-tg, tg, tg + up, -tg + up]
		var uvs := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]
		for i: int in [0, 1, 2, 0, 2, 3]:
			st.set_uv(uvs[i])
			st.set_normal(Vector3.UP)
			st.add_vertex(pts[i])
	var mesh := st.commit()
	mesh.surface_set_material(0, mat)
	return mesh


func _kvet_img(barva: Color, stred: Color, seed: int) -> Image:
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var r := RandomNumberGenerator.new()
	r.seed = seed
	var zelena := Color(0.25, 0.42, 0.13)
	for k in 9:
		var bx := r.randf_range(12, n - 12)
		var top := r.randf_range(8, n * 0.55)
		# stonek
		for y in range(int(top), n):
			var x := bx + sin(y * 0.05 + k) * 2.0
			for dx in range(-1, 2):
				img.set_pixel(clampi(int(x) + dx, 0, n - 1), y, zelena * (0.8 + 0.2 * r.randf()))
		# lisky
		for q in 3:
			var ly := r.randf_range(top + 15, n - 4)
			for t in 10:
				var lx := bx + (t if q % 2 == 0 else -t)
				img.set_pixel(clampi(int(lx), 0, n - 1), clampi(int(ly - t * 0.5), 0, n - 1), zelena)
		# kvet: kolecko okvetnich listku a stred
		var rad := r.randf_range(4.0, 7.0)
		for y in range(-8, 9):
			for x in range(-8, 9):
				var d := Vector2(x, y).length()
				if d < rad:
					var c := stred if d < rad * 0.35 else barva * r.randf_range(0.85, 1.1)
					c.a = 1.0
					img.set_pixel(clampi(int(bx) + x, 0, n - 1), clampi(int(top) + y, 0, n - 1), c)
	return img


# ------------------------------------------------------------------ trsy travy z karet (atlas)


const ATLAS_POMER := 341.0 / 256.0      # sirka : vyska bunky atlasu obrazky/trava_atlas.png (3x2 bunky, 1024x512)


## Vrstva z jineho atlasu (grass_pack): bunku vybira druh, vyska nahodne mezi h0 a h1 (stebla.gdshader rezim 1).
func _atlas_vrstvy(m: Mesh, atlas: String, sl: int, rd: int, h0: float, h1: float) -> void:
	var sm := (m.surface_get_material(0) as ShaderMaterial).duplicate() as ShaderMaterial
	sm.set_shader_parameter("atlas", load(atlas))
	sm.set_shader_parameter("rezim", 1)
	sm.set_shader_parameter("sloupce", float(sl))
	sm.set_shader_parameter("radky", float(rd))
	sm.set_shader_parameter("vyska_od", h0)
	sm.set_shader_parameter("vyska_do", h1)
	sm.set_shader_parameter("prah", 0.4)
	m.surface_set_material(0, sm)


## Trs = n zkrizenych svislych karet (n = 3: 6 troj., obe strany: cull_disabled v shaderu), sirka x vyska v jednotkach
## meritka instance. UV v ramci bunky (v = 0 nahore); bunku atlasu vybira INSTANCE_CUSTOM.b.
## orez = kolik shora bunky vynechat (kupy berou jen husty spodek), ponor = o kolik karta zasahuje pod zem.
func _karta_mesh(n: int, sirka: float, vyska: float, orez: float, ponor: float, vitr: float, shora := false) -> Mesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hw := 0.5 * sirka
	# karty se nekrizi v jednom bode a lisi se vyskou a zrcadlenim: shora neni videt hvezdice, zboku opakovani
	var posun := [Vector3(0.0, 0, 0.0), Vector3(0.09, 0, -0.06), Vector3(-0.07, 0, 0.08), Vector3(0.05, 0, 0.1)]
	var vysky := [1.0, 0.86, 0.93, 0.8]
	for q in n:
		var ang := PI * q / n + 0.35
		var tg := Vector3(cos(ang), 0, sin(ang)) * hw
		var nrm := Vector3(-sin(ang), 0, cos(ang))
		var stred: Vector3 = posun[q % 4] * sirka
		var up := Vector3(0, vyska * float(vysky[q % 4]), 0)
		var dole := Vector3(0, -ponor, 0)
		var pts := [stred - tg + dole, stred + tg + dole, stred + tg + up, stred - tg + up]
		var u0 := 1.0 if q == 1 else 0.0
		var uvs := [Vector2(u0, 1), Vector2(1.0 - u0, 1), Vector2(1.0 - u0, orez), Vector2(u0, orez)]
		for i: int in [0, 1, 2, 0, 2, 3]:
			st.set_uv(uvs[i])
			st.set_normal(nrm)
			st.add_vertex(pts[i])
	if shora:
		# karta skloněná 30 deg od vodorovne (radce 11:20): shora vyplni plochu trsu (jinak jen kriz tri hran),
		# z boku se ztrati; husty spodek bunky atlasu (v 0,35-1)
		var L := sirka * 0.9
		var tg := Vector3(cos(1.2), 0, sin(1.2)) * hw
		var sm := Vector3(-sin(1.2), 0, cos(1.2))
		var a0 := -sm * L * 0.5 + Vector3(0, 0.03, 0)
		var a1 := sm * L * 0.5 + Vector3(0, 0.03 + L * 0.577, 0)
		var nrm := Vector3(0, 0.866, 0) - sm * 0.5
		var pts := [a0 - tg, a0 + tg, a1 + tg, a1 - tg]
		var uvs := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0.35), Vector2(0, 0.35)]
		for i: int in [0, 1, 2, 0, 2, 3]:
			st.set_uv(uvs[i])
			st.set_normal(nrm)
			st.add_vertex(pts[i])
	var mesh := st.commit()
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://shaders/stebla.gdshader")
	mat.set_shader_parameter("atlas", preload("res://obrazky/trava_atlas.png"))
	mat.set_shader_parameter("vitr", vitr)
	mesh.surface_set_material(0, mat)
	return mesh


# ------------------------------------------------------------------ stavba
