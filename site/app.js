const V = new URL(import.meta.url).searchParams.get("v") ?? "dev";
const D = await (await fetch(`data.json?v=${V}`)).json();
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
const FONT = 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif';
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const el = (tag, props = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k === "style") n.style.cssText = v;
    else n.setAttribute(k, v);
  }
  for (const k of kids) if (k != null) n.append(k);
  return n;
};

// ---------- formatting ----------
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const mLabel = (iso) => { const [y, m] = iso.split("-"); return `${MONTHS[+m - 1]} ${y.slice(2)}`; };
const wLabel = (iso) => { const [, m, d] = iso.split("-"); return `${+d} ${MONTHS[+m - 1]}`; };
const pct = (v, d = 1) => (v == null ? "–" : `${(v * 100).toFixed(d)}%`);
const inr = (v, d = 1) => (v == null ? "–" : `${v < 0 ? "−" : ""}₹${Math.abs(v).toFixed(d)}`);
const compact = (v) => (Math.abs(v) >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : Math.abs(v) >= 1e3 ? `${(v / 1e3).toFixed(1)}K` : `${Math.round(v)}`);
const int = (v) => Math.round(v).toLocaleString("en-IN");

// ---------- theme tokens ----------
function isDark() {
  const t = document.documentElement.dataset.theme;
  return t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
}
function tokens() {
  const cs = getComputedStyle(document.documentElement);
  const v = (n) => cs.getPropertyValue(n).trim();
  const dark = isDark();
  return {
    dark, surface: v("--surface"), surface2: v("--surface-2"), ink: v("--ink"), ink2: v("--ink-2"), muted: v("--muted"), line: v("--line"), axis: v("--axis"),
    s1: v("--s1"), s2: v("--s2"), s3: v("--s3"), s4: v("--s4"),
    ramp: dark ? ["#104281", "#1c5cab", "#2a78d6", "#5598e7", "#86b6ef", "#b7d3f6"] : ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
    wash: dark ? "rgba(255,255,255,0.05)" : "rgba(11,11,11,0.045)",
  };
}
let T = tokens();
const GEN = () => ({ Gen1: T.s2, Gen2: T.s1, Gen3: T.s3 });

// ---------- shared chart pieces ----------
function base(extra = {}) {
  return {
    animation: !REDUCED, animationDuration: 700, animationEasing: "cubicOut",
    textStyle: { fontFamily: FONT, color: T.ink2 },
    grid: { left: 4, right: 18, top: 40, bottom: 4, containLabel: true },
    tooltip: {
      confine: true, backgroundColor: T.surface, borderColor: T.line, borderWidth: 1, padding: [8, 12],
      textStyle: { color: T.ink, fontSize: 12, fontFamily: FONT }, extraCssText: "border-radius:10px;box-shadow:0 10px 30px -10px rgba(0,0,0,.35);",
    },
    legend: { top: 0, left: 0, itemGap: 16, itemWidth: 16, itemHeight: 3, icon: "roundRect", textStyle: { color: T.ink2, fontSize: 12 } },
    ...extra,
  };
}
const barLegend = { itemWidth: 10, itemHeight: 10, icon: "roundRect" };
const xCat = (data, extra = {}) => ({
  type: "category", data, boundaryGap: extra.boundaryGap ?? true, axisLine: { lineStyle: { color: T.axis } }, axisTick: { show: false },
  axisLabel: { color: T.muted, fontSize: 11, hideOverlap: true }, ...extra,
});
const yVal = (extra = {}) => ({
  type: "value", splitLine: { lineStyle: { color: T.line, type: "solid" } }, axisLine: { show: false }, axisTick: { show: false },
  axisLabel: { color: T.muted, fontSize: 11 }, nameTextStyle: { color: T.muted, fontSize: 11 }, ...extra,
});
const line = (name, data, color, extra = {}) => ({
  type: "line", name, data, symbol: "circle", symbolSize: 8, showSymbol: false, connectNulls: false,
  lineStyle: { width: 2, color, cap: "round", join: "round" }, itemStyle: { color, borderColor: T.surface, borderWidth: 2 }, emphasis: { disabled: true }, ...extra,
});
const bar = (name, data, color, extra = {}) => ({
  type: "bar", name, data, barMaxWidth: 24, itemStyle: { color, borderRadius: [4, 4, 0, 0] }, emphasis: { itemStyle: { opacity: 0.85 } }, ...extra,
});
const vline = (x, label) => ({ xAxis: x, label: { formatter: label, position: "insideEndTop", color: T.ink2, fontSize: 10.5, fontFamily: FONT }, lineStyle: { color: T.muted, width: 1, type: "solid" } });
const markLines = (items) => ({ symbol: "none", silent: true, animation: false, data: items });

function row(color, name, value, key = "line") {
  const k = key === "dot"
    ? `<i style="display:inline-block;width:9px;height:9px;border-radius:50%;background:${color}"></i>`
    : `<i style="display:inline-block;width:12px;height:3px;border-radius:2px;background:${color}"></i>`;
  return `<div style="display:flex;justify-content:space-between;gap:18px;align-items:center;line-height:1.7">
    <span style="display:inline-flex;align-items:center;gap:7px;color:${T.ink2}">${k}${esc(name)}</span><b style="color:${T.ink};font-weight:600">${esc(value)}</b></div>`;
}
const head = (s) => `<div style="font-weight:600;color:${T.ink};margin-bottom:2px">${esc(s)}</div>`;
function axisTip(fmt, key = "line") {
  return (ps) => {
    ps = Array.isArray(ps) ? ps : [ps];
    let h = head(ps[0].axisValueLabel ?? ps[0].name);
    for (const p of ps) {
      const v = Array.isArray(p.value) ? p.value[p.value.length - 1] : p.value;
      if (v == null || p.seriesType === "custom") continue;
      h += row(p.color, p.seriesName, fmt(v, p), key);
    }
    return h;
  };
}

// ---------- chart registry ----------
const REG = {};
const live = new Map();

function register(id, option, table, opts = {}) { REG[id] = { option, table, ...opts }; }

function setupCard(fig) {
  const id = fig.dataset.chart;
  const title = $("h3", fig)?.textContent ?? id;
  const chart = el("div", { class: "chart", role: "img", "aria-label": `${title} chart. Use the Table button for the underlying values.` });
  if (REG[id]?.height) chart.style.blockSize = `${REG[id].height}px`;
  const tableBox = el("div", { class: "table-view", hidden: "" });
  const tBtn = el("button", { class: "ghost", type: "button", "aria-pressed": "false" });
  tBtn.innerHTML = '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M9 10v10"/></svg>';
  tBtn.append(document.createTextNode("Table"));
  const cBtn = el("button", { class: "ghost", type: "button" });
  cBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>';
  cBtn.append(document.createTextNode("CSV"));
  const actions = el("div", { class: "card-actions" }, tBtn, cBtn);
  fig.append(chart, tableBox, actions);
  tBtn.addEventListener("click", () => {
    const open = tBtn.getAttribute("aria-pressed") === "true";
    tBtn.setAttribute("aria-pressed", String(!open));
    if (open) tableBox.hidden = true;
    else { tableBox.replaceChildren(buildTable(REG[id].table())); tableBox.hidden = false; }
  });
  cBtn.addEventListener("click", () => downloadCsv(REG[id].table(), `voltrelay-${id}.csv`));
  return chart;
}

function render(id) {
  const fig = $(`[data-chart="${id}"]`);
  if (!fig || !REG[id]) return;
  const node = $(".chart", fig);
  live.get(id)?.inst.dispose();
  const inst = echarts.init(node, null, { renderer: "svg" });
  inst.setOption(REG[id].option());
  live.set(id, { inst });
  const box = $(".table-view", fig);
  if (!box.hidden) box.replaceChildren(buildTable(REG[id].table()));
}
const refresh = (...ids) => ids.forEach((id) => live.has(id) && render(id));

function buildTable({ cols, rows }) {
  const t = el("table");
  const thead = el("thead"), tr = el("tr");
  cols.forEach((c) => tr.append(el("th", { class: c.num ? "num" : "", text: c.label })));
  thead.append(tr);
  const tb = el("tbody");
  rows.forEach((r) => {
    const row = el("tr");
    cols.forEach((c) => row.append(el("td", { class: c.num ? "num" : "", text: c.fmt ? c.fmt(r[c.key], r) : r[c.key] ?? "–" })));
    tb.append(row);
  });
  t.append(thead, tb);
  return t;
}
function downloadCsv({ cols, rows }, name) {
  const q = (v) => (/[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v ?? ""));
  const text = [cols.map((c) => q(c.label)).join(","), ...rows.map((r) => cols.map((c) => q(r[c.key])).join(","))].join("\n");
  const a = el("a", { href: URL.createObjectURL(new Blob([text], { type: "text/csv" })), download: name });
  document.body.append(a); a.click(); a.remove();
}

// ================= DATA PREP =================
const M = D.monthly_network;
const months = M.map((r) => mLabel(r.month));
const CITIES = [...new Set(D.monthly_city.map((r) => r.city))].sort();
const state = { cities: new Set(CITIES), pack: "2W_2.1kWh", factor: D.retention_lifts[0].factor };

// ================= KPIs =================
function kpis() {
  const avg = (rows, k) => rows.reduce((a, r) => a + r[k], 0) / rows.length;
  const q1 = M.slice(0, 3), q6 = M.slice(-3);
  const items = [
    { label: "Completed swaps / month", key: "completed", fmt: (v) => compact(v), good: true, ratio: true },
    { label: "Revenue / month", key: "revenue", fmt: (v) => `₹${compact(v)}`, good: true, ratio: true },
    { label: "Service failures / month", key: "failures", fmt: (v) => compact(v), good: false, ratio: true },
    { label: "Contribution / swap after wear", key: "per_swap_cm2", fmt: (v) => inr(v), good: true, ratio: false },
  ];
  const grid = $("#kpis");
  for (const it of items) {
    const a = avg(q1, it.key), b = avg(q6, it.key);
    const up = b > a;
    const deltaText = it.ratio ? `${(b / a).toFixed(1)}× vs Q1 2024` : `${inr(b - a)} vs Q1 2024`.replace("₹", up ? "+₹" : "₹");
    const cls = up === it.good ? "up-good" : "up-bad";
    const arrow = up ? '<svg viewBox="0 0 12 12"><path d="M6 10V2M2.5 5.5 6 2l3.5 3.5"/></svg>' : '<svg viewBox="0 0 12 12"><path d="M6 2v8M2.5 6.5 6 10l3.5-3.5"/></svg>';
    const vals = M.map((r) => r[it.key]);
    const min = Math.min(...vals), max = Math.max(...vals);
    const pts = vals.map((v, i) => `${(i / (vals.length - 1)) * 92 + 2},${30 - ((v - min) / (max - min || 1)) * 26}`).join(" ");
    const last = pts.split(" ").pop().split(",");
    const valueEl = el("span", { class: "kpi-value", text: it.fmt(b) });
    const delta = el("span", { class: `delta ${cls}` });
    delta.innerHTML = arrow;
    delta.append(document.createTextNode(deltaText));
    const spark = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    spark.setAttribute("class", "spark"); spark.setAttribute("viewBox", "0 0 96 32"); spark.setAttribute("aria-hidden", "true");
    spark.innerHTML = `<polyline points="${pts}" fill="none" stroke="var(--muted)" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="${last[0]}" cy="${last[1]}" r="3" fill="var(--s1)" stroke="var(--surface)" stroke-width="1.5"/>`;
    grid.append(el("article", { class: "kpi reveal" }, el("span", { class: "kpi-label", text: it.label }), valueEl, el("div", { class: "kpi-foot" }, delta, spark)));
    if (!REDUCED && it.ratio) countUp(valueEl, b, it.fmt);
  }
}
function countUp(node, target, fmt) {
  const t0 = performance.now(), dur = 1100;
  const step = (t) => {
    const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
    node.textContent = fmt(target * e);
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// ================= 01 OVERVIEW =================
register("growth", () => {
  const idx = (k) => M.map((r) => +((r[k] / M[0][k]) * 100).toFixed(1));
  return base({
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } }, formatter: axisTip((v) => v.toFixed(0)) },
    xAxis: xCat(months, { boundaryGap: false }), yAxis: yVal({ min: 0 }),
    series: [line("Completed swaps", idx("completed"), T.s1), line("Revenue", idx("revenue"), T.s3), line("Failures", idx("failures"), T.s2)],
  });
}, () => ({ cols: [{ key: "month", label: "Month" }, { key: "completed", label: "Completed", num: true }, { key: "revenue", label: "Revenue ₹", num: true, fmt: (v) => int(v) }, { key: "failures", label: "Failures", num: true }], rows: M }));

