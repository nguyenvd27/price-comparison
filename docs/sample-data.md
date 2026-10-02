# Dữ liệu trước khi crawler chạy (9/18–10/01) trong `web/data/daily.json`

Crawler bắt đầu ghi từ 2026-10-02. Các ngày trước đó được bổ sung bằng **giá thật lấy từ bản lưu trên Internet Archive (Wayback Machine)**. Ngày nào không có bản lưu thì để trống. Biểu đồ nối thẳng giữa các ngày có dữ liệu.

## Giá thật đã nhập (`tools/real_prices_2026-09.csv`)

| Ngày | Nguồn (bản lưu Wayback) | Kaitori | Thời điểm giá |
|---|---|---|---|
| 2026-09-18 | `mobile-ichiban.com/Prod/1/01/40` @ 20260918031235 | chỉ 海峡 | 9/18 12:12 JST |
| 2026-09-22 | `is-checker.com/iphone18_betaa.html?12` @ 20260922121929 | cả 6 kaitori | is-checker "更新 09/22 16:06" |
| 2026-09-24 | `is-checker.com/iphone18_beta.html` @ 20260924160141 | cả 6 kaitori | is-checker "更新 09/24 14:24" |
| 2026-09-25 | `is-checker.com/iphone18_beta.html` @ 20260925151141 | cả 6 kaitori | is-checker "更新 09/26 00:10" (giá cuối ngày 9/25) |
| 2026-09-30 | `mobile-ichiban.com/Prod/1` @ 20260930014623 | chỉ 海峡 | 9/30 10:46 JST |

Link đầy đủ có dạng `https://web.archive.org/web/<mốc thời gian>/<url>`.

**Thêm cho màu burgundy (mọi dung lượng), 9/18–10/01:** API công khai của trang so sánh giá miyagadget, `https://iphone-price.miyagadget.page/api/history?modelSlug=iphone-18-pro-max&capacityGb=<256|512|1024|2048>`, lấy ngày 2026-10-02.
- API trả về các mức giá mỗi ngày của từng kaitori, theo dung lượng, **không ghi màu**. Mình lấy giá cao nhất trong ngày của 4 kaitori có trong web: モバイルミックス=mix, 森森買取=morimori, 買取１丁目=ichome, 海峡通信=ichiban.
- Giá này được gán cho **burgundy**, vì burgundy luôn là màu giá cao nhất: ở mọi ngày có giá theo màu (is-checker, 海峡, crawler), burgundy ≥ các màu khác. Đối chiếu ngày 9/22, 9/24 và 9/25: số của miyagadget **trùng khớp** với giá burgundy trên is-checker ở cả 4 dung lượng.
- Ngày đã có giá từ bản lưu thì lấy số cao hơn của hai nguồn.
- Có ngày miyagadget chỉ có giá của 1–3 trong 4 tiệm. Còn trống: 2TB ngày 9/24, 9/27–29, 10/01; 512GB và 1TB ngày 9/27; 1TB ngày 10/01.
- Không dùng 買取比較ナビ (kaitori-pro.app): khách chưa đăng nhập chỉ xem được từ 10/01, và giá theo màu có dấu hiệu bị ghép nhầm (256GB glacier = burgundy). 買取X (kaitorix.app) cần đăng nhập.

- `max` = giá cao nhất trong số các kaitori có dữ liệu ngày đó, tại thời điểm chụp, chưa phải giá cao nhất cả ngày. Hai ngày chỉ có 海峡 (9/18, 9/30) có thể thấp hơn giá cao nhất thật của 6 kaitori.
- Bằng giá thì ghi kaitori đứng trước theo thứ tự trong `catalog.json`.
- Màu trên is-checker được đọc theo class `color-burgundy / glacier / black / silver`.
- Không dùng:
  - Trang sản phẩm 森森 trên Wayback: mỗi bản lưu chỉ có 1 sản phẩm, giá ngày 9/18 còn kèm thưởng "来店+15000".
  - Trang `kaitorishouten-co.jp/keitai` ngày 9/27: bản HTML viết sẵn cho SEO, chỉ có 3 phiên bản.
- Màu glacier, black, silver còn thiếu: 9/19–21, 9/23, 9/26–29, 10/01. Chưa tìm được nguồn công khai có giá theo màu. Các bài trên X cần đăng nhập.

Dữ liệu mẫu (tạo bằng `tools/make_sample_daily.py`, cờ `"sample": true`) đã được xoá khỏi `daily.json`. Web vẫn hỗ trợ cờ này: điểm mẫu vẽ rỗng ruột, tooltip ghi "· dữ liệu mẫu".

## Thêm giá thật cho các ngày còn thiếu

1. Tạo CSV (UTF-8) 4 cột:

   ```csv
   date,variant,max,shop
   2026-09-19,pm-256-burgundy,265000,mobaste
   2026-09-19,pm-256-black,"248,000",ichiban
   ```

   - `date`: dạng `YYYY-MM-DD`.
   - `variant`: `pm-<256|512|1tb|2tb>-<burgundy|glacier|black|silver>`.
   - `max`: giá cao nhất trong ngày (có thể có dấu phẩy).
   - `shop`: `morimori`, `ichiban`, `mobaste`, `shouten`, `ichome` hoặc `mix`.

2. Chạy:

   ```bash
   .venv/bin/python -m crawler.import_daily gia_that.csv
   ```

   Mỗi dòng ghi đè đúng ngày + phiên bản đó. Nếu có dòng sai (mã không tồn tại, ngày sai dạng, giá ngoài 100,000–1,000,000), lệnh báo lỗi kèm số dòng và không ghi file.
