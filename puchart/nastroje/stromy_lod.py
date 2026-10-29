"""LOD1 stromů Havrana (pravidla_modelu.json strom: troj_lod [12000, 3000, 2]).

Automatická decimace listových karet nefunguje (díry a „plácačky“ – Havran), proto postup jako SpeedTree:
z listí se ponechá podíl karet (souvislé komponenty) a zbylé se zvětší kolem svého středu, aby koruna zůstala
stejně hustá. Kmen a větve beze změny. Výstup <model>_lod1.glb vedle originálu.
python3 stromy_lod.py <adresar_glb> <podil_karet> <zvetseni>
"""
import sys, glob, os, struct, json
import numpy as np
from pygltflib import GLTF2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

d, podil, zv = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
rng = np.random.default_rng(7)
TYP = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NK = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}

def cti(g, blob, ai):
    a = g.accessors[ai]; bv = g.bufferViews[a.bufferView]
    n = NK[a.type]; dt = TYP[a.componentType]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    st = bv.byteStride or n * np.dtype(dt).itemsize
    if st == n * np.dtype(dt).itemsize:
        return np.frombuffer(blob, dt, a.count * n, off).reshape(a.count, n) if n > 1 else np.frombuffer(blob, dt, a.count, off)
    raw = np.frombuffer(blob, np.uint8, st * a.count, off).reshape(a.count, st)[:, :n * np.dtype(dt).itemsize]
    return raw.copy().view(dt).reshape(a.count, n)

for f in sorted(glob.glob(os.path.join(d, "*.glb"))):
    if f.endswith(("_daleko.glb", "_lod1.glb")): continue
    g = GLTF2().load(f); blob = bytearray(g.binary_blob())
    pred = po = 0
    for m in g.meshes:
        for p in m.primitives:
            mat = g.materials[p.material] if p.material is not None else None
            jm = (mat.name or "").lower() if mat else ""
            idx = cti(g, blob, p.indices).astype(np.int64).reshape(-1, 3)
            pred += len(idx)
            if not (mat and (mat.alphaMode in ("MASK", "BLEND") or "list" in jm or "jehl" in jm)):
                po += len(idx); continue
            pos = cti(g, blob, p.attributes.POSITION).astype(np.float64)
            nv = len(pos)
            e = np.r_[idx[:, 0], idx[:, 1], idx[:, 2]]; e2 = np.r_[idx[:, 1], idx[:, 2], idx[:, 0]]
            ncomp, lab = connected_components(coo_matrix((np.ones(len(e)), (e, e2)), shape=(nv, nv)), directed=False)
            keep_c = rng.random(ncomp) < podil
            tri_c = lab[idx[:, 0]]
            nidx = idx[keep_c[tri_c]]
            # zvětšit ponechané karty kolem středu komponenty
            cnt = np.bincount(lab, minlength=ncomp).astype(np.float64)
            stred = np.stack([np.bincount(lab, pos[:, k], ncomp) for k in range(3)], 1) / cnt[:, None]
            npos = stred[lab] + (pos - stred[lab]) * zv
            # zapsat zpět do bufferu (stejná místa; indexy kratší -> count se zmenší)
            a = g.accessors[p.attributes.POSITION]; bv = g.bufferViews[a.bufferView]
            st = bv.byteStride or 12; off = (bv.byteOffset or 0) + (a.byteOffset or 0)
            for i in range(nv):
                struct.pack_into("<3f", blob, off + i * st, *npos[i])
            a.max = npos.max(0).tolist(); a.min = npos.min(0).tolist()
            ai = g.accessors[p.indices]; bvi = g.bufferViews[ai.bufferView]; offi = (bvi.byteOffset or 0) + (ai.byteOffset or 0)
            dt = TYP[ai.componentType]; data = nidx.astype(dt).ravel().tobytes()
            blob[offi:offi + len(data)] = data
            ai.count = int(nidx.size)
            po += len(nidx)
    g.set_binary_blob(bytes(blob))
    out = f[:-4] + "_lod1.glb"
    g.save_binary(out)
    # LOD1 nemá vlastní textury (hra mu dá materiály LOD0) – jinak by byly ve VRAM dvakrát (změřeno 29. 10.: 315 -> 1448 MB)
    if not os.path.exists(out + ".import"):
        open(out + ".import", "w").write('[remap]\n\nimporter="scene"\n\n[params]\n\ngltf/embedded_image_handling=0\n')
    print(os.path.basename(out), pred, "->", po)
