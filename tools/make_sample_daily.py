"""Tạo DỮ LIỆU MẪU (không phải giá thật) cho daily.json từ ngày mở bán 2026-09-18 đến 2026-10-01.

Chỉ dùng để xem trước biểu đồ khi chưa có lịch sử thật. Xem docs/sample-data.md.
Dùng: .venv/bin/python tools/make_sample_daily.py

Cách tạo cho mỗi phiên bản 18 Pro Max:
- Điểm neo là giá thật cao nhất của ngày 2026-10-02 (do crawler ghi).
- Ngày mở bán cao hơn ~6.5%, giảm tuyến tính về giá neo.
- Thứ 7/Chủ nhật thấp hơn 6,000 yên; cộng nhiễu ngẫu nhiên ±1,500 (seed cố định); làm tròn 1,000 yên.
- Mọi điểm có "sample": true. Điểm dữ liệu thật đã có (không có cờ sample) không bị ghi đè.
"""
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "web" / "data"
LAUNCH = date(2026, 9, 18)
ANCHOR = date(2026, 10, 2)
LAUNCH_PREMIUM = 0.065
WEEKEND_DROP = 6000
NOISE = 1500


def main() -> int:
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    daily = json.loads((DATA / "daily.json").read_text(encoding="utf-8"))
    anchor = daily.get(ANCHOR.isoformat())
    if not anchor:
        sys.exit(f"Chưa có dữ liệu thật ngày {ANCHOR} để làm điểm neo")

    rng = random.Random(918)
    span = (ANCHOR - LAUNCH).days
    written = 0
    for offset in range(span):
        day = LAUNCH + timedelta(days=offset)
        key = day.isoformat()
        entries = daily.setdefault(key, {})
        for variant in catalog["variants"]:
            real = anchor.get(variant["id"])
            if variant["model"] != "pm" or not real:
                continue
            if variant["id"] in entries and not entries[variant["id"]].get("sample"):
                continue  # đã có giá thật: giữ nguyên
            price = real["max"] * (1 + LAUNCH_PREMIUM * (1 - offset / span))
            if day.weekday() >= 5:
                price -= WEEKEND_DROP
            price += rng.uniform(-NOISE, NOISE)
            entries[variant["id"]] = {"max": int(round(price, -3)), "shop": real["shop"], "sample": True}
            written += 1
        daily[key] = dict(sorted(entries.items()))

    ordered = {k: daily[k] for k in sorted(daily)}
    (DATA / "daily.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Đã ghi {written} điểm dữ liệu mẫu ({LAUNCH} → {ANCHOR - timedelta(days=1)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
