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
		var ma_st: bool = sc[1] != null
		for g in n.find_children("*", "GeometryInstance3D", true, false):
			(g as GeometryInstance3D).visibility_range_end = blizko if ma_st else st_do
			(g as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if ma_st else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
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
				_brana(sit, e, pr, kb)
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
func _brana(sit: Sit, e: Dictionary, pr: Dictionary, kb: StaticBody3D) -> void:
	var a := Vector3(float(e["a"][0]), float(e["a"][1]), float(e["a"][2])); var b := Vector3(float(e["b"][0]), float(e["b"][1]), float(e["b"][2]))
	var y := minf(a.y, b.y); a.y = y; b.y = y
	var dn := (b - a); var w := dn.length(); dn /= w; var nrm := Vector3(-dn.z, 0, dn.x)
	var druh := String(e["druh"])
	if druh == "branka":
		var bp: Dictionary = pr["branka"]
		for q: Vector3 in [a, b]: sit.valec("kura", q + Vector3(0, -0.4, 0), q + Vector3(0, 1.25, 0), 0.075, 0.068)
		var wl := w - 0.16; var n := 7
		for i in n:
			var x0 := 0.08 + wl * i / n + 0.008; var x1 := 0.08 + wl * (i + 1) / n - 0.008; var hh := float(bp["vyska_m"])
			var o := a + Vector3(0, 0.08, 0)
			sit.hranol("lata", [o + dn * x0, o + dn * x1, o + dn * x1 + Vector3(0, hh - 0.04, 0), o + dn * (x0 + x1) / 2 + Vector3(0, hh, 0), o + dn * x0 + Vector3(0, hh - 0.04, 0)], nrm, 0.022)
		for yy: float in [0.2, 0.85]: sit.kvadr("vrata", a + dn * (w / 2) + Vector3(0, 0.08 + yy, 0) - nrm * 0.03, dn, Vector3.UP, nrm, Vector3(wl, 0.09, 0.035))
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
	# dvě křídla z prken (5 prken, svlaky nahoře a dole, vzpěra)
	var hk := float(vp["kridla_m"]); var wl := w / 2 - 0.14
	for side: float in [-1.0, 1.0]:
		var hp := (a + dn * 0.13) if side < 0 else (b - dn * 0.13); var x_ := dn * (-side)
		for i in 5:
			var x0 := 0.03 + (wl - 0.03) * i / 5.0; var x1 := 0.03 + (wl - 0.03) * (i + 1) / 5.0 - 0.012
			var top := hk + 0.1 * sin((x0 + x1) / 2 / wl * PI / 2)
			sit.kvadr("vrata", hp + x_ * (x0 + x1) / 2 + Vector3(0, 0.06 + top / 2, 0), x_, Vector3.UP, nrm, Vector3(x1 - x0, top, 0.04))
		for yy: float in [0.3, hk - 0.3]:
			sit.kvadr("vrata", hp + x_ * wl / 2 + Vector3(0, 0.06 + yy, 0) - nrm * 0.04, x_, Vector3.UP, nrm, Vector3(wl - 0.05, 0.12, 0.04))
		var bp0 := hp + x_ * 0.1 + Vector3(0, 0.36, 0) - nrm * 0.045; var bp1 := hp + x_ * (wl - 0.1) + Vector3(0, hk - 0.36, 0) - nrm * 0.045
		var bx := (bp1 - bp0).normalized()
		sit.kvadr("vrata", (bp0 + bp1) / 2, bx, nrm.cross(bx).normalized() * -1.0, nrm, Vector3(bp0.distance_to(bp1), 0.1, 0.035))
	var cs := CollisionShape3D.new(); var bs := BoxShape3D.new(); bs.size = Vector3(w, hk, 0.1); cs.shape = bs
	cs.transform = Transform3D(Basis(Vector3.UP, atan2(-dn.z, dn.x)), (a + b) / 2 + Vector3(0, hk / 2, 0)); kb.add_child(cs)


## ------------------------------------------------------------------ studna na návsi (Havran vesnice.py well)
func _studny() -> void:
	var sp: Dictionary = d["studna_pravidla"]
	for s: Dictionary in d["studny"]:
		var c := Vector3(float(s["x"]), float(s["y"]), float(s["z"]))
		var sit := Sit.new(c, _mat); var yaw := float(s["yaw"])
		var x := Vector3(cos(yaw), 0, -sin(yaw)); var z := Vector3(sin(yaw), 0, cos(yaw))
		var ro := float(sp["polomer_m"]); var ri := ro - 0.2; var h := float(sp["vyska_m"]); var n := 16
		for i in n:   # kamenná roubenka: vnější a vnitřní plášť, koruna
			var f0 := TAU * i / n; var f1 := TAU * (i + 1) / n
			var d0 := x * cos(f0) + z * sin(f0); var d1 := x * cos(f1) + z * sin(f1)
			var y0 := c + Vector3(0, -0.2, 0); var y1 := c + Vector3(0, h, 0)
			var u0 := ro * f0 / 1.0; var u1 := ro * f1 / 1.0
			sit.quad("kamen", y0 + d0 * ro, y0 + d1 * ro, y1 + d1 * ro, y1 + d0 * ro, Vector2(u0, h + 0.2), Vector2(u1, 0))
			sit.quad("kamen", y0 + d1 * ri, y0 + d0 * ri, y1 + d0 * ri, y1 + d1 * ri, Vector2(u0, h + 0.2), Vector2(u1, 0))
			sit.quad("kamen", y1 + d0 * ro, y1 + d1 * ro, y1 + d1 * ri, y1 + d0 * ri, Vector2(u0, 0.2), Vector2(u1, 0))
			var t := sit.s("tma")   # tma v šachtě
			for p: Vector3 in [c + Vector3(0, 0.3, 0), c + Vector3(0, 0.3, 0) + d1 * ri, c + Vector3(0, 0.3, 0) + d0 * ri]:
				t.set_normal(Vector3.UP); t.set_uv(Vector2.ZERO); t.add_vertex(p - c)
		for sx: float in [-1.0, 1.0]:
			sit.kvadr("tram", c + x * sx * (ro - 0.1) + Vector3(0, float(sp["sloupy_m"]) / 2, 0), x, Vector3.UP, z, Vector3(0.14, float(sp["sloupy_m"]), 0.14))
		sit.valec("kura", c + x * -(ro - 0.1) + Vector3(0, 1.55, 0), c + x * (ro - 0.1) + Vector3(0, 1.55, 0), 0.11, 0.11, 10)
		var hr := c + Vector3(0, float(sp["sloupy_m"]) + 0.45, 0)
		for su: float in [-1.0, 1.0]:
			var ok := c + Vector3(0, float(sp["sloupy_m"]) - 0.1, 0) + z * su * 0.75
			var yv := (hr - ok).normalized(); var zv := x.cross(yv).normalized() * (1.0 if su > 0 else -1.0)
			sit.kvadr("sindel", (hr + ok) / 2 + zv * 0.03, x, yv, zv, Vector3(2.2, hr.distance_to(ok) + 0.12, 0.05))
		var mi := MeshInstance3D.new(); mi.name = "Studna"; mi.mesh = sit.mesh(); mi.position = c
		mi.visibility_range_end = _f("ploty_do_m", "ploty_do_m_mobil") * 2.0
		add_child(mi)
		var kb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var cy := CylinderShape3D.new()
		cy.radius = ro; cy.height = h + 0.2; cs.shape = cy; cs.position = Vector3(0, (h - 0.2) / 2, 0); kb.add_child(cs); mi.add_child(kb)


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
		if not sceny.has(dr):
			var e: Dictionary = md[dr]; var a := []
			for k in ["soubor", "lod1", "daleko"]:
				a.append(load(String(e[k])) if e.has(k) and ResourceLoader.exists(String(e[k])) else null)
			sceny[dr] = a
		var sc: Array = sceny[dr]
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
