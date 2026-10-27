# Krok C – zasazení (rozpracováno při exportu 0.97, zapojit po vydání)

Výchozí stav: test `zasazeni` po zámku terénu (export 15:01) hlásí 11 343 chyb.

## 1. Kamínky na cestách – rozpor dvou pravidel (≈ 9 000 z 9 102 „bylin v pásmu“)
- `pasma.skupiny.popis`: „nízké byliny … a kamínky jen mimo jízdní pás (0)“.
- Rádce 18:00 bod 3 (`svet._cesty_kameny`): kamínky 5–20 cm jako modely na cestě (kraje 1,5/m², hřbet 0,4, koleje 0,2) – hra je tam klade záměrně.
- Návrh: nová skupina `povrch_cesty` = [`kamen_maly`] s odstupem `-inf` (patří na hlínu). Větší kameny (`kamen_zula`, `kamen_piskovec`, `kamen_droba`, 0,4–1,4 m) přidat do skupiny `balvan` → mimo pás a ker_od_m. Na hlíně jich je z Blenderu ~30, to je pak skutečná chyba.
- Byliny na hlíně přímo z Blenderu: `divoka_trava` 77, `grass_medium` 28, kopřivy 20, pampelišky 9, keře 10, smrk 3 (data Blenderu). Hra je má odstranit v `_cesty_rostliny`. Co zůstane, přidávají až rozsevy hry po něm → rozsevy volat přes `smi_tu_byt` s pásmem cest (místo mazání stanoviště, pipeline zásada 4).

## 2. Visí stromy a keře (≈ 600)
- Rostliny na skalách a balvanech: test je už vynechává (jejich kolize se načítá jen kolem hráče).
- Kolize terénu se teď staví z hotové sítě (zámek). Zbytek ověřit po exportu 0.97: `_na_zem` posouvá jen rostliny mimo pás ±0,25 m, test hlásí nad 0,30 m.

## 3. Nad cestou (32 vozová, 25 pěšina) – vypsat, co to je (kolize objektu nad osou cesty).

## 4. Míšovy poznámky z 0.95 (data, ne záplaty)
- Hlína kolem kupeckého stanu: dvůr stanu jako plocha `udusano` v `lokace.json` (jako placek hostince), ne zelený čtverec.
- Strom u prvního domu vpravo moc velký: druh a velikost z tabulky (`modely.json` třída), ne ručně.
- Cestička k rybníku moc široká a jiná textura: šířka v `cesty.json` `pesiny_odvozene` podle tabulky pásem pěšin; povrch stejný jako u pěšin.
- Rastr bylin u (415, 917): rozsev bez mřížky (zjistit, který rozsev).
- Šířka cestiček 0,75 m natvrdo v `_cesty_tvar` → `cesty.json`.

## 5. Předloha KCD1/KCD2 (docs/screens/kcd1, ref_kcd2_*) – kameny, rostliny, cesty
- **Cesta (kcd1_03, kcd1_33, ref_kcd2_cesta_les):** povrch je hlína se štěrkem **v textuře** (drobné kamínky jen jako povrch, ne 3D). 3D kameny leží **na kraji** a za krajem: snosy polních kamenů u cesty a meze, větší balvany v trávě u krajnice. Hřbet mezi kolejemi travnatý, v kolejích nic. Okraj cesty = vysoká tráva s květy (vlčí mák, chrpy), kapradí a mladé smrčky v lese.
- **Louka a mez (kcd1_03):** kamenná mez / snos kamení podél cesty a polí, na ní tráva a keře; jednotlivé stromy na mezi, za nimi les jako stěna.
- **Ves (kcd1_22):** dvůr udusaný, pár kamenů u zdí a podezdívky, sudy, stůl, kůlna; tráva jen u zdí a v koutech.
- **Pravidla z toho (krok C, data):**
  - `_cesty_kameny`: 3D kamínky jen na krajích hlíny (pás kraj ± 0,5 m), hřbet a koleje 0 (povrch = textura). Rozpor s pásmy pak zmizí. Stačí upravit hodnoty rádce 18:00 (hřbet 0,4 a koleje 0,2 → 0), test a skupiny zůstanou.
  - Meze a snosy kamení podél cest a polí jako záznam v `plochy.json` (mez = pás 2–4 m na hranici lánu nebo cesty: kameny + keře + tráva + občas strom).
