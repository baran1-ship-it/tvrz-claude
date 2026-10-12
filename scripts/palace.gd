extends RefCounted
## Palac u severni hradby: dole hodovni sin a spizirna, nahore komnata a loznice, na dvorni strane pavlac.

const Batch := preload("res://scripts/mesh_batch.gd")
const Fort := preload("res://scripts/fort.gd")
const Props := preload("res://scripts/props.gd")

const X0 := -3.0       # zapadni stit (vnejsi lic)
const X1 := 17.0       # vnitrni lic vychodni hradby
const OX := 18.8
const ZN := -14.0      # vnitrni lic severni hradby
const OZN := -15.8
const ZS := -7.0       # dvorni pruceli (vnejsi lic)
const T := 0.6         # tloustka pruceli a stitu
const F1 := 3.9        # podlaha patra
const EAVE := 7.5
const RIDGE_Z := -11.4
const RIDGE_Y := 11.46
const BASE := -4.5
const WOOD := Color(0.8, 0.74, 0.66)
const DARK := Color(0.56, 0.5, 0.44)
const PLASTER := Color(0.97, 0.95, 0.92)

var M: Dictionary
var info: Dictionary
var P: Props


func _init(p_mats: Dictionary, p_info: Dictionary, props: Props) -> void:
	M = p_mats
	info = p_info
	P = props


func build(parent: Node3D) -> void:
	_shell(parent)
	_gallery(parent)
	_hall(parent)
	_pantry(parent)
	_chamber(parent)
	_bedroom(parent)


func _roof_y(z: float) -> float:
	return RIDGE_Y - 0.9 * absf(z - RIDGE_Z)


