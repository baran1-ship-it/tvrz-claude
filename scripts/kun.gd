extends CharacterBody3D
## Kun a jizda (Misa 27. 10. noc: „kun a jizda se vsim vsudy, drzet se cesty nebo ne, podle KCD2“).
## Model: horse.glb z Disku (kostra, 28 animaci, sedlo s trmeny) -> tools/kun_priprava.py -> modely/postavy/kun.glb.
## Jako v KCD2:
##  - nasednout / sesednout akci u kone (svitek akci), pri jizde hrac sedi v sedle, kamera ve vysce oci jezdce
##    (2,4 m - kompozice C), rozhlizeni volne;
##  - chody (Misa 28. 10.): packa = krok, packa naplno = cval, beh (jako u hrace) = trysk; vydrz kone ubyva jen
##    v trysku, pri nule kun zpomali do cvalu a trysk jde znovu od tretiny vydrze (ukazatel kone dole, hud.gd);
##  - rizeni: kun se toci za pohledem jezdce (kamera) a packou do stran, rychlost otaceni podle chodu;
##  - „Drzet se cesty“ (nastaveni, vychozi zapnuto): na ceste a bez rizeni do strany kun sam jde po ose cesty, na
##    rozcesti vybere vetev, ktera miri nejvic tam, kam se jezdec diva; z cesty sjede rizenim nebo pohledem stranou;
##  - kun nevejde do hluboke vody (brod ano), na prudkem svahu zpomali, prekazky (stromy, zdi) ho zastavi;
##  - volny kun stoji, prešlapuje a pase se (Idle / Eat); kopyta zni podle povrchu.
## Vyska a orientace modelu se zmeri z kostry (hlava vs. panev), meritko na kohoutek 1,58 m (stredni tezky kun 1393).

const Pravidla := preload("res://scripts/pravidla.gd")
# vsechna cisla z pravidla/svet/jizda.json (kun) - ladi se v datech, ne v kodu
static var MODEL := String(Pravidla.cti("jizda", "kun", "model"))
static var KOHOUTEK := float(Pravidla.cti("jizda", "kun", "kohoutek_m"))
static var MODEL_VYSKA := float(Pravidla.cti("jizda", "kun", "model_vyska"))
static var OCI_NAD_SEDLEM := float(Pravidla.cti("jizda", "kun", "oci_nad_sedlem_m"))
static var CHODY: Dictionary = Pravidla.cti("jizda", "kun", "chody")
static var OTACENI: Dictionary = Pravidla.cti("jizda", "kun", "otaceni")
static var ZRYCHLENI := float(Pravidla.cti("jizda", "kun", "zrychleni"))
static var BRZDENI := float(Pravidla.cti("jizda", "kun", "brzdeni"))
static var VYDRZ_MAX := float(Pravidla.cti("jizda", "kun", "vydrz_s"))
static var VYDRZ_OBNOVA := float(Pravidla.cti("jizda", "kun", "vydrz_obnova"))
static var ZIVOTY_MAX := float(Pravidla.cti("jizda", "kun", "zivoty_max"))
static var NADOSAH := float(Pravidla.cti("jizda", "kun", "nadosah_m"))
static var HLOUBKA_MAX := float(Pravidla.cti("jizda", "kun", "hloubka_max_m"))
static var SVAH_MAX := float(Pravidla.cti("jizda", "kun", "svah_max_sin"))
static var CESTA_DOHLED := float(Pravidla.cti("jizda", "kun", "cesta_dohled_m"))
static var CESTA_DOHLED_V := float(Pravidla.cti("jizda", "kun", "cesta_dohled_za_rychlost"))
static var CESTA_ODBOCKA := deg_to_rad(float(Pravidla.cti("jizda", "kun", "cesta_odbocka_st")))
static var PASTVA: Array = Pravidla.cti("jizda", "kun", "pastva_s")
static var DOSAH := float(Pravidla.cti("jizda", "kun", "dosah_m"))
static var KOLIZE: Array = Pravidla.cti("jizda", "kun", "kolize_m")
static var KOLIZE_Y := float(Pravidla.cti("jizda", "kun", "kolize_vyska_m"))
static var SEDLO_POD := float(Pravidla.cti("jizda", "kun", "sedlo_pod_kohoutkem_m"))
static var SEDLO_VZAD := float(Pravidla.cti("jizda", "kun", "sedlo_vzad_m"))
static var SESEDNOUT := float(Pravidla.cti("jizda", "kun", "sesednout_vlevo_m"))
static var COUVANI := float(Pravidla.cti("jizda", "kun", "couvani"))
static var KROK: Array = Pravidla.cti("jizda", "kun", "krok_delka_m")
static var HOUPANI: Array = Pravidla.cti("jizda", "kun", "houpani_m")
static var PODLAHA := deg_to_rad(float(Pravidla.cti("jizda", "kun", "podlaha_max_st")))
static var PROLINANI: Array = Pravidla.cti("jizda", "kun", "prolinani_s")
static var VYSTROJ: Dictionary = Pravidla.cti("jizda", "kun").get("vystroj", {})
static var NECINNOST: Array = Pravidla.cti("jizda", "kun").get("necinnost", ["Eat"])
static var KLIPY_Z_USEKU: Dictionary = Pravidla.cti("jizda", "kun").get("klipy_z_useku", {})
# nazvy klipu modelu horse.glb -> obecne nazvy klipu_z_useku (kun_hnedak ma jednu dlouhou animaci)
const ALIAS := {"1 Ilde": "Idle", "6 Eat": "Eat"}

