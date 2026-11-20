"""Scene templates for Webora reels (times are INTERNAL = real seconds x SPEED)."""
import sys
from engine import *
from engine import _cache

_scaled = {}


def scaled(key, spr, s):
    k = (key, s)
    if k not in _scaled:
        _scaled[k] = spr.resize((int(spr.width * s), int(spr.height * s)), Image.LANCZOS)
    return _scaled[k]


# ---------- reusable scenes ----------
def hook(items, size=112, y=None):
    def fn(c, t, d, g):
        yy = y if y is not None else 960 - len(items) * size * 1.18 / 2
        lines(c, t, 0.1, items, yy, size, g=g, stagger=0.13)
    return fn


def statement(items, size=104, dark=True, small=None):
    def fn(c, t, d, g):
        col, hl = (WHITE, TURQ) if dark else (DARK, TEAL)
        n = len(items) + (1 if small else 0)
        yy = 930 - n * size * 1.18 / 2
        yy = lines(c, t, 0.05, items, yy, size, col, hl, g=g, stagger=0.15)
        if small:
            a, dy = appear(t, 0.05 + len(items) * 0.15 + 0.35)
            cue("thud", t, 0.05 + len(items) * 0.15 + 0.35)
            paste(c, pill(small, TURQ if dark else DARK), W / 2, yy + 30 + dy, a * g, "mt")
    return fn


def phone_scene(top_lines, notifs, clock, date):
    """notifs: list of (start, title, body, color, glyph)."""
    ph = scaled(("ph", clock, date), phone(clock, date), 0.8)

    def fn(c, t, d, g):
        lines(c, t, 0.05, top_lines, 330, 66, g=g, stagger=0.12)
        a, dy = appear(t, 0.25, 0.6, 120)
        shake = 0
        for st, _, _, _, glyph in notifs:
            cue("buzz" if glyph == "☎" else "ding", t, st)
            if glyph == "☎" and st <= t < st + 0.55:
                shake = 9 * math.sin((t - st) * 95) * (1 - (t - st) / 0.55)
        px, py = W / 2 - ph.width / 2 + shake, 580 + dy
        paste(c, ph, px, py, a * g)
        ny = py + 330
        shown = [n for n in notifs if t >= n[0]]
        # newest on top, older ones pushed down
        for k, (st, title, body, colr, glyph) in enumerate(reversed(shown)):
            p = out_back(prog(t, st, 0.45))
            spr = scaled(("n", title, body), notif(title, body, colr, glyph, "maintenant" if k == 0 else "il y a 1 min", 860), 0.66)
            yk = ny + k * 128 - (1 - p) * 60
            paste(c, spr, W / 2 + shake, yk, clamp(p) * g, "mt")
    return fn


def search_scene(top_lines, query, cards, ghost=False, after=None, bar_y=380, cur=None):
    """cards: list of (start, name, url, rating). after: (start, pill label)."""
    def fn(c, t, d, g):
        y_end = lines(c, t, 0.05, top_lines, bar_y - 60 - len(top_lines) * 66 * 1.18, 66, g=g)
        a, dy = appear(t, 0.2)
        L = len(query)
        n = int(L * prog(t, 0.6, 1.4) + 1e-6)
        for i in range(L):
            if query[i] != " " or i % 3 == 0:
                cue("key", t, 0.6 + (i + 1) * 1.4 / L - 1 / FPS)
        caret = (int(t * 2.4) % 2 == 0) or n < len(query)
        paste(c, search_bar(query[:n], caret), W / 2, bar_y - 16 + dy, a * g, "mt")
        y = bar_y + 175
        card_y = []
        for k, (st, name, url, rating) in enumerate(cards):
            a, dy = appear(t, st, 0.4, 70)
            cue("pop" if k % 2 == 0 else "pop_hi", t, st)
            card_y.append(y)
            sc = press(t, [cur[1]]) if (cur and k == 0) else 1.0
            paste(c, result_card(name, url, rating), W / 2, y - 14 + dy + (1 - sc) * 100, a * g, "mt", scale=sc)
            y += 230
        if ghost:
            st = ghost
            cue("thud", t, st)
            a, dy = appear(t, st, 0.5, 70)
            # little shake to draw attention
            sx = 10 * math.sin((t - st) * 30) * max(0, 1 - (t - st) / 0.6) if t > st else 0
            paste(c, ghost_card(), W / 2 + sx, y + dy, a * g, "mt")
        if after:
            st, label = after
            cue("error", t, st)
            p = out_back(prog(t, st, 0.45))
            paste(c, pill(label, RED), W / 2, y + 10, clamp(p) * g, "mt", scale=max(0.01, p))
        if cur:
            move, clk = cur
            by = bar_y + 81
            cy0 = card_y[0] + 120 if card_y else by
            cursor(c, t, [(0.0, 900, by + 420), (0.42, 470, by + 10), (move, 470, by + 10),
                          (move + 0.55, 640, cy0)], [0.45, clk], g)
    return fn


