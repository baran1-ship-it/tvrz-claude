# Tráva: hotová řešení pro Godot 4 a prototyp pro Havrana (4. 11.)

Rešerše skutečného kódu (staženo 4. 11. do scratchpadu `…/scratchpad/grass_src/`, nic z toho se nespouštělo).
Doplňuje `docs/rozpracovane/trava_gpu.md` (návrh). V projektu se zatím nic neměnilo. Všechna čísla výkonu u
prototypu níže jsou **NEOVĚŘENO** (rozpočet, ne měření), dokud je neprojede měřicí trasa na tabletu.

Stažené verze:
- franos-cm/grass-demo @ `e518b4a` (1. 7. 2025)
- Zylann/godot_heightmap_plugin @ `7f574eb` (30. 7. 2026)
- dip000/godot-landscaper @ `9127246` (11. 8. 2025)
- mohsenph69/Godot-MTerrain-plugin (jen `gdextension/src/grass`, HEAD 4. 11. 2026)
- Godot `4.4.1-stable`: `drivers/gles3/shaders/scene.glsl` a `drivers/gles3/storage/material_storage.cpp`, abych ověřil,
  jak se v GL Compatibility chovají `MODEL_MATRIX`, `INSTANCE_ID` a `NODE_POSITION_WORLD`.

---

## 0. Co rozhoduje u nás (shrnutí na začátek)

| Zdroj | Poloha instancí | Kde tráva je | Výška | Při pohybu kamery | Licence |
|---|---|---|---|---|---|
| grass-demo | CPU jednou při startu, náhodně v pevných blocích 40 m | nikde (všude) | CPU `Image.get_pixel` při plnění | nic (pole je statické) | **žádná** → kód nepřebírat |
| normalized (fórum) | jedna pevná mřížka N×N, uzel jede s hráčem, **shader přichytí na světovou mřížku** | textura pokrytí → nulové měřítko | heightmapa ve vertex shaderu | jen posun uzlu | neuvedena (podmínky fóra) → jen princip |
| Zylann hterrain | **jeden sdílený MultiMesh** 32×32 m pro všechny bloky, bloky jen přesouvá | detail mapa R8, `density > hash` | heightmapa ve vertex shaderu | při přechodu do jiného bloku přidá nebo odebere bloky (jen transformace a AABB) | **MIT** → smíme převzít s copyrightem |
| Landscaper | CPU jednou v editoru (raycast) | maska `Image` | raycast | nic | MIT |
| MTerrain | C++ na CPU, po blocích terénu | bitová mapa | `grid->get_height` na CPU | přestavba bloků | MIT |

Pro oba naše problémy jsou podstatné dvě věci:
1. **Nic se nepřepočítává na CPU**: normalized (mřížka přichycená v shaderu) a Zylann (jeden MultiMesh, bloky se jen
   přesouvají). To přímo odstraní „tráva naroste pozdě“: dnešních 0,4–1,7 s rozsevu buňky v GDScriptu zmizí.
2. **Počet instancí v záběru** sníží jen hustota, která ubývá se vzdáleností (prstence s větším krokem). Samotné
   přesunutí výpočtu na GPU ho nesníží. Stejný vzhled jako dnes (do 20 m plná hustota, k 80 m plynule méně) znamená
   zhruba stejný počet trsů a nejspíš i podobnou cenu na GPU. Viz §6: naše měření zatím **neříká**, jestli tablet brzdí
   vrcholy, nebo pixely.

---

## 1. franos-cm/grass-demo (https://github.com/franos-cm/grass-demo)

Školní projekt (README: „PCS3539 … 2025.1“), Godot 4.4.1, **Forward Plus** (`project.godot`:
`config/features=PackedStringArray("4.4", "Forward Plus")`). Hra pro PC s klávesnicí.

**Generování pozic: na CPU jednou při startu, náhodně.**
- `assets/scripts/multi_mesh_grass.gd:5-8`: `high_density = 0.2`, `high_quality = 4`, `chunks_number = 6`, `chunk_size = 40`.
- `:33-37`: `for i in range(-chunks_number, chunks_number): for j in …: instance_chunk(…); maybe_fill_chunk(…)`
  vytvoří 12 × 12 = 144 bloků po 40 m, tedy pole 480 × 480 m kolem počátku (ne kolem hráče).
- `:78-90`: `count_side = ceil(chunk_size/density)` = 200, tj. **40 000 instancí na blok, celkem 5,76 milionu**. Každá
  má `randf_range` posun, `Heightmap.get_height(x, z)` (CPU, `assets/scripts/Heightmap.gd:7-27`: bilineárně ze 4 ×
  `image.get_pixel`) a náhodné otočení, zapsané přes `set_instance_transform`.
- `:40-54`: každý blok má vlastní `MultiMeshInstance3D` (`top_level = true`) a vlastní `PlaneMesh` s
  `subdivide_width = quality` (`:80`).

**LOD a mizení:** v kódu je **vypnuté**. `:62-70` mají LOD zakomentovaný a `:72-74` se při stejné kvalitě hned vrátí.
README („LoD“) slibuje řidší trávu 2 bloky od hráče, kód to nedělá. Výpočet vzdálenosti `:57-58` má navíc chybu:
`Vector2(chunk.index) + chunk_size/2` nenásobí index velikostí a bere dvakrát `.x`. Fade podle vzdálenosti v shaderu není.
**Pohyb kamery:** `_process` (`:96-98`) jen volá `maybe_fill_chunk`, které nic nedělá. Bloky se nehýbou, pole je konečné.
Kolem hráče jezdí jen terén (`assets/scripts/terrain_mesh.gd:6`: `global_position = player.global_position.round() * Vector3(1, 0, 1)`)
a kolizní plocha 8×8.

