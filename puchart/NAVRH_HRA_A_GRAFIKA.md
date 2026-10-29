# Puchart – nová hra na základu Havrana (grafika a hra, bez příběhu)

Zdroj: PDF „Puchart – Oldřich, Boček a kluk ze vsi“ (pracovní návrh 1.0, 29. 10. 2026) + stav Havrana
(větev `claude/new-session-0dtk58`, vydání 0.995, `docs/rozpracovane/stav_29_10_vecer.md`, `docs/stav.md`).
Příběh tu záměrně neřeším – jen svět, grafiku, stavbu a herní systémy.

## 1. Jednou větou

Nový projekt (Godot 4.4.1 Compatibility, Xiaomi Pad 8) se **skutečným terénem Potštátska z DMR 5G**, dvojhradem Puchart
z **kamenné a šindelové stavebnice Havrana**, vsí, mlýny a lesem z **hotových modelů, materiálů a pravidel Havrana** –
ale svět se **peče předem do dlaždic**, ne staví při startu. To je hlavní poučení z Havrana.

## 2. Co z Havrana převzít (ověřené, funguje)

| Oblast | Co je hotové v Havranovi | Jak to použít v Puchartu |
|---|---|---|
| **Pravidla v datech** | `pravidla/svet/*.json` (druhy, plochy, cesty, voda, rozpočty, vztahy), `pravidla_sveta.json` `pasma` | Převzít formát 1:1. PDF chce totéž („data místo rozesetých čísel v kódu“). Začít čistě – v Havranovi je část jen „krok B, nezapojeno“. |
| **Pevné pořadí stavby** | terén → cesty → budovy → voda → vegetace → předměty, zákaz záplat | Stejně. Odpovídá pořadí v PDF (krok 5 terénu: průchody, pole, náhony, až potom vegetace). |
| **Test smyslu + hlídači** | `tools/test_smyslu.py`, mapa stavby, test `zasazeni`, `stavby_na_zemi` | Převzít celé. Každá chyba od člověka = nová kontrola. |
| **Pokládání na terén** | `svet.pata_lom`, `polozit_na_body` (náklon vozu), budovy s podezdívkou a `dum_teren` | Převzít; v Puchartu poběží v pečení, ne na tabletu. |
| **Stavebnice zdiva a střech** | `blender/kit.py`, `fort.py`, `palace.py`, `zdivo.gdshader`, šindel `tools/sindel_tex.py`, portály, dveře na pantu | Základ obou hradů (viz kap. 4). Lomové zdivo, kvádrová nároží, omítka, šindel, ochozy – vše už existuje. |
| **Materiály** | Poly Haven / ambientCG (`blender/textures.py`), ETC2 bez horních mip úrovní (`tools/textury_tablet.py`), 1024/512 px | Stejná sada a limity – PDF chce 512–1024, 2048 jen dominanty. Havran to už dodržuje. |
| **Vegetace** | ~70 modelů v `modely/nove` (dub, buk, lípa, olše, vrba hlavatá, jedle, smrk, bříza, borovice, trnka, hloh, šípek, bez, kapradí, kopřiva, rákos, orobinec, mech…), každý strom s `_daleko` verzí, impostory (`blender/impostory.py`, `impostor.gdshader`), louka ve vrstvách (`louka.gd`, `stebla.gdshader`), stanoviště (`druhy.json`) | Převzít celé. Druhy sedí i na Moravu (Oderské vrchy: buk, jedle, smrk výš; olše a vrby u Veličky). |
| **Voda** | `koryto.gd` (nárazový/vnitřní břeh), `nadrz.gd`, `voda.gdshader`, `reka.gdshader`, mlýn s náhonem a lednicí, `mlyn_kolo.gd` | Údolí Veličky a Kouteckého potoka, dva mlýny. Pozor na otevřené chyby 0.994 (schodovité okraje vody u soutoku). |
| **Ves** | `vesnice.py`, `ves_domy.py`, ves B (dvorce: stodola, kůlna, sad, živý plot – připravený patch) | Kyžlířov a Boňkov postavit rovnou podle „ves B“ (dvorce), ne podle staré Lhoty. Domy přizpůsobit Moravě (viz kap. 5). |
| **Předměty** | 336 balíků `p_*` (kovárna, nádobí, nářadí, vozy, sudy, bedny, zbraně…) | Kovárna, sklady zásob, nádvoří – skoro vše hotové. |
| **Postavy** | Quaternius CC0 + dobové oblečení 1393, 3 hrdinové + 9 NPC (≤ 8 k troj., 2×512), UAL animace, mrkání, `postava_sklada.gd`, `lide.gd` | Kluk ze vsi = upravený „Jan mladší“; Oldřich, Boček, písař, ozbrojenci, kovář, mlynář = nové kombinace ze stávající skládačky. Šlechtický oděv (Boček) je jediný nový kus. |
| **Zvířata, kůň** | `zvirata.gd`, `kun.gd`, `kun_zivy.gd`, jízda (`jizda.json`) | Bočkův doprovod na koních, povozy se zásobami. |
| **Světlo, zvuk** | `daylight.gd`, `sky.gdshader`, 100+ zvuků (les, ves, potok, kovárna, zvířata), 14 skladeb | Převzít. Léto 1393 = jedna sada počasí na začátek. |
| **Ovládání a UI** | dotyk + Xbox (`pad.gd`), `menu_hrace.gd`, mapa, deník | Převzít. |
| **Diagnostika** | `diag.gd` (panel, záseky > 40 ms s příčinou), testy `kresleni_ab`, `mapa_vyhledu`, `TVRZ_MERENI` | Přesně to, co PDF chce v kap. 13. Převzít a od prvního dne měřit na tabletu. |
| **Vydávání** | `tools/vydani.py`, balíky `data/*.pck`, opravné balíky `z_*`, `tools/beh.sh` | Převzít; nový podpisový klíč a nové ID balíčku (jiná hra). |

