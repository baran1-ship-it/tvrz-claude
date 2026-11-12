import os, re, struct, glob, sys
R = '/home/user/tvrz-claude'
# 1) chybejici dest soubory z .import (binarne)
need = set()
for root, dirs, files in os.walk(R):
    if '/.git' in root or '/.godot' in root: continue
    for f in files:
        if f.endswith('.import'):
            b = open(os.path.join(root, f), 'rb').read()
            for m in re.finditer(rb'res://\.godot/imported/[^"\]]+', b):
                p = m.group(0).decode('utf8', 'replace')
                if not os.path.exists(os.path.join(R, p[6:])):
                    need.add(p)
import shutil
existuje = set(os.listdir(R + '/.godot/imported'))
def ma_variantu(p):
    jm = p.rsplit('/', 1)[1]
    if not jm.endswith('.ctex'): return False
    base = jm.rsplit('.', 2)[0]
    return any(e.startswith(base + '.') for e in existuje)
need = {p for p in need if not ma_variantu(p) and not p.endswith('.etc2.ctex')}
print('chybi', len(need))
# 2) virtualni soubor pres casti baliku
class Casti:
    def __init__(self, parts):
        self.parts = parts; self.sizes = [os.path.getsize(p) for p in parts]; self.pos = 0
    def seek(self, o): self.pos = o
    def read(self, n):
        out = b''; o = self.pos
        while n > 0:
            acc = 0
            for p, s in zip(self.parts, self.sizes):
                if o < acc + s:
                    with open(p, 'rb') as fh:
                        fh.seek(o - acc); d = fh.read(min(n, acc + s - o))
                    out += d; o += len(d); n -= len(d); break
                acc += s
            else: break
        self.pos = o; return out
packs = {}
for f in sorted(glob.glob(R + '/data/*.pck.*')):
    packs.setdefault(re.sub(r'\.\d{3}$', '', f), []).append(f)
obnoveno = 0
for base, parts in packs.items():
    v = Casti(sorted(parts))
    v.seek(0)
    if v.read(4) != b'GDPC': continue
    fmt, maj, mi, pat = struct.unpack('<4I', v.read(16))
    flags = 0; files_base = 0
    if fmt >= 2:
        flags, files_base = struct.unpack('<IQ', v.read(12))
    if fmt >= 3:
        dir_ofs = struct.unpack('<Q', v.read(8))[0]
        v.seek(dir_ofs)
    else:
        v.read(16 * 4)
    n = struct.unpack('<I', v.read(4))[0]
    for i in range(n):
        ln = struct.unpack('<I', v.read(4))[0]
        path = v.read(ln).rstrip(b'\0').decode('utf8', 'replace')
        ofs, size = struct.unpack('<QQ', v.read(16)); v.read(16)
        if fmt >= 2: v.read(4)
        p = path if path.startswith('res://') else 'res://' + path
        if p in need and shutil.disk_usage(R).free < 900e6:
            print('STOP malo mista'); break
        if p in need:
            here = v.pos
            v.seek(files_base + ofs); data = v.read(size); v.seek(here)
            out = os.path.join(R, p[6:]); os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'wb').write(data); need.discard(p); obnoveno += 1
print('obnoveno', obnoveno, 'zbyva', len(need))
for p in sorted(need)[:15]: print('  ', p)
