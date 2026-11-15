# Rozpory Blender × Godot (soupis 2. 11. večer, Míša: „Blender píše starou vesnici a Godot novou… zkontrolovat, jestli tam a nejen tam nemáme rozpor“)

Soupis ze čtení kódu (svet.gd S, ves_oblouk.gd VO, louka.gd L; blender kraj.py, vesnice.py, export_game.py). Řádky
k 2. 11. Detail každého bodu: místo, co mění, z jakého záznamu, co dělá Blender, proč riziko.

## Hlavní příčina
Blender peče barvu terénu (G), masku trávy a výšky ve STARÉM rozložení vsi (`vesnice.layout`, `ves_paths`, `_pads`).
Godot pak každou z těchto věcí přenáší do nového rámce zvlášť a vlastním pravidlem (`_vo_data`, `_vo_teren`, `_vo_sit`,
`_vo_scena`). Jedna věc tak má dvě nebo tři pravidla.

## Riziko vysoké
1. **Stará náves.**
   - Godot ořízne jen osu cesty (`_vo_stara_naves` S:41, natvrdo obdélník kolem (470, 830)). Barvu G a masku staré návsi
     mimo půdorysy usedlostí nic nepřebarví → holé hnědé pásy bez trsů.
   - `lokace.ves.stred_stare_navsi` existuje, ale nečte se.
2. **Šířka ulice, tři pravidla:**
   - `vo.pulsirka`/`ulice_pas` (barva + maska);
   - `cesta_ok` se šumem ±0,5 m a rozšířením `_cesty_opotrebeni` (hlína v shaderu, trsy, rostliny, ploty, vybavení);
   - `ves_cesta` m<60 (rostliny).
3. **Toky a usedlosti.** Toky na starém místě usedlosti (teď tam tečou) a na novém (netečou): výšku opravuje
   `_breh_toku_y`, barvu ani masku nic.
4. **Krčma natvrdo ve starém rámci.** `CESTA_UDUSANO` (S:6914) je natvrdo (461, 779) = starý střed krčmy. Nová krčma
   (369, 760) udusaný plac nemá.
5. **Stará místa jako louka.** Maska 200 natvrdo, barva louky = průměr prvních 200 vrcholů s g>0,8 (skvrna).
6. **Okraj mřížky.** `trava_ves` končí na x≈350, nový půdorys k=0 sahá na 337 → v pásu nesedí barva a maska (NEOVĚŘENO).
7. **Terén pod domem.** Podstava staré chalupy (`pad_adjust`) + nový dům (`dum_teren`, `DUM_MER` natvrdo) → dvě rovinky
   vedle sebe.
8. **Okraj stavby.**
   - Blender: `_in_building` 1,6 / `okraj_stavby` 1,0–2,2 kolem starého obrysu chalupy.
   - Louka: `_v_budove` prah 0,4 kolem obrysu nového domu.
   - V samotném Blenderu: maska = okraj², barva okraj¹.

## Riziko střední
9. Půdorys usedlosti: okraje v VO:21 opsané natvrdo z `_homestead_green`.
10. `_vo_sit`/`_vo_scena`: díl na hranici půdorysu jede celý, nebo zůstane.
11. `_ves_site_vyrez`: ploty podle `cesta_ok`, ne podle pulsirky.
12. Výška ulice: `uprav_y` (příčně) + `_cesty_profil` (podélně, ±0,25 natvrdo) dvěma pravidly.
13. Terén pod cestou: Blender `flatten`/`road_y` (přechod 6 m) + Godot profil (12 m) → dvojí zářez.
14. Koryto toku: vzorec opsaný z `kraj.voda_tvar` do `koryto_toku_y` (drobné rozdíly smin/max).
15. Hráz rybníka: `kraj._hraz` + `_ryb_hraz_toky`, `ryb_teren` × `ryb_mrizka` záměrně jinak.
16. Terasa (`_terasa_terenu`, natvrdo obdélník): jen ve hře, barva G ani maska se nepřepočítají.
17. Lom: `LOM_Z`/`LESENI_Z` opsané z `plochy.json`, pata se hledá ve hře.
    Brod: Blender 0,12 m, Godot 0,45 m.
18. Vrata: `_teren_pod_vraty` posouvá vrata i terén.
19. Holý břeh toku, tři šířky: `breh_hlina_m` 0,9 / `dno_toku_m` 0,6 / `breh_m` 0,3.
20. `_stare_cesticky`: barva přepsána na louku, maska ne (NEOVĚŘENO).
21. Vybavení se po úpravách terénu znovu neusazuje (kromě posunutých).
22. Díl mlýna: tráva podle G dílu, mimo díl podle masky → šev.