func _shell(parent: Node3D) -> void:
	var b := Batch.new(M, 101)
	var ST := Color(1, 1, 1)
	# severni hradba v delce palace, s okny
	Fort.wall_x(b, "stone", X0, OX, OZN, ZN, BASE, EAVE, [
		[5.7, 6.3, 1.9, 3.1], [9.7, 10.3, 1.9, 3.1], [13.7, 14.3, 1.9, 3.1],
		[1.6, 2.4, 4.9, 6.2], [11.6, 12.4, 4.9, 6.2]])
	# vychodni hradba se stitem a oknem loznice
	Fort.wall_z(b, "stone", ZN, ZS, X1, OX, BASE, EAVE, [[-9.4, -8.5, 4.9, 6.3]])
	b.tri_slab("stone", Vector3(OX, EAVE, OZN), Vector3(OX, EAVE, ZS), Vector3(OX, RIDGE_Y - 0.15, RIDGE_Z), 0.9, ST, false, true)
	# dvorni pruceli: prizemi a patro
	Fort.wall_x(b, "plaster_worn", X0, X1, ZS - T, ZS, 0.0, EAVE, [
		[-0.6, 0.5, 0.0, 2.1], [7.1, 8.9, 0.0, 2.35],
		[4.5, 5.5, 1.3, 2.6], [11.0, 12.0, 1.3, 2.6], [14.0, 15.0, 1.3, 2.6],
		[0.5, 1.6, F1, 5.95], [10.4, 11.5, F1, 5.95],
		[4.0, 5.0, 4.9, 6.2], [13.5, 14.5, 4.9, 6.2]], PLASTER)
	# zapadni stit
	Fort.wall_z(b, "plaster_worn", ZN, ZS - T, X0, X0 + T, 0.0, EAVE, [], PLASTER)
	b.tri_slab("planks", Vector3(X0 + 0.25, EAVE, OZN + 0.2), Vector3(X0 + 0.25, EAVE, ZS), Vector3(X0 + 0.25, RIDGE_Y - 0.15, RIDGE_Z), 0.2, Color(0.62, 0.57, 0.52))
	# kamenny sokl a narozi
	b.bb("stone", Vector3(X0 - 0.06, 0.0, ZS - 0.02), Vector3(X1, 0.55, ZS + 0.07), ST, false, -1, 0, true)
	b.bb("ashlar", Vector3(X0 - 0.05, 0.0, ZS - T - 0.3), Vector3(X0 + 0.5, EAVE, ZS + 0.05), Color(0.9, 0.88, 0.84))
	# strecha: dve roviny, hreben podel X
	var sh := Color(0.9, 0.87, 0.83)
	var xa := X0 - 0.5
	var xb := OX + 0.35
	var zn := OZN - 0.45
	var zs := -5.35
	b.slab("shingles", Vector3(xa, _roof_y(zn), zn), Vector3(xb, _roof_y(zn), zn), Vector3(xb, RIDGE_Y, RIDGE_Z), Vector3(xa, RIDGE_Y, RIDGE_Z), 0.16, sh, false, "planks")
	b.slab("shingles", Vector3(xa, _roof_y(zs), zs), Vector3(xb, _roof_y(zs), zs), Vector3(xb, RIDGE_Y, RIDGE_Z), Vector3(xa, RIDGE_Y, RIDGE_Z), 0.16, sh, false, "planks")
	b.beam("beam", Vector3(xa, RIDGE_Y + 0.05, RIDGE_Z), Vector3(xb, RIDGE_Y + 0.05, RIDGE_Z), 0.22, 0.12, DARK)
	# krokve a hambalky viditelne z patra
	var x := X0 + 1.0
	while x < X1 - 0.3:
		b.beam("beam", Vector3(x, EAVE - 0.1, ZN + 0.1), Vector3(x, RIDGE_Y - 0.25, RIDGE_Z), 0.14, 0.18, DARK)
		b.beam("beam", Vector3(x, EAVE - 0.1, ZS - T + 0.1), Vector3(x, RIDGE_Y - 0.25, RIDGE_Z), 0.14, 0.18, DARK)
		b.beam("beam", Vector3(x, 9.3, RIDGE_Z - 2.25), Vector3(x, 9.3, RIDGE_Z + 2.25), 0.12, 0.16, DARK)
		x += 1.85
	b.beam("beam", Vector3(X0 + T, EAVE - 0.14, ZN + 0.14), Vector3(X1, EAVE - 0.14, ZN + 0.14), 0.24, 0.24, DARK)
	b.beam("beam", Vector3(X0 + T, EAVE - 0.14, ZS - T - 0.14), Vector3(X1, EAVE - 0.14, ZS - T - 0.14), 0.24, 0.24, DARK)
	# komin
	b.bb("stone", Vector3(15.5, 3.0, -11.5), Vector3(16.9, 13.3, -10.1), ST, false, -1, 0, true)
	b.bb("flag", Vector3(15.4, 13.3, -11.6), Vector3(17.0, 13.42, -10.0), Color(0.8, 0.8, 0.78))
	b.bb("soot", Vector3(15.8, 13.42, -11.2), Vector3(16.6, 13.44, -10.4))
	info["smoke"].append(Vector3(16.2, 13.6, -10.8))
	# strop prizemi = podlaha patra
	var z := ZN + 0.5
	while z < ZS - T:
		b.beam("beam", Vector3(X0 + T - 0.1, F1 - 0.42, z), Vector3(X1 + 0.1, F1 - 0.42, z), 0.22, 0.28, DARK)
		z += 1.08
	b.bb("planks", Vector3(X0 + T, F1 - 0.28, ZN), Vector3(X1, F1, ZS - T), WOOD, true, 0)
	# podlahy prizemi
	b.bb("flag", Vector3(X0 + T, -0.2, ZN), Vector3(X1, 0.02, ZS - T), Color(0.82, 0.8, 0.76), true)
	# pricky
	Fort.wall_z(b, "plaster", ZN, ZS - T, 2.8, 3.2, 0.02, F1 - 0.28, [[-11.2, -10.0, 0.02, 2.1]], PLASTER)
	Fort.wall_z(b, "plaster", ZN, ZS - T, 6.8, 7.2, F1, EAVE, [[-9.7, -8.5, F1, 5.95]], PLASTER)
	# pricka pod strechou: petiuhelnik ze tri trojuhelniku
	var q1 := Vector3(7.2, EAVE, ZN)
	var q2 := Vector3(7.2, _roof_y(ZN) - 0.2, ZN)
	var q3 := Vector3(7.2, RIDGE_Y - 0.2, RIDGE_Z)
	var q4 := Vector3(7.2, _roof_y(ZS - T) - 0.2, ZS - T)
	var q5 := Vector3(7.2, EAVE, ZS - T)
	b.tri_slab("plaster", q1, q2, q3, 0.4, PLASTER)
	b.tri_slab("plaster", q1, q3, q5, 0.4, PLASTER)
	b.tri_slab("plaster", q5, q3, q4, 0.4, PLASTER)
	# dozdivka mezi korunou zdi a strechou (jinak by tudy bylo videt ven)
	b.bb("plaster", Vector3(X0 + T, EAVE, ZN - 0.3), Vector3(X1, _roof_y(ZN - 0.3) - 0.02, ZN + 0.04), PLASTER)
	b.bb("plaster", Vector3(X0 + T, EAVE, ZS - T), Vector3(X1, _roof_y(ZS - T + 0.25) - 0.02, ZS - T + 0.25), PLASTER)
	b.beam("beam", Vector3(X0 + T, _roof_y(ZN) - 0.24, ZN + 0.1), Vector3(X1, _roof_y(ZN) - 0.24, ZN + 0.1), 0.26, 0.24, DARK)
	b.beam("beam", Vector3(X0 + T, _roof_y(ZS - T) - 0.24, ZS - T - 0.1), Vector3(X1, _roof_y(ZS - T) - 0.24, ZS - T - 0.1), 0.26, 0.24, DARK)
	# omitka uvnitr na hradebnich zdech (patro) - tenka vrstva
	b.bb("plaster", Vector3(X0 + T, F1, ZN), Vector3(X1, EAVE, ZN + 0.04), PLASTER, false, -1, 0, false)
	# zarubne a nadprazi
	for d: Array in [[-0.05, 2.1, 1.1], [8.0, 2.35, 1.8]]:
		b.bb("beam", Vector3(d[0] - d[2] * 0.5 - 0.12, d[1], ZS - T - 0.04), Vector3(d[0] + d[2] * 0.5 + 0.12, d[1] + 0.22, ZS + 0.04), DARK, false, 0)
	for d2: Array in [[1.05, 5.95, 1.1], [10.95, 5.95, 1.1]]:
		b.bb("beam", Vector3(d2[0] - d2[2] * 0.5 - 0.1, d2[1], ZS - T - 0.04), Vector3(d2[0] + d2[2] * 0.5 + 0.1, d2[1] + 0.18, ZS + 0.04), DARK, false, 0)
	# okenni ramy a okenice na pruceli
	for w: Array in [[5.0, 1.3, 2.6], [11.5, 1.3, 2.6], [14.5, 1.3, 2.6], [4.5, 4.9, 6.2], [14.0, 4.9, 6.2]]:
		_window_frame(b, w[0], w[1], w[2], ZS)
	b.commit(parent, "Palac")
	info["rooms"].append({"name": "sin", "aabb": AABB(Vector3(3.2, 0, ZN), Vector3(X1 - 3.2, F1 - 0.3, ZS - T - ZN)), "ambient": Color(0.20, 0.185, 0.17)})
	info["rooms"].append({"name": "spiz", "aabb": AABB(Vector3(X0 + T, 0, ZN), Vector3(2.8 - X0 - T, F1 - 0.3, ZS - T - ZN)), "ambient": Color(0.16, 0.155, 0.15)})
	info["rooms"].append({"name": "komnata", "aabb": AABB(Vector3(X0 + T, F1, ZN), Vector3(6.8 - X0 - T, 6.5, ZS - T - ZN)), "ambient": Color(0.25, 0.24, 0.23)})
	info["rooms"].append({"name": "loznice", "aabb": AABB(Vector3(7.2, F1, ZN), Vector3(X1 - 7.2, 6.5, ZS - T - ZN)), "ambient": Color(0.24, 0.225, 0.21)})


