import pytest

COLORS = {
    "burgundy": ["バーガンディ", "Burgundy"],
    "glacier": ["グレイシャー", "グレイシャ", "Glacier"],
    "black": ["ブラック", "Black"],
    "silver": ["シルバー", "Silver"],
}


@pytest.fixture
def colors():
    return COLORS


@pytest.fixture
def colors_all():
    """Màu của cả 2 dòng máy, kèm bảng dòng máy → màu như crawl_colors() trả về khi Duo được crawl."""
    from crawler.normalize import Colors

    return Colors(
        {**COLORS, "nightsky": ["ナイトスカイ", "Night Sky"], "starwhite": ["スターホワイト", "Star White"]},
        models={"pm": list(COLORS), "duo": ["nightsky", "starwhite"]},
    )
