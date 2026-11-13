# Brody: podklady z KCD a ze skutečných brodů (13. 11. 2026)

Rešerše pro nástroj, který tvaruje koryto a nájezdy cesty v místě brodu a sází kameny a vegetaci (`pravidla/svet/voda_hra.json` → `koryto.brod`). Míša 13. 11. napsala, že „brod není dobrý“ (k hájovně: cesta vede přes úzký příkop s hrbem).

**Značení zdrojů:** u každého čísla je uvedený zdroj. **NEOVERENO** znamená, že číslo nemá doložený zdroj a jde o návrh nebo o odhad podle obrázku. **ODHAD Z OBRÁZKU** znamená, že rozměr nikdo neměřil a odhadl jsem ho podle postav a koní na snímku.

---

## 1. Obrázky ve složce

### KCD (screenshoty jsou chráněné autorským právem Warhorse Studios; slouží jen jako interní reference, nešířit)

| soubor | co ukazuje | odkud |
|---|---|---|
| `kcd1_brod_vozy_valouny.jpg` | KCD1, oficiální screenshot. Vozy stojí v brodu přes širší potok nebo říčku. Na břehu je široká lavice oblých valounů, ve vodě leží jednotlivé velké balvany. Koně brodí s vodou po spěnku až nadprstí, tedy asi 0,2–0,3 m (ODHAD Z OBRÁZKU). Kolem je smrkový a listnatý les. | Steam, obchod KCD (app 379430), `https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/379430/ss_3c205f4c6b09f7838aa003cac2bdf3842629e50a.1920x1080.jpg` |
| `kcd1_brod_sazava_tight_spot.jpg` | KCD1, DLC Band of Bastards, úkol „A Tight Spot“: brod SZ od Sázavského kláštera. Valounová lavice na břehu přechází plynule do vody, tráva roste až k okraji štěrku. Ve vodě a na lavici leží jednotlivé balvany. Hnědý pruh hlíny vyjeté cesty vede přes lavici k vodě. | GamerGuides, `https://www.gamerguides.com/images/markup-img-full/17/149/KC_D_Ambush2.jpg.jpeg` (stránka `https://www.gamerguides.com/kingdom-come-deliverance/guide/walkthrough/dlc/band-of-bastards`). Polohu brodu potvrzuje wiki: `https://kingdom-come-deliverance.fandom.com/wiki/A_Tight_Spot` („Ford northwest of Sasau Monastery“) |
| `kcd1_brod_tight_spot_brodeni.jpg` | Tentýž brod, postavy stojí ve vodě. Voda sahá po kotník až polovinu lýtka, asi 0,1–0,25 m (ODHAD Z OBRÁZKU). Na protějším břehu je rákosí nebo vysoká tráva a nízké kameny. Obrázek má nízké rozlišení (480×270). | snímek z videa YouTube `fp5UIg1pooU` („Banda drani – W potrzasku“), automatický náhled `https://i.ytimg.com/vi/fp5UIg1pooU/hq2.jpg` (oříznutý černý pruh) |
| `kcd2_brod_bylany_kameny.jpg` | KCD2, úkol „The Fifth Commandment“: lesní brod u mlýna jižně od Bylan. Úzký potok, dno je tmavé a bahnité. Na krajích leží hranaté kameny, u brodu stojí velký balvan a přes potok leží padlý kmen. Les sahá až k vodě. | PowerPyx, `https://www.powerpyx.com/wp-content/uploads/kcd2-the-fifth-commandment-29.jpg` (stránka `https://www.powerpyx.com/kingdom-come-deliverance-2-the-fifth-commandment-walkthrough/`) |
| `kcd2_brod_bylany_mapa.jpg` | KCD2, herní mapa téhož místa. Cesta (světlá čára) kříží potok téměř kolmo a není u ní značka mostu. | PowerPyx, `https://www.powerpyx.com/wp-content/uploads/kcd2-the-fifth-commandment-28.jpg` |
| `kcd1_potok_breh_vesnice.jpg` | KCD1, oficiální screenshot. **Není to brod**, jen kontext břehu: hliněný nárazový břeh potoka, břízy, olše a kmen přes vodu. Tráva roste až k hraně břehu. | Steam, obchod KCD, `https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/379430/ss_01dea4f433b9dcf121a3120c6c36712dc136c63a.1920x1080.jpg` |

