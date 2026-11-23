# Plán z rešerše 17. 11. (dvě PDF Míši) – převzít vše užitečné

Míša 17. 11.: „přeber vše, co nám nějak pomůže, jak v menší chybovosti a plynulosti, tak v kvalitě reality a krásy“.
Zdroje: `docs/rozpracovane/reserse_pdf_17_11.md` (Puchart) a Havran `docs/rozpracovane/reserse_17_11_pdf.md`
(větev claude/new-session-0dtk58). Začne se po vydání APK 17. 11. Všechno je zatím NEOVERENO na tabletu.

## A. Plynulost
| č. | co | odkud | kde u nás |
|---|---|---|---|
| A1 | Automatika detailu: p75 času snímku s hysterezí, ubírá detail (ne rozlišení), po zchladnutí vrací | Halcyon (PDF 1 s. 3) | nový `hra/scripts/regulator.gd`, `rozpocty.json automatika` |
| A2 | Kontrola textur v grafické paměti: 30 největších, duplicity, nepoužité; VRAM na tabletu 938 MB a roste | Havran | nástroj + výpis v měření |
| A3 | Měření: podíl snímků pod 30 FPS a nejhorších 5 % na úsek | Halcyon, Havran | `mereni.gd` |
| A4 | Vlastní LOD1/LOD2 stromů z Blenderu (decimace, méně karet listí) místo automatických | Halcyon flora.mjs, Havran K13 | `blender/`, `stromy_modely.json` |

Stav 17. 11.: **A1** hotovo – `hra/scripts/regulator.gd`, `rozpocty.json automatika` (p75 > 40 ms 15 s → stupeň dolů,
p75 < 36 ms 60 s → zpět; stupně tráva 0,7 → keře 0,7 → stíny 25 m → LOD ×2), řádek v panelu FPS, při měření vypnutý,
test `test_regulator.gd` v hlídačích (simulované snímky). Prahy a cena stupňů na tabletu NEOVERENO. **A2** hotovo –
`nastroje/textury_vram.py`, ve hře `textury_vram.gd` po měření, rozbor `docs/rozpracovane/textury_vram_17_11.md`
(duplicity textur staveb ~200 MB – návrh, nic nesmazáno). **A3** hotovo – výsledek měření má navíc sloupce
„> 33,3 ms %“, p99 a průměr nejhorších 5 % (na konci řádku, dřívější sloupce beze změny). **B1** hotovo – mřížka dosažitelnosti `hra/scripts/test_dosah.gd` (test průchodu `dosah`, pravidla `kontroly_hra.json dosah`,
mapa `build/dosah.png` + `build/dosah.json`, ~2,5 min): našla únik ze světa (opraveno, hranice v `hrac.gd`, č. 387), uvíznutí u štoly (389),
ostrovy u hradů a patra domů (390). **B2** hotovo – `smysl:cesty_souvislost` (11 kusů sítě cest, č. 388, mez `kontroly.json cesty_sit`).
**B4** hotovo – `mereni.gd` MERENI_CIL (kamera v cíli úseku, mez `mereni.json dojit_mez_m`), hlídač měření.

## B. Menší chybovost
| č. | co | odkud | kde u nás |
|---|---|---|---|
| B1 | Mřížka dosažitelnosti celého světa (díry, uvíznutí, únik ze světa) mimo naše trasy | Alchemists of Prague `--reach` | `test_pruchod.gd`, `hlidaci.sh` |
| B2 | Souvislost sítě cest a pěšin (odtržené kusy grafu) | Havran | test smyslu nad grafem cest |
| B3 | Kontrola nového materiálu ve třech světlech (ráno, poledne, večer) + interiér s loučí | Second Take | nástroj snímků, hlídač |
| B4 | Trasa: hráč musí dojít do cíle úseku (zaseknutí = chyba) | Alchemists autotest | měřicí trasa |

