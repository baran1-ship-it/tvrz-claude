extends SceneTree
## Overeni pravidla pravidla/lod_import.json ve hre (plan 18. 11. C14): kazda citliva sit z importu ma 0 LOD urovni.
## Seznam pise tools/lod_import.py (build/lod_import_plan.json: soubor -> null = cely soubor | jmena siti v importu).
## LOD urovne vraci jen skutecny renderer (headless = dummy) -> spoustet s xvfb a gl_compatibility:
##   tools/beh.sh lodimp cmd xvfb-run -a godot --path . --rendering-driver opengl3 --rendering-method gl_compatibility -s tools/lod_import_over.gd
## Vypis: LOD_IMPORT_OVER OK|CHYBA, radky LOD_SIT <soubor> <sit> <povrch> <urovni>.
func _init() -> void:
	var f := FileAccess.open("res://build/lod_import_plan.json", FileAccess.READ)
	if f == null:
		print("LOD_IMPORT_OVER CHYBA chybi build/lod_import_plan.json (python3 tools/lod_import.py kontrola)")
		quit(1)
		return
	var plan: Dictionary = JSON.parse_string(f.get_as_text())
	var chyby: Array = []
	var n_sit := 0
	var bez_zdroje := 0
	for soubor: String in plan:
		var cesta := "res://" + soubor
		if not ResourceLoader.exists(cesta):
			bez_zdroje += 1
			continue
		var ps := load(cesta) as PackedScene
		if ps == null:
			chyby.append("%s nenacteno" % soubor)
			continue
		var sc := ps.instantiate()
		var jen = plan[soubor]
		for nd in sc.find_children("*", "MeshInstance3D", true, false):
			var me := (nd as MeshInstance3D).mesh
			if me == null:
				continue
			if jen != null and not (jen as Array).has(String(me.resource_name)):
				continue
			n_sit += 1
			for si in me.get_surface_count():
				var u: int = (RenderingServer.mesh_get_surface(me.get_rid(), si).get("lods", []) as Array).size()
				if u > 0:
					chyby.append("%s %s/%d: %d LOD" % [soubor, me.resource_name, si, u])
				if OS.has_environment("TVRZ_LOD_VYPIS") or u > 0:
					print("LOD_SIT %s %s %d %d" % [soubor, me.resource_name, si, u])
		if jen != null:
			for j: String in jen:
				var ok := false
				for nd in sc.find_children("*", "MeshInstance3D", true, false):
					if (nd as MeshInstance3D).mesh and String((nd as MeshInstance3D).mesh.resource_name) == j:
						ok = true
				if not ok:
					chyby.append("%s: sit %s v importu neni (jmeno site?)" % [soubor, j])
		sc.free()
	print("LOD_IMPORT_OVER %s souboru %d (bez zdroje %d), siti %d, chyb %d %s" % ["OK" if chyby.is_empty() else "CHYBA", plan.size(), bez_zdroje, n_sit, chyby.size(), str(chyby.slice(0, 10))])
	quit(0 if chyby.is_empty() else 1)
