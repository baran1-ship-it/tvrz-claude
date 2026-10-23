# Modely od Míši – průchod `nove._import_sketchup`

Funkce (blender/nove.py): sloučení vrcholů 1 mm, normály ven, materiály podle klíčového slova na herní
fotografické materiály (UV v metrech), ostatní glb materiály bez lesku (drsnost 0,9, kov jen u kovu),
rovinná decimace 1°, strop trojúhelníků, textury ≤ 1024 (předměty 512). Ve hře svet.gd přiřadí herní
materiály podle názvu i statickým stavbám.

| Model | Soubor | Troj. před → po | Textury před → po | Materiály → herní |
|---|---|---|---|---|
| hostinec | stazene/medieval_tavern_interior.glb | 9 292 → 8 598 (stavba jen rovinné slučování; collapse na 4 000 zúžil dveře) | 8×, max 1024 → max 1024 | RoofTilesWood → sindel_hra, Wood → dub_ven, LogEdgeWeathered → drevo_rez; StoneWall (zdivo_hostinec), DarkStone, Brick, Sign, RustedMetal z glb bez lesku |

## Disk – stav 23. 10. 2026 21:40 (rádce)
- **Postavy/**: `Universal Base Characters[Standard].zip` (Quaternius CC0), `Modular Character Outfits - Fantasy[Standard].zip` (Quaternius CC0 – dobovou vhodnost každého kusu posoudit, „Fantasy“ je jen název balíku), `makehuman_system_assets_cc0.zip` (280 MB). **Chybí:** Quaternius *Universal Animation Library 1 + 2* (Standard, CC0) – klipy idle/chůze/běh/sezení/práce, kompatibilní s Base Characters → stáhnout pro POSTAVY.
- **horse.glb** (55 MB, 22. 10.): ověřit, zda má kostru a animace; velikost napovídá fotosken bez rigu → model pro stáj; pro jízdu (FUNKCE) rigovaný kůň (Quaternius Animals CC0).
- **Keře**: `bush.glb`, `tall_bush.glb`, `3d_bush_-_01.glb` (51 MB fotosken) – 23. 10. ráno, v 0.71.
- **Zvěř**: nic – Quaternius Animals pack (CC0, s animacemi) až ve FUNKCI/POSTAVÁCH.
- **Universal Animation Library 1 + 2 [Standard]** (23. 10. 21:24, Míša stáhl; nahrát do Disk/Postavy): CC0, `UAL1_Standard.glb` + `UAL2_Standard.glb` (bez root motion) a `_RM.glb` (s root motion), 66 kostí = rig Base Characters, 43 + 43 klipů. **Použitelné:**
  - život: Idle_Loop, Idle_Talking_Loop, Idle_FoldArms_Loop, Idle_Torch_Loop, Idle_Lantern_Loop, Walk_Loop, Walk_Formal_Loop, Walk_Carry_Loop, Jog_Fwd_Loop, Sprint_Loop, Crouch_Idle/Fwd, Sitting_Enter/Idle_Loop/Talking_Loop/Exit, PickUp_Table, Interact, Chest_Open, Consume, Yes, Idle_No_Loop, LayToIdle
  - práce: Farm_Harvest (srp – žně), Farm_PlantSeed, Farm_Watering, TreeChopping_Loop (dřevo, lom, kovadlina s jiným nástrojem), Fixing_Kneeling, Push_Loop
  - boj/obležení: Sword_Idle/Attack/Block/Regular_A/B/C/Heavy_Combo/Dash, Shield_Loop/Break/OneShot/Dash, Hit_Chest/Head/Knockback, Death01, Roll, Punch_Jab/Cross (zápas), Melee_Hook, OverhandThrow
  - hráč (FUNKCE): Jump_Start/Loop/Land, ClimbUp_1m, Swim_Idle_Loop/Swim_Fwd_Loop (brody, plavání), Slide
  - **nepoužít**: Pistol_*, Spell_*, Zombie_*, Driving, TalkingPhone, Dance, NinjaJump
  - chybí: jízda na koni, zametání, kosa (Farm_Harvest = srp, pro 1393 správně), kovář u kovadliny (náhrada TreeChopping).
  Postup (Astra 21:15): jeden rig, klipy přímo bez retargetu (stejné kosti), AnimationTree Idle/Move/Work/Sit/React, první verze bez root motion.