## 3. Co z Havrana NEpřevzít (a proč)

1. **Stavbu světa při startu.** Havran: koryto terénu 36 s, rostliny 27 s, svět 83 s, hra běží 110 s; halda 1,26–1,45 GB
   (cíl 1,25). Puchart má obálku 5×7 km = **~20× plochu Havrana** (1,1×1,6 km). Tím se to nedá zvětšit.
   → Vše (terén, cesty v terénu, rozmístění rostlin, sloučení sítí) **péct v Blenderu/nástrojích do dlaždic**, tablet jen načítá.
   PDF krok 7: „Tablet nemá za chůze stahovat mapy ani přestavovat celý svět.“
2. **Půdorys tvrze Havran a Posázaví/Český ráj.** Puchart má skutečnou skálu a dvojhrad; pískovcové skalní věže
   (`skala_*.glb`) na Potštátsko nepatří (PDF výslovně). Použít jen jako výchozí tvary pro ruční skalní hranu, s jiným
   materiálem (droba/břidlice Oderských vrchů – `balvan_droba_1`, `kamen_droba_1` už existují).
3. **Nedotažené „krok B“ věci** (dvě různé hranice světa, čísla v kódu, `zapojeno: false`). V novém projektu od začátku jen data.
4. **Stíny přes celou scénu a domy po jednom.** Měření Havrana: stín slunce 337–471 kreslení, domy vsi 420, ves 1205 kreslení.
   → Od začátku: domy sloučené po dvorcích podle materiálu, stíny jen 40 m, impostory pro vše za 100 m.

## 4. Stavba dvojhradu z Havranovy stavebnice

Pořadí podle PDF kap. 6, s tím, co už máme:

