# Soupis čísel a pravidel – `scripts/svet.gd` ř. 7160–10721 (díl C)

Zdroj: jen čtení, v repu se nic neměnilo. Sloupec „tabulka“: 1 ZASAZENÍ, 2 POVRCHY, 3 TŘÍDY (vykreslování), 4 MATERIÁLY, „-“ = jen semínko náhody (pro opakovatelnost).
Zápis „a..b“ = rozsah náhody, „x0.8-1.2“ = násobek měřítka, „ponor“ = zapuštění do země (záporné číslo = podíl výšky modelu).

## Pořadí stavby dnes

`build()` (ř. 426–512), každý krok měří `_krok_cas`:

1. ř. 429–431 `svet.json` → `data`, `water_y = voda_y (-2.75)`, `pasma()` (pásma zasazení, hlavní vlákno)
2. ř. 433 `_vo_data()` (jen VES_OBLOUK) · ř. 435 `_ves_stare_pryc()` · ř. 437 `_make_noise()`
3. ř. 439–442 načtení `tvrz.glb` → `root`
4. ř. 444 `_vo_scena(root)` (VES_OBLOUK)
5. ř. 446 `_koryto_terenu(root)` (def. 1336) – uvnitř v pořadí: 1338 `_terasa_terenu` → 1340 `_stare_cesticky` → 1342 `_prikop_zaplata` → nádrže/hladiny (1361–1397) → 1407 koryto `pokryj` → 1415 `_najezdy_mostu` → 1417 `_teren_pod_vraty` → **1419 `_upravy_terenu`** (7787: `_najdi_brody` → `_ryb_priprav` → `_domy_vysky` → profil lomu `_lom_srov` → rovina trhu → vrcholy Teren*: `dum_teren(ryb_teren(uprava_y(y)))`) → **1421 `_cesty_tvar`** (6340)
6. ř. 448–473 smyčka přes MeshInstance3D: `_apply_materials`, stíny DOUBLE_SIDED, skrytí Reka_voda/Teren_cesta_kamen/Skaly, `_bez_zeli`, most (`_most_kuly`, `_most_podlozka`), `_trimesh` pro Teren*/Nadvori*, stíny OFF pro terén/vodu/ruiny/zahrady/hnojiště, rákos a sláma do 70 m
7. ř. 475 `_reka` · 477 `_zaplaty` · 479 `_kontrola_hladiny`
8. ř. 481 `_collisions` (2115) – uvnitř 2127 `_usad_skaly` → 2108 `_na_povrch_skal` → 1975 **`_na_zem` (1. průchod)**, uloží `_na_zem_arg`
9. ř. 483 `_static_items` (10659; plní `_stavby`) · 485 `_lom_sit_priprav` (9275) · 487 `_lom_vybaveni` (3012; plní `_lom_zabrano`) · 489 `_lom_sut` (9054, kvádry MultiMesh) · 491 `_lom_stena_svisla` (9186) · 493 `_rybnik_dil` (7705) · 495 `_ves_domy` · 497 `_erb_tvrze` · 499 `_info`
10. ř. 501 **`_plants`** (10217) – uvnitř v pořadí:
    `_nacti_kryti` 10230 → `_cesta_do_kryti` 10231 → `_uvnitr` (pudorysy staveb) 10232–10241 → `_smrky_na_listnace` 10242 → `_skalni_mesto` 10243 → `_lesni_patro` 10244 → `_tvrz_zvencí` 10245 → `_nove_lesy` 10246 → **`_stanoviste` 10247** (8439: maska stromů/skal → `_pes_postav` 8499 (+`_pes_od_sten`) → kanál A pěšin → **`_krajina` 8560** (9544: vrba −0,3 → keře z louky pryč → kameny z kosené louky pryč → rozsev 4 m → `_vychozy` 9708 → `_pata_sten` 9709 → `_lom` 9710 → kameny/balvany/keře potoka → `_stromy_u_potoka` 9789 → rákos na suchu pryč → rákos u nádrží → `_prikop_kameny` 9831) → `_pudy` 8562) → `_les_hustsi` 10248 → `_kere_podel_pesin` 10249 → `_lesni_plast` 10250 → `_lesni_puda` 10251 → `_kvetiny_louky` 10252 → `_kvetiny_zahrad` 10253 → `_kere_kulate` 10254 → `_ves_cesty_volne` 10255 → `_rybnik_breh` 10256 (→ `_rybnik_breh_dil`) → `_brody` 10257 → `_lom_cisti` 10258 → `_trziste_cisti` 10259 → (`_byliny_rozsev` zakomentováno 10260) → vrba_hlavata* = [] 10262 → smrk_/kamen_ z kosené louky pryč 10266 → **`_na_zem` (2. průchod) 10279** → `_na_povrch` 10280 → `_mekke_mimo_kvadry` 10281 → `_pesiny_volne` 10282 → `_most_bez_stromu` 10283 → `_stromy_mimo_balvany` 10284 → `_kmeny` 10285 → `_cesty_rostliny` 10286 → `_cesty_kameny` 10287 → `_cesty_kere` 10288 → `_ves_kompozice` 10289 → šípek* = [] 10291 → tvorba MultiMeshů (VYSKA_BYLIN, mech, `smi_tu_byt` znovu pro nízké/střední, LOD/dosahy/stíny) → `_impostory` 10546 → `_obzor_les` (deferred)
11. ř. 503 `_ves_grass` (vrací se hned po výrobě `grass_mesh`, trávu dělá louka.gd) · 505 `_rozdel_site` · 507 `_cesty_material` · 509 `_kolize_cisteni` · 511 `_okluzory`

### Kde pozdější krok přidává nebo posouvá to, co už usadil předchozí

| krok (řádek) | co dělá s již usazeným |
|---|---|
| `_upravy_terenu` 7825 (v `_koryto_terenu` po `_terasa_terenu`) | přepisuje výšky vrcholů terénu: brody → srovnání stěny lomu → trh → pás rybníka → dům (dům až po rybníku); pak `_cesty_tvar` znovu tvaruje terén pod cestami |
| `_usad_skaly`/`_na_povrch_skal`/`_na_zem` (v `_collisions`) | přesune rostliny z exportu (byly na terénu před úpravami) na nový terén / povrch skal |
| `_krajina` 9582 | vrby hlavaté z exportu i z `_tvrz_zvencí` (10245) sníží o 0,3 m – a v 10262 se pak všechny vrby smažou |
| `_krajina` 9587, 9601; `_pata_sten` 8825; `_lom` 8754; `_stromy_u_potoka` 9942–9996 | MAŽOU dříve rozseté i exportované keře, kameny a stromy (louka, strmý svah, lom < 2 m, potok, most, tvrz) |
| `_lom_cisti` 10258 | znovu maže rostliny v lomu, teď < 3 m (dřív `_lom` < 2 m) – smaže i keře, které `_lom` sám zasadil 0,5–5 m za okrajem plochy (přežijí jen 3–5 m) |
| vrba_hlavata* = [] 10262 | smaže vrby z `_rybnik_breh_dil`, `_tvrz_zvencí`, `_krajina` i exportu; `_ves_kompozice` (10289, scéna 3) ale přidá `vrba_hlavata_1_0` POTOM → ve vsi vrba zůstane (model `vrba_hlavata_1.glb` existuje) |
| kosená louka 10266 | maže smrky a kameny ze všech předchozích rozsevů (i kameny brodů a koryta, pokud by padly do kosené louky) |
| `_na_zem` 2. průchod 10279 a `_na_povrch` 10280 | znovu usadí všechno včetně rozsevů na terén/povrch |
| `_cesty_rostliny` 10286 | po `_na_zem` maže rostliny v pásmu cest a POSOUVÁ výšku rostlin do 12 m od cesty o vyrovnání profilu (zářez/násyp) |
| `_cesty_kameny`, `_cesty_kere`, `_ves_kompozice` 10287–10289 | přidávají až po `_na_povrch`, `_pesiny_volne`, `_stromy_mimo_balvany`, `_kmeny` → tyto kontroly na ně neplatí; výška jen `_vyska − 0,05` nebo `cesta_y` |
| šípek* = [] 10291 | smaže šípek z `_cesty_kere`, `_lom`, `_tvrz_zvencí`, `_krajina`, `_kere_*` |
| kreslení 10406–10438 | mění měřítko bylin (VYSKA_BYLIN), mech sklopí a zapustí o 3 cm, nízké/střední ještě jednou projdou `smi_tu_byt` |
| `_stanoviste` 10247 | maska „po všech úpravách“ se ve skutečnosti počítá UPROSTŘED rozsevů – stromy z `_les_hustsi`, `_lesni_plast`, `_kere_kulate`, `_ves_kompozice` atd. v masce kryti (R/G) nejsou |

