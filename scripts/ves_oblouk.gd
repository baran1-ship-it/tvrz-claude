extends RefCounted
## Ves v oblouku (Misa 27. 10.: „nemusime mit ves vlevo vpravo, udelame zatacku a tahneme ves do boku, to uzavre
## vyhled“; plan docs/screens/ves_plan_navrh.jpg). Puvodni ves z Blenderu (blender/vesnice.py layout: dve rady po
## ctyrech usedlostech podel rovne navsi) je upecena v sitich Vesnice*, terenu Teren_ves a datech svet.json. Kazda
## usedlost (dum, dvur, chlev, zahrada, sad az k zadnimu plotu) se tu presune jako celek na nove misto podel oblouku
## ulice: trojuhelniky siti, samostatne uzly (dvere, vrata), vsechna data v jejim pudorysu (rostliny, vybaveni, kolize,
## mistnosti, ohne, pouziti, pohyb) a s ni i kus terenu (vyska a barva vrcholu, mrizka trava_ves) - dvur, cesticky
## a ploty sedi na svem terenu jako predtim. Stare misto se zatravni.

# zaznam vsi (radce 27. 10. 09:55 PRAVIDLA ZASAZENI): usedlosti a ulice jen z pravidla/lokace_ves.json, odstupy
# a pricny profil ulice z pravidla/pravidla_sveta.json pasma.ulice_vsi - zadna vlastni cisla tady
const ZAZNAM := "res://pravidla/lokace_ves.json"
const PRAVIDLA := "res://pravidla/pravidla_sveta.json"

var u: Array = []                     # {k, oc, oau, oav, hu0, hu1, hv0, hv1, nc, nau, nav, dyaw, dy}
var ul: Dictionary = {}               # zaznam ulice
var pasmo: Dictionary = {}            # pasma.cesta.ulice_vsi
var PRECHOD := 10.0                   # okraj pudorysu, kde se teren prolina s okolim (m)


func _init() -> void:
	var z: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ZAZNAM))
	var pr: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PRAVIDLA))
	ul = z["ulice"]
	pasmo = pr["pasma"]["cesta"]["ulice_vsi"]
	PRECHOD = float(z["prechod_terenu_m"])
	for e0: Dictionary in z["usedlosti"]:
		var oy := float(e0["stary_yaw"])
		var ny := float(e0["novy_yaw"])
		var L := float(e0["L"])
		var W := float(e0["W"])
		var so: Array = e0["stary_stred"]
		var sn: Array = e0["novy_stred"]
		u.append({"k": int(e0["k"]), "oc": Vector2(so[0], so[1]), "oau": Vector2(cos(oy), sin(oy)), "oav": Vector2(-sin(oy), cos(oy)),
				# pudorys usedlosti v ramci chalupy (vesnice.py _homestead_green: zadni plot L/2 + 13, boky -W/2 - 6,2 a W/2 + 9,5)
				"hu0": -(L / 2.0 + 14.0), "hu1": L / 2.0 + 2.5, "hv0": -W / 2.0 - 7.2, "hv1": W / 2.0 + 10.5,
				"nc": Vector2(sn[0], sn[1]), "nau": Vector2(cos(ny), sin(ny)), "nav": Vector2(-sin(ny), cos(ny)), "dyaw": ny - oy, "dy": 0.0,
				"oyaw": oy, "nyaw": ny})


## Mistni souradnice (a podel osy, b napric) bodu vuci staremu / novemu ramci.
func _ab(e: Dictionary, p: Vector2, novy: bool) -> Vector2:
	var c: Vector2 = e["nc"] if novy else e["oc"]
	var a: Vector2 = e["nau"] if novy else e["oau"]
	var b: Vector2 = e["nav"] if novy else e["oav"]
	return Vector2((p - c).dot(a), (p - c).dot(b))


## Vzdalenost za okrajem pudorysu (< 0 uvnitr).
func _venku(e: Dictionary, ab: Vector2) -> float:
	var du := maxf(float(e["hu0"]) - ab.x, ab.x - float(e["hu1"]))
	var dv := maxf(float(e["hv0"]) - ab.y, ab.y - float(e["hv1"]))
	return maxf(du, dv)


## Usedlost, do jejiz stareho pudorysu bod patri (-1 zadna).
func stara(p: Vector2, okraj := 0.0) -> int:
	for i in u.size():
		if _venku(u[i], _ab(u[i], p, false)) < okraj:
			return i
	return -1


## Usedlost, do jejiz noveho pudorysu (+ okraj) bod patri: [index, vzdalenost za okrajem] nebo [-1, INF].
func nova(p: Vector2, okraj := 0.0) -> Array:
	var best := -1
	var bd := INF
	for i in u.size():
		var d := _venku(u[i], _ab(u[i], p, true))
		if d < okraj and d < bd:
			bd = d
			best = i
	return [best, bd]