| Krok PDF | Puchart | Havranův díl |
|---|---|---|
| 1. Zdivo, příkopy, skála nad terénem | půdorys z Archeologického atlasu [2] nad DMR 5G, míra jistoty v `rekonstrukce.json` | `kraj.py` (pásma terénu 1 m u hradu), příkop z `nadrz.gd` |
| 2. Jednoduché objemy v metrech, projít hráčem | šedé objemy, ověření zásobovací cesty a spojnice | `rychle_testy.sh` (průchod, `stavby_na_zemi`) |
| 3. Střechy a hmoty paláců | přední: větší palác + obranná stavba; zadní: **hranolová věž** + palác | `palace.py` (kamenné přízemí, hrázděné patro, šindel), věž z `fort.py` (kamenný dřík, bedněné patro na krakorcích) |
| 4. Místnosti a úseky k načítání | síň, obytná komora, sklad, kuchyně, strážnice | `portaly.gd` + `predmety.gd` (interiéry jen uvnitř) |
| 5. Portály, trámy, omítka, vrata | | dveře ve 3 úrovních (PLAN E2), lomený portál, kování |

Modulární sada (PDF): zdi 2 a 4 m, rohy, ostění, sklony střech, trámy, schody → je to `kit.py`; doplnit jen
díly „usazení na skálu“ (pata zdi podle skutečné skály, ne rovná podezdívka).

## 5. Co je potřeba nově (Havran to nemá)

1. **Terén z DMR 5G** (ČÚZK, otevřená data, uvést zdroj): výřez, souřadnice S-JTSK → lokální metry, odstranit novodobé
   zářezy (silnice, náspy, lomy), historické průchody. Nástroj: `tools/dmr_do_terenu.py` (GDAL/rasterio → výšková mřížka
   → Blender `kraj.py`).
2. **Dlaždice a streamování**: dlaždice např. 256 m (návrh, změřit), 3 úrovně (1 m blízko / 5 m / 25 m obzor – stejná
   pásma jako `generovani.json`), přednačítání s hysterezí (PDF kap. 9). Havran má jen planovač rostlin (115/145 m) –
   rozšířit na celé dlaždice.
3. **Skalní hrana a převisy** jako samostatné modely (výšková mapa je neumí) – z fotek Pusté skály / Puchartu.
4. **Moravské venkovské domy 1393**: roubené a hliněné chalupy s doškem; havranovské domy upravit (dřevo, doška, méně
   kamene). Žádné cihly, žádný štěrk (pravidlo Havrana platí).
5. **Šlechtický oděv a doprovod** (Boček): barvený sukno, plášť, ozbrojenci s kroužkovou košilí (předmět `p_kosile_kruzkova` existuje).
6. **Katalog rekonstrukcí** (PDF: „rozhodnutí zapisovat do katalogu“): `pravidla/rekonstrukce.json` – každý díl má
   DOLOŽENO / REKONSTRUKCE / NÁVRH a zdroj [1]–[15].

## 6. Herní systémy (bez příběhu)

Převzít z Havrana a jen přenastavit:
- **Chůze, jízda na koni, povoz** (`player.gd`, `kun.gd`, `jizda.json`) – zásobovací cesta mezi hrady je jádro mapy.
- **Zásoby a hospodářství**: sklad, oves, dříví, mouka z mlýna, kovárna (palivo + odběratelé). Havran má potřeby a
  zásoby z položených předmětů – rozšířit na tok zboží ves → mlýn → hrad (PDF: „sídla nesmí být dekorace bez obživy“).
- **Lidé s denním rozvrhem** (`lide.gd`): správce, stráž, mlynář, kovář, vesničané – práce, příchod, pozdrav,
  odpočinek, reakce na hráče (PDF krok F). Prvních 10 NPC blízko hráče, pak 15.
- **Stav světa podle událostí** (návštěva pána: stráže, přístup, ceny) – obecný systém příznaků z Havrana
  (`pro_programatora.md`: příznaky, spouštěče `vstup_do_oblasti`, `cas`…) bez konkrétního příběhu.
- **Rozhovor s volbami, deník, mapa, menu hráče** – hotové.
- Souboj až později, jak říká PDF („boj je možnost“).

## 7. Rozpočty – PDF vs. změřený Havran

