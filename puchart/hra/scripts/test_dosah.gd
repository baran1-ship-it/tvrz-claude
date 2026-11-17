extends Node
## Mřížka dosažitelnosti (test průchodu „dosah“, plán 17. 11. B1). Postup jako sonda --reach v Alchemists of Prague
## (github.com/msveshnikov/alchemists-of-prague; kód nepřevzat, licence neuvedena): od startu hráče a míst mapy (brána
## vsi, hrady, krčma, hájovna – mapa_body.json) se po mřížce buněk „rozlévá“ chůze hráče a hledá se, kam se nedostane,
## kde uvízne a kudy uteče. Naše trasy (pruchody.json) najdou chybu jen tam, kudy vedou; mřížka i mimo ně.
## - buňky jen s terénem (krok_venku_m): přechod podle sklonu terénu (floor_max_angle hráče) nebo schodu (hrac.json schod_m)
## - buňky u kolizí mimo terén (stavby, skály, mosty, kmeny): jemnější mřížka, patra paprskem shora (pochozí normála,
##   kapsle hráče se vejde), přechod kráčí kapsle hráče (test_move: rovně, po svahu, krok nahoru s dosednutím, dopad)
## - dveře z dat: uzel navíc ve středu křídla, spojený chůzí s buňkami do dvere_r_m (mřížka 1 m dveře snadno mine)
## CHYBA: díra (dopad bez kolize pod sebou), únik ze světa (hráč na dosažitelném okraji výseku dojde ven / propadne).
## Výpis: uvíznutí (dosažitelné, zpět ke startu nevede cesta), ostrovy pochozích míst mimo dosah, dveře bez dosahu.
## Pravidla hra/data/kontroly_hra.json dosah; výsledek PUCHART_DOSAH (json) + obrázek mapy (.png vedle).
const Mapa := preload("res://scripts/mapa.gd")
const Pravidla := preload("res://scripts/pravidla.gd")
const DOSAZENO := 1
const NAVRAT := 2
const OKRAJ := 4

var hl: Node
var hrac: CharacterBody3D
var cfg: Dictionary
var space: PhysicsDirectSpaceState3D
var kf: float; var dl: int; var kb: float
var x0: float; var z0: float; var x1: float; var z1: float
var NFX: int; var NFZ: int; var NBX: int; var NBZ: int; var NB: int
var slozite := PackedByteArray()      # základní buňka s kolizí mimo terén
var vrch := PackedFloat32Array()      # nejvyšší kolize nad základní buňkou
var hb := PackedFloat32Array()        # výška terénu v uzlu terénu (roh základní buňky)
var sl_id := {}                       # jemný index -> sloupec (jen sloupce s patry)
var sl_fi := PackedInt32Array()       # sloupec -> jemný index
var sl_off := PackedInt32Array()      # sloupec -> první uzel (id − NB)
var sl_n := PackedInt32Array()        # sloupec -> počet pater
var uy := PackedFloat32Array()        # uzel stavby -> výška podlahy
var usl := PackedInt32Array()         # uzel stavby -> sloupec
var NU := 0                           # uzlů staveb
var dvere: Array = []                 # [{jm, p: Vector3}] – uzly id NB + NU + i
var dv_bliz: Dictionary = {}          # uzel -> [indexy dveří]
var stav := PackedByteArray()
var rev: Dictionary = {}              # cíl -> [zdroje] (hrany přes stavby a dveře; terén se počítá znovu)
var diry: Array = []
var okraj: Array = []
var cos_max: float; var tan_max: float; var schody: Array; var schod_max: float
var _col := KinematicCollision3D.new()
var _q := PhysicsRayQueryParameters3D.new()
var _sq := PhysicsShapeQueryParameters3D.new()
var _tvar_y := 0.875
var chuzi := 0