register("failrate", () => base({
  tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } }, formatter: axisTip((v) => pct(v)) },
  legend: { show: false },
  xAxis: xCat(months, { boundaryGap: false }), yAxis: yVal({ axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => pct(v, 0) } }),
  series: [line("Failure rate", M.map((r) => r.failure_rate), T.s1, {
    showSymbol: true, areaStyle: { color: T.s1, opacity: 0.1 },
    markArea: { silent: true, itemStyle: { color: T.wash }, label: { color: T.muted, fontSize: 10.5, position: "insideBottom" },
      data: [[{ name: "Summer", xAxis: "Apr 24" }, { xAxis: "Jun 24" }], [{ name: "Summer", xAxis: "Apr 25" }, { xAxis: "Jun 25" }]] },
  })],
}), () => ({ cols: [{ key: "month", label: "Month" }, { key: "attempts", label: "Attempts", num: true }, { key: "failures", label: "Failures", num: true }, { key: "failure_rate", label: "Failure rate", num: true, fmt: (v) => pct(v) }], rows: M }));

register("margin", () => base({
  tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } }, formatter: axisTip((v) => inr(v)) },
  xAxis: xCat(months, { boundaryGap: false }), yAxis: yVal({ axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => `₹${v}` } }),
  series: [
    line("Before battery wear (CM1)", M.map((r) => +r.per_swap_cm1.toFixed(2)), T.s1, {
      markLine: markLines([vline("Jul 24", "Price rise"), vline("Sep 24", "Kyron lots"), vline("Nov 24", "ZipDrop 28%")]) }),
    line("After battery wear (CM2)", M.map((r) => +r.per_swap_cm2.toFixed(2)), T.s2, {
      markLine: markLines([{ yAxis: 0, label: { show: false }, lineStyle: { color: T.axis, width: 1, type: "solid" } }]) }),
  ],
}), () => ({ cols: [{ key: "month", label: "Month" }, { key: "per_swap_cm1", label: "CM1 ₹/swap", num: true, fmt: (v) => v.toFixed(2) }, { key: "per_swap_cm2", label: "CM2 ₹/swap", num: true, fmt: (v) => v.toFixed(2) }], rows: M }));

register("coststack", () => {
  const s = (name, key, color) => bar(name, M.map((r) => +r[key].toFixed(2)), color, { stack: "cost", itemStyle: { color, borderColor: T.surface, borderWidth: 1, borderRadius: 0 } });
  const series = [s("Energy", "per_swap_energy_cost_inr", T.s1), s("Station fixed", "per_swap_fixed_per_swap", T.s3), s("Battery wear", "per_swap_wear_inr", T.s2)];
  series[2].itemStyle.borderRadius = [4, 4, 0, 0];
  series.push(line("Revenue per swap", M.map((r) => +r.per_swap_amount_charged_inr.toFixed(2)), T.ink, { showSymbol: true, symbolSize: 6 }));
  return base({
    legend: { ...base().legend, ...barLegend },
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "shadow", shadowStyle: { color: T.wash } }, formatter: axisTip((v) => inr(v), "dot") },
    xAxis: xCat(months), yAxis: yVal({ axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => `₹${v}` } }), series,
  });
}, () => ({ cols: [{ key: "month", label: "Month" }, { key: "per_swap_amount_charged_inr", label: "Revenue", num: true, fmt: (v) => v.toFixed(2) },
  { key: "per_swap_energy_cost_inr", label: "Energy", num: true, fmt: (v) => v.toFixed(2) }, { key: "per_swap_fixed_per_swap", label: "Station fixed", num: true, fmt: (v) => v.toFixed(2) },
  { key: "per_swap_wear_inr", label: "Battery wear", num: true, fmt: (v) => v.toFixed(2) }], rows: M }));

// ================= 02 FAILURES =================
const mcRows = () => D.monthly_city.filter((r) => state.cities.has(r.city));
register("heatmap", () => {
  const cities = CITIES.filter((c) => state.cities.has(c)).reverse();
  const data = mcRows().map((r) => [mLabel(r.month), r.city, +r.failure_rate.toFixed(4)]);
  const vals = D.monthly_city.map((r) => r.failure_rate);
  return base({
    grid: { left: 4, right: 70, top: 8, bottom: 4, containLabel: true },
    tooltip: { ...base().tooltip, formatter: (p) => head(`${p.value[1]} · ${p.value[0]}`) + row(T.s1, "Failure rate", pct(p.value[2]), "dot") },
    xAxis: xCat(months, { splitArea: { show: false } }), yAxis: { ...xCat(cities), axisLine: { show: false } },
    visualMap: { min: Math.min(...vals), max: Math.max(...vals), calculable: false, orient: "vertical", right: 0, top: "middle", itemHeight: 160, itemWidth: 10,
      inRange: { color: T.ramp }, text: ["high", "low"], textStyle: { color: T.muted, fontSize: 11 }, formatter: (v) => pct(v, 0) },
    series: [{ type: "heatmap", data, itemStyle: { borderColor: T.surface, borderWidth: 2, borderRadius: 3 }, emphasis: { itemStyle: { borderColor: T.ink, borderWidth: 1 } } }],
  });
}, () => ({ cols: [{ key: "month", label: "Month" }, { key: "city", label: "City" }, { key: "attempts", label: "Attempts", num: true }, { key: "failure_rate", label: "Failure rate", num: true, fmt: (v) => pct(v) }], rows: mcRows() }), { height: 300 });

register("hourly", () => {
  const hrs = [...Array(24).keys()].map((h) => `${h}:00`);
  const s = (vc, color) => line(vc, [...Array(24).keys()].map((h) => D.hourly_failure.find((r) => r.hour === h && r.vehicle_class === vc)?.failure_rate), color, { showSymbol: true, symbolSize: 6 });
  const a = s("2W", T.s1);
  a.markArea = { silent: true, itemStyle: { color: T.wash }, label: { color: T.muted, fontSize: 10.5 }, data: [[{ name: "Evening peak", xAxis: "19:00" }, { xAxis: "22:00" }]] };
  return base({
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } }, formatter: axisTip((v) => pct(v)) },
    xAxis: xCat(hrs, { boundaryGap: false }), yAxis: yVal({ axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => pct(v, 0) } }), series: [a, s("3W", T.s2)],
  });
}, () => ({ cols: [{ key: "hour", label: "Hour" }, { key: "vehicle_class", label: "Class" }, { key: "attempts", label: "Attempts", num: true }, { key: "failure_rate", label: "Failure rate", num: true, fmt: (v) => pct(v) }], rows: D.hourly_failure }));

const OUTCOMES = [["failed_no_charged_battery", "No charged battery"], ["abandoned_queue", "Abandoned in queue"], ["cancelled_by_rider", "Cancelled by rider"], ["failed_system_error", "System error"]];
register("eventmix", () => {
  const cols = [T.s1, T.s2, T.s3, T.s4];
  const series = OUTCOMES.map(([k, name], i) => bar(name, D.event_mix_monthly.map((r) => +r[k].toFixed(4)), cols[i], { stack: "mix", itemStyle: { color: cols[i], borderColor: T.surface, borderWidth: 1, borderRadius: 0 } }));
  series[3].itemStyle.borderRadius = [4, 4, 0, 0];
  return base({
    legend: { ...base().legend, ...barLegend },
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "shadow", shadowStyle: { color: T.wash } }, formatter: axisTip((v) => pct(v, 2), "dot") },
    xAxis: xCat(months), yAxis: yVal({ axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => pct(v, 0) } }), series,
  });
}, () => ({ cols: [{ key: "month", label: "Month" }, ...OUTCOMES.map(([k, n]) => ({ key: k, label: n, num: true, fmt: (v) => pct(v, 2) }))], rows: D.event_mix_monthly }));

// ---- map: MapLibre GL + OpenFreeMap vector tiles (open source, no API key, no usage limits) ----
let map = null, mapMode = "points", popup = null, hoverId = null, mapFitted = false;
const MAP_STYLE = () => `https://tiles.openfreemap.org/styles/${isDark() ? "dark" : "positron"}`;
// Sequential ramp: on a dark basemap high values must be the brightest, so the ramp runs the other way.
const heatRamp = () => (isDark() ? ["rgba(217,89,38,0)", "#4a1c0b", "#7f3113", "#b8431a", "#e0622f", "#f59a70", "#fde0d2"]
  : ["rgba(235,104,52,0)", "#fde0d2", "#f7b596", "#f08a5d", "#eb6834", "#b8431a", "#7a2a0e"]);
let HEAT = heatRamp();
const WAVE_NAME = { Launch: "Launch network", Wave1_2024H2: "Wave 1 (2024 H2)", Wave2_2025H1: "Wave 2 (2025 H1)" };
const mapRows = () => D.stations.filter((s) => state.cities.has(s.city));
const stationById = (id) => D.stations.find((s) => s.station_id === id);

const CITY_ZOOM = 6.6;
// Label side per city, chosen so neighbouring cities (Delhi/Jaipur, Mumbai/Pune) never label each other's bubble.
const LABEL_SIDE = { "Delhi NCR": "left", Jaipur: "right", Mumbai: "right", Pune: "left", Hyderabad: "left", Bengaluru: "left" };
const mapPadding = () => { const w = map.getContainer().clientWidth, s = w < 600 ? 28 : 70; return { top: 80, bottom: w < 600 ? 170 : 150, left: s, right: s + 10 }; };
const pointsFC = (rows) => ({ type: "FeatureCollection", features: rows.map((s, i) => ({ type: "Feature", id: i, geometry: { type: "Point", coordinates: [s.longitude, s.latitude] },
  properties: { id: s.station_id, gen: s.charger_generation, fr: s.failure_rate_all } })) });
