# Vzhled postav: co dělá KCD lidi „skutečnými“ a jak se k tomu přiblížit na tabletu

Rešerše 12. 11. 2026 (subagent, jen web; v repu nic neměněno kromě tohoto souboru). Navazuje na
`reserse_postavy_kcd2.md`, `obleceni_reserse.md`, `postavy_plan.md`. Zdroje [Zn] na konci. **NEOVĚŘENO** = zdroj nenalezen
nebo jen z výpisu vyhledávače / fóra.

## 1. Recept KCD/KCD2 na NPC

**Obličeje = skeny skutečných lidí.**
- KCD2: studio More.is.More postavilo pro Warhorse skenovací studio a automatickou linku do enginu: **přes 300 postav,
  u každé ~40 výrazů**, mezi nimi herci Tom McKay a Luke Dale, skeny kontroloval Warhorse živě [Z1].
- KCD1: Warhorse měl vlastní 3D skener obličejů a podle Davida Jankese (Weekly Torch, 10/2016) „máme víc modelů, než
  stihneme zpracovat“; zuby a jazyk se skenovat nedají; postup design → 2D koncept → 3D (3ds Max/Maya, ZBrush, Photoshop) [Z2].
  Warhorse sháněl dobrovolníky „3D SCAN“ (ideálně muže bez vousů) [Z3].
- Výrok Vávry „těla skládáme z malých dílů, hlavu každé postavy děláme zvlášť ze skenu a ručně dočistíme“ se objevuje ve
  výpisu vyhledávače, původní stránku jsem nenašel – **NEOVĚŘENO**.
- Hlavní character artistka Anna Pačesová: při tvorbě zohledňují **společenské postavení → účes a tvář (vrásky, kruhy
  pod očima)**, kvůli čitelnosti někdy přeženou realitu [Z4]. Konceptová výtvarnice (Kawatani) cílí na „100% přesnost“
  a estetiku středověké malby, ne na vlastní styl [Z5].
- Vlasy: žádné NVIDIA HairWorks [Z2] (tj. klasická karta/síť, technika jinak **NEOVĚŘENO**). Kůže: Vávra sám uvádí,
  že původní render má limity (chybějící stíny, detail kůže, normálové mapy) [Z6]. Rozbor Digital Foundry zaměřený na
  obličeje jsem nenašel (**NEOVĚŘENO**).

**Oděv = vrstvy + materiálové sloty + maska špíny.**
- Vrstvený oděv: přednáška Tomáše Baráka (GDC Europe 2015) „Adaptive Clothing System“ – systém procedurálně přizpůsobí
  vrstvy, aby se neprotínaly [Z7][Z8]. Každý díl oděvu musí fungovat se všemi ostatními [Z2]. Hra má ~20 slotů / 4 vrstvy
  (počty se mezi zdroji liší) [Z9].
- Materiály KCD2 (modding wiki): PBR spec/gloss; **_id mapa** (barevné kódy přiřazují „sloty“ materiálu, hojně na oděvu)
  + v .mtl „Feature slots“; **_bgs** maska Krev (R) / **Bláto (G)** / Poškození-špína (B) [Z10]. Tj. látka se skládá
  z ID masky + sdílených materiálů a dynamické vrstvy špíny, ne jen z unikátní malované textury. Že sloty nesou
  dlaždicové textury látek, je moje odvození – **NEOVĚŘENO**.

**Variabilita:** stovky skenovaných hlav [Z1] × kombinace dílů oděvu ve slotech [Z9] × materiálové sloty a špína [Z10].

## 2. Historie: co nosili Čechové kolem 1390

- **Látky:** v nálezech převládá vlna [Z11]; na venkově domácí výroba, len a plátno hojně [Z12]. Archeologie českého
  textilu 13.–15. st.: Bravermanová, Březinová [Z13].
- **Barvy:** nejlevnější a nejběžnější barviva boryt (modř), mořena (červeň), rezeda (žluť) [Z14][Z15]; černá např.
  z dubové kůry [Z15]. Nebarvená vlna má barvy ovcí (bílá, šedé, černá, světle hnědá), **ne „bahnitě hnědá“**; nebarvený
  len je světle šedý až bělavý. I prostí lidé na vyobrazeních nosí modrou, červenou, žlutou; úplně nebarvený oděv je na
  obrazech vzácný [Z14]. Kermes (šarlat) a indigo jsou drahé dovozy [Z14].
- **Obraz doby:** Bible Václava IV. (Vídeň, přes 650 miniatur, konec 14. st.) – studie Kočové rozebírá rozdíly oděvu
  bohatých/chudých a symboliku barev [Z16]. Velislavova bible (Praha, 1325–1349, 747 obrázků) je většinou jen kresba
  perem – na barvy slabý zdroj, na střih dobrý [Z17].
