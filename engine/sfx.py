"""Procedural sound effects + mixer."""
import numpy as np, wave

SR = 44100
rng = np.random.default_rng(7)


def env(n, attack=0.002, decay=0.08):
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1) if attack > 0 else np.ones(n)
    return a * np.exp(-t / decay)


def lp(x, k):
    # simple one-pole low-pass, k in (0,1): higher = brighter
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc); y[i] = acc
    return y


def hp(x, k):
    return x - lp(x, k)


def tone(f0, f1, dur, decay, harm=(1.0,), attack=0.002):
    n = int(SR * dur); t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(a * np.sin(ph * (i + 1)) for i, a in enumerate(harm))
    return s * env(n, attack, decay)


def key():
    n = int(SR * 0.05)
    noise = rng.standard_normal(n)
    click = hp(noise, 0.35) * env(n, 0.0005, 0.006) * 0.9
    body = tone(rng.uniform(1700, 2600), 1200, 0.05, 0.012, (1, .3)) * 0.25
    thock = tone(rng.uniform(170, 230), 140, 0.05, 0.015) * 0.35
    return (click + body + thock) * rng.uniform(0.65, 1.0)


def pop(pitch=1.0):
    s = tone(950 * pitch, 260 * pitch, 0.12, 0.035, (1, .25))
    n = len(s); s[:int(SR * .004)] += rng.standard_normal(int(SR * .004)) * 0.15
    return s * 0.75


def whoosh(dur=0.45):
    n = int(SR * dur); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n); acc = 0.0
    for i in range(n):  # sweeping low-pass
        k = 0.02 + 0.25 * np.sin(np.pi * t[i] / dur) ** 2
        acc += k * (noise[i] - acc); out[i] = acc
    return out * np.sin(np.pi * t / dur) ** 1.5 * 1.1


def click():
    n = int(SR * 0.06)
    a = hp(rng.standard_normal(n), 0.5) * env(n, 0.0002, 0.003)
    b = tone(3200, 2500, 0.06, 0.006) * 0.4
    c = tone(240, 160, 0.06, 0.012) * 0.5
    d = np.zeros(n); off = int(SR * 0.035)  # release click
    d[off:] = (hp(rng.standard_normal(n - off), 0.5) * env(n - off, 0.0002, 0.002)) * 0.4
    return (a + b + c + d) * 0.9


def ding():  # message notification
    a = tone(1318.5, 1318.5, 0.6, 0.18, (1, .2, .08))
    b = tone(1975.5, 1975.5, 0.6, 0.22, (1, .2, .08))
    out = np.zeros(int(SR * 0.75)); out[:len(a)] += a * 0.5
    o = int(SR * 0.09); out[o:o + len(b)] += b * 0.45
    return out


def buzz():  # phone vibration x2
    out = np.zeros(int(SR * 0.62))
    for st in (0.0, 0.32):
        n = int(SR * 0.24); t = np.arange(n) / SR
        s = np.sign(np.sin(2 * np.pi * 165 * t)) * 0.6 + np.sin(2 * np.pi * 330 * t) * 0.3
        s = lp(s, 0.18) * np.clip(np.minimum(t / 0.01, (0.24 - t) / 0.02), 0, 1)
        o = int(SR * st); out[o:o + n] += s * 1.4
    return out


def success():  # bright arpeggio for new quote request
    out = np.zeros(int(SR * 1.0))
    for i, f in enumerate((1046.5, 1318.5, 1568.0, 2093.0)):
        s = tone(f, f, 0.7, 0.2, (1, .3, .1)) * 0.38
        o = int(SR * 0.07 * i); out[o:o + len(s)] += s
    return out


def error():  # two descending tones
    out = np.zeros(int(SR * 0.5))
    for i, f in enumerate((520, 390)):
        s = tone(f, f * 0.97, 0.22, 0.09, (1, .5, .3, .15)) * 0.45
        o = int(SR * 0.13 * i); out[o:o + len(s)] += s
    return out


def thud():  # "introuvable" low hit
    s = tone(140, 55, 0.5, 0.16, (1, .4)) * 0.9
    n = int(SR * .02); s[:n] += lp(rng.standard_normal(n), 0.2) * 0.6
    return s


def shimmer():  # logo reveal
    out = np.zeros(int(SR * 1.4))
    out[:int(SR * .45)] += whoosh(0.45) * 0.6
    for i, f in enumerate((1568, 2093, 2637, 3136)):
        s = tone(f, f, 0.9, 0.3, (1, .15)) * 0.16
        o = int(SR * (0.3 + 0.05 * i)); out[o:o + len(s)] += s
    s = tone(130, 90, 0.6, 0.2) * 0.5; o = int(SR * .3); out[o:o + len(s)] += s
    return out


def check():
    return tone(1500, 2200, 0.12, 0.04, (1, .2)) * 0.45 + np.pad(pop(0.8), (0, 0))[:int(SR * 0.12)] * 0.3


BANK = {
    "key": (key, 0.55), "pop": (pop, 0.45), "pop_hi": (lambda: pop(1.35), 0.4),
    "whoosh": (whoosh, 0.35), "click": (click, 0.8), "ding": (ding, 0.45), "buzz": (buzz, 0.45),
    "success": (success, 0.55), "error": (error, 0.5), "thud": (thud, 0.7), "shimmer": (shimmer, 0.6),
    "check": (check, 0.5),
}


def mix(events, total, path):
    out = np.zeros(int(SR * (total + 1.5)))
    for t, name in events:
        fn, vol = BANK[name]
        s = fn() * vol
        o = int(SR * t); out[o:o + len(s)] += s[:len(out) - o]
    out = out[:int(SR * total)]
    fade = int(SR * 0.3); out[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(out)) or 1
    out = np.tanh(out / peak * 1.3) / np.tanh(1.3) * 0.89  # soft limit
    pcm = (out * 32767).astype(np.int16)
    st = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
