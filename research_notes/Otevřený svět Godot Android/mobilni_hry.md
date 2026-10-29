# Jak dosahují výkonu vydané mobilní hry s otevřeným světem (rozpočty a postupy použitelné v Godotu 4 na Androidu)

Rešerše 29. 10. 2026, 21 nástrojových volání. Obecné zjištění: studia (miHoYo, Tencent/LightSpeed, Krafton, thatgamecompany,
NetEase/Blizzard, Infold) **veřejně nezveřejňují rozpočty po snímcích** (počty draw callů, trojúhelníků, paměť textur).
Ověřená čísla pocházejí hlavně z dokumentace enginů a výrobců (Epic, Google Android, Samsung/Unity, Arm, Qualcomm) a z několika
případových studií. Kde čísla chybí, je to uvedeno v Gaps, nic není odhadnuto.

## 1. Rozpočty na snímek, LOD/HLOD, poloměr streamování, hustota vegetace, stíny, cílové fps (podle her)

### Takeaway
Veřejně doložitelný je jen rámec: Epic pro mobilní Unreal udává ≤700 draw callů a ≤500k trojúhelníků na pohled (30 fps, staré
iPady); Honor of Kings (Tencent) vydává 1080p/60 fps od levných telefonů po vlajkové; Genshin má pro Android/iOS zvláštní,
upravenou renderovací cestu a mobil byl primární vývojovou platformou. Konkrétní rozpočty Genshinu, PUBG Mobile, Sky, Tower of
Fantasy, HSR, Infinity Nikki a Diabla Immortal jsem v primárních zdrojích nenašel.

