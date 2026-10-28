# Rešerše: matice vztahů (vztahy.json) podle KCD2, reálné krajiny a výkonu tabletu

28. 10. 2026. Podklad pro hodnoty v `pravidla/svet/vztahy.json` (45 dvojic s pravidlem, 10 „nezavisle“).
Dnešní hodnoty: `pravidla_sveta.json` `pasma`, `svet/voda.json` `toky_tvar`, `svet/lokace.json` `ves.plot_od_domu_m` (16).
Nic v datech jsem neměnil, jsou to **návrhy**. Hodnoty označené *odhad* jsou z fotek KCD1/2, terénní a lesnické
praxe a z obecné znalosti, ne z měření s citací – před zapsáním do dat je ověřit snímkem ze hry (KCD2) nebo z Disku.

## Co se dá a nedá zjistit

- Warhorse nezveřejnil rozestupy ani hustoty (žádná přednáška GDC o vegetaci KCD2 nebyla nalezena). Ví se: KCD2 běží
  na silně upraveném CryEngine 5 a jeho vegetace je hustá procedurální, vázaná hlavně na CPU [S1, S2]. Tráva v CryEngine
  = „merged meshes“, slučované do **buněk 16 m**, které mají vlastní LOD [S3]; tráva se animuje jen do ~20 m
  (`e_MergedMeshesInstanceDist`), vzdálenost stromů řídí `e_ViewDistRatioVegetation` (KCD1, výchozí 500) [S4, S3].
  Nastavení „Vegetation Detail“ v KCD2 ubírá hustotu a dohled trávy a stojí až ~20 % výkonu; „Low“ vypne vzdálenou trávu
  a stíny středních trsů [S5].
- Warhorse stavěl vsi s historikem a podle fotek míst, včetně toho, kudy teče voda přes dvory a kde stojí kurníky [S6].
- Archeologie vsí 13.–15. stol. (Pfaffenschlag, Mstěnice, Konůvky, Bystřec): usedlosti často **desítky metrů od sebe,
  v Bystřci přes 40 m**; dům dvojdílný (síň + jizba), štítem do cesty (Mstěnice) [S7, S8]. Pfaffenschlag: krátká lesní
  lánová ves s prostornou návsí kolem potoka, 16 domů [S8].
- Středověké cesty: nezpevněné, na svahu se zařezávají do úvozů, rozpadají se do svazku souběžných kolejí; úvoz „široký
  na jeden vůz“ [S9]; rozvor kol vozů se blíží 1,4–1,5 m [S10, S11]; úvozy 1–3 m (dno 1 m, nahoře 3 m, hloubka 1 m),
  širší středověké úvozy až ~10 m s hloubkou 0,75–1 m [S12].
- Tablet: Meta pro mobilní GLES (Quest 1) radí < 100 kreslení statické geometrie, ~200 celkem, otevřený svět 50 %
  trojúhelníkového cíle [S13, S14]; Qualcomm: trojúhelník ≥ 4 px (LOD), `discard` ruší LRZ/early‑Z, alfa-test kreslit až po
  neprůhledném, alpha-to-coverage omezit [S15]. Godot: MultiMesh = tisíce instancí jedním kreslením, ale celá MultiMesh
  se kreslí, pokud její obal zasahuje do pohledu → dělit na buňky a dávat ruční AABB; v Compatibility se barva/custom
  data instance balí do 16 bitů; visibility range „Disabled“ fade je nejlevnější [S16, S17].
- Náš dosavadní rozpočet (docs/predani.md): ≤ 2,5 M trojúhelníků, ≤ 1500 kreslení, GPU < 700 MB; naměřeno louka
  731–843 kreslení / 1,1–1,5 M, za hostincem 1233 / 2,21 M; rostliny do `rozpocty.json planovac.rostliny_dosah_m` 115 m.

## Obecné zásady (platí pro všechny řádky)

1. **Pravidlo = dvě čísla, ne jedno.** Tvrdé minimum (fyzika, smysl – „kmen ne v cestě“) a **pásmo přechodu**, ve kterém
   hustota roste plynule (náhodný práh na instanci, ne ostrá hrana). Ostrá hranice odstupu je hlavní zdroj „umělé čáry“
   u cest a zdí. Navrhuji ke každému `*_m` přidat `*_prechod_m` (šířka náběhu hustoty 0 → 1).
2. **Rozptyl:** každá vzdálenost se v rozsevu bere jako minimum + náhodná přirážka (doporučeno 0–50 % hodnoty), nikdy ne
   konstanta – stejné rozestupy jsou nejviditelnější chyba. Shluky: stromy a keře Poissonovým diskem s **shlukovou maskou**
   (šum 20–60 m), kameny a rákos ve skupinách 3–12 kusů.