## C. Realita a krása (každá změna nejdřív podle reference KCD/fotek)
| č. | co | odkud | kde u nás |
|---|---|---|---|
| C1 | Opotřebení staveb vrstvením (sdílené textury + masky do barvy vrcholů, 0 vzorkovačů navíc) – pokus na jedné stavbě | NOSTALGIC TRAIN | `blender/`, barvy_vrcholu |
| C2 | Okraje pěšin a cest: střídání holé hlíny, trávy, květů a kamenů | Qiankun Seal | `cesty.json`, byliny, kameny |
| C3 | Přechod voda → kámen → tráva → první řada stromů | NOSTALGIC TRAIN | `voda_hra.json`, břeh |
| C4 | Proti opakování dílů (zídky, ploty, šindele): varianty, natočení, barevný posun | A Taste of Home | generátory staveb |
| C5 | Stíny mraků po krajině (zem.gdshader 9 → 10 vzorkovačů) | PDF 1 | `zem.gdshader` |
| C6 | Tráva se ohýbá kolem hráče | PDF 1 | `stebla.gdshader` |
| C7 | Ptáci a vzdálená zvěř jako MultiMesh s pohybem ve vertex shaderu (k oživení světa) | Alchemists | později se zvěří |
| C8 | Vlastní skeny kamene a zdiva z Potštátska (RealityScan Mobile, Míša v terénu); TRELLIS.2 (MIT) jen pro drobné předměty, Hunyuan3D ne (licence vylučuje EU) | Unleash the Avatar | modelový filtr |

## Nepoužitelné v Compatibility
Voda čtoucí obraz pod hladinou, dynamické rozlišení s doostřením, POM, shader baker / ubershadery, Lumen, Nanite,
World Partition, DLSS, FFT oceán, průhledné prolínání dosahů. Terrain3D testováno 29. 10.

## Pořadí
A1, A2, A3, B1, B2 (malé až střední, hned) → B3, B4 → C2, C3, C4 (krása u nohou, podle referencí) → A4, C1, C5, C6 → C7 se zvěří.

## D. Voda a mlha podle Míšina lesa „Hvozd“ (18. 11., odloženo do obnovy týdenního limitu)
Zdroj: artefakt Hvozd (three.js r128). Rozbor a návod: `docs/rozpracovane/voda_hvozd_navod.md`.
| č. | co | kde u nás |
|---|---|---|
| D1 | Odraz z panoramatické fotky lesa (equirect, CC0 Poly Haven) podle odraženého vektoru + Fresnel | `hra/shaders/voda.gdshader`, `voda_hra.json` |
| D2 | Tmavé tělo vody (okraj hnědý → střed černozelený), dvojí posouvající se normálová mapa, pěna u kraje ze šumu | `voda.gdshader` |
| D3 | Přízemní mlha: průsvitné obláčky podél potoků (billboardy, bez zápisu hloubky) | nový krok vody / `voda_hra.json mlha` |

