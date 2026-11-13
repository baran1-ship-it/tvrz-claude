extends SceneTree
## Izolovane mereni ceny prepoctu oblohy (13. 11., podezreni: daylight._apply meni parametry oblohy kazdych 0,25 s, Sky
## PROCESS_MODE_QUALITY = prepocet radiance mapy; Puchart bez sekani meni oblohu jen pri znatelne zmene). Stejne nastaveni
## oblohy jako daylight.gd (shaders/sky.gdshader, radiance 128, QUALITY), koule s PBR materialem (cte radiance).
## Rezimy: "stoji" (parametry beze zmeny) x "meni" (zenith o kousek kazdy snimek) - prumer a nejdelsi snimek.
## Spusteni: tools/beh.sh obl cmd xvfb-run -a -s "-screen 0 640x400x24" godot --path . --rendering-driver opengl3 \
##   --rendering-method gl_compatibility --resolution 640x400 -s res://tools/mereni_oblohy.gd
## llvmpipe = jen pomer rezimu, ne cisla tabletu.


func _initialize() -> void:
	_beh.call_deferred()


func _beh() -> void:
	var koren := Node3D.new()
	root.add_child(koren)
	var we := WorldEnvironment.new()
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/sky.gdshader") if ResourceLoader.exists("res://shaders/sky.gdshader") else null
	sky.sky_material = sm if sm.shader else ProceduralSkyMaterial.new()
	sky.radiance_size = Sky.RADIANCE_SIZE_128
	sky.process_mode = Sky.PROCESS_MODE_QUALITY
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	we.environment = env
	koren.add_child(we)
	var cam := Camera3D.new()
	koren.add_child(cam)
	cam.position = Vector3(0, 1, 4)
	var k := MeshInstance3D.new()
	k.mesh = SphereMesh.new()
	var mat := StandardMaterial3D.new()
	mat.roughness = 0.3
	mat.metallic = 0.5
	k.material_override = mat
	koren.add_child(k)
	for _i in 30:
		await process_frame
	var vysl := {}
	for kolo in 2:
		for rez in ["stoji", "meni"]:
			var t_max := 0.0
			var t0 := Time.get_ticks_usec()
			var t := t0
			for i in 90:
				if rez == "meni":
					var c := Color(0.13 + 0.01 * sin(i * 0.3), 0.31, 0.66)
					if sm.shader:
						sm.set_shader_parameter("zenith", c)
					else:
						(sky.sky_material as ProceduralSkyMaterial).sky_top_color = c
				await process_frame
				var t2 := Time.get_ticks_usec()
				t_max = maxf(t_max, (t2 - t) / 1000.0)
				t = t2
			var pr := float(Time.get_ticks_usec() - t0) / 90.0 / 1000.0
			var a: Array = vysl.get(rez, [INF, INF])
			vysl[rez] = [minf(a[0], pr), minf(a[1], t_max)]
	print("MERENI_OBLOHY shader %s: %s ([prumer ms, nejdelsi ms], mensi ze 2 kol; llvmpipe - jen pomer)" % [sm.shader != null, str(vysl)])
	quit()
