from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

URL = "https://www.kaitorishouten-co.jp/category/1/747"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for link in soup.select('a[href^="/products/detail/"]'):
        row = link.find_parent("tr")
        price = row.select_one("td.num") if row else None
        if not price:
            continue
        offer = offer_from_name(link.get_text(" ", strip=True), parse_price(price.get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
