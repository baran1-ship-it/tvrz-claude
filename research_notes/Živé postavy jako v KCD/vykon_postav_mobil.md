# Výkon 30–40 skinovaných postav na Android tabletu (Godot 4.4, Compatibility / GLES3)

Rešerše 11. 11. 2026. Zdroje: dokumentace Godotu, issue tracker, fórum, **přímo zdrojový kód Godot 4.4-stable**
(`drivers/gles3/storage/mesh_storage.cpp`, `drivers/gles3/shaders/skeleton.glsl`, `scene/3d/skeleton_3d.cpp`,
`servers/rendering/renderer_scene_cull.cpp`, staženo z `raw.githubusercontent.com/godotengine/godot/4.4-stable/...`).
Žádné číslo níže není naměřené na našem tabletu – vše, co je pro náš tablet, je **NEOVĚŘENO** do změření Měřicí trasou.

## 1. Skinning v Compatibility rendereru: CPU, nebo GPU? Kolik stojí?

### Takeaway
Skinning v Godot 4.4 Compatibility běží **na GPU přes transform feedback** (vertex shader zapisuje skinované vrcholy do
bufferu, `GL_RASTERIZER_DISCARD`), a to jen pro instance, které prošly ořezem kamery. Drahé je ale všechno kolem:
CPU míchání animací, výpočet póz kostí, volání RenderingServeru po kostech, nahrání textury kostí a OpenGL volání na
hlavním vlákně. Známé issue #88954 ukazuje, že ~100 animovaných skeletů je v OpenGL řádově pomalejší než ve Vulkanu
(i na Androidu ~28 FPS), příčina zatím neopravená.

### Cited Findings
- `MeshStorage::_compute_skeleton()` v GLES3 dělá skinning takto: naváže skin buffer (kosti+váhy jako `GL_UNSIGNED_SHORT`,
  4 nebo 8 vah), texturu kostí, `glBeginTransformFeedback(GL_POINTS); glDrawArrays(GL_POINTS, 0, vertex_count); glEndTransformFeedback();`
  – tj. **jeden průchod GPU na každý povrch (surface) každé skinované instance**, výsledek jde do `vertex_buffer` instance,
  ze kterého se pak kreslí (i do stínů) — [mesh_storage.cpp 4.4-stable](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/drivers/gles3/storage/mesh_storage.cpp)
- `update_mesh_instances()` zapne `GL_RASTERIZER_DISCARD` a komentář říká „Process skeletons and blend shapes using transform
  feedback" — [mesh_storage.cpp](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/drivers/gles3/storage/mesh_storage.cpp)
- Shader `skeleton.glsl` má specializace `USE_SKELETON`, `USE_EIGHT_WEIGHTS`, `USE_BLEND_SHAPES`; kosti čte ze
  `sampler2D skeleton_texture` — [skeleton.glsl](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/drivers/gles3/shaders/skeleton.glsl)
- Skinning se spouští jen pro instance v `scene_cull_result.mesh_instances` (po ořezu) a jen když se změnila verze
  skeletu (`sk->version != mi->skeleton_version`) — [renderer_scene_cull.cpp](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/servers/rendering/renderer_scene_cull.cpp),
  [mesh_storage.cpp `mesh_instance_check_for_update`](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/drivers/gles3/storage/mesh_storage.cpp)
- Textura kostí: šířka 256 texelů RGBA32F, 3 texely na kost (3D), výška = ceil(kosti×3/256). Každý změněný skelet se nahrává
  celý přes `glTexImage2D` (realokace, ne `glTexSubImage2D`) a zvýší se `version` — [mesh_storage.cpp `skeleton_allocate_data`, `_update_dirty_skeletons`](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/drivers/gles3/storage/mesh_storage.cpp)
- Na straně scény `Skeleton3D` při `NOTIFICATION_UPDATE_SKELETON` pro každou kost skinu volá
  `rs->skeleton_bone_set_transform(skeleton, i, global_pose * bind_pose)` — tj. **N volání RenderingServeru na skelet a snímek** —
  [skeleton_3d.cpp 4.4-stable](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/scene/3d/skeleton_3d.cpp)