func _window_frame(b: Batch, cx: float, y0: float, y1: float, z_face: float) -> void:
	var w := 1.0
	b.bb("beam", Vector3(cx - w * 0.5 - 0.08, y0 - 0.1, z_face - T - 0.03), Vector3(cx + w * 0.5 + 0.08, y0, z_face + 0.06), DARK, false, 0)
	b.bb("beam", Vector3(cx - w * 0.5 - 0.08, y1, z_face - T - 0.03), Vector3(cx + w * 0.5 + 0.08, y1 + 0.12, z_face + 0.06), DARK, false, 0)
	b.bb("beam", Vector3(cx - 0.03, y0, z_face - 0.3), Vector3(cx + 0.03, y1, z_face - 0.24), DARK, false, 1)
	b.bb("beam", Vector3(cx - w * 0.5, (y0 + y1) * 0.5 - 0.03, z_face - 0.3), Vector3(cx + w * 0.5, (y0 + y1) * 0.5 + 0.03, z_face - 0.24), DARK, false, 0)
	# otevrene okenice
	for sx: float in [-1.0, 1.0]:
		var hx := cx + sx * (w * 0.5 + 0.02)
		b.box("planks", Transform3D(Basis(Vector3.UP, sx * deg_to_rad(-72.0)), Vector3(hx + sx * 0.08, (y0 + y1) * 0.5, z_face + 0.26)),
				Vector3(0.5, y1 - y0, 0.035), Color(0.5, 0.42, 0.34), false, 1)


