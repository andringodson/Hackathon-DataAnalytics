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

        def glide(sel, off=80, ms=1500):
            pg.evaluate("([s, o, m]) => __glideTo(s, o, m)", [sel, off, ms])

        def click(sel):
            hover(sel, 0.5, 0.5)
            pg.wait_for_timeout(120)
            pg.click(sel)

        def to_delhi():
            # Hover the Delhi column on the dashboard's own 3D view; a custom camera fly-in stalled the headless renderer.
            pt = pg.evaluate("__proj(77.15, 28.6)")
            if pt:
                move(pt["x"], pt["y"] - 30)

        def js_click(sel):
            pg.evaluate("(s) => document.querySelector(s).click()", sel)

        shots = [
            (0.4, lambda: move(W * 0.66, H * 0.40, 20)),
            (2.7, lambda: pg.evaluate("__startShow()")),
            (3.4, lambda: move(W * 0.78, H * 0.30, 60)),
            (6.0, lambda: move(W * 0.55, H * 0.55, 50)),
            (8.3, lambda: glide(".kpis", 110, 1700)),
            (10.3, lambda: hover(".kpi:nth-child(1)")),
            (11.3, lambda: hover(".kpi:nth-child(2)")),
            (12.6, lambda: hover(".kpi:nth-child(3)")),
            (15.8, lambda: hover(".insight:nth-child(4)", 0.5, 0.35)),
            (19.4, lambda: hover(".kpi:nth-child(4)")),
            (22.6, lambda: glide("#overview", 70, 1600)),
            (24.6, lambda: point("growth", 2, "max")),
            # Our approach
            (28.7, lambda: glide("#quality", 70, 1900)),
            (31.2, lambda: hover(".anomaly:nth-child(2)")),
            (34.2, lambda: hover(".anomaly:nth-child(1)")),
            (38.6, lambda: glide("#cleaning", 120, 1400)),
            (40.6, lambda: hover("#cleaning tbody tr:nth-child(1)", 0.35, 0.5)),
            (43.4, lambda: hover("#cleaning tbody tr:nth-child(2)", 0.35, 0.5)),
            (46.6, lambda: hover("#cleaning tbody tr:nth-child(5)", 0.35, 0.5)),
            (49.9, lambda: glide("[data-chart=did]", "center", 1700)),
            (52.4, lambda: point("did", 3, 0)),
            (55.6, lambda: glide("[data-chart=logit]", "center", 1400)),
            (57.6, lambda: point("logit", 1, "min")),
            # Insights: Gen1 heat
            (60.4, lambda: glide("#failures", 70, 1700)),
            (63.4, lambda: point("heatmap", 0, "max")),
            (69.4, lambda: glide("[data-chart=chargetime]", 150, 1500)),
            (71.9, lambda: point("chargetime", 0, "max")),
            (75.8, lambda: point("stockout", 0, "max")),
            (78.9, lambda: point("stockout", 1, "max", -6)),
            (81.4, lambda: glide("[data-chart=heatmap]", 140, 1300)),
            (83.0, lambda: click("#city-filter [data-city='Delhi NCR']")),
            (84.0, lambda: click("#city-filter [data-city='Jaipur']")),
            (85.0, lambda: click("#city-filter [data-city='Hyderabad']")),
            (86.1, lambda: glide("#map-card", 130, 1400)),
            (87.7, lambda: click("#map-mode [data-mode='columns']")),
            (89.4, lambda: to_delhi()),
            # Insights: batteries
            (92.2, lambda: glide("[data-chart=lots]", "center", 1600)),
            (93.4, lambda: (js_click("#city-filter .all"), js_click("#map-mode [data-mode='points']"))),
            (94.6, lambda: point("lots", 0, "max")),
            (102.6, lambda: glide("#battery-stats", "center", 1300)),
            (104.6, lambda: hover("#battery-stats .mini:nth-child(3)")),
            (106.9, lambda: hover("#battery-stats .mini:nth-child(4)")),
            (108.8, lambda: glide("[data-chart=range]", 110, 1300)),
            (110.6, lambda: click("#pack-toggle [data-pack='3W_4.8kWh']")),
            # Insights: churn
            (112.9, lambda: glide("[data-chart=cohort]", 110, 1500)),
            (115.1, lambda: point("cohort", 0, "min")),
            (118.6, lambda: point("cohort", 1, "max")),
            (121.4, lambda: glide(".tiers", "center", 1400)),
            (123.2, lambda: hover(".tier-primary")),
            (126.4, lambda: hover(".tier-none")),
            # Recommendations
            (129.6, lambda: glide("#actions", 70, 1700)),
            (131.8, lambda: hover(".verdict:nth-child(1)", 0.5, 0.4)),
            (140.1, lambda: hover(".verdict:nth-child(2)", 0.5, 0.4)),
            (146.0, lambda: hover(".verdict:nth-child(3)", 0.5, 0.4)),
            (151.9, lambda: hover(".verdict:nth-child(4)", 0.5, 0.4)),
            (164.8, lambda: glide("#plan li:nth-child(4)", "center", 1500)),
            (166.8, lambda: hover("#plan li:nth-child(4)", 0.4, 0.5)),
            (172.3, lambda: pg.evaluate("__endCard()")),
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
    (HERE / "manifest.json").write_text(json.dumps({"t0": t0, "total": stop, "frames": manifest}))
    ts = [m[0] - t0 for m in manifest if m[0] >= t0]
    gaps = sorted(b - a for a, b in zip(ts, ts[1:]))
    print(f"{len(manifest)} frames, {len(ts) / stop:.1f} fps average, p95 gap {gaps[int(len(gaps) * .95)] * 1000:.0f} ms, max gap {gaps[-1] * 1000:.0f} ms")
    print("page errors:", errors or "none")


main()