**Výška terénu:** pro trávu se počítá na CPU (viz výše). Terén ji bere ve vertex shaderu z globální heightmapy
(`assets/shaders/terrain.gdshader:9-13`: `VERTEX.y = texture(heightmap, texture_position).r * amplitude;`).

**Stéblo (shader):** `assets/shaders/grass_blade.gdshader`, `render_mode cull_disabled` (`:2`). Bézierova křivka,
„tloušťka podle pohledu“, vítr z šumové textury. Náhodnost se bere z polohy instance:
`:186 world_position = MODEL_MATRIX[3].xyz;` a `:190 instance_rand_num_1 = hash13(world_position.xyz);`.
Sešlapání: `SubViewport` kreslí stopy hráče do textury, kterou shader čte (`:61-63` globální uniformy, `:175`).
To je zajímavé pro koně, ale ne pro náš výkon.

**Výkon:** README §3 neuvádí žádné číslo ani zařízení. O velikosti bloku jen říká „defined testing the performance
against different configurations“. Na mobilu ani v Compatibility se nezkoušelo.

**Licence:** v repozitáři **chybí soubor LICENSE** a README licenci neuvádí. Výchozí stav je „všechna práva
vyhrazena“, kód tedy **nekopírovat**, brát jen inspiraci. (Přibalený `addons/sky_3d` má vlastní licenci, pro nás nepodstatné.)

**Pro Havrana:** neřeší ani jeden z našich problémů. Je to statické pole bez LOD a 5,76 M instancí by tablet nedal.
Použitelný je jen nápad se stopou hráče v textuře (sešlapání koněm), na později.

---

## 2. Fórum: „Transmit grass across individual unique planes/meshes“ (uživatel normalized)

https://forum.godotengine.org/t/transmit-grass-across-individual-unique-planes-meshes/141821. Staženo přes JSON
(`/t/141821/N.json`), 126 příspěvků. Tazatel používá Godot 4.7.1 a Terrain3D. Příspěvky normalized: #6, #21, #29,
#41, #50, #53, #66, #71, #75, #81, #83, #84, #86, #88, #90, #92, #111, #114, #116.

