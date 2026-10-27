# Soupis čísel a pravidel – scripts/svet.gd ř. 1–3600 (díl A)

Zdroj: `scripts/svet.gd` (10 721 ř.), čteny ř. 1–3607. Jen čteno, nic v repu neměněno. Souřadnice v metrech (x, z) světa; barvy lineárně, pokud není řečeno jinak.
Konstanty definované mimo rozsah, na které díl A odkazuje: `LOM_Z=(906,975)` ř. 8951, `LESENI_Z=(911,950.5)` ř. 8953, `NASTOJATO` ř. 8952, `NA_BODECH` ř. 9360, `TRZISTE=false`, `TRZ_O/TRZ_U/TRZ_R` ř. 8995–8999, `RYB_C=(525.08,879.45)` ř. 7571, `RYBNIK_DIL` ř. 7570, `PESINY` ř. 8093, `PES_SIRKA` ř. 8121, `VES_DOMY`/`VES_STARE` ř. 4708–4711.

## Cesty, pěšiny, mosty a nájezdy

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:209-219 | prah 0.005 m | ulice napric rovna (vo.uprav_y) – mrizka kolem ulice srovnana | _vo_data | 1 |
| svet.gd:224-227 | na_ulici(0.92); cil = RYB_C + smer*27 m; mezibody lerp 0.35 +(4,-3), 0.7 +(-2,4); PES_SIRKA 1.1 m | pesina od konce ulice k rybniku (27 m od stredu rybnika), sirka 1,1 m | _vo_data | 1 |
| svet.gd:390-394 | prah 0.005 m | ulice napric rovna i v siti terenu (Teren_ves) | _vo_teren | 1 |
| svet.gd:456-458 | Teren_cesta_kamen skryt | tmave kocici hlavy pres cestu s ostrou hranou zrusene (Misa 17.10.) – pod nimi cesta | build | 2/4 |
| svet.gd:1290 | CESTICKY_PRYC Rect2(-90,24,170,126) = x -90..80, z 24..150 | stare cesticky pred branou zapecene v barve vrcholu -> louka | _stare_cesticky | 1/2 |
| svet.gd:1297 | Teren_cesta*, Teren_obzor vynechany | hlavni cesta se nezazeleni | _stare_cesticky | 2 |
| svet.gd:1315-1320 | okraj 4 m plynule; COLOR.g -> 0.85 | kanal g barvy vrcholu = louka (>=0,85) | _stare_cesticky | 2 |
| svet.gd:2291 | NAJEZD_DELKA 14 m | najezd mostu: teren zvednut k mostovce a do 14 m plynule zpet | _najezdy_mostu, najezd_y | 1 |
| svet.gd:2311-2323 | mostovka: histogram vysek po 5 cm v pasu 35 %..(max-0.6 m), +0.05 m | vyska mostovky | _najezdy_mostu | 1 |
| svet.gd:2328 | deck: \|y - y_most\| < 0.5 m | vrcholy mostovky pro osu | _najezdy_mostu | 1 |
| svet.gd:2351-2352 | najezd na obou koncich mostovky (osa z kovariance) | dva najezdy mostu | _najezdy_mostu | 1 |
| svet.gd:2355 | Teren_obzor vynechan | najezd se nepropisuje do obzoru | _najezdy_mostu | 2 |
| svet.gd:2366 | sirka najezdu = pul sirky mostovky + 0.3 m | siroky plny najezd | najezd_y | 1 |
| svet.gd:2367-2373 | bok 9 m plynule (smoothstep^2) | pozvolny bok najezdu (driv 3 m = strmina) | najezd_y | 1 |
| svet.gd:2370 | cil = mostovka - 0.08 m | teren najezdu tesne pod prkny | najezd_y | 1 |
| svet.gd:2375-2382 | za koncem mostovky (al < -1.5 m) nasyp 1:1.25 (0.8 m/m); ne do vody (sirka hladiny + 1 m) | svah naspu pod mostem, hladina souvisla | najezd_y | 1 |
| svet.gd:2383-2384 | jen zvednout (ny > y) | najezd teren nikdy nesnizi | najezd_y | 1 |
| svet.gd:2402 | prah 0.01 m | posun vrcholu siti terenu najezdem | _najezd_sit | 2 |
| svet.gd:2538-2539 | pesina volna: tvrde do 1.2 m od osy pryc; kameni na kraji (0.8-1.5 m) a mekke zustavaji | odstup tvrdych veci od pesiny | _pesiny_volne | 1 |

## Terén

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:168 | louka_m = 200 | kod masky trava_ves pro louku (stara mista usedlosti zatravnit) | _vo_data | 2 |
| svet.gd:178,186,202 | vysky v mrizce trava_ves s16 /100 (cm), clamp +-32000 | presnost vysek mrizky 1 cm | _vo_data | 2 |
| svet.gd:197 | vaha > 0.5 | maska travy prevzata ze zdroje usedlosti, pod 0,5 a ve starem pudorysu = louka | _vo_data | 2 |
| svet.gd:341 | mrizka 1 m (round x,z) | vzorkovani zdroje vysek/barev terenu po 1 m | _vo_teren | 2 |
| svet.gd:348 | cl.g > 0.8, stara(...,3.0)<0, max 200 vzorku | barva louky = prumer vrcholu s g>0,8 mimo pudorys (okraj 3 m) | _vo_teren | 2 |
| svet.gd:354 | hledani 0..2 m | nejblizsi zdrojovy vrchol do 2 m | _vo_teren | 2 |
| svet.gd:1110 | TERASA Rect2(60,750,215,615) = x 60-275, z 750-1365 | oblast terasy (kolmy schod vyskove mapy 7-36 m) | _terasa_terenu, terasa_svah | 1/2 |
| svet.gd:1145 | W = 8 bunek | okoli hran schodu, ktere se upravuje | _terasa_terenu | 2 |
| svet.gd:1153 | hrana: \|dh\|>=3 m a \|dh\|/k >= 1.2 | detekce schodu v mrizce trava_kraj | _terasa_terenu | 2 |
| svet.gd:1163-1168 | sum seed 1108 freq 0.08 (uhel po 10-15 m); seed 1109 freq 0.3 (profil 2-4 m) | nepravidelnost svahu terasy | _terasa_terenu | 2 |
| svet.gd:1175 | uhel svahu 53 +- 5 st. (s = 2 tan uhlu) | sklon svahu terasy 48-58 st. | _terasa_terenu | 1/2 |
| svet.gd:1198-1205 | prah zmeny 0.05 m; vyhlazeni 3x3 lerp 0.6; sum profilu zm*0.25 max 0.9 m | zaobleni hrany a paty, sum jen ve svahu | _terasa_terenu | 2 |
| svet.gd:1242 | Teren_obzor, Teren_cesta_kamen vynechany | neposouvaji se terasou | _terasa_terenu | 2 |
| svet.gd:1261 | prah 0.01 m | posun vrcholu siti terenu dle zmeny mrizky | _terasa_terenu | 2 |
| svet.gd:1408-1414 | vsechny Teren* krome Teren_obzor, Teren_cesta_kamen: koryto.vyhloub + nadrz.vyhloub | vyhloubeni koryta potoka a nadrzi do siti terenu | _koryto_terenu | 1/2 |
| svet.gd:1415-1422 | poradi: _najezdy_mostu -> _teren_pod_vraty -> _upravy_terenu -> _cesty_tvar | poradi uprav terenu po korytu | _koryto_terenu | 1 |
| svet.gd:1423-1445 | mrizka trava_kraj (2 m): y = min(strop koryta, strop nadrze), max(podlaha), najezd_y, uprava_y, dum_teren, ryb_mrizka; prah 0.005 | poradi skladani vysky louky/rostlin | _koryto_terenu | 1/2 |
| svet.gd:1446-1461 | mrizka trava_ves (jemnejsi): dum_teren + ryb_mrizka | pod dilem rybnika a domy vyska mrizky vsi | _koryto_terenu | 1/2 |
| svet.gd:1612-1651 | pas koryta +-22 m, bunky 1 m, 4 paprsky +-0.25 m; dira = nic nebo zasah < min(vyska, strop) - 0.8 m (krome Teren_reka/most); zaplata 1,5 m (rezerva 0.25) o 0.03 m niz, COLOR g 0.85 | zaplaty der v terenu podel potoka | _zaplaty | 1/2 |
| svet.gd:3516-3532 | mrizka Teren_obzor 25 m | vysky obzoru | _obzor_les | 2 |

