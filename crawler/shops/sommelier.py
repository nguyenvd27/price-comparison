from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

URL = "https://somurie-kaitori.com/products?category=1"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("div.ant-card"):
        name = card.select_one("p.text-lg")
        price = card.select_one("p.text-price-red")
        if not name or not price or "未開封" not in card.get_text():
            continue
        offer = offer_from_name(name.get_text(strip=True), parse_price(price.get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