function hexagon(lon, lat, km) {
  const dLat = km / 110.574, dLon = km / (111.32 * Math.cos((lat * Math.PI) / 180));
  return [[...Array(7).keys()].map((j) => { const a = (Math.PI / 3) * j + Math.PI / 6; return [lon + dLon * Math.cos(a), lat + dLat * Math.sin(a)]; })];
}
const stationColsFC = (rows) => ({ type: "FeatureCollection", features: rows.map((s, i) => ({ type: "Feature", id: i, geometry: { type: "Polygon", coordinates: hexagon(s.longitude, s.latitude, 1.4) },
  properties: { id: s.station_id, gen: s.charger_generation, fr: s.failure_rate_all, h: s.failure_rate_all * 140000 } })) });
function cityAgg(rows) {
  const by = new Map();
  for (const s of rows) {
    const c = by.get(s.city) ?? { city: s.city, lon: 0, lat: 0, n: 0, gen1: 0, attempts: 0, failures: 0, spd: 0 };
    c.lon += s.longitude; c.lat += s.latitude; c.n += 1; c.gen1 += s.charger_generation === "Gen1" ? 1 : 0;
    c.attempts += s.attempts; c.failures += s.failures; c.spd += s.swaps_per_day ?? 0;
    by.set(s.city, c);
  }
  return [...by.values()].map((c) => ({ ...c, lon: c.lon / c.n, lat: c.lat / c.n, fr: c.failures / c.attempts }));
}
const citiesFC = (rows) => ({ type: "FeatureCollection", features: cityAgg(rows).map((c, i) => ({ type: "Feature", id: i, geometry: { type: "Point", coordinates: [c.lon, c.lat] },
  properties: { city: c.city, fr: c.fr, attempts: c.attempts, label: `${pct(c.fr)} failed`, side: LABEL_SIDE[c.city] ?? "left" } })) });
const cityColsFC = (rows) => ({ type: "FeatureCollection", features: cityAgg(rows).map((c, i) => ({ type: "Feature", id: i, geometry: { type: "Polygon", coordinates: hexagon(c.lon, c.lat, 38) },
  properties: { city: c.city, fr: c.fr, h: c.fr * 4200000 } })) });

const heatColor = (prop) => ["interpolate", ["linear"], ["get", prop], 0.035, HEAT[2], 0.055, HEAT[4], 0.075, HEAT[6]];
const LAYERS = { points: ["city-bubbles", "city-labels", "st-dots"], heat: ["st-heat", "st-dots"], columns: ["city-cols", "st-cols"] };
const ALL_LAYERS = ["st-heat", "city-cols", "st-cols", "city-bubbles", "city-labels", "st-dots"];

function addStationLayers() {
  if (isDark()) {
    try {
      map.setPaintProperty("background", "background-color", "#000000");
      if (map.getLayer("water")) map.setPaintProperty("water", "fill-color", "#060a24");
    } catch (e) { /* basemap layer names changed upstream; keep its defaults */ }
  }
  const rows = mapRows(), gen = GEN();
  const genColor = ["match", ["get", "gen"], "Gen1", gen.Gen1, "Gen2", gen.Gen2, gen.Gen3];
  const hover = ["boolean", ["feature-state", "hover"], false];
  map.addSource("stations", { type: "geojson", data: pointsFC(rows) });
  map.addSource("columns", { type: "geojson", data: stationColsFC(rows) });
  map.addSource("cities", { type: "geojson", data: citiesFC(rows) });
  map.addSource("city-columns", { type: "geojson", data: cityColsFC(rows) });
  map.addLayer({ id: "st-heat", type: "heatmap", source: "stations", layout: { visibility: "none" }, paint: {
    "heatmap-weight": ["interpolate", ["linear"], ["get", "fr"], 0.03, 0, 0.09, 1],
    "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 3, 1.1, 10, 2.6],
    "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 3, 14, 6, 28, 10, 56],
    "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"], 0, HEAT[0], 0.15, HEAT[1], 0.3, HEAT[2], 0.5, HEAT[3], 0.7, HEAT[4], 0.85, HEAT[5], 1, HEAT[6]],
    "heatmap-opacity": 0.9 } });
  map.addLayer({ id: "city-cols", type: "fill-extrusion", source: "city-columns", maxzoom: 7.5, layout: { visibility: "none" }, paint: {
    "fill-extrusion-color": ["case", hover, T.ink, heatColor("fr")], "fill-extrusion-height": ["get", "h"], "fill-extrusion-opacity": 0.9, "fill-extrusion-vertical-gradient": true } });
  map.addLayer({ id: "st-cols", type: "fill-extrusion", source: "columns", minzoom: 7.5, layout: { visibility: "none" }, paint: {
    "fill-extrusion-color": ["case", hover, T.ink, genColor], "fill-extrusion-height": ["get", "h"], "fill-extrusion-opacity": 0.92, "fill-extrusion-vertical-gradient": true } });
  map.addLayer({ id: "city-bubbles", type: "circle", source: "cities", maxzoom: CITY_ZOOM, paint: {
    "circle-color": heatColor("fr"),
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, ["interpolate", ["linear"], ["get", "attempts"], 450000, 12, 800000, 22],
      6, ["interpolate", ["linear"], ["get", "attempts"], 450000, 18, 800000, 32]],
    "circle-stroke-color": ["case", hover, T.ink, T.surface], "circle-stroke-width": ["case", hover, 3, 2], "circle-opacity": 0.92 } });
  map.addLayer({ id: "city-labels", type: "symbol", source: "cities", maxzoom: CITY_ZOOM, layout: {
    "text-field": ["format", ["get", "city"], { "text-font": ["literal", ["Noto Sans Bold"]], "font-scale": 1 }, "\n", {}, ["get", "label"], { "font-scale": 0.82 }],
    "text-font": ["Noto Sans Regular"], "text-size": 13, "text-anchor": ["get", "side"], "text-justify": "auto", "text-allow-overlap": true,
    "text-offset": ["match", ["get", "side"], "right", ["literal", [-2.3, 0]], ["literal", [2.3, 0]]], "text-line-height": 1.25 },
    paint: { "text-color": T.ink, "text-halo-color": T.surface, "text-halo-width": 1.6 } });
  map.addLayer({ id: "st-dots", type: "circle", source: "stations", minzoom: 0, paint: {
    "circle-color": genColor,
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 5, ["interpolate", ["linear"], ["get", "fr"], 0.035, 3.5, 0.09, 8], 11, ["interpolate", ["linear"], ["get", "fr"], 0.035, 7, 0.09, 18]],
    "circle-stroke-color": ["case", hover, T.ink, T.surface], "circle-stroke-width": ["case", hover, 2.5, 1.5], "circle-opacity": 0.92 } });
  applyMode(false, !mapFitted);
  mapFitted = true;
}

function applyMode(animate = true, fit = true) {
  if (!map?.getLayer("st-dots")) return;
  for (const id of ALL_LAYERS) map.setLayoutProperty(id, "visibility", LAYERS[mapMode].includes(id) ? "visible" : "none");
  map.setLayerZoomRange("st-dots", { points: CITY_ZOOM, heat: 7, columns: 0 }[mapMode], 24);
  map.setPaintProperty("st-dots", "circle-opacity", mapMode === "heat" ? 0.3 : 0.92);
  if (fit) fitStations(animate);
  mapLegend();
}

function fitStations(animate = true) {
  const rows = mapRows();
  if (!map || !rows.length) return;
  const b = new maplibregl.LngLatBounds();
  rows.forEach((s) => b.extend([s.longitude, s.latitude]));
  const cols = mapMode === "columns";
  const cam = map.cameraForBounds(b, { padding: mapPadding(), maxZoom: 11.5 });
  if (!cam) return;
  const one = state.cities.size === 1;
  map.flyTo({ center: cam.center, zoom: cam.zoom + (cols && !one ? 0.2 : 0), pitch: cols ? (one ? 55 : 45) : 0, bearing: cols ? -12 : 0,
    duration: animate && !REDUCED ? 1400 : 0, essential: true });
}

function updateMap() {
  if (!map?.getSource("stations")) return;
  const rows = mapRows();
  map.getSource("stations").setData(pointsFC(rows));
  map.getSource("columns").setData(stationColsFC(rows));
  map.getSource("cities").setData(citiesFC(rows));
  map.getSource("city-columns").setData(cityColsFC(rows));
  popup?.remove();
  fitStations(true);
}

