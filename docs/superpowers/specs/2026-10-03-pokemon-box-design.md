# Thiết kế: so sánh giá thu mua BOX Pokémon Card

Ngày: 2026-10-03 · Trạng thái: chờ duyệt · Bổ sung cho `2026-10-02-kaitori-price-checker-design.md`

## 1. Mục tiêu

Trang `/pokemon-card/` giúp người Việt ở Nhật biết bán **BOX Pokémon Card chưa bóc, còn màng co (シュリンク付)** ở đâu được giá cao nhất. Trang tham khảo: pokeca-box-hikaku.com.

**Thành công khi:**
- Bảng hiện giá của 8 tiệm cho 21 BOX đang được thu mua.
- Giá tự cập nhật cùng lịch với iPhone (30 phút/lần, 10:00–20:00 JST).
- Xem tốt trên điện thoại.
- Một tiệm lỗi không làm hỏng dữ liệu tiệm khác, cũng không làm hỏng dữ liệu iPhone.

**Không làm lần này:**
- biểu đồ (dữ liệu hằng ngày vẫn được lưu)
- thẻ lẻ, thùng (カートン), gói lẻ (パック), deck/set
- bản DX và スペシャルBOX

## 2. Kiến trúc: tổng quát hoá theo "danh mục"

Phần lõi dùng chung giữ nguyên hành vi:
- quy tắc cập nhật trong `crawler/update.py`
- đọc/ghi JSON trong `crawler/store.py`
- HTTP trong `crawler/http.py`
- khung giờ crawl và quy tắc "dữ liệu cũ" trên web

Mỗi danh mục khai báo:

| | iPhone (đã có) | Pokémon (mới) |
|---|---|---|
| Thư mục dữ liệu | `web/data/` (giữ nguyên để link GitHub raw không đổi) | `web/data/pokemon/` |
| Parser | `crawler/shops/*.py` | `crawler/pokemon/shops/*.py` |
| Thứ parser cần | bảng màu (`crawl_colors`) | danh sách BOX trong catalog |
| Giá hợp lệ | 100,000–1,000,000 | 1,000–2,000,000 |

- Lệnh chạy: `python -m crawler.run --category pokemon`. Không có `--category` thì mặc định `iphone`, nên mọi lệnh và test hiện có giữ nguyên.
- `crawl.yml` chạy lần lượt `--category iphone` rồi `--category pokemon` trong cùng một job, rồi commit thư mục `web/data` một lần. Bước Pokémon chạy cả khi bước iPhone lỗi (`if: always()`).
- Định dạng `latest.json`, `history/YYYY-MM.json`, `daily.json` giống iPhone; khoá giá là `id` của BOX thay vì mã phiên bản iPhone.
- `daily.json` vẫn bỏ qua tiệm `mail_only`.

## 3. Catalog: `web/data/pokemon/catalog.json` (sửa tay)

```json
{
  "series": [
    {"id": "mega", "name": "MEGA"},
    {"id": "sv", "name": "SV"}
  ],
  "items": [
    {"id": "mega-30th", "series": "mega", "name": "30th CELEBRATION", "retail": 7200,
     "release": "2026-09-16", "image": "https://www.pokemon-card.com/products/2026/images/30th_celebration.jpg",
     "jan": ["4521329462424"], "aliases": ["30th CELEBRATION"], "exclude": ["FUTURISTIC"]}
  ],
  "shops": [ /* giống catalog iPhone: id, name, url, hours, closed_dates, note, mail_only? */ ]
}
```

- **`id`:** dạng `<dòng>-<tên>`, không kèm mã bộ thẻ.
- **`release`:** ngày phát hành chính thức, lấy từ API trang sản phẩm của pokemon-card.com (`/products/resultAPI.php`). "Newest" trên web sắp theo trường này. BOX phát hành cùng ngày giữ thứ tự trong catalog.
- **`image`:** link tuyệt đối tới ảnh trên pokemon-card.com (`tumbsImg` của API trên). Ảnh là gói thẻ của bộ đó, riêng FUTURISTIC BOX là ảnh hộp. Mình nhập tay link ảnh vào catalog, crawler không đụng tới.
- **`retail`:** giá gốc đã gồm thuế (定価), theo giá niêm yết công khai.
- **`aliases`:** chuỗi để ghép theo tên khi tiệm không ghi JAN.
- **`exclude`:** chuỗi mà nếu có trong tên thì không phải BOX này. Ví dụ "30th CELEBRATION" phải loại "FUTURISTIC".

