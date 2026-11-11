"""Pracovni animace z CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu, volne pro jakekoli pouziti)
prenesene na kostru Quaternius UAL (stejna kostra jako postavy) -> modely/postavy/anim/UAL_prace.glb.
Mixamo (Misa 5. 11. povolila) bez prihlaseni nejde stahnout (API: 403 "Api Key is required"), proto CMU.
BVH: github.com/una-dinosauria/cmu-mocap (data/0SS/SS_KK.bvh, prevod cgspeed).
  /opt/bl/bin/python -I tools/postavy_q/anim_cmu.py <slozka_bvh> [vystup.glb]
Prenos: smer kazde kosti jako ve zdroji (rotace svetova vuci klidu, srovnani klidovych smeru kosti), panev posun
v meritku delky nohou, bez driftu (jen kmitani kolem mista), stredni natoceni dopredu; smycky prolnute na konci.
Prsty: uchop z klipu UAL Sword_Idle (prava ruka; leva zrcadlove), kdyz klip drzi nastroj.
"""
import bpy, sys, os, math, numpy as np
from mathutils import Quaternion, Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
BVH = args[0]; OUT = args[1] if len(args) > 1 else os.path.join(REPO, "modely/postavy/anim/UAL_prace.glb")
FPS = 30
# jmeno klipu (pripona _Loop = smycka), soubor CMU, zacatek s, delka s, uchop (r, lr, "")
CLIPS = [
    ("Prace_Zametani_Loop", "13_23", 6.0, 5.0, "lr"),     # zametani (koste)
    # Misa 9. 11. r. 83 (kovar „ma krec“): 62_07 je zatloukani hrebiku v predklonu (ruka se hybe o 5 cm, hlava 0,36 m
    # pred panvi) - ne kovani. 79_01 „chopping wood“: uder obema rukama shora dolu na spalek = mlatec s perlikem u kovadliny
    ("Prace_Kovar_Loop", "79_01", 2.25, 1.2, "lr"),       # uder perlikem shora (kovar u kovadliny)
    # Misa 0.99993 r. 48 (krumpac obourucne) a test_drzeni: TreeChopping_Loop (UAL) je sek JEDNOU rukou - ruce 0,94-1,23 m
    # od sebe, leva paze (0,55 m) na topurko nedosahne. Obourucni uder shora (prvni uder 79_01) pro krumpac a sekeru.
    ("Prace_Uder_Loop", "79_01", 0.45, 1.2, "lr"),        # uder obema rukama (krumpac v lomu, sekera na spalku)
    # Misa 10. 11. (varianta B, svizna chuze hrace 2,3 m/s): UAL Walk_Loop / Walk_Formal_Loop jdou 0,98 m/s - nohy by
    # kluzaly o 134 %. Hledano: UAL1/UAL2 (jen Walk, Walk_Formal, Walk_Carry, Jog_Fwd, Sprint), CMU index
    # (brisk walk 07_12, 81_04, 82_12, Walk Fast 132_17-22): nejrychlejsi chuze 07_12 „brisk walk“ 1,82 m/s (median panve).
    ("Prace_Pila_Loop", "62_03", 2.5, 4.0, "r"),          # rezani pilou
    ("Prace_Uklid_Loop", "62_11", 4.0, 6.0, "lr"),        # uklizeni, prenaseni veci
    ("Prace_Sbirani_Loop", "02_06", 0.5, 6.0, "r"),       # predklon, nabrat ze zeme, vstat (sber, prace u zeme)
    ("Piti", "13_09", 1.0, 6.0, "r"),                     # napit se (dzban, korbel)
    ("Piti_Unavene", "62_12", 0.5, 7.0, "r"),             # „hard day's drink" (hostinec)
    ("Hovor_Gesta_Loop", "18_08", 3.0, 8.0, ""),          # vysvetlovani rukama
    ("Hovor_Gesta2_Loop", "19_08", 3.0, 8.0, ""),         # druhy z dvojice
    ("Ceka_Loop", "40_10", 10.0, 8.0, ""),                # postavani, prešlapování (straz, cekani)
    ("Mavani", "13_26", 0.8, 4.0, ""),                    # mavani, ukazovani
    ("Otocka", "69_18", 0.5, 3.0, ""),                    # otoceni na miste
    # Mixamo (zdroj .fbx, zacatek 0, delka None = cely klip, prsty z klipu)
    ("Chuze_Mix_Loop", "Walking.fbx", 0.0, None, ""),           # chuze hrace (svizna)
    ("Chuze_Mix1_Loop", "Walking_1.fbx", 0.0, None, ""),
    ("Spanek_Lezmo_Loop", "Laying_Sleeping.fbx", 0.0, None, ""), # spanek vleze (r. 59/85)
    # Misa 10. 11. r. 100 (stojici rozkroceni - UAL Idle_Loop; chuze jako pochod - UAL Walk_Loop): stani a chuze postav
    ("Stani_Loop", "Idle.fbx", 0.0, None, ""),
    ("Stani_Dech_Loop", "Breathing_Idle.fbx", 0.0, None, ""),
    ("Stani_Stary_Loop", "Old_Man_Idle.fbx", 0.0, None, ""),
    ("Stani_Presun_Loop", "gesta/weight_shift.fbx", 0.0, None, ""),
    ("Chuze_Std_Loop", "Standard_Walk.fbx", 0.0, None, ""),
    ("Chuze_Mix3_Loop", "Walking_3.fbx", 0.0, None, ""),
    ("Chuze_Mix4_Loop", "Walking_4.fbx", 0.0, None, ""),
    ("Chuze_Mix5_Loop", "Walking_5.fbx", 0.0, None, ""),
    # r. 95 kovar: jednorucni uder kladivem (prava ruka drzi kladivo - uchop prstu z UAL Sword_Idle)
    ("Kovar_Bash_Loop", "Bash.fbx", 0.0, None, "r"),
    ("Kovar_Swing_Loop", "Heavy_Weapon_Swing.fbx", 0.0, None, "r"),
    # Misa 10. 11. (Hammering na Mixamo neni): buseni = vyrez Mixamo Bash_1 (prava ruka od pasu sn. ~22 k hlave ~46 a
    # dolu k pasu ~58, leva niz - jednorucni uder shora), snimky 25-64, smycka prolnuta do zvedani
    ("Prace_Kovar_Buseni_Loop", "Bash_1.fbx", 0.8, 1.3, "r"),
    ("Kovar_Silny", "Standing_Melee_Attack_Downward.fbx", 0.0, None, "r"),   # silny uder (nad hlavu sn. 22, dolu 28)
    # r. 96/99 hostinec: piti vsedě a sed (panev srovnana na UAL Sitting_Idle_Loop - SED_VZOR, data sedani.vyska_klipu_m)
    # 10. 11. snimek fmix4/piti_bok: prevod Sitting_Drinking stoji nad sedakem (neni sed) - piti vsedě je slepene (SLEP)
    ("Sed_Loop", "Male_Sitting_Pose.fbx", 0.0, None, ""),
    # Misa 10. 11. (hostinec: obsluha nosi hostum, hoste vykladaji): chuze s nosenim, hovor vestoje (Mixamo)
    ("Chuze_Nese_Loop", "Carrying.fbx", 0.0, None, "r"),
    ("Hovor_Mix_Loop", "Talking.fbx", 0.0, None, ""),
    ("Hovor_Mix1_Loop", "Talking_1.fbx", 0.0, None, ""),
    # Misa 10. 11. (hostinsky jako v KCD: mezi obsluhou opreny o zed, pozoruje lokal)
    ("Opreny_Loop", "Leaning.fbx", 0.0, None, ""),
    # Misa 10. 11.: prechody sedu (vstup/vystup na sedak - panev konce / zacatku srovnana na SED_VZOR) a vstavani z kleku
    ("Sed_Vstup", "Stand_To_Sit.fbx", 0.0, None, ""),
    ("Sed_Vystup", "Sit_To_Stand.fbx", 0.0, None, ""),
    ("Vstava", "Standing_Up.fbx", 0.0, None, ""),
    # Misa 10. 11. zahon: kleknuti -> pleti vkleče -> vstavani
    ("Klekne", "Kneeling_Down.fbx", 0.0, None, ""),
    # 10. 11. snimek fmix3/vstava: Standing_Up vstava z lehu na zemi (sedi s natazenyma nohama), ne z kleku ->
    # vstavani z kleku = Kneeling_Down pozpatku (POZPATKU)
    ("Vstava_Z_Kleku", "Kneeling_Down.fbx", 0.0, None, ""),
    ("Kleci_Loop", "Kneeling.fbx", 0.0, None, ""),
    ("Pleti_Loop", "Pull_Plant.fbx", 0.0, None, ""),
    ("Seje2", "Dig_And_Plant_Seeds_1.fbx", 0.0, None, ""),
    # Misa 10. 11. sed: varianty sedu (kazda postava svou, obcas zmeni) - panev srovnana na SED_VZOR (jmeno Sed_*)
    ("Sed_Poza_Loop", "Sitting.fbx", 0.0, None, ""),
    ("Sed_Poza1_Loop", "Sitting_1.fbx", 0.0, None, ""),
    ("Sed_Poza2_Loop", "Sitting_2.fbx", 0.0, None, ""),
    ("Sed_Poza3_Loop", "Sitting_3.fbx", 0.0, None, ""),
    ("Sed_Klid_Loop", "Sitting_Idle.fbx", 0.0, None, ""),
    ("Sed_Klid1_Loop", "Sitting_Idle_1.fbx", 0.0, None, ""),
    ("Sed_Piti1_Loop", "Sitting_Drinking_1.fbx", 0.0, None, "r"),
    # Misa 10. 11.: protazeni po praci a rano, mavani (pozdrav), kyvnuti „pojd sem“, probuzeni na luzku
    ("Protazeni", "Arm_Stretching.fbx", 0.0, None, ""),
    ("Protazeni_Krk", "Neck_Stretching.fbx", 0.0, None, ""),
    ("Mava", "Waving.fbx", 0.0, None, ""),
    ("Kyva_Pojd", "Beckoning.fbx", 0.0, None, ""),
    ("Probouzi", "Waking.fbx", 0.0, None, ""),
    ("Kostky", "Checking_Dice.fbx", 0.0, None, ""),          # hra v kostky (vsedě slepena se sedem: Sed_Kostky_Loop)
    # 10. 11. hra v kostky po tazich (Misa): ceka, trese, hodi, odkryje, ukazuje - vsechny vsedě slepene se sedem
    ("Kostky_Ceka", "Dice_Idle.fbx", 0.0, None, ""),
    ("Kostky_Trese", "Shaking_Dice.fbx", 0.0, None, ""),
    ("Kostky_Hodi", "Throwing_Dice.fbx", 0.0, None, ""),
    ("Kostky_Odkryje", "Revealing_Dice.fbx", 0.0, None, ""),
    ("Ukazuje", "Pointing.fbx", 0.0, None, ""),
    # mlynari: nosi pytel (holding_walk = chuze s nakladem, box_idle = stoji s nakladem)
    ("Chuze_Pytel_Loop", "farma/holding_walk.fbx", 0.0, None, "lr"),
    ("Pytel_Stoji_Loop", "farma/box_idle.fbx", 0.0, None, "lr"),
    # spanek vleze (varianty) - vyska na luzku viz postavy.json spani
    ("Spanek_Lezmo1_Loop", "Sleeping_Idle.fbx", 0.0, None, ""),
    ("Spanek_Lezmo2_Loop", "Sleeping_Idle_1.fbx", 0.0, None, ""),
    ("Spanek_Lezmo3_Loop", "Sleeping_Idle_2.fbx", 0.0, None, ""),
    # Misa 10. 11. (zivot jako v KCD, docs/rozpracovane/kcd_zivot_postav.md): mikro-animace uvnitr cinnosti (jednorazove)
    ("Rozhlizi", "Look_Around.fbx", 0.0, None, ""),
    ("Rozhlizi2", "Looking_Around.fbx", 0.0, None, ""),
    ("Napiti", "Drinking.fbx", 0.0, None, "r"),
    ("Zvedne", "Picking_Up.fbx", 0.0, None, ""),
    ("Truhla_Otevri", "Opening_A_Lid.fbx", 0.0, None, ""),
    ("Truhla_Zavri", "Closing_A_Lid.fbx", 0.0, None, ""),
    ("Hodi", "Throw_Object.fbx", 0.0, None, ""),
    ("Krici", "Yelling.fbx", 0.0, None, ""),
    ("Hleda_Loop", "Looking_Through_Files_Low.fbx", 0.0, None, ""),
    ("Kope_Loop", "Digging.fbx", 0.0, None, "lr"),
    ("Seje", "Dig_And_Plant_Seeds.fbx", 0.0, None, ""),
    ("Trha_Ovoce", "Pick_Fruit.fbx", 0.0, None, ""),
    ("Trha_Ovoce2", "Pick_Fruit_1.fbx", 0.0, None, ""),
    ("Farma_Zalevani", "farma/watering.fbx", 0.0, None, "r"),
    ("Farma_Vytrhava", "farma/pull_plant.fbx", 0.0, None, ""),
    ("Farma_Vytrhava2", "farma/pull_plant_2.fbx", 0.0, None, ""),
    ("Farma_Sadi", "farma/plant_a_plant.fbx", 0.0, None, ""),
    ("Farma_Klece_Loop", "farma/kneeling_idle.fbx", 0.0, None, ""),
    ("Farma_Trha", "farma/pick_fruit_2.fbx", 0.0, None, ""),
    ("Nese_Stoji_Loop", "farma/holding_idle.fbx", 0.0, None, "r"),
    # Misa 11. 11. (natazena ruka u stolu = ukazovani do prazdna): polozit / vzit predmet, sed s vykladanim, otevreni
    # dveri, ukrok, otocka s louci; Action Adventure Pack: otocky na miste (misto smyku pri otaceni), stani, skok hrace
    ("Polozi", "akce/Putting_Down.fbx", 0.0, None, "r"),
    ("Vezme", "akce/Picking_Up_1.fbx", 0.0, None, "r"),
    ("Sed_Vyklada_Loop", "akce/Sitting_Talking.fbx", 0.0, None, ""),
    ("Otevre_Dvere", "akce/Opening.fbx", 0.0, None, "r"),
    ("Ukrok_Vpravo_Loop", "akce/Right_Strafe_Walking.fbx", 0.0, None, ""),
    ("Louc_Otocka", "akce/Standing_Torch_Turn_Left_180.fbx", 0.0, None, "r"),
    ("Otocka_Vlevo", "akce/aap_left_turn.fbx", 0.0, None, ""),
    ("Otocka_Vpravo", "akce/aap_right_turn.fbx", 0.0, None, ""),
    ("Stani_A1_Loop", "akce/aap_idle.fbx", 0.0, None, ""),
    ("Stani_A2_Loop", "akce/aap_idle__2.fbx", 0.0, None, ""),
    ("Stani_A3_Loop", "akce/aap_idle__3.fbx", 0.0, None, ""),
    ("Stani_A4_Loop", "akce/aap_idle__4.fbx", 0.0, None, ""),
    ("Stani_A5_Loop", "akce/aap_idle__5.fbx", 0.0, None, ""),
    ("Hrac_Skok", "akce/aap_jumping_up.fbx", 0.0, None, ""),
    ("Hrac_Pad_Loop", "akce/aap_falling_idle.fbx", 0.0, None, ""),
    ("Hrac_Dopad", "akce/aap_hard_landing.fbx", 0.0, None, ""),
    ("Beh_Zastavi", "akce/aap_run_to_stop.fbx", 0.0, None, ""),
] + [("Gesto_" + g, "gesta/" + g + ".fbx", 0.0, None, "") for g in (
    "acknowledging", "angry_gesture", "annoyed_head_shake", "being_cocky", "dismissing_gesture", "happy_hand_gesture",
    "hard_head_nod", "head_nod_yes", "lengthy_head_nod", "look_away_gesture", "relieved_sigh", "sarcastic_head_nod",
    "shaking_head_no", "thoughtful_head_shake")]
