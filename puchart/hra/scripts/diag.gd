extends CanvasLayer
## Panel měření (PDF kap. 13, Havran diag.gd): skutečná délka snímku z razítek (ne vyhlazené delta – Havran: „nejdelší“
## lhalo), p95 za posledních 300 snímků, záseky > 40 ms, kreslení, trojúhelníky, paměť. Nedostupné = N/A, ne 0.

var lbl: Label
var casy := PackedFloat32Array()
var _posledni := 0
var zaseky := 0
var sestava := ""

func _ready() -> void:
	lbl = Label.new()
	lbl.position = Vector2(12, 8)
	lbl.add_theme_font_size_override("font_size", 18)
	lbl.add_theme_color_override("font_outline_color", Color.BLACK)
	lbl.add_theme_constant_override("outline_size", 4)
	add_child(lbl)
	_posledni = Time.get_ticks_usec()
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	if FileAccess.file_exists("res://data/sestava.json"):
		sestava = JSON.parse_string(FileAccess.get_file_as_string("res://data/sestava.json")).get("commit", "")

func _process(_d: float) -> void:
	var t := Time.get_ticks_usec()
	var ms := (t - _posledni) / 1000.0
	_posledni = t
	casy.append(ms)
	if casy.size() > 300:
		casy = casy.slice(casy.size() - 300)
	if ms > 40.0 and Engine.get_frames_drawn() > 60:
		zaseky += 1
	if Engine.get_frames_drawn() % 15 != 0:
		return
	var s := casy.duplicate(); s.sort()
	var p95 := s[int(s.size() * 0.95)] if s.size() > 20 else -1.0
	var kres := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
	var troj := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
	var vram := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED)
	var halda := OS.get_static_memory_usage()
	var vp := get_viewport(); var rid := vp.get_viewport_rid()
	var vel := vp.get_visible_rect().size; var sc := vp.scaling_3d_scale
	var gpu := RenderingServer.viewport_get_measured_render_time_gpu(rid); var cpu := RenderingServer.viewport_get_measured_render_time_cpu(rid)
	lbl.text = "FPS %d  p95 %s ms  záseky>40 ms %d\nkreslení %d  troj. %.2f M\nVRAM %d MB  halda(debug) %s\nokno %dx%d  3D %d%% = %dx%d  GPU %s CPU %s ms  %s" % [
		Engine.get_frames_per_second(), ("%.1f" % p95) if p95 >= 0 else "N/A", zaseky,
		kres, troj / 1e6, vram / 1048576, ("%d MB" % (halda / 1048576)) if halda > 0 else "N/A",
		vel.x, vel.y, roundi(sc * 100), roundi(vel.x * sc), roundi(vel.y * sc),
		("%.1f" % gpu) if gpu > 0.0 else "N/A", ("%.1f" % cpu) if cpu > 0.0 else "N/A", sestava]