**21 BOX ban đầu** (JAN đối chiếu từ 森森 và ルデヤ ngày 2026-10-02; giá gốc theo bảng giá công khai; ngày phát hành và ảnh theo pokemon-card.com. Mình đã kiểm tra: cả 21 BOX đều có ảnh):

| id | Dòng | Tên | 定価 | Phát hành | JAN |
|---|---|---|---|---|---|
| mega-30th-futuristic | mega | 30th CELEBRATION FUTURISTIC BOX | 27,500 | 2026-09-16 | 4521329463872 |
| mega-30th | mega | 30th CELEBRATION | 7,200 | 2026-09-16 | 4521329462424 |
| mega-storm-emeralda | mega | ストームエメラルダ | 6,000 | 2026-07-31 | 4521329462233 |
| mega-abyss-eye | mega | アビスアイ | 6,000 | 2026-05-22 | 4521329462127 |
| mega-ninja-spinner | mega | ニンジャスピナー | 5,400 | 2026-03-13 | 4521329432786 |
| mega-munikis-zero | mega | ムニキスゼロ | 5,400 | 2026-01-23 | 4521329432274 |
| mega-mega-dream-ex | mega | MEGAドリームex | 5,500 | 2025-11-28 | 4521329431932 |
| mega-inferno-x | mega | インフェルノX | 5,400 | 2025-09-26 | 4521329431529, 4521329431512 (オク) |
| mega-mega-brave | mega | メガブレイブ | 5,400 | 2025-08-01 | 4521329431161 |
| mega-mega-symphonia | mega | メガシンフォニア | 5,400 | 2025-08-01 | 4521329431185 |
| sv-black-bolt | sv | ブラックボルト | 5,800 | 2025-06-06 | 4521329427768 |
| sv-white-flare | sv | ホワイトフレア | 5,800 | 2025-06-06 | 4521329427782 |
| sv-rocket-gang | sv | ロケット団の栄光 | 5,400 | 2025-04-18 | 4521329374659 |
| sv-heat-arena | sv | 熱風のアリーナ | 5,400 | 2025-03-14 | 4521329374758 |
| sv-battle-partners | sv | バトルパートナーズ | 5,400 | 2025-01-24 | 4521329362649 |
| sv-terastal-fes-ex | sv | テラスタルフェスex | 5,500 | 2024-12-06 | 4521329362342 |
| sv-super-electric-breaker | sv | 超電ブレイカー | 5,400 | 2024-10-18 | 4521329361505 |
| sv-paradise-dragona | sv | 楽園ドラゴーナ | 5,400 | 2024-09-13 | 4521329361352 |
| sv-stellar-miracle | sv | ステラミラクル | 5,400 | 2024-07-19 | 4521329361000 |
| sv-night-wanderer | sv | ナイトワンダラー | 5,400 | 2024-06-07 | 4521329362496 |
| sv-151 | sv | 151 | 5,400 | 2023-06-16 | 4521329346038 |

Chi tiết cần lưu ý:
- ブラックボルト và ホワイトフレア có bản DX với JAN khác (4521329427300, 4521329427324). Chúng không thuộc danh sách, nên alias phải loại "デラックス" và "DX".
- Alias "151" ngắn, phải đi kèm "強化拡張パック" hoặc "SV2a", để không khớp nhầm số khác.

## 4. Ghép sản phẩm của tiệm với BOX: `crawler/pokemon/match.py`

`match_item(name: str, jan: str | None, items: list[dict]) -> str | None`:

1. **Chuẩn hoá tên:** NFKC, bỏ khoảng trắng, chữ thường.
2. **Loại hàng không phải BOX còn màng co:** trả `None` nếu tên chứa シュリンクなし / シュリンク無し, カートン, パック単品 / バラパック, 開封済 / 開封品 (nhưng 未開封 vẫn hợp lệ), プロモなし / プロモカードなし, デッキ, セット, デラックス / DX.
3. **Có JAN và khớp `jan` của đúng một BOX:** trả `id` đó.
4. **Không có JAN:** tìm các BOX mà tên chứa một alias và không chứa chuỗi nào trong `exclude`.
   - Đúng 1 BOX: trả `id`.
   - 0 hoặc từ 2 BOX trở lên: trả `None`; trường hợp từ 2 trở lên thì ghi cảnh báo vào log.
