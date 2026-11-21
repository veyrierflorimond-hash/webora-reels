"""'Dynamic' style for Webora Reels (présentation format): animated particle backgrounds, 3D camera moves,
punchy zoom transitions, a phone that flies in, slammed words. Enabled with "style": "dynamic" in a scenario."""
import math
import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

from engine import (DARK, GREY, LIGHT_TURQ, PETROL, TEAL, TURQ, WHITE, H, W, _gradient, appear, clamp, cue, font,
                    in_out, notif, out_back, out_cubic, paste, pill, prog, rounded, sym, text)

# ---------- backgrounds ----------
_rng = random.Random(7)
PARTS = [(_rng.random() * W, _rng.random() * H, 0.25 + 0.75 * _rng.random() ** 2, _rng.random() * 6.28,
          20 + 60 * _rng.random()) for _ in range(70)]


@lru_cache(maxsize=None)
def _base(kind):
    if kind == "light":
        g = _gradient((252, 253, 250), (222, 241, 242), LIGHT_TURQ, (200, 1500), 650)
    else:  # deep navy / petrol, like a tech studio backdrop
        g = _gradient((2, 12, 24), (5, 44, 62), TURQ, (820, 420), 560)
    return g.resize((int(W * 1.15), int(H * 1.15)), Image.BICUBIC)


@lru_cache(maxsize=None)
def _dot(r, light):
    s = int(r * 8) + 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = (19, 124, 139) if light else (150, 235, 240)
    d.ellipse((s / 2 - r * 2.5, s / 2 - r * 2.5, s / 2 + r * 2.5, s / 2 + r * 2.5), fill=col + (70,))
    img = img.filter(ImageFilter.GaussianBlur(r * 1.2))
    d = ImageDraw.Draw(img)
    d.ellipse((s / 2 - r * 0.7, s / 2 - r * 0.7, s / 2 + r * 0.7, s / 2 + r * 0.7), fill=(255, 255, 255, 230) if not light else col + (200,))
    return img


