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
