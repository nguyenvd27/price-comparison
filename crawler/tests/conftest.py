import pytest

COLORS = {
    "burgundy": ["バーガンディ"],
    "glacier": ["グレイシャー", "グレイシャ"],
    "black": ["ブラック"],
    "silver": ["シルバー"],
}


@pytest.fixture
def colors():
    return COLORS
