"""Mix ctyr zvuku mechanismu brany ze skutecnych nahravek BigSoundBank (CC0, viz zvuky/pohyb/LICENCE.txt):
retez.ogg (smycka 4 s), vrata_smycka.ogg (smycka 3 s), dopad_most.ogg, dopad_mriz.ogg.
Nahravky stahnout jako WAV do jednoho adresare pod cislem zvuku, napr.
  curl -o raw/0359.wav https://bigsoundbank.com/UPLOAD/bwf-en/0359.wav
cisla: 0223 0235 0306 0580 0619 0902 1022 1133 1134 1441 1501 1777 2359 2360
  python3 tools/mix_nahravky.py <adresar s WAV> zvuky/pohyb"""
import os, sys, subprocess
import numpy as np
from scipy import signal

SR = 44100


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

RAW, OUT = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(11)


def L(i, a=None, b=None):
    x = load(os.path.join(RAW, f"{i}.wav"))
    if a is not None:
        x = x[int(a * SR):int(b * SR)]
    return x


def pitch(x, k):
    """resample so playback is k times faster (k<1 = lower, slower, 'heavier')."""
    from fractions import Fraction
    fr = Fraction(k).limit_denominator(100)
    return signal.resample_poly(x, fr.denominator, fr.numerator).astype(np.float64)


def hp(x, f, o=4):
    return signal.sosfilt(signal.butter(o, f, "hp", fs=SR, output="sos"), x)


def lp(x, f, o=4):
    return signal.sosfilt(signal.butter(o, f, "lp", fs=SR, output="sos"), x)


def peq(x, f0, gain_db, q=0.8):
    # RBJ peaking EQ
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]; a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x)


def shelf_hi(x, f0, gain_db):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; al = np.sin(w) / 2 * np.sqrt(2)
    c = np.cos(w); s = 2 * np.sqrt(A) * al
    b = [A * ((A + 1) + (A - 1) * c + s), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - s)]
    a = [(A + 1) - (A - 1) * c + s, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - s]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x)


def norm(x, db=0.0):
    return x / (np.max(np.abs(x)) + 1e-12) * 10 ** (db / 20)


def rmsn(x, db):
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-12) * 10 ** (db / 20)


def add(buf, x, t, g=1.0):
    i = int(t * SR); n = min(len(x), len(buf) - i)
    if n > 0:
        buf[i:i + n] += x[:n] * g


def fade(x, fi, fo):
    x = x.copy(); a = int(fi * SR); b = int(fo * SR)
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b) ** 2
    return x


def limit(x, ceil_db=-1.0, drive_db=0.0, release=0.08):
    """simple look-ahead-free peak limiter: gain envelope from |x|, then hard ceiling."""
    x = x * 10 ** (drive_db / 20)
    c = 10 ** (ceil_db / 20)
    env = np.abs(x)
    # smooth peak hold with fast attack / slow release
    g = np.ones_like(x)
    r = np.exp(-1 / (release * SR))
    e = 0.0
    for i in range(len(x)):  # noqa  (short files, fine)
        v = env[i]
        e = v if v > e else e * r + v * (1 - r)
        g[i] = 1.0 if e <= c else c / e
    y = x * g
    return np.clip(y, -c, c)


def loopify(x, length, xf):
    """take length+xf samples; crossfade the tail beyond 'length' into the head (equal power)."""
    n = int(length * SR); f = int(xf * SR)
    x = x[:n + f].copy()
    t = np.linspace(0, np.pi / 2, f)
    head = x[:f] * np.sin(t) + x[n:n + f] * np.cos(t)
    y = x[:n].copy(); y[:f] = head
    return y


def save(name, x, q=6):
    path = os.path.join(OUT, name + ".ogg")
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "libvorbis", "-q:a", str(q), path], input=pcm, check=True)
    print("saved", path)


