"""Parser của 8 kaitori thêm sau. Fixture được cắt từ trang thật ngày 2026-10-02."""
from pathlib import Path

from crawler.shops import akimoba, base, homura, jcka, rakuen, rudeya, sommelier, wiki

FIXTURES = Path(__file__).parent / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def as_dict(offers):
    return {offer.variant: offer.price for offer in offers}


def test_sommelier_cards_skip_other_models(colors):
    assert as_dict(sommelier.parse(read("sommelier.html"), colors)) == {
        "pm-256-glacier": 236000, "pm-256-silver": 232000, "pm-256-black": 236000,
        "pm-512-burgundy": 289000,
    }


def test_wiki_cards(colors):
    assert as_dict(wiki.parse(read("wiki.html"), colors)) == {
        "pm-256-black": 236000, "pm-256-silver": 230000,
        "pm-256-glacier": 235000, "pm-256-burgundy": 255000,
    }


def test_rudeya_new_unopened_cards(colors):
    assert as_dict(rudeya.parse(read("rudeya.html"), colors)) == {
        "pm-256-burgundy": 255000, "pm-256-black": 234000,
        "pm-256-glacier": 230000, "pm-256-silver": 230000,
        "pm-2tb-burgundy": 430000,
    }


def test_homura_english_colors(colors):
    assert as_dict(homura.parse(read("homura.html"), colors)) == {
        "pm-256-burgundy": 256000, "pm-256-glacier": 222000,
        "pm-256-silver": 222000, "pm-256-black": 226000,
    }


def test_akimoba_table_skips_iphone17(colors):
    assert as_dict(akimoba.parse(read("akimoba.html"), colors)) == {
        "pm-256-burgundy": 256000, "pm-256-glacier": 229000,
        "pm-256-silver": 229000, "pm-256-black": 229000,
    }


def test_rakuen_listed_colors_have_own_price_rest_get_new_price(colors):
    # "新品: ¥250,000" là giá màu không được liệt kê (バーガンディ); "黒/青 231,000" là giá riêng.
    assert as_dict(rakuen.parse(read("rakuen.html"), colors)) == {
        "pm-256-burgundy": 250000, "pm-256-black": 231000,
        "pm-256-glacier": 231000, "pm-256-silver": 230000,
        "pm-2tb-burgundy": 430000, "pm-2tb-black": 422000,
        "pm-2tb-glacier": 422000, "pm-2tb-silver": 422000,
    }


def test_jcka_unopened_row_and_one_kanji_colors(colors):
    # "青・黒・白-20,000": 白 là シルバー.
    result = as_dict(jcka.parse(read("jcka.html"), colors))
    assert result["pm-256-burgundy"] == 250000
    assert result["pm-256-glacier"] == result["pm-256-black"] == result["pm-256-silver"] == 230000
    assert result["pm-2tb-burgundy"] == 420000
    assert result["pm-2tb-silver"] == 415000
    assert len(result) == 16


def test_base_table_without_iphone_prefix(colors):
    result = as_dict(base.parse(read("base.html"), colors))
    assert result["pm-256-burgundy"] == 257500
    assert result["pm-256-glacier"] == result["pm-256-black"] == 237500
    assert result["pm-256-silver"] == 233500
    assert result["pm-1tb-black"] == 348000
    assert result["pm-1tb-silver"] == 341500
    assert len(result) == 16
