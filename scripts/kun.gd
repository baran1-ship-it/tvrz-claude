extends CharacterBody3D
## Kun a jizda (Misa 27. 10. noc: „kun a jizda se vsim vsudy, drzet se cesty nebo ne, podle KCD2“).
## Model: horse.glb z Disku (kostra, 28 animaci, sedlo s trmeny) -> tools/kun_priprava.py -> modely/postavy/kun.glb.
## Jako v KCD2:
##  - nasednout / sesednout akci u kone (svitek akci), pri jizde hrac sedi v sedle, kamera ve vysce oci jezdce
##    (2,4 m - kompozice C), rozhlizeni volne;
##  - chody: krok (packa malo), klus (packa naplno), cval (rezim behu), trysk (rezim behu + packa naplno dele nez
##    3 s; stoji vydrz, pri nule kun zpomali do cvalu); zastaveni postupne (Run_Stop z cvalu);
##  - rizeni: kun se toci za pohledem jezdce (kamera) a packou do stran, rychlost otaceni podle chodu;
##  - „Drzet se cesty“ (nastaveni, vychozi zapnuto): na ceste a bez rizeni do strany kun sam jde po ose cesty, na
##    rozcesti vybere vetev, ktera miri nejvic tam, kam se jezdec diva; z cesty sjede rizenim nebo pohledem stranou;
##  - kun nevejde do hluboke vody (brod ano), na prudkem svahu zpomali, prekazky (stromy, zdi) ho zastavi;
##  - volny kun stoji, prešlapuje a pase se (Idle / Eat); kopyta zni podle povrchu.
## Vyska a orientace modelu se zmeri z kostry (hlava vs. panev), meritko na kohoutek 1,58 m (stredni tezky kun 1393).

const MODEL := "res://modely/postavy/kun.glb"
const KOHOUTEK := 1.58            # vyska v kohoutku (m)
const OCI_NAD_SEDLEM := 0.88      # oci jezdce nad sedlem
const CHODY := {"stani": 0.0, "krok": 1.7, "klus": 3.8, "cval": 6.5, "trysk": 10.5}
const OTACENI := {"stani": 1.4, "krok": 1.4, "klus": 1.1, "cval": 0.8, "trysk": 0.55}   # rad/s
const ZRYCHLENI := 2.2            # m/s2
const BRZDENI := 4.0
const VYDRZ_MAX := 12.0           # s trysku
const NADOSAH := 2.6              # m od sedla pro nasednuti
const HLOUBKA_MAX := 1.1          # m vody, do ktere kun vejde
const SVAH_MAX := 0.62            # sinus svahu (~38 st.), kde se kun zastavi

var main: Node
var jezdec: Node = null           # hrac v sedle
var drzet_cestu := true
var chod := "stani"
var vydrz := VYDRZ_MAX
var _rych := 0.0                  # m/s vpred
var _yaw := 0.0
var _otaceni := 0.0               # aktualni rychlost otaceni (pro prolinani Walk_L/R)
var _trysk_t := 0.0
var _model: Node3D
var _ap: AnimationPlayer
var _at: AnimationTree
var _kostra: Skeleton3D
var _sedlo := Vector3(0, 1.3, -0.1)      # bod sedla v mistnich souradnicich kone
var _krok := 0.0
var _past := 0.0
var _cesta_mriz := {}             # bunka 8 m -> [[index osy, index bodu]]

signal kopyto(povrch: String, hlasitost: float)


