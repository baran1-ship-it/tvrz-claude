# Soupis čísel a pravidel podoby světa – Blender (`blender/`)

Podklad pro tabulky v `pravidla/`. Sloupec **tabulka**: 1 = ZASAZENÍ (pořadí stavby, odstupy cesta/budova/voda/skála/vegetace),
2 = POVRCHY (druhy povrchu, masky), 3 = TŘÍDY (vykreslování, LOD), 4 = MATERIÁLY (rozlišení, měřítko vzoru v m, drsnost).
Souřadnice hry: x vpravo (při pohledu od tvrze k jihu), y nahoru, z od brány ven (+z). Tvrz ≈ (−4, 0), ves (470, 830).
Řádky = stav repa ke dni čtení (jen čteno, nic neměněno).

**Pořadí stavby světa** (`fort.terrain`, fort.py:95–143): Teren 1 m u tvrze → `kraj.tiles` (Teren_ves 2 m, Teren_most 1 m,
Teren_okoli 5 m, Teren_obzor 25 m, Teren_reka) → `near_skirt` → `roads` (Teren_cesta) → `reka` (voda, kameny, most) →
`rocks` (skalní město, kameny u cest) → `outcrops` → `vesnice.build` → `hostinec.build` → `ruiny.build`; potom
`veg.scatter` (vegetace, rozmístí `nove.MISTA`, `kraj.ROCK_PLANTS`, `ruiny.ROSTLINY`, `vesnice.village_trees`, `kraj.plant_spots`)
a `export_game.py` (barvy vrcholů, mřížky `trava_ves`/`trava_kraj`, svet.json). Výška všude = `fort.land()`.

---

## blender/kraj.py (krajina, řeka, cesty, pole, les, skály)

### Pásma terénu a hlavní body
| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| kraj.py:10 | `VES = (470, 830)` | střed návsi | vše (ves_r, hills, pole, les, vesnice, export trava_ves) | 1 |
| kraj.py:11 | `VES_R = 120` | poloměr roviny vsi | hills, fort.land (útlum hrbolů), tree_spots, field_strip | 1 |
| kraj.py:12, 177 | `CROSS = (3, 400)` → po meandru nejbližší bod HLAVNI | křižovatka hlavní cesty a odbočky (boží muka export_game +6.5/+5 m) | ODBOCKA, STAVBY (hostinec) | 1 |
| kraj.py:18 | `NEAR = (−60, 60, −55, 70)` | pásmo 1 m (fort.terrain) | tiles (vynechá), roads (cesta začíná za ním) | 3 |
| kraj.py:19 | `ACT = (−250, 900, −250, 1350)` | pásmo 5 m = herní plocha (stromy, rozsev, trava_kraj) | tiles, tree_spots, outcrops, plant_spots, export trava_kraj | 1/3 |
| kraj.py:20 | `VRECT = (310, 630, 670, 990)` | pásmo 2 m ve vsi (krtince, drobné nerovnosti) | tiles „Teren_ves“, near_skirt | 3 |
| kraj.py:21 | `FAR = (−1500, 2000, −1500, 2600)` | pásmo 25 m (obzor) | tiles „Teren_obzor“ | 3 |
| kraj.py:904–905 | `BRECT` = most zaokrouhlený na 5 m ±40 m | jemný terén u mostu 1 m | tiles „Teren_most“ | 3 |
| kraj.py:907–908 | kroky 2 / 1 / 5 / 25 m | hustota mřížky Teren_ves / Teren_most / Teren_okoli / Teren_obzor | tiles | 3 |
| kraj.py:915 | `y + 11·les·smooth(les)` | obzor: les jako vyvýšená tmavá koruna (+11 m) místo stromů | Teren_obzor | 3 |
| kraj.py:918 | lem dolů 5 m (most) / 8 m (okolí) | svislá sukně proti škvírám mezi pásmy | _skirt | 3 |
| kraj.py:929, 1098, 1113 | `REKA_PAS = 17` m, 1 m napříč, 1.5 m podél (1095), sukně 6 m (1122) | jemný pás terénu podél potoka „Teren_reka“ | _teren_reka, _v_pasu_reky (vynechá okolí do 17−6 = 11 m) | 3 |
| kraj.py:1152–1153 | sukně 3 m | lem pod pásmem 1 m a vsi | near_skirt „Teren_lem“ | 3 |

### Cesty (CESTY)
| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| kraj.py:13–14 | HLAVNI surová osa (0,16)…(−50,2400) | hlavní cesta od brány na jih | _meander | 1 |
| kraj.py:15 | ODBOCKA (CROSS)…(398,766) | odbočka do vsi | _meander | 1 |
| kraj.py:16, 179 | `CESTY = [(HLAVNI, 3.4), (ODBOCKA, 2.8)]` | „šířka“ w: road_near bere polovinu w/2 = 1.7 / 1.4 m; pás hlíny v roads je ±0.75·w (≈ 2.55 / 2.1 m) | road_near, flatten, roads, forest, rozsev | 1 |
| kraj.py:137 | `_meander` krok 6 m, vyhlazení ±2 body | kličkování cest a potoka | _setup_paths | 1 |
| kraj.py:175 | HLAVNI: amp 75 m, vlna 170 m, seed 3.3, náběh 170 m od 75 m (u brány rovně) | zákruty hlavní | | 1 |
| kraj.py:178 | ODBOCKA: amp 60 m, vlna 130 m, seed 7.1, náběh 40 / doběh 45 m | zákruty odbočky | | 1 |
| kraj.py:296 | odbočky ke stavbám: 2.2 (hostinec) / 1.7 (stan) | šířka w odbočky z hlavní (Bézier 9 bodů, start 6 m „po proudu“, ohyb +2.5/−2.0) | CESTY += CESTY_STAVBY (311) | 1 |
| kraj.py:384 | dosah hledání cesty 70 m, buňka 40 m | _Line mřížka | road_near | 3 |
| kraj.py:553–557 | srovnání jen r > 70 m od tvrze, do 26 m od osy | flatten pod cestami | fort.land | 1 |
| kraj.py:559, 575 | jádro 15 cm pod povrchem cesty; přechod hw+0.6 … hw+6 m | srovnaný terén pod cestou | fort.land(flat) | 1 |
| kraj.py:595 | `road_y = land − 0.03` | výška povrchu cesty | roads, deck | 1 |
| kraj.py:1173, 1182 | vzorek 2 m, klouzavý průměr ±3 | podélné vzorkování pásu | roads | 3 |
| kraj.py:1178 | vynechat v NEAR (±2 m, z < NEAR.z1−4) | u tvrze je cesta jen v terénu | roads | 1 |
| kraj.py:1185–1186 | profil napříč (s, dy, g): ±0.75/−0.32/0.8, ±0.45/−0.02/0.3, ±0.22/−0.035/0.0, ±0.12/0/0.08 | koleje uprostřed, krajní hrbol; **g = COLOR.g pásu** (0.08 střed, 0.3 bok, 0.8 vnější okraj) | roads → Godot _cesty_tvar čte G | 1/2 |
| kraj.py:1196 | šířka × (1 + 0.22·perlin(x/25)) | proměnná šířka | roads | 1 |
| kraj.py:1202–1203 | rozbitý okraj 0.28·perlin/7 + 0.14·perlin/2.6 (×0.55 vnitřní) | nepravidelné kraje | roads | 1 |
| kraj.py:1215, 1224 | kamenný úsek: jen vnitřní pruhy, +0.025 m, materiál `kocicky` | „Teren_cesta_kamen“ | roads | 2/4 |
| kraj.py:1231–1233 | kámen: 500 < z < 640 a x < 0 (stoupání), ve vsi < 75 m | místa dlažby | _stone_road | 2 |

