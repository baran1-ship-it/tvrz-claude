# Míša 0.99 (28. 10. večer) – snímky z tabletu, 40 fotek

Každý řádek = chyba od člověka → oprava záznamu/pravidla + kontrola v testu (CLAUDE.md). Stav: OTEVŘENO.

| # | Co | Kde | Příčina (zjistit) | Kontrola v testu |
|---|----|-----|-------------------|------------------|
| 1 | Potok všude „kanál bagrem“: svislé kamenné stěny, zuby, rovné úseky, lomy | všechny toky | profil koryta v Blenderu (lichoběžník, kámen), osa z A* | profil břehu (sklon, šířka), zakřivení osy |
| 2 | Vypusť/vpusť rybníka a prameny = rovné kamenné žlaby | rybníky, prameny | totéž | totéž |
| 3 | Postavy a tělo hráče v T-póze | celá ves, mlýn, příkop | lide.gd/telo.gd/anim_ual | test: kost ruky ≠ klidová póza po 1 s |
| 4 | Tráva uvnitř mlynářova domu (chalupa u větrného mlýna) | ~ (469, 1196) | chalupa k=30 není v maskách vegetace | test uvnitr_na_podlaze pro chalupu |
| 5 | Do mlýna nejde vejít | vodní mlýn ~ (597, 912) / větrák | postava stojí ve dveřích? kolize | test průchodu dveřmi |
| 6 | Větrný mlýn se točí moc rychle | (479, 1212) | rychlost křídel | číslo z dat, rešerše ot/min |
| 7 | Na kolo neteče voda ze žlabu | vodní mlýn | žlab končí nad kolem bez proudu | test: voda žlabu nad kolem |
| 8 | Pytle ve mlýně hnusné (roztažená textura) | vodní mlýn | vlastní primitivum | hotový model (Poly Haven/Kenney/Disk) |
| 9 | Brána ve vsi: jen křídla, chybí plot a stříška | (388, 757) | díl brány posunut/oříznut | test: vrata mají sloupy+plot |
| 10 | Holé světlé fleky bez trávy, schodovité okraje povrchu | stan, svah, mlýn, rybník, pšenice | maska dílu / splat rozlišení | test povrchu dílu |
| 11 | Suchý příkop s levitujícími kameny; kulatý černý rybník | hrad, les (-128,-132) | voda příkopu, tvar rybníka | voda_v_korytu suche, kameny na zemi |
| 12 | Kůň stojí v póze běhu; na pastvě se nehýbe (má se pást, přešlapovat, ocas, hlava) | kůň | stavový strom koně bez klidových klipů | test: kůň v klidu ≠ klip běhu |
| 13 | První osoba: po otočení je vidět celé tělo zvenku | hráč | telo.gd: tělo se neotáčí s kamerou / kamera mimo hlavu | test: kamera uvnitř hlavy, trup za kamerou |
| 14 | Obilí svítí jako žárovka | pšenice | materiál (unshaded/emise/albedo) | albedo v mezích (tools/albedo_textur.py) |

**Příčina #3 (T-póza) nalezena:** `modely/postavy/anim/UAL*.glb` nebyly v žádném balíku (`tools/vydani.py` skupina z_postavy brala jen
`modely/postavy/*`, bez podsložky). Oprava: rekurzivní glob + nová brána `tools/kontrola_baliku.py` (každá cesta modelu z kódu
musí být v balíku jako `<soubor>.import`).

## Stav oprav (29. 10. noc) – vše NEOVĚŘENO na tabletu (rádce 07:10), do Míšova průchodu
- #3 T-póza: balík z_postavy s animacemi (vydani.py) + brána kontrola_baliku.py. Hotovo, ověří tablet.
- #4 tráva v chalupě: louka._v_budove = půdorys každého domu (_dum_zabira). Hotovo.
- #5 do mlýna: kolize schodů z kvádrů (_schody_kolize, hrac.json schod_kolize_m). Hotovo, ověřit snímkem.
- #6 větrník 11 ot/min (lokace.json). #7 mlýn mele od začátku (voda.json bezi_na_zacatku).
- #8 pytle: síť modelu pryč, pytel_mouky z katalogu (_mlyn_pytle).
- #9 brány: plot domu se pro cestu maže jen nízkým kusem (pasma budova podjezd_m) - snímek brana.png: brána se stříškou zpět.
- #1, #2, #11 potoky/rybníky: profil, hladina pod břehy (toky_hladina.py), pás hladiny pod břeh, lesní rybník nepravidelný,
  test smyslu breh_toku + toky_nasyp. Export běží.
- #12 kůň: kun_zivy.gd (pastva, ocas, uši, dech), stání z úseku s nohama v klidu.
- #14 obilí: tint 0,62 (svet.gd TINT_LISTI). **Po exportu:** blender/nove.py `_prebarvi_zelene` přebarvuje VŠECHNY obrázky
  psenice_2 (i normálovou mapu a metal/drsnost - `set()` náhodné pořadí) → jen baseColor.
- Zelený rastr louky: zem.gdshader dva vzorky zrna (jiné měřítko a natočení).

