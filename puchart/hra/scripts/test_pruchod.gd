extends Node
## Test průchodu hradem (PUCHART_TEST=pruchod): postava sama projde trasy z data/pruchody.json (generuje je stavitel
## hradu ze stejné geometrie) – mosty, brány, nádvoří, schody, ochozy, věže. U každého bodu musí být do 0,6 m
## vodorovně (nebo podle 4. čísla bodu) a ve výšce podlahy (±0,5 m); když 3 s nepostoupí o 5 cm, uvízla. Výsledek: stdout + user://pruchod.json.
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
	hrac.set_physics_process(true)
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
func _test_povrch() -> void:
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
	for vr: Node in vrstvy:
		for m in vr.find_children("*", "MeshInstance3D", true, false):
			var mi := m as MeshInstance3D
			if mi.mesh == null or String(mi.name).begins_with("KOLIZE") or String(mi.get_parent().name).begins_with("Pohyb"):
				continue
			for si in mi.mesh.get_surface_count():   # hladina se neprochází po povrchu (brodí se) – bez ní
				var mat := mi.get_active_material(si)
				if mat != null and String(mat.resource_name) in cfg["bez_materialu"]: continue
				var am := ArrayMesh.new(); am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, mi.mesh.surface_get_arrays(si))
				var tm := am.generate_triangle_mesh()
				if tm != null: site.append([tm, mi.global_transform.affine_inverse(), mi.global_transform, (mi.global_transform * am.get_aabb()).grow(3.0)])
	print("POVRCH sítí %d, příprava %d ms" % [site.size(), Time.get_ticks_msec() - _t0])
	var space := hrac.get_world_3d().direct_space_state
	var n := 0; var spatne: Array = []; var horsi := 0.0; var sten := 0; var vse: Array = []
	var tr_vse: Dictionary = trasy.duplicate()
	var sk: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/skaly_body.json"))["skaly"]
	for i in range(0, sk.size(), int(cfg["skaly_kazda"])):
		var c: Array = sk[i]["stred"]
		tr_vse["skala_%d" % i] = [[c[0] - 1.0, c[1], null], [c[0] + 1.0, c[1], null]]
	for jm in tr_vse:
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
				var vis: float = hlavni.svet.vyska(p.x, p.z)
				var blizko := site.filter(func(e): var bb: AABB = e[3]; return p.x >= bb.position.x and p.x <= bb.end.x and p.z >= bb.position.z and p.z <= bb.end.z)
				for s in blizko:
					var lo: Vector3 = s[1] * od; var ld: Vector3 = (s[1] * do_) - lo
					var r: Dictionary = (s[0] as TriangleMesh).intersect_ray(lo, ld.normalized())
					if not r.is_empty():
						var w: Vector3 = s[2] * (r["position"] as Vector3)
						if w.y <= od.y and w.y >= do_.y: vis = maxf(vis, w.y)
				if h.is_empty(): continue
				n += 1
				if n % 100 == 0: print("POVRCH bod %d za %d ms" % [n, Time.get_ticks_msec() - _t0])
				if k % int(cfg["steny_kazdy"]) == 0:   # zdi: vodorovně v 8 směrech, viditelná stěna a kolize hradu musí sedět
					for v in [1.0, 1.7]:
						for u in 8:
							var sm := Vector3(cos(u * PI / 4), 0, sin(u * PI / 4)); var z0 := Vector3(p.x, h["position"].y + v, p.z)
							var dv := INF
							for s in blizko:
								var lo: Vector3 = s[1] * z0; var r: Dictionary = (s[0] as TriangleMesh).intersect_ray(lo, (s[1].basis * sm).normalized())
								if not r.is_empty(): dv = minf(dv, z0.distance_to(s[2] * (r["position"] as Vector3)))
							var qs := PhysicsRayQueryParameters3D.create(z0, z0 + sm * float(cfg["steny_dosah_m"])); qs.exclude = [hrac.get_rid()]
							var hs := space.intersect_ray(qs)
							var dk := INF
							if not hs.is_empty() and vrstvy.any(func(vv): return vv.is_ancestor_of(hs["collider"])): dk = z0.distance_to(hs["position"])
							if dv > float(cfg["steny_dosah_m"]) and dk == INF: continue
							if absf(minf(dv, 9.0) - minf(dk, 9.0)) > float(cfg["steny_tolerance_m"]):
								sten += 1; vse.append({"druh": "zed", "trasa": jm, "p": [p.x, p.z, v], "smer": u * 45, "zed": dv, "kolize": dk, "objekt": (hs["collider"] as Node).get_parent().name if not hs.is_empty() else ""})
								if spatne.size() < 24: spatne.append("%s [%.1f, %.1f, +%.1f] směr %d° zeď %s m, kolize %s m" % [jm, p.x, p.z, v, u * 45, "–" if dv == INF else "%.2f" % dv, "–" if dk == INF else "%.2f" % dk])
				var d: float = (h["position"] as Vector3).y - vis
				if absf(d) > tol:
					horsi = maxf(horsi, absf(d)); vse.append({"druh": "povrch", "trasa": jm, "p": [p.x, p.z, p.y], "d": d, "kolize_y": h["position"].y, "vid_y": vis, "objekt": (h["collider"] as Node).get_parent().name})
					if spatne.size() < 12: spatne.append("%s [%.1f, %.1f] %s %.2f m" % [jm, p.x, p.z, "stojí nad viditelným" if d > 0 else "boří se", absf(d)])
	var fo := FileAccess.open(OS.get_environment("PUCHART_POVRCH") if OS.has_environment("PUCHART_POVRCH") else "user://povrch.json", FileAccess.WRITE); fo.store_string(JSON.stringify(vse, " "))
	vysledek["povrch_kolize"] = "OK" if spatne.is_empty() and n > 100 else "CHYBA: %d bodů, %s" % [n, "; ".join(spatne) if not spatne.is_empty() else "málo bodů"]
	print("PRUCHOD povrch_kolize ", vysledek["povrch_kolize"], " (bodů %d, nejhorší %.2f m, zdí nesedí %d)" % [n, horsi, sten])

## vrata_funkce (Míša 3. 11.: funkční vrata): zavřená vrata hlavní brány předního hradu postavu zastaví, otevřená pustí
func _test_vrata() -> void:
	var cl := CanvasLayer.new(); add_child(cl)
	var dv: Node = load("res://scripts/dvere.gd").new(); cl.add_child(dv); dv.zacni(hlavni, cl)
	var tr: Array = trasy.get("A_vstup", [])
	if dv.mista.is_empty() or tr.size() < 6:
		vysledek["vrata_funkce"] = "CHYBA: bez vrat nebo trasy"; return
	var brana := Vector3(tr[4][0], float(tr[4][2]), tr[4][1]); var g := ""; var nd := 1e9   # bod brány má výšku (průjezd)
	var smer := Vector3(tr[4][0] - tr[3][0], 0, tr[4][1] - tr[3][1]).normalized()
	var pred := brana - smer * 3.0; var za := brana + smer * 3.0   # 3 m před a za vraty v rovině průjezdu (ne terén pod mostem)
	for k in dv.mista:
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
	hrac.autopilot = Vector3.INF
	var f := FileAccess.open(OS.get_environment("PUCHART_VYSTUP") if OS.has_environment("PUCHART_VYSTUP") else "user://pruchod.json", FileAccess.WRITE); f.store_string(JSON.stringify(vysledek, " "))
	var ok := vysledek.values().all(func(v): return v == "OK")
	print("PRUCHOD VYSLEDEK ", "OK" if ok else "CHYBA", " ", vysledek)
	get_tree().quit(0 if ok else 1)
