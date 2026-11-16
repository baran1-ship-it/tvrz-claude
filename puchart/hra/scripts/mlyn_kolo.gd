extends Node3D
## Toceni casti vodniho mlyna (svet.gd _mlyn_dil, NAVOD_MLYN.md bod 5): osa v lokalnich souradnicich a plna rychlost
## (rad/s) z voda.json mlyn.dil; stavidlo (main.gd, skupina mlyn_kolo) pousti vodu - kolo se rozjede a dobehne za rozjezd_s.
var osa := Vector3.RIGHT
var plna := 0.0
var rozjezd_s := 4.0
var bezi := false
var pad: Node3D = null          # dopad vody z vantroku na korecky: viditelny jen pri puste vode (stavidlo)
var zdvih_m := 0.0              # Puchart (Misa 16. 11.): kolo na spodni vodu se zastavi zdvizenim z proudu (zajimava_mista.json mlyn.zastavit)
var zdvih_s := 2.0
var _w := 0.0
var _y0 := 0.0


func _ready() -> void:
	_w = plna if bezi else 0.0
	_y0 = position.y


func _process(delta: float) -> void:
	if pad and pad.visible != bezi:
		pad.visible = bezi
	_w = move_toward(_w, plna if bezi else 0.0, absf(plna) * delta / maxf(rozjezd_s, 0.1))
	if zdvih_m > 0.0:
		position.y = move_toward(position.y, _y0 + (0.0 if bezi else zdvih_m), zdvih_m * delta / maxf(zdvih_s, 0.1))
	if is_visible_in_tree() and _w != 0.0:
		rotate_object_local(osa, _w * delta)


## Kolo v plnem chodu (mleti jen tehdy).
func v_chodu() -> bool:
	return bezi and absf(_w) >= absf(plna) * 0.95
