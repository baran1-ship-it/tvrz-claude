# Míša 28. 10. – chyby z tabletu (0.97) → pravidlo + kontrola v testu

Míša: „Nelep jen díry, chce to podle tabulek, ať to má smysl.“ Každý řádek = příčina v datech/pravidlu,
oprava v jednom místě (tabulka nebo generátor) a nová kontrola v testu smyslu / zasazení. Ne výjimka v kódu.

| # | Co Míša viděla (místo) | Příčina (zjištěno) | Pravidlo / tabulka | Kontrola v testu | Stav |
|---|---|---|---|---|---|
| 1 | Bílé pásy místo vody: odtok rybníka, náhon a lednice mlýna (484,875; 339,888; 535,889) | `kraj.toky_voda` nedávala barvy proudu; shader `voda` (tekoucí) čte R jako pěnu, export dal R≈0,9 → celá hladina pěna | hladina toku má barvy proudu jako Bystřice (R pěna, G peřej, B/A směr) – `kraj._toky_proud` | test smyslu --po: tekoucí hladina s průměrnou pěnou > 0,3 = chyba | opraveno v generátoru, čeká export |
| 2 | Řeka skoro bez vody, lom (189,922) „zničený“ hlubokým zářezem | na tabletu starý balík z_reka (27. 10. 11:23, před přesunem Bystřice): hra schovala hladinu z exportu a kreslila starou; brod u lomu bral dno podle staré hladiny (−8,3 místo −4,5) → vykopal 4 m zářez přes lom | předpečený potok jen se stejným `reka_otisk` (svet.json z exportu = reka.json z pečení); dno brodu podle viditelné vody jen do `pasma.test.brod_odchylka_max_m` | hra: nesedící otisk → voda z exportu; brod mimo odchylku = varování | opraveno v kódu (hra), otisk zapíše příští export |
| 3 | Potůčky k mlýnu, odtok a nový rybník bez koryta a břehů, „voda v trávě“ | terén okolí má síť po 5 m (ves 2 m) – koryto 1–1,5 m v ní neexistuje, hladina zahrabaná; břehový povrch (hlína, štěrk) měla jen Bystřice | `toky_tvar.pas_jemny_m` (jemný terén 1 m u všech toků a rybníků, `kraj._teren_u_vody`), `toky_tvar.breh_hlina_m` (holá hlína a štěrk u vody) | (doplnit) test smyslu: dno toku pod hladinou ve výsledné síti | opraveno v generátoru, čeká export |
| 4+5 | Tráva a strom v hostinci, ve vratech a vstupech, v záhonech, strom na cestě | export rostlin (Blender) neznal nové záhony, průchody ani obrysy staveb hry; vstup exportu je nehlídal | jedno pravidlo užívání `svet.uzivani_smi` (záhon, průchod `pasma.budova.pruchod_m`, vnitřek stavby, hlína cesty podle `odstup_cesty`) v `druh_smi_hra` → rozsev, vstup exportu i louka | test smyslu/zasazení používají `druh_smi_hra` | opraveno v kódu |
| 6 | Hnědá kláda přes cestu a plot (454,842) | lano studny: kotva lana (světové souřadnice) se při posunu usedlosti neposunula, lano vedlo z původního místa | posun kotev `ropes`/`chains` s usedlostí | (doplnit) délka lana do hloubky studny | opraveno v kódu, ověřit snímkem |
| 7 | Hřiby létají a obří (504,901) | houby pod každým 10. stromem i ve vsi, síť bez měřítka uzlu modelu, paprsek na první kolizi (střecha, kmen) | `druhy.json` skupina houba (les_min, pod_stromy, od_kmene_m); model s transformací uzlu; jen zásah u výšky terénu | | opraveno v kódu |
| 8 | Hranice dřeva s černými plochami (331,902), „hřib“ u mlýna (346,909) | doplňky modelu mlýna (Mlyn_Doplnky) | viz 11 | | opraveno (pryč) |
| 9 | Z kopce dohled „až do nevidim“ (−137,576) – mělo být plné, krátký dohled | kompozice výhledů (rádce 26. 10. 19:28–19:29, krok C) nedotažena | výhled ze skalního města **zůstává** (Míša 28. 10.); ostatní místa zavřít remízky, lesem, terénem (záznamy `lokace.json kompozice`, zábrana ≥ 3 m) | test `mapa_vyhledu` | po vodě |
| 10 | Do mlýna se nedá dostat, dveře nefungují | systém dveří (pohyb.gd) hledá křídla jen pod uzlem Tvrz, mlýn je samostatný díl | dveře mlýna jako dveře domů (záznam pohybu), `voda.json mlyn.dil.dvere_otevrene` | | opraveno v kódu |
| 11 | Venku u mlýna dřevo, špalek, pytle z modelu – pryč, dáme svoje | | `mlyn.dil.vynechat_uzly` = Mlyn_Dvur (dvůr vedle budovy; Mlyn_Doplnky je u a v budově) | | opraveno v kódu |
| 12 | Spustit kolo a mletí | kolo se točilo pořád | `mlyn.dil.ovladani`: páka stavidla ve mlýnici (rozjezd 4 s), mletí u kamene jen v chodu: pytel obilí → pytel mouky | | hotovo v kódu |
| 13 | Bystřice bez vody, kameny levitují, tráva pod mostem v řece | viz 2 (starý balík řeky); louka neznala koryto pod hladinou | louka: v korytu a holém břehu (`pasma.voda.breh_m`) žádná tráva, i u malých toků | | opraveno v kódu |
| 14 | Cesta na most vede pod ním | zjišťuji (most (234,601), odbočka do vsi) | | | |
| 15 | Příkop málo vody | hladina −2,75 | `voda.json prikop.hladina_y` −2,0 (0,4 m pod nejnižším hřebenem valu −1,6) | | čeká export |
| 16 | Lom nemá skálu, stěna nízká | lom neměl v datech vlastní tvar - hra stavěla stěnu z náhodného srazu v kopci a údolí Bystřice (krok B) ho zarovnalo; výjimky ze srážení svahů natvrdo v kódu | `plochy.json lom` (pata, dno, rozsah) → `kraj.lom_tvar` v pořadí po stavbách; výjimky `teren.bez_srazeni` | test smyslu `lom`: stěna ≥ `stena_min_m` (na starém tvaru 11 míst pod 6 m) | čeká export |
| 17 | Stůl před hostincem na hlíně cesty (test zasazení, (−56, 925)) | třetí stůl (bx 7,4) natvrdo v kódu, cesta k_hostinci přichází z té strany | `lokace.json hostinec.stoly_venku` (jen strana bez cesty) | test smyslu `stul`: stůl venku na hlíně cesty | čeká export |
| 18 | Ruce na žebříku | tělo se při lezení skrývalo | tělo vidět, obě ruce IK na příčle střídavě (`jizda.json telo.lezeni`) | | v kódu |
| 19 | Test zasazení po exportu: ulice napříč nad potokem, dům 7 nad terénem, schody nad pěšinou, střecha chýše nad plácem | nový jemný terén u toků se neposouval s vsí; dům 7 si při přesunu odnesl koryto ze starého místa; pěšina od zdi pod schody; plácek od zdi pod okap | Teren_toky v `_vo_teren`; zdroj v korytu = výška břehu (`_breh_toku_y`); `pasma.budova.schody_m`, `okap_m` | test zasazení (17 → 13 → ověřuje se) | v kódu |
| 20 | Bystřice bez vody | předpečená řeka vypnutá (stará trasa) | upečena znovu pro novou trasu, otisk sedí | snímek: voda, pěna, břehy | hotovo |

