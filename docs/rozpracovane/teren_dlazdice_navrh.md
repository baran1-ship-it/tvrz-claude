# K4 – terén na dlaždice s LOD (návrh a stav, 16. 11.)

Podklad: `docs/rozpracovane/rozbor_gpu_15_11.md` (Z3, K4, „Potvrzení z Pucharta“), Puchart
`origin/ccr-f2d32673-9fi7m5`: `puchart/nastroje/teren_dlazdice.py`, `puchart/pravidla/svet/teren.json`,
`puchart/hra/scripts/svet.gd` (`_ready`, `_postav_dlazdici`, `_sit`, `_umisti`).

Značky jako v rozboru: **NAMĚŘENO**, **POTVRZENO V KÓDU**, **PODEZŘENÍ**, **NEOVĚŘENO NA ZAŘÍZENÍ**.

## 1. Dnešní stav (POTVRZENO V KÓDU)

Terén staví Blender (`blender/kraj.py`, `blender/export_game.py`) jako pásma `Teren_*` v `modely/tvrz.glb`
(Teren_toky 163 k, Teren_okoli 133 k, Teren_reka 99 k, Teren_ves 47 k, Teren_obzor 40 k, Teren 30 k, Teren_cesta 18 k,
Teren_most 13 k troj. – rozbor Z3). Hra pak sítě při stavbě světa (`scripts/svet.gd` `build`, ř. 683–811) mnohokrát
přepisuje (`mi.mesh = …`). Pořadí kroků, které smějí terén měnit, hlídá test `zamek_terenu`
(`pravidla/pravidla_sveta.json` `pasma.test.poradi_terenu`; stopa `svet.gd:582` `teren_kroky`, `_krok_cas` ř. 662):

| krok (poradi_terenu) | kde | co dělá se sítí Teren* |
|---|---|---|
| `_vo_scena` | `svet.gd:307` (`_vo_sit` 339, `_vo_teren` 454) | ves v oblouku: výška a barva Teren_ves / Teren_toky pod usedlostmi |
| `koryto: _terasa_terenu` | `svet.gd:1463` | terasy (schody svahu) ve vrcholech |
| `koryto: _prikop_zaplata` | `svet.gd:1346` | příkop tvrze |
| `koryto: _dno_toku` | `svet.gd:1625` | dno malých toků (Teren_toky) |
| `koryto: potok a nádrže` | `svet.gd:1670–1759`, `koryto.gd:396 pokryj`, `koryto.gd:422 vyhloub`, `koryto.gd:481 sukne` (nová síť `<pásmo>_sukne`), `nadrz.gd:282 vyhloub`, `nadrz.gd:340 hloubka_hladiny` | zářez potoka, nádrže, bahno v COLOR.a |
| `koryto: _najezdy_mostu` | `svet.gd:2977` (`_najezd_sit` 3073) | nájezdy mostů |
| `koryto: _teren_pod_vraty` | `svet.gd:2109` | terén pod křídly vrat |
| `koryto: _upravy_terenu` | `svet.gd:11172` | úpravy z dat (srovnání u staveb) |
| `koryto: _cesty_tvar` | `svet.gd:8080` (`_cesty_do_terenu` 8339) | cesty = terén: zářez/násyp, CUSTOM0/1 (koleje, okraj) |
| `koryto: _koryta_naposled` | `svet.gd:2047` | koryta malých toků po všech úpravách |
| `_lom_stena_svisla` | `svet.gd:12599` | lom (nová síť Teren_lom_stena) |
| `_rybnik_dil` | `svet.gd:9782` | terén hry pod dílem rybníka |
| `_mlyn_dil` | `svet.gd:10141` | terén pod dílem mlýna |
| `_ves_domy` | `svet.gd:6936` | terén pod domy vsi |

Mimo pořadí: `_zaplaty` (`svet.gd:2257`, nová síť `Teren_zaplata`), kolize `_trimesh` (`svet.gd:2541`, tělo
`<síť>_kolize` jako dítě sítě) a `_zamek_terenu` (`svet.gd:8446`: kolize znovu z hotové sítě + mřížka výšek). Po zámku už
žádný krok síť terénu nemění (stopa `teren_kroky`). `_rozdel_site` (`svet.gd:821`) terén záměrně nedělí
(`svet.gd:836`: „ImporterMesh.generate_lods v běhu hry LOD nevytvoří (0 úrovní, ověřeno), béžové plachty 0.60“).

Kdo potom síť terénu čte podle jména `Teren*` (nesmí se rozbít): `_sled_bod` (642), `_krok_cas` (669),
`_chyse_na_sit`/vrchol pod body (7123), `_cesty_*` (8297, 8341), `_zamek_terenu` (8453), okluzory (8480), výška u tvrze
(13699), `diag.gd:1017` (skupina „teren“), `tools/reka_bake.gd`, testy (`test_svet.gd`, `zamek_terenu`, `bod`…).
Materiál: `_apply_materials` (`svet.gd:1179`) dá každé ploše sdílený `material("zem…")` (zem.gdshader; vrcholy nesou
COLOR, CUSTOM0 a CUSTOM1 – cesty, bahno, koryto). Stín terén nevrhá (`svet.gd:744`).