3. **Výkon neřídí počet instancí, ale počet MultiMesh (druh × buňka) a plocha alfa-testu na obrazovce.** Odstupy od cest a
   budov ubírají instance jen málo (pás 2 m kolem 1 km cesty = 0,4 % plochy 1 km²); velký vliv mají jen
   strom|strom (hustota lesa), cesta|bylina a budova|bylina v blízkém pásmu (tam je tráva na obrazovce největší) a
   budova|predmet / plot (jednotlivé uzly = jednotlivá kreslení).

## Tabulka dvojic

Sloupce: **Realita/KCD2** (čísla) · **Estetika** · **Výkon (tablet)** · **Návrh: hodnota → klíč (soubor)** · zdroj.
Klíče označené „nový“ v datech zatím nejsou.

### Terén × ostatní

| Dvojice | Realita / KCD2 | Estetika | Výkon | Návrh: hodnota → klíč | Zdroj |
|---|---|---|---|---|---|
| teren\|teren | Krajina středních Čech: svahy polí do ~15°, lesní svahy 20–35°, skály strmější. Úvozy 1–3 m hluboké jsou přirozené, rovné plochy delší než ~40 m mimo nivu a náves ne. | Žádné umělé roviny a kužely; hrany zaoblit (poloměr ≥ 5 m). | Bez vlivu na kreslení; hustota sítě terénu u cest a vody je trojúhelníkově nejdražší díl – jemná síť jen v pásmu (už `pas_jemny_m`). | Ponechat `meze_kroku`; `logika.svah_max_stupne` 35 ok. | S9, S12, *odhad* |
| teren\|voda | Malý potok v nivě: šířka 0,5–2 m, hloubka 0,1–0,4 m, břeh 0,2–0,6 m nad hladinou; vnější strana oblouku strmý holý břeh, vnitřní nános štěrku. | Asymetrie oblouků (strmý / plochý břeh) dělá potok živým; stejný profil po celé délce působí jako kanál. | Jemná síť u vody stojí trojúhelníky – `pas_jemny_m` 5 m je hranice, nezvětšovat. | `toky_tvar.breh_m` 0,3 ok; nový `toky_tvar.breh_vnejsi_m` 0,5 a `breh_vnitrni_m` 0,1 (podle křivosti osy). | S20, *odhad* |
| teren\|cesta | Historické vozové cesty se vyhýbají sklonu nad ~10–12 %, na svahu se zařezávají do úvozu (hloubka 1–3 m); pěšina snese 20–25 %. Příčně je cesta skoro rovná, ve vsi vyjetá do mírného žlabu. | Úvoz se svahy porostlými keři a kořeny je typický obraz KCD (cesty kolem Trosek/Ratají). Násep jen u brodu a mostu. | Bez vlivu. | Nový `pasma.cesta.<typ>.podelny_max`: vozova 0,12, ulice_vsi 0,10, pesina 0,25; `pricny_podil` ulice 0,12 ok; nový `uvoz_max_m` 2,5 (= mez kroku). | S9, S12, *odhad* |
| teren\|budova | Chalupy stály na mírně upravené plošině; na svahu podezdívka z kamene ze strany svahu 0,3–1 m, nikdy terasa přes 2 m. Dům štítem do cesty. | Viditelná kamenná podezdívka na svahu je žádoucí (ne terén zakrývající práh). | Bez vlivu. | `podlaha_teren_m` 0,5 ok; nový `plochy.json teren.stavba_max_sklon` doporučeno 0,15 (≈ 8,5°), podezdívka do 1,0 m. | S7, S8, *odhad* |
| teren\|plot | Proutěný plot: kůly zaražené 0,3–0,5 m, výplet od země (mezera 0–5 cm), na svahu kopíruje terén, laťky svisle (ne kolmo na svah). | Plot má po svahu „schodovat“ jen u laťkových polí, proutěný sleduje terén. | Bez vlivu. | Ponechat 2 cm (`_teren_pod_vraty`) – přesunout číslo do `pasma.plot.mezera_zem_m` 0,02 (nový, zákaz čísel v kódu). | *odhad* |
| teren\|strom | Kmen vyrůstá ze země svisle, na svahu je pata na horní straně zapuštěná, na dolní obnažené kořeny 0,1–0,3 m. Buk/smrk rostou do 35°, borovice a bříza i na skalách. | Lehký náklon kmenů (0–5°), na svahu kořenový náběh. Svislé „tužky“ vypadají uměle. | Bez vlivu. | `visi_m` 0,3 ok; nový `pasma.strom.naklon_max_st` 5; zahrabání pata 0,1–0,3 m na straně svahu. | *odhad* |
| teren\|ker | Keře na zemi; trnka, šípek, líska na mezích a v plášti lesa, i na svazích do 35°. | Keře zapustit 0,05–0,15 m (kořenový krček není vidět). | Bez vlivu. | `visi_m` ok; zapuštění keře 0,1 → nový `pasma.ker.zapusteni_m`. | *odhad* |
| teren\|bylina | Tráva roste na svazích do ~40–45°; nad tím mech, skála. Louky KCD nemají díry ani pruhy; hustota se mění plynule s vlhkostí a stínem. | Plynulé přechody hustoty (šum), žádné buňky viditelné shora (test `rastr`). | Tráva = největší podíl kreslení a overdraw. CryEngine (KCD) slučuje trávu do buněk 16 m a animuje jen do ~20 m. Doporučení tablet: plná hustota 0–25 m, 25–60 m řídnutí po jednotlivých trsech (hash), za 60 m jen barva terénu. | `skala.trava_max_sklon_st` 40 ok; nové `rozpocty.json louka.plna_m` 25, `louka.konec_m` 60, `louka.animace_m` 20. | S3, S4, S5 |
| teren\|kamen | Balvany a kameny jsou v zemi zapuštěné 20–40 % výšky, kolem nich vyšší tráva/kapradí. | Nikdy celý kámen na povrchu (vypadá položený). | Kameny jako MultiMesh, 3 velikosti × buňka. | Nový `pasma.kamen.zapusteni_podil` 0,3 (rozptyl 0,2–0,4); `visi_m` ok. | radce.md, *odhad* |
| teren\|predmet | Předměty na zemi, na svahu vyrovnané (sud na boku podložený). | — | Předměty jako samostatné uzly = kreslení; viz budova\|predmet. | Ponechat. | — |

