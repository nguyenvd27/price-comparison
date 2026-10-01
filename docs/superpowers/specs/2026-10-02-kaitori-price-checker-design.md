# Thiết kế: Web so sánh giá kaitori iPhone 18 Pro Max

Ngày: 2026-10-02 · Trạng thái: chờ duyệt

## 1. Mục tiêu

Một trang web tiếng Việt, tối giản và dễ nhìn, giúp cộng đồng người Việt ở Nhật xem nhanh giá thu mua (kaitori) iPhone 18 Pro Max **mới, chưa kích hoạt (新品未開封)** ở các cửa hàng. Người dùng cần biết:

- cửa hàng nào đang trả cao nhất cho từng phiên bản (dung lượng × màu);
- bán thì lãi hay lỗ bao nhiêu so với giá Apple;
- cửa hàng đó có đang mở cửa không, và bấm một lần là mở được trang kaitori;
- giá đang lên hay xuống theo ngày, và thứ nào trong tuần thường được giá cao nhất.

Đây là trang công khai cho cộng đồng; sau này có thể gắn quảng cáo. Giai đoạn đầu chạy **hoàn toàn miễn phí**, sau này chuyển lên server riêng.

**Thành công khi:** giá của 6 cửa hàng tự động cập nhật khoảng 15 phút một lần mà không cần ai can thiệp; xem tốt trên điện thoại; một cửa hàng bị lỗi không làm hỏng dữ liệu của các cửa hàng còn lại.

**Ngoài phạm vi bản đầu:** model khác ngoài 18 Pro Max, máy đã qua sử dụng, quảng cáo, tài khoản người dùng, thông báo (push/LINE), crawl giờ mở cửa tự động.

## 2. Nguồn dữ liệu

Tự crawl trực tiếp trang của từng kaitori, **không** lấy dữ liệu từ is-checker.

| Mã | Cửa hàng | Trang giá | Cách lấy |
|---|---|---|---|
| `morimori` | 森森買取 | https://www.morimori-kaitori.jp/category/03 | HTML tĩnh (requests + BeautifulSoup) |
| `ichiban` | 海峡 / モバイル一番 | https://www.mobile-ichiban.com/Prod/1/01/40 | HTML tĩnh |
| `mobaste` | モバステ | https://pastec.net/iphone/ | HTML tĩnh |
| `shouten` | 買取商店 | https://www.kaitorishouten-co.jp/category/1/747 | Trang React: ưu tiên tìm API JSON phía sau, nếu không được thì dùng Playwright |
| `ichome` | 買取1丁目 | https://www.1-chome.com/mobile?category=RGNg976kptBN7UjF | Trang Vue: ưu tiên API JSON, nếu không được thì dùng Playwright |
| `mix` | モバイルミックス | https://mobile-mix.jp/ | Giá tải bằng JS/AJAX: ưu tiên endpoint AJAX, nếu không được thì dùng Playwright |

Quy tắc lịch sự khi crawl: mỗi lần chạy chỉ gửi 1 request (hoặc 1 phiên trình duyệt) cho mỗi cửa hàng, User-Agent có tên dự án, và không crawl dày hơn 15 phút một lần.

## 3. Kiến trúc

```
GitHub Actions (cron */15)  ──►  crawler/ (Python)  ──►  web/data/*.json  ──git commit──►  Cloudflare Pages tự deploy  ──►  web/ (HTML/CSS/JS tĩnh)
```

- Repo trên GitHub để **public**, để dùng GitHub Actions miễn phí không giới hạn phút. Nếu sau này cần repo private, giảm cron xuống `0 * * * *`.
- Không dùng database. Các file JSON trong `web/data/` chính là nơi lưu dữ liệu, và Git giữ toàn bộ lịch sử.
- Workflow chỉ commit khi có file JSON thay đổi.
- Thời gian dùng **giờ Nhật (Asia/Tokyo)** ở mọi nơi. "Một ngày" tính từ 00:00 đến 24:00 JST.

### Cấu trúc thư mục

```
crawler/
  shops/            mỗi cửa hàng 1 file: morimori.py, ichiban.py, mobaste.py, shouten.py, ichome.py, mix.py
  normalize.py      chuẩn hóa tên model / màu / dung lượng về mã biến thể
  store.py          đọc/ghi JSON (lớp duy nhất biết dữ liệu nằm ở đâu)
  run.py            điểm chạy: gọi các parser, áp quy tắc cập nhật, ghi file
  tests/            pytest + HTML mẫu (fixtures) của từng cửa hàng
web/
  index.html, style.css
  js/               app.js (render), logic.js (hàm thuần: lọc, thống kê, trạng thái mở cửa)
  data/catalog.json, latest.json, daily.json, history/YYYY-MM.json
.github/workflows/crawl.yml
```