# slepene klipy: horni pulka tela (pater, ruce, hlava) z prvniho klipu, panev a nohy z druheho (sed) - vykladani vsedě
# 10. 11. snimek fmix4: Male_Sitting_Pose (Sed_Loop) je rozvaleny zaklon -> spodek ze Sitting_Idle (Sed_Klid_Loop, vzpřímeny)
SLEP = [("Sed_Hovor_Loop", "Hovor_Mix_Loop", "Sed_Klid_Loop"), ("Sed_Hovor1_Loop", "Hovor_Mix1_Loop", "Sed_Klid_Loop"),
        ("Sed_Jidlo_Loop", "Ual_Consume", "Sed_Klid_Loop"), ("Sed_Kostky_Loop", "Kostky", "Sed_Klid_Loop"),
        ("Sed_Piti_Loop", "Napiti", "Sed_Klid_Loop"),
        ("Sed_Kostky_Ceka_Loop", "Kostky_Ceka", "Sed_Klid_Loop"), ("Sed_Kostky_Trese", "Kostky_Trese", "Sed_Klid_Loop"),
        ("Sed_Kostky_Hodi", "Kostky_Hodi", "Sed_Klid_Loop"), ("Sed_Kostky_Odkryje", "Kostky_Odkryje", "Sed_Klid_Loop"),
        ("Sed_Ukazuje", "Ukazuje", "Sed_Klid_Loop"), ("Sed_Raduje", "Gesto_happy_hand_gesture", "Sed_Klid_Loop"),
        ("Sed_Zlobi", "Gesto_angry_gesture", "Sed_Klid_Loop"), ("Sed_Vrti", "Gesto_annoyed_head_shake", "Sed_Klid_Loop")]          # jidlo vsedě: UAL2 Consume (ji vestoje) + sed
