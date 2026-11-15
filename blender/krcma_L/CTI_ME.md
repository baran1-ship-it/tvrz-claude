# Zdroj krčmy do L (Míšin model z Disku, `krcma_L (1).zip`, 14. 11.)

Sestavení: `bash stahni_foto.sh` (15. 11.; fotky nejsou v gitu) → `foto/` = fotky textur z Poly Haven 2k (`<pid>_diff|nor|rough.jpg`, nor = nor_gl; pid: rough_wood, clay_plaster,
white_rough_plaster, weathered_planks, stone_wall, bark_brown_02, dirt_floor, rock_surface, broken_wall, brown_leather,
cobblestone_large_01, reed_roof_04, rough_linen, mossy_rock jen diff) + `trava_grass004.jpg` (jen náhledová scéna), pak
`/opt/bl/bin/python krcma_L.py --norender` → `krcma_L.glb`, `krcma_L_lod1.glb` do `modely/krcma/`.

Změny proti zdroji z Disku (15. 11., Míša „krčma má špatné zábradlí nahoru, na koncích ochozu chybí zábradlí“):
- `_stavba.stairs(rail_side)`: zábradlí schodů na volné straně (dřív u zdi stáje);
- schody končí na severním kraji podesty (dřív pod podestou – schod 0,5 m);
- `zabradli()` + `ZAB`: zábradlí podesty (vnější kraj, jižní konec) a obou konců pavlače, kolize `Zabr*`, `ZabrSchodu`;
- Blender 4.2: `use_nodes = True` u nových materiálů (zdroj psaný pro novější Blender).
