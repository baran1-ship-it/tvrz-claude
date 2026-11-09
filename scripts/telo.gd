extends Node3D
## Telo hrace v prvni osobe (radce 27. 10. 21:20 bod 6, Misa: „ruce s plnou animaci, jak v KCD2, ale at se to neseka“).
## Jako v KCD: hrac je cela postava (Quaternius Universal Base Characters + selsky odev, CC0), kamera v hlave; ruce jsou
## ruce tela, ne samostatny model. Animace z Quaternius Universal Animation Library 1 + 2 (CC0, stejna kostra 65 kosti,
## bez retargetu, bez root motion; modely/postavy/anim/UAL*.glb jen kostra + klipy).
## Plynulost (Misa): kamera NENI prilepena na kost hlavy (kyvani hlavy pri chuzi = trhani obrazu a nevolnost) - kamera
## zustava hladka (player.gd), telo se pod ni posouva: hlava modelu tesne za kamerou, trup se otaci s pohledem do stran
## s mirnym zpozdenim, pri pohledu dolu je videt trup a nohy, pri akcich ruce. Hlava se nekresli (odev bez hlavy).
## Tablet (pravidla_modelu.json trida postava): jedna kostra, stin jen ze stinove kopie (hrdina), AnimationTree jen kdyz
## hrac neni v letu; mimo kameru (pohled nahoru) se kostra dal pocita (drobnost: 65 kosti).

const DIR := "res://modely/postavy/"
const HRDINA := "res://modely/postavy/hrdina/hrac_cela.gltf"
const Pravidla := preload("res://scripts/pravidla.gd")
# cisla z pravidla/svet/jizda.json (telo)
static var RAMENA_MAX := float(Pravidla.cti("jizda", "telo", "ramena_k_pohledu_max_st"))
static var KLIPY: Dictionary = Pravidla.cti("jizda", "telo", "klipy_m_s")
static var OKO_PRED := float(Pravidla.cti("jizda", "telo", "oko_pred_hlavou_m"))     # oko pred kosti hlavy (sit hlavy)
static var DOLU_VZAD := float(Pravidla.cti("jizda", "telo", "hlava_dolu_vzad_m"))    # pri pohledu dolu krk vpred
static var OTOCENI_TRUPU := float(Pravidla.cti("jizda", "telo", "otoceni_trupu"))  # jak rychle trup dobiha pohled
static var VE_STANI := deg_to_rad(float(Pravidla.cti("jizda", "telo", "otoceni_ve_stani_st")))
static var BOK_MAX := deg_to_rad(float(Pravidla.cti("jizda", "telo", "bok_max_st")))
static var VZAD_OD := deg_to_rad(float(Pravidla.cti("jizda", "telo", "vzad_od_st")))
static var SED := float(Pravidla.cti("jizda", "telo", "sed_m"))
static var SED_V_SEDLE: Dictionary = Pravidla.cti("jizda", "telo", "sed_v_sedle")
static var STEHNO_VPRED := deg_to_rad(float(SED_V_SEDLE["stehno_vpred_st"]))
static var STEHNO_VEN := deg_to_rad(float(SED_V_SEDLE["stehno_ven_st"]))
static var LYTKO_VZAD := deg_to_rad(float(SED_V_SEDLE["lytko_vzad_st"]))
static var LYTKO_VEN := deg_to_rad(float(SED_V_SEDLE["lytko_ven_st"]))
static var PANEV_NAD := float(SED_V_SEDLE["panev_nad_sedlem_m"])
static var SAH: Dictionary = Pravidla.cti("jizda", "telo", "sahnuti")
static var LEZ: Dictionary = Pravidla.cti("jizda", "telo", "lezeni")
static var HOUP: Dictionary = (Pravidla.cti("jizda", "telo", "drzeni") as Dictionary)["houpani"]
static var VZABERU: Dictionary = (Pravidla.cti("jizda", "telo", "drzeni") as Dictionary)["v_zaberu"]
static var OTEZI: Dictionary = Pravidla.cti("jizda", "telo", "otezi")
static var OTEZI_REMEN: Dictionary = Pravidla.cti("jizda", "kun", "otezi")
var _houp_yaw := 0.0                    # zpozdeni ruky za otacenim (pruzina)
var _yaw_minule := 0.0
var _faze := 0.0
const PRSTY := ["index_01", "index_02", "index_03", "middle_01", "middle_02", "middle_03", "ring_01", "ring_02", "ring_03",
		"pinky_01", "pinky_02", "pinky_03", "thumb_02", "thumb_03"]
const AKCE := {"pouzit": "Interact", "sebrat": "PickUp_Table", "otevrit": "Chest_Open", "jist": "Consume",
		"skok": "Jump_Start", "dopad": "Jump_Land", "lezt": "ClimbUp_1m"}
