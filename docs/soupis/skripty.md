# Soupis čísel a pravidel ve skriptech (mimo svet.gd a UI/ladění)

Tabulky: 1 ZASAZENÍ (pořadí stavby, odstupy/pásma cesta/budova/voda/skála/vegetace), 2 POVRCHY (z čeho je zem, druhy, drsnost, vlhkost),
3 TŘÍDY (vykreslování: visibility_range, LOD, impostor, stíny, kolize, načítání/dlaždice, rozpočty), 4 MATERIÁLY (rozlišení textur, měřítko vzoru, drsnost, zákazy).
Řádky odpovídají stavu repa 27. 10. 2026 (jen čteno, nic neměněno).

## louka.gd (tráva, drn, trsy, kupy, pásma u cest)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| louka.gd:12 | BUNKA = 32.0 m | dlaždice louky (rozsev, načítání, MultiMesh na buňku) | celý soubor (_krok, _nacti, _rozsej) | 3 |
| louka.gd:13 | KROK = 0.36 m | rozestup trsů při plné hustotě (±0.45·KROK náhodný posun, ř. 1093) | _rozsej | 1 |
| louka.gd:16,80 | _dosah = 120; setup: tablet 80+10, PC 110+10 m | do kam se načítají buňky louky | _krok, nacti_okoli | 3 |
| louka.gd:17 | UVOLNIT = 24 m | hystereze uvolnění buňky za dosahem | _krok | 3 |
| louka.gd:18 | STROP = 90 buněk | max. buněk v paměti; vyhodí jen o BUNKA vzdálenější (ř. 576) | _strop | 3 |
| louka.gd:21-22 | UROVEN_OD [0,35,65] m, UROVEN_PRO [0,20,50] m | LOD buňky: od jaké vzdálenosti, pro jakou vzdálenost je buffer ořezán | _uroven, _limity | 3 |
| louka.gd:23-24 | HUST_OD 20, HUST_DO 130 m | ubývání trsů s vzdáleností (komentář; v kódu se nepoužívá, skutečně ZANIK + shader hust_do) | (nikdo) | 3 |
| louka.gd:25-26 | KVETY_OD 12, KVETY_DO 45 m | květy (nepoužito, platí ZANIK[1]) | (nikdo) | 3 |
| louka.gd:30 | VRSTVY = 5 | 0 trsy, 1 květy, 2 drn, 3 vysoká tráva, 4 vějíř | celý soubor | 3 |
| louka.gd:31 | ZANIK [[20,110],[12,45],[12,45],[20,110],[40,60]] m | od–do zániku po trsech pro každou vrstvu; visibility_range_end = ZANIK[k][1]+30 (ř. 819) | _podil, _postav_cast | 3 |
| louka.gd:32 | DRN_KROK = 0.35 m (~8/m²) | mřížka výplně (drn/vějíř/směs) | _rozsej | 1 |
| louka.gd:33 | ROZSEV = res://modely/louka/ (kryti.bin) | offline zakrytí shora | rozsev_vse, _nacti_kryti | 3 |
| louka.gd:34 | ZAZNAM = 12 B/trs | formát záznamu (x,z u16, y s16 cm, druh, hash) | _zaznam, _nacti | 3 |
| louka.gd:35 | VLAKEN = 2 | souběžné načítání buněk | _krok | 3 |
| louka.gd:36-39 | KUPY [[64 m, 45, 280, 1.2–2.0, pokr. 0.85], [128 m, 240, 650, 2.6–4.2, 0.4]] | „impostor“ trávy: buňka, od–do, měřítko, pokrytí | _krok, _kupy_vlakno, _kupy_uzel | 3 |
| louka.gd:44,101 | _voda_y = -2.75 (z data voda_y) | hladina pro „sucho“ | _sucho | 1 |
| louka.gd:79 | hustota = [0.45, 0.7, 1.0][quality] | hustota trávy podle kvality (drn/vějíř vždy 1.0, ř. 139) | setup, _podil | 3 |
| louka.gd:99-100 | stavba > 4×4 m, AABB.grow(-0.2) | statické stavby (Staticky_*) bez trávy uvnitř | setup, _vzorek | 1 |
| louka.gd:104-107,1071-1075 | šum seed 1393 freq 0.045; seed 77 freq 0.16 | rozložení druhů trsů / suchých skvrn (2× zadané!) | setup, _sumy | 2 |
| louka.gd:110 | _trs: 3 karty, ATLAS_POMER, výška 1, vítr 1.0, bez karty shora | síť trsu | setup, _karta_mesh | 3 |
| louka.gd:111-112 | 4 barvy květů (žlutá, bílá, růžová, fialová) | atlas květů 512×128 | _kvety_atlas | 4 |
| louka.gd:118-119 | drn: atlas trava_nizka_atlas.png 3×1, výška 0.12–0.2 m, vítr 0.6 | nízká tráva | setup | 4 |
| louka.gd:120-121 | vysoka: trava_vysoka_atlas.png 3×2, výška 0.65–1.1 m, vítr 1.3 | vysoká tráva na okrajích | setup | 4 |
| louka.gd:125 | vějíř: vejir_atlas.png 2×2, 0.12–0.18 m | výplň | setup | 4 |
| louka.gd:128 | hust_do trsů: tablet 80, PC 110 m | shader ztenčení trsů | setup | 3 |
| louka.gd:130-133 | vějíř hust_od 15, hust_do 40, zbytek 0.25, konec 40 | pásma vějíře v shaderu (vs. _podil 15/40/60 a ZANIK [40,60]) | setup | 3 |
| louka.gd:138 | jas = 0.85 | jas všech vrstev trávy | setup | 4 |
| louka.gd:140 | kupa: 3 karty šíře 1.9, výška 0.6, ořez 0.3, ponor 0.08, vítr 0.25 | síť kupy | setup | 3 |
| louka.gd:145 | barva terénu: trsy/vysoká 40–80 m, drn 20–40, vějíř 30–70, kupy 0–1 | od kdy tráva přebírá barvu terénu (KCD use_terrain_color 80 m) | setup | 4 |
| louka.gd:160-170 | mřížka 4 m (9×9), okolí 6 m | okraj lesa = zhuštění pásu trsů | _okraje, _okraj | 1 |
| louka.gd:184 | sucho: y > voda_y + 0.3 | tráva jen nad vodou +0.3 m | _sucho | 1 |
| louka.gd:199-200 | pás u zdi stavby 2.5 m, hustota až 0.85 | zarostlé u zdi | _vzorek | 1 |
| louka.gd:232-245 | maska stanoviště po 2 m, A = 0.5 + vzdál./6 m | vzdálenost od osy pěšiny | _vzorek | 1 |
| louka.gd:251 | smoothstep(1.4,1.9) | přechod znaménková/bez znaménka | _vzorek | 1 |
| louka.gd:252-258 | lat < 1.2 m; pes_f = smoothstep(0.72, 1.05, lat ± 0.1 + šum 0.08) | tráva začíná 0.72–1.05 m od osy pěšiny (= okraj hlíny v zem.gdshader 0.45–0.7) | _vzorek | 1 |
| louka.gd:261 | les: −90 % (smoothstep 0.6–1.0 R+G); skály −80 % (0.3–0.7 B) | pod korunami / v soutěsce | _vzorek | 1 |
| louka.gd:266-269 | val tvrze abs(x+4)<36, abs(z)<32 → min 0.75 | tráva na valu a břehu příkopu | _vzorek | 1 |
| louka.gd:272-276,1019,1208 | nádvoří x −27.6…18.5, z −16.6…17.4 (4× ručně) | nádvoří = udusaná hlína, trsy jen pás 1.2–2.8 m u zdi, hustota 0.7 | _vzorek, _nadvori, _rozsej | 1, 2 |
| louka.gd:281-282 | rybníček ve vsi: −14 < dk < −0.5 m → 0.85 | tráva na břehu od 0.5 m | _vzorek | 1 |
| louka.gd:286-287 | rybník Lhota: výška > ryb_y + 0.12; smoothstep 0.12–0.4 → 0.85 | suchý břeh | _vzorek | 1 |
| louka.gd:288-293 | potok: mřížka 16 m; 0.7 < e < 9 m, útlum 6–9 m, hustota 0.8 | tráva u potoka | _vzorek | 1 |
| louka.gd:298-299 | mimo abs(x+4)<80, abs(z)<75: sklon 1.2–1.6 (≈50–58°) → bez trávy | skalní stěna bez trávy (kolem tvrze nikdy) | _vzorek | 1, 2 |
| louka.gd:303-305 | terasa: sklon 0.85–1.15 ±0.125 | svah terasy bez trávy | _vzorek | 1 |
| louka.gd:308-315 | 0 v budově, zahradě, záhonu (v_nove_zahrade==2), tržišti (< −1+šum·1.5), rybníku, lomu (< −0.5) | vyloučení trávy | _vzorek | 1, 2 |
| louka.gd:421,429 | přestavba LOD: rezerva 10 m, ztenčení d−20 m | priorita načítání | _krok | 3 |
| louka.gd:451 | viditelnost buňky každý 4. snímek | aktualizace visible_instance_count | _krok | 3 |
| louka.gd:454 | kupy: každý 3. snímek jedno pásmo; dosah + 0.75·bk, uvolnění + 2·bk | načítání kup | _krok | 3 |
| louka.gd:534-535 | uvnitř budovy: tráva jen do 20 m | interiér | _podil | 3 |
| louka.gd:538 | vějíř: plný do 15 m, 15–40 m na 25 %, 40–60 m zánik, ×1.1 | pásma vějíře | _podil | 3 |
| louka.gd:540-541 | tablet: trsy a vysoká tráva max 80 m | mobil | _podil | 3 |
| louka.gd:544 | ×1.1 rezerva podílu | — | _podil | 3 |
| louka.gd:763 | _vypnute = [2, 4] (drn a vějíř vypnuty), env TVRZ_LOUKA_VYP | vrstvy vyřazené („hvězdice“) | _postav_cast, _rozsej | 3 |
| louka.gd:764-765 | PLNIT 400 instancí; ROZPOCET_US 3000 µs/snímek | rozpočet stavby louky | _krok, _plnit | 3 |
| louka.gd:803 | AABB +1.5 m do stran, −0.5…+2.5 m | culling buňky | _postav_cast | 3 |
| louka.gd:818,935 | stíny trávy VYPNUTO (kupy stin=false) | stíny | _postav_cast, _mm | 3 |
| louka.gd:890,933-934 | fade 14 m; visibility_range_begin = od−20, end = do+30 (shader) | prolínání kup | _mm, _mat_pas | 3 |
| louka.gd:953 | KRYTI_K = 0.5 m (64×64 na buňku) | mřížka paprsků shora | _kryti | 1 |
| louka.gd:973-988 | hrubě po 2 m, jemně 0.5 m v okolí 6×6 m | paprsky shora (střecha/stůl/skála = bez trávy) | _kryti | 1 |
| louka.gd:1000-1001 | paprsek y+9 … y−2 m | výška paprsku | _zasah | 1 |
| louka.gd:1010-1013 | Teren*/Nadvori*/Rybnik_Teren* = terén; terén o 0.5 m níž = převis | co se počítá jako zem | _zasah | 1 |
| louka.gd:1024-1031 | průměr okolí 5 m (4 vzorky), cache 2 m | pás za okrajem cest | _okoli_hust | 1 |
| louka.gd:1038 | nízká = nádvoří nebo nová zahrada (==1) | sešlapaná tráva | _nizka | 2 |
| louka.gd:1062-1064 | zářez potoka: hrana > b2 + 1 + 4·b3; smoothstep 0.5–1.4 | vysoká tráva ve svahu zářezu | _zarez | 1 |
| louka.gd:1097-1098 | okraj lesa +0.5 | zhuštění | _rozsej | 1 |
| louka.gd:1099-1106 | divokost: ×1.5 trsů (rng > v·1.6·(1+0.5·div)), ×1.3 výška (ř. 1133) | neudržovaná louka | _rozsej | 1, 2 |
| louka.gd:1102-1105 | pás krytí cesty: cesta_trava.x > 0.9 → hustota okolí, lat ≥ 3 | tráva za okrajem cesty | _rozsej | 1 |
| louka.gd:1110-1112 | typ: n1 < 0.45 nízká, < 0.72 střední, jinak vysoká; n2 > 0.72 suchá | druh trsu ze šumu | _rozsej | 2 |
| louka.gd:1113-1117 | v < 0.45 nebo lat < 1.6 m → jen nízká, 50 % vynechat | lem cest | _rozsej | 1 |
| louka.gd:1118-1119 | 25 % náhodný typ | promíchání | _rozsej | 2 |
| louka.gd:1120 | velikost 0.75–1.25 × (0.85–1.15 podle hustoty) | měřítko trsu | _rozsej | 3 |
| louka.gd:1123-1131 | druhy: 0 nízká 0.36 m, 1 nízká 0.5, 2 střední 0.6, 3 vysoká 0.82, 4 suchá 0.6 (tab. v stebla.gdshader) | druhy trsů | _rozsej | 2 |
| louka.gd:1133 | y − 0.04 m (trsy), −0.03 (byliny), −0.02 (drn/vějíř) | zapuštění paty | _rozsej | 1 |
| louka.gd:1134-1144 | byliny 22 %: 5 jitrocel 0.28 m, 6 kapradí 0.55 (v<0.45, 30 %), 7 drobné květy 0.32 (18 %) | byliny | _rozsej | 2 |
| louka.gd:1148 | květy: 0 × … (vypnuto, pravidla_sveta kvety hustota 0) | skupinky 16×16 m, 14–40 ks, r 0.8–2.2 m, měř. 1.1–1.9 | _rozsej | 2 |
| louka.gd:1181 | brod: kb0 > kb2 + 1.5 | ne v potoce | _rozsej | 1 |
| louka.gd:1198-1204 | hřbet cesty: ct.x ≤ 0.9; pravd. ct.x·0.4·clamp(okolí·1.3, 0.15, 1); výška 0.55, šíře 0.5–0.8 | tráva mezi kolejemi | _rozsej | 1 |
| louka.gd:1211 | pod vozem/lavicí: jen vějíř | krytí shora mimo cestu | _rozsej | 1 |
| louka.gd:1219-1220 | hranice ±0.5 m šum + 2 vlny po 0.25 | roztřepený okraj u cest | _rozsej | 1 |
| louka.gd:1224-1232 | svet.pasmo_cesty(typ osy): drn_m, trsy_od_m; lz ≤ 1.59·dkr/trs_m | pásma cest z pravidla_sveta.json pasma.cesta | _rozsej | 1 |
| louka.gd:1233-1240 | lz < 1.6 = lem; v drn_m sešlapaný drn: ponechat 0.1 + 0.6·smoothstep | lem cest | _rozsej | 1 |
| louka.gd:1244,1258 | nízká z atlasu [0,0,1,1,1,2] | výběr buňky atlasu | _rozsej | 2 |
| louka.gd:1247-1248 | lz 0.9–1.6: nízké stojící trsy 0.55×0.5 | pás u cesty | _rozsej | 1 |
| louka.gd:1251 | hash výplně < 110 (≈0.43) | výplň kvalita neubere | _rozsej | 3 |
| louka.gd:1268 | vysoká: buňky [0,2,3,5] | druhy vysoké trávy | _rozsej | 2 |
| louka.gd:1291-1310 | výplňový mix (kosená / divoká / les / voda): vějíř 0.48→0.08→0.7→0.5; nízká 0.2→0; suchá 0.1→0.15; byliny 0.22→0.12→0.05; trsy 0→0.25; kapradí les 0.3; zbytek vysoká | směs výplně podle stanoviště (komentář ř. 1288 uvádí jiná čísla 60/20/10/10!) | _vyplnovy_mix | 2 |
| louka.gd:1315-1318 | práh masky 0.12 ± 0.12 + vlna 0.08, clamp 0.02–0.3 | okraj louky | _prah | 1 |
| louka.gd:1350 | počet kup: plocha/kupa · pokrytí · 1.3 · (0.6–1.0 podle hustoty) | hustota kup | _kupy_vlakno | 3 |
| louka.gd:1355 | kupa jen při v ≥ 0.12 | — | _kupy_vlakno | 1 |
| louka.gd:1358-1360 | měřítko × 0.8–1.2, výška × 0.7–1.1 × 0.9–1.25; zapuštění 0.08·s | kupy | _kupy_vlakno | 3 |
| louka.gd:1362 | kupa suchá při šumu > 0.72, jinak 70 % buňka 0 | druh kupy | _kupy_vlakno | 2 |
| louka.gd:1382,1408 | atlas květů 512×128, obrázek 128 px | rozlišení | _kvety_atlas, _kvet_img | 4 |
| louka.gd:1394-1395 | květ 0.44 × 0.42 m (2 karty) | síť květu | _kvety_atlas | 3 |
| louka.gd:1412 | zelená stonku (0.25, 0.42, 0.13) | barva | _kvet_img | 4 |
| louka.gd:1442 | ATLAS_POMER = 341/256 (atlas 1024×512, 3×2) | trava_atlas.png | setup | 4 |
| louka.gd:1454 | alfa práh 0.4 | alpha scissor trávy | _atlas_vrstvy | 4 |
| louka.gd:1461-1462 | TVRZ_UNSHADED (tráva unshaded), mobil = feature mobile / TVRZ_MOBIL | — | _stebla_shader | 3 |
| louka.gd:1484-1490 | světlo trávy každých 0.5 s; slunce·(0.25+0.75·el)·0.55 + ambient·0.35 | kalibrace unshaded trávy | _svetlo_travy | 4 |
| louka.gd:1507-1514 | vějíř 3 karty, sklon 12°, šíře 1.25, posun 0.08 | síť vějíře | _vejir_mesh | 3 |
| louka.gd:1530 | vítr vějíře 0.4 | — | _vejir_mesh | 4 |
| louka.gd:1543-1544 | posuny karet ±0.1, výšky 1.0/0.86/0.93/0.8 | nepravidelnost trsu | _karta_mesh | 3 |
| louka.gd:1560-1569 | karta shora 30°, délka 0.9·šíře, UV 0.35–1 | (dnes nepoužito, shora=false) | _karta_mesh | 3 |

