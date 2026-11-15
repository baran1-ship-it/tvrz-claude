extends Node
## DOČASNÝ ladicí skript (snímky funkcí 15. 11., po pořízení smazat): PUCHART_FOTO (poloha jen pro načtení okolí) +
## PUCHART_SKRIPT=res://scripts/_foto_funkce.gd + PUCHART_FUNKCE=mech|studna|zlab + PUCHART_FUNKCE_PNG=/abs/cesta.png
func _ready() -> void:
	var h := get_parent(); h._snimek = -100000
	var co := OS.get_environment("PUCHART_FUNKCE"); var png := OS.get_environment("PUCHART_FUNKCE_PNG")
	for i in 30: await get_tree().process_frame
	var cam: Camera3D = h.hrac.cam
	var cl := CanvasLayer.new(); add_child(cl)
	var fu: Node = load("res://scripts/funkce.gd").new(); cl.add_child(fu); fu.zacni(h, cl)
	match co:
		"mech":
			for p: Dictionary in fu.polozky_:
				if p["druh"] != "mech": continue
				var k: Node3D = p["koren"]
				cam.look_at_from_position(k.global_transform * Vector3(1.9, 1.75, 1.7), k.global_transform * Vector3(-0.4, 1.1, -1.6), Vector3.UP)
				fu.foukej(p)
				await get_tree().create_timer(2.6).timeout   # nadechnutý měch, páka dole, výheň rozhořelá
		"studna":
			var dv: Node = h.get_node("DvereFoto")
			for g: String in dv.dily:
				if not g.begins_with("ves_studna"): continue
				var vedro: Node3D = null
				for d: Dictionary in dv.dily[g]:
					if String(d["e"]["kind"]) == "vedro": vedro = d["uzel"]
				var c: Vector3 = vedro.get_parent().global_position
				cam.look_at_from_position(c + Vector3(1.3, 2.3, 1.5), c + Vector3(0, 0.7, 0), Vector3.UP)
				dv.prepni(g)
				await get_tree().create_timer(float(dv.doba[g]) + 1.0).timeout
		"zlab":
			for p: Dictionary in fu.polozky_:
				if p["druh"] != "zlab": continue
				var dum: Node3D = p["dum"]; var ab: AABB = p["aabb"]
				var c := ab.get_center()
				cam.look_at_from_position(dum.global_transform * Vector3(c.x + 0.4, ab.end.y + 1.0, c.z + 1.6), dum.global_transform * Vector3(c.x - 0.3, ab.end.y - 0.15, c.z), Vector3.UP)
				fu.nalij(p)
				var vm: MeshInstance3D = p["voda"]
				if OS.get_environment("PUCHART_CERVENA") != "": var cm := StandardMaterial3D.new(); cm.albedo_color = Color.RED; cm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; vm.material_override = cm
				print("VODA ", vm.global_transform * vm.mesh.get_aabb().position, " ", vm.global_transform * vm.mesh.get_aabb().end, " mat ", vm.material_override, " vis ", vm.is_visible_in_tree(), " cam ", cam.global_position, " pov ", vm.mesh.get_faces().size())
				await get_tree().create_timer(1.0).timeout
				break
	for i in 10: await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(png)
	print("FOTO_FUNKCE ", co, " ", png)
	get_tree().quit()