function stationCard(s) {
  const gen = GEN();
  const grid = el("div", { class: "pop-grid" });
  [["Failure rate", pct(s.failure_rate_all)], ["Failure rate, Mar–Jun 2025", pct(s.fail_2025)], ["Swaps per day", Math.round(s.swaps_per_day)],
    ["Swap attempts", int(s.attempts)], ["Location", s.location_type.replace(/_/g, " ")], ["Host", s.host_type.replace(/_/g, " ")],
    ["Opened", WAVE_NAME[s.expansion_wave] ?? s.expansion_wave], ["Connectivity", s.connectivity_tier]]
    .forEach(([k, v]) => grid.append(el("span", { text: k }), el("span", { text: String(v) })));
  return el("div", { class: "map-pop" },
    el("div", { class: "pop-head" }, el("i", { class: "swatch", style: `background:${gen[s.charger_generation]}` }), document.createTextNode(s.station_id)),
    el("div", { class: "pop-sub", text: `${s.zone.replace(/^[A-Z]+-/, "")}, ${s.city} · ${s.charger_generation} cabinet` }), grid);
}
function cityCard(name) {
  const c = cityAgg(mapRows()).find((x) => x.city === name);
  if (!c) return null;
  const grid = el("div", { class: "pop-grid" });
  [["Failure rate", pct(c.fr)], ["Stations", c.n], ["Gen1 cabinets", `${c.gen1} of ${c.n}`], ["Swap attempts", int(c.attempts)], ["Swaps per day (2025)", int(c.spd)]]
    .forEach(([k, v]) => grid.append(el("span", { text: k }), el("span", { text: String(v) })));
  return el("div", { class: "map-pop" }, el("div", { class: "pop-head", text: c.city }), el("div", { class: "pop-sub", text: "Click to zoom into this city's stations" }), grid);
}
function showPopup(id, lngLat) {
  const s = stationById(id);
  if (s) popup.setLngLat(lngLat).setDOMContent(stationCard(s)).addTo(map);
}
function setHover(source, fid) {
  if (hoverId) map.setFeatureState(hoverId, { hover: false });
  hoverId = fid == null ? null : { source, id: fid };
  if (hoverId) map.setFeatureState(hoverId, { hover: true });
}
function zoomToCity(name) {
  const rows = D.stations.filter((s) => s.city === name);
  const b = new maplibregl.LngLatBounds();
  rows.forEach((s) => b.extend([s.longitude, s.latitude]));
  const cam = map.cameraForBounds(b, { padding: mapPadding(), maxZoom: 11.5 });
  popup.remove();
  map.flyTo({ center: cam.center, zoom: Math.max(cam.zoom, 8), pitch: mapMode === "columns" ? 55 : 0, bearing: mapMode === "columns" ? -12 : 0, duration: REDUCED ? 0 : 1800, essential: true });
}
function bindMapEvents() {
  popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 14, maxWidth: "300px" });
  const leave = () => { setHover(null, null); popup.remove(); map.getCanvas().style.cursor = ""; };
  for (const [layer, source] of [["st-dots", "stations"], ["st-cols", "columns"]]) {
    const on = (e) => {
      const f = e.features?.[0];
      if (!f) return;
      setHover(source, f.id);
      showPopup(f.properties.id, source === "stations" ? f.geometry.coordinates : e.lngLat);
      map.getCanvas().style.cursor = "pointer";
    };
    map.on("mousemove", layer, on);
    map.on("click", layer, on);
    map.on("mouseleave", layer, leave);
  }
  for (const [layer, source] of [["city-bubbles", "cities"], ["city-cols", "city-columns"]]) {
    map.on("mousemove", layer, (e) => {
      const f = e.features?.[0];
      if (!f) return;
      setHover(source, f.id);
      const card = cityCard(f.properties.city);
      if (card) popup.setLngLat(source === "cities" ? f.geometry.coordinates : e.lngLat).setDOMContent(card).addTo(map);
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("click", layer, (e) => { const f = e.features?.[0]; if (f) zoomToCity(f.properties.city); });
    map.on("mouseleave", layer, leave);
  }
  map.on("zoomend", mapLegend);
  map.on("styleimagemissing", (e) => { if (!map.hasImage(e.id)) map.addImage(e.id, { width: 1, height: 1, data: new Uint8Array(4) }); });
}

function mapLegend() {
  const box = $("#map-legend"), gen = GEN();
  const cityLevel = map && map.getZoom() < (mapMode === "columns" ? 7.5 : CITY_ZOOM);
  const genRow = el("div", { class: "lg-row" }, ...Object.entries(gen).map(([g, c]) =>
    el("span", { class: "lg-item" }, el("i", { class: "dot", style: `inline-size:11px;block-size:11px;background:${c}` }), document.createTextNode(`${g} cabinets`))));
  const ramp = (lo, hi) => [el("i", { class: "ramp", style: `background:linear-gradient(90deg, ${HEAT.slice(2).join(", ")})` }),
    el("div", { class: "ends" }, el("span", { text: lo }), el("span", { text: hi }))];
  const hint = (t) => el("span", { text: t });
  if (mapMode === "heat") {
    box.replaceChildren(el("span", { class: "lg-title", text: "Where failures concentrate" }),
      el("i", { class: "ramp", style: `background:linear-gradient(90deg, ${HEAT.slice(1).join(", ")})` }),
      el("div", { class: "ends" }, el("span", { text: "fewer" }), el("span", { text: "more failures" })));
  } else if (mapMode === "columns") {
    box.replaceChildren(...(cityLevel
      ? [el("span", { class: "lg-title", text: "City columns · height and colour = failure rate" }), ...ramp("3.5%", "7.5%+"), hint("Zoom in or click a city for station columns")]
      : [el("span", { class: "lg-title", text: "Station columns · height = failure rate" }), genRow, hint("Right-drag (or Ctrl + drag) to rotate and tilt")]));
  } else if (cityLevel) {
    box.replaceChildren(el("span", { class: "lg-title", text: "Cities · colour = failure rate · size = swap volume" }), ...ramp("3.5%", "7.5%+"),
      hint("Zoom in or click a city to see its stations"));
  } else {
    const sizes = el("div", { class: "lg-row" }, ...[[7, "4%"], [11, "6%"], [16, "8%+"]].map(([d, l]) =>
      el("span", { class: "lg-item" }, el("i", { class: "dot", style: `inline-size:${d}px;block-size:${d}px;background:var(--muted)` }), document.createTextNode(l))));
    box.replaceChildren(el("span", { class: "lg-title", text: "Stations · colour = charger generation · size = failure rate" }), genRow, sizes);
  }
}

function setMapMode(mode) {
  mapMode = mode;
  $$("#map-mode button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.mode === mode)));
  popup?.remove();
  applyMode(true);
}

function exportMapPng() {
  if (!map) return;
  map.once("render", () => {
    const src = map.getCanvas();
    const c = el("canvas");
    c.width = src.width; c.height = src.height;
    const ctx = c.getContext("2d");
    ctx.drawImage(src, 0, 0);
    const dpr = window.devicePixelRatio || 1;
    const txt = "© OpenStreetMap contributors · OpenFreeMap · VoltRelay network analysis";
    ctx.font = `${11 * dpr}px Inter, system-ui, sans-serif`;
    const w = ctx.measureText(txt).width;
    ctx.fillStyle = isDark() ? "rgba(26,26,25,0.85)" : "rgba(252,252,251,0.88)";
    ctx.fillRect(c.width - w - 16 * dpr, c.height - 22 * dpr, w + 16 * dpr, 22 * dpr);
    ctx.fillStyle = isDark() ? "#c3c2b7" : "#52514e";
    ctx.fillText(txt, c.width - w - 8 * dpr, c.height - 7 * dpr);
    c.toBlob((blob) => {
      const a = el("a", { href: URL.createObjectURL(blob), download: `voltrelay-station-map-${mapMode}.png` });
      document.body.append(a); a.click(); a.remove();
    });
  });
  map.triggerRepaint();
}

const ML = "https://cdn.jsdelivr.net/npm/maplibre-gl@5.24.0/dist/maplibre-gl";
let mlPromise = null, mapPromise = null;
function loadMapLibre() {
  if (window.maplibregl) return Promise.resolve();
  return (mlPromise ??= new Promise((resolve, reject) => {
    const js = el("script", { src: `${ML}.js` });
    js.onload = resolve; js.onerror = reject;
    document.head.append(el("link", { rel: "stylesheet", href: `${ML}.css` }), js);
  }));
}
const ensureMap = () => (mapPromise ??= loadMapLibre().then(initMap, () => { $("#map-fallback").hidden = false; return null; }));
function initMap() {
  if (map) return map;
  const fail = () => { $("#map-fallback").hidden = false; return null; };
  if (!window.maplibregl) return fail();
  try {
    map = new maplibregl.Map({ container: "station-map", style: MAP_STYLE(), center: [78.3, 22.8], zoom: 3.9, attributionControl: false,
      cooperativeGestures: true, maxPitch: 70, fadeDuration: 150 });
  } catch (e) {
    return fail();
  }
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
  map.addControl(new maplibregl.FullscreenControl({ container: $("#map-card .map-wrap") }), "top-right");
  map.addControl(new maplibregl.AttributionControl({}), "bottom-right");
  map.on("style.load", addStationLayers);
  bindMapEvents();
  return map;
}

function flyToStation(id) {
  const s = stationById(id);
  if (!s) return;
  $("#map-card").scrollIntoView({ behavior: REDUCED ? "auto" : "smooth", block: "center" });
  ensureMap().then((m) => {
    if (!m) return;
    const go = () => {
      m.flyTo({ center: [s.longitude, s.latitude], zoom: 12, pitch: mapMode === "columns" ? 55 : 0, duration: REDUCED ? 0 : 2200, essential: true });
      m.once("moveend", () => showPopup(id, [s.longitude, s.latitude]));
    };
    m.getLayer("st-dots") ? go() : m.once("idle", go);
  });
}

function mapControls() {
  $$("#map-mode button").forEach((b) => b.addEventListener("click", () => setMapMode(b.dataset.mode)));
  $("#map-reset").addEventListener("click", () => { popup?.remove(); fitStations(true); });
  $("#map-png").addEventListener("click", exportMapPng);
  $("#map-csv").addEventListener("click", () => downloadCsv({ cols: ["station_id", "city", "zone", "latitude", "longitude", "charger_generation", "location_type", "host_type",
    "expansion_wave", "connectivity_tier", "swaps_per_day", "attempts", "failures", "failure_rate_all", "fail_2025"].map((k) => ({ key: k, label: k })), rows: mapRows() }, "voltrelay-stations.csv"));
  const io = new IntersectionObserver((entries) => { if (entries.some((e) => e.isIntersecting)) { io.disconnect(); ensureMap(); } }, { rootMargin: "300px 0px" });
  io.observe($("#map-card"));
}
function worstStations() {
  const rows = D.stations.filter((s) => state.cities.has(s.city)).sort((a, b) => b.failure_rate_all - a.failure_rate_all).slice(0, 10);
  const max = Math.max(...rows.map((r) => r.failure_rate_all), 0.01);
  const gen = GEN();
  const t = el("table");
  const hr = el("tr");
  [["Station"], ["City"], ["Gen"], ["Failure rate"], ["Swaps/day", "num"]].forEach(([l, c]) => hr.append(el("th", { class: c ?? "", text: l })));
  t.append(el("thead", {}, hr));
  const tb = el("tbody");
  for (const r of rows) {
    const bar = el("div", { class: "bar-cell" }, el("i", { style: `inline-size:${(r.failure_rate_all / max) * 80}px` }), document.createTextNode(pct(r.failure_rate_all)));
    const link = el("button", { type: "button", class: "station-link", text: r.station_id, "aria-label": `Show ${r.station_id} on the map` });
    link.addEventListener("click", () => flyToStation(r.station_id));
    tb.append(el("tr", {}, el("td", {}, link), el("td", { text: r.city }),
      el("td", {}, el("i", { class: "swatch", style: `background:${gen[r.charger_generation]}` }), document.createTextNode(r.charger_generation)),
      el("td", {}, bar), el("td", { class: "num", text: Math.round(r.swaps_per_day) })));
  }
  t.append(tb);
  $("#worst-stations").replaceChildren(t);
}
function cityFilter() {
  const box = $("#city-filter");
  const all = el("button", { type: "button", class: "all", "aria-pressed": "true", text: "All cities" });
  const btns = CITIES.map((c) => el("button", { type: "button", "aria-pressed": "true", "data-city": c, text: c }));
  const sync = () => {
    btns.forEach((b) => b.setAttribute("aria-pressed", String(state.cities.has(b.dataset.city))));
    all.setAttribute("aria-pressed", String(state.cities.size === CITIES.length));
    refresh("heatmap"); updateMap(); worstStations();
  };
  all.addEventListener("click", () => { state.cities = new Set(CITIES); sync(); });
  btns.forEach((b) => b.addEventListener("click", () => {
    const c = b.dataset.city;
    if (state.cities.size === CITIES.length) state.cities = new Set([c]);
    else if (state.cities.has(c)) { state.cities.delete(c); if (!state.cities.size) state.cities = new Set(CITIES); }
    else state.cities.add(c);
    sync();
  }));
  box.append(all, ...btns);
}

// ================= 03 STATIONS =================
const BANDS = ["<25°C", "25–30", "30–35", "35–40", ">40°C"];
const genBars = (key, fmt) => () => {
  const gen = GEN();
  return base({
    legend: { ...base().legend, ...barLegend },
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "shadow", shadowStyle: { color: T.wash } }, formatter: axisTip(fmt, "dot") },
    xAxis: xCat(BANDS, { name: "ambient temperature", nameLocation: "middle", nameGap: 28, nameTextStyle: { color: T.muted, fontSize: 11 } }),
    yAxis: yVal(key === "stockout_hours" ? { axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => pct(v, 0) } } : {}),
    series: ["Gen1", "Gen2", "Gen3"].map((g) => bar(g, BANDS.map((b) => D.gen_heat.find((r) => r.temp_band === b && r.charger_generation === g)?.[key]), gen[g], { barGap: "12%" })),
  });
};
const genTable = () => ({ cols: [{ key: "temp_band", label: "Ambient temp" }, { key: "charger_generation", label: "Generation" },
  { key: "charge_minutes", label: "Charge minutes", num: true, fmt: (v) => v.toFixed(1) }, { key: "stockout_hours", label: "Stockout hours", num: true, fmt: (v) => pct(v) },
  { key: "hours", label: "Station-hours", num: true, fmt: (v) => int(v) }], rows: D.gen_heat });
