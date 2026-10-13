extends Node
## Herni data (modely, textury) jsou mimo APK: datovy balik .pck rozdeleny na casti pod 95 MB v repozitari.
## Pri prvnim spusteni (a po nove verzi dat) se stahne do user://, spoji, overi a nacte.
## V editoru a pri testech jsou data primo v projektu, nic se nestahuje.

signal status(text: String)

const MANIFEST := "res://data_manifest.json"
const BASE := "https://raw.githubusercontent.com/baran1-ship-it/tvrz-claude/claude/new-session-0dtk58/data/"


func ensure() -> bool:
	if FileAccess.file_exists("res://modely/svet.json"):
		return true
	var mf := FileAccess.open(MANIFEST, FileAccess.READ)
	if mf == null:
		status.emit("Chybí popis herních dat")
		return false
	var man: Dictionary = JSON.parse_string(mf.get_as_text())
	var id: String = man["id"]
	var dst := "user://data_%s.pck" % id
	if not (FileAccess.file_exists(dst) and _size(dst) == int(man["size"])):
		if not await _download(man, dst):
			return false
	_cleanup(dst)
	if not ProjectSettings.load_resource_pack(dst):
		status.emit("Herní data nejdou načíst")
		DirAccess.remove_absolute(dst)
		return false
	return FileAccess.file_exists("res://modely/svet.json")


func _size(path: String) -> int:
	var f := FileAccess.open(path, FileAccess.READ)
	return f.get_length() if f else -1


func _download(man: Dictionary, dst: String) -> bool:
	var parts: Array = man["parts"]
	var total := float(man["size"])
	var done := 0.0
	var http := HTTPRequest.new()
	http.use_threads = true
	http.download_chunk_size = 1 << 20
	add_child(http)
	for i in parts.size():
		var p: Dictionary = parts[i]
		var tmp := "user://data_cast_%d.tmp" % i
		# uz stazena cast z minuleho (prerusenoho) pokusu
		if _size(tmp) == int(p["size"]) and FileAccess.get_md5(tmp) == String(p["md5"]):
			done += float(p["size"])
			continue
		var ok := false
		for attempt in 4:
			http.download_file = tmp
			var res := []
			http.request_completed.connect(func(r: int, code: int, _h: PackedStringArray, _b: PackedByteArray) -> void:
				res.append_array([r, code]), CONNECT_ONE_SHOT)
			var base := OS.get_environment("TVRZ_DATA_URL") if OS.has_environment("TVRZ_DATA_URL") else BASE
			if http.request(base + String(man["id"]) + "/" + String(p["name"])) != OK:
				await get_tree().create_timer(2.0).timeout
				continue
			while res.is_empty():
				var got := done + float(http.get_downloaded_bytes())
				status.emit("Stahuji herní data… %d %%  (%.0f / %.0f MB)" % [int(100.0 * got / total), got / 1048576.0, total / 1048576.0])
				await get_tree().create_timer(0.25).timeout
			if int(res[0]) == HTTPRequest.RESULT_SUCCESS and int(res[1]) == 200 and _size(tmp) == int(p["size"]) and FileAccess.get_md5(tmp) == String(p["md5"]):
				ok = true
				break
			status.emit("Stahování se nepovedlo, zkouším znovu…")
			await get_tree().create_timer(2.0 * (attempt + 1)).timeout
		if not ok:
			status.emit("Herní data se nepodařilo stáhnout. Zkontroluj internet a spusť hru znovu.")
			return false
		done += float(p["size"])
	# spojit casti do jednoho baliku
	status.emit("Skládám herní data…")
	await get_tree().process_frame
	var out := FileAccess.open(dst, FileAccess.WRITE)
	for i in parts.size():
		var tmp := "user://data_cast_%d.tmp" % i
		var f := FileAccess.open(tmp, FileAccess.READ)
		while f.get_position() < f.get_length():
			out.store_buffer(f.get_buffer(8 << 20))
		f = null
		DirAccess.remove_absolute(tmp)
	out = null
	http.queue_free()
	return _size(dst) == int(man["size"])


func _cleanup(keep: String) -> void:
	# stare verze dat smazat (setri misto v tabletu)
	var d := DirAccess.open("user://")
	if d == null:
		return
	for f in d.get_files():
		if f.begins_with("data_") and f.ends_with(".pck") and "user://" + f != keep:
			d.remove(f)
