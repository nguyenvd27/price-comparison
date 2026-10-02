import json
from datetime import datetime
from types import SimpleNamespace

from crawler.categories import get_category
from crawler.models import Offer, ShopResult
from crawler.run import main
from crawler.store import DATA_DIR
from crawler.update import JST, apply_results

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=JST)


def test_iphone_category_is_the_old_setup():
    cat = get_category("iphone")
    assert cat.data_dir == DATA_DIR
    assert cat.price_range == (100_000, 1_000_000)
    assert "morimori" in cat.shops


def test_pokemon_category_has_own_folder_and_range():
    cat = get_category("pokemon")
    assert cat.data_dir == DATA_DIR / "pokemon"
    assert cat.price_range == (1_000, 2_000_000)
    assert cat.context({"items": [{"id": "x"}]}) == [{"id": "x"}]


def test_price_range_is_per_category():
    results = {"a": ShopResult({"mega-30th": 26000}, None)}
    latest, _ = apply_results({"shops": {}}, results, NOW)
    assert latest["shops"]["a"]["error"].startswith("Giá vô lý")
    latest, _ = apply_results({"shops": {}}, results, NOW, price_range=(1_000, 2_000_000))
    assert latest["shops"]["a"]["error"] is None


def test_run_pokemon_writes_only_its_folder(tmp_path):
    catalog = {"items": [{"id": "mega-30th"}], "shops": [{"id": "a"}, {"id": "b"}]}
    (tmp_path / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    seen = []

    def parse(raw, items):
        seen.append(items)
        return [Offer("mega-30th", 26000)]

    empty = SimpleNamespace(fetch=lambda session: "raw", parse=lambda raw, items: [])
    shops = {"a": SimpleNamespace(fetch=lambda session: "raw", parse=parse), "b": empty}
    assert main(tmp_path, shops, NOW, category="pokemon") == 0
    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert latest["shops"]["a"]["prices"] == {"mega-30th": 26000}
    assert latest["shops"]["b"]["error"] == "Không lấy được giá nào"
    assert seen == [[{"id": "mega-30th"}]]