# drzeni predmetu: klip, ze ktereho se bere poza ruky (ostatni kosti z pohybu)
const HORNI := ["spine_02", "spine_03", "neck_01", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l",
		"lowerarm_r", "hand_l", "hand_r", "thumb_01_l", "thumb_02_l", "thumb_03_l", "index_01_l", "index_02_l", "index_03_l",
		"middle_01_l", "middle_02_l", "middle_03_l", "ring_01_l", "ring_02_l", "ring_03_l", "pinky_01_l", "pinky_02_l",
		"pinky_03_l", "thumb_01_r", "thumb_02_r", "thumb_03_r", "index_01_r", "index_02_r", "index_03_r", "middle_01_r",
		"middle_02_r", "middle_03_r", "ring_01_r", "ring_02_r", "ring_03_r", "pinky_01_r", "pinky_02_r", "pinky_03_r"]
const DRZENI := {"louc": ["Idle_Torch_Loop", "r"], "lucerna": ["Idle_Lantern_Loop", "r"]}

var player: CharacterBody3D
var kostra: Skeleton3D
var ap: AnimationPlayer
var at: AnimationTree
var _yaw_trup := 0.0
var _drzi := ""
var _vyska := 1.0                 # meritko tela, aby oci modelu byly ve vysce kamery
var ruka_r: BoneAttachment3D      # sem patri predmet v prave ruce
var ruka_l: BoneAttachment3D
var _vzduch := 0.0
var _byl_ve_vzduchu := false
var _hlava_lok := Vector3.ZERO      # kost hlavy v soustave tela (vyhlazena) - telo se stavi podle hlavy (r. 73)
var _hlava_ok := false
var _cesta := ""                  # cesta ke kostre od korene animaci (stopy klipu i filtr ruky)


func setup(p_player: CharacterBody3D, muz := true) -> bool:
	player = p_player
	# mlady hrdina v dobovem odevu (Misa 5. 11.; tools/postavy_q hrac), bez nej stary selsky odev Quaternius
	var hrdina := muz and ResourceLoader.exists(HRDINA)
	var odev: PackedScene = load(HRDINA if hrdina else DIR + ("Male_Peasant.gltf" if muz else "Female_Peasant.gltf"))
	if odev == null:
		return false
	var o := odev.instantiate()
	add_child(o)
	var sk := o.find_children("*", "Skeleton3D", true, false)
	if sk.is_empty():
		return false
	kostra = sk[0] as Skeleton3D
	for mi in o.find_children("*", "GeometryInstance3D", true, false):
		var g := mi as GeometryInstance3D
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		g.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		g.extra_cull_margin = 1.0          # kostra hybe siti mimo klidovy obal (ruce pred kamerou)
		if hrdina and mi is MeshInstance3D:
			_bez_hlavy(mi as MeshInstance3D)
	# vyska oci modelu (klidova kostra): stred hlavy ~ oci
	var hl := kostra.find_bone("Head")
	var oci := kostra.get_bone_global_rest(hl).origin.y + 0.07 if hl >= 0 else 1.65
	_vyska = player.EYE / oci
	scale = Vector3.ONE * _vyska
	# animace: klipy obou knihoven do jedne knihovny; stopy prepsane na nasi kostru
	ap = AnimationPlayer.new()
	ap.name = "Animace"
	add_child(ap)
	ap.root_node = NodePath("..")
	_cesta = String(get_path_to(kostra))
	var lib: AnimationLibrary = preload("res://scripts/anim_ual.gd").knihovna(_cesta)
	ap.add_animation_library("", lib)
	# kazdy klip, ktery strom pouziva, musi v knihovne byt (jinak tise T-poza)
	var chybi: Array = []
	for jm: String in ["Idle_Loop", "Walk_Loop", "Jog_Fwd_Loop", "Sprint_Loop", "Jump_Loop", "Interact", "Driving_Loop"] + AKCE.values() + DRZENI.values().map(func(v: Array) -> String: return v[0]):
		if not lib.has_animation(jm):
			chybi.append(jm)
	if not chybi.is_empty():
		push_error("telo hrace: v knihovne chybi klipy %s" % str(chybi))
	_strom()
	ruka_r = BoneAttachment3D.new()
	ruka_r.bone_name = "hand_r"
	kostra.add_child(ruka_r)
	ruka_l = BoneAttachment3D.new()
	ruka_l.bone_name = "hand_l"
	kostra.add_child(ruka_l)
	_yaw_trup = player.yaw
	print("telo hrace: %d klipu, meritko %.3f" % [lib.get_animation_list().size(), _vyska])
	if at == null:
		push_error("telo hrace: strom animaci nevznikl")
		return false
	return true


## Hrdina je jedna sit (hlava, vlasy, telo+odev): kamera je v hlave, takze se kresli jen povrch tela a odevu;
## cela postava vcetne hlavy vrha stin (jen stin) - hrac vidi na zemi svuj stin (snimek pohledu dolu 5. 11.).
func _bez_hlavy(mi: MeshInstance3D) -> void:
	var m := mi.mesh as ArrayMesh
	if m == null:
		return
	var tel := ArrayMesh.new()
	tel.blend_shape_mode = m.blend_shape_mode
	for i in m.get_blend_shape_count():
		tel.add_blend_shape(m.get_blend_shape_name(i))
	for si in m.get_surface_count():
		var mat := m.surface_get_material(si)
		var jm := String(mat.resource_name) if mat else ""
		if not jm.contains("obleceni"):          # hlava (kuze, oci) a vlasy - jen stin
			continue
		tel.add_surface_from_arrays(m.surface_get_primitive_type(si), m.surface_get_arrays(si), m.surface_get_blend_shape_arrays(si))
		tel.surface_set_material(tel.get_surface_count() - 1, mat)
	if tel.get_surface_count() == 0:
		return
	var v := MeshInstance3D.new()
	v.name = mi.name + "_bez_hlavy"
	v.mesh = tel
	v.skin = mi.skin
	mi.get_parent().add_child(v)
	v.skeleton = v.get_path_to(mi.get_node(mi.skeleton))
	v.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	v.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	v.extra_cull_margin = 1.0
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY


## AnimationTree: pohyb (stani - chuze - klus - beh podle rychlosti), poza ruky pri drzeni predmetu (jen kosti ruky),
## jednorazova akce pres vse (pouzit, sebrat, otevrit, jist).
func _strom() -> void:
	at = AnimationTree.new()
	at.name = "Strom"
	add_child(at)
	at.anim_player = at.get_path_to(ap)
	var bt := AnimationNodeBlendTree.new()
	var bs := AnimationNodeBlendSpace1D.new()
	# body prolnuti = rychlost, kterou klip sam jde (jizda.json telo.klipy_m_s, test_klipy_chuze) - nohy nekluzou;
	# sync: chuze a klus v prolnuti ve stejne fazi kroku (jinak se mezi body michaly dva ruzne kroky)
	for b: Array in [["Idle_Loop", 0.0], ["Walk_Loop", float(KLIPY["Walk_Loop"])], ["Jog_Fwd_Loop", float(KLIPY["Jog_Fwd_Loop"])], ["Sprint_Loop", float(KLIPY["Sprint_Loop"])]]:
		var n := AnimationNodeAnimation.new()
		n.animation = b[0]
		bs.add_blend_point(n, b[1])
	bs.sync = true
	bs.min_space = 0.0
	bs.max_space = float(KLIPY["Sprint_Loop"]) * 2.0
	bt.add_node("pohyb", bs)
	# rychlost klipu podle skutecne rychlosti (nohy nekluzou); zaporna = chuze pozpatku
	bt.add_node("tempo", AnimationNodeTimeScale.new())
	var vz := AnimationNodeAnimation.new()
	vz.animation = "Jump_Loop"
	bt.add_node("vzduch_klip", vz)
	var vzb := AnimationNodeBlend2.new()
	bt.add_node("vzduch", vzb)
	var drz := AnimationNodeAnimation.new()
	drz.animation = "Idle_Torch_Loop"
	bt.add_node("drzeni", drz)
	var b2 := AnimationNodeBlend2.new()
	b2.filter_enabled = true
	for kn: String in ["clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "thumb_01_r", "thumb_02_r", "thumb_03_r",
			"index_01_r", "index_02_r", "index_03_r", "middle_01_r", "middle_02_r", "middle_03_r", "ring_01_r", "ring_02_r",
			"ring_03_r", "pinky_01_r", "pinky_02_r", "pinky_03_r"]:
		b2.set_filter_path(NodePath(_cesta + ":" + kn), true)
	bt.add_node("ruka", b2)
	var os := AnimationNodeOneShot.new()
	os.fadein_time = 0.15
	os.fadeout_time = 0.25
	# akce jen horni polovinou tela (od beder nahoru) - nohy dal jdou podle pohybu (jako v KCD: sebrat za chuze)
	os.filter_enabled = true
	for kn: String in HORNI:
		os.set_filter_path(NodePath(_cesta + ":" + kn), true)
	bt.add_node("akce", os)
	var ak := AnimationNodeAnimation.new()
	ak.animation = "Interact"
	bt.add_node("akce_klip", ak)
	bt.connect_node("tempo", 0, "pohyb")
	bt.connect_node("vzduch", 0, "tempo")
	bt.connect_node("vzduch", 1, "vzduch_klip")
	bt.connect_node("ruka", 0, "vzduch")
	bt.connect_node("ruka", 1, "drzeni")
	bt.connect_node("akce", 0, "ruka")
	bt.connect_node("akce", 1, "akce_klip")
	# jizda na koni: cele telo z Driving_Loop (ruce vpred na otezich, sed), stehna do rozkroku pres sedlo (_po_mixu)
	var jz := AnimationNodeAnimation.new()
	jz.animation = "Driving_Loop"
	bt.add_node("jizda_klip", jz)
	bt.add_node("jizda", AnimationNodeBlend2.new())
	bt.connect_node("jizda", 0, "akce")
	bt.connect_node("jizda", 1, "jizda_klip")
	bt.connect_node("output", 0, "jizda")
	at.tree_root = bt
	at.active = true
	at.mixer_applied.connect(_po_mixu)
	at.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_IDLE