func spust(h: Node, p: CharacterBody3D) -> Dictionary:
	hl = h; hrac = p
	var t0 := Time.get_ticks_msec()
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/kontroly_hra.json"))["dosah"]
	space = hrac.get_world_3d().direct_space_state
	cos_max = cos(hrac.floor_max_angle); tan_max = tan(hrac.floor_max_angle)
	schody = Pravidla.cti("hrac", "schod_m"); schod_max = 0.0
	for s in schody: schod_max = maxf(schod_max, float(s))
	var cs: CollisionShape3D = null
	for c in hrac.get_children():
		if c is CollisionShape3D: cs = c; break
	_tvar_y = cs.position.y
	_sq.shape = cs.shape; _sq.exclude = [hrac.get_rid()]; _sq.collision_mask = hrac.collision_mask
	_q.exclude = [hrac.get_rid()]; _q.collision_mask = hrac.collision_mask
	kb = float(cfg["krok_venku_m"]); dl = int(cfg["jemne_deleni"]); kf = kb / dl
	var vi: Dictionary = hl.svet.vinfo
	x0 = float(vi["x0_hra"]); z0 = float(vi["z0_hra"]); x1 = x0 + float(vi["sirka"]) - 1.0; z1 = z0 + float(vi["vyska"]) - 1.0
	NFX = int((x1 - x0) / kf) + 1; NFZ = int((z1 - z0) / kf) + 1
	NBX = ceili(float(NFX) / dl); NBZ = ceili(float(NFZ) / dl); NB = NBX * NBZ
	# kolize terénu celého výseku (jinak jen 180 m kolem hráče – svet.gd)
	var kdo: float = hl.svet.kolize_do_m
	hl.svet.kolize_do_m = 1.0e7
	for i in 80: hl.svet._kolize_okoli(hrac.global_position)
	hrac.set_physics_process(false)
	await get_tree().physics_frame; await get_tree().physics_frame
	var vysl := {}
	_rastr()
	var t1 := Time.get_ticks_msec()
	_sloupce()
	var t2 := Time.get_ticks_msec()
	_dvere()
	stav.resize(NB + NU + dvere.size())
	var starty := _starty()
	print("DOSAH mřížka %d × %d (%.1f m, u staveb %.1f m), základních buněk se stavbou %d, uzlů staveb %d, dveří %d, startů %d; příprava %d + %d ms" % [NBX, NBZ, kb, kf, slozite.count(1), NU, dvere.size(), starty.size(), t1 - t0, t2 - t1])
	_dopredu(starty)
	var t3 := Time.get_ticks_msec()
	_zpet(starty)
	var t4 := Time.get_ticks_msec()
	var dos := 0; var nav := 0
	for i in stav.size():
		if stav[i] & DOSAZENO: dos += 1
		if stav[i] & NAVRAT: nav += 1
	print("DOSAH dosaženo %d uzlů, zpět ke startu %d; chůzí kapslí %d; dopředu %d ms, zpět %d ms" % [dos, nav, chuzi, t3 - t2, t4 - t3])
	var uviz := _shluky(func(i: int) -> bool: return (stav[i] & DOSAZENO) != 0 and (stav[i] & NAVRAT) == 0)
	var ostr := _shluky(func(i: int) -> bool: return (stav[i] & DOSAZENO) == 0 and i < NB + NU and (i >= NB or slozite[i] == 0))
	ostr = ostr.filter(func(s: Dictionary) -> bool: return int(s["uzlu"]) >= int(cfg["ostrov_min_uzlu"]))
	var dv_bez: Array = []
	for i in dvere.size():
		if (stav[NB + NU + i] & DOSAZENO) == 0: dv_bez.append({"dvere": dvere[i]["jm"], "x": snappedf(dvere[i]["p"].x, 0.1), "z": snappedf(dvere[i]["p"].z, 0.1), "y": snappedf(dvere[i]["p"].y, 0.1)})
	var t5 := Time.get_ticks_msec()
	var unik: Array = await _unik()
	hl.svet.kolize_do_m = kdo
	hrac.set_physics_process(true)
	var t6 := Time.get_ticks_msec()
	var m: Dictionary = cfg["meze"]
	var chyby: Array = []
	if diry.size() > int(m["diry_max"]): chyby.append("díry %d: %s" % [diry.size(), _kde(diry)])
	if unik.size() > int(m["unik_max"]): chyby.append("únik ze světa %d: %s" % [unik.size(), _kde(unik)])
	var n_uv := 0
	for s in uviz: n_uv += int(s["uzlu"])
	if m.get("uviznuti_max_uzlu") != null and n_uv > int(m["uviznuti_max_uzlu"]): chyby.append("uvíznutí %d uzlů > %d" % [n_uv, int(m["uviznuti_max_uzlu"])])
	if m.get("dvere_bez_dosahu_max") != null and dv_bez.size() > int(m["dvere_bez_dosahu_max"]): chyby.append("dveří bez dosahu %d > %d" % [dv_bez.size(), int(m["dvere_bez_dosahu_max"])])
	var vm := int(cfg["vypis_max"])
	vysl = {"popis": "mřížka dosažitelnosti (hra/scripts/test_dosah.gd, kontroly_hra.json dosah)", "mrizka": [NBX, NBZ, kb, kf],
		"uzlu_teren": NB - slozite.count(1), "uzlu_stavby": NU, "dveri": dvere.size(), "dosazeno": dos, "navrat": nav, "chuzi": chuzi,
		"starty": starty.map(func(i: int) -> Array: var q := _poz(i); return [snappedf(q.x, 0.1), snappedf(q.z, 0.1), snappedf(q.y, 0.1)]),
		"diry": diry.slice(0, vm), "diry_pocet": diry.size(), "unik": unik, "okraj_dosazeny": okraj.size(),
		"uviznuti_uzlu": n_uv, "uviznuti": uviz.slice(0, vm), "ostrovy_pocet": ostr.size(), "ostrovy": ostr.slice(0, vm), "dvere_bez_dosahu": dv_bez,
		"cas_ms": {"rastr": t1 - t0, "sloupce": t2 - t1, "dopredu": t3 - t2, "zpet": t4 - t3, "shluky": t5 - t4, "unik": t6 - t5, "celkem": t6 - t0},
		"chyby": chyby}
	var cesta := OS.get_environment("PUCHART_DOSAH") if OS.has_environment("PUCHART_DOSAH") else "user://dosah.json"
	var f := FileAccess.open(cesta, FileAccess.WRITE)
	if f: f.store_string(JSON.stringify(vysl, " ")); f.close()
	_obrazek(cesta.get_basename() + ".png", uviz, ostr, dv_bez, unik)
	if (t6 - t0) / 1000.0 > float(cfg["cas_max_s"]): chyby.append("běh %.0f s > %d s" % [(t6 - t0) / 1000.0, int(cfg["cas_max_s"])])
	vysl["chyby"] = chyby
	print("DOSAH uvíznutí %d uzlů v %d shlucích, ostrovů %d, dveří bez dosahu %d/%d, děr %d, únik %d (okraj dosažen v %d uzlech), %.0f s" % [n_uv, uviz.size(), ostr.size(), dv_bez.size(), dvere.size(), diry.size(), unik.size(), okraj.size(), (t6 - t0) / 1000.0])
	for s in uviz.slice(0, 8): print("DOSAH uvíznutí ", s)
	for s in ostr.slice(0, 8): print("DOSAH ostrov ", s)
	for s in dv_bez.slice(0, 12): print("DOSAH dveře bez dosahu ", s)
	return vysl

