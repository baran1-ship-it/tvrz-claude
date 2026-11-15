# Míša 15. 11. – chyby z tabletu (0.999998) → příčina + pravidlo + kontrola v testu

Snímky: `docs/screens/misa_15_11/01.jpg` … `17.jpg` (zmenšené, pořadí jako v chatu).
Míša: „už se to řešilo stokrát“ → u opakovaných chyb (tráva v hostinci, oblečení, létající rostliny) platí CLAUDE.md:
po dvou neúspěšných opravách žádný třetí pokus naslepo, nový rozbor příčiny (co je jinak na tabletu × PC).

| # | Co Míša viděla (místo, snímek) | Příčina (zjištěno) | Pravidlo / tabulka | Kontrola v testu | Stav |
|---|---|---|---|---|---|
| 1 | Tráva v hostinci na podlaze (01) – opakovaně (ř. 57, 92 dřívějších tabulek; na PC test `hostinec_trava` 0) | rozbor běží | | | rozbor |
| 2 | Tráva před dveřmi chýší v lomu (07, u 163, 959) | rozbor běží | | | rozbor |
| 3 | Postavy mají potrhané oblečení – díry/trojúhelníky na ramenou a zádech (02, 12) | rozbor běží | | | rozbor |
| 4 | Vodopád (kaskáda potoka z kopce) vypadá divně – ploché lesklé plachty, prochází trávou a kameny (08, 09, 10; u 276–291, 1094–1129). Míša: načíst na internetu, jak se dělá | rozbor + rešerše běží | | | rozbor |
| 5 | Dvůr krčmy nepustí k domu; když tam hráč přiletí, nepustí ho ven – „neviditelné ploty“ (13–17, u 470–483, 805–814) | rozbor běží | | | rozbor |
| 6 | Déšť na ploše dvora krčmy nebyl a nebyl vidět ani na SZ hraně pozemku (16, 17) | podezření: stejná příčina jako 5 (něco nad dvorem → hra myslí „pod střechou“) – rozbor běží | | | rozbor |
| 7 | Pozemek krčmy nepustí na schody k pokojům (15) | rozbor běží (souvisí s 5?) | | | rozbor |
| 8 | Létající trsy trávy, bylinky, mech a houby – hřib v koruně stromu (05, u 177, 906), hřib vysoko na nebi (06, u 158, 956), trs ve vzduchu (03, u 149, 848) | rozbor běží (dřív ř. 7 tabulky 28. 10. „hřiby létají“ – opraveno, vrací se) | | | rozbor |
| 9 | Puchart: jak dělá déšť a jaké má hlídače – vzít, co je lepší nebo co nemáme | porovnání běží (dřívější: `dest_z_pucharta.md`, `hlidaci_z_pucharta.md`) | | | rozbor |
