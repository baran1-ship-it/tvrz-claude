# Odkaz Havrana – celý příběh

Čechy, podzim 1393 – léto 1394. Jeden příběh pro dva hrdiny: **mladého Jana (24)** a **staršího Jana (44)**.
Hlavní příběh a vedlejší linky jsou pro oba stejné. Liší se milostná linka (kap. 8 pro mladého, kap. 9 pro staršího)
a několik řádků v dialozích označených `[starší]`.

*Tento soubor je složený z jednotlivých souborů ve složce `pribeh/`. Když se něco mění, mění se tam.*

## Obsah
- 1. Úvod a dva Janové
- 2. Svět a doba
- 3. Postavy
- 4. Hlavní příběh: Havraní pečeť
- 5. Vedlejší: Lapkové od Pusté skály
- 6. Vedlejší: Milostivé léto
- 7. Vedlejší: Popel Doubravy
- 8. Láska – mladý Jan: Šenk a Kamenec
- 9. Láska – starší Jan: Vdova ze Lhoty
- 10. Drobné úkoly
- 11. Dialogy – hlavní příběh
- 12. Dialogy – vedlejší linky a láska
- 13. Pro programátora

---

## 1. Úvod a dva Janové


Čechy, podzim 1393 – léto 1394. Jeden hrdina: **Jan z Havraní**.
Jedna hlavní linka, tři vedlejší a milostný příběh (pro každého Jana jiný). Každá vedlejší linka patří k jedné ruině v lesích
a každá se vlévá do hlavního příběhu.

| Linka | Kde | Nálada | Co dá do hlavního příběhu |
|---|---|---|---|
| **Hlavní: Havraní pečeť** | tvrz Havran, celý kraj | politika, zrada, válka | – |
| Vedlejší: **Lapkové od Pusté skály** | zřícenina hrádku na hřebeni | akce, pomsta, krev | méně nepřátel při obležení, Vojtěch a jeho muži |
| Vedlejší: **Milostivé léto** | zřícený kostelík se hřbitovem | detektivka, strach z moci | otcův svitek se jmény spiklenců, pomoc od krále |
| Vedlejší: **Šenk a Kamenec** | hostinec, Kamenec, skály, tvrz | románek, dobrodružství, útěk | Anežka vynáší plány nepřítele a uprchne za novým světem, Eliška pomáhá v obležení a stane se paní z Havraní |
| Vedlejší: **Popel Doubravy** | zaniklá ves Doubrava | noční horor, vina | pravda o otci, tajná chodba pod tvrzí |

### Dva Janové – volba na začátku hry
Při nové hře si hráč vybere, kterého Jana hraje. Hlavní příběh i vedlejší linky jsou stejné.
| | **Mladý Jan (24)** | **Starší Jan (44)** |
|---|---|---|
| Kdo je | mladší syn, panoš z cizího dvora | starší syn, veterán z tažení do Litvy |
| Láska | Šenk a Kamenec (Eliška, Anežka) – `vedlejsi/laska.md` | Vdova ze Lhoty (Markéta/Olena) – `varianty/vdova.md` |
| Eliška | pravá láska, paní z Havraní | drzá holka, které Jan fandí jako strýc |
| Rozdíly v dialozích | základní text | řádky označené `[starší]` |

### Soubory
- `svet.md` – doba, ověřené historické reálie, místa (stávající i nová), kalendář
- `postavy.md` – všechny postavy, kde žijí, co chtějí, jaký model potřebují
- `hlavni_pribeh.md` – 6 kapitol, úkoly krok po kroku, spouštěče, volby a konce
- `vedlejsi/lapkove.md`, `vedlejsi/milostive_leto.md`, `vedlejsi/doubrava.md`, `vedlejsi/laska.md`
- `vedlejsi/drobne_ukoly.md` – menší úkoly na vyplnění světa
- `dialogy/` – klíčové rozhovory s volbami
- `pro_programatora.md` – co hra musí umět, příznaky (flagy), předměty, pořadí práce
- `varianty/vdova.md` – milostná linka staršího Jana: vdova Markéta ze Lhoty

### Hlavní pravidla příběhu
- Žádná fantasy. Strašidelné věci mají vždy lidské vysvětlení.
- Láska a pikantnost jako v KCD: škádlení, polibky, lázeň, a pak zatmívačka. Nic explicitního.
- Krev a smrt jsou vidět (mrtví, šibenice, ohořelé kosti), ale bez samoúčelného mučení na obrazovce.
  O mučení se jen mluví.
- Volby mají následky. Hra si pamatuje, koho jsi ušetřil a komu jsi lhal.
- Skutečné osoby (král, Rožmberk, Jošt, Jan Zhořelecký) jsou jen v pozadí, na scénu nevstupují.
  Na scéně jsou jen vymyšlené postavy.

---

## 2. Svět a doba


### Doba (ověřeno)
- **1393:** Král Václav IV. se přel s arcibiskupem Janem z Jenštejna o výnosy kladrubského kláštera.
  Arcibiskupovy úředníky dal zatknout. Jan z Pomuku byl mučen a 20. 3. 1393 svržen z Karlova mostu
  do Vltavy. Arcibiskup unikl.
- **1393:** V Praze bylo milostivé léto. Poutníci putovali do Prahy pro odpustky,
  po cestách a v hostincích jich bylo víc než jindy.
- **1393:** Proti králi se postavil moravský markrabě Jošt. Na jaře 1394 se zformovala **Panská jednota**
  (v čele Jindřich III. z Rožmberka, dále mj. Jindřich z Hradce, Vilém z Landštejna, Jan z Michalovic,
  Boček z Poděbrad).
- **8. 5. 1394:** Páni zajali krále na Králově Dvoře. Jošt se stal správcem země.
- **1. 8. 1394:** Králův bratr Jan Zhořelecký s věrnými vymohl králův návrat.
- **Mor:** Čechy zasáhly vlny moru v letech 1380–1382, v Praze umíraly tisíce lidí denně.
  Na venkově zanikaly celé vsi. Proto má smysl pustá Doubrava.
- **Lapkové:** Zchudlí zemané loupili z hrádků na cestách. Vzor: Jan Zoul z Ostředka
  přepadal z Čejchanova kupce. Král na něj poslal zemskou hotovost, hrádek dobyl a lapky popravil
  (1404, pro naši hru „o deset let dřív, jinde“).
- **Peníze:** pražské groše, 60 grošů = 1 kopa. Úrok z lánů se platí na sv. Jiří (24. 4.)
  a sv. Havla (16. 10.).
- **Smírčí kříž:** kdo zabil, mohl se smířit s rodinou mrtvého smlouvou. Platil mše,
  odškodné a postavil kamenný kříž u cesty.

### Místa, která už ve hře jsou
- **Tvrz Havran** – brána s mostem a mříží, palác s hodovní síní, komnata, ložnice, spíž,
  strážnice, kovárna, střelnice, věž, ochozy, příkop.
- **Ves Lhota** – 8 usedlostí, krčma U Kohouta, rychtář, náves se studnou a rybníčkem.
- **Zájezdní hostinec U Zlatého kola** – šenk, kuchyně, sklad, pokoje; kupecký stan; boží muka na rozcestí.
- **Potok Bystřice s mostem**, lesy, pole, **pískovcové skalní město** na hřebeni.
- **Zřícený kostelík sv. Jiljí** se hřbitovem → linka *Milostivé léto*.
- **Zaniklá ves Doubrava** (podezdívky, ohořelé trámy, studna) → linka *Popel Doubravy*.
- **Pustá skála** – zřícenina hrádku se dvěma věžemi na hřebeni → linka *Lapkové*.

### Nová místa (návrh, přidat do mapy postupně)
Seřazeno podle toho, jak brzy je příběh potřebuje.

| Místo | Co tam je | Proč |
|---|---|---|
| **Mlýn na Bystřici** (Mlýnek) | mlýnské kolo, náhon, jez, mlýnice, světnice, chlév | mlynář Kuneš je donašeč lapků; noční scéna u kola |
| **Šibenice u rozcestí** | dřevěná šibenice na kopečku, havrani | poprava, varování, nálada |
| **Lapkovský tábor ve skalním městě** (Liščí soutěska) | přístřešky z větví, ohniště, ukradené sudy, hlídka na skále | první střet s lapky |
| **Lapkovský tábor u uhlířů** (Spáleniště) | milíře, uhlířská chýše, ohrada s kradenými koňmi | lapkové se skrývají mezi uhlíři |
| **Podzemí Pusté skály** | sklep pod věží, cisterna, vězení, sklad kořisti | závěr linky lapků |
| **Krypta pod kostelíkem** | kostnice, kamenné rakve, schovaný oltářní kámen | úkryt kněze Prokopa |
| **Ves Zálesí** | 5 usedlostí na mýtině, kaple, kovář | druhá Janova ves, chudá a vystrašená |
| **Městečko Lipník** (trh, patří pánům z Lipé) | náměstí, kostel s farou, lázeň, lékárna, notář, rychta s pranýřem | trh, lékárník, kde se dá koupit jed |
| **Tvrz Kamenec** (sídlo pána z Vartenberka) | kamenná věž, dvůr, stáje, kaple | nepřítel; noční vloupání v kap. 3 |
| **Tajná chodba** | z Doubravy pod kopcem do sklepa tvrze Havran | odměna za Doubravu, rozhodující při obležení |
| **Poustevna** | chýše pod převisem ve skalním městě | poustevník Bartoloměj, svědek |

Krajina se dá rozšířit směrem k Lipníku (cesta s hostincem vede tam) a k Kamenci (za skalním hřebenem).

### Kalendář příběhu
| Kdy | Kapitola | Počasí |
|---|---|---|
| 14.–31. 10. 1393 (sv. Havel 16. 10.) | 1 Dědictví | podzim, mlhy |
| listopad 1393 | 2 Dluh | déšť, bláto |
| prosinec 1393 – únor 1394 | 3 Zima | sníh, krátké dny |
| březen – duben 1394 (sv. Jiří 24. 4.) | 4 Volba | tání, první zelená |
| květen 1394 (8. 5. zajetí krále) | 5 Obležení | jaro |
| srpen 1394 | 6 Odkaz | léto, žně |

Vedlejší linky se odemknou v kapitole 2 a dají se hrát kdykoli až do kapitoly 5.
Den a noc se střídá dál, kapitola se posune jen dokončením hlavního úkolu
(nebo spánkem „do jara“, když hráč chce přeskočit čas).

---

## 3. Postavy


Všechny postavy na scéně jsou vymyšlené. Skuteční lidé (král Václav IV., Jindřich z Rožmberka,
markrabě Jošt, Jan Zhořelecký, arcibiskup Jenštejn) se jen zmiňují.

Model: **M** = dospělý muž, **Ž** = žena, **K** = kluk ~13 let, **S** = stařec/stařena.
Z nástrojů v `nastroje/postavy` jdou zatím muž a kluk, ostatní modely jsou potřeba.

### Hrdina – dva Janové (volba na začátku hry)
**Mladý Jan z Havraní** (24, M) – mladší syn vladyky Oldřicha. Léta sloužil jako panoš na cizím dvoře,
otce skoro neznal. Vrací se, protože otec umřel. Umí luk a trochu meč, číst jen špatně.

**Starší Jan z Havraní** (44, M) – starší syn Oldřicha. Před dvaceti lety odešel s Řádem německých rytířů
na tažení do Prus a Litvy, byl u obléhání Vilniusu (1390). Šedivé spánky, šrámy, pruský meč, noční můry z ohně.
Otce dvacet let neviděl.

Oba chtějí totéž: udržet tvrz a zjistit, proč otec zemřel. Postupně zjistí, kdo otec opravdu byl.

### Tvrz Havran
| Postava | Model | Kdo to je | Co chce / tajemství |
|---|---|---|---|
| **Oldřich z Havraní** | – | mrtvý otec | V roce 1381 sloužil pánovi z Vartenberka a na jeho rozkaz zapálil zamořenou Doubravu, i se živými uvnitř. Pak se s Vartenberkem rozešel a stal se tajně královým mužem. Byl otráven. |
| **Ota Hruška** | S | starý purkrabí, otcův zbrojnoš | Věrný, mrzutý, ví o Doubravě, ale mlčí. Učí Jana boj. |
| **Ludmila** | Ž | kuchařka a klíčnice | Viděla, jak otec umíral. Myslí si, že to nebyla nemoc. |
| **Vítek** | K | páže, sirotek po strážném | Jde všude za Janem, nosí louč, vyleze, kam dospělý nevyleze. Hlavní parťák. |
| **Martin Písař** | M | písař, vede urbář a účty | **Zrádce.** Má dluhy z kostek, Kostka ho koupil. Padělal otcův dlužní úpis a přimíchal jed do vína. |
| **Vojtěch** | M | strážný | Lapkové mu na cestě zabili bratra Mikuláše. Chce pomstu. |
| **Hroch** | M | kovář | Silák, mluví málo. Kove zbraně, opraví mříž. |

### Lhota, mlýn a Zálesí
| Postava | Model | Kdo to je | Co chce / tajemství |
|---|---|---|---|
| **Matouš Bílek** | S | rychtář ve Lhotě | V roce 1381 byl u pálení Doubravy. Ukrývá přeživšího, svého synovce. |
| **Kubát** | M | krčmář U Kohouta | Ví všechno, co se kde šeptá, za pivo to řekne. |
| **Bára** | Ž | bylinkářka na kraji vsi | Pozná jed. Ves ji obviní z čarodějnictví. |
| **Kuneš** | M | mlynář na Bystřici | Donašeč lapků. Hlásí jim, kdy jedou kupci, za podíl. Má malé děti a bojí se. |
| **Tomáš „Ohořelý“** | M | přeživší z Doubravy, 25 let | Jako kluk unikl z hořící vsi. Má spálenou tvář. Zabíjí muže, kteří Doubravu zapálili. |
| **Starý Šebek** | S | sedlák v Zálesí | Poslední, kdo z pálení Doubravy žije – kromě rychtáře a Oty. |