V KCD wiki jsou doložené tyto brody: KCD1 „A Tight Spot“ (SZ od Sázavy), KCD1 „Cold Steel, Hot Blood“ („Defend the ford!“, říční brod u mostu), KCD2 „The Fifth Commandment“ (brod u mlýna jižně od Bylan) a KCD2 „Unveiling“ (brod na cestě ze Zimburgu do Malešova). Zdroj: fandom wiki, texty stránek z API `kingdom-come-deliverance.fandom.com`. Snímek brodů z „Cold Steel“ a „Unveiling“ jsem nenašel.

**Pozor:** `voda_hra.json` uvádí jako zdroj brodu „KCD brody: cesta sjíždí mělkým zářezem do širokého mělkého toku (docs/reference/kcd_vzhled)“. Ve složce `kcd_vzhled` (misa_kcd_01–16, web_kcd1_broken_wheel_hostinec) **žádný brod není**, jsou tam hradby, nádvoří a cesty. Tento zdroj je proto NEOVERENO.

### Skutečné brody (Wikimedia Commons, volné licence)

| soubor | co ukazuje | zdroj, autor, licence |
|---|---|---|
| `real_wupperfurt_huckeswagen_uvoz.jpg` | **Nejbližší vzor pro vozový brod.** Dvoustopá polní cesta (dvě vyjeté koleje, mezi nimi tráva) sjíždí mírným zářezem do vody. Potok se v brodu rozlévá do šířky a vytváří mělkou plochu. Tráva roste až k vodě, na okraji leží několik plochých kamenů. Kolem stojí staré vrby a olše, za brodem je louka. | `https://commons.wikimedia.org/wiki/File:H%C3%BCckeswagen_H%C3%A4mmern_-_Wupperfurt_01_ies.jpg`, Frank Vincentz, 2008, **CC BY-SA 3.0** |
| `real_retlage_historicky_brod.jpg` | **Historický brod, chráněný jako „Bodendenkmal“ (archeologická památka)** „Furt über die Retlage“ (Detmold). Široká mělká voda nad písčito-štěrkovým dnem a několik balvanů. Nájezd je hliněný a štěrkový, rozšířený a mírný. Hned vedle vede lávka pro pěší. | `https://commons.wikimedia.org/wiki/File:Detmold-Pivitsheide_V.L_Furt_%C3%BCber_die_Retlage_01.jpg`, Grugerio, 2024, **CC BY-SA 4.0** |
| `real_sankenbach_brod_lavka_les.jpg` | Lesní horský potok (Schwarzwald, Baiersbronn). Pěšina přechází přes **dlažbu z plochých kamenů** na peřejnatém úseku, pod ní je malý stupeň. Kousek proti proudu stojí dřevěná lávka. | `https://commons.wikimedia.org/wiki/File:SankenbachFurtSkaliert_2013-11.jpg`, Mussklprozz, 2013, **CC BY-SA 3.0** |
| `real_menach_brod_lavka.jpg` | Lesní cesta (štěrk a hlína) sjíždí do brodu. Voda je hnědá a stojatá, dno bahnité, na vjezdu je pruh bahna. Vedle stojí dřevěná lávka a tráva roste až k vodě. | `https://commons.wikimedia.org/wiki/File:Menach_Furt.JPG`, Gomera-b, 2014, **CC BY-SA 3.0** |
| `real_reinshagener_bach_slapaky.jpg` | Pěšina přes potůček s **šlapáky z plochých desek břidlice nebo droby**. Kolem leží drť a úlomky stejné horniny. Nejpodobnější podloží Puchartu. | `https://commons.wikimedia.org/wiki/File:Remscheid_-_Reinshagener_Bach_02_ies.jpg`, Frank Vincentz, 2008, **CC BY-SA 3.0** (v kategorii Commons „Fords in Germany“) |

Licence CC BY-SA vyžaduje uvést autora a licenci, pokud se obrázek někde použije.

---

## 2. Co ukazuje KCD (vizuálně, bez měření)

