# Animace z Disku – inventura 25. 11. (Míša: „máme více animací, projdi si poctivě všechny“)

Složky: A = `1QccSsm8qrs2OtSEtehUJN9je80YPkStW`, B = `1e_00stKPJ4IObGT2EAVG9FnsM1YfOtyi`.
Postup: seznam celé složky, rozbalení všech archivů (velké čteny po kouskách přes HTTP Range), rozbor každého FBX v Blenderu
(kostra, počet kostí, snímky, fps, posun pánve), u nových klipů kontaktní list 10 snímků (panáček zepředu a z boku) –
skript `anim_info.py` / `anim_listy.py` (scratchpad, ne v repu). 193 + 25 FBX rozebráno, 39 kontaktních listů prohlédnuto.

## A – už ve hře (Míša poslal 10.–11. 11.)
84 Mixamo FBX + Farming Pack (25) + Gestures Pack Basic (15) + Action Adventure Pack (22) = vše už je v
`tools/postavy_q/mixamo/` a přenáší se na kostru UAL (`tools/postavy_q/anim_cmu.py`). Kostra Mixamo 67 kostí, 30 fps.
Nové jen 3: **Sitting Laughing** (smích vsedě, 8,3 s – hostinec), **Boxing** (pěstní postoj s údery, 1,7 s – rvačka
v krčmě), **Body Block** (kryt pažemi, 3,4 s). Heavy Weapon Swing (1), Standing Melee Attack Downward (1), Bash (1),
Dig And Plant Seeds (1), Picking Up (1) = stejné klipy jako bez (1). Zbytek složky A nejsou animace (modely glb,
Female01 zdroje, skripty tváří).

## B – nové
| Balík | Klipů | Kostra / fps | Co to je | Pro hru |
|---|---|---|---|---|
| Animations_V1_01.zip (1 GB) + Anims_Only_FBX_V1.zip (463 MB) | 2 549 (2× totéž, jednou s panáčkem) | 62 kostí Root/Hips/Abdomen, 30 fps | **celá databáze CMU mocap** (předměty 01–144) jako FBX | Hra už CMU bere (BVH z githubu, `stahni_cmu.sh`); balík = celá knihovna offline. Hledat podle popisu CMU, ne celé. |
| BlenderGoodies.zip | – | – | převodní skript BVH→FBX (vyžaduje Auto-Rig Pro), GPL | nepotřebujeme (máme anim_cmu.py) |
| MotionLibrary_WalkCycles.zip | 12 | 23 kostí, 120 fps, s posunem | Movella/Xsens mocap | **nošení pytle na levém/pravém rameni** (s165/s166 – mlynář, čeledín), **chůze do svahu 35°**, **opilá chůze** ×2 (krčma), **kulhání** (zraněný); skok přes překážku jednou rukou (ohrada); zombie/„reveal“ ne |
| MotionLibrary_Weapons.zip (×2 stejné) | 11 | totéž | | **lovec s lukem** (77 s: natažení, míření, výstřel – myslivec, stráž s lukem); nůž (bodnutí) možná; pistole/granát/puška ne |
| Rokoko gesta (*_mixamo.fbx, 17 souborů) | 17 | Mixamo 52 kostí (bez prstů?), 24 fps, dlouhé (20–83 s), několik pokusů za sebou, začátek T-póza | Rokoko free | **SomethingBehindMe_Eating** (0–19 s jídlo vsedě – hosté jedí), **SittingTalking_Gossip** (0–24 s klep vsedě), **TalkingHead_Intv** (vykládání vsedě), **ChefCooking** (práce rukama v pase – kuchařka u krbu), **Fight_01/02** (hádka – gesta, ne rvačka), **Laughs** (smích vestoje), **FootTapping** (čekání, ruce v bok – stráž, čekající), **Clap_SlowClap**, **FistPumps** (jásání – dav), **Shrugging**, **HeadTilts**, **DoubleTakes**, **FacePalms**, **Judges** (ukazování, hodnocení – trh), **Flirty** (drobné postávání); OnCellPhone, Sitcom*, NatureDocumentary, MiddleFingers, ShoulderShimmy, BurstThroughDoor ne |
| Loop_DrinkinHand_Left/RightHand | 2 | 62 kostí (jako CMU FBX), 30 fps | pití vestoje s pohárem v ruce, smyčka | **hosté vestoje u pultu** |
| Loop_Dancer_01–05, DJ, DJ_02, Bouncer_01–02 | 9 | 62 kostí | moderní tanec / DJ / vyhazovač | ne (Dancer_03_Sitting = tanec vsedě, ne) |
| MARTIAL-ARTS-MOCAP.zip | 6 | Mixamo 53 kostí, 30 fps | | **GetUp_WipeBloodfromMouth** (pád, vstane, otře ústa – po ráně), **BattleTaunts_WithSword** (vyzývání s mečem), **Samurai_DrawSword** (tasení, japonské – jen část); kata a taiči ne |
| Sports.zip, Superhero.zip, Rokoko Wingardium Leviosa (magie) | 7 + 9 + 24 | Mixamo | sporty, superhrdinové, kouzla | ne; snad Hawkeye_Archery (luk), WatchOverCity (stojí a hledí do dálky – stráž na hradbě) – nerozebráno |

## Jak je dostat do hry (návrh)
- Mixamo (52/53/67 kostí) jde stávající cestou `anim_cmu.py` (mapa Mixamo → UAL); Rokoko: převzorkovat 24 → 30 fps,
  vyříznout úsek (bez T-pózy a bez dalších pokusů), panev bez driftu.
- Movella (23 kostí, 120 fps) a 62kostní CMU FBX: nová mapa kostí v `anim_cmu.py` (CMU BVH už má – stejná jména Hips/
  Spine…?) – NEOVĚŘENO, ověřit na jednom klipu.
- Licence: Mixamo a CMU ověřeny dřív (README, stahni_cmu.sh); Rokoko free „pro komerční projekty“ (rešerše 2020, znění
  u jednotlivých klipů nečteno); Movella Motion Library – licence nečtena = NEOVĚŘENO před vydáním.
