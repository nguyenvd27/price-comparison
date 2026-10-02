import json

from crawler.store import DATA_DIR


def test_catalog_is_consistent():
    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    models = {m["id"]: m for m in catalog["models"]}
    assert list(models) == ["pm", "duo"]
    for variant in catalog["variants"]:
        model = models[variant["model"]]
        assert variant["color"] in model["colors"], variant["id"]
        assert variant["color"] in catalog["colors"], variant["id"]
    counts = {m: sum(v["model"] == m for v in catalog["variants"]) for m in models}
    assert counts == {"pm": 16, "duo": 8}
    duo = {v["id"]: v["apple_price"] for v in catalog["variants"] if v["model"] == "duo"}
    assert duo["duo-256-nightsky"] == 364800
    assert duo["duo-2tb-starwhite"] == 574800
    assert models["duo"]["crawl"] is False and models["duo"]["release"] == "2026-10-23"


def test_every_catalog_shop_has_a_crawler_and_hours():
    from crawler.shops import SHOPS

    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    ids = [shop["id"] for shop in catalog["shops"]]
    assert sorted(ids) == sorted(SHOPS)
    assert len(ids) == 14
    for shop in catalog["shops"]:
        assert set(shop["hours"]) == {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}, shop["id"]
        assert any(shop["hours"].values()), shop["id"]


def test_mail_only_shops():
    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    assert [s["id"] for s in catalog["shops"] if s.get("mail_only")] == ["base"]
