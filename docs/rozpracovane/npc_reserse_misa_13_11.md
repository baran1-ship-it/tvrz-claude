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

---

# Druhá rešerše: příběh, interakce, dialogy (Míša 13. 11.) – jen co se nám hodí

Filtr: Godot **4.4.1**, jen **GDScript** (žádné C#/.NET – Android export C# chce .NET 9 a je experimentální), Android
tablet, data v `pravidla/` (záplatování zakázáno – pravda světa ve vlastních datech, ne v addonu).

**Bereme:**
- **Tři vrstvy příběhu**: pevný autorský hlavní děj (1393) + systémový příběh z simulace (rozvrh, práce, vztahy už máme) +
  příběh hráče (komu věří, koho obviní).
- **Paměť NPC: fakta nejsou přesvědčení** – záznam: obsah, zdroj (viděl / slyšel od koho / domněnka / listina), čas a místo,
  jistota, ověřeno, komu předal. Svět zná pravdu, NPC jen to, co vidělo nebo slyšelo; šíření jen rozhovorem
  (máme společné scény hovoru u studny – přirozené místo předání).
- **Témata podle znalosti**: NPC nabízí jen to, co zná (kovář ví, kdo si objednal opravu meče, ne tajemství dvora).
- **Datové záznamy** (jako tabulky v `pravidla/svet/`): profil (už `postavy.json` obyvatele), stav (už rozvrh/činnost),
  paměť, vztah (důvěra, strach, dluh…), událost světa (čas, místo, účastníci, stopy), téma rozhovoru, stav úkolu.
- **Interakce**: NPC může být zaneprázdněné/ve spěchu/ve společnosti → hráč počká nebo přeruší práci; odmítnutí jasně
  rozlišit (nemá čas / bojí se / neví).
- **Mobilní UI**: rozhovor nezakryje scénu, přeskočení textu, historie, málo voleb najednou, dotyk i ovladač stejný systém
  (navázat na `docs/ovladani.md`).
- **Vyšetřování**: stopy s místem, časem, svědky a životností; chybné obvinění je povolené a má následky (inspirace
  Pentiment, Obra Dinn – jen postupy, nic nekopírovat).
- **První prototyp přesně podle rešerše**: mlynář (Bartoš, už má práci a rozvrh), mlynářova žena, jeden svědek, tři stopy;
  pozdravit / ptát se / ukázat důkaz / obvinit / odejít; po návratu reagují podle toho, co se mezitím dozvěděli; test
  uložení a načtení znalostí.

**Nástroj na dialogy:**
- **Dialogue Manager 3.x** (Nathan Hoad, MIT, GDScript; od v3.4 vyžaduje Godot 4.4, poslední 3.10.4 v Asset Library) –
  **jediný kandidát, který sedí na naši verzi Godotu bez C#**. Stateless – stav světa zůstává v našich datech, což chceme.
  Ověřit: Android export, výkon, ukládání (NEOVĚŘENO).
- Nebereme teď: Yarn Spinner (Godot verze v C#; čistě GDScriptový port byl v lednu 2026 ve fázi revize – sledovat),
  Dialogue Manager 4 (podle dokumentace Godot 4.6+), Dialogic 2 (alfa), Dialogue & Quest System (Godot 4.7.2, unstable),
  BLUE (4.7.1, licenční omezení), gd_dialog a Ink (zbytečné, když sedí DM3).

**Z první rešerše (NPC/animace/boj) bereme:** kontaktní body a časované události v pracovních klipech (další krok),
přerušení práce a změna plánu, později paměť/vztahy (viz výše), boj až nakonec (MS I.33 jako dobově nejbližší pramen),
benchmark s počtem NPC na tabletu. Pluginy (GOAP, LimboAI, Simulation Plugins, FullSwordDemo) zatím ne – máme vlastní
rozvrh a činnosti v datech; každý jen jako izolovaný pokus s měřením.

Zdroje ověření: [Dialogue Manager – Asset Library](https://godotengine.org/asset-library/asset/edit/22113),
[DM v3.5 devlog](https://nathanhoad.itch.io/godot-dialogue-manager/devlog/907148/godot-dialogue-manager-v35),
[Yarn Spinner leden 2026](https://www.yarnspinner.dev/blog/monthly_jan_26/),
[Godot C# – Android](https://docs.godotengine.org/en/4.4/tutorials/scripting/c_sharp/c_sharp_basics.html).
