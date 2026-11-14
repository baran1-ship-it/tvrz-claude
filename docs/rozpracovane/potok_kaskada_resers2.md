# Rešerše 2: strmý úsek řeky – kaskáda místo „schodů“ (14. 11. 2026)

Zadání: 10 m široká řeka typu horní Sázavy, úsek 70 m s převýšením 27 m (sklon S ≈ 0,39). Terasy přes celou šířku
Míša odmítl, chce vodu, která se klikatí ze strany na stranu mezi kameny.
Značení: **[L]** je hodnota z literatury, **[O]** je můj odhad odvozený z literatury a fotografií, NEOVĚŘENO měřením.

## 1. Jak strmé toky vypadají ve skutečnosti
- **Typ koryta podle sklonu** [L] (Montgomery & Buffington 1997): step-pool 0,03–0,065, kaskáda > 0,065. Sklon 0,39 je
  daleko za kaskádou, takže jde o **skalní (bedrock) úsek s vodopády**. Kaskády jsou „úzce sevřené svahy údolí“,
  jejich dno je „podélně i příčně neuspořádané“, proudění „přepadá a obtéká jednotlivé velké balvany“ a „malé tůně, které
  nepřehrazují celou šířku, leží méně než jednu šířku koryta od sebe“. Step-pool má tůně po 1–4 šířkách, kaskáda < 1.
  Největší balvany v kaskádě jsou velké zhruba jako hloubka vody při plném korytě.
- **Rozestupy stupňů jsou nepravidelné** [L]: Zimmermann & Church 2001 (koryto široké 8 m, sklon 5–10 %) uvádějí
  „velký rozptyl výšky stupňů, rozestupů i hloubky tůní“. Stupně vznikají tam, kde se zaklíní klíčový balvan (keystone),
  tedy v náhodných místech. Chin naměřila rozestupy 0,43–2,4 šířky koryta.
- **Šikmé a obloukové stupně** [L]: v pokusech ve žlabu vznikají šikmé a zakřivené stupně a prstencové shluky. Málo
  vyvinutý stupeň má kameny šikmo k proudu, dobře vyvinutý stojí kolmo. Stupně se tvoří hlavně tam, kde se koryto zužuje.
- **Poměr výšky stupně a rozestupu** [L] (Abrahams et al. 1995): (H/L)/S = 1–2, platí pro S > 0,05–0,07.
- **Čím strmější, tím užší** [L] (Finnegan et al. 2005): W ∝ Q^3/8 · S^−3/16.
- **České příklady** [L]: Mumlavský vodopád je široký i dlouhý asi 10 m, voda padá přes stupně žulových bloků a ve
  skále jsou obří hrnce o průměru až 6 m a hloubce až 3 m. Bílá Opava protéká hlubokým údolím kaňonovitého rázu, prudký
  tok se vine mezi balvany přes peřeje, kaskády a vodopád vysoký asi 8 m, se skalními výchozy a hlubokými tůněmi
  (horní část rula, níže břidlice a křemence). U Černého potoka (Jizerské hory, vodopád 7 m) voda teče dvěma koryty
  kolem velkého balvanu zaklíněného mezi skalními stěnami. U Jedlových vodopádů padá voda strmě a tříští se o velké balvany.

## 2. Jak by vypadala 10 m řeka na sklonu 39 %
Řeka by se nerozdělila na rameno vedle ramene, protože soutěska je sevřená. Vznikla by **soutěska ze skalních plotn
a balvanů**, místně by voda obtékala velký balvan dvěma proudy. Hlavní proud při běžném průtoku přebíhá od jednoho
břehu ke druhému na každém stupni a tůně pod skoky jsou střídavě vlevo a vpravo. To je Míšova klikatá čára.

Doporučené hodnoty do pravidel:

| Parametr | Hodnota | Zdroj |
|---|---|---|
| šířka koryta v kaskádě | 0,4–0,6 × běžná šířka, tedy 4–6 m | [L] Finnegan: (0,39/0,002)^−3/16 ≈ 0,37; spodní hranici zvedá [O] |
| smáčená šířka při běžném průtoku | 0,5–0,7 × šířka kaskády, tedy 2–4 m | [O] |
| klikatost proudnice uvnitř koryta | 1,15–1,3 | [O]; v půdorysu je celá soutěska téměř rovná (1,0–1,1) [L] |
| vlna klikatění | 2 rozestupy stupňů (strana se střídá na každém stupni) | [O] z [L] tůně střídavě |
| výchylka proudnice od osy | ±0,25–0,35 × šířka kaskády | [O] |
| rozestup stupňů L | průměr 0,8–1,5 × šířka kaskády (4–7 m), variační koeficient 0,4–0,5 | [L] Chin, M&B, Z&C |
| výška stupně H | 0,5–3 m, log-normální, medián 1,5 m; 1 hlavní skok 4–6 m | [L] Abrahams, ČR 7–12 m |
| (H/L)/S | 1–2 (hloubka tůně se počítá do H) | [L] |
| natočení stupně | 15–40° od kolmice, střídavě vlevo a vpravo | [O] z [L] šikmé stupně |
| tůň pod stupněm | délka 1–2 H, hloubka 0,3–0,6 H, posunutá k té straně, kam míří přepad | [O] |
| klíčové balvany D | 0,6–1,5 m; W/D 3–6 | [L] Zimmermann 2010 |
| plocha, kterou zabírají balvany vyčnívající z vody | 30–50 % koryta | [O] |
| ostatní balvany | 0,2–0,6 m, shluky za klíčovými | [O] |
| skalní plotny se žlaby | 20–40 % délky úseku, hrnce o průměru 1–3 m | [L] Mumlava, [O] |
| bílá voda | 50–70 % délky: hrana každého stupně a 1–2 H pod ní; v tůních tmavá klidná voda | [O] |

