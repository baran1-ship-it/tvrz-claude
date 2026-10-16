# Stav projektu – Odkaz Havrana (16. 10. 2026, verze 0.44)

## Rozpočet (Android, Xiaomi Pad 8 / Adreno 825)
- Volání kreslení: max 1500 / snímek
- Trojúhelníky: cíl 2 M / snímek, tolerance do 2,75 M, pokud FPS drží 30+
- Paměť GPU: pod 700 MB (monitor ukazuje zvlášť textury a buffery)
- Hlídání: diag.gd loguje každé 2 s do user://diag.log, varování při 1,5× rozpočtu (s pozicí hráče) do user://diag_varovani.log, panel „Měření výkonu“ v nastavení
- Skály: LOD0 ≤ 3000 troj. (0–40 m, se stínem), LOD1 ~800 (40–120 m), LOD2 ~150 (120–500 m)
- Stromy: plný model do 60 m (stín), zjednodušený tvar 55–120 m bez stínu, za 120 m nic
- Stíny: 2 kaskády, atlas 2048, vegetace (mimo stromy a skály LOD0) bez stínů
- Louka: max 3–4 volání na buňku (32 m); střední pásmo do 100 m, 1,2 trsu/m²
- Drobná vegetace: nízká 22/32/45 m, střední 50/70/95 m (podle kvality)
- Předměty: dosah podle velikosti 20 / 40 / 80 m, drobné (<0,5 m) bez stínu
- Textury: terén a modely 1024, vegetace 512, stromy a skály 1024; vše VRAM komprese + mipmapy (tools/limity_textur.py, spouští vydani.py)
- Prah LOD sítí: rendering/mesh_lod/lod_change/threshold_pixels = 4

## Měření na PC (Compatibility, kvalita 1, 800×500) – vodítko, ne důkaz

| Místo | Kreslení | Troj. | GPU |
|---|---|---|---|
| tvrz nádvoří | 764 | 1,65 M | 444 MB |
| louka u tvrze | 788 | 1,91 M | 444 MB |
| hostinec ke skalám | 979 | 2,63 M | 443 MB |
| skalní město | 981 | 2,73 M | 445 MB |
| vesnice | 813 | 2,02 M | 443 MB |
| potok u mostu | 616 | 1,84 M | 444 MB |

Textury 306 MB, buffery 137 MB. Před zahájením stabilizace: 15–20 M troj., 7500 volání, 1235 MB na tabletu.

Měření: `TVRZ_MERENI="nazev;x,z,tx,tz|..."` (viz main.gd), rozpad po částech `TVRZ_ROZPAD=1`.

## Co se změnilo v kole stabilizace
- Skály LOD0/1/2 podle rozpočtu, borovice na skalách zvlášť
- Stromy: dohled 120 m, zjednodušené tvary
- Louka: sloučené vrstvy (custom data), květy v jednom atlasu, kupy trávy ve velkých buňkách, řidší střední pásmo
- Předměty: rozsah viditelnosti podle velikosti
- Limity textur + mipmapy, monitor paměti textur/bufferů
- Vulkan varianta: MSAA 2× od startu (pruhy), bez mipmap u screen textury (pád)
- Diagnostika pádů (zpráva po pádu, fáze načítání)

## Otevřené
- **Změřit 0.42 na tabletu** (5 míst, panel „Měření výkonu“). Drží 30+ FPS a nepadá → stabilizace hotová, jde se na krásu. Jinak řezat podle skutečných čísel.
- Další fáze: occlusion culling pro interiéry (nádobí a předměty za zdmi; u hostince Predmety ~1 M troj.)
- Chalupy LOD0 ≤ 4000 troj. (trámy a detaily do normálových map), pokud bude třeba
- Impostory pro stromy a skály
- Stíny do 60 m podle zadání (teď 60 m na kvalitě 1)
- Uzel „Zivot“ u hostince ~0,4 M troj. – neprozkoumáno
- Domy z Disku (house_farm_wood a další)
- Terrain3D, lightmapy – odloženo

## K1 – měření na PC (Compatibility, kvalita 1, 1200×800)

K1: terén z fotek Poly Haven ve skutečném měřítku (louka 2 m, letecký snímek 15 m do dálky, lesní hrabanka), bez procedurálního přebarvení; skály remesh+zapečení; rostliny posazené na terén.

| Místo | Kreslení | Troj. | GPU (textury / buffery) |
|---|---|---|---|
| tvrz nadvori | 722 | 1.66 M | 454 MB (316 / 137) |
| louka u tvrze | 768 | 1.73 M | 455 MB (316 / 138) |
| vesnice | 766 | 1.98 M | 454 MB (316 / 137) |
| skalni mesto | 977 | 2.61 M | 455 MB (316 / 139) |
| hostinec ke skalam | 1022 | 2.86 M | 454 MB (316 / 137) |
| potok u mostu | 606 | 1.83 M | 454 MB (316 / 138) |
| cesta zblizka | 730 | 2.16 M | 454 MB (316 / 137) |
| zed tvrze zblizka | 860 | 1.93 M | 454 MB (316 / 137) |

