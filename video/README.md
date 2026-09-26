# Three-minute video

**Watch or download:** [VoltRelay_3min_video.mp4](https://github.com/andringodson/Hackathon-DataAnalytics26/releases/download/video-v1/VoltRelay_3min_video.mp4) (1920×1080, 2:58, H.264 + AAC, 64 MB), also on the [release page](https://github.com/andringodson/Hackathon-DataAnalytics26/releases/tag/video-v1).

The video follows [`report/video_script.md`](../report/video_script.md). It is a narrated walkthrough of the live dashboard: every chart, tooltip, filter and map view is recorded from the real site, not mocked up. Captions are burned in.

## How it is made

| Step | File | What it does |
|---|---|---|
| 1 | [`narration.py`](narration.py) | The script as spoken lines, grouped into the four sections. |
| 2 | [`tts.py`](tts.py) | Synthesises each line with a Microsoft neural voice (via `edge-tts`), lays out the timeline and mixes a loudness-normalised narration track. |
| 3 | [`overlay.js`](overlay.js) | Injected into the dashboard while recording: title and end cards, captions on the page's own clock, a visible cursor and eased scrolling. |
| 4 | [`director.py`](director.py) | Opens the dashboard in Edge at 1920×1080 and plays a timed shot list against the narration: scrolls, hovers the exact data points discussed, filters to the three hot cities and switches the map to 3D. It captures frames through Chrome's screencast. |
| 5 | [`assemble.py`](assemble.py) | Rebuilds exact frame timing from the capture timestamps, adds the narration and encodes the MP4. |

To rebuild (Windows or macOS with Microsoft Edge and ffmpeg installed):

```bash
pip install edge-tts playwright
cd video
python tts.py en-IN-PrabhatNeural +12%     # any edge-tts voice, e.g. en-IN-NeerjaNeural
python director.py                         # about 4 minutes; uses the live dashboard
python assemble.py VoltRelay_3min_video.mp4
```

To narrate it in your own voice, record over the same timeline (`timeline.json` lists when each line starts) and pass your recording to `assemble.py` as `narration.wav`.
