extends SceneTree
## Test voda_odraz (Misa 9. 11. r. 61/79 „bila ledova plocha“ na rybnicich): hladina se skutecnym materialem vody
## (shaders/voda.gdshader, parametry jako svet.gd material „voda“ + svet.voda_odraz z prostredi.json) a oblohou
## a sluncem hry (scripts/daylight.gd), bez sveta (~20 s). Pohled pri nizkem uhlu (oko 1,7 m nad hladinou) - tam
## fresnel -> 1 a engine bez SSR odrazel jen obzor oblohy. Meri prumerny jas hladiny proti jasu oblohy u obzoru.
## A/B: varianta „stara“ = obzor okoli -90 st (odraz jen oblohy jako pred opravou).
## Spusteni (render): tools/beh.sh fvoda cmd xvfb-run -a -s "-screen 0 1200x800x24" godot --path . --rendering-driver opengl3
##   --rendering-method gl_compatibility --resolution 1200x800 -s res://tools/foto_voda.gd
## Vystup: VODA_ODRAZ <varianta> <doba> hladina <jas> obzor <jas> pomer <p> ; TEST voda_odraz OK|CHYBA; snimky build/foto_voda/

const Svet := preload("res://scripts/svet.gd")
const Pravidla := preload("res://scripts/pravidla.gd")
const DIR := "res://build/foto_voda"

var cam: Camera3D
var den: Node
var mat: ShaderMaterial
var t := 0
var krok := 0
var chyby := 0
class Diag:
	func cas(_co: String, _us: int) -> void:
		pass


const KROKY := [["nova", "odpoledne"], ["nova", "poledne"], ["nova", "rano"], ["stara", "odpoledne"]]


func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(DIR))
	Engine.set_meta("diag", Diag.new())          # daylight.gd meri cas do diag (hra), tady nic
	den = Node.new()
	den.set_script(load("res://scripts/daylight.gd"))
	root.add_child(den)
	den.setup("odpoledne")
	# hladina 120 x 120 m (rybnik), hloubka v barve vrcholu R*4 = 2 m (uprostred tmava, jako nadrz.gd)
	var pm := PlaneMesh.new()
	pm.size = Vector2(120, 120)
	pm.subdivide_width = 24
	pm.subdivide_depth = 24
	var st := SurfaceTool.new()
	st.create_from(pm, 0)
	var arr := st.commit_to_arrays()
	var n: int = (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
	var col := PackedColorArray()
	col.resize(n)
	col.fill(Color(0.5, 0, 0, 1))
	arr[Mesh.ARRAY_COLOR] = col
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	mat = ShaderMaterial.new()
	mat.shader = load("res://shaders/voda.gdshader")
	mat.set_shader_parameter("nmap", load("res://obrazky/voda_normaly.png"))
	var fn := FastNoiseLite.new()           # sum jako svet.gd (okrehek, poryvy)
	fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	fn.frequency = 0.012
	fn.fractal_octaves = 5
	var sum := NoiseTexture2D.new()
	sum.width = 512
	sum.height = 512
	sum.seamless = true
	sum.noise = fn
	sum.generate_mipmaps = true
	mat.set_shader_parameter("sum", sum)
	mat.set_shader_parameter("okrehek", 1.0)
	# stejne jako svet.gd material „voda“ (rybnik dilu, prikop)
	mat.set_shader_parameter("deep", Color(0.08, 0.115, 0.08))
	mat.set_shader_parameter("zakal", Color(0.13, 0.16, 0.11))
	mat.set_shader_parameter("kalnost", 0.82)
	mat.set_shader_parameter("hloubka_vrcholu", true)
	mat.set_shader_parameter("melko_m", float(Pravidla.cti("voda", "stojata_melko_m")))
	Svet.voda_odraz(mat)
	var mi := MeshInstance3D.new()
	mi.mesh = am
	mi.material_override = mat
	root.add_child(mi)
	cam = Camera3D.new()
	cam.fov = 60.0
	root.add_child(cam)
	cam.look_at_from_position(Vector3(0, 1.7, 55), Vector3(0, 1.7 - 55.0 * tan(deg_to_rad(8.0)), 0))    # 8 st pod vodorovnou
	cam.current = true
	_nastav()


func _nastav() -> void:
	var k: Array = KROKY[krok]
	var o: Dictionary = Pravidla.cti("prostredi", "voda_odraz")
	mat.set_shader_parameter("obzor_okoli_st", -90.0 if k[0] == "stara" else float(o["obzor_okoli_st"]))
	den.set_time(k[1], 0.01)
	t = 0


func _process(_d: float) -> bool:
	t += 1
	if t < 40:
		return false
	var img := root.get_viewport().get_texture().get_image()
	var k: Array = KROKY[krok]
	img.save_png(DIR + "/%s_%s.png" % [k[0], k[1]])
	var w := img.get_width()
	var h := img.get_height()
	# hladina: dolni cast obrazu pod obzorem (obzor hladiny ~ 8 st nad stredem), obloha: pas nad obzorem
	var hor := int(h * 0.5 - h * 0.5 * tan(deg_to_rad(8.0)) / tan(deg_to_rad(30.0)))
	var jh := _jas(img, int(w * 0.2), int(w * 0.8), hor + int(h * 0.04), int(h * 0.62))
	var jo := _jas(img, int(w * 0.2), int(w * 0.8), maxi(hor - int(h * 0.08), 0), maxi(hor - int(h * 0.02), 1))
	var tt: Dictionary = (Pravidla.cti("prostredi", "voda_odraz") as Dictionary)["test"]
	var pomer := jh / maxf(jo, 1e-3)
	var ok := pomer <= float(tt["jas_k_obzoru_max"]) and jh >= float(tt["jas_min"])
	print("VODA_ODRAZ %s %s hladina %.3f obzor %.3f pomer %.2f %s" % [k[0], k[1], jh, jo, pomer, "ok" if ok else "MIMO MEZE"])
	if k[0] == "nova" and not ok:
		chyby += 1
	krok += 1
	if krok >= KROKY.size():
		print("TEST voda_odraz %s (chyb %d, meze prostredi.json voda_odraz.test)" % ["OK" if chyby == 0 else "CHYBA", chyby])
		quit(0 if chyby == 0 else 1)
		return true
	_nastav()
	return false


func _jas(img: Image, x0: int, x1: int, y0: int, y1: int) -> float:
	var s := 0.0
	var n := 0
	for y in range(y0, y1, 4):
		for x in range(x0, x1, 4):
			var c := img.get_pixel(x, y)
			s += 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b
			n += 1
	return s / maxf(n, 1)