### Cesta a hostinec U Zlatého kola
| Postava | Model | Kdo to je | Co chce / tajemství |
|---|---|---|---|
| **Ondřej Šafránek** | M | hostinský | Obviněn z vraždy poutníka. Nevinný. |
| **Eliška** | Ž | jeho dcera, šenkýřka, ~20 let | Prosí Jana o pomoc. Bystrá, drzá, viděla „kupce“ v noci na chodbě. Jan se do ní zamiluje a v kap. 6 si ji vezme – stane se paní z Havraní. |
| **Šimon** | – | mrtvý poutník | Otcův posel. Vracel se z Prahy se svitkem. |
| **Konrád z Řezna** | M | „kupec“ v kupeckém stanu | Ve skutečnosti Kostkův žoldnéř a vrah poutníka. |
| **kněz Prokop** | M | uprchlý kaplan arcibiskupa | V Praze viděl, co se dělo s arcibiskupovými lidmi. Spal s Šimonem v pokoji, při vraždě utekl a vzal jeho brašnu. Schovává se v kryptě kostelíka. |
| **Vilém Sup** | M | královský biřic | Hledá arcibiskupovy uprchlíky. Tvrdý, neúplatný. Pro krále udělá cokoli. |

### Pustá skála a lapkové
| Postava | Model | Kdo to je | Co chce / tajemství |
|---|---|---|---|
| **Bušek Vlk z Ostrého** | M | zchudlý zeman, vůdce lapků | Kdysi rytíř, dnes zloděj. Má čest jen tam, kde se mu hodí. Kostka mu platí, aby zruinoval Havraní cestu. |
| **Kašpar Řezák** | M | Buškova pravá ruka | Krutý. Zabil Vojtěchova bratra. |
| **Pivoňka** | S | uhlíř | Lapkové se mu usadili u milířů. Pomůže, když ho Jan ochrání. |
| **lapkové** | M | 10–15 chlapů | luky, sekery, kopí, kradené kabátce |

### Kamenec a páni
| Postava | Model | Kdo to je | Co chce / tajemství |
|---|---|---|---|
| **pan Hynek z Vartenberka na Kamenci** | M | mocný soused, vymyšlený člen rodu, je v Panské jednotě | Chce Havran a cestu s mýtem. Jednotu bere jako příležitost ke krádeži cizích tvrzí. Platí lapkům. |
| **Anežka z Kamence** | Ž | Hynkova mladá žena, ~22 let | Provdaná proti své vůli za starého muže. Románek s Janem, vynáší mu Kostkovy plány. Sní o moři a nakonec uprchne s kupci na jih, za novým světem. |
| **Dorota** | Ž | Anežčina komorná | Věrná paní. Nosí dopisy k dubu a v noci útěku odemkne branku. |
| **Heřman Kostka** | M | jeho purkrabí | **Hlavní protivník na scéně.** Úlisný, chytrý, nikdy si neušpiní ruce. |
| **Zbyněk z Chotče** | M | služebník pánů z Lipé | Přijede v zimě v noci. Nabízí spojenectví. |

### Lipník a páni z Lipé (spojenci)
| Postava | Model | Kdo to je | Co chce / tajemství |
|---|---|---|---|
| **pan Ješek z Lipé** | M | vymyšlený člen rodu, pán na Lipníku, otcův starý přítel | Je v Panské jednotě, ale na staré pravidlo: „Proti králi ano, proti sousedům ne.“ Vartenberka nesnáší. Chce Jana na své straně. |

### Ostatní
| Postava | Model | Kdo to je |
|---|---|---|
| **poustevník Bartoloměj** | S | žije ve skalním městě. Viděl, kdo chodí k Doubravě. |
| **farář Kliment** | M | farář v Lipníku. Pohřbí otce, přečte latinu, kterou Jan nepřečte. |
| **lékárník Jakub** | M | v Lipníku. Prodal Martinovi „lék na krysy“ (oměj). |
| **notář Mikuláš** | M | veřejný notář v Lipníku. Pozná padělanou listinu a pečeť. |

---

## 4. Hlavní příběh: Havraní pečeť


**V kostce:** Jan přijede na pohřeb otce. Zjistí, že otec byl otráven, že dluh, kterým ho soused vydírá,
je padělaný, a že otec byl tajně králův muž, který chtěl varovat krále před spiknutím pánů.
Na jaře si Jan musí vybrat stranu. V květnu 1394 páni zajmou krále a soused z Kamence
využije zmatku a oblehne Havran. To, jak Jan zvládl vedlejší linky, rozhodne, kolik má
při obležení spojenců. V srpnu je král volný a každý dostane, co si zasloužil.

Zápis kroků: **ID – úkol** · *kde* · **Spouštěč:** co hra kontroluje · **Příznak:** co si uloží.
Kroky s (NPC), (ROZHOVOR), (BOJ) potřebují věci, které hra zatím neumí – viz `pro_programatora.md`.

---

### Kapitola 1 – Dědictví (14.–16. 10. 1393)
*Učí ovládání: chůze, brána, oheň, jídlo, spánek, truhly, luk.*

*Na začátku hry si hráč vybere mladého (24) nebo staršího (44) Jana – viz README. Kapitoly jsou pro oba stejné.*

**H1.1 – Domů** · *cesta od hostince k tvrzi*
Jan přijíždí za soumraku. Na rozcestí u božích muk visí na stromě oběšenec s cedulí „LAPKA“.
Most je zvednutý. Ota Hruška křičí z ochozu, kdo jde. (ROZHOVOR) Spustí most a zvedne mříž.
**Spouštěč:** hráč u brány. **Příznak:** `ch1_prijezd`.
Bez NPC: brána se po příchodu otevře sama a na bráně je vzkaz „Vítej doma, pane. – Ota“.

**H1.2 – Poslední noc** · *hodovní síň*
Otec leží v otevřené rakvi na stole. Zapal dvě svíce/louče u márů a probdi noc (sedni si na lavici, čas skočí do rána).
Ludmila v noci přijde a zašeptá, že otec měl modré rty a cukal sebou. „To nebyla horečka, pane.“
**Spouštěč:** 2 hořící světla u márů + sezení. **Příznak:** `ch1_bdeni`, `podezreni_jed`.

**H1.3 – Pohřeb u svatého Jiljí** · *zřícený kostelík*
Otec si přál ležet v hrobce rodu u starého kostelíka, ne ve městě. Ráno průvod (Ota, Vítek, Ludmila, farář Kliment).
U hrobu Jan zahlédne čerstvé stopy v blátě vedoucí ke kryptě a cítí kouř. Vítek: „Tady straší, pane, všichni to říkaj.“
→ háček pro linku *Milostivé léto* (zatím zamčená).
**Spouštěč:** hráč dojde ke hrobce. **Příznak:** `ch1_pohreb`.

**H1.4 – Otcova truhla** · *komnata*
Klíč má Ludmila (nebo leží na stole v kuchyni). V truhle:
- **pečetní prsten s havranem** (havranovi chybí kousek zobáku – odštípnutý kámen),
- **dopis Janovi** (viz `dialogy/hlavni.md` → D-H1-dopis),
- **stará listina s pravou otcovou pečetí** (darovací listina mlýna – důležité v kap. 2),
- měšec: 3 kopy grošů.
**Spouštěč:** všechny 4 předměty v inventáři. **Příznak:** `ma_prsten`, `ma_dopis`, `ma_pravou_listinu`.

**H1.5 – Pán v domě** · *tvrz*
Rozdělej oheň v krbu, najez se ve spíži (spíž je skoro prázdná – vidíš, jak zle tvrz je), vyspi se v ložnici.
Na střelnici zkus luk (3 zásahy do terče). Ota: „Lapkové na cestě se těma terčema nenechaj strašit.“
**Spouštěč:** oheň v krbu + jídlo + spánek + 3 zásahy. **Příznak:** `ch1_tutorial`.

**H1.6 – Svatý Havel** · *nádvoří*
16. 10. přijde rychtář Matouš Bílek s úrokem. Přinese jen polovinu (8 kop místo 16): „Lidi se bojej jezdit na trh, pane, na cestě loupí.“
Volba: odpustit zbytek / chtít zbytek do Vánoc / pohrozit. (ROZHOVOR)
**Příznak:** `urok_havel` = `odpusteno` | `odlozeno` | `vyhrozeno` (ovlivní náladu vsi).
**Konec kapitoly:** na obzoru se z hřebene od Kamence blíží jezdci s praporcem pánů z Vartenberka.

---

### Kapitola 2 – Dluh (listopad – 21. 12. 1393)
*Rozjede se svět: všechny tři vedlejší linky se odemknou.*

**H2.1 – Kostka u brány** · *brána*
Heřman Kostka, purkrabí pána z Vartenberka, přiveze otcův dlužní úpis na 60 kop. Termín: sv. Tomáš (21. 12.),
jinak Havran připadne pánovi z Vartenberka. Volba, jak s ním mluvit: pustit dovnitř / jen přes mříž / poslat ho pryč šípem pod nohy.
**Příznak:** `kostka_postoj`.

**H2.2 – Pečeť** · *komnata → Lipník*
Porovnej pečeť na úpisu s pravou listinou z truhly. Na úpisu má havran **celý zobák**, na pravé listině a na prstenu kus chybí.
Úpis je padělek. Notář Mikuláš v Lipníku to potvrdí, ale řekne: „Padělek dokážeš, až budeš mít ruku, která ho psala.“
**Spouštěč:** oba dokumenty u notáře (nebo položené vedle sebe na stole v komnatě – zjednodušená verze bez NPC).
**Příznak:** `vi_padelek`.

**H2.3 – Jed** · *kuchyně, Lhota*
Ludmila ukáže džbán vína, které přišlo „darem od pana Kostky“ na sv. Václava. Na dně je usazenina.
Odnes džbán bylinkářce Báře. Pozná **oměj**: „Tím se trávěj vlci. A lidi, co někomu překážej.“
Kdo otci víno nosil? Písař Martin.
**Příznak:** `vi_jed`, `podezrely_martin`.

**H2.4 – Písař** · *tvrz, krčma, Lipník*
Hledej důkazy proti Martinovi:
- krčmář Kubát: Martin prohrál v kostkách přes 10 kop a pak najednou všechno splatil,
- lékárník Jakub v Lipníku: Martin u něj v září koupil „lék na krysy“,
- Martinova truhla v písárně: **lipová kostka s vyřezanou havraní pečetí** (padělané razidlo) a rozepsaný druhý úpis.
Pak Martina konfrontuj. (ROZHOVOR) Volba:
- **oběsit** ho na šibenici u rozcestí (spravedlnost hned, ale ztratíš svědka),
- **zavřít** do strážnice jako svědka (Kostka se ho v kap. 3 pokusí umlčet),
- **obrátit** ho: bude dál psát Kostkovi, ale co mu Jan nadiktuje (v kap. 5 velká výhoda, ale riziko zrady).
**Příznak:** `martin` = `popraven` | `vezen` | `obracen`.

**H2.5 – Svatý Tomáš** · *brána*
Kostka si přijede pro peníze. Tři cesty:
- máš důkaz (`vi_padelek` + Martin živý nebo razidlo): Kostka zbledne, ustoupí, ale vyhrožuje,
- máš 60 kop (úrok, výlov rybníka, prodej dřeva, odměny za lapky, kořist, nebo půjčka od pana Ješka z Lipé – pak mu dlužíš službu): zaplatíš a máš klid – zatím,
- nemáš nic: Kostka nechá na bráně přibít výzvu k zemskému soudu a odjede. Havran je „sporný“.
V každém případě Kostka u odjezdu řekne: „Pán z Vartenberka si vezme svý tak jako tak.“
**Příznak:** `dluh` = `dokazan_padelek` | `zaplaceno` | `sporne`.

*Během kapitoly 2 se odemknou vedlejší linky:*
- Eliška z hostince přiběhne na tvrz: v noci zabili poutníka a jejího otce odvedli → **Milostivé léto**.
- Vojtěch přinese zprávu, že lapkové u mostu přes Bystřici přepadli kupecký vůz a zabili jeho bratra → **Lapkové**.
- U studny v Doubravě najdou oběšeného kováře ze Zálesí, vesnice šeptá o mrtvých → **Popel Doubravy**.

---

### Kapitola 3 – Zima (prosinec 1393 – únor 1394)
*Přežití, temné noci, zrada zevnitř.*

**H3.1 – Do jara** · *tvrz, Zálesí*
Udrž tvrz přes zimu: hranice dříví (cíl 20 polen ve dřevníku), jídlo ve spíži (cíl 30 kusů), krb nesmí vyhasnout.
Zálesí hladoví. Volba: dát jim obilí ze sýpky (ves tě bude milovat, ale budeš mít méně) nebo ne.
**Příznak:** `zalesi_pomoc` ano/ne.

**H3.2 – Posel v bouři** · *brána, noc*
Za sněhové bouře buší na bránu jezdec: Zbyněk z Chotče, služebník pana Ješka z Lipé, otcova starého přítele.
Páni se spojují proti králi a Lipští jsou s nimi. Pan Ješek chce Jana na své straně a slibuje mu ochranu proti Vartenberkovi:
„Vartenberk je vlk. Páni z Lipé nedovolí, aby se ve jménu jednoty kradly cizí tvrze.“ Chce odpověď do sv. Jiří.
Nechá **lipský prsten s lipovými listy** jako znamení. (ROZHOVOR)
**Příznak:** `nabidka_lipe`.

