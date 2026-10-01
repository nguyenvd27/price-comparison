# iPhone Duo (chưa crawl): Kế hoạch triển khai

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hiện iPhone Duo cùng bảng với 18 Pro Max, có bộ lọc dòng máy. Duo chưa được crawl, nên hiện giá Apple và "—" ở các ô cửa hàng.

**Architecture:** `catalog.json` có thêm danh sách `models`; mỗi phiên bản có thêm trường `model`. Crawler chỉ truyền cho parser các màu thuộc dòng máy có `crawl: true`. Frontend thêm các hàm thuần trong `logic.js` (`modelColors`, `hasPrices`, `groupLabel`, `filterVariants` có lọc theo `model`, `chartSeries` có tham số `model`). `app.js` vẽ bảng chia nhóm theo dòng máy kèm bộ lọc dòng máy; `charts.js` có thêm phần chọn dòng máy.

**Tech Stack:** Python 3 + pytest; JS ES modules + `node --test`; Chart.js 4.4.1.

**Spec:** `docs/superpowers/specs/2026-10-02-iphone-duo-design.md` (bổ sung cho `docs/superpowers/specs/2026-10-02-kaitori-price-checker-design.md`)

## Global Constraints

- Mã dòng máy: `pm` ("iPhone 18 Pro Max", nhãn ngắn "18 Pro Max") và `duo` ("iPhone Duo", nhãn ngắn "Duo", `release` "2026-10-23").
- Màu Duo: `nightsky` {vi "Night Sky", hex "#1f2a44", aliases ["ナイトスカイ"]} và `starwhite` {vi "Star White", hex "#ecebe4", aliases ["スターホワイト"]}.
- Giá Apple của Duo: 256GB 364800 · 512GB 399800 · 1TB 469800 · 2TB 574800. Mã phiên bản dạng `duo-<256|512|1tb|2tb>-<nightsky|starwhite>`.
- Màu chỉ hiển thị bằng chấm màu (swatch); dòng máy hiển thị bằng chữ.
- Tiêu đề nhóm: `<name>` + ` · mở bán MM/DD` (chỉ khi hôm nay theo JST trước `release`) + ` · chưa có giá kaitori` (chỉ khi không cửa hàng nào có giá cho dòng máy đó).
- Giữ nguyên parser, quy tắc cập nhật và định dạng `latest.json`, `daily.json`, `history/`.

## Review Focus

1. **Đổi bộ lọc dòng máy trong khi đang lọc một màu của dòng máy kia** (ví dụ `?model=duo&color=burgundy`). Màu phải về "Mọi màu" thay vì làm bảng trống. Kiểm tra trên trình duyệt ở Task 3, Step 5.
2. **Màu Duo lọt vào crawler.** Parser không được sinh giá Pro Max cho Night Sky / Star White. Test: `test_run_only_passes_colors_of_crawled_models` (Task 1).
3. **Catalog không nhất quán** (phiên bản trỏ tới dòng máy hoặc màu không tồn tại, màu không thuộc dòng máy của phiên bản). Test: `test_catalog_is_consistent` (Task 1).
4. **Ngày mở bán theo giờ Nhật.** Ngày 10/23 JST thì nhãn "mở bán 10/23" phải biến mất. Test: `groupLabel hides release note on release day` (Task 2).
5. **Biểu đồ của dòng máy chưa có dữ liệu.** Phải hiện "Chưa có dữ liệu giá", không vẽ khung trống. Kiểm tra trên trình duyệt ở Task 4, Step 2.

---

### Task 1: Catalog có nhiều dòng máy; crawler chỉ dùng màu của dòng máy được crawl

**Files:**
- Modify: `web/data/catalog.json`, `crawler/run.py:20-22`, `crawler/tests/test_run.py:10`
- Create: `crawler/tests/test_catalog.py`

**Interfaces:**
- Produces: `catalog.models: [{id, name, short, colors: [colorId], crawl: bool, release?: "YYYY-MM-DD"}]`; mỗi `variants[]` có thêm `model`. Hàm `crawler.run.crawl_colors(catalog) -> dict[str, list[str]]`.

