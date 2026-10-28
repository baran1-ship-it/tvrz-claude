extends RefCounted
## Knihovna animaci Quaternius Universal Animation Library 1 + 2 (CC0, kostra 65 kosti jako postavy kitu) pro libovolnou
## kostru: stopy klipu prepsane na cestu ke kostre od korene prehravace. Jedna knihovna na cestu (sdilena vsemi
## postavami se stejnou stavbou uzlu - tablet: klipy v pameti jednou). Pouziva telo hrace (telo.gd) i postavy (lide.gd).

const ANIM := ["res://modely/postavy/anim/UAL1.glb", "res://modely/postavy/anim/UAL2.glb"]
static var _cache := {}


static func knihovna(cesta: String) -> AnimationLibrary:
	if _cache.has(cesta):
		return _cache[cesta]
	var lib := AnimationLibrary.new()
	for f: String in ANIM:
		var ps: PackedScene = load(f)
		if ps == null:
			continue
		var s := ps.instantiate()
		for a in s.find_children("*", "AnimationPlayer", true, false):
			var p := a as AnimationPlayer
			for ln in p.get_animation_library_list():
				var l := p.get_animation_library(ln)
				for an in l.get_animation_list():
					var anim := (l.get_animation(an) as Animation).duplicate(true) as Animation
					for ti in anim.get_track_count():
						var tp := anim.track_get_path(ti)
						if tp.get_subname_count() > 0:
							anim.track_set_path(ti, NodePath(cesta + ":" + tp.get_concatenated_subnames()))
					var jm := String(an).trim_suffix("_Armature")
					# importer Godotu klipum *_Loop priponu odrizne a nastavi smycku (Idle_Loop -> Idle); jmena v kodu
					# jsou podle knihovny UAL - bez tohoto se klip nenasel a telo stalo v T-poze (snimek 27. 10.)
					if anim.loop_mode != Animation.LOOP_NONE and not jm.ends_with("_Loop"):
						jm += "_Loop"
					if jm.ends_with("_Loop"):
						anim.loop_mode = Animation.LOOP_LINEAR
					lib.add_animation(jm, anim)
		s.free()
	_cache[cesta] = lib
	return lib
