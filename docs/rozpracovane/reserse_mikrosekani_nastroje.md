# Rešerše: mikrosekání na tabletu + nástroje pro stavbu světa (28. 10.)

Výchozí stav: Godot 4.4.1, Android, `rendering_method.mobile="gl_compatibility"` (OpenGL ES 3), svět ~3 km,
MultiMesh vegetace s visibility_range, louka po buňkách ve vláknech, physics 60 Hz + interpolace, .pck za běhu.
Měřeno: 20–55 FPS, stovky záseků, občas 2,8 s; diag „kreslení+čekání“ 40–90 ms (= čas od konce `_process`
do dalšího snímku: odeslání GL příkazů, kompilace shaderů, nahrání bufferů a čekání na GPU/swap).

Značky: **[ověřeno]** = ověřeno přímo ve zdrojáku Godotu 4.4.1 nebo v oficiální dokumentaci, **[komunita]** = fórum
nebo blog, je potřeba si to změřit.

---

## TOP 10 podle poměru přínos/práce

| # | Co | Proč u nás | Práce |
|---|----|-----------|-------|
| 1 | **Zahřát shadery při načítání** (každý materiál × varianta, 1 snímek před kamerou za krycím ColorRectem) a za běhu nevytvářet nové materiály ani neměnit jejich vlastnosti | V Compatibility není ubershader ani předkompilace. Každá nová kombinace materiál/varianta se kompiluje při prvním kreslení přímo ve vlákně kreslení. To je typický zásek 100 ms až několik sekund. | malá |
| 2 | **Stíny zlevnit**: tráva, keře a drobné předměty `cast_shadow = OFF`, `directional_shadow_max_distance` 40–60 m, `soft_shadow_filter_quality.mobile` = 0–1, zvážit 2 rozdělení (splits) místo 4 | Compatibility kreslí stínící objekty ve **zvláštním průchodu**. Každý stínící MultiMesh se tak kreslí dvakrát (do stínové mapy i do obrazu). | malá |
| 3 | **`rendering/limits/time/time_rollover_secs` = 30–60** (výchozí je 3600) | Na mobilu má `TIME` v shaderu nízkou přesnost. Pohyb trávy a vody ve větru pak po pár minutách „schodovitě poskakuje“. Vypadá to jako mikrosekání, i když FPS sedí. | 1 řádek |
| 4 | **Kamera mimo automatickou interpolaci**: kamera `top_level`, `physics_interpolation_mode = OFF`, v `_process` sleduje `hrac.get_global_transform_interpolated()`; po teleportu `reset_physics_interpolation()` | Při 20–55 FPS a fyzice 60 Hz se nejvíc projeví nesoulad mezi fyzikou a snímkem. Dokumentace 4.4 doporučuje kameru interpolovat ručně. | malá |
| 5 | **Fyzika 30 Hz** (`physics_ticks_per_second=30`, interpolace už běží) a `max_physics_steps_per_frame` = 3–4 | Při 20 FPS se teď za snímek spouští 3 kroky fyziky. Hrozí „spirála smrti“ (pomalý snímek → víc kroků fyziky → ještě pomalejší snímek). Pro chůzi stačí 30 Hz a interpolace pohyb vyhladí. | 1 řádek + test chůze |
| 6 | **Pevný cíl 30 FPS** (`Engine.max_fps = 30` na tabletu) a měřit histogram délek snímků | **Swappy v gl_compatibility neběží.** Ve 4.4.1 je jen ve Vulkan driveru (`swappyVk`), takže `enable_frame_pacing=true` nám nic nedělá. Rovných 30 FPS působí plynuleji než skoky 20–55. | 1 řádek + měření |
| 7 | **Vegetace: visibility fade vypnout** (`FADE_DISABLED` + margin jako hystereze), těsný `custom_aabb` na každý MultiMesh, jeden MultiMesh na buňku a pásmo LOD | **Compatibility 4.4.1 fade vůbec nekreslí** (`rasterizer_scene_gles3` nečte `fade_near`/`fade_far`), přepíná okamžitě. `FADE_SELF` nám nic nedává a v Mobile/Forward+ by vynutil průhledný průchod. Velké AABB = kreslí se všechno. | malá |
| 8 | **MultiMesh znovu používat** (bazén, `visible_instance_count`), plnit jedním `multimesh.buffer = PackedFloat32Array` připraveným ve vlákně, nevytvářet nové MultiMesh/MMI pro každou buňku | Změna `instance_count` znovu alokuje GPU buffer. Nové uzly a zdroje stojí `add_child`, nový materiál = riziko kompilace. | střední |
| 9 | **Zásek 2,8 s dohledat systémovou stopou**: Perfetto `record_android_trace` (bez vlastního buildu) a značky v diag kolem každého `load()`, `load_threaded_get`, `wait_for_task_completion`, `add_child` a nového materiálu | Tak dlouhý zásek nebude „pomalé kreslení“. Půjde o synchronní věc: kompilaci a zápis shader cache, blokující načtení, čekání na vlákno nebo přehřátí. | malá |
| 10 | **`rendering/limits/opengl/max_lights_per_object` = 2–4** (výchozí 8) a co nejméně světel se stíny | Podle dokumentace to zkrátí kompilaci shaderů a zrychlí kreslení na slabém mobilu. Issue #86731 uvádí velký počet světel jako jednu z příčin pomalé kompilace. | 1 řádek |

