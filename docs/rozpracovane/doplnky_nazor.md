# Doplňky – rešerše Pucharta (13. 11., puchart/docs/reference/doplnky/README.md) a co z toho pro Havrana

Pozor: test běžel v Godotu 4.7.2, Havran je 4.4.1 – co „funguje“, je u nás NEOVERENO, dokud se nezkusí v 4.4.1.

- Dialogue Manager 3: ano (už dřív vybrán, rešerše 13. 11. npc_reserse). U nás řada 3.x pro Godot 4.4, ne main 4.2.0
  (ten cílí na novější Godot) – ověřit v 4.4.1. Krok: prototyp rozhovoru s mlynářem.
- Beehave: zatím NE. Chování vesničanů máme datové (rozvrh, činnosti, podmínky, místa jako smart objekty v
  pravidla/svet/postavy.json) – to je postup KCD (denní rozvrhy). Beehave by znamenal přepis lide.gd bez nového přínosu.
  Smysl až pro boj a stráže (reakce na hráče) – tam znovu zvážit.
- Godot State Charts: ne (denní režim řeší rozvrh).
- MPFB + Moveset: ne. 27–37 tis. troj. na postavu (limit 14 tis.), licence oblečení MPFB neověřená; máme Quaternius
  + zapečenou látku (tools/zena30) + nové tváře (tools/tvare). Moveset jen kdyby chyběl konkrétní klip (CC BY → titulky).
- Rigify: ne (706 kostí).
- Phantom Camera: později pro průlety a scény.
- IvyGen: zvážit pro zarostlé zdi tvrze – jen po převodu na karty (8 m = 4,4 mil. troj.).
- Sapling: jen pro druh, který nemáme (strom přes náš filtr LOD/impostor).
- Godriver: zvážit pro hlídače v běžící hře (máme vlastní test_svet; přínos = vstupy a snímky z APK).
- Souhlas s „nebrat“: Sky3D, ProtonScatter, Spatial Gardener, Simple Grass Textured, Octahedral Impostor, Terrain3D,
  Waterways, Swell, Dialogic, A.N.T.