## Ves / budovy

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:36 | VES_OBLOUK = not env TVRZ_VES_RADA | ves v oblouku (nova ulice) je vychozi; rovna rada jen pres promennou prostredi | _vo_data, _vo_scena, zem shader ves_rovna | 1 |
| svet.gd:42-47 | stara naves: stred (470,830), osa u=(0.76193,0.64764), u -88..80, \|v\|<=45, od_ulice>14 m | bod stare navsi (puvodni rovna osa), mimo novou ulici | _vo_stara_naves | 1 |
| svet.gd:67-87 | 24 bodu obvodu usedlosti | vyskovy posun usedlosti = prumer terenu na novem minus starem obvodu (dy) | _vo_data | 1 |
| svet.gd:107 | vo.nova(p, 0.5) | rostlina ve starem pudorysu presunuta; rostlina v novem pudorysu (okraj 0,5 m) odjinud se maze | _vo_data | 1 |
| svet.gd:126 | vo.nova(...,0.0) a \|x-470\|<200 | kolize stare navsi/louky v novem dvore pryc | _vo_data | 1 |
| svet.gd:250 | bb > 40 m | samostatne uzly vetsi nez 40 m se nepresouvaji s usedlosti | _vo_scena | 1 |
| svet.gd:287 | vo.stara(c, 0.5) | trojuhelnik site vsi patri usedlosti s okrajem 0,5 m | _vo_sit | 1 |
| svet.gd:459-460 | *_zahrady -> _bez_zeli | zahrady bez zeli | build | 1 |
| svet.gd:1480 | okno Teren_ves x 400..560, z 760..900 | vrcholy terenu vsi pro vysky pod kridly vrat | _teren_pod_vraty | 1 |
| svet.gd:1482-1505 | Pohyb_ves_* s branka/vrata: polomer = pul AABB + 0.6 m; kridlo nejvys 0.02 m nad nejnizsim vrcholem; bod = spodek - 0.03 | kridlo vrat spusteno na teren (Misa 0.72 kopecek zrusen) | _teren_pod_vraty | 1 |
| svet.gd:1523-1527 | d < 1.3 m od kridla, teren > bod+0.05 -> srovnat | zarez terenu pod kridlem (otevreni nezajede do zeme) | _teren_pod_vraty | 1/2 |
| svet.gd:3118-3122 | zeli: 30 % salat, jinak zeli_hlavka; y = teren - 0.05; meritko 0.8-1.15; s VES_DOMY stara mista smazana | zahony ve vsi (nove domy maji vlastni zahony) | _lom_vybaveni | 1 |

## Lom (ručně umístěné vybavení)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:3016-3019 | usporadani lomu dle KCD lom u Talmberka: u steny osyp a leseni, rada pristresku a stanu, sklad kvadru, vozy, ujezdena plocha, tabor, drevo na severu | pravidlo rozvrzeni lomu | _lom_vybaveni | 1 |
| svet.gd:3021-3045 | polozky [id, odstup od paty steny m, z, natoceni]: stan_jehlan 9/916; pristresek_plachta 8/928, 8/970; pristresek_maly 8.5/940; pracoviste u 6.8-9.6 m z 926-930 a 939-941; sklad 7-8.8 m z 969-971; tabor ohniste 15.5/917, lavice 15.5/915, 17.6/917.2, kosik, sud 13.2/914.6, koryto_kone 19.5/921; drevo 4.5-16.5 m z ~908-909.5; zebrinak 20.5/930, 20.8/943.5, 14.5/952.5; trakar 5.2/924, 12/938.5, 4.6/961.5; jerab_slapaci 6.5/956; drevo_vysoka_1 2.6/961; zebrik 4.6/949.6; lopata 5.4/950.6; krumpac 3.5/952 (a 9.6/941.2) | rucne umistene vybaveni lomu (odstupy od paty steny) | _lom_vybaveni | 1 |
| svet.gd:3046-3048 | normala steny z rozdilu +-3 m | predmety natoceny podle odklonu steny | _lom_vybaveni | 1 |
| svet.gd:3057 | vychozi rozmer predmetu [0.6,0.6,0.6] m (modely/predmety.json) | pudorys pro patu na terenu | _lom_vybaveni | 1 |
| svet.gd:3060-3067 | NA_BODECH -> polozit_na_body (opory); NASTOJATO -> orient 3 (naplocho) | vozy/napajedlo/trakar na kola a nohy; krumpac naplocho | _lom_vybaveni | 1 |
| svet.gd:3070 | zabrano: polomer = max(rozmer x,z)/2 + 0.15 m | plocha zabrana predmety lomu (pro sut) | _lom_vybaveni | 1 |
| svet.gd:3074-3077 | seed 949; useky leseni [leseni_lom_3 7.5 m, leseni_lom_2 12.5, leseni_lom 10, leseni_lom_3 7.5] od LESENI_Z.x, mezera 0.4 m | leseni podel lamane casti steny, ruzne vysoke | _lom_vybaveni | 1 |
| svet.gd:3089-3091 | pivot vychozi [0,0.4,0.06]; zad = 1.6 - pivot.z; odstup 0.35 m od steny | zadni rada leseni 0,35 m od steny | _lom_vybaveni | 1 |
| svet.gd:3094-3096 | vyska leseni = min 7 bodu (vpredu i vzadu) | pata leseni na nejnizsim bode | _lom_vybaveni | 1 |
| svet.gd:3098 | _leseni_rect: odstup + 2.0 m | pas leseni (zabrany pro sut/vegetaci) | _lom_vybaveni | 1 |
| svet.gd:3075,3101-3108 | naradi na leseni: kladivo_kamenicke, palice, krumpac, vedro, kvadr_hruby_3, kosik, lopata; 35 % mist prazdnych; max 2 kvadry na usek | naradi a kvadry na podlahach leseni | _lom_vybaveni | 1 |