func _kde(a: Array) -> String:
	return ", ".join(a.slice(0, 6).map(func(e: Dictionary) -> String: return "[%.1f, %.1f]" % [float(e["x"]), float(e["z"])]))

## buňky s kolizí mimo terén (každý trojúhelník / tvar zvlášť, rozšířeno o okraj_kolize_m)
func _rastr() -> void:
	slozite.resize(NB); vrch.resize(NB); vrch.fill(-INF); hb.resize(NB)
	for bz in NBZ:
		for bx in NBX:
			hb[bz * NBX + bx] = hl.svet.vyska(x0 + bx * kb, z0 + bz * kb)
	var ok := float(cfg["okraj_kolize_m"])
	for c in hl.find_children("*", "CollisionShape3D", true, false):
		var cs := c as CollisionShape3D
		if cs.disabled or cs.shape == null: continue
		var par := cs.get_parent()
		if not (par is PhysicsBody3D) or par == hrac or hl.svet.is_ancestor_of(cs): continue
		if ((par as CollisionObject3D).collision_layer & hrac.collision_mask) == 0: continue
		var xf := cs.global_transform
		if cs.shape is ConcavePolygonShape3D:
			var fc: PackedVector3Array = (cs.shape as ConcavePolygonShape3D).get_faces()
			for i in range(0, fc.size(), 3):
				var a := xf * fc[i]; var b := xf * fc[i + 1]; var d := xf * fc[i + 2]
				_oznac(minf(a.x, minf(b.x, d.x)) - ok, minf(a.z, minf(b.z, d.z)) - ok, maxf(a.x, maxf(b.x, d.x)) + ok, maxf(a.z, maxf(b.z, d.z)) + ok, maxf(a.y, maxf(b.y, d.y)))
		else:
			var bb := xf * cs.shape.get_debug_mesh().get_aabb()
			_oznac(bb.position.x - ok, bb.position.z - ok, bb.end.x + ok, bb.end.z + ok, bb.end.y)