register("chargetime", genBars("charge_minutes", (v) => `${v.toFixed(0)} min`), genTable);
register("stockout", genBars("stockout_hours", (v) => pct(v)), genTable);

function waves() {
  const names = { Launch: "Launch network", Wave1_2024H2: "Wave 1 · 2024 H2", Wave2_2025H1: "Wave 2 · 2025 H1" };
  const box = $("#waves");
  const maxSpd = Math.max(...Object.keys(names).map((w) => avgBy(D.stations.filter((s) => s.expansion_wave === w), "swaps_per_day")));
  for (const [w, label] of Object.entries(names)) {
    const rows = D.stations.filter((s) => s.expansion_wave === w);
    const spd = avgBy(rows, "swaps_per_day"), fail = avgBy(rows, "fail_2025");
    const counts = {};
    rows.forEach((s) => (counts[s.location_type] = (counts[s.location_type] ?? 0) + 1));
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 2).map(([k, n]) => `${n} ${k.replace(/_/g, " ")}`).join(", ");
    const gens = [...new Set(rows.map((s) => s.charger_generation))].sort().join(" + ");
    box.append(el("div", { class: "mini reveal" }, el("span", { class: "k", text: label }), el("span", { class: "v", text: `${Math.round(spd)} swaps/day` }),
      el("div", { class: "meter" }, el("i", { style: `inline-size:${(spd / maxSpd) * 100}%` })),
      el("span", { class: "d", text: `${rows.length} stations · ${gens} · ${pct(fail)} failure (Mar–Jun 2025)` }), el("span", { class: "d", text: `Mostly ${top}` })));
  }
}
const avgBy = (rows, k) => rows.reduce((a, r) => a + (r[k] ?? 0), 0) / Math.max(rows.length, 1);

// ================= 04 BATTERIES =================
const BAD = ["KY-2407", "KY-2408", "KY-2409"];
register("lots", () => {
  const lots = [...D.battery_lots].sort((a, b) => a.commissioned.localeCompare(b.commissioned));
  return base({
    legend: { show: false },
    tooltip: { ...base().tooltip, trigger: "item", formatter: (p) => { const r = lots[p.dataIndex]; return head(`${r.manufacturing_lot} · ${r.supplier}`) +
      row(p.color, "SoH lost / 100 swaps", r.loss.toFixed(2), "dot") + row(T.muted, "Packs", r.packs, "dot") + row(T.muted, "Commissioned", r.commissioned, "dot"); } },
    xAxis: xCat(lots.map((r) => r.manufacturing_lot), { axisLabel: { color: T.muted, fontSize: 10, rotate: 60, interval: 0 } }),
    yAxis: yVal(),
    series: [bar("SoH lost per 100 swaps", lots.map((r) => ({ value: +r.loss.toFixed(2), itemStyle: { color: BAD.includes(r.manufacturing_lot) ? T.s2 : T.axis, borderRadius: [4, 4, 0, 0] },
      label: BAD.includes(r.manufacturing_lot) ? { show: true, position: "top", color: T.ink, fontSize: 11, fontWeight: 600, formatter: (p) => p.value.toFixed(1) } : { show: false } })),
    T.axis, { barMaxWidth: 14, markLine: markLines([{ yAxis: 3.05, label: { formatter: "typical lot ≈ 3.0", position: "insideEndTop", color: T.ink2, fontSize: 10.5 }, lineStyle: { color: T.muted, width: 1, type: "solid" } }]) })],
  });
}, () => ({ cols: [{ key: "manufacturing_lot", label: "Lot" }, { key: "supplier", label: "Supplier" }, { key: "commissioned", label: "Commissioned" },
  { key: "packs", label: "Packs", num: true }, { key: "loss", label: "SoH lost / 100 swaps", num: true, fmt: (v) => v.toFixed(2) }], rows: D.battery_lots }), { height: 340 });

const SOH = ["<70", "70–75", "75–80", "80–85", "85–90", "90–95", "95–100"];
const COHORT_LABEL = { Cellora: "Cellora", Amptek: "Amptek", "Kyron KY-2407..09": "Kyron bad lots (KY-2407/08/09)", Kyron: "Kyron later lots" };
register("range", () => {
  const colors = { Cellora: T.s1, Amptek: T.s3, "Kyron KY-2407..09": T.s2, Kyron: T.muted };
  const rows = D.range_vs_soh.filter((r) => r.pack_type === state.pack);
  const cohorts = Object.keys(colors).filter((c) => rows.some((r) => r.cohort === c));
  return base({
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } }, formatter: axisTip((v) => `${v.toFixed(1)} km`) },
    xAxis: xCat(SOH, { boundaryGap: false, name: "SoH of returned pack (%)", nameLocation: "middle", nameGap: 28, nameTextStyle: { color: T.muted, fontSize: 11 } }),
    yAxis: yVal({ scale: true }),
    series: cohorts.map((c) => line(COHORT_LABEL[c], SOH.map((b) => rows.find((r) => r.cohort === c && r.soh_band === b)?.mean ?? null), colors[c], { showSymbol: true })),
  });
}, () => ({ cols: [{ key: "pack_type", label: "Pack" }, { key: "cohort", label: "Cohort" }, { key: "soh_band", label: "SoH band" },
  { key: "mean", label: "km per swap", num: true, fmt: (v) => v.toFixed(1) }, { key: "size", label: "Swaps", num: true, fmt: (v) => int(v) }], rows: D.range_vs_soh.filter((r) => r.pack_type === state.pack) }));

register("fleet", () => {
  const F = D.fleet_monthly;
  return base({
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } }, formatter: axisTip((v) => v.toFixed(1)) },
    xAxis: xCat(F.map((r) => mLabel(r.month)), { boundaryGap: false }), yAxis: yVal({ scale: true }),
    series: [line("km delivered per swap", F.map((r) => +((r.km / F[0].km) * 100).toFixed(1)), T.s1),
      line("Mean SoH of returned packs", F.map((r) => +((r.soh / F[0].soh) * 100).toFixed(1)), T.s2)],
  });
}, () => ({ cols: [{ key: "month", label: "Month" }, { key: "km", label: "km per swap", num: true, fmt: (v) => v.toFixed(1) }, { key: "soh", label: "Mean SoH %", num: true, fmt: (v) => v.toFixed(1) },
  { key: "bad_lot_share", label: "Bad-lot share of swaps", num: true, fmt: (v) => pct(v) }], rows: D.fleet_monthly }));

function batteryStats() {
  const c = D.battery_cohorts;
  const bad2 = c.find((r) => r.cohort === "Kyron KY-2407..09" && r.pack_type === "2W_2.1kWh");
  const ok2 = c.filter((r) => r.pack_type === "2W_2.1kWh" && r.cohort !== "Kyron KY-2407..09");
  const badPacks = c.filter((r) => r.cohort === "Kyron KY-2407..09").reduce((a, r) => a + r.packs, 0);
  const share = avgBy(D.fleet_monthly.slice(-9), "bad_lot_share");
  const stats = [
    ["Packs in bad lots", int(badPacks), `≈${pct(share, 0)} of swaps since Oct 2024`],
    ["SoH lost / 100 swaps", `${bad2.soh_loss_per_100_swaps.toFixed(1)} vs ${avgBy(ok2, "soh_loss_per_100_swaps").toFixed(1)}`, "bad 2W lots vs other 2W packs"],
    ["Wear cost per 2W swap", `${inr(bad2.wear_inr_per_swap, 0)} vs ${inr(avgBy(ok2, "wear_inr_per_swap"), 0)}`, "bad lots vs other 2W packs"],
    ["Excess wear, 18 months", "≈ ₹45M", "≈ ₹12 on every swap in the network"],
  ];
  $("#battery-stats").replaceChildren(...stats.map(([k, v, d]) => el("div", { class: "mini reveal" }, el("span", { class: "k", text: k }), el("span", { class: "v", text: v }), el("span", { class: "d", text: d }))));
}

// ================= 05 PRICING =================
register("pilot", () => {
  const W = D.pilot_weekly.slice(1, -1);
  const weeks = W.map((r) => wLabel(r.week));
  const start = weeks[W.findIndex((r) => r.week >= "2024-09-30")];
  return base({
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } }, formatter: axisTip((v) => pct(v)) },
    xAxis: xCat(weeks, { boundaryGap: false }), yAxis: yVal({ scale: true, axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => pct(v, 0) } }),
    series: [line("Control cities", W.map((r) => r["Control cities"]), T.muted),
      line("Pilot cities (BLR, PUN)", W.map((r) => r["Pilot cities (BLR, PUN)"]), T.s2, { markLine: markLines([vline(start, "Pilot starts 1 Oct")]) })],
  });
}, () => ({ cols: [{ key: "week", label: "Week" }, { key: "Control cities", label: "Control", num: true, fmt: (v) => pct(v) }, { key: "Pilot cities (BLR, PUN)", label: "Pilot", num: true, fmt: (v) => pct(v) }], rows: D.pilot_weekly }));

