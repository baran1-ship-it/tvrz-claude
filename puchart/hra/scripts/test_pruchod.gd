extends Node
## Test průchodu hradem (PUCHART_TEST=pruchod): postava sama projde trasy z data/pruchody.json (generuje je stavitel
## hradu ze stejné geometrie) – mosty, brány, nádvoří, schody, ochozy, věže. U každého bodu musí být do 0,6 m
## vodorovně (nebo podle 4. čísla bodu) a ve výšce podlahy (±0,5 m); když 3 s nepostoupí o 5 cm, uvízla. Výsledek: stdout + user://pruchod.json.
const Pravidla := preload("res://scripts/pravidla.gd")
var hlavni: Node
var hrac: CharacterBody3D
var trasy: Dictionary
var jmena: Array
var ti := 0
var bi := 0
var vysledek := {}
var _posl := Vector3.ZERO
var _cas_posl := 0.0
var _cekej := 0.0

func zacni(h: Node, p: CharacterBody3D) -> void:
	hlavni = h; hrac = p
	trasy = JSON.parse_string(FileAccess.get_file_as_string("res://data/pruchody.json"))["trasy"]
	for f in DirAccess.get_files_at("res://data"):   # trasy dalších stavitelů (pruchody_voda.json …)
		if f.begins_with("pruchody_") and f.ends_with(".json"):
			trasy.merge(JSON.parse_string(FileAccess.get_file_as_string("res://data/" + f))["trasy"])
	jmena = trasy.keys()
	if OS.get_environment("PUCHART_JEN") != "": jmena = []   # ladění: jen vybrané testy (_konec), bez tras
	if OS.get_environment("PUCHART_TRASA") != "": jmena = Array(OS.get_environment("PUCHART_TRASA").split(",", false))   # ladění: jen vybrané trasy (a,b,…)
	hrac.set_physics_process(true)
	var clm := CanvasLayer.new(); add_child(clm); var dvm: Node = load("res://scripts/dvere.gd").new(); clm.add_child(dvm); dvm.zacni(hlavni, clm, true)   # padací mosty mají kolizi jen z dvere.gd (bez ní trasy přes most padaly, 12. 11.); křídla dveří zkouší test vrat
	_start_trasy()

func _y(b: Array) -> float:
	return float(b[2]) if b[2] != null else hlavni.svet.vyska(b[0], b[1])

func _start_trasy() -> void:
	if ti >= jmena.size():
		_konec(); return
	var b: Array = trasy[jmena[ti]][0]
	hlavni.svet.kolize_ihned(Vector3(b[0], _y(b), b[1]))
	hrac.velocity = Vector3.ZERO
	hrac.position = Vector3(b[0], _y(b) + 0.15, b[1])
	bi = 1; _cekej = 1.0; _cas_posl = 0.0; _posl = hrac.position
	hrac.autopilot = Vector3.INF

func _physics_process(dt: float) -> void:
	if ti >= jmena.size() or hrac == null:
		return
	if _cekej > 0.0:   # dosednutí po přesunu
		_cekej -= dt; return
	var body: Array = trasy[jmena[ti]]
	var b: Array = body[bi]
	var cil := Vector3(b[0], 0, b[1])
	hrac.autopilot = cil
	var vod := Vector2(hrac.position.x - b[0], hrac.position.z - b[1]).length()
	if vod < (float(b[3]) if b.size() > 3 else 0.6):   # [x, z, y, tolerance] – přesné body (konec schodů)
		if b[2] != null and absf(hrac.position.y - float(b[2])) > 0.5:
			_chyba("bod %d ve výšce %.2f místo %.2f" % [bi, hrac.position.y, float(b[2])]); return
		bi += 1; _cas_posl = 0.0; _posl = hrac.position
		if bi >= body.size():
			vysledek[jmena[ti]] = "OK"; print("PRUCHOD ", jmena[ti], " OK")
			ti += 1; _start_trasy()
		return
	_cas_posl += dt
	if _cas_posl > 3.0:
		if (hrac.position - _posl).length() < 0.05:
			_chyba("uvízla u [%.2f, %.2f, %.2f] na cestě k bodu %d [%.2f, %.2f]" % [hrac.position.x, hrac.position.z, hrac.position.y, bi, b[0], b[1]]); return
		_cas_posl = 0.0; _posl = hrac.position
	if hrac.position.y < -60.0:
		_chyba("propad pod terén"); return

## strom_kolize: postava jde přímo na kmen nejbližšího stromu u startu – kmen ji musí zastavit (matice strom|hrac)
func _test_kmene() -> void:
	var les: Node = hlavni.get_node_or_null("Les")
	if les == null or not les.has_method("nejblizsi_kmen"):
		vysledek["strom_kolize"] = "CHYBA: les bez kolizí kmenů"; return
	var p0 := Vector3(-60, 0, -150)
	var k: Vector4 = les.nejblizsi_kmen(p0)
	for r_ in [40.0, 80.0, 120.0]:   # 14. 11.: u startu stojí kovářova usedlost (stromy pryč) – nejbližší strom v okolí
		for a_ in 8:
			if k.x != INF: break
			p0 = Vector3(-60, 0, -150) + Vector3(cos(a_ * TAU / 8.0), 0, sin(a_ * TAU / 8.0)) * r_
			k = les.nejblizsi_kmen(p0)
	if k.x == INF:
		vysledek["strom_kolize"] = "CHYBA: žádný strom u startu"; return
	var smer := Vector3(1, 0, 0)
	var st := Vector3(k.x, 0, k.z) - smer * 3.0; st.y = hlavni.svet.vyska(st.x, st.z) + 0.2
	les.aktualizuj_kolize(Vector3(k.x, k.y, k.z), true); hlavni.svet.kolize_ihned(st)
	hrac.velocity = Vector3.ZERO; hrac.position = st
	await get_tree().create_timer(0.5).timeout
	hrac.autopilot = Vector3(k.x + smer.x * 3.0, 0, k.z)
	var nejbliz := INF   # kmen smí postavu odklonit (obejde ho), ale nesmí jím projít: osa kmene ≥ poloměr + kapsle
	for i in 80:
		await get_tree().physics_frame
		nejbliz = minf(nejbliz, Vector2(hrac.position.x - k.x, hrac.position.z - k.z).length())
	hrac.autopilot = Vector3.INF
	var ujela := Vector2(hrac.position.x - st.x, hrac.position.z - st.z).length()   # QA: bez pohybu by test prošel naprázdno
	if ujela < 1.5: vysledek["strom_kolize"] = "CHYBA: postava se nerozešla (%.2f m)" % ujela   # kmen zastaví na ~3 − (poloměr + kapsle)
	else: vysledek["strom_kolize"] = "OK" if nejbliz > k.w + 0.2 else "CHYBA: prošla kmenem (nejblíž %.2f m od osy, poloměr %.2f)" % [nejbliz, k.w]
	print("PRUCHOD strom_kolize ", vysledek["strom_kolize"])

## povrch_kolize (Míša 3. 11.: „nic nelevituje, nepropadá se“; Havran kolize_troj/stavby_na_zemi): po všech trasách
## průchodu po 0,5 m paprsek dolů proti kolizi a proti viditelné síti (hrad + terén). Liší-li se o víc než tolerance
## (pravidla/svet/kontroly.json povrch), postava se bořila do podlahy nebo stála na neviditelném.
var _dv: Node = null
func _dvere() -> Node:   # skript dveří jako ve hře (křídla mají kolizi až z něj) – sdílí povrch i vrata
	if _dv == null:
		var cl := CanvasLayer.new(); add_child(cl)
		_dv = load("res://scripts/dvere.gd").new(); cl.add_child(_dv); _dv.zacni(hlavni, cl)
	return _dv

## rozbor nálezu povrchu: bod světa v souřadnicích stavby (dítě vrstvy Mista / Ves / Hrad), ve kterém leží síť – [stavba, x, y, z]
func _lokalne(n: Node3D, w: Vector3) -> Array:
	if n == null: return []
	var u: Node = n
	while u.get_parent() != null and not (String(u.get_parent().name) in ["Mista", "Ves", "Hrad", "Hospodarske"]): u = u.get_parent()
	if not (u is Node3D): return []
	var l: Vector3 = (u as Node3D).global_transform.affine_inverse() * w
	return [String(u.name), snappedf(l.x, 0.01), snappedf(l.y, 0.01), snappedf(l.z, 0.01)]