## E. Plná krajina jako KCD (Míša 18. 11., priorita po obnově limitu)
Míša: „vše běží slušně, ale mrzí mě ty obrazy před sebou – je to prázdné a roste to před očima; máme mít vše zastoupené
minimálně třemi modely a minimálně bych měl v dálce vidět nějakou výplň, ne holé cesty a kopce; chci obraz plné
krajiny jako v KCD“. Snímky: docs/screens/misa_18_11_prazdna_dalka_1.jpg (x 131 z 276), _2.jpg (x 126 z 38). Tablet: 30 FPS, p75 34 ms, automatika 0/4.
| č. | co | kde u nás |
|---|---|---|
| E1 | Střední pás 20–150 m: levné trsy trávy/bylin/keřů (karty, 1 materiál, impostor trsu) – svahy a okraje cest nejsou holé | louka.gd, byliny.gd, kere.gd, nový pás „dálka“ |
| E2 | Dálka nad 150 m: travní drn a porost v barvě a struktuře terénu (zem.gdshader – makro textura porostu, šrafa stébel, barevný šum) | zem.gdshader, stanoviště |
| E3 | Pozvolné objevování (dither/prolnutí podle vzdálenosti, delší pásma) místo „roste před očima“ | stebla.gdshader, byliny, keře |
| E4 | Každý druh (tráva, byliny, keře, kameny, stromy na pase) minimálně 3 modely/varianty – audit + doplnit | katalog modelů, test smyslu |
| E5 | Okraje cest: lem trávy a bylin až k vyjetým kolejím (podle KCD fotek) | cesty, byliny |
Měřit na tabletu (rozpočet troj. 2,1 M; dnes v lese 2,35 M), snímky před/po ze stejných míst jako Míša.
Stav 18. 11.: Míša „Havran už to má celkem vychytané“ → postup: nejdřív převzít Havranovo řešení plné krajiny
(louka/drn, střední pás, pole za vsí, terén v dálce, pozvolné objevení – větev claude/new-session-0dtk58, jeho
mereni_verze.md), vlastní jen co Havran nemá. ODLOŽENO – Míša dá vědět, kdy začít (limit). Pomocník zastaven
dřív, než cokoli změnil – začne se od nuly.
Míša 18. 11. (zadání pro E): „určitě si to dobře promysli tu zeleň, ale inspiruj se od Havrana; my to máme celkově
vychytanější, takže nechci něco přehlédnout, ať to má řád a smysl a je to hezké.“ → Havran = inspirace, ne kopie.
Postup: 1) rozbor nejdřív (dokument: co kde roste a proč – stanoviště, světlo, vlhkost, pastva, sešlap u cest a vsí,
okraje lesa; pásy vzdálenosti a co se v kterém kreslí; čím se liší od Havrana a co z něj vezmeme) → Míša schválí;
2) teprve pak stavba, po krocích se snímky ze stejných míst jako misa_18_11_prazdna_dalka_*; 3) měření tabletu.
Míša 18. 11.: „nejsou to jen místa z fotek, ale celá mapa“ → E platí pro CELÝ svět (všechna stanoviště, všechny
cesty, vsi, okolí hradů, lesy, okraje, louky, pole, břehy). Snímky misa_18_11 jsou jen ukázky; kontrola pak
pokryje celou mapu (síť bodů po celém výseku + trasy, ne jen 4 místa).
Předloha pro E (Míša 18. 11., znovu): docs/reference/lod_trava_video/ – karty blízko + impostor buňky v dálce
s ditherovým přechodem (41k troj. místo 83k), stromy LOD0–3 + impostor s časovaným prolnutím. Plus Havranovy zkušenosti.

## F. Zdivo hradů – skutečný kámen (Míša 18. 11.: „není to reálné a nevím co s tím“, snímky docs/screens/misa_18_11_zdivo_*.jpg)
Příčiny: procedurální zdivo.gdshader (hex míchání výřezů + parallax) – rozmazané/natažené kameny na šikmých a zakřivených
plochách (klenba, schodiště, zdi u louče), plastový lesk. 18. 11.: parallax vypnut, kámen matný (chyba 396).
Další krok: skutečná skenovaná textura zdiva (Poly Haven castle_wall_slates / lomové zdivo z břidlice podle gc_18 a fotek
Potštátu), krabicová projekce s plynulým přechodem mezi stranami (bez natažení na šikmých plochách), měřítko kamene 20–40 cm,
spáry s maltou, bez procedurálních skvrn; srovnat snímky vedle fotek skutečných zdí (docs/reference).
Míša 18. 11. doplnila: „je to furt tapeta, to je vono“ → textura sama nestačí, zeď je rovná deska s obrázkem. Řešení jako KCD:
skutečný reliéf v geometrii – (1) zblízka (LOD0, do ~25 m) síť zdi zjemněná a vysunutá podle výškové mapy kamenů v Blenderu
(kameny vystupují 2–5 cm, spáry zapadlé), (2) nepravidelné hrany: nároží, ostění, cimbuří a koruna z jednotlivých
nepravidelných kamenů (ne ostrý kvádr), vypadlé kameny a otlučené hrany, (3) patka zdi s většími kameny, (4) dál LOD1
dnešní rovná síť s texturou; rozpočet troj. hlídat (jen blízké úseky), měřit tablet. Vzor: Havran stavebnice + KCD fotky
zdí (docs/reference/kcd_vzhled, kcd2), skutečné zdi Potštátska (docs/reference).
Míša 18. 11. (misa_cimburi_kostky.jpg, zakroužkované zuby cimbuří): „tohle je všude – vezmu kostku a potáhnu ji kamennou
tapetou“ → zuby cimbuří, nároží, ostění a koruny jsou holé kvádry s promítnutou texturou (na horní ploše a bocích
natažená). Oprava F2: zub cimbuří = skládaný z kamenů (2–4 řady nepravidelných kvádrů s maltovou spárou, sražené/otlučené
hrany, krycí deska nebo kameny na vrchu), nároží z velkých tesaných kvádrů střídavě na vazbu – geometrie v Blenderu
(blender/puchart_hrad.py ve společné funkci pro všechna cimbuří a nároží obou hradů), ne textura na kostce.
Míša 18. 11. upřesnila: „ne na cimbuří, ale na obou hradech, podzemích a vnitřních prostorách – všude je tapeta“ →
F platí pro VŠECHNO zdivo obou hradů: vnější zdi, cimbuří, nároží, paláce, věže, sklepy a podzemí, schodiště, klenby,
vnitřní stěny místností. Postup: (1) klidné zdivo podle předloh (měřítko, kontrast, barva) všude, (2) omítka uvnitř
obytných místností a na palácích (vápenná, místy opadaná), sklepy/podzemí režné zdivo z lomového kamene, (3) skutečná
geometrie kamenů tam, kde je kámen vidět zblízka (nároží, ostění, cimbuří, klenební pasy, schody, paty zdí),
(4) žádná promítnutá textura natažená na šikmých/zakřivených plochách (klenby, schodiště). Kontrola: snímky ze stejných
míst jako misa_18_11_zdivo_*.jpg vedle předloh docs/reference/zdivo_kcd_18_11/.
Míša 18. 11.: „…nejenom“ (hrady) → F platí pro všechny stavby na mapě: ves, krčma, kovárna, hájovna, mlýn, chýše a zemljanky, studny, podezdívky, zídky, mosty, pece a krby – všude, kde je kámen nebo omítka.

