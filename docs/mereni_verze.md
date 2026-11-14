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
| 0.99992 | e7272fb | 5. 11. 16:59 | měřicí trasa (vše / tráva bez stínu / bez trávy / vše znovu), Míša tablet | | studený: vše p50 17–34, p95 19–39; bez stínu p50 17–26; zahřátý p95 54–122 | | | | | | kůň (sesednutí, most, voda, překrok), most s cestou, vlajky ve větru (latka.gdshader), předehřátí všech shaderů + keš do diag.log, export (kryti, datové textury) |
| 0.99993 | 9e23ea1 | 6. 11. 06:22 | měřicí trasa: vše / tráva bez stínu / bez trávy / vše znovu / auto (nová varianta automatické kvality) | | studený vše p50 17–30 p95 20–36; zahřátý p95 55–128; auto p95 37–46 (po zapnutí 30 FPS) | | | | | | postavy dobové (26 sad, ~7,5 tis. troj. místo ~30 tis., 32 obyvatel podle příběhu, lůžka, nábytek, předměty v rukou, stín jen do 15 m, animace v dálce 4 fps), automatická kvalita (výchozí ruční), tráva unshaded s 2 složkami světla (tablet false), korouhev |

### 0.99991 (b5decff) – měřicí trasa 5. 11. 07:06 (Míša, tablet ráno studený)
| úsek | vše (1., studený) | tráva bez stínu (2.) | bez trávy (3.) | vše znovu (4., horký) |
|---|---|---|---|---|
| tvrz-cesta | 25/28 | 23/61 | 18/22 | 31/126 |
| louka | 24/30 | 19/55 | 17/21 | 30/104 |
| les | 32/38 | 26/47 | 18/22 | 37/94 |
| kun-louka-otoc | 28/75 | 26/71 | 19/23 | 36/127 |
| kun-louka-trava | 22/59 | 18/28 | 17/21 | 30/82 |
**Naměřeno:** studený tablet s trávou p95 28–38 ms (žádné sekání na tvrz-cesta/louka/les); stejné úseky na konci 94–126 ms.
**Sekání = škrcení teplem**, ne obsah: GPU se zahřeje a zpomalí 2–3×. Tráva bez stínu p50 −2 až −6 ms proti studenému
„vše“ (konzistentně), p95 už ovlivněné ohřevem. Bez trávy drží 17–22 ms i zahřátý (nejméně práce = nejméně tepla).
**Závěr:** cíl není rychlejší snímek, ale méně práce za minutu (méně tepla): (1) tráva bez stínového průchodu (po opravě
barvy v lese), (2) A/B Nastavení → „Snímky: pevných 30 FPS“ (už existuje) – omezení snímků snižuje ohřev; ověřit 20 min hrou.

### 0.99992 (e7272fb) – měřicí trasa 5. 11. 16:59 (Míša, tablet)
| úsek | vše p50/p95 | tráva bez stínu p50/p95 | bez trávy p50/p95 | vše znovu p50/p95 |
|---|---|---|---|---|
| tvrz-cesta | 25/30 | 18/23 | 18/22 | 32/122 |
| louka | 27/31 | 17/24 | 18/21 | 31/108 |
| les | 34/39 | 18/26 | 20/24 | 39/88 |
| skaly | 26/30 | 18/34 | 20/24 | 29/54 |
| kun-les | 18/21 | 20/28 | 19/23 | 20/29 |
| kun-louka-otoc | 31/37 | 26/70 | 19/24 | 33/89 |
| kun-les-mimo | 26/30 | 24/61 | 21/25 | 29/77 |
| kun-louka-trava | 21/32 | 21/44 | 18/22 | 29/60 |
| ves | 26/31 | 24/31 | 23/31 | 26/34 |
| mlyn | 17/19 | 18/20 | 21/24 | 19/23 |
| vez-vyhled | 21/29 | 22/25 | 19/22 | 24/28 |

Paměť VRAM 849 MB (textury 592, buffery 257). Špičky > 200 ms: 696 ms a 250 ms při zahřátí (věž, tvrz-cesta), po konci
trasy 1208 ms kreslení u (4, 4) a 176 ms skript `den` (NEOVĚŘENO, co to bylo – přepnutí denní doby po měření?).
**Naměřeno:** studený tablet: tráva bez stínového průchodu (unshaded) má p50 skoro stejně jako úplně bez trávy
(louka 17 vs 18, les 18 vs 20, tvrz-cesta 18 vs 18) – **cena trávy na tabletu je prakticky celá stínový průchod**.
P95 bez stínu na koni (kun-louka-otoc 70, kun-les-mimo 61) už v době, kdy se tablet ohřívá (pořadí variant – NEOVĚŘENO,
zda by šlo i studené). Zahřátý („vše znovu“) znovu p95 54–122 – škrcení teplem jako 0.99991.
**Závěr:** zapnout trávu unshaded na tabletu hned, jak bude opravená barva v lese (pomocník běží, 2 dřívější pokusy
neúspěšné → nový rozbor). Je to největší naměřená úspora (p50 −7 až −16 ms na tvrz/louka/les) a méně práce = méně tepla.