## Cesty a pěšiny

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:7286 | kraje ~1,5/m2, hrbet 0,4, koleje 0,2; 5-20 cm, pul v zemi | zadani hustoty kamenku na ceste (komentar radce 18:00) | _cesty_kameny | 1/2 |
| svet.gd:7289-7290 | kamen_maly_1_0 .. kamen_maly_5_0 | druhy kamenku cest | _cesty_kameny | 1 |
| svet.gd:7295 | seed 18001 | nahoda kamenku cest | _cesty_kameny | - |
| svet.gd:7304,7339 | krok 0.8 m | krok bodu osy cesty (s = i*0.8 + s0) - pouziva se ve vsech funkcich cest | _cesty_kameny, _cesty_kere | 1 |
| svet.gd:7306 | 3 + 9*kmn kusu na krok | pocet pokusu na krok osy, kamenity usek (cesta_useky.z) az 12 | _cesty_kameny | 1 |
| svet.gd:7307 | lat +-1.1*hw | kamenky az 10 % za polosirku cesty | _cesty_kameny | 1 |
| svet.gd:7309 | hus = (1+1.5*op.w) * {0.25 v koleji (abs(pr.w)<0.2), 0.5 hrbet (abs(lat)<0.35), 0.55..0.95 k okraji (hw-0.8..hw)}; x0.8 | relativni hustota kamenku napric profilem; pr.z > 0.3 nic | _cesty_kameny | 1 |
| svet.gd:7313-7316 | 0.06-0.2 (x1.4 v 0.6 m u kraje); 25%*kmn: 0.18-0.35 | meritko kamenku; vetsi vystupujici kameny v kamenitych usecich | _cesty_kameny | 1 |
| svet.gd:7318 | -sc*0.35 | kamenek zapusten o 35 % velikosti pod profil cesty | _cesty_kameny | 1 |
| svet.gd:8093-8114 | PESINY - 12 lomenych car (rucni souradnice): 0 tvrz-kostelik (6,95)->(220,40); 1 Doubrava (8,140)->(300,340); 2 skalni mesto-Pusta skala-hostinec (-2,120)->(-95,860); 3 do vsi (300,340)->(462,806); 4 most tvrze->rozcesti (-3,23)->(2,72); 5 ves->uhlire (538,856)->(640,825); 6 lom->brod->odbocka (140,940)->(300,673); 7 prazdna; 8-11 nadvori (brana->studna->palac (-3,17)..(8,-6.8), kovarna (-14,7), (-0.1,-6.8), staje (12,12)) | osy pesin a stezek | _pes_postav, pes_useky | 1 |
| svet.gd:8118 | PES_ZAKLAD = 0.55 m | zakladni polosirka pesiny; prahy v metrech (shader, louka, rozsev) plati pro 0,55 a skaluji se PES_SIRKA/PES_ZAKLAD | _pes_postav, _stanoviste | 1/2 |
| svet.gd:8121 | PES_SIRKA = [0.6,0.6,0.6,0.6,1.6,0.6,1.6,0.6,0.7,0.7,0.7,0.7] | polosirka kazde pesiny (1.6 = vjezd od mostu a cesta z lomu, pro vuz) | _pes_postav | 1/2 |
| svet.gd:8136 | PES_K = 0.5 m | mrizka pole vzdalenosti od osy pesiny (pes_dist) | _pes_postav, pes_d | 2 |
| svet.gd:8137 | PES_DMAX = 4.0 m | dosah pole vzdalenosti od pesiny (R8 = d/4 m) | _pes_postav, pes_d | 1/2 |
| svet.gd:8146 | bunka 16 m | mrizka bodu osy pesin | _pes_od_sten, _pes_postav | - |
| svet.gd:8178-8195 | 4 iterace; d < 1.3 m; posun max 1.3 m/iteraci | osa pesiny odsunuta od sten skal na 1,3 m (POSOUVA osu po _pes_postav) | _pes_od_sten | 1 |
| svet.gd:8231-8240 | bunka 16 m, kruh - 16 | mrizka prekazek pesin | _pes_postav | - |
| svet.gd:8241-8263 | Teren_cesta: plocha troj. po 1 m do mrizky 2 m; vyluka +-4 bunky (8 m, komentar 6 m) | kde je cesta z Blenderu blizko, pesina se prerusi (zadne zdvojene cesty) | _pes_postav | 1 |
| svet.gd:8276-8278 | pesiny 4, 6 a >= 12 vynechany v pes_osa | z pesin 4 (od mostu) a 6 (k lomu) jsou cesty (_cesty_tvar) | _pes_postav | 1 |
| svet.gd:8285-8288 | bod po 2 m; vlnka _pes_o x _brod_tlum; u pesiny 4 x0.15 | osa pesiny zvlnena | _pes_postav | 1 |
| svet.gd:8289-8299 | 3 pruchody | odsunuti bodu osy z kruhu skal a staveb | _pes_postav | 1 |
| svet.gd:8303 | tvrz x -46..37, z -35..36 (krome 4 a >= 8) | ke tvrzi jen hlavni cesta pres most - zadna stezka do tvrze, prikopu a 5 m kolem | _pes_postav | 1 |
| svet.gd:8312-8323 | klouzavy prumer 5 bodu | vyhlazeni osy (konce drzi) | _pes_postav | 1 |
| svet.gd:8324-8336 | 1 pruchod po vyhlazeni | znovu od skal (vyhlazeni vratilo body) | _pes_postav | 1 |
| svet.gd:8394 | _pes_o = 8.0*sin(PI*x/dl)*(0.65*sin(0.045x+1.7s)+0.35*sin(0.11x+4.1s)) | vlnka osy pesiny az 8 m kolmo, konce useku drzi | _pes_o | 1 |
| svet.gd:8589-8626 | Teren_cesta: troj. vzorkovany po 0.5 m (+0.25) -> kryti 2 | na ceste z tvrze nic neroste (louka ani nizky drn) | _cesta_do_kryti | 1/2 |
| svet.gd:8627-8642 | cesty_osy: lat -1.3*hw-0.5 .. 1.3*hw+0.5 po 0.4 m, podel 0 a 0.4 m -> kryti 2 | cely pas cesty bez louky - louka tam sazi jen travu cesty (cesta_trava) | _cesta_do_kryti | 1/2 |
| svet.gd:8645-8675 | Most_potok: AABB +8 m; podel +-6 m za konec mostovky; napric 15 % z kazde strany pryc | pas mostovky prodlouzeny o 6 m bez travy | _cesta_do_kryti | 1 |

## Terén

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:7669-7682 | okraj = hladina+0.30; v pasu lerp z okraj-0.02; uvnitr h-0.06 (do 2,5 m od okraje) jinak h-0.6 | teren hry pod dilem nize nez povrch dilu, za okrajem pas 6 m | ryb_teren | 2 |
| svet.gd:7685-7695 | hladina+0.28 na okraji, v pasu lerp; uvnitr povrch dilu | mrizka vysek pro louku a rostliny na dilu | ryb_mrizka | 2 |
| svet.gd:7759 | la > 5 m, al > w + 40 m -> mimo brod | dosah upravy brodu | uprava_y | 1/2 |
| svet.gd:7763 | dno = hladina - 0.45 + max(al-w,0)*0.25 | dno brodu 0,45 m pod vodou, najezdy 1:4 | uprava_y | 1/2 |
| svet.gd:7765-7766 | w+4 m; smoothstep(2.5, 4.5, la) | zarez svahu koryta, brod 4-5 m siroky s nabehem | uprava_y | 1/2 |
| svet.gd:7769-7776 | LESENI_Z +-4 m (nabeh 3,5 m); u 0.3..-5.2 dno = vyska paty; za tim lavice ve vysce q.z do k+6 | srovnani steny lomu za lesenim (vybrat skalu 5 m za patou) | uprava_y | 1/2 |
| svet.gd:7777-7779 | d < 5 m; smoothstep(0,5) | rovina trhu (je-li TRZISTE) svazana na 5 m | uprava_y | 1/2 |
| svet.gd:7788-7790 | poradi: _najdi_brody, _ryb_priprav, _domy_vysky | priprava pred upravami terenu | _upravy_terenu | 1 |
| svet.gd:7792-7800 | LOM_Z -4..+4; LESENI_Z -5..+5; k od 1 do 12 po 0.5, dokud prevyseni < 9.5 m; lavice max yf+10 | profil srovnane steny lomu (_lom_srov) | _upravy_terenu | 1/2 |
| svet.gd:7802-7808 | TRZ_R po 2 m | rovina trhu = prumer vysky plochy (jen kdyz TRZISTE) | _upravy_terenu | 2 |
| svet.gd:7812 | Teren_obzor, Teren_cesta_kamen vynechany | site, ktere se neupravuji | _upravy_terenu | 2 |
| svet.gd:7825 | dum_teren(ryb_teren(uprava_y(y))) | PORADI uprav vysky vrcholu: brody/lom/trh -> rybnik -> dum (dum az po pasu rybnika); prah 0.005 m | _upravy_terenu | 1 |
| svet.gd:8699-8724 | tan sklonu = max rozdil hran bunky / k (mrizka trava_kraj 2 m, vysky v cm) | sklon bunky; terasy/skalni steny 1,2-18 | sklon_bunky, smi_tu_byt, _pata_sten | 1/2 |
| svet.gd:9837-9862 | tvrz abs(x+4) <= 80, abs(z) <= 75; mrizka 1 m (max vrchol), soused do 2 m | vyska terenu u tvrze z vrcholu siti (po prikopu) | _vyska_sit | 2 |