## Riziko nízké
23. `_zamek_terenu`: kontrola, opravuje výšky, ne masku.
24. Druhé vyhloubení Bystřice.
25. Záplaty s barvou natvrdo.
26. `_ves_maska_ulice`: mrtvá větev.
27. Stará zahrada natvrdo.
28. `VES_STARE`: kopie lokace.json natvrdo.
29. `_na_zem`: (470, 830) natvrdo.
30. Rostliny u cest: další použití `cesta_ok`.

## Řešení (návrh): Blender vyváží ves rovnou v novém rámci, Godot nic nepřepisuje
Blender nový rámec už zčásti zná: `kraj._HUMNA` čte `novy_stred`, `nove.NOVY_RAMEC` vyváží zahumenky.
1. **`vesnice.layout()` z `novy_stred`/`novy_yaw`.** `_pads`, `okraj_stavby`, `yard_dirt`, ploty, stodoly, rostliny
   a vybavení se vyvezou na novém místě.
   - Odpadnou `_vo_data`, `_vo_sit`, `_vo_scena`, `_vo_teren`, `VES_STARE`, `_vo_stara_naves`, staré místo jako louka.
   - Řeší body 1, 3, 5, 9, 10, 28, 29.
2. **`ves_paths`/`path_dist` nahradit osou ulice** (`osa_ulice` + `pulsirka` do Pythonu, data v `lokace.ves.ulice`).
   - Barvu i masku pak počítá jedno pravidlo.
   - Godot pro hlínu a trsy bere stejnou šířku (ne `cesta_ok` s rozšířením).
   - Řeší body 2, 11, 26.
3. **Srovnání ulice a podstavu nového domu do `F.land`/`pad_adjust`.** `_zamek_terenu` zůstane jen jako kontrola
   (body 7, 12, 18).
4. **Okraj stavby z obrysu nového domu** v Blenderu i v louce, jeden záznam `pasma.budova` (bod 8).
5. **Terasa, lom a brody jako záznamy** tvarované jen Blenderem, barva a maska podle nich (body 16, 17, 19).
   `CESTA_UDUSANO` z lokace.json (bod 4).

V Godotu zůstane jen vkládání dílů (rybník, mlýn), zářez profilu cest a `_zamek_terenu` jako kontrola.
Postup: po krocích s exportem a snímky před a po (hlídači), každý krok vratný (git + `VES_OBLOUK`).

## Postup (3. 11., Míša „náprav to“)
**Krok 1 – ves v novém rámci z Blenderu** (přepínač `lokace.json ves.blender_novy_ramec`, výchozí false do ověření):
- `blender/ves_ramec.py`: přepis `ves_oblouk.gd` (usedlosti, `presun2`, `osa_ulice`, `pulsirka`, `ulice_pas`).
  Shodu os hlídá test `ves_osa` + `tools/porovnej_osu.py`.
- `vesnice.layout` → `_novy_ramec`: chalupa, stodola a kůlna každé usedlosti na novém místě.
  `ves_paths`/`path_dist` z osy ulice: hlína ulice a odbočky k vratům.
  Mřížka `trava_ves` ±140 m.
- Hra (`svet.VES_BLENDER`): `_vo_jen_ulice` (jen nové domy a srovnání ulice napříč), bez `_vo_sit`, přesunu uzlů,
  přenosu terénu, barvy a masky.
- Odstraňuje body 1, 2 (barva a maska), 3, 5, 6, 9, 10, 28.

Zbývá: krok 2 (srovnání ulice a podstava domu do `F.land`), krok 3 (okraj stavby z obrysu nového domu), krok 4
(terasa, lom, brody, `CESTA_UDUSANO` jako záznamy).

