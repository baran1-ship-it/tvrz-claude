#!/usr/bin/env python3
"""Zvuky pro Tvrz: vse synteza (sum, sinusy), zadne nahravky. Smycky jsou periodicke, takze navazuji."""
import os
import wave
import numpy as np

SR = 22050
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)


def save(name, x, peak=0.7, fade=True):
    x = np.asarray(x, dtype=np.float64)
    if fade:
        n = min(len(x) // 4, int(SR * 0.012))
        x[:n] *= np.linspace(0, 1, n)
        x[-n:] *= np.linspace(1, 0, n)
    m = np.max(np.abs(x))
    if m > 0:
        x = x / m * peak
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    print("  %-12s %.2fs" % (name, len(x) / SR))


def band(n, lo, hi, slope=0.0, seed=None):
    """Periodicky sum v pasmu lo..hi Hz, slope = sklon spektra v dB/okt (zaporny = temnejsi)."""
    r = np.random.default_rng(seed) if seed is not None else rng
    f = np.fft.rfft(r.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    amp = np.ones_like(fr)
    amp[fr < lo] = 0
    amp[fr > hi] = 0
    nz = fr > 0
    amp[nz] *= (fr[nz] / 1000.0) ** (slope / 6.0)
    x = np.fft.irfft(f * amp, n)
    return x / (np.max(np.abs(x)) + 1e-9)


def slow(n, hz, seed):
    """Pomala periodicka obalka 0..1."""
    x = band(n, 0.01, hz, 0, seed)
    x = (x - x.min()) / (x.max() - x.min())
    return x


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, attack, decay):
    tt = np.arange(n) / SR
    return np.minimum(tt / max(attack, 1e-4), 1.0) * np.exp(-tt * decay)


# ---- smycky
n = SR * 10
wind = band(n, 60, 900, -5, 1) * (0.35 + 0.65 * slow(n, 0.35, 2)) + 0.5 * band(n, 300, 2600, -8, 3) * slow(n, 0.6, 4) ** 2
save("wind", wind, 0.55, False)

n = SR * 12
birds = np.zeros(n)
r2 = np.random.default_rng(21)
for i in range(34):
    start = r2.integers(0, n)
    kind = r2.integers(0, 3)
    notes = r2.integers(2, 7)
    f0 = r2.uniform(2400, 5200)
    vol = r2.uniform(0.15, 1.0) ** 2
    pos = start
    for k in range(notes):
        d = r2.uniform(0.05, 0.14)
        m = int(SR * d)
        tt = np.arange(m) / SR
        if kind == 0:
            fr = f0 * (1 + 0.25 * np.sin(2 * np.pi * r2.uniform(12, 30) * tt))
        elif kind == 1:
            fr = f0 * (1 + r2.uniform(-0.3, 0.3) * tt / d)
        else:
            fr = f0 * (1.15 - 0.3 * (tt / d) ** 2)
        note = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.sin(np.pi * tt / d) ** 2 * vol
        idx = (pos + np.arange(m)) % n
        birds[idx] += note
        pos += m + int(SR * r2.uniform(0.02, 0.12))
        f0 *= r2.uniform(0.9, 1.12)
save("birds", birds + 0.02 * band(n, 200, 3000, -6, 5), 0.4, False)

n = SR * 12
cr = np.zeros(n)
r3 = np.random.default_rng(33)
# cvrcci: kratke cvrknuti (3-4 pulzy po 12 ms), opakovane nepravidelne, kazdy jinak daleko
for c in range(5):
    f0 = r3.uniform(3900, 4800)
    vol = r3.uniform(0.15, 0.6)
    pos = int(r3.uniform(0, SR))
    while pos < n:
        for p_ in range(r3.integers(2, 5)):
            m = int(SR * 0.012)
            tt = np.arange(m) / SR
            note = np.sin(2 * np.pi * f0 * tt) * np.sin(np.pi * tt / 0.012) ** 2 * vol
            idx = (pos + np.arange(m)) % n
            cr[idx] += note
            pos += int(SR * 0.028)
        pos += int(SR * r3.uniform(0.45, 1.4))
save("night", cr * 0.5 + 0.12 * band(n, 80, 500, -6, 7), 0.22, False)

n = SR * 6
fire = band(n, 90, 1600, -7, 31) * (0.5 + 0.5 * slow(n, 3.0, 32))
r3 = np.random.default_rng(33)
for i in range(70):
    p = r3.integers(0, n)
    m = int(SR * r3.uniform(0.004, 0.03))
    click = r3.standard_normal(m) * np.exp(-np.arange(m) / (m * 0.25)) * r3.uniform(0.3, 1.6)
    fire[(p + np.arange(m)) % n] += click
save("fire", fire, 0.6, False)

# ---- kroky
for name, lo, hi, slope, dec in (("step_stone", 180, 3200, -3, 34), ("step_wood", 90, 1400, -6, 22), ("step_grass", 500, 5000, -2, 26)):
    for k in range(3):
        m = int(SR * 0.22)
        x = band(m, lo, hi, slope) * env(m, 0.004, dec)
        if name == "step_wood":
            x += 0.8 * np.sin(2 * np.pi * (95 + 12 * k) * t(0.22)) * env(m, 0.003, 28)
        if name == "step_stone":
            x += 0.4 * band(m, 1500, 6000, 0) * env(m, 0.001, 90)
        save("%s%d" % (name, k + 1), x, 0.5)

# ---- luk
m = int(SR * 0.9)
tt = np.arange(m) / SR
creak = np.sin(2 * np.pi * np.cumsum(140 + 60 * tt + 25 * np.sin(2 * np.pi * 9 * tt)) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * (22 + 18 * tt) * tt)))
save("bow_draw", creak * np.sin(np.pi * tt / tt[-1]) ** 0.7 * 0.6 + 0.3 * band(m, 400, 2500, -4) * np.sin(np.pi * tt / tt[-1]), 0.35)
m = int(SR * 0.45)
tt = np.arange(m) / SR
twang = np.sin(2 * np.pi * np.cumsum(190 * np.exp(-tt * 3) + 80) / SR) * np.exp(-tt * 11) + 0.9 * band(m, 600, 6000, -2) * np.exp(-tt * 28)
save("bow_shot", twang, 0.7)
m = int(SR * 0.3)
tt = np.arange(m) / SR
save("hit_target", band(m, 150, 1800, -5) * np.exp(-tt * 26) + 0.8 * np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 30), 0.75)
save("hit_wood", band(m, 300, 4200, -3) * np.exp(-tt * 34) + 0.7 * np.sin(2 * np.pi * 260 * tt) * np.exp(-tt * 40), 0.7)

