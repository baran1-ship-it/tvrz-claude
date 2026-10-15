# Hlavní příběh: Havraní pečeť

**V kostce:** Jan přijede na pohřeb otce. Zjistí, že otec byl otráven, že dluh, kterým ho soused vydírá,
je padělaný, a že otec byl tajně králův muž, který chtěl varovat krále před spiknutím pánů.
Na jaře si Jan musí vybrat stranu. V květnu 1394 páni zajmou krále a soused z Kamence
využije zmatku a oblehne Havran. To, jak Jan zvládl vedlejší linky, rozhodne, kolik má
při obležení spojenců. V srpnu je král volný a každý dostane, co si zasloužil.

Zápis kroků: **ID – úkol** · *kde* · **Spouštěč:** co hra kontroluje · **Příznak:** co si uloží.
Kroky s (NPC), (ROZHOVOR), (BOJ) potřebují věci, které hra zatím neumí – viz `pro_programatora.md`.

---

## Kapitola 1 – Dědictví (14.–16. 10. 1393)
*Učí ovládání: chůze, brána, oheň, jídlo, spánek, truhly, luk.*

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

## Kapitola 2 – Dluh (listopad – 21. 12. 1393)
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

## Kapitola 3 – Zima (prosinec 1393 – únor 1394)
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

## Kapitola 4 – Volba (březen – 24. 4. 1394)

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

## Kapitola 5 – Obležení (květen 1394)

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

### Spojenci z vedlejších linek
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

## Kapitola 6 – Odkaz (srpen 1394)
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
