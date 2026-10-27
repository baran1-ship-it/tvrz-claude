extends RefCounted
## Ves v oblouku (Misa 27. 10.: „nemusime mit ves vlevo vpravo, udelame zatacku a tahneme ves do boku, to uzavre
## vyhled“; plan docs/screens/ves_plan_navrh.jpg). Puvodni ves z Blenderu (blender/vesnice.py layout: dve rady po
## ctyrech usedlostech podel rovne navsi) je upecena v sitich Vesnice*, terenu Teren_ves a datech svet.json. Kazda
## usedlost (dum, dvur, chlev, zahrada, sad az k zadnimu plotu) se tu presune jako celek na nove misto podel oblouku
## ulice: trojuhelniky siti, samostatne uzly (dvere, vrata), vsechna data v jejim pudorysu (rostliny, vybaveni, kolize,
## mistnosti, ohne, pouziti, pohyb) a s ni i kus terenu (vyska a barva vrcholu, mrizka trava_ves) - dvur, cesticky
## a ploty sedi na svem terenu jako predtim. Stare misto se zatravni.

# [k, stary stred chalupy, stary yaw osy (+u = stit k navsi), L, W, novy stred, novy yaw] (scratchpad planovac.py)
const USEDL := [
	[0, Vector2(461.781, 779.047), 2.27529, 14.000, 7.200, Vector2(369.463, 760.876), -0.76607],
	[1, Vector2(484.237, 798.135), 2.27529, 11.262, 5.682, Vector2(399.875, 749.812), 2.15552],
	[2, Vector2(505.590, 816.285), 2.27529, 11.079, 6.369, Vector2(409.602, 797.031), -0.81607],
	[3, Vector2(525.660, 833.345), 2.27529, 11.915, 5.653, Vector2(452.033, 860.425), -2.70594],
	[4, Vector2(419.386, 830.945), -0.86630, 11.406, 6.166, Vector2(441.715, 786.367), 2.54864],
	[5, Vector2(441.199, 849.486), -0.86630, 13.000, 7.000, Vector2(428.316, 835.214), 0.25041],
	[6, Vector2(461.501, 866.743), -0.86630, 10.662, 6.081, Vector2(413.890, 876.126), 0.47566],
	[7, Vector2(483.642, 885.562), -0.86630, 11.328, 5.735, Vector2(432.124, 907.434), -2.93594],
]
# ulice (planovac plan4.py): od vjezdu u tvrze rovne 75 m ve smeru stare navsi, zatacka 70 st. (polomer 45 m) a 70 m
# rovne - pohled podel ulice se po par domech zavre zatackou; rybnik zustava stranou za vsi (pesina)
const UL_A := Vector2(372.0, 744.0)
const UL_H0 := 0.70472
const UL_L1 := 75.0
const UL_TURN := 1.22173            # 70 st.
const UL_RB := 45.0
const UL_L2 := 70.0
const PRECHOD := 10.0                # okraj pudorysu, kde se teren prolina s okolim (m)

var u: Array = []                     # {k, oc, oau, oav, hu0, hu1, hv0, hv1, nc, nau, nav, dyaw, dy}


func _init() -> void:
	for s: Array in USEDL:
		var oy := float(s[2])
		var ny := float(s[6])
		var L := float(s[3])
		var W := float(s[4])
		u.append({"k": int(s[0]), "oc": s[1], "oau": Vector2(cos(oy), sin(oy)), "oav": Vector2(-sin(oy), cos(oy)),
				# pudorys usedlosti v ramci chalupy (vesnice.py _homestead_green: zadni plot L/2 + 13, boky -W/2 - 6,2 a W/2 + 9,5)
				"hu0": -(L / 2.0 + 14.0), "hu1": L / 2.0 + 2.5, "hv0": -W / 2.0 - 7.2, "hv1": W / 2.0 + 10.5,
				"nc": s[5], "nau": Vector2(cos(ny), sin(ny)), "nav": Vector2(-sin(ny), cos(ny)), "dyaw": ny - oy, "dy": 0.0,
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
	var zak := PackedVector2Array([UL_A])
	var p := UL_A
	var h := UL_H0
	for i in int(UL_L1):
		p += Vector2(cos(h), sin(h))
		zak.append(p)
	var n := int(absf(UL_TURN) * UL_RB)
	for i in n:
		h += UL_TURN / n
		p += Vector2(cos(h), sin(h)) * absf(UL_TURN) * UL_RB / n
		zak.append(p)
	for i in int(UL_L2):
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
	for i in m:
		var o := 2.0 * sin(i / 9.0 + 0.6) + 0.6 * sin(i / 4.1 + 2.0)
		for d: Array in domy:
			o += float(d[1]) * clampf((float(d[2]) - 6.0) * 0.9, -1.5, 3.0) * exp(-pow((i - int(d[0])) / 13.0, 2.0))
		off[i] = o * smoothstep(0.0, 12.0, float(i))          # vjezd navazuje na cestu od tvrze
	# do pudorysu usedlosti ne (pulsirka 1,6 + 0,8 rezerva): zkracovat odklon, pak vyhladit
	for k in 6:
		for i in m:
			if nova(zak[i] + nrm[i] * off[i], 2.4)[0] >= 0:
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


## Ulice napric rovna (Misa 27. 10. „cesta jakoby v brehu“; test ves_ulice: ulice vedla napric svahem mezi dvory,
## 4 m od osy +1,4 / -1,2 m): vyska osy yc (z mrizky trava_ves po presunu, vyhlazena podel), kolem osy teren
## k ni - na hlinu a 0,6 m za ni zbude ctvrtina priecneho sklonu (vyslapana ulice), k 5 m za okrajem prechod do svahu.
var yc := PackedFloat32Array()
var _yc_mriz := {}
const UL_HW := 1.5


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
					_yc_mriz[k] = PackedInt32Array()
				(_yc_mriz[k] as PackedInt32Array).append(i)


func uprav_y(p: Vector2, y: float) -> float:
	if yc.is_empty():
		return y
	var l: PackedInt32Array = _yc_mriz.get(Vector2i(floori(p.x / 4.0), floori(p.y / 4.0)), PackedInt32Array())
	if l.is_empty():
		return y
	var bi := -1
	var bd := INF
	for i in l:
		var d := p.distance_squared_to(_osa[i])
		if d < bd:
			bd = d
			bi = i
	var d := sqrt(bd)
	var w := 1.0 - smoothstep(UL_HW + 0.6, UL_HW + 5.0, d)
	if w <= 0.0:
		return y
	var cil := yc[bi] + (y - yc[bi]) * 0.25
	return lerpf(y, cil, w)
