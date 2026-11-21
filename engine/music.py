#!/usr/bin/env python3
"""Generate a light, upbeat royalty-free background loop (pure synthesis, no samples).

Usage:  python3 engine/music.py <seconds> out.wav [--bpm 112] [--seed 0]
The track is made to sit UNDER the voice: soft pads, pluck arpeggio, round bass, light drums.
"""
import sys, wave
import numpy as np

SR = 44100


def note(m):  # MIDI -> Hz
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, a):  # one-pole low-pass, a in (0,1): smaller = darker
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc); y[i] = acc
    return y


def adsr(n, a, d, s, r):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e = np.full(n, s, np.float32)
    e[:a] = np.linspace(0, 1, a, endpoint=False) if a else 1
    e[a:a + d] = np.linspace(1, s, len(e[a:a + d]))
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for dt in (-detune, 0.0, detune):
        ph = (t * f * (1 + dt)) % 1.0
        out += (2 * ph - 1).astype(np.float32)
    return out / 3


def sine(f, n):
    return np.sin(2 * np.pi * f * np.arange(n) / SR).astype(np.float32)


def make(seconds, bpm=112, seed=0):
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    bar = 4 * beat
    N = int(seconds * SR)
    pad = np.zeros(N, np.float32); arp = np.zeros(N, np.float32)
    bass = np.zeros(N, np.float32); drums = np.zeros(N, np.float32)
    # Am - F - C - G  (bright, "positive" pop progression)
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    roots = [45, 41, 48, 43]
    nbars = int(np.ceil(seconds / bar))
    for b in range(nbars):
        c = chords[b % 4]; r = roots[b % 4]
        s0 = int(b * bar * SR); n = int(bar * SR)
        seg = slice(s0, min(N, s0 + n)); L = seg.stop - seg.start
        if L <= 0:
            break
        # pad
        p = sum(saw(note(m + 12), n, 0.004) for m in c) / 3
        p = lp(p, 0.06) * adsr(n, 0.25, 0.3, 0.8, 0.3)
        pad[seg] += p[:L] * 0.5
        # bass: root on 1, octave on the "and" of 2, root on 3
        for at, m, ln in ((0, r, 1.4), (1.5, r + 12, 0.45), (2, r, 1.4), (3.5, r + 7, 0.45)):
            i0 = s0 + int(at * beat * SR); k = int(ln * beat * SR)
            if i0 >= N:
                continue
            x = (sine(note(m), k) + 0.25 * sine(note(m) * 2, k)) * adsr(k, 0.005, 0.15, 0.6, 0.08)
            bass[i0:i0 + k] += x[:N - i0] * 0.55
        # pluck arpeggio in 8ths
        pattern = [0, 1, 2, 1, 0, 2, 1, 2]
        for j in range(8):
            i0 = s0 + int(j * beat / 2 * SR); k = int(0.35 * SR)
            if i0 >= N:
                continue
            m = c[pattern[j]] + 24
            x = (sine(note(m), k) + 0.3 * sine(note(m) * 2, k) + 0.1 * sine(note(m) * 3, k))
            x *= np.exp(-np.arange(k) / SR * 9).astype(np.float32)
            arp[i0:i0 + k] += x[:N - i0] * (0.32 if j % 2 == 0 else 0.22)
        # drums
        for q in range(4):
            i0 = s0 + int(q * beat * SR)
            if i0 >= N:
                continue
            # kick on every beat (soft four-on-the-floor)
            k = int(0.22 * SR); t = np.arange(k) / SR
            f = 50 + 90 * np.exp(-t * 35)
            kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
            drums[i0:i0 + k] += kick[:N - i0].astype(np.float32) * 0.7
            # clap on 2 and 4
            if q in (1, 3):
                k = int(0.18 * SR)
                nz = rng.standard_normal(k).astype(np.float32)
                nz = nz - lp(nz, 0.15)
                clap = nz * np.exp(-np.arange(k) / SR * 22)
                drums[i0:i0 + k] += clap[:N - i0] * 0.22
            # hats on the off-beats
            h0 = i0 + int(beat / 2 * SR); k = int(0.05 * SR)
            if h0 < N:
                nz = rng.standard_normal(k).astype(np.float32)
                nz = nz - lp(nz, 0.5)
                drums[h0:h0 + k] += (nz * np.exp(-np.arange(k) / SR * 70))[:N - h0] * 0.12
    mixl = pad * 0.9 + arp + bass + drums
    # light stereo: arp a bit left, pad a bit right
    left = mixl + 0.15 * arp - 0.1 * pad
    right = mixl - 0.15 * arp + 0.1 * pad
    st = np.stack([left, right], 1)
    fade_in, fade_out = int(0.3 * SR), int(1.2 * SR)
    st[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    st[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
    st /= max(1e-6, np.abs(st).max()) / 0.9
    return st


def write(path, st):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    args = sys.argv[1:]
    bpm = float(args[args.index("--bpm") + 1]) if "--bpm" in args else 112
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 0
    write(args[1], make(float(args[0]), bpm, seed))
