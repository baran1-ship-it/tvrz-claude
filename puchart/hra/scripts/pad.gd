extends Node
## Herní ovladač (Xbox) podle Havrana (scripts/pad.gd, Míša 3. 11.: „ovladač od Xboxu – ovládání dle Havrana“):
## levá páčka chůze (stisk = běh do zastavení), pravá rozhled, A použít (vrata, dveře), B létání / zpět z nabídky,
## Start nabídka (svitky, výběr křížem, A potvrdit), kříž nahoru mapa, LB/RB při létání dolů/nahoru.
var proch: Node        # prochazka.gd (nabídka, mapa, dveře)
var hrac: Node

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS

func _input(e: InputEvent) -> void:
	if not (e is InputEventJoypadButton) or not e.pressed: return
	var b := (e as InputEventJoypadButton).button_index
	var menu: Control = proch.nabidka
	if menu.visible and proch.pad_nabidka:
		match b:
			JOY_BUTTON_B, JOY_BUTTON_START, JOY_BUTTON_BACK:
				proch.zavri_nabidku(); get_viewport().set_input_as_handled()
		return   # kříž a A obslouží fokus nabídky (ui_up/ui_down/ui_accept)
	match b:
		JOY_BUTTON_START, JOY_BUTTON_BACK:
			proch.otevri_nabidku()
		JOY_BUTTON_A:
			proch.pouzij()
		JOY_BUTTON_B:
			hrac.prepni_let()
		JOY_BUTTON_DPAD_UP:
			proch.mapa.prepni()
		JOY_BUTTON_LEFT_STICK:
			hrac.bezi = true; hrac._beh_packa = true
	get_viewport().set_input_as_handled()