## Voda

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:454-455 | Reka_voda skryta, kdyz existuje modely/reka/reka.res | potok kresli Waterways (_reka), mrizkova hladina pryc | build | 2 |
| svet.gd:463-465 | Most_potok -> _most_kuly, _most_podlozka | most pres potok: kuly a podlozka | build | 1 |
| svet.gd:806-813 | rybnik: tekouci -> okrehek 0/1, kalnost 0.35 (potok)/0.82 (rybnik), zakal (0.1,0.11,0.07)/(0.13,0.16,0.10), deep (0.08,0.115,0.08) | rybnik s okrehkem kalny, potok cisty | material rybnik | 2/4 |
| svet.gd:838-850 | prikop: deep (0.08,0.115,0.08), zakal (0.13,0.16,0.11), kalnost 0.82 | zelenohneda hladina prikopu | material voda | 2/4 |
| svet.gd:18,430 | water_y -2.75 (vychozi; svet.json voda_y) | vyska hladiny prikopu | build | 2 |
| svet.gd:25 | VRSTVA_VODA 1<<19 | vrstva Area3D hladin (hrac stoji ve vode) | _hladina | 3 |
| svet.gd:934 | hladina < 3 m -> bez oblasti | male nadoby nemaji Area3D vody | _hladina | 3 |
| svet.gd:937-939 | Area3D vrstva VRSTVA_VODA, maska 0, trimesh | hladina jako oblast, ne kolize | _hladina | 3 |
| svet.gd:950-977 | potok reka.res/reka.json, flow_speed 0.3, normal_scale 0.6, roughness 0.15, foam_amount 1.2, foam_color (0.7,0.72,0.66,0.6) | shader potoka (Waterways) | _reka | 2/4 |
| svet.gd:967-970 | melka (0.24,0.27,0.15), hluboka (0.06,0.08,0.05), hloubka_barvy 1.4, cirost 0.55 | barvy potoka lin.; mela voda pruhledna, dno videt | _reka | 2/4 |
| svet.gd:984,988-1000 | kameny_toku Vector4(x,z,polomer,uhel); 12 nejblizsich do 60 m (d^2<3600) | kameny ve vode do shaderu potoka (cereni a pena) | kameny_toku_k | 2 |
| svet.gd:1006-1103 | dira pod mostem ~5x7 m (x -2.5..2.5, z 19..26); hledani podel z 22.5, x +-8, z 14..32, krok 0.1; vyber troj. z>12, \|x\|<12 | zaplata hladiny prikopu pod padacim mostem mrizkou 0,5 m, presah 0,05 m | _prikop_zaplata | 1/2 |
| svet.gd:1344-1359 | voda_prikop / voda, hladina > 5x5 m | nadrze (rybnik a prikop) se stojatou vodou | _koryto_terenu | 1/2 |
| svet.gd:1363-1376 | RYBNIK_DIL: navesni rybnicek (kruh) skryt, nadrz vyrazena | misto nej dil z modely/rybnik | _koryto_terenu | 1 |
| svet.gd:1377-1397 | nadrz s kruhem -> nova_hladina (oval z vesnice.py), puvodni ctverec pruhledny | prirozeny tvar hladiny | _koryto_terenu | 2 |
| svet.gd:1405-1407 | Teren_reka, Teren_most: koryto.pokryj | jemne site potoka a mostu pokryji koryto | _koryto_terenu | 1/2 |
| svet.gd:1708 | kul: vyska > 0.5 m (komentar 1 m) a > 2x sirka | svisle kuly mostu (kura) | _most_kuly | 1 |
| svet.gd:1712-1718 | teren min v kriz +-0.3 m; pata = teren - 0.5 m; prodlouzit jen kdyz pata < spodek - 0.05 | kuly mostu zapustene 0,5 m do dna koryta, UV protazeno | _most_kuly | 1 |
| svet.gd:1796-1816 | hloubka pecena COLOR.r*4 m; paprsek +3/-40 m; dno do 1.5 m; tune pec > 1.2 -> max 4 m; jinak visici = 0 | kontrola a prepocet hloubky hladiny potoka | _kontrola_hladiny | 2 |
| svet.gd:1814 | prah 0.03 m | prepocet hloubky ve vrcholu | _kontrola_hladiny | 2 |
| svet.gd:1854-1884 | Most_podlozka: convex hull prken, y0+0.005, albedo (0.05,0.04,0.03), rough 1.0, stin OFF | tmava deska pod mezerami 1,5 cm v mostovce (proti blikani) | _most_podlozka_deska | 1/4 |

