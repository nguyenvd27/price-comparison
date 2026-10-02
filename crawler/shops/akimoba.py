from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

URL = "https://akiba-mobile.co.jp/"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Bảng giá trên trang chủ: tên máy | tình trạng | giá.
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for row in soup.select("tr"):
        cells = row.find_all("td")
        if len(cells) != 3 or "未開封" not in cells[1].get_text():
            continue
        offer = offer_from_name(cells[0].get_text(" ", strip=True), parse_price(cells[2].get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
