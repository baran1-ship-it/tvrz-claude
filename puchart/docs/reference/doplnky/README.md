# Doplňky pro Godot a Blender – rešerše a test (13. 11.)

Míša 13. 11.: „udělej rešerši doplňků a otestuj je“. Testováno v **samostatném** projektu ve scratchpadu
(`…/scratchpad/doplnky/godot`, Godot **4.7.2** `/opt/godot47`, renderer **gl_compatibility**, bez MSAA) a v Blenderu
jako modulu (`/opt/bl/bin/python`, **bpy 4.2.0**, bez GUI). V `puchart/hra` se nic neměnilo, nic se nenasadilo.

**Jak číst čísla:** Godot snímky běží v xvfb na **llvmpipe (software render na CPU, 640×400)**; CPU navíc sdílel jiný
běžící Godot. Čas snímku je proto **jen poměrový mezi variantami téže scény** – o tabletu (Adreno) neříká nic
→ výkon na tabletu je u všech doplňků **NEOVERENO**. Počet kreslení a primitiv je spolehlivý (nezávisí na GPU).
Testovací scéna: rovina 300 m, slunce se stíny 40 m, kamera 6 m nad zemí. Prázdná scéna: **5 kreslení, 32–37 ms**.

## Tabulka

| doplněk | k čemu | licence | Godot 4.7 Compatibility / Blender headless | otestováno | doporučení |
|---|---|---|---|---|---|
| **Moveset Free** 1.3.9 (Blender ext.) | 55 procedurálních animací (chůze, stání…) na humanoidní rig | kód GPL-3; obsah CC BY 4.0, vytvořené animace bez povinného uvedení (LICENSE-content.txt) | bpy ano – operátory `gait.create`, `gait.bake` | **ano**: na rigu MPFB (mixamo) upeklo `idle_normal` (191 sn.) a `walk_normal` (23 sn.) za 0,31 s; GLB s animacemi se v Godotu načte | **bere pro krok F** – animace postav skriptem, bez ručního klíčování |
| **MPFB** 2.0.18 (MakeHuman pro Blender) | generátor realistických lidí, rigy (default, game_engine, mixamo…) | GPL-3 (kód); assety (oblečení, kůže) zvlášť – licence NEOVERENO | bpy ano – `HumanService.create_human()`, `add_builtin_rig()` | **ano**: člověk 0,8 s, 26 756 troj. (s maskou pomocné sítě), rig mixamo 52 kostí; GLB 4,8 MB → Godot: 52 kostí, 2 animace, **36 972 troj.** (pomocné sítě se exportovaly – nutné `export_apply`); oblečení/vlasy nezkoušeno (stahují se zvlášť) | **zvážit pro krok F** – „realističtěji než Quaternius“; chybí ověřit oblečení 1393, LOD a cenu na tabletu |
| **Rigify** (vestavěný v Blenderu 4.2) | automatický rig postavy | GPL-2+ | bpy ano | **ano**: metarig + generate 5,0–6,7 s, 706 kostí, z toho 160 DEF | **zvážit** – pro hru exportovat jen DEF kosti; pro MPFB+Moveset stačí rig mixamo (52 kostí) |
| **Beehave** 2.9.x | stromy chování NPC (GDScript) | MIT | Godot 4.7 ano, čistý GDScript, žádné shadery | **ano** (headless): 200 NPC chodících mezi body – tick všech **1,22 ms**, 1000 NPC 6,3 ms (CPU PC, ~6 µs/NPC); bez editoru sype hlášky „No active debugger“ (autoload BeehaveGlobalDebugger vynechat) | **bere** pro chování NPC (krok E/F) |
| **LimboAI** 1.8.x | stromy chování + stavové automaty (C++ GDExtension) | MIT | podle stránky releases build pro Godot 4.7.2; Android NEOVERENO | **ne** – binárky z GitHub releases proxy zablokovala (403), stavět ze zdroje jsem nezkoušel | **zvážit** jako rychlejší alternativa k Beehave, až ověříme arm64 build |
| **Dialogue Manager 3** (main = 4.2.0) | dialogy ve skriptovém textu, volby, podmínky | MIT | Godot 4.7 ano (runtime); editorová část hlásí chybu shaderu jen v editoru | **ano**: český rozhovor s volbami se zparsuje za 1 ms, `get_next_dialogue_line` vrací repliky i volby | **bere** pro dialogy (text v souborech = data, ne kód) |
| **Dialogic 2** | dialogy s vizuálním editorem | MIT | 2.0 **alfa 20**, podle releases max. Godot 4.6.x | ne | **nebere** – alfa, 4.7 neuvádí |
| **Godot State Charts** 0.22.5 | stavové diagramy (NPC, dveře, denní režim) | MIT | Godot 4.7 ano, GDScript | **ano**: stav Práce → událost „vecer“ → Spánek funguje | **zvážit** (doplněk k Beehave pro denní režim vesničanů) |
| **Phantom Camera** 0.11 | chytrá kamera (sledování, přechody, otřesy) | MIT | Godot 4.7 ano, GDScript | **ano** (headless): sledování cíle funguje; editorová ikona hlásí chybu importu | **zvážit později** (průlety, scény) – teď nepotřebujeme |
| **ProtonScatter** 4.2 | rozmisťování objektů (vegetace, kameny) | MIT | Compatibility ano: výstup MultiMesh; modifikátor Relax má výpočetní shader, ale bez RenderingDevice sám přepne na CPU (relax.gd) | **ano**: 100 stromů → **49 MultiMesh uzlů (bloky 15 m), 157 kreslení** proti **15** u našeho jednoho MultiMeshe se stejnými stromy; stavba 334 ms; *Project on geometry* + vlákno v našem skriptu **zamrzlo**, bez vlákna 21 ms | **nebere** – sázení už pečeme sami (byliny.gd, stavby_vegetace.py) s menším počtem kreslení; nanejvýš vzor modifikátorů |
| **Spatial Gardener** 1.4.1 | malování vegetace štětcem v editoru | MIT | **v Godotu 4.7 se nenačte**: „The member "Logger" shadows a native class“ (Godot má od 4.5 vlastní třídu Logger) | ano – selže už při importu | **nebere** (rozbité, a je jen pro ruční malování v editoru) |
| **Simple Grass Textured** 2.1.1 | tráva jako MultiMesh, vítr, interakce s hráčem | MIT | vykreslí se v Compatibility; interakce = singleton se **7 SubViewporty** a shaderem s `hint_depth_texture`; globální shader parametry registruje jen editorový plugin; sázení jen štětcem v editoru | **ano**: 20 000 trsů → **8 kreslení**, 240 tis. primitiv, VRAM +19 MB, 681 ms na llvmpipe (alfa výřez) | **nebere** – trávu máme; 7 viewportů a čtení hloubky jsou proti pravidlům tabletu |
| **Sky3D** 2.2-dev (main) | den/noc, slunce, měsíc, hvězdy, mraky, mlha | MIT | Compatibility podporuje (README), ale mlha `AtmFog` čte **`hint_depth_texture`** – porušuje pravidlo „žádné čtení obrazovky/hloubky“ (dá se vypnout `fog_enabled=false`) | **ano**: stejná scéna se stromem **362–395 ms** (s mlhou 374, bez 362, večer 395) proti **40,6 ms** s naší `sky.gdshader` (13–14 kreslení v obou) | **nebere** – ~9× dražší než naše obloha z Havrana; mlha s hloubkou zakázaná |
| **Octahedral Impostor LOD** 1.0.0 | octahedral impostory, pečení z příkazové řádky, spojování do MultiMesh | v repu **žádná licence**, Asset Library uvádí „Proprietary“ | pečení CLI běží headless v Compatibility; shader 7 vzorkovačů, smyčky, zápis `DEPTH` | **ano**: 100 stromů upečeno za **7,7 s**; režim replace: primitivy **321 tis. → 268**, kreslení 223 → 134, ale čas 98 → **1125 ms** na llvmpipe (těžký fragment shader); režim dynamic_lod bez spojení 352 kreslení | **nebere** (licence; těžký shader na Adreno NEOVERENO) – vzor pro naše impostory (pečení z CLI, crossfade) |
| **godot-imposter** 1.3 | octahedral impostory | MIT | pečení jen v editoru (EditorPlugin, EditorInterface) | načte se; pečení headless nejde | **nebere** – impostory už máme z Havrana |
| **Terrain3D** 1.0.2 / 1.1.0 | terén clipmap, malování, instancer | MIT | dříve A/B na tabletu (docs/ab_srovnani.md) | dříve: voda 2,4× horší, les 1,5×, +55 MB VRAM, +100 kreslení | **nebere** (rozhodnuto 30. 10.) |
| **Waterways .NET** 1.0.1 | řeky z Bézierových křivek s flowmapou | MIT | jen C# (.NET 8) – náš export je GDScript | ne | **nebere**; řeky dál `blender/voda.py` + `voda.gdshader` |
| **Swell** (fórum Godotu) | vodní systém | – | podle autora jen Forward+ | ne | **nebere** |
| **Godot Jolt** | fyzika Jolt | MIT | **ve 4.7.2 vestavěný**: Project Settings `physics/3d/physics_engine` nabízí „Jolt Physics“ (ověřeno) | ano – volba existuje | doplněk nepotřebujeme; přepnout lze nastavením (měřit zvlášť) |
| **Godriver** 1.0 | E2E testy běžící hry (HTTP doplněk + Node 24 klient, snímky, vstupy) | MIT | GDScript doplněk | ne (jen přečten README) | **zvážit** pro hlídače (průchody, snímky) |
| **Godot Road Generator** 0.9.5 | silnice po křivkách | MIT | NEOVERENO | ne | **nebere** – cesty pečeme `cesty.py` |
| **Sapling Tree Gen** 0.3.6 (Blender ext.) | parametrické stromy (9 předloh: osika, bříza, javor, vrba, douglaska…) | GPL-2+ | bpy ano (`curve.tree_add`, předlohu lze předat jako parametry) | **ano**: osika 5 556 troj. (rozlišení křivky 2), 0,01 s, GLB 195 kB → Godot MultiMesh OK | **zvážit** – jen pro druhy, které v Havranu chybí; vzhled bez textur kůry/listů slabší než naše stromy |
| **MTree** (modular_tree 4) | stromy z uzlů, C++ jádro | GPL-3 | binárky z releases nedostupné → **sestaveno ze zdroje** (Eigen 3.4 + pybind11, 13 s); doplněk sám používá `np.int`/`np.bool` → s numpy 2.4.6 v /opt/bl **spadne** | **ano (jen jádro)**: `m_tree` API v bpy funguje, strom 1 úroveň větví 7 458 troj. za 1 ms; výchozí 2 úrovně = 37 mil. troj. | **nebere** zatím – nutná oprava doplňku a vlastní listí |
| **Space colonization tree generator** 1.0.0 | kostra stromu z bodů koruny | GPL-3 | bpy ano | **ano**: 0,05–0,08 s, vznikne síť | **nebere** – jednoduchý, bez listí |
| **IvyGen** 0.1.5 | břečťan po síti (zdi) | GPL-2+ | bpy ano (`curve.ivy_gen(updateIvy=True)`) | **ano**: 8 m po zdi za 3 s = **4,4 mil. troj.** větví (křivka) + 375 tis. listů | **zvážit** pro zarostlé zdi – jen po decimaci/převodu na karty |
| **A.N.T. Landscape** 0.2.0 | generovaný terén, eroze | GPL-2+ | bpy ano (`mesh.landscape_add`, `mesh.eroder`) | **ano**: 128² 32 tis. troj. 0,06 s, eroze 5 iterací 0,46 s | **nebere** – terén máme z DMR 5G |
| **Scatter Objects** 0.2.0 | rozmístění tahem myši | GPL-2+ | jen interaktivně (tah štětcem) | nainstalováno, funkce NEOVERENO | **nebere** |
| BlenderGIS, Instant Meshes, LODify, Bagapie, Leaf Gen, PlaceHelper | GIS import, retopologie, LOD, scatter, listy | různé | NEOVERENO | ne | GIS a LOD už řešíme vlastními nástroji (dmr_mrizka.py, gltfpack v plánu 9. 11.) |

