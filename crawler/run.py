import argparse
import sys
from datetime import datetime
from pathlib import Path

from crawler.categories import crawl_colors, get_category  # noqa: F401  (crawl_colors giữ để import cũ vẫn chạy)
from crawler.http import new_session
from crawler.models import ShopResult
from crawler.store import append_history, load_json, save_json
from crawler.update import JST, apply_results, update_daily


def crawl_shop(module, session, context) -> ShopResult:
    try:
        offers = module.parse(module.fetch(session), context)
        return ShopResult({offer.variant: offer.price for offer in offers}, None)
    except Exception as exc:  # một cửa hàng lỗi không được làm hỏng các cửa hàng khác
        return ShopResult({}, f"{type(exc).__name__}: {exc}")


def main(data_dir: Path | None = None, shops: dict | None = None, now: datetime | None = None,
         category: str = "iphone") -> int:
    cat = get_category(category)
    data_dir = data_dir or cat.data_dir
    shops = shops if shops is not None else cat.shops
    catalog = load_json(data_dir / "catalog.json", None)
    context = cat.context(catalog)
    session = new_session()

    results = {}
    for shop in catalog["shops"]:
        result = crawl_shop(shops[shop["id"]], session, context)
        status = f"OK {len(result.prices)} giá" if result.error is None else f"LỖI {result.error}"
        print(f"[{category}/{shop['id']}] {status}")
        results[shop["id"]] = result

    now = now or datetime.now(JST)
    old_latest = load_json(data_dir / "latest.json", {"generated_at": None, "shops": {}})
    latest, events = apply_results(old_latest, results, now, price_range=cat.price_range)
    if latest["shops"] != old_latest["shops"]:
        save_json(data_dir / "latest.json", latest)
    if events:
        append_history(data_dir, events)
    old_daily = load_json(data_dir / "daily.json", {})
    mail_only = {shop["id"] for shop in catalog["shops"] if shop.get("mail_only")}
    daily = update_daily(old_daily, latest, now, skip=mail_only)
    if daily != old_daily:
        save_json(data_dir / "daily.json", daily)

    for shop_id in results:
        if latest["shops"][shop_id]["error"]:
            print(f"[{category}/{shop_id}] bị bỏ qua: {latest['shops'][shop_id]['error']}")
    all_failed = all(latest["shops"][shop_id]["error"] for shop_id in results)
    return 1 if all_failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="iphone", choices=["iphone", "pokemon"])
    sys.exit(main(category=parser.parse_args().category))