### 0.99993 (9e23ea1) – měřicí trasa 6. 11. 06:22 (Míša, tablet), 5 variant
| úsek | vše | bez stínu | bez trávy | vše znovu | auto (stupeň) |
|---|---|---|---|---|---|
| tvrz-cesta | 23/28 | 20/23 | 19/23 | 30/128 | 29/123 (−1) |
| louka | 24/28 | 19/24 | 16/19 | 29/98 | 30/102 (−3) |
| les | 30/36 | 25/31 | 18/22 | 36/87 | 36/88 (−4) |
| skaly | 23/29 | 21/25 | 19/22 | 27/55 | 32/55 (−5) |
| kun-louka-otoc | 25/34 | 21/29 | 18/22 | 32/118 | 33/46 |
| kun-les-mimo | 21/26 | 20/23 | 20/23 | 26/77 | 33/37 |
| kun-louka-trava | 18/27 | 18/23 | 18/22 | 28/82 | 33/37 |
| ves | 24/30 | 23/29 | 22/28 | 24/30 | 33/37 |
| vez-vyhled | 22/25 | 20/23 | 19/22 | 22/27 | 33/38 |
(p50/p95 ms). VRAM 902 MB (0.99992: 849).
**Naměřeno:**
- 32 dobových postav: „vše“ studený stejně jako 0.99992 (ves 24/30 proti 26/31) – nové postavy výkon nezhoršily.
- Automatika zapnula 30 FPS, kratší stíny, stíny předmětů, efekty, 3D 86 %. Po 30 FPS je zahřátý tablet rovnoměrný:
  p95 37–46 místo 77–118 („vše znovu“), p50 33 = strop 30 FPS. Obraz se viditelně nezměnil (Míša: „nic neubralo“) –
  jemné kroky jsou málo vidět záměrně; pozná se to na plynulosti, ne na grafice.
- **Potvrzená příčina zásekům 1359 a 1369 ms:** změna rozlišení 3D za hry (zapnutí 3d_86 u skal, vrácení u věže) –
  kroky 3d_86 a 3d_72 vypnuty v datech.
- Automatika reagovala pomalu: první 3 úseky (200 s) ještě sekané – dolu_oken 3 → 2.
- Tráva bez stínu: les 25/31 (0.99992: 18/26) – nový stín korun ve vertex shaderu (3 čtení textury) zdražil unshaded
  o ~7 ms v lese (podezření, ověřit variantou bez stínu korun).
- Špičky v „vše“: ves 444 ms (kreslení 723), skaly 278 ms – podezření první vykreslení nových postav/materiálů.

### Rozbor 0.99993 – volná hra horší než trasa (6. 11., pomocník; snímky `docs/screens/misa_6_11`, jen kód a data, nic nespuštěno)
**Podmínky (zjištěno z EXIF a panelu):** snímky 06:25–06:41, trasa skončila ~06:21, t na panelu 1228–2139 s → volná hra
běžela hned po trase, v **20.–35. minutě souvislé zátěže** (tablet nejteplejší). Automatika **vypnutá** (výchozí ruční;
trasa po konci vrací původní stav; řádek FPS nemá „· kvalita“), snímky **neomezené** (FPS až 39). Trasa navíc: hráč bez
fyziky (fyzika ve hře 2–10 ms, 2 kroky), bez koně, panel vypnut (Míša měla jen řádek FPS – levný), denní doba stojí,
**nikdy nevjede do interiéru ani k ohništím domů zblízka**, ves jen ulicí (413–458, 781–817).
**Hypotézy podle pravděpodobnosti (vše PODEZŘENÍ):**
1. Teplo + bez automatiky a bez 30 FPS: odpovídá „vše znovu“ (p95 77–128) – už naměřený vzor 0.99991–0.99993.
2. Ohně: všech 12 ohnišť + pec v každém domě vsi svítí **i ve dne** (`svet.gd` night_only = false), `life._shadow_budget`
   zapne až 7 OmniLight do 38 m a na kvalitě 1 nejbližší do 18 m **se stínem** (krychle 6 pohledů). V Compatibility je
   každé světlo se stínem další průchod všech objektů v dosahu 9,5 m (zeď, terén, buňka louky celá). Hostinec: 2 krby
   se stínem 10 m od sebe + tráva uvnitř (ř. 57) → 117–155 ms. Plameny CPUParticles mají výchozí cast_shadow = zapnuto
   (může vynutit překreslení stínu každý snímek – neověřeno).
