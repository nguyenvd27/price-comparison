// Hàm thuần dùng chung cho app.js và charts.js. Không chạm DOM, để test được bằng node.
const TZ = "Asia/Tokyo";

export const WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
export const WEEKDAY_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
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

export function isStale(iso, now, hours = 2) {
  return !iso || now - new Date(iso) > hours * 3600 * 1000;
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

// Xếp hạng các cửa hàng cho một phiên bản: giá cao trước, bằng giá thì cùng hạng (1, 1, 2…).
// Cửa hàng lỗi/dữ liệu cũ nằm cuối, không có hạng; cửa hàng không thu mua thì bỏ qua.
export function rankOffers(variantId, latest, shops, applePrice, now) {
  const rows = shops
    .map((shop) => {
      const state = latest.shops?.[shop.id];
      const price = state?.prices?.[variantId];
      return price == null ? null : { shop, price, diff: price - applePrice, usable: isUsable(state, now), rank: null };
    })
    .filter(Boolean)
    .sort((a, b) => Number(b.usable) - Number(a.usable) || b.price - a.price);
  let rank = 0;
  let lastPrice = null;
  for (const row of rows) {
    if (!row.usable) continue;
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

export function openStatus(shop, now) {
  const today = jstParts(now);
  const hours = hoursOn(shop, today.date);
  if (hours && today.time >= hours[0] && today.time < hours[1]) {
    return { open: true, text: `Đang mở · đóng ${hours[1]}` };
  }
  if (hours && today.time < hours[0]) {
    return { open: false, text: `Đã đóng · mở ${hours[0]}` };
  }
  for (let i = 1; i <= 7; i++) {
    const day = addDays(today.date, i);
    const next = hoursOn(shop, day);
    if (next) {
      const when = i === 1 ? "ngày mai" : WEEKDAY_VI[weekdayIndex(day)];
      return { open: false, text: `Đã đóng · mở ${next[0]} ${when}` };
    }
  }
  return { open: false, text: "Đã đóng" };
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
    }));
  return { labels, datasets };
}

export function weekdayStats(daily, variantId, today, windowDays = 28) {
  const values = [];
  for (let i = windowDays - 1; i >= 0; i--) {
    const d = addDays(today, -i);
    const v = daily[d]?.[variantId]?.max;
    if (v != null) values.push({ d, v });
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
  return { ready: true, deltas, best, worst, gap: Math.round((deltas[best] - deltas[worst]) / 100) * 100 };
}
