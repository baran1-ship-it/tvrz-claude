# Kompozice celé mapy – „plné scény“ (Míša 29. 10. večer: „udělej takhle ves, ale takhle musíme udělat celou mapu“)

Cíl: z žádného místa, kam hráč dojde pěšky nebo dojede na koni, není vidět dál, než oblast unese (kromě záměrných
výhledů). Co není vidět, se nekreslí (zakrývač u každé zábrany). Výkon i dojem z jednoho principu – svět jako
místnosti (KCD: zatáčka, remízek, stodola, mez, lem lesa).

## Výchozí stav (29. 10., `tools/mapa_vyhledu.py --krok 25`)
- Ves: 117 ze 136 bodů otevřených přes 130 m, průměrný dohled 235 m (`docs/screens/ves_dohled_pred.png`). Ves má
  8 domů 40–60 m od sebe, mezi nimi louka – není čím zavřít.
- Celá mapa: 31 z 506 bodů přes 300 m. Záznamů: 16 remízků, 5 výhledů.
- Kreslení (měření mer0995): let nad vsí 654, u chlívku 1151, mlýn 537 (rozpočet tabletu ~500).

## Mez dohledu podle oblasti (`lokace.json kompozice dohled_oblasti`)
| oblast | mez | proč |
|---|---|---|
| ves | 130 m | nejdražší pohledy (stavby, předměty) |
| les | 120 m | uvnitř plný, průhled jen světlinou/pěšinou |
| louky a pole | 200 m | okraj lesem, remízkem nebo mezí |
| cesty mezi lokacemi | 250 m | rytmus zavřeno → zavřeno → výhled |
| záměrné výhledy | bez meze | věž, Pustá skála, příjezd ke vsi/tvrzi/hostinci |

## Zábrany (každá je záznam v datech s důvodem, nikdy ruční výjimka)
- **Dvorec** (ves): dům + stodola za domem + chlév/kůlna do strany + plot dvora + sad za stodolou. Stodola zavře
  pohled napříč vsí, sad a ploty doplní. Modely: stodola a kůlna z Disku/Sketchfabu (CC-BY), jabloň, plůtky.
- **Zatáčka ulice a náves**: lípa a studna/kříž na návsi, ulice s ohybem – ze žádného bodu ulice víc než 4–6 domů.
- **Remízek** (meze, kamení, vlhko), **mez s keři** (hranice lánů, plužina), **lem lesa** (keře do výšky chlapa),
  **stromořadí u cesty**, **úvoz** (cesta ve svahu).

## Postup na každou oblast (pojistky, Míša: „bojím se miliardy chyb“)
1. Mapa dohledu oblasti → seznam otevřených bodů a směrů.
2. Návrh zábran z dat (generátor): zábrana jen tam, kde je logická (okraj pole, mez, za domem), s důvodem.
3. Test smyslu: zábrana ne na cestě, ve vodě, na svahu, ne přes záměrný výhled; každá chyba od Míši = nová kontrola.
4. Export → mapa dohledu znovu (cíl: 0 chyb v oblasti) → měření kreslení na pevných bodech (cíl ≤ 500).
5. Snímky z pevné sady záběrů (Míšina místa + pohledy do oblasti) před a po, porovnat vedle sebe, až pak vydání.

## Pořadí oblastí
1. Ves (dvorce, náves, zatáčka) – plánek Míše před stavbou.
2. Cesta tvrz – ves a okolí tvrze.
3. Mlýn, rybník Lhota, potoky.
4. Hostinec a stan, lom, skály a větrák, okraje mapy.

## Výkon (souběžně, měřeno na stejných bodech)
- Zakrývače domů (hotovo v kódu 29. 10.), zábrany dostanou zakrývač automaticky.
- Stíny: kratší dosah, stínují jen velké věci (měření: stíny −186 až −224 kreslení).
- Stavby vsi sloučit podle materiálů po dvorcích (měření: stavby −290 kreslení).
- Bez prolínání dosahů (hotovo 29. 10., `modely.json prolinani_dosahu`).