### Voda × ostatní

| Dvojice | Realita / KCD2 | Estetika | Výkon | Návrh: hodnota → klíč | Zdroj |
|---|---|---|---|---|---|
| voda\|voda | Hladina jen klesá; peřeje a tůně se střídají – u kamenitých toků tůň po 2–4 šířkách koryta (silný rozptyl), v nížinných štěrkových tocích peřej po ~5–7 šířkách. | Střídání peřej / klidná hladina místo rovnoměrného spádu. | Bez vlivu. | `potok.min_spad` ok; nový `toky_tvar.perej_po_sirkach` [2, 7] (rozptyl). | S18, S19 |
| voda\|cesta | Brody na malých tocích jsou běžné (šířka brodu = šířka cesty + 1–2 m, dno zpevněné štěrkem/kameny), lávka 0,6–1 m široká pro pěší, most jen na větších tocích. Cesta podél potoka v nivě je přirozená (často 2–10 m od něj). | Brod se má poznat: rozšířené mělké koryto, vyjeté břehy, kamení. | Bez vlivu. | `krizeni_max` 3 a `tok_od_cesty_m` 1,0 ok; nový `cesty.json prechod.brod_sirka_navic_m` 1,5; `brod_hloubka_m` 0,12 ok. | S9, *odhad* |
| voda\|budova | Domy stály mimo záplavu, typicky 5–20 m od potoka; potok tekl návsí (Pfaffenschlag), kolem něj volný pás. Mlýn a stavidla jsou výjimka (díl). KCD: voda protéká i dvory (Duchek). | Mezi domem a vodou pruh drnu a pěšina k vodě. | Bez vlivu. | Nový `pasma.voda.budova_m` 4,0 (dnes jen `breh_m` 1,5 – dům 1,5 m od vody je na hranici nesmyslu); výjimky mlýn, hráz, lávka. | S6, S8, *odhad* |
| voda\|plot | Ploty k potoku dobíhají a končí na břehu (dobytek se tam napájí); přes malý potok občas přecházejí s mezerou nad hladinou. | Konec plotu na břehu je přirozený, nemusí končit 1,5 m od vody. | Bez vlivu. | `breh_m` → nový `pasma.voda.plot_m` 0,5. | *odhad* |
| voda\|strom | **Olše a vrby rostou přímo na břehové hraně**, kořeny ve vodě (0–1 m od hladiny); břehový porost 8–10 m od sebe v řadě podél toku; hlavaté vrby u vsí. Suchozemské stromy (buk, smrk, dub) od vody ≥ 2–3 m. KCD: vrby a olše lemují potoky. | Nepravidelná řada břehových stromů s mezerami, některé nakloněné nad vodu. | Břehová řada 1 strom / 8–10 m – zanedbatelné. | Rozdělit: suchozemské `breh_m` 1,5 → 2,0; nový `pasma.voda.brehove_od_m` 0,3 pro druhy se stanovištěm `breh` (olše, vrba); `brehove_rozestup_m` 8 (rozptyl 4–14). Dnešní `breh_m` pro olši je proti přírodě. | S21, druhy.json, *odhad* |
| voda\|ker | Vrbové keře, krušina, střemcha na břehu 0–2 m od vody. | Shluky u vody, ne souvislý val. | Malé. | Břehové keře od 0,3 m (`brehove_od_m`), ostatní `breh_m`. | *odhad* |
| voda\|bylina | Na břehu malého toku tráva a ostřice až k hladině kromě vymletého vnějšího oblouku; rákos a orobinec ve vodě do 0,5–1 m hloubky v rybnících a klidných úsecích, ve skupinách. U Bystřice vymleté břehy 2–3 m. | Pruh „holé hlíny“ stejné šířky po celém toku je umělý: hlína hlavně na vnějších obloucích, na rovných úsecích tráva k vodě. | Rákos v blízkém pásmu = alfa overdraw; skupiny ≤ 30 trsů. | `toky_tvar.breh_hlina_m` 0,9 → proměnné 0,2 (rovně) až 1,2 (vnější oblouk); `pasma.voda.breh_m` pro byliny 1,5 → 0,6 (vlhkomilné druhy smí do 0); nový `rakos_skupina` [5, 30]. | voda.json, *odhad* |
| voda\|kamen | Malý kamenitý potok ~1 kámen/m (dnes 0,9), v peřejích shluky, v tůních málo; kotevní balvany = největší zrna v korytu; část vyčnívá nad hladinu; na brehu zapuštěné. | Shluky v peřejích + jednotlivé kameny mezi nimi, ne rovnoměrný rozsev. | 0,9/m × ~250 m toku v dosahu 115 m ≈ 230 instancí = zanedbatelné, pokud MultiMesh. `kamen_lod_bias` 8 drží tvar (jehlany z LOD byly chybou). | `kameny_na_m` 0,9 ponechat jako průměr; v peřeji ×3, v tůni ×0,3; nový `toky_tvar.nad_hladinou_podil` 0,2. | S18, S19, voda.json |
| voda\|predmet | U vody: necky, vědra, lávka, kůly, vrš, loďka u rybníka, stavidlo. | Pár stop člověka u brodu a u vsi. | Malé. | Výjimky z `breh_m`: předměty se značkou `u_vody` (nová skupina v `pasma.skupiny`). | *odhad* |