## main.gd (světlo, stíny, kvalita, mobil, kamera, occlusion, pořadí stavby)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| main.gd:18,105 | kvalita 0/1/2 (Nízká/Střední/Vysoká); výchozí tablet 1, PC 2; TVRZ_MERENI = 1 | stupeň kvality | _ready, apply_quality | 3 |
| main.gd:25-26 | SPAWN (2.5, 0, 40), pohled (0, 4.5, 15); dopad z výšky +30 m | start hráče | _build | 1 |
| main.gd:58 | HRANICE Rect2(−215, −215, 1075, 1505) = x −215…860, z −215…1290 | hranice hratelného světa (kraj.py ACT −250..900 × −250..1350 minus 35–60 m) | _process_vlastni | 1 |
| main.gd:97-98 | Vulkan: MSAA 2× hned od startu | proti pruhům na Adreno 8xx (v rozporu s pravidlem „tablet nikdy MSAA“, pak přepíše apply_quality) | _ready | 3 |
| main.gd:120 | msaa_on výchozí = ne na mobilu | MSAA volba | _ready | 3 |
| main.gd:123,1702 | rozlišení 3D: 0 sníž. (podle kvality), 1 = max(sc, 0.8), 2 = 1.0 | 3D render scale | apply_quality | 3 |
| main.gd:343-454 | pořadí stavby: Svet.build → Pohyb → Predmety → MenuHrace → Mapa → Daylight → Player → Life → Lide → Louka → Voda → Ruchy → Sber → Pad → apply_quality → 2× physics → svet.dosednout → tvrz_kryti → kolize_rozdel/rostliny_rozdel → kolize_okoli/rostliny_okoli(SPAWN) → place → předehrání shaderů | pořadí stavby světa | _build | 1 |
| main.gd:375-378 | výšková mlha fog_height = nejnižší Teren* + 4 m | mlha v nivách | _build | 3 |
| main.gd:398 | louka bez fyzikální interpolace | statické MultiMeshe | _build | 3 |
| main.gd:760-765,789-794 | předehrání: kopie ×0.002, extra_cull_margin 16384, vis_range_end 3.5 + margin 2; 3+2 snímky, omni 6 m | předehrání shaderů (všechny kombinace materiál/stín/prolínání) | _predehrej_shadery | 3 |
| main.gd:1026,1032 | paprsek 60 → −30 m, +0.05 m | nalezení země | _ground | 1 |
| main.gd:1081-1089 | každých 0.5 s: kameny toku; mlha v lese = korun v 5 bodech (±10 m), (z/5 − 0.3)/0.5, jen venku (interior ≤ 0.5) | lesní mlha | _process_vlastni | 3 |
| main.gd:1242-1249 | zóna tvrz x −25…17, z −14…14, y < 14 (hystereze 1.5/−0.5); ves střed (470, 830), r 135/150 m | hudební zóny = hranice tvrze a vsi | _music_zone | 1 |
| main.gd:1488-1493 | kruhy 0–3 m, 12 směrů, dy 0.05/0.4, paprsek +0.3…−1.5 | volné místo po načtení | _volne_misto | 3 |
| main.gd:1514-1516 | truhla (−6.6, 0.04, 13.35), sud (−15.4, 0.02, 13.2), vědro (−16.2, 0.02, 12.9) | výchozí vybavení zbrojnice a kovárny (ručně) | _default_items | 1 |
| main.gd:1528-1545 | louče v hostinci výška min(1.9, výška−0.4), místnost > 6 m = 4 stěny, 0.2·rozměr od středu | (vypnuto, ř. 1517) | _hostinec_svetla | 1 |
| main.gd:1608-1616 | kapsle r 0.4, h 1.8; spirála 40 kroků po 0.15 m (do 6 m) | volné místo při rychlém cestování | fast_travel | 3 |
| main.gd:1691-1692 | fyzika 60 Hz (30 Hz při volbě 2), max 2 kroky (3 při volbě 0) | krok fyziky | apply_fyzika | 3 |
| main.gd:1698 | render scale tablet [0.45, 0.55, 0.7], PC [0.7, 0.85, 1.0]; bilineární škálování (ne FSR) | rozlišení 3D podle kvality | apply_quality | 3 |
| main.gd:1707 | use_occlusion_culling = true (okluzory terén + domy) | occlusion | apply_quality | 3 |
| main.gd:1708 | mesh_lod_threshold tablet 10 px, PC 4 px | LOD sítí | apply_quality | 3 |
| main.gd:1712 | MSAA 4× pokud msaa_on, jinak vypnuto | MSAA | apply_quality | 3 |
| main.gd:1714-1715 | SSAO jen kvalita 2 a ne mobil; glow od kvality 1 | efekty | apply_quality | 3 |
| main.gd:1718-1724 | stíny slunce [40, 60, 80] m, 2 kaskády; tablet 40 m, ORTHOGONAL (1 kaskáda) | dosah stínů | apply_quality | 3 |
| main.gd:1725 | stínový atlas 2048 (16-bit) | rozpočet GPU paměti | apply_quality | 3 |
| main.gd:2060 | paprsek 400 → −200 m | nejvyšší kolize (střechy, koruny) | _ground_hi | 1 |

