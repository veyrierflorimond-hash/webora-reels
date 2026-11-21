#!/usr/bin/env python3
"""Add the background music to an already rendered Reel (same mix as build_reel.py).

Usage:  python3 engine/add_music.py in.mp4 out.mp4 [variant]
The existing audio (voice + sound effects) is kept as is and drives the ducking of the music.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import music  # noqa: E402

src, dst = sys.argv[1], sys.argv[2]
variant = int(sys.argv[3]) if len(sys.argv) > 3 else 0
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                           capture_output=True, text=True, check=True).stdout)
mpath = dst[:-4] + ".music.wav"
music.write(mpath, music.make(dur, 112, variant))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-i", mpath, "-filter_complex",
                "[1:a]loudnorm=I=-27:TP=-6,aresample=44100[m];[0:a]asplit[a][key];"
                "[m][key]sidechaincompress=threshold=0.05:ratio=4:attack=30:release=350[md];"
                "[a][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false[out]",
                "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", dst], check=True)
os.remove(mpath)
print(dst, "variant", variant)