func _oznac(ax: float, az: float, bx_: float, bz_: float, y: float) -> void:
	# základní buňka bx pokrývá jemné body bx*dl … bx*dl+dl−1, tj. x od x0 + bx*kb do x0 + bx*kb + (dl−1)*kf
	var i0 := maxi(0, floori((ax - x0 - (dl - 1) * kf) / kb) ); var i1 := mini(NBX - 1, floori((bx_ - x0) / kb))
	var j0 := maxi(0, floori((az - z0 - (dl - 1) * kf) / kb)); var j1 := mini(NBZ - 1, floori((bz_ - z0) / kb))
	for j in range(j0, j1 + 1):
		for i in range(i0, i1 + 1):
			var b := j * NBX + i
			slozite[b] = 1; vrch[b] = maxf(vrch[b], y)

## patra ve sloupcích jemné mřížky u staveb
func _sloupce() -> void:
	for b in NB:
		if slozite[b] == 0: continue
		var bx := b % NBX; var bz := b / NBX
		for jz in dl:
			for jx in dl:
				var fx := bx * dl + jx; var fz := bz * dl + jz
				if fx >= NFX or fz >= NFZ: continue
				var x := x0 + fx * kf; var z := z0 + fz * kf
				var pt := _patra(x, z, maxf(vrch[b], hl.svet.vyska(x, z)) + 0.5)
				if pt.is_empty(): continue
				var fi := fz * NFX + fx
				sl_id[fi] = sl_fi.size(); sl_fi.append(fi); sl_off.append(NU); sl_n.append(pt.size())
				for y in pt:
					uy.append(y); usl.append(sl_fi.size() - 1); NU += 1

func _patra(x: float, z: float, top: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	var dno: float = hl.svet.vyska(x, z) - float(cfg["pod_terenem_m"])
	var y := top
	for i in int(cfg["zasahu_max"]):
		_q.from = Vector3(x, y, z); _q.to = Vector3(x, dno, z)
		var h := space.intersect_ray(_q)
		if h.is_empty(): break
		var p: Vector3 = h["position"]
		if (h["normal"] as Vector3).y >= cos_max and _vejde(p): out.append(p.y)
		if out.size() >= int(cfg["pater_max"]): break
		y = p.y - 0.05
	return out

func _vejde(p: Vector3) -> bool:
	_sq.transform = Transform3D(Basis(), p + Vector3(0, 0.05 + _tvar_y, 0))
	return space.intersect_shape(_sq, 1).is_empty()

## dveře z dat: křídla *_Dvere_* ve vsi a místech, dveře hradu (pohyb.json, skupina = střed křídel)
func _dvere() -> void:
	var sk := {}
	var hr := hl.get_node_or_null("Hrad")
	if hr != null and FileAccess.file_exists("res://data/pohyb.json"):
		for e: Dictionary in JSON.parse_string(FileAccess.get_file_as_string("res://data/pohyb.json"))["dily"]:
			if String(e.get("kind", "dvere")) != "dvere": continue
			var u := hr.find_child(String(e["name"]), true, false) as Node3D
			if u != null: sk.get_or_add("Hrad/" + String(e.get("group", e["name"])), []).append(_stred(u))
	for k in ["Mista", "Ves", "Zajimava"]:
		var kk := hl.get_node_or_null(k)
		if kk == null: continue
		for u in kk.find_children("*_Dvere_*", "Node3D", true, false):
			if String(u.name).begins_with("Schod_") or (u.get_parent() != null and "_Dvere_" in String(u.get_parent().name)): continue
			sk.get_or_add("%s/%s/%s" % [k, u.get_parent().name, u.name], []).append(_stred(u as Node3D))
	for jm in sk:
		var s := Vector3.ZERO
		for q: Vector3 in sk[jm]: s += q
		s /= float(sk[jm].size())
		var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(s + Vector3(0, 0.5, 0), s - Vector3(0, 2.5, 0), hrac.collision_mask, [hrac.get_rid()]))
		var py: float = (h["position"] as Vector3).y if not h.is_empty() else s.y - 1.0
		var p := Vector3(s.x, py, s.z)
		var id := NB + NU + dvere.size()
		dvere.append({"jm": jm, "p": p})
		var r := float(cfg["dvere_r_m"]); var dy := float(cfg["dvere_dy_m"])
		for fz in range(floori((p.z - r - z0) / kf), ceili((p.z + r - z0) / kf) + 1):
			for fx in range(floori((p.x - r - x0) / kf), ceili((p.x + r - x0) / kf) + 1):
				if fx < 0 or fz < 0 or fx >= NFX or fz >= NFZ: continue
				for u in _uzly_sloupce(fx, fz):
					var q := _poz(u)
					if Vector2(q.x - p.x, q.z - p.z).length() <= r and absf(q.y - p.y) <= dy:
						dv_bliz.get_or_add(u, []).append(id); dv_bliz.get_or_add(id, []).append(u)

