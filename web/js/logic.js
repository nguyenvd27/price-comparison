// Hàm thuần dùng chung cho app.js và charts.js. Không chạm DOM, để test được bằng node.
const TZ = "Asia/Tokyo";

export const WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
export const WEEKDAY_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
const WEEKDAY_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
export const WEEKDAY_FULL = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ESCAPES[ch]);
}

export function formatYen(n) {
  return n == null ? "—" : n.toLocaleString("en-US");
}

export function formatDiff(n) {
  if (n == null) return "—";
  return `${n >= 0 ? "+" : "−"}${Math.abs(n).toLocaleString("en-US")}`;
}

const jstFormat = new Intl.DateTimeFormat("en-CA", {
  timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", hourCycle: "h23",
});

function jstParts(date) {
  const p = Object.fromEntries(jstFormat.formatToParts(date).map((x) => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, month: p.month, day: p.day, time: `${p.hour}:${p.minute}` };
}

export function jstDate(date) {
  return jstParts(date).date;
}

export function formatTime(iso) {
  if (!iso) return "—";
  const p = jstParts(new Date(iso));
  return `${p.month}/${p.day} ${p.time}`;
}

// Bản rút gọn cho điện thoại: hôm nay chỉ hiện giờ, ngày khác chỉ hiện ngày.
export function formatShortTime(iso, now) {
  if (!iso) return "—";
  const p = jstParts(new Date(iso));
  return p.date === jstParts(now).date ? p.time : `${p.month}/${p.day}`;
}

// Giờ crawler chạy (JST), khớp với cron trong .github/workflows/crawl.yml.
export const CRAWL_HOURS = ["10:00", "20:00"];

// Số phút nằm trong giờ crawl giữa hai thời điểm. Ngoài giờ crawl không có dữ liệu mới là bình thường.
function crawlMinutesBetween(from, to) {
  let total = 0;
  for (let day = jstParts(from).date, i = 0; day <= jstParts(to).date && i < 30; day = addDays(day, 1), i++) {
    const start = Math.max(from, new Date(`${day}T${CRAWL_HOURS[0]}:00+09:00`));
    const end = Math.min(to, new Date(`${day}T${CRAWL_HOURS[1]}:00+09:00`));
    if (end > start) total += (end - start) / 60000;
  }
  return total;
}

export function isStale(iso, now, hours = 2) {
  return !iso || crawlMinutesBetween(new Date(iso), now) > hours * 60;
}

export function addDays(dateStr, n) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export function weekdayIndex(dateStr) {
  return (new Date(`${dateStr}T00:00:00Z`).getUTCDay() + 6) % 7;
}

export function isWeekend(dateStr) {
  return weekdayIndex(dateStr) >= 5;
}

// Cửa hàng đang lỗi hoặc dữ liệu đã cũ: vẫn hiện giá nhưng không tính là giá tốt nhất.
export function isUsable(shopState, now) {
  return Boolean(shopState) && !shopState.error && !isStale(shopState.last_success_at, now);
}

export function bestOffer(variantId, latest, shopIds, now = null) {
  let best = null;
  for (const id of shopIds) {
    if (now && !isUsable(latest.shops?.[id], now)) continue;
    const price = latest.shops?.[id]?.prices?.[variantId];
    if (price != null && (best === null || price > best.price)) best = { shop: id, price };
  }
  return best;
}

// Cửa hàng chỉ mua qua bưu điện (không mang máy đến bán được) không tính vào giá cao nhất và xếp hạng.
export function rankedShopIds(shops) {
  return shops.filter((shop) => !shop.mail_only).map((shop) => shop.id);
}

// Xếp hạng các cửa hàng cho một phiên bản: giá cao trước, bằng giá thì cùng hạng (1, 1, 2…).
// Sau đó là cửa hàng chỉ mua qua bưu điện, rồi cửa hàng lỗi/dữ liệu cũ, đều không có hạng.
// Cửa hàng không thu mua thì bỏ qua.
export function rankOffers(variantId, latest, shops, applePrice, now) {
  const group = (row) => (!row.usable ? 2 : row.shop.mail_only ? 1 : 0);
  const rows = shops
    .map((shop) => {
      const state = latest.shops?.[shop.id];
      const price = state?.prices?.[variantId];
      return price == null ? null : { shop, price, diff: price - applePrice, usable: isUsable(state, now), rank: null };
    })
    .filter(Boolean)
    .sort((a, b) => group(a) - group(b) || b.price - a.price);
  let rank = 0;
  let lastPrice = null;
  for (const row of rows) {
    if (group(row) !== 0) continue;
    if (row.price !== lastPrice) {
      rank += 1;
      lastPrice = row.price;
    }
    row.rank = rank;
  }
  return rows;
}

export function filterVariants(variants, { model = "all", cap = "all", color = "all" } = {}) {
  return variants.filter(
    (v) => (model === "all" || v.model === model) && (cap === "all" || v.capacity === cap) && (color === "all" || v.color === color),
  );
}

const FILTER_KEYS = ["model", "cap", "color"];

// Link có bộ lọc thì chỉ dùng link (để link chia sẻ luôn ra đúng kết quả); không có mới dùng bộ lọc đã lưu.
export function pickFilters(params, saved) {
  const source = FILTER_KEYS.some((key) => params.has(key)) ? (key) => params.get(key) : (key) => saved[key] ?? null;
  return Object.fromEntries(FILTER_KEYS.map((key) => [key, source(key)]));
}

export function modelColors(catalog, model) {
  const models = model === "all" ? catalog.models : catalog.models.filter((m) => m.id === model);
  return [...new Set(models.flatMap((m) => m.colors))];
}

export function hasPrices(latest, variantIds) {
  return Object.values(latest.shops ?? {}).some((shop) => variantIds.some((id) => shop.prices?.[id] != null));
}

// Tiêu đề nhóm trong bảng, ví dụ "iPhone Duo · mở bán 10/23 · chưa có giá kaitori".
export function groupLabel(model, variantIds, latest, today) {
  const parts = [model.name];
  if (model.release && today < model.release) parts.push(`mở bán ${model.release.slice(5).replace("-", "/")}`);
  if (!hasPrices(latest, variantIds)) parts.push("chưa có giá kaitori");
  return parts.join(" · ");
}

function hoursOn(shop, dateStr) {
  if ((shop.closed_dates ?? []).includes(dateStr)) return null;
  return shop.hours?.[WEEKDAYS[weekdayIndex(dateStr)]] ?? null;
}

// text: câu đầy đủ (hiện khi rê chuột); label: giờ mở cửa hôm nay, gọn để tiêu đề cột hẹp.
export function openStatus(shop, now) {
  const today = jstParts(now);
  const hours = hoursOn(shop, today.date);
  const label = hours ? `${hours[0]}–${hours[1]}` : "Closed";
  if (hours && today.time >= hours[0] && today.time < hours[1]) {
    return { open: true, text: `Open · closes ${hours[1]}`, label };
  }
  if (hours && today.time < hours[0]) {
    return { open: false, text: `Closed · opens ${hours[0]}`, label };
  }
  for (let i = 1; i <= 7; i++) {
    const day = addDays(today.date, i);
    const next = hoursOn(shop, day);
    if (next) {
      const when = i === 1 ? "tomorrow" : WEEKDAY_EN[weekdayIndex(day)];
      return { open: false, text: `Closed · opens ${next[0]} ${when}`, label };
    }
  }
  return { open: false, text: "Closed", label };
}

export const MIN_DAYS = 14;

export function dateRange(daily, today, range) {
  const first = Object.keys(daily).sort()[0] ?? today;
  const start = range === "all" ? first : addDays(today, -(range - 1));
  const dates = [];
  for (let d = start; d <= today; d = addDays(d, 1)) dates.push(d);
  return dates;
}

export function chartSeries(daily, catalog, model, cap, range, today) {
  const labels = dateRange(daily, today, range);
  const datasets = catalog.variants
    .filter((v) => v.model === model && v.capacity === cap)
    .map((v) => ({
      variant: v.id,
      color: v.color,
      label: catalog.colors[v.color].vi,
      hex: catalog.colors[v.color].hex,
      data: labels.map((d) => daily[d]?.[v.id]?.max ?? null),
      shops: labels.map((d) => daily[d]?.[v.id]?.shop ?? null),
      samples: labels.map((d) => Boolean(daily[d]?.[v.id]?.sample)),
    }));
  return { labels, datasets };
}

export function weekdayStats(daily, variantId, today, windowDays = 28) {
  const values = [];
  for (let i = windowDays - 1; i >= 0; i--) {
    const d = addDays(today, -i);
    const entry = daily[d]?.[variantId];
    if (entry?.max != null) values.push({ d, v: entry.max, sample: Boolean(entry.sample) });
  }
  if (values.length < MIN_DAYS) return { ready: false, needDays: MIN_DAYS - values.length };

  // So mỗi ngày với trung bình của chính tuần đó, để xu hướng tăng/giảm dài hạn không làm lệch kết quả.
  const weeks = new Map();
  for (const x of values) {
    const monday = addDays(x.d, -weekdayIndex(x.d));
    if (!weeks.has(monday)) weeks.set(monday, []);
    weeks.get(monday).push(x);
  }
  const sums = Array(7).fill(0);
  const counts = Array(7).fill(0);
  for (const list of weeks.values()) {
    if (list.length < 2) continue;
    const mean = list.reduce((s, x) => s + x.v, 0) / list.length;
    for (const x of list) {
      const w = weekdayIndex(x.d);
      sums[w] += x.v - mean;
      counts[w] += 1;
    }
  }
  const deltas = sums.map((s, i) => (counts[i] ? Math.round(s / counts[i]) : null));
  const known = deltas.map((v, i) => [v, i]).filter(([v]) => v != null);
  const best = known.reduce((a, b) => (b[0] > a[0] ? b : a))[1];
  const worst = known.reduce((a, b) => (b[0] < a[0] ? b : a))[1];
  const gap = Math.round((deltas[best] - deltas[worst]) / 100) * 100;
  return { ready: true, deltas, best, worst, gap, sample: values.some((x) => x.sample) };
}

// Lãi cao nhất so với giá Apple của một dòng máy, cho thẻ tóm tắt ở trang chủ.
export function bestDiff(catalog, latest, model, now) {
  const shopIds = rankedShopIds(catalog.shops);
  let best = null;
  for (const v of catalog.variants.filter((x) => x.model === model)) {
    const offer = bestOffer(v.id, latest, shopIds, now);
    if (offer && (best === null || offer.price - v.apple_price > best.diff)) {
      best = { variant: v.id, diff: offer.price - v.apple_price };
    }
  }
  return best;
}

// Link cũ "/?model=…&cap=…&color=…" (trước khi tách trang) chuyển sang trang iPhone 18.
export function legacyRedirect(search) {
  const params = new URLSearchParams(search);
  return FILTER_KEYS.some((key) => params.has(key)) ? `iphone-18/?${params}` : null;
}

// ---- Pokémon BOX ----

export function itemDiff(item, latest, shopIds, now) {
  const best = bestOffer(item.id, latest, shopIds, now);
  return best ? best.price - item.retail : null;
}

export function filterItems(items, { series = "all" } = {}) {
  return items.filter((item) => series === "all" || item.series === series);
}

export function sortItems(items, sort, latest, shopIds, now) {
  const indexed = items.map((item, index) => ({ item, index, diff: itemDiff(item, latest, shopIds, now) }));
  const byDiff = (a, b) => (a.diff === null) - (b.diff === null) || (b.diff ?? 0) - (a.diff ?? 0) || a.index - b.index;
  const byNewest = (a, b) => b.item.release.localeCompare(a.item.release) || a.index - b.index;
  return indexed.sort(sort === "diff" ? byDiff : byNewest).map((x) => x.item);
}

const SORTS = ["newest", "diff"];

export function pickPokemonFilters(params, saved, seriesIds) {
  const fromUrl = params.has("series") || params.has("sort");
  const get = (key) => (fromUrl ? params.get(key) : saved?.[key] ?? null);
  const series = get("series");
  const sort = get("sort");
  return {
    series: seriesIds.includes(series) ? series : "all",
    sort: SORTS.includes(sort) ? sort : "newest",
  };
}

export function bestItemDiff(catalog, latest, now) {
  const shopIds = rankedShopIds(catalog.shops);
  let best = null;
  for (const item of catalog.items) {
    const diff = itemDiff(item, latest, shopIds, now);
    if (diff !== null && (best === null || diff > best.diff)) best = { item, diff };
  }
  return best;
}