- **„Plné scény“ / svět jako místnosti** (Míša 26. 10. 21:00–21:10): popředí a střední plán plné (lem lesa z keřů do výšky chlapa, meze, ploty, sady), výhled do dálky jen ze skal a z věže. Úspora: co zakryje lem a terén, se nekreslí (okluzory, dosahy tříd), takže se kreslí míň než dnes s holými kmeny a prázdnou plání. Rozpočet tabletu ≤ 700 kreslení a ≤ 1,5 M troj. na záběr, měří `mapa_vyhledu` před a po.

## 6. Předloha KCD – cesty ve svahu, vodní toky, les (kcd1_05, _14, _26, _38, ref_kcd2_ves_rybnik, _louka_les)
- **Cesta ve svahu (kcd1_05):** na straně do kopce zářez (úvoz) s obnaženými kameny a hlínou ve svahu zářezu, na straně z kopce lem kamenů v trávě. Kamínky jen u krajů, ve stopě nic. → `cesty`: úvoz = svah zářezu se stanovištěm „kamenitý svah“ (kameny 0,2–0,6 m napůl v zemi), lem kamenů na dolní krajnici.
- **Příchod k bráně (kcd1_14):** ploché kameny napůl zapuštěné u krajů, štěrk ve stopě jen jako textura.
- **Potok a strouha (kcd1_26):** voda tmavá, na klidné vodě lekníny a okřehek, břeh podemletý (hlinitý stupeň), na něm vysoká tráva a rákos; podél vsi proutěný plot (`withe_fence.glb` od Míši). → malé toky: hladina s okřehkem a lekníny v klidných úsecích (spád < 1 %), břeh = stupeň 0,3–0,5 m (`toky_tvar.breh_m`), rákos a vysoká tráva v pásu 0–1,5 m od vody.
- **Rybník u vsi (ref_kcd2_ves_rybnik):** přes přítok lávka z kulatin, blátivá cesta k vodě, rákos, ploty. → přítok Lhoty pod pěšinou: lávka z kmenů (most/brod se odvodí z křížení toku a pěšiny).
- **Les (kcd1_38, ref_kcd2_louka_les):** listnatý les hustý od země (mladé stromy, keře, podrost), kmeny teprve uvnitř; okraj lesa = souvislá stěna zeleně; ve svahu obnažená půda a kameny. → potvrzuje „plné scény“: lem lesa z keřů a mladých stromů, uvnitř podrost.

## 7. Kompozice z pohledu hráče (rádce 19:35, Míša 19:28–19:29) – součást C
- **Průchod:** nejdřív cesty po 50 m (hlavní, odbočka do vsi, cesta k lomu, pěšina k hostinci), pak mřížka 100 m přes celou mapu (les i louka). Výška očí 1,7 m (pěšák) a 2,4 m (jezdec).
- **Zápis bodu:** dohled (paprsky z očí v 16 směrech, terén + kolize + koruny), co výhled otevírá, čím ho zavřít a proč je ta zábrana logická.
- **Zábrany ≥ 3 m s důvodem:** remízek na mezi / u kamení / na vlhku, klenba korun nad cestou v úvozu a lesním úseku, hřbet terénu, zatáčka za lesíkem nebo skálou, mez s keři a stromem, sad, plot a stodola u lokací. Keř do výšky chlapa zavře jen pěšáka.
- **Záměrné výhledy** (`vyhled` v kompozici, test je nepočítá jako chybu): vyhlídky (věž, Pustá skála, vrchol kopce), příjezdový pohled na každou lokalitu (z kopce na ves, na tvrz na návrší, od brodu na mlýn – vždy po zavřeném úseku), výhled přes louku k lesu 150–250 m. Rytmus zavřeno → zavřeno → otevřeno, každý výhled jiný, plánovat pro jezdce.
- **Louka** má okraj do 150–200 m (les, remízek, mez); velké plochy rozdělit mezemi s keři a kamením (plužina 1393). **Les** uvnitř plný, průhledy jen světlinou nebo pěšinou.
- **Data:** `lokace.json: kompozice` (záznamy remízků, klenby, sadů, mezí a výhledů) → generátor je postaví. Test `mapa_vyhledu` po trase i na mřížce v obou výškách: dohled > 300 m jen na záznamech `vyhled`. Snímky před a po z týchž bodů.
- **Kamínky:** rádce 19:30 ruší 26. 10. 18:00. Na hřbetu a v kolejích 0, platí KCD a pásma.

