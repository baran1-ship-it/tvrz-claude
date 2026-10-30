# A/B srovnání: Godot 4.4.1 × Godot 4.7.2 × Terrain3D (29. 10. 2026)

Míša: „udělej to srovnání výseku obou verzí Godotu a Terrainu“. Tři APK se **stejným obsahem** (výsek 2×2 km, les
60 tis. stromů s LOD, tráva u hráče, návrh hradu 1, obzor), liší se jen tím, co se srovnává:

| APK | engine | terén | balíček (instalují se vedle sebe) |
|---|---|---|---|
| A | Godot 4.4.1 (jako Havran) | naše dlaždice z výšek (ve vláknech při startu) | cz.puchart.ab.a441 |
| B | Godot 4.7.2 | totéž jako A | cz.puchart.ab.b472 |
| C | Godot 4.4.1 + Terrain3D 1.0.2 | Terrain3D (clipmap s geomorfingem), data upečená předem | cz.puchart.ab.c_t3d |

Rozdíl C: povrch je jen auto shader Terrain3D (opad + skála podle sklonu), ne naše maska stanovišť – vzhled jiný,
výkon srovnatelný. Kolize ve všech třech stejná (naše HeightMapShape3D kolem hráče).

## Stažení (debug podpis, instalují se vedle sebe, Havrana nepřepíšou)
- A 4.4.1 (82,5 MB): https://github.com/baran1-ship-it/tvrz-claude/raw/ccr-f2d32673-9fi7m5/puchart/apk/puchart_A_441.apk
- B 4.7.2 (83,5 MB): https://github.com/baran1-ship-it/tvrz-claude/raw/ccr-f2d32673-9fi7m5/puchart/apk/puchart_B_472.apk
- C Terrain3D (98,0 MB): https://github.com/baran1-ship-it/tvrz-claude/raw/ccr-f2d32673-9fi7m5/puchart/apk/puchart_C_terrain3d.apk

Rozdíl obsahu: C má obzor jednoduchým materiálem a povrch auto shaderem Terrain3D (limit 100 MB); hrad ve všech třech
bez auto-LOD (celý návrh 1, 380 tis. troj.) – v měření „vyhlídka“ je proto hrad dražší, než bude ve hře (dálková verze hradu
`*_daleko.glb` je ve staviteli, zatím nevyexportovaná a do A/B záměrně nezapojená, aby byly varianty stejné).

## Jak měřit
1. Nainstalovat APK (debug podpis; nic nepřepíše Havrana ani sebe navzájem).
2. Spustit, nic nedělat: kamera sama proletí **hrad → les → údolí Veličky → vyhlídka**, každý úsek 5 s zahřátí + 30 s.
3. Na konci je na obrazovce tabulka (p50, p95, max ms, záseky > 40 ms, kreslení, troj., VRAM, halda) – **vyfotit**.
   Totéž se uloží do `user://mereni.txt`.
4. Každé APK pustit 2× (poprvé se předkompilují shadery), brát druhý běh. Tablet nechat 2 min vychladnout mezi běhy.

## Co je změřeno na PC (llvmpipe, jen orientačně – rozhoduje tablet)
- A: terén postaven za 2,7 s (64 dlaždic ve vláknech), snímek z dronu 280 kreslení / 1,6 M troj. (plné stromy do 110 m pro snímek).
- B: projekt 4.4 otevřen ve 4.7.2 bez úprav kódu, terén 2,6 s.
- C: Terrain3D se načte za 0,5–1,0 s.
Výkon na PC (software render) nic neříká o tabletu – NEOVERENO.

## Velikost APK (limit GitHubu 100 MB na soubor)
První export A měl 368 MB. Příčiny a opravy (platí pro všechny tři varianty stejně):
| příčina | MB | oprava |
|---|---|---|
| každá velikost stromu nesla vlastní kopii textury | 185 | sdílené textury (`stromy_sdilene_textury.py`), listí/kůra 512, karty 256, normály 256 |
| hotové sítě dlaždic terénu | 78 | terén z výšek ve vláknech při startu |
| hrad: mapy drsnosti, textury 1k, auto-LOD a stínové sítě | 40 | bez drsnosti, 512 px, bez auto-LOD |
| staré stromy LOD0 (25–30 k troj.) | ~8 | zblízka LOD1 (i výkon) |
| výšky r16 8 MB nekomprimované | 3 | roviny bajtů + zstd (4,7 MB) |

## Výsledky z tabletu (Míša, Xiaomi Pad 8, 30. 10. 2026 ráno, 2 běhy každé APK)
p95 v ms (běh 1 / běh 2), záseky = snímky nad 40 ms za 30 s úseku:
| | hrad | les | voda | vyhlídka | záseky les | kreslení les | troj. les | VRAM | halda |
|---|---|---|---|---|---|---|---|---|---|
| A 4.4.1 | 18,4 / 19,2 | 54,7 / 57,0 | 22,9 / 23,7 | 44,9 / 46,8 | 451 / 452 | 369 | 2,96 M | 209–210 MB | 405–411 MB |
| B 4.7.2 | 19,0 / 18,9 | 56,2 / 56,9 | 23,8 / 26,0 | 45,8 / 49,5 | 454 / 448 | 361 | 2,89 M | 212–213 MB | **350–351 MB** |
| C Terrain3D | 20,5 / 23,6 | 78,0 / 90,7 | 54,1 / 57,3 | 84,5 / 84,8 | 439 / 418 | 462 | 3,1 M | 264–265 MB | 488–493 MB |

## Rozhodnutí
- **Terrain3D ne:** ve všech úsecích výrazně horší (voda 2,4×, les 1,5×, +55 MB VRAM, +80 MB haldy), +100 kreslení.
  Přínos (editor, švy) nevyváží výkon na tabletu. Zůstává náš terén z výšek.
- **Godot 4.7.2 ano** (Míša: „B nejstabilnější“): výkon jako 4.4.1 v rámci šumu, **halda o 60 MB menší** (350 vs. 410).
  Puchart přechází na 4.7.2 (Havran zůstává na 4.4.1).
- **Brzda je les:** hrad 60 FPS (p95 19 ms), voda 23 ms; les p95 ~56 ms a vyhlídka ~46 ms – nad cílem 40 ms.
  Les v pohledu 2,9–3 M troj. a ~365 kreslení → další krok: impostory stromů, kratší dosah LOD1, méně vrstev listí.

## D – Godot 4.7.2 + impostory + hrad 6 (tablet 30. 10. 07:33)
| hrad | les | voda | vyhlídka |
|---|---|---|---|
| p95 11,7 ms (dřív 19) | **44,8 ms** (dřív 56) | 21,7 | **35,9** (dřív 46) |
Vyhlídka splňuje cíl 40 ms, les ještě o 5 ms nad (2,62 M troj., 429 kreslení – plné stromy blízko). Hrad 85 FPS.