3. Postavy: 32 skinovaných do 70 m, animace každý snímek zblízka; studená trasa vliv nenašla, zahřátá neměřena.
4. Záseky 2095 ms (372,748, na koni, první pohled do vsi od západu) a 485 ms (421,869, žena s košíkem): kreslení+čekání,
   skripty 5, nové uzly 0, grafika beze změny (žádné nové nahrávání), louka hotové 5 / 1 → podezření: první stín ohně
   domu (vstup do 18 m) nebo první vykreslení postavy/předmětu v ruce na Adrenu (ovladač); louka méně pravděpodobná.
   Stejný druh jako 444 ms ves (trasa 0.99993), 2586 ms (0.9999), 4104 ms most (0.99991).
**Jak změřit (přidáno, NEOVĚŘENO NA ZAŘÍZENÍ):** úseky `ves-vjezd` (330,725→380,752, výška jezdce), `ves-dvory`
(415,862→425,876), `hostinec` (uvnitř, −62,929→−68,933); varianty `vše / bez_svetel / bez_postav / svetla_bez_stinu /
stiny / vše znovu`. Čtení: zásek na ves-vjezd jen v 1. průchodu = první vykreslení; v každém = obsah. bez_svetel ≈
svetla_bez_stinu ≪ vše v hostinci/vsi = stín ohně. Teplo: porovnávat s průměrem obou „vše“. Volná hra potom 20 min
s automatikou zapnutou (Nastavení), jinak srovnání s trasou nemá smysl.


### 0.99995 (3a58318) – měřicí trasa 9. 11. 14:17 (Míša, tablet), 3D 100 %, snímek `docs/screens/mereni_0_99995.jpg`
| varianta | úseky p50 | p95 | >100 ms | poznámka |
|---|---|---|---|---|
| vše | 25–57 (les 57, skály 49, louka-otoč 51) | 29–122 (les 122, louka-otoč 106) | les 25, louka-otoč 19 | ves/mlýn/hostinec p50 25, p95 29–35 |
| bez postav | 24–61 | 28–132 | les 32 | ≈ vše → postavy nejsou cena |
| vše znovu | 18–61 | 23–127 | les 29, tvrz-cesta 13 | kůň/ves/mlýn p50 18–22 |
| auto | 33 (30 FPS) | 36–127 | les 27 | automatika přepnula hned teplem 0,89 (fps_30, stíny, efekty), ne FPS |
Skripty (skr) 3–8 ms všude, fyzika 1–7 (kun-les-mimo 68 jednou). VRAM 930 MB.
Špičky: 1699 ms auto/kun-les (−2,461), 760 ms tvrz-cesta (5,31), 566 ms bez postav/tvrz-cesta (18,72), 258 ms, 208 ms
hostinec – všechny „kreslení“ 280–500, skripty 3–9. Volná hra po trase: 750, 1708, 1242 ms (proces = celý snímek)
a úseky 60–75 ms průměr (FPS 13–16) asi 15 s.

**Rozbor (9. 11.):**
- **OVĚŘENO NA ZAŘÍZENÍ:** záseky skriptů jsou pryč – skr 3–8 ms (0.99994: lide 692–957 ms, predmety 13–61 ms).
- **NAMĚŘENO:** 3D 100 % zdražilo les a otevřenou louku: les p50 57 / p95 122 (0.99993 studený p50 17–34 při 3D 45–70 %).
  Ves, mlýn, hostinec p50 25 (40 FPS) i při plném obrazu. Podle §0 „plný obraz“ se ubírá detail lesa (překreslování
  průhledných listů a trávy v plném rozlišení), ne rozlišení – další krok: izolovaná varianta les bez trávy / bez korun.
- **NAMĚŘENO:** postavy nemají vliv (bez postav ≈ vše).
- **PODEZŘENÍ:** špičky 0,5–1,7 s jsou kreslení (ne skripty, ne nové uzly) – první vykreslení / kompilace na Adrenu
  při vjezdu do nové oblasti (kun-les −2,461, tvrz-cesta). Ověřit: zda se opakují ve 2. průchodu stejného místa.
- Teplo 0,89 hned na začátku auto varianty (po 15 min trasy) – automatika správně sáhla nejdřív po 30 FPS.

### 0.99995 (3a58318) + Game Turbo – měřicí trasa 10. 11. 09:17 (Míša, tablet), 3D 100 %, varianty vše / bez postav / vše znovu / auto
- Game Turbo nalezen: **Zabezpečení → Nástroje zabezpečení → Game Turbo → Přidat hru** (Odkaz Havrana zapnut). Baterie
  „Vyvážený“. Srovnání s 9. 11. (bez Game Turbo, stejná verze): les p50/p95 57/122 → **49/94**, skály 49/– → 44/61,
  louka 35/58, ves 27/36, mlýn 26/31, hostinec 19/25. Rozdíl Game Turbo × teplota tabletu NEROZLIŠEN (jeden běh).
