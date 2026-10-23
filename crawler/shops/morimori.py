from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

URL = "https://www.morimori-kaitori.jp/category/0301070"
DUO_URL = "https://www.morimori-kaitori.jp/category/0301071"  # iPhone Duo
MAX_PAGES = 5


def fetch_category(session, start: str) -> list[str]:
    pages = []
    url = start
    while url and len(pages) < MAX_PAGES:
        html = get_text(session, url)
        pages.append(html)
        next_link = BeautifulSoup(html, "html.parser").select_one("ul.pagination li.next a")
        url = urljoin(start, next_link["href"]) if next_link else None
    return pages


def fetch(session) -> str:
    return "\n".join(fetch_category(session, URL) + fetch_category(session, DUO_URL))


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Giao diện từ 2026-10-08: mỗi sản phẩm là div.mm1551-prow, giá máy mới ở data-cond-new-price.
    # (Các thẻ article.mm1551-hotcard phía trên chỉ là phần "nổi bật", trùng với danh sách này.)
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for item in soup.select("div.mm1551-prow"):
        name = item.select_one(".mm1551-prow__name")
        price = item.get("data-cond-new-price")
        if not name or not price:
            continue
        offer = offer_from_name(name.get_text(" ", strip=True), parse_price(price), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