### Potok Bystřice a most
| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| kraj.py:181–182 | osa (940,120)…(330,1500), amp 50, vlna 90, seed 11.7, krok 5 m | REKA | river, reka, tiles, veg | 1 |
| kraj.py:385 | dosah 90 m | _REKA_LINE | river | 3 |
| kraj.py:402–404 | dno = min(hills) napříč ±12 m − 2.4; nikdy nestoupá (−0.01/vzorek); max 12 m pod | výška dna | _river_bed | 1 |
| kraj.py:413 | perej = smooth(0.02, 0.3, perlin(x/38)) | brod/peřej 0..1 | river, ground_attrs, kameny | 2 |
| kraj.py:426 | dno + 0.32·perej | mělčí brod | river | 1 |
| kraj.py:432–434 | koryto šířka × (1+0.75·pj); stupeň 0.75−0.35pj na 1.5–2.5 m, +1 m na 2.4–8 m, svah 0.12 za 8 m | povolená výška břehu | hills | 1 |
| kraj.py:534–537 | do 80 m od osy, rozbitý břeh 0.9·perlin/7 + 0.3·perlin/2.6 | zaříznutí údolí | hills | 1 |
| kraj.py:618–621 | hladina = min terénu ±0.8 m + 0.5 − 0.3·perej, vyhlazení ±4 body | hladina potoka | reka | 1 |
| kraj.py:622, 637 | mřížka 1 m, do 11 m od osy | síť Reka_voda | reka | 3 |
| kraj.py:664 | UV = délka po proudu × 0.25, napříč × 0.25 | 1 UV = 4 m | voda_potok | 4 |
| kraj.py:1012–1047 | **barva vrcholů hladiny „Pena“: R = pěna u kamenů, G = peřej, B,A = směr toku 0.5+0.5·(fx,fz)** | maska vody | export_game (Pena zachová), Godot voda | 2 |
| kraj.py:969–1004 | kameny po 0.7 m osy: p = 0.09+0.6·pj, 12 % balvany 0.9–1.7 m, jinak 0.35–0.9; v brodu 4·pj kamínků; břehy 2 kamínky/str. 1.4–3.0·wf, 30 % kámen 1.6–2.6 | kameny v korytu | nove.misto | 1 |
| kraj.py:972 | 5 m od mostu bez kamenů | odstup most/kámen | | 1 |
| kraj.py:454, 467, 472 | most jen když osa odbočky ≤ 6 m od potoka; konce kde osa > 7.8 m; +1.5 m | rozpětí mostu | bridge | 1 |
| kraj.py:561–574 | nájezd: do rozpětí+24 m, koruna 4.8 m (+0.4 šum), svah 1:2.5 (min 5 m), v korytu 4.8–6.6 m ne | násyp | flatten | 1 |
| kraj.py:589 | mostovka +0.3 m nad nejvyšším břehem (±rozpětí, +1.5) | výška mostu | deck_y | 1 |
| kraj.py:600 | nájezd sklon 0.22, do rozpětí+30 m | road_y u mostu | | 1 |
| kraj.py:705–734 | opěry 12 kůlů r 0.13 na 4.6 m, trámy ±0.5/±1.5 (0.28×0.32), fošny 0.2–0.3×4.0 m, piloty po 3.5 m, zábradlí ±2.05 m, výška 1.05 | Most_potok | | 1/4 |

### Kopce, hřeben, ves – výšky
| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| kraj.py:43 | HREBEN (−120,230)…(−120,900) | osa skalního hřebene | ridge, skaly_plan | 1 |
| kraj.py:49–52 | do 160 m, výška 34 m·exp(−(d/70)²), náběh z 200–300, konec 860–960 | hřbet | _hills_raw | 1 |
| kraj.py:56 | seed 77 | perlin permutace (vše deterministické) | perlin | – |
| kraj.py:84–88 | warp 70 m/230 + 28 m/85; elipsa 0.2·sin2a, 0.12 šum | „nekruhová“ vzdálenost od vsi | ves_r | 1 |
| kraj.py:477–482 | 11/150 + 5/65 + 1.5/26 + 0.55/11 m, hřbítky 1.6 | detail krajiny | _hills_raw | 1 |
| kraj.py:491–499 | 200–900 m od vsi, pás 240–380/650–880, výška 58 m, k tvrzi (−0.49,−0.87) nízko (−85 %) | kopečky kolem vsi | _hills_raw, forest (+1.1) | 1 |
| kraj.py:504–510 | útlum u tvrze smooth(140, 330); big 32·smooth(350,1600); mid 8 + 3.5; mikro 0.32/7.3 + 0.14/3.1 | kopce | hills | 1 |
| kraj.py:524–531 | rovina vsi do VES_R+140 (ves_r) nebo 90–140 m (kruh); sklon −0.6 m k východu; míra 0.6; − pond_depth | rovina pod vsí | hills | 1 |
| kraj.py:345–351 | srovnání pod stavbou/ruinou: průměr 8 bodů na 0.8r + střed, přechod 9 m | stavba_pad | fort.land | 1 |

### Stavby, ruiny
| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| kraj.py:219 | stan: 200 m od brány, 10+6 m od cesty, r 7.5; hostinec: CROSS+500 m, 20+8 m, r 12.5 | STAVBY (vpravo = −x, předek k cestě) | stavba_pad, forest, hostinec, export „staticke“ | 1 |
| kraj.py:233 | kostel (220,40) yaw 0.6 r 15; zaniklá ves (300,340) −0.3 r 24; hrádek (−190,540) 1.2 r 17 | RUINY | ruiny, stavba_pad | 1 |
| kraj.py:237, 263 | STRED, PUDORYS hostinec (−6.9..9.6, −2.3..12.2), stan (−4.5..4.5, −3.5..4.5), okraj 0.3 | půdorys bez trávy | v_pudorysu, veg obvody | 1/2 |
| kraj.py:299–306 | plácek r 8.5 m (1.5,−5.2 v modelu); 3 stoly bx −3.9/−0.7/7.4, lavice ±0.6 m | před hostincem | placek, STOLY_VENKU | 1 |
| kraj.py:319 | okraj plácku r−2 … r+1, šum ±2 m | hlína plácku | ground_attrs | 2 |
| kraj.py:325, 333 | stavba r+extra; ruina jádro 0.75·r | odstupy | stavba_near, ruina_near | 1 |

### Pole, les, povrch (masky terénu)
| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| kraj.py:93, 118 | `HON = 125` m, střed ±0.15–0.85 buňky | Voronoi hony | field_strip; **duplicitně shaders/zem.gdshader:58** | 2 |
| kraj.py:96–107 | hash 0x7FEB352D/0x846CA68B, (ci+1000)·73856093 ^ (cj+1000)·19349663 | stejná celočíselná náhoda jako shader | hon | 2 |
| kraj.py:129–130 | směr lánů 0..π, šířka lánu 9–18 m | lány | field_strip | 2 |
| kraj.py:752–753 | pole od ves_r 60+0.5·wob do VES_R+270+2·wob (wob 22 m) | pás polí | field_strip | 2 |
| kraj.py:755–762 | do 110 m od vsi ne v usedlosti (+5 m), rybníku, návsi (|v| < 24+30, −100 < u < 90) | záhumenky | field_strip | 1/2 |
| kraj.py:764–765 | sektor −0.9 < a < 0.55 rad (východ) bez polí | luka a les u potoka | | 2 |
| kraj.py:768 | do 22+6·perlin m od potoka bez polí | luh | | 1/2 |
| kraj.py:771 | `(h>>8) % 5 == 0` → 1/5 honů ladem | louka/pastvina | | 2 |
| kraj.py:773, 777 | mez mezi hony 3 m; mez mezi lány f < 0.09 | meze | | 2 |
| kraj.py:779 | plodina = hash % 4 (0..3) | druh plodiny (kreslí shader) | | 2 |
| kraj.py:742 | les_raw = sin(0.0061x+0.7)cos(0.0049z−1.1)+0.55 sin(..)+0.3 sin(..) | základ lesa | forest | 2 |
| kraj.py:790–804 | les 0 když: < 170 m od tvrze; cesta hw+9; potok 9 m; stavba r+14; pole; < VES_R+25 nebo < 95 m od vsi | odstupy lesa | forest | 1 |
| kraj.py:805–808 | v = raw + 0.6·smooth(500,1600,r) + 0.22·perlin/28 + 1.1·min(1, ves_hills/12); les = smooth(0.38, 0.62, v) | míra lesa 0..1 | ground_attrs, tree_spots, plant_spots | 2 |
| kraj.py:811–845 | **ground_attrs (g, les, pole)**: g výchozí 0.85; pole → g 0.6, pole=1; ves < 90 m g 0.75 − 0.55·yard_dirt; cesta ve vsi pd < 2.5 → 0.08+0.7·smooth; plácek 0.75−0.62·pl; okolí cesty hw+3 → 0.15+0.5·smooth(−0.4,1.6); potok < 6 m → 0.05+0.8·smooth(2.1,3.4) | atributy grass/les/pole terénu | _grid, _skirt, export trava_ves/kraj | 2 |
| kraj.py:1141–1145 | atributy bodů `grass`, `les`, `pole` (FLOAT POINT) | → export_game.py:96 **COLOR terénu: R = pole (0/1), G = tráva g 0..1 (0 = hlína), B = les 0..1, A = 1** | Godot zem.gdshader (COLOR.r pole, .g tráva, .b les; .a dopisuje Godot – koryto/bahno) | 2 |
| export_game.py:103 | ostatní sítě: COLOR = (0.8+0.2·rnd, 0, rnd, 1) | odstín kusu (rnd na plochu) | Godot tint/tint2 | 4 |