func _gallery(parent: Node3D) -> void:
	var b := Batch.new(M, 102)
	var gz0 := ZS
	var gz1 := -5.6
	var gx0 := X0
	var gx1 := 14.2
	# podlaha pavlace
	b.bb("planks", Vector3(gx0, F1 - 0.08, gz0), Vector3(gx1, F1, gz1), WOOD, true, 2)
	var x := gx0 + 0.15
	var posts: Array[float] = []
	while x <= gx1 + 0.01:
		posts.append(x)
		x += 2.86
	for px: float in posts:
		b.beam("beam", Vector3(px, 0.0, gz1 - 0.08), Vector3(px, _roof_y(gz1 - 0.08) - 0.12, gz1 - 0.08), 0.18, 0.18, DARK, false)
		b.boxes.append([Transform3D(Basis.IDENTITY, Vector3(px, 3.0, gz1 - 0.08)), Vector3(0.2, 6.0, 0.2)])
		b.beam("beam", Vector3(px, F1 - 0.2, gz0 - 0.1), Vector3(px, F1 - 0.2, gz1 + 0.05), 0.16, 0.2, DARK)
		b.beam("beam", Vector3(px, F1 - 0.9, gz1 - 0.08), Vector3(px, F1 - 0.24, gz1 - 0.75), 0.1, 0.1, DARK)
		b.beam("beam", Vector3(px, 2.6, gz1 - 0.08), Vector3(px + 0.75, F1 - 0.3, gz1 - 0.08), 0.1, 0.1, DARK)
		b.beam("beam", Vector3(px, 2.6, gz1 - 0.08), Vector3(px - 0.75, F1 - 0.3, gz1 - 0.08), 0.1, 0.1, DARK)
	b.beam("beam", Vector3(gx0, F1 - 0.2, gz1 - 0.08), Vector3(gx1, F1 - 0.2, gz1 - 0.08), 0.16, 0.2, DARK)
	b.beam("beam", Vector3(gx0 - 0.4, _roof_y(gz1 - 0.08) - 0.2, gz1 - 0.08), Vector3(gx1 + 0.4, _roof_y(gz1 - 0.08) - 0.2, gz1 - 0.08), 0.16, 0.18, DARK)
	# zabradli
	b.beam("beam", Vector3(gx0, F1 + 1.0, gz1 - 0.08), Vector3(gx1, F1 + 1.0, gz1 - 0.08), 0.09, 0.1, WOOD)
	b.beam("beam", Vector3(gx0, F1 + 0.18, gz1 - 0.08), Vector3(gx1, F1 + 0.18, gz1 - 0.08), 0.07, 0.08, WOOD)
	var bx := gx0 + 0.2
	while bx < gx1:
		b.bb("planks", Vector3(bx, F1 + 0.2, gz1 - 0.1), Vector3(bx + 0.12, F1 + 0.98, gz1 - 0.06), WOOD, false, 1)
		bx += 0.26
	b.boxes.append([Transform3D(Basis.IDENTITY, Vector3((gx0 + gx1) * 0.5, F1 + 0.55, gz1 - 0.08)), Vector3(gx1 - gx0, 1.1, 0.12)])
	# celo pavlace na vychode
	b.beam("beam", Vector3(gx1, F1 + 1.0, gz0), Vector3(gx1, F1 + 1.0, gz1), 0.09, 0.1, WOOD, true)
	b.beam("beam", Vector3(gx1, F1 + 0.5, gz0), Vector3(gx1, F1 + 0.5, gz1), 0.07, 0.08, WOOD, true)
	# schodiste ze dvora: od zapadu nahoru k pavlaci
	var sz := (gz0 + gz1) * 0.5
	b.stairs("planks", Vector3(-9.4, 0.0, sz), Vector3(1, 0, 0), 6.4, F1, 1.25, 20, WOOD)
	for s2: float in [gz0 + 0.02, gz1 - 0.02]:
		b.beam("beam", Vector3(-9.4, -0.1, s2), Vector3(gx0, F1 - 0.1, s2), 0.09, 0.3, DARK)
	var rx0 := -8.4
	var ry0 := F1 * (rx0 + 9.4) / 6.4 + 0.95
	b.beam("beam", Vector3(rx0, ry0, gz1 - 0.04), Vector3(gx0, F1 + 0.95, gz1 - 0.04), 0.08, 0.1, WOOD, true)
	b.beam("beam", Vector3(rx0, ry0, gz0 + 0.04), Vector3(gx0, F1 + 0.95, gz0 + 0.04), 0.08, 0.1, WOOD, true)
	for k in 4:
		var px2 := lerpf(rx0, gx0, float(k) / 3.0)
		var t := (px2 + 9.4) / 6.4
		for s3: float in [gz0 + 0.04, gz1 - 0.04]:
			b.beam("beam", Vector3(px2, F1 * t - 0.1, s3), Vector3(px2, F1 * t + 1.0, s3), 0.1, 0.1, WOOD)
		if k > 0 and k < 3:
			b.beam("beam", Vector3(px2, 0.0, gz1 - 0.04), Vector3(px2, F1 * t - 0.1, gz1 - 0.04), 0.14, 0.14, DARK)
			b.beam("beam", Vector3(px2, 0.0, gz0 + 0.04), Vector3(px2, F1 * t - 0.1, gz0 + 0.04), 0.14, 0.14, DARK)
	b.commit(parent, "Pavlac")


