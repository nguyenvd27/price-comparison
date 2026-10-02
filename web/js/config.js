// Nơi đọc dữ liệu JSON. Chạy local: "data/". Trên web thật: đọc thẳng từ GitHub, để
// crawler commit dữ liệu mới mà không phải build lại Cloudflare Pages.
export const DATA_BASE = location.hostname === "localhost" || location.hostname === "127.0.0.1"
  ? "data/"
  : "https://raw.githubusercontent.com/nguyenvd27/price-comparison/main/web/data/";
