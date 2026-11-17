# Mapa KCD 1 a 2 – znaky bodů zájmu (rešerše 17. 11.)

Míša 17. 11.: „mrkni, jak vypadá mapa KCD a naše, chci zájmové body mít taky pod nějakým pěkným malým znakem, ale jen
v pískovišti a potom v příběhu, když to objevím“. Pořadí podle pravidla: Havran → KCD → internet. Z her se nic nekopíruje,
jen styl a chování.

## 1. Havran (větev claude/new-session-0dtk58)
- `scripts/mapa.gd`: pergamenová mapa (tools/gen_mapa.py), erby míst pro rychlé cestování, **objevování**: ruiny
  (`"ruina": true`) jsou v příběhu na mapě až po objevení – kontrola jednou za sekundu i při zavřené mapě, okruh
  `OBJEV_R = 40 m`, oznámení `hud.toast("Objeveno místo: …", 3.0)` jen mimo pískoviště; v pískovišti vše hned.
- `scripts/main.gd`: `objevena: Array` v uložené hře (`"objevena": objevena` v save, `objevena = Array(j.get(...))` při
  nahrání). → Puchart to přebírá beze změny principu (mapa.gd `objevena`, prochazka.gd `_uloz` / `_nahraj`).
- Fotky mapy KCD v Havranovi ani zde nejsou (docs/screens/kcd1, ref_kcd2_*, docs/reference/kcd_vzhled = jen svět).

## 2. KCD 1 a 2 (internet; vlastní snímek mapy KCD nemáme – NEOVERENO proti obrázku)
- Mapa je **zakrytá (mlha) a místa se objevují chůzí**: „Initially, the entire map is covered in fog of war… you have to
  discover all locations yourself“ – GamePressure, KCD1 průvodce
  https://www.gamepressure.com/kingdom-come-deliverance/world-exploration-npcs/z7a886
- Body zájmu se ukážou **až po objevení**: „The map shows you all important points of interest, at least once you have
  discovered them in the game world“ (KCD2, souhrn hledání – Windows Central / MeinMMO interaktivní mapa
  https://mein-mmo.de/en/kingdom-come-deliverance-2-map-interactive-map-with-all-important-locations,1220872).
- Objevení = **krátká zpráva a ikona na mapě**: „you get a message and a fast travel icon will appear on your map“
  (KCD2 Kuttenberg, GamePressure https://www.gamepressure.com/kingdom-come-deliverance-2/kuttenberg-map/z711795).
  Kapličky a kříže se počítají za objevené, až když k nim hráč dojde blízko (GamePressure interaktivní mapa KCD1
  https://www.gamepressure.com/kingdom-come-deliverance/interactive-map/zc11a4e).
- Rychlé cestování = **erb/štít** (KCD2 modrý štít) – u nás erby míst (mapa_body.json mista), odděleně od znaků.
- Druhy bodů na mapě KCD2 (kategorie, ne obrázky; mapmaster.io
  https://mapmaster.io/games/kingdom-come-deliverance-2/maps/trosky-region): lůžko, tábor, jeskyně, město, kaplička
  (Shrine), místo (Site), kovář, zbrojíř, kožešník, bylinkář, kupec, lázeň, mlýn/řemeslníci, úl (Beehive), lovná místa,
  hrob; KCD1 navíc smírčí kříže a boží muka (guides4gamers https://guides4gamers.com/kingdom-come-deliverance/pois/conciliation-crosses/).
- Vzhled ikon (z paměti hráčů a obecných popisů, **NEOVERENO** obrázkem): drobné jednobarevné kresby v barvě inkoustu
  na pergamenu, jednotný tah, výjimečně červený akcent; popisky bodů zájmu nejsou stále – název se ukáže u kurzoru.

## 3. Co z toho Puchart bere (pravidla/svet/mapa_body.json zajimava)
| KCD / Havran | Puchart |
|---|---|
| malé kreslené piktogramy inkoustem, červený akcent | `znak_sada` – 15 znaků z `nastroje/mapa_znaky.py` (tah pera s chvěním, šrafy), inkoust = barva mapy, červená = pečeť |
| body zájmu až po objevení, pískoviště vše | `objev.okruh_m` 35 m (mlýn 45, lom a milíř 40, štola a brtě 30) – Havran 40 m |
| zpráva při objevení | toast „Objeveno: Mlýn na Veličce“ 3 s, jen v příběhu |
| stav v uložené hře | `objevena` v `user://ulozeni/hra_*.json` |
| název u kurzoru, ne stále | `popisek.kdy = vyber`: název po klepnutí na znak nebo pod kurzorem |
| štít rychlého cestování | erby míst beze změny |

Znaky (vlastní kresba): dřevěný kříž se stříškou, kamenný smírčí kříž, boží muka, milíř, smolárna, brť, studánka, lom,
štola (kladívko a želízko – hornický symbol doložený od 15. st., https://de.wikipedia.org/wiki/Schl%C3%A4gel_und_Eisen),
mlýn (vodní kolo), do zásoby ves, hrad, krčma (džbán), kovárna (kovadlina), hájovna (smrk a srub).
Snímky: `docs/screens/mapa_znaky_17_11_*.png`, náhled sady `docs/screens/mapa_znaky_17_11_sada.png`.