func _test_povrch() -> void:
	_dvere(); await get_tree().physics_frame
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/kontroly_hra.json"))["povrch"]
	var tol := float(cfg["tolerance_m"]); var krok := float(cfg["krok_m"]); var _t0 := Time.get_ticks_msec()
	var site: Array = []   # [TriangleMesh, Transform3D inv, Transform3D]
	var hr: Node = hlavni.get_node_or_null("Hrad")
	if hr == null:
		vysledek["povrch_kolize"] = "CHYBA: bez hradu"; return
	var vrstvy: Array = []   # celý svět (Míša 3. 11.: „ne jen hrad, celkově světa“): hrad, skály, břehy a lávky
	for jm in cfg["vrstvy"]:
		var nd: Node = hlavni.get_node_or_null(jm)
		if nd != null: vrstvy.append(nd)
	for par in hlavni._lod_pary:   # LOD hradu podle kamery (≥60 m = HradDaleko) – test porovnává s blízkou verzí, kterou hráč u zdi vidí (15. 11.: 702 falešných nálezů u A, když test skončil u B)
		for m in par[2]: (m as Node3D).visible = true
		for m in par[3]: (m as Node3D).visible = false
	for vr: Node in vrstvy:
		for m in vr.find_children("*", "MeshInstance3D", true, false):
			var mi := m as MeshInstance3D
			if mi.mesh == null or String(mi.name).begins_with("KOLIZE") or (String(mi.get_parent().name).begins_with("Pohyb") and not String(mi.get_parent().name).begins_with("Pohyb_most")):   # padací most se chodí (spuštěný) – je to povrch
				continue
			if mi.visibility_range_begin > float(cfg.get("lod_od_max_m", 1.0)) or not mi.is_visible_in_tree() or mi.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:   # + kopie jen pro stín (_Daleko_Stin) – není vidět   # vzdálený/střední stupeň (Dum2_Daleko od 110 m) zblízka není vidět – hráč u vchodu ho nevidí (15. 11.: falešné „projde viditelným“ u Dum2 po přidání vrstvy Mista)
				continue
			for si in mi.mesh.get_surface_count():   # hladina se neprochází po povrchu (brodí se) – bez ní
				var mat := mi.get_active_material(si)
				if mat != null and String(mat.resource_name) in cfg["bez_materialu"]: continue
				var am := ArrayMesh.new(); am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, mi.mesh.surface_get_arrays(si))
				var tm := am.generate_triangle_mesh()
				if tm != null: site.append([tm, mi.global_transform.affine_inverse(), mi.global_transform, (mi.global_transform * am.get_aabb()).grow(3.0), String(mat.resource_name) if mat != null else "", String(mi.name), mi])
	print("POVRCH sítí %d, příprava %d ms" % [site.size(), Time.get_ticks_msec() - _t0])
	var koule := CapsuleShape3D.new(); koule.radius = float(cfg["telo_r_m"]); koule.height = float(cfg["telo_vyska_m"])   # celé tělo postavy
	var space := hrac.get_world_3d().direct_space_state
	var n := 0; var spatne: Array = []; var horsi := 0.0; var sten := 0; var vse: Array = []
	var tr_vse: Dictionary = trasy.duplicate()
	var sk: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/skaly_body.json"))["skaly"]
	for i in range(0, sk.size(), int(cfg["skaly_kazda"])):
		var c: Array = sk[i]["stred"]
		tr_vse["skala_%d" % i] = [[c[0] - 1.0, c[1], null], [c[0] + 1.0, c[1], null]]
	var jen_tr: PackedStringArray = OS.get_environment("PUCHART_POVRCH_TRASY").split(",", false)   # rozbor: jen trasy s těmito předponami (prázdné = všechny)
	for jm in tr_vse:
		if not jen_tr.is_empty() and not Array(jen_tr).any(func(pr_): return String(jm).begins_with(pr_)): continue
		var body: Array = tr_vse[jm]
		for i in body.size() - 1:
			var a: Array = body[i]; var b: Array = body[i + 1]
			var pa := Vector3(a[0], _y(a), a[1]); var pb := Vector3(b[0], _y(b), b[1])
			var kroku := maxi(1, int(Vector2(pb.x - pa.x, pb.z - pa.z).length() / krok))
			for k in kroku + (1 if String(jm).begins_with("skala") else 0):
				var p := pa.lerp(pb, float(k) / kroku)
				var od := p + Vector3(0, float(cfg["nad_m"]) + (8.0 if String(jm).begins_with("skala") else 0.0), 0); var do_ := p - Vector3(0, float(cfg["pod_m"]), 0)
				hlavni.svet.kolize_ihned(p)
				var q := PhysicsRayQueryParameters3D.create(od, do_); q.exclude = [hrac.get_rid()]
				var h := space.intersect_ray(q)
				var ex: Array[RID] = [hrac.get_rid()]
				while not h.is_empty() and not (hlavni.svet.is_ancestor_of(h["collider"]) or vrstvy.any(func(vv): return vv.is_ancestor_of(h["collider"]))):
					ex.append((h["collider"] as CollisionObject3D).get_rid()); q.exclude = ex; h = space.intersect_ray(q)   # kmeny, keře: nejsou povrch
				if h.is_empty(): continue
				if String(jm).begins_with("skala") and _pod_stavbou(h["position"]): continue   # bod skály pod zdí/palácem (stavby_clony.json) – není povrch
				var pq := PhysicsShapeQueryParameters3D.new(); pq.shape = koule; pq.transform = Transform3D(Basis(), Vector3(p.x, h["position"].y + 0.05 + float(cfg["telo_vyska_m"]) / 2, p.z)); pq.exclude = [hrac.get_rid()]
				if not space.intersect_shape(pq, 1).is_empty(): continue   # tělo postavy by tu bylo ve zdi (vzorek u zdi / přes její tloušťku) – tam se nestojí
				var hy: float = h["position"].y   # viditelný povrch v okně kolem místa, kde postava opravdu stojí (zásah kolize)
				var o_od := Vector3(p.x, hy + float(cfg["okno_m"]), p.z); var o_do := Vector3(p.x, hy - float(cfg["pod_m"]), p.z)
				var vt: float = hlavni.svet.vyska(p.x, p.z)
				var vis: float = vt if vt <= o_od.y else -INF
				var blizko := site.filter(func(e): var bb: AABB = e[3]; return p.x >= bb.position.x and p.x <= bb.end.x and p.z >= bb.position.z and p.z <= bb.end.z)
				var pet: Array = []   # 5 paprsků v okruhu 6 cm, medián (mezera mezi prkny ani hrana schodu není povrch, chodidlo je širší)
				for o5 in [Vector3.ZERO, Vector3(0.05, 0, 0.05), Vector3(-0.05, 0, 0.05), Vector3(0.05, 0, -0.05), Vector3(-0.05, 0, -0.05)]:   # úhlopříčně: spára prken v ose x/z zachytí nejvýš 1 paprsek (dřív 3 – medián = spára, 4. 11.)
					var v5: float = vis
					for s in blizko:
						var lo: Vector3 = s[1] * (o_od + o5); var ld: Vector3 = (s[1] * (o_do + o5)) - lo
						var r: Dictionary = (s[0] as TriangleMesh).intersect_ray(lo, ld.normalized())
						if not r.is_empty():
							var w: Vector3 = s[2] * (r["position"] as Vector3)
							if w.y <= o_od.y and w.y >= o_do.y: v5 = maxf(v5, w.y)
					pet.append(v5)
				pet.sort(); vis = pet[2]
				if vis == -INF: vis = hy - float(cfg["pod_m"])
				n += 1
				if k % int(cfg["steny_kazdy"]) == 0:   # zdi: v 8 směrech, v několika výškách těla; hráče zajímá, zda projde viditelným nebo narazí do neviditelného
					var dosah := float(cfg["steny_dosah_m"]); var tol_s := float(cfg["steny_tolerance_m"])
					for u in 8:
						var sm := Vector3(cos(u * PI / 4), 0, sin(u * PI / 4))
						var _dwp := Vector3.ZERO; var _dnode: Node3D = null; var dv_min := INF; var dv_vse := INF; var dk_min := INF; var dmat := ""; var dk_obj := ""   # dv_min od 0,4 m (projde viditelným), dv_vse všechny výšky (neviditelná stěna)
						for v in cfg["steny_vysky_m"]:
							var z0 := Vector3(p.x, hy + float(v), p.z)
							var pin := PhysicsPointQueryParameters3D.new(); pin.position = z0; pin.exclude = [hrac.get_rid()]
							if not space.intersect_point(pin, 1).is_empty(): continue   # začátek paprsku v kameni (pata klenby nad hlavou) – zevnitř kolize nic netrefí
							for s in blizko:
								var lo: Vector3 = s[1] * z0; var r: Dictionary = (s[0] as TriangleMesh).intersect_ray(lo, (s[1].basis * sm).normalized())
								if not r.is_empty() and (s[2].basis * (r["normal"] as Vector3)).dot(sm) < 0.0:   # jen líc natočený k hráči (rub plochy není vidět)
									var dd: float = z0.distance_to(s[2] * (r["position"] as Vector3))
									dv_vse = minf(dv_vse, dd)
									if dd < dv_min and float(v) >= float(cfg["steny_od_m"]) and not (s[4] in cfg["projit_smi"]): dv_min = dd; _dwp = s[2] * (r["position"] as Vector3); _dnode = s[6]; dmat = "%s %s y%.2f [%.2f,%.2f,%.2f]" % [s[4], s[5], hy, (s[2] * (r["position"] as Vector3)).x, (s[2] * (r["position"] as Vector3)).z, (s[2] * (r["position"] as Vector3)).y]
							var qs := PhysicsRayQueryParameters3D.create(z0, z0 + sm * dosah); qs.exclude = [hrac.get_rid()]
							var hs := space.intersect_ray(qs)
							if not hs.is_empty() and vrstvy.any(func(vv): return vv.is_ancestor_of(hs["collider"])):
								var dk_ := z0.distance_to(hs["position"])
								if dk_ < dk_min: dk_min = dk_; dk_obj = "%s/%s" % [(hs["collider"] as Node).get_parent().name, (hs["collider"] as Node).name]
						var chyba := ""
						if dv_min < float(cfg["steny_blizko_m"]) and dk_min > dv_min + tol_s:
							chyba = "projde viditelným"   # ...pokud to není výstupek reliéfu u zdi s kolizí (paprsky o 12 cm vedle)
							var bok := Vector3(-sm.z, 0, sm.x) * float(cfg["relief_bok_m"])
							for v in cfg["steny_vysky_m"]:
								for b_ in [bok, -bok]:
									var z1: Vector3 = Vector3(p.x, hy + float(v), p.z) + b_
									var q1 := PhysicsRayQueryParameters3D.create(z1, z1 + sm * (dv_min + tol_s)); q1.exclude = [hrac.get_rid()]
									if not space.intersect_ray(q1).is_empty(): chyba = ""
						elif dk_min < float(cfg["steny_blizko_m"]) and dv_vse > dk_min + tol_s:
							chyba = "neviditelná stěna"   # ...pokud v místě kolize není nic vidět nad ani pod (otevřené zábradlí: madlo a sloupky)
							var hp := Vector3(p.x, hy, p.z) + sm * (dk_min + 0.06)
							for o5 in [Vector3.ZERO, sm * 0.08, -sm * 0.08]:
								for s in blizko:
									var lo: Vector3 = s[1] * (hp + o5 + Vector3(0, 2.0, 0)); var ld: Vector3 = (s[1] * (hp + o5 - Vector3(0, 0.3, 0))) - lo
									var r: Dictionary = (s[0] as TriangleMesh).intersect_ray(lo, ld.normalized())
									if not r.is_empty() and (s[2] * (r["position"] as Vector3)).y > hy - 0.3: chyba = ""
						if chyba != "":
							sten += 1; vse.append({"druh": "zed", "chyba": chyba, "trasa": jm, "p": [p.x, p.z, hy], "smer": u * 45, "zed": dv_min, "kolize": dk_min, "mat": dmat, "lok": _lokalne(_dnode, _dwp), "kolize_obj": dk_obj})
							if spatne.size() < 24: spatne.append("%s [%.1f, %.1f] směr %d° %s (vidět %s m, kolize %s m %s, %s)" % [jm, p.x, p.z, u * 45, chyba, "–" if dv_min == INF else "%.2f" % dv_min, "–" if dk_min == INF else "%.2f" % dk_min, dk_obj, dmat])
				var d: float = (h["position"] as Vector3).y - vis
				if absf(d) > tol:
					horsi = maxf(horsi, absf(d)); vse.append({"druh": "povrch", "trasa": jm, "p": [p.x, p.z, p.y], "d": d, "kolize_y": h["position"].y, "vid_y": vis, "objekt": (h["collider"] as Node).get_parent().name, "kolize_obj": String((h["collider"] as Node).name), "lok": _lokalne(h["collider"] as Node3D, h["position"])})
					if spatne.size() < 12: spatne.append("%s [%.1f, %.1f] %s %.2f m" % [jm, p.x, p.z, "stojí nad viditelným" if d > 0 else "boří se", absf(d)])
	var fo := FileAccess.open(OS.get_environment("PUCHART_POVRCH") if OS.has_environment("PUCHART_POVRCH") else "user://povrch.json", FileAccess.WRITE); fo.store_string(JSON.stringify(vse, " "))
	var skup := {}   # souhrn nálezů podle (trasa bez pořadí, druh, síť / kolize, materiál) – výpis bodů je ořezaný, souhrn ukáže všechny skupiny (15. 11.)
	for e: Dictionary in vse:
		var tr_ := String(e["trasa"]); var rx := RegEx.create_from_string("_\\d+$"); tr_ = rx.sub(tr_, "")
		var k_ := ""
		if e["druh"] == "zed": k_ = "%s | %s | %s" % [tr_, e["chyba"], " ".join(String(e["mat"]).split(" ").slice(0, 2)) if e["chyba"] == "projde viditelným" else "kolize " + String(e.get("kolize_obj", ""))]   # projde: viditelná síť bez kolize; neviditelná stěna: kolize bez sítě
		else: k_ = "%s | %s | %s" % [tr_, "stojí nad viditelným" if float(e["d"]) > 0 else "boří se", e.get("kolize_obj", e["objekt"])]
		skup[k_] = int(skup.get(k_, 0)) + 1
	var sk_: Array = skup.keys(); sk_.sort_custom(func(a_, b_): return int(skup[a_]) > int(skup[b_]))
	for k_ in sk_: print("POVRCH souhrn %4d  %s" % [skup[k_], k_])
	var souhrn := ", ".join(sk_.slice(0, 8).map(func(k_): return "%d× %s" % [skup[k_], k_]))
	vysledek["povrch_kolize"] = "OK" if spatne.is_empty() and n > 100 else "CHYBA: %d bodů, nálezů %d ve %d skupinách (%s); %s" % [n, vse.size(), skup.size(), souhrn, "; ".join(spatne) if not spatne.is_empty() else "málo bodů"]
	print("PRUCHOD povrch_kolize ", vysledek["povrch_kolize"], " (bodů %d, nejhorší %.2f m, zdí nesedí %d)" % [n, horsi, sten])

