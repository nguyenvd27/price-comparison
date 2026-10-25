import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

const ENV = { GITHUB_TOKEN: "t", PROXY_KEY: "k" };
const realFetch = globalThis.fetch;
let loads = 0;

// Mỗi test một bản Worker mới: bộ nhớ tạm (lần bấm, cache trạng thái) không dính sang test khác.
async function freshWorker() {
  loads += 1;
  return (await import(`../../worker/crawl-trigger.js?v=${loads}`)).default;
}

function run(title, minutesAgo, status = "completed") {
  return { display_title: title, status, created_at: new Date(Date.now() - minutesAgo * 60000).toISOString() };
}

// GitHub giả: trả danh sách lần chạy, mã commit nhánh data, và ghi lại các lần dispatch.
function fakeGitHub(runs) {
  const calls = { dispatch: [] };
  globalThis.fetch = async (url, init = {}) => {
    if (url.endsWith("/dispatches")) {
      calls.dispatch.push(JSON.parse(init.body));
      return new Response(null, { status: 204 });
    }
    if (url.includes("/runs")) return Response.json({ workflow_runs: runs });
    if (url.endsWith("/git/ref/heads/data")) return Response.json({ object: { sha: "abc123" } });
    return new Response("not found", { status: 404 });
  };
  return calls;
}

const req = (path, method = "GET", headers = {}) =>
  new Request(`https://w.example${path}`, { method, headers });

afterEach(() => { globalThis.fetch = realFetch; });

test("status: last button press, running flag, data sha, CORS", async () => {
  const worker = await freshWorker();
  fakeGitHub([run("crawl", 1, "in_progress"), run("crawl (nút bấm)", 10), run("crawl (nút bấm)", 60)]);
  const res = await worker.fetch(req("/status"), ENV);
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("access-control-allow-origin"), "*");
  const body = await res.json();
  assert.equal(body.data_sha, "abc123");
  assert.equal(body.running, true);
  assert.ok(Math.abs(Date.parse(body.last_press) - (Date.now() - 10 * 60000)) < 2000);
  assert.equal(body.cooldown_s, 120);
});

test("status with no button press yet", async () => {
  const worker = await freshWorker();
  fakeGitHub([run("crawl", 5)]);
  const body = await (await worker.fetch(req("/status"), ENV)).json();
  assert.equal(body.last_press, null);
  assert.equal(body.running, false);
});

test("press within 2 minutes of the last press is refused without dispatching", async () => {
  const worker = await freshWorker();
  const calls = fakeGitHub([run("crawl (nút bấm)", 0.5)]);
  const res = await worker.fetch(req("/crawl", "POST"), ENV);
  assert.equal(res.status, 429);
  assert.equal(calls.dispatch.length, 0);
});

test("press after cooldown dispatches a button run; an immediate second press is refused", async () => {
  const worker = await freshWorker();
  const calls = fakeGitHub([run("crawl (nút bấm)", 5), run("crawl", 3)]);
  const res = await worker.fetch(req("/crawl", "POST"), ENV);
  assert.equal(res.status, 202);
  assert.deepEqual(calls.dispatch, [{ ref: "main", inputs: { source: "button" } }]);
  const body = await res.json();
  assert.equal(body.running, true);
  assert.ok(Date.now() - Date.parse(body.last_press) < 2000);
  // GitHub chưa kịp ghi nhận lần chạy mới, nhưng Worker vẫn nhớ lần bấm.
  assert.equal((await worker.fetch(req("/crawl", "POST"), ENV)).status, 429);
  assert.equal(calls.dispatch.length, 1);
});

test("schedule and manual key trigger are not button presses", async () => {
  const worker = await freshWorker();
  const calls = fakeGitHub([]);
  const waits = [];
  await worker.scheduled({}, ENV, { waitUntil: (p) => waits.push(p) });
  await Promise.all(waits);
  assert.equal((await worker.fetch(req("/", "POST"), ENV)).status, 403);
  assert.equal((await worker.fetch(req("/", "POST", { "x-proxy-key": "k" }), ENV)).status, 200);
  assert.deepEqual(calls.dispatch.map((d) => d.inputs.source), ["schedule", "manual"]);
});

test("CORS preflight", async () => {
  const worker = await freshWorker();
  const res = await worker.fetch(req("/crawl", "OPTIONS"), ENV);
  assert.equal(res.status, 204);
  assert.match(res.headers.get("access-control-allow-methods"), /POST/);
});
