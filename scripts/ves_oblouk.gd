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
	[0, Vector2(461.781, 779.047), 2.27529, 14.000, 7.200, Vector2(370.565, 778.197), -0.40086],
	[1, Vector2(484.237, 798.135), 2.27529, 11.262, 5.682, Vector2(392.936, 760.268), 2.56125],
	[2, Vector2(505.590, 816.285), 2.27529, 11.079, 6.369, Vector2(388.676, 808.168), -0.68047],
	[3, Vector2(525.660, 833.345), 2.27529, 11.915, 5.653, Vector2(451.031, 813.929), 2.09945],
	[4, Vector2(419.386, 830.945), -0.86630, 11.406, 6.166, Vector2(420.289, 797.800), 2.46308],
	[5, Vector2(441.199, 849.486), -0.86630, 13.000, 7.000, Vector2(419.582, 832.169), -1.04708],
	[6, Vector2(461.501, 866.743), -0.86630, 10.662, 6.081, Vector2(450.467, 848.184), -1.09669],
	[7, Vector2(483.642, 885.562), -0.86630, 11.328, 5.735, Vector2(499.494, 828.566), 1.45076],
]
# ulice: oblouk kruznice (stred, polomer, uhel vjezdu od tvrze, uhel konce u rybnika)
const OBL_O := Vector2(503.179, 705.602)
const OBL_R := 136.683
const OBL_A0 := 2.85683
const OBL_A1 := 1.50621
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


## Body osy ulice (po ~1 m) od vjezdu k rybniku.
func osa_ulice() -> PackedVector2Array:
	var out := PackedVector2Array()
	var n := int(absf(OBL_A1 - OBL_A0) * OBL_R)
	for i in n + 1:
		var a := lerpf(OBL_A0, OBL_A1, float(i) / n)
		out.append(OBL_O + Vector2(cos(a), sin(a)) * OBL_R)
	return out


## Vahy usedlosti v bode noveho sveta: [[index, vaha 0..1]] (vaha 1 uvnitr pudorysu, k okraji prechodu 0).
## Kdyz se prechody dvou usedlosti prekryvaji, teren se sklada z obou (zadny hrbet mezi nimi).
func vahy(p: Vector2) -> Array:
	var out: Array = []
	for i in u.size():
		var d := _venku(u[i], _ab(u[i], p, true))
		if d < PRECHOD:
			out.append([i, 1.0 - smoothstep(0.0, PRECHOD, maxf(d, 0.0))])
	return out
