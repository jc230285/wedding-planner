"""Create the guests table in Supabase using the direct Postgres connection."""

import os
import textwrap
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from utils.db import normalize_database_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL = textwrap.dedent(
    """
    create extension if not exists "pgcrypto";

    create table if not exists public.guests (
        id uuid primary key default gen_random_uuid(),
        name text not null,
        age text,
        side text,
        guest_type text,
        sex text,
        stag integer,
        hen integer,
        friday_room integer,
        ceremony integer,
        wedding_meal integer,
        restrictions text,
        saturday_room integer,
        email text,
        mobile text,
        address text,
        family_id text,
        music_requests text,
        comment text,
        created_at timestamptz default timezone('utc', now())
    );

    create table if not exists public.guest_change_log (
        id uuid primary key default gen_random_uuid(),
        guest_id uuid not null references public.guests(id) on delete cascade,
        family_id text,
        column_name text not null,
        old_value text,
        new_value text,
        changed_by text,
        changed_at timestamptz default timezone('utc', now())
    );

    create index if not exists idx_guest_change_log_guest_id on public.guest_change_log(guest_id);
    create index if not exists idx_guest_change_log_family_id on public.guest_change_log(family_id);
    """
)


def ensure_env() -> str:
    load_dotenv(PROJECT_ROOT / ".env")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit("Missing DATABASE_URL in .env")
    return normalize_database_url(db_url)


def execute_sql(sql: str, database_url: str) -> None:
    statements = [stmt.strip() for stmt in sql.strip().split(";") if stmt.strip()]
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)
        conn.commit()


def main() -> None:
    database_url = ensure_env()
    execute_sql(SQL, database_url)
    print("Supabase guests table created or already exists.")


if __name__ == "__main__":
    main()