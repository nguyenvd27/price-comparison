# Kaitori Price Checker: Kế hoạch triển khai

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Web tĩnh tiếng Việt so sánh giá thu mua iPhone 18 Pro Max (新品未開封) của 6 kaitori. Dữ liệu được crawl tự động khoảng 15 phút/lần, có lịch sử giá, biểu đồ theo ngày và thống kê theo thứ.

**Architecture:** Crawler Python (requests + BeautifulSoup), mỗi cửa hàng một parser thuần (`parse(raw, colors) -> list[Offer]`). Crawler chạy bằng GitHub Actions cron và ghi JSON vào `web/data/` rồi commit. Frontend HTML/CSS/JS thuần (không cần build) host trên Cloudflare Pages, đọc JSON từ `raw.githubusercontent.com` và vẽ bằng Chart.js. Toàn bộ logic tính toán ở frontend nằm trong `web/js/logic.js` (hàm thuần, test bằng `node --test`).

**Tech Stack:** Python 3.12 (local 3.14 chạy được), requests, beautifulsoup4, pytest; JavaScript ES modules, Node `node:test`, Chart.js 4.4.1 (cdnjs); GitHub Actions; Cloudflare Pages.

**Spec:** `docs/superpowers/specs/2026-10-02-kaitori-price-checker-design.md`

## Global Constraints

- Mọi chữ hiển thị cho người dùng là tiếng Việt; tên cửa hàng giữ nguyên tiếng Nhật.
- Chỉ iPhone 18 Pro Max, 4 dung lượng `256GB`, `512GB`, `1TB`, `2TB` × 4 màu `burgundy`, `glacier`, `black`, `silver`. Mã biến thể dạng `pm-<256|512|1tb|2tb>-<màu>`.
- Chỉ lấy giá **mới, chưa kích hoạt (未開封)**. Bỏ qua mọi giá 開封 / 中古.
- Mọi mốc thời gian dùng giờ Nhật `Asia/Tokyo`, định dạng ISO 8601 có offset `+09:00`. "Một ngày" tính từ 00:00 đến 24:00 JST.
- Giá hợp lệ: từ 100,000 đến 1,000,000 yên. Parser trả về 0 offer hoặc giá ngoài khoảng này đều bị coi là lỗi, và giá cũ được giữ nguyên.
- Gửi ít request nhất có thể: 1 request cho mỗi cửa hàng, riêng MIX cần 2 (lấy cookie) và 森森 cần 1 request cho mỗi trang (10 sản phẩm/trang, hiện có 2 trang, tối đa 5). User-Agent có chuỗi `iphone-checker-web/1.0`.
- `display_at` chỉ đổi khi giá của cửa hàng đổi hoặc ở lần crawl thành công đầu tiên trong ngày JST. `last_success_at` thêm điều kiện đã quá 60 phút. Nếu không có gì đổi thì không ghi lại `latest.json`.
- Dữ liệu cũ: `last_success_at` cũ hơn 2 giờ thì hiện "⚠ dữ liệu cũ".
- Frontend không có bước build. Thư viện ngoài chỉ có Chart.js từ `https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js`.
- Thống kê theo thứ chỉ hiện khi có ít nhất 14 ngày dữ liệu trong 28 ngày gần nhất.

## Review Focus

1. **Cửa hàng ghi "chỉ thu mua màu X" (MIX: `バーガンディのみ 他色買取不可`).** Các màu khác phải hiện "—", không được hiện giá gốc. Test: `test_deductions_only_one_color_buyable` (Task 2) và `test_mix_only_burgundy_row` (Task 4).
2. **Trang trả về nội dung rỗng hoặc rác** (MIX khi thiếu cookie trả về 9KB và chuyển sang `/cookie-error`; trang đổi giao diện). Phải thành lỗi và giữ nguyên giá cũ, không được xóa trắng cột. Test: `test_mix_cookie_error_page_returns_nothing` (Task 4), `test_empty_prices_is_error_and_keeps_old` (Task 6), `test_run_records_error_for_failing_shop` (Task 7).
3. **Lần crawl qua mốc nửa đêm JST** (runner của GitHub dùng UTC). Lần đầu sau 00:00 JST phải cập nhật `display_at` dù giá không đổi. Test: `test_first_success_of_new_jst_day_updates_display_at` (Task 6).
4. **Trạng thái mở cửa ở ranh giới**: đúng giờ đóng cửa, ngày nghỉ đột xuất trong `closed_dates`, Chủ nhật nghỉ. Test: `openStatus` (Task 9).
5. **Có ngày thiếu dữ liệu** (crawler chết cả ngày). Biểu đồ vẫn nối liền (`spanGaps`) và thống kê theo thứ bỏ qua ngày thiếu. Test: `chartSeries fills missing days with null` và `weekdayStats ignores missing days` (Task 10).

---

## Cấu trúc file

```
requirements.txt            requests, beautifulsoup4, pytest
pyproject.toml              cấu hình pytest
package.json                {"type":"module"} + script test cho node
crawler/
  __init__.py
  models.py                 Offer, ShopResult
  normalize.py              nfkc, is_pro_max, parse_capacity, find_colors, parse_color, parse_price, variant_id, parse_deductions
  http.py                   new_session, get_text
  update.py                 apply_results, update_daily (logic thuần, không I/O)
  store.py                  DATA_DIR, load_json, save_json, append_history
  run.py                    main(): fetch → parse → update → ghi file
  shops/
    __init__.py             SHOPS registry
    common.py               offer_from_name, offers_from_base, dedupe
    morimori.py shouten.py ichiban.py mobaste.py mix.py ichome.py
  tests/
    conftest.py             fixture colors
    fixtures/*.html|json    HTML/JSON mẫu viết tay, mô phỏng đúng markup thật
    test_*.py
web/
  index.html  style.css
  js/config.js              DATA_BASE
  js/logic.js               hàm thuần (format, lọc, giờ, mở cửa, series, thống kê)
  js/app.js                 state, bộ lọc, bảng giá
  js/charts.js              vẽ biểu đồ Chart.js
  data/catalog.json latest.json daily.json history/
tests/web/logic.test.js
.github/workflows/crawl.yml ci.yml
```

---

### Task 1: Khởi tạo dự án Python + chuẩn hóa tên sản phẩm

**Files:**
- Create: `requirements.txt`, `pyproject.toml`, `crawler/__init__.py`, `crawler/models.py`, `crawler/normalize.py`, `crawler/tests/__init__.py`, `crawler/tests/conftest.py`
- Test: `crawler/tests/test_normalize.py`

**Interfaces:**
- Produces:
  - `crawler.models.Offer(variant: str, price: int)` (frozen dataclass)
  - `crawler.models.ShopResult(prices: dict[str, int], error: str | None)` (NamedTuple)
  - `crawler.normalize`: `nfkc(text) -> str`, `is_pro_max(name) -> bool`, `parse_capacity(name) -> str | None` (trả về `"256"|"512"|"1tb"|"2tb"`), `find_colors(text, colors) -> list[tuple[int, str]]`, `parse_color(name, colors) -> str | None`, `parse_price(text) -> int | None`, `variant_id(capacity, color) -> str`
  - `colors` có kiểu `dict[str, list[str]]` (mã màu → các alias tiếng Nhật). Đây là kiểu dùng chung ở mọi task crawler.

- [ ] **Step 1: Tạo file cấu hình và venv**

`requirements.txt`:
```
requests==2.32.3
beautifulsoup4==4.12.3
pytest==8.3.3
```

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["crawler/tests"]
```

`crawler/__init__.py` và `crawler/tests/__init__.py`: file rỗng.

Run:
```bash
python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
```
Expected: cài đặt xong, không lỗi.

- [ ] **Step 2: Tạo `crawler/models.py` và fixture `colors`**

`crawler/models.py`:
```python
from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class Offer:
    variant: str
    price: int


class ShopResult(NamedTuple):
    prices: dict[str, int]
    error: str | None
```

`crawler/tests/conftest.py`:
```python
import pytest

COLORS = {
    "burgundy": ["バーガンディ"],
    "glacier": ["グレイシャー", "グレイシャ"],
    "black": ["ブラック"],
    "silver": ["シルバー"],
}


@pytest.fixture
def colors():
    return COLORS
```

- [ ] **Step 3: Viết test thất bại**

`crawler/tests/test_normalize.py`:
```python
import pytest

from crawler.normalize import is_pro_max, parse_capacity, parse_color, parse_price, variant_id


@pytest.mark.parametrize("name, expected", [
    ("Apple iPhone18 ProMax 256GB バーガンディ SIMフリー", True),
    ("iPhone 18 Pro Max 1TB", True),
    ("ｉＰｈｏｎｅ１８ Ｐｒｏ Ｍａｘ", True),
    ("iPhone 18 Pro 256GB", False),
    ("iPhone 17 Pro Max 256GB", False),
])
def test_is_pro_max(name, expected):
    assert is_pro_max(name) is expected


@pytest.mark.parametrize("name, expected", [
    ("iPhone 18 Pro Max 256GB バーガンディ MJX74J/A", "256"),
    ("iPhone 18 Pro Max 512ＧＢ", "512"),
    ("iPhone 18 Pro Max 1TB", "1tb"),
    ("iPhone 18 Pro Max 2 TB", "2tb"),
    ("iPhone 18 Pro Max 128GB", None),
    ("iPhone 18 Pro Max", None),
])
def test_parse_capacity(name, expected):
    assert parse_capacity(name) == expected


@pytest.mark.parametrize("name, expected", [
    ("Apple iPhone18 ProMax 256GB バーガンディ SIMフリー", "burgundy"),
    ("グレイシャ-", "glacier"),
    ("グレイシャー", "glacier"),
    (" ブラック", "black"),
    ("ゴールド", None),
])
def test_parse_color(name, expected, colors):
    assert parse_color(name, colors) == expected


@pytest.mark.parametrize("text, expected", [
    ("¥262,000", 262000),
    ("\n  263,000円\n", 263000),
    ("２６２，０００円", 262000),
    ("   ", None),
])
def test_parse_price(text, expected):
    assert parse_price(text) == expected


def test_variant_id():
    assert variant_id("256", "black") == "pm-256-black"
```

- [ ] **Step 4: Chạy test, xác nhận thất bại**

Run: `.venv/bin/python -m pytest crawler/tests/test_normalize.py -q`
Expected: FAIL với `ModuleNotFoundError: No module named 'crawler.normalize'`

- [ ] **Step 5: Viết `crawler/normalize.py`**

```python
import re
import unicodedata

CAPACITIES = {"256GB": "256", "512GB": "512", "1TB": "1tb", "2TB": "2tb"}


def nfkc(text: str | None) -> str:
    return unicodedata.normalize("NFKC", text or "")


def is_pro_max(name: str) -> bool:
    compact = re.sub(r"\s+", "", nfkc(name)).lower()
    return "iphone18promax" in compact


def parse_capacity(name: str) -> str | None:
    match = re.search(r"(\d+)\s*(GB|TB)", nfkc(name), re.IGNORECASE)
    if not match:
        return None
    return CAPACITIES.get(f"{match.group(1)}{match.group(2).upper()}")


def find_colors(text: str, colors: dict[str, list[str]]) -> list[tuple[int, str]]:
    """Mọi vị trí xuất hiện tên màu trong text, sắp theo vị trí."""
    normalized = nfkc(text)
    found = set()
    for color, aliases in colors.items():
        for alias in aliases:
            for match in re.finditer(re.escape(nfkc(alias)), normalized):
                found.add((match.start(), color))
    return sorted(found)


def parse_color(name: str, colors: dict[str, list[str]]) -> str | None:
    found = find_colors(name, colors)
    return found[0][1] if found else None


def parse_price(text: str | None) -> int | None:
    digits = re.sub(r"\D", "", nfkc(text))
    return int(digits) if digits else None


def variant_id(capacity: str, color: str) -> str:
    return f"pm-{capacity}-{color}"
```

- [ ] **Step 6: Chạy test, xác nhận pass**

Run: `.venv/bin/python -m pytest crawler/tests/test_normalize.py -q`
Expected: PASS (21 passed)

- [ ] **Step 7: Commit**

```bash
git add requirements.txt pyproject.toml crawler/
git commit -m "feat(crawler): chuẩn hóa tên model, dung lượng, màu, giá"
```

---

### Task 2: Đọc ghi chú trừ tiền theo màu

Ba cửa hàng (海峡, モバステ, MIX) chỉ niêm yết một giá gốc cho mỗi dung lượng, kèm ghi chú tự do về số tiền bị trừ theo màu. Màu không được nhắc tới trong ghi chú thì lấy giá gốc.

**Files:**
- Modify: `crawler/normalize.py` (thêm `parse_deductions`)
- Test: `crawler/tests/test_deductions.py`

**Interfaces:**
- Consumes: `nfkc`, `find_colors` (Task 1)
- Produces: `parse_deductions(text: str, colors) -> dict[str, int | None]`. Giá trị `0` là giá gốc, số âm là tiền bị trừ, `None` là không thu mua màu đó.

- [ ] **Step 1: Viết test thất bại**

`crawler/tests/test_deductions.py`:
```python
from crawler.normalize import parse_deductions


def test_each_color_own_amount(colors):
    text = "シルバー -32000/\nグレイシャー -27000/\nブラック -26000"
    assert parse_deductions(text, colors) == {
        "burgundy": 0, "glacier": -27000, "black": -26000, "silver": -32000,
    }


