# Plán dalších míst (ne chyby – nové části světa)

Míša 9. 11.: „když jsme čekali na reset, měli jsme připravenou spoustu věcí jako osadu, hospodu, hájovnu… máš to v tabulce?“
Tabulka chyb (`docs/chyby.md`) je jen pro vady. Nová místa jsou zde, každé s rešerší a stavem dokladu.

| místo | stav | podklad | poznámka |
|---|---|---|---|
| Ves Předhradí / „Předhradsko“ (1547 pustá) | plán, poloha doložená stopami | GC80T08 (`docs/hrady_podle_kreseb.md`): kamenné hrázky políček ~250 m SZ podél žluté + 250 m SV, relikty nedostavěného příkopu předpolí s valem; DMR 5G lokální reliéf: rovnoběžné čáry na plošině SZ od hradu A | ves na plošině SZ od hradu A podle hrázek v DMR; cesta do vsi z hřebenové cesty (ne z údolí – cesta k hájovně vede na J do údolí, Míša 10. 11. se ptala) |
| Krčma u obchodní cesty | rešerše hotová | `docs/reference/reserse_mosty_krcma.md` (Richterová 1999) | krčmy na křižovatkách cest a u brodů, nálevna nebo zájezdní hospoda; poloha NAVRH u cesty údolím |
| Hostinec U Tlustého Jana | rešerše hotová | `docs/reference/reserse_tlusty_jan.md` | dům z r. 1710 (zahradnická usedlost) – v r. 1393 nestál; jen jako dnešní orientační bod |
| Mlýny na Veličce | podklad | `docs/reference/reserse_tlusty_jan.md` (11 mlýnů Boňkov–Potštát, 4 ve skalním městě) | doložení pro rok 1393 NEOVERENO – před stavbou rešerše |
| Hájovna | bez dokladu | `docs/reference/reserse_tlusty_jan.md` | NEOVERENO, zdroj nenalezen – stavět jen jako NAVRH po schválení |
| Boňkov (dvorce) | plán | `docs/predani.md` bod 3 | dvorce jako ves B Havrana |
| Skalní město | plán | úkol 20, `docs/reference/osm_ns_skalni_mesto_6631727.json` | skály podle DMR a fotek, ne z hlavy |

Pořadí (Míša): nejdřív dodělat seznam chyb a vydat, pak místa v pořadí výše.

## Cesty ves – hrad – údolí – hájovna (Míša 10. 11.: „můžou být obě?“) – ověřeno v DMR 5G (lokální reliéf)
- Ves Předhradí: na plošině ~300 m SSZ od hradu A jsou v reliéfu pravoúhlé linie (hrázky/meze) – sedí na popis GC80T08.
- Spojení existuje bez vymýšlení: ves → hlavní cesta / hřebenová k hradu A → hrad B → pěšina z B dolů k Veličce (OSM/žlutá) → údolní cesta → cesta k hájovně.
- Chyběl jen spoj cesty k hájovně s údolní cestou (50 m přes Veličku; dnes most s červeným zábradlím, Street View hajovna_01) – doplněn.
- Úvoz z vsi přímo do údolí v DMR nevidím (les = triangulační artefakty, starý úvoz nerozpoznatelný); boční údolíčko SZ (630 m, 15,6 %) – Míša 10. 11.: NESTAVĚT.
- Na plošině JZ za Veličkou (u cesty k hájovně) jsou v reliéfu jasné úzké souběžné pásy polí (plužina) – patří spíš k Olšovci/Boňkovu, ne k Předhradí (NEOVERENO).

## Příprava staveb 11. 11. (Míša: „připrav import staveb – vesnice dle pozůstatků, mlýn vodní, hospoda, hájovna“)
- Modely z Havrana: `nastroje/stavby_z_havrana.sh` → `hra/modely/stavby_h/` (domy.glb: Dum1, Dum2, Rychta, ChyseKura,
  ChysePrkna + domy_stredni.glb; mlyn.glb + mlyn_lod1.glb). Textury albedo 1024 / normála 512.