## Rešerše „budovy plus zeleň“ (Míša 29. 10.: „najdi si návody pro KCD2… budovy plus zeleň“)
- **Warhorse** (level designer, welcometothejungle.com): ves skládají z budov zasazených do terénu, zeleň generuje
  program podle pravidel a designer ji pak ručně doladí; předlohou jsou skutečná místa (Rataje, cesty sedí dodnes),
  Google Maps a Street View; detaily se ladí tam, kde hráči chodí (cesty), hluboko v lese jsou jen 2 % hráčů.
  Veřejný návod na stavbu vsi v nástrojích KCD/KCD2 není: wiki KCD (Nexus) má jen vegetaci jako binární data
  level.pak, nástroje KCD2 (Editor.exe, CryEngine Sandbox) zatím jen úpravy assetů.
- **Far Cry 5** (GDC 2018, É. Carrier): každý druh roste jen tam, kde má důvod (stanoviště); vegetace se
  generuje podle pravidel – stejně jako náš `druhy.json` a test smyslu.
- **Tradiční schéma zeleně u stavení** (Dohnalová, Dohnal: Předzahrádky na Podluží, 2023, obr. 1 a 2): 1 předzahrádka
  s lavičkou, 2 jeden až dva stromy u vjezdu, 3 strom na dvoře (stín, hnojiště), 4 protipožární strom u stodoly
  v humně, 5 ovocná zahrada. Stromy návsi tvoří srdce sídla, stromy zahrad zelený prstenec, který ves spojí s krajinou.
  Stromy u stodol a humen dělí uzavřený dvůr od otevřených sadů.
- **Plužina** (Černý, Vermouzek): záhumenice navazují přímo na usedlosti podél osy vsi, takže za stodolou pokračuje pruh
  zahrady a sadu a pak pole.
- Zapsáno v `lokace.json ves.dvorec` (stodola, kůlna, sad, živý plot, zeleň, doplnění chalup), plánek
  `tools/ves_dvorce.py` → `docs/screens/ves_dvorce_plan.png`. Dohled z ulice: dnes 19 z 20 bodů nad 130 m,
  B 15, C 5 (průměr 73 → 49 → 33 m).

## Astra 29. 10. – pravidla pro celou mapu (platí přednostně před tím, co je výš)
- Svět jako propojené menší scény, sevřená a otevřená místa se střídají (dvůr, ohyb mezi stodolami, náves, sad,
  cesta pod mezí, světlinka, výhled); žádná nekonečná chodba ani kruh keřů kolem hráče.
- Hlavní zakrytí **pevnými tvary**: terénní hřbet, zatáčka kolem skály nebo dvorce, plné stěny domů a stodol, úvoz.
  Keře, sady a lem lesa jsou jen doplněk; listí není neprůhledná stěna. Terén kvůli zakrytí neupravovat.
- **Ves = varianta B** (dvorce v `lokace.json ves.dvorec`): žádné domy navíc jen kvůli mapě dohledu (každý dům stojí
  výkon), takže `tools/ves_dvorce.py` je kreslí jen s `--doplnit`; průhled branou zůstává skutečný.
- **Zakrývače** (OccluderInstance3D) jen přes pevný tvar (terén, zdi domů a stodol), ne přes remízek a nitro lesa:
  `pravidla_sveta.json pasma.test.okluzor_listi` false (dřívější krabice remízků a lesa vypnuté, true jen pro A/B).
  Nečpat je do dveří, oken a průhledů. Slučovat jen uvnitř dvorce podle materiálu, ne celou ves nebo celý les;
  MultiMesh dělit prostorově.
- **Výhledy** mají levnou dálku (reliéf, siluety lesa, střechy, dominanty; HLOD/impostor, přepínání s hysterezí, ne
  průhledné prolínání). Výjimka výhledu potřebuje výšku a směr pohledu (kruh kolem věže nesmí povolit dohled odevšad
  dole u tvrze) – **ZBÝVÁ** doplnit do `kompozice.vyhledy`. Mlha není úspora.
