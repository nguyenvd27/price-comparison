import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "web" / "data"


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def append_history(data_dir: Path, events: list[dict]) -> None:
    """Mỗi tháng (theo JST) một file history/YYYY-MM.json."""
    by_month: dict[str, list[dict]] = {}
    for event in events:
        by_month.setdefault(event["t"][:7], []).append(event)
    for month, items in by_month.items():
        path = data_dir / "history" / f"{month}.json"
        save_json(path, load_json(path, []) + items)