func _stred(u: Node3D) -> Vector3:
	var bb := AABB(); var je := false
	for m in [u] + u.find_children("*", "VisualInstance3D", true, false):
		if m is VisualInstance3D:
			var a := (m as VisualInstance3D).global_transform * (m as VisualInstance3D).get_aabb()
			bb = a if not je else bb.merge(a); je = true
	return bb.get_center() if je else u.global_position

## uzly ve sloupci jemné mřížky (patra u staveb, jinak uzel terénu, je-li to jeho roh)
func _uzly_sloupce(fx: int, fz: int) -> Array:
	var b := (fz / dl) * NBX + fx / dl
	if slozite[b] == 1:
		var c: int = sl_id.get(fz * NFX + fx, -1)
		if c < 0: return []
		return range(NB + sl_off[c], NB + sl_off[c] + sl_n[c])
	return [b] if fx % dl == 0 and fz % dl == 0 else []

func _poz(id: int) -> Vector3:
	if id < NB: return Vector3(x0 + (id % NBX) * kb, hb[id], z0 + (id / NBX) * kb)
	if id < NB + NU:
		var fi := sl_fi[usl[id - NB]]
		return Vector3(x0 + (fi % NFX) * kf, uy[id - NB], z0 + (fi / NFX) * kf)
	return dvere[id - NB - NU]["p"]

func _starty() -> Array:
	var c: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/mapa_body.json"))
	var body: Array = [Vector2(c["start"]["cil"][0], c["start"]["cil"][1])]
	for e: Dictionary in Mapa.nacti_mista(c): body.append(e["cil"])
	var out: Array = []
	for b: Vector2 in body:
		var p := Mapa.cil_na_zemi(hl, c, b, [hrac.get_rid()])
		var nej := -1; var nd := INF
		var fx0 := roundi((p.x - x0) / kf); var fz0 := roundi((p.z - z0) / kf)
		for fz in range(fz0 - 2 * dl, fz0 + 2 * dl + 1):
			for fx in range(fx0 - 2 * dl, fx0 + 2 * dl + 1):
				if fx < 0 or fz < 0 or fx >= NFX or fz >= NFZ: continue
				for u in _uzly_sloupce(fx, fz):
					var d := _poz(u).distance_to(p)
					if d < nd: nd = d; nej = u
		if nej >= 0 and not (nej in out): out.append(nej)
		else: print("DOSAH start ", b, " bez uzlu")
	return out

func _svah(ha: float, hb_: float, d: float) -> bool:
	return hb_ - ha <= maxf(schod_max, d * tan_max)

## Chůze kapsle hráče z p k cíli (x, z): podkroky – rovně, po pochozím svahu, krok nahoru (s dosednutím na stupeň výš),
## pak dopad. Vrací polohu dopadu; Vector3.INF = neprojde; y = −INF = pod sebou nemá kolizi (díra).
func _jdi(p: Vector3, cil: Vector2) -> Vector3:
	chuzi += 1
	var d := Vector3(cil.x - p.x, 0, cil.y - p.z); var L := d.length()
	var n := maxi(1, ceili(L / float(cfg["podkrok_m"]))); var s := d / n
	var q := p + Vector3(0, 0.01, 0)
	for i in n:
		var xf := Transform3D(Basis(), q)
		if hrac.test_move(xf, s, _col):
			var jde := false
			var nr := _col.get_normal()
			if nr.y >= cos_max:   # pochozí svah: posun po rovině svahu
				var s2 := Vector3(s.x, -(nr.x * s.x + nr.z * s.z) / nr.y + 0.01, s.z)
				if not hrac.test_move(xf, s2): q += s2; jde = true
			if not jde:
				for vy in schody:
					var v := float(vy)
					if hrac.test_move(xf, Vector3.UP * v): continue
					var up := xf.translated(Vector3.UP * v)
					if hrac.test_move(up, s): continue
					if not hrac.test_move(up.translated(s), Vector3.DOWN * (v + 0.05), _col): continue
					if v - _col.get_travel().length() < 0.02 or _col.get_normal().y < cos_max: continue   # dosednout výš, na pochozí plochu (ne přeskok zídky)
					q = up.origin + s + _col.get_travel(); jde = true; break
			if not jde: return Vector3.INF
		else:
			q += s
		if hrac.test_move(Transform3D(Basis(), q), Vector3.DOWN * float(cfg["pad_hledat_m"]), _col): q += _col.get_travel()
		else: return Vector3(q.x, -INF, q.z)
	return q

