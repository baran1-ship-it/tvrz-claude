extends Node3D
## Teren na dlazdice s LOD (rozbor_gpu_15_11.md K4; postup Pucharta puchart/nastroje/teren_dlazdice.py + svet.gd _umisti).
## Pravidla: pravidla/svet/teren_dlazdice.json (zapnuto false = dnesni cele site). Navrh a rizika:
## docs/rozpracovane/teren_dlazdice_navrh.md.
##
## Poradi stavby (pipeline: pozdejsi krok nehybe drivejsim): dlazdice vznikaji z HOTOVE site terenu - posledni krok
## svet.build, az po vsech hernich upravach (koryto, nadrze, terasy, cesty, dily, _zamek_terenu). Puvodni site Teren*
## se nemeni: zustavaji pro kolize (_trimesh), dotazy vysek a testy, jen se nekresli (layers 0, ne visible - kod
## i testy vynechavaji neviditelne site a hledaji je podle jmena). Dlazdice jsou pod uzlem TerenDlazdice vedle modelu
## sveta, jmena D_* (find_children("Teren*") je nenajde - zadna herni uprava ani dotaz vysky je nevidi).
##
## Pece (offline, PC): TVRZ_DLAZDICE_PEC=1 godot --headless --path .  -> soubor + index (otisk hotove site).
## Hra: nacte soubor; kdyz otisk nesedi (jiny export), kdyz_neplatne: stara_cesta | pec_za_behu.
## Prostredi: TVRZ_DLAZDICE=1 vynuti zapnuti (pec za behu, kdyz soubor chybi nebo nesedi), TVRZ_DLAZDICE=0 vypne.
##
## Kus = trojuhelniky jednoho povrchu (material + format) ze vsech pasem v ctverci dlazdice podle teziste: LOD0 je
## presna kopie (vsechna pole vcetne CUSTOM0/1 cest - 0.60 _rozdel je vynechaval). Zjednodusene urovne = indexy
## z ImporterMesh.generate_lods (meshoptimizer, SIMPLIFY_LOCK_BORDER: okraj kusu se nehne -> sousedni dlazdice v jine
## urovni navazuji presne). Rozsahy urovni s hysterezi jako Puchart, sukne u zjednodusenych urovni.

const Pravidla := preload("res://scripts/pravidla.gd")
const POLE := [Mesh.ARRAY_VERTEX, Mesh.ARRAY_NORMAL, Mesh.ARRAY_TANGENT, Mesh.ARRAY_COLOR, Mesh.ARRAY_TEX_UV,
		Mesh.ARRAY_TEX_UV2, Mesh.ARRAY_CUSTOM0, Mesh.ARRAY_CUSTOM1, Mesh.ARRAY_CUSTOM2, Mesh.ARRAY_CUSTOM3]

var P: Dictionary = {}                 # pravidla/svet/teren_dlazdice.json (vsechny klice prectene pri pripojeni)
var tvrz: Node3D                       # model sveta (Tvrz) - zdroj siti Teren*
var zdroje: Array = []                 # MeshInstance3D, ktere dlazdice nahrazuji v kresleni
var zapnute := false
var stav := "vypnuto"                  # vypnuto | nacteno | peceno | neplatne | chyba
var troj_urovni: Array = []            # soucet troj. po urovnich (vypis, test)


## Hook ze svet.build (posledni krok, po vsech upravach terenu). Vrati uzel (i pri vypnuti - trasa ho muze zapnout).
static func pripoj(root: Node3D, parent: Node3D) -> Node3D:
	var d: Node3D = load("res://scripts/teren_dlazdice.gd").new()
	d.name = "TerenDlazdice"
	d.tvrz = root
	d._cti_pravidla()
	parent.add_child(d)
	var env := OS.get_environment("TVRZ_DLAZDICE")
	if OS.has_environment("TVRZ_DLAZDICE_PEC"):
		d.pec_a_uloz()
		Engine.get_main_loop().quit.call_deferred()
	elif (bool(d.P["zapnuto"]) and env != "0") or env == "1":
		d.zapni(true, env == "1")
	return d


