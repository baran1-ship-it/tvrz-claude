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

## Měření H (2. 11. 2026, Xiaomi Pad 8, Godot 4.7.2, sestava 62a8f47) – rozlišení 3D 100 % vs 70 %
| úsek | 100 % p50 / p95 / max | záseky | 70 % p50 / p95 / max | záseky | kreslení | troj M |
|---|---|---|---|---|---|---|
| hrad | 16,6 / 19,1 / 574 | 3 | 16,7 / 19,9 / 667 | 2 | 246 | 0,86–0,94 |
| les | 35,3 / **44,5** / 48 | 221 | 22,1 / 26,7 / 29 | 0 | 486 | 2,35 |
| voda | 17,4 / 21,7 / 58 | 10 | 16,6 / 19,9 / 38 | 0 | 282 | 0,70 |
| vyhlídka | 29,8 / 34,8 / 37 | 0 | 17,6 / 20,1 / 26 | 0 | 527 | 1,17 |
VRAM 227–252 MB. Závěr: les a vyhlídka jsou omezené **pixely** (průhledné listí, overdraw) – při 70 % klesne p95 lesa
44,5 → 26,7 ms; hrad a voda ne (≈ 17 ms = vsync 60 Hz / CPU). Max 574–667 ms u hradu = jednorázový zásek při startu úseku
(načítání), ne průběh. Skály výkon nezhoršily (hrad p95 19 ms, D: 11,7 ms – jiný obsah, nesrovnatelné 1:1).
Další krok výkonu: výchozí obraz 3D 0,75 a/nebo méně překrytých listových karet v lese, ne snižování trojúhelníků.

## Měření I – tablet, sestava 004e898 (2. 11. 13:16; popisek v APK ještě „H“)
| úsek | 3D px | p50 | p95 | max | záseky | troj M | VRAM |
|---|---|---|---|---|---|---|---|
| hrad 100 % | 1600×1000 | 16,6 | 18,7 | 173 | 3 | 0,88 | 216 |
| les 100 % | 1600×1000 | 32,5 | 42,4 | 964 | 130 | 2,02 | 216 |
| voda 100 % | 1600×1000 | 17,5 | 22,4 | 47 | 2 | 0,72 | 216 |
| výhlídka 100 % | 1600×1000 | 26,1 | 31,7 | 33 | 0 | 0,96 | 216 |
| hrad 70 % | 1120×700 | 16,7 | 19,5 | 172 | 3 | 0,96 | 240 |
| les 70 % | 1120×700 | 20,2 | 25,6 | 217 | 4 | 2,09 | 240 |
| voda 70 % | 1120×700 | 16,5 | 19,2 | 39 | 0 | 0,73 | 240 |
| výhlídka 70 % | 1120×700 | 16,8 | 19,1 | 29 | 0 | 0,97 | 240 |

Proti H (62a8f47): les p95 44,5 → 42,4 (100 %), 26,7 → 25,6 (70 %) i se 4 novými dřevinami a podrostem. Při výchozích 75 % je
vše pod 33,3 ms. Les ve 100 % zůstává pixelově vázaný; max 964 ms a 130 záseků jen v prvním průchodu (100 % se měří první) →
pravděpodobně kompilace shaderů / první načtení modelů nových dřevin, NEOVERENO. Další krok: předehřátí materiálů stromů
a podrostu při startu, oprava popisku měření.

## Měření K – tablet, sestava 24e074e (3. 11. 05:15; popisek „J“)
| úsek | 3D px | p50 | p95 | max | záseky | troj M | VRAM |
|---|---|---|---|---|---|---|---|
| hrad 100 % | 1600×1000 | 8,7 | 13,8 | 21 | 0 | 0,86 | 381 |
| les 100 % | 1600×1000 | 38,9 | 49,5 | 231 | 362 | 2,26 | 380 |
| voda 100 % | 1600×1000 | 21,6 | 39,5 | 50 | 60 | 0,99 | 381 |
| vyhlídka 100 % | 1600×1000 | 32,3 | 38,4 | 42 | 17 | 1,22 | 380 |
| hrad 70 % | 1120×700 | 8,3 | 10,2 | 21 | 0 | 0,94 | 352 |
| les 70 % | 1120×700 | 26,5 | 34,5 | 39 | 0 | 2,25 | 351 |
| voda 70 % | 1120×700 | 14,1 | 26,8 | 35 | 0 | 1,00 | 352 |
| vyhlídka 70 % | 1120×700 | 21,0 | 24,8 | 28 | 0 | 1,22 | 351 |

Proti J: hrad 2× rychlejší (dohled podle scén), velké záseky pryč (max les 231 ms při 1. průchodu 100 %), při 70 % vše pod 33 ms
kromě lesa p95 34,5. VRAM 380 MB (+164, impostory 2048 – odhad byl ~100). Les 100 % pixelově vázaný. Další krok: keře a zmlazení
(3. 11. zmenšeno), měření L.

