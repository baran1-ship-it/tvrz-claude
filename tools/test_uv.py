#!/usr/bin/env python3
"""Hlidac UV (Misa 0.996 snimek ves_let: strechy stodol a kulen jedna barva - UV strechy v druhe vrstve, TEXCOORD_0 v bode).
Kazda cast modelu s texturou musi mit TEXCOORD_0 s rozsahem (ne vsechny vrcholy v jednom bode).
Pouziti: python3 tools/test_uv.py [soubory.glb ...]  (bez argumentu modely/**/*.glb)"""
import glob, json, struct, sys
import numpy as np


def kontrola(cesta):
    f = open(cesta, 'rb').read()
    if f[:4] != b'glTF':
        return []
    n = struct.unpack('<I', f[12:16])[0]
    j = json.loads(f[20:20 + n])
    b0 = 20 + n + 8
    mats = j.get('materials', [])
    chyby = []
    for me in j.get('meshes', []):
        for p in me['primitives']:
            m = p.get('material')
            if m is None or 'baseColorTexture' not in mats[m].get('pbrMetallicRoughness', {}):
                continue
            ai = p['attributes'].get('TEXCOORD_0')
            if ai is None:
                chyby.append('%s: %s/%s bez UV' % (cesta, me.get('name'), mats[m].get('name')))
                continue
            a = j['accessors'][ai]
            if 'bufferView' not in a or a['componentType'] != 5126:
                continue
            bv = j['bufferViews'][a['bufferView']]
            o = b0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            st = bv.get('byteStride', 8)
            uv = np.frombuffer(f[o:o + (a['count'] - 1) * st + 8], dtype=np.uint8)
            uv = np.lib.stride_tricks.as_strided(uv.view(np.float32), shape=(a['count'], 2), strides=(st, 4))
            if a['count'] > 3 and float(np.ptp(uv, axis=0).max()) < 1e-4:
                chyby.append('%s: %s/%s UV v jednom bode (%d vrcholu)' % (cesta, me.get('name'), mats[m].get('name'), a['count']))
    return chyby


if __name__ == '__main__':
    sb = sys.argv[1:] or sorted(glob.glob('modely/**/*.glb', recursive=True))
    vse = []
    for s in sb:
        try:
            vse += kontrola(s)
        except Exception as e:
            print('UV preskoceno %s: %s' % (s, e))
    for c in vse:
        print('UV CHYBA', c)
    print('TEST UV %s  %d modelu, %d chyb' % ('OK' if not vse else 'CHYBA', len(sb), len(vse)))
    sys.exit(1 if vse else 0)
