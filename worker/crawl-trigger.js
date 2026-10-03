// Cloudflare Worker: hẹn giờ chạy workflow "crawl" trên GitHub, vì lịch (schedule) của GitHub Actions
// với repo này không tự chạy. Cloudflare Cron Triggers chạy đúng giờ và miễn phí.
//
// Cài đặt (Cloudflare dashboard → Workers & Pages → Worker):
// 1. Edit code → dán file này → Deploy.
// 2. Settings → Variables and Secrets → Secret GITHUB_TOKEN = fine-grained token của GitHub,
//    chỉ repo price-comparison, quyền "Actions: Read and write".
//    (Secret PROXY_KEY đã có dùng làm khoá để gọi thử bằng tay.)
// 3. Settings → Trigger events → Cron Triggers, thêm 2 lịch (giờ UTC = JST − 9):
//    "*/30 1-10 * * *"  → 10:00–19:30 JST
//    "0 11 * * *"       → 20:00 JST
// Gọi thử bằng tay: POST https://<worker>/ với header "x-proxy-key: <PROXY_KEY>".

const WORKFLOW = "https://api.github.com/repos/nguyenvd27/price-comparison/actions/workflows/crawl.yml/dispatches";

async function dispatch(env) {
  return fetch(WORKFLOW, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "kaitori-crawl-trigger",
    },
    body: JSON.stringify({ ref: "main" }),
  });
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      dispatch(env).then(async (res) => {
        if (!res.ok) console.log(`dispatch failed: ${res.status} ${await res.text()}`);
      }),
    );
  },

  async fetch(request, env) {
    if (request.method !== "POST" || !env.PROXY_KEY || request.headers.get("x-proxy-key") !== env.PROXY_KEY) {
      return new Response("forbidden", { status: 403 });
    }
    const res = await dispatch(env);
    // GitHub trả 204 khi đã nhận lệnh chạy workflow.
    return new Response(`GitHub dispatch: ${res.status} ${await res.text()}`, { status: res.ok ? 200 : 502 });
  },
};
