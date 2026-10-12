extends Node
## Jen pro vyvoj: projde seznam pohledu a ulozi snimky. Do exportu se nebali.

var shots: Array = []
var out_dir := ""
var cam: Camera3D
var idx := -1
var wait := 0
var main: Node


func _ready() -> void:
	main = get_parent()
	out_dir = OS.get_environment("TVRZ_SHOTS")
	cam = Camera3D.new()
	cam.fov = 70.0
	cam.far = 2500.0
	main.add_child(cam)
	cam.make_current()
	var f := FileAccess.open(OS.get_environment("TVRZ_SHOTLIST"), FileAccess.READ)
	shots = JSON.parse_string(f.get_as_text())
	_next()


func _next() -> void:
	idx += 1
	if idx >= shots.size():
		print("SHOTS DONE")
		get_tree().quit()
		return
	var s: Dictionary = shots[idx]
	var p: Array = s["pos"]
	var t: Array = s["at"]
	cam.fov = s.get("fov", 70.0)
	cam.look_at_from_position(Vector3(p[0], p[1], p[2]), Vector3(t[0], t[1], t[2]), Vector3.UP)
	if s.has("time") and main.day.current != s["time"]:
		main.day.set_time(s["time"], 0.01)
	if s.has("call"):
		main.call(s["call"])
	wait = int(s.get("frames", 10))


func _process(_dt: float) -> void:
	if idx < 0 or idx >= shots.size():
		return
	wait -= 1
	if wait <= 0:
		var img := get_viewport().get_texture().get_image()
		var path := out_dir.path_join(str(shots[idx]["name"]) + ".png")
		img.save_png(path)
		print("shot ", path)
		_next()
