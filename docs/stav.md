# Stav projektu – Odkaz Havrana (16. 10. 2026, verze 0.42)

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