## Ves / budovy

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:7365-7366 | VES_D = (0.7620, 0.6476), VES_N = (-0.6476, 0.7620) | osy navsi u (podel rad) a v (napric); rady domu v = 294,6 a 361,6 | _ves_bod, _ves_kompozice | 1 |
| svet.gd:7377 | seed 1393 | nahoda kompozice vsi | _ves_kompozice | - |
| svet.gd:7381 | pasma.budova.kmen_od_zdi_m | odstup kmene stromu od zdi (AABB domu zvetseny); ostatni (plevel, kere) 0.2 m | _ves_kompozice.pridej | 1 |
| svet.gd:7385-7386 | cesta_kraj_osa < odstup_cesty(druh, typ osy) | rostlina vsi blize kraji cesty pryc | _ves_kompozice.pridej | 1 |
| svet.gd:7387 | v stare zahrade jen bez* a shrub* | smi_tu_byt + _v_stare_zahrade | _ves_kompozice.pridej | 1 |
| svet.gd:7393 | y = _vyska - 0.05 | rostliny vsi zapusteny 5 cm | _ves_kompozice | 1 |
| svet.gd:7395-7397 | druh_daleko_0 | kazdy strom se zaroven prida do daleke varianty (impostor/daleko) | _ves_kompozice | 3 |
| svet.gd:7402-7405 | lipa_stara_0 (878,340, x1.2), dub_stary_0 (931,312, x1.05); s vo: lipa f 0.08 bok 9.0 x1.2, dub f 0.52 bok -9.5 x1.1 | rucne umistene stare stromy na navsi (u,v resp. pozice na oblouku ulice); rozptyl +-4/+-3 m resp. +-0.02/+-1.5, 6 pokusu, meritko x0.9-1.1 | _ves_kompozice | 1 |
| svet.gd:7417 | kere = bez_cerny_1..3_0, shrub_02_0..2 | seznam keru vsi | _ves_kompozice | 1 |
| svet.gd:7418-7434 | sceny 1-7: [druh, x pres osu, z podel osy, meritko] (1 chalupa bez 1.2/0.6; 2 lipa -1.0/0.9; 3 vrba hlavata -1.3/-0.8; 4 dub 0.4/-1.6 + shrub 1.25/0.7; 5 rychta lipa 0/1.9; 6 brizy 1.5/0.3, 1.7/-0.2; 7 bez, shrub, dub_stredni) | rucni scena u kazdeho domu podle typu k; "k" = shluk koprivy | _ves_kompozice | 1 |
| svet.gd:7435 | plevel = nettle_plant_0..3 | kopřivy | _ves_kompozice | 1 |
| svet.gd:7437 | d.k >= 20 vynechat | chyse u lomu maji vlastni vybaveni | _ves_kompozice | 1 |
| svet.gd:7447-7449 | 4-7 kusu; podel +-1.5 m; 0.3-0.9 m od zdi; meritko 0.5-0.9 | shluk kopriv u paty zdi | _ves_kompozice | 1 |
| svet.gd:7453 | q = c + av*(sign(x)*hw + x*2.5) + au*(sign(z)*f + z*2.5) | prepocet sceny: jednotka 2,5 m za zdi domu; 4 pokusy, posun +-1.5 m, meritko x0.93-1.07 | _ves_kompozice | 1 |
| svet.gd:7461-7468 | 3-6 kusu, 0.25-0.8 m od zdi, +-0.9 delky; druhy plevel + grass_medium_02_0 x2 + dandelion_01_0; kopriva 0.45-0.85, jine 0.8-1.2 | pas plevele u zadni zdi nebo boku bez vstupu | _ves_kompozice | 1 |
| svet.gd:7469-7472 | 60 %; roh +1.0 m za zdi; 70 % zadni; meritko 0.6-0.95 | kerik u rohu domu | _ves_kompozice | 1 |
| svet.gd:7489 | rozdil polohy na oblouku > 0.05 | mezera mezi usedlostmi (vo); 101 vzorku oblouku | _ves_kompozice | 1 |
| svet.gd:7492-7494 | rady [885.8, 913.9, 940.2; v 294.6, -1], [857.7, 886.3, 912.9, 942.0; v 361.6, +1]; v posun -6..+2 | mezery v radach bez oblouku (stara naves) | _ves_kompozice | 1 |
| svet.gd:7495-7501 | +-2 m; strom lipa_stredni/dub_stredni/briza_2 x0.75-1.05; 1-3 kere +-3 m x0.7-1.3 | strom + kere v mezere usedlosti (zavira pohled) | _ves_kompozice | 1 |
| svet.gd:7503-7505 | konce [838,322],[842,340],[962,318],[968,336]; s vo [-0.03,9],[0.02,-10],[1.03,8],[0.98,-9] | konce navsi: strom (lipa_stara/dub_stredni/lipa_stredni x0.85-1.15) + 2-4 kere +-3.5 m; rozptyl +-4 (vo) nebo +-6/+-5; 8 pokusu | _ves_kompozice | 1 |
| svet.gd:8216 | _stavby (zricenina, stan, hostinec) | staticke stavby obchazene pesinou | _pes_postav | 1 |
| svet.gd:8217-8230 | kolize exportu velikost >= 0.6 m, mimo tvrz abs(x) < 45 a abs(z) < 50; dlouhy kvadr = retez kruhu, polomer max(tl, delka/kusu)*0.71 + 1.0 | kvadry (ploty, chalupy) obchazene pesinou | _pes_postav | 1 |
| svet.gd:8995 | TRZISTE = false | trziste vypnuto (kod zustava, docs/patche/trziste.md) | _trziste, v_trzisti, uprava_y | 1 |
| svet.gd:8996-9000 | TRZ_O (381.7, 750.9), TRZ_U (0.7317, 0.6816), TRZ_V (0.6816, -0.7317), TRZ_R Rect2(-2, 6.5, 24, 12), TRZ stred ulicky (u 10, v 12.5) | soustava trhu vedle cesty most-ves | trz_bod, v_trzisti, _trziste | 1 |
| svet.gd:9026-9031 | zbozi (zeli_hlavka, salat, bochnik, veka, hrnec_*, okurka, vedro_drevene) a zasoby (bedna_trzni*, sud, pytel_obili, necky, ...) | seznam zbozi stanku | _trziste | 1 |
| svet.gd:9032-9046 | rady v 9.0 / 16.0 (zasoby v 6.8 / 18.6), u 2, 6, 10, 14; zbozi 5 kusu po 0.4 m na desce +0.84 m; stan_jehlan (19.5, 12.5); kul_cedule (-1, 5); koryto_kone (-4.5, 8.8); y -0.02; yaw +-0.03 | rozmisteni stanku trhu (vypnute) | _trziste | 1 |
| svet.gd:9419-9432 | v_trzisti < 1.5 m | rostliny z trhu pryc | _trziste_cisti | 1 |
| svet.gd:10659-10674 | predmety.json katalog; data.staticke (id, p, yaw) | staticke stavby a predmety (bozi muka, hostinec, stan, zricenina) - souradnice v svet.json | _static_items | 1 |
| svet.gd:10676-10678 | obal > 0.5 m vysky a > 0.6 m; polomer max/2 + 1.2 m | _stavby: pesiny je obchazeji | _static_items | 1 |

## Voda

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:7570 | RYBNIK_DIL = not env TVRZ_BEZ_DILU | dil rybnika Lhota zapnut | _ryb_priprav | 1 |
| svet.gd:7571 | RYB_C = (525.08, 879.45) | stred dilu rybnika (misto stareho rybnicku vesnice.py POND) | _ryb_priprav | 1 |
| svet.gd:7572 | RYB_YAW = -0.705 | otoceni dilu (mistni +x -> VES_AU) | _ryb_priprav | 1 |
| svet.gd:7573 | RYB_POL = 30.0 m | polovina dilu 60 x 60 m | _ryb_* | 1/2 |
| svet.gd:7574 | RYB_PAS = 6.0 m | pas za okrajem dilu, kde se teren hry svazi k okraji (+0,30) | ryb_teren, ryb_mrizka | 1/2 |
| svet.gd:7593-7601 | 120 bodu obvodu; dolni decil (0.1) - 0.30 | hladina rybnika = 10. percentil terenu obvodu minus 0,30 (okraj dilu +0,30 nad hladinou); komentar rika kvartil | _ryb_priprav | 1/2 |
| svet.gd:7612 | mrizka 2 m | bunky trojuhelniku dilu pro vysku | _ryb_priprav, _tri_vyska | - |
| svet.gd:7698-7702 | h < hladina + 0.12 | voda nebo bahno dilu: bez travy a rostlin | ryb_voda | 2 |
| svet.gd:7710-7716 | material zem.gdshader z Teren_ves* | teren dilu dostane material terenu vsi | _rybnik_dil | 2/4 |
| svet.gd:7726-7731 | Rybnik_Teren: stin OFF; Rybnik_Voda: material "voda", _hladina; ostatni visibility_range_end 90 m | stiny a dosah dilu rybnika | _rybnik_dil | 3 |
| svet.gd:7883-7884 | kameny_toku (x, z, 0.3, smer) | slapaci kameny jako prekazky toku (polomer 0,3) | _brody | 1 |
| svet.gd:8015 | voda_y z svet.json (vychozi -2.75) | hladina prikopu (shodne s build) | _tvrz_zvencí | 1/2 |
| svet.gd:9716-9718 | kam = kamen_maly_1..5_0, kamen_zula_1/2_0; balv = balvan_zula_1_0, balvan_droba_1_0; kere_v = shrub_02_0/1, bez_cerny_1/2_0, sipek_0 | druhy u potoka | _krajina | 1 |
| svet.gd:9730-9746 | krok 0.8-2.2 m; 60 % kamen na brehu w-0.4..w+1.4 meritko 1.5-4.0 ponor 0.05 naklon 0.4; 20 % balvan v korytu +-0.8w 0.5-1.0 ponor 0.25 -> kameny_toku polomer 0.55*sc | kameny v korytu a na brehu potoka | _krajina | 1 |
| svet.gd:9749-9776 | krok 2-4 m, obe strany; svah = hrana - w - 0.6; narazovy breh (svah > 1.5, vn < -0.3, u < 0.55*-vn): balvan 1.0-2.2 x clamp(svah/5, 0.6, 1.6) ponor 0.5*sc + 3 kameny 2-5 (+-2 m); jinak svah > 1 a 25 %: balvan 0.5-1.3 ponor 0.45*sc | vychozy a balvany v zarezu potoka | _krajina | 1 |
| svet.gd:9777-9782 | 45 %; w + 1.5 + 4*max(vn,0) .. hrana + 3 m; smi_tu_byt; 0.8-1.4 | kere na svahu a hrane zarezu (ne na jesepu) | _krajina | 1 |
| svet.gd:9791-9810 | rakos_/orobinec_ zustane: tvrz abs(x+4) < 80 a abs(z) < 75; nadrz -1.5..0.6 m; potok kraj vody -0.6..+1.5 m | rakos na suchu PRYC (CTVRTA sada hranic tvrze) | _krajina | 1 |
| svet.gd:9812-9829 | mrizka nadrze po 2 bunkach (1 m); d -1.2..0.25; 45 %; +-0.4 m; y = min(teren, hladina) - 0.05; x0.8-1.25 | rakos v pasu bahna u nadrzi a prikopu | _krajina | 1 |
| svet.gd:9866-9868 | stred tvrze (-4.5, 0.4); kamen_zula_1/2_0, kamen_piskovec_1_0, kamen_maly_2/4_0 | kameny prikopu | _prikop_kameny | 1 |
| svet.gd:9876 | nadrz do 20 m od stredu | jen prikop (ne rybnik) | _prikop_kameny | 1 |
| svet.gd:9893-9901 | d -6..0.3, 50 %; +-0.25; most/brana abs(x+3) < 4 a z > 10 vynechat; y < hladina-0.4 nic | pas rozsevu prikopu | _prikop_kameny | 1 |
| svet.gd:9906-9917 | vnitrni d > -1.5, 30 %: plenta kam[2..4] 2.0-3.2 ponor 0.1; vnejsi d > -6, 6 %: sut 1.0-3.0; d > -5, 1.5 %: balvan 0.5-1.1 ponor 0.45*sc; naklon 0.3; y z _vyska_sit | kamenna plenta u hradby, sut a balvany na vnejsim svahu prikopu | _prikop_kameny | 1 |