const SEG_LABEL = { "independent (pays PEAK)": "Independents", "partner, surcharge billed": "Partners, billed", "partner, surcharge exempt": "Partners, exempt" };
register("did", () => {
  const outcomes = [["peak-hour share (pp)", "Change in peak-hour share (pp)", (v) => `${v.toFixed(1)} pp`], ["revenue per swap (₹)", "Change in revenue per swap (₹)", (v) => inr(v)]];
  const segs = Object.keys(SEG_LABEL);
  const grids = [{ left: 4, right: "54%", top: 30, bottom: 4, containLabel: true }, { left: "54%", right: 12, top: 30, bottom: 4, containLabel: true }];
  const series = [];
  outcomes.forEach(([key, , fmt], gi) => {
    const rows = segs.map((s) => D.pilot_did.find((r) => r.segment === s && r.outcome === key));
    series.push({ type: "custom", xAxisIndex: gi, yAxisIndex: gi, silent: true, data: rows.map((r, i) => [i, r["CI low"], r["CI high"]]),
      renderItem: (params, api) => { const a = api.coord([api.value(1), api.value(0)]), b = api.coord([api.value(2), api.value(0)]);
        return { type: "line", shape: { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, style: { stroke: T.muted, lineWidth: 2, lineCap: "round" } }; } });
    series.push({ type: "scatter", xAxisIndex: gi, yAxisIndex: gi, name: key, symbolSize: 12, data: rows.map((r, i) => [r["DiD estimate"], i]),
      itemStyle: { color: gi ? T.s1 : T.s2, borderColor: T.surface, borderWidth: 2 },
      label: { show: true, position: "top", distance: 8, color: T.ink, fontSize: 11, fontWeight: 600, formatter: (p) => fmt(p.value[0]) },
      markLine: markLines([{ xAxis: 0, label: { show: false }, lineStyle: { color: T.axis, width: 1, type: "solid" } }]) });
  });
  return base({
    grid: grids,
    legend: { show: false },
    title: outcomes.map(([, t], i) => ({ text: t, left: i ? "54%" : 4, top: 0, textStyle: { fontSize: 12, fontWeight: 500, color: T.ink2, fontFamily: FONT } })),
    tooltip: { ...base().tooltip, trigger: "item", formatter: (p) => { const key = outcomes[p.seriesIndex >> 1][0]; const r = D.pilot_did.find((x) => x.segment === segs[p.value[1]] && x.outcome === key);
      return head(SEG_LABEL[r.segment]) + row(p.color, "Estimate", outcomes[p.seriesIndex >> 1][2](r["DiD estimate"]), "dot") + row(T.muted, "95% CI", `${r["CI low"].toFixed(2)} to ${r["CI high"].toFixed(2)}`, "dot") + row(T.muted, "p-value", r.p < 0.001 ? "< 0.001" : r.p.toFixed(3), "dot"); } },
    xAxis: [yVal({ type: "value", gridIndex: 0 }), yVal({ type: "value", gridIndex: 1 })],
    yAxis: [{ ...xCat(segs.map((s) => SEG_LABEL[s])), gridIndex: 0, axisLine: { show: false } }, { ...xCat(segs.map(() => "")), gridIndex: 1, axisLine: { show: false }, axisLabel: { show: false } }],
    series,
  });
}, () => ({ cols: [{ key: "segment", label: "Segment" }, { key: "outcome", label: "Outcome" }, { key: "DiD estimate", label: "Estimate", num: true, fmt: (v) => v.toFixed(2) },
  { key: "CI low", label: "CI low", num: true, fmt: (v) => v.toFixed(2) }, { key: "CI high", label: "CI high", num: true, fmt: (v) => v.toFixed(2) }, { key: "p", label: "p", num: true, fmt: (v) => (v < 0.001 ? "<0.001" : v.toFixed(3)) }], rows: D.pilot_did }));

const PARTNERS = () => D.partners.filter((p) => p.pid !== "Independent");
register("partners", () => {
  const P = PARTNERS();
  const labelled = new Set(["ZipDrop", "FeastFly", "CargoTuk", "HaulKing", "ParcelNest", "Swiggle Go"]);
  return base({
    grid: { left: 4, right: 24, top: 20, bottom: 26, containLabel: true },
    legend: { show: false },
    tooltip: { ...base().tooltip, trigger: "item", formatter: (p) => { const r = P[p.dataIndex]; return head(`${r.partner_name} · ${r.partner_segment.replace(/_/g, " ")}`) +
      row(p.color, "Swaps", int(r.swaps), "dot") + row(T.muted, "Revenue", `₹${r.revenue_m.toFixed(1)}M`, "dot") + row(T.muted, "Discount / swap", inr(r.discount_per_swap), "dot") +
      row(T.muted, "CM1 / swap", inr(r.cm1), "dot") + row(T.muted, "CM2 / swap", inr(r.cm2), "dot") + row(T.muted, "Peak surcharge billed", r.peak_surcharge_billable === "Y" ? "Yes" : "No", "dot") +
      row(T.muted, "Payment terms", `${r.payment_terms_days} days`, "dot"); } },
    xAxis: yVal({ type: "value", name: "Total revenue (₹ million)", nameLocation: "middle", nameGap: 28 }),
    yAxis: yVal({ type: "value", scale: true, axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => `₹${v}` } }),
    series: [{ type: "scatter", data: P.map((r) => ({ value: [+r.revenue_m.toFixed(2), +r.cm1.toFixed(2)], symbolSize: Math.sqrt(r.swaps) / 13,
      itemStyle: { color: r.partner_name === "ZipDrop" ? T.s2 : T.s1, opacity: r.partner_name === "ZipDrop" ? 0.95 : 0.7, borderColor: T.surface, borderWidth: 2 },
      label: { show: labelled.has(r.partner_name), formatter: r.partner_name, position: "right", distance: 6, color: T.ink2, fontSize: 11, fontWeight: r.partner_name === "ZipDrop" ? 700 : 400 } })),
      emphasis: { scale: 1.08, label: { show: true } } }],
  });
}, () => ({ cols: [{ key: "partner_name", label: "Partner" }, { key: "swaps", label: "Swaps", num: true, fmt: (v) => int(v) }, { key: "revenue_m", label: "Revenue ₹M", num: true, fmt: (v) => v.toFixed(2) },
  { key: "cm1", label: "CM1 ₹/swap", num: true, fmt: (v) => v.toFixed(2) }, { key: "cm2", label: "CM2 ₹/swap", num: true, fmt: (v) => v.toFixed(2) }], rows: PARTNERS() }), { height: 400 });

function partnerTable() {
  const cols = [
    { key: "partner_name", label: "Partner" }, { key: "partner_segment", label: "Segment", fmt: (v) => (v ?? "–").replace(/_/g, " ") },
    { key: "swaps", label: "Swaps", num: true, fmt: int }, { key: "revenue_m", label: "Revenue", num: true, fmt: (v) => `₹${v.toFixed(1)}M` },
    { key: "discount_per_swap", label: "Discount/swap", num: true, fmt: (v) => inr(v) }, { key: "cm1", label: "CM1/swap", num: true, fmt: (v) => inr(v) },
    { key: "cm2", label: "CM2/swap", num: true, fmt: (v) => inr(v) }, { key: "peak_share", label: "Peak share", num: true, fmt: (v) => pct(v, 0) },
    { key: "peak_surcharge_billable", label: "Surcharge billed", fmt: (v) => (v === "Y" ? "Yes" : v === "N" ? "No" : "–") },
    { key: "payment_terms_days", label: "Terms", num: true, fmt: (v) => (v == null ? "–" : `${v} d`) },
  ];
  let sort = { key: "swaps", dir: -1 };
  const box = $("#partner-table");
  const draw = () => {
    const rows = [...D.partners].sort((a, b) => { const x = a[sort.key], y = b[sort.key]; return (x > y ? 1 : x < y ? -1 : 0) * sort.dir; });
    const t = el("table"), hr = el("tr");
    cols.forEach((c) => {
      const b = el("button", { type: "button", text: c.label });
      const th = el("th", { class: c.num ? "num" : "", scope: "col" }, b);
      if (sort.key === c.key) th.setAttribute("aria-sort", sort.dir > 0 ? "ascending" : "descending");
      b.addEventListener("click", () => { sort = { key: c.key, dir: sort.key === c.key ? -sort.dir : c.num ? -1 : 1 }; draw(); });
      hr.append(th);
    });
    const tb = el("tbody");
    rows.forEach((r) => {
      const trEl = el("tr", { class: r.partner_name === "ZipDrop" ? "hl-row" : "" });
      cols.forEach((c) => trEl.append(el("td", { class: c.num ? "num" : "", text: c.fmt ? c.fmt(r[c.key]) : r[c.key] ?? "–" })));
      tb.append(trEl);
    });
    t.append(el("thead", {}, hr), tb);
    box.replaceChildren(t);
  };
  draw();
}

// ================= 06 RETENTION =================
register("cohort", () => {
  const C = D.cohort_retention;
  const x = C.map((r) => mLabel(r.first_month));
  return base({
    grid: [{ left: 4, right: 18, top: 34, height: "46%", containLabel: true }, { left: 4, right: 18, top: "66%", bottom: 4, containLabel: true }],
    axisPointer: { link: [{ xAxisIndex: "all" }] },
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } }, formatter: axisTip((v) => pct(v)) },
    legend: { ...base().legend, data: [{ name: "30–59 day retention" }, { name: "Failure rate, first 14 days", ...barLegend }] },
    xAxis: [xCat(x, { gridIndex: 0, axisLabel: { show: false } }), xCat(x, { gridIndex: 1 })],
    yAxis: [yVal({ gridIndex: 0, scale: true, axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => pct(v, 0) } }),
      yVal({ gridIndex: 1, axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => pct(v, 0) }, splitNumber: 2 })],
    series: [line("30–59 day retention", C.map((r) => r.retention), T.s1, { showSymbol: true, xAxisIndex: 0, yAxisIndex: 0 }),
      bar("Failure rate, first 14 days", C.map((r) => r.early_fail), T.s2, { xAxisIndex: 1, yAxisIndex: 1, barMaxWidth: 18 })],
  });
}, () => ({ cols: [{ key: "first_month", label: "First swap month" }, { key: "riders", label: "New riders", num: true }, { key: "retention", label: "Retention", num: true, fmt: (v) => pct(v) },
  { key: "early_fail", label: "Early failure rate", num: true, fmt: (v) => pct(v) }, { key: "early_km", label: "Early km/swap", num: true, fmt: (v) => v.toFixed(1) }], rows: D.cohort_retention }), { height: 380 });

const liftRows = () => D.retention_lifts.filter((r) => r.factor === state.factor);
register("lift", () => {
  const rows = liftRows();
  const overall = 0.854;
  return base({
    legend: { show: false },
    tooltip: { ...base().tooltip, trigger: "item", formatter: (p) => { const r = rows[p.dataIndex]; return head(`${state.factor}: ${r.level}`) + row(T.s1, "Retention", pct(r.retention), "dot") + row(T.muted, "Riders", int(r.riders), "dot"); } },
    xAxis: xCat(rows.map((r) => String(r.level).replace(/_/g, " "))),
    yAxis: yVal({ min: 0, max: 1, axisLabel: { color: T.muted, fontSize: 11, formatter: (v) => pct(v, 0) } }),
    series: [bar("Retention", rows.map((r) => r.retention), T.s1, {
      label: { show: true, position: "top", color: T.ink, fontSize: 11, fontWeight: 600, formatter: (p) => pct(p.value, 0) },
      markLine: markLines([{ yAxis: overall, label: { formatter: "all new riders 85%", position: "insideEndTop", color: T.ink2, fontSize: 10.5 }, lineStyle: { color: T.muted, width: 1, type: "solid" } }]) })],
  });
}, () => ({ cols: [{ key: "factor", label: "Factor" }, { key: "level", label: "Level" }, { key: "riders", label: "Riders", num: true, fmt: int }, { key: "retention", label: "Retention", num: true, fmt: (v) => pct(v) }], rows: liftRows() }));