Snímky: docs/screens/K1_*.jpg

## K1c – měření na PC (Compatibility, kvalita 1, 1200×800)

K1c: světelný profil pro Compatibility (LDR: slunce ×0,38, obloha ×0,45, ACES white 1,6), výšková mlha od nejnižšího místa terénu, louka ambientCG Grass004/Grass001, pole z fotek (obilí, oranice), kalibrace odrazivosti fotek terénu.

| Místo | Kreslení | Troj. | GPU (textury / buffery) |
|---|---|---|---|
| tvrz nadvori | 722 | 1.66 M | 455 MB (317 / 137) |
| louka u tvrze | 768 | 1.73 M | 456 MB (317 / 138) |
| vesnice | 766 | 1.98 M | 455 MB (317 / 137) |
| skalni mesto | 436 | 1.81 M | 458 MB (317 / 140) |
| hostinec ke skalam | 1020 | 2.86 M | 455 MB (317 / 137) |
| potok u mostu | 606 | 1.83 M | 456 MB (317 / 138) |
| cesta zblizka | 730 | 2.16 M | 455 MB (317 / 137) |
| zed tvrze zblizka | 860 | 1.93 M | 455 MB (317 / 137) |

Snímky: docs/screens/K1c_*.jpg

## K2 – měření na PC (Compatibility, kvalita 1, 1200×800)

K2: tráva z karet s fotkami (atlas 1024×512, 6 trsů z Poly Haven), trs = 3 zkřížené karty (6 troj.), alpha scissor, normála nahoru z obou stran, pata ne černá; prolínání podle trsu místo středu buňky.

| Místo | Kreslení | Troj. | GPU (textury / buffery) |
|---|---|---|---|
| tvrz nadvori | 717 | 1.36 M | 457 MB (318 / 138) |
| louka u tvrze | 757 | 1.10 M | 458 MB (318 / 139) |
| vesnice | 758 | 1.33 M | 456 MB (318 / 138) |
| skalni mesto | 429 | 0.92 M | 459 MB (318 / 141) |
| hostinec ke skalam | 1010 | 2.32 M | 456 MB (318 / 138) |
| potok u mostu | 597 | 1.21 M | 457 MB (318 / 139) |
| cesta zblizka | 718 | 1.39 M | 457 MB (318 / 138) |
| zed tvrze zblizka | 857 | 1.64 M | 457 MB (318 / 138) |

Snímky: docs/screens/K2_*.jpg

## Známá omezení (Compatibility renderer)
- U MultiMesh je transformace instance už ve VERTEX, MODEL_MATRIX je jen uzel (střed 32m buňky louky) –
  vzdálenost pro prolínání se musí brát z polohy vrcholu, ne z MODEL_MATRIX (stebla i kvety.gdshader).
- Není HDR buffer: světlo nad 1 se ořízne před tonemapem → samostatný světelný profil (daylight.gd, `ldr`).

## K2b – měření na PC (Compatibility, kvalita 1, 1200×800)

K2b: střední pásmo louky hustší (DAL_HUST 2,0), hustší pás trávy na okraji lesa (maska hustoty), kvítí prolíná po celých květech; hostinec přes _import_sketchup.

| Místo | Kreslení | Troj. | GPU (textury / buffery) |
|---|---|---|---|
| tvrz nadvori | 718 | 1.44 M | 457 MB (316 / 140) |
| louka u tvrze | 760 | 1.12 M | 457 MB (316 / 140) |
| vesnice | 757 | 1.43 M | 456 MB (316 / 139) |
| skalni mesto | 429 | 0.96 M | 459 MB (316 / 142) |
| hostinec ke skalam | 1011 | 2.31 M | 456 MB (316 / 139) |
| potok u mostu | 597 | 1.28 M | 457 MB (316 / 140) |
| cesta zblizka | 721 | 1.50 M | 457 MB (316 / 140) |
| zed tvrze zblizka | 860 | 1.72 M | 456 MB (316 / 140) |

Snímky: docs/screens/K2b_*.jpg

## Vydání 0.44 (16. 10. 2026)
K1 (terén z fotek, světelný profil pro Compatibility, výšková mlha od dna terénu, kalibrace odrazivosti),
K2 + K2b (tráva z karet s fotkami, hustší střední pásmo a okraj lesa), skály remesh + zapečení, hostinec přes
_import_sketchup. Čísla viz sekce K2b. Další: K3 (vzdálený terén), K4 (zapečené AO), dávka Míšových modelů.
Pozastaveno do pondělí (limit účtu).

## K3 – impostory stromů (PC, Compatibility, kvalita 1)
| Místo | Kreslení | Troj. | GPU (textury / buffery) |
|---|---|---|---|
| louka u tvrze | 843 | 1.11 M | 485 MB (346 / 138) |
| vyhlídka u skal | 679 | 1.25 M | 487 MB (346 / 141) |

Snímky: docs/screens/K3_louka.jpg, K3_vyhled.jpg. Les až k obzoru (900 m), 9 339 impostorů po 2 troj.
