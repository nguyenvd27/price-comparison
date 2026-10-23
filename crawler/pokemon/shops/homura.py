import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.pokemon.match import clean_jan, match_item
from crawler.shops.common import dedupe

# Từ 2026-10-12 trang web dựng bằng JavaScript; giá lấy từ API công khai mà trang gọi.
# Danh mục 128 = "シュリンク有り" (BOX còn màng co).
API = "https://api.kaitori-homura.com/api/v1/products?product_sub_category_id=128&page={page}"
MAX_PAGES = 5


def fetch(session) -> str:
    pages = []
    for page in range(1, MAX_PAGES + 1):
        data = json.loads(get_text(session, API.format(page=page)))
        pages.append(data)
        if page >= (data.get("meta") or {}).get("total_pages", 1):
            break
    return json.dumps({"pages": pages}, ensure_ascii=False)


def parse(raw: str, items: list[dict]) -> list[Offer]:
    offers = []
    for page in json.loads(raw)["pages"]:
        for product in page.get("data") or []:
            # jan_code có thêm 2 chữ số phía trước, ví dụ 114521329462424.
            item = match_item(product.get("name") or "", clean_jan(product.get("jan_code")), items)
            price = product.get("price")
            if item and isinstance(price, int) and price > 0:
                offers.append(Offer(item, price))
    return dedupe(offers)
