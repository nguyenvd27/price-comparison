import json
from urllib.parse import quote

from crawler.http import get_text
from crawler.models import Offer
from crawler.pokemon.match import match_item
from crawler.shops.common import dedupe

# Giá mua qua bưu điện (郵送買取), hạng S. Mỗi trang tối đa 100.
URL = "https://shinsoku-tcg.com/api/items?postal_only=true&sort=price_desc&type=BOX&brand=" + quote("ポケモン") + "&limit=100&page={page}"
MAX_PAGES = 5


def fetch(session) -> str:
    pages = []
    for page in range(MAX_PAGES):
        data = json.loads(get_text(session, URL.format(page=page)))
        pages.append(data)
        if not data.get("ok") or not data["data"]["has_more"]:
            break
    return json.dumps({"pages": pages}, ensure_ascii=False)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    offers = []
    for page in json.loads(raw)["pages"]:
        if not page.get("ok"):
            raise ValueError(f"API lỗi: {page.get('error')}")
        for product in page["data"]["items"]:
            item = match_item(product.get("name") or "", None, items)
            price = product.get("postal_purchase_price_s")
            if item and price:
                offers.append(Offer(item, price))
    return dedupe(offers)