# ---------------------------------------------------------------- retez (loop 4 s)
LEN, XF = 4.0, 0.5
T = LEN + XF
N = int(T * SR)
# A: manual chain hoist (links running over sprocket), pitched down -> heavy links
a1 = pitch(L("1134", 3.0, 3.0 + T * 0.62 + 0.1), 0.62)[:N]
a2 = pitch(L("1133", 6.0, 6.0 + T * 0.5 + 0.1), 0.5)[:N]
# B: manual winch crank (pawl/drum clicks), pitched down
b1 = pitch(L("0902", 2.0, 2.0 + T * 0.7 + 0.1), 0.7)[:N]
# C: heavy chain handling clanks scattered, pitched down
chain = L("0619")
cl = []
# pick loud onsets in medium chain
e = np.array([np.sqrt(np.mean(chain[i:i + 2205] ** 2)) for i in range(0, len(chain) - 2205, 2205)])
idx = np.argsort(e)[::-1][:40]
for k in idx[:14]:
    s = max(0, k * 2205 - 300)
    cl.append(chain[s:s + int(0.35 * SR)])
c1 = np.zeros(N)
t = 0.05
while t < T - 0.2:
    seg = pitch(cl[rng.integers(len(cl))], rng.uniform(0.5, 0.62))
    add(c1, fade(seg, 0.002, 0.08), t, rng.uniform(0.5, 1.0))
    t += rng.uniform(0.16, 0.34)
# D: wooden drum friction / load (stone-on-wood slide recording), low level body
d1 = pitch(L("0580", 4.6, 4.6 + T * 0.8 + 0.1), 0.8)[:N]

mix = (rmsn(a1, -20) + rmsn(a2, -23) + rmsn(b1, -24) + rmsn(c1, -21) + rmsn(d1, -27))
mix = hp(mix, 60)
mix = lp(mix, 5000, 4)          # dull, not glassy
mix = peq(mix, 7300, -10, 3)
mix = peq(mix, 900, 4, 0.7)     # body of the links on small speakers
mix = peq(mix, 250, 3, 0.9)     # heaviness that still survives a small speaker
mix = peq(mix, 3200, -3, 1.0)   # tame ringing
mix = loopify(mix, LEN, XF)
mix = norm(mix, 0)
# gentle limiting to raise loudness, but avoid limiter pumping across the loop seam: process 3 copies, keep middle
tri = np.concatenate([mix, mix, mix])
tri = limit(tri, -1.3, 5.0, 0.05)
retez = tri[len(mix):2 * len(mix)]
save("retez", retez)

# ---------------------------------------------------------------- vrata_smycka (loop 3 s)
LEN, XF = 3.0, 0.4
T = LEN + XF; N = int(T * SR)
cr = pitch(L("0306", 0.4, 0.4 + T * 0.6 + 0.1), 0.6)[:N]          # long door creak, lowered -> heavy gate
cr2 = pitch(L("0306", 2.6, 2.6 + T * 0.52 + 0.1), 0.52)[:N]
body = pitch(L("0580", 0.25, 0.25 + T * 0.85 + 0.1), 0.85)[:N]     # heavy wooden/stone friction body
mix = rmsn(hp(cr, 150), -20) + rmsn(hp(cr2, 150), -24) + rmsn(body, -23)
mix = hp(mix, 60); mix = lp(mix, 7000, 2); mix = peq(mix, 600, 3, 0.8)
mix = loopify(mix, LEN, XF)
mix = norm(mix, 0)
tri = np.concatenate([mix, mix, mix]); tri = limit(tri, -1.3, 4.0, 0.05)
save("vrata_smycka", tri[len(mix):2 * len(mix)])