Další krok, pokud TOP 10 nestačí: **A/B test `rendering_method.mobile="mobile"` (Vulkan)**. Získá se tím
předkompilace pipeline a ubershadery z 4.4 i Swappy, ale vzhled se změní a Vulkan drivery na Androidu mají různou kvalitu
(pravidlo tabletu: bez MSAA a bez screen texture platí dál). Práce je velká hlavně kvůli kontrole vzhledu.

---

## 1) Mikrosekání a pacing snímků

### 1.1 Kompilace shaderů v Compatibility (hlavní podezřelý na záseky)
- **Co:** OpenGL kompiluje shader až při prvním kreslení a jen ve vlákně kreslení, celé kreslení přitom stojí.
  Předkompilace a ubershadery z 4.4 platí jen pro Forward+ a Mobile. Pro Compatibility dokumentace radí jedině
  „preloading materials, shaders, and particles by displaying them for at least one frame“. **[ověřeno]**
- **Shader cache:** `rendering/shader_compiler/shader_cache/enabled` je ve výchozím stavu zapnutá. GLES3 ukládá binárky
  (`glGetProgramBinary`) na disk do `user://`, takže **první spuštění po instalaci** a každá nová kombinace se kompilují.
  Při každé nové variantě (specialization) se celý soubor cache přepisuje synchronně, což přidává další zásek
  (issue #86731). Na Adreno 3xx je cache pro transform feedback (částice) vypnutá. **[ověřeno ve zdrojáku]**
- **Stav oprav:** #87558 snížil počet permutací shaderů (zhruba −40 % času). PR #124566 („Overhaul GLES3 shader
  compiler“: kompilace 6–8× rychlejší, cache se ukládá jen při změně) je **otevřený, milník 4.9**, takže pro 4.4 se
  nedá počítat. Issue #86731 je stále otevřené (v říjnu 2026 hlášeno i na 4.7.2 na Pixelu 5).
- **Co udělat:**
  - Zahřívací scéna: po načtení (a při prvním načtení každé sady .pck) postavit před kameru řadu malých kopií
    **všech** materiálů v kombinacích, jak se ve hře kreslí: MeshInstance i MultiMesh, se stínem i bez, ve světle
    pochodně. Obraz překryje neprůhledný `ColorRect`, nechá se vykreslit 2–3 snímky a pak se scéna smaže. Diag už
    počítá „nové materiály ve snímku“, a to je přesně seznam míst, kde se kompiluje.
  - Za běhu neměnit vlastnosti materiálu, které mění shader (transparency, shading_mode, cull, `ALPHA` ano/ne,
    flagy textur). Uniformy (barva, parametry) se měnit smí. Materiály sdílet přes `.tres`, nedělat
    `StandardMaterial3D.new()` v kódu stavby.
  - Méně různých shaderů = méně kompilací (sjednotit materiály trávy, keřů a listí do jednoho shaderu s atlasem).
