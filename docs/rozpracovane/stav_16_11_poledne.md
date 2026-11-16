# Stav 16. 11. ~poledne – pauza do 17:00 (limit session)

Vydaná verze: 0.999999 (16. 11. 01:04) – na tabletu padá po 2. kole trasy (textury +222 MB, misa_16_11_chyby.md ř. 7).
Míša chce další vydání se VŠÍM (ne bez scén). Kontrolovat snímky pomocníků sám (predani.md 16. 11.).

## Rozpracováno (pokračovat po 17:00, pomocníci se probudí SendMessage, nebo nová práce podle těchto bodů)
1. **Lůžka/pece/zemljanky/seno/uhlíři** – hotové a testy OK, ALE: barvy sena (modrošedé) a lůžkovin (černé) a houní
   (tmavě modré) špatně → převzít postup Pucharta (nativní .tscn + sdílený materiál, `barvy_vrcholu.json` lineární→sRGB,
   `seno.json` albedo_modulace); seno do žebřin/jeslí na zdi stáje, ne kupa na zemi; pec v chalupě do rohu (pravidlo
   v `tools/krok_b/pece_domu.py`), postel ne uprostřed; plamen v peci krčmy. Tabulka `misa_16_11_sady.md`.
2. **Scény** (houština, malebná uzavřená ves, pole jen za vsí, les s podrostem, řeka opatrně) – pomocník rozpracoval,
   plán `sceny_kcd_15_11.md` (+ jeho poznámka stav a další krok). Na konci JEDEN export světa (zahrne vše níž).
3. **Sdílené textury dílů** (paměť) – krok 17 exportu hotový (`textury_predmetu.py dily`, modely/dily_tex), zbývá
   změřit MB před/po a snímky; ř. 7.
4. **Doubrava/sklep/krčma/rybník** (misa_16_11_chyby.md ř. 1–6) – Blender část v exportu zem2, rybník ve hře (nadrz),
   ověřit snímky.
5. **Houby** ve vzduchu – opraveno (uprava_y), test houby_na_zemi OK; kopřivy pod terénem (ř. 10) otevřené.
6. **Dlaždice terénu** – hotové, vypnuté (`teren_dlazdice.json zapnuto false`), upéct znovu PO posledním exportu
   (`tools/beh.sh dlazdice cmd bash tools/pregeneruj.sh dlazdice`), varianta trasy teren_dlazdice.

## Pořadí do vydání
pomocníci dokončí → git pull → export světa (`BEH_LIMIT=7000 tools/beh.sh export_X cmd bash tools/export.sh`) →
upéct dlaždice → testy po skupinách → snímky (prohlédnout!) → nezávislá kontrola subagentem → celá sada testů
(`TVRZ_TEST_LIMIT=6600`) → `vydani.py 0.9999991 --testovaci --jen z_svet,z_krcma,z_kostel,z_ruiny_ves,z_ves,z_rostliny,
z_katalog,z_reka,tex_predmety2,z_dlazdice,… + p_* nových předmětů` (seznam z hlášení pomocníka lůžek) → zpráva Vydáno.
Postavy (z_postavy) stále rozbité (15 sad, ř. 22 tabulky 15. 11.) – nevydávat.

## Doplněno před pauzou (hlášení pomocníků)
- **Textury dílů HOTOVO:** ETC2 211 → 87 MB (Doubrava 117 → 25), PC grafika 1322 → 1208 MB, testy OK; prohlédnout
  `build/dily_tex/po2_doubrava.png`, `po2_krcma.png` (fronta za exportem scén). Kovárna/mlýn v kontejneru bez glb (vynecháno).
- **Míša ř. 1–6 HOTOVO** (testy OK: ruiny_ves, sklep_vstup, prochod, krcma_l/dvur/schody, ryb_napojeni); otevřené:
  `ryb_vznaseni` 6 vrcholů 0,06–0,13 m (úhlopříčky čtverců); prohlédnout `build/m16/*.png` (sklep, vrata krčmy, lávka, přeliv).
- Focení: NIKDY dvě focení najednou (2× Killed – paměť kontejneru).
- Budík přesunut na 17:25 (reset limitu 17:20).
- **Scény HOTOVO v datech, export `export_sceny` běžel ve 14:15 (výsledek v build/beh/export_sceny.log)**: pole jen za vsí
  (plochy.json pole.za_vsi), houština (les_podrost.json houstina: meze, břeh s mezerami, plášť lesa, podrost), clony vsi
  (kompozice.clony, ves.zelen_ulice, ves.ploty_ulice), výhled prijezd_ves na hraně svahu, okluzor_houstina, varianta
  bez_houstin. Test smyslu OK (982 kusů houštiny). Další krok: oddíl „Stav a další krok“ v sceny_kcd_15_11.md
  (výsledek exportu → dlaždice → testy clona_vsi, houstina_volno… → snímky po dvou bězích, PROHLÉDNOUT).
  Riziko: jabloně u vjezdu 24–28 tis. troj. (výkon ves-vjezd).