## Vegetace a rozsev

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:21 | SBER: nettle_plant->kopriva, celandine_01->vlastovicnik, periwinkle_plant->barvinek | rostliny ke sberu, kazda instance sberne misto | _plants/sber | 1 |
| svet.gd:9 | BUNKA 24 m | velikost bunky MultiMesh rostlin | _plants | 3 |
| svet.gd:1210-1223 | sklon gr > 0.84 (tan 40 st.) | maska svahu terasy = stanoviste skalni_stena: bez travy a trsu | _terasa_terenu, terasa_svah | 1/2 |
| svet.gd:1553-1571 | *_zahrady: trojuhelniky < 12 m, bunky 1 m | zahradky ve vsi: louka tam netrsuje | _zahrady_tab, v_zahrade | 1 |
| svet.gd:1574-1578 | stara zahrada vyriznuta, kdyz jsou nove domy | bunka bez travy jen u nove zahrady | v_zahrade | 1 |
| svet.gd:1586-1597 | okruh 20 m (d^2 400); zahon \|dx\|<0.68, \|dz\|<1.62 m -> 2; jinak v obdelniku -> 1 | nove zahrady: 2 pod zahonem bez travy, 1 mezi zahony nizka seslapana trava, 0 jinde | v_nove_zahrade | 1/2 |
| svet.gd:1998-1999 | nadvori tvrze \|x+4.5\|<24, \|z-0.4\|<19 (x -28.5..19.5, z -18.6..19.4) | uvnitr hradeb se rostliny neusazuji (vlastni teren) | _na_zem | 1 |
| svet.gd:2001-2004 | okoli tvrze: \|(x+4, z)\| < 75 m -> vyska ze site terenu (_vyska_sit) | val a prikop mrizka nezna | _na_zem | 1/2 |
| svet.gd:2010-2011 | tolerance: ter-1.0 < y < ter+0.25 nechat | rostliny jen mirne mimo teren se nehybou | _na_zem | 1 |
| svet.gd:2023 | ladeni: tvrz < 80 m od (-4,0), ves < 130 m od (470,830) | oblasti statistiky TVRZ_NA_ZEM | _na_zem | 1 |
| svet.gd:2026 | y = teren - 0.05 m | zapusteni rostliny do zeme | _na_zem | 1 |
| svet.gd:2251-2253 | nadvori tvrze \|x+4.5\|<24, \|z-0.4\|<19 | bez dosednuti fyzikou | _na_povrch | 1 |
| svet.gd:2254-2267 | paprsek +0.5/-80 m; nahoru 120 m; visi > 0.25 m -> dosedne, ponor clamp(vyska-y, 0.05, 1.0) | posledni posazeni na fyziku; za okrajem terenu pryc | _na_povrch | 1 |
| svet.gd:2428 | skala_* vynechany | skaly nedosedaji po fyzice | dosednout | 1 |
| svet.gd:2447-2462 | paprsek +0.5/-60 m; dosedne 0.05 m pod povrch, kdyz visi > 0.25 m | dosednuti po prvnim kroku fyziky (i impostory) | dosednout | 1/3 |
| svet.gd:2435-2437 | mech_*, moss_* -> _mech_na_zem | mech zvlast (sklopit k povrchu) | dosednout | 1 |
| svet.gd:2476-2492 | mech: okraje 0.4 * sirka; paprsek +0.6/-3 m, okraje +0.6/-1.5 m; nrm.y min 0.3; 0.03 m do povrchu | placka mechu sklopena podle normaly, na nejnizsim z 5 bodu | _mech_na_zem | 1 |
| svet.gd:2507,2529 | maly kvadr < 2 m; mekka rostlina < 0.6 m od stredu kvadru -> pryc | ker na miste kamene/polen z exportu smazan | _mekke_mimo_kvadry | 1 |
| svet.gd:2581-2582 | tvrde: balvan_, dead_tree, tree_stump, root_cluster, stromy s impostorem | co se maze z pesiny | _pesiny_volne | 1 |
| svet.gd:2586-2597 | odstup = 1.2 m + polomer balvanu * meritko | stromy/balvany/kmeny od osy pesiny | _pesiny_volne | 1 |
| svet.gd:2662 | TK_R Rect2(-29,-18,49,36) = x -29..20, z -18..18 | pudorys tvrze pro kryti travy | tvrz_kryti, pod_strechou_tvrze | 1 |
| svet.gd:2674-2677 | mrizka 0.5 m, paprsek 40..-10, zasah > teren + 1.6 m = strecha | pod strechou/stropem/ochozem tvrze trava neroste | tvrz_kryti | 1 |
| svet.gd:2679 | krov kovarny a zbrojnice x -20.5..-3.7, z 8.6..15.9 | bez kolize, rucne pod strechou | tvrz_kryti | 1 |
| svet.gd:3156-3157 | NIZKE: divoka_trava, grass_medium_01/02, dandelion_01, nettle_plant, fern_02, kamen_maly_1..5 | trida nizkych rostlin (kratky dosah) | _plants | 3 |
| svet.gd:3158-3161 | STREDNI: shrub_02, sipek, fir_sapling, rock_moss_set_01, dry_branches_medium_01, tree_stump_01/02, kamen_zula_1/2, kamen_piskovec_1/2, kamen_droba_1, orobinec_1/2, rakos_1/2, bez_cerny_1..3, dead_tree_trunk(_02), root_cluster_01, pine_sapling_small, balvan_droba_1, ker_husty, ker_kulaty | trida strednich rostlin | _plants | 3 |
| svet.gd:3163-3164 | PODROST: kapradi_1..3, kapradi_les, kopretiny, kvety_bile, byliny, mech_1..3, celandine_01, periwinkle_plant, moss_01, bark_debris_01 | podrost jen zblizka | _plants | 3 |
| svet.gd:3212-3217 | VYSKA_BYLIN [m]: nettle 0.25-0.5, dandelion 0.15-0.35, celandine 0.3-0.6, fern_02 0.4-0.9, periwinkle 0.1-0.25, kopretiny 0.12-0.2, kvety_bile 0.1-0.17, kapradi_ 0.35-0.8 | vyska bylin a kvetin ve hre | _plants | 1 |
| svet.gd:3218-3219 | VYSKA_BYLIN rakos_ 1.2-2.0 m, orobinec_ 1.0-1.6 m | rakosi zblizka nebylo obri (radce 20:30) | _plants | 1 |
| svet.gd:3220 | LISTNACE: lipa, dub, briza, vrba, buk, olse, borovice (+ smrk zvlast) | ktere druhy jsou stromy s plnym tvarem zdalky | _strom_tvar | 1/3 |
| svet.gd:3495-3497 | OBZ_ACT Rect2(-250,-250,1150,1600) = x -250..900, z -250..1350; OBZ_PAS 1100 m; OBZ_BUNKA 1024 m | hrana hratelne mapy a pas lesa obzoru | _obzor_les | 1/3 |
| svet.gd:3533 | les obzoru: smrk 0.55, buk_stredni 0.30, dub_stredni 0.15 | 3 druhy = malo volani kresleni | _obzor_les | 1/3 |
| svet.gd:3535-3544 | seed 2500, krok 7.5 m, rozptyl +-3.2 m | hustota stromu obzoru | _obzor_les | 1 |
| svet.gd:3550-3551 | sum p*0.0021+0.37 (0.7) + p*0.011+0.11 (0.3); les = smoothstep(0.44, 0.56) | stejna mista lesa jako zem.gdshader venku | _obzor_les | 1/2 |
| svet.gd:3553 | hustota smoothstep(0,0.6,les) * lerp(1.0 -> 0.45 po OBZ_PAS) | u kraje plny les, dal ridsi | _obzor_les | 1 |
| svet.gd:3567 | meritko 1.05-1.55 | dospely les (jinak "sad") | _obzor_les | 1 |
| svet.gd:3573 | y - 0.8 m | patka impostoru obzoru zapustena | _obzor_les | 1 |
| svet.gd:3582-3583,3597-3603 | pod 25 m nad tvrzi smrk -> dubohabrina (dub, buk, lipa, dub); primes 15 %; seed 1393 | realie 1393: smrk v nizinach nerostl | _smrky_na_listnace | 1 |

