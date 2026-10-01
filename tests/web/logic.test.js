import assert from "node:assert/strict";
import { test } from "node:test";
import {
  addDays, bestOffer, esc, filterShops, filterVariants, formatDiff, formatTime, formatYen,
  isStale, isWeekend, jstDate, openStatus, weekdayIndex,
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

test("isStale after 2 hours", () => {
  const now = new Date("2026-10-02T12:00:00+09:00");
  assert.equal(isStale("2026-10-02T10:30:00+09:00", now), false);
  assert.equal(isStale("2026-10-02T09:59:00+09:00", now), true);
  assert.equal(isStale(null, now), true);
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

test("filterVariants and filterShops", () => {
  const variants = [
    { id: "1", capacity: "256GB", color: "black" },
    { id: "2", capacity: "256GB", color: "silver" },
    { id: "3", capacity: "1TB", color: "black" },
  ];
  assert.deepEqual(filterVariants(variants, { cap: "all", color: "all" }).map((v) => v.id), ["1", "2", "3"]);
  assert.deepEqual(filterVariants(variants, { cap: "256GB", color: "black" }).map((v) => v.id), ["1"]);
  const shops = [{ id: "morimori", name: "森森" }, { id: "mix", name: "MIX" }];
  assert.deepEqual(filterShops(shops, "森").map((s) => s.id), ["morimori"]);
  assert.deepEqual(filterShops(shops, " Mi ").map((s) => s.id), ["mix"]);
  assert.equal(filterShops(shops, "").length, 2);
});

const SHOP = {
  hours: { mon: ["10:00", "19:00"], tue: ["10:00", "19:00"], wed: ["10:00", "19:00"], thu: ["10:00", "19:00"], fri: ["10:00", "19:00"], sat: ["10:00", "19:00"], sun: null },
  closed_dates: ["2026-10-05"],
};
const at = (iso) => new Date(iso);

test("openStatus during opening hours", () => {
  assert.deepEqual(openStatus(SHOP, at("2026-10-02T12:00:00+09:00")), { open: true, text: "Đang mở · đóng 19:00" });
});

test("openStatus before opening today", () => {
  assert.deepEqual(openStatus(SHOP, at("2026-10-02T09:00:00+09:00")), { open: false, text: "Đã đóng · mở 10:00" });
});

test("openStatus exactly at closing time is closed", () => {
  assert.deepEqual(openStatus(SHOP, at("2026-10-02T19:00:00+09:00")), { open: false, text: "Đã đóng · mở 10:00 ngày mai" });
});

test("openStatus skips Sunday and closed_dates", () => {
  // T7 20:00 → CN nghỉ, T2 10/05 nghỉ đột xuất → mở lại T3
  assert.deepEqual(openStatus(SHOP, at("2026-10-03T20:00:00+09:00")), { open: false, text: "Đã đóng · mở 10:00 T3" });
});

test("openStatus uses JST even when given UTC", () => {
  assert.equal(openStatus(SHOP, at("2026-10-02T03:00:00Z")).open, true); // 12:00 JST
});
