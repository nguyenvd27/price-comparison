import { DATA_BASE } from "./config.js";
import {
  bestOffer, esc, filterItems, formatDiff, formatYen, isUsable, pickPokemonFilters, rankOffers, rankedShopIds, sortItems,
} from "./logic.js";
import { bindRankModal, diffClass, renderRankModal, shopHeader } from "./table.js";

const STORAGE_KEY = "pokemon-filters";
const state = { series: "all", sort: "newest" };
let data = null;
const $ = (selector) => document.querySelector(selector);

async function loadJson(name) {
  const res = await fetch(`${DATA_BASE}pokemon/${name}?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return res.json();
}

function readState() {
  let saved = {};
  try {
    saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    saved = {};
  }
  Object.assign(state, pickPokemonFilters(new URLSearchParams(location.search), saved, data.catalog.series.map((s) => s.id)));
}

function saveState() {
  const url = new URLSearchParams();
  if (state.series !== "all") url.set("series", state.series);
  if (state.sort !== "newest") url.set("sort", state.sort);
  const query = url.toString();
  history.replaceState(null, "", query ? `?${query}` : location.pathname);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // trình duyệt chặn localStorage: bộ lọc vẫn nằm trong URL
  }
}

function renderChips(el, options, current, onPick) {
  el.innerHTML = options
    .map((o) => `<button type="button" class="chip${o.value === current ? " on" : ""}" data-value="${esc(o.value)}">${esc(o.label)}</button>`)
    .join("");
  el.onclick = (event) => {
    const button = event.target.closest("button[data-value]");
    if (button) onPick(button.dataset.value);
  };
}

function renderFilters() {
  const series = [{ value: "all", label: "All" }, ...data.catalog.series.map((s) => ({ value: s.id, label: s.name }))];
  renderChips($("#series-chips"), series, state.series, (v) => { state.series = v; update(); });
  const sorts = [{ value: "newest", label: "Newest" }, { value: "diff", label: "Top Diff" }];
  renderChips($("#sort-chips"), sorts, state.sort, (v) => { state.sort = v; update(); });
}

function itemRow(item, shops, shopIds, latest, now) {
  const best = bestOffer(item.id, latest, shopIds, now);
  const diff = best ? best.price - item.retail : null;
  const cells = shops
    .map((s) => {
      const price = latest.shops?.[s.id]?.prices?.[item.id];
      const usable = isUsable(latest.shops?.[s.id], now);
      const cls = !usable ? "muted" : best && price === best.price && !s.mail_only ? "best" : "";
      if (price == null) return `<td class="${cls}">—</td>`;
      return `<td class="${cls} clickable" data-item="${esc(item.id)}" data-shop="${esc(s.id)}" tabindex="0">${formatYen(price)}</td>`;
    })
    .join("");
  return `<tr>
    <td class="s1"><span class="box"><img src="${esc(item.image)}" alt="${esc(item.name)}" width="40" height="40" loading="lazy" onerror="this.remove()"><span class="box-name">${esc(item.name)}</span></span></td>
    <td class="s2">${formatYen(item.retail)}</td>
    <td class="s3 ${diff == null ? "" : diffClass(diff)}">${formatDiff(diff)}</td>${cells}
  </tr>`;
}

function renderTable() {
  const { catalog, latest } = data;
  const now = new Date();
  const shops = catalog.shops;
  const shopIds = rankedShopIds(shops);
  const columns = 3 + shops.length;
  const head = `<thead><tr><th class="s1">BOX</th><th class="s2">Retail</th><th class="s3">Diff</th>${shops
    .map((s) => shopHeader(s, latest.shops?.[s.id], now))
    .join("")}</tr></thead>`;
  const items = sortItems(filterItems(catalog.items, state), state.sort, latest, shopIds, now);
  let body;
  if (state.sort === "diff") {
    body = items.map((item) => itemRow(item, shops, shopIds, latest, now)).join("");
  } else {
    body = catalog.series
      .map((s) => {
        const rows = items.filter((item) => item.series === s.id);
        if (!rows.length) return "";
        const header = `<tr class="group"><td colspan="${columns}"><span>${esc(s.name)}</span></td></tr>`;
        return header + rows.map((item) => itemRow(item, shops, shopIds, latest, now)).join("");
      })
      .join("");
  }
  const empty = `<tr><td colspan="${columns}" class="empty">Không có kết quả phù hợp</td></tr>`;
  $("#price-table").innerHTML = `${head}<tbody>${body || empty}</tbody>`;
}

function openOfferModal(itemId, shopId) {
  const { catalog, latest } = data;
  const item = catalog.items.find((i) => i.id === itemId);
  renderRankModal($("#offer-modal"), {
    titleHtml: esc(item.name),
    refLabel: "Retail",
    refPrice: item.retail,
    rows: rankOffers(itemId, latest, catalog.shops, item.retail, new Date()),
    shopId,
  });
}

function update() {
  saveState();
  renderFilters();
  renderTable();
}

async function init() {
  try {
    const [catalog, latest] = await Promise.all(["catalog.json", "latest.json"].map(loadJson));
    data = { catalog, latest };
  } catch (err) {
    $("#error").hidden = false;
    $("#error").textContent = `Không tải được dữ liệu (${err.message}). Hãy thử tải lại trang.`;
    return;
  }
  readState();
  bindRankModal($("#price-table"), $("#offer-modal"), (cell) => openOfferModal(cell.dataset.item, cell.dataset.shop));
  update();
  // Cập nhật lại trạng thái mở cửa và nhãn "dữ liệu cũ" mỗi phút mà không cần tải lại trang.
  setInterval(renderTable, 60 * 1000);
}

init();
