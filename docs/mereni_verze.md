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
| 0.9996 | (vydání) | 3. 11. | měřicí trasa | vše | NEOVĚŘENO NA ZAŘÍZENÍ | | | | | | ves z Blenderu v novém rámci, mlýn – pás napojení, příkop – hloubka hladiny; čeká na jízdu Míši |

Závěr 0.9995: bez panelu měření tablet na trase drží 42–59 FPS bez záseků. Panel (plný) sám stojí 7–10 ms, tedy
dřívější snímky s panelem (25–35 FPS) výkon podhodnocovaly. Zbytek tabulky (tráva 35 m, stromy, stavby, stíny)
čeká na text ze schránky.
