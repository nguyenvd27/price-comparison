// Nút "Lấy giá mới nhất": gọi Worker chạy crawl (giới hạn 2 phút một lần cho mọi người),
// theo dõi trạng thái, và báo trang tải lại giá khi nhánh data có commit mới.
import { WORKER_URL } from "./config.js";
import { refreshView } from "./logic.js";

const FAST_POLL_MS = 15 * 1000; // khi đang crawl
const SLOW_POLL_MS = 60 * 1000; // bình thường: để thấy người khác vừa bấm

export async function fetchStatus() {
  try {
    const res = await fetch(`${WORKER_URL}/status`, { cache: "no-store", signal: AbortSignal.timeout(4000) });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

// el: khung chứa nút; status: kết quả fetchStatus() lúc tải trang;
// onNewData(sha): tải lại giá theo mã commit mới của nhánh data.
export function setupRefresh(el, status, onNewData) {
  let current = status;
  let sha = status?.data_sha ?? null;
  let error = "";
  let timer = null;
  el.innerHTML = `<button type="button" class="refresh-btn"></button><span class="refresh-note"></span>`;
  const button = el.querySelector("button");
  const note = el.querySelector(".refresh-note");

  function render() {
    const view = refreshView(current, new Date());
    el.hidden = !view;
    if (!view) return;
    button.textContent = view.label;
    button.disabled = view.disabled;
    note.textContent = error || view.note;
  }

  function schedule(ms) {
    clearTimeout(timer);
    timer = setTimeout(poll, ms);
  }

  async function poll() {
    const next = await fetchStatus();
    if (next) {
      current = next;
      error = "";
      if (next.data_sha && next.data_sha !== sha) {
        sha = next.data_sha;
        await onNewData(sha);
      }
    }
    render();
    schedule(current?.running ? FAST_POLL_MS : SLOW_POLL_MS);
  }

  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      const res = await fetch(`${WORKER_URL}/crawl`, { method: "POST" });
      const body = await res.json();
      const { error: failure, ...next } = body;
      current = { ...current, ...next };
      error = res.ok || res.status === 429 ? "" : "Không gửi được yêu cầu, hãy thử lại sau.";
      if (failure && res.status !== 429) console.warn(failure);
    } catch {
      error = "Không gửi được yêu cầu, hãy thử lại sau.";
    }
    render();
    schedule(FAST_POLL_MS);
  });

  render();
  setInterval(render, 1000); // đếm ngược
  schedule(current?.running ? FAST_POLL_MS : SLOW_POLL_MS);
}