## 29. 10. ráno – potoky po 4 exportech (NEOVĚŘENO na tabletu)
- Skutečná příčina kanálu: pojistka násep zvedala zem na hladina + 0,3 m už od kraje vody → svislá stěna u každého
  toku. Ve hře navíc maximum náspu přes všechny úseky (stěny jen ve hře). Obojí opraveno, test `breh_toku` 0 míst
  (ze 317), `toky_nasyp` 4 místa do 0,44 m v 5,7–6 m (z 303).
- Výpust rybníka Lhota: svislý zářez 2,3 m v hrázi → koryto se svahy břehu. Vtok do lesního rybníka = hladina rybníka.
- Placky chalup z terénu bez vody (pořadí stavby).
- Pytle ve mlýně: všechny povrchy M_Pytel* → katalog (obilí/mouka).

## Míša 0.991 (29. 10.) – „zatím nejlepší verze, ale chyby a sekání, někdy větší“ (38 snímků + měření)
| # | Co | Kde | Kontrola |
|---|----|-----|----------|
| 15 | Hladina malých toků = tmavomodrý neprůhledný pás jako asfalt, švy po úsecích, zuby na kraji, leží na rovině (koryto pod ní není vidět) | všechny toky, (-171,-162), (686,943), (512,864), (532,880) | ribbon jedna síť bez švů, průhledná voda (dno vidět), test: hladina toku mimo jemný terén |
| 16 | Kůň ve stání v póze trysku | kůň u tvrze | test: klip stání |
| 17 | Na koni ruce zkřížené před obličejem, pohled dolů = vidím celé tělo shora | jízda | |
| 18 | Suchý hradní příkop (hlína, kameny) | tvrz (-2,22) | voda_v_korytu suche |
| 19 | Lesní rybník bílý jako led, hnědý kruh bahna | (-155,-147) | |
| 20 | Postava chodí po střeše mlýna | mlýn (595,909) | test: cesty postav ne přes stavby |
| 21 | Tráva ve dveřích chalupy, omítka s diagonálním moaré | (474,1195) | |
| 22 | Pšenice oranžová jako barva, pravidelné čtverce | ves, (556,941), (519,955) | |
| 23 | Pytle = „sněhuláci“ / vajíčka | mlýn, větrník | |
| 24 | Záseky kreslení 120–190 ms u remízku (-145,470), FPS 15 v listnatém lese (127,895), 6 s zamrznutí | | měření |
| 25 | Dveře chatrčí u lomu nejdou otevřít | (173, 960) | test dvere_chysi (skupina, nabídka před dveřmi, otočení křídla): 29. 10. OK na současném kódu – NEOVĚŘENO Míšou |
| 26 | Záseky kreslení 60–135 ms od lomu k řece (x 187–190, z 922–945), 858 ms jednou | | měření, rozbor kreslení na místě |

**Měření kreslení A/B (f103, f104; TVRZ_MERENI_AB, o kolik ubude, když se skupina vypne):**
| místo | celkem | louka | rostliny | stíny | předměty | terén | stavby |
|---|---|---|---|---|---|---|---|
| remízek (-145,470) | 859 / 2,86 M | −63 / −0,80 M | −438 / −1,03 M | −261 / −0,64 M | | | |
| les u lomu (127,895) | 589 / 1,69 M | −68 | −98 | −169 / −0,18 M | −232 / −0,10 M | −16 / −0,62 M | −1 |
| smrky (16,988) | 462 / 1,74 M | | | −66 | 0 | −7 / −0,64 M | −34 |
| mlýn žebřík (597,920) | 979 / 2,56 M | | | −283 / −0,26 M | +19 | | |
| lom–řeka | 785 | −89 / −0,63 M | −164 | | | | |
Závěr: hlavní cena = rostliny (MultiMesh na buňku × druh) a stíny; u lomu i předměty (každý kus vybavení lomu
vlastní kreslení, 232 navíc); terén má jen trojúhelníky (0,6 M), ne kreslení. Oprava podle Astry: LOD/impostor
rostlin, rozsah stínů a sloučení pevných předmětů lomu – ne prořídnutím. NEOVĚŘENO na tabletu.

**Opravy 29. 10. dopoledne (0.991 #15–26): NEOVĚŘENO** – kůň BlendSpace, Y na koně, rozhled jezdce 95°, otěže v soustavě koně, voda_tok, prameny, postavy paprsek od kolen + _volny_bod, žebřík větrníku, práh, pytle ze záznamu, pšenice, kopyta, louka dopředu (podezření Astry na záseky – sledovat frontami v záznamu).

## Testovací 0.992 (29. 10.) – co je nového (vše NEOVĚŘENO na tabletu)
- Kovárna na tvrzi ze sady z Disku (old_smithy): výheň s ohněm, měch, ponk, kovadlina, brus, vědro, polena.
- Zvířata ve vsi: košár s 6 ovcemi za rychtou, 2 chlívky s prasaty (usedlost 2 a 6), slepice na 5 dvorech, kurník;
  ohrady z pletených plůtků z Disku (oboustranné), zvířata se pasou, chodí, slepice utíkají, zvuky.
- Menu hráče: stránky Postava (sloty, obléct/vyměnit/sundat, nosnost, výdrž), Dovednosti, Deník.
- Lešení v lomu s patry po 2,1 m (hráč nahoře nespadne o patro), žebříky všude včetně mlýna (test 10 míst).
- Dveře chatrčí v lomu (test: nabídka před dveřmi, křídlo se otočí).
- Drobnosti lomu z 60 m na 20 m (u lomu −232 kreslení).
