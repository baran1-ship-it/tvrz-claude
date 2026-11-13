extends SceneTree
## Mereni uderu (reference Misa 13. 11. docs/reference/kcd_13_11 kovarna: kladivo ma dopadnout na kus na kovadline):
## postava kovare z dat, cinnost kovani, klip buseni po 1/48 cyklu; hlava kladiva (horni cast predmetu) v soustave
## postavy (x bok, y vyska, z dopredu). Vypise nejnizsi bod (okamzik uderu) a fazi.
## Spusteni: tools/beh.sh uder cmd godot --headless --path . -s res://tools/mereni_uderu.gd
##   TVRZ_UDER="kdo;cinnost;klip;ruka;predmet" (vychozi kovar;kovani;Prace_Kovar_Buseni_Loop;r;kladivo)

const Lide := preload("res://scripts/lide.gd")


func _initialize() -> void:
	_beh.call_deferred()


func _beh() -> void:
	var a := (OS.get_environment("TVRZ_UDER") if OS.has_environment("TVRZ_UDER") else "kovar;kovani;Prace_Kovar_Buseni_Loop;r;kladivo").split(";")
	var koren := Node3D.new()
	root.add_child(koren)
	var lide: Node3D = Lide.new()
	koren.add_child(lide)
	var P: Dictionary = Lide.P
	var o: Dictionary = (P["obyvatele"] as Array).filter(func(x: Dictionary) -> bool: return String(x["id"]) == a[0])[0]
	var c: Dictionary = lide.nova_postava(o)
	var u: Node3D = c["uzel"]
	u.scale = Vector3.ONE
	c["cn"] = P["cinnosti"][a[1]]
	c["klip"] = ""
	lide.call("_klip", c, a[2], 1.0)
	var ap: AnimationPlayer = c["ap"]
	# hlava predmetu v jeho soustave: stred vrcholu v hornich 6 cm
	var ps: PackedScene = load("res://modely/predmety/%s.glb" % a[4])
	var t: Node3D = ps.instantiate()
	root.add_child(t)
	var vs: Array = []
	var ymax := -INF
	for mi: Node in t.find_children("*", "MeshInstance3D", true, false):
		var m := (mi as MeshInstance3D).mesh
		var tr := (mi as MeshInstance3D).global_transform
		for si in m.get_surface_count():
			for v: Vector3 in m.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
				vs.append(tr * v)
				ymax = maxf(ymax, (tr * v).y)
	var hl := Vector3.ZERO
	var n := 0
	for w: Vector3 in vs:
		if w.y > ymax - 0.06:
			hl += w
			n += 1
	hl /= maxf(n, 1)
	t.queue_free()
	print("UDER hlava %s v predmetu %s" % [a[4], hl])
	var dl := ap.get_animation(a[2]).length
	var nej := Vector3(0, INF, 0)
	var nej_f := 0.0
	for i in 48:
		ap.stop()
		ap.play(a[2], 0.0)
		ap.seek(dl * i / 48.0, true)
		ap.advance(0.0)
		await process_frame
		await process_frame
		var uz: Node3D = (c["ruce"] as Dictionary).get(a[3] + "_uzel")
		if uz == null:
			continue
		var w := u.global_transform.affine_inverse() * (uz.global_transform * hl)
		if w.y < nej.y:
			nej = w
			nej_f = float(i) / 48.0
	print("UDER %s %s: nejnize hlava %s (x bok, y vyska, z dopredu) ve fazi %.2f, delka klipu %.2f s" % [a[0], a[2], nej.snapped(Vector3.ONE * 0.01), nej_f, dl])
	quit()
