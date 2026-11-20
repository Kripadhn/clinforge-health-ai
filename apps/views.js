// ClinForge views: lab-trend line chart + encounter-class timeline. Vanilla SVG, light/dark via CSS vars.
const byId = (id) => document.getElementById(id);
const tip = byId("tip");
const NS = "http://www.w3.org/2000/svg";
// fixed class -> slot mapping: color follows the entity, never rank
const CLASSES = ["ambulatory", "emergency", "inpatient", "outpatient", "urgentcare", "wellness"];
const SLOT = { ambulatory: "--s1", emergency: "--s2", inpatient: "--s3",
               outpatient: "--s4", urgentcare: "--s5", wellness: "--s6" };

const auth = () => ({ Authorization: "Bearer " + byId("tok").value });
const css = (v) => getComputedStyle(document.body).getPropertyValue(v).trim();

function el(tag, attrs, parent) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (parent) parent.appendChild(n);
  return n;
}
function showTip(ev, html) {
  tip.innerHTML = html;
  tip.style.display = "block";
  tip.style.left = Math.min(ev.clientX + 12, innerWidth - 310) + "px";
  tip.style.top = ev.clientY + 12 + "px";
}
const hideTip = () => (tip.style.display = "none");

async function getJSON(path) {
  const r = await fetch(path, { headers: auth() });
  if (!r.ok) throw new Error((await r.json()).detail || "request failed " + r.status);
  return r.json();
}

async function loadPatients() {
  const pts = await getJSON("/views/patients");
  byId("pt").innerHTML = pts.map(function (p) {
    return "<option value=" + JSON.stringify(p.id) + ">" + p.first_name + " " + p.last_name + "</option>";
  }).join("");
}

// ---- lab trend (single series -> no legend box; title names it; last value direct-labeled) ----
let ltData = null;
async function drawTrend() {
  const q = byId("lt-q").value.trim();
  if (!q) return;
  const host = byId("lt-chart");
  host.textContent = "loading...";
  try {
    ltData = await getJSON("/views/lab-trend?patient_id=" + byId("pt").value +
      "&q=" + encodeURIComponent(q));
  } catch (e) {
    host.textContent = e.message;
    return;
  }
  byId("lt-title").textContent = ltData.description;
  byId("lt-sub").textContent = ltData.stats.n + " results | code " + ltData.code +
    (ltData.units ? " | " + ltData.units : "");
  host.textContent = "";
  const pts = ltData.series.map((d) => ({ t: Date.parse(d.observed_at), v: +d.value, d }))
    .filter((p) => Number.isFinite(p.v));
  if (!pts.length) { host.textContent = "No numeric results for this lab."; renderTrendTable(); return; }
  const W = 880, H = 260, m = { l: 48, r: 76, t: 12, b: 26 };
  const x0 = Math.min(...pts.map((p) => p.t)), x1 = Math.max(...pts.map((p) => p.t));
  let v0 = Math.min(...pts.map((p) => p.v)), v1 = Math.max(...pts.map((p) => p.v));
  if (v0 === v1) { v0 -= 1; v1 += 1; }
  const pad = (v1 - v0) * 0.08; v0 -= pad; v1 += pad;
  const X = (t) => m.l + ((t - x0) / (x1 - x0 || 1)) * (W - m.l - m.r);
  const Y = (v) => m.t + (1 - (v - v0) / (v1 - v0)) * (H - m.t - m.b);
  const svg = el("svg", { viewBox: "0 0 " + W + " " + H, width: "100%" }, host);
  for (let i = 0; i <= 4; i++) { // recessive horizontal grid
    const v = v0 + (i / 4) * (v1 - v0), y = Y(v);
    el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, stroke: css("--grid"), "stroke-width": 1 }, svg);
    el("text", { x: m.l - 6, y: y + 3, "text-anchor": "end", class: "lbl" }, svg).textContent = v.toFixed(1);
  }
  el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, stroke: css("--axis"), "stroke-width": 1 }, svg);
  const years = new Set();
  for (const p of pts) {
    const y = new Date(p.t).getFullYear();
    if (!years.has(y)) { years.add(y);
      el("text", { x: X(p.t), y: H - 8, "text-anchor": "middle" }, svg).textContent = y; }
  }
  const color = css("--s1");
  el("path", { d: pts.map((p, i) => (i ? "L" : "M") + X(p.t) + " " + Y(p.v)).join(" "),
    fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round" }, svg);
  const last = pts[pts.length - 1];
  el("circle", { cx: X(last.t), cy: Y(last.v), r: 4, fill: color }, svg);
  el("text", { x: X(last.t) + 8, y: Y(last.v) + 4, class: "lbl", "font-weight": 600 }, svg)
    .textContent = last.v + (ltData.units ? " " + ltData.units : "");
  // crosshair + nearest-point tooltip over the whole plot
  const hover = el("circle", { r: 5, fill: color, stroke: css("--surface-1"), "stroke-width": 2,
    visibility: "hidden" }, svg);
  const cross = el("line", { y1: m.t, y2: H - m.b, stroke: css("--axis"), "stroke-width": 1,
    visibility: "hidden" }, svg);
  const zone = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b,
    fill: "transparent" }, svg);
  zone.addEventListener("mousemove", (ev) => {
    const r = svg.getBoundingClientRect();
    const mx = ((ev.clientX - r.left) / r.width) * W;
    let best = pts[0];
    for (const p of pts) if (Math.abs(X(p.t) - mx) < Math.abs(X(best.t) - mx)) best = p;
    cross.setAttribute("x1", X(best.t)); cross.setAttribute("x2", X(best.t));
    cross.setAttribute("visibility", "visible");
    hover.setAttribute("cx", X(best.t)); hover.setAttribute("cy", Y(best.v));
    hover.setAttribute("visibility", "visible");
    showTip(ev, "<b>" + best.v + " " + (ltData.units || "") + "</b><br>" +
      best.d.observed_at.slice(0, 10) + " [obs:" + best.d.id + "]");
  });
  zone.addEventListener("mouseleave", () => { hideTip();
    cross.setAttribute("visibility", "hidden"); hover.setAttribute("visibility", "hidden"); });
  renderTrendTable();
}
function renderTrendTable() {
  if (!ltData) return;
  byId("lt-table").innerHTML = "<table><tr><th>date</th><th>value</th><th>units</th><th>record</th></tr>" +
    ltData.series.map((d) => "<tr><td>" + d.observed_at.slice(0, 10) + "</td><td class=num>" + d.value +
      "</td><td>" + (d.units || "") + "</td><td>obs:" + d.id + "</td></tr>").join("") + "</table>";
}

