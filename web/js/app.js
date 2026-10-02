import { DATA_BASE } from "./config.js";
import {
  bestOffer, esc, filterVariants, formatDiff, formatShortTime, formatTime, formatYen, groupLabel, isStale, isUsable, jstDate, modelColors,
  openStatus, pickFilters, rankOffers,
} from "./logic.js";
import { renderCharts } from "./charts.js";

const state = { model: "all", cap: "all", color: "all", chartModel: null, chartCap: null, chartColor: null, range: 30 };
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

function colorOptions(model) {
  return modelColors(data.catalog, model).map((id) => {
    const c = data.catalog.colors[id];
    return { value: id, label: c.vi, dot: c.hex, swatchOnly: true };
  });
}

function modelOf(colorId) {
  return data.catalog.models.find((m) => m.colors.includes(colorId))?.id;
}

function readState() {
  let saved = {};
  try {
    saved = JSON.parse(localStorage.getItem("filters") || "{}");
  } catch {
    saved = {};
  }
  const { model, cap, color } = pickFilters(new URLSearchParams(location.search), saved);
  const { models } = data.catalog;
  state.model = models.some((m) => m.id === model) ? model : "all";
  state.cap = capacities().includes(cap) ? cap : "all";
  state.color = modelColors(data.catalog, state.model).includes(color) ? color : "all";
  state.chartModel = state.model !== "all" ? state.model : state.color !== "all" ? modelOf(state.color) : models[0].id;
  state.chartCap = state.cap !== "all" ? state.cap : capacities()[0];
  state.chartColor = state.color !== "all" ? state.color : modelColors(data.catalog, state.chartModel)[0];
}

function saveState() {
  const url = new URLSearchParams();
  if (state.model !== "all") url.set("model", state.model);
  if (state.cap !== "all") url.set("cap", state.cap);
  if (state.color !== "all") url.set("color", state.color);
  const query = url.toString();
  history.replaceState(null, "", query ? `?${query}` : location.pathname);
  try {
    localStorage.setItem("filters", JSON.stringify({ model: state.model, cap: state.cap, color: state.color }));
  } catch {
    // trình duyệt chặn localStorage: bỏ qua, bộ lọc vẫn nằm trong URL
  }
}

function setChartModel(model) {
  state.chartModel = model;
  if (!modelColors(data.catalog, model).includes(state.chartColor)) state.chartColor = modelColors(data.catalog, model)[0];
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
  const modelOptions = data.catalog.models.map((m) => ({ value: m.id, label: m.short }));
  renderChips($("#model-chips"), [{ value: "all", label: "All" }, ...modelOptions], state.model, (v) => {
    state.model = v;
    if (!modelColors(data.catalog, v).includes(state.color)) state.color = "all";
    if (v !== "all") setChartModel(v);
    update();
  });
  renderChips($("#cap-chips"), [{ value: "all", label: "All" }, ...capacities().map((c) => ({ value: c, label: c }))], state.cap, (v) => {
    state.cap = v;
    if (v !== "all") state.chartCap = v;
    update();
  });
  renderChips($("#color-chips"), [{ value: "all", label: "All" }, ...colorOptions(state.model)], state.color, (v) => {
    state.color = v;
    if (v !== "all") {
      setChartModel(modelOf(v));
      state.chartColor = v;
    }
    update();
  });
  renderChips($("#chart-model"), modelOptions, state.chartModel, (v) => {
    setChartModel(v);
    update();
  });
  renderChips($("#chart-cap"), capacities().map((c) => ({ value: c, label: c })), state.chartCap, (v) => {
    state.chartCap = v;
    update();
  });
  const ranges = [{ value: "7", label: "7 ngày" }, { value: "30", label: "30 ngày" }, { value: "all", label: "All" }];
  renderChips($("#range-chips"), ranges, String(state.range), (v) => {
    state.range = v === "all" ? "all" : Number(v);
    update();
  });
  renderChips($("#stat-color"), colorOptions(state.chartModel), state.chartColor, (v) => {
    state.chartColor = v;
    update();
  });
}

function shopHeader(shop, shopState, now) {
  const status = openStatus(shop, now);
  const stale = shopState && isStale(shopState.last_success_at, now);
  const icon = status.open ? "🟢" : "🔴";
  const tip = [status.text, shop.note].filter(Boolean).join(" · ");
  return `<th class="shop" title="${esc(tip)}">
    <a href="${esc(shop.url)}" target="_blank" rel="noopener">${esc(shop.name)} ↗</a>
    <span class="time long">${formatTime(shopState?.display_at)}</span>
    <span class="status long ${status.open ? "open" : "closed"}">${icon} ${esc(status.text)}</span>
    <span class="short">${icon} ${formatShortTime(shopState?.display_at, now)}</span>
    ${stale ? '<span class="stale">⚠ dữ liệu cũ</span>' : ""}
  </th>`;
}

function variantRow(v, shops, shopIds, latest, now) {
  const color = data.catalog.colors[v.color];
  const best = bestOffer(v.id, latest, shopIds, now);
  const diff = best ? best.price - v.apple_price : null;
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
    <td class="s1" title="${esc(color.vi)}"><span class="dot" style="background:${esc(color.hex)}" aria-label="${esc(color.vi)}"></span><span class="long">${esc(v.capacity)}</span><span class="short">${esc(v.capacity.replace("GB", ""))}</span></td>
    <td class="s2">${formatYen(v.apple_price)}</td>
    <td class="s3 ${diff == null ? "" : diffClass(diff)}">${formatDiff(diff)}</td>${cells}
  </tr>`;
}

function renderTable() {
  const { catalog, latest } = data;
  const now = new Date();
  const today = jstDate(now);
  const shops = catalog.shops;
  const shopIds = shops.map((s) => s.id);
  const columns = 3 + shops.length;
  const head = `<thead><tr><th class="s1"><span class="long">Model</span><span class="short">Model</span></th><th class="s2">Apple</th><th class="s3"><span class="long">Diff</span><span class="short">Diff</span></th>${shops
    .map((s) => shopHeader(s, latest.shops?.[s.id], now))
    .join("")}</tr></thead>`;

  const variants = filterVariants(catalog.variants, state);
  const body = catalog.models
    .map((m) => {
      const rows = variants.filter((v) => v.model === m.id);
      if (!rows.length) return "";
      const allIds = catalog.variants.filter((v) => v.model === m.id).map((v) => v.id);
      const header = `<tr class="group"><td colspan="${columns}"><span>${esc(groupLabel(m, allIds, latest, today))}</span></td></tr>`;
      return header + rows.map((v) => variantRow(v, shops, shopIds, latest, now)).join("");
    })
    .join("");

  const empty = `<tr><td colspan="${columns}" class="empty">Không có kết quả phù hợp</td></tr>`;
  $("#price-table").innerHTML = `${head}<tbody>${body || empty}</tbody>`;
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
      <thead><tr><th>Hạng</th><th>Cửa hàng</th><th>Giá</th><th>Diff</th></tr></thead>
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
