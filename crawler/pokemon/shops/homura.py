from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

# Danh mục "シュリンク有り" (BOX còn màng co).
URL = (
    "https://kaitori-homura.com/products"
    "?q%5Bproduct_sub_category_id_eq%5D=128&q%5Bproduct_sub_category_product_category_id_eq%5D=14"
)
MAX_PAGES = 3


def fetch(session) -> str:
    return "\n".join(get_text(session, f"{URL}&page={page}") for page in range(1, MAX_PAGES + 1))


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for title in soup.select("h5"):
        card = title.find_parent(lambda tag: tag.name == "div" and tag.select_one("span.text-lg"))
        if not card:
            continue
        # Dãy số trong thẻ là JAN có thêm 2 chữ số phía trước, ví dụ 114521329462424.
        jan = clean_jan(" ".join(span.get_text() for span in card.select("span.text-xs")))
        item = match_item(" ".join(title.get_text().split()), jan, items)
        value = parse_price(card.select_one("span.text-lg").get_text())
        if item and value:
            offers.append(Offer(item, value))
    return dedupe(offers)
