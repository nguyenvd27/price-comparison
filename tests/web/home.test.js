import assert from "node:assert/strict";
import { test } from "node:test";
import { bestDiff, legacyRedirect } from "../../web/js/logic.js";

const NOW = new Date("2026-10-02T12:00:00+09:00");
const FRESH = "2026-10-02T11:30:00+09:00";
const state = (prices, extra = {}) => ({ last_success_at: FRESH, error: null, prices, ...extra });
const CATALOG = {
  shops: [{ id: "a" }, { id: "b" }, { id: "m", mail_only: true }],
  variants: [
    { id: "pm-256-burgundy", model: "pm", apple_price: 239800 },
    { id: "pm-256-black", model: "pm", apple_price: 239800 },
    { id: "duo-256-nightsky", model: "duo", apple_price: 364800 },
  ],
};

test("bestDiff is the largest profit over Apple among ranked shops", () => {
  const latest = { shops: {
    a: state({ "pm-256-burgundy": 255000, "pm-256-black": 236000 }),
    b: state({ "pm-256-burgundy": 256000 }),
    m: state({ "pm-256-burgundy": 270000 }),
  } };
  assert.deepEqual(bestDiff(CATALOG, latest, "pm", NOW), { variant: "pm-256-burgundy", diff: 16200 });
});

test("bestDiff is null when the model has no usable prices", () => {
  const latest = { shops: { a: state({ "pm-256-burgundy": 255000 }, { error: "HTTPError" }) } };
  assert.equal(bestDiff(CATALOG, latest, "pm", NOW), null);
  assert.equal(bestDiff(CATALOG, { shops: {} }, "duo", NOW), null);
});

test("legacyRedirect sends old filter links from home to /iphone-18", () => {
  assert.equal(legacyRedirect("?model=pm&cap=256GB"), "/iphone-18/?model=pm&cap=256GB");
  assert.equal(legacyRedirect("?color=black"), "/iphone-18/?color=black");
  assert.equal(legacyRedirect(""), null);
  assert.equal(legacyRedirect("?utm_source=x"), null);
});