## Bod stareho mista -> nove misto (xz).
func presun2(i: int, p: Vector2) -> Vector2:
	var e: Dictionary = u[i]
	var ab := _ab(e, p, false)
	return (e["nc"] as Vector2) + (e["nau"] as Vector2) * ab.x + (e["nav"] as Vector2) * ab.y


## Novy bod -> odkud prisel (xz).
func zdroj2(i: int, p: Vector2) -> Vector2:
	var e: Dictionary = u[i]
	var ab := _ab(e, p, true)
	return (e["oc"] as Vector2) + (e["oau"] as Vector2) * ab.x + (e["oav"] as Vector2) * ab.y


func presun3(i: int, p: Vector3) -> Vector3:
	var q := presun2(i, Vector2(p.x, p.z))
	return Vector3(q.x, p.y + float(u[i]["dy"]), q.y)


func otoceni(i: int) -> Basis:
	return Basis(Vector3.UP, -float(u[i]["dyaw"]))


## Transformace stareho sveta -> nove (cela usedlost i).
func xf(i: int) -> Transform3D:
	var b := otoceni(i)
	var o := Vector3((u[i]["oc"] as Vector2).x, 0.0, (u[i]["oc"] as Vector2).y)
	var n := Vector3((u[i]["nc"] as Vector2).x, float(u[i]["dy"]), (u[i]["nc"] as Vector2).y)
	return Transform3D(b, n) * Transform3D(Basis(), -o)


## Body osy ulice po 1 m od vjezdu. Zaklad je plan4.py (rovne - zatacka 70 st. - rovne), ulice se ale mezi domy
## klikati (Misa 27. 10.: „neni dalnice, klikati se mezi domy smysluplne“): u kazdeho domu se stoci k jeho stitu, kdyz
## stoji dal (vyjezdeno ke dverim), od blizkeho odhne; mezi tim pomala vlna. Do pudorysu usedlosti nevjede.
func osa_ulice() -> PackedVector2Array:
	var p := Vector2(ul["vjezd"][0], ul["vjezd"][1])
	var zak := PackedVector2Array([p])
	var h := float(ul["smer"])
	var turn := deg_to_rad(float(ul["turn_st"]))
	var rb := float(ul["R"])
	for i in int(ul["L1"]):
		p += Vector2(cos(h), sin(h))
		zak.append(p)
	var n := int(absf(turn) * rb)
	for i in n:
		h += turn / n
		p += Vector2(cos(h), sin(h)) * absf(turn) * rb / n
		zak.append(p)
	for i in int(ul["L2"]):
		p += Vector2(cos(h), sin(h))
		zak.append(p)
	var m := zak.size()
	var nrm := PackedVector2Array()
	for i in m:
		var t := (zak[mini(i + 1, m - 1)] - zak[maxi(i - 1, 0)]).normalized()
		nrm.append(Vector2(-t.y, t.x))
	# domy promitnute na zakladni osu: index, strana, odstup stitu od osy
	var domy: Array = []
	for e: Dictionary in u:
		var c: Vector2 = e["nc"]
		var bi := 0
		for i in m:
			if c.distance_squared_to(zak[i]) < c.distance_squared_to(zak[bi]):
				bi = i
		var lat := (c - zak[bi]).dot(nrm[bi])
		domy.append([bi, signf(lat), absf(lat) - (float(e["hu1"]) - 2.5)])
	var off := PackedFloat32Array()
	off.resize(m)
	var ks: Dictionary = ul["ke_stitu"]
	for i in m:
		var o := 0.0
		for vl: Array in ul["vlny"]:
			o += float(vl[0]) * sin(i / float(vl[1]) + float(vl[2]))
		for d: Array in domy:
			o += float(d[1]) * clampf((float(d[2]) - float(ks["od_m"])) * float(ks["nasobek"]), float(ks["min"]), float(ks["max"])) \
					* exp(-pow((i - int(d[0])) / float(ks["dosah"]), 2.0))
		off[i] = o * smoothstep(0.0, float(ul["napojeni_vjezdu_m"]), float(i))          # vjezd navazuje na cestu od tvrze
	# do pudorysu usedlosti ne (pulsirka 1,6 + 0,8 rezerva): zkracovat odklon, pak vyhladit
	for k in 6:
		for i in m:
			if nova(zak[i] + nrm[i] * off[i], float(ul["od_pudorysu_m"]))[0] >= 0:
				off[i] *= 0.6
		var o2 := off.duplicate()
		for i in range(2, m - 2):
			o2[i] = (off[i - 2] + off[i - 1] + off[i] + off[i + 1] + off[i + 2]) / 5.0
		off = o2
	var out := PackedVector2Array()
	for i in m:
		out.append(zak[i] + nrm[i] * off[i])
	return out


