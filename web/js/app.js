import { DATA_BASE } from "./config.js";
import {
  bestOffer, esc, filterVariants, formatDiff, formatTime, formatYen, isStale, isUsable, openStatus,
} from "./logic.js";
import { renderCharts } from "./charts.js";

const state = { cap: "all", color: "all", chartCap: null, chartColor: null, range: 30 };
let data = null;

const $ = (selector) => document.querySelector(selector);

async function loadJson(name) {
  const res = await fetch(`${DATA_BASE}${name}?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return res.json();
}

function capacities() {
  return [...new Set(data.catalog.variants.map((v) => v.capacity))];
}

function colorOptions() {
  return Object.entries(data.catalog.colors).map(([id, c]) => ({ value: id, label: c.vi, dot: c.hex, swatchOnly: true }));
}

function readState() {
  let saved = {};
  try {
    saved = JSON.parse(localStorage.getItem("filters") || "{}");
  } catch {
    saved = {};
  }
  const url = new URLSearchParams(location.search);
  const cap = url.get("cap") || saved.cap;
  const color = url.get("color") || saved.color;
  state.cap = capacities().includes(cap) ? cap : "all";
  state.color = color in data.catalog.colors ? color : "all";
  state.chartCap = state.cap !== "all" ? state.cap : capacities()[0];
  state.chartColor = state.color !== "all" ? state.color : Object.keys(data.catalog.colors)[0];
}

function saveState() {
  const url = new URLSearchParams();
  if (state.cap !== "all") url.set("cap", state.cap);
  if (state.color !== "all") url.set("color", state.color);
  const query = url.toString();
  history.replaceState(null, "", query ? `?${query}` : location.pathname);
  try {
    localStorage.setItem("filters", JSON.stringify({ cap: state.cap, color: state.color }));
  } catch {
    // trình duyệt chặn localStorage: bỏ qua, bộ lọc vẫn nằm trong URL
  }
}

function renderChips(el, options, current, onPick) {
  el.innerHTML = options
    .map((o) => {
      const on = o.value === current ? " on" : "";
      if (o.swatchOnly) {
        // Màu máy: chỉ hiện chấm màu, tên màu nằm trong title/aria-label
        return `<button type="button" class="chip swatch${on}" data-value="${esc(o.value)}" title="${esc(o.label)}" aria-label="${esc(o.label)}"><span class="dot" style="background:${esc(o.dot)}"></span></button>`;
      }
      return `<button type="button" class="chip${on}" data-value="${esc(o.value)}">${esc(o.label)}</button>`;
    })
    .join("");
  el.onclick = (event) => {
    const button = event.target.closest("button[data-value]");
    if (button) onPick(button.dataset.value);
  };
}

function renderFilters() {
  renderChips($("#cap-chips"), [{ value: "all", label: "Tất cả" }, ...capacities().map((c) => ({ value: c, label: c }))], state.cap, (v) => {
    state.cap = v;
    if (v !== "all") state.chartCap = v;
    update();
  });
  renderChips($("#color-chips"), [{ value: "all", label: "Mọi màu" }, ...colorOptions()], state.color, (v) => {
    state.color = v;
    if (v !== "all") state.chartColor = v;
    update();
  });
  renderChips($("#chart-cap"), capacities().map((c) => ({ value: c, label: c })), state.chartCap, (v) => {
    state.chartCap = v;
    update();
  });
  const ranges = [{ value: "7", label: "7 ngày" }, { value: "30", label: "30 ngày" }, { value: "all", label: "Tất cả" }];
  renderChips($("#range-chips"), ranges, String(state.range), (v) => {
    state.range = v === "all" ? "all" : Number(v);
    update();
  });
  renderChips($("#stat-color"), colorOptions(), state.chartColor, (v) => {
    state.chartColor = v;
    update();
  });
}

function shopHeader(shop, shopState, now) {
  const status = openStatus(shop, now);
  const stale = shopState && isStale(shopState.last_success_at, now);
  return `<th class="shop" title="${esc(shop.note ?? "")}">
    <a href="${esc(shop.url)}" target="_blank" rel="noopener">${esc(shop.name)} ↗</a>
    <span class="time">${formatTime(shopState?.display_at)}</span>
    <span class="status ${status.open ? "open" : "closed"}">${status.open ? "🟢" : "🔴"} ${esc(status.text)}</span>
    ${stale ? '<span class="stale">⚠ dữ liệu cũ</span>' : ""}
  </th>`;
}

function renderTable() {
  const { catalog, latest } = data;
  const now = new Date();
  const shops = catalog.shops;
  const shopIds = shops.map((s) => s.id);
  const head = `<thead><tr><th class="s1">Phiên bản</th><th class="s2">Apple</th><th class="s3">Chênh lệch</th>${shops
    .map((s) => shopHeader(s, latest.shops?.[s.id], now))
    .join("")}</tr></thead>`;

  const rows = filterVariants(catalog.variants, state)
    .map((v) => {
      const color = catalog.colors[v.color];
      const best = bestOffer(v.id, latest, shopIds, now);
      const diff = best ? best.price - v.apple_price : null;
      const diffClass = diff == null ? "" : diff >= 0 ? "pos" : "neg";
      const cells = shops
        .map((s) => {
          const price = latest.shops?.[s.id]?.prices?.[v.id];
          const usable = isUsable(latest.shops?.[s.id], now);
          const cls = !usable ? "muted" : best && price === best.price ? "best" : "";
          return `<td class="${cls}">${formatYen(price)}</td>`;
        })
        .join("");
      return `<tr>
        <td class="s1" title="${esc(color.vi)}"><span class="dot" style="background:${esc(color.hex)}" aria-label="${esc(color.vi)}"></span>${esc(v.capacity)}</td>
        <td class="s2">${formatYen(v.apple_price)}</td>
        <td class="s3 ${diffClass}">${formatDiff(diff)}</td>${cells}
      </tr>`;
    })
    .join("");

  const empty = `<tr><td colspan="${3 + shops.length}" class="empty">Không có kết quả phù hợp</td></tr>`;
  $("#price-table").innerHTML = `${head}<tbody>${rows || empty}</tbody>`;
}

function update() {
  saveState();
  renderFilters();
  renderTable();
  renderCharts(data, state);
}

async function init() {
  try {
    const [catalog, latest, daily] = await Promise.all(["catalog.json", "latest.json", "daily.json"].map(loadJson));
    data = { catalog, latest, daily };
  } catch (err) {
    $("#error").hidden = false;
    $("#error").textContent = `Không tải được dữ liệu (${err.message}). Hãy thử tải lại trang.`;
    return;
  }
  readState();
  update();
  // Cập nhật lại trạng thái mở cửa và nhãn "dữ liệu cũ" mỗi phút mà không cần tải lại trang.
  setInterval(renderTable, 60 * 1000);
}

init();
