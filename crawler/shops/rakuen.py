import re

from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import find_colors, is_pro_max, nfkc, parse_capacity, parse_price, variant_id
from crawler.shops.common import dedupe, kanji_colors

URL = "https://www.keitairakuen.com/product-category/keitai/iphone/iphone18-%e3%82%b7%e3%83%aa%e3%83%bc%e3%82%ba/iphone18-promax/"
AMOUNT = re.compile(r"(-?)\s*(\d[\d,]{3,})")


def fetch(session) -> str:
    return get_text(session, URL)


def card_offers(name: str, lines: list[str], new_price: int, colors: dict[str, list[str]]) -> list[Offer]:
    """Mỗi dòng "黒/青 231,000" là giá riêng của các màu đó ("青/銀-2000" là trừ từ giá 新品).

    Màu không được nhắc tới (thường là バーガンディ) lấy giá 新品.
    """
    prices = {color: new_price for color in colors}
    for line in lines:
        listed = [color for _, color in find_colors(line, kanji_colors(colors))]
        amount = AMOUNT.search(nfkc(line))
        if not listed or not amount:
            continue
        value = int(amount.group(2).replace(",", ""))
        for color in listed:
            prices[color] = new_price - value if amount.group(1) else value
    capacity = parse_capacity(name)
    return [Offer(variant_id(capacity, color), price) for color, price in prices.items()]


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Nhãn "在庫切れ" có trên mọi sản phẩm của trang (thiết lập chung), không có nghĩa là ngừng thu mua.
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for card in soup.select("div.product-small.col"):
        title = card.select_one("p.product-title")
        price = card.select_one("p.global-attribute-price")
        lines = [p.get_text(" ", strip=True) for p in card.select("div.woocommerce-loop-description p")]
        if not title or not price or not any("未開封" in line and "開封済" not in line for line in lines):
            continue
        name = title.get_text(" ", strip=True)
        new_price = parse_price(price.get_text())
        if is_pro_max(name) and parse_capacity(name) and new_price:
            offers += card_offers(name, lines, new_price, colors)
    return dedupe(offers)