## daylight.gd (slunce, obloha, mlha, denní doba)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| daylight.gd:9-30 | předvolby 5 dob: elevace/azimut slunce (ráno 13°/100°, poledne 48°/180°, odpoledne 22°/238°, soumrak 4.5°/286°, noc 38°/150°), energie slunce 2.6/3.5/3.3/1.7/0.32, ambient 0.5–1.6, mlha hustota 0.0004–0.0022, výšková mlha 0.004–0.03, barvy oblohy/mlhy | osvětlení podle doby | state_at, _apply | 3, 4 |
| daylight.gd:33 | RATE = 24 h / 5400 s (den = 90 min) | běh času | _process_vlastni | — |
| daylight.gd:34-36 | KEY_HOUR (7, 12, 15.5, 19.6, 23); FRAMES (0 noc, 4.6 noc, 6.6 ráno, 12, 15.5, 19.4 soumrak, 21 noc) | klíčové snímky | state_at | 3 |
| daylight.gd:49-52 | Compatibility (LDR): slunce ×0.38, ambient ×0.65, expozice 1.0 (Vulkan 0.95) | profil tabletu | _apply, _amb | 3 |
| daylight.gd:66-74 | stíny 4 kaskády, 110 m, bias 0.07, normal bias 2.0, fade 0.75, blur 0.8, úhel 0.7° | výchozí stíny (main.apply_quality je přepíše na 40/60/80 m, 2 kaskády) | setup | 3 |
| daylight.gd:82-83 | radiance 128, PROCESS_MODE_QUALITY | obloha | setup | 3 |
| daylight.gd:90-104 | ACES, white 1.6 (LDR) / 8.0; aerial 0.12, sky_affect 0.15, sun_scatter 0.28, fog_height −6 (main přepíše); glow 0.55/bloom 0.04/práh 1.1; kontrast 1.1, saturace 1.06 | prostředí | setup | 3, 4 |
| daylight.gd:140-148 | ráno 5.5–10.5, poledne 10.5–14, odpoledne 14–18.6, soumrak 18.6–21, jinak noc | názvy dob (svítidla, zvuky) | key_at | — |
| daylight.gd:224 | obloha se obnoví 4× za s | — | _process_vlastni | 3 |
| daylight.gd:241 | směr slunce se mění skokem až po 0.026 rad (1.5°) | stíny neblikají | _apply | 3 |
| daylight.gd:255 | zem oblohy = horizont × 0.32/0.31/0.3 | barva | _apply | 4 |
| daylight.gd:210,276-278 | lesní mlha: přechod 0.25/s, barva (0.52, 0.56, 0.5), hustota max(d, 0.012) | mlha v lese | _les_mlha | 3 |
| daylight.gd:291-294 | interiér: ambient ×(1 − 0.95·i), obloha ×(1 − 0.7·i), barva (0.55, 0.45, 0.34), expozice +0.1 | interiér | _amb | 3 |

