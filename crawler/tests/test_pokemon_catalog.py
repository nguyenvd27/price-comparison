import json
import re

from crawler.store import DATA_DIR


def load():
    return json.loads((DATA_DIR / "pokemon" / "catalog.json").read_text(encoding="utf-8"))


def test_items_are_well_formed_and_unique():
    catalog = load()
    series = {s["id"] for s in catalog["series"]}
    items = catalog["items"]
    assert len(items) == 21
    assert len({i["id"] for i in items}) == 21
    jans = [j for i in items for j in i["jan"]]
    assert len(jans) == len(set(jans))
    for item in items:
        assert item["series"] in series, item["id"]
        assert item["retail"] > 0, item["id"]
        assert all(re.fullmatch(r"\d{13}", j) for j in item["jan"]), item["id"]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", item["release"]), item["id"]
        assert item["image"].startswith("https://www.pokemon-card.com/"), item["id"]
        assert item["aliases"], item["id"]


def test_shops_have_hours_and_shinsoku_is_mail_only():
    shops = load()["shops"]
    assert [s["id"] for s in shops] == ["morimori", "homura", "rudeya", "ichiban", "oku", "runto", "ichome", "shinsoku"]
    for shop in shops:
        assert set(shop["hours"]) == {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}, shop["id"]
    assert [s["id"] for s in shops if s.get("mail_only")] == ["shinsoku"]


def test_every_pokemon_shop_has_a_parser():
    from crawler.pokemon.shops import SHOPS

    assert sorted(s["id"] for s in load()["shops"]) == sorted(SHOPS)
