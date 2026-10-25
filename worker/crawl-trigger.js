// Cloudflare Worker: chạy workflow "crawl" trên GitHub.
// - Hẹn giờ (Cron Triggers), vì lịch (schedule) của GitHub Actions với repo này chạy trễ hàng giờ.
// - Nút "Lấy giá mới nhất" trên web: POST /crawl, giới hạn 2 phút một lần cho mọi người.
// - GET /status: lần bấm gần nhất, crawl có đang chạy không, mã commit mới nhất của nhánh data
//   (web đọc dữ liệu theo mã commit để không dính cache 5 phút của raw.githubusercontent.com).
//
// Lần bấm gần nhất lấy từ lịch sử chạy workflow: lần chạy do nút bấm có tên "crawl (nút bấm)"
// (run-name trong crawl.yml), nên không cần database.
//
// Cài đặt (Cloudflare dashboard → Workers & Pages → Worker):
// 1. Edit code → dán file này → Deploy.
// 2. Settings → Variables and Secrets → Secret GITHUB_TOKEN = fine-grained token của GitHub,
//    chỉ repo price-comparison, quyền "Actions: Read and write" (và "Contents: Read", có sẵn).
//    (Secret PROXY_KEY dùng làm khoá để gọi thử bằng tay.)
// 3. Settings → Trigger events → Cron Triggers, thêm 2 lịch (giờ UTC = JST − 9):
//    "*/30 1-10 * * *"  → 10:00–19:30 JST
//    "0 11 * * *"       → 20:00 JST
// Gọi thử bằng tay: POST https://<worker>/ với header "x-proxy-key: <PROXY_KEY>".

const REPO = "https://api.github.com/repos/nguyenvd27/price-comparison";
const BUTTON_TITLE = "crawl (nút bấm)";
const COOLDOWN_MS = 2 * 60 * 1000;
const STATUS_CACHE_MS = 10 * 1000;
// Sau khi bấm, GitHub mất vài giây mới hiện lần chạy mới; trong lúc đó vẫn coi là đang chạy.
const PENDING_MS = 60 * 1000;
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

// Bộ nhớ tạm của Worker (mất khi Worker khởi động lại; chỉ để chặn bấm dồn trong vài giây).
let pressedAt = 0;
let cached = null;

function github(env, path, init = {}) {
  return fetch(REPO + path, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "kaitori-crawl-trigger",
    },
  });
}

function dispatch(env, source) {
  return github(env, "/actions/workflows/crawl.yml/dispatches", {
    method: "POST",
    body: JSON.stringify({ ref: "main", inputs: { source } }),
  });
}

// Đọc từ GitHub: lần bấm gần nhất, có lần chạy nào chưa xong không, mã commit nhánh data.
async function readGitHub(env, fresh) {
  if (!fresh && cached && Date.now() - cached.at < STATUS_CACHE_MS) return cached;
  const [runsRes, refRes] = await Promise.all([
    github(env, "/actions/workflows/crawl.yml/runs?per_page=100"),
    github(env, "/git/ref/heads/data"),
  ]);
  if (!runsRes.ok) throw new Error(`GitHub runs: ${runsRes.status}`);
  const runs = (await runsRes.json()).workflow_runs ?? [];
  const press = runs.find((r) => r.display_title === BUTTON_TITLE);
  cached = {
    at: Date.now(),
    lastPress: press ? Date.parse(press.created_at) : 0,
    running: runs.some((r) => r.status !== "completed"),
    sha: refRes.ok ? (await refRes.json()).object?.sha ?? null : null,
  };
  return cached;
}

async function status(env, fresh = false) {
  const gh = await readGitHub(env, fresh);
  const lastPress = Math.max(gh.lastPress, pressedAt);
  return {
    last_press: lastPress ? new Date(lastPress).toISOString() : null,
    next_allowed: lastPress ? new Date(lastPress + COOLDOWN_MS).toISOString() : null,
    running: gh.running || Date.now() - pressedAt < PENDING_MS,
    data_sha: gh.sha,
    cooldown_s: COOLDOWN_MS / 1000,
  };
}

function json(body, code = 200) {
  return Response.json(body, { status: code, headers: { ...CORS, "Cache-Control": "no-store" } });
}

async function press(env) {
  const before = await status(env, true);
  // Kiểm tra lại pressedAt sau khi chờ GitHub: hai lần bấm gần như cùng lúc chỉ chạy một lần.
  const lastPress = Math.max(Date.parse(before.last_press ?? 0) || 0, pressedAt);
  if (Date.now() - lastPress < COOLDOWN_MS) return json({ error: "cooldown", ...before }, 429);
  const previous = pressedAt;
  pressedAt = Date.now();
  const res = await dispatch(env, "button");
  if (!res.ok) {
    pressedAt = previous;
    return json({ error: `GitHub dispatch: ${res.status}`, ...before }, 502);
  }
  return json(await status(env), 202);
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      dispatch(env, "schedule").then(async (res) => {
        if (!res.ok) console.log(`dispatch failed: ${res.status} ${await res.text()}`);
      }),
    );
  },

  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    try {
      if (pathname === "/status" && request.method === "GET") return json(await status(env));
      if (pathname === "/crawl" && request.method === "POST") return await press(env);
    } catch (err) {
      return json({ error: String(err.message ?? err) }, 502);
    }
    if (request.method !== "POST" || !env.PROXY_KEY || request.headers.get("x-proxy-key") !== env.PROXY_KEY) {
      return new Response("forbidden", { status: 403 });
    }
    const res = await dispatch(env, "manual");
    // GitHub trả 204 khi đã nhận lệnh chạy workflow.
    return new Response(`GitHub dispatch: ${res.status} ${await res.text()}`, { status: res.ok ? 200 : 502 });
  },
};
