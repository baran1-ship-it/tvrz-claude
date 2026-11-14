# Jak často hry aktualizují NPC (rešerše 14. 11., Míša: „možná toho valíme moc najednou“)

[FAKT] = zveřejněno (zdroj), [ODVOZENO] = návrh pro nás, NEOVĚŘENO na zařízení.

## Zjištění
- **KCD2** [FAKT]: ~2400 NPC, nové LOD techniky simulace AI kvůli času snímku a paměti; behavior trees mají „LOD větev“ se zjednodušenou simulací (GDC 2026, Smrček: https://gdcvault.com/play/1035718/Supporting-Thousands-of-NPCs-in). Konkrétní čísla Warhorse nezveřejnil (údaj „plná simulace do 150 m“ z druhé ruky – NEOVĚŘENO).
- **AC Unity** [FAKT]: plně autonomní NPC do ~12 m, max **40 naráz**; 12–40 m loutky; dál 11 kostí místo 300 (https://game.watch.impress.co.jp/docs/news/20150307_691715.html).
- **Bethesda** [FAKT]: 4 úrovně zpracování AI; High každý snímek, Middle-high ~**18 s**, Low ~**120 s** (Fallout 3, https://geckwiki.com/index.php/GetActorProcessingLevel); Skyrim plné zpracování ~20 postav (komunita).
- **Unreal Animation Budget Allocator** [FAKT, výchozí]: animace **1 ms** na snímek; nejřidší aktualizace každý 10. snímek; mimo obraz jen **4** postavy; nejvýš **4 přepnutí za snímek**; změna úrovně až po **30 snímcích** (hystereze) (https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-budget-allocator-in-unreal-engine).
- **Unreal Mass** [FAKT]: úrovně s frekvencí v sekundách, `spread_first_simulation_update` rozloží první aktualizaci přes periodu.
- **Godot dokumentace** [FAKT]: nepočítat cesty všem agentům v jednom snímku (skupiny / náhodné časovače); nedosažitelný cíl = nejdražší dotaz (https://docs.godotengine.org/en/4.4/tutorials/navigation/navigation_optimizing_performance.html).

## Porovnání s Havranem (stav 14. 11.)
| Oblast | Havran | Doporučení [ODVOZENO] |
|---|---|---|
| plná animace | plne_max 8 nejbližších, do 25 m každý snímek, do 45 m 10 FPS, dál 4 FPS | 8–12 v úrovni A – sedí |
| IK, hlava, sukně | sukně 4, hlava 6 nejbližších (0.999995) | IK/look-at ~4 nejbližší – sedí |
| změna činnosti | nejvýš 4 za snímek (14. 11.) + rozvrh_rozptyl ±15 min v roli | 1–2 nové činnosti za snímek, posun začátku každé postavy podle id (ne jen v roli) |
| cesty | rozpočet 2 ms / 48 sond na snímek, nedosažitelné páry se pamatují | ~1 ms nebo 1–2 dotazy za snímek; cíle jen z ověřených míst |
| mimo obraz | animace a modifikátory stojí, poloha podle rozvrhu | stejně (úroveň C) |
| hystereze úrovní | ne | změna úrovně LOD nejdřív po ~30 snímcích |

Další kroky: posun začátku činnosti podle id postavy (data), zmena_bloku_snimek 4 → 2 změřit, hystereze LOD animace.