## Vegetace a rozsev

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:7324-7326 | na ceste a 1,5 m kolem pryc, do 12 m za okrajem posun podle profilu | zadani _cesty_rostliny (komentar); bezi pred _cesty_kameny a _kere | _cesty_rostliny | 1 |
| svet.gd:7336 | mrizka 4 m (_cesty_mriz) | rychly test, zda je strom u cesty | _cesty_rostliny | 1 |
| svet.gd:7342-7346 | odstup_cesty(druh, typ osy) od kraje hliny (cesta_ok) | rostlina blize kraji nez pasma.cesta pryc | _cesty_rostliny | 1 |
| svet.gd:7347 | dy * (1 - smoothstep(hw+1, hw+12, abs(lat))) | rostlina do 12 m za okrajem posunuta o vyrovnani profilu cesty (zarez/nasyp) - POSOUVA uz usazene rostliny exportu | _cesty_rostliny | 1 |
| svet.gd:7527 | sipek_0..2, bez_cerny_1..3_0, shrub_02_0..3 | druhy keru podel cest | _cesty_kere | 1 |
| svet.gd:7532 | seed 8402 | nahoda keru u cest | _cesty_kere | - |
| svet.gd:7539 | osy ves a pesina vynechat | kere jen u cest mimo ves | _cesty_kere | 1 |
| svet.gd:7544 | start 4 + 0..30 bodu | zacatek prvniho shluku na kazde strane | _cesty_kere | 1 |
| svet.gd:7550 | ok + 1.5..6 m; podel +-2 m | stred shluku keru za okrajem hliny (komentar rika 1-6 m / 1,5-4 m) | _cesty_kere | 1 |
| svet.gd:7551 | [1,1,2,2,3,3,4,6] | pocet keru ve shluku | _cesty_kere | 1 |
| svet.gd:7553 | +-2.5 m | polomer shluku | _cesty_kere | 1 |
| svet.gd:7555 | abs(lat) < 1.3*hw + 1.2 -> ne | ker ne v pasmu jine cesty (vlastni pravidlo, ne pasma.cesta) | _cesty_kere | 1 |
| svet.gd:7560 | -0.05; meritko 0.55-1.35 | zapusteni a velikost keru u cest | _cesty_kere | 1 |
| svet.gd:7563 | 6-45 m; x1.6 kdyz divokost < 0.15 | mezera mezi shluky; delsi na kosene louce | _cesty_kere | 1 |
| svet.gd:7890-7892 | pas od 0,3 m ve vode do 1,2 m na brehu | zadani rakosu u rybnika (komentar) | _rybnik_breh | 1 |
| svet.gd:7899 | rakos_1_0, rakos_2_0, orobinec_1_0, orobinec_2_0 | druhy brehu rybnika | _rybnik_breh, _rybnik_breh_dil | 1 |
| svet.gd:7907-7924 | seed 5250; 220 uhlu x 2; pristup abs(a-PI) < 0.45 hust 0.35, jinak 0.95 (sin(a+0.6)>0) / 0.7; k 0.93-1.07 polomeru; 80 % libovolny druh; y = clamp(vyska, hladina-0.4, hladina+0.1); -0.05; x0.8-1.25 | rakos stareho rybnicku (nadrz), kdyz neni dil | _rybnik_breh | 1 |
| svet.gd:7939 | vrba_hlavata_1_0, vrba_hlavata_2_0, olse_mlada_0 | stromy brehu rybnika Lhota | _rybnik_breh_dil | 1 |
| svet.gd:7949-7953 | sum seed 879, frekv 0.18; seed 5251 | shluky rakosu | _rybnik_breh_dil | 1 |
| svet.gd:7954 | volno: lavka Rect2(1.8,2.4,6,6.2), dlabanka (4.6,2.6,5.4,4.2), susak (1.6,8,5.2,4.6) v mistnich x,z dilu | bez rakosu kolem lavky, dlabanky, susaku | _rybnik_breh_dil | 1 |
| svet.gd:7958-7979 | mrizka 0.55 m (+-0.3); vyska hladina-0.3 .. +0.28; napajedlo z < -6 a abs(x) < 4; hus 0.25 + 0.75*smoothstep(-0.1,0.45,sum); ve vode jen rakos; -0.04; x0.8-1.2 | rakos a orobinec Lhota | _rybnik_breh_dil | 1 |
| svet.gd:7982-7998 | max 7 stromu, 400 pokusu, +-24 m; vyska hladina+0.4..+1.3; ne v Rect2(0,0,12,14) (lavka); od sebe >= 7 m; -0.1; x0.85-1.1 | vrby hlavate a olse na brehu Lhota | _rybnik_breh_dil | 1 |
| svet.gd:8009 | nettle_plant_0, grass_medium_02_0, dandelion_01_0, vrba_hlavata_1_0, _2_0 | druhy u hradeb tvrze | _tvrz_zvencí | 1 |
| svet.gd:8017-8023 | seed 1390; obvod hradeb x -27.4..18.3, z -16.4..17.2 | obdelnik hradeb tvrze z exportu | _tvrz_zvencí | 1 |
| svet.gd:8025-8044 | 3 kusy/m obvodu; odstup 0.3 + rnd^1.5*2.2 m; pred branou abs(x+3) < 2.5 a z > z1 volno; y > voda+0.25; 40 % kopriva, 45 % trava, 15 % pampeliska; -0.03; x0.8-1.3 | zarostla pata hradeb | _tvrz_zvencí | 1 |
| svet.gd:8046-8069 | sipek_0, bez_cerny_1/2_0, kapradi_1_0, fern_02_0, kopretiny_0; 9 (kere) / 22 (ostatni) shluku; odstup 0.6-2.2 m; brana abs(x+1) < 5; y > voda+0.3; shluk 1 nebo 2-5 +-0.7 m; -0.04; x0.7-1.15 | kere a kapradi na valu | _tvrz_zvencí | 1 |
| svet.gd:8071-8082 | max 14 vrb, 400 pokusu; elipsa stred (-4.5, 0.4) poloosy 34 x 28 m x0.95-1.25; y voda+0.15..+1.2; ne u brany abs(x+3) < 6 a z > 0; -0.1; x0.85-1.15 | vrby hlavate na brehu prikopu | _tvrz_zvencí | 1 |
| svet.gd:8092 | JEHLICNATE = smrk, borovice, fir_, pine_ | predpony jehlicnanu (kanal R masky) | _stanoviste | 2 |
| svet.gd:8691 | VODNI = rakos, orobinec, vrba, olse | vodni druhy (smi u vody) | smi_tu_byt (?) | 1 |
| svet.gd:8799-8813 | shrub_02_0, sipek_0, bez_cerny_1/2_0, fir_sapling_0; krok z 1.5-6 m, 25 % mezera, 1-4 ks +-1.5 m; x = pata + lom_okraj + 0.5..5; meritko 0.6-1.3, -0.05 | kere na okraji udusane plochy lomu | _lom | 1 |
| svet.gd:8892-8899 | vyska > 6 m, 7 %; 2-4 m za hranou; sklon < 0.6, pes_d > 2.0; y = _vyska_min - 0.15; meritko 0.7-1.1; naklon +-0.08 | borovice na hrane steny (Cesky raj) | _pata_sten | 1 |
| svet.gd:9446-9484 | poradi testu: trh < 1.5 m; voda dilu; lom < 1.0 (krome kamen/balvan); kryti_tab != 0; uvnitr budovy (_uvnitr AABB); sklon > 1.2; tvrz abs(x+4) < 75 a abs(z) < 70 nebo ves do 130 m od (470, 830) -> ano; VODNI -> ano; kamen/balvan v korytu do brehu + 2 m -> ano; pesina _st(3) > 0.5 -> ne; louka < 0.03 a les < 0.1 a skaly < 0.1 -> ne (cesta, voda, dvur) | jedno misto pro vsechny rozsevy: smi tu rust? (louka.gd cte tentyz zaklad) | smi_tu_byt | 1 |
| svet.gd:9487 | SEC_TVRZ = 225.0 m | dosah kosy od tvrze (75 m tvrz + 150 m) | divokost | 1/2 |
| svet.gd:9488 | SEC_VES = 280.0 m | dosah kosy od vsi (130 m ves + 150 m) | divokost | 1/2 |
| svet.gd:9492-9500 | stred tvrze (-4, 0), vsi (470, 830); zvlneni 3 sin*cos + 1.5 sin (+-4 m); prechod 60 m | divokost 0 = kosena, 1 = 60 m za hranici seci | divokost | 1/2 |
| svet.gd:9497-9499 | val x -31.5..22.5, z -20.5..21.5 bez vnitrku x -27.6..18.5, z -16.6..17.4 -> min 0.75 | val mezi hradbou a prikopem nekosen | divokost | 1/2 |
| svet.gd:9503-9515 | ne tvrz/ves; divokost 0; louka > 0.5, les < 0.1, skaly < 0.15, pesina < 0.3, vyska < 25 m; ne v zarezu potoka (strop < vyska+1); ne u nadrze (misto > -6) | kosena louka/pole: tady nesmi byt vychozy, smrky ani kameni | kosena_louka | 1/2 |
| svet.gd:9524-9525 | _les = min(1, jehl + list) | mira lesa | _les | 2 |
| svet.gd:9555-9575 | pridej(druh, x, z, meritko, ponor, naklon, y): ponor < 0 = podil vysky modelu (kameni -0.3 = 30 %); vychozi vyska modelu 0.2 m; meritko x meritko prvni instance druhu; seed hash(x,z) | spolecny pridavac rozsevu krajiny | _krajina.pridej | 1 |
| svet.gd:9579 | seed 750 | nahoda krajiny | _krajina | - |
| svet.gd:9582-9585 | vrba_hlavata*: y - 0.3 m | zapusteni vrby hlavate (pata visela) - POSOUVA instance exportu i z _rybnik_breh_dil/_tvrz_zvencí | _krajina | 1 |
| svet.gd:9587-9598 | kere shrub_02/sipek/bez_cerny zustanou jen kdyz les +-12 m > 0.15, les > 0.1, skaly > 0.1, louka < 0.6 nebo pesina > 0.2 | kere uprostred louky PRYC (i ty z _cesty_kere? - bezi pozdeji, ne) | _krajina | 1 |
| svet.gd:9610-9611 | kere = shrub_02_0/1, sipek_0/1, bez_cerny_1..3_0; kameni = kamen_maly_1..5_0 | druhy rozsevu krajiny | _krajina | 1 |
| svet.gd:9614-9620 | krok 4 m, posun +-1.8 m, okraj 2 m | mrizka rozsevu krajiny | _krajina | 1 |
| svet.gd:9621-9624 | tvrz abs(x+4) < 60 a abs(z) < 55; ves < 110 m od (470, 830) | rozsev krajiny vynechava tvrz a ves (TRETI sada hranic tvrze/vsi) | _krajina | 1 |
| svet.gd:9630-9631 | u > 0.30 -> nic | nejvyssi pravdepodobnost cehokoli 30 % na bod 4 m | _krajina | 1 |
| svet.gd:9633-9636 | les < 0.12, louka > 0.2; les ve 9 m (x1.0) a 18 m (x0.8) | plast lesa 15-20 m | _krajina | 1 |
| svet.gd:9637-9639 | les <= 0.25, skaly <= 0.45, pesina <= 0.55, u < 0.09; sklon z +-2 m | sklon pro balvany na svazich | _krajina | 1 |
| svet.gd:9642 | ponor vychozi 0.05 | zapusteni rozsevu krajiny | _krajina | 1 |
| svet.gd:9643-9645 | okraj > 0.35 a u < 0.30; meritko 0.8-1.4 | ker v plasti lesa | _krajina | 1 |
| svet.gd:9665-9681 | les > 0.25: u < 0.155 mech_1..3_0 0.04-0.08; < 0.165 nalet (pine_sapling_small_0 / ker); < 0.175 bark_debris_01_0..3 (listnaty); < 0.178 dead_tree_trunk_0/_02_0 ponor 0.15; < 0.182 nic; < 0.192 balvan_zula_1_0 / balvan_piskovec_3_0 0.4-0.9 ponor 0.35 | les ve trech patrech | _krajina | 1 |
| svet.gd:9696 | pridej(..., ponor*sc, kamen -> -0.3, naklon 0.25) | spolecne volani | _krajina | 1 |
| svet.gd:9699-9706 | les > 0.6; 1.5-3 m od kmene; les > 0.6, pesina < 0.4; root_cluster_01_0 ponor 0.1 | vyvraceny koren u padleho kmene | _krajina | 1 |
| svet.gd:9708-9710 | poradi: _vychozy -> _pata_sten -> _lom -> potok -> _stromy_u_potoka -> rakos -> rakos u nadrzi -> _prikop_kameny | podkroky _krajina | _krajina | 1 |
| svet.gd:9930-9933 | blizko hrany: < sirka + 0.6, nebo strop < vyska + 0.5, nebo < hrana + 2.0 m | zona potoka | _stromy_u_potoka | 1 |
| svet.gd:9936-9941 | Most_potok AABB grow 4 m | zadny strom ani ker do 4 m od mostu | _stromy_u_potoka | 1 |
| svet.gd:9944 | stromy (_strom_tvar), vrba, olse, kere shrub/bez_/sipek/liska | druhy filtrovane u potoka | _stromy_u_potoka | 1 |
| svet.gd:9958 | ve vode = vzdalenost < sirka + 0.3 m | strom ve vode pryc | _stromy_u_potoka | 1 |
| svet.gd:9961 | briza s meritkem < 0.3 | male brizy pryc vsude (svitici kura) | _stromy_u_potoka | 1 |
| svet.gd:9963 | tvrz abs(x+4) < 38 a abs(z) < 34 | zadny strom u hradby ani v prikopu (PATA sada hranic tvrze) | _stromy_u_potoka | 1 |
| svet.gd:9978-9996 | dub, lipa, buk, briza, smrk blizko hrany pryc (s _daleko verzi stejneho indexu) | u potoka jen olse a vrby | _stromy_u_potoka | 1 |
| svet.gd:9997-10019 | olse kazdych 12-25 m strida strany; sirka + 1 .. hrana + 1.5 m; 40 % olse_mlada, jinak olse_stredni; y - 0.2; x0.8-1.2; + _daleko_0 | olse podel hrany potoka | _stromy_u_potoka | 1/3 |
| svet.gd:10072-10087 | borovice_0 na vrcholu (paprsek na horni plochy, jinak 92 % vysky), y - 0.1, meritko x0.5-0.75 | borovice na vychozu | _vychozy | 1 |
| svet.gd:10088-10092 | 6 kusu: 3 kapradi_1..3_0 (0.8-1.3), 3 kamen_maly (1.0-3.0), 0.5-0.8 sirky od stredu, ponor 0.05 | kapradi a sut u paty vychozu | _vychozy | 1 |
| svet.gd:10223-10224 | keep_low [0.3, 0.6, 1.0], keep_tree [0.5, 0.8, 1.0] podle kvality | podil nizkych rostlin a stromu podle kvality | _plants | 3 |
| svet.gd:10232-10241 | Staticky_* s obalem > 4 x 4 m; AABB zmenseny o 0.1 m | pudorysy statickych staveb (hostinec, stan) - uvnitr zadna trava, kapradi ani kere (_uvnitr) | _plants, smi_tu_byt, _ves_kompozice | 1 |
| svet.gd:10262-10264 | vrba_hlavata* = [] (vsechny) | vrby hlavate skryty (model useknuty valec, ceka na novy z Blenderu) | _plants | 1 |
| svet.gd:10266-10276 | smrk_* a kamen_* na kosena_louka pryc | pravidla stanovist na konci pro vse z rozsevu | _plants | 1 |
| svet.gd:10288-10293 | sipek* = [] (vsechny) | sipek pryc (Misa 0.88: neni realny) | _plants | 1 |
| svet.gd:10383-10384 | divoka_trava, grass_medium_01, grass_medium_02, dandelion* se nekresli | travu dela louka.gd; pampeliska = "hvezdice" na cestach | _plants | 1/3 |
| svet.gd:10406-10419 | VYSKA_BYLIN [min, max] m, hash polohy | skutecna vyska byliny (kopriva 0.25-0.5) - prepise meritko exportu | _plants | 1 |
| svet.gd:10421-10424 | mech/moss/rock_moss meritko > 2 -> 0.8-1.6 / sc | mech exportu zvetseny 25-50x - srovnat (pozn.: randf bez seedu - nedeterministicke) | _plants | 1 |
| svet.gd:10427-10436 | normala z +-0.5 m; jen do 0.3 m od zeme; y = min(y, teren) - 0.03 | mech sklopen podle svahu a 3 cm do zeme - POSOUVA uz usazene | _plants | 1 |
| svet.gd:10437-10438 | low/mid: smi_tu_byt znovu | posledni filtr nizkych a strednich rostlin pri kresleni | _plants | 1 |
| svet.gd:10555-10590 | trava_karta.png, albedo (0.6, 0.64, 0.44), scissor 0.45, roughness 0.85, backlight (0.22, 0.27, 0.08); 3 karty 0.8 x 0.6 m; barva pata (0.55, 0.58, 0.5) | grass_mesh trsu travy vsi (pouziva louka.gd) | _ves_grass | 4 |
| svet.gd:10590-10651 | return - zbytek mrtvy kod: krok [0.95, 0.75, 0.62], seed 1393, hustota x1.1, meritko 0.55-1.2, -0.04, dosah [30, 42, 55] m | travu ve vsi dela louka.gd (mrizka trava_ves) | _ves_grass | 3 |

