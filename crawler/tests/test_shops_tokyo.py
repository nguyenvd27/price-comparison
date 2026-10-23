"""3 kaitori thêm 2026-10-23: トゥインクルモバイル, 買取オク, ドラゴンモバイル."""
import json
from pathlib import Path

from crawler.categories import crawl_colors
from crawler.shops import dragon, oku, twinkle
from crawler.store import DATA_DIR

FIXTURES = Path(__file__).parent / "fixtures"
COLORS = crawl_colors(json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8")))


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def as_dict(offers):
    return {o.variant: o.price for o in offers}


def test_catalog_variants_have_unique_jan_and_colors_expose_lookup():
    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    jans = [v["jan"] for v in catalog["variants"]]
    assert len(jans) == 24 and len(set(jans)) == 24 and all(len(j) == 13 and j.isdigit() for j in jans)
    assert COLORS.jans["4549995734645"] == "pm-256-burgundy"
    assert COLORS.jans["4549995732696"] == "duo-256-nightsky"


def test_twinkle_unopened_price_per_color():
    assert as_dict(twinkle.parse(read("twinkle.html"), COLORS)) == {
        "pm-256-burgundy": 236000, "pm-256-black": 224000, "duo-256-nightsky": 440000,
    }


def test_oku_iphone_cards_skip_text_price():
    assert as_dict(oku.parse(read("oku.html"), COLORS)) == {
        "pm-256-burgundy": 236000, "pm-256-black": 225600, "duo-256-starwhite": 440000,
    }


def test_dragon_maps_capacity_price_to_the_jan_color():
    # Mỗi dung lượng chỉ có 1 giá; JAN cho biết màu (256GB = バーガンディ, Duo 256GB = ナイトスカイ).
    assert as_dict(dragon.parse(read("dragon.html"), COLORS)) == {
        "pm-256-burgundy": 236000, "pm-512-burgundy": 275000, "duo-256-nightsky": 440000,
    }