### Stromy, rozsev, skalní město
| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| kraj.py:1238 | n = 7000, max 40× pokusů | místa stromů v ACT | veg.scatter | 1 |
| kraj.py:1245, 1259 | ne u stavby (+6 m); ne < 160 m od (−4,0) | odstupy | | 1 |
| kraj.py:1262–1270 | les když forest ≥ 0.5; jinak 5 % solitér, ne u cesty hw+3, ne < VES_R | les / solitéry | | 1 |
| kraj.py:1274 | rozestup² 18 (≈ 4.2 m) les, 30 (≈ 5.5 m) solitér, mřížka 6 m | hustota stromů | | 1 |
| kraj.py:1363–1372 | seed 1394; místa po 28–55 m podél hřebene | skaly_plan | | 1 |
| kraj.py:1381 | bludiště jen 250 ≤ z ≤ 880, od sebe > 95 m, posun ±15 m | zóny skalního města | | 1 |
| kraj.py:1388–1393 | poloměr 48–70 m; pukliny 10–13 × 8.5–11.5 m, kosost ±0.12; soutěska ±0.4·rz šířky 3 m; 5 % mýtinky | geometrie bludiště | | 1 |
| kraj.py:1402 | za okrajem dk < 1.2 jen 3 % jehla (ne do 20 m od stavby) | osamělé jehly | | 1 |
| kraj.py:1407–1411 | ne do 14 m od stavby/ruiny; ne do hw+8 od cesty | odstupy skal | | 1 |
| kraj.py:1412–1435 | výška 1−0.55·smooth(0.25,1,dk); masiv dk<0.5 35 %; měřítko min 0.45; dk<0.9 60 % masiv 2–4 věží, krok 0.4–0.6·šířky | tvar věží | nove.skala | 1 |
| kraj.py:1448–1474 | jen −320<x<−40, 200<z<960; kopec zóny 9 m·exp(−(d/0.85rz)²) do 1.6rz; sutový kužel min(6, 0.2·výška věže) do r+10 m; útlum u staveb r+6…r+35, u cest hw+2…hw+18 | skaly_podstava (zvednutí terénu) | _hills_raw | 1 |
| kraj.py:1502 | 65 % věží (ne nakloněná) borovice na vrcholu 2.5–6 m | ROCK_PLANTS | veg | 1 |
| kraj.py:1513–1532 | rz²·0.22 rostlin v 1.15·rz: 28 % kapradí, 17 % mech 0.04–0.1, 17 % tráva, 18 % keř, 6 % bříza 2–7 m, 14 % borovice 3–12 m | zarostlé rokle | veg | 1 |
| kraj.py:1537–1554 | na zónu 30–50 balvanů/kamenů (σ 30 m, 0.8–3.5 m), 6–12 balvan_piskovec_3 ×1.8–3.2, 40–70 kamínků | sutě | nove.misto | 1 |
| kraj.py:1561–1575 | kameny u krajnic po 6–22 m, w/2+0.3…1.8 m, 85 % 0.15–0.55 m jinak 0.6–1.1 m; ne < 75 m od tvrze, < 60 m od vsi | Skaly_cesty | | 1 |
| kraj.py:1605–1626 | divočina: ne cesta hw+1.2, potok 6 m, tvrz 75 m, dvory 15 m, cesta ve vsi 0.8 m, pole | _wild | outcrops, plant_spots | 1 |
| kraj.py:1637–1660 | 150 skalek, p = 0.15 + rid·1.6; 2–7 kamenů σ 2.5, 70 % 0.5–2.6 m; 3–8 kamínků; na hřebeni (ridge > 2) pískovec | Skalky | | 1 |
| kraj.py:1663–1669 | 700 rozházených kamínků 0.12–0.5 m | | | 1 |
| kraj.py:1679–1698 | 2600 keřových míst (okraj lesa f≈0.35), 1–4 ks ±2.5 m: 35 % shrub_02 0.9–2.2, 25 % šípek 0.8–2.0, 25 % bříza 1.6–5, 15 % smrk 1.2–3.5 | křoví | veg | 1 |
| kraj.py:1700–1721 | 26 000 trsů; mimo 40 m od cesty a 260 m od vsi jen 35 %: 62 % divoká tráva 0.5–1.1, 20 % grass_medium_02, 8 % pampeliška, 6 % kopřiva, 4 % kapradí | trsy | veg | 1 |
| kraj.py:1723–1751 | kraje cest: krok 1–2.2 m, w/2 + 0.7…3.2 m; 4 % keř, 51 % tráva, 20 %, 10 % kopřiva, 7 % pampeliška | lem cest | | 1 |
| kraj.py:1753–1776 | břehy potoka: každý 2. bod, 5.8–9 m od osy, ne do 14 m od mostu, ne na cestě hw+1.5: 10 % vrba 6–10 m, 22 % keř, 23 % kopřiva, 45 % tráva | lem potoka | | 1 |

---

