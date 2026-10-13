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


# --- retez: smycka 3 s; tezke clanky (kov pres hranu bubnu, nizko a tlumene, ne zvonive), skripot bubnu a duneni
heavy = [load("impactMetal_heavy_%03d" % i) for i in range(5)] + [load("impactMetal_medium_%03d" % i) for i in range(5)]
mining = [load("impactMining_%03d" % i) for i in range(5)]
creak = [load("impactWood_light_%03d" % i) for i in range(5)]
L = 3.0
buf = np.zeros(int(L * SR) + SR)
t = 0.0
while t < L:
    c = heavy[rng.integers(len(heavy))]
    add(buf, pitch(c, rng.uniform(0.32, 0.5)), t, rng.uniform(0.25, 0.55))
    if rng.random() < 0.5:
        add(buf, pitch(mining[rng.integers(5)], rng.uniform(0.45, 0.65)), t + 0.01, 0.3)
    t += rng.uniform(0.07, 0.13)
# kazdy zub rohatky / clanek pres buben tezsi raz
for k in range(int(L / 0.42)):
    add(buf, pitch(heavy[k % 5], 0.3), k * 0.42, 0.8)
    add(buf, pitch(creak[k % 5], 0.45), k * 0.42 + 0.05, 0.35)
# hluboke duneni bubnu a hrideli (filtrovany sum)
nz = rng.normal(0, 1, len(buf))
buf += lowpass(lowpass(nz, 120), 120) * 1.5
buf = lowpass(buf, 2600)
x = buf[:int(L * SR)].copy()
tail = buf[int(L * SR):int(L * SR) + int(0.3 * SR)]
x[:len(tail)] += tail
save("retez", x, 0.9)

# --- vrata: tezke drevene kridlo na zelezne ose, smycka skripani a duneni (3 s)
buf = np.zeros(int(3.0 * SR) + SR)
v = [load("impactWood_heavy_%03d" % i) for i in range(5)]
t = 0.0
while t < 3.0:
    add(buf, pitch(creak[rng.integers(5)], rng.uniform(0.25, 0.35)), t, rng.uniform(0.3, 0.6))
    t += rng.uniform(0.05, 0.11)
for k in range(6):
    add(buf, pitch(v[k % 5], 0.35), k * 0.5 + rng.uniform(0, 0.1), 0.3)
nz = rng.normal(0, 1, len(buf))
buf += lowpass(lowpass(nz, 90), 90) * 1.2
buf = lowpass(buf, 1800)
x = buf[:int(3.0 * SR)].copy()
x[:int(0.3 * SR)] += buf[int(3.0 * SR):int(3.3 * SR)]
save("vrata_smycka", x, 0.85)

clinks = heavy
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

# --- zaby (skokan): kratke "kvak" = sled harmonickych pulzu s formantem, nekolik variant
OUTZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "zvuky", "zaby")
os.makedirs(OUTZ, exist_ok=True)
OUT = OUTZ


def croak(f0, pulses, rate, formant, dur):
    t = np.arange(int(dur * SR)) / SR
    env = np.zeros_like(t)
    for k in range(pulses):
        c = k / rate
        env += np.exp(-((t - c - 0.012) / 0.006) ** 2)
    sig = np.zeros_like(t)
    for h in range(1, 14):
        sig += np.sin(2 * np.pi * f0 * h * t + rng.uniform(0, 6)) * np.exp(-((f0 * h - formant) / 500.0) ** 2)
    sig += rng.normal(0, 0.15, len(t))
    out = lowpass(sig * env, 3000) * np.minimum(1, t * 40)
    return out


for v, (f0, pul, rate, form, n) in enumerate(((180, 7, 70, 900, 2), (230, 5, 90, 1200, 3), (150, 9, 60, 700, 1), (260, 4, 100, 1400, 4))):
    buf = np.zeros(int(2.5 * SR))
    t = 0.02
    for k in range(n):
        c = croak(f0 * rng.uniform(0.95, 1.05), pul, rate, form, pul / rate + 0.05)
        add(buf, c, t, rng.uniform(0.7, 1.0))
        t += pul / rate + rng.uniform(0.12, 0.3)
    x = buf[:int((t + 0.2) * SR)]
    save("kvak%d" % (v + 1), fade(reverb(x, 0.6, 0.15), 0.002, 0.1), 0.8)
