from bs4 import BeautifulSoup

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import parse_price
from crawler.shops.common import dedupe, kanji_colors, offers_from_base

# Bài "iPhone/スマートフォン 買取価格表", cập nhật mỗi ngày. Giá là giá máy chưa mở hộp.
URL = "https://kaitori-base.com/?p=9907"


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    # Dòng dạng "18 ProMax 256GB | 257,500 | 青,黒-20,000、銀-24,000" (không có chữ iPhone).
    soup = BeautifulSoup(raw, "html.parser")
    offers = []
    for row in soup.select("table tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        offers += offers_from_base(
            "iPhone " + cells[0].get_text(" ", strip=True),
            parse_price(cells[1].get_text()),
            cells[2].get_text(" ", strip=True),
            kanji_colors(colors),
        )
    return dedupe(offers)
