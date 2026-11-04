# Detaily gotického hradu kolem 1393: pravidla pro model Puchartu

Kontext: Puchart (Pustý zámek, Zighart) u Potštátu. Jde o dvojhrad, přední a zadní hrad stojí asi 100 m od sebe.
První zmínka je z roku 1318, zánik se klade asi do roku 1394 (obsazení Potštátu markrabětem Prokopem).
Model stojí na drobě (lomové zdivo z břidlice a droby), maltě a částečné omítce.

Rozsahy níže jsou typické hodnoty pro české a moravské hrady z let asi 1300–1420.
Vycházejí z běžně uváděných hodnot v kastelologii (Durdík, *Ilustrovaná encyklopedie českých hradů*;
Durdík a Bolina, *Středověké hrady v Čechách a na Moravě*), ze zaměřených příkladů a z údajů památkové péče.
**Stav čísel: všechny rozsahy v „Pravidlo:“ jsou NEOVERENO** (typické literární rozsahy, ne zaměření konkrétního objektu),
kromě výslovně citovaných (Helfštýn zeď 2 m; prkna dveří 25–32 mm; valouny až 15. stol.). Do JSON zapisovat se stavem NEOVERENO a zdrojem.
**Pro Puchart platí (CLAUDE.md): ostění, nároží a stupně z droby nebo místního kamene, ne z pískovce.** Pískovec v textu znamená jen srovnávací příklady jinde.

Obecné zdroje:
- https://www.hrady.cz/hrad-puchart-potstat-sudetsky-zamek-zighart-pusty-zamek
- https://www.hrady.cz/hrad-puchart-potstat-sudetsky-zamek-zighart-pusty-zamek/galerieo/4218
- https://cs.wikipedia.org/wiki/Cimbuří (vývoj stínek: od konce 14. stol. se proluky zužují, stínky rozšiřují)

---

## 1. Portál brány (průjezd) a branky / palácové dveře

Jak to vypadalo:
- **Tvar oblouku.** Kolem 1390 převažuje u vjezdu **lomený oblouk**. Tvoří ho buď kamenné **klínky**, nebo prostý lomený
  záklenek z plochých kamenů (na drobovém hradě častější). Půlkruh se drží u starších a skromnějších staveb.
  Branky a vnitřní dveře mají často **lomený záklenek**, jinak přímé nadpraží na **konzolkách** (takzvaný
  „sedlový“ nebo „segmentový“ záklenek). Půlkruh je u nich spíš konzervativní prvek.
- **Ostění.** Kamenné ostění brány sedí **v líci zdi**, nevystupuje. Jinde (Zvíkov, Křivoklát) se na portály používal pískovec.
  Na Puchartu budou ostění z **vybraných větších drobových bloků**, hrubě opracovaných, s menším sražením. Hrana je **sražená** (okosená). Bohatší portály (Zvíkov, Křivoklát) mají **výžlabek**.
- **Polodrážka (dorazová drážka).** Je na vnitřní straně ostění, tj. směrem do průjezdu. Vrata **dosedají zevnitř** na ostění
  a otevírají se **dovnitř**. Za ostěním se průjezd **rozšiřuje** do **špalety**, kam se otevřené křídlo sklopí.
  Často je tam i **kapsa pro závorový trám** (závora), hluboká 1,5–3 m do zdi, a na druhé straně protilehlá jamka.
- **Závěs.** **Hák (čep) zazděný nebo zaolovený do ostění či spáry zdiva.** Na něj se navlékne oko **pásového závěsu**.
  Velká vrata mohla mít i **spodní kuželový čep** v kamenné kapsě (kamenná pánev) a horní čep v kapse nadpraží.
- **Průjezd za portálem.** Brána je buď prostý průjezd zdí (u Puchartu nejpravděpodobnější), nebo průjezd
  přízemím **branské věže**. Průjezd je zaklenutý **valenou klenbou** (půlkruh nebo mírně lomená) z lomového kamene
  na bednění, často s otisky prken. Klenba je **o 0,3–0,6 m vyšší a 0,3–0,6 m širší** než otvor portálu.
  Na vnější straně bývá **padací most** s nikou pro zdvižené mostovky nebo hřeble (padací mříž je spíš u větších hradů).
- **Práh.** Kamenný blok nebo práh na úrovni vozovky. U vjezdu není schod, nanejvýš 0,05–0,15 m.
  Branka mívá 1 stupeň 0,15–0,25 m. Palácové dveře nad terénem mají 1–3 stupně.

