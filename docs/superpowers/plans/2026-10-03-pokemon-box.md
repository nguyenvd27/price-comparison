# Pokémon BOX Price Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trang `/pokemon-card/` so sánh giá thu mua 21 BOX Pokémon (còn màng co) ở 8 tiệm, tự cập nhật cùng lịch với iPhone.

**Architecture:**
- Tổng quát hoá crawler theo "danh mục" (`crawler/categories.py`). iPhone giữ nguyên dữ liệu ở `web/data/`; Pokémon ghi vào `web/data/pokemon/`.
- Parser Pokémon nằm ở `crawler/pokemon/shops/`, ghép sản phẩm qua `crawler/pokemon/match.py` (theo JAN, hoặc theo tên).
- Web: trang tĩnh mới dùng chung `logic.js` với iPhone. Phần tiêu đề cột tiệm và cửa sổ xếp hạng được tách ra `table.js`.

**Tech Stack:** Python 3 (requests, BeautifulSoup, pytest) · HTML/CSS/JS ES modules (node --test) · GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-03-pokemon-box-design.md`

## Global Constraints

- Mọi lệnh pytest chạy kèm `--ignore-glob='* 2.py'`, vì repo nằm trong iCloud và hay có file trùng tên "* 2.py".
- Giới hạn giá hợp lệ: iPhone 100,000–1,000,000; Pokémon 1,000–2,000,000.
- `python -m crawler.run` không có `--category` vẫn phải chạy iPhone như cũ.
- Dữ liệu iPhone giữ nguyên ở `web/data/` (link GitHub raw đang dùng).
- Mỗi tiệm gửi tối đa số request trong bảng ở mục 5 của spec. Hết số trang thì dừng, không báo lỗi.
- Ghép sản phẩm:
  - Tên chứa từ loại trừ → bỏ.
  - Có JAN → chỉ khớp theo JAN (JAN lạ → bỏ).
  - Không có JAN → khớp alias, đúng 1 BOX mới nhận.
- Tiệm `mail_only` không tính vào Diff, ô cao nhất, xếp hạng và `daily.json`.
- Ảnh BOX hiển thị thẳng từ `https://www.pokemon-card.com/...`, không chép vào repo.
- Commit message kết thúc bằng dòng `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Làm trên nhánh `feat/pokemon-box`. Không push khi người dùng chưa đồng ý.
- Không `git add` theo đường dẫn rộng, để không dính file "* 2.*" của iCloud.

## Review Focus

1. **Tên của một bộ deck hay set chứa đúng alias của BOX** (ví dụ "30th CELEBRATION プレミアムデッキセット", "30th CELEBRATION カードセット"). Phải bị loại, không được nhận là BOX 30th. Test ở Task 2.
2. **Tiệm đổi giao diện, parser không đọc ra giá nào.** Tiệm đó phải được ghi lỗi ("Không lấy được giá nào") và giữ giá cũ, không xoá giá. Đây là quy tắc hiện có của `apply_results`; Task 1 có test với danh mục Pokémon.
3. **Ô giá ghi chữ ("問い合わせ") hoặc trống.** Bỏ qua dòng đó, không làm hỏng cả tiệm. Test ở Task 3 (オク).
4. **Tiệm lỗi hoặc dữ liệu cũ có giá cao nhất.** Không được tô xanh, không tính vào Diff, Top Diff và thẻ ở trang chủ. Test ở Task 7.
5. **Chưa có `web/data/pokemon/latest.json`** (lần chạy đầu, hoặc lỗi tải). Trang hiện thông báo thay vì vỡ; thẻ trang chủ để trống. Test `bestItemDiff` với dữ liệu rỗng ở Task 7.

---

## File Structure

- `crawler/categories.py` (mới): khai báo danh mục `iphone` và `pokemon`, gồm thư mục dữ liệu, danh sách tiệm, dữ liệu cho parser và giới hạn giá. `crawl_colors` chuyển từ `run.py` sang đây.
- `crawler/run.py` (sửa): `main(..., category="iphone")`, CLI `--category`.
- `crawler/update.py` (sửa): `validate` và `apply_results` nhận thêm `price_range`.
- `crawler/pokemon/__init__.py`, `crawler/pokemon/match.py` (mới): ghép sản phẩm.
- `crawler/pokemon/shops/__init__.py` (mới): `SHOPS` của Pokémon.
- `crawler/pokemon/shops/{morimori,homura,rudeya,ichiban,oku,ichome,shinsoku,runto}.py` (mới).
- `crawler/tests/test_categories.py`, `test_pokemon_match.py`, `test_pokemon_shops.py`, `test_pokemon_catalog.py` (mới) và `crawler/tests/fixtures/pokemon/*` (mới).
- `web/data/pokemon/catalog.json` (mới, sửa tay).
- `.github/workflows/crawl.yml` (sửa): chạy thêm danh mục Pokémon.
- `web/js/table.js` (mới): `shopHeader`, `diffClass`, `renderRankModal`, `bindRankModal`, dùng chung cho 2 trang.
- `web/js/app.js` (sửa): dùng `table.js`.
- `web/js/logic.js` (sửa): thêm `itemDiff`, `filterItems`, `sortItems`, `pickPokemonFilters`, `bestItemDiff`.
- `web/js/pokemon.js` (mới), `web/pokemon-card/index.html` (thay nội dung tạm), `web/style.css` (thêm style bảng Pokémon).
- `web/js/home.js`, `web/index.html` (sửa): thẻ Pokémon trên trang chủ.
- `tests/web/pokemon.test.js` (mới).

---

### Task 0: Tạo nhánh

- [ ] **Step 1:**

```bash
cd /Users/nguyenvd/Documents/tool/iphone-checker-web
git checkout main && git checkout -b feat/pokemon-box
```

---

### Task 1: Tổng quát hoá crawler theo danh mục

**Files:**
- Create: `crawler/categories.py`, `crawler/tests/test_categories.py`
- Modify: `crawler/run.py`, `crawler/update.py`

**Interfaces:**
- Produces:
  - `crawler.categories.Category(id: str, data_dir: Path, shops: dict, context: Callable[[dict], object], price_range: tuple[int, int])`
  - `get_category(category_id: str) -> Category`
  - `crawl_colors(catalog) -> dict[str, list[str]]`
  - `crawler.update.validate(prices, price_range=(MIN_PRICE, MAX_PRICE))`
  - `apply_results(latest, results, now, price_range=(MIN_PRICE, MAX_PRICE))`
  - `crawler.run.main(data_dir=None, shops=None, now=None, category="iphone") -> int`
- `get_category("pokemon")` import `crawler.pokemon.shops.SHOPS`. Module này được tạo ở Task 3, nên Task 1 tạo trước một bản rỗng.

- [ ] **Step 1: Viết test (fail)**

`crawler/tests/test_categories.py`:

```python
import json
from datetime import datetime
from types import SimpleNamespace

from crawler.categories import get_category
from crawler.models import Offer, ShopResult
from crawler.run import main
from crawler.store import DATA_DIR
from crawler.update import JST, apply_results

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=JST)


def test_iphone_category_is_the_old_setup():
    cat = get_category("iphone")
    assert cat.data_dir == DATA_DIR
    assert cat.price_range == (100_000, 1_000_000)
    assert "morimori" in cat.shops


def test_pokemon_category_has_own_folder_and_range():
    cat = get_category("pokemon")
    assert cat.data_dir == DATA_DIR / "pokemon"
    assert cat.price_range == (1_000, 2_000_000)
    assert cat.context({"items": [{"id": "x"}]}) == [{"id": "x"}]


def test_price_range_is_per_category():
    results = {"a": ShopResult({"mega-30th": 26000}, None)}
    latest, _ = apply_results({"shops": {}}, results, NOW)
    assert latest["shops"]["a"]["error"].startswith("Giá vô lý")
    latest, _ = apply_results({"shops": {}}, results, NOW, price_range=(1_000, 2_000_000))
    assert latest["shops"]["a"]["error"] is None


def test_run_pokemon_writes_only_its_folder(tmp_path):
    catalog = {"items": [{"id": "mega-30th"}], "shops": [{"id": "a"}, {"id": "b"}]}
    (tmp_path / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    seen = []

    def parse(raw, items):
        seen.append(items)
        return [Offer("mega-30th", 26000)]

    empty = SimpleNamespace(fetch=lambda session: "raw", parse=lambda raw, items: [])
    shops = {"a": SimpleNamespace(fetch=lambda session: "raw", parse=parse), "b": empty}
    assert main(tmp_path, shops, NOW, category="pokemon") == 0
    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert latest["shops"]["a"]["prices"] == {"mega-30th": 26000}
    assert latest["shops"]["b"]["error"] == "Không lấy được giá nào"
    assert seen == [[{"id": "mega-30th"}]]
```

- [ ] **Step 2: Chạy test, thấy fail**

Run: `.venv/bin/python -m pytest -q crawler/tests/test_categories.py --ignore-glob='* 2.py'`
Expected: lỗi `ModuleNotFoundError: No module named 'crawler.categories'`.

- [ ] **Step 3: Cài đặt**

`crawler/pokemon/__init__.py`: file rỗng.

`crawler/pokemon/shops/__init__.py`: bản rỗng tạm, Task 3 sẽ điền:

```python
SHOPS: dict = {}
```

`crawler/categories.py`:

```python
"""Mỗi danh mục (iPhone, Pokémon…) khai báo nơi lưu dữ liệu, danh sách cửa hàng và giới hạn giá."""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from crawler.store import DATA_DIR


@dataclass(frozen=True)
class Category:
    id: str
    data_dir: Path
    shops: dict
    context: Callable[[dict], object]  # catalog -> thứ parser cần (màu iPhone, danh sách BOX…)
    price_range: tuple[int, int]


def crawl_colors(catalog: dict) -> dict[str, list[str]]:
    """Chỉ các màu thuộc dòng máy đang crawl, để parser không sinh giá cho màu của dòng máy khác."""
    wanted = {color for model in catalog["models"] if model["crawl"] for color in model["colors"]}
    return {color_id: color["aliases"] for color_id, color in catalog["colors"].items() if color_id in wanted}


def pokemon_items(catalog: dict) -> list[dict]:
    return catalog["items"]


def get_category(category_id: str) -> Category:
    if category_id == "iphone":
        from crawler.shops import SHOPS

        return Category("iphone", DATA_DIR, SHOPS, crawl_colors, (100_000, 1_000_000))
    if category_id == "pokemon":
        from crawler.pokemon.shops import SHOPS

        return Category("pokemon", DATA_DIR / "pokemon", SHOPS, pokemon_items, (1_000, 2_000_000))
    raise ValueError(f"Danh mục không tồn tại: {category_id}")
```

`crawler/update.py`: sửa `validate` và `apply_results`:

```python
def validate(prices: dict[str, int], price_range: tuple[int, int] = (MIN_PRICE, MAX_PRICE)) -> str | None:
    if not prices:
        return "Không lấy được giá nào"
    low, high = price_range
    bad = sorted(v for v, p in prices.items() if not low <= p <= high)
    if bad:
        return f"Giá vô lý: {', '.join(bad)}"
    return None


def apply_results(
    latest: dict,
    results: dict[str, ShopResult],
    now: datetime,
    price_range: tuple[int, int] = (MIN_PRICE, MAX_PRICE),
) -> tuple[dict, list[dict]]:
```

Trong thân hàm, đổi dòng `error = result.error or validate(result.prices)` thành:

```python
        error = result.error or validate(result.prices, price_range)
```

`crawler/run.py`: thay toàn bộ file:

```python
import argparse
import sys
from datetime import datetime
from pathlib import Path

from crawler.categories import crawl_colors, get_category  # noqa: F401  (crawl_colors giữ để import cũ vẫn chạy)
from crawler.http import new_session
from crawler.models import ShopResult
from crawler.store import append_history, load_json, save_json
from crawler.update import JST, apply_results, update_daily


def crawl_shop(module, session, context) -> ShopResult:
    try:
        offers = module.parse(module.fetch(session), context)
        return ShopResult({offer.variant: offer.price for offer in offers}, None)
    except Exception as exc:  # một cửa hàng lỗi không được làm hỏng các cửa hàng khác
        return ShopResult({}, f"{type(exc).__name__}: {exc}")


def main(data_dir: Path | None = None, shops: dict | None = None, now: datetime | None = None,
         category: str = "iphone") -> int:
    cat = get_category(category)
    data_dir = data_dir or cat.data_dir
    shops = shops if shops is not None else cat.shops
    catalog = load_json(data_dir / "catalog.json", None)
    context = cat.context(catalog)
    session = new_session()

    results = {}
    for shop in catalog["shops"]:
        result = crawl_shop(shops[shop["id"]], session, context)
        status = f"OK {len(result.prices)} giá" if result.error is None else f"LỖI {result.error}"
        print(f"[{category}/{shop['id']}] {status}")
        results[shop["id"]] = result

    now = now or datetime.now(JST)
    old_latest = load_json(data_dir / "latest.json", {"generated_at": None, "shops": {}})
    latest, events = apply_results(old_latest, results, now, price_range=cat.price_range)
    if latest["shops"] != old_latest["shops"]:
        save_json(data_dir / "latest.json", latest)
    if events:
        append_history(data_dir, events)
    old_daily = load_json(data_dir / "daily.json", {})
    mail_only = {shop["id"] for shop in catalog["shops"] if shop.get("mail_only")}
    daily = update_daily(old_daily, latest, now, skip=mail_only)
    if daily != old_daily:
        save_json(data_dir / "daily.json", daily)

    for shop_id in results:
        if latest["shops"][shop_id]["error"]:
            print(f"[{category}/{shop_id}] bị bỏ qua: {latest['shops'][shop_id]['error']}")
    all_failed = all(latest["shops"][shop_id]["error"] for shop_id in results)
    return 1 if all_failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="iphone", choices=["iphone", "pokemon"])
    sys.exit(main(category=parser.parse_args().category))
```

- [ ] **Step 4: Chạy cả bộ test, thấy pass**

Run: `.venv/bin/python -m pytest -q --ignore-glob='* 2.py'`
Expected: toàn bộ pass, gồm `test_run.py` cũ (gọi `main(data_dir, shops, NOW)` theo vị trí) và 4 test mới.

- [ ] **Step 5: Commit**

```bash
git add crawler/categories.py crawler/run.py crawler/update.py crawler/pokemon/__init__.py crawler/pokemon/shops/__init__.py crawler/tests/test_categories.py
git commit -m "refactor(crawler): crawl theo danh mục (iphone mặc định, pokemon ghi vào web/data/pokemon)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Catalog Pokémon và bộ ghép sản phẩm

**Files:**
- Create: `web/data/pokemon/catalog.json`, `crawler/pokemon/match.py`, `crawler/tests/test_pokemon_match.py`, `crawler/tests/test_pokemon_catalog.py`

**Interfaces:**
- Produces:
  - `crawler.pokemon.match.normalize(text: str) -> str`
  - `match_item(name: str, jan: str | None, items: list[dict]) -> str | None`
  - `clean_jan(text: str | None) -> str | None`: 13 chữ số cuối của dãy số dài nhất có từ 13 chữ số trở lên, hoặc `None`.
- Catalog: `{"series": [...], "items": [...], "shops": [...]}` theo mục 3 của spec.

- [ ] **Step 1: Viết test của bộ ghép (fail)**

`crawler/tests/test_pokemon_match.py`:

```python
import pytest

from crawler.pokemon.match import clean_jan, match_item

ITEMS = [
    {"id": "mega-30th-futuristic", "jan": ["4521329463872"], "aliases": ["FUTURISTIC BOX"], "exclude": []},
    {"id": "mega-30th", "jan": ["4521329462424"], "aliases": ["30th CELEBRATION"], "exclude": ["FUTURISTIC"]},
    {"id": "sv-black-bolt", "jan": ["4521329427768"], "aliases": ["ブラックボルト"], "exclude": []},
    {"id": "mega-inferno-x", "jan": ["4521329431529", "4521329431512"], "aliases": ["インフェルノX"], "exclude": []},
    {"id": "sv-151", "jan": ["4521329346038"], "aliases": ["ポケモンカード151", "151 BOX", "SV2a"], "exclude": []},
]


@pytest.mark.parametrize("name, jan, expected", [
    ("ポケモンカードゲーム MEGA 拡張パック 30th CELEBRATION BOX [M6a]", "4521329462424", "mega-30th"),
    ("MEGA 30th CELEBRATION FUTURISTIC BOX", "4521329463872", "mega-30th-futuristic"),
    ("インフェルノX m2 BOX", "4521329431512", "mega-inferno-x"),          # JAN phụ của オク
    ("ブラックボルト デラックス BOX", "4521329427300", None),              # JAN lạ (bản DX)
    ("拡張パック「30th CELEBRATION」(M6a)", None, "mega-30th"),           # theo tên
    ("ポケモンカードゲーム MEGA 30th CELEBRATION FUTURISTIC BOX", None, "mega-30th-futuristic"),
    ("拡張パックデラックス「ブラックボルト」(SV11B)", None, None),          # DX bị loại
    ("【BOX】ブラックボルトDX", None, None),
    ("強化拡張パック「ポケモンカード151」(SV2a)", None, "sv-151"),
    ("拡張パック「ドラゴンストーム」(SM6a)", None, None),                   # không có alias nào
])
def test_match_by_jan_then_name(name, jan, expected):
    assert match_item(name, jan, ITEMS) == expected


@pytest.mark.parametrize("name", [
    "シュリンクなし MEGA 拡張パック 30th CELEBRATION BOX",
    "30th CELEBRATION BOX シュリンク無し",
    "MEGA 拡張パック 30th CELEBRATION カートン",
    "ポケモンカードゲーム MEGA 30th CELEBRATION プレミアムデッキセット エーフィ・ブラッキー",
    "ポケモンカードゲーム MEGA 30th CELEBRATION カードセット フシギダネ・ヒトカゲ・ゼニガメ",
    "拡張パック バトルパートナーズ BOX プロモカードなし",
    "30th CELEBRATION 開封済み",
])
def test_non_box_or_no_shrink_is_rejected_even_with_known_jan(name):
    assert match_item(name, "4521329462424", ITEMS) is None
    assert match_item(name, None, ITEMS) is None


def test_name_matching_two_items_is_rejected():
    items = ITEMS + [{"id": "dup", "jan": ["0"], "aliases": ["30th CELEBRATION"], "exclude": ["FUTURISTIC"]}]
    assert match_item("30th CELEBRATION BOX", None, items) is None


def test_unopened_is_not_mistaken_for_opened():
    assert match_item("30th CELEBRATION BOX 新品未開封", None, ITEMS) == "mega-30th"


@pytest.mark.parametrize("text, expected", [
    ("JAN: 4521329462424", "4521329462424"),
    ("114521329462424", "4521329462424"),      # ホムラ ghép thêm 2 chữ số phía trước
    ("‎4521329431161", "4521329431161"),  # 一丁目 có ký tự ẩn
    ("JAN: 8821329462424", "8821329462424"),
    ("", None),
    (None, None),
])
def test_clean_jan(text, expected):
    assert clean_jan(text) == expected
```

- [ ] **Step 2: Chạy, thấy fail**

Run: `.venv/bin/python -m pytest -q crawler/tests/test_pokemon_match.py --ignore-glob='* 2.py'`
Expected: lỗi `ModuleNotFoundError: No module named 'crawler.pokemon.match'`.

- [ ] **Step 3: Cài đặt `crawler/pokemon/match.py`**

```python
"""Ghép tên/JAN sản phẩm của từng cửa hàng với BOX trong catalog Pokémon."""
import re
import sys
import unicodedata

# Không phải BOX còn màng co: không màng co, thùng, deck/set, bản DX, mất thẻ khuyến mãi, đã mở.
EXCLUDE = [
    "シュリンクなし", "シュリンク無", "カートン", "デッキ", "セット", "デラックス", "dx",
    "プロモなし", "プロモカードなし", "開封済", "開封品", "パック単品", "バラパック",
]


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text or "")).lower()


def clean_jan(text: str | None) -> str | None:
    runs = [run for run in re.findall(r"\d+", unicodedata.normalize("NFKC", text or "")) if len(run) >= 13]
    return max(runs, key=len)[-13:] if runs else None


def excluded(name: str) -> bool:
    text = normalize(name).replace("未開封", "")
    return any(normalize(word) in text for word in EXCLUDE)


def match_item(name: str, jan: str | None, items: list[dict]) -> str | None:
    if excluded(name):
        return None
    if jan:
        found = [item["id"] for item in items if jan in item["jan"]]
        return found[0] if len(found) == 1 else None
    text = normalize(name)
    found = [
        item["id"]
        for item in items
        if any(normalize(alias) in text for alias in item["aliases"])
        and not any(normalize(word) in text for word in item.get("exclude", []))
    ]
    if len(found) > 1:
        print(f"Cảnh báo: {name!r} khớp nhiều BOX {found}, bỏ qua", file=sys.stderr)
    return found[0] if len(found) == 1 else None
```

- [ ] **Step 4: Chạy test bộ ghép, thấy pass**

Run: `.venv/bin/python -m pytest -q crawler/tests/test_pokemon_match.py --ignore-glob='* 2.py'`
Expected: tất cả PASS.

- [ ] **Step 5: Viết test catalog (fail)**

`crawler/tests/test_pokemon_catalog.py`:

```python
import json
import re

from crawler.store import DATA_DIR


def load():
    return json.loads((DATA_DIR / "pokemon" / "catalog.json").read_text(encoding="utf-8"))


def test_items_are_well_formed_and_unique():
    catalog = load()
    series = {s["id"] for s in catalog["series"]}
    items = catalog["items"]
    assert len(items) == 21
    assert len({i["id"] for i in items}) == 21
    jans = [j for i in items for j in i["jan"]]
    assert len(jans) == len(set(jans))
    for item in items:
        assert item["series"] in series, item["id"]
        assert item["retail"] > 0, item["id"]
        assert all(re.fullmatch(r"\d{13}", j) for j in item["jan"]), item["id"]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", item["release"]), item["id"]
        assert item["image"].startswith("https://www.pokemon-card.com/"), item["id"]
        assert item["aliases"], item["id"]


def test_shops_have_hours_and_shinsoku_is_mail_only():
    shops = load()["shops"]
    assert [s["id"] for s in shops] == ["morimori", "homura", "rudeya", "ichiban", "oku", "runto", "ichome", "shinsoku"]
    for shop in shops:
        assert set(shop["hours"]) == {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}, shop["id"]
    assert [s["id"] for s in shops if s.get("mail_only")] == ["shinsoku"]
```

- [ ] **Step 6: Chạy, thấy fail**

Run: `.venv/bin/python -m pytest -q crawler/tests/test_pokemon_catalog.py --ignore-glob='* 2.py'`
Expected: lỗi `FileNotFoundError` ở `web/data/pokemon/catalog.json`.

- [ ] **Step 7: Tạo `web/data/pokemon/catalog.json`**

Sinh file bằng script (giữ định dạng của `save_json`: `indent=1`, `ensure_ascii=False`):

```bash
.venv/bin/python - <<'EOF'
from pathlib import Path
from crawler.store import save_json

IMG = "https://www.pokemon-card.com/products/"
ROWS = [
 # id, series, name, retail, release, jans, image, aliases, exclude
 ("mega-30th-futuristic","mega","30th CELEBRATION FUTURISTIC BOX",27500,"2026-09-16",["4521329463872"],"2026/images/furbox.jpg",["FUTURISTIC BOX"],[]),
 ("mega-30th","mega","30th CELEBRATION",7200,"2026-09-16",["4521329462424"],"2026/images/30th_celebration.jpg",["30th CELEBRATION"],["FUTURISTIC"]),
 ("mega-storm-emeralda","mega","ストームエメラルダ",6000,"2026-07-31",["4521329462233"],"2026/images/stormemeralda.jpg",["ストームエメラルダ"],[]),
 ("mega-abyss-eye","mega","アビスアイ",6000,"2026-05-22",["4521329462127"],"2026/images/abisueye.jpg",["アビスアイ"],[]),
 ("mega-ninja-spinner","mega","ニンジャスピナー",5400,"2026-03-13",["4521329432786"],"2026/images/m4pkg.jpg",["ニンジャスピナー"],[]),
 ("mega-munikis-zero","mega","ムニキスゼロ",5400,"2026-01-23",["4521329432274"],"2025/images/m3.jpg",["ムニキスゼロ"],[]),
 ("mega-mega-dream-ex","mega","MEGAドリームex",5500,"2025-11-28",["4521329431932"],"2025/images/m2a.jpg",["MEGAドリームex","メガドリームex"],[]),
 ("mega-inferno-x","mega","インフェルノX",5400,"2025-09-26",["4521329431529","4521329431512"],"2025/images/M2.jpg",["インフェルノX"],[]),
 ("mega-mega-brave","mega","メガブレイブ",5400,"2025-08-01",["4521329431161"],"2025/images/M1L.jpg",["メガブレイブ"],[]),
 ("mega-mega-symphonia","mega","メガシンフォニア",5400,"2025-08-01",["4521329431185"],"2025/images/M1S.jpg",["メガシンフォニア"],[]),
 ("sv-black-bolt","sv","ブラックボルト",5800,"2025-06-06",["4521329427768"],"2025/images/sv11b.jpg",["ブラックボルト"],[]),
 ("sv-white-flare","sv","ホワイトフレア",5800,"2025-06-06",["4521329427782"],"2025/images/sv11w.jpg",["ホワイトフレア","フレアホワイト"],[]),
 ("sv-rocket-gang","sv","ロケット団の栄光",5400,"2025-04-18",["4521329374659"],"2025/images/sv10.jpg",["ロケット団の栄光"],[]),
 ("sv-heat-arena","sv","熱風のアリーナ",5400,"2025-03-14",["4521329374758"],"2025/images/sv9a.jpg",["熱風のアリーナ"],[]),
 ("sv-battle-partners","sv","バトルパートナーズ",5400,"2025-01-24",["4521329362649"],"2024/images/sv9.jpg",["バトルパートナーズ"],[]),
 ("sv-terastal-fes-ex","sv","テラスタルフェスex",5500,"2024-12-06",["4521329362342"],"2024/images/sv8a.jpg",["テラスタルフェス"],[]),
 ("sv-super-electric-breaker","sv","超電ブレイカー",5400,"2024-10-18",["4521329361505"],"2024/images/pakku_choudenbureika.jpg",["超電ブレイカー"],[]),
 ("sv-paradise-dragona","sv","楽園ドラゴーナ",5400,"2024-09-13",["4521329361352"],"2024/images/sv7a_pillow_thumbnail.jpg",["楽園ドラゴーナ"],[]),
 ("sv-stellar-miracle","sv","ステラミラクル",5400,"2024-07-19",["4521329361000"],"2024/images/pakku_suteramirakuru.jpg",["ステラミラクル"],[]),
 ("sv-night-wanderer","sv","ナイトワンダラー",5400,"2024-06-07",["4521329362496"],"2024/images/sv6a.jpg",["ナイトワンダラー"],[]),
 ("sv-151","sv","151",5400,"2023-06-16",["4521329346038"],"2023/images/sv2a.jpg",["ポケモンカード151","151 BOX","SV2a"],[]),
]
week = lambda o, c, sun=True: {**{d: [o, c] for d in ["mon","tue","wed","thu","fri","sat"]}, "sun": [o, c] if sun else None}
shops = [
 {"id":"morimori","name":"森森","url":"https://www.morimori-kaitori.jp/category/2401","hours":week("11:00","20:00"),"closed_dates":[],"note":"Giờ của 秋葉原本店"},
 {"id":"homura","name":"ホムラ","url":"https://kaitori-homura.com/products?q%5Bproduct_sub_category_id_eq%5D=128&q%5Bproduct_sub_category_product_category_id_eq%5D=14","hours":week("13:00","22:00"),"closed_dates":[],"note":"Giờ của 秋葉原店"},
 {"id":"rudeya","name":"ルデヤ","url":"https://kaitori-rudeya.com/category/detail/114","hours":week("10:00","19:00",sun=False),"closed_dates":[],"note":"Thứ 2–7 và ngày lễ; nghỉ Chủ nhật"},
 {"id":"ichiban","name":"モバイル一番","url":"https://www.mobile-ichiban.com/Prod/3/","hours":week("10:00","19:00",sun=False),"closed_dates":[],"note":"Giờ của 池袋駅前店"},
 {"id":"oku","name":"オク","url":"https://kaitori-oku.jp/category.html?cat1=340&cat2=363&cat3=367","hours":week("11:00","19:00"),"closed_dates":[],"note":"Cửa hàng 神田須田町"},
 {"id":"runto","name":"ラントゥ","url":"https://runto666.com/product-category/card/","hours":week("11:00","19:00"),"closed_dates":[],"note":"Giờ của 神田店"},
 {"id":"ichome","name":"一丁目","url":"https://www.1-chome.com/tradeCards?category=IIzyMdayU5wp7T4G","hours":week("10:00","19:00",sun=False),"closed_dates":[],"note":"Giờ của 秋葉原本店"},
 {"id":"shinsoku","name":"シンソク","url":"https://shinsoku-tcg.com/yuso-kaitori","hours":week("12:30","21:00"),"closed_dates":[],"mail_only":True,"note":"Giá mua qua bưu điện (郵送買取); giá tại cửa hàng 秋葉原 có thể khác"},
]
catalog = {
 "series": [{"id":"mega","name":"MEGA"},{"id":"sv","name":"SV"}],
 "items": [{"id":i,"series":s,"name":n,"retail":r,"release":d,"image":IMG+img,"jan":j,"aliases":a,"exclude":e}
           for i,s,n,r,d,j,img,a,e in ROWS],
 "shops": shops,
}
save_json(Path("web/data/pokemon/catalog.json"), catalog)
EOF
```

- [ ] **Step 8: Chạy test catalog và bộ ghép, thấy pass**

Run: `.venv/bin/python -m pytest -q crawler/tests/test_pokemon_catalog.py crawler/tests/test_pokemon_match.py --ignore-glob='* 2.py'`
Expected: tất cả PASS.

- [ ] **Step 9: Commit**

```bash
git add web/data/pokemon/catalog.json crawler/pokemon/match.py crawler/tests/test_pokemon_match.py crawler/tests/test_pokemon_catalog.py
git commit -m "feat(pokemon): catalog 21 BOX và bộ ghép sản phẩm theo JAN/tên

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Parser HTML (森森, ホムラ, ルデヤ, モバイル一番, オク)

**Files:**
- Create: `crawler/pokemon/shops/{morimori,homura,rudeya,ichiban,oku}.py`
- Create: `crawler/tests/fixtures/pokemon/{morimori,homura,rudeya,ichiban,oku}.html`, `crawler/tests/test_pokemon_shops.py`
- Modify: `crawler/pokemon/shops/__init__.py`

**Interfaces:**
- Consumes: `match_item`, `clean_jan` (Task 2); `crawler.shops.common.dedupe`; `crawler.http.get_text`; `crawler.normalize.parse_price`.
- Produces: mỗi module có `fetch(session) -> str` và `parse(raw: str, items: list[dict]) -> list[Offer]`, với `Offer.variant` là `id` của BOX.

**Fixture:** mỗi file HTML nhỏ, viết tay theo đúng cấu trúc thật đã khảo sát ngày 2026-10-03.

- [ ] **Step 1: Tạo fixture**

`crawler/tests/fixtures/pokemon/morimori.html`:

```html
<html><body><div id="category-2401010-products">
<div class="product-item"><div class="product-details"><a href="/category/2401010/product/339016">
<h5 class="product-details-name"> ポケモン ポケモンカードゲーム MEGA 拡張パック アビスアイ BOX </h5><h5>JAN:4521329462127</h5></a></div>
<div class="product-price"><div class="price-normal-number"><h5> 7,500円 </h5></div></div></div>
<div class="product-item"><div class="product-details"><a href="/category/2401010/product/2">
<h5 class="product-details-name"> ポケモン ニンジャスピナー </h5><h5>JAN:4521329432786</h5></a></div>
<div class="product-price"><div class="price-normal-number"><h5> 7,300円 </h5></div></div></div>
</div>
<div id="category-2401001-products">
<div class="product-item"><div class="product-details"><a href="/x">
<h5 class="product-details-name"> ポケモン ブラックボルト 拡張パック デラックス BOX </h5><h5>JAN:4521329427300</h5></a></div>
<div class="product-price"><div class="price-normal-number"><h5> 19,000円 </h5></div></div></div>
<div class="product-item"><div class="product-details"><a href="/y">
<h5 class="product-details-name"> ポケモン 拡張パック バトルパートナーズ BOX プロモカードなし </h5><h5>JAN:4521329362649</h5></a></div>
<div class="product-price"><div class="price-normal-number"><h5> 9,600円 </h5></div></div></div>
</div></body></html>
```

`crawler/tests/fixtures/pokemon/homura.html`:

```html
<html><body>
<div class="h-full"><div class="flex flex-col"><div class="flex flex-1 flex-col">
<a href="/products/7237"><h5 class="text-sm"> 【BOX】30th CELEBRATION </h5></a>
<div class="min-h-[20px]"><span class="text-xs text-gray-600">114521329462424</span></div>
<div class="flex flex-col"><span class="text-xs">買取金額（税込）</span><span class="text-lg font-semibold"> ¥ 26,500 </span></div>
</div></div></div>
<div class="h-full"><div class="flex flex-col"><div class="flex flex-1 flex-col">
<a href="/products/1"><h5 class="text-sm"> 【BOX】ブラックボルトDX </h5></a>
<div class="min-h-[20px]"><span class="text-xs text-gray-600">114521329427300</span></div>
<div class="flex flex-col"><span class="text-lg font-semibold"> ¥ 22,000 </span></div>
</div></div></div>
</body></html>
```

`crawler/tests/fixtures/pokemon/rudeya.html`:

```html
<html><body>
<article class="pgrid-card"><h3 class="product-card-name"><span class="product-card-cond-badge is-new">新品</span>
<a class="product-card-name-link">ポケモンカードゲーム MEGA 拡張パック 30th CELEBRATION BOX [M6a]</a></h3>
<p class="product-card-jan"><span class="product-card-jan-text">JAN: 4521329462424</span></p>
<span class="product-card-price-value">22,500<span class="unit">円</span></span></article>
<article class="pgrid-card"><h3 class="product-card-name"><span class="product-card-cond-badge is-new">新品</span>
<a class="product-card-name-link">ポケモンカードゲーム MEGA 30th CELEBRATION FUTURISTIC BOX</a></h3>
<p class="product-card-jan"><span class="product-card-jan-text">JAN: 4521329463872</span></p>
<span class="product-card-price-value">58,000<span class="unit">円</span></span></article>
<article class="pgrid-card"><h3 class="product-card-name"><span class="product-card-cond-badge is-new">新品</span>
<a class="product-card-name-link">ポケモンカードゲームMEGA 30th CELEBRATION プレミアムデッキセット エーフィ・ブラッキー</a></h3>
<p class="product-card-jan"><span class="product-card-jan-text">JAN: 4521329462189</span></p>
<span class="product-card-price-value">17,200<span class="unit">円</span></span></article>
</body></html>
```

`crawler/tests/fixtures/pokemon/ichiban.html`:

```html
<html><body>
<div class="card"><div class="card-body">
<label class="hideText" title="ポケモンカードゲーム MEGA 拡張パック 30th CELEBRATION BOX m6a"> x </label>
<label class="hideText" title=""></label>
<small class="text-muted">JAN:4521329462424</small>
<small class="my-prod-remarks"> シュリンク付き、新品未開封 </small>
<label id="NewPrice_S013463"> 25,500円 </label></div></div>
<div class="card"><div class="card-body">
<label class="hideText" title="スカーレット&amp;バイオレット 強化拡張パック ポケモンカード151 BOX sv2a"> x </label>
<small class="text-muted">JAN:4521329346038</small>
<small class="my-prod-remarks"> シュリンクなし、新品未開封 </small>
<label id="NewPrice_S2"> 30,000円 </label></div></div>
<div class="card"><div class="card-body">
<label class="hideText" title="遊戯王 ORIGINAL ARTWORK COLLECTION BOX"> x </label>
<small class="my-prod-remarks"> シュリンク付き、新品未開封 </small>
<label id="NewPrice_S3"> 7,000円 </label></div></div>
</body></html>
```

`crawler/tests/fixtures/pokemon/oku.html`:

```html
<html><body><div class="pro"><div class="wrap">
<div class="proItem"><a href="/gdetail/697.html"><div class="des"><div class="sn">JAN: 4521329462424</div>
<h4 class="tit elli2"> MEGA 拡張パック 30th CELEBRATION BOX</h4><div class="price"> ¥27,000</div></div></a></div>
<div class="proItem"><a href="/gdetail/2.html"><div class="des"><div class="sn">JAN: 4521329431512</div>
<h4 class="tit elli2">ポケモンカードゲーム MEGA インフェルノX m2 BOX</h4><div class="price"> ¥15,200</div></div></a></div>
<div class="proItem"><a href="/gdetail/3.html"><div class="des"><div class="sn">JAN: 4521329427768</div>
<h4 class="tit elli2">ポケモンカードゲーム ブラックボルト sv11b</h4><div class="price">問い合わせ</div></div></a></div>
</div></div></body></html>
```

- [ ] **Step 2: Viết test (fail)**

`crawler/tests/test_pokemon_shops.py`:

```python
import json
from pathlib import Path

import pytest

from crawler.pokemon.shops import homura, ichiban, morimori, oku, rudeya
from crawler.store import DATA_DIR

FIXTURES = Path(__file__).parent / "fixtures" / "pokemon"
ITEMS = json.loads((DATA_DIR / "pokemon" / "catalog.json").read_text(encoding="utf-8"))["items"]


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def as_dict(offers):
    return {offer.variant: offer.price for offer in offers}


def test_morimori_jan_and_skips_dx_and_no_promo():
    assert as_dict(morimori.parse(read("morimori.html"), ITEMS)) == {"mega-abyss-eye": 7500, "mega-ninja-spinner": 7300}


def test_homura_jan_from_last_13_digits_and_skips_dx():
    assert as_dict(homura.parse(read("homura.html"), ITEMS)) == {"mega-30th": 26500}


def test_rudeya_new_cards_with_jan():
    assert as_dict(rudeya.parse(read("rudeya.html"), ITEMS)) == {"mega-30th": 22500, "mega-30th-futuristic": 58000}


def test_ichiban_needs_jan_and_shrink():
    assert as_dict(ichiban.parse(read("ichiban.html"), ITEMS)) == {"mega-30th": 25500}


def test_oku_alternate_jan_and_skips_text_price():
    assert as_dict(oku.parse(read("oku.html"), ITEMS)) == {"mega-30th": 27000, "mega-inferno-x": 15200}
```

- [ ] **Step 3: Chạy, thấy fail**

Run: `.venv/bin/python -m pytest -q crawler/tests/test_pokemon_shops.py --ignore-glob='* 2.py'`
Expected: lỗi `ImportError: cannot import name 'homura' from 'crawler.pokemon.shops'`.

- [ ] **Step 4: Cài đặt 5 parser**

`crawler/pokemon/shops/morimori.py`:

```python
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

BASE = "https://www.morimori-kaitori.jp"
CATEGORIES = ["/category/2401010", "/category/2401001"]  # MEGA, SV
MAX_PAGES = 3  # mỗi danh mục; hàng mới ở trang đầu


def fetch(session) -> str:
    pages = []
    for path in CATEGORIES:
        url = BASE + path
        for _ in range(MAX_PAGES):
            html = get_text(session, url)
            pages.append(html)
            nxt = BeautifulSoup(html, "html.parser").select_one("ul.pagination li.next a")
            if not nxt:
                break
            url = urljoin(BASE, nxt["href"])
    return "\n".join(pages)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("div[id$='-products'] .product-item"):
        name = card.select_one(".product-details-name")
        price = card.select_one(".price-normal-number")
        jan = clean_jan(card.select_one(".product-details").get_text(" ") if card.select_one(".product-details") else "")
        if not name or not price:
            continue
        item = match_item(name.get_text(" ", strip=True), jan, items)
        value = parse_price(price.get_text())
        if item and value:
            offers.append(Offer(item, value))
    return dedupe(offers)
```

`crawler/pokemon/shops/homura.py`:

```python
from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

# Danh mục "シュリンク有り" (BOX còn màng co).
URL = (
    "https://kaitori-homura.com/products"
    "?q%5Bproduct_sub_category_id_eq%5D=128&q%5Bproduct_sub_category_product_category_id_eq%5D=14"
)
MAX_PAGES = 3


def fetch(session) -> str:
    return "\n".join(get_text(session, f"{URL}&page={page}") for page in range(1, MAX_PAGES + 1))


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for title in soup.select("h5"):
        card = title.find_parent(lambda tag: tag.name == "div" and tag.select_one("span.text-lg"))
        if not card:
            continue
        # Dãy số trong thẻ là JAN có thêm 2 chữ số phía trước, ví dụ 114521329462424.
        jan = clean_jan(" ".join(span.get_text() for span in card.select("span.text-xs")))
        item = match_item(" ".join(title.get_text().split()), jan, items)
        value = parse_price(card.select_one("span.text-lg").get_text())
        if item and value:
            offers.append(Offer(item, value))
    return dedupe(offers)
```

`crawler/pokemon/shops/rudeya.py`:

```python
from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

URL = "https://kaitori-rudeya.com/category/detail/114"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("article.pgrid-card"):
        badge = card.select_one(".product-card-cond-badge")
        name = card.select_one(".product-card-name-link")
        price = card.select_one(".product-card-price-value")
        jan = card.select_one(".product-card-jan-text")
        if not (badge and name and price) or badge.get_text(strip=True) != "新品":
            continue
        item = match_item(name.get_text(" ", strip=True), clean_jan(jan.get_text() if jan else ""), items)
        value = parse_price(price.get_text())
        if item and value:
            offers.append(Offer(item, value))
    return dedupe(offers)
```

`crawler/pokemon/shops/ichiban.py`:

```python
import re

from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

URL = "https://www.mobile-ichiban.com/Prod/3/"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for price in soup.select('label[id^="NewPrice_"]'):
        card = price.find_parent("div", class_="card")
        if not card:
            continue
        labels = card.select("label.hideText")
        name = labels[0].get("title", "") if labels else ""
        remark = card.select_one(".my-prod-remarks")
        jan_text = " ".join(t for t in card.find_all(string=re.compile("JAN")))
        # Ghi chú (ví dụ "シュリンクなし") nằm ngoài tên nên ghép vào để bộ ghép loại được.
        text = f"{name} {remark.get_text(' ', strip=True) if remark else ''}"
        item = match_item(text, clean_jan(jan_text), items)
        value = parse_price(price.get_text())
        if item and value and clean_jan(jan_text):
            offers.append(Offer(item, value))
    return dedupe(offers)
```

`crawler/pokemon/shops/oku.py`:

```python
from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

# Danh mục "シュリンクあり"; hàng mới ở các trang đầu.
URL = "https://kaitori-oku.jp/category.html?cat1=340&cat2=363&cat3=367"
MAX_PAGES = 3


def fetch(session) -> str:
    return "\n".join(get_text(session, f"{URL}&page={page}") for page in range(1, MAX_PAGES + 1))


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("div.proItem"):
        name = card.select_one("h4.tit")
        price = card.select_one(".price")
        jan = card.select_one(".sn")
        if not name or not price:
            continue
        value = parse_price(price.get_text())  # "問い合わせ" → None
        item = match_item(name.get_text(" ", strip=True), clean_jan(jan.get_text() if jan else ""), items)
        if item and value:
            offers.append(Offer(item, value))
    return dedupe(offers)
```

`crawler/pokemon/shops/__init__.py`: Task 4 sẽ thêm các tiệm còn lại.

```python
from crawler.pokemon.shops import homura, ichiban, morimori, oku, rudeya

SHOPS = {
    "morimori": morimori,
    "homura": homura,
    "rudeya": rudeya,
    "ichiban": ichiban,
    "oku": oku,
}
```

- [ ] **Step 5: Chạy, thấy pass**

Run: `.venv/bin/python -m pytest -q crawler/tests/test_pokemon_shops.py --ignore-glob='* 2.py'`
Expected: 5 PASS.

- [ ] **Step 6: Thử trên trang thật** (chỉ để kiểm tra, không commit dữ liệu)

```bash
.venv/bin/python - <<'EOF'
import json, time
from crawler.http import new_session
from crawler.pokemon.shops import SHOPS
items = json.load(open("web/data/pokemon/catalog.json"))["items"]
s = new_session()
for sid, mod in SHOPS.items():
    d = {o.variant: o.price for o in mod.parse(mod.fetch(s), items)}
    print(sid, len(d), sorted(d.items())[:4]); time.sleep(1)
EOF
```

Expected: mỗi tiệm từ 10 BOX trở lên (riêng モバイル一番 khoảng 5–8), giá trong khoảng 5,000–60,000. Tiệm nào ra 0 thì mở trang thật xem lại selector trước khi đi tiếp.

- [ ] **Step 7: Commit**

```bash
git add crawler/pokemon/shops/ crawler/tests/fixtures/pokemon/ crawler/tests/test_pokemon_shops.py
git commit -m "feat(pokemon): parser 森森, ホムラ, ルデヤ, モバイル一番, オク

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Parser API (一丁目, シンソク, ラントゥ)

**Files:**
- Create: `crawler/pokemon/shops/{ichome,shinsoku,runto}.py`, `crawler/tests/fixtures/pokemon/{ichome,shinsoku,runto}.json`
- Modify: `crawler/pokemon/shops/__init__.py`, `crawler/tests/test_pokemon_shops.py`

**Interfaces:**
- Như Task 3. Riêng `fetch` của シンソク và ラントゥ trả về chuỗi JSON do mình tự ghép từ nhiều request: `{"pages": [...]}` với シンソク, `{"products": [...], "variations": [...]}` với ラントゥ.

- [ ] **Step 1: Tạo fixture**

`crawler/tests/fixtures/pokemon/ichome.json`:

```json
{"code": 200, "msg": "success", "data": {"totalElements": 3, "size": 100, "content": [
 {"title": "【MEGA】 30th CELEBRATION BOX", "jan": "4521329462424",
  "goodsKbDetails": [{"kbDetailName": "シュリンク有", "kbDetailPrice": 26000}, {"kbDetailName": "シュリンクなし未開封", "kbDetailPrice": 22000}]},
 {"title": "【MEGA】 メガブレイブ BOX", "jan": "‎4521329431161",
  "goodsKbDetails": [{"kbDetailName": " シュリンク有", "kbDetailPrice": 7800}]},
 {"title": "【MEGA】 30th CELEBRATION プレミアムデッキセット エーフィ・ブラッキー", "jan": "4521329462189",
  "goodsKbDetails": [{"kbDetailName": " 新品未開封", "kbDetailPrice": 17500}]}
]}}
```

`crawler/tests/fixtures/pokemon/shinsoku.json`:

```json
{"pages": [{"ok": true, "data": {"has_more": false, "items": [
 {"name": "拡張パック「30th CELEBRATION」(M6a)", "type": "BOX", "postal_purchase_price_s": 26300},
 {"name": "拡張パックデラックス「ブラックボルト」(SV11B)", "type": "BOX", "postal_purchase_price_s": 21800},
 {"name": "拡張パック「ブラックボルト」(SV11B)", "type": "BOX", "postal_purchase_price_s": 17600},
 {"name": "拡張パック「ドラゴンストーム」(SM6a)", "type": "BOX", "postal_purchase_price_s": 120000},
 {"name": "強化拡張パック「ポケモンカード151」(SV2a)", "type": "BOX", "postal_purchase_price_s": null}
]}}]}
```

`crawler/tests/fixtures/pokemon/runto.json`:

```json
{"products": [
 {"id": 99427, "type": "variable", "name": "ポケモンカードゲーム MEGA 拡張パック「30th CELEBRATION」", "prices": {"price": "24000"},
  "variations": [{"id": 99581, "attributes": [{"name": "シュリンク", "value": "ari"}]}, {"id": 99428, "attributes": [{"name": "シュリンク", "value": "nashi"}]}]},
 {"id": 99435, "type": "simple", "name": "ポケモンカードゲーム MEGA 30th CELEBRATION FUTURISTIC BOX", "prices": {"price": "58000"}, "variations": []},
 {"id": 44414, "type": "variable", "name": "ポケモンカードゲーム スカーレット&#038;バイオレット拡張パック 「ロケット団の栄光」", "prices": {"price": "15000"},
  "variations": [{"id": 44415, "attributes": [{"name": "シュリンク", "value": "ari"}]}]}
],
 "variations": [
 {"id": 99581, "parent": 99427, "prices": {"price": "26800"}},
 {"id": 44415, "parent": 44414, "prices": {"price": "18700"}}
]}
```

- [ ] **Step 2: Thêm test (fail)** vào cuối `crawler/tests/test_pokemon_shops.py`

```python
from crawler.pokemon.shops import ichome, runto, shinsoku  # noqa: E402


def test_ichome_takes_shrink_price_and_cleans_jan():
    assert as_dict(ichome.parse(read("ichome.json"), ITEMS)) == {"mega-30th": 26000, "mega-mega-brave": 7800}


def test_ichome_rejects_truncated_list():
    raw = json.dumps({"code": 200, "data": {"totalElements": 150, "size": 100, "content": []}})
    with pytest.raises(ValueError):
        ichome.parse(raw, ITEMS)


def test_shinsoku_matches_by_name_skips_dx_and_missing_price():
    assert as_dict(shinsoku.parse(read("shinsoku.json"), ITEMS)) == {"mega-30th": 26300, "sv-black-bolt": 17600}


def test_runto_uses_shrink_variation_or_simple_price():
    assert as_dict(runto.parse(read("runto.json"), ITEMS)) == {
        "mega-30th": 26800, "mega-30th-futuristic": 58000, "sv-rocket-gang": 18700,
    }
```

- [ ] **Step 3: Chạy, thấy fail**

Run: `.venv/bin/python -m pytest -q crawler/tests/test_pokemon_shops.py --ignore-glob='* 2.py'`
Expected: lỗi `ImportError: cannot import name 'ichome'`.

- [ ] **Step 4: Cài đặt**

`crawler/pokemon/shops/ichome.py`:

```python
import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

URL = (
    "https://www.1-chome.com/api/goods/listPage?accCode=&page=1&size=100&keyword="
    "&isImpo=false&isCampaign=false&cateCode=IIzyMdayU5wp7T4G&kbNames=&cateName="
)
SHRINK = "シュリンク有"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    data = json.loads(raw)
    if data.get("code") != 200:
        raise ValueError(f"API trả về code {data.get('code')}: {data.get('msg')}")
    page = data["data"]
    if page["totalElements"] > page["size"]:
        raise ValueError(f"API có {page['totalElements']} sản phẩm, nhiều hơn 1 trang ({page['size']})")
    offers = []
    for product in page["content"]:
        price = next(
            (d["kbDetailPrice"] for d in product.get("goodsKbDetails") or [] if (d.get("kbDetailName") or "").strip() == SHRINK),
            None,
        )
        item = match_item(product.get("title") or "", clean_jan(product.get("jan")), items)
        if item and price:
            offers.append(Offer(item, price))
    return dedupe(offers)
```

`crawler/pokemon/shops/shinsoku.py`:

```python
import json
from urllib.parse import quote

from crawler.http import get_text
from crawler.models import Offer
from crawler.pokemon.match import match_item
from crawler.shops.common import dedupe

# Giá mua qua bưu điện (郵送買取), hạng S. Mỗi trang tối đa 100.
URL = "https://shinsoku-tcg.com/api/items?postal_only=true&sort=price_desc&type=BOX&brand=" + quote("ポケモン") + "&limit=100&page={page}"
MAX_PAGES = 5


def fetch(session) -> str:
    pages = []
    for page in range(MAX_PAGES):
        data = json.loads(get_text(session, URL.format(page=page)))
        pages.append(data)
        if not data.get("ok") or not data["data"]["has_more"]:
            break
    return json.dumps({"pages": pages}, ensure_ascii=False)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    offers = []
    for page in json.loads(raw)["pages"]:
        if not page.get("ok"):
            raise ValueError(f"API lỗi: {page.get('error')}")
        for product in page["data"]["items"]:
            item = match_item(product.get("name") or "", None, items)
            price = product.get("postal_purchase_price_s")
            if item and price:
                offers.append(Offer(item, price))
    return dedupe(offers)
```

`crawler/pokemon/shops/runto.py`:

```python
import html
import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import match_item
from crawler.shops.common import dedupe

API = "https://runto666.com/wp-json/wc/store/v1/products"
PRODUCTS = API + "?category=108&per_page=100"  # 108 = ポケモンカード
SHRINK = "ari"  # biến thể "シュリンク有"


def shrink_variation(product: dict) -> int | None:
    for variation in product.get("variations") or []:
        if any(a.get("value") == SHRINK for a in variation.get("attributes") or []):
            return variation["id"]
    return None


def fetch(session) -> str:
    products = json.loads(get_text(session, PRODUCTS))
    ids = [vid for vid in (shrink_variation(p) for p in products if p["type"] == "variable") if vid]
    variations = json.loads(get_text(session, f"{API}?type=variation&per_page=100&include={','.join(map(str, ids))}")) if ids else []
    return json.dumps({"products": products, "variations": variations}, ensure_ascii=False)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    data = json.loads(raw)
    variation_price = {v["id"]: parse_price(v["prices"]["price"]) for v in data["variations"]}
    offers = []
    for product in data["products"]:
        if product["type"] == "variable":
            price = variation_price.get(shrink_variation(product))
        elif product["type"] == "simple":
            price = parse_price(product["prices"]["price"])
        else:
            continue
        item = match_item(html.unescape(product["name"]), None, items)
        if item and price:
            offers.append(Offer(item, price))
    return dedupe(offers)
```

`crawler/pokemon/shops/__init__.py`: thay bằng:

```python
from crawler.pokemon.shops import homura, ichiban, ichome, morimori, oku, rudeya, runto, shinsoku

SHOPS = {
    "morimori": morimori,
    "homura": homura,
    "rudeya": rudeya,
    "ichiban": ichiban,
    "oku": oku,
    "runto": runto,
    "ichome": ichome,
    "shinsoku": shinsoku,
}
```

- [ ] **Step 5: Thêm test "mọi tiệm trong catalog có parser"** vào `crawler/tests/test_pokemon_catalog.py`

```python
def test_every_pokemon_shop_has_a_parser():
    from crawler.pokemon.shops import SHOPS

    assert sorted(s["id"] for s in load()["shops"]) == sorted(SHOPS)
```

- [ ] **Step 6: Chạy cả bộ test, thấy pass**

Run: `.venv/bin/python -m pytest -q --ignore-glob='* 2.py'`
Expected: toàn bộ PASS.

- [ ] **Step 7: Thử trên trang thật**

Chạy lại script ở Task 3, Step 6. Expected: 一丁目 và シンソク mỗi tiệm từ 15 BOX trở lên, ラントゥ từ 10 trở lên.

- [ ] **Step 8: Commit**

```bash
git add crawler/pokemon/shops/ crawler/tests/fixtures/pokemon/ crawler/tests/test_pokemon_shops.py crawler/tests/test_pokemon_catalog.py
git commit -m "feat(pokemon): parser API 一丁目, シンソク (mail only), ラントゥ

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Workflow và lần crawl đầu

**Files:**
- Modify: `.github/workflows/crawl.yml`
- Create (dữ liệu): `web/data/pokemon/latest.json`, `daily.json`, `history/2026-10.json`

- [ ] **Step 1: Sửa bước crawl trong `crawl.yml`**

Thay khối

```yaml
      - name: Crawl giá
        run: python -m crawler.run
```

bằng

```yaml
      - name: Crawl giá iPhone
        run: python -m crawler.run --category iphone
      - name: Crawl giá Pokémon BOX
        if: always()
        run: python -m crawler.run --category pokemon
```

Bước commit hiện có đã có `if: always()` và `git add web/data`, nên tự gồm cả `web/data/pokemon/`.

- [ ] **Step 2: Crawl thật lần đầu**

Run: `.venv/bin/python -m crawler.run --category pokemon`
Expected: 8 dòng `[pokemon/<tiệm>] OK n giá`, và tạo ra `web/data/pokemon/latest.json`, `daily.json`, `history/2026-10.json`.

- [ ] **Step 3: Kiểm tra iPhone vẫn chạy như cũ**

Run: `.venv/bin/python -m crawler.run`
Expected: 14 dòng `[iphone/<tiệm>] …`, exit 0.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/crawl.yml web/data/pokemon/latest.json web/data/pokemon/daily.json web/data/pokemon/history/
git commit -m "feat(pokemon): workflow crawl thêm danh mục Pokémon, dữ liệu lần đầu

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Không `git add` dữ liệu iPhone vừa crawl ở Step 3. Nếu đã lỡ ghi thay đổi, khôi phục bằng `git checkout -- web/data/latest.json web/data/daily.json web/data/history/`.

---

### Task 6: Tách phần dùng chung của bảng (`table.js`)

**Files:**
- Create: `web/js/table.js`
- Modify: `web/js/app.js`

**Interfaces:**
- Produces (`web/js/table.js`):
  - `shopHeader(shop, shopState, now) -> string`: thẻ `<th>`, giữ nguyên HTML hiện tại.
  - `diffClass(n) -> "pos" | "neg"`
  - `renderRankModal(modal, { titleHtml, refLabel, refPrice, rows, shopId })`: điền `#modal-body` rồi `showModal()`; không làm gì nếu `shopId` không có trong `rows`.
  - `bindRankModal(table, modal, onOpen)`: gọi `onOpen(cell)` khi click hoặc nhấn Enter/Space vào `td.clickable`; đóng modal khi bấm ✕ hoặc nền ngoài.
- `rows` là kết quả của `rankOffers(...)` trong `logic.js`.

- [ ] **Step 1: Tạo `web/js/table.js`** (chuyển nguyên code từ `app.js`, chỉ tham số hoá phần đầu modal)

```js
// Phần bảng giá dùng chung cho các trang (iPhone, Pokémon…): tiêu đề cột cửa hàng và cửa sổ xếp hạng.
import { esc, formatDiff, formatShortTime, formatTime, formatYen, isStale, openStatus } from "./logic.js";

export function diffClass(n) {
  return n >= 0 ? "pos" : "neg";
}

export function shopHeader(shop, shopState, now) {
  const status = openStatus(shop, now);
  const stale = shopState && isStale(shopState.last_success_at, now);
  const icon = shop.mail_only ? "📦" : status.open ? "🟢" : "🔴";
  const label = shop.mail_only ? "Mail only" : status.label;
  const statusClass = shop.mail_only ? "mail" : status.open ? "open" : "closed";
  const tip = [shop.mail_only ? "Không xếp hạng, không tính vào Diff" : status.text, shop.note].filter(Boolean).join(" · ");
  return `<th class="shop" title="${esc(tip)}">
    <a href="${esc(shop.url)}" target="_blank" rel="noopener">${esc(shop.name)} ↗</a>
    <span class="time long">${formatTime(shopState?.display_at)}</span>
    <span class="status long ${statusClass}">${icon} ${esc(label)}</span>
    <span class="short">${icon} ${formatShortTime(shopState?.display_at, now)}</span>
    ${stale ? '<span class="stale">⚠ dữ liệu cũ</span>' : ""}
  </th>`;
}

// rows: kết quả của rankOffers(); titleHtml đã được escape bởi trang gọi.
export function renderRankModal(modal, { titleHtml, refLabel, refPrice, rows, shopId }) {
  const picked = rows.find((r) => r.shop.id === shopId);
  if (!picked) return;
  const rankedCount = rows.filter((r) => r.rank).length;
  const rankText = picked.rank
    ? `Hạng ${picked.rank} / ${rankedCount}`
    : picked.shop.mail_only ? "📦 Mail only, không xếp hạng" : "Dữ liệu cũ hoặc lỗi, không xếp hạng";
  const list = rows
    .map((r) => {
      const cls = [r.shop.id === shopId ? "picked" : "", r.usable ? "" : "muted"].join(" ").trim();
      return `<tr class="${cls}">
        <td class="rank">${r.rank ?? (r.usable && r.shop.mail_only ? "📦" : "—")}</td>
        <td class="name"><a href="${esc(r.shop.url)}" target="_blank" rel="noopener">${esc(r.shop.name)} ↗</a></td>
        <td>¥${formatYen(r.price)}</td>
        <td class="${r.usable ? diffClass(r.diff) : ""}">${formatDiff(r.diff)}</td>
      </tr>`;
    })
    .join("");
  modal.querySelector("#modal-body").innerHTML = `
    <div class="modal-head">
      <h2>${titleHtml}</h2>
      <span class="apple">${esc(refLabel)} ¥${formatYen(refPrice)}</span>
      <button type="button" class="close" data-close aria-label="Đóng">✕</button>
    </div>
    <div class="modal-summary">
      <p class="shop-price">${esc(picked.shop.name)} trả <strong>¥${formatYen(picked.price)}</strong></p>
      <p><span class="profit ${diffClass(picked.diff)}">Lãi: ${formatDiff(picked.diff)}</span><span class="rank-badge">${rankText}</span></p>
    </div>
    <table class="rank-table">
      <thead><tr><th>Hạng</th><th>Cửa hàng</th><th>Giá</th><th>Diff</th></tr></thead>
      <tbody>${list}</tbody>
    </table>`;
  modal.showModal();
}

export function bindRankModal(table, modal, onOpen) {
  const open = (event) => {
    const cell = event.target.closest("td.clickable");
    if (cell) onOpen(cell);
  };
  table.addEventListener("click", open);
  table.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      open(event);
    }
  });
  // Đóng khi bấm nút ✕ hoặc bấm ra ngoài khung modal (Esc do <dialog> tự xử lý).
  modal.addEventListener("click", (event) => {
    if (event.target === modal || event.target.closest("[data-close]")) modal.close();
  });
}
```

- [ ] **Step 2: Sửa `web/js/app.js` để dùng `table.js`**

1. Đổi khối import:

```js
import { DATA_BASE } from "./config.js";
import {
  bestOffer, esc, filterVariants, formatDiff, formatYen, groupLabel, isUsable, jstDate, modelColors,
  pickFilters, rankOffers, rankedShopIds,
} from "./logic.js";
import { renderCharts } from "./charts.js";
import { bindRankModal, diffClass, renderRankModal, shopHeader } from "./table.js";
```

2. Xoá các hàm `shopHeader` (dòng 127–141), `diffClass` (189–191) và `setupModal` (234–251) trong `app.js`.

3. Thay `openOfferModal` bằng:

```js
function openOfferModal(variantId, shopId) {
  const { catalog, latest } = data;
  const variant = catalog.variants.find((v) => v.id === variantId);
  const color = catalog.colors[variant.color];
  renderRankModal($("#offer-modal"), {
    titleHtml: `<span class="dot" style="background:${esc(color.hex)}" title="${esc(color.vi)}" aria-label="${esc(color.vi)}"></span>${esc(variant.capacity)}`,
    refLabel: "Apple",
    refPrice: variant.apple_price,
    rows: rankOffers(variantId, latest, catalog.shops, variant.apple_price, new Date()),
    shopId,
  });
}
```

4. Trong `init()`, thay `setupModal();` bằng:

```js
  bindRankModal($("#price-table"), $("#offer-modal"), (cell) => openOfferModal(cell.dataset.variant, cell.dataset.shop));
```

- [ ] **Step 3: Chạy test JS**

Run: `npm test 2>&1 | grep -E "(pass|fail) [0-9]+"`
Expected: `pass 38`, `fail 0`.

- [ ] **Step 4: Kiểm tra trang iPhone trên trình duyệt** (giao diện phải không đổi)

```bash
(cd web && python3 -m http.server 8765 >/dev/null 2>&1 &); sleep 1
SP=/private/tmp/claude-501/-Users-nguyenvd-Documents-tool-iphone-checker-web/ebb6effc-21fa-43d9-8b1b-28591e55145d/scratchpad
$SP/.venv/bin/python - <<'EOF'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://localhost:8765/iphone-18/"); pg.wait_for_timeout(1500)
    print("rows", pg.locator("#price-table tbody tr").count(), "shops", pg.locator("th.shop").count())
    pg.locator("td.clickable").first.click(); pg.wait_for_timeout(300)
    print(pg.locator("#modal-body").inner_text()[:120]); print("errors", errs); b.close()
EOF
pkill -f "http.server 8765"
```

Expected: `rows 26`, `shops 14`, modal có "trả ¥" và "Hạng", `errors []`.

- [ ] **Step 5: Commit**

```bash
git add web/js/table.js web/js/app.js
git commit -m "refactor(web): tách tiêu đề cột cửa hàng và cửa sổ xếp hạng ra table.js để dùng chung

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Logic của trang Pokémon (hàm thuần)

**Files:**
- Modify: `web/js/logic.js`
- Create: `tests/web/pokemon.test.js`

**Interfaces:**
- Consumes: `bestOffer(variantId, latest, shopIds, now)`, `rankedShopIds(shops)` (đã có).
- Produces:
  - `itemDiff(item, latest, shopIds, now) -> number | null`: giá cao nhất (bỏ tiệm lỗi/dữ liệu cũ, chỉ trong `shopIds`) trừ `item.retail`.
  - `filterItems(items, { series }) -> items`
  - `sortItems(items, sort, latest, shopIds, now) -> items` (mảng mới). `"newest"`: `release` giảm dần, cùng ngày giữ thứ tự gốc. `"diff"`: Diff giảm dần, `null` xếp cuối, bằng nhau giữ thứ tự gốc.
  - `pickPokemonFilters(params, saved, seriesIds) -> { series, sort }`: giá trị không hợp lệ thì về `"all"` / `"newest"`; URL có `series` hoặc `sort` thì chỉ dùng URL.
  - `bestItemDiff(catalog, latest, now) -> { item, diff } | null`

- [ ] **Step 1: Viết test (fail)** — `tests/web/pokemon.test.js`

```js
import assert from "node:assert/strict";
import { test } from "node:test";
import { bestItemDiff, filterItems, itemDiff, pickPokemonFilters, sortItems } from "../../web/js/logic.js";

const NOW = new Date("2026-10-03T12:00:00+09:00");
const FRESH = "2026-10-03T11:30:00+09:00";
const st = (prices, extra = {}) => ({ last_success_at: FRESH, error: null, prices, ...extra });
const ITEMS = [
  { id: "a", series: "mega", retail: 7200, release: "2026-09-16" },
  { id: "b", series: "mega", retail: 27500, release: "2026-09-16" },
  { id: "c", series: "sv", retail: 5400, release: "2023-06-16" },
  { id: "d", series: "sv", retail: 5800, release: "2025-06-06" },
];
const LATEST = { shops: {
  x: st({ a: 26000, b: 58000, c: 32000 }),
  y: st({ a: 27000 }, { error: "HTTPError: 403" }),
  m: st({ c: 40000 }),
} };
const SHOP_IDS = ["x", "y"]; // "m" là mail only nên không có trong danh sách

test("itemDiff ignores erroring and mail-only shops", () => {
  assert.equal(itemDiff(ITEMS[0], LATEST, SHOP_IDS, NOW), 26000 - 7200);
  assert.equal(itemDiff(ITEMS[2], LATEST, SHOP_IDS, NOW), 32000 - 5400);
  assert.equal(itemDiff(ITEMS[3], LATEST, SHOP_IDS, NOW), null);
});

test("filterItems by series", () => {
  assert.deepEqual(filterItems(ITEMS, { series: "sv" }).map((i) => i.id), ["c", "d"]);
  assert.deepEqual(filterItems(ITEMS, { series: "all" }).map((i) => i.id), ["a", "b", "c", "d"]);
});

test("sortItems newest keeps catalog order on same day", () => {
  assert.deepEqual(sortItems(ITEMS, "newest", LATEST, SHOP_IDS, NOW).map((i) => i.id), ["a", "b", "d", "c"]);
});

test("sortItems diff puts items without price last", () => {
  assert.deepEqual(sortItems(ITEMS, "diff", LATEST, SHOP_IDS, NOW).map((i) => i.id), ["b", "c", "a", "d"]);
});

test("pickPokemonFilters prefers URL and validates", () => {
  const ids = ["mega", "sv"];
  assert.deepEqual(pickPokemonFilters(new URLSearchParams("series=sv"), { sort: "diff" }, ids), { series: "sv", sort: "newest" });
  assert.deepEqual(pickPokemonFilters(new URLSearchParams(""), { series: "mega", sort: "diff" }, ids), { series: "mega", sort: "diff" });
  assert.deepEqual(pickPokemonFilters(new URLSearchParams("series=xx&sort=yy"), {}, ids), { series: "all", sort: "newest" });
});

test("bestItemDiff for the home card", () => {
  const catalog = { items: ITEMS, shops: [{ id: "x" }, { id: "y" }, { id: "m", mail_only: true }] };
  assert.deepEqual(bestItemDiff(catalog, LATEST, NOW), { item: ITEMS[1], diff: 30500 });
  assert.equal(bestItemDiff(catalog, { shops: {} }, NOW), null);
});
```

- [ ] **Step 2: Chạy, thấy fail**

Run: `node --test tests/web/pokemon.test.js 2>&1 | grep -E "(pass|fail) [0-9]+"`
Expected: `fail 1` (lỗi import, vì hàm chưa tồn tại).

- [ ] **Step 3: Cài đặt** — thêm vào cuối `web/js/logic.js`

```js
// ---- Pokémon BOX ----

export function itemDiff(item, latest, shopIds, now) {
  const best = bestOffer(item.id, latest, shopIds, now);
  return best ? best.price - item.retail : null;
}

export function filterItems(items, { series = "all" } = {}) {
  return items.filter((item) => series === "all" || item.series === series);
}

export function sortItems(items, sort, latest, shopIds, now) {
  const indexed = items.map((item, index) => ({ item, index, diff: itemDiff(item, latest, shopIds, now) }));
  const byDiff = (a, b) => (a.diff === null) - (b.diff === null) || (b.diff ?? 0) - (a.diff ?? 0) || a.index - b.index;
  const byNewest = (a, b) => b.item.release.localeCompare(a.item.release) || a.index - b.index;
  return indexed.sort(sort === "diff" ? byDiff : byNewest).map((x) => x.item);
}

const SORTS = ["newest", "diff"];

export function pickPokemonFilters(params, saved, seriesIds) {
  const fromUrl = params.has("series") || params.has("sort");
  const get = (key) => (fromUrl ? params.get(key) : saved?.[key] ?? null);
  const series = get("series");
  const sort = get("sort");
  return {
    series: seriesIds.includes(series) ? series : "all",
    sort: SORTS.includes(sort) ? sort : "newest",
  };
}

export function bestItemDiff(catalog, latest, now) {
  const shopIds = rankedShopIds(catalog.shops);
  let best = null;
  for (const item of catalog.items) {
    const diff = itemDiff(item, latest, shopIds, now);
    if (diff !== null && (best === null || diff > best.diff)) best = { item, diff };
  }
  return best;
}
```

- [ ] **Step 4: Chạy, thấy pass**

Run: `npm test 2>&1 | grep -E "(pass|fail) [0-9]+"`
Expected: `pass 44`, `fail 0`.

- [ ] **Step 5: Commit**

```bash
git add web/js/logic.js tests/web/pokemon.test.js
git commit -m "feat(web): hàm lọc, sắp xếp, Diff cho BOX Pokémon

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Trang `/pokemon-card/`

**Files:**
- Modify: `web/pokemon-card/index.html` (thay toàn bộ), `web/style.css` (thêm cuối file)
- Create: `web/js/pokemon.js`

**Interfaces:**
- Consumes:
  - `table.js`: `shopHeader`, `diffClass`, `renderRankModal`, `bindRankModal` (Task 6)
  - `logic.js`: `itemDiff`, `filterItems`, `sortItems`, `pickPokemonFilters`, `rankedShopIds`, `bestOffer`, `rankOffers`, `isUsable`, `formatYen`, `formatDiff`, `esc` (Task 7 và đã có)
  - `config.js`: `DATA_BASE`

- [ ] **Step 1: Thay `web/pokemon-card/index.html`**

```html
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Giá Kaitori BOX Pokémon Card</title>
  <meta name="description" content="So sánh giá thu mua BOX Pokémon Card chưa bóc (còn màng co) ở các cửa hàng kaitori tại Tokyo, cập nhật tự động.">
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <nav class="site-nav">
    <a class="brand" href="../">Kaitori Check</a>
    <a href="../iphone-18/">iPhone 18</a>
    <a href="../pokemon-card/" aria-current="page">Pokémon Card</a>
  </nav>

  <header class="top">
    <h1>Giá thu mua BOX Pokémon Card</h1>
    <p class="sub">So sánh giá kaitori ở Tokyo · BOX chưa bóc, còn màng co (シュリンク付)</p>
  </header>

  <main>
    <p id="error" class="error" hidden></p>
    <section class="filters">
      <div id="series-chips" class="chips"></div>
      <div id="sort-chips" class="chips"></div>
    </section>
    <div class="table-wrap"><table id="price-table" class="pk-table"></table></div>
    <p class="legend">Retail = giá gốc (定価) · Diff = giá cao nhất − giá gốc · Ô xanh = cửa hàng trả cao nhất · — = không thu mua · 📦 = chỉ mua qua bưu điện, không tính vào Diff</p>
  </main>

  <dialog id="offer-modal" class="modal"><div id="modal-body"></div></dialog>

  <footer>
    <p>Giá tự động cập nhật 30 phút/lần từ 10:00 đến 20:00 (giờ Nhật) và chỉ để tham khảo. Hãy xác nhận trên trang của cửa hàng trước khi bán.</p>
    <p class="credits">Ảnh sản phẩm © Pokémon / Nintendo / Creatures / GAME FREAK, nguồn: <a href="https://www.pokemon-card.com/products/" target="_blank" rel="noopener">pokemon-card.com</a>. Trang này không liên kết với các công ty trên.</p>
  </footer>

  <script type="module" src="../js/pokemon.js"></script>
</body>
</html>
```

- [ ] **Step 2: Tạo `web/js/pokemon.js`**

```js
import { DATA_BASE } from "./config.js";
import {
  bestOffer, esc, filterItems, formatDiff, formatYen, isUsable, pickPokemonFilters, rankOffers, rankedShopIds, sortItems,
} from "./logic.js";
import { bindRankModal, diffClass, renderRankModal, shopHeader } from "./table.js";

const STORAGE_KEY = "pokemon-filters";
const state = { series: "all", sort: "newest" };
let data = null;
const $ = (selector) => document.querySelector(selector);

async function loadJson(name) {
  const res = await fetch(`${DATA_BASE}pokemon/${name}?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return res.json();
}

function readState() {
  let saved = {};
  try {
    saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    saved = {};
  }
  Object.assign(state, pickPokemonFilters(new URLSearchParams(location.search), saved, data.catalog.series.map((s) => s.id)));
}

function saveState() {
  const url = new URLSearchParams();
  if (state.series !== "all") url.set("series", state.series);
  if (state.sort !== "newest") url.set("sort", state.sort);
  const query = url.toString();
  history.replaceState(null, "", query ? `?${query}` : location.pathname);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // trình duyệt chặn localStorage: bộ lọc vẫn nằm trong URL
  }
}

function renderChips(el, options, current, onPick) {
  el.innerHTML = options
    .map((o) => `<button type="button" class="chip${o.value === current ? " on" : ""}" data-value="${esc(o.value)}">${esc(o.label)}</button>`)
    .join("");
  el.onclick = (event) => {
    const button = event.target.closest("button[data-value]");
    if (button) onPick(button.dataset.value);
  };
}

function renderFilters() {
  const series = [{ value: "all", label: "All" }, ...data.catalog.series.map((s) => ({ value: s.id, label: s.name }))];
  renderChips($("#series-chips"), series, state.series, (v) => { state.series = v; update(); });
  const sorts = [{ value: "newest", label: "Newest" }, { value: "diff", label: "Top Diff" }];
  renderChips($("#sort-chips"), sorts, state.sort, (v) => { state.sort = v; update(); });
}

function itemRow(item, shops, shopIds, latest, now) {
  const best = bestOffer(item.id, latest, shopIds, now);
  const diff = best ? best.price - item.retail : null;
  const cells = shops
    .map((s) => {
      const price = latest.shops?.[s.id]?.prices?.[item.id];
      const usable = isUsable(latest.shops?.[s.id], now);
      const cls = !usable ? "muted" : best && price === best.price && !s.mail_only ? "best" : "";
      if (price == null) return `<td class="${cls}">—</td>`;
      return `<td class="${cls} clickable" data-item="${esc(item.id)}" data-shop="${esc(s.id)}" tabindex="0">${formatYen(price)}</td>`;
    })
    .join("");
  return `<tr>
    <td class="s1"><span class="box"><img src="${esc(item.image)}" alt="${esc(item.name)}" width="40" height="40" loading="lazy" onerror="this.remove()"><span class="box-name">${esc(item.name)}</span></span></td>
    <td class="s2">${formatYen(item.retail)}</td>
    <td class="s3 ${diff == null ? "" : diffClass(diff)}">${formatDiff(diff)}</td>${cells}
  </tr>`;
}

function renderTable() {
  const { catalog, latest } = data;
  const now = new Date();
  const shops = catalog.shops;
  const shopIds = rankedShopIds(shops);
  const columns = 3 + shops.length;
  const head = `<thead><tr><th class="s1">BOX</th><th class="s2">Retail</th><th class="s3">Diff</th>${shops
    .map((s) => shopHeader(s, latest.shops?.[s.id], now))
    .join("")}</tr></thead>`;
  const items = sortItems(filterItems(catalog.items, state), state.sort, latest, shopIds, now);
  let body;
  if (state.sort === "diff") {
    body = items.map((item) => itemRow(item, shops, shopIds, latest, now)).join("");
  } else {
    body = catalog.series
      .map((s) => {
        const rows = items.filter((item) => item.series === s.id);
        if (!rows.length) return "";
        const header = `<tr class="group"><td colspan="${columns}"><span>${esc(s.name)}</span></td></tr>`;
        return header + rows.map((item) => itemRow(item, shops, shopIds, latest, now)).join("");
      })
      .join("");
  }
  const empty = `<tr><td colspan="${columns}" class="empty">Không có kết quả phù hợp</td></tr>`;
  $("#price-table").innerHTML = `${head}<tbody>${body || empty}</tbody>`;
}

function openOfferModal(itemId, shopId) {
  const { catalog, latest } = data;
  const item = catalog.items.find((i) => i.id === itemId);
  renderRankModal($("#offer-modal"), {
    titleHtml: esc(item.name),
    refLabel: "Retail",
    refPrice: item.retail,
    rows: rankOffers(itemId, latest, catalog.shops, item.retail, new Date()),
    shopId,
  });
}

function update() {
  saveState();
  renderFilters();
  renderTable();
}

async function init() {
  try {
    const [catalog, latest] = await Promise.all(["catalog.json", "latest.json"].map(loadJson));
    data = { catalog, latest };
  } catch (err) {
    $("#error").hidden = false;
    $("#error").textContent = `Không tải được dữ liệu (${err.message}). Hãy thử tải lại trang.`;
    return;
  }
  readState();
  bindRankModal($("#price-table"), $("#offer-modal"), (cell) => openOfferModal(cell.dataset.item, cell.dataset.shop));
  update();
  // Cập nhật lại trạng thái mở cửa và nhãn "dữ liệu cũ" mỗi phút mà không cần tải lại trang.
  setInterval(renderTable, 60 * 1000);
}

init();
```

- [ ] **Step 3: Thêm style vào cuối `web/style.css`**

```css
/* Bảng BOX Pokémon: cột đầu rộng hơn để có ảnh và tên */
.pk-table .s1 { min-width: 190px; width: 190px; }
.pk-table .s2 { left: 190px; min-width: 70px; width: 70px; }
.pk-table .s3 { left: 260px; min-width: 80px; width: 80px; }
.pk-table .box { display: flex; align-items: center; gap: 8px; white-space: normal; }
.pk-table .box img { width: 40px; height: 40px; object-fit: contain; flex: none; border-radius: 4px; background: #fff; }
.pk-table .box-name { line-height: 1.25; }
@media (max-width: 600px) {
  .pk-table .s1 { min-width: 120px; width: 120px; }
  .pk-table .s2 { left: 120px; min-width: 54px; width: 54px; }
  .pk-table .s3 { left: 174px; min-width: 56px; width: 56px; }
  .pk-table .box { gap: 4px; }
  .pk-table .box img { width: 32px; height: 32px; }
}
```

- [ ] **Step 4: Kiểm tra trên trình duyệt**

```bash
(cd web && python3 -m http.server 8765 >/dev/null 2>&1 &); sleep 1
SP=/private/tmp/claude-501/-Users-nguyenvd-Documents-tool-iphone-checker-web/ebb6effc-21fa-43d9-8b1b-28591e55145d/scratchpad
$SP/.venv/bin/python - <<'EOF'
from playwright.sync_api import sync_playwright
SP = "/private/tmp/claude-501/-Users-nguyenvd-Documents-tool-iphone-checker-web/ebb6effc-21fa-43d9-8b1b-28591e55145d/scratchpad"
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in ((1300, 900), (390, 800)):
        pg = b.new_page(viewport={"width": w, "height": h}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://localhost:8765/pokemon-card/"); pg.wait_for_timeout(2000)
        print(w, "rows", pg.locator("#price-table tbody tr").count(), "shops", pg.locator("th.shop").count(),
              "imgs", pg.locator(".box img").count(), "best", pg.locator("td.best").count(), errs)
        pg.screenshot(path=f"{SP}/pokemon_{w}.png")
        if w == 1300:
            pg.click("#series-chips >> text=SV"); pg.click("#sort-chips >> text=Top Diff"); pg.wait_for_timeout(300)
            print("url", pg.url, "first", pg.locator("#price-table tbody tr").first.inner_text()[:40])
            pg.locator("td.clickable").first.click(); pg.wait_for_timeout(300)
            print(pg.locator("#modal-body").inner_text()[:160])
    b.close()
EOF
pkill -f "http.server 8765"
```

Expected:
- Màn hình rộng: `rows 23` (21 BOX + 2 dòng nhóm), `shops 8`, `imgs` ≥ 18, `errors []`.
- Sau khi chọn SV và Top Diff: URL có `?series=sv&sort=diff`.
- Cửa sổ xếp hạng có "Retail ¥", "trả ¥", "Hạng".
- Mở 2 ảnh chụp để xem bố cục: cột BOX không đè lên cột Retail; trên điện thoại tên BOX xuống dòng gọn.

- [ ] **Step 5: Commit**

```bash
git add web/pokemon-card/index.html web/js/pokemon.js web/style.css
git commit -m "feat(web): trang /pokemon-card/ so sánh giá BOX (ảnh, lọc dòng, sắp xếp, xếp hạng)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Thẻ Pokémon trên trang chủ

**Files:**
- Modify: `web/index.html`, `web/js/home.js`

**Interfaces:**
- Consumes: `bestItemDiff(catalog, latest, now)` (Task 7).

- [ ] **Step 1: Sửa `web/index.html`**

Trong thẻ Pokémon, thay

```html
          <p class="category-desc">Box chưa bóc seal và thẻ lẻ</p>
          <p class="category-stat soon">Sắp có</p>
          <span class="category-cta">Xem trước →</span>
```

bằng

```html
          <p class="category-desc">BOX chưa bóc, còn màng co (シュリンク付)</p>
          <p id="pokemon-summary" class="category-stat" hidden></p>
          <span class="category-cta">Xem bảng giá →</span>
```

- [ ] **Step 2: Sửa `web/js/home.js`**

Đổi dòng import thành:

```js
import { bestDiff, bestItemDiff, formatDiff, legacyRedirect } from "./logic.js";
```

Thêm hàm này sau `showIphoneSummary`:

```js
async function showPokemonSummary() {
  const el = document.querySelector("#pokemon-summary");
  try {
    const [catalog, latest] = await Promise.all([loadJson("pokemon/catalog.json"), loadJson("pokemon/latest.json")]);
    const best = bestItemDiff(catalog, latest, new Date());
    if (!best) return;
    el.textContent = `💰 ${best.item.name} lãi tới ${formatDiff(best.diff)} yên so với giá gốc`;
    el.classList.add(best.diff >= 0 ? "pos" : "neg");
    el.hidden = false;
  } catch {
    // Không tải được dữ liệu thì thẻ vẫn bấm được, chỉ không có dòng tóm tắt.
  }
}
```

Thay dòng cuối `if (!redirect) showIphoneSummary();` bằng:

```js
if (!redirect) {
  showIphoneSummary();
  showPokemonSummary();
}
```

- [ ] **Step 3: Kiểm tra trên trình duyệt**

Mở `http://localhost:8765/` như Step 4 của Task 8. Expected: thẻ Pokémon hiện dòng xanh "💰 <tên BOX> lãi tới +… yên so với giá gốc", nút "Xem bảng giá →", và không có lỗi.

- [ ] **Step 4: Chạy toàn bộ test**

Run: `.venv/bin/python -m pytest -q --ignore-glob='* 2.py' && npm test 2>&1 | grep -E "(pass|fail) [0-9]+"`
Expected: pytest pass hết; JS `pass 44`, `fail 0`.

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/js/home.js
git commit -m "feat(web): thẻ Pokémon trên trang chủ hiện BOX lãi cao nhất

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Hoàn tất

- [ ] **Step 1:** Cập nhật trạng thái spec `docs/superpowers/specs/2026-10-03-pokemon-box-design.md` từ "chờ duyệt" thành "đã triển khai", rồi commit.
- [ ] **Step 2:** Dùng superpowers:finishing-a-development-branch: chạy toàn bộ test, đưa người dùng 3 lựa chọn (merge vào `main` ở máy / tạo PR / giữ nhánh). Không push khi người dùng chưa đồng ý.
