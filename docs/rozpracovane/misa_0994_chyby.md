# Míša 0.994 (29. 10. večer) – 17 snímků + záznam měření

Míša: „podívej se pořádně na ty fotky, to je furt dokola“. Pravidlo od teď: každá oprava se ověří snímkem **z Míšiny
polohy a směru** (HUD: x, z, výška, pohled; J = +z, S = −z, V = +x, Z = −x), ne z vlastního místa, a snímek se porovná
s jejím vedle sebe.

Tabulka ve formátu brány `tools/kontrola_tabulek.py` (2. 11.: dřív bez sloupce Stav, brána ji nečetla – díra
v hlídání). Stav „opraveno“ jen se jménem testu nebo „snimek <jméno>“ v Kontrole; ověření na tabletu = Míša.

| # | Co | Kde (Míšin snímek) | Příčina a pravidlo | Kontrola | Stav |
|---|----|-----|----------|----------|------|
| 1 | Příkop: chybí voda (suchý pruh) | (−27, 27) pohled SV | mělká stojatá voda skoro průhledná → `voda.json stojata_melko_m` 0,3 | snimek prikop (f121) | opraveno (0.995) |
| 2 | Rybník za tvrzí: přítok „peklo“ | (−128, −167) | pás potoka a hladina rybníka z různých obrysů → `kraj.ryb_obrys` (pás končí na mnohoúhelníku hladiny); zbytek (kamenné dno peřeje) neověřen | snimek pritok_nizko (f123) | rozpracováno |
| 3 | Rybník za tvrzí: odtok | (−171, −162) | – | snimek odtok (f121) | opraveno (0.995) |
| 4 | Prasata se prolínají | chlívek (412, 802) | rozestup podle velikosti zvířete (`zvirata.json rozestup_m`) | zvirata_chuze | opraveno (0.995) |
| 5 | Ovce a slepice sáňkují | košár, dvůr | nohy se za chůze netočily; + náběh/doběh kroku a náklon podle svahu (2. 11., manuál) | zvirata_chuze | opraveno (0.995, náběh 2. 11. v kódu) |
| 6 | Ovce: zvednutý ocásek | košár | klidová póza z dat (`klid_kosti`) | snimek prasata (f121) | opraveno (0.995) |
| 7 | Neviditelné zadní ploty | (404, 827) | automatické LOD tenkých plotů → `plutek_lod_bias`; vyříznutý plot = vyříznutá kolize | ohrady | opraveno (0.995) |
| 8 | Mlýn: šedé desky, voda pod dnem | (589, 892), (583, 886) | hladina v dílu = koryto modelu + 0,25 m (`mlyn.dil.potok_hladina_m`), oblouk napojení | mlyn | opraveno (0.995) |
| 9 | Potok ve vsi: zubaté okraje, holá plocha bez trávy | (489, 895) | holá plocha = díl rybníka Lhota: terén dílu v údolí pod hladinou i mimo rybníček, louka bralo „pod hladinou“ za vodu → `svet.ryb_voda` jen do voda_polomer_m + breh_sirka_m (stejně jako od_vody); zubaté okraje koryta neověřeny ; 2. 11. odpoledne zbýval holý pás pod hrází (údolí dílu pod úrovní hladiny, ale suché) → tráva dílu podle výšky nad hladinou jen v kruhu vody a břehu (`svet.ryb_v_kruhu`, `louka._vzorek`); test louka_bod: 0 holých z 283 | louka_bod | holá plocha opravena (snimek potok f123, louka_bod OK), okraje rozpracovány |
| 10 | Holé fleky a zubaté zelené pruhy na cestě ve vsi | (413, 781) | barva a výška terénu přesunutých usedlostí z nejbližšího vrcholu → bilineárně (`svet._vo_teren`) ; snímek f123 ves_cesta: **pruhy trvají** – bilineární přenos nestačí, f124 shora a u hráze: světle zelená holá zem = místa, kde barva terénu (zem.gdshader, COLOR.g) říká tráva, ale louka trsy nedá (okraj cesty, průchod, břeh) – dvě různá pravidla pro jedno místo. Příčina: po přesunu usedlostí se maska trávy (mřížka 2 m) zapsala jen při váze > 0,5, jinde zůstala hlína staré ulice, barva terénu se ale míchala plynule → maska se míchá stejnými vahami a vzorcem jako výška a barva (`svet._vo_data`) ; snímek f126: pruhy trvají – výpis barev vrcholů (test ves_maska s TVRZ_CO) ukázal pás G 0,4–0,6 podél ulice s maskou 0: ulici vsi barva terénu neznala a maska ji nulovala binárně po buňkách 2 m (`_ves_maska_ulice`) → jedno plynulé pravidlo `ves_oblouk.ulice_pas` (hlína do kraje, `pasma.cesta.ulice_vsi drn_m`, `trsy_od_m`, `barva_hliny_g`) pro barvu terénu i masku ; kolem stodol a kůlen pás 1,6 m s maskou 0 a zelenou barvou (Blender `_in_building` jen v masce) → `lokace.json ves.okraj_stavby` + `vesnice.okraj_stavby` pro barvu (`kraj.ground_attrs`) i masku (`export_game`) ; f128: pruhy trvají – jsou 6–8 m od osy, kde Blender nechal G ~0,5 (stará hlína návsi): maska tam dává řídké trsy, shader už plnou travní barvu → ve vsi travní barva země až od G, kde jsou trsy husté (`zem.gdshader` ves_k) ; export 0997 + f130: pruhy užší (shora jen lem podél hrany hlíny), zblízka zubaté okraje trvají; ves_maska 353 → 49 neshod z 814 (zbytek u (334–342, 766–770), mimo snímek) | ves_maska, snimek ves_cesta (f130) | rozpracováno (0.997 zlepšení, ověří Míša) |
| 11 | Sekání ve vsi | měření | stavby = polovina kreslení (1205 na cestě); zakrývače jen pevné; hlídač drahých průhledů (ves + mlýn) ; 2. 11. manuál „LOD pro statické stavby, počet draw calls“: domy vsi střední stupeň `_Stredni` (stejná síť, barva zapečená do vrcholů, 1 materiál) od `modely.json ves_domy_lod podrobny_do_m` 30 m místo 21–25 materiálů (`blender/ves_domy_lod.py`) ; měření f125 (PC): ves_cesta 1133 → 999 kreslení, chlívek 1153 → 1016, podíl staveb −466 → −351 a −416 → −279; + stodoly a kůlna `_stredni` (`blender/lod_barvy.py`, `predmety_lod`): ves_cesta 972 (−14 %), chlívek 978 (−15 %) | kresleni_rozbor, snimek ves_40 (f125) | rozpracováno (střední LOD v kódu, −12 %; tablet NEOVĚŘENO) |
| 12 | Břeh pod mlýnem ve vzduchu / schody nad vodou | (598, 904), (613, 921) | terén světa pod dnem toku → dno toku je záznam (`kraj.voda_tvar`); terén modelu dílu nad vodou potoka a napojení lednice → v kroku `_mlyn_dil` dolů na koryto (`voda.json mlyn.dil.lednice_napojeni`, `teren_koryto_okraj_m`) | breh_toku, mlyn | v kódu (2. 11.), čeká na export |
| 13 | Tráva doroste až po cestování | kdekoli | louka v dosahu pod zatměním | teleport | opraveno (0.995) |
| 14 | 0.995: po cestování černá obrazovka | tablet | 0.995 stavělo okolí v hlavním vlákně najednou, odtmění bez pojistky → běžné načítání do 48 m, tween při pauze, pojistka 20 s | teleport | v kódu (2. 11.) |
| 15 | 0.995: „pozdě načítání, špatná grafika“ (les) | (177, 486), (50, 828) a další | plošně vypnuté prolínání → strom ve 40 m skočil na rozmazaný impostor; prolínání u stromů zpět (`modely.json prolinani_stromu`) | snimek les_a (f122) | v kódu (2. 11.), ověřit na tabletu |
| 16 | Ves B: střechy stodol a kůlen jedna tmavá barva bez šindele | snímky ves_let, ves_nahled (f123) | UV střechy z bmesh `uv.verify()` mimo vrstvu UVMap → spojení dílů ji dalo do TEXCOORD_1, TEXCOORD_0 v bodě (totéž provazy lešení a jeřábu v lomu) → `predmety._uv_jednotne` před každým spojením; hlídač modelů s texturou | test_uv | v kódu (2. 11.), modely přestavěny (stodoly, kůlna, lešení, jeřáb; test_uv 199 modelů 0 chyb) |
| 17 | Snímek ves_dvur0 uvnitř stodoly | f123 | pevná sada snímků z doby před vsí B; místo snímku je teď půdorys stodoly → nový bod ves_dvur1 mimo stavby | snimek ves_dvur1 (f124) | opraveno (f124 ves_dvur1) |
| 18 | 0.997: „něco se moc domrvilo, dřív mikrozáseky, teď se to vyloženě sekalo“ (20 snímků, les, skály, ves 17–30 FPS, kreslení souvisle 55–75 ms) | (−202, 525), (−101, 880), (415, 800) a další | v 0.997 poprvé na tabletu: prolínání stromů (dvojí průhledné kreslení listí) a střední LOD domů do 110 m s plnou sítí místo obalu od 75 m → `modely.json prolinani_stromu` false, `ves_domy_lod stredni_do_m_mobil` 75 | prolinani | v kódu (2. 11.), vydat 0.998, ověří Míša |
| 19 | 0.997: „dům nebyl vidět, jen stodola, pak se najednou objevil“; stodoly z dálky černé | (440, 851) JZ → dům 6 (414, 876) ve 37 m | střední stupeň (šindel po šindeli) rozpustilo automatické LOD Godotu (tablet `mesh_lod_threshold` 10) → `modely.json ves_domy_lod / predmety_lod lod_bias` | lod_mezera | v kódu (2. 11.), vydat 0.999 |

### Měření 0995c (29. 10. 19:54, build/beh/retez_0995c.txt; PC, ne tablet)
| místo | kreslení | troj. | bez staveb | bez stínů | bez předmětů |
|---|---|---|---|---|---|
| ves_let | 654 | 1,72 M | −291 | −186 | −166 |
| chlivek | 1160 | 2,51 M | −513 | −343 | −271 |
| ves_cesta | 1205 | 2,53 M | −583 | −367 | −198 |
| mlyn_a | 394 | 1,48 M | −28 | −99 | 0 |
Zakrývače domů v datech nestačí: stavby vsi jsou pořád polovina kreslení. Další krok = slučovat stavby po dvorcích
podle materiálu (Astra 29. 10.: ne celou ves). Stíny na tabletu už jen 40 m (zkrácení jen se souhlasem Míši).
Snímky f121: prasata se neprolínají (bod 4 OK), mlýn a, b voda navazuje; **bod 10 trvá** (ves_cesta: zubaté zelené
pruhy na hlíně ulice – schodovité okraje barvy terénu po přesunu usedlostí).