def test_group_shares_amount(colors):
    assert parse_deductions("シルバー/グレイシャー/ブラック -22000", colors) == {
        "burgundy": 0, "glacier": -22000, "black": -22000, "silver": -22000,
    }


def test_two_groups(colors):
    assert parse_deductions("シルバー/グレイシャー -18000 ブラック-11000", colors) == {
        "burgundy": 0, "glacier": -18000, "black": -11000, "silver": -18000,
    }


def test_japanese_commas_and_suffix(colors):
    text = "グレイシャー 、ブラック、シルバー -34,000(開封済・未開封)"
    assert parse_deductions(text, colors) == {
        "burgundy": 0, "glacier": -34000, "black": -34000, "silver": -34000,
    }


def test_yen_suffix_halfwidth_comma(colors):
    text = "ブラック-27,000円､グレイシャー-28,000円､シルバー-32,000円"
    assert parse_deductions(text, colors) == {
        "burgundy": 0, "glacier": -28000, "black": -27000, "silver": -32000,
    }


def test_unicode_minus(colors):
    assert parse_deductions("ブラック −11000", colors)["black"] == -11000


def test_deductions_only_one_color_buyable(colors):
    assert parse_deductions("バーガンディのみ 他色買取不可", colors) == {
        "burgundy": 0, "glacier": None, "black": None, "silver": None,
    }


def test_empty_text_means_all_base_price(colors):
    assert parse_deductions("", colors) == {
        "burgundy": 0, "glacier": 0, "black": 0, "silver": 0,
    }
```

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `.venv/bin/python -m pytest crawler/tests/test_deductions.py -q`
Expected: FAIL với `ImportError: cannot import name 'parse_deductions'`

- [ ] **Step 3: Thêm vào cuối `crawler/normalize.py`**

```python
AMOUNT = re.compile(r"[-−‐]\s*(\d[\d,]*)")


def parse_deductions(text: str, colors: dict[str, list[str]]) -> dict[str, int | None]:
    """Đọc ghi chú kiểu "シルバー/グレイシャー -18000 ブラック-11000".

    Mỗi số tiền áp cho các màu đứng ngay trước nó (chưa được gán).
    "Xのみ ... 不可" nghĩa là chỉ thu mua màu X, các màu khác là None.
    """
    normalized = nfkc(text)
    if "のみ" in normalized and "不可" in normalized:
        allowed = {color for _, color in find_colors(normalized.split("のみ")[0], colors)}
        return {color: (0 if color in allowed else None) for color in colors}

    result: dict[str, int | None] = {color: 0 for color in colors}
    tokens = [(pos, "color", color) for pos, color in find_colors(normalized, colors)]
    tokens += [(m.start(), "amount", int(m.group(1).replace(",", ""))) for m in AMOUNT.finditer(normalized)]
    pending: list[str] = []
    for _, kind, value in sorted(tokens, key=lambda token: token[0]):
        if kind == "color":
            pending.append(value)
        else:
            for color in pending:
                result[color] = -value
            pending = []
    return result
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `.venv/bin/python -m pytest crawler/tests -q`
Expected: PASS (29 passed)

- [ ] **Step 5: Commit**

```bash
git add crawler/normalize.py crawler/tests/test_deductions.py
git commit -m "feat(crawler): đọc ghi chú trừ tiền theo màu"
```

---

### Task 3: HTTP + parser 森森 và 買取商店 (mỗi màu một dòng)

**Files:**
- Create: `crawler/http.py`, `crawler/shops/__init__.py` (rỗng ở task này), `crawler/shops/common.py`, `crawler/shops/morimori.py`, `crawler/shops/shouten.py`
- Create: `crawler/tests/fixtures/morimori.html`, `crawler/tests/fixtures/shouten.html`
- Test: `crawler/tests/test_shops_table.py`

**Interfaces:**
- Consumes: `Offer` (Task 1), các hàm trong `crawler.normalize` (Task 1, 2)
- Produces:
  - `crawler.http.new_session() -> requests.Session`, `crawler.http.get_text(session, url) -> str`
  - `crawler.shops.common.offer_from_name(name, price, colors) -> Offer | None`, `offers_from_base(name, base_price, remark, colors) -> list[Offer]`, `dedupe(offers) -> list[Offer]`
  - Mỗi module cửa hàng có: `URL: str`, `fetch(session) -> str`, `parse(raw: str, colors) -> list[Offer]`

- [ ] **Step 1: Tạo fixture (mô phỏng markup thật ngày 2026-10-02)**

`crawler/tests/fixtures/morimori.html`:
```html
<div class="product-list-container" id="category-0301070-products">
  <div class="product-item">
    <div class="product-details"><a href="/category/0301070/product/344310">
      <h5 class="product-details-name">
        Apple
        iPhone18 ProMax 256GB
        バーガンディ SIMフリー
      </h5><h5>JAN:4549995734645</h5></a></div>
    <div class="product-price"><div class="price-normal-number"><h5>
      263,000円
    </h5></div></div>
    <div class="deposit-price"><div class="deposit-price-number"><h5>266,890円</h5></div></div>
  </div>
  <div class="product-item">
    <div class="product-details"><a href="#"><h5 class="product-details-name">Apple iPhone18 ProMax 256GB シルバー SIMフリー</h5></a></div>
    <div class="product-price"><div class="price-normal-number"><h5>231,000円</h5></div></div>
  </div>
  <div class="product-item">
    <div class="product-details"><a href="#"><h5 class="product-details-name">Apple iPhone18 Pro 256GB ブラック SIMフリー</h5></a></div>
    <div class="product-price"><div class="price-normal-number"><h5>217,000円</h5></div></div>
  </div>
</div>
```

`crawler/tests/fixtures/shouten.html`:
```html
<table><tbody>
<tr><td><img src="x.png" alt="x"><a href="/products/detail/27097">iPhone 18 Pro Max 256GB バーガンディ MJX74J/A SIMフリー</a><span class="strong-dot">強化</span></td><td class="num">¥262,000</td><td class="num">¥202,000</td></tr>
<tr><td><a href="/products/detail/27099">iPhone 18 Pro Max 256GB シルバー MJX64J/A SIMフリー</a></td><td class="num">¥230,000</td><td class="num">¥202,000</td></tr>
<tr><td><a href="/products/detail/27109">iPhone 18 Pro Max 2TB バーガンディ MJXL4J/A SIMフリー</a></td><td class="num">¥435,000</td><td class="num">¥345,000</td></tr>
<tr><td><a href="/products/detail/27097">iPhone 18 Pro Max 256GB バーガンディ MJX74J/A SIMフリー</a></td><td class="num">¥199,000</td></tr>
</tbody></table>
```

- [ ] **Step 2: Viết test thất bại**

`crawler/tests/test_shops_table.py`:
```python
from pathlib import Path
from types import SimpleNamespace

from crawler.models import Offer
from crawler.shops import morimori, shouten

FIXTURES = Path(__file__).parent / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_morimori_parses_pro_max_only(colors):
    assert morimori.parse(read("morimori.html"), colors) == [
        Offer("pm-256-burgundy", 263000),
        Offer("pm-256-silver", 231000),
    ]


def test_shouten_uses_first_price_and_dedupes(colors):
    assert shouten.parse(read("shouten.html"), colors) == [
        Offer("pm-256-burgundy", 262000),
        Offer("pm-256-silver", 230000),
        Offer("pm-2tb-burgundy", 435000),
    ]


def test_parsers_return_empty_on_unrelated_html(colors):
    assert morimori.parse("<html></html>", colors) == []
    assert shouten.parse("<html></html>", colors) == []


def test_morimori_fetch_follows_pagination():
    page1 = (
        '<div id="category-0301070-products"></div>'
        '<ul class="pagination"><li class="next"><p>'
        '<a href="https://www.morimori-kaitori.jp/category/0301070?page=2"><span>次のページ</span></a>'
        "</p></li></ul>"
    )
    pages = {morimori.URL: page1, morimori.URL + "?page=2": "<p>trang 2</p>"}
    calls = []

    class FakeSession:
        def get(self, url, timeout):
            calls.append(url)
            return SimpleNamespace(encoding="utf-8", text=pages[url], raise_for_status=lambda: None)

    assert morimori.fetch(FakeSession()) == page1 + "\n<p>trang 2</p>"
    assert calls == [morimori.URL, morimori.URL + "?page=2"]
```

- [ ] **Step 3: Chạy test, xác nhận thất bại**

Run: `.venv/bin/python -m pytest crawler/tests/test_shops_table.py -q`
Expected: FAIL với `ModuleNotFoundError: No module named 'crawler.shops'`

- [ ] **Step 4: Viết `crawler/http.py`**

```python
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0 Safari/537.36 iphone-checker-web/1.0"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.8",
}
TIMEOUT = 30


def new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def get_text(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding
    return response.text
```

- [ ] **Step 5: Viết `crawler/shops/common.py`**

`crawler/shops/__init__.py`: tạo file rỗng (Task 5 sẽ thêm registry).

```python
from crawler.models import Offer
from crawler.normalize import is_pro_max, parse_capacity, parse_color, parse_deductions, variant_id


def offer_from_name(name: str, price: int | None, colors: dict[str, list[str]]) -> Offer | None:
    """Cửa hàng ghi mỗi màu một dòng, ví dụ "iPhone 18 Pro Max 256GB ブラック"."""
    capacity = parse_capacity(name)
    color = parse_color(name, colors)
    if not (is_pro_max(name) and capacity and color and price):
        return None
    return Offer(variant_id(capacity, color), price)


def offers_from_base(name: str, base_price: int | None, remark: str, colors: dict[str, list[str]]) -> list[Offer]:
    """Cửa hàng ghi một giá gốc cho mỗi dung lượng, kèm ghi chú trừ tiền theo màu."""
    capacity = parse_capacity(name)
    if not (is_pro_max(name) and capacity and base_price):
        return []
    deltas = parse_deductions(remark, colors)
    return [
        Offer(variant_id(capacity, color), base_price + delta)
        for color, delta in deltas.items()
        if delta is not None
    ]


def dedupe(offers: list[Offer]) -> list[Offer]:
    """Giữ offer đầu tiên của mỗi biến thể (bảng chính luôn nằm trước)."""
    seen = set()
    result = []
    for offer in offers:
        if offer.variant not in seen:
            seen.add(offer.variant)
            result.append(offer)
    return result
```

- [ ] **Step 6: Viết `crawler/shops/morimori.py`**

森森 chỉ hiện 10 sản phẩm mỗi trang, nên phải đi theo link "次のページ" (`ul.pagination li.next a`).

```python
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

URL = "https://www.morimori-kaitori.jp/category/0301070"
MAX_PAGES = 5


def fetch(session) -> str:
    pages = []
    url = URL
    while url and len(pages) < MAX_PAGES:
        html = get_text(session, url)
        pages.append(html)
        next_link = BeautifulSoup(html, "html.parser").select_one("ul.pagination li.next a")
        url = urljoin(URL, next_link["href"]) if next_link else None
    return "\n".join(pages)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for item in soup.select("#category-0301070-products .product-item"):
        name = item.select_one(".product-details-name")
        price = item.select_one(".price-normal-number")
        if not name or not price:
            continue
        offer = offer_from_name(name.get_text(" ", strip=True), parse_price(price.get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
```

- [ ] **Step 7: Viết `crawler/shops/shouten.py`**

```python
from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

URL = "https://www.kaitorishouten-co.jp/category/1/747"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for link in soup.select('a[href^="/products/detail/"]'):
        row = link.find_parent("tr")
        price = row.select_one("td.num") if row else None
        if not price:
            continue
        offer = offer_from_name(link.get_text(" ", strip=True), parse_price(price.get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
```

- [ ] **Step 8: Chạy test, xác nhận pass**

Run: `.venv/bin/python -m pytest crawler/tests -q`
Expected: PASS (33 passed)

- [ ] **Step 9: Commit**

```bash
git add crawler/http.py crawler/shops crawler/tests/fixtures crawler/tests/test_shops_table.py
git commit -m "feat(crawler): parser 森森 và 買取商店"
```

---

### Task 4: Parser 海峡, モバステ và MIX (giá gốc + trừ tiền theo màu)

**Files:**
- Create: `crawler/shops/ichiban.py`, `crawler/shops/mobaste.py`, `crawler/shops/mix.py`
- Create: `crawler/tests/fixtures/ichiban.html`, `crawler/tests/fixtures/mobaste.html`, `crawler/tests/fixtures/mix.html`
- Test: `crawler/tests/test_shops_base.py`

**Interfaces:**
- Consumes: `get_text`, `offers_from_base`, `dedupe` (Task 3), `parse_price` (Task 1)
- Produces: các module `ichiban`, `mobaste`, `mix`, cùng giao diện `URL`, `fetch(session)`, `parse(raw, colors)`

- [ ] **Step 1: Tạo fixture**

