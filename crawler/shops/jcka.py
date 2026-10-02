from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, kanji_colors, offers_from_base

URL = "https://www.jcka-mobile.co.jp/kisyu/iphone/"
UNOPENED = "未開封 判定〇"  # chưa mở hộp, đã trả góp xong; "判定△" là đang trả góp


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
            if not title or len(cells) < 3 or cells[0].get_text(" ", strip=True) != UNOPENED:
                continue
            offers += offers_from_base(
                title.get_text(" ", strip=True),
                parse_price(cells[2].get_text()),
                cells[1].get_text(" ", strip=True),
                kanji_colors(colors),
            )
    return dedupe(offers)
