"""Consolidate duplicate columns and clean up the guests table."""

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

    # First, ensure the restrictions column exists
    print("Adding restrictions column if it doesn't exist...")
    execute_sql("ALTER TABLE public.guests ADD COLUMN IF NOT EXISTS restrictions text;", database_url)

    # Consolidate duplicate columns by taking the higher value (GREATEST function handles nulls)
    SQL = """
    -- Consolidate ideas columns (stag_ideas -> ideas if ideas is null or empty)
    UPDATE public.guests 
    SET ideas = COALESCE(NULLIF(TRIM(stag_ideas), ''), NULLIF(TRIM(ideas), ''))
    WHERE (ideas IS NULL OR TRIM(ideas) = '') AND stag_ideas IS NOT NULL AND TRIM(stag_ideas) != '';

    UPDATE public.guests 
    SET ideas = COALESCE(NULLIF(TRIM(hen_ideas), ''), NULLIF(TRIM(ideas), ''))
    WHERE (ideas IS NULL OR TRIM(ideas) = '') AND hen_ideas IS NOT NULL AND TRIM(hen_ideas) != '';

    -- Consolidate friday room columns (take the higher value)
    UPDATE public.guests 
    SET friday_room = GREATEST(COALESCE(friday_room, -2), COALESCE(friday_stay_preference, -2))
    WHERE friday_stay_preference IS NOT NULL;

    -- Consolidate saturday room columns (take the higher value)
    UPDATE public.guests 
    SET saturday_room = GREATEST(COALESCE(saturday_room, -2), COALESCE(saturday_stay_preference, -2))
    WHERE saturday_stay_preference IS NOT NULL;

    -- Drop the duplicate columns
    ALTER TABLE public.guests DROP COLUMN IF EXISTS stag_ideas;
    ALTER TABLE public.guests DROP COLUMN IF EXISTS hen_ideas;
    ALTER TABLE public.guests DROP COLUMN IF EXISTS friday_stay_preference;
    ALTER TABLE public.guests DROP COLUMN IF EXISTS saturday_stay_preference;
    """
    
    print("Consolidating duplicate columns...")
    execute_sql(SQL, database_url)
    print("Successfully consolidated duplicate columns and cleaned up the guests table.")

if __name__ == "__main__":
    main()