Pravidlo: vjezd_sirka = 2.6–3.4 m (typ. 3.0); vjezd_vyska_do_vrcholu = 3.4–4.2 m (typ. 3.8); patka_oblouku_vyska = 2.4–2.8 m
Pravidlo: obluk = "lomeny" (pomer vysky vzepeti k rozpeti 0.5–0.6); klinku_pocet = 15–25 (lich., svorník uprostřed); klinek_hloubka = 0.35–0.50 m, sirka_lice = 0.20–0.35 m
Pravidlo: osteni_kamen_tloustka_lice = 0.30–0.45 m (do hloubky zdi 0.4–0.6 m); osteni_lic = "v lici zdi" (předsazení 0 m)
Pravidlo: srazeni_hrany = 0.06–0.12 m (45°); vyzlabek_polomer = 0.05–0.08 m (jen bohatší portál)
Pravidlo: polodrazka_hloubka = 0.08–0.15 m, sirka = 0.10–0.15 m, na vnitřní straně; kridlo_otevira = "dovnitř"
Pravidlo: spaleta_rozsireni = 0.3–0.6 m na každou stranu; spaleta_hloubka >= sirka_kridla (1.3–1.7 m pro 2křídlá vrata)
Pravidlo: zavora_kapsa = 0.20×0.20–0.25×0.25 m, hloubka 1.5–3.0 m; vyska_osy_zavory = 1.0–1.3 m
Pravidlo: zavesy_na_kridlo = 2–3 (vrata), 2 (branka); hak_prumer_trnu = 0.025–0.04 m
Pravidlo: pruchod_klenba = "valena" (pulkruh/mírně lomená), delka_pruchodu = tl. zdi 1.8–2.5 m (věž 5–8 m)
Pravidlo: branka_sirka = 0.8–1.2 m; branka_vyska = 1.8–2.3 m; palacove_dvere = 0.9–1.3 × 1.9–2.4 m
Pravidlo: prah_vjezd = 0–0.15 m; prah_branka = 0.15–0.25 m; schod_vyska = 0.17–0.25 m

Zdroje:
- https://commons.wikimedia.org/w/index.php?search=Rab%C3%AD+castle+gate&title=Special:MediaSearch&type=image
- https://commons.wikimedia.org/w/index.php?search=Zv%C3%ADkov+gate+portal&title=Special:MediaSearch&type=image
- https://commons.wikimedia.org/w/index.php?search=Helf%C5%A1t%C3%BDn+br%C3%A1na&title=Special:MediaSearch&type=image
- https://www.buildingconservation.com/articles/early-timber-doors/early-timber-doors.htm (háky ve kamenné polodrážce)
- https://digilib.phil.muni.cz/_flysystem/fedora/pdf/140837.pdf (Rabí, brány, AH 2009)

## 2. Gotická okna paláce (1390s)

Jak to vypadala:
- **Okno.** Kamenné ostění (jinde pískovec, na Puchartu droba nebo hrubé ostění s omítnutou špaletou) s **okosením 45°** po obvodu. Typy:
  (a) **obdélné okno, často dělené kamenným křížem nebo sloupkem** (kolem 1400 nastupuje);
  (b) **dvojice lomených nebo trojlistých záklenků** (vrcholná gotika, bohatší sídla);
  (c) úzké **obdélné okénko nebo štěrbina** (sklepy, schodiště, nižší podlaží).
  Na skromném moravském hradě je realistické (a) nebo (b) v hlavním sále a (c) jinde.
- **Uvnitř.** Okno sedí v **nice** se špaletami **rozevřenými dovnitř**. Nika je zaklenutá segmentem nebo lomeným záklenkem.
  V sále bývá **sedátková nika**: podél boků jsou kamenné lavice (Valdek, Křivoklát, Zvíkov).
  Parapet niky se snižuje k podlaze, sedátka leží na úrovni 0,4–0,5 m.
- **Zasklení.** Sklo v olověných mřížkách bylo kolem 1390 drahé. Měl ho hlavní sál nebo kaple, jinak se používaly
  **dřevěné okenice** (vnitřní, na pásových závěsech, zavírané na závoru), **blána, napuštěné plátno, pergamen**
  v dřevěném rámu. Ostění má **polodrážku nebo otvory pro mříž** (železné pruty v přízemí).

