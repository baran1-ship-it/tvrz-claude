# Návrh: dovednosti hráče a menu hráče (Postava, Brašna, Dovednosti, Deník)

Stav: **návrh k odsouhlasení Míšou** (29. 10. 2026). Nic z toho zatím není v kódu ani v datech.
Podklady: rešerše KCD2 a jiných her (zdroje na konci, [Z1]–[Z25]), naše `docs/rozpracovane/warhorse_do_dat.md`
(sekce 2.1 Dovednosti, 2.2 Oblečení, 2.3 Jakost), `reserse_reakce_kcd2.md` (2.4–2.6, 6.4),
`pravidla/svet/hrac.json` (`zavisi_na`), `pravidla/svet/postavy.json` (`vnimani`, `hrac_dojem`, `reakce`),
`modely/predmety.json` (váhy, ceny, kategorie), `scripts/menu_hrace.gd`, `scripts/sber.gd`.

Pravidlo: **čísla jen v `pravidla/svet/*.json`, kód jen čte.** Každé číslo, které není přímo z KCD2 (KM-A-20)
nebo z našich dat, je označené **NEOVĚŘENO** a ladí se hraním, ne od stolu. Z KCD2 bereme principy (učení prací,
vrstvy oděvu, špína snižuje dojem), ne jména, strom perků ani texty.

---

## 0. Co už máme (výchozí stav)

| Co | Kde | Co z toho plyne pro návrh |
|---|---|---|
| Menu hráče kreslené přímo (`_draw`), virtuální plocha 1600×1000 × `u`, stránky LT/RT (Brašna, Stavění, výměna s truhlou, spánek), kategorie LB/RB jako erbovní štíty, vlevo detail, vpravo pergamen se seznamem po 8 řádcích, dotyk přes `_rects` | `scripts/menu_hrace.gd` | Nové záložky se přidají jako další `page` ve stejném stylu (stejný rám, písmo Grenze Gotisch, `Styl.kresli_*`). Ovládání LT/RT = záložky, LB/RB = kategorie zůstává. |
| Výdrž a běh podle KCD2 (`beh_za_s` 3,5, `obnova_za_s` 22, `skok_vydrz` 9, pády 1,5/2,2/8 m) a připravené vazby `zavisi_na: vydrz_max → vitalita, beh_za_s → vitalita, pad → hbitost` | `pravidla/svet/hrac.json` | Vazby přejmenujeme na naše vlohy (`dech`, `mrstnost`) a doplníme vzorce do `dovednosti.json`. |
| Katalog 328 předmětů: `kat` (zbrane 13, zbroj 19 – z toho 16 štítů a 3 přilby, naradi 23, jidlo 35, piti 7, byliny 3, nadoby 25, ostatni 17), `vaha` kg, `cena` groše | `modely/predmety.json` | Hmotnost výstroje je hotová. **Oblečení (košile, prošívanice, kroužky, obuv…) v katalogu není** – bez modelů nejde Postava naplno (otázka O3). |
| Bylinkářství už existuje, ale čísla jsou v kódu: `XP_UROVNE [0,8,25,55,100]`, `POZNAT {kopriva:1, …}`, počty kusů podle úrovně | `scripts/sber.gd` | První kandidát na převod do `dovednosti.json` (porušuje pravidlo „čísla v datech“). |
| Vnímání NPC (`rozpoznani_s` 4, `dohled_strop_m` 50, zorné pole), dojem z hráče (`hrac_dojem.vzhled_trida`, pověst), tabulka reakcí (`pozdrav_pan` od `trida_od` 0,7) | `pravidla/svet/postavy.json` | Plížení a oděv do nich jen **násobí** vstupy; nic nového v reakcích netřeba, jen se začne plnit `vzhled_trida` a nápadnost. |
| Rozbor KCD2 konstant KM-A-20/21 (XP za činnost, strop 30, perky od 6. úrovně, nosnost 90 lb + 10 lb/síla, špína, opotřebení vrstev) | `warhorse_do_dat.md` 2.1–2.3 | Převzaté hodnoty KCD2 v tomto návrhu odkazují tam. |

---

## 1. Jak to dělá KCD2 (rešerše, stručně)

### 1.1 Vlastnosti, dovednosti, úrovně
- **Čtyři hlavní vlastnosti:** Strength, Agility, Vitality, Speech; nad nimi **Main Level** = vychází ze součtu
  vlastností a z úkolů a příběhu, sám nic nezvyšuje a výbava na něm nezávisí [Z1][Z5].
- **Dovednosti** (hráč vidí): Alchemy, Craftsmanship, Drinking, Houndmaster, Scholarship, Stealth, Survival,
  Thievery, Horsemanship; bojové: Warfare, Swords, Heavy Weapons, Unarmed, Marksmanship, Polearms [Z1].
  V datech je jich víc (weapon_shield, weapon_dagger, tailoring, bowyery…), část interní (KM-A-21, viz
  `warhorse_do_dat.md` 2.1).
- **Učení prací:** každá dovednost roste jen svou činností – meč zvedá Swords, palcát Heavy Weapons, pití Drinking,
  luk a kuše Marksmanship [Z2][Z6]. Vlastnosti: síla bojem a nošením těžkého nákladu, obratnost lehkými zbraněmi,
  úhyby a střelbou, vitalita sprintem, skoky a bojem, výřečnost rozhovory, zkouškami v dialogu a smlouváním
  [Z6][Z8][Z9]. Jízda roste ručním ježděním (ne rychlým cestováním), přežití dlouhými cestami pěšky,
  plížení pohybem nepozorovaně blízko lidí, zlodějství zámky a kapsami [Z6]. Warfare dostává XP z každé bojové
  dovednosti [Z7].
- **Čísla XP (KM-A-20):** zásah 3, kombo 4, zabití 20, blok 0,5, dokonalý blok 2,5; vlastnost za zásah 2, zabití
  12; úhyb +10 obratnost; skok +1,5, přelez +2 vitalita; bylina 5; plížení nepozorován 10; čtení 30 XP/h;
  zkouška úspěch 3 / neúspěch 1 (celý seznam `warhorse_do_dat.md` 2.1). Křivka: `SkillXPLevelBase` 25,
  `SkillXPLevelDiff` 35, tvar vzorce Warhorse nezveřejnil.
- **Strop 30** u každé vlastnosti a dovednosti zvlášť (KCD1 měl 20); dočasné bonusy (lektvar, výbava) mohou ukázat
  víc, strop nemění [Z2][Z6].
- **Body perků:** v každém stromu zvlášť, **každou sudou úroveň od 6.** (6, 8, 10…), nepřenášejí se mezi stromy
  [Z1][Z3][Z6][Z7]. Některé perky se vylučují (Opportunist × Charming Man), některé čekají na úroveň [Z3].
  Přeučení lektvarem (lethean water) [Z2b].
- **Knihy a učitelé:** knihy dávají pevnou dávku XP dovednosti, kterou popisují; vyšší Scholarship = rychlejší čtení;
  knihy se dají prodat zpět písaři [Z6][Z10]. Učitelé: stupně Basics 100, Apprentice 500, Journeyman 1 500, další
  5 000 grošů [Z7][Z10]; vyšší stupeň až od určité úrovně (Scholarship advanced od 18) [Z11].
- **Obrazovka hráče:** záložky Vlastnosti / Dovednosti / Boj (utrácení bodů), dál jen ke čtení: Další, Komba,
  Pověst, Statistiky, Účinky, Společníci; tabulky s rozbalovacími skupinami a ukazatelem postupu; popis perku =
  kurzívou příběh + obyčejně herní účinek [Z12].

### 1.2 Výstroj
- **Vrstvy:** spodní (košile, prošívanice/gambeson, vatovaný kabátec) → kroužky (košile, kukla) → plát (kyrys,
  plechy rukou a nohou) → svrchní (suknice, waffenrock, plášť); přilba zvlášť, uzavřená zužuje výhled [Z13].
  KCD1: 20 slotů – hlava 4 (přilba, čepec/kukla, kroužkový závěs, obojek), tělo 6 (svrchní, plát, kroužky, spodní,
  rukavice, paže), nohy 4 (kroužky, nohavice, plát, boty), ostatní (hlavní ruka, druhá ruka, luk, šípy, prsten,
  ostruhy); dvakrát stejný kus obléct nelze [Z14]. Podrobné vrstvy KCD2 (KM-A-23) jsou v `warhorse_do_dat.md` 2.2.
