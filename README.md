# Kaitori Check

Website so sánh giá thu mua (買取 / kaitori) của các cửa hàng ở Nhật, viết cho cộng đồng người Việt tại Nhật. Giá được crawl tự động 30 phút một lần, từ 10:00 đến 20:00 giờ Nhật.

| Trang | Nội dung |
|---|---|
| `/` | Trang chủ: các danh mục, kèm mức lãi cao nhất hiện tại |
| `/iphone-18/` | iPhone 18 Pro Max và iPhone Duo mới chưa kích hoạt (新品未開封), 17 cửa hàng: bảng so sánh, biểu đồ giá theo ngày, giá theo thứ trong tuần |
| `/pokemon-card/` | BOX Pokémon Card chưa bóc, còn màng co (シュリンク付), 21 BOX × 8 cửa hàng |

Mỗi trang có:

- bảng giá, với 3 cột cố định khi vuốt ngang: sản phẩm, giá gốc, chênh lệch so với giá gốc
- ô giá cao nhất được tô xanh
- cửa sổ xếp hạng các cửa hàng khi bấm vào một ô giá
- giờ mở cửa hôm nay của từng tiệm (🟢 đang mở / 🔴 đã đóng; 📦 = chỉ mua qua bưu điện)

## Kiến trúc

```
Cloudflare Worker (Cron 30 phút)
   │  gọi workflow_dispatch
   ▼
GitHub Actions: crawl.yml
   │  python -m crawler.run --category iphone | pokemon
   ▼
web/data/**/*.json ──git commit──► GitHub (raw.githubusercontent.com)
                                         ▲
Cloudflare Pages (web/, trang tĩnh) ─────┘  trình duyệt đọc JSON trực tiếp từ GitHub
```

- **Không có database.** Dữ liệu là các file JSON trong `web/data/`, được crawler commit vào repo.
- **Crawler commit dữ liệu không làm Cloudflare Pages build lại.** Pages chỉ build khi code thay đổi (watch paths loại trừ `web/data/*`), còn trình duyệt đọc JSON thẳng từ `raw.githubusercontent.com` (xem `web/js/config.js`).
- **Lịch chạy do Cloudflare Worker gọi** (`worker/crawl-trigger.js`). Lịch `schedule` của GitHub Actions chạy trễ hàng giờ với repo này, nên `crawl.yml` không dùng nó.

### Thư mục

```
crawler/                Python: tải trang, đọc giá, cập nhật JSON
  run.py                lệnh chạy: python -m crawler.run [--category iphone|pokemon]
  categories.py         khai báo danh mục: thư mục dữ liệu, danh sách tiệm, giới hạn giá
  update.py             quy tắc cập nhật latest/daily/history
  shops/*.py            parser iPhone (mỗi tiệm 1 file: fetch() + parse())
  pokemon/match.py      ghép sản phẩm của tiệm với BOX trong catalog (theo JAN, rồi theo tên)
  pokemon/shops/*.py    parser Pokémon
  tests/                pytest + fixture HTML/JSON cắt từ trang thật
web/                    trang tĩnh (HTML/CSS/JS module, không cần build)
  data/                 catalog.json (sửa tay), latest.json, daily.json, history/
  data/pokemon/         dữ liệu Pokémon, cùng định dạng
  js/logic.js           hàm thuần dùng chung (có test bằng node --test)
  js/table.js           tiêu đề cột cửa hàng và cửa sổ xếp hạng, dùng chung cho các trang
worker/crawl-trigger.js Cloudflare Worker hẹn giờ chạy crawl
tools/                  script phụ (nhập lịch sử giá từ CSV…)
docs/                   spec thiết kế và ghi chú dữ liệu
```

### Dữ liệu

| File | Nội dung |
|---|---|
| `catalog.json` | Sửa tay: danh sách sản phẩm (giá gốc, màu/JAN, ảnh…) và cửa hàng (link, giờ mở cửa, `mail_only`) |
| `latest.json` | Giá mới nhất của từng tiệm, thời điểm lấy, lỗi nếu có |
| `daily.json` | Giá cao nhất mỗi ngày (giờ Nhật) của từng sản phẩm, dùng cho biểu đồ. Không tính tiệm `mail_only` |
| `history/YYYY-MM.json` | Mỗi lần giá của một tiệm thay đổi |

Quy tắc chính:

