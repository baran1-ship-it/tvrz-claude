# Rešerše: body předmětů – stání, vstupy, úchopy (27. 11.)

Zadání Míši 27. 11.: „udělej si rešerši, jak se řeší postavy a předměty ve hře – podle mě má vše své body úchopu
a vstupu, a pořádně“. Navazuje na `reserse_animace_postavy_27_11.md` kap. 1 (UE Smart Objects základ, Witcher job
tree, Bethesda směry vstupu, Sims jig/footprint, Horizon, kuchařka) a `uchop_reserse.md` (řešené pózy prstů, testy
2 mm / 5 mm). To se zde **neopakuje**; tady je další úroveň: **jak hry a enginy popisují PŘEDMĚT daty**, aby
postava věděla, kde stát, odkud přijít, kam dát ruce a kam nesmí – a jak se to kontroluje. Cíl: jeden datový
systém pro všechny předměty (kotel nad ohništěm, kovadlina, stůl, truhla, studna, lavice, postel, seno, sudy).

Pravidla čtení: tvrzení „jak to dělají jiní“ má zdroj (URL). Bez zdroje = **odhad** (NEOVĚŘENO, změřit na modelu
/ tabletu dle CLAUDE.md). Mnoho stránek Epic/UESP/EA je za JS nebo 403; kde cituji jen výtah z vyhledávání
oficiální stránky, je URL stejně uvedena. Názvy polí jsou převzaté doslova (angl.), aby šly dohledat.

---

## 1. Jak to dělají hry a enginy

### 1.1 The Sims 2 / 3 / 4 – sloty jako kosti v „rigu“ předmětu
- **Každý předmět má rig (kostru) a SLOT resource; sloty odkazují na kosti rigu.** V TS4 max. 180 kostí v rigu;
  slot bez kosti „funguje jen trochu“ – dekorativní sloty ano, ale **interakce, ke kterým Sim musí dojít (routing),
  nefungují**. Doporučení vývojáře S4S: každý slot = vlastní kost. https://forums.ea.com/discussions/the-sims-4-mods-and-custom-content-en/bone-limit-for-rig-and-slot-resources/2490547
- **Typy slotů (TS2 SLOT resource):** *routing* (kde Sim stojí), *container* (kam se pokládá předmět), *target*
  (jen poloha). Routing slot má: násobitele preference (`Standing Multiplier`, `Sitting Multiplier`),
  `Controller Flags` (8 směrů hledání N..NW, absolutní směry, `snap to directions`, `ignore walls`, `ignore rooms`,
  `random scoring`), `Route Search Parameter` Min/Max/Optimal/Gradient/Spacing (tj. **nejde o bod, ale o pásmo
  vzdáleností s optimem**), `Facing Direction`, `Target Container`; container slot má `Height Type`; slot buď
  na pevné XYZ, nebo na kosti (`Expect Bone Info`). https://db.modthesims.info/wiki.php?title=SLOT
- **TS3:** sloty typu *routing, container, effect, IKtarget*; v editoru (Blender addon) jsou to osy, které se
  posouvají jako objekty; kost se zadává hashem jména; container sloty mají příznaky.
  https://db.modthesims.info/d/456325/blender-2-65-ts3-slot-editor-updated-6-23-17.html
  → **IK cíl ruky je v Sims samostatný typ slotu na předmětu** (ne odvozený za běhu).
