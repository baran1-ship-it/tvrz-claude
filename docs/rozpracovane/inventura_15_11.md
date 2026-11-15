# Inventura otevřené práce 15. 11. (Míša: „mrkni do složek, kde máš práci do budoucna a plány, co tam chybí dodělat a co odkládáš“)

Nezávislá kontrola (jen čtení, HEAD c906ee3). Dnešní řádky 1–17 `misa_15_11_chyby.md` vynechány. „export“ = potřebuje export světa z Blenderu.
Seznam neuzavřených řádků tabulek: `python3 tools/otevrene_radky.py`.

**Hlavní nález:** brána 1.0 (`tools/kontrola_tabulek.py`) velkou část otevřeného nevidí – `misa_099_chyby.md` a `misa_0992_chyby.md`
nemají sloupec Stav, `misa_28_chyby.md` ř. 49–89 mají stav ve sloupci Kontrola → „ČEKÁ“/„ROZBOR“ řádky bránu nikdy nezastaví.

## (A) Míša chtěla, stále otevřené
1. Záseky – systémová oprava (misa_28 ř. 112, 143, 144, 159; `zaseky_rozbor_system.md` §3): jeden plánovač snímku pro rostliny a kolize, „kupy“ nahrávají celý buffer naráz, konvexní kolize hostince (potvrzená příčina A8). L.
2. Tři úrovně LOD / „bílé kostky z dálky“ (ř. 151, 14. 11.). L, export.
3. Hlídači z Pucharta – všech 11 „čeká“ (`hlidaci_z_pucharta.md`; Míša 3. 11.). M–L.
4. Postavy: anatomie chlapce (ř. 115), zadní noha za botou (ř. 116), světlý pruh pod kápí (ř. 120), poutník bez zápěstí (ř. 130). M, přestavba postav.
5. Krčma/hostinec: hostinský se opírá o vzduch (ř. 128), obsluha přes kuchyň ke všem stolům (ř. 129), přesun postav hostince do krčmy do L (`kovarna_ves.md:31`), hostinský u krbu. M.
6. Plot a byliny bylinkářky (ř. 119/131/156, příčina neznámá). S–M.
7. Purkrabí chodí vodou vedle mostu (ř. 148). S–M.
8. Lavice na nádvoří tvrze a rozmístění míst (ř. 149). S.
9. Deska na mostě (ř. 49/118) – čeká na Míšin snímek s panelem. S.
10. Mapa z Pucharta (ř. 136, „po vydání“). M.
11. Starší rozpracované: ř. 85 (stojí nad postelí), 96 (překryv hostů), 97 (zubatá cesta u hostince), 94 (drn jako plocha), 91 (voda odtoku mlýna), 106/107 (místa vsi, zívání), 90 (textury předmětů), 89 (klenba sklepa). S–M; 91, 97, 89 asi export.
12. Mokro deště jen ve shaderu skal (`dest_z_pucharta.md:27`, Míša 13. 11.). S–M.
13. Ověřit po exportu: ř. 157 dům kováře na potoce (podle `predani.md:1374` přeplánování potoka selhává → posunout stavbu). S.

## (B) Vnitřní plán – kvalita a výkon
1. Rozpory Blender × Godot #8, 11, 13–17, 19–21, 34, 35 (`rozpory_blender_godot.md`). L, export.
2. Brány 1.0 (`plan_1_0.md`): matice vztahů 100 %, `site_natazene` 36 chyb (export), snímky 01–20 proti předlohám; oprava bran tabulek (viz hlavní nález). M.
3. Warhorse W1–W6 „po exportu“ (`plan_1_0.md:34–41`). L.
4. Pevná souřadnice vsi v `shaders/zem.gdshader:55` (`ves = vec2(470,830)`). S.
5. Neověřeno na tabletu: automatická kvalita, neosvícená tráva, GPU tráva A/B, 3D 75 % – Měřicí trasa.
6. Drobnosti: test `breh` 58 z meze 59, záblesk před kamerou na začátku trasy, výška nábytku chýší jen ze středu kusu, misa_0994 ř. 2/10/20/21.
7. Plánování krajiny: toky a cesty spolu, ≤ 3 přechody na tok, hodnoty KCD2 do pravidel dálky. M, export.

## (C) Dlouhodobé / odložené
Dovednosti hráče, tváře a zbroj; rozhovory a hlas, oblečení podle počasí; řemeslné animace; otázky pro Míšu (UAL Pro);
W7 výdrž a pády, W8; zapečené světlo, impostory lesa, atlasy materiálů, `max_lights_per_object`; kůň (`kun_zivy.gd`, výlez z vody).

## Zastaralé (k úklidu / potvrdit)
`docs/radce.md` (poslední 2. 11.), `docs/stav.md` (20.–28. 10.), `PREHLED.md` (10. 11.), `plan_1_0.md` pořadí 1–5, tabulky misa_099/0992,
misa_28 řádky jen „měřicí trasa“ (31, 52, 58, 72, 76, 81), ř. 67/78 krtinec „čeká export“ (export proběhl), ř. 9 dohled z kopce (potvrdit),
ř. 134 ves světlejší = dnešní ř. 10.
