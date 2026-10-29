# Terén a vegetace pro velký otevřený svět v Godotu 4 na Androidu

Kontext projektu: terén = mesh z Blenderu rozdělený na díly, luční tráva jako MultiMesh v buňkách 32 m stavěných ve vláknech, stromy LOD0/LOD1/impostor, ~150 druhů, ~150k instancí celkem. Rešerše 29. 10. 2026, 19 volání nástrojů. Telefonních měření (FPS na jmenovaném zařízení) se pro trávu v Godotu skoro nenašlo, viz Gaps.

## 1. Terén: Terrain3D, HTerrain, clipmap / quadtree, jeden mesh nebo díly, cena splatmapy, podpora Androidu, kolize

### Takeaway
Terrain3D (GDExtension, geometry clipmap, kolize z výškové mapy jen kolem kamery) je dnes jediný udržovaný terénní addon s deklarovanou plnou podporou Mobile i Compatibility rendereru. Android ale sám označuje za „trochu experimentální“ kvůli texture arrays na některých zařízeních. HTerrain (Zylann) je jen v režimu oprav chyb a je celý v GDScriptu. Na mobilu se vyplácí blendovat málo vrstev: CLASSIC4 stojí zhruba polovinu MULTISPLAT16 (měřeno na desktopu).

### Cited Findings
- Terrain3D: „The Forward Vulkan Mobile renderer is fully supported“. Compatibility (OpenGL ES 3) je „fully supported since Terrain3D 1.0 and Godot 4.4“. — [Terrain3D docs – Platforms](https://terrain3d.readthedocs.io/en/latest/docs/platforms.html)
- Terrain3D na Androidu: hlášeno funkční s 0.9.1 a Godotem 4.2, stále „a bit experimental“. Doporučuje max_regions 64–256 (nejširší pokrytí má 128), PNG/TGA místo DDS a zapnutý import ETC2/ASTC. Release obsahuje binárky arm32 i arm64. Známý problém: „Some mobile devices appear to not fully support texture arrays“. Související issues #668, #137, #197. Konkrétní zařízení nejsou uvedena. — [Terrain3D docs – Platforms](https://terrain3d.readthedocs.io/en/latest/docs/platforms.html)
- Terrain3D používá geometry clipmap (podle Mike Savage a Witcher 3), ne mřížku chunků, které se vytvářejí a ruší. Mesh vznikne jednou při startu a posouvá se za kamerou, výšky čte vertex shader z heightmapy. Platí 1 pixel = 1 vertex na LOD0. `vertex_spacing` roztahuje mřížku: při 2.0 pokryje mapa 1024 px svět 2048 m. Paměť se alokuje jen pro regiony s obsahem. — [Terrain3D docs – System Architecture](https://terrain3d.readthedocs.io/en/latest/docs/system_architecture.html)
- Kolize v Terrain3D: výchozí je Dynamic/Game, kolize jen kolem kamery, bez uzlů, „nejrychlejší“. Full režimy generují kolizi pro celý terén a na velkých terénech berou hodně paměti. Pro nepřátele doporučují místo kapslí raycasty nebo `get_height()`, pro fyzikální potíže Jolt. — [Terrain3D docs – Collision](https://terrain3d.readthedocs.io/en/latest/docs/collision.html)
- HTerrain (Zylann): cílí na Godot 4.6+, už se nevyvíjí aktivně („only do bug fixes these days“), celý v GDScriptu bez plánu na GDExtension. — [GitHub Zylann/godot_heightmap_plugin](https://github.com/Zylann/godot_heightmap_plugin)
- HTerrain LOD: CPU quadtree nad chunky 32×32 (nebo 16×16), švy mezi úrovněmi jsou ošetřené. Větší chunk znamená méně draw callů, ale víc paměti. LOD funguje jen pro jednu kameru. Kolize přímo z heightmapy (heightfield), podle autora levnější než klasický mesh collider. Collider se neaktualizuje sám a jeho update nejde dát do vlákna. — [HTerrain docs](https://hterrain-plugin.readthedocs.io/en/latest/)
- Cena texturování v HTerrain (NVIDIA GTX 1060, fullscreen průchod): CLASSIC4 (4 textury) 0,8 ms, MULTISPLAT16 (16 textur, blend 4 na pixel, texture arrays) 1,8 ms, tedy „zhruba 2× pomalejší“. ARRAY (až 256 textur, blend 3 na pixel) je experimentální. Podle docs objekty na terénu obvykle část pixelů terénu zakryjí. Plugin běží na GLES3 rendereru, GLES2 nepodporuje. Zabalené textury šetří texture units, protože ne každé GPU jich v shaderu povolí mnoho. — [HTerrain docs](https://hterrain-plugin.readthedocs.io/en/latest/)

### Inferences
- Pro náš terén z Blenderu po dílech: hlavní výhody Terrain3D (clipmap, kolize z heightmapy kolem hráče) si můžeme vzít i bez addonu, a to kolizí přes HeightMapShape3D místo trimeshe a jen kolem hráče. Přechod na Terrain3D by znamenal převést terén na heightmapu a vzdát se převisů a ručně modelovaných míst. Riziko texture arrays na Androidu platí i pro náš splat, pokud ho na texture arrays postavíme.
- Na tabletu je 1,8 ms z GTX 1060 zhruba úměrně horší. Splat se 4 vrstvami na díl (CLASSIC4 styl) je bezpečnější než 16 vrstev v jednom shaderu. To je odvození z desktopového měření, NEOVĚŘENO na zařízení.

### Gaps
- Chybí měření Terrain3D nebo HTerrain na konkrétním telefonu či tabletu (FPS, ms terénu). V docs ani issues, které jsem prošel, nejsou.
- Výchozí mesh_size a počet LOD úrovní Terrain3D ani poloměr dynamické kolize v docs na stránkách, které jsem četl, nejsou.
- Přímé srovnání „jeden velký mesh“ vs „díly“ s čísly pro Godot jsem nenašel. Obecně platí culling po dílech (viz bod 2, celý MultiMesh se kreslí, když do frusta zasáhne kus AABB).

## 2. Vegetace a scatter: Spatial Gardener, ProtonScatter, instancer Terrain3D, SimpleGrassTextured, vlastní MultiMesh, GPU tráva, falloff, buňky, vítr, alpha scissor / A2C / opaque, overdraw

### Takeaway
Všechny hlavní addony stojí na MultiMesh po buňkách (Terrain3D přesně 32×32 m na buňku a druh). Pro nejhustší trávu se doporučuje GPU částicový shader bez uložených dat, pro stromy a kameny MultiMesh. Na mobilu (TBDR GPU) je hlavní nepřítel `discard` (alpha scissor) a alpha-to-coverage, protože vypínají early rejection. Proto je lepší úzká geometrie stébel nebo těsně oříznuté karty, žádné stíny trávy a dither místo alfa prolínání.

### Cited Findings
- Instancer Terrain3D: každý region dělí na buňky 32×32 m, každá buňka má vlastní MultiMesh pro každý mesh, kvůli frustum a occlusion cullingu. Zvládá „hundreds of thousands of meshes“. LOD se přepíná po buňkách, ne po instancích. Výchozí rozestup LOD je 32 m, max 10 LOD, doporučeno ≤4. `last_shadow_lod` určuje poslední LOD se stínem, `shadow_impostor` dává blízkému LOD stín z levnějšího LOD. Bez kolize (plánováno v PR 699), bez cullingu po instancích, žádný vítr (musí přijít z vlastního shaderu), bez ochrany proti přetečení VRAM. — [Terrain3D docs – Instancer](https://terrain3d.readthedocs.io/en/latest/docs/instancer.html)
- Terrain3D doporučuje kombinaci: částicový shader pro trávu (GPU generuje kolem kamery, žádná uložená data, lépe škáluje na velké světy, méně kontroly) a instancer pro stromy a kameny. Příklad je v `extras/particle_example`. Obsahuje i skript pro import ze SimpleGrassTextured. — [Terrain3D docs – Instancer](https://terrain3d.readthedocs.io/en/latest/docs/instancer.html)
- HTerrain detail layers: MultiMesh po chunkách, vertex shader skrývá instance podle 8bit density mapy. Tráva je alpha scissor (opaque průchod, levnější než průhledné řazení). Do dálky mizí zvyšováním prahu alpha scissor, chunky za view distance se cullují. — [HTerrain docs](https://hterrain-plugin.readthedocs.io/en/latest/)
- Spatial Gardener: vyžaduje Godot 4.2+, „thousands of foliage instances without completely tanking the FPS“. Bez čísel a bez zmínky o mobilu. — [GitHub dreadpon/godot_spatial_gardener](https://github.com/dreadpon/godot_spatial_gardener)
- ProtonScatter: Godot 4, procedurální scatter přes modifier stack, MIT, cca 3k hvězd, GitHub je zrcadlo Codebergu. README neříká nic o chunkování, LOD, vláknech ani mobilu. — [GitHub HungryProton/scatter](https://github.com/HungryProton/scatter)
- SimpleGrassTextured: Godot 4 plugin, MIT. Rady k výkonu: vypnout stíny u nízké trávy a použít „auto center position“, aby fungoval LOD. Interaktivní tráva přes render layer 17. Čísla ani poznámky k mobilu nemá. — [GitHub IcterusGames/SimpleGrassTextured](https://github.com/IcterusGames/SimpleGrassTextured)
- 2Retr0/GodotGrass (inspirace Ghost of Tsushima): pozice stébel počítá CPU a kreslí přes MultiMeshInstance, LOD po dlaždicích (hustota a mesh high/low). Autor hlásí, že přepínání LOD po dlaždicích je „very noticeable“ a stíny trávy mají „very high performance cost“. — [GitHub 2Retr0/GodotGrass](https://github.com/2Retr0/GodotGrass)
- Ghost of Tsushima (GDC 2021, Eric Wohllaib): stébla generovaná na GPU, compute shader po dlaždicích s frustum a distance cullingem, high/low LOD stébla s plynulým přechodem. Druhotný zdroj uvádí do dálky „2× širší, poloviční počet“ stébel, NEOVĚŘENO, ze slajdů jsem to nečetl (GDC Vault za přihlášením). — [GDC Vault](https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass); [vyhledávací souhrn včetně threejs fóra](https://discourse.threejs.org/t/migrating-my-grass-system-to-webgpu-and-making-a-robust-grass-plugin/92893)
- Velký MultiMesh se kreslí celý, jakmile do frusta zasáhne jakákoli část jeho AABB, takže je potřeba chunkovat. Culling po instancích by vyžadoval přestavbu na CPU. Uživatelský test: 1 milion instancí MultiMesh ≈ 144 FPS (desktop, neuvedený HW). Calinou (maintainer) doporučuje pro trávu vlastní particle shader, unshaded materiál a vypnuté stíny. — [godot-proposals #8647](https://github.com/godotengine/godot-proposals/discussions/8647)
- Godot fórum (4.6): jeden velký MultiMeshInstance byl na slabém notebooku drahý, doporučení je rozdělit na víc MultiMeshů kvůli cullingu a visibility range. — [forum.godotengine.org 133384](https://forum.godotengine.org/t/how-do-i-make-an-optimized-grass-field-in-godot-4/133384)
- PowerVR (Imagination): „Applications should avoid the use of the discard operation… prefer alpha blending over discarding“. Alpha-tested primitivy nemohou zapsat hloubku, dokud fragment shader nedoběhne, a zdržují následující primitivy. Doporučené pořadí kreslení: opaque → alpha-test → blend. — [Imagination docs – Do Not Use Discard](https://docs.imgtec.com/starter-guides/powervr-architecture/html/topics/rules/do-not-use-discard.html)
- Arm Mali (slajdy 2018): early rejection zakrytých fragmentů funguje jen bez discard, bez zápisu hloubky a s vypnutým alpha-to-coverage. — [Arm mobile graphics optimization guides (slideshare)](https://www.slideshare.net/OwenWu/mobile-graphics-optimization-guides). Alpha-to-coverage navíc potřebuje MSAA, bez něj vypadá jako dither. — [Wikipedia – Alpha to coverage](https://en.wikipedia.org/wiki/Alpha_to_coverage)
- Opačný názor: na Unity fóru někteří tvrdí, že na mobilu je pár vrstev blendu rychlejší než alpha test. Jde o starší příspěvky z éry PowerVR. — [Unity discussions](https://discussions.unity.com/t/is-alpha-test-still-the-evil-for-mobile/684417). Článek z roku 2026 uvádí, že hustý les s alpha kartami má 8–15× efektivní overdraw a na TBDR GPU může `discard` vypnout Hi-Z a kompresi hloubky pro celý snímek. Depth prepass to podle něj stáhne na 1–2× (čísla jsou přebraná, NEOVĚŘENO). — [Cinevva – foliage overdraw](https://app.cinevva.com/blog/2026-05-11-foliage-overdraw)
- Godot visibility ranges: fade mode Disabled je nejlevnější (hystereze, žádná průhlednost). Self a Dependencies vynucují průhledný render během prolnutí. Doporučuje se dither (Object Dither v materiálu, margin 0), nejlépe pro 2 LOD. MultiMeshInstance3D se hodí jako vzdálený HLOD. — [Godot docs – Visibility ranges](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)
- Data na instanci v MultiMesh: transform, color a custom (4 hodnoty). Formát Byte je rychlejší a menší než Float. — [Godot docs – Animating thousands of fish](https://docs.godotengine.org/en/stable/tutorials/performance/vertex_animation/animating_thousands_of_fish.html)

### Inferences
- Naše tráva v buňkách 32 m odpovídá přesně schématu Terrain3D, takže velikost buňky je v souladu s praxí. LOD a falloff hustoty dělat po buňkách (nebo plynule ve vertex shaderu podle vzdálenosti: posun stébel pod zem nebo zúžení), ne přes Self fade.
- Pro tablet: tráva bez stínů, materiál co nejjednodušší (bez normal map), alpha scissor jen tam, kde to jinak nejde. Lepší jsou úzké geometrické trsy stébel nebo karty oříznuté těsně podle alfy, aby bylo méně pixelů s discard. A2C nepoužívat, protože vyžaduje MSAA, které máme zakázané. Vítr ve vertex shaderu nic nestojí na overdraw, jen na vertexech.

### Gaps
- Žádný zdroj s FPS trávy v Godotu na jmenovaném Android zařízení jsem nenašel.
- Doporučené počty stébel nebo trojúhelníků na trs pro mobil z primárního zdroje chybí.
- Jestli Godot Mobile renderer řadí alpha scissor až za opaque, jsem neověřil.

## 3. Stromy a lesy: impostory, billboard a cross-quad LOD, kolik stromů je vidět, visibility ranges

### Takeaway
Pro Godot 4 existují tři cesty k impostorům: „Octahedral Impostor LOD“ (hdrsniped, Forward+ i Mobile, licence nejasná), „godot-imposter“ (zhangjt93, MIT, octahedral, ověřeno na 4.5 beta) a původní SIsilicon/wojtekpil pro Godot 3, které je potřeba portovat. Přepínání LOD dělat přes visibility ranges s Disabled nebo dither, stín brát z levnějšího LOD.

### Cited Findings
- Octahedral Impostor LOD (hdrsniped): Asset Library, peče impostory z vybraných meshů v editoru, Forward+ i Mobile, GDScript API. Licence se v listinách rozchází (Custom „free with credit“ vs Proprietary). — [Asset Library 5528](https://godotengine.org/asset-library/asset/5528)
- godot-imposter (zhangjt93): „Simple implementation of octahedral impostors in Godot“, MIT, ověřeno s Godot 4.5.beta5. Batch zpracování je vypnuté, v plánu je komprese textur kvůli paměti. Podpora Mobile/Compatibility ani rozlišení atlasu uvedené nejsou. — [GitHub zhangjt93/godot-imposter](https://github.com/zhangjt93/godot-imposter)
- Godot Octahedral Impostors (SIsilicon/wojtekpil) je pro Godot 3.2, MIT, verzi pro Godot 4 jsem nenašel. — [GitHub SIsilicon/Godot-Octahedral-Impostors](https://github.com/SIsilicon/Godot-Octahedral-Impostors)
- Octahedral impostor = jednoduchý mesh, který prolíná 2–3 předrenderované pohledy. Používá ho Microsoft Flight Simulator, implementace Ryan Brucks. Trs 30 listů jde nahradit jednou kartou. — [Cinevva – foliage overdraw](https://app.cinevva.com/blog/2026-05-11-foliage-overdraw)
- Instancer Terrain3D: `shadow_impostor` a `last_shadow_lod` snižují cenu stínů stromů, LOD se přepíná po buňkách 32 m. — [Terrain3D docs – Instancer](https://terrain3d.readthedocs.io/en/latest/docs/instancer.html)
- Visibility ranges s Visibility Parent (HLOD) a dither fade bez průhlednosti. — [Godot docs – Visibility ranges](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)

### Inferences
- Naše LOD0/LOD1/impostor odpovídá praxi. Na tabletu by impostor měl být bez discardu, jen tam, kde je silueta (těsný mesh kolem siluety). Stíny jen z LOD0/LOD1 nebo ze stínového proxy, vzdálené stromy bez stínu.

### Gaps
- Počet viditelných stromů a vzdálenosti LOD pro mobilní Godot hru z primárního zdroje jsem nenašel. Výchozí rozestup 32 m v Terrain3D je jediné publikované číslo.

## 4. Kameny a drobnosti: instancing, LOD, kolize jen u hráče

### Takeaway
Instancer Terrain3D ani GPU tráva kolizi nemají. Kolize se generuje jen kolem hráče (vzor Terrain3D Dynamic) a pro NPC se nahrazuje raycastem nebo dotazem na výšku.

### Cited Findings
- Instancer Terrain3D nemá kolizi (plánováno PR 699), MultiMesh je jen jeden mesh a jeden material override na druh, multi-part objekty je třeba spojit, transformy ze scén se ignorují. — [Terrain3D docs – Instancer](https://terrain3d.readthedocs.io/en/latest/docs/instancer.html)
- Terrain3D Dynamic kolize kolem kamery je nejrychlejší. Pro nepřátele raycast nebo `get_height()`, žádné kapsle. — [Terrain3D docs – Collision](https://terrain3d.readthedocs.io/en/latest/docs/collision.html)
- Zvětšení modelů, aby jich bylo méně, dalo 5–20 % zrychlení. Nativní occlusion culling dal přes 50 %, ale nefunguje ve web exportu bez vláken. Měřeno na desktopu s RTX 3080 Ti, „High“ preset (~3,3 M primitiv) prý běží „comfortably on mobile“, bez FPS čísel. — [maclyn devlog](https://maclyn.itch.io/mms-maze-madness/devlog/898004/reasonably-seamless-and-scalable-wall-and-ground-rendering)

### Inferences
- Pro kameny: MultiMesh po buňkách jako u trávy plus jednoduché kolizní tvary (koule, kvádr) vytvářené jen v buňkách kolem hráče, třeba 3×3 buňky. Odpovídá našemu úkolu K2 (hrubá kolize, HeightMap).

### Gaps
- Výkon occlusion cullingu v Godotu na Androidu (CPU cena raster occluderů) jsem nedohledal.

## 5. Streamování vegetace kolem hráče bez záseků (vlákna, set_buffer)

### Takeaway
Generovat data instancí ve vlákně jde, ale samotné předání do MultiMesh běží přes RenderingServer, takže je potřeba posílat celý buffer najednou (`set_buffer` / `multimesh_set_buffer` s PackedFloat32Array) a rozložit nové buňky do více snímků. Thread-safety `set_buffer` jsem v primárním zdroji nepotvrdil.

### Cited Findings
- `buffer` lze nastavit jen když je instance_count ≤ 0, jinak je potřeba pořadí: nastavit buffer před počtem instancí, nebo nejdřív vynulovat počet. Existuje `set_buffer_interpolated` pro fyzikální interpolaci. — [Godot docs – MultiMesh](https://docs.godotengine.org/en/stable/classes/class_multimesh.html) (souhrn z vyhledávání)
- Uživatel, který generoval chunky ve vlákně, hlásil lag při vzniku nového chunku, protože operace MultiMesh obsluhuje visual server. Starší příspěvek z éry Godot 3. — [forum.godotengine.org 11758](https://forum.godotengine.org/t/creating-multimeshes-with-huge-instance-count-during-runtime/11758)
- Při 1M instancí je každá instance plný transform v bufferu, což stojí paměť i čas. Návrh na indirect draw bez transformů zatím nebyl implementován (stav 2024). — [godot-proposals #8647](https://github.com/godotengine/godot-proposals/discussions/8647)
- Terrain3D upozorňuje, že MultiMesh data je nutné ukládat a načítat, zatímco částice nemají žádná data a líp škálují. — [Terrain3D docs – Instancer](https://terrain3d.readthedocs.io/en/latest/docs/instancer.html)

### Inferences
- Náš postup (buňky 32 m, výpočet ve vláknech) je správný. Proti zásekům: připravit PackedFloat32Array ve vlákně, na hlavním vlákně jedno volání `set_buffer` na buňku, max N buněk za snímek. Na tablet použít formát Byte pro color a custom. Nové MultiMeshe nevytvářet, recyklovat pool buněk (podobně jako Terrain3D recykluje clipmap mesh).

### Gaps
- Měření ceny `set_buffer` vs `set_instance_transform` na Androidu jsem nenašel.

## 6. Konkrétní čísla (souhrn)

### Takeaway
Publikovaná čísla jsou téměř jen desktopová. Pro tablet je nutné změřit vlastní (NEOVĚŘENO = vše bez měření na zařízení).

### Cited Findings
- HTerrain: CLASSIC4 0,8 ms vs MULTISPLAT16 1,8 ms fullscreen na GTX 1060. — [HTerrain docs](https://hterrain-plugin.readthedocs.io/en/latest/)
- Terrain3D: buňka 32×32 m, LOD po 32 m, max 10 LOD (doporučeno ≤4), max_regions 64–256 na Androidu. — [Instancer](https://terrain3d.readthedocs.io/en/latest/docs/instancer.html); [Platforms](https://terrain3d.readthedocs.io/en/latest/docs/platforms.html)
- MultiMesh 1M instancí ≈ 144 FPS (desktop, HW neuveden). Calinou uvádí 2D částice 1M při 300+ FPS. — [godot-proposals #8647](https://github.com/godotengine/godot-proposals/discussions/8647)
- maclyn: 3080 Ti 4K, 100 → 120 FPS, ~5,5 M primitiv Ultra a ~3,3 M High. Occlusion culling přes 50 %, manuální culling na webu 30–40 %. — [maclyn devlog](https://maclyn.itch.io/mms-maze-madness/devlog/898004/reasonably-seamless-and-scalable-wall-and-ground-rendering)
- Alpha kartový les: 8–15× overdraw, s depth prepassem 1–2× (přebráno). — [Cinevva](https://app.cinevva.com/blog/2026-05-11-foliage-overdraw)

### Inferences
- Pro náš rozpočet (150k instancí) není problém samotný počet instancí, MultiMesh zvládá řádově víc. Na tabletu rozhoduje overdraw trávy a listí (discard), stíny vegetace a počet draw callů (buňky × druhy: 150 druhů × viditelné buňky může dát tisíce MultiMeshů). Doporučení: sloučit druhy do atlasu, aby jedna buňka měla málo MultiMeshů.

### Gaps
- FPS na jmenovaném Android zařízení pro hustou trávu nebo les v Godotu 4 jsem v žádném zdroji nenašel. Reddit se přímo dohledat nepodařilo.
