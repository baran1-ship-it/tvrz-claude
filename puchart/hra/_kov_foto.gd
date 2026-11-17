extends Node
# dočasné (agent textur 17. 11.): snímek kovadliny – v režimu snímku se funkce (osad_kovadliny) nespouští
var n := 0
func _process(_d: float) -> void:
	n += 1
	if n == 1: print("KOVFOTO ", preload("res://scripts/funkce.gd").osad_kovadliny(get_tree().current_scene).size())
