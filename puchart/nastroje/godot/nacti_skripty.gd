extends SceneTree
## Vrstva 0: načte (zkompiluje) všechny skripty v res://scripts – chyba i ve skriptu testů, který se při startu nenačítá.
func _init() -> void:
	var chyb := 0
	for f in DirAccess.get_files_at("res://scripts"):
		if f.ends_with(".gd"):
			var s: GDScript = load("res://scripts/" + f)
			if s == null or not s.can_instantiate(): print("SKRIPT_CHYBA ", f); chyb += 1
	print("SKRIPTY_NACTENY chyb ", chyb)
	quit(1 if chyb else 0)