## Hlášení k 0.98 (Míša 28. 10. odpoledne, tablet)

| # | Co Míša viděla (místo) | Příčina (zjištěno) | Pravidlo / tabulka | Kontrola v testu | Stav |
|---|---|---|---|---|---|
| 21 | Kůň v zemi (4,45; 1,223) | kolize kone = kvádr 0,65–1,65 m nad kopyty, na zemi stojí kvádr → kopyta 0,65 m pod terénem | kolize nohou od kopyt (`jizda.json kun.kolize`) | snímek kone: kopyta na terénu | zjišťuji |
| 22 | Jezdec sedí na zadku, ne za kohoutkem | sedlo = střed modelu + 0,15 m vzad, střed modelu není u kohoutku | sedlo z kostry (kost kohoutku) + `sedlo_vzad_m` | snímek z kone | zjišťuji |
| 23 | Při jízdě žádný pohyb | | | | zjišťuji |
| 24 | Po sesednutí nejde odejít (jen znovu nasednout / mapa); totéž žebříky v lomu | | | | zjišťuji |
| 25 | Voda všude katastrofa: toky jako ploché pásy nad terénem a ve svahu, schodovité okraje po 1 m, kameny jako jehlany, tmavé mnohoúhelníky; příkop | | | | zjišťuji |
| 26 | Mlýn: voda neteče po kole, po stavidle nemele | | | | zjišťuji |
| 27 | Stromy a keře ve vstupech a na cestě (ves), rostlina na cestě | | | | zjišťuji |
| 28 | Dlouhá hnědá tyč přes cestu / šikmo (439,844; 460,850; 442,879) | | | | zjišťuji |
| 29 | Černá vrata, vrata v jámě (422,898), šedé ploché obdélníky u domu (460,850) | | | | zjišťuji |
| 30 | Bříza se zeleným spodkem kmene (439,826) | | | | zjišťuji |
| 31 | Sekání (FPS 18–25 ve vsi) | | | | zjišťuji |

