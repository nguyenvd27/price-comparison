import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.shops.common import dedupe, offer_from_name

# Không đọc trang /category/1/747: HTML ở đó là bản render sẵn cho SEO, chỉ tạo lại mỗi ngày một lần
# ("毎日更新") nên lệch với giá thật. Giá thật trên trang được trình duyệt lấy từ API này.
URL = "https://www.kaitorishouten-co.jp/api/v1/products?per_page=100&perPage=100&page=1&category_id=747&sort=enhanced_first"
NEW_LABEL = "新品"  # máy mới chưa kích hoạt; các nhãn "新品 開封済…", "中古…" bị bỏ qua


DUO_URL = URL.replace("category_id=747", "category_id=748")  # iPhone Duo


def fetch(session) -> str:
    return json.dumps({"pages": [json.loads(get_text(session, url)) for url in (URL, DUO_URL)]}, ensure_ascii=False)


def items_of(raw: str) -> list[dict]:
    data = json.loads(raw)
    items = []
    for page in data.get("pages", [data]):
        if page["total"] > page["per_page"]:
            raise ValueError(f"API có {page['total']} sản phẩm, nhiều hơn 1 trang ({page['per_page']})")
        items += page["items"]
    return items


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    offers = []
    for item in items_of(raw):
        if item.get("price_undecided"):
            continue
        price = next((p["amount"] for p in item.get("prices") or [] if p.get("label") == NEW_LABEL), None)
        offer = offer_from_name(item.get("name") or "", price, colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
