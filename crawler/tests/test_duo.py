"""Crawl iPhone Duo cùng với 18 Pro Max (mở bán 2026-10-23)."""
import json

import pytest

from crawler.normalize import parse_model, variant_id
from crawler.shops import akimoba, ichome, rakuen
from crawler.shops.common import offer_from_name, offers_from_base


@pytest.mark.parametrize("name, expected", [
    ("iPhone Duo 256GB Star White", "duo"),
    ("Apple iPhoneDuo 1TB ナイトスカイ SIMフリー", "duo"),
    ("iPhone18 Pro Max 256GB Burgundy", "pm"),
    ("iPhone 18 Pro 256GB", None),
    ("iPhone 17 Pro Max 256GB", None),
])
def test_parse_model(name, expected):
    assert parse_model(name) == expected


def test_variant_id_has_model_prefix():
    assert variant_id("256", "burgundy") == "pm-256-burgundy"
    assert variant_id("2tb", "nightsky", "duo") == "duo-2tb-nightsky"


def test_offer_from_name_duo_and_no_cross_model_colors(colors_all):
    assert offer_from_name("iPhone Duo 512GB Night Sky", 400000, colors_all).variant == "duo-512-nightsky"
    # Màu của Pro Max không được gán cho Duo và ngược lại.
    assert offer_from_name("iPhone Duo 512GB Black", 400000, colors_all) is None
    assert offer_from_name("iPhone 18 Pro Max 512GB Night Sky", 280000, colors_all) is None


def test_placeholder_price_is_ignored(colors_all):
    assert offer_from_name("iPhone Duo 256GB Star White", 999, colors_all) is None
    assert offers_from_base("iPhone Duo 256GB", 999, "", colors_all) == []


def test_offers_from_base_uses_only_the_models_colors(colors_all):
    offers = {o.variant: o.price for o in offers_from_base("iPhone Duo 256GB", 380000, "スターホワイト-5,000", colors_all)}
    assert offers == {"duo-256-nightsky": 380000, "duo-256-starwhite": 375000}


def test_akimoba_duo_rows_and_placeholder(colors_all):
    raw = """<table>
    <tr><td>iPhone18 Pro Max 256GB Burgundy</td><td class="dt">未開封品</td><td class="p">256,000円</td></tr>
    <tr><td>iPhone Duo 256GB Star White</td><td class="dt">未開封品</td><td class="p">380,000円</td></tr>
    <tr><td>iPhone Duo 512GB Night Sky</td><td class="dt">未開封品</td><td class="p">999円</td></tr>
    </table>"""
    assert {o.variant: o.price for o in akimoba.parse(raw, colors_all)} == {
        "pm-256-burgundy": 256000, "duo-256-starwhite": 380000,
    }


def test_ichome_duo_item(colors_all):
    raw = json.dumps({"code": 200, "data": {"content": [{
        "title": "iPhone Duo 256GB",
        "goodsKbDetails": [{"allGoodsKbDetailId": 1, "kbDetailName": "未開封", "kbDetailPrice": 385000}],
        "keitaiColorOptions": [
            {"color": "ナイトスカイ", "keitaiKbDetailColorRels": [{"keitaiKbDetailId": 1, "varPrice": None}]},
            {"color": "スターホワイト", "keitaiKbDetailColorRels": [{"keitaiKbDetailId": 1, "varPrice": -5000}]},
        ],
    }]}})
    assert {o.variant: o.price for o in ichome.parse(raw, colors_all)} == {
        "duo-256-nightsky": 385000, "duo-256-starwhite": 380000,
    }


def test_rakuen_duo_card(colors_all):
    raw = """<div class="product-small col"><div class="col-inner">
    <p class="name product-title">iPhone Duo 256GB</p>
    <div class="woocommerce-loop-description"><p>SIM FREE 未開封</p></div>
    <span class="price"><p class="global-attribute-price">新品: ¥ 380,000</p></span>
    </div></div>"""
    assert {o.variant: o.price for o in rakuen.parse(raw, colors_all)} == {
        "duo-256-nightsky": 380000, "duo-256-starwhite": 380000,
    }