Pravidlo: okno_svetla_sirka = 0.45–0.70 m (jedno pole), kriz/sloupek: celkem 0.9–1.3 m; svetla_vyska = 1.0–1.8 m
Pravidlo: osteni_profil = "okoseni 45°", sirka_okoseni = 0.04–0.08 m; osteni_sirka_kamene = 0.18–0.28 m
Pravidlo: parapet_vnejsi_vyska_nad_podlahou = 0.8–1.0 m (okno s nikou), sedatka = 0.40–0.50 m vys., 0.35–0.45 m hloub.
Pravidlo: nika_rozevreni = 10–20° na stranu (špaleta), nika_sirka_uvnitr = 1.2–2.0 m, hloubka = tl. zdi minus 0.3 m
Pravidlo: nika_zaklenek = "segment" nebo "lomeny", vrchol 2.2–2.8 m nad podlahou
Pravidlo: mriz_pruty = 0.02–0.03 m čtyřhran, rozteč 0.12–0.18 m (přízemí); okenice_tl = 0.03–0.04 m
Pravidlo: zaskleni_1393 = {sal: "olověné sklo/terčíky Ø 0.08–0.12 m", ostatni: "okenice + blána/plátno"}

Zdroje:
- https://www.pruzkumypamatek.cz/pdfs/prp/2000/02/04.pdf (palác, okenní niky se sedátky, okosené ostění)
- https://www.pruzkumypamatek.cz/pdfs/prp/1996/01/15.pdf (okosené ostění, nika se segmentovým záklenkem)
- https://commons.wikimedia.org/w/index.php?search=K%C5%99ivokl%C3%A1t+window+niche&title=Special:MediaSearch&type=image
- https://commons.wikimedia.org/w/index.php?search=Zv%C3%ADkov+palace+window&title=Special:MediaSearch&type=image

## 3. Konstrukce křídla vrat

- **Dvě vrstvy prken.** Vnější prkna jsou **svislá** (lépe odvádí vodu), vnitřní **vodorovná nebo šikmá**.
  Vrstvy spojují **kované hřeby** procházející skrz, na rubu **zahnuté (roznýtované)**. Prkna mají tupý sraz
  nebo pero a drážku (doloženo už od 14. stol.).
- **Pásové závěsy.** Ploché kované pásy na vnitřní straně, přes celou nebo 2/3 šířky křídla, s okem na hák.
  Pásy současně stahují prkna.
- **Horní tvar.** Kopíruje lomený oblouk. Prkna jsou šikmo seříznutá do oblouku, křídlo zapadá do polodrážky celým obvodem.
  Dvoukřídlá vrata mají **branku (průlez) v jednom křídle**.
- **Povrch.** Dub nebo jedle, přírodní, lze **pobít plechem** nebo hřebovými hlavami v rastru.

Pravidlo: vrstvy = 2; vnejsi = "svisle", vnitrni = "vodorovne|diagonalne"; tl_prkna = 0.025–0.035 m (celkem 0.05–0.08 m)
Pravidlo: sirka_prkna = 0.20–0.40 m (nestejné), vrata 2křídlá po 1.3–1.7 m
Pravidlo: hreby_rozteč = 0.10–0.20 m po řadách, hlava Ø 0.015–0.03 m; konce na rubu zahnuté
Pravidlo: zaves_pas_sirka = 0.04–0.07 m, tl = 0.006–0.010 m, delka = 0.7–1.0 × sirka_kridla; pocet = 2–3
Pravidlo: prulez_v_kridle = 0.6–0.8 × 1.5–1.8 m, prah prulezu 0.25–0.40 m nad zemí
Pravidlo: horni_hrana = "kopiruje lomeny oblouk", vule v polodrazce 0.01–0.02 m

Zdroje:
- https://www.buildingconservation.com/articles/early-timber-doors/early-timber-doors.htm (2 vrstvy, 25–32 mm, háky ve kameni)
- https://www.iforgeiron.com/topic/34909-studs-in-medieval-doors/
- https://commons.wikimedia.org/w/index.php?search=medieval+door+strap+hinges+gothic&title=Special:MediaSearch&type=image

## 4. Dřevěná schodiště (vnitřní, přízední)