- [ ] **Step 1: Viết test thất bại**

Sửa dòng `CATALOG = ...` trong `crawler/tests/test_run.py` thành:
```python
CATALOG = {
    "models": [{"id": "pm", "colors": ["black"], "crawl": True}],
    "colors": {"black": {"aliases": ["ブラック"]}},
    "shops": [{"id": "a"}, {"id": "b"}],
}
```

Thêm vào cuối `crawler/tests/test_run.py`:
```python


def test_run_only_passes_colors_of_crawled_models(tmp_path):
    catalog = {
        "models": [
            {"id": "pm", "colors": ["black"], "crawl": True},
            {"id": "duo", "colors": ["nightsky"], "crawl": False},
        ],
        "colors": {"black": {"aliases": ["ブラック"]}, "nightsky": {"aliases": ["ナイトスカイ"]}},
        "shops": [{"id": "a"}],
    }
    (tmp_path / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    seen = []

    def parse(raw, colors):
        seen.append(colors)
        return [Offer("pm-256-black", 236000)]

    main(tmp_path, {"a": SimpleNamespace(fetch=lambda session: "raw", parse=parse)}, NOW)
    assert seen == [{"black": ["ブラック"]}]
```

Tạo `crawler/tests/test_catalog.py`:
```python
import json

from crawler.store import DATA_DIR


def test_catalog_is_consistent():
    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    models = {m["id"]: m for m in catalog["models"]}
    assert list(models) == ["pm", "duo"]
    for variant in catalog["variants"]:
        model = models[variant["model"]]
        assert variant["color"] in model["colors"], variant["id"]
        assert variant["color"] in catalog["colors"], variant["id"]
    counts = {m: sum(v["model"] == m for v in catalog["variants"]) for m in models}
    assert counts == {"pm": 16, "duo": 8}
    duo = {v["id"]: v["apple_price"] for v in catalog["variants"] if v["model"] == "duo"}
    assert duo["duo-256-nightsky"] == 364800
    assert duo["duo-2tb-starwhite"] == 574800
    assert models["duo"]["crawl"] is False and models["duo"]["release"] == "2026-10-23"
```

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `.venv/bin/python -m pytest -q 2>&1 | tail -4`
Expected: FAIL. `test_run_only_passes_colors_of_crawled_models` fail vì `seen == [{"black": [...], "nightsky": [...]}]`; `test_catalog_is_consistent` fail với `KeyError: 'models'`.

- [ ] **Step 3: Sửa `crawler/run.py`**

Thêm hàm này ngay trên `def main`:
```python
def crawl_colors(catalog: dict) -> dict[str, list[str]]:
    """Chỉ các màu thuộc dòng máy đang crawl, để parser không sinh giá cho màu của dòng máy khác."""
    wanted = {color for model in catalog["models"] if model["crawl"] for color in model["colors"]}
    return {color_id: color["aliases"] for color_id, color in catalog["colors"].items() if color_id in wanted}
```

Trong `main`, thay dòng:
```python
    colors = {color_id: color["aliases"] for color_id, color in catalog["colors"].items()}
```
bằng:
```python
    colors = crawl_colors(catalog)
```

- [ ] **Step 4: Cập nhật `web/data/catalog.json`**

Run:
```bash
.venv/bin/python - <<'EOF'
import json
p = "web/data/catalog.json"
c = json.load(open(p, encoding="utf-8"))
c.pop("model", None)
c["models"] = [
    {"id": "pm", "name": "iPhone 18 Pro Max", "short": "18 Pro Max", "colors": ["burgundy", "glacier", "black", "silver"], "crawl": True},
    {"id": "duo", "name": "iPhone Duo", "short": "Duo", "colors": ["nightsky", "starwhite"], "release": "2026-10-23", "crawl": False},
]
c["colors"]["nightsky"] = {"vi": "Night Sky", "hex": "#1f2a44", "aliases": ["ナイトスカイ"]}
c["colors"]["starwhite"] = {"vi": "Star White", "hex": "#ecebe4", "aliases": ["スターホワイト"]}
for v in c["variants"]:
    v["model"] = "pm"
prices = {"256GB": ("256", 364800), "512GB": ("512", 399800), "1TB": ("1tb", 469800), "2TB": ("2tb", 574800)}
for cap, (code, price) in prices.items():
    for color in ["nightsky", "starwhite"]:
        c["variants"].append({"id": f"duo-{code}-{color}", "model": "duo", "capacity": cap, "color": color, "apple_price": price})
ordered = {"models": c.pop("models"), **c}
json.dump(ordered, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(p, "a", encoding="utf-8").write("\n")
EOF
```

