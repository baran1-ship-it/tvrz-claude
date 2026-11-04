# Rešerše: jak kreslí trávu hry (a co z toho pro tablet) – 4. 11.

Zadání: tráva na tabletu stojí p50 +7–13 ms, p95 +30–90 ms (bez trávy 17–20 ms). Prototyp „GPU tráva“ (poloha ve
vertex shaderu) nepomohl, takže brzdí **kreslení na GPU** (pixely průhledných karet, discard, překryv), ne CPU.
Rešerše her + zdrojáku Godot 4.4.1 + rozbor našich textur. Nic v projektu se neměnilo.

Značení spolehlivosti: **[primární]** = studio/výrobce GPU/zdroják enginu, **[sekundární]** = rozbor třetí strany,
**[pozorování]** = hráčské/komunitní, **NEOVĚŘENO** = nemáme zdroj ani měření.

---

## 0. Nejdůležitější zjištění hned na začátek

1. **Náš shader trávy discard dělá, i když komentář tvrdí opak.** `shaders/trava_gpu.gdshader` (ř. 7–9) i
   `shaders/stebla.gdshader` mají `render_mode … alpha_to_coverage_and_one` a komentář „bez discard (vypíná early-Z)“.
   Ve zdrojáku Godot 4.4.1 GL Compatibility ale:
   - `ALPHA_SCISSOR_THRESHOLD` se překládá na `if (alpha < alpha_scissor_threshold) { discard; }`
     (`drivers/gles3/shaders/scene.glsl` ř. 1904–1906 a 2247–2249) **[primární]**,
   - režim alpha-to-coverage v GLES3 nedělá nic: `case BLEND_MODE_ALPHA_TO_COVERAGE: { // Do nothing for now. }`
     (`drivers/gles3/rasterizer_scene_gles3.cpp` ř. 3116–3118) **[primární]**, a bez MSAA (tablet: MSAA zakázáno)
     by stejně neměl na co působit.
   → Na tabletu tedy kreslíme klasický alpha test (discard) se všemi jeho náklady. Rozhodnutí „A2C místo discard“
   z rádce 20:30 se ve skutečnosti neuplatnilo.
2. **Depth prepass je na Mali/Adreno v Godotu vypnutý.** `rendering/driver/depth_prepass/disable_for_vendors`
   má výchozí `"PowerVR,Mali,Adreno,Apple"` (Godot 4.4.1 `doc/classes/ProjectSettings.xml` ř. 2604) **[primární]**.
   Každý pixel karty, který projde depth testem, spustí celý fragment shader; schovat ho za pozdější geometrii nejde.
3. **Naše karty jsou z velké části prázdné** (změřeno na PNG v repu, alfa ≥ 128, skript ve scratchpadu):

   | textura (buňka) | podíl plochy, který zůstane | konvexní obal alfy | vrcholů obalu |
   |---|---|---|---|
   | `trava_atlas.png` 0,0 / 0,1 / 0,2 | 0,28 / 0,33 / 0,24 | 0,63 / 0,74 / 0,80 | 21 / 22 / 15 |
   | `trava_atlas.png` 1,0 / 1,1 / 1,2 | 0,20 / 0,23 / 0,21 | 0,47 / 0,41 / 0,47 | 16 / 13 / 21 |
   | `drn_atlas.png` (celá) | **0,07** | 0,82 | 23 |
   | `trava_vysoka_atlas.png` (celá) | **0,06** | 0,79 | 17 |
   | `trava_nizka_atlas.png` (celá) | 0,28 | 0,88 | 21 |
   | `vejir_atlas.png` (celá) | 0,82 | – | – |

   U trsů se 67–80 % rasterizovaných fragmentů spočítá a zahodí; u drnu a vysoké trávy 93–94 % (pokud karta
   používá celou texturu – rozložení UV drnu a vysoké trávy jsem neověřoval). To je přesně profil „drahé pixely,
   levné vrcholy“, který odpovídá výsledku prototypu.
4. Už máme: stíny trávy vypnuté (`trava_gpu.gd` ř. 110, `louka.gd` ř. 956), `vertex_lighting`, `specular_disabled`,
   hustota přes `visible_instance_count`. Tyto známé triky tedy už nejsou rezerva.

