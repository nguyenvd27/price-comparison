from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from crawler.models import ShopResult

JST = ZoneInfo("Asia/Tokyo")
MIN_PRICE = 100_000
MAX_PRICE = 1_000_000
HEARTBEAT = timedelta(minutes=60)
EMPTY_SHOP = {"last_success_at": None, "display_at": None, "error": None, "prices": {}}


def jst_date(value: str | datetime) -> str:
    moment = datetime.fromisoformat(value) if isinstance(value, str) else value
    return moment.astimezone(JST).date().isoformat()


def validate(prices: dict[str, int]) -> str | None:
    if not prices:
        return "Không lấy được giá nào"
    bad = sorted(v for v, p in prices.items() if not MIN_PRICE <= p <= MAX_PRICE)
    if bad:
        return f"Giá vô lý: {', '.join(bad)}"
    return None


def apply_results(latest: dict, results: dict[str, ShopResult], now: datetime) -> tuple[dict, list[dict]]:
    now_iso = now.astimezone(JST).isoformat(timespec="seconds")
    shops = dict(latest.get("shops", {}))
    events: list[dict] = []
    for shop_id, result in results.items():
        prev = shops.get(shop_id, EMPTY_SHOP)
        error = result.error or validate(result.prices)
        if error:
            shops[shop_id] = {**prev, "error": error}
            continue

        old = prev["prices"]
        new = dict(sorted(result.prices.items()))
        changed = new != old
        last = prev["last_success_at"]
        first_today = last is None or jst_date(last) != jst_date(now)
        heartbeat = last is None or now - datetime.fromisoformat(last) >= HEARTBEAT

        for variant in sorted(set(old) | set(new)):
            if old.get(variant) != new.get(variant):
                events.append({"t": now_iso, "shop": shop_id, "variant": variant, "price": new.get(variant)})

        shops[shop_id] = {
            "last_success_at": now_iso if changed or first_today or heartbeat else last,
            "display_at": now_iso if changed or first_today else prev["display_at"],
            "error": None,
            "prices": new,
        }
    return {"generated_at": now_iso, "shops": shops}, events


def update_daily(daily: dict, latest: dict, now: datetime, skip: set[str] = frozenset()) -> dict:
    """Giá cao nhất từng thấy trong ngày JST, tính trên các cửa hàng đã crawl thành công hôm nay.

    `skip`: cửa hàng không tính (chỉ mua qua bưu điện, khớp với cột Diff trên web).
    """
    day = jst_date(now)
    today = dict(daily.get(day, {}))
    for shop_id, shop in latest["shops"].items():
        if shop_id in skip or shop["error"] or not shop["last_success_at"] or jst_date(shop["last_success_at"]) != day:
            continue
        for variant, price in shop["prices"].items():
            if variant not in today or price > today[variant]["max"]:
                today[variant] = {"max": price, "shop": shop_id}
    return {**daily, day: dict(sorted(today.items()))}