## predmety.gd (předměty, svítidla, portály/interiér)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| predmety.gd:5-6 | katalog modely/predmety.json, modely/predmety/*.glb | zdroj předmětů | setup, scene | — |
| predmety.gd:81 | paprsek top 3 m, 8 m dolů | země pod předmětem | ground_y | 1 |
| predmety.gd:89,96 | paprsek na zeď 6 m; WALL_GAP 0.035 m (ř. 1221) | předmět na zdi | spawn_on_wall | 1 |
| predmety.gd:131 | voda v nádobách = svet.material("voda") (drsnost 0.08 = zrcadlo, bílý pruh na tabletu) | zákaz vlastního materiálu vody | spawn | 4 |
| predmety.gd:168-169 | dosah viditelnosti: < 0.5 m → 20 m, < 1.5 m → 40 m, jinak 80 m; margin 3 m, FADE_SELF | třídy předmětů podle velikosti | spawn | 3 |
| predmety.gd:170-171 | lomová stěna (sc) 160 m | výjimka | spawn | 3 |
| predmety.gd:178-179 | bez stínu, je-li největší rozměr < 1 m | stíny drobností | spawn | 3 |
| predmety.gd:199-201 | kolize hráče jen výška > 0.25 m nebo šířka > 0.6 m (ne na zdi, ne „pruchozi“); jinak vrstva 2 (jen pokládání) | třídy kolize | spawn | 3 |
| predmety.gd:205 | box 0.95 × půdorys, výška přesně | kolize předmětu | spawn | 3 |
| predmety.gd:211-215 | pevné vybavení vsi: vis_range 60 m, margin 8 (přepíše 20/40/80!) | dosah pevných předmětů | spawn | 3 |
| predmety.gd:237-238 | dosah použití 1.6 + 0.5·rozměr; výška min(0.6·v, 1.2) | interakce | _refresh_use | — |
| predmety.gd:244 | drobnost = váha < 15 | do brašny | _small | — |
| predmety.gd:248-272 | SVETLA: louč (výkon 1.8, dosah 9), lucerna 2.2/9.5, svícen 0.75/4.5, svícny 1.4/6.5, dvojsvícen 1.0/5, kotlík 2.4/9, svícen stojací 1.0/5.5, věnec 1.6/7, svíčky 0.7/4, svíce velké 1.0/5, lustr 1.8/8 | svítidla | _fire_fx, hold | 3 |
| predmety.gd:496-501 | útlum 1.4, stíny svítidel vypnuté (rozpočet life._shadow_budget), bias 0.06/1.2 | stíny světel | _fire_fx | 3 |
| predmety.gd:541-542 | zvuk ohně unit 2.5, max 18 m | — | _light_fx | — |
| predmety.gd:559-564 | louč v držáku 5.7 cm od zdi, sklon 12°; 1.6/7.5 m | — | _bracket_torch | 1 |
| predmety.gd:588 | v ruce ×1.1 výkon, ×1.15 dosah | — | hold | 3 |
| predmety.gd:648 | vzdálenost ducha 1.3 + 0.7·rozměr | pokládání | begin_place | — |
| predmety.gd:782 | místnost hledat jen ±12 m od středu | — | _mistnost_predmetu | 3 |
| predmety.gd:792 | interiér vyhodnocovat 5× za s | portály | _interier | 3 |
| predmety.gd:811 | otvor ven viditelný do 12 m (144 m²) | portály | _interier | 3 |
| predmety.gd:830 | okno do 10 m v zorném poli = režim 1 | portály | _interier | 3 |
| predmety.gd:849 | VNITREK_ROSTLINY 30 m (nepoužito) | — | — | 3 |
| predmety.gd:864 | přepočet po 8 m pohybu | — | _vnitrek | 3 |
| predmety.gd:884-885 | VNITREK_DOSAH 25 m (zavřená místnost), VNITREK_OKNO 80 m (s výhledem); impostor*/obzor*/Teren mimo budovu pryč v režimu 2 | skrývání světa uvnitř | _vnitrek_krok | 3 |
| predmety.gd:900 | rozpočet 1.5 ms/snímek | průchod stromem | _vnitrek_krok | 3 |
| predmety.gd:966,969 | zeď: paprsek 3.5 m, abs(normála.y) < 0.35 | pokládání na zeď | _process_vlastni | 1 |
| predmety.gd:987 | paprsek +1.6 … −3 m | země pokládání | _process_vlastni | 1 |
| predmety.gd:997-1000 | box 0.85 × půdorys, bez spodních 0.08 m; zdvih 0.06 + 0.08·rozměr (mírný svah nevadí) | kontrola místa | _process_vlastni | 1 |
| predmety.gd:1011 | viditelnost místa: zásah do 0.35 m | — | _process_vlastni | 1 |
| predmety.gd:1236 | zapíchnout: nářadí/zbraně delší 0.6 m | — | can_stick | — |
| predmety.gd:1276-1278 | zapíchnuté: 1/5 délky v zemi, náklon 0.12/0.06 rad | — | orient_xf | 1 |
| predmety.gd:1296-1314 | stojan/hák: 0.75 m od přímky, do 3.2 m, zdvih 0.75 | — | _find_snap | — |

## portaly.gd (portály místností – ručně zadané souřadnice tvrze)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| portaly.gd:10-14 | hostinec z modely/portaly.json (tools/portaly.py), „cela“ = celá budova | portály hostince | nacti | 3 |
| portaly.gd:39-41 | ZS −7.6 (líc dvorního průčelí paláce), ZN −14.0 (severní hradba), F1 3.9 (patro) | rozměry paláce | _tvrz | 1 |
| portaly.gd:48-68 | palác: dveře síně (8, 1.475) 1.8×2.95, okna 1.0×1.3, okna sever 0.6×1.2 aj. | ruční souřadnice | _tvrz | 1 |
| portaly.gd:69-88 | věž: líce x −26.3/−21.3, z −15.3/−10.3 (posun TX −8); vyhlídka y 14.7, okna 0.95×1.2 po 2.8 m | ruční souřadnice | _tvrz | 1 |
| portaly.gd:90-96 | strážní komora nad branou y 7.48–7.93, z 10.05/16.45 | ruční souřadnice | _tvrz | 1 |
| portaly.gd:98-101 | zbrojnice z 9.8, x −5.45…−10.2 | ruční souřadnice | _tvrz | 1 |

## voda.gd (hráč ve vodě)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| voda.gd:17 | 8 kruhových vln najednou (sdílí life.gd) | rozpočet vln | setup, vlna | 3 |
| voda.gd:46 | paprsek +2 … −0.3 m na vrstvu VRSTVA_VODA (Area3D) | detekce vody | _fyz_krok | 3 |
| voda.gd:54 | ve vodě = hloubka 0.02–1.9 m | — | _fyz_krok | 1 |
| voda.gd:58-65 | síla 0.45 + 0.12·v; vlna každých 0.32 s (chůze) / 1.4 s (stání); vstup 1.3 | vlnky | _fyz_krok | — |
| voda.gd:67 | poloměr čeření 0.22 + 0.12·hloubka | shader vody | _fyz_krok | 4 |

## jerab.gd (šlapací jeřáb v lomu)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| jerab.gd:8-9 | R_KOLO 2.15 m (kolo 4.3 m), šlapání 0.8 m/s | mechanika | _process | — |
| jerab.gd:14,29 | buben r 0.255 m (z katalogu „dily“) | — | setup | — |
| jerab.gd:17 | klid: kvádr 1 m nad zemí | — | — | 1 |
| jerab.gd:41,48 | max zdvih = horní kladka − 0.75 − y0 | — | setup | 1 |
| jerab.gd:46-47 | dno kladnice 1.6 m (výchozí), +0.03 m nad terén svet._vyska | posazení na terén | setup | 1 |

## trava.gd (STARÁ tráva v krajině – nikde se nenačítá, nahrazena louka.gd)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| trava.gd:6-7 | BUNKA 16 m, 2 buňky/snímek | (mrtvý kód) | _process_vlastni | 3 |
| trava.gd:39-40 | krok [0.95, 0.75, 0.62] m, dosah [30, 42, 55] m podle kvality | (mrtvý kód) | setup | 3 |
| trava.gd:118-126 | posun ±0.4·krok, měřítko 0.55–1.2 × 0.7–1.1, výška ×0.75–1.35, −0.04 m, seed ^1393 | (mrtvý kód) | _postav | 3 |
| trava.gd:139-142 | bez stínu, vis_range_end = dosah, margin 8, FADE_SELF | (mrtvý kód) | _postav | 3 |

