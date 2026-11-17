import json, re, subprocess, unicodedata, os

BASE = os.path.expanduser("~/workspace/bayt-wa-hikaya/mutanabbi-video")
TRIM = 0.28

def strip_diacritics(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

lines = json.load(open(f"{BASE}/script_lines.json"))

# silences from ffmpeg
out = subprocess.run(
    ["ffmpeg","-hide_banner","-nostats","-i",f"{BASE}/src/voice.wav",
     "-af","silencedetect=n=-38dB:d=0.25","-f","null","-"],
    capture_output=True, text=True).stderr
sil = re.findall(r"silence_start: ([\d.]+)\nsilence_end: ([\d.]+)", out)
# fallback parse line by line
if not sil:
    sil = re.findall(r"silence_start: ([\d.]+).*?silence_end: ([\d.]+)", out, re.S)
silences = [(float(a), float(b)) for a,b in sil]
print("silences:", len(silences))
for s,e in silences: print(f"  {s:.2f}-{e:.2f}  dur {e-s:.2f}")

total = 113.28 - TRIM  # 113.0
lengths = [len(strip_diacritics(l["text"]).replace(" ","")) for l in lines]
print("char lengths:", lengths, "sum", sum(lengths))
# proportional boundaries in trimmed time
bounds = [0.0]
acc = 0.0
for L in lengths[:-1]:
    acc += total * L / sum(lengths)
    bounds.append(acc)
bounds.append(total)
print("proportional bounds:", [round(b,2) for b in bounds])

# snap each interior boundary to nearest silence midpoint (within 2.0s)
gaps = [( (s+e)/2, s, e) for s,e in silences if s > 0.3]
snapped = [0.0]
for b in bounds[1:-1]:
    cand = min(gaps, key=lambda g: abs(g[0]-b))
    if abs(cand[0]-b) <= 0.6:
        snapped.append(round(cand[0],3))
    else:
        snapped.append(round(b,3))
snapped.append(round(total,3))
# enforce monotonic increasing with min 1.0s gaps
for i in range(1, len(snapped)):
    if snapped[i] <= snapped[i-1] + 0.8:
        snapped[i] = round(snapped[i-1] + 0.8, 3)
print("snapped bounds:", snapped)

timeline = []
for i,l in enumerate(lines):
    s, e = snapped[i], snapped[i+1]
    timeline.append({"id": l["id"], "kind": l["kind"], "text": l["text"],
                     "start": round(s,3), "end": round(e,3), "dur": round(e-s,3)})
for t in timeline:
    print(f"{t['id']:10s} {t['start']:7.2f} - {t['end']:7.2f}  ({t['dur']:.2f}s)  {t['text']}")
json.dump(timeline, open(f"{BASE}/build/timeline.json","w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("durations min/max:", min(t['dur'] for t in timeline), max(t['dur'] for t in timeline))
