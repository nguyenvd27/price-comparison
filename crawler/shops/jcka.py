from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, kanji_colors, offers_from_base

URL = "https://www.jcka-mobile.co.jp/kisyu/iphone/"
# Dòng máy chưa mở hộp: "未開封 判定〇", hoặc kèm ghi chú như "未開封（郵送買取中止）17時まで".
# "判定△" là máy đang trả góp, bỏ qua.


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Mỗi dung lượng một bảng: "未開封 判定〇 | 青・黒・白-20,000 | 250,000円". 白 là シルバー.
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for post in soup.select("div.kaitori_price"):
        title = post.select_one(".vk_post_title")
        for row in post.select("tbody tr"):
            cells = row.find_all("td")
            label = cells[0].get_text(" ", strip=True) if cells else ""
            if not title or len(cells) < 3 or not label.startswith("未開封") or "△" in label:
                continue
            offers += offers_from_base(
                title.get_text(" ", strip=True),
                parse_price(cells[2].get_text()),
                cells[1].get_text(" ", strip=True),
                kanji_colors(colors),
            )
    return dedupe(offers)
