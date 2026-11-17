extends SceneTree
## Závislosti scén a zdrojů (nastroje/textury_vram.py, plán 17. 11. A2): pro každý .glb/.gltf/.blend/.tscn/.scn/.tres/.res
## v projektu ResourceLoader.get_dependencies (importované scény jsou komprimované RSCC – Python je nečte). Výstup JSON do
## souboru z proměnné PUCHART_ZAVISLOSTI: {"res://cesta": ["res://závislost", …]}. Spouští ho textury_vram.py.
const PRIPONY := ["glb", "gltf", "blend", "tscn", "scn", "tres", "res"]
var out := {}

func _pruchod(d: String) -> void:
	for f in DirAccess.get_files_at(d):
		if f.get_extension() in PRIPONY:
			var p := d.path_join(f)
			var z := []
			for x in ResourceLoader.get_dependencies(p):
				z.append(x.get_slice("::", 2) if x.contains("::") else x)   # "uid::typ::cesta"
			out[p] = z
	for s in DirAccess.get_directories_at(d):
		if not s.begins_with("."): _pruchod(d.path_join(s))

func _init() -> void:
	_pruchod("res://")
	var f := FileAccess.open(OS.get_environment("PUCHART_ZAVISLOSTI"), FileAccess.WRITE)
	f.store_string(JSON.stringify(out)); f.close()
	print("ZAVISLOSTI zdrojů %d" % out.size())
	quit()
