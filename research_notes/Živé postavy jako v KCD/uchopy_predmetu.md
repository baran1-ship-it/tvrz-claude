# Úchopy předmětů v rukou animovaných postav (kladivo, krumpáč, srp, vědro, korbel, podnos, lucerna, louč) – praxe her a Godot 4.4

Poznámka ke zdrojům: dokumentace docs.godotengine.org vracela při rešerši HTTP 429, proto jsou třídy Godotu 4.4 citovány
přímo ze zdrojového XML referenční dokumentace větve `4.4-stable` na GitHubu (je to tentýž text, ze kterého se generuje
docs.godotengine.org/en/4.4). Projekt už má `scripts/uchop.gd` (SkeletonModifier3D s režimy „visi“, „svisle“,
„druha_ruka“ a sevřením prstů) a `tools/test_drzeni.gd`; závěry níže jsou psány tak, aby šly porovnat s tímto stavem.

## 1. Jaký je standardní postup pro předměty v rukou (kost/socket + offset úchopu + póza prstů)?

### Takeaway
Standard v průmyslu: předmět je dítětem „socketu“ (kost ruky nebo zvláštní kost/virtuální kost pro zbraň, např.
`ik_hand_gun` v UE mannequinu), na předmětu je definovaný bod úchopu (socket/marker na předmětu) a offset patří k předmětu,
ne k postavě; druhá ruka se k předmětu dotahuje two‑bone IK na socket na předmětu; prsty se řeší pózou úchopu míchanou
jen na kosti ruky. V Godotu 4.4 tomu odpovídá BoneAttachment3D (+ Marker3D úchopu na předmětu) a vlastní
SkeletonModifier3D běžící po animaci.

