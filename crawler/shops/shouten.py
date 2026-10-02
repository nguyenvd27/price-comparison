import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.shops.common import dedupe, offer_from_name

# Không đọc trang /category/1/747: HTML ở đó là bản render sẵn cho SEO, chỉ tạo lại mỗi ngày một lần
# ("毎日更新") nên lệch với giá thật. Giá thật trên trang được trình duyệt lấy từ API này.
URL = "https://www.kaitorishouten-co.jp/api/v1/products?per_page=100&perPage=100&page=1&category_id=747&sort=enhanced_first"
NEW_LABEL = "新品"  # máy mới chưa kích hoạt; các nhãn "新品 開封済…", "中古…" bị bỏ qua


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    data = json.loads(raw)
    if data["total"] > data["per_page"]:
        raise ValueError(f"API có {data['total']} sản phẩm, nhiều hơn 1 trang ({data['per_page']})")
    offers = []
    for item in data["items"]:
        if item.get("price_undecided"):
            continue
        price = next((p["amount"] for p in item.get("prices") or [] if p.get("label") == NEW_LABEL), None)
        offer = offer_from_name(item.get("name") or "", price, colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
