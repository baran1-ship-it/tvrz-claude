# Zadání Míši 2. 11. večer: „Havran a Puchart – inteligentní tvorba scén otevřeného světa“

Platí pro Havrana. Puchart je jiný projekt: jeho body (rozpocty.json, skutečné výšky hradů, krajina 1393) tu jen
zapisuju, nedělám je.

## Zadání ve zkratce (plné znění v konverzaci 2. 11.)
1. **Svět souvislý.** Hráč nemusí vidět všechno najednou. Střídají se uzavřené, polootevřené a panoramatické scény.
   Svoboda pohybu se neomezuje.
2. **Mapa viditelnosti tras** (chůze, běh, kůň). Rozlišuje tři pásma: vidět, zakryto pevnou geometrií, částečně
   zastíněno vegetací.
3. **Clony z krajiny.** Zatáčky, terénní zlomy, okraje lesa, remízky, meze, ploty a stavby. Žádné umělé překážky jen
   kvůli FPS.
4. **Tři typy scén:** A uzavřená, B polootevřená, C panoramatická. Panorama se vegetací automaticky nezakrývá.
5. **Řízení kreslení:**
   - ořez záběrem a LOD podle velikosti na obrazovce;
   - MultiMesh a prostorové členění;
   - okluze jen pevnou geometrií (listí není spolehlivý zakrývač);
   - přednačítání podle směru a rychlosti;
   - omezení vzdálené fyziky, animací a NPC.
6. **Žádné objevování a mizení.**
   - Plynulé přechody, překryv, hystereze a přednačítání.
   - Prověřit AABB MultiMesh buněk.
   - Vzdálené kopce nesmí zešednout.
7. **Les není zelená masa.** Druhy, výšky, průseky, podrost podle stanoviště, mrtvé dřevo. Opar dává hloubku, nemá
   zakrývat chyby LOD. Kvalitu nesnižovat bez měření proti referenci.
8. **Rozpočty scén.**
   - Sleduje se: FPS, p95, záseky, kreslení, GPU a CPU, paměť, overdraw, stíny.
   - Postup: stejná trasa, stejné rozlišení, stejný směr.
   - Měří se při stání, chůzi, běhu, na koni a při otáčení.
9. **Automatický hlídač scén na trasách.**
   - Hlídá: průhledy, zátěž, přechody LOD, doskakování, chybějící terén, změny proti schválené verzi.
   - Každá chyba dostane regresní kontrolu.
10. **Postup:**
    - Nejdřív rozbor toho, co je. Žádný druhý systém vedle fungujícího.
    - Jedna reprezentativní trasa (les + polootevřená krajina + panorama), teprve po prokázaném zlepšení dál.
    - Každá změna musí jít vrátit.
11. **Kritéria úspěchu:** věrohodnost, střídání výhledů, bez doskakování, správné LOD, výkon na Xiaomi Pad 8,
    zachovaná kvalita, automatické kontroly a návrat.

## Co už máme (nestavět znovu) → k bodu zadání
| bod | existuje | stav |
|---|---|---|
| 2 mapa viditelnosti | `tools/mapa_vyhledu.py`: pevné vs. listí (29. 10.), hlídač drahých celků `kompozice.drahe_celky` → `build/drahe_pruhledy.json` (47 bodů) | jen body mřížky a cest, ne trasa s chůzí/koněm; pásma A/B/C nejsou |
| 3 clony | `lokace.json kompozice.remizky`, ves B dvorce (stodola zavře průhled) | remízky hotové, nové clony zatím ne |
| 5 okluze | `svet._okluzory`: terén, domy vsi; listí vypnuto (`pasma.test.okluzor_listi` false) | odpovídá zadání |
| 5 LOD staveb | domy `_Stredni`/`_Daleko`, stodoly a kůlny `_stredni` (2. 11.) | **0.997: prostřední stupeň na tabletu neviditelný** (automatické LOD Godotu rozpustí šindele) – oprava 0.999 |
| 5 přednačítání | louka buňky 32 m a 3 vlákna, předstih 8 s; rostliny po buňkách | podle polohy, ne podle směru a rychlosti |
| 6 žádné doskakování | test `prolinani` (0.998: žádné průhledné prolínání, overdraw); hystereze ne | **chybí hlídač doskakování** |
| 6 šedé kopce | impostory a `kraj` barva; reference ne | neověřeno |
| 8 rozpočty a měření | `MERENI` / `MERENI_AB` (kreslení, trojúhelníky, skupiny vč. stínů), diagnostika na tabletu (záseky, panel) | p95 a trasa se stejným pohybem chybí; tablet měří Míša |
| 9 hlídač scén | hlídači vrstvy 0–7 (`docs/pipeline.md`), pevná sada snímků, tabulky chyb s kontrolou | trasa se záznamem LOD přechodů a doskakování chybí |