- „vše znovu“ (tablet teplejší) tvrz-cesta 22/32, louka 23/35 – lepší než první „vše“ (37/76, 35/58): první průchod
  = načítání/kompilace (srov. rešerše krok 2a).
- VRAM 949 MB (textury 687, buffery 262), uzlů 18 360. Kreslení 259–717 (ves-vjezd 717).
- **Špičky 2,3–3,8 s: všech 5 změn automatické kvality leží v místě špičky** (FAZE KVALITA u (5,31) fps_30 → 2273 ms
  u (5,32); (205,250) stiny_predmetu → 3829 ms; (−78,896) efekty → 3331 ms; vypnutí u (4,4) → 3283 ms u (2,2)).
  = naměřený vliv (shoda poloh), příčina NEOVĚŘENO (krok sám, nebo načítání na začátku úseku). Izolovaný test zaveden
  10. 11.: `kvalita.gd` zapíše u každého kroku čas uplatnění a nejdelší snímek po změně („↳ krok …“).

### 0.99996 (1a832b0) – vydáno 10. 11. 13:13, 3D 75 %, Game Turbo, Baterie Vyvážený – NEOVĚŘENO NA ZAŘÍZENÍ
- Trasa: varianty vše / les bez trávy / les bez korun / stíny (slunce bez stínu) / vše / auto; u špiček volná paměť, halda,
  VRAM; automatika zapisuje „↳ krok: uplatnění X ms, nejdelší snímek po změně Y ms“.
- **Měřeno 10. 11. 15:34 (Míša, tablet, 3D 80 % = volba „střední“ v Nastavení, Game Turbo, Vyvážený).** p50/p95 ms:
  | úsek | vše | les bez trávy | les bez korun | slunce bez stínu | vše znovu |
  |---|---|---|---|---|---|
  | les | 38/85 | 29/65 | 25/52 | 27/42 | 30/48 |
  | louka | 28/57 | 28/49 | 23/39 | 23/35 | 30/39 |
  | skály | 26/55 | 29/38 | 24/38 | 23/29 | 26/33 |
  | kůň-louka-otoč | 31/64 | 29/60 | 24/52 | 25/46 | 25/38 |
  | ves / mlýn / hostinec | 21/28, 20/24, 18/21 | – | – | – | – |
  Srovnání 0.99995 (100 %): les 49/94 → 38/85, skály 44/61 → 26/55.
- **Naměřený vliv:** stín slunce je v lese a na louce největší jednotlivá cena (les p95 85 → 42, louka 57 → 35); koruny
  stromů v lese p50 −13 ms; tráva v lese p50 −9 ms.
- **Automatika (izolovaný test):** krok fps_30 snímek po změně 60 ms, stiny_kratsi 37, **stiny_predmetu uplatnění 46 ms +
  snímek 332 ms**, efekty 45 + 77 ms. Kroky samy 2–4 s nedělají → předchozí hypotéza VYVRÁCENA. Špičky 1,2–2,2 s jsou
  na začátku každé varianty u (5, 30) („zahrati“, `_process` 1250 ms neměřených skriptů) = přepnutí varianty trasy
  (podezření: mereni_trasa / louka při přestavbě varianty, NEOVĚŘENO), ne hra.
- Paměť u špiček: `OS.get_memory_info()["available"]` na tabletu vrací 0 („volna -0 MB“) – zdroj volné paměti je třeba
  vzít z měřiče PSS v diag.gd. VRAM 948 MB (textury 676).


### 0.99997 (aa03c89) – vydáno 10. 11. 22:31 – NEOVĚŘENO NA ZAŘÍZENÍ
- Změny proti 0.99996: sdílené textury předmětů (glb 310 → 28 MB, 161 kopií pryč), jádro korun + stínové těleso stromů,
  listí bez depth_prepass_alpha, živé postavy (rozvrhy, scénky, Mixamo), tlačítko Běh.
- **Měřeno 11. 11. 05:12 (Míša, tablet, 3D 80 % „střední“, Game Turbo).** Varianta „vše“ p50/p95 ms:
  tvrz-cesta 28/34, louka 27/31, **les 35/40**, skály 24/31, kůň-les 20/28, ves 25/32, mlýn 20/26, ves-vjezd 26/35,
  hostinec 17/20, věž 26/29.
- **NAMĚŘENO (proti 0.99996, stejných 80 %):** les p95 85 → 40, louka 57 → 31, skály 55 → 31 – jádro korun + stínové
  těleso stromů (Puchart) srazilo špičky lesa na polovinu. VRAM 948 → 786 MB (textury 676 → 508; sdílené textury
  předmětů). Uzlů 18,7 k → 26,9 k (postavy, lavice, stínová tělesa).
