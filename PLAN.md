# Odkaz Havrana – plán prostředí

Cíl: tvrz kolem roku 1400 v kraji pod Sázavou, s prostředím, které působí jako v KCD2: skutečný kámen,
vápenná omítka, dub, šindel a došky. Má to být uvěřitelné, opotřebované a zabydlené přírodou.
Hra běží na tabletu (Xiaomi Pad 8, OpenGL renderer), takže každý detail musí projít i výkonem.

## Zásady vzhledu

1. **Tvar dělá geometrie, povrch dělá materiál.**
   - Geometrie: obrys, hrany a všechno, co oko vidí z boku. Nároží a ostění z kvádrů se zkosením,
     klenáky oblouků, nerovná koruna zdi, jednotlivá prkna s mezerou, trámy se zkosenou hranou,
     došky s tloušťkou, šindel v řadách.
   - Materiál: plochy. Fotografická textura s výškovou mapou (parallax), omítka zatéká do spár,
     u paty zdi vlhko a špína, mech na severních stranách.
2. **Žádná textura nesmí působit jako fotka nalepená na krabici.**
   - Každá plocha má mít výškovou mapu, správné měřítko (asi 256 px na metr) a nesmí se opakovat
     v pravidelném vzoru.
   - Na hranách je vždy geometrie.
3. **Stavebnice místo jednoho bloku.**
   - Každá stavba je samostatný model (`modely/stavby/<nazev>.glb`) s vlastními kolizemi.
     Hra je skládá podle `svet.json`.
   - Dveře a vrata jsou samostatné dílky se zárubní a pantem a dají se otevřít.
4. **Napojení musí dávat stavebně smysl.**
   - Na rohu hradby se střechy ochozu potkají v úžlabí a nároží (jako dům do L).
   - U věže ochoz končí do zdi pod římsou.
   - Volný konec ochozu uzavírá prkenný štítek.
   - Štít je zarovnaný se zdí, střecha přes něj přesahuje a hranu kryje čelní prkno.
5. **Střechy: staré dřevo (šindel), šedohnědé, zvětralé.**
   - Řady šindelů jsou nepravidelné a zvlněné, místy vybledlé, s mechem a záplatami z novějšího dřeva.
   - Pálené tašky nikde.

## Podle referenčních fotek z KCD2 (Suchdol, Trosky)
- **Omítka:**
  - souvislá hrubá vápenná, bílá až krémová, šedne nečistotou a stéká;
  - kámen jen u paty zdi (vlhko), u nároží a v menších ostrůvcích.
- **Nároží a ostění:** střídavé kvádry, které vystupují z líce; oblouky z klenáků.
- **Dveře:**
  - lomený kamenný portál se zkosenou hranou;
  - dubová prkna, husté kované hřeby v řadách, kované pásy, kruh;
  - malé dveře mají také lomený oblouk.
- **Ochozy:**
  - svislá prkna s mezerami, sloupky se vzpěrami a šindelová stříška;
  - z nádvoří jsou vidět otevřené, s trámovou konstrukcí.
- **Věže:**
  - kamenný omítnutý dřík s kvádrovými nárožími;
  - nahoře hrázděné nebo bedněné patro na krakorcích, vysoká šindelová střecha s makovicí.
- **Nádvoří:** udusaná hlína a písek, ostrůvky kočičích hlav, tráva u zdí.

## Etapy

### E1 – úklid a opravy (verze 0.6)
- [ ] Smazat veškeré vybavení interiérů a předměty na nádvoří. Místnosti zůstanou prázdné, studna a vůz zůstávají jako součást stavby.
- [ ] Most a padací most: plynulý nájezd bez schodu.
- [ ] Schody na ochoz: kolize. Deska na schodišti v patře: otvor v podlaze.
- [ ] Prahy ve dveřích pryč (zůstane jen kamenný práh v úrovni podlahy).
- [ ] Střecha paláce: štít zarovnaný se zdí, čelní prkna.
- [ ] Parallax: zeslabit při ostrém úhlu pohledu (zubaté schůdky na hraně omítky).
- [ ] Les: stromy s jehličím (méně zjednodušit, ve větší dálce billboardy). Tráva bez zelených čtverců.
- [ ] Kroky: skutečné nahrávky (CC0) pro hlínu, trávu, kámen, dřevo.
- [ ] Nápis v menu oříznutý vlevo.

### E2 – stavebnice, dveře a dřevo
- [ ] Dřevo všude ze skutečných prken a trámů. Každé prkno má:
  - vlastní tvar, vlastní odstín a jinou orientaci letokruhů;
  - mezeru, hřebíky a zkosené hrany.
- [ ] Most a padací most: prkna ochozená chůzí (vyšlapaná stopa uprostřed, ohlazené hrany, tmavé vlhké spáry, bláto).
- [ ] Padací most jako samostatný model:
  - rám z trámů, prkna, kované pásy;
  - řetězy z článků přes kladky;
  - zvedání ve hře.