## Skály, kameny a lom

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:7853-7854 | male kamen_maly_1..5_0; velke kamen_zula_1_0, kamen_zula_2_0, kamen_droba_1_0 | kameny brodu | _brody | 1 |
| svet.gd:7860 | vychozi vyska 0.3 m | neznama vyska modelu kamene | _brody | - |
| svet.gd:7862 | seed 2207 | nahoda brodu | _brody | - |
| svet.gd:7868-7887 | w = sirka+2 m; pricne -2..2 po 1 m (+-0.3), podel po 0.5 m (+-0.15); stred: velky, cil hladina+0.04, sirka 0.55-0.75; jinde maly, vyska 0.07, sirka 0.3-0.5; y dno-0.03 | kameny brodu 5 m siroke, slapaci kameny uprostred | _brody | 1 |
| svet.gd:8159-8174 | skala_* bez _daleko; polomer pudorysu*meritko + 3 m; vrcholy a teziste troj. 0.3-2.2 m nad zemi | body sten skal, od kterych se odsouva pesina | _pes_od_sten | 1 |
| svet.gd:8213 | polomer pudorysu*meritko*0.9 + 2.0 m | kruh skaly, kterym osa pesiny nesmi projit | _pes_postav | 1 |
| svet.gd:8728-8745 | v_lomu < 3.0 m; skala_/balvan_/kamen_ zustavaji | po vsech rozsevech: na plose lomu a 3 m pred ni jen kameni (rostliny PRYC az na konci) | _lom_cisti | 1 |
| svet.gd:8754-8761 | v_lomu < 2.0 m | prvni cisteni lomu (pri rozsevu, pred _lom_cisti s 3 m) - DVA RUZNE PRAHY | _lom | 1 |
| svet.gd:8762 | seed 1393 | nahoda lomu (stejny seed jako ves) | _lom | - |
| svet.gd:8764-8765 | kam = kamen_maly_1..3_0, kamen_zula_1/2_0, kamen_droba_1_0; bal = balvan_zula_1_0, balvan_droba_1_0 | sut lomu ze sede zuly a droby (ne mechovy piskovec) | _lom | 1/4 |
| svet.gd:8770-8778 | 2200 kusu; x = pata + 0.6 + rnd^2.2*11 m; kazdy 4. u pracovist [(8,928),(8.5,940),(14.5,922),(14.5,933.5),(14.5,946)] (x od paty) +-3.5/+-2.2; lom_volno r 0.2; meritko 0.6-2.2, zapusteni -0.25, naklon 0.6 | drobna sut a stepy u steny a pracovist | _lom | 1 |
| svet.gd:8779-8791 | krok z 0.9 m, 14 pokusu; x = pata + 1 + rnd^1.6*9; vyhrazeno 70 % vynechat; lom_volno 0.4; 25 % balvan 0.35-0.9 (-0.35, 0.4), jinak kamen 1.2-3.5 (-0.3, 0.5) | osyp u paty steny (hustsi u paty) | _lom | 1 |
| svet.gd:8793-8797 | 30 bloku; z LOM_Z +4..-4; x pata + 1.5..6; lom_volno 1.0; meritko 1.0-1.8, -0.4, 0.3 | velke odlomene bloky (komentar rika az 15 m od paty) | _lom | 1 |
| svet.gd:8825-8836 | stromy (LISTNACE+JEHLICNATE) tan < 0.9 (~42 st.), ostatni tan < 1.2 (~50 st.) | ve stene nic neroste - rostliny exportu ve strmem svahu PRYC | _pata_sten | 1 |
| svet.gd:8848-8855 | schod abs(dh) >= 3 m a tan >= 1.2 | zbyle kolme schody mrizky = hrany sten | _pata_sten | 1 |
| svet.gd:8858 | seed 6407 | nahoda paty sten | _pata_sten | - |
| svet.gd:8859 | kamen_maly_1..3_0, kamen_piskovec_1/2_0 | sut paty sten | _pata_sten | 1 |
| svet.gd:8866 | svah 53 st. (r2 = vyska/(2*tan53)), jinak k/2 | polobeh svahu terasy | _pata_sten, _bloky_steny | 1 |
| svet.gd:8869-8870 | vynechat abs(x+4) < 90 a abs(z) < 90 (tvrz) nebo do 130 m od (470, 830) (ves) | bez suti u tvrze a ve vsi | _pata_sten | 1 |
| svet.gd:8871-8872 | hrany terasy (e[4]) vynechany | sut terasy vypnuta (levitovala nad travou, radce 18:00 bod 1) | _pata_sten | 1 |
| svet.gd:8873-8890 | dosah 1.5 + 0.22*vyska; 2 + vyska/8 kusu; sklon > 1.1, pes_d < 1.5, mimo louku/les/skaly -> ne; 12 % balvan_piskovec_1/2 0.5-1.1 (y 0.3*, 0.35); 8 % kapradi (jen terasa); jinak kamen exp(N(0.4,0.5)) 0.6-3.5 (-0.3, 0.4) | sut u paty steny | _pata_sten | 1 |
| svet.gd:8900 | _bloky_steny zakomentovano | bloky terasy skryty (radce 18:00 bod 1) | _pata_sten | 1 |
| svet.gd:8912-8945 | seed 1100; hrana >= 5 m, 33 %; od sebe 9 m; balvan_piskovec_1..3_0 meritko 2.2-3.8, -0.5, 0.45 | balvany zapustene do svahu terasy (nepouziva se) | _bloky_steny | 1 |
| svet.gd:8951 | LOM_Z = (906, 975) | rozsah lomu v z | lom_* | 1 |
| svet.gd:8952 | NASTOJATO = krumpac, kladivo_kamenicke | modely nastojato, ve vybaveni lomu se polozi | _lom_vybaveni | 1 |
| svet.gd:8953 | LESENI_Z = (911, 950.5) | lamana cast steny s lesenim (svetla stena, bez osypu) | uprava_y, lom_vyhrazeno | 1 |
| svet.gd:8955 | LOM_SIRKA = 42.0 m | plocha lomu 42 m od paty steny | v_lomu, lom_okraj | 1 |
| svet.gd:8964-8968 | leseni: z LESENI_Z +-1, u < 4.6 m; jerab: z 951.5..960.5, u < 13 m | vyhrazena mista lomu (bez velkych kusu) | lom_vyhrazeno | 1 |
| svet.gd:8971-8988 | z omezeno LOM_Z +-4; od x 100 do 160 po 0.5 m; sraz pokles > 0.8 m/m, konec srazu < 0.25 m/m; +0.5 | pata steny lomu (cache) | lom_stena_x | 1 |
| svet.gd:9056-9058 | kvadr_hruby_1..3.glb (res://modely/predmety/) | 3 varianty kvadru lomu (blender/vlastni.py), MultiMesh = 3 volani kresleni | _lom_sut | 3/4 |
| svet.gd:9070 | seed 9490 | nahoda kvadru | _lom_sut | - |
| svet.gd:9075-9089 | krok z 1.3 m, 5 ks; meritko 0.45-1.0; x = pata + 0.8 + rnd^1.8*6; lom_volno 0.5*sc; y = pata_lom(1.2*sc) - 0.12*sc; naklon +-0.45 rad; protazeni 0.8-1.2 | osypy kvadru u paty steny (ne pod lesenim a jerabem) | _lom_sut | 1 |
| svet.gd:9093-9094 | delky [0.95, 1.35, 0.65], sirky [0.62, 0.7, 0.5] m | rozmery 3 modelu kvadru | _lom_sut | 1/3 |
| svet.gd:9095 | sklady (u od paty, z stredu, delka): (14, 922, 7), (14.6, 933.5, 8), (14, 946, 6), (10.6, 957.6, 3.2) | rucne umistene stohy hotovych kvadru (posledni pod jerabem) | _lom_sut | 1 |
| svet.gd:9097-9124 | 2 rady po 0.82 m; varianty [0,0,0,1,1,2]; protazeni 0.85-1.18; 8 % chybi (mezera 0.5-1 m); mezera 0.04-0.25; vyska 0.85-1.12; natoceni +-0.08 rad, 50 % +180 st.; y pata_lom - 0.02 | spodni vrstva skladu kvadru | _lom_sut | 1 |
| svet.gd:9126-9143 | 55 %; jen pres sparu <= 0.3 m; yt = max vrchu - 0.03; natoceni +-0.12 | druha vrstva kvadru pres spary | _lom_sut | 1 |
| svet.gd:9145-9155 | 60 ks u pracovist [(8,928),(8.5,940),(13,922),(13,933.5),(13,946)] +-3/+-1.6; lom_volno 0.3; meritko 0.25-0.55; y pata_lom - 0.08*sc | odrezky a zmetky u skladu a pristresku | _lom_sut | 1 |
| svet.gd:9186-9194 | material zem.gdshader z Teren_okoli (aktivni) | svisla stena lomu ma material terenu - z kolme plochy dela sedy lamany kamen | _lom_stena_svisla | 2/4 |
| svet.gd:9196-9197 | sum seed 911, frekv 0.35 | zvlneni svisle steny | _lom_stena_svisla | 1 |
| svet.gd:9206-9209 | z LESENI_Z -3.5 .. +3.5, krok 0.25 m; NY = 40 radku | rozsah a hustota site svisle steny | _lom_stena_svisla | 1/3 |
| svet.gd:9215-9216 | vychozi lavice (k 6, vyska paty + 9); nabeh konce 4.5 m; horni hrana q.z + 0.2 + sum*1.4, na koncich pata + 0.6 | vyska steny, konce zapadaji do puvodni steny | _lom_stena_svisla | 1 |
| svet.gd:9218-9221 | bloky 2 m (jz = z/2 + sum*0.6); spara 0.18 m (sirka 0.12) | svisle spary po 1-3 m | _lom_stena_svisla | 1 |
| svet.gd:9224-9236 | dno q.w - 0.8; lavice 1-3 m vysoke (6 lavic), ustup 0.3-1.0 (x0.55); dx 0.12 + ... +-0.2 + sum 0.1; previs u paty 0.2 m do 0.5 m vysky; na koncich 0.3 + h*0.6 | schodovita stena (radce 19:05) | _lom_stena_svisla | 1 |
| svet.gd:9237-9239 | lem: xt - 1.2 (yt + 0.25), xt - 6.0 (max(teren, yt-1) - 0.5) | vodorovny lem nahore 5,5 m dozadu | _lom_stena_svisla | 1 |
| svet.gd:9276-9280 | x 95..190, z LOM_Z -20..+20 | oblast, kde se predmety lomu pokladaji na kreslene troj. site (bunka 2 m) | _lom_sit_priprav | 1 |
| svet.gd:9285 | Teren_obzor, Teren_cesta_kamen, *_sukne vynechany | site mimo pokladani | _lom_sit_priprav | - |
| svet.gd:9302 | abs(normala.y) < 0.35 -> stena, ne podlaha | jen vodorovnejsi plochy pro pokladani | _lom_sit_priprav | 1 |
| svet.gd:9345-9357 | 5x5 vzorku pres pudorys x0.96 (kola x0.8, jen krajni sloupce); -0.01 (kola -0.02) | pata predmetu v lomu = nejnizsi bod pudorysu (proti levitaci) | pata_lom | 1 |
| svet.gd:9360 | NA_BODECH = zebrinak, trakar, koryto_kone, lavice_selska, lavice, lavice_nizka, stul_selsky, stul_prkenny, stul_kozy_dub | predmety s opernymi body (place_on_points) | opory, polozit_na_body | 1 |
| svet.gd:9364-9373 | koryto_kone (+-0.8, +-0.25); trakar (0, -0.45d) x2, (+-0.35w, 0.4d); jinak (+-0.42w, +-0.42d) | oporne body predmetu | opory | 1 |
| svet.gd:9405-9407 | tecna z +-3 m | normala steny lomu | nrm_lom | 1 |
| svet.gd:9435-9436 | lom_okraj = 27.5 + 1.8 sin(0.19z+1.3) + 1.2 sin(0.47z+0.4) + 0.8 sin(1.07z) (23-31 m) | okraj udusane plochy lomu od paty steny; STEJNA funkce v zem.gdshader | lom_okraj, v_lomu, _lom | 1/2 |
| svet.gd:9439-9443 | od paty + 0.3 m do lom_okraj; z LOM_Z | znamenkova vzdalenost od plochy lomu (<0 uvnitr) | v_lomu | 1 |
| svet.gd:9568-9569 | balvan_ u mostu (_u_mostu_jen) vynechat | balvan v najezdu mostu (226, 597) | _krajina.pridej | 1 |
| svet.gd:9601-9609 | kamen_* na kosene_louce pryc | kameni exportu (14 700 kusu, "brouci") v kosene louce pryc | _krajina | 1 |
| svet.gd:9646-9655 | skaly > 0.45, les < 0.9: u < 0.45 kameni exp(N(0.5,0.5)) 0.7-4.0 ponor 0.3; < 0.53 balvan_piskovec_1/2 0.5-1.2 ponor 0.3; < 0.60 ker | sut pod skalami (prakticky u < 0.30 vzdy kameni - prahy 0.45/0.53/0.60 nad 0.30 jsou mrtve) | _krajina | 1 |
| svet.gd:9656-9664 | les > 0.25, jehl > 0.5: u < 0.10 kameni exp(N(0.2,0.5)) 0.5-3.5 ponor 0.3; < 0.13 kamen_piskovec_1_0 0.6-1.4 ponor 0.15 | kameni v boru | _krajina | 1 |
| svet.gd:9682-9685 | pesina 0.5-0.75 (0,8-1,5 m od osy), u < 0.06; exp(N(0,0.45)) 0.5-2.5; ponor 0.3 | kameni na kraji pesiny | _krajina | 1 |
| svet.gd:9686-9694 | sklon > 0.3, louka > 0.1, u < 0.09, 50 %; vyska > 20 m piskovec (Cesky raj), jinak zula/droba (Posazavi); exp(N(0,0.35)) 0.5-1.6; ponor 0.35 | balvany na svazich | _krajina | 1/4 |
| svet.gd:10040-10044 | skala_hlava_0 (+ skala_hlava_daleko_0, skala_hlava_daleko2_0) | model vychozu a jeho dalekych verzi | _vychozy | 1/3 |
| svet.gd:10051-10055 | max 30 vychozu, 4000 pokusu; okraj masky 40 m; les >= 0.3, skaly <= 0.05, mimo tvrz abs(x+4) < 90 a abs(z) < 90, ne kosena louka, pes_d >= 8 m | kde muze byt vychoz (komentar 20-40 kusu) | _vychozy | 1 |
| svet.gd:10057-10060 | prevyseni nad prumerem 8 bodu ve 25 m >= 3 m | jen hrbet nebo vrsek | _vychozy | 1 |
| svet.gd:10061-10065 | vyska 4.0-6.5 m; y = nejnizsi z 8 bodu na 0.45 sirky - 0.5 | velikost a zapusteni vychozu | _vychozy | 1 |

## Vykreslování / LOD / stíny / kolize

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:3169 (pouzito 10465-10489) | STROM_PREP = 40 m (mobil) / 60 m (PC); STROM_DOHLED 120 m; SKALA_LOD0 40, SKALA_LOD1 120, LOD_M 220, BUNKA 24, IMP_BUNKA 1024 (definice mimo muj dil, uvedeno pro uplnost) | prepinaci vzdalenosti pouzite v _plants | _plants | 3 |
| svet.gd:7169 | OKL_BUNKA = 12.0 m | bunka okluzoru terenu (occlusion culling Godotu, CPU rastr); vyska uzlu = minimum 3x3 vzorku po 6 m | _okluzory | 3 |
| svet.gd:7170 | OKL_DOMY = false | krabicove okluzory domu vsi a hostince vypnuty (kamera uvnitr krabice by zakryla vse) | _okluzory | 3 |
| svet.gd:7176-7179 | x -250..900, z -250..1350 | rozsah okluzoru terenu (obdelnik sveta) | _okluzory | 3 |
| svet.gd:7190 | -0.8 m | okluzor terenu 0,8 m pod nejnizsim bodem okoli bunky (nic na zemi nezakryje) | _okluzory | 3 |
| svet.gd:7201,7206 | k = 0.8; AABB > 15 m | krabice domu z obalu _Vnejsek zmensena na 80 %; u hostince jen site s obalem > 15 m | _okluzory | 3 |
| svet.gd:7217-7224 | min 2 m; vyska x0.6, posun -0.2*vyska | krabice okluzoru jen pro obal >= 2 m ve vsech osach; vyska 60 % obalu | _okl_krabice | 3 |
| svet.gd:7238 | plocha^2 < 4e-8 | degenerovany trojuhelnik kolize pryc (kapsle se zasekava; hostinec 537 troj.) | cisti_faces | 3 |
| svet.gd:7259 | 180000 vrcholu (60 k troj.) | vetsi ConcavePolygon kolize se necisti | _kolize_cisteni | 3 |
| svet.gd:7735-7740 | Rybnik_Lavka: ConcavePolygon -> konvexni obalka | kolize lavky (tablet move_and_slide 21-59 ms) | _rybnik_dil | 3 |
| svet.gd:9113,9143,9410-9416 | BoxShape3D velikost x0.95 (x, z) | kolize jen stohu kvadru (osypy a odrezky bez kolize) | _lom_kolize | 3 |
| svet.gd:9168 | visibility_range_end = 140 m | dosah kvadru lomu (MultiMesh) | _lom_sut | 3 |
| svet.gd:9254-9262 | Teren_lom_stena: stin OFF; kolize trimesh z teze site | stiny a kolize svisle steny | _lom_stena_svisla | 3 |
| svet.gd:9573-9577 | balvan_: konvexni obalka; dead_tree: trimesh | kolize pridanych balvanu a padlych kmenu (kolize sveta uz stoji) | _krajina.pridej | 3 |
| svet.gd:10069-10070 | kolize trimesh vychozu | kolize | _vychozy | 3 |
| svet.gd:10374-10377 | ZJEDNODUSIT (LOD0 <= 300 troj., kere 600) | zjednoduseni fotoskenu bylin a keru pri nacteni (meshoptimizer) | _plants | 3 |
| svet.gd:10386-10388 | _daleko krome skal se nekresli jako MultiMesh | daleke stromy resi impostor | _plants | 3 |
| svet.gd:10390-10393 | impostor kdyz _imp_druh; jinak _tvar_mesh (jednoduchy tvar) | K3: za plnym stromem impostor z atlasu | _plants | 3 |
| svet.gd:10397 | keep = keep_low (NIZKE/PODROST), keep_tree, STREDNI 1.0; vyber fmod(k*0.618, 1) > keep | ridnuti podle kvality (zlaty rez) | _plants | 3 |
| svet.gd:10402 | bunka BUNKA 24 m (nizke, stredni, stromy s impostorem/tvarem), jinak 48 m | velikost bunky MultiMeshe (48 200 uzlu = pad) | _plants | 3 |
| svet.gd:10453-10455 | SBER (kopriva, vlastovicnik, barvinek) | mista sberu | _plants | 1 |
| svet.gd:10458-10463 | stiny jen quality > 0; vychozi stin OFF; fade SELF | rozpocet 1500 kresleni / 2 M troj.: stin jen skaly LOD0 a plne stromy | _plants | 3 |
| svet.gd:10464-10476 | impostor: end STROM_PREP, margin 10, stin ON; IMP_BUNKA 1024 m; Color(pata xyz, round(sc*256) + yaw/TAU) | plny strom do STROM_PREP, dal impostor | _plants | 3 |
| svet.gd:10477-10494 | tvar: plny do STROM_PREP (+10), tvar od STROM_PREP-5 (+10) do STROM_DOHLED 120 (+15), stin OFF | jednoduchy tvar stromu bez impostoru | _plants | 3 |
| svet.gd:10495-10506 | skala_*_daleko2: SKALA_LOD1 120 .. 500 m (margin 40); _daleko: SKALA_LOD0 40 .. 120 (10); plna: do 40 (5), stin ON | LOD skal (LOD0 do 40 m jen ta vrha stin) | _plants | 3 |
| svet.gd:10507-10509 | _daleko (ne skala): LOD_M 220 .. [300, 450, 650] | daleke verze ostatnich | _plants | 3 |
| svet.gd:10510-10511 | ma_lod: do LOD_M 220 m | plna verze s _daleko | _plants | 3 |
| svet.gd:10512-10514 | nizke: [18, 25, 40] m, margin 6 | byliny (louka pokryva dal) | _plants | 3 |
| svet.gd:10515-10526 | stredni: [50, 70, 95] m, margin 10; lesni puda (shrub, sipek, bez_cerny, ker_husty, ker_kulaty, fir_sapling, pine_sapling, dry_branches, tree_stump, root_cluster, rock_moss) na mobilu 40 m (6) | dosah stredni vegetace | _plants | 3 |
| svet.gd:10527-10531 | balvan_ [100, 140, 200], kamen_ [60, 90, 120], margin 15 | dosah kamenu a balvanu (drive 450 m) | _plants | 3 |
| svet.gd:10532-10534 | ostatni [300, 450, 650], margin 40 | dosah ostatniho | _plants | 3 |
| svet.gd:10536-10538 | end <= 100 m, begin <= 0, ne SBER/impostor/tvar/skala -> meta "tok" | kratky dosah: uzly jen v okoli hrace (rostliny_rozdel / rostliny_okoli) | _plants | 3 |
| svet.gd:10540-10541 | _impostory(root, imp); _obzor_les deferred | impostory a les na obzoru po rostlinach | _plants | 3 |
| svet.gd:10686-10697 | "boxy" -> BoxShape3D | stan: kolize jen stoly, sudy, platno | _static_items | 3 |
| svet.gd:10698-10710 | kolize "trimesh": ze site <id>_kolize (neviditelna) nebo vsech siti; stin DOUBLE_SIDED | hostinec, stan - da se vejit dovnitr | _static_items | 3 |
| svet.gd:10711-10721 | ostatni: BoxShape3D rozmer katalogu x0.7 (x, z), vychozi 1 x 1 x 1 | kolize predmetu kvadrem | _static_items | 3 |

## Materiály / textury

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:7278-7279 | res://obrazky/cesta/cesta_atlas_a.jpg, _n.jpg | atlas 2x2 Poly Haven CC0 (forrest_sand_01, dry_mud_field_001, rocky_trail, aerial_ground_rock), dlazdici vybira zem.gdshader | _cesty_material | 4 |
| svet.gd:7280 | hlina_k = 0.64 | jas cesty (stred ~140; KCD2 105-128; v 0.82 bylo 0.85 = 186) | _cesty_material | 4 |
| svet.gd:9170-9174 | normal_enabled = false; albedo_color (1.55, 1.52, 1.45) | kvadry bez normalove mapy (v MultiMeshi cerne), zula svetle seda jako fotky KCD | _lom_sut | 4 |
| svet.gd:9245-9246 | barva vrcholu (0,0,0,1); UV = (z, y)*0.3 | meritko UV svisle steny (1 opakovani na 3,3 m) | _lom_stena_svisla | 4 |
| svet.gd:10103 | PUDY = pesina, les_listi, les_jehlici, les_pisek, hrabanka, oblazky, blato, kamen_lisejnik, skala_piskovec | 9 vrstev pole textur povrchu (vrstva 0 na PC cerna -> pesina, kterou shader nepouziva; hrabanka 4; skala_piskovec 8 jen albedo) | _pudy | 2/4 |
| svet.gd:10146-10147 | zastupce 512x512 barva (0.3, 0.27, 0.22) | seda nahradni textura | _pudy_img | 4 |
| svet.gd:10150-10158 | PC bez ETC2: rozbalit, max 512 px, mipmapy; tablet ETC2 beze zmeny | rozliseni pudnich textur | _pudy_img | 4 |
| svet.gd:10166-10186 | nesoulad tvaru -> nejmensi spolecna velikost RGBA8 | sjednoceni vrstev pole | _pudy_sjednot | 4 |
| svet.gd:10196-10201 | tm: les_* 0.7; oblazky, blato 0.75; skala_piskovec 2.5; ostatni 1.0; pudy_k = 0.08 / albedo * tm | kalibrace odrazivosti puda (lesni puda ~0,08; piskovec ~0,2) | _pudy | 4 |
| svet.gd:10208 | pudy_m = 2.2 | parametr shaderu (meritko/mix pud - vyznam v zem.gdshader) | _pudy | 4 |
| svet.gd:10209-10211 | stanoviste, stan_k = trava_kraj.k (2 m), stan_rect | maska stanoviste do shaderu terenu | _pudy | 2 |
| svet.gd:10225 | material trava_divoka | material travy | _plants | 4 |
| svet.gd:10296-10297 | zakladni modely pred _daleko | LOD sdili materialy zakladniho modelu (1 kopie textur v pameti) | _plants | 3/4 |
| svet.gd:10301 | MOD + rostliny/<druh>.glb | zdroj modelu rostlin (druh = klic bez posledniho _N) | _plants | 3 |
| svet.gd:10333-10334 | ALPHA / DEPTH_PRE_PASS -> ALPHA_SCISSOR, prah 0.5 | listi bez pruhlednosti (stinovy pruchod netestuje alfu) | _plants | 3/4 |
| svet.gd:10336-10340 | briza: albedo kury x (0.62, 0.62, 0.6) | kura brizy tmavsi (svitila) | _plants | 4 |
| svet.gd:10342-10356 | _listi_shader pro stromy, bez_, shrub, vrba, ker_husty; tint x TINT_LISTI (sRGB) | listi s vetrem a normalami od stredu koruny; odstin podle druhu | _plants | 4 |
| svet.gd:10361-10368 | skala_* krome _daleko2 -> _skala_detail | detailni material skal | _plants | 4 |
| svet.gd:10371 | briza -> _briza_kmen | uprava kmene brizy | _plants | 4 |
| svet.gd:10680-10685 | materialy pojmenovane podle hernich (data.materialy) -> material() | modely od Misi dostanou stejne fotky jako stavby | _static_items | 4 |

## Ostatní – maska stanoviště, krytí, půdy (podklad pro tabulku 2)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:7270-7283 | je_cesta = true; duplikat materialu "zem" | material cest = kopie terenu s kolejemi, prachem, okrajem (height blend v zem.gdshader) | _cesty_material | 2 |
| svet.gd:8087-8091 | maska stanoviste RGBA, mrizka 2 m: R jehlicnany, G listnace, B skaly (pata + 12 m), A pesina | zem.gdshader vybira povrch (listi/jehlici/pisek/mech/pesina), louka nedava trsy na pesiny | _stanoviste | 2 |
| svet.gd:8441-8447 | data.trava_kraj (x0, z0, k, nx, nz) - mrizka 2 m | mrizka masky stanoviste a louky | _stanoviste | 2 |
| svet.gd:8458-8465 | JEHLICNATE -> R (0), LISTNACE -> G (1), skala_ -> B (2) | kanaly kryti podle druhu | _stanoviste | 2 |
| svet.gd:8468-8471 | koruna 3.0 m vychozi; z impostoru sqrt(polomer^2 - (vyska/2)^2), min 18 % vysky | polomer koruny pro kryti (stin dela koruna 8-12 m) | _stanoviste | 2 |
| svet.gd:8476 | skala: meritko*6 + 12 m; strom: koruna*meritko | polomer vlivu na masku (pata skaly + 12 m) | _stanoviste | 2 |
| svet.gd:8484 | skala lin. 1-dd; strom 1 - smoothstep(0.7, 1.05, dd) | pokles vahy kryti od stredu | _stanoviste | 2 |
| svet.gd:8492-8496 | rozmazani 2x r=2 (5x5 bunek = 10 m); smoothstep(0.25, 0.45, jehl+list) | kryti korunou jen v zapoji lesa (samotny strom v louce nema opad) | _stanoviste | 2 |
| svet.gd:8500-8502 | A = 0.5 + 0.5*sd/3 m, sd vychozi 3.0 | kanal A: znamenkova vzdalenost od osy pesiny +-3 m (pes_dist byl 14. sampler - Adreno) | _stanoviste | 2 |
| svet.gd:8513-8516 | +-3 m * f | pas, ve kterem se pocita vzdalenost od pesiny | _stanoviste | 2 |
| svet.gd:8534-8538 | v_lomu < 3 m | lom = udusana hlina jako pesina (A ~ 0,5), okraj 3 m do louky | _stanoviste | 1/2 |
| svet.gd:8540-8541 | ch[3] = 1 - abs(sd)/3 | CPU maska "pesina do 3 m" | _stanoviste, _st | 2 |
| svet.gd:8550-8556 | poradi: _pes_postav -> maska -> _krajina -> _pudy | stanoviste se pocita z rozmisteni stromu a skal PO vsech upravach | _stanoviste | 1 |
| svet.gd:8568 | KRYTI_SOUBOR = res://modely/louka/kryti.bin | kryti shora z offline casti (TVRZ_ROZSEV=1): bunka 32 m, mrizka 64x64 po 0,5 m (1 = kryto, 2 = cesta) | _nacti_kryti, smi_tu_byt, louka | 1/2 |
| svet.gd:9518-9521 | _st: mrizka 2 m, kanaly 0 jehl, 1 list, 2 skaly, 3 pesina | cteni masky stanoviste | _st | 2 |
| svet.gd:9532-9538 | trava_kraj.m (base64, 0-255) | mira louky z Blenderu (0 = cesta, voda, stavba; pole s nizsi vahou) | _louka_m | 2 |

## Duplicity a rozpory

1. **Hranice tvrze a vsi napsané ručně na mnoha místech, pokaždé jinak** (střed tvrze (−4, 0), jen někde (−4,5; 0,4); střed vsi (470, 830)):
   - `smi_tu_byt` 9467 a `kosena_louka` 9504: tvrz abs(x+4) < 75, abs(z) < 70; ves 130 m
   - `_krajina` rozsev 9621–9624: tvrz 60 × 55; ves **110 m**
   - `_krajina` rákos 9800: tvrz 80 × 75; `_vyska_sit` 9846: 80 × 75
   - `_pata_sten` 8869 a `_vychozy` 10055: tvrz **90 × 90**; ves 130 m
   - `_stromy_u_potoka` 9963: tvrz **38 × 34**
   - `_pes_postav` 8303: x −46..37, z −35..36; kvádry 8219: abs(x) < 45, abs(z) < 50 (střed 0, ne −4)
   - `SEC_TVRZ` 225 / `SEC_VES` 280 (= 75 + 150 a 130 + 150) jsou odvozené z „75 m“ a „130 m“, ale samy tato čísla jako konstanty nemají
   - obrys hradeb: `_tvrz_zvencí` 8020 x −27,4..18,3, z −16,4..17,2 vs. `divokost` 9497 vnitřek −27,6..18,5, −16,6..17,4; elipsa příkopu (−4,5; 0,4) 34 × 28 m
2. **Odstup od cesty má tři různá pravidla**: `pasma.cesta` přes `odstup_cesty` (`_cesty_rostliny`, `_ves_kompozice`); `_cesty_kere` 7555 vlastní abs(lat) < 1,3·hw + 1,2 m; `_cesta_do_kryti` 8632 zakazuje pás 1,3·hw + 0,5 m (krytí 2 → `smi_tu_byt`); kamínky jdou do 1,1·hw. Komentář `_cesty_rostliny` 7324 říká „1,5 m kolem“, kód bere pásma. Výluka pěšin u cesty: komentář „+6 m“, kód ±4 buňky po 2 m (8 m).
3. **Lom se čistí dvakrát s jiným prahem**: `_lom` 8754 v_lomu < 2 m, `_lom_cisti` 8737 < 3 m, `smi_tu_byt` 9451 < 1 m. `_lom_cisti` tak smaže keře, které `_lom` 8810 zasadil na okraj plochy (0,5–5 m za `lom_okraj`) – přežijí jen ty 3–5 m daleko; `_cesty_kere` a `_ves_kompozice` (později) mohou zasadit už od 1 m. `lom_okraj` je jako kopie i v `zem.gdshader` (dvě místa k údržbě). Kvádry ze stohů `_lom_sut` se nezapisují do `_lom_zabrano`, takže suť z `_lom` (`lom_volno`) se jim nevyhýbá (komentář 9272 říká opak).
4. **Mazání celých druhů, do kterých jiné kroky dál sázejí**: `vrba_hlavata*` se v 10262 maže (předtím ji sázejí `_tvrz_zvencí` až 14 vrb, `_rybnik_breh_dil` 7 stromů, `_krajina` ji snižuje o 0,3 m), ale `_ves_kompozice` (scéna 3, 7422) ji přidá až potom → jediná vrba hlavatá ve světě je u chalupy 3. `sipek*` se maže v 10291, a přitom ho sázejí `_cesty_kere` (sipek_0..2), `_lom`, `_tvrz_zvencí` (9 shluků), `_krajina` (keře). `grass_medium_02`, `dandelion_01` se v `_plants` 10383 vůbec nekreslí, takže 60 % rostlin od paty hradeb (`_tvrz_zvencí`: 45 % tráva, 15 % pampeliška) a část pásu u zdí ve vsi je neviditelná.
5. **Pořadí: maska stanoviště není „po všech úpravách“**: komentář 8090 i `_stanoviste` tvrdí, že se počítá z konečného rozmístění, ale volá se v 10247 uprostřed rozsevů (po ní ještě `_les_hustsi`, `_lesni_plast`, `_kere_kulate`, `_ves_kompozice` …) a před `_na_zem`. Pozdní kroky (`_cesty_kameny`, `_cesty_kere`, `_ves_kompozice`) jdou po `_na_povrch`/`_pesiny_volne`/`_stromy_mimo_balvany`/`_kmeny`, takže tyto kontroly na ně neplatí.
6. **Prahy pěšiny se liší**: `smi_tu_byt` _st(3) > 0,5; `kosena_louka` ≥ 0,3; `_krajina` keře > 0,2, kameny na kraji 0,5–0,75; `_pata_sten` pes_d < 1,5 m, borovice > 2 m; `_vychozy` pes_d < 8 m. Kanál A má dosah ±3 m, `PES_DMAX` 4 m – dvě různá pole vzdálenosti od pěšiny.
7. **Prahy sklonu**: `smi_tu_byt` tan > 1,2 (50°); `_pata_sten` stromy 0,9 (42°), ostatní 1,2, suť > 1,1, borovice < 0,6; terasa 53° (`_pata_sten`, `_bloky_steny`); `_lom_sit_priprav` normála.y < 0,35.
8. **Komentář vs. kód**: hladina rybníka „nižší kvartil“ (7591), kód 10. percentil (7601); keře u cest „1,5–4 m, úseky 10–40 m“ (7357) vs. kód 1,5–6 m a mezery 6–45 m; velké bloky lomu „až 15 m od paty“ (8792) vs. 1,5–6 m; výchozy „20–40 kusů“ vs. max 30; `_krajina` pod skalami prahy u < 0,45/0,53/0,60, jenže u > 0,30 se už předtím zahazuje → balvany a keře pod skalami se nikdy nevyberou, vždycky jen kamení.
9. **Semínka**: 1393 používají `_ves_kompozice`, `_lom` i mrtvý `_ves_grass` (stejná řada čísel v různých místech; neškodí, ale je to dvojí použití). Mech v `_plants` 10423 používá `randf_range` bez semínka → při každém načtení jiné měřítko.
10. **Mrtvý nebo vypnutý kód s čísly**: `_ves_grass` po `return` (10590–10651), `TRZISTE = false` (celé tržiště, rovina trhu v `uprava_y`), `OKL_DOMY = false`, `_bloky_steny` zakomentováno, suť terasy vypnutá (8871), `_byliny_rozsev` zakomentováno.
11. **Zapuštění do země bez jednotného pravidla**: −0,03 (hradby, mech), −0,04 (val, rákos Lhota), −0,05 (ves, keře u cest, rákos), −0,1 (vrby, borovice na výchozu), −0,15 (borovice na hraně), −0,2 (olše), −0,3 vrba hlavatá; kamení −30 % výšky.
12. **Krytí cesty**: zápis do `kryti_tab[c][i] = 2` – komentář 8677 připomíná, že starší zápis přes `as PackedByteArray` psal do kopie (cesty v krytí dřív nebyly vůbec). Čtení v `smi_tu_byt` 9457 dál používá `as PackedByteArray` jen ke čtení (to funguje).
