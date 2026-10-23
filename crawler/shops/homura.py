import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.shops.common import dedupe, offer_from_name

# Từ 2026-10-12 trang web dựng bằng JavaScript; giá lấy từ API công khai mà trang gọi.
API = "https://api.kaitori-homura.com/api/v1/products?product_sub_category_id={sub}&page={page}"
SUB_CATEGORIES = [192, 194]  # iPhone 18 Pro Max, iPhone Duo
MAX_PAGES = 3  # 20 sản phẩm/trang, gồm cả hàng đã mở hộp
# Trang hiển thị cho người dùng (link trong catalog).
URL = (
    "https://kaitori-homura.com/products"
    "?q%5Bproduct_sub_category_id_eq%5D=192&q%5Bproduct_sub_category_product_category_id_eq%5D=10"
)


def fetch_pages(session, sub: int) -> list[dict]:
    pages = []
    for page in range(1, MAX_PAGES + 1):
        data = json.loads(get_text(session, API.format(sub=sub, page=page)))
        pages.append(data)
        if page >= (data.get("meta") or {}).get("total_pages", 1):
            break
    return pages


def fetch(session) -> str:
    return json.dumps({"pages": [p for sub in SUB_CATEGORIES for p in fetch_pages(session, sub)]}, ensure_ascii=False)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    offers = []
    for page in json.loads(raw)["pages"]:
        for product in page.get("data") or []:
            name = " ".join((product.get("name") or "").split())
            if "未開封" not in name:  # bỏ "【開封open】…"
                continue
            offer = offer_from_name(name, product.get("price"), colors)
            if offer:
                offers.append(offer)
    return dedupe(offers)
