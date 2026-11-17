#!/usr/bin/env python3
"""Original slow dark pad, Hijaz on E, no drums, no copyrighted material.
Chords move slowly under the voice; each chord crossfades into the next."""
import numpy as np, wave, os

BASE = os.path.expanduser("~/workspace/bayt-wa-hikaya/mutanabbi-video")
SR = 44100
DUR = 117.5
N = int(SR * DUR)

# Hijaz on E: E F G# A B C D#
# chord roots/notes (Hz) — slow pad chords, each ~14.7s
CHORDS = [
    [82.41, 123.47, 164.81, 196.00],   # Em  (E B E G)
    [87.31, 130.81, 174.61, 220.00],   # F   (F C F A)
    [103.83, 155.56, 207.65, 246.94],  # G#  (G# D# G# B)
    [110.00, 164.81, 220.00, 261.63],  # Am  (A E A C)
    [82.41, 123.47, 164.81, 207.65],   # Em  (E B E G#) — brighter turn
    [87.31, 130.81, 174.61, 220.00],   # F
    [110.00, 164.81, 220.00, 277.18],  # Am  (A E A C#) — lift for the verses
    [82.41, 123.47, 164.81, 196.00],   # Em  — return home for the end
]
CHORD_DUR = DUR / len(CHORDS)

t = np.arange(N) / SR
out = np.zeros(N)
rng = np.random.default_rng(7)
for ci, notes in enumerate(CHORDS):
    start = int(ci * CHORD_DUR * SR)
    end = int(min((ci + 1) * CHORD_DUR, DUR) * SR)
    seg = np.zeros(end - start)
    tt = np.arange(end - start) / SR
    for ni, f in enumerate(notes):
        det = 1.0 + rng.normal(0, 0.0006)
        # fundamental + soft harmonics, slow swell per note
        sig = (np.sin(2 * np.pi * f * det * tt)
               + 0.4 * np.sin(2 * np.pi * f * 2 * det * tt)
               + 0.18 * np.sin(2 * np.pi * f * 3 * det * tt))
        swell = 0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * tt + ni * 1.3)
        seg += sig * swell / len(notes)
    # 3s raised-cosine fades at both ends for crossfading
    fade = int(3.0 * SR)
    win = np.ones(len(seg))
    win[:fade] = 0.5 - 0.5 * np.cos(np.pi * np.arange(fade) / fade)
    win[-fade:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(fade) / fade)
    out[start:end] += seg * win

# gentle low drone under everything
out += 0.25 * np.sin(2 * np.pi * 41.20 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.05 * t))
# overall fade out in the last 3s
fade = int(3.0 * SR)
out[-fade:] *= np.linspace(1, 0, fade)
# normalise music to a low level: peak -12 dBFS, then the mix sets it well under the voice
peak = np.max(np.abs(out))
out = out / peak * 10 ** (-12 / 20)
stereo = np.stack([out, out], axis=1)
pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
with wave.open(f"{BASE}/build/music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("music.wav written", len(pcm) / SR, "s, peak dBFS", 20 * np.log10(np.max(np.abs(out))))
