"""Slozene zvuky mechanismu brany z Kenney Impact Sounds (CC0): rachot retezu pri navijeni (smycka),
tezky dopad padaciho mostu a zelezne mrize (vrstveny uder, hluboke duneni, odskok, dozvuk).
  python3 tools/gen_zvuky.py <adresar s Kenney Audio>"""
import os
import subprocess
import sys

import numpy as np

SR = 44100
SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "zvuky", "pohyb")
rng = np.random.default_rng(7)


def load(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(SRC, name + ".ogg"), "-f", "f32le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def pitch(x, k):
    # zmena vysky resamplingem (k < 1 = nizsi a delsi)
    n = int(len(x) / k)
    return np.interp(np.arange(n) * k, np.arange(len(x)), x)


def add(buf, x, t, g=1.0):
    i = int(t * SR)
    n = min(len(x), len(buf) - i)
    if n > 0:
        buf[i:i + n] += x[:n] * g


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s
        y[i] = s
    return y


def thump(dur, f0, f1, g):
    t = np.arange(int(dur * SR)) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 4.5) * g


def reverb(x, tail=1.6, wet=0.35):
    # jednoduchy dozvuk: rozptylene zpozdene kopie s dolni propusti (kamenny pruchod brany)
    n = len(x) + int(tail * SR)
    y = np.zeros(n)
    y[:len(x)] += x
    lp = lowpass(x, 1800)
    for k in range(28):
        d = rng.uniform(0.02, tail * 0.8)
        g = wet * np.exp(-d * 3.2 / tail) * rng.uniform(0.5, 1.0) * (1 if k % 2 else -1)
        add(y, lp, d, g)
    return y


def save(name, x, norm=0.95):
    x = x / (np.max(np.abs(x)) + 1e-9) * norm
    wav = os.path.join(OUT, name + ".wav")
    import wave
    with wave.open(wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "6",
                    os.path.join(OUT, name + ".ogg")], check=True)
    os.remove(wav)
    print(name, round(len(x) / SR, 2), "s")


def fade(x, a=0.01, b=0.05):
    na, nb = int(a * SR), int(b * SR)
    x[:na] *= np.linspace(0, 1, na)
    x[-nb:] *= np.linspace(1, 0, nb)
    return x


# --- retez: smycka 3 s, husty rachot clanku pres buben a zub rohatky
clinks = [load("impactMetal_light_%03d" % i) for i in range(5)] + [load("impactPlate_light_%03d" % i) for i in range(5)]
L = 3.0
buf = np.zeros(int(L * SR) + SR)
t = 0.0
while t < L:
    c = clinks[rng.integers(len(clinks))]
    add(buf, pitch(c, rng.uniform(0.55, 1.0)), t, rng.uniform(0.25, 0.7))
    t += rng.exponential(1 / 34.0)
# kazdy ~0.35 s tezsi cvak clanku pres hranu bubnu
for k in range(int(L / 0.36)):
    add(buf, pitch(load("impactMetal_medium_%03d" % (k % 5)), rng.uniform(0.5, 0.6)), k * 0.36 + rng.uniform(0, 0.03), 0.6)
# smycka: konec preklopit do zacatku
x = buf[:int(L * SR)].copy()
tail = buf[int(L * SR):int(L * SR) + int(0.3 * SR)]
x[:len(tail)] += tail
save("retez", x, 0.9)

# --- tezky dreveny most dopadl na kraj prikopu: uder, duneni, odskok, drnceni retezu, dozvuk
w = [load("impactWood_heavy_%03d" % i) for i in range(5)]
buf = np.zeros(int(3.0 * SR))
add(buf, pitch(w[0], 0.42), 0.0, 1.0)
add(buf, pitch(w[2], 0.55), 0.008, 0.8)
add(buf, pitch(load("impactPunch_heavy_001"), 0.5), 0.0, 0.7)
add(buf, thump(1.4, 95, 38, 1.1), 0.0)
add(buf, pitch(w[3], 0.5), 0.22, 0.35)          # odskok
add(buf, thump(0.6, 70, 40, 0.35), 0.22)
for k in range(14):                              # drnceni retezu po dopadu
    add(buf, pitch(clinks[k % len(clinks)], rng.uniform(0.6, 0.9)), 0.05 + k * 0.045 + rng.uniform(0, 0.02), 0.25 * (1 - k / 14))
save("dopad_most", fade(reverb(buf, 1.8, 0.4), 0.0, 0.3))

# --- zelezna mriz dosedla na dlazbu: kovovy tresk, zvoneni mrize, duneni
buf = np.zeros(int(3.0 * SR))
add(buf, pitch(load("impactMetal_heavy_000"), 0.55), 0.0, 1.0)
add(buf, pitch(load("impactMetal_heavy_003"), 0.7), 0.006, 0.7)
add(buf, pitch(load("impactBell_heavy_002"), 0.45), 0.0, 0.35)
add(buf, pitch(load("impactMining_001"), 0.6), 0.0, 0.6)          # hroty o kamen
add(buf, thump(1.2, 85, 42, 0.9), 0.0)
add(buf, pitch(load("impactMetal_medium_002"), 0.6), 0.16, 0.4)  # odskok
for k in range(10):
    add(buf, pitch(clinks[k % len(clinks)], rng.uniform(0.7, 1.0)), 0.04 + k * 0.05, 0.22 * (1 - k / 10))
save("dopad_mriz", fade(reverb(buf, 1.8, 0.4), 0.0, 0.3))