- [ ] **Step 5: Chạy test, xác nhận pass**

Run: `.venv/bin/python -m pytest -q 2>&1 | tail -1`
Expected: `63 passed`

- [ ] **Step 6: Commit**

```bash
git add crawler/run.py crawler/tests/test_run.py crawler/tests/test_catalog.py web/data/catalog.json
git commit -m "feat: catalog nhiều dòng máy, thêm iPhone Duo (chưa crawl)"
```

---

### Task 2: Hàm logic theo dòng máy

**Files:**
- Modify: `web/js/logic.js` (`filterVariants`, `chartSeries`; thêm `modelColors`, `hasPrices`, `groupLabel`)
- Modify: `web/js/charts.js:31-32` (gọi `chartSeries` theo tham số mới, để trang không lỗi giữa các task)
- Modify: `tests/web/charts.test.js:5-12,25`
- Create: `tests/web/models.test.js`

**Interfaces:**
- Consumes: định dạng catalog của Task 1.
- Produces:
  - `filterVariants(variants, {model = "all", cap = "all", color = "all"})`
  - `modelColors(catalog, model: "all" | id) -> colorId[]` (thứ tự theo `models`, không trùng)
  - `hasPrices(latest, variantIds) -> boolean`
  - `groupLabel(model, variantIds, latest, today: "YYYY-MM-DD") -> string`
  - `chartSeries(daily, catalog, model, cap, range, today)`. Tham số `model` mới đứng **trước** `cap`.

- [ ] **Step 1: Viết test thất bại**

`tests/web/models.test.js`:
```js
import assert from "node:assert/strict";
import { test } from "node:test";
import { filterVariants, groupLabel, hasPrices, modelColors } from "../../web/js/logic.js";

const CATALOG = {
  models: [
    { id: "pm", name: "iPhone 18 Pro Max", colors: ["burgundy", "black"] },
    { id: "duo", name: "iPhone Duo", colors: ["nightsky", "starwhite"], release: "2026-10-23" },
  ],
};
const VARIANTS = [
  { id: "pm-256-black", model: "pm", capacity: "256GB", color: "black" },
  { id: "duo-256-nightsky", model: "duo", capacity: "256GB", color: "nightsky" },
  { id: "duo-1tb-starwhite", model: "duo", capacity: "1TB", color: "starwhite" },
];

test("filterVariants by model", () => {
  assert.deepEqual(filterVariants(VARIANTS, { model: "duo" }).map((v) => v.id), ["duo-256-nightsky", "duo-1tb-starwhite"]);
  assert.deepEqual(filterVariants(VARIANTS, { model: "duo", cap: "256GB" }).map((v) => v.id), ["duo-256-nightsky"]);
  assert.equal(filterVariants(VARIANTS, {}).length, 3);
});

test("modelColors per model and for all", () => {
  assert.deepEqual(modelColors(CATALOG, "duo"), ["nightsky", "starwhite"]);
  assert.deepEqual(modelColors(CATALOG, "all"), ["burgundy", "black", "nightsky", "starwhite"]);
  assert.deepEqual(modelColors(CATALOG, "nope"), []);
});

test("hasPrices", () => {
  const latest = { shops: { a: { prices: { "pm-256-black": 236000 } }, b: { prices: {} } } };
  assert.equal(hasPrices(latest, ["pm-256-black"]), true);
  assert.equal(hasPrices(latest, ["duo-256-nightsky"]), false);
  assert.equal(hasPrices({ shops: {} }, ["pm-256-black"]), false);
});

test("groupLabel before release without prices", () => {
  const latest = { shops: { a: { prices: { "pm-256-black": 236000 } } } };
  assert.equal(groupLabel(CATALOG.models[1], ["duo-256-nightsky"], latest, "2026-10-02"), "iPhone Duo · mở bán 10/23 · chưa có giá kaitori");
  assert.equal(groupLabel(CATALOG.models[0], ["pm-256-black"], latest, "2026-10-02"), "iPhone 18 Pro Max");
});

test("groupLabel hides release note on release day", () => {
  const latest = { shops: { a: { prices: { "duo-256-nightsky": 400000 } } } };
  assert.equal(groupLabel(CATALOG.models[1], ["duo-256-nightsky"], latest, "2026-10-23"), "iPhone Duo");
  assert.equal(groupLabel(CATALOG.models[1], ["duo-256-nightsky"], latest, "2026-10-22"), "iPhone Duo · mở bán 10/23");
});
```