- **Konstrukce.** Do 15. stol. převládají **masivní dubové stupně (špalíky)**. Jsou to trojboké nebo obdélné hranoly,
  připevněné na dvě **schodnice** nebo uložené na šikmém trámu. Alternativou jsou **žebříková schodiště**
  (strmá, s deskami zapuštěnými do schodnic). Spirála z dubových špalků je doložena hlavně v západní Evropě.
- **Přízední schodiště.** Jde o **jednu schodnici ke zdi**, vázanou do **kapes ve zdi** (horní a dolní trám zapuštěný 0,2–0,4 m).
  Alternativně jsou **stupně konzolovitě vetknuté** do zdi (u kamenných stupňů) a dřevěné stupně leží na
  **zděných ozubech nebo trámcích v kapsách**. Druhá schodnice je volná, na sloupku.
  Venkovní přístup do patra paláce vede často přes **dřevěnou pavlač a schodiště na nádvoří**.
- **Zábradlí.** Doloženo málo. Realisticky jde o **jednoduché madlo**: kulatina nebo hranol na 2–3 sloupcích,
  bez výplně, nebo o lano u zdi. U zdi zábradlí chybí.

Pravidlo: sirka_ramene = 0.8–1.2 m (vnitřní), 1.0–1.5 m (venkovní k paláci); zebrikove = 0.6–0.8 m
Pravidlo: vyska_stupne = 0.20–0.25 m (strmé až 0.30); hloubka_stupne = 0.22–0.30 m; sklon = 38–50°
Pravidlo: spalek_prurez = 0.20–0.25 × 0.25–0.30 m (trojboký/obdélný); deskovy_stupen_tl = 0.05–0.07 m
Pravidlo: schodnice_prurez = 0.08–0.12 × 0.25–0.35 m; kapsa_ve_zdi = 0.25–0.35 m hloub.
Pravidlo: podesta_min = 1.0 × sirka_ramene (typ. 1.0–1.4 m čtverec); podchodna_vyska >= 1.9–2.1 m
Pravidlo: zabradli_madlo_vyska = 0.85–1.0 m, sloupky po 1.5–2.0 m, prurez madla 0.08–0.12 m; u zdi = žádné

Zdroje:
- https://www.spab.org.uk/node/541 (raná dřevěná schodiště: žebřík nebo dubové špalky)
- https://historicengland.org.uk/images-books/photos/item/MP/ROC0258 (Rochester, výkres stupňů)
- https://commons.wikimedia.org/w/index.php?search=Pernštejn+wooden+staircase&title=Special:MediaSearch&type=image

## 5. Ochoz a cimbuří (i na svažitých hradbách)

- **Ochoz na koruně.** Vede po koruně zdi za cimbuřím. Na tenčí zdi se rozšiřuje **dřevěným ochozem na krakorcích nebo
  trámech v kapsách** na vnitřní straně. Často byl **zastřešený pultovou nebo sedlovou stříškou** (doloženo na vedutách).
  Kolem 1400 vzniká souvislá obranná linie po koruně. Dřevěný **přízední ochoz** (hurdice, polygonální podsebití)
  vystupoval i vně.
- **Na svahu.** Koruna **neklesá šikmo**, ale **stupňovitě**. Ochoz má vodorovné úseky a mezi nimi schod nebo
  několik stupňů. Stínky sedí vždy na vodorovném úseku a stupeň připadá obvykle na střed stínky nebo za ni.
  Při mírném sklonu může ochoz i **plynule stoupat** a cimbuří pak sleduje sklon (na Moravě méně časté).
- **Stínky.** Do konce 14. stol. jsou zhruba stejně široké jako proluky nebo širší. Kolem 1400 se **stínky rozšiřují a
  proluky zužují**, ve stínkách se objevují **štěrbinové nebo klíčové střílny**. Proluky mohly mít **dřevěné okenice**
  na čepech.
- **Napojení na věž.** Ochoz vede do věže **vstupním portálkem v patře** (často je to původní vstup do věže):
  lomený nebo segmentový otvor, dveře zevnitř se závorou. Někdy přes **dřevěnou lávku nebo padací můstek**
  (věž je samostatně hájitelná). Ochoz věž neobchází.
- **Zábradlí.** Na vnitřní straně ochozu **obvykle žádné**. Volná hrana dřevěného ochozu na trámech mohla mít jednoduché madlo,
  ale doloženo to není. Pro hru je bezpečné použít nízké madlo jen u dřevěných úseků.

