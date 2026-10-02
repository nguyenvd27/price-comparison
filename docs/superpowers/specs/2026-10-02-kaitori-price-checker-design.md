# Thiết kế: Web so sánh giá kaitori iPhone 18 Pro Max

Ngày: 2026-10-02 · Trạng thái: chờ duyệt

## 1. Mục tiêu

Một trang web tiếng Việt, tối giản và dễ nhìn, giúp cộng đồng người Việt ở Nhật xem nhanh giá thu mua (kaitori) iPhone 18 Pro Max **mới, chưa kích hoạt (新品未開封)** ở các cửa hàng. Người dùng cần biết:

- cửa hàng nào đang trả cao nhất cho từng phiên bản (dung lượng × màu);
- bán thì lãi hay lỗ bao nhiêu so với giá Apple;
- cửa hàng đó có đang mở cửa không, và bấm một lần là mở được trang kaitori;
- giá đang lên hay xuống theo ngày, và thứ nào trong tuần thường được giá cao nhất.

Đây là trang công khai cho cộng đồng; sau này có thể gắn quảng cáo. Giai đoạn đầu chạy **hoàn toàn miễn phí**, sau này chuyển lên server riêng.

**Thành công khi:** giá của 6 cửa hàng tự động cập nhật 30 phút một lần trong khung 10:00–20:00 JST mà không cần ai can thiệp; xem tốt trên điện thoại; một cửa hàng bị lỗi không làm hỏng dữ liệu của các cửa hàng còn lại.

**Ngoài phạm vi bản đầu:** model khác ngoài 18 Pro Max, máy đã qua sử dụng, quảng cáo, tài khoản người dùng, thông báo (push/LINE), crawl giờ mở cửa tự động.

## 2. Nguồn dữ liệu

Tự crawl trực tiếp trang của từng kaitori, **không** lấy dữ liệu từ is-checker.

| Mã | Cửa hàng | Trang giá | Cách lấy |
|---|---|---|---|
| `morimori` | 森森買取 | https://www.morimori-kaitori.jp/category/0301070 | HTML tĩnh (requests + BeautifulSoup), mỗi màu một dòng |
| `ichiban` | 海峡 / モバイル一番 | https://www.mobile-ichiban.com/Prod/1/01/40 | HTML tĩnh, giá gốc + ghi chú trừ tiền theo màu |
| `mobaste` | モバステ | https://pastec.net/iphone?series_child_id=644 | HTML tĩnh, giá gốc + ghi chú trừ tiền theo màu |
| `shouten` | 買取商店 | https://www.kaitorishouten-co.jp/category/1/747 | API JSON `/api/v1/products?category_id=747`, giá nhãn `新品`. **Không** đọc HTML của trang: đó là bản render sẵn cho SEO, chỉ tạo lại mỗi ngày một lần nên lệch với giá thật (đã gặp 8/16 phiên bản sai ngày 2026-10-02) |
| `ichome` | 買取1丁目 | https://www.1-chome.com/mobile?category=eOd8WFZllXmBd3Rt | API JSON công khai `/api/keitai/listPage?cateCode=eOd8WFZllXmBd3Rt` (giá theo màu = giá 未開封 + `varPrice`) |
| `mix` | モバイルミックス | https://mobile-mix.jp/?category=7 | HTML tĩnh, nhưng phải gọi trang chủ trước để nhận cookie (nếu không sẽ bị chuyển sang `/cookie-error`); giá gốc + ghi chú trừ tiền, có trường hợp "バーガンディのみ 他色買取不可" (màu khác không thu mua) |
| `akimoba` | アキモバ | https://akiba-mobile.co.jp/ | Bảng trên trang chủ: tên máy (màu tiếng Anh) \| 未開封品 \| giá |
| `homura` | 買取ホムラ | https://kaitori-homura.com/products?q[product_sub_category_id_eq]=192… | Danh mục 18 Pro Max, thẻ "【未開封】… burgundy" (màu tiếng Anh) |
| `rudeya` | 買取ルデヤ | https://kaitori-rudeya.com/category/detail/253 | Thẻ 新品 … 未開封, mỗi màu một thẻ; bỏ qua "郵送買取 +500円" |
| `wiki` | 買取wiki | https://iphonekaitori.tokyo/series/iphone | Thẻ `div.pro_list`, mỗi màu một thẻ |
| `rakuen` | 買取楽園 | https://www.keitairakuen.com/…/iphone18-promax/ | Thẻ mỗi dung lượng: "新品: ¥…" là giá màu không được nhắc; "黒/青 231,000" là giá riêng các màu đó |
| `base` | 買取BASE | https://kaitori-base.com/?p=9907 | Bài bảng giá cập nhật hằng ngày: "18 ProMax 256GB \| 257,500 \| 青,黒-20,000、銀-24,000" |
| `sommelier` | 買取ソムリエ | https://somurie-kaitori.com/products?category=1 | Thẻ `div.ant-card` có "新品未開封", mỗi màu một thẻ |
| `jcka` | JCKA | https://www.jcka-mobile.co.jp/kisyu/iphone/ | Bảng mỗi dung lượng, dòng "未開封 判定〇": giá gốc + "青・黒・白-20,000" |

Màu viết tắt một chữ Hán (青 = glacier, 黒 = black, 銀/白 = silver) chỉ dùng trong parser của 楽園, JCKA, BASE (`kanji_colors`). Chưa thêm: 携帯空間 (giá theo màu chỉ hiện trong giờ 11–19 bằng JavaScript) và エノキン (Cloudflare chặn bằng màn "Just a moment…").

Đã kiểm tra ngày 2026-10-02: cả 6 cửa hàng đều lấy được bằng `requests`, **không cần Playwright**.