- Một tiệm bị lỗi thì giữ giá cũ, chỉ làm mờ cột của tiệm đó.
- Kết quả rỗng, hoặc giá nằm ngoài khoảng hợp lệ (iPhone 100,000–1,000,000; Pokémon 1,000–2,000,000), bị coi là lỗi.
- Trong khung giờ crawl, tiệm quá 2 giờ không có dữ liệu mới bị gắn nhãn "dữ liệu cũ".

## Chạy ở máy

Cần Python 3.12 trở lên và Node 22 trở lên.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Crawl và ghi vào web/data/
.venv/bin/python -m crawler.run                     # iPhone
.venv/bin/python -m crawler.run --category pokemon  # Pokémon BOX

# Xem trang (khi chạy ở localhost, trang đọc dữ liệu từ web/data/ trong máy)
cd web && python3 -m http.server 8765               # mở http://localhost:8765/
```

### Test

```bash
.venv/bin/python -m pytest -q   # crawler
npm test                        # hàm JS trong web/js/logic.js
```

CI (`.github/workflows/ci.yml`) chạy cả hai bộ test mỗi khi push.

## Thêm tiệm hoặc sản phẩm

- **Thêm sản phẩm Pokémon:** thêm một mục vào `items` trong `web/data/pokemon/catalog.json` (`id`, `series`, `name`, `retail`, `release`, `image`, `jan`, `aliases`, `exclude`). Không cần sửa code.
- **Thêm tiệm:**
  1. Viết `crawler/shops/<tiệm>.py` (hoặc `crawler/pokemon/shops/<tiệm>.py`) với `fetch(session)` và `parse(raw, context)`.
  2. Đăng ký tiệm trong `SHOPS` của thư mục đó.
  3. Thêm tiệm vào `shops` trong catalog.
  4. Thêm fixture và test.
- **Tiệm chỉ mua qua bưu điện:** thêm `"mail_only": true` trong catalog. Tiệm đó sẽ hiện 📦, và không được tính vào chênh lệch, ô cao nhất, xếp hạng hay biểu đồ.

## Triển khai

1. **GitHub:**
   - Repo public.
   - Settings → Actions → General → Workflow permissions: **Read and write**, để workflow commit được dữ liệu.
2. **Cloudflare Pages:**
   - Kết nối repo; Build command để trống; Build output directory: `web`.
   - Settings → Build watch paths: Include `*`, Exclude `web/data/*`.
3. **Cloudflare Worker** (`worker/crawl-trigger.js`):
   - Secret `GITHUB_TOKEN`: fine-grained token, chỉ cho repo này, quyền **Actions: Read and write**.
   - Secret `PROXY_KEY`: khoá dùng khi gọi thử Worker bằng tay.
   - Cron Triggers (giờ UTC): `*/30 1-10 * * *` và `0 11 * * *`, tức 10:00–20:00 JST.
   - Đổi giờ crawl thì sửa cả các Cron Triggers này lẫn `CRAWL_HOURS` trong `web/js/logic.js`.

## Hạn chế đã biết

- **モバステ (pastec.net) và 買取wiki chặn IP máy chủ** (GitHub Actions, Cloudflare). Hai tiệm này chỉ crawl được từ IP mạng gia đình. Trên web, cột của chúng giữ giá lần cuối lấy được và bị làm mờ.
- **Một số tiệm ẩn danh sách ngoài giờ làm việc** (ví dụ trang iPhone của ホムラ). Crawler coi đó là lỗi và giữ giá cũ.
- **Parser phụ thuộc giao diện trang của từng tiệm.** Khi một tiệm đổi giao diện, cột của tiệm đó báo "Không lấy được giá nào" cho tới khi sửa parser.
- **Dữ liệu iPhone trước ngày 2026-10-02** được bổ sung từ bản lưu Wayback và dữ liệu công khai của trang so sánh khác. Xem `docs/sample-data.md`.

## Ghi chú

- Giá chỉ để tham khảo; hãy xác nhận trên trang của cửa hàng trước khi bán.
- Trang này không liên kết với Apple, The Pokémon Company hay các cửa hàng được liệt kê. iPhone là thương hiệu của Apple Inc.; Pokémon là thương hiệu của Nintendo / Creatures / GAME FREAK.
- Ảnh trên trang chủ dùng giấy phép CC BY-SA 4.0 (Wikimedia Commons), tác giả ghi ở cuối trang. Ảnh BOX Pokémon được hiển thị trực tiếp từ pokemon-card.com.