Pravidlo: zed_tl_koruna = 1.5–2.5 m (Helfštýn obvodová 2 m); predprsen_tl = 0.5–0.8 m
Pravidlo: ochoz_sirka_volna = 0.8–1.5 m (na zdi), drevěny_na_krakorcich = 0.8–1.2 m; krakorce rozteč 1.2–1.8 m
Pravidlo: stinka_sirka = 1.2–2.2 m (kolem 1400 spíš 1.6–2.2); stinka_vyska_nad_ochozem = 1.8–2.2 m
Pravidlo: proluka_sirka = 0.5–0.9 m; parapet_proluky_vyska = 0.8–1.0 m nad ochozem; stinka_hloubka = tl. předprsně 0.5–0.8 m
Pravidlo: strilna_ve_stince = štěrbina 0.06–0.12 × 0.8–1.2 m, osa 1.2–1.4 m nad ochozem
Pravidlo: svah_stupen_vyska = 0.4–1.0 m (max 1 stupeň na 1 stínku; při >1.0 m použít 3–5 schodů); svah_max_plynuly = 10°
Pravidlo: krycí_stříška = pult 25–35°, přesah 0.3 m; okap na straně nádvoří
Pravidlo: vez_portalek = 0.7–0.9 × 1.7–2.0 m, lomený/segment, práh = úroveň ochozu ±0.2 m; vazba: ochoz nekončí slepě
Pravidlo: zabradli = {kamenny_ochoz: false, drevěny: "volitelné madlo 0.9 m"}

Zdroje:
- https://cs.wikipedia.org/wiki/Cimbuří
- https://en.wikipedia.org/wiki/Battlement (proluka asi 1/3 šířky stínky u pozdějšího cimbuří)
- https://cs.wikipedia.org/wiki/Helfštýn (obvodová zeď 2 m, parkán konec 14. stol.)
- https://commons.wikimedia.org/w/index.php?search=Kokořín+castle+battlements&title=Special:MediaSearch&type=image
- https://commons.wikimedia.org/w/index.php?search=Sovinec+castle+wall&title=Special:MediaSearch&type=image

## 6. Prkenné podlahy, lávky a mosty

- Prkna jsou **štípaná nebo tesaná, řidčeji řezaná** (rámová pila se rozšiřuje od 14. stol.). Mají **nestejné šířky**
  a jsou **přibitá kovanými hřeby** (2 na trám) nebo na mostech zajištěná dřevěnými kolíky.
  Spoje jsou **střídané (vazba na přeskáčku)** a vždy **na trámu**. U mostu leží mostovky **napříč** přes 2–3 podélné trámy.
- Lávka nebo most přes příkop: **dubové nosníky** na zděných nebo dřevěných pilířích, nejbližší pole u brány je **padací**.

Pravidlo: prkno_sirka = 0.20–0.40 m (náhodně); prkno_tl = 0.04–0.06 m (podlaha), 0.06–0.10 m (most/mostovky)
Pravidlo: prkno_delka = 3–6 m (podlaha), mostovka = šířka mostu 2.5–3.5 m
Pravidlo: trámy_rozteč = 0.8–1.2 m (podlaha), trám 0.20–0.30 × 0.25–0.35 m; mostní pole 4–6 m
Pravidlo: spoj_na_tramu = true; posun_spoju_sousednich_prken >= 1 rozteč trámu; spáry 0.005–0.015 m
Pravidlo: hreby = 2 na průsečík, hlava Ø 0.015–0.02 m, odsazení od hrany 0.04 m; most: kolíky Ø 0.025–0.03 m
Pravidlo: mostni_zabradli = madlo 0.9–1.0 m, sloupky po 2–3 m (u pevných polí; padací pole bez)

Zdroje:
- https://www.buildingconservation.com/articles/early-timber-doors/early-timber-doors.htm (štípaná prkna, kované hřeby)
- https://cs.wikipedia.org/wiki/Helfštýn (most na zděných pilířích)
- https://commons.wikimedia.org/w/index.php?search=Bouzov+bridge+castle&title=Special:MediaSearch&type=image

## 7. Napojení hradby na věž nebo palác, nároží, šíje sklepa

- **Vazba zdiva.** Obvodová zeď a palác se stavěly současně a **provazují se** (střídavé zazubení vrstev),
  nebo na sebe **nasedají se spárou** (zeď přistavěná k věži, typická stavební etapa).
  Na drobovém zdivu je patrné **vrstvení** (lože po 0,3–0,6 m, vyrovnávací vrstvy z plochých kamenů a
  pracovní horizonty po 1–1,5 m s kapsami po lešení).
