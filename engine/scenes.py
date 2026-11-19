"""Scene templates for Webora reels (times are INTERNAL = real seconds x SPEED)."""
import sys
from engine import *

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


