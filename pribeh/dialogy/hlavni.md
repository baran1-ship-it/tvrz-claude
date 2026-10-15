# Dialogy – hlavní příběh

Formát: `MLUVČÍ: text`. Volby hráče jsou číslované, za šipkou je, co se stane a jaký příznak se uloží.
Mluví se lehce staročesky, ale tak, aby tomu rozuměl i kluk.

---

## D-H1-brana (H1.1)
*Soumrak, most zvednutý. Ota na ochozu s lukem.*

OTA: Stůj! Kdo jde k Havranu po setmění?
JAN: Jan. Oldřichův syn.
OTA: …Jan? Ten malej Jan, co utek ke Šternberkům na panoše? Ukaž se ve světle.
OTA `[starší]`: …Jan? Ten, co odešel s křižákama, když mi ještě nešedivěly vousy? Ukaž se ve světle.
1. *Zvedni louč k obličeji.* → OTA: Oči máš po mámě, chudák. *(`[starší]`: Pánbůh, ty jsi zestárnul. Já taky.)* Spouštím most. Zavři za sebou, pane. Lapkové se tu po tmě toulaj.
2. „Otevři, nebo tě nechám vyhnat jak psa, až budu uvnitř.“ → OTA: *(chvíli mlčí)* Po otci máš i jazyk. Spouštím. `ota_nalada -1`

---

## D-H1-bdeni (H1.2)
*Noc, síň, svíce u rakve. Ludmila přijde se šálem kolem ramen.*

LUDMILA: Pane… nespíte? Ani já ne. Musím vám něco říct, dokud to nepozřu.
LUDMILA: Pán neumřel na horečku. Měl modrý rty. Cukal sebou a hlava ho pálila, jako by mu někdo nalil do žil oheň.
LUDMILA: A ten den pil to víno. Co přišlo od pana Kostky na svatýho Václava.
1. „Kdo mu to víno nosil?“ → LUDMILA: Písař Martin. Jako vždycky. `podezreni_jed`
2. „Mlč o tom. Nikomu ani slovo.“ → LUDMILA: Jak poroučíte. Ale já vím, co jsem viděla. `podezreni_jed`

---

## D-H1-dopis (H1.4) – text dopisu
*Čte se, když hráč otevře dopis z truhly. Část je latinsky – Jan ji nepřečte.*

> Jene,
> jestli tohle čteš, nedožil jsem se, abych ti to řekl do očí. Nejsem dlužen pánům z Vartenberka ani groš.
> Cokoli ti přinesou s mou pečetí, je lež. Moje pečeť má havrana s ulomeným zobákem. Pamatuj si to.
> Čekej posla Šimona. Co nese, patří králi. *[Dva řádky latinsky.]*
> Je tu ještě Doubrava. Ota ví. Nechtěl jsem, abys to věděl, a teď nevím, jestli je horší, když to víš, nebo když ne.
> Odpusť mi, synu. Bůh mi neodpustí.
> Oldřich

---

## D-H1-havel (H1.6)
*Nádvoří, rychtář Bílek se dvěma měšci.*

BÍLEK: Svatej Havel, pane, úrok. Je tu osm kop. Víc… víc nemáme.
BÍLEK: Lidi nejezdí na trh. Na cestě loupí. Kubátovi vzali vůz i s koněm a Pánbůh ví, kde je čeledín.
1. „Zbytek vám odpouštím. Letos.“ → BÍLEK: Pán Bůh vám to oplať. Ves na to nezapomene. `urok_havel = odpusteno`
2. „Zbytek do Vánoc.“ → BÍLEK: Budem se snažit, pane. `urok_havel = odlozeno`
3. „Jestli to do neděle nebude, zabavím dobytek.“ → BÍLEK: *(sklopí oči)* Jak řeknete, pane. `urok_havel = vyhrozeno`, `ves_nalada -2`

---

## D-H2-kostka (H2.1)
*Brána. Kostka na koni, za ním dva zbrojnoši s vartenberskou korouhví.*