## vrata_funkce (Míša 3. 11.: funkční vrata): zavřená vrata hlavní brány předního hradu postavu zastaví, otevřená pustí
func _test_vrata() -> void:
	var dv: Node = _dvere()
	var tr: Array = trasy.get("A_vstup", [])
	if dv.mista.is_empty() or tr.size() < 6:
		vysledek["vrata_funkce"] = "CHYBA: bez vrat nebo trasy"; return
	var brana := Vector3(tr[4][0], float(tr[4][2]), tr[4][1]); var g := ""; var nd := 1e9   # bod brány má výšku (průjezd)
	var smer := Vector3(tr[4][0] - tr[3][0], 0, tr[4][1] - tr[3][1]).normalized()
	var pred := brana - smer * 3.0; var za := brana + smer * 3.0   # 3 m před a za vraty v rovině průjezdu (ne terén pod mostem)
	for k in dv.mista:
		if dv.druh.get(k, "") == "most": continue   # naviják padacího mostu stojí u brány – test je pro vrata
		var dd: float = Vector2(dv.mista[k].x - brana.x, dv.mista[k].z - brana.z).length()
		if dd < nd: nd = dd; g = k
	var prosla := func() -> bool:
		hrac.velocity = Vector3.ZERO; hrac.position = pred + Vector3(0, 0.3, 0); hlavni.svet.kolize_ihned(pred)
		await get_tree().create_timer(0.4).timeout
		hrac.autopilot = Vector3(za.x, 0, za.z)
		for i in 240:
			await get_tree().physics_frame
		hrac.autopilot = Vector3.INF
		return Vector2(hrac.position.x - za.x, hrac.position.z - za.z).length() < 1.0
	dv.prepni(g); await get_tree().create_timer(1.5).timeout   # zavřít
	var zavrena_prosla: bool = await prosla.call()
	dv.prepni(g); await get_tree().create_timer(1.5).timeout   # otevřít
	var otevrena_prosla: bool = await prosla.call()
	vysledek["vrata_funkce"] = "OK" if (not zavrena_prosla and otevrena_prosla) else "CHYBA: zavřená prošla=%s, otevřená prošla=%s (skupina %s, %.1f m od brány)" % [zavrena_prosla, otevrena_prosla, g, nd]
	print("PRUCHOD vrata_funkce ", vysledek["vrata_funkce"])

## mapa_cestovani (Míša 12. 11. večer: přesun do sklepa z nabídky Místa propadl pod mapu): pro každé místo mapy a start
## stejný výpočet jako hra (mapa.gd priprav_kolize + cil_na_zemi), postava 2 s stojí – musí být na zemi (is_on_floor)
## a do 0,5 m nad podlahou pod sebou (paprsek dolů na kolize), ne pod terénem.
func _test_mapa() -> void:
	var M: GDScript = load("res://scripts/mapa.gd")
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/mapa_body.json"))
	var body: Array = M.nacti_mista(cfg)
	body.append({"nazev": "start", "cil": Vector2(cfg["start"]["cil"][0], cfg["start"]["cil"][1])})
	var spatne: Array = []
	for m: Dictionary in body:
		var c: Vector2 = m["cil"]
		M.priprav_kolize(hlavni, c)
		hlavni.svet._t = 1.0   # jako ve hře: údržba kolizí proběhne ještě se starou polohou hráče (Míša 14. 11.: propad po přesunu)
		await get_tree().process_frame
		await get_tree().physics_frame
		var bez: Array[RID] = [hrac.get_rid()]
		var p: Vector3 = M.cil_na_zemi(hlavni, cfg, c, bez)
		hrac.velocity = Vector3.ZERO; hrac.position = p + Vector3(0, 0.1, 0)
		for i in 120: await get_tree().physics_frame
		var q := PhysicsRayQueryParameters3D.create(hrac.position + Vector3(0, 1.0, 0), hrac.position - Vector3(0, 5.0, 0)); q.exclude = bez
		var h := hrac.get_world_3d().direct_space_state.intersect_ray(q)
		var nad: float = hrac.position.y - (float(h["position"].y) if not h.is_empty() else -INF)
		var teren: float = hlavni.svet.vyska(hrac.position.x, hrac.position.z)
		var ok: bool = hrac.is_on_floor() and not h.is_empty() and absf(nad) <= 0.5 and hrac.position.y > teren - 0.5
		print("PRUCHOD mapa %s [%.1f, %.1f] y %.2f, teren %.2f, nad podlahou %.2f, na zemi %s -> %s" % [m["nazev"], hrac.position.x, hrac.position.z, hrac.position.y, teren, nad, hrac.is_on_floor(), "OK" if ok else "CHYBA"])
		if not ok: spatne.append("%s (y %.2f, terén %.2f, nad %.2f, na zemi %s)" % [m["nazev"], hrac.position.y, teren, nad, hrac.is_on_floor()])
	# Míša 14. 11.: jízda po mapě po cestách a zastavení kdekoli – bod v 40 % každé trasy (od posledního místa), hráč na zemi
	var mp: Node = M.new(); add_child(mp); mp.hrac = hrac
	for m: Dictionary in body:
		if not m.has("pohled"): continue
		var od := Vector2(hrac.position.x, hrac.position.z)
		var tr: PackedVector2Array = mp.trasa(od, m["cil"])
		var L: float = mp._delka(tr)
		mp._zacni_jizdu(m); mp._jizda["s"] = L * 0.4
		var c2: Vector2 = mp._bod_trasy(L * 0.4)
		M.priprav_kolize(hlavni, c2)
		hlavni.svet._t = 1.0
		await get_tree().process_frame
		await get_tree().physics_frame
		var bez2: Array[RID] = [hrac.get_rid()]
		var p2: Vector3 = M.cil_na_zemi(hlavni, cfg, c2, bez2)
		hrac.velocity = Vector3.ZERO; hrac.position = p2 + Vector3(0, 0.1, 0)
		for i in 120: await get_tree().physics_frame
		var teren2: float = hlavni.svet.vyska(hrac.position.x, hrac.position.z)
		var ok2: bool = hrac.is_on_floor() and hrac.position.y > teren2 - 0.5 and L > 0.0 and L < float(cfg["cestovani"]["test_max_trasa_m"])
		print("PRUCHOD mapa_jizda -> %s: trasa %.0f m (vzdušně %.0f), zastaveno [%.1f, %.1f] y %.2f terén %.2f na zemi %s -> %s" % [m["nazev"], L, od.distance_to(m["cil"]), hrac.position.x, hrac.position.z, hrac.position.y, teren2, hrac.is_on_floor(), "OK" if ok2 else "CHYBA"])
		if not ok2: spatne.append("jízda %s zastavena v [%.1f, %.1f] (y %.2f, terén %.2f, trasa %.0f m)" % [m["nazev"], c2.x, c2.y, hrac.position.y, teren2, L])
		mp._jizda = {}
	mp.queue_free()
	vysledek["mapa_cestovani"] = "OK" if spatne.is_empty() and body.size() >= 6 else "CHYBA: %s" % ("; ".join(spatne) if not spatne.is_empty() else "málo míst (%d)" % body.size())
	print("PRUCHOD mapa_cestovani ", vysledek["mapa_cestovani"])