- Odkazy: [Pipeline compilations (docs)](https://docs.godotengine.org/en/stable/tutorials/performance/pipeline_compilations.html) ·
  [#86731 Slow shader compilation in Compatibility](https://github.com/godotengine/godot/issues/86731) ·
  [PR #124566](https://github.com/godotengine/godot/pull/124566) ·
  [Forum: precache shaderů](https://forum.godotengine.org/73069/how-to-make-sure-all-shaders-are-pre-cached-to-avoid-lag-spikes)

### 1.2 Swappy / frame pacing, vsync, max_fps
- **Co:** Swappy (Android Frame Pacing) srovnává snímky s obnovováním displeje. Godot ho přidal v PR #96439
  (`display/window/frame_pacing/android/enable_frame_pacing`, `swappy_mode`).
- **Proč nás se to týká:** ve 4.4.1 je Swappy jen v `drivers/vulkan` (`swappyVk.h`). Pro GLES3 se nepoužije
  **[ověřeno ve zdrojáku]**, takže náš `enable_frame_pacing=true` nemá žádný účinek.
- **Co udělat:** na tabletu nastavit `Engine.max_fps = 30` (nebo projektové `application/run/max_fps` s přepisem
  pro android přes feature tag) a změřit rozptyl délek snímků. Omezovač v Godotu uspává CPU, což se může tlouct
  s vsync (16/50 ms střídavě). Proto měřit percentily, ne průměr. Pokud tablet běží na 90/120 Hz, vyjde 30 lépe
  (dělitel 120). Swappy ve Vulkanu (`swappy_mode` auto) by sám „spadl“ na rovných 30 při 40–60 FPS, jak popisuje
  dokumentace.
- Odkazy: [ProjectSettings 4.4: frame_pacing, max_fps](https://docs.godotengine.org/en/4.4/classes/class_projectsettings.html) ·
  [PR #96439 Swappy](https://github.com/godotengine/godot/pull/96439) ·
  [Android Frame Pacing](https://developer.android.com/games/sdk/frame-pacing) ·
  [Jitter, stutter and input lag](https://docs.godotengine.org/en/4.4/tutorials/rendering/jitter_stutter.html)

### 1.3 Fyzika a interpolace
- **Kamera:** dokumentace 4.4 výslovně doporučuje kameru interpolovat ručně: `top_level = true`,
  `set_physics_interpolation_mode(PHYSICS_INTERPOLATION_MODE_OFF)` a v `_process` pozici z
  `cil.get_global_transform_interpolated()`. Otáčení dotykem a myší aplikovat přímo v `_process`, ne ve fyzice.
  Pokud kamera sleduje `global_transform` hráče, poskakuje při každém tiku. **[ověřeno]**
- **Teleport/respawn/načtení:** nejdřív nastavit transform, potom `reset_physics_interpolation()`. Opačné pořadí
  způsobí „šmouhu“ (streaking).
- **MultiMesh:** interpolace instancí jen přes `set_buffer_interpolated` / `reset_instance_physics_interpolation`.
  Statickou vegetaci nechat bez interpolace (u statických MMI `physics_interpolation_mode = OFF` je bezpečné).
- **Krokování:** `physics_jitter_fix` se při zapnuté interpolaci vypíná sám. Při 20 FPS se za snímek simulují 3 tiky.
  30 Hz fyzika s interpolací ušetří polovinu CPU. `max_physics_steps_per_frame` 3–4 zabrání spirále smrti
  (hra se pak jen zpomalí, nezamrzne).
- Odkazy: [Advanced physics interpolation (kamera, MultiMesh)](https://docs.godotengine.org/en/4.4/tutorials/physics/interpolation/advanced_physics_interpolation.html) ·
  [Using physics interpolation](https://docs.godotengine.org/en/4.4/tutorials/physics/interpolation/using_physics_interpolation.html)

### 1.4 add_child / instantiate / načítání za běhu / .pck
- **Co:** `load_threaded_request` přesune do vlákna jen čtení a parsování. `instantiate()` a `add_child()` (vstup do
  stromu, `_ready`, registrace do RenderingServeru a fyziky) běží vždy v hlavním vlákně.
  `load_threaded_get()` **blokuje**, pokud se ještě nedonačetlo (napřed `load_threaded_get_status`). **[ověřeno]**
- **Co udělat:**
  - Žádné `load()` ani `preload` velkých věcí během hry. Vše přes `load_threaded_request` a výsledek brát až ve stavu
    `THREAD_LOAD_LOADED` (u `life.gd`, `ruchy.gd` a `main.gd` to tak už je, zkontrolovat zbytek, hlavně načítání .pck).
  - Uzly připravit dopředu (bazén) a jen je přepínat (`visible`, `process_mode`) místo nových instancí. Případně kulisy
    bez logiky kreslit přímo přes `RenderingServer.instance_create()` / `instance_set_base()` bez uzlů ve stromu.
  - Rozpočet v µs za snímek pro stavbu (louka ho má, stejný vzor použít i pro předměty, budovy a stromy).
  - `WorkerThreadPool.wait_for_task_completion` v hlavním vlákně volat jen na úlohu, o které víme, že je hotová
    (`is_task_completed`). Jinak je to skryté čekání.
  - Textura nebo mesh načtené ve vlákně se do GPU nahrávají při vytvoření nebo prvním použití. Velká textura
    (4k) = zásek. Na tabletu držet menší mip/rozlišení (už se řeší v `textury_tablet.py`). **[komunita]**
- **GC:** GDScript nemá garbage collector (počítá reference), ale vytváření Array/Dictionary/String v každém snímku stojí
  alokace. V horkých smyčkách používat Packed*Array a znovu použitelné bufferu.
- Odkazy: [Background loading](https://docs.godotengine.org/en/4.4/tutorials/io/background_loading.html) ·
  [Forum: add_child stále seká](https://forum.godotengine.org/t/understanding-and-smoothing-resource-management-of-godot-4/95761)

### 1.5 MultiMesh, visibility_range a vegetace
- **AABB:** MultiMesh se ořezává (culling) jako jeden celek. Rozlezlé instance = kreslí se vždy všechny. Na každou
  buňku vlastní MMI a těsný `custom_aabb`. **[ověřeno, docs MultiMesh]**
- **LOD:** všechny instance v jednom MultiMeshi mají stejný LOD, který se vybírá podle bodu AABB nejblíž ke kameře.
  Proto je potřeba samostatný MultiMesh pro každé pásmo (blízko plný mesh, dál zjednodušený, nejdál impostor).
  **[ověřeno + komunita]**
- **Fade:** v Compatibility 4.4.1 se fade nekreslí (viz TOP 7). V Mobile/Forward+ by `FADE_SELF` vynutil průhledný
  průchod. Mizení trávy v dálce dělat ve vertex shaderu (zmenšit instanci podle vzdálenosti k nule), ne přes alfu.
- **Alfa:** alpha scissor drží listí v neprůhledném průchodu (lepší než blend). Na dlaždicových (tile) GPU ale
  `discard` ruší brzké odmítání hloubkou (early-Z), takže overdraw trávy je drahý. Méně vrstev a menší plochy karet,
  případně plná geometrie stébel bez alfy. **[komunita, změřit]**
- **Compatibility a custom data:** instanční custom data se ukládají jen v **16 bitech**, takže tam nedávat přesná čísla.
  **[ověřeno, docs]**
- **Plnění:** `multimesh.buffer = PackedFloat32Array` naráz místo tisíců `set_instance_transform`.
  `instance_count` a formát nastavit jen jednou, MultiMesh znovu používat (měnit jen `visible_instance_count`).
- **Rozpočet draw callů:** diag má max 1500. Pro GLES3 na mobilu je to hodně a stínový průchod to ještě zvyšuje.
  Cíl: pod 500 v obraze.
- Odkazy: [Visibility ranges (HLOD) 4.4](https://docs.godotengine.org/en/4.4/tutorials/3d/visibility_ranges.html) ·
  [MultiMesh](https://docs.godotengine.org/en/4.4/classes/class_multimesh.html) ·
  [Forum: les tisíců stromů 4.7](https://forum.godotengine.org/t/best-approach-for-rendering-a-procedurally-generated-forest-with-thousands-of-trees-in-godot-4-7/141770) ·
  [GodotFest 2025: Plants, Polygons and Pixels (velká vegetace)](https://media.ccc.de/v/godotfest2025-plants-polygons-and-pixels-large-scale-vegetation-rendering-in-godot)

### 1.6 Stíny a světla v Compatibility
- **Co:** Compatibility kreslí světla bez stínů v jednom průchodu, ale světla se stínem **vícepruchodově**: první průchod
  unese 1 směrové světlo se stínem, každé další stínící omni/spot přidá další průchod přes osvětlené objekty.
  Stínová mapa = další kreslení všech stínících objektů. **[ověřeno, docs Internal rendering architecture]**
- **Co udělat:** stín jen ze slunce, pochodně bez stínů. `cast_shadow` vypnout u trávy, keřů, drobností a impostorů.
  `directional_shadow_max_distance` zkrátit, mapu 2048 nechat, soft filtr na mobilu 0–1.
  `max_lights_per_object` 2–4.
- Odkazy: [Internal rendering architecture](https://docs.godotengine.org/en/4.4/contributing/development/core_and_modules/internal_rendering_architecture.html)

### 1.7 Přehřátí (thermal throttling)
- **Co:** po pár minutách tablet sníží frekvence. V případové studii Lineage W spadlo FPS z 60 na 32 za ~4 min.
  Vypadá to jako „zhoršování v čase“. **[ověřeno, Android docs]**
- **Co udělat:** do diag logu přidat teplotu nebo stav (`adb shell dumpsys thermalservice`) a FPS v čase. Rovných 30 FPS
  (TOP 6) samo snižuje zahřívání. Godot nemá hotový ADPF plugin, Thermal API (Android 11+) by šlo jen přes vlastní
  Android plugin.
- Odkazy: [ADPF Thermal API](https://developer.android.com/games/optimize/adpf/thermal) ·
  [ADPF best practices](https://developer.android.com/games/optimize/adpf/best-practices-adpf)

### 1.8 Co měřit a jak
1. **V Godotu (bez nástrojů):** `RenderingServer.viewport_set_measure_render_time(vp, true)` a pak
   `get_measured_render_time_cpu/gpu`. Tak se odliší „GPU nestíhá“ (vysoké GPU) od „CPU odesílá a kompiluje“
   (vysoké CPU kreslení, GPU nízké). Dále `Performance.get_monitor(RENDER_TOTAL_DRAW_CALLS_IN_FRAME,
   RENDER_TOTAL_PRIMITIVES_IN_FRAME)` a vlastní monitory `Performance.add_custom_monitor`. Logovat **percentily**
   (p50/p95/p99, „1 % low“) a počet snímků nad 50 a 100 ms, ne jen průměr FPS.
2. **Heatmapa záseků podle polohy:** diag už loguje polohu hráče. Python skript (vzor `mapa_vyhledu.py`) vykreslí
   nad mapou délku snímku a počet záseků po buňkách 32 m. Hned je vidět, jestli zásek dělá místo (budova, nový
   materiál, hranice .pck), nebo pohyb (stavba buněk louky).
3. **Perfetto systémová stopa (bez vlastního buildu Godotu):**
   `python3 record_android_trace -o stopa.perfetto-trace -t 15s -b 64mb sched freq idle gfx view am wm power thermal`
   a otevřít na ui.perfetto.dev. Ukáže hlavní vlákno a vlákno kreslení, kdy čeká na `eglSwapBuffers`/fence, frekvence
   CPU a GPU a přehřátí. Kategorie `godot` vyžadují build s Perfetto (šablony až od 4.7).
4. **Android GPU Inspector (AGI):** System profile s typem **„OpenGL on ANGLE“** (AGI překládá GLES přes ANGLE
   do Vulkanu). Frame profile ukáže cenu jednotlivých draw callů (tráva, stínový průchod). Vybrat správný typ API,
   jinak AGI nic nezachytí.
5. **SurfaceFlinger:** `adb shell dumpsys SurfaceFlinger --latency "<jméno SurfaceView vrstvy>"` (posledních 128 snímků,
   jank = překročení periody), na Androidu 12+ `adb shell dumpsys SurfaceFlinger --frametimeline -jank`.
   `dumpsys gfxinfo <balík> framestats` měří jen UI vykreslované přes HWUI, ne GL SurfaceView hry, takže ho neber
   jako měřítko.
6. **Vzdálený profiler Godotu:** export s „Remote debug“ a one-click deploy, pak záložka Profiler/Visual Profiler
   (podporuje i Compatibility). Ladicí build je ale pomalejší než release, proto čísla brát relativně.
- Odkazy: [Perfetto v Godotu](https://docs.godotengine.org/en/4.7/engine_details/development/profiling/perfetto.html) ·
  [AGI frame profiler](https://developer.android.com/agi/frame-trace/frame-profiler) ·
  [AGI quickstart](https://developer.android.com/agi/start) ·
  [Perfetto FrameTimeline](https://perfetto.dev/docs/data-sources/frametimeline) ·
  [Debugger panel / profiler](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/debugger_panel.html)

### 1.9 Ostatní drobnosti
- `rendering/driver/threads/thread_model` (vícevláknové kreslení) je ve 4.4 **experimentální**, s pády. Nezapínat.
- Release vs. debug: na fóru jsou hlášené rozdíly v obou směrech. Měřit vždy stejný typ buildu. **[komunita]**
- Occlusion culling: dokumentace říká, že velké otevřené scény z něj moc nemají a více pomůže LOD a visibility_range.
  Stojí CPU. Ve světě zvážit vypnutí a ponechat ho jen v tvrzi (`occlusion_culling/use_occlusion_culling=true`
  teď běží všude). **[ověřeno, docs]**

---

## 2) Nástroje a postupy pro stavbu a ladění světa

### 2.1 Vizuální regresní testy
- **Deterministické snímky:** Movie Maker `--write-movie out.png --fixed-fps 30 --quit-after N` vyrábí PNG sekvenci
  bez vynechaných snímků, se stejným výstupem na rychlém i pomalém stroji (dostupné i v exportu). Pro focení míst:
  skript přesune kameru na seznam pevných bodů (z `pravidla`), vyrenderuje N snímků a uloží poslední.
- **Porovnání:** `odiff` (rychlé CLI, práh, ignorované oblasti, detekce antialiasingu) nebo `pixelmatch` (je i
  v Pythonu). Případně SSIM ze scikit-image. Ukládat diff PNG vedle snímku a referenci obnovovat jen po schválení
  (Míša). Navazuje na `tools/porovnej.py` a `over_obrazky.py`.
- **GDSnap** (MIT, Godot 4.4): knihovna pro snapshot testy přímo v Godotu.
- **Headless neumí renderovat:** `--headless` v Godot 4 použije dummy renderer, takže snímky z něj nejsou. Na Linuxu
  pustit pod `xvfb-run` s `--rendering-driver opengl3`.
- Odkazy: [Creating movies (Movie Maker)](https://docs.godotengine.org/en/4.4/tutorials/animation/creating_movies.html) ·
  [odiff](https://github.com/dmtrKovalenko/odiff) · [pixelmatch](https://github.com/mapbox/pixelmatch) ·
  [GDSnap](https://godotengine.org/asset-library/asset/4018) ·
  [Headless ≠ no-window](https://ask.godotengine.org/150510/godot-headless-not-same-godot-window-cant-render-the-backend)

### 2.2 Headless testy (logika, data, invarianty)
- **GUT** a **gdUnit4**: oba mají CLI, JUnit XML výstup a běží `--headless`. gdUnit4 má navíc GitHub Action
  a HTML report. Hodí se pro testy generátorů (stejné semínko = stejný výstup), pravidel `pasma` (žádný strom v cestě,
  stavba ne na svahu) a rozpočtů (počet instancí na buňku, draw cally na buňku z dat, ne z renderu).
- Naše `test_smyslu.py` a `test_svet.gd` jsou správná cesta. Doplnit **property-based testy** (Python `hypothesis`):
  náhodná semínka a polohy a ověřit invarianty `pasma`, nejen pár ručně vybraných míst. A **JSON Schema** pro
  `pravidla/*.json`, aby se překlep v klíči nebo jednotce chytil dřív než ve hře.
- Odkazy: [gdUnit4](https://github.com/MikeSchulze/gdUnit4) · [GUT](https://github.com/bitwes/Gut) ·
  [Hypothesis](https://hypothesis.readthedocs.io/) · [JSON Schema](https://json-schema.org/)

### 2.3 Ladicí vizualizace
- **Debug Draw 3D** (DmitriySalnikov, GDExtension v C++, MIT, předkompilované i pro **Android**, verze pro 4.4.1+):
  čáry, boxy, AABB, text v 3D i 2D overlay. Hodí se pro zobrazení AABB MultiMeshů, hranic buněk, pásem `pasma`
  a os cest přímo na tabletu.
- **Mapa shora z dat** (Python, bez Godotu): vrstvy cest, budov, vody a vegetace a pásma odstupů barevně. Kolize vrstev
  zvýrazněné červeně. Navázat na `protokol_mapa.py`. Heatmapy: hustota instancí na buňku, draw cally na buňku
  (odhad z dat), záseky z diag logu (viz 1.8).
- Odkazy: [Debug Draw 3D](https://github.com/DmitriySalnikov/godot_debug_draw_3d) ·
  [GameFromScratch recenze](https://gamefromscratch.com/godot-debug-draw-3d-add-on/)

### 2.4 CI s Godotem
- `chickensoft-games/setup-godot` (GitHub Action, instaluje Godot a šablony) nebo Docker `barichello/godot-ci`
  (připnutá verze). Postup: `godot --headless --import`, testy (`gdUnit4`/GUT + `test_smyslu.py`), případně
  `--export-release`. Podpisový klíč jen jako CI secret, nikdy v repu.
- Odkazy: [setup-godot](https://github.com/chickensoft-games/setup-godot) · [godot-ci](https://github.com/abarichello/godot-ci)

### 2.5 Rychlý import a cache
- Složku `.godot/imported` a `.godot/shader_cache` mezi běhy nemazat (cache importu). Při CI ji cachovat podle hashe
  zdrojových assetů. První `--headless --import` je pomalý, další jen přírůstkové.
- Textury pro tablet: ETC2/ASTC (`import_etc2_astc=true` už je), mipmapy, menší rozlišení.

### 2.6 LOD a impostory
- **Octahedral Impostor LOD** (hdrsniped): pečení jedním klikem, přepínání přes visibility_range, ale oficiálně
  **jen Forward+ a Mobile**. V Compatibility nutno ověřit (pravděpodobně jen shader port).
- **godot-imposter** (zhangjt93, MIT, 4.4) a původní **wojtekpil Octahedral Impostors** (Godot 3, shader portovaný
  do 4). Pro Compatibility je nejbezpečnější vlastní jednoduchý impostor: 8–16 pohledů upečených v Blenderu do atlasu
  a billboard shader bez alfa blendu (scissor). Stejnou cestu (EZTree a Blender) popisuje i talk GodotFest 2025.
- Mesh LOD v Godotu (automatický při importu) funguje i u MultiMeshe, ale jeden LOD pro celý MultiMesh (viz 1.5).
- Odkazy: [Octahedral Impostor LOD](https://godotengine.org/asset-library/asset/5528) ·
  [Godot-Octahedral-Impostors](https://github.com/wojtekpil/Godot-Octahedral-Impostors) ·
  [Mesh LOD docs](https://docs.godotengine.org/en/4.4/tutorials/3d/mesh_lod.html)

### 2.7 Terén
- **Terrain3D:** shader v Compatibility **nefunguje** (Texture2DArray). Android je „experimental at best“. Pro nás tedy
  zůstat u vlastního ArrayMesh terénu po dlaždicích s LOD (sukně proti dírám) a těsnými AABB.
- Odkazy: [Terrain3D Mobile & Web](https://terrain3d.readthedocs.io/en/latest/docs/mobile_web.html)

### 2.8 Rozmisťování vegetace
- **Spatial Gardener** (octree, kreslení po povrchu, 4.4 ano, s 4.6+ problémy) a **Proton Scatter**. U nás je
  rozmístění daty řízené z pravidel, takže addon spíš jako inspirace (octree buňky, ~20k instancí na uzel bez stínů,
  podle fóra).
- Odkazy: [Spatial Gardener](https://github.com/dreadpon/godot_spatial_gardener) ·
  [Proton Scatter](https://github.com/HungryProton/scatter)

---

## Zdroje (souhrn)
- Godot docs: [pipeline compilations](https://docs.godotengine.org/en/stable/tutorials/performance/pipeline_compilations.html),
  [jitter/stutter](https://docs.godotengine.org/en/4.4/tutorials/rendering/jitter_stutter.html),
  [physics interpolation advanced](https://docs.godotengine.org/en/4.4/tutorials/physics/interpolation/advanced_physics_interpolation.html),
  [visibility ranges](https://docs.godotengine.org/en/4.4/tutorials/3d/visibility_ranges.html),
  [background loading](https://docs.godotengine.org/en/4.4/tutorials/io/background_loading.html),
  [ProjectSettings 4.4](https://docs.godotengine.org/en/4.4/classes/class_projectsettings.html),
  [Perfetto](https://docs.godotengine.org/en/4.7/engine_details/development/profiling/perfetto.html)
- GitHub: [#86731](https://github.com/godotengine/godot/issues/86731), [PR #124566](https://github.com/godotengine/godot/pull/124566),
  [PR #96439 Swappy](https://github.com/godotengine/godot/pull/96439),
  zdroják 4.4.1: `drivers/gles3/shader_gles3.cpp` (cache), `drivers/vulkan/rendering_device_driver_vulkan.cpp`
  (jediné místo se Swappy), `drivers/gles3/rasterizer_scene_gles3.cpp` (fade_near/far se nepoužívá)
- Android: [Frame pacing](https://developer.android.com/games/sdk/frame-pacing), [AGI](https://developer.android.com/agi/start),
  [ADPF thermal](https://developer.android.com/games/optimize/adpf/thermal)
- Fóra: [les 4.7](https://forum.godotengine.org/t/best-approach-for-rendering-a-procedurally-generated-forest-with-thousands-of-trees-in-godot-4-7/141770),
  [release vs debug Android](https://forum.godotengine.org/t/noticeable-stutter-frame-drops-on-android-release-version-works-better-on-debug-version/141035),
  [4.4 výkon Android](https://community.gamedev.tv/t/godot-4-4-performance-on-android/253061)