### Cesta × ostatní

| Dvojice | Realita / KCD2 | Estetika | Výkon | Návrh: hodnota → klíč | Zdroj |
|---|---|---|---|---|---|
| cesta\|cesta | Křižovatky se rozšiřují (vozy se míjejí), na nich boží muka/kříž, strom (lípa). Cesty se na svahu rozpadají do souběžných kolejí. | Rozšíření a vyjeté „zkratky“ v rohu křižovatky. | Bez vlivu. | Nový `cesty.json krizovatka.rozsireni_m` 2. | S9 |
| cesta\|budova | Domy štítem do cesty; mezi štítem a cestou 2–6 m dvorku/předzahrádky; okap 0,6–1,2 m; před vchodem kamenný práh/schod. KCD ves: chalupy 3–8 m od ulice. | Různé odstupy domů od ulice (ne jedna uliční čára). | Bez vlivu. | `okap_m` 1,2, `schody_m` 1 ok; nový `pasma.budova.od_cesty_m` 2,0 (rozptyl +0–4 m). | S7, *odhad* |
| cesta\|plot | Ve vsi lemují ulici ploty zahrad a dvorů, často 0,5–1,5 m od vyjeté hlíny (pruh drnu s kopřivami). | Plot mírně „plave“ podél cesty, ne rovnoběžka. | Plot = mnoho dílů → slučovat do jedné sítě/MultiMesh na usedlost (jinak desítky kreslení). | Nový `pasma.cesta.<typ>.plot_m`: ulice 0,5, vozova 1,0, pesina 0,3. | *odhad* |
| cesta\|strom | Vozová cesta v lese: kmeny 1–3 m od koleje (průjezd vozu 3 m, větve ořezané); v otevřené krajině osamělé duby/lípy u cest 2–5 m. Stromořadí jsou novověká, ve 14. stol. ne. KCD: les často těsně u cesty, kořeny přes kraj. | Pravidelné řady podél cesty nepoužívat; les u cesty s keřovým lemem. | Bez vlivu na počet (malá plocha). | `kmen_m` vozova 6,0 → **3,0** (s rozptylem +0–3 m; v lese nový `kmen_les_m` 1,5), ulice 3,0 ok, pesina 3,0 → 1,0. Průjezdní výška 4 m bez větví – nový `pruchod_vyska_m` 4. | S9, *odhad* |
| cesta\|ker | Keře (líska, trnka, šípek, bez) lemují úvozy a okraje cest 1–2 m od koleje. | Lem keřů nepravidelný se shluky a mezerami. | Keře v blízkém pásmu jsou drahé (alfa); u cest jen 2. stupeň LOD dál než 30 m. | `ker_od_m` vozova 3,0 → 1,5; ulice 3,0 → 1,0 (u plotů); pesina 1,5 → 0,8. | *odhad* |
| cesta\|bylina | Vozová cesta: dvě koleje (rozvor ~1,4 m, kolej 0,2–0,35 m holá hlína), uprostřed travnatý pruh 0,4–0,7 m nízké trávy (jen na málo jezděných cestách), krajnice 0,3–0,5 m sešlapaná, pak plná tráva, vysoké byliny (kopřivy, lopuch) až od 1–2 m a v příkopu. Ves: náves a ulice bahnité, tráva jen u plotů. | Přechod hlína → nízký drn → trsy plynule (náhodný práh), ne čára. | Pás bez trávy na cestě ušetří fill; jinak malý vliv. Nízký drn v pásmu 0–1 m může být jen texturou terénu (bez instancí) – levné. | `drn_m` vozova 2,0 → 0,5; `trsy_od_m` 2,0 → 1,0 (+ nový `trsy_prechod_m` 1,0); vysoká bylina `vysoka_od_m` (nový) 1,5; nový `stred_trava` true jen pro vozova mimo ves, `rozvor_m` 1,4, `kolej_m` 0,3. Ulice: drn 1,0, trsy 1,5. Pěšina 1,0/1,0 ok → 0,3/0,6. | S10, S11, *odhad* |
| cesta\|kamen | Kamínky a štěrk v kolejích a na krajnici; větší kameny vyorané na krajnici 0,5–1,5 m; balvany ne na jízdním pásu. Na svahu úvozu vyčnívá skála. | Kamení shlukovat u příkopu a v úvozu. | Malé. | `kaminky_kraj_m` 0,6 ok; nový `balvan_od_m` 1,5 (dnes balvan spadá pod `ker_od_m`). | S9, *odhad* |
| cesta\|predmet | Na kraji: odstavený vůz, hromada dříví, kámen-milník, kříž; nikdy na jízdním pásu. | Předměty u křižovatek a vjezdů, ne rozsypané podél cesty. | Viz budova\|predmet. | Nový `pasma.cesta.<typ>.predmet_m` 0,5. | *odhad* |