## zebrik_lezeni (Míša 14. 11.: „na půdu hájovny se dá vylézt po žebříku v předsíni“): pro každý žebřík z dat (hlavni.zebriky)
## postava stojí na nástupu – nabídka žebříku musí být na dosah (zebriky.gd nejblizsi, dole), chytí se, dotyk nahoru – musí
## vystoupit nahoře na podlaze (±0,5 m od sestupu, na zemi); pak nabídka nahoře, dotyk dolů – zpět na podlahu u nástupu.
func _test_zebriky() -> void:
	var Z: GDScript = load("res://scripts/zebriky.gd")
	var spatne: Array = []; var zvenku_n := 0
	var zbs: Array = hlavni.zebriky
	# počet (Míša 15. 11.: „chci všechny žebříky ve hře funkční“): každý vložený dům, jehož model má žebřík v mista.json
	# modely.domy.zebriky, a každý celek se záznamem zebrik musí mít žebřík v hlavni.zebriky
	var ms: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista_stavby.json"))
	var zd: Dictionary = (ms["modely"]["domy"] as Dictionary).get("zebriky", {}); var cekano := 0
	for st: Dictionary in ms["stavby"]:
		if st.has("soubor"):
			if st.get("zebrik") != null and ResourceLoader.exists(String(st["soubor"])): cekano += 1
		elif (zd.get(String(st["model"]), []) as Array).size() == 4: cekano += 1
	if zbs.size() != cekano: spatne.append("žebříků ve hře %d, v datech %d" % [zbs.size(), cekano])
	print("PRUCHOD zebrik počet: ve hře %d, v datech (domy s modelem v modely.domy.zebriky + celky se zebrik) %d" % [zbs.size(), cekano])
	for zb: Dictionary in zbs:
		var pod := Vector3((zb["sestup"] as Vector3).x, (zb["nastup"] as Vector3).y, (zb["sestup"] as Vector3).z)   # místnost pod sestupem (komora): ne „Slézt dolů“
		var up: Dictionary = Z.nejblizsi(zbs, pod)
		if not up.is_empty() and bool(up["nahore"]): spatne.append("%s: pod povalou nabízí Slézt dolů" % zb["nazev"])
		# zvenku přes zeď (Míša 15. 11.: „nemůžu lézt po žebříku, který je uvnitř, zvenku“): hráč za nejbližší vnější stěnou,
		# dívá se na patu – nabídka nesmí být
		var pata_pos: Vector3 = Z.mista_pouziti(zb)[0]["pos"]
		var stena := false   # paprsek musí v některém směru najít stěnu – jinak kontrola neproběhla (CHYBA, ne tiché přeskočení)
		for sm: Vector3 in [Vector3(1, 0, 0), Vector3(-1, 0, 0), Vector3(0, 0, 1), Vector3(0, 0, -1)]:
			var q := PhysicsRayQueryParameters3D.create(pata_pos, pata_pos + sm * 3.0)
			var ex_zb: Array[RID] = [hrac.get_rid()]
			if zb.get("telo") != null: ex_zb.append((zb["telo"] as CollisionObject3D).get_rid())   # kolize samotného žebříku (č. 316) není vnější stěna
			q.exclude = ex_zb
			var hh := hrac.get_world_3d().direct_space_state.intersect_ray(q)
			if hh.is_empty(): continue
			stena = true; zvenku_n += 1
			var venku: Vector3 = (hh["position"] as Vector3) + sm * 0.7
			hlavni.svet.kolize_ihned(venku); hrac.velocity = Vector3.ZERO; hrac.position = Vector3(venku.x, (zb["nastup"] as Vector3).y, venku.z)
			await get_tree().physics_frame; await get_tree().physics_frame
			hrac.pohled_na(pata_pos)
			var zv: Dictionary = Z.nejblizsi(zbs, hrac.global_position, hrac.cam)
			if not zv.is_empty(): spatne.append("%s: zvenku přes stěnu (%.1f m) nabízí žebřík" % [zb["nazev"], (hh["position"] as Vector3).distance_to(pata_pos)])
			break
		if not stena: spatne.append("%s: kontrola zvenku přes stěnu – paprsek od paty v žádném směru nenašel stěnu do 3 m" % zb["nazev"])
		for nahoru: bool in [true, false]:
			var start: Vector3 = zb["nastup"] if nahoru else zb["sestup"]; var cil: Vector3 = zb["sestup"] if nahoru else zb["nastup"]
			hlavni.svet.kolize_ihned(start)
			hrac.autopilot = Vector3.INF; hrac.velocity = Vector3.ZERO; hrac.position = start + Vector3(0, 0.1, 0)
			for i in 60: await get_tree().physics_frame
			var jm := "%s %s" % [zb["nazev"], "nahoru" if nahoru else "dolů"]
			var mp: Array = Z.mista_pouziti(zb)
			hrac.pohled_na(mp[1 if not nahoru else 0]["pos"]); await get_tree().physics_frame   # zaměřit žebřík (zamer.gd)
			var u: Dictionary = Z.nejblizsi(zbs, hrac.global_position, hrac.cam)
			if u.is_empty() or bool(u["nahore"]) == nahoru:
				spatne.append("%s: u %s není nabídka (hráč y %.2f)" % [jm, "paty" if nahoru else "vrcholu", hrac.position.y]); continue
			hrac.chyt_zebrik(u["zb"], bool(u["nahore"]))
			hrac._pohyb = Vector2(0, -1.0 if nahoru else 1.0)
			var n := 0
			while hrac.leze and n < 600: await get_tree().physics_frame; n += 1
			hrac._pohyb = Vector2.ZERO
			for i in 60: await get_tree().physics_frame
			var ok: bool = not hrac.leze and hrac.is_on_floor() and absf(hrac.position.y - cil.y) < 0.5 and Vector2(hrac.position.x - cil.x, hrac.position.z - cil.z).length() < 1.5
			print("PRUCHOD zebrik %s: %d snímků, konec [%.2f, %.2f, %.2f], cíl [%.2f, %.2f, %.2f], na zemi %s -> %s" % [jm, n, hrac.position.x, hrac.position.z, hrac.position.y, cil.x, cil.z, cil.y, hrac.is_on_floor(), "OK" if ok else "CHYBA"])
			if not ok: spatne.append("%s: konec y %.2f místo %.2f (leze %s, na zemi %s)" % [jm, hrac.position.y, cil.y, hrac.leze, hrac.is_on_floor()])
	print("PRUCHOD zebrik zvenku přes stěnu zkontrolováno %d z %d" % [zvenku_n, zbs.size()])
	vysledek["zebrik_lezeni"] = "OK" if spatne.is_empty() and not zbs.is_empty() else "CHYBA: %s" % ("; ".join(spatne) if not spatne.is_empty() else "žádný žebřík v datech")
	print("PRUCHOD zebrik_lezeni ", vysledek["zebrik_lezeni"])


