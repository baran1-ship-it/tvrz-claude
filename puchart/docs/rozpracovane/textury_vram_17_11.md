# Textury v grafické paměti – kontrola 17. 11. (plán z rešerše A2)

Tablet ukazuje VRAM 938 MB a roste (Míša, panel), rozbor GPU Havrana 15. 11.: textury 619 MB z ~900 MB. **Návrh – nic
nesmazáno ani nepřestaveno.** Čísla z tabletu NEOVERENO (tablet zatím výpis nedělal).

## Jak se to zjistilo
- `python3 nastroje/textury_vram.py .` – všechny importy textur (hra/**/*.import) a hlavičky výsledných `.etc2.ctex`
  (tablet): rozměr, formát, mipmapy, velikost v grafické paměti; duplicity podle obsahu zdrojového souboru; použití
  podle cest a uid v kódu a datech + závislostí modelů z Godotu (`nastroje/godot/zavislosti.gd`, importované glb jsou
  komprimované). Trvá ~3 s.
- Ve hře: `hra/scripts/textury_vram.gd` – po měření (`mereni.gd`) zapíše `user://textury_vram.txt`: všechny textury
  z materiálů scény od největší + součet a řádek do výsledku měření. Godot 4.7 nemá v GDScriptu výpis paměti po texturách
  (`texture_debug_usage` není vystavený), proto odhad z rozměru × formátu × 4/3 (mipmapy).
- PC (llvmpipe, desktopové formáty DXT ≈ stejná velikost jako ETC2) po startu u předního hradu: **873 textur ve scéně,
  odhad 548 MB, Godot hlásí textury 588 MB z VRAM 761 MB**. Tablet NEOVERENO – Míša pošle výsledek měření (nový řádek
  „textury ve scéně …“ a soubor textury_vram.txt).

## Hlavní nálezy (PC, scéna po startu)
1. **Duplicity ve scéně: 123 skupin, ~198 MB** (stejný obsah pod jinou cestou, každá kopie je v paměti zvlášť). Skoro vše
   `modely/stavby_h`: každá stavba z Blenderu vyveze svou kopii stejné textury Poly Haven (`hajovna_rough_wood_*`,
   `krcma_rada_rough_wood_*`, `kovarna_*`, k tomu `*_lod1_*` ještě jednou; normály domů `domy_M_*_normal` – 51 kopií
   jednoho souboru; jabloně `Young_Apple_0x_LOD1/LOD2` 6×). V celém projektu 239 skupin (309 MB, kdyby se nahrálo vše).
2. **`modely/stavby_h` 300 MB** ve scéně – největší složka; impostory stromů 86 MB (13 × 2048² ETC2_RGBA8 = 5,3 MB),
   rostliny 42 MB.
3. **Bez VRAM komprese 72 MB** (38 textur): `textury/maska_koleje.png` 4000×4000 L8 bez mipmap (15,3 MB, v terénu
   každý snímek), `maska_vysek` 1000² RGBA8, `maska_cesty` RGB8, barvy rostlin `modely/rostliny/*_color.png` RGBA8
   (`import_velikost.py` je nechává bezeztrátově kvůli alfě), UI (`ui/list.png` 4 MB, `obrazky/intro.jpg` 5,9 MB – jen
   v nabídce).
4. **2048 px a víc: 31 textur, 148 MB** ve scéně – impostory, jabloně (`jablon_*_color/normal` 2048², 3 stejné kopie),
   `cesta_atlas_a/_n`, kovadlina (6 × 2048²).
5. Nepoužité kandidáti: 19 textur, 13 MB (`obrazky/erb_kunstat.png`, `vz2.png`, `textury/hrad/kamen_*`, `omitka_bila_*`,
   `modely/voda_*` …) – VRAM nezatěžují (nikdo je nenačte), jen balík dat. Cesty skládané za běhu (předměty podle id,
   impostory podle druhu) nástroj počítá jako „možná“ – proto kandidáti, ne jistota.

