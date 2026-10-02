from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

# Danh mục "シュリンクあり"; hàng mới ở các trang đầu.
URL = "https://kaitori-oku.jp/category.html?cat1=340&cat2=363&cat3=367"
MAX_PAGES = 3


def fetch(session) -> str:
    return "\n".join(get_text(session, f"{URL}&page={page}") for page in range(1, MAX_PAGES + 1))


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("div.proItem"):
        name = card.select_one("h4.tit")
        price = card.select_one(".price")
        jan = card.select_one(".sn")
        if not name or not price:
            continue
        value = parse_price(price.get_text())  # "問い合わせ" → None
        item = match_item(name.get_text(" ", strip=True), clean_jan(jan.get_text() if jan else ""), items)
        if item and value:
            offers.append(Offer(item, value))
    return dedupe(offers)
