// Nơi đọc dữ liệu JSON. Chạy local: thư mục data/ cạnh js/, tính theo vị trí file này nên đúng dù mở
// ở trang con (/iphone-18/) hay server đặt gốc ở thư mục repo (/web/…).
// Trên web thật: đọc thẳng từ GitHub để không phải build lại Cloudflare Pages:
// catalog.json (sửa tay) ở nhánh main, giá do crawler cập nhật ở nhánh data (tools/sync-data.sh).
// Giá đọc theo mã commit của nhánh data (Worker trả về) khi có, vì URL theo tên nhánh bị
// raw.githubusercontent.com cache 5 phút.
const LOCAL = location.hostname === "localhost" || location.hostname === "127.0.0.1";
const LOCAL_DATA = new URL("../data/", import.meta.url).href;
const GITHUB = "https://raw.githubusercontent.com/nguyenvd27/price-comparison/";

// Worker (worker/crawl-trigger.js): nút "Lấy giá mới nhất" và mã commit mới nhất của nhánh data.
export const WORKER_URL = "https://kaitori-proxy.ducnguyen272727.workers.dev";

export function dataUrl(path, sha = null) {
  if (LOCAL) return LOCAL_DATA + path;
  return path.endsWith("catalog.json") ? `${GITHUB}main/web/data/${path}` : `${GITHUB}${sha ?? "data"}/${path}`;
}