### Budova × ostatní

| Dvojice | Realita / KCD2 | Estetika | Výkon | Návrh: hodnota → klíč | Zdroj |
|---|---|---|---|---|---|
| budova\|budova | Usedlost: dům + chlév + stodola kolem dvora; uvnitř usedlosti 3–8 m mezi stavbami (průjezd vozu ≥ 3 m), mezi usedlostmi desítky metrů (Bystřec > 40 m), kvůli požáru a zahradám. KCD vsi: sousední chalupy 8–20 m. | Shluk v usedlosti, velké mezery mezi usedlostmi; domy různě natočené (±10°). | Domy jsou samostatná kreslení (síť × materiál); slučovat díly jedné usedlosti. | `dvur_m` 2 → jen dvorek před vstupem; nové `pasma.budova.mezera_usedlost_m` 3,0 (min.) a `mezera_sousede_m` 10 (min., typicky 15–40). | S7, S8, *odhad* |
| budova\|plot | Plot ohrazuje dvůr a zahradu, navazuje na roh domu nebo chléva; zahrada za domem 10–30 m. Proutěný plot zahrady 0,8–1,2 m, dvora 1,2–1,8 m, kůly po 0,5–0,8 m. | Plot dotýkající se stavby je správně (navazuje), ne 0,5 m mezera. | Viz cesta\|plot – slučovat. | `ves.plot_od_domu_m` 16 ok (dosah); nový `pasma.plot.vyska_m` [0,8, 1,8], `kul_rozestup_m` 0,6 (rozptyl 0,5–0,8). | *odhad* |
| budova\|strom | Ovocné stromy v zahradě 3–8 m od domu, lípa/ořešák u stavení 4–10 m; koruny nad doškovou střechou se nenechávaly (vlhko, požár). KCD: stromy u chalup typicky 3–6 m. | Strom u domu je hezký, ale koruna nesmí procházet střechou. | Bez vlivu. | `kmen_od_zdi_m` 2,5 → 3,0 a nová kontrola `koruna_nad_strechou_podil` 0,3 (koruna nejvýš 30 % nad střechou). | *odhad* |
| budova\|ker | Bez černý u zdi, u hnojiště a záchodu (klasika vsi), 0,5–2 m od zdi; jinak kopřivy a lopuch u paty zdi. | Bez a kopřivy v koutě mezi stavbami, ne kolem celé zdi. | Malé. | `plevel_u_zdi_m` 0,6 ok; nový `ker_od_zdi_m` 0,8 jen pro bez/plevelné keře, ostatní keře `drn_m` 3. | *odhad* |
| budova\|bylina | Uvnitř a ve vstupech nic; dvůr ušlapaný (hlína), u zdí plevel. | Dvůr hliněný s trsy jen u okrajů a pod okapem kopřivy. | Ušlapaný dvůr = méně instancí trávy v nejbližším pásmu (dobrý pro výkon). | `pruchod_m` 1,6 ok (vrata 3 m → polovina šířky vrat + 0,5 m, ne pevný kruh); nový `pruchod_od_sirky` true. | misa_28_chyby, *odhad* |
| budova\|kamen | Kameny podezdívky a prahů jsou součástí stavby; volné balvany ne ve zdi; hromada sbíraných kamenů u stodoly/na mezi. | — | — | Ponechat (kolize obalů). | — |
| budova\|predmet | Dříví naskládané pod okapem u zdi (0–1,2 m), sudy a kádě u zdi a u vchodu, žebřík opřený, trakař, nářadí na kolíku, lavice u vchodu. KCD má všude tyto stopy. | Předměty v shlucích u vchodu a pod okapem, opřené o zeď (0–0,3 m). | **Nejvíc kreslení na předmět**: každý předmět jako uzel = 1+ kreslení. Opakující se předměty (polena, sudy, kameny) dávat do MultiMesh na buňku nebo slít do jedné sítě na usedlost; na tablet ≤ ~30–50 kreslení předmětů v pohledu. | Nový `pasma.budova.predmet_u_zdi_m` [0,0, 0,3] a `drevo_pod_okapem` true (pás `okap_m`). | S13, S14, *odhad* |