### Detail fotek 0.98 (každá zvlášť)
- (4,45) kůň stojí, kopyta a spodek nohou zapadlé v terénu; bez sedla.
- (0,141) z koně: kamera daleko vzadu – vidím celý dlouhý krk a hřbet před sebou (sedím na zádi); hříva jako tmavé průhledné pruhy, srst pixelovaná.
- (1,223) a detail: volný kůň má přední i zadní nohy zlomené pod sebou, trup u země – úsek animace „pastva/rozhlížení“ je ve skutečnosti lehnutí, nebo nohy v zemi.
- (390,760) cestička k vratům zarostlá trsy trávy.
- (421,792) vrata černá (bez světla), trs trávy přímo ve vjezdu.
- (437,795) okraj cestičky zubatý po čtvercích (hranatá hlína v trávě).
- (443,806) velký dub stojí kmenem na okraji cesty.
- (439,826) bříza: kmen nahoře bílý, dole plochý zelený kus; bílá bylina na cestě; tenké tmavé čáry (dráty?) vodorovně přes pohled.
- (439,844) dlouhá hladká hnědá tyč vodorovně ~1 m nad cestou přes celý obraz.
- (460,850) šikmý hnědý trám u plotu; šedý plochý obdélník u dveří domu (hladina toku bez vody/materiálu?).
- (442,879) shora: hnědá tyč z domu přes koryto na cestu; tok obtéká dvůr, záhony hned u koryta.
- (481,893) tok = plochý pás na světle zeleném holém břehu, pás končí uprostřed, tmavé mnohoúhelníky.
- (508,867) tok podél svahu, kameny jako jehlany trčí z vody, valouny nad zemí.
- (528,882) přítok rybníka = rovný tmavý pás přes zelenou plochu, u rybníka tmavý mnohoúhelník.
- (422,898) vrata v jámě – terén kolem vrat a plotu nahrnutý do valů, vrata černá.
- (418,859) koryto se zubatými okraji po 1 m, suché štěrkové dno, uprostřed modrý kus hladiny; hnědý plochý balvan.
- (380,866) koryto přes cestu bez vody a s trávou, voda pokračuje až za cestou.
- Mlýn (332,901): žlab nad kolem suchý, na kolo nic neteče; (338,903) u kamene „Kámen stojí – nejdřív pusť vodu“ i po stavidle; pytle obilí jako bílé hroudy.
- (353,892) tok končí na pěšině, pěšina leží přes koryto.
- (317,895) tok s ostrým pravoúhlým lomem.
- Příkop (−4,28): pod hladinou vidět travnatý svah, hladina má rovné ostré hrany; (−9,27) u mostu hladina končí rovnou hranou uprostřed příkopu – příkop není plný.
- Rybníky (−118,−172), (−145,−202): hladina mléčně bílá jako led, bez odrazu; tok vedle koryta, ne v něm; (−171,−174) ústí toku do rybníka hlubokou jámou.
- Sekání: FPS 18–25 ve vsi, záseky stovky, jeden snímek 2851 ms u (422,886).
