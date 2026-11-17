extends Node
## Test znaků mapy a objevování (Míša 17. 11.: „zájmové body pod pěkným malým znakem, ale jen v pískovišti a potom
## v příběhu, když to objevím“): PUCHART_SKRIPT=res://scripts/test_mapa_znaky.gd (xvfb, opengl3).
## Příběh: znak mlýna skrytý → hráč dojde k mlýnu → objeveno a znak viditelný → uložit → nová hra (skrytý) → nahrát
## (viditelný). Pískoviště: všechny znaky hned. Každé zajímavé místo má obrázek znaku. PUCHART_MAPA_FOTO=<předpona>
## uloží snímky mapy <předpona>_pribeh_pred.png, _pribeh_objeveno.png, _hra_oznameni.png, _piskoviste.png.
const MISTO := "mlyn"
var pr: Node
var M: Node
var chyby: Array = []
var foto := OS.get_environment("PUCHART_MAPA_FOTO")


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for k in 400:
		await get_tree().create_timer(0.5, true).timeout
		for c in get_tree().current_scene.get_children():
			if c.get("mapa") != null and c.mapa != null and c.get("hv") != null and c.hv != null: pr = c
		if pr: break
	if pr == null:
		print("MAPA_ZNAKY_TEST CHYBA: hra nenaběhla"); get_tree().quit(); return
	M = pr.mapa
	await get_tree().create_timer(2.0, true).timeout
	var zi := -1
	for i in M.zajimava.size():
		if M.zajimava[i]["id"] == MISTO: zi = i
		if not M._znak_tex.has(M.zajimava[i]["znak"]): chyby.append("%s bez obrázku znaku %s" % [M.zajimava[i]["id"], M.zajimava[i]["znak"]])
	if zi < 0:
		print("MAPA_ZNAKY_TEST CHYBA: místo %s není na mapě" % MISTO); get_tree().quit(); return
	var z: Dictionary = M.zajimava[zi]
	# příběh: nová hra
	pr._akce("story", null)
	await get_tree().create_timer(1.5, true).timeout
	_ma(not M.znak_videt(z), "příběh na začátku: znak %s skrytý" % MISTO)
	var n0: int = M.zajimava.filter(func(q: Dictionary) -> bool: return M.znak_videt(q)).size()
	print("MAPA_ZNAKY_TEST příběh start: viditelných znaků %d z %d (%s)" % [n0, M.zajimava.size(), M.objevena])
	await _snimek("pribeh_pred", -1)
	# dojít k mlýnu (okraj okruhu objevení)
	var cil: Vector2 = z["p"] + Vector2(float(z["okruh"]) * 0.6, 0.0)
	M.priprav_kolize(pr.hlavni, cil)
	await get_tree().physics_frame; await get_tree().physics_frame
	var bez: Array[RID] = [(pr.hrac as CollisionObject3D).get_rid()]
	var p: Vector3 = M.cil_na_zemi(pr.hlavni, M.cfg, cil, bez)
	pr.hrac.velocity = Vector3.ZERO; pr.hrac.position = p + Vector3(0, 0.1, 0)
	pr.hrac.nastav_pohled(atan2(-(z["p"].x - p.x), -(z["p"].y - p.z)), -0.05)
	await get_tree().create_timer(2.5, true).timeout
	_ma(M.objevena.has(MISTO) and M.znak_videt(z), "po příchodu k místu: objeveno a znak viditelný")
	if foto != "":
		get_viewport().get_texture().get_image().save_png(foto + "_hra_oznameni.png")
	await _snimek("pribeh_objeveno", zi)
	# uložit, nová hra (smaže), nahrát (vrátí)
	pr._akce("save", null)
	pr.menu.saves = pr._seznam_ulozeni()
	pr._akce("story", null)
	await get_tree().create_timer(0.5, true).timeout
	_ma(not M.znak_videt(z), "nová hra příběhu: znak zase skrytý")
	if not pr.menu.saves.is_empty(): pr._akce("load", pr.menu.saves[0]["file"])
	await get_tree().create_timer(1.0, true).timeout
	_ma(M.objevena.has(MISTO) and M.znak_videt(z) and pr.hv.mode == "pribeh", "po nahrání uložené hry: znak zůstal (režim %s)" % pr.hv.mode)
	# pískoviště: vše hned
	pr._akce("sandbox", null)
	await get_tree().create_timer(1.0, true).timeout
	var n1: int = M.zajimava.filter(func(q: Dictionary) -> bool: return M.znak_videt(q)).size()
	_ma(n1 == M.zajimava.size(), "pískoviště: viditelných znaků %d z %d" % [n1, M.zajimava.size()])
	await _snimek("piskoviste", -1)
	print("MAPA_ZNAKY_TEST %s" % ("OK" if chyby.is_empty() else "CHYBA " + "; ".join(chyby)))
	get_tree().quit()


func _ma(ok: bool, co: String) -> void:
	print("MAPA_ZNAKY_TEST  %s %s" % ["OK   " if ok else "CHYBA", co])
	if not ok: chyby.append(co)


func _snimek(jmeno: String, vyber: int) -> void:
	if foto == "": return
	M.show_map(); M._vyber_z = vyber; M._hover_z = -1; M._c.queue_redraw()
	for i in 6: await get_tree().process_frame
	await get_tree().create_timer(0.3, true).timeout
	get_viewport().get_texture().get_image().save_png(foto + "_" + jmeno + ".png")
	M.close()
	await get_tree().create_timer(0.3, true).timeout