- **Statistiky kusu:** obrana bod/sek/tup, váha, **hluk** (pohyb), **viditelnost** (pro nepřátele), **nápadnost**
  (jak moc vyčnívá), **charisma** (jak důležitě vypadá, sedláci se klaní), výdrž/stav kusu, min. síla (KCD1)
  [Z13][Z14]. Kroužky drží sek, slabé proti tupé; plát drží vše kromě silného tupého úderu; prošívanice pod
  kroužky výrazně zvedá obranu [Z13][Z15].
- **Jakost a stav:** 4 stupně jakosti; poškozená zbroj chrání méně; oprava u kováře nebo vlastní sadou (levnější
  a trénuje dovednost) [Z13]. Vzorce (KM-A-89): obrana a charisma × (√stav·0,6 + 0,4).
- **Špína a krev:** snižují charisma, ztěžují řečové zkoušky, zhoršují ceny, krčmář krvavého neobslouží; silně
  špinavého zvířata a nepřátelé ucítí z dálky; koryto smyje část, mýdlo nebo lázeň vše (lázeň pere jen to, co je
  na sobě) [Z16][Z17][Z18]. Konstanty: čistý do 0,25, páchne od 0,8 (`reserse_reakce_kcd2.md` 2.5).
- **Sady oblečení:** 3 uložené sady, přepnutí mimo boj [Z13][Z19].
- **Rozvržení inventáře:** vlevo seznam (tabulka s klíčovými čísly), vpravo menu hráče; ikony špinavé / kradené /
  vylepšené / nové; poškozený kus na sobě červeně; záložka Kůň jen s koněm nablízku [Z12][Z20].
- **Kritika rozhraní KCD2 (z čeho se poučit) [Z12]:** dlouhý seznam bez hledání, popis předmětu skáče podle
  kontextu (vlevo / vpravo / obojí), nejasné názvy (viditelnost vs. nápadnost, jakost vs. stav), záložky bez
  odznaku „nový bod“, účinky bez vysvětlení zdroje, okno přetéká okraj obrazovky [Z20].

### 1.3 Jiné hry (ovladač a dotyk)
- **Skyrim:** učení prací, cena úrovně `Mult·úroveň^1,95 + Offset`, úroveň postavy ze součtu zvýšení dovedností,
  perky za úroveň postavy [Z21].
- **Bannerlord:** vlastnost zvyšuje rychlost učení i „mez učení“ všech svých 3 dovedností, body zaměření zvedají mez
  (+50 za bod); za mezí se učení zpomalí až na nulu [Z22]. Pro nás: vloha jako **rychlost učení**, ne jako práh.
- **Zaklínač 3 (patch 1.20):** inventář pro ovladač rozdělen na sekce, pravá páčka skáče mezi sekcemi; kritika
  malého písma na TV a celoobrazovkového menu [Z23].
- **RDR2:** brašna podržením D-pad vpravo, kolo zbraní (podržet L1, vybrat pravou páčkou, pustit); realismus:
  jen 2 hlavní + 2 boční zbraně na těle [Z24]. Pro nás: **zbraně „na těle“ omezit sloty**, zbytek u koně/v truhle.
- **Dotyk Android:** cíl dotyku nejméně **48×48 dp** (≈ 9 mm) a 8 dp mezery [Z25].

---

## 2. Náš systém: „Vlohy, Umy a Zvyky“

Tři vrstvy, každá jinak než v KCD2:

1. **Vlohy** (4) – tělesné a duševní dispozice. **Netrénují se přímo**, rostou jen z umů (každý um odvádí díl XP
   své vloze) a z několika čistě tělesných činností (nošení, běh). Vloha **zrychluje učení** svých umů
   (vzor Bannerlord, ne KCD) a mění tělo (výdrž, nosnost, pád, dojem).
2. **Umy** (17) – co Kryštof umí; rostou prací, knihou a učitelem. Strop **20**.
3. **Zvyky** – náš náhradník perků: **nekupují se za body**, ale **získají se skutkem** (podmínka „úroveň umu +
   počet skutků“), a pak se **nosí v omezených místech mysli** jako oděv na těle; měnit je jde jen po spánku
   („zvyk se mění přes noc“). K tomu **neřesti**: zvyky se zápornou stránkou, které hráč dostane sám (pití,
   rvačky, kradení) a zbaví se jich jen tím, že činnost dlouho nedělá.

### 2.1 Vlohy (naše jména, ne KCD)
KCD v češtině používá Síla, Obratnost, Vitalita, Výřečnost – těm se vyhýbáme. Staročeské, dobově znějící:

| id | Jméno | Význam (1393) | Co mění v systémech | Krmí ji umy |
|---|---|---|---|---|
| `tuhost` | **Tuhost** | stč. *tuhý* = silný, pevný | nosnost, síla úderu obuchem a dřevcem, natažení luku/kuše | Obuch, Dřevce, Rvačka, Řemeslo, Hospodaření |
| `mrstnost` | **Mrštnost** | hbitost těla a rukou | pád (mez škody), rychlost útoku, tichost kroku, kapsy a zámky | Šerm, Střelba, Plížení, Lstivost, Ranhojičství |
| `dech` | **Dech** | vytrvalost, „dlouhý dech“ | `vydrz_max`, `beh_za_s`, obnova výdrže, vydrž kone při jízdě, snesení pití | Vojna, Jízda, Lov, Pití |
| `vaznost` | **Vážnost** | jak se člověk nese, úcta, kterou budí | dojem (náš „charisma“), ceny, řečové zkoušky, pozdrav „pane“ | Smlouvání, Písmo, Bylinkářství |

Strop vloh 20. Vloha nemá body zvyků (zvyky jsou u umů).

### 2.2 Umy a co je trénuje (XP za skutek)

Čísla XP vycházejí z KCD2 KM-A-20 tam, kde stejný skutek existuje (sloupec „zdroj“); ostatní **NEOVĚŘENO**.

| Skupina | id | Um | Zbraně / předměty z katalogu | Skutky → XP | Zdroj |
|---|---|---|---|---|---|
| Boj | `serm` | **Šerm** | `mec_dlouhy`, `mec_jednoruc`, `estok`, `tesak`, `dyka` | zásah 3, zásah v řadě 4, přemožení 20, kryt 0,5, čistý kryt 2,5, odveta 4 | KM-A-20 |
| Boj | `obuch` | **Obuch** | `palcat`, `kladivo_valecne`, `kladivo_bodec`, `sekera_valecna` | stejné jako Šerm | KM-A-20 |
| Boj | `drevce` | **Dřevce** | `kopi`, `halapartna` | stejné jako Šerm | KM-A-20 |
| Boj | `rvacka` | **Rvačka** | holé ruce | zásah 3, přemožení 20 (bez zabití – pěstní souboj v krčmě) | KM-A-20 |
| Boj | `strelba` | **Střelba** | `luk_toulec`, `kuse` | zásah terče 2 + 0,1/m vzdálenosti (max 6), zásah zvěře 8, střelnice: soutěž 15 | NEOVĚŘENO |
| Boj | `vojna` | **Vojna** | štíty, pavéza, zbroj | 50 % XP každého bojového umu + kryt štítem 1, nošení zbroje v boji 1/min | podíl NEOVĚŘENO (KCD2 Warfare z každého boje [Z7]) |
| Svět | `jizda` | **Jízda** | kůň | 3 za 100 m v sedle (trysk ×2), skok s koněm 5, zvládnutí splašení 10 | NEOVĚŘENO |
| Svět | `lov` | **Lov** | luk, nůž, past | úlovek 20 × koef. zvířete, vyvržení 8, stopa nalezena 3, 2 za 100 m mimo cesty | KM-A-20 (lov), zbytek NEOVĚŘENO |
| Svět | `bylinkarstvi` | **Bylinkářství** | `kopriva`, `barvinek`, `vlastovicnik`, `hriby`, `bedly` | utržení známé 5, neznámé 8, odvar uvařen 10 | 5 = KM-A-20 HerbGatherXP |
| Svět | `ranhojicstvi` | **Ranhojičství** | obvaz, mast | ošetření 1 za bod zdraví, zastavení krvácení 6 | NEOVĚŘENO |
| Svět | `plizeni` | **Plížení** | – | 10 za každých 10 s nepozorovaně v dohledu NPC (`vnimani`), tichý útok 30, prozrazení 5 | KM-A-20 |
| Svět | `lstivost` | **Lstivost** | paklíč | zámek otevřen 10 × obtížnost, kapsa 15, nezdar 3 | NEOVĚŘENO |
| Hospodář | `remeslo` | **Řemeslo** | `sekera_tesarska`, nářadí | oprava 1,5 za bod stavu, broušení 15, výroba 20 × jakost | KM-A-20 (oprava, broušení) |
| Hospodář | `hospodareni` | **Hospodaření** | mlýn, pole, stavění | pytel semletý 6, záhon zasetý/sklizený 4, stavba položena 2 (jen hra, ne pískoviště), prodej vlastní úrody 1 za 10 grošů | NEOVĚŘENO |
| Duch | `pismo` | **Písmo** | `kniha`, `kniha_modra`, `pult_kniha` | čtení 30/h, nová listina/nápis 5, zkouška Písmem úspěch 3 / nezdar 1 | KM-A-20 |
| Duch | `smlouvani` | **Smlouvání** | groše | koupě/prodej se smlouváním 1 za 10 grošů rozdílu (max 25), řečová zkouška úspěch 3 / nezdar 1 | KM-A-20 (zkouška) |
| Duch | `piti` | **Pití** | `piti` (pivo, víno, medovina) | 2 za číši, 10 za přečkání opilosti bez pádu | NEOVĚŘENO |