- Issue #88954 „Skeleton3D Animation performance is terrible on OpenGL" (otevřené, potvrzené): 4.2.1, i9-14900K + RTX 4090,
  ~100 skeletů ≈ 20 FPS v OpenGL vs >100 FPS ve Vulkanu; bez animací ~120 FPS; ~50 % času v jedné OpenGL funkci. Calinou (4.4.1,
  M4 Max): 5 FPS s animacemi vs 300 FPS pozastaveno. TinyMatt (4.5 beta): Android Xiaomi Mi 10T Pro ~28 FPS. TokageItLab: úzké
  hrdlo spíš deformace skinu přes RenderingServer než přehrávání animací; navrhl deformovat všechny skelety najednou jednou za
  snímek. Calinou (7/2025): oprava „nontrivial", OpenGL volání běží na hlavním vlákně; doporučuje rozložit update animací do
  více snímků, pozastavit vzdálené postavy, impostory pro davy. Bez PR, bez milníku — [github.com/godotengine/godot/issues/88954](https://github.com/godotengine/godot/issues/88954)
- Commit, který přidal skelety do OpenGL rendereru (2022-11-29), popisuje „multipass approach similar to blend shapes";
  PR #95452 (8/2024, clayjohn) zvýšil přesnost transformací kostí ve skeleton shaderu Compatibility — [zrcadlo historie skeleton.glsl](https://remotebranch.eu/Stowage/godot/commits/commit/fe84b84b51df1ff6db658f521d1040aa563cedd0/drivers/gles3/shaders/skeleton.glsl)
- Oficiální dokumentace: „Animation and vertex animation such as skinning and morphing can be very expensive on some
  platforms" – snižovat polycount animovaných modelů, omezit jejich počet na obrazovce, snížit rychlost animace u vzdálených —
  [Optimizing 3D performance (4.4)](https://docs.godotengine.org/en/4.4/tutorials/performance/optimizing_3d_performance.html)
- Docs: OpenGL/GLES/WebGL mají vysokou režii ovladače na komunikaci CPU–GPU — [GPU optimization](https://docs.godotengine.org/ru/4.4/tutorials/performance/gpu_optimization.html)

### Inferences
- Cena na postavu a snímek v Compatibility ≈ (a) CPU: AnimationMixer + výpočet globálních póz kostí + 65× `skeleton_bone_set_transform`;
  (b) 1× upload textury kostí: 65 kostí = 195 texelů → 1 řádek 256×RGBA32F = **4 KiB** (výpočet ze zdroje); (c) 1 transform-feedback
  draw **na každý povrch** (na každý materiál!) – GPU práce úměrná počtu vrcholů × vah (4 vs 8); (d) normální draw cally pro kreslení a stíny.
  Pro 40 postav × 3 materiály = 120 TF průchodů + 40 uploadů za snímek jen na skinning – proto **1 materiál na postavu** a **4 váhy**
  (ne 8) jsou nejlevnější opatření.
- Počet kostí (65) ovlivňuje hlavně CPU (globální pózy, počet RS volání, velikost uploadu); GPU skinning na vrchol závisí na
  počtu vah (4/8), ne na počtu kostí. Pevný limit kostí v GLES3 není (textura roste po 85 kostech na řádek).
- Off-screen postava neplatí GPU skinning (je mimo cull result), ale **dál platí CPU animaci, póz kostí a upload textury**,
  pokud ji ručně nezastavíme (z kódu: skelet se označí dirty při změně pózy bez ohledu na viditelnost).
- Postava, jejíž animace se v daném snímku neposunula, nezvýší `version` → žádný TF průchod ani upload. Tj. **přeskakování
  snímků animace ušetří CPU i GPU skinning**, ne jen CPU.

### Gaps
- Přesné µs na vrchol/kost na Adreno/Mali jsem nenašel; nutno změřit (Godot profiler + `RenderingServer.get_rendering_info`).
- Transform feedback na některých Mali ovladačích může být pomalý – nenašel jsem spolehlivý zdroj.

## 2. AnimationTree vs AnimationPlayer, a jak škrtit update animací

### Takeaway
Publikovaný mikrobenchmark per instance neexistuje; komunita opakovaně hlásí, že AnimationTree je výrazně dražší než
samotný AnimationPlayer a že odebrání AnimationTree řeší propady. Doporučený vzor: `callback_mode_process = MANUAL`
a ručně `advance(delta * k)` jednou za k snímků podle vzdálenosti, mimo obrazovku vůbec.

### Cited Findings
- AnimationMixer: `ANIMATION_CALLBACK_MODE_PROCESS_MANUAL` – „Do not process animation. Use advance to process the animation
  manually"; `advance(delta)` posune animace o čas v sekundách; režim PHYSICS je pro animaci fyzikálních těles —
  [AnimationMixer docs](https://docs.godotengine.org/en/4.3/classes/class_animationmixer.html)
- Vzor animačního LOD (Godot 4.3+): `anim_tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL`;
  >50 m neposouvat; 20–50 m `if Engine.get_process_frames() % 2 == 0: anim_tree.advance(delta * 2.0)`; blízko `advance(delta)`.
  Upozornění: „AnimationTree updates itself every frame, so returning early from `_process()` doesn't reduce its animation work";
  `active = false` strom úplně zastaví a `advance()` pak nefunguje; NPC vypnout foot IK, zapnout kompresi animací v importu;
  „IK is the expensive part: IK recalculates every frame" — [uhiyama-lab: 3D Skeletal Animation in Godot](https://uhiyama-lab.com/en/notes/godot/3d-skeletal-animation/)
- Fórum (4.3): ~10 nepřátel s fyzikálními skelety při 60 FPS; testy bez modelů beze změny; příčina „animationtrees being super
  expensive", smazání AnimationTree pomohlo — [forum: Skeletons lagging game](https://forum.godotengine.org/t/skeletons-lagging-game-even-not-actively-simulated/103690)
- Fórum (testy 4.2, Ryzen 5 2400G iGPU): >50 animovaných postav na obrazovce; s vypínáním AnimationPlayeru mimo obraz/v dálce
  >200 jednotek; ~36 FPS při ~300 jednotkách; AnimationTree vynechán („uses a lot of resources"), animace nastavovány ručně na
  AnimationPlayeru; „Godot doesn't do skeleton 3D culling"; root motion nejde s vypnutým playerem; pohyb přes raycast serveru bez
  fyziky — [forum: Performance of crowds of animated rigged characters](https://forum.godotengine.org/t/performance-of-crowds-of-animated-rigged-characters-in-3d/130409)
- Od 4.3 sjednocení AnimationPlayer a AnimationTree pod AnimationMixer — [Migrating animations from Godot 4.0 to 4.3](https://godotengine.org/article/migrating-animations-from-godot-4-0-to-4-3/)
- SkeletonModifier3D (4.3) běží po AnimationMixeru; modifikátory (IK, LookAt) se při každém updatu skeletu přepočítávají a
  `Skeleton3D` u nich zálohuje/obnovuje pózy všech kostí — [Design of the Skeleton Modifier 3D](https://godotengine.org/article/design-of-the-skeleton-modifier-3d/),
  [skeleton_3d.cpp](https://raw.githubusercontent.com/godotengine/godot/4.4-stable/scene/3d/skeleton_3d.cpp)
- Otevřený PR #113441 „Optimize Skeleton3D" (TokageItLab, master, 12/2025) – stav a čísla neověřena — [PR #113441](https://github.com/godotengine/godot/pull/113441)
- Docs: pauzovat animace, kde si toho hráč nevšimne; k tomu `VisibleOnScreenEnabler3D` / `VisibleOnScreenNotifier3D` —
  [Optimizing 3D performance](https://docs.godotengine.org/en/4.4/tutorials/performance/optimizing_3d_performance.html)

### Vzor kódu (navrženo z citovaných zdrojů, neměřeno)
```gdscript
# Jeden správce pro všechny NPC (ne _process v každém NPC) – časové krájení.
extends Node
var npcs: Array = []          # {mixer: AnimationMixer, node: Node3D, acc: float, on_screen: bool}
var _i := 0
func _ready():
    for n in npcs:
        n.mixer.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
func _process(delta):
    var cam := get_viewport().get_camera_3d().global_position
    for n in npcs:
        n.acc += delta
        if not n.on_screen: continue                 # z VisibleOnScreenNotifier3D.screen_entered/exited
        var d := cam.distance_to(n.node.global_position)
        var krok := 1 if d < 15.0 else (3 if d < 40.0 else 0)   # pásma patří do pravidla/…json, ne do kódu
        if krok == 0: continue                       # zmražená póza / impostor
        if (Engine.get_process_frames() + n.hash_offset) % krok == 0:   # rozprostřít NPC přes snímky
            n.mixer.advance(n.acc); n.acc = 0.0
```
- `acc` posouvá o skutečný uplynulý čas → animace neutíká; `hash_offset` rozloží NPC, aby se nepočítaly všechny ve stejném snímku.
- U AnimationTree nezapínat/vypínat `active` za běhu (pak nefunguje `advance`), raději neposouvat.

### Inferences
- Pro 30–40 NPC: AnimationPlayer (bez AnimationTree) u běžných NPC; AnimationTree jen u hráče/koně/blízkých bojovníků.
- Animace s 1/3 snímků v pásmu 15–40 m snižuje CPU i GPU skinning cca na třetinu pro ty postavy (viz §1, verze skeletu se nemění).

### Gaps
- Číselné µs/instanci pro AnimationPlayer vs AnimationTree na mobilu nikde publikované – nutné vlastní měření (scéna 40 NPC na trase).

## 3. LOD strategie (plná animace < 15 m, nižší fps 15–40 m, zmražené/impostor dál) a rozpočty

### Takeaway
Pásma podle vzdálenosti jsou standard; Godot je nedělá automaticky pro animace – nutný vlastní správce. Mesh LOD
a visibility ranges (HLOD) Godot nabízí; impostory doporučuje i Calinou pro davy. Pro mobil se uvádí přechod na impostor
kolem 40–60 m (neověřený blogový zdroj).

### Cited Findings
- Godot 4 LOD: automatický mesh LOD při importu + ruční visibility ranges (HLOD) + distance fade; „most effective when used
  together"; visibility ranges vhodné pro impostory vzdálené geometrie; impostor = předrenderované pohledy z více úhlů —
  [Optimizing 3D performance](https://docs.godotengine.org/en/4.4/tutorials/performance/optimizing_3d_performance.html),
  [Visibility ranges (HLOD)](https://docs.godotengine.org/en/4.4/tutorials/3d/visibility_ranges.html)
- Automatický instancing (slučování draw callů) je **jen ve Forward+, ne v Mobile/Compatibility** → každá postava a každý
  materiál = vlastní draw call — [Optimizing 3D performance](https://docs.godotengine.org/en/4.4/tutorials/performance/optimizing_3d_performance.html)
- MultiMesh: „many thousands of objects at very little performance cost" pro identické objekty — tamtéž
- VAT v Godotu 4: antzGames „Godot Vertex Animation Textures Plugin" (rozšiřuje MultiMeshInstance3D o instancované vertex
  animace, MIT, + Blender exporter) a „Godot 4.3 Vertex Animation Instancing Demo"; OpenVAT z Blenderu má shader pro Godot —
  [přehled pluginu](https://awesome.ecosyste.ms/projects/github.com%2Fantzgames%2Fgodot_vertex_animation_textures_plugin),
  [demo 4.3](https://relatedrepos.com/gh/antzGames/Godot-4.3-Vertex-Animation-Instancing-Demo),
  [godotshaders VAT s instancováním](https://godotshaders.com/shader/vertex-animation-with-instancing/),
  [OpenVAT shader](https://godotshaders.com/shader/vertex-animation-texture-uses-openvat-output/)
- Obecné (blog, neověřené): pozadí NPC na mobilu 500–2000 polygonů, za 40–60 m přechod na impostor sprite; méně kostí v dálce;
  stupňované update rate s držením poslední pózy, tvrzená úspora animačního CPU 50–70 % —
  [mocaponline: Mobile game animation](https://mocaponline.com/blogs/mocap-news/mobile-game-animation-guide),
  [mocaponline: Animation LOD](https://mocaponline.com/blogs/mocap-news/animation-lod-performance-guide)
- Reddit/fórum: LOD skeletu s méně kostmi v dálce, počet kostí obvykle hlavní faktor; alternativně řešit animace v compute
  shaderu (složité) — souhrn ve vyhledávání k [forum: crowds](https://forum.godotengine.org/t/performance-of-crowds-of-animated-rigged-characters-in-3d/130409) (originál Reddit neověřen)
- AC Unity: pooling low-res ↔ high-res NPC bez povšimnutí hráče, jednoduchý „mozek" pro tisíce NPC —
  [GDC: Massive Crowd on Assassin's Creed Unity](https://www.gdcvault.com/play/1022141/contactUs)
- GDC 2025/26 session „Supporting Thousands of NPCs in Kingdom Come: Deliverance / KCD II" (vývoj AI LOD) – obsah nedostupný (403) —
  [GDC schedule](https://schedule.gdconf.com/session/supporting-thousands-of-npcs-in-kingdom-come-deliverance-kingdom-come-deliverance-ii/915120)
- Unreal Significance Manager přiděluje každému aktéru „significance", podle níž se řídí animační LOD — [mocaponline: Animation LOD](https://mocaponline.com/blogs/mocap-news/animation-lod-performance-guide)

### Doporučené nastavení (inference, NEOVĚŘENO na tabletu)
| Pásmo | Animace | Mesh | Stín | Logika |
|---|---|---|---|---|
| 0–15 m | každý snímek, AnimationPlayer (AnimationTree jen hráč/kůň), foot IK jen do ~8 m | LOD0, 1 materiál, 4 váhy | ano | každý snímek / 2. |
| 15–40 m | `advance` každý 2.–4. snímek, bez IK | LOD1 (mesh LOD importu) | ne (`cast_shadow = OFF`) | 2–4× za s |
| 40–80 m | zmražená póza nebo VAT/MultiMesh (chůze) | LOD2 / VAT | ne | 1× za s |
| > 80 m | skrýt (visibility_range_end) nebo impostor | – | ne | jen plán |
| mimo obraz | neposouvat (VisibleOnScreenNotifier3D) | – | – | časově krájená |
- Hranice pásem patří do `pravidla/…json` (pravidlo projektu: v kódu žádná vlastní čísla).
- Stíny: GLES3 skinuje do bufferu jednou a stínový průchod jen kreslí znovu (z kódu) → stín stojí další draw call(y)
  a vrcholy, ne další skinning; vypnout od ~15–20 m přes `cast_shadow` měněné správcem LOD.
- Pozor: `visibility_range` na skinované MeshInstance3D skryje kreslení, ale **nezastaví AnimationPlayer ani Skeleton3D** –
  animaci je nutné zastavit ručně (inference z kódu §1 a z fóra „Godot doesn't do skeleton 3D culling").

### Gaps
- Rozpočty Genshin Impact / Albion Online na NPC jsem nenašel ve spolehlivém zdroji (žádný postmortem s čísly).
- Číselné rozpočty z GDC pro mobilní davy nenalezeny; KCD2 GDC přednáška nepřístupná.

## 4. Známé issues/PR k výkonu mnoha skeletů; logika NPC, raycasty, IK

### Takeaway
Hlavní známý problém: #88954 (OpenGL, otevřený, bez opravy). Engine nemá ořez animací ani skeletů – vše řeší vlastní správce.
Logiku NPC časově krájet, raycasty dělat přes `PhysicsDirectSpaceState3D` jen pro blízké a jen občas, IK jen pro nejbližší.

### Cited Findings
- #88954 – viz §1 (Compatibility/OpenGL ~5× pomalejší než Vulkan při ~100 skeletech; Android Mi 10T Pro ~28 FPS) — [issue #88954](https://github.com/godotengine/godot/issues/88954)
- Calinou v #88954: OpenGL volání jsou na hlavním vlákně, vícevláknové zpracování animací (godot-proposals#12759) by OpenGL část
  neřešilo — [issue #88954](https://github.com/godotengine/godot/issues/88954)
- PR #113441 „Optimize Skeleton3D" (otevřený, master) — [PR](https://github.com/godotengine/godot/pull/113441)
- Fórum: davová hra pohybovala jednotky raycastem serveru po terénu bez fyziky a kolizí, Area3D jen pro výběr —
  [forum: crowds](https://forum.godotengine.org/t/performance-of-crowds-of-animated-rigged-characters-in-3d/130409)
- Docs CPU optimalizace: každý uzel se zpracovává zvlášť, méně uzlů s více prací bývá rychlejší (→ jeden správce místo 40× `_process`) —
  [CPU optimization](https://docs.godotengine.org/en/4.3/tutorials/performance/cpu_optimization.html)
- IK přepočítává každý snímek a je drahé; NPC vypnout — [uhiyama-lab](https://uhiyama-lab.com/en/notes/godot/3d-skeletal-animation/)

### Inferences
- Pro náš projekt (Compatibility, tablet): 30–40 NPC je na hraně toho, co #88954 ukazuje (100 skeletů = 28 FPS na Mi 10T Pro);
  realistický cíl je **≤ 8–12 plně animovaných postav v záběru**, zbytek škrtaný/zmražený/VAT. NEOVĚŘENO – změřit variantou
  Měřicí trasy s 40 NPC a se skupinou NPC vypnutou (izolovaný test dle pravidel projektu).
- Jeden `_process` správce NPC: AI rozhodování round-robin (např. 5 NPC za snímek), raycast na zem jen při pohybu a v blízkém pásmu,
  vzdálení NPC drží výšku z heightmapy/navmesh bez raycastu.
- Postavy připravit: sloučit materiály do 1 (atlas), 4 váhy na vrchol (import „8 bone weights" vypnout), mesh LOD v importu,
  kompresi animací v importu, odstranit nepoužité kosti (prsty, obličej) pro NPC varianty.

### Gaps
- Cena raycastu na Androidu (Godot Physics vs Jolt) per volání nezměřena v nalezených zdrojích.
- Neověřeno, zda `_update_dirty_skeletons` běží pro všechny dirty skelety i mimo obraz (silně pravděpodobné ze struktury kódu,
  volající místo jsem nedohledal).
