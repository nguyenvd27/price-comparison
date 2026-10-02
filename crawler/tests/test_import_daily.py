import pytest

from crawler.import_daily import import_rows

CATALOG = {
    "variants": [{"id": "pm-256-black"}, {"id": "pm-256-silver"}],
    "shops": [{"id": "mobaste"}, {"id": "ichiban"}],
}


def test_import_overwrites_and_clears_sample_flag():
    daily = {
        "2026-09-18": {
            "pm-256-black": {"max": 250000, "shop": "ichiban", "sample": True},
            "pm-256-silver": {"max": 240000, "shop": "ichiban", "sample": True},
        },
    }
    rows = [{"date": "2026-09-18", "variant": "pm-256-black", "max": "275,000", "shop": "mobaste"}]
    assert import_rows(daily, rows, CATALOG) == {
        "2026-09-18": {
            "pm-256-black": {"max": 275000, "shop": "mobaste"},
            "pm-256-silver": {"max": 240000, "shop": "ichiban", "sample": True},
        },
    }


def test_import_adds_new_day_in_order():
    daily = {"2026-09-20": {}}
    rows = [{"date": "2026-09-19", "variant": "pm-256-silver", "max": "241000", "shop": "ichiban"}]
    assert list(import_rows(daily, rows, CATALOG)) == ["2026-09-19", "2026-09-20"]


@pytest.mark.parametrize("row, message", [
    ({"date": "2026-09-18", "variant": "pm-9tb-black", "max": "275000", "shop": "mobaste"}, "variant"),
    ({"date": "2026-09-18", "variant": "pm-256-black", "max": "275000", "shop": "nope"}, "shop"),
    ({"date": "2026-09-18", "variant": "pm-256-black", "max": "5000", "shop": "mobaste"}, "giá"),
    ({"date": "18/9", "variant": "pm-256-black", "max": "275000", "shop": "mobaste"}, "ngày"),
])
def test_import_rejects_bad_rows(row, message):
    with pytest.raises(ValueError, match=message):
        import_rows({}, [row], CATALOG)


def test_main_reads_csv_with_bom(tmp_path):
    import json

    from crawler.import_daily import main

    (tmp_path / "catalog.json").write_text(json.dumps(CATALOG), encoding="utf-8")
    (tmp_path / "daily.json").write_text("{}", encoding="utf-8")
    csv_file = tmp_path / "gia.csv"
    csv_file.write_text("date,variant,max,shop\n2026-09-18,pm-256-black,\"275,000\",mobaste\n", encoding="utf-8-sig")
    assert main(str(csv_file), tmp_path) == 0
    saved = json.loads((tmp_path / "daily.json").read_text(encoding="utf-8"))
    assert saved == {"2026-09-18": {"pm-256-black": {"max": 275000, "shop": "mobaste"}}}
