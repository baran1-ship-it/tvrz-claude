# Postřehy z Puchartu pro Havrana (9. 11.)

Zjištěno při práci na Puchartu 9. 11. Každý bod má příčinu a co s ním dělat.

## Textury a výkon
1. **Mipmapy a VRAM komprese textur načítaných skriptem.** Textury, které hra načte jen přes `load()` ve skriptu
   (materiály skládané v kódu), Godot nepozná jako 3D. Importuje je jako 2D: bez mipmap a bezztrátově.
   Následky jsou blikání a „zrnění“ v dálce, paměť a šířka pásma na Adreno. Wildhearth (Reddit) na tom ztratil 7 FPS.
   - Pojistka: `[importer_defaults] texture = {compress/mode: 2, mipmaps/generate: true}` v project.godot (Havran má).
   - Kontrola u existujících: `.import` s `mipmaps/generate=false` nebo `compress/mode=0` mimo datové masky.
   - Puchart má na to test smyslu `textury_3d_mipmapy` (nastroje/test_smyslu.py). **Doporučuji stejný hlídač i v Havranovi.**
2. **Datové masky** (flow, distance, stanoviště, cesty) bezztrátově a bez mipmap. Havran `tools/datove_textury.txt` –
   v Puchartu převzato.
3. **Hash v shaderech bez `sin()`.** `fract(sin(dot(p, …)) * 43758.5)` na Adreno (mediump) se rozpadne na čtverce po
   metru („minecraft“ na zdech a skalách). Pomohl hash bez sinu (Dave Hoskins) se vstupem `mod(p, 1024)`.
4. **Projekce textury podle normály buňky.** Tečna počítaná z normály reliéfu se natáčí o 1–2° po každé buňce sítě
   a na stovkách metrů od počátku to posune UV o metry. Výsledek: každá buňka jiný výřez textury, čtverce.
   Řešení: pevné osy (X nebo Z podle převažující složky normály, hranici rozmazat šumem).
5. **Odstíny po malých plochách** (skála: 4 materiály po čtvercích 0,4 m) dělají pixely. Stačí jeden materiál
   a odstín z textury, hladké normály (svařit vrcholy) a světový triplanar.
6. **LOD:** `mesh_lod/lod_change/threshold_pixels=4` a `.mobile=10` (převzato z Havrana do Puchartu).

## Stavba a logika světa
7. **Žádné rampy ani klíny jako záplaty** (Míša 9. 11.: „žádné rampy, to není logické v reálném světě“).
   Na most vede násyp cesty v terénu do výšky mostovky a test smyslu kontroluje, že terén před nástupem sedí na mostovce.
   - Puchart testy: `nastup_mostu_v_terenu`, `nabeh_vyska`, `most_navazuje_na_cestu`.
   - Most do prázdna (cesta končila 27 m od mostu) chytil až nový test.
8. **Vyhlazení terénu stahuje úzké násypy** (sigma 1,5 m ubrala 0,5 m). Násypy u mostů se proto nevyhlazují.
9. **Plížení výšky:** most bral výšku z terénu, terén z mostu a každá stavba ho zvedla o 0,1 m.
   Výška mostu se drží z minulé stavby.
10. **Štíty sedlových střech nejsou kamenné až do špičky.** Podle KCD je zeď kamenná do okapu a štít ze svislých prken.
    Prkenný štít potřebuje vlastní kolizi.
11. **Nároží z kamenů, ne pravítko.** Zdi z kvádrů mají dokonalé hrany. Nárožní kameny (střídavé vazáky, výstupek
    1–3,5 cm, pootočené) dají lomovou siluetu. Otlučené kameny jen do ~2,5 m nad terénem kvůli rozpočtu trojúhelníků.

## Postup a nástroje
12. **Komentář vložený doprostřed řádku seznamu v Pythonu** (`… bod(x),   # komentář … bod(y)`) zakomentoval zbytek
    trasy. Test průchodu pak hlásil divné uvíznutí. Komentáře jen na konec logického řádku.
13. **Měřit trvání kroků hlídačů** (Puchart `build/hlidaci_casy.txt`). Podle toho rozhodnout, co pouštět souběžně
    (4 jádra; Python testy vedle Godotu ano, dva Godoty naráz až po změření).
14. **Importní cache nemazat a import nepouštět zbytečně opakovaně** (rada z rešerše: u velkých projektů hodiny).
15. **Rešerše GitHubu** (Puchart `docs/reserse_github_nastroje.md`):
    - meshoptimizer/gltfpack a glTF-Transform pro optimalizaci exportu;
    - xatlas pro UV2 a Cycles bake světla bez obrazovky (LightmapGI v Compatibility zapéct nejde);
    - octahedral impostory pro les (hdrsniped, Compatibility, Godot 4.7; licence ověřit);
    - Terrain3D v Compatibility nefunguje (Texture2DArray);
    - arjun988/blender-skills potřebuje Blender s okny (MCP), headless ne.
