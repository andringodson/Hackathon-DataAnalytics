"""Synthesise the narration, lay out the timeline and mix the audio track.

Usage: python tts.py [voice] [rate]      e.g. python tts.py en-IN-NeerjaNeural +12%
Writes s??.mp3 (one per sentence), timeline.json and narration.wav.
"""
import asyncio
import json
import subprocess
import sys

import edge_tts

from narration import SECTIONS

VOICE = sys.argv[1] if len(sys.argv) > 1 else "en-IN-PrabhatNeural"
RATE = sys.argv[2] if len(sys.argv) > 2 else "+12%"
TITLE, GAP, SECTION_GAP, END = 3.2, 0.3, 0.6, 3.6   # seconds: title card, pause between lines / sections, end card


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(out.stdout.strip())


async def synthesise():
    items = []
    for si, (title, lines) in enumerate(SECTIONS):
        for text in lines:
            path = f"s{len(items):02d}.mp3"
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
            items.append({"section": si, "title": title, "text": text, "file": path, "dur": round(duration(path), 3)})
    return items


def main():
    items = asyncio.run(synthesise())
    t, prev = TITLE, None
    for it in items:
        if prev is not None:
            t += SECTION_GAP if it["section"] != prev else GAP
        it["start"] = round(t, 3)
        t += it["dur"]
        prev = it["section"]
    total = round(t + END, 3)
    json.dump({"items": items, "total": total, "voice": VOICE, "rate": RATE}, open("timeline.json", "w"), indent=1)

    # Place each sentence at its start time, then normalise loudness for speech.
    args = ["ffmpeg", "-y", "-v", "error"]
    for it in items:
        args += ["-i", it["file"]]
    delays = ";".join(f"[{n}]adelay={int(it['start'] * 1000)}:all=1[a{n}]" for n, it in enumerate(items))
    mix = "".join(f"[a{n}]" for n in range(len(items))) + f"amix=inputs={len(items)}:normalize=0,apad,atrim=0:{total},loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    subprocess.run(args + ["-filter_complex", f"{delays};{mix}", "-map", "[out]", "-ar", "48000", "-ac", "2", "narration.wav"], check=True)
    print(f"{len(items)} lines, {sum(i['dur'] for i in items):.1f}s of speech, video length {total:.1f}s")


main()