### Ranh giới giữa các phần

- **Parser cửa hàng:** `fetch() -> list[Offer]`, với `Offer = {variant, price, url}`. Parser chỉ biết trang của cửa hàng mình, không đọc hay ghi file. Thêm cửa hàng mới chỉ cần thêm một file và một dòng trong `catalog.json`.
- **`normalize`:** nhận chuỗi tên sản phẩm của cửa hàng (ví dụ "iPhone 18 Pro Max 256GB ディープブルー") và trả về mã biến thể (`pm-256-blue`) hoặc `None` nếu không phải 18 Pro Max. Bảng ánh xạ màu nằm trong `catalog.json`.
- **`store`:** `load_latest()`, `save_latest()`, `append_history()`, `update_daily()`. Khi chuyển lên server, chỉ cần thay file này bằng bản dùng Postgres.
- **Frontend:** chỉ đọc JSON, không biết gì về crawler.

## 4. Dữ liệu

### `catalog.json` (sửa tay)

```json
{
  "model": "iPhone 18 Pro Max",
  "variants": [{ "id": "pm-256-blue", "capacity": "256GB", "color": "blue", "apple_price": 0 }],
  "colors": { "blue": { "vi": "Xanh", "hex": "#2b3a67", "aliases": ["青", "ブルー", "ディープブルー"] } },
  "shops": [{
    "id": "morimori", "name": "森森", "url": "https://www.morimori-kaitori.jp/category/03",
    "hours": { "mon": ["10:00", "19:00"], "sun": null },
    "closed_dates": ["2026-12-31"],
    "note": "Nhận gửi bưu điện"
  }]
}
```

Danh sách màu, giá Apple (`apple_price`) và giờ mở cửa: khi làm, tra trên apple.com/jp và trang của từng cửa hàng để điền giá trị thật. `hours` ghi khung giờ cho từng thứ; `null` nghĩa là ngày nghỉ.

### `latest.json` (crawler ghi)

```json
{
  "generated_at": "2026-10-02T01:15:00+09:00",
  "shops": {
    "morimori": {
      "last_success_at": "2026-10-02T01:15:00+09:00",
      "display_at": "2026-10-02T00:05:00+09:00",
      "error": null,
      "prices": { "pm-256-blue": 258000 }
    }
  }
}
```

**Quy tắc cập nhật `display_at`** (giờ hiển thị dưới tên cửa hàng): đặt bằng thời điểm hiện tại khi lần crawl thành công **và** (giá của cửa hàng có thay đổi so với lần trước **hoặc** đây là lần crawl thành công đầu tiên trong ngày JST). Các trường hợp còn lại giữ nguyên.

### `history/YYYY-MM.json`

Mảng các sự kiện, mỗi lần một giá thay đổi (kể cả xuất hiện mới hoặc biến mất) ghi thêm một dòng: `{"t": "...", "shop": "morimori", "variant": "pm-256-blue", "price": 258000}`. `price: null` nghĩa là cửa hàng ngừng thu mua phiên bản đó. Biểu đồ chưa dùng file này; nó được giữ lại để tra cứu và dùng cho tính năng sau này.

### `daily.json`

`{ "2026-10-02": { "pm-256-blue": { "max": 262000, "shop": "ichiban" } } }`. Sau mỗi lần crawl thành công, với mỗi biến thể: nếu giá cao nhất hiện tại trên mọi cửa hàng lớn hơn `max` của hôm nay thì cập nhật. Như vậy mỗi ngày ghi lại giá cao nhất từng thấy trong ngày.

## 5. Xử lý lỗi

- Mỗi parser chạy trong một `try` riêng. Nếu có lỗi, ghi `error` vào latest cho cửa hàng đó, **giữ nguyên giá cũ**, không ghi history, và in lỗi ra log của Actions.
- Coi là lỗi nếu: request thất bại, parser trả về 0 offer, hoặc có giá nằm ngoài khoảng 100,000–1,000,000 yên. Như vậy khi trang đổi giao diện, dữ liệu cũ không bị xóa trắng.
- Tên sản phẩm không chuẩn hóa được: bỏ qua dòng đó và in cảnh báo.
- Workflow chỉ báo thất bại (GitHub gửi email) khi **tất cả** cửa hàng đều lỗi. Nếu chỉ một số lỗi, vẫn commit phần thành công.
- Frontend: nếu `last_success_at` của một cửa hàng cũ hơn 2 giờ, hiện nhãn "⚠ dữ liệu cũ" dưới tên cửa hàng.

## 6. Giao diện

Toàn bộ chữ tiếng Việt, tối giản, nền sáng, ưu tiên điện thoại. Dùng HTML/CSS/JS thuần, không cần bước build, Chart.js tải qua CDN.

