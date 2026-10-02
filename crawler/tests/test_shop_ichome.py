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


def test_registry_has_all_shops():
    assert set(SHOPS) == {
        "morimori", "ichiban", "mobaste", "shouten", "ichome", "mix",
        "akimoba", "homura", "rudeya", "wiki", "rakuen", "base", "sommelier", "jcka",
    }
    assert all(hasattr(m, "fetch") and hasattr(m, "parse") for m in SHOPS.values())