**H3.3 – Vrah ve strážnici** · *strážnice, noc* (jen když `martin` = `vezen`)
V noci se někdo pokusí Martina zabít šipkou okénkem. Vítek to uslyší. Zachraň Martina, stopy ve sněhu vedou k Pusté skále.
Martin se zlomí a všechno přizná písemně → silný důkaz proti Kostkovi.
Když `martin` = `obracen`: Martin místo toho přinese Kostkovu odpověď, ze které je jasné, že Vartenberk platí lapkům.
**Příznak:** `priznani_martina`.

**H3.4 – Noc v Kamenci** · *tvrz Kamenec, noc* (nepovinné, ale velmi důležité)
Přejdi hřeben a v noci se vplíž do Kamence (tajně, v tmavém plášti, louč zhasnutá). V Kostkově písárně najdi:
- **dopis Vartenberka Kostkovi**: až páni krále zajmou, vzít Havran silou, „ať se mladý Havraní přidá ke komukoli“,
- **knihu výplat**: měsíční platby „B. V.“ (Bušek Vlk) za „čištění cesty“.
Chycen = útěk přes zeď, nebo souboj (BOJ).
**Příznak:** `dopis_vartenberka`, `kniha_vyplat`.

**H3.5 – Co nesl Šimon** · *komnata*
Farář Kliment přečte latinskou část otcova dopisu: otec čekal posla Šimona se seznamem pánů, kteří chystají zajetí krále.
Otec ho chtěl poslat králi. Šimona zabili v hostinci (→ linka *Milostivé léto*).
**Hotovo, když:** Jan má **Šimonův svitek** (z linky Milostivé léto) nebo **dopis Vartenberka** (z Kamence).
**Příznak:** `vi_o_spiknuti`.

---

### Kapitola 4 – Volba (březen – 24. 4. 1394)

**H4.1 – Svatý Jiří** · *nádvoří*
Rychtář nese jarní úrok. Po zimě je ves chudá. Volba: ulevit (méně peněz, věrná ves – v kap. 5 přijdou sedláci s cepy)
nebo vybrat všechno (víc peněz na žoldnéře, ale část sedláků uteče).
**Příznak:** `urok_jiri`.

**H4.2 – Volba strany** · *komnata, pak podle volby*
Na stole leží Šimonův svitek, otcův prsten s havranem a lipský prsten. (ROZHOVOR s Otou, který řekne svůj názor.)
Ve svitku jsou jména pánů, kteří chtějí krále zajmout. Mezi nimi i Lipští – a Vartenberk.
- **A – Králi (otcova cesta):** předej svitek královskému biřici Vilému Supovi. Ten ho pošle do Prahy.
  Pozdě – krále stejně zajmou –, ale král si to bude pamatovat. Pan Ješek z Lipé se cítí zrazen a pomoc nepošle.
- **B – S pány z Lipé:** odjeď do Lipníku a dej panu Ješkovi svitek i **dopis Vartenberka** (když ho máš).
  Ješek spálí svitek, aby nikdo z jednoty nepadl, a s Vartenberkovým dopisem jede za Rožmberkem:
  jednota bojuje proti králi, ne za loupež cizích tvrzí. Vartenberk tím ztratí zastání pánů, ale zaútočí stejně –
  ze msty a na vlastní pěst. Lipští Janovi slíbí pomoc.
- **C – Vlastní cesta:** nikomu nic nedej, svitek ukryj (třeba do hrobky otce). Pojistka na později.
**Příznak:** `strana` = `kral` | `lipe` | `sam`.

**H4.3 – Připrav se** · *tvrz*
Přijde zpráva z Kamence: Vartenberk verbuje žoldnéře. Příprava (každá věc přidá body obrany):
- kovář Hroch: 10 kopí, 5 seker (dodej železo a uhlí – uhlí od uhlíře Pivoňky),
- šípy: 60 kusů do toulců na ochozech,
- voda: 6 sudů na nádvoří a u brány (proti ohni),
- zásoby: spíž plná,
- mříž opravená (železo + kovář),
- žoldnéři: 1 kopa za muže na měsíc (najmout v Lipníku),
- spojenci z vedlejších linek (viz níže).
**Příznak:** `obrana_body` (číslo).

---

### Kapitola 5 – Obležení (květen 1394)

**H5.1 – Ohně na hřebeni** · *věž, noc*
8. 5. přijede Vítek s novinou: páni zajali krále! Té noci vidíš z věže ohně na hřebeni a na cestě.
Zvedni most, spusť mříž, rozmísti louče na ochozy.
**Spouštěč:** most nahoře, mříž dole, ≥ 6 loučí na ochozech.

**H5.2 – Vyjednávání** · *brána*
Kostka u brány s praporcem Vartenberků, za ním Bušek Vlk (když lapkové ještě žijí). Nabídne:
„Otevři bránu a odejdeš živý se svým prstenem.“ (ROZHOVOR)
Když `martin` = `obracen`: Jan už ví, odkud zaútočí (od kovárny přes příkop).

**H5.3 – Útok** · *ochozy, brána* (BOJ)
Dvě vlny útočníků s žebříky. Střílej z ochozů, házej kameny, hasič zapálenou bránu vodou ze sudů.
Počet útočníků = 30 − body ze spojenců (viz tabulka).

**H5.4 – Noc mezi útoky**
Když `chodba` (z linky Doubrava): vyjdi s Vojtěchem a Tomášem tajnou chodbou do Doubravy, obejdi tábor
a zapal jejich zásoby a beranidlo. Druhý útok bude slabší o polovinu.
Bez chodby: přečkej noc, hlídkuj, Vítek přinese zprávu, kde stojí stráže.

**H5.5 – Souboj** · *nádvoří nebo tábor* (BOJ)
Rozhodující souboj: s Kašparem Řezákem (když lapkové žijí) nebo s Kostkovým velitelem.
Kostka sám nebojuje. Když prohrává, utíká – dá se dohnat a zajmout (`kostka_zajat`).

**Výsledek obležení:** `obrana` = `ubraneno` | `tesne` | `padlo`.

#### Spojenci z vedlejších linek
| Splněno | Co to dá při obležení |
|---|---|
| Lapkové poraženi | Bušek a jeho muži chybí, −10 útočníků; Vojtěch + 2 strážní navíc |
| Lapkové obráceni (Bušek ušetřen za službu) | Bušek v noci zaútočí Kostkovi do zad |
| Milostivé léto – Ondřej očištěn | hostinský pošle 3 pacholky a varování, že nepřítel jde |
| Milostivé léto – Prokop zachráněn | Prokop přivede z Lipníku faráře a měšťany, Kostka nemůže tvrz po dobytí vypálit |
| Doubrava – smír s Tomášem | tajná chodba + Tomáš bojuje po tvém boku |
| Doubrava – Tomáš utekl | **zle:** v noci vnikne nepřítel chodbou do sklepa tvrze. Boj ve sklepě, pak chodbu zasypat |
| Doubrava – Bára zachráněna | Bára ošetřuje raněné (rychlejší léčení) |
| Zálesí nakrmeno, úrok ulevený | 6 sedláků s cepy a sekerami |
| `martin` = `obracen` | víš, odkud zaútočí; první vlna padne do pasti |
| `strana` = `lipe` | třetí ráno přijede pan Ješek z Lipé s 12 jezdci a udeří Vartenberkovým do zad |
| milostná linka (Eliška, Anežka) | viz tabulka na konci `vedlejsi/laska.md` |
| zvon nalezen (drobný úkol) | Jan zazvoní ve věži a sedláci ze Lhoty a Zálesí přiběhnou dřív |

---

### Kapitola 6 – Odkaz (srpen 1394)
1. 8. 1394 se král vrací. Do kraje přijíždí Vilém Sup s královým listem.

**H6.1 – Účty** · *tvrz nebo Lipník*
Podle toho, jak ses rozhodoval:

| Strana | Obrana | Konec |
|---|---|---|
| Král | ubráněno | **Havran nad bránou.** Král potvrdí Janovi tvrz, mýto na cestě a odebere Vartenberkovi dvůr u Bystřice. Kostka (když zajat) je souzen. Nejlepší konec. |
| Král | padlo | **Návrat.** Jan s Vítkem přijde s Vilémem Supem a hotovostí a vezme Havran zpátky. Tvrz je ohořelá, ale tvoje. |
| Lipé | ubráněno | **Lípa a havran.** Pan Ješek z Lipé vezme Jana za svého muže, Kamenec je potrestán a Kostka (když zajat) visí u rozcestí. Po králově návratu se Lipští s králem smíří a Jan s nimi. Vilém Sup mu ale nikdy nebude věřit a otec by se možná mračil. |
| Lipé | padlo | **Lipští vracejí úder.** Vartenberk Havran vypálí, ale pan Ješek ho s Janem do týdne dobude zpátky. Tvrz je ohořelá, Jan dluží Lipským víc, než kdy dlužil otec. |
| Sám | ubráněno | **Havraní hra.** Jan vymění ukrytý svitek u Jana Zhořeleckého za listinu, která mu Havran zaručí. Chytrý konec. |
| Sám | padlo | **Havran odlétá.** Jan s Vítkem odjíždí za svítání. Ve hrobce otce zůstal svitek – možná se jednou vrátí. |

**H6.2 – Otcův hrob** · *kostelík sv. Jiljí*
Poslední scéna u otcova hrobu. Když je hotová linka Doubrava se smírem: Jan a Tomáš spolu postaví **smírčí kříž**
u cesty do Doubravy. Jan položí prsten na hrob, nebo si ho nasadí. Vítek se zeptá: „A co teď, pane?“
Vedle Jana stojí Eliška s košíkem z hostince. Následuje svatba v kostelíku sv. Jiljí a Eliška se stává paní z Havraní (LE7).
Když přišel dopis s mušlí od Anežky, Jan ho drží v ruce. Pak ho schová do otcovy truhly.
Volná hra (Hospodář) pokračuje dál.

---

## 5. Vedlejší: Lapkové od Pusté skály


**V kostce:** Na zřícenině hrádku Pustá skála se usadil zchudlý zeman Bušek Vlk s bandou.
Přepadají kupce na cestě kolem hostince a mostu přes Bystřici. Platí jim purkrabí Kostka,
aby Havraní cesta zpustla a Jan neměl z mýta ani z hostince ani groš.
Vojtěchovi zabili bratra. Jan musí najít donašeče, rozprášit tábory a dobýt hrádek.

**Odemkne se:** kapitola 2 (Vojtěch přinese zprávu). **Hrát do:** kapitoly 5.
**Ladění:** nejkrvavější linka. Mrtví na cestě, oběšenci, boj v táborech.
**Historie:** podle Jana Zoula z Ostředka, který z Čejchanova přepadal kupce, dokud na něj král nepostavil zemskou hotovost.

---

**L1 – Krev u mostu** · *most přes Bystřici*
Převrácený vůz, mrtvý vozka a Vojtěchův bratr Mikuláš s šípem v zádech. Rozházené sukno a rozbité sudy.
Pod vozem se schovává kupcův synek Hanuš (K): lapků bylo deset, vůdce měl štít s vlkem, „ten s jizvou“ dobíjel raněné.
Najdi stopy: **šíp s rudě obarveným pírkem** (znak bandy), stopy koní do skalního města.
Volitelně: odvez mrtvé k božím mukám, ať je farář pohřbí (+ důvěra Vojtěcha).
**Příznak:** `L_most`.

**L2 – Liščí soutěska** · *lapkovský tábor ve skalním městě (nové místo)*
Čtyři lapkové u ohně, hlídka na skále. Hrát se dá:
- potichu: v noci sundat hlídku z luku ze skály, pak ostatní,
- nahlas: s Vojtěchem a Otou rovnou útok (BOJ).
V táboře: ukradené sudy vína z hostince, kořist, **jeden lapka přežije** – Hanzlík, mladý kluk z vesnice.
Výslech (ROZHOVOR): řekne, že kdy jedou kupci, jim „dává znamení mlynář“.
Volba s Hanzlíkem: oběsit na šibenici u rozcestí / pustit / vzít do služby jako pacholka.
**Příznak:** `L_soutezka`, `hanzlik` = `oběšen` | `puštěn` | `sluha`.

**L3 – Bílý hadr na kole** · *mlýn na Bystřici, noc*
Hlídej mlýn v noci. Když jede kupec, mlynář Kuneš pověsí na mlýnské kolo bílý hadr. Na skále nad ním se mihne světlo.
Konfrontace (ROZHOVOR): Kuneš pláče, lapkové mu vyhrožovali dětmi, a dostává podíl.
Volba:
- vydat ho rychtáři → oběšen, mlýn pustý (vznikne drobný úkol *Nový mlynář*),
- **použít ho**: dá falešné znamení a lapkové vletí do pasti (→ L4 s výhodou),
- odpustit a nechat být (lapkové se dozví, že o něm víš, a Kuneše zabijí – najdeš ho v náhonu).
**Příznak:** `kunes` = `popraven` | `past` | `zabit_lapky`.

**L4 – Vůz plný mužů** · *cesta u hostince*
Past: kupecký vůz, pod plachtou Jan, Vojtěch a strážní. Lapkové zaútočí (BOJ, 6–8 lapků).
Kašpar Řezák je zraněn a uteče k Pusté skále. Jeden zajatý lapka prozradí, kde jsou koně: u uhlířů.
Bez pasti (Kuneš popraven nebo zabit): lapky musíš stopovat k uhlířům sám, bez výhody překvapení.
**Příznak:** `L_past`.

**L5 – Spáleniště** · *uhlířské milíře (nové místo)*
Uhlíř Pivoňka se třese: lapkové u něj drží kradené koně a nutí ho dělat jim jídlo.
Osvoboď koně (3 koně – Jan si může jednoho nechat) a ochraň Pivoňku. Za odměnu ukáže
**starou odpadní šachtu**, kterou se dá vylézt do podzemí Pusté skály (dospělý neprojde, kluk ano).
**Příznak:** `L_sachta`.

