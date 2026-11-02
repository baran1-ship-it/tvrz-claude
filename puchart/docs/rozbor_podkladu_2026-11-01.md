# Rozbor podkladů Míši z 1. 11. 2026

Podklady: tři PDF (kompletní manuál, technický dodatek v1.1, hloubkový výzkum se 100 zdroji) a snímky rozhovoru
s ChatGPT (knihovny modelů, modelový filtr, sektory viditelnosti, okluze, vize KCD2 + Medieval Dynasty + Bellwright,
pluginy). Každé tvrzení, které šlo ověřit v kódu, je ověřené (sloupec „ověřeno“).

## Hned použito (2. 11.)
| poznatek | ověřeno | co se udělalo |
|---|---|---|
| Hrany dlaždic: `D / krok` celočíselně → při 250 m a kroku 16 m končí dlaždice na 240 m, 10 m pruh bez povrchu (výzkum kap. 10) | ano, `svet.gd` | `ceil(D / krok)` a poslední vzorek přesně na D (`svet.gd`, `teren_dlazdice.py`) – pravděpodobná příčina chyby #2 (světlé čáry na svazích) |
| `canvas_items` 1600×1000 neomezuje 3D, tablet kreslí 3D v plném rozlišení displeje (kap. 24) | ano, `project.godot` | `rozpocty.json` obraz_3d, tlačítko „Obraz 3D“ v procházce (100/75/60 %), měřicí APK měří trasu při 100 % a 70 % |
| Diagnostika: rozlišit délku snímku a čas GPU/CPU, skutečné pixely, paměť debug jako N/A, identita sestavy (kap. 25) | ano, `diag.gd` | panel: okno, 3D %, px, GPU/CPU ms (`viewport_set_measure_render_time`), halda(debug) nebo N/A, commit sestavy (`data/sestava.json` z exportu) |
| Výkop sklepa ze společné geometrie s budovou, bez trávy v interiéru (manuál P0) | ano | už hotovo 30. 10. (`hrad_geom.py`, jámy, byliny) |
| Test průchodu nestačí jako důkaz geometrie; každá opravená chyba = regresní test (dodatek kap. 3) | – | pravidlo do CLAUDE.md; test průchodu zůstává povinný před APK |

## Použitelné jako další kroky (pořadí podle přínosu)
1. **Obytné místnosti v paláci** (výzkum kap. 15, 30.3): palác je dnes plný kvádr kolize. Rozdělit na stěny, podlahy,
   otvory, schodiště; jeden palác jako vzorek. Navazuje na sklep pod ním.
2. **Měření na tabletu podle nové APK**: srovnání 100 % / 70 % rozhodne, zda nás brzdí pixely (les, alfa listí)
   nebo CPU/draw cally. Podle toho výchozí obraz_3d a další optimalizace lesu.
3. **Profil startu** (kap. 11, 30.4): terén se staví celý při startu (všechny dlaždice a LOD) – změřit fáze
   (výšky, sítě, vložení, vegetace) a teprve pak řešit postupné načítání.
4. **Modelový filtr a katalog** (snímky): licence + historická vhodnost → měřítko/orientace → materiály → LOD + kolize →
   interakční třída → test ve stejném světle → zápis do katalogu. „Jeden kvalitní model na konstrukční typ.“ Knihovny:
   Poly Haven (CC0), BlenderKit (podle assetu), Smithsonian 3D (CC0 výběr), 3D Valley, Fab/itch/CGTrader (ověřit licenci).
5. **Kontroly vztahů** (manuál, dodatek kap. 3): most–brána–cesta, schody–podesta, dveře–otvor, sklep–výkop–vegetace,
   ochoz–zábradlí, hradba–střílna jako levné geometrické testy vedle testu průchodu.
6. **Voda a podrost** (manuál P1): koryto podle reliéfu, klesající hladina, brody; podrost podle biotopů a světla;
   chybějící druhy javor, jasan, habr, jilm.
7. **Sektory viditelnosti a hlídač průhledů** (snímky): offline výpočet viditelnosti z cest nad DMR, označit drahá
   místa; zachovat klíčové výhledy (první pohled na Puchart z příjezdu). Okluze: Godot nepeče okludery z MultiMesh
   ani průhledných materiálů – pro les nepomůže, pro zdi/hřbety ano (jen pokus s měřením).
8. **Živý svět Havrana** (manuál P2, výzkum kap. 18–21): rozhraní Interactable/SaveState, trvalé NPC jako data,
   dveře se stavem a navigací – až po funkčním paláci.

## Opravy nepřesností v podkladech
- Výzkum na několika místech uvádí Godot 4.4.1 – projekt běží na **4.7.2** (A/B test 30. 10.); upraveno i v CLAUDE.md.
- „Palácový helper má plnou kolizi“ – platí pro palác (obytné místnosti chybí); věže a sklep jsou průchozí (test 10 tras).
- „Tablet jen načítá hotové meshe“ – správně: výšky jsou předpečené, sítě terénu se staví za běhu (cena startu).

## Nepoužito / odloženo
Přechod na jiný engine nebo Terrain3D bez konkrétního měřeného problému; PC efekty (SSAO, SSR, volumetrika);
HLOD a fotogrammetrie (P3) až po měření; procentní sliby výkonu bez srovnatelné APK.