## Skály a kameny

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:461-462 | Skaly skryt | zaoblene balvany u tvrze (textura v letokruzich) – smazat | build | 1/4 |
| svet.gd:1903-1919 | skala_* kolize z <druh>_daleko.glb (LOD1 ~800 troj.), balvan z modelu | sit skaly/balvanu pro kolizi a usazeni | _skala_sit | 3 |
| svet.gd:1942 | rostlina > teren + 1.5 m | kandidat na dosednuti na povrch skaly | _na_povrch_skal | 1 |
| svet.gd:1944,2014,2089 | mrizka plosin skal 16 m (3x3 sousedni) | vyhledani skal pod rostlinou | _na_povrch_skal, _na_zem, _usad_skaly | 1 |
| svet.gd:1959 | paprsek od y+60 m | shora nad celou skalou | _na_povrch_skal | 1 |
| svet.gd:1968-1973 | na skale: y = povrch - 0.1 m; bez skaly: teren - 0.05 m | zapusteni rostlin na skale / na zemi | _na_povrch_skal | 1 |
| svet.gd:2008-2009 | kamen_* do 130 m od (470,830) se neusazuje | ves: kameny na dlazbe a cestach, ktere mrizka nezna | _na_zem | 1 |
| svet.gd:2045-2053 | obvod paty: 12 smeru, spodni 1 m site | obvod paty skaly | _usad_skaly | 1 |
| svet.gd:2056-2058 | LOD klice <druh>_daleko_0, _daleko2_0 | vsechny LOD skaly posunuty stejne | _usad_skaly | 3 |
| svet.gd:2068-2070 | obvod * 0.9; zapusteni 0.4 m pod nejnizsi teren pod obvodem | usazeni skal: pata na nejnizsim bode, zapustit 0,4 m | _usad_skaly | 1 |
| svet.gd:2071 | jen dolu (dy <= 0) | skala se nezveda | _usad_skaly | 1 |
| svet.gd:2073-2075 | balvan_: max zapusteni 40 % vysky | balvan nezakopat cely | _usad_skaly | 1 |
| svet.gd:2085 | plosina: polomer = rmax*meritko + 0.5 m, vyska = o.y + 1.0 | co stoji na skale, jde s ni dolu | _usad_skaly | 1 |
| svet.gd:2104 | rostlina nad patou+1, v polomeru a > teren + 0.5 m | rostlina na skale se posune se skalou | _usad_skaly | 1 |
| svet.gd:2553-2567 | skala: pes_d > rp*meritko + 1 m -> nechat; sit do 0.7 m od osy a 0.3-2 m nad zemi -> skala pryc | skala, kterou pesina neobesla, pryc (vc. vzdalenych verzi) | _pesiny_volne | 1 |

## Povrchy (shader zem)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:749-798 | zem shader: hlina = obrazky/cesta/cesta_atlas_a/n.jpg; louka, zrno_travy.png, louka_letecky, louka_dal, pole_obili, pole_oranice | vsechna useslapana zem (cesty, pesiny, dvory) z atlasu hliny cest (pravidla povrchu A) | material zem | 2/4 |
| svet.gd:767 | hlina_k 0.64 | kalibrace jasu atlasu cest (stred ~140, KCD2) | material zem | 2/4 |
| svet.gd:770-771 | obili_k 0.20, oranice_k 0.10 / albedo fotky | odrazivost pole obili a oranice | material zem | 2/4 |
| svet.gd:773 | atlas_travy_rgb vychozi (0.1,0.125,0.025) | prumer atlasu travy | material zem | 2/4 |
| svet.gd:777 | lom_rect (100, LOM_Z.x-16, 180, LOM_Z.y+40) | obdelnik lomu v shaderu zeme (x 100..180) | material zem | 2 |
| svet.gd:778 | lom_cerstve = LESENI_Z | cerstvy lom u leseni | material zem | 2 |
| svet.gd:779-782 | lom_pata: 16 bodu po 5 m od LOM_Z.x | pata steny lomu v shaderu | material zem | 2 |
| svet.gd:783-786 | trziste Vector4(TRZ_O, TRZ_U), trziste_r = TRZ_R | plocha trziste v shaderu zeme | material zem | 2 |
| svet.gd:787 | lom_y = max vysky v z 930 a 970 (x = stena+12) | vyska horni hrany lomu | material zem | 2 |
| svet.gd:793 | louka_k, louka_dal_k = atlas/fotka *0.95 | teren louky jako osvetleny list (driv 0.8, 1.3 svetle plochy) | material zem | 2/4 |
| svet.gd:794-797 | oranice_m, hlina_m=_size(pesina), louka_m, letecky_m | meritka vzoru zeme | material zem | 4 |