## 8. Ves: stromy, sady, zahrádky, vrby (Míša 27. 10. večer, z tabletu 0.97 předběžně)
- **Strom u 1. domu vpravo je moc vysoký.** Lípy, duby a břízy na návsi mají dnes 11–17 m a stojí i u stěny chalupy (`vesnice.village_trees`). Pravidlo do `pasma`: strom u stavby ≤ výška hřebene + 3 m. Vzrostlá lípa jen na návsi (u studny, u kříže), od stěny dál než polovina koruny.
- **Sady:** „sad za chlevem“ dnes tvoří lípa, dub, bříza a keře 4–9 m, tedy žádný sad. Nově u části usedlostí (záznam u domu v `lokace.json` ves: `zahrada: sad | bylinky | zeli`) bude jabloňový sad. 3–8 jabloní v řadách ~6–8 m, nízký kmen 1,2–1,8 m, rozložitá koruna 4–6 m, pod nimi vysoká tráva a pokosená cestička. Model jabloně zatím chybí (Drive ani tvrz-modely ho nemají), proto ho postavím v `listnace.py` stejně jako lípu a dub (kůra + karty listů, pár jablek).
- **Bylinková zahrádka:** u jiných usedlostí za chalupou, ohrazená proutěným plotem (withe_fence). Záhony ~1 × 3 m s pěšinkou, šalvěj, máta, kopr, routa, mateřídouška a měsíček. Karty bylin se dodělají do atlasu `byliny` (dnes jsou v něm jen divoké: divizna, jitrocel, pelyněk, podběl).
- **Vrby u rybníka nepůsobí hezky.** Smuteční vrba (*Salix babylonica*) se do Čech dostala až v novověku, ve 14. století sem nepatří. Proto smuteční vrby (`vesnice.py` 3×, `listnace.willow_mesh`) zruším a místo nich budou vrby hlavaté a olše, které už jsou ve `veg.py`, rozestavené ve skupinách, ne dokola. Hlavaté vrby předtím zkontroluju na snímku zblízka.

## 9. Kopec se skálami (Míša 27. 10.)
- Z kopce se skalním městem je dnes výhled přes celou mapu. Nově bude svah kolem skal a před nimi v hustém lese, buk a smrk s borovicí na skalách, jako na Kokořínsku a v Českém ráji. Koruny 20–25 m zakryjí výhled z paty skal i ze stezky mezi nimi.
- Výhled bude jen z vrcholků skal, které ční nad koruny. V kompozici to jsou záznamy `vyhled` na `SKALY_VRCHOL` (vršek věže > koruna + 2 m) s přístupem po stezce, žebříku nebo zářezu. Test `mapa_vyhledu` hlídá, že jinde na kopci dohled ≤ 300 m.