## uzel v jemném sloupci (fx, fz) nejblíž výšce y (patro do shoda_patra_m, terén do 2× víc)
func _uzel(fx: int, fz: int, y: float) -> int:
	var nej := -1; var nd := float(cfg["shoda_patra_m"])
	for u in _uzly_sloupce(fx, fz):
		var d := absf(_poz(u).y - y) * (0.5 if u < NB else 1.0)
		if d <= nd: nd = d; nej = u
	return nej

## přechod u → jemný sloupec (fx, fz) chůzí
func _krok(u: int, pu: Vector3, fx: int, fz: int, out: Array) -> void:
	if fx < 0 or fz < 0 or fx >= NFX or fz >= NFZ: return
	if _uzly_sloupce(fx, fz).is_empty(): return
	var c := _jdi(pu, Vector2(x0 + fx * kf, z0 + fz * kf))
	if c == Vector3.INF: return
	if c.y == -INF:
		if diry.size() < 1000: diry.append({"x": snappedf(c.x, 0.1), "z": snappedf(c.z, 0.1), "od_y": snappedf(pu.y, 0.1)})
		return
	var v := _uzel(fx, fz, c.y)
	if v >= 0: out.append(v); rev.get_or_add(v, []).append(u)

const SMERY := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
func _hrany(u: int) -> Array:
	var out: Array = []
	var pu := _poz(u)
	if u < NB:
		var bx := u % NBX; var bz := u / NBX
		for s: Vector2i in SMERY:
			var nx := bx + s.x; var nz := bz + s.y
			if nx < 0 or nz < 0 or nx >= NBX or nz >= NBZ: _na_okraji(u); continue
			var nb := nz * NBX + nx
			if slozite[nb] == 0:
				if _svah(hb[u], hb[nb], kb): out.append(nb)
				continue
			for k in dl:   # hraniční sloupce sousední buňky se stavbou
				var fx := nx * dl + (k if s.x == 0 else (0 if s.x > 0 else dl - 1))
				var fz := nz * dl + (k if s.y == 0 else (0 if s.y > 0 else dl - 1))
				_krok(u, pu, fx, fz, out)
	elif u < NB + NU:
		var fi := sl_fi[usl[u - NB]]; var fx := fi % NFX; var fz := fi / NFX
		for s: Vector2i in SMERY:
			var nx := fx + s.x; var nz := fz + s.y
			if nx < 0 or nz < 0 or nx >= NFX or nz >= NFZ: _na_okraji(u); continue
			var nb := (nz / dl) * NBX + nx / dl
			if slozite[nb] == 1: _krok(u, pu, nx, nz, out)
			else:   # do uzlu terénu sousední buňky (jejího rohu)
				var c := _jdi(pu, Vector2(x0 + (nb % NBX) * kb, z0 + (nb / NBX) * kb))
				if c != Vector3.INF and c.y != -INF and absf(c.y - hb[nb]) <= 2.0 * float(cfg["shoda_patra_m"]): out.append(nb); rev.get_or_add(nb, []).append(u)
				elif c != Vector3.INF and c.y == -INF and diry.size() < 1000: diry.append({"x": snappedf(c.x, 0.1), "z": snappedf(c.z, 0.1), "od_y": snappedf(pu.y, 0.1)})
	for dv in dv_bliz.get(u, []):   # dveře (uzel ↔ střed křídla)
		var p2 := _poz(dv)
		var c := _jdi(pu, Vector2(p2.x, p2.z))
		if c == Vector3.INF or c.y == -INF: continue
		if u >= NB + NU:
			if absf(c.y - p2.y) <= float(cfg["dvere_dy_m"]): out.append(dv); rev.get_or_add(dv, []).append(u)
		elif absf(c.y - p2.y) <= float(cfg["shoda_patra_m"]) * 2.0: out.append(dv); rev.get_or_add(dv, []).append(u)
	return out

func _na_okraji(u: int) -> void:
	if (stav[u] & OKRAJ) == 0: stav[u] |= OKRAJ; okraj.append(u)

func _dopredu(starty: Array) -> void:
	var fr := PackedInt32Array(); var h := 0
	for s in starty: stav[s] |= DOSAZENO; fr.append(s)
	while h < fr.size():
		var u := fr[h]; h += 1
		for v in _hrany(u):
			if (stav[v] & DOSAZENO) == 0: stav[v] |= DOSAZENO; fr.append(v)

