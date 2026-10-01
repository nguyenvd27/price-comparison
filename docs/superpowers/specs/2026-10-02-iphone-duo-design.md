# Thiết kế: thêm iPhone Duo (chưa crawl)

Ngày: 2026-10-02 · Trạng thái: chờ duyệt · Bổ sung cho `2026-10-02-kaitori-price-checker-design.md`

## 1. Mục tiêu

Hiển thị iPhone Duo trong cùng bảng với iPhone 18 Pro Max, kèm bộ lọc dòng máy. **Giai đoạn này chưa crawl giá Duo**: các dòng Duo hiện giá Apple và "—" ở mọi ô cửa hàng. Việc crawl Duo (tự tìm trang Duo trên từng cửa hàng) sẽ làm ở một bước sau và không nằm trong spec này.

Thông tin Duo (Apple Japan, công bố 2026-09-10): mở bán 2026-10-23; 4 dung lượng 256GB ¥364,800 · 512GB ¥399,800 · 1TB ¥469,800 · 2TB ¥574,800; 2 màu ナイトスカイ (Night Sky) và スターホワイト (Star White).

**Thành công khi:** người dùng thấy 16 dòng Pro Max và 8 dòng Duo trong một bảng chia nhóm; lọc được theo dòng máy, dung lượng và màu; crawler vẫn chỉ ra giá Pro Max và không sinh giá cho màu của Duo.

## 2. Dữ liệu: `web/data/catalog.json`

- Thay khóa `"model": "iPhone 18 Pro Max"` bằng danh sách `models` (theo thứ tự hiển thị):
  ```json
  "models": [
    {"id": "pm", "name": "iPhone 18 Pro Max", "short": "18 Pro Max", "colors": ["burgundy", "glacier", "black", "silver"], "crawl": true},
    {"id": "duo", "name": "iPhone Duo", "short": "Duo", "colors": ["nightsky", "starwhite"], "release": "2026-10-23", "crawl": false}
  ]
  ```
- Thêm vào `colors`:
  - `"nightsky": {"vi": "Night Sky", "hex": "#1f2a44", "aliases": ["ナイトスカイ"]}`
  - `"starwhite": {"vi": "Star White", "hex": "#ecebe4", "aliases": ["スターホワイト"]}`
- Mọi phiên bản có thêm trường `"model"`: `"pm"` cho 16 phiên bản cũ, `"duo"` cho 8 phiên bản mới. Mã phiên bản Duo dạng `duo-<256|512|1tb|2tb>-<nightsky|starwhite>`, theo thứ tự dung lượng rồi đến màu.

## 3. Crawler

- `crawler/run.py` chỉ đưa vào parser các màu thuộc những dòng máy có `"crawl": true`. Nếu không giới hạn, `parse_deductions` sẽ coi Night Sky và Star White là "màu không bị trừ tiền" và sinh giá Pro Max cho hai màu đó.
- Parser, quy tắc cập nhật và định dạng `latest.json`, `daily.json`, `history/` giữ nguyên.

## 4. Giao diện

### Bộ lọc
- Thêm hàng **dòng máy** trước hàng dung lượng: `Tất cả | 18 Pro Max | Duo`, hiện bằng chữ (`short`).
- Hàng **màu** chỉ hiện chấm màu của dòng máy đang chọn; chọn "Tất cả" thì hiện màu của mọi dòng máy theo thứ tự trong `models`.
- Đổi dòng máy mà màu đang chọn không thuộc dòng máy đó: màu về "Mọi màu".
- URL: `?model=duo&cap=256GB&color=nightsky`. Giá trị không hợp lệ về "Tất cả". Bộ lọc vẫn lưu trong `localStorage` như hiện tại.

### Bảng
- Một bảng chung. Mỗi dòng máy còn phiên bản sau khi lọc có một **dòng tiêu đề nhóm** kéo hết chiều ngang bảng. Nội dung tiêu đề luôn nằm ở mép trái (sticky) khi vuốt ngang.
  - Pro Max: `iPhone 18 Pro Max`
  - Duo: `iPhone Duo · mở bán 10/23 · chưa có giá kaitori`. Phần "mở bán 10/23" chỉ hiện khi hôm nay (JST) trước ngày `release`. Phần "chưa có giá kaitori" chỉ hiện khi không cửa hàng nào có giá cho dòng máy đó.
- Các dòng phiên bản giữ nguyên định dạng: chấm màu + dung lượng, giá Apple, Chênh lệch, các ô cửa hàng. Khi không có giá, Chênh lệch và ô cửa hàng hiện "—".
- Modal giữ nguyên, chỉ mở khi ô có giá.

### Biểu đồ
- Thêm hàng chọn **dòng máy** (`18 Pro Max | Duo`) trước hàng chọn dung lượng của biểu đồ. Bộ lọc dòng máy ở bảng khác "Tất cả" thì biểu đồ đổi theo.
- Biểu đồ đường chỉ vẽ phiên bản thuộc dòng máy và dung lượng đã chọn. Đường giá Apple dùng giá của dòng máy đó.
- Nếu dòng máy đó chưa có dữ liệu ngày nào trong khoảng đang xem: ẩn canvas, hiện "Chưa có dữ liệu giá".
- Thống kê theo thứ: nút chọn màu chỉ hiện màu của dòng máy đang chọn. Khi đổi dòng máy, màu chuyển về màu đầu tiên của dòng máy đó.

## 5. Kiểm thử

- `node --test`:
  - `filterVariants` lọc theo `model`.
  - `modelColors(catalog, model)` trả về màu theo dòng máy, hoặc của mọi dòng máy khi chọn "all".
  - `chartSeries` chỉ lấy phiên bản của dòng máy đã chọn.
  - `hasPrices(latest, variantIds)` cho biết dòng máy đã có giá chưa.
- `pytest`: `run.main` với catalog có màu Duo nhưng `crawl: false` không sinh giá cho màu Duo.
- Trình duyệt: bảng chia nhóm (tiêu đề nhóm sticky khi vuốt ngang), bộ lọc dòng máy/màu/dung lượng, URL, biểu đồ Duo "Chưa có dữ liệu giá", màn hình điện thoại.