5. **Có JAN nhưng JAN không có trong catalog:** trả `None`, không thử theo tên, để tránh nhận nhầm bản DX hoặc set.

Parser của từng tiệm tách ra (tên, JAN nếu có, giá), gọi `match_item`, rồi bỏ trùng như `dedupe` hiện có.

## 5. Tiệm (8)

Đã khảo sát trang thật ngày 2026-10-03.

| id | Tên | Nguồn crawl | Ghép bằng | Số trang tối đa | Giờ (cửa hàng chính) |
|---|---|---|---|---|---|
| `morimori` | 森森 | HTML `/category/2401010` (MEGA) và `/category/2401001` (SV), `.product-item` có `JAN:` | JAN | 3 trang mỗi danh mục | 11:00–20:00 hằng ngày (秋葉原本店) |
| `homura` | ホムラ | HTML `/products?q[product_sub_category_id_eq]=128&q[product_sub_category_product_category_id_eq]=14` (シュリンク有り), JAN là 13 chữ số cuối của dãy số trong thẻ (ví dụ `114521329462424`) | JAN | 3 | 13:00–22:00 hằng ngày (秋葉原店) |
| `rudeya` | ルデヤ | HTML `/category/detail/114`, `article.pgrid-card` nhãn 新品 | JAN | 1 | 10:00–19:00 thứ 2–7, nghỉ Chủ nhật |
| `ichiban` | モバイル一番 | HTML `/Prod/3/`, thẻ `div.card` có `JAN:` và ghi chú `シュリンク付き` | JAN | 1 | 10:00–19:00, nghỉ Chủ nhật (池袋駅前店) |
| `oku` | オク | HTML `/category.html?cat1=340&cat2=363&cat3=367` (シュリンクあり), `div.proItem` | JAN | 3 (hàng mới ở trang đầu) | 11:00–19:00 hằng ngày (神田須田町) |
| `runto` | ラントゥ | WooCommerce Store API: `/wp-json/wc/store/v1/products?category=108&per_page=100`, rồi giá biến thể `シュリンク=ari` qua `/wp-json/wc/store/v1/products?type=variation&include=…` | tên | 2 request | 11:00–19:00 hằng ngày (神田店) |
| `ichome` | 一丁目 | API `/api/goods/listPage?…&cateCode=IIzyMdayU5wp7T4G&size=100`, mức giá `kbDetailName` = `シュリンク有` | JAN | 1 | 10:00–19:00, nghỉ Chủ nhật (秋葉原本店) |
| `shinsoku` | シンソク | API `/api/items?postal_only=true&type=BOX&brand=ポケモン&limit=100&page=N`, giá `postal_purchase_price_s` | tên | 5 (dừng khi `has_more` = false) | 12:30–21:00 hằng ngày (秋葉原本店); `mail_only: true` vì giá là giá mua qua bưu điện |

- **Phân trang:** mỗi tiệm có số trang tối đa riêng (bảng trên). Hết số trang thì dừng, không báo lỗi. Các tiệm đều xếp hàng mới trước, nên các BOX trong catalog nằm ở mấy trang đầu.
- **Thiếu BOX trong catalog:** BOX của catalog không thấy ở tiệm nào thì ô đó hiện "—".
- **Không lấy được giá nào:** tiệm không có giá cho BOX nào bị coi là lỗi, đúng quy tắc hiện có.
- **JAN phụ:** オク ghi JAN của インフェルノX là `4521329431512`, khác JAN `4521329431529` ở 森森 và ホムラ. Catalog ghi cả hai JAN cho BOX này.
- **Giá không phải số** ("問い合わせ"): bỏ qua dòng đó.

## 6. Giao diện `/pokemon-card/`