- **TS4 pojmenování kostí slotů:** např. `_ctnm_sitIndividual_` číslovaně pro každé místo u herního stolu;
  klip selže, když jmenuje slot, který rig nemá („slot that doesn't exist on the rig has been specified in Maya“).
  https://forums.ea.com/idea/the-sims-4-bug-reports-en/animation-issue-when-playing-cards-on-a-game-table/11979805
- **Části (parts) pro více uživatelů:** pohovka/stůl mají `part_definition` se `subroot_index` → kosti
  `b__subroot__N` v rigu; chybějící subroot = chyba „Unable to find joint b__subroot__0“; části mají
  `adjacent_parts` / `overlapping_parts` (indexy, které sousedí / se překrývají – kdo blokuje koho).
  https://sims4studio.com/thread/36521/converting-counter-height-chairs-working
  https://forums.ea.com/discussions/the-sims-4-mods-and-custom-content-en/adding-seating-positions---adjacent-and-overlapping-tuning-values/910259
  Sekční pohovka má `dynamic_parts`. https://sims4studio.com/thread/27644/add-interaction-sectionalsofapiece
- **Přístup = omezení (constraint), ne bod.** Interakce mají `_constraints`: kruh s ideálním a max. poloměrem,
  natočení (facing), přímá viditelnost; změna kruhu způsobí „animace daleko od předmětu“.
  https://sims4studio.com/thread/22042/sims-object-custom-interaction-tuning
  https://www.patreon.com/zer0_Mods_/posts/tutorial-2-46356734
  Constraints řídí i to, zda dvě interakce smí běžet souběžně (poloha, postura, co drží v ruce) – GDC 2014
  Ingebretson. https://www.slideshare.net/slideshow/concurrent-interactions-in-sims4-by-peter-ingebretson/34106153
  Postura je graf, přechod se hledá Dijkstrou (neověřený bývalý vývojář). https://forums.ea.com/discussions/the-sims-4-general-discussion-en/qa-with-alleged-lead-ai-programmer-for-sims-4/292168/replies/292170
- **Sloty i na těle:** TS4 má „slots“ na povrchu těla; animace ví, ke kterému slotu je ruka nejblíž, a při změně
  postavy (tloušťka) se ruka posune o stejný posun slotu – tj. **ruka se cílí relativně ke slotu, ne absolutně**.
  https://simscommunity.info/2014/08/20/sims-4-create-sim-animation/
- Ladění v S4S: kost+slot = barevný „váleček“, kost bez slotu = růžová pyramida (vizuální kontrola).
  https://sims4studio.com/thread/4420/
- Debug: postava nedošla k předmětu v oblouku → příčina kost `ctnm` uprostřed portálu (slot ve zdi).
  https://sims4studio.com/thread/20095/removing-footprint-having-routing-issues

### 1.2 Unreal Engine 5 – Smart Objects (detail polí)
- Slot (`FSmartObjectSlotDefinition`): poloha+rotace vůči kotvě, vlastní tagy, per-slot `BehaviorDefinitions`
  (jinak `DefaultBehaviorDefinitions` objektu); stavy Free → Claimed (ClaimSmartObject) → Occupied (Use);
  při zrušení objektu `OnSlotInvalidatedDelegate`. https://dev.epicgames.com/documentation/en-us/unreal-engine/smart-objects-in-unreal-engine---overview
  https://docs.unrealengine.com/5.1/en-US/PythonAPI/class/SmartObjectSlotDefinition.html
- **Anotace slotu** (pole `Data` slotu – rozšiřitelné struktury):
  - `SmartObjectSlotEntranceAnnotation` (dříve `…EntryAnnotation`): offset+rotace, `bIsEntry`, `bIsExit`
    (vstup a výstup zvlášť!), `bTraceGroundLocation`, `bCheckTransitionTrajectory`.
    https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SmartObjectSlotEntranceAnnotation
  - `SmartObjectAnnotation_SlotUserCollision`: **kapsle testovaná v místě slotu** (nebo velikost z filtru
    uživatele `bUseUserCapsuleSize`). https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/SmartObjectsModule/FSmartObjectAnnotation_SlotUserC-
  - Link anotace (slot→slot) a debug anotace pro Gameplay Debugger.
    https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/SmartObjectsModule/FSmartObjectAnnotationGameplayDe-
- **Validační filtr** `USmartObjectSlotValidationFilter`: dvě sady parametrů – pro vstup (a obecné kolize) a pro
  výstup; navigační filtr a kapsle uživatele (z nav agenta nebo explicitní). Vstupní kontroly používají kapsli
  filtru, kontrola místa slotu kapsli anotace. https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/SmartObjectsModule/USmartObjectSlotValidationFilter
  https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SmartObjectSlotValidationParams
- Dotaz na vstup: `FindEntranceLocationForSlot` vrací nejlepší validní vstup.
  https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/SmartObjectsModule/USmartObjectSubsystem/FindEntranceLocationForSlot
- Ladění: sloty se v úrovni kreslí až se zapnutou kategorií SmartObject v Gameplay Debuggeru.
  https://issues.unrealengine.com/issue/UE-171598

### 1.3 UE Motion Warping – dorovnání kořene na slot
- V klipu (montáži) je **okno** (`AnimNotifyState_MotionWarping`) se jménem `Warp Target Name`; hra za běhu
  zapíše cíl (`Add or Update Warp Target`) – typicky transform slotu na předmětu. Modifikátor `Skew Warp`
  zkosí kořenový pohyb tak, aby **na konci okna** kořen seděl přesně na cíli; přepínače `Warp Translation`,
  `Ignore ZAxis`, `Warp Rotation`, `Rotation Type` (Default = převzít natočení cíle / Facing = otočit se k cíli),
  `Warp Point Anim Provider` (None/Static/Bone). https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-warping-in-unreal-engine
  https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/RootMotionModifier_Warp
- Pro nás: vstupní klip (dojít + zastavit, sednout) má okno, v němž se kořen „dotáhne“ na slot; mimo okno čistý klip.

### 1.4 UE Contextual Animation Scenes (CAS) – synchronní scéna postava×předmět
- Scéna má role (postava, předmět…), sekce a sady klipů; **warp pointy** (`FContextualAnimWarpPointDefinition`:
  `WarpTargetName`, `Mode` = PrimaryActor / Socket (`SocketName` na primárním aktéru) / Custom) jsou
  referenční transformy pro zarovnání; `GetAlignmentTransform` vrací posun role vůči warp pointu; zarovnávací
  a IK stopy se vzorkují (`sample_rate`) a lze je předpočítat (`precompute_alignment_tracks`).
  https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/ContextualAnimation/FContextualAnimWarpPointDefiniti-
  https://api.unrealengine.com/INT/PythonAPI/class/ContextualAnimWarpPointDefinitionMode.html
  https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ContextualAnimSceneAsset
- **IK cíle ve scéně** (`ContextualAnimIKTargetDefinition`): `goal_name`, `bone_name`, `provider`,
  `target_role_name`, `target_bone_name` (tj. „ruka role A míří na kost/soket role B“); ve verzi 5.0 ještě
  `alpha_curve_name` = **váha IK z křivky klipu**. https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ContextualAnimIKTargetDefinition
  https://docs.unrealengine.com/5.0/en-US/PythonAPI/class/ContextualAnimIKTargetDefinition.html
- Komunita: systém je experimentální, warp point skáče na počátek dveří u klipu bez root motion.
  https://forums.unrealengine.com/t/contextual-animation-warp-point-moves-to-door-origin-when-i-assign-the-door-animation-how-can-i-fix-this/2831513
  → **Lekce: předmět i postava mají společný počátek scény; offset postavy je uložený v klipu vůči tomuto počátku**
  (shodné s Sims a CryEngine „animace odsazená od smart objectu, ten v počátku“, viz 1.9).

### 1.5 Unity – IK cíle na rekvizitách, MatchTarget, Final IK InteractionSystem
- **Animation Rigging Two Bone IK**: `Target` (efektor), `Hint` (směr lokte/kolena), `Weight`,
  `Target Position Weight`, `Target Rotation Weight`, `Hint Weight`.
  https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.0/manual/constraints/TwoBoneIKConstraint.html
- **Mecanim IK**: `OnAnimatorIK` + `SetIKPosition/SetIKPositionWeight`; příklad v dokumentaci čte váhu z parametru
  animátoru „RightHandReach“ (tj. váha z křivky). https://docs.unity3d.com/ScriptReference/Animator.SetIKPositionWeight.html
  https://docs.unity3d.com/Manual/InverseKinematics.html
- **MatchTarget**: `MatchTarget(pos, rot, AvatarTarget, MatchTargetWeightMask, startNormalizedTime,
  targetNormalizedTime)` – kost (např. ruka/noha) dorazí na cíl v daném časovém okně klipu (obdoba warp okna).
  https://docs.unity3d.com/ScriptReference/MatchTargetWeightMask.html
- **Final IK InteractionSystem** (RootMotion): `InteractionObject` = **jak** interakce vypadá (křivky
  `weightCurves`: PositionWeight, RotationWeight, Reach, Pull, PoserWeight; `events` v čase: Pause, Pick Up =
  přivěsit na kost efektoru, jen jedna ruka); `InteractionTarget` = **pózovaná ruka na předmětu pro jeden efektor**
  (`effectorType`, `pivot`, `twistAxis`, `twistWeight`, `swingWeight`, `rotateOnce` – cíl se natočí k postavě);
  `InteractionTrigger` = **odkud** lze interakci spustit (`characterPosition`: `offset`, `maxAngle`, `radius`,
  `orbit` = ze všech stran, `fixYAxis`; `cameraPosition`). http://www.root-motion.com/finalikdox/html/page10.html
  → Přesně Míšovo „body úchopu a vstupu“: úchop = InteractionTarget per ruka, vstup = Trigger range.
- **Meta Interaction SDK**: úchop není jen bod, ale **plocha** – `CylinderGrabSurface` (délka, směr, max. úhel),
  Box/Sphere/Bezier; `HandGrabPose` nese ruku (levá/pravá), pózu prstů a omezení prstů.
  https://developers.meta.com/horizon/documentation/unity/unity-isdk-creating-handgrab-poses
  https://developers.meta.com/horizon/documentation/unity/unity-isdk-hand-grab-interaction/
  → pro násady (vařečka, perlík, vědro) stačí „úsečka úchopu“ (válec) místo jednoho bodu.

### 1.6 Bethesda (Creation Kit) – markery v modelu, klíčová slova v datech
- Markery nábytku jsou v NIF (`BSFurnitureMarkerNode` jako extra data kořene); v CK se k nim přiřadí
  `Marker Keyword` a povolené `Marker Entry Points`. https://ck.uesp.net/wiki/Furniture
  https://forums.nexusmods.com/topic/663641-furniture-marker-in-nifskope
- Pole markeru v NifSkope: `Offset`, `Heading`, `Animation Type` (Sit/Sleep/Lean), `Entry Properties`
  (Front/Behind/Left/Right/Up); **Z offset nemá vliv – animace se srovná na počátek kořene, model musí být
  pod počátkem**. https://wiki.beyondskyrim.org/w/images/a/ab/Nifskope_Furniture_tutorial.pdf
- Vstupní body (modré/žluté kruhy v CK) určují, kde končí vstupní animace; **posun vstupu = přetočit animaci**
  (offset je v klipu). https://forums.nexusmods.com/topic/10242203-remaking-the-furniture-entry-points
  Model je jen statika; bod interakce se k němu přidá – jakýkoli model může dostat marker spánku.
  https://forums.nexusmods.com/topic/9706683-adding-markers-to-objects

### 1.7 The Witcher 3 (REDkit) – action point + job tree
- Action point = entita `CActionPoint` + `CActionPointComponent` s `jobTreeRes`. Job tree: `Valid Categories`
  (kategorie pro rozvrh komunity), `Selection Mode` (`SM_SEQUENCE` / `SM_RANDOM`), `Iterations`,
  **`Left Item` / `Right Item`** (co je v které ruce), vstupní a „leave“ uzly; uzel klipu: `Category name`,
  `Anim Name`, `Anim Blend In/Out`, `Is Lookat Enabled`, **`Disable Path Agent`** (postavu kolize nevytlačí
  ze slotu – sezení u stolu); nastavení: `Left/Right Remove at end`, `Left/Right Drop on break`, `Can React`;
  volitelné pre/post animace (spawn rovnou v sedu; opakované použití bez vstávání).
  https://redkitwiki.cdprojektred.com/actionpoints.htm
  https://cdprojektred.atlassian.net/wiki/spaces/W3REDkit/pages/6328487/TOOL%3A+Job+Tree+editor

### 1.8 RAGE (GTA V; RDR2 stejná rodina enginu – **odhad**, RDR2 formát veřejně nedoložen)
- **Body scénářů přímo na archetypu (modelu) předmětu**: `CExtensionDefSpawnPoint` = `offsetPosition`,
  `offsetRotation` (vůči modelu), `spawnType` (scénář, např. sedět na lavici), `pedType`, `group`,
  `probability`, `timeTillPedLeaves`, `radius`, `start`/`end` (hodiny dne), `flags`.
  Samostatné body v mapě (`CScenarioPoint`): `iType`, `ModelSetId`, `iProbability`, `iTimeStartOverride`,
  `iTimeEndOverride`, `iRadius`, `iTimeTillPedLeaves`, `vPositionAndDirection`; příznaky mj.
  `NoSpawn`, `StationaryReactions`, `PreciseUseTime`, `CheckCrossedArrivalPlane`, `OpenDoor`.
  Řetězy bodů (`CScenarioChainingNode`) nesou jméno rekvizity (`prop_bench_01a`, `prop_atm_01`).
  Zdroj: zpětně analyzované typy v CodeWalker
  https://github.com/dexyfex/CodeWalker/blob/master/CodeWalker.Core/GameFiles/MetaTypes/MetaTypes.cs
  → **Lavice nese své body sezení sama** – kdekoli ji položíš, body jdou s ní (to chceme pro katalog).

### 1.9 CryEngine a KCD / KCD2 (Warhorse)
- CryEngine Smart Objects: pravidlo páruje třídu *User* a *Object* (+ stav), spouští AI akci; **helpery** =
  orientované body s offsetem **vázané na třídu smart objectu, ne na model**; pravidla v externí XML knihovně
  (`GameSDK/Libs/SmartObjects.xml`); navigační helpery mají cenu průchodu. **Animace musí být odsazená od
  smart objectu, který leží v počátku**; helpery se neexportují jako potomci geometrie.
  https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1048822
  https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/25534850
  https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1048656
- **Warhorse (oficiální ScriptBind dokumentace KCD)**: `C_ScriptBindSmartObject` má `GetHelpers`,
  `GetHelpersCategory(categoryName)`, `GetHelperLinks(helperName)`, `GetHelperLinkTarget`,
  `GetHelperUserData(helperName, userDataKey)`; AI: `GetSmartObjectHelper`, `SetSmartObjectState`,
  `GetLastSmartObjectExitPoint` (výstupní bod). Tj. helpery jsou **pojmenované, kategorizované, propojené do
  grafu (vstup → místo → …) a nesou klíč/hodnota uživatelská data**.
  https://github.com/Nexus-Mods/kcd-documentation (soubory `C_ScriptBindSmartObject*.html`)
- Komunitní wiki: helpery tvoří „les“ (stromovou strukturu), nesou informaci, které animace lze u objektu použít;
  existují debug příkazy pro ověření helperů. https://wiki.nexusmods.com/index.php/Animations_on_Smart_Objects
  (stránka vrací 403, citováno z výtahu vyhledávání – detaily **neověřeny**).
- **KCD2 oficiální modding wiki** (Warhorse YouTrack): tabulky `ai/smartentity/smartEntity`,
  `ai/subbrain_smart_object`, `ai/subbrain_smart_area`, `animation/anim_fragment`, a **`LEVEL/smartobjectanimations`**
  (data animací smart objectů exportovaná z levelu, patchovatelná). https://youtrack.warhorsestudios.cz/articles/KM-A-12
  https://youtrack.warhorsestudios.cz/articles/KM-A-92 (zrcadlo: https://github.com/souky-byte/kcd2-modding-docs)
  Entita `UsableItem` má vlastnost `soclasses_SmartObjectClass` (třída určuje helpery).
  Konkrétní schéma `smartobjectanimations` veřejně popsané nenašel jsem.

### 1.10 Cyberpunk 2077 (workspot) a Assassin's Creed
- Workspot (`.workspot`): seznam `worksSequence` s `workAnimClip` (`idleName`, `animName`), přepínání mezi klipy
  ve stejném workspotu; entita odkazuje přes `workWorkspotResourceComponent`.
  https://wiki.redmodding.org/cyberpunk-2077-modding/modding-guides/animations/abusing-workspots
- AC Unity: AI LOD (jednodušší NPC = méně animací), „crowd stations“ (skupiny kolem jedné události); detaily
  markerů veřejně nejsou. https://game.watch.impress.co.jp/docs/news/20150307_691715.html
  https://www.killscreen.com/assassins-creed-unity-making-crowd-main-character

### 1.11 Úchopy: sockety, pózy rukou, dvouruční, IK okna
- **Socket = offset vůči kosti** (UE Persona); rekvizitu lze náhledově připnout a doladit; sockety sdílené
  kostrou vs. „mesh socket“ jen pro jeden model. https://dev.epicgames.com/documentation/unreal-engine/skeletal-mesh-sockets-in-unreal-engine
- **Dva protikusy**: soket na ruce (kost `hand_r` + offset) a úchopový bod na předmětu; připnutí = zarovnat
  úchop předmětu na soket ruky (u nás dnes `drzeni.uchop` + `rot_st` v `postavy.json`). Druhá ruka = IK na druhý
  bod předmětu (Final IK `InteractionTarget` jiného efektoru; CAS `target_bone_name`).
- **Póza prstů per typ úchopu** (`HandGrabPose`, Pose Asset) – viz `uchop_reserse.md`; u nás cache v
  `uchop_pozy.json` klíčovaná předmět|ruka|bod|osa.
- **IK okno**: váha IK z křivky klipu (UE CAS `alpha_curve_name`, Unity „RightHandReach“) nebo časové okno
  (MatchTarget `start/targetNormalizedTime`, Motion Warping okno). Mimo okno čistý klip.

### 1.12 Validace a nástroje (jak týmy ověřují)
| Kontrola | Kdo | Zdroj |
|---|---|---|
| kapsle postavy v místě slotu nekoliduje | UE `SlotUserCollision` | výše 1.2 |
| trajektorie navmesh-bod → slot bez kolize | UE `bCheckTransitionTrajectory` | výše 1.2 |
| bod na zemi (ground trace) | UE `bTraceGroundLocation` | výše 1.2 |
| vstup leží na navigovatelné ploše (≠ dosažitelný!) | UE validace | reserse_animace kap. 1 |
| slot odkazuje na existující kost / jméno | Sims (klip selže), S4S pyramida | 1.1 |
| úchop: ruka ≤ 2 mm v předmětu, ≤ 5 mm mimo | deadnight PR #507 | uchop_reserse.md |
| validace dat při uložení / v CI (`-run=DataValidation`) | UE Data Validation | https://dev.epicgames.com/documentation/en-us/unreal-engine/data-validation-in-unreal-engine |
| vizuální ladění bodů ve hře | UE Gameplay Debugger, CK kruhy vstupů, S4S váleček | 1.2, 1.6, 1.1 |
| vstupní body vypnuté u zdi (varianty L/R) | Bethesda | reserse_animace kap. 1 |

Konkrétní automatické testy „ruka nezajede do ohně přes celý klip“ veřejně popsané nenašel jsem → **odhad**
(náš návrh v 3.5 vychází z UE validačních kroků + vzorkování klipu jako CAS `sample_rate`).

### 1.13 Godot 4.4 – co máme k dispozici
- `SkeletonModifier3D` (základ, 4.3+), **`LookAtModifier3D`** (4.4, = jednokostní IK, hlava/krk na cíl);
  `SkeletonIK3D` je **deprecated** (stále funguje, váha přes `SkeletonModifier3D.influence`). Plné IK
  (`TwoBoneIK3D`, `FABRIK3D`, `CCDIK3D` …) až ve 4.6; `BoneConstraint3D`/`CopyTransformModifier3D` ve 4.5.
  https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/
  https://godotengine.org/article/design-of-the-skeleton-modifier-3d/
  https://docs.godotengine.org/ja/4.4/classes/class_skeletonik3d.html
  https://docs.godotengine.org/ja/4.4/classes/class_lookatmodifier3d.html
  → Na 4.4 máme pro ruce jen `SkeletonIK3D` (deprecated) nebo vlastní analytické 2-kostní IK ve skriptu
  (vlastní `SkeletonModifier3D` s `_process_modification()`); u nás už existuje IK druhé ruky (`drzeni`).
- `BoneAttachment3D` = soket ruky (už používáme, `postavy.json` → `drzeni._popis`).
- **Prázdné objekty (empty) z Blenderu** přicházejí v glTF jako uzly → v Godotu `Node3D`; jmenné přípony
  importu (`-noimp`, `-col`, `-colonly`, `-navmesh`, `-occ`, `-loop` …) – `-noimp` uzel odstraní.
  https://docs.godotengine.org/en/4.4/tutorials/assets_pipeline/importing_3d_scenes/node_type_customization.html
- **Custom properties → glTF `extras`**: Blender exportér to umí (volba Custom Properties / `export_extras`,
  vlastnosti musí být na *Object*, ne *Object Data*). https://docs.blender.org/manual/en/4.4/addons/import_export/scene_gltf2.html
  https://forum.babylonjs.com/t/how-to-read-custom-properties-from-blender-in-babylonjs/33088
  Godot 4.4 je importuje jako metadata `extras` (doloženo na *mesh* resource: `mesh.get_meta("extras")`);
  na uzlu `Node3D` z empty **neověřeno** (odhad: ano, ověřit). Spolehlivá cesta: `GLTFDocumentExtension._import_node`
  (dostane JSON uzlu vč. extras). https://forum.godotengine.org/t/gltf-import-how-does-one-get-metadata-extras/105711
  https://docs.godotengine.org/en/latest/classes/class_gltfdocumentextension.html
- U nás: `blender/export_game.py` exportuje s `export_extras=False`; `blender/predmety.py` už umí číst JSON
  uzlů z GLB (`_uzly_sceny`) – to je hotová cesta „empties v Blenderu → katalog JSON“ bez závislosti na importu Godotu.

---

## 2. Srovnávací tabulka pojmů

| Pojem (u nás) | The Sims | UE5 (SO + MW + CAS) | Unity / Final IK | Bethesda CK | Witcher 3 | RAGE (GTA V) | CryEngine / KCD |
|---|---|---|---|---|---|---|---|
| **slot / stání** (kde stojí kořen) | routing slot (kost rigu), part + subroot | Slot (offset+rot vůči kotvě) | (pozice z Triggeru) | furniture marker (Offset, Heading) | action point | `offsetPosition/Rotation` na archetypu | helper třídy SO |
| **vstup / přístup** | constraint: kruh ideal/max, facing; routing flags 8 směrů | `EntranceAnnotation` (`bIsEntry`/`bIsExit`, ground trace, trajektorie) | `InteractionTrigger.characterPosition` (radius, maxAngle, orbit) | Marker Entry Points (Front/Behind/L/R/Up) | (navigace k AP) | `CheckCrossedArrivalPlane`, `radius` | navigační helpery + linky, `GetLastSmartObjectExitPoint` |
| **úchop / cíl ruky** | IKtarget slot; tělové sloty | CAS `IKTargetDefinition` (bone→target bone), sockety | `InteractionTarget` per efektor, TwoBone IK target, MatchTarget | (v animaci) | `Left/Right Item` | (v animaci) | helper user data |
| **póza ruky** | v klipu | Pose Asset / Control Rig | `HandGrabPose` + grab surface | v klipu | v klipu | v klipu | v klipu |
| **zakázaná zóna** | footprint + jig (blokuje routing) | `SlotUserCollision` kapsle, nav filtr | (collider triggeru) | navmesh cut | `Disable Path Agent` (opačně: nevytlačit) | — | navmesh |
| **obsazenost / víc uživatelů** | parts, `adjacent/overlapping_parts` | Free/Claimed/Occupied, víc slotů | (jedna interakce na efektor) | 1 marker = 1 herec | 1 AP = 1 NPC | 1 bod = 1 ped, `probability` | stav SO (`SetSmartObjectState`) |
| **sada klipů vstup–smyčka–výstup** | klip s offsetem v rigu | montáž + warp okno, CAS sekce | weightCurves + events (Pause) | enter/idle/exit furniture anim | enter / loop×`Iterations` / leave, pre/post | scenario type | `smartobjectanimations` tabulka |
| **kategorie těla / kdo smí** | postura (stání/sed) v constraints | `UserTagFilter`, Activity tags | — | Marker Keyword, Animation Type | `Valid Categories`, m/w/d v názvu | `pedType`, `ModelSetId`, čas `start/end` | třída User × Object |
| **kontrola** | S4S vizualizace, klip selže bez slotu | validační filtr, Data Validation, Gameplay Debugger | gizmo v editoru | kruhy v CK | náhled v editoru (Globe) | CodeWalker náhled | debug cvar helperů |

Shrnutí shody: (1) body jsou **v souřadnicích předmětu** a jdou s ním; (2) **vstup ≠ slot** – vstup je mimo
překážky, slot je cíl, mezi nimi krátký zarovnávací přechod (warp okno); (3) úchop je **na předmětu per ruka**
a IK jen v okně klipu; (4) obsazenost po slotech; (5) validace offline + vizuální ladění.

---

## 3. Návrh pro nás

### 3.1 Principy (odvozené z kap. 1)
1. **Předmět nese body, postava chování** (UE SO, RAGE archetyp, Cry helper). Body jsou součást záznamu předmětu
   v katalogu a jdou s ním, ať je položen kdekoli (`nabytek.json` jen umisťuje).
2. **Tři druhy bodů**: `sloty` (kde stojí/sedí/leží kořen), `vstupy` (odkud se k slotu přijde a kam se odejde),
   `uchopy` (cíl ruky / bod předmětu pro dlaň). Plus `zakazane_zony` a `uloziste` (container sloty – kam se
   pokládá, Sims).
3. **Souřadnice**: lokální soustava předmětu jako v Godotu (Y nahoru, metry, `yaw_st` ve stupních kolem Y,
   0 = postava hledí po −Z předmětu? → **odhad, zvolit jednou a zapsat do `_popis`**), měřítko katalogu (`meritko`)
   se aplikuje na offsety.
4. **Slot říká, jaké klipy smí** (kategorie těla), ne naopak – nemůže nastat „klečí v ohni“ (rešerše kap. 1.3).
5. **Ruka se cílí na bod předmětu a pózu jménem**; vazba na kost se řeší soketem ruky (`BoneAttachment3D`),
   ne pevným offsetem na kost (Mixamo roll – `uchop_reserse.md`).
6. **Kontrola je data-driven a automatická** (test v `pravidla/svet/kontroly.json`, žádná čísla v kódu).

### 3.2 Kde data žijí
- **Autorování (doporučeno): prázdné objekty v Blenderu** jako potomci předmětu, pojmenované předponou:
  `SLOT_<id>`, `VSTUP_<slot>_<n>`, `UCHOP_<id>_<l|r|lr>`, `ZONA_<id>` (empty typu koule/válec = poloměr/výška),
  `ULOZ_<id>`; doplňkové hodnoty jako Custom Properties na objektu (`klipy`, `kategorie`, `poza_ruky`…).
  Vizuálně se ladí v Blenderu nad modelem (jako S4S/TS3 slot editor, CK kruhy). Prázdné objekty dostanou při
  exportu do hry příponu `-noimp` nebo se z herního GLB vynechají – **do hry jdou jen přes katalog** (odhad:
  jednodušší než spoléhat na import extras v Godotu 4.4, viz 1.13).
- **Generování**: `blender/predmety.py meta` (už čte uzly GLB přes `_uzly_sceny`) přečte empties a zapíše do
  `modely/predmety.json` → klíč `body` u každého předmětu. U předmětů bez empties (Poly Haven kusy) se body
  zatím zapíšou ručně do přepisu `pravidla/svet/predmety_body.json` (stejné schéma; přepis má přednost).
- **Pravidla chování** (kategorie klipů, rezervy zón, IK okna, tolerance testů) zvlášť v
  `pravidla/svet/interakce.json` – ruční, s `_popis` a citací Míši/rešerše (jako ostatní pravidla).
- **Body budov** (lavice v modelu domu, `sedaky_modelu`, `zapecene`) přejít na stejné schéma (`body` u modelu
  v `modely/svet.json` nebo nabytku), aby existoval jeden kód.

### 3.3 JSON schéma (záznam předmětu v `modely/predmety.json` → `body`)
```json
{
 "kotel_zavesny": {
  "nazev": "Kotel na řetězu", "rozmer": [0.45, 0.40, 0.45],
  "body": {
   "verze": 1,
   "max_uzivatelu": 1,
   "sloty": [
    {"id": "michani", "druh": "stani",
     "pos": [0.0, 0.0, 0.62], "yaw_st": 180.0,
     "kategorie": ["stoj"], "zakazane_kategorie": ["klek", "leh", "sed_zem"],
     "cinnosti": ["vareni"], "klipy": {"vstup": "Vareni_Enter", "smycka": "Vareni_Michani_Loop",
       "zpestreni": ["Vareni_Prilozit", "Vareni_Ochutnat"], "vystup": "Vareni_Exit"},
     "rekvizity": {"r": "varecka"},
     "uchopy": ["ucho", "nad_hrncem"],
     "kapsle": {"r": 0.25, "v": 1.7},
     "warp": {"klip": "Vareni_Enter", "okno": [0.0, 0.6], "translace": true, "rotace": "prevzit"},
     "blokuje": []}
   ],
   "vstupy": [
    {"id": "vpredu", "slot": "michani", "pos": [0.0, 0.0, 1.10], "yaw_st": 180.0,
     "vstup": true, "vystup": true, "na_zem": true, "kontrola_trajektorie": true}
   ],
   "uchopy": [
    {"id": "ucho", "ruka": "l", "pos": [0.20, 0.38, 0.0], "osa": [0, 0, 1], "delka_m": 0.06,
     "poza": "ucho_hak", "ik_okno": [0.15, 0.85], "kost": "hand_l"},
    {"id": "nad_hrncem", "ruka": "r", "pos": [0.0, 0.45, 0.05], "osa": [0, 1, 0], "delka_m": 0.0,
     "poza": "varecka_sevreni", "ik_okno": null, "kost": "hand_r", "pres_rekvizitu": "varecka"}
   ],
   "zakazane_zony": [
    {"id": "ohen", "tvar": "valec", "pos": [0.0, -0.55, 0.0], "r": 0.55, "v": 0.9,
     "pro": ["koren", "ruce", "hlava", "nohy"], "rezerva_m": 0.35}
   ],
   "uloziste": []
  }
 }
}
```
Klíče (všechny délky v m, souřadnice v soustavě předmětu, Y nahoru):
- `max_uzivatelu` – horní mez současných uživatelů (Sims parts / UE počet slotů); `sloty[].blokuje` = id slotů,
  které se obsazením tohoto slotu zablokují (Sims `overlapping_parts`) – např. postel 2 místa vs. „ležet uprostřed“.
- `sloty[].druh` ∈ `stani | sed | leh | drep | klek` = postura kořene; `kategorie` = povolené kategorie klipů
  (vlastnost klipu, rešerše kap. 1.3 bod 6); `cinnosti` = které činnosti z `postavy.json cinnosti` sem smí.
- `sloty[].klipy` = sada vstup–smyčka–zpestření–výstup (Witcher job tree; Bethesda enter/idle/exit);
  `rekvizity` = co je v které ruce během smyčky (`Left/Right Item`, odložit při přerušení = `drop_pri_preruseni`).
- `sloty[].warp` = okno ve vstupním klipu, kdy se kořen dotáhne na slot (UE Motion Warping, Unity MatchTarget).
- `sloty[].kapsle` = kapsle postavy testovaná v místě slotu (UE `SlotUserCollision`).
- `vstupy[]` = odkud se do slotu jde a kam se z něj odchází (`vstup`/`vystup` zvlášť jako UE `bIsEntry/bIsExit`),
  `na_zem` (ground trace), `kontrola_trajektorie` (UE `bCheckTransitionTrajectory`). Víc vstupů = výběr podle
  volnosti (Bethesda Front/Behind/L/R) – vstup u zdi se zahodí za běhu, ne variantou modelu.
- `uchopy[]` = bod (nebo úsečka `osa`×`delka_m` = válcová plocha úchopu, Meta `CylinderGrabSurface`) na předmětu,
  `ruka` ∈ `l|r|lr`, `poza` = jméno pózy prstů (cache `uchop_pozy.json`), `kost` = soket ruky,
  `ik_okno` = normovaný čas ve smyčce, kdy je IK zapnuté (null = rekvizita je v ruce přes BoneAttachment3D
  a IK neběží), `pres_rekvizitu` = ruka drží rekvizitu, jejíž hrot míří k bodu.
- `zakazane_zony[]` = koule/válec/kvádr; `pro` = které části těla se testují; `rezerva_m` se přičte
  (nahrazuje `postavy.json u_ohne.odstup_m` pro konkrétní předmět).
- `uloziste[]` = sloty pro pokládání předmětů (Sims container): `pos`, `yaw_st`, `max_rozmer`.

Pravidla v `pravidla/svet/interakce.json` (ruční):
```json
{
 "_popis": "Míša 27. 11. body úchopu a vstupu; rešerše reserse_body_predmetu_27_11.md",
 "kategorie_klipu": {"Sitting_Idle_Loop": "sed", "Vareni_Michani_Loop": "stoj", "Kneel_Loop": "klek"},
 "vychozi": {"kapsle": {"r": 0.25, "v": 1.7}, "rezerva_zony_m": 0.35, "warp_okno": [0.0, 0.5]},
 "rezervace": {"uvolnit_po_s": 5.0, "zavazek_dojit_s": 30.0},
 "testy": {"ruka_v_predmetu_mm": 2, "ruka_mimo_mm": 5, "vzorku_na_klip": 30,
           "koren_od_slotu_m": 0.05, "noha_nad_zemi_m": 0.03, "vstup_od_slotu_max_m": 1.5}
}
```
(číselné hodnoty: 2 mm / 5 mm ze zdroje deadnight; ostatní **odhad**, doladit snímkem na tabletu).

Příklady dalších předmětů (zkráceně, **odhad poloh – změřit v Blenderu**):
- `kovarna_kovadlina`: 1 slot `stani` čelem k rohu, vstupy vpředu+vlevo, `uchopy`: žádné na kovadlině (perlík
  v ruce přes `drzeni.perlik`), `zakazane_zony`: kvádr kovadliny pro nohy; výheň zvlášť se zónou ohně.
- `stul_selsky`: 4–6 slotů `sed` po stranách (vazba na lavici: slot stolu má `potrebuje: "lavice_selska"`),
  `uloziste` na desce (misky, hrnek – dnes `nabytek.json` výška 0.776), `max_uzivatelu` 6.
- `truhla`: 1 slot `drep|stani` před víkem, `uchopy` víko `lr` s `ik_okno` v klipu `Truhla_Otevri`
  (dnes `postavy.json klipy_cil`), stav předmětu otevřeno/zavřeno (Sims animation states / UE object state).
- `studanka`: 1–2 sloty `stani` u roubení, uchop rumpál/vědro, zóna = šachta (kořen + nohy).
- `lavice_selska`: N slotů `sed` po `sirka_mista_m`, vstupy vpředu, `blokuje` sousední místo jen u úzké lavice.
- `postel_*`: slot `leh` (+ `sed` na hraně jako přechod), vstup z boku volného od zdi, `max_uzivatelu` 1–2.
- `seno_kupa`: slot `leh|sed` nahoře, zóna celá kupa pro chůzi ostatních (Sims footprint).
- `sud`: `stani` u boku, `uchopy` čep/víko; `uloziste` na víku (korbel).

### 3.4 Běh za hry (postup)
1. Činnost z rozvrhu vybere předmět dle `cinnosti` → **rezervuje slot** (Free→Claimed; UE claim) → vybere
   vstup (volný, na navmesh, ne v zóně jiného předmětu).
2. Chůze na vstup (navigace); příchod = překročení roviny vstupu (RAGE `CheckCrossedArrivalPlane`, **odhad** užití).
3. Vstupní klip s `warp` oknem: kořen se dotáhne na slot (pozice+yaw); Occupied.
4. Smyčka + zpestření; IK ruky jen v `ik_okno` (váha rampou 0,1–0,2 s, **odhad**); `LookAtModifier3D` hlavy na
   bod zájmu (kotlík, kovadlina).
5. Výstup přes `vystup` vstupu; přerušení → odložit/upustit rekvizitu dle slotu, uvolnit slot.

### 3.5 Automatické kontroly (test v `kontroly.json` / test lide_chovani; bez Godotu jen datové 1–6)
1. **Schéma**: každý předmět s `cinnosti` má ≥1 slot; každý slot ≥1 vstup s `vstup:true` a ≥1 s `vystup:true`;
   id unikátní; `uchopy` slotu existují; `klipy` existují v knihovně; kategorie klipů ∈ `kategorie` slotu a ∉
   `zakazane_kategorie` (Sims: klip na neexistující slot = chyba).
2. **Zóny**: kořen slotu i každý vstup leží mimo všechny `zakazane_zony` + `rezerva_m` (všech předmětů v okolí po
   umístění z `nabytek.json`).
3. **Podlaha**: slot `stani/sed` – kapsle stojí na podlaze/zemi (raycast do kolizí `Kol_*` ≤ `noha_nad_zemi_m`);
   sed – výška sedáku ± tolerance (dnes `sedani.tolerance_m`).
4. **Průnik**: kapsle slotu (`kapsle`) nekoliduje s geometrií okolí (zdi, jiný nábytek) – UE `SlotUserCollision`.
5. **Trajektorie**: úsečka vstup→slot (šířka kapsle) bez kolize a mimo zóny (UE `bCheckTransitionTrajectory`);
   délka ≤ `vstup_od_slotu_max_m`; vstup na navmesh a **dosažitelný** cestou ode dveří (ne jen „na navmesh“).
6. **Více uživatelů**: kapsle současně obsaditelných slotů (bez `blokuje`) se nepřekrývají; `max_uzivatelu`
   ≤ počet slotů.
7. **Dosah ruky** (offline přes klip, vzorkovat `vzorku_na_klip`): v `ik_okno` je vzdálenost ramene → úchop ≤
   délka paže × 0,95 (**odhad**), loket podle `hint` neprochází tělem; mimo okno ruka ≤ X od klipové polohy.
8. **Zóny přes celý klip**: kosti rukou, hlavy, nohou a kořen pro každý vzorek smyčky/vstupu/výstupu mimo
   `zakazane_zony` (rešerše kap. 1.3 bod 10).
9. **Úchop**: dlaň ≤ 2 mm v předmětu, kontakt ≤ 5 mm mimo (deadnight; už `test_drzeni`).
10. **Vizuální ladění**: debug přepínač kreslí sloty (šipka yaw), vstupy (kroužek), úchopy (křížek per ruka),
    zóny (červený válec) a stav Free/Claimed/Occupied barvou (UE Gameplay Debugger, S4S, CK); snímek z tabletu
    pro Míšu u každého nového předmětu.

### 3.6 Převod z dnešního stavu (co nahradí co)
| Dnes | Nově |
|---|---|
| `postavy.json u_predmetu` (střed strany kvádru + `od_m`) | `body.sloty` + `vstupy` z empties; výpočet z kvádru jen jako záloha pro předměty bez `body` |
| `postavy.json u_ohne.odstup_m` | `body.zakazane_zony[].rezerva_m` u ohniště/kotle |
| `postavy.json klipy_cil` (Truhla_Otevri → truhla) | `sloty[].klipy` + `uchopy` s `ik_okno` |
| `postavy.json drzeni` (uchop, rot_st, druha_ruka) | zůstává pro **rekvizity v ruce**; body na pracovním předmětu jdou do `body.uchopy` |
| `nabytek.json sedaky_modelu`, `zapecene` | sloty `sed`/`leh` u modelu budovy ve stejném schématu |
| `postavy.json sedani` (hledat sedák, výška) | slot `sed` s výškou z modelu; pravidla tolerancí v `interakce.json` |

### 3.7 Otevřené / odhady k ověření
- Import extras na uzlech empties v Godotu 4.4 (odhad ano) – nepotřebujeme, pokud jde přes `predmety.py`.
- Konvence `yaw_st = 0` (směr pohledu postavy) – určit jednou a otestovat na lavici.
- IK rukou na 4.4: vlastní 2-kostní IK jako `SkeletonModifier3D` vs. `SkeletonIK3D` (deprecated) – rozhodnout podle
  výkonu na tabletu; 4.6 přinese `TwoBoneIK3D`.
- Přesné schéma KCD2 `smartobjectanimations` a RDR2 scénářů veřejně nedoloženo.
