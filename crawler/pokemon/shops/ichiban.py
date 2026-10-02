import re

from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

URL = "https://www.mobile-ichiban.com/Prod/3/"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for price in soup.select('label[id^="NewPrice_"]'):
        card = price.find_parent("div", class_="card")
        if not card:
            continue
        labels = card.select("label.hideText")
        name = labels[0].get("title", "") if labels else ""
        remark = card.select_one(".my-prod-remarks")
        jan = clean_jan(" ".join(card.find_all(string=re.compile("JAN"))))
        # Ghi chú (ví dụ "シュリンクなし") nằm ngoài tên nên ghép vào để bộ ghép loại được.
        text = f"{name} {remark.get_text(' ', strip=True) if remark else ''}"
        item = match_item(text, jan, items)
        value = parse_price(price.get_text())
        if item and value and jan:
            offers.append(Offer(item, value))
    return dedupe(offers)