## data.gd, pad.gd, styl.gd (bez vlivu na podobu světa)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| data.gd:2-11 | data mimo APK v balících .pck < 95 MB, user://data, md5 | načítání dat (ne dlaždice světa) | ensure | 3 |
| pad.gd:5-6 | mrtvá zóna 0.16, otáčení 2.7 rad/s | ovladač (UI) | — | — |
| styl.gd:6-10 | barvy inkoustu UI | jen UI (class_name Styl) | — | — |

## ves_oblouk.gd (ves v oblouku – přesun usedlostí, ulice)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| ves_oblouk.gd:12-13 | čte pravidla/lokace_ves.json (usedlosti, ulice) a pravidla_sveta.json pasma.cesta.ulice_vsi | „žádná vlastní čísla“ – pravidla z JSON | _init | 1 |
| ves_oblouk.gd:18,26 | PRECHOD 10 m výchozí → lokace_ves.prechod_terenu_m | prolnutí terénu usedlosti s okolím | vahy | 1 |
| ves_oblouk.gd:36 | půdorys usedlosti: −(L/2 + 14) … L/2 + 2.5 podél, −W/2 − 7.2 … W/2 + 10.5 napříč (ručně, ne z JSON!; komentář: vesnice.py L/2+13, −W/2−6.2, W/2+9.5) | rozsah usedlosti (dvůr, zahrada, sad) | _init, _venku | 1 |
| ves_oblouk.gd:110-165 | osa ulice po 1 m: L1, oblouk R/turn_st, L2, vlny, ke_stitu {od_m, nasobek, min, max, dosah}, napojeni_vjezdu_m, od_pudorysu_m (vše z lokace_ves.json) | trasa ulice | osa_ulice | 1 |
| ves_oblouk.gd:141 | štít = hu1 − 2.5 | odstup štítu od osy | osa_ulice | 1 |
| ves_oblouk.gd:154-161 | 6 kol: odklon ×0.6 v půdorysu, vyhlazení 5 bodů | ulice nevjede do usedlosti | osa_ulice | 1 |
| ves_oblouk.gd:185 | vzdálenost od osy po každém 2. bodu | — | od_ulice | 1 |
| ves_oblouk.gd:199-205 | půlšířka ulice z lokace_ves.ulice.pulsirka (zaklad, vjezd, vlny, min, max) | šířka ulice | pulsirka | 1, 2 |
| ves_oblouk.gd:226-229 | výška osy vyhlazená ±6 bodů | podélný profil ulice | ulice_vysky | 1 |
| ves_oblouk.gd:232 | mřížka 4 m, okolí ±2 buňky (±8 m) | dosah úpravy výšky | ulice_vysky, uprav_y | 1 |
| ves_oblouk.gd:255-261 | rovne_m, prechod_m, pricny_podil (pravidla_sveta pasma.cesta.ulice_vsi) | příčný profil ulice | uprav_y | 1 |

## nadrz.gd (rybník, příkop – dno, břeh, bahno)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| nadrz.gd:7 | K = 0.5 m | mřížka nádrže | priprav, misto | 1 |
| nadrz.gd:8 | HLOUBKA 1.8 m | max hloubka | strop, nova_hladina | 1 |
| nadrz.gd:9 | SVAH 4 (1:4) | sklon dna od břehu | strop | 1, 2 |
| nadrz.gd:10 | BAHNO 1.2 m | pás bahna za břehem | strop, bahno | 1, 2 |
| nadrz.gd:11 | OKRAJ 1.1 m | břeh posunut dovnitř od hrany hladiny z Blenderu | priprav | 1 |
| nadrz.gd:37-38 | okraj +12 m do louky | rozsah mřížky | priprav | 1 |
| nadrz.gd:66-72 | rozmazání 2× (r 2 = 2.5 m), šum seed 5 freq 0.15 ±0.35 m | hladký břeh | priprav | 1 |
| nadrz.gd:81 | rybníček ve vsi: střed do 25 m od VES+POND | výběr tvaru | priprav | 1 |
| nadrz.gd:90-93 | VES (470, 830), osy AU (0.762, 0.648), AV; POND (u 74, v 2, poloosy 14 × 9 m) | ručně zadaný rybníček (blender/vesnice.py) | _pond_d, _pond_bod | 1 |
| nadrz.gd:97 | tvar břehu: 1 + 0.16 sin2a + 0.09 sin3a + 0.05 sin5a | zátoky | _pond_r | 1 |
| nadrz.gd:124-130 | hladina 72 × 10 bodů, přes břeh +0.45/9 (0.9 m) | síť hladiny | nova_hladina | 3 |
| nadrz.gd:134,349 | hloubka = min(1.8, 0.05 + d/4); COLOR.r = h/4 m | průhlednost u břehu | nova_hladina, hloubka_hladiny | 4 |
| nadrz.gd:137 | UV = poloha × 0.25 (vzor 4 m) | měřítko vzoru hladiny | nova_hladina | 4 |
| nadrz.gd:230 | bahno: hladina + 0.04 … +0.16 m | výška pásu bahna | strop | 1, 2 |
| nadrz.gd:245-251 | malá nádrž: do 6 m za břehem; do 0.35 m hladina −0.05, pak +0.15 na 0.8 m a 1:10 | podlaha břehu | podlaha | 1 |
| nadrz.gd:273 | bahno 1 − smoothstep(0.72, 1.92 m) | maska bahna | bahno | 2 |
| nadrz.gd:291,263 | výchozí barva vrcholu (0, 0.85, 0, 1) | COLOR.g = louka | vyhloub | 2 |
| nadrz.gd:301-305 | do 14 m od kruhu: alfa = bahno (−0.2…0.7), G 0.3→0.85 (0.1…0.8 m) | bahno/louka kolem rybníčku | vyhloub | 2 |
| nadrz.gd:310 | COLOR.a = 1 − 0.5·bahno (a < 0.5 = potok) | kódování povrchu ve vrcholu | vyhloub | 2 |

## koryto.gd (potok Bystřice – profil koryta a zářezu)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| koryto.gd:16 | HLOUBKA 0.6 m (±20 %, šum ×0.33) | hloubka vody | priprav, strop | 1 |
| koryto.gd:17 | PRAH 0.6 m | práh od kraje vody k hladině +5 cm | strop, dno | 1 |
| koryto.gd:18 | DOSAH 34 m | vyhodnocení koryta (rostliny, maska) | blizko, hrana | 1 |
| koryto.gd:19 | PAS 17 m | zářez končí nejpozději tady (jemná síť Teren_reka ~18 m) | strop | 1 |
| koryto.gd:20 | POD_JEMNOU 2.5 m | hrubá síť pod jemnou | vyhloub | 3 |
| koryto.gd:21-23 | sklon svahu: vnější 0.85 (~40°), rovný 0.42 (~23°), vnitřní 0.2 (~11°) | břehy (nárazový skalnatý / jesep) | strop | 1, 2 |
| koryto.gd:24 | ROZEVRENI 0.012 | kvadratické rozevření údolí | strop | 1 |
| koryto.gd:25 | KRIVOST 0.025 (r 40 m) | plná zatáčka | blizko | 1 |
| koryto.gd:33,108 | mřížka 16 m | vyhledávání úseků | priprav, blizko | 3 |
| koryto.gd:49-63 | šumy: seed 77 f 0.02; seed 91 f 0.012; seed 13 f 0.18 2 oktávy | šířka/hloubka, sklon, zvlnění svahu | priprav | 1 |
| koryto.gd:69 | dno = min terénu v ±3 m (5 vzorků) | — | priprav | 1 |
| koryto.gd:76 | půlšířka vody 2.4 m ×(1 ± 0.5·šum) | šířka potoka | priprav | 1 |
| koryto.gd:78 | sklon ×(1 ± 0.5) podél toku | — | priprav | 1 |
| koryto.gd:84-91 | křivost vyhlazena ±3 body (~30 m) | — | priprav | 1 |
| koryto.gd:93-107 | hladina = průměr 9 bodů + 0.35 m, nikdy nestoupá po proudu | hladina | priprav | 1 |
| koryto.gd:158 | dno: střed − hloubka, k okraji 0.6–1·w polovina | profil dna | strop | 1 |
| koryto.gd:163-164 | jesep 0–4 m, +0.03 m/m | vnitřní břeh | strop | 1, 2 |
| koryto.gd:168 | zvlnění svahu ±0.45 m (od 2 m) | — | strop | 1 |
| koryto.gd:180-191 | podlaha břehu (jen Teren_reka po 2 m): 0.4–9 m od vody, +0.05 + 0.1·(e−0.4), za 5 m −0.6/m | val u potoka | podlaha | 1 |
| koryto.gd:199-200 | dno (oblázky) = šířka + 0.6 + 4·jesep, přechod −0.3…+0.6 m | maska oblázků v zem.gdshader | dno | 2 |
| koryto.gd:240-246 | buňky 2 m pokryté jemnou sítí | — | pokryj | 3 |
| koryto.gd:278 | hrubá síť v PAS + 2 m níž | — | vyhloub | 3 |
| koryto.gd:286 | COLOR.a = 0.5 − 0.5·dno (oblázky) | kódování povrchu | vyhloub | 2 |
| koryto.gd:341 | sukně 3 m dolů, bez kolize | skrytí škvír | sukne | 3 |

