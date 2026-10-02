import sys
from datetime import datetime
from pathlib import Path

from crawler.http import new_session
from crawler.models import ShopResult
from crawler.shops import SHOPS
from crawler.store import DATA_DIR, append_history, load_json, save_json
from crawler.update import JST, apply_results, update_daily


def crawl_shop(module, session, colors) -> ShopResult:
    try:
        offers = module.parse(module.fetch(session), colors)
        return ShopResult({offer.variant: offer.price for offer in offers}, None)
    except Exception as exc:  # một cửa hàng lỗi không được làm hỏng các cửa hàng khác
        return ShopResult({}, f"{type(exc).__name__}: {exc}")


def crawl_colors(catalog: dict) -> dict[str, list[str]]:
    """Chỉ các màu thuộc dòng máy đang crawl, để parser không sinh giá cho màu của dòng máy khác."""
    wanted = {color for model in catalog["models"] if model["crawl"] for color in model["colors"]}
    return {color_id: color["aliases"] for color_id, color in catalog["colors"].items() if color_id in wanted}


def main(data_dir: Path = DATA_DIR, shops: dict = SHOPS, now: datetime | None = None) -> int:
    catalog = load_json(data_dir / "catalog.json", None)
    colors = crawl_colors(catalog)
    session = new_session()

    results = {}
    for shop in catalog["shops"]:
        result = crawl_shop(shops[shop["id"]], session, colors)
        status = f"OK {len(result.prices)} giá" if result.error is None else f"LỖI {result.error}"
        print(f"[{shop['id']}] {status}")
        results[shop["id"]] = result

    now = now or datetime.now(JST)
    old_latest = load_json(data_dir / "latest.json", {"generated_at": None, "shops": {}})
    latest, events = apply_results(old_latest, results, now)
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
            print(f"[{shop_id}] bị bỏ qua: {latest['shops'][shop_id]['error']}")
    all_failed = all(latest["shops"][shop_id]["error"] for shop_id in results)
    return 1 if all_failed else 0


if __name__ == "__main__":
    sys.exit(main())