// ---- encounter timeline (labeled swimlane per class; identity never color-alone) ----
async function drawTimeline() {
  const host = byId("tl-chart");
  host.textContent = "loading...";
  let data;
  try {
    data = await getJSON("/views/timeline?patient_id=" + byId("pt").value);
  } catch (e) {
    host.textContent = e.message;
    return;
  }
  const enc = data.encounters.map((d) => ({ t: Date.parse(d.start_at), d }))
    .filter((p) => Number.isFinite(p.t)).sort((a, b) => a.t - b.t);
  byId("tl-sub").textContent = enc.length +
    " encounters. Each labeled row is one encounter class; a dot is one encounter.";
  host.textContent = "";
  if (!enc.length) { host.textContent = "No encounters."; return; }
  const rows = CLASSES.filter((c) => enc.some((p) => p.d.encounter_class === c));
  const W = 880, RH = 34, m = { l: 96, r: 16, t: 8, b: 26 }, H = m.t + rows.length * RH + m.b;
  const x0 = enc[0].t, x1 = enc[enc.length - 1].t;
  const X = (t) => m.l + ((t - x0) / (x1 - x0 || 1)) * (W - m.l - m.r);
  const svg = el("svg", { viewBox: "0 0 " + W + " " + H, width: "100%" }, host);
  rows.forEach((c, i) => {
    const y = m.t + i * RH + RH / 2;
    el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, stroke: css("--grid"), "stroke-width": 1 }, svg);
    el("text", { x: m.l - 8, y: y + 4, "text-anchor": "end", class: "row-lbl" }, svg).textContent = c;
  });
  el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, stroke: css("--axis"), "stroke-width": 1 }, svg);
  const years = new Set();
  for (const p of enc) {
    const y = new Date(p.t).getFullYear();
    if (!years.has(y) && y % 2 === 0) { years.add(y);
      el("text", { x: X(p.t), y: H - 8, "text-anchor": "middle" }, svg).textContent = y; }
  }
  for (const p of enc) {
    const i = rows.indexOf(p.d.encounter_class);
    if (i < 0) continue;
    const dot = el("circle", { cx: X(p.t), cy: m.t + i * RH + RH / 2, r: 5,
      fill: css(SLOT[p.d.encounter_class]), stroke: css("--surface-1"), "stroke-width": 2 }, svg);
    dot.addEventListener("mousemove", (ev) => showTip(ev,
      "<b>" + (p.d.description || p.d.encounter_class) + "</b><br>" + p.d.start_at.slice(0, 10) +
      (p.d.reason ? "<br>" + p.d.reason : "") + "<br>[enc:" + p.d.id + "]"));
    dot.addEventListener("mouseleave", hideTip);
  }
  byId("tl-table").innerHTML = "<table><tr><th>date</th><th>class</th><th>description</th><th>reason</th></tr>" +
    enc.slice().reverse().map((p) => "<tr><td>" + p.d.start_at.slice(0, 10) + "</td><td>" +
      p.d.encounter_class + "</td><td>" + (p.d.description || "") + "</td><td>" +
      (p.d.reason || "") + "</td></tr>").join("") + "</table>";
}

async function refresh() {
  try { await loadPatients(); } catch (e) { byId("tl-chart").textContent = e.message; return; }
  await drawTimeline();
  if (ltData) await drawTrend();
}
byId("tok").addEventListener("change", refresh);
byId("pt").addEventListener("change", () => { drawTimeline(); if (ltData) drawTrend(); });
byId("lt-go").addEventListener("click", drawTrend);
byId("lt-q").addEventListener("keydown", (e) => { if (e.key === "Enter") drawTrend(); });
byId("lt-tbl").addEventListener("click", () => byId("lt-table").classList.toggle("hidden"));
byId("tl-tbl").addEventListener("click", () => byId("tl-table").classList.toggle("hidden"));
byId("theme").addEventListener("click", () => {
  const r = document.documentElement;
  const dark = r.getAttribute("data-theme") === "dark" ||
    (!r.getAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
  r.setAttribute("data-theme", dark ? "light" : "dark");
  drawTimeline(); if (ltData) drawTrend(); // re-read CSS vars
});
refresh();
