# Měření verzí na tabletu (Xiaomi Pad 8)

Každé vydání: Nastavení → Měřicí trasa (7 míst × 8 variant, `pravidla/svet/mereni_trasa.json`). Míša pošle fotku
tabulky, stavitel ji sem přepíše. Hodnoty jsou ms na snímek (p50 / p95 / max), záseky = snímky nad 40 ms.
Varianty: vše (1. průchod), 2. průchod, 3D 70 %, bez stínů / trávy / stromů / staveb / předmětů.

## Historie před měřicí trasou (z `docs/radce.md`, panel na tabletu)
| verze | datum | stav |
|---|---|---|
| 0.57–0.63 | 21.–23. 10. | mikrosekání, louka 15–18 FPS (výplň trávy) |
| 0.67–0.74 | 23.–24. 10. | sekání žádné, špiček 0/30, nejdelší 22–44 ms – **poslední dobrá** |
| 0.75–0.88 | 24.–26. 10. | velké záseky: trimesh kolize dílů, ves a hostinec bez LOD, cesty jako síť (rádce 2. 11. 19:50) |
| 0.997–0.999 | 2. 11. | 17–32 FPS, kreslení+čekání 45–110 ms souvisle, zásek 3,3 s u (13, 42) |

## Záznamy měřicí trasy
| verze | commit | datum | místo | varianta | p50 | p95 | max | záseky | kreslení | troj M | poznámka |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.9991 | eff0c07 | 2. 11. | tvrz-cesta (28, 101) | vše 2. průchod | – | – | 105 | – | – | – | z panelu na snímku: FPS 23, kreslení+čekání 98 ms |
| 0.9991 | eff0c07 | 2. 11. | tvrz-cesta (27, 98) | 3D 70 % | – | – | 117 | – | – | – | FPS 22: tablet má 3D 55 %, varianta tedy rozlišení **zvýšila** o 60 % pixelů a FPS se nezměnilo → brzda není vyplňování pixelů (podezření z 2. 11. vyvráceno) |
| 0.9991 | eff0c07 | 2. 11. | ves (436, 800) | bez předmětů | – | – | 94 | – | – | – | FPS 39, už za soumraku (trasa 30 min, denní doba běžela – opraveno) |

Tabulka trasy se 2. 11. nedostala ven (na obrazovce minutu). Od 0.9992 ji „Zkopírovat záznam měření“ přidá na začátek
(soubor `user://mereni_trasa.txt` z tabletu zůstává, trasu není třeba jezdit znovu).
| 0.9992 | dcc1cb7 | 3. 11. | volná hra (−24, 29), (−157, −150) | vše | – | – | 84 | – | – | – | Míša: „zatím se neseká“; panel 3 záseky za 208 s (0.9991: 979 za 458 s). Kód kreslení mezi 0.9991 a 0.9992 beze změny → rozdíl NEVYSVĚTLEN (jiné místo, krátká hra, bez letu?) – potvrdit měřicí trasou |
| 0.9993 | 4d1b408 | 3. 11. | Test výkonu při chůzi u tvrze (−13…37, 0…32) | vše / bez 3D / bez louky / bez rostlin+předmětů+tvrze / bez života / bez stínů | – | – | – | – | – | – | FPS 37 / 53 / **59** / 68 / 50 / 57 (kroky 6–7 omezeny na 30 FPS – nesrovnatelné). **Louka = největší jednotlivý náklad (+22 FPS bez ní)**, skript louky 4,6 ms. Bez 3D jen 53 FPS → ~19 ms mimo 3D (plný panel sám 7–10 ms – měřit s panelem „jen FPS“). Současně běžel test záseků (varianty Hz/FPS) – kroky nejsou čistě oddělené. |

