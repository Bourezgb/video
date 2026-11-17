#!/usr/bin/env python3
"""Assemble the Mutanabbi video: zoompan segments -> concat -> loudnorm mix -> phone + SRT + contact sheet."""
import json, os, subprocess, sys
from PIL import Image

BASE = os.path.expanduser("~/workspace/bayt-wa-hikaya/mutanabbi-video")
BUILD = f"{BASE}/build"
FINAL = f"{BASE}/final"
os.makedirs(f"{BUILD}/segs", exist_ok=True)
os.makedirs(FINAL, exist_ok=True)

def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)

timeline = json.load(open(f"{BUILD}/timeline.json"))
segs = []
for i, line in enumerate(timeline):
    dur = line["dur"]
    frames = max(30, int(round(dur * 30)))
    seg = f"{BUILD}/segs/{i+1:02d}_{line['id']}.mp4"
    still = f"{BUILD}/stills/{i+1:02d}_{line['id']}.jpg"
    if not os.path.exists(seg):
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", still,
             "-vf", f"zoompan=z='min(zoom+0.0004,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30",
             "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", seg])
    segs.append(seg)
# end card, 4.5s, very slight push-in
end = f"{BUILD}/segs/28_endcard.mp4"
if not os.path.exists(end):
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", f"{BUILD}/stills/28_endcard.jpg",
         "-vf", "zoompan=z='min(zoom+0.0002,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=135:s=1080x1920:fps=30",
         "-t", "4.5", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", end])
segs.append(end)

with open(f"{BUILD}/concat.txt", "w") as f:
    for s in segs:
        f.write(f"file '{s}'\n")
run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{BUILD}/concat.txt",
     "-c", "copy", f"{BUILD}/video_silent.mp4"])

# ---- audio: mix voice (trimmed, padded to 117.5s) + music, two-pass loudnorm ----
# pass 1: measure
meas = subprocess.run(
    ["ffmpeg", "-i", f"{BUILD}/voice_trim.wav", "-i", f"{BUILD}/music.wav",
     "-filter_complex",
     "[0:a]aresample=44100,apad=whole_dur=117.5[voice];"
     "[1:a]volume=0.16[mus];"
     "[voice][mus]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
     "-f", "null", "-"],
    capture_output=True, text=True)
import re
m = re.search(r"\{[^}]*\}", meas.stderr[meas.stderr.rfind("Parsed_loudnorm"):])
stats = json.loads(m.group(0)) if m else {}
print("loudnorm pass1:", stats)
lin = "linear=true" if stats.get("input_i") else ""
loudnorm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:{lin}"
            f":measured_I={stats.get('input_i','-14')}:measured_TP={stats.get('input_tp','-1.5')}"
            f":measured_LRA={stats.get('input_lra','11')}:measured_thresh={stats.get('input_thresh','-34')}"
            f":offset={stats.get('target_offset','0')}")
run(["ffmpeg", "-y", "-v", "error", "-i", f"{BUILD}/voice_trim.wav", "-i", f"{BUILD}/music.wav",
     "-filter_complex",
     f"[0:a]aresample=44100,apad=whole_dur=117.5[voice];"
     f"[1:a]volume=0.16[mus];"
     f"[voice][mus]amix=inputs=2:duration=first:dropout_transition=0,{loudnorm}[aout]",
     "-map", "[aout]", "-c:a", "aac", "-b:a", "160k", f"{BUILD}/mix.m4a"])

# ---- mux ----
run(["ffmpeg", "-y", "-v", "error", "-i", f"{BUILD}/video_silent.mp4", "-i", f"{BUILD}/mix.m4a",
     "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
     "-movflags", "+faststart", f"{FINAL}/mutanabbi-albayt.mp4"])
# phone version
run(["ffmpeg", "-y", "-v", "error", "-i", f"{FINAL}/mutanabbi-albayt.mp4",
     "-vf", "scale=720:1280", "-c:v", "libx264", "-preset", "medium",
     "-b:v", "400k", "-maxrate", "500k", "-bufsize", "1000k",
     "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
     f"{FINAL}/mutanabbi-albayt-phone.mp4"])

# ---- SRT ----
def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms//3600000:02d}:{(ms//60000)%60:02d}:{(ms//1000)%60:02d},{ms%1000:03d}"

with open(f"{FINAL}/mutanabbi-albayt.srt", "w", encoding="utf-8") as f:
    for i, line in enumerate(timeline, 1):
        f.write(f"{i}\n{srt_time(line['start'])} --> {srt_time(line['end'])}\n{line['text']}\n\n")

# ---- contact sheet: 28 stills, 4 cols x 7 rows at 270x480 ----
cols, rows, tw, th = 4, 7, 270, 480
sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
files = sorted(os.listdir(f"{BUILD}/stills"))
for k, fn in enumerate(files):
    im = Image.open(f"{BUILD}/stills/{fn}").resize((tw, th))
    sheet.paste(im, ((k % cols) * tw, (k // cols) * th))
sheet.save(f"{BUILD}/contact_sheet.jpg", quality=85)
print("contact sheet:", f"{BUILD}/contact_sheet.jpg")
print("DONE")