def test_kanji_color_shops_do_not_give_duo_colors_to_pro_max(colors_all):
    from pathlib import Path

    from crawler.shops import base, jcka

    fixtures = Path(__file__).parent / "fixtures"
    for shop, name in ((base, "base.html"), (jcka, "jcka.html")):
        variants = {o.variant for o in shop.parse((fixtures / name).read_text(encoding="utf-8"), colors_all)}
        assert variants and all(v.startswith("pm-") for v in variants), shop.__name__
        assert not any(v.endswith(("nightsky", "starwhite")) for v in variants), shop.__name__


class RecordingSession:
    """Session giả: ghi lại các URL được gọi, trả về nội dung rỗng hợp lệ."""

    def __init__(self, body="<html></html>"):
        self.calls = []
        self.body = body

    def get(self, url, timeout):
        self.calls.append(url)
        import requests

        response = requests.Response()
        response.status_code = 200
        response._content = self.body.encode()
        response.encoding = "utf-8"
        response.url = url
        return response


@pytest.mark.parametrize("module_name, duo_part", [
    ("morimori", "/category/0301071"),
    ("ichiban", "/Prod/1/01/41"),
    ("homura", "product_sub_category_id_eq%5D=194"),
])
def test_html_shops_also_fetch_duo_page(module_name, duo_part):
    import importlib

    module = importlib.import_module(f"crawler.shops.{module_name}")
    session = RecordingSession()
    module.fetch(session)
    assert any(duo_part in url for url in session.calls), session.calls


def test_shouten_fetches_and_parses_both_categories(colors_all):
    from crawler.shops import shouten

    page = '{"page": 1, "per_page": 100, "total": 0, "items": []}'
    session = RecordingSession(page)
    shouten.fetch(session)
    assert any("category_id=747" in u for u in session.calls) and any("category_id=748" in u for u in session.calls)
    duo = {"page": 1, "per_page": 100, "total": 1, "items": [
        {"name": "iPhone Duo 256GB ナイトスカイ MK254J/A SIMフリー", "prices": [{"label": "新品", "amount": 440000}]}]}
    raw = json.dumps({"pages": [json.loads(page), duo]})
    assert {o.variant: o.price for o in shouten.parse(raw, colors_all)} == {"duo-256-nightsky": 440000}


def test_ichome_fetches_and_parses_both_categories(colors_all):
    page = '{"code": 200, "data": {"content": []}}'
    session = RecordingSession(page)
    ichome.fetch(session)
    assert any("eOd8WFZllXmBd3Rt" in u for u in session.calls) and any("DtVXYic3qit6ckmN" in u for u in session.calls)
    duo = {"code": 200, "data": {"content": [{
        "title": "iPhone Duo 512GB",
        "goodsKbDetails": [{"allGoodsKbDetailId": 7, "kbDetailName": "未開封", "kbDetailPrice": 475000}],
        "keitaiColorOptions": [{"color": "スターホワイト", "keitaiKbDetailColorRels": []}],
    }]}}
    raw = json.dumps({"pages": [json.loads(page), duo]})
    assert {o.variant: o.price for o in ichome.parse(raw, colors_all)} == {"duo-512-starwhite": 475000}


def test_base_reads_18_duo_rows(colors_all):
    from crawler.shops import base

    raw = "<table><tr><td>18 Duo 256GB</td><td>440,000</td><td></td></tr><tr><td>18 Duo 512GB</td><td></td><td></td></tr></table>"
    assert {o.variant: o.price for o in base.parse(raw, colors_all)} == {
        "duo-256-nightsky": 440000, "duo-256-starwhite": 440000,
    }


def test_jcka_accepts_unopened_row_with_note(colors_all):
    from crawler.shops import jcka

    raw = """<div class="kaitori_price"><h5 class="vk_post_title">iPhone Duo[256GB]</h5><table><tbody>
    <tr><td>未開封（郵送買取中止）17時まで</td><td>全色</td><td>440,000円</td></tr>
    <tr><td>未開封 判定△</td><td>全色</td><td>430,000円</td></tr>
    <tr><td>開封</td><td>全色</td><td>390,000円</td></tr></tbody></table></div>"""
    assert {o.variant: o.price for o in jcka.parse(raw, colors_all)} == {
        "duo-256-nightsky": 440000, "duo-256-starwhite": 440000,
    }