Závěr 3. 11.: první izolovaný test na tabletu ukazuje louku (trávu) jako hlavní brzdu, ne stavby ani stíny.
Další krok: A/B Nastavení → Tráva úsporná (trsy do 50 m místo 80 m) – FPS i vzhled porovná Míša. NEOVĚŘENO.
| 0.9995 | 7ef213d | 3. 11. | měřicí trasa (tablet, panel vypnut) | vše | 17–24 | 20–32 | 27–89 | 0–1 | 266–528 | 1,1–1,5 | **první úplná tabulka.** p50 17–24 ms (42–59 FPS) na všech 7 místech, p95 ≤ 32 ms – v rozpočtu 30 FPS (33 ms). CPU kreslení (cpuR) 6–10 ms, GPU tablet neměří. Sloupec „skr“ = celý snímek (chybná metrika, opraveno v 0.9996) |
| 0.9995 | 7ef213d | 3. 11. | měřicí trasa | bez trávy | 14–19 | 16–23 | 20–81 | 0–1 | 236–484 | 1,0–1,4 | tráva stojí 3–6 ms na snímek |
| 0.9995 | 7ef213d | 3. 11. | měřicí trasa | tráva do 50 m | 21–26 | 26–35 | 30–39 | 0 | 267–478 | 1,2–1,4 | **beze změny proti vše** → zkrácení dosahu nepomáhá, cena trávy je zblízka; volba „Tráva úsporná“ zbytečná, vzhled nechat |
| 0.9996 | f01023b (= vydání fd77b39) | 3. 11. 21:28 | měřicí trasa (tablet, panel vypnut, 3D 70 %) | vše | 18–27 | 21–43 | 31–117 | >40: 45 sn. (les 31), >100: 1 | 285–526 | 1,1–1,5 | proti 0.9995 (17–24 / 20–32) **horší**: tvrz-cesta p50 27, les p95 43 – PODEZŘENÍ, neprokázáno |
| 0.9996 | f01023b | 3. 11. | měřicí trasa | bez trávy | 17–22 | 20–29 | 24–96 | 2 | 254–484 | 1,0–1,4 | 0.9995: 14–19 / 16–23 → o ~3 ms horší i bez trávy |
| 0.9996 | f01023b | 3. 11. | měřicí trasa | tráva 50 m | 20–32 | 24–76 | 42–407 | 211 | 285–526 | 1,1–1,5 | 0.9995: 21–26 / 26–35, 0 záseků → **výrazně horší**; špička 407 ms les (208, 266) |
| 0.9996 | f01023b | 3. 11. | měřicí trasa | tráva 35 m | 19–32 | 23–67 | 36–94 | 163 | 285–524 | 1,1–1,5 | |
| 0.9996 | f01023b | 3. 11. | měřicí trasa | bez stromů a keřů | 18–27 | 21–73 | 23–98 | 175 | 156–454 | 0,9–1,4 | |
| 0.9996 | f01023b | 3. 11. | měřicí trasa | bez staveb | 18–29 | 22–72 | 26–143 | 145 | 263–355 | 1,1–1,3 | |
| 0.9996 | f01023b | 3. 11. | měřicí trasa | bez stínů slunce | 18–23 | 21–60 | 32–98 | 145 | 248–513 | 1,1–1,4 | |
| 0.9997 | bf4f4c0 | 4. 11. 06:06 | měřicí trasa (tablet, panel vyp, 3D 70 %) | vše | 16–32 | 21–38 | 26–69 | >40: 9 sn. (les 7) | 298–516 | 1,1–1,8 | **kun-les (trysk ve výšce jezdce): p50 18, p95 27, max 67** – jízda na koni bez trávy pozadu výkonově v pořádku; les p50 32 nejdražší |
| 0.9997 | bf4f4c0 | 4. 11. | měřicí trasa | bez trávy | 16–18 | 18–25 | 21–135 | 4 | 252–478 | 1,0–1,4 | tráva stojí 1–15 ms (les 15 ms) |
| 0.9997 | bf4f4c0 | 4. 11. | měřicí trasa | tráva 50/35 m, bez stromů, bez staveb, bez stínů | 16–37 | 19–121 | 24–208 | 0–112/úsek | | | **neplatné pro srovnání**: od 3. varianty (~5 min) záseky na tvrz-cesta/louka/les/skaly u všech variant, i u těch, které práci ubírají; panel: FPS klesá 58 → 25–35 a drží (snímek 29 ms ustáleně) = škrcení tabletu teplem. Potvrzeno 2. měřením po sobě (0.9996 stejný vzor). |
| 0.9998 | (vydání) | 4. 11. | měřicí trasa: vše / bez louky / tráva GPU / vše znovu; úseky kůň mimo cesty | | NEOVĚŘENO NA ZAŘÍZENÍ | | | | | | nový kůň, ovládání KCD, voda bezztrátově, povrchy, prototyp trávy GPU (A/B) |

