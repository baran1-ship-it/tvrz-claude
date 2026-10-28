# Odkaz Havrana – pravidla pro každou session

Předání a podrobnosti: `docs/predani.md` (přečíst na začátku). Rádce píše do `docs/radce.md` (před čtením `git pull`).
S Míšou česky.

## Nečekat (Míša 25. 10.: „pravidlo navždy, ať nečekáme jak blbci… všude“)
- Nic dlouhého neběží v popředí a nikdy se nečeká se založenýma rukama. Godot (testy, focení, vydání) jen přes
  `tools/beh.sh … ` na pozadí (`run_in_background`), na výsledek upozorní oznámení – žádný `sleep`, žádné dotazování.
- Během běhu se dělá další práce: další úprava, poznámka rádci, příprava vydání, commit. Co na výsledku nezávisí, nečeká.
- Nezávislé věci najednou (paralelní volání nástrojů, víc úprav v jednom kroku).
- Testovat jen lehce (snímek opraveného místa + test, který se ho týká); celou sadu ne, zbytek dělá Míša na tabletu.
- Když něco spadne: příčinu opravit hned a zapsat do `docs/predani.md`, ať se neopakuje – ne jen pustit znovu.
- Míše psát krátce, co se děje, a nečekat na potvrzení u věcí, které už zadala.
- Míša 28. 10.: když něco běží, hned dělat další bod plánu (seznam v odpovědi „co ještě dle plánu“, tabulka
  `docs/rozpracovane/misa_28_chyby.md`, úkoly) – nikdy nekončit tah jen „čekám na výsledek“, dokud je v plánu práce.

## Další stálá pravidla
- **Záplatování zakázáno** (Míša 27. 10.; rádce 09:55 PRAVIDLA ZASAZENÍ): každý díl (cesta, budova, voda, skála) je
  záznam v datech; stavba v pevném pořadí terén → cesty → budovy → voda → vegetace → předměty, pozdější krok nehýbe
  dřívějším; odstupy jen z `pravidla/pravidla_sveta.json` `pasma`, v kódu žádná vlastní čísla; test `zasazeni` musí
  projít před vydáním. Chyba = oprav záznam nebo pravidlo a postav znovu, ne další výjimka.
- **Test smyslu před exportem** (rádce 27. 10. 20:50, Míša „už nechci vidět cestu pod mostem, levitující trávu…“):
  `/opt/bl/bin/python tools/test_smyslu.py` musí projít, jinak se export nespouští. Povrch a rostliny podle užívání
  a stanoviště (`pravidla/svet/druhy.json`), nic živého ve vodě, stavby ne ve vodě/na cestě/svahu, cesta přes vodu jen
  s přechodem. Každá nová chyba, kterou najde člověk = nová kontrola v testu, ne jen oprava.
- **Hlídači a mapa stavby** (Míša 28. 10.): postup v `docs/pipeline.md` „Hlídači a mapa stavby“ – každá změna světa projde
  vrstvami 0–7, před snímky se prohlédne `build/mapa_stavby.png`, chyba od člověka = řádek tabulky s kontrolou v testu.
- **Godot soubory, snímky, čísla** (28. 10., radce.md 19:55): ruční úpravy .tscn/.tres/.uid jen podle pravidel tam (žádné vymyšlené uid://, po úpravě `--import`); po změně scény snímek `--write-movie` a **podívat se na něj sám, než se pošle**; nezměřené číslo = NEOVĚŘENO, nikdy odhad.
- Nejdřív se podívat do světa (KCD2 apod., rešerše), nic nedělat z hlavy.
- **Než se něco vytvoří, hledat hotové** (Míša 28. 10.): Míšin Disk (složka Modely), Poly Haven, ambientCG, Quaternius, Kenney,
  Sketchfab (CC0/CC-BY, autor do titulků), Godot Asset Library, hotové postupy her (KCD2 modding dokumentace Warhorse) –
  vlastní model, textura nebo systém až když nic nesedí (zapsat, kde se hledalo). Kopírovat z her nesmíme, inspiraci ano.
- Tablet: nikdy MSAA, žádné shadery se screen texture; vždy modely, ne primitiva.
- Podpisový klíč nikdy do repa.
