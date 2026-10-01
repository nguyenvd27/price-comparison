import assert from "node:assert/strict";
import { test } from "node:test";
import { addDays, chartSeries, dateRange, weekdayIndex, weekdayStats } from "../../web/js/logic.js";

const CATALOG = {
  colors: { black: { vi: "Đen", hex: "#333" }, silver: { vi: "Bạc", hex: "#aaa" }, nightsky: { vi: "Night Sky", hex: "#123" } },
  variants: [
    { id: "pm-256-black", model: "pm", capacity: "256GB", color: "black", apple_price: 239800 },
    { id: "pm-256-silver", model: "pm", capacity: "256GB", color: "silver", apple_price: 239800 },
    { id: "pm-1tb-black", model: "pm", capacity: "1TB", color: "black", apple_price: 344800 },
    { id: "duo-256-nightsky", model: "duo", capacity: "256GB", color: "nightsky", apple_price: 364800 },
  ],
};

test("dateRange fixed and all", () => {
  assert.deepEqual(dateRange({}, "2026-10-02", 3), ["2026-09-30", "2026-10-01", "2026-10-02"]);
  assert.deepEqual(dateRange({ "2026-10-01": {} }, "2026-10-02", "all"), ["2026-10-01", "2026-10-02"]);
  assert.deepEqual(dateRange({}, "2026-10-02", "all"), ["2026-10-02"]);
});

test("chartSeries fills missing days with null", () => {
  const daily = {
    "2026-09-30": { "pm-256-black": { max: 236000, shop: "a" } },
    "2026-10-02": { "pm-256-black": { max: 238000, shop: "b" }, "pm-256-silver": { max: 231000, shop: "a" } },
  };
  const { labels, datasets } = chartSeries(daily, CATALOG, "pm", "256GB", 3, "2026-10-02");
  assert.deepEqual(labels, ["2026-09-30", "2026-10-01", "2026-10-02"]);
  assert.deepEqual(datasets.map((d) => d.variant), ["pm-256-black", "pm-256-silver"]);
  assert.deepEqual(datasets[0].data, [236000, null, 238000]);
  assert.deepEqual(datasets[0].shops, ["a", null, "b"]);
  assert.equal(datasets[0].label, "Đen");
  assert.equal(datasets[0].hex, "#333");
  assert.deepEqual(datasets[1].data, [null, null, 231000]);
});

function buildDaily(today, days, valueFor) {
  const daily = {};
  for (let i = 0; i < days; i++) {
    const d = addDays(today, -i);
    const v = valueFor(d);
    if (v != null) daily[d] = { "pm-256-black": { max: v, shop: "a" } };
  }
  return daily;
}

test("weekdayStats finds weekday pattern", () => {
  // 2026-10-04 là Chủ nhật → 28 ngày = đúng 4 tuần T2..CN
  const daily = buildDaily("2026-10-04", 28, (d) => (weekdayIndex(d) >= 5 ? 243000 : 250000));
  const stats = weekdayStats(daily, "pm-256-black", "2026-10-04");
  assert.equal(stats.ready, true);
  assert.deepEqual(stats.deltas, [2000, 2000, 2000, 2000, 2000, -5000, -5000]);
  assert.equal(stats.best, 0);
  assert.equal(stats.worst, 5);
  assert.equal(stats.gap, 7000);
});

test("weekdayStats not ready under 14 days", () => {
  const daily = buildDaily("2026-10-04", 10, () => 250000);
  assert.deepEqual(weekdayStats(daily, "pm-256-black", "2026-10-04"), { ready: false, needDays: 4 });
});

test("weekdayStats ignores missing days", () => {
  // Bỏ hết các ngày Thứ 4 → delta Thứ 4 là null, các thứ khác vẫn tính được
  const daily = buildDaily("2026-10-04", 28, (d) => (weekdayIndex(d) === 2 ? null : weekdayIndex(d) >= 5 ? 244000 : 250000));
  const stats = weekdayStats(daily, "pm-256-black", "2026-10-04");
  assert.equal(stats.ready, true);
  assert.equal(stats.deltas[2], null);
  assert.equal(stats.deltas[0], 2000);
  assert.equal(stats.deltas[6], -4000);
  assert.equal(stats.gap, 6000);
});