Závěr 0.9995: bez panelu měření tablet na trase drží 42–59 FPS bez záseků. Panel (plný) sám stojí 7–10 ms, tedy
dřívější snímky s panelem (25–35 FPS) výkon podhodnocovaly. Zbytek tabulky (tráva 35 m, stromy, stavby, stíny)
čeká na text ze schránky.

Rozbor 0.9996 (3. 11. večer, stavitel): záseky >40 ms přibývají s **pořadím varianty**, ne s vypnutou skupinou
(vše 45, bez trávy 2, pak 145–211 u všech dalších – i u variant, které práci ubírají). To ukazuje na stav zařízení
v průběhu trasy (teplo, baterie 21 % na Míšiných snímcích = možný úsporný režim), ne na obsah. **Podezření, ne příčina.**
Ověření: trasa znovu na nabíječce / po vychladnutí, nebo pořadí variant obrácené (`mereni_trasa.json varianty`).
Skutečné zhoršení 0.9996 proti 0.9995 v první variantě (p50 +3 ms tvrz-cesta, les p95 43) – rozdíl commitů
7ef213d..f01023b: ves z Blenderu (jiná geometrie vsi), mlýn, příkop, chýše, diag. Neověřeno, který.

Závěr 0.9997: první dvě varianty (prvních ~4 min) jsou spolehlivé. Jízda na koni (kun-les) 18/27 ms – sekání při jízdě
z 0.9996 (FPS 15–25) se na trase neopakuje; tehdy tráva nestíhala a buňky se stavěly za jízdy. Další varianty měří
teplo tabletu, ne hru → trasa: varianty zkrátit na 2 (vše, bez trávy) nebo pauzy mezi variantami (NEOVĚŘENO, zda pomůže).

### 0.9998 (afa2bc7) – částečná tabulka z fotky Míši 4. 11. 18:13 (varianty „vše“ a „bez louky“ chybí, čekám na text)
| úsek | vše znovu p50/p95/max | tráva GPU p50/p95/max | trojM vše znovu → GPU |
|---|---|---|---|
| tvrz-cesta | 27/111/640 | 18/21/26 | 1.76 → 1.15 |
| louka | 25/82/92 | 17/20/24 | 1.49 → 1.03 |
| les | 31/71/83 | 18/22/27 | 1.52 → 1.11 |
| skaly | 25/50/86 | 18/21/77 | 1.53 → 1.29 |
| kun-les | 20/31/44 | 18/22/28 | 1.27 → 1.22 |
| kun-louka-otoc | 36/111/128 | 20/25/82 | 1.55 → 1.19 |
Pozor: „vše znovu“ běží poslední (tablet nejteplejší), tráva GPU třetí – rozdíl je směs trávy GPU a tepla. Podezření
(ne příčina): tráva GPU zlevní i úseky mimo oblasti GPU (skaly) → ověřit na PC, zda zapnutí GPU neubírá louku jinde.
Volná hra po trase (t 957–1755 s, horký tablet): kreslení+čekání 53–115 ms, FPS 17–30 v trávě/lese, 52–57 FPS na holém
(lom, pohled dolů) → zátěž je kreslení vegetace, ne skripty (_process 4–9 ms, fyzika 1–4 ms).