func setup(p_main: Node, poloha: Vector3, yaw: float) -> bool:
	main = p_main
	var ps: PackedScene = load(MODEL)
	if ps == null:
		return false
	_model = ps.instantiate() as Node3D
	add_child(_model)
	var sk := _model.find_children("*", "Skeleton3D", true, false)
	if sk.is_empty():
		return false
	_kostra = sk[0] as Skeleton3D
	var aps := _model.find_children("*", "AnimationPlayer", true, false)
	if aps.is_empty():
		return false
	_ap = aps[0] as AnimationPlayer
	# rozmery a smer modelu z klidove kostry: hlava pred panvi = smer vpred, nejnizsi kost = kopyta
	var hlava := Vector3.ZERO
	var panev := Vector3.ZERO
	var dno := INF
	var vrch := -INF
	for i in _kostra.get_bone_count():
		var n := _kostra.get_bone_name(i)
		var p := (_kostra.global_transform * _kostra.get_bone_global_rest(i)).origin - _model.global_transform.origin
		dno = minf(dno, p.y)
		if n.contains("Head_00"):
			hlava = p
		if n.contains("Pelvis"):
			panev = p
		if n.contains("Neck_00") or n.contains("Spine") or n.contains("Pelvis"):
			vrch = maxf(vrch, p.y)
	var vpred := Vector3(hlava.x - panev.x, 0, hlava.z - panev.z).normalized()
	var k := KOHOUTEK / maxf(vrch - dno, 0.1)
	_model.scale = Vector3.ONE * k
	# model natocit, aby hlava mirila na -Z (vpred v Godotu), kopyta na y = 0
	_model.rotation.y = atan2(vpred.x, vpred.z) + PI
	_model.position.y = -dno * k
	_sedlo = Vector3(0, KOHOUTEK - 0.12, 0.15)
	for mi in _model.find_children("*", "GeometryInstance3D", true, false):
		var g := mi as GeometryInstance3D
		g.visibility_range_end = 200.0
		g.extra_cull_margin = 1.0
	# kolize: trup kone (kvadr), hrac ma vlastni kapsli
	var col := CollisionShape3D.new()
	var bx := BoxShape3D.new()
	bx.size = Vector3(0.7, 1.0, 2.1)
	col.shape = bx
	col.position = Vector3(0, 1.15, 0)
	add_child(col)
	floor_max_angle = deg_to_rad(42.0)
	floor_snap_length = 0.6
	_strom()
	global_position = poloha
	_yaw = yaw
	rotation.y = _yaw
	print("kun: meritko %.4f, vpred %s, animaci %d" % [k, vpred, _ap.get_animation_list().size()])
	return true


func _klip(jm: String) -> String:
	for a in _ap.get_animation_list():
		if String(a).ends_with(jm) or String(a) == jm:
			return String(a)
	return ""


## AnimationTree: BlendSpace2D (x = otaceni -1..1, y = rychlost) z Idle / Walk(_L/_R) / Gallop(_L/_R); klus = cval
## zpomaleny (model nema klus), pastva a zastaveni z cvalu jednorazove.
func _strom() -> void:
	_at = AnimationTree.new()
	add_child(_at)
	_at.anim_player = _at.get_path_to(_ap)
	var bt := AnimationNodeBlendTree.new()
	var bs := AnimationNodeBlendSpace2D.new()
	bs.min_space = Vector2(-1, 0)
	bs.max_space = Vector2(1, CHODY["trysk"])
	for b: Array in [["1 Idle", 0.0, 0.0], ["Walk", 0.0, CHODY["krok"]], ["Walk_L", -1.0, CHODY["krok"]], ["Walk_R", 1.0, CHODY["krok"]],
			["Gallop", 0.0, CHODY["trysk"]], ["Gallop_L", -1.0, CHODY["trysk"]], ["Gallop_R", 1.0, CHODY["trysk"]]]:
		var jm := _klip(b[0])
		if jm == "":
			continue
		var n := AnimationNodeAnimation.new()
		n.animation = jm
		bs.add_blend_point(n, Vector2(b[1], b[2]))
	bt.add_node("chod", bs)
	bt.add_node("tempo", AnimationNodeTimeScale.new())
	var os := AnimationNodeOneShot.new()
	os.fadein_time = 0.3
	os.fadeout_time = 0.4
	bt.add_node("jednou", os)
	var jk := AnimationNodeAnimation.new()
	jk.animation = _klip("6 Eat")
	bt.add_node("jednou_klip", jk)
	bt.connect_node("tempo", 0, "chod")
	bt.connect_node("jednou", 0, "tempo")
	bt.connect_node("jednou", 1, "jednou_klip")
	bt.connect_node("output", 0, "jednou")
	_at.tree_root = bt
	for a in _ap.get_animation_list():
		var an := _ap.get_animation(a)
		if String(a).contains("Idle") or String(a).contains("Walk") or String(a).contains("Gallop") or String(a).contains("Swim"):
			an.loop_mode = Animation.LOOP_LINEAR
	_at.active = true