var main: Node
var jezdec: Node = null           # hrac v sedle
var drzet_cestu := true
var chod := "stani"
var vydrz := VYDRZ_MAX
var _rych := 0.0                  # m/s vpred
var _yaw := 0.0
var _otaceni := 0.0               # aktualni rychlost otaceni (pro prolinani Walk_L/R)
var zivoty := ZIVOTY_MAX
var zivoty_max := ZIVOTY_MAX           # pro ukazatel (hud.gd)
var vydrz_max := VYDRZ_MAX
var _vycerpan := false          # vydrz dosla: trysk az od tretiny
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
	# model s jednou dlouhou animaci (kun_hnedak): chody jako useky [od, do] s z jizda.json klipy_z_useku
	if not KLIPY_Z_USEKU.is_empty() and _ap.get_animation_list().size() > 0:
		var zdroj := _ap.get_animation(_ap.get_animation_list()[0])
		var lib := AnimationLibrary.new()
		for jm: String in KLIPY_Z_USEKU:
			var us: Array = KLIPY_Z_USEKU[jm]
			var a := (preload("res://scripts/svet.gd") as GDScript).call("klip_z_useku", zdroj, float(us[0]), float(us[1])) as Animation
			if jm in NECINNOST:
				a.loop_mode = Animation.LOOP_NONE
			lib.add_animation(jm, a)
		_ap.add_animation_library("chody", lib)
	# rozmery a smer modelu z klidove kostry: hlava pred panvi = smer vpred, nejnizsi kost = kopyta
	var hlava := Vector3.ZERO
	var panev := Vector3.ZERO
	var dno := INF
	var vrch := -INF
	# kostra vuci modelu (retez transformaci uzlu; kun jeste neni ve strome, global_transform by nemel meritko
	# armatury 0,01 - meritko vyslo 100x mensi a kun nebyl videt, snimek kun 27. 10.)
	var xk := Transform3D()
	var uz: Node = _kostra
	while uz and uz != _model:
		if uz is Node3D:
			xk = (uz as Node3D).transform * xk
		uz = uz.get_parent()
	for i in _kostra.get_bone_count():
		var n := _kostra.get_bone_name(i)
		var p := (xk * _kostra.get_bone_global_rest(i)).origin
		dno = minf(dno, p.y)
		if n.contains("Head_0"):
			hlava = p
		if n.contains("Pelvis") or n.begins_with("Hips"):
			panev = p
		if n.contains("Neck_00") or n.contains("Spine") or n.contains("Pelvis") or n.begins_with("Hips"):
			vrch = maxf(vrch, p.y)
	var vpred := Vector3(hlava.x - panev.x, 0, hlava.z - panev.z).normalized()
	# meritko z vysky vykreslene site (jizda.json model_vyska, zmereno v Blenderu): kosti maji v modelu z FBX jine
	# meritko nez sit (kun ~30x mensi, nez ukazovala kostra - snimky 27. 10.); kohoutek = podil vysky z kostry
	var vrch_k := -INF
	for i in _kostra.get_bone_count():
		vrch_k = maxf(vrch_k, (xk * _kostra.get_bone_global_rest(i)).origin.y)
	var podil := clampf((vrch - dno) / maxf(vrch_k - dno, 1e-6), 0.3, 1.0)
	var k := KOHOUTEK / maxf(MODEL_VYSKA * podil, 1e-6)
	dno = 0.0                                          # kopyta site v klidu na nule modelu (Blender: -0,04)
	_model.scale = Vector3.ONE * k
	# model natocit, aby hlava mirila na -Z (vpred v Godotu), kopyta na y = 0
	_model.rotation.y = atan2(vpred.x, vpred.z) + PI
	_model.position.y = -dno * k
	_sedlo = Vector3(0, KOHOUTEK - SEDLO_POD, SEDLO_VZAD)
	for mi in _model.find_children("*", "GeometryInstance3D", true, false):
		var g := mi as GeometryInstance3D
		g.visibility_range_end = DOSAH
		# site se skinem maji klidovy obal jinde nez vykresleny kun (retez meritek 0,01 x 100 x 0,1 x 10 z FBX) -
		# orezani podle nej kone schovalo (snimek kun 27. 10.); obal pres celeho kone v lokalnich jednotkach site
		var xg := Transform3D()
		var uz2: Node = g
		while uz2 and uz2 != _model:
			if uz2 is Node3D:
				xg = (uz2 as Node3D).transform * xg
			uz2 = uz2.get_parent()
		var r_l := 4.0 / maxf(k * xg.basis.get_scale().x, 1e-9)
		g.custom_aabb = AABB(Vector3(-r_l, -r_l, -r_l), Vector3(2.0 * r_l, 2.0 * r_l, 2.0 * r_l))
	# kolize: trup kone (kvadr), hrac ma vlastni kapsli
	var col := CollisionShape3D.new()
	var bx := BoxShape3D.new()
	bx.size = Vector3(float(KOLIZE[0]), float(KOLIZE[1]), float(KOLIZE[2]))
	col.shape = bx
	col.position = Vector3(0, KOLIZE_Y, 0)
	add_child(col)
	floor_max_angle = PODLAHA
	floor_snap_length = 0.6
	_vystroj()
	_strom()
	global_position = poloha
	_yaw = yaw
	rotation.y = _yaw
	print("kun: meritko %.4f, vpred %s, animaci %d" % [k, vpred, _ap.get_animation_list().size()])
	return true