## nevylezt (č. 330; zadání 15. 11. k č. 315: krok nahoru „nesmí vyskakovat na hrany zdí a zábradlí“): na vodorovných úsecích
## tras ochozů a pavlače (kontroly_hra.json nevylezt) postava jde kolmo proti předprsni / zábradlí / zdi – nesmí vystoupat.
func _test_nevylezt() -> void:
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/kontroly_hra.json"))["nevylezt"]
	var space := hrac.get_world_3d().direct_space_state
	var spatne: Array = []; var zk := 0; var horsi := 0.0
	for jm in trasy:
		if not (cfg["trasy"] as Array).any(func(pr_): return String(jm).begins_with(pr_)): continue
		var body: Array = trasy[jm]
		for i in body.size() - 1:
			var a: Array = body[i]; var b: Array = body[i + 1]
			if a[2] == null or b[2] == null or absf(float(a[2]) - float(b[2])) > 0.05: continue   # jen vodorovné úseky (ne schody)
			var pa := Vector3(a[0], float(a[2]), a[1]); var pb := Vector3(b[0], float(b[2]), b[1])
			var L := Vector2(pb.x - pa.x, pb.z - pa.z).length()
			if L < 1.0: continue
			var t := Vector3(pb.x - pa.x, 0, pb.z - pa.z).normalized(); var kolmo := Vector3(-t.z, 0, t.x)
			var nb := maxi(1, int(L / float(cfg["krok_bodu_m"])))
			for k in nb:
				var p := pa.lerp(pb, (k + 0.5) / nb)
				hlavni.svet.kolize_ihned(p)
				var qd := PhysicsRayQueryParameters3D.create(p + Vector3(0, 1.0, 0), p - Vector3(0, 1.0, 0)); qd.exclude = [hrac.get_rid()]
				var hd := space.intersect_ray(qd)
				if hd.is_empty(): continue
				var pod: Vector3 = hd["position"]
				for sm: Vector3 in [kolmo, -kolmo]:
					var z0 := pod + Vector3(0, float(cfg["vyska_paprsku_m"]), 0)
					var qs := PhysicsRayQueryParameters3D.create(z0, z0 + sm * float(cfg["dosah_m"])); qs.exclude = [hrac.get_rid()]
					var hs := space.intersect_ray(qs)
					if hs.is_empty() or absf((hs["normal"] as Vector3).y) > 0.5: continue   # bez svislé překážky (otevřený okraj) – nezkouší se (spadl by)
					hrac.autopilot = Vector3.INF; hrac.velocity = Vector3.ZERO; hrac.position = pod + Vector3(0, 0.05, 0)
					for f_ in 20: await get_tree().physics_frame
					if not hrac.is_on_floor(): continue
					var y0 := hrac.position.y; var ymax := y0
					var cil: Vector3 = (hs["position"] as Vector3) + sm * 1.0
					hrac.autopilot = Vector3(cil.x, 0, cil.z)
					for f_ in int(float(cfg["chuze_s"]) * Engine.physics_ticks_per_second):
						await get_tree().physics_frame
						ymax = maxf(ymax, hrac.position.y)
					hrac.autopilot = Vector3.INF
					zk += 1; horsi = maxf(horsi, ymax - y0)
					if ymax - y0 > float(cfg["max_stoupani_m"]):
						spatne.append("%s [%.2f, %.2f] proti %s vystoupala o %.2f m" % [jm, p.x, p.z, (hs["collider"] as Node).get_parent().name + "/" + (hs["collider"] as Node).name, ymax - y0])
	hrac.velocity = Vector3.ZERO
	vysledek["nevylezt"] = "OK" if spatne.is_empty() and zk >= int(cfg["min_zkousek"]) else "CHYBA: zkoušek %d; %s" % [zk, "; ".join(spatne.slice(0, 12)) if not spatne.is_empty() else "málo zkoušek"]
	print("PRUCHOD nevylezt ", vysledek["nevylezt"], " (zkoušek %d, nejvíc stoupla %.2f m)" % [zk, horsi])

## lavice_sezeni (Míša 15. 11.: „u modelů domů jsou někdy součástí modelu lavičky, tak ať jsou taky funkční“): pro každé místo
## k sezení z hlavni.lavice (lavice.gd z kolizí modelů) hráč stojí před lavicí, dívá se na místo – nabídka „Sednout si“ musí být
## (lavice.gd nejblizsi se zaměřením), sedne (seated, kamera oci_nad_sedu_m nad sedem ±0,05 m), pohne páčkou – vstane, stojí
## na podlaze (is_on_floor, ±0,5 m od podlahy lavice) a kapsle nikde nenarazí.
func _test_lavice() -> void:
	var L: GDScript = load("res://scripts/lavice.gd")
	var spatne: Array = []
	var mista_: Array = hlavni.lavice
	var oci := float(Pravidla.cti("hrac", "sezeni", "oci_nad_sedu_m"))
	var lavic := {}
	for m: Dictionary in mista_:
		lavic[m["lavice"]] = true
		var jm := "%s [%.1f, %.1f]" % [m["lavice"], (m["pos"] as Vector3).x, (m["pos"] as Vector3).z]
		var stoj: Vector3 = m["vstat"]
		hlavni.svet.kolize_ihned(stoj)
		# podlaha pod místem vstání: lavice na podlaze = spodek kvádru; sedátko v nice okna hradu (hrady.py okno_palace) leží na
		# dně niky nad podlahou místnosti – vstává se na podlahu pod ním (Míša 15. 11.: sedátka v nikách jako lavice)
		var pod_ := hrac.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(stoj + Vector3.UP * 0.2, stoj - Vector3.UP * 3.0, 0xFFFFFFFF, [hrac.get_rid()]))
		if not pod_.is_empty(): stoj = pod_["position"]
		hrac.autopilot = Vector3.INF; hrac.velocity = Vector3.ZERO
		hrac.postav_na_volne(stoj + Vector3(0, 0.05, 0))
		for i in 20: await get_tree().physics_frame
		hrac.pohled_na(m["pos"]); await get_tree().physics_frame
		var u: Dictionary = L.nejblizsi(mista_, hrac.global_position, hrac.cam)
		if u.is_empty() or (u["m"] as Dictionary)["lavice"] != m["lavice"]:
			spatne.append("%s: není nabídka Sednout si (hráč [%.2f, %.2f, %.2f])" % [jm, hrac.position.x, hrac.position.z, hrac.position.y]); continue
		L.sedni(hrac, u["m"])
		for i in 60: await get_tree().physics_frame
		var sed: Vector3 = (u["m"] as Dictionary)["pos"]
		var vk: float = hrac.cam.global_position.y - sed.y
		if not hrac.seated or absf(vk - oci) > 0.05 or Vector2(hrac.position.x - sed.x, hrac.position.z - sed.z).length() > 0.05:
			spatne.append("%s: nesedí (seated %s, oči %.2f m nad sedem)" % [jm, hrac.seated, vk]); hrac.stand_up(); continue
		hrac._pohyb = Vector2(0, -1.0)   # páčka = vstát (Havran)
		for i in 3: await get_tree().physics_frame
		hrac._pohyb = Vector2.ZERO
		for i in 40: await get_tree().physics_frame
		var q := PhysicsShapeQueryParameters3D.new(); q.shape = hrac._col.shape; q.exclude = [hrac.get_rid()]
		q.transform = Transform3D(Basis(), hrac.global_position + hrac._col.position + Vector3(0, 0.02, 0))
		var v_kolizi: bool = not hrac.get_world_3d().direct_space_state.intersect_shape(q, 1).is_empty()
		var ok: bool = not hrac.seated and hrac.is_on_floor() and not v_kolizi and absf(hrac.position.y - stoj.y) < 0.5
		print("PRUCHOD lavice %s: oči %.2f, vstal [%.2f, %.2f, %.2f], na zemi %s, v kolizi %s -> %s" % [jm, vk, hrac.position.x, hrac.position.z, hrac.position.y, hrac.is_on_floor(), v_kolizi, "OK" if ok else "CHYBA"])
		if not ok: spatne.append("%s: po vstání seated %s, na zemi %s, v kolizi %s, y %.2f (podlaha %.2f)" % [jm, hrac.seated, hrac.is_on_floor(), v_kolizi, hrac.position.y, stoj.y])
	vysledek["lavice_sezeni"] = "OK" if spatne.is_empty() and not mista_.is_empty() else "CHYBA: %s" % ("; ".join(spatne) if not spatne.is_empty() else "žádná lavice v modelech")
	print("PRUCHOD lavice_sezeni ", vysledek["lavice_sezeni"], " (lavic %d, míst %d)" % [lavic.size(), mista_.size()])

## Funkční věci (funkce.gd) jako ve hře: uzel s vlastní vrstvou tlačítek, položky ze světa
var _fu: Node = null
func _funkce() -> Node:
	if _fu == null:
		var cl := CanvasLayer.new(); add_child(cl)
		_fu = load("res://scripts/funkce.gd").new(); cl.add_child(_fu); _fu.zacni(hlavni, cl)
	return _fu

## Postavit hráče na podlahu u bodu cil (paprsek dolů bez vyjma, pak postav_na_volne) a zamířit na něj; vrátí nabídku funkce.gd
func _k_veci(cil: Vector3, od: Vector3, vyjma: Array = []) -> Dictionary:
	var F: GDScript = load("res://scripts/funkce.gd")
	hlavni.svet.kolize_ihned(od)
	hrac.autopilot = Vector3.INF; hrac.velocity = Vector3.ZERO
	var q := PhysicsRayQueryParameters3D.create(od + Vector3(0, 0.5, 0), od - Vector3(0, 3.0, 0)); q.exclude = vyjma + [hrac.get_rid()]
	var hh := hrac.get_world_3d().direct_space_state.intersect_ray(q)
	var pod: Vector3 = (hh["position"] as Vector3) if not hh.is_empty() else od
	hrac.postav_na_volne(pod + Vector3(0, 0.05, 0))
	for i in 20: await get_tree().physics_frame
	hrac.pohled_na(cil); await get_tree().physics_frame
	return F.nejblizsi(_funkce().polozky_, hrac.cam)

## Bod podlahy 0,9 m od věci směrem ke středu stavby (kořen instance) – tam stojí hráč, který věc používá
static func _pred(p: Vector3, koren: Node3D, y_podlahy: float, od_m := 0.9) -> Vector3:
	var k := koren.global_position - p; k.y = 0.0
	var q := p + k.normalized() * od_m
	return Vector3(q.x, y_podlahy, q.z)

