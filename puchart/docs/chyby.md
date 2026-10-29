# Tabulka chyb (formát Havrana: každá chyba od člověka = kontrola v testu, jinak se nevydává)

| # | chyba | kde (x, z) | příčina | pravidlo / data | kontrola | stav |
|---|---|---|---|---|---|---|
| 1 | Pás 100–300 m žlutý se světlými pruhy (snímek 01) | (−60, −150) → ostroh | opad listí (maska G) bez stromů je z dálky žlutý; ne komprese (ověřeno bezeztrátově), ne lesk (ověřeno SPECULAR 0,08) | les z dálky = barva korun (KCD/Havran) → krok C stromy; do té doby dálková barva lesa dřív | snimek 01_louka_k_hradu | otevřeno |
| 2 | Světlé čáry na vzdálených svazích | levý svah snímku 01 | škvíra mezi LOD dlaždic větší než sukně 3 m | `teren.json` sukne_m + 1,5 × krok | snimek 01_louka_k_hradu | zmírněno, ověřit |
| 3 | Osy toků z OSM leží ~15 m vedle dna, 1,2 m nad ním | celý výsek | OSM kreslené z mapy | osy z terénu (D8), OSM jen jméno – `toky.py` | (doplnit: test voda_v_korytu) | v datech |