---

## 1. Jak to dělají hry

### Kingdom Come: Deliverance 1 a 2 (CryEngine, Warhorse)
- Tráva v CryEngine 5 = **Merged Meshes**: vegetace se slučuje do **buněk 16 m**, které „se samy LODují tím, že
  s rostoucí vzdáleností kamery od buňky ubírají instance“ (CRYENGINE 5 docs, Vegetation 02 Grass – Maya)
  **[primární]** https://cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/24285891 .
  Starší způsob jsou „grass patches“ (Vegetation 01 Grass (Patch))
  https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/24285885 .
- Ladění: `e_MergedMeshes 0/1`, `e_MergedMeshesInstanceDist` (CryEngine 3: výchozí 1), `e_MergedMeshesViewDistRatio`.
  Komunita u KCD1 uvádí `e_MergedMeshesInstanceDist` ~20 (vzdálenost animace trávy) a `ViewDistRatio` 25–100
  **[pozorování]** https://www.gog.com/forum/kingdom_come_deliverance/fixed_detail_distances_with_131 ,
  https://steamcommunity.com/app/379430/discussions/0/2860219962081819052/ . Hodnoty se mezi patchi liší.
- **Barva terénu do trávy**: CryEngine má u vegetace „Use Terrain Color“ + `Terrain Color Blend` (zblízka, 0–1)
  a `Terrain Color Blend Dist` (v dálce); dokumentace říká, že to „pomáhá vegetaci splynout s terénem, aby byl
  LOD popping a aliasing méně vidět“; síla 1 zcela přebije texturu trsu **[primární]**
  https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1048607 ,
  https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/24285888 .
- Konkrétní rozpočty KCD2 (trojúhelníky trsu, vzdálenosti) jsem v otevřených zdrojích **nenašel**; Digital
  Foundry / TechPowerUp chválí vegetaci, u KCD1 (Switch/konzole) zmiňují nižší hustotu a pop-in trávy
  **[sekundární]** https://www.techpowerup.com/review/kingdom-come-deliverance-ii-performance-benchmark/8.html .
  Vavra (citováno sekundárně): UE5 je „pro hustou vegetaci slabší než CryEngine“
  https://mein-mmo.de/kcd2-cryengine-statt-unreal-engine/ .

### Ghost of Tsushima (Sucker Punch, GDC 2021, Eric Wohllaib)
Talk: https://gdcvault.com/play/1027033/Advanced-Graphics-Summit-Procedural-Grass **[primární, za paywallem]**;
čísla níže ze shrnutí **[sekundární]** https://tigerabrodi.blog/what-we-can-learn-from-grass-in-ghost-of-tsushima-renders ,
https://gist.ly/youtube-summarizer/procedural-grass-systems-in-ghost-of-tsushima-achieving-art-direction .
- **Geometrická stébla, žádné alfa karty**: stéblo = Bézierova křivka (4 body), **15 vrcholů blízko, 7 daleko**;
  krátká tráva použije zbylých 8 vrcholů na druhé stéblo (zdvojení zdarma). Opaque → funguje early-Z.
- Dlaždice; vzdálené dlaždice 2× větší se stejným počtem stébel; v blízké dlaždici se k hranici LOD **plynule
  zahodí 3 ze 4 stébel**, aby hustota na hranici seděla; tvar stébla se před přepnutím „domorfuje“ (bez skoku).
- ~**83 000 stébel v záběru za ~2,5 ms** (PS4) **[sekundární]**.
- **Dál než tráva**: dlaždice nahradí **autorská textura na terénu**, kterou kreslí výtvarník – terén „vypadá jako
  tráva“, takže konec trávy není vidět.
- Stíny: tráva se do shadow mapy nekreslí; terén se ve stínovém průchodu zvedne do výšky trávy a zapíše hloubku
  ditherem (aproximace hustoty) + screen-space stíny.
- Stébla kolmo ke kameře se mírně natočí ke kameře (tráva nevypadá z boku řídce); normály se „zaoblí“ bez vrcholů.
- Shluky (Voronoi clumping): stébla ve shluku sdílí výšku/směr/barvu.