func _hall(parent: Node3D) -> void:
	var b := Batch.new(M, 103)
	var hx0 := 3.2
	var cz := (ZN + ZS - T) * 0.5      # -10.8
	# krb u vychodni zdi
	var fx := X1
	var ash := Color(0.92, 0.9, 0.86)
	b.bb("ashlar", Vector3(fx - 1.3, 0.02, cz - 1.5), Vector3(fx, 0.24, cz + 1.5), ash, true)
	for sz: float in [-1.0, 1.0]:
		b.bb("ashlar", Vector3(fx - 1.05, 0.24, cz + sz * 1.3 - 0.2), Vector3(fx, 1.45, cz + sz * 1.3 + 0.2), ash, true)
	b.bb("ashlar", Vector3(fx - 1.2, 1.45, cz - 1.6), Vector3(fx, 1.8, cz + 1.6), ash, true)
	# digestor: zuzuje se ke stropu
	var h0 := 1.8
	var h1 := F1 - 0.3
	var pc := Color(0.9, 0.87, 0.82)
	b.slab("plaster", Vector3(fx - 1.15, h0, cz - 1.55), Vector3(fx - 1.15, h0, cz + 1.55), Vector3(fx - 0.6, h1, cz + 0.9), Vector3(fx - 0.6, h1, cz - 0.9), 0.1, pc)
	b.slab("plaster", Vector3(fx - 1.15, h0, cz - 1.55), Vector3(fx, h0, cz - 1.55), Vector3(fx, h1, cz - 0.9), Vector3(fx - 0.6, h1, cz - 0.9), 0.1, pc)
	b.slab("plaster", Vector3(fx - 1.15, h0, cz + 1.55), Vector3(fx, h0, cz + 1.55), Vector3(fx, h1, cz + 0.9), Vector3(fx - 0.6, h1, cz + 0.9), 0.1, pc)
	# zacernene ohniste, popel a polena
	b.bb("soot", Vector3(fx - 0.03, 0.24, cz - 1.1), Vector3(fx - 0.01, 1.45, cz + 1.1))
	b.bb("soot", Vector3(fx - 0.95, 0.24, cz - 1.1), Vector3(fx - 0.03, 0.26, cz + 1.1))
	P.logs(b, Props.at(Vector3(fx - 0.5, 0.26, cz), 90.0), 4, 0.7)
	b.rod("iron", Vector3(fx - 0.75, 0.26, cz - 0.5), Vector3(fx - 0.75, 0.5, cz - 0.5), 0.015, 5)
	b.rod("iron", Vector3(fx - 0.75, 0.26, cz + 0.5), Vector3(fx - 0.75, 0.5, cz + 0.5), 0.015, 5)
	info["fires"].append({"kind": "hearth", "pos": Vector3(fx - 0.5, 0.42, cz), "night_only": false, "size": 1.0, "name": "krb"})
	info["use"].append({"kind": "fire", "pos": Vector3(fx - 1.3, 0.9, cz), "r": 2.0, "name": "krb"})
	P.woodpile(b, Props.at(Vector3(fx - 0.35, 0.02, cz + 2.3), 90.0), 1.0, 4)
	# dlouha tabule a lavice
	var tx := 9.2
	P.table(b, Props.at(Vector3(tx, 0.02, cz)), 6.4, 1.05)
	P.bench(b, Props.at(Vector3(tx, 0.02, cz - 0.95)), 6.0)
	P.bench(b, Props.at(Vector3(tx, 0.02, cz + 0.95)), 6.0)
	P.chair(b, Props.at(Vector3(tx + 3.75, 0.02, cz), 90.0))
	# prostreno
	var ty := 0.8
	for k in 6:
		var px := tx - 2.6 + 1.04 * k
		P.plate(b, Vector3(px, ty, cz - 0.3), k % 2 == 0)
		P.plate(b, Vector3(px + 0.3, ty, cz + 0.32), k % 3 == 0)
		P.mug(b, Vector3(px + 0.22, ty, cz - 0.18))
		P.mug(b, Vector3(px + 0.05, ty, cz + 0.2))
	P.jug(b, Vector3(tx - 1.4, ty, cz + 0.02), 1.15)
	P.jug(b, Vector3(tx + 1.7, ty, cz - 0.04))
	P.bread(b, Vector3(tx + 0.4, ty, cz))
	P.bread(b, Vector3(tx - 2.2, ty, cz + 0.05))
	P.candle(b, Vector3(tx - 0.6, ty, cz), true, 0.18)
	P.candle(b, Vector3(tx + 2.5, ty, cz + 0.02), true, 0.15)
	# lustr
	P.chandelier(b, Vector3(tx, 2.55, cz), 0.75, F1 - 0.42, 10)
	# podel sten: truhly, police, sud, zavesy
	P.chest(b, Props.at(Vector3(hx0 + 0.45, 0.02, cz + 1.2), 90.0), 1.15)
	P.shelf(b, Props.at(Vector3(hx0 + 0.25, 0.02, cz - 1.8), 90.0), 1.6, 1.9, 4)
	for k in 3:
		P.jug(b, Vector3(hx0 + 0.25, 0.75 + 0.0, cz - 2.4 + 0.5 * k), 0.9 + 0.1 * k)
		P.plate(b, Vector3(hx0 + 0.25, 1.33, cz - 2.3 + 0.5 * k))
	P.barrel(b, Vector3(hx0 + 0.6, 0.02, ZN + 0.6))
	P.hanging(b, Props.at(Vector3(6.6, 3.2, ZN + 0.03)), 2.2, 1.9, Color(0.46, 0.14, 0.12))
	P.hanging(b, Props.at(Vector3(12.0, 3.2, ZN + 0.03)), 2.2, 1.9, Color(0.16, 0.24, 0.42))
	P.rug(b, Props.at(Vector3(14.6, 0.02, cz)), 2.2, 3.2, Color(0.42, 0.14, 0.12))
	P.shield(b, Props.at(Vector3(8.0, 2.6, ZS - T - 0.03), 180.0), Color(0.5, 0.12, 0.1), Color(0.86, 0.82, 0.7))
	b.rod("steel", Vector3(7.5, 2.95, ZS - T - 0.05), Vector3(8.5, 2.25, ZS - T - 0.05), 0.012, 5)
	P.torch(b, Vector3(4.2, 2.1, ZN + 0.02), Vector3(0, 0, 1), false)
	P.torch(b, Vector3(13.2, 2.1, ZS - T - 0.02), Vector3(0, 0, -1), false)
	b.commit(parent, "Sin")


