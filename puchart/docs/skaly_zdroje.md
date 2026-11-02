# Skály Puchartu – zdroje a postup (2. 11. 2026)

Fotky a data: přehled `scratchpad/skaly_puchart_skutecne.jpg` (poslaný Míše), ZABAGED `docs/screens/zabaged_skaly.png`.
- vyraznavylet.cz (Patrik, únor 2021): skála u cesty na hřbetu 3–5 m, stupně na J boku, příkop před zadním hradem,
  zdivo na deskovité skále. GC80T08: skála pod čelem zadního hradu 5–8 m s mechem. hrady.cz 25698: plán a řez – řada
  ~8 skalek po hřebeni. ČÚZK ZABAGED vrstva 130: skalní útvar = ostroh pod zadním hradem. ČGS GEOČR50: droby (šedá,
  modrošedá) a břidlice, lavicovitá/deskovitá, úklon 20–25° k S–SV. Fotky skalního města (Míša): šedé hranaté bloky,
  pukliny, mech na plochách.
- DMR 5G má u hradů 0,07 bodu/m² – kolmé stěny 2–6 m v něm nejsou. Hustší otevřená data ČÚZK nejsou (DMP OK = koruny).

## Postup (3. pokus, schválený princip)
1. Kvádry ze skenů / z bloků zamítnuty (vypadaly jako beton položený na kopci).
2. Skála = terén sám v místech skal: výška DMR se rozláme na stupně podle ukloněných vrstev (svislá stěna + police),
   Voronoi bloky ~1,6 m s vlastním posunem a fází vrstev, pukliny jako zářezy, okraj zóny se noří pod terén.
3. Zóny: boky hřebene (s mezerami a různou výškou výchozů), boky průrvy, obrys ZABAGED, podloží pod hradbami zadního
   hradu (skála až pod patu zdi), nízké výchozy na V straně předního hradu. U mostu nižší.
4. DMR beze změny, hrady na místě; test průchodu 9 tras OK; kolize = hrubá síť skály.
Data `pravidla/svet/skaly.json`, stavba `blender/skaly.py`, podklad terénu `nastroje/skaly_podklad.py`.