@lru_cache(maxsize=None)
def _beam(light):
    img = Image.new("RGBA", (900, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((330, 0, 570, H * 2), fill=((38, 182, 196, 26) if light else (120, 230, 240, 34)))
    img = img.filter(ImageFilter.GaussianBlur(90))
    return img.rotate(-24, resample=Image.BICUBIC, expand=False)


def background(kind, T):
    light = kind == "light"
    b = _base("light" if light else "dark")
    ox = (b.width - W) / 2 + math.sin(T * 0.55) * (b.width - W) * 0.45
    oy = (b.height - H) / 2 + math.cos(T * 0.4) * (b.height - H) * 0.45
    c = b.crop((int(ox), int(oy), int(ox) + W, int(oy) + H)).copy()
    # two slow light beams sweeping across
    bm = _beam(light)
    for k, sp in enumerate((90, -60)):
        x = ((T * sp + k * 700) % (W + 900)) - 900 if sp > 0 else W - ((T * -sp + k * 500) % (W + 900))
        c.alpha_composite(bm, (int(max(0, x)), 0), (int(max(0, -x)), int(H / 2)))
    # drifting particles (parallax: near ones are bigger and faster)
    for x0, y0, z, ph, sp in PARTS:
        y = (y0 - T * sp * z) % (H + 40) - 20
        x = x0 + math.sin(T * 0.6 + ph) * 30 * z
        tw = 0.55 + 0.45 * math.sin(T * 2.3 + ph * 3)
        r = round(1 + 3.5 * z)
        dot = _dot(r, light)
        if tw < 0.999:
            dot = dot.copy(); dot.putalpha(dot.getchannel("A").point(lambda v, tw=tw: int(v * tw)))
        xi, yi = int(x - dot.width / 2), int(y - dot.height / 2)
        if 0 <= xi < W - dot.width and 0 <= yi < H - dot.height:
            c.alpha_composite(dot, (xi, yi))
    return c


# ---------- camera ----------
def _coeffs(src, dst):
    """PIL perspective coefficients mapping output points (dst) to input points (src)."""
    import numpy as np
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def tilt(layer, yaw_deg, pitch_deg=0.0, dist=2600.0):
    """Rotate a flat layer in 3D around its centre (yaw = left/right, pitch = up/down)."""
    if abs(yaw_deg) < 0.05 and abs(pitch_deg) < 0.05:
        return layer
    cx, cy = W / 2, H / 2
    a, b = math.radians(yaw_deg), math.radians(pitch_deg)

    def proj(x, y):
        X, Y, Z = x - cx, y - cy, 0.0
        X, Z = X * math.cos(a), X * math.sin(a)
        Y, Z = Y * math.cos(b) - Z * math.sin(b), Y * math.sin(b) + Z * math.cos(b)
        s = dist / (dist + Z)
        return cx + X * s, cy + Y * s

    src = [(0, 0), (W, 0), (W, H), (0, H)]
    dst = [proj(*p) for p in src]
    return layer.transform((W, H), Image.PERSPECTIVE, _coeffs(src, dst), Image.BILINEAR)


def camera(layer, cam, t, d, T):
    if cam == "orbit":  # slow turn around the subject
        p = in_out(clamp(t / max(d, 0.1)))
        return tilt(layer, 13 - 22 * p, 4 * math.sin(T * 0.9))
    if cam == "swing":
        return tilt(layer, 9 * math.sin(t * 2.0), 3 * math.cos(t * 1.6))
    if cam == "float":
        return tilt(layer, 4 * math.sin(T * 1.1), 2.5 * math.sin(T * 0.8 + 1))
    return layer


# ---------- transitions ----------
def transition_in(t):
    """(zoom, rotation_deg, alpha) for the first 0.28 s of a scene."""
    if t >= 0.28:
        return 1.0, 0.0, 1.0
    p = t / 0.28
    b = out_back(p, 1.4)
    return 0.78 + 0.22 * b, 6 * (1 - out_cubic(p)), clamp(p * 2.2)


def transition_out(rem):
    """(zoom, alpha) for the last 0.16 s of a scene: the camera rushes through it."""
    if rem >= 0.16:
        return 1.0, 1.0
    p = 1 - rem / 0.16
    return 1 + 0.45 * p * p, 1 - p


@lru_cache(maxsize=None)
def _flash():
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse((W / 2 - 700, H / 2 - 700, W / 2 + 700, H / 2 + 700), fill=150)
    g = g.filter(ImageFilter.GaussianBlur(220))
    img = Image.new("RGBA", (W, H), (170, 240, 245, 255)); img.putalpha(g)
    return img


def flash(canvas, t):
    if t < 0.14:
        f = _flash().copy()
        a = 1 - t / 0.14
        f.putalpha(f.getchannel("A").point(lambda v: int(v * a)))
        canvas.alpha_composite(f)


# ---------- scenes ----------
@lru_cache(maxsize=None)
def phone_site(name="Ton entreprise", button="Demander un devis"):
    """A phone showing a small website (hero, button, gallery)."""
    w, h = 700, 1180
    img = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((40, 60, 40 + w, 60 + h), 100, fill=170)
    sh = sh.filter(ImageFilter.GaussianBlur(30))
    bk = Image.new("RGBA", img.size, (0, 0, 0, 255)); bk.putalpha(sh)
    img = Image.alpha_composite(img, bk)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 40, 40 + w, 40 + h), 100, fill=(18, 22, 24))
    sw, shh = w - 36, h - 36
    scr = Image.new("RGBA", (sw, shh), (247, 248, 242, 255))
    s = ImageDraw.Draw(scr)
    s.rectangle((0, 0, sw, 470), fill=PETROL)
    s.rounded_rectangle((60, 120, sw - 60, 168), 24, fill=(255, 255, 255, 40))
    s.text((sw / 2, 144), "www.ton-entreprise.fr", font=font(24, "Medium"), fill=LIGHT_TURQ, anchor="mm")
    s.text((60, 220), name, font=font(54, "ExtraBold"), fill=WHITE)
    s.text((60, 292), "Artisan · Beauté · Indépendant", font=font(28, "Medium"), fill=LIGHT_TURQ)
    s.rounded_rectangle((60, 360, 420, 430), 35, fill=TURQ)
    s.text((240, 395), button, font=font(28, "Bold"), fill=WHITE, anchor="mm")
    s.text((60, 510), "Nos réalisations", font=font(34, "ExtraBold"), fill=DARK)
    cols = [(12, 110, 126), (38, 182, 196), (4, 72, 91), (19, 124, 139)]
    for i in range(4):
        x, y = 50 + (i % 2) * 290, 580 + (i // 2) * 240
        s.rounded_rectangle((x, y, x + 270, y + 220), 26, fill=cols[i])
        s.text((x + 135, y + 110), ["⌂", "★", "✓", "♥"][i], font=sym(64), fill=(255, 255, 255, 210), anchor="mm")
    s.text((sw / 2 - 120, 1090), "★★★★★", font=sym(30), fill=(245, 183, 49), anchor="mm")
    s.text((sw / 2 + 70, 1090), "Avis clients", font=font(28, "Bold"), fill=TEAL, anchor="mm")
    m = Image.new("L", scr.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, sw - 1, shh - 1), 84, fill=255)
    img.paste(scr, (58, 58), m)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40 + w / 2 - 90, 78, 40 + w / 2 + 90, 120), 21, fill=(10, 10, 10))
    return img