func _pantry(parent: Node3D) -> void:
	var b := Batch.new(M, 104)
	var px0 := X0 + T
	P.barrel(b, Vector3(px0 + 0.5, 0.02, ZN + 0.55))
	P.barrel(b, Vector3(px0 + 1.25, 0.02, ZN + 0.5))
	P.barrel(b, Vector3(px0 + 0.55, 0.02, ZN + 1.3), 0.3, 0.8)
	P.barrel(b, Vector3(px0 + 2.4, 0.02, ZN + 0.8), 0.36, 1.05, 0.0)
	P.shelf(b, Props.at(Vector3(2.55, 0.02, -12.6), -90.0), 2.2, 2.0, 4)
	for k in 4:
		P.jug(b, Vector3(2.55, 0.17, -13.4 + 0.5 * k), 1.0)
		P.bread(b, Vector3(2.55, 0.77, -13.4 + 0.5 * k))
	P.sack(b, Vector3(px0 + 0.45, 0.02, -9.0))
	P.sack(b, Vector3(px0 + 0.95, 0.02, -8.6))
	P.sack(b, Vector3(px0 + 0.5, 0.02, -8.3), 0.3, true)
	P.crate(b, Props.at(Vector3(px0 + 0.5, 0.02, -10.2), 8.0))
	P.crate(b, Props.at(Vector3(px0 + 0.55, 0.72, -10.25), -12.0), 0.55)
	P.table(b, Props.at(Vector3(0.6, 0.02, -8.4)), 1.8, 0.8)
	P.jug(b, Vector3(0.3, 0.8, -8.4))
	P.bread(b, Vector3(0.9, 0.8, -8.35))
	P.candle(b, Vector3(1.2, 0.8, -8.5), true)
	# suseny na tramu: svazky bylin
	for k in 5:
		var hx := -1.6 + 0.8 * k
		b.rod("fabric", Vector3(hx, F1 - 0.56, -11.2), Vector3(hx, F1 - 0.9, -11.2), 0.004, 3, Color(0.6, 0.5, 0.3))
		b.ball("straw", Vector3(hx, F1 - 1.05, -11.2), Vector3(0.09, 0.17, 0.09), 6, Color(0.55, 0.7, 0.4))
	b.commit(parent, "Spiz")


