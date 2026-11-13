"""Úprava textury kůže podle 3D oblastí (rasterizace do UV)."""
import numpy as np
from PIL import Image, ImageFilter
def raster_attr(obj, attr, size):
    """attr: per-vertex hodnota (N,) -> obraz size x size, průměr přes trojúhelníky (barycentricky)."""
    me = obj.data; me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    img = np.zeros((size, size)); cnt = np.zeros((size, size))
    for t in me.loop_triangles:
        P = np.array([uv[l].uv for l in t.loops]) * size
        A = np.array([attr[v] for v in t.vertices])
        if A.max() <= 1e-4: continue
        x0, y0 = np.floor(P.min(0)).astype(int); x1, y1 = np.ceil(P.max(0)).astype(int)
        x0=max(x0,0); y0=max(y0,0); x1=min(x1,size-1); y1=min(y1,size-1)
        xs, ys = np.meshgrid(np.arange(x0, x1+1)+0.5, np.arange(y0, y1+1)+0.5)
        (ax, ay), (bx, by), (cx, cy) = P
        den = (by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den) < 1e-9: continue
        l1 = ((by-cy)*(xs-cx)+(cx-bx)*(ys-cy))/den; l2 = ((cy-ay)*(xs-cx)+(ax-cx)*(ys-cy))/den; l3 = 1-l1-l2
        m = (l1>=-0.02)&(l2>=-0.02)&(l3>=-0.02)
        val = l1*A[0]+l2*A[1]+l3*A[2]
        yy = (size-1-(ys[m]-0.5)).astype(int); xx = (xs[m]-0.5).astype(int)
        img[yy, xx] = np.maximum(img[yy, xx], val[m])
    return img
