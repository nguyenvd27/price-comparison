import json
from datetime import datetime
from types import SimpleNamespace

from crawler.models import Offer
from crawler.run import main
from crawler.update import JST

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=JST)
CATALOG = {
    "models": [{"id": "pm", "colors": ["black"], "crawl": True}],
    "colors": {"black": {"aliases": ["ブラック"]}},
    "shops": [{"id": "a"}, {"id": "b"}],
}


def ok_shop(price=236000):
    return SimpleNamespace(fetch=lambda session: "raw", parse=lambda raw, colors: [Offer("pm-256-black", price)])


def broken_shop():
    def fetch(session):
        raise RuntimeError("boom")
    return SimpleNamespace(fetch=fetch, parse=lambda raw, colors: [])


def setup(tmp_path):
    (tmp_path / "catalog.json").write_text(json.dumps(CATALOG), encoding="utf-8")
    return tmp_path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_run_records_error_for_failing_shop(tmp_path):
    data_dir = setup(tmp_path)
    assert main(data_dir, {"a": ok_shop(), "b": broken_shop()}, NOW) == 0
    latest = read(data_dir / "latest.json")
    assert latest["shops"]["a"]["prices"] == {"pm-256-black": 236000}
    assert latest["shops"]["b"]["error"] == "RuntimeError: boom"
    assert read(data_dir / "history" / "2026-10.json") == [
        {"t": "2026-10-02T12:00:00+09:00", "shop": "a", "variant": "pm-256-black", "price": 236000},
    ]
    assert read(data_dir / "daily.json") == {"2026-10-02": {"pm-256-black": {"max": 236000, "shop": "a"}}}


def test_run_returns_1_when_all_shops_fail(tmp_path):
    data_dir = setup(tmp_path)
    assert main(data_dir, {"a": broken_shop(), "b": broken_shop()}, NOW) == 1


def test_run_does_not_rewrite_latest_when_nothing_changed(tmp_path):
    data_dir = setup(tmp_path)
    shops = {"a": ok_shop(), "b": ok_shop()}
    main(data_dir, shops, NOW)
    before = (data_dir / "latest.json").read_text(encoding="utf-8")
    main(data_dir, shops, NOW.replace(minute=15))
    assert (data_dir / "latest.json").read_text(encoding="utf-8") == before
    assert len(read(data_dir / "history" / "2026-10.json")) == 2


def test_run_only_passes_colors_of_crawled_models(tmp_path):
    catalog = {
        "models": [
            {"id": "pm", "colors": ["black"], "crawl": True},
            {"id": "duo", "colors": ["nightsky"], "crawl": False},
        ],
        "colors": {"black": {"aliases": ["ブラック"]}, "nightsky": {"aliases": ["ナイトスカイ"]}},
        "shops": [{"id": "a"}],
    }
    (tmp_path / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    seen = []

    def parse(raw, colors):
        seen.append(colors)
        return [Offer("pm-256-black", 236000)]

    main(tmp_path, {"a": SimpleNamespace(fetch=lambda session: "raw", parse=parse)}, NOW)
    assert seen == [{"black": ["ブラック"]}]