**L6 – Pustá skála** · *zřícenina hrádku (+ podzemí, nové)*
Tři způsoby, jak hrádek vzít:
1. **Zemská hotovost:** ukaž Vilému Supovi **knihu výplat** z Kamence nebo zajatého lapku jako svědka.
   Sup přivede 20 královských. Velký útok za svítání, Jan vede útok na bránu.
2. **Vítek a šachta:** v noci Vítek vyleze šachtou (hraje se za Vítka? – nebo jen čekání a znamení loučí),
   otevře branku a Jan s Vojtěchem vniknou dovnitř. Tichý, nebezpečný noční útok.
3. **Vyjednávání s Buškem:** jdi sám pod bílým praporem. Ukaž Buškovi **dopis Vartenberka** – Vartenberk se ho chystá
   po obsazení Havranu „uklidit“. Bušek zuří. Volba: Bušek odejde z kraje, nebo **přejde k Janovi** (pomůže v kap. 5).
V podzemí: kořist z přepadení, vězněný kupec (vykoupit nebo osvobodit), cisterna, sklad zbraní.
**Příznak:** `pusta_skala` = `hotovost` | `vnik` | `vyjednano`.

**L7 – Kašpar** · *Pustá skála*
Zraněný Kašpar Řezák se zabarikádoval ve věži. Vojtěch chce jeho krev.
Volba:
- nech Vojtěcha, ať ho zabije (Vojtěch je spokojený, ale pak dlouho mlčí),
- spoutat ho a dát ho oběsit u rozcestí podle práva (Vojtěch nesouhlasí, ale poslechne),
- Vojtěch sám spustí meč: „Mikuláš by nechtěl, abych byl jako on.“ (jen když jsi ušetřil Hanzlíka nebo Kuneše).
**Příznak:** `kaspar` + `vojtech_vernost`.

**L8 – Kořist** · *Pustá skála → hostinec*
Vrátit zboží kupcům (odměna 10 kop, víc kupců na cestě, hostinec bohatne) nebo si ho nechat
(15 kop hned, ale kupci o tom budou mluvit).
**Hotovo:** `lapkove_konec` = `poraženi` | `obráceni`.

---

## 6. Vedlejší: Milostivé léto


**V kostce:** V hostinci U Zlatého kola někdo v noci podřízl poutníka Šimona. Byl to otcův posel,
nesl z Prahy svitek se jmény spiklenců. Hostinského Ondřeje obvinili z vraždy a královský biřic
Vilém Sup ho chce oběsit. Skutečný vrah je „kupec“ Konrád, Kostkův žoldnéř. Svitek odnesl kněz Prokop,
který spal ve stejném pokoji a utekl do krypty zříceného kostelíka. Hledá ho Sup i Konrád.

**Odemkne se:** kapitola 2 (Eliška přiběhne na tvrz). **Hrát do:** kapitoly 4 (svitek je potřeba k volbě strany).
**Ladění:** detektivka, noc na hřbitově, strach z moci.
**Historie:** milostivé léto 1393 (poutníci do Prahy), spor krále s arcibiskupem Jenštejnem,
umučení Jana z Pomuku 20. 3. 1393. O mučení se ve hře jen mluví.

---

**M1 – Mrtvý v pokoji tři** · *hostinec, pokoje*
Eliška vede Jana nahoru. Šimon leží na posteli, hrdlo podřezané, krev na podlaze i na stěně.
Druhá postel je prázdná a rozházená. Vilém Sup a dva biřici drží Ondřeje ve sklepě.
Sup: hostinec stojí na Janově půdě, takže soudit má Jan – ale Sup dává **tři dny**, pak Ondřeje oběsí sám.
**Příznak:** `M_mrtvy`.

**M2 – Stopy** · *hostinec, kupecký stan*
Najdi důkazy (pořadí libovolné, stačí 3 ze 4):
1. **nůž** v latríně za hostincem – kupecký nůž s řezenskou značkou, ne kuchyňský,
2. **krvavé otisky bot** na schodech – hostinský chodí v dřevácích, tohle jsou jezdecké boty s ostruhou,
3. **Eliška** viděla v noci na chodbě „kupce“ v plášti, myslela, že jde na latrínu,
4. **kupecký stan:** sudy jsou plné kamení a slámy, žádný kupec. Pod polštářem měšec s 5 kopami v nových groších.
Šimonovy sandály mají **dvojité dno** – prázdné. Někdo z něj něco vytáhl, nebo to Šimon měl jinde.
**Příznak:** `M_dukazy` (počet).

**M3 – Kdo spal vedle** · *hostinec → kostelík*
Hostinský přes mříž sklepa: ve druhé posteli spal poutník-kněz Prokop, „bledej jak smrt, bál se každýho“.
Venku stopy bosých nohou v blátě vedou k lesu. U kostelíka sv. Jiljí jsou ty samé stopy, které Jan viděl na pohřbu.
**Příznak:** `M_prokop_stopa`.

**M4 – Noc na hřbitově** · *kostelík sv. Jiljí, krypta (nová), noc*
Jen v noci, s loučí. Hřbitov: vyvrácené náhrobky, otevřený hrob, sova. Ve kryptě kostnice s lebkami ve výklencích.
Prokop se brání svícnem. (ROZHOVOR) Vypráví, proč utekl z Prahy: viděl, jak královi lidé odvedli arcibiskupovy úředníky,
a slyšel, co se s nimi dělo. Šimonovu brašnu vzal, protože Šimon mu řekl: „Kdyby se mi něco stalo, dones to Havranímu.“
V brašně: **Šimonův svitek** (zapečetěný, latinsky). Dá ho Janovi, jen když slíbí, že ho ochrání.
**Příznak:** `ma_svitek`, `prokop_nalezen`.

**M5 – Psi v lese** · *les, kostelík, noc*
Té noci přijdou ke kostelíku Konrádovi muži (3, BOJ) pro svitek. Zároveň v dálce štěkají Supovi psi.
Bránit kryptu, pak rozhodnout, kam s Prokopem:
- **vydat ho Supovi:** Sup je vděčný (strana Král je pak snazší), Prokopa odvezou do Prahy. Co tam s ním bude, se nedozvíš.
- **schovat ho na tvrzi:** v podkroví věže. Když ho tam Sup najde, je zle (`sup_nepritel`).
- **převést ho přes skály:** poustevník Bartoloměj zná stezku skalním městem. Noční doprovod, vyhýbat se psům a loučím biřiců.
  Na konci Prokop odejde do kláštera za hranice panství.
**Příznak:** `prokop` = `vydan` | `ukryt` | `preveden`.

**M6 – Soud v šenku** · *hostinec*
Jan soudí v šenku před lidmi. Předloží důkazy, Konrád se směje – dokud Eliška neukáže na jeho boty s ostruhou.
Konrád vytáhne nůž (BOJ v šenku, převržené stoly). Když přežije, přizná, že ho poslal Kostka.
Ondřej je volný. Sup uzná Janův soud.
Volba s Konrádem: **oběsit** u rozcestí / **vydat Supovi** / **vyměnit** Kostkovi za otcův úpis (Kostka souhlasí, ale nedodrží to).
**Hotovo:** `leto_konec`, `ondrej_ocisten`, `konrad` = ...

**Odměny:** hostinský dává Janovi podíl ze šenku (pravidelný příjem), Eliška nosí na tvrz zprávy z cesty.
Svitek je klíčový pro **H3.5** a **H4.2**.

---

## 7. Vedlejší: Popel Doubravy


**V kostce:** Před dvanácti lety (1381) přišel do vsi Doubrava mor. Tehdejší pán z Vartenberka poslal
mladého Oldřicha z Havraní, aby ves uzavřel. Oldřich ji zapálil – i s lidmi, kteří ještě žili.
Dveře drželi rychtář Bílek, kovář ze Zálesí a sedlák Šebek. Jeden kluk, Tomáš, utekl starou chodbou
pod kopcem. Dnes se vrátil a zabíjí ty, kdo tehdy drželi dveře. Vesnice věří, že si pro ně chodí mrtví.

**Odemkne se:** kapitola 2 (oběšený kovář u studny). **Hrát do:** kapitoly 5.
**Ladění:** horor bez nadpřirozena. Noc, mlha, louč, kosti, zvuky. Všechno má lidské vysvětlení.
**Historie:** mor v Čechách 1380–1382, zaniklé vsi. Smírčí kříže a smírčí smlouvy po zabití.

---

**D1 – Oběšený u studny** · *zaniklá ves Doubrava*
Ráno v mlze. Na rumpálu studny visí kovář ze Zálesí. Na prsou má vyřezané **D** a v ruce sevřený ohořelý dřevěný koník.
Vesničané se nepřiblíží. Šebek: „Mrtví z Doubravy. Já věděl, že si přijdou.“ Pak zmlkne a odejde.
Prozkoumej: stopy jen jedněch bot vedou k rozvalině největšího domu a tam mizí.
**Příznak:** `D_kovar`.

**D2 – Noc v Doubravě** · *Doubrava, noc*
Vrať se v noci s loučí (ve dne nic nenajdeš). V rozvalinách:
- čerstvý popel a ohryzané kosti od zajíce – někdo tu jí,
- zasypaný sklep: **kostry celé rodiny**, dveře zabedněné **zvenku**. Na trámu vyryto: „Bůh vidí.“,
- ve studni na laně **vědro s vodou** – studnu někdo používá,
- zvuk kroků za zdí, světlo, které zhasne. Když jdeš za ním, nikoho nenajdeš.
**Příznak:** `D_noc`, `vi_o_paleni` (ještě neví kdo).

**D3 – Čarodějnice** · *Lhota, náves*
Ves chytí bylinkářku Báru: chodí v noci do Doubravy pro byliny, prý tam „vaří s mrtvými“.
Dav ji táhne k rybníčku, kde ji chtějí potopit, chalupu už zapálili.
Zastav to: autoritou pána (stačí, když přijdeš), lukem (výstřel do vzduchu) nebo důkazem – ukaž stopy bot, Bára chodí bosá.
Když nepřijdeš včas, Bára se utopí a ve vsi ji už nenajdeš (ztratíš léčitelku i pomoc s jedem v kap. 2, pokud ještě nebyla).
**Příznak:** `bara` = `zachranena` | `mrtva`.

**D4 – Poustevník** · *skalní město, poustevna (nová)*
Bartoloměj žije ve skalách dvacet let. Viděl „muže bez tváře“, jak v noci chodí z Doubravy ke Lhotě, do stodoly rychtáře.
„A taky viděl, jak Doubrava hořela. Nebyl jsem tehdy poustevník, pane. Byl jsem tam.“ Víc neřekne.
**Příznak:** `D_poustevnik`.

**D5 – Rychtářova stodola** · *Lhota, noc*
Sleduj rychtáře Bílka: v noci nese do stodoly chléb a džbán. Ve stodole pod senem **padací dvířka** a díra do země.
Konfrontace (ROZHOVOR): Bílek se zhroutí a řekne pravdu o roce 1381. Drželi dveře. Oldřich dal rozkaz zapálit.
Tomáš je jeho synovec, přežil a vrátil se. Bílek ho živí, protože se bojí – a protože si to zaslouží.
„Další je Šebek. Pak Ota. A pak vy, pane. Jste jeho syn.“
**Příznak:** `vi_o_otci`, `D_rychtar`.

**D6 – Chodba** · *podzemní chodba (nová) mezi Doubravou, Lhotou a tvrzí*
Stará úniková chodba z doby, kdy Doubrava patřila k Havranu. Vede z Doubravy pod kopcem a jedním ramenem
**až do sklepa tvrze Havran**. Tomáš tudy chodil i do tvrze (proto Ludmila slyšela kroky ve spíži a chybělo jídlo).
Úzké, mokré, krysy, louč musí hořet, místy se jde po čtyřech. Na zdech Tomášovy značky uhlem: jména a křížky.
Šebkovo jméno je přeškrtnuté čerstvě.
**Příznak:** `chodba` (odemkne tajnou chodbu pro kap. 5).

**D7 – Oheň u studny** · *Doubrava, noc*
Tomáš drží Šebka svázaného u studny a chystá oheň. Spálená tvář, v ruce otcův starý meč (ukradený z tvrze).
(ROZHOVOR) Tomáš: „Tvůj otec mi zapálil mámu. Sestru. Mě taky. Jen jsem byl rychlejší.“
Volba:
- **zabít Tomáše** (BOJ) – Šebek žije, chodba je tvoje, ale Bílek se oběsí ve stodole,
- **vydat ho k soudu** – oběšen u rozcestí, ves si oddychne,
- **smír:** přiznáš otcovu vinu, slíbíš smírčí smlouvu – mše za mrtvé, Doubrava znovu osazená, Tomáš dostane
  pole a dům, a společně postavíte **smírčí kříž**. Tomáš odhodí meč. Šebek musí veřejně přiznat, co udělal.
  (Funguje jen když `vi_o_otci` – Jan musí vědět, za co se omlouvá. Jinak Tomáš nevěří.)
- **nestihnout:** Šebek shoří. Tomáš zmizí v chodbě a v kap. 5 se objeví u Kostky – ukáže Vartenberkovým chodbu do tvrze!
**Příznak:** `tomas` = `zabit` | `popraven` | `smir` | `utekl`.

**Odměny:** chodba, Tomáš jako spojenec (jen při smíru), Bára jako léčitelka, pravda o otci.
Při smíru se v kap. 6 na kraji Doubravy postaví první nová chalupa a kříž (scéna H6.2).

---

## 8. Láska – mladý Jan: Šenk a Kamenec


