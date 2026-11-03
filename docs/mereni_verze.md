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
| 0.9997 | (vydání) | 3. 11. | měřicí trasa (nově úsek kun-les: trysk ve výšce jezdce) | vše | NEOVĚŘENO NA ZAŘÍZENÍ | | | | | | louka: rozsev 2 s → 0,6–0,8 s/buňka, vlákna podle jader, úroveň podle místa za předstih; kopřivy a sud |

Závěr 0.9995: bez panelu měření tablet na trase drží 42–59 FPS bez záseků. Panel (plný) sám stojí 7–10 ms, tedy
dřívější snímky s panelem (25–35 FPS) výkon podhodnocovaly. Zbytek tabulky (tráva 35 m, stromy, stavby, stíny)
čeká na text ze schránky.

Rozbor 0.9996 (3. 11. večer, stavitel): záseky >40 ms přibývají s **pořadím varianty**, ne s vypnutou skupinou
(vše 45, bez trávy 2, pak 145–211 u všech dalších – i u variant, které práci ubírají). To ukazuje na stav zařízení
v průběhu trasy (teplo, baterie 21 % na Míšiných snímcích = možný úsporný režim), ne na obsah. **Podezření, ne příčina.**
Ověření: trasa znovu na nabíječce / po vychladnutí, nebo pořadí variant obrácené (`mereni_trasa.json varianty`).
Skutečné zhoršení 0.9996 proti 0.9995 v první variantě (p50 +3 ms tvrz-cesta, les p95 43) – rozdíl commitů
7ef213d..f01023b: ves z Blenderu (jiná geometrie vsi), mlýn, příkop, chýše, diag. Neověřeno, který.
