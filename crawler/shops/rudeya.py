from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

URL = "https://kaitori-rudeya.com/category/detail/253"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Lấy giá gốc; "郵送買取 +500円" (gửi bưu điện được cộng thêm) không tính.
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("article.pgrid-card"):
        badge = card.select_one(".product-card-cond-badge")
        name = card.select_one(".product-card-name-link")
        price = card.select_one(".product-card-price-value")
        if not (badge and name and price) or badge.get_text(strip=True) != "新品" or "未開封" not in name.get_text():
            continue
        offer = offer_from_name(name.get_text(strip=True), parse_price(price.get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