## blender/vesnice.py (ves: layout, usedlosti, náves, rybníček)

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| vesnice.py:15 | seed 1393 | náhoda stavění (latě, sudy…) | | – |
| vesnice.py:963 | `AXIS = atan2(0.85, 1)` ≈ 40.4° (cos 0.762, sin 0.648) | osa návsi | layout, ves_paths, pond, naves_uv; **v Godotu natvrdo 0.76193/0.64764** | 1 |
| vesnice.py:964 | `NAVES = (62, 24)` | polodélka a pološířka návsi | field_strip, molehills, village_trees, meadows | 1 |
| vesnice.py:974 | seed 5 | layout usedlostí (L, W, střechy…) | layout | 1 |
| vesnice.py:981–983 | 2 strany × u = −40, −12, 16, 44 (±3 m), v = ±(24 + 9.5) = ±33.5 m | 8 usedlostí (stít k návsi) | layout | 1 |
| vesnice.py:986–988 | krčma (strana −1, i 0) 14×7.2; rychtář (+1, i 1) 13×7; ostatní L 10.5–12.5 × W 5.6–6.4 | rozměry chalup | | 1 |
| vesnice.py:990, 993 | chlév za chalupou L/2+6.5, kolmo, 5.5–7.5 × 4.5–5.5 | chlév | | 1 |
| vesnice.py:978, 992–994 | střechy šindel/došky/sláma po (k·5+1)%3; krčma a rychta šindel; bílé 30 %; valba 50 % | střechy | | 4 |
| vesnice.py:995–999 | dřevo roubení/tmavé/šedé; bílé spáry 40 %; okna 1–3, 0.42–0.6 m; podsíň 1.9 m (40 %); podlomenice 45 %; sklon 44–54°; ye 2.3–2.6 m; sokl 0.3–0.6 m | varianty chalupy | cottage | 1/4 |
| vesnice.py:47–48 | LOG_H 0.26, LOG_W 0.2 | trám roubení | log_wall | 4 |
| vesnice.py:443–449 | jizba max(5.2, L/2), komora 2.3 (krčma 2.8); okna ±1.3 / ±1.8 | dispozice | | 1 |
| vesnice.py:133, 543 | schod 0.19 m, hloubka 0.36 (0.34) | schody od prahu na terén | door, podsíň | 1 |
| vesnice.py:151–166 | štít: přesah 0.55, u štítu 0.45; došky/sláma deska 0.32 m | roof_gable | | 4 |
| vesnice.py:183–199 | valba: přesah 0.6, hřeben L/2 − 0.35·W, deska 0.34 | roof_hip | | 4 |
| vesnice.py:205–209 | podezdívka od terénu po práh: h = y0 − ypad + 0.25 | plinth | | 1 |
| vesnice.py:595–597, 668 | chlév: podlaha +0.08, ye 2.6, sklon 44–50° | barn | | 1 |
| vesnice.py:685, 694 | laťkový plot h 1.15 m, sloupky po 2 m | picket_fence | | 1 |
| vesnice.py:750, 757 | ohrada z kulatiny h 1.1 m, kůly po 2.8 m | rail_fence | | 1 |
| vesnice.py:1076–1087 | plot ulice v linii štítu (L/2+0.05) od W/2+0.12 do W/2+9.5, vrata 3 m na W/2+2.72; zahrada k −W/2−6.2 s brankou 0.9 m; zadní plot −(L/2+13) | ploty usedlosti | build, in_homestead, yard_dirt | 1 |
| vesnice.py:1089 | zahrádka u −L/2+0.8…L/2−0.6, v −W/2−5.8…−W/2−1.0; řady po 0.85 m, zelí po 0.62–0.75 (85 %) | zahrádky | garden | 1 |
| vesnice.py:1108 | studna c + au·(−6) + av·(−11) | studna na návsi | studna.build | 1 |
| vesnice.py:1112, 949–954 | 25 krtinců, ne < 14 m od chalupy, ne |v| < 22 | krtince | | 1 |
| vesnice.py:1430–1437 | 40 kamenů na kraji návsi (|v| 18–25), 80 % 0.25–0.6 m | naves_stones | | 1 |
| vesnice.py:1022–1033 | plocha pod stavbou = průměr 9 bodů, polovina +0.6 m | _pads | fort.land(pads) | 1 |
| vesnice.py:1040–1050 | jen do 160 m od vsi; přechod 2.5 m | pad_adjust | fort.land | 1 |
| vesnice.py:1120 | `POND = (74, 2, 14, 9)` (u, v, poloosy) | rybníček na horním konci návsi | pond_q, pond_depth, hills; **Godot RYB_C natvrdo** | 1 |
| vesnice.py:1135 | břeh 1 + 0.16 sin2a + 0.09 sin3a + 0.05 sin5a | nepravidelný břeh | | 1 |
| vesnice.py:1142–1148 | do q 1.4; hloubka 1.6 (0.2–0.95) + 0.6 stupeň (0.9–1.04); val −0.3 (1.0–1.38) | dno a val | kraj.hills | 1 |
| vesnice.py:1161 | `POND_LEVEL = 0.28` | hladina pod okolím | pond | 1 |
| vesnice.py:1172–1176 | hladina = min(okraj 1.15×) − 0.28; mřížka 1 m, dosah 1.5×max poloosy | síť vody „voda“ | | 3 |
| vesnice.py:1443–1471 | hlavní cesta u −95 … +73 (41 bodů po 4.2 m), v = 2.5 sin(u/23) + 1.2 sin(u/9+1); odbočky k vratům (Bézier, 5 m rovně ven) pološířka 1.3 | ves_paths | path_dist → ground_attrs (jen barva) | 1/2 |
| vesnice.py:1478 | pološířka hlavní 2 + 3·exp(−((u+6)/30)²) + 0.5 sin(u/7) (≈ 1.5–5.5) | šířka ulice | path_dist | 1 |
| vesnice.py:1384 | usedlost: −(L/2+13) < u < L/2, −W/2−6.2 < v < W/2+9.5 | in_homestead | field_strip | 1 |
| vesnice.py:1389–1409 | dvůr: jádro mezi chalupou, chlévem a vraty (okraj −0.4…1.8 + šum 1.2), pruh u zdi 0.3–1.2 m ×0.85 | yard_dirt 0..1 | ground_attrs | 2 |
| vesnice.py:1207–1211 | okraj budovy 1.5 m | _in_building | export trava_ves (1.6) | 1 |
| vesnice.py:1221–1224 | 7 stromů na návsi (pevná u,v), lípa/dub/bříza 11–17 m | | veg | 1 |
| vesnice.py:1225–1229 | 26 keřů u plotů návsi (|v| 21–26) | | | 1 |
| vesnice.py:1231–1236 | 3 vrby 8–11 m na 1.35–1.5× břehu, 10 keřů na 1.2–1.45× | u rybníka | | 1 |
| vesnice.py:1239–1259 | 1400 trsů na návsi (u −95…85), ne < 0.5 m od cesty; < 1.5 m od cesty výška ×0.6; keře jen > 3 m od cesty | zeleň návsi | | 1 |
| vesnice.py:1264–1272 | sad 2–4 stromy 4–9 m za chlévem; 2–5 keřů u plotu zahrady | | | 1 |
| vesnice.py:1287–1288 | `_HS` výšky trsů: divoká tráva 0.45–1.05, kopřiva 0.35–0.75, grass_medium_02 0.3–0.6, _01 0.25–0.5, shrub 0.8–2.2, šípek 0.8–2.0, kapradí 0.4–0.8, pampeliška 0.2–0.35, weed 0.3–0.7 | seznam druhů + výšky | _clump | 1 |
| vesnice.py:1300–1329 | ploty krok 0.6–1.1 m, ±0.35 m, 75 %; pata zdi L·2.2 trsů; sad 90 trsů; kouty 4–8; zelí 25 | _homestead_green | | 1 |
| vesnice.py:1339–1359 | 2600 trsů v ±120 m (40 000 pokusů), mimo náves |v| < 26, cestu hw+1, dvůr > 0.4; 5 % keř, 2 % strom 2.5–6 m | louky kolem vsi | | 1 |

---

## blender/fort.py (tvrz a terén u ní, `land()`)

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| fort.py:13–14 | vnitřní líc IX 17 / IZ 14; vnější OX 18.8 / OZ 15.8 | hradby | rect_dist, veg, hospodar | 1 |
| fort.py:15–16 | WALK 6.5 (ochoz), BASE −4.5 (pata) | výšky | | 1 |
| fort.py:18–22 | EXT 8 (rozšíření na západ), CX −4, TX −8 | půdorys | | 1 |
| fort.py:43–48 | rozbité břehy příkopu od 1.2–2.5 do 26–40 m: 1.3·perlin/7 + 0.55·perlin/2.6; u mostu (z > 15) rovně do |x| 3.5–8 | | land | 1 |
| fort.py:49–56 | profil: d < 1.5 → −0.35 (berma); 1.5–5.5 sráz na −3.6; 5.5–8.5 dno −3.6; 8.5–12.5 val +2.3 | příkop a val | land | 1 |
| fort.py:57–58 | daleko −1.3 + 1.2 sin·cos − 4·smooth(30,120,r); prolnutí 11.5–34 m | okolí tvrze | land | 1 |
| fort.py:60–64 | amplituda hrbolů 0.15 + 0.2·smooth(2,5) + 1.5·smooth(12,26); u cesty z > 15 ×0.25…1; ve vsi ×0.55 | | land | 1 |
| fort.py:65–71 | `land = profil + bumps + kraj.hills` → flatten (cesty) → stavba_pad → vesnice.pad_adjust (±170 m od vsi) | **pořadí výpočtu výšky** | všichni | 1 |
| fort.py:77–82 | seed 1403: 9 vln (6× 0.06–0.22, 3× 0.3–0.55), 14 dolinek r 4–9 m hl. 0.6–1.4 | bumps | land | 1 |
| fort.py:99–108 | mřížka 1 m x −60…60, z −55…70; uvnitř hradeb y = −0.3 | „Teren“ | | 3 |
| fort.py:125–129 | grass: cesta |x| < 2.2, z > 16 → 0; jinak 0.4 + 0.45·smooth(0.5,2,d); dno příkopu (y < −2.45, d < 13) → 0.1 | maska trávy u tvrze (bez les/pole) | export COLOR.g | 2 |
| fort.py:150–177 | nádvoří 68×56 buněk; pod budovami −0.4; grass smooth(0.8,2.6,dp)·0.75 + 0.35 u zdi (< 1.2 m) | „Nadvori“ | | 2/3 |
| fort.py:577 | brána gx 3.5, z 9.5–17, průjezd ±1.6, střecha patra 10.6 | Brana | | 1 |
| fort.py:646 | `DB_L = 5.0` | padací most | | 1 |
| fort.py:1062–1064 | pevný most z 22–28.6, pološířka 1.75 | Most | | 1 |
| fort.py:836–838 | věž (−19.8…−11.8, −16.8…−8.8), zeď 1.5, výška 17, kamenná do 13 | Vez | | 1 |