- **Mapa dohledu** (`mapa_vyhledu.py`, `ves_dvorce.py`) odděluje A) pevné zakrytí (terén, zdi), B) listí (koruna jen
  pás od nasazení `kompozice.mapa_dohledu.nasazeni_koruny` po vrchol, vizuálně zavře až po `listi_zavre_m` listí),
  C) výkon ve hře (jen měření). Oči pěšího 1,7 m i jezdce 2,4 m. Po opravě: celá mapa 106 z 506 bodů přes 300 m
  (dřív 31 – koruny falešně zavíraly), ulice vsi: otevřených směrů přes 130 m pevně dnes 43 %, B 34 %.
- Vzdálenosti 130/120/200/250 m jsou kompoziční vodítko, ne limit tabletu. Rozhoduje, co je vidět a kolik to stojí.
- **Přejímka na tabletu** pro každou oblast: stejné místo, směr, rozlišení, HUD, po doběhnutí načítání; snímek,
  draw calls, trojúhelníky, paměť; stání i průchod pěšky a na koni; p95/p99 časů snímků a dlouhé záseky; A/B okluze.
  500 draw calls je pracovní cíl. Hotovo = plnější svět a prokazatelně lepší výkon, nic nemizí v průhledech.

## Astra 29. 10. (2) – krajina v duchu KCD pro Xiaomi Pad 8: co přebíráme (Míša: „vem si z toho, co se nám hodí“)
Pásma a rozpočty jsou návrh k měření, ne zjištěný výkon. Přebíráme:
1. **Jedno rozmístění, tři podoby** (blízko detail, středně zjednodušeně, dálka silueta). Přepnutí nesmí změnit místo,
   výšku, barvu ani objem koruny. Navazuje na stávající LOD a impostory stromů. Kontrola: snímek před a po přepnutí ze
   stejného místa.
2. **Terén**: jeden výsledný terén pro vodu, cesty, stavby, rostliny a kolizi (máme: zámek terénu, `fort.land`). Jemná
   síť jen u koryt, hran cest, břehů a lomu (máme pásy u vody 0,5–1 m). Spáry mezi díly hlídá test `visici`/`breh_toku`.
   Dno toku je záznam (hladina − hloubka), terén v korytě pod něj nejde (`kraj.py` 29. 10., export 0995b, výtok od mlýna).
3. **Povrch bez trsů**: po skrytí trávy (A/B `louka`) musí zůstat smysluplný povrch stanoviště, ne světlá plocha.
   Masky z Blenderu z finálního terénu, nejvýš dvě hlavní vrstvy na díl a makrovariace. Ověřit, že normal mapy
   a masky nejdou přes úpravu barev albeda (`tools/textury_tablet.py`) a že ve vydání jsou mipmapy a ETC2.
   **ZBÝVÁ:** snímek A/B bez louky z Míšiných míst.
4. **Les**: šetřit modelem, ne vyprázdněním. Karty listí oříznout těsně k vyplněné části (overdraw), méně povrchů
   materiálu, porovnat LOD ze strany i shora. Podrost ve shlucích podle světla. **ZBÝVÁ:** změřit overdraw karet.
5. **Tráva**: 0–20 m detailní trsy, 20–60 m jednodušší shluky stejné barvy, dál povrch a jen výrazné porosty (rákos,
   obilí, lem lesa vlastní pravidla). Střední podoba musí převzít pokrytí, ne náhodné mazání. Tráva a drobné květiny
   bez vrhaných stínů (ověřit). Buňky 32 m zůstávají, jiné velikosti až podle měření.
6. **Zakrytí a slučování**: jak výš (pevné tvary, slučovat po dvorcích, otevřené dveře a kůlna průhledné). Sdílený
   materiál sám nesloučí uzly do jednoho draw callu – slučovat skutečně v síti.
7. **Výhled**: v popředí kvalitní skála, zábradlí a stromy (měřítko), dálka jen tvary (reliéf, siluety lesa, střechy).