Proč takhle (rozdíly proti KCD2, ne kopie): **Hospodaření** je náš um (mlýn, pole, stavění – KCD2 nic takového
nemá), alchymie se slévá do Bylinkářství, Survival + Houndmaster = Lov (psa zatím nemáme), Speech není
vlastnost, ale um **Smlouvání** + vloha Vážnost (řeč = co říkáš × jak vypadáš), Warfare = **Vojna** dostává
jen polovinu.

### 2.3 Křivka XP (konkrétně)

**Um:** XP na postup z úrovně *n* na *n+1*: `xp(n) = round(zaklad + prirustek · n^mocnina)`,
`zaklad 20, prirustek 30, mocnina 1,25` (**NEOVĚŘENO**; KCD2 má 25/35 bez zveřejněného tvaru, Skyrim exponent
1,95 [Z21] – my mírnější, hra je kratší).

| Úroveň → | 1 | 2 | 3 | 5 | 8 | 10 | 12 | 15 | 18 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| XP na krok | 20 | 50 | 91 | 190 | 362 | 488 | 621 | 832 | 1 056 | 1 210 |
| XP celkem | 20 | 70 | 161 | 489 | 1 397 | 2 309 | 3 483 | 5 766 | 8 708 | 11 050 |

Kontrola smyslu: souboj ≈ 8 zásahů + přemožení ≈ 45 XP → úroveň 10 Šermu ≈ 50 soubojů; bylina 5 XP → úroveň 5
Bylinkářství ≈ 100 utržení (dnes v `sber.gd` 100 bodů ≈ 60–100 utržení – srovnatelné).

**Vloha:** `zaklad 30, prirustek 40, mocnina 1,25` → úroveň 10 = 3 852 XP, 20 = 14 798 XP. Vloha dostane
**podíl 0,5** z XP každého svého umu (KCD2 `SecondaryStatXPRatio` 1, my polovinu, protože vloha nemá vlastní
skutky – **NEOVĚŘENO**) + přímé tělesné XP:

| Skutek | Vloha | XP | Zdroj |
|---|---|---|---|
| 50 m s nákladem nad nosností (lehce / 2× přetížen) | Tuhost i Dech | 8 / 10 za 10 m | KM-A-20 |
| běh 100 m | Dech | 6,4 | KM-A-20 `AthleticXPAward` (dávka, vzdálenost NEOVĚŘENO) |
| skok / přelez | Dech | 1,5 / 2 | KM-A-20 |
| úhyb v okně | Mrštnost | 10 | KM-A-20 |
| pozdrav „pane“ (reakce `pozdrav_pan`) | Vážnost | 1 (max 10 za den) | NEOVĚŘENO |

**Rychlost učení:** každé XP umu × `(1 + 0,03 · vloha)` → při vloze 20 o 60 % rychleji (**NEOVĚŘENO**).

**Omrzelost (proti „mlácení do panáka“):** stejný skutek na stejném cíli (stejný strom, stejný terč, stejný NPC)
víckrát než 15× za 10 herních minut dává jen ×0,25 (**NEOVĚŘENO**). Výjimka čtení (omezené dobou).

**Začátek:** Kryštof (syn z tvrze) začíná: Šerm 3, Jízda 3, Písmo 2, Vojna 1, ostatní 0; vlohy Tuhost 3, Mrštnost
3, Dech 4, Vážnost 4 (**NEOVĚŘENO**, otázka O1).

### 2.4 Zvyky (náš koncept místo perků)

- Každý um má **4–6 zvyků** (celkem ~80). Zvyk se **odemkne skutkem**: `podminka = {um_od, skutek, pocet}`, např.
  „Mlynářská ruka“: Hospodaření ≥ 6 a 40 semletých pytlů. Hráč nevybírá z bodů – zvyk „přijde sám“, když se to
  udělá; v deníku je vidět, co k němu chybí (proti kritice KCD: „nevím, kde je nový bod“).
- **Místa mysli:** nosit jde jen `mista = 3 + floor(součet vloh / 10)` zvyků, nejvýš 8 (začátek 3+1 = 4,
  konec 3+8 = 11 → strop 8) (**NEOVĚŘENO**). Výměna jen při spánku (stránka `spanek` v `menu_hrace.gd` už je –
  přidá se krok „Zvyky na zítra“).
- **Úrovně zvyku:** některé mají stupně I/II (druhý od vyšší úrovně umu), stupeň nezabere další místo.
- **Neřesti:** zvyk s plus i minus, přijde sám: „Pijan“ (Pití ≥ 5 a 3 opilosti za 2 dny: opilost nesnižuje
  Vážnost, ale za střízliva −1 Mrštnost), „Rváč“ (5 rvaček: +Rvačka, ale strážní mají kratší rozpoznání),
  „Dlouhé prsty“ (10 krádeží). Neřest zabírá místo mysli a **nedá se sundat**; zmizí po N dnech bez činnosti
  (`odvyk_dni`, NEOVĚŘENO 7).
- Účinek zvyku = seznam změn jako buf KCD2 (`[{"co": "beh_za_s", "krat": 0.85}]`) – stejný formát jako
  účinky vloh, kód jen sčítá a násobí (KM-A-16/84 `buff_params`).

Příklady (vlastní jména a účinky):

| Zvyk | Um | Podmínka (skutek) | Účinek |
|---|---|---|---|
| Lehká noha | Plížení | Plížení 4, 30× nepozorovaně | hluk kroků ×0,8 |
| Pod korouhví | Vojna | Vojna 8, 10 soubojů ve zbroji | váha zbroje počítá do běhu ×0,75 |
| Mlynářská ruka | Hospodaření | Hospodaření 6, 40 pytlů | mletí ×1,25 rychleji, pytel +1 kg mouky |
| Zná groš | Smlouvání | Smlouvání 5, 20 obchodů | nákup −5 %, vidí skutečnou cenu kusu |
| Jezdec od Labe | Jízda | Jízda 6, 20 km v sedle | výdrž koně v trysku ×1,2 |
| Bylinná paměť | Bylinkářství | Bylinkářství 3, 5 druhů poznáno | pozná všechny byliny, poloměr sběru +0,2 m |
| Čte bez prstu | Písmo | Písmo 6, 3 knihy dočteny | čtení 1,5× rychleji |
| Pijan (neřest) | Pití | samo | viz výše |

### 2.5 Knihy a učitelé (rok 1393)

- **Gramotnost:** v roce 1393 čte málokdo; knihy jsou **česky** (kroniky, žaltáře, herbáře, rytířské návody)
  a **latinsky**. Kniha má `jazyk` a `pismo_min`: česká kniha od Písma 1, latinská od Písma 8. Bez Písma kniha
  nejde číst vůbec (obrázkový herbář jde – `pismo_min 0`).
