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
