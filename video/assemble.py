"""Turn captured frames + narration into an MP4 with exact timing."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "VoltRelay_3min_video.mp4"
m = json.loads((HERE / "manifest.json").read_text())
t0, total, raw = m["t0"], m["total"], m["frames"]
# Split the capture file back into numbered JPEGs (only the frames the timeline uses).
FR = HERE / "frames"
FR.mkdir(exist_ok=True)
for old in FR.glob("*.jpg"):
    old.unlink()
blob = (HERE / "frames.bin").read_bytes()
frames = []
for n, (ts, off, size) in enumerate(raw):
    if ts >= t0 + total:
        break
    name = f"f{n:06d}.jpg"
    frames.append((ts, name))
    if ts >= t0 - 1:
        (FR / name).write_bytes(blob[off:off + size])

# Timeline position of each frame; the last frame captured before t0 covers the very start.
before = [f for f in frames if f[0] < t0]
after = [f for f in frames if t0 <= f[0] < t0 + total]
seq = ([(0.0, before[-1][1])] if before else []) + [(ts - t0, name) for ts, name in after]
lines = []
for i, (t, name) in enumerate(seq):
    nxt = seq[i + 1][0] if i + 1 < len(seq) else total
    if nxt <= t:
        continue
    lines += [f"file 'frames/{name}'", f"duration {min(nxt, total) - t:.4f}"]
lines.append(f"file 'frames/{seq[-1][1]}'")
(HERE / "frames.txt").write_text("\n".join(lines) + "\n")

audio = HERE / "narration.wav"
cmd = ["ffmpeg", "-y", "-v", "error", "-stats", "-f", "concat", "-safe", "0", "-i", str(HERE / "frames.txt")]
if audio.exists():
    cmd += ["-i", str(audio)]
# Fade up from black onto the title card, and out at the very end.
fades = f"fade=t=in:st=1.2:d=0.7,fade=t=out:st={total - 1.2:.2f}:d=1.2"
cmd += ["-vf", f"fps=30,scale=1920:1080:flags=lanczos,{fades},format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
        "-t", f"{total:.3f}"]
if audio.exists():
    cmd += ["-c:a", "aac", "-b:a", "192k"]
cmd += ["-movflags", "+faststart", str(OUT)]
subprocess.run(cmd, check=True, cwd=HERE)
info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height,r_frame_rate", "-of", "json", str(OUT)],
                      capture_output=True, text=True).stdout
print(OUT, json.dumps(json.loads(info)))
