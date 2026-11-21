"""Small animation engine for Webora reels (1080x1920, 30 fps)."""
import math, subprocess, os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
SPEED = 1.3

# Palette (sampled from the logo)
DARK = (6, 42, 50)
PETROL = (4, 72, 91)
TEAL = (19, 124, 139)
TURQ = (38, 182, 196)
LIGHT_TURQ = (165, 226, 229)
CREAM = (247, 248, 242)
WHITE = (255, 255, 255)
RED = (229, 72, 77)
GOLD = (245, 183, 49)
GREEN = (46, 170, 110)
GREY = (120, 135, 140)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONT = os.path.join(ROOT, "assets", "fonts", "Montserrat-wght.ttf")
SYM = os.path.join(ROOT, "assets", "fonts", "DejaVuSans-Bold.ttf")
LOGO = os.path.join(ROOT, "assets", "logo.jpg")


@lru_cache(maxsize=None)
def font(size, weight="ExtraBold"):
    f = ImageFont.truetype(MONT, size)
    f.set_variation_by_name(weight)
    return f


@lru_cache(maxsize=None)
def sym(size):
    return ImageFont.truetype(SYM, size)


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur) if dur > 0 else float(t >= start)


def out_cubic(x):
    return 1 - (1 - x) ** 3


def out_back(x, s=1.6):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def in_out(x):
    return 3 * x * x - 2 * x * x * x