**F2 + F bod 2 + klenby hotovo 23. 11. (hrady, PC; tablet NEOVERENO)** – chyby.md 414–418, smysl:kameny_lod0, smysl:narozi_bez_styku:
- blender/kamenivo.py (společné pro oba hrady, volá puchart_hrad.zed2, hrady.zed, zed_plynula, narozi): zub cimbuří z 2–4 řad
  nepravidelných kamenů se spárou 1,6 cm, otlučené hrany, krycí deska; krycí kameny koruny zídky / předprseně v prolukách;
  patka hradeb z větších kamenů u terénu; nárožní kvádry na vazbu po celé výšce s otlučenými hranami. LOD0 = sítě Kameny_* po
  buňkách 10 m, hlavni.gd je kreslí do 28 m (+4 m okraj), bez vrhání stínu (stín dělá jádro zubu, o 6 cm menší – jinak
  šrafování na kamenech); dál zub = kvádr zdiva, nároží kvádr s texturou jednoho kamene (kamen_kus). Data hrad_vzhled.json
  kameny_lod0 se zdrojem. Ostění oken a dveří už byla z tesaných kvádrů na vazbu (portaly.py, kit.stone_window).
- Troj. (PC, stejné místo, A/B kameny vyp./zap.): x −0,8 z 22,4 +24 k (1,58 → 1,60 M), x 1,3 z 22,3 +20 k (1,55 → 1,57 M);
  celkově před začátkem práce 1,685 / 1,656 M → 1,602 / 1,570 M (včetně souběžných změn krajiny). Kreslení +11.
- Omítka (hrad_puchart.json omitka_zdiva): paláce líc vápenná omítka místy opadaná (zdivo_omitka_opadana), strana v hradbě
  kámen, uvnitř místností omítka; sklep a šíje A režné lomové zdivo (zdivo_rezne). Klenby (kamen_klenak) a kamenné stupně
  (kamen_stupen): textura jednoho kamene s UV po plochách kvádru – bez natažení světovou projekcí, bez reliéfu zdiva.
- Zbývá z F: stavby vsi, mosty, studny, pece (F platí pro všechny stavby – Míša 18. 11.), klenební pasy z kamenů v geometrii,
  vypadlé kameny; klenáky nemají spáru v geometrii (jen předěl textury).