- **Dno a břeh:** v KCD1 vede brod přes **lavici oblých valounů**. Štěrk sahá od vody na břeh 2–5 m (ODHAD Z OBRÁZKU, `kcd1_brod_sazava_tight_spot.jpg`, `kcd1_brod_vozy_valouny.jpg`). V KCD2 (Bylany) je lesní brod s tmavým bahnitým dnem a **hranatými kameny po stranách**, uprostřed je volný průchod (`kcd2_brod_bylany_kameny.jpg`).
- **Hloubka:** voda po kotník až polovinu lýtka, u koní po spěnku, tedy asi 0,1–0,3 m (ODHAD Z OBRÁZKU).
- **Šířka:** u říčkových brodů KCD1 je voda široká asi 10 m a víc (ODHAD Z OBRÁZKU). Brod v KCD2 je úzký lesní potok. Žádné číslo v KCD dohledané nemám (NEOVERENO).
- **Nájezd:** v KCD1 vede cesta po valounové lavici ploše k vodě, bez výrazného zářezu. V KCD2 vede lesní cesta k potoku kolmo, bez mostu (mapa). Úvoz u brodu jsem na snímcích KCD **nenašel** (NEOVERENO).
- **Lávka vedle brodu:** na nalezených snímcích KCD **není** (NEOVERENO pro jiné brody v KCD).
- **Šlapáky:** na nalezených snímcích nejsou. V KCD1 leží ve vodě jen jednotlivé balvany.
- **Vegetace:** tráva roste až k okraji štěrkové lavice, na protějším břehu je vysoká tráva nebo rákosí (`kcd1_brod_tight_spot_brodeni.jpg`). Okolo je les nebo stromy na břehu, padlé kmeny (KCD2).
- **Bahno, stopy kol:** na nalezených snímcích nejsou koleje u brodu zřetelné (NEOVERENO). Tmavé bahnité dno je vidět v KCD2.

## 3. Skutečné a historické brody: čísla

### 3.1 Archeologie a historie
- **Zlatá cesta, Obora u Tachova (12.–16. st.):** v nejzachovalejším úseku jsou „pozůstatky úvozů, mezí, hrází rybníků, brodů“. V plánu lokality je vyznačené „kamenité dno zpevňující cestu mezi potoky“ a fotka „Úvoz mezi brody přes Studenecký a Sklářský potok“. Zdroj: Archeologický atlas ČR, `https://www.archeologickyatlas.cz/cs/lokace/obora_tc_zlata_cesta.pdf` (Kuna a kol. 2014). Fotky tam nejsou s volnou licencí, proto je neukládám. Z toho plyne, že k brodům českých středověkých cest vedly **úvozy** a že cesta mezi potoky byla **zpevněná kamenem**. Rozměry zdroj neuvádí.
- **Brno, ul. Brněnská (Přehled výzkumů 66/2, 2025):** cesta přes podmáčený terén (asi 70 m) z „vodorovně položených klád či jejich dílů a desek vyztužených drobnými i většími kameny“. Brod se zde nepodařilo prokázat. Zdroj: `https://app2.ssc.avcr.cz/ARUB-prehled-vyzkumu/files/30644.pdf` (podle souhrnu z vyhledávání).
- **Evesham (Anglie), dlážděný brod:** odkrytý úsek je asi 12 m dlouhý a 4 m široký, primární dlažba 2,95 m. Na kameni jsou stopy kolejí. Datování není jisté (snad římské, ale „could equally date to any time before“ přeložení potoka v 18.–19. st.). Zdroj: `https://the-past.com/news/rare-ford-unearthed-at-evesham/`
- **Iden Green (Kent), římský brod:** dlažba z hrubě otesaných bloků, plocha 5,72 × 3,89 m. Zdroj: `https://www.kentarchaeology.org.uk/journal/101/roman-ford-iden-green-benenden` (podle souhrnu z vyhledávání).
- **Bidford-on-Avon, římský brod:** asi 22 m široký, kůly po 1,3 m, na nich štěrk a dlažba z vápencových desek („submerged causeway“). Jde o velkou řeku, pro Veličku to neplatí. Zdroj: `https://www.ourwarwickshire.org.uk/?p=44180` (podle souhrnu z vyhledávání).
- **Detmold, „Furt über die Retlage“:** brod chráněný jako archeologická památka, viz foto `real_retlage_historicky_brod.jpg`. Rozměry nemám (NEOVERENO).

