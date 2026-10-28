# Plán k 1.0 (stavitel 28. 10. večer, Míša: „můžeš připravovat 100?“)

**1.0 = brána, ne datum.** Vydání 1.0 až když platí všechno najednou, k jednomu otisku exportu:
1. Matice vztahů: pokrytí 100 % a úspěšnost 100 % (`tools/kontrola_vztahu.py --vydani`), bez povolení nad rámec.
2. Test smyslu, meze kroků stavby, `zasazeni`, `voda_v_korytu`, `breh_hladky`, `site_natazene` beze chyby.
3. Snímky 01–20 vedle referencí (estetika) prohlédnuté rádcem a Míšou.
4. Výkon za celý záběr a okruh: `mapa_vyhledu` a `pamet_okruh` v rozpočtu tabletu; sekání změřené testem záseků bez
   variant nad mez.
5. Tabulka chyb Míši: každý řádek opravený s kontrolou v testu (`tools/kontrola_tabulek.py`).

## Pořadí
| # | Úkol | Proč | Stav |
|---|---|---|---|
| 1 | 0.99: export s mlýnem na přítoku, větrným mlýnem, cestami ≤ 12,5 % → testy → vydání | Míša chce svět vidět | běží |
| 2 | Chyby z testů 0.99: suché koryto (28 bodů), zubatý břeh a schody, natažené sítě (36), zasazení (ulice napříč, pěšina) | brána 2 | |
| 3 | Ruce: otěže v záběru, louč svisle (`telo_zaber`) | Míša „animace rukou žádná“ | rozpracováno |
| 4 | Sekání ve vsi (FPS 18–25): zpráva z testu záseků z tabletu → příčina → oprava | brána 4 | čeká zprávu |
| 5 | Tabulka 0.98: most (cesta pod ním), příkop, černá vrata, bílý rybník u tvrze, dům 7 | brána 5 | |
| 6 | Hodnoty z rešerše KCD2 (odstupy cest a stromů, břehové stromy, přechodová pásma) změřit na snímcích KCD2, pak do pásem | estetika | rešerše hotová |
| 7 | Toky a cesty plánovat společně (rádce 17:40): tok v údolnici, cesta po boku, ≤ 3 křížení na tok | logika krajiny | částečně |
| 8 | Snímky 01–20 vedle referencí + kontrola rádce | brána 3 | |
| 9 | 1.0 | | |

## Další sekce (Míša 28. 10. večer)
- **Postavy – vzhled**: obličeje, oblečení, zbroj (samostatná sekce, později); vlasy ve větru a mimika jen u hrdiny a v rozhovorech tváří v tvář.
- **Dovednosti hráče** (po animacích): celá paleta dovedností, které hráč zlepšuje, a jak (vzor KCD2, ale vlastní názvy a pojetí) – probrat s Míšou, až se k tomu dojde.

## Z dokumentace Warhorse (docs/rozpracovane/warhorse_do_dat.md) – po exportu, postupně s testem
| # | Co | Kam | Stav |
|---|---|---|---|
| W1 | rozměry staveb (výšky pater, tloušťky zdí, schod 0,20 m, příčle 0,20 m, sedák 0,45 m) + test `rozmery` | `pasma.budova`, test_svet | po exportu |
| W2 | hustota textur `texel_m` (tablet 256 px/m NEOVĚŘENO) + test texel 0,5–2× | `pravidla_modelu.json` | po exportu |
| W3 | stínové modely (`stin: "proxy"` z LOD1, bez alfy) – nejdřív ověřit na jednom domě, jestli Godot 4.4 mobil `shadow_mesh` používá | `pravidla_modelu.json`, svet.gd | po exportu, NEOVĚŘENO |
| W4 | okluzory staveb (pár troj., oboustranné vnější zdi, načítat s budovou) | `pravidla_modelu.json`, svet.gd | po exportu |
| W5 | kolize: jednoduché tvary místo sítě u staveb; `kamen` bez síťové kolize (rozpor kolize_m 0) | `pravidla_modelu.json` | po exportu |
| W6 | předměty drobný/střední/velký (LOD až od 1 m³) | `pravidla_modelu.json` | po exportu |
| W7 | výdrž a pád (sprint, obnova, pády 1,5/2,2/8 m) | `hrac.json` | čeká na Míšu |
| W8 | dovednosti, oblečení, výbava, události | nové soubory | v jejich sekcích |