## blender/hostinec.py

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| hostinec.py:18 | ZVEDNUTÍ hostinec +0.06, stan −0.04 m | podlaha nad terénem (proti prorůstání trávy) | export „staticke“, build | 1 |
| hostinec.py:21–35 | okna přízemí parapet 1.07 / nadpraží 2.19, patro 3.72 / 4.85 | otvory | build | 1 |
| hostinec.py:49 | `TEXTURY = {dvere_hostinec: [1.0, 1.0]}` | rozměr textury v m | export „textury“ → Godot _size | 4 |
| hostinec.py:178–193 | UV zdiva hostince z krychle, dlaždice 2.5 m; cihly krbu 1.6 m | měřítko vzoru | uprav_model | 4 |
| hostinec.py:208–212 | zdivo_hostinec: zdivo diff/rough/nor 2k | materiál | | 4 |
| hostinec.py:235–243 | dveře 1024×1024, drsnost = zelený kanál DoorCave_drsnost_kov, disp 64×64 šedá | textury dveří | export textury | 4 |
| hostinec.py:58, 97, 100 | lustr 1.68 m, krby, lůžka | vybavení | | – |

## blender/ruiny.py

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| ruiny.py:15 | seed 1420 | | | – |
| ruiny.py:222–225 | 3–5 buků/dubů 13–18 m na r+2…7 m | okraj ruiny | nove.strom | 1 |
| ruiny.py:226–229 | 1–3 kmeny/pařezy 0.5–1.2 | | ROSTLINY | 1 |
| ruiny.py:230–234 | 25 mechů 1–2.5× uvnitř r | | nove.misto | 1 |
| ruiny.py:236–261 | zarůst: 45 % divoká tráva 0.5–1.0, 30 % kopřiva, pak n_kopřiv / n_kapradí / n_bezu / n_náletu (bříza 2.5–6) mimo keep_out | | ROSTLINY, MISTA | 1 |
| ruiny.py:276–281 | kostel loď 12×7 m, zeď 0.95, štít 3–7 m, okna 1.6–3.2 | | | 1 |
| ruiny.py:341–347 | zaniklá ves: 5 domů po 9 m, 7–8.5 × 5–6.5 m, zídky 0.15–0.8 m | | | 1 |
| ruiny.py:413–421 | hrádek: věže ruina_vez_1/2, ovál 32×21 m (±16, ±10.5), zdi 0.4–3.6 m, tl. 1.6 | | STATICKE (trimesh) | 1 |
| ruiny.py:427–431 | 45 sutí 13–18 × 8–12.5 m | | | 1 |
| ruiny.py:437, 446 | keep_out (u/14)²+(v/8.5)² < 1 s 85 %; `_kraj_ruiny(r+5, 120, 40, 12, 14)` | volné nádvoří | | 1 |
| ruiny.py:446 | `P.decimace = ("skala", 30000)` | kámen ruin 113 k → 30 k troj. | Part.commit | 3 |

## blender/veg.py (rozmístění vegetace)

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| veg.py:23 | KEEP grass_medium_01 jen 11 variant | paměť | load_library | 3 |
| veg.py:25 | SKIP pine_tree_01, shrub_01/04, fir_tree_01, saplingy | Poly Haven stromy (miliony troj.) se nepoužijí | | 3 |
| veg.py:80, 93–94 | FLAT {grass_medium_01/02, dandelion, fern_02, weed_plant_02}: měřítko podle šířky | | place | 1 |
| veg.py:107–117 | divoká tráva: 6 variant, 45–80 listů, 0.35–1.0 m, 22 % suchá | vlastní trs | LIB „divoka_trava“ (výška 1.0, šířka 0.35) | 3 |
| veg.py:142 | `WATER_Y = −2.75` | hladina příkopu | water, scatter, export „voda_y“ | 1 |
| veg.py:180–193 | hladina příkopu mřížka 0.7 m, 3 < d < 11.5, jen kde terén < hladina+0.4; ne pod mostem |x| < 2 | | Prikop_voda | 3 |
| veg.py:201–202 | atribut `breh` = hloubka/0.8 | okřehek u břehu | mat_pond | 2 |
| veg.py:270–295 | uvnitř 4200 pokusů: u zdi (< 0.9 m) tráva/kopřiva 0.18–0.5; jinde > 2 m od cestiček 55 %·smooth(2,4) | nádvoří | | 1 |
| veg.py:297–301 | 2500 divokých trsů u paty zdi (< 0.7 m) | | | 1 |
| veg.py:314–355 | venku 16 000: d < 1.6 kopřivy a tráva; < 12.5 louka; dál 60 % | okolí tvrze | | 1 |
| veg.py:357–368 | 42 000 divokých trsů, hustota 1 do 14 m, pak 0.55·(1−smooth(14,30))+0.1; ×1.15 u zdi a vody | | | 1 |
| veg.py:374–400 | 150 keřů/březí na 0.4–4.6 nebo 9.6–26 m od zdi; břízy 1.6–4 / 5–9 m | | | 1 |
| veg.py:402–417 | 60 kamenů s mechem 3.5–12 m, 18 větví 2–13 m, 2 pařezy | | | 1 |
| veg.py:423–445 | les u tvrze: 340 stromů v ±150 m, ne d < 24, ne u cesty (|x|<10, z>0 a |x − 0.25(z−20)| < 9); hustota 0.22 + 0.75·smooth(−20,−60,z) + 0.5·smooth(−20,−70,x); rozestup √14 ≈ 3.7 m; smrk 14–24 (70 %−35 % okraj), bříza 10–17, malý smrk 5–9 | | | 1 |
| veg.py:449–480 | tree_spots: ve skalách (podstava > 2) 70 % borovice 5–14, bříza 6–13; les listn = 0.15 + 0.55·(1 − min(1, (f−0.5)·2.5)): smrk 13–25 (15 % 4–8), dub 11–17, lípa 12–18, bříza 9–16; solitéry 50 % dub 11–19, 30 % lípa 12–20, 20 % bříza 8–16 | druhová skladba | | 1 |
| veg.py:248–254 | dub → dub_stredni/stary, lípa → lipa_stredni/stara (strom v2, min 9 m) | | nove.strom | 3 |
| veg.py:483–503 | potok: olše po 16–34 m, 5.5–9 m od osy (ne u cesty hw+3): 55 % olse_stredni 11–16, 25 % mladá 6–9, 20 % vrba hlavatá 5.5–7.5 | | | 1 |
| veg.py:507–522 | rybník: rákos/orobinec v trsech 4–9 ks na 0.86–1.08× břehu, krok 0.35–0.7 rad (70 %); 7 vrb/olší na 1.3–1.6× | | | 1 |
| veg.py:538–558 | obvod domů: per·1.4 trsů 0.2–2.2 m od zdi (hustší u zdi, ^1.6), ne do 2 m od cesty; 30 % kopřiva 0.6–1.2, 30 % tráva, 15 %, 10 % keř, 10 % pampeliška, 5 % šípek | | | 1 |
| veg.py:575–587 | rákos v příkopu 34 trsů, výška terénu −0.35…+0.2 od hladiny | | Rakos | 1 |
| veg.py:591–607 | rákos u potoka každý 6. bod, 30 %, 3.4–5 m od osy, ne do 16 m od mostu | | | 1 |
| veg.py:145–169 | mat_pond: okřehek podle breh a šumu; drsnost 0.07–0.3 voda, 0.55 okřehek; IOR 1.33 | voda_prikop / voda_potok (tekouci) | GAMEMAT type „rybnik“ | 4 |