- **REGRESE (naměřený vliv, příčina NEOVĚŘENO):** v auto variantě každý krok automatiky = zásek 2,7–3,5 s v neměřeném
  `_process` (stiny_kratsi uplatnění 0 ms → snímek 3506 ms; stiny_predmetu 101 → 3086; efekty 52 → 2744). 0.99996:
  37 / 332 / 77 ms. Měřič PSS u záseků NEBYL (značka chybí). Izolovaný test: `tools/test_vykon.gd` kroky_kvality
  (každý krok zvlášť ve světě, headless = jen skripty).
- **Izolovaný test 11. 11. (PC headless, `kroky_kvality`, krok zapnout/vypnout bez zápisu deníku):** uplatnění
  fps_30 / stiny_kratsi / efekty / trava_dosah 0 ms, stiny_predmetu 136–154 ms (`find_children` přes celý strom);
  snímky po kroku 7–8 ms (jednou 170 ms po fps_30). **Kroky samy (skripty) 2–3 s nedělají** → zbývá zápis deníku
  `diag.faze` s čekáním na vlákno (opraveno 5e04eda, ověří trasa: řádek „cekani na predchozi zapis“) nebo ovladač.
- Začátky variant 946 / 265 / 319 / 414 ms (0.99996: 1,2–2,2 s). „volna -0 MB“: opraveno čtením /proc/meminfo.

### 0.99998 – vydáno 11. 11. 19:00 (testovací, export 7d492cc068) – NEOVĚŘENO NA ZAŘÍZENÍ
- Změny proti 0.99997: choreografie dne každé postavy (`docs/rozpracovane/choreografie_postav.md`), kupec u stanu +
  obchod jako v KCD (6 obchodníků, `pravidla/svet/obchod.json`), poutníci po celé mapě, hosté po celé síni, lavice
  venku s odstupem a ne v místnostech, nové Mixamo klipy (položení, výklad vsedě), sedlo se smíchem kostí krku (NEOVĚŘENO),
  diag: fáze ve hře nečekají na zápis (oprava podezření na 2–3 s záseky po krocích kvality – ověří trasa: řádek
  „cekani na predchozi zapis“), volná paměť z /proc/meminfo, export: UV klenby sklepa.
- Matice vztahů testovací: pokrytí 44/114, úspěšnost 32/44.
- **Měřeno 11. 11. 19:59 (Míša, tablet, 3D 80 %).** „vše“ p50/p95: tvrz-cesta 28/34, louka 27/31, les 35/41, skály 23/30,
  kůň-les 22/27, ves 20/26, mlýn 20/24, **ves-vjezd 34/44 (0.99997: 26/35)**, ves-dvory 30/37, hostinec 19/23, věž 25/30.
- **OVĚŘENÁ OPRAVA (1 běh):** kroky automatiky fps_30 33 ms, stiny_kratsi 35, stiny_predmetu 138+172, efekty 67+104
  (0.99997: 3506 / 3086 / 2744 ms) – příčina byla čekání `diag.faze` na zápis ve vlákně (5e04eda).
- **REGRESE (naměřený vliv, příčina NEOVĚŘENO):** ves-vjezd +8 ms p50 (kreslení 706, 2,3 M troj.); podezření nové
  postavy a lavice na návsi (choreografie) – izolovaný test: varianta trasy bez postav.
- Špičky 2,5–3,6 s (3× za 30 min: (-24,331), (172,894), (439,802)) mimo skripty (proces max 28 ms při snímku 3588 ms),
  bez vztahu ke krokům kvality – kreslení/ovladač/systém, NEOVĚŘENO. Paměť u špiček „-0/0“: trasa četla
  OS.get_memory_info – opraveno (bere diag: /proc/meminfo, halda).

### 0.99999 – vydáno 13. 11. 12:45 (testovací, commit 80686596 → e3c0e84a)
- **Měřeno 13. 11. 14:17 (Míša, tablet, 3D 75 %).** p50/p95 „vše“ / „bez postav“: tvrz-cesta 21/33 / 17/26, louka 25/31 /
  17/25, les 27/62 / 19/38, ves 30/35 / 20/24, mlýn 26/32 / 17/22, ves-vjezd 29/34 / 20/25, ves-dvory 33/38 / 29/42,
  hostinec 28/33 / 20/27, věž 29/33 / 17/22. VRAM 741 MB, uzlů 26,7 k.
- **REGRESE (naměřený vliv):** postavy stojí +8–10 ms p50 skoro na každém úseku (i louka/les). 0.99995: „bez postav ≈ vše“;
  ves/mlýn/hostinec p50 0.99996 21/20/18, 0.99998 20/20/19 → 0.99999 30/26/28; „bez postav“ 20/17/20 = stará úroveň.
  Měřené skripty (skr) jen +1–2 ms → cena je mimo měřené skripty (kostra, modifikátory, skinning). Příčina NEOVĚŘENO.