**Proč „béžové plachty“ 0.60 (PODEZŘENÍ):** `_rozdel` (`svet.gd:861`) kopíruje jen VERTEX, NORMAL, TANGENT, COLOR,
UV, UV2 – ne CUSTOM0/1. Terénu by po dělení chyběly údaje cest. Druhá polovina („0 úrovní LOD“) v Godotu 4.4.1
neplatí: sonda `generate_lods` na mřížce 128×128 dala 6 úrovní (NAMĚŘENO 16. 11., build/beh/lodprobe.log); zdroj
`importer_mesh.cpp:461` používá `SIMPLIFY_LOCK_BORDER`, meshoptimizer je i v šablonách (`config.py: not disable_3d`).

## 2. Návrh (zvolený)

Herní úpravy terénu do exportu přesunout nejde bez přepsání ~15 kroků (koryto, nádrže, cesty = terén, díly, domy) –
to je samostatný projekt a koliduje s prací na zemljankách. Zvolil jsem druhou variantu ze zadání: **krok dlaždic běží
na hotové síti**, jako poslední krok `svet.build` (po `_zamek_terenu`, rostlinách i okluzorech), a nic dřívějšího
nemění. Postup dlaždic je Puchartův (dlaždice, LOD uzly, hystereze, sukně, vše offline), jen zdrojem není výšková
mřížka, ale hotová síť.

- **Pravidla:** `pravidla/svet/teren_dlazdice.json` – `zapnuto` (jediný přepínač návratu, výchozí `false`),
  `dlazdice_m` 128, `lod` [{do_m 180, chyba_m 0}, {450, 0,3}, {100000, 1,2}], `hystereze_m` 20, `sukne_m` 1,
  `site` (předpona, vynechané `Teren_obzor`, `Teren_cesta_kamen`, sukně, `min_troj`), soubor + index, `kdyz_neplatne`,
  otisk, prahy testu. Žádné číslo v kódu.
- **Kód:** nový `scripts/teren_dlazdice.gd` (uzel `TerenDlazdice` vedle modelu světa). Háčky: `svet.gd` 3 řádky
  (proměnná `teren_dlazdice` + volání `pripoj` za `_okluzory`), `diag.gd` 2 řádky (síť s `layers == 0` se nepočítá),
  `main.gd` (env `TVRZ_DLAZDICE_PEC` spustí hru bez menu), `mereni_trasa.gd` varianta, `pregeneruj.sh dlazdice`,
  `vydani.py --jen z_dlazdice`.
- **Kusy:** trojúhelníky každé sítě podle těžiště do čtverce `floor(x/128), floor(z/128)`; v dlaždici se spojí pásma
  se stejným materiálem a formátem (méně kreslení). **LOD0 = přesná kopie** všech polí včetně CUSTOM0..3 (formát
  z `surface_get_format`, bez komprese – kvantování podle AABB kusu by posunulo sdílené hrany).
- **Hrubší úrovně:** `ImporterMesh.generate_lods` (meshoptimizer, `SIMPLIFY_LOCK_BORDER`) – vybere se nejhrubší LOD
  s chybou ≤ `chyba_m`; okrajové vrcholy kusu se nehýbou, takže sousední dlaždice v jiné úrovni a švy pásem navazují
  přesně (bez T-spojů). Úroveň bez zisku (> 80 % troj.) se sloučí s předchozí. Sukně (`sukne_m`, oboustranné, svisle
  dolů po okrajových hranách) jen u hrubších úrovní – pojistka jako u Pucharta.
- **Bez přeskakování:** rozsahy jako Puchart `_umisti`: začátek = do_m předchozí − h, konec = do_m + h, margin h,
  `FADE_DISABLED` (Godot `_visibility_range_check`, renderer_scene_cull.cpp:2827: skrytá instance má rozsah zúžený
  o margin, viditelná rozšířený → hystereze; překryv 2h zaručí, že ani po startu/teleportu není díra).
- **Původní sítě zůstávají:** kolize (plné rozlišení, `_kolize` těla), výšky, testy a všechny `find_children("Teren*")`
  dál vidí hotovou síť. Jen se nekreslí: `layers = 0` (ne `visible` – kód i testy neviditelné sítě vynechávají).
  Dlaždice se jmenují `D_<i>_<j>_<n>_L<k>` pod `TerenDlazdice` – hledání `Teren*` je nenajde, diag je počítá do
  skupiny „teren“ podle rodiče.
- **Offline:** `TVRZ_DLAZDICE_PEC=1 godot --headless --path .` (= `bash tools/pregeneruj.sh dlazdice`) postaví svět
  jako tablet, z hotové sítě upeče `modely/teren_dlazdice/dlazdice.scn` (komprimovaný PackedScene) a `dlazdice.json`
  (otisk hotové sítě: počty vrcholů/indexů + výška každého n-tého vrcholu, tolerance 2 cm – PC × ARM).
  Hra: soubor načte, otisk ověří; nesedí-li (jiný export), `kdyz_neplatne: stara_cesta` = celé sítě (bezpečné), nebo
  `pec_za_behu`. Materiál a rozsahy se nastaví při načtení (sdílený materiál země, změna `do_m`/hystereze bez nové pece).