- **Nároží.** Je zpevněné **většími kvádry nebo lomovými bloky** v **střídavé vazbě** (dlouhá a krátká strana, takzvané armování).
  U droby jde o větší hrubě opracované kameny z téhož materiálu (Puchart: jen droba, bez pískovce).
- **Omítka.** Gotická **režná nebo „pietra rasa“** (malta přetažená přes hlavy kamenů, nechávající je částečně
  viditelné). Celoplošná omítka na palácích může mít malované spárořezy.
- **Šíje sklepa.** Úzký **zaklenutý vstup se schody dolů** (valená klenba, stoupající nebo stupňovitá), vede
  z nádvoří nebo z přízemí paláce. Ostění portálku je kamenné se sražením, nároží šíje má kvádrové armování.
  **Kamenné stupně** jsou masivní, ošlapané. Nahoře bývá dřevěné **přiklopení** (sklepní poklop) nebo dveře.

Pravidlo: narozni_kvadr = 0.4–0.8 (dl.) × 0.25–0.4 (výš.) × 0.25–0.4 m (hl.), střídat dl./krátká strana po každé vrstvě
Pravidlo: zdivo_vrstva = 0.3–0.6 m; vyrovnavaci_vrstva_kazdych = 1.0–1.5 m; lesen_kapsy = 0.12–0.18 m čtvercové, rozteč 1.5–2.0 m
Pravidlo: napojeni = {soucasne: "zazubení po 1–2 vrstvách", pristavba: "svislá spára, bez vazby"}
Pravidlo: omitka = "pietra rasa", podil_odhaleni_kamene = 30–60 %, barva vápenná béžovo-šedá
Pravidlo: sije_sirka = 1.0–1.6 m; sije_vyska_klenby = 1.9–2.3 m; schod = 0.18–0.25 vys. × 0.25–0.35 m hl., kamenný blok
Pravidlo: sije_klenba = "valená stoupající/stupňovitá"; portalek = 0.9–1.2 × 1.8–2.0 m, srazeni 0.05–0.08 m

Zdroje:
- https://cs.wikipedia.org/wiki/Helfštýn (malý kamenný palác s valeně zaklenutým sklepem)
- https://commons.wikimedia.org/w/index.php?search=Hukvaldy+castle+wall&title=Special:MediaSearch&type=image
- https://commons.wikimedia.org/w/index.php?search=Star%C3%BD+Ji%C4%8D%C3%ADn+castle&title=Special:MediaSearch&type=image
- https://commons.wikimedia.org/w/index.php?search=pietra+rasa+medieval+plaster&title=Special:MediaSearch&type=image

## 8. Povrch nádvoří kolem 1400 a vegetace

- Ve 14. stol. převládá **udusaná hlína nebo jíl, rostlá skála a štětovaný drť**. Postupně narůstají vrstvy
  **odpadu, hnoje a organiky**. Pravidelnější **valounová dlažba** se v archeologii objevuje většinou **až v 15. století**.
  Kolem 1393 je tedy realistické: **skála, udusaná hlína a drť**, místy **štětování z plochých lomových kamenů**
  (u brány, pod okapy, u studny nebo cisterny) a **dřevěné lávky a prkna** přes bláto.
- U drobového hradu na ostrožně je tu **vystupující rostlá skála** s kluzkými lavicemi břidlice.
- **Vegetace.** Nádvoří bylo prošlapané, ale při patách zdí, v koutech a okolo předhradí rostla **ruderální vegetace**
  (kopřiva, lopuch, merlík, pelyněk, jitrocel u cest, mech na severních stěnách). Kolem hradu byl **bezlesý pás**
  (palebné pole, kácení na dřevo), pastvina a křoviny (trnka, šípek, líska).

Pravidlo: povrch_nadvori = {skala: 20–40 %, udusana_hlina: 40–60 %, stetovani_lomovy: 10–20 % (brána, okap, studna), valouny: 0 % (pozdější)}
Pravidlo: stetovani_kamen = 0.15–0.30 m ploché lomové; okapova_ryha = 0.3–0.5 m šir., 0.05–0.1 m hl. pod okapem
Pravidlo: koleje_vjezd = rozchod 1.1–1.3 m, hloubka 0.03–0.10 m; prošlapané cesty 0.6–1.0 m mezi vstupy
Pravidlo: vegetace = {pata_zdi: pás 0.2–0.6 m kopřiva/lopuch/tráva, kouty: 0.5–1.5 m, střed_nádvoří: <10 % pokryvu}
Pravidlo: okoli_hradu = bezlesý pás 30–80 m (tráva, pařezy, křoví); les až za ním

