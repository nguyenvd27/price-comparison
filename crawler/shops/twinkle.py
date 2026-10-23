from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

# Một trang có đủ 18 Pro Max và Duo (pageSize lớn để không phải phân trang).
URL = "https://twinkle-mobile.com/shop/products/category/0/1?page=1&pageSize=200&keyword=iPhone%2018"
UNOPENED = "未開封品"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Mỗi dòng: tên (div.font-bold) | "未開封品 236,000円" | "開封新品 …円".
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for row in soup.select("tr"):
        name = row.select_one("div.font-bold")
        label = row.find("span", string=lambda s: s and s.strip() == UNOPENED)
        price = label.find_next_sibling("span") if label else None
        if not name or not price:
            continue
        offer = offer_from_name(name.get_text(" ", strip=True), parse_price(price.get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
