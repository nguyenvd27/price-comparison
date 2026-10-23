from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan
from crawler.shops.common import dedupe, real_price

BASE = "https://mobileone.co.jp/sell.html?cat1=140&cat2=144&cat3="
URLS = [BASE + "446", BASE + "447"]  # iPhone 18 Pro Max, iPhone Duo


def fetch(session) -> str:
    return "\n".join(get_text(session, url) for url in URLS)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Mỗi dung lượng chỉ có 1 giá "新品", không ghi màu; JAN cho biết đó là màu nào (tra trong catalog).
    jans = getattr(colors, "jans", {})
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for item in soup.select("div.list2 li"):
        jan = clean_jan(item.select_one(".splist").get_text() if item.select_one(".splist") else "")
        new = next((d for d in item.select(".hot4") if "新品" in d.get_text()), None)
        variant = jans.get(jan)
        price = parse_price(new.get_text().replace("新品", "")) if new else None
        if variant and real_price(price):
            offers.append(Offer(variant, price))
    return dedupe(offers)