## blender/nove.py (balvany, kameny, stromy v2, skalní věže, import SketchUp)

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| nove.py:15–24 | DIM balvanů (2.2–3.12 m), kamenů (0.63–1.36), kamínků (0.14–0.34), žebřiňák 1.73×1.76×6.26, bez černý 2.9–5.3 | rozměry modelů | misto, kraj | 1 |
| nove.py:26–30 | STROMY v2: dub_stary 19.1 m, dub_stredni 13.9, lipa_stara 22.5, lipa_stredni 14.6, buk 15.7, olše 15.8 / 7.7, vrba hlavatá 6.6 / 7.65 | výška modelu | strom (měřítko) | 1/3 |
| nove.py:32 | LOD = STROMY: k nim `<model>_daleko` (karty dál než ~60 m) | LOD stromů | rozmistit | 3 |
| nove.py:33–36 | PODROST kapradí 0.48–0.68, orobinec 1.95–1.98, rákos 2.77–2.82, mech 0.03–0.10, borovice 5.32 | | | 1 |
| nove.py:39–40 | SKALY: jehla 28.3, věž 22.5, hlava 20.6, nakloněná 18.8, masiv 2 věže 31.8, 3 věže 31.3 m (vč. 1 m pod zemí) | skalní věže | kraj.skaly_plan | 1 |
| nove.py:41 | `SKALY_POD = 1.03` m pod terénem | zapuštění | skala | 1 |
| nove.py:50–54 | seznamy hornin: BALVANY_PISKOVEC, BALVANY_POLE (žula, droba, pískovec 2), KAMENY_PISKOVEC, KAMENY_POLE, KAMINKY 1–5 | druhy kamení | kraj, ruiny | 1 |
| nove.py:60–72 | zapuštění sink 0.18·výšky (výchozí); kolize kvádrem jen když výška > 0.45 m, půdorys ×0.82 | | KOLIZE → export | 1 |
| nove.py:153–158 | skála LOD0: voxel 0.15 m → 2700 troj.; LOD1 800, LOD2 150 | LOD skal | add_to_library | 3 |
| nove.py:170–172 | zapečená barva/normála 1024×1024, drsnost 0.92 | | | 4 |
| nove.py:235–237 | `_daleko` a `_daleko2` vyrobeny jen pro LOD | | | 3 |
| nove.py:309–315 | strom v2: y − 0.1 m, yaw náhodně (seed 2026), bez kolize | | veg, ruiny | 1 |
| nove.py:320–328 | SKETCHUP_MAT: roof/tile/shingle → sindel_hra; thatch/straw → dosky_hra; log_end → drevo_rez; bark → kura; plank/floor → prkna_ven; wood/beam → dub_ven; plaster → omitka_ven | mapování materiálů cizích modelů | _import_sketchup (hostinec) | 4 |
| nove.py:360–372 | UV přepočítané krychlovou projekcí v metrech | měřítko = size_m textury | | 4 |
| nove.py:388–389 | zbylé: drsnost 0.9 (kov 0.7), kov 0.6 | bez lesku | | 4 |
| nove.py:331, 396, 410–413 | tris_max 4000, decimace 1°, tex_max 1024 px | rozpočet | predmety | 3/4 |

## blender/lib.py (Part, UV, materiály)

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| lib.py:15 | seed 7 | rnd ploch, jit | | – |
| lib.py:104 | kvádr nafouknut o 0.4–3 mm | proti z-fightingu | box | 3 |
| lib.py:108–127 | **UV kvádru v metrech (1 UV = 1 m)**, posun 0–7, náhodné zrcadlení | měřítko vzoru = size_m textury | box, bb, beam | 4 |
| lib.py:131–133 | zkosení hran mimo zdivo/omítku | bevel | | 3 |
| lib.py:185–187 | lathe UV: délka profilu × obvod (m) | | | 4 |
| lib.py:295–304 | planar UV v m: vodorovné (x,z), svislé (podél, y) | face/mesh bez UV | | 4 |
| lib.py:265–266 | atribut `rnd` (FACE) | odstín kusu → COLOR.b/r | export | 4 |
| lib.py:287–290 | bevel modifier šířka = Part.bevel, 1 segment | | | 3 |
| lib.py:491–492 | GAMEMAT = popis pro Godot; GAME = jedna deska šindele | | export „materialy“ | 4 |
| lib.py:527–547 | wcoord: světové promítání v m (/su), třetí složka hloubka ×0.37; vodorovné když |nz| > 0.7 | „world“ materiály | | 4 |
| lib.py:958–1034 | procedurální materiály (záloha bez fotek): zdivo kryti 0.55 / omítka 0.85 / bílé 0.9 / holé −0.8 / kámen −0.6; dřevo, šindel, dlažba 0.55 m, kočičí hlavy 0.17 m, zem; mat_simple drsnosti (ocel 0.35, mosaz 0.35, saze 0.95, kůra 0.95…) | | Blender render | 4 |
| lib.py:789–791 | mat_simple → GAMEMAT {simple, col, rough, metal} | jediný zdroj drsnosti jednoduchých mat. ve hře | Godot StandardMaterial | 4 |
| lib.py:802–803, 866–867 | trava col (0.13,0.19,0.04), trava_sucha (0.36,0.29,0.14) | GAMEMAT „trava“ | | 4 |
| lib.py:1039 | šindel řada 0.13 m, délka 0.44, bednění 0.03 | shingle_roof | | 4 |
| lib.py:1061–1072 | GAME: jedna deska `sindel_hra`, UV v m po spádu, hřeben 0.18×0.05 | herní střecha | | 3/4 |
| lib.py:1212–1218 | TEX = tex_cache/meta_2k.json: size_m = rozměr Poly Haven (mm/1000) | **měřítko fotek v m** (soubor není v repu) | pbr, export „textury“ | 4 |
| lib.py:1239–1244 | vzorek / size_m; anti-tile 2. vzorek +(0.37,0.61), zrcadlený, maska šum 1.3 (0.45–0.55) | | pbr | 4 |
| lib.py:1260 | GAMEMAT zdivo {omitka, kryti, tint, kamen, spina} | | Godot zdivo.gdshader | 4 |
| lib.py:1298–1300 | GAMEMAT tex {tex, coord uv/world, swap, tint, grey, tint2} — **bump, rough_add, dirt_low, moss se neexportují** | | Godot textura.gdshader | 4 |
| lib.py:1305 | uv + rnd·(3.7, 7.3) | posun textury na kus | | 4 |
| lib.py:1335–1337 | zem: hlína ×1, tráva ×0.7 (vzor 1/0.7 větší), maska grass 0.35–0.6 | Blender zem | (Godot má vlastní zem) | 2/4 |
| lib.py:1354–1409 | mapa materiál → fotka (tint, bump, grey, moss): viz níže | | build_pbr_materials | 4 |

**lib.py:1354–1409 – materiál → fotka (coord; bump; grey; moss; tint2)**: zdivo/zdivo_omitka/zdivo_bile/zdivo_hole/zdivo_kamen → zdivo + omitka_bila (kryti 0.55/0.85/0.9/−0.8/−0.6);
kvadr, kvadr_sedy → piskovec (uv; 0.02; 0.92/1.0; 0.3/0.4; tint2 modravě šedá); omitka, omitka_bila → omitka_bila (world; 0.03); omitka_ven → omitka_kremova (world);
dub, dub_ven, hraz, roubeni, roubeni_bile, roubeni_tmave, roubeni_sede, deska_stodola, drevo_rez → tram (uv, swap; 0.012–0.015; grey 0–0.92); prkna, deska → podlaha (uv; 0.01/0.008);
prkna_ven, sindel → prkna_ven (swap); okenice, dvere → okenice (swap); dlazba → dlazba, dlazba_hrad/dlazba_kus → dlazba_hrad (world 0.03); kocicky → kocicky (world 0.04);
skala → kamen_lisejnik (world 0.05); piskovec_skala → skala_piskovec (uv 0.05); sindel_hra → sindel (uv 0.02 – **fotka „sindel“ není v textures.py ASSETS**); mazanice → malta (world);
mazanice_bila → omitka_bila; dosky_hra, slama_hra → dosky; lata, drevo_plot → drevo_stare (swap); kura → kura; hlina_hra → hlina (world); zem → mat_ground_pbr (hlina + trava).

