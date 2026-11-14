extends SceneTree
## SVG → PNG (Godot ThorVG; v kontejneru není rsvg). Použití: godot --headless -s svg_png.gd -- vstup.svg vystup.png velikost_px
func _init() -> void:
	var a := OS.get_cmdline_user_args()
	var txt := FileAccess.get_file_as_string(a[0])
	var im := Image.new(); im.load_svg_from_string(txt, 1.0)
	var k := float(a[2]) / im.get_width()
	im = Image.new(); im.load_svg_from_string(txt, k); im.save_png(a[1])
	quit()
