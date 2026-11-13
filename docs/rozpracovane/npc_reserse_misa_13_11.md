# Rešerše NPC, animace, boj (Míša, dokument 12. 11. 2026) – porovnání se stavem hry

Zdroj: `Havran_technologicka_reserse_NPC_animace_boj.docx` (Míša 13. 11.). Projekty v něm **nejsou ověřené** (licence,
verze, výkon na Xiaomi Pad 8) – před převzetím kódu ověřit v repozitáři.

| Bod rešerše | Stav ve hře | Co chybí / další krok |
|---|---|---|
| Úrovně simulace podle vzdálenosti | **Je**: `lide.gd` LOD AI (mimo dosah se nepočítá, při změně bloku skok na místo), LOD animací (dál po krocích, mimo záběr bez animace), `daleko_cekani_nasobek` | datová simulace zdrojů/výsledků práce mimo dohled (zásoby, výroba) – zatím ne |
| Denní režim, místa, činnosti | **Je**: rozvrh po hodinách, AStar po cestách, činnosti s významem klipů, společné scény (`postavy.json`, test `lide_chovani`) | přerušení práce a změna plánu (Utility AI/GOAP) – ne |
| Pracovní animace s kontaktem na předmět (kladivo–kovadlina, sekera–strom) | **Částečně**: úchop rukou (`uchop.gd`, test_drzeni 0/300), zapuštění hrotu/ostří do země (`hrot`, `zapust_m`) | časované **kontaktní události** v klipu (okamžik úderu) navázané na bod předmětu ve světě (kovadlina, špalek, strom) + test „nástroj se trefí“ – **další krok** (bod 2 pořadí rešerše) |
| Oblečení, tváře, sukně | **Je** (12. 11.): vrstvy, sukně s kolizí nohou, tváře podle věku a role | stehno při chůzi u kabátce mužů |
| Paměť a vztahy (původ, čas, svědek, jistota) | ne | samostatný modul dat, šíření jen rozhovorem |
| Dialogy (Yarn Spinner / Patter) | ne | vybrat runtime až s paměťí (Yarn Spinner má Godot 4 podporu – ověřit C#/GDScript, Android) |
| Vyšetřování | ne | po dialozích |
| Boj (MS I.33 meč a puklíř ~1320–30 – nejbližší době 1393) | ne | po pracovních animacích; ragdoll jen u důležitých událostí |
| Benchmark 10/20/50/100 NPC, 1v1/1v3, 15 min | **částečně**: Měřicí trasa (`mereni_trasa.json`) | přidat variantu s počtem NPC – NEOVĚŘENO NA ZAŘÍZENÍ |

Doporučené pořadí v dokumentu (1 rig a lokomoce → kontakt nástrojů → kovář a dřevorubec s režimem → GOAP/Utility →
paměť → dialogy → boj → benchmark) sedí na náš stav: body 1 a 3 máme, **teď bod 2 (kontakt nástrojů)**, pak 4.

Kandidáti k testu (z dokumentu): GOAP pro Godot (asset 4888), LimboAI (BT + FSM, MIT – v Godot 4.4 jako GDExtension,
ověřit Android build), Godot Simulation Plugins. Nic se neinstaluje bez izolovaného pokusu a měření na tabletu.
