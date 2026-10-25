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

## Další stálá pravidla
- Nejdřív se podívat do světa (KCD2 apod., rešerše), nic nedělat z hlavy.
- Tablet: nikdy MSAA, žádné shadery se screen texture; vždy modely, ne primitiva.
- Podpisový klíč nikdy do repa.