- **Čtení:** XP za hodinu čtení 30 (KM-A-20) × `(1 + 0,05 · Písmo)`; kniha má `hodin` a `xp` (strop dávky);
  dočtená kniha dá XP navíc umu, o kterém je, a +5 Písmu; každou knihu jde dočíst jednou. Čte se u stolu/pultu
  (`pult_kniha`) nebo při odpočinku (sed, postel) – čas běží.
- **Učitelé = role z `postavy.json`:** kovář (Řemeslo), mlynář (Hospodaření), myslivec/hajný (Lov, Střelba),
  farář (Písmo), lazebník (Ranhojičství), krčmář (Pití, Smlouvání), purkrabí tvrze (Šerm, Vojna, Jízda). Lekce
  zvedne um o **jednu úroveň** až do `do_urovne` učitele, stojí `cena · (úroveň+1)` grošů a 2 herní hodiny;
  podmínka pověsti u učitele (`povest_od` 0,4). Ceny NEOVĚŘENO – navázat na ceny katalogu (dlouhý meč 600 grošů,
  lekce Šermu do úrovně 5: 30 × 5 = 150 grošů).

### 2.6 Jak umy a vlohy mění existující systémy

Všechny vzorce jsou v `dovednosti.json` `ucinky` (kód je jen vyhodnotí). Hodnoty u stropu (20):

| Systém (soubor) | Vzorec | Při 0 → 20 | Zdroj |
|---|---|---|---|
| Výdrž `hrac.json vydrz_max` | 100 + 3 · Dech | 100 → 160 | NEOVĚŘENO (KCD2 max výdrž z vlastností, KM-A-21) |
| Běh `beh_za_s` | 3,5 · (1 − 0,02 · Dech) | 3,5 → 2,1 /s | NEOVĚŘENO |
| Obnova `obnova_za_s` | 22 · (1 + 0,01 · Dech) | 22 → 26,4 | NEOVĚŘENO |
| Pád `pad.*_m` | × (1 + 0,5 · Mrštnost/20)⁻¹ na škodu; KCD2 `FallDamageMultiplierAtMaxAgility` 0,667 | škoda ×1 → ×0,667 | KM-A-20 |
| Nosnost (nové `hrac.json nosnost`) | 41 + 4,5 · Tuhost kg | 41 → 131 kg | KM-A-20 (90 lb + 10 lb/bod) |
| Ceny (obchod) | nákup × (1 − 0,01·Smlouvání − 0,005·(Vážnost+dojem)), prodej opačně, změna nejvýš ±25 % | – | NEOVĚŘENO (KCD2 omezuje rozdíl ±0,25 i u rychlosti útoku, KM-A-20) |
| Mlýn, pole (Hospodaření) | čas práce × (1 − 0,02·Hosp.), výnos × (1 + 0,02·Hosp.) | ×1 → ×0,6 / ×1,4 | NEOVĚŘENO |
| Oprava (Řemeslo) | max. stav po vlastní opravě 0,5 + 0,025·Řemeslo; spotřeba sady × (1 − 0,02·Ř.) | 0,5 → 1,0 | NEOVĚŘENO |
| Jízda (`jizda.json kun`) | vydrž koně v trysku `vydrz_s` × (1 + 0,02·Jízda); pád z koně při splašení šance 0,5 − 0,02·Jízda | 12 s → 16,8 s | NEOVĚŘENO |
| Střelba | rozptyl × (1 − 0,03·Střelba); přiblížení od úrovně 10, +1,5°/úroveň; natažení kuše čas × (1 − 0,02·Tuhost) | – | přiblížení KM-A-20 |
| Plížení (`postavy.json vnimani`) | `rozpoznani_s` × (1 + 0,6·P/20); `dohled` × (1 − 0,3·P/20); hluk kroků × (1 − 0,4·P/20) | 4 s → 6,4 s | KM-A-20 (0,6 / 0,3 / kroky 0,6) |
| Bylinkářství (`sber.gd`) | poloměr sběru 0,4 + 0,04 m/úroveň; kusů = 1 + floor(0,25 · √úroveň · 4); poznání druhu od úrovně z `byliny.poznat` | – | KM-A-20 |
| Řeč s NPC (`postavy.json reakce`, budoucí zkoušky) | síla = 0,5·Smlouvání + 0,3·Vážnost + 0,2·dojem·20 + 0,4·pověst·20 proti obtížnosti 11/17/24 | – | obtížnosti a 0,4 pověst KM-A-20; váhy NEOVĚŘENO |
| Pozdrav „pane“ | `hrac_dojem.vzhled_trida` = třída oděvu (2.7) − 0,8 · špína | – | `reserse_reakce_kcd2.md` 2.4 |
| Opilost | Pití zvedá práh opilosti 0,32 + 0,01·Pití; Vážnost −4 · opilost (KCD2 `AlcoholMaxCHAEffect` 4) | – | KM-A-20 |

---

## 3. Výstroj: sloty, vrstvy, statistiky

### 3.1 Zóny těla a sloty

Ochrana se počítá **po zónách** (zásah do hlavy bere jen vrstvy na hlavě): `hlava, krk, trup, paze, ruce,
nohy, chodidla`.

| Slot | Vrstva | Zóny | Příklad 1393 (z katalogu / chybí) |
|---|---|---|---|
| `kosile` | 0 spodní | trup, paže | lněná košile (chybí) |
| `nohavice` | 0 spodní | nohy | vlněné nohavice (chybí) |
| `vycpavka` | 1 prošívaná | trup, paže (krátká bez paží) | prošívanice, vatovaný kabátec (chybí) |
| `krouzky` | 2 kroužková | trup, paže (+ nohy u dlouhé) | kroužková košile (chybí) |
| `plat` | 3 plátová | trup | prsní plát, brigantina (chybí) |
| `pazni` | 3 | paže | plechové rukávy (chybí) |
| `nohy_plat` | 3 | nohy | plechové nohy (chybí) |
| `svrchni` | 4 svrchní | trup (+ nohy u dlouhé suknice) | suknice, jupka, plášť, kabátec s erbem (chybí) |
| `cepec` | 1 | hlava | plátěný čepec, prošívaná kukla (chybí) |
| `kukla_krouzkova` | 2 | hlava, krk | kroužková kukla / závěs (chybí) |
| `kape` | 4 | hlava, krk | kápě s límcem (chybí) |
| `pokryvka` | 3 | hlava | `barbuta`, `bascinet`, `klobouk_zelezny`, plstěný klobouk (chybí) |
| `rukavice` | 3 | ruce | kožené / plátové (chybí) |
| `obuv` | 3 | chodidla | krpce, škorně (chybí) |
| `opasek` | – | – | opasek: 2 místa na zbraň + měšec (chybí) |
| `prsten` | – | – | pečetní prsten (dojem, chybí) |
| `ostruhy` | – | – | ostruhy (Jízda: rychlejší pobídka, chybí) |
| `ruka_hlavni` | zbraň | – | meče, obuchy, dřevce (`kat: zbrane`) |
| `ruka_druha` | štít | – | `stit*`, `puklir`, `paveza` (16 štítů) |
| `zada` | zbraň | – | `luk_toulec`, `kuse`, dřevce na zádech |

Pravidla: kus může zabrat víc slotů (`sloty: ["kosile","nohavice"]` u dlouhé suknice), dva kusy do jednoho slotu ne,
plát jen přes vycpávku (`vyzaduje: ["vycpavka"]`, bez ní obrana plátu ×0,7 – NEOVĚŘENO; princip [Z13][Z15]).
Na těle jen **opasek 2 + ruce + záda** zbraní (vzor RDR2 [Z24]), ostatní nese brašna (váha).

### 3.2 Statistiky kusu (nové `pravidla/svet/odev.json`, klíč = id z `predmety.json`)