# klipy UAL ponechane jen jako zdroj slepeni (UAL1.glb nese i klipy UAL2? ne - Consume je v UAL2.glb, nacte se zvlast)
UAL_ZDROJ = {"Consume": "Ual_Consume", "LayToIdle": "Ual_LayToIdle"}
# vzor lehu (postavy.json spani.nad_postel_m je ladene na UAL LayToIdle v case 0): klipy spanku (jmeno Spanek_*) se
# natoci a posunou tak, aby panev v prvnim snimku byla jako panev LayToIdle v case 0
LEH_VZOR = "Ual_LayToIdle"
# 10. 11. snimek fmix3/hovor_sed: s panvi sedu a patri horniho klipu (stani) byl trup zakloneny ~30 st - spodni pater
# (spine_01, spine_02) taky ze sedu, horni klip jen hrudnik, ruce, krk a hlava
DOLNI = {"root", "pelvis", "spine_01", "spine_02"} | {f"{b}_{t}" for b in ("thigh", "calf", "foot", "ball") for t in ("l", "r")}
# klipy vsedě (jmeno Sed_*): stredni poloha panve = jako v UAL Sitting_Idle_Loop, aby platila jedna vyska sedaku
# (postavy.json sedani.vyska_klipu_m) - Mixamo sed je nahrany na jine zidli (vyska panve z klidove pozy nesedi)
SED_VZOR = "Sitting_Idle_Loop"
POZPATKU = {"Vstava_Z_Kleku"}
MAP = {"Hips": "pelvis", "LowerBack": "spine_01", "Spine": "spine_02", "Spine1": "spine_03", "Neck": "neck_01", "Head": "Head"}
for s, t in (("Left", "l"), ("Right", "r")):
    MAP.update({f"{s}Shoulder": f"clavicle_{t}", f"{s}Arm": f"upperarm_{t}", f"{s}ForeArm": f"lowerarm_{t}", f"{s}Hand": f"hand_{t}",
                f"{s}UpLeg": f"thigh_{t}", f"{s}Leg": f"calf_{t}", f"{s}Foot": f"foot_{t}", f"{s}ToeBase": f"ball_{t}"})
