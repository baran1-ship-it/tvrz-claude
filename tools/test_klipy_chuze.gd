extends SceneTree
## Test klipy_chuze (Misa 9. 11. „animace v KCD kvalite“ - kroky bez klouzani nohou). Bez sveta, headless, sekundy:
## z kazdeho klipu chuze/behu (UAL, kostra postav) se zmeri rychlost, kterou klip „sam jde“: chodidlo na zemi (spicka
## ball_* do dotyk_m nad svym minimem) jede vuci koreni dozadu - prumer teto rychlosti = rychlost klipu. Porovna s daty:
## postavy.json chuze_klip_m_s (postavy) a jizda.json telo.klipy_m_s (telo hrace). Odchylka nad klouzani_podil = CHYBA
## (nohy by klouzaly). Vypise i delku kroku a podil opory.
## Spusteni: tools/beh.sh klipy cmd godot --headless --path . -s res://tools/test_klipy_chuze.gd
## Vystup: KLIP ... radky, TEST KLIPY_CHUZE OK/CHYBA.

const Lide := preload("res://scripts/lide.gd")
const Pravidla := preload("res://scripts/pravidla.gd")
var chyb := 0


func _initialize() -> void:
	_beh.call_deferred()


func _beh() -> void:
	var koren := Node3D.new()
	root.add_child(koren)
	var lide: Node3D = Lide.new()
	koren.add_child(lide)
	var P: Dictionary = Lide.P
	var o: Dictionary = (P["obyvatele"] as Array)[0]
	var c: Dictionary = lide.nova_postava(o)
	var u: Node3D = c["uzel"]
	u.scale = Vector3.ONE
	var kostra: Skeleton3D = c["kostra"]
	var ap: AnimationPlayer = c["ap"]
	var T: Dictionary = Pravidla.cti("postavy", "test_chuze")
	var zdroje := {"postavy": P["klip_m_s"], "telo": Pravidla.cti("jizda", "telo", "klipy_m_s")}
	var zmereno := {}
	for jm: String in T["klipy"]:
		if not ap.has_animation(jm):
			print("KLIP %s chybi v knihovne" % jm)
			continue
		var dl := ap.get_animation(jm).length
		var n := 120
		var rych: Array = []
		var opora := 0
		var body := {"l": [], "r": []}
		for i in n + 1:
			ap.stop()
			ap.play(jm, 0.0)
			ap.seek(dl * float(i) / n, true)
			ap.advance(0.0)
			for strana: String in ["l", "r"]:
				var ib := kostra.find_bone("ball_" + strana)
				(body[strana] as Array).append(u.global_transform.affine_inverse() * (kostra.global_transform * kostra.get_bone_global_pose(ib).origin))
		var ymin := INF
		for strana: String in body:
			for b: Vector3 in body[strana]:
				ymin = minf(ymin, b.y)
		# opora = nizsi spicka a do dotyk_m nad minimem; rychlost jen podel smeru chuze (osa z postavy)
		for i in n:
			for strana: String in ["l", "r"]:
				var jina := "r" if strana == "l" else "l"
				var a: Vector3 = body[strana][i]
				var b: Vector3 = body[strana][i + 1]
				# jen pohyb spicky dozadu (postava hledi po +z): driv absf - u behu (opora 9-12 %) se pocitala i svihova
				# faze nizko nad zemi (spicka jede dopredu ~2x rychleji) a rychlost behu vysla nadsazena (jog 5,9 m/s)
				if a.y <= (body[jina][i] as Vector3).y and a.y < ymin + float(T["dotyk_m"]) and b.y < ymin + float(T["dotyk_m"]) and b.z < a.z:
					rych.append((a.z - b.z) / (dl / n))
					opora += 1
		rych.sort()
		var v: float = rych[rych.size() / 2] if not rych.is_empty() else 0.0       # median (dotyk a odraz spicky mimo)
		zmereno[jm] = v
		print("KLIP %-22s delka %.2f s, rychlost klipu %.2f m/s (median opory), opora %.0f %%" % [jm, dl, v, 100.0 * opora / float(n)])
	for zd: String in zdroje:
		var data: Dictionary = zdroje[zd]
		for jm: String in data:
			if jm.begins_with("_") or not zmereno.has(jm):
				continue
			var v: float = zmereno[jm]
			var ma := float(data[jm])
			var odch := absf(ma - v) / maxf(v, 1e-3)
			var ok := odch <= float(T["klouzani_podil"])
			if not ok:
				chyb += 1
			print("KLIP %s %-22s data %.2f m/s, klip %.2f m/s, odchylka %.0f %% %s" % [zd, jm, ma, v, odch * 100.0, "OK" if ok else "CHYBA (nohy kluzou)"])
	# hrac (Misa 10. 11. varianta B): klouzani nohou pri rychlostech hrace (player.gd WALK, RUN) - body prolnuti tela
	# (jizda.json telo.klip_chuze, Jog, Sprint) se synchronizaci kroku: klip jde prumerem zmerenych rychlosti podle vah
	# prolnuti, pod bodem chuze tempo = rychlost / bod chuze
	var kd: Dictionary = Pravidla.cti("jizda", "telo", "klipy_m_s")
	var body_t: Array = [[String(Pravidla.cti("jizda", "telo", "klip_chuze"))], ["Jog_Fwd_Loop"], ["Sprint_Loop"]]
	for b: Array in body_t:
		b.append(float(kd.get(b[0], 0.0)))
		b.append(float(zmereno.get(b[0], 0.0)))
	var kon: Dictionary = (load("res://scripts/player.gd") as GDScript).get_script_constant_map()
	# player.gd WALK/RUN musi sedet s hrac.json (cislo jen v datech, const kvuli tomuto testu)
	for par: Array in [["WALK", "chuze_m_s"], ["RUN", "beh_m_s"]]:
		if absf(float(kon.get(par[0], -1.0)) - float(Pravidla.cti("hrac", par[1]))) > 1e-3:
			print("KLIP CHYBA player.gd %s %s != hrac.json %s" % [par[0], str(kon.get(par[0])), par[1]])
			chyb += 1
	for nm: String in ["WALK", "RUN"]:
		if not kon.has(nm):
			continue
		var hv := float(kon[nm])
		var ef := 0.0
		if hv <= float(body_t[0][1]):
			ef = float(body_t[0][2]) * hv / maxf(float(body_t[0][1]), 1e-3)
		elif hv >= float(body_t[2][1]):
			ef = float(body_t[2][2]) * hv / maxf(float(body_t[2][1]), 1e-3)
		else:
			for i in 2:
				var a: Array = body_t[i]
				var b2: Array = body_t[i + 1]
				if hv >= float(a[1]) and hv <= float(b2[1]):
					var w := (hv - float(a[1])) / maxf(float(b2[1]) - float(a[1]), 1e-3)
					ef = lerpf(float(a[2]), float(b2[2]), w)
		var odh := absf(ef - hv) / hv
		var ok2 := odh <= float(T["klouzani_podil"])
		if not ok2:
			chyb += 1
		print("KLIP hrac %s %.2f m/s: klip jde %.2f m/s, klouzani %.0f %% %s" % [nm, hv, ef, odh * 100.0, "OK" if ok2 else "CHYBA"])
	print("TEST KLIPY_CHUZE %s (%d chyb)" % ["OK" if chyb == 0 else "CHYBA", chyb])
	quit(1 if chyb > 0 else 0)