## Transformace uzlu vuci _model (kun jeste neni ve strome - global_transform nema retez meritek).
func _vuci_modelu(n: Node) -> Transform3D:
	var t := Transform3D()
	var u: Node = n
	while u and u != _model:
		if u is Node3D:
			t = (u as Node3D).transform * t
		u = u.get_parent()
	return t


## Sedlo s cabrakou a uzdecka (jizda.json kun.vystroj): kus v klidove poze na kotve v siti tela (cm), pak pod
## BoneAttachment3D kosti - hybe se s hrbetem a hlavou podle animace.
var _vystroj_cekat: Array = []          # [kus, cil vuci _model] - poloha se nastavi v prvnim snimku ve strome


func _vystroj_usadit() -> void:
	for e: Array in _vystroj_cekat:
		(e[0] as Node3D).global_transform = _model.global_transform * (e[1] as Transform3D)
		print("kun vystroj: %s kun %s model %s" % [(e[0] as Node3D).global_position, global_position, _model.global_transform.basis.get_scale()])
	_vystroj_cekat.clear()


func _vystroj() -> void:
	if VYSTROJ.is_empty():
		return
	var telo: MeshInstance3D = null
	for mi in _model.find_children("*", "MeshInstance3D", true, false):
		if telo == null or (mi as MeshInstance3D).mesh.get_faces().size() > telo.mesh.get_faces().size():
			telo = mi as MeshInstance3D
	var t_telo := _vuci_modelu(telo)
	var t_kostra := _vuci_modelu(_kostra)
	var mer := float(VYSTROJ["meritko"]) * 100.0                 # kus v m, sit tela v cm
	for jm: String in VYSTROJ["kusy"]:
		var d: Dictionary = VYSTROJ["kusy"][jm]
		var cesta := String(d["model"]) % String(VYSTROJ["varianta"])
		var ib := _kostra.find_bone(String(d["kost"]))
		if not ResourceLoader.exists(cesta) or ib < 0:
			push_warning("kun: vystroj %s (%s, kost %s) chybi" % [jm, cesta, d["kost"]])
			continue
		var kus := (load(cesta) as PackedScene).instantiate() as Node3D
		var k: Array = d["kotva_cm"]
		var chce := t_telo * Transform3D(Basis.from_scale(Vector3.ONE * mer), Vector3(float(k[0]), float(k[1]), float(k[2])))
		var att := BoneAttachment3D.new()
		att.bone_name = String(d["kost"])
		_kostra.add_child(att)
		# poloha az ve strome (prvni snimek fyziky): kus.global = model.global * cil - nezavisle na tom, v jake soustave
		# BoneAttachment3D drzi kost (dva vypocty 28. 10. sedlo nechaly viset nad konem)
		att.add_child(kus)
		_vystroj_cekat.append([kus, chce])
		for g in kus.find_children("*", "GeometryInstance3D", true, false):
			(g as GeometryInstance3D).visibility_range_end = DOSAH