### 3.2 Hloubka vody pro brodění
- Britská vojenská příručka (kolem r. 1900): nejvyšší brodná hloubka je pro **jízdu 4 ft (1,22 m)**, **dělostřelectvo (koňské potahy s koly) 2 ft 4 in (0,71 m)** a **pěchotu 3 ft (0,91 m)**. Zdroj: `https://heritage.christchurchcitylibraries.com/Archives/OSullivan/Clutterbuck/Diary/PDF/0050-033.pdf`
- US Army, tabulka 1-3 „Trafficability of Fords“: pěší mají nejvyšší hloubku 1,0 m, šířku nejméně 1,0 m za sebou a 2,0 m ve dvojstupu a nájezd do 100 % (1:1). Nákladní vozy mají nejvyšší hloubku 0,75 m, šířku 3,6 m a nájezd nejvýš 33 % (1:3). Kategorie dna: M bahno, C jíl, S písek, G štěrk, R skála, P dlažba. Zdroj: `https://armyengineer.tpub.com/EN5621/EN56210017.htm`
- Gu (2005) podle USFS: kvůli bezpečnosti provozu má být nejvyšší hloubka proudu přes brod 6 in (0,15 m). Platí pro motorová vozidla. Zdroj: Clarkin a kol., *Low-Water Crossings* (USDA FS 2006), kap. 4, `https://www.fs.usda.gov/eng/pubs/pdf/LowWaterCrossings/Lo_pdf/5_Chapter4.pdf`
- Občanská válka v USA: „maximum depth of water recommended in a ford is 30 inches“ (0,76 m). Je to tvrzení z fóra bez primárního zdroje, tedy NEOVERENO. `https://civilwartalk.com/threads/supply-wagon-dimensions.142300/`
- **Na Veličce (0,1–0,4 m)** je tedy brodné celé koryto pro pěší, koně i vůz. Brod nemusí vodu prohlubovat, jeho smysl je **mělké, pevné, ploché dno a sjízdné břehy**.

### 3.3 Nájezdy a šířka (návrhové příručky pro lesní a polní cesty)
- **Sklon nájezdu:** „Limit grades into the ford to 10 percent or less if possible.“ a „Where practical, 10 percent is the recommended maximum approach grade. Grades into and out of fords have been in the 15- to 20-percent range“ (to ale vyžaduje zpevnění). Zdroj: Clarkin 2006, kap. 4.
- **Svislé zakružení:** používat „vertical curve dip through the ford, sufficiently gentle not to catch the bumper or undercarriage“. Ostré svislé lomy jsou mezi „practices to avoid“. Zdroje: Clarkin 2006, kap. 4; Keller & Sherar, *Low-Volume Roads Engineering*, kap. 9, `https://www.fs.usda.gov/t-d/programs/forest_mgmt/projects/lowvolroads/ch9.pdf`. **To odpovídá Míšině stížnosti na „hrb“.**
- **Šířka vozovky v brodu:** „typically as wide as the normal roadway width, usually 10 to 12 feet“ (3,0–3,7 m). Zdroj: Clarkin 2006, kap. 4.2.
- **Poloha:** brod patří na rovný úsek toku a má vést kolmo k toku. Zdroj: Clarkin 2006, kap. 4.4.1. Má být tam, kde jsou „stream banks are low and where the channel is well confined“, na skalním nebo hrubém podloží, a ne v hluboce zaříznutém údolí, kde by byl potřeba vysoký násyp nebo příliš strmé nájezdy. Zdroj: Keller & Sherar kap. 9.
- **Příčný sklon brodu** je 3–5 % „outslope“ (po proudu). Zdroj: Clarkin 2006, kap. 4.2.
- **Dno brodu:** „large graded rock in the roadbed… Fill the voids with clean, small rock or gravel to provide a smooth driving surface“. Na dolní hraně brodu hrozí vymílání, proto se tam dávají kameny (riprap). Zdroj: Keller & Sherar kap. 9.
- **River Cole (UK, Manual of River Restoration Techniques 8.1, 1995):** tok s **korytem širokým asi 3 m**, tedy stejně jako Velička.
  - Brod je **„overwide“ asi 6 m** proti běžným asi 3 m, tedy 2× šíře koryta. Dno je zvýšené asi 0,3 m nad průměrné dno, aby voda přetékala mělce.
  - Zpevnění tvoří vrstva 0,4 m z kamene o velikosti 0,15 m, **vytažená po proudu jako mírně se svažující peřej („riffle“)**.
  - Nájezdy mají **sklon 1:6 (asi 17 %)** a jsou „smoothly contoured into the bank lines“, takže vznikly ploché svahy břehů.
  - Jiný brod tam vede šikmo, asi 15 m dlouhý přes 3 m koryto, v místě přirozené štěrkové lavice („point bar“) pod ohybem: „upland rivers where point bars and shoals of gravel often serve as crossing points“.
  - Zdroj: `https://www.therrc.co.uk/assets/pdfs/mot/final/8.1_Cole.pdf`
