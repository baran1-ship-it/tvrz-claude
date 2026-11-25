# Kůň Hero Horse v2.0 (Míša 25. 11.: „co bys řekl na tohoto koníka… placené, je to moje… udělej to“)

Zdroj: Disk složka 1GVCyUx5FwSUDUGoSYD6Md1WbeymqUqY9 – `CH_Hero_Horse.v.2.0_LIGHT.rar` (FBX/DAE, TIF 4K, .max),
`UNR_HorseForHeroes_v.2.0.rar` (Unreal projekt, animace .uasset – mimo Unreal nečitelné; jen Docs a 3DMAX rig),
zbroje `Hell_Armor`, `Poor_Armor`. Placený balík Míši („Horse for Heroes“), stažení `curl drive.usercontent … confirm=t`,
rozbalení `bsdtar` (apt libarchive-tools), TIF s alfou `tifffile` (PIL/Blender bez okna alfu ani data nečtou).

Model (notes.rtf): tělo 11 566 troj. (LOD 4 502), lehká zbroj 16 270, Hell 18 806, Poor 19 356 (LOD 11 212); kostra
Biped 40–41 kostí (`horse Pelvis`, `horse Spine`…`Spine2`, `horse Neck`…`Neck3`, `horse Head`, `horse Jaw`, nohy
`horse L/R Thigh/Calf/HorseLink/Foot/Toe0`, přední `Clavicle/UpperArm/Forearm/Hand/Finger0`, `horse Tail`…`Tail2`,
`horse HORSEMAN_BONE`, `stirrup_left/right`, `bone_reins`); textury 5 srstí (Bay, Black, Chestnut, Palomino, White),
4 hřívy, normály, specular. Sedlo chudé zbroje = moderní anglické → ve hře dobové sedlo Balt (jizda.json kun.vystroj).

Animace – jedna stopa „Take 001“, 30 FPS, snímky (Hero_Horse_notes.rtf, Unreal Docs):
0 T-pose; Idle_A 2–100; Idle_B 101–201; bite 201–241; kick 242–268; looking_around 269–394; rear_up 395–480;
sniff 481–541; eating 546–646; kick_ground 651–685; death 690–716; M_galloping 721–736; M_jump 737–772;
M_galloping_turn_left 773–788; M_galloping_turn_right 793–808; M_running_death 813–853; M_swim 858–892; M_trot 897–921;
M_trot_turn_left 922–946; M_trot_turn_right 951–975; M_walk 980–1014; M_walk_turn_Left 1015–1049;
M_walk_turn_right 1054–1088; M_walk_back 1093–1127; RM_* (root motion) 1132–1554. Otočka = 24°.

Postup: `python3 tools/kun_hero_tex.py <rozbaleno>` (PNG do modely/kone/kun_hero_tex), pak
`/opt/bl/bin/python tools/kun_hero.py <rozbaleno> Bay Brown` → modely/kone/kun_hero.glb (tělo, hříva, ocas, PA_Harness
= uzdečka s poprsníkem; sedlo/deka/třmeny/otěže/sukně postroje pryč), `godot --import`. Pravidla jizda.json kun
(model, klipy_z_useku, kosti, otezi.uzdecka_sit PA_Harness, zivy.kosti, kosti_vzory); původní kůň v kun.henry.
