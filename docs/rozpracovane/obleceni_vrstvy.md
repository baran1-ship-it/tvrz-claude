# Oblečení po vrstvách jako v KCD (Míša 11. 11.)

> „Nešlo by udělat jen oblečení a podle potřeby model obléknout? Jako v KCD. Muž bez oblečení je jen v bruchách, žena
> bez oblečení jen ve spodničce; ženy mají výstřih, někdy holé ruce, muži mají holé ruce podle potřeby.“

## Proč
Dnes je každá postava jeden slitý model (tělo + šaty, `tools/postavy_q/sestav.sh`), šaty mají váhy přenesené z těla:
sukně a zástěra dole až 80 % na stehnech → trčí s nohou dopředu/dozadu, nesplývá při ohybu ani sedu (Míša 11. 11.).

## Jak (KCD: tělo + sloty oblečení na jedné kostře)
1. **Základ**: muž = tělo v bruchách (plátěné spodky), žena = tělo ve spodní košilce. Zakryté části těla se pod oblečením
   nekreslí (maska) – nic neprokoukne.
2. **Sloty** (vrstvy odspodu): košile (dlouhý / krátký rukáv / bez rukávů – holé paže), nohavice, sukně/kotle, kabátec,
   zástěra, opasek, šátek/čepec, kápě, plášť, boty. Ženy: výstřih podle šatů (hluboký/kulatý/šněrovaný), u práce holé paže.
   Muži: holé paže podle práce (kovář u výhně, lamač, sedlák v létě).
3. **Data**: `pravidla/svet/postavy_vzhled.json` – každá postava = výčet kusů a barev, např.
   `"selka_2": {"telo": "zena", "kusy": [["kosilka", "len"], ["sukne_dlouha", "hneda"], ["zastera", "bila"], ["satek", "modra"]]}`.
   Nový vzhled = data, ne přestavba modelu; později oblékání hráče.
4. **Splývání**: sukně, zástěra, plášť mají pomocné kosti (2–3 řady) s pružinou (SkeletonModifier3D, KCD/„swing bones“)
   – látka visí a dobíhá, nekopíruje stehno 1:1. Váhy dlouhých kusů hlavně na pánev.
5. **Výkon tabletu**: kusy se při vzniku postavy slijí do jedné sítě (jedno kreslení na postavu jako dnes).

## Postup
1. Hotové kusy: Quaternius (modulární postavy s oblečením, CC0, kostra UAL), Sketchfab CC0/CC-BY, Míšův Disk (Modely);
   vlastní jen dobové kusy, které nikde nejsou (zástěra, šátek, kápě) – zapsat, kde se hledalo.
2. Vzorek: selka (košilka + sukně + zástěra + šátek) → snímky chůze, sedu, kleku u záhonu → Míša.
3. Pak všichni podle `choreografie_postav.md` (role → oblečení podle práce a stavu).
