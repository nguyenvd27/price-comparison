from crawler.normalize import parse_deductions


def test_each_color_own_amount(colors):
    text = "シルバー -32000/\nグレイシャー -27000/\nブラック -26000"
    assert parse_deductions(text, colors) == {
        "burgundy": 0, "glacier": -27000, "black": -26000, "silver": -32000,
    }


def test_group_shares_amount(colors):
    assert parse_deductions("シルバー/グレイシャー/ブラック -22000", colors) == {
        "burgundy": 0, "glacier": -22000, "black": -22000, "silver": -22000,
    }


def test_two_groups(colors):
    assert parse_deductions("シルバー/グレイシャー -18000 ブラック-11000", colors) == {
        "burgundy": 0, "glacier": -18000, "black": -11000, "silver": -18000,
    }


def test_japanese_commas_and_suffix(colors):
    text = "グレイシャー 、ブラック、シルバー -34,000(開封済・未開封)"
    assert parse_deductions(text, colors) == {
        "burgundy": 0, "glacier": -34000, "black": -34000, "silver": -34000,
    }


def test_yen_suffix_halfwidth_comma(colors):
    text = "ブラック-27,000円､グレイシャー-28,000円､シルバー-32,000円"
    assert parse_deductions(text, colors) == {
        "burgundy": 0, "glacier": -28000, "black": -27000, "silver": -32000,
    }


def test_unicode_minus(colors):
    assert parse_deductions("ブラック −11000", colors)["black"] == -11000


def test_deductions_only_one_color_buyable(colors):
    assert parse_deductions("バーガンディのみ 他色買取不可", colors) == {
        "burgundy": 0, "glacier": None, "black": None, "silver": None,
    }


def test_empty_text_means_all_base_price(colors):
    assert parse_deductions("", colors) == {
        "burgundy": 0, "glacier": 0, "black": 0, "silver": 0,
    }