- Podezření (vše nové u postav mezi 0.99998 a 0.99999): (a) `sukne_ridic.gd` SkeletonModifier3D (jen v záběru do 15 m),
  (b) +24 kostí sukně na postavu (ec42097f), (c) úchopy – druhá ruka IK ve 3 kolech (8dd3ab02, e0f27d6f),
  (d) LOD: jdoucí postava v záběru do anim_do_m plná animace (fe4e4039).
- Izolovaný test: varianty trasy bez_sukne / bez_uchopu / anim_lod_stary (zavést), PC headless měření stejných skupin.

### 0.999991 – měřicí sestavení 13. 11. 14:30 (stejný obsah jako 0.99999, varianty izolace postav)
- **Měřeno 13. 11. 14:56 (Míša, tablet, 3D 75 %).** p50 vše / bez postav / bez modif. / bez sukně / bez úchopů:
  tvrz-cesta 20/17/33/26/27, louka 25/17/28/25/27, les 24/19/27/23/23, ves 28/18/30/28/28, mlýn 24/17/33/25/25,
  ves-vjezd 29/20/30/29/31, ves-dvory 36/30/37/35/35, hostinec 29/18/28/28/27, věž 26/19/26/26/30.
- **VYVRÁCENO:** řidič sukně, úchopy ani ostatní modifikátory kostry cenu postav nedělají (vypnuté ≈ vše; „bez modif.“
  dokonce +80–100 kreslení – NEOVĚŘENO proč). Postavy dál +8–11 ms p50, skripty jen +1–2 ms, kreslení stejné.
- Zbývající podezření: animace a přepočet kostry (+24 kostí sukně na postavu, ec42097f) a plná animace jdoucích postav
  v záběru do 45 m (fe4e4039). Izolace v dalším sestavení: varianty bez_animace a chuze_lod.

### 0.999992 – vydáno 13. 11. 15:28 (postavy bez prosvítání, atlas jen viditelné části)
- **Měřeno 13. 11. 17:16 (Míša, tablet, 3D 75 %, Game Turbo „Výkon“).** p50 vše / bez postav / bez animace / chůze LOD /
  vše znovu: tvrz-cesta 24/27/35/31/32, louka 24/29/30/28/30, les 30/29/32/28/26, ves 34/23/27/28/30, mlýn 21/22/27/26/28,
  ves-vjezd 42/33/27/27/42, ves-dvory 32/38/36/38/33, hostinec 31/19/29/30/33, věž 27/19/31/33/35.
- **Šum větší než hledaný vliv:** stejná varianta vše × vše znovu se liší až o 8 ms (tvrz-cesta 24/32, věž 27/35); celý
  běh pomalejší než 0.999991 (jiný režim Game Turbo / teplota – NEOVĚŘENO). „Bez postav“ tentokrát ≈ vše → vliv postav
  z 0.99999/0.999991 (+8–11 ms) se NEPOTVRDIL ani nevyvrátil.
- **Naměřená souvislost:** ves-vjezd 42 ms při 692 kresleních (vše, vše znovu) × 27 ms při 561–563 (bez animace, chůze
  LOD). Varianty „vše“ a „bez postav“ mají o ~100–130 kreslení víc než ostatní na většině úseků – PROČ NEOVĚŘENO
  (podezření: louka/stíny po startu trasy, ne postavy). Ves potřebuje 560–690 kreslení (tvrz ~330) → sloučení staveb vsi.

### 0.999993 – vydáno 13. 11. 17:58 (částice, drobné díly tvrze, předměty v domech)
- **Měřeno 13. 11. 19:46 (Míša, tablet, 3D 75 %).** p50 vše / bez postav / bez animace / chůze LOD / vše znovu: tvrz-cesta
  26/18/30/31/25, louka 27/18/27/24/22, les 31/19/25/22/21, ves 25/18/27/23/35, mlýn 17/20/24/20/20, ves-vjezd 25/22/27/24/29,
  ves-dvory 28/27/37/36/36, hostinec 21/18/25/28/22, věž 27/17/27/26/24.