**V kostce:** Jan prožije dvě lásky. **Anežka z Kamence** je mladá žena starého pana Hynka z Vartenberka.
Zakázaný, nebezpečný románek, který Janovi dá tajemství nepřítele, ale málem ho stojí všechno.
Na konci Anežka uprchne pryč z Čech, za novým světem, a nikdo neví kam.
**Eliška**, hostinského dcera, je drzá, odvážná a věrná. S ní se Jan nakonec ožení a stane se **paní z Havraní**.
Obě linky běží vedle sebe a **ženy o sobě nikdy nevědí**. Anežka je dobrodružství a koření příběhu, Eliška je pravá láska.
Hráč rozhoduje, jestli Anežce pomůže utéct a jak se s ní rozloučí, a jak si získá Elišku.

**Odemkne se:** Eliška po M1 (vražda v hostinci), Anežka při nočním vloupání do Kamence (H3.4).
**Pikantnost:** škádlení, dvojsmysly, schovávání za závěsem, noc v bouřce, lázeň. Polibek se ukáže, víc ne –
zatmívačka a střih na ráno.
**Historie:** šlechtické dívky se vdávaly podle vůle rodiny, často za mnohem starší muže. Románek s ženou pána
byl smrtelně nebezpečný pro oba. Vladyka, který si vezme hostinského dceru, je skandál, ale ne nemožnost.
Kupecké karavany jezdily z Čech přes Alpy do Benátek – odtud lodě vozily lidi až za moře.

---

### Část 1 – Šenk (kap. 2–3)

**LE1 – Pivo na účet pána** · *hostinec, večer* (po M6)
Eliška natočí Janovi pivo „na účet pána, protože pán je teď náš hrdina“. Sedne si k němu, i když by neměla.
Smějí se Konrádovým botám. Volba: flirtovat / zůstat pánem / zeptat se na její matku (zemřela na mor).
**Příznak:** `eliska_naklonnost`.

**LE2 – Nesu ti zprávu** · *tvrz* (kap. 2–4)
Eliška chodí na tvrz se zprávami z cesty: kdo projel, kolik mužů má Kostka, co se šeptá v šenku.
Pokaždé si najde důvod zůstat déle. Ludmila ji nesnáší, Vítek ji zbožňuje.
Ota: „Hostinská holka na pánově tvrzi. Lidi budou mluvit, pane.“
**Příznak:** `eliska_naklonnost` +1 za každou návštěvu, kdy ji Jan neodbyde.

**LE3 – Oheň u Zlatého kola** · *hostinec, noc* (kap. 3)
Kostkovi muži se chtějí Elišce pomstít za Konráda. V noci zapálí stodolu a vtrhnou do šenku.
Vítek vzbudí Jana: „Hoří u Zlatýho kola!“ BOJ, hašení, záchrana.
Po boji mu Eliška čistí ránu v kuchyni pálenkou. Blízko. Velmi blízko. Skoro polibek – a pak vejde otec Ondřej.
**Příznak:** `eliska_zachranena`.

---

### Část 2 – Kamenec (kap. 3–4)

**LK1 – Za závěsem** · *Kamenec, noc* (během H3.4)
V Kostkově písárně Jana načapá mladá žena v noční košili se svící: **Anežka**, paní z Kamence.
Na chodbě duní kroky stráže. Místo křiku ho strčí za závěs ve své komnatě a stráže pošle pryč:
„Nikdo tu není. Jen já a moje modlitby.“ Za závěsem stojí tak blízko, že slyší její dech.
„Ty jsi ten mladej Havraní, co ho chce můj muž sežrat. Vypadáš chutněji, než říkal.“
Pomůže mu ven oknem do příkopu. Na rozloučenou: „U božích muk je dutej dub. Napiš mi.“
**Příznak:** `anezka_potkana`.

**LK2 – Dutý dub** · *boží muka na rozcestí* (kap. 3–4)
V dutině dubu si nechávají dopisy (předměty). Anežka píše o kleci, o starém muži, o tom, že chce vidět moře,
a mezi tím vynáší **Kostkovy plány**: kolik má žoldnéřů, kdy dorazí, kde budou stát.
Jan odpovídá – volby v dopise: o sobě / o tvrzi / škádlivě o tom, co by s ní dělal, kdyby nebyla vdaná.
**Příznak:** `anezka_dopisy` (počet), `vi_plany_kamence` (od 3 dopisů).

**LK3 – Pouť do bouřky** · *hostinec → poustevna ve skalách* (začátek jara)
Anežka jede s komornou „na pouť do Prahy“ – milostivé léto je skvělá záminka. Zastaví se v hostinci.
Eliška ji obsluhuje a nemá tušení. Večer se Anežka „ztratí“ cestou do skal. Jan ji najde u poustevny.
Přijde bouřka, poustevník Bartoloměj je zrovna ve Lhotě. Oheň, mokré pláště, polibek. Zatmívačka.
Ráno stojí Bartoloměj ve dveřích, neřekne nic, jen se pokřižuje.
Anežka u ohně: „Jednou odsud uteču, Havraní. Tam, kde mě nikdo nezná. Možná až za moře.“
**Příznak:** `anezka_noc`.

**LE4 – Svatba ve Lhotě** · *Lhota* (U10, jaro)
Na svatbě Jan tančí s Eliškou. Večer u rybníčka první polibek. Eliška: „Já vím, že se pán nežení s šenkýřkama.
Tak mi aspoň neříkej žádný lži.“
**Příznak:** `eliska_polibek`.

---

### Část 3 – Dopis v dubu (konec kap. 4)

**LK4 – Prozrazená** · *rozcestí, Kamenec*
Kostka najde dopis v dutém dubu. Jméno Havraní v něm není, jen „můj havrane“ – Kostka tuší, ale nemá důkaz.
Hynek nechá Anežku zavřít ve věži Kamence a chce ji poslat do kláštera „nebo hůř“. Ven to nepustí:
paroháč mezi pány z jednoty by byl pro smích. V dubu Jan najde poslední vzkaz, škrábnutý uhlem:
„Věž. Pomoz mi. – A.“
**Příznak:** `anezka_zavrena`.

---

### Část 4 – Útěk a lázeň (kap. 5–6)

**LK5 – Věž v Kamenci** · *Kamenec, noc během obležení* (H5.4)
Vartenberkovi jsou u Havranu, na Kamenci zůstalo jen pár stráží. Anežčina komorná Dorota nechá
v noci **odemčenou zadní branku** a na zdi rozsvítí louč jako znamení. Jan s Vítkem (nebo s Vojtěchem)
proklouznou dovnitř, Vítek odláká stráž házením kamenů do stáje, Jan vyleze do věže a vyvede Anežku.
Na útěku je musí honit stráž s psy přes hřeben – nejdivočejší noc celé hry.
Když Jan nepřijde: Anežka uteče sama. Ve věži Jan později najde jen provaz ze svázaných prostěradel, visící z okna,
a na posteli její šátek.
**Příznak:** `anezka_utek` = `s_janem` | `sama`.

**LK6 – Za novým světem** · *most přes Bystřici, svítání*
(jen s `anezka_utek = s_janem`) Na mostě čeká kupecká karavana na jih. Anežka v prostém plášti, vlasy pod šátkem.
„Ty sem patříš, Havraní. Ke svý tvrzi, ke svým lidem. A já patřím někam, kde ještě nikdo nebyl.“
Kam jede, neřekne. Volba: poslední polibek / jen ruka / dát jí na cestu měšec grošů.
Karavana zmizí v mlze.
Když utekla sama, Jan se rozloučit nestihne. Jen Vítek tvrdí, že ji viděl na voze s kupci jedoucími na jih.
V kap. 6 může přijít **dopis bez podpisu**, s mořskou mušlí uvnitř a jedinou větou:
„Moře je větší, než jsem myslela.“ Odkud přišel, nikdo neví.
**Příznak:** `anezka = uprchla`.

**LE6 – Lázeň** · *tvrz Havran, lázeňská káď, noc* (po obležení)
Eliška zůstane na tvrzi ošetřovat raněné. V noci připraví Janovi koupel, „ať pán nesmrdí jako bitva“. Zůstane.
Zatmívačka. Ráno ji Ota najde na schodech: „No, tak to bude paní.“

**LE7 – Paní z Havraní** · *kostelík sv. Jiljí* (kap. 6)
Jan musí Elišku nejdřív požádat – u studny ve Lhotě, na kolenou, před půlkou vsi. Eliška: „Pán se žení se šenkýřkou?
Ota to nepřežije.“ – „Přežije.“ – „Tak jo.“
Svatba v kostelíku sv. Jiljí, farář Kliment, celá Lhota, Ota bručí, Ludmila pláče, Vítek nese prsten. Tanec do rána.
Od té doby je Eliška **paní z Havraní**. V Hospodáři vede spíž a stará se o šenk (víc peněz z hostince).
**Příznak:** `laska = eliska`, `svatba`.

---

### Co to dá v obležení
| Příznak | Účinek |
|---|---|
| `vi_plany_kamence` | víš, kdy a odkud zaútočí, Vartenberk má o 5 mužů méně (padnou do pasti) |
| `eliska_naklonnost` ≥ 3 | Eliška přivede z hostince pacholky, v noci přenáší přes příkop šípy a jídlo |
| `anezka_zavrena` | Hynek je vzteky bez sebe a útočí ukvapeně: první vlna přijde dřív, než jsou všichni jeho muži na místě |
| `anezka_utek = s_janem` | Hynek se dozví, že mu utekla žena, a polovina jeho žoldnéřů odjede hledat ji – druhý útok je slabší |

---

## 9. Láska – starší Jan: Vdova ze Lhoty


*Milostná linka pro **staršího Jana (44)**. Mladý Jan (24) místo ní hraje linku Šenk a Kamenec (`vedlejsi/laska.md`).*

**V kostce:** Jan není mladý panoš, ale **muž kolem 44 let**, který se po dvaceti letech vrací z válek na východě.
Ve Lhotě žije **vdova Markéta** (35), včelařka, o které ves šeptá, že otrávila muže.
Je cizí, mluví s přízvukem a v noci se modlí jinak než ostatní. Jan ji odněkud zná – a ona jeho taky.
Postupně vyjde najevo, že se potkali už jednou: v hořícím Vilniusu v roce 1390.

**Pikantnost:** včelí žihadlo na krku, noční koupání v Bystřici za úplňku, medovina u ohně. Polibek ano, dál zatmívačka.
**Nálada:** zralá, pomalá, hořkosladká láska dvou lidí, kteří už mají něco za sebou.

---

### Co se mění v hlavním příběhu
- **Jan z Havraní (44):** starší syn Oldřicha. Ve 24 letech odešel na Prusy a do Litvy s Řádem německých rytířů
  na „reisy“ – válečná tažení proti Litvě, kam jezdili rytíři z celé Evropy. Má šrámy, šedivé spánky, pruský meč
  a noční můry z ohně. Otce dvacet let neviděl a teď se vrací na jeho pohřeb.
- **Ota:** místo „ten malej Jan“ říká „Jan? Ten, co odešel s křižákama, když mi ještě nešedivěly vousy?“
- **Vítek** zůstává páže. Pro staršího Jana je skoro jako syn.
- **Eliška** zůstává hostinského dcera, ale bez lásky – pro Jana je to drzá holka, které fandí jako strýc.
- **Anežka z Kamence** zůstává jako spojenkyně bez románku: schová Jana za závěsem, posílá dopisy v dubu
  s Kostkovými plány a Jan ji vyvede z věže. Pro staršího Jana je to zoufalá mladá žena, které pomůže na svobodu
  jako otec dceři. Pikantní scény (LK3 bouřka v poustevně) se pro staršího Jana přeskočí.

### Historie (ověřeno)
- Řád německých rytířů s litevským knížetem Vytautem obléhal **Vilnius od 11. 9. do 7. 10. 1390**.
  **Křivý hrad** padl 16. 9., nejspíš kvůli zradě nebo panice při požáru. Asi tisíc obyvatel zahynulo a dva tisíce
  odvlekli do zajetí. Hrad byl zničen a už ho neobnovili. Obléhatelé nakonec kvůli počasí a zásobám odtáhli.
- Ve Vilniusu žili Litevci, Rusíni (pravoslavní) i němečtí kupci. Proto se Markéta modlí po rusínsku.

---

### Postavy
| Postava | Model | Kdo to je | Tajemství |
|---|---|---|---|
| **Markéta, vdova** (35) | Ž | včelařka na kraji Lhoty, vaří nejlepší medovinu v kraji | Ve skutečnosti **Olena**, dcera rusínského kupce z Vilniusu. Při pádu Křivého hradu ji odvlekl český žoldnéř Mikeš Krahulec, přivezl ji do Čech a vzal si ji. Česky ji pojmenoval Markéta. |
| **Mikeš Krahulec** | – | její mrtvý muž | Žoldnéř z reisy, surovec a pijan. Loni v zimě se utopil v rybníčku. Markéta ho tam viděla padat – a nepomohla mu. |
| **Zikmund Kolář** | M | Krahulcův bývalý druh ze žoldu | Přijede pro **stříbro z Vilna**, které Krahulec ukradl z kostela a schoval. |
| **Bára, bylinkářka** | Ž | (už ve hře) | Jediná ve vsi, kdo Markétu bere. Ví, že ji muž bil. |

---

### Úkoly

**V1 – Medovina** · *Lhota, náves* (kap. 1–2)
Na trhu ve vsi prodává vdova medovinu. Když Jan přijde, upustí džbán. Dívá se na jeho pruský meč a šrám přes ruku.
„Pán byl na severu.“ Není to otázka. Jan má pocit, že ji zná. Ona odejde dřív, než se stihne zeptat.
**Příznak:** `marketa_potkana`.