function termLabel(t) {
  const m = {
    fail_rate_14d_z: "Early failure rate (per SD)", km_per_swap_14d_z: "Early km per swap (per SD)", soh_14d_z: "Early pack SoH (per SD)", bad_lot_share_14d_z: "Bad-lot share of packs (per SD)",
    price_14d_z: "Price paid (per SD)", peak_tariff_share_14d_z: "Peak-tariff exposure (per SD)", tickets_30d_z: "Tickets raised (per SD)", competitor_promo_days_30d_z: "Competitor promo days (per SD)",
    first_attempt_failed: "First attempt failed", competitor_nearby: "Competitor within 1.5 km", "kyc_verified[T.True]": "KYC verified",
  };
  if (m[t]) return m[t];
  const lvl = (t.match(/\[T\.(.+)\]$/) ?? [])[1] ?? t;
  if (t.includes("vehicle_class")) return `${lvl} vehicle (vs 2W)`;
  if (t.includes("plan_type")) return `${lvl.replace(/_/g, " ")} plan (vs partner-billed)`;
  if (t.includes("signup_channel")) return `Signup: ${lvl.replace(/_/g, " ")} (vs app store)`;
  if (t.includes("home_city")) return `${lvl} (vs Bengaluru)`;
  if (t.includes("home_station_gen")) return `Home station ${lvl} (vs Gen2)`;
  return t;
}
const logitRows = () => D.retention_logit.filter((r) => !r.term.startsWith("attempts_14d")).sort((a, b) => a.coef - b.coef);
register("logit", () => {
  const rows = logitRows();
  const cats = rows.map((r) => termLabel(r.term));
  return base({
    grid: { left: 4, right: 18, top: 10, bottom: 26, containLabel: true },
    legend: { show: false },
    tooltip: { ...base().tooltip, trigger: "item", formatter: (p) => { const r = rows[p.value[1]]; if (!r) return ""; return head(termLabel(r.term)) +
      row(p.color, "Coefficient", r.coef.toFixed(3), "dot") + row(T.muted, "Odds ratio", r.odds_ratio.toFixed(2), "dot") + row(T.muted, "95% CI", `${r.lo.toFixed(2)} to ${r.hi.toFixed(2)}`, "dot") +
      row(T.muted, "p-value", r.p < 0.001 ? "< 0.001" : r.p.toFixed(3), "dot"); } },
    xAxis: yVal({ type: "value", name: "effect on log-odds of retention", nameLocation: "middle", nameGap: 28 }),
    yAxis: { ...xCat(cats), axisLine: { show: false }, axisLabel: { color: T.ink2, fontSize: 11, interval: 0 } },
    series: [
      { type: "custom", silent: true, data: rows.map((r, i) => [i, r.lo, r.hi, r.p < 0.05 ? 1 : 0]),
        renderItem: (params, api) => { const a = api.coord([api.value(1), api.value(0)]), b = api.coord([api.value(2), api.value(0)]);
          return { type: "line", shape: { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, style: { stroke: api.value(3) ? T.s2 : T.axis, lineWidth: 2, lineCap: "round" } }; } },
      { type: "scatter", symbolSize: 10, data: rows.map((r, i) => ({ value: [+r.coef.toFixed(3), i], itemStyle: { color: r.p < 0.05 ? T.s2 : T.muted, borderColor: T.surface, borderWidth: 2 } })),
        markLine: markLines([{ xAxis: 0, label: { show: false }, lineStyle: { color: T.ink2, width: 1, type: "solid" } }]) },
    ],
  });
}, () => ({ cols: [{ key: "term", label: "Term", fmt: (v) => termLabel(v) }, { key: "coef", label: "Coef", num: true, fmt: (v) => v.toFixed(3) }, { key: "lo", label: "CI low", num: true, fmt: (v) => v.toFixed(3) },
  { key: "hi", label: "CI high", num: true, fmt: (v) => v.toFixed(3) }, { key: "p", label: "p", num: true, fmt: (v) => (v < 0.001 ? "<0.001" : v.toFixed(3)) }], rows: logitRows() }), { height: 520 });

function factorSelect() {
  const sel = $("#factor-select");
  [...new Set(D.retention_lifts.map((r) => r.factor))].forEach((f) => sel.append(el("option", { value: f, text: f })));
  sel.addEventListener("change", () => { state.factor = sel.value; refresh("lift"); });
}

// ================= 07 ACTIONS =================
const X = '<svg viewBox="0 0 12 12"><path d="M3 3l6 6M9 3 3 9"/></svg>';
const HALF = '<svg viewBox="0 0 12 12"><circle cx="6" cy="6" r="4.2"/><path d="M6 1.8v8.4"/></svg>';
const VERDICTS = [
  { title: "More stations", tag: "Not as proposed", kind: "no", icon: X, ev: "Failures aren't a network-wide capacity gap: Gen1 cabinets alone cause ~35K excess failures, 94% of them in three hot cities. Wave 1 went to low-demand sites.",
    instead: "Upgrade or cool the 36 hot-city Gen1 cabinets first; add sites only where they saturate." },
  { title: "More batteries", tag: "Replace, don't expand", kind: "partial", icon: HALF, ev: "Gen1 stockouts are a charging-speed problem, so extra packs in a hot cabinet don't help. But 1,461 bad-lot packs (~22% of swaps) need replacing.",
    instead: "Replace the Kyron bad lots under warranty; retire packs below ~75% SoH sooner." },
  { title: "Network-wide pricing", tag: "Targeted only", kind: "partial", icon: HALF, ev: "The pilot earns ₹6–8 more per exposed swap and shifts ~3 pp of demand, but gave no reliability gain, and peak exposure slightly lowers new-rider retention.",
    instead: "Peak pricing at congested hot-city hubs in summer; 30-day grace period for new riders." },
  { title: "Exclusive with ZipDrop", tag: "Do not lock in", kind: "no", icon: X, ev: "Largest partner, least profitable 2W partner: 28% discount, exempt from the peak surcharge, 45-day terms. The Nov 2024 amendment costs ~₹5.5M a year.",
    instead: "Renegotiate: discount floor, surcharge billing, 30-day terms. Grow higher-margin partners." },
];
const PLAN = [
  ["Upgrade or cool the 36 hot-city Gen1 cabinets before April 2026", "Pre-position charged stock at those sites in April–June. Targets ~35K excess failures and protects summer new-rider cohorts.", ["Failures", "Retention"]],
  ["Replace the bad Kyron lots and claim warranty", "Add an SoH retirement threshold (~75%) and fix the asset ledger. Saves ≈ ₹12 of wear on every swap and restores range.", ["Margin", "Range"]],
  ["Renegotiate ZipDrop; no exclusivity", "Discount floor, peak-surcharge billing, 30-day payment terms. Recovers ~₹5.5M a year.", ["Margin"]],
  ["Protect every new rider's first 14 days", "Route new riders to reliable stations and healthy packs, and follow up after any failed first attempt.", ["Retention"]],
  ["Targeted peak pricing, not a network-wide rollout", "Keeps the ₹6–8 per swap revenue gain where it also relieves real congestion.", ["Revenue"]],
  ["Fix the data plumbing", "Cabinet clock sync, pack-ID capture, test-station revenue reconciliation, and ticket re-classification from rider text.", ["Data quality"]],
];
function actions() {
  $("#verdicts").replaceChildren(...VERDICTS.map((v) => {
    const tag = el("span", { class: `verdict-tag ${v.kind}` }); tag.innerHTML = v.icon; tag.append(document.createTextNode(v.tag));
    const instead = el("p", { class: "instead" }, el("strong", { text: "Instead: " }), document.createTextNode(v.instead));
    return el("article", { class: "verdict reveal" }, tag, el("h3", { text: v.title }), el("p", { class: "ev", text: v.ev }), instead);
  }));
  $("#plan").replaceChildren(...PLAN.map(([h, p, tags]) => el("li", { class: "reveal" }, el("h4", { text: h }),
    el("div", {}, el("p", { text: p }), el("div", { class: "tags" }, ...tags.map((t) => el("span", { class: "pill", text: t })))))));
}

// ================= 08 QUALITY =================
register("tickets", () => {
  const Q = D.ticket_themes_quarterly.filter((r) => r.quarter >= "2024Q1" && r.quarter <= "2025Q2");
  const other = Q.map((r) => r.app + r.billing + r.queue);
  return base({
    tooltip: { ...base().tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } }, formatter: axisTip((v) => int(v)) },
    xAxis: xCat(Q.map((r) => r.quarter.replace("Q", " Q")), { boundaryGap: false }), yAxis: yVal(),
    series: [line("Range / battery", Q.map((r) => r["range / battery"]), T.s2, { showSymbol: true }),
      line("Vague 'vehicle' complaints (filed as other)", Q.map((r) => r["vehicle 'performance' (vague)"]), T.s1, { showSymbol: true }),
      line("Stockout", Q.map((r) => r.stockout), T.s3, { showSymbol: true }), line("App, billing, queue", other, T.muted, { showSymbol: true })],
  });
}, () => ({ cols: [{ key: "quarter", label: "Quarter" }, { key: "range / battery", label: "Range/battery", num: true }, { key: "vehicle 'performance' (vague)", label: "Vague vehicle", num: true },
  { key: "stockout", label: "Stockout", num: true }, { key: "app", label: "App", num: true }, { key: "billing", label: "Billing", num: true }, { key: "queue", label: "Queue", num: true }], rows: D.ticket_themes_quarterly }), { height: 340 });

function quality() {
  $("#anomalies").replaceChildren(...D.anomalies.map((a) => el("article", { class: "anomaly reveal" }, el("h3", { text: a.Anomaly }), el("p", { text: a.Evidence }),
    el("p", { class: "act" }, el("strong", { text: "Action: " }), document.createTextNode(a["Suggested action"])))));
  const rows = [
    ["Firmware v3.2.0 clock bug", "139,490 events logged 5h30m early; proven by PEAK tariffs at off-tariff hours", "Shifted +5h30m"],
    ["Test stations STN-TST-01/02", "62K events and ₹3.9M revenue, not 'a few zero-value rows'", "Excluded and flagged"],
    ["Offline-sync near-duplicates", "None present: same-rider pairs always use different packs", "Check kept, nothing removed"],
    ["Odometer and sensor outliers", "15.3K invalid km readings; ~13K SoC/SoH readings above 100%", "Nulled or clipped"],
    ["City spellings", "21 variants of 6 cities", "Standardised"],
    ["Missing telemetry", "Concentrated at poor-connectivity stations", "Never zero-filled"],
    ["CSAT", "Only recorded for resolved tickets, half as often when slow", "Not used as a KPI"],
    ["Undocumented", "payment_mode constant; PREPAID/PROMO never used; battery IDs physically inconsistent", "Batteries analysed as cohorts"],
  ];
  $("#cleaning").replaceChildren(buildTable({ cols: [{ key: 0, label: "Issue" }, { key: 1, label: "What we found" }, { key: 2, label: "Treatment" }], rows }));
}

// ================= BOOT =================
function lazyCharts() {
  const io = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (!e.isIntersecting) return;
    io.unobserve(e.target);
    render(e.target.dataset.chart);
  }), { rootMargin: "200px 0px" });
  $$("[data-chart]").forEach((fig) => {
    const node = setupCard(fig);
    new ResizeObserver(() => live.get(fig.dataset.chart)?.inst.resize()).observe(node);
    io.observe(fig);
  });
}
function scrollSpy() {
  const links = new Map($$(".nav a").map((a) => [a.getAttribute("href").slice(1), a]));
  const io = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (e.isIntersecting) { links.forEach((a) => a.classList.remove("active")); links.get(e.target.id)?.classList.add("active"); }
  }), { rootMargin: "-40% 0px -55% 0px" });
  links.forEach((_, id) => { const s = document.getElementById(id); if (s) io.observe(s); });
  const hero = new IntersectionObserver(([e]) => { if (e.isIntersecting) links.forEach((a) => a.classList.remove("active")); }, { rootMargin: "-40% 0px -55% 0px" });
  hero.observe(document.getElementById("top"));
}
function reveal() {
  $$(".insight, .card, .callout, .tier, .anomaly").forEach((n) => n.classList.add("reveal"));
  if (REDUCED) { $$(".reveal").forEach((n) => n.classList.add("in")); return; }
  const io = new IntersectionObserver((entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { rootMargin: "0px 0px -8% 0px" });
  $$(".reveal").forEach((n) => io.observe(n));
}
function themeToggle() {
  $("#theme-toggle").addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("vr-theme", next); } catch (e) { /* storage unavailable */ }
    T = tokens();
    [...live.keys()].forEach(render);
    HEAT = heatRamp();
    fx?.repaint();
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", next === "dark" ? "#000000" : "#f1f2ee");
    if (map) {
      map.stop();
      popup?.remove();
      hoverId = null;
      ALL_LAYERS.forEach((id) => map.getLayer(id) && map.removeLayer(id));
      ["stations", "columns", "cities", "city-columns"].forEach((id) => map.getSource(id) && map.removeSource(id));
      map.setStyle(MAP_STYLE(), { diff: false });
    }
    worstStations();
  });
}
function packToggle() {
  $$("#pack-toggle button").forEach((b) => b.addEventListener("click", () => {
    state.pack = b.dataset.pack;
    $$("#pack-toggle button").forEach((x) => x.setAttribute("aria-checked", String(x === b)));
    refresh("range");
  }));
}