Snímky: `godot_vlastni_multimesh.png` × `godot_protonscatter.png` (100 stromů Sapling, bez materiálu),
`godot_simplegrass.png`, `godot_sky3d_poledne.png` / `godot_sky3d_vecer.png` × `godot_nase_nebe.png`,
`godot_octa_stromy.png` × `godot_octa_karty.png` (stromy za 30 m → karty), `blender_sapling_ivy_ant.png`
(koule s kostrou stromu, osika Sapling, terén A.N.T., břečťan na zdi), `blender_mpfb_moveset.png` (MPFB člověk v chůzi
z Moveset, snímek 12).

## Doporučení – pořadí nasazení (zatím nic nenasazeno)
1. **Dialogue Manager 3** (krok E) – rozhovory jako textové soubory v `hra/data/…`, hra jen čte. Malý, MIT, ověřený
   v 4.7. Zapojení: doplněk do `hra/addons`, autoload `DialogueManager`, vlastní UI bubliny (ne jejich ukázkové).
2. **Beehave** (krok E/F) – chování NPC (chůze po cestách, práce, útěk), parametry v `pravidla/…json`. Měřit tick na
   tabletu na trase měření (cíl: desítky NPC pod 1 ms). Alternativa LimboAI po ověření arm64 buildu.
3. **MPFB + Moveset Free (+ Rigify)** v Blenderu (krok F) – nový nástroj `blender/postavy.py` (headless): člověk
   s parametry z dat → rig mixamo → animace Moveset → GLB s `export_apply`, LOD. Nejdřív ověřit oblečení a licenci
   assetů MPFB, počet trojúhelníků (dnes 27–37 tis. na postavu) a skinning na tabletu. Uvést „Moveset Free by NoMicro
   Studio“ v titulcích (CC BY pro obsah doplňku).
