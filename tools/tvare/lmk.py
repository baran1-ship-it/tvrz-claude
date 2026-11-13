"""Landmarky hlavy Quaternius (žena/muž) – všechny posuny se zadávají vůči nim."""
import numpy as np
def landmarks(body, eyes):
    V = np.array([body.matrix_world @ v.co for v in body.data.vertices])
    E = np.array([eyes.matrix_world @ v.co for v in eyes.data.vertices])
    el = E[E[:, 0] > 0]; eye = (el.min(0) + el.max(0)) / 2
    head = V[V[:, 2] > eye[2] - 0.2]
    c = head[np.abs(head[:, 0]) < 0.004]
    band = c[(c[:, 2] < eye[2] - 0.02) & (c[:, 2] > eye[2] - 0.08)]
    nose = band[np.argmin(band[:, 1])]
    low = c[(c[:, 2] < nose[2] - 0.03) & (c[:, 2] > nose[2] - 0.14) & (c[:, 1] < nose[1] + 0.06)]
    # brada = nejnižší bod přední linie, kde se profil ještě nestáčí ke krku
    low = low[np.argsort(-low[:, 2])]
    chin = low[0]
    for p in low:
        if p[1] < chin[1] + 0.035: chin = p
        else: break
    top = head[np.argmax(head[:, 2])]
    back = head[(head[:, 2] > eye[2] - 0.02) & (head[:, 2] < eye[2] + 0.04)]
    return dict(eye=eye, nose=nose, chin=chin, top=top, ex=float(eye[0]),
                back_y=float(back[:, 1].max()), V=V)
