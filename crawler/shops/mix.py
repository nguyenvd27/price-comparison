from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offers_from_base

HOME = "https://mobile-mix.jp/"
URL = "https://mobile-mix.jp/?category=7"


def fetch(session) -> str:
    # Lần đầu chưa có cookie, MIX chuyển hướng sang /cookie-error, nên phải gọi trang chủ trước để nhận cookie.
    get_text(session, HOME)
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for row in soup.select("tr[id]"):
        product = row.select_one('td.product[name="model"]')
        price = row.select_one("td.price")
        detail = row.find_next_sibling("tr")
        cells = detail.find_all("td") if detail else []
        if not product or not price or len(cells) < 2 or "未開封" not in cells[0].get_text():
            continue
        offers += offers_from_base(
            product.get_text(strip=True),
            parse_price(price.get_text()),
            cells[1].get_text(" ", strip=True),
            colors,
        )
    return dedupe(offers)
