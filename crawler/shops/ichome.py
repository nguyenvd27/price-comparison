import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import is_pro_max, parse_capacity, parse_color, variant_id

URL = (
    "https://www.1-chome.com/api/keitai/listPage?accCode=&page=1&size=50&keyword="
    "&isImpo=false&isCampaign=false&cateCode=eOd8WFZllXmBd3Rt&kbNames=&cateName=&isImpoCate=false"
)


def fetch(session) -> str:
    return get_text(session, URL)


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    data = json.loads(raw)
    if data.get("code") != 200:
        raise ValueError(f"API trả về code {data.get('code')}: {data.get('msg')}")
    offers = []
    for item in data["data"]["content"]:
        title = item.get("title") or ""
        capacity = parse_capacity(title)
        unopened = next(
            (d for d in item.get("goodsKbDetails") or [] if d.get("kbDetailName") == "未開封"),
            None,
        )
        if not (is_pro_max(title) and capacity and unopened):
            continue
        for option in item.get("keitaiColorOptions") or []:
            color = parse_color(option.get("color") or "", colors)
            if not color:
                continue
            var_price = next(
                (
                    rel.get("varPrice")
                    for rel in option.get("keitaiKbDetailColorRels") or []
                    if rel.get("keitaiKbDetailId") == unopened["allGoodsKbDetailId"]
                ),
                None,
            )
            offers.append(Offer(variant_id(capacity, color), unopened["kbDetailPrice"] + (var_price or 0)))
    return offers
