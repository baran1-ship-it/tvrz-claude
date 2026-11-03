# Hlídači převzaté z Pucharta (Míša 3. 11.: „má Puchart lepší hlídače a smysly? pak si je taky vem“)
Porovnání 3. 11. (nezávislý subagent, jen čtení `origin/ccr-f2d32673-9fi7m5:puchart/`). Havran je silnější v matici
vztahů, otisku, formátu povolení (`vztahy.json povoleni` s duvod/schvalil/plati_do), test_uv, zamek_terenu, koryto/brod/
stanoviste/uzivani, dil_okraj. Puchart je lepší / Havran nemá – pořadí převzetí podle přínosu:

| # | z Pucharta | co u nás chytí | kam | stav |
|---|---|---|---|---|
| 1 | `blender/kontrola_geometrie.py` – opora kusů modelu (souvislé kusy, opora terénem/jiným kusem, šíření od země; visí ≥ 0,25 m; celý kus > 0,3 m pod terénem) | střechy, trámy, kvádry, lavice, díly mostů ve vzduchu (tvrz, ves, mlýn), studna lano–ucho; dnes `_visici` jen rostliny | krok exportu nad .glb, `test_smyslu --po` | čeká |
| 2 | rohatka schválených nálezů (shoda 1,5 m; nový nález = chyba) – ve formátu našeho `povoleni` | zavést přísné hlídače bez zablokování vydání a bez výjimek v kódu | `vztahy.json povoleni` | čeká |
| 3 | `test_pruchod.gd _test_povrch` – viditelné × kolize po trasách (boří se / stojí nad / projde viditelným / neviditelná stěna) | propady, trám ve dveřích, schody s kolizí jinde | `test_svet.gd` | čeká |
| 4 | `posledni_dobra.py` + `dobra_verze.json` | regrese: co bylo OK v dobré verzi a teď ne + git diff (CLAUDE.md Regrese) | `vydani.py` | čeká |
| 5 | `kontrola_tabulek.py`: test ve sloupci existuje a v tomto běhu prošel | „opraveno“ s neexistujícím/padajícím testem | `tools/kontrola_tabulek.py` | čeká |
| 6 | `kontrola_scen.py`: doskok (změna obrazu proti mediánu), rozpočet typu scény, +15 % troj. proti schválenému | doskakování, vyskakující domy a tráva | hlídač scén (zadani_sceny_2_11.md) | čeká |
| 7 | `strom_na_zemi`: pata proti nejnižšímu z 8 bodů obvodu kořenů | mezera pod kmenem na svahu | test_smyslu --po | čeká |
| 8 | `teren_shoda`: viditelný LOD0 × kolize ve středech a hranách trojúhelníků | boření a schody mezi sítěmi Teren* | test_smyslu --po | čeká |
| 9 | pre-commit hook s rychlými hlídači (test_smyslu, kontrola_vztahu) | rozbitá data už při commitu | `tools/hooks/` | čeká |
| 10 | assert prorůstání ve staviteli | díl skrz podlahu/strop | `fort.py`, `palace.py` | čeká |
| 11 | drobné: hladina_nestoupa, lod_navaznost, počet tras ≥ min, „test neprošel naprázdno“ | | test_smyslu / test_svet | čeká |