### Stav 3. 11. odpoledne (v kódu, čeká na export `retez_ves1` a ověření)
| # | rozpor | řešení | stav |
|---|---|---|---|
| 1, 3, 5, 6, 9, 10, 28 | přesun vsi ve hře (barva, maska, výška, instance, sítě) | Blender staví ves v novém rámci, hra nepřesouvá (`VES_BLENDER`) | v kódu, zapnuto |
| 2, 11 (část), 26 | šířka a hlína ulice třemi pravidly | `ves_ramec.ulice_pas` v Blenderu pro barvu i masku, hra nepřepočítává | v kódu |
| 12 | srovnání ulice napříč ve hře | `ves_ramec.uprav_y` ve `fort.land` | v kódu |
| 4 | udusaný plac krčmy na starém místě | `svet._krcma_udusano` z lokace | v kódu |
| 7 | placka staré chalupy × podezdívka nového domu | `lokace.json ves.domy_podezdivka` pro Blender placku i `DUM_MER` | v kódu |
| 22 | mlýn: dolina pod hranou dílu | pás napojení patří dílu: tok se v něm prolne do terénu dílu jen v Blenderu, hra pás nepřepisuje | v kódu |
| – | příkop: průhledná hladina | hloubka = max(odhad, hladina − terén) | v kódu |
| – | cesty braly výšku i s plackami budov (zacyklení) | `flatten` bez placek (pořadí terén → cesty → budovy) | v kódu |
| 19 | holý břeh toku třemi šířkami | jedno pásmo `pasma.voda.holy_breh_m` (Blender, louka) | v kódu |
| 20 | `_stare_cesticky` přebarvovaly bez masky | odstraněno (ves staví Blender) | v kódu |
| 21 | vybavení se po úpravách terénu neusazuje | `_vybaveni_nad_zaznam` před úpravami, `_vybaveni_na_teren` po `_zamek_terenu` (do 0,6 m nad zemí drží odstup) | v kódu |
| 14 | koryto: vzorec opsaný ve hře | měření: `koryta toku naposled … nejvic X m` v logu; velký rozdíl mimo cesty = rozešlý vzorec | **naměřeno 3. 11.: 8624 vrcholů, nejvíc 6,00 m u (263, 972) na lhota_odtok**. Blender tam koryto má správně (`fort.land` −6,67, hladina −6,4, `Teren_reka` po načtení −6,59) → přepisuje hra jinou síť terénu (kterou – výpis doplněn); podezření, ne příčina |

Zbývá (stav 15. 11. – tabulka „Stav 15. 11.“ níže): 13 (profil cest dvakrát), 14 (koryto, jiný pomocník),
16 (terasa), 34 (pěšiny), 35 (hrana dílu mlýna). Vyřešeno nebo potvrzeno: 8, 11, 15, 17, 19, 20, 21.

