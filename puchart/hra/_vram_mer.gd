extends Node
# dočasné (agent textur 17. 11.): po 40 s hry výpis textur ve scéně a konec
var t := 0.0
func _process(d: float) -> void:
	t += d
	if Engine.get_process_frames() > 200 and t > 40.0:
		var out := OS.get_environment("VRAM_OUT")
		print("VRAMMER ", preload("res://scripts/textury_vram.gd").zapis(get_tree().current_scene, out))
		get_tree().quit()