- **Poloha v podélném profilu:** peřeje jsou mělká místa, která se střídají s hlubšími tůněmi. Zdroj: Scottish Geology Trust, `https://geoguide.scottishgeologytrust.org/page/964` (podle souhrnu z vyhledávání). Brod tedy patří na peřej nebo štěrkovou lavici, ne do tůně. Středověký doklad této zásady nemám, takže pro středověk je to NEOVERENO, ale logika a příklad River Cole tomu odpovídají.
- **České lesní cesty:** podle vyhlášky 239/2017 Sb. se přechod malých toků na celoročních lesních cestách brody nezajišťuje. Brod je řešení pro sezónní cesty. Parametry brodu z ČSN 73 6108 jsem nezískal (norma je placená), takže NEOVERENO. Zdroj: `https://www.tzb-info.cz/docu/predpisy/download/V239-2017.pdf` (podle souhrnu z vyhledávání).

### 3.4 Co je vidět na fotkách skutečných brodů
- Cesta do brodu vchází **plnou šířkou**, bez zúžení. Voda se v brodu **rozlévá do šířky** a je mělká (Wupperfurt, Retlage).
- Koleje: dvě vyjeté stopy, mezi nimi tráva, až k vodě (Wupperfurt).
- Břehy u brodu jsou **snížené a rozevřené do trychtýře**, s travnatými zaoblenými hranami. Ostrá hrana ani práh nejsou vidět (Wupperfurt, Retlage, Menach).
- Dno tvoří štěrk, písek a jednotlivé balvany mimo jízdní stopu (Retlage). Dlažba z plochých kamenů se objevuje na peřeji (Sankenbach).
- Šlapáky jsou ploché desky místní horniny, položené kolmo přes tok (Remscheid).
- Lávka pro pěší vede hned vedle brodu, 0–10 m proti proudu (Retlage, Menach, Sankenbach). Jsou to **novodobé** lávky, takže pro rok 1393 NEOVERENO.
- Bahno je hlavně na vjezdu a výjezdu u vody (Menach). Jinde roste tráva až k vodě a na břehu stojí vrby a olše (Wupperfurt).
- Rákos u žádného z podhorských brodů na fotkách není. Rákos v KCD1 je u větší říčky.

---

## 4. Doporučení pro Puchart

Kontext: Velička je široká 2–3 m a hluboká 0,1–0,4 m. Dno tvoří droba a břidlice. Vozová cesta má `sirka_m` 2,8 m a povrch 3,6 m (`cesty_puchart.json`), pěšina 1,0–1,6 m. Současný brod: `polosirka_m` 3,0, `nabeh_m` 4,0, `hloubka_m` 0,12, `sklon_najezdu` 0,12, `prah_nad_hladinou_m` 0,55.

**Hlavní diagnóza.** Brod nemá být „úzký příkop s hrbem“, ale **mělká rozlitá plocha, do které cesta plynule klesá a z které plynule stoupá**. Tvar má mít tři části: **trychtýř → plochá mísa → trychtýř**. Ve svislém profilu nesmí být žádný lom, práh ani hrb (Clarkin 2006; Keller & Sherar kap. 9).

