extends Node3D
## Usedlosti nových míst (Předhradí, krčma, hájovna) – vše kromě domů (domy staví hlavni.gd _mista).
## Data: hra/data/mista_stavby.json z nastroje/mista_rozmisteni.py (pravidla/svet/mista.json „usedlosti“; Míša 11.–12. 11.:
## „mrkni na KCD“, „ať není každý dům nebo zahrada stejná“, hospodářské budovy, ploty, pole, stromy ve vsi).
## - hospodářské stavby Havrana (stodola, malá stodola, kůlna, kurník; modely/stavby_h zesvětlené jako domy): podrobný model
##   do podrobny_do_m, střední stupeň (barva vrcholů) do stredni_do_m, stín jen ze středního (jako _mista a Havran _ves_domy),
##   kolize z modelu *_kolize (modely/predmety_h, pivot z predmety_h.json)
## - ploty a vrata stavěné z pravidel Havrana (blender/vesnice.py picket_fence, rail_fence, roofed_gate, wicket): jedna síť
##   na usedlost (po materiálech), kreslí se do ploty_do_m; proutěné díly (předmět plutek) přes BunkyKolem
## - studna na návsi podle Havrana vesnice.py well
## - drobnosti (záhony, hranice dřeva, sudy, vůz, kupky, panáky…): MultiMesh po buňkách kolem hráče (bunky_kolem.gd) –
##   paměť tabletu (rozpocty.json pamet.uzlu_max)
## - stromy (jabloně sadů, lípy u vjezdu a na návsi): podrobný model, LOD1, daleko

const BunkyKolem := preload("res://scripts/bunky_kolem.gd")
const PH := "res://modely/predmety_h/"
const SH := "res://modely/stavby_h/"

var d: Dictionary
var lod: Dictionary
var mob := OS.has_feature("mobile")
var _mat := {}            # klíč -> materiál plotů a studny
var _st_mat: StandardMaterial3D
var _kat := {}            # predmety_h.json (pivot kolizí, rozměry)
var _site := {}           # model drobnosti -> [Mesh, Transform3D v rámci scény]
var _uzlu := 0
var pohyb_dily: Array = []   # vrata a vrátka plotů pro dvere.gd (formát data/pohyb.json, souřadnice světa)


func _init() -> void:
	name = "Ves"   # dvere.gd hledá díly pod uzlem Ves


func _ready() -> void:
	d = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista_stavby.json"))
	if not d.has("lod_ves"): return
	lod = d["lod_ves"]
	if FileAccess.file_exists("res://modely/predmety_h.json"):
		_kat = JSON.parse_string(FileAccess.get_file_as_string("res://modely/predmety_h.json"))
	_st_mat = StandardMaterial3D.new(); _st_mat.vertex_color_use_as_albedo = true; _st_mat.roughness = 0.9
	_materialy()
	_hospodarske()
	_ploty()
	_studny()
	_sezeni()
	_drobne()
	_stromy()
	print("VES uzlů %d, hospodářských %d, plotů %d, bran %d, drobností %d, stromů %d" % [_pocet(self), (d["hospodarske"] as Array).size(),
		(d["ploty"] as Array).size(), (d["brany"] as Array).size(), (d["drobne"] as Array).size(), (d["stromy"] as Array).size()])


func _pocet(n: Node) -> int:
	var k := 1
	for c in n.get_children(): k += _pocet(c)
	return k


func _f(key: String, mob_key := "") -> float:
	return float(lod[mob_key if (mob and mob_key != "") else key])


## ------------------------------------------------------------------ materiály (textury Havrana: plot, kůra, šindel, kámen)
func _materialy() -> void:
	var tx: Dictionary = d["ploty_pravidla"]["textury"]
	var jas := float(tx["jas_cil"])
	for k: String in tx:
		if not tx[k] is Dictionary: continue
		var e: Dictionary = tx[k]
		var m := StandardMaterial3D.new(); m.roughness = 0.92
		if e.has("albedo") and ResourceLoader.exists(String(e["albedo"])): m.albedo_texture = _zesvetli(load(String(e["albedo"])), jas)
		if e.has("normal") and ResourceLoader.exists(String(e["normal"])):
			m.normal_enabled = true; m.normal_texture = load(String(e["normal"]))
		if e.has("barva"): m.albedo_color = Color(String(e["barva"]))
		if e.has("nasob"): m.albedo_color = m.albedo_color * Color(float(e["nasob"]), float(e["nasob"]), float(e["nasob"]))   # ztmavit světlou texturu (kůra kůlů)
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		_mat[k] = [m, float(e.get("velikost_m", 1.0))]


## textura dřeva Havrana je tmavá (jas 0,27) – na jas_cil jako domy (stavby_export.gd _jas, nejvýš 2,6×); jednou při načtení
static func _zesvetli(t: Texture2D, cil: float) -> Texture2D:
	var im := t.get_image()
	if im == null: return t
	if im.is_compressed(): im.decompress()
	var s := 0.0; var n := 0
	for y in range(0, im.get_height(), 16):
		for x in range(0, im.get_width(), 16): s += im.get_pixel(x, y).get_luminance(); n += 1
	var j := s / maxf(n, 1)
	if j >= cil or j <= 0.01: return t
	im.adjust_bcs(minf(cil / j, 2.6), 1.0, 0.9)
	im.generate_mipmaps()
	return ImageTexture.create_from_image(im)