## Měření – tablet, sestava 7f0ca2c, Game Turbo ZAPNUTÉ (Míša 10. 11. 09:29; popisek „J“)
| úsek | 3D px | p50 | p95 | max | záseky | kreslení | troj M | VRAM |
|---|---|---|---|---|---|---|---|---|
| hrad 100 % | 1600×1000 | 17,3 | 29,3 | 61 | 1 | 351 | 1,80 | 437 |
| les 100 % | 1600×1000 | 29,6 | 41,7 | 45 | 84 | 870 | 2,58 | 436 |
| voda 100 % | 1600×1000 | 19,5 | 36,4 | 45 | 35 | 685 | 1,61 | 437 |
| vyhlídka 100 % | 1600×1000 | 38,9 | 44,2 | 83 | 292 | 876 | 1,34 | 515 |
| hrad 70 % | 1120×700 | 17,0 | 22,5 | 27 | 0 | 375 | 1,89 | 489 |
| les 70 % | 1120×700 | 37,2 | 62,4 | 71 | 196 | 870 | 2,66 | 487 |
| voda 70 % | 1120×700 | 23,6 | 45,3 | 59 | 83 | 683 | 1,65 | 489 |
| vyhlídka 70 % | 1120×700 | 25,1 | 29,8 | 33 | 0 | 872 | 1,33 | 486 |
Les 70 % je POMALEJŠÍ než les 100 % (62 vs 42 ms p95) – druhý průchod běží zahřátý, tablet zpomaluje teplem i s Game Turbo.
Srovnání s měřením téže sestavy BEZ Game Turbo (Míša 9. 11. 12:21, snímek v konverzaci):
| úsek | p95 bez GT | p95 s GT | záseky bez / s GT |
|---|---|---|---|
| hrad 100 % | 29,0 | 29,3 | 0 / 1 |
| les 100 % | 94,7 | 41,7 | 477 / 84 |
| voda 100 % | 62,7 | 36,4 | 364 / 35 |
| vyhlídka 100 % | 46,0 (max 26 s!) | 44,2 (max 83 ms) | 446 / 292 |
| hrad 70 % | 21,0 | 22,5 | 0 / 0 |
| les 70 % | 61,0 | 62,4 | 131 / 196 |
| voda 70 % | 43,7 | 45,3 | 83 / 83 |
| vyhlídka 70 % | 31,6 | 29,8 | 0 / 0 |
Závěr: Game Turbo výrazně pomáhá v první polovině trasy (les 100 % p95 −53 ms, záseky 477 → 84, bez 26s zamrznutí). V druhé
polovině (tablet už zahřátý) je výsledek stejný – teplo pak brzdí stejně. Game Turbo tedy oddálí zpomalení, neodstraní ho.
→ do návodu k instalaci: přidat hru do Game Turbo (i Havran, stejný tablet). Teplo dál řešit ve hře (rozpočty, 30 FPS strop).
NEOVERENO: start obou běhů nemusel být ze stejně studeného tabletu.

## Měření – tablet, sestava 23bd811 (Míša 10. 11. 12:15; Game Turbo ZAPNUTÉ, start ze studeného tabletu, ohřeje se během chvilky)
| úsek | 3D px | p50 | p95 | max | záseky | kreslení | troj M | VRAM |
|---|---|---|---|---|---|---|---|---|
| hrad 100 % | 1600×1000 | 19,8 | 27,9 | 165 | 2 | 382 | 1,92 | 477 |
| les 100 % | 1600×1000 | 53,1 | 77,3 | 95 | 508 | 860 | 2,38 | 475 |
| voda 100 % | 1600×1000 | 37,6 | 60,7 | 71 | 324 | 717 | 1,45 | 477 |
| vyhlídka 100 % | 1600×1000 | 36,3 | 41,3 | 48 | 95 | 863 | 1,20 | 474 |
| hrad 70 % | 1120×700 | 16,8 | 17,8 | 33 | 0 | 403 | 2,01 | 448 |
| les 70 % | 1120×700 | 34,7 | 56,6 | 70 | 132 | 860 | 2,37 | 446 |
| voda 70 % | 1120×700 | 23,9 | 45,9 | 56 | 82 | 718 | 1,45 | 448 |
| vyhlídka 70 % | 1120×700 | 23,0 | 27,4 | 30 | 0 | 863 | 1,20 | 445 |
Les 100 % p95 77 ms: mezi 7f0ca2c bez GT (94,7) a s GT (41,7). Kreslení a trojúhelníky lesa nižší než u 7f0ca2c → rozdíl
spíš teplo/režim než obsah (skály a rostliny jsou u hradů, ne v lese). Míša: start studený, s Game Turbo, tablet se ohřeje za chvilku. Proti 7f0ca2c s GT (09:29): první polovina (100 %) horší (les 41,7 → 77,3), druhá zahřátá polovina stejná nebo lepší (hrad 70 % 22,5 → 17,8, les 70 % 62,4 → 56,6, vyhlídka 29,8 → 27,4). Obsah lesa se nezměnil (kreslení 870 → 860, troj 2,58 → 2,38). → rozptyl první poloviny (kdy a jak dlouho GT drží boost) je větší než rozdíl verzí; jediná nová věc s vlivem na les: anizotropní filtrování (mobil 2) zavedené s mipmapami – NEOVERENO, A/B v příští měřicí APK.

## A/B na PC (10. 11., softwarové kreslení 800×500 okno, trasa měření) – jádro korun + stín z elipsoidu (12ad855)
| úsek | p95 bez | p95 s | troj M bez → s |
|---|---|---|---|
| les 100 % | 846 | 371 | 2,19 → 1,40 |
| les 70 % | 790 | 340 | 2,19 → 1,40 |
| voda 100 % | 432 | 292 | 1,22 → 1,14 |
| vyhlídka 100 % | 283 | 241 | 1,12 → 0,95 |
| hrad 100 % | 283 | 290 | 1,90 → 1,90 |
Les −56 %: stínový průchod už nekreslí listí (−0,8 M troj.) a vnitřek korun bez discard. Absolutní ms z PC neplatí pro tablet, poměr ano – ověřit na tabletu.