## Doporučení (pořadí podle úspory; každé po souhlasu, pak měření na tabletu)
| # | co | úspora VRAM (odhad PC) | kde | riziko |
|---|---|---|---|---|
| T1 | **Sdílené textury staveb**: jedna knihovna materiálů (Poly Haven dřevo, prkna, omítka, hlína, šindel) pro všechny stavby a jejich LOD1 – Blender export s odkazem na společný soubor místo kopie v každém glb (nebo `glb_prebal.py`: přemapovat obrázky stejného obsahu na jednu cestu). Navazuje na NOSTALGIC TRAIN (sdílené dlaždice + malé masky, plán C1) | do ~200 MB (duplicity ve scéně 198 MB) | `blender/` export staveb, `nastroje/glb_prebal.py`, `nastroje/stavby_z_havrana.sh` | střední: každá stavba znovu snímkem (pravidlo „prvek všech staveb“) |
| T2 | **Maska kolejí 4000² L8 → 2048² (nebo ETC2_R11) s mipmapami**; masky `vysek`/`cesty` VRAM komprese nebo menší | ~15–20 MB | `nastroje/cesty.py` (rozlišení), import masky | nízké; ostrost kolejí ověřit snímkem |
| T3 | **Barvy rostlin s alfou do ETC2_RGBA8** místo RGBA8 (4× méně), zkusit nejdřív na 2 druzích – ETC2 alfa na okrajích listů snímkem | ~30 MB | `nastroje/import_velikost.py` (rostliny *.png → VRAM) | ETC2 alfa může zubatět okraje (důvod, proč zůstaly bezeztrátové – NEOVERENO) |
| T4 | **Impostory 2048 → 1024** (atlas 8×8, jeden pohled 256 → 128 px; impostor začíná až v dálce – ostrost NEOVERENO, snímek) | ~64 MB | `stromy_modely.json impostor.barva_max_px` | nízké; snímek hranice strom → impostor |
| T5 | **Jabloně 2048 → 1024** (+ 3 stejné kopie na jednu), kovadlina 2048 → 512–1024 (drobný předmět, rozpočet `textury_px bezna` 512–1024) | ~15 MB | import limit `process/size_limit` | nízké |
| T6 | ASTC místo ETC2: import dnes vyrábí pro mobil jen `.etc2.ctex` (ETC2_RGB8 0,5 B/px, ETC2_RGBA8 1 B/px); ASTC 4×4 má 1 B/px (bez úspory, lepší kvalita), úsporu by dalo jen ASTC 8×8 (0,25 B/px) – Godot 4.7 ho vybírá pro HDR/zvláštní případy, ne nastavením projektu (NEOVERENO) | 0 při 4×4 | – | teď nedělat; zvážit až po T1–T5 |
| T7 | Nepoužité kandidáty smazat z `hra/` | 0 VRAM, ~13 MB balíku | – | jen po potvrzení Míši |

Růst VRAM za hry (938 MB a roste) výpis jedné scény nevysvětlí – další krok: výpis `textury_vram.txt` po měření na začátku
a po 30 min hry porovnat (NEOVERENO, jestli rostou textury, nebo buffery MultiMeshů – `zasoba_mm`).

## Výstup nástroje (celý projekt, tablet ETC2) 17. 11.
Textur: 2603 (s výsledkem importu 2600). Součet VRAM všech importovaných (tablet ETC2): **787.3 MB** – horní mez, na tabletu je nahrané jen to, co je ve scéně.

Po formátech: ETC2_RGB8 538.7 MB, ETC2_RGBA8 147.5 MB, RGBA8 41.0 MB, ETC2_RG11 21.6 MB, RGB8 20.4 MB, L8 18.1 MB