4. **Godot State Charts** – jen pokud Beehave nestačí na denní režim (den/noc z naší oblohy).
5. **IvyGen / Sapling** – jednorázově v Blenderu pro chybějící druhy nebo břečťan na zdech, výsledek přes náš modelový
   filtr (decimace, karty, impostor). Stromy z Havrana zůstávají hlavní.
6. **Godriver** – zvážit pro hlídače (vstup a snímky v běžící hře).
- **Nebrat:** Sky3D (9× dražší než naše obloha, mlha čte hloubku), ProtonScatter (10× víc kreslení než náš MultiMesh),
  Spatial Gardener (v 4.7 nefunguje), Simple Grass Textured (7 viewportů, editor), Octahedral Impostor LOD (licence),
  Terrain3D (A/B), Waterways .NET (C#), Dialogic (alfa), A.N.T. Landscape.

## Co nešlo ověřit
- Výkon čehokoli na Xiaomi Pad 8 (Adreno) – NEOVERENO; čísla výše jsou z llvmpipe.
- LimboAI – binárky z GitHub releases zablokované proxy (403). Stahovat šlo jen `git clone` a extensions.blender.org.
- MPFB oblečení, vlasy, kůže (zvláštní balíky assetů) a jejich licence – NEOVERENO.
- Scatter Objects, BlenderGIS, Instant Meshes, LODify a další ze spodního řádku – nezkoušeno.

## Postup testu (pro zopakování)
Skripty zůstaly ve scratchpadu `doplnky/skripty/` (bl_test.py, bl_postava.py, mtree_test.py, r.sh) a
`doplnky/godot/test/beh.gd` (testy: prazdna, multimesh, scatter, trava, sky3d*, nase_nebe, octa_*, beehave, dialog,
pcam, statechart). Doplňky se stáhly `git clone --depth 1` (GitHub) a z extensions.blender.org; po testu smazány.
Zdroje: godotengine.org/asset-library (API), extensions.blender.org (API), github.com (README, LICENSE),
github.com/limbonaut/limboai/releases, github.com/dialogic-godot/dialogic/releases,
forum.godotengine.org (Swell).