def solution(checks, notif_spec, title="Avec un *site* :"):
    def fn(c, t, d, g):
        lines(c, t, 0.1, [title], 400, 96, DARK, TEAL, g=g)
        y = 600
        for i, lab in enumerate(checks):
            a, dy = appear(t, 0.6 + i * 0.45, 0.45, 0)
            cue("check", t, 0.6 + i * 0.45)
            dx = (1 - out_cubic(prog(t, 0.6 + i * 0.45, 0.45))) * 120
            paste(c, check_item(lab), W / 2 + dx, y, a * g, "mt")
            y += 165
        st, ttl, body = notif_spec
        cue("success", t, st)
        p = out_back(prog(t, st, 0.5))
        paste(c, notif(ttl, body, TURQ, "✉", "maintenant", 900), W / 2, y + 40 - (1 - p) * 80, clamp(p) * g, "mt")
    return fn


CTA_PILL = "Envoie-moi un message"
CTA_SUB = "pour qu'on discute de ton projet !"


def cta(top_lines):
    lg = logo(440)

    def fn(c, t, d, g):
        lines(c, t, 0.1, top_lines, 300, 78, stagger=0.18)
        cue("shimmer", t, 0.4)
        p = out_back(prog(t, 0.5, 0.7), 1.3)
        breathe = 1 + 0.015 * math.sin(t * 2.2)
        paste(c, lg, W / 2, 880, clamp(p), "mm", scale=max(0.01, p * breathe))
        a, dy = appear(t, 1.2)
        cue("pop", t, 1.2)
        sc = press(t, [2.75])
        paste(c, pill(CTA_PILL, TURQ, WHITE, 46), W / 2, 1140 + dy + (1 - sc) * 60, a, "mt", scale=sc)
        a, dy = appear(t, 1.4)
        cue("pop_hi", t, 1.4)
        paste(c, text(CTA_SUB, 44, WHITE, TURQ, "Bold"), W / 2, 1275 + dy, a, "mt")
        a, dy = appear(t, 1.6)
        paste(c, text("@webora.agence", 36, LIGHT_TURQ, TURQ, "SemiBold"), W / 2, 1345 + dy, a, "mt")
        cursor(c, t, [(2.0, 980, 1600), (2.65, 868, 1200)], [2.75])
    return fn




# ---------- extra interfaces (variety) ----------
def wrap(s, f, maxw):
    out, cur = [], ""
    for w_ in s.split():
        t_ = (cur + " " + w_).strip()
        if f.getlength(t_) <= maxw or not cur:
            cur = t_
        else:
            out.append(cur); cur = w_
    if cur:
        out.append(cur)
    return out


def bubble(txt, mine, maxw=600):
    key = ("bub", txt, mine, maxw)
    if key in _cache:
        return _cache[key]
    f = font(36, "Medium")
    ls = wrap(txt, f, maxw - 64)
    w = int(max(f.getlength(l) for l in ls)) + 64
    h = 30 + len(ls) * 48 + 22
    card, pad = rounded(w, h, 34, TURQ if mine else (255, 255, 255), shadow=8)
    img = card.copy()
    d = ImageDraw.Draw(img)
    for i, l in enumerate(ls):
        d.text((pad + 32, pad + 26 + i * 48), l, font=f, fill=WHITE if mine else DARK)
    _cache[key] = img
    return img


