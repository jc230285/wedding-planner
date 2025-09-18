"""Utilities for loading CSV guest data into Supabase."""

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = PROJECT_ROOT / "data.csv"


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


def load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"CSV file not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = []
        for row in reader:
            if not any(cell and cell.strip() for cell in row.values()):
                continue
            rows.append({key: (value.strip() if value is not None else None) or None for key, value in row.items()})
    if not rows:
        raise SystemExit("No rows were found in the CSV file.")
    return rows


def batched(rows: Iterable[Dict[str, str]], size: int) -> Iterator[List[Dict[str, str]]]:
    batch: List[Dict[str, str]] = []
    for row in rows:
        batch.append(row)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def import_rows(config: Dict[str, str], rows: List[Dict[str, str]], chunk_size: int) -> int:
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