PRSTY = ("index", "middle", "ring", "pinky", "thumb")
# Mixamo (Misa 10. 11.: „na internetu to urcite je“ - FBX z mixamo.com, tools/postavy_q/mixamo, 30 fps, na miste)
MIX = os.path.join(HERE, "mixamo")
MAPM = {"mixamorig:Hips": "pelvis", "mixamorig:Spine": "spine_01", "mixamorig:Spine1": "spine_02", "mixamorig:Spine2": "spine_03",
        "mixamorig:Neck": "neck_01", "mixamorig:Head": "Head"}
for s_, t in (("Left", "l"), ("Right", "r")):
    MAPM.update({f"mixamorig:{s_}Shoulder": f"clavicle_{t}", f"mixamorig:{s_}Arm": f"upperarm_{t}",
                 f"mixamorig:{s_}ForeArm": f"lowerarm_{t}", f"mixamorig:{s_}Hand": f"hand_{t}",
                 f"mixamorig:{s_}UpLeg": f"thigh_{t}", f"mixamorig:{s_}Leg": f"calf_{t}", f"mixamorig:{s_}Foot": f"foot_{t}",
                 f"mixamorig:{s_}ToeBase": f"ball_{t}"})
    for pr in PRSTY:
        for i in (1, 2, 3):
            MAPM[f"mixamorig:{s_}Hand{pr.capitalize()}{i}"] = f"{pr}_0{i}_{t}"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, "modely/postavy/anim/UAL1.glb"))