def chat_panel(contact, status, w=920, h=900):
    key = ("chatp", contact, status, w, h)
    if key in _cache:
        return _cache[key]
    card, pad = rounded(w, h, 48, (232, 243, 243), shadow=20)
    img = card.copy()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((pad, pad, pad + w, pad + 130), 48, fill=PETROL)
    d.rectangle((pad, pad + 80, pad + w, pad + 130), fill=PETROL)
    paste(img, icon_circle(80, TURQ, contact[:1].upper(), WHITE, 40), pad + 36, pad + 25)
    d.text((pad + 140, pad + 30), contact, font=font(36, "Bold"), fill=WHITE)
    d.text((pad + 140, pad + 76), status, font=font(26, "Medium"), fill=LIGHT_TURQ)
    _cache[key] = (img, pad)
    return img, pad


def chat_scene(top_lines, contact, status, msgs, alert=None):
    """msgs: list of (start, mine, text). alert: (start, label)."""
    panel, pad = chat_panel(contact, status)
    py = 470

    def fn(c, t, d, g):
        lines(c, t, 0.05, top_lines, 300 - (len(top_lines) - 1) * 70, 66, g=g, stagger=0.12)
        a, dy = appear(t, 0.2, 0.5, 80)
        paste(c, panel, W / 2, py - pad + dy, a * g, "mt")
        y = py + 170
        for st, mine, txt in msgs:
            spr = bubble(txt, mine)
            cue("pop_hi" if mine else "ding", t, st)
            p = out_back(prog(t, st, 0.4))
            x = W / 2 + 430 - spr.width if mine else W / 2 - 430
            paste(c, spr, x + (1 - clamp(p)) * (40 if mine else -40), y + dy, clamp(p) * a * g)
            y += spr.height + 4
        if alert:
            st, label = alert
            cue("error", t, st)
            p = out_back(prog(t, st, 0.45))
            paste(c, pill(label, RED), W / 2, min(y + 30, 1300), clamp(p) * g, "mt", scale=max(0.01, p))
    return fn


def site_card(name, url, tagline, button, gallery, w=920, h=930):
    key = ("site", name, url, tagline, button, tuple(gallery), w, h)
    if key in _cache:
        return _cache[key]
    card, pad = rounded(w, h, 40, WHITE, shadow=20)
    img = card.copy()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((pad, pad, pad + w, pad + 90), 40, fill=(233, 238, 238))
    d.rectangle((pad, pad + 50, pad + w, pad + 90), fill=(233, 238, 238))
    for i, col in enumerate([RED, GOLD, GREEN]):
        d.ellipse((pad + 34 + i * 40, pad + 34, pad + 58 + i * 40, pad + 58), fill=col)
    d.rounded_rectangle((pad + 180, pad + 22, pad + w - 40, pad + 70), 24, fill=WHITE)
    d.text((pad + 210, pad + 46), url, font=font(28, "Medium"), fill=GREY, anchor="lm")
    _cache[key] = (img, pad)
    return img, pad


