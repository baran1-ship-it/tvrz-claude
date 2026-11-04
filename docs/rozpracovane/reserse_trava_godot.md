# Rešerše: levná tráva v Godot 4.4.1 Compatibility na Android tabletu

Stav 4. 11. 2026. Rešerše = podklady a hypotézy, **nic z toho není změřeno na našem tabletu** (NEOVĚŘENO NA ZAŘÍZENÍ).
Výchozí stav (z měření): tráva +7–13 ms p50, +30–90 ms p95; bez trávy 17–20 ms. „GPU tráva“ (pevná mřížka kolem kamery,
hash ve vertex shaderu, princip z forum.godotengine.org/t/141821) nepomohla → náklad je kreslení na GPU, ne CPU.

Rozlišení: **[zdroj Godot]** = přečteno přímo ve zdrojácích Godot 4.4.1-stable (odkaz na soubor), **[cizí měření]** =
číslo z cizího projektu/zařízení, **[názor]** = forum/blog bez měření, **[hypotéza]** = můj závěr pro náš případ.

---

## 1. Nejdůležitější nálezy (ze zdrojáků Godot 4.4.1, týkají se přímo nás)

### 1a. Stínované slunce = celá tráva se kreslí DVAKRÁT  [zdroj Godot]
`drivers/gles3/rasterizer_scene_gles3.cpp` (4.4.1-stable), ř. 3032–3033 a 3041–3055:

```
bool uses_additive_lighting = (inst->light_passes.size() + p_render_data->directional_shadow_count) > 0;
uses_additive_lighting = uses_additive_lighting && !shader->unshaded;
for (pass = 0; pass < MAX(1, light_passes.size() + directional_shadow_count); pass++) { ... BLEND_MODE_ADD ... }
```

- Compatibility kreslí stínované světlo **další celou geometrickou pasáží** (aditivní blending). `directional_shadow_count`
  je globální pro snímek → jakmile má slunce `shadow_enabled = true` (u nás `scripts/daylight.gd:66`, `main.gd:1966`),
  **každý stínovaný materiál** (tedy i tráva s `vertex_lighting`) jde 2×: základní pasáž + pasáž stínu slunce
  (s PCF5 při `soft_shadow_filter_quality.mobile=2`, ř. 3327–3331).
- Výjimku má jen `render_mode unshaded` (ř. 3033). `shadows_disabled` ani `receive_shadows` tu **nehrají roli** – v tomto
  kódu je nehledá.
- Totéž pro každé OmniLight/SpotLight se stínem, jehož dosah zasáhne AABB instance (`inst->light_passes`). MultiMesh má
  jedno velké AABB → stínovaná lucerna/oheň (u nás `life.gd:551`, stín do 18 m) může přidat **další pasáž celé buňky trávy**.