### Stav 15. 11. (zbývající body; `tools/test_smyslu.py` SMYSL souhrn OK)
| # | rozpor | jeden zdroj / proč ne | test | stav |
|---|---|---|---|---|
| 8 | okraj stavby | obrys = `lokace.json ves.domy_podezdivka`: Blender `vesnice._pads` (+ `pasma.budova.placka_okraj_m`) → `okraj_stavby` (barva i maska), hra `DUM_MER` (`_vo_jen_ulice` čte totéž) → `_dum_zabira` + `pasma.budova.prah_m` (louka `_v_budove`). Pásmo prah 0,4 m leží v udusaném okraji Blenderu (placka 0,6 + hlína do 1,0 m) – žádný pás, kde jedno pravidlo trávu má a druhé ne | test smyslu `okraj_stavby`: placka Blenderu = podezdívka domu hry (střed a rozměr do 5 cm) a `okraj_stavby` = 0 v pásmu prah_m – **7 z 7 domů OK** | vyřešeno (data); snímek po exportu jen pro jistotu |
| 11 | ploty podle `cesta_ok` | ploty staví jen Blender (`vesnice.ploty_usedlosti` – jedna funkce pro `build` i test); hra je na hlíně usekne (`_ves_site_vyrez`). Změřeno: nejbližší bod plotu **3,18 m za nejširší obálkou okraje hry** (pulsirka × 1,24 + 0,25 m, čísla čtena ze `svet.gd cesta_ok`) u (442,1; 797,3) – obě pravidla se u plotů nepotkají, `cesta_ok` neměněn (rozbitý okraj hlíny, Míša 0.80) | test smyslu `plot_ulice` (mez 0 m za obálkou) | vyřešeno; po exportu log `ves: … kusu plotu N` – žádný kus u ulice (ostatní jen nízké kusy na odbočkách mimo vrata) |
| 15 | hráz rybníka | rybník Lhota v2 (`voda.json rybnik_lhota.obrys`): dno, břeh, hráz, hladinu i výpusť staví jen Blender (`kraj.ryb2_*`), hra `_ryb_priprav` končí hned („Lhota v2 z Blenderu“), `_ryb_y` = INF → `ryb_teren`/`ryb_mrizka` nic nemění, `_ryb_hraz_toky` se nevolá | test smyslu rybník v2 (voda_bez_hrany, kontrola_vody, vypust, `odtok_za_hrazi`) | vyřešeno v kódu (staré větve jen pro v1) |
| 17 | lom | `LOM_Z` a `LESENI_Z` ve hře teď ze záznamu `plochy.json lom.z` / nový `lom.leseni_z` (dřív konstanty). Patu stěny hra dál hledá v terénu (`lom_stena_x`, na ní stojí stěna, lešení, suť), proto se porovnává se záznamem: hledání hry na terénu Blenderu (`fort.land`) dá `pata_x` + 0,5 m ve všech 26 řezech z 902–977 (změřeno) | Godot `lom_na_zemi`: `LOM_PATA` v logu, mez `lom.pata_steny_tolerance_m` 1,0 m | **čeká export**: rozdíl > 1 m = terasa (#16) posunula stěnu jen ve hře |
| 17 | brod | už jeden záznam: Blender `kraj.voda_tvar` i hra `koryto_toku_y`/`_na_brodu_toku` berou `voda.json toky_tvar.brod_hloubka_m` (0,12) a `cesty.json prechody polomer_m`; 0,45 m už v kódu není | test smyslu `brod` | vyřešeno (potvrzeno čtením) |
| 19 | holý břeh | `pasma.voda.holy_breh_m` v `kraj.py` (barva, stanoviště) i `louka.gd`/`svet.gd` | – | potvrzeno |
| 20 | `_stare_cesticky` | volání odstraněno (`svet.gd` u `_terasa_terenu`: „vypnuto 3. 11.“) | – | potvrzeno |
| 21 | vybavení po úpravách terénu | `_vybaveni_nad_zaznam` (před) a `_vybaveni_na_teren` (po `_zamek_terenu`) volány | – | potvrzeno |
| 13 | profil cest dvakrát | dvě různé operace: Blender `kraj.flatten` srovná terén napříč k výšce osy (jen osy `CESTY`, přechod hw+0,6…hw+6 m natvrdo), hra `_cesty_profil` vyrovná podélně (klouzavý průměr ±10 bodů, sklon ≤ `CESTA_SKLON`·0,8, zářez/násyp ≤ 3 m) a rozprostře `dl` do ok+1…ok+12 m – na všech osách hry, i těch, které Blender nezná (pěšiny → cesty, ulice, `k_vetraku`). Jeden zdroj = podélný profil v Blenderu pro každou osu a hra jen čte `dl`; to vyžaduje osy hry v datech (viz 34) | – | otevřené (rozbor); přesun až s osami pěšin v datech |
| 16 | terasa | `_terasa_terenu` jen ve hře: obdélník `TERASA` natvrdo (x 60–275, z 750–1365, obsahuje i lom), svah 53° ± 5° šumem FastNoise, mění mřížku `trava_kraj` a sítě `Teren*`; masku trávy ve svahu hra počítá (`terasa_maska`), barvu G Blender peče z terénu bez terasy. Jeden zdroj = krok terénu v Blenderu (po lomu, před cestami) + maska `skalni_stena` z exportu; hra krok smaže. Nepřeneseno: změní terén v celém pásu a lom (nutný export + snímky) | nepřímo `lom_na_zemi` (`LOM_PATA`) | otevřené |
| 34 | rostliny nad pěšinou (512, 1139) | bod leží 0,9 m od osy `cesty.json pesiny k_vetraku` (typ vozová, plán astar se sklonem). Výslednou osu pěšin ale tvoří až hra: `_pes_postav` ji zvlní `_pes_o` až o 8 m a odsune od skal Blenderu (kruhy podle skal z exportu) – Blender ji tedy znát nemůže (kruh: osa závisí na skalách Blenderu). Instance rostlin hra po stavbě os odebere (`_cesty_rostliny`, `_pesiny_volne`), ne ale sítě mimo instance (`Rakos`) ani kolize. Jeden zdroj = výslednou osu pěšin počítat v `tools/krok_b` (vlna + skály ze záznamu skal `kraj.skaly_plan`) a zapsat do `cesty.json`; hra bez vlny, Blender `road_near` + rozsev z ní | test `zasazeni` (`v_pasmu_pesina_*`, `nad_cestou_pesina`) | otevřené (rozbor); `k_vetraku` je vozová cesta, a přesto ji hra vlní jako pěšinu – další rozpor |
| 35 | hrana dílu mlýna u výtoku | data sedí (Blender `fort.land` × `_mlyn_teren` 0,02 m), rozdíl 0,16–0,20 m dělá triangulace: síť světa (`Teren_toky` po `toky_tvar.jemny_krok_m`) a síť dílu mají vrcholy jinde ve svahu 0,45 m/m. Jeden zdroj = vrcholy hrany dílu jako vrcholy sítě světa v `kraj._teren_u_vody` (konformní šev); jemnější krok jen zmenší chybu | Godot `dil_okraj` (mez `pasma.dil.okraj_schod_m`) | otevřené (rozbor, změna sítě světa čeká na samostatný krok s exportem) |

### Nové rozpory nalezené 3. 11. večer (testy po exportu ves3)
| # | rozpor | stav |
|---|---|---|
| 31 | barva okraje stavby a hlíny ulice v Blenderu jen do 90 m od starého středu vsi, maska všude → u krčmy tráva bez trsů (test ves_maska 50 bodů) | v kódu: obě pravidla v celé oblasti vsi (±170 m jako `fort.land`) |
| 32 | `koryto_toku_y` ve hře prohlubuje i vlastní terén dílu mlýna – přeskočení pásu dílu ho vypnulo (test mlyn: terén dílu nad hladinou) | v kódu: parametr `i_v_pasu_dilu` pro terén dílu |
| 33 | plácek před chýšemi u lomu odsazený o průčelí + okap 1,2 m, střecha chýše sahá 4,8 m → střecha nad pěšinou (test zasazeni, dlouhodobě) | v kódu: odstup od předku střechy `DUM_MER ft` |
| 34 | rostliny a rákos z Blenderu neznají pěšiny (Blender `road_near` jen cesty z `CESTY`) – srážky nad pěšinou (512, 1139) | otevřené – rozbor 15. 11. v tabulce „Stav 15. 11.“ |
| 35 | okraj dílu mlýna u výtoku: test dil_okraj 2 z 299 bodů 0,16–0,20 m (589, 899), (585, 904) | Blender data sedí na 0,02 m (`fort.land` × `_mlyn_teren`); rozdíl je v sítích: hrana leží ve svahu stěny výtoku (0,45 m/m), síť dílu a síť světa ho trojúhelníkují jinak; bod 2 svět ve hře o 0,11 m níž než `fort.land` – rozlišení sítě světa u hrany dílu | otevřené (měřeno) – rozbor 15. 11. v tabulce „Stav 15. 11.“ |

### Rozpory vody nalezené 9. 11. (pomocník vody, Míša ř. 51/53/61/79 „kolikrát jsme to řešili“)
| # | rozpor | stav |
|---|---|---|
| 36 | odtoky rybníků naplánované po terénu bez rybníků (voda_sit/odtok_mimo_ves): lhota_odtok začínal uprostřed hráze 1,56 m pod hladinou a 16 m vedl podél ní, tvrz_odtok 0,3 m od osy hráze 1,34 m pod hladinou; Blender (`voda_tvar` výpust) i hra (`_ryb_hraz_toky`) pak hráz prorazily korytem i dolinou → díra v hrázi, hladina visela 1–2 m nad terénem, „hliněný sráz“ (08) | data: `tools/krok_b/odtok_za_hrazi.py --zapis` (osa začíná za vzdušnou patou), hráz se nikde nepřerušuje (kraj.py, svet.gd); test smyslu `odtok_za_hrazi` |
| 37 | hladina rybníka tvrze = pevný mnohoúhelník `ryb_polomer + presah` bez ohledu na terén → přes korunu hráze na vzdušný svah | `kraj.ryb_hladina_r` (vrstevnice terénu), test smyslu `breh_nadrze`, hra `breh_nadrzi` |
| 38 | díl Lhota má pevný okraj +0,30 a leží ve svahu (svět na hraně −2…+4 m); hra stahovala svět v pásu 6 m na okraj (srázy 30–35°), model holý pás do +0,2 m (3–4 m), louka bez trsů do +0,4 m nad hladinou | hra: břeh dílu podle pravidla `voda.json rybnik_lhota.breh` (model jen 2 m od vody, dál svět omezený svahem), hrana dílu = svět, tráva a bahno podle vzdálenosti od vody (`svet.ryb_od_vody`) |
