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
            for match in re.finditer(re.escape(nfkc(alias)), normalized):
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
