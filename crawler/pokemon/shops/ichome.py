import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

URL = (
    "https://www.1-chome.com/api/goods/listPage?accCode=&page=1&size=100&keyword="
    "&isImpo=false&isCampaign=false&cateCode=IIzyMdayU5wp7T4G&kbNames=&cateName="
)
SHRINK = "シュリンク有"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    data = json.loads(raw)
    if data.get("code") != 200:
        raise ValueError(f"API trả về code {data.get('code')}: {data.get('msg')}")
    page = data["data"]
    if page["totalElements"] > page["size"]:
        raise ValueError(f"API có {page['totalElements']} sản phẩm, nhiều hơn 1 trang ({page['size']})")
    offers = []
    for product in page["content"]:
        price = next(
            (d["kbDetailPrice"] for d in product.get("goodsKbDetails") or [] if (d.get("kbDetailName") or "").strip() == SHRINK),
            None,
        )
        item = match_item(product.get("title") or "", clean_jan(product.get("jan")), items)
        if item and price:
            offers.append(Offer(item, price))
    return dedupe(offers)