### 0.9998 – celá tabulka (text od Míši 4. 11.); pozor: první blok vypsán jako „vše znovu“ = ve skutečnosti „vše“
(chyba popisku opravena: název varianty se ukládá v okamžiku měření), „tráva“ = varianta louka = **bez trávy**.
| úsek | vše p50/p95 | bez trávy | tráva GPU | vše znovu |
|---|---|---|---|---|
| tvrz-cesta | 27/111 | 18/21 | 32/134 | 32/127 |
| louka | 25/82 | 17/20 | 27/91 | 31/104 |
| les | 31/71 | 18/22 | 37/86 | 39/97 |
| skaly | 25/50 | 18/21 | 29/55 | 32/65 |
| kun-les | 20/31 | 18/22 | 21/27 | 20/30 |
| kun-louka-otoc | 36/111 | 20/25 | 36/93 | 34/78 |
| kun-les-mimo | 26/68 | 20/25 | 27/44 | 27/60 |
| kun-louka-trava | 20/37 | 17/20 | 22/41 | 20/36 |
| ves | 19/28 | 19/26 | 21/28 | 21/28 |
| mlyn | 17/23 | 17/19 | 18/24 | 17/21 |
| vez-vyhled | 21/28 | 18/21 | 20/27 | 20/25 |
**Naměřený vliv:** louka (tráva) stojí na tabletu p50 +7–13 ms a p95 +30–90 ms v trávě a lese; bez ní je celá trasa
17–20 ms (50–58 FPS). Ves, mlýn, výhled: tráva skoro nic. **Prototyp trávy GPU nepomohl** (v rámci tepla stejně jako
vše) → náklad je kreslení trsů na GPU (vrcholy a překryv karet), ne CPU rozsev. Rozsev GPU se dál nerozšiřuje.
Špičky 560–774 ms u (11–16, 50–63) na začátku úseku tvrz-cesta jen s trávou (bez trávy max 26 ms) – po teleportu se
staví a nahrává louka kolem hráče najednou (podezření, ne potvrzeno; platí i pro rychlé cestování).
Další krok: tablet tráva 80 → 60 m (9565e72) jen kvůli vzhledu (Míša) – výkon NEŘEŠÍ: 0.9995 už ukázala, že 50 m = beze změny
(cena trávy je zblízka; ChatGPT 4. 11. správně připomněl). Trasa 0.9999: vše / bez trávy / **3D 50 %** / vše znovu.
Rozhodovací pravidlo: 3D 50 % ≈ bez trávy → tráva brzdí vyplňováním pixelů (překryv karet, discard alfa nůžek) → zlevnit
fragmenty; 3D 50 % ≈ vše → brzdí vrcholy/instance → méně a jednodušší trsy zblízka.
| 0.9999 | (vydání) | 4. 11. | měřicí trasa: vše / tráva bez stínu (černá – jen výkon) / karty bez ořezu / bez trávy / vše znovu | | NEOVĚŘENO NA ZAŘÍZENÍ | | | | | | ořez karet trávy, tráva 80 m, kůň sedlo+posed+ovladač, rybník kameny, stodola, kůlna, lom opřené nářadí |

### 0.9999 (6dc48e2) – měřicí trasa 4. 11. 23:02 (Míša)
| úsek | vše p50/p95 | tráva bez stínu | karty bez ořezu | bez trávy | vše znovu |
|---|---|---|---|---|---|
| tvrz-cesta | 27/93 | 22/71 | 32/128 | 18/22 | 32/119 |
| louka | 28/86 | 21/53 | 31/94 | 17/21 | 30/96 |
| les | 35/76 | 27/46 | 38/89 | 19/23 | 37/92 |
| skaly | 28/54 | 23/40 | 30/59 | 19/22 | 29/54 |
| kun-les | 19/29 | 20/28 | 20/30 | 19/23 | 21/29 |
| kun-louka-otoc | 35/82 | 24/48 | 33/74 | 20/25 | 30/69 |
| kun-les-mimo | 27/61 | 22/32 | 29/72 | 21/25 | 24/43 |
| kun-louka-trava | 20/37 | 19/24 | 20/48 | 18/21 | 20/32 |
| ves | 24/33 | 23/30 | 23/31 | 23/30 | 24/31 |
| mlyn | 18/26 | 17/21 | 19/26 | 17/20 | 17/23 |
| vez-vyhled | 25/74 | 22/53 | 25/66 | 19/27 | 23/53 |
**Naměřený vliv (potvrzeno):** stínový průchod slunce přes trávu (GL Compatibility kreslí stínované světlo druhým
průchodem) = asi **60 % ceny trávy v p50** (louka 28 → 21, bez trávy 17) a **polovina p95** (86 → 53). Tráva bez stínu
běžela 2. (tablet teplejší než u „vše“) – přínos spíš podhodnocen. **Ořez karet: v rámci šumu tepla** (bez ořezu 31/94 ×
vše 28/86 × vše znovu 30/96) – malý nebo žádný. Zbytek ceny trávy (~4–6 ms p50, ~30 ms p95) = kreslení trsů samo.
Další krok: tráva unshaded jako výchozí na tabletu – nejdřív opravit barvu (na PC i tabletu tmavá/černá; Míšiny snímky).
Špička 2586 ms u (186, 887) v kun-les-mimo (jednou, varianta karty_cele) – NEOVĚŘENO, co to bylo.
| 0.99991 | (vydání) | 5. 11. | měřicí trasa: vše / tráva bez stínu (barva louky kalibrovaná, les bělavý) / bez trávy / vše znovu | | NEOVĚŘENO NA ZAŘÍZENÍ | | | | | | kalibrace barvy unshaded trávy; tablet zatím stínovaná |
