from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

BASE = "https://kaitori-oku.jp/category.html?cat1=222&cat2="
URLS = [BASE + "778", BASE + "780"]  # iPhone 18 Pro Max, iPhone Duo


def fetch(session) -> str:
    return "\n".join(get_text(session, url) for url in URLS)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("div.proItem"):
        name = card.select_one("h4.tit")
        price = card.select_one(".price")
        if not name or not price:
            continue
        offer = offer_from_name(" ".join(name.get_text().split()), parse_price(price.get_text()), colors)  # "問い合わせ" → None
        if offer:
            offers.append(offer)
    return dedupe(offers)