def site_scene(top_lines, name, url, tagline, button, gallery, click_at, notif_spec):
    """Website mockup on a light background; the cursor clicks the main button at click_at."""
    card, pad = site_card(name, url, tagline, button, gallery)
    cy0 = 380
    hero_h = 380
    btn = pill(button, TURQ, WHITE, 38, 40, 90)
    tiles = []
    for i, lab in enumerate(gallery[:3]):
        cols = [(12, 110, 126), (38, 182, 196), (4, 72, 91)]
        tc, tp = rounded(270, 230, 26, cols[i], shadow=6)
        im = tc.copy()
        dd = ImageDraw.Draw(im)
        dd.text((tp + 135, tp + 95), ["⌂", "★", "✓"][i], font=sym(70), fill=(255, 255, 255, 200), anchor="mm")
        dd.text((tp + 135, tp + 185), lab, font=font(28, "Bold"), fill=WHITE, anchor="mm")
        tiles.append(im)

    def fn(c, t, d, g):
        lines(c, t, 0.05, top_lines, 210 - (len(top_lines) - 1) * 40, 64, DARK, TEAL, g=g, stagger=0.12)
        a, dy = appear(t, 0.15, 0.5, 90)
        y0 = cy0 + dy
        paste(c, card, W / 2, y0 - pad, a * g, "mt")
        x0 = W / 2 - 460
        # hero
        ha = clamp(prog(t, 0.45, 0.4))
        if ha > 0:
            hero = Image.new("RGBA", (920, hero_h), PETROL + (255,))
            hd = ImageDraw.Draw(hero)
            hd.text((60, 70), name, font=font(58, "ExtraBold"), fill=WHITE)
            yy = 160
            for l in wrap(tagline, font(34, "Medium"), 780):
                hd.text((60, yy), l, font=font(34, "Medium"), fill=LIGHT_TURQ); yy += 46
            paste(c, hero, x0, y0 + 90, ha * a * g)
        ba, bdy = appear(t, 0.8, 0.4, 30)
        cue("pop", t, 0.8)
        sc = press(t, [click_at])
        paste(c, btn, x0 + 60 + btn.width / 2, y0 + 90 + hero_h - 125 + bdy + (1 - sc) * 40, ba * a * g, "mt", scale=sc)
        la, ldy = appear(t, 1.0, 0.4, 20)
        paste(c, text("Nos réalisations", 40, DARK, TEAL, "ExtraBold"), x0 + 40, y0 + 90 + hero_h + 40 + ldy, la * a * g)
        for i, tl in enumerate(tiles):
            st = 1.1 + i * 0.18
            cue("pop_hi" if i % 2 else "pop", t, st)
            p = out_back(prog(t, st, 0.4))
            paste(c, tl, x0 + 20 + i * 295 + tl.width / 2, y0 + 90 + hero_h + 120, clamp(p) * a * g, "mt", scale=max(0.01, p))
        bx, by = x0 + 60 + btn.width / 2, y0 + 90 + hero_h - 125 + 50
        cursor(c, t, [(0.0, 1000, 1500), (max(0.3, click_at - 0.75), 1000, 1500), (click_at - 0.08, bx + 60, by + 20)], [click_at], g)
        st, ttl, body = notif_spec
        cue("success", t, st)
        p = out_back(prog(t, st, 0.5))
        paste(c, notif(ttl, body, TURQ, "✉", "maintenant", 900), W / 2, 1230 - (1 - p) * 80, clamp(p) * g, "mt")
    return fn


def compare_row(label, good, w=470):
    key = ("cmp", label, good, w)
    if key in _cache:
        return _cache[key]
    card, pad = rounded(w, 130, 30, WHITE if good else (255, 255, 255, 40), shadow=10 if good else 0,
                        outline=None if good else (255, 255, 255, 90), ow=0 if good else 3)
    img = card.copy()
    paste(img, icon_circle(60, TURQ if good else RED, "✓" if good else "✕", WHITE, 34), pad + 22, pad + 35)
    d = ImageDraw.Draw(img)
    f = font(30, "Bold")
    ls = wrap(label, f, w - 120)[:2]
    y = pad + 65 - len(ls) * 19
    for l in ls:
        d.text((pad + 100, y), l, font=f, fill=DARK if good else WHITE); y += 38
    _cache[key] = img
    return img


def compare_scene(top_lines, left_title, right_title, rows):
    """rows: list of (start, left_label, right_label); the right card arrives 0.35 s after the left one."""
    def fn(c, t, d, g):
        lines(c, t, 0.05, top_lines, 300 - (len(top_lines) - 1) * 70, 70, g=g, stagger=0.12)
        a, dy = appear(t, 0.3)
        paste(c, pill(left_title, RED, WHITE, 36, 36, 84), W / 2 - 250, 470 + dy, a * g, "mt")
        paste(c, pill(right_title, TURQ, WHITE, 36, 36, 84), W / 2 + 250, 470 + dy, a * g, "mt")
        y = 620
        for st, l, r in rows:
            for k, (lab, good, x, s) in enumerate([(l, False, W / 2 - 250, st), (r, True, W / 2 + 250, st + 0.35)]):
                cue("check" if good else "thud", t, s)
                p = out_back(prog(t, s, 0.4))
                paste(c, compare_row(lab, good), x + (1 - clamp(p)) * (60 if good else -60), y, clamp(p) * g, "mt")
            y += 175
    return fn