- [ ] Export po stavbách (`modely/stavby/*.glb`), rozmístění v `svet.json`, kolize každé stavby zvlášť.
- [ ] Dveře ve třech úrovních:
  - **hlavní venkovní** (síň, věž, brána):
    - lomený kamenný portál s profilací;
    - těžké dubové dveře (i dvoukřídlé), husté kované hřeby v řadách;
    - pásy pantů s rozvilinami, kruh s klepadlem;
  - **venkovní obyčejné** (zbrojnice, sklep, hospodářské):
    - prostý kamenný nebo dřevěný rám;
    - prkna se šikmou vzpěrou, dva pásy, zámek, závora;
  - **vnitřní:**
    - lehčí prkna v dřevěné zárubni;
    - dřevěná nebo kovaná klika a petlice, bez hřebů.
- [ ] Všechny dveře ve hře: klepnutím otevřít a zavřít (otočení na pantu, kolize se otáčí s křídlem, zvuk).
- [ ] Vrata brány a padací most jako pohyblivé dílky.

### E3 – hradby, ochozy, věž, brána
- [ ] Hradba: lomové zdivo s omítkou podle výšky, kvádrová nároží a pata zdi, nerovná koruna.
- [ ] Krytý ochoz:
  - bednění z jednotlivých prken s mezerami a střílnami;
  - došková střecha s tloušťkou a okapovou hranou;
  - nároží a úžlabí na rozích, napojení na věž a bránu.
- [ ] Věž: kamenné patro, hrázděné patro, šindelová stanová střecha s makovicí, střílny a okna v ostění z kvádrů.
- [ ] Brána: klenutý průjezd, klenáky, padací most na řetězech z článků, vrata.

### E4 – palác, strážnice, zbrojnice
- [ ] Palác znovu:
  - kamenné přízemí a hrázděné patro;
  - pavlač;
  - šindelová střecha s polovalbou a vikýři;
  - komín;
  - portály: gotický portál do síně, pravoúhlé ostatní.
- [ ] Zbrojnice (stávající budova u brány): zůstane na místě, uvnitř prázdná.
- [ ] Hospodářské doplňky: přístřešek na dříví, žlaby, studna s rumpálem.

### E5 – vybavení a stavění
- [ ] Katalog předmětů (`modely/predmety/*.glb`): stoly, lavice, truhly, sudy, police, postele, svícny, zbraně,
      stojany. Vlastní modely a CC0 modely (Poly Haven a další), všechny ve stejném stylu a měřítku.
- [ ] Pískoviště: výběr předmětu, umístění, otočení, odebrání, uložení rozmístění.
- [ ] Menu hráče (pergamen, LB/RB přepíná hlavní stránky):
  - **Výbava:** postava a sloty;
  - **Brašna:** Zbraně, Zbroj, Nářadí, Jídlo, Suroviny, Ostatní;
  - **Výměna** s truhlou, skříní, sudem nebo pytlem;
  - **Stavění** (pískoviště), záložky:
    - Venkovní vybavení: vozy, seno, palivo, ohrady, koryta, stojany na zbraně;
    - Vnitřní vybavení: postele, stoly, lavice, skříně, truhly, police;
    - Dekorace: svícny, lucerny, nádobí, koberce, praporce, štíty na zeď;
    - Řemeslo a nářadí: kovadlina, ponk, kolovrat, nářadí;
    - Zbrojnice: stojany a figuríny se zbrojí, terče.
- [ ] Louče:
  - kovaný držák na zeď (objímka, rozvilina, kroužek), louč v něm;
  - louč jde vzít do ruky a vrátit do držáku, zapálit a zhasnout;
  - světlo: plamen jako částice, kouř, jiskry, mihotající světlo se stíny, teplá barva, zvuk praskání;
  - v ruce se světlo pohupuje s chůzí.
- [ ] Stoly a židle: Poly Haven + vlastní dobové (selský stůl na kozách, trůnní křeslo, trojnožka).
- [ ] Interakce: sednout (lavice, židle, stolička), lehnout a spát (postel), otevřít úložiště (truhla, skříň, sud, bedna, pytel) bez animace, jen zvuk a menu výměny.
- [ ] Příběh: na začátku jen pár věcí, zbytek se vyrábí v dílně nebo kovárně nebo kupuje (doladíme spolu).

### E6 – krajina
- [ ] Les z více druhů (smrk, borovice, buk, bříza) s podrostem a padlými kmeny.
- [ ] Cesta k tvrzi s vyjetými kolejemi, louky s květy, plot a pole.
- [ ] Světlo a atmosféra: denní doby, mlha u vody, mraky.

## Kvalita a distribuce
- Rozhodnutí: kvalita má přednost před velikostí APK.
  - Textury 2k (normály i drsnost).
  - Rostliny a předměty 1k.
  - Žádné zmenšování kvůli limitu.
- Distribuce velké hry:
  - APK (kód, menu, zvuky, pod 100 MB) + datové balíky `.pck` (modely, textury) rozdělené na části pod 95 MB v repozitáři.
  - Hra je při prvním spuštění stáhne z GitHubu do `user://`, spojí a načte (`ProjectSettings.load_resource_pack`).
  - Při nové verzi se stáhne jen to, co se změnilo.
  - Pokud budou k dispozici GitHub Releases (soubor až 2 GB), stačí jeden soubor.

## Zdroje
Jen licence, které dovolí hru volně šířit: CC0 (Poly Haven, ambientCG, Kenney), Sketchfab s licencí CC0 nebo CC BY
(s uvedením autora). Ke stahování ze Sketchfabu je potřeba API token.
Seznam je ve hře v titulcích.