| Klíč | Rozsah | Význam |
|---|---|---|
| `ochrana` | `{bod, sek, tup}` 0–30 | po zónách v `zony` |
| `teplo` | −2…+5 | teplo kusu (noc, déšť – jen když se zavede chlad, otázka O4) |
| `napadnost` | 0–1 | jak moc vyčnívá (barva, lesk, erb) → `postavy.json` váha `napadnost` 0,3 a `rozpoznani_s` |
| `hluk` | 0–1 | hluk při pohybu → poloměr slyšení NPC; kroužky a plát nahoře, látka ~0 |
| `dojem` | 0–20 | náš „charisma“ kusu; **dojem postavy = průměr viditelných kusů** (spodní vrstvy schované pod svrchní se nepočítají) |
| `trida` | sedlacky / mestsky / pansky / zbroj | „šaty dělají člověka“: třída s ≥ 1/3 výstroje = jak hráče vidí NPC (`trida_podil_vystroje` 0,333) |
| `stav` | 0–1 (za hry) | opotřebení; obrana a dojem × (√stav·0,6 + 0,4); cena × (stav·0,99 + 0,01) (KM-A-89) |
| `spina`, `krev` | 0–1 (za hry) | dojem × (1 − 0,8·špína) (`ArmorDirtToCharismaCoef`); krev viditelná od 0,3; páchne od 0,8 |
| `vaha` | kg | **z `predmety.json`**, v `odev.json` se neopakuje |

Ukazatele postavy (Postava, pravý sloupec): **Ochrana** (bod/sek/tup na každou zónu – obrázek postavy s barvou
zóny), **Dojem**, **Nápadnost**, **Hluk**, **Teplo**, **Čistota**, **Náklad** (kg / nosnost). Jména volíme
srozumitelně (kritika KCD2: „viditelnost vs. nápadnost“ [Z12]) – **viditelnost nezavádíme** zvlášť; tma a světlo
(louč) jsou v `hrac_dojem.noc_bez_svetla_napadnost`, oděv dává jen nápadnost.

### 3.3 Náklad (z vah katalogu)

- `náklad = P.weight(P.inv) + váha všeho na sobě` (`predmety.gd` už `weight()` umí).
- Stupně (`hrac.json nosnost.stupne`): ≤ 1,0 × nosnost volně; ≤ 1,25 bez běhu, chůze ×0,85; ≤ 1,5 chůze ×0,6,
  skok ne; nad 1,5 nehne se (hláška „Nesu toho moc“) (**NEOVĚŘENO**; princip KCD2 přetížení).
- Váha zbroje na sobě zdražuje běh: `beh_za_s × (1 + 0,01 · max(0, váha_zbroje − 8 kg))` (NEOVĚŘENO).
- Přetížení dává XP Tuhosti a Dechu (2.3) – trénink nošením, jak to dělá KCD2.

### 3.4 Špína, krev, stav

Čísla KCD2 jsou v `reserse_reakce_kcd2.md` 2.5 a `warhorse_do_dat.md` 2.2–2.3; převezmeme je do `odev.json`
(`spina_plna_km` 35, `krev_plna_s` 240, `poskozeni_vrstvy` 0,3/0,375/0,0075, `nova_obuv_km` 10). Praní: koryto
a potok (`kad` má `myti: true`) smyje špínu do 0,3–0,8 (KM-A-20 `WashDirtLimit`), lázeň vše; pere se jen co je
na sobě [Z17][Z18]. Oprava: kovář (groše) nebo sada (Řemeslo, XP).

---

## 4. Menu hráče (tablet 2000×1335, dotyk + ovladač)

Kreslí se dál v `menu_hrace.gd` na virtuální plochu 1600×1000 (`u = min(2000/1600, 1335/1000) = 1,25`). Na
2000×1335 zbývá po stranách 0 px a nahoře/dole 42 px. **Nejmenší cíl dotyku 60 u = 75 px** (≈ 48 dp při hustotě
~1,5; hustota tabletu **NEOVĚŘENO** – změřit, Xiaomi Pad 8), mezera ≥ 10 u [Z25].

### 4.1 Struktura a ovládání (stejné na všech záložkách)

| Akce | Ovladač | Dotyk |
|---|---|---|
| otevřít menu | D-pad dolů (už je) / Start = Deník | ikona brašny v HUD |
| záložka Postava · Brašna · Dovednosti · Deník (+ Stavění v pískovišti) | **LT / RT** (už je) | klep na název nahoře |
| kategorie / skupina v záložce | **LB / RB** (už je, erbovní štíty) | klep na štít |
| pohyb fokusu | levá páčka / D-pad | – |
| přeskočit mezi panely (seznam ↔ panenka ↔ detail) | **pravá páčka** vlevo/vpravo (vzor Zaklínač 3 [Z23]) | klep do panelu |
| použít / obléct / sundat | **A** | dvojklep, nebo tlačítko v detailu |
| odložit / zahodit | **Y** (už je „uložit“) | tlačítko v detailu |
| porovnat s tím, co mám na sobě | **X** podržet | dlouhý stisk |
| zpět / zavřít | **B** (už je) | pečeť vpravo nahoře (už je) |

Zásady z rešerše: **detail předmětu vždy na stejném místě** (levý panel), na záložce s novým zvykem nebo úrovní
**odznak** (zlatá tečka), účinky vždy s uvedeným zdrojem, nic nepřetéká okraj (kritika KCD2 [Z12][Z20]); písmo
nejméně 26 u (Zaklínač kritika malého písma [Z23]).

### 4.2 Záložka POSTAVA (panenka + sloty)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐ 2000 px
│ POSTAVA   Brašna   Dovednosti   Deník                 LB [Oděv][Zbraně][Sady] RB      (✕)│ 0–150
├───────────────────────┬──────────────────────────────────────┬───────────────────────────┤
│ DETAIL (500 u)        │        PANENKA (560 u)                │ UKAZATELE (460 u)         │
│ ┌───────────────────┐ │  [čepec] [kukla] [kápě] [pokrývka]   │ Ochrana  bod 18 sek 24 tup 9│
│ │ ikona/model kusu  │ │        ┌────────┐                     │  ┌─ obrys těla, zóny barvou ┐│
│ │ Barbuta           │ │ [hlav.]│ obrys  │[druhá]              │  │ hlava ███ trup ██ nohy █ ││
│ │ Pokrývka · vrstva3│ │ [ruka] │ Kryštof│[ruka ]              │  └──────────────────────────┘│
│ │ ochrana 14/16/6   │ │        │ (2D/3D)│                     │ Dojem        11  ▲ +2       │
│ │ dojem 6  hluk 0,2 │ │ [košile][vycpávka][kroužky][plát]     │ Nápadnost   0,4             │
│ │ stav ▓▓▓▓░ 0,72   │ │ [svrchní][pažnice][rukavice]          │ Hluk        0,3             │
│ │ špína ▓░░░ 0,18   │ │ [nohavice][nohy plát][obuv][ostruhy]  │ Teplo       +3              │
│ │ váha 2,5 kg 380 g.│ │ [opasek: ⚔ ⚔ měšec] [záda] [prsten]   │ Čistota     ▓▓▓▓░           │
│ │ [Sundat] [Porovn.]│ │                                       │ Náklad 38,2 / 54,5 kg ▓▓▓░  │
│ └───────────────────┘ │  Sady: [I] [II] [III]                 │ Vypadáš jako: měšťan        │
├───────────────────────┴──────────────────────────────────────┴───────────────────────────┤
│ A obléct/sundat · X porovnat · Y odložit · pravá páčka panel · B zpět                     │ 950–1000
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

- Sloty = štíty 84×84 u (dotyk OK), sousedé pro ovladač se berou z dat (`menu.postava.sousede`), ne z kódu.
- Výběr slotu → seznam vhodných kusů z brašny **v levém panelu pod detailem** (filtr podle `slot`), A = obléct.
- Obrys postavy: fáze 1 kreslený obrys (textura, vrstvy odstínem); fáze 4 živý model hráče v `SubViewport`
  (jen když je menu otevřené, hra stojí; **cena na tabletu NEOVĚŘENO**, změřit).
- „Vypadáš jako: měšťan“ = výsledek třídy oděvu (3.2) – hráč hned ví, jak na něj budou lidé reagovat.
- Sady I–III: uložit/přepnout (mimo boj), vzor KCD2 [Z13].