## Plán (pořadí podle zadání bod 10)
1. **0.999: mizející dům.** Míša 2. 11.: „dům nebyl vidět, jen stodola, pak se najednou objevil“ (440, 851).
   - Oprava: prostřední stupeň bez automatického LOD (`lod_bias` z dat).
   - Regresní test `lod_mezera`: v režimu tabletu je dům z 20–120 m vždy kreslen aspoň jedním stupněm.
2. **Reprezentativní trasa:** tvrz → les → ves. Cesta tvrz–Lhota obsahuje les (uzavřená scéna), louky a remízky
   (polootevřená) a výhled z hřebene na ves (panorama). Body trasy v datech: `lokace.json kompozice.trasa_hlidace`.
3. **Hlídač scén na trase** (`tools/hlidac_sceny`, test `trasa`).
   - Kamera jede po trase rychlostí chůze, běhu a koně, se směrem pohledu po trase.
   - Každý snímek zapíše: kreslení, trojúhelníky, čas, typ scény (podle délky průhledu z mapy viditelnosti) a seznam
     objektů, které se mezi dvěma snímky objevily nebo zmizely v záběru ve vzdálenosti, kde to hráč pozná.
   - Výsledek: p95 kreslení na úsek, místa s doskakováním, porovnání se schválenou verzí (`build/trasa_schvalena.json`).
4. Teprve potom clony a úpravy LOD na úsecích, které hlídač označí. A/B měření. Míša měří na tabletu stejnou trasu.

## Puchart (jen záznam)
Respektovat `pravidla/svet/rozpocty.json` toho projektu, skutečné výšky a polohy hradů, vodní toky, biotopy kolem
roku 1393. Tady se nedělá.

## Výsledek mapy viditelnosti (2. 11. večer, `mapa_vyhledu.py --krok 50 --max 1500`, obzor = zorná přímka přes koruny do 12 m listí)
| oblast | bodů | obzor p50 | uzavřené (<180 m) | panorama (>600 m) |
|---|---|---|---|---|
| ves | 33 | 555 m | 0 % | 39 % |
| cesty mimo ves | 60 | 478 m | 7 % | 30 % |
| chráněné vyhlídky | 37 | 420 m | 3 % | 14 % |
| louky a les (mřížka) | 588 | 398 m | 17 % | 30 % |

Závěry:
- Ořez vzdálenosti podle scén by ušetřil málo, svět je otevřený.
- Ves je nejdražší a zároveň nejotevřenější (žádné uzavřené místo). Přirozená clona dvorci, sady a remízky má smysl
  právě tam.
- ChatGPT 2. 11.: ověřit, že výpočet počítá vegetaci. Počítá: koruny jsou překážka, víc než 12 m listí na zorné přímce
  výhled zavře (`kompozice.mapa_dohledu.listi_zavre_m`).
- 0.999 až po testu pohybu a otáčení bez mizení (`lod_mezera` a hlídač trasy).

## Návrh hlídače scén (3. 11. večer, po vydání 0.9996) – rozšíření měřicí trasy, ne druhý systém
Základ: `scripts/mereni_trasa.gd` (úseky od → do, pohled na cíl, p50/p95/záseky/kreslení po úsecích) – na tabletu už běží
sama po nové verzi. Hlídač ji rozšíří, ne nahradí:
1. **Souvislá trasa tvrz → les → ves** v datech (`mereni_trasa.json` `trasa_hlidace`: body po cestách z `cesty_osy`,
   ne přímky přes pole), rychlosti chůze / běh / kůň z `pravidla/svet/hrac.json` a `jizda`. Pohled podél trasy
   (směr pohybu + rozhlédnutí ±60° na zlomu úseku).
2. **Typ scény** v každém bodě z mapy výhledů (`tools/mapa_vyhledu.py`: obzor < 180 m = A uzavřená, 180–600 m = B,
   > 600 m = C panorama) – zapíše se k úseku, rozpočty kreslení se pak porovnávají podle typu.
3. **Doskakování:** každých 0,25 s seznam GeometryInstance3D v záběru do vzdálenosti, kde je hráč pozná
   (`pasma.test` – nové číslo `doskok_m`, změřit, ne odhad). Objekt, který mezi dvěma vzorky přibude/zmizí, aniž
   kamera přešla jeho `visibility_range_begin/end` s hysterezí, = doskok (místo, uzel, vzdálenost). Buňky louky
   a rostlin zvlášť (buňka postavená až v záběru blíž než předstih).
4. **Výstup:** `user://hlidac_sceny.json` + tabulka v `docs/mereni_verze.md`; na PC test `trasa` (headless bez
   renderu jen doskoky a přechody LOD), na tabletu i čas. Porovnání se schválenou verzí `build/trasa_schvalena.json`.
5. Teprve podle nálezů: clony (remízky, ploty, sady, terénní zlom) a LOD na úsecích s doskoky nebo drahými průhledy;
   každá změna A/B na stejné trase a jde vrátit.
