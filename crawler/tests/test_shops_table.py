from pathlib import Path

import pytest
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


def test_shouten_reads_live_api_new_price(colors):
    # Giá lấy từ API (giá thật đang hiển thị), nhãn "新品"; bỏ qua sản phẩm chưa có giá và model khác
    assert shouten.parse(read("shouten.json"), colors) == [
        Offer("pm-256-burgundy", 255000),
        Offer("pm-2tb-black", 426000),
    ]


def test_shouten_api_more_pages_than_fetched_raises(colors):
    with pytest.raises(ValueError, match="trang"):
        shouten.parse('{"page": 1, "per_page": 100, "total": 150, "items": []}', colors)


def test_parsers_return_empty_on_unrelated_html(colors):
    assert morimori.parse("<html></html>", colors) == []
    assert shouten.parse('{"page": 1, "per_page": 100, "total": 0, "items": []}', colors) == []


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
