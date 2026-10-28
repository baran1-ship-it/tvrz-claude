extends Node3D
## Telo hrace v prvni osobe (radce 27. 10. 21:20 bod 6, Misa: „ruce s plnou animaci, jak v KCD2, ale at se to neseka“).
## Jako v KCD: hrac je cela postava (Quaternius Universal Base Characters + selsky odev, CC0), kamera v hlave; ruce jsou
## ruce tela, ne samostatny model. Animace z Quaternius Universal Animation Library 1 + 2 (CC0, stejna kostra 65 kosti,
## bez retargetu, bez root motion; modely/postavy/anim/UAL*.glb jen kostra + klipy).
## Plynulost (Misa): kamera NENI prilepena na kost hlavy (kyvani hlavy pri chuzi = trhani obrazu a nevolnost) - kamera
## zustava hladka (player.gd), telo se pod ni posouva: hlava modelu tesne za kamerou, trup se otaci s pohledem do stran
## s mirnym zpozdenim, pri pohledu dolu je videt trup a nohy, pri akcich ruce. Hlava se nekresli (odev bez hlavy).
## Tablet (pravidla_modelu.json trida postava): jedna kostra, telo bez stinu (ruce zblizka), AnimationTree jen kdyz
## hrac neni v letu; mimo kameru (pohled nahoru) se kostra dal pocita (drobnost: 65 kosti).

const DIR := "res://modely/postavy/"
const ANIM := ["res://modely/postavy/anim/UAL1.glb", "res://modely/postavy/anim/UAL2.glb"]
const Pravidla := preload("res://scripts/pravidla.gd")
# cisla z pravidla/svet/jizda.json (telo)
static var ZA_KAMEROU := float(Pravidla.cti("jizda", "telo", "za_kamerou_m"))      # hlava tela za kamerou
static var OTOCENI_TRUPU := float(Pravidla.cti("jizda", "telo", "otoceni_trupu"))  # jak rychle trup dobiha pohled
static var VE_STANI := deg_to_rad(float(Pravidla.cti("jizda", "telo", "otoceni_ve_stani_st")))
static var BOK_MAX := deg_to_rad(float(Pravidla.cti("jizda", "telo", "bok_max_st")))
static var VZAD_OD := deg_to_rad(float(Pravidla.cti("jizda", "telo", "vzad_od_st")))
static var SED := float(Pravidla.cti("jizda", "telo", "sed_m"))                    # panev v sedu nad korenem tela
static var ROZKROK := deg_to_rad(float(Pravidla.cti("jizda", "telo", "rozkrok_st")))
static var LYTKA := deg_to_rad(float(Pravidla.cti("jizda", "telo", "lytka_st")))
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
var _cesta := ""                  # cesta ke kostre od korene animaci (stopy klipu i filtr ruky)


func setup(p_player: CharacterBody3D, muz := true) -> bool:
	player = p_player
	var odev: PackedScene = load(DIR + ("Male_Peasant.gltf" if muz else "Female_Peasant.gltf"))
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
	var lib := AnimationLibrary.new()
	_cesta = String(get_path_to(kostra))
	var cesta := _cesta
	for f: String in ANIM:
		var ps: PackedScene = load(f)
		if ps == null:
			continue
		var s := ps.instantiate()
		for a in s.find_children("*", "AnimationPlayer", true, false):
			var p := a as AnimationPlayer
			for ln in p.get_animation_library_list():
				var l := p.get_animation_library(ln)
				for an in l.get_animation_list():
					var anim := (l.get_animation(an) as Animation).duplicate(true) as Animation
					for ti in anim.get_track_count():
						var tp := anim.track_get_path(ti)
						if tp.get_subname_count() > 0:
							anim.track_set_path(ti, NodePath(cesta + ":" + tp.get_concatenated_subnames()))
					var jm := String(an).trim_suffix("_Armature")
					# importer Godotu klipum *_Loop priponu odrizne a nastavi smycku (Idle_Loop -> Idle); jmena v kodu
					# jsou podle knihovny UAL - bez tohoto se klip nenasel a telo stalo v T-poze (snimek 27. 10.)
					if anim.loop_mode != Animation.LOOP_NONE and not jm.ends_with("_Loop"):
						jm += "_Loop"
					if jm.ends_with("_Loop"):
						anim.loop_mode = Animation.LOOP_LINEAR
					lib.add_animation(jm, anim)
		s.free()
	ap.add_animation_library("", lib)
	# kazdy klip, ktery strom pouziva, musi v knihovne byt (jinak tise T-poza)
	var chybi: Array = []
	for jm: String in ["Idle_Loop", "Walk_Loop", "Jog_Fwd_Loop", "Sprint_Loop", "Jump_Loop", "Interact", "Driving_Loop"] + AKCE.values() + DRZENI.values().map(func(v: Array) -> String: return v[0]):
		if not lib.has_animation(jm):
			chybi.append(jm)
	if not chybi.is_empty():
		push_error("telo hrace: v knihovne chybi klipy %s" % str(chybi))
	ruka_r = BoneAttachment3D.new()
	ruka_r.bone_name = "hand_r"
	kostra.add_child(ruka_r)
	ruka_l = BoneAttachment3D.new()
	ruka_l.bone_name = "hand_l"
	kostra.add_child(ruka_l)
	_yaw_trup = player.yaw
	print("telo hrace: %d klipu, meritko %.3f, hrac %s strom %s, snimek %d" % [lib.get_animation_list().size(), _vyska, player != null, at != null, Engine.get_process_frames()])
	return true