func _cti_pravidla() -> void:
	for k: String in ["zapnuto", "dlazdice_m", "lod", "hystereze_m", "sukne_m", "uhel_slouceni_normal_st", "site", "soubor",
			"index", "kdyz_neplatne", "otisk_vzorku", "otisk_tolerance_m", "test"]:
		P[k] = Pravidla.cti("teren_dlazdice", k)
	for k: String in ["predpona", "vynechat", "vynechat_konec", "min_troj"]:
		Pravidla.cti("teren_dlazdice", "site", k)


## Zapnout / vypnout kresleni dlazdicemi (trasa: varianta teren_dlazdice). Prvni zapnuti dlazdice nacte nebo upece.
## pec: kdyz soubor chybi nebo nesedi, upect za behu (jinak podle kdyz_neplatne).
func zapni(zap: bool, pec := false) -> void:
	if zap and get_child_count() == 0:
		_vyber_zdroje()
		if not _nacti():
			if pec or String(P["kdyz_neplatne"]) == "pec_za_behu":
				var t0 := Time.get_ticks_msec()
				_postav(pec_kusy())
				stav = "peceno"
				print("TEREN_DLAZDICE peceno za behu %d ms" % (Time.get_ticks_msec() - t0))
			else:
				print("TEREN_DLAZDICE %s - zustava cela sit (kdyz_neplatne stara_cesta)" % stav)
				return
		_nastav_rozsahy()
	if get_child_count() == 0:
		return
	zapnute = zap
	visible = zap
	for mi: MeshInstance3D in zdroje:
		if not mi.has_meta("dl_layers"):
			mi.set_meta("dl_layers", mi.layers)
		mi.layers = 0 if zap else int(mi.get_meta("dl_layers"))
	print("TEREN_DLAZDICE %s (%s): kusu %d, zdroju %d, troj po urovnich %s" % ["zapnuto" if zap else "vypnuto", stav,
			get_child_count(), zdroje.size(), str(troj_urovni)])


func _vyber_zdroje() -> void:
	zdroje.clear()
	var s: Dictionary = P["site"]
	for n in tvrz.find_children(String(s["predpona"]) + "*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		if mi.mesh == null or not mi.is_visible_in_tree() or nm in (s["vynechat"] as Array):
			continue
		if (s["vynechat_konec"] as Array).any(func(k: String) -> bool: return nm.ends_with(k)):
			continue
		var troj := 0
		for si in mi.mesh.get_surface_count():
			var ni: int = mi.mesh.surface_get_array_index_len(si)
			troj += (ni if ni > 0 else mi.mesh.surface_get_array_len(si)) / 3
		if troj >= int(s["min_troj"]):
			zdroje.append(mi)
	zdroje.sort_custom(func(a: Node, b: Node) -> bool: return String(a.name) < String(b.name))


# ------------------------------------------------------------------ otisk hotove site

func otisk() -> Dictionary:
	var o := {}
	var nvz := int(P["otisk_vzorku"])
	for mi: MeshInstance3D in zdroje:
		var pov: Array = []
		for si in mi.mesh.get_surface_count():
			var v: PackedVector3Array = mi.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]
			var krok := maxi(1, v.size() / nvz)
			var ys: Array = []
			for i in range(0, v.size(), krok):
				ys.append(snappedf(v[i].y, 0.001))
			pov.append([v.size(), mi.mesh.surface_get_array_index_len(si), ys])
		o[String(mi.name)] = pov
	return o