Quy tắc lịch sự khi crawl: mỗi lần chạy chỉ gửi 1 request (hoặc 1 phiên trình duyệt) cho mỗi cửa hàng, User-Agent có tên dự án, và không crawl dày hơn 15 phút một lần.

## 3. Kiến trúc

```
GitHub Actions (cron 30 phút, 10:00–20:00 JST) ──► crawler/ (Python) ──► web/data/*.json ──git commit──► GitHub
                                                                           │
Cloudflare Pages (web/: HTML/CSS/JS) ──trình duyệt fetch──► raw.githubusercontent.com/.../web/data/*.json
```

- Repo trên GitHub để **public**, để dùng GitHub Actions miễn phí không giới hạn phút. Nếu sau này cần repo private, giảm cron xuống `0 * * * *`.
- Không dùng database. Các file JSON trong `web/data/` chính là nơi lưu dữ liệu, và Git giữ toàn bộ lịch sử.
- Workflow chỉ commit khi có file JSON thay đổi.
- **Dữ liệu không đi qua bước deploy của Cloudflare Pages.** Gói miễn phí chỉ cho 500 lần build mỗi tháng, mà dữ liệu có thể đổi vài chục lần mỗi ngày. Vì vậy trình duyệt đọc JSON trực tiếp từ `raw.githubusercontent.com` (có CORS `*`, cache 5 phút). Đường dẫn này cấu hình trong `web/js/config.js`; khi chạy local thì để `data/`. Trong Cloudflare Pages, đặt build watch paths loại trừ `web/data/*`, để chỉ build lại khi code thay đổi.
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

- **Parser cửa hàng:** mỗi module có `fetch(session) -> str` và `parse(raw, colors) -> list[Offer]`, với `Offer = {variant, price}`. Link sang cửa hàng lấy từ `catalog.json`. Parser chỉ biết trang của cửa hàng mình, không đọc hay ghi file. Thêm cửa hàng mới chỉ cần thêm một file và một dòng trong `catalog.json`.
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

**`last_success_at`** chỉ cập nhật khi giá đổi, khi là lần đầu trong ngày, hoặc khi giá trị cũ đã quá 60 phút. Nhờ vậy, nếu giá không đổi thì file chỉ thay đổi khoảng 1 lần mỗi giờ thay vì 15 phút một lần (ít commit hơn), mà vẫn đủ để phát hiện dữ liệu cũ sau 2 giờ. Chỉ tính thời gian trong khung crawl 10:00–20:00 JST (`CRAWL_HOURS` trong `web/js/logic.js`), nên ban đêm dữ liệu không bị coi là cũ. Nếu không cửa hàng nào thay đổi, `latest.json` được giữ nguyên, kể cả `generated_at`.

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

Toàn bộ chữ tiếng Việt, tối giản, nền sáng, ưu tiên điện thoại. **Màu máy chỉ hiển thị bằng chấm màu**, không hiện tên màu (tên màu chỉ nằm trong tooltip). Dùng HTML/CSS/JS thuần, không cần bước build, Chart.js tải qua CDN.

### Bảng giá (ma trận)

- Mỗi dòng là một biến thể. Thứ tự cột: **Phiên bản** (chấm màu + "256GB"), **Apple** (giá Apple), **Chênh lệch** (= giá cao nhất − giá Apple; xanh nếu ≥ 0, đỏ nếu < 0), rồi đến các cột cửa hàng.
- **3 cột đầu cố định** (`position: sticky`). Khi vuốt ngang chỉ các cột cửa hàng di chuyển.
- Mỗi ô cửa hàng chỉ hiện giá. Ô có giá cao nhất của dòng được tô xanh. Cửa hàng không thu mua phiên bản đó hiện "—".
- Đầu cột cửa hàng gồm: tên (link sang trang kaitori, mở tab mới, có ↗); `display_at` dạng `10/02 01:15`; trạng thái mở cửa 🟢 "Đang mở · đóng 19:00" hoặc 🔴 "Đã đóng · mở 10:00", tính theo `hours`/`closed_dates` và giờ JST hiện tại; nhãn "⚠ dữ liệu cũ" nếu có.

### Modal khi bấm ô giá

- Bấm (hoặc Enter) vào ô giá của một cửa hàng sẽ mở modal (`<dialog>`). Đóng bằng ✕, Esc, hoặc bấm ra ngoài.
- Đầu modal: chấm màu + dung lượng, giá Apple. Phần tóm tắt: "<cửa hàng> trả ¥…", **Lãi** = giá đó − giá Apple (xanh/đỏ), và **Hạng X / N**.
- Danh sách mọi cửa hàng thu mua phiên bản đó, xếp giá từ cao xuống thấp: Hạng, tên (link ↗), giá, chênh lệch so với giá Apple. Bằng giá thì cùng hạng (1, 1, 2…). Cửa hàng lỗi hoặc dữ liệu cũ hiện xám ở cuối, không có hạng. Dòng đang chọn được tô nổi bật.

### Bộ lọc

- Nút chọn dung lượng: Tất cả / 256GB / 512GB / 1TB / 2TB.
- Nút chọn màu: Mọi màu / từng màu (có chấm màu).
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

- Cloudflare Pages kết nối repo GitHub, thư mục xuất bản là `web/`, không có build command, build watch paths loại trừ `web/data/*`.
- `web/js/config.js` trỏ `DATA_BASE` tới `https://raw.githubusercontent.com/<user>/<repo>/main/web/data/`.
- Khi chuyển lên server: chạy `crawler/run.py` bằng cron trên VPS, đổi `store.py` sang Postgres (hoặc đưa vào Rails) và thêm API trả về JSON cùng định dạng. Frontend và các parser không phải đổi.
