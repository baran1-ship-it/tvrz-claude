# Rešerše stavu Puchartu (6. 11. 2026)

## Co máme hotové
- **Terén a krajina:** výsek 2×2 km z DMR 5G, terén upravený na stav 1393 (průrva B, příkopy A, odlesnění kolem hradů),
  vodní síť s Veličkou, les ze stromů Havrana podle skutečných biotopů (AOPK, PPV, CHM).
- **Hrad A (přední):** půdorys podle GC80T08 a náčrtu Míši, jádro 35,5 × 25 m, vnější hradba po valu s brankou a dvěma mosty,
  věžička, sklep s kobkami a šíjí. Obytný palác: kuchyně s dýmníkem, síň, roubená světnice s kamny, komora, krytá pavlač
  s venkovními schody, přístupné podkroví (rešerše docs/reference/reserse_dispozice_palacu.md).
- **Hrad B (zadní):** dvě nádvoří podle náčrtu, štít/donjon, palác, příčná zeď s branou, most přes průrvu.
- **Vzhled:** zdivo podle Havrana (spáry, malta, bez opakování textury), malta A hlinitá a B vápenitá (GC80T08), cimbuří,
  přesahy střech, zapečené stínění.
- **Cesty:** údolní cesta podél Veličky s dřevěnými mosty, hřebenová cesta, pěšiny podle OSM.
- **Hlídači:** geometrie, spoje, test smyslu, test průchodu (desítky tras), hlídač scén, matice vztahů, tabulka chyb (128 řádků).
- **Tablet:** Godot 4.7.2 Compatibility, data mimo APK (balík .pck), měření v APK.

## Chyby a rezervy (otevřené: docs/chyby.md 108–128, pořadí docs/opravy_6_11.md)
1. **Cesty a mosty** – největší rozdíl proti Havranovi: cesta je kolejiště místo kamenité, boční hrb na hřebeni, cesta nad
   terénem, mosty s kamennými opěrami a nájezdem mimo osu cesty, brody zarostlé. Chybí cesta po hřebeni k dolnímu hradu.
2. **Napojení staveb na terén:** vrata v hlíně, nájezd mostu B na svahu, zeď trčí střechou, poslední schod ze sklepa.
3. **Tesařina:** zábradlí a rohy ochozů (40+ vadných spojů, výjimka do 20. 11.).
4. **Hrad B:** nádvoří plné schodů, štít úzký, nároží hradby, chybí dveře/okna/světla, palác není obytný jako A.
5. **Skály:** „jedna koule“ a jen pod hradem – nepatří kopci.
6. **Textura:** zdivo lepší, ale výřezy fotky jsou místy pořád znát; interiéry tmavé.
7. **Výkon:** hrad p95 ~35 ms (cíl 40 splněn), les 58–71 ms a voda ~54 ms v údolí (nad cílem). Rezerva: impostory a LOD lesu,
   kratší dosah jemné vody.
8. **Proces:** chyby se vracejí (švy, schody u zdí, napojení) – víc z nich má mít automatický test, ne jen snímek.

## Historická přesnost
- **Dobře doloženo:** poloha a půdorysy obou hradů (GC80T08, DMR), dvojhrad, příkopy a průrva, malta (A hlinitá, B vápenitá),
  břidlicové zdivo, odlesnění 1393, zaniklá ves Předhradí (zatím jen v plánu), Bočkové z Kunštátu jako majitelé.
- **Rekonstrukce podle typu (poctivě značeno):** dispozice paláce (Bezděz, Valdek, Brníčko, Žebrák), pavlač, kamna, cimbuří,
  krovy a přesahy střech (konkrétní cm NEOVERENO), mosty na kozách.
- **Vlastní návrh / slepá místa:** výšky budov, okna, interiér hradu B, cesty v údolí (kde dnes II/440), hospoda a mlýn.
- **Slabiny:** hrad B ještě neodpovídá kresbě v detailech (štít, nádvoří); vozová cesta v údolí 1393 je spíš hypotéza –
  hlavní cesta vedla podle GC80T08 po hřebeni přes Boňkov.

## Hratelnost
- **Funguje:** procházka po celém výseku, oba hrady průchozí (schody, ochozy, pavlač, podkroví, sklep), mapa, rychlé přesuny,
  létání, otevírání vrat, měření na tabletu.
- **Chybí:** postavy (plán „realističtější než Quaternius“), příběh (PDF Oldřich, Boček a kluk ze vsi), předměty a interakce,
  zvuky prostředí, ves Předhradí jako živé místo, cíle/úkoly. Je to zatím **krásná procházka, ne hra**.
- **Pořadí podle PDF (krása → funkce → postavy):** jsme na konci „krásy“ – po opravách 108–128 a výkonu lesa je rozumné přejít
  na funkce (interakce, zvuky, ves) a pak postavy.

## Doporučení na další týden
1. Cesty a mosty podle Havrana (nejvíc viditelné, Havran má hotové).
2. Napojení na terén + hlídač „zeď nad střechou“ a „schod nahoru“.
3. Hrad B dotáhnout na úroveň A.
4. Skály po hřbetu a výkon lesa.
5. Pak ves Předhradí a první interakce.