## G. Míša 19. 11. (APK f60122c) – k dalšímu kolu
| č. | snímek | co |
|---|---|---|
| G1 | misa_19_11_zdivo_1/2.jpg (x −0,8 z 22,4) | hradby a kámen celkově „s tapetou vypadají fakt blbě“ – rozmazaný pixelový kámen zblízka, natažený na cimbuří → plán F (priorita) |
| G2 | misa_19_11_voda_1/2.jpg (x −76 z 124, x −47 z 121) | voda „bílá, nic moc, skoro vyschla“ – mělký potok vypadá jako bílý štěrk/prázdné koryto; tmavší, méně průhledná hladina, víc vody v korytě (hloubka/výška hladiny) |
| G3 | misa_19_11_nadvori_A_srovnat.jpg (x 5,9 z −11,7, směr 269°) | kroužek = místo ke srovnání do roviny (Z kout nádvoří A u hradby pod ochozem) – plošina v hrad_puchart.json teren.plosiny |
| G4 | misa_19_11_staj_misto.jpg (x 5,4 z 4,5, směr 204°) | sem umístit STÁJ z Havrana (model z větve claude/new-session-0dtk58), u hradby JZ nádvoří A pod ochozem |
Míša 19. 11. (misa_19_11_svah_ridky.png, kroužek na svahu pod hradem z x 131 z 276): i po E2/E3 svah 30–80 m řídký –
rozházené jednotlivé byliny jako tečky, mezi nimi hladký terén, mizející rostliny jako šachovnice (dither přechodu).
→ E1 (střední pás: husté levné trsy/impostor buňky 20–150 m podle předlohy lod_trava_video) je nutný; samotná textura
terénu (E2) a delší dosah (E3) nestačí. Dither přechodu nahradit plynulým (alfa/řídnutí hustoty), ne šachovnicí.
Míša 19. 11. (misa_19_11_krajnice_holé.png, x 131 z 276 po E1 kroku 1): svah pořád řídký (byliny jako ostrůvky) a OBĚ
KRAJNICE CESTY HOLÉ – pás 2–5 m vedle vyjetých kolejí je jen plochá textura trávníku bez trsů. → E5 (lem trávy a bylin až
ke kolejím) první na řadě: zjistit, proč louka/byliny vynechávají pás u cesty (třída stanoviště „cesta“ širší než koleje?
maska cest v louka.gd/byliny.gd?) a zúžit vyloučení jen na vyjeté koleje; pak E1 (husté trsy na svahu).

## H. Míša 20. 11. (APK 166e19d)
| č. | snímek | co |
|---|---|---|
| H1 | misa_20_11_voda.jpg (x 136,9 z 155,9) | voda „není pěkná a měla by být“ – tmavá plochá s bílými šmouhami vln, bez odrazu; plán D (Hvozd) dotáhnout pořádně |
| H2 | misa_20_11_dira.jpg (x 127,1 z 30,3 směr 4°) | díra v povrchu terénu u přechodu cesty přes potok (brod) – terén nad korytem nenavazuje |
| H3 | misa_20_11_vykon.jpg + ostatní | výkon: troj. 2,27–2,70 M (rozpočet 2,1 M), p95 až 63 ms, záseky 171–416, automatika stupeň 2/4 – rozšíření trávy 19. 11. (dosah 96 m, hust_zbytek 0,35, krajnice) je na tabletu drahé → nahradit plánem E1 (buňky), zatím vrátit dosah/hustotu |

