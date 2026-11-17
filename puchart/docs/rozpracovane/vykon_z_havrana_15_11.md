# Výkon: co si vzít z Havranova rozboru GPU (15. 11.)

Zdroj: Havran `docs/rozpracovane/rozbor_gpu_15_11.md` (větev claude/new-session-0dtk58), Míša 15. 11.: „Havran jede na grafiku,
možná se ti bude něco hodit“. Porovnání s Puchartem (kód 15. 11.):

| Havran zjištění | Puchart | Akce |
|---|---|---|
| Terén jedna obří síť na pásmo, bez LOD (547 tis. troj. stále) | **už dlaždice + LOD** (`scripts/svet.gd` _lod, visibility_range) | nic – ověřit jen počet troj. terénu v panelu |
| Uvnitř krčmy se kreslí celý venkovní svět (1,2–1,6 M prim.) | **totéž** – vnitřky mají jen `vnitrek_do_m`, venkovní svět (les, louka, terén, hrad) se uvnitř kreslí dál | **P1:** režim „uvnitř“ (hráč pod střechou celku/domu: zkrátit dohled louky/lesa/dálky, nebo okluzory zdí krčmy/hájovny/domů) – data `rozpocty.json uvnitr`, měřit snímkem v krčmě |
| Nové MultiMeshe při každé přestavbě buňky (alokace GPU bufferu dokola, špička 1,2 s) | `bunky_kolem.gd`, `byliny.gd`, `les.gd`, `louka.gd` dělají `MultiMesh.new()` za hry | **P2:** pevná zásoba MultiMeshů (kruh slotů), přestavba = přepis bufferu; ověřit na trase řádkem záseků |
| Diag čte buffer MultiMeshe z GPU (`get_instance_transform` na `mm.buffer`) = synchronizace CPU–GPU | Puchart diag to nedělá | nic |
| Plný panel stojí 7–11 ms | panel Puchartu také prochází strom? | **P3:** změřit cenu panelu (zapnutý/vypnutý), drahé části jen na požádání |
| „shadery +0“ v Compatibility nic nedokazuje (`get_pipeline_compilations` vždy 0) | platí i pro Puchart | do docs/kcd_grafika_tablet.md poznámka |
| Impostory obzoru v buňkách 1024 m bez visibility_range | Puchart les dálky – zkontrolovat buňky a `visibility_range_end` | **P4:** kontrola les.gd dálky |
| Stínová tělesa (`SHADOWS_ONLY`) panel počítá jako viditelná | Puchart má `_Daleko_Stin` u domů | panel: oddělit viditelné/stín (`get_render_info TYPE_VISIBLE/TYPE_SHADOW`) |

Pořadí: po dokončení funkcí a hlídačů, před vydáním APK měřit P1 a P3 (rychlé), P2 a P4 podle výsledku.

## Video Míši 16. 11. (LOD stromů a trávy) – co z toho pro Puchart
| Technika z videa | Puchart dnes | Akce po APK |
|---|---|---|
| Časované prolnutí LOD (timed fade 0,25 s místo pásma podle vzdálenosti – strom kreslen dvakrát jen chvíli) | stromy: doplňkový dithering v pásmu `prolinani_m` (10 m) – v pásmu běží oba stupně (discard), les.gd _fade | P2: časované prolnutí v shaderu (čas spuštění v INSTANCE_CUSTOM), změřit dvojí kreslení v pásmu, Havran to plánuje také |
| LOD0–LOD3 + impostor (2 troj.) | plný strom → jednoduchý tvar → impostor (atlas 8×8, Havran) | jen ověřit počty troj. stupňů |
| Tráva: dither maska do dálky | byliny i louka – rozpouštění ditheringem / zmenšení trsu podle hustoty(vzdálenost) | nic |
| Tráva z dálky: impostorové buňky (2 troj./buňka místo karet) | louka jen v okruhu buněk, dál barva terénu | P3: zvážit „travní impostor“ pásmo, pokud dálka louky vypadá holá |
| Záseky Havrana (bohatší příroda) | Puchart P2 výše: zásoba MultiMeshů, plánovač | měřit trasou na tabletu |

## Stav 17. 11. (bod 1b plánu po APK)
- **P2 hotovo:** `hra/scripts/zasoba_mm.gd` (rozpocty.json `zasoba_mm`) – louka, byliny, keře, les zblízka, kameny koryt,
  rostliny skal a drobnosti vsi berou MultiMesh ze zásoby; přestavba = přepis bufferu stejné velikosti (`glBufferData` bez
  `glGenBuffers`), slot znovu až po 3 snímcích. Zdroj Godot 4.7.2 gles3 `mesh_storage.cpp`: změna sítě u MultiMeshe
  s nahraným bufferem čte buffer z GPU → klíč zásoby obsahuje síť. Havran K5 zatím jen v plánu – tady první.
- **Časované prolnutí stromů hotovo** (bez kopie obrazovky, bez vzorkovače navíc): shader porovná vzdálenost stromu teď
  a před `cas_s` (uniform `kamera_pred`) → bez stavu na strom; `stromy_modely.json lod_casove`, A/B `PUCHART_LOD_PASMO=1`.
- **Měření PC** (llvmpipe, 1200×750 = 75 %, stejná trasa, A = vše vypnuto, B1 = P2 + časovaný LOD, B = + houštiny):

| úsek | A p50/p95 | B1 p50/p95 | B p50/p95 | A/B1/B >2×p50 | troj M A/B |
|---|---|---|---|---|---|
| hrad | 248/312 | 210/242 | 218/255 | 0/0/0 | 1,82/1,83 |
| les | 485/1145 | 335/548 | 381/565 | 30/0/0 | 1,36/1,47 |
| voda | 265/323 | 187/226 | 194/262 | 0/0/0 | 1,06/1,10 |
| vyhlídka | 239/341 | 151/209 | 170/225 | 0/0/0 | 0,89/0,93 |
| les znovu | 353/719 | 334/554 | 381/579 | 15/0/0 | 1,33/1,45 |

  Alokací MultiMeshů za trasu: A 20 257 → B 9 257 nových + 12 247 znovu (volných na konci 442, VRAM +8 MB).
  Pozor: llvmpipe kreslí na CPU (každý snímek > 40 ms), rozptyl mezi běhy velký (výchozí běh téže verze les p50 341,
  p95 736) – směr ano, čísla pro tablet NEOVERENO. Záseky tabletu změří Míša (řádek „zásoba MM“ a sloupec >2×p50 v měření).
