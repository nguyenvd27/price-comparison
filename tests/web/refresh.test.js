import assert from "node:assert/strict";
import { test } from "node:test";
import { refreshView } from "../../web/js/logic.js";

const NOW = new Date("2026-10-25T05:32:00Z"); // 14:32 JST
const ago = (s) => new Date(NOW.getTime() - s * 1000).toISOString();
const status = (over) => ({ last_press: ago(600), running: false, cooldown_s: 120, data_sha: "a", ...over });

test("ready: button enabled, shows last press in JST", () => {
  assert.deepEqual(refreshView(status({}), NOW), {
    label: "🔄 Lấy giá mới nhất", disabled: false, note: "Lần bấm gần nhất: 10/25 14:22",
  });
});

test("cooldown counts down m:ss from the last press", () => {
  const view = refreshView(status({ last_press: ago(37) }), NOW);
  assert.equal(view.label, "Bấm lại sau 1:23");
  assert.equal(view.disabled, true);
});

test("running crawl locks the button", () => {
  const view = refreshView(status({ running: true }), NOW);
  assert.equal(view.label, "⏳ Đang lấy giá…");
  assert.equal(view.disabled, true);
});

test("never pressed", () => {
  assert.equal(refreshView(status({ last_press: null }), NOW).note, "Chưa có ai bấm");
});

test("no status (server unreachable) hides the button", () => {
  assert.equal(refreshView(null, NOW), null);
});
