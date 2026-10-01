from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

URL = "https://www.morimori-kaitori.jp/category/0301070"
MAX_PAGES = 5


def fetch(session) -> str:
    pages = []
    url = URL
    while url and len(pages) < MAX_PAGES:
        html = get_text(session, url)
        pages.append(html)
        next_link = BeautifulSoup(html, "html.parser").select_one("ul.pagination li.next a")
        url = urljoin(URL, next_link["href"]) if next_link else None
    return "\n".join(pages)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for item in soup.select("#category-0301070-products .product-item"):
        name = item.select_one(".product-details-name")
        price = item.select_one(".price-normal-number")
        if not name or not price:
            continue
        offer = offer_from_name(name.get_text(" ", strip=True), parse_price(price.get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