func _otisk_sedi(a: Dictionary, b: Dictionary) -> String:
	var tol := float(P["otisk_tolerance_m"])
	if a.keys().size() != b.keys().size():
		return "jine site %s / %s" % [str(a.keys()), str(b.keys())]
	for k: String in a:
		if not b.has(k) or (a[k] as Array).size() != (b[k] as Array).size():
			return "sit %s chybi nebo ma jiny pocet povrchu" % k
		for si in (a[k] as Array).size():
			var pa: Array = a[k][si]
			var pb: Array = b[k][si]
			if int(pa[0]) != int(pb[0]) or int(pa[1]) != int(pb[1]) or (pa[2] as Array).size() != (pb[2] as Array).size():
				return "%s povrch %d: vrcholu %d/%d, indexu %d/%d" % [k, si, int(pa[0]), int(pb[0]), int(pa[1]), int(pb[1])]
			for i in (pa[2] as Array).size():
				if absf(float(pa[2][i]) - float(pb[2][i])) > tol:
					return "%s povrch %d: vyska vzorku %d %.3f / %.3f" % [k, si, i, float(pa[2][i]), float(pb[2][i])]
	return ""


# ------------------------------------------------------------------ pece

## Kusy z hotove site: [{"klic", "zdroj": [[mi, si], ...], "urovne": [[pole, troj, od_urovne], ...]}].
func pec_kusy() -> Array:
	var D := float(P["dlazdice_m"])
	var skup := {}                     # klic kusu -> {"casti": [[pole zdroje, PackedInt32Array troj.]], "mat", "flags", "zdroj"}
	for mi: MeshInstance3D in zdroje:
		var xf := mi.global_transform
		var jednotkova := xf.is_equal_approx(Transform3D.IDENTITY)
		for si in mi.mesh.get_surface_count():
			var a := mi.mesh.surface_get_arrays(si)
			var fmt: int = mi.mesh.surface_get_format(si)
			var mat := mi.get_active_material(si)
			var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
			if not jednotkova:
				a = _do_sveta(a, xf)
				v = a[Mesh.ARRAY_VERTEX]
			var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX] if a[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			if idx.is_empty():
				idx.resize(v.size())
				for i in v.size():
					idx[i] = i
				a[Mesh.ARRAY_INDEX] = idx
			var flags := _flags_custom(fmt)
			var podpis := "%d|%d" % [mat.get_instance_id() if mat else 0, flags]
			for ai in POLE:
				podpis += "1" if a[ai] != null else "0"
			var podle := {}
			for t in idx.size() / 3:
				var c := (v[idx[t * 3]] + v[idx[t * 3 + 1]] + v[idx[t * 3 + 2]]) / 3.0
				var k := Vector2i(floori(c.x / D), floori(c.z / D))
				if not podle.has(k):
					podle[k] = []                # Array (odkaz) - PackedInt32Array ve slovniku by se pri append kopirovalo
				(podle[k] as Array).append(t)
			for k: Vector2i in podle:
				var kk := "%d_%d|%s" % [k.x, k.y, podpis]
				if not skup.has(kk):
					skup[kk] = {"dl": k, "casti": [], "mat": mat, "flags": flags, "zdroj": []}
				(skup[kk]["casti"] as Array).append([a, podle[k]])
				(skup[kk]["zdroj"] as Array).append([String(mi.name), si])
	var kusy: Array = []
	var klice := skup.keys()
	klice.sort()
	var n_dl := {}
	for kk: String in klice:
		var g: Dictionary = skup[kk]
		var dl: Vector2i = g["dl"]
		var ci := int(n_dl.get(dl, 0))
		n_dl[dl] = ci + 1
		var pole := _spoj(g["casti"])
		kusy.append({"jmeno": "D_%d_%d_%d" % [dl.x, dl.y, ci], "mat": g["mat"], "flags": g["flags"], "zdroj": g["zdroj"],
				"urovne": _urovne(pole, int(g["flags"]))})
	return kusy


## Pole povrchu ve svetovych souradnicich (zdroj pod transformaci).
func _do_sveta(a: Array, xf: Transform3D) -> Array:
	var b := a.duplicate()
	var v: PackedVector3Array = (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).duplicate()
	for i in v.size():
		v[i] = xf * v[i]
	b[Mesh.ARRAY_VERTEX] = v
	if a[Mesh.ARRAY_NORMAL] != null:
		var n: PackedVector3Array = (a[Mesh.ARRAY_NORMAL] as PackedVector3Array).duplicate()
		for i in n.size():
			n[i] = (xf.basis * n[i]).normalized()
		b[Mesh.ARRAY_NORMAL] = n
	if a[Mesh.ARRAY_TANGENT] != null:
		var t: PackedFloat32Array = (a[Mesh.ARRAY_TANGENT] as PackedFloat32Array).duplicate()
		for i in t.size() / 4:
			var q := (xf.basis * Vector3(t[i * 4], t[i * 4 + 1], t[i * 4 + 2])).normalized()
			t[i * 4] = q.x
			t[i * 4 + 1] = q.y
			t[i * 4 + 2] = q.z
		b[Mesh.ARRAY_TANGENT] = t
	return b


## Formaty CUSTOM0..3 ze zdroje (bez komprese: kvantovani podle AABB kusu by posunulo sdilene hrany dlazdic).
static func _flags_custom(fmt: int) -> int:
	var f := 0
	for sh in [Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT, Mesh.ARRAY_FORMAT_CUSTOM1_SHIFT, Mesh.ARRAY_FORMAT_CUSTOM2_SHIFT, Mesh.ARRAY_FORMAT_CUSTOM3_SHIFT]:
		f |= fmt & (Mesh.ARRAY_FORMAT_CUSTOM_MASK << sh)
	return f


## Vybrane vrcholy pole (vsechna pole, delka prvku podle poctu prvku na vrchol) - jako svet._rozdel, i CUSTOM0..3.
static func _vyber(a: Array, ids: PackedInt32Array) -> Array:
	var nv := (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
	var out := []
	out.resize(Mesh.ARRAY_MAX)
	for ai in POLE:
		if a[ai] == null:
			continue
		var src = a[ai]
		var sl: int = src.size() / nv
		var dst = src.slice(0, 0)
		dst.resize(ids.size() * sl)
		if sl == 1:
			for j in ids.size():
				dst[j] = src[ids[j]]
		else:
			for j in ids.size():
				for q in sl:
					dst[j * sl + q] = src[ids[j] * sl + q]
		out[ai] = dst
	return out


## Casti z vice pasem (stejny material a format) do jednoho pole: jen pouzite vrcholy, indexy precislovane.
static func _spoj(casti: Array) -> Array:
	var out := []
	out.resize(Mesh.ARRAY_MAX)
	var idx := PackedInt32Array()
	for c: Array in casti:
		var a: Array = c[0]
		var tr: Array = c[1]
		var ai_: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		var mapa := {}
		var ids := PackedInt32Array()
		var zac := (out[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() if out[Mesh.ARRAY_VERTEX] != null else 0
		for t in tr:
			for e in 3:
				var vi := ai_[t * 3 + e]
				if not mapa.has(vi):
					mapa[vi] = ids.size()
					ids.append(vi)
				idx.append(zac + int(mapa[vi]))
		var vyb := _vyber(a, ids)
		for ai in POLE:
			if vyb[ai] == null:
				continue
			if out[ai] == null:
				out[ai] = vyb[ai]
			else:
				var cur = out[ai]
				cur.append_array(vyb[ai])
				out[ai] = cur
	out[Mesh.ARRAY_INDEX] = idx
	return out


## Urovne kusu: [[pole, troj, index urovne v P.lod od, do]]. Uroven 0 = presna kopie; dalsi = nejhrubsi LOD z
## generate_lods s chybou <= chyba_m, vrcholy zhustene, sukne po okraji. Bez zisku se slouci s predchozi.
func _urovne(pole: Array, flags: int) -> Array:
	var lod: Array = P["lod"]
	var idx0: PackedInt32Array = pole[Mesh.ARRAY_INDEX]
	var out: Array = [[pole, idx0.size() / 3, 0, 0]]
	if lod.size() < 2:
		return out
	var im := ImporterMesh.new()
	im.add_surface(Mesh.PRIMITIVE_TRIANGLES, pole, [], {}, null, "", flags)
	im.generate_lods(float(P["uhel_slouceni_normal_st"]), 0.0, [])
	var predchozi := idx0.size()
	for ui in range(1, lod.size()):
		var chyba := float(lod[ui]["chyba_m"])
		var nej := -1
		var nej_n := predchozi
		for li in im.get_surface_lod_count(0):
			var n := im.get_surface_lod_indices(0, li).size()
			if im.get_surface_lod_size(0, li) <= chyba and n < nej_n:
				nej = li
				nej_n = n
		if nej < 0 or nej_n > int(predchozi * 0.8):
			(out[out.size() - 1] as Array)[3] = ui                 # bez zisku: predchozi uroven siaha dal
			continue
		out.append([_s_suknemi(pole, im.get_surface_lod_indices(0, nej)), nej_n / 3, ui, ui])
		predchozi = nej_n
	return out


## Zjednodusena uroven: jen pouzite vrcholy + sukne (svisle dolu o sukne_m, oboustranne) po okrajovych hranach.
func _s_suknemi(pole: Array, idx: PackedInt32Array) -> Array:
	var v: PackedVector3Array = pole[Mesh.ARRAY_VERTEX]
	var s := float(P["sukne_m"])
	var mapa := {}
	var ids := PackedInt32Array()
	var ni := PackedInt32Array()
	ni.resize(idx.size())
	for i in idx.size():
		var vi := idx[i]
		if not mapa.has(vi):
			mapa[vi] = ids.size()
			ids.append(vi)
		ni[i] = int(mapa[vi])
	var dolu := PackedInt32Array()            # nove vrcholy sukne: index zdroje
	if s > 0.0:
		# okraj = hrana jen jednoho trojuhelniku (vrcholy svarene podle polohy po 1 mm)
		var svar := {}
		var sid := PackedInt32Array()
		sid.resize(ids.size())
		for j in ids.size():
			var key := Vector3i((v[ids[j]] * 1000.0).round())
			if not svar.has(key):
				svar[key] = j
			sid[j] = int(svar[key])
		var hrany := {}
		for t in ni.size() / 3:
			for e in 3:
				var a := sid[ni[t * 3 + e]]
				var b := sid[ni[t * 3 + (e + 1) % 3]]
				var k := Vector2i(mini(a, b), maxi(a, b))
				hrany[k] = int(hrany.get(k, 0)) + 1
		for t in ni.size() / 3:
			for e in 3:
				var a := ni[t * 3 + e]
				var b := ni[t * 3 + (e + 1) % 3]
				var k := Vector2i(mini(sid[a], sid[b]), maxi(sid[a], sid[b]))
				if int(hrany[k]) != 1:
					continue
				var a2 := ids.size() + dolu.size()
				dolu.append(ids[a])
				dolu.append(ids[b])
				var b2 := a2 + 1
				ni.append_array(PackedInt32Array([a, a2, b, b, a2, b2, a, b, a2, b, b2, a2]))
	var vse := ids.duplicate()
	vse.append_array(dolu)
	var out := _vyber(pole, vse)
	var ov: PackedVector3Array = out[Mesh.ARRAY_VERTEX]
	for j in range(ids.size(), vse.size()):
		var q := ov[j]
		q.y -= s
		ov[j] = q
	out[Mesh.ARRAY_VERTEX] = ov
	out[Mesh.ARRAY_INDEX] = ni
	return out


## Uzly kusu (bez materialu - ten se bere ze zdroje pri nacteni, sdileny material zeme s uniformami pocasi apod.).
func _postav(kusy: Array) -> void:
	troj_urovni = []
	troj_urovni.resize((P["lod"] as Array).size())
	troj_urovni.fill(0)
	for k: Dictionary in kusy:
		for u: Array in k["urovne"]:
			var am := ArrayMesh.new()
			am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, u[0], [], {}, int(k["flags"]))
			var mi := MeshInstance3D.new()
			mi.name = "%s_L%d" % [k["jmeno"], int(u[2])]
			mi.mesh = am
			mi.set_meta("od", int(u[2]))
			mi.set_meta("do", int(u[3]))
			mi.set_meta("zdroj", k["zdroj"])
			if k["mat"]:
				mi.material_override = k["mat"]
			add_child(mi)
			troj_urovni[int(u[2])] += int(u[1])


## Rozsahy viditelnosti a material ze zdroje (vzdy z dnesnich pravidel - zmena do_m / hystereze bez nove pece).
func _nastav_rozsahy() -> void:
	var lod: Array = P["lod"]
	var h := float(P["hystereze_m"])
	var podle := {}
	for mi: MeshInstance3D in zdroje:
		podle[String(mi.name)] = mi
	for n in get_children():
		var mi := n as MeshInstance3D
		var od := int(mi.get_meta("od"))
		var do_ := int(mi.get_meta("do"))
		mi.visibility_range_begin = 0.0 if od == 0 else maxf(0.0, float(lod[od - 1]["do_m"]) - h)
		mi.visibility_range_end = 0.0 if do_ == lod.size() - 1 else float(lod[do_]["do_m"]) + h
		mi.visibility_range_begin_margin = h
		mi.visibility_range_end_margin = h
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF          # jako teren (svet.build: rozpocet)
		var z: Array = (mi.get_meta("zdroj") as Array)[0]
		var src: MeshInstance3D = podle.get(String(z[0]))
		if src:
			mi.material_override = src.get_active_material(int(z[1]))
			mi.layers = int(src.get_meta("dl_layers")) if src.has_meta("dl_layers") else src.layers
			mi.gi_mode = src.gi_mode


# ------------------------------------------------------------------ soubor

func pec_a_uloz() -> void:
	var t0 := Time.get_ticks_msec()
	_vyber_zdroje()
	var kusy := pec_kusy()
	_postav(kusy)
	for n in get_children():
		n.owner = self
		(n as MeshInstance3D).material_override = null          # material se priradi pri nacteni ze zdroje
	var ps := PackedScene.new()
	ps.pack(self)
	DirAccess.make_dir_recursive_absolute(String(P["soubor"]).get_base_dir())
	var e := ResourceSaver.save(ps, String(P["soubor"]), ResourceSaver.FLAG_COMPRESS)
	var f := FileAccess.open(String(P["index"]), FileAccess.WRITE)
	f.store_string(JSON.stringify({"otisk": otisk(), "kusu": get_child_count(), "troj_urovni": troj_urovni,
			"dlazdice_m": P["dlazdice_m"], "lod": P["lod"], "peceno": Time.get_datetime_string_from_system()}))
	f.close()
	print("TEREN_DLAZDICE PEC %s: zdroju %d, kusu %d, troj po urovnich %s, %d ms (chyba ulozeni %d)" % [P["soubor"],
			zdroje.size(), get_child_count(), str(troj_urovni), Time.get_ticks_msec() - t0, e])


func _nacti() -> bool:
	if not ResourceLoader.exists(String(P["soubor"])) or not FileAccess.file_exists(String(P["index"])):
		stav = "chybi soubor"
		return false
	var ix: Variant = JSON.parse_string(FileAccess.get_file_as_string(String(P["index"])))
	if not (ix is Dictionary):
		stav = "chyba indexu"
		return false
	var duvod := _otisk_sedi(otisk(), (ix as Dictionary).get("otisk", {}))
	if duvod != "":
		stav = "neplatne: " + duvod
		return false
	var ps: PackedScene = load(String(P["soubor"]))
	var uzel := ps.instantiate() if ps else null
	if uzel == null:
		stav = "chyba nacteni"
		return false
	for n in uzel.get_children():
		uzel.remove_child(n)
		n.owner = null
		add_child(n)
	uzel.free()
	troj_urovni = (ix as Dictionary).get("troj_urovni", [])
	stav = "nacteno"
	return true