- **Bez postav** zase −7..−9 ms (3 ze 4 běhů). **Bez animace ani chůze LOD nepomáhají** → cena postav NENÍ animace, modifikátory
  ani skripty; kreslení stejné → zbývá vykreslení skinovaných sítí postav (Compatibility/GLES3, Godot #88954) – podezření.
- Izolovaný test: PC (xvfb, gl_compatibility) N postav před kamerou – animované / zastavené / skryté; na trase varianta
  postavy_skryte (neviditelné, logika běží).
- **PC A/B 13. 11. (tools/mereni_postav.gd, 20 postav, llvmpipe):** nové modely 72/59/54 ms (animované/zastavené/statické),
  staré z 0.99998 75/63/56 ms → **nové modely VYVRÁCENY** jako příčina (aspoň na PC). Skinování ~10 % kreslení postavy.
  Další izolace na tabletu: varianty postavy_skryte / postavy_stoji. Pevných 30 FPS (výchozí) skryje cenu, dokud snímek < 33 ms.

### 0.999994 – vydáno 13. 11. 20:44 (sukně ve stehnech, kuchařky, trhání u stromu)
- **Měřeno 13. 11. 21:29 (Míša, tablet, 3D 75 %, bez omezení 30 FPS – p50 až 17 ms = 60 FPS).** p50 vše / bez postav /
  post. skryté / post. stojí / vše znovu: tvrz-cesta 26/30/29/17/30, louka 27/29/32/17/26, les 32/25/26/18/26, skály 33/25/30/17/26,
  ves 27/22/28/17/22, mlýn 32/20/25/17/20, ves-vjezd 29/33/31/17/36, ves-dvory 29/31/37/20/32, hostinec 27/27/30/17/24, věž 26/22/24/19/27.
- **Naměřený vliv (dosud nejsilnější):** „post. stojí“ (Lide zastavené, postavy vidět) = 17 ms skoro všude, sousední varianty
  (skryté, vše znovu) 20–37 ms → **cena postav je výpočet podstromu postav (~9–12 ms), ne kreslení** („skryté“ ≈ vše).
  Skripty (skr) jen 3–6 ms → většina mimo měřené skripty. Podezření: přepočet kostry (Skeleton3D + skin) se spustí, když
  kostrou hne cokoli – animace, LookAt hlavy, nohy IK, úchop, řidič sukně, **pružina sukně (SpringBoneSimulator3D – vypínač
  „modifikatory“ ji nezahrnoval)**; proto jednotlivé vypínače dřív nic neukázaly. Izolace: tools/mereni_postav.gd režimy
  anim_bez_modif / kostry_stoji (PC) → pak varianta trasy.
- „Bez postav“ (2. v pořadí) jen −2..−5 ms, méně než „stojí“ – nesedí (mělo by být ≤); teplo/pořadí (FPS z 60 na ~40 od 1033 s
  v záznamu panelu) – šum pořadí NEOVĚŘENO.
- Špička **2230 ms ve vsi (439, 802), vše znovu:** fyzika 243 ms, skripty 6, proces 2209 ms → mimo skripty i krok fyziky;
  podezření: synchronní načtení / stavba kolizní sítě při přiblížení (predmety kolize glb, load v hlavním vlákně) – NEOVĚŘENO.
- Hostinec 226–266 ms (bez postav, skryté) – přepnutí interiéru (dříve predmety 96 ms) – NEOVĚŘENO.
- **Obloha (PC, tools/mereni_oblohy.gd):** změna parametrů oblohy každý snímek 24 ms proti 7 ms (radiance QUALITY 128);
  daylight je měnil každých 0,25 s → opraveno prahem (kvalita.json obloha_prah 0,004, jako Puchart). Vliv na tabletu NEOVĚŘENO.
- **Les (PC, tools/mereni_prvni.sh, studená keš):** po předehřátí v lese (-85, 214) jen 2 programy (41 ms) → zásek 1,8 s v lese
  sestavením shaderů NEVYSVĚTLEN (hypotéza odložena).

### 0.999995 – vydáno 13. 11. (postavy bez fleků = nový import, hnědé dřevo, déšť, obloha jen při změně, sukně/hlava jen u nejbližších)
- Trasa: varianty vše / postavy stojí / déšť / vše. Rozdíl vše × stojí = co postavy ještě stojí po omezení modif_max. NEOVĚŘENO NA ZAŘÍZENÍ.
- **Měřeno 14. 11. 09:49 (Míša, tablet, 3D 75 %).** p50 vše / post. stojí / déšť / vše znovu: tvrz-cesta 27/19/32/30, louka 26/17/31/30,
  les 32/19/28/28, skály 27/27/30/27, ves 19/19/25/22, mlýn 20/20/20/21, ves-vjezd 26/30/35/33, ves-dvory 37/26/30/30,
  hostinec 20/17/18/25, věž 19/24/25/23.
- **Naměřený vliv – postavy:** ve vsi, mlýně, hostinci vše ≈ stojí (dřív +9–12 ms). Proti 0.999994 (vše): ves 27→19, mlýn 32→20,
  hostinec 27→20, věž 26→19. Omezení modif_max (řidič sukně 4, hlava 6) + skryté postavy bez modifikátorů = OVĚŘENÁ OPRAVA
  ceny postav na tabletu (aspoň ve vsi; tvrz-cesta/louka/les v 1. průjezdu ještě vše > stojí – viz níže).
- **Déšť:** +0–3 ms p50 (déšť × vše znovu). Začátek deště: zásek 357 ms, skripty 109 ms (`zahrati dest/tvrz-cesta`) = sběr
  materiálů přes celou scénu (pocasi._sber_materialu, find_children 26 tis. uzlů) → rozložit do snímků.
- **1. průjezd horší než v 0.999994** (vše p95 tvrz-cesta 70, louka 56, les 68, skály 58; >40 ms 55–67 snímků; 0.999994: 31–43),
  2. průjezd (vše znovu) p95 37–49. PODEZŘENÍ: změněný kód shaderů zem/zdivo/skála/textura (dest_mokro, AO) = keš shaderů
  po aktualizaci neplatí, tablet sestavuje znovu. Ověřit: 2. spuštění téže verze. NEOVĚŘENO.
- Špička ves-vjezd 206 ms (fyzika 34) u (374, 749) = u krčmy (r. 125, cesty ke krčmě selhávají).
- Teplo: panel 50 → 30 FPS během trasy (stejně jako dřív).

## 0.999996 (commit 4f6de2ba, 14. 11. 14:50) – měřeno 14. 11. 15:53 (Míša, tablet, 3D 75 %)
Změny proti 0.999995: změna činnosti postav 1/snímek (PC lide_zasek 10,8 ms, dřív 13–14), řetěz mříže jen použité články,
déšť: sběr materiálů po částech (PC; tablet měřil 357 ms zásek na začátku deště v 0.999995), ves zesvětlená (textury, bez vlivu na výkon – NEOVĚŘENO).
Čeká na Měřicí trasu (varianta dest).

### 0.999996 – test záseků u hostince (−62, 969), Míša 14. 11. (zrušen po 2 variantách)
| varianta | p50 | p95 | p99 | max | > 50 ms |
|---|---|---|---|---|---|
| fyzika 60 Hz (výchozí), volně | 32 | 41 | 45 | 48 | 0× |
| fyzika 30 Hz, volně | 33 | 69 | 80 | 91 | 204× (91 ms u −63/962) |

Naměřený vliv (ne příčina): fyzika 30 Hz při snímku ~33 ms střídá 0 a 2 kroky fyziky v jednom snímku → špičky 69–91 ms;
60 Hz dělá rovnoměrně 2 kroky. Výchozí zůstává 60 Hz (main.gd fyzika_i 1). Hostinec 32 ms p50 = kolem 31 FPS.

### 0.999996 – Měřicí trasa 14. 11. 15:53 (sestavení fc315402, manifest fd569111)
p50 vše / post. stojí / déšť / vše znovu (v závorce 0.999995): tvrz-cesta 32/30/40/29 (27/19/32/30), louka 24/28/29/31
(26/17/31/30), les 21/27/30/29 (32/19/28/28), skály 23/26/32/34 (27/27/30/27), ves 22/23/21/20 (19/19/25/22),
mlýn 20/21/23/23 (20/20/20/21), ves-vjezd 23/21/33/35 (26/30/35/33), ves-dvory 27/38/29/23 (37/26/30/30),
hostinec 20/17/24/23 (20/17/18/25), věž 27/25/33/36 (19/24/25/23).
- **Ověřená oprava:** začátek deště bez záseku (déšť/tvrz-cesta max 86 ms; 0.999995: 357 ms, skripty 109) – sběr po částech.
- **Ověřená oprava:** ves-vjezd bez špičky (max 33 ms; 0.999995: 206 ms u krčmy).
- **Nová špička (naměřeno, příčina NEZNÁMÁ):** ves-dvory u (421–423, 871–874), 8,8 m od domu usedlosti 6: 329 ms
  (1. průjezd) a 2 431 ms (vše znovu), skripty 4/11, fyzika 3/2, kreslení 337/422 → čas mimo skripty a fyziku (GPU/ovladač
  nebo načítání). PODEZŘENÍ 1: první vykreslení vnitřku domu (rozpocty ves_vnitrek, předměty jen zblízka) = sestavení
  shaderů v ovladači. PODEZŘENÍ 2: něco nového v okolí usedlosti 6 (kurník posunutý podél zdi, ohrady). Test: varianta
  trasy s vypnutým vnitřkem domů + zastavení u (421, 871).
- **Teplo:** konec trasy (vše znovu) 19–25 FPS, průměr snímku 43–51 ms (1. část 26–40) – tablet se zahřál.
- 1. průjezd (vše) tvrz-cesta p95 72, max 525 (louka 979 ms zahřátí) – stejně jako 0.999995 (keš shaderů?).

## 0.999997 (commit e129384d, 14. 11. 19:00) – NEOVĚŘENO NA ZAŘÍZENÍ
Nové: kovárna (65 tis. troj.) a krčma do L (172 tis.) ve vsi, úsek trasy krcma-kovarna, varianta bez_vnitrku_vsi
(místo postavy_stoji). Hlášení záseku nově „shadery +N“ (sestavené programy v tom snímku). Čeká na Měřicí trasu.