## ------------------------------------------------------------------ hospodářské stavby
func _hospodarske() -> void:
	var blizko := _f("podrobny_do_m"); var st_do := _f("stredni_do_m", "stredni_do_m_mobil")
	var sceny := {}
	var obaly: Dictionary = (d["modely"]["hospodarske"] as Dictionary).get("obal", {})
	var uzel := Node3D.new(); uzel.name = "Hospodarske"; add_child(uzel)
	for h: Dictionary in d["hospodarske"]:
		var mid := String(h["model"])
		if not sceny.has(mid):
			var p := SH + mid + ".glb"
			sceny[mid] = [load(p) if ResourceLoader.exists(p) else (load(PH + mid + ".glb") if ResourceLoader.exists(PH + mid + ".glb") else null),
				load(SH + mid + "_stredni.glb") if ResourceLoader.exists(SH + mid + "_stredni.glb") else null,
				load(PH + mid + "_kolize.glb") if ResourceLoader.exists(PH + mid + "_kolize.glb") else null]
		var sc: Array = sceny[mid]
		if sc[0] == null: continue
		var n: Node3D = (sc[0] as PackedScene).instantiate()
		n.name = "%s_%d" % [mid, int(h["usedlost"])]
		n.transform = Transform3D(Basis(Vector3.UP, float(h["yaw"])), Vector3(float(h["x"]), float(h["y"]), float(h["z"])))
		uzel.add_child(n)
		# střední stupeň (barva vrcholů) se ve hře kreslí černě (snímek 12. 11.: stejná stodola s jednobarevným materiálem
		# osvětlená, s barvou vrcholů černá – příčina NEOVERENA, týká se i domů _mista); má stejně trojúhelníků jako podrobný
		# model (17,8 tis.), šetří jen volání kreslení → zatím podrobný model až do stredni_do_m (lod.stredni_zapnuto)
		var ma_st: bool = sc[1] != null and bool(lod.get("stredni_zapnuto", false))
		for g in n.find_children("*", "GeometryInstance3D", true, false):
			(g as GeometryInstance3D).visibility_range_end = blizko if ma_st else st_do
			(g as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if ma_st else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		for sk_ in (d["modely"]["hospodarske"] as Dictionary).get(mid + "_skryt", []):   # části modelu, které se nekreslí (kovárna: dlažba, podlaha)
			var u_ := n.find_child(String(sk_), true, false)
			if u_: u_.queue_free()
		var lod1_p := SH + mid + "_lod1.glb"   # vzdálený stupeň z modelu (kovárna, Míša 14. 11.: návod 0–60 m podrobně, od 55 m LOD1)
		if ResourceLoader.exists(lod1_p):
			var od1 := float((d["modely"]["hospodarske"] as Dictionary).get("lod1_od_m", 55.0))
			for g in n.find_children("*", "GeometryInstance3D", true, false): (g as GeometryInstance3D).visibility_range_end = od1 + 5.0
			var l1: Node3D = (load(lod1_p) as PackedScene).instantiate(); l1.name = mid + "_LOD1"; n.add_child(l1)
			preload("res://scripts/hlavni.gd").Ztmav_daleko(l1, (d["modely"]["domy"] as Dictionary).get("daleko_textury", {}).get("jas", {}))
			for g in l1.find_children("*", "GeometryInstance3D", true, false):   # hrubý stupeň do dálky (Míša 14. 11.: „alespoň hmota“)
				(g as GeometryInstance3D).visibility_range_begin = od1; (g as GeometryInstance3D).visibility_range_end = _f("obal_do_m")
		elif obaly.has(mid):   # stodola, kůlna: od stredni_do_m levný texturovaný obal (dřív za 180 / 120 m zmizely)
			if not sceny.has(mid + "_obal"): sceny[mid + "_obal"] = _obal(n, obaly[mid], float(obaly["velikost_m"]), obaly.get("jas", {}))
			var ob := MeshInstance3D.new(); ob.name = mid + "_Obal"; ob.mesh = sceny[mid + "_obal"]
			ob.visibility_range_begin = st_do; ob.visibility_range_end = _f("obal_do_m"); ob.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			n.add_child(ob)
		if ma_st:
			var si: Node = (sc[1] as PackedScene).instantiate()
			for mi in si.find_children("*", "MeshInstance3D", true, false):
				var xf := _xf_ve_scene(mi, si)
				for k in 2:   # střední stupeň a jeho kopie jen pro stín (jako predmety.gd / _mista)
					var st := MeshInstance3D.new(); st.name = mid + ("_Stredni" if k == 0 else "_Stin")
					st.mesh = (mi as MeshInstance3D).mesh; st.transform = xf; st.material_override = _st_mat
					st.lod_bias = float(lod["lod_bias"])   # bez automatického LOD (Havran: stodola z dálky černá silueta)
					st.visibility_range_begin = blizko if k == 0 else 0.0; st.visibility_range_end = st_do
					st.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if k == 0 else GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
					n.add_child(st)
			si.free()
		# kolize: z kolizního modelu (Havran dily.kolize, pivot), jinak kvádr z rozměru katalogu
		var info: Dictionary = _kat.get(mid, {})
		var kb := StaticBody3D.new(); kb.name = "Kolize"
		if sc[2] != null and info.get("dily", {}).has("kolize"):
			var ki: Node = (sc[2] as PackedScene).instantiate()
			var kmi: Array = ki.find_children("*", "MeshInstance3D", true, false)
			if not kmi.is_empty():
				var cs := CollisionShape3D.new(); var sh := ConcavePolygonShape3D.new()
				sh.set_faces((kmi[0] as MeshInstance3D).mesh.get_faces()); cs.shape = sh; kb.add_child(cs)
				var pv: Array = info["dily"]["kolize"]["pivot"]
				kb.position = Vector3(float(pv[0]), float(pv[1]), float(pv[2]))
			ki.free()
		elif info.has("rozmer"):
			var r: Array = info["rozmer"]; var cs := CollisionShape3D.new(); var bs := BoxShape3D.new()
			bs.size = Vector3(float(r[0]) * 0.95, float(r[1]), float(r[2]) * 0.95); cs.shape = bs; cs.position.y = float(r[1]) * 0.5
			kb.add_child(cs)
		if kb.get_child_count() > 0: n.add_child(kb)
		else: kb.free()


## Hrubý obal stavby pro dálku (mista.json modely.hospodarske.obal; KCD/HLOD – zjednodušený tvar se skutečnou texturou):
## stěny L × D do okapu, sedlová střecha (hřeben podél x) nebo pultová (předek +z) až po obal modelu (přesah), textury
## materiálů podrobného modelu promítnuté trojrozměrně (obal nemá UV).
func _obal(n: Node3D, o: Dictionary, vel: float, obal_jas: Dictionary) -> ArrayMesh:
	var ab := AABB(); var prvni := true
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var b := _xf_ve_scene(mi, n) * (mi as MeshInstance3D).get_aabb()
		ab = b if prvni else ab.merge(b); prvni = false
	var hx := float(o["L"]) / 2; var hz := float(o["D"]) / 2
	var cx := ab.get_center().x; var cz := ab.get_center().z
	var ax := ab.size.x / 2; var az := ab.size.z / 2; var top := ab.end.y
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var kr := SurfaceTool.new(); kr.begin(Mesh.PRIMITIVE_TRIANGLES)
	var tri := func(t: SurfaceTool, a: Vector3, b: Vector3, c: Vector3) -> void:
		var nn := (c - a).cross(b - a).normalized()
		for v: Vector3 in [a, b, c]: t.set_normal(nn); t.add_vertex(v)
	var ctyr := func(t: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, e: Vector3) -> void:
		tri.call(t, a, b, c); tri.call(t, a, c, e)
	var P := func(x: float, y: float, z: float) -> Vector3: return Vector3(cx + x, y, cz + z)
	var sedl := String(o["strecha"]) == "sedlova"
	# výška stěny v místě z (vršek stěny pod střechou), střecha v místě z
	var hp := float(o.get("predek_m", o.get("okap_m", 3.0))); var hzad := float(o.get("zadek_m", o.get("okap_m", 3.0)))
	var stena_y := func(z: float) -> float:
		if sedl: return float(o["okap_m"]) + (top - float(o["okap_m"])) * (1.0 - absf(z) / hz) if absf(z) < hz else float(o["okap_m"])
		return lerpf(hzad, hp, (z + hz) / (2 * hz))
	# stěny (vnější strana, normála ven): přední +z, zadní −z, boky ±x (štíty u sedlové až k hřebeni)
	var zz: Array = [-hz, 0.0, hz] if sedl else [-hz, hz]
	ctyr.call(st, P.call(-hx, 0, hz), P.call(hx, 0, hz), P.call(hx, stena_y.call(hz), hz), P.call(-hx, stena_y.call(hz), hz))
	ctyr.call(st, P.call(hx, 0, -hz), P.call(-hx, 0, -hz), P.call(-hx, stena_y.call(-hz), -hz), P.call(hx, stena_y.call(-hz), -hz))
	for sx: float in [-1.0, 1.0]:
		for i in zz.size() - 1:
			var z0: float = zz[i]; var z1: float = zz[i + 1]
			if sx > 0: ctyr.call(st, P.call(hx, 0, z1), P.call(hx, 0, z0), P.call(hx, stena_y.call(z0), z0), P.call(hx, stena_y.call(z1), z1))
			else: ctyr.call(st, P.call(-hx, 0, z0), P.call(-hx, 0, z1), P.call(-hx, stena_y.call(z1), z1), P.call(-hx, stena_y.call(z0), z0))
	# střecha po obal modelu (přesah), spodní strana přesahu jen jako tmavší krytina (z dálky nevidět)
	if sedl:
		var ok := float(o["okap_m"]); var sk := (top - ok) / hz; var ye := ok - (az - hz) * sk
		for sz: float in [-1.0, 1.0]:
			var a: Vector3 = P.call(-ax, ye, az * sz); var b: Vector3 = P.call(ax, ye, az * sz)
			var c: Vector3 = P.call(ax, top, 0.0); var e: Vector3 = P.call(-ax, top, 0.0)
			if sz > 0: ctyr.call(kr, a, b, c, e)
			else: ctyr.call(kr, b, a, e, c)
	else:
		var sk := (hp - hzad) / (2 * hz)
		var yp := hp + (az - hz) * sk; var yz := hzad - (az - hz) * sk
		ctyr.call(kr, P.call(-ax, yp, az), P.call(ax, yp, az), P.call(ax, yz, -az), P.call(-ax, yz, -az))
	var m := ArrayMesh.new()
	for k in 2:
		var t: SurfaceTool = st if k == 0 else kr
		var arr := t.commit_to_arrays(); m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		var kl := "steny" if k == 0 else "krytina"
		m.surface_set_material(k, _triplanar(_textura_materialu(n, String(o[kl])), vel, (obal_jas as Dictionary).get(kl, 1.0)))
	return m


## albedo textura materiálu daného jména v modelu (pro obaly z dálky)
static func _textura_materialu(n: Node, jm: String) -> Texture2D:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var me := (mi as MeshInstance3D).mesh
		if me == null: continue
		for i in me.get_surface_count():
			var mt := me.surface_get_material(i) as BaseMaterial3D
			if mt and mt.resource_name == jm: return mt.albedo_texture
	return null


## jas: číslo, nebo [R, G, B] (teplý tón hrubých stupňů – Míša 14. 11.: „nemohly by být hnědé?“)
static func Barva_jas(j: Variant) -> Color:
	if j is Array: return Color(float(j[0]), float(j[1]), float(j[2]))
	return Color(float(j), float(j), float(j))


static func _triplanar(t: Texture2D, vel: float, jas: Variant = 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.roughness = 1.0; m.albedo_color = Barva_jas(jas)
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	if t: m.albedo_texture = t; m.uv1_triplanar = true; m.uv1_scale = Vector3.ONE / vel
	else: m.albedo_color = Color(0.35, 0.28, 0.2) * Barva_jas(jas)
	return m


static func _xf_ve_scene(n: Node, koren: Node) -> Transform3D:
	var t := Transform3D(); var x := n
	while x != koren and x != null:
		if x is Node3D: t = (x as Node3D).transform * t
		x = x.get_parent()
	return t


## ------------------------------------------------------------------ geometrie (SurfaceTool po materiálech)
class Sit:
	var st := {}          # klíč materiálu -> SurfaceTool
	var o := Vector3.ZERO # počátek uzlu (vrcholy relativně)
	var mat := {}
	func _init(p_o: Vector3, p_mat: Dictionary) -> void:
		o = p_o; mat = p_mat
	func s(k: String) -> SurfaceTool:
		if not st.has(k):
			var t := SurfaceTool.new(); t.begin(Mesh.PRIMITIVE_TRIANGLES); st[k] = t
		return st[k]
	func quad(k: String, a: Vector3, b: Vector3, c: Vector3, e: Vector3, uv0: Vector2, uv1: Vector2) -> void:
		# a-b-c-e proti směru hodinových ručiček při pohledu zvenku (normála = (b-a)×(e-a))
		var t := s(k); var n := (b - a).cross(e - a).normalized()
		var uvs := [uv0, Vector2(uv1.x, uv0.y), uv1, Vector2(uv0.x, uv1.y)]
		var p := [a - o, b - o, c - o, e - o]
		for i in [0, 2, 1, 0, 3, 2]:
			t.set_normal(n); t.set_uv(uvs[i]); t.add_vertex(p[i])
	## kvádr: střed c, osy x/y/z (jednotkové), rozměr r
	func kvadr(k: String, c: Vector3, x: Vector3, y: Vector3, z: Vector3, r: Vector3) -> void:
		var vm: float = mat[k][1] if mat.has(k) else 1.0
		z = x.cross(y).normalized()   # pravotočivá soustava (jinak obrácené normály – stěna vidět zevnitř)
		var hx := x * r.x / 2; var hy := y * r.y / 2; var hz := z * r.z / 2
		var u_x := r.x / vm; var u_y := r.y / vm; var u_z := r.z / vm
		quad(k, c - hx - hy + hz, c + hx - hy + hz, c + hx + hy + hz, c - hx + hy + hz, Vector2(0, u_y), Vector2(u_x, 0))   # +z
		quad(k, c + hx - hy - hz, c - hx - hy - hz, c - hx + hy - hz, c + hx + hy - hz, Vector2(0, u_y), Vector2(u_x, 0))   # -z
		quad(k, c + hx - hy + hz, c + hx - hy - hz, c + hx + hy - hz, c + hx + hy + hz, Vector2(0, u_y), Vector2(u_z, 0))   # +x
		quad(k, c - hx - hy - hz, c - hx - hy + hz, c - hx + hy + hz, c - hx + hy - hz, Vector2(0, u_y), Vector2(u_z, 0))   # -x
		quad(k, c - hx + hy + hz, c + hx + hy + hz, c + hx + hy - hz, c - hx + hy - hz, Vector2(0, u_z), Vector2(u_x, 0))   # +y
		quad(k, c - hx - hy - hz, c + hx - hy - hz, c + hx - hy + hz, c - hx - hy + hz, Vector2(0, u_z), Vector2(u_x, 0))   # -y
	## kulatina (kůl, žerď): válec z a do b, poloměry r0 → r1, n stěn; kůra po obvodu
	func valec(k: String, a: Vector3, b: Vector3, r0: float, r1: float, n := 6) -> void:
		var vm: float = mat[k][1] if mat.has(k) else 1.0
		var ax := (b - a); var ln := ax.length(); if ln < 1e-4: return
		ax /= ln
		var x := ax.cross(Vector3.UP if absf(ax.y) < 0.9 else Vector3.RIGHT).normalized(); var y := ax.cross(x)
		for i in n:
			var f0 := TAU * i / n; var f1 := TAU * (i + 1) / n
			var d0 := x * cos(f0) + y * sin(f0); var d1 := x * cos(f1) + y * sin(f1)
			quad(k, a + d0 * r0, a + d1 * r0, b + d1 * r1, b + d0 * r1, Vector2(float(i) / n * 0.4, ln / vm), Vector2(float(i + 1) / n * 0.4, 0))   # normála ven
		var t := s(k)   # čela s letokruhy jen jako plocha (malé)
		for e in [[b, ax, r1], [a, -ax, r0]]:
			var c: Vector3 = e[0]; var nn: Vector3 = e[1]; var r: float = e[2]
			for i in n:
				var f0 := TAU * i / n; var f1 := TAU * (i + 1) / n
				var p0: Vector3 = c + (x * cos(f0) + y * sin(f0)) * r; var p1: Vector3 = c + (x * cos(f1) + y * sin(f1)) * r
				var tri := [c, p0, p1] if nn.dot((p0 - c).cross(p1 - c)) > 0 else [c, p1, p0]
				for p: Vector3 in tri:
					t.set_normal(nn); t.set_uv(Vector2(0.5, 0.5)); t.add_vertex(p - o)
	## hranol z obrysu (body v rovině, proti směru) vytažený o tloušťku podél nrm
	func hranol(k: String, body: Array, nrm: Vector3, tl: float) -> void:
		var vm: float = mat[k][1] if mat.has(k) else 1.0
		var t := s(k); var n := body.size()
		var pr := [body, body.map(func(p: Vector3) -> Vector3: return p + nrm * tl)]
		for strana in 2:
			var nn := -nrm if strana == 0 else nrm
			for i in range(1, n - 1):
				var tri := [pr[strana][0], pr[strana][i], pr[strana][i + 1]]
				if nn.dot((tri[1] - tri[0]).cross(tri[2] - tri[0])) < 0: tri = [tri[0], tri[2], tri[1]]
				for p: Vector3 in tri:
					t.set_normal(nn); t.set_uv(Vector2(p.x + p.z, p.y) / vm * 0.3 + Vector2(0.37, 0.0)); t.add_vertex(p - o)
		for i in n:
			var a: Vector3 = body[i]; var b: Vector3 = body[(i + 1) % n]
			var q := [a, b, b + nrm * tl, a + nrm * tl]
			var nn := (b - a).cross(nrm).normalized()
			var c_: Vector3 = (body as Array).reduce(func(acc: Vector3, p: Vector3) -> Vector3: return acc + p, Vector3.ZERO) / n
			if nn.dot(a - c_) < 0: q = [b, a, a + nrm * tl, b + nrm * tl]
			quad(k, q[0], q[1], q[2], q[3], Vector2(0, 0), Vector2(0.05, (b - a).length() / vm))
	func mesh() -> ArrayMesh:
		var am := ArrayMesh.new()
		for k: String in st:
			var t: SurfaceTool = st[k]
			if mat.has(k): t.generate_tangents()
			t.commit(am)
			am.surface_set_material(am.get_surface_count() - 1, mat[k][0] if mat.has(k) else null)
		return am


## ------------------------------------------------------------------ ploty a vrata (Havran vesnice.py)
func _ploty() -> void:
	var pr: Dictionary = d["ploty_pravidla"]
	var po_used := {}
	for p: Dictionary in d["ploty"]: po_used[int(p["usedlost"])] = (po_used.get(int(p["usedlost"]), []) as Array) + [p]
	for b: Dictionary in d["brany"]: po_used[int(b["usedlost"])] = (po_used.get(int(b["usedlost"]), []) as Array) + [b]
	var uzel := Node3D.new(); uzel.name = "Ploty"; add_child(uzel)
	var dosah := _f("ploty_do_m", "ploty_do_m_mobil")
	for ui: int in po_used:
		var prvky: Array = po_used[ui]
		var c := Vector3.ZERO; var nc := 0
		for e: Dictionary in prvky:
			if e.has("body"): for q: Array in e["body"]: c += Vector3(float(q[0]), float(q[1]), float(q[2])); nc += 1
		c /= maxi(nc, 1)
		var sit := Sit.new(c, _mat); var kb := StaticBody3D.new(); kb.name = "Kolize"
		for e: Dictionary in prvky:
			if e.has("body"):
				var body: Array = (e["body"] as Array).map(func(q: Array) -> Vector3: return Vector3(float(q[0]), float(q[1]), float(q[2])))
				var rng := RandomNumberGenerator.new(); rng.seed = int(e["semeno"])
				match String(e["druh"]):
					"latovy": _plot_latovy(sit, body, pr["latovy"], rng)
					"zerdovy": _plot_zerdovy(sit, body, pr["zerdovy"], rng)
					"proutěny": pass   # díly plutek: _drobne (BunkyKolem)
				_kolize_plotu(kb, body, float(pr["latovy"]["vyska_m"]))
			else:
				_brana(sit, e, pr, uzel)
		var mi := MeshInstance3D.new(); mi.name = "Ploty_%d" % ui; mi.mesh = sit.mesh(); mi.position = c
		mi.visibility_range_end = dosah; mi.visibility_range_end_margin = 4.0
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		uzel.add_child(mi)
		if kb.get_child_count() > 0: uzel.add_child(kb)
		else: kb.free()


func _y_na(body: Array, s: float) -> Vector3:
	## bod na lomené čáře ve vzdálenosti s
	for i in range(body.size() - 1):
		var a: Vector3 = body[i]; var b: Vector3 = body[i + 1]; var l := a.distance_to(b)
		if s <= l or i == body.size() - 2: return a.lerp(b, clampf(s / maxf(l, 1e-4), 0.0, 1.0))
		s -= l
	return body[-1]


func _delka(body: Array) -> float:
	var l := 0.0
	for i in range(body.size() - 1): l += (body[i] as Vector3).distance_to(body[i + 1])
	return l


## laťový plot: kůlové sloupky po 2 m, dvě žerdě s kůrou, latě různě široké a vysoké, špice / šikmo / rovně, 4 % chybí
func _plot_latovy(sit: Sit, body: Array, p: Dictionary, rng: RandomNumberGenerator) -> void:
	var L := _delka(body); var a: Vector3 = body[0]; var b: Vector3 = body[-1]
	var dn := Vector3(b.x - a.x, 0, b.z - a.z).normalized(); var nrm := Vector3(-dn.z, 0, dn.x)
	var h := float(p["vyska_m"]); var np_ := maxi(1, int(L / float(p["sloupky_m"])))
	var tops := []
	for i in np_ + 1:
		var q := _y_na(body, L * i / np_) - nrm * 0.12
		sit.valec("kura", q + Vector3(0, -0.3, 0), q + Vector3(rng.randf_range(-0.05, 0.05), h + 0.05, rng.randf_range(-0.05, 0.05)), 0.065, 0.055)
	for yy: float in p["zerde_y_m"]:
		var y_ := minf(yy, h - 0.25)
		var q0 := _y_na(body, 0.0) - nrm * 0.07; var q1 := _y_na(body, L) - nrm * 0.07
		var prev := q0 + Vector3(0, y_, 0)
		for i in range(1, np_ + 1):
			var q := _y_na(body, L * i / np_) - nrm * 0.07 + Vector3(0, y_ + rng.randf_range(-0.04, 0.04), 0)
			sit.valec("kura", prev, q, 0.035, 0.035, 5); prev = q
	var s := 0.05; var w_r: Array = p["lata_sirka_m"]; var g_r: Array = p["lata_mezera_m"]
	while s < L - 0.03:
		var w := rng.randf_range(float(w_r[0]), float(w_r[1]))
		if rng.randf() < float(p["chybi_p"]):
			s += w + rng.randf_range(float(g_r[0]), float(g_r[1])); continue
		var q := _y_na(body, s); var hh := h + rng.randf_range(-0.12, 0.08)
		var tilt := rng.randf_range(-0.04, 0.04) if rng.randf() < 0.85 else rng.randf_range(-0.12, 0.12)
		var up := Vector3.UP.rotated(nrm, tilt); var ds := dn.rotated(nrm, tilt)
		var k := rng.randf(); var b0 := -0.08; var prof: Array
		if k < 0.55: prof = [Vector2(-w / 2, b0), Vector2(w / 2, b0), Vector2(w / 2, hh - w * 0.55), Vector2(rng.randf_range(-0.01, 0.01), hh), Vector2(-w / 2, hh - w * 0.55)]
		elif k < 0.85:
			var sl := (1.0 if rng.randf() < 0.5 else -1.0) * rng.randf_range(0.03, 0.07)
			prof = [Vector2(-w / 2, b0), Vector2(w / 2, b0), Vector2(w / 2, hh - 0.05 + sl), Vector2(-w / 2, hh - 0.05 - sl)]
		else: prof = [Vector2(-w / 2, b0), Vector2(w / 2, b0), Vector2(w / 2, hh - 0.06), Vector2(-w / 2, hh - 0.06)]
		var base := q - nrm * 0.035
		sit.hranol("lata", prof.map(func(v: Vector2) -> Vector3: return base + ds * v.x + up * v.y), nrm, 0.022)
		s += w + rng.randf_range(float(g_r[0]), float(g_r[1]))


## ohrada z kulatiny: křivé kůly po 2,8 m, dvě až tři žerdě s kůrou, konce přesahují a překrývají se, někde žerď spadla
func _plot_zerdovy(sit: Sit, body: Array, p: Dictionary, rng: RandomNumberGenerator) -> void:
	var L := _delka(body); var a: Vector3 = body[0]; var b: Vector3 = body[-1]
	var dn := Vector3(b.x - a.x, 0, b.z - a.z).normalized(); var nrm := Vector3(-dn.z, 0, dn.x)
	var h := float(p["vyska_m"]); var n := maxi(1, int(L / float(p["kuly_m"])))
	var pata := []
	for i in n + 1:
		var q := _y_na(body, L * i / n); pata.append(q)
		var r := rng.randf_range(0.06, 0.08)
		var mid := q + Vector3(rng.randf_range(-0.03, 0.03), (h + 0.3) / 2 - 0.35, rng.randf_range(-0.03, 0.03))
		var top := q + Vector3(rng.randf_range(-0.06, 0.06), h - 0.05, rng.randf_range(-0.06, 0.06))
		sit.valec("kura", q + Vector3(0, -0.35, 0), mid, r * 1.05, r, 6); sit.valec("kura", mid, top, r, r * 0.88, 6)
	var rady: Array = [0.42, h - 0.1] if rng.randf() < 0.6 else [0.3, 0.68, h - 0.08]
	for i in n:
		for k in rady.size():
			var yy: float = rady[k]; var str_ := nrm * 0.08 * (1.0 if k % 2 else -1.0)
			var p0: Vector3 = pata[i] + Vector3(0, yy + rng.randf_range(-0.05, 0.05), 0) - dn * rng.randf_range(0.15, 0.3) + str_
			var p1: Vector3 = pata[i + 1] + Vector3(0, yy + rng.randf_range(-0.05, 0.05), 0) + dn * rng.randf_range(0.15, 0.3) + str_
			if rng.randf() < float(p["spadla_p"]): p1.y = (pata[i + 1] as Vector3).y + 0.05
			var mid := (p0 + p1) / 2 + Vector3(0, rng.randf_range(-0.04, 0.02), 0)   # žerď se prohýbá
			var r := rng.randf_range(0.035, 0.05)
			sit.valec("kura", p0, mid, r, r, 5); sit.valec("kura", mid, p1, r, r * 0.85, 5)


func _kolize_plotu(kb: StaticBody3D, body: Array, h: float) -> void:
	var a: Vector3 = body[0]; var b: Vector3 = body[-1]; var ln := Vector2(b.x - a.x, b.z - a.z).length()
	if ln < 0.2: return
	var cs := CollisionShape3D.new(); var bs := BoxShape3D.new(); bs.size = Vector3(ln, h, 0.14); cs.shape = bs
	var c := (a + b) / 2 + Vector3(0, h / 2, 0)
	cs.transform = Transform3D(Basis(Vector3.UP, atan2(-(b.z - a.z), b.x - a.x)), c)
	kb.add_child(cs)


## vrata se stříškou (Havran roofed_gate), prostá vrata a branka (wicket) – zavřená křídla z prken na svlacích se vzpěrou
## Křídla jsou samostatné uzly s pantem (Pohyb_ves_*), pohybuje jimi dvere.gd jako dveřmi hradu (Míša 13. 11.: „funkční
## dveře, vrata, vrátka“; Havran vesnice.py roofed_gate/wicket + kit.movable): v modelu zavřená, ve hře výchozí stav otevřeno,
## otevírají se do dvora (ke středu parcely), zavřené křídlo má kolizi.
func _brana(sit: Sit, e: Dictionary, pr: Dictionary, uzel: Node3D) -> void:
	var a := Vector3(float(e["a"][0]), float(e["a"][1]), float(e["a"][2])); var b := Vector3(float(e["b"][0]), float(e["b"][1]), float(e["b"][2]))
	var y := minf(a.y, b.y); a.y = y; b.y = y
	var dn := (b - a); var w := dn.length(); dn /= w; var nrm := Vector3(-dn.z, 0, dn.x)
	var druh := String(e["druh"])
	var dovnitr := -nrm   # do dvora: ke středu parcely usedlosti
	for u_: Dictionary in d["usedlosti"]:
		if int(u_["i"]) == int(e["usedlost"]):
			var st_ := Vector3(float(u_["stred"][0]), 0, float(u_["stred"][1])) - (a + b) / 2; st_.y = 0
			dovnitr = nrm if st_.dot(nrm) > 0 else -nrm
	var ib := pohyb_dily.size()
	if druh == "branka":
		var bp: Dictionary = pr["branka"]
		for q: Vector3 in [a, b]: sit.valec("kura", q + Vector3(0, -0.4, 0), q + Vector3(0, 1.25, 0), 0.075, 0.068)
		var wl := w - 0.16; var hh := float(bp["vyska_m"])
		var kresli_b := func(ls: Sit, x_: Vector3, n_: Vector3) -> void:
			var n := 7
			for i in n:
				var x0 := wl * i / n + 0.008; var x1 := wl * (i + 1) / n - 0.008
				var o := Vector3(0, 0.08, 0)
				ls.hranol("lata", [o + x_ * x0, o + x_ * x1, o + x_ * x1 + Vector3(0, hh - 0.04, 0), o + x_ * (x0 + x1) / 2 + Vector3(0, hh, 0), o + x_ * x0 + Vector3(0, hh - 0.04, 0)], n_, 0.022)
			for yy: float in [0.2, 0.85]: ls.kvadr("vrata", x_ * (wl / 2) + Vector3(0, 0.08 + yy, 0) - n_ * 0.03, x_, Vector3.UP, n_, Vector3(wl, 0.09, 0.035))
		_kridlo(uzel, "Pohyb_ves_branka_%d" % ib, "ves_branka_%d" % ib, a + dn * 0.08, dn, nrm, dovnitr, wl, hh, (a + b) / 2 + Vector3(0, 1.0, 0), kresli_b)
		return
	var kryta := druh == "kryta_vrata"
	var vp: Dictionary = pr["kryta_vrata"] if kryta else pr["vrata"]
	var hs := float(vp.get("sloupy_m", 1.9)) if kryta else float(vp["kridla_m"]) + 0.35
	for q: Vector3 in [a, b]:
		sit.kvadr("tram", q + Vector3(0, (hs - 0.4) / 2, 0), dn, Vector3.UP, nrm, Vector3(0.24 if kryta else 0.2, hs + 0.4, 0.24 if kryta else 0.2))
	if kryta:
		# práh nahoře přes oba sloupy a stříška ze šindele na obě strany
		var ta := a + Vector3(0, hs + 0.05, 0) - dn * 0.4; var tb := b + Vector3(0, hs + 0.05, 0) + dn * 0.4
		sit.kvadr("tram", (ta + tb) / 2, dn, Vector3.UP, nrm, Vector3(w + 0.8, 0.22, 0.22))
		var hr := (ta + tb) / 2 + Vector3(0, 0.45, 0)
		for su: float in [-1.0, 1.0]:
			var ok := hr + nrm * su * 0.78 - Vector3(0, 0.65, 0)
			var c := (hr + ok) / 2; var dl := hr.distance_to(ok)
			var yv := (hr - ok).normalized(); var zv := dn.cross(yv).normalized() * (1.0 if su > 0 else -1.0)
			sit.kvadr("sindel", c + zv * 0.03, dn, yv, zv, Vector3(w + 0.95, dl + 0.12, 0.05))
	# dvě křídla z prken (5 prken, svlaky nahoře a dole, vzpěra) – každé na svém pantu u sloupu
	var hk := float(vp["kridla_m"]); var wl := w / 2 - 0.14
	var kresli_v := func(ls: Sit, x_: Vector3, n_: Vector3) -> void:
		for i in 5:
			var x0 := 0.03 + (wl - 0.03) * i / 5.0; var x1 := 0.03 + (wl - 0.03) * (i + 1) / 5.0 - 0.012
			var top := hk + 0.1 * sin((x0 + x1) / 2 / wl * PI / 2)
			ls.kvadr("vrata", x_ * (x0 + x1) / 2 + Vector3(0, 0.06 + top / 2, 0), x_, Vector3.UP, n_, Vector3(x1 - x0, top, 0.04))
		for yy: float in [0.3, hk - 0.3]:
			ls.kvadr("vrata", x_ * wl / 2 + Vector3(0, 0.06 + yy, 0) - n_ * 0.04, x_, Vector3.UP, n_, Vector3(wl - 0.05, 0.12, 0.04))
		var bp0 := x_ * 0.1 + Vector3(0, 0.36, 0) - n_ * 0.045; var bp1 := x_ * (wl - 0.1) + Vector3(0, hk - 0.36, 0) - n_ * 0.045
		var bx := (bp1 - bp0).normalized()
		ls.kvadr("vrata", (bp0 + bp1) / 2, bx, n_.cross(bx).normalized() * -1.0, n_, Vector3(bp0.distance_to(bp1), 0.1, 0.035))
	for side: float in [-1.0, 1.0]:
		var hp := (a + dn * 0.13) if side < 0 else (b - dn * 0.13)
		_kridlo(uzel, "Pohyb_ves_vrata_%d_%s" % [ib, "l" if side < 0 else "p"], "ves_vrata_%d" % ib, hp, dn * (-side), nrm, dovnitr, wl, hk, (a + b) / 2 + Vector3(0, 1.0, 0), kresli_v)


## křídlo jako uzel s pantem v hp: místní osa x podél křídla (od pantu), geometrie z kresli(Sit, x, nrm) v místních
## souřadnicích; záznam pro dvere.gd (kolize zavřeného křídla, úhel do dvora, místo ovládání ve světě)
func _kridlo(uzel: Node3D, jm: String, skup: String, hp: Vector3, x_: Vector3, nrm: Vector3, dovnitr: Vector3, wl: float, hk: float, pouzit: Vector3, kresli: Callable) -> void:
	var B := Basis(x_, Vector3.UP, x_.cross(Vector3.UP).normalized())
	var bi := B.inverse()
	var ls := Sit.new(Vector3.ZERO, _mat)
	kresli.call(ls, Vector3.RIGHT, (bi * nrm).normalized())
	var mi := MeshInstance3D.new(); mi.name = jm; mi.mesh = ls.mesh(); mi.transform = Transform3D(B, hp)
	mi.visibility_range_end = _f("ploty_do_m", "ploty_do_m_mobil"); mi.visibility_range_end_margin = 4.0
	uzel.add_child(mi)
	var dl := bi * dovnitr   # Basis(UP, a) * (1, 0, 0) = (cos a, 0, −sin a) → do dvora
	var uhel := float(d["ploty_pravidla"].get("kridlo_uhel_deg", 85.0)) * (-1.0 if dl.z > 0 else 1.0)
	pohyb_dily.append({"name": jm, "kind": "vrata" if skup.begins_with("ves_vrata") else "dvere", "group": skup, "glb_zavreno": true,
		"cols": [[wl / 2, hk / 2 + 0.06, 0.0, wl, hk, 0.08]], "use": [pouzit.x, pouzit.y, pouzit.z], "open": uhel, "dur": 1.6 if skup.begins_with("ves_vrata") else 1.0})


## ------------------------------------------------------------------ studna na návsi (Havran vesnice.py well + KCD1 fotky)
## mista.json usedlosti.studna (zdroj: KCD1 kcd1/11_nadvori_studna_drevo_kone, kcd_vzhled/misa_kcd_15): roubení z oblých
## kamenů po vrstvách s vazbou (každá vrstva pootočená o půl kamene), za kameny jádro, nahoře koruna z plochých kamenů,
## uvnitř tma; dva sloupy vně roubení s pražcem a vzpěrami, rumpál z kulatiny s klikou, lano, vědro na koruně, sedlová stříška.
## Míša 13. 11. (foto ec383bfe): dřív válec s normálami dovnitř – zvenku průhledný, bez kamene.
func _studny() -> void:
	var sp: Dictionary = d["studna_pravidla"]
	for s: Dictionary in d["studny"]:
		var c := Vector3(float(s["x"]), float(s["y"]), float(s["z"]))
		var sit := Sit.new(c, _mat); var yaw := float(s["yaw"])
		var rng := RandomNumberGenerator.new(); rng.seed = int(absf(c.x) * 100.0 + absf(c.z) * 7.0)
		var x := Vector3(cos(yaw), 0, -sin(yaw)); var z := Vector3(sin(yaw), 0, cos(yaw))
		var ro := float(sp["polomer_m"]); var tl := float(sp.get("tloustka_zdi_m", 0.34)); var ri := ro - tl; var h := float(sp["vyska_m"])
		var rm := (ro + ri) / 2.0
		var nk := int(sp.get("kamenu_ve_vrstve", 15)); var nv := int(sp.get("vrstvy", 5)); var kr: Array = sp.get("kamen_rozmer_m", [0.32, 0.2, 0.3])
		var hv := h / nv
		# jádro za kameny (zemina a drobné kamení): válec vně i uvnitř, normály ven / dovnitř
		_valec_plast(sit, "spara", c + Vector3(0, -0.2, 0), h + 0.15, rm + 0.08, x, z, 20, 1.0)   # jádro ve spárách, kameny ho přečnívají
		_valec_plast(sit, "spara", c + Vector3(0, 0.25, 0), h - 0.3, rm - 0.08, x, z, 20, -1.0)
		for i in nv:   # vrstvy valounů s vazbou
			var y := c.y + (i + 0.5) * hv - 0.04
			for k in nk:
				var f := TAU * (k + (0.5 if i % 2 else 0.0) + rng.randf_range(-0.12, 0.12)) / nk
				var dr := x * cos(f) + z * sin(f); var tg := Vector3.UP.cross(dr).normalized()
				var sc := rng.randf_range(0.88, 1.12)
				var p := Vector3(c.x, y, c.z) + dr * (rm + rng.randf_range(-0.02, 0.02))
				var xk := tg.rotated(dr, rng.randf_range(-0.12, 0.12)).rotated(Vector3.UP, rng.randf_range(-0.15, 0.15))
				var yk := Vector3.UP.rotated(xk.cross(Vector3.UP).normalized(), rng.randf_range(-0.1, 0.1))
				sit.kvadr("valoun", p + dr * rng.randf_range(0.0, 0.03), xk, yk, Vector3.ZERO, Vector3(float(kr[0]) * sc, float(kr[1]) * rng.randf_range(0.8, 1.0), float(kr[2]) * sc))
		for k in 12:   # koruna: ploché kameny přes celou tloušťku
			var f := TAU * (k + rng.randf_range(-0.1, 0.1)) / 12.0
			var dr := x * cos(f) + z * sin(f); var tg := Vector3.UP.cross(dr).normalized()
			# Míša 14. 11.: „studna ve vsi – blikají jí horní kameny“: sousední kameny koruny se překrývaly (0,48 m na rozteč 0,41 m)
			# se svrchní plochou v téže výšce → blikání; střídavě o 2,5 cm výš/níž a mírně nakloněné, překryv jen v té nižší
			var dy := 0.0125 if k % 2 == 0 else -0.0125
			var tgk := tg.rotated(Vector3.UP, rng.randf_range(-0.12, 0.12))
			sit.kvadr("valoun", Vector3(c.x, c.y + h + 0.04 + dy, c.z) + dr * rm, tgk, Vector3.UP.rotated(tgk, rng.randf_range(-0.04, 0.04)), Vector3.ZERO, Vector3(0.46 * rng.randf_range(0.92, 1.05), 0.1, tl + 0.08))
		var t := sit.s("tma")   # hladina hluboko dole: tma
		for i in 16:
			var f0 := TAU * i / 16.0; var f1 := TAU * (i + 1) / 16.0
			var q0 := c + Vector3(0, 0.3, 0); var q1 := q0 + (x * cos(f0) + z * sin(f0)) * (ri + 0.06); var q2 := q0 + (x * cos(f1) + z * sin(f1)) * (ri + 0.06)
			var tri := [q0, q1, q2] if Vector3.UP.dot((q1 - q0).cross(q2 - q0)) < 0 else [q0, q2, q1]   # přední strana nahoru (jako Sit.quad: vektorový součin proti normále)
			for p: Vector3 in tri:
				t.set_normal(Vector3.UP); t.set_uv(Vector2.ZERO); t.add_vertex(p - c)
		# sloupy vně roubení, pražec, vzpěry (čep a dlab – vzpěra osedlaná na sloupu a pražci)
		var hs := float(sp["sloupy_m"]); var xs := ro + float(sp.get("sloupy_od_okraje_m", 0.1)) + 0.08
		for sx: float in [-1.0, 1.0]:
			var q := c + x * sx * xs
			sit.kvadr("tram", q + Vector3(0, (hs - 0.4) / 2, 0), x, Vector3.UP, z, Vector3(0.16, hs + 0.4, 0.16))
			var b0 := q + Vector3(0, hs - 0.62, 0) - x * sx * 0.08; var b1 := q - x * sx * 0.5 + Vector3(0, hs - 0.06, 0)
			var bx := (b1 - b0).normalized()
			sit.kvadr("tram", (b0 + b1) / 2, bx, z.cross(bx).normalized(), z, Vector3(b0.distance_to(b1), 0.09, 0.09))
		sit.kvadr("tram", c + Vector3(0, hs + 0.05, 0), x, Vector3.UP, z, Vector3(2.0 * xs + 0.5, 0.15, 0.17))
		# rumpál s klikou a lano s vědrem
		var ry := float(sp.get("rumpal_y_m", 1.55)); var rr := float(sp.get("rumpal_r_m", 0.11)); var kl := float(sp.get("klika_m", 0.35))
		sit.valec("kura", c + x * -(xs + 0.12) + Vector3(0, ry, 0), c + x * (xs + 0.14) + Vector3(0, ry, 0), rr, rr, 10)
		var ka := c + x * (xs + 0.16) + Vector3(0, ry, 0)
		sit.kvadr("tram", ka + Vector3(0, -kl / 2, 0), z, Vector3.UP, x, Vector3(0.05, kl + 0.05, 0.05))
		sit.valec("kura", ka + Vector3(0, -kl, 0), ka + Vector3(0, -kl, 0) + x * 0.22, 0.025, 0.025, 6)
		var vr := float(sp.get("vedro_r_m", 0.15)); var vh := float(sp.get("vedro_v_m", 0.3))
		var vd := c + x * 0.28 + z * rm + Vector3(0, h + 0.08, 0)
		sit.valec("vrata", vd, vd + Vector3(0, vh, 0), vr * 0.88, vr, 10)
		for yy: float in [0.06, vh - 0.06]: sit.valec("tma", vd + Vector3(0, yy - 0.015, 0), vd + Vector3(0, yy + 0.015, 0), vr * 0.93 + 0.008, vr * 0.95 + 0.008, 10)
		sit.valec("kura", c + x * 0.28 + Vector3(0, ry - rr, 0), vd + Vector3(0, vh + 0.12, 0), 0.012, 0.012, 4)
		# sedlová stříška z prken (šindel) nad pražcem
		var hr := c + Vector3(0, hs + 0.55, 0); var ss := float(sp.get("strisky_sirka_m", 2.4))
		for su: float in [-1.0, 1.0]:
			var ok := c + Vector3(0, hs - 0.05, 0) + z * su * 0.85
			var yv := (hr - ok).normalized(); var zv := x.cross(yv).normalized() * (1.0 if su > 0 else -1.0)
			sit.kvadr("sindel", (hr + ok) / 2 + zv * 0.03, x, yv, zv, Vector3(ss, hr.distance_to(ok) + 0.14, 0.05))
		sit.kvadr("tram", hr + Vector3(0, -0.06, 0), x, Vector3.UP, z, Vector3(ss + 0.1, 0.12, 0.12))
		var mi := MeshInstance3D.new(); mi.name = "Studna"; mi.mesh = sit.mesh(); mi.position = c
		mi.visibility_range_end = _f("ploty_do_m", "ploty_do_m_mobil") * 2.0
		add_child(mi)
		var kb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var cy := CylinderShape3D.new()
		cy.radius = ro; cy.height = h + 0.2; cs.shape = cy; cs.position = Vector3(0, (h - 0.2) / 2, 0); kb.add_child(cs)
		for sx: float in [-1.0, 1.0]:
			var cp := CollisionShape3D.new(); var bs := BoxShape3D.new(); bs.size = Vector3(0.18, hs, 0.18); cp.shape = bs
			cp.position = x * sx * xs + Vector3(0, hs / 2, 0); kb.add_child(cp)
		mi.add_child(kb)


## plášť válce (střed paty c, výška h, poloměr r, n stěn); smer +1 normály ven, −1 dovnitř
func _valec_plast(sit: Sit, k: String, c: Vector3, h: float, r: float, x: Vector3, z: Vector3, n: int, smer: float) -> void:
	var vm: float = _mat[k][1] if _mat.has(k) else 1.0
	for i in n:
		var f0 := TAU * i / n; var f1 := TAU * (i + 1) / n
		var d0 := x * cos(f0) + z * sin(f0); var d1 := x * cos(f1) + z * sin(f1)
		var a := c + d0 * r; var b := c + d1 * r; var e := c + d0 * r + Vector3(0, h, 0); var g := c + d1 * r + Vector3(0, h, 0)
		var u0 := r * f0 / vm; var u1 := r * f1 / vm
		# quad: normála (b−a)×(e−a) – při chybném směru prohodit pořadí (Godot: přední strana po směru hodinových ručiček)
		if (b - a).cross(e - a).dot((d0 + d1) * smer) > 0.0: sit.quad(k, a, b, g, e, Vector2(u0, h / vm), Vector2(u1, 0))
		else: sit.quad(k, b, a, e, g, Vector2(u1, h / vm), Vector2(u0, 0))


## ------------------------------------------------------------------ venkovní sezení krčmy (mista.json typy.krcma.sezeni)
## modely Havrana (stul_hospoda, lavice_selska) jako u hostince Havrana (kraj.py STOLY_VENKU), kolize z rozměru katalogu
func _sezeni() -> void:
	if not d.has("sezeni"): return
	var uzel := Node3D.new(); uzel.name = "Sezeni"; add_child(uzel)
	var dosah := _f("drobne_do_m") * 2.0
	for e: Dictionary in d["sezeni"]:
		var mid := String(e["model"]); var p := PH + mid + ".glb"
		if not ResourceLoader.exists(p): continue
		var n: Node3D = (load(p) as PackedScene).instantiate(); n.name = mid
		n.transform = Transform3D(Basis(Vector3.UP, float(e["yaw"])), Vector3(float(e["x"]), float(e["y"]), float(e["z"])))
		for g in n.find_children("*", "GeometryInstance3D", true, false): (g as GeometryInstance3D).visibility_range_end = dosah
		var info: Dictionary = _kat.get(mid, {})
		if info.has("rozmer"):
			var r: Array = info["rozmer"]; var kb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var bs := BoxShape3D.new()
			bs.size = Vector3(float(r[0]) * 0.95, float(r[1]), float(r[2]) * 0.95); cs.shape = bs; cs.position.y = float(r[1]) * 0.5
			kb.add_child(cs); n.add_child(kb)
		uzel.add_child(n)


## ------------------------------------------------------------------ drobnosti a proutěné ploty (MultiMesh po buňkách)
func _sit_modelu(mid: String) -> Array:
	if _site.has(mid): return _site[mid]
	var p := PH + mid + ".glb"
	if not ResourceLoader.exists(p): _site[mid] = []; return []
	var sc: Node = (load(p) as PackedScene).instantiate()
	var mis: Array = sc.find_children("*", "MeshInstance3D", true, false)
	_site[mid] = [(mis[0] as MeshInstance3D).mesh, _xf_ve_scene(mis[0], sc)] if not mis.is_empty() else []
	sc.free()
	return _site[mid]


func _drobne() -> void:
	var B := float(lod["bunka_m"])
	var dosah_d := _f("drobne_do_m"); var dosah_z := _f("zahony_do_m"); var dosah_p := _f("ploty_do_m", "ploty_do_m_mobil")
	var vrstvy := {}
	for k in [["drobne", dosah_d], ["zahony", dosah_z], ["ploty", dosah_p]]:
		var bk: Node3D = BunkyKolem.new(); bk.name = "Ves_" + String(k[0]); bk.B = B; bk.R = float(k[1]) + B * 0.75 + 4.0
		var dosah: float = k[1]
		bk.vyrob = func(sk: String, buf: PackedFloat32Array, n: int) -> Array:
			var sm: Array = _sit_modelu(sk)
			if sm.is_empty(): return []
			var mmi := BunkyKolem.mmi(sm[0], buf, n); mmi.visibility_range_end = dosah
			var vel := (sm[0] as Mesh).get_aabb().size
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if maxf(vel.x, maxf(vel.y, vel.z)) >= float(lod["stin_drobne_od_m"]) \
				else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			return [mmi]
		add_child(bk); vrstvy[k[0]] = bk
	for e: Dictionary in d["drobne"]:
		var mid := String(e["model"]); var sm := _sit_modelu(mid)
		if sm.is_empty(): continue
		var t := Transform3D(Basis(Vector3.UP, float(e["yaw"])), Vector3(float(e["x"]), float(e["y"]), float(e["z"]))) * (sm[1] as Transform3D)
		var vr: String = "zahony" if (mid.begins_with("zahon") or mid in ["panak_snopu", "kupka_sena", "zebrinak"]) else "drobne"
		vrstvy[vr].pridej(t, mid)
	# proutěné ploty z dílů plutek (2,07 m): díly po délce, náklon podle terénu, délka dorovnaná měřítkem
	var pp: Dictionary = d["ploty_pravidla"]["proutěny"]; var dl := float(pp["delka_m"]); var mid_p := String(pp["model"])
	var smp := _sit_modelu(mid_p)
	if smp.is_empty(): return
	for p: Dictionary in d["ploty"]:
		if String(p["druh"]) != "proutěny": continue
		var body: Array = (p["body"] as Array).map(func(q: Array) -> Vector3: return Vector3(float(q[0]), float(q[1]), float(q[2])))
		var L := _delka(body); var n := maxi(1, roundi(L / dl)); var sk := L / (n * dl)
		for i in n:
			var p0 := _y_na(body, L * i / n); var p1 := _y_na(body, L * (i + 1) / n)
			var yaw := atan2(-(p1.z - p0.z), p1.x - p0.x); var sklon := atan2(p1.y - p0.y, Vector2(p1.x - p0.x, p1.z - p0.z).length())
			var bas := Basis(Vector3.UP, yaw) * Basis(Vector3.BACK, sklon) * Basis.from_scale(Vector3(sk, 1.0, 1.0))
			vrstvy["ploty"].pridej(Transform3D(bas, (p0 + p1) / 2 - Vector3(0, 0.04, 0)) * (smp[1] as Transform3D), mid_p)


## ------------------------------------------------------------------ stromy (jabloně, lípy)
func _stromy() -> void:
	var md: Dictionary = d["modely"]["stromy"]
	var uzel := Node3D.new(); uzel.name = "Stromy"; add_child(uzel)
	var b1 := _f("strom_podrobny_do_m"); var b2 := _f("strom_lod1_do_m"); var b3 := _f("strom_daleko_do_m")
	var sceny := {}
	for s: Dictionary in d["stromy"]:
		var dr := String(s["druh"])
		if not md.has(dr): continue
		var e: Dictionary = md[dr]; var klic := dr
		if e.has("varianty"):   # varianty z Disku (jabloně Míši 14. 11.): stálá volba z polohy, podil_mladych mladých stromků
			var hv := absi(hash(Vector2i(roundi(float(s["x"]) * 10.0), roundi(float(s["z"]) * 10.0))))
			var ml := float(hv % 1000) / 1000.0 < float(e.get("podil_mladych", 0.0)) and not bool(s.get("stara", false))
			var vs: Array = (e["varianty"] as Array).filter(func(v: Dictionary) -> bool: return bool(v.get("mlada", false)) == ml)
			if vs.is_empty(): vs = e["varianty"]
			var vi := (hv / 1000) % vs.size(); e = vs[vi]; klic = "%s_%s_%d" % [dr, "m" if ml else "s", vi]
		if not sceny.has(klic):
			var a := []
			for k in ["soubor", "lod1", "daleko"]:
				a.append(load(String(e[k])) if e.has(k) and ResourceLoader.exists(String(e[k])) else null)
			sceny[klic] = a
		var sc: Array = sceny[klic]
		var xf := Transform3D(Basis(Vector3.UP, float(s["yaw"])).scaled(Vector3.ONE * float(s["meritko"])), Vector3(float(s["x"]), float(s["y"]), float(s["z"])))
		var rozsahy := [[0.0, b1], [b1, b2], [b2 if sc[1] else b1, b3]]
		for k in 3:
			if sc[k] == null: continue
			var n: Node3D = (sc[k] as PackedScene).instantiate(); n.transform = xf; n.name = "%s_%d" % [dr, k]
			if dr == "jablon": _listi(n)
			for g in n.find_children("*", "GeometryInstance3D", true, false):
				(g as GeometryInstance3D).visibility_range_begin = rozsahy[k][0]; (g as GeometryInstance3D).visibility_range_end = rozsahy[k][1]
				(g as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if k == 0 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			uzel.add_child(n)


## Listí jabloně (Havran z_rostliny; Havran svet.gd 9. 11. r. 80: „jabloň není v LISTNACE, listí zůstalo StandardMaterial –
## koruny skvrnité“): stejný shader listí jako les (les.gd _listi, shaders/listi.gdshader) – normály od středu koruny, vítr
var _listi_mat := {}
func _listi(n: Node) -> void:
	for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi.mesh; var bb := m.get_aabb(); var c := bb.get_center()
		for i in m.get_surface_count():
			var om := m.surface_get_material(i) as BaseMaterial3D
			if om == null or om.albedo_texture == null or (om.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED and not om.resource_name.to_lower().contains("list")): continue
			var key := "%d_%d" % [m.get_instance_id(), i]
			if not _listi_mat.has(key):
				var sm := ShaderMaterial.new(); sm.shader = load("res://shaders/listi.gdshader")
				sm.set_shader_parameter("barva", om.albedo_texture); sm.set_shader_parameter("tint", om.albedo_color)
				sm.set_shader_parameter("prah", maxf(om.alpha_scissor_threshold, 0.3))
				sm.set_shader_parameter("stred", Vector3(c.x, bb.position.y + bb.size.y * 0.62, c.z)); sm.set_shader_parameter("vyska", maxf(bb.end.y, 0.5))
				sm.set_shader_parameter("sila_vetru", 0.8); sm.set_shader_parameter("objem", 0.65)
				_listi_mat[key] = sm
			mi.set_surface_override_material(i, _listi_mat[key])