# ---- kovadlina
for k, base in enumerate((2150.0, 2480.0)):
    m = int(SR * 1.1)
    tt = np.arange(m) / SR
    x = np.zeros(m)
    for mult, dec, a in ((1.0, 4.5, 1.0), (2.41, 6.5, 0.6), (3.87, 9.0, 0.4), (5.3, 12.0, 0.25), (0.52, 8.0, 0.3)):
        x += a * np.sin(2 * np.pi * base * mult * tt + mult) * np.exp(-tt * dec)
    x += 1.2 * band(m, 800, 8000, 0) * np.exp(-tt * 70)
    save("anvil%d" % (k + 1), x, 0.7)

# ---- ostatni
m = int(SR * 0.5)
tt = np.arange(m) / SR
save("whoosh", band(m, 300, 3000, -3) * np.sin(np.pi * tt / tt[-1]) ** 2, 0.4)
m = int(SR * 0.09)
tt = np.arange(m) / SR
save("click", np.sin(2 * np.pi * 900 * tt) * np.exp(-tt * 60), 0.35)
m = int(SR * 1.6)
tt = np.arange(m) / SR
bell = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in ((392, 1.0, 2.2), (587, 0.6, 2.8), (784, 0.4, 3.4)))
save("chime", bell, 0.4)