### Plot, strom, keř, kámen, předmět

| Dvojice | Realita / KCD2 | Estetika | Výkon | Návrh: hodnota → klíč | Zdroj |
|---|---|---|---|---|---|
| plot\|strom | Plot se stromu vyhýbá nebo strom slouží jako kůl; mezera 0,1–0,3 m od kůry. | Plot uhýbající kolem stromu působí přirozeně. | — | Nový `pasma.plot.od_kmene_m` 0,2 + poloměr kmene. | *odhad* |
| plot\|kamen | Balvan v linii plotu: plot končí/uhne, nebo balvan slouží jako patka. | — | — | Odstup = poloměr kamene + 0,1 m (nový `pasma.plot.od_kamene_m` 0,1). | *odhad* |
| plot\|predmet | Předměty se o plot opírají (vidle, hrábě, sudy vedle). | Opření je žádoucí. | — | Obaly se nesmí protínat, dotyk ano (tolerance 0,05 m). | *odhad* |
| strom\|strom | Hospodářský les 14. stol. byl často **pařezina/střední les** (výmladky ve shlucích po 2–5 kmenech, mezi nimi výstavky duby). Dospělá bučina ~250–450 kmenů/ha (průměrný rozestup 5–6 m), doubrava 150–300/ha (6–8 m), smrčina 400–700/ha (4–5 m), tyčovina 1500–3000/ha (2–2,5 m). Bučina po výsadbě ~6400/ha klesne probírkou na 22–33 %. Prales Žofín: zásoba 785–884 m³/ha, všechny věkové třídy. Kmeny v přírodě i 0,3–1 m od sebe (dvojáky, výmladky). | Poissonův disk s rozestupem podle velikosti + shluková maska; okraj lesa: plášť keřů 5–10 m a nižší stromy, ne stěna kmenů. Mýtiny a světliny. | **Hlavní pákou výkonu.** 300 kmenů/ha v kruhu 115 m (4,2 ha) ≈ 1250 stromů; plný model lze jen do ~40 m (≤ 150–250 stromů), dál impostor (už máme okluzor nitra lesa a atlas). Rozestup 5 m místo 4 m = −36 % instancí. | Nové `pasma.strom.rozestup_m` podle stáří: stary 6,0, stredni 4,0, mlady 2,0 (min., rozptyl +0–50 %), `shluk_m` 0,5 pro výmladky (pařezina, podíl 0,2), `les_kmenu_ha` cíl 300 (tablet strop 400). | S22, S23, S24, *odhad* |
| strom\|kamen | Stromy rostou vedle balvanů i z puklin skal (bříza, borovice); kořeny objímají kámen. | Strom u balvanu je pěkný detail. | — | Odstup = poloměr kmene + poloměr kamene + 0 (dotyk smí); kmen nikdy uvnitř obalu kamene. | *odhad* |
| strom\|predmet | Pod stromem lavice, špalek, nářadí opřené o kmen. | Opření smí. | — | Obaly se neprotínají, dotyk smí. | — |
| ker\|predmet | Keř neroste ze stolu/sudu; předmět u keře smí. | — | — | Předmět ne ve středu keře: odstup 0,5 × poloměr keře. | — |
| kamen\|predmet | Předmět smí ležet na kameni (kámen jako stolek, špalek). | — | — | Neprotínat; položení na horní plochu smí. | — |
| predmet\|predmet | Sudy ve skupinách 2–4 těsně (dotyk), polena ve stohu, nádobí na stole. | Shluky s dotykem, mírné natočení (±15°). | Shluky = kandidát na sloučení do jedné sítě. | Tolerance průniku 0,02 m; `polozeno_na` pro talíř/stůl. | *odhad* |