### Horizon Zero Dawn / Forbidden West (Guerrilla, Decima)
- GDC 2017 Jaap van Muijden: **veškerá vegetace je umísťována procedurálně na GPU** podle 2D map hustoty
  (~4 MB/km², tj. ~32 bitů na m²), diskretizace ditheringem, 500+ typů, 100 000+ objektů, **~250 µs GPU**
  na umístění **[primární]** https://www.guerrilla-games.com/media/News/Files/GDC2017_VanMuijden_GPUBasedProceduralPlacementInHorizonZeroDawn.pdf .
  Pozn.: to řeší **umístění** (to, co náš prototyp), ne cenu pixelů – shoduje se s naším zjištěním, že GPU umístění
  samo kreslení nezlevní.
- GDC 2018 Gilbert Sanders „Between Tech and Art: The Vegetation of HZD“
  https://gdcvault.com/play/1025066/Between-Tech-and-Art-The : vlastní LOD řetězec místo SpeedTree LODů, billboardy
  (zkřížené roviny) až na LOD 4–5, stínové kaskády 0–1 normálně, dál stín z výškového pole, stínové meshe oddělené
  od viditelných **[sekundární – shrnutí videa]**. Že Decima kreslí alfa vegetaci s depth prepassem, tvrdí jen
  blog https://app.cinevva.com/blog/2026-05-11-foliage-overdraw (neověřeno proti talku).

### Red Dead Redemption 2 (RAGE)
- Rozbor snímku (PC): G-buffer začíná **depth prepassem terénu**, pak deferred; detail trávy rozbor neuvádí
  **[sekundární]** https://imgeself.github.io/posts/2020-06-19-graphics-study-rdr2 . Primární popis trávy
  jsem nenašel; je to desktop/konzole s depth prepassem – pro TBDR mobil nepřenosné.

### The Witcher 3 (REDengine, SpeedTree)
- Jen čísla z configu **[pozorování]**: `GrassDensity` Ultra 2400, `GrassDistanceScale` Ultra 1,
  `GrassGenerationEfficiency` 0,075, `GrassRingSize`; nad 2400/3 bliká, nad 3600 mizí květiny
  https://primagames.com/news/the-witcher-3-pc-config-ini-tweaks-are-plentiful-demanding .
  Durante (PC Gamer): hustota trávy má menší vliv než dohled vegetace, ale „mezi prvními věcmi ke snížení“
  https://pcgamer.com/durantes-witcher-3-analysis-the-alchemy-of-smoothness/2 . → Tráva = prstenec kolem hráče,
  dál nic (terén).

### Zelda: Breath of the Wild (Switch – slabé GPU, nejbližší náš případ)
- Primární technický popis trávy **nenašel jsem**. Ověřené: **dynamické rozlišení** (dok 900p, ruka 720p, obojí
  dynamicky) https://www.nintendolife.com/news/2017/03/zelda_breath_of_the_wild_uses_dynamic_resolution_scaling_to_maintain_performance
  a „velmi agresivní LOD“ **[sekundární]** https://gamingbolt.com/the-legend-of-zelda-tears-of-the-kingdom-graphics-analysis-how-big-of-a-leap-is-it ;
  Nintendo: Korok Forest (hustá vegetace) byl na Switchi nejtěžší místo
  https://www.gamesradar.com/games/open-world/nintendo-exec-says-switch-2-runs-zelda-breath-of-the-wild-so-much-better-even-he-was-shocked-all-this-foliage-is-finally-being-able-to-get-rendered .
- **[pozorování]** tráva jen v krátkém poloměru kolem Linka, dál terén natřený stejnou barvou; přechod skryt tím, že
  barva trsu = barva terénu. NEOVĚŘENO čísly.

### Genshin Impact (mobil!)
- miHoYo má **dvě různé pipeline**: PC/konzole a Android/iOS (Unite Seoul 2020, Zhenzhong Yi) **[primární,
  ale o světle/stínech, ne trávě]** https://docswell.com/s/UnityJapan/KWRPQ5-210617-unity-dojo20211mihoyozhenzhongyi .