`crawler/tests/fixtures/ichiban.html`:
```html
<div class="row bg-white">
  <div class="col-6 col-md-4 col-lg-3 mb-1"><div class="card"><div class="col-12 px-0">
    <div class="card-body text-center py-1 px-0">
      <label class="hideText mb-0 px-2 w-100" title="iPhone 18 Pro Max 256GB">iPhone 18 Pro Max 256GB</label>
      <label class="hideText mb-0 px-2 w-100" title="simfree未開封">simfree未開封 &nbsp;</label>
      <label class="hideText mb-0 px-5 w-100" title="x"><small class="my-prod-remarks">シルバー -32000/
グレイシャー -27000/
ブラック -26000&nbsp;</small></label>
      <label class="mb-0 text-right" id="NewPrice_S013610">262,000円</label>
    </div>
  </div></div></div>
  <div class="col-6 col-md-4 col-lg-3 mb-1"><div class="card"><div class="col-12 px-0">
    <div class="card-body text-center py-1 px-0">
      <label class="hideText mb-0 px-2 w-100" title="iPhone 18 Pro Max 512GB">iPhone 18 Pro Max 512GB</label>
      <label class="hideText mb-0 px-2 w-100" title="simfree未開封">simfree未開封</label>
      <label class="hideText mb-0 px-5 w-100" title="x"><small class="my-prod-remarks">シルバー/グレイシャー/ブラック -22000&nbsp;</small></label>
      <label class="mb-0 text-right" id="NewPrice_S013611">292,000円</label>
    </div>
  </div></div></div>
  <div class="col-6 col-md-4 col-lg-3 mb-1"><div class="card"><div class="col-12 px-0">
    <div class="card-body text-center py-1 px-0">
      <label class="hideText mb-0 px-2 w-100" title="iPhone 18 Pro Max 256GB">iPhone 18 Pro Max 256GB</label>
      <label class="hideText mb-0 px-2 w-100" title="simfree開封">simfree開封</label>
      <label class="hideText mb-0 px-5 w-100" title="x"><small class="my-prod-remarks">&nbsp;</small></label>
      <label class="mb-0 text-right" id="NewPrice_S013620">223,000円</label>
    </div>
  </div></div></div>
</div>
```

`crawler/tests/fixtures/mobaste.html`:
```html
<table class="p-priceTable"><thead><tr><th><h2>iPhone18 Pro Max</h2></th></tr></thead><tbody>
<tr class="js-targetStorage" data-storage-id="9" data-carrier-key="docomo"><td><div class="p-priceTable__inner">
  <div class="p-priceTable__name">
    <span>iPhone18 Pro Max 256GB</span>
    <div class="p-priceTable__caution whitespace-pre-line">グレイシャー 、ブラック、シルバー -34,000(開封済・未開封)</div>
    <div class="p-priceTable__price">
      <div class="p-priceTable__priceItem"><span class="label">未開封品買取価格</span><span class="price price--unopened">264,000円</span></div>
      <div class="p-priceTable__priceItem"><span class="label">中古買取価格</span><span class="price">185,000円〜158,000円</span></div>
    </div>
  </div>
</div></td></tr>
<tr class="js-targetStorage" data-storage-id="12" data-carrier-key="docomo"><td><div class="p-priceTable__inner">
  <div class="p-priceTable__name">
    <span>iPhone18 Pro Max 2TB</span>
    <div class="p-priceTable__price"><div class="p-priceTable__priceItem"><span class="price price--unopened">435,000円</span></div></div>
  </div>
</div></td></tr>
<tr class="js-targetStorage" data-storage-id="5" data-carrier-key="docomo"><td><div class="p-priceTable__inner">
  <div class="p-priceTable__name">
    <span>iPhone18 Pro 256GB</span>
    <div class="p-priceTable__price"><div class="p-priceTable__priceItem"><span class="price price--unopened">218,000円</span></div></div>
  </div>
</div></td></tr>
</tbody></table>
```

`crawler/tests/fixtures/mix.html`:
```html
<table class="list"><tbody>
<tr id="613"><td colspan="2" class="product" name="model">iPhone 18 Pro Max 256GB</td><td class="price" id="model613">263,000円</td></tr>
<tr><td class="open"><span class="noopen">未開封</span></td><td>ブラック-27,000円､グレイシャー-28,000円､シルバー-32,000円</td><td class="cart"><a href="#">買取申込</a></td></tr>
<tr id="614"><td colspan="2" class="product" name="model">iPhone 18 Pro Max 512GB</td><td class="price" id="model614">292,000円</td></tr>
<tr><td class="open"><span class="noopen">未開封</span></td><td>バーガンディのみ 他色買取不可</td><td class="cart"></td></tr>
<tr id="590"><td colspan="2" class="product" name="model">iPhone 17 Pro Max 256GB</td><td class="price" id="model590">180,000円</td></tr>
<tr><td class="open"><span class="noopen">未開封</span></td><td></td><td class="cart"></td></tr>
</tbody></table>
```

- [ ] **Step 2: Viết test thất bại**

`crawler/tests/test_shops_base.py`:
```python
from pathlib import Path

from crawler.models import Offer
from crawler.shops import ichiban, mix, mobaste

FIXTURES = Path(__file__).parent / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def as_dict(offers):
    return {offer.variant: offer.price for offer in offers}


def test_ichiban_applies_deductions_and_skips_opened(colors):
    assert as_dict(ichiban.parse(read("ichiban.html"), colors)) == {
        "pm-256-burgundy": 262000, "pm-256-glacier": 235000,
        "pm-256-black": 236000, "pm-256-silver": 230000,
        "pm-512-burgundy": 292000, "pm-512-glacier": 270000,
        "pm-512-black": 270000, "pm-512-silver": 270000,
    }


def test_mobaste_unopened_price_and_deductions(colors):
    assert as_dict(mobaste.parse(read("mobaste.html"), colors)) == {
        "pm-256-burgundy": 264000, "pm-256-glacier": 230000,
        "pm-256-black": 230000, "pm-256-silver": 230000,
        "pm-2tb-burgundy": 435000, "pm-2tb-glacier": 435000,
        "pm-2tb-black": 435000, "pm-2tb-silver": 435000,
    }


def test_mix_only_burgundy_row(colors):
    assert as_dict(mix.parse(read("mix.html"), colors)) == {
        "pm-256-burgundy": 263000, "pm-256-glacier": 235000,
        "pm-256-black": 236000, "pm-256-silver": 231000,
        "pm-512-burgundy": 292000,
    }


def test_mix_cookie_error_page_returns_nothing(colors):
    assert mix.parse("<html><body>Cookieを有効にしてください</body></html>", colors) == []


def test_mix_fetch_visits_home_first():
    calls = []

    class FakeResponse:
        encoding = "utf-8"
        text = "ok"

        def raise_for_status(self):
            pass

    class FakeSession:
        def get(self, url, timeout):
            calls.append(url)
            return FakeResponse()

    assert mix.fetch(FakeSession()) == "ok"
    assert calls == ["https://mobile-mix.jp/", "https://mobile-mix.jp/?category=7"]


def test_offer_type(colors):
    assert all(isinstance(o, Offer) for o in mix.parse(read("mix.html"), colors))
```

- [ ] **Step 3: Chạy test, xác nhận thất bại**

Run: `.venv/bin/python -m pytest crawler/tests/test_shops_base.py -q`
Expected: FAIL với `ImportError: cannot import name 'ichiban'`

- [ ] **Step 4: Viết `crawler/shops/ichiban.py`**

```python
from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offers_from_base

URL = "https://www.mobile-ichiban.com/Prod/1/01/40"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for price in soup.select('label[id^="NewPrice_"]'):
        card = price.find_parent("div", class_="card")
        if not card:
            continue
        labels = card.select("label.hideText")
        name = labels[0].get("title", "") if labels else ""
        condition = labels[1].get("title", "") if len(labels) > 1 else ""
        if "未開封" not in condition:
            continue
        remark = card.select_one(".my-prod-remarks")
        offers += offers_from_base(
            name,
            parse_price(price.get_text()),
            remark.get_text(" ", strip=True) if remark else "",
            colors,
        )
    return dedupe(offers)
```

- [ ] **Step 5: Viết `crawler/shops/mobaste.py`**

```python
from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offers_from_base

URL = "https://pastec.net/iphone?series_child_id=644"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for row in soup.select("tr.js-targetStorage"):
        name = row.select_one(".p-priceTable__name > span")
        price = row.select_one(".price--unopened")
        if not name or not price:
            continue
        caution = row.select_one(".p-priceTable__caution")
        offers += offers_from_base(
            name.get_text(strip=True),
            parse_price(price.get_text()),
            caution.get_text(" ", strip=True) if caution else "",
            colors,
        )
    return dedupe(offers)
```

- [ ] **Step 6: Viết `crawler/shops/mix.py`**

```python
from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offers_from_base

HOME = "https://mobile-mix.jp/"
URL = "https://mobile-mix.jp/?category=7"


def fetch(session) -> str:
    # Lần đầu chưa có cookie, MIX chuyển hướng sang /cookie-error, nên phải gọi trang chủ trước để nhận cookie.
    get_text(session, HOME)
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for row in soup.select("tr[id]"):
        product = row.select_one('td.product[name="model"]')
        price = row.select_one("td.price")
        detail = row.find_next_sibling("tr")
        cells = detail.find_all("td") if detail else []
        if not product or not price or len(cells) < 2 or "未開封" not in cells[0].get_text():
            continue
        offers += offers_from_base(
            product.get_text(strip=True),
            parse_price(price.get_text()),
            cells[1].get_text(" ", strip=True),
            colors,
        )
    return dedupe(offers)
```

- [ ] **Step 7: Chạy test, xác nhận pass**

Run: `.venv/bin/python -m pytest crawler/tests -q`
Expected: PASS (39 passed)

- [ ] **Step 8: Commit**

```bash
git add crawler/shops crawler/tests
git commit -m "feat(crawler): parser 海峡, モバステ, MIX"
```

---

### Task 5: Parser 一丁目 (API JSON) + registry cửa hàng

API `listPage` trả về giá 未開封 (`kbDetailPrice`) cho mỗi dung lượng. Mỗi màu có `varPrice` riêng trong `keitaiKbDetailColorRels`, khớp theo `keitaiKbDetailId == allGoodsKbDetailId` của dòng 未開封.

**Files:**
- Create: `crawler/shops/ichome.py`, `crawler/tests/fixtures/ichome.json`
- Modify: `crawler/shops/__init__.py`
- Test: `crawler/tests/test_shop_ichome.py`

**Interfaces:**
- Consumes: `get_text` (Task 3), `is_pro_max`, `parse_capacity`, `parse_color`, `variant_id` (Task 1)
- Produces: `crawler.shops.SHOPS: dict[str, module]` với các khóa `morimori`, `ichiban`, `mobaste`, `shouten`, `ichome`, `mix`

- [ ] **Step 1: Tạo fixture `crawler/tests/fixtures/ichome.json`**

```json
{"code": 200, "msg": "success", "data": {"totalElements": 2, "content": [
  {"title": "iPhone 18 Pro Max 256GB", "kbName": "新品",
   "goodsKbDetails": [
     {"allGoodsKbDetailId": 4011, "kbDetailName": "未開封", "kbDetailPrice": 262000},
     {"allGoodsKbDetailId": 4012, "kbDetailName": "開封済未使用品", "kbDetailPrice": 229000}],
   "keitaiColorOptions": [
     {"color": "ブラック", "publicPrice": 239800, "keitaiKbDetailColorRels": [
       {"keitaiKbDetailId": 4012, "varPrice": -20000},
       {"keitaiKbDetailId": 4011, "varPrice": -26000}]},
     {"color": "グレイシャ-", "publicPrice": 239800, "keitaiKbDetailColorRels": [
       {"keitaiKbDetailId": 4011, "varPrice": -27000}]},
     {"color": " バーガンディ", "publicPrice": 239800, "keitaiKbDetailColorRels": [
       {"keitaiKbDetailId": 4011, "varPrice": null}]}]},
  {"title": "iPhone 18 Pro 256GB", "kbName": "新品",
   "goodsKbDetails": [{"allGoodsKbDetailId": 5000, "kbDetailName": "未開封", "kbDetailPrice": 217000}],
   "keitaiColorOptions": [{"color": "ブラック", "keitaiKbDetailColorRels": []}]}
]}}
```

- [ ] **Step 2: Viết test thất bại**

`crawler/tests/test_shop_ichome.py`:
```python
import json
from pathlib import Path

import pytest

from crawler.models import Offer
from crawler.shops import SHOPS, ichome

FIXTURE = Path(__file__).parent / "fixtures" / "ichome.json"


def test_ichome_adds_color_var_price(colors):
    assert ichome.parse(FIXTURE.read_text(encoding="utf-8"), colors) == [
        Offer("pm-256-black", 236000),
        Offer("pm-256-glacier", 235000),
        Offer("pm-256-burgundy", 262000),
    ]


def test_ichome_api_error_raises(colors):
    with pytest.raises(ValueError, match="401"):
        ichome.parse(json.dumps({"code": 401, "msg": "ログインしていません"}), colors)


def test_registry_has_six_shops():
    assert set(SHOPS) == {"morimori", "ichiban", "mobaste", "shouten", "ichome", "mix"}
    assert all(hasattr(m, "fetch") and hasattr(m, "parse") for m in SHOPS.values())
```

- [ ] **Step 3: Chạy test, xác nhận thất bại**

Run: `.venv/bin/python -m pytest crawler/tests/test_shop_ichome.py -q`
Expected: FAIL với `ImportError: cannot import name 'SHOPS'`

- [ ] **Step 4: Viết `crawler/shops/ichome.py`**