func _jednou(jm: String) -> void:
	var k := _klip(jm)
	if k == "":
		return
	((_at.tree_root as AnimationNodeBlendTree).get_node("jednou_klip") as AnimationNodeAnimation).animation = k
	_at.set("parameters/jednou/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)


# ------------------------------------------------------------------ jezdec

func sedlo_global() -> Vector3:
	return global_transform * _sedlo


func na_dosah(p: Vector3) -> bool:
	return jezdec == null and p.distance_to(sedlo_global() - Vector3(0, 1.0, 0)) < NADOSAH


func nasedni(hrac: Node) -> void:
	if jezdec != null:
		return
	jezdec = hrac
	hrac.set("na_koni", self)
	chod = "stani"
	_rych = 0.0
	drzet_cestu = bool(main.get("kun_drzet_cestu")) if main.get("kun_drzet_cestu") != null else true
	main.hud.toast("Na koni – packa vpřed krok, naplno klus, běh = cval" + (" · drží se cesty" if drzet_cestu else ""), 2.5)


func sesedni() -> void:
	if jezdec == null:
		return
	var hrac := jezdec
	jezdec = null
	hrac.set("na_koni", null)
	# vlevo od kone (jezdci sesedaji vlevo), na zem
	var vlevo := global_transform.basis * Vector3(-1.0, 0, 0)
	var cil := global_position + vlevo * 1.1 + Vector3(0, 0.2, 0)
	(hrac as Node3D).global_position = cil
	hrac.set("velocity", Vector3.ZERO)
	_rych = 0.0
	chod = "stani"


# ------------------------------------------------------------------ cesty

func _mriz_cest() -> void:
	var sv: Object = main.get("svet")
	if sv == null:
		return
	var osy: Array = sv.get("cesty_osy")
	for oi in osy.size():
		var pp: PackedVector2Array = osy[oi]["p"]
		for i in pp.size():
			var c := Vector2i(floori(pp[i].x / 8.0), floori(pp[i].y / 8.0))
			if not _cesta_mriz.has(c):
				_cesta_mriz[c] = []
			(_cesta_mriz[c] as Array).append([oi, i])


## Smer, kudy vede cesta pred konem (yaw), nebo INF mimo cestu. Z vetvi na dosah ta, ktera miri nejbliz smeru pohledu.
func _smer_cesty(poloha: Vector2, smer: float, pohled: float) -> float:
	var sv: Object = main.get("svet")
	if _cesta_mriz.is_empty():
		_mriz_cest()                                   # osy cest vznikaji az ve stavbe sveta
	var osy: Array = sv.get("cesty_osy")
	var c0 := Vector2i(floori(poloha.x / 8.0), floori(poloha.y / 8.0))
	var nejlepsi := INF
	var skore := -INF
	var vpred := Vector2(-sin(smer), -cos(smer))
	var dohled := 6.0 + _rych * 1.2
	for dx in range(-1, 2):
		for dz in range(-1, 2):
			for e: Array in _cesta_mriz.get(c0 + Vector2i(dx, dz), []):
				var pp: PackedVector2Array = osy[e[0]]["p"]
				var ws: PackedFloat32Array = osy[e[0]]["w"]
				var i: int = e[1]
				if poloha.distance_to(pp[i]) > ws[i] + 2.5:
					continue
				# oba smery po ose: bod o 'dohled' dal
				for sg: int in [-1, 1]:
					var j := i
					var ujeto := 0.0
					while j + sg >= 0 and j + sg < pp.size() and ujeto < dohled:
						ujeto += pp[j].distance_to(pp[j + sg])
						j += sg
					if j == i:
						continue
					var d := (pp[j] - poloha).normalized()
					if d.dot(vpred) < 0.2:
						continue                          # vetev za konem
					var yaw_d := atan2(-d.x, -d.y)
					var s := d.dot(vpred) * 0.4 + cos(wrapf(yaw_d - pohled, -PI, PI)) * 0.6
					if s > skore:
						skore = s
						nejlepsi = yaw_d
	return nejlepsi


# ------------------------------------------------------------------ pohyb

func _physics_process(delta: float) -> void:
	var cil_rych := 0.0
	var cil_yaw := _yaw
	if jezdec != null:
		var inp: Vector2 = jezdec.get("move_input")
		var beh: bool = jezdec.get("beh")
		var pohled: float = jezdec.get("yaw")
		var ml := clampf(inp.y, -1.0, 1.0)
		if ml > 0.1:
			if beh:
				chod = "trysk" if (ml > 0.95 and vydrz > 0.0 and _trysk_t > 3.0) else "cval"
				_trysk_t = _trysk_t + delta if ml > 0.95 else 0.0
			else:
				chod = "klus" if ml > 0.8 else "krok"
				_trysk_t = 0.0
		elif ml < -0.3:
			chod = "krok"
		else:
			chod = "stani"
		cil_rych = CHODY[chod] * (-0.6 if ml < -0.3 else 1.0)
		# rizeni: pohled jezdce (kamera) + packa do stran; na ceste bez rizeni po ose
		var rizeni := inp.x
		cil_yaw = pohled if absf(wrapf(pohled - _yaw, -PI, PI)) < deg_to_rad(100.0) else _yaw
		if absf(rizeni) > 0.25:
			cil_yaw = _yaw - rizeni * 0.6
		elif drzet_cestu and _rych > 0.5:
			var sc := _smer_cesty(Vector2(global_position.x, global_position.z), _yaw, pohled)
			if sc != INF and absf(wrapf(pohled - sc, -PI, PI)) < deg_to_rad(55.0):
				cil_yaw = sc
		if chod == "trysk":
			vydrz = maxf(0.0, vydrz - delta)
		else:
			vydrz = minf(VYDRZ_MAX, vydrz + delta * 0.6)
	# voda a svah pred konem
	var vpred3 := -global_transform.basis.z
	var pred := global_position + vpred3 * 1.6
	var sv: Object = main.get("svet")
	if sv != null and cil_rych > 0.0:
		# hluboke koryto nebo sraz pred konem (teren o vic nez HLOUBKA_MAX niz): kun nevejde; brod je melky - projde
		var y0 := float(sv.call("_vyska", global_position.x, global_position.z))
		var y1 := float(sv.call("_vyska", pred.x, pred.z))
		if y0 - y1 > HLOUBKA_MAX:
			cil_rych = 0.0
	if is_on_floor() and get_floor_normal().y < cos(asin(SVAH_MAX)) and cil_rych > CHODY["krok"]:
		cil_rych = CHODY["krok"]
	var zpomal := cil_rych < _rych
	_rych = move_toward(_rych, cil_rych, (BRZDENI if zpomal else ZRYCHLENI) * delta)
	if zpomal and _rych > 5.0 and cil_rych < 1.0:
		_jednou("Run_Stop")
	# otaceni (rychlost podle chodu)
	var dy := wrapf(cil_yaw - _yaw, -PI, PI)
	var max_ot: float = OTACENI.get(chod, 1.0)
	var ot := clampf(dy * 2.5, -max_ot, max_ot) if absf(_rych) > 0.2 or jezdec != null else 0.0
	_yaw += ot * delta
	_otaceni = lerpf(_otaceni, clampf(ot / maxf(max_ot, 0.01), -1.0, 1.0), minf(1.0, delta * 5.0))
	rotation.y = _yaw
	var v := -Basis(Vector3.UP, _yaw).z * _rych
	velocity.x = v.x
	velocity.z = v.z
	velocity.y = 0.0 if is_on_floor() else velocity.y - 12.0 * delta
	move_and_slide()
	if is_on_wall() and _rych > 0.5:
		_rych *= 0.5                                   # narazil (strom, zed)
	# animace
	_at.set("parameters/chod/blend_position", Vector2(_otaceni, absf(_rych)))
	var tempo := 1.0
	if absf(_rych) > CHODY["krok"] + 0.5 and absf(_rych) < CHODY["cval"]:
		tempo = 0.75                                    # klus = zpomaleny cval (model nema klus)
	_at.set("parameters/tempo/scale", -tempo if _rych < -0.1 else tempo)
	# kopyta: kadence podle chodu
	if absf(_rych) > 0.3:
		_krok += absf(_rych) * delta
		var delka := 1.6 if absf(_rych) < 3.0 else 2.6
		if _krok > delka:
			_krok = 0.0
			kopyto.emit("cesta", clampf(absf(_rych) / 6.0, 0.4, 1.4))
	# volny kun se obcas pase
	if jezdec == null and absf(_rych) < 0.1:
		_past -= delta
		if _past < 0.0:
			_past = randf_range(8.0, 20.0)
			_jednou("6 Eat")
	# jezdec v sedle (poloha a vyska oci; pohupovani podle chodu)
	if jezdec != null:
		var houp := sin(_krok / (1.6 if absf(_rych) < 3.0 else 2.6) * TAU) * (0.015 if absf(_rych) < 3.0 else 0.035)
		(jezdec as Node3D).global_position = sedlo_global() + Vector3(0, houp - OCI_NAD_SEDLEM * 0.0, 0)
		jezdec.set("velocity", velocity)