## player.gd (jen fyzika pohybu související se světem)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| player.gd:7-8 | chůze 2.3 m/s, běh 4.8 m/s | rychlost (měřítko světa, mapa počítá 4.5 km/h) | _physics | 1 |
| player.gd:10 | skok 4.4 m/s | — | _physics | 1 |
| player.gd:11 | oči 1.62 m | výška kamery | _ready, place | 1 |
| player.gd:12 | AREA x −240…890, z −240…1340 | hranice pohybu (kraj.py ACT − 5 m) | _physics | 1 |
| player.gd:15,360 | STEP 0.45 m (pak 0.25, 0.15 pod nízkým stropem) | nejvyšší schod | _step_up | 1 |
| player.gd:40,58 | gravitace 12 (projekt) | — | _physics | — |
| player.gd:61-64 | kapsle r 0.28, výška 1.76 | kolize hráče (průchody ≥ 0.56 m, výška dveří ≥ 1.76 + schod) | _ready | 1, 3 |
| player.gd:73-75 | FOV 72°, near 0.04, far 2200 m | kamera (dohled) | _ready | 3 |
| player.gd:81 | floor_max_angle 52° | nejstrmější schůdný svah | _ready, _zkus_schod | 1, 2 |
| player.gd:82 | floor_snap 0.45 m | přilnutí k zemi | _ready | 1 |
| player.gd:85 | max_slides 6 | — | _ready | 3 |
| player.gd:283 | zrychlení 11 (zem) / 2.5 (vzduch) | — | _physics | — |
| player.gd:310-311 | pod −90 m → návrat na (0, 2, 30) | propad světem | _physics | 1 |
| player.gd:327 | krok 1.15 m (chůze) / 1.5 m (běh); zvuky kroků vypnuté | — | _physics | — |
| player.gd:350 | strop letu 120 m | pískoviště | _fly | — |

## life.gd (ohně, světla, povrch kroků, místa, příkop)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| life.gd:12 | dřevěná podlaha: branka, vez1, vez2, komnata, loznice, zbrojnice | druh povrchu místností | surface_at | 2 |
| life.gd:13 | FIRE_COL (1.0, 0.64, 0.38) | barva ohně | _light | 4 |
| life.gd:156-157 | povrchy kroků: stone, wood, grass, dirt, listi, most, voda, sterk, blato, seno | seznam druhů povrchu (zvuk) | step_sound | 2 |
| life.gd:203-219 | povrch: místnost → wood/stone; y > 5.6 → wood; voda; nádvoří abs(x+4)<21, abs(z)<14 → dirt (lešení wood); ruiny r−8 m → listi; jinak grass | z čeho je zem (pro zvuk) – ručně, ne z masky povrchu | surface_at | 2 |
| life.gd:255-286 | plamen: částice 0.32×0.42, box 0.22×0.03×0.12·size | efekty | _flames | 3 |
| life.gd:335-339 | útlum 1.3, bias 0.08/1.5, specular 0.35 | světla ohňů | _light | 3 |
| life.gd:355-384 | krb 2.7/9.5 m se stínem; výheň 2.1/6.5 se stínem; pánev 1.7/6; louč 1.35/6; lustr 1.5/7.5; svíce 0.35/2.4 (max 10 světel svíček) | světla z info.fires | _build_fires | 3 |
| life.gd:400 | dosah použití světla 1.5 (lustr 2.2) | — | _build_fires | — |
| life.gd:415-416,541 | zvuk ohně unit 2.5, max 22 m | — | _add_fire_loop | — |
| life.gd:427-450 | kouř 14 částic, 8 s, škála 0.4→3.2 | komíny | _build_smoke | 3 |
| life.gd:467 | MAX_LIT 7 nejbližších světel (mobil max 8 na model) | rozpočet světel | _shadow_budget | 3 |
| life.gd:493-494 | distance fade 28 m + 8 m | světla | _shadow_budget | 3 |
| life.gd:501 | stíny bodových světel: kvalita 0/1/2 → 0/1/2 nejbližší | rozpočet stínů | _shadow_budget | 3 |
| life.gd:506 | zapnuto do 34 m (vypnout až 38 m) | hystereze | _shadow_budget | 3 |
| life.gd:509 | stín jen do 18 m | — | _shadow_budget | 3 |
| life.gd:575 | rozpočet přepočet 0.3 s | — | _process_vlastni | 3 |
| life.gd:591 | místnost ±12 m | — | _update_place | 3 |
| life.gd:597 | ambient místnosti = jas·2.3, 0.32–1 | interiér | _update_place | 3 |
| life.gd:617-628 | názvy míst: hradby y > 6 a abs(x)>15.5 nebo abs(z)>12.5; nádvoří abs(x+4)<21, abs(z)<14; Lhota (470, 830) r 130; Boží muka (5, 400) r 25; Skalní město x < −90, z 220…920 | ručně zadané oblasti | _update_place | 1 |
| life.gd:658-680 | 32 paprsků 30 m, 6/snímek | kolik oblohy je vidět | _sky_probe | 3 |
| life.gd:844 | voda_y −2.75 výchozí | hladina příkopu | _moat_setup | 1 |
| life.gd:848-861 | příkop: 260 bodů, 3–10 m vně hradeb (z ±15.8, x −26.8 / 18.8), dno < hladina − 0.15 | body pro vlnky | _moat_setup | 1 |
| life.gd:884 | vlnka každých 5–20 s | — | _moat | — |

## lide.gd (vesničané)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| lide.gd:8-9 | DOSAH 70 m (vis_range_end), animace do 45 m; skrytí za 90 m | rozpočet NPC | setup, _process | 3 |
| lide.gd:10-12 | VES (470, 830), osy AU/AV staré rovné návsi | trasa vesničanů | _naves | 1 |
| lide.gd:24-31 | 5 lidí na návsi, u −70…60, bok ±1.6 m, bod po 6 m | trasy | setup | 1 |
| lide.gd:33-35 | lom: (117, 936–948), (126–127, 930–931) | ručně | setup | 1 |
| lide.gd:37 | nádvoří: (−2,6), (−3,14), (6,4), (−9,10.5), (−12,4) | ručně | setup | 1 |
| lide.gd:47 | osa návsi 2.5 sin(u/23) + 1.2 sin(u/9+1) | křivka (shoda se zem.gdshader) | _naves | 1 |
| lide.gd:107-108 | stíny NPC ZAPNUTÉ, vis_range 70 m | — | _pridej | 3 |
| lide.gd:130 | bod trasy jen kde zásah ≤ terén + 0.6 m | ne pod střechou | _over_trasy | 1 |
| lide.gd:251 | chůze 1.15 × 0.95–1.25 m/s; zastaví se 1.6 m před hráčem | — | _process | — |

## pohyb.gd (mosty, vrata, mříž, studna)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| pohyb.gd:36-48 | křídla vrat na Teren*: 5 paprsků ±0.3 m, +3 … −6 m, posun −0.02 | posazení na terén | na_zem | 1 |
| pohyb.gd:60-68 | řetěz: TorusMesh r 0.024/0.046, železo kov 0.75 drsnost 0.5 | PRIMITIVUM (v rozporu s pravidlem „vždy modely“) | setup | 4 |
| pohyb.gd:139 | 80 článků na řetěz | — | setup | 3 |
| pohyb.gd:146-153,173-180 | lano: CylinderMesh r 0.016 / 0.018, barva (0.42, 0.35, 0.23), drsnost 0.95 | PRIMITIVUM | setup, _coil | 4 |
| pohyb.gd:108-125 | zvuky 60 m / 30 m | — | setup | — |
| pohyb.gd:132 | dosah použití 1.9 (naviják) / 2.3 | — | setup | — |
| pohyb.gd:183-199 | navíjení: stoupání 0.1/0.04, krok 0.075/0.07, max 600 článků | — | _coil | 3 |

