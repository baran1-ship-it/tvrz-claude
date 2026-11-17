extends Node
# dočasné (agent textur 17. 11.): ve snímku (PUCHART_FOTO) těsně před uložením výpis textur ve scéně
var n := 0
func _process(_d: float) -> void:
	n += 1
	if n == 8:
		print("VRAMMER ", preload("res://scripts/textury_vram.gd").zapis(get_tree().current_scene, OS.get_environment("VRAM_OUT")))
