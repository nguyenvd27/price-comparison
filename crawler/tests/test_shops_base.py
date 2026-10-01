from pathlib import Path

from crawler.models import Offer
from crawler.shops import ichiban, mix, mobaste

FIXTURES = Path(__file__).parent / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def as_dict(offers):
    return {offer.variant: offer.price for offer in offers}


def test_ichiban_applies_deductions_and_skips_opened(colors):
    assert as_dict(ichiban.parse(read("ichiban.html"), colors)) == {
        "pm-256-burgundy": 262000, "pm-256-glacier": 235000,
        "pm-256-black": 236000, "pm-256-silver": 230000,
        "pm-512-burgundy": 292000, "pm-512-glacier": 270000,
        "pm-512-black": 270000, "pm-512-silver": 270000,
    }


def test_mobaste_unopened_price_and_deductions(colors):
    assert as_dict(mobaste.parse(read("mobaste.html"), colors)) == {
        "pm-256-burgundy": 264000, "pm-256-glacier": 230000,
        "pm-256-black": 230000, "pm-256-silver": 230000,
        "pm-2tb-burgundy": 435000, "pm-2tb-glacier": 435000,
        "pm-2tb-black": 435000, "pm-2tb-silver": 435000,
    }


def test_mix_only_burgundy_row(colors):
    assert as_dict(mix.parse(read("mix.html"), colors)) == {
        "pm-256-burgundy": 263000, "pm-256-glacier": 235000,
        "pm-256-black": 236000, "pm-256-silver": 231000,
        "pm-512-burgundy": 292000,
    }


def test_mix_cookie_error_page_returns_nothing(colors):
    assert mix.parse("<html><body>Cookieを有効にしてください</body></html>", colors) == []


def test_mix_fetch_visits_home_first():
    calls = []

    class FakeResponse:
        encoding = "utf-8"
        text = "ok"

        def raise_for_status(self):
            pass

    class FakeSession:
        def get(self, url, timeout):
            calls.append(url)
            return FakeResponse()

    assert mix.fetch(FakeSession()) == "ok"
    assert calls == ["https://mobile-mix.jp/", "https://mobile-mix.jp/?category=7"]


def test_offer_type(colors):
    assert all(isinstance(o, Offer) for o in mix.parse(read("mix.html"), colors))
