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
| 9 | Potok ve vsi: zubaté okraje, rozlévá se | (489, 895) | násep lhota_potok; holá plocha bez trávy = staré místo usedlosti 7 | louka_bod | rozpracováno |
| 10 | Holé fleky a zubaté zelené pruhy na cestě ve vsi | (413, 781) | barva a výška terénu přesunutých usedlostí z nejbližšího vrcholu → bilineárně (`svet._vo_teren`) | snimek ves_cesta (f123) | v kódu (2. 11.), čeká na snímek |
| 11 | Sekání ve vsi | měření | stavby = polovina kreslení (1205 na cestě); zakrývače jen pevné; hlídač drahých průhledů (ves + mlýn) | kresleni_rozbor | rozpracováno |
| 12 | Břeh pod mlýnem ve vzduchu / schody nad vodou | (598, 904), (613, 921) | terén světa pod dnem toku → dno toku je záznam (`kraj.voda_tvar`); terén modelu dílu nad vodou potoka a napojení lednice → v kroku `_mlyn_dil` dolů na koryto (`voda.json mlyn.dil.lednice_napojeni`, `teren_koryto_okraj_m`) | breh_toku, mlyn | v kódu (2. 11.), čeká na export |
| 13 | Tráva doroste až po cestování | kdekoli | louka v dosahu pod zatměním | teleport | opraveno (0.995) |
| 14 | 0.995: po cestování černá obrazovka | tablet | 0.995 stavělo okolí v hlavním vlákně najednou, odtmění bez pojistky → běžné načítání do 48 m, tween při pauze, pojistka 20 s | teleport | v kódu (2. 11.) |
| 15 | 0.995: „pozdě načítání, špatná grafika“ (les) | (177, 486), (50, 828) a další | plošně vypnuté prolínání → strom ve 40 m skočil na rozmazaný impostor; prolínání u stromů zpět (`modely.json prolinani_stromu`) | snimek les_a (f122) | v kódu (2. 11.), ověřit na tabletu |

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
