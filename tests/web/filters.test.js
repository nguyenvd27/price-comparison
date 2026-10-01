import assert from "node:assert/strict";
import { test } from "node:test";
import { pickFilters } from "../../web/js/logic.js";

const SAVED = { model: "pm", cap: "512GB", color: "black" };

test("pickFilters uses only the URL when it has any filter param", () => {
  assert.deepEqual(pickFilters(new URLSearchParams("color=nightsky"), SAVED), { model: null, cap: null, color: "nightsky" });
  assert.deepEqual(pickFilters(new URLSearchParams("model=duo&cap=1TB"), SAVED), { model: "duo", cap: "1TB", color: null });
});

test("pickFilters falls back to saved filters when the URL has none", () => {
  assert.deepEqual(pickFilters(new URLSearchParams(""), SAVED), SAVED);
  assert.deepEqual(pickFilters(new URLSearchParams("utm_source=x"), {}), { model: null, cap: null, color: null });
});
