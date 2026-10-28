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
