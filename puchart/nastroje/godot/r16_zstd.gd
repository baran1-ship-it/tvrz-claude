extends SceneTree
## vysek.r16 -> vysek.r16z: roviny horních a dolních bajtů zvlášť, zstd (Godot FileAccess.open_compressed).
## Celé r16 se zstd zmenší jen 8,0 -> 7,7 MB (dolní bajty = šum); horní rovina se zmenší ~100×.
## Hra čte obě roviny a výšku skládá až v _v() – bez průchodu přes 4 M hodnot při startu.
func _initialize() -> void:
	for jm in ["vysek", "vysek_sit"]:   # vysek_sit = viditelná síť (snížená pod jemným pásem koryta, teren_dlazdice.py)
		if not FileAccess.file_exists("res://data/%s.r16" % jm): continue
		var b := FileAccess.get_file_as_bytes("res://data/%s.r16" % jm)
		var n := b.size() / 2
		var hi := PackedByteArray(); hi.resize(n)
		var lo := PackedByteArray(); lo.resize(n)
		for i in n:
			lo[i] = b[2 * i]; hi[i] = b[2 * i + 1]
		var f := FileAccess.open_compressed("res://data/%s.r16z" % jm, FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
		f.store_buffer(hi); f.store_buffer(lo); f.close()
		print("r16z ", jm, " ", b.size(), " -> ", FileAccess.get_file_as_bytes("res://data/%s.r16z" % jm).size())
	quit()