- **Kápě:** většina kápí doby měla cíp (liripip), někdy střižený zvlášť [Z18]; střihy Herjolfsnes (Grónsko, ~1350–1400)
  v *Medieval Garments Reconstructed* [Z19].
- **Ženy:** vdané ženy na veřejnosti hlavu kryly (závoj, rouška, barbet), nepokrytá hlava jen u dívek; doklady jsou ze
  západní a severní Evropy, pro Čechy **NEOVĚŘENO** [Z20].

## 3. Jak to přiblížit na mobilu bez záseků

**Rozpočty (zdroje, ne naše měření):**
- Arm/Android: demo *Armies* – ~210 000 troj. na snímek stabilně ~30 fps, voják ~360 troj., věže ~3 000; LOD po
  **−50 % na úroveň**; trojúhelník držet nad ~10 px; detail do textur a normálových map, ne do sítě [Z21].
- Unity (starší manuál): mobil ~300–1 500 polygonů na síť, **jeden skinovaný renderer na postavu**, 2–3 materiály,
  kostra pod ~30 kostí na mobil [Z22] (UAL má 65 kostí [Z23]).
- Quaternius Universal Base Characters: v průměru ~13 000 troj. [Z24] – sama hlava+tělo je nad třídou `postava` (14k/3k).
- Na Mali ani Adreno jsem nenašel oficiální číslo „troj. na postavu“ – **NEOVĚŘENO**; Arm doporučuje rozpočet celého
  snímku změřit (Mobile Studio) [Z25].

**Textury:** atlas = méně volání kreslení; mipmapy; ASTC (záloha ETC2); **AO a světla zapéct do albeda**; barvení šedé
textury barvou vrcholů nebo RGB maskou; balit kanály [Z26].

**Shadery v Godot Compatibility:** podpovrchový rozptyl (SSS) jen ve Forward+, v Compatibility **není** [Z27] → kůže
musí „hrát“ z textury. Rim (mikro-chloupky látky) a režim stínování per-vertex existují [Z27]. Detail textura
(maska, albedo, normála, UV2/triplanar) existuje [Z27] – stojí další vzorkování. Alpha Scissor je rychlejší než blend;
Alpha Hash se hodí na vlasy, ale chce MSAA [Z27] → u nás jen Scissor. `discard`/alfa test na Mali vynutí pozdní Z
a vypne FPK [Z28] → alfa jen na malém povrchu vlasů, tělo neprůhledné. Compatibility kreslí světla po průchodech
(stínící omni/spot = další průchod) [Z29].

**LOD:** Godot generuje LOD při importu (meshoptimizer), ale u skinovaných sítí může dělat chyby [Z30] → LOD stavět
v Blenderu a kontrolovat snímkem.

**Realistické hlavy CC0:** MakeHuman/MPFB – jádrové assety (kůže, obočí, oči, vlasy) **CC0**, plugin GPL, export glTF;
pozor na komunitní CC-BY assety [Z31][Z32]. Kompatibilita kostry MPFB ↔ UAL: retarget nutný, **NEOVĚŘENO**. UAL 2 deklaruje
kompatibilitu s běžnými rigy (Mixamo) [Z23].

## 4. Doporučení pro naši linku (Blender → 1 glTF na NPC), od největšího zisku na cenu

1. **Paleta a hodnoty z barviv (≈0 Kč výkonu).** Ověřit `_barvy` proti [Z14]: nebarvená vlna bílá/šedá/černá/světle hnědá,
   len světle šedý; boryt/mořena/rezeda v **vybledlých, nerovnoměrných** tónech; drahé jen šarlat. Každé NPC ±5–10 % jas/sytost
   na díl (seed). Chudí: vybledlé, záplaty; měšťané: sytější modrá/červená.
2. **Zapečená špína a AO do atlasu (nulová cena za běhu)** [Z26]. V Blenderu barva vrcholů / maska: bláto na lemu, nohavicích,
   botách (analog `_bgs` G [Z10]), ztmavení pod pásem, v podpaží, u límce; odřené lokty a kolena. Podle role (mlynář mouka,
   kameník prach) – jako záznam v datech, ne výjimka.
3. **Záhyby látky normálovou mapou z vysoké sítě** (cloth sim v Blenderu → bake na nízkou síť) [Z21][Z26]. Na vzdálenost
   tabletu záhyby a vrstvy (lem košile pod kotlí, pás, kápě s liripipem) udělají víc než vazba látky.
4. **Tvář podle postavení a věku** [Z4]: 3–4 varianty textury hlavy (opálení, vrásky, kruhy pod očima, strniště), teplý
   podtón místo SSS [Z27], mírná variace drsnosti (čelo/nos lesklejší). Proporce: zkusit MPFB hlavu (CC0) zdecimovanou
   na ~2–3 tis. troj. s normálou zapečenou z plné sítě – jako izolovaný pokus, kostra/retarget **NEOVĚŘENO**.