### 4.3 Záložka BRAŠNA (stávající, upravit)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Postava   BRAŠNA   Dovednosti   Deník        LB [Vše][Zbraně][Zbroj][Nářadí][Jídlo]... RB │
├───────────────────────┬──────────────────────────────────────────────────────────────────┤
│ DETAIL (stejný panel  │ Kryštofova brašna                  řadit: [jméno][váha][cena]     │
│ jako v Postavě)       │ ───────────────────────────────────────────────────────────────── │
│                       │ ◆ Dlouhý meč            1   1,5 kg   600   ●na sobě               │
│ + srovnání s kusem    │   Bochník chleba        3   0,5 kg     2                          │
│   na sobě: ▲▼ čísla   │   Kopřiva               7   0,1 kg     1   ♦nová                  │
│                       │   Halapartna            1   3,2 kg   260   ⚠ poškozená            │
│                       │   … (8 řádků, posun)                                              │
├───────────────────────┴──────────────────────────────────────────────────────────────────┤
│ Náklad 38,2 / 54,5 kg ▓▓▓▓▓▓░░  ·  groše 312  ·  A použít/obléct · Y odložit · B zpět    │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

Změny proti dnešku: pruh **náklad / nosnost** dole, značky (na sobě, nová, poškozená, špinavá, kradená –
vzor ikon KCD2 [Z12]), řazení LS-klik / klep na hlavičku, oděvy z Brašny jdou obléct přímo (A).

### 4.4 Záložka DOVEDNOSTI

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Postava   Brašna   DOVEDNOSTI•   Deník              LB [Vlohy][Boj][Svět][Hospodář][Duch] RB│
├───────────────────────┬──────────────────────────────────────────────────────────────────┤
│ DETAIL UMU            │ Umy – Svět                                                        │
│ Bylinkářství  7       │  Jízda          ▓▓▓▓▓▓░░░░  6   (Dech)                            │
│ „Kdo zná kořínek…“    │  Lov            ▓▓░░░░░░░░  2   (Dech)                            │
│ (kurzívou příběh)     │ ▶Bylinkářství   ▓▓▓▓▓▓▓░░░  7   (Vážnost)   •nový zvyk            │
│ Účinky teď:           │  Ranhojičství   ░░░░░░░░░░  0   (Mrštnost)                        │
│ · sběr 0,68 m         │  Plížení        ▓▓▓░░░░░░░  3   (Mrštnost)                        │
│ · 1–2 kusy            │  Lstivost       ▓░░░░░░░░░  1   (Mrštnost)                        │
│ Do 8: 112 / 362 XP    │ ───────────────────────────────────────────────────────────────── │
│ Učí se: utržením (5), │  ZVYKY umu:  [✓ Bylinná paměť]  [◻ Kořenář: 4/10 odvarů]         │
│ odvarem (10)          │              [🔒 Ranní rosa: od úrovně 10]                        │
│ Učitel: lazebník (do 8)│                                                                  │
├───────────────────────┴──────────────────────────────────────────────────────────────────┤
│ Místa mysli 3/4: [Lehká noha] [Bylinná paměť] [Zná groš] [ — ]   (měnit jde při spánku)   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

- Skupina **Vlohy** ukazuje 4 vlohy s pruhem a „co mění“ (výdrž 112, nosnost 54,5 kg…) s rozpisem zdroje.
- U každého umu: čím se učí (z dat `xp_za`), co chybí k dalšímu zvyku, který učitel a kniha existuje.

### 4.5 Záložka DENÍK (statistiky a stav)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Postava   Brašna   Dovednosti   DENÍK                  LB [Stav][Statistiky][Knihy][Pověst] RB│
├───────────────────────┬──────────────────────────────────────────────────────────────────┤
│ STAV TĚLA             │ Statistiky (od začátku hry)                                       │
│ Životy  86/100        │  Dní na tvrzi .................. 12                               │
│ Výdrž   112           │  Ušlo pěšky .................... 41,3 km                          │
│ Únava   ▓▓░░ 0,35     │  Ujeto v sedle ................. 18,0 km                          │
│ Hlad    ▓░░░          │  Utrženo bylin ................. 143                              │
│ Opilost ░░░░          │  Semleto pytlů ................. 22                               │
│ Čistota ▓▓▓░          │  Přemoženo soupeřů ............. 5                                │
│ Účinky (se zdrojem):  │  Přečteno knih ................. 2                                │
│ · Vážnost −1 (špína)  │  Vyděláno / utraceno ........... 840 / 610 grošů                  │
│ · Běh ×0,85 (zvyk)    │  Nejdelší střela ............... 46 m                             │
├───────────────────────┴──────────────────────────────────────────────────────────────────┤
│ B zpět · LB/RB stránka                                                                    │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

Statistiky jsou jen součty událostí z kap. 5 (žádný zvláštní kód) – každá událost se zapíše do `deník.pocty`.

---

## 5. Data: `pravidla/svet/dovednosti.json` (návrh, výňatek)

```json
{
 "popis": "Vlohy, umy a zvyky hrace (navrh docs/rozpracovane/navrh_skilly_menu_hrace.md). Uceni praci: udalost -> xp_za -> um (+ podil vloze). Cte scripts/dovednosti.gd; v kodu zadna cisla.",
 "strop": 20,
 "krivka_um":    {"zaklad": 20, "prirustek": 30, "mocnina": 1.25, "_": "xp(n->n+1) = round(zaklad + prirustek * n^mocnina); NEOVERENO, KCD2 25/35 tvar nezverejnen (KM-A-20)"},
 "krivka_vloha": {"zaklad": 30, "prirustek": 40, "mocnina": 1.25},
 "podil_vloze": 0.5,
 "uceni_za_vlohu": 0.03,
 "omrzelost": {"stejny_skutek_max": 15, "okno_min": 10, "krat": 0.25},
 "vlohy": {
  "tuhost":   {"nazev": "Tuhost",   "popis": "pevnost tela a paze", "start": 3},
  "mrstnost": {"nazev": "Mrštnost", "popis": "hbitost tela a rukou", "start": 3},
  "dech":     {"nazev": "Dech",     "popis": "vytrvalost, dlouhy dech", "start": 4},
  "vaznost":  {"nazev": "Vážnost",  "popis": "jak se nese a jakou budi uctu", "start": 4}
 },
 "umy": {
  "serm": {
   "nazev": "Šerm", "skupina": "boj", "vloha": "mrstnost", "start": 3,
   "zbrane": ["mec_dlouhy", "mec_jednoruc", "estok", "tesak", "dyka"],
   "xp_za": {"zasah": 3, "zasah_rada": 4, "premozeni": 20, "kryt": 0.5, "kryt_cisty": 2.5, "odveta": 4},
   "ucinky": [{"co": "rychlost_utoku", "plus_za_uroven": 0.0125, "_": "max +0,25 u stropu (KM-A-20 omezeni +-0,25)"}],
   "ucitele": [{"role": "purkrabi", "do_urovne": 10, "cena_za_uroven": 30}]
  },
  "bylinkarstvi": {
   "nazev": "Bylinkářství", "skupina": "svet", "vloha": "vaznost", "start": 0,
   "xp_za": {"bylina_znama": 5, "bylina_neznama": 8, "odvar": 10},
   "poznat": {"kopriva": 1, "hriby": 1, "barvinek": 3, "bedly": 3, "vlastovicnik": 6, "_": "z scripts/sber.gd POZNAT (1/2/3 -> 1/3/6)"},
   "ucinky": [
    {"co": "sber_polomer_m", "zaklad": 0.4, "plus_za_uroven": 0.04, "_": "KM-A-20"},
    {"co": "sber_kusu", "vzorec": "1 + floor(sqrt(uroven))", "_": "KM-A-20 x0,25*sqrt; nase zaokrouhleni NEOVERENO"},
    {"co": "sber_soused_sance", "od_urovne": 6, "plus_za_uroven": 0.04}
   ],
   "ucitele": [{"role": "lazebnik", "do_urovne": 8, "cena_za_uroven": 15}]
  },
  "hospodareni": {
   "nazev": "Hospodaření", "skupina": "hospodar", "vloha": "tuhost", "start": 0,
   "xp_za": {"pytel_semlet": 6, "zahon_zaset": 4, "zahon_sklizen": 4, "stavba_polozena": 2, "prodej_urody_za_10_g": 1},
   "ucinky": [
    {"co": "mleti_cas", "krat_za_uroven": -0.02},
    {"co": "vynos", "krat_za_uroven": 0.02}
   ],
   "ucitele": [{"role": "mlynar", "do_urovne": 8, "cena_za_uroven": 20}]
  }
 },
 "vloha_ucinky": {
  "dech":     [{"cil": "hrac.vydrz_max", "plus_za_uroven": 3}, {"cil": "hrac.beh_za_s", "krat_za_uroven": -0.02}, {"cil": "hrac.obnova_za_s", "krat_za_uroven": 0.01}],
  "tuhost":   [{"cil": "hrac.nosnost_kg", "zaklad": 41, "plus_za_uroven": 4.5, "_": "KM-A-20 90 lb + 10 lb/bod"}],
  "mrstnost": [{"cil": "hrac.pad_skoda", "na_stropu": 0.667, "_": "KM-A-20 FallDamageMultiplierAtMaxAgility"}],
  "vaznost":  [{"cil": "obchod.cena_nakup", "krat_za_uroven": -0.005}]
 },
 "vloha_xp_za": {
  "pretizen_10m": {"tuhost": 8, "dech": 8}, "pretizen_2x_10m": {"tuhost": 10, "dech": 10},
  "beh_100m": {"dech": 6.4}, "skok": {"dech": 1.5}, "prelez": {"dech": 2}, "uhyb": {"mrstnost": 10},
  "pozdrav_pan": {"vaznost": 1, "max_za_den": 10}
 },
 "zvyky": {
  "mista": {"zaklad": 3, "za_soucet_vloh": 10, "max": 8, "menit": "spanek"},
  "seznam": {
   "lehka_noha":     {"nazev": "Lehká noha", "um": "plizeni", "podminka": {"um_od": 4, "skutek": "nepozorovan_10s", "pocet": 30}, "ucinky": [{"co": "hluk_kroku", "krat": 0.8}]},
   "mlynarska_ruka": {"nazev": "Mlynářská ruka", "um": "hospodareni", "podminka": {"um_od": 6, "skutek": "pytel_semlet", "pocet": 40}, "ucinky": [{"co": "mleti_cas", "krat": 0.8}]},
   "pijan":          {"nazev": "Pijan", "um": "piti", "nerest": true, "podminka": {"um_od": 5, "skutek": "opilost", "pocet": 3, "za_dni": 2}, "odvyk_dni": 7,
                      "ucinky": [{"co": "vaznost_z_opilosti", "krat": 0.0}, {"co": "vloha.mrstnost", "plus": -1, "kdy": "strizlivy"}]}
  }
 },
 "knihy": {
  "kniha":       {"nazev": "Žaltář", "jazyk": "latina", "pismo_min": 8, "um": "pismo", "hodin": 6, "xp": 180},
  "kniha_modra": {"nazev": "Herbář s obrázky", "jazyk": "cestina", "pismo_min": 0, "um": "bylinkarstvi", "hodin": 4, "xp": 120},
  "cteni_xp_za_h": 30, "cteni_za_pismo": 0.05, "docteni_pismo_xp": 5,
  "_": "id = predmety.json; cteni 30 XP/h KM-A-20 ReadingXpPerHour, ostatni NEOVERENO"
 },
 "zkouska": {"lehka": 11, "stredni": 17, "tezka": 24, "povest_vaha": 0.4, "_": "KM-A-20"}
}
```

