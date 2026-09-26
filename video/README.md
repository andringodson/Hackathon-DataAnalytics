# Three-minute video

**Watch or download:** [VoltRelay_3min_video.mp4](https://github.com/andringodson/Hackathon-DataAnalytics26/releases/download/video-v1/VoltRelay_3min_video.mp4) (**4K UHD 3840×2160**, 30 fps, 2:58, H.264 + 320 kbps AAC, 162 MB), also on the [release page](https://github.com/andringodson/Hackathon-DataAnalytics26/releases/tag/video-v1).

The video follows [`report/video_script.md`](../report/video_script.md), reworded to be spoken rather than read. It is a narrated walkthrough of the live dashboard: every chart, tooltip, filter and map view is recorded from the real site, not mocked up. Captions are burned in.

**Sound:**
- **Narration:** Microsoft's conversational neural voice *Andrew* (`en-US-AndrewMultilingualNeural`), with deliberate pauses before key points and slower, lower delivery on the lines that matter.
- **Score:** an original ambient piece, synthesised in code, so there is nothing to license. It swells on the title and end cards and dips automatically under the voice, which sits about 19 dB above it.
- **Effects:** soft whooshes follow each scroll, ticks mark each click, and chimes ring on the title and end cards.
- **Delivery:** the 1080p master is upscaled to 4K with a Lanczos filter. The soundtrack is mastered to the streaming standard (−14 LUFS integrated, −1 dB true peak) with gentle bus compression and a two-pass linear loudness normalisation, then encoded as 320 kbps AAC.

## How it is made

| Step | File | What it does |
|---|---|---|
| 1 | [`narration.py`](narration.py) | The script as spoken lines, with pause and emphasis markup, grouped into the four sections. |
| 2 | [`tts.py`](tts.py) | Synthesises each line with a Microsoft neural voice (via `edge-tts`), adds the pauses and emphasis, lays out the timeline and mixes a loudness-normalised voice track. |
| 3 | [`overlay.js`](overlay.js) | Injected into the dashboard while recording: title and end cards, captions on the page's own clock, a visible cursor and eased scrolling. |
| 4 | [`director.py`](director.py) | Opens the dashboard in Edge at 1920×1080 and plays a shot list anchored to the narration lines: scrolls, hovers the exact data points discussed, filters to the three hot cities and switches the map to 3D. It captures frames through Chrome's screencast and logs each scroll and click. |
| 5 | [`sound.py`](sound.py) | Composes the score, places the sound effects on the logged scrolls and clicks, and mixes everything under the voice. |
| 6 | [`assemble.py`](assemble.py) | Rebuilds exact frame timing from the capture timestamps, adds the soundtrack and encodes the MP4. |

To rebuild (Windows or macOS with Microsoft Edge and ffmpeg installed):

```bash
pip install edge-tts playwright numpy scipy
cd video
python tts.py en-US-AndrewMultilingualNeural -3%   # any edge-tts voice, e.g. en-US-AvaMultilingualNeural
python director.py                                 # about 5 minutes; uses the live dashboard
python sound.py                                    # score, effects and final mix
python assemble.py VoltRelay_3min_video.mp4
```

To narrate it in your own voice, record each line to fit the timeline (`timeline.json` lists when each line starts), save the result as `narration.wav`, then run `sound.py` and `assemble.py`.