## kovarna_mech (Míša 15. 11.: „dmychadlo v kovárně“; Havran kovarna_mech.gd): u úchopu páky nabídka „Foukat měchem“, po stisku
## se páka otáčí a měch nadechuje (tvar Nadech), výheň kovárny se rozhoří (ohne.gd boost, plamen větší), po pumpovat_s se měch vrátí do klidu.
func _test_mech() -> void:
	var fu := _funkce(); var spatne: Array = []; var n := 0
	var me: Dictionary = Pravidla.cti("funkce", "mech")
	for p: Dictionary in fu.polozky_:
		if p["druh"] != "mech": continue
		n += 1
		var kor: Node3D = p["koren"]
		var u: Dictionary = await _k_veci(p["pos"], _pred(p["pos"], kor, kor.global_position.y))
		if u.is_empty() or u["p"] != p:
			spatne.append("%s: není nabídka %s (hráč [%.2f, %.2f, %.2f])" % [kor.name, me["nabidka"], hrac.position.x, hrac.position.z, hrac.position.y]); continue
		fu.pouzij_polozku(p)
		var mx := 0.0; var uh := 0.0; var boost := 0.0; var plamen := 1.0
		for i in 60:   # 3 s (víc než jeden tah: 2π / tempo_rad_s)
			await get_tree().create_timer(0.05).timeout
			mx = maxf(mx, (p["mech"] as MeshInstance3D).get_blend_shape_value(int(p["tvar"])) if int(p["tvar"]) >= 0 else 0.0)
			uh = maxf(uh, ((p["paka"] as Node3D).transform.basis.get_rotation_quaternion().angle_to((p["zaklad"] as Basis).get_rotation_quaternion())))
			var oh: Node = hlavni.get_node_or_null("Ohne")
			if oh:
				for o: Dictionary in oh.ohne:
					if is_instance_valid(o.get("uzel")) and kor.is_ancestor_of(o["uzel"]):
						boost = maxf(boost, float(o["boost"]))
						if o.has("plamen"): plamen = maxf(plamen, (o["plamen"] as Node3D).scale.y)
		await get_tree().create_timer(float(me["pumpovat_s"]) + 2.0).timeout
		var klid: bool = not fu.mech_bezi(p) and ((p["mech"] as MeshInstance3D).get_blend_shape_value(int(p["tvar"])) < 0.05 if int(p["tvar"]) >= 0 else true)
		var ok: bool = int(p["tvar"]) >= 0 and mx > 0.5 and uh > float(me["uhel_rad"]) * 0.5 and boost > 0.0 and plamen > 1.05 and klid
		print("PRUCHOD mech %s: nadech max %.2f, páka %.3f rad, výheň rozhoření %.2f, plamen ×%.2f, klid po pumpování %s -> %s" % [kor.name, mx, uh, boost, plamen, klid, "OK" if ok else "CHYBA"])
		if not ok: spatne.append("%s: nadech %.2f, páka %.3f, rozhoření %.2f, plamen %.2f, klid %s" % [kor.name, mx, uh, boost, plamen, klid])
	vysledek["kovarna_mech"] = "OK" if spatne.is_empty() and n > 0 else "CHYBA: %s" % ("; ".join(spatne) if not spatne.is_empty() else "žádný měch ve světě")
	print("PRUCHOD kovarna_mech ", vysledek["kovarna_mech"], " (měchů %d)" % n)

## spanek (Míša 15. 11.: spánek „ano, jako Havran“): u každého místa spánku nabídka „Lehnout si“ (zaměřené), hráč si lehne
## (seated, oči oci_m nad bodem lehu), přespí do rána (funkce.gd spi_do: den.gd doba rano), pak stojí na podlaze bez kolize.
func _test_spanek() -> void:
	var fu := _funkce(); var spatne: Array = []; var n := 0
	var sp: Dictionary = Pravidla.cti("funkce", "spanek")
	for p: Dictionary in fu.polozky_:
		if p["druh"] != "spani": continue
		n += 1
		var zn: Node3D = p["znacka"]; var jm := "%s %s" % [p["misto"], zn.get_parent().name]
		var q := PhysicsRayQueryParameters3D.create(zn.global_position, zn.global_position - Vector3(0, 3.0, 0)); q.exclude = p["vlastni"] + [hrac.get_rid()]
		var hh := hrac.get_world_3d().direct_space_state.intersect_ray(q)
		var podlaha: float = (hh["position"] as Vector3).y if not hh.is_empty() else zn.global_position.y - 0.6
		var inst: Node3D = zn
		while not (inst.get_parent() is Node3D) or not String(inst.get_parent().name) in ["Mista", "Ves"]: inst = inst.get_parent()
		var u: Dictionary = await _k_veci(p["pos"], _pred(zn.global_position, inst, podlaha, 1.4) if not (p["vlastni"] as Array).is_empty() else Vector3(zn.global_position.x, podlaha, zn.global_position.z), p["vlastni"])   # lůžko s kolizí: stát vedle něj směrem do stavby
		if u.is_empty() or u["p"] != p:
			spatne.append("%s: není nabídka %s (hráč [%.2f, %.2f, %.2f])" % [jm, sp["nabidka"], hrac.position.x, hrac.position.z, hrac.position.y]); continue
		var stal := hrac.global_position
		fu.lehni(p)
		for i in 60: await get_tree().physics_frame
		var oci: float = hrac.cam.global_position.y - (p["leh"] as Vector3).y
		var lezi: bool = hrac.seated and absf(oci - float(sp["oci_m"])) < 0.05
		await fu.spi_do("rano")
		for i in 40: await get_tree().physics_frame
		var den: Node = hlavni.get("den")
		var rano: bool = den != null and String(den.current) == "rano"
		var qs := PhysicsShapeQueryParameters3D.new(); qs.shape = hrac._col.shape; qs.exclude = [hrac.get_rid()]
		qs.transform = Transform3D(Basis(), hrac.global_position + hrac._col.position + Vector3(0, 0.02, 0))
		var v_kolizi: bool = not hrac.get_world_3d().direct_space_state.intersect_shape(qs, 1).is_empty()
		var ok: bool = lezi and rano and not hrac.seated and hrac.is_on_floor() and not v_kolizi and absf(hrac.position.y - stal.y) < 0.5
		print("PRUCHOD spanek %s: leží %s (oči %.2f), ráno %s (%s), vstal [%.2f, %.2f, %.2f], na zemi %s, v kolizi %s -> %s" % [jm, lezi, oci, rano, den.clock_text() if den else "?", hrac.position.x, hrac.position.z, hrac.position.y, hrac.is_on_floor(), v_kolizi, "OK" if ok else "CHYBA"])
		if not ok: spatne.append("%s: leží %s, ráno %s, seated %s, na zemi %s, v kolizi %s" % [jm, lezi, rano, hrac.seated, hrac.is_on_floor(), v_kolizi])
		if den: den.set_time("odpoledne", 0.01)
	vysledek["spanek"] = "OK" if spatne.is_empty() and n >= 2 else "CHYBA: %s" % ("; ".join(spatne) if not spatne.is_empty() else "málo míst spánku (%d)" % n)
	print("PRUCHOD spanek ", vysledek["spanek"], " (míst %d)" % n)

## zlab_voda (Míša 15. 11.: žlab „nalít vodu“): u žlabu nabídka „Nalít vodu“, po stisku hladina (shader vody) uvnitř půdorysu kolize
## žlabu pod jeho horní hranou; nabídka pak zmizí, voda zůstane.
func _test_zlab() -> void:
	var fu := _funkce(); var spatne: Array = []; var n := 0
	var zl: Dictionary = Pravidla.cti("funkce", "zlab")
	for p: Dictionary in fu.polozky_:
		if p["druh"] != "zlab": continue
		n += 1
		var dum: Node3D = p["dum"]; var ab: AABB = p["aabb"]
		var u: Dictionary = await _k_veci(p["pos"], _pred(p["pos"], dum, (dum.global_transform * ab.position).y), p["vlastni"])
		if u.is_empty() or u["p"] != p:
			spatne.append("%s: není nabídka %s (hráč [%.2f, %.2f, %.2f])" % [dum.name, zl["nabidka"], hrac.position.x, hrac.position.z, hrac.position.y]); continue
		fu.pouzij_polozku(p)
		await get_tree().process_frame
		var mi: MeshInstance3D = p["voda"]
		var ok := mi != null and mi.material_override is ShaderMaterial and String((mi.material_override as ShaderMaterial).shader.resource_path).ends_with("voda.gdshader")
		var vab := AABB()
		if mi != null:
			vab = mi.mesh.get_aabb(); vab.position = mi.transform * vab.position   # síť v souřadnicích domu
			ok = ok and vab.position.x >= ab.position.x and vab.end.x <= ab.end.x and vab.position.z >= ab.position.z and vab.end.z <= ab.end.z \
				and vab.position.y > ab.position.y and vab.position.y < ab.end.y
		var znovu: Dictionary = fu.nejblizsi(fu.polozky_, hrac.cam)
		ok = ok and (znovu.is_empty() or znovu["p"] != p)
		print("PRUCHOD zlab %s: voda %s, hladina y %.2f (žlab %.2f..%.2f) -> %s" % [dum.name, mi != null, vab.position.y, ab.position.y, ab.end.y, "OK" if ok else "CHYBA"])
		if not ok: spatne.append("%s: voda %s, hladina %.2f" % [dum.name, mi != null, vab.position.y])
	vysledek["zlab_voda"] = "OK" if spatne.is_empty() and n > 0 else "CHYBA: %s" % ("; ".join(spatne) if not spatne.is_empty() else "žádný žlab ve světě")
	print("PRUCHOD zlab_voda ", vysledek["zlab_voda"], " (žlabů %d)" % n)

