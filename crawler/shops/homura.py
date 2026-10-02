from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

# Lọc sẵn danh mục iPhone 18 Pro Max (sub_category 192) nên chỉ có 1 trang.
URL = (
    "https://kaitori-homura.com/products"
    "?q%5Bproduct_sub_category_id_eq%5D=192&q%5Bproduct_sub_category_product_category_id_eq%5D=10"
)


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for title in soup.select("h5"):
        name = " ".join(title.get_text().split())
        card = title.find_parent(lambda tag: tag.name == "div" and tag.select_one("span.text-lg"))
        if not card or "未開封" not in name:
            continue
        offer = offer_from_name(name, parse_price(card.select_one("span.text-lg").get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