- Kandidátní místa a doklady: `pravidla/svet/mista.json` (stav KANDIDAT – stavět až po snímku a schválení).
- Mlýn: kandidát u tečkovaných obrysů na vojenské mapě 1:25 000 (~500 m SZ od hradu u silnice podél Veličky) – legendu
  mapy vyžádat; spád pro kolo ověřit v DMR (Havran tools/krok_b/mlyn_misto.py).
- Krčma: křížení cesty Veličkou s cestou údolím Kouteckého potoka pod hrady (most a brod).
- Hájovna: konec cesty k hájovně u Boňkova (Míša: hájenka je i na vojenské mapě).

## Usedlosti a pole Předhradí (Míša 11. 11.: „nemají tam být i hospodářské budovy, ploty a pole?“)
- Převzít z Havrana blender/vesnice.py: barn (stodola/chlév), picket_fence a rail_fence (laťový a proutěný plot),
  roofed_gate a wicket (krytá vrata, branka), garden (zelí, květiny), well (studna), dvůr (yard_dirt); z předmětů Havrana
  stodola, stodola_mala, kolna, kurnik, zebrinak, drevo_hromada.
- Pole: Havran docs/rozpracovane/reserse_pole_kcd2.md + pravidla/svet/plochy.json pole („kousky přímo za vsí, pár úzkých
  lánů mezi mezemi a remízky“), model blender/zdroje/psenice.glb; lány za humny podél mezí z DMR (relief SSZ od hradu A).
- Chýše (kůra, prkna): k lomu a uhlířům v lese – poloha až podle dokladu.
- Míša 11. 11.: „ať není každý dům nebo zahrada stejná“ – každá usedlost z vlastního semínka (Havran vesnice.py: pevné
  semeno, usedlosti se liší náhodou): typ domu, zrcadlení, natočení ±, odstín/varianta dřeva (Havran materiály mech,
  lišejník, vybledlé), stodola / malá stodola / kůlna, kurník jen někde, plot laťový / proutěný, vrata kryté / branka,
  zahrada jiný tvar a skladba (zelí, květiny, ovocný strom), lány různé šířky a plodiny (obilí, úhor, pastvina).
- Míša 11. 11.: „i nějaké stromy by ve vsi měly být“ – Havran vesnice.py village_trees / _homestead_green / dvorec_stromy:
  ovocné stromy v zahradách a u dvorů (jabloň, hrušeň, švestka), lípa/dub u studny nebo na návsi, keře (bez, líska) u plotů
  a na mezích, vrby u vody; jednotlivě a ve skupinkách, ne les.
- KCD reference (Havran docs/screens/kcd1/ves_1–6, Míša 11. 11. „mrkni na KCD“): ves hustá – usedlosti 15–20 m podél
  široké hliněné návsi s kolejemi, kameny a kládami (ne úzká cesta); na usedlost dům + 1–2 hospodářské stavby (otevřená
  kůlna se sedlovou střechou, stodola, chlév), dvůr; ploty laťové do ulice, proutěné kolem zahrad, žerďové kolem pastvin,
  krytá vrata; stromy jednotlivě mezi domy (lípy, ovocné), les až za poli; střechy doškové světle šedohnědé a šindel
  stříbřitý, zdi bílé omítky nebo ohlazené roubení; v ulici vozy, sudy, hranice dřeva, lavice u domů.

