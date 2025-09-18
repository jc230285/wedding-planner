"""Add missing columns to the guests table."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from utils.db import normalize_database_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def execute_sql(sql: str, database_url: str) -> None:
    """Execute SQL statements."""
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for statement in sql.strip().split(";"):
                if statement.strip():
                    cur.execute(statement)
        conn.commit()

def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    database_url_raw = os.getenv("DATABASE_URL")
    database_url = normalize_database_url(database_url_raw) if database_url_raw else None
    if not database_url:
        raise ValueError("DATABASE_URL not found in .env")

    SQL = """
    ALTER TABLE public.guests ADD COLUMN IF NOT EXISTS attendance_status integer;
    """
    execute_sql(SQL, database_url)
    print("Added attendance_status column to guests table.")

if __name__ == "__main__":
    main()