## 3. Postup ze hry a herní grafiky
- **Nejdřív terén a kameny, potom voda.** Unity Forest Stream: vymodelovat terén, položit plochy toku, potom vodopády a
  kameny. Kameny lámou tvar toku a mění vzor pěny. Použít dvě velikosti, balvany a menší kameny. Plocha vodopádu sahá
  od jednoho stupně k dalšímu a má průhledné okraje, aby navázala na tok.
- **Spline padající po svahu** (Simon Schreibt, Houdini do Unrealu): spline se nechá spadnout na terén, body se posunou
  ve směru spádu a skript hlídá, aby žádný bod nebyl výš než předchozí. Svahové úseky se obarví. Ze sítě řeky se odvodí
  koryto a terén pod ní, mapa toku se peče z geometrie a překážek.
- **Pěna** [L]: podle vzdálenosti od překážky se uloží do vertex color a rozruší šumem. Pěna na kaskádě je zvláštní
  textura, posouvá se rychleji než voda a objevuje se jen na svazích. Vodopád má hustší pěnu nahoře a dole.
  Na střetu s geometrií se použije logika pobřeží. Na středy kaskád a na místa nárazu se dají částice.
- **Tablet:** pro odraz na šikmé vodě nelze použít planární odraz (Far Cry 5). Pěnu udělat ve vertex color a textuře,
  ne simulací. O Witcher 3, RDR2, KCD2 a Ghost of Tsushima jsem nenašel veřejný rozbor, jak dělají kaskády.

**Návrh pro naše pořadí stavby:** záznam „kaskáda“ obsahuje sevřenou soutěsku, plotny a klíčové balvany, které se
umístí na střídající se šikmé stupně. Teprve potom se mezi nimi vede proudnice vody, nejnižší cestou mezi balvany, střídavě
k jednomu a druhému břehu. Pěnu a částice určí vzdálenost od balvanů a hrany stupňů.

## Zdroje
- Montgomery & Buffington 1997: https://fs.usda.gov/rm/boise/publications/watershed/rmrs_1997_montomeryr001.pdf
- Finnegan et al. 2005: https://earthweb.ess.washington.edu/roe/Web/GerardWeb/Publications_files/FinneganEtal_Width_Geology05.pdf
- Chin, periodicita: https://ajsonline.org/article/61660.pdf ; Chin 1989/1999 přehled: https://typeset.io/pdf/characteristics-of-step-pool-morphology-in-the-mountain-5adtl4fhnx.pdf
- Zimmermann & Church 2001 (abstrakt): https://data.zhenzhi.com/details/1/889439483
- Church & Zimmermann 2007 / Zimmermann et al. 2010, jamming: https://zendy.io/title/10.1029/2009jf001365 , https://circle.ubc.ca/handle/2429/7016
- Abrahams et al. 1995: https://earthref.org/ERR/68349 ; Wilcox & Wohl 2006: https://www.umt.edu/wilcox/documents/publications/wilcox_wohl-wrr2006.pdf
- Comiti et al. 2007, Rio Cordon: https://www.umt.edu/wilcox/documents/publications/comiti-etal2007-jhydrol.pdf
- Šikmé stupně ve žlabu: https://www.interpraevent.at/reference/media/1636/download/2004_1_III-343.pdf?v=1
- eSurf 2026, náhodné a pravidelné rozestupy: https://esurf.copernicus.org/articles/14/653/2026/
- Mumlava: https://lokality.geology.cz/3126?la=en
- Bílá Opava: https://cz.hikingtrails.eu/praded-a-udoli-bile-opavy/ , https://severnimorava.travel/en/zazitky/the-bila-opava-valley/
- Černý potok, Jedlová: https://www.slevomat.cz/vylety/9452-vodopad-cerneho-potoka , https://www.turistika.cz/mista/vodopady-jedlove/detail
- Simon Schreibt, řeka: https://80.lv/articles/006sdf-river-simulation-with-simonschreibt/
- Unity Forest Stream: https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/Shader-Graph-Sample-Production-Ready-Tutorial.html
- Pěna vodopádu (UE): https://threadreaderapp.com/thread/1574797115477434375
- Far Cry 5, šikmá voda: https://www.advances.realtimerendering.com/s2018/The%20Challenges%20of%20Rendering%20an%20Open%20World%20in%20Far%20Cry%205%20(With%20Notes).pdf