## 10. Povrch a rostliny podle užívání (Míša 27. 10. večer: „když jsou tam dveře, tak se tam chodí“)
Pravidlo smyslu: povrch a vegetace vzniká z toho, **kudy a jak se místo používá**, ne ze šumu.
- **Dveře → vyšlapaná pěšina** ke skutečnému cíli: ulice nebo cesta, studna, chlév, hnojiště, pec, branka. Záznam `pesiny_odvozene` u každých dveří. Test: dveře bez pěšiny = chyba.
- **Před dveřmi** udusaná hlína (`pasma.budova.dvur_m`), na prahu kámen nebo prkno.
- **Kolem domu** do `pasma.budova.drn_m` jen nízký sešlapaný drn. Vysoká tráva (divoka_trava, grass_medium), kapradí ani keře tam ne.
- **U paty zdi** pruh `pasma.budova.plevel_u_zdi_m` (0,3–0,6 m) s kopřivou, lopuchem a vlaštovičníkem, hlavně na severní a stinné straně a u okapu. Ne před dveřmi a ne na pěšinách.
- **Dvůr** je udusaná hlína. Tráva roste jen v rozích a u plotu (kam se nechodí), stejně u tvrze, hostince, stanu, mlýna a chýší.
- **Trasy chůze mezi body** (dveře ↔ studna ↔ chlév) jsou sešlapané pásy, ne jen konce. Šířka 0,6–0,9 m (Míša: šířka cestiček 0,75).
- **Test smyslu `uzivani`** na posledním exportu: vysoká tráva, keř nebo strom v `drn_m` od zdi nebo na trase chůze = chyba, dveře bez pěšiny = chyba. Podklady jsou pudorysy a dveře (Godot `_domy` a lokace) a osy pěšin.
- Pozor: vegetaci kolem domů ve vsi rozsévá Blender (`vesnice._homestead_green`) podle starého rozložení. Domy pak hra posune (`novy_stred`), takže zeleň u domů musí jít ze stejného záznamu jako dům (C2, export po dílech).
- **Stan kupce** (Míša): stojí v trávě, ale nízké a sešlapané (chodí se kolem, stojí tam zboží a koně). Před vchodem a mezi stanem a cestou je vyšlapaný pás. Vysoká tráva až dál od stanu, kam se nechodí. Stejné pravidlo `uzivani` platí pro stan jako pro dům: `drn_m` od plachty, pěšina od vchodu k cestě (ke_stanu).
- **Stupeň sešlapání podle četnosti chůze** (Míša): každá trasa a plocha má v záznamu `chuze: casto | obcas | zridka`. Z ní vzniká povrch:
  - `casto` = holá hliněná pěšina (dveře → ulice, vchod stanu → cesta, dvůr, studna);
  - `obcas` = nízká sešlapaná tráva s prošlapanými kolejemi (kolem stanu, za chlévem, na mezi);
  - `zridka` = běžná tráva a dál vysoká.

  Hranice mezi stupni je měkká a nepravidelná, ne jako pravítkem. Šířka pásu roste s četností. Čísla pro stupně patří do `pasma.uzivani`, v kódu žádná. Test `uzivani` ověří, že na `casto` není tráva a na `obcas` není vysoká tráva.
- **Zelený rastr kolem záhonů a dvorů** (Míša 27. 10., snímek 0.95 u (381, 725)): čtverce trávy na hlíně bez logiky. Příčiny: (1) maska tráva/hlína v `Teren_ves` je atribut vrcholu po 2 m, takže okraj dělá schody. (2) Tráva je tam, kde podle užívání být nemá: `yard_dirt` + šum. Oprava podle pravidla užívání: kolem záhonu je pěšina (`chuze: casto`), tráva jen v rozích dvora a u plotu. Okraj masky se kreslí v shaderu z jemné masky nebo ze vzdálenosti k záznamu (pěšina, dvůr, záhon), ne z mřížky 2 m. Test smyslu `rastr`: maska trávy podél řezu 0,25 m nesmí skákat ve schodech o rozteči mřížky bez zdroje v datech (záznam okraje).