# ---------- backgrounds ----------
def _gradient(top, bottom, glow, glow_pos, glow_r):
    g = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / (H - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    img = g.resize((W, H)).convert("RGBA")
    gl = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(gl)
    x, y = glow_pos
    d.ellipse((x - glow_r, y - glow_r, x + glow_r, y + glow_r), fill=90)
    gl = gl.filter(ImageFilter.GaussianBlur(glow_r * 0.6))
    col = Image.new("RGBA", (W, H), glow + (255,))
    col.putalpha(gl)
    return Image.alpha_composite(img, col)


@lru_cache(maxsize=None)
def bg(kind):
    if kind == "dark":
        return _gradient((4, 30, 37), (8, 66, 80), TURQ, (900, 300), 520)
    if kind == "light":
        return _gradient((250, 251, 247), (226, 243, 243), LIGHT_TURQ, (150, 1500), 600)
    if kind == "turq":
        return _gradient((12, 110, 126), (8, 70, 86), (80, 210, 220), (540, 700), 600)
    raise ValueError(kind)


# ---------- sprites ----------
def rich_line(segments, size, weight="ExtraBold"):
    """segments: list of (text, color). Returns RGBA sprite."""
    f = font(size, weight)
    asc, desc = f.getmetrics()
    widths = [f.getlength(s) for s, _ in segments]
    w = int(sum(widths)) + 4
    img = Image.new("RGBA", (w, asc + desc + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 2
    for (s, c), wd in zip(segments, widths):
        d.text((x, 2), s, font=f, fill=c)
        x += wd
    return img


def parse(line, base, hl):
    """'Tu rates des *chantiers*' -> segments; *x* highlighted."""
    parts = line.split("*")
    return [(p, hl if i % 2 else base) for i, p in enumerate(parts) if p]


_cache = {}


def text(line, size, color=WHITE, hl=TURQ, weight="ExtraBold"):
    key = ("t", line, size, color, hl, weight)
    if key not in _cache:
        _cache[key] = rich_line(parse(line, color, hl), size, weight)
    return _cache[key]


def rounded(w, h, r, fill, shadow=0, outline=None, ow=0):
    key = ("r", w, h, r, fill, shadow, outline, ow)
    if key in _cache:
        return _cache[key]
    pad = shadow * 2
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("L", img.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + shadow // 2, pad + w, pad + h + shadow // 2), r, fill=110)
        sh = sh.filter(ImageFilter.GaussianBlur(shadow))
        black = Image.new("RGBA", img.size, (0, 20, 25, 255))
        black.putalpha(sh)
        img = Image.alpha_composite(img, black)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill, outline=outline, width=ow)
    _cache[key] = (img, pad)
    return img, pad


def paste(canvas, sprite, x, y, alpha=1.0, anchor="lt", scale=1.0):
    """Composite sprite onto canvas. anchor: 'lt' top-left, 'mt' centered horizontally, 'mm' centered."""
    if alpha <= 0.003:
        return
    if scale != 1.0:
        sw, sh = max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale))
        sprite = sprite.resize((sw, sh), Image.BICUBIC)
    if anchor[0] == "m":
        x -= sprite.width / 2
    if anchor[1] == "m":
        y -= sprite.height / 2
    if alpha < 0.999:
        a = sprite.getchannel("A").point(lambda v: int(v * alpha))
        sprite = sprite.copy()
        sprite.putalpha(a)
    x, y = int(round(x)), int(round(y))
    canvas.alpha_composite(sprite, (max(0, x), max(0, y)),
                           (max(0, -x), max(0, -y)))


def appear(t, start, dur=0.45, dist=50):
    """returns (alpha, dy) for a slide-up fade."""
    p = out_cubic(prog(t, start, dur))
    return p, (1 - p) * dist


def lines(canvas, t, start, items, y, size, color=WHITE, hl=TURQ, gap=1.18, stagger=0.12, g=1.0, x=W / 2, weight="ExtraBold"):
    """Centered stack of lines that slide in one by one. Returns bottom y."""
    for i, ln in enumerate(items):
        st = start + i * stagger
        a, dy = appear(t, st, 0.3, 30)
        cue("pop" if i % 2 == 0 else "pop_hi", t, st)
        spr = text(ln, size, color, hl, weight)
        sc = min(1.0, 960 / spr.width)
        b = out_back(prog(t, st, 0.38), 2.2)
        if b < 0.999 or b > 1.001:
            sc *= max(0.05, 0.55 + 0.45 * b)
        paste(canvas, spr, x, y + dy + (1 - sc / min(1.0, 960 / spr.width)) * size * 0.5, a * g, "mt", scale=sc)
        y += size * gap
    return y


# ---------- UI pieces ----------
def icon_circle(d_size, color, glyph, gcol=WHITE, gsize=None):
    key = ("ic", d_size, color, glyph, gcol, gsize)
    if key in _cache:
        return _cache[key]
    img = Image.new("RGBA", (d_size, d_size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, d_size - 1, d_size - 1), fill=color)
    f = sym(gsize or int(d_size * 0.5))
    d.text((d_size / 2, d_size / 2 + 1), glyph, font=f, fill=gcol, anchor="mm")
    _cache[key] = img
    return img


def notif(title, body, icon_color, glyph, when="maintenant", w=860):
    key = ("n", title, body, icon_color, glyph, when, w)
    if key in _cache:
        return _cache[key]
    h = 170
    card, pad = rounded(w, h, 40, (255, 255, 255, 240), shadow=18)
    img = card.copy()
    paste(img, icon_circle(96, icon_color, glyph), pad + 34, pad + 37)
    d = ImageDraw.Draw(img)
    d.text((pad + 154, pad + 34), title, font=font(34, "Bold"), fill=DARK)
    d.text((pad + 154, pad + 88), body, font=font(30, "Medium"), fill=(60, 80, 86))
    d.text((pad + w - 30, pad + 38), when, font=font(24, "Medium"), fill=GREY, anchor="ra")
    _cache[key] = img
    return img


def phone(clock="10:42", date="mardi 14 mai"):
    key = ("ph", clock, date)
    if key in _cache:
        return _cache[key]
    w, h = 700, 1180
    img = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((40, 60, 40 + w, 60 + h), 100, fill=140)
    sh = sh.filter(ImageFilter.GaussianBlur(30))
    b = Image.new("RGBA", img.size, (0, 0, 0, 255)); b.putalpha(sh)
    img = Image.alpha_composite(img, b)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 40, 40 + w, 40 + h), 100, fill=(18, 22, 24))
    # screen gradient
    scr = _gradient((10, 90, 106), (5, 40, 50), TURQ, (500, 200), 300).resize((w - 36, h - 36))
    m = Image.new("L", scr.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, scr.width - 1, scr.height - 1), 84, fill=255)
    img.paste(scr, (58, 58), m)
    d.rounded_rectangle((40 + w / 2 - 90, 78, 40 + w / 2 + 90, 120), 21, fill=(10, 10, 10))
    d.text((40 + w / 2, 220), clock, font=font(150, "SemiBold"), fill=WHITE, anchor="mm")
    d.text((40 + w / 2, 330), date, font=font(34, "Medium"), fill=(220, 240, 240), anchor="mm")
    _cache[key] = img
    return img


def search_bar(typed, caret=True, w=900):
    card, pad = rounded(w, 130, 65, WHITE, shadow=16)
    img = card.copy()
    d = ImageDraw.Draw(img)
    cx, cy = pad + 70, pad + 65
    d.ellipse((cx - 22, cy - 26, cx + 16, cy + 12), outline=GREY, width=6)
    d.line((cx + 10, cy + 6, cx + 30, cy + 26), fill=GREY, width=8)
    f = font(40, "Medium")
    d.text((pad + 130, cy), typed, font=f, fill=DARK, anchor="lm")
    if caret:
        x = pad + 130 + f.getlength(typed) + 6
        d.line((x, cy - 26, x, cy + 26), fill=TEAL, width=4)
    return img