func _chamber(parent: Node3D) -> void:
	var b := Batch.new(M, 105)
	var cx0 := X0 + T
	var y := F1
	# psaci stul u okna, zidle, knihy
	P.table(b, Props.at(Vector3(4.5, y, -8.5)), 1.9, 0.85)
	P.chair(b, Props.at(Vector3(4.5, y, -9.3), 180.0))
	P.book(b, Props.at(Vector3(4.2, y + 0.8, -8.5), 12.0), Color(0.9, 0.4, 0.3))
	P.book(b, Props.at(Vector3(4.24, y + 0.85, -8.48), -8.0), Color(0.5, 0.7, 0.5))
	P.candle(b, Vector3(5.1, y + 0.8, -8.4), true, 0.16)
	P.jug(b, Vector3(3.8, y + 0.8, -8.35), 0.8)
	# police s knihami, truhly, kozesina
	P.shelf(b, Props.at(Vector3(cx0 + 0.22, y, -11.5), 90.0), 2.2, 2.0, 4)
	for k in 5:
		P.book(b, Props.at(Vector3(cx0 + 0.22, y + 0.77, -12.3 + 0.4 * k), 90.0 + 6.0 * k), Color(0.8 - 0.1 * k, 0.4 + 0.08 * k, 0.3))
		P.jug(b, Vector3(cx0 + 0.22, y + 1.37, -12.3 + 0.4 * k), 0.7)
	P.chest(b, Props.at(Vector3(1.0, y, ZN + 0.4)), 1.2)
	P.chest(b, Props.at(Vector3(5.6, y, ZN + 0.4)), 0.9)
	P.rug(b, Props.at(Vector3(2.4, y, -10.6)), 3.2, 2.2, Color(0.2, 0.3, 0.42))
	P.hanging(b, Props.at(Vector3(3.9, y + 2.9, ZN + 0.07)), 2.6, 2.0, Color(0.38, 0.3, 0.12))
	P.stool(b, Props.at(Vector3(1.6, y, -9.6)))
	P.brazier(b, Vector3(-0.2, y, -9.2))
	P.torch(b, Vector3(6.75, y + 2.0, -12.4), Vector3(-1, 0, 0), false)
	b.commit(parent, "Komnata")