## ruchy.gd (zvuky prostředí – zóny)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| ruchy.gd:17-26 | REKA: 50 ručně zadaných bodů toku (945,127)…(316,1416) | osa potoka pro zvuk – DUPLICITA k modely/reka/osa.json | _blizko_reky | 1 |
| ruchy.gd:27 | RYBNIK (525.1, 879.4) | = VES + AU·74 + AV·2 (nadrz POND) | — | 1 |
| ruchy.gd:28 | VES (470, 830), zóna r 140 m | zóna vsi | _zona | 1 |
| ruchy.gd:29 | KOVARNA (16.3, 1.2, 6.2) | ručně | setup | 1 |
| ruchy.gd:30-31 | STROMY [smrk, dub, lipa, buk, jedle, olse, briza, borovice], LES_BUNKA 32 m, les > 9 stromů/buňka (průměr 3×3) | seznam druhů stromů a práh lesa | _les_hustota, _zona | 1 |
| ruchy.gd:136 | tvrz x −25…17, z −14…14 | zóna tvrze | _zona | 1 |
| ruchy.gd:252-256 | rybník do 45 m; okolí tvrze 22–55 m | zvířata | — | 1 |

## sber.gd (byliny, houby)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| sber.gd:7 | DORUST 3 (dny) | — | — | — |
| sber.gd:11 | HOUBY: hřiby pod smrk, dub_stary, dub_stredni, buk_stredni; bedly pod dub, lipa, briza | vazba druh houby → strom | _houby | 1 |
| sber.gd:12 | BUNKA 6 m | mřížka hledání | setup | 3 |
| sber.gd:64-68 | u každého 10. stromu, 1.4–3.0 m od kmene | rozmístění hub | _houby | 1 |
| sber.gd:70-75 | paprsek +2 … −25 m, +0.01; měřítko 0.8–1.2 | posazení | _houby | 1 |
| sber.gd:79 | buňky 64 m | MultiMesh hub | _houby | 3 |
| sber.gd:91-94 | vis_range 40 m, margin 6, FADE_SELF, bez stínu | třída „houby“ | _houby | 3 |
| sber.gd:135-138 | sběr do 1.4 m, abs(dy) < 1.6, úhel cos > 0.82 | — | usable | — |

## mapa.gd (místa, rychlé cestování)

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| mapa.gd:9-12 | mapa x −240…890, z −240…1340 | = player.AREA | — | 1 |
| mapa.gd:13-30 | místa: Tvrz (0,0), Lhota (470,830) cíl (413,781), hostinec (−71,881), lom (138,940), kostel sv. Jiljí (220,40), Doubrava (300,340), Pustá skála (−190,540) | ručně zadané souřadnice lokací | _answer, fast_travel | 1 |
| mapa.gd:31 | OBJEV_R 40 m | objevení ruiny | — | 1 |
| mapa.gd:250,354,373 | chůze 4.5 km/h, vzdálenost ×1.35 | čas cestování | _dist_km | — |

## Mrtvý kód (nikde se nenačítá): mesh_batch.gd, props.gd, fort.gd, palace.gd, trava.gd

Tvrz se dnes načítá z Blenderu (svet.gd). Tyto skripty zůstaly z procedurální stavby; čísla v nich jsou jen historický zdroj rozměrů tvrze (blender/lib.py „stejná logika jako fort.gd“).

| soubor:řádek | hodnota | význam | kdo používá (funkce) | tabulka |
|---|---|---|---|---|
| fort.gd:7-12 | nádvoří IX 17 / IZ 14 (vnitřní líc), vnější líc 18.8 / 15.8, ochoz 6.5 m, základ −4.5 m | rozměry tvrze | (mrtvé) | 1 |
| fort.gd:~70-80 | cimbuří: zub 1.25 m, mezera 0.8, zídka 0.9 m, tl. 0.5 | — | parapet | 1 |
| palace.gd:8-22 | palác X0 −3, X1 17, ZN −14, ZS −7, T 0.6, patro 3.9, okap 7.5, hřeben (z −11.4, y 11.46) | rozměry paláce (portaly.gd: ZS − T = −7.6 sedí) | (mrtvé) | 1 |
| palace.gd/props.gd/fort.gd | barvy WOOD (0.8–0.82…), DARK, PLASTER (0.97, 0.95, 0.92), IRON | barvy | (mrtvé) | 4 |
| mesh_batch.gd:56,80-83 | UV = světové souřadnice / mats[key].tile | měřítko vzoru v metrech (tile) | quad4 | 4 |
| mesh_batch.gd:33-34,134-136 | odstín zdi: šum f 0.16, 3 okt., 0.92 ± 0.13, ztmavení u země do 1.5 m (×0.74) | tónování zdí | tint | 4 |
| mesh_batch.gd:141,181 | buňka odstínu 1.6 m (vršky 3 m) | — | gquad | 4 |
| mesh_batch.gd:446,452 | schod: nášlap 0.06, rampa pod schody −0.3 m | — | stairs | 1 |
| mesh_batch.gd:370 | kolize válce = box 1.6·r | — | cyl | 3 |

## pravidla/pravidla_sveta.json a pravidla/pravidla_modelu.json – co existuje a co kód opravdu čte

Ověřeno grepem ve `scripts/`, `tools/`, `blender/` (*.gd, *.py). Komentáře v kódu, které se na JSON odvolávají, se jako čtení nepočítají.

### pravidla_sveta.json

| sekce | obsah | čte kód? | kde |
|---|---|---|---|
| sloupce | popis sloupců (CryEngine/KCD) | ne (dokumentace) | — |
| druhy | 36 druhů (trs_nizky, trs_vysoky, drn, kvety, kapradi, mech, boruvci, vres, byliny_sber, liska, bez_cerny, hloh_trnka, malinik, vrba_ker, dub, lipa, habr, buk, briza, smrk, borovice, olse, vrba_hlavata, padly_kmen, parez_koren, kameni, balvan, vychoz, rakos, ostrice, kopriva, divizna, jitrocel, pelynek, podbel, javor_jasan, jalovec): stanoviště, výška, sklon, hustota/m², velikost, zapuštění, kolize, stín, zanik_m, pokryv_m2 | **NE** – popis tvrdí „čte svet._rozsev, louka.gd“, ale žádný `["druhy"]` v kódu není; louka.gd má čísla natvrdo | jen komentáře louka.gd:142, 1147, 1187 |
| stanoviste | 29 typů stanovišť | **NE** (mapa stanovišť v svet.gd je obrázek s kanály, ne tento seznam) | — |
| poznamky | pole, brod, voda (hloubky 0.5/1.5 m), pokryv ≥ 1 | ne | — |
| vyplnovy_druh | výplň podle stanoviště (drn, ostřice, kopřiva, boruvci, mech…) | **NE** | komentář louka.gd:1187 |
| vyplnovy_mix | podíly výplně (kosená, neudržovaná, okraj lesa, břeh, mez) | **NE** – louka._vyplnovy_mix má vlastní (jiná) čísla | komentář louka.gd:1213, 1288 |
| pasma.cesta (vozova, ulice_vsi, pesina) | drn_m, trsy_od_m, ker_od_m, kmen_m, pricny_podil, rovne_m, prechod_m | **ANO** | svet.gd:6168 (pasma, pasmo_cesty), louka.gd:1228-1230, ves_oblouk.gd:25, 255-261 |
| pasma.budova | dvur_m 2.0, kmen_od_zdi_m 2.5, plevel_u_zdi | **částečně** – jen kmen_od_zdi_m | svet.gd:7382 |
| pasma.voda | breh_m 1.5 | **NE** | — |
| pasma.skala | trava_max_sklon_st 40 | **NE** | — |
| pasma.test | visi_m 0.3, pricny_max 0.15, podlaha_teren_m 0.5 | ano (jen test) | tools/test_svet.gd:58 |
| pasma.skupiny | strom / ker / balvan / vysoka_bylina (podřetězce klíčů) | **ANO** | svet.gd:6185 |

### pravidla_modelu.json

| sekce | obsah | čte kód? | kde |
|---|---|---|---|
| sloupce | popis | ne | — |
| tridy | 12 tříd (strom, ker, trava, bylina, drevo, kamen, skala, balvan, stavba, predmet, postava, zvire): troj_lod, lod_m, lod_px, textura_px, listi_px, roughness, alfa, stin, kolize, dosah_m, kolize_m, stin_m, nacitani, uvolnit_m, vertex_lighting… | **NE** – popis uvádí tools/import_model.py, ten v repu není; žádný `["tridy"]` | — |
| rozpocet | gpu_textury_mb 400, gpu_buffery_mb 200 | **NE** | — |
| nacitani | rozpocet_us_tablet 2000 / pc 3000, tezkych_uloh 1, rostliny_dosah_m 115, uvolnit 145, kolize_bunka_m 32, okoli 1, uvolnit 2, davka 20, zasek_ms 40 | **ANO** | svet.gd:2941-2956 (_nac, planovac, rostliny_okoli) |

