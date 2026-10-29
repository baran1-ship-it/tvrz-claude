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

## Výsledky z tabletu (doplní Míša)
| | hrad p95 | les p95 | voda p95 | vyhlídka p95 | záseky | VRAM | halda | dojem |
|---|---|---|---|---|---|---|---|---|
| A 4.4.1 | | | | | | | | |
| B 4.7.2 | | | | | | | | |
| C Terrain3D | | | | | | | | |
