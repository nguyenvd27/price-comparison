from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offers_from_base

URL = "https://www.mobile-ichiban.com/Prod/1/01/40"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for price in soup.select('label[id^="NewPrice_"]'):
        card = price.find_parent("div", class_="card")
        if not card:
            continue
        labels = card.select("label.hideText")
        name = labels[0].get("title", "") if labels else ""
        condition = labels[1].get("title", "") if len(labels) > 1 else ""
        if "未開封" not in condition:
            continue
        remark = card.select_one(".my-prod-remarks")
        offers += offers_from_base(
            name,
            parse_price(price.get_text()),
            remark.get_text(" ", strip=True) if remark else "",
            colors,
        )
    return dedupe(offers)