// ================= INTERACTIVE ROYAL BACKGROUND =================
// Two canvases on one rAF loop: a quarter-resolution aurora (soft glows are cheap at low res and upscale smoothly)
// and a full-resolution constellation that swirls around and links to the cursor. Paused when the tab is hidden.
function backgroundFx() {
  const aur = $("#bg-aurora"), par = $("#bg-particles");
  if (!aur || !par) return null;
  const a = aur.getContext("2d"), c = par.getContext("2d");
  const coarse = matchMedia("(pointer: coarse)").matches;
  const m = { x: innerWidth * 0.7, y: innerHeight * 0.25, tx: innerWidth * 0.7, ty: innerHeight * 0.25, on: false, e: 0 };
  let W = 0, H = 0, parts = [], raf = 0;
  const LB = [[], [], [], []], CB = [[], [], [], []], DB = Array.from({ length: 9 }, () => []);
  const palette = () => (isDark()
    ? { blobs: ["rgba(29,43,160,0.55)", "rgba(88,40,170,0.48)", "rgba(12,24,98,0.62)", "rgba(120,40,150,0.34)"], glow: "rgba(82,100,255,0.34)",
        dots: ["#7d92ff", "#a98bff", "#d4b36a"], line: "125,145,255", dotAlpha: 0.9 }
    : { blobs: ["rgba(65,105,225,0.16)", "rgba(120,81,169,0.14)", "rgba(29,43,143,0.10)", "rgba(155,120,220,0.12)"], glow: "rgba(65,105,225,0.16)",
        dots: ["#3b5bdb", "#7048e8", "#b08a2e"], line: "59,91,219", dotAlpha: 0.55 });
  let P = palette();

  function seed(n) {
    parts = Array.from({ length: n }, () => ({ x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3,
      r: 0.7 + Math.random() * 1.6, k: Math.random() < 0.12 ? 2 : Math.random() < 0.55 ? 0 : 1, ph: Math.random() * 6.283 }));
  }
  function resize() {
    const oldW = W;
    W = innerWidth; H = innerHeight;
    const dpr = Math.min(devicePixelRatio || 1, 1.25);
    aur.width = Math.ceil(W / 4); aur.height = Math.ceil(H / 4);
    par.width = Math.round(W * dpr); par.height = Math.round(H * dpr);
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const n = Math.round(Math.min(95, Math.max(26, (W * H) / (coarse ? 24000 : 16000))));
    if (Math.abs(W - oldW) > 80 || !parts.length) seed(n);
  }
  function aurora(t) {
    const w = aur.width, h = aur.height, s = t / 1000, big = Math.max(w, h);
    a.clearRect(0, 0, w, h);
    const blobs = [[0.15 + 0.08 * Math.sin(s * 0.13), 0.2 + 0.07 * Math.cos(s * 0.11), 0.6], [0.85 + 0.07 * Math.cos(s * 0.09), 0.28 + 0.08 * Math.sin(s * 0.12), 0.55],
      [0.55 + 0.1 * Math.sin(s * 0.07), 0.9 + 0.05 * Math.cos(s * 0.1), 0.65], [0.35 + 0.09 * Math.cos(s * 0.1), 0.6 + 0.08 * Math.sin(s * 0.08), 0.45]];
    blobs.forEach(([bx, by, br], i) => {
      const x = bx * w, y = by * h, g = a.createRadialGradient(x, y, 0, x, y, br * big);
      g.addColorStop(0, P.blobs[i]); g.addColorStop(1, "rgba(0,0,0,0)");
      a.fillStyle = g; a.fillRect(0, 0, w, h);
    });
    const gx = m.x / 4, gy = m.y / 4, g = a.createRadialGradient(gx, gy, 0, gx, gy, big * (0.22 + 0.06 * m.e));
    g.addColorStop(0, P.glow); g.addColorStop(1, "rgba(0,0,0,0)");
    a.fillStyle = g; a.fillRect(0, 0, w, h);
  }
  function constellation(t) {
    c.clearRect(0, 0, W, H);
    const R = coarse ? 130 : 180, R2 = R * R, L = coarse ? 95 : 125, L2 = L * L;
    for (const p of parts) {
      if (m.on) {
        const dx = m.x - p.x, dy = m.y - p.y, d2 = dx * dx + dy * dy;
        if (d2 < R2) {
          const d = Math.sqrt(d2) || 1, f = 1 - d / R, pull = d < 55 ? -0.14 : 0.025;
          p.vx += (-dy / d) * f * 0.07 + (dx / d) * f * pull;
          p.vy += (dx / d) * f * 0.07 + (dy / d) * f * pull;
        }
      }
      p.vx = p.vx * 0.975 + Math.cos(p.ph + t * 0.0002) * 0.004;
      p.vy = p.vy * 0.975 + Math.sin(p.ph + t * 0.00025) * 0.004;
      p.x += p.vx; p.y += p.vy;
      if (p.x < -12) p.x = W + 12; else if (p.x > W + 12) p.x = -12;
      if (p.y < -12) p.y = H + 12; else if (p.y > H + 12) p.y = -12;
    }
    // Batch strokes and fills by opacity level: ~13 draw calls per frame instead of one per line/dot.
    for (const b of LB) b.length = 0;
    for (const b of CB) b.length = 0;
    for (const b of DB) b.length = 0;
    for (let i = 0; i < parts.length; i++) {
      const p = parts[i];
      for (let j = i + 1; j < parts.length; j++) {
        const q = parts[j], dx = p.x - q.x, dy = p.y - q.y, d2 = dx * dx + dy * dy;
        if (d2 < L2) LB[Math.min(3, ((1 - d2 / L2) * 4) | 0)].push(p.x, p.y, q.x, q.y);
      }
      if (m.on) {
        const dx = p.x - m.x, dy = p.y - m.y, d2 = dx * dx + dy * dy;
        if (d2 < R2) CB[Math.min(3, ((1 - d2 / R2) * 4) | 0)].push(p.x, p.y);
      }
      const level = Math.min(2, ((0.5 + 0.5 * Math.sin(p.ph + t * 0.0018)) * 3) | 0);
      DB[p.k * 3 + level].push(p.x, p.y, p.r);
    }
    c.lineWidth = 1;
    LB.forEach((pts, b) => {
      if (!pts.length) return;
      c.strokeStyle = `rgba(${P.line},${(0.05 * (b + 1)).toFixed(2)})`;
      c.beginPath();
      for (let k = 0; k < pts.length; k += 4) { c.moveTo(pts[k], pts[k + 1]); c.lineTo(pts[k + 2], pts[k + 3]); }
      c.stroke();
    });
    CB.forEach((pts, b) => {
      if (!pts.length) return;
      c.strokeStyle = `rgba(${P.line},${(0.14 * (b + 1)).toFixed(2)})`;
      c.beginPath();
      for (let k = 0; k < pts.length; k += 2) { c.moveTo(pts[k], pts[k + 1]); c.lineTo(m.x, m.y); }
      c.stroke();
    });
    DB.forEach((pts, key) => {
      if (!pts.length) return;
      c.globalAlpha = P.dotAlpha * (0.4 + 0.3 * (key % 3));
      c.fillStyle = P.dots[(key / 3) | 0];
      c.beginPath();
      for (let k = 0; k < pts.length; k += 3) { c.moveTo(pts[k] + pts[k + 2], pts[k + 1]); c.arc(pts[k], pts[k + 1], pts[k + 2], 0, 6.283); }
      c.fill();
    });
    c.globalAlpha = 1;
  }
  function frame(t) {
    m.x += (m.tx - m.x) * 0.12; m.y += (m.ty - m.y) * 0.12; m.e *= 0.96;
    aurora(t); constellation(t);
    raf = requestAnimationFrame(frame);
  }
  const start = () => { if (!raf && !document.hidden && !REDUCED) raf = requestAnimationFrame(frame); };
  const stop = () => { cancelAnimationFrame(raf); raf = 0; };
  const still = () => { aurora(0); constellation(0); };

  addEventListener("pointermove", (e) => { const dx = e.clientX - m.tx, dy = e.clientY - m.ty; m.e = Math.min(1, m.e + Math.hypot(dx, dy) / 400);
    m.tx = e.clientX; m.ty = e.clientY; m.on = true; }, { passive: true });
  document.addEventListener("pointerleave", () => { m.on = false; });
  addEventListener("blur", () => { m.on = false; });
  let rt = 0;
  addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { resize(); if (REDUCED) still(); }, 120); }, { passive: true });
  document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));
  resize();
  still();
  if (!REDUCED) {
    // Start animating only once the page is idle so the effect never competes with first render.
    const go = () => (window.requestIdleCallback ? requestIdleCallback(start, { timeout: 2500 }) : setTimeout(start, 800));
    document.readyState === "complete" ? go() : addEventListener("load", go, { once: true });
  }
  return { repaint() { P = palette(); if (REDUCED) still(); } };
}

function spotlight() {
  $$(".card, .kpi, .insight, .verdict, .mini, .anomaly, .tier, .plan li").forEach((n) => n.classList.add("fx-spot"));
  let last = null, queued = false;
  document.addEventListener("pointermove", (e) => {
    last = e;
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      const n = last.target.closest?.(".fx-spot");
      if (!n) return;
      const r = n.getBoundingClientRect();
      n.style.setProperty("--x", `${last.clientX - r.left}px`);
      n.style.setProperty("--y", `${last.clientY - r.top}px`);
    });
  }, { passive: true });
}

function scrollUi() {
  const bar = $("#progress"), top = $("#to-top");
  let queued = false;
  const update = () => {
    queued = false;
    const h = document.documentElement.scrollHeight - innerHeight;
    bar.style.transform = `scaleX(${h > 0 ? Math.min(1, scrollY / h) : 0})`;
    top.classList.toggle("show", scrollY > innerHeight * 0.9);
  };
  addEventListener("scroll", () => { if (!queued) { queued = true; requestAnimationFrame(update); } }, { passive: true });
  top.addEventListener("click", () => scrollTo({ top: 0, behavior: REDUCED ? "auto" : "smooth" }));
  update();
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register(`sw.js?v=${V}`).catch(() => {});
}

const fx = backgroundFx();

kpis();
cityFilter();
worstStations();
waves();
batteryStats();
partnerTable();
factorSelect();
actions();
quality();
lazyCharts();
packToggle();
themeToggle();
scrollSpy();
reveal();
mapControls();
spotlight();
scrollUi();
registerServiceWorker();
