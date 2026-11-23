# Oděvy jako 3D modely na postavě (Míša 23. 11.: „oblečení musíš dělat jako 3D model na skutečný model postavy“)

## Proč
Dosavadní oděvy NPC (`tools/postavy_q/clothes.py shell`) = kopie ploch těla posunutá po normále → tvar těla, trhá se,
prorůstá (kukla/šátek 3 neúspěšné pokusy). Quaternius Peasant (repo, CC0, stejná kostra) je fantasy (korzet, kalhoty
u ženy, přezky) → jako dobové oblečení nevyhovuje; jen případně nohavice muže.

## Rešerše postupu (23. 11.)
- Šití ze střihových dílů v Blenderu (cloth + sewing springs), jako Marvelous Designer:
  - [A Tailor's Approach to Cloth Sewing in Blender](https://blenderartists.org/t/a-tailors-approach-to-cloth-sewing-in-blender/1396059):
    díly podle skutečných měr těla 1:1 (košile ~10k ploch), předvolba Cotton (kalhoty Denim), kolize objekt 5 mm,
    vlastní kolize 2 mm, Speed Multiplier 0,5, Max Sewing Force 20; po simulaci použít modifikátor a sloučit šicí vrcholy.
  - [Roger: Sewing Clothes (archiv wiki)](https://archive.blender.org/wiki/2015/index.php/User:Roger/Sewing_Clothes):
    tělo = kolizní objekt s odstupem ~1 cm, horní okraj (pas/ramena) připnout skupinou vrcholů (pin), díly předtvarovat
    kolem těla (proporční úprava), zkontrolovat, že tělo nikde neprosvítá.
  - [Sewing Clothes in Blender (2.70)](https://blenderartists.org/t/sewing-clothes-in-blender-available-in-2-70/544167):
    šicí hrany = hrany mezi vrcholy dílů, při šití vypnout gravitaci, simulovat do sešití, pak použít a sloučit.
- Rig: váhy kostí z těla přenosem (Data Transfer, nejbližší plocha, interpolace), pak test v pózách
  ([Roblox armature setup](https://create.roblox.com/docs/art/accessories/creating/armature-setup)).

## Stav prototypu (`/tmp/claude-0/odev/sit.py`, kotle muže)
- v1/v2 díly rovné daleko od těla → spadly. v3 díly obtočené kolem těla → tunika drží, hranatá.
- v4 měkčí látka → sklouzla. v5/v6 připnutá ramena → drží, ale stahuje se k tělu a lem jde šikmo nahoru.
- Další krok: hodnoty z rešerše (Cotton, kolize 5/2 mm s vlastní kolizí, speed 0,5, sewing 20, gravitace až po sešití),
  díly podle měr těla s volností; pak váhy, skrytí těla pod oděvem, export do sady, test švů v pózách.

## ODLOŽENO 23. 11. (Míša: „pokud ti nejde modelování oblečení, kašli na to, ať nepálíš tokeny“)
- Simulace látky (v1–v8) nevyšla (padá / lepí se na tělo). Model z obtočených dílů bez simulace (v9–v12,
  `tools/postavy_q/prototyp/kotle_model.py`, snímky poslané Míše) dává uzavřenou tuniku se sklady, ale do hry chybí:
  váhy kostí z těla, skrytí těla, export do sad, test v pózách, další kusy (cotte, kápě, šátek, zástěra) – velká práce.
- Ve hře zůstávají sady přestavěné 23. 11. (B5: 15 sad bez děr na hrudníku, kukle v kleku/sedu dál prorůstá).