### Dvojice „nezavisle“ – kontrola, zda je to správně

| Dvojice | Hodnocení | Poznámka k výkonu |
|---|---|---|
| plot\|plot | ok | slučovat segmenty |
| plot\|ker | ok (keře u plotů typické – bez, líska) | — |
| plot\|bylina | ok; u paty plotu vyšší tráva a kopřivy (sekáč tam nedosáhl) – doporučeno ×1,5 hustoty v pásu 0,3 m | malý |
| strom\|ker | ok; ale pod hustou korunou (buk, smrk) podrost řídký, na okraji lesa plášť hustý | hustotu podrostu násobit (1 − zápoj) – ušetří instance uvnitř lesa |
| strom\|bylina | ok; pod bukem/smrkem téměř žádná tráva, pod dubem/břízou ano | totéž – největší úspora trávy v lese |
| ker\|ker | ok (skupiny) | — |
| ker\|bylina, ker\|kamen, bylina\|bylina, bylina\|kamen, kamen\|kamen | ok | — |
| bylina\|predmet | ok venku; pod velkým předmětem (vůz, stůl) tráva nižší | — |

## Výkon tabletu – souhrnné limity (doporučení)

| Položka | Návrh | Proč / zdroj |
|---|---|---|
| Kreslení celkem | ≤ 1000 typicky, strop 1500 (dnes 731–1233) | S13, S14: mobilní GLES 100–200 jsou cíle pro VR (2 oči, 72 Hz); tablet 30–60 fps unese víc, ale každé kreslení = CPU v Compatibility |
| MultiMesh | po druhu × buňce; buňka trávy 16–32 m (KCD 16 m), stromy 64–256 m; ruční AABB | S3, S16 |
| Tráva | plná do 25 m, řídnutí po trsech do 60 m, animace do 20 m; trs ≤ 30–60 troj.; pásy bez trávy (cesta, dvůr) jako textura terénu | S3, S4, S5, S15 |
| Stromy | plný model ≤ 150–250 v pohledu (do ~40 m), dál impostor; les cíl 300 kmenů/ha | výpočet výše |
| Kameny | MultiMesh 3 velikosti, korytu ~1/m; `kamen_lod_bias` 8 | voda.json |
| Alfa-test | kreslit po neprůhledném; nepoužívat alpha-to-coverage ani MSAA; LOD tak, aby trojúhelník ≥ 4 px | S15, CLAUDE.md |
| Visibility range | fade „Disabled“ + vlastní dither v shaderu (průhledný fade je drahý) | S17 |

## Zdroje

