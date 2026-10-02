from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

BASE = "https://www.morimori-kaitori.jp"
CATEGORIES = ["/category/2401010", "/category/2401001"]  # MEGA, SV
MAX_PAGES = 3  # mỗi danh mục; hàng mới ở trang đầu


def fetch(session) -> str:
    pages = []
    for path in CATEGORIES:
        url = BASE + path
        for _ in range(MAX_PAGES):
            html = get_text(session, url)
            pages.append(html)
            nxt = BeautifulSoup(html, "html.parser").select_one("ul.pagination li.next a")
            if not nxt:
                break
            url = urljoin(BASE, nxt["href"])
    return "\n".join(pages)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("div[id$='-products'] .product-item"):
        name = card.select_one(".product-details-name")
        price = card.select_one(".price-normal-number")
        details = card.select_one(".product-details")
        if not name or not price:
            continue
        jan = clean_jan(details.get_text(" ") if details else "")
        item = match_item(name.get_text(" ", strip=True), jan, items)
        value = parse_price(price.get_text())
        if item and value:
            offers.append(Offer(item, value))
    return dedupe(offers)
