import re
import unicodedata

CAPACITIES = {"256GB": "256", "512GB": "512", "1TB": "1tb", "2TB": "2tb"}


def nfkc(text: str | None) -> str:
    return unicodedata.normalize("NFKC", text or "")


def is_pro_max(name: str) -> bool:
    compact = re.sub(r"\s+", "", nfkc(name)).lower()
    return "iphone18promax" in compact


def parse_capacity(name: str) -> str | None:
    match = re.search(r"(\d+)\s*(GB|TB)", nfkc(name), re.IGNORECASE)
    if not match:
        return None
    return CAPACITIES.get(f"{match.group(1)}{match.group(2).upper()}")


def find_colors(text: str, colors: dict[str, list[str]]) -> list[tuple[int, str]]:
    """Mọi vị trí xuất hiện tên màu trong text, sắp theo vị trí."""
    normalized = nfkc(text)
    found = set()
    for color, aliases in colors.items():
        for alias in aliases:
            for match in re.finditer(re.escape(nfkc(alias)), normalized, re.IGNORECASE):
                found.add((match.start(), color))
    return sorted(found)


def parse_color(name: str, colors: dict[str, list[str]]) -> str | None:
    found = find_colors(name, colors)
    return found[0][1] if found else None


def parse_price(text: str | None) -> int | None:
    digits = re.sub(r"\D", "", nfkc(text))
    return int(digits) if digits else None


def variant_id(capacity: str, color: str) -> str:
    return f"pm-{capacity}-{color}"


AMOUNT = re.compile(r"[-−‐]\s*(\d[\d,]*)")
ONLY_RULE = re.compile(r"のみ.*他色.*不可")


def parse_deductions(text: str, colors: dict[str, list[str]]) -> dict[str, int | None]:
    """Đọc ghi chú kiểu "シルバー/グレイシャー -18000 ブラック-11000".

    Mỗi số tiền áp cho các màu đứng ngay trước nó (chưa được gán).
    "Xのみ ... 不可" nghĩa là chỉ thu mua màu X, các màu khác là None.
    """
    normalized = nfkc(text)
    allowed = None
    if ONLY_RULE.search(normalized):
        allowed = {color for _, color in find_colors(normalized.split("のみ")[0], colors)}
    elif "不可" in normalized:
        # Ghi chú có "không thu mua" nhưng không theo mẫu đã biết: báo lỗi để giữ giá cũ,
        # thay vì lặng lẽ tính màu đó theo giá gốc.
        raise ValueError(f"Không hiểu ghi chú: {text!r}")

    result: dict[str, int | None] = {color: 0 for color in colors}
    tokens = [(pos, "color", color) for pos, color in find_colors(normalized, colors)]
    tokens += [(m.start(), "amount", int(m.group(1).replace(",", ""))) for m in AMOUNT.finditer(normalized)]
    pending: list[str] = []
    for _, kind, value in sorted(tokens, key=lambda token: token[0]):
        if kind == "color":
            pending.append(value)
        else:
            for color in pending:
                result[color] = -value
            pending = []
    if allowed is None and pending:
        raise ValueError(f"Không hiểu ghi chú: {text!r}")
    if allowed is not None:
        return {color: (result[color] if color in allowed else None) for color in colors}
    return result