def hook_phone(items, size, notif_spec):
    """Words at the top, a phone with a website flies in underneath, a notification pops on it."""
    ph = phone_site()

    def fn(c, t, d, g):
        y = 200
        for k, (st, line) in enumerate(items):
            cue("pop" if k % 2 == 0 else "pop_hi", t, st)
            p = out_back(prog(t, st, 0.32), 2.2)
            paste(c, text(line, size), W / 2, y + (1 - clamp(p)) * 30, clamp(p) * g, "mt", scale=max(0.01, 0.6 + 0.4 * p))
            y += size * 1.22
        cue("whoosh", t, 0.1)
        p = out_cubic(prog(t, 0.1, 0.75))
        rot = 22 * (1 - p)
        sc = 0.55 + 0.17 * out_back(prog(t, 0.1, 0.75), 1.2) + 0.02 * math.sin(t * 1.5)
        spr = ph.resize((int(ph.width * sc), int(ph.height * sc)), Image.BICUBIC).rotate(rot, Image.BICUBIC, expand=True)
        py = 640 + y - 200 - 260 + (1 - p) * 900 + 12 * math.sin(t * 2)
        paste(c, spr, W / 2, py, clamp(p * 1.5) * g, "mt")
        if notif_spec:
            st, ttl, body = notif_spec
            cue("success", t, st)
            q = out_back(prog(t, st, 0.4), 1.8)
            paste(c, notif(ttl, body, TURQ, "✉", "maintenant", 860), W / 2, py + 260 - (1 - clamp(q)) * 60,
                  clamp(q) * g, "mt", scale=max(0.01, 0.75 + 0.15 * q))
    return fn


def punch_words(items, size, pill_spec):
    """One big line at a time, slammed on the beat; the previous one is pushed away."""
    def fn(c, t, d, g):
        cur = [k for k, (st, _) in enumerate(items) if t >= st]
        for k, (st, line) in enumerate(items):
            cue("thud" if k == len(items) - 1 else "pop", t, st)
            if k not in cur:
                continue
            nxt = items[k + 1][0] if k + 1 < len(items) else None
            p = clamp(prog(t, st, 0.2))
            sc = 1.7 - 0.7 * out_cubic(p)
            a = p
            y = 860
            if nxt is not None and t >= nxt:
                q = clamp(prog(t, nxt, 0.18))
                sc = 1 - 0.4 * q; a = 1 - q; y -= 260 * q
            sx = 14 * math.sin((t - st) * 60) * max(0, 1 - (t - st) / 0.25) if t > st + 0.15 else 0
            spr = text(line, size)
            paste(c, spr, W / 2 + sx, y, a * g, "mm", scale=sc * min(1.0, 980 / spr.width))
        if pill_spec:
            st, label = pill_spec
            cue("success", t, st)
            p = out_back(prog(t, st, 0.4), 1.8)
            paste(c, pill(label, TURQ, WHITE, 50, 54, 120), W / 2, 1010, clamp(p) * g, "mt", scale=max(0.01, p))
    return fn
