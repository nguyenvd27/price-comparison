from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

URL = "https://iphonekaitori.tokyo/series/iphone"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Giá trên trang là giá máy chưa mở hộp ("開封済み未使用品…は買取不可").
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("div.pro_list"):
        name = card.select_one("li.sub-pro-name a")
        price = card.select_one("li.sub-pro-jia span")
        if not name or not price:
            continue
        offer = offer_from_name(name.get_text(strip=True), parse_price(price.get_text()), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