Doprovodné soubory: `pravidla/svet/odev.json` (sloty, vrstvy, zóny, statistiky kusů – kostra je
v `warhorse_do_dat.md` 2.2, doplnit `ochrana/napadnost/hluk/dojem/trida/teplo`), `hrac.json` (`nosnost.stupne`,
`zavisi_na` přejmenovat: `vitalita → dech`, `hbitost → mrstnost`), `menu` sekce (sousedé slotů, rozložení v u).

### 5.1 Události (háčky), které musí kód vysílat

Jeden vstup: `main.udalost(id: String, data: Dictionary)` → `dovednosti.gd` (XP, zvyky, omrzelost) a deník
(počty). Kód hry jen ohlásí, co se stalo; o XP rozhodují data.

| Událost | Data | Kdo vysílá (soubor) | Um / vloha |
|---|---|---|---|
| `zasah`, `zasah_rada`, `premozeni` | `zbran` (id), `cil` (id NPC/terč) | budoucí boj | podle `umy.*.zbrane`, Vojna 50 % |
| `kryt`, `kryt_cisty`, `odveta`, `uhyb` | `zbran` | budoucí boj | zbraňový um, Vojna, Mrštnost |
| `strela_zasah` | `zbran`, `vzdalenost_m`, `cil_druh` (terč/zvěř) | luk (`dev_test` už testuje luk; hráčův kód střelby) | Střelba |
| `beh_m`, `chuze_m`, `pretizen_m` | `m`, `podil_nosnosti` | `player.gd` / `pohyb.gd` (souhrn po 10 m) | Dech, Tuhost |
| `skok`, `prelez`, `pad` | `vyska_m` | `player.gd` | Dech, Mrštnost |
| `jizda_m`, `kun_skok`, `kun_splasen` | `chod`, `m` | `kun.gd` | Jízda |
| `bylina` | `id`, `znal` | `sber.gd pick()` (už má `zisk`, nahradit) | Bylinkářství |
| `ulovek`, `vyvrzeni`, `stopa` | `zvire` | budoucí lov | Lov |
| `nepozorovan_10s`, `prozrazen` | `npc` | vnímání NPC (`lide.gd`) | Plížení |
| `zamek`, `kapsa`, `kradez` | `obtiznost`, `uspech` | budoucí | Lstivost |
| `cteni_h`, `kniha_doctena` | `kniha` | čtení u pultu / sed | Písmo + um knihy |
| `lekce` | `um`, `ucitel` | rozhovor s učitelem | daný um (+1 úroveň) |
| `oprava`, `brouseni`, `vyroba` | `predmet`, `body`, `jakost` | brus, kovárna | Řemeslo |
| `pytel_semlet`, `zahon_zaset`, `zahon_sklizen`, `stavba_polozena` | `misto` | mlýn (`mlyn_kolo.gd v_chodu`), pole, `predmety.gd` (jen režim hra) | Hospodaření |
| `obchod` | `cena`, `sleva`, `prodavac` | výměna / obchod (`menu_hrace.gd` výměna) | Smlouvání |
| `zkouska_reci` | `druh`, `obtiznost`, `vysledek` | rozhovory (budoucí) | Smlouvání, Písmo |
| `pozdrav_pan` | `npc` | `lide.gd` při reakci `pozdrav_pan` | Vážnost |
| `piti`, `opilost` | `napoj`, `mira` | jídlo/pití v Brašně | Pití |
| `osetreni` | `body` | obvaz | Ranhojičství |
| `prani`, `spanek` | `misto` | koryto `kad`, stránka `spanek` | čistota; spánek = výměna zvyků, přepočet neřestí |

Test (nový `tools/test_dovednosti.py`, běží s testem smyslu): JSON proti schématu, křivky rostoucí, každé
`xp_za`/`skutek` v datech má v kódu `udalost("…")` (grep), každý `zbrane`/`knihy` id existuje v `predmety.json`,
každý zvyk dosažitelný (podmínka ≤ strop).

---

## 6. Plán po fázích

| Fáze | Co | Hotovo když |
|---|---|---|
| **1. Jádro umů** | `dovednosti.json` (vlohy, 17 umů, křivky, `xp_za`), `scripts/dovednosti.gd` (`udalost`, úrovně, uložení do save, hláška „Bylinkářství: úroveň 3“), převod `sber.gd` čísel do dat, události `beh_m`, `skok`, `bylina`, `jizda_m`; napojení `hrac.json zavisi_na` (výdrž, běh, pád) a nosnosti | snímek hlášky + test_dovednosti projde |
| **2. Záložka Dovednosti a Deník** | nové `page` v `menu_hrace.gd` (LT/RT), pruhy, detail umu, statistiky z počtů událostí, odznak nového | snímek obou záložek na 2000×1335 |
| **3. Náklad a Brašna** | pruh náklad/nosnost, stupně přetížení, značky v seznamu, řazení | snímek + krátký test přetížení |
| **4. Postava (oděv)** | `odev.json`, sloty a vrstvy, obléct/sundat, ukazatele, třída → `hrac_dojem.vzhled_trida`, nápadnost → vnímání; **nejdřív hledat hotové modely oděvu** (Disk Modely, Sketchfab CC0/CC-BY, Quaternius…) | snímek panenky + pozdrav „pane“ v plném oděvu |
| **5. Zvyky a učení** | zvyky se skutky, místa mysli při spánku, neřesti, knihy (čtení u pultu), učitelé podle rolí | test dosažitelnosti zvyků |
| **6. Opotřebení a čistota** | stav, špína, krev, praní u koryta, oprava; dojem a ceny | snímek špinavého oděvu v detailu |
| 7. Později | boj (zásahy, kryty), lov, zámky, řečové zkoušky – události jsou připravené v 5.1 | – |