func _bedroom(parent: Node3D) -> void:
	var b := Batch.new(M, 106)
	var y := F1
	# postel v rohu u severni zdi
	P.bed(b, Props.at(Vector3(15.9, y, -12.7), 0.0))
	info["use"].append({"kind": "bed", "pos": Vector3(15.9, y + 0.7, -12.4), "r": 2.2})
	# nebesa: ctyri sloupky a zaves
	for sx: float in [-0.75, 0.75]:
		for sz: float in [-1.05, 1.05]:
			b.beam("beam", Vector3(15.9 + sx, y, -12.7 + sz), Vector3(15.9 + sx, y + 2.3, -12.7 + sz), 0.07, 0.07, DARK)
	b.bb("fabric", Vector3(15.1, y + 2.28, -13.8), Vector3(16.7, y + 2.32, -11.6), Color(0.45, 0.14, 0.12))
	b.bb("fabric", Vector3(15.1, y + 1.2, -13.78), Vector3(16.7, y + 2.3, -13.75), Color(0.45, 0.14, 0.12))
	b.bb("fabric", Vector3(16.68, y + 0.6, -13.75), Vector3(16.71, y + 2.3, -12.9), Color(0.45, 0.14, 0.12))
	P.chest(b, Props.at(Vector3(12.6, y, ZN + 0.4)), 1.1)
	P.rug(b, Props.at(Vector3(13.6, y, -11.4)), 2.6, 2.0, Color(0.44, 0.2, 0.14))
	# stolek se svici a dzbanem, zidle
	P.table(b, Props.at(Vector3(14.3, y, -13.45)), 1.0, 0.6, 0.72)
	P.candle(b, Vector3(14.1, y + 0.74, -13.45), true, 0.17)
	P.jug(b, Vector3(14.6, y + 0.74, -13.5), 0.85)
	P.book(b, Props.at(Vector3(14.3, y + 0.74, -13.35), 20.0), Color(0.7, 0.3, 0.25))
	P.chair(b, Props.at(Vector3(13.2, y, -8.6), 200.0))
	# almara a umyvadlo
	P.shelf(b, Props.at(Vector3(7.45, y, -12.4), 90.0), 1.5, 1.9, 3, 0.45)
	b.bb("planks", Vector3(7.22, y, -13.15), Vector3(7.68, y + 1.9, -13.1), WOOD, false, 1)
	b.bb("planks", Vector3(7.22, y, -11.7), Vector3(7.68, y + 1.9, -11.65), WOOD, false, 1)
	P.bucket(b, Vector3(8.4, y, -13.4), true)
	P.stool(b, Props.at(Vector3(9.0, y, -13.3)))
	# male ohniste: kos se zhavym uhlim u vychodni zdi
	P.brazier(b, Vector3(16.3, y, -8.4))
	P.hanging(b, Props.at(Vector3(10.6, y + 2.9, ZN + 0.07)), 2.2, 1.9, Color(0.18, 0.28, 0.2))
	P.shield(b, Props.at(Vector3(7.24, y + 2.2, -9.0), 90.0), Color(0.14, 0.2, 0.36), Color(0.82, 0.7, 0.3))
	b.commit(parent, "Loznice")