Trong `tests/web/charts.test.js`, sửa `CATALOG` và lời gọi `chartSeries`:
```js
const CATALOG = {
  colors: { black: { vi: "Đen", hex: "#333" }, silver: { vi: "Bạc", hex: "#aaa" }, nightsky: { vi: "Night Sky", hex: "#123" } },
  variants: [
    { id: "pm-256-black", model: "pm", capacity: "256GB", color: "black", apple_price: 239800 },
    { id: "pm-256-silver", model: "pm", capacity: "256GB", color: "silver", apple_price: 239800 },
    { id: "pm-1tb-black", model: "pm", capacity: "1TB", color: "black", apple_price: 344800 },
    { id: "duo-256-nightsky", model: "duo", capacity: "256GB", color: "nightsky", apple_price: 364800 },
  ],
};
```
```js
  const { labels, datasets } = chartSeries(daily, CATALOG, "pm", "256GB", 3, "2026-10-02");
```
(Assert `datasets.map((d) => d.variant)` vẫn là `["pm-256-black", "pm-256-silver"]`: Duo không được lẫn vào.)

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `npm test 2>&1 | grep -m1 -E "does not provide|not ok"`
Expected: `SyntaxError: ... does not provide an export named 'groupLabel'`

- [ ] **Step 3: Sửa `web/js/logic.js`**

Thay `filterVariants`:
```js
export function filterVariants(variants, { model = "all", cap = "all", color = "all" } = {}) {
  return variants.filter(
    (v) => (model === "all" || v.model === model) && (cap === "all" || v.capacity === cap) && (color === "all" || v.color === color),
  );
}

export function modelColors(catalog, model) {
  const models = model === "all" ? catalog.models : catalog.models.filter((m) => m.id === model);
  return [...new Set(models.flatMap((m) => m.colors))];
}

export function hasPrices(latest, variantIds) {
  return Object.values(latest.shops ?? {}).some((shop) => variantIds.some((id) => shop.prices?.[id] != null));
}

// Tiêu đề nhóm trong bảng, ví dụ "iPhone Duo · mở bán 10/23 · chưa có giá kaitori".
export function groupLabel(model, variantIds, latest, today) {
  const parts = [model.name];
  if (model.release && today < model.release) parts.push(`mở bán ${model.release.slice(5).replace("-", "/")}`);
  if (!hasPrices(latest, variantIds)) parts.push("chưa có giá kaitori");
  return parts.join(" · ");
}
```

Thay dòng đầu và bộ lọc của `chartSeries`:
```js
export function chartSeries(daily, catalog, model, cap, range, today) {
  const labels = dateRange(daily, today, range);
  const datasets = catalog.variants
    .filter((v) => v.model === model && v.capacity === cap)
```
(phần còn lại của hàm giữ nguyên).