var _osa := PackedVector2Array()


## Bod na ulici v podilu f (0 vjezd .. 1 konec) posunuty o bok (m, + vlevo od smeru).
func na_ulici(f: float, bok := 0.0) -> Vector2:
	if _osa.is_empty():
		_osa = osa_ulice()
	var i := clampi(int(f * (_osa.size() - 1)), 0, _osa.size() - 2)
	var t := (_osa[i + 1] - _osa[i]).normalized()
	return _osa[i] + Vector2(-t.y, t.x) * bok


## Vzdalenost od osy ulice.
func od_ulice(p: Vector2) -> float:
	if _osa.is_empty():
		_osa = osa_ulice()
	var d := INF
	for i in range(0, _osa.size(), 2):
		d = minf(d, p.distance_squared_to(_osa[i]))
	return sqrt(d)
## Vahy usedlosti v bode noveho sveta: [[index, vaha 0..1]] (vaha 1 uvnitr pudorysu, k okraji prechodu 0).
## Kdyz se prechody dvou usedlosti prekryvaji, teren se sklada z obou (zadny hrbet mezi nimi).
func vahy(p: Vector2) -> Array:
	var out: Array = []
	for i in u.size():
		var d := _venku(u[i], _ab(u[i], p, true))
		if d < PRECHOD:
			out.append([i, 1.0 - smoothstep(0.0, PRECHOD, maxf(d, 0.0))])
	return out


## Pulsirka ulice v podilu f (zaznam ulice.pulsirka).
func pulsirka(f: float) -> float:
	var ps: Dictionary = ul["pulsirka"]
	var w := float(ps["zaklad"]) + float(ps["vjezd"]) * exp(-pow(f / float(ps["vjezd_delka"]), 2.0))
	for vl: Array in ps["vlny"]:
		w += float(vl[0]) * sin(f * float(vl[1]) + float(vl[2]))
	return clampf(w, float(ps["min"]), float(ps["max"]))


## Ulice napric rovna (Misa 27. 10. „cesta jakoby v brehu“; test ves_ulice: ulice vedla napric svahem mezi dvory,
## 4 m od osy +1,4 / -1,2 m): vyska osy yc (z mrizky trava_ves po presunu, vyhlazena podel), kolem osy teren k ni
## podle pasma ulice_vsi (pricny_podil na hline a rovne_m za ni, pak prechod_m do svahu). Krok stavby terenu - pred
## cestami (cesty berou teren, jak je).
var yc := PackedFloat32Array()
var _yc_mriz := {}


func ulice_vysky(vz: Callable) -> void:
	if _osa.is_empty():
		_osa = osa_ulice()
	var h := PackedFloat32Array()
	for q in _osa:
		h.append(float(vz.call(q)))
	yc.resize(h.size())
	for i in h.size():
		var su := 0.0
		var nn := 0
		for j in range(maxi(i - 6, 0), mini(i + 7, h.size())):
			su += h[j]
			nn += 1
		yc[i] = su / nn
	_yc_mriz.clear()
	for i in _osa.size():
		var c := Vector2i(floori(_osa[i].x / 4.0), floori(_osa[i].y / 4.0))
		for dx in range(-2, 3):
			for dz in range(-2, 3):
				var k := c + Vector2i(dx, dz)
				if not _yc_mriz.has(k):
					_yc_mriz[k] = []
				(_yc_mriz[k] as Array).append(i)          # Array (odkaz) - PackedInt32Array by se pri append kopiroval


func uprav_y(p: Vector2, y: float) -> float:
	if yc.is_empty():
		return y
	var l: Array = _yc_mriz.get(Vector2i(floori(p.x / 4.0), floori(p.y / 4.0)), [])
	if l.is_empty():
		return y
	var bi := -1
	var bd := INF
	for i: int in l:
		var d := p.distance_squared_to(_osa[i])
		if d < bd:
			bd = d
			bi = i
	var d := sqrt(bd)
	var hw := pulsirka(float(bi) / maxf(_osa.size() - 1, 1))
	var r0 := hw + float(pasmo["rovne_m"])
	var w := 1.0 - smoothstep(r0, r0 + float(pasmo["prechod_m"]), d)
	if w <= 0.0:
		return y
	var cil := yc[bi] + (y - yc[bi]) * float(pasmo["pricny_podil"])
	return lerpf(y, cil, w)
