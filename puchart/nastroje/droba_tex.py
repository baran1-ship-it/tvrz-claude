"""Textura droby pro skály (blender/tex/droba_*): Poly Haven rock_face (CC0) je teplá červenohnědá – droba a břidlice
na Puchartu jsou šedé až šedozelené (fotky vyraznavylet.cz, GC80T08). Odbarvit na 25 % sytosti, posunout do studena,
zesvětlit; normála beze změny. python3 droba_tex.py <koren>"""
import sys, shutil
import numpy as np
from PIL import Image
T = sys.argv[1] + "/blender/tex/"
a = np.asarray(Image.open(T + "rock_face_Diffuse.jpg").convert("RGB")).astype(np.float32) / 255
l = (a @ np.array([0.3, 0.55, 0.15]))[..., None]
g = l + (a - l) * 0.25
g = g * np.array([0.97, 1.0, 1.04]) * 1.12
Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).save(T + "droba_Diffuse.jpg", quality=92)
shutil.copy(T + "rock_face_nor_gl.jpg", T + "droba_nor_gl.jpg")
print("droba_Diffuse.jpg")
