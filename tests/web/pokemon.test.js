import assert from "node:assert/strict";
import { test } from "node:test";
import { bestItemDiff, filterItems, itemDiff, pickPokemonFilters, sortItems } from "../../web/js/logic.js";

const NOW = new Date("2026-10-03T12:00:00+09:00");
const FRESH = "2026-10-03T11:30:00+09:00";
const st = (prices, extra = {}) => ({ last_success_at: FRESH, error: null, prices, ...extra });
const ITEMS = [
  { id: "a", series: "mega", retail: 7200, release: "2026-09-16" },
  { id: "b", series: "mega", retail: 27500, release: "2026-09-16" },
  { id: "c", series: "sv", retail: 5400, release: "2023-06-16" },
  { id: "d", series: "sv", retail: 5800, release: "2025-06-06" },
];
const LATEST = { shops: {
  x: st({ a: 26000, b: 58000, c: 32000 }),
  y: st({ a: 27000 }, { error: "HTTPError: 403" }),
  m: st({ c: 40000 }),
} };
const SHOP_IDS = ["x", "y"]; // "m" là mail only nên không có trong danh sách

test("itemDiff ignores erroring and mail-only shops", () => {
  assert.equal(itemDiff(ITEMS[0], LATEST, SHOP_IDS, NOW), 26000 - 7200);
  assert.equal(itemDiff(ITEMS[2], LATEST, SHOP_IDS, NOW), 32000 - 5400);
  assert.equal(itemDiff(ITEMS[3], LATEST, SHOP_IDS, NOW), null);
});

test("filterItems by series", () => {
  assert.deepEqual(filterItems(ITEMS, { series: "sv" }).map((i) => i.id), ["c", "d"]);
  assert.deepEqual(filterItems(ITEMS, { series: "all" }).map((i) => i.id), ["a", "b", "c", "d"]);
});

test("sortItems newest keeps catalog order on same day", () => {
  assert.deepEqual(sortItems(ITEMS, "newest", LATEST, SHOP_IDS, NOW).map((i) => i.id), ["a", "b", "d", "c"]);
});

test("sortItems diff puts items without price last", () => {
  assert.deepEqual(sortItems(ITEMS, "diff", LATEST, SHOP_IDS, NOW).map((i) => i.id), ["b", "c", "a", "d"]);
});

test("pickPokemonFilters prefers URL and validates", () => {
  const ids = ["mega", "sv"];
  assert.deepEqual(pickPokemonFilters(new URLSearchParams("series=sv"), { sort: "diff" }, ids), { series: "sv", sort: "newest" });
  assert.deepEqual(pickPokemonFilters(new URLSearchParams(""), { series: "mega", sort: "diff" }, ids), { series: "mega", sort: "diff" });
  assert.deepEqual(pickPokemonFilters(new URLSearchParams("series=xx&sort=yy"), {}, ids), { series: "all", sort: "newest" });
});

test("bestItemDiff for the home card", () => {
  const catalog = { items: ITEMS, shops: [{ id: "x" }, { id: "y" }, { id: "m", mail_only: true }] };
  assert.deepEqual(bestItemDiff(catalog, LATEST, NOW), { item: ITEMS[1], diff: 30500 });
  assert.equal(bestItemDiff(catalog, { shops: {} }, NOW), null);
});
