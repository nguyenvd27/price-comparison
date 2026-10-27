from pathlib import Path

import pytest

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


def test_morimori_iphone18_landing_cards_pro_max_and_duo(colors_all):
    # Trang /iphone18: mỗi sản phẩm là article.mm1551-ip18-card, giá ở data-mm-price; bỏ iPhone 18 Pro.
    assert morimori.parse(read("morimori_iphone18.html"), colors_all) == [
        Offer("duo-256-nightsky", 380000),
        Offer("duo-256-starwhite", 365000),
        Offer("pm-256-burgundy", 240500),
        Offer("pm-256-glacier", 236000),
    ]
