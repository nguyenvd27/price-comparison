import pytest

from crawler.pokemon.match import clean_jan, match_item

ITEMS = [
    {"id": "mega-30th-futuristic", "jan": ["4521329463872"], "aliases": ["FUTURISTIC BOX"], "exclude": []},
    {"id": "mega-30th", "jan": ["4521329462424"], "aliases": ["30th CELEBRATION"], "exclude": ["FUTURISTIC"]},
    {"id": "sv-black-bolt", "jan": ["4521329427768"], "aliases": ["ブラックボルト"], "exclude": []},
    {"id": "mega-inferno-x", "jan": ["4521329431529", "4521329431512"], "aliases": ["インフェルノX"], "exclude": []},
    {"id": "sv-151", "jan": ["4521329346038"], "aliases": ["ポケモンカード151", "151 BOX", "SV2a"], "exclude": []},
]


@pytest.mark.parametrize("name, jan, expected", [
    ("ポケモンカードゲーム MEGA 拡張パック 30th CELEBRATION BOX [M6a]", "4521329462424", "mega-30th"),
    ("MEGA 30th CELEBRATION FUTURISTIC BOX", "4521329463872", "mega-30th-futuristic"),
    ("インフェルノX m2 BOX", "4521329431512", "mega-inferno-x"),          # JAN phụ của オク
    ("ブラックボルト デラックス BOX", "4521329427300", None),              # JAN lạ (bản DX)
    ("拡張パック「30th CELEBRATION」(M6a)", None, "mega-30th"),           # theo tên
    ("ポケモンカードゲーム MEGA 30th CELEBRATION FUTURISTIC BOX", None, "mega-30th-futuristic"),
    ("拡張パックデラックス「ブラックボルト」(SV11B)", None, None),          # DX bị loại
    ("【BOX】ブラックボルトDX", None, None),
    ("強化拡張パック「ポケモンカード151」(SV2a)", None, "sv-151"),
    ("拡張パック「ドラゴンストーム」(SM6a)", None, None),                   # không có alias nào
])
def test_match_by_jan_then_name(name, jan, expected):
    assert match_item(name, jan, ITEMS) == expected


@pytest.mark.parametrize("name", [
    "シュリンクなし MEGA 拡張パック 30th CELEBRATION BOX",
    "30th CELEBRATION BOX シュリンク無し",
    "MEGA 拡張パック 30th CELEBRATION カートン",
    "ポケモンカードゲーム MEGA 30th CELEBRATION プレミアムデッキセット エーフィ・ブラッキー",
    "ポケモンカードゲーム MEGA 30th CELEBRATION カードセット フシギダネ・ヒトカゲ・ゼニガメ",
    "拡張パック バトルパートナーズ BOX プロモカードなし",
    "30th CELEBRATION 開封済み",
])
def test_non_box_or_no_shrink_is_rejected_even_with_known_jan(name):
    assert match_item(name, "4521329462424", ITEMS) is None
    assert match_item(name, None, ITEMS) is None


def test_name_matching_two_items_is_rejected():
    items = ITEMS + [{"id": "dup", "jan": ["0"], "aliases": ["30th CELEBRATION"], "exclude": ["FUTURISTIC"]}]
    assert match_item("30th CELEBRATION BOX", None, items) is None


def test_unopened_is_not_mistaken_for_opened():
    assert match_item("30th CELEBRATION BOX 新品未開封", None, ITEMS) == "mega-30th"


@pytest.mark.parametrize("text, expected", [
    ("JAN: 4521329462424", "4521329462424"),
    ("114521329462424", "4521329462424"),      # ホムラ ghép thêm 2 chữ số phía trước
    ("‎4521329431161", "4521329431161"),  # 一丁目 có ký tự ẩn
    ("JAN: 8821329462424", "8821329462424"),
    ("", None),
    (None, None),
])
def test_clean_jan(text, expected):
    assert clean_jan(text) == expected


@pytest.mark.parametrize("name", [
    "ポケモンカードゲーム MEGA 30th CELEBRATION スペシャルBOX",
    "30th CELEBRATION 1パック",
    "拡張パック「30th CELEBRATION」バラ 1P",
    "30th CELEBRATION パック 1pack",
])
def test_special_box_and_single_packs_are_rejected(name):
    assert match_item(name, None, ITEMS) is None


def test_box_names_with_pack_word_still_match():
    assert match_item("ポケモンカードゲーム MEGA 拡張パック「30th CELEBRATION」", None, ITEMS) == "mega-30th"
