"""68 bodů obličeje (dlib): python3 lmk.py <obr> <out.json> [nahled.jpg]"""
import sys, json, dlib, numpy as np
from PIL import Image, ImageDraw
M = "/home/claude/dl/frm/face_recognition_models-0.3.0/face_recognition_models/models/"
img = np.asarray(Image.open(sys.argv[1]).convert("RGB"))
det = dlib.get_frontal_face_detector(); sp = dlib.shape_predictor(M + "shape_predictor_68_face_landmarks.dat")
faces = det(img, 1)
if not faces:
    cnn = dlib.cnn_face_detection_model_v1(M + "mmod_human_face_detector.dat"); faces = [f.rect for f in cnn(img, 1)]
print("faces", len(faces))
r = max(faces, key=lambda f: f.width())
pts = [(p.x, p.y) for p in sp(img, r).parts()]
json.dump(pts, open(sys.argv[2], "w"))
if len(sys.argv) > 3:
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    for i, (x, y) in enumerate(pts): d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 0, 0))
    im.resize((im.width // 2, im.height // 2)).save(sys.argv[3])