## Vykreslování / LOD / načítání

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:472-474 | Rakos*, Slama*: stin OFF, visibility_range_end 70 m | rakos a slama do 70 m, bez stinu | build | 3 |
| svet.gd:520-521 | DELIT_OD 60 m, DELIT_TROJ 8000 | site vetsi nez 60 m a s vic nez 8000 troj. se deli na ctverce s LOD | _rozdel_site | 3 |
| svet.gd:535-536 | materialy voda* se nedeli | hladiny drzi nadrz.gd | _rozdel_site | 3 |
| svet.gd:542 | Pohyb*, s blend shapes, neviditelne -> nedelit |  | _rozdel_site | 3 |
| svet.gd:546-547 | Teren* se nedeli (0.62) | ImporterMesh LOD za behu nevznikne; deleni terenu delalo plachty a skvrny | _rozdel_site | 3 |
| svet.gd:556 | krok = clamp(vel/5, 128, 640) m | velikost ctverce deleni (driv vel/10 = 64 m -> 1770 kresleni) | _rozdel_site | 3 |
| svet.gd:626-629 | kus dedi cast_shadow, visibility_range_end/margin/fade_mode | kusy deleni maji stejne dosahy jako puvodni sit | _rozdel | 3 |
| svet.gd:2272-2280 | impostor: 4 paprsky +-0.07 m, +0.5/-60 m | impostor ma polohu v pul presnosti (6 cm), nejvyssi zasah | paprsek_imp | 3 |
| svet.gd:2804 | ROST_R 115 m (vychozi; pravidla_modelu.json nacitani.rostliny_dosah_m) | dosah stavby uzlu rozsevu (byliny, puda, kere, kameni) kolem hrace | rostliny_okoli | 3 |
| svet.gd:2882 | rostliny_uvolnit_m = ROST_R + 30 m | za touto vzdalenosti (+ bunka) se bunky rostlin ruseji | rostliny_okoli | 3 |
| svet.gd:2805 | ROST_ZA_SNIMEK 8 | limit MultiMeshu za snimek (pouziva se uz rozpocet_us) | rostliny_okoli | 3 |
| svet.gd:2829 | davka 512 instanci | MultiMesh rozsevu delen po 512 instancich | rostliny_rozdel | 3 |
| svet.gd:2821-2822,2897 | bunka 24 m (nebo 48 m); d - 1.5*BUNKA < ROST_R | prirazeni do bunky a vyber bunek v dosahu | rostliny_rozdel, rostliny_okoli | 3 |
| svet.gd:2830-2832 | uzel dedi visibility_range_end, margin, cast_shadow, material | bunky rozsevu drzi dosahy z _plants | rostliny_rozdel, _rost_dil | 3 |
| svet.gd:2878 | rozpocet 1500 us vychozi | stavba rostlin za snimek | rostliny_okoli | 3 |
| svet.gd:2943-2945 | res://pravidla/pravidla_modelu.json -> "nacitani" | zdroj cisel nacitani (dosah, rozpocty) | _nac | 3 |
| svet.gd:2954 | rozpocet_us_tablet 2000 / rozpocet_us_pc 3000 | rozpocet planovace na snimek | planovac | 3 |
| svet.gd:2956 | tezkych_uloh_za_snimek 1 | nejvys 1 davka kolizi za snimek | planovac | 3 |
| svet.gd:2963 | zbyva > 200 us | rostliny jen kdyz zbyva rozpocet | planovac | 3 |
| svet.gd:3165 | LOD_M 220 m | LOD vzdalenost (dvojice strom/vzdalena verze) | _plants | 3 |
| svet.gd:3169 | STROM_PREP 40 m tablet / 60 m PC | prepnuti plny strom -> impostor (les 13-16 FPS na tabletu) | _plants | 3 |
| svet.gd:3170-3171 | SKALA_LOD0 40 m, SKALA_LOD1 120 m | LOD skal | _plants | 3 |
| svet.gd:3172 | STROM_DOHLED 120 m | za 120 m zadne stromy (rozpocet) | _plants | 3 |
| svet.gd:3173-3174 | ZJEDNODUSIT: nettle_plant, dandelion_01, celandine_01, fern_02, periwinkle_plant, weed_plant 300 troj.; bez_cerny, shrub_02 600 | nejvys trojuhelniku na model | _zjednodus | 3 |
| svet.gd:3196 | min 12 troj. na povrch | zjednoduseni | _zjednodus | 3 |
| svet.gd:3236-3300 | vzdaleny tvar stromu: kmen polomer max(h*0.012, 0.12), vyska 0.5h (smrk) / 0.45h, 5 sten; smrk 5 pater kuzelu od 0.12h, 9 zubu; listnac koruna od 0.55h (borovice) / 0.32h / 0.4h (vrba), 4-5 hrud | plny nizkopolygonovy tvar stromu zdalky | _tvar_mesh | 3 |
| svet.gd:3421 | IMP_BUNKA 1024 m (komentar: driv 256 m = 312 uzlu) | bunka MultiMeshe impostoru | _impostory | 3 |
| svet.gd:3422 | IMP_DOHLED 900 m | dohled impostoru stromu | _impostory | 3 |
| svet.gd:3427 | obrazky/impostory/impostory.json (stred, polomer, vyska) | ktere druhy maji impostor (= stromy) | _imp_druh | 3 |
| svet.gd:3456-3457 | fade_od = STROM_PREP - 10 m, fade_do = dohled | prolinani impostoru | _impostory | 3 |
| svet.gd:3478-3479 | custom_aabb + polomer*2.5 | obal bunky impostoru rucne | _impostory | 3 |
| svet.gd:3579 | obzor dohled 2500 m (v mlze) | dohled lesa obzoru | _obzor_les | 3 |

## Stíny

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:452 | SHADOW DOUBLE_SIDED | vsechny site oboustranne stiny (tenke vrstvy jinak propousteji svetlo) | build | 3 |
| svet.gd:469-471 | Teren*, Reka*, Ruiny*, Skaly*, *_zahrady, Hnojiste* -> cast_shadow OFF | rozpocet stinu: teren, voda, ruiny, zahrady nevrhaji stin | build | 3 |
| svet.gd:975 | Potok cast_shadow OFF | potok nevrha stin | _reka | 3 |
| svet.gd:1659-1662 | Teren_zaplata: material zem, stin OFF, trimesh kolize | zaplata jako ostatni teren | _zaplaty | 3 |
| svet.gd:3483 | impostor cast_shadow OFF | impostory nevrhaji stin | _impostory | 3 |

## Kolize

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:467-468 | Teren*, Nadvori* (ne *_sukne) -> trimesh kolize | teren a nadvori maji presnou kolizi; sukne jen pro oko (byla svislou stenou) | build | 3 |
| svet.gd:1887-1899 | meta bez_kolize; meta kolize_sit (Teren_cesta: kolize na vysce cesty); backface_collision true | trimesh kolize oboustranna (SketchUp otocene plochy) | _trimesh | 3 |
| svet.gd:2123 | skala_*/balvan_* (ne _daleko, konci _0) | druhy s kolizi ze site | _collisions | 3 |
| svet.gd:2133-2135 | balvan: konvexni obal; skala: trimesh z LOD1 | balvan (4000 troj. trimesh = fyzika 150 ms) -> konvex; veze/previsy trimesh | _collisions | 3 |
| svet.gd:2138,2161-2163 | veze: Vector2i(x*2,z*2) | kvadry exportu na miste skal vynechany | _collisions | 3 |
| svet.gd:2143-2148 | MEKKE (seznam), bunky 1 m | mekke rostliny bez kolize | _collisions | 3 |
| svet.gd:2151-2157 | skryte balvany uzel Skaly, bunky 1 m | kvadry pod skrytou siti Skaly pryc | _collisions | 3 |
| svet.gd:2167 | v_tvrzi: x -29..19.6, z -17.8..17.9 | uvnitr hradeb se kvadry nevynechavaji | _collisions | 1/3 |
| svet.gd:2170 | skryte: max(\|sx\|,\|sz\|) < 3 m a vyska < 3 m | jen nizke kvadry balvanu (ne pilire palace) | _collisions | 3 |
| svet.gd:2173-2180 | u mekke +-1 m, kvadr < 2 m siroky, < 2.5 m vysoky | kvadr rostliny z exportu vynechan | _collisions | 3 |
| svet.gd:2183 | min velikost kvadru 0.02 m |  | _collisions | 3 |
| svet.gd:2189-2211 | zabradli: sirka < 0.15, vyska 1.1+-0.05, delka > 1.5, sklon > 0.2 -> hranol se svislymi cely, o 0.05 m kratsi | zabradli schodu nebrzdi kapsli | _collisions | 3 |
| svet.gd:2218-2220 | rampa schodu: deska 0.1+-0.02, delka > 2, sirka > 0.8, sklon > 0.3 -> tloustka 0.6 m dolu | kapsle nepropadne rampou | _collisions | 3 |
| svet.gd:2225-2229 | podesty: 0.06 < tl < 0.22, > 0.8x0.8 m, vodorovna, y > 1 m -> 0.8 m dolu | tenke podesty/pavlac neprostupne | _collisions | 3 |
| svet.gd:2600-2607 | kolize odebranych pryc (klic x*4) | bez neviditelnych prekazek na pesine | _pesiny_volne | 3 |
| svet.gd:2618 | _daleko, sapling bez kmene | mlade stromky a vzdalene verze bez kolize | _kmeny | 3 |
| svet.gd:2627 | prumer kmene clamp(vyska*meritko*0.012, 0.12, 0.6) m (polomer), krok 0.04 | strom 20 m -> kmen 0,48 m | _kmeny | 3 |
| svet.gd:2633-2635 | valec vyska 3 m, stred y+1.4 | kolize kmene do 3 m | _kmeny | 3 |
| svet.gd:2644 | KOLIZE_MIN 0.15 m | co vycniva mene nez 0,15 m, kolizi nema (krok prekroci) | kolize | 3 |
| svet.gd:2645-2646 | MEKKE: mech_, moss_, kapradi_, ker_husty, ker_kulaty, fern_, celandine, periwinkle, dandelion, weed_plant, nettle, shrub_, sipek, bez_cerny, divoka_trava, grass_, rakos, orobinec, bark_debris, dry_branches | mekke rostliny nikdy nemaji kolizi (hrac projde) | _collisions, _mekke_mimo_kvadry | 1/3 |
| svet.gd:2652 | KOL_BUNKA 32 m | kolize krajiny po bunkach, nactene 3x3 kolem hrace (aspon 32 m) | kolize_rozdel, kolize_okoli | 3 |
| svet.gd:2714 | KOL_DAVKA 20 tvaru | bunka se stavi po davkach, jedna davka za snimek | _kol_davka | 3 |
| svet.gd:2756 | ruseni bunek dal nez 2 (pri presunu dal nez 1) | odlozene uvolneni kolizi | kolize_okoli | 3 |
| svet.gd:2996-2999 | pata = teren; do 80 m od (-4,0) min s _vyska_sit; vycnivani < KOLIZE_MIN -> bez kolize | jedine misto vzniku kolize krajiny (tvrde veci) | kolize | 3 |
| svet.gd:3004 | meta "tok" | kolize presouvane do bunek KOL_BUNKA | kolize, kolize_rozdel | 3 |

