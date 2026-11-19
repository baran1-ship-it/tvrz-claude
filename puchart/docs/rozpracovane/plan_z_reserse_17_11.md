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
