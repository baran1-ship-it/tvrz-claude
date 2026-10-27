extends Node3D
## Toceni casti vodniho mlyna (svet.gd _mlyn_dil, NAVOD_MLYN.md bod 5): osa v lokalnich souradnicich a rychlost
## (rad/s) nastavi svet z voda.json mlyn.dil.
var osa := Vector3.RIGHT
var rychlost := 0.0


func _process(delta: float) -> void:
	if is_visible_in_tree():
		rotate_object_local(osa, rychlost * delta)