func _klip(jm: String) -> String:
	for nm: String in [jm, String(ALIAS.get(jm, jm))]:
		for a in _ap.get_animation_list():
			if String(a).ends_with("/" + nm) or String(a).ends_with(nm) or String(a) == nm:
				return String(a)
	return ""


## AnimationTree: BlendSpace2D (x = otaceni -1..1, y = rychlost) z Idle / Walk(_L/_R) / Gallop(_L/_R) (cval a trysk
## podle rychlosti), pastva a zastaveni z cvalu jednorazove.
func _strom() -> void:
	_at = AnimationTree.new()
	add_child(_at)
	_at.anim_player = _at.get_path_to(_ap)
	var bt := AnimationNodeBlendTree.new()
	var bs := AnimationNodeBlendSpace2D.new()
	bs.min_space = Vector2(-1, 0)
	bs.max_space = Vector2(1, CHODY["trysk"])
	# "1 Ilde": preklep v modelu horse.glb (Disk) - klip stani se jinak nenasel
	for b: Array in [["1 Ilde", 0.0, 0.0], ["Walk", 0.0, CHODY["krok"]], ["Walk_L", -1.0, CHODY["krok"]], ["Walk_R", 1.0, CHODY["krok"]],
			["Gallop", 0.0, CHODY["trysk"]], ["Gallop_L", -1.0, CHODY["trysk"]], ["Gallop_R", 1.0, CHODY["trysk"]]]:
		var jm := _klip(b[0])
		if jm == "":
			push_warning("kun: klip %s v modelu neni" % b[0])
			continue
		var n := AnimationNodeAnimation.new()
		n.animation = jm
		bs.add_blend_point(n, Vector2(b[1], b[2]))
	bt.add_node("chod", bs)
	bt.add_node("tempo", AnimationNodeTimeScale.new())
	var os := AnimationNodeOneShot.new()
	os.fadein_time = float(PROLINANI[0])
	os.fadeout_time = float(PROLINANI[1])
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
		if String(a).contains("Ilde") or String(a).contains("Idle") or String(a).contains("Walk") or String(a).contains("Gallop") or String(a).contains("Swim"):
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
	main.hud.toast("Na koni – packa vpřed krok, naplno cval, běh = trysk" + (" · drží se cesty" if drzet_cestu else ""), 2.5)


