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