### Cited Findings
- UE mannequin: kost `ik_hand_gun` slouží jako rodičovská kost zbraně („VB ik_hand_gun acts as the weapon parent bone“);
  `ik_hand_l`/`ik_hand_r` jsou cíle, ke kterým se ruce dotahují two‑bone IK přes virtuální kosti —
  [Kinemation FPS Animation Pack docs](https://kinemation.gitbook.io/fps-animation-pack-unreal/animations/character);
  [Reallusion forum](https://forum.reallusion.com/513711/We-Need-Unreal-Engine-IK-Bone-Support)
- Typické použití: zbraň zavěšená na `ik_hand_weapon/gun`, levá ruka volná (např. pro přebíjení) — [UE forum: mannequin hand IK confusion](https://forums.unrealengine.com/t/mannequin-hand-ik-confusion/56882);
  Epic API uvádí `ik_hand_gun`, `ik_hand_l`, `ik_hand_r` jako IK kosti umísťované na ruce — [Epic Python API UpdateIKBones](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AnimDatabaseFunction_UpdateIKBones)
- Obvyklý postup pro druhou ruku: socket na zbrani v místě úchopu druhé ruky → transformace do prostoru kosti → Two Bone IK
  s tímto cílem; doporučeno mít stejný název socketu na všech zbraních — [UE forum: Weapons and Hand Placement](https://forums.unrealengine.com/t/weapons-and-hand-placement/12801);
  [UE forum: left hand IK](https://forums.unrealengine.com/t/left-hand-ik/350399)
- Unity Animation Rigging Two Bone IK: Root/Mid/Tip, Target (kam má jít konec), Hint (směr ohybu lokte),
  váhy pro polohu a natočení cíle, „Maintain Target Offset“ — [Unity Two Bone IK constraint](https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/constraints/TwoBoneIKConstraint.html)
- Godot 4.4 BoneAttachment3D: „dynamically copies or overrides the 3D transform of a bone“; vlastnosti `bone_name`,
  `bone_idx`, `override_pose`, externí kostra; pozor: `override_pose` „performs interruptively in the skeleton update
  process using signals due to the old design. It may cause unintended behavior when used at the same time with
  SkeletonModifier3D“ — [BoneAttachment3D.xml 4.4-stable](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/doc/classes/BoneAttachment3D.xml)
- Transformace BoneAttachment3D = světová transformace kosti × lokální transformace dítěte; doporučení ladit lokální offset
  a ukládat ho u předmětu (sub‑resource zbraně), ne u postavy — [bugnet.io: bone attachment offset](https://bugnet.io/blog/fix-godot-mesh-instance3d-skeleton-bone-attachment-offset) (blog, ne oficiální)
- Kost ruky (Mixamo) začíná v zápěstí, ne uprostřed dlaně, proto je vždy potřeba posun ke středu sevřené pěsti — [three.js forum: adding weapon to hand](https://discourse.threejs.org/t/adding-weapon-to-character-hand/30702.md)
- Prsty: animace s prázdnou rukou obsahují pohyb prstů, takže úchop potřebuje vlastní pózu ruky — [Bevy issue 14395](https://github.com/bevyengine/bevy/issues/14395);
  v Godotu se póza míchá přes Blend2 s filtrem kostí („Enable Filtering… only those bones will be affected“) —
  [Godot forum: Edit Filters](https://forum.godotengine.org/t/edit-filters-in-animationtree-nodes-not-working-as-expected/65287);
  [Godot forum: upper/lower body bone filters](https://forum.godotengine.org/t/mixing-two-animations-with-bone-filters-for-upper-lower-body-of-armature/117058)

### Inferences
- Pro Odkaz Havrana: každý předmět = záznam s (a) bodem úchopu hlavní ruky (Marker3D „grip_r“ v modelu předmětu nebo
  souřadnice v `postavy.json drzeni.<id>`), (b) volitelným bodem druhé ruky („grip_l“), (c) osou rukojeti, (d) typem
  sevření prstů (válec silný/tenký, ucho, podnos plochou dlaní). To odpovídá „offset patří k předmětu“ a souhlasí se
  stávajícím `drzeni.<id>` v datech (pravidlo „záplatování zakázáno“ – vše v záznamu, ne v kódu).
- Pozice předmětu se má počítat tak, aby **bod úchopu předmětu = bod úchopu ruky** (marker v dlani, posunutý od kosti
  zápěstí), ne „předmět v počátku kosti + ruční offset“.

### Gaps
- Nenašel jsem veřejný GDC/blog text konkrétního studia (KCD2/Warhorse, Naughty Dog) popisující jejich pipeline úchopů;
  výše jsou dokumentace enginů a komunitní fóra.

## 2. Jak řešit stejný předmět v různých klipech (chůze × práce) bez přeautorování?

### Takeaway
Hlavní příčina „v jednom klipu sedí, v jiném je předmět zkroucený“ u Mixamo je různé natočení (bone roll) kosti ruky
v různých stahováních; doložené řešení je sjednotit klidové pózy při importu (BoneMap → SkeletonProfileHumanoid,
Rest Fixer „Overwrite Axis“), pak stačí jeden offset na předmět. Zbytek (věci visící, svislé, obouruční) se řeší
procedurálně po animaci (SkeletonModifier3D), případně animovanou stopou na uzlu úchopu u specifických klipů.

### Cited Findings
- Mixamo „bakes the source character's bone rolls into the animation tracks“; pevně připojená zbraň „looked correctly held
  in one animation but visibly twisted in another“, rozdíl báze ruky mezi dávkami až ~130°; řešení autora: BoneMap na
  SkeletonProfileHumanoid s Rest Fixer „Overwrite Axis“ na všech modelech i animačních FBX → „one shared hand basis“,
  jeden kalibrovaný offset pro všechny klipy — [Godot forum: best practice attaching weapons across many animations](https://forum.godotengine.org/t/best-practice-for-attaching-weapons-items-to-a-characters-hand-across-many-animations-godot-4/141270)
  (jeden autor, bez odpovědí – praktická zkušenost, ne oficiální doporučení)
- Godot docs: modely mají různé Bone Rest podle exportéru (Blender glTF používá „Edit Bone Orientation“); Overwrite Axis
  „unifies the models' Bone Rests by overwriting them to match the reference poses defined in the SkeletonProfile“;
  referenční póza SkeletonProfileHumanoid je T‑póza, +Z dopředu, Y nahoru; fitting siluety „may not work for fixing bone
  roll“ — [Retargeting 3D Skeletons (4.4)](https://docs.godotengine.org/en/4.4/tutorials/assets_pipeline/retargeting_3d_skeletons.html);
  [italská verze 4.4 s pravidly Rest Fixer](https://docs.godotengine.org/it/4.4/tutorials/assets_pipeline/retargeting_3d_skeletons.html)
- Alternativa z jiných enginů: vložit do Mixamo kostry zvláštní „WeaponGrip“ kost a ručně ji upravovat per klip –
  autor sám označuje za „very tedious and manual“ — [Babylon.js forum](https://forum.babylonjs.com/t/parenting-weapon-node-to-character-node-on-gltf-imported-assets/56924)
- Godot 4.4 RetargetModifier3D (zachovává klidové pózy) a LookAtModifier3D přibyly ve 4.4 spolu s bází SkeletonModifier3D
  — [Godot blog: IK returns to Godot 4.6 (přehled verzí)](https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/)
- SkeletonModifier3D: „If there is AnimationMixer, modification always performs after playback process“; pořadí modifikátorů
  = pořadí dětí Skeleton3D; modifikace je dočasná a aplikuje se na 100 %, prolínání dělá `influence` —
  [SkeletonModifier3D.xml 4.4-stable](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/doc/classes/SkeletonModifier3D.xml);
  [Design of the Skeleton Modifier 3D](https://godotengine.org/article/design-of-the-skeleton-modifier-3d/)
- Modifikovanou pózu číst jen v signálu `modification_processed` (resp. `Skeleton3D.skeleton_updated` po všech
  modifikátorech) — [SkeletonModifier3D.xml](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/doc/classes/SkeletonModifier3D.xml);
  [Skeleton3D.xml 4.4-stable](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/doc/classes/Skeleton3D.xml)

### Inferences
- Pořadí v projektu: AnimationTree → `uchop.gd` (natočení ruky/předmětu, IK druhé ruky, prsty) → BoneAttachment3D čte
  výslednou pózu. BoneAttachment3D s `override_pose=false` je bezpečné; `override_pose=true` spolu s modifikátory nepoužívat.
- Per‑klip korekce (výjimky, např. kování, sekání) autorovat jako záznam „drzeni.<id>.klipy.<klip>“ v datech (offset,
  váha IK druhé ruky, režim), nebo jako stopu animace na uzlu úchopu / na `influence` modifikátoru (AnimationPlayer umí
  animovat libovolnou vlastnost uzlu). To je inference; žádný zdroj nepředepisuje konkrétní formát.
- Pokud projekt neimportuje Mixamo klipy přes BoneMap + Overwrite Axis, je to první podezřelý zdroj „zkrouceného předmětu
  v jiném klipu“ – ověřit porovnáním báze `RightHand` ve dvou klipech (měření, ne odhad).

### Gaps
- Skutečné lokální osy `mixamorig:RightHand` jsem nenašel ve spolehlivém zdroji (fóra se rozcházejí; Blender dává Y podél
  kosti, roll určuje X/Z — [Babylon.js forum](https://forum.babylonjs.com/t/issues-with-x-rotation-in-skeleton-when-using-mixamo-animations/53631)). Nutno změřit v projektu.

## 3. Jaké uzly/API Godotu 4.4 a komunitní doplňky pro IK a připojení existují, a jak jsou na tom na mobilu?

### Takeaway
Ve 4.4 je jádrem SkeletonModifier3D (vlastní `_process_modification`), BoneAttachment3D, LookAtModifier3D (≈ jednokostní
IK, natočení kosti/hlavy), RetargetModifier3D; SkeletonIK3D (FABRIK) je **zastaralý**. Vestavěné TwoBoneIK3D/FABRIK3D/
CCDIK3D přišly až v 4.6, BoneConstraint3D a SpringBoneSimulator3D v 4.5. Pro 4.4 je nejjednodušší a nejlevnější
vlastní analytické two‑bone IK v SkeletonModifier3D (pár desítek řádků, deterministické), případně GodotIK (GDExtension).

### Cited Findings
- SkeletonIK3D je v 4.4 označen `deprecated`; interně FABRIK; `interpolation` zastaralé („Use SkeletonModifier3D.influence
  instead“); popis výslovně uvádí scénář „character's hands on a currently held object“ — [SkeletonIK3D.xml 4.4-stable](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/doc/classes/SkeletonIK3D.xml)
- SkeletonModifier3D: „should be used to implement custom IK solvers, constraints, or skeleton physics“;
  `_process_modification` nesmí sám aplikovat influence — [SkeletonModifier3D.xml](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/doc/classes/SkeletonModifier3D.xml)
- Update kostry je odložené volání „performed only once per frame“; pokud modifikátor ovlivňuje uzel z physics procesu,
  nastavit `modifier_callback_mode_process` na Physics — [Design of the Skeleton Modifier 3D](https://godotengine.org/article/design-of-the-skeleton-modifier-3d/);
  [Skeleton3D.xml](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/doc/classes/Skeleton3D.xml)
- LookAtModifier3D (4.4): natáčí kost k cíli („moving a character's head to look at the player“), `forward_axis`,
  `primary_rotation_axis`, `origin_from`/`origin_offset`, úhlové limity, časová interpolace `duration`; víc LookAt
  modifikátorů: rodičovská kost musí být v seznamu výš — [LookAtModifier3D.xml 4.4-stable](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/doc/classes/LookAtModifier3D.xml)
- Verze: 4.4 = SkeletonModifier3D, LookAtModifier3D, RetargetModifier3D; 4.5 = SpringBoneSimulator3D, BoneConstraint3D
  (Aim/ConvertTransform/CopyTransform); 4.6 = IKModifier3D: TwoBoneIK3D, ChainIK3D, SplineIK3D, FABRIK3D, CCDIK3D,
  JacobianIK3D; TwoBoneIK3D a SplineIK3D jsou deterministické; deterministické IK „cannot avoid causing rotation with
  large angular velocities“ → LimitAngularVelocityModifier3D — [Godot blog: IK returns in 4.6](https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/)
- TwoBoneIK3D (4.6): průsečík dvou kružnic, vyžaduje pole target, root/middle/end kost, cíl a pól — [TwoBoneIK3D 4.6](https://docs.godotengine.org/en/4.6/classes/class_twoboneik3d.html)
- GodotIK (monxa): GDExtension pro Godot 4.3+, FABRIK (poziční, twist dopočítán), uzly GodotIK (SkeletonModifier),
  GodotIKEffector, GodotIKConstraint (Pole/Straight/Smooth/MaxRotation), MIT; README neuvádí výkon ani Android binárky —
  [GitHub monxa/GodotIK](https://github.com/monxa/GodotIK)
- many_bone_ik (V‑Sekai, EWBIK): multi‑chain IK s omezeními, MIT; V‑Sekai chtěli nahradit FABRIK v RenIK kvůli kvalitě,
  později návrh řešit RenIK přímo — [V-Sekai decisions: walking controller/RenIK](https://v-sekai.github.io/manuals/decisions/20230106-walking-controller-renik.html);
  [V-Sekai: solve RenIK directly](https://v-sekai.github.io/manuals/decisions/20230726-solve-renik-directly-rather-than-many-bone-ik.html);
  [awesome.ecosyste.ms many_bone_ik](https://awesome.ecosyste.ms/projects/github.com%2FV-Sekai%2Fmany_bone_ik)
- Starší komunitní XR/avatar řešení používají IK z doby před SkeletonModifier3D a nejsou udržovaná — [Godot forum: XR puppet](https://forum.godotengine.org/t/whats-the-best-way-to-puppet-a-character-using-my-xr-headset-and-controller-movements-ive-researched-a-couple-of-options-but-really-needing-advise/126410)

### Inferences
- Pro mobil a Godot 4.4: analytické two‑bone IK (zákon kosinů + pól/hint) je O(1) na ruku, bez iterací; iterativní
  FABRIK/EWBIK jsou pro ruku s předmětem zbytečné. GDExtension (GodotIK, many_bone_ik) přidává nativní knihovnu pro
  Android arm64, kterou je třeba sestavit/ověřit – vyšší riziko než ~50 řádků GDScriptu.
- Výkon: modifikátor vypínat mimo blízkost hráče (`active=false`) – projekt to už dělá (`uchop.gd` `zapni()` podle
  `anim_do_m`). Cena na zařízení: NEOVĚŘENO (nenašel jsem měření; nutno změřit Měřicí trasou).
- Přechod na 4.6 by dal hotové TwoBoneIK3D + BoneConstraint3D(Node3D cíl) + SpringBoneSimulator3D (4.5) – to je
  rozhodnutí o upgradu enginu, ne o úchopech.

### Gaps
- Repozitáře RenIK a many_bone_ik jsem nemohl otevřít (přístup GitHub API v této session zakázán); stav údržby a podpora
  Godot 4.4/Android neověřeny.
- Žádné zveřejněné měření ceny SkeletonModifier3D/IK na Android zařízení jsem nenašel.

## 4. Jak opravit druhou ruku u obouručních nástrojů (krumpáč, perlík, kosa) a jak řešit vědro, podnos/korbel, louč?

### Takeaway
Druhá ruka: bod úchopu na předmětu (marker na topůrku/kosišti) → po animaci two‑bone IK nadloktí–předloktí–ruka s cílem
= bod úchopu, pól = směr lokte z animace (loket ven/dolů), natočení ruky dorovnat podle osy rukojeti; IK počítat ve
**stejném** průchodu modifikátoru jako umístění předmětu, jinak ruka zaostává o snímek (známý problém UE). Vědro/lucerna
visí svisle z bodu úchopu s kyvadlem; podnos/korbel = předmět vodorovně (svět‑orientace) s rukou dorovnanou k němu;
louč = svisle plamenem nahoru. Automatický test: vzdálenost dlaň–rukojeť a úhel osy rukojeti vůči ose sevřené pěsti.

### Cited Findings
- Dvouruční nástroje v UE: socket na zbrani pro druhou ruku jako efektor Two Bone IK; jeden uživateli pomohla virtuální
  kost jako efektor + „take rotation from effector space“ + ruční offset jako dlaň — [UE forum: Weapons and Hand Placement](https://forums.unrealengine.com/t/weapons-and-hand-placement/12801/9);
  [UE forum: dynamic two-handed melee left hand](https://forums.unrealengine.com/t/handling-left-hand-for-dynamic-two-handed-melee-animations/2695878)
- Známý problém: cíl IK brán ze socketu je „one frame behind“ — [UE forum: left hand IK not updating](https://forums.unrealengine.com/t/stumped-left-hand-ik-not-updating-when-i-move-the-socket/2209450)
- Hint/pól určuje směr ohybu končetiny; bez něj se loket může otočit špatně — [Unity Two Bone IK](https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/constraints/TwoBoneIKConstraint.html);
  TwoBoneIK3D v 4.6 pól vyžaduje — [TwoBoneIK3D 4.6](https://docs.godotengine.org/en/4.6/classes/class_twoboneik3d.html)
- Houpání (vědro): SpringBoneSimulator3D (4.5) dává setrvačné kývání řetězci kostí kořen→konec, nepodporuje větvení,
  kostra se nemá škálovat — [SpringBoneSimulator3D 4.5](https://docs.godotengine.org/en/4.5/classes/class_springbonesimulator3d.html);
  ve 4.4 není k dispozici (přibyl v 4.5) — [Godot blog: IK returns 4.6](https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/)
- Deterministické IK může dávat velké úhlové rychlosti (cukání) → omezit úhlovou rychlost — [Godot blog](https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/)

### Inferences
- **Krumpáč/perlík/kosa**: hlavní (horní nebo dolní dle nástroje) ruka nese předmět přes kost ruky + marker; druhá ruka
  IK na marker „grip_l“. U kosy jsou úchyty (kolíky) pevné body na kosišti – dva markery. Pól: z animované pozice lokte
  (zachová styl klipu). Váha IK (`influence` nebo vlastní váha na ruku) animovatelná per klip – při chůzi s krumpáčem
  přes rameno 0, při práci 1. Rotace ruky po IK: osa sevřené pěsti (prsty kolem) || osa rukojeti.
- **Vědro (nesené za ucho při chůzi)**: paže visí z animace (Mixamo „carry“/„walk“), předmět se nevěší pevně na ruku, ale
  bod ucha = bod úchopu a předmět visí ve směru tíže (to `uchop.gd` „visi“ už dělá); kývání = tlumené kyvadlo na úhlu
  předmětu (2 stavy na předmět, pružina + tlumení, buzení zrychlením ruky). Ve 4.4 v GDScriptu v modifikátoru nebo na
  uzlu předmětu; ve 4.5+ by šlo SpringBoneSimulator3D, ale jen pokud je vědro kostí v kostře.
- **Podnos/korbel (obsluha)**: předmět udržovat v orientaci světa (dno vodorovně) jako „svisle“ režim u kopí – ruka se
  natočí k předmětu; podnos plochou dlaní (prsty natažené, jiné sevření než válec), korbel za ucho (sevření tenký válec,
  palec nahoře). Těžký podnos obouručně = dva markery + IK jako u nástrojů.
- **Louč/lucerna**: louč – osa svisle (plamen nahoru) v orientaci světa, ruka dorovnaná; lucerna – visí za kroužek
  (režim „visi“) s kyvadlem. Světlo louče na mobilu je samostatný rozpočet (mimo rozsah této rešerše).
- **Automatický test úchopu** (návrh pro `tools/test_drzeni.gd`, inference – tolerance nejsou z žádného zdroje):
  pro každý klip × předmět vzorkovat N snímků po modifikátoru (signál `skeleton_updated`), měřit
  (1) vzdálenost bodu dlaně (marker v ruce) od osy rukojeti v místě markeru, (2) úhel mezi osou rukojeti a osou sevření
  pěsti (napříč dlaní, kolmo na prsty), (3) u druhé ruky totéž + dosažitelnost (délka paže vs. vzdálenost cíle; při
  natažení > ~98 % délky paže hlásit), (4) u „visi“ úhel osy předmětu od svislice, (5) u podnosu úhel normály od svislice.
  Výchozí prahy k ověření měřením na vlastních modelech: poloměr rukojeti + ~1–1,5 cm, úhel ~15–20°, podnos ~10°.
  Tyto hodnoty jsou ODHAD → do `pravidla` jako NEOVĚŘENO, dokud se nezměří na snímcích, které člověk uzná za správné.

### Gaps
- Nenašel jsem veřejný zdroj s průmyslovými tolerancemi pro testy úchopu (vzdálenost/úhel); výše uvedené prahy jsou návrh.
- Nenašel jsem zdroj, jak konkrétně KCD/KCD2 řeší nošení vědra či podnosu (motion matching / ručně animované klipy?).
- Mixamo nemá klipy s předmětem v balení; konkrétní seznam Mixamo klipů „předpokládajících předmět“ (např. carry, digging,
  hammering) a jejich typické chyby jsem ve spolehlivém zdroji nenašel.