func sesedni() -> void:
	if jezdec == null:
		return
	var hrac := jezdec
	jezdec = null
	hrac.set("na_koni", null)
	# vlevo od kone (jezdci sesedaji vlevo), na zem
	var vlevo := global_transform.basis * Vector3(-1.0, 0, 0)
	var cil := global_position + vlevo * SESEDNOUT + Vector3(0, 0.2, 0)
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
	var dohled := CESTA_DOHLED + _rych * CESTA_DOHLED_V
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
	if not _vystroj_cekat.is_empty():
		_vystroj_usadit()
	var cil_rych := 0.0
	var cil_yaw := _yaw
	if jezdec != null:
		var inp: Vector2 = jezdec.get("move_input")
		var beh: bool = jezdec.get("beh")
		var pohled: float = jezdec.get("yaw")
		var ml := clampf(inp.y, -1.0, 1.0)
		if vydrz <= 0.0:
			_vycerpan = true
		elif vydrz > VYDRZ_MAX / 3.0:
			_vycerpan = false
		if ml > 0.1:
			if beh and not _vycerpan:
				chod = "trysk"                            # beh jako u hrace = trysk (stoji vydrz)
			else:
				chod = "cval" if ml > 0.8 or beh else "krok"
		elif ml < -0.3:
			chod = "krok"
		else:
			chod = "stani"
		cil_rych = float(CHODY[chod]) * (-COUVANI if ml < -0.3 else 1.0)
		# rizeni: pohled jezdce (kamera) + packa do stran; na ceste bez rizeni po ose
		var rizeni := inp.x
		cil_yaw = pohled if absf(wrapf(pohled - _yaw, -PI, PI)) < deg_to_rad(100.0) else _yaw
		if absf(rizeni) > 0.25:
			cil_yaw = _yaw - rizeni * 0.6
		elif drzet_cestu and _rych > 0.5:
			var sc := _smer_cesty(Vector2(global_position.x, global_position.z), _yaw, pohled)
			if sc != INF and absf(wrapf(pohled - sc, -PI, PI)) < CESTA_ODBOCKA:
				cil_yaw = sc
		if chod == "trysk":
			vydrz = maxf(0.0, vydrz - delta)
		else:
			vydrz = minf(VYDRZ_MAX, vydrz + delta * VYDRZ_OBNOVA)
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
	var max_ot := float(OTACENI.get(chod, 1.0))
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
	_at.set("parameters/tempo/scale", -tempo if _rych < -0.1 else tempo)
	# kopyta: kadence podle chodu
	if absf(_rych) > 0.3:
		_krok += absf(_rych) * delta
		var delka := float(KROK[0]) if absf(_rych) < (float(CHODY["krok"]) + float(CHODY["cval"])) * 0.5 else float(KROK[1])
		if _krok > delka:
			_krok = 0.0
			kopyto.emit("cesta", clampf(absf(_rych) / 6.0, 0.4, 1.4))
	# volny kun se obcas pase
	if jezdec == null and absf(_rych) < 0.1:
		_past -= delta
		if _past < 0.0:
			_past = randf_range(float(PASTVA[0]), float(PASTVA[1]))
			_jednou(String(NECINNOST.pick_random()) if not KLIPY_Z_USEKU.is_empty() else "6 Eat")
	# jezdec v sedle (poloha a vyska oci; pohupovani podle chodu)
	if jezdec != null:
		var cv := absf(_rych) >= (float(CHODY["krok"]) + float(CHODY["cval"])) * 0.5
		var houp := sin(_krok / float(KROK[1] if cv else KROK[0]) * TAU) * float(HOUPANI[1] if cv else HOUPANI[0])
		(jezdec as Node3D).global_position = sedlo_global() + Vector3(0, houp, 0)
		jezdec.set("velocity", velocity)