### Cited Findings
- **Unreal mobil (oficiální Epic):** draw callů celé scény ≤700 na jeden pohled; trojúhelníků ≤500k na pohled – „maximum, které
  dosáhne 30 fps na iPad 4 a iPad Air“; 5 texture samplerů na materiál, použít všech 5 je „dost drahé“; čtvercové textury 2^n
  (256/512/1024); `mediump` místo `highp`; UV výpočty do vertex shaderu; masked/translucent jen na malé ploše obrazovky, protože
  „overdraw může zdvojnásobit i víc čas GPU snímku“; Bloom a DoF mohou na některých zařízeních stát 60 ms a víc; přednastavená
  viditelnost (Precomputed Visibility Volumes) pro occlusion — [Epic: Performance Guidelines for Mobile Devices](https://dev.epicgames.com/documentation/en-us/unreal-engine/performance-guidelines-for-mobile-devices-in-unreal-engine)
- Epic: nejsnazší snížení draw callů = méně unikátních meshů ve světě; slučování actorů (merge) převede víc draw callů na jeden;
  automatické LOD — [UE 4.27 Optimization and Development Best Practices for Mobile](https://docs.unrealengine.com/4.27/en-US/SharingAndReleasing/Mobile/Rendering/MobileOptimization/OptimizationandDevelopmentBestPracticesforMobile)
- PUBG Mobile běží na Unreal Engine 4 (bez veřejných rozpočtů) — [Wikipedia: PUBG Mobile](https://en.wikipedia.org/wiki/PUBG_Mobile)
- Neoficiální orientační cíl (průvodce 2026, nízká autorita): střední telefony 100–300k viditelných trojúhelníků, draw cally pod
  ~100–150 — [creatuneagency.com](https://www.creatuneagency.com/en/blog/low-poly-3d-models-for-mobile-games/)
- **Honor of Kings (Tencent, GDC 2023, Xiaoxin Guo):** cíl 1080p a 60 fps na široké škále od entry-level po nejnovější telefony,
  >100 mil. DAU; přednáška rozebírá shading pipeline a optimalizace (engine na stránce neuveden) — [GDC Vault 1028837](https://gdcvault.com/play/1028837/Practical-High-Performance-Rendering-On)
- **Genshin Impact (miHoYo, Unity):** Unity Dojo 2021 (Zhenzhong Yi) – mobil byl primární vývojová platforma; engine má dvě
  upravené renderovací cesty: PC/konzole a Android/iOS — [Unity Japan / docswell](https://docswell.com/s/UnityJapan/KWRPQ5-210617-unity-dojo20211mihoyozhenzhongyi)
- **Diablo Immortal (Blizzard + NetEase):** na Androidu Vulkan, hardwarový ray tracing pro odrazy mimo obrazovku, visibility
  buffer oddělující geometrii od shadingu (jen vlajkové GPU) — [Android Developers story](https://developer.android.com/stories/games/diablo-raytracing);
  120 fps na zařízeních s čipem Pixelworks IRX (tisková zpráva výrobce) — [Pixelworks](https://pixelworks.gcs-web.com/node/16716)
- **Infinity Nikki (Infold, UE5):** přechod na otevřený svět si vyžádal UE5 — [Unreal developer interview](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world);
  na iOS/Android dynamické odražené světlo v interiérech přes middleware Enlighten (Silicon Studio) — [tisková zpráva PDF](https://siliconstudio.co.jp/en/news/pressreleases/2025/250206InfinityNikki/pdf/NewsRelease_InfinityNikki_20250206_EN.pdf)
- **Sky: Children of the Light (thatgamecompany, vlastní engine):** GDC 2026 přednáška „Dynamic Environment Lighting in Sky“
  (bez čísel ve shrnutí) — [gamedev.net](https://gamedev.net/news/994-dynamic-environment-lighting-in-sky-children-of-the-light-gdcrewind-gdc2026/);
  na Switchi dva režimy: 30 fps HD, nebo 60 fps se sníženým rozlišením — [mynintendonews](https://mynintendonews.com/2021/06/30/sky-children-of-light-now-on-nintendo-switch-and-features-two-modes-performance-and-graphics/)
- **Delta Force mobile (GDC 2026, Qualcomm):** přednáška o škálování PC obsahu na mobil — [GDC schedule](https://schedule.gdconf.com/session/mobile-development-best-practices-delta-force-mobile-presented-by-qualcomm-technologies-inc/917699)
- **Call of Duty Mobile (Tencent TiMi J3, Unity):** cíl 60 fps; stínová vzdálenost škálovaná 80 → 50 (jednotky hry), foliage
  LOD 1,0 → 0,8 (viz bod 2) — [Samsung Developers](https://developer.samsung.com/galaxy-gamedev/gamedev-blog/cod.html)

### Inferences
- Pro Godot tablet je rozumné převzít strop Epicu jako horní hranici a jít pod ni: cílit na stovky draw callů (ne tisíce) a řádově
  stovky tisíc trojúhelníků na pohled; na 60 fps u střední třídy spíš polovinu. Svět 1,2 × 1,6 km je menší než mapy PUBG (8 × 8 km),
  takže celý terén může být v paměti a streamovat se mají hlavně detaily (budovy, vegetace, předměty).
- Všechny tituly mají pro mobil oddělenou/zjednodušenou cestu renderingu → v Godotu Mobile renderer, ne Forward+.
- Vzor „30 fps kvalita / 60 fps výkon se sníženým rozlišením“ (Sky Switch) je jednoduchý a srozumitelný preset pro hráče.

### Gaps
- Konkrétní rozpočty (draw cally, trojúhelníky, VRAM/RAM, poloměr streamování, hustota trávy) pro Genshin, PUBG Mobile, Arena
  Breakout, Tower of Fantasy, Honkai Star Rail, Infinity Nikki a Sky jsem v primárních zdrojích nenašel; Zhihu dotaz nevrátil nic
  relevantního. Další krok: GDC Vault plné záznamy (HoK 2023, Delta Force 2026), Unite Shanghai 2020 Genshin talk.
- Strategie HLOD a poloměry streamování konkrétních her nedoloženy.

## 2. Úrovně zařízení, presety kvality, dynamické rozlišení, teplotní škrcení

### Takeaway
Nejlépe doložený postup: CoD Mobile s Unity Adaptive Performance – při růstu teploty nejdřív snížit funkce (stínová vzdálenost,
foliage LOD, animation LOD), pak cílové fps (60 → 57), pak takty; výsledek o ~7 % vyšší průměrné fps a o ~2 °C nižší teplota.
Android Thermal API (ADPF) dává standardní signál `getThermalHeadroom`, volat max. jednou za 10 s.

### Cited Findings
- CoD Mobile: původně výchozí škrcení Androidu; Adaptive Performance udržel cíl 60 fps se stabilnějším fps. Škálovatelné položky:
  Shadow Distance 80 → 50 (CPU úspora 0–10 %), Foliage LOD 1,0 → 0,8 (GPU 0–5 %), Target Frame Rate 60 → 57 (CPU/GPU 0–5 %),
  Animation LOD 0 → 2 (CPU/GPU 0–5 %). Stupně: Normal (drží cíl, podle CPU/GPU-bound snižuje funkce), NearThrottling (snížit
  úrovně CPU/GPU), CloseThrottling (nejdřív změnit fps, pak úrovně). Výsledek: ve 3 zápasech BR fps výrazně stabilnější,
  průměr o ~7 % vyšší, teplota v průměru o ~2 °C nižší (max. 3 °C). Samsung GameSDK je od Androidu 16 zastaralý — [Samsung Developers](https://developer.samsung.com/galaxy-gamedev/gamedev-blog/cod.html)
- Android Thermal API: `PowerManager.getThermalHeadroom(forecastSeconds)` od API 30 (NDK od API 31); 0,0 = bez škrcení,
  1,0 = THERMAL_STATUS_SEVERE; **nevolat častěji než jednou za 10 s** (jinak NaN); NaN při prvním volání = nepodporováno.
  Doporučeno registrovat `addThermalStatusListener` a začít dotazovat headroom až od LIGHT. Heuristika: >0,85 ≈ LIGHT (sledovat),
  >0,95 ≈ MODERATE (snížit hned), >1,0 ≈ SEVERE. Akce: snížit fps, snížit kvalitu grafiky, práci na malá jádra; po vychladnutí
  vrátit, ale mířit na udržitelnou úroveň; zapisovat teplotní stav do telemetrie — [Android ADPF Thermal API](https://developer.android.com/games/optimize/adpf/thermal)
- ADPF obsahuje i Performance Hint API, Game Mode/Game State API a od Androidu 15 Power Efficiency Mode
  (`setPreferPowerEfficiency`) — [Android ADPF](https://developer.android.com/games/optimize/adpf)
- Unity: běžné je mít úrovně (Quality Levels) a vybrat je automaticky při startu podle zařízení — (shrnutí výsledků vyhledávání,
  viz [Unity discussions: Adaptive Performance](https://discussions.unity.com/t/adaptive-performance-package/737426))
- Arm příklad rozpočtu GPU: 850 MHz / 30 fps = 28 M cyklů na snímek — [Arm prezentace 2021 (slideshare)](https://www.slideshare.net/slideshow/unity-mobile-game-performance-profiling-using-arm-mobile-studio/249692787)
- Unreal Android: Mobile Content Scale Factor 1,0 = 1280×720, 2,0 = 2560×1440 (pevné škálování rozlišení) — [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/performance-guidelines-for-mobile-devices-in-unreal-engine)
- GDC 2026 (Arm): „Performance Tuning and Upscaling for Mobile Development in Unity“ — [GDC Vault 1035616](https://gdcvault.com/play/1035616/Performance-Tuning-and-Upscaling-for)

### Inferences
- Pro Godot: preset Nízký/Střední/Vysoký s položkami přesně podle CoD tabulky (vzdálenost stínu, násobič LOD/visibility range
  vegetace, animační LOD, cílové fps) + `Viewport.scaling_3d_scale` jako hlavní páka rozlišení. Teplotu číst přes JNI/Android
  plugin (`getThermalHeadroom` max. 1× za 10 s); Godot to sám nedělá (NEOVĚŘENO pro Godot 4.5+).
- Pořadí snižování: nejdřív to, co je málo vidět (stíny daleko, hustota trávy daleko, animace daleko), až pak rozlišení a fps.

### Gaps
- Reálné hodnoty dynamického rozlišení (rozsahy scale) u Genshinu/PUBG nenalezeny.
- Zda Godot 4 nabízí vestavěné ADPF/thermal – nebylo ověřeno v této rešerši.

## 3. Bez záseků: předkompilace shaderů / PSO cache, streamování, GC, asynchronní načítání

### Takeaway
Unreal na Androidu řeší záseky z kompilace shaderů „bundled PSO cache“ nasbíranou hraním na zařízení (-logPSO); cache odstraní
záseky při dalších bězích, ale ne při úplně prvním setkání se shaderem, pokud nebyl nasbírán. Pro velké světy se doporučuje
skládat svět z dlaždic načítaných podle potřeby.

### Cited Findings
- Epic: PSO caching předem vytvoří často používané pipeline state objekty, aby se omezily záseky; postup: zapnout Share Material
  Shader Code, spustit build s `-logPSO` na zařízení, nasbírané soubory vložit do buildu — [Epic: Bundled PSO caches for Android](https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-bundled-pso-caches-for-android-in-unreal-engine)
- Shadery se mezi buildy mění, proto stabilní klíče (`NeedsShaderStableKeys`) — [Epic: Manually creating bundled PSO caches](https://dev.epicgames.com/documentation/unreal-engine/manually-creating-bundled-pso-caches-in-unreal-engine)
- Zkušenost z fóra (GearVR): cache odstranila záseky při dalších spuštěních, ne při „prvním setkání“ se shaderem — [Unreal forum](https://forums.unrealengine.com/t/406915);
  Meta fórum: předkompilace při startu odstranila záseky, ale některé materiály se zpožďovaly — [Meta forum](https://communityforums.atmeta.com/discussions/dev-unreal/oculus-quest-4-25-enginge-pso-cache-causes-materials-not-to-load/836284)
- Godot docs: velké světy „může být potřeba stavět v dlaždicích načítaných na požádání, jak se pohybujete světem“ – omezí paměť
  a zpracování na okolí — [Godot: Optimizing 3D performance](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)

### Inferences
- Godot ekvivalent: po startu/na načítací obrazovce jednou vykreslit všechny materiály a varianty (stíny, mlha, instancing) mimo
  pohled kamery, aby se zkompilovaly pipeline; Godot 4.3+ má ubershadery/pipeline cache (NEOVĚŘENO v této rešerši – ověřit v
  dokumentaci Godotu). Dlaždice světa načítat `ResourceLoader.load_threaded_request` s předstihem.
- GC: u GDScriptu hlavně nevytvářet objekty každý snímek; konkrétní zdroj z mobilních her nenalezen.

### Gaps
- Jak to řeší Genshin/HSR (Unity) – shader variant collection/warmup – v primárních zdrojích nenalezeno.
- Fortnite mobile údajně PipelineFileCache už nepoužívá – jen jeden neoficiální příspěvek na fóru, neověřeno.

## 4. Animační LOD pro davy a zvířata

### Takeaway
Jediný doložený herní údaj: CoD Mobile má „Animation LOD“ 0 → 2 jako položku škálovanou při přehřívání (úspora CPU/GPU 0–5 %).
Primární mobilní zdroj s konkrétními frekvencemi aktualizace podle vzdálenosti nebo počtem kostí jsem nenašel.

### Cited Findings
- CoD Mobile: Animation LOD 0 → 2 jako škálovací položka — [Samsung Developers](https://developer.samsung.com/galaxy-gamedev/gamedev-blog/cod.html)
- Vertex animace v textuře (polypostors, I3D 2008): posuny vrcholů uložené kompaktně v jedné textuře, interpolace celá ve
  vertex shaderu – davy v reálném čase — [Kavan et al. 2008](https://dcgi.fel.cvut.cz/home/zara/papers/KavanEtAll-I3D08.pdf)
- LOD postav v davu volí počet vrcholů/trojúhelníků podle viditelnosti — [Chao et al. 2011](https://people.cs.vt.edu/~yongcao/publication/pdf/chao2011_MIG.pdf)
- Godot MultiMesh „kreslí mnoho tisíc objektů za velmi malou cenu“ – vhodné na hejna, trávu, částice — [Godot docs](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)

### Inferences
- Pro Godot: blízko AnimationTree + Skeleton3D; střední vzdálenost snížit frekvenci (AnimationMixer `callback_mode_process`
  = manual, volat `advance()` každý 2.–4. snímek); daleko zvířata/ptáci jako MultiMesh s vertex animací v textuře nebo jen
  statický mesh. Frekvence jsou návrh, nezměřené (NEOVĚŘENO).

### Gaps
- Konkrétní vzdálenostní pásma a frekvence animací v Genshinu/Sky/RDR-like mobilních hrách nenalezeny.

## 5. Mali vs. Adreno (dlaždicové GPU: overdraw, alpha test, šířka pásma, MSAA)

### Takeaway
Na obou rodinách je hlavní nepřítel overdraw a průhlednost/discard (vegetace). Adreno má LRZ (hrubý Z v binning průchodu),
který zahodí celé dlaždice – ale nefunguje, když shader potřebuje late-Z (discard, zápis hloubky) a s MSAA. Arm doporučuje
málo přepínání stavu, malé množství velkých draw callů a ≥10 fragmentů na trojúhelník (žádné mikro-trojúhelníky).

### Cited Findings
- Arm: kreslit co nejvíc primitiv v jednom draw callu, přepínání render state je drahé; draw cally drahé pro CPU — [Arm Mali best practices blog](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/arm-mali-best-practices)
- Arm fórum: držet počet fragmentů na trojúhelník „vyšší než 10“ (pravidlo palce); drobné trojúhelníky způsobují velké problémy
  s malým vizuálním přínosem — [Arm community forum](https://community.arm.com/support-forums/f/graphics-gaming-and-vr-forum/6301/mali-gpu-counter/23639)
- Arm Frame Advisor: ukazuje primitiva na draw call; Index rate ideálně blízko 1 (každý vrchol sdílen 3 trojúhelníky) — [Arm Frame Advisor](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/coming-soon-in-arm-frame-advisor)
- Arm: u dlaždicových GPU je nejdůležitější správný frame graph (render passy a tok dat mezi nimi) — [Arm best practice principles](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/p2-best-practices-mobile-game-development)
- Qualcomm Adreno: v binning průchodu se staví low-resolution Z buffer, který může zahodit příspěvky celých LRZ dlaždic (od A5x) — [Qualcomm Adreno GPU overview](https://developer.qualcomm.com/sites/default/files/docs/adreno-gpu/snapdragon-game-toolkit/gdg/gpu/overview.html), [FAQ](https://developer.qualcomm.com/sites/default/files/docs/adreno-gpu/snapdragon-game-toolkit/gdg/gpu/faq.html)
- LRZ je předčasný test hloubky, nelze ho použít, když je potřeba late-Z — [Mesa freedreno LRZ](https://docs.mesa3d.org/drivers/freedreno/hw/lrz.html)
- Qualcomm (citace FAQ ve fóru): alpha test a alpha blend mají stejnou propustnost; při 1 vzorku obojí konzervativně odmítnuto,
  ale **se zapnutým MSAA se kvůli šířce pásma neodmítají a jdou jen na late Z**; alpha test HW běží až po pixel shaderu — [Qualcomm forum](https://developer.qualcomm.com/forum/qdn-forums/software/adreno-gpu-sdk/68788)
- Epic: masked/translucent se stínují pro každou vrstvu, overdraw může zdvojnásobit čas GPU; Alpha to Coverage vyžaduje MSAA — [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/performance-guidelines-for-mobile-devices-in-unreal-engine)
- Godot: depth prepass je výchozí ve Forward+ a Compatibility (o Mobile stránka mlčí); automatický instancing je jen ve Forward+,
  ne v Mobile a Compatibility; MultiMesh je doporučená cesta i pro alpha-blended materiály; billboardy/impostory přes visibility
  ranges; v otevřeném prostředí occlusion culling pomáhá méně, místo toho mesh LOD nebo ruční HLOD s visibility ranges;
  baked světlo doporučeno pro mobil — [Godot: Optimizing 3D performance](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html), [Godot 4.0 sets sail](https://godotengine.org/article/godot-4-0-sets-sail/)

### Inferences
- Pro Godot Mobile renderer na tabletu: (a) bez MSAA (souhlasí s pravidlem projektu) – s MSAA se na Adrenu ztrácí časné
  odmítání alpha-test vegetace; (b) tráva a listí: co nejmenší plocha průhledných pixelů (karty oříznuté těsně k tvaru, víc
  vrcholů místo prázdné alfy), daleko přejít na neprůhledné impostory/mesh bez discardu; (c) protože automatický instancing
  v Mobile renderer chybí, opakované objekty (stromy, keře, kameny, plot) dávat do MultiMeshInstance3D; (d) vyhnout se
  mikro-trojúhelníkům – LOD agresivně podle velikosti na obrazovce (≥10 px na trojúhelník); (e) žádné čtení screen textury
  (rozbije dlaždicový průchod).
- Rozdíl Mali (HSR „Forward Pixel Kill“) vs Adreno (LRZ) nebyl v nalezených zdrojích doložen čísly; oba trpí stejně na discard.

### Gaps
- Úplný text Arm Mali Best Practices Guide (101897) a Arm geometrie (102695) se nepodařilo stáhnout (přesměrování na
  support.arm.com bez obsahu); konkrétní doporučení k ASTC, mipmapám, stínovým mapám a load/store z nich tedy necituji.
- Zda Godot Mobile renderer dělá depth prepass – oficiální stránka to neuvádí (třetí strana tvrdí, že ne; neověřeno).