5. **Vlasy schovat do historie:** vdané ženy pod roušku/závoj [Z20], muži často kápě [Z18] → méně alfa povrchů [Z28].
   Vlasy = několik karet s Alpha Scissor [Z27], jeden malý povrch.
6. **Vazba látky:** nejdřív zapéct do atlasu; pokud v 512 px zanikne, sdílená dlaždicová detail normála (128–256 px) přes
   UV2 [Z27] – jen u LOD0, změřit na tabletu (**NEOVĚŘENO**).
7. **LOD a rozpočet:** LOD0 ≤ ~10–14 tis. (třída 14k), LOD1 ~3 tis. (−50 % krokově [Z21]), LOD2 ~1 tis. za ~40 m;
   jeden skinovaný renderer [Z22]; stín jen LOD0 do `stin_m`. Čísla do `pravidla_modelu.json`, ne do kódu; výkon NEOVĚŘENO
   na zařízení – Měřicí trasa.

## Zdroje
- [Z1] https://moreismore.cz/work/kingdom-come-deliverance-2/
- [Z2] https://forum.kingdomcomerpg.com/t/warhorse-studios-weekly-torch/29593/24
- [Z3] https://forum.kingdomcomerpg.com/t/chcete-sve-pra-rodice-objevit-ve-hre-kingdomcomedeliverance/26207
- [Z4] https://www.gamestar.de/artikel/kingdom-come-2-sigismund-gucci-unterwaesche-charakterdesign,3453665.html
- [Z5] https://automaton-media.com/en/news/kingdom-come-deliverance-2-japanese-concept-artist-about-their-depiction-of-medieval-europe/
- [Z6] https://www.pcgamer.com/games/rpg/kingdom-come-deliverance-director-says-dlss-5-does-right-by-kcd-2-people-are-crazy-for-thinking-its-ai-slop/
- [Z7] https://gdcvault.com/play/1022822/Adaptive-Clothing-System-in-Kingdom
- [Z8] https://forum.kingdomcomerpg.com/t/adaptive-clothing-system-in-kcd/25894
- [Z9] https://kingdomcomedeliverance.wiki.fextralife.com/Clothing ; https://kingdomcomedeliverance.wiki.gg/wiki/Armour
- [Z10] https://modding.wiki/en/kingdomcomedeliverance2/mod-development/disciplines/3d/caseter-texture-megadump
- [Z11] https://digilib.phil.muni.cz/_flysystem/fedora/pdf/127393.pdf
- [Z12] https://digilib.phil.muni.cz/_flysystem/fedora/pdf/127395.pdf
- [Z13] https://digilib.phil.muni.cz/_flysystem/fedora/pdf/127400.pdf ; https://invenio.nusl.cz/record/364643?ln=en
- [Z14] https://acoup.blog/2021/04/02/collections-clothing-how-did-they-make-it-part-iva-dyed-in-the-wool/
- [Z15] https://users.ox.ac.uk/~wychwood/costumefabrics.shtml
- [Z16] https://historica.upol.cz/artkey/hol-201201-0010_symbolicky-rozmer-odevu-ceska-vrcholne-goticka-moda-ve-svetle-bible-vaclava-iv.php
- [Z17] https://en.wikipedia.org/wiki/Velislai_biblia_picta
- [Z18] https://matsukazesewing.blogspot.com/2014/12/14th-century-womens-hood-documentation.html
- [Z19] https://muse.jhu.edu/book/110581
- [Z20] https://www.themcs.org/costume/Female%20reenactment%20costume.htm ; https://en.wikipedia.org/wiki/Wimple
- [Z21] https://developer.android.com/games/optimize/geometry
- [Z22] https://docs.unity3d.com/2018.3/Documentation/Manual/ModelingOptimizedCharacters.html
- [Z23] https://quaternius.com/packs/universalanimationlibrary2.html ; https://app.cinevva.com/blog/2026-05-01-open-world-browser-part-17-animations-and-search
- [Z24] https://quaternius.com/packs/universalbasecharacters.html
- [Z25] https://blog.unity.com/games/tackling-profiling-for-mobile-games-with-unity-and-arm
- [Z26] https://developer.android.com/games/optimize/textures
- [Z27] https://docs.godotengine.org/en/4.4/tutorials/3d/standard_material_3d.html
- [Z28] https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/hidden-surface-graphics-removal-methods-in-mali-gpus
- [Z29] https://docs.godotengine.org/en/4.4/contributing/development/core_and_modules/internal_rendering_architecture.html
- [Z30] https://docs.godotengine.org/en/4.4/tutorials/3d/mesh_lod.html
- [Z31] https://static.makehumancommunity.org/about/license.html ; https://static.makehumancommunity.org/oldsite/faq/what_changed_regarding_the_license_in_2020.html
- [Z32] https://www.cgchannel.com/2025/03/check-out-open-source-blender-character-generation-plugin-mpfb-2