## Materiály / textury

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:7 | BARVA_LOUKY (0.145,0.235,0.02) lin. | barva louky z dalky (kalibrace test dalka; sRGB ~85,118,36) | material zem: barva_louky | 2/4 |
| svet.gd:8 | BARVA_LESA (0.062,0.095,0.015) lin. | barva lesa v terenu | material zem: barva_lesa | 2/4 |
| svet.gd:11 | HLOUBKA: dlazba 0.04, dlazba_hrad 0.035, kocicky 0.05, piskovec 0.02, podlaha 0.008, prkna_ven 0.012, sindel 0.035, skala_piskovec 0.07, kamen 0.04, kamen_lisejnik 0.05 (m) | hloubka parallaxu (vyskove mapy) v metrech | material tex | 4 |
| svet.gd:745 | parallax jen coord=world nebo sindel/skala_piskovec | kde se pouziva vyskova mapa | material | 4 |
| svet.gd:640-647 | FastNoise simplex freq 0.012, 5 oktav, 512x512 seamless | sumova textura "sum" pro skvrny/antitile/stekance | _make_noise | 4 |
| svet.gd:667 | vychozi velikost textury [2,2] m | meritko vzoru, kdyz svet.json/textury nema zaznam | _size | 4 |
| svet.gd:653 | modely/textury/<jmeno>_<diff\|nor\|rough\|disp>.jpg | sada map textury | _t | 4 |
| svet.gd:677-683 | popel: alpha scissor, pruhledny | vrstva popela pod poleny neviditelna | material | 4 |
| svet.gd:684-691 | uhli: albedo (0.05,0.04,0.035), emise (1,0.35,0.08) x0.6, roughness 0.9 | doutnajici uhliky | material | 4 |
| svet.gd:694-712 | zdivo: kamen zdivo_* + omitka_*, kamen_m/omitka_m = _size, kryti, tint, kamen tint, spina ze svet.json | shader zdiva | material | 4 |
| svet.gd:713-724 | tex: velikost=_size(tx), prohodit, svet(world/uv), tint, sedost(grey) | obecny texturovy shader | material | 4 |
| svet.gd:725-727 | deska_stodola tint x1.7 | stodola svetlejsi (sedohneda, KCD2) | material | 4 |
| svet.gd:728-730 | tint2 -> pestrost 1.0 | pestrost barvy | material | 4 |
| svet.gd:731-734 | skala_piskovec, kamen_lisejnik, kamen: antitile 1, skvrny 1 | kamen proti opakovani vzoru | material | 4 |
| svet.gd:735-738 | sindel: skvrny 1, radky 1 | sindel po radach | material | 4 |
| svet.gd:739-742 | tram, prkna_ven, okenice, omitka_bila, malta, dosky, drevo_stare, kura (ne dub/deska/prkna): stekance 0.55 (roubeni*, lata, dub_ven, sindel_hra) jinak 0.4; skvrny 0.6 | stekance a skvrny na drevu/omitce | material | 4 |
| svet.gd:743-744 | swap a coord uv -> kus 1.0 |  | material | 4 |
| svet.gd:828-836 | trava: roughness 0.75, backlight (0.25,0.3,0.1), cull off | material trav ze svet.json | material | 4 |
| svet.gd:851-861 | vychozi: col (0.5,0.48,0.45), rough 0.8, metal 0, emise max 4 | obecny material | material | 4 |
| svet.gd:892-925 | dlazba_kus: normaly s y<0.5 -> nahoru | kusy dlazby jsou ploche kameny, normaly nahoru (byly cerne) | _dlazba_normaly | 2/4 |
| svet.gd:1835-1851 | drevo_plot -> textura tram, velikost 1.2 m, prohodit true | prkna mostu a vrat/branek: jedno prkno = fotka tramu podel (ne ctverecky) | _prkna_tram | 4 |
| svet.gd:3221-3222 | TINT_LISTI: dub_ (0.6,0.84,0.58), briza (0.82,0.96,0.72), smrk (1.3,1.4,1.15), borovice (0.9,1.05,0.85) | tonovani listi (impostory) | _impostory | 4 |
| svet.gd:3253-3256 | kura (0.2,0.15,0.1), briza (0.6,0.58,0.52); zelen smrk (0.07,0.13,0.06), briza (0.2,0.28,0.1), vrba (0.2,0.26,0.14), borovice (0.1,0.16,0.07), olse (0.11,0.19,0.07), jinak (0.14,0.22,0.08) | barvy vzdalenych tvaru stromu | _tvar_mesh | 4 |
| svet.gd:3293-3297 | tvar: barva z vrcholu, roughness 1.0, bez odlesku, lambert wrap | material vzdaleneho tvaru | _tvar_mesh | 4 |
| svet.gd:3361-3362 | stin koruny 0.45 dole .. 1.2 nahore | svetlo nahore, tma dole | _hruda | 4 |
| svet.gd:3369-3383 | listi.gdshader: stred koruny 0.62 h (strom) / 0.5 (ker); sila_vetru 1.0 / 0.6; objem 0.65 / 0.5; prah = alpha scissor | vitr a objem listi | _listi_shader | 4 |
| svet.gd:3396-3400 | obal koruny: UV opakovani po ~2.5 m (rep = max/1.25) | textura listi na vzdalene koruně | _obal | 4 |
| svet.gd:3584-3594 | skala_detail.gdshader: detail skala_piskovec, detail_m = _size, detail_prumer albedo (vychozi 0.2) | detail textura na skalach | _skala_detail | 4 |
## Duplicity a rozpory

