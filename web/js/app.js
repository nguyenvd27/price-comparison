import { DATA_BASE } from "./config.js";
import {
  bestOffer, esc, filterVariants, formatDiff, formatTime, formatYen, isStale, isUsable, openStatus, rankOffers,
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
          if (price == null) return `<td class="${cls}">—</td>`;
          return `<td class="${cls} clickable" data-variant="${esc(v.id)}" data-shop="${esc(s.id)}" tabindex="0">${formatYen(price)}</td>`;
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

function diffClass(n) {
  return n >= 0 ? "pos" : "neg";
}

function openOfferModal(variantId, shopId) {
  const { catalog, latest } = data;
  const variant = catalog.variants.find((v) => v.id === variantId);
  const color = catalog.colors[variant.color];
  const rows = rankOffers(variantId, latest, catalog.shops, variant.apple_price, new Date());
  const picked = rows.find((r) => r.shop.id === shopId);
  if (!picked) return;
  const rankedCount = rows.filter((r) => r.usable).length;
  const rankText = picked.rank ? `Hạng ${picked.rank} / ${rankedCount}` : "Dữ liệu cũ hoặc lỗi, không xếp hạng";

  const list = rows
    .map((r) => {
      const cls = [r.shop.id === shopId ? "picked" : "", r.usable ? "" : "muted"].join(" ").trim();
      return `<tr class="${cls}">
        <td class="rank">${r.rank ?? "—"}</td>
        <td class="name"><a href="${esc(r.shop.url)}" target="_blank" rel="noopener">${esc(r.shop.name)} ↗</a></td>
        <td>¥${formatYen(r.price)}</td>
        <td class="${r.usable ? diffClass(r.diff) : ""}">${formatDiff(r.diff)}</td>
      </tr>`;
    })
    .join("");

  $("#modal-body").innerHTML = `
    <div class="modal-head">
      <h2><span class="dot" style="background:${esc(color.hex)}" title="${esc(color.vi)}" aria-label="${esc(color.vi)}"></span>${esc(variant.capacity)}</h2>
      <span class="apple">Apple ¥${formatYen(variant.apple_price)}</span>
      <button type="button" class="close" data-close aria-label="Đóng">✕</button>
    </div>
    <div class="modal-summary">
      <p class="shop-price">${esc(picked.shop.name)} trả <strong>¥${formatYen(picked.price)}</strong></p>
      <p><span class="profit ${diffClass(picked.diff)}">Lãi: ${formatDiff(picked.diff)}</span><span class="rank-badge">${rankText}</span></p>
    </div>
    <table class="rank-table">
      <thead><tr><th>Hạng</th><th>Cửa hàng</th><th>Giá</th><th>Chênh lệch</th></tr></thead>
      <tbody>${list}</tbody>
    </table>`;
  $("#offer-modal").showModal();
}

function setupModal() {
  const modal = $("#offer-modal");
  const open = (event) => {
    const cell = event.target.closest("td.clickable");
    if (cell) openOfferModal(cell.dataset.variant, cell.dataset.shop);
  };
  $("#price-table").addEventListener("click", open);
  $("#price-table").addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      open(event);
    }
  });
  // Đóng khi bấm nút ✕ hoặc bấm ra ngoài khung modal (Esc do <dialog> tự xử lý).
  modal.addEventListener("click", (event) => {
    if (event.target === modal || event.target.closest("[data-close]")) modal.close();
  });
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
  setupModal();
  update();
  // Cập nhật lại trạng thái mở cửa và nhãn "dữ liệu cũ" mỗi phút mà không cần tải lại trang.
  setInterval(renderTable, 60 * 1000);
}

init();