Shrnutí: z JSON se dnes skutečně čtou jen `pasma.cesta`, `pasma.skupiny`, `pasma.budova.kmen_od_zdi_m`, `pasma.test` (test) a `nacitani`. Tabulky druhů, tříd, výplně, rozpočtu, pasma vody a skály jsou jen dokumentace – kód má vlastní čísla.

## Duplicity a rozpory

| # | věc | kde a jaké číslo | poznámka |
|---|---|---|---|
| 1 | hranice světa | main.gd:58 HRANICE x −215…860, z −215…1290; player.gd:12 AREA i mapa.gd:9-12 x −240…890, z −240…1340 | dvě různé hranice (main tlačí hráče dřív) |
| 2 | obrys tvrze / nádvoří | louka.gd:266-276, 1019, 1208 a svet.gd:9498 x −27.6…18.5, z −16.6…17.4; life.gd:211, 619 a ruchy.gd:136, main.gd:1243 x −25…17, z −14…14; fort.gd IX 17 / IZ 14 (líc 18.8/15.8); life.gd:854-857 příkop od x −26.8 / 18.8, z ±15.8; louka val abs(x+4)<36, abs(z)<32; výjimka strmin abs(x+4)<80, abs(z)<75 | stejné místo pětkrát ručně, různé meze |
| 3 | ves – střed a poloměr | (470, 830): main.gd:1247 r 135/150, life.gd:621 r 130, ruchy.gd:28,138 r 140, nadrz.gd:90, lide.gd:10, mapa.gd:16 | po přesunu do oblouku (ves_oblouk + lokace_ves.json: nové středy x 369–452, z 750–907, vjezd (372, 744)) je (470, 830) střed STARÉ návsi |
| 4 | vesničané na staré návsi | lide.gd:24-31, 47 chodí po staré rovné ose VES + AU·u (u −70…60) | svet.gd:41-47 tuto oblast vede jako „starou náves, kudy už cesta nevede“ → lidé chodí mimo novou ulici (ověřit snímkem) |
| 5 | rybníček ve vsi | nadrz.gd:93 POND (u 74, v 2) na staré ose = ruchy.gd:27 RYBNIK (525.1, 879.4) | ručně ve dvou souborech; s oblouku se nepřesouvá |
| 6 | stíny slunce | daylight.gd:67-68 4 kaskády 110 m; main.gd:1718-1724 2 kaskády [40, 60, 80] m, tablet 1 kaskáda 40 m; pravidla_modelu stin_m strom 60, skála/stavba/balvan 40, předmět 20 (nečte se) | daylight hodnoty se hned přepíší |
| 7 | LOD | main.gd:1708 mesh_lod_threshold PC 4 px, tablet 10 px; pravidla_modelu lod_px 4 pro všechny třídy | tablet jinak než tabulka |
| 8 | dohled trávy | louka ZANIK trsy/vysoká 110 m (tablet 80), drn 45, vějíř 60; HUST_DO 130 (nepoužitá konst.); pravidla_sveta trs_nizky 130, trs_vysoky 100, drn 45; pravidla_modelu trava dosah 130 / uvolnit 160; louka _dosah 120 + UVOLNIT 24 | tři různé hodnoty pro trsy |
| 9 | vějíř – pásma | louka.gd:31 ZANIK [40, 60]; _podil 15/40/60 a 25 %; shader hust_od 15, hust_do 40, konec 40; komentáře 25/60/90 m (ř. 30, 520) | komentáře neodpovídají číslům; vrstva je navíc vypnutá (_vypnute [2, 4]) |
| 10 | výplňový mix | pravidla_sveta kosená vějíř 0.6 / nízká 0.2 / suchá 0.1 / byliny 0.1; louka.gd:1296-1299 0.48 / 0.2 / 0.1 / 0.22; neudržovaná JSON vějíř 0.2 / suchá 0.15 / trsy 0.25 / vysoká 0.3 / kopřiva 0.1, kód vějíř 0.08 / suchá 0.15 / trsy 0.25 / byliny 0.12 / vysoká 0.40; břeh JSON vějíř + ostřice 0.5, kód (zářez) vějíř + vysoká 0.5; mez jen v JSON | kód a JSON se rozešly, komentář louka.gd:1288 cituje JSON |
| 11 | drn | pravidla_sveta drn 6/m², vyplnovy_druh drn; louka DRN_KROK 0.35 ≈ 8/m²; vrstva drn vypnutá (_vypnute obsahuje 2), výplň dělá nízká tráva a textura | — |
| 12 | sklon bez trávy | pravidla_sveta pasma.skala trava_max_sklon_st 40 a druhy trs ≤ 40/45°; louka.gd:299 sklon 1.2–1.6 (≈ 50–58°), terasa 0.85–1.15 (≈ 40–49°); player.gd:81 schůdné do 52° | JSON se nečte |
| 13 | břeh vody | pravidla_sveta pasma.voda breh_m 1.5 (nečte se); louka: rybníček tráva od 0.5 m (ř. 281), potok od 0.7 m (ř. 292), Lhota výška +0.12 m (ř. 286); nadrz BAHNO 1.2 m; koryto PRAH 0.6 m | čtyři různá pravidla |
| 14 | u zdi budovy | pasma.budova dvur_m 2.0 rovný dvůr (nečte se); louka.gd:199-200 pás 2.5 m u zdi hustší (0.85); nádvoří trsy jen 1.2–2.8 m od zdi | — |
| 15 | pěšina – kraj trávy | louka.gd:258 trsy od 0.72–1.05 m od osy (hlína zem.gdshader 0.45–0.7); pasma.pesina drn_m 1.0, trsy_od_m 1.0 od kraje hlíny | dvě různé soustavy (osa vs kraj hlíny) |
| 16 | předměty | predmety.gd:169 dosah 20/40/80 m (= pravidla_modelu predmet lod_m); pevné vybavení 60 m (ř. 213) přepíše; stíny všech ≥ 1 m až do dosahu (tabulka stin_m 20); kolize_m 20 neplatí | — |
| 17 | postavy | lide.gd:8, 107-108 dosah 70 m, stíny zapnuté; pravidla_modelu postava dosah 60, stin_m 15 | — |
| 18 | houby/byliny | sber.gd:91 houby 40 m bez stínu; pravidla_modelu bylina 60 m | — |
| 19 | interiér | louka.gd:534 tráva 20 m; predmety VNITREK_DOSAH 25, VNITREK_OKNO 80, VNITREK_ROSTLINY 30 (nepoužitá) | — |
| 20 | rozpočet načítání | louka ROZPOCET_US 3000 µs na všech zařízeních; pravidla_modelu nacitani tablet 2000 / PC 3000 (jen svet.planovac) | na tabletu dohromady až 5 ms |
| 21 | MSAA | main.gd:97-98 MSAA 2× hned od startu na Vulkanu (i tablet); apply_quality 4× / vypnuto (tablet výchozí vypnuto); komentář ř. 1711 „4× i na Compatibility“ | CLAUDE.md: tablet nikdy MSAA |
| 22 | primitiva | pohyb.gd:63-68 TorusMesh (články řetězu), :146, :173 CylinderMesh (lana); mesh_batch/props/fort/palace (mrtvé) | CLAUDE.md: vždy modely, ne primitiva |
| 23 | kapsle hráče | player.gd:61-62 r 0.28, h 1.76; main.gd:1608-1609 (hledání místa) r 0.4, h 1.8 | — |
| 24 | šum louky | louka.gd:104-107 a 1071-1075 seed 1393 f 0.045, seed 77 f 0.16 – dvakrát | — |
| 25 | osa potoka | ruchy.gd:17-26 REKA 50 ručních bodů; koryto.gd čte modely/reka/osa.json | dva zdroje téže řeky |
| 26 | výška hladiny | voda_y −2.75 výchozí v louka.gd:44,101, life.gd:844, svet.gd:18,430 | shodné, ale 4× natvrdo jako záloha |
| 27 | půdorys usedlosti | ves_oblouk.gd:36 čísla 14 / 2.5 / 7.2 / 10.5 natvrdo (komentář tvrdí „žádná vlastní čísla“ a uvádí vesnice.py 13 / 6.2 / 9.5) | patří do lokace_ves.json |
| 28 | rychlost chůze | player WALK 2.3 m/s (8.3 km/h); mapa.gd 4.5 km/h × 1.35 | mapa počítá pomalejší pochod (záměrně?) |
| 29 | trava.gd | stará tráva (16 m buňky, dosah 30–55 m) – nikde se nenačítá | mrtvý kód |
| 30 | mlha | daylight.gd:97 fog_height −6; main.gd:378 přepíše na dno terénu + 4 m | — |
