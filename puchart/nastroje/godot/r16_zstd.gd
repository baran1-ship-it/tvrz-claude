extends SceneTree
## vysek.r16 -> vysek.r16z: roviny horních a dolních bajtů zvlášť, zstd (Godot FileAccess.open_compressed).
## Celé r16 se zstd zmenší jen 8,0 -> 7,7 MB (dolní bajty = šum); horní rovina se zmenší ~100×.
## Hra čte obě roviny a výšku skládá až v _v() – bez průchodu přes 4 M hodnot při startu.
func _initialize() -> void:
	var b := FileAccess.get_file_as_bytes("res://data/vysek.r16")
	var n := b.size() / 2
	var hi := PackedByteArray(); hi.resize(n)
	var lo := PackedByteArray(); lo.resize(n)
	for i in n:
		lo[i] = b[2 * i]; hi[i] = b[2 * i + 1]
	var f := FileAccess.open_compressed("res://data/vysek.r16z", FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
	f.store_buffer(hi); f.store_buffer(lo); f.close()
	print("r16z ", b.size(), " -> ", FileAccess.get_file_as_bytes("res://data/vysek.r16z").size())
	quit()
