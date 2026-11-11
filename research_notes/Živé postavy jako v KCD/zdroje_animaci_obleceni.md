# Zdroje animací a modulárního oblečení pro postavy vsi + vrstvené oblečení a pružné kosti v Godotu 4.4.1

Rešerše 11. 11. 2026. Primární index Mixamo: dataset `tanish434/Mixamo-Animations-Characters` (metadata.csv, **2 446 klipů**
s názvem z UI Mixamo a popisem) – [HF dataset](https://huggingface.co/datasets/tanish434/Mixamo-Animations-Characters).
Stažený index: `/tmp/claude-0/-home-user/e2090080-7084-5736-a3c7-8c30d4a43985/scratchpad/mx/meta.csv` (v scratchpadu, smaže se).
Název v tabulce = **text, který se píše do vyhledávání na mixamo.com** („prompt“), v závorce popis z katalogu; číslo = počet snímků
(30 fps).

## Které konkrétní klipy Mixamo existují pro práce ve vsi (přesné názvy) a co musí přijít odjinud?

### Takeaway
Mixamo pokryje sezení/jídlo/pití/hovor, opírání o zeď, klečení, kopání lopatou, sázení, trhání plodů, žně kosou, trakař,
tlačení a tahání těžkého, nošení bedny, tahání lana a obsluhu u pultu. **V indexu 2 446 klipů NENÍ** zametání, kování
u kovadliny, krumpáč, štípání dřeva, nošení vědra, tácu, pytle na rameni ani krmení slepic – ty musí přijít z UAL
(Quaternius), CMU nebo vlastní úpravou (např. „Box“ klipy + jiný předmět v ruce). Pozor: Míšův seznam z 10. 11.
(`docs/predani.md`: „Hammering, Pick Axe Mining, Chopping Wood, Sweeping“) v indexu nemá shodu – před stažením ověřit
vyhledáním na webu, neočekávat je.

### Cited Findings
Všechny názvy níže jsou z metadata.csv indexu — [HF dataset tanish434/Mixamo-Animations-Characters](https://huggingface.co/datasets/tanish434/Mixamo-Animations-Characters):

**Voda / lano / studna**
- `Pulling A Rope` („Mime Pulling A Rope“, 443 sn.) – nejblíž vytahování vědra ze studny (pantomima, ruce střídavě). Jiné „rope“ klipy jsou šplh (`Climbing A Rope`, `Rope Climb`) – nehodí se.
- `Pulling Lever` („Pulling A Lever Down“, 189) – rumpál/klika nahrazuje jen přibližně.
- `Drinking Fountain` (326) – sehnutí a pití; pro napití u studny/koryta.
- Vědro/džber: **žádný klip** (hledáno bucket, pail, well).

**Nošení**
- `Box Idle` („Carrying A Box“, 190), `Box Walk Arc` (38), `Box Turn` (vlevo 47 / vpravo 36), `Jogging With Box` (24) – nošení před tělem oběma rukama; s jiným předmětem (koš, náruč dříví, necky) použitelné.
- `Walking With Shopping Bag` („Male Walking With Shopping Bag“, 39) – jedna ruka nese u boku → **nejlepší náhrada chůze s vědrem/džberem**.
- `Lifting Object` („Lifting A Heavy Object With Both Hands“, 346), `Picking Up` (288), `Picking Up Object` (jednou rukou, 104), `Dropping` (149), `Gathering Objects` („Squatting Down To Gather Objects“, 180).
- `Carrying`/`Walking`/`Carrying Turn` = **nesení člověka** („Carrying Someone…“) – ne pytel; pro pytel na rameni nevhodné.
- Tác/servírování: `Bartending` („Pouring And Serving Drinks“, 408) – za pultem hostince. Klip „tray“ v indexu není.

**Vozík / trakař / tlačení**
- `Wheelbarrow Walk` (plný i prázdný, 30), `Wheelbarrow Walk Turn` (33), `Wheelbarrow Idle` („Holding A Full Wheelbarrow Idle“, 46), `Wheelbarrow Dump` (236) – kompletní sada pro trakař.
- `Push Start` (143) / `Push` („Pushing Heavy Object“, 52 i 241) / `Push Stop` (79), `Pushing` (81, 120) – tlačení vozíku/vrat.
- `Pull Heavy Object Start` (42) / `Pull Heavy Object` (34) / `Pull Heavy Object Stop` (41) – tahání káry/klády.

**Pole a zahrada**
- `Harvesting` („Harvesting With A Sythe“ [sic], 98) – **žně kosou** (Mixamo má kosu, UAL má srp `Farm_Harvest`).
- `Digging` („Digging Hole With Shovel“, 196) – rýč/lopata.
- `Dig And Plant Seeds` (klečí, 166), `Plant A Plant` (klečí, 228), `Plant Tree` (stojí, 279), `Pull Plant` (klečí 203 / stojí 250) – plení.
- `Pick Fruit` (3 varianty: ve výši očí 187, ze země 214, nízko visící 281) – sad.
- Krmení slepic: **žádný klip**; nejblíž `Throw` („Throwing An Object From A Standard Pose“, 67) nebo `Throw Object` (217) – rozhazování zrna jen přibližně.
- `Petting Animal` (426), `Petting` („Petting A Large Animal“, 228) – u koně/krávy ve stáji.

**Řemesla**
- Kovadlina/kladivo, krumpáč, štípání dřeva, zametání: **v indexu nic** (hledáno hammer, anvil, smith, pick, mining, chop, axe, wood, sweep, broom). Klipy se sekerou jsou jen bojové (`Standing Melee Attack Downward` „Downward Attack With Axe“, 107; `Heavy Weapon Swing` „Two Handed Heavy Weapon Swing“, 157) – obouruční úder shora je nouzová náhrada štípání/kování.
- `Kneeling Inspecting` („Kneeling And Inspecting Element With Hands“, 149), `Holding Down` (58) – klečící práce (oprava, porážka). `Opening A Lid`/`Closing A Lid` (truhla, 269/330). `Writing` („Male Writing While Seated“, 151) – písař.
- `Fishing Cast` (264), `Fishing Idle` (107) – rybník.

**Sezení, stůl, hospoda**
- `Seated Idle` („…With Hands On A Table“, 126), `Asking Question` (stůl, 176), `Angry Gesture` (stůl, 176), `Banging Fist` („Banging Fist On Table“, 80), `Dice Idle` (ťukání prsty, 145).
- `Sitting Talking` („Sitting And Talking To Another Person“, 1323 a 1350 – dlouhé, dobré pro pozadí), `Talking` („Male Talking While Seated“, 151), `Sitting Laughing` (251), `Cheering While Sitting` (4 var.), `Sitting Clap`, `Sitting Yell`, `Sitting Disapproval`, `Beckoning` („Waving Someone Over While Seated“, 79), `Pointing` („Pointing While Seated“, 104).
- `Sitting Drinking` („Having A Seat And Drinking A Canned Beverage“, 457) a `Drinking` („Male Drinking“, 267) – pití; **jídlo (eating) v indexu není**.
- Přechody: `Stand To Sit` (68), `Sit To Stand` (69), `Stand Up` („Standing Up From Seated Position“, 146); na zemi `Sitting Idle` („Sitting On The Floor“ 327 / „Reclined“ 309), `Sitting` („Sitting Cross Legged“, 288).
- Opilci: `Drunk Idle`, `Drunk Idle Variation` (hiccup/stumble), `Drunk Walk` (91), `Drunk Turn` aj.

**Stání, opírání, klečení, spánek**
- `Leaning` („Leaning Square Against A Wall With One Leg Up“, 101; a 2-snímková póza „…With Shoulders Against A Wall“), `One Shoulder Lean` („Leaning Against A Wall With Various Postures“, 61), `Male Standing Pose` „Legs Crossed, Leaning On Object“ / „Left Elbow Resting On Object“ (pózy 2 sn.).
- `Standing Arguing` (1009, 823), `Talking At Watercooler` („Having A Chat At The Watercooler“, 1338 – stání ve dvojici u studny), `Talking` („General Conversation“ 309, „Asking A Question…“).
- `Kneeling` („Kneeling On One Knee Idle“, 141), `Kneeling Idle` (129), `Kneeling Down` (84), `Kneel` („Kneeling Warming Hands Over Campfire“, 325 – u ohniště!), `Praying` (5 variant vč. „Kneeling In Prayer“ – kaple).
- `Sleeping Idle` („Sleeping Deeply“ 207 / „Restless Sleeping“ 578), `Laying Sleeping` („Laying Asleep On A Bed“, 52), `Yawn` (251), `Wiping Sweat` (80), `Arm Stretching` (267), `Neck Stretching` (97), `Sad Idle`, `Quick Formal Bow`/`Quick Informal Bow` (83 – úklona pánovi).
- Pochodeň: `Standing Torch Light Torch From Wall` (134), `Crouch Torch …` sada.

**Licence Mixamo**
- Postavy i animace jsou royalty free pro osobní, komerční i neziskové projekty, výslovně „Create video games“; stačí Adobe ID — [Adobe Mixamo FAQ](https://helpx.adobe.com/en/creative-cloud/faq/mixamo-faq.html).
- Nesmí se šířit surové soubory (FBX) mimo tým; ve hře zabudované je OK; atribuce nepovinná; zákaz trénování ML — [Adobe community Mixamo FAQ](https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/td-p/13234775).
- Knihovna má „přes 2 000“ animací, řazeno podle žánru + vyhledávání — [School of Motion](https://schoolofmotion.com/blog/why-mixamo-is-still-one-of-the-best-animation-resources).

### Inferences
- Pro práce, které Mixamo nemá, je pořadí: UAL1/2 (stejná kostra jako postavy, `TreeChopping_Loop`, `Farm_Harvest`, `Fixing_Kneeling` – viz `docs/modely_misa.md`) → CMU (projekt už používá 79_01 „chopping wood“ pro kováře, 79_04 digging) → teprve ruční klíčování v Blenderu. Zametání a krmení drůbeže pravděpodobně skončí ručním klipem nebo úpravou (např. `Pull Plant` stojící + koště). 
- Licence Mixamo zakazuje šířit FBX → **`tools/postavy_q/mixamo/*.fbx` v repu, pokud je repo veřejné, je v rozporu s FAQ** (repo `baran1-ship-it/tvrz-claude` – ověřit viditelnost); ve hře zabudované .res/.glb jsou v pořádku.
- Mixamo klipy „In Place“ + vlastní posun postavy je pro NPC jednodušší než root motion (projekt to už tak dělá u UAL).
- Dlouhé klipy (Sitting Talking 1 323 sn. ≈ 44 s) zvětší APK; zvážit zkrácení na smyčku 8–12 s při importu.

### Gaps
- Index je třetí strana (HF, 2 446 položek); Mixamo nemá veřejný seznam. Shoda s živým katalogem 11/2026 NEOVĚŘENA – agent se na mixamo.com nepřihlásí (API 403, viz `docs/predani.md`). Pokud Míša najde „Hammering“/„Sweeping“, index je neúplný.
- Neověřeno, zda v Mixamo existuje klip jedení („Eating“) – v indexu není.

## Které volné balíky nabízejí středověké pracovní animace s licencí pro komerční hru?

### Takeaway
Bezpečné a bez atribuce: **Quaternius UAL1 + UAL2 (CC0)** – stejná kostra jako Quaternius postavy, UAL2 má farmaření a rybaření.
Mixamo (vlastní licence, bez atribuce, nešířit FBX). Rokoko Motion Library má zdarma ~150 mocapů pro komerční užití.
**Bandai Namco dataset je NC (nekomerční) → pro hru nepoužít.** CMU mocap už projekt používá.

### Cited Findings
- **Quaternius Universal Animation Library 2**: CC0, „free to use in personal, educational and commercial projects“; 130+ animací na univerzálním humanoidním rigu; kategorie boj (kombo 3–4 úderů rozdělené na údery), parkour, **farmaření, rybaření**, zombie; formáty FBX/GLB/Blend; Standard zdarma = 60–70 % balíku, Source (.blend s rigem) placený — [Quaternius UAL2](https://quaternius.com/packs/universalanimationlibrary2.html); [itch.io UAL2](https://quaternius.itch.io/universal-animation-library-2); [OpenGameArt UAL2 (CC0)](https://opengameart.org/content/universal-animation-library-2).
- **Quaternius UAL1**: CC0, 120+ animací – lokomoce v 8 směrech, jog, sprint, push, plazení, plavání, sezení, smrt, boj, emoce; „ready for retargeting“ — [Quaternius UAL1](https://quaternius.com/packs/universalanimationlibrary.html). Godot Asset Store verze: CC0, kompatibilní s Mixamo rigem; recenzent uvádí, že kost UpperChest se ve většině animací ohýbá příliš (neověřeno) — [Godot Asset Store UAL](https://store.godotengine.org/asset/quaternius/universal-animation-library/).
- Seznam klipů a viewer: [quaternius.com/animviewer.html](https://quaternius.com/animviewer.html) (odkaz z OpenGameArt). Projektová data: UAL1/UAL2 Standard = 43 + 43 klipů, 66 kostí = rig Base Characters, varianty `_RM` s root motion; použitelné práce `Farm_Harvest` (srp), `Farm_PlantSeed`, `Farm_Watering`, `TreeChopping_Loop`, `Fixing_Kneeling`, `Push_Loop`, `Walk_Carry_Loop`, `Sitting_*`, `Idle_Talking_Loop`, `Idle_Lantern_Loop`; chybí zametání, kosa, kovadlina — `docs/modely_misa.md` (ř. 17–22).
- Pozor z projektu: `TreeChopping_Loop` je sek jednou rukou (ruce 0,94–1,23 m od sebe) – na obouruční nástroj nesedí; importér Godotu odřízne `_Loop` z názvu klipu — `docs/predani.md` (ř. 274, 924–927).
- **Rokoko Motion Library**: 150 pohybů zdarma (2020), „licensed for use in commercial projects“ — [CG Channel 2020](https://www.cgchannel.com/2020/03/get-150-free-mocap-moves-from-rokokos-motion-library); ceník: animace „for free or at low cost“, export a užití „including commercial ones“ — [Rokoko pricing](https://rokoko.com/pricing/).
- **Bandai Namco Research Motiondataset**: README uvádí CC BY-NC 4.0 (skript MIT) — [GitHub README](https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset/blob/master/README.md); dřívější zpráva uvádí CC BY-NC-ND 4.0 a „nelze komerčně“ — [AUTOMATON 2022](https://automaton-media.com/en/news/20220430-12213/). Obsah: 17 typů (denní činnosti, boj, tanec) v 15 stylech, 36 673 snímků (Dataset-1).
- **Quaternius Modular Character Outfits – Fantasy** je kompatibilní s UAL (viz část B) — [itch.io](https://quaternius.itch.io/modular-character-outfits-fantasy).

### Inferences
- Pro tablet a jednu kostru: UAL zůstává páteř (bez retargetu, stejné kosti); Mixamo doplňuje jen to, co UAL nemá (kosa, trakař, hospoda, studna/lano, opírání), přes retarget při importu.
- Bandai Namco: NC = vyloučeno bez ohledu na ND spor.

### Gaps
- Úplný seznam klipů UAL2 Standard (které farmářské klipy jsou zdarma) se z webu nepodařilo získat (stránka je jen obrázky/viewer); v projektu je lokálně v `modely/postavy/anim/UAL2.glb`.
- **ActorCore free packy, Kenney animace, Unity Asset Store / Fab volné „medieval/peasant animations“, Sketchfab animace**: v rámci rozpočtu nedohledáno ze spolehlivých zdrojů – licence a názvy NEOVĚŘENY. Fab/Unity licence obecně omezují užití na daný engine (Unity EULA / Fab Standard License) – NEOVĚŘENO pro Godot, nutné číst licenci konkrétního balíku.
- **CMU mocap**: licenci jsem v této rešerši znovu neověřoval (projekt ji už používá; index `github.com/una-dinosauria/cmu-mocap`). CMU nemá prsty a natočení dlaní (`docs/predani.md` ř. 928).
- Rokoko: aktuální znění licence jednotlivých free klipů nečteno (zdroje 2020 + ceník).

## Jak v Godotu 4.4.1 udělat vrstvené modulární oblečení + pružné kosti levně na mobilu?

### Takeaway
**Velká oprava dřívější rešerše:** `SpringBoneSimulator3D` **JE v Godotu 4.4** (ne až 4.5) – je v dokumentaci 4.4, v poznámkách
k vydání 4.4 („Jiggle physics“) a **v binárce projektu `godot 4.4.1.stable.official.49a5bc7b6`** (třídy SpringBoneSimulator3D,
SpringBoneCollisionSphere3D/Capsule3D/Plane3D). Addon není potřeba. Oblečení: jedna Skeleton3D, tělo + kusy oděvu jako
samostatné MeshInstance3D se stejným skinem, zakryté části těla odstranit už v Blenderu (ne alfa), a pro NPC v dálce kusy
sloučit do jednoho meshe/jedné surface s atlasem.

### Cited Findings
**Pružné kosti**
- Dokumentace 4.4 obsahuje `SpringBoneSimulator3D` (stránka „Godot Engine 4.4 documentation“); nastavení = `setting_count`, pro každý řetěz root/end kost, stiffness, drag, gravity, radius, rotation axis, end bone direction/length, extend end bone, individual config; křivky útlumu podél řetězu; potomci `SpringBoneCollision3D` nezávislí na PhysicsServer3D; varování „A scaled SpringBoneSimulator3D will likely not behave as expected“; `reset()` proti „violent“ simulaci po skoku pózy — [Godot 4.4 docs SpringBoneSimulator3D](https://docs.godotengine.org/en/4.4/classes/class_springbonesimulator3d.html). Stránka pro 4.3 vrací 404 (ověřeno curl) → nové v 4.4.
- Poznámky k vydání 4.4, oddíl „Jiggle physics“: animační tým přepracoval MIT kód addonu VRMSpringBone na SkeletonModifier3D — [Godot 4.4 release](https://godotengine.org/releases/4.4/); totéž [GameFromScratch „Godot 4.4 Gets Jiggle Physics“](https://gamefromscratch.com/godot-4-4-gets-jiggle-physics/).
- Rozpor: blog o IK píše „In Godot 4.5, I implemented SpringBoneSimulator3D and BoneConstraint3D“ — [Godot blog IK 4.6](https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/); dokumentace 4.4, release notes 4.4 i binárka 4.4.1 to vyvracejí (pravděpodobně v 4.5 přibyl BoneConstraint3D / úpravy). **`docs/rozpracovane/reserse_postavy_kcd2.md` ř. 287 a 297 („až v 4.5“) je třeba opravit.**
- Alternativy addonů: `detomon/wigglebone` (MIT, SkeletonModifier3D, vyžaduje 4.3, rotační a poziční varianta) — [awesome.ecosyste.ms wigglebone](https://awesome.ecosyste.ms/projects/github.com%2Fdetomon%2Fwigglebone); `yaelatletl/godot-jigglebones` (Godot 4.x, volitelné kolizní tvary pro pláště, copy) — [GitHub](https://github.com/yaelatletl/godot-jigglebones); JiggleBones (4.0) — [Asset Library](https://godotengine.org/asset-library/asset/1595).
- Návrh SkeletonModifier3D (pořadí modifikátorů pod Skeleton3D) — [Godot blog design of SkeletonModifier3D](https://godotengine.org/article/design-of-the-skeleton-modifier-3d/).

**Retarget Mixamo → kostra UAL (Godot 4.4)**
- BoneMap + `SkeletonProfileHumanoid` (automapování podle anglických jmen kostí; barevná varování u chybějících/duplicitních kostí neblokují import, ale animace nemusí sedět); referenční póza T-póza, +Z dopředu; volby: Apply Node Transform (neaplikované transformace z Blenderu), **Overwrite Axis** (nejdůležitější pro sdílení), Fix Silhouette (A→T póza, filtrovat chodidla při podpatcích), **Normalize Position Tracks** (`motion_scale` podle výšky Hips – méně klouzání nohou), Remove Tracks: Except Bone Transform / **Unimportant Positions** (pozice jen root + hips) / **Unmapped Bones** (pro sdílené AnimationLibrary; u scén s animovanými doplňky je zabije); Unique Node + `skeleton_name` aby cesty stop nezávisely na hierarchii — [Godot 4.4 docs Retargeting 3D skeletons](https://docs.godotengine.org/en/4.4/tutorials/assets_pipeline/retargeting_3d_skeletons.html).
- Mixamo je jen pro dvounohé humanoidy — [Adobe community FAQ](https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/td-p/13234775).

**Slučování meshů (draw cally)**
- Hotové addony slučují jen statické meshe (Static Mesh Merger) — [Asset Library 5429](https://godotengine.org/asset-library/asset/5429); MeshMerger uvádí Skeleton3D/skinned jako nepodporované — [MeshMerger-Godot](https://gh.r-mj.com/necat101/MeshMerger-Godot); Material Merger tvrdí, že zachová bone indices/weights (neověřeno) — [Material-Merger-Godot](https://gh.r-mj.com/necat101/Material-Merger-Godot).
- Každá surface = samostatný draw call i po sloučení do jednoho ArrayMesh; řešení jedna surface + atlas/jeden materiál — [Godot forum: limiting draw calls](https://forum.godotengine.org/t/limiting-draw-calls-by-combining-meshes/77302); [Understanding batching in Godot 4](https://forum.godotengine.org/t/understanding-batching-in-godot-4/65635).
- V-Sekai „splerger“ (dělení/slučování meshů, V-Sekai skupina) — [awesome.ecosyste.ms splerger](https://awesome.ecosyste.ms/projects/github.com%2Fv-sekai%2Fv-sekai.splerger).

**Volné modulární oblečení**
- **Quaternius Modular Character Outfits – Fantasy**: CC0, 12 oblečení z 62 modulárních dílů (u Source obrázku 82 – nesoulad), 3 barevné textury na oblek, humanoidní rig kompatibilní s UAL, funguje s hlavou Universal Base Character; od v2.0 všechny modely jen s hlavou Base Character, `Peasant_Male` obsahuje lidské paže; tagy Medieval/Knight/Peasant; **Standard zdarma obsahuje Ranger a Peasant**, Source ($20+) rigované .blend — [itch.io](https://quaternius.itch.io/modular-character-outfits-fantasy); [Quaternius](https://quaternius.com/packs/modularcharacteroutfitsfantasy.html). Projekt balík má na Disku (`docs/modely_misa.md` ř. 13).
- Balík „Ultimate Modular Men/Women“ od Quaternius jsem nenašel (vyhledávání vrací jen Outfits Fantasy a starší „Modular RPG characters“ na [OpenGameArt](https://opengameart.org/content/modular-rpg-characters)).
- Placené středověké sady existují (CGTrader „Medieval male/female outfits pack“, Unity „Modular Addon Medieval Dresses“) — [CGTrader](https://www.cgtrader.com/3d-models/character/clothing/medieval-male-outfits-pack), [Unity](https://marketplace.unity.com/packages/3d/characters/modular-addon-medieval-dresses-315790); licence/cena nečteny.

### Inferences
Doporučený postup (úvaha, NEOVĚŘENO na tabletu):
1. **Jedna kostra** (UAL/Base Character, 66 kostí) + přidané sekundární kosti jen tam, kde je třeba: sukně/zástěra 4–6 řetězů × 2–3 kosti od Hips, plášť 3–5 řetězů od Spine2/ramen, kapuce/cop 1 řetěz. Kosti přidat v Blenderu do rigu postav, animace z UAL/Mixamo je neovlivní (nejsou v BoneMap → u sdílené knihovny „Remove Unmapped Bones“ jejich stopy odstraní, simulace je ovládá).
2. **Váhy**: sukně = Hips + vlastní sukňové kosti, **ne stehna** (jinak se sukně trhá s nohou a proniká); jen spodní lem může mít malý podíl stehna u úzkých sukní; zástěra = Spine/Hips + 1 řetěz; rukávy a kabátec podle těla (kopírovat váhy z těla – Blender Data Transfer – pak sukňovou část přepsat). Kolize nohou řešit `SpringBoneCollisionCapsule3D` na stehnech (2 kapsle), ne fyzikou.
3. **Maskování těla**: části těla pod oděvem smazat v Blenderu podle varianty (tělo rozdělené na zóny trup/paže/stehna/lýtka; každý kus oděvu nese seznam zón, které skrývá → sestavení vynechá zóny) – žádný alpha discard (tablet: early-Z, overdraw). Quaternius `Peasant_Male` už má paže, tj. je to „oděv + odkrytá kůže“ v jednom meshi.
4. **Sloučení**: v Blenderu (export) nebo při načtení v GDScriptu přes `SurfaceTool`/`ArrayMesh` sloučit tělo + oděv jedné postavy do **jedné surface s texturovým atlasem** (kosti/váhy se kopírují, protože kostra je stejná) → 1 draw call na NPC místo 4–6. Hotový addon pro skinned merge v Godotu jsem nenašel; Material Merger netestován.
5. **SpringBoneSimulator3D** jen pro blízké NPC (LOD: zapnout ve vzdálenosti < ~15 m, dál `active = false`; číslo NEOVĚŘENO) a jen pro 1–2 řetězce na postavu; volat `reset()` po teleportu/změně animace skokem. Neškálovat uzel (varování v docs).
6. Pozor na pořadí modifikátorů: SpringBone až po AnimationTree/LookAt pod Skeleton3D.

### Gaps
- Cena SpringBoneSimulator3D na Mali/Adreno – žádné měření nenalezeno → NEOVĚŘENO, změřit Měřicí trasou se 5/10/20 NPC.
- Spolehlivý návod na slučování skinned meshů v Godotu 4 za běhu (zachování `Skin` a bind pose) nenalezen – nutný vlastní test.
- Rozdíl API SpringBoneSimulator3D 4.4 → 4.5 (např. `external_force` na stránce 4.4 chybí) neprozkoumán.