T = next(o for o in bpy.data.objects if o.type == "ARMATURE")
for o in [o for o in bpy.data.objects if o.type == "MESH"]: bpy.data.objects.remove(o)
# uchop prstu z klipu UAL (lokalni rotace kosti prstu prave ruky v 1. snimku)
grip = {}
ga = bpy.data.actions.get("Sword_Idle_Armature")
if ga:
    for fc in ga.fcurves:
        dp = fc.data_path
        if 'pose.bones["' in dp and dp.endswith("rotation_quaternion"):
            bn = dp.split('"')[1]
            if bn.endswith("_r") and bn.startswith(PRSTY):
                grip.setdefault(bn, [1, 0, 0, 0])[fc.array_index] = fc.evaluate(ga.frame_range[0])
print("UCHOP kosti", len(grip))
# vzor sedu: stredni poloha panve (svet) v UAL klipu SED_VZOR minus klidova poloha
sed_d = None
sa = bpy.data.actions.get(SED_VZOR + "_Armature") or bpy.data.actions.get(SED_VZOR)
if sa:
    T.animation_data_create(); T.animation_data.use_nla = False; T.animation_data.action = sa
    pz = []
    for f in range(int(sa.frame_range[0]), int(sa.frame_range[1]) + 1):
        bpy.context.scene.frame_set(f); pz.append((T.matrix_world @ T.pose.bones["pelvis"].head) - (T.matrix_world @ T.data.bones["pelvis"].head_local))
    sed_d = sum(pz, Vector()) / len(pz)
    T.animation_data.action = None; T.animation_data.use_nla = True
print("SED_VZOR", SED_VZOR, sed_d)
if T.animation_data:
    T.animation_data.action = None
    for tr in list(T.animation_data.nla_tracks): T.animation_data.nla_tracks.remove(tr)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
