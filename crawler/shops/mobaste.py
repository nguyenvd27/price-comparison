from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offers_from_base

URL = "https://pastec.net/iphone?series_child_id=644"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for row in soup.select("tr.js-targetStorage"):
        name = row.select_one(".p-priceTable__name > span")
        price = row.select_one(".price--unopened")
        if not name or not price:
            continue
        caution = row.select_one(".p-priceTable__caution")
        offers += offers_from_base(
            name.get_text(strip=True),
            parse_price(price.get_text()),
            caution.get_text(" ", strip=True) if caution else "",
            colors,
        )
    return dedupe(offers)
