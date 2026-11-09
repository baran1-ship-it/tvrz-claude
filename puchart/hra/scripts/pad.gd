extends Node
## Herní ovladač (Xbox) podle Havrana (scripts/pad.gd, Míša 3. 11.): levá páčka chůze (stisk = běh do zastavení), pravá
## rozhled, A použít (vrata, dveře), B létání, Start nabídka (pauza, menu.gd), kříž dolů menu hráče (mapa, místa, deník),
## kříž nahoru mapa, LB/RB při létání dolů/nahoru. Když je otevřená nabídka nebo menu hráče, ovladač obslouží ona.
var proch: Node        # prochazka.gd (nabídka, menu hráče, mapa, dveře)
var hrac: Node

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS

func _input(e: InputEvent) -> void:
	if not (e is InputEventJoypadButton) or not e.pressed: return
	if proch.menu.visible or proch.menu_hrace.open: return   # menu.gd / menu_hrace.gd mají vlastní ovládání
	var b := (e as InputEventJoypadButton).button_index
	match b:
		JOY_BUTTON_START, JOY_BUTTON_BACK:
			proch.otevri_nabidku()
		JOY_BUTTON_DPAD_DOWN:
			proch.otevri_menu_hrace()
		JOY_BUTTON_A:
			proch.pouzij()
		JOY_BUTTON_B:
			hrac.prepni_let()
		JOY_BUTTON_DPAD_UP:
			proch.mapa.prepni()
		JOY_BUTTON_LEFT_STICK:
			hrac.bezi = true; hrac._beh_packa = true
	get_viewport().set_input_as_handled()