Trong `renderLine` (`web/js/charts.js`), thay 2 dòng đầu:
```js
  const { labels, datasets } = chartSeries(daily, catalog, state.chartCap, state.range, today);
  const apple = catalog.variants.find((v) => v.capacity === state.chartCap)?.apple_price ?? null;
```
bằng:
```js
  const model = state.chartModel ?? catalog.models[0].id;
  const { labels, datasets } = chartSeries(daily, catalog, model, state.chartCap, state.range, today);
  const apple = catalog.variants.find((v) => v.model === model && v.capacity === state.chartCap)?.apple_price ?? null;
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `npm test 2>&1 | grep -E '^ℹ (pass|fail)'`
Expected: `ℹ pass 26` và `ℹ fail 0`

- [ ] **Step 5: Commit**

```bash
git add web/js/logic.js web/js/charts.js tests/web/models.test.js tests/web/charts.test.js
git commit -m "feat(web): hàm lọc, màu, tiêu đề nhóm và dữ liệu biểu đồ theo dòng máy"
```

---

### Task 3: Bộ lọc dòng máy và bảng chia nhóm

**Files:**
- Modify: `web/index.html` (hàng `#model-chips`), `web/js/app.js`, `web/style.css`

**Interfaces:**
- Consumes: `filterVariants`, `modelColors`, `groupLabel`, `jstDate` (Task 2 và có sẵn).
- Produces: `state.model` ("all" | id), `state.chartModel` (id). `renderCharts(data, state)` đọc thêm `state.chartModel` (Task 4).

- [ ] **Step 1: `web/index.html`**

Thêm `<div id="model-chips" class="chips"></div>` ngay trước dòng `<div id="cap-chips" class="chips"></div>`. Trong `.card-head` của biểu đồ "Giá cao nhất mỗi ngày", thêm `<div id="chart-model" class="chips"></div>` ngay trước `<div id="chart-cap" class="chips"></div>` (Step 2 vẽ chip vào thẻ này).

- [ ] **Step 2: `web/js/app.js`: state, đọc/lưu bộ lọc, các hàng chip**

Import thêm `groupLabel, jstDate, modelColors`:
```js
import {
  bestOffer, esc, filterVariants, formatDiff, formatTime, formatYen, groupLabel, isStale, isUsable, jstDate, modelColors,
  openStatus, rankOffers,
} from "./logic.js";
```

```js
const state = { model: "all", cap: "all", color: "all", chartModel: null, chartCap: null, chartColor: null, range: 30 };
```

Thay `colorOptions` bằng:
```js
function colorOptions(model) {
  return modelColors(data.catalog, model).map((id) => {
    const c = data.catalog.colors[id];
    return { value: id, label: c.vi, dot: c.hex, swatchOnly: true };
  });
}

function modelOf(colorId) {
  return data.catalog.models.find((m) => m.colors.includes(colorId))?.id;
}
```

Thay `readState` và `saveState`:
```js
function readState() {
  let saved = {};
  try {
    saved = JSON.parse(localStorage.getItem("filters") || "{}");
  } catch {
    saved = {};
  }
  const url = new URLSearchParams(location.search);
  const pick = (key) => url.get(key) || saved[key];
  const { models } = data.catalog;
  const model = pick("model");
  state.model = models.some((m) => m.id === model) ? model : "all";
  const cap = pick("cap");
  state.cap = capacities().includes(cap) ? cap : "all";
  const color = pick("color");
  state.color = modelColors(data.catalog, state.model).includes(color) ? color : "all";
  state.chartModel = state.model !== "all" ? state.model : state.color !== "all" ? modelOf(state.color) : models[0].id;
  state.chartCap = state.cap !== "all" ? state.cap : capacities()[0];
  state.chartColor = state.color !== "all" ? state.color : modelColors(data.catalog, state.chartModel)[0];
}

function saveState() {
  const url = new URLSearchParams();
  if (state.model !== "all") url.set("model", state.model);
  if (state.cap !== "all") url.set("cap", state.cap);
  if (state.color !== "all") url.set("color", state.color);
  const query = url.toString();
  history.replaceState(null, "", query ? `?${query}` : location.pathname);
  try {
    localStorage.setItem("filters", JSON.stringify({ model: state.model, cap: state.cap, color: state.color }));
  } catch {
    // trình duyệt chặn localStorage: bỏ qua, bộ lọc vẫn nằm trong URL
  }
}

function setChartModel(model) {
  state.chartModel = model;
  if (!modelColors(data.catalog, model).includes(state.chartColor)) state.chartColor = modelColors(data.catalog, model)[0];
}
```