| # | věc | místa a čísla | poznámka |
|---|---|---|---|
| 1 | Okolí tvrze, kde se výška bere ze sítě terénu (val, příkop) místo mřížky louky | `_na_zem` ř. 2001: \|(x+4, z)\| < **75 m**; `kolize` ř. 2997: < **80 m**; ladicí oblast „tvrz“ ř. 2023: < **80 m** | Stejný pojem, dvě čísla; rostlina mezi 75 a 80 m dosedá na mřížku, ale její kolize počítá s výškou sítě. |
| 2 | Odstup od osy pěšiny | `_pesiny_volne` ř. 2594: tvrdé věci **1,2 m** + poloměr balvanu; skála: síť do **0,7 m** od osy a 0,3–2 m nad zemí, hrubý filtr rp+**1 m** (ř. 2557–2565); komentář ř. 2539: kamení na kraji **0,8–1,5 m** zůstává. Mimo rozsah (rozsev): keře **1,8 / 1,5 / 1,6 / 2,2 m** (ř. 4143, 4208, 4258, 4266), **2,5 m** (ř. 4288), **0,6 m** (ř. 4337), stromy **2,0 m** (ř. 4433, 4455), **1,5 m** (ř. 8882), **8 m** (ř. 10055) | Každý rozsev má vlastní odstup od pěšiny a úklid po rozsevu má další. Žádná společná tabulka. |
| 3 | Nádvoří tvrze (vlastní terén, rostliny se nesahají) a půdorys tvrze | `_na_zem` ř. 1998 a `_na_povrch` ř. 2251: \|x+4,5\|<24, \|z−0,4\|<19 → x **−28,5..19,5**, z **−18,6..19,4**; `_collisions` v_tvrzi ř. 2167: x **−29..19,6**, z **−17,8..17,9**; `TK_R` ř. 2662: x **−29..20**, z **−18..18** | Tři obdélníky pro tutéž tvrz, liší se o 0,5–1,5 m (hlavně na jihu: z 19,4 vs. 17,9 vs. 18). |
| 4 | Dosahy načítání v `pravidla_modelu.json` vs. konstanty v kódu | JSON `nacitani`: rostliny_dosah_m 115, rostliny_uvolnit_m 145, **kolize_bunka_m 32, kolize_bunek_okoli 1, kolize_uvolnit_bunek 2, kolize_davka_tvaru 20, zasek_ms 40**; kód: `ROST_R` 115 (ř. 2804, jen výchozí, čte se z JSON), ale `KOL_BUNKA` 32 (ř. 2652), `KOL_DAVKA` 20 (ř. 2714), rušení >2 / >1 buňky (ř. 2756) jsou **pevné v kódu** a klíče kolize_* / zasek_ms kód nečte | Čísla teď sedí, ale změna v JSON se u kolizí neprojeví. `ROST_ZA_SNIMEK` 8 (ř. 2805) se nikde nepoužívá (nahradil ho rozpočet µs). |
| 5 | Dosah stromů / impostorů | `STROM_DOHLED` **120 m** (ř. 3172, „za 120 m žádné stromy“) vs. `IMP_DOHLED` **900 m** (ř. 3422) a les obzoru **2500 m** (ř. 3579); `STROM_PREP` 40/60 m (ř. 3169), fade impostoru od STROM_PREP−10 (ř. 3456); `LOD_M` 220 m (ř. 3165) | Komentář u STROM_DOHLED platil před impostory; podle ř. 10495 je 120 m konec vzdáleného tvaru, impostor jde dál až do 900 m. Pro tabulku 3 je nutné rozlišit tvar a impostor. |
| 6 | Ponoření paty rostliny / skály do země | `_na_zem` −**0,05 m** (ř. 2026); `_na_povrch_skal` na skále −**0,1 m**, na zemi −0,05 (ř. 1969–1972); `_na_povrch` ponor clamp(výška−y, **0,05..1,0**) (ř. 2264); `dosednout` −**0,05** (ř. 2452); mech −**0,03** (ř. 2492); skály −**0,4 m** (ř. 2070); balvan max **40 %** výšky (ř. 2075); impostor obzoru −**0,8 m** (ř. 3573); zelí −0,05 (ř. 3122) | Různá zapuštění podle kroku; prahy pro „visí“ jsou všude **0,25 m** (ř. 2010, 2263, 2453), ale „zakopaná“ jen v `_na_zem` (−1,0 m). |
| 7 | Seznamy měkkých rostlin a tříd | `MEKKE` (ř. 2645) obsahuje `kapradi_`, `fern_`, `rakos`, `orobinec`, `bez_cerny`, `sipek`, `shrub_`; tytéž druhy jsou v `STREDNI` (ř. 3158: rakos, orobinec, bez_cerny, sipek, shrub_02, ker_*) a `PODROST` (ř. 3163) – třídy dosahu a třídy kolize se kříží | Není chyba, ale stejný druh má dvě nezávislé klasifikace (měkký/tvrdý a nízký/střední/podrost); `_pesiny_volne` má třetí („tvrdé“ ř. 2581). |
| 8 | Centrum vsi a poloměr | stará náves (470, 830), ±88/80 × 45 m (ř. 42–45); kameny vsi < **130 m** od (470,830) (ř. 2008); ladění „ves“ < 130 m (ř. 2023); kolize staré návsi \|x−470\| < **200 m** (ř. 126); okno Teren_ves x 400..560, z 760..900 (ř. 1480) | Ves popsaná pěti různými oblastmi. |
| 9 | Prahy „změny výšky“ při úpravách terénu | 0,005 m (ř. 217, 393, 1442, 1457), 0,01 m (ř. 1261, 2402), 0,05 m (ř. 1198) | Technicky drobné, ale každá úprava jinak. |
| 10 | Barva louky | `BARVA_LOUKY` (ř. 7) vs. louka z vrcholů terénu (g>0,8, ř. 348) vs. kód masky louky 200 (ř. 168) vs. COLOR.g 0,85 (ř. 1320, 1648) | Louka je kódovaná třemi způsoby (barva, maska trava_ves, zelený kanál vrcholu, práh 0,8 vs. 0,85). |
| 11 | Kolize kmene vs. vzdálený tvar | kmen kolize poloměr clamp(výška·měřítko·**0,012**, 0,12, 0,6) (ř. 2627) – vzdálený tvar kmene max(h·**0,012**, 0,12) (ř. 3258) | Stejný vzorec, horní mez jen u kolize. Komentář ř. 2627 „kmen 0,48 m průměr“ – kód dává poloměr. |
| 12 | Kůl mostu | komentář ř. 1667 „vyšší než 1 m“, kód `bb.size.y < 0.5` (ř. 1708) | Komentář a kód se liší. |
