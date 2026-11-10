# Živé postavy jako v KCD – zásady (Míša 10. 11.: „chci ty postavy živé, hodně animace a života, nastuduj si KCD“)

## Co je o KCD veřejně doložené
- KCD2: ~2 400 trvalých postav, každá „má vlastní cesty a život, který vede, ať s ní hráč mluví, nebo ne“ – denní rozvrhy
  běží pořád (GDC 2025/26 Petr Smrček „Supporting Thousands of NPCs in KCD & KCD2“; GDC Festival „NPC Daycycles“).
- Témata Smrčkovy přednášky na MFF 2018 (KCD1): stromy chování, smart objects (místa nabízející činnost), plánování
  rozvrhu, navmesh, vyhýbání ORCA. Podrobnosti přednášky veřejně nečteny (PDF přesměrováno, GDC Vault za přihlášením).
- Modding KCD: rozvrhy postav se dají upravit a questy na nich závisí (Nexus, úprava rozvrhu zbrojíře).

## Co z toho děláme (odvození, ne převzatý kód)
1. **Místa činností (smart objects)** – každé místo v datech nabízí činnost: lavice/stůl (sed, jíst, pít, vykládat),
   pult (obsluha), krb/ohniště (vařit, ohřát se), stěna/trám (opřít se, pozorovat), kovadlina, lom (kutat), záhon.
   Místo má: animaci vstupu, smyčku (víc variant), výstupu; rezervaci (obsadí ho jedna postava); směr (záda ke zdi).
2. **Denní rozvrh v blocích** (ráno, dopoledne, poledne, odpoledne, večer, noc) – v každém bloku seznam činností s váhami;
   postava si vybírá náhodně podle váhy a podmínek (hosté v hostinci → obsluha bez přestávky; poledne → jídlo pracujících).
3. **Pestrost uvnitř činnosti** – smyčka se střídá s krátkými mikro-animacemi: přešlápnutí, rozhlédnutí, gesto, napití,
   protažení; občas pohled po okolí nebo po hráči (jen sem tam, Míša). Nikdo nemá celý den jednu činnost.
4. **Postavy spolu** – dvě postavy u sebe občas hovoří (Talking, gesta), hosté vykládají a pijí, kameníci obědvají spolu.
5. **Pohyb mezi místy** – přirozená chůze (Mixamo), dveře otevře a zavře, s předmětem v ruce (korbel, mísa, vědro).
6. **Reakce na hráče** – podívá se, když jde hráč blízko; nepřekáží mu.
7. **Levně pro tablet** – plná logika a animace jen blízko hráče; dál jen poloha podle rozvrhu (bez animace), mimo dohled
   skok do správné činnosti podle času.

Zdroje: GDC schedule „Supporting Thousands of NPCs…“, gamedev.net 5526, nexusmods kcd mods/726 (rozvrh), MFF 2018 (téma).