Trong `renderFilters`, thêm hàng dòng máy ở đầu hàm, cập nhật hàng màu, và thêm hàng `#chart-model` (thay hàng `#stat-color` hiện có bằng bản dưới):
```js
  const modelOptions = data.catalog.models.map((m) => ({ value: m.id, label: m.short }));
  renderChips($("#model-chips"), [{ value: "all", label: "Tất cả" }, ...modelOptions], state.model, (v) => {
    state.model = v;
    if (!modelColors(data.catalog, v).includes(state.color)) state.color = "all";
    if (v !== "all") setChartModel(v);
    update();
  });
```
```js
  renderChips($("#color-chips"), [{ value: "all", label: "Mọi màu" }, ...colorOptions(state.model)], state.color, (v) => {
    state.color = v;
    if (v !== "all") {
      setChartModel(modelOf(v));
      state.chartColor = v;
    }
    update();
  });
  renderChips($("#chart-model"), modelOptions, state.chartModel, (v) => {
    setChartModel(v);
    update();
  });
```
```js
  renderChips($("#stat-color"), colorOptions(state.chartModel), state.chartColor, (v) => {
    state.chartColor = v;
    update();
  });
```

- [ ] **Step 3: `web/js/app.js`: bảng chia nhóm**

Tách phần vẽ một dòng phiên bản trong `renderTable` thành hàm riêng, rồi vẽ theo nhóm dòng máy:
```js
function variantRow(v, shops, shopIds, latest, now) {
  const color = data.catalog.colors[v.color];
  const best = bestOffer(v.id, latest, shopIds, now);
  const diff = best ? best.price - v.apple_price : null;
  const cells = shops
    .map((s) => {
      const price = latest.shops?.[s.id]?.prices?.[v.id];
      const usable = isUsable(latest.shops?.[s.id], now);
      const cls = !usable ? "muted" : best && price === best.price ? "best" : "";
      if (price == null) return `<td class="${cls}">—</td>`;
      return `<td class="${cls} clickable" data-variant="${esc(v.id)}" data-shop="${esc(s.id)}" tabindex="0">${formatYen(price)}</td>`;
    })
    .join("");
  return `<tr>
    <td class="s1" title="${esc(color.vi)}"><span class="dot" style="background:${esc(color.hex)}" aria-label="${esc(color.vi)}"></span>${esc(v.capacity)}</td>
    <td class="s2">${formatYen(v.apple_price)}</td>
    <td class="s3 ${diff == null ? "" : diffClass(diff)}">${formatDiff(diff)}</td>${cells}
  </tr>`;
}

function renderTable() {
  const { catalog, latest } = data;
  const now = new Date();
  const today = jstDate(now);
  const shops = catalog.shops;
  const shopIds = shops.map((s) => s.id);
  const columns = 3 + shops.length;
  const head = `<thead><tr><th class="s1">Phiên bản</th><th class="s2">Apple</th><th class="s3">Chênh lệch</th>${shops
    .map((s) => shopHeader(s, latest.shops?.[s.id], now))
    .join("")}</tr></thead>`;

  const variants = filterVariants(catalog.variants, state);
  const body = catalog.models
    .map((m) => {
      const rows = variants.filter((v) => v.model === m.id);
      if (!rows.length) return "";
      const allIds = catalog.variants.filter((v) => v.model === m.id).map((v) => v.id);
      const header = `<tr class="group"><td colspan="${columns}"><span>${esc(groupLabel(m, allIds, latest, today))}</span></td></tr>`;
      return header + rows.map((v) => variantRow(v, shops, shopIds, latest, now)).join("");
    })
    .join("");

  const empty = `<tr><td colspan="${columns}" class="empty">Không có kết quả phù hợp</td></tr>`;
  $("#price-table").innerHTML = `${head}<tbody>${body || empty}</tbody>`;
}
```

- [ ] **Step 4: `web/style.css`**

Thêm sau dòng `td.empty { ... }`:
```css
tr.group td { background: #f3f4f6; text-align: left; font-weight: 700; font-size: 13px; color: var(--text); padding: 8px 10px; }
tr.group td span { position: sticky; left: 10px; }
```

