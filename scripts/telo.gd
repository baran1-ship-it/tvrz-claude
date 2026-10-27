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
const ZA_KAMEROU := 0.16          # hlava tela za kamerou (m) - aby kamera nevidela dovnitr krku a ramen
const OTOCENI_TRUPU := 7.0        # jak rychle trup dobiha smer pohledu (1/s)
const AKCE := {"pouzit": "Interact", "sebrat": "PickUp_Table", "otevrit": "Chest_Open", "jist": "Consume",
		"skok": "Jump_Start", "dopad": "Jump_Land", "lezt": "ClimbUp_1m"}
# drzeni predmetu: klip, ze ktereho se bere poza ruky (ostatni kosti z pohybu)
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
					if jm.ends_with("_Loop") or jm in ["Idle_Torch_Loop", "Idle_Lantern_Loop"]:
						anim.loop_mode = Animation.LOOP_LINEAR
					lib.add_animation(jm, anim)
		s.free()
	ap.add_animation_library("", lib)
	_strom()
	ruka_r = BoneAttachment3D.new()
	ruka_r.bone_name = "hand_r"
	kostra.add_child(ruka_r)
	ruka_l = BoneAttachment3D.new()
	ruka_l.bone_name = "hand_l"
	kostra.add_child(ruka_l)
	_yaw_trup = player.yaw
	print("telo hrace: %d klipu, meritko %.3f" % [lib.get_animation_list().size(), _vyska])
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
	bt.add_node("akce", os)
	var ak := AnimationNodeAnimation.new()
	ak.animation = "Interact"
	bt.add_node("akce_klip", ak)
	bt.connect_node("ruka", 0, "pohyb")
	bt.connect_node("ruka", 1, "drzeni")
	bt.connect_node("akce", 0, "ruka")
	bt.connect_node("akce", 1, "akce_klip")
	bt.connect_node("output", 0, "akce")
	at.tree_root = bt
	at.active = true
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


func _process(delta: float) -> void:
	if player == null or at == null:
		return
	visible = not bool(player.get("flying")) and not bool(player.get("seated")) and not bool(player.get("climbing"))
	at.active = visible
	if not visible:
		return
	var hv := Vector2(player.velocity.x, player.velocity.z).length()
	at.set("parameters/pohyb/blend_position", hv)
	at.set("parameters/ruka/blend_amount", 1.0 if _drzi != "" else 0.0)
	# trup dobiha smer pohledu (pri chuzi hned, ve stani az kdyz se hrac otoci o vic nez 50 st. - jako clovek)
	var d := wrapf(float(player.get("yaw")) - _yaw_trup, -PI, PI)
	if hv > 0.3 or absf(d) > deg_to_rad(50.0):
		_yaw_trup += d * minf(1.0, delta * OTOCENI_TRUPU)
	# poloha: hlava tesne za kamerou (kamera je v player.gd hladka, bez kyvani kosti hlavy)
	var c: Vector3 = (player.get("cam") as Camera3D).global_position
	var smer := Basis(Vector3.UP, _yaw_trup)
	global_transform = Transform3D(smer.rotated(Vector3.UP, PI).scaled(Vector3.ONE * _vyska),
			Vector3(c.x, player.global_position.y, c.z) + smer * Vector3(0, 0, ZA_KAMEROU))
