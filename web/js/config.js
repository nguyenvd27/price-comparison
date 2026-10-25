// Nơi đọc dữ liệu JSON. Chạy local: thư mục data/ cạnh js/, tính theo vị trí file này nên đúng dù mở
// ở trang con (/iphone-18/) hay server đặt gốc ở thư mục repo (/web/…).
// Trên web thật: đọc thẳng từ GitHub để không phải build lại Cloudflare Pages:
// catalog.json (sửa tay) ở nhánh main, giá do crawler cập nhật ở nhánh data (tools/sync-data.sh).
const LOCAL = location.hostname === "localhost" || location.hostname === "127.0.0.1";
const LOCAL_DATA = new URL("../data/", import.meta.url).href;
const GITHUB = "https://raw.githubusercontent.com/nguyenvd27/price-comparison/";

export function dataUrl(path) {
  if (LOCAL) return LOCAL_DATA + path;
  return path.endsWith("catalog.json") ? `${GITHUB}main/web/data/${path}` : `${GITHUB}data/${path}`;
}
