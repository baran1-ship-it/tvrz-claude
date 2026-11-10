"""Valouny a balvany do koryt (Míša 10. 11.: „brod a potok nemají jediný kámen, přitom je to kamenný potok“; AOPK: kamenité
koryto Veličky, voda_hra.json; geologie droba – skaly.json). 6 tvarů valounu velikosti 1 m (otlučené, zaoblené hrany, ~70 troj.),
ve hře instancované podle hra/data/koryto_kameny.json (nastroje/koryto_kameny.py). Materiál skala → skala.gdshader.
  /opt/bl/bin/python blender/kameny_koryta.py <koren_puchartu>
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrady as H
from hrady import Part, M, kit
import random
rg = random.Random(1393)
P = []
for i in range(6):
    p = Part("valoun_%d" % i)
    kit.RND.seed(1393 + i)
    sx, sy, sz = 1.0, rg.uniform(0.45, 0.7), rg.uniform(0.6, 0.9)   # valoun: plochý, protáhlý (droba se láme do desek)
    kit.stone(p, M((0, sy / 2, 0)), (sx, sy, sz), "skala", cham=rg.uniform(0.18, 0.26), rough=rg.uniform(0.03, 0.06))
    P.append(p)
import bpy
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
H.uloz(P, "kameny_koryta", kolize=False)
