extends Node
## Herni data (modely, textury) jsou mimo APK: samostatne baliky .pck (svet a kazdy predmet zvlast),
## velke rozdelene na casti pod 95 MB. Stahuji se jen baliky, ktere v tabletu jeste nejsou (po aktualizaci
## jen zmenene), ulozi se do user://data, overi md5 a nactou. Ulozene hry se nemazou.
## V editoru a pri testech jsou data primo v projektu, nic se nestahuje.

signal status(text: String)

const MANIFEST := "res://data_manifest.json"
const BASE := "https://raw.githubusercontent.com/baran1-ship-it/tvrz-claude/claude/new-session-0dtk58/data/"
const DIR := "user://data"


func ensure() -> bool:
	if FileAccess.file_exists("res://modely/svet.json"):
		return true
	var mf := FileAccess.open(MANIFEST, FileAccess.READ)
	if mf == null:
		status.emit("Chybí popis herních dat")
		return false
	var man: Dictionary = JSON.parse_string(mf.get_as_text())
	var packs: Dictionary = man["packs"]
	DirAccess.make_dir_recursive_absolute(DIR)
	# co chybi
	var need: Array = []
	var total := 0.0
	for name: String in packs:
		var pk: Dictionary = packs[name]
		if not (FileAccess.file_exists(_path(name, pk)) and _size(_path(name, pk)) == int(pk["size"])):
			need.append(name)
			total += float(pk["size"])
	if not need.is_empty():
		status.emit("Stahuji herní data… (%.0f MB)" % (total / 1048576.0))
		var done := [0.0]
		for name: String in need:
			if not await _download(name, packs[name], done, total):
				return false
	_cleanup(packs)
	status.emit("Načítám herní data…")
	await get_tree().process_frame
	# svet prvni (katalog predmetu), pak predmety
	var order: Array = packs.keys()
	order.sort_custom(func(a: String, b: String) -> bool: return a == "svet" and b != "svet")
	for name: String in order:
		# bez prepisovani: spolecne soubory (seznam UID, project.binary) plati z APK, ne ze starsich baliku
		if not ProjectSettings.load_resource_pack(_path(name, packs[name]), false):
			status.emit("Herní data nejdou načíst, stáhnu je znovu při dalším spuštění")
			DirAccess.remove_absolute(_path(name, packs[name]))
			return false
	return FileAccess.file_exists("res://modely/svet.json")


func _path(name: String, pk: Dictionary) -> String:
	return "%s/%s-%s.pck" % [DIR, name, String(pk["md5"]).substr(0, 10)]


func _size(path: String) -> int:
	var f := FileAccess.open(path, FileAccess.READ)
	return f.get_length() if f else -1


func _download(name: String, pk: Dictionary, done: Array, total: float) -> bool:
	var parts: Array = pk["parts"]
	var http := HTTPRequest.new()
	http.use_threads = true
	http.download_chunk_size = 1 << 20
	add_child(http)
	var base := OS.get_environment("TVRZ_DATA_URL") if OS.has_environment("TVRZ_DATA_URL") else BASE
	for i in parts.size():
		var p: Dictionary = parts[i]
		var tmp := "%s/cast_%s_%d.tmp" % [DIR, name, i]
		if _size(tmp) == int(p["size"]) and FileAccess.get_md5(tmp) == String(p["md5"]):
			done[0] += float(p["size"])
			continue
		var ok := false
		for attempt in 4:
			http.download_file = tmp
			var res := []
			http.request_completed.connect(func(r: int, code: int, _h: PackedStringArray, _b: PackedByteArray) -> void:
				res.append_array([r, code]), CONNECT_ONE_SHOT)
			var err := http.request(base + String(p["file"]))
			if err != OK:
				status.emit("Stahování nejde spustit (chyba %d), zkouším znovu…" % err)
				await get_tree().create_timer(2.0).timeout
				continue
			while res.is_empty():
				var got: float = done[0] + float(http.get_downloaded_bytes())
				status.emit("Stahuji herní data… %d %%  (%.0f / %.0f MB)" % [int(100.0 * got / maxf(total, 1.0)), got / 1048576.0, total / 1048576.0])
				await get_tree().create_timer(0.25).timeout
			if int(res[0]) == HTTPRequest.RESULT_SUCCESS and int(res[1]) == 200 and _size(tmp) == int(p["size"]) and FileAccess.get_md5(tmp) == String(p["md5"]):
				ok = true
				break
			status.emit("Stahování se nepovedlo (chyba %s / %s), zkouším znovu…" % [res[0] if res.size() > 0 else "?", res[1] if res.size() > 1 else "?"])
			await get_tree().create_timer(2.0 * (attempt + 1)).timeout
		if not ok:
			status.emit("Herní data se nepodařilo stáhnout. Zkontroluj internet a spusť hru znovu.")
			http.queue_free()
			return false
		done[0] += float(p["size"])
	# spojit casti do baliku
	var dst := _path(name, pk)
	var out := FileAccess.open(dst, FileAccess.WRITE)
	for i in parts.size():
		var tmp := "%s/cast_%s_%d.tmp" % [DIR, name, i]
		var f := FileAccess.open(tmp, FileAccess.READ)
		while f.get_position() < f.get_length():
			out.store_buffer(f.get_buffer(8 << 20))
		f = null
		DirAccess.remove_absolute(tmp)
	out = null
	http.queue_free()
	return _size(dst) == int(pk["size"])


func _cleanup(packs: Dictionary) -> void:
	# stare verze baliku a data z drivejsich verzi hry smazat (setri misto); ulozene hry zustavaji
	var keep := {}
	for name: String in packs:
		keep[_path(name, packs[name]).get_file()] = true
	var d := DirAccess.open(DIR)
	if d:
		for f in d.get_files():
			if f.ends_with(".pck") and not keep.has(f):
				d.remove(f)
	var u := DirAccess.open("user://")
	if u:
		for f in u.get_files():
			if f.begins_with("data_") and (f.ends_with(".pck") or f.ends_with(".tmp")):
				u.remove(f)
