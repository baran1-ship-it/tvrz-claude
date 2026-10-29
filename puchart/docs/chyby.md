# Tabulka chyb (formát Havrana: každá chyba od člověka = kontrola v testu, jinak se nevydává)

| # | chyba | kde (x, z) | příčina | pravidlo / data | kontrola | stav |
|---|---|---|---|---|---|---|
| 1 | Pás 100–300 m žlutý se světlými pruhy (snímek 01) | (−60, −150) → ostroh | opad listí (maska G) bez stromů je z dálky žlutý; ne komprese (ověřeno bezeztrátově), ne lesk (ověřeno SPECULAR 0,08) | les z dálky = barva korun (KCD/Havran) → krok C stromy; do té doby dálková barva lesa dřív | snimek 01_louka_k_hradu | otevřeno |
| 2 | Světlé čáry na vzdálených svazích | levý svah snímku 01 | škvíra mezi LOD dlaždic větší než sukně 3 m | `teren.json` sukne_m + 1,5 × krok | snimek 01_louka_k_hradu | zmírněno, ověřit |
| 3 | Osy toků z OSM leží ~15 m vedle dna, 1,2 m nad ním | celý výsek | OSM kreslené z mapy | osy z terénu (D8), OSM jen jméno – `toky.py` | (doplnit: test voda_v_korytu) | v datech |
| 4 | Les 3,43 M troj., VRAM 1430 MB (snímek z lesa, PC) | (−60, −150) | plné modely do 44 m; textury stromů z glb nekomprimované; LOD1 si nesl kopie textur | `stromy_modely.json` lod0_m 22 / blizko_m 40; textury VRAM + max 1024; LOD1 vlastní (30 % karet) bez textur | snimek 03_les_bucina (panel: 1,83 M, VRAM 315 MB) | zmírněno – 1,83 M je stále nad cílem 1,5 M |
| 5 | Start hráče stojí v lese, ne na louce | (−60, −150) | plošina S od hradu je dnes i podle PPV les | start přesunout na předpolí hradu (hlavni.gd) – vyřeší se s cestami | snimek 03_les_bucina | otevřeno |
| 6 | Louka u hradu přesvícená do žluta, tráva řídká, nároží věží jako cihly | val S (2, −62) | leafy_grass bez kalibrace odrazivosti; 2,6 trsu/m²; nároží ze stacked_stone_wall (rezavý) | `zem.gdshader` kalibrace_travy; `byliny.json` 5/m²; nároží z castle_wall_slates | snimek hrad_1_most_val | v datech |
