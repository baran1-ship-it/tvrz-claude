# Účinnost hlídačů (Míša 19. 11.: „hlídači jsou na prd, udělej rešerši jejich účinnosti“)
Zdroj: docs/chyby.md (365 řádků), logy hlídačů 17.–19. 11.

## Kdo chyby našel
| období | chyb | Míša | hlídači/testy | já a pomocníci (snímky, kód) |
|---|---|---|---|---|
| celkem (od 29. 10.) | 365 | 176 (48 %) | ~18 (5 %) | ~170 |
| od 16. 11. | 57 | 44 (77 %) | 7 (12 %) | 6 |

## Co hlídači opravdu chytili (17.–19. 11.)
- lávka most_440_1: kolize nad prkny po přestavbě terénu (skutečná regrese z naší opravy),
- hájovna: staré lůžko + kolize se vrátily po přestavbě krčmy (skutečná regrese),
- hlídač dosahu: únik za okraj světa (skutečná vada), uvíznutí u štoly, odtržené cesty,
- hlídač spojů: 16 prostupů trámů u nové stáje.
Tedy: regrese z našich vlastních přestaveb, kolize, průchodnost, prostupy – to, co člověk okem nevidí.

## Co nechytí nikdy (= skoro vše, co hlásí Míša)
vzhled (tapeta zdí, bílá voda, prázdná krajina, šachovnice), smysl umístění (krumpáč u skály, lopata v peci, stáj ve zdi,
tráva na nádvoří), barvy a světlo, výkon na tabletu. To jsou 3/4 Míšiných hlášení.

## Planné poplachy a cena
- 5 z 11 plných běhů nevedlo k APK: 2 skutečné chyby, 1 planý poplach (karta 10,62 s místo 10,7 – tolerance testu),
  2 restarty kontejneru. Mezistavy (pata_pas, plosiny_rovne) padaly jen kvůli rozdělané práci.
- Plný běh 74–85 min; po 19. 11. jen změněné části 7–24 min.

## Závěr a návrh
Hlídači nejsou na prd – chrání před regresemi, které sami způsobujeme přestavbami (kolize, průchod, únik, prostupy).
Ale na to, co trápí Míšu (vzhled a smysl), jsou slepí a stojí hodinu.
1. Ponechat levné a účinné: test smyslu (18 s), geometrie a spoje jen změněné, průchod jen změněné části (už od 19. 11.).
2. Celý průchod jen před velkým vydáním (HLIDACI_VSE=1), ne před každou APK.
3. Zrušit nebo zmírnit testy s planými poplachy (časování karty, pevné meze, které padají na mezistavu).
4. Vzhled hlídat jinak: kontrolní pohledy s předlohou (snímek z daného místa vedle fotky KCD) a seznam „smyslových“ pravidel
   (nic nestojí ve zdi, nářadí opřené/uložené, nádvoří bez trávy…) jako testy nad daty – to chytí část Míšiných nálezů levně.