### 30 největších
| # | textura | rozměr | formát | mipmapy | VRAM MB | import | odkazy |
|---|---|---|---|---|---|---|---|
| 1 | `textury/maska_koleje.png` | 4000×4000 | L8 | 0 | 15.3 | bezeztrátová | ano |
| 2 | `obrazky/intro.jpg` | 1920×1080 | RGB8 | 0 | 5.9 | bezeztrátová | ano |
| 3 | `modely/stavby_h/jablon_3_jablon_color.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese | jablon_3.glb |
| 4 | `modely/stavby_h/jablon_1_jablon_color.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese | jablon_1.glb |
| 5 | `modely/stavby_h/jablon_2_jablon_color.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese | jablon_2.glb |
| 6 | `textury/impostory/lipa_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 7 | `textury/impostory/jilm_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 8 | `textury/impostory/borovice_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 9 | `textury/impostory/dub_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 10 | `textury/impostory/habr_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 11 | `textury/impostory/vrba_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 12 | `textury/impostory/briza_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 13 | `textury/impostory/jedle_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 14 | `textury/impostory/smrk_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 15 | `textury/impostory/buk_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 16 | `textury/impostory/olse_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 17 | `textury/impostory/jasan_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 18 | `textury/impostory/javor_a.png` | 2048×2048 | ETC2_RGBA8 | 11 | 5.3 | VRAM komprese, limit 2048 px | možná (cesta skládaná za běhu) |
| 19 | `obrazky/erb_kunstat.png` | 960×1160 | RGBA8 | 0 | 4.2 | bezeztrátová | nenalezeno |
| 20 | `textury/ui/list.png` | 1024×1024 | RGBA8 | 0 | 4.0 | bezeztrátová | možná (cesta skládaná za běhu) |
| 21 | `textury/maska_vysek.png` | 1000×1000 | RGBA8 | 0 | 3.8 | bezeztrátová | ano |
| 22 | `textury/maska_cesty.png` | 1000×1000 | RGB8 | 0 | 2.9 | bezeztrátová | ano |
| 23 | `modely/predmety_h/kovadlina_1393_zelezo_albedo.jpg` | 2048×2048 | ETC2_RGB8 | 11 | 2.7 | VRAM komprese | kovadlina_1393.glb |
| 24 | `modely/predmety_h/kovadlina_1393_drevo_normal.jpg` | 2048×2048 | ETC2_RGB8 | 11 | 2.7 | VRAM komprese | kovadlina_1393.glb |
| 25 | `modely/predmety_h/kovadlina_1393_zelezo_normal.jpg` | 2048×2048 | ETC2_RGB8 | 11 | 2.7 | VRAM komprese | kovadlina_1393.glb |
| 26 | `modely/predmety_h/kovadlina_1393_drevo_albedo.jpg` | 2048×2048 | ETC2_RGB8 | 11 | 2.7 | VRAM komprese | kovadlina_1393.glb |
| 27 | `modely/predmety_h/kovadlina_1393_zelezo_orm.jpg` | 2048×2048 | ETC2_RGB8 | 11 | 2.7 | VRAM komprese | kovadlina_1393.glb |
| 28 | `modely/predmety_h/kovadlina_1393_drevo_orm.jpg` | 2048×2048 | ETC2_RGB8 | 11 | 2.7 | VRAM komprese | kovadlina_1393.glb |
| 29 | `modely/stavby_h/jablon_3_jablon_normal.png` | 2048×2048 | ETC2_RGB8 | 11 | 2.7 | VRAM komprese | jablon_3.glb |
| 30 | `modely/stavby_h/jablon_2_jablon_normal.png` | 2048×2048 | ETC2_RGB8 | 11 | 2.7 | VRAM komprese | jablon_2.glb |

### Součty po složkách (nejvíc VRAM)
| složka | textur | VRAM MB |
|---|---|---|
| `modely/stavby_h` | 661 | 325.7 |
| `modely/predmety_h` | 1403 | 173.8 |
| `textury/impostory` | 27 | 86.9 |
| `modely/rostliny` | 108 | 55.3 |
| `modely/les` | 39 | 26.0 |
| `modely/stromy` | 179 | 18.8 |
| `textury/maska_koleje.png` | 1 | 15.3 |
| `modely/topeni` | 22 | 14.7 |
| `modely/luzka` | 12 | 10.7 |
| `modely/hrady` | 73 | 9.3 |
| `textury/ui` | 13 | 8.8 |
| `obrazky/intro.jpg` | 1 | 5.9 |
| `textury/cesta` | 2 | 5.3 |
| `modely/seno` | 6 | 4.7 |
| `obrazky/erb_kunstat.png` | 1 | 4.2 |

### Duplicity (stejný obsah zdroje pod více cestami): 239 skupin, zbytečně 309.3 MB VRAM, pokud se nahrají všechny kopie
| kopií | VRAM MB/kus | cesty |
|---|---|---|
| 43 | 0.7 | `modely/predmety_h/stolicka_trzni_stolicka_trzni_Image_34.jpg` (možná)<br>`modely/predmety_h/vesak_kuze_vesak_kuze_Image_38.jpg` (možná)<br>`modely/predmety_h/stan_kupce_stan_kupce_Image_26.jpg` (možná)<br>`modely/predmety_h/stan_kupce_stan_kupce_Image_69.jpg` (možná)<br>`modely/predmety_h/stan_kupce_stan_kupce_Image_61.jpg` (možná)<br>`modely/predmety_h/stan_kupce_stan_kupce_Image_53.jpg` (možná) … |
| 36 | 0.7 | `modely/les/textury/rough_wood_lw_rough_b2073120.png` (možná)<br>`modely/stavby_h/kovarna_rough_wood_tram_c2_rough.png` (možná)<br>`modely/stavby_h/hajovna_rough_wood_tram_rough.png` (ano)<br>`modely/stavby_h/hajovna_rough_wood_tram_g_rough.png` (ano)<br>`modely/stavby_h/kovarna_rough_wood_tram_in_rough.png` (možná)<br>`modely/stavby_h/kovarna_rough_wood_tram_g_rough.png` (možná) … |
| 126 | 0.2 | `modely/predmety_h/spalek_stipani_jasan_naradi_albedo.jpg` (možná)<br>`modely/predmety_h/prapor_kolovrat_dub_tyc_albedo.jpg` (možná)<br>`modely/predmety_h/vidle_jasan_naradi_albedo.jpg` (možná)<br>`modely/predmety_h/stit_pernstejn_stit_rub_albedo.jpg` (možná)<br>`modely/predmety_h/hrabe_jasan_naradi_albedo.jpg` (možná)<br>`modely/predmety_h/soudek_duzka1_albedo.jpg` (možná) … |
| 3 | 5.3 | `modely/stavby_h/jablon_3_jablon_color.png` (ano)<br>`modely/stavby_h/jablon_1_jablon_color.png` (ano)<br>`modely/stavby_h/jablon_2_jablon_color.png` (ano) |
| 51 | 0.2 | `modely/stavby_h/domy_M_RoubeniHnede_001_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_Sindel_001_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_Zhlavi_001_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_Zhlavi_003_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_SindelMech_001_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_RoubeniVnitrni_001_normal.jpg` (ano) … |
| 13 | 0.7 | `modely/stavby_h/krcma_rada_weathered_planks_stit_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_weathered_planks_pod_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_weathered_planks_dv_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_weathered_planks_povc_rough.png` (ano)<br>`modely/stavby_h/hajovna_weathered_planks_dv_rough.png` (ano)<br>`modely/stavby_h/hajovna_weathered_planks_stit_rough.png` (ano) … |
| 6 | 1.3 | `modely/stavby_h/Young_Apple_01_LOD2_AppleLeaf_BaseColor.png` (ano)<br>`modely/stavby_h/Young_Apple_01_LOD1_AppleLeaf_BaseColor.png` (ano)<br>`modely/stavby_h/Young_Apple_03_LOD2_AppleLeaf_BaseColor.png` (ano)<br>`modely/stavby_h/Young_Apple_02_LOD1_AppleLeaf_BaseColor.png` (ano)<br>`modely/stavby_h/Young_Apple_02_LOD2_AppleLeaf_BaseColor.png` (ano)<br>`modely/stavby_h/Young_Apple_03_LOD1_AppleLeaf_BaseColor.png` (ano) |
| 3 | 2.7 | `modely/stavby_h/jablon_3_jablon_normal.png` (ano)<br>`modely/stavby_h/jablon_2_jablon_normal.png` (ano)<br>`modely/stavby_h/jablon_1_jablon_normal.png` (ano) |
| 126 | 0.0 | `modely/predmety_h/polevka_jasan_naradi_normal.jpg` (možná)<br>`modely/predmety_h/pristresek_plachta_jasan_naradi_normal.jpg` (možná)<br>`modely/predmety_h/stit_michalovic_stit_rub_normal.jpg` (možná)<br>`modely/predmety_h/vlajka_sternberk_dub_tyc_normal.jpg` (možná)<br>`modely/predmety_h/kad_kad_duzka2_normal.jpg` (možná)<br>`modely/predmety_h/stul_hodovni_dub_hodovni_normal.jpg` (možná) … |
| 8 | 0.7 | `modely/stavby_h/hajovna_clay_plaster_maz_rough.png` (ano)<br>`modely/stavby_h/hajovna_clay_plaster_mazc_rough.png` (ano)<br>`modely/stavby_h/hajovna_clay_plaster_pecc2_rough.png` (ano)<br>`modely/stavby_h/hajovna_clay_plaster_pop_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_clay_plaster_mazc_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_clay_plaster_pop_rough.png` (možná) … |
| 7 | 0.7 | `modely/les/textury/rough_wood_nor_fca32dca.jpg` (možná)<br>`modely/stavby_h/krcma_rada_rough_wood_nor.jpg` (ano)<br>`modely/stavby_h/hajovna_rough_wood_nor.jpg` (ano)<br>`modely/stavby_h/krcma_rada_lod1_rough_wood_nor.jpg` (ano)<br>`modely/stavby_h/kovarna_lod1_rough_wood_nor.jpg` (možná)<br>`modely/stavby_h/kovarna_rough_wood_nor.jpg` (možná) … |
| 6 | 0.7 | `modely/stavby_h/kovarna_lod1_rough_wood_sin_rough.png` (možná)<br>`modely/stavby_h/kovarna_rough_wood_sin_rough.png` (možná)<br>`modely/stavby_h/hajovna_rough_wood_sin_rough.png` (ano)<br>`modely/stavby_h/hajovna_lod1_rough_wood_sin_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_rough_wood_sin_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_lod1_rough_wood_sin_rough.png` (ano) |
| 6 | 0.7 | `modely/stavby_h/kovarna_lod1_weathered_planks_stit_diff.jpg` (možná)<br>`modely/stavby_h/hajovna_lod1_weathered_planks_stit_diff.jpg` (ano)<br>`modely/stavby_h/krcma_rada_lod1_weathered_planks_stit_diff.jpg` (ano)<br>`modely/stavby_h/kovarna_weathered_planks_stit_diff.jpg` (možná)<br>`modely/stavby_h/hajovna_weathered_planks_stit_diff.jpg` (ano)<br>`modely/stavby_h/krcma_rada_weathered_planks_stit_diff.jpg` (ano) |
| 6 | 0.7 | `modely/stavby_h/kovarna_rough_wood_sin_diff.jpg` (možná)<br>`modely/stavby_h/hajovna_rough_wood_sin_diff.jpg` (ano)<br>`modely/stavby_h/kovarna_lod1_rough_wood_sin_diff.jpg` (možná)<br>`modely/stavby_h/krcma_rada_lod1_rough_wood_sin_diff.jpg` (ano)<br>`modely/stavby_h/krcma_rada_rough_wood_sin_diff.jpg` (ano)<br>`modely/stavby_h/hajovna_lod1_rough_wood_sin_diff.jpg` (ano) |
| 6 | 0.7 | `modely/stavby_h/hajovna_rough_wood_sinm1_rough.png` (ano)<br>`modely/stavby_h/hajovna_rough_wood_sint_rough.png` (ano)<br>`modely/stavby_h/kovarna_rough_wood_sint_rough.png` (možná)<br>`modely/stavby_h/krcma_rada_rough_wood_sinm1_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_rough_wood_sint_rough.png` (ano)<br>`modely/stavby_h/kovarna_rough_wood_sinm1_rough.png` (možná) |
| 6 | 0.7 | `modely/stavby_h/kovarna_rough_wood_tram_diff.jpg` (možná)<br>`modely/stavby_h/krcma_rada_rough_wood_tram_diff.jpg` (ano)<br>`modely/stavby_h/hajovna_lod1_rough_wood_tram_diff.jpg` (ano)<br>`modely/stavby_h/krcma_rada_lod1_rough_wood_tram_diff.jpg` (ano)<br>`modely/stavby_h/kovarna_lod1_rough_wood_tram_diff.jpg` (možná)<br>`modely/stavby_h/hajovna_rough_wood_tram_diff.jpg` (ano) |
| 6 | 0.7 | `modely/stavby_h/Young_Apple_02_LOD2_Bark_Normal.jpg` (ano)<br>`modely/stavby_h/Young_Apple_03_LOD2_Bark_Normal.jpg` (ano)<br>`modely/stavby_h/Young_Apple_01_LOD2_Bark_Normal.jpg` (ano)<br>`modely/stavby_h/Young_Apple_01_LOD1_Bark_Normal.jpg` (ano)<br>`modely/stavby_h/Young_Apple_03_LOD1_Bark_Normal.jpg` (ano)<br>`modely/stavby_h/Young_Apple_02_LOD1_Bark_Normal.jpg` (ano) |
| 6 | 0.7 | `modely/stavby_h/Young_Apple_03_LOD2_AppleLeaf_Normal.png` (ano)<br>`modely/stavby_h/Young_Apple_03_LOD1_AppleLeaf_Normal.png` (ano)<br>`modely/stavby_h/Young_Apple_01_LOD2_AppleLeaf_Normal.png` (ano)<br>`modely/stavby_h/Young_Apple_02_LOD2_AppleLeaf_Normal.png` (ano)<br>`modely/stavby_h/Young_Apple_01_LOD1_AppleLeaf_Normal.png` (ano)<br>`modely/stavby_h/Young_Apple_02_LOD1_AppleLeaf_Normal.png` (ano) |
| 6 | 0.7 | `modely/stavby_h/kovarna_lod1_weathered_planks_nor.jpg` (možná)<br>`modely/stavby_h/krcma_rada_lod1_weathered_planks_nor.jpg` (ano)<br>`modely/stavby_h/hajovna_lod1_weathered_planks_nor.jpg` (ano)<br>`modely/stavby_h/krcma_rada_weathered_planks_nor.jpg` (ano)<br>`modely/stavby_h/hajovna_weathered_planks_nor.jpg` (ano)<br>`modely/stavby_h/kovarna_weathered_planks_nor.jpg` (možná) |
| 6 | 0.7 | `modely/stavby_h/krcma_rada_dirt_floor_hl_rough.png` (ano)<br>`modely/stavby_h/kovarna_dirt_floor_hlc_rough.png` (možná)<br>`modely/stavby_h/hajovna_dirt_floor_hlc_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_dirt_floor_hlc_rough.png` (ano)<br>`modely/stavby_h/kovarna_dirt_floor_hl_rough.png` (možná)<br>`modely/stavby_h/hajovna_dirt_floor_hl_rough.png` (ano) |
| 6 | 0.7 | `modely/stavby_h/Young_Apple_02_LOD2_Bark_BaseColor.jpg` (ano)<br>`modely/stavby_h/Young_Apple_01_LOD2_Bark_BaseColor.jpg` (ano)<br>`modely/stavby_h/Young_Apple_03_LOD1_Bark_BaseColor.jpg` (ano)<br>`modely/stavby_h/Young_Apple_02_LOD1_Bark_BaseColor.jpg` (ano)<br>`modely/stavby_h/Young_Apple_01_LOD1_Bark_BaseColor.jpg` (ano)<br>`modely/stavby_h/Young_Apple_03_LOD2_Bark_BaseColor.jpg` (ano) |
| 6 | 0.7 | `modely/stavby_h/Young_Apple_01_LOD2_Bark_Roughness.png` (ano)<br>`modely/stavby_h/Young_Apple_02_LOD2_Bark_Roughness.png` (ano)<br>`modely/stavby_h/Young_Apple_03_LOD2_Bark_Roughness.png` (ano)<br>`modely/stavby_h/Young_Apple_01_LOD1_Bark_Roughness.png` (ano)<br>`modely/stavby_h/Young_Apple_02_LOD1_Bark_Roughness.png` (ano)<br>`modely/stavby_h/Young_Apple_03_LOD1_Bark_Roughness.png` (ano) |
| 19 | 0.2 | `modely/stavby_h/mlyn_M_ZhlaviMech_normal.jpg` (ano)<br>`modely/stavby_h/mlyn_M_Dub_normal.jpg` (ano)<br>`modely/stavby_h/mlyn_M_SindelMechSlaby_normal.jpg` (ano)<br>`modely/stavby_h/mlyn_M_Hrazdeni_normal.jpg` (ano)<br>`modely/stavby_h/mlyn_M_RoubeniLisejnik_normal.jpg` (ano)<br>`modely/stavby_h/mlyn_M_RoubeniSpodni_normal.jpg` (ano) … |
| 17 | 0.2 | `modely/stavby_h/domy_M_PovalaZacouzena_002_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_Dvere_001_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_Dvere_004_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_Dvere_003_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_PovalaZacouzena_normal.jpg` (ano)<br>`modely/stavby_h/domy_M_StitPrkna_002_normal.jpg` (ano) … |
| 5 | 0.7 | `modely/stavby_h/hajovna_bark_brown_02_prt_rough.png` (ano)<br>`modely/stavby_h/hajovna_bark_brown_02_r_rough.png` (ano)<br>`modely/stavby_h/krcma_rada_bark_brown_02_r_rough.png` (ano)<br>`modely/stavby_h/kovarna_bark_brown_02_r_rough.png` (možná)<br>`modely/stavby_h/hajovna_bark_brown_02_prts_rough.png` (ano) |

### Nepoužité – kandidáti (cesta ani uid nenalezeny v kódu, datech, scénách ani importovaných glb): 19, 12.9 MB
Hra je nenahraje, dokud je nikdo nenačte – VRAM tablet nezatěžují, jen velikost balíku dat. Nic nesmazáno.

| textura | rozměr | VRAM MB |
|---|---|---|
| `obrazky/erb_kunstat.png` | 960×1160 | 4.2 |
| `modely/seno/textures/Seno_Albedo_1K.png` | 1024×1024 | 1.3 |
| `vz2.png` | 1600×1000 | 1.0 |
| `modely/voda_weathered_brown_planks_nor_gl.jpg` | 1024×1024 | 0.7 |
| `modely/voda_weathered_brown_planks_Diffuse.jpg` | 1024×1024 | 0.7 |
| `textury/hrad/omitka_bila_nor.jpg` | 1024×1024 | 0.7 |
| `textury/hrad/kamen_nor.jpg` | 1024×1024 | 0.7 |
| `textury/hrad/kamen_diff.jpg` | 1024×1024 | 0.7 |
| `textury/hrad/omitka_bila_diff.jpg` | 1024×1024 | 0.7 |
| `textury/hrad/kamen_disp.jpg` | 1024×1024 | 0.7 |
| `textury/trava_nizka_atlas.png` | 1024×256 | 0.3 |
| `modely/voda_droba_nor_gl.jpg` | 512×512 | 0.2 |
| `modely/voda_dirt_floor_Diffuse.jpg` | 512×512 | 0.2 |
| `modely/voda_wood_planks_grey_Diffuse.jpg` | 512×512 | 0.2 |
| `modely/voda_dirt_floor_nor_gl.jpg` | 512×512 | 0.2 |
| `modely/voda_wood_planks_grey_nor_gl.jpg` | 512×512 | 0.2 |
| `modely/voda_rough_wood_Diffuse.jpg` | 512×512 | 0.2 |
| `modely/voda_rough_wood_nor_gl.jpg` | 512×512 | 0.2 |
| `modely/voda_droba_Diffuse.jpg` | 512×512 | 0.2 |

Možná použité (jméno souboru nebo složka se v kódu/datech vyskytuje, cesta se skládá za běhu): 1956, 442.8 MB.

### Další nálezy
- 2048 px a víc: 28 textur, 129.9 MB: `textury/maska_koleje.png`, `modely/stavby_h/jablon_3_jablon_color.png`, `modely/stavby_h/jablon_1_jablon_color.png`, `modely/stavby_h/jablon_2_jablon_color.png`, `textury/impostory/lipa_a.png`, `textury/impostory/jilm_a.png`, `textury/impostory/borovice_a.png`, `textury/impostory/dub_a.png`, `textury/impostory/habr_a.png`, `textury/impostory/vrba_a.png`, `textury/impostory/briza_a.png`, `textury/impostory/jedle_a.png` …
- bez VRAM komprese nad 0,5 MB (na GPU rozbalené RGBA/RGB): 39 textur, 77.3 MB: `textury/maska_koleje.png` (L8), `obrazky/intro.jpg` (RGB8), `obrazky/erb_kunstat.png` (RGBA8), `textury/ui/list.png` (RGBA8), `textury/maska_vysek.png` (RGBA8), `textury/maska_cesty.png` (RGB8), `textury/ui/mapa.png` (RGB8), `modely/rostliny/trava_vysoka_1_trava1k_color.png` (RGBA8), `modely/rostliny/kapradi_1_kapradiP_color.png` (RGBA8), `modely/rostliny/ostruzina_1_ostruzinaP_color.png` (RGBA8), `modely/rostliny/kopriva_1_koprivaP_color.png` (RGBA8), `modely/rostliny/hloh_2_hloh_color.png` (RGBA8)
- použité bez mipmap nad 0,25 MB (ve 3D šum a víc čtení paměti v dálce): 11: `textury/maska_koleje.png`, `obrazky/intro.jpg`, `textury/ui/list.png`, `textury/maska_vysek.png`, `textury/maska_cesty.png`, `textury/ui/mapa.png`, `data/stanoviste.png`, `data/kryt.png`, `data/kamenitost.png`, `textury/ui/pruh.png`, `textury/ui/pergamen.png`