- S1 GameGPU benchmark KCD2: https://en.gamegpu.com/test-gpu/action-fps-tps/kingdom-come-deliverance-ii-itogovyj-godovoj-benchmark-2025
- S2 CheckFPS KCD2: https://checkfps.io/en/optimize-fps/kingdom-come-deliverance-2
- S3 CryEngine 5 docs, Vegetation 02 Grass (Merged Meshes), buňky 16 m; Lumberyard/AWS dotaz k `e_MergedMeshes*`: https://cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/24285889 , https://www.repost.aws/questions/QUndEqT6iPSvSLRQOw38r9Ow/1-6-problem-with-vegetation-applied-via-terrain-layers
- S4 Steam, KCD1 konzolové příkazy (`e_ViewDistRatioVegetation` 500, `e_MergedMeshesInstanceDist` 20): https://steamcommunity.com/app/379430/discussions/0/1642043267241229851 ; fórum KCD Graphics Tweaks: https://forum.kingdomcomerpg.com/t/graphics-tweaks/20955
- S5 PC Optimized Settings KCD2 (Vegetation Detail ~20 %): https://pcoptimizedsettings.com/ko/kingdom-come-deliverance-2-pc-%ec%b5%9c%ec%a0%81%ed%99%94-%ec%84%a4%ec%a0%95-%eb%b9%84%ea%b5%90/ ; https://tier1settings.com/best-kingdom-come-deliverance-2-settings-for-fps/
- S6 ZČU, Tomáš Duchek (Warhorse) – vsi, kurníky, voda přes dvory, historik: https://info.zcu.cz/Jiri-Frei-is-the-new-candidate-for-Dean-of-the-Faculty-of-Health-Care-Studies/clanek.jsp?id=8016
- S7 Usedlosti desítky m od sebe, Bystřec > 40 m, dvojdílný dům, štít do cesty (Mstěnice): https://is.slu.cz/el/fpf/leto2025/ARCHSTN039/4._Vesnice_vs._vsi__pudorysna_dispozice__zastavba__dum.pdf , https://www.archeologickyatlas.cz/cs/lokace/jedovnice_bk_ves_bystrec.pdf
- S8 Pfaffenschlag (lánová ves, náves s potokem, 16 domů): https://www.archeologickyatlas.cz/en/lokace/slavonice_jh_ves_pfaffenschlag.pdf ; Nekuda, Mstěnice 2 – Dům a dvůr (1997) k dohledání rozměrů
- S9 Viabundus – jak vypadaly středověké cesty (úvozy, svazky kolejí, „Geleis“): https://www.landesgeschichte.uni-goettingen.de/roads/viabundus/?p=528
- S10 Rozvor povozů 1,4–1,5 m: https://newtownpentacle.com/2010/12/6
- S11 Koleje San Pawl tat‑Targa, rozvor 138–149 cm: https://www.um.edu.mt/library/oar/bitstream/123456789/12044/1/OA%20The%20cart%20tracks%20at%20San%20Pawl%20tat-Targa%2c%20Naxxar.pdf
- S12 Úvozy: Coflein https://coflein.gov.uk/en/site/530186 ; Buckinghamshire HER (středověký úvoz ~10 m, 0,75–1 m): https://heritageportal.buckinghamshire.gov.uk/Monument/MBC6746
- S13 Meta, Asset streaming / open world (GLES < 100 statických, ~200 kreslení, 50 % trojúhelníků): https://developers.meta.com/horizon/documentation/unity/po-assetstreaming/
- S14 Meta, Quest best practices (50–100 kreslení, stav mezi kresleními): https://developers.meta.com/vr/blog/down-the-rabbit-hole-w-oculus-quest-developer-best-practices-the-store/
- S15 Qualcomm Adreno – Mobile best practices (≥ 4 px/troj., discard ruší LRZ, alfa po neprůhledném): https://docs.qualcomm.com/bundle/publicresource/80-78185-2/topics/mobile_best_practices.md
- S16 Godot MultiMesh (jedno kreslení, AABB, 16 bit v Compatibility): https://docs.godotengine.org/en/4.3/classes/class_multimesh.html
- S17 Godot Visibility ranges (HLOD, fade Disabled nejlevnější): https://docs.godotengine.org/es/4.4/tutorials/3d/visibility_ranges.html
- S18 Tůně po 2–4 šířkách koryta v balvanitých tocích (GSA Bulletin 102), kotevní balvany (ASCE 2000): https://ascelibrary.com/doi/10.1061/40517%282000%29340
- S19 Erikson & Turowski 2026, rozestup stupňů mezi pravidelností a náhodou: https://esurf.copernicus.org/articles/14/653/2026/
- S20 voda.json (fotky potoků v nivě, stav odhad) – vlastní data
- S21 Náhradní výsadba břehového porostu Orlice, rozestup 8–10 m: https://zakazky.eagri.cz/document_audit_332948/navrh-vysadby-bp-orlice-hradec-kralove-pdf ; podíly olše 30–70 %: https://www.pod.cz/projekty/flora_a_fauna/PDF/MapyKop/kopotok5.pdf
- S22 Vývoj počtu stromů bukového porostu (6400/ha → 22–33 %): https://jfs.agriculturejournals.cz/contents/jfs/1988/02.pdf
- S23 Žofínský prales, zásoba 785–884 m³/ha, věková struktura: https://ziva.avcr.cz/files/ziva/pdf/zamysleni-nad-clankem-o-zofinskem-pralese.pdf
- S24 GDC: Horizon Zero Dawn GPU procedural placement (hustotní mapy, deterministické, lokálně stabilní): https://www.guerrilla-games.com/read/gpu-based-procedural-placement-in-horizon-zero-dawn ; Ghost of Tsushima Procedural Grass: https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass

Nenalezeno (k doplnění, až bude přístup): přesné rozměry dvorů z Nekudy (Mstěnice 2), výška středověkých proutěných
plotů z archeologie, počet kmenů/ha z Žofína, čísla rozestupů přímo z KCD2 (nutné změřit ve hře / na snímcích Míši).