**Bảng**
- Dòng = BOX, chia nhóm theo `series` (MEGA, SV). Dòng tiêu đề nhóm dính trái.
- 3 cột cố định:
  - **BOX:** ảnh nhỏ 40×40 (điện thoại 32×32) cạnh tên, tên được xuống dòng trên điện thoại.
    - Ảnh hiển thị thẳng từ pokemon-card.com, không chép vào repo, với `loading="lazy"` và `alt` là tên BOX.
    - Ảnh lỗi thì ẩn, chỉ còn tên. Mình đã kiểm tra: trang này không chặn nhúng ảnh từ trang khác.
  - **Retail:** 定価.
  - **Diff:** giá cao nhất − 定価, xanh nếu dương, đỏ nếu âm.
- **Cột tiệm:** dùng cùng phần tiêu đề với iPhone (tên + link, giờ cập nhật, 🟢/🔴 kèm giờ mở cửa hôm nay, 📦 Mail only).
  - Ô cao nhất tô xanh.
  - Tiệm lỗi hoặc dữ liệu cũ bị làm mờ.
  - "—" là tiệm không mua.
  - Tiệm `mail_only` không tính vào Diff và ô cao nhất.
- Dòng tiêu đề bảng dính trên cùng khi cuộn.

**Bộ lọc** (lưu ở URL `?series=…&sort=…` và localStorage `pokemon-filters`)
- Dòng: `All | MEGA | SV`
- Sắp xếp: `Newest` (theo `release`) | `Top Diff` (Diff giảm dần; BOX chưa có giá xếp cuối). Với `Top Diff` thì bỏ chia nhóm, hiện một danh sách liền.

**Cửa sổ xếp hạng:** khi bấm một ô giá, hiện:
- tên BOX và Retail
- "<tiệm> trả ¥…"
- lãi so với 定価 và hạng
- danh sách tiệm, tiệm mail only đứng cuối và không có hạng

Đây là cùng cửa sổ với trang iPhone.

**Bản quyền ảnh:** cuối trang ghi "Ảnh sản phẩm © Pokémon / Nintendo / Creatures / GAME FREAK, nguồn: pokemon-card.com. Trang này không liên kết với các công ty trên." Ảnh vẫn thuộc bản quyền của The Pokémon Company; dùng không xin phép trên trang có quảng cáo có rủi ro bị yêu cầu gỡ, và người dùng đã chọn chấp nhận rủi ro này.

**Trang chủ:** thẻ Pokémon Card bỏ "Sắp có", thay bằng "💰 <tên BOX> lãi tới +¥… so với giá gốc" (BOX có Diff cao nhất). Không có dữ liệu thì để trống dòng này.

**Code web**
- `js/table.js` (mới): chứa `shopHeader` và cửa sổ xếp hạng, chuyển ra từ `app.js` và dùng chung cho cả hai trang. Trang iPhone giữ nguyên giao diện.
- `js/pokemon.js` (mới): code của trang Pokémon.
- `js/logic.js`: thêm các hàm thuần `filterItems`, `sortItems`, `itemDiff`.

## 7. Kiểm thử

**pytest**
- `match_item`:
  - khớp theo JAN
  - khớp theo tên
  - JAN lạ thì trả `None`
  - loại シュリンクなし / カートン / DX / プロモなし / セット
  - "30th CELEBRATION" và "…FUTURISTIC BOX" ra đúng 2 BOX khác nhau
  - tên khớp 2 BOX thì trả `None`
- Mỗi parser của 8 tiệm có một fixture cắt từ trang thật.
- `run.main(category="pokemon")` ghi vào `web/data/pokemon/`, không đụng dữ liệu iPhone.
- `run.main()` mặc định vẫn là iPhone.
- `test_catalog`: mọi tiệm trong catalog Pokémon có parser; mọi BOX có `series` hợp lệ, `retail` > 0, JAN 13 chữ số và không trùng, `release` dạng YYYY-MM-DD, `image` bắt đầu bằng `https://www.pokemon-card.com/`.

**node --test:** `filterItems`, `sortItems` (Newest theo `release`, cùng ngày giữ thứ tự catalog; Top Diff, BOX chưa có giá xếp cuối), `itemDiff` (bỏ mail only, dữ liệu cũ).

**Trình duyệt:**
- bảng, bộ lọc, URL, cửa sổ xếp hạng
- giao diện điện thoại
- trang iPhone không đổi
- thẻ Pokémon trên trang chủ
