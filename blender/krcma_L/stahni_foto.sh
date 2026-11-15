#!/bin/bash
# Fotky textur pro zdroj krcmy (Poly Haven 2k, CC0) do foto/ - v gitu nejsou (.gitignore). 15. 11.: export v nove session
# spadl na chybejicich foto/*_disp.png a brown_leather (na Poly Haven je diffuse jako _albedo).  bash stahni_foto.sh
cd "$(dirname "$0")" && mkdir -p foto && cd foto
U=https://dl.polyhaven.org/file/ph-assets/Textures
for p in rough_wood clay_plaster white_rough_plaster weathered_planks stone_wall bark_brown_02 dirt_floor rock_surface broken_wall brown_leather cobblestone_large_01 reed_roof_04 rough_linen; do
  [ -f ${p}_diff.jpg ] || curl -sSf -o ${p}_diff.jpg $U/jpg/2k/$p/${p}_diff_2k.jpg || curl -sSf -o ${p}_diff.jpg $U/jpg/2k/$p/${p}_albedo_2k.jpg || echo "CHYBI $p diff"
  [ -f ${p}_nor.jpg ] || curl -sSf -o ${p}_nor.jpg $U/jpg/2k/$p/${p}_nor_gl_2k.jpg || echo "CHYBI $p nor"
  [ -f ${p}_rough.jpg ] || curl -sSf -o ${p}_rough.jpg $U/jpg/2k/$p/${p}_rough_2k.jpg || rm -f ${p}_rough.jpg
done
[ -f mossy_rock_diff.jpg ] || curl -sSf -o mossy_rock_diff.jpg $U/jpg/2k/mossy_rock/mossy_rock_diff_2k.jpg
for p in broken_wall cobblestone_large_01; do [ -f ${p}_disp.png ] || curl -sSf -o ${p}_disp.png $U/png/2k/$p/${p}_disp_2k.png; done
[ -f trava_grass004.jpg ] || { curl -sSfL -o g.zip "https://ambientcg.com/get?file=Grass004_1K-JPG.zip" && python3 -c "
import zipfile;z=zipfile.ZipFile('g.zip');n=[x for x in z.namelist() if 'Color' in x][0];open('trava_grass004.jpg','wb').write(z.read(n))" && rm g.zip; }
ls | wc -l