func _zpet(starty: Array) -> void:
	var fr := PackedInt32Array(); var h := 0
	for s in starty: stav[s] |= NAVRAT; fr.append(s)
	while h < fr.size():
		var v := fr[h]; h += 1
		for u in rev.get(v, []):
			if (stav[u] & (DOSAZENO | NAVRAT)) == DOSAZENO: stav[u] |= NAVRAT; fr.append(u)
		if v < NB:   # terén → terén (sklon), hrany se nepamatují
			var bx := v % NBX; var bz := v / NBX
			for s: Vector2i in SMERY:
				var nx := bx + s.x; var nz := bz + s.y
				if nx < 0 or nz < 0 or nx >= NBX or nz >= NBZ: continue
				var u := nz * NBX + nx
				if slozite[u] == 0 and (stav[u] & (DOSAZENO | NAVRAT)) == DOSAZENO and _svah(hb[u], hb[v], kb): stav[u] |= NAVRAT; fr.append(u)

## shluky uzlů splňujících podmínku (sousedství mřížky, výškový rozdíl do schodu / sklonu), od největšího
func _shluky(pod: Callable) -> Array:
	var vid := PackedByteArray(); vid.resize(stav.size())
	var out: Array = []
	for i in NB + NU:
		if vid[i] == 1 or not pod.call(i): continue
		var fr := PackedInt32Array([i]); vid[i] = 1; var h := 0
		var sx := 0.0; var sz := 0.0; var sy := 0.0
		while h < fr.size():
			var u := fr[h]; h += 1
			var pu := _poz(u); sx += pu.x; sz += pu.z; sy += pu.y
			for v in _sousede(u):
				if vid[v] == 1 or not pod.call(v): continue
				var pv := _poz(v)
				if absf(pv.y - pu.y) > maxf(schod_max, Vector2(pv.x - pu.x, pv.z - pu.z).length() * tan_max): continue
				vid[v] = 1; fr.append(v)
		var n := fr.size(); var pr := _poz(fr[0])
		out.append({"uzlu": n, "x": snappedf(sx / n, 0.1), "z": snappedf(sz / n, 0.1), "y": snappedf(sy / n, 0.1), "bod": [snappedf(pr.x, 0.1), snappedf(pr.z, 0.1), snappedf(pr.y, 0.1)], "stavba": fr[0] >= NB})
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["uzlu"]) > int(b["uzlu"]))
	return out

func _sousede(u: int) -> Array:
	var out: Array = []
	if u < NB:
		var bx := u % NBX; var bz := u / NBX
		for s: Vector2i in SMERY:
			var nx := bx + s.x; var nz := bz + s.y
			if nx < 0 or nz < 0 or nx >= NBX or nz >= NBZ: continue
			var nb := nz * NBX + nx
			if slozite[nb] == 0: out.append(nb); continue
			for k in dl:
				out.append_array(_uzly_sloupce(nx * dl + (k if s.x == 0 else (0 if s.x > 0 else dl - 1)), nz * dl + (k if s.y == 0 else (0 if s.y > 0 else dl - 1))))
	else:
		var fi := sl_fi[usl[u - NB]]; var fx := fi % NFX; var fz := fi / NFX
		for s: Vector2i in SMERY:
			var nx := fx + s.x; var nz := fz + s.y
			if nx < 0 or nz < 0 or nx >= NFX or nz >= NFZ: continue
			var nb := (nz / dl) * NBX + nx / dl
			if slozite[nb] == 1: out.append_array(_uzly_sloupce(nx, nz))
			else: out.append(nb)
	return out