- [ ] **Step 5: Kiểm tra bằng trình duyệt**

Run: `python3 -m http.server 8000 -d web`, mở `http://localhost:8000/?model=all`.

Kiểm tra:
- Có hàng chip `Tất cả | 18 Pro Max | Duo` đứng trước hàng dung lượng. Hàng màu có 6 chấm màu.
- Bảng có tiêu đề nhóm "iPhone 18 Pro Max" (16 dòng), rồi "iPhone Duo · mở bán 10/23 · chưa có giá kaitori" (8 dòng). Các dòng Duo có giá Apple 364,800… và "—" ở mọi ô cửa hàng.
- Bấm `Duo` thì chỉ còn nhóm Duo, URL là `?model=duo`, và hàng màu chỉ còn 2 chấm màu.
- Mở `?model=duo&color=burgundy` thì màu về "Mọi màu" và có 8 dòng Duo.
- Ở khổ 375px, vuốt ngang bảng: chữ tiêu đề nhóm vẫn nằm ở mép trái.
- Không có lỗi JS trong console.

- [ ] **Step 6: Commit**

```bash
git add web/index.html web/js/app.js web/style.css
git commit -m "feat(web): bộ lọc dòng máy và bảng chia nhóm Pro Max / Duo"
```

---

### Task 4: Biểu đồ theo dòng máy

**Files:**
- Modify: `web/index.html` (`#line-empty`), `web/js/charts.js` (`renderLine`, `renderWeekday`)

**Interfaces:**
- Consumes: `state.chartModel` (Task 3), `chartSeries(daily, catalog, model, cap, range, today)` (Task 2).

- [ ] **Step 1: Sửa `web/index.html` và `web/js/charts.js`**

Thêm `<p id="line-empty" class="empty" hidden>Chưa có dữ liệu giá</p>` ngay trước `<div class="chart-box"><canvas id="line-chart"></canvas></div>`.

Trong `renderLine` (`web/js/charts.js`), ngay sau dòng `const apple = ...` (đã sửa ở Task 2), thêm:
```js
  const canvas = document.querySelector("#line-chart");
  const noData = datasets.every((s) => s.data.every((v) => v == null));
  document.querySelector("#line-empty").hidden = !noData;
  canvas.parentElement.hidden = noData;
  lineChart?.destroy();
  lineChart = null;
  if (noData) return;
```
và đổi `lineChart?.destroy();\n  lineChart = new Chart(document.querySelector("#line-chart"), {` thành `lineChart = new Chart(canvas, {`.

Trong `renderWeekday`, đổi dòng tìm phiên bản thành:
```js
  const variant = catalog.variants.find(
    (v) => v.model === state.chartModel && v.capacity === state.chartCap && v.color === state.chartColor,
  );
```

- [ ] **Step 2: Kiểm tra bằng trình duyệt**

Run: `python3 -m http.server 8000 -d web`, mở `http://localhost:8000/?model=all`.

Kiểm tra:
- Biểu đồ đường có hàng `18 Pro Max | Duo`. Với `18 Pro Max`, biểu đồ vẽ như trước (4 đường).
- Bấm `Duo`: canvas ẩn, hiện "Chưa có dữ liệu giá". Hàng màu ở phần thống kê theo thứ còn 2 chấm màu Duo và hiện "Đang thu thập dữ liệu (cần thêm 14 ngày)".
- Bấm lại `18 Pro Max`: biểu đồ hiện lại.
- Bộ lọc bảng chọn `Duo` thì biểu đồ cũng chuyển sang Duo.
- Không có lỗi JS.

- [ ] **Step 3: Chạy toàn bộ test và commit**

Run: `npm test 2>&1 | grep -E '^ℹ (pass|fail)'; .venv/bin/python -m pytest -q | tail -1`
Expected: `ℹ pass 26`, `ℹ fail 0`, `63 passed`

```bash
git add web/index.html web/js/charts.js
git commit -m "feat(web): biểu đồ chọn theo dòng máy, báo khi chưa có dữ liệu"
```