Zdroje:
- https://app2.ssc.avcr.cz/ARUB-prehled-vyzkumu/files/28247.pdf (pravidelnější valounová dlažba až 15. stol.)
- https://app2.ssc.avcr.cz/ARUB-prehled-vyzkumu/files/28506.pdf (narůstání terénu humusem ve 14. až počátkem 15. stol.)
- https://www.seznamzpravy.cz/clanek/regiony-zpravy-karlovarsky-kraj-na-hrade-hartenberg-zkoumaji-archeologove-nadvori-i-puvodni-pristup-212437

## 9. Lesní potok v Nízkém Jeseníku a Oderských vrších

- **Koryto.** V úzkém zaříznutém údolí (V tvar) je koryto **mělké a kamenité**: štěrk, valouny a **ploché kameny droby
  a břidlice** (rozpadají se do desek, hrany jsou ostré a málo omleté). Střídají se **peřeje, stupně a tůně**
  (step–pool), drobné **kaskády přes skalní prahy** a **naplavené dřevo** (padlé kmeny, větve), které tvoří stupně.
- **Břehy.** Jsou nepravidelné. Na jedné straně je **nárazový břeh** (podemletý, s obnaženými kořeny), na druhé **štěrková lavice**.
  Mech na kamenech nad hladinou, **kapradiny, devětsil, bažanka, šťavel, řeřišnice a netýkavka** jsou ve vlhkých partiích.
  Stromy: **olše lepkavá, jasan, javor klen, buk a smrk** dál od vody. Kořeny olší drží břeh.
- **Co dělá přírodní dojem.** Žádné rovné úseky delší než 5–10 m, proměnlivá šířka, kameny ve shlucích (ne
  rovnoměrně), světlejší suché kameny nad čárou vody a tmavé vlhké pod ní, pěna a bílá voda jen na stupních,
  listí a jehličí v tůních, mokré tmavé pásy na břehu, drobné postranní pramínky.
  KCD2 (Warhorse) staví prostředí na fotogrammetrii české krajiny. Potoky tam mají přesně tuto
  skladbu: štěrk, mech, kapradí, padlé dřevo a nepravidelný břeh.

Pravidlo: sirka_hladiny = 0.5–2.5 m (měnit ±50 % po 5–15 m); hloubka = 0.05–0.3 m, tůně 0.4–0.8 m
Pravidlo: step_pool_roztec = 2–5 × šířka koryta; stupen_vyska = 0.1–0.5 m; meandr_amplituda = 1–3 × šířka
Pravidlo: substrat = {stěrk 2–6 cm: 40 %, valouny 6–25 cm: 35 %, balvany 0.25–1.0 m: 15 %, skála: 10 %}; tvar kamenů: ploché desky (droba/břidlice)
Pravidlo: balvany_shluky = 3–7 kamenů, rozestup shluků 2–6 m; naplavene_drevo = 1 kmen na 10–30 m toku
Pravidlo: breh_vyska = 0.2–1.0 m; strana_narazova: strmá + kořeny; strana_jesepni: štěrková lavice 0.5–2 m šir.
Pravidlo: vegetace_pas = 0–2 m: mech/kapradí/devětsil/netýkavka; 2–8 m: olše, jasan, klen; dál buk/smrk
Pravidlo: barvy = {kámen_suchý: světle šedý/okrový, kámen_mokrý: tmavě šedý + mech, voda: čirá s hnědým nádechem}

Zdroje:
- https://www.ametyst21.cz/wp-content/uploads/2025/06/Metodicky-list_-Zivot-v-hornich-usecich-toku-–-perlorodka.pdf (dno: balvany a štěrek)
- https://dspace.cuni.cz/handle/20.500.11956/30716 (step–pool, kaskády, dřevo v korytě)
- https://theses.cz/id/uk613t?lang=en (skalní koryta, Jeseníky)
- https://80.lv/articles/this-is-how-kingdom-come-deliverance-ii-locations-look-in-real-life