- Oficiální popis: Compatibility „používá jednu pasáž pro světla bez stínu, s více pasážemi u stínů; každá další pasáž
  kreslí jedno Omni, jedno Spot a jedno Directional světlo se stínem“
  ([Godot docs – Internal rendering architecture](https://docs.godotengine.org/en/latest/engine_details/architecture/internal_rendering_architecture.html)).
- Náš kód už má připravenou variantu `unshaded` (`scripts/louka.gd:1706–1745`, `TVRZ_UNSHADED`), ale je odložená
  („na PC černé“), na tabletu tedy tráva dnes s velkou pravděpodobností jede ve 2 pasážích. **[hypotéza – ověřit snímkem
  RenderDoc/Snapdragon Profiler nebo variantou trasy]**

### 1b. `alpha_to_coverage_and_one` v Compatibility nedělá nic, discard zůstává  [zdroj Godot]
- `rasterizer_scene_gles3.cpp` ř. 3116–3118: `case BLEND_MODE_ALPHA_TO_COVERAGE: // Do nothing for now.` – GL stav
  `GL_SAMPLE_ALPHA_TO_COVERAGE` se nikde nezapíná. Bez MSAA by stejně nemělo účinek (MSAA na tabletu nesmíme).
- `drivers/gles3/shaders/scene.glsl` ř. 1897–1907: když shader nastaví `ALPHA_SCISSOR_THRESHOLD`, vygeneruje se
  `if (alpha < alpha_scissor_threshold) discard;`.
- Náš `shaders/stebla.gdshader` má v komentáři „bez discard“, ale ř. 138 nastavuje `ALPHA_SCISSOR_THRESHOLD = prah`
  → **na tabletu discard je**. Předpoklad z „godot-mobile-optimized-grass“ v Compatibility neplatí.

### 1c. Depth prepass je na Mali i Adreno vypnutý  [zdroj Godot]
`servers/rendering_server.cpp` ř. 3644–3645:
`rendering/driver/depth_prepass/enable = true`, `rendering/driver/depth_prepass/disable_for_vendors = "PowerVR,Mali,Adreno,Apple"`
(`drivers/gles3/storage/config.cpp` ř. 190–203 porovnává s `GL_RENDERER`). Na tabletu tedy **žádný Z-prepass**:
alfa-testovaná tráva se stíní plně v pořadí, v jakém přijde, a s `discard` hardware nemůže zahodit skryté fragmenty
předem (viz kap. 4). Prepass by zase znamenal ještě jedno zpracování všech vrcholů trávy.

### 1d. MultiMesh nemá ořez po instancích  [zdroj Terrain3D docs, forum]
„MultiMesh kreslí všechny instance jedním voláním a neořezává jednotlivé instance frustumem, okluzí ani vzdáleností“
([Terrain3D – Instancer](https://terrain3d.readthedocs.io/en/latest/docs/instancer.html)). Instance zmenšené na 0 stále
projdou vertex shaderem; jeden uživatel hlásí, že „škálování na nulu FPS nevrátilo“
([forum: Optimising performance with terrain](https://forum.godotengine.org/t/optimising-performance-with-terrain/19635)).
Naše GPU mřížka kolem kamery je kruh 360° → **vrcholy za kamerou se počítají zbytečně** (a podle 1a dvakrát). [hypotéza]

---

## 2. Co dělají Godot projekty

| Projekt | Jak kreslí trávu | Mobil / Compatibility | Poznatky pro nás |
|---|---|---|---|
| **Terrain3D** (TokisanGames) | Instancer: MultiMesh po buňkách **32×32 m**, LOD po buňkách (max. 10, doporučeno ≤4), `last_shadow_lod`, `shadow_impostor`; alternativa „particle shader“ = instance generované na GPU kolem kamery bez dat | Compatibility plně od Terrain3D 1.0 + Godot 4.4; Android „experimentální“, `max_regions` 64–256, ETC2/ASTC ([platforms](https://terrain3d.readthedocs.io/en/latest/docs/platforms.html)); výchozí dosah MMI snížen na **64 m** ([releases](https://github.com/TokisanGames/Terrain3D/releases)) | Buňky 32 m = ořez frustumem; stín jen z bližších LOD; žádná čísla výkonu pro mobil |
| **HTerrain** (Zylann) | Detail layers: MultiMesh po chunkách, hustota z 8bit mapy, instance skryté ve vertex shaderu, **alpha scissor**, normála terénu místo vlastní; v dálce **zvedá práh scissoru** (řídne), alternativa „zasunout do země“ | Bez mobilních poznámek ([docs](https://hterrain-plugin.readthedocs.io/en/latest/)) | `u_view_distance` ořez chunků; tint z global mapy terénu = splývání s terénem |
| **GodotGrass** (2Retr0) | Geometrická stébla (2 sítě HQ/LQ), MultiMesh, LOD po dlaždicích, Ghost-of-Tsushima tvar | Mobil neřeší; autor: stíny trávy „very high performance cost“, přepínání LOD „velmi viditelné“ ([GitHub](https://github.com/2Retr0/GodotGrass)) | Stíny trávy vypnout; stébla jen blízko |
| **Spatial Gardener** (dreadpon) | Octree + MultiMesh, malování | „tisíce instancí bez propadu“, jen Windows ukázka ([GitHub](https://github.com/dreadpon/godot_spatial_gardener)) | Nic mobilního |
| **ProtonScatter / ScatterShot** | MultiMesh po chuncích | Kompromis: víc chunků = lepší ořez, ale víc draw callů ([ScatterShot](https://store.godotengine.org/asset/helvetica-scenario/scattershot/), [forum 143319](https://forum.godotengine.org/t/multimesh-vs-renderingserver-meshinstances-for-an-extremely-high-number-of-instances/143319)) | Středně velké chunky |
| **SimpleGrassTextured** (IcterusGames) | Kreslení trsů karet, MultiMesh | Volba „vypnout stíny“ pro nízkou trávu ([GitHub](https://github.com/IcterusGames/SimpleGrassTextured)) | – |
| **godot-landscaper** | Billboard/CrossBillboard; chunky „zatím nejsou“ ([README](https://github.com/dip000/godot-landscaper)) | – | – |
| **Forum 141821** | MultiMesh chunky 5×5/10×10 m, 2 LOD + impostorové roviny v dálce; rada: výška z heightmapy ve vertex shaderu, `world_vertex_coords`; „impostor nepotřebuješ, když je terén otexturovaný“ ([vlákno](https://forum.godotengine.org/t/141821)) | – | Dálku řeší textura terénu |

Hledal jsem i „Open World“ dema a devlogy mobilních open-world her v Godotu: konkrétní měření trávy na Androidu jsem
nenašel (nejblíž `SirNeirda/godot_procedural_infinite_world`, bez zmínky o trávě). Reddit r/godot vlákno o trávě na
mobilu s čísly jsem nenašel; forum zmiňuje jen obecně „alfa textury zatěžují mobilní GPU, čím víc plochy, tím hůř“
([Island demo](https://godotforums.org/d/20549-island-demo)) a „na mobilu je fill rate omezený, i průhledné pixely se počítají“.

---

## 3. Kolik trávy mobilní GPU zvládne (cizí čísla)

| Zdroj | Zařízení | Čísla | Pozor |
|---|---|---|---|
| ColinLeung-NiloCat, Unity URP DrawMeshInstancedIndirect ([GitHub](https://github.com/ColinLeung-NiloCat/UnityURP-MobileDrawMeshInstancedIndirectExample)) | Adreno 612 (Galaxy A70) / Adreno 506 | 10 M instancí v datech, **50–60 fps při dohledu 125**, resp. ~30 fps při 75; výkon „hlavně podle počtu viditelných stébel“ | GPU culling compute shaderem (my nemáme), Vulkan/GLES 3.2, Unity; počet *viditelných* neuveden |
| Android/Arm „Armies“ demo ([developer.android.com](https://developer.android.com/games/optimize/geometry)) | mobil 2019+ | celá scéna **~210 000 trojúhelníků při ~30 fps** | celkový rozpočet, ne jen tráva |
| Unreal 4.17 test ([forum](https://forums.unrealengine.com/t/test-of-instanced-foliage-and-overdraw-with-opaque-masked-and-translucent-in-4-17/100351)) | GTX 750 Ti | 47 124 instancí: maska bez prázdných míst 82–86 fps, **maska s velkou prázdnou plochou 52–54 fps**; 4 990 instancí: 24 tri maskované 76–77 fps vs **216 tri neprůhledné 77–79 fps** | desktop, ale ukazuje, že **plocha zahozených pixelů stojí víc než 9× víc trojúhelníků** |
| Ghost of Tsushima, GDC 2021 ([GDC Vault](https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass); sekundárně [Stylized Station](https://threadreaderapp.com/thread/1688939411575119872)) | PS4 | stéblo **15 vrcholů blízko, 7 v dálce**, plynulé přelití LOD posunem vrcholů | konzole |

Pravidla od výrobců GPU:
- Android/Arm: „vrcholy jsou na mobilu velmi drahé“; **trojúhelníky držet nad 10 px plochy**, dlouhé tenké trojúhelníky
  jsou dražší; LOD po 50 % ([developer.android.com/games/optimize/geometry](https://developer.android.com/games/optimize/geometry)).
- Arm (forum inženýr): poměr fragmentů na primitivum držet **> 10**
  ([Arm community](https://community.arm.com/support-forums/f/graphics-gaming-and-vr-forum/6301/mali-gpu-counter)).
- → Geometrická stébla vycházejí v dálce jako mikro-trojúhelníky = špatné; blízko (velké na obrazovce) jsou v pořádku.

**Závěr pro rozpočet [hypotéza]:** spolehlivé číslo „X instancí na Mali/Adreno v Compatibility“ neexistuje. Z cizích
dat: celá scéna ~200 k trojúhelníků při 30 fps na střední třídě; tráva by měla být řádově **desítky tisíc viditelných
trojúhelníků** a hlavně **malá plocha zahozených (discard) pixelů**. Odhad našeho stavu z výchozích uniformů
`trava_gpu.gdshader` (krok 0,36 m, 3 karty = 6 tri, r_out 20 m): πr² ≈ 1 257 m² / 0,13 m² ≈ 9 700 trsů ≈ 58 000 tri
jen v plném kruhu do 20 m, z toho za kamerou ~2/3 zbytečně, a ×2 kvůli pasáži stínu (1a). **NEOVĚŘENO** – skutečný krok
a počet instancí na tabletu je třeba vypsat z běhu.

---

## 4. Alpha scissor vs. alpha hash vs. neprůhledné na mobilních GPU

- **Godot docs:** Alpha Scissor „rychlejší než Alpha, bez problémů s řazením“; Alpha Hash = dithering; Depth Pre-Pass
  „za cenu výkonu“; alfa-blendované materiály „výrazně pomalejší, hlavně když se překrývají“
  ([StandardMaterial3D](https://docs.godotengine.org/en/4.4/tutorials/3d/standard_material_3d.html)). Alpha hash v GLES3
  je také `discard` (stejný `ALPHA_SCISSOR_USED`/`uses_alpha_clip` větev, `material_storage.cpp` ř. 2960–2963) → **pro
  výkon žádná výhra oproti scissoru**.
- **Mali:** blending i discard vypínají optimalizace proti overdraw. FPK (Forward Pixel Kill) potřebuje okluder
  „neprůhledný… se známým pokrytím – tedy žádné discardy, žádné alpha-to-coverage“
  ([Arm community – FPK / early ZS](https://community.arm.com/support-forums/f/graphics-gaming-and-vr-forum/54421/subpasses-alpha-blending-fpk-early-zs)).
  Logika je per-pipeline a Mali se snaží EZ/FPK obnovit hned po takových drawech → **neprůhledné věci nakreslené před
  trávou ji pořád zakrývají; tráva sama ale nezakrývá trávu za sebou.**
- **Adreno:** oficiální FAQ: „discard/clip nemá vliv na LRZ, jde na plné rozlišení Z ve všech situacích“
  (citováno ve [výsledcích Qualcomm FAQ](https://developer.qualcomm.com/sites/default/files/docs/adreno-gpu/snapdragon-game-toolkit/gdg/gpu/faq.html),
  stránka teď přesměrovává). Na Questu (Adreno) komunita volí alfa-test, blending „nejde udělat výkonný“
  ([Unity forum](https://discussions.unity.com/t/any-clever-trick-for-tall-grass-on-mobile-quest/811738)) [názor].
- **Shrnutí:** pořadí cen na tablet: neprůhledná geometrie < alpha scissor ≈ alpha hash << alpha blend (i fade
  viditelnosti „Self“). Cena scissoru roste s **plochou prázdných (zahozených) pixelů karty × počet vrstev**.
- **Depth prepass v Compatibility:** viz 1c – na Mali/Adreno vypnutý. Cizí blog uvádí prepass jako hlavní zbraň proti
  foliage overdraw (8–15× → 1–2×) na desktopu ([cinevva blog](https://app.cinevva.com/blog/2026-05-11-foliage-overdraw));
  pro dlaždicové GPU je to sporné (PowerVR výslovně „nedělat prepass“ –
  [Imagination](https://docs.imgtec.com/starter-guides/powervr-architecture/html/topics/rules/do-not-use-depth-pre-pass.html)).

---

## 5. Co v Compatibility rendereru konkrétně stojí (tráva)

| Prvek | Cena v Compatibility | Zdroj |
|---|---|---|
| **Stín slunce zapnutý (celá scéna)** | +1 celá pasáž (vrcholy + fragmenty + PCF5/13 vzorků stínu) pro každý *ne-unshaded* materiál, i když sám stín nepřijímá | [zdroj Godot] 1a |
| **Omni/Spot se stínem v dosahu AABB** | +1 pasáž na světlo pro celou instanci (u MultiMeshe celá buňka) | [zdroj Godot] 1a |
| Omni/Spot bez stínu | v základní pasáži, max. 8 na mesh (`max_lights_per_object`) – smyčka per pixel (u `vertex_lighting` per vrchol) | [docs renderers](https://docs.godotengine.org/en/4.4/tutorials/rendering/renderers.html) |
| `vertex_lighting` | v 4.4 GLES3 funguje (`material_storage.cpp` ř. 1375–1377, `scene.glsl` USE_VERTEX_LIGHTING); docs: „na slabých/mobilních zařízeních výrazně zvyšuje výkon“. Pasáž stínu ale zůstává | [zdroj Godot] + docs |
| `unshaded` | žádné světlo, **žádná aditivní pasáž**; barvu dodat uniformem (u nás `svetlo`) | [zdroj Godot] |
| Normal mapa | +1 vzorek textury + TBN v fragmentu; v trávě zbytečná (docs: v dálce vypínat normal mapy) | [visibility ranges](https://docs.godotengine.org/en/4.4/tutorials/3d/visibility_ranges.html) |
| Vrhání stínu trávou | další vykreslení do shadow mapy (s discard) pro každou kaskádu; u nás už `SHADOW_CASTING_OFF` (`louka.gd:956`, `trava_gpu.gd:110`), kromě `louka.gd:1073` „if stin“ | GodotGrass, Terrain3D |
| `BACKLIGHT`, `diffuse_lambert_wrap` | drobné ALU navíc v každé světelné pasáži | – |
| Fade viditelnosti „Self“ / distance fade Pixel Alpha | přepne do průhledné pasáže (řazení, blending) – nepoužívat; Pixel/Object Dither = discard | [StandardMaterial3D](https://docs.godotengine.org/en/4.4/tutorials/3d/standard_material_3d.html) |
| Automatický instancing | v Compatibility není, jen MultiMesh | [Optimizing 3D](https://docs.godotengine.org/en/4.4/tutorials/performance/optimizing_3d_performance.html) |
| `dFdx/dFdy` + `textureSize` (náš mip-fix alfy, `stebla.gdshader` ř. 130–132) | malá ALU, ale v každé pasáži | – |
| Vzorek `stanoviste` + `sum` (barva terénu) | +2 vzorky textury na pixel trávy | – |

---

## 6. Tvar trsu: co je nejlevnější

1. **Neprůhledná geometrická stébla (bez alfy)** – žádný discard → early-Z/FPK/LRZ fungují, overdraw se ořízne hardwarem.
   Unreal test: 216 tri neprůhledné ≥ 24 tri maskované. Cena: víc vrcholů; v dálce mikro-trojúhelníky (< 10 px) → jen
   blízko (cca do 8–15 m), s LOD 15 → 7 vrcholů (GoT) nebo 5 → 3 (trojúhelník).
2. **Karty ořezané podle tvaru alfy (card trimming)** – místo obdélníku polygon 6–8 vrcholů kolem neprůhledné části;
   méně zahozených pixelů. Unreal test: velká prázdná plocha karty 84 → 53 fps, maska bez prázdných míst ≈ bez ceny.
3. **Méně karet na trs** – 3 zkřížené karty = až 3 vrstvy discardu na pixel; 2 karty nebo 1 karta „V“ pro dálku.
4. **Shell/plochá textura terénu** – nejlevnější pro dálku: žádné instance (HTerrain tint, forum 141821 „stačí
   otexturovaný terén“).

---

## 7. Jak skrýt hranici trávy

- **Barva terénu = barva trávy** v pásmu, kde tráva končí (KCD `e_vegetationUseTerrainColorDistance`; HTerrain
  global map tint). U nás `barva_krajiny.gdshaderinc` už existuje → **posunout konec trávy blíž a nechat dálku na
  textuře terénu** s šumem/„trávovou“ detail texturou.
- **Zánik po trsech podle hashe + zmenšení k patě** (už máme): žádná čára. HTerrain místo toho zvedá práh scissoru
  (řídnutí), alternativně „zasunutí do země“.
- **Zvětšit trsy v řídkém pásmu** (máme `mix(1.0, 1.6, dal)`) – méně instancí pokryje stejnou plochu.
- **Nerovnoměrná hranice** – posun konce o šum (máme `(hs-0.5)*8`), plus nízkofrekvenční šum ve světových souřadnicích,
  ať hranice není kruh kolem hráče.
- **Fog/atmosféra** zakryje rozdíl detailu v dálce (Compatibility fog podporuje).

---

## 8. Shader triky

- **Bez discard v dálce:** v pásmu za ~15 m nahradit karty neprůhledným tvarem (trojúhelník/„stříška“ bez alfy) nebo
  úplně texturou terénu. Discard má smysl jen tam, kde je tvar stébla vidět.
- **Zmenšení do dálky místo zániku** (vertex): degenerované trojúhelníky se nerasterizují (žádný fragment), ale vertex
  shader běží dál – proto zmenšit *a* zároveň mít méně instancí v MultiMeshi (prstence s vlastním počtem instancí,
  `visible_instance_count`).
- **Vítr jen ve vertex shaderu**, bez textury šumu ve fragmentu; vítr jen pro vrchní vrcholy (UV.y), v dálce vypnout.
- **Vynechat světla:** `unshaded` + uniform barvy světla z denní doby (eliminuje pasáž stínu – 1a). Stín stromů na
  trávě nahradit: (a) vzorkem upečené „stínové mapy“ krajiny shora (textura v rozlišení ~0,5 m, pečená z polohy stromů
  a slunce jednou za X minut herního času), nebo (b) ztmavením podle `barva_krajiny`/AO pod korunami.
- **Normály nahoru** (máme) – žádná normal mapa.
- **Levnější fragment v dálce:** materiál pro vzdálený prstenec bez `stanoviste`, `dFdx`, `BACKLIGHT`.
- **Nepoužívat** fade viditelnosti „Self“, distance fade Pixel Alpha, alpha blend, `alpha_to_coverage*` (v GLES3 bez
  efektu, 1b).

---

## 9. Doporučení seřazená podle přínosu pro náš případ

Pořadí = odhad přínosu (hypotéza, ne měření). Podle pravidel CLAUDE.md nejdřív izolovat, pak opravovat.

| # | Doporučení | Proč (zdroj) | Očekávaný přínos | Náročnost |
|---|---|---|---|---|
| 1 | **Rozkladové varianty měřicí trasy**: (a) tráva `unshaded`, (b) slunce bez stínu, (c) `prah = 0` (karty bez discardu, jen pro měření), (d) `velikost = 0` (zbude čistá cena vrcholů), (e) jen prstenec do 20 m | zjistí, kolik z +7–13 ms je pasáž stínu / discard / vrcholy | nutné rozhodnutí místo hádání | malá (přepínače v `louka.gd`/`trava_gpu.gd`, 1 jízda) |
| 2 | **Tráva `unshaded` na tabletu** (dokončit odloženou variantu `TVRZ_UNSHADED`; černá na PC = vyřešit zvlášť, možná souvisí s `BACKLIGHT`/A2C) | 1a: odstraní celou aditivní pasáž stínu slunce i stínovaných lamp | potenciálně až ~polovina nákladu trávy (vrcholy i fragmenty 2× → 1×) | malá–střední |
| 3 | **Vyřadit trávu ze stínovaných Omni/Spot** (cull mask světel bez vrstvy trávy, nebo stín lamp na tabletu vypnout) | 1a: každé stínované světlo v AABB buňky = další pasáž celé buňky | velký v noci/u ohňů, p95 špičky | malá |
| 4 | **Ořez mřížky frustumem**: GPU mřížku rozdělit do 6–12 výsečí/chunků (vlastní MMI s `custom_aabb`) nebo posunout mřížku před kameru | 1d: MultiMesh neořezává instance; za kamerou ~2/3 vrcholů zbytečně | vertex náklad −50–60 % [odhad] | střední |
| 5 | **Zkrátit pásmo trávy** (plná do ~15 m, řídká do ~35–40 m) a dálku nechat na barvě/šumu terénu | Terrain3D výchozí dosah 64 m; forum 141821; méně instancí = méně vrcholů i discardu | střední až velký | malá (uniformy `r_out`, `hust_do`, `hust_konec`) |
| 6 | **Ořezat karty podle alfy** (6–8vrcholový obrys místo obdélníku, `blender/atlas_travy.py`) | Unreal test: prázdná plocha karty je hlavní cena masky | střední (méně zahozených pixelů) | střední |
| 7 | **Méně vrstev na trs**: 3 → 2 karty, v dálce 1 karta | méně překryvu discardu | střední | malá |
| 8 | **Neprůhledná geometrická stébla do ~8–10 m** (bez alfy, 5–7 vrcholů na stéblo, LOD na 3) | early-Z/FPK/LRZ fungují jen bez discardu (Arm, Qualcomm); Unreal 216 tri opaque ≥ 24 tri masked; GoT 15/7 vrcholů | velký pro blízkou trávu, která zabírá nejvíc obrazovky | velká (nový model + vzhled) |
| 9 | **Lehčí fragment v dálce**: druhý materiál pro vnější prstenec bez `stanoviste`, `dFdx`, `BACKLIGHT` | každý vzorek textury × pasáže × overdraw | malý–střední | malá |
| 10 | **Zkusit depth prepass jen na Adreno** (`rendering/driver/depth_prepass/disable_for_vendors` bez „Adreno“) | 1c; LRZ + prepass může snížit overdraw discardu, ale vrcholy 2× | nejistý (může i zhoršit) | malá (1 nastavení, měřit) |
| 11 | **Opravit komentáře a předpoklady** v `stebla.gdshader` / `trava_gpu.gdshader` („bez discard“, A2C) – A2C v GLES3 nic nedělá | 1b; aby další rozbor nestavěl na chybném předpokladu | – (prevence) | malá |
| 12 | **3D rozlišení < 1,0 jen pro 3D** (`scaling_3d_scale` ~0,8) – fill rate klesá s počtem pixelů | obecně fill-rate; podporu bilineárního škálování v Compatibility 4.4 **ověřit** | střední pro p95 | malá (ověřit podporu + vzhled UI) |

Nedoporučuji: alpha blend / fade viditelnosti „Self“ (průhledná pasáž), MSAA + A2C (pravidlo projektu), compute culling
(Compatibility nemá compute), další zjemňování GPU mřížky (problém není CPU).

---

## Zdroje
- Godot 4.4.1-stable zdroják: [rasterizer_scene_gles3.cpp](https://github.com/godotengine/godot/blob/4.4.1-stable/drivers/gles3/rasterizer_scene_gles3.cpp),
  [scene.glsl](https://github.com/godotengine/godot/blob/4.4.1-stable/drivers/gles3/shaders/scene.glsl),
  [config.cpp](https://github.com/godotengine/godot/blob/4.4.1-stable/drivers/gles3/storage/config.cpp),
  [material_storage.cpp](https://github.com/godotengine/godot/blob/4.4.1-stable/drivers/gles3/storage/material_storage.cpp),
  [rendering_server.cpp](https://github.com/godotengine/godot/blob/4.4.1-stable/servers/rendering_server.cpp)
- Godot docs: [Renderers](https://docs.godotengine.org/en/4.4/tutorials/rendering/renderers.html),
  [Optimizing 3D](https://docs.godotengine.org/en/4.4/tutorials/performance/optimizing_3d_performance.html),
  [Visibility ranges](https://docs.godotengine.org/en/4.4/tutorials/3d/visibility_ranges.html),
  [StandardMaterial3D](https://docs.godotengine.org/en/4.4/tutorials/3d/standard_material_3d.html),
  [Internal rendering architecture](https://docs.godotengine.org/en/latest/engine_details/architecture/internal_rendering_architecture.html)
- Terrain3D: [Instancer](https://terrain3d.readthedocs.io/en/latest/docs/instancer.html), [Platforms](https://terrain3d.readthedocs.io/en/latest/docs/platforms.html), [Releases](https://github.com/TokisanGames/Terrain3D/releases)
- [HTerrain docs](https://hterrain-plugin.readthedocs.io/en/latest/), [GodotGrass](https://github.com/2Retr0/GodotGrass),
  [Spatial Gardener](https://github.com/dreadpon/godot_spatial_gardener), [SimpleGrassTextured](https://github.com/IcterusGames/SimpleGrassTextured),
  [godot-landscaper](https://github.com/dip000/godot-landscaper), [ScatterShot](https://store.godotengine.org/asset/helvetica-scenario/scattershot/)
- Forum: [141821](https://forum.godotengine.org/t/141821), [Optimising performance with terrain](https://forum.godotengine.org/t/optimising-performance-with-terrain/19635),
  [MultiMesh vs RS instances](https://forum.godotengine.org/t/multimesh-vs-renderingserver-meshinstances-for-an-extremely-high-number-of-instances/143319),
  [Island demo](https://godotforums.org/d/20549-island-demo)
- Mobilní GPU: [Android – geometry](https://developer.android.com/games/optimize/geometry),
  [Arm FPK/early ZS](https://community.arm.com/support-forums/f/graphics-gaming-and-vr-forum/54421/subpasses-alpha-blending-fpk-early-zs),
  [Arm counters](https://community.arm.com/support-forums/f/graphics-gaming-and-vr-forum/6301/mali-gpu-counter),
  [Qualcomm Adreno FAQ](https://developer.qualcomm.com/sites/default/files/docs/adreno-gpu/snapdragon-game-toolkit/gdg/gpu/faq.html),
  [Imagination – no depth prepass](https://docs.imgtec.com/starter-guides/powervr-architecture/html/topics/rules/do-not-use-depth-pre-pass.html)
- Unity/Unreal: [Mobile DrawMeshInstancedIndirect](https://github.com/ColinLeung-NiloCat/UnityURP-MobileDrawMeshInstancedIndirectExample),
  [GPU Instancer](https://wiki.gurbu.com/), [Unreal foliage overdraw test](https://forums.unrealengine.com/t/test-of-instanced-foliage-and-overdraw-with-opaque-masked-and-translucent-in-4-17/100351),
  [Unity Quest grass](https://discussions.unity.com/t/any-clever-trick-for-tall-grass-on-mobile-quest/811738),
  [Foliage overdraw blog](https://app.cinevva.com/blog/2026-05-11-foliage-overdraw)
- Ghost of Tsushima: [GDC Vault](https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass)

Nenalezeno / neprověřeno: Acerola a Minions Art videa (desktop, geometry/compute shadery – pro GLES3 nepoužitelné),
konkrétní Reddit vlákna s měřením na Androidu, Brackeys (desktop geometry shader). Mobilní devlogy garážových open-world
her v Godotu s čísly trávy jsem nenašel.
