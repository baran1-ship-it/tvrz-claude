"""Zvuk myti v kadi: nabrani vody do dlani, splouchnuti do obliceje, odkapavani (kapky = kratke stoupajici tony bublin).
  python3 tools/gen_voda.py"""
import os
import subprocess
import wave

import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "zvuky", "predmety")
rng = np.random.default_rng(3)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s
        y[i] = s
    return y


def band(x, lo, hi):
    return lowpass(x, hi) - lowpass(x, lo)


def add(buf, x, t, g=1.0):
    i = int(t * SR)
    n = min(len(x), len(buf) - i)
    if n > 0:
        buf[i:i + n] += x[:n] * g


def slosh(dur, att, lo, hi):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / att) * np.exp(-t * 5 / dur)
    # vodni sum je "zrnity": modulace rychlym nahodnym obalem
    grain = np.repeat(rng.uniform(0.3, 1.0, len(t) // 220 + 1), 220)[:len(t)]
    return band(rng.normal(0, 1, len(t)), lo, hi) * env * grain


def drop(f0):
    t = np.arange(int(0.05 * SR)) / SR
    f = f0 * (1 + 2.2 * t / 0.05)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 70)


buf = np.zeros(int(3.2 * SR))
add(buf, slosh(0.5, 0.15, 200, 1800), 0.0, 0.7)        # nabrani vody
add(buf, slosh(0.35, 0.01, 400, 4000), 0.65, 1.0)      # splouchnuti do obliceje
add(buf, slosh(0.4, 0.05, 200, 1500), 1.1, 0.5)
add(buf, slosh(0.3, 0.01, 400, 3500), 1.5, 0.8)
for k in range(26):
    add(buf, drop(rng.uniform(700, 1700)), 0.75 + rng.exponential(0.6), rng.uniform(0.15, 0.4))
t = np.arange(len(buf)) / SR
buf *= np.minimum(1, (3.2 - t) / 0.4)
buf = buf / np.max(np.abs(buf)) * 0.9
wav = os.path.join(OUT, "myti.wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "6", os.path.join(OUT, "myti.ogg")], check=True)
os.remove(wav)
print("myti", len(buf) / SR)