**V2 – Co se šeptá** · *krčma, rychta, rybníček*
Kubát: „Otrávila ho, pane. Cizí ženská, mluví divně, modlí se k obrázkům.“ Rychtář Bílek: Krahulce našli
v rybníčku pod ledem, opilého. Bára: „Bil ji. Každou sobotu. Nikdo nic neviděl, protože nikdo nechtěl.“
Na ledě tehdy byly stopy dvou lidí. Jedny se zastavily na břehu a pak odešly.
**Příznak:** `vi_o_krahulci`.

**V3 – Včely** · *Markétin dvorek, úly v klátech*
Markéta potřebuje vykouřit roj, který usedl na lípu. Jan drží kouřák, ona sbírá roj do koše.
Včela ji žihne do krku. „Vytáhněte to, pane. Já tam nevidím.“ Jan jí opatrně vytáhne žihadlo – velmi blízko.
Ona se usměje poprvé: „Na křižáka máte jemné ruce.“ (ROZHOVOR, škádlení)
**Příznak:** `marketa_naklonnost`.

**V4 – Píseň u ohně** · *Markétina chalupa, večer*
Medovina, oheň. Markéta tiše zpívá písničku v cizí řeči. Jan ji zná. Slyšel ji v noci, kdy hořel Vilnius.
Kus po kusu skládá vzpomínku: hořící ulice pod Křivým hradem, mladá žena v kouři, kterou vynesl z domu –
a pak ji předal svým lidem, „ať ji odvedou do bezpečí“. Mezi nimi byl Krahulec.
**Příznak:** `jan_si_vzpomnel`.

**V5 – Bystřice za úplňku** · *potok pod mlýnem, noc*
Jan jde v noci ke Bystřici a najde tam Markétu, jak se koupe. Ona se neschová. „Pán se dívá, nebo se přidá?“
Volba: odejít / přidat se. Studená voda, smích, polibek na břehu, zatmívačka.
Ráno: medovina na stole a vzkaz „Přijď zase“ – ale napsaný **cyrilicí**. Jan ho nepřečte, jen tuší.
**Příznak:** `marketa_noc`.

**V6 – Stříbro z Vilna** · *Lhota, chalupa, noc* (kap. 3–4)
Do kraje přijede Zikmund Kolář. Hledá Krahulcovo stříbro – kalich a monstranci z vilniuského kostela.
V noci přepadne Markétu. Jan dorazí (Vítek ho varuje) – BOJ v chalupě, převrhnuté úly, rozzuřené včely.
Kolář před smrtí nebo v poutech řekne Markétě, kdo ji tehdy ve Vilniusu předal Krahulcovi: „Tenhle, panička.
Tenhle tě vynes z ohně a dal nám tě jak pytel obilí.“
→ **Volba před tím (V4):** když Jan Markétě pravdu řekl sám dřív, Kolářova slova nic nezmění:
„Já vím. Řekl mi to sám.“ Když ji zamlčel, Markéta zbledne a odejde do tmy.
**Příznak:** `pravda_marketa` (Jan to řekl sám) / `marketa_zrazena`.

**V7 – Kalich** · *Markétina chalupa, pod podlahou úlu*
Stříbro je zakopané pod úlem. Co s ním:
- **dát kostelíku sv. Jiljí** (farář Kliment ho posvětí znovu, ves bude Markétu brát jinak),
- **prodat** a zaplatit dluh Kostkovi (60 kop – řeší H2.5, ale Markéta na to bude koukat ztuha),
- **dát Markétě** – ať si rozhodne sama. Ona ho dá do kostelíka a jeden malý stříbrný křížek si nechá.
**Příznak:** `kalich`.

**V8 – Olena** · *tvrz nebo Lhota* (kap. 6)
- s `pravda_marketa`: Markéta Janovi řekne své pravé jméno – **Olena**. Je to největší dar, jaký mu může dát.
  Svatba v kostelíku sv. Jiljí. Ves šeptá dál, ale už jen o tom, jak mladě vedle ní pán vypadá.
  Olena je **paní z Havraní**. Na tvrzi jsou úly a v Hospodáři se prodává medovina.
- s `marketa_zrazena`: Markéta se s Janem rozloučí u božích muk. Odjede s kupci na východ, domů – nebo co z něj zbylo.
  Nechá mu na prahu džbán medoviny. Jan může jet za ní – dlouhý úkol, který končí v Lipníku, kde ji dohoní
  a na trhu před všemi poprosí o odpuštění. Kdo to stihne, má svatbu taky. Kdo ne, má jen medovinu.
**Příznak:** `laska = marketa` | `marketa_odesla`.

---

### Co to dá v obležení
| Příznak | Účinek |
|---|---|
| `marketa_naklonnost` ≥ 3 | Markéta ošetřuje raněné medem a bylinami (léčení rychlejší) |
| `laska = marketa` | **úly na ochozu**: Markéta poradí shazovat úly na útočníky u brány, první vlna se rozprchne |
| `jan_si_vzpomnel` | Jan ví z Vilniusu, jak se hrady berou ohněm. Hasení brány je rychlejší (víc vody, méně škody) |

### Dialogy

#### D-V1-medovina
*Náves, Markéta za stolkem se džbány. Upustí jeden.*

MARKÉTA: Pán byl na severu. *(dívá se na meč)* Tohle kovají v Prusích.
1. „Dvacet let. Ty taky nejsi odsud.“ → MARKÉTA: Nikdo tady není odsud, pane. Jen někdo to umí lépe skrývat.
2. „Kolik za džbán?“ → MARKÉTA: Pro pána nic. Je rozbitej.

#### D-V3-zihadlo
*Dvorek, bzučení roje.*

MARKÉTA: Au! Do krku… Vytáhněte to, pane. Já tam nevidím.
*Jan se skloní.*
MARKÉTA: Opatrně. Žihadlo se nemá mačkat, ale vyškrábnout. *(tiše)* Na křižáka máte jemné ruce.
1. „Na vdovu máš hebkou kůži.“ → MARKÉTA: *(zrudne, pak se zasměje)* Za tohle vás v kostele nepochválí. `marketa_naklonnost +2`
2. „Hotovo.“ → MARKÉTA: Děkuju. *(dlouze se podívá)* `marketa_naklonnost +1`

#### D-V4-pisen
*Chalupa, oheň, medovina. Markéta dozpívá.*

JAN: Tu píseň znám.
MARKÉTA: *(ztuhne)* Nemůžete. Zpívala ji jen moje máma. A pak už nikdo.
JAN: Vilnius. Pod Křivým hradem. Hořelo to celou noc.
1. „Vynesl jsem z ohně ženu. A dal ji svým lidem. Mezi nimi byl Krahulec. Byla jsi to ty.“ → MARKÉTA: *(dlouho mlčí, pak mu vezme ruku)* Zachránil jsi mě a prodal jsi mě. Jednou nocí. *(nepustí ji)* `pravda_marketa`
2. *Neříct nic.* „Byl jsem tam. Je to dávno.“ → MARKÉTA: Je to dávno. *(dolije mu)* `jan_si_vzpomnel`

#### D-V5-bystrice
*Potok, úplněk. Markéta po pás ve vodě, mokré vlasy na ramenou.*

MARKÉTA: Pán se dívá, nebo se přidá?
1. *Přidat se.* → MARKÉTA: *(cákne na něj)* Je ledová! *(smích, polibek, zatmívačka)* `marketa_noc`
2. „Odpusť. Půjdu.“ → MARKÉTA: Škoda, pane. Úplněk je jen jednou za měsíc.

#### D-V8-olena
*Ochoz Havranu, západ slunce.*

MARKÉTA: Chceš vědět, jak se jmenuju doopravdy?
JAN: Jestli mi to chceš říct.
MARKÉTA: Olena. *(usměje se)* Nikdo to tu neumí vyslovit. Tak to budeš říkat jen ty.

---

## 10. Drobné úkoly


Krátké úkoly, které oživí svět, dají peníze na dluh a body obrany. Většinou na 10–30 minut.

| ID | Úkol | Kde | Od kap. | O co jde | Odměna |
|---|---|---|---|---|---|
| U1 | **Zvon sv. Jiljí** | kostelík, rybník u Doubravy | 2 | Za války kdysi zvon zakopali. Najdi stopy (zápis v otcově truhle, starý Šebek), vykopej ho, kovář Hroch ho opraví, zavěs na věž tvrze. | V kap. 5 zvonem svoláš sedláky dřív. |
| U2 | **Ostatky svatého Jiljí** | hostinec | 2 | Kramář prodává poutníkům „kost sv. Jiljí“. Je to kost z kostnice v kryptě. Odhalit ho / vzít podíl / nechat být. | 2 kopy nebo vděk faráře Klimenta |
| U3 | **Výlov** | rybník ve Lhotě | 2 | Listopadový výlov: vypustit stavidlo, nosit ryby do kádí, prodat v Lipníku. | 8 kop, ryby do spíže |
| U4 | **Vlk v ovčíně** | Zálesí, noc | 3 | Ve sněhu vlčí stopy, roztrhané ovce. Čekat v noci u ohrady s lukem. | kožešina, vděk Zálesí |
| U5 | **Pytláci** | panský les | 2 | V lese oka na srnce. Pytlák je Kubátův syn Jíra. Potrestat (pokuta, pranýř) / odpustit / vzít za lovčího. | lovčí na tvrzi, nebo 1 kopa pokuta |
| U6 | **Nový mlynář** | mlýn | po L3 | Když mlynář Kuneš zemře, mlýn stojí. Najdi v Lipníku mlynářského tovaryše, oprav jez. | nájem z mlýna |
| U7 | **Železo pro Hrocha** | Lipník, trh | 4 | Kovář potřebuje železo na kopí a mříž. Smlouvat na trhu, převézt vozem. | zbraně, body obrany |
| U8 | **Turnaj lučištníků** | Lipník, trh | 3–4 | Střelba na terče, na papouška na tyči. Vítěz dostane stříbrný pohár a pozornost pana Ješka z Lipé. | 3 kopy, lepší luk |
| U9 | **Uhlí** | Spáleniště | po L5 | Pivoňka znovu pálí milíře. Pomoz mu postavit milíř (nosit polena, zakrýt drnem, hlídat noc). | uhlí pro kovárnu |
| U10 | **Svatba ve Lhotě** | Lhota | 4 | Jarní svatba. Pán má přinést dar a tancovat s nevěstou. Zkazit to nebo ne. | nálada vsi |
| U11 | **Kdo chodí do spíže** | tvrz, noc | 2 | Ludmile mizí jídlo a v noci slyší kroky. Hlídat spíž. Stopy mizí ve zdi sklepa – vede to k chodbě z linky Doubrava. | háček pro D6 |
| U12 | **Vítkův pes** | les | 1–2 | Vítkovi utekl pes Bodlák. Najít ho ve skalním městě v liščí noře. | pes chodí s Vítkem, štěká na nepřátele v noci |
| U13 | **Šibenice** | rozcestí | 1 | Oběšenec u božích muk z úvodu. Sundat ho a pohřbít? Jméno na ceduli neodpovídá – byl to obyčejný pocestný. Lapkové ho pověsili pro výstrahu. | háček pro Lapky |

---

## 11. Dialogy – hlavní příběh


Formát: `MLUVČÍ: text`. Volby hráče jsou číslované, za šipkou je, co se stane a jaký příznak se uloží.
Mluví se lehce staročesky, ale tak, aby tomu rozuměl i kluk.

---

### D-H1-brana (H1.1)
*Soumrak, most zvednutý. Ota na ochozu s lukem.*

OTA: Stůj! Kdo jde k Havranu po setmění?
JAN: Jan. Oldřichův syn.
OTA: …Jan? Ten malej Jan, co utek ke Šternberkům na panoše? Ukaž se ve světle.
OTA `[starší]`: …Jan? Ten, co odešel s křižákama, když mi ještě nešedivěly vousy? Ukaž se ve světle.
1. *Zvedni louč k obličeji.* → OTA: Oči máš po mámě, chudák. *(`[starší]`: Pánbůh, ty jsi zestárnul. Já taky.)* Spouštím most. Zavři za sebou, pane. Lapkové se tu po tmě toulaj.
2. „Otevři, nebo tě nechám vyhnat jak psa, až budu uvnitř.“ → OTA: *(chvíli mlčí)* Po otci máš i jazyk. Spouštím. `ota_nalada -1`

---

### D-H1-bdeni (H1.2)
*Noc, síň, svíce u rakve. Ludmila přijde se šálem kolem ramen.*

LUDMILA: Pane… nespíte? Ani já ne. Musím vám něco říct, dokud to nepozřu.
LUDMILA: Pán neumřel na horečku. Měl modrý rty. Cukal sebou a hlava ho pálila, jako by mu někdo nalil do žil oheň.
LUDMILA: A ten den pil to víno. Co přišlo od pana Kostky na svatýho Václava.
1. „Kdo mu to víno nosil?“ → LUDMILA: Písař Martin. Jako vždycky. `podezreni_jed`
2. „Mlč o tom. Nikomu ani slovo.“ → LUDMILA: Jak poroučíte. Ale já vím, co jsem viděla. `podezreni_jed`

---

### D-H1-dopis (H1.4) – text dopisu
*Čte se, když hráč otevře dopis z truhly. Část je latinsky – Jan ji nepřečte.*

> Jene,
> jestli tohle čteš, nedožil jsem se, abych ti to řekl do očí. Nejsem dlužen pánům z Vartenberka ani groš.
> Cokoli ti přinesou s mou pečetí, je lež. Moje pečeť má havrana s ulomeným zobákem. Pamatuj si to.
> Čekej posla Šimona. Co nese, patří králi. *[Dva řádky latinsky.]*
> Je tu ještě Doubrava. Ota ví. Nechtěl jsem, abys to věděl, a teď nevím, jestli je horší, když to víš, nebo když ne.
> Odpusť mi, synu. Bůh mi neodpustí.
> Oldřich

---

### D-H1-havel (H1.6)
*Nádvoří, rychtář Bílek se dvěma měšci.*

