"""Mỗi danh mục (iPhone, Pokémon…) khai báo nơi lưu dữ liệu, danh sách cửa hàng và giới hạn giá."""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from crawler.store import DATA_DIR


@dataclass(frozen=True)
class Category:
    id: str
    data_dir: Path
    shops: dict
    context: Callable[[dict], object]  # catalog -> thứ parser cần (màu iPhone, danh sách BOX…)
    price_range: tuple[int, int]


def crawl_colors(catalog: dict) -> dict[str, list[str]]:
    """Chỉ các màu thuộc dòng máy đang crawl, để parser không sinh giá cho màu của dòng máy khác."""
    wanted = {color for model in catalog["models"] if model["crawl"] for color in model["colors"]}
    return {color_id: color["aliases"] for color_id, color in catalog["colors"].items() if color_id in wanted}


def pokemon_items(catalog: dict) -> list[dict]:
    return catalog["items"]


def get_category(category_id: str) -> Category:
    if category_id == "iphone":
        from crawler.shops import SHOPS

        return Category("iphone", DATA_DIR, SHOPS, crawl_colors, (100_000, 1_000_000))
    if category_id == "pokemon":
        from crawler.pokemon.shops import SHOPS

        return Category("pokemon", DATA_DIR / "pokemon", SHOPS, pokemon_items, (1_000, 2_000_000))
    raise ValueError(f"Danh mục không tồn tại: {category_id}")
