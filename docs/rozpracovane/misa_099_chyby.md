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