**Princip (#66, #71, #75):**
> #71: „At startup you just instantiate a rectangular grid of NxN blades into a single multimesh instance. … Parent this
> multimesh centered to the player and that's it. Everything else is done by the shader. This can be upgraded into some
> clipmap-like thing by creating two or three multimesh instances that use progressively simpler meshes and cover wider
> rings. … the shader needs to keep an illusion that they are rooted at fixed points on the terrain. This is done by
> snapping instance's xz to the nearest fixed grid position. This fixed position is then used as a seed … A coverage
> texture can be used to zero-out any instances that are outside of covered areas.“

> #71 (video): „It's a single pre-generated mmi. … Nothing changes in the mmi except its position. All the work is done
> by the vertex shader.“

**Pozice:** CPU jednou rozmístí instance do **dokonalé mřížky bez otočení a měřítka**:
- #88: „The blades need to be distributed in a perfect grid in order for snapping to work properly. Also the actual grid
  step and the grid_step uniform in the shader must match. … You also don't want to rotate the instances.“
- #90: „don't use "populate". The size of the patch as well as grid step need to be sent to the shader.“

Ve vertex shaderu (#75, totéž rozšířené v #111) se pak instance přichytí na světovou mřížku:
```glsl
// #75, řádky 34-35 a 47-51 kódu v příspěvku
vec2 snapped_position = floor(MODEL_MATRIX[3].xz / grid_step) * grid_step;
float position_id = rand(snapped_position);
...
VERTEX.xz += snapped_position - MODEL_MATRIX[3].xz;                 // snap xz position to implicit grid
vec3 vertex_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
VERTEX.y += texture(heightmap, 0.5 + vertex_world.xz / terrain_size).r * elevation_scale - NODE_POSITION_WORLD.y;
VERTEX = mix(vec3(0.0), VERTEX, step(0.001, texture(grass_coverage, 0.5 + snapped_position / terrain_size).r));
```
`rand` je `fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453)`. Pořadí podle #109: deformace (vítr, ohnutí,
měřítko) **před** přichycením, pak výška a otočení. V #111 je oprava chvění: „The jitter was caused by how the patch
texture was sampled. The snapped position should have been used as the uv coordinate instead of NODE_POSITION_WORLD.“

**Kde tráva je:** textura pokrytí přes celý terén v UV 0–1 (#66, #75: „It doesn't need to match any resolution, its UV
space implicitly covers the whole terrain“). Mimo pokrytí se trs smrskne na nulu (degenerované trojúhelníky, žádné fragmenty).

**Výška:** heightmapa ve vertex shaderu (#6, #21, #41 `remap` na min–max výšku). #39 varuje: 16bitové PNG Godot při
importu převede na 8 bitů a vznikají schody, proto EXR. #50: tráva mimo kameru mizí kvůli **AABB**. Řešením je
`custom_aabb`, nebo posunout uzel na výšku terénu a v shaderu odečíst `NODE_POSITION_WORLD.y`.

**LOD:** #84 (video): „splits the grass into 3 mmis in a clipmap fashion … just a matter of initially distributing the
instances into 3 mmis depending on the distance. … each subsequent cascade would use a simpler mesh, and possibly a lower
density. … this can be further divided up into radial sectors or along a square grid to employ engine's frustum culling.“
Fade v ukázce není.

**Pohyb kamery:** posouvá se jen uzel (rodič = hráč), MultiMesh buffer se nikdy nepřepisuje (#83, #92: „Not messing with
vertex buffers is always better“). U chvění (#98) radí: „eliminate all scaling and rotation from the node the grass is
parented to.“

**Výkon:** nic nenaměřeno. #81 tvrdí „A single mmi with half a million instances … doesn't present performance problems
for modern gpus“, ovšem pro desktop, bez čísla. Mobil se nezmiňuje.

**Demo projekt:** odkaz v #75 (`https://limewire.com/d/w7VSl#9vSxMWQC58`) vrací **HTTP 410 Gone**, stáhnout nejde.
Skript, který mřížku vytváří, ve vlákně není. Je jen popis v #86/#88/#90.

**Licence:** v příspěvcích žádná. Podmínky fóra (Discourse ToS) dávají licenci jen provozovateli fóra. Kód proto
nekopírovat doslova, vlastní implementace podle principu je v pořádku (princip je obecně známý).

**Pozor na Compatibility (ověřeno ve zdrojích Godot 4.4.1):**
- `drivers/gles3/shaders/scene.glsl:504-507`:
  ```glsl
  highp mat4 model_matrix = world_transform;
  #ifdef USE_INSTANCING
  	highp mat4 m = mat4(instance_xform0, instance_xform1, instance_xform2, vec4(0.0, 0.0, 0.0, 1.0));
  	model_matrix = model_matrix * transpose(m);
  ```
  → `MODEL_MATRIX` **obsahuje** transformaci instance i v GL Compatibility, takže `MODEL_MATRIX[3].xz` z #75 funguje.
- `drivers/gles3/storage/material_storage.cpp:1287` `actions.renames["NODE_POSITION_WORLD"] = "model_matrix[3].xyz";`.
  V Compatibility je tedy `NODE_POSITION_WORLD` poloha **instance**, ne uzlu, na rozdíl od Forward+. Odečet
  `- NODE_POSITION_WORLD.y` z #75 by v Compatibility odečítal výšku instance. U nás se proto výška uzlu musí předat uniformou.
- `material_storage.cpp:1165` `actions.renames["INSTANCE_ID"] = "gl_InstanceID";` → `INSTANCE_ID` v GLES3 funguje.
- **Rozpor s naším komentářem**: `shaders/stebla.gdshader:92-93` tvrdí, že „v rendereru compatibility je transformace
  instance MultiMeshe už ve VERTEX a MODEL_MATRIX je jen uzel“. Podle `scene.glsl:504-507` a `:617-625` (`#CODE : VERTEX`
  běží před `vertex = (modelview * vec4(vertex, 1.0)).xyz`) to v 4.4.1 neplatí. Louka používá jednotkové transformace
  instancí, takže se to v ní nikdy nemohlo projevit. **Podezření, neověřeno na zařízení.** Před prototypem to potvrdit
  jednoduchým shaderem a snímkem (§5 krok 0).

**Pro Havrana:** ze všech zdrojů nejlépe sedí na problém (1). Pevná síť, žádná práce CPU na trs, tráva je v novém
místě hned ve stejném snímku. Převezmeme princip, ne kód. Pro Compatibility a tablet ho upravíme v §5.

---

## 3. Zylann: „grass around the player“ a godot_heightmap_plugin (https://github.com/Zylann/godot_heightmap_plugin)

**Fórum (popis principu):** https://forum.godotengine.org/t/how-to-dynamically-render-grass-only-around-the-player/6657
(Zylann, 2022, převedeno ze staré Q&A):
> „maintaining a grid of grass chunks around the camera … When a chunk gets too far, I remove it. When the area has empty
> spots for a chunk, I add them. … precalculate one with full density, share it on all multimeshes and rather decimate
> instances from a vertex shader according to a density map … to smooth out the "popping" effect … I fade grass using a
> fragment shader based on distance.“ Video: https://www.youtube.com/watch?v=nrkvvzZ51Js

**Kód: `addons/zylann.hterrain/hterrain_detail_layer.gd` (989 ř.)**
- Blok: `:20 const CHUNK_SIZE = 32`, dosah `:65 view_distance := 100.0` (max 500; `:63` TODO: zrychlit `_get_chunk_aabb`,
  issue #155). Rozpočet aktualizací `:23 CHUNK_UPDATES_BUDGET_US = 1000` (1 ms na snímek, `:616-638`).
- **Jeden MultiMesh pro všechny bloky:** `:195 var _multimesh: MultiMesh`, generuje se jednou (`:868-878`
  `_regen_multimesh` → `_generate_multimesh(CHUNK_SIZE, density, …)`). Bazén instancí `:197`, `:760-769`
  (`mmi.set_multimesh(_multimesh)`).
- Generování (`:934-975`): `cell_count = resolution * resolution` (32² = 1024), `total = cell_count * int(density) + …`.
  Výchozí `density := 4.0` (`:107`) dává **4096 instancí na blok 32 × 32 m** (4 na m²). Pozice jsou v buňce 1 m
  rozházené ±0,5 m (`:943`, `:960-962`), otočení náhodné, výška 0 (dopočítá shader).
- **Při pohybu kamery** (`process`, `:475-575`): spočítá rozsah bloků kolem diváka (`:498-503`
  `cr = int(view_distance) / CHUNK_SIZE + 1`). **Jen když se změní** (`:539-540 # Only update when the camera moves
  across chunks`), přidá chybějící bloky do fronty (`:543-556`). Nový blok dostane z bazénu MMI a nastaví se mu jen
  transformace a AABB: `:677-685` `mmi.set_transform(trans)`, `mmi.set_aabb(local_aabb)`. Vzdálené bloky vrátí do bazénu
  (`:651-653`, `:746-757`). Bloky, kde detail mapa nic nemá, přeskočí podle mapy obsazenosti (`:662-674` `occ.get_state(cpos)`).
- MMI bez uzlů ve stromu: `util/direct_multimesh_instance.gd:9` `RenderingServer.instance_create()`, `:26-40`
  `instance_set_transform`, `instance_set_custom_aabb`.
- AABB bloku z rozsahu výšek heightmapy: `:715-734` `_get_chunk_aabb` → `terrain_data.get_region_aabb(...)`.

**Shader: `addons/zylann.hterrain/shaders/detail.gdshader` (116 ř.)**
```glsl
// :55-74
vec4 obj_pos = MODEL_MATRIX * vec4(0, 1, 0, 1);
vec3 cell_coords = (u_terrain_inverse_transform * obj_pos).xyz;
cell_coords.xz += vec2(0.5);              // střed pixelu kvůli bilineárnímu filtru (#183)
vec2 map_uv = cell_coords.xz / vec2(textureSize(u_terrain_heightmap, 0));
...
density = texture(u_terrain_detailmap, map_uv).r;
float hash = get_hash(obj_pos.xz);
if (density > hash) {
    ...
    float height = get_height(u_terrain_heightmap, map_uv) / cell_coords.y;   // :79
    VERTEX *= u_instance_scale;
    VERTEX.y += height;
    ...
    float dr = distance(wpos, CAMERA_POSITION_WORLD) / u_view_distance;       // :87-88 fade
    COLOR.a = clamp(1.0 - dr * dr * dr, 0.0, 1.0);
} else {
    VERTEX = vec3(0, 0, 0);               // :94-96 degenerované trojúhelníky
}
```
- **Kde tráva je:** detail mapa R8 přes celý terén (dokumentace `doc/docs/index.md:740`: „`u_terrain_detailmap` |
  `sampler2D` | `R8` | … grass density, from 0 to 1“). Trs se kreslí, když `density > hash` (hash z polohy instance),
  takže hustota ubývá po jednotlivých trsech, stejně jako dnes u nás.
- **Výška:** heightmapa (formát RF) ve vertex shaderu (`shaders/include/heightmap.gdshaderinc:5-8`
  `return texture(spl, pos).r;`). Pro textury, které filtr neumí, je ruční bilineární varianta přes `texelFetch`
  (`:34-66` `sample_height_from_viewport`). Tu lze převzít pro tablet (§5, pozn. k formátu).
- **LOD a mizení:** jen fade alfou s třetí mocninou vzdálenosti (`:87-88`) a alpha scissor ve fragmentu (`:102`).
  Hustota se vzdáleností neubývá, LOD sítě není.
- **Compatibility:** dokumentace `doc/docs/index.md:9` říká „expected to work on all platforms supported by Godot's
  GLES3 renderer“ a `:1072` „GLES2 is not supported“ (text z doby Godotu 3). Pro 4.x Compatibility jsem v repu
  nenašel žádné výslovné ověření. Shader používá jen `texture()` ve vertex shaderu a `textureSize`, obojí je v GLES3 jádru.
- **Výkon:** v repu žádná čísla. Strop je dosah 500 m kvůli GDScriptu (`:63`).

**Licence:** **MIT** (`addons/zylann.hterrain/LICENSE.md`: „Copyright (c) 2016-2023 Marc Gilleron … Permission is
hereby granted, free of charge…“). Převzít smíme, s ponecháním copyrightu v hlavičce převzatého souboru a v titulcích.

**Pro Havrana:** dva přímo použitelné triky. (a) **Jeden sdílený MultiMesh pro všechny bloky, blok se jen posune**
(transformace a `custom_aabb`), takže paměť ani přestavba nezávisí na počtu bloků. (b) **Hustota z textury a `hash`
ve vertex shaderu** s degenerovaným trojúhelníkem místo `discard`, což sedí k pravidlu bez discard v našem `stebla.gdshader:6-7`.
Hash z polohy instance ale u Zylanna funguje proto, že bloky stojí na pevných světových pozicích po 32 m. Totéž
splní přichycená mřížka podle normalized.

---

## 4. Volitelné: Godot Landscaper, M Terrain, hexaquo

**Godot Landscaper** (https://github.com/dip000/godot-landscaper, MIT, „Copyright (c) 2023 Adrián“)
- Pozice: CPU jednou při přestavbě v editoru. `addons/godot_landscaper/scripts/brush_grass_spawn.gd:126`
  `total_grass = density.value * world_size.x * world_size.y`, `:161-195` náhodný bod, maska
  `img.get_pixelv(...)` (`:169`), `PhysicsRayQueryParameters3D` raycast na výšku (`:181-189`), `set_instance_transform`
  (`:204-210`). LOD ani dělení na bloky není, při pohybu se nic neděje.
- Compatibility: `shaders/grass_shader.gdshader:38-43`
  ```glsl
  // "instance" keyword is only for Vulkan rendering drivers. This avoids compilation errors
  #if defined GL_COMPATIBILITY
  uniform int variant_index = 0;
  #else
  instance uniform int variant_index;
  #endif
  ```
  README:117 „supports GL Compatibility rendering! But it is limited to one grass variant due to the lack of shader
  instance variables in Compatibility“. → **U nás žádné `instance uniform`**. Parametry prstenců předávat přes materiál
  (jeden materiál na prstenec) nebo přes globální uniformy.

**M Terrain** (https://github.com/mohsenph69/Godot-MTerrain-plugin, MIT, „Copyright (c) 2023 mohsenph69“)
- Pozice: C++ GDExtension na CPU, po blocích terénu. `gdextension/src/grass/mgrass.cpp:369` `create_grass_chunk`.
  Smyčka přes pixely bitové mapy trávy (`:436-446` `_grass_cell_getter(x,y,…)`), kopie předpočítané náhodné
  transformace z bazénu (`:449-454` `rand_buffer + (rand_index%rand_buffer_size)*…`), výška `ptrw[7] +=
  grid->get_height(pos)` (`:458`) a jeden zápis bufferu `g->set_buffer(count, …, buffer, …)` (`:505`).
- LOD: na úrovni `lod` se bere jen každý `2^lod`-tý pixel (`:394-399` `lod_scale = pow(2,lod)`, `:436`
  `x = px.left + i*lod_scale`), takže hustota ubývá po mocninách 2. Každá úroveň může mít vlastní síť
  (`meshes->get_mesh_rid(lod)`, `:501-505`). Strop instancí `grass_count_limit` (`:351-366` `cull_out_of_bound`).
- Pro nás: potvrzuje, že i nativní C++ plugin plní buffer po blocích na CPU. To je přesně naše současná cesta, jen
  rychlejší. GDScript tuhle rychlost nedá (`docs/predani.md`: je potřeba ~7× zrychlit). Nepřebíráme.

**hexaquo, Grass Rendering Series Part 4** (https://hexaquo.at/pages/grass-rendering-series-part-4-level-of-detail-tricks-for-infinite-plains-of-grass-in-godot/,
na nějž odkazuje fórum #1): blok 5 × 5 m s 10 000 stébly (9 trojúhelníků na stéblo). Daleko se vymění za
`grass_multimesh_simple.tres` (1 trojúhelník) a ještě dál za impostor rovinu (fade 5–10 / 10–20 m). Autor uvádí „just
under 2 ms“ na svém stroji (bez specifikace) a renderer neuvádí. Repo `https://git.hexaquo.at/karl/godot-grass`
licenci neuvádí, článek je cc-by-sa 4.0. Číst jsem ho jen přes WebFetch, kód jsem nestahoval.

---

## 5. Prototyp pro Havrana

### 5.0 Co převzít

| Co | Odkud | Jak |
|---|---|---|
| pevná mřížka instancí, uzel jede s kamerou, světová poloha trsu = přichycená mřížka, hash z buňky mřížky | normalized #71/#75/#88 | vlastní implementace (bez licence) |
| jeden sdílený MultiMesh na prstenec, dlaždice jen transformace + `custom_aabb` (ořez záběrem) | Zylann `hterrain_detail_layer.gd:195,677-685`, `direct_multimesh_instance.gd` | MIT, převzít postup |
| hustota z textury, `hustota > hash`, jinak `VERTEX = vec3(0)` (bez discard) | Zylann `detail.gdshader:69-74,94-96` | MIT |
| výška z textury ve vertex shaderu, vzorek ve středu pixelu (+0,5) | Zylann `detail.gdshader:57-61`, `heightmap.gdshaderinc:34-66` | MIT |
| zákaz `instance uniform` | Landscaper `grass_shader.gdshader:38-43` | poučení |
| prstence s řidší mřížkou (clipmap) | normalized #84, MTerrain `mgrass.cpp:394-399,436` | princip |
| vzhled trsu (atlas, druhy, vítr, fragment, barva terénu) | **náš** `shaders/stebla.gdshader` | beze změny fragmentu, nový jen vertex |

**Pravidla zůstávají na jednom místě:** hustotu, druh a „bez trávy“ dál rozhoduje `louka.gd` (`_vzorek` a podmínky
z `_rozsej`). Jen se jednou upečou do textury (jak navrhuje `trava_gpu.md` bod 1), takže v shaderu není druhá sada
pravidel. Odstupy zůstávají jen v `pravidla_sveta.json` `pasma` (CLAUDE.md, záplatování zakázáno).

### 5.1 Data: co upéct a jak velké

Zdroje u nás:
- masky `trava_kraj` (x0 −250, z0 −250, krok 2 m, 576 × 801, výšky −14,42…84,68 m) a `trava_ves` (x0 330, z0 690,
  2 m, 141 × 141, −6,02…17,05 m) v `modely/svet.json`. Spočteno z dat 4. 11.
- výšky louky bere `louka.gd:101-102` z `main.svet._vys[key]["y"]`, tedy **po úpravě profilem cest**, ne ze svet.json.
  Péct se proto musí ve hře (headless), ne skriptem nad JSONem.
- `_vzorek` (`louka.gd:206-350`): maska, pěšiny (`stanoviste` A), koruny a skály, nádvoří a val, břehy, koryto, sklon,
  terasy, budovy, zahrady, tržiště, rybník, mlýn (vlastní výška `mt.x`), lom.
- `_rozsej` (`louka.gd:1301-1365`): `+ 0,5 × _okraj` (okraj lesa), `kr_cesta` a `_okoli_hust`, `_prah`, krytí shora
  `_kryto`, `_nizka`, divokost, druh (šumy `s1`/`s2` → `typ`), lem cest (`v.x < 0,45 or v.z < 1,6`), byliny (22 %).

Upéct na mřížku **0,5 m** (bod = střed pixelu; `louka.gd:1318-1319` dnes rozhazuje trsy o ±0,45 KROK):
- `hustota_<oblast>.bin`: hlavička (x0, z0, krok, nx, nz) a pole RG8:
  - R = pravděpodobnost trsu `p = clamp(v.x · 1,6 · (1 + 0,5 · div), 0, 1)`, a 0, kde dnes platí `v.x < _prah`, krytí
    (mimo `kr_cesta`) nebo `_nizka` (`louka.gd:1331`),
  - G = kód druhu: `typ` 0–3 ze šumů (`:1333-1337`), příznak lemu (`:1338-1343`), příznak kapradí (`v.x < 0,45`,
    `:1362`) a divokost (výška × (1 + 0,3 div), `:1358`) zakódované v bitech,
- `vyska_<oblast>.bin`: RH (half float) = `_vzorek(...).y`, aby seděl i terén mlýna a dalších dílů.
- Načtení: `Image.create_from_data(nx, nz, false, Image.FORMAT_RG8 / FORMAT_RH, bytes)` → `ImageTexture.create_from_image`.
  **Žádný import ani .tres/.uid** (CLAUDE.md pravidla pro Godot soubory).

Velikosti (spočteno):
| oblast | rozsah | pixelů po 0,5 m | RG8 | RH | ~ čas pečení (65 µs/`_vzorek`, PC, `predani.md`) |
|---|---|---|---|---|---|
| louka u tvrze | x −60..60, z 150..330 | 240 × 360 = 86 400 | 173 kB | 173 kB | ~6 s |
| les | x 140..240, z 860..920 | 200 × 120 = 24 000 | 48 kB | 48 kB | ~2 s |
| celá krajina (pro budoucnost) | 1152 × 1602 m | 2304 × 3204 = 7,38 M | 14,8 MB | 14,8 MB | ~8 min (1 vlákno) |
| celá krajina po 1 m | | 1,85 M | 3,7 MB | 3,7 MB | ~2 min |

Masky obou oblastí: louka 5165 z 5400 buněk 2 m s trávou, les 1372 z 1500. Výšky v oblastech: louka −5,9…5,6 m,
les −8,1…6,0 m.

**Formát výšky na tablet:** R16F (RH) se v GLES3 smí filtrovat lineárně (jádro specifikace), R32F ne (filtrace
float32 vyžaduje rozšíření `OES_texture_float_linear`, které Mali často nemá). Proto RH, ne RF jako hterrain.
Přesnost half float: do 8 m krok ≤ 4 mm (obě oblasti), nad 64 m 6 cm. Pro celou krajinu ukládat výšku vůči
výšce oblasti, nebo 2 × R8 a ručně bilineárně přes `texelFetch` (postup `heightmap.gdshaderinc:34-66`). Ve vertex
shaderu vždy `textureLod(..., 0.0)` (bez mip).

### 5.2 Kreslení: prstence a dlaždice

Nové soubory (vedle louky, žádná úprava jejích výpočtů):
- `scripts/trava_gpu.gd`: uzel `TravaGpu`, prstence a dlaždice, načtení textur, přepínač.
- `shaders/trava_gpu.gdshader`: `#include` téhož kódu jako `stebla.gdshader`. Fragment beze změny (Bayer, atlas,
  barva terénu), nový je jen `vertex()`.
- parametry v pravidlech (ne v kódu): `pravidla/svet/modely.json` → `"trava_gpu": {"prstence": [[krok, dlazdice_m,
  pul_strana_m, od_m, do_m], …], "oblasti": [[x0, z0, x1, z1], …]}`.

Návrh prstenců (krok × počet instancí na dlaždici = celé číslo, aby mřížka navazovala):
| prstenec | krok trsu | dlaždice | pokrytí | instancí / dlaždici | dlaždic | instancí celkem |
|---|---|---|---|---|---|---|
| A | 0,36 m (= `KROK`) | 7,2 m (20 × 20) | čtverec 6 × 6 = 43,2 m | 400 | 36 | 14 400 |
| B | 0,72 m | 14,4 m (20 × 20) | 8 × 8 = 115,2 m bez středu 3 × 3 | 400 | 55 | 22 000 |
| C | 1,44 m | 28,8 m (20 × 20) | 6 × 6 = 172,8 m bez středu 4 × 4 | 400 | 20 | 8 000 |
|   |   |   |   |   | **111 kreslení max.** | **44 400** |

- Každý prstenec má **jeden** MultiMesh (400 instancí, `TRANSFORM_3D`, bez custom data). Transformace instance =
  jen posun na bod mřížky dlaždice (normalized #88: bez otočení a měřítka). Paměť: 3 × 400 × 48 B = **58 kB**
  (dnes MultiMesh na buňku a vrstvu). Plní se jednou při startu.
- Dlaždice = `RenderingServer.instance_create()` se sdíleným MultiMeshem prstence (Zylann `direct_multimesh_instance.gd`),
  `instance_set_custom_aabb` s výškou z rozsahu oblasti (Zylann `:715-734`, normalized #50). Bez uzlů ve stromu.
- Každý snímek: uzel prstence přichytit na **jeho krok** (ne na dlaždici): `pos = (cam.xz / krok).floor() * krok`.
  Trs pak stojí na pevném světovém bodě a čtverec drží kolem kamery s chybou ≤ 1 krok. Kůň 10,5 m/s při 60 FPS ujede
  0,175 m za snímek < 0,36, takže jedno přichycení za snímek stačí. `physics_interpolation_mode = OFF` jako louka
  (`main.gd:494`), jinak se uzel opozdí o tik fyziky (chvění, normalized #98).
- Předávka mezi prstenci **ve shaderu podle skutečné kamery** (ne podle tvaru prstence). A kreslí trs, když
  `max(|dx|, |dz|) < hranice_AB`. B kreslí, když je ≥ `hranice_AB` a < `hranice_BC`, a tak dál. Geometrie musí mít
  rezervu ≥ 1 krok: A s polovinou strany 21,6 m kryje kameru do 21,2 m, díra B (21,6 m) začíná nejpozději na
  21,6 + 0,72 m. Hranice proto vychází A/B ≈ 21 m a B/C ≈ 57 m, konec C ≈ 86 m (tablet dnes trsy do 80 m,
  `modely.json` `trava_dosah_m`). Přesná čísla doladit, **NEOVĚŘENO**.

`vertex()` (postup, náš vlastní kód):
1. `w = (MODEL_MATRIX * vec4(0,0,0,1)).xz` je bod mřížky trsu (v Compatibility i Forward+ obsahuje transformaci
   instance, `scene.glsl:504-507`; ověřit §5 krok 0). `id = ivec2(round(w / krok))` jsou celá čísla.
2. Hash: celočíselný z `id` (uint, GLES3 umí) a prstence. Ne `fract(sin(dot(...)) * 43758)` z fóra a hterrain, protože
   při souřadnicích do 1350 m je argument `sin` ~10⁵ a přesnost `sin` na mobilních GPU je u velkých argumentů
   nejistá. **Podezření, neměřeno.** Z hashe se vezme posun ±0,45 kroku (jako `louka.gd:1318`), otočení, velikost a
   prahy (místo dnešního `INSTANCE_CUSTOM.x`).
3. `uv = (pata.xz - oblast.xy) / oblast.zw` a pak `textureLod(hustota, uv, 0)` a `textureLod(vyska, uv, 0)`. Mimo
   oblast p = 0.
4. Hustota podle vzdálenosti: tentýž vzorec jako dnes (`stebla.gdshader:73-75`, `hu = mix(1, hust_zbytek,
   smoothstep(hust_od, hust_do, d)) …`) vynásobený `krok_prstence² / KROK²` (B kreslí 4× méně trsů na m², proto má
   každý 4× větší šanci). Trs je vidět, když `hash < p · hu`. Jinak `VERTEX = vec3(0)` (Zylann `detail.gdshader:94-96`).
5. Druh a výška trsu z G a hashe, pak zbytek dnešního `vertex()` (`stebla.gdshader:76-111`: tabulka druhů, otočení,
   vítr, normála) beze změny.

**Hustota a vzhled (upozornění):** dnes se do 80 m ubírá plynule (`hust_od` 20 → `hust_do` 80). Při 40 m tak zbývá
asi 74 % trsů z kroku 0,36 m. Prstenec B s krokem 0,72 m umí nejvýš 25 %. Proto dvě varianty, obě z pravidel:
- **„shoda“**: A i B krok 0,36 m. Vzhled jako dnes a tráva hned, instancí v záběru zhruba jako dnes, GPU se nejspíš
  nezlepší.
- **„úspora“**: prstence podle tabulky. Méně instancí, ale 20–60 m řidší (vynahradit velikostí trsu jako dnes
  `mix(1.0, 1.6, dal)`). Vzhled posoudí Míša.

Vrstvy: prototyp nahrazuje jen vrstvu 0 (trsy a byliny). Vrstva 3 (vysoká tráva) zůstává v `louka.gd`. Vrstvy 2 a 4
jsou dnes vypnuté (`louka.gd:877-878` výchozí `[2, 4]`).

### 5.3 Zapnutí vedle louky (A/B)

- `main.gd`: nová volba `trava_gpu` stejně jako `trava_uspora` (`main.gd:86`, `:147` čtení cfg, `:267` přepnutí,
  `:352` text v Nastavení, `:1900` uložení). Po restartu se `TravaGpu` vytvoří vedle `Louka` (`main.gd:492-496`).
- V režimu B `louka.gd` **nezapisuje trsy vrstvy 0 uvnitř obdélníků `oblasti`**: jedna podmínka v `_zaznam` (`louka.gd:1546`)
  pro seznam `zaz[0]` (zapisuje se z `:1358`, `:1368`, `:1427`, `:1473`, `:1485-1491`). Vně oblastí běží louka jako dnes. Rozsev buněk tedy dál stojí CPU v obou režimech,
  srovnání FPS je férové.
- Měřicí trasa: varianta `"trava_gpu"` už v `pravidla/svet/mereni_trasa.json` (`varianty`, od ř. 189) je, jenže
  `scripts/mereni_trasa.gd:82` ji chytí jako `begins_with("trava_")` → `float("gpu")` = 0 → `nastav_dosah_trsu(0)`
  = výchozí dosah (`louka.gd:1819-1821`). **Dnes tedy měří totéž co "".** Před měřením přidat větev
  `v == "trava_gpu"` před `:82` (a popisek u `:97`). Přepnutí za běhu = viditelnost uzlu `TravaGpu` a zákaz vrstvy 0
  v oblastech (to druhé potřebuje znovu postavit buňky v oblastech, takže `zahrati_s` trasy musí stačit).
- Do `_ab_skupiny` (`main.gd:2532`) přidat skupinu `trava_gpu`, aby šla vypnout samostatně.

### 5.4 Co měřit a čím porovnat

Trasa: úseky `louka` (28,102 → 60,200) a `kun-louka-trava` (−20,300 → −30,380, ve výšce jezdce) vedou loukou
u tvrze, `kun-les-mimo` (150,905 → 200,880) lesem (`mereni_trasa.json` `useky`). Varianty v tomto pořadí (kvůli
zahřívání tabletu, `mereni_verze.md` 0.9996/0.9997): `""`, `"trava_gpu"`, `"louka"` (bez trávy), případně `"3d_50"`
pro oba režimy.

| veličina | jak | A (louka.gd) | B (trava_gpu) |
|---|---|---|---|
| ms na snímek p50 / p95 / max, záseky > 40 ms | stávající trasa (`viewport_set_measure_render_time`, `mereni_trasa.gd:45`) | ✓ | ✓ |
| instance v záběru | A: součet `visible_instance_count` buněk, jejichž AABB protne frustum (`Camera3D.get_frustum()`); B: dlaždice v záběru × 400 a zvlášť počet s `p·hu > hash` (počítat na CPU ze stejných textur, jen v diag režimu) | ✓ | ✓ |
| vrcholy | instance × 18 (trs = 3 karty × 6 vrcholů, `louka.gd:1770-1783`) + `RENDER_TOTAL_PRIMITIVES_IN_FRAME` (`main.gd:2586-2587`) | ✓ | ✓ |
| kreslení | `RENDER_TOTAL_DRAW_CALLS_IN_FRAME` | ✓ | ✓ |
| VRAM | `Performance.RENDER_VIDEO_MEM_USED`, `RENDER_TEXTURE_MEM_USED`, `RENDER_BUFFER_MEM_USED` | ✓ | ✓ |
| CPU louky | čas `_process` louky (`TVRZ_LOUKA_CAS`, `louka.gd:77`) + `TIME_PROCESS` | ✓ | ✓ (má být ~0) |
| objevení trávy při 10,5 m/s | test `trava_dorust` (`tools/test_svet.gd:3133-3197`, trasa (0,170) → (−10,540) vede loukou u tvrze): A jako dnes (buňka do `trava_dorust_m` bez úrovně = pozdě); B nová kontrola: snímek je „pozdě“, když je střed prstence od kamery dál než 1 krok, nebo když oblast pod kamerou nemá načtenou texturu | pozdě X z 1800 | očekáváno 0, ověřit |

Oddělit vrcholy a pixely: `"3d_50"` (méně pixelů) v obou režimech. Když B zrychlí jen s plným rozlišením, brzdí
vrcholy nebo instance, a když zrychlí i A s `3d_50`, brzdí pixely (překreslování karet). Dosavadní záznamy si
**protiřečí**: 0.9991 (`mereni_verze.md:19`) při +60 % pixelů FPS beze změny, tedy „brzda není vyplňování“. 0.9995
při zkrácení trsů na 50 m beze změny, tedy „cena trávy je zblízka“. Obojí je slučitelné s tím, že brzdí trsy do ~20 m.
Ty má varianta „shoda“ stejné jako dnes. **Bez tohoto měření nelze slíbit, že B sníží 80–130 ms.** Jisté je jen
odstranění pozdního objevení (problém 1).

Přijetí (navazuje na `trava_gpu.md` „Přijetí“): `trava_dorust` B 0 snímků pozdě ve všech třech chodech. Snímky louky
u tvrze a lesa A vs B (`--write-movie`, prohlédnout sám) a pak nezávislý kontrolor. Tabulka trasy do
`docs/mereni_verze.md`. `zasazeni`, `louka_bod`, `nizka_trava`, `bylina_velikost` v oblastech na upečených datech.

### 5.5 Pořadí kroků prototypu
0. Ověřit v Compatibility na PC (a jedním snímkem na tabletu), co je `MODEL_MATRIX[3]` u MultiMeshe s nejednotkovou
   transformací instance. Rozhoduje, zda bod 1 ve `vertex()` platí, a opraví komentář `stebla.gdshader:92-93`.
1. Pečení dvou oblastí (test `louka_pec` v `tools/test_svet.gd`, výstup `modely/louka/hustota_*.bin`, `vyska_*.bin`).
   Kontrola obrázkem: R kanál vedle `build/mapa_stavby.png`.
2. `trava_gpu.gd` + `trava_gpu.gdshader`, jen prstenec A, louka u tvrze. Snímek.
3. Prstence B a C, předávka, varianty „shoda“ / „úspora“.
4. Přepínač v Nastavení, varianta trasy, oprava `mereni_trasa.gd:82`.
5. Míša: trasa na tabletu → `mereni_verze.md`. Teprve pak rozhodnout o celé krajině (14,8 + 14,8 MB po 0,5 m,
   nebo 7,4 MB po 1 m) a o smazání rozsevu za běhu.

---

## 6. Co nešlo stáhnout nebo ověřit
- Demo projekt normalized (limewire, #75): HTTP 410. Skript na mřížku chybí.
- Video Zylanna a videa z fóra jsem neviděl, jen text.
- hexaquo repo (`git.hexaquo.at/karl/godot-grass`): nestahoval jsem ho, licence neznámá.
- U žádného zdroje nejsou naměřená čísla na mobilu nebo v GL Compatibility. Jediné číslo, „just under 2 ms“ (hexaquo),
  je z neuvedeného PC.
