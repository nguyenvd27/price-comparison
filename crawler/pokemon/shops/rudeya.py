from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

URL = "https://kaitori-rudeya.com/category/detail/114"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("article.pgrid-card"):
        badge = card.select_one(".product-card-cond-badge")
        name = card.select_one(".product-card-name-link")
        price = card.select_one(".product-card-price-value")
        jan = card.select_one(".product-card-jan-text")
        if not (badge and name and price) or badge.get_text(strip=True) != "新品":
            continue
        item = match_item(name.get_text(" ", strip=True), clean_jan(jan.get_text() if jan else ""), items)
        value = parse_price(price.get_text())
        if item and value:
            offers.append(Offer(item, value))
    return dedupe(offers)
