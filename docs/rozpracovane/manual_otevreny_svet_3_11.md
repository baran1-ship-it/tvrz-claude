# Manuál „Velké otevřené 3D světy na omezeném hardwaru“ v1.0 (Míša 3. 11.) – rozbor pro Havrana
Plné znění manuálu je v konverzaci 3. 11. večer. Rozbor podle jeho bodu 30 (máme? funguje? důkaz problému? měření?).

| bod manuálu | co máme | stav / důkaz | co s tím |
|---|---|---|---|
| 3 buňky | louka 32 m (3 vlákna, předstih 8 s), rostliny po buňkách, dlaždice terénu; ves/tvrz celky | funguje; hranice buněk bez děr ověřuje `teleport`, `lod_mezera` | neměnit bez doloženého problému |
| 4 logika × grafika | stav vrat, dveří, větráku, mlýna v uzlech scény | nedoloženo, zda LOD ztrácí stav (dveře domů vsi `_Stredni` bez interakce – správně) | ověřit při NPC/interaktivitě (priorita E) |
| 5 autoritativní data | **rozpory Blender × Godot – 35 položek** (`rozpory_blender_godot.md`), ves už z Blenderu v novém rámci | rozpracováno; otevřené #8, #11, #13–17, #34, #35 | priorita A – pokračovat |
| 6–8 streamování | fronty louky/rostlin/kolizí s rozpočtem na snímek (`FRONTY …`), test `pamet_stani`, `fronty` | funguje; přednačítání jen podle polohy, ne směru a rychlosti (koně) | změřit doskoky hlídačem scén, pak případně předstih podle rychlosti |
| 9–10 paměť, trasa A→B→C→B→A | `pamet_okruh` (3 okruhy, halda 2190 MB stabilní), `pamet_stani` | funguje (+0,5 MB/min) | nic |
| 14 tři LOD | domy vsi podrobný/_Stredni/_Daleko, stromy LOD0/LOD1/impostor, `lod_mezera` | 0.999 oprava mizejícího domu | hlídač scén (doskoky) |
| 15 vegetace – nejdřív měřit | 0.9995: tráva 3–6 ms, kratší dosah nepomáhá (naměřeno) | v souladu | – |
| 16 **žádné ruční souřadnice ve shaderu** | **PORUŠENO:** `shaders/zem.gdshader` ř. 52 `ves = vec2(470, 830)` (výchozí, ze hry se nenastavuje – po přesunu vsi neplatí), ř. 117 obdélník nádvoří tvrze `(-27.6, -16.6)–(18.5, 17.4)` | potvrzeno čtením kódu | převést na uniformy z dat (lokace.json ves, tvrz nádvoří), nastavovat ze svet.gd – další verze |
| 17 grafické profily | mobil/PC přepínače v kódu (`OS.has_feature("mobile")`, `TVRZ_MOBIL`), stredni_do_m_mobil | částečně | až po stabilizaci |
| 18 inteligentní scény | `zadani_sceny_2_11.md` + reference 3. 11. | plán, hlídač nezačatý | priorita D, po vydání 0.9996 začato |
| 19 NPC úrovně simulace | lidé a zvířata ve vsi, `zvirata_chuze` | NEOVĚŘENO | priorita E |
| 21–23 testy, regrese | test_smyslu, test_svet (~60 testů), matice vztahů s otiskem, měřicí trasa | **chybí automatická „poslední dobrá verze“** | převzít z Pucharta (`hlidaci_z_pucharta.md` bod 4) |
| 24 kontrola kontrol (záměrné chyby) | nemáme | – | nový krok: izolovaná kopie s vloženými chybami (chybějící kolize, visící díl, špatné souřadnice) musí brána odmítnout |
| 24 „test, který nebyl spuštěn, nesmí být OK“ | `kontrola_vztahu` váže výsledky na otisk (0.9996: „žádný běh k otisku“ → 0 %, vydáno jen jako testovací) | funguje | – |
| 26 důkazy místo prohlášení | zprávy Míše, `predani.md` | částečně | u každé dokončené práce: commit, testy prošly/neprovedeny, rizika, jak vrátit |
| 27 žádná zbytečná složitost | hlídač scén = rozšíření měřicí trasy, ne nový systém | v souladu | – |

Nové úkoly z manuálu (pořadí): 1) souřadnice ze shaderu do dat (ves, nádvoří); 2) kontrola kontrol záměrnými chybami;
3) poslední dobrá verze (s Puchartem); 4) předstih načítání podle rychlosti – jen pokud hlídač scén ukáže doskoky.
