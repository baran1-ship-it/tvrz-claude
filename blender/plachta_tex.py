"""Textura plachty lomu (Misa: "nic neni ciste bile ani sede, mrkni fotky"): Poly Haven rough_linen (CC0) jako vazba,
barva nebielene lnene platno zasedle, spinave lemy (UV okraje = cipy a lem), vodni mapy. Vystup tex_cache/plachta_diff_2k.jpg.
Spusteni: python3 blender/plachta_tex.py (potrebuje PIL, numpy, sit)."""
import io, os, urllib.request
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/rough_linen/rough_linen_diff_2k.jpg"
im = Image.open(io.BytesIO(urllib.request.urlopen(URL).read())).convert("L").resize((2048, 2048))
a = np.asarray(im, dtype=np.float32)
a = (a - a.mean()) / a.std()
H = W = 2048
rng = np.random.default_rng(7)


def blot(scale, amp):
    n = rng.random((H // scale + 2, W // scale + 2)).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), dtype=np.float32) / 255
    return (n - 0.5) * amp


v = np.linspace(0, 1, H)[:, None]
u = np.linspace(0, 1, W)[None, :]
edge = np.minimum(v, 1 - v)                     # lemy (v kraje), ne boky
grime = np.clip(1 - edge / 0.12, 0, 1) ** 1.5
base = np.array([132, 123, 102], np.float32)       # zasedle, na slunci nesviti bile
l = 1 + 0.06 * a + blot(128, 0.1) + blot(32, 0.05) - 0.28 * grime
st = np.zeros((H, W), np.float32)
yy, xx = np.ogrid[:H, :W]
for _ in range(40):
    cx, cy = rng.integers(0, W), rng.integers(0, H)
    r = rng.integers(30, 180)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    st = np.maximum(st, (np.exp(-((d - 1) / 0.12) ** 2) * 0.5 + np.clip(1 - d, 0, 1) * 0.25) * rng.uniform(0.3, 1))
l -= 0.12 * st
col = base[None, None, :] * l[..., None]
col[..., 2] -= 12 * grime + 8 * st
col[..., 0] += 4 * grime
Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(os.path.join(HERE, "tex_cache", "plachta_diff_2k.jpg"), quality=92)