```python
import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import is_pro_max, parse_capacity, parse_color, variant_id

URL = (
    "https://www.1-chome.com/api/keitai/listPage?accCode=&page=1&size=50&keyword="
    "&isImpo=false&isCampaign=false&cateCode=eOd8WFZllXmBd3Rt&kbNames=&cateName=&isImpoCate=false"
)


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    data = json.loads(raw)
    if data.get("code") != 200:
        raise ValueError(f"API trả về code {data.get('code')}: {data.get('msg')}")
    offers = []
    for item in data["data"]["content"]:
        title = item.get("title") or ""
        capacity = parse_capacity(title)
        unopened = next(
            (d for d in item.get("goodsKbDetails") or [] if d.get("kbDetailName") == "未開封"),
            None,
        )
        if not (is_pro_max(title) and capacity and unopened):
            continue
        for option in item.get("keitaiColorOptions") or []:
            color = parse_color(option.get("color") or "", colors)
            if not color:
                continue
            var_price = next(
                (
                    rel.get("varPrice")
                    for rel in option.get("keitaiKbDetailColorRels") or []
                    if rel.get("keitaiKbDetailId") == unopened["allGoodsKbDetailId"]
                ),
                None,
            )
            offers.append(Offer(variant_id(capacity, color), unopened["kbDetailPrice"] + (var_price or 0)))
    return offers
```

- [ ] **Step 5: Viết `crawler/shops/__init__.py`**

```python
from crawler.shops import ichiban, ichome, mix, mobaste, morimori, shouten

SHOPS = {
    "morimori": morimori,
    "ichiban": ichiban,
    "mobaste": mobaste,
    "shouten": shouten,
    "ichome": ichome,
    "mix": mix,
}
```

- [ ] **Step 6: Chạy test, xác nhận pass**

Run: `.venv/bin/python -m pytest crawler/tests -q`
Expected: PASS (42 passed)

- [ ] **Step 7: Commit**

```bash
git add crawler/shops crawler/tests
git commit -m "feat(crawler): parser 一丁目 qua API JSON và registry cửa hàng"
```

---

### Task 6: Quy tắc cập nhật giá, lịch sử, giá cao nhất mỗi ngày

**Files:**
- Create: `crawler/update.py`
- Test: `crawler/tests/test_update.py`

**Interfaces:**
- Consumes: `ShopResult` (Task 1)
- Produces:
  - `JST`, `jst_date(value: str | datetime) -> str` (`"YYYY-MM-DD"`)
  - `validate(prices: dict[str, int]) -> str | None`
  - `apply_results(latest: dict, results: dict[str, ShopResult], now: datetime) -> tuple[dict, list[dict]]`: trả về `(latest mới, events)`, mỗi event có dạng `{"t", "shop", "variant", "price"}`
  - `update_daily(daily: dict, latest: dict, now: datetime) -> dict`
  - Dạng của `latest`: `{"generated_at": str|None, "shops": {id: {"last_success_at", "display_at", "error", "prices"}}}`

- [ ] **Step 1: Viết test thất bại**

`crawler/tests/test_update.py`:
```python
from datetime import datetime, timedelta, timezone

from crawler.models import ShopResult
from crawler.update import JST, apply_results, update_daily

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=JST)
ISO_NOW = "2026-10-02T12:00:00+09:00"


def shop_state(prices, last="2026-10-02T11:30:00+09:00", display="2026-10-02T09:00:00+09:00", error=None):
    return {"last_success_at": last, "display_at": display, "error": error, "prices": prices}


def test_first_run_records_everything():
    latest, events = apply_results({"shops": {}}, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert latest["generated_at"] == ISO_NOW
    assert latest["shops"]["a"] == shop_state({"pm-256-black": 236000}, last=ISO_NOW, display=ISO_NOW)
    assert events == [{"t": ISO_NOW, "shop": "a", "variant": "pm-256-black", "price": 236000}]


def test_unchanged_same_day_keeps_times_and_no_events():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000})}}
    latest, events = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert latest["shops"]["a"] == prev["shops"]["a"]
    assert events == []


def test_heartbeat_refreshes_last_success_after_60_minutes():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000}, last="2026-10-02T10:59:00+09:00")}}
    latest, _ = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert latest["shops"]["a"]["last_success_at"] == ISO_NOW
    assert latest["shops"]["a"]["display_at"] == "2026-10-02T09:00:00+09:00"


def test_price_change_updates_display_and_logs_event():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000})}}
    latest, events = apply_results(prev, {"a": ShopResult({"pm-256-black": 237000}, None)}, NOW)
    assert latest["shops"]["a"]["display_at"] == ISO_NOW
    assert events == [{"t": ISO_NOW, "shop": "a", "variant": "pm-256-black", "price": 237000}]


def test_disappeared_variant_logs_none():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000, "pm-256-silver": 231000})}}
    _, events = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert events == [{"t": ISO_NOW, "shop": "a", "variant": "pm-256-silver", "price": None}]


def test_first_success_of_new_jst_day_updates_display_at():
    prev = {"shops": {"a": shop_state(
        {"pm-256-black": 236000},
        last="2026-10-01T23:50:00+09:00",
        display="2026-10-01T09:00:00+09:00",
    )}}
    now_utc = datetime(2026, 10, 1, 15, 5, tzinfo=timezone.utc)  # = 10/02 00:05 JST
    latest, events = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, now_utc)
    assert latest["shops"]["a"]["display_at"] == "2026-10-02T00:05:00+09:00"
    assert events == []


def test_error_keeps_old_prices():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000})}}
    latest, events = apply_results(prev, {"a": ShopResult({}, "HTTPError: 503")}, NOW)
    assert latest["shops"]["a"] == {**prev["shops"]["a"], "error": "HTTPError: 503"}
    assert events == []


def test_empty_prices_is_error_and_keeps_old():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000})}}
    latest, events = apply_results(prev, {"a": ShopResult({}, None)}, NOW)
    assert latest["shops"]["a"]["error"] == "Không lấy được giá nào"
    assert latest["shops"]["a"]["prices"] == {"pm-256-black": 236000}
    assert events == []


def test_absurd_price_is_error():
    latest, _ = apply_results({"shops": {}}, {"a": ShopResult({"pm-256-black": 5000}, None)}, NOW)
    assert latest["shops"]["a"]["error"].startswith("Giá vô lý")
    assert latest["shops"]["a"]["prices"] == {}


def test_recovery_clears_error():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000}, error="HTTPError: 503")}}
    latest, _ = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert latest["shops"]["a"]["error"] is None


def test_daily_keeps_highest_of_the_day():
    daily = {"2026-10-02": {"pm-256-black": {"max": 240000, "shop": "b"}}}
    latest = {"shops": {
        "a": shop_state({"pm-256-black": 236000, "pm-256-silver": 231000}, last=ISO_NOW),
        "b": shop_state({"pm-256-silver": 233000}, last=ISO_NOW),
    }}
    assert update_daily(daily, latest, NOW) == {"2026-10-02": {
        "pm-256-black": {"max": 240000, "shop": "b"},
        "pm-256-silver": {"max": 233000, "shop": "b"},
    }}


def test_daily_ignores_failed_and_stale_shops():
    latest = {"shops": {
        "a": shop_state({"pm-256-black": 300000}, last=ISO_NOW, error="HTTPError: 503"),
        "b": shop_state({"pm-256-black": 299000}, last="2026-10-01T18:00:00+09:00"),
        "c": shop_state({"pm-256-black": 236000}, last=ISO_NOW),
    }}
    assert update_daily({}, latest, NOW) == {"2026-10-02": {"pm-256-black": {"max": 236000, "shop": "c"}}}
```

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `.venv/bin/python -m pytest crawler/tests/test_update.py -q`
Expected: FAIL với `ModuleNotFoundError: No module named 'crawler.update'`

- [ ] **Step 3: Viết `crawler/update.py`**

```python
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from crawler.models import ShopResult

JST = ZoneInfo("Asia/Tokyo")
MIN_PRICE = 100_000
MAX_PRICE = 1_000_000
HEARTBEAT = timedelta(minutes=60)
EMPTY_SHOP = {"last_success_at": None, "display_at": None, "error": None, "prices": {}}


def jst_date(value: str | datetime) -> str:
    moment = datetime.fromisoformat(value) if isinstance(value, str) else value
    return moment.astimezone(JST).date().isoformat()


def validate(prices: dict[str, int]) -> str | None:
    if not prices:
        return "Không lấy được giá nào"
    bad = sorted(v for v, p in prices.items() if not MIN_PRICE <= p <= MAX_PRICE)
    if bad:
        return f"Giá vô lý: {', '.join(bad)}"
    return None


def apply_results(latest: dict, results: dict[str, ShopResult], now: datetime) -> tuple[dict, list[dict]]:
    now_iso = now.astimezone(JST).isoformat(timespec="seconds")
    shops = dict(latest.get("shops", {}))
    events: list[dict] = []
    for shop_id, result in results.items():
        prev = shops.get(shop_id, EMPTY_SHOP)
        error = result.error or validate(result.prices)
        if error:
            shops[shop_id] = {**prev, "error": error}
            continue

        old = prev["prices"]
        new = dict(sorted(result.prices.items()))
        changed = new != old
        last = prev["last_success_at"]
        first_today = last is None or jst_date(last) != jst_date(now)
        heartbeat = last is None or now - datetime.fromisoformat(last) >= HEARTBEAT

        for variant in sorted(set(old) | set(new)):
            if old.get(variant) != new.get(variant):
                events.append({"t": now_iso, "shop": shop_id, "variant": variant, "price": new.get(variant)})

        shops[shop_id] = {
            "last_success_at": now_iso if changed or first_today or heartbeat else last,
            "display_at": now_iso if changed or first_today else prev["display_at"],
            "error": None,
            "prices": new,
        }
    return {"generated_at": now_iso, "shops": shops}, events


def update_daily(daily: dict, latest: dict, now: datetime) -> dict:
    """Giá cao nhất từng thấy trong ngày JST, tính trên các cửa hàng đã crawl thành công hôm nay."""
    day = jst_date(now)
    today = dict(daily.get(day, {}))
    for shop_id, shop in latest["shops"].items():
        if shop["error"] or not shop["last_success_at"] or jst_date(shop["last_success_at"]) != day:
            continue
        for variant, price in shop["prices"].items():
            if variant not in today or price > today[variant]["max"]:
                today[variant] = {"max": price, "shop": shop_id}
    return {**daily, day: dict(sorted(today.items()))}
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `.venv/bin/python -m pytest crawler/tests -q`
Expected: PASS (54 passed)

- [ ] **Step 5: Commit**

```bash
git add crawler/update.py crawler/tests/test_update.py
git commit -m "feat(crawler): quy tắc cập nhật giá, lịch sử và giá cao nhất mỗi ngày"
```

---

### Task 7: Lưu file, điểm chạy crawler, catalog và chạy thử với dữ liệu thật

**Files:**
- Create: `crawler/store.py`, `crawler/run.py`, `web/data/catalog.json`, `web/data/latest.json`, `web/data/daily.json`
- Test: `crawler/tests/test_run.py`

**Interfaces:**
- Consumes: `SHOPS` (Task 5), `apply_results`, `update_daily`, `JST` (Task 6), `new_session` (Task 3), `ShopResult` (Task 1)
- Produces:
  - `crawler.store`: `DATA_DIR: Path`, `load_json(path, default)`, `save_json(path, data)`, `append_history(data_dir, events)`
  - `crawler.run.main(data_dir=DATA_DIR, shops=SHOPS, now=None) -> int` (exit code: 1 nếu mọi cửa hàng đều lỗi)
  - Định dạng `catalog.json` mà frontend dùng ở Task 9–12: `variants[{id, capacity, color, apple_price}]`, `colors{id: {vi, hex, aliases}}`, `shops[{id, name, url, hours{mon..sun: [open, close] | null}, closed_dates[], note}]`

- [ ] **Step 1: Viết test thất bại**

`crawler/tests/test_run.py`:
```python
import json
from datetime import datetime
from types import SimpleNamespace

from crawler.models import Offer
from crawler.run import main
from crawler.update import JST

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=JST)
CATALOG = {"colors": {"black": {"aliases": ["ブラック"]}}, "shops": [{"id": "a"}, {"id": "b"}]}


def ok_shop(price=236000):
    return SimpleNamespace(fetch=lambda session: "raw", parse=lambda raw, colors: [Offer("pm-256-black", price)])


def broken_shop():
    def fetch(session):
        raise RuntimeError("boom")
    return SimpleNamespace(fetch=fetch, parse=lambda raw, colors: [])


def setup(tmp_path):
    (tmp_path / "catalog.json").write_text(json.dumps(CATALOG), encoding="utf-8")
    return tmp_path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_run_records_error_for_failing_shop(tmp_path):
    data_dir = setup(tmp_path)
    assert main(data_dir, {"a": ok_shop(), "b": broken_shop()}, NOW) == 0
    latest = read(data_dir / "latest.json")
    assert latest["shops"]["a"]["prices"] == {"pm-256-black": 236000}
    assert latest["shops"]["b"]["error"] == "RuntimeError: boom"
    assert read(data_dir / "history" / "2026-10.json") == [
        {"t": "2026-10-02T12:00:00+09:00", "shop": "a", "variant": "pm-256-black", "price": 236000},
    ]
    assert read(data_dir / "daily.json") == {"2026-10-02": {"pm-256-black": {"max": 236000, "shop": "a"}}}


def test_run_returns_1_when_all_shops_fail(tmp_path):
    data_dir = setup(tmp_path)
    assert main(data_dir, {"a": broken_shop(), "b": broken_shop()}, NOW) == 1


def test_run_does_not_rewrite_latest_when_nothing_changed(tmp_path):
    data_dir = setup(tmp_path)
    shops = {"a": ok_shop(), "b": ok_shop()}
    main(data_dir, shops, NOW)
    before = (data_dir / "latest.json").read_text(encoding="utf-8")
    main(data_dir, shops, NOW.replace(minute=15))
    assert (data_dir / "latest.json").read_text(encoding="utf-8") == before
    assert len(read(data_dir / "history" / "2026-10.json")) == 2
