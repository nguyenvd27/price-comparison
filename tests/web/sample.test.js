import assert from "node:assert/strict";
import { test } from "node:test";
import { addDays, chartSeries, weekdayStats } from "../../web/js/logic.js";

const CATALOG = {
  colors: { black: { vi: "Đen", hex: "#333" } },
  variants: [{ id: "pm-256-black", model: "pm", capacity: "256GB", color: "black", apple_price: 239800 }],
};

test("chartSeries marks sample points", () => {
  const daily = {
    "2026-10-01": { "pm-256-black": { max: 236000, shop: "a", sample: true } },
    "2026-10-02": { "pm-256-black": { max: 238000, shop: "b" } },
  };
  const { datasets } = chartSeries(daily, CATALOG, "pm", "256GB", 3, "2026-10-02");
  assert.deepEqual(datasets[0].samples, [false, true, false]);
});

function daily28(sampleUntil) {
  const out = {};
  for (let i = 0; i < 28; i++) {
    const d = addDays("2026-10-04", -i);
    out[d] = { "pm-256-black": { max: 250000, shop: "a", ...(d <= sampleUntil ? { sample: true } : {}) } };
  }
  return out;
}

test("weekdayStats reports whether sample data was used", () => {
  assert.equal(weekdayStats(daily28("2026-10-01"), "pm-256-black", "2026-10-04").sample, true);
  assert.equal(weekdayStats(daily28("2000-01-01"), "pm-256-black", "2026-10-04").sample, false);
});