### Bảng giá (ma trận)

- Mỗi dòng là một biến thể. Thứ tự cột: **Phiên bản** (chấm màu + "256GB Xanh"), **Apple** (giá Apple), **Chênh lệch** (= giá cao nhất − giá Apple; xanh nếu ≥ 0, đỏ nếu < 0), rồi đến các cột cửa hàng.
- **3 cột đầu cố định** (`position: sticky`). Khi vuốt ngang chỉ các cột cửa hàng di chuyển.
- Mỗi ô cửa hàng chỉ hiện giá. Ô có giá cao nhất của dòng được tô xanh. Cửa hàng không thu mua phiên bản đó hiện "—".
- Đầu cột cửa hàng gồm: tên (link sang trang kaitori, mở tab mới, có ↗); `display_at` dạng `10/02 01:15`; trạng thái mở cửa 🟢 "Đang mở · đóng 19:00" hoặc 🔴 "Đã đóng · mở 10:00", tính theo `hours`/`closed_dates` và giờ JST hiện tại; nhãn "⚠ dữ liệu cũ" nếu có.

### Bộ lọc

- Nút chọn dung lượng: Tất cả / 256GB / 512GB / 1TB / 2TB.
- Nút chọn màu: Mọi màu / từng màu (có chấm màu).
- Ô tìm kiếm: lọc **cột cửa hàng** theo tên (tiếng Nhật hoặc mã).
- Lựa chọn lọc được lưu trong URL query (`?cap=256&color=blue`) để chia sẻ link, và trong `localStorage` (bọc try/catch).

### Biểu đồ giá theo ngày (Chart.js, dạng đường)

- Chọn **một dung lượng** (mặc định theo bộ lọc dung lượng, hoặc 256GB nếu bộ lọc là "Tất cả"). Mỗi màu là một đường có màu `hex` của máy. Mỗi điểm là `daily.max` của ngày đó, các điểm nối với nhau.
- Thêm đường ngang nét đứt cho giá Apple.
- Nền các ngày Thứ 7 và Chủ nhật được tô màu cam nhạt.
- Chọn khoảng thời gian: 7 ngày / 30 ngày (mặc định) / Tất cả.
- Chạm hoặc di chuột vào điểm sẽ hiện ngày, giá và cửa hàng trả cao nhất.

### Thống kê theo thứ (Chart.js, dạng cột)

- Dùng chung lựa chọn dung lượng với biểu đồ đường. Mỗi màu xem riêng qua một nút chọn, mặc định là màu đầu tiên.
- Dữ liệu: 28 ngày gần nhất trong `daily.json`. Với mỗi tuần (T2–CN), lấy `max` từng ngày trừ trung bình của tuần đó, rồi lấy trung bình độ lệch theo từng thứ.
- 7 cột T2→CN, cột xanh khi > 0 và đỏ khi < 0. Kèm dòng gợi ý: "Nên bán: Thứ X, trung bình cao hơn Thứ Y khoảng ¥Z", với X là thứ cao nhất và Y là thứ thấp nhất.
- Nếu có ít hơn 14 ngày dữ liệu: hiện "Đang thu thập dữ liệu (cần thêm N ngày)" thay cho biểu đồ.

## 7. Kiểm thử

- **Parser:** lưu một bản HTML/JSON mẫu của từng cửa hàng vào `crawler/tests/fixtures/` và kiểm tra parser trả về đúng các biến thể và giá. Khi trang cửa hàng đổi giao diện, cập nhật fixture rồi sửa parser.
- **normalize:** bảng các trường hợp tên tiếng Nhật → mã biến thể, gồm cả trường hợp model khác phải ra `None`.
- **run/store:** quy tắc `display_at` (giá đổi, lần đầu trong ngày, không đổi), giữ giá cũ khi lỗi, chặn giá vô lý, ghi history chỉ khi giá thay đổi, cập nhật `daily.max`.
- **Frontend `logic.js`:** kiểm tra bằng `node --test`: lọc, tính chênh lệch, trạng thái mở cửa theo JST (có trường hợp ranh giới giờ và ngày nghỉ), thống kê theo thứ, ngưỡng 14 ngày.
- Workflow có thể chạy tay (`workflow_dispatch`) để thử ngay.

## 8. Triển khai và chuyển lên server sau này

- Cloudflare Pages kết nối repo GitHub, thư mục xuất bản là `web/`, không có build command.
- Khi chuyển lên server: chạy `crawler/run.py` bằng cron trên VPS, đổi `store.py` sang Postgres (hoặc đưa vào Rails) và thêm API trả về JSON cùng định dạng. Frontend và các parser không phải đổi.
