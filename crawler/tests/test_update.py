from datetime import datetime, timedelta, timezone

from crawler.models import ShopResult
from crawler.update import JST, apply_results, update_daily

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=JST)
ISO_NOW = "2026-10-02T12:00:00+09:00"


def shop_state(prices, last="2026-10-02T11:30:00+09:00", display="2026-10-02T09:00:00+09:00", error=None):
    return {"last_success_at": last, "display_at": display, "error": error, "prices": prices}


def test_first_run_records_everything():
    latest, events = apply_results({"shops": {}}, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert latest["generated_at"] == ISO_NOW
    assert latest["shops"]["a"] == shop_state({"pm-256-black": 236000}, last=ISO_NOW, display=ISO_NOW)
    assert events == [{"t": ISO_NOW, "shop": "a", "variant": "pm-256-black", "price": 236000}]


def test_unchanged_same_day_keeps_times_and_no_events():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000})}}
    latest, events = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert latest["shops"]["a"] == prev["shops"]["a"]
    assert events == []


def test_heartbeat_refreshes_last_success_after_60_minutes():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000}, last="2026-10-02T10:59:00+09:00")}}
    latest, _ = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert latest["shops"]["a"]["last_success_at"] == ISO_NOW
    assert latest["shops"]["a"]["display_at"] == "2026-10-02T09:00:00+09:00"


def test_price_change_updates_display_and_logs_event():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000})}}
    latest, events = apply_results(prev, {"a": ShopResult({"pm-256-black": 237000}, None)}, NOW)
    assert latest["shops"]["a"]["display_at"] == ISO_NOW
    assert events == [{"t": ISO_NOW, "shop": "a", "variant": "pm-256-black", "price": 237000}]


def test_disappeared_variant_logs_none():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000, "pm-256-silver": 231000})}}
    _, events = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert events == [{"t": ISO_NOW, "shop": "a", "variant": "pm-256-silver", "price": None}]


def test_first_success_of_new_jst_day_updates_display_at():
    prev = {"shops": {"a": shop_state(
        {"pm-256-black": 236000},
        last="2026-10-01T23:50:00+09:00",
        display="2026-10-01T09:00:00+09:00",
    )}}
    now_utc = datetime(2026, 10, 1, 15, 5, tzinfo=timezone.utc)  # = 10/02 00:05 JST
    latest, events = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, now_utc)
    assert latest["shops"]["a"]["display_at"] == "2026-10-02T00:05:00+09:00"
    assert events == []


def test_error_keeps_old_prices():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000})}}
    latest, events = apply_results(prev, {"a": ShopResult({}, "HTTPError: 503")}, NOW)
    assert latest["shops"]["a"] == {**prev["shops"]["a"], "error": "HTTPError: 503"}
    assert events == []


def test_empty_prices_is_error_and_keeps_old():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000})}}
    latest, events = apply_results(prev, {"a": ShopResult({}, None)}, NOW)
    assert latest["shops"]["a"]["error"] == "Không lấy được giá nào"
    assert latest["shops"]["a"]["prices"] == {"pm-256-black": 236000}
    assert events == []


def test_absurd_price_is_error():
    latest, _ = apply_results({"shops": {}}, {"a": ShopResult({"pm-256-black": 5000}, None)}, NOW)
    assert latest["shops"]["a"]["error"].startswith("Giá vô lý")
    assert latest["shops"]["a"]["prices"] == {}


def test_recovery_clears_error():
    prev = {"shops": {"a": shop_state({"pm-256-black": 236000}, error="HTTPError: 503")}}
    latest, _ = apply_results(prev, {"a": ShopResult({"pm-256-black": 236000}, None)}, NOW)
    assert latest["shops"]["a"]["error"] is None


def test_daily_keeps_highest_of_the_day():
    daily = {"2026-10-02": {"pm-256-black": {"max": 240000, "shop": "b"}}}
    latest = {"shops": {
        "a": shop_state({"pm-256-black": 236000, "pm-256-silver": 231000}, last=ISO_NOW),
        "b": shop_state({"pm-256-silver": 233000}, last=ISO_NOW),
    }}
    assert update_daily(daily, latest, NOW) == {"2026-10-02": {
        "pm-256-black": {"max": 240000, "shop": "b"},
        "pm-256-silver": {"max": 233000, "shop": "b"},
    }}


def test_daily_ignores_failed_and_stale_shops():
    latest = {"shops": {
        "a": shop_state({"pm-256-black": 300000}, last=ISO_NOW, error="HTTPError: 503"),
        "b": shop_state({"pm-256-black": 299000}, last="2026-10-01T18:00:00+09:00"),
        "c": shop_state({"pm-256-black": 236000}, last=ISO_NOW),
    }}
    assert update_daily({}, latest, NOW) == {"2026-10-02": {"pm-256-black": {"max": 236000, "shop": "c"}}}


def test_daily_skips_given_shops():
    latest = {"shops": {
        "mail": shop_state({"pm-256-black": 300000}, last=ISO_NOW),
        "c": shop_state({"pm-256-black": 236000}, last=ISO_NOW),
    }}
    assert update_daily({}, latest, NOW, skip={"mail"}) == {"2026-10-02": {"pm-256-black": {"max": 236000, "shop": "c"}}}
