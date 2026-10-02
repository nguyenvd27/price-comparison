// Nơi đọc dữ liệu JSON. Chạy local: thư mục data/ cạnh js/, tính theo vị trí file này nên đúng dù mở
// ở trang con (/iphone-18/) hay server đặt gốc ở thư mục repo (/web/…).
// Trên web thật: đọc thẳng từ GitHub, để crawler commit dữ liệu mới mà không phải build lại Cloudflare Pages.
export const DATA_BASE = location.hostname === "localhost" || location.hostname === "127.0.0.1"
  ? new URL("../data/", import.meta.url).href
  : "https://raw.githubusercontent.com/nguyenvd27/price-comparison/main/web/data/";
