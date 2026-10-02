import html
import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.pokemon.match import match_item
from crawler.shops.common import dedupe

API = "https://runto666.com/wp-json/wc/store/v1/products"
PRODUCTS = API + "?category=108&per_page=100"  # 108 = ポケモンカード
SHRINK = "ari"  # biến thể "シュリンク有"


def shrink_variation(product: dict) -> int | None:
    for variation in product.get("variations") or []:
        if any(a.get("value") == SHRINK for a in variation.get("attributes") or []):
            return variation["id"]
    return None


def fetch(session) -> str:
    products = json.loads(get_text(session, PRODUCTS))
    ids = [vid for vid in (shrink_variation(p) for p in products if p["type"] == "variable") if vid]
    variations = json.loads(get_text(session, f"{API}?type=variation&per_page=100&include={','.join(map(str, ids))}")) if ids else []
    return json.dumps({"products": products, "variations": variations}, ensure_ascii=False)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    data = json.loads(raw)
    variation_price = {v["id"]: parse_price(v["prices"]["price"]) for v in data["variations"]}
    offers = []
    for product in data["products"]:
        if product["type"] == "variable":
            price = variation_price.get(shrink_variation(product))
        elif product["type"] == "simple":
            price = parse_price(product["prices"]["price"])
        else:
            continue
        item = match_item(html.unescape(product["name"]), None, items)
        if item and price:
            offers.append(Offer(item, price))
    return dedupe(offers)
