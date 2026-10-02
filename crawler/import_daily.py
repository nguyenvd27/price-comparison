"""Nhập giá thật (ví dụ gõ lại từ bài đăng trên X) vào web/data/daily.json.

Dùng: python -m crawler.import_daily gia_that.csv
CSV có các cột: date,variant,max,shop  (vd: 2026-09-18,pm-256-burgundy,275000,mobaste)
Mỗi dòng ghi đè đúng ngày + phiên bản đó và bỏ cờ "sample".
"""
import csv
import re
import sys
from pathlib import Path

from crawler.normalize import parse_price
from crawler.store import DATA_DIR, load_json, save_json
from crawler.update import MAX_PRICE, MIN_PRICE


def import_rows(daily: dict, rows: list[dict], catalog: dict) -> dict:
    variants = {v["id"] for v in catalog["variants"]}
    shops = {s["id"] for s in catalog["shops"]}
    result = {day: dict(entries) for day, entries in daily.items()}
    for line, row in enumerate(rows, start=2):  # dòng 1 là tiêu đề
        date, variant, shop = row["date"].strip(), row["variant"].strip(), row["shop"].strip()
        price = parse_price(row["max"])
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            raise ValueError(f"Dòng {line}: ngày phải có dạng YYYY-MM-DD, nhận được {date!r}")
        if variant not in variants:
            raise ValueError(f"Dòng {line}: variant không có trong catalog: {variant!r}")
        if shop not in shops:
            raise ValueError(f"Dòng {line}: shop không có trong catalog: {shop!r}")
        if price is None or not MIN_PRICE <= price <= MAX_PRICE:
            raise ValueError(f"Dòng {line}: giá vô lý: {row['max']!r}")
        result.setdefault(date, {})[variant] = {"max": price, "shop": shop}
    return {day: dict(sorted(result[day].items())) for day in sorted(result)}


def main(csv_path: str, data_dir: Path = DATA_DIR) -> int:
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    catalog = load_json(data_dir / "catalog.json", None)
    daily = import_rows(load_json(data_dir / "daily.json", {}), rows, catalog)
    save_json(data_dir / "daily.json", daily)
    print(f"Đã nhập {len(rows)} dòng vào {data_dir / 'daily.json'}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Dùng: python -m crawler.import_daily <file.csv>")
    sys.exit(main(sys.argv[1]))