## jesle_seno (Míša 15. 11.: jesle „nasypat seno“, „seno ale fotorealistické“): u jeslí nad žlabem nabídka „Nasypat seno“, po stisku
## model sena Míšina modeláře (funkce.json jesle.model, Seno_Jesle_420) v jeslích: obal LOD0 v souřadnicích domu v délce jeslí,
## vrch nad horním koncem příček, nejníž u dolního konce příček, za roubení (2 cm) nejvýš 1 % vrcholů, přes horní břevno do chléva
## nejvýš 25 cm (stébla přesahují); LOD0 a LOD1 kreslí jen v dosahu (Visibility Range);
## troj. LOD0 ≤ troj_max; nabídka pak zmizí, seno zůstane.
func _test_jesle() -> void:
	var fu := _funkce(); var spatne: Array = []; var n := 0
	var je: Dictionary = Pravidla.cti("funkce", "jesle")
	for p: Dictionary in fu.polozky_:
		if p["druh"] != "jesle": continue
		n += 1
		var dum: Node3D = p["dum"]; var tv: Dictionary = je["tvar"][p["kolize"]]
		var u: Dictionary = await _k_veci(p["pos"], _pred(p["pos"], dum, dum.global_position.y, 1.3))
		if u.is_empty() or u["p"] != p:
			spatne.append("%s: není nabídka %s (hráč [%.2f, %.2f, %.2f])" % [dum.name, je["nabidka"], hrac.position.x, hrac.position.z, hrac.position.y]); continue
		fu.pouzij_polozku(p)
		await get_tree().process_frame
		var uz: Node3D = p["seno"]
		var ok := uz != null and String(uz.scene_file_path) == String(je["model"])
		var ab := AABB(); var troj := 0; var vid_ok := true; var lod0 := 0; var zad := 0; var vse := 0
		if ok:
			var inv := dum.global_transform.affine_inverse()
			for mi: MeshInstance3D in uz.find_children("*", "MeshInstance3D", true, false):
				vid_ok = vid_ok and (mi.visibility_range_end > 0.0 or mi.visibility_range_begin > 0.0)
				if mi.visibility_range_begin > 0.0: continue   # LOD1
				lod0 += 1
				var xf: Transform3D = inv * mi.global_transform   # vrcholy v souřadnicích domu (obal otočené sítě by byl větší než seno)
				for v in mi.mesh.get_faces():
					var q: Vector3 = xf * v
					if vse == 0: ab = AABB(q, Vector3.ZERO)
					else: ab = ab.expand(q)
					vse += 1
					if q.z < float(tv["stena_z"]) - 0.02: zad += 1
				for si in mi.mesh.get_surface_count():
					var ar: Array = mi.mesh.surface_get_arrays(si)
					troj += ((ar[Mesh.ARRAY_INDEX] as PackedInt32Array).size() if ar[Mesh.ARRAY_INDEX] != null else (ar[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3
		var nah: Array = tv["pricky_nahore"]; var dol: Array = tv["pricky_dole"]
		var tvar_ok := ok and lod0 > 0 and ab.position.x >= float(tv["x"][0]) - 0.06 and ab.end.x <= float(tv["x"][1]) + 0.06 \
			and ab.end.y > float(nah[0]) and ab.position.y >= float(dol[0]) - 0.05 and float(zad) <= 0.01 * vse \
			and ab.end.z <= float(nah[1]) + 0.25
		var znovu: Dictionary = fu.nejblizsi(fu.polozky_, hrac.cam)
		ok = ok and vid_ok and tvar_ok and troj > 0 and troj <= int(je["troj_max"]) and (znovu.is_empty() or znovu["p"] != p)
		print("PRUCHOD jesle %s: seno %s, LOD0 x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f, za roubením %.1f %%, troj. LOD0 %d, viditelnost %s -> %s" % [dum.name, uz != null,
			ab.position.x, ab.end.x, ab.position.y, ab.end.y, ab.position.z, ab.end.z, 100.0 * zad / maxi(vse, 1), troj, vid_ok, "OK" if ok else "CHYBA"])
		if not ok: spatne.append("%s: seno %s, tvar %s, troj. %d, viditelnost %s" % [dum.name, uz != null, tvar_ok, troj, vid_ok])
	vysledek["jesle_seno"] = "OK" if spatne.is_empty() and n > 0 else "CHYBA: %s" % ("; ".join(spatne) if not spatne.is_empty() else "žádné jesle ve světě")
	print("PRUCHOD jesle_seno ", vysledek["jesle_seno"], " (jeslí %d)" % n)

## kovadlina_osazena (Míša 15. 11.: nová kovadlina podle KCD2 v kovárně): na každé značce Kovarna_Kovadlina_misto uzel kovadliny
## (funkce.gd osad_kovadliny) se stupni podle vzdálenosti; stojí na podlaze (střed a 8 bodů na obvodu špalku: podlaha pod ním
## nejvýš 3 cm – nevisí, nejvýš 4 cm nad ní – není pod podlahou), má kolizi (paprsek shora narazí na dráhu ve výšce ~0,78 m),
## špalek nezasahuje do jiné kolize kovárny (výheň, měch, sloupy).
func _test_kovadlina() -> void:
	_funkce()
	var kv: Dictionary = Pravidla.cti("funkce", "kovadlina"); var spatne: Array = []; var n := 0
	var dr := float(kv["drah_vyska_m"])
	var prostor := hrac.get_world_3d().direct_space_state
	for k in ["Mista", "Ves"]:
		var kor := hlavni.get_node_or_null(k)
		if kor == null: continue
		for zn: Node3D in kor.find_children(String(kv["bod"]), "Node3D", true, false):
			n += 1
			var uz := zn.get_parent().get_node_or_null(String(kv["uzel"])) as Node3D
			var jm := "%s %s" % [zn.get_parent().name, zn.name]
			if uz == null: spatne.append("%s: kovadlina není osazena" % jm); continue
			hlavni.svet.kolize_ihned(uz.global_position)
			for i in 3: await get_tree().physics_frame
			var tela: Array = uz.find_children("*", "CollisionObject3D", true, false)
			var rid: Array = []
			for t: CollisionObject3D in tela: rid.append(t.get_rid())
			var lod := 0
			for g in uz.find_children("*", "GeometryInstance3D", true, false): if (g as GeometryInstance3D).visibility_range_end > 0.0: lod += 1
			var o := uz.global_position; var pod_max := -1e9; var pod_min := 1e9; var bez := 0
			for i in 9:
				var b := o if i == 0 else o + uz.global_basis * (Vector3(cos(TAU * i / 8.0), 0, sin(TAU * i / 8.0)) * 0.42)
				var q := PhysicsRayQueryParameters3D.create(b + Vector3(0, 0.25, 0), b - Vector3(0, 1.0, 0)); q.exclude = rid + [hrac.get_rid()]
				var hh := prostor.intersect_ray(q)
				if hh.is_empty(): bez += 1; continue
				pod_max = maxf(pod_max, (hh["position"] as Vector3).y); pod_min = minf(pod_min, (hh["position"] as Vector3).y)
			var q2 := PhysicsRayQueryParameters3D.create(o + Vector3(0, 1.6, 0), o); q2.exclude = [hrac.get_rid()]
			var h2 := prostor.intersect_ray(q2)
			var vrch: float = (h2["position"] as Vector3).y - o.y if not h2.is_empty() and rid.has(h2["rid"]) else -1.0
			var qs := PhysicsShapeQueryParameters3D.new(); var cyl := CylinderShape3D.new(); cyl.radius = 0.5; cyl.height = 0.16
			qs.shape = cyl; qs.transform = Transform3D(Basis(), o + Vector3(0, 0.18, 0)); qs.exclude = rid + [hrac.get_rid()]
			var kriz: Array = []
			for c: Dictionary in prostor.intersect_shape(qs, 8): kriz.append(String((c["collider"] as Node).name))
			var nevisi := bez == 0 and o.y - pod_max <= 0.03
			var nad_podlahou := bez == 0 and pod_max - o.y <= 0.04 and o.y - pod_min <= 0.06
			var ok: bool = not tela.is_empty() and nevisi and nad_podlahou and absf(vrch - dr) < 0.06 and lod >= 3 and kriz.is_empty()
			print("PRUCHOD kovadlina %s: [%.2f, %.2f, %.2f], podlaha %.3f..%.3f (bez podlahy %d), dráha (kolize) %.2f m, kolizí %d, stupňů %d, zasahuje do %s -> %s" % [jm, o.x, o.z, o.y,
				pod_min, pod_max, bez, vrch, tela.size(), lod, kriz, "OK" if ok else "CHYBA"])
			if not ok: spatne.append("%s: nevisí %s, nad podlahou %s, dráha %.2f, kolizí %d, stupňů %d, zasahuje %s" % [jm, nevisi, nad_podlahou, vrch, tela.size(), lod, kriz])
	vysledek["kovadlina_osazena"] = "OK" if spatne.is_empty() and n > 0 else "CHYBA: %s" % ("; ".join(spatne) if not spatne.is_empty() else "žádná značka kovadliny ve světě")
	print("PRUCHOD kovadlina_osazena ", vysledek["kovadlina_osazena"], " (kováren %d)" % n)

## studna_vedro (Míša 15. 11.: „co může mít funkci, tak ji mít bude“; Havran blender/studna.py + pohyb.gd vedro): u kliky studny
## nabídka (dvere.gd, zaměřená), „Spustit vědro“ – rumpál se točí, vědro sjede o hloubku k hladině (dvere.gd druh vedro), lano
## končí u ucha vědra; „Vytáhnout vědro“ – vědro zpět nahoru na původní místo.
func _test_studna() -> void:
	var dv: Node = _dvere(); var spatne: Array = []; var n := 0
	var Z := preload("res://scripts/zamer.gd")
	for g: String in dv.dily:
		if dv.druh.get(g, "") != "vedro": continue
		n += 1
		var vedro: Node3D = null; var rumpal: Node3D = null; var lift := 0.0
		for d: Dictionary in dv.dily[g]:
			if String(d["e"]["kind"]) == "vedro": vedro = d["uzel"]; lift = float(d["e"]["lift"])
			else: rumpal = d["uzel"]
		var m: Vector3 = dv.mista[g]
		var sm := m - vedro.global_position; sm.y = 0.0
		var stoj := m + sm.normalized() * 0.7
		hlavni.svet.kolize_ihned(stoj); hrac.autopilot = Vector3.INF; hrac.velocity = Vector3.ZERO
		hrac.postav_na_volne(Vector3(stoj.x, hlavni.svet.vyska(stoj.x, stoj.z), stoj.z))
		for i in 20: await get_tree().physics_frame
		hrac.pohled_na(m); await get_tree().physics_frame
		var vidi: bool = Z.skore(hrac.cam, m, dv.DOSAH + 1.0) >= 0.0 and hrac.cam.global_position.distance_to(m) < dv.DOSAH + 1.0
		var nab: String = dv.popis(g)
		var y0 := vedro.global_position.y; var r0 := rumpal.global_transform.basis
		dv.prepni(g)
		await get_tree().create_timer(float(dv.doba[g]) * 0.5).timeout
		var toci: bool = rumpal.global_transform.basis.get_rotation_quaternion().angle_to(r0.get_rotation_quaternion()) > 0.05
		await get_tree().create_timer(float(dv.doba[g]) * 0.5 + 0.5).timeout
		var dole := vedro.global_position.y
		var lano_ok := true
		for c: Dictionary in dv.lana:
			if c["uzel"] == vedro:
				var konec: Vector3 = vedro.global_transform * (c["e"] as Vector3); var mi: MeshInstance3D = c["mi"]
				lano_ok = absf(mi.global_transform.basis.y.length() - (c["a"] as Vector3).distance_to(konec)) < 0.02
		var nab2: String = dv.popis(g)
		dv.prepni(g); await get_tree().create_timer(float(dv.doba[g]) + 0.5).timeout
		var nahore := vedro.global_position.y
		var ok: bool = vidi and nab == "Spustit vědro" and nab2 == "Vytáhnout vědro" and toci and absf((y0 - dole) + lift) < 0.02 and lano_ok and absf(nahore - y0) < 0.01
		print("PRUCHOD studna %s: nabídka %s (%s / %s), rumpál se točí %s, vědro %.2f -> %.2f (o %.2f m, má %.2f) -> %.2f, lano %s -> %s" % [g, vidi, nab, nab2, toci, y0, dole, y0 - dole, -lift, nahore, lano_ok, "OK" if ok else "CHYBA"])
		if not ok: spatne.append("%s: nabídka %s, točí %s, vědro dolů %.2f m (má %.2f), zpět %.2f, lano %s" % [g, vidi, toci, y0 - dole, -lift, nahore - y0, lano_ok])
	vysledek["studna_vedro"] = "OK" if spatne.is_empty() and n > 0 else "CHYBA: %s" % ("; ".join(spatne) if not spatne.is_empty() else "žádná studna s vědrem")
	print("PRUCHOD studna_vedro ", vysledek["studna_vedro"], " (studní %d)" % n)

## zajimava_mista (Míša 15. 11., docs/zajimava_mista_plan.md): každé místo z hra/data/zajimava_mista.json je ve hře (uzel Z_<id>
## s díly), díly stojí na terénu (počátek dílu do tolerance nad/pod viditelnou výškou – nevisí, nejsou pod zemí; zemljanky,
## štola a mlýn mají vlastní jámy/zářezy a hlídají je trasy průchodu), studánka nabízí „Napít se“ a „Nabrat vodu“ a obojí jde použít.
func _test_zajimava() -> void:
	var spatne: Array = []; var zj: Node = hlavni.get_node_or_null("Zajimava")
	if zj == null or not FileAccess.file_exists("res://data/zajimava_mista.json"):
		vysledek["zajimava_mista"] = "CHYBA: zajímavá místa nejsou ve hře"; print("PRUCHOD zajimava_mista ", vysledek["zajimava_mista"]); return
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/zajimava_mista.json"))
	var n := 0
	for m: Dictionary in d["mista"]:
		var u := zj.get_node_or_null("Z_" + String(m["id"])) as Node3D
		if u == null or u.get_child_count() == 0: spatne.append("%s: chybí ve hře" % m["id"]); continue
		for di: Dictionary in m["dily"]:
			if di.get("zemljanka", false) or String(di.get("model", "")) in ["stola", "mlyn"] or di.has("strom"): continue
			var t := hlavni.svet.vyska(float(di["x"]), float(di["z"])) as float
			n += 1
			if di.get("predmet", "") == "truhla": continue   # truhla v zemljance stojí na podlaze jámy (kolize terénu tam snížená)
			var dy := float(di["y"]) - t
			if dy > 0.6 or dy < -0.6: spatne.append("%s %s: y %.2f, terén %.2f" % [m["id"], di.get("model", di.get("predmet", di.get("balvan", "?"))), float(di["y"]), t])
	# studánka: nabídky a použití
	var fu := _funkce(); var ns := 0
	for p: Dictionary in fu.polozky_:
		if not String(p["druh"]).begins_with("studanka"): continue
		ns += 1
		var u2: Dictionary = await _k_veci(p["pos"], p["pos"] + Vector3(0, 0, 1.4), p["vlastni"])
		if u2.is_empty() or u2["p"]["druh"] != p["druh"]:
			for sm in [Vector3(1.3, 0, 0), Vector3(-1.3, 0, 0), Vector3(0, 0, -1.3), Vector3(0.9, 0, 0.9), Vector3(-0.9, 0, 0.9)]:
				u2 = await _k_veci(p["pos"], p["pos"] + sm, p["vlastni"])
				if not u2.is_empty() and u2["p"]["druh"] == p["druh"]: break
		if u2.is_empty() or u2["p"]["druh"] != p["druh"]: spatne.append("studánka: není nabídka %s" % p["nazev"]); continue
		fu.pouzij_polozku(p)
		var ok := int(p.get("napito", 0)) + int(p.get("nabrano", 0)) > 0
		print("PRUCHOD studanka %s: nabídka %s -> %s" % [p["druh"], p["nazev"], "OK" if ok else "CHYBA"])
		if not ok: spatne.append("studánka %s nejde použít" % p["nazev"])
	if ns < 2: spatne.append("studánka: nabídek %d (čeká se Napít se + Nabrat vodu)" % ns)
	vysledek["zajimava_mista"] = "OK" if spatne.is_empty() else "CHYBA: %s" % "; ".join(spatne)
	print("PRUCHOD zajimava_mista ", vysledek["zajimava_mista"], " (míst %d, dílů na terénu %d, nabídek studánky %d)" % [d["mista"].size(), n, ns])

func _chyba(t: String) -> void:
	for i in hrac.get_slide_collision_count():
		var c := hrac.get_slide_collision(i)
		t += " | narazila na %s v [%.2f, %.2f, %.2f] normála [%.2f, %.2f, %.2f]" % [c.get_collider().get_parent().name if c.get_collider() else "?", c.get_position().x, c.get_position().z, c.get_position().y, c.get_normal().x, c.get_normal().y, c.get_normal().z]
	vysledek[jmena[ti]] = "CHYBA: " + t; print("PRUCHOD ", jmena[ti], " CHYBA ", t)
	ti += 1; _start_trasy()

func _konec() -> void:
	var jen := OS.get_environment("PUCHART_JEN")
	if jen == "" or "kmene" in jen: await _test_kmene()
	if jen == "" or "povrch" in jen: await _test_povrch()
	if jen == "" or "vrata" in jen: await _test_vrata()
	if jen == "" or "mapa" in jen: await _test_mapa()
	if jen == "" or "nevylezt" in jen: await _test_nevylezt()
	if jen == "" or "zebrik" in jen: await _test_zebriky()
	if jen == "" or "lavice" in jen: await _test_lavice()
	if jen == "" or "mech" in jen: await _test_mech()
	if jen == "" or "spanek" in jen: await _test_spanek()
	if jen == "" or "zlab" in jen: await _test_zlab()
	if jen == "" or "jesle" in jen: await _test_jesle()
	if jen == "" or "studna" in jen: await _test_studna()
	if jen == "" or "kovadlina" in jen: await _test_kovadlina()
	if jen == "" or "zajimava" in jen: await _test_zajimava()
	hrac.autopilot = Vector3.INF
	var f := FileAccess.open(OS.get_environment("PUCHART_VYSTUP") if OS.has_environment("PUCHART_VYSTUP") else "user://pruchod.json", FileAccess.WRITE); f.store_string(JSON.stringify(vysledek, " "))
	var ok := vysledek.values().all(func(v): return v == "OK")
	print("PRUCHOD VYSLEDEK ", "OK" if ok else "CHYBA", " ", vysledek)
	get_tree().quit(0 if ok else 1)


var _clony: Array = []
func _pod_stavbou(q: Vector3) -> bool:   # bod uvnitř půdorysu zdiva (kolizní kvádry > 2 m, hra/data/stavby_clony.json) a pod jeho vrchem
	if _clony.is_empty() and FileAccess.file_exists("res://data/stavby_clony.json"):
		for k in JSON.parse_string(FileAccess.get_file_as_string("res://data/stavby_clony.json"))["kvadry"]:
			var pl := PackedVector2Array()
			for r in k["rohy"]: pl.append(Vector2(r[0], r[1]))
			_clony.append([pl, float(k["vrch"])])
	for c in _clony:
		if q.y < float(c[1]) - 0.3 and Geometry2D.is_point_in_polygon(Vector2(q.x, q.z), c[0]): return true
	return false

