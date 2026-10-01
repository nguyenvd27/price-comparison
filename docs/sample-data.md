# Dữ liệu mẫu trong `web/data/daily.json`

> ⚠️ **Các điểm giá từ 2026-09-18 đến 2026-10-01 là DỮ LIỆU MẪU, không phải giá thật.**
> Chúng được tạo để xem trước biểu đồ khi chưa có lịch sử. Cần thay bằng giá thật (ví dụ lấy từ bài đăng của các kaitori trên X).

## Phạm vi

| | |
|---|---|
| Ngày | 2026-09-18 (ngày mở bán) → 2026-10-01 (14 ngày) |
| Phiên bản | 16 phiên bản iPhone 18 Pro Max (`pm-*`). iPhone Duo không có dữ liệu mẫu. |
| Đánh dấu | Mỗi điểm mẫu có `"sample": true`, ví dụ `"pm-256-burgundy": {"max": 282000, "shop": "mobaste", "sample": true}` |
| Dữ liệu thật | Từ 2026-10-02 trở đi (crawler ghi, không có cờ `sample`). `history/*.json` chỉ chứa dữ liệu thật. |

Trên web, điểm mẫu được vẽ **rỗng ruột** trên biểu đồ, tooltip ghi "· dữ liệu mẫu", và gợi ý "Nên bán" ghi thêm "(tính trên dữ liệu mẫu)" khi trong 4 tuần còn điểm mẫu.

## Cách tạo

Script `tools/make_sample_daily.py`, seed cố định nên chạy lại ra đúng số cũ:
- Điểm neo: giá thật cao nhất ngày 2026-10-02 của từng phiên bản.
- Ngày mở bán cao hơn khoảng 6.5%, giảm tuyến tính về giá neo.
- Thứ 7 và Chủ nhật thấp hơn 6,000 yên; cộng nhiễu ±1,500 yên; làm tròn tới 1,000 yên.
- Cửa hàng ghi kèm là cửa hàng trả cao nhất ngày 2026-10-02.
- Không ghi đè điểm nào đã là giá thật.

## Thay bằng giá thật

1. Tạo bảng tính (Google Sheets / Excel) với 4 cột, rồi xuất ra CSV (UTF-8):

   ```csv
   date,variant,max,shop
   2026-09-18,pm-256-burgundy,275000,mobaste
   2026-09-18,pm-256-black,"248,000",ichiban
   ```

   - `date`: dạng `YYYY-MM-DD`.
   - `variant`: mã phiên bản trong `web/data/catalog.json`: `pm-<256|512|1tb|2tb>-<burgundy|glacier|black|silver>`.
   - `max`: **giá cao nhất trong ngày** trên các kaitori (có thể có dấu phẩy).
   - `shop`: mã cửa hàng trả giá đó: `morimori`, `ichiban`, `mobaste`, `shouten`, `ichome`, `mix`.

2. Chạy:

   ```bash
   .venv/bin/python -m crawler.import_daily gia_that.csv
   ```

   Mỗi dòng ghi đè đúng ngày + phiên bản đó và **bỏ cờ `sample`**. Dòng sai (mã phiên bản hoặc cửa hàng không tồn tại, ngày sai dạng, giá ngoài khoảng 100,000–1,000,000) sẽ báo lỗi kèm số dòng, và file không bị ghi.

3. Kiểm tra còn bao nhiêu điểm mẫu:

   ```bash
   .venv/bin/python -c "import json;d=json.load(open('web/data/daily.json'));print(sum(v.get('sample',False) for day in d.values() for v in day.values()))"
   ```

   Muốn xóa hết điểm mẫu chưa được thay, xóa các mục có `"sample": true` trong `daily.json`.
