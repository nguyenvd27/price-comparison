from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, offer_from_name

# Trang tổng hợp iPhone 18 (Pro, Pro Max, Duo) trên một trang.
# Từ 2026-10-26 các trang danh mục (/category/0301070, /category/0301071) ngắt kết nối với crawler.
URL = "https://www.morimori-kaitori.jp/iphone18"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Trang /iphone18: mỗi sản phẩm là article.mm1551-ip18-card, giá máy mới ở data-mm-price.
    # Trang danh mục (giao diện từ 2026-10-08): div.mm1551-prow, giá ở data-cond-new-price.
    # (Các thẻ article.mm1551-hotcard phía trên chỉ là phần "nổi bật", trùng với danh sách này.)
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    rows = [(i.select_one(".mm1551-ip18-card__name"), i.get("data-mm-price")) for i in soup.select("article.mm1551-ip18-card")]
    rows += [(i.select_one(".mm1551-prow__name"), i.get("data-cond-new-price")) for i in soup.select("div.mm1551-prow")]
    for name, price in rows:
        if not name or not price:
            continue
        offer = offer_from_name(name.get_text(" ", strip=True), parse_price(price), colors)
        if offer:
            offers.append(offer)
    return dedupe(offers)