KOSTKA: Pan Jan z Havraní! Upřímnou soustrast. Váš otec byl… zvláštní člověk.
KOSTKA: Nerad otravuju v čas smutku. Ale tady je úpis. Šedesát kop. Do svatýho Tomáše.
KOSTKA: Jinak tvrz propadá pánu z Vartenberka. Tak to otec podepsal. Vidíte pečeť? Havran.
1. „Pojďte dál, promluvíme si u ohně.“ → Kostka vejde, prohlíží si tvrz jako by už byla jeho. `kostka_postoj = vpusten`
2. „Úpis mi ukažte přes mříž. Dál nepůjdete.“ → KOSTKA: Opatrnost po otci. Chválím. `kostka_postoj = mriz`
3. *Vystřel šíp do země před jeho koně.* → KOSTKA: *(kůň se plaší)* To si zapamatuju, mladej pane. `kostka_postoj = sip`, `kostka_nenavist +1`

---

## D-H2-martin (H2.4)
*Písárna. Na stole lipová kostka s vyřezaným havranem.*

MARTIN: Pane? To je… to jsem vyřezával pro zábavu. Zimní večery jsou dlouhý.
JAN: S celým zobákem. Otcův havran ho měl ulomený.
MARTIN: *(zbledne)* Měl jsem dluhy, pane. Kostka mě měl v hrsti. Říkal, že to víno je jen na spaní, aby pán…
MARTIN: Já nevěděl, že je to jed! Přísahám na svatou Ludmilu!
1. „Oběsím tě u rozcestí. Dnes.“ → `martin = popraven`. Ota mlčky vezme provaz.
2. „Půjdeš do strážnice. Až přijde čas, řekneš to před soudem.“ → `martin = vezen`
3. „Budeš Kostkovi psát dál. Ale to, co ti nadiktuju já.“ → MARTIN: Cokoli, pane. Cokoli! `martin = obracen`

---

## D-H3-posel (H3.2)
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

## D-H4-ota (H4.2)
*Komnata. Na stole svitek, dva prsteny.*

OTA: Tak co, pane. Král, nebo Lipští?
1. „Co bys udělal ty?“ → OTA: Já? Já držel dveře v Doubravě, protože mi to pán poručil. Od tý doby nevím, co je správně. Ale vím, že pan Ješek drží slovo. A král… král je daleko.
2. „Co by udělal otec?“ → OTA: Poslal by to králi. A kvůli tomu je teď pod zemí.
3. „Rozhodnu sám.“ → OTA: Tak rozhodněte. A rozhodněte se brzo. Na Kamenci už brousej meče.

---

## D-H5-vyjednavani (H5.2)
*Brána, ráno po ohních. Kostka pod bílým praporem, za ním vojsko.*

KOSTKA: Mladej Havraní! Krále zavřeli páni. Žádnej král tě nezachrání.
KOSTKA: Otevři bránu a můžeš odejít. S prstenem, s koněm, s tím klukem. Nikdo vám nezkřiví vlas.
1. „Pojď si pro ni.“ → Útok začíná.
2. „Tvůj pán zradil i jednotu. Pan Ješek to ví.“ *(jen když `strana = lipe`)* → KOSTKA: *(zaváhá)* Pan Ješek je daleko. → Útok začíná, ale třetí den přijedou Lipští.
3. „Kolik ti zaplatil za otcovu smrt, Kostko?“ *(jen když `priznani_martina`)* → Žoldnéři za Kostkou si začnou šeptat. −5 útočníků (část odejde).

---

## D-H6-konec (H6.2)
*Kostelík sv. Jiljí, srpen, cvrčci. Jan u otcova hrobu, Vítek opodál.*

VÍTEK: Pane? Co jste mu řek?
1. „Že jsem to udržel.“ *(obrana ubráněna)*
2. „Že jsem to ztratil. Ale ještě ne navždy.“ *(obrana padla)*
3. „Že mu Doubrava odpustila. Aspoň trochu.“ *(jen při `tomas = smir`)*
VÍTEK: A co teď?
JAN: Teď? Teď jsou žně, Vítku. A pak bude zas svatej Havel.
