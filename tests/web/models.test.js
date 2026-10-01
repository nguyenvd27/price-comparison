import assert from "node:assert/strict";
import { test } from "node:test";
import { filterVariants, groupLabel, hasPrices, modelColors } from "../../web/js/logic.js";

const CATALOG = {
  models: [
    { id: "pm", name: "iPhone 18 Pro Max", colors: ["burgundy", "black"] },
    { id: "duo", name: "iPhone Duo", colors: ["nightsky", "starwhite"], release: "2026-10-23" },
  ],
};
const VARIANTS = [
  { id: "pm-256-black", model: "pm", capacity: "256GB", color: "black" },
  { id: "duo-256-nightsky", model: "duo", capacity: "256GB", color: "nightsky" },
  { id: "duo-1tb-starwhite", model: "duo", capacity: "1TB", color: "starwhite" },
];

test("filterVariants by model", () => {
  assert.deepEqual(filterVariants(VARIANTS, { model: "duo" }).map((v) => v.id), ["duo-256-nightsky", "duo-1tb-starwhite"]);
  assert.deepEqual(filterVariants(VARIANTS, { model: "duo", cap: "256GB" }).map((v) => v.id), ["duo-256-nightsky"]);
  assert.equal(filterVariants(VARIANTS, {}).length, 3);
});

test("modelColors per model and for all", () => {
  assert.deepEqual(modelColors(CATALOG, "duo"), ["nightsky", "starwhite"]);
  assert.deepEqual(modelColors(CATALOG, "all"), ["burgundy", "black", "nightsky", "starwhite"]);
  assert.deepEqual(modelColors(CATALOG, "nope"), []);
});

test("hasPrices", () => {
  const latest = { shops: { a: { prices: { "pm-256-black": 236000 } }, b: { prices: {} } } };
  assert.equal(hasPrices(latest, ["pm-256-black"]), true);
  assert.equal(hasPrices(latest, ["duo-256-nightsky"]), false);
  assert.equal(hasPrices({ shops: {} }, ["pm-256-black"]), false);
});

test("groupLabel before release without prices", () => {
  const latest = { shops: { a: { prices: { "pm-256-black": 236000 } } } };
  assert.equal(groupLabel(CATALOG.models[1], ["duo-256-nightsky"], latest, "2026-10-02"), "iPhone Duo · mở bán 10/23 · chưa có giá kaitori");
  assert.equal(groupLabel(CATALOG.models[0], ["pm-256-black"], latest, "2026-10-02"), "iPhone 18 Pro Max");
});

test("groupLabel hides release note on release day", () => {
  const latest = { shops: { a: { prices: { "duo-256-nightsky": 400000 } } } };
  assert.equal(groupLabel(CATALOG.models[1], ["duo-256-nightsky"], latest, "2026-10-23"), "iPhone Duo");
  assert.equal(groupLabel(CATALOG.models[1], ["duo-256-nightsky"], latest, "2026-10-22"), "iPhone Duo · mở bán 10/23");
});
