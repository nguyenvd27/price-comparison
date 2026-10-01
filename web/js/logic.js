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

export function bestOffer(variantId, latest, shopIds) {
  let best = null;
  for (const id of shopIds) {
    const price = latest.shops?.[id]?.prices?.[variantId];
    if (price != null && (best === null || price > best.price)) best = { shop: id, price };
  }
  return best;
}

export function filterVariants(variants, { cap = "all", color = "all" } = {}) {
  return variants.filter((v) => (cap === "all" || v.capacity === cap) && (color === "all" || v.color === color));
}

export function filterShops(shops, query = "") {
  const q = query.trim().toLowerCase();
  if (!q) return shops;
  return shops.filter((s) => s.name.toLowerCase().includes(q) || s.id.includes(q));
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

export function chartSeries(daily, catalog, cap, range, today) {
  const labels = dateRange(daily, today, range);
  const datasets = catalog.variants
    .filter((v) => v.capacity === cap)
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