---

## 7. Otázky pro Míšu (jen nutné)

- **O1:** Kdo je Kryštof na začátku – zkušený syn z tvrze (Šerm 3, Jízda 3, Písmo 2) nebo začátečník od nuly?
- **O2:** Líbí se „zvyky za skutky + místa mysli měněná přes noc“ místo bodů perků, nebo chceš klasické body?
- **O3:** Oděv potřebuje modely (košile, prošívanice, kroužky, suknice, obuv) – máš něco na Disku, nebo hledat na
  Sketchfabu? Bez nich jde Postava jen se zbraněmi, štíty a 3 přilbami.
- **O4:** Chceme chlad (teplo oděvu v noci a v dešti), nebo teplo vynechat?
- **O5:** Jména vloh **Tuhost, Mrštnost, Dech, Vážnost** a umů (Obuch, Dřevce, Lstivost, Hospodaření…) – sedí?

---

## Zdroje

- [Z1] Gamer Guides – KCD2 Stats and Skills (seznam, Main Level, perk každou sudou úroveň):
  https://www.gamerguides.com/kingdom-come-deliverance-ii/guide/stats-and-skills
- [Z2] Steam diskuze KCD2 – strop 30 (KCD1 20), perk každé 2 úrovně: https://steamcommunity.com/app/1771300/discussions/0/601895828709212593 ;
  [Z2b] přeučení lektvarem: https://steamcommunity.com/app/1771300/discussions/0/600771216994759604
- [Z3] Shacknews – How leveling up & perk points work (body po kategoriích, vylučující se perky):
  https://www.shacknews.com/article/142954/level-up-perk-points-kcd2
- [Z4] Loot Level Chill – How to use Perk Points: https://lootlevelchill.com/guides/kingdom-come-deliverance-2-how-to-use-perk-points/
- [Z5] Gamer Guides – Main Level: https://www.gamerguides.com/kingdom-come-deliverance-ii/guide/stats-and-skills/level
- [Z6] kcd2.org – KCD2 skills (čím se co učí, strop 30, knihy, učitelé): https://kcd2.org/en/post/kcd2-skills
- [Z7] Gamer Guides – Warfare (XP z každého boje, ceny učitelů 100/500/1 500/5 000):
  https://gamerguides.com/kingdom-come-deliverance-ii/guide/stats-and-skills/warfare
- [Z8] Sportskeeda – How to level up quickly in KCD2: https://sportskeeda.com/esports/how-level-quickly-kingdom-come-deliverance-2
- [Z9] Method.gg – How to level up every skill fast: https://www.method.gg/kcd2/how-to-level-up-every-skill-fast-in-kingdom-come-deliverance-2
- [Z10] Gamer Guides – Scholarship (knihy, učitelé, perk Liberal Arts 10):
  https://www.gamerguides.com/kingdom-come-deliverance-ii/guide/stats-and-skills/scholarship
- [Z11] Deltia's Gaming – Scholarship (pokročilý stupeň od 18): https://deltiasgaming.com/?p=136540
- [Z12] DTF – Разбор интерфейса Kingdom Come: Deliverance II (rozbor a kritika UI): https://dtf.ru/3876402-razbor-interfeisa-kingdom-come-deliverance-ii
- [Z13] Method.gg – Armor Explained (vrstvy, statistiky, jakost, oprava, 3 sady): https://www.method.gg/kcd2/armor-explained-best-early-game-builds
- [Z14] KCD wiki.gg – Armour (KCD1, 20 slotů, definice statistik): https://kingdomcomedeliverance.wiki.gg/wiki/Armour
- [Z15] Loot Level Chill – The basics of armour: https://lootlevelchill.com/guides/kingdom-come-deliverance-2-the-basics-of-armour/
- [Z16] Sportskeeda – Charisma in KCD2 explained: https://sportskeeda.com/esports/charisma-kingdom-come-deliverance-2-explained
- [Z17] Ludo.guide – Washing clothes and armor (špína, koryto, mýdlo, lázeň):
  https://www.ludo.guide/guide/kingdom-come-deliverance-ii/getting-started/gameplay/washing-clothes-and-armor
- [Z18] Prima Games – How to wash your clothes in KCD2: https://primagames.com/tips/how-to-wash-your-clothes-in-kingdom-come-deliverance-2
- [Z19] Steam diskuze KCD2 – 3 sady oblečení, opasky na víc zbraní: https://steamcommunity.com/app/1771300/discussions/0/601894472784096065
- [Z20] Deltia's Gaming – KCD2 Inventory Explained (rozdělení inventář / menu hráče): https://deltiasgaming.com/?p=134177 ;
  Steam – inventář přetéká obrazovku: https://steamcommunity.com/app/1771300/discussions/0/601895505111290440
- [Z21] UESP – Skyrim Leveling (vzorec ceny úrovně, exponent 1,95): https://content2.uesp.net/wiki/Skyrim:Adept , https://pt.uesp.net/wiki/Skyrim:Leveling
- [Z22] Bannerlord – rychlost a mez učení (komunitní vzorce): https://nexusmods.com/mountandblade2bannerlord/mods/6519 ,
  https://www.gamerguides.com/mount-and-blade-ii-bannerlord/guide/introduction/character-development/skills
- [Z23] GamingBolt – Witcher 3 patch 1.20 (nový inventář, sekce pro ovladač): https://gamingbolt.com/the-witcher-3-wild-hunt-patch-1-20-released-changes-just-about-everything ;
  Tom's Hardware (malé písmo na TV): https://www.tomshardware.com/uk/news/witcher-3-wild-hunt-gameplay,29139.html
- [Z24] RDR2 ovládání brašny a kola zbraní: https://www.twingalaxies.com/feed_details.php/3565/read-dead-redemption-2-controls-for-ps4-and-xbox-one/15 ;
  omezení zbraní na těle: https://www.gtabase.com/red-dead-redemption-2/guides/red-dead-redemption-2-guide-combat-system-weapons-dead-eye-and-more
- [Z25] Google Android Accessibility – Touch target size (48×48 dp, 8 dp mezera): https://support.google.com/accessibility/android/answer/7101858
- Vnitřní: Warhorse KM-A-20/21/23/89 přes `docs/rozpracovane/warhorse_do_dat.md`; `docs/rozpracovane/reserse_reakce_kcd2.md`.

## Rozhodnutí Míši (29. 10.)
- **O1:** mladý Kryštof začíná skoro od nuly (umy 0–1); starý Kryštof má něco umět – návrh: Šerm 5, Jízda 5, Vojna 4, Písmo 3, Smlouvání 3, ostatní 1–2 (NEOVĚŘENO, doladí se v pískovišti).
- **O2:** bez námitky → zvyky za skutky + místa mysli (dle návrhu).
- **O3:** modely oděvů Míša nemá → stáhnout volné (CC0/CC-BY) a otestovat v pískovišti.
- **O4:** chlad ne – teplo oděvu se nezavádí.
- **O5:** názvy vloh a umů platí.

## Modely oděvů (29. 10.) – `modely/postavy/odevy/` (mimo git, jde do balíku z_postavy), zdroje `docs/rozpracovane/odevy_zdroje.md`
Vše CC0, na naší kostře 65 kostí (Quaternius): košile, rukávy, nohavice, boty nízké a vysoké, kabátec (Ranger – místo prošívanice), kapuce, nárameník, opasek, přilba hrnec a klobouk. **Chybí:** kroužky, plát/plátová kazajka, suknice, kukla, rukavice, plášť, chaperon. Nejsilnější možnost: Quaternius Source edition (20 $, CC0, 12 oděvů vč. rytíře v plátu a šlechtice, stejná kostra) – rozhodne Míša; jinak Sketchfab CC-BY (bacinet „hundsgugel“ 1390, kroužková košile, prošívanice, kukla – potřeba přihlášení a převod vah).