# zdroje slepeni z UAL2 (stejna kostra): akce nacist, prejmenovat, objekty pryc
_pred = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, "modely/postavy/anim/UAL2.glb"))
for a in list(bpy.data.actions):
    zk = a.name.split("_Armature")[0]
    if zk in UAL_ZDROJ: a.name = UAL_ZDROJ[zk]; a.use_fake_user = True
    else: bpy.data.actions.remove(a)
for o in [o for o in bpy.data.objects if o not in _pred]: bpy.data.objects.remove(o)
leh_q = leh_d = None
la = bpy.data.actions.get(LEH_VZOR)
if la:
    T.animation_data_create(); T.animation_data.use_nla = False; T.animation_data.action = la
    bpy.context.scene.frame_set(int(la.frame_range[0]))
    pb = T.pose.bones["pelvis"]
    leh_q = (T.matrix_world @ pb.matrix).to_quaternion() @ T.data.bones["pelvis"].matrix_local.to_quaternion().inverted()
    leh_d = (T.matrix_world @ pb.head) - (T.matrix_world @ T.data.bones["pelvis"].head_local)
    T.animation_data.action = None; T.animation_data.use_nla = True
    bpy.data.actions.remove(la)
print("LEH_VZOR", leh_q, leh_d)
TB = [b for b in T.data.bones]
order = []
def walk(b):
    order.append(b.name)
    for c in b.children: walk(c)
for b in TB:
    if b.parent is None: walk(b)
Qr = {b.name: b.matrix_local.to_quaternion() for b in TB}
dirT = {b.name: (b.tail_local - b.head_local).normalized() for b in TB}
par = {b.name: (b.parent.name if b.parent else None) for b in TB}
H_T = T.data.bones["pelvis"].head_local.z
for pb in T.pose.bones: pb.rotation_mode = 'QUATERNION'
FWD = Vector((0, -1, 0))

def nacti(cid):
    if cid.endswith(".fbx"):
        for o in [o for o in bpy.data.objects if o is not T]: bpy.data.objects.remove(o)
        bpy.ops.import_scene.fbx(filepath=os.path.join(MIX, cid), automatic_bone_orientation=False)
        return next(o for o in bpy.context.selected_objects if o.type == "ARMATURE")
    s3 = cid.split("_")[0].zfill(3)
    p = os.path.join(BVH, f"{cid}.bvh")
    for o in [o for o in bpy.data.objects if o is not T]: bpy.data.objects.remove(o)
    bpy.ops.import_anim.bvh(filepath=p, axis_forward='-Z', axis_up='Y', global_scale=1.0, update_scene_fps=False, update_scene_duration=False)
    return bpy.context.object

