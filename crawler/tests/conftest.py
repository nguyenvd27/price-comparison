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
