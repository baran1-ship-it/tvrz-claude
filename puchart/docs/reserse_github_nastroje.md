# Rešerše GitHub: nástroje pro stavbu a optimalizaci (9. 11.)

Míša 9. 11.: „mrkni na GitHub, bude tam víc takových věcí, třeba nám to pomůže se stavbou a optimalizací“.
Nic se neinstalovalo. Hvězdy a licence přečtené ze stránek GitHubu. Co je označené NEOVĚŘENO, je odhad.

## Hlavní zjištění
- Hotový open-source generátor středověkých staveb pro headless bpy neexistuje. Placené jsou na Superhive, open-source staré nebo obecné. Zdivo, krovy a šindel dál píšeme sami v bmesh.
- Terrain3D v Compatibility rendereru nefunguje (Texture2DArray). Zůstáváme u vlastních dlaždic.
- LightmapGI se v Compatibility zobrazí, ale zapéct ho v něm nejde. Světlo se dá zapéct jen v Blenderu.

## Kandidáti
| nástroj | k čemu | licence | u nás |
|---|---|---|---|
| zeux/meshoptimizer – gltfpack | zjednodušení meshů, LOD, optimalizace glTF z příkazové řádky | MIT, ~8,8k ★ | ano, bez komprese (Godot meshopt/Draco nejspíš neumí) |
| donmccurdy/glTF-Transform | prune, dedup, join, zmenšení textur po exportu | MIT, ~2,1k ★ | ano (Node CLI) |
| jpcy/xatlas + mworchel/xatlas-python | UV2 pro lightmapy a atlasy | MIT | ano (pip) |
| Cycles bake (`bpy.ops.object.bake`) | AO a denní světlo do textury | součást Blenderu | ano, headless |
| hdrsniped/octahedral-impostor-lod-godot | octahedral impostory, crossfade i v Compatibility, MultiMesh, chunk streaming, CLI baker | vlastní („free with credit“) – ověřit | Godot 4.7+, nové (4 ★) |
| zhangjt93/godot-imposter | octahedral impostory pro Godot 4 | MIT, ~169 ★ | Compatibility NEOVĚŘENO |
| Zylann/godot_heightmap_plugin (HTerrain) | terén s chunk LOD | ~2,3k ★ | Compatibility NEOVĚŘENO, zdroj inspirace |
| rikh42/meshmerge, V-Sekai splerger | slučování meshů (méně draw callů) | MIT | inspirace pro hrad po chuncích |
| HungryProton/scatter, Spatial Gardener | rozmístění vegetace | MIT | spíš tráva a keře u hradu |
| arjun988/blender-skills | 94 návodů (LOD, export do Godotu…) | MIT, ~2,3k ★ | potřebuje Blender s okny přes MCP, jen jako čtení |
| HKUDS/CLI-Anything (blender, godot) | ovládání Blenderu a Godotu bez obrazovky pro agenty | Apache-2.0 | NEOVĚŘENO |
| Coding-Solo/godot-mcp, Randroids-Dojo skills | Godot přes CLI, headless testy (GdUnit4) | MIT | inspirace pro hlídače |

## Tipy pro Adreno a GLES3
- `highp` pro UV v shaderu zdiva, aby se daleko od počátku nepřeskakovalo (NEOVĚŘENO).
- Kompilace shaderů v Compatibility na Androidu je pomalá (godot#86731). Předehřívání shaderů už máme (predehrati.gd).

## Plán (Míša 9. 11.: „souhlasím, ale tři je málo“) – po dokončení seznamu chyb, každý krok měřit na tabletu
**Světlo a vzhled**
1. Zapečené světlo a AO v Cycles do lightmapy (UV2 z xatlas) – hrady, místnosti; nahradí vertex AO.
2. Atlas textur hradu (xatlas) – méně materiálů a vzorkovačů (limit Adreno 13).
3. `highp` UV ve shaderech zdiva a terénu – kontrola přesnosti na Adreno (skákání textur daleko od počátku).

**Méně kreslení a dat**
4. gltfpack a glTF-Transform za exportem – dedup, prune, zmenšení textur, vzdálené LOD automaticky.
5. Slučování dílů hradu po chuncích podle materiálu (vzor V-Sekai splerger) – méně draw callů.
6. Impostory lesu (hdrsniped po ověření licence, jinak MIT shader zhangjt93) + MultiMesh po dlaždicích – úkol les p95.
7. Tráva a keře u hradu přes MultiMesh po chuncích (vzor ProtonScatter).
8. Occlusion culling jako Havran: zakrývací plochy z terénu (kopce, hřbet mezi hrady) a ze zdí hradů – bez nich ořez nic nedělá; měřit variantou měřicí trasy (Havran to zatím neměřil).

**Terén a načítání**
9. HTerrain jako vzor chunk LOD a clipmap pro vzdálený terén (test v Compatibility).
10. Předehřívání shaderů podle godot#86731 – měřit záseky při prvním pohledu.

**Hlídači a postup**
11. Headless testy Godotu (vzor GdUnit4 / godot-mcp) – rozšířit hlídače o testy skriptů a scén.
12. Vytěžit návody z arjun988/blender-skills (LOD, collision-proxy, asset-optimization, godot-export) do našich pravidel – jen čtení.