- **Návrat:** `"zapnuto": false` (výchozí) = 0.999999 beze změny; `TVRZ_DLAZDICE=1` / `=0` pro zkoušky.
- **Měření:** varianta `teren_dlazdice` v `pravidla/svet/mereni_trasa.json` (hned za „vše“) – zapne dlaždice za běhu
  (pečená sada, jinak peče za běhu), porovnání vše × teren_dlazdice ve stejném běhu.

## 3. Výsledky (PC, 16. 11.)

Test `teren_dlazdice` (`tools/beh.sh dl1 testy teren_dlazdice,zamek_terenu,pravidla_cteni`, export 15. 11. + herní
úpravy, pečení za běhu): **OK**. `zamek_terenu` OK (krok dlaždic síť nemění), `teren_dlazdice.json` 0 nepřečtených klíčů.

- Zdroje: 6 sítí (pásma s ≥ 4000 troj., bez Teren_obzor), po herních úpravách **705 971 troj.** (víc než 547 k z glb –
  úpravy přidávají trojúhelníky). 273 kusů (dlaždice × materiál/formát), pečení za běhu na PC **4,7 s**.
- Troj. po úrovních celkem: L0 705 971, L1 205 247 (chyba ≤ 0,3 m), L2 117 105 (≤ 1,2 m). Hrubé úrovně brzdí zamčený
  okraj (okraj každého kusu zůstává v plném rozlišení) – NAMĚŘENO, prostor pro další krok (větší dlaždice pro L2).
- Pokrytí (28 798 bodů po 8 m): L0 bez děr, shoda s původní sítí 0,00 m; L1 max 0,21 m, L2 max 1,18 m, děr 0;
  kolize se liší od původní sítě ve 12 bodech a od LOD0 v týchž 12 (dlaždice nesoulad s fyzikou nepřidávají).
- Škvíry: šachovnice úrovní (L0/L1, L1/L0, L0/L2, L1/L2) po hranách dlaždic, 451 296 bodů: **0 škvír**.
- Troj. v zorném jehlanu (výpočet jako Godot: ořez AABB + vzdálenost ke středu AABB, bez hystereze):

| místo → cíl | celé sítě | dlaždice | kusů | podíl |
|---|---|---|---|---|
| tvrz (0, 40) → (0, 300) | 705 971 | 321 637 | 72 | 46 % |
| kopec (73, 947) → ves (470, 830) | 655 874 | 227 234 | 58 | 35 % |
| potok (822, 215) → (600, 600) | 673 520 | 317 141 | 79 | 47 % |
| ves (440, 820) → (650, 950) | 655 874 | 121 677 | 22 | 19 % |
| les (−197, 988) → (300, 900) | 673 520 | 290 237 | 81 | 43 % |

Výkon na tabletu: **NEOVĚŘENO NA ZAŘÍZENÍ** – varianta trasy `teren_dlazdice`.

## 4. Rizika a otevřené body

- **Paměť GPU:** původní sítě zůstávají nahrané (kvůli dotazům a kolizím) + LOD0 kopie + hrubší úrovně ≈ +25–35 MB
  bufferů (ODHAD). Další krok: po stavbě původním sítím vrátit jen CPU data (kolize a výšky z mřížky) – samostatná změna.
- **Soubor a export:** pečená sada platí jen pro jeden export a jeden stav herních úprav terénu (otisk). Po každém
  `tools/export.sh` nebo změně kroku z tabulky výše: `bash tools/pregeneruj.sh dlazdice`, jinak hra kreslí celé sítě
  (bezpečné, ale bez zisku). Balík: `modely/teren_dlazdice/*` je v balíku svet, v kontejneru bez zdrojů opravný
  `--jen z_dlazdice`.
- **Překryv 2h při přechodu:** na hranici úrovní se ve 40 m pásu kreslí obě úrovně (Puchart to přijal, je to cena za
  žádnou díru). V ~180 m může problikávat z-fight dvou úrovní – PODEZŘENÍ, ověřit na tabletu.
- **Kreslení:** místo ~8 velkých sítí desítky kusů v záběru (+~50–100 kreslení, rozpočet ≤ 1500).
- **Pečení za běhu na tabletu** (jen varianta trasy / `pec_za_behu`): GDScript + meshoptimizer nad 0,55 M troj. –
  sekundy (NEOVĚŘENO NA ZAŘÍZENÍ). Pro hru jen pečená sada.
- **Předehřátí shaderů:** kusy mají stejný materiál, ale nekomprimovaný formát vrcholů – možná nová kombinace
  (main.gd předehřátí). PODEZŘENÍ, ověřit prvním průchodem trasy.
- Teren_obzor zůstává jedním kusem (40 k troj., K9 řeší obzor zvlášť).
