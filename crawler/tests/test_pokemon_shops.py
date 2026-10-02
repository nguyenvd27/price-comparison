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


from crawler.pokemon.shops import ichome, runto, shinsoku  # noqa: E402


def test_ichome_takes_shrink_price_and_cleans_jan():
    assert as_dict(ichome.parse(read("ichome.json"), ITEMS)) == {"mega-30th": 26000, "mega-mega-brave": 7800}


def test_ichome_reads_first_page_without_error_when_list_is_longer():
    # Spec mục 5: hết số trang thì dừng, không báo lỗi.
    raw = json.dumps({"code": 200, "data": {"totalElements": 150, "size": 100, "content": [
        {"title": "【MEGA】 30th CELEBRATION BOX", "jan": "4521329462424",
         "goodsKbDetails": [{"kbDetailName": "シュリンク有", "kbDetailPrice": 26000}]}]}})
    assert as_dict(ichome.parse(raw, ITEMS)) == {"mega-30th": 26000}


def test_api_prices_given_as_strings_become_ints():
    raw = json.dumps({"code": 200, "data": {"totalElements": 1, "size": 100, "content": [
        {"title": "【MEGA】 30th CELEBRATION BOX", "jan": "4521329462424",
         "goodsKbDetails": [{"kbDetailName": "シュリンク有", "kbDetailPrice": "26,000"}]}]}})
    assert ichome.parse(raw, ITEMS)[0].price == 26000
    raw = json.dumps({"pages": [{"ok": True, "data": {"has_more": False, "items": [
        {"name": "拡張パック「30th CELEBRATION」(M6a)", "postal_purchase_price_s": "26300"}]}}]})
    assert shinsoku.parse(raw, ITEMS)[0].price == 26300


def test_shinsoku_matches_by_name_skips_dx_and_missing_price():
    assert as_dict(shinsoku.parse(read("shinsoku.json"), ITEMS)) == {"mega-30th": 26300, "sv-black-bolt": 17600}


def test_runto_uses_shrink_variation_or_simple_price():
    assert as_dict(runto.parse(read("runto.json"), ITEMS)) == {
        "mega-30th": 26800, "mega-30th-futuristic": 58000, "sv-rocket-gang": 18700,
    }