BÍLEK: Svatej Havel, pane, úrok. Je tu osm kop. Víc… víc nemáme.
BÍLEK: Lidi nejezdí na trh. Na cestě loupí. Kubátovi vzali vůz i s koněm a Pánbůh ví, kde je čeledín.
1. „Zbytek vám odpouštím. Letos.“ → BÍLEK: Pán Bůh vám to oplať. Ves na to nezapomene. `urok_havel = odpusteno`
2. „Zbytek do Vánoc.“ → BÍLEK: Budem se snažit, pane. `urok_havel = odlozeno`
3. „Jestli to do neděle nebude, zabavím dobytek.“ → BÍLEK: *(sklopí oči)* Jak řeknete, pane. `urok_havel = vyhrozeno`, `ves_nalada -2`

---

### D-H2-kostka (H2.1)
*Brána. Kostka na koni, za ním dva zbrojnoši s vartenberskou korouhví.*

KOSTKA: Pan Jan z Havraní! Upřímnou soustrast. Váš otec byl… zvláštní člověk.
KOSTKA: Nerad otravuju v čas smutku. Ale tady je úpis. Šedesát kop. Do svatýho Tomáše.
KOSTKA: Jinak tvrz propadá pánu z Vartenberka. Tak to otec podepsal. Vidíte pečeť? Havran.
1. „Pojďte dál, promluvíme si u ohně.“ → Kostka vejde, prohlíží si tvrz jako by už byla jeho. `kostka_postoj = vpusten`
2. „Úpis mi ukažte přes mříž. Dál nepůjdete.“ → KOSTKA: Opatrnost po otci. Chválím. `kostka_postoj = mriz`
3. *Vystřel šíp do země před jeho koně.* → KOSTKA: *(kůň se plaší)* To si zapamatuju, mladej pane. `kostka_postoj = sip`, `kostka_nenavist +1`

---

### D-H2-martin (H2.4)
*Písárna. Na stole lipová kostka s vyřezaným havranem.*

MARTIN: Pane? To je… to jsem vyřezával pro zábavu. Zimní večery jsou dlouhý.
JAN: S celým zobákem. Otcův havran ho měl ulomený.
MARTIN: *(zbledne)* Měl jsem dluhy, pane. Kostka mě měl v hrsti. Říkal, že to víno je jen na spaní, aby pán…
MARTIN: Já nevěděl, že je to jed! Přísahám na svatou Ludmilu!
1. „Oběsím tě u rozcestí. Dnes.“ → `martin = popraven`. Ota mlčky vezme provaz.
2. „Půjdeš do strážnice. Až přijde čas, řekneš to před soudem.“ → `martin = vezen`
3. „Budeš Kostkovi psát dál. Ale to, co ti nadiktuju já.“ → MARTIN: Cokoli, pane. Cokoli! `martin = obracen`

---

### D-H3-posel (H3.2)
*Noc, sněhová bouře. Jezdec za mříží, na plášti lipové listy.*

ZBYNĚK: Zbyněk z Chotče, služebník pana Ješka z Lipé. Pusťte mě, ať tady nezmrznu.
ZBYNĚK: *(u krbu)* Pán vzkazuje: přicházejí jiné časy. Páni se spolčujou. Rožmberk, Hradečtí, my.
ZBYNĚK: Král si s nimi nedělá hlavu, tak si páni udělají hlavu s králem.
ZBYNĚK: Pan Ješek měl vašeho otce rád, i když se v posledních letech rozešli. Chce vás mít na své straně.
ZBYNĚK: A Vartenberk? Pan Ješek říká: proti králi ano, proti sousedům ne. Vlka si ohlídá.
ZBYNĚK: Odpověď do svatýho Jiří. Tady je prsten pana Ješka. Kdybyste přijel, ukažte ho v bráně.
1. „Vyřiď panu Ješkovi, že o tom budu přemýšlet.“ → `nabidka_lipe`
2. „Můj otec byl králův muž.“ → ZBYNĚK: Váš otec je mrtvej, pane. A vy jste živej. Zatím. `nabidka_lipe`

---

### D-H4-ota (H4.2)
*Komnata. Na stole svitek, dva prsteny.*

OTA: Tak co, pane. Král, nebo Lipští?
1. „Co bys udělal ty?“ → OTA: Já? Já držel dveře v Doubravě, protože mi to pán poručil. Od tý doby nevím, co je správně. Ale vím, že pan Ješek drží slovo. A král… král je daleko.
2. „Co by udělal otec?“ → OTA: Poslal by to králi. A kvůli tomu je teď pod zemí.
3. „Rozhodnu sám.“ → OTA: Tak rozhodněte. A rozhodněte se brzo. Na Kamenci už brousej meče.

---

### D-H5-vyjednavani (H5.2)
*Brána, ráno po ohních. Kostka pod bílým praporem, za ním vojsko.*

KOSTKA: Mladej Havraní! Krále zavřeli páni. Žádnej král tě nezachrání.
KOSTKA: Otevři bránu a můžeš odejít. S prstenem, s koněm, s tím klukem. Nikdo vám nezkřiví vlas.
1. „Pojď si pro ni.“ → Útok začíná.
2. „Tvůj pán zradil i jednotu. Pan Ješek to ví.“ *(jen když `strana = lipe`)* → KOSTKA: *(zaváhá)* Pan Ješek je daleko. → Útok začíná, ale třetí den přijedou Lipští.
3. „Kolik ti zaplatil za otcovu smrt, Kostko?“ *(jen když `priznani_martina`)* → Žoldnéři za Kostkou si začnou šeptat. −5 útočníků (část odejde).

---

### D-H6-konec (H6.2)
*Kostelík sv. Jiljí, srpen, cvrčci. Jan u otcova hrobu, Vítek opodál.*

VÍTEK: Pane? Co jste mu řek?
1. „Že jsem to udržel.“ *(obrana ubráněna)*
2. „Že jsem to ztratil. Ale ještě ne navždy.“ *(obrana padla)*
3. „Že mu Doubrava odpustila. Aspoň trochu.“ *(jen při `tomas = smir`)*
VÍTEK: A co teď?
JAN: Teď? Teď jsou žně, Vítku. A pak bude zas svatej Havel.

---

## 12. Dialogy – vedlejší linky a láska


Formát stejný jako v `hlavni.md`.

---

### Lapkové

#### D-L1-hanus (L1)
*Pod převráceným vozem se třese kluk.*

HANUŠ: Nechte mě! Nic nemám! Všechno vzali!
1. „Klid. Jsem Jan z Havraní. Pán tady.“ → HANUŠ: Pán? Tak proč jste nás nechránil?! *(rozbrečí se)* Táta… táta utek do lesa. Nevím, jestli žije.
HANUŠ: Bylo jich deset. Jeden měl štít s vlkem. A jeden s jizvou přes pusu chodil a… a dobíjel, kdo ještě sténal.
VOJTĚCH: *(tiše)* Kašpar. Ten s jizvou je Kašpar Řezák.

#### D-L2-hanzlik (L2)
*Svázaný mladý lapka u vyhaslého ohně.*

HANZLÍK: Nezabíjejte mě, pane! Jsem ze Zálesí, Vavřincův, jen jsem neměl co jíst!
1. „Kdo vám dává vědět, kdy jedou kupci?“ → HANZLÍK: Mlynář! Na kolo pověsí bílej hadr. Víc nevím, přísahám!
2. „Kolik jich je na Pustý skále?“ → HANZLÍK: Patnáct, možná víc. A pan Bušek. On byl rytíř, pane, opravdovej.
3. „Kdo vám platí?“ → HANZLÍK: Nějakej pán z Kamence. Kašpar mu jezdí pro peníze každej měsíc.

#### D-L3-kunes (L3)
*Mlýn, noc. Kuneš drží v ruce bílý hadr.*

KUNEŠ: Pane… já… mám tři děti. Říkali, že když nebudu dávat znamení, hodí je do náhonu.
KUNEŠ: A pak mi začali dávat podíl. Co jsem měl dělat? Vy jste tu nebyl. Váš otec umíral.
1. „Půjdeš k rychtáři. Zbytek rozhodne právo.“ → `kunes = popraven`
2. „Ještě jednou dáš znamení. Až ti řeknu.“ → KUNEŠ: Pán Bůh vám žehnej! `kunes = past`
3. „Jdi domů. Nic jsem neviděl.“ → `kunes = zabit_lapky` (lapkové se to dozví)

#### D-L6-busek (L6, vyjednávání)
*Nádvoří Pusté skály. Bušek Vlk v obnošené zbroji, kolem lapkové s luky.*

BUŠEK: Mladej Havraní přišel sám pod bílým hadrem. Buď jsi statečnej, nebo hloupej.
1. *Ukaž dopis Vartenberka.* → BUŠEK: *(čte pomalu, rty se mu hýbou)* „…a lapky pak pověsit pro pořádek.“ *(zmuchlá dopis)* Tak takhle, pane z Vartenberka.
   BUŠEK: Co chceš, Havraní?
   a) „Odejdi z kraje. Dnes.“ → Bušek odjede. `pusta_skala = vyjednano`
   b) „Slouž mi. Až přijde Kostka, budeš stát na mé straně.“ → BUŠEK: Rytíř bez pána je jen zloděj. Proč ne. `busek = spojenec`
2. „Vzdej se a budeš mít spravedlivej soud.“ → BUŠEK: *(směje se)* Spravedlivej soud? Ten jsem viděl. Na šibenici. → BOJ

#### D-L7-kaspar (L7)
*Věž, Kašpar krvácí, Vojtěch s mečem.*

KAŠPAR: Tvůj bratr kňučel jak štěně, víš to?
VOJTĚCH: Pane. Dovolte mi to.
1. „Je tvůj.“ → `kaspar = zabit_vojtechem`
2. „Ne. Bude viset podle práva. Ať ho vidí každej kupec na cestě.“ → VOJTĚCH: *(dlouho mlčí)* Jak poroučíte. `kaspar = popraven`
3. *(jen když jsi ušetřil Hanzlíka nebo Kuneše)* Mlč a nech Vojtěcha rozhodnout. → VOJTĚCH: *(spustí meč)* Mikuláš by nechtěl, abych byl jako on. `kaspar = popraven`, `vojtech_vernost +2`

---

### Milostivé léto

#### D-M1-sup (M1)
*Šenk, Vilém Sup u stolu, za ním biřici.*

SUP: Vilém Sup, královský biřic. Hledám zrádce z arcibiskupovy čeledi. A našel jsem vraha.
SUP: Hostinskej. Měl klíč od pokoje. Kdo jinej?
SUP: Hostinec je na vaší půdě, pane, soudit můžete vy. Dávám vám tři dny. Pak ho pověsím sám.

#### D-M4-prokop (M4)
*Krypta, louč, kněz se svícnem v ruce.*

PROKOP: Ani krok! Já… já se budu bránit!
1. „Jsem Jan z Havraní. Šimon nesl dopis mému otci.“ → PROKOP: *(svícen klesne)* Havraní… Bůh je milostivej.
PROKOP: V Praze odvedli arcibiskupovy lidi. Slyšel jsem křik ze sklepů. Mistra Jana pak našli ve Vltavě.
PROKOP: Utekl jsem. Šimon šel stejnou cestou. Řekl mi: kdyby se mi něco stalo, dones to Havranímu.
PROKOP: Tu noc jsem se vzbudil a nad Šimonem stál muž v plášti. Utekl jsem oknem. S brašnou.
PROKOP: Vezměte si ji. Ale slibte mi, že mě nevydáte. Prosím.
a) „Slibuju.“ → `ma_svitek`, `slib_prokopovi`
b) „Nic ti slibovat nebudu.“ → PROKOP: *(podá brašnu)* Tak ať vás Bůh soudí. `ma_svitek`

#### D-M6-soud (M6)
*Šenk plný lidí, Konrád u stolu.*

KONRÁD: Nůž? Takovej má každej kupec od Řezna po Vídeň.
ANEŽKA: Ale ne každej kupec chodí v noci po chodbě v botách s ostruhou. *(ukáže na jeho boty)*
KONRÁD: *(vstane, vytáhne nůž)* Zatracená holka! → BOJ

---

### Doubrava

#### D-D1-sebek (D1)
*Mlha, oběšenec na rumpálu.*

ŠEBEK: Mrtví z Doubravy. Já věděl, že si přijdou. Dvanáct let jsem to věděl.
1. „Proč by si pro něj chodili mrtví?“ → ŠEBEK: *(zbledne)* Na to se zeptejte Oty, pane. Nebo rychtáře. Já… já musím jít.

#### D-D5-bilek (D5)
*Stodola, noc. Bílek s džbánem, padací dvířka otevřená.*

BÍLEK: Pane… vy jste mě sledoval.
BÍLEK: Byl rok mrtvejch. Mor. V Doubravě umírali, už jich žilo jen pár. Pán z Vartenberka poslal vašeho otce, ať ves uzavře.
BÍLEK: Zatlouct dveře a zapálit, řek. Aby mor nepřelez k nám. Já, Šebek a kovář jsme drželi dveře.
BÍLEK: Někdo uvnitř ještě křičel. A váš otec… váš otec stál s pochodní a brečel. A pak ji hodil na střechu.
BÍLEK: Tomáš je můj synovec. Bylo mu třináct. Utek chodbou. Dvanáct let žil v lesích, a teď se vrátil.
BÍLEK: Šebek je další. Pak Ota. A pak vy, pane. Jste jeho syn.
1. „Proč jsi to nikomu neřekl?“ → BÍLEK: Protože si to zasloužíme. *(pláče)*
2. „Ukaž mi, kudy chodí.“ → BÍLEK: *(ukáže dolů)* Tudy. Ale nechoďte tam bez louče.