def prenes(name, cid, t0, dl, uchop):
    S = nacti(cid)
    act_s = S.animation_data.action
    n_src = int(act_s.frame_range[1])
    mix = cid.endswith(".fbx")
    MP = MAPM if mix else MAP
    src_fps = 30 if mix else 120
    if dl is None:
        dl = (n_src - 1) / src_fps
    QsR = {b.name: b.matrix_local.to_quaternion() for b in S.data.bones}
    A = {}
    for sb, tb in MP.items():
        b = S.data.bones[sb]; ds = (b.tail_local - b.head_local).normalized()
        A[tb] = ds.rotation_difference(dirT[tb])
    step = src_fps // FPS
    loop = name.endswith("_Loop") and (not mix or t0 > 0)   # Mixamo cely klip: smycka hotova; vyrez (t0 > 0) prolnout
    K = int(0.4 * FPS) if loop else 0
    f0 = max(1, int(t0 * src_fps) - K * step)
    f1 = min(n_src + (1 if mix else 0), int((t0 + dl + (0 if mix else 1.5)) * src_fps) + (1 if mix else 0))
    frames = list(range(f0, f1, step))
    sc = bpy.context.scene
    Ds, Ps = [], []
    for f in frames:
        sc.frame_set(f)
        D = {}
        for sb, tb in MP.items():
            q = (S.matrix_world @ S.pose.bones[sb].matrix).to_quaternion()
            D[tb] = q @ QsR[sb].inverted() @ A[tb].inverted()
        Ds.append(D); Ps.append(S.matrix_world @ S.pose.bones["mixamorig:Hips" if mix else "Hips"].head)
    P = np.array([p[:] for p in Ps])
    # meritko podle vysky panve ve stoji (90. percentil celeho klipu), drift pryc (klouzavy prumer 1,5 s)
    zs = []
    for f in range(1, n_src, max(1, src_fps // 4)):
        sc.frame_set(f); zs.append((S.matrix_world @ S.pose.bones["mixamorig:Hips" if mix else "Hips"].head).z)
    zst = float(np.percentile(zs, 90)); k = H_T / zst
    if mix:
        # Mixamo: meritko a vyska z klidove pozy (lezeni/sed: 90. percentil klipu = pánev u zeme -> postava visela 0,9 m
        # nad zemi, snimek build/fmix/Spanek_Lezmo 10. 11.)
        zst = (S.matrix_world @ S.data.bones["mixamorig:Hips"].head_local).z; k = H_T / zst
    w = int(1.5 * FPS) | 1
    ker = np.ones(w) / w
    sm = np.stack([np.convolve(np.pad(P[:, i], (w // 2, w // 2), mode="edge"), ker, mode="valid") for i in (0, 1)], 1)
    if name.startswith("Chuze"):
        # chuze: posun panve = stala rychlost -> odecist primku (klouzavy prumer 1,5 s pri cyklu ~1 s nechal v panvi
        # cast posunu: 10. 11. test_klipy_chuze Chuze_Svizna_Loop spicky z -1,07..0,45 m, opora 5 %, 0,26 m/s)
        t = np.arange(len(P))
        sm = np.stack([np.polyval(np.polyfit(t, P[:, i], 1), t) for i in (0, 1)], 1)
    # stredni natoceni panve -> dopredu (-Y)
    yaws = []
    for D in Ds:
        v = D["pelvis"] @ FWD; yaws.append(math.atan2(v.y, v.x))
    my = math.atan2(np.mean(np.sin(yaws)), np.mean(np.cos(yaws)))
    Cy = Quaternion((0, 0, 1), math.atan2(FWD.y, FWD.x) - my)
    if name.startswith("Spanek_") and leh_q is not None:
        Cy = leh_q @ Ds[K]["pelvis"].inverted()          # lezici: panev prvniho snimku jako LayToIdle (cele natoceni)
    # sed: posun panve tak, aby stredni poloha byla jako u SED_VZOR (svet, po natoceni Cy)
    sed_posun = Vector()
    if name.startswith("Spanek_") and leh_d is not None:
        d0 = Cy @ Vector(((P[K, 0] - sm[K, 0]) * k, (P[K, 1] - sm[K, 1]) * k, (P[K, 2] - zst) * k))
        sed_posun = leh_d - d0
        print("LEH", name, "posun panve", tuple(round(x, 3) for x in sed_posun))
    if name.startswith("Sed_") and sed_d is not None:
        ds_ = [Cy @ Vector(((P[i, 0] - sm[i, 0]) * k, (P[i, 1] - sm[i, 1]) * k, (P[i, 2] - zst) * k)) for i in range(len(P))]
        sed_posun = sed_d - sum(ds_, Vector()) / len(ds_)
        if name == "Sed_Vstup": sed_posun = sed_d - ds_[-1]      # prechod: sedi az na konci
        if name == "Sed_Vystup": sed_posun = sed_d - ds_[0]      # prechod: sedi na zacatku
        print("SED", name, "posun panve", tuple(round(x, 3) for x in sed_posun))
    # mistni rotace vsech kosti cile
    L = []
    for i, D in enumerate(Ds):
        Dall = {}
        loc = {}
        for bn in order:
            if bn in D: Dall[bn] = (Cy @ D[bn]) if True else D[bn]
            else: Dall[bn] = Dall[par[bn]] if par[bn] else Quaternion()
        fr = {}
        for bn in order:
            Dp = Dall[par[bn]] if par[bn] else Quaternion()
            fr[bn] = Qr[bn].inverted() @ Dp.inverted() @ Dall[bn] @ Qr[bn]
        d = Vector(((P[i, 0] - sm[i, 0]) * k, (P[i, 1] - sm[i, 1]) * k, (P[i, 2] - zst) * k))
        d = Cy @ d + sed_posun
        fr["_loc"] = Qr["pelvis"].inverted() @ d
        if uchop:
            for bn, q in grip.items():
                fr[bn] = Quaternion(q)
                if "l" in uchop and uchop != "r": fr[bn[:-2] + "_l"] = Quaternion(q)
        L.append(fr)
    # smycka: konec vybrat tak, aby se poza co nejvic shodovala se zacatkem, a prolnout
    i0 = K
    nlen = int(dl * FPS)
    if loop:
        def dist(a, b): return sum(1 - abs(L[a][bn].dot(L[b][bn])) for bn in MP.values())
        cand = range(i0 + max(FPS, nlen - FPS), min(len(L) - 1, i0 + nlen + FPS))
        iend = min(cand, key=lambda j: dist(j, i0)) if len(cand) else min(len(L) - 1, i0 + nlen)
        if mix:
            iend = min(len(L) - 1, i0 + nlen)          # vyrez Mixamo: presne zadana delka, konec prolnut do zacatku
        for j in range(K):
            wgt = (j + 1) / (K + 1)
            a, b = L[iend - K + j], L[i0 - K + j]
            for bn in a:
                if bn == "_loc": a[bn] = a[bn].lerp(b[bn], wgt)
                else: a[bn] = a[bn].slerp(b[bn], wgt)
        seq = L[i0:iend]
    else:
        seq = L[i0:i0 + nlen]
    if name in POZPATKU:
        seq = seq[::-1]
    act = bpy.data.actions.new(name)
    for bn in order:
        prev = None
        vals = []
        for fr in seq:
            q = fr.get(bn, Quaternion())
            if prev is not None and q.dot(prev) < 0: q = -q
            prev = q; vals.append(q)
        for c in range(4):
            fc = act.fcurves.new(f'pose.bones["{bn}"].rotation_quaternion', index=c, action_group=bn)
            fc.keyframe_points.add(len(vals))
            co = np.zeros(len(vals) * 2, np.float32); co[0::2] = np.arange(len(vals)); co[1::2] = [v[c] for v in vals]
            fc.keyframe_points.foreach_set("co", co); fc.update()
    for c in range(3):
        fc = act.fcurves.new('pose.bones["pelvis"].location', index=c, action_group="pelvis")
        fc.keyframe_points.add(len(seq))
        co = np.zeros(len(seq) * 2, np.float32); co[0::2] = np.arange(len(seq)); co[1::2] = [fr["_loc"][c] for fr in seq]
        fc.keyframe_points.foreach_set("co", co); fc.update()
    act.use_fake_user = True
    T.animation_data_create()
    tr = T.animation_data.nla_tracks.new(); tr.name = name
    tr.strips.new(name, 0, act)
    bpy.data.actions.remove(act_s)
    print("KLIP", name, cid, "snimku", len(seq), "smycka" if loop else "", "meritko %.4f" % k)
    sys.stdout.flush()

for c in CLIPS:
    try: prenes(*c)
    except Exception as e: print("CHYBA", c[0], e); sys.stdout.flush()
for jm, ah, ad in SLEP:
    A_h, A_d = bpy.data.actions.get(ah), bpy.data.actions.get(ad)
    if not (A_h and A_d):
        print("CHYBA slep", jm); continue
    act = bpy.data.actions.new(jm)
    h0, h1 = int(A_h.frame_range[0]), int(A_h.frame_range[1])
    d0, d1 = int(A_d.frame_range[0]), int(A_d.frame_range[1])
    n = h1 - h0 + 1
    for fc in A_h.fcurves:
        bn = fc.data_path.split('"')[1]
        src, dolni = fc, False
        if bn in DOLNI:
            s2 = A_d.fcurves.find(fc.data_path, index=fc.array_index)
            if s2 is not None: src, dolni = s2, True
        nf = act.fcurves.new(fc.data_path, index=fc.array_index, action_group=bn)
        nf.keyframe_points.add(n)
        co = np.zeros(n * 2, np.float32); co[0::2] = np.arange(n)
        co[1::2] = [src.evaluate(d0 + (i % (d1 - d0 + 1)) if dolni else h0 + i) for i in range(n)]
        nf.keyframe_points.foreach_set("co", co); nf.update()
    # panev (poloha) jen ze sedu, i kdyz ji horni klip nema
    for c in range(3):
        dp = 'pose.bones["pelvis"].location'
        if act.fcurves.find(dp, index=c) is None and A_d.fcurves.find(dp, index=c) is not None:
            s2 = A_d.fcurves.find(dp, index=c)
            nf = act.fcurves.new(dp, index=c, action_group="pelvis"); nf.keyframe_points.add(n)
            co = np.zeros(n * 2, np.float32); co[0::2] = np.arange(n); co[1::2] = [s2.evaluate(d0) for i in range(n)]
            nf.keyframe_points.foreach_set("co", co); nf.update()
    act.use_fake_user = True
    tr = T.animation_data.nla_tracks.new(); tr.name = jm
    tr.strips.new(jm, 0, act)
    print("KLIP", jm, "slepeno", ah, "+", ad)
for zd in UAL_ZDROJ.values():
    if bpy.data.actions.get(zd): bpy.data.actions.remove(bpy.data.actions[zd])
for o in [o for o in bpy.data.objects if o is not T]: bpy.data.objects.remove(o)
bpy.context.scene.render.fps = FPS
T.animation_data.action = None
bpy.ops.object.select_all(action="DESELECT"); T.select_set(True); bpy.context.view_layer.objects.active = T
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_animations=True,
                          export_animation_mode="ACTIONS", export_force_sampling=True, export_skins=True, export_def_bones=False)
print("ANIM", OUT, [a.name for a in bpy.data.actions])
sys.stdout.flush(); os._exit(0)
