

## Louka v bodech (Misa 0.994 potok ve vsi (489, 895): holy zeleny obdelnik bez travy): hustota a podminky na mrizce.
func _louka_bod() -> void:
	var lk = main.louka
	var v := OS.get_environment("TVRZ_CO").split_floats(",") if OS.has_environment("TVRZ_CO") else PackedFloat64Array([480.0, 860.0, 540.0, 905.0])
	var z := float(v[1])
	while z <= float(v[3]):
		var radek := ""
		var x := float(v[0])
		while x <= float(v[2]):
			var s: Vector3 = lk._vzorek(x, z)
			var proc := ""
			if main.svet.v_zahrade(x, z):
				proc += "Z"
			if main.svet.v_nove_zahrade(x, z) == 2:
				proc += "N"
			if main.svet.v_pruchodu(x, z):
				proc += "P"
			if main.svet.od_vody(x, z) < 1.5:
				proc += "V"
			if lk._v_budove(x, z):
				proc += "B"
			radek += " %3d%-2s" % [roundi(s.x * 100.0), proc]
			x += 4.0
		print("LOUKA z %4.0f:%s" % [z, radek])
		z += 4.0
	_vysledek("louka_bod", true, "vypis mrizky")