| | PDF / projekt | Havran (změřeno) | Závěr |
|---|---|---|---|
| FPS | 30 (p95 ≤ 40 ms) | 20–30 ve vsi | od začátku měřit p95 |
| Kreslení | (Havran: ≤ 1500, cíl < 700) | ves 1205, hostinec 1000–1248, krajina < 650 | slučování po dvorcích, stíny 40 m |
| Trojúhelníky | (≤ 2,5 M) | 2,46–3,13 M v nejhorších pohledech | impostory od 100 m |
| Paměť procesu | 1,25 GB | halda 1,26–1,45 GB | pečené dlaždice, uvolňování |
| Načtení | – | 83–110 s | cíl < 20 s (nic se nepočítá na tabletu) |
| Textury | 512–1024, 2048 dominanty | 1024/512, ETC2 | stejné |
| MSAA, screen texture | nikdy | nikdy (pády 0.58–0.59) | stejné |

## 8. Pořadí práce (PDF kap. 12: KRÁSA → FUNKCE → POSTAVY)

| Krok | Obsah | Co se vezme z Havrana | Hotovo, když |
|---|---|---|---|
| **0. Projekt** | nový Godot projekt, nové repo/větev, kopie systémů z kap. 2 (ne fork celé hry) | `scripts/`, `shaders/`, `pravidla/`, `tools/` výběrově | prázdný svět se spustí na tabletu, diag panel běží |
| **A. Podklady** | DMR 5G výřez, souřadnice, vodní síť, sídla, cesty jako vrstvy | formát `lokace.json`, `cesty.json`, `voda.json` | sedí hradní ostroh, vody a cesty |
| **B. Hmoty světa** | **první hratelný výsek ~2×2 km**: oba hrady (objemy), spojnice, Kyžlířov, údolí Veličky s mlýnem; zbytek obálky jen obzor 25 m | `kraj.py`, `kit.py`, test průchodu | celá síť cest průchozí |
| **C. Podoba krajiny** | les, louky, pole, voda, ves podle pravidel | vegetace, louka, `druhy.json`, test smyslu | prohlídka 5 stálých míst (hrad, les, voda, ves, vyhlídka) |
| **D. Dálka a načítání** | dlaždice, impostory, LOD, 3 vyhlídky (ochoz, skalní hrana, mez nad údolím) | `impostory.py`, `_daleko` modely | vyhlídky bez děr a záseků |
| **E. Funkce** | vrata, zásoby, mlýn, kovárna, povoz | dveře, `mlyn_kolo.gd`, kovárna | každá funkce změřená |
| **F. Lidé** | správce, stráž, mlynář, kovář, vesničané; pak návštěva | postavy Quaternius, `lide.gd`, kůň | 10 NPC u hráče v rozpočtu |
| **Pak** | rozšiřovat po buňkách (jih k Olšovci…), detail hradů | | |

Každý krok končí měřením na tabletu (PDF kap. 13: stejná trasa hrad / les / voda / vyhlídka, 30 s panel / 30 s FPS / 30 s panel).

## 9. Doporučení

- **Nový projekt, ne přestavba Havrana.** Havran nechat jak je (0.995); Puchart si z něj bere knihovnu: modely, materiály,
  stavebnici, pravidla, testy, postavy, zvuky. Sdílené zdroje přes balíky `.pck` / větev `assets`, ne kopií velkých souborů.
- **Svět péct, ne počítat na tabletu** – to je jediná zásadní architektonická změna a bez ní 35 km² nepůjde.
- **Začít výsekem 2×2 km** a ukázat ho na tabletu dřív, než se obálka 5×7 km začne plnit. Obálka zůstává jako obzor.
- Otevřené body před stavbou hradů (z PDF kap. 15): přesná hranice mapy, míra dochování obou hradů, historické přístupy.

## 10. Otázky pro Míšu

1. Nové repo (např. `puchart`), nebo nová větev v `tvrz-claude`?
2. Souhlas se začátkem výsekem ~2×2 km (oba hrady + Kyžlířov + Velička s mlýnem)?
3. Postavy: zůstat u stylizace Quaternius (schválená v Havranovi), nebo jít realističtěji?