```

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `.venv/bin/python -m pytest crawler/tests/test_run.py -q`
Expected: FAIL với `ModuleNotFoundError: No module named 'crawler.run'`

- [ ] **Step 3: Viết `crawler/store.py`**

```python
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "web" / "data"


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def append_history(data_dir: Path, events: list[dict]) -> None:
    """Mỗi tháng (theo JST) một file history/YYYY-MM.json."""
    by_month: dict[str, list[dict]] = {}
    for event in events:
        by_month.setdefault(event["t"][:7], []).append(event)
    for month, items in by_month.items():
        path = data_dir / "history" / f"{month}.json"
        save_json(path, load_json(path, []) + items)
```

- [ ] **Step 4: Viết `crawler/run.py`**

```python
import sys
from datetime import datetime
from pathlib import Path

from crawler.http import new_session
from crawler.models import ShopResult
from crawler.shops import SHOPS
from crawler.store import DATA_DIR, append_history, load_json, save_json
from crawler.update import JST, apply_results, update_daily


def crawl_shop(module, session, colors) -> ShopResult:
    try:
        offers = module.parse(module.fetch(session), colors)
        return ShopResult({offer.variant: offer.price for offer in offers}, None)
    except Exception as exc:  # một cửa hàng lỗi không được làm hỏng các cửa hàng khác
        return ShopResult({}, f"{type(exc).__name__}: {exc}")


def main(data_dir: Path = DATA_DIR, shops: dict = SHOPS, now: datetime | None = None) -> int:
    catalog = load_json(data_dir / "catalog.json", None)
    colors = {color_id: color["aliases"] for color_id, color in catalog["colors"].items()}
    session = new_session()

    results = {}
    for shop in catalog["shops"]:
        result = crawl_shop(shops[shop["id"]], session, colors)
        status = f"OK {len(result.prices)} giá" if result.error is None else f"LỖI {result.error}"
        print(f"[{shop['id']}] {status}")
        results[shop["id"]] = result

    now = now or datetime.now(JST)
    old_latest = load_json(data_dir / "latest.json", {"generated_at": None, "shops": {}})
    latest, events = apply_results(old_latest, results, now)
    if latest["shops"] != old_latest["shops"]:
        save_json(data_dir / "latest.json", latest)
    if events:
        append_history(data_dir, events)
    old_daily = load_json(data_dir / "daily.json", {})
    daily = update_daily(old_daily, latest, now)
    if daily != old_daily:
        save_json(data_dir / "daily.json", daily)

    for shop_id in results:
        if latest["shops"][shop_id]["error"]:
            print(f"[{shop_id}] bị bỏ qua: {latest['shops'][shop_id]['error']}")
    all_failed = all(latest["shops"][shop_id]["error"] for shop_id in results)
    return 1 if all_failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Chạy test, xác nhận pass**

Run: `.venv/bin/python -m pytest crawler/tests -q`
Expected: PASS (57 passed)

- [ ] **Step 6: Tạo `web/data/catalog.json`**

Giá Apple lấy từ `publicPrice` trong API của 一丁目 (2026-10-02). Giờ mở cửa lấy từ cửa hàng chính, đã tra ngày 2026-10-02. `closed_dates` của MIX là các ngày lễ còn lại đến tháng 2/2027, vì MIX nghỉ ngày lễ.

```json
{
 "model": "iPhone 18 Pro Max",
 "colors": {
  "burgundy": {"vi": "Burgundy", "hex": "#7a1f3d", "aliases": ["バーガンディ"]},
  "glacier": {"vi": "Glacier", "hex": "#7fa9bd", "aliases": ["グレイシャー", "グレイシャ"]},
  "black": {"vi": "Đen", "hex": "#333333", "aliases": ["ブラック"]},
  "silver": {"vi": "Bạc", "hex": "#a9adb3", "aliases": ["シルバー"]}
 },
 "variants": [
  {"id": "pm-256-burgundy", "capacity": "256GB", "color": "burgundy", "apple_price": 239800},
  {"id": "pm-256-glacier", "capacity": "256GB", "color": "glacier", "apple_price": 239800},
  {"id": "pm-256-black", "capacity": "256GB", "color": "black", "apple_price": 239800},
  {"id": "pm-256-silver", "capacity": "256GB", "color": "silver", "apple_price": 239800},
  {"id": "pm-512-burgundy", "capacity": "512GB", "color": "burgundy", "apple_price": 274800},
  {"id": "pm-512-glacier", "capacity": "512GB", "color": "glacier", "apple_price": 274800},
  {"id": "pm-512-black", "capacity": "512GB", "color": "black", "apple_price": 274800},
  {"id": "pm-512-silver", "capacity": "512GB", "color": "silver", "apple_price": 274800},
  {"id": "pm-1tb-burgundy", "capacity": "1TB", "color": "burgundy", "apple_price": 344800},
  {"id": "pm-1tb-glacier", "capacity": "1TB", "color": "glacier", "apple_price": 344800},
  {"id": "pm-1tb-black", "capacity": "1TB", "color": "black", "apple_price": 344800},
  {"id": "pm-1tb-silver", "capacity": "1TB", "color": "silver", "apple_price": 344800},
  {"id": "pm-2tb-burgundy", "capacity": "2TB", "color": "burgundy", "apple_price": 449800},
  {"id": "pm-2tb-glacier", "capacity": "2TB", "color": "glacier", "apple_price": 449800},
  {"id": "pm-2tb-black", "capacity": "2TB", "color": "black", "apple_price": 449800},
  {"id": "pm-2tb-silver", "capacity": "2TB", "color": "silver", "apple_price": 449800}
 ],
 "shops": [
  {"id": "morimori", "name": "森森", "url": "https://www.morimori-kaitori.jp/category/0301070",
   "hours": {"mon": ["11:00", "20:00"], "tue": ["11:00", "20:00"], "wed": ["11:00", "20:00"], "thu": ["11:00", "20:00"], "fri": ["11:00", "20:00"], "sat": ["11:00", "20:00"], "sun": ["11:00", "20:00"]},
   "closed_dates": [], "note": "Giờ của 秋葉原本店"},
  {"id": "ichiban", "name": "海峡", "url": "https://www.mobile-ichiban.com/Prod/1/01/40",
   "hours": {"mon": ["10:00", "19:00"], "tue": ["10:00", "19:00"], "wed": ["10:00", "19:00"], "thu": ["10:00", "19:00"], "fri": ["10:00", "19:00"], "sat": ["10:00", "19:00"], "sun": null},
   "closed_dates": [], "note": "モバイル一番 · giờ của 池袋駅前店"},
  {"id": "mobaste", "name": "モバステ", "url": "https://pastec.net/iphone?series_child_id=644",
   "hours": {"mon": ["11:00", "19:30"], "tue": ["11:00", "19:30"], "wed": ["11:00", "19:30"], "thu": ["11:00", "19:30"], "fri": ["11:00", "19:30"], "sat": ["11:00", "19:30"], "sun": ["11:00", "19:30"]},
   "closed_dates": [], "note": "Giờ của 秋葉原店 · nhận gửi bưu điện"},
  {"id": "shouten", "name": "買取商店", "url": "https://www.kaitorishouten-co.jp/category/1/747",
   "hours": {"mon": ["10:20", "19:00"], "tue": ["10:20", "19:00"], "wed": ["10:20", "19:00"], "thu": ["10:20", "19:00"], "fri": ["10:20", "19:00"], "sat": ["10:20", "19:00"], "sun": null},
   "closed_dates": [], "note": "Giờ của 秋葉原店"},
  {"id": "ichome", "name": "一丁目", "url": "https://www.1-chome.com/mobile?category=eOd8WFZllXmBd3Rt",
   "hours": {"mon": ["10:00", "19:00"], "tue": ["10:00", "19:00"], "wed": ["10:00", "19:00"], "thu": ["10:00", "19:00"], "fri": ["10:00", "19:00"], "sat": ["10:00", "19:00"], "sun": null},
   "closed_dates": [], "note": "Giờ của 秋葉原本店"},
  {"id": "mix", "name": "MIX", "url": "https://mobile-mix.jp/?category=7",
   "hours": {"mon": ["11:00", "19:00"], "tue": ["11:00", "19:00"], "wed": ["11:00", "19:00"], "thu": ["11:00", "19:00"], "fri": ["11:00", "19:00"], "sat": ["11:00", "19:00"], "sun": null},
   "closed_dates": ["2026-10-12", "2026-11-03", "2026-11-23", "2027-01-01", "2027-01-11", "2027-02-11", "2027-02-23"],
   "note": "Giờ của 秋葉原中央通り店 · nghỉ ngày lễ"}
 ]
}
```

`web/data/latest.json`:
```json
{"generated_at": null, "shops": {}}
```

`web/data/daily.json`:
```json
{}
```

- [ ] **Step 7: Chạy thử với các trang thật**

Run: `.venv/bin/python -m crawler.run`
Expected: in ra 6 dòng `[morimori] OK 16 giá`, `[ichiban] OK 16 giá`, … Số giá có thể ít hơn 16 nếu cửa hàng không thu mua một số màu (ví dụ MIX khoảng 6–12 giá). Exit code 0. Kiểm tra thêm:
```bash
.venv/bin/python -c "import json;d=json.load(open('web/data/latest.json'));[print(k,v['error'],len(v['prices'])) for k,v in d['shops'].items()]"
```
Expected: cả 6 cửa hàng đều có `error` là `None`. Nếu cửa hàng nào lỗi hoặc có 0 giá, mở URL của cửa hàng đó, so markup với fixture, sửa parser, cập nhật fixture và test, rồi chạy lại. Mở `web/data/latest.json` và đối chiếu 2–3 giá với trang thật.

- [ ] **Step 8: Commit**

```bash
git add crawler/store.py crawler/run.py crawler/tests/test_run.py web/data
git commit -m "feat(crawler): điểm chạy crawler, catalog và dữ liệu đầu tiên"
```

---

### Task 8: GitHub Actions (crawl 15 phút/lần + CI)

**Files:**
- Create: `.github/workflows/crawl.yml`, `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `python -m crawler.run` (Task 7), `npm test` (Task 9 sẽ tạo `package.json`; ci.yml chạy được sau Task 9)

- [ ] **Step 1: Viết `.github/workflows/crawl.yml`**

```yaml
name: crawl

on:
  schedule:
    - cron: "*/15 * * * *"
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: crawl
  cancel-in-progress: false

jobs:
  crawl:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt
      - name: Crawl giá
        run: python -m crawler.run
      - name: Commit dữ liệu nếu có thay đổi
        if: always()
        run: |
          git config user.name "kaitori-bot"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add web/data
          if git diff --cached --quiet; then
            echo "Không có thay đổi"
            exit 0
          fi
          git commit -m "data: cập nhật giá $(TZ=Asia/Tokyo date '+%m/%d %H:%M')"
          git pull --rebase
          git push
```

- [ ] **Step 2: Viết `.github/workflows/ci.yml`**

```yaml
name: ci

on:
  push:
    paths-ignore: ["web/data/**"]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt
      - run: python -m pytest -q
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - run: npm test
```

- [ ] **Step 3: Kiểm tra cú pháp YAML**

Run: `.venv/bin/python -c "import yaml" 2>/dev/null || .venv/bin/pip install -q pyyaml; .venv/bin/python -c "import yaml,sys;[yaml.safe_load(open(f)) for f in ['.github/workflows/crawl.yml','.github/workflows/ci.yml']];print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add .github
git commit -m "ci: crawl giá 15 phút/lần và chạy test"
```

---

### Task 9: `logic.js` phần 1: định dạng, lọc, giờ, trạng thái mở cửa

**Files:**
- Create: `package.json`, `web/js/logic.js`
- Test: `tests/web/logic.test.js`

**Interfaces:**
- Consumes: định dạng `catalog.json` và `latest.json` (Task 6, 7)
- Produces (export từ `web/js/logic.js`):
  - `WEEKDAYS = ["mon",…,"sun"]`, `WEEKDAY_VI = ["T2",…,"CN"]`, `WEEKDAY_FULL = ["Thứ 2",…,"Chủ nhật"]`
  - `esc(value) -> string`, `formatYen(n) -> string`, `formatDiff(n) -> string`
  - `jstDate(date: Date) -> "YYYY-MM-DD"`, `formatTime(iso) -> "MM/DD HH:MM"`, `isStale(iso, now: Date, hours = 2) -> boolean`
  - `addDays(dateStr, n) -> dateStr`, `weekdayIndex(dateStr) -> 0..6` (0 = Thứ 2), `isWeekend(dateStr) -> boolean`
  - `bestOffer(variantId, latest, shopIds) -> {shop, price} | null`
  - `filterVariants(variants, {cap, color})`, `filterShops(shops, query)`
  - `openStatus(shop, now: Date) -> {open: boolean, text: string}`

- [ ] **Step 1: Tạo `package.json`**

```json
{
  "name": "iphone-checker-web",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test tests/web/"
  }
}
```

- [ ] **Step 2: Viết test thất bại**

`tests/web/logic.test.js`:
```js
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  addDays, bestOffer, esc, filterShops, filterVariants, formatDiff, formatTime, formatYen,
  isStale, isWeekend, jstDate, openStatus, weekdayIndex,
} from "../../web/js/logic.js";

