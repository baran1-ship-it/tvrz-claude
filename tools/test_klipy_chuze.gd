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
		for strana: String in ["l", "r"]:
			var ib := kostra.find_bone("ball_" + strana)
			var body: Array = []
			for i in n + 1:
				ap.stop()
				ap.play(jm, 0.0)
				ap.seek(dl * float(i) / n, true)
				ap.advance(0.0)
				body.append(u.global_transform.affine_inverse() * (kostra.global_transform * kostra.get_bone_global_pose(ib).origin))
			var ymin := INF
			for b: Vector3 in body:
				ymin = minf(ymin, b.y)
			for i in n:
				var a: Vector3 = body[i]
				var b: Vector3 = body[i + 1]
				if a.y < ymin + float(T["dotyk_m"]) and b.y < ymin + float(T["dotyk_m"]):
					rych.append(Vector2(b.x - a.x, b.z - a.z).length() / (dl / n))
					opora += 1
		rych.sort()
		var v: float = rych[rych.size() / 2] if not rych.is_empty() else 0.0       # median (dotyk a odraz spicky mimo)
		zmereno[jm] = v
		print("KLIP %-22s delka %.2f s, rychlost klipu %.2f m/s (median opory), opora %.0f %%" % [jm, dl, v, 100.0 * opora / (2.0 * n)])
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
	print("TEST KLIPY_CHUZE %s (%d chyb)" % ["OK" if chyb == 0 else "CHYBA", chyb])
	quit(1 if chyb > 0 else 0)