## Ves podle KCD – stav 12. 11. (Míša: „dodělej plánovanou vesnici dle KCD“, „přesně pestrost“, krčma a hájovna „podle skutečnosti“)
**Rešerše (pořadí Havran → KCD → internet):**
- Havran `blender/vesnice.py`: usedlost = chalupa štítem do návsi, dvůr na straně vchodu, laťový plot do ulice v linii štítu
  s krytými vraty 3 m (dvorní strana) a brankou 0,9 m (zahradní strana), boční/zadní ohrada žerďová, zahrádka mezi stěnou
  a bočním plotem (zelí, květiny), hranice dřeva u zadního štítu, sudy u stěny, vůz na dvoře, studna na návsi.
  `pravidla/svet/lokace.json ves.dvorec`: stodola 9,9 × 7,7 m napříč za dvorem 4,5 m za domem od boku 0,8 m, kůlna 7,7 × 4,6 m
  na stejné čáře (mezera 0,6 m), sad jabloní za plotem, zeleň u stavení (Dohnalová & Dohnal 2023: strom u vjezdu, na dvoře,
  u stodoly). `svet.gd`: stodoly s vraty, kurník u zdi chalupy na straně dvora. Modely: předměty stodola, stodola_mala,
  kolna (+ _stredni, _kolize), kurnik, plutek, zahon_*, hranice_dreva, zebrinak…; jabloň ze z_rostliny.
- KCD (Havran `docs/screens/kcd1/ves_1–6`, `ref_kcd2_ves_*`, `ref_kcd2_zahrada_plot`, `ref_kcd2_chalupa_vecer`,
  `docs/screens/reference/kcd1/01–20`, zde `docs/reference/kcd_vzhled`, `misa_12_11`): usedlosti těsně vedle sebe podél
  široké hliněné ulice/návsi, laťové ploty do ulice, krytá vrata, proutí kolem zahrad, žerďová ohrada kolem pastvin,
  otevřená kůlna bokem do dvora, stodola, dvůr udusaná hlína, stromy jednotlivě mezi domy, za vsí pruhy polí.
- Internet (archeologie zaniklých vsí Moravy): V. Nekuda (AH 1976) – usedlosti jednořadové a hákové, dvůr obestavěn ze
  dvou (jednořadové) nebo tří stran (hákové); Pfaffenschlag (2. pol. 13. st. – zánik 1. čtvrt. 15. st.): dvůr = trojdílný
  dům, dvě stáje, kolny, kovárna; ves Konůvky (Ždánický les) kol. r. 1400 ~19 usedlostí s hákovými půdorysy.
  Rozměry usedlostí v dostupných textech nenalezeny (NEOVERENO) – rozměry podle Havrana.

**Stavba:** pravidla `pravidla/svet/mista.json` „usedlosti“ (typy selska / krcma / hajovna, ploty, studna, pole, povrch,
lod – vše se zdrojem) → `nastroje/mista_rozmisteni.py` (každá usedlost z vlastního semínka: předzahrádka 0–2 m, dvůr
8,5–10,5 m, zahrada 4,5–6,5 m, velká/malá stodola, kůlna za dvorem / bokem / u zahrady, kurník, druh plotů a vrat,
2–6 záhonů, 1–4 jabloně, lípa u vjezdu, vůz, kupka, sudy, lavice, štípání; lány za humny 1–3 pruhy, orané / strniště /
úhor) → `hra/data/mista_stavby.json` → `hra/scripts/ves.gd` (hospodářské stavby, ploty a vrata stavěné podle Havrana,
studna, drobnosti a proutí přes BunkyKolem, stromy) a `nastroje/stavby_vegetace.py` (dvůr hlína, lány, parcela bez lesa).
Krčma (U Tlustého Jana, mezi silnicí 440 a svahem): stáj (malá stodola) bokem do dvora, kůlna na vozy, koryto pro koně,
vozy, sudy, lavice, lípa u vjezdu. Hájovna (Olšovec 44, u soutoku): kůlna-dřevník, hranice dřeva, štípání, kurník, zahrádka.
Snímky: `docs/screens/ves_kcd_*.png` (plán `ves_kcd_plan.png`).

| díl | jistota |
|---|---|
| poloha vsi Předhradí, krčmy, hájovny | DOLOZENO (GC80T08 + DMR; OSM/Míša 12. 11.) |
| skladba usedlosti (dům, dvůr, stodola, kůlna, ploty, zahrada, sad) | REKONSTRUKCE (Havran + KCD + Nekuda 1976) |
| konkrétní rozměry, počet a pořadí usedlostí, lány a plodiny | NAVRH |
| krčma: stáj bokem, kůlna na vozy | NAVRH (svah za domem) |
