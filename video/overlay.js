// Injected into the dashboard for recording: title and end cards, captions, a visible cursor and eased scrolling.
(() => {
  const css = `
  html { scroll-behavior: auto !important; }
  .to-top { display: none !important; }
  #vx-black { position: fixed; inset: 0; background: #000; z-index: 10000; transition: opacity .6s ease; }
  #vx-black.off { opacity: 0; pointer-events: none; }
  .vx-card { position: fixed; inset: 0; z-index: 9800; display: grid; place-items: center; text-align: center; pointer-events: none;
    transition: opacity .8s cubic-bezier(.22,1,.36,1), transform .8s cubic-bezier(.22,1,.36,1); }
  .vx-card.off { opacity: 0; transform: scale(.985); }
  .vx-card .in { display: grid; justify-items: center; gap: 18px; }
  .vx-card .mark { width: 92px; height: 92px; filter: drop-shadow(0 18px 40px rgba(42,58,168,.55)); }
  .vx-card .mark svg { width: 100%; height: 100%; display: block; }
  .vx-eyebrow { font: 600 14px/1 Inter, sans-serif; letter-spacing: .22em; text-transform: uppercase; color: #cdb27c; margin: 6px 0 0; }
  .vx-card h1 { font: 400 84px/1.02 "Instrument Serif", Georgia, serif; color: #fff; margin: 0; letter-spacing: 0; }
  .vx-card h1 em { font-style: italic; background: linear-gradient(100deg, #f3e6c4 10%, #c9a96e 60%, #a8884f); -webkit-background-clip: text; background-clip: text; color: transparent; padding-right: .06em; }
  .vx-sub { font: 400 22px/1.5 Inter, sans-serif; color: #c9cdea; margin: 0; max-width: 820px; }
  .vx-rule { width: 64px; height: 1px; background: linear-gradient(90deg, transparent, #c9a96e, transparent); margin: 6px 0; }
  .vx-by { font: 500 17px/1 Inter, sans-serif; color: #e6e8f5; letter-spacing: .04em; margin: 0; }
  .vx-links { display: grid; gap: 12px; margin-top: 8px; }
  .vx-links p { margin: 0; font: 400 19px/1.4 Inter, sans-serif; color: #dde1f4; }
  .vx-links span { display: inline-block; min-width: 190px; text-align: right; margin-right: 18px; font-weight: 600; font-size: 13px; letter-spacing: .16em; text-transform: uppercase; color: #cdb27c; }
  body.vx-intro .topbar, body.vx-intro main, body.vx-intro .progress { opacity: 0; }
  .topbar, main, .progress { transition: opacity .9s cubic-bezier(.22,1,.36,1); }
  body.vx-outro .topbar, body.vx-outro main, body.vx-outro .progress { opacity: 0; }
  #vx-cap { position: fixed; left: 50%; bottom: 34px; z-index: 9000; max-width: 1180px; width: max-content; padding: 13px 28px 15px; border-radius: 14px;
    background: rgba(3, 4, 14, .88); border: 1px solid rgba(201, 169, 110, .28); box-shadow: 0 24px 60px -24px #000, inset 0 1px 0 rgba(255,255,255,.04);
    color: #fff; font: 500 21px/1.45 Inter, sans-serif; text-align: center; opacity: 0; transform: translate(-50%, 10px);
    transition: opacity .35s ease, transform .35s cubic-bezier(.22,1,.36,1); pointer-events: none; }
  #vx-cap.on { opacity: 1; transform: translate(-50%, 0); }
  #vx-cap .sec { display: block; font: 600 11.5px/1 Inter, sans-serif; letter-spacing: .2em; text-transform: uppercase; color: #cdb27c; margin-bottom: 8px; }
  #vx-cursor { position: fixed; left: 0; top: 0; width: 24px; height: 24px; margin: -12px 0 0 -12px; border-radius: 50%; z-index: 9500; pointer-events: none;
    border: 1.5px solid rgba(241, 227, 189, .92); box-shadow: 0 0 0 5px rgba(42, 58, 168, .28), 0 0 22px rgba(201, 169, 110, .4); opacity: 0; transition: opacity .4s; }
  #vx-cursor.on { opacity: 1; }
  #vx-cursor::after { content: ""; position: absolute; left: 50%; top: 50%; width: 4px; height: 4px; margin: -2px; border-radius: 50%; background: #f1e3bd; }
  #vx-cursor .pulse { position: absolute; inset: -2px; border-radius: 50%; border: 2px solid rgba(241, 227, 189, .9); opacity: 0; }
  #vx-cursor.click .pulse { animation: vx-pulse .55s ease-out; }
  @keyframes vx-pulse { from { opacity: 1; transform: scale(.6); } to { opacity: 0; transform: scale(2.4); } }
  `;
  document.head.append(Object.assign(document.createElement("style"), { textContent: css }));
  const mark = document.querySelector(".brand-mark")?.innerHTML.replace(/vr-(tile|bolt)/g, "vx-$1") ?? "";

  const black = Object.assign(document.createElement("div"), { id: "vx-black" });
  const title = Object.assign(document.createElement("div"), { id: "vx-title", className: "vx-card" });
  title.innerHTML = `<div class="in"><div class="mark">${mark}</div>
    <p class="vx-eyebrow">Gradient Learnings · Data Analytics Hackathon ’26</p>
    <h1>VoltRelay Energy</h1>
    <p class="vx-sub">What is really driving service failures, rider churn and eroding margins, and what the next budget should fund.</p>
    <div class="vx-rule"></div><p class="vx-by">Andrin Godson</p></div>`;
  const end = Object.assign(document.createElement("div"), { id: "vx-end", className: "vx-card off" });
  end.innerHTML = `<div class="in"><div class="mark">${mark.replace(/vx-(tile|bolt)/g, "vy-$1")}</div>
    <h1><em>Thank you</em></h1><div class="vx-rule"></div>
    <div class="vx-links"><p><span>Live dashboard</span>andringodson.github.io/Hackathon-DataAnalytics26</p>
    <p><span>Notebook &amp; report</span>github.com/andringodson/Hackathon-DataAnalytics26</p></div></div>`;
  const cap = Object.assign(document.createElement("div"), { id: "vx-cap" });
  const cur = Object.assign(document.createElement("div"), { id: "vx-cursor" });
  cur.append(Object.assign(document.createElement("i"), { className: "pulse" }));
  document.body.append(black, title, end, cap, cur);
  document.body.classList.add("vx-intro");

  addEventListener("pointermove", (e) => { cur.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`; cur.classList.add("on"); }, { passive: true, capture: true });
  addEventListener("pointerdown", () => { cur.classList.remove("click"); void cur.offsetWidth; cur.classList.add("click"); }, { capture: true });

  // Capture the MapLibre instance when the dashboard lazy-loads the library, so the camera can be directed.
  let ml;
  Object.defineProperty(window, "maplibregl", { configurable: true, get: () => ml, set: (v) => {
    const Base = v.Map;
    v.Map = class extends Base { constructor(...a) { super(...a); window.__map = this; } };
    ml = v;
  } });
  window.__proj = (lng, lat) => { const m = window.__map; if (!m) return null; const p = m.project([lng, lat]), r = m.getContainer().getBoundingClientRect(); return { x: r.left + p.x, y: r.top + p.y }; };
  window.__fly = (o) => window.__map?.flyTo({ essential: true, ...o });

  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  let raf = 0;
  window.__glide = (y, ms = 1500) => {
    const max = document.documentElement.scrollHeight - innerHeight;
    const y0 = scrollY, dy = Math.max(0, Math.min(y, max)) - y0, t0 = performance.now();
    cancelAnimationFrame(raf);
    const f = (t) => { const k = Math.min(1, (t - t0) / ms); scrollTo(0, y0 + dy * ease(k)); if (k < 1) raf = requestAnimationFrame(f); };
    raf = requestAnimationFrame(f);
  };
  // off: pixels from the top of the viewport; "center" centres the element in the space above the captions.
  window.__glideTo = (sel, off = 80, ms = 1500) => {
    const el = document.querySelector(sel);
    if (!el) return false;
    const r = el.getBoundingClientRect();
    const o = off === "center" ? Math.max(70, (innerHeight - 130 - r.height) / 2 + 30) : off;
    window.__glide(r.top + scrollY - o, ms);
    return true;
  };
  window.__box = (sel, fx = 0.5, fy = 0.5) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: r.left + r.width * fx, y: r.top + r.height * fy };
  };
  // Screen position of a chart's data point: si = series index, which = "max" | "min" | data index.
  window.__pt = (id, si, which = "max") => {
    const node = document.querySelector(`[data-chart="${id}"] .chart`);
    const inst = node && echarts.getInstanceByDom(node);
    if (!inst) return null;
    const r = node.getBoundingClientRect();
    const opt = inst.getOption().series[si];
    const val = (v) => (v && typeof v === "object" ? (Array.isArray(v) ? v[v.length - 1] : Array.isArray(v.value) ? v.value[v.value.length - 1] : v.value) : v);
    const vals = opt.data.map(val);
    let di = which;
    if (which === "max" || which === "min") {
      di = 0;
      vals.forEach((v, i) => { if (v != null && (vals[di] == null || (which === "max" ? v > vals[di] : v < vals[di]))) di = i; });
    }
    const data = inst.getModel().getSeriesByIndex(si).getData();
    const l = data.getItemLayout(di);
    let x, y;
    if (l && l.width != null) { x = l.x + l.width / 2; y = l.y + l.height * 0.4; }
    else if (Array.isArray(l)) { [x, y] = l; }
    else {
      const raw = opt.data[di];
      const v = raw && typeof raw === "object" && !Array.isArray(raw) ? raw.value : raw;
      [x, y] = inst.convertToPixel({ seriesIndex: si }, Array.isArray(v) ? v.slice(0, 2) : [di, v]);
    }
    return { x: r.left + x, y: r.top + y };
  };
  // After the warm-up pass, hide revealed cards again and re-arm the cascade so it still plays on camera.
  window.__resetReveals = () => {
    const els = [...document.querySelectorAll(".reveal.in")];
    els.forEach((n) => { n.style.transition = "none"; n.classList.remove("in"); });
    void document.body.offsetWidth;
    els.forEach((n) => { n.style.transition = ""; });
    const io = new IntersectionObserver((entries) => {
      entries.filter((e) => e.isIntersecting).forEach(({ target: n }, i) => {
        io.unobserve(n);
        const d = Math.min(i, 5) * 70;
        if (d) { n.style.transitionDelay = `${d}ms`; setTimeout(() => { n.style.transitionDelay = ""; }, d + 900); }
        n.classList.add("in");
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    els.forEach((n) => io.observe(n));
  };
  window.__intro = () => document.getElementById("vx-black").classList.add("off");
  window.__startShow = () => {
    document.getElementById("vx-title").classList.add("off");
    document.body.classList.remove("vx-intro");
    // Replay the hero entrance and the KPI count-up for the recording.
    document.querySelectorAll(".hero-inner > *").forEach((n) => { n.style.animation = "none"; void n.offsetWidth; n.style.animation = ""; });
    document.querySelectorAll(".kpi-value").forEach((n, i) => {
      const m = n.textContent.match(/^([^\d−-]*)([\d.]+)(\D*)$/);
      if (!m || i > 2) return;
      const target = +m[2], dec = (m[2].split(".")[1] ?? "").length, t0 = performance.now();
      const step = (t) => { const k = Math.min(1, (t - t0) / 1300), e = 1 - Math.pow(1 - k, 3); n.textContent = `${m[1]}${(target * e).toFixed(dec)}${m[3]}`; if (k < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    });
  };
  window.__endCard = () => { document.body.classList.add("vx-outro"); document.getElementById("vx-end").classList.remove("off"); cap.classList.remove("on"); cur.classList.remove("on"); };
  // Captions run on the page's own clock so they stay locked to the narration.
  window.__captions = (items) => {
    items.forEach((it, i) => {
      setTimeout(() => {
        cap.classList.remove("on");
        setTimeout(() => { cap.innerHTML = ""; cap.append(Object.assign(document.createElement("span"), { className: "sec", textContent: it.title }), document.createTextNode(it.text)); cap.classList.add("on"); }, 160);
      }, Math.max(0, it.start * 1000 - 160));
      // Hide only after the last line or before a long pause, so consecutive lines swap without a gap.
      const next = items[i + 1];
      if (!next || next.start - (it.start + it.dur) > 0.7) setTimeout(() => cap.classList.remove("on"), (it.start + it.dur) * 1000 + 250);
    });
  };
})();