test("formatYen and formatDiff", () => {
  assert.equal(formatYen(262000), "262,000");
  assert.equal(formatYen(null), "—");
  assert.equal(formatDiff(22200), "+22,200");
  assert.equal(formatDiff(-1800), "−1,800");
  assert.equal(formatDiff(0), "+0");
  assert.equal(formatDiff(null), "—");
});

test("esc escapes html", () => {
  assert.equal(esc(`<a href="x">&'`), "&lt;a href=&quot;x&quot;&gt;&amp;&#39;");
});

test("JST dates and times", () => {
  assert.equal(jstDate(new Date("2026-10-01T15:05:00Z")), "2026-10-02");
  assert.equal(formatTime("2026-10-01T16:15:00Z"), "10/02 01:15");
  assert.equal(formatTime(null), "—");
});

test("isStale after 2 hours", () => {
  const now = new Date("2026-10-02T12:00:00+09:00");
  assert.equal(isStale("2026-10-02T10:30:00+09:00", now), false);
  assert.equal(isStale("2026-10-02T09:59:00+09:00", now), true);
  assert.equal(isStale(null, now), true);
});

test("date helpers", () => {
  assert.equal(addDays("2026-10-31", 1), "2026-11-01");
  assert.equal(addDays("2026-10-01", -1), "2026-09-30");
  assert.equal(weekdayIndex("2026-10-05"), 0); // Thứ 2
  assert.equal(weekdayIndex("2026-10-04"), 6); // Chủ nhật
  assert.equal(isWeekend("2026-10-03"), true);
  assert.equal(isWeekend("2026-10-02"), false);
});

test("bestOffer picks highest among given shops", () => {
  const latest = { shops: {
    a: { prices: { "pm-256-black": 236000 } },
    b: { prices: { "pm-256-black": 238000 } },
    c: { prices: {} },
  } };
  assert.deepEqual(bestOffer("pm-256-black", latest, ["a", "b", "c"]), { shop: "b", price: 238000 });
  assert.deepEqual(bestOffer("pm-256-black", latest, ["a"]), { shop: "a", price: 236000 });
  assert.equal(bestOffer("pm-2tb-black", latest, ["a", "b"]), null);
});

test("filterVariants and filterShops", () => {
  const variants = [
    { id: "1", capacity: "256GB", color: "black" },
    { id: "2", capacity: "256GB", color: "silver" },
    { id: "3", capacity: "1TB", color: "black" },
  ];
  assert.deepEqual(filterVariants(variants, { cap: "all", color: "all" }).map((v) => v.id), ["1", "2", "3"]);
  assert.deepEqual(filterVariants(variants, { cap: "256GB", color: "black" }).map((v) => v.id), ["1"]);
  const shops = [{ id: "morimori", name: "森森" }, { id: "mix", name: "MIX" }];
  assert.deepEqual(filterShops(shops, "森").map((s) => s.id), ["morimori"]);
  assert.deepEqual(filterShops(shops, " Mi ").map((s) => s.id), ["mix"]);
  assert.equal(filterShops(shops, "").length, 2);
});

const SHOP = {
  hours: { mon: ["10:00", "19:00"], tue: ["10:00", "19:00"], wed: ["10:00", "19:00"], thu: ["10:00", "19:00"], fri: ["10:00", "19:00"], sat: ["10:00", "19:00"], sun: null },
  closed_dates: ["2026-10-05"],
};
const at = (iso) => new Date(iso);

test("openStatus during opening hours", () => {
  assert.deepEqual(openStatus(SHOP, at("2026-10-02T12:00:00+09:00")), { open: true, text: "Đang mở · đóng 19:00" });
});

test("openStatus before opening today", () => {
  assert.deepEqual(openStatus(SHOP, at("2026-10-02T09:00:00+09:00")), { open: false, text: "Đã đóng · mở 10:00" });
});

test("openStatus exactly at closing time is closed", () => {
  assert.deepEqual(openStatus(SHOP, at("2026-10-02T19:00:00+09:00")), { open: false, text: "Đã đóng · mở 10:00 ngày mai" });
});

test("openStatus skips Sunday and closed_dates", () => {
  // T7 20:00 → CN nghỉ, T2 10/05 nghỉ đột xuất → mở lại T3
  assert.deepEqual(openStatus(SHOP, at("2026-10-03T20:00:00+09:00")), { open: false, text: "Đã đóng · mở 10:00 T3" });
});

test("openStatus uses JST even when given UTC", () => {
  assert.equal(openStatus(SHOP, at("2026-10-02T03:00:00Z")).open, true); // 12:00 JST
});
```

- [ ] **Step 3: Chạy test, xác nhận thất bại**

Run: `npm test`
Expected: FAIL với `Cannot find module .../web/js/logic.js`

- [ ] **Step 4: Viết `web/js/logic.js`**

```js
// Hàm thuần dùng chung cho app.js và charts.js. Không chạm DOM, để test được bằng node.
const TZ = "Asia/Tokyo";

export const WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
export const WEEKDAY_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
export const WEEKDAY_FULL = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ESCAPES[ch]);
}

export function formatYen(n) {
  return n == null ? "—" : n.toLocaleString("en-US");
}

export function formatDiff(n) {
  if (n == null) return "—";
  return `${n >= 0 ? "+" : "−"}${Math.abs(n).toLocaleString("en-US")}`;
}

const jstFormat = new Intl.DateTimeFormat("en-CA", {
  timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", hourCycle: "h23",
});