## AnimationTree: pohyb (stani - chuze - klus - beh podle rychlosti), poza ruky pri drzeni predmetu (jen kosti ruky),
## jednorazova akce pres vse (pouzit, sebrat, otevrit, jist).
func _strom() -> void:
	at = AnimationTree.new()
	at.name = "Strom"
	add_child(at)
	at.anim_player = at.get_path_to(ap)
	var bt := AnimationNodeBlendTree.new()
	var bs := AnimationNodeBlendSpace1D.new()
	for b: Array in [["Idle_Loop", 0.0], ["Walk_Loop", player.WALK], ["Jog_Fwd_Loop", player.RUN], ["Sprint_Loop", player.RUN * 1.4]]:
		var n := AnimationNodeAnimation.new()
		n.animation = b[0]
		bs.add_blend_point(n, b[1])
	bs.min_space = 0.0
	bs.max_space = player.RUN * 1.4
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


## Predmet v ruce ("" = nic): poza ruky z klipu drzeni.
func drz(id: String) -> void:
	_drzi = id
	if at == null:
		return
	if DRZENI.has(id):
		((at.tree_root as AnimationNodeBlendTree).get_node("drzeni") as AnimationNodeAnimation).animation = DRZENI[id][0]


## Po animaci: na koni stehna do rozkroku a lytka dolu k trmenum (Driving_Loop je sed na zidli).
func _po_mixu() -> void:
	if player == null or player.get("na_koni") == null or kostra == null:
		return
	for b: Array in [["thigh_l", 1.0], ["thigh_r", -1.0]]:
		var i := kostra.find_bone(b[0])
		if i >= 0:
			kostra.set_bone_pose_rotation(i, kostra.get_bone_pose_rotation(i) * Quaternion(Vector3(0, 0, 1), ROZKROK * float(b[1])))
	for b2: String in ["calf_l", "calf_r"]:
		var j := kostra.find_bone(b2)
		if j >= 0:
			kostra.set_bone_pose_rotation(j, kostra.get_bone_pose_rotation(j) * Quaternion(Vector3(1, 0, 0), LYTKA))


var snimku := 0                         # pocet behu _process (zkouska jizdy: bezi telo?)
var naposled := ""


func _process(delta: float) -> void:
	snimku += 1
	if player == null or at == null:
		naposled = "bez hrace %s / stromu %s (snimek %d)" % [player == null, at == null, Engine.get_process_frames()]
		return
	var kon: Node = player.get("na_koni")
	at.set("parameters/jizda/blend_amount", 1.0 if kon != null else 0.0)
	visible = not bool(player.get("flying")) and not bool(player.get("seated")) and not bool(player.get("climbing"))
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
	# tempo: na bodech prolnuti 1, mezi nimi podle rychlosti (chuze 2,3 m/s, klus 4,8 m/s)
	var ref := float(player.get("WALK")) if hv < float(player.get("WALK")) * 1.5 else float(player.get("RUN"))
	var tempo := clampf(hv / ref, 0.6, 1.4) if hv > 0.3 else 1.0
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
	global_transform = Transform3D(smer.rotated(Vector3.UP, PI).scaled(Vector3.ONE * _vyska),
			Vector3(c.x, y0, c.z) + smer * Vector3(0, 0, ZA_KAMEROU))
