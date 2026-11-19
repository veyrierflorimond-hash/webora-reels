#!/usr/bin/env python3
"""Build a Webora Reel (1080x1920, 30 fps, voice + sound effects) from a JSON scenario.

Usage:  python3 engine/build_reel.py scenario.json out/2026-11-23_sujet.mp4

Scenario format (see PLAYBOOK.md for the full guide):
{
  "scenes": [
    {"type": "hook", "lines": ["Tu rates", "des *chantiers*", "sans même", "le savoir."], "voice": "v/0.wav"},
    {"type": "phone", "lines": ["Tu es sur le chantier.", "Impossible de *décrocher*."],
     "clock": "10:42", "date": "mardi 14 mai",
     "notifs": [{"at": 2.5, "kind": "call", "title": "Appel manqué", "body": "06 12 •• •• 48"}], "voice": "v/1.wav"},
    {"type": "search", "lines": ["Il tape sur Google :"], "query": "électricien près de chez moi",
     "cards": [{"at": 1.6, "name": "Martin Électricité", "url": "www.martin-elec.fr", "rating": "4,8 · 37 avis"}],
     "ghost_at": 3.7,  "alert": {"at": 2.6, "text": "Et c'est lui qu'il appelle."}, "voice": "v/2.wav"},
    {"type": "statement", "bg": "dark", "lines": ["Il appelle", "*le premier*", "qu'il trouve."], "pill": "Pas toi.", "voice": "v/3.wav"},
    {"type": "solution", "checks": ["Tes réalisations en photos", "Visible sur Google", "Demandes de devis 24h/24"],
     "notif": {"at": 1.9, "title": "Nouvelle demande de devis", "body": "Rénovation salle de bain"}, "voice": "v/4.wav"},
    {"type": "cta", "lines": ["Toi, tu bosses.", "Ton site prend", "*les demandes*."], "voice": "v/5.wav"}
  ]
}
- "*mot*" = mot surligné en turquoise.
- Every "at" is in REAL seconds from the start of its scene. The voice of a scene starts at 0.1 s,
  so a word that starts at W ms in the voice clip happens at 0.1 + W/1000.
- Scene length is computed automatically from its voice clip (never cut the voice).
"""
import json, os, subprocess, sys, wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import GREEN, RED, SPEED, mux, render  # noqa: E402
from scenes import cta, hook, phone_scene, search_scene, solution, statement  # noqa: E402

VOICE_OFFSET = 0.1
TAIL = 0.35
MIN_DUR = {"hook": 2.2, "phone": 3.6, "search": 3.7, "statement": 2.4, "solution": 3.9, "cta": 3.6}
TYPING_END = 1.55  # real seconds: the search bar finishes typing here


def k(x):
    return float(x) * SPEED


def clip_len(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def build_scene(sc):
    t = sc["type"]
    ats = []
    if t == "hook":
        return hook(sc["lines"]), sc.get("bg", "dark"), ats
    if t == "statement":
        dark = sc.get("bg", "dark") == "dark"
        return statement(sc["lines"], sc.get("size", 100), dark=dark, small=sc.get("pill")), sc.get("bg", "dark"), ats
    if t == "phone":
        notifs = []
        for n in sc["notifs"]:
            call = n.get("kind", "call") == "call"
            notifs.append((k(n["at"]), n["title"], n["body"], RED if call else GREEN, "☎" if call else "✉"))
            ats.append(n["at"])
        return phone_scene(sc["lines"], notifs, sc.get("clock", "10:42"), sc.get("date", "mardi 14 mai")), "dark", ats
    if t == "search":
        cards = sc.get("cards", [])
        for c in cards:
            assert c["at"] >= TYPING_END, "cards must appear after the typing ends (>= %.2f s)" % TYPING_END
            ats.append(c["at"])
        ghost = sc.get("ghost_at")
        alert = sc.get("alert")
        if ghost:
            ats.append(ghost)
        if alert:
            ats.append(alert["at"])
        n = len(cards)
        bar_y = 430 if (ghost or n >= 3) else (560 if n == 2 else 640)
        cur = None
        if cards:
            if alert:
                click = k(alert["at"]) - 0.4
            else:
                last = max([c["at"] for c in cards] + ([ghost] if ghost else []))
                click = k(last) + 0.85
            move = max(k(cards[-1]["at"]) + 0.2, click - 0.65)
            cur = (move, max(click, move + 0.5))
            ats.append(cur[1] / SPEED)
        fn = search_scene(sc["lines"], sc["query"],
                          [(k(c["at"]), c["name"], c["url"], c.get("rating", "4,8 · 30 avis")) for c in cards],
                          ghost=k(ghost) if ghost else False,
                          after=(k(alert["at"]), alert["text"]) if alert else None,
                          bar_y=bar_y, cur=cur)
        return fn, "dark", ats
    if t == "solution":
        nt = sc["notif"]
        ats.append(nt["at"])
        kw = {}
        if sc.get("title"):
            kw["title"] = sc["title"]
        return solution(sc["checks"], (k(nt["at"]), nt["title"], nt["body"]), **kw), "light", ats
    if t == "cta":
        return cta(sc["lines"]), "dark", [2.75 / SPEED]
    raise ValueError("unknown scene type: %s" % t)


def main(spec_path, out_path):
    spec = json.load(open(spec_path))
    base = os.path.dirname(os.path.abspath(spec_path))
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    scenes, voices = [], []
    for sc in spec["scenes"]:
        fn, bg, ats = build_scene(sc)
        vp = sc.get("voice")
        vp = os.path.join(base, vp) if vp and not os.path.isabs(vp) else vp
        vlen = clip_len(vp) if vp else 0.0
        d = max(MIN_DUR[sc["type"]], VOICE_OFFSET + vlen + TAIL, (max(ats) + 0.7) if ats else 0)
        scenes.append((round(d, 2), bg, fn))
        voices.append(vp)
    total = sum(s[0] for s in scenes)
    render(scenes, out_path)
    # voice track
    sr = 44100
    track = np.zeros(int(sr * total), np.float32)
    acc = 0.0
    for (d, _, _), vp in zip(scenes, voices):
        if vp:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", vp, "-af", "loudnorm=I=-13:TP=-1.5", "-ac", "1",
                                  "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
            x = np.frombuffer(raw, np.float32)
            o = int(sr * (acc + VOICE_OFFSET))
            track[o:o + len(x)] += x[:len(track) - o]
        acc += d
    vpath = out_path[:-4] + ".voice.wav"
    with wave.open(vpath, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
    mux(out_path, extra_audio=vpath)
    for ext in (".video.mp4", ".sfx.wav", ".voice.wav", ".events.json"):
        try:
            os.remove(out_path[:-4] + ext)
        except FileNotFoundError:
            pass
    print(json.dumps({"out": out_path, "seconds": round(total, 2),
                      "scenes": [s[0] for s in scenes], "bytes": os.path.getsize(out_path)}))


def preview(spec_path, out_dir):
    """Render one still per scene (end of scene) to check the layout before the full render."""
    spec = json.load(open(spec_path))
    scenes, acc, times = [], 0.0, []
    for sc in spec["scenes"]:
        fn, bg, ats = build_scene(sc)
        d = max(MIN_DUR[sc["type"]], (max(ats) + 0.7) if ats else 0)
        scenes.append((d, bg, fn)); times.append(acc + d - 0.3); acc += d
    render(scenes, None, times, out_dir)
    print(out_dir)


if __name__ == "__main__":
    if sys.argv[1] == "--preview":
        preview(sys.argv[2], sys.argv[3])
    else:
        main(sys.argv[1], sys.argv[2])
