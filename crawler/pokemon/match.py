"""Ghép tên/JAN sản phẩm của từng cửa hàng với BOX trong catalog Pokémon."""
import re
import sys
import unicodedata

# Không phải BOX còn màng co: không màng co, thùng, deck/set, bản DX, スペシャルBOX, gói lẻ, mất thẻ khuyến mãi, đã mở.
EXCLUDE = [
    "シュリンクなし", "シュリンク無", "カートン", "デッキ", "セット", "デラックス", "dx", "スペシャル",
    "プロモなし", "プロモカードなし", "開封済", "開封品", "パック単品", "バラ",
]
# Gói lẻ: "1パック", "1P", "1pack" (tên BOX nào cũng có chữ "拡張パック" nên không loại chữ パック nói chung).
SINGLE_PACK = re.compile(r"(?<!\d)1(パック|pack|p)(?![a-z])")


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text or "")).lower()


def clean_jan(text: str | None) -> str | None:
    runs = [run for run in re.findall(r"\d+", unicodedata.normalize("NFKC", text or "")) if len(run) >= 13]
    return max(runs, key=len)[-13:] if runs else None


def excluded(name: str) -> bool:
    text = normalize(name).replace("未開封", "")
    return any(normalize(word) in text for word in EXCLUDE) or bool(SINGLE_PACK.search(text))


def match_item(name: str, jan: str | None, items: list[dict]) -> str | None:
    if excluded(name):
        return None
    if jan:
        found = [item["id"] for item in items if jan in item["jan"]]
        return found[0] if len(found) == 1 else None
    text = normalize(name)
    found = [
        item["id"]
        for item in items
        if any(normalize(alias) in text for alias in item["aliases"])
        and not any(normalize(word) in text for word in item.get("exclude", []))
    ]
    if len(found) > 1:
        print(f"Cảnh báo: {name!r} khớp nhiều BOX {found}, bỏ qua", file=sys.stderr)
    return found[0] if len(found) == 1 else None