## blender/textures.py (seznam fototextur – pro tabulku 4)

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| textures.py:11–46 | Poly Haven (CC0): zdivo castle_wall_slates; omitka_kremova beige_wall_002; omitka_bila medieval_wall_01; tram rough_wood; prkna_ven weathered_planks; podlaha old_wood_floor; okenice wood_shutter; dlazba stone_floor; dlazba_hrad monastery_stone_floor; kocicky rock_embedded_floor; piskovec old_sandstone_02; hlina stony_dirt_path; trava grass_path_2; strecha roof_09; kamen rock_surface; malta plastered_stone_wall; dosky thatch_roof_angled; skala_piskovec cliff_side; skala_vrstvy rock_06; kamen_lisejnik lichen_rock; kura bark_brown_02; drevo_stare weathered_brown_planks; hrabanka forest_leaves_02; blato brown_mud_leaves_01; louka_letecky aerial_grass_rock; pole_obili withered_grass; pole_oranice dry_mud_field_001; les_listi forest_leaves_03; les_jehlici forrest_ground_03; pesina forest_ground_05; les_pisek forrest_sand_01; oblazky dry_river_pebbles | názvy fotek ve hře | lib.pbr, export textury, Godot | 4 |
| textures.py:58 | ambientCG: louka Grass004 2.0 m, louka_dal Grass001 2.0 m | svěží louka | Godot zem | 4 |
| textures.py:3, 86, 90 | rozlišení 2k (volitelně 1k); size_m z API (mm → m); mapy diff, nor_gl, rough, disp | | | 4 |
| export_game.py:233–242 | do hry: diff, nor, disp 2k beze změny, **rough zmenšená na 1024** | rozlišení | Godot | 4 |
| textures.py:48–55 | modely Poly Haven (glTF 1k): fir/pine, shrub_01/02/04, nettle, fern_02, weed_plant_02, dandelion_01, grass_medium_01/02, tree_stump_01/02, rock_moss_set_01/02, dry_branches, periwinkle, celandine, moss_01, root_cluster_01/02, dead_tree_trunk(_02), bark_debris_01, pine_sapling_small | druhy rostlin | veg | 1/3 |

