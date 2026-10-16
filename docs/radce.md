# Komunikace s rádcem

## 2026-10-16 – K1 (textury): nesouhlas s předpokladem, upravený postup

**Zjištění:** hlavní hra už fotografické PBR textury z Poly Haven používá (blender/textures.py: zdivo
castle_wall_slates, hlína stony_dirt_path, tráva grass_path_2, došky, šindel, kůra, pískovec ...).
`tools/gen_tex.py`, `textures/*_a.png` a `shaders/terrain.gdshader` patří ke staré krajině (scripts/terrain.gd),
kterou hra vůbec nenačítá – výměna tam by nic nezměnila.

**Skutečná příčina vzhledu terénu (shaders/zem.gdshader):** fotku trávy přebarvovaly dva procedurální šumy,
od 25 m ji nahrazovala plochá tmavě zelená barva (od ~140 m žádná fotka), les byl jen vypočtená barva
a tráva byla grass_path_2 (tráva s cestičkou, vzor 1 m) opakovaná po 1,4 m.

**Postup K1:** louka = leafy_grass (2 m, skutečné měřítko), velké skvrny a dálka = aerial_grass_rock
(letecký snímek, 15 m) místo ploché barvy, les = forest_leaves_02 (3 m), procedurální přebarvení pryč.
brown_mud_leaves_01 stažena pro blátivé cesty ve vsi. Pole (lány) zatím zůstávají vypočtené barvy – návrh:
v dalším kole fotka pole (dry_mud_field_001 / withered_grass) podle plodiny.

**Otázka:** souhlasí rádce, že K1 = jen terén (stěny, střechy a dřevo už fotky mají a 1024 px limit drží)?

## 2026-10-16 – K4 (skály) už částečně hotovo

Remesh (voxel 0,15 m) → decimace na 2 700 / 800 / 150 troj. → zapečení barvy a normál z originálu (Cycles)
v jedné funkci `_skala_lod` (blender/nove.py) pro všech 6 typů věží. Voxel 0,15 místo navržených 0,4 m:
při 0,4 m mizí vodorovné vrstvy pískovce (nejvýraznější tvar), po decimaci na 2 700 troj. je rozdíl jen
v čase pečení (sekundy). Varianty textury (okr/šedá/mech) zatím ne – přijdou s K4.
