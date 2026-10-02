import assert from "node:assert/strict";
import { test } from "node:test";
import {
  addDays, bestOffer, esc, filterVariants, formatDiff, formatTime, formatYen,
  isStale, isUsable, isWeekend, jstDate, openStatus, weekdayIndex,
} from "../../web/js/logic.js";

test("formatYen and formatDiff", () => {
  assert.equal(formatYen(262000), "262,000");
  assert.equal(formatYen(null), "—");
  assert.equal(formatDiff(22200), "+22,200");
  assert.equal(formatDiff(-1800), "−1,800");
  assert.equal(formatDiff(0), "+0");
  assert.equal(formatDiff(null), "—");
});

test("esc escapes html", () => {
  assert.equal(esc(`<a href="x">&'`), "&lt;a href=&quot;x&quot;&gt;&amp;&#39;");
});

test("JST dates and times", () => {
  assert.equal(jstDate(new Date("2026-10-01T15:05:00Z")), "2026-10-02");
  assert.equal(formatTime("2026-10-01T16:15:00Z"), "10/02 01:15");
  assert.equal(formatTime(null), "—");
});

test("isStale after 2 hours of crawl time", () => {
  const now = new Date("2026-10-02T12:30:00+09:00");
  assert.equal(isStale("2026-10-02T10:31:00+09:00", now), false);
  assert.equal(isStale("2026-10-02T10:29:00+09:00", now), true);
  assert.equal(isStale(null, now), true);
});

test("isStale ignores the hours when the crawler is off (20:00–10:00 JST)", () => {
  const last = "2026-10-02T20:00:00+09:00";
  assert.equal(isStale(last, new Date("2026-10-02T23:00:00+09:00")), false);
  assert.equal(isStale(last, new Date("2026-10-03T09:30:00+09:00")), false);
  assert.equal(isStale(last, new Date("2026-10-03T11:30:00+09:00")), false);
  assert.equal(isStale(last, new Date("2026-10-03T12:30:00+09:00")), true);
  // Ngừng từ 17:00 hôm trước: đã lỡ 3 giờ crawl.
  assert.equal(isStale("2026-10-02T17:00:00+09:00", new Date("2026-10-03T09:00:00+09:00")), true);
});

test("date helpers", () => {
  assert.equal(addDays("2026-10-31", 1), "2026-11-01");
  assert.equal(addDays("2026-10-01", -1), "2026-09-30");
  assert.equal(weekdayIndex("2026-10-05"), 0); // Thứ 2
  assert.equal(weekdayIndex("2026-10-04"), 6); // Chủ nhật
  assert.equal(isWeekend("2026-10-03"), true);
  assert.equal(isWeekend("2026-10-02"), false);
});

test("bestOffer picks highest among given shops", () => {
  const latest = { shops: {
    a: { prices: { "pm-256-black": 236000 } },
    b: { prices: { "pm-256-black": 238000 } },
    c: { prices: {} },
  } };
  assert.deepEqual(bestOffer("pm-256-black", latest, ["a", "b", "c"]), { shop: "b", price: 238000 });
  assert.deepEqual(bestOffer("pm-256-black", latest, ["a"]), { shop: "a", price: 236000 });
  assert.equal(bestOffer("pm-2tb-black", latest, ["a", "b"]), null);
});

test("filterVariants", () => {
  const variants = [
    { id: "1", capacity: "256GB", color: "black" },
    { id: "2", capacity: "256GB", color: "silver" },
    { id: "3", capacity: "1TB", color: "black" },
  ];
  assert.deepEqual(filterVariants(variants, { cap: "all", color: "all" }).map((v) => v.id), ["1", "2", "3"]);
  assert.deepEqual(filterVariants(variants, { cap: "256GB", color: "black" }).map((v) => v.id), ["1"]);
});

const SHOP = {
  hours: { mon: ["10:00", "19:00"], tue: ["10:00", "19:00"], wed: ["10:00", "19:00"], thu: ["10:00", "19:00"], fri: ["10:00", "19:00"], sat: ["10:00", "19:00"], sun: null },
  closed_dates: ["2026-10-05"],
};
const at = (iso) => new Date(iso);

test("openStatus during opening hours", () => {
  assert.deepEqual(openStatus(SHOP, at("2026-10-02T12:00:00+09:00")), { open: true, text: "Open · closes 19:00", label: "10:00–19:00" });
});

test("openStatus before opening today", () => {
  assert.deepEqual(openStatus(SHOP, at("2026-10-02T09:00:00+09:00")), { open: false, text: "Closed · opens 10:00", label: "10:00–19:00" });
});

test("openStatus exactly at closing time is closed", () => {
  assert.deepEqual(openStatus(SHOP, at("2026-10-02T19:00:00+09:00")), { open: false, text: "Closed · opens 10:00 tomorrow", label: "10:00–19:00" });
});

test("openStatus skips Sunday and closed_dates", () => {
  // T7 20:00 → CN nghỉ, T2 10/05 nghỉ đột xuất → mở lại T3
  assert.deepEqual(openStatus(SHOP, at("2026-10-03T20:00:00+09:00")), { open: false, text: "Closed · opens 10:00 Tue", label: "10:00–19:00" });
});

test("openStatus uses JST even when given UTC", () => {
  assert.equal(openStatus(SHOP, at("2026-10-02T03:00:00Z")).open, true); // 12:00 JST
});

test("bestOffer skips stale or erroring shops", () => {
  const now = new Date("2026-10-02T12:00:00+09:00");
  const latest = { shops: {
    fresh: { last_success_at: "2026-10-02T11:30:00+09:00", error: null, prices: { "pm-256-black": 236000 } },
    stale: { last_success_at: "2026-09-30T11:30:00+09:00", error: null, prices: { "pm-256-black": 270000 } },
    broken: { last_success_at: "2026-10-02T11:30:00+09:00", error: "HTTPError: 503", prices: { "pm-256-black": 280000 } },
  } };
  assert.deepEqual(bestOffer("pm-256-black", latest, ["fresh", "stale", "broken"], now), { shop: "fresh", price: 236000 });
  assert.equal(isUsable(latest.shops.stale, now), false);
  assert.equal(isUsable(latest.shops.broken, now), false);
  assert.equal(isUsable(latest.shops.fresh, now), true);
});

test("openStatus label is Closed on a day off", () => {
  // CN 10/04: nghỉ cả ngày
  assert.deepEqual(openStatus(SHOP, at("2026-10-04T12:00:00+09:00")), { open: false, text: "Closed · opens 10:00 Tue", label: "Closed" });
});
