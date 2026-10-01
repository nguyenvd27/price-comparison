import assert from "node:assert/strict";
import { test } from "node:test";
import { rankOffers } from "../../web/js/logic.js";

const NOW = new Date("2026-10-02T12:00:00+09:00");
const FRESH = "2026-10-02T11:30:00+09:00";
const SHOPS = ["a", "b", "c", "d", "e", "f"].map((id) => ({ id, name: id.toUpperCase() }));
const shop = (price, extra = {}) => ({ last_success_at: FRESH, error: null, prices: price == null ? {} : { v: price }, ...extra });

test("rankOffers sorts by price with dense ranks for ties", () => {
  const latest = { shops: { a: shop(235000), b: shop(236000), c: shop(236000), d: shop(230000), e: shop(null), f: shop(null) } };
  const rows = rankOffers("v", latest, SHOPS, 239800, NOW);
  assert.deepEqual(
    rows.map((r) => [r.shop.id, r.price, r.diff, r.rank, r.usable]),
    [
      ["b", 236000, -3800, 1, true],
      ["c", 236000, -3800, 1, true],
      ["a", 235000, -4800, 2, true],
      ["d", 230000, -9800, 3, true],
    ],
  );
});

test("rankOffers puts stale or erroring shops last without rank", () => {
  const latest = { shops: {
    a: shop(235000),
    b: shop(299000, { error: "HTTPError: 503" }),
    c: shop(240000, { last_success_at: "2026-09-30T11:30:00+09:00" }),
    d: shop(236000),
  } };
  const rows = rankOffers("v", latest, SHOPS, 239800, NOW);
  assert.deepEqual(
    rows.map((r) => [r.shop.id, r.rank, r.usable]),
    [["d", 1, true], ["a", 2, true], ["b", null, false], ["c", null, false]],
  );
});

test("rankOffers omits shops that do not buy the variant", () => {
  const rows = rankOffers("v", { shops: { a: shop(null) } }, SHOPS, 239800, NOW);
  assert.deepEqual(rows, []);
});