- Primární popis trávy jsem nenašel (EN ani CN). **[pozorování]** na mobilu nízké trsy jen v blízkém okolí,
  rozlišení 3D se na mobilu škáluje (nastavení „Render Resolution“). NEOVĚŘENO čísly.

### Sky: Children of the Light, PUBG Mobile, Fortnite mobile
- Primární zdroje o trávě **nenalezeny**. Co je doložené:
  - Unity fórum k trávě na Quest (Adreno): alfa blending na Adrenu „nejde udělat výkonně“, použít alpha test
    **[pozorování]** https://discussions.unity.com/t/any-clever-trick-for-tall-grass-on-mobile-quest/811738 .
  - Unreal (PUBG Mobile i Fortnite běží na UE): Landscape Grass Type má `Start/End Cull Distance` (plynulé
    mizení mezi nimi) a škálování `grass.DensityScale` podle nastavení kvality **[primární – dokumentace UE]**
    https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Landscape/FGrassVariety ; Epic dočasně
    vypnul „3D Grass“ v UEFN na PS4/Xbox One/Switch 2/PC (pády) **[sekundární]**.
  - **[pozorování]** PUBG Mobile: tráva jen v malém poloměru (hráči si stěžují, že ležící hráč je z dálky vidět,
    protože tráva dál není) https://steamcommunity.com/app/578080/discussions/1/1621724915784318361 (PC verze, princip
    stejný). Tj. i kompetitivní hra raději useká dohled trávy, než by platila pixely.

---

## 2. Co říkají výrobci mobilních GPU

**Arm (Mali)**
- „Real-Time 3D Art Best Practices: Materials and Shaders“ (Arm, v1.0) **[primární]**
  https://documentation-service.arm.com/static/625591e9caabfd7b3c13f176 :
  - „Avoid the alpha test, or cutout, unless it is required.“ – „Using alpha test disables some optimization
    features within the GPU.“ – „In general, avoid using transparencies with alpha blend on mobile platforms.“ –
    „If alpha blend is needed, try to make the coverage of the blend area small.“ – profilovat oboje.
  - §7.4 (listí): alpha test je pro vegetaci v pohybu lepší než blend (blend se špatně třídí); zubaté hrany
    v pohybu nevadí.
- Arm komunita (zaměstnanci Armu): **blending vypíná early-ZS i FPK** (Forward Pixel Kill); aby fragment mohl
  zakrýt a zabít předchozí (FPK/HSR), musí být neprůhledný se **známým pokrytím – žádný discard, žádný
  alpha-to-coverage**; logika je po pipeline (jedna alfa kresba nerozbije opaque před ní) **[primární]**
  https://community.arm.com/support-forums/f/graphics-gaming-and-vr-forum/54421/subpasses-alpha-blending-fpk-early-zs .
- Immortalis-G925 (nová HW „fragment pre-pass“): draw s discardem je **late-ZS**, pre-pass musí část fragment
  shaderu spustit dvakrát; Arm radí „optimalizovat cestu ke známému pokrytí“ **[primární]**
  https://community.arm.com/arm-community-blogs/b/graphics-gaming-and-vr-blog/posts/immortalis-g925-the-fragment-prepass .