#### D-D7-tomas (D7)
*Studna, noc, oheň. Šebek svázaný. Tomáš se spálenou tváří, v ruce otcův meč.*

TOMÁŠ: Havraní. Přišels sám. Jako tvůj otec. Ten taky přišel sám a odešel s pochodní.
TOMÁŠ: Zapálil mi mámu. Sestru. Mě taky, ale já byl rychlejší.
1. „Otec udělal hroznou věc. A já ji nemůžu vzít zpátky.“ *(jen když `vi_o_otci`)* → TOMÁŠ: *(meč se zachvěje)* Tak co chceš?
   a) „Smír. Mše za vaše mrtvé. Doubrava bude znovu žít. Tvoje pole, tvůj dům. A kříž u cesty, ať každej ví, co se tu stalo.“
      → TOMÁŠ: *(dlouho)* …A Šebek to řekne nahlas. Všem. → *(Šebek kývne)* → Tomáš odhodí meč. `tomas = smir`
   b) „Vzdej se. Bude soud.“ → TOMÁŠ: Soud, kterej soudí pálení? Ten neexistuje. → BOJ
2. „Pusť ho, nebo tě zabiju.“ → TOMÁŠ: Zkus to. → BOJ

---

### Šenk a Kamenec

#### D-LE1-pivo (LE1)
*Šenk, večer, oheň v krbu. Eliška postaví před Jana pivo a sedne si naproti.*

ELIŠKA: Na účet pána. Pán je teď náš hrdina, tak ať taky něco má.
ELIŠKA: Viděl jsi Konrádovy oči, když jsem ukázala na ty boty? Myslela jsem, že se pomočí.
1. „Ty bys mohla vyslýchat i biskupa.“ → ELIŠKA: Biskupa ne. Ale pána z Havraní bych si vyslechla ráda. Celou noc, kdyby bylo potřeba. *(mrkne)* `eliska_naklonnost +1`
2. „Neměla bys sedět u pánova stolu.“ → ELIŠKA: *(vstane)* Jak poroučíte, pane. Pivo je stejně zadarmo.
3. „Kde máš matku?“ → ELIŠKA: Na hřbitově. Mor. Byla jsem malá. Táta od tý doby vaří za dva a já nalejvám za tři. `eliska_naklonnost +2`

#### D-LE3-rana (LE3)
*Kuchyně hostince po boji. Eliška čistí Janovi ránu na rameni pálenkou.*

ELIŠKA: Drž. Bude to pálit.
JAN: *(sykne)*
ELIŠKA: Pán, co přeseká tři chlapy, a kvůli kapce pálenky syčí jak kocour. *(nepouští jeho rameno)*
ELIŠKA: Proč jsi přijel? Mohl jsi poslat Vojtěcha.
1. „Kvůli tobě.“ → ELIŠKA: *(dlouho se dívá, nakloní se…)* → ONDŘEJ: *(ve dveřích)* Eliško! Voda do kotle! `eliska_naklonnost +2`
2. „Hostinec je na mojí půdě.“ → ELIŠKA: Aha. Na půdě. *(utáhne obvaz trochu víc, než je nutné)*

#### D-LK1-zaves (LK1)
*Komnata v Kamenci, noc. Za závěsem Jan, před závěsem Anežka v noční košili, na chodbě stráže.*

STRÁŽ: *(za dveřmi)* Paní? Slyšeli jsme kroky.
ANEŽKA: To jsem byla já. Modlím se. Chcete se modlit se mnou, Vaňku? Ne? Tak jděte spát.
ANEŽKA: *(odhrne závěs, tiše)* Ty jsi ten mladej Havraní, co ho chce můj muž sežrat. Vypadáš chutněji, než říkal.
1. „A ty jsi kdo? Kostkova služka?“ → ANEŽKA: Služka? *(směje se do dlaně)* Jsem paní tohohle vězení. Anežka. Hynkova žena. Ta třetí, protože první dvě to tu nepřežily.
2. „Proč jsi nekřičela?“ → ANEŽKA: Protože jsi první zajímavá věc, co sem za dva roky vlezla oknem.
ANEŽKA: Jdi. Oknem do příkopu, voda je mělká. A Havraní… u božích muk je dutej dub. Napiš mi.

#### D-LK3-bourka (LK3)
*Poustevna, bouřka, oheň. Anežka si suší vlasy, plášť jí sklouzl z ramen.*

ANEŽKA: Zmokla jsem až na kůži. To se stává, když se paní ztratí cestou na pouť.
ANEŽKA: Víš, co chci nejvíc na světě? Vidět moře. Kupci v hostinci o něm mluví. Prej nemá konec.
1. „Jednou ho uvidíš.“ → ANEŽKA: Jednou. Až odsud uteču. Tam, kde mě nikdo nezná. *(přisune se k ohni, k němu)* Ale dneska jsem tady. *(polibek, zatmívačka)* `anezka_noc`
2. „Měla by ses vrátit, než tě začnou hledat.“ → ANEŽKA: Hledají mě celej život, Havraní. Aspoň jednu noc ať nenajdou. *(polibek, zatmívačka)* `anezka_noc`

#### D-LK6-most (LK6)
*Most přes Bystřici, svítání, mlha, kupecké vozy. Anežka v prostém plášti.*

ANEŽKA: Kupci jedou přes hory na jih. Pak dál. Až tam, kde končí cesty.
ANEŽKA: Ty sem patříš, Havraní. Ke svý tvrzi, ke svým lidem. A já patřím někam, kde ještě nikdo nebyl.
1. *Poslední polibek.* → ANEŽKA: *(usměje se)* Ať se ti tady líbí. Mně se tu nikdy nelíbilo.
2. *Podat jí ruku.* → ANEŽKA: *(stiskne ji)* Jsi lepší, než si myslíš. Nekaž to.
3. *Dát jí měšec grošů.* → ANEŽKA: Platíš mi, abych odjela? *(vezme ho)* Chytrej Havraní. Na moři se bude hodit.
*Vozy zmizí v mlze. Jan stojí na mostě, dokud se mlha nezvedne.*

#### D-LE7-zadost (LE7)
*Studna ve Lhotě, poledne, půlka vsi kouká. Jan klečí.*

ELIŠKA: Pán klečí v blátě. Před šenkýřkou. Lidi si budou povídat.
ELIŠKA: Pán se žení se šenkýřkou? Ota to nepřežije.
JAN: Přežije.
ELIŠKA: *(dlouho se dívá, pak se rozesměje)* Tak jo. Ale klíče od spíže budu mít já.
*U oltáře:* ELIŠKA: Tak, pane z Havraní. Teď už mi neutečeš ani oknem.

---

## 13. Pro programátora


Tady je, co hra potřebuje, aby příběh šel hrát. Seřazeno tak, aby šlo začít hned a postavy přišly později.

### 1. Co jde udělat hned (bez postav)
Kapitola 1 se dá skoro celá odehrát s tím, co hra už umí:
- **Deník úkolů** (svitek): název úkolu, aktuální krok, splněné kroky.
- **Spouštěče** kroků:
  - `vstup_do_oblasti` (hráč dojde k bráně, ke hrobce, do Doubravy),
  - `predmet_v_inventari` (prsten, dopis, listina),
  - `predmet_polozen_v_oblasti` (2 louče u márů, džbán u Báry, dokumenty na stole),
  - `ohen_hori` (krb, louče na ochozech),
  - `cas` (noc/den, konkrétní datum),
  - `zasahy_lukem` (terč),
  - `stav_brany` (most nahoře/dole, mříž).
- **Příznaky (flagy):** slovník `jméno → hodnota` v uložené hře. Úkoly je čtou i zapisují.
- **Text na obrazovce:** dopisy a listiny se čtou jako svitek (D-H1-dopis).
- **Kalendář:** datum + roční období. Kapitola posune datum.
- **Náhradní řešení bez NPC:** vzkazy na dveřích, dopisy na stole, hlas z ochozu jako titulky.

### 2. Postavy a rozhovory
- Postava stojí na místě nebo chodí mezi 2–3 body podle denní doby (Ludmila: kuchyně ↔ spíž, Ota: brána ↔ strážnice).
- **Rozhovor:** okno ve stylu svitku, text postavy + 1–4 volby. Volba může nastavit příznak, dát/vzít předmět, posunout úkol.
- Formát dialogů je v `dialogy/` (MLUVČÍ: text, číslované volby, za šipkou příznaky).
- Nejdůležitější postavy podle pořadí: **Ota, Ludmila, Vítek, rychtář Bílek, Kostka, Martin, Bára, Eliška, Vojtěch**.
- Vítek jako **společník**: chodí za hráčem, nosí louč, umí otevřít branku zevnitř.

### 3. Souboj
- Luk už je. Přidat: nepřítel se blíží, střílí, padá. Zásahy, život hráče.
- Boj zblízka: sek, bod, kryt (stačí jednoduché, KCD-styl až později).
- Obležení: vlny nepřátel s žebříky ke zdem, oheň na bráně, hašení vodou ze sudů.
- Číslo `obrana_body` a tabulka spojenců z `hlavni_pribeh.md` určí počet útočníků.

### 4. Potřeby a zásoby (už rozpracované v PRIBEH.md)
Hlad, únava, špína; spíž, dřevník, sýpka počítané z položených předmětů. Peníze v groších a kopách.

### Nová místa (podle toho, kdy je příběh potřebuje)
| Priorita | Místo | Kap. |
|---|---|---|
| 1 | hrobka u kostelíka sv. Jiljí (ruina už je), šibenice u rozcestí | 1 |
| 2 | mlýn na Bystřici, městečko Lipník (stačí náměstí, fara, lékárna, notář, trh) | 2 |
| 2 | krypta pod kostelíkem, lapkovský tábor v Liščí soutěsce | 2 |
| 3 | ves Zálesí, uhlířské Spáleniště, poustevna | 2–3 |
| 3 | podzemní chodba Doubrava → Lhota → sklep tvrze | 2–5 |
| 4 | tvrz Kamenec (noční vloupání) | 3 |
| 4 | podzemí Pusté skály, odpadní šachta | 2–5 |

### Předměty příběhu
| ID | Předmět | Kde |
|---|---|---|
| `prsten_havran` | pečetní prsten, havran s ulomeným zobákem | otcova truhla |
| `dopis_otce` | dopis Janovi (čitelný text) | otcova truhla |
| `listina_mlyn` | darovací listina s pravou pečetí | otcova truhla |
| `upis_kostka` | padělaný dlužní úpis | od Kostky |
| `dzban_vino` | džbán s usazeninou oměje | kuchyně |
| `razidlo_lipove` | padělané razidlo (lipová kostka) | Martinova truhla |
| `sip_rudy` | lapkovský šíp s rudým pírkem | most |
| `hadr_bily` | znamení mlynáře | mlýn |
| `svitek_simon` | Šimonův svitek se jmény | brašna u Prokopa |
| `prsten_lipe` | prsten pana Ješka s lipovými listy | od Zbyňka |
| `dopis_vartenberka` | dopis Kostkovi o útoku | Kamenec |
| `kniha_vyplat` | platby „B. V.“ | Kamenec |
| `konik_ohoraly` | ohořelý dřevěný koník | oběšenec v Doubravě |
| `mec_otce` | otcův meč | Tomáš (D7) |
| `zvon` | zvon sv. Jiljí | zakopaný (U1) |
| `dopis_anezka` | dopisy z dutého dubu (víc kusů) | dutý dub u božích muk |
| `musle` | dopis s mořskou mušlí | kap. 6 |

### Volba hrdiny
Na začátku nové hry: **Mladý Jan (24)** / **Starší Jan (44)** → příznak `jan_vek` = `mlady` | `starsi`.
- `mlady`: aktivní linka `vedlejsi/laska.md`, model hrdiny mladší muž.
- `starsi`: aktivní linka `varianty/vdova.md`, model hrdiny starší muž (šedivé spánky, šrámy, pruský meč).
- Dialogy: když má řádek variantu `[starší]`, použije se pro staršího Jana.

### Seznam příznaků
**Hlavní:** `ch1_prijezd`, `ch1_bdeni`, `podezreni_jed`, `ch1_pohreb`, `ma_prsten`, `ma_dopis`, `ma_pravou_listinu`,
`ch1_tutorial`, `urok_havel`, `kostka_postoj`, `kostka_nenavist`, `vi_padelek`, `vi_jed`, `podezrely_martin`, `martin`,
`dluh`, `zalesi_pomoc`, `nabidka_lipe`, `priznani_martina`, `dopis_vartenberka`, `kniha_vyplat`, `vi_o_spiknuti`,
`urok_jiri`, `strana`, `obrana_body`, `kostka_zajat`, `obrana`, `ota_nalada`, `ves_nalada`.
**Lapkové:** `L_most`, `L_soutezka`, `hanzlik`, `kunes`, `L_past`, `L_sachta`, `pusta_skala`, `busek`, `kaspar`,
`vojtech_vernost`, `lapkove_konec`.
**Milostivé léto:** `M_mrtvy`, `M_dukazy`, `M_prokop_stopa`, `ma_svitek`, `prokop_nalezen`, `slib_prokopovi`, `prokop`,
`sup_nepritel`, `konrad`, `ondrej_ocisten`, `leto_konec`.
**Láska:** `eliska_naklonnost`, `eliska_zachranena`, `eliska_polibek`, `svatba`,
`anezka_potkana`, `anezka_dopisy`, `vi_plany_kamence`, `anezka_noc`, `anezka_zavrena`, `anezka_utek`, `anezka`, `jesek_nalada`, `laska`.
Polibky se ukazují, víc ne – noc řeší zatmívačka a střih na ráno.
**Doubrava:** `D_kovar`, `D_noc`, `vi_o_paleni`, `bara`, `D_poustevnik`, `vi_o_otci`, `D_rychtar`, `chodba`, `tomas`.