function jstParts(date) {
  const p = Object.fromEntries(jstFormat.formatToParts(date).map((x) => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, month: p.month, day: p.day, time: `${p.hour}:${p.minute}` };
}

export function jstDate(date) {
  return jstParts(date).date;
}

export function formatTime(iso) {
  if (!iso) return "—";
  const p = jstParts(new Date(iso));
  return `${p.month}/${p.day} ${p.time}`;
}

export function isStale(iso, now, hours = 2) {
  return !iso || now - new Date(iso) > hours * 3600 * 1000;
}

export function addDays(dateStr, n) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export function weekdayIndex(dateStr) {
  return (new Date(`${dateStr}T00:00:00Z`).getUTCDay() + 6) % 7;
}

export function isWeekend(dateStr) {
  return weekdayIndex(dateStr) >= 5;
}

export function bestOffer(variantId, latest, shopIds) {
  let best = null;
  for (const id of shopIds) {
    const price = latest.shops?.[id]?.prices?.[variantId];
    if (price != null && (best === null || price > best.price)) best = { shop: id, price };
  }
  return best;
}

export function filterVariants(variants, { cap = "all", color = "all" } = {}) {
  return variants.filter((v) => (cap === "all" || v.capacity === cap) && (color === "all" || v.color === color));
}

export function filterShops(shops, query = "") {
  const q = query.trim().toLowerCase();
  if (!q) return shops;
  return shops.filter((s) => s.name.toLowerCase().includes(q) || s.id.includes(q));
}

function hoursOn(shop, dateStr) {
  if ((shop.closed_dates ?? []).includes(dateStr)) return null;
  return shop.hours?.[WEEKDAYS[weekdayIndex(dateStr)]] ?? null;
}

export function openStatus(shop, now) {
  const today = jstParts(now);
  const hours = hoursOn(shop, today.date);
  if (hours && today.time >= hours[0] && today.time < hours[1]) {
    return { open: true, text: `Đang mở · đóng ${hours[1]}` };
  }
  if (hours && today.time < hours[0]) {
    return { open: false, text: `Đã đóng · mở ${hours[0]}` };
  }
  for (let i = 1; i <= 7; i++) {
    const day = addDays(today.date, i);
    const next = hoursOn(shop, day);
    if (next) {
      const when = i === 1 ? "ngày mai" : WEEKDAY_VI[weekdayIndex(day)];
      return { open: false, text: `Đã đóng · mở ${next[0]} ${when}` };
    }
  }
  return { open: false, text: "Đã đóng" };
}
```

- [ ] **Step 5: Chạy test, xác nhận pass**

Run: `npm test`
Expected: PASS (12 tests)

- [ ] **Step 6: Commit**

```bash
git add package.json web/js/logic.js tests/web/logic.test.js
git commit -m "feat(web): hàm logic định dạng, lọc, giờ JST, trạng thái mở cửa"
```

---

### Task 10: `logic.js` phần 2: dữ liệu biểu đồ và thống kê theo thứ

**Files:**
- Modify: `web/js/logic.js` (thêm vào cuối file)
- Test: `tests/web/charts.test.js`

**Interfaces:**
- Consumes: `addDays`, `weekdayIndex` (Task 9), định dạng `daily.json` `{date: {variant: {max, shop}}}` (Task 6)
- Produces:
  - `MIN_DAYS = 14`
  - `dateRange(daily, today, range: number | "all") -> string[]`
  - `chartSeries(daily, catalog, cap, range, today) -> {labels, datasets: [{variant, color, label, hex, data: (number|null)[], shops: (string|null)[]}]}`
  - `weekdayStats(daily, variantId, today, windowDays = 28) -> {ready: false, needDays} | {ready: true, deltas: (number|null)[7], best, worst, gap}`

- [ ] **Step 1: Viết test thất bại**

`tests/web/charts.test.js`:
```js
import assert from "node:assert/strict";
import { test } from "node:test";
import { addDays, chartSeries, dateRange, weekdayIndex, weekdayStats } from "../../web/js/logic.js";

const CATALOG = {
  colors: { black: { vi: "Đen", hex: "#333" }, silver: { vi: "Bạc", hex: "#aaa" } },
  variants: [
    { id: "pm-256-black", capacity: "256GB", color: "black", apple_price: 239800 },
    { id: "pm-256-silver", capacity: "256GB", color: "silver", apple_price: 239800 },
    { id: "pm-1tb-black", capacity: "1TB", color: "black", apple_price: 344800 },
  ],
};

test("dateRange fixed and all", () => {
  assert.deepEqual(dateRange({}, "2026-10-02", 3), ["2026-09-30", "2026-10-01", "2026-10-02"]);
  assert.deepEqual(dateRange({ "2026-10-01": {} }, "2026-10-02", "all"), ["2026-10-01", "2026-10-02"]);
  assert.deepEqual(dateRange({}, "2026-10-02", "all"), ["2026-10-02"]);
});

test("chartSeries fills missing days with null", () => {
  const daily = {
    "2026-09-30": { "pm-256-black": { max: 236000, shop: "a" } },
    "2026-10-02": { "pm-256-black": { max: 238000, shop: "b" }, "pm-256-silver": { max: 231000, shop: "a" } },
  };
  const { labels, datasets } = chartSeries(daily, CATALOG, "256GB", 3, "2026-10-02");
  assert.deepEqual(labels, ["2026-09-30", "2026-10-01", "2026-10-02"]);
  assert.deepEqual(datasets.map((d) => d.variant), ["pm-256-black", "pm-256-silver"]);
  assert.deepEqual(datasets[0].data, [236000, null, 238000]);
  assert.deepEqual(datasets[0].shops, ["a", null, "b"]);
  assert.equal(datasets[0].label, "Đen");
  assert.equal(datasets[0].hex, "#333");
  assert.deepEqual(datasets[1].data, [null, null, 231000]);
});

function buildDaily(today, days, valueFor) {
  const daily = {};
  for (let i = 0; i < days; i++) {
    const d = addDays(today, -i);
    const v = valueFor(d);
    if (v != null) daily[d] = { "pm-256-black": { max: v, shop: "a" } };
  }
  return daily;
}

test("weekdayStats finds weekday pattern", () => {
  // 2026-10-04 là Chủ nhật → 28 ngày = đúng 4 tuần T2..CN
  const daily = buildDaily("2026-10-04", 28, (d) => (weekdayIndex(d) >= 5 ? 243000 : 250000));
  const stats = weekdayStats(daily, "pm-256-black", "2026-10-04");
  assert.equal(stats.ready, true);
  assert.deepEqual(stats.deltas, [2000, 2000, 2000, 2000, 2000, -5000, -5000]);
  assert.equal(stats.best, 0);
  assert.equal(stats.worst, 5);
  assert.equal(stats.gap, 7000);
});

test("weekdayStats not ready under 14 days", () => {
  const daily = buildDaily("2026-10-04", 10, () => 250000);
  assert.deepEqual(weekdayStats(daily, "pm-256-black", "2026-10-04"), { ready: false, needDays: 4 });
});

test("weekdayStats ignores missing days", () => {
  // Bỏ hết các ngày Thứ 4 → delta Thứ 4 là null, các thứ khác vẫn tính được
  const daily = buildDaily("2026-10-04", 28, (d) => (weekdayIndex(d) === 2 ? null : weekdayIndex(d) >= 5 ? 244000 : 250000));
  const stats = weekdayStats(daily, "pm-256-black", "2026-10-04");
  assert.equal(stats.ready, true);
  assert.equal(stats.deltas[2], null);
  assert.equal(stats.deltas[0], 2000);
  assert.equal(stats.deltas[6], -4000);
  assert.equal(stats.gap, 6000);
});
```

Phép tính cho test cuối: mỗi tuần có 4 ngày trong tuần × 250000 và 2 ngày cuối tuần × 244000, trung bình = (1,000,000 + 488,000) / 6 = 248,000. Delta ngày thường là +2000, cuối tuần là −4000, nên gap = 6000.

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `npm test`
Expected: FAIL với `SyntaxError: The requested module '../../web/js/logic.js' does not provide an export named 'chartSeries'`

- [ ] **Step 3: Thêm vào cuối `web/js/logic.js`**

```js
export const MIN_DAYS = 14;

export function dateRange(daily, today, range) {
  const first = Object.keys(daily).sort()[0] ?? today;
  const start = range === "all" ? first : addDays(today, -(range - 1));
  const dates = [];
  for (let d = start; d <= today; d = addDays(d, 1)) dates.push(d);
  return dates;
}

export function chartSeries(daily, catalog, cap, range, today) {
  const labels = dateRange(daily, today, range);
  const datasets = catalog.variants
    .filter((v) => v.capacity === cap)
    .map((v) => ({
      variant: v.id,
      color: v.color,
      label: catalog.colors[v.color].vi,
      hex: catalog.colors[v.color].hex,
      data: labels.map((d) => daily[d]?.[v.id]?.max ?? null),
      shops: labels.map((d) => daily[d]?.[v.id]?.shop ?? null),
    }));
  return { labels, datasets };
}

export function weekdayStats(daily, variantId, today, windowDays = 28) {
  const values = [];
  for (let i = windowDays - 1; i >= 0; i--) {
    const d = addDays(today, -i);
    const v = daily[d]?.[variantId]?.max;
    if (v != null) values.push({ d, v });
  }
  if (values.length < MIN_DAYS) return { ready: false, needDays: MIN_DAYS - values.length };

  // So mỗi ngày với trung bình của chính tuần đó, để xu hướng tăng/giảm dài hạn không làm lệch kết quả.
  const weeks = new Map();
  for (const x of values) {
    const monday = addDays(x.d, -weekdayIndex(x.d));
    if (!weeks.has(monday)) weeks.set(monday, []);
    weeks.get(monday).push(x);
  }
  const sums = Array(7).fill(0);
  const counts = Array(7).fill(0);
  for (const list of weeks.values()) {
    if (list.length < 2) continue;
    const mean = list.reduce((s, x) => s + x.v, 0) / list.length;
    for (const x of list) {
      const w = weekdayIndex(x.d);
      sums[w] += x.v - mean;
      counts[w] += 1;
    }
  }
  const deltas = sums.map((s, i) => (counts[i] ? Math.round(s / counts[i]) : null));
  const known = deltas.map((v, i) => [v, i]).filter(([v]) => v != null);
  const best = known.reduce((a, b) => (b[0] > a[0] ? b : a))[1];
  const worst = known.reduce((a, b) => (b[0] < a[0] ? b : a))[1];
  return { ready: true, deltas, best, worst, gap: Math.round((deltas[best] - deltas[worst]) / 100) * 100 };
}
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `npm test`
Expected: PASS (17 tests)

- [ ] **Step 5: Commit**

```bash
git add web/js/logic.js tests/web/charts.test.js
git commit -m "feat(web): dữ liệu biểu đồ theo ngày và thống kê theo thứ"
```

---

### Task 11: Trang chính: bảng giá, bộ lọc, giờ cập nhật, trạng thái mở cửa

**Files:**
- Create: `web/index.html`, `web/style.css`, `web/js/config.js`, `web/js/app.js`, `web/js/charts.js` (Task này chỉ tạo bản tạm có `renderCharts` rỗng; Task 12 viết bản thật)

**Interfaces:**
- Consumes: mọi export của `logic.js` (Task 9, 10); các file `web/data/*.json` (Task 7)
- Produces: `state = {cap, color, q, chartCap, chartColor, range}` truyền cho `renderCharts(data, state)`; `data = {catalog, latest, daily}`

- [ ] **Step 1: Viết `web/js/config.js`**

```js
// Nơi đọc dữ liệu JSON. Chạy local: "data/". Khi deploy: đổi thành
// "https://raw.githubusercontent.com/<user>/<repo>/main/web/data/" (xem Task 13).
export const DATA_BASE = "data/";
```

- [ ] **Step 2: Viết `web/index.html`**

```html
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Giá Kaitori iPhone 18 Pro Max</title>
  <meta name="description" content="So sánh giá thu mua iPhone 18 Pro Max mới chưa kích hoạt ở các cửa hàng kaitori tại Nhật, cập nhật tự động.">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="top">
    <h1>Giá thu mua iPhone 18 Pro Max</h1>
    <p class="sub">So sánh giá kaitori ở Nhật · máy mới chưa kích hoạt (新品未開封)</p>
  </header>

  <main>
    <p id="error" class="error" hidden></p>

    <section class="filters">
      <input id="q" type="search" placeholder="🔍 Tìm cửa hàng…" autocomplete="off">
      <div id="cap-chips" class="chips"></div>
      <div id="color-chips" class="chips"></div>
    </section>

    <div class="table-wrap"><table id="price-table"></table></div>
    <p class="legend">Chênh lệch = giá kaitori cao nhất − giá Apple · Ô xanh = cửa hàng trả cao nhất · — = không thu mua · Giờ dưới tên cửa hàng = lần giá thay đổi gần nhất</p>

    <section class="card">
      <div class="card-head">
        <h2>Giá cao nhất mỗi ngày</h2>
        <div id="chart-cap" class="chips"></div>
        <div id="range-chips" class="chips"></div>
      </div>
      <div class="chart-box"><canvas id="line-chart"></canvas></div>
      <p class="legend">Nền cam = Thứ 7, Chủ nhật · Nét đứt = giá Apple</p>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Giá theo thứ trong tuần <small>(4 tuần gần nhất)</small></h2>
        <div id="stat-color" class="chips"></div>
      </div>
      <p id="weekday-empty" class="empty" hidden></p>
      <div class="chart-box short"><canvas id="weekday-chart"></canvas></div>
      <p id="weekday-tip" class="tip"></p>
    </section>
  </main>

  <footer>Giá tự động cập nhật khoảng 15 phút/lần và chỉ để tham khảo. Hãy xác nhận trên trang của cửa hàng trước khi bán.</footer>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <script type="module" src="js/app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Viết `web/style.css`**

```css
:root {
  --bg: #f6f7f9;
  --surface: #ffffff;
  --text: #1d1f23;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #111827;
  --link: #1565c0;
  --good: #0a7a33;
  --good-bg: #e7f7ec;
  --bad: #c62828;
  --warn: #b45309;
}

* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
.top, main, footer { max-width: 1200px; margin: 0 auto; padding: 0 16px; }
.top { padding-top: 20px; }
h1 { font-size: 20px; margin: 0; }
h2 { font-size: 16px; margin: 0; }
h2 small { color: var(--muted); font-weight: 400; }
.sub, .legend, footer { color: var(--muted); font-size: 12px; }
footer { padding-bottom: 24px; }
.error { background: #fdecea; color: var(--bad); padding: 10px 12px; border-radius: 8px; }

.filters { display: flex; flex-direction: column; gap: 8px; margin: 16px 0 12px; }
#q { max-width: 320px; padding: 8px 12px; border: 1px solid var(--line); border-radius: 8px; font-size: 14px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { border: 1px solid var(--line); background: var(--surface); border-radius: 999px; padding: 4px 12px; font-size: 13px; cursor: pointer; color: var(--text); }
.chip.on { background: var(--accent); border-color: var(--accent); color: #fff; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; border: 1px solid rgba(0, 0, 0, .1); }

.table-wrap { overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
table { border-collapse: separate; border-spacing: 0; width: 100%; }
th, td { padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: right; white-space: nowrap; background: var(--surface); font-variant-numeric: tabular-nums; }
th { font-size: 12px; color: var(--muted); font-weight: 600; background: #fafafa; vertical-align: top; }
tbody tr:last-child td { border-bottom: 0; }
.s1, .s2, .s3 { position: sticky; z-index: 2; }
.s1 { left: 0; min-width: 130px; width: 130px; text-align: left; }
.s2 { left: 130px; min-width: 80px; width: 80px; }
.s3 { left: 210px; min-width: 90px; width: 90px; border-right: 2px solid var(--line); }
th.shop { min-width: 120px; }
th.shop a { color: var(--link); text-decoration: none; font-size: 13px; }
th.shop span { display: block; font-weight: 400; font-size: 11px; }
.status.open { color: var(--good); }
.status.closed { color: var(--muted); }
.stale { color: var(--warn); }
td.best { background: var(--good-bg); color: var(--good); font-weight: 700; }
.pos { color: var(--good); font-weight: 700; }
.neg { color: var(--bad); font-weight: 700; }
td.empty { text-align: center; color: var(--muted); }

.card { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 14px; margin: 16px 0; }
.card-head { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; margin-bottom: 10px; }
.chart-box { position: relative; height: 300px; }
.chart-box.short { height: 220px; }
.empty { color: var(--muted); text-align: center; padding: 40px 0; }
.tip { font-weight: 600; color: var(--good); }

@media (max-width: 600px) {
  /* Điện thoại: tên màu xuống dòng để 3 cột cố định chỉ chiếm khoảng 230px */
  .s1 { min-width: 96px; width: 96px; white-space: normal; }
  .s1 .cname { display: block; padding-left: 16px; color: var(--muted); font-size: 12px; }
  .s2 { left: 96px; min-width: 64px; width: 64px; }
  .s3 { left: 160px; min-width: 70px; width: 70px; }
  th, td { padding: 6px 6px; font-size: 13px; }
  th.shop { min-width: 104px; }
  .chart-box { height: 240px; }
}
```

- [ ] **Step 4: Viết `web/js/charts.js` (bản tạm)**

```js
export function renderCharts() {}
```

- [ ] **Step 5: Viết `web/js/app.js`**

```js
import { DATA_BASE } from "./config.js";
import {
  bestOffer, esc, filterShops, filterVariants, formatDiff, formatTime, formatYen, isStale, openStatus,
} from "./logic.js";
import { renderCharts } from "./charts.js";

const state = { cap: "all", color: "all", q: "", chartCap: null, chartColor: null, range: 30 };
let data = null;

const $ = (selector) => document.querySelector(selector);

async function loadJson(name) {
  const res = await fetch(`${DATA_BASE}${name}?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return res.json();
}

function capacities() {
  return [...new Set(data.catalog.variants.map((v) => v.capacity))];
}

function colorOptions() {
  return Object.entries(data.catalog.colors).map(([id, c]) => ({ value: id, label: c.vi, dot: c.hex }));
}

function readState() {
  let saved = {};
  try {
    saved = JSON.parse(localStorage.getItem("filters") || "{}");
  } catch {
    saved = {};
  }
  const url = new URLSearchParams(location.search);
  const cap = url.get("cap") || saved.cap;
  const color = url.get("color") || saved.color;
  state.cap = capacities().includes(cap) ? cap : "all";
  state.color = color in data.catalog.colors ? color : "all";
  state.chartCap = state.cap !== "all" ? state.cap : capacities()[0];
  state.chartColor = state.color !== "all" ? state.color : Object.keys(data.catalog.colors)[0];
}

function saveState() {
  const url = new URLSearchParams();
  if (state.cap !== "all") url.set("cap", state.cap);
  if (state.color !== "all") url.set("color", state.color);
  const query = url.toString();
  history.replaceState(null, "", query ? `?${query}` : location.pathname);
  try {
    localStorage.setItem("filters", JSON.stringify({ cap: state.cap, color: state.color }));
  } catch {
    // trình duyệt chặn localStorage: bỏ qua, bộ lọc vẫn nằm trong URL
  }
}

function renderChips(el, options, current, onPick) {
  el.innerHTML = options
    .map((o) => {
      const dot = o.dot ? `<span class="dot" style="background:${esc(o.dot)}"></span>` : "";
      return `<button type="button" class="chip${o.value === current ? " on" : ""}" data-value="${esc(o.value)}">${dot}${esc(o.label)}</button>`;
    })
    .join("");
  el.onclick = (event) => {
    const button = event.target.closest("button[data-value]");
    if (button) onPick(button.dataset.value);
  };
}

function renderFilters() {
  renderChips($("#cap-chips"), [{ value: "all", label: "Tất cả" }, ...capacities().map((c) => ({ value: c, label: c }))], state.cap, (v) => {
    state.cap = v;
    if (v !== "all") state.chartCap = v;
    update();
  });
  renderChips($("#color-chips"), [{ value: "all", label: "Mọi màu" }, ...colorOptions()], state.color, (v) => {
    state.color = v;
    if (v !== "all") state.chartColor = v;
    update();
  });
  renderChips($("#chart-cap"), capacities().map((c) => ({ value: c, label: c })), state.chartCap, (v) => {
    state.chartCap = v;
    update();
  });
  const ranges = [{ value: "7", label: "7 ngày" }, { value: "30", label: "30 ngày" }, { value: "all", label: "Tất cả" }];
  renderChips($("#range-chips"), ranges, String(state.range), (v) => {
    state.range = v === "all" ? "all" : Number(v);
    update();
  });
  renderChips($("#stat-color"), colorOptions(), state.chartColor, (v) => {
    state.chartColor = v;
    update();
  });
}

function shopHeader(shop, shopState, now) {
  const status = openStatus(shop, now);
  const stale = shopState && isStale(shopState.last_success_at, now);
  return `<th class="shop" title="${esc(shop.note ?? "")}">
    <a href="${esc(shop.url)}" target="_blank" rel="noopener">${esc(shop.name)} ↗</a>
    <span class="time">${formatTime(shopState?.display_at)}</span>
    <span class="status ${status.open ? "open" : "closed"}">${status.open ? "🟢" : "🔴"} ${esc(status.text)}</span>
    ${stale ? '<span class="stale">⚠ dữ liệu cũ</span>' : ""}
  </th>`;
}

function renderTable() {
  const { catalog, latest } = data;
  const now = new Date();
  const shops = filterShops(catalog.shops, state.q);
  const shopIds = shops.map((s) => s.id);
  const head = `<thead><tr><th class="s1">Phiên bản</th><th class="s2">Apple</th><th class="s3">Chênh lệch</th>${shops
    .map((s) => shopHeader(s, latest.shops?.[s.id], now))
    .join("")}</tr></thead>`;

  const rows = filterVariants(catalog.variants, state)
    .map((v) => {
      const color = catalog.colors[v.color];
      const best = bestOffer(v.id, latest, shopIds);
      const diff = best ? best.price - v.apple_price : null;
      const diffClass = diff == null ? "" : diff >= 0 ? "pos" : "neg";
      const cells = shops
        .map((s) => {
          const price = latest.shops?.[s.id]?.prices?.[v.id];
          const isBest = best && price === best.price;
          return `<td class="${isBest ? "best" : ""}">${formatYen(price)}</td>`;
        })
        .join("");
      return `<tr>
        <td class="s1"><span class="dot" style="background:${esc(color.hex)}"></span>${esc(v.capacity)} <span class="cname">${esc(color.vi)}</span></td>
        <td class="s2">${formatYen(v.apple_price)}</td>
        <td class="s3 ${diffClass}">${formatDiff(diff)}</td>${cells}
      </tr>`;
    })
    .join("");

  const empty = `<tr><td colspan="${3 + shops.length}" class="empty">Không có kết quả phù hợp</td></tr>`;
  $("#price-table").innerHTML = `${head}<tbody>${rows || empty}</tbody>`;
}

function update() {
  saveState();
  renderFilters();
  renderTable();
  renderCharts(data, state);
}

async function init() {
  try {
    const [catalog, latest, daily] = await Promise.all(["catalog.json", "latest.json", "daily.json"].map(loadJson));
    data = { catalog, latest, daily };
  } catch (err) {
    $("#error").hidden = false;
    $("#error").textContent = `Không tải được dữ liệu (${err.message}). Hãy thử tải lại trang.`;
    return;
  }
  readState();
  $("#q").addEventListener("input", (event) => {
    state.q = event.target.value;
    renderTable();
  });
  update();
  // Cập nhật lại trạng thái mở cửa và nhãn "dữ liệu cũ" mỗi phút mà không cần tải lại trang.
  setInterval(renderTable, 60 * 1000);
}

init();
```

- [ ] **Step 6: Kiểm tra bằng trình duyệt**

Run: `python3 -m http.server 8000 -d web`, rồi mở `http://localhost:8000/`.

Kiểm tra:
- Bảng hiện 16 dòng × 6 cửa hàng với dữ liệu thật từ Task 7. Ô cao nhất mỗi dòng được tô xanh. Cột Chênh lệch có màu xanh hoặc đỏ.
- Đầu mỗi cột cửa hàng có link ↗ mở tab mới, giờ dạng `10/02 01:15`, và 🟢/🔴 kèm giờ đóng hoặc mở.
- Thu hẹp cửa sổ về khoảng 375px (DevTools, chế độ điện thoại) rồi cuộn ngang: 3 cột đầu đứng yên, chữ "256GB" và tên màu nằm trên 2 dòng, không bị cắt.
- Bấm `512GB` thì chỉ còn 4 dòng, URL thành `?cap=512GB`. Tải lại trang thì bộ lọc vẫn giữ.
- Gõ `森` vào ô tìm kiếm thì chỉ còn cột 森森.
- Mở `http://localhost:8000/?cap=foo` thì trang về "Tất cả" và không lỗi.
- Đổi tạm tên `web/data/latest.json` rồi tải lại trang: hiện thông báo lỗi tiếng Việt. Sau đó đổi tên lại.

- [ ] **Step 7: Commit**

```bash
git add web/index.html web/style.css web/js/config.js web/js/app.js web/js/charts.js
git commit -m "feat(web): bảng giá ma trận, bộ lọc, giờ cập nhật và trạng thái mở cửa"
```

---

### Task 12: Biểu đồ đường theo ngày và biểu đồ cột theo thứ

**Files:**
- Modify: `web/js/charts.js` (thay toàn bộ bản tạm)

**Interfaces:**
- Consumes: `chartSeries`, `weekdayStats`, `isWeekend`, `jstDate`, `formatYen`, `WEEKDAY_VI`, `WEEKDAY_FULL` (Task 9, 10); `state.chartCap`, `state.chartColor`, `state.range` (Task 11); biến toàn cục `Chart` từ CDN
- Produces: `renderCharts(data, state)`

- [ ] **Step 1: Viết `web/js/charts.js`**

```js
import { WEEKDAY_FULL, WEEKDAY_VI, chartSeries, formatYen, isWeekend, jstDate, weekdayStats } from "./logic.js";

let lineChart = null;
let barChart = null;

// Tô nền cam nhạt cho Thứ 7 và Chủ nhật để dễ thấy giá cuối tuần.
const weekendShade = {
  id: "weekendShade",
  beforeDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const labels = chart.data.labels;
    const step = labels.length > 1 ? scales.x.getPixelForValue(1) - scales.x.getPixelForValue(0) : chartArea.width;
    ctx.save();
    ctx.fillStyle = "rgba(255, 167, 38, 0.14)";
    labels.forEach((date, i) => {
      if (!isWeekend(date)) return;
      const x = scales.x.getPixelForValue(i);
      ctx.fillRect(x - step / 2, chartArea.top, step, chartArea.bottom - chartArea.top);
    });
    ctx.restore();
  },
};

export function renderCharts(data, state) {
  const today = jstDate(new Date());
  renderLine(data, state, today);
  renderWeekday(data, state, today);
}

function renderLine({ catalog, daily }, state, today) {
  const { labels, datasets } = chartSeries(daily, catalog, state.chartCap, state.range, today);
  const apple = catalog.variants.find((v) => v.capacity === state.chartCap)?.apple_price ?? null;
  const shopName = (id) => catalog.shops.find((s) => s.id === id)?.name ?? id;

  lineChart?.destroy();
  lineChart = new Chart(document.querySelector("#line-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        ...datasets.map((s) => ({
          label: s.label,
          data: s.data,
          shops: s.shops,
          borderColor: s.hex,
          backgroundColor: s.hex,
          borderWidth: 2,
          pointRadius: 3,
          spanGaps: true,
          tension: 0,
        })),
        {
          label: "Giá Apple",
          data: labels.map(() => apple),
          borderColor: "#9ca3af",
          borderDash: [6, 4],
          borderWidth: 1.5,
          pointRadius: 0,
          pointHitRadius: 0,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { ticks: { callback: (_, i) => labels[i].slice(5).replace("-", "/") } },
        y: { ticks: { callback: (v) => `${Math.round(v / 1000)}k` } },
      },
      plugins: {
        legend: { position: "bottom", labels: { boxWidth: 14 } },
        tooltip: {
          callbacks: {
            title: (items) => items[0]?.label ?? "",
            label: (ctx) => {
              const shop = ctx.dataset.shops?.[ctx.dataIndex];
              return `${ctx.dataset.label}: ¥${formatYen(ctx.parsed.y)}${shop ? ` · ${shopName(shop)}` : ""}`;
            },
          },
        },
      },
    },
    plugins: [weekendShade],
  });
}

function renderWeekday({ catalog, daily }, state, today) {
  const variant = catalog.variants.find((v) => v.capacity === state.chartCap && v.color === state.chartColor);
  const stats = variant ? weekdayStats(daily, variant.id, today) : { ready: false, needDays: 14 };
  const empty = document.querySelector("#weekday-empty");
  const canvas = document.querySelector("#weekday-chart");
  const tip = document.querySelector("#weekday-tip");

  barChart?.destroy();
  barChart = null;
  if (!stats.ready) {
    empty.hidden = false;
    empty.textContent = `Đang thu thập dữ liệu (cần thêm ${stats.needDays} ngày)`;
    canvas.parentElement.hidden = true;
    tip.textContent = "";
    return;
  }

  empty.hidden = true;
  canvas.parentElement.hidden = false;
  barChart = new Chart(canvas, {
    type: "bar",
    data: {
      labels: WEEKDAY_VI,
      datasets: [{
        data: stats.deltas,
        backgroundColor: stats.deltas.map((v) => ((v ?? 0) >= 0 ? "#2e7d32" : "#c62828")),
        borderRadius: 4,
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y >= 0 ? "+" : "−"}¥${formatYen(Math.abs(ctx.parsed.y))} so với trung bình tuần`,
          },
        },
      },
      scales: { y: { ticks: { callback: (v) => `${v >= 0 ? "+" : ""}${(v / 1000).toFixed(1)}k` } } },
    },
  });
  tip.textContent = `Nên bán: ${WEEKDAY_FULL[stats.best]}, trung bình cao hơn ${WEEKDAY_FULL[stats.worst]} khoảng ¥${formatYen(stats.gap)}`;
}
```

- [ ] **Step 2: Tạo dữ liệu giả để kiểm tra biểu đồ (không commit)**

```bash
cp web/data/daily.json /tmp/daily.backup.json
.venv/bin/python - <<'EOF'
import json, datetime, random
random.seed(1)
today = datetime.date.today()
daily = {}
for i in range(35):
    d = today - datetime.timedelta(days=i)
    if i == 9:
        continue  # một ngày thiếu dữ liệu để kiểm tra đường vẫn nối liền
    base = 250000 + (0 if d.weekday() < 5 else -6000) + random.randint(-1500, 1500)
    daily[d.isoformat()] = {
        f"pm-256-{c}": {"max": base + off, "shop": "ichiban"}
        for c, off in [("burgundy", 25000), ("glacier", -2000), ("black", 0), ("silver", -4000)]
    }
