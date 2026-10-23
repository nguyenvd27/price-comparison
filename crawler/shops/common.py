from crawler.models import Offer
from crawler.normalize import Colors, model_colors, parse_capacity, parse_color, parse_deductions, parse_model, variant_id

# Giá dưới mức này là giá giữ chỗ (ví dụ 999円 khi máy chưa mở bán), không phải giá thu mua thật.
PLACEHOLDER_BELOW = 10_000


def real_price(price: int | None) -> bool:
    return bool(price) and price >= PLACEHOLDER_BELOW


def offer_from_name(name: str, price: int | None, colors: dict[str, list[str]]) -> Offer | None:
    """Cửa hàng ghi mỗi màu một dòng, ví dụ "iPhone 18 Pro Max 256GB ブラック" hoặc "iPhone Duo 256GB Star White"."""
    model = parse_model(name)
    if not model:
        return None
    capacity = parse_capacity(name)
    color = parse_color(name, model_colors(colors, model))
    if not (capacity and color and real_price(price)):
        return None
    return Offer(variant_id(capacity, color, model), price)


def offers_from_base(name: str, base_price: int | None, remark: str, colors: dict[str, list[str]]) -> list[Offer]:
    """Cửa hàng ghi một giá gốc cho mỗi dung lượng, kèm ghi chú trừ tiền theo màu."""
    model = parse_model(name)
    capacity = parse_capacity(name)
    if not (model and capacity and real_price(base_price)):
        return []
    deltas = parse_deductions(remark, model_colors(colors, model))
    return [
        Offer(variant_id(capacity, color, model), base_price + delta)
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
    # Giữ bảng dòng máy → màu (Colors.models) để không gán màu của Duo cho 18 Pro Max.
    return Colors(
        {color: KANJI_COLORS.get(color, []) for color in colors},
        models=getattr(colors, "models", None),
        jans=getattr(colors, "jans", None),
    )