**E1 hotovo 23. 11. (PC, tablet NEOVERENO):** jemné trsy do 45 m (buňka 16 m), střední pás 25–150 m = karty s pečenou texturou porostu (louka.json pas, nastroje/trava_pas_atlas.py, stebla.gdshader rezim 2, zkosení podle svahu v transformaci instance), keře dosah 48 a byliny 40 (= konec zániku), automatika stupeň 1 = pás blíž. PC troj. ve Míšiných polohách 1,86 → 1,55 M (x 131,4 z 276,4 sever) a 1,78 → 1,30 M (x 146,7 z 311 směr 273°); chyby.md 413, smysl:stredni_pas_travy. Zbývá E2 (dálka za 150 m) a impostory keřů.
| H4 | misa_20_11_vykon (svah s hradem) | černé skvrny na svahu pod hradem (stíny/impostory?) – prověřit |
| H5 | misa_20_11_staj_tma.jpg (x 8,4 z 16 – i s loučí) | stáj uvnitř skoro černá i s hořící loučí – zjistit příčinu (stáj bere „interiér se stropem“ → světlo jen z otvorů? tmavé dřevo prkna_ven/dub? louč nesvítí na dřevo stáje?) – zesvětlení pod_strechou 1,6 nepomohlo a přesvětlilo místnosti → vráceno |
| H6 | misa_20_11_svy.jpg (x 8,2 z 24,3) | svislé tmavé švy / rýhy na zdech a nároží (spáry mezi díly zdí – úkol #25) + kámen pořád „tapeta“ (plán F) |

**H6 hotovo 23. 11.** (chyby.md 415, smysl:narozi_bez_styku): příčina nebyla mezera sítí, normály ani UV – nárožní kvádry
(hrady.narozi) se kladly na všechny rohy věží, paláců a pilířů, i tam, kam přiléhá hradba; ve styku trčely 1–3,5 cm z líce po
celé výšce (stín + mech zdivového shaderu na horních plochách = svislý šev a vodorovné čárky). Nároží se teď staví až po všech
zdech (kamenivo.dokonci) a na rohu s přiléhající zdí se nekladou (402 kamenů); kontrolní snímek ze stejného místa bez švu.
**Hlídač spojů 34 > 32** (chyby.md 417): ne stáj – slučování konců zábradlí do těžiště posunulo madlo ramene schodiště ochozu A
o 5,6 cm a sloupky prošly schodnicí; konec zábradlí ramene je teď pevný → 28.

H5 rozbor 20. 11.: hlavni.gd pozná „uvnitř“ paprskem 25 m nahoru (interier.paprsek_nahoru_m); ve stáji trefí kolizi ochozu nad ní (~8 m) → hra ji bere jako uzavřenou místnost se stropem (světlo jen z otvorů) → černo. Oprava: strop jen do výšky místnosti (např. ≤ 5 m nad hráčem) nebo stáj vyjmout z kolize stropu; pozor na vysoké síně hradu – ověřit.
H5 návrh (promyšleno 20. 11., Míša: „stáj nemá přední díl – světlo dovnitř, stín dělá jen střecha“):
- Dnes: 1 paprsek nahoru 25 m → zásah = „uvnitř“ (0/1). Chyba principu: neřeší, zda je prostor ze stran otevřený, a bere
  i cizí kolize vysoko nad hlavou (ochoz nad stájí, krakorce, koruna zdi).
- Nově „otevřenost oblohy“ jako podíl: z hlavy hráče 9 paprsků do polokoule (1 nahoru + 8 šikmo 35° nad vodorovnou ve 8
  směrech), délka ~12 m. uvnitr = podíl zablokovaných (plynule 0–1, vyhlazeno v čase). Stáj/přístřešek/pavlač: zablokovaný
  jen paprsek nahoru a strany ke zdi, k otevřené straně volné → uvnitr ~0,3–0,5 → venkovní světlo mírně tlumené střechou.
  Místnost se stropem a okny: všechny zablokované → 1 (jako dnes). Vysoká síň: zablokované (strop i stěny) → 1 (správně).
- Stín střechy sám dělá stínová mapa slunce (do 40 m) – světlo „zvenku“ pod střechou nemá být dál tlumeno; pod_strechou
  nastavení pak sjednotit s novým podílem (méně zvláštních případů).
- Cena: 9 paprsků každých 10 snímků (dnes 1) – zanedbatelné; data: interier.otevrenost {paprsku, uhel_st, delka_m}.
- Kontrola: stáj (x 8 z 16), pavlač krčmy, přístřešek kovárny, síň paláce A, sklep, půda – podíl vypsat v panelu FPS.

Stav 23. 11. (H1, H2, D1–D2): H2 = šikmý brod, ne otvor v síti – cesta osm_track_1/2 kříží tok 4 pod 58° od kolmice, nájezd
koryta.py byl jen kolmo na tok, cesta stoupala přes val břehu 42 % a za hřbetem byla vidět hladina. Pás brodu je teď i v ose
cesty (všech 14 brodů ≤ mezí, smysl:brod_v_ose_cesty, chyby.md 411). H1 + D1–D2 hotové podle Hvozdu (chyby.md 412,
smysl:voda_odraz_hvozd): odraz z panoramy lesa (Poly Haven Niederwihl Forest CC0) do EMISSION × okolí dne, tělo hnědé →
černozelené, dvě vrstvy vln, pěna u kraje a na peřejích, krytí 0,2 → 0,7 → 0,92. D3 (přízemní mlha) neuděláno. Tablet NEOVERENO.
Zbývá (stará chyba, nezhoršeno): na okraji jemného pásu BREH u brodů 0,3–0,5 m schod mezi BREH a sítí dlaždic (BREH napříč
v brodu jen 5 bodů na 4–20 m – chorda nad zářezem); vidět jako tmavý lem vpravo na kontrola_23_11_brod_dira.jpg.

**Stav 23. 11. (F ves, C4, A4, C1, B3; PC, tablet NEOVERENO):** F mimo hrady – audit všech glb vsi (deskové plochy s texturou dřeva):
stěny, vrata, ploty, štíty a podbití domů/krčmy/hájovny/kovárny/mlýna už jsou z prken v geometrii; tapeta zbyla na střechách
stodol a kůlen a stříškách krytých vrat → šindel v geometrii (řady s čely, LOD0 do 35 m, dál deska; chyby.md 421). C4: proutěné
díly plotu otočené/výškově různé, šindel po úsecích jiný výřez a tón (422); zídky ve vsi nejsou. C1: pokus na velké stodole –
vlhko, špína, stékance, mech k severu v barvě vrcholů, 4 varianty podle natočení (423). A4: kůra LOD1 decimovaná v Blenderu
(blender/stromy_lod_kmen.py, 172,7 → 80,1 tis. troj.), les x 136,9 z 155,9: 2,005 → 1,929 M (sever), 1,796 → 1,646 M (východ)
(424). B3: `nastroje/foto_tri_svetla.sh "x,z,y,cx,cz,cy" prefix [hodiny]` – jeden start, snímky ráno/poledne/soumrak/noc
s loučí v ruce (hlavni.gd PUCHART_FOTO_CASY), 4 snímky ~1,5 min. Mosty a lávky (blender/voda.py) nekontrolovány – soubor krajiny.

**Stav 23. 11. odpoledne – krajina (E2, H4, E4, C2, C3, C5, C6; PC, tablet NEOVERENO).** PC troj. ve Míšiných polohách
(nastroje měření mer_troj, 500 snímků ustálení): x 131,4 z 276,4 sever 1,586 → 1,744 M, x 146,7 z 311 směr 273° 1,321 → 1,411 M
(nárůst hlavně keře E4: těžší modely liska_3, hloh_3, trnka_3, šípek 2–3 a nové zmlazení; rozpočet 2,1 M drží).
- E2: zem.gdshader porost_dal_* (louka.json porost_dalka): od 110–190 m trsy 9/4,3 m, tmavé skvrny 23 m, světlá místa, barevný
  šum – 0 vzorkovačů, +5 čtení šumu. Na PC v protisvětle (směr 267–273°) kopec 150–250 m pořád spíš tmavý a klidný (ACES + kontrast
  stlačí tmavé rozdíly) – docs/screens/kontrola_23_11_e2_273.jpg; ověřit na tabletu za světla od zad.
- H4: černé skvrny = skalní výchozy (skaly.glb, skala.gdshader) – fotka droby průměr 0,088 → ve stínu 0,0,0; pudy.json skala_vychozy
  albedo_cil 0,45 (chyby.md 425, smysl:skaly_bez_cerne, docs/screens/kontrola_23_11_h4_svah.jpg).
- E4: každý druh ≥ 3 modely (smysl:tri_modely_druhu) – z knihovny Havrana modely/nove + vrba_ker_3 z rostliny_u_vody.py; mladé
  stromy: buk, jedle + dub, olše, lípa podle stanoviště. Výjimka padlé stromy (2 modely, e4_vyjimky, varování) – třetí CC0 padlý kmen
  střední Evropy není, kmen_* Havrana jsou pokácené klády (Míša 13. 11.) → vývrat z blender/havran/strom2.py NEUDĚLÁNO.
- C2: louka.json kraj_cesty – krajnice po úsecích ~7 m: holá hlína s kameny / tráva / květy (louka.gd + byliny.gd stejný šum).
- C3: byliny.json voda_pas.pasmo – kameny u čáry vody, tráva za nimi, pak keře břehu (vrba_ker 1–3, olše zmlazení); stromy první řady
  dělá les (stromy.bin) – beze změny (jiný pomocník).
- C6: stebla.gdshader ohyb_hrac (louka.json ohyb) – jemné trsy se odkloní od nohou do 0,9 m. Trava_sada bylin (bylina.gdshader) ne.
- C5: zem.gdshader mraky_stin – putující stíny mraků od 60–140 m, ze šumu (vzorkovačů 9), bez vazby na zatažení (NEOVERENO).