json.dump(daily, open("web/data/daily.json", "w"), indent=1)
EOF
```

- [ ] **Step 3: Kiểm tra bằng trình duyệt**

Run: `python3 -m http.server 8000 -d web`, mở `http://localhost:8000/`.

Kiểm tra:
- Biểu đồ đường có 4 đường màu, nét đứt xám là giá Apple 239,800, các vùng T7–CN có nền cam, và đường vẫn nối liền qua ngày bị thiếu.
- Chạm hoặc di chuột vào một điểm: tooltip hiện "Đen: ¥250,123 · 海峡".
- Bấm `7 ngày`, `Tất cả`: trục x đổi theo. Bấm `512GB` ở biểu đồ: không có dữ liệu thì các đường trống, trang không lỗi.
- Biểu đồ cột: T2–T6 xanh, T7/CN đỏ, dòng gợi ý "Nên bán: Thứ …, trung bình cao hơn … khoảng ¥…".
- Chọn màu khác ở `#stat-color` thì biểu đồ cột đổi theo.
- Kiểm tra trạng thái chưa đủ dữ liệu: chạy `git checkout web/data/daily.json` rồi tải lại trang. Phải hiện "Đang thu thập dữ liệu (cần thêm N ngày)".

- [ ] **Step 4: Khôi phục dữ liệu thật**

Run: `git checkout web/data/daily.json && git status --short web/data`
Expected: `web/data/daily.json` không còn trong danh sách thay đổi.

- [ ] **Step 5: Commit**

```bash
git add web/js/charts.js
git commit -m "feat(web): biểu đồ giá cao nhất mỗi ngày và thống kê theo thứ"
```

---

### Task 13: Đưa lên GitHub + Cloudflare Pages

Task này thao tác với tài khoản của người dùng: tạo repo public, push code, kết nối Cloudflare. **Phải hỏi người dùng và được đồng ý trước mỗi bước có tác động ra bên ngoài.**

**Files:**
- Modify: `web/js/config.js`

- [ ] **Step 1: Hỏi người dùng tên GitHub và tên repo, rồi tạo repo public và push**

```bash
gh repo create <user>/iphone-checker-web --public --source=. --remote=origin --push
```
Expected: repo được tạo và nhánh `main` đã được push.

- [ ] **Step 2: Trỏ frontend tới dữ liệu trên GitHub**

`web/js/config.js`:
```js
// Nơi đọc dữ liệu JSON. Chạy local: "data/".
export const DATA_BASE = location.hostname === "localhost" || location.hostname === "127.0.0.1"
  ? "data/"
  : "https://raw.githubusercontent.com/<user>/iphone-checker-web/main/web/data/";
```
Thay `<user>` bằng tên GitHub thật của người dùng (lấy ở Step 1).

```bash
git add web/js/config.js && git commit -m "chore(web): đọc dữ liệu từ raw.githubusercontent.com" && git push
```

- [ ] **Step 3: Chạy workflow crawl lần đầu**

Run: `gh workflow run crawl && sleep 5 && gh run watch $(gh run list --workflow=crawl --limit 1 --json databaseId -q '.[0].databaseId')`
Expected: workflow thành công. Log có 6 dòng `[shop] OK …`. Nếu giá có thay đổi thì xuất hiện commit `data: cập nhật giá …`.

- [ ] **Step 4: Hướng dẫn người dùng kết nối Cloudflare Pages (thao tác trên dashboard)**

Trong Cloudflare: Workers & Pages → Create → Pages → Connect to Git → chọn repo, rồi cấu hình:
- Production branch: `main`
- Build command: để trống
- Build output directory: `web`
- Settings → Builds → Build watch paths: Include `*`, Exclude `web/data/*`

- [ ] **Step 5: Kiểm tra trang đã deploy**

Mở `https://<project>.pages.dev/`. Bảng có dữ liệu, DevTools → Network thấy `latest.json` được tải từ `raw.githubusercontent.com` với status 200. Đợi 15–30 phút để xác nhận workflow cron chạy tự động (tab Actions) mà không tạo build mới trên Cloudflare.
