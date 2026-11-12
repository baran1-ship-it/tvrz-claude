# Rešerše: vrstvené oblečení postav (KCD styl) pro Godot 4.4 / tablet (12. 11.)

Navazuje na `obleceni_vrstvy.md` (plán) a `odevy_zdroje.md` (inventura Quaternius kusů). Co nemá zdroj nebo nebylo
změřeno, je **NEOVĚŘENO**.

## 1. Jak to dělá KCD a jiné hry
- **KCD (Warhorse, CryEngine)**: každý kus oděvu má definované zóny těla (hrudník, záda, paže…), které zakrývá celé nebo
  částečně. U plně zakrytých zón se ve **předzpracování odmažou trojúhelníky** spodní vrstvy (těla i spodního oděvu),
  které nemají být vidět; u částečně zakrytých zón dostane spodní kus **jiný morph target** (smrskne se pod vrchní kus).
  Blaho: „clipping je náš největší nepřítel“ – [GameBanshee](http://www.gamebanshee.com/frhp),
  [PCGH, Vávra](https://www.pcgameshardware.de/Kingdom-Come-Deliverance-Spiel-16151/Specials/Kingdom-Come-Deliverance-Interview-1118601/).
- Morph target se u kusu volí v datech oděvu (KCD1 mod: `morph_target="#V_002"` v `clothing_*.xml` opravil prosvítání
  ruky rukavicí) – [Nexus KCD1](https://www.nexusmods.com/kingdomcomedeliverance/mods/1610?tab=posts). Postava =
  XML preset se seznamem GUID kusů – [Nexus KCD2 článek](https://www.nexusmods.com/kingdomcomedeliverance2/articles/79).
- Kusy jsou v CryEngine **skin attachments** (samostatný `.skin` navázaný na kosti postavy; 1 mesh a 1 materiál na
  soubor) – [CryEngine attachments](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/56658776),
  [modding.wiki KCD2](https://modding.wiki/en/kingdomcomedeliverance2/mod-development/disciplines/3d/Addingcustomweapon).
- Sloty (komunitní rozbor KCD1, ne Warhorse): bruchy, košile, nohavice, prošívané nohavice, boty, prošívanice, kroužková,
  plát, rukavice, paže, opasek, látková vrchní vrstva, kukla, helma, šperky –
  [fórum KCD](https://forum.kingdomcomerpg.com/t/layering-system-and-medieval-clothing-explained-lots-of-pictures/9396).
  Přesný počet slotů v KCD2 NEOVĚŘENO.
- Simulace látky (sukně) v KCD/KCD2: oficiální technický popis **nenalezen** (NEOVĚŘENO). CryEngine nabízí VCloth
  (simulační + vykreslovací mesh) a uvádí, že sukně fungují dobře „hnané animací“, simulace je drahá –
  [CryEngine VCloth](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/29799532).
- **Jiné hry/nástroje**: tělo s maskou zakrytých oblastí – inZOI ukládá v oděvu, které oblasti těla kryje (UV2) –
  [inZOI ModKit](https://mod-docs.playinzoi.com/ModKit/project/CAZ/Guide/03.%20Masking%20System.html) (odkaz teď 404,
  obsah z výsledku vyhledávání = NEOVĚŘENO); Character Creator „Hide Inner Mesh“ skrývá trojúhelníky těla podle
  vzdálenosti od oděvu – [Reallusion](https://manual.reallusion.com/character-creator-4/content/enu/4.0/08_Cloth/Automatically_Hiding_Inner_Meshes.htm);
  Godot fórum: vertex group zakrytých ploch smazat při exportu, případně shader posouvající oděv ven –
  [forum.godotengine.org](https://forum.godotengine.org/t/how-can-i-hide-poly-behind-clothes/30980).
- Quaternius v4 kit: kusy jsou samostatné skinned meshe na stejné kostře; při nasazení „body“ kusu se základní tělo
  skryje, ruce/nohy/boty se vrší – [cinevva blog](https://app.cinevva.com/blog/2026-05-10-open-world-browser-part-25-universal-characters)
  (třetí strana).

## 2. Sukně, zástěry, dlouhé suknice
- **Váhy na pánev s přechodem**: sukně visí z boků, vyšší vliv `pelvis`; celá na pánvi = tuhý zvon, proto přechod
  k lemu – [Sims4Studio](https://sims4studio.com/thread/21260/weights-bone-assignment-question). Mezi nohama plynulý
  přechod pravé→levé stehno, jinak ostrý zlom – [Second Life fórum](https://community.secondlife.com/forums/topic/309008-short-skirt-rigging-issue).
- **Pomocné kosti sukně**: kost „skirt-thigh“ s damped-track na koleno (bez zkrutu stehna), deformuje jen sukni –
  [BlenderArtists](https://blenderartists.org/t/how-do-you-rig-weight-paint-a-short-skirt-properly/1376331). V Godotu
  lze totéž přes `SkeletonModifier3D` / `LookAtModifier3D` (4.4) – konkrétní zapojení NEOVĚŘENO.
- **Pružné kosti**: `SpringBoneSimulator3D` je v Godotu **od 4.4** – [GameFromScratch](https://gamefromscratch.com/godot-4-4-gets-jiggle-physics/),
  [docs 4.4](https://docs.godotengine.org/en/4.4/classes/class_springbonesimulator3d.html). Řetěz = root→end kost,
  **bez větvení** (sukně = několik samostatných řetězů), parametry stiffness/drag/gravity/radius, kolize
  `SpringBoneCollision3D` (mimo PhysicsServer), kostra nesmí být škálovaná. Výkonová čísla (i mobilní) **nenalezena –
  NEOVĚŘENO**, nutné změřit Měřicí trasou.
- Alternativa bez běhové fyziky: zapéct simulaci do kostí/blend shapes (v hrách běžné kvůli výkonu) –
  [BlenderArtists](https://blenderartists.org/t/how-do-you-rig-weight-paint-a-short-skirt-properly/1376331); CryEngine
  doporučuje řídit sukni animací (viz výše).

## 3. Sloučení kusů do jedné sítě v Godotu 4
- Více `MeshInstance3D` na jednom `Skeleton3D` funguje (tak importuje každý glTF), ale každý povrch = vlastní draw call.
  **Automatické instancování je jen ve Forward+, ne v Compatibility** –
  [Optimizing 3D performance](https://docs.godotengine.org/en/stable/tutorials/optimization/optimizing_3d_performance.html).
  Skinning je „na některých platformách velmi drahý“, u animovaných modelů snížit polygony (tamtéž).
- Vestavěné slučování skinned meshí v Godotu 4 **není** (MergeGroup jen 3.6 –
  [docs 3.6](https://docs.godotengine.org/en/3.6/tutorials/3d/merge_groups.html)). Postup: `SurfaceTool.append_from()`
  / ruční `ArrayMesh` s `ARRAY_BONES` + `ARRAY_WEIGHTS` (4, nebo 8 s `ARRAY_FLAG_USE_8_BONE_WEIGHTS`) –
  [SurfaceTool](https://docs.godotengine.org/en/latest/classes/class_surfacetool.html). Podmínka: všechny kusy mají
  stejné pořadí kostí a bind pose (Skin) – u Quaternius kusů ověřeno v `odevy_zdroje.md`. Jeden povrch = jeden materiál,
  tedy **atlas textur**; povrchy v jedné meshi se stejným materiálem jsou pořád zvlášť draw cally –
  [Godot fórum](https://forum.godotengine.org/t/limiting-draw-calls-by-combining-meshes/77302).
- Doplněk s přenosem skinu: [Material Merger Godot](https://gh.r-mj.com/necat101/Material-Merger-Godot) (kvalita
  NEOVĚŘENO); Unity obdoba: kombinátory slučují 16 meshí → 1 mesh + 1 materiál –
  [SkinnedMesh Combiner](https://sites.google.com/view/awtdev/home/skinnedmesh-combiner-documentation).
- Compatibility renderer dělá skinning na GPU zvláštním průchodem (`drivers/gles3/shaders/skeleton.glsl`) –
  [commit](https://remotebranch.eu/Stowage/godot/commit/f33ffd9ab4948e0fa649de9bbe490a1d4f977691); že je cena úměrná
  počtu skinned meshí, je **NEOVĚŘENO** (měřit).
- **Rozpočet draw callů**: Arm (Peter Harris) „pro většinu mobilů cílit ~500 draw callů na snímek“ –
  [Arm fórum](https://community.arm.com/support-forums/f/graphics-gaming-and-vr-forum/48848/overhead-of-the-driver).
  Unity (stará doc.): 1 skinned renderer na postavu, mobil < 30 kostí –
  [Unity 4.6](https://docs.unity3d.com/462/Documentation/Manual/ModelingOptimizedCharacters.html) (zastaralé; UAL má 65).

## 4. Hotové kusy
| zdroj | licence | kostra UAL | poznámka |
|---|---|---|---|
| [Quaternius Modular Character Outfits – Fantasy](https://quaternius.itch.io/modular-character-outfits-fantasy) | CC0 | ano (uvádí kompatibilitu s UAL; jména kostí ověřena v `odevy_zdroje.md`) | 12 oděvů / 62 dílů, Peasant a Ranger zdarma, v2.0 „méně clippingu“, Peasant_Male má holé paže; .blend jen ve Source |
| [Quaternius Universal Base Characters](https://quaternius.com/packs/universalbasecharacters.html) | CC0 | ano | 6 těl, ~13k troj., 20 účesů; dělení těla na zóny nezmíněno (NEOVĚŘENO) |
| [OpenGameArt Modular RPG Characters](https://opengameart.org/content/modular-rpg-characters) | CC0 | NEOVĚŘENO (spíš ne) | rigged, středověk |
| [Amir modular pack](https://ahmedamirdev.itch.io/amir-the-only-modular-character-pack-youll-ever-need) | CC-BY 4.0, placený | NEOVĚŘENO | |
Sukně, zástěra, kápě, plášť, čepec v CC0 na UAL kostře **nenalezeny** → vlastní model (v Blenderu na Quaternius těle).
Sketchfab CC0 dobové oděvy: v rešerši nenalezeny (hledat dál ručně).

## 5. Doporučený postup (Blender → glTF → Godot)
1. **Tělo**: Quaternius tělo (muž v bruchách, žena ve spodní košilce) rozdělit v Blenderu na zóny jako samostatné
   materiálové sloty/vertex groupy: hrudník, záda, břicho, rameno, paže, předloktí, ruka, stehno, lýtko, chodidlo, krk
   (inspirace KCD zóny). Uložit jako data.
2. **Kus oděvu** = samostatný glTF na stejné 65kostní kostře + v metadatech (`extras` nebo JSON v `pravidla/`)
   seznam zón `kryje_cele` / `kryje_castecne`. Váhy: přenos z těla jen pro přiléhavé kusy; sukně/zástěra/suknice
   ruční váhy pánev → lem s přechodem.
3. **Pomocné kosti** pro sukni/zástěru/plášť přidat do kostry těla v Blenderu (pojmenované, UAL animace je ignorují,
   protože cílí jmény – NEOVĚŘENO pro náš import, ověřit). Řetězy 2–3 kosti × 6–8 kolem pasu (návrh, nezměřeno).
4. **Godot při vzniku postavy** (ne každý snímek): podle `postavy_vzhled.json` vybrat kusy → u těla a spodních vrstev
   vynechat trojúhelníky plně zakrytých zón (KCD volba 1) → u částečně zakrytých použít menší/„stažený“ tvar nebo blend
   shape (KCD volba 2) → sloučit vše přes `SurfaceTool.append_from` do **1 ArrayMesh, 1 povrch, 1 materiál s atlasem**
   na postavu → `MeshInstance3D.skin` + `skeleton`. Výsledek kešovat podle kombinace kusů.
5. **Pružiny** (`SpringBoneSimulator3D`) zapínat jen u blízkých NPC; ostatní jen váhy na pánev. Cenu změřit
   Měřicí trasou (NEOVĚŘENO).
6. **Rozpočty**: ~500 draw callů na snímek celkem (Arm); 1 draw call na postavu; trojúhelníky/kosti na postavu pro
   Mali/Adreno ve zdrojích nenalezeny – NEOVĚŘENO, určit měřením (dnešní Quaternius kus 1–9k troj., tělo ~13k).
7. Test smyslu: kontrola „spodní vrstva prosvítá“ (vrchol těla v zakryté zóně blíž kameře než oděv) – návrh.
