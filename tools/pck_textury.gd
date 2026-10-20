extends SceneTree
## Opravny balik z_textury (radce 20:45 krok 4): zmenene ETC2 .ctex z tools/textury_tablet.py do build/z_textury.pck.
## Hra ho nacte posledni s prepisem (data.gd). godot --headless --path . -s res://tools/pck_textury.gd

func _init() -> void:
	var seznam := FileAccess.get_file_as_string("res://build/textury_tablet.txt").split("\n", false)
	var pk := PCKPacker.new()
	pk.pck_start(ProjectSettings.globalize_path("res://build/z_textury.pck"))
	for f: String in seznam:
		pk.add_file("res://" + f, ProjectSettings.globalize_path("res://" + f))
	pk.flush()
	print("z_textury: %d souboru" % seznam.size())
	quit()