## únik ze světa: hráč (fyzika hry, hrac.gd) postavený na dosažitelný okraj výseku jde unik_chuze_s ven
func _unik() -> Array:
	var out: Array = []
	if okraj.is_empty(): return out
	var n := mini(int(cfg["unik_zkousek"]), okraj.size())
	var serazene := okraj.duplicate()
	var st := Vector2((x0 + x1) / 2, (z0 + z1) / 2)
	serazene.sort_custom(func(a: int, b: int) -> bool: var pa := _poz(a); var pb := _poz(b); return Vector2(pa.x, pa.z).angle_to_point(st) < Vector2(pb.x, pb.z).angle_to_point(st))
	hrac.set_physics_process(true)
	for k in n:
		var u: int = serazene[k * serazene.size() / n]
		var p := _poz(u)
		var ven := Vector2(p.x - st.x, p.z - st.y)
		var dx := minf(p.x - x0, x1 - p.x); var dz := minf(p.z - z0, z1 - p.z)
		ven = Vector2(signf(ven.x), 0) if dx < dz else Vector2(0, signf(ven.y))
		var cil := Vector2(p.x, p.z) + ven * float(cfg["unik_ven_m"])
		hrac.velocity = Vector3.ZERO; hrac.global_position = p + Vector3(0, 0.15, 0)
		for f_ in 10: await get_tree().physics_frame
		hrac.autopilot = Vector3(cil.x, 0, cil.y)
		var ymin := p.y
		for f_ in int(float(cfg["unik_chuze_s"]) * Engine.physics_ticks_per_second):
			await get_tree().physics_frame
			ymin = minf(ymin, hrac.global_position.y)
			if hrac.global_position.y < p.y - 100.0: break
		hrac.autopilot = Vector3.INF
		var q := hrac.global_position
		var venku := q.x < x0 - 0.01 or q.x > x1 + 0.01 or q.z < z0 - 0.01 or q.z > z1 + 0.01
		print("DOSAH únik zkouška [%.1f, %.1f] → [%.1f, %.1f, %.1f]%s" % [p.x, p.z, q.x, q.z, q.y, " ZA HRANICÍ" if venku or ymin < p.y - 50.0 else ""])
		if venku or ymin < p.y - 50.0: out.append({"x": snappedf(p.x, 0.1), "z": snappedf(p.z, 0.1), "konec": [snappedf(q.x, 0.1), snappedf(q.z, 0.1), snappedf(q.y, 0.1)]})
	hrac.velocity = Vector3.ZERO
	hrac.set_physics_process(false)
	return out

## mapa dosažitelnosti po základních buňkách: zelená dosažitelné (stín podle výšky), žlutá dosažitelné u staveb,
## červená uvíznutí, modrá ostrovy / nedosažitelné pochozí, šedá bez pochozí plochy, purpurová díra, oranžová únik,
## azurová dveře bez dosahu, bílá start
func _obrazek(cesta: String, uviz: Array, ostr: Array, dv_bez: Array, unik: Array) -> void:
	var img := Image.create(NBX, NBZ, false, Image.FORMAT_RGB8)
	var hmin := INF; var hmax := -INF
	for v in hb: hmin = minf(hmin, v); hmax = maxf(hmax, v)
	for b in NB:
		var sv := 0.55 + 0.45 * (hb[b] - hmin) / maxf(1.0, hmax - hmin)
		var col := Color(0.25, 0.35, 0.6) * sv
		if slozite[b] == 0:
			if stav[b] & DOSAZENO: col = (Color(0.35, 0.75, 0.3) if stav[b] & NAVRAT else Color(0.9, 0.1, 0.1)) * (sv if stav[b] & NAVRAT else 1.0)
		else:
			var bx := b % NBX; var bz := b / NBX; var nd := 0; var nn := 0; var nu := 0; var nv := 0
			for jz in dl:
				for jx in dl:
					var fx := bx * dl + jx; var fz := bz * dl + jz
					if fx >= NFX or fz >= NFZ: continue
					for u in _uzly_sloupce(fx, fz):
						nv += 1
						if stav[u] & DOSAZENO:
							nd += 1
							if (stav[u] & NAVRAT) == 0: nu += 1
						else: nn += 1
			col = Color(0.3, 0.3, 0.3)
			if nu > 0: col = Color(0.9, 0.1, 0.1)
			elif nd > 0: col = Color(0.95, 0.85, 0.3)
			elif nv > 0: col = Color(0.3, 0.45, 0.95)
		img.set_pixel(b % NBX, b / NBX, col)
	var bod := func(x: float, z: float, c: Color, r: int) -> void:
		var px := int((x - x0) / kb); var pz := int((z - z0) / kb)
		for j in range(-r, r + 1):
			for i in range(-r, r + 1):
				if px + i >= 0 and pz + j >= 0 and px + i < NBX and pz + j < NBZ: img.set_pixel(px + i, pz + j, c)
	for d in dv_bez: bod.call(float(d["x"]), float(d["z"]), Color(0.1, 0.9, 0.95), 1)
	for d in diry: bod.call(float(d["x"]), float(d["z"]), Color(1, 0, 1), 2)
	for d in unik: bod.call(float(d["x"]), float(d["z"]), Color(1, 0.55, 0), 3)
	for s in uviz.slice(0, 25): bod.call(float(s["x"]), float(s["z"]), Color(1, 0.2, 0.2), 1)
	img.save_png(cesta)
