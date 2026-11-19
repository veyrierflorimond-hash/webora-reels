#!/usr/bin/env python3
"""Render a Webora Instagram carousel (1080x1350 JPEG slides) from a JSON scenario.

Usage:  python3 engine/post.py scenario.json out_dir/

Scenario:
{
  "tag": "ARTISANS DU BÂTIMENT",                      # small label on the cover
  "cover": ["3 erreurs qui", "font *fuir*", "tes clients"],   # 2-4 short lines, *mot* = turquoise
  "cover_sub": "La 2e est la plus courante.",          # optional, one line under the cover
  "slides": [                                          # 3 to 5 content slides
    {"title": "Pas de photos de tes chantiers", "body": "Le client veut voir ton travail avant d'appeler. Sans photos, il passe au suivant.",
     "fix": "Une page « Réalisations » avec tes plus beaux chantiers."},   # "fix" optional
    ...
  ],
  "cta_lines": ["Ton travail mérite", "d'être *vu*."]   # 1-3 lines above the fixed call to action
}
The last slide always ends with the fixed call to action:
« Envoie-moi un message » / « pour qu'on discute de ton projet ! » / @webora.agence
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
import engine  # noqa: E402
from engine import (CREAM, DARK, LIGHT_TURQ, PETROL, TEAL, TURQ, WHITE, font, icon_circle, logo, paste,  # noqa: E402
                    pill, rich_line, parse, rounded)

PW, PH = 1080, 1350


def gradient(top, bottom, glow, gpos, gr):
    g = Image.new("RGB", (1, PH))
    for y in range(PH):
        k = y / (PH - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    img = g.resize((PW, PH)).convert("RGBA")
    gl = Image.new("L", (PW, PH), 0)
    x, y = gpos
    ImageDraw.Draw(gl).ellipse((x - gr, y - gr, x + gr, y + gr), fill=90)
    gl = gl.filter(ImageFilter.GaussianBlur(gr * 0.6))
    col = Image.new("RGBA", (PW, PH), glow + (255,))
    col.putalpha(gl)
    return Image.alpha_composite(img, col)


def dark_bg():
    return gradient((4, 30, 37), (8, 66, 80), TURQ, (900, 220), 480)


def light_bg():
    return gradient((250, 251, 247), (226, 243, 243), LIGHT_TURQ, (120, 1200), 520)


def wrap(text, size, weight, maxw):
    f = font(size, weight)
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t.replace("*", "")) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(img, lines, x, y, size, color, hl, weight="ExtraBold", gap=1.2, align="left", maxw=900):
    for ln in lines:
        spr = rich_line(parse(ln, color, hl), size, weight)
        sc = min(1.0, maxw / spr.width)
        if sc < 1:
            spr = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.LANCZOS)
        xx = x - spr.width / 2 if align == "center" else x
        img.alpha_composite(spr, (int(xx), int(y)))
        y += size * gap * sc
    return y


def page_dots(img, i, n, dark):
    col_on = TURQ
    col_off = (255, 255, 255, 90) if dark else (4, 72, 91, 60)
    d = ImageDraw.Draw(img)
    w = n * 26
    x0 = PW / 2 - w / 2
    for k in range(n):
        cx = x0 + k * 26 + 13
        r = 7 if k == i else 5
        d.ellipse((cx - r, PH - 70 - r, cx + r, PH - 70 + r), fill=col_on if k == i else col_off)


def small_logo(img, x, y, d=120):
    lg = logo(d)
    img.alpha_composite(lg, (int(x), int(y)))


def cover(spec, n):
    img = dark_bg()
    if spec.get("tag"):
        p = pill(spec["tag"], TURQ, WHITE, 30, padx=34, h=70)
        img.alpha_composite(p, (60, 110))
    lines = spec["cover"]
    size = 118 if len(lines) <= 3 else 104
    y = 330
    y = text_block(img, lines, 80, y, size, WHITE, TURQ, maxw=920)
    if spec.get("cover_sub"):
        text_block(img, [spec["cover_sub"]], 84, y + 40, 44, LIGHT_TURQ, TURQ, "SemiBold", maxw=900)
    swipe = rich_line([("Glisse  →", WHITE)], 40, "Bold")
    img.alpha_composite(swipe, (PW - swipe.width - 70, PH - 150))
    small_logo(img, 40, PH - 230, 150)
    page_dots(img, 0, n, True)
    return img


def content(slide, i, n):
    img = light_bg()
    num = icon_circle(150, TURQ, str(i), WHITE, 84)
    img.alpha_composite(num, (80, 150))
    y = 360
    y = text_block(img, wrap(slide["title"], 76, "ExtraBold", 920), 80, y, 76, DARK, TEAL, maxw=920)
    y += 30
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((80, y, 200, y + 10), 5, fill=TURQ)
    y += 60
    y = text_block(img, wrap(slide["body"], 48, "Medium", 900), 80, y, 48, (40, 64, 70), TEAL, "Medium", gap=1.4, maxw=920)
    if slide.get("fix"):
        fl = wrap(slide["fix"], 42, "SemiBold", 760)
        h = 150 + len(fl) * 56
        y0 = max(y + 70, PH - 170 - h)
        card, pad = rounded(920, h, 36, WHITE, shadow=14)
        img.alpha_composite(card, (80 - pad, int(y0) - pad))
        d.rounded_rectangle((80, y0, 92, y0 + h), 6, fill=TURQ)
        img.alpha_composite(icon_circle(64, TURQ, "✓", WHITE, 36), (122, int(y0) + 30))
        text_block(img, ["*La solution*"], 206, y0 + 38, 40, DARK, TEAL, "ExtraBold")
        text_block(img, fl, 122, y0 + 108, 42, DARK, TEAL, "SemiBold", gap=1.33, maxw=800)
    tag = rich_line([("@webora.agence", PETROL)], 30, "SemiBold")
    img.alpha_composite(tag, (PW - tag.width - 70, 90))
    page_dots(img, i, n, False)
    return img


def final(spec, n):
    img = dark_bg()
    y = text_block(img, spec.get("cta_lines", []), PW / 2, 170, 80, WHITE, TURQ, align="center", maxw=940)
    lg = logo(420)
    img.alpha_composite(lg, (int(PW / 2 - lg.width / 2), int(max(y, 380) + 10)))
    yb = int(max(y, 380) + 10 + lg.height + 10)
    p = pill("Envoie-moi un message", TURQ, WHITE, 48)
    img.alpha_composite(p, (int(PW / 2 - p.width / 2), yb))
    yb += p.height + 10
    text_block(img, ["pour qu'on discute de ton projet !"], PW / 2, yb, 46, WHITE, TURQ, "Bold", align="center")
    text_block(img, ["@webora.agence"], PW / 2, yb + 80, 38, LIGHT_TURQ, TURQ, "SemiBold", align="center")
    page_dots(img, n - 1, n, True)
    return img


def main(spec_path, out_dir):
    spec = json.load(open(spec_path))
    slides = spec["slides"]
    assert 3 <= len(slides) <= 5, "3 à 5 slides de contenu"
    n = len(slides) + 2
    os.makedirs(out_dir, exist_ok=True)
    imgs = [cover(spec, n)] + [content(s, i + 1, n) for i, s in enumerate(slides)] + [final(spec, n)]
    paths = []
    for i, im in enumerate(imgs):
        p = os.path.join(out_dir, "%02d.jpg" % (i + 1))
        im.convert("RGB").save(p, quality=90)
        paths.append(p)
    print(json.dumps({"slides": paths}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
