import json

from crawler.http import get_text
from crawler.models import Offer
from crawler.normalize import model_colors, parse_capacity, parse_color, parse_model, variant_id
from crawler.shops.common import real_price

URL = (
    "https://www.1-chome.com/api/keitai/listPage?accCode=&page=1&size=50&keyword="
    "&isImpo=false&isCampaign=false&cateCode=eOd8WFZllXmBd3Rt&kbNames=&cateName=&isImpoCate=false"
)


DUO_URL = URL.replace("cateCode=eOd8WFZllXmBd3Rt", "cateCode=DtVXYic3qit6ckmN")  # iPhone Duo


def fetch(session) -> str:
    return json.dumps({"pages": [json.loads(get_text(session, url)) for url in (URL, DUO_URL)]}, ensure_ascii=False)


def items_of(raw: str) -> list[dict]:
    data = json.loads(raw)
    items = []
    for page in data.get("pages", [data]):
        if page.get("code") != 200:
            raise ValueError(f"API trả về code {page.get('code')}: {page.get('msg')}")
        items += page["data"]["content"]
    return items


def parse(raw: str, colors: dict[str, list[str]]) -> list[Offer]:
    offers = []
    for item in items_of(raw):
        title = item.get("title") or ""
        capacity = parse_capacity(title)
        unopened = next(
            (d for d in item.get("goodsKbDetails") or [] if d.get("kbDetailName") == "未開封"),
            None,
        )
        model = parse_model(title)
        if not (model and capacity and unopened and real_price(unopened.get("kbDetailPrice"))):
            continue
        for option in item.get("keitaiColorOptions") or []:
            color = parse_color(option.get("color") or "", model_colors(colors, model))
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
            offers.append(Offer(variant_id(capacity, color, model), unopened["kbDetailPrice"] + (var_price or 0)))
    return offers
