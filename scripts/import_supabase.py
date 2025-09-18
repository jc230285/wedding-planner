"""Utilities for loading CSV guest data into Supabase."""

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = PROJECT_ROOT / "data.csv"
INT_COLUMNS = {"stag", "hen", "friday_room", "ceremony", "wedding_meal", "saturday_room"}
COLUMN_OVERRIDES = {"type": "guest_type"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import rows from a CSV file into a Supabase table via the REST API.",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"Path to the CSV file (default: {DEFAULT_CSV_PATH})",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Number of rows to send per request (default: 500)",
    )
    return parser.parse_args()


def ensure_env() -> Dict[str, str]:
    load_dotenv(PROJECT_ROOT / ".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    table = os.getenv("SUPABASE_TABLE", "guests")

    missing = [name for name, value in {
        "SUPABASE_URL": url,
        "SUPABASE_SERVICE_ROLE_KEY": key,
    }.items() if not value]

    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing required environment values: {joined}.")

    return {"url": url.rstrip("/"), "key": key, "table": table}


def to_column_name(header: str) -> str:
    candidate = re.sub(r"[^a-z0-9]+", "_", header.strip().lower()).strip("_")
    if not candidate:
        raise SystemExit(f"Unable to derive column name from header '{header}'.")
    return COLUMN_OVERRIDES.get(candidate, candidate)


def load_rows(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        raise SystemExit(f"CSV file not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise SystemExit("CSV file does not contain headers.")
        mapping = {header: to_column_name(header) for header in reader.fieldnames}

        rows = []
        for raw_row in reader:
            normalized: Dict[str, object] = {}
            for raw_key, raw_value in raw_row.items():
                if raw_key is None:
                    continue
                column = mapping[raw_key]
                value = (raw_value.strip() if raw_value is not None else "")
                normalized[column] = value or None

            if not any(value not in (None, "") for value in normalized.values()):
                continue

            for column in INT_COLUMNS:
                if column in normalized and normalized[column] not in (None, ""):
                    try:
                        normalized[column] = int(normalized[column])
                    except ValueError:
                        pass

            rows.append(normalized)

    if not rows:
        raise SystemExit("No rows were found in the CSV file.")
    return rows


def batched(rows: Iterable[Dict[str, object]], size: int) -> Iterator[List[Dict[str, object]]]:
    batch: List[Dict[str, object]] = []
    for row in rows:
        batch.append(row)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def import_rows(config: Dict[str, str], rows: List[Dict[str, object]], chunk_size: int) -> int:
    endpoint = f"{config['url']}/rest/v1/{config['table']}"
    session = requests.Session()
    session.headers.update({
        "apikey": config["key"],
        "Authorization": f"Bearer {config['key']}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    })

    total_inserted = 0
    for batch in batched(rows, chunk_size):
        response = session.post(endpoint, data=json.dumps(batch))
        if not response.ok:
            raise SystemExit(
                f"Supabase returned {response.status_code}: {response.text}"
            )
        total_inserted += len(batch)
    return total_inserted


def main() -> None:
    args = parse_args()
    env = ensure_env()
    rows = load_rows(args.file)
    inserted = import_rows(env, rows, args.chunk_size)
    print(f"Imported {inserted} rows into table '{env['table']}'.")


if __name__ == "__main__":
    main()