| parametr | doporučení | zdroj |
|---|---|---|
| Umístění | Rovný úsek toku, cesta kolmo k toku (odchylka do asi 20°, NEOVERENO). Nejlépe na peřeji nebo štěrkové lavici, ne v tůni, a tam, kde jsou břehy nízké. | Clarkin 2006 kap. 4.4.1; Keller & Sherar kap. 9; River Cole 8.1 |
| Šířka pásu brodu podél toku (jízdní dno) | 4–6 m, tedy `polosirka_m` 2,0–3,0. Současných 3,0 je v pořádku. | Clarkin: šířka vozovky 3,0–3,7 m; Evesham 4 m; Iden Green 3,9 × 5,7 m; River Cole 6 m |
| Přechodový pás (`nabeh_m`) | 4–6 m na každou stranu podél toku, s plynulým přechodem do normálního koryta. Délku přechodu a tvar křivky jsem v žádném zdroji nenašel, takže konkrétní číslo je NEOVERENO. | River Cole „smoothly contoured“ |
| Šířka vody v brodu | **Asi 2× normální šířka**, u Veličky 3 m → 5–6 m. Mezi břehy je ploché mělké dno, voda se rozlévá. | River Cole (6 m proti 3 m); fotky Wupperfurt a Retlage |
| Hloubka vody v brodu | 0,10–0,15 m (současných 0,12 je dobře). Dno má být **zvednuté a ploché**, ne prohloubené. Povolené zvýšení dna proti okolnímu dnu je do asi 0,3 m. | Gu 2005 (0,15 m); River Cole (+0,3 m); KCD 0,1–0,3 m (ODHAD Z OBRÁZKU) |
| Příčný profil dna v brodu | Plochý, s mírným sklonem po proudu 3–5 %. Bez parabolického „žlabu“ uprostřed. | Clarkin 2006 kap. 4.2 |
| Sklon nájezdů | Cíl ≤ 10 %, nejvýš 12–17 % (1:6). Současných 12 % je na horní hraně, doporučuji 10 %. | Clarkin („≤ 10 %“, výjimečně 15–20 %); River Cole 1:6 |
| Délka nájezdů | Plyne z výšky břehu: délka = (výška terénu nad hladinou) ÷ sklon. Při prahu 0,55 m a sklonu 10 % je to asi 5,5 m, u vyšších břehů víc. **Nájezd musí sahat až na původní terén**, nesmí končit na hraně. | výpočet z čísel výše |
| Svislé zakružení (proti „hrbu“) | Přechod nájezd → dno brodu a nájezd → terén zaoblit, ne lomit. Délka zakružení asi 2–3 m (NEOVERENO, číslo pro vůz 1393 nemám). Práh břehu (`prah_m`/`prah_nad_hladinou_m`) se v pásu brodu **úplně vynechá** a terén v pásu se nikde nesmí zvednout nad nájezd. | Clarkin („gentle vertical curve“); Keller & Sherar („avoid sharp vertical curves“) |
| Tvar břehů (úvoz) | Mělký zářez (úvoz) široký jako vozovka plus rozevření. Boční svahy zářezu jsou mírné, travnaté a zaoblené, nahoře se rozšiřují do trychtýře. Sklon bočních svahů asi 1:2 (NEOVERENO). Úvozy u středověkých brodů jsou doložené (Zlatá cesta), jejich rozměry ne. | Archeologický atlas, Obora; fotky Wupperfurt a Menach |
| Materiál dna | Štěrk a valouny 2–15 cm, mezery vyplněné drobným štěrkem. Na drobě a břidlici navíc **ploché desky** místní horniny. Velké balvany ne do jízdní stopy, jen na okraj pásu. Na dolní hraně brodu práh ze 0,15 m kamenů jako malá peřej. | Keller & Sherar kap. 9; River Cole (0,15 m kámen, „riffle“); KCD1 valouny; fotky Sankenbach a Remscheid |
| Kameny koryta na brodu | Jízdní pruh volný (`brod_volno_m` ponechat). Po stranách brodu a hlavně **pod brodem** (po proudu) víc kamenů a balvanů. Nad brodem klidnější voda. | Keller & Sherar (vymílání dolní hrany); KCD2 Bylany (kameny po stranách) |
| Šlapáky (pěšina přes tok) | Řada 4–6 plochých desek droby nebo břidlice napříč tokem, rozestup asi 0,5–0,7 m (krok, NEOVERENO), desky asi 0,4–0,8 m (ODHAD Z OBRÁZKU Remscheid). Na vozovém brodu volitelně jedna řada šlapáků vedle jízdního pruhu (NEOVERENO). | foto Remscheid |
| Lávka pro pěší | **Volitelná, ne povinná.** V KCD jsem lávku u brodu nedoložil. U skutečných brodů je běžná, ale novodobá. Pokud ano, tak jednoduchá (kláda nebo dvě fošny se zábradlím z tyče) 3–10 m proti proudu od brodu. Pro rok 1393 NEOVERENO. | fotky Retlage, Menach a Sankenbach (novodobé) |
| Vegetace | Tráva až k okraji štěrku a vody. Na nájezdech tráva mezi kolejemi a holé koleje. Vrby a olše na březích kolem brodu, ne v jízdním pruhu. Bez rákosí (podhorský potok). Kopřivy ze současného nastavení až mimo pás brodu. | fotky Wupperfurt a Menach; KCD1 snímky |
| Bahno | Pruh tmavé mokré hlíny a bláta na nájezdu u vody, asi 2–4 m od hladiny (NEOVERENO, odhad z fotky Menach), hlavně v kolejích. Dál od vody běžná hliněná cesta. | foto Menach; KCD2 Bylany (bahnité dno) |
| Štěrková lavice | Na vnitřní straně ohybu nebo pod brodem holý pruh valounů a štěrku 1–3 m (ODHAD Z OBRÁZKU KCD1), přechází do trávy. | KCD1 Tight Spot; River Cole (point bar) |

### Co konkrétně změnit oproti současnému stavu (návrh, k ověření Míšou)
1. V pásu brodu **zrušit práh a parabolu koryta**: dno je ploché ve výšce hladina − 0,12 m a široké asi 2× normální šířku vody. Hladina se tam rozlije.
2. **Nájezdy sklonem 10 % až na původní terén** se zaoblením nahoře i dole. Délka plyne z výšky břehu, nemá být pevných 4 m.
3. **Rozevřít zářez do trychtýře** se zaoblenými hranami. Žádný svislý ani ostrý okraj a žádný vyvýšený pás terénu mezi cestou a vodou.
4. Kameny: jízdní pruh nechat volný (štěrk a ploché desky jako materiál dna). Balvany dát na kraje a **kamenitou peřej pod brod**.
5. Vegetace: tráva až k vodě, vrby a olše po stranách, bláto jen v kolejích těsně u vody.

---

## Zdroje (souhrn)
- Kingdom Come: Deliverance wiki (fandom), stránky A Tight Spot, Cold Steel Hot Blood, The Fifth Commandment, Unveiling: `https://kingdom-come-deliverance.fandom.com/`
- GamerGuides, KCD Band of Bastards: `https://www.gamerguides.com/kingdom-come-deliverance/guide/walkthrough/dlc/band-of-bastards`
- PowerPyx, KCD2 The Fifth Commandment: `https://www.powerpyx.com/kingdom-come-deliverance-2-the-fifth-commandment-walkthrough/`
- Steam store screenshots KCD1 (app 379430)
- Clarkin K. a kol. (2006): *Low-Water Crossings: Geomorphic, Biological, and Engineering Design Considerations*, USDA Forest Service, kap. 4: `https://www.fs.usda.gov/eng/pubs/pdf/LowWaterCrossings/Lo_pdf/5_Chapter4.pdf`
- Keller G., Sherar J.: *Low-Volume Roads Engineering – Best Management Practices Field Guide*, kap. 9 „Fords and Low-Water Crossings“: `https://www.fs.usda.gov/t-d/programs/forest_mgmt/projects/lowvolroads/ch9.pdf`
- River Restoration Centre, *Manual of River Restoration Techniques* 8.1 River Cole: `https://www.therrc.co.uk/assets/pdfs/mot/final/8.1_Cole.pdf`
- US Army, Table 1-3 Trafficability of Fords: `https://armyengineer.tpub.com/EN5621/EN56210017.htm`
- Christchurch City Libraries, Clutterbuck diary s. 58 (hloubky brodů): `https://heritage.christchurchcitylibraries.com/Archives/OSullivan/Clutterbuck/Diary/PDF/0050-033.pdf`
- Archeologický atlas ČR, Obora u Tachova, Zlatá cesta: `https://www.archeologickyatlas.cz/cs/lokace/obora_tc_zlata_cesta.pdf`
- The Past, Evesham ford: `https://the-past.com/news/rare-ford-unearthed-at-evesham/`
- Wikimedia Commons, kategorie „Fords in Germany“ (fotky real_*)
