from pathlib import Path
import json
import time

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT = DATA_DIR / "criteo_sample_5000.csv"
META = DATA_DIR / "sample_metadata.json"
BASE = "https://datasets-server.huggingface.co/rows"
PARAMS = {"dataset": "criteo/criteo-uplift", "config": "default", "split": "train"}


def get_page(offset, length=100, retries=4):
    params = dict(PARAMS, offset=offset, length=length)
    last = None
    for attempt in range(retries):
        try:
            response = requests.get(BASE, params=params, timeout=45)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Unable to fetch offset {offset}: {last}")


def main():
    first = get_page(0)
    total = int(first["num_rows_total"])
    pages = 50
    offsets = [int(i * (total - 100) / (pages - 1)) for i in range(pages)]
    rows = []
    for i, offset in enumerate(offsets, start=1):
        payload = first if offset == 0 else get_page(offset)
        rows.extend(item["row"] for item in payload["rows"])
        print(f"fetched {i}/{pages} pages, offset={offset}")
    df = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)
    df.to_csv(OUT, index=False)
    metadata = {
        "dataset": "criteo/criteo-uplift",
        "viewer_endpoint": BASE,
        "split": "train",
        "full_rows_reported_by_viewer": total,
        "requested_pages": pages,
        "rows_saved": len(df),
        "sampling_scheme": "50 deterministic pages of 100 rows spaced across the full row index range",
        "warning": "This is a stratified index sample for portfolio demonstration. It must not be presented as a full-dataset estimate.",
    }
    META.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