## blender/vlastni.py (jen materiály)

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| vlastni.py:13 | generované textury → tex_cache/vlastni/*.png (PIL) | | | 4 |
| vlastni.py:26, 48, 94 | kožešina 1024², koberec 1024×1536, látka 512² | rozlišení | | 4 |
| vlastni.py:799, 955, 1059 | štít 1024 (šířka), pavéza 512×1024, tapiserie 768×1152 | | | 4 |
| vlastni.py:1390, 1427, 1452 | erb 512², prapor 512×1024, vlajka 768×512 | | | 4 |
| vlastni.py:1498, 1517, 1569, 1926 | kůra 512×1024, letokruhy 256², konopí 256², sláma 256×1024 | | | 4 |
| vlastni.py:2207, 3236, 3435 | šumová textura 512², žilky 512², mramorované maso 512² | | | 4 |
| vlastni.py:2549, 2881, 3296, 3364, 3519 | 1024, 512×256, 256, 512, 512 | další generované | | 4 |
| vlastni.py:3737, 3766 | výklenek 256×384; starý šindel 512² (16 řad) | | | 4 |
| vlastni.py:4904, 4914 | erb havrana 512×600 (líc), korouhev 768×512 | | | 4 |
| vlastni.py:110–117 | `_mat` drsnost 0.9 (vlajky 0.85, líc erbu 0.6) | | | 4 |
| vlastni.py:228–251 | `_wood_mat`: fotka `<tex>_diff_2k.jpg` + `_nor_2k.jpg` × tint, drsnost 0.8 (žula 0.92, plachta 0.95) | | | 4 |
| vlastni.py:255–261 | `_plain` drsnost 0.6 | | | 4 |
| vlastni.py:2028–2050, 2102–2103 | `_mat_foto` drsnost 0.85; kůra bark_brown_02 **1k** 0.9, štěpiny rough_wood **1k** 0.8 | polena | | 4 |
| vlastni.py:2233–2245, 2698–2699 | `_noise_mat` 0.8; listy 0.75; sklo 0.08 (3080) | | | 4 |
| vlastni.py:265, 287 | `_box` UV: 1 opakování = 1.2 m (kvádry na voze 0.8 m, 3973) | měřítko vzoru | | 4 |
| vlastni.py:441 | soustružené: obvod ×0.4, výška /1.2 m | | | 4 |
| vlastni.py:3812 | šindel stříšky TEX 1.4 m | | | 4 |
| vlastni.py:4299–4300 | kůl: obvod/0.7 m, délka/1.4 m | | | 4 |
| vlastni.py:4358 | prkno /1.2 m | | | 4 |
| vlastni.py:4729, 4767 | list zelí ×3 (0.33 m), hlína záhonu /1.4 m | | | 4 |
| vlastni.py (seznam fotek) | tram (rough_wood) 2k ×20+ materiálů; zdivo, omitka_bila, kamen (rock_surface), malta – boží muka (3841–3849); zula_kvadr (Poly Haven rock_04, 3971, 4116); kura_kul (bark_brown_02, 4256, 4417); plachta (plachta_tex.py, 3985); hlina (záhon, 4692/4822 – komentář říká dirt_floor, textures.py má hlina = stony_dirt_path: **rozpor**); obrázky obrazky/erby, obrazky/erb/havrani_erb_stit_1024.png, tex_cache/game_icons | použité fototextury | | 4 |

## blender/predmety.py, listnace.py, kit.py, props.py, palace.py, hospodar.py

| soubor:řádek | hodnota | význam | kdo používá | tabulka |
|---|---|---|---|---|
| predmety.py:1–2, 384 | modely Poly Haven 2k (rostliny pro sběr 1k z krajiny, :76) | | | 4 |
| predmety.py:669–672 | strop trojúhelníků 15 000 (modely hráče „ext:“), 40 000 (Poly Haven), jinak `troj` z katalogu | rozpočet | | 3 |
| predmety.py:675–681 | textury max `tex` (výchozí 1024; stavby 2048: stan_kupce :371, ruina_vez_1/2 :377–378; hostinec 1024 :379; stan_velky 1024 :280) | rozlišení | | 4 |
| predmety.py:690–692 | ikona 384 px, 48 vzorků Cycles | | | – |
| listnace.py:18, 48, 180 | karty listí 1024 px (bříza, šípek, dub, lípa, vrba), kůra břízy 1024 | | | 4 |
| listnace.py:259–262 | drsnost listí 0.8, alfa CLIP/DITHERED, oboustranně | | | 4 |
| listnace.py:494–512 | LIB: bříza 4 var. 14 m (š. 4), šípek 3 var. 1.8 m (š. 2), dub/lípa 4 var. 12 m (š. 9), vrba 3 var. 10 m (š. 7) | výchozí výšky druhů | veg.place (měřítko = cíl/výška) | 1/3 |
| kit.py:17 | seed 11 | | | – |
| kit.py:39 | kámen ostění: zkosení 0.035, hrbolatost 0.007 | | | 4 |
| kit.py:67, 118 | prkno: segment 0.3 m, UV v m (délka × obvod průřezu) | | | 4 |
| kit.py:533 | deck: prkna 0.24–0.32 m, tl. 0.06, trámy ±1.3 | | | 1 |
| props.py:28–504 | nábytek (stůl 2.0×0.85×0.78, lavice 0.45, sud r 0.34/0.95…) | rozměry vybavení tvrze | | – |
| palace.py:10–26 | palác X −3…17, Z −14…−7, zeď 0.6, patro 3.9, okap 7.5, polovalba 9.2 | | | 1 |
| hospodar.py:35–38 | kovárna/zbrojnice x −20.5…−3.7, zf 9, střecha 5.3/3.6 | | | 1 |
| hospodar.py:329–331 | stáj u západní hradby, 3 boxy po 3.1 m, střecha 4.4/2.55 | | | 1 |

---

## Druhá pravda (Blender počítá → Godot `scripts/svet.gd` přepisuje / počítá znovu jinak)

1. **Cesty – osa a šířka.** Blender: CESTY (HLAVNI w 3.4, ODBOCKA 2.8, odbočky ke stavbám 2.2/1.7), meandr (kraj.py:175–178),
   pás „Teren_cesta“ s profilem napříč a COLOR.g 0.08/0.3/0.8 (kraj.py:1185), srovnání terénu 15 cm pod cestou (kraj.py:559)
   a `road_y = land − 0.03`. Godot: `_cesty_tvar` (svet.gd:6340) **zpětně rekonstruuje osy z barev vrcholů pásu** (G ≈ 0.078 střed,
   0.298 bok, 0.8 okraj, svet.gd:6354–6359), pološířku počítá znovu `clamp(bd/0.45·0.75, 1.4, 3.0)` (6404/6452), pak pás
   **skryje a vypne kolizi** (6700–6701) a cestu vtiskne do terénu. Vlastní podélný profil: klouzavý průměr ±10 bodů, sklon max
   `CESTA_SKLON 0.14` (5930), zářez/násyp ±3 m (komentář říká 5 m), ve vsi ±0.25 m (5971–5975); `_cesty_napoj` prodlužuje konce až
   30 m (6029); posune i mřížku výšek (`_cesty_vys_mrizka`, 5982). Přidává osy, které Blender nezná: vjezd od mostu tvrze
   (0,28.5)…(2,72) 2.2 m a cesta z lomu 1.8 m (6581–6586), stezky k domům 0.75 m (6633–6656), `PESINY` (8093) a `PES_SIRKA` (8121).
   Kočičí hlavy `Teren_cesta_kamen` (kraj.py:1224, `_stone_road`) jsou ve hře skryté (svet.gd:456–458).
2. **Ves – poloha domů a ulice.** Blender `vesnice.layout()` (8 usedlostí, AXIS, NAVES, seed 5) a `ves_paths`/`path_width` (pološířka
   1.5–5.5 m). Godot (`VES_OBLOUK`, svet.gd:36, scripts/ves_oblouk.gd + pravidla/lokace_ves.json) **přestěhuje usedlosti do oblouku**
   (`_vo_data` 59–230: rostliny, výbava, kolize, ohně, místnosti, pohyblivé díly, výškový posun dy), ulici kreslí jako novou osu
   s pološířkou 1.3–1.9 (6547–6569); stará osa návsi je v Godotu **opsaná vzorcem** 2.5 sin(u/23)+1.2 sin(u/9+1) s jiným ořezem
   šířky 3.2–4.6 (6570–6575). Konstanty vsi jsou v Godotu natvrdo: (470, 830), (0.76193, 0.64764) (svet.gd:42–44, 6573),
   `VES_D/VES_N` (7365). `VES_STARE` (4711–4719) je **ručně opsaný střed/yaw/L/W 7 chalup** z Blenderu (krčma k = 0 chybí) –
   změna seedu nebo layoutu v vesnice.py je rozhodí. Chalupy z Blenderu se vyřezávají (`_ves_site_vyrez`, 5769) a nahrazují
   modely `modely/ves/domy.glb` s vlastními rozměry `DUM_MER` (4722) a vlastní výbavou `DUM_VYB` (4743) místo `vesnice.interior`.
3. **Tráva ve vsi – maska `trava_ves`.** Export (export_game.py:252–264): mřížka 2 m, 121×121 kolem VES, výška v cm,
   m = clamp((g−0.3)/0.45)·(1−0.7·les)·(0.5 na poli), 0 v budově (+1.6 m) a rybníku. (Pro `trava_kraj` jiné koeficienty:
   1−0.75·les, 0.35 na poli, 0 do 3.5·(1+0.75pj) m od potoka – export_game.py:278–283 – tj. ani Blender nemá jedno pravidlo.)
   Godot masku přepisuje: přesune ji s usedlostmi, stará místa = louka 200 (svet.gd:168, 203–207), novou ulici vyřízne na 20
   tam, kde m ≥ 60 (`_ves_maska_ulice` 3782–3807); práh „bez trávy“ je m < 60 (`ves_cesta` 3826). Vlastní trávu ze mřížky
   `_ves_grass` už nekreslí (return 10592) – dělá ji louka.gd.
4. **Výšky.** Blender: `fort.land` = profil příkopu + bumps + kraj.hills (+ řeka, rybník, kopce vsi, skalní podstava) → flatten
   cest → stavba_pad → pad_adjust; sítě Teren_* a mřížky trava_ves/trava_kraj (cm). Godot `_vyska` (3628) čte jen mřížku 2 m
   (odchylka od sítě Teren_ves až 0.5 m, svet.gd:1491) a výšky dál mění: koryto potoka (`koryto.gd`: HLOUBKA 0.6, PAS 17,
   svahy 0.85/0.42/0.2 – místo kraj.river/river_bank/_river_bed), profil cest, `dum_teren` (5163), rybník `ryb_teren` (7669),
   terasa `TERASA` (1110), lom, nájezdy mostu `NAJEZD_DELKA 14` (2291), `uprava_y` (7749), posun usedlostí dy.
5. **Potok.** Blender „Reka_voda“ (hladina 0.5 m nad dnem, mřížka 1 m, barva Pena R/G/B/A, UV 0.25) je ve hře skrytá, pokud
   existuje `modely/reka/reka.res` (svet.gd:454–455); hladinu dělá Waterways z `modely/reka/osa.json` (`_reka` 949).
   Kameny v toku Godot čte zvlášť (`kameny_toku`).
6. **Rybníček.** Blender `POND = (74, 2, 14, 9)`, hloubka 1.6, `POND_LEVEL 0.28`, síť „voda“. Godot `RYBNIK_DIL` (7570) dává
   vlastní díl `Rybnik_dil` na **natvrdo přepočítané** `RYB_C = (525.08, 879.45)`, `RYB_YAW −0.705` (= −AXIS), `RYB_POL 30`,
   `RYB_PAS 6` – změna POND nebo AXIS v Blenderu se nepropíše. Pěšina k rybníku se v Godotu přidává zvlášť (svet.gd:224–227).
7. **Les.** Blender `forest()` → COLOR.b terénu (a +11 m koruna na obzoru). Godot `zem.gdshader:277` bere
   max(COLOR.b, smoothstep(0.6, 1, st.r+st.g)), kde `stanoviste` (svet.gd:8439) **počítá les znovu z instancí stromů**
   (koruna z impostoru, zápoj v 10 m ≥ 0.35). Rozsev a čištění louky (`_krajina` 9544, `kosena_louka` 9503) jdou podle
   stanoviště, `_louka_m` a vlastních hranic seče `SEC_TVRZ 225`, `SEC_VES 280` (9487) – Blender nic z toho nezná.
8. **Pole.** Hony a lány jsou dvakrát: kraj.py:93–132 (`HON 125`, hash, lány 9–18 m, meze 3 m / f < 0.09) a znovu
   v shaders/zem.gdshader:58, 227–237. Blender do COLOR.r dává jen 0/1 (pole), plodinu a meze počítá shader – každá změna musí jít na obě místa.
9. **Materiály.** Blender: uzlové materiály (bump, rough_add, dirt_low, moss, anti-tile) se do hry nepřenášejí. Godot staví
   materiál jen z `GAMEMAT` (type, tex, coord, swap, tint, tint2, grey) + `textury` (size_m) (svet.gd:671–863); drsnost bere
   z mapy rough (1024 px), `HLOUBKA` paralaxy má vlastní (svet.gd:11), velikost bez záznamu = 2.0 m (667), `deska_stodola`
   tint ×1.7 natvrdo (726–727). Materiál „zem“ je v Godotu úplně jiný (atlas cest, louka ambientCG, letecký snímek, pole,
   půdy – 749–799) než Blenderová hlína + tráva ×0.7 (lib.py:1336–1337).
10. **Vegetace a LOD.** Blender rozmístí instance (svet.json „rostliny“); Godot je přetváří: keře shrub_02 → `ker_kulaty`
    (3849), smrky na listnáče (3597), pryč z ulice a dvorů (`_ves_cesty_volne` 3831), keře/kameny pryč z louky (`_krajina`),
    vlastní lesní patra, pláště a rozsev (3937–4466). LOD: Blender předpokládá `_daleko` u ~60 m (nove.py:32); Godot má
    `STROM_PREP` 40 m tablet / 60 m PC, `STROM_DOHLED 120`, `SKALA_LOD0 40`, `SKALA_LOD1 120`, `LOD_M 220`, `ROST_R 115`,
    impostory `IMP_DOHLED 900` (3165–3172, 2804, 3421).
11. **Skryté sítě z Blenderu:** „Skaly“ (svet.gd:461–462), „Teren_cesta“ (6700), „Teren_cesta_kamen“ (456), „Reka_voda“ (454),
    staré chalupy ve „Vesnice*“ (5769); kolize sukní terénu se nepoužívá (466–468).
12. **Místa natvrdo jen v Godotu** (Blender je nezná a nehlídá jim odstupy): `CESTA_UDUSANO` (6265: (0,24), (−71,881), (150,938),
    (461,779)), `VECHET_A/B` (5753), lom `LOM_Z` (8951), tržiště `TRZ_*` (8996, vypnuto), chýše `VES_CHYSE` (4736),
    `CESTICKY_PRYC` (1290), `TERASA` (1110), `PESINY` (8093).