# ---------------------------------------------------------------- dopad_most (~2.2 s)
DUR = 1.8; N = int(DUR * SR)
buf = np.zeros(N)
slam = pitch(L("0223", 0.0, 0.9), 0.72)                 # wooden door slam, lowered -> big wooden leaf
add(buf, rmsn(slam, -12), 0.0)
slam2 = pitch(L("0223", 1.0, 1.7), 0.6)                  # second slam layered for weight / bounce
add(buf, rmsn(slam2, -16), 0.012)
logs = L("1441", 76.05, 77.1)                            # logs crashing out of a truck = wooden crash texture
add(buf, fade(rmsn(logs, -17), 0.004, 0.5), 0.005)
barrier = L("2360", 0.0, 1.6)                            # big barn barrier slam (low-mid thump)
add(buf, fade(rmsn(barrier, -19), 0.0, 0.5), 0.0)
bounce = pitch(L("1501", 0.0, 0.6), 0.75)                # small rebound knock
add(buf, rmsn(bounce, -22), 0.33)
# short chain rattle after impact (chains go slack)
t = 0.08
for k in range(9):
    seg = pitch(cl[rng.integers(len(cl))], rng.uniform(0.55, 0.7))
    add(buf, fade(seg, 0.002, 0.07), t, 0.12 * np.exp(-k / 4))
    t += rng.uniform(0.07, 0.15)
x = hp(buf, 60, 4)
x = peq(x, 120, -3, 0.8)        # less sub/boom that small speakers can't play anyway
x = peq(x, 450, 5, 0.7)         # wood body
x = peq(x, 1500, 4, 0.8)        # crack / presence
x = lp(x, 9000, 2)
x = fade(x, 0.0, 0.5)
x = limit(norm(x, 0), -1.3, 7.0, 0.06)
x = norm(x, -1.3)
save("dopad_most", x)

# ---------------------------------------------------------------- dopad_mriz (~1.8 s)
DUR = 1.7; N = int(DUR * SR)
buf = np.zeros(N)
iron = L("2359", 0.2, 0.95)                                # metal barrier slam (iron clank)
add(buf, fade(rmsn(pitch(iron, 0.8), -15), 0.0, 0.55), 0.0)
add(buf, fade(rmsn(pitch(L("2359", 0.95, 1.6), 0.8), -29), 0.005, 0.3), 0.92)  # small rebound
bars = L("1777", 0.0, 1.2)                                # steel bars falling on a path (metal on ground)
add(buf, fade(rmsn(pitch(bars, 0.75)[:int(0.5 * SR)], -17), 0.0, 0.35), 0.004)
wood = pitch(L("0223", 0.0, 0.8), 0.65)                   # wooden body of the grate
add(buf, rmsn(wood, -15), 0.0)
stone = L("1022")
# loudest stone impact as stone/grit layer
es = np.array([np.max(np.abs(stone[i:i + 4410])) for i in range(0, len(stone) - 4410, 4410)])
k = int(np.argmax(es)) * 4410
add(buf, fade(rmsn(stone[max(0, k - 200):k + int(0.6 * SR)], -21), 0.002, 0.3), 0.003)
ib = L("0235", 0.0, 1.1)                                  # iron bar falls: bright iron clank, lowered + damped
add(buf, fade(rmsn(lp(pitch(ib, 0.7), 3500)[:int(0.35 * SR)], -22), 0.0, 0.3), 0.02)
t = 0.06
for k2 in range(7):
    seg = pitch(cl[rng.integers(len(cl))], rng.uniform(0.6, 0.75))
    add(buf, fade(seg, 0.002, 0.06), t, 0.10 * np.exp(-k2 / 3))
    t += rng.uniform(0.06, 0.13)
x = hp(buf, 60, 4)
x = peq(x, 120, -3, 0.8)
x = peq(x, 500, 4, 0.7)
x = peq(x, 1800, 3, 0.8)
for fq, g in ((659, -10), (963, -14), (1870, -14), (2327, -14), (3035, -14)):
    x = peq(x, fq, g, fq / 25)          # damp the ringing modes of the metal barrier so it does not read as a bell
x = lp(x, 10000, 2)
x = fade(x, 0.0, 0.45)
x = limit(norm(x, 0), -1.3, 9.0, 0.06)
x = norm(x, -1.3)
save("dopad_mriz", x)
