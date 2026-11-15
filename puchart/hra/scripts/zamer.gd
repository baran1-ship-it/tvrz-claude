extends RefCounted
## Zaměření interakcí (Míša 15. 11.: „vše, co je interaktivní, na to musí být umístěn kurzor“, „nemůžu lézt po žebříku,
## který je uvnitř, zvenku“). Havran life.usable: nabídne se jen to, na co míří střed obrazovky (směr pohledu · směr k cíli
## ≥ min_cos), vybírá se nejmenší kolmá vzdálenost od paprsku pohledu (blízkost jen mírně); navíc paprsek z očí k cíli nesmí
## narazit dřív než tolerance_m před cílem (zeď mezi hráčem a žebříkem / dveřmi). Čísla pravidla/svet/hrac.json zamer.
const Pravidla := preload("res://scripts/pravidla.gd")

## Skóre cíle (menší = lepší) nebo −1, když na něj hráč nemíří nebo ho nevidí. vlastni = RID kolizí, které cíl tvoří
## (křídlo dveří) – paprsek je přeskočí.
static func skore(cam: Camera3D, cil: Vector3, dosah: float, vlastni: Array = []) -> float:
	if cam == null: return -1.0
	var z: Dictionary = Pravidla.cti("hrac", "zamer")
	var oko := cam.global_position; var to := cil - oko; var d := to.length()
	if d > dosah: return -1.0
	var fwd := -cam.global_transform.basis.z
	if d > float(z["bez_miru_m"]) and fwd.dot(to / d) < float(z["min_cos"]): return -1.0
	var q := PhysicsRayQueryParameters3D.create(oko, cil); q.exclude = vlastni; q.collide_with_areas = false
	var hrac := cam.get_parent()
	while hrac != null and not hrac is CharacterBody3D: hrac = hrac.get_parent()
	if hrac: q.exclude = vlastni + [(hrac as CollisionObject3D).get_rid()]
	var h := cam.get_world_3d().direct_space_state.intersect_ray(q)
	if not h.is_empty() and oko.distance_to(h["position"]) < d - float(z["tolerance_m"]): return -1.0
	var perp := (to - fwd * maxf(to.dot(fwd), 0.0)).length()
	return perp + d * float(z["vaha_vzdalenosti"])
