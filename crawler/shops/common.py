from crawler.models import Offer
from crawler.normalize import is_pro_max, parse_capacity, parse_color, parse_deductions, variant_id


def offer_from_name(name: str, price: int | None, colors: dict[str, list[str]]) -> Offer | None:
    """Cửa hàng ghi mỗi màu một dòng, ví dụ "iPhone 18 Pro Max 256GB ブラック"."""
    capacity = parse_capacity(name)
    color = parse_color(name, colors)
    if not (is_pro_max(name) and capacity and color and price):
        return None
    return Offer(variant_id(capacity, color), price)


def offers_from_base(name: str, base_price: int | None, remark: str, colors: dict[str, list[str]]) -> list[Offer]:
    """Cửa hàng ghi một giá gốc cho mỗi dung lượng, kèm ghi chú trừ tiền theo màu."""
    capacity = parse_capacity(name)
    if not (is_pro_max(name) and capacity and base_price):
        return []
    deltas = parse_deductions(remark, colors)
    return [
        Offer(variant_id(capacity, color), base_price + delta)
        for color, delta in deltas.items()
        if delta is not None
    ]


def dedupe(offers: list[Offer]) -> list[Offer]:
    """Giữ offer đầu tiên của mỗi biến thể (bảng chính luôn nằm trước)."""
    seen = set()
    result = []
    for offer in offers:
        if offer.variant not in seen:
            seen.add(offer.variant)
            result.append(offer)
    return result


# Vài cửa hàng viết tắt màu bằng một chữ Hán ("青,黒-20,000"). Chỉ dùng trong parser của các cửa hàng đó,
# vì dùng chung cho mọi cửa hàng thì một chữ dễ khớp nhầm.
KANJI_COLORS = {"burgundy": ["紫", "赤"], "glacier": ["青"], "black": ["黒"], "silver": ["銀", "白"]}


def kanji_colors(colors: dict[str, list[str]]) -> dict[str, list[str]]:
    return {color: KANJI_COLORS.get(color, []) for color in colors}