def result_card(name, url, rating, w=900):
    key = ("res", name, url, rating, w)
    if key in _cache:
        return _cache[key]
    card, pad = rounded(w, 200, 32, WHITE, shadow=14)
    img = card.copy()
    d = ImageDraw.Draw(img)
    d.text((pad + 40, pad + 30), url, font=font(26, "Medium"), fill=GREEN)
    d.text((pad + 40, pad + 72), name, font=font(40, "Bold"), fill=(26, 70, 160))
    d.text((pad + 40, pad + 135), "★★★★★", font=sym(32), fill=GOLD)
    d.text((pad + 230, pad + 136), rating, font=font(28, "Medium"), fill=GREY)
    _cache[key] = img
    return img


def ghost_card(w=900):
    key = ("ghost", w)
    if key in _cache:
        return _cache[key]
    h = 200
    img = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # dashed rounded outline (approx.)
    col = (255, 255, 255, 170)
    x0, y0, x1, y1 = 4, 4, w + 4, h + 4
    for x in range(x0 + 40, x1 - 40, 36):
        d.line((x, y0, x + 18, y0), fill=col, width=5)
        d.line((x, y1, x + 18, y1), fill=col, width=5)
    for y in range(y0 + 40, y1 - 40, 36):
        d.line((x0, y, x0, y + 18), fill=col, width=5)
        d.line((x1, y, x1, y + 18), fill=col, width=5)
    for (cx, cy, a0) in [(x0 + 32, y0 + 32, 180), (x1 - 32, y0 + 32, 270), (x1 - 32, y1 - 32, 0), (x0 + 32, y1 - 32, 90)]:
        d.arc((cx - 32, cy - 32, cx + 32, cy + 32), a0, a0 + 90, fill=col, width=5)
    d.text((w / 2 + 4, 70), "Ton entreprise ?", font=font(44, "ExtraBold"), fill=WHITE, anchor="mm")
    d.text((w / 2 + 4, 135), "Introuvable.", font=font(36, "Medium"), fill=LIGHT_TURQ, anchor="mm")
    _cache[key] = img
    return img


def check_item(label, dark_text=True, w=900):
    key = ("chk", label, dark_text, w)
    if key in _cache:
        return _cache[key]
    card, pad = rounded(w, 130, 36, (255, 255, 255, 255), shadow=12)
    img = card.copy()
    paste(img, icon_circle(78, TURQ, "✓", WHITE, 44), pad + 30, pad + 26)
    d = ImageDraw.Draw(img)
    d.text((pad + 135, pad + 65), label, font=font(38, "Bold"), fill=DARK, anchor="lm")
    _cache[key] = img
    return img