## Jednorazova akce (pouzit, sebrat, otevrit, jist, skok...): klip pres cele telo, pak zpet do pohybu.
func akce(co: String) -> void:
	if at == null or not AKCE.has(co):
		return
	var bt := at.tree_root as AnimationNodeBlendTree
	(bt.get_node("akce_klip") as AnimationNodeAnimation).animation = AKCE[co]
	at.set("parameters/akce/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)


## Sahnuti na misto ve svete (Misa 28. 10.: ruka na skutecny cil, ne tupy klip): IK ruky v _po_mixu.
var _sah := {}                          # cil (svet), ruka "r"/"l", t (s od zacatku)


func sahni(cil: Vector3, ruka := "r") -> void:
	_sah = {"cil": cil, "ruka": ruka, "t": 0.0}


func _vaha_sahnuti() -> float:
	if _sah.is_empty():
		return 0.0
	var t := float(_sah["t"])
	var a := float(SAH["prisah_s"])
	var b := a + float(SAH["drzet_s"])
	var c := b + float(SAH["navrat_s"])
	if t >= c:
		_sah = {}
		return 0.0
	if t < a:
		return smoothstep(0.0, a, t)
	if t < b:
		return 1.0
	return 1.0 - smoothstep(b, c, t)


## Natoceni kosti i v soustave kostry o q (globalne), smichane s animaci vahou w.
func _otoc_kost(i: int, q: Quaternion, w: float) -> void:
	var g := kostra.get_bone_global_pose(i)
	var p := kostra.get_bone_parent(i)
	var gp := kostra.get_bone_global_pose(p) if p >= 0 else Transform3D()
	var nova := gp.basis.inverse() * (Basis(q) * g.basis)
	var stara := kostra.get_bone_pose_rotation(i)
	kostra.set_bone_pose_rotation(i, stara.slerp(nova.get_rotation_quaternion().normalized(), w))


static func _q_mezi(a: Vector3, b: Vector3) -> Quaternion:
	if a.length_squared() < 1e-10 or b.length_squared() < 1e-10:
		return Quaternion()
	return Quaternion(a.normalized(), b.normalized())


## Dvoukloubova IK: rameno (upperarm) a loket (lowerarm) tak, aby zapesti (hand) bylo v cili; rovina lokte podle
## animace (loket zustava tam, kam ho dal klip - prirozene dolu a ven), predklon trupu na nizky cil.
func _ik_ruky(w: float, cil_svet: Variant = null, ruka := "", predklon := true) -> void:
	var sx := "_" + (ruka if ruka != "" else String(_sah["ruka"]))
	var iu := kostra.find_bone("upperarm" + sx)
	var il := kostra.find_bone("lowerarm" + sx)
	var ih := kostra.find_bone("hand" + sx)
	var isp := kostra.find_bone("spine_02")
	if iu < 0 or il < 0 or ih < 0:
		return
	var inv := kostra.global_transform.affine_inverse()
	var t := inv * ((cil_svet if cil_svet != null else _sah["cil"]) as Vector3)
	# predklon: cil pod rameny -> trup se sklopi k cili
	var a0 := kostra.get_bone_global_pose(iu).origin
	var pod := a0.y - t.y - float(SAH["pod_rameny_m"]) / maxf(_vyska, 1e-3)
	if predklon and isp >= 0 and pod > 0.0:
		var dh := Vector3(t.x - a0.x, 0.0, t.z - a0.z)
		if dh.length() > 1e-4:
			var uhel := minf(deg_to_rad(float(SAH["predklon_st_na_m"])) * pod * _vyska, deg_to_rad(float(SAH["predklon_max_st"])))
			_otoc_kost(isp, Quaternion(Vector3.UP.cross(dh.normalized()).normalized(), uhel), w)
	var A := kostra.get_bone_global_pose(iu).origin
	var B := kostra.get_bone_global_pose(il).origin
	var C := kostra.get_bone_global_pose(ih).origin
	var la := A.distance_to(B)
	var lb := B.distance_to(C)
	var at_ := t - A
	var d := clampf(at_.length(), absf(la - lb) + 1e-3, la + lb - 1e-3)
	var smer := at_.normalized()
	var pol := (B - A) - smer * (B - A).dot(smer)
	if pol.length_squared() < 1e-8:
		pol = Vector3.DOWN - smer * Vector3.DOWN.dot(smer)
	pol = pol.normalized()
	var cos_a := clampf((la * la + d * d - lb * lb) / (2.0 * la * d), -1.0, 1.0)
	var B2 := A + smer * la * cos_a + pol * la * sqrt(1.0 - cos_a * cos_a)
	var T2 := A + smer * d
	_otoc_kost(iu, _q_mezi(B - A, B2 - A), w)
	var B3 := kostra.get_bone_global_pose(il).origin
	var C3 := kostra.get_bone_global_pose(ih).origin
	_otoc_kost(il, _q_mezi(C3 - B3, T2 - B3), w)
	# uchop: prsty se ve vrcholu sevrou
	var g := smoothstep(0.7, 1.0, w)
	if g > 0.0:
		for pn: String in PRSTY:
			var ip := kostra.find_bone(pn + sx)
			if ip >= 0:
				kostra.set_bone_pose_rotation(ip, kostra.get_bone_pose_rotation(ip) * Quaternion(Vector3.RIGHT, deg_to_rad(float(SAH["uchop_st"])) * g))


## Lezeni (jizda.json telo.lezeni): obe ruce na pricle zebriku, stridave podle vysky na zebriku (prehmat).
func _ruce_na_zebriku() -> void:
	var zb: Dictionary = player.get("_zb")
	if zb.is_empty():
		return
	var a: Vector3 = zb["pata"]
	var b: Vector3 = zb["vrchol"]
	var osa := (b - a).normalized()
	var bok := osa.cross(Vector3.UP).normalized()
	if bok.length() < 0.1:
		bok = Basis(Vector3.UP, float(player.get("yaw"))).x
	var oci: float = (player.get("cam") as Camera3D).global_position.y
	var kr := float(LEZ["pricle_m"])
	var s_oci := (oci + float(LEZ["nad_ocima_m"]) - a.y) / maxf(osa.y, 0.3)     # vzdalenost po zebriku k pricli nad ocima
	var n := floori(s_oci / kr)
	var faze := n % 2                                    # ktera ruka je nahore se strida po kazde pricli
	for r: Array in [["r", 1.0], ["l", -1.0]]:
		var horni: bool = (faze == 0) == (String(r[0]) == "r")
		var s := float(n if horni else n - 1) * kr
		var cil := a + osa * s + bok * float(r[1]) * float(LEZ["bok_m"])
		_ik_ruky(1.0, cil, String(r[0]), false)


## Ruka s predmetem (louc, lucerna): houpani pri chuzi a zpozdeni za otocenim - predlokti a zapesti, z jizda.json
## telo.drzeni.houpani. Pocita _process (faze, pruzina), tady se jen prilozi po animaci.
func _houpani_ruky() -> void:
	var il := kostra.find_bone("lowerarm_r")
	var ih := kostra.find_bone("hand_r")
	if il < 0 or ih < 0:
		return
	var hv := Vector2(player.velocity.x, player.velocity.z).length()
	var kyv := deg_to_rad(float(HOUP["chuze_st"])) * hv * sin(_faze)
	var zp := deg_to_rad(clampf(_houp_yaw * float(HOUP["otoceni_st"]), -25.0, 25.0))
	kostra.set_bone_pose_rotation(il, kostra.get_bone_pose_rotation(il) * Quaternion(Vector3.RIGHT, kyv))
	kostra.set_bone_pose_rotation(ih, kostra.get_bone_pose_rotation(ih) * Quaternion(Vector3.FORWARD, zp) * Quaternion(Vector3.RIGHT, kyv * 0.5))


## Predmet v ruce ("" = nic): poza ruky z klipu drzeni.
func drz(id: String) -> void:
	_drzi = id
	if at == null:
		return
	if DRZENI.has(id):
		((at.tree_root as AnimationNodeBlendTree).get_node("drzeni") as AnimationNodeAnimation).animation = DRZENI[id][0]


## Ramena celem k pohledu (r. 73, test_telo_poza 9. 11.): Idle_Loop i chuze UAL stoji s trupem pootocenym - prave
## rameno 0,22 m za kamerou, leve 0,10 m (cara ramen ~18 st. od pohledu), ruka s louci proto do zaberu nedosahla.
## Jako clovek v KCD (hlava a hrudnik k tomu, kam se diva, nohy do smeru chuze): hrudni obratel (spine_03) se natoci
## kolem svisle tak, aby cara ramen byla kolmo k pohledu kamery, nejvys jizda.json telo.ramena_k_pohledu_max_st.
func _ramena_k_pohledu() -> void:
	var il := kostra.find_bone("upperarm_l")
	var ir := kostra.find_bone("upperarm_r")
	var isp := kostra.find_bone("spine_03")
	if il < 0 or ir < 0 or isp < 0:
		return
	var kg := kostra.global_transform
	var cara := kg * kostra.get_bone_global_pose(ir).origin - kg * kostra.get_bone_global_pose(il).origin
	var vpravo := (player.get("cam") as Camera3D).global_basis.x
	var a := Vector2(cara.x, cara.z)
	var b := Vector2(vpravo.x, vpravo.z)
	if a.length() < 1e-4 or b.length() < 1e-4:
		return
	# uhel kolem svisle osy (svet), o ktery se ma cara ramen otocit k pravemu smeru kamery
	var uh := -a.angle_to(b)
	var mx := deg_to_rad(float(RAMENA_MAX))
	uh = clampf(uh, -mx, mx)
	var osa := (kg.basis.inverse() * Vector3.UP).normalized()
	_otoc_kost(isp, Quaternion(osa, uh), 1.0)


## Po animaci: na koni stehna do rozkroku a lytka dolu k trmenum (Driving_Loop je sed na zidli).
func _po_mixu() -> void:
	if kostra == null or player == null:
		return
	if bool(player.get("climbing")):
		_ruce_na_zebriku()
		return
	if player.get("na_koni") == null:
		_ramena_k_pohledu()
	var w := _vaha_sahnuti()
	if w > 0.0 and String(_sah["ruka"]) == "obe":
		# obe ruce (klika rumpalu, vrata, paka): kazda o pul rozpeti vedle cile, kolmo k pohledu
		var bok := Basis(Vector3.UP, float(player.get("yaw"))).x * float(SAH["obe_rozpeti_m"]) * 0.5
		_ik_ruky(w, (_sah["cil"] as Vector3) + bok, "r")
		_ik_ruky(w, (_sah["cil"] as Vector3) - bok, "l", false)
	elif w > 0.0:
		_ik_ruky(w)
	elif _drzi != "" and VZABERU.has(_drzi):
		# predmet v zaberu kamery (jizda.json telo.drzeni.v_zaberu), houpani chuze jako posun cile
		var hv := Vector2(player.velocity.x, player.velocity.z).length()
		var k: Array = VZABERU[_drzi]
		var cam := player.get("cam") as Camera3D
		var cil := cam.global_transform * Vector3(float(k[0]), float(k[1]) + sin(_faze) * hv * float(VZABERU["chuze_m"]), float(k[2]))
		_ik_ruky(1.0, cil, "r", false)
		# Misa 0.99994 (r. 73) „ruka s louci se trepe a drzi ji spatne“: driv se predmet natacel ke kamere a ruka zustala
		# v poze klipu chuze - louc stala, ruka se kolem ni klepala a nesvirala ji. Ted vede predmet: kost ruky se natoci
		# tak, aby predmet v uchopu z dat (jizda.json telo.drzeni.<id> posun/rot_st, jako v klipu drzeni) mel natoceni
		# rot_kamera_st vuci kamere - ruka svira louc vzdy stejne a nekmita s klipem.
		var rk: Array = (VZABERU["rot_kamera_st"] as Dictionary).get(_drzi, [0.0, 0.0, 0.0])
		var chteno := cam.global_basis.orthonormalized() * Basis.from_euler(Vector3(deg_to_rad(float(rk[0])), deg_to_rad(float(rk[1])), deg_to_rad(float(rk[2]))))
		var ih := kostra.find_bone("hand_r")
		var dr: Dictionary = (Pravidla.cti("jizda", "telo", "drzeni") as Dictionary).get(_drzi, {})
		if ih >= 0 and dr.has("rot_st"):
			var rs: Array = dr["rot_st"]
			var uchop := Basis.from_euler(Vector3(deg_to_rad(float(rs[0])), deg_to_rad(float(rs[1])), deg_to_rad(float(rs[2]))))
			var ruka_svet := chteno * uchop.inverse()
			var ruka_kostra := kostra.global_basis.orthonormalized().inverse() * ruka_svet
			var rod := kostra.get_bone_parent(ih)
			var rod_b := kostra.get_bone_global_pose(rod).basis.orthonormalized() if rod >= 0 else Basis.IDENTITY
			kostra.set_bone_pose_rotation(ih, (rod_b.inverse() * ruka_kostra).orthonormalized().get_rotation_quaternion())
	elif _drzi != "":
		_houpani_ruky()
	if player.get("na_koni") == null:
		if _otezi != null and is_instance_valid(_otezi):
			(_otezi as Node3D).visible = false
		return
	# otezi: obe ruce pred sedlem v zaberu
	var camk := player.get("cam") as Camera3D
	# cil v soustave kone (nad kohoutkem pred sedlem), ne kamery: pri pohledu dolu se ruce s kamerou zvedaly pred
	# oblicej a krizily (Misa 0.991)
	var o: Array = OTEZI["sedlo"]
	var kn: Node3D = player.get("na_koni") as Node3D
	var zak: Vector3 = kn.call("sedlo_global") if kn and kn.has_method("sedlo_global") else camk.global_position
	var kb := kn.global_transform.basis.orthonormalized() if kn else camk.global_transform.basis
	_ik_ruky(1.0, zak + kb * Vector3(float(o[0]), float(o[1]), float(o[2])), "r", false)
	_ik_ruky(1.0, zak + kb * Vector3(-float(o[0]), float(o[1]), float(o[2])), "l", false)
	_nohy_v_sedle(kn)
	_otezi_kresli(kn)


## Otezi (Misa 9. 11. r. 86: ruce na otezich jsou, chybi remeny): scripts/otezi.gd, konce v dlanich (jizda.json kun.otezi.dlan).
var _otezi: Node = null
var _otezi_chyba: Node = null


func _otezi_kresli(kn: Node3D) -> void:
	if _otezi_chyba == kn:
		return                                   # setup pro tohoto kone selhal (hlaseno jednou), nezkouset kazdy snimek
	if _otezi == null or not is_instance_valid(_otezi) or _otezi.get_meta("kun", null) != kn:
		if _otezi != null and is_instance_valid(_otezi):
			_otezi.queue_free()
		_otezi = preload("res://scripts/otezi.gd").new()
		_otezi.set_meta("kun", kn)
		add_child(_otezi)
		if not _otezi.call("setup", kn, OTEZI_REMEN):
			_otezi.queue_free()
			_otezi = null
			_otezi_chyba = kn
			return
	(_otezi as Node3D).visible = true
	var dl: Array = OTEZI_REMEN["dlan"]
	var kg := kostra.global_transform
	var pl := kg * (kostra.get_bone_global_pose(kostra.find_bone("hand_l")) * Vector3(float(dl[0]), float(dl[1]), float(dl[2])))
	var pr := kg * (kostra.get_bone_global_pose(kostra.find_bone("hand_r")) * Vector3(float(dl[0]), float(dl[1]), float(dl[2])))
	_otezi.call("aktualizuj", pl, pr)


## Nohy jezdce v sedle (Misa 4. 11. „hrac drepi na koni“): Driving_Loop je sed na zidli - stehna vodorovne vpred,
## kolena vysoko. Driv se k nemu pridavalo natoceni kolem mistnich os kosti (rozkrok_st, lytka_st), coz kolena nechalo
## nahore a lytka vytocila dozadu (z pohledu dolu nohy roztazene, kolena vpred). Ted se stehno a lytko natoci na
## smer v soustave kone (jizda.json telo.sed_v_sedle): stehno dolu a mirne vpred a ven pres trup kone, lytko skoro
## svisle podel boku do trmenu - sed jako u jezdce 14. stol. (dlouhe trmeny, noha skoro natazena).
func _nohy_v_sedle(kn: Node3D) -> void:
	if kn == null:
		return
	var inv := kostra.global_transform.basis.orthonormalized().inverse()
	var kb := kn.global_transform.basis.orthonormalized()
	var vpred := inv * (-kb.z)
	var dolu := inv * Vector3.DOWN
	for st: Array in [["l", -1.0], ["r", 1.0]]:
		var ven := inv * (kb.x * float(st[1]))           # vlevo / vpravo od kone
		var it := kostra.find_bone("thigh_" + String(st[0]))
		var ic := kostra.find_bone("calf_" + String(st[0]))
		var iff := kostra.find_bone("foot_" + String(st[0]))
		if it < 0 or ic < 0 or iff < 0:
			continue
		var cil_t := (dolu * cos(STEHNO_VPRED) + vpred * sin(STEHNO_VPRED)) * cos(STEHNO_VEN) + ven * sin(STEHNO_VEN)
		var cil_c := (dolu * cos(LYTKO_VZAD) - vpred * sin(LYTKO_VZAD)) * cos(LYTKO_VEN) + ven * sin(LYTKO_VEN)
		var t0 := kostra.get_bone_global_pose(it).origin
		var c0 := kostra.get_bone_global_pose(ic).origin
		_otoc_kost(it, _q_mezi(c0 - t0, cil_t), 1.0)
		var c1 := kostra.get_bone_global_pose(ic).origin
		var f1 := kostra.get_bone_global_pose(iff).origin
		_otoc_kost(ic, _q_mezi(f1 - c1, cil_c), 1.0)


var snimku := 0                         # pocet behu _process (zkouska jizdy: bezi telo?)
var naposled := ""


func _process(delta: float) -> void:
	snimku += 1
	if not _sah.is_empty():
		_sah["t"] = float(_sah["t"]) + delta
	# houpani ruky s predmetem: faze kroku a pruzina zpozdeni za otacenim pohledu
	var yk := float(player.get("yaw")) if player else 0.0
	var om := wrapf(yk - _yaw_minule, -PI, PI) / maxf(delta, 1e-4)
	_yaw_minule = yk
	_houp_yaw = lerpf(_houp_yaw, om, minf(1.0, delta * float(HOUP["tlumeni"])))
	if player:
		_faze += delta * TAU * clampf(Vector2(player.velocity.x, player.velocity.z).length() / 1.4, 0.0, 3.0)
	if player == null or at == null:
		naposled = "bez hrace %s / stromu %s (snimek %d)" % [player == null, at == null, Engine.get_process_frames()]
		return
	var kon: Node = player.get("na_koni")
	at.set("parameters/jizda/blend_amount", 1.0 if kon != null else 0.0)
	visible = not bool(player.get("flying")) and not bool(player.get("seated"))
	at.active = visible
	if not visible:
		naposled = "skryte (let/sed/lezeni)"
		return
	naposled = "poloha"
	var hv := Vector2(player.velocity.x, player.velocity.z).length()
	var yaw_k := float(player.get("yaw"))
	# smer chuze vuci pohledu: do strany se telo natoci do smeru pohybu (UAL nema ukroky), dozadu jde pozpatku
	var cil := yaw_k
	var vzad := false
	if hv > 0.3:
		var smer_v := atan2(-player.velocity.x, -player.velocity.z)          # yaw, kterym by se hrac koukal po pohybu
		var rel := wrapf(smer_v - yaw_k, -PI, PI)
		if absf(rel) > VZAD_OD:
			vzad = true
			rel = wrapf(rel + PI, -PI, PI)
		cil = yaw_k + clampf(rel, -BOK_MAX, BOK_MAX)
	at.set("parameters/pohyb/blend_position", hv)
	# tempo: mezi body prolnuti 1 (body = rychlosti klipu), pod chuzi a nad sprintem rychlost / rychlost klipu
	var vw := float(KLIPY["Walk_Loop"])
	var vs := float(KLIPY["Sprint_Loop"])
	var tempo := 1.0
	if hv > 0.3 and hv < vw:
		tempo = clampf(hv / vw, 0.5, 1.0)
	elif hv > vs:
		tempo = hv / vs
	at.set("parameters/tempo/scale", -tempo if vzad else tempo)
	var ve_vzduchu := not player.is_on_floor() and absf(player.velocity.y) > 1.0
	_vzduch = move_toward(_vzduch, 1.0 if ve_vzduchu else 0.0, delta * 6.0)
	at.set("parameters/vzduch/blend_amount", _vzduch)
	if _byl_ve_vzduchu and not ve_vzduchu and _vzduch > 0.5:
		akce("dopad")
	_byl_ve_vzduchu = ve_vzduchu
	at.set("parameters/ruka/blend_amount", 1.0 if _drzi != "" else 0.0)
	if kon != null:
		cil = (kon as Node3D).rotation.y                 # na koni telo ve smeru kone, hlava (kamera) se rozhlizi
		hv = 1.0
	# trup dobiha cil (pri chuzi hned, ve stani az kdyz se hrac otoci o vic nez 50 st. - jako clovek)
	var d := wrapf(cil - _yaw_trup, -PI, PI)
	if hv > 0.3 or absf(d) > VE_STANI:
		_yaw_trup += d * minf(1.0, delta * OTOCENI_TRUPU)
	# poloha: hlava tesne za kamerou (kamera je v player.gd hladka, bez kyvani kosti hlavy)
	var c: Vector3 = (player.get("cam") as Camera3D).global_position
	var smer := Basis(Vector3.UP, _yaw_trup)
	# na koni: hrac (player.global_position) je sedlo, panev sedu z Driving_Loop je ~SED nad korenem tela
	var y0 := player.global_position.y - (SED * _vyska if kon != null else 0.0)
	# Misa 0.99994 r. 73 (louc u oka obri, ruka mimo zaber) - ROZBOR 9. 11.: telo stalo koren 0,16 m za kamerou, takze
	# kost hlavy byla 0,18 m za okem a rameno 0,30 m (paze 0,47 m do zaberu nedosahla). Oko je v hlave ~0,09 m pred kosti
	# hlavy (sit hlavy hrac_cela: Head z -0,017, nos +0,115). Ted se telo stavi podle sve hlavy: kost hlavy (poza klipu,
	# vodorovne) oko_pred_hlavou_m za kamerou, pri pohledu dolu o hlava_dolu_vzad_m * sin vic (krk se predkloni, oko je
	# nad hrudnikem, ne v nem) - jako hlava cloveka, ne pevny posun korene.
	var xf := Transform3D(smer.rotated(Vector3.UP, PI).scaled(Vector3.ONE * _vyska), Vector3(c.x, y0, c.z))
	var ih0 := kostra.find_bone("Head") if kostra else -1
	if ih0 >= 0 and kon == null:
		var hl := kostra.global_transform * kostra.get_bone_global_pose(ih0).origin
		_hlava_lok = _hlava_lok.lerp(global_transform.affine_inverse() * hl, minf(1.0, delta * 12.0)) if _hlava_ok else global_transform.affine_inverse() * hl
		_hlava_ok = true
		var hw := xf * _hlava_lok
		var za := OKO_PRED + DOLU_VZAD * maxf(0.0, -sin(float(player.get("pitch"))))
		var chci := Vector3(c.x, 0.0, c.z) + smer * Vector3(0, 0, za)
		xf.origin += Vector3(chci.x - hw.x, 0.0, chci.z - hw.z)
	global_transform = xf
	# na koni panev do sedla (Misa 4. 11.: „pri pohledu pod sebe furt sedim na zadku“ - telo stalo za kamerou, panev sedu
	# z Driving_Loop je za hlavou, takze sedela na zadi kone): vodorovne posunout, aby kost panve byla nad sedlem
	if kon != null and kostra:
		var ip := kostra.find_bone("pelvis")
		if ip >= 0:
			var pw := (kostra.global_transform * kostra.get_bone_global_pose(ip)).origin
			var sd := player.global_position
			# i svisle: kycelni kloub (pelvis) o panev_nad_sedlem_m nad sedadlem - driv odhad SED pod korenem tela
			# (panev ve vzduchu nad sedlem, drep)
			global_position += Vector3(sd.x - pw.x, sd.y + PANEV_NAD - pw.y, sd.z - pw.z)
		# oci do hlavy tela (Misa 4. 11. „hrac by nemel koukat do vlastniho hrudniku“): kamera vodorovne nad kost hlavy
		# + oko pred kosti hlavy (OKO_PRED, pri pohledu dolu krk vpred DOLU_VZAD - stejne jako pesky, r. 73), vyska zustava
		# oci nad sedlem
		var ih2 := kostra.find_bone("Head")
		var sd2 := player.global_position
		if ih2 >= 0:
			var hw := (kostra.global_transform * kostra.get_bone_global_pose(ih2)).origin
			var vpred := -(kon as Node3D).global_transform.basis.z
			vpred.y = 0.0
			var cil_o := Vector3(hw.x - sd2.x, 0.0, hw.z - sd2.z) + vpred.normalized() * (OKO_PRED + DOLU_VZAD * maxf(0.0, -sin(float(player.get("pitch")))))
			player.set("oci_posun", (player.get("oci_posun") as Vector3).lerp(cil_o, minf(1.0, delta * 8.0)))