- Arm Mali Best Practices guide (do/don't) https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/arm-mali-best-practices .

**Qualcomm (Adreno)**
- FAQ (citováno na fóru Qualcommu): alpha test vs. blend mají z pohledu propustnosti stejnou cenu; discard nemá vliv
  na LRZ, jde se na plné Z **[primární, nepřímo]** https://developer.qualcomm.com/sites/default/files/docs/adreno-gpu/snapdragon-game-toolkit/gdg/gpu/faq.html .
  Mesa freedreno to upřesňuje: draw s discardem **nemůže přispět do LRZ v binning průchodu**, jen zpětně v render
  průchodu **[primární – reverzní dokumentace HW]** https://docs.mesa3d.org/drivers/freedreno/hw/lrz.html .
- Fórum Qualcommu: HW alpha test (Adreno 530) běží **až po doběhnutí shaderu** → práce za `discard` se platí,
  `discard` dávat co nejdřív/nejlépe dřív než drahé výpočty https://developer.qualcomm.com/forum/qdn-forums/software/adreno-gpu-sdk/64682 .

**Imagination (PowerVR)**: depth prepass na TBDR nepřináší nic https://docs.imgtec.com/starter-guides/powervr-architecture/html/topics/rules/do-not-use-depth-pre-pass.html
(proto ho Godot na mobilech vypíná, viz §0).

**Humus (Emil Persson) – ořez karet na obrys („particle trimming“)** **[primární]**
https://www.humus.name/Articles/Persson_GraphicsGemsForGames.pdf , https://humus.name/index.php?page=Cool :
- už jen ořez quadu na bounding box alfy ušetří „přes 30 %“ fill-rate; polygon podle alfy víc;
- **víc než ~8 vrcholů se obvykle nevyplatí** (Just Cause 2: 4 vrcholy pro mraky z CPU, 8 pro GPU částice).

---

## 3. Shrnutí: vzorec, který opakují všechny hry

1. **Tráva je jen blízko.** Plná hustota v desítkách metrů na konzoli/PC, na Switchi a mobilu ještě méně; dál
   terén. Hustota se ubírá po instancích v buňkách (CryEngine 16 m buňky, Tsushima 3 ze 4 stébel, UE Start/End
   Cull Distance).
2. **Konec trávy schová barva, ne geometrie**: terén pod trávou je natřený jako tráva (Tsushima autorská textura,
   CryEngine Terrain Color Blend v opačném směru – tráva přebírá barvu terénu).
3. **Blízko geometrie, dál karty, nejdál textura.** Kdo má rozpočet, kreslí opaque stébla (Tsushima 15/7 vrcholů),
   karty až v LOD 4–5 (HZD).
4. **Tráva nevrhá skutečný stín** (Tsushima fake z terénu; HZD stín z výškového pole v dálce).
5. **Na mobilu**: žádný blend, alpha test jen nutně a na co nejmenší ploše, nízké 3D rozlišení, dynamické škálování.

---

## 4. Techniky pro náš případ (seřazeno podle očekávaného přínosu)

Přínos = odhad, NEOVĚŘENO na tabletu, dokud neprojede měřicí trasa. Řazení vychází z §0: brzdí pixely karet s
discardem, vrcholy ne.

| # | Technika | Proč / zdroj | Očekávaný přínos | Náročnost |
|---|---|---|---|---|
| 1 | **Ořez karet na obrys alfy** (mesh trsu = polygon 6–8 vrcholů podle alfy buňky atlasu místo obdélníku; generovat v `blender/atlas_travy.py`) | Humus: bbox >30 %, polygon víc; naše buňky: konvexní obal 41–80 % plochy quadu (průměr ~0,59) | −20 až −59 % fragmentů trsů (změřeno na texturách, ne na zařízení) | nízká–střední (skript + export, žádná změna shaderu) |
| 2 | **Drn a vysoká tráva: zrušit nebo přestavět** – drn má krytí 7 %, vysoká 6 % (93–94 % plochy jde do discardu); drn nahradit texturou terénu, vysokou trávu ořezat (#1) nebo dát tenkou geometrii | Arm „coverage small“; Tsushima nejdál textura | velký u drnu (celá vrstva pryč) | nízká |
| 3 | **Kratší poloměr plné hustoty** 20 m → 10–12 m, řídnutí do ~30 m, dál nic; plocha ∝ r² (12 m = 36 % plochy 20 m kruhu) | Witcher/PUBG/BOTW: prstenec kolem hráče; CryEngine buňky ubírají instance | velký, lineárně s plochou | nízká (uniformy `r_out`, `hust_od`, …; pravidla do `pravidla/`) |
| 4 | **Terén pod trávou natřít „jako tráva“ + trs přebírá barvu terénu u paty** (grass color map; ověřit, co už dělá `barva_krajiny.gdshaderinc`) – umožní #3 bez viditelné hrany | CryEngine Terrain Color Blend/Dist; Tsushima autorská textura | umožňuje #2 a #3 (sám o sobě 0 ms) | nízká–střední |
| 5 | **Discard hned na začátku `fragment()`**: první přečíst jen alfu atlasu, `if (a < prah) discard;` ručně, teprve pak barva/mip/jas. Godot vkládá svůj discard až za celý uživatelský `fragment()` (scene.glsl ř. 1904) | Qualcomm: práce před discardem se platí; Arm: zkrátit cestu ke známému pokrytí | malý–střední (dle délky fragmentu) | nízká |
| 6 | **Opravit iluzi A2C**: odstranit `alpha_to_coverage_and_one` + `ALPHA_ANTIALIASING_EDGE`, komentář opravit (§0.1); nic se nezrychlí, ale přestaneme rozhodovat podle neplatného předpokladu | zdroják Godot 4.4.1 | 0 ms, správnost | velmi nízká |
| 7 | **3D rozlišení 0,75–0,85** (`scaling_3d/scale`, v Compatibility bilineárně) – nebo dynamicky podle času snímku, jen na tabletu | BOTW dynamické rozlišení; Genshin mobil render scale | −28 až −44 % pixelů celé scény (0,85² = 0,72; 0,75² = 0,56) | nízká (ale mění vzhled všeho – Míša posoudí) |
| 8 | **Pořadí kreslení**: buňky trávy menší (8–16 m, vlastní AABB místo jednoho prstence) → Godot je seřadí zepředu dozadu (opaque řazení = priorita → 16 hloubkových vrstev podle středu instance, `rasterizer_scene_gles3.h` sort key); budovy/skály/terén s nižší `render_priority`, aby byly v Z bufferu dřív a trávu za nimi zabil early-Z test | CryEngine 16 m buňky; běžně GPU u discard draw zachová early Z *test* proti už zapsané hloubce a odloží jen *zápis* (Arm to výslovně netvrdí – NEOVĚŘENO na našem Mali/Adreno, ověřit variantou trasy) | střední tam, kde tráva je za budovami; malý na volné louce | nízká–střední |
| 9 | **Geometrická stébla do ~6–8 m** (opaque, bez discardu, 5–7 vrcholů/stéblo, Tsushima styl), karty jen dál | Tsushima 15/7 vrcholů; Arm: opaque = early-ZS + FPK | potenciálně velký zblízka, ale riziko mikrotrojúhelníků (2×2 quady) a víc vrcholů | vysoká (nový mesh, LOD, vzhled) |
| 10 | **Frustum culling buněk** (dnes prototyp: `custom_aabb` na celý prstenec → vrcholy za kamerou se zpracují) | CryEngine buňky | malý (vrcholy nejsou hlavní náklad) | nízká (spojit s #8) |
| 11 | **Depth-only prepass jen pro trávu** (`depth_prepass_alpha` / dva průchody) | Desktop (RDR2 terén, cinevva blog) | na TBDR pravděpodobně záporný (2× vrcholy + 2× discard); jen jako izolovaný test | střední |
| 12 | **Alpha-to-coverage** | vyžaduje MSAA (zakázáno) a v Godot 4.4.1 GLES3 neimplementováno | žádný | – (zamítnuto) |

**Doporučené pořadí měření** (každé jako varianta měřicí trasy, ať se přínos dá přiřadit): #6 (úklid) → #2 drn
vypnout → #3 poloměr 12 m → #1 ořez karet → #5 discard dopředu → #8 pořadí → teprve pak #7 a #9.
Na PC lze předem kvantifikovat překryv: Godot `Viewport.debug_draw = DEBUG_DRAW_OVERDRAW` funguje i v Compatibility
(`rasterizer_scene_gles3.cpp` ř. 2494) – snímek louky s trávou a bez, ať máme číslo vrstev místo dohadu.

---

## 5. Nenašel jsem (místa, kde se hledalo)
- KCD1/2: rozpočty trsu a vzdálenosti (CryEngine docs, Steam/GOG/Nexus cfg, Digital Foundry/TechPowerUp/PCGH).
  Warhorse modding dokumentace k trávě nedohledána.
- Genshin, Sky, PUBG Mobile, Fortnite mobile, BOTW, RDR2: žádný primární technický popis trávy (GDC Vault, Unite,
  CN weby, rozbory snímků). Uvedené jsou jen nepřímé věci (rozlišení, UE nastavení, pozorování).
- Tsushima: přesná velikost dlaždice a počet stébel na dlaždici (jen za paywallem GDC Vault / video talku).