def pill(label, fill=TURQ, color=WHITE, size=40, padx=46, h=96):
    key = ("pill", label, fill, color, size)
    if key in _cache:
        return _cache[key]
    f = font(size, "ExtraBold")
    w = int(f.getlength(label)) + padx * 2
    card, pad = rounded(w, h, h // 2, fill, shadow=10)
    img = card.copy()
    ImageDraw.Draw(img).text((pad + w / 2, pad + h / 2), label, font=f, fill=color, anchor="mm")
    _cache[key] = img
    return img


@lru_cache(maxsize=None)
def logo(d=520):
    src = Image.open(LOGO).convert("RGB")
    cx, cy, r = 704, 384, 352
    crop = src.crop((cx - r, cy - r, cx + r, cy + r)).resize((d, d), Image.LANCZOS)
    m = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
    m = m.resize((d, d), Image.LANCZOS)
    out = Image.new("RGBA", (d + 80, d + 80), (0, 0, 0, 0))
    sh = Image.new("L", out.size, 0)
    ImageDraw.Draw(sh).ellipse((40, 52, 40 + d, 52 + d), fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(24))
    b = Image.new("RGBA", out.size, (0, 15, 20, 255)); b.putalpha(sh)
    out = Image.alpha_composite(out, b)
    crop = crop.convert("RGBA"); crop.putalpha(m)
    out.alpha_composite(crop, (40, 40))
    return out


# ---------- sound cues ----------
CUE = {"T0": 0.0, "events": None}


def cue(name, t, start):
    """Register a sound at scene-local time `start` (fires on the frame that reaches it)."""
    ev = CUE["events"]
    k = CUE.get("k", 1.0)
    if ev is not None and start - 1e-6 <= t < start + k / FPS - 1e-6:
        ev.append((CUE["T0"] + start / k, name))


# ---------- cursor ----------
@lru_cache(maxsize=None)
def cursor_sprite():
    s = 2.2
    pts = [(0, 0), (0, 34), (8, 26), (14, 40), (20, 37), (14, 24), (25, 24)]
    img = Image.new("RGBA", (80, 110), (0, 0, 0, 0))
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).polygon([(x * s + 10, y * s + 14) for x, y in pts], fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    b = Image.new("RGBA", img.size, (0, 0, 0, 255)); b.putalpha(sh)
    img = Image.alpha_composite(img, b)
    d = ImageDraw.Draw(img)
    d.polygon([(x * s + 6, y * s + 6) for x, y in pts], fill=WHITE, outline=(20, 20, 20), width=4)
    return img


def cursor(c, t, keys, clicks=(), g=1.0):
    """keys: [(time, x, y)] tip positions; eased between keys. clicks: times (ring + sound)."""
    if t < keys[0][0] - 0.25:
        return
    a = clamp((t - keys[0][0] + 0.25) / 0.25)
    x, y = keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t0 <= t:
            p = in_out(prog(t, t0, t1 - t0))
            x, y = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    sc = 1.0
    for ct in clicks:
        cue("click", t, ct)
        if ct <= t < ct + 0.45:
            p = (t - ct) / 0.45
            r = 20 + 60 * out_cubic(p)
            ring = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse((90 - r, 90 - r, 90 + r, 90 + r), outline=(255, 255, 255, int(200 * (1 - p))), width=6)
            paste(c, ring, x, y, g, "mm")
        if ct <= t < ct + 0.15:
            sc = 0.86
    paste(c, cursor_sprite(), x - 6 * sc, y - 6 * sc, a * g, scale=sc)


def press(t, clicks):
    """scale factor for an element pressed at click times."""
    for ct in clicks:
        if ct <= t < ct + 0.3:
            return 1 - 0.05 * math.sin(math.pi * (t - ct) / 0.3)
    return 1.0


# ---------- render ----------
STYLE = {"name": "classic", "cams": []}  # build_reel sets {"name": "dynamic", "cams": [...]} for the dynamic style


def render(scenes, out_path, preview_times=None, preview_dir=None):
    """scenes: list of (duration, bgkind, draw_fn(canvas, t, dur, g)).
    Background crossfades over 0.4 s between scenes; content fades out over last 0.3 s."""
    starts, acc = [], 0.0
    for d, _, _ in scenes:
        starts.append(acc); acc += d
    total = acc

    last = len(scenes) - 1

    @lru_cache(maxsize=None)
    def bigbg(kind):
        return bg(kind).resize((int(W * 1.08), int(H * 1.08)), Image.BICUBIC)

    def background(kind, T):
        b = bigbg(kind)
        ox = (b.width - W) / 2 + math.sin(T * 0.7) * (b.width - W) * 0.45
        oy = (b.height - H) / 2 + math.cos(T * 0.5) * (b.height - H) * 0.45
        return b.crop((int(ox), int(oy), int(ox) + W, int(oy) + H))

    def frame(T):
        i = max(k for k in range(len(scenes)) if starts[k] <= T + 1e-9)
        d, kind, fn = scenes[i][:3]
        k = scenes[i][3] if len(scenes[i]) > 3 else SPEED
        t = T - starts[i]
        CUE["T0"] = starts[i]; CUE["k"] = k
        if i > 0:
            cue("whoosh", t * k, 0.0)
        if STYLE["name"] == "dynamic":
            return dyn_frame(i, d, kind, fn, k, t, T)
        canvas = background(kind, T)
        if i > 0 and t < 0.25 and scenes[i - 1][1] != kind:
            canvas = Image.blend(background(scenes[i - 1][1], T), canvas, in_out(t / 0.25))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(layer, t * k, d * k, 1.0)
        z, a = 1 + 0.035 * (t / d), 1.0
        if i > 0 and t < 0.22:
            p = out_cubic(t / 0.22); z *= 1.14 - 0.14 * p; a = p
        if i < last and d - t < 0.16:
            p = (d - t) / 0.16; z *= 0.93 + 0.07 * p; a *= p
        sx = sy = 0.0
        evs = CUE["events"] or []
        for et, name in evs[-12:]:
            if name in ("thud", "error") and 0 <= T - et < 0.3:
                f = 1 - (T - et) / 0.3
                sx += 16 * f * math.sin((T - et) * 90); sy += 10 * f * math.cos((T - et) * 70)
        if abs(z - 1) > 1e-3 or sx or sy:
            zw, zh = int(W * z), int(H * z)
            big = layer.resize((zw, zh), Image.BILINEAR)
            x0, y0 = (zw - W) / 2 - sx, (zh - H) / 2 - sy
            layer = big.crop((int(x0), int(y0), int(x0) + W, int(y0) + H))
        if a < 0.999:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
        canvas.alpha_composite(layer)
        return canvas.convert("RGB")

    def dyn_frame(i, d, kind, fn, k, t, T):
        import dynamic as dy
        canvas = dy.background(kind, T)
        if i > 0 and t < 0.2 and scenes[i - 1][1] != kind:
            canvas = Image.blend(dy.background(scenes[i - 1][1], T), canvas, in_out(t / 0.2))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(layer, t * k, d * k, 1.0)
        cams = STYLE.get("cams") or []
        layer = dy.camera(layer, cams[i] if i < len(cams) else None, t, d, T)
        z, rot, a = 1 + 0.05 * (t / d), 0.0, 1.0
        if i > 0:
            zi, rot, ai = dy.transition_in(t); z *= zi; a = ai
        if i < last:
            zo, ao = dy.transition_out(d - t); z *= zo; a *= ao
        sx = sy = 0.0
        for et, name in (CUE["events"] or [])[-12:]:
            if name in ("thud", "error") and 0 <= T - et < 0.3:
                f = 1 - (T - et) / 0.3
                sx += 18 * f * math.sin((T - et) * 90); sy += 12 * f * math.cos((T - et) * 70)
        if abs(z - 1) > 1e-3 or sx or sy or rot:
            zw, zh = int(W * z), int(H * z)
            big = layer.resize((zw, zh), Image.BILINEAR)
            if rot:
                big = big.rotate(rot, Image.BILINEAR)
            x0, y0 = (zw - W) / 2 - sx, (zh - H) / 2 - sy
            if z >= 1:
                layer = big.crop((int(x0), int(y0), int(x0) + W, int(y0) + H))
            else:
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); layer.alpha_composite(big, (int(-x0), int(-y0)))
        if a < 0.999:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
        canvas.alpha_composite(layer)
        if i > 0:
            dy.flash(canvas, t)
        return canvas.convert("RGB")

    if preview_times:
        CUE["events"] = []
        os.makedirs(preview_dir, exist_ok=True)
        for T in preview_times:
            frame(T).save(f"{preview_dir}/f_{T:05.2f}.jpg", quality=88)
        CUE["events"] = None
        return

    n = int(round(total * FPS))
    silent = out_path[:-4] + ".video.mp4"
    tmp = silent[:-4] + ".tmp.mp4"
    CUE["events"] = []
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(frame(k / FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    os.replace(tmp, silent)
    import json
    json.dump({"total": total, "events": CUE["events"]}, open(out_path[:-4] + ".events.json", "w"))
    CUE["events"] = None
    mux(out_path, total)


def mux(out_path, total=None, extra_audio=None, music=None):
    import json, sfx
    base = out_path[:-4]
    info = json.load(open(base + ".events.json"))
    sfx.mix(info["events"], info["total"], base + ".sfx.wav")
    tmp = base + ".tmp.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", base + ".video.mp4", "-i", base + ".sfx.wav"]
    if extra_audio and music:
        # music sits ~14 dB under the voice and ducks further whenever voice or sound effects play
        cmd += ["-i", extra_audio, "-i", music, "-filter_complex",
                "[1:a]volume=0.3[s];[2:a]aresample=44100,pan=stereo|c0=c0|c1=c0[v];"
                "[s][v]amix=inputs=2:duration=first:normalize=0[fg];[fg]asplit[fg1][key];"
                "[3:a]loudnorm=I=-27:TP=-6,aresample=44100[m];"
                "[m][key]sidechaincompress=threshold=0.05:ratio=4:attack=30:release=350[md];"
                "[fg1][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.85:level=false[a]",
                "-map", "0:v", "-map", "[a]"]
    elif extra_audio:
        cmd += ["-i", extra_audio, "-filter_complex",
                "[1:a]volume=0.3[s];[2:a]aresample=44100,pan=stereo|c0=c0|c1=c0[v];[s][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.85:level=false[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp]
    subprocess.run(cmd, check=True)
    os.replace(tmp, out_path)
