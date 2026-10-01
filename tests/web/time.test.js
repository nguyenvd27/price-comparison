import assert from "node:assert/strict";
import { test } from "node:test";
import { formatShortTime } from "../../web/js/logic.js";

const NOW = new Date("2026-10-02T12:00:00+09:00");

test("formatShortTime shows HH:MM for today (JST) and MM/DD otherwise", () => {
  assert.equal(formatShortTime("2026-10-02T02:05:00+09:00", NOW), "02:05");
  assert.equal(formatShortTime("2026-10-01T16:30:00Z", NOW), "01:30"); // = 10/02 01:30 JST
  assert.equal(formatShortTime("2026-10-01T23:50:00+09:00", NOW), "10/01");
  assert.equal(formatShortTime(null, NOW), "—");
});
