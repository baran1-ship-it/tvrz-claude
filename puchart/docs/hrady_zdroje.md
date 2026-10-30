# Dvojhradí Puchart – dochované zdroje a jak je stavba používá

Míša 30. 10.: „Udělej to vše přesně podle dochovaných zdrojů a maleb… co není doložené, si můžeme vymyslet.“
Data: `pravidla/svet/hrad_puchart.json` (každý díl má `jistota`), stavba `blender/puchart_hrad.py`,
terén `nastroje/teren_upravy.py`. Kresby jsou autorské – v repu jen odkazy.

## Zdroje
| zdroj | co obsahuje | odkaz |
|---|---|---|
| GC80T08 „Pověsti o hradu Puchart“ (Hlavacek Team) | půdorys v současnosti + řez A–A'; kresebná rekonstrukce celku; přední hrad; zadní hrad ve verzi se štítovou zdí; text o podobě | geocaching.com/geocache/GC80T08; obrázky s3.amazonaws.com/gs-geo-images/ 3ea7868f…png (půdorys), 3995d35a…_l.jpg (celek), 1d5bf2cf…_l.jpg (přední), b64f0880…_l.jpg (zadní) |
| Archeologický atlas (Tomášek a kol. 2015) | plán A/B/C, „zadní hrad lichoběžníkovitého tvaru… skalní průrva s hranolovou věží a hlavní objekt – palác“, „čelní hradba zadního hradu se špaletou vstupní brány“ | archeologickyatlas.cz/cs/lokace/kyzlirov_pr_hrad_pusty_zamek |
| turistika.cz | obytná věž / palác 10×12 m, okna a dveře v přízemí, příčná zeď > 6 m | turistika.cz/mista/puchart-sudetske-dvojhradi |
| Krška 2004, Sborník SOkA Přerov | jméno Puchart-Zighart, Předhradí, nejstarší zmínky (bez stavebního popisu) | archives.cz … soka_prerov_sbornik_2004.pdf |
| ČÚZK DMR 5G | lokální reliéf: jádro na vrcholu, okružní val, úzký hřbet, příkop, skalní suk | `docs/screens/hrady_relief.png` |
| OSM (lokace.json) | bod zříceniny zadního hradu x 62, z 151 | leží na suku z DMR |

## Co je podle čeho
**Přední hrad** – DOLOZENO: bezvěžový plášťový hrad, lichoběžník cca 35×25 m (GC80T08), na hraně vrcholové plošiny
(DMR); brána v SV rohu; nástup mostu ve V části valu; tři budovy SV, SZ, J; mohutný val (DMR). KRESBA: vysoký plášť
s cimbuřím, palác se sedlovou střechou u J strany, nárožní věžička se stanovou střechou, zeď po hřebeni valu a branka
se stanovou střechou na jejím konci, dřevěný most na kozách. NAVRH: SV roh seříznutý (brána kolmo na most), práh 1 m
pod nádvořím s rampou (most by jinak stoupal 20 %), krytý ochoz s pavlačí, dřevěné schodiště s podestou, cesta parkánem.

**Zadní hrad** – DOLOZENO: poloha na skalním suku za příkopem (DMR, OSM), lichoběžník/mnohoúhelník, skalní průrva,
hranolová věž, palác 10×12 m, čelní hradba se špaletou brány, most přes průrvu začínající níž, než ukazuje kresba
(GC80T08). KRESBA: dlouhý vodorovný most na vysokých kozách, nízká lomená hradba kolem skály, vysoký hranol a palác
se strmou střechou nad ní, hrad v terasách. NAVRH: dolní nádvoří 10,5 m (brána, most) a horní 12 m s kamennými schody,
vstup do věže z ochozu lávkou, schodiště na ochoz.

**Cesta mezi hrady** – DOLOZENO spojnice po hřbetu (atlas), průběh NAVRH: z předbraní parkánem podél V strany jádra
a po hřbetu k nástupu mostu přes průrvu (`cesty_puchart.json` hrebenova).

## Rozpor ve zdrojích
- Atlas: „v čele plošiny věž“ × GC80T08: „bezvěžový“ → věž jen jako nárožní věžička z kresby.
- Příkop předního hradu „mělký“ (GC80T08) × „hluboký a široký“ (turistika) → terén nechán podle DMR.
- Vzdálenost hradů 100 m (GCXYVZ) × 150–200 m (turistika) → podle DMR ~155 m mezi středy.
