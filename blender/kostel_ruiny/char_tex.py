# Ohořelé dřevo: nepravidelné "aligátorové" bloky uhlíku (Voronoi protažené po vláknech), hluboké trhliny,
# vypouklé hřbety, dlaždicové; 1024 px = 0,75 m (UV trámů), svisle = podél vláken.
import numpy as np, os, sys
from PIL import Image
N = 1024; rng = np.random.default_rng(5); out = sys.argv[1]
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
def tnoise(s, seed):
    r = np.random.default_rng(seed); g = r.random((s, s)).astype(np.float32)
    X = xx / N * s; Y = yy / N * s; x0 = np.floor(X).astype(int); y0 = np.floor(Y).astype(int)
    fx = X - x0; fy = Y - y0; fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    return (g[y0 % s, x0 % s] * (1 - fx) + g[y0 % s, (x0 + 1) % s] * fx) * (1 - fy) + (g[(y0 + 1) % s, x0 % s] * (1 - fx) + g[(y0 + 1) % s, (x0 + 1) % s] * fx) * fy
def fbm(s, o, seed):
    a = 0; w = 1; t = 0
    for k in range(o): a = a + tnoise(s * 2 ** k, seed + k) * w; t += w; w *= 0.5
    return a / t
def vor(nx, ny, warp):
    cw, ch = N / nx, N / ny
    px = (np.arange(nx)[None, :] + rng.uniform(0.1, 0.9, (ny, nx))) * cw
    py = (np.arange(ny)[:, None] + rng.uniform(0.1, 0.9, (ny, nx))) * ch
    X = xx + warp[0]; Y = yy + warp[1]
    cx = np.floor(X / cw).astype(int); cy = np.floor(Y / ch).astype(int)
    F1 = np.full((N, N), 1e9, np.float32); F2 = F1.copy(); ID = np.zeros((N, N), np.int64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            gx = cx + dx; gy = cy + dy
            ox = px[gy % ny, gx % nx] + np.floor_divide(gx, nx) * N; oy = py[gy % ny, gx % nx] + np.floor_divide(gy, ny) * N
            d = np.sqrt(((X - ox) / cw) ** 2 + ((Y - oy) / ch) ** 2)
            m = d < F1
            F2 = np.where(m, F1, np.minimum(F2, d)); ID = np.where(m, (gy % ny) * nx + gx % nx, ID); F1 = np.where(m, d, F1)
    return F1, F2, ID
warp = ((fbm(4, 3, 1) - 0.5) * 40, (fbm(4, 3, 2) - 0.5) * 40)
F1, F2, ID = vor(17, 11, warp)                    # bloky ~4,4 × 6,8 cm
e = F2 - F1
cell = ((ID * 2654435761) % 1009) / 1009.0
cwid = 0.035 + 0.05 * fbm(6, 2, 3) + 0.03 * cell
crk = np.clip((e - cwid) / 0.10, 0, 1)
dome = np.clip(1 - F1 * 0.9, 0, 1) ** 0.6
f1, f2, _ = vor(41, 27, warp); small = np.clip(((f2 - f1) - 0.04) / 0.08, 0, 1)
hair = np.clip((np.abs(fbm(18, 3, 4) - 0.5) - 0.01) / 0.02, 0, 1)
grain = fbm(3, 2, 6) * 0.3 + tnoise(64, 7) * 0.0
hgt = crk * (0.45 + 0.4 * dome + 0.15 * cell) * (0.75 + 0.25 * small) * (0.85 + 0.15 * hair)
lo = fbm(2, 4, 9)
burn = np.clip(1.3 + (lo - 0.5) * 2.6, 0, 1)
col = np.array([0.018, 0.017, 0.016]) * (0.3 + 1.1 * hgt[..., None])
sheen = np.clip((hgt - 0.6) * 3, 0, 1) * (0.4 + 0.6 * fbm(20, 2, 10))
col = col + np.array([0.035, 0.034, 0.033]) * sheen[..., None]
brown = np.array([0.16, 0.09, 0.045]) * (0.6 + 0.6 * fbm(3, 4, 11)[..., None]) * (0.3 + 0.7 * crk[..., None])
col = col * burn[..., None] + brown * (1 - burn[..., None])
Image.fromarray((np.clip(col, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)).save(os.path.join(out, "char_wood_diff.jpg"), quality=93)
H = hgt * burn + 0.55 * crk * (1 - burn)
gy, gx = np.gradient(H)
st = 7.0; nx = -gx * st; ny = gy * st; nz = np.ones_like(H); l = np.sqrt(nx * nx + ny * ny + nz * nz)
Image.fromarray(((np.stack([nx / l, ny / l, nz / l], -1) * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(out, "char_wood_nor.jpg"), quality=95)
rough = np.clip(0.97 - 0.30 * sheen * burn, 0.6, 1.0)
Image.fromarray((rough * 255).astype(np.uint8)).save(os.path.join(out, "char_wood_rough.jpg"), quality=92)
print("ok")
