"""Record the VoltRelay dashboard following the narration timeline.

Usage: python director.py [dashboard URL] [stop after N seconds, for test takes]
Frames come from Chrome's screencast (JPEG, with capture timestamps) and are appended to frames.bin with a
manifest, so assemble.py can rebuild exact timing and lay the narration over it.
"""
import base64
import json
import math
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://andringodson.github.io/Hackathon-DataAnalytics26/"
UNTIL = float(sys.argv[2]) if len(sys.argv) > 2 else None   # stop early (seconds) for test takes
HERE = Path(__file__).resolve().parent
TL = json.loads((HERE / "timeline.json").read_text())
# Frames are appended to one open file: thousands of small writes get stalled by real-time antivirus scanning.
BIN = open(HERE / "frames.bin", "wb")

W, H, DPR = 1600, 900, 1.2
manifest = []
events = []
state = {"last": -1}


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True, args=["--enable-gpu", "--use-angle=d3d11", "--ignore-gpu-blocklist", "--hide-scrollbars"])
        ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=DPR, color_scheme="dark")
        ctx.add_init_script("try { localStorage.setItem('vr-theme', 'dark') } catch (e) {}")
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)[:200]))
        pg.goto(URL, wait_until="networkidle")
        pg.wait_for_selector(".kpi")
        pg.add_script_tag(path=str(HERE / "overlay.js"))
        pg.evaluate("document.fonts.ready")

        # Build every chart behind the black cover so nothing is constructed on camera.
        page_h = pg.evaluate("document.documentElement.scrollHeight")
        for y in range(0, page_h, 450):
            pg.evaluate(f"scrollTo(0, {y})")
            pg.wait_for_timeout(180)
        pg.wait_for_function("[...document.querySelectorAll('[data-chart] .chart')].every(n => echarts.getInstanceByDom(n))", timeout=20000)
        pg.wait_for_timeout(1200)
        # Warm up the map behind the black cover: jump near it, pause, and wait for the first frame.
        pg.evaluate("scrollTo(0, document.getElementById('map-card').getBoundingClientRect().top + scrollY - 200)")
        pg.wait_for_timeout(400)
        pg.evaluate("dispatchEvent(new Event('scroll'))")
        pg.wait_for_selector("#map-card .map-wrap.ready", timeout=30000)
        pg.wait_for_timeout(1500)
        pg.evaluate("scrollTo(0, 0)")
        pg.wait_for_timeout(300)
        pg.evaluate("__resetReveals()")
        pg.mouse.move(W * 0.62, H * 0.42)
        pg.wait_for_timeout(2500)

        cdp = ctx.new_cdp_session(pg)

        def on_frame(ev):
            ts = ev["metadata"]["timestamp"]
            cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
            slot = int(ts * 30)                  # keep the first frame in each 1/30 s slot
            if slot == state["last"]:
                return
            state["last"] = slot
            data = base64.b64decode(ev["data"])
            manifest.append((ts, BIN.tell(), len(data)))
            BIN.write(data)

        cdp.on("Page.screencastFrame", on_frame)
        cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": int(W * DPR), "maxHeight": int(H * DPR), "everyNthFrame": 1})
        pg.wait_for_timeout(600)

        t0 = time.time()
        pg.evaluate("(items) => { __intro(); __captions(items); }", [{"start": i["start"], "dur": i["dur"], "title": i["title"], "text": i["text"]} for i in TL["items"] if i["text"] != "Thank you."])  # the end card says it

        def wait_until(t):
            while True:
                left = t - (time.time() - t0)
                if left <= 0:
                    return
                pg.wait_for_timeout(min(left * 1000, 50))

        def move(x, y, steps=None):
            if steps is None:
                cur = state.get("mouse", (x, y))
                steps = int(min(45, max(12, math.dist(cur, (x, y)) / 22)))
            pg.mouse.move(x, y, steps=steps)
            state["mouse"] = (x, y)

        def hover(sel, fx=0.5, fy=0.45):
            pt = pg.evaluate("([s, fx, fy]) => __box(s, fx, fy)", [sel, fx, fy])
            if pt:
                move(pt["x"], pt["y"])

        def point(chart, si, which="max", dy=0):
            pt = pg.evaluate("([c, s, w]) => __pt(c, s, w)", [chart, si, which])
            if pt:
                move(pt["x"], pt["y"] + dy)

        def log(kind, **extra):
            events.append({"t": round(time.time() - t0, 3), "kind": kind, **extra})

        def glide(sel, off=80, ms=1500):
            log("glide", ms=ms)
            pg.evaluate("([s, o, m]) => __glideTo(s, o, m)", [sel, off, ms])

        def click(sel):
            hover(sel, 0.5, 0.5)
            pg.wait_for_timeout(120)
            log("click")
            pg.click(sel)

        def to_delhi():
            # Hover the Delhi column on the dashboard's own 3D view; a custom camera fly-in stalled the headless renderer.
            pt = pg.evaluate("__proj(77.15, 28.6)")
            if pt:
                move(pt["x"], pt["y"] - 30)

        def js_click(sel):
            pg.evaluate("(s) => document.querySelector(s).click()", sel)

        # Shots are anchored to narration lines (index, fraction of the line), so they follow any voice's pacing.
        lines = TL["items"]

        def A(k, f):
            return f if k < 0 else lines[k]["start"] + f * lines[k]["dur"]

        shots = [
            (A(-1, 0.4), lambda: move(W * 0.66, H * 0.40, 20)),
            (A(-1, 2.7), lambda: (log("title_out"), pg.evaluate("__startShow()"))),
            (A(0, 0.024), lambda: move(W * 0.78, H * 0.30, 60)),
            (A(0, 0.330), lambda: move(W * 0.55, H * 0.55, 50)),
            (A(0, 0.600), lambda: glide(".kpis", 110, 1700)),
            (A(0, 0.836), lambda: hover(".kpi:nth-child(1)")),
            (A(0, 0.953), lambda: hover(".kpi:nth-child(2)")),
            (A(1, 0.059), lambda: hover(".kpi:nth-child(3)")),
            (A(1, 0.369), lambda: hover(".insight:nth-child(4)", 0.5, 0.35)),
            (A(1, 0.717), lambda: hover(".kpi:nth-child(4)")),
            (A(2, 0.0), lambda: glide("#overview", 70, 1600)),
            (A(2, 0.359), lambda: point("growth", 2, "max")),
            # Our approach
            (A(3, 0.0), lambda: glide("#quality", 70, 1900)),
            (A(3, 0.258), lambda: hover(".anomaly:nth-child(2)")),
            (A(3, 0.572), lambda: hover(".anomaly:nth-child(1)")),
            (A(4, 0.001), lambda: glide("#cleaning", 120, 1400)),
            (A(4, 0.183), lambda: hover("#cleaning tbody tr:nth-child(1)", 0.35, 0.5)),
            (A(4, 0.438), lambda: hover("#cleaning tbody tr:nth-child(2)", 0.35, 0.5)),
            (A(4, 0.729), lambda: hover("#cleaning tbody tr:nth-child(5)", 0.35, 0.5)),
            (A(5, 0.002), lambda: glide("[data-chart=did]", "center", 1700)),
            (A(5, 0.255), lambda: point("did", 3, 0)),
            (A(5, 0.578), lambda: glide("[data-chart=logit]", "center", 1400)),
            (A(5, 0.781), lambda: point("logit", 1, "min")),
            # Insights: Gen1 heat
            (A(6, 0.004), lambda: glide("#failures", 70, 1700)),
            (A(6, 0.348), lambda: point("heatmap", 0, "max")),
            (A(7, 0.002), lambda: glide("[data-chart=chargetime]", 150, 1500)),
            (A(7, 0.212), lambda: point("chargetime", 0, "max")),
            (A(7, 0.539), lambda: point("stockout", 0, "max")),
            (A(7, 0.800), lambda: point("stockout", 1, "max", -6)),
            (A(8, 0.0), lambda: glide("[data-chart=heatmap]", 140, 1300)),
            (A(8, 0.146), lambda: click("#city-filter [data-city='Delhi NCR']")),
            (A(8, 0.249), lambda: click("#city-filter [data-city='Jaipur']")),
            (A(8, 0.352), lambda: click("#city-filter [data-city='Hyderabad']")),
            (A(8, 0.466), lambda: glide("#map-card", 130, 1400)),
            (A(8, 0.631), lambda: click("#map-mode [data-mode='columns']")),
            (A(8, 0.806), lambda: to_delhi()),
            # Insights: batteries
            (A(9, 0.058), lambda: glide("[data-chart=lots]", "center", 1600)),
            (A(9, 0.169), lambda: (js_click("#city-filter .all"), js_click("#map-mode [data-mode='points']"))),
            (A(9, 0.280), lambda: point("lots", 0, "max")),
            (A(10, 0.0), lambda: glide("#battery-stats", "center", 1300)),
            (A(10, 0.193), lambda: hover("#battery-stats .mini:nth-child(3)")),
            (A(10, 0.422), lambda: hover("#battery-stats .mini:nth-child(4)")),
            (A(10, 0.611), lambda: glide("[data-chart=range]", 110, 1300)),
            (A(10, 0.790), lambda: click("#pack-toggle [data-pack='3W_4.8kWh']")),
            # Insights: churn
            (A(11, 0.0), lambda: glide("[data-chart=cohort]", 110, 1500)),
            (A(11, 0.540), lambda: point("cohort", 0, "min")),
            (A(12, 0.120), lambda: point("cohort", 1, "max")),
            (A(12, 0.356), lambda: glide(".tiers", "center", 1400)),
            (A(12, 0.507), lambda: hover(".tier-primary")),
            (A(12, 0.776), lambda: hover(".tier-none")),
            # Recommendations
            (A(13, 0.0), lambda: glide("#actions", 70, 1700)),
            (A(13, 0.211), lambda: hover(".verdict:nth-child(1)", 0.5, 0.4)),
            (A(14, 0.0), lambda: hover(".verdict:nth-child(2)", 0.5, 0.4)),
            (A(15, 0.0), lambda: hover(".verdict:nth-child(3)", 0.5, 0.4)),
            (A(16, 0.002), lambda: hover(".verdict:nth-child(4)", 0.5, 0.4)),
            (A(17, 0.0), lambda: glide("#plan li:nth-child(4)", "center", 1500)),
            (A(17, 0.241), lambda: hover("#plan li:nth-child(4)", 0.4, 0.5)),
            (A(18, -0.5), lambda: (log("end_card"), pg.evaluate("__endCard()"))),
        ]
        stop = UNTIL or TL["total"]
        for t, fn in shots:
            if t > stop:
                break
            wait_until(t)
            try:
                fn()
            except Exception as e:  # a missed shot must not abort the take
                errors.append(f"shot at {t}s: {str(e)[:160]}")
        wait_until(stop + 0.3)
        cdp.send("Page.stopScreencast")
        pg.wait_for_timeout(300)
        b.close()

    BIN.close()
    (HERE / "manifest.json").write_text(json.dumps({"t0": t0, "total": stop, "frames": manifest, "events": events}))
    ts = [m[0] - t0 for m in manifest if m[0] >= t0]
    gaps = sorted(b - a for a, b in zip(ts, ts[1:]))
    print(f"{len(manifest)} frames, {len(ts) / stop:.1f} fps average, p95 gap {gaps[int(len(gaps) * .95)] * 1000:.0f} ms, max gap {gaps[-1] * 1000:.0f} ms")
    print("page errors:", errors or "none")